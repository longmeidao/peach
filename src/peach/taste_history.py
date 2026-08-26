from __future__ import annotations

import csv
import hashlib
import json
import re
import socket
import sqlite3
import tempfile
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


@dataclass(frozen=True)
class HistorySource:
    browser: str
    profile: str
    path: Path


@dataclass(frozen=True)
class HistoryVisit:
    visit_key: str
    visited_at: str
    url: str
    title: str


QUERY_KEYS = {"q", "query", "search", "keyword", "keywords", "tag", "tags", "term"}
CREATOR_MARKERS = {"artist", "artists", "author", "channel", "creator", "creators", "model", "models", "profile"}
CREATOR_HOSTS = {"fansly.com", "onlyfans.com", "patreon.com", "rule34video.com"}
RESERVED_HANDLES = {
    "about", "account", "creator", "creators", "explore", "home", "login", "messages", "model",
    "models", "notifications", "post", "posts", "search", "settings", "share", "user", "users",
}
STOPWORDS = {
    "and", "com", "download", "for", "from", "html", "http", "https", "in", "index", "is",
    "login", "of", "one", "page", "search", "the", "this", "to", "video", "watch", "www",
    "图片", "搜索", "视频",
}
TASTE_DOMAIN_SUFFIXES = {
    "cangku.moe", "coomer.st", "e-hentai.org", "exhentai.org", "f95zone.to", "fanbox.cc",
    "fansly.com", "fantia.jp", "gelbooru.com", "hanime1.me", "jable.tv", "javbus.com",
    "javdb.com", "kemono.cr", "kemono.su", "missav.com", "nhentai.net", "onlyfans.com",
    "patreon.com", "pawchive.com", "pixiv.net", "pornhub.com", "redgifs.com", "rule34.xxx",
    "rule34video.com", "simpcity.cr", "simpcity.su", "south-plus.org", "spankbang.com",
    "supjav.com", "xhamster.com", "xsijishe.com", "xvideos.com",
}
CATEGORY_TERMS: dict[str, set[str]] = {
    "足系": {"feet", "foot", "footjob", "soles", "toes", "足", "足交", "脚", "脚交"},
    "3D/动画": {"3d", "animation", "blender", "daz", "sfm", "动画"},
    "制服/角色扮演": {"cosplay", "jk", "maid", "schoolgirl", "uniform", "制服", "女仆", "角色扮演"},
    "乳系": {"bigbreasts", "bigboobs", "boobs", "breasts", "tits", "巨乳", "乳"},
    "口交": {"blowjob", "deepthroat", "oral", "口交", "深喉"},
    "马眼/尿道/龟头": {"glans", "glansjob", "sounding", "urethra", "尿道", "马眼", "龟头"},
    "ASMR/音声": {"asmr", "audio", "音声"},
    "游戏同人": {"game", "gamecg", "hgame", "游戏", "同人"},
    "反差/泄密/探花": {"leak", "leaked", "private", "反差", "探花", "泄密", "流出"},
}


def discover_history_sources(
    *,
    home: Path | None = None,
    appdata: Path | None = None,
    localappdata: Path | None = None,
    platform_name: str | None = None,
) -> list[HistorySource]:
    platform_name = platform_name or ("windows" if __import__("os").name == "nt" else "macos")
    home = home or Path.home()
    candidates: list[tuple[str, Path]] = []
    if platform_name == "windows":
        appdata = appdata or home / "AppData" / "Roaming"
        localappdata = localappdata or home / "AppData" / "Local"
        candidates.extend(
            [
                ("firefox", appdata / "Mozilla" / "Firefox" / "Profiles"),
                ("zen", appdata / "zen" / "Profiles"),
                ("chrome", localappdata / "Google" / "Chrome" / "User Data"),
            ]
        )
    else:
        candidates.extend(
            [
                ("firefox", home / "Library" / "Application Support" / "Firefox" / "Profiles"),
                ("zen", home / "Library" / "Application Support" / "zen" / "Profiles"),
                ("chrome", home / "Library" / "Application Support" / "Google" / "Chrome"),
            ]
        )

    found: list[HistorySource] = []
    for browser, root in candidates:
        if not root.is_dir():
            continue
        filename = "History" if browser == "chrome" else "places.sqlite"
        for path in root.glob(f"*/{filename}"):
            if path.is_file():
                found.append(HistorySource(browser, path.parent.name, path))
    if platform_name == "macos":
        safari = home / "Library" / "Safari" / "History.db"
        if safari.is_file():
            found.append(HistorySource("safari", "iCloud", safari))
    return sorted(found, key=lambda source: (source.browser, source.profile.casefold()))


def _readonly_uri(path: Path) -> str:
    return f"file:{path.resolve().as_posix()}?mode=ro"


def _consistent_copy(source: Path, destination: Path) -> None:
    with closing(sqlite3.connect(_readonly_uri(source), uri=True)) as source_db:
        with closing(sqlite3.connect(destination)) as destination_db:
            source_db.backup(destination_db)


def _iso_from_unix_microseconds(value: int | float) -> str:
    return datetime.fromtimestamp(float(value) / 1_000_000, UTC).isoformat()


def _iso_from_chrome(value: int | float) -> str:
    return (datetime(1601, 1, 1, tzinfo=UTC) + timedelta(microseconds=float(value))).isoformat()


def _iso_from_safari(value: int | float) -> str:
    return (datetime(2001, 1, 1, tzinfo=UTC) + timedelta(seconds=float(value))).isoformat()


def _read_visits(snapshot: Path, browser: str) -> list[HistoryVisit]:
    with closing(sqlite3.connect(snapshot)) as db:
        if browser in {"firefox", "zen"}:
            rows = db.execute(
                "SELECT v.id, v.visit_date, p.url, COALESCE(p.title, '') "
                "FROM moz_historyvisits v JOIN moz_places p ON p.id = v.place_id "
                "WHERE v.visit_date IS NOT NULL AND p.url IS NOT NULL"
            )
            convert = _iso_from_unix_microseconds
        elif browser == "chrome":
            rows = db.execute(
                "SELECT v.id, v.visit_time, u.url, COALESCE(u.title, '') "
                "FROM visits v JOIN urls u ON u.id = v.url "
                "WHERE v.visit_time IS NOT NULL AND u.url IS NOT NULL"
            )
            convert = _iso_from_chrome
        elif browser == "safari":
            rows = db.execute(
                "SELECT v.id, v.visit_time, i.url, COALESCE(v.title, '') "
                "FROM history_visits v JOIN history_items i ON i.id = v.history_item "
                "WHERE v.visit_time IS NOT NULL AND i.url IS NOT NULL"
            )
            convert = _iso_from_safari
        else:
            raise ValueError(f"不支持的浏览器类型：{browser}")
        return [HistoryVisit(str(row[0]), convert(row[1]), row[2], row[3]) for row in rows]


def _source_key(source: HistorySource, host: str) -> str:
    identity = f"{host}\0{source.browser}\0{source.profile}\0{source.path.resolve()}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _prepare_store(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS history_source (
            source_key TEXT PRIMARY KEY,
            browser TEXT NOT NULL,
            profile TEXT NOT NULL,
            host TEXT NOT NULL,
            path_hash TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS history_visit (
            source_key TEXT NOT NULL REFERENCES history_source(source_key),
            visit_key TEXT NOT NULL,
            visited_at TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            PRIMARY KEY (source_key, visit_key)
        );
        CREATE INDEX IF NOT EXISTS history_visit_time_idx ON history_visit(visited_at);
        """
    )


def refresh_history(
    sources: list[HistorySource],
    store_path: Path,
    *,
    host: str | None = None,
) -> list[dict[str, object]]:
    host = host or socket.gethostname()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    results: list[dict[str, object]] = []
    with closing(sqlite3.connect(store_path)) as store:
        _prepare_store(store)
        for source in sources:
            with tempfile.TemporaryDirectory(prefix="peach-history-") as temp_dir:
                snapshot = Path(temp_dir) / "history.sqlite"
                _consistent_copy(source.path, snapshot)
                visits = _read_visits(snapshot, source.browser)
            source_key = _source_key(source, host)
            path_hash = hashlib.sha256(str(source.path.resolve()).encode("utf-8")).hexdigest()
            store.execute(
                "INSERT INTO history_source VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(source_key) DO UPDATE SET last_seen_at=excluded.last_seen_at",
                (source_key, source.browser, source.profile, host, path_hash, now, now),
            )
            before = store.total_changes
            store.executemany(
                "INSERT OR IGNORE INTO history_visit(source_key, visit_key, visited_at, url, title) "
                "VALUES (?, ?, ?, ?, ?)",
                ((source_key, visit.visit_key, visit.visited_at, visit.url, visit.title) for visit in visits),
            )
            added = store.total_changes - before
            results.append(
                {"browser": source.browser, "profile": source.profile, "visits": len(visits), "added": added}
            )
        store.commit()
    return results


def _tokens(value: str) -> set[str]:
    decoded = unquote(value).casefold().replace("_", " ").replace("-", " ")
    values = re.findall(r"[a-z0-9]{2,}|[\u3400-\u9fff]{1,12}", decoded)
    return {value for value in values if value not in STOPWORDS and not value.isdigit()}


def _is_taste_domain(domain: str) -> bool:
    return any(domain == suffix or domain.endswith(f".{suffix}") for suffix in TASTE_DOMAIN_SUFFIXES)


def _creator_candidate(value: str) -> str | None:
    candidate = unquote(value).casefold().strip("@ ")
    if candidate in RESERVED_HANDLES or candidate.isdigit() or not (3 <= len(candidate) <= 80):
        return None
    if re.fullmatch(r"[0-9a-f]{24,}", candidate):
        return None
    if not re.fullmatch(r"[a-z0-9._-]+|[\u3400-\u9fff][\u3400-\u9fff·._-]*", candidate):
        return None
    return candidate


def _url_candidates(url: str) -> tuple[str | None, set[str], set[str]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None, set(), set()
    domain = (parsed.hostname or "").casefold()
    if domain.startswith("www."):
        domain = domain[4:]
    if not _is_taste_domain(domain):
        return domain or None, set(), set()
    tags: set[str] = set()
    for key, values in parse_qs(parsed.query).items():
        if key.casefold() in QUERY_KEYS:
            for value in values:
                tags.update(_tokens(value))

    segments = [unquote(segment).casefold() for segment in parsed.path.split("/") if segment]
    creators: set[str] = set()
    for index, segment in enumerate(segments[:-1]):
        candidate = _creator_candidate(segments[index + 1])
        if segment in CREATOR_MARKERS and candidate:
            creators.add(candidate)
    if domain in CREATOR_HOSTS and segments:
        if domain != "rule34video.com" or segments[0] in {"model", "models"}:
            candidate = _creator_candidate(segments[-1] if domain == "rule34video.com" else segments[0])
            if candidate:
                creators.add(candidate)
    return domain or None, tags, creators


def analyze_history(store_path: Path, output_dir: Path, *, since: str | None = None) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    query = (
        "SELECT v.source_key, v.visited_at, v.url, s.browser, s.profile "
        "FROM history_visit v JOIN history_source s ON s.source_key = v.source_key"
    )
    params: tuple[str, ...] = ()
    if since:
        query += " WHERE v.visited_at >= ?"
        params = (since,)
    domains: Counter[str] = Counter()
    tag_visits: Counter[str] = Counter()
    creator_visits: Counter[str] = Counter()
    tag_urls: dict[str, set[str]] = defaultdict(set)
    creator_urls: dict[str, set[str]] = defaultdict(set)
    tag_sources: dict[str, set[str]] = defaultdict(set)
    creator_sources: dict[str, set[str]] = defaultdict(set)
    category_visits: Counter[str] = Counter()
    min_time: str | None = None
    max_time: str | None = None
    total = 0
    with closing(sqlite3.connect(store_path)) as db:
        source_count = db.execute("SELECT COUNT(*) FROM history_source").fetchone()[0]
        for source_key, visited_at, url, browser, profile in db.execute(query, params):
            total += 1
            min_time = visited_at if min_time is None or visited_at < min_time else min_time
            max_time = visited_at if max_time is None or visited_at > max_time else max_time
            domain, tags, creators = _url_candidates(url)
            if domain:
                domains[domain] += 1
            url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
            source_label = f"{browser}:{profile}"
            for tag in tags:
                tag_visits[tag] += 1
                tag_urls[tag].add(url_hash)
                tag_sources[tag].add(source_label)
                compact = tag.replace(" ", "")
                for category, terms in CATEGORY_TERMS.items():
                    if compact in terms or tag in terms:
                        category_visits[category] += 1
            for creator in creators:
                creator_visits[creator] += 1
                creator_urls[creator].add(url_hash)
                creator_sources[creator].add(source_label)

    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    tag_path = output_dir / f"taste-tag-candidates-{stamp}.csv"
    creator_path = output_dir / f"taste-creator-candidates-{stamp}.csv"
    report_path = output_dir / f"taste-report-{stamp}.md"
    _write_candidates(tag_path, "tag", tag_visits, tag_urls, tag_sources)
    _write_candidates(creator_path, "creator", creator_visits, creator_urls, creator_sources)

    lines = [
        "# 浏览记录口味分析",
        "",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 范围：{min_time or '无'} 至 {max_time or '无'}",
        f"- 访问记录：{total:,}",
        f"- 数据源：{source_count}",
        "- 隐私：报告不含完整 URL、页面标题或原始搜索记录；所有结论均为 candidate。",
        "",
    ]
    _append_ranking(lines, "口味维度候选", category_visits)
    _append_ranking(lines, "Tag 候选", tag_visits)
    _append_ranking(lines, "创作者候选", creator_visits)
    _append_ranking(lines, "高频域名", domains)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "visits": total,
        "sources": source_count,
        "range_start": min_time,
        "range_end": max_time,
        "report": str(report_path),
        "tags": str(tag_path),
        "creators": str(creator_path),
    }


def _write_candidates(
    path: Path,
    kind: str,
    visits: Counter[str],
    urls: dict[str, set[str]],
    sources: dict[str, set[str]],
) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate", "kind", "visits", "distinct_urls", "source_count", "sources", "status"],
        )
        writer.writeheader()
        for candidate, count in visits.most_common():
            writer.writerow(
                {
                    "candidate": candidate,
                    "kind": kind,
                    "visits": count,
                    "distinct_urls": len(urls[candidate]),
                    "source_count": len(sources[candidate]),
                    "sources": " | ".join(sorted(sources[candidate])),
                    "status": "candidate",
                }
            )


def _append_ranking(lines: list[str], title: str, values: Counter[str], limit: int = 30) -> None:
    lines.extend([f"## {title}", "", "| 候选 | 访问次数 |", "| --- | ---: |"])
    if values:
        lines.extend(f"| {name.replace('|', '\\|')} | {count:,} |" for name, count in values.most_common(limit))
    else:
        lines.append("| 未提取到 | 0 |")
    lines.append("")


def write_manifest(path: Path, refresh_results: list[dict[str, object]], analysis: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "refresh": refresh_results,
        "analysis": analysis,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
