from __future__ import annotations

import csv
import hashlib
import json
import re
import socket
import sqlite3
import tempfile
import zipfile
import math
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from browserexport.parse import read_visits as read_browser_visits
from browserexport.browsers.chrome import Chrome
from browserexport.browsers.firefox import Firefox
from browserexport.browsers.safari import Safari


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
TAKEOUT_HISTORY_MEMBER = "Takeout/Chrome/History.json"
TAKEOUT_ACTIVITY_MEMBERS = (
    ("chrome", "Google My Activity - Chrome", "Takeout/My Activity/Chrome/MyActivity.html"),
    ("google_activity", "Google My Activity - Search", "Takeout/My Activity/Search/MyActivity.html"),
    ("google_activity", "Google My Activity - Image Search", "Takeout/My Activity/Image Search/MyActivity.html"),
    ("google_activity", "Google My Activity - Video Search", "Takeout/My Activity/Video Search/MyActivity.html"),
)
TAKEOUT_ACTIVITY_ACTIONS = {"Visited", "Searched for", "Viewed", "Watched"}
TAKEOUT_DATE_RE = re.compile(
    r"^(?P<date>[A-Z][a-z]{2} \d{1,2}, \d{4}, \d{1,2}:\d{2}:\d{2}\s+[AP]M) (?P<zone>HKT|UTC|GMT)$"
)
HONG_KONG_TIMEZONE = timezone(timedelta(hours=8), name="HKT")


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


def _read_visits(snapshot: Path, _browser: str | None = None) -> list[HistoryVisit]:
    """Use browserexport's maintained schema adapters and keep Peach's private DTO.

    The source database is already a consistent SQLite backup when this is called for a
    running browser.  Exported JSON/JSONL and compressed files can be passed directly.
    """
    occurrences: Counter[tuple[str, str]] = Counter()
    visits: list[HistoryVisit] = []

    def consume(source, browser: str | None = None) -> None:
        known = {"chrome": Chrome, "firefox": Firefox, "zen": Firefox, "safari": Safari}
        iterator = known[browser].extract_visits(source) if browser in known else read_browser_visits(source)
        for visit in iterator:
            visited = visit.dt
            if visited.tzinfo is None:
                visited = visited.replace(tzinfo=UTC)
            visited_at = visited.astimezone(UTC).isoformat()
            url = str(visit.url)
            fingerprint = (url, visited_at)
            occurrences[fingerprint] += 1
            ordinal = occurrences[fingerprint]
            visit_key = hashlib.sha256(
                f"{visited_at}\0{url}\0{ordinal}".encode("utf-8")
            ).hexdigest()
            title = ""
            if visit.metadata is not None:
                title = str(visit.metadata.title or "")
            visits.append(HistoryVisit(visit_key, visited_at, url, title))

    try:
        with snapshot.open("rb") as handle:
            is_sqlite = handle.read(16) == b"SQLite format 3\x00"
    except OSError:
        is_sqlite = False
    if is_sqlite:
        # browserexport 0.4.4 accepts an owned connection.  Passing a path uses a
        # context manager that commits but does not close sqlite3.Connection on Windows.
        with closing(sqlite3.connect(_readonly_uri(snapshot), uri=True)) as connection:
            consume(connection, _browser)
    else:
        consume(snapshot)
    return visits


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


def _normalize_takeout_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.hostname in {"google.com", "www.google.com"} and parsed.path == "/url":
        query = parse_qs(parsed.query)
        for key in ("q", "url"):
            if query.get(key):
                return query[key][0]
    return value


def _parse_takeout_date(value: str) -> datetime:
    match = TAKEOUT_DATE_RE.fullmatch(value.replace("\u202f", " "))
    if not match:
        raise ValueError("Google My Activity 时间格式无法识别")
    naive = datetime.strptime(match.group("date"), "%b %d, %Y, %I:%M:%S %p")
    source_timezone = HONG_KONG_TIMEZONE if match.group("zone") == "HKT" else UTC
    return naive.replace(tzinfo=source_timezone).astimezone(UTC)


class _TakeoutActivityParser(HTMLParser):
    def __init__(self, *, visit_prefix: str) -> None:
        super().__init__()
        self.visit_prefix = visit_prefix
        self.depth = 0
        self.card_number = 0
        self.pending_visit = False
        self.in_target = False
        self.href: str | None = None
        self.title_parts: list[str] = []
        self.date_text: str | None = None
        self.visits: list[HistoryVisit] = []
        self.errors = 0
        self.matched_action = False
        self.skipped = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "div" and self.depth == 0 and "outer-cell" in (values.get("class") or "").split():
            self.depth = 1
            self.pending_visit = False
            self.in_target = False
            self.href = None
            self.title_parts = []
            self.date_text = None
            self.matched_action = False
            return
        if not self.depth:
            return
        if tag == "div":
            self.depth += 1
        elif tag == "a" and self.pending_visit and self.href is None:
            self.in_target = True
            self.href = values.get("href")

    def handle_endtag(self, tag: str) -> None:
        if self.depth and tag == "a" and self.in_target:
            self.in_target = False
            self.pending_visit = False
        if not self.depth or tag != "div":
            return
        self.depth -= 1
        if self.depth:
            return
        self.card_number += 1
        if self.href is None or self.date_text is None:
            if self.matched_action:
                self.skipped += 1
            return
        try:
            visited = _parse_takeout_date(self.date_text)
        except ValueError:
            self.errors += 1
            return
        url = _normalize_takeout_url(self.href)
        if urlparse(url).scheme not in {"http", "https"}:
            self.errors += 1
            return
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        self.visits.append(
            HistoryVisit(
                f"{self.visit_prefix}:{self.card_number}:{int(visited.timestamp())}:{digest}",
                visited.isoformat(),
                url,
                " ".join(self.title_parts).strip(),
            )
        )

    def handle_data(self, data: str) -> None:
        if not self.depth:
            return
        value = data.strip()
        if value in TAKEOUT_ACTIVITY_ACTIONS:
            self.matched_action = True
            self.pending_visit = True
        elif self.in_target and value:
            self.title_parts.append(value)
        elif value.endswith((" HKT", " UTC", " GMT")) and len(value) >= 20:
            self.date_text = value


def _read_takeout_archive(path: Path) -> list[tuple[str, str, list[HistoryVisit], int]]:
    with zipfile.ZipFile(path) as archive:
        members = set(archive.namelist())
        if TAKEOUT_HISTORY_MEMBER not in members and not any(
            member in members for _browser, _profile, member in TAKEOUT_ACTIVITY_MEMBERS
        ):
            raise ValueError("Takeout 未包含可识别的浏览或搜索活动")
        history_visits: list[HistoryVisit] = []
        if TAKEOUT_HISTORY_MEMBER in members:
            history_payload = json.loads(archive.read(TAKEOUT_HISTORY_MEMBER))
            history_rows = history_payload.get("Browser History")
            if not isinstance(history_rows, list):
                raise ValueError("Takeout Chrome History 缺少 Browser History 列表")
            for index, row in enumerate(history_rows, 1):
                if not isinstance(row, dict) or not row.get("url") or row.get("time_usec") is None:
                    raise ValueError("Takeout Chrome History 含无效记录")
                url = str(row["url"])
                time_usec = int(row["time_usec"])
                digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
                history_visits.append(
                    HistoryVisit(
                        f"history:{index}:{time_usec}:{digest}",
                        _iso_from_unix_microseconds(time_usec),
                        url,
                        str(row.get("title") or ""),
                    )
                )
        sources: list[tuple[str, str, list[HistoryVisit], int]] = []
        if history_visits:
            sources.append(("chrome", "Takeout Browser History", history_visits, 0))
        for browser, profile, member in TAKEOUT_ACTIVITY_MEMBERS:
            if member not in members:
                continue
            activity = _TakeoutActivityParser(visit_prefix=hashlib.sha256(member.encode()).hexdigest()[:10])
            activity.feed(archive.read(member).decode("utf-8"))
            activity.close()
            if activity.errors:
                raise ValueError(f"{profile} 含无法解析的活动记录：{activity.errors}")
            sources.append((browser, profile, activity.visits, activity.skipped))
    return sources


def _event_fingerprint(url: str, visited_at: str) -> tuple[str, int]:
    return url, int(datetime.fromisoformat(visited_at).timestamp())


def refresh_takeout_history(
    archives: list[Path],
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
        existing = Counter(
            _event_fingerprint(url, visited_at)
            for visited_at, url in store.execute(
                "SELECT v.visited_at, v.url FROM history_visit v "
                "JOIN history_source s ON s.source_key = v.source_key"
            )
        )
        for archive_path in archives:
            for browser, profile, visits, skipped in _read_takeout_archive(archive_path):
                source = HistorySource(browser, profile, archive_path)
                source_key = _source_key(source, host)
                path_hash = hashlib.sha256(str(archive_path.resolve()).encode("utf-8")).hexdigest()
                store.execute(
                    "INSERT INTO history_source VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(source_key) DO UPDATE SET last_seen_at=excluded.last_seen_at",
                    (source_key, source.browser, source.profile, host, path_hash, now, now),
                )
                source_seen: Counter[tuple[str, int]] = Counter()
                additions: list[HistoryVisit] = []
                for visit in visits:
                    fingerprint = _event_fingerprint(visit.url, visit.visited_at)
                    source_seen[fingerprint] += 1
                    if source_seen[fingerprint] > existing[fingerprint]:
                        additions.append(visit)
                before = store.total_changes
                store.executemany(
                    "INSERT OR IGNORE INTO history_visit(source_key, visit_key, visited_at, url, title) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ((source_key, visit.visit_key, visit.visited_at, visit.url, visit.title) for visit in additions),
                )
                added = store.total_changes - before
                for fingerprint, count in source_seen.items():
                    existing[fingerprint] = max(existing[fingerprint], count)
                results.append(
                    {
                        "browser": browser,
                        "profile": profile,
                        "visits": len(visits),
                        "added": added,
                        "skipped": skipped,
                    }
                )
        store.commit()
    return results


def refresh_export_history(
    exports: list[Path],
    store_path: Path,
    *,
    host: str | None = None,
) -> list[dict[str, object]]:
    """Import browserexport SQLite/JSON/JSONL (including compressed variants).

    Raw exports stay in the private sources directory.  Only normalized visits enter the
    private history store; no URL or title is copied to the Peach ledger.
    """
    host = host or socket.gethostname()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    results: list[dict[str, object]] = []
    with closing(sqlite3.connect(store_path)) as store:
        _prepare_store(store)
        for export_path in exports:
            visits = _read_visits(export_path)
            source = HistorySource("browserexport", export_path.name, export_path)
            source_key = _source_key(source, host)
            path_hash = hashlib.sha256(str(export_path.resolve()).encode("utf-8")).hexdigest()
            store.execute(
                "INSERT INTO history_source VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(source_key) DO UPDATE SET last_seen_at=excluded.last_seen_at",
                (source_key, source.browser, source.profile, host, path_hash, now, now),
            )
            before = store.total_changes
            store.executemany(
                "INSERT OR IGNORE INTO history_visit(source_key, visit_key, visited_at, url, title) "
                "VALUES (?, ?, ?, ?, ?)",
                ((source_key, visit.visit_key, visit.visited_at, visit.url, visit.title)
                 for visit in visits),
            )
            results.append({
                "browser": source.browser,
                "profile": source.profile,
                "visits": len(visits),
                "added": store.total_changes - before,
                "skipped": 0,
            })
        store.commit()
    return results


def import_history_exports(
    exports: list[Path],
    store_path: Path,
    *,
    host: str | None = None,
) -> list[dict[str, object]]:
    """Route Google Takeout archives and browserexport-compatible files."""
    results: list[dict[str, object]] = []
    for export_path in exports:
        is_takeout = False
        if zipfile.is_zipfile(export_path):
            with zipfile.ZipFile(export_path) as archive:
                members = set(archive.namelist())
                is_takeout = TAKEOUT_HISTORY_MEMBER in members or any(
                    member in members for _browser, _profile, member in TAKEOUT_ACTIVITY_MEMBERS
                )
        if is_takeout:
            results.extend(refresh_takeout_history([export_path], store_path, host=host))
        else:
            results.extend(refresh_export_history([export_path], store_path, host=host))
    return results


def remove_history_source(store_path: Path, source_key: str) -> int:
    """Remove one normalized source while retaining the immutable raw export."""
    if not store_path.is_file():
        return 0
    with closing(sqlite3.connect(store_path)) as store:
        _prepare_store(store)
        row = store.execute(
            "SELECT count(*) FROM history_visit WHERE source_key=?", (source_key,),
        ).fetchone()
        removed = int(row[0]) if row else 0
        store.execute("DELETE FROM history_visit WHERE source_key=?", (source_key,))
        store.execute("DELETE FROM history_source WHERE source_key=?", (source_key,))
        store.commit()
    return removed


def _history_dashboard_evidence(store_path: Path, since: str | None) -> dict[str, object]:
    empty = {
        "visits": 0, "sources": [], "range_start": None, "range_end": None,
        "tags": Counter(), "creators": Counter(), "categories": Counter(),
        "domains": Counter(),
    }
    if not store_path.is_file():
        return empty
    with closing(sqlite3.connect(store_path)) as store:
        store.row_factory = sqlite3.Row
        try:
            source_rows = [dict(row) for row in store.execute(
                "SELECT s.source_key,s.browser,s.profile,s.host,s.first_seen_at,s.last_seen_at,"
                "count(v.visit_key) visits,min(v.visited_at) range_start,max(v.visited_at) range_end "
                "FROM history_source s LEFT JOIN history_visit v ON v.source_key=s.source_key "
                "GROUP BY s.source_key ORDER BY s.last_seen_at DESC,s.browser,s.profile"
            )]
            query = (
                "SELECT v.visited_at,v.url FROM history_visit v "
                "JOIN history_source s ON s.source_key=v.source_key"
            )
            params: tuple[str, ...] = ()
            if since:
                query += " WHERE v.visited_at>=?"
                params = (since,)
            rows = store.execute(query, params)
        except sqlite3.DatabaseError:
            return empty

        tags: Counter[str] = Counter()
        creators: Counter[str] = Counter()
        categories: Counter[str] = Counter()
        domains: Counter[str] = Counter()
        seen: set[tuple[str, int]] = set()
        range_start: str | None = None
        range_end: str | None = None
        visits = 0
        for row in rows:
            visited_at, url = str(row["visited_at"]), str(row["url"])
            try:
                fingerprint = (url, int(datetime.fromisoformat(visited_at).timestamp()))
            except ValueError:
                continue
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            visits += 1
            range_start = visited_at if range_start is None or visited_at < range_start else range_start
            range_end = visited_at if range_end is None or visited_at > range_end else range_end
            domain, row_tags, row_creators = _url_candidates(url)
            if domain and _is_taste_domain(domain):
                domains[domain] += 1
            tags.update(row_tags)
            creators.update(row_creators)
            for tag in row_tags:
                compact = tag.replace(" ", "")
                for category, terms in CATEGORY_TERMS.items():
                    if compact in terms or tag in terms:
                        categories[category] += 1
        return {
            "visits": visits,
            "sources": source_rows,
            "range_start": range_start,
            "range_end": range_end,
            "tags": tags,
            "creators": creators,
            "categories": categories,
            "domains": domains,
        }


def _epoch(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None


def _peach_dashboard_evidence(connection: sqlite3.Connection, since: str | None) -> dict[str, object]:
    since_epoch = datetime.fromisoformat(since).timestamp() if since else None
    rows = connection.execute(
        "SELECT a.id,a.creator,a.studio,a.play_count,a.play_seconds,a.o_count,a.rating,"
        "a.feedback,a.last_played,COALESCE(p.liked,0) liked "
        "FROM asset a LEFT JOIN asset_preference p ON p.asset_id=a.id AND p.profile_id='local-default' "
        "WHERE COALESCE(a.play_count,0)>0 OR COALESCE(a.play_seconds,0)>0 "
        "OR COALESCE(a.o_count,0)>0 OR COALESCE(a.rating,0)>0 "
        "OR a.feedback IN ('seen','dislike') OR COALESCE(p.liked,0)>0"
    ).fetchall()
    assets: dict[int, dict[str, object]] = {}
    total_seconds = 0.0
    liked = disliked = 0
    for raw in rows:
        row = dict(raw)
        played_at = _epoch(row.get("last_played"))
        if since_epoch is not None and (played_at is None or played_at < since_epoch):
            continue
        seconds = max(float(row.get("play_seconds") or 0), 0)
        plays = max(int(row.get("play_count") or 0), 0)
        o_count = max(int(row.get("o_count") or 0), 0)
        rating = max(int(row.get("rating") or 0), 0)
        is_liked = bool(row.get("liked"))
        is_disliked = row.get("feedback") == "dislike"
        positive = (1.0 if plays or seconds else 0.0) + math.log2(1 + seconds / 60)
        positive += min(plays, 12) * .75 + min(o_count, 8) * 1.5 + rating / 20
        positive += 3.0 if is_liked else 0.0
        positive += .5 if row.get("feedback") == "seen" else 0.0
        row["positive"] = max(positive, 0.0)
        row["negative"] = 1.0 if is_disliked else 0.0
        assets[int(row["id"])] = row
        total_seconds += seconds
        liked += int(is_liked)
        disliked += int(is_disliked)

    scores: dict[str, Counter[str]] = defaultdict(Counter)
    negatives: dict[str, Counter[str]] = defaultdict(Counter)
    items: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    labels: dict[str, dict[str, str]] = defaultdict(dict)
    entity_kinds: dict[int, set[str]] = defaultdict(set)
    if assets:
        ids = list(assets)
        for offset in range(0, len(ids), 800):
            batch = ids[offset:offset + 800]
            placeholders = ",".join("?" for _ in batch)
            entity_rows = connection.execute(
                "SELECT ae.asset_id,e.kind,e.canonical_name,e.normalized_name "
                f"FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id IN ({placeholders})",
                batch,
            )
            for entity in entity_rows:
                aid = int(entity["asset_id"])
                kind = str(entity["kind"])
                normalized = str(entity["normalized_name"] or entity["canonical_name"]).casefold()
                labels[kind][normalized] = str(entity["canonical_name"])
                entity_kinds[aid].add(kind)
                if assets[aid]["positive"]:
                    scores[kind][normalized] += float(assets[aid]["positive"])
                    items[kind][normalized].add(aid)
                if assets[aid]["negative"]:
                    negatives[kind][normalized] += 1

        for aid, asset in assets.items():
            for kind, column in (("creator", "creator"), ("studio", "studio")):
                value = str(asset.get(column) or "").strip()
                if not value or kind in entity_kinds[aid]:
                    continue
                normalized = value.casefold()
                labels[kind][normalized] = value
                if asset["positive"]:
                    scores[kind][normalized] += float(asset["positive"])
                    items[kind][normalized].add(aid)
                if asset["negative"]:
                    negatives[kind][normalized] += 1

    tagged = sum("tag" in entity_kinds[aid] for aid in assets)
    identified = sum(bool(entity_kinds[aid] & {"creator", "performer"}) for aid in assets)
    return {
        "assets": len(assets), "seconds": total_seconds, "liked": liked, "disliked": disliked,
        "scores": scores, "negatives": negatives, "items": items, "labels": labels,
        "coverage": {
            "tagged": tagged, "identified": identified,
            "untagged": len(assets) - tagged, "unidentified": len(assets) - identified,
        },
    }


def _rank_combined(
    kind: str,
    web_values: Counter[str],
    peach: dict[str, object],
    *,
    limit: int = 30,
) -> list[dict[str, object]]:
    scores = peach["scores"].get(kind, Counter())
    labels = peach["labels"].get(kind, {})
    item_sets = peach["items"].get(kind, {})
    normalized_web: Counter[str] = Counter()
    web_labels: dict[str, str] = {}
    for label, count in web_values.items():
        normalized = label.casefold().strip()
        normalized_web[normalized] += count
        web_labels.setdefault(normalized, label)
    rows: list[dict[str, object]] = []
    for normalized in set(scores) | set(normalized_web):
        web_visits = int(normalized_web[normalized])
        peach_score = float(scores[normalized])
        combined = peach_score + math.log2(1 + web_visits) * 2.0
        rows.append({
            "name": labels.get(normalized) or web_labels.get(normalized) or normalized,
            "score": round(combined, 2),
            "web_visits": web_visits,
            "peach_score": round(peach_score, 2),
            "peach_items": len(item_sets.get(normalized, set())),
            "evidence": [source for source, present in (
                ("浏览记录", web_visits > 0), ("Peach", peach_score > 0),
            ) if present],
        })
    rows.sort(key=lambda row: (-float(row["score"]), -int(row["web_visits"]), str(row["name"])))
    return rows[:limit]


def build_taste_dashboard(
    history_store: Path,
    ledger_connection: sqlite3.Connection,
    *,
    since: str | None = None,
) -> dict[str, object]:
    """Build a privacy-bounded, read-only taste view from both evidence stores."""
    history = _history_dashboard_evidence(history_store, since)
    peach = _peach_dashboard_evidence(ledger_connection, since)
    tags = _rank_combined("tag", history["tags"], peach)
    creators = _rank_combined("creator", history["creators"], peach)
    performers = _rank_combined("performer", Counter(), peach)

    category_scores: Counter[str] = Counter(history["categories"])
    for row in tags:
        compact = str(row["name"]).casefold().replace(" ", "")
        for category, terms in CATEGORY_TERMS.items():
            if compact in terms:
                category_scores[category] += max(1, round(float(row["peach_score"])))

    gaps = [row for row in tags if row["web_visits"] >= 2 and not row["peach_items"]][:12]
    negative_tags = []
    for normalized, count in peach["negatives"].get("tag", Counter()).most_common(12):
        negative_tags.append({
            "name": peach["labels"].get("tag", {}).get(normalized, normalized),
            "disliked_items": count,
        })
    return {
        "summary": {
            "history_visits": history["visits"],
            "history_sources": len(history["sources"]),
            "peach_items": peach["assets"],
            "peach_seconds": round(float(peach["seconds"])),
            "liked": peach["liked"],
            "disliked": peach["disliked"],
            "range_start": history["range_start"],
            "range_end": history["range_end"],
        },
        "sources": history["sources"],
        "rankings": {
            "categories": [{"name": name, "score": score}
                           for name, score in category_scores.most_common(20)],
            "tags": tags,
            "creators": creators,
            "performers": performers,
            "domains": [{"name": name, "visits": count}
                        for name, count in history["domains"].most_common(20)],
            "negative_tags": negative_tags,
        },
        "coverage": peach["coverage"],
        "gaps": gaps,
        "privacy": {
            "raw_history_local_only": True,
            "ledger_unchanged": True,
            "candidate_only": True,
        },
    }


def read_creator_candidates(output_dir: Path, limit: int = 200) -> list[dict]:
    """读最新一批创作者候选，按访问次数从多到少。

    只读，不联网、不重跑分析。取最新那个文件而不是合并全部：每次分析都是对当时
    全量历史的重算，旧文件是快照不是增量，合起来只会把同一个人算两遍。
    """
    try:
        files = sorted(Path(output_dir).glob("taste-creator-candidates-*.csv"))
    except OSError:
        return []
    if not files:
        return []
    rows: list[dict] = []
    try:
        with files[-1].open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                name = (row.get("candidate") or "").strip()
                if not name:
                    continue
                try:
                    visits = int(row.get("visits") or 0)
                except ValueError:
                    visits = 0
                rows.append({
                    "name": name,
                    "visits": visits,
                    "status": (row.get("status") or "").strip(),
                    "sources": (row.get("sources") or "").strip(),
                })
    except (OSError, csv.Error, UnicodeError):
        return []
    rows.sort(key=lambda item: (-item["visits"], item["name"]))
    return rows[:limit]


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
