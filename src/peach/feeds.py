"""番号发现源：订阅拉取、条目解析、未入库的番号壳（ADR-0042）。

Feed 只回答一个问题——最近出了哪些番号。一次拉取的全部产物是一条「这个源见过这个条目」
的记录和一条「这个番号还没入库」的记录；不下载种子、不下载 enclosure、不建目录、
不碰任何媒体文件。

解析用标准库 `xml.etree`，不为这件事引 feedparser：这里只需要 RSS 2.0 与 Atom 里的四个
字段，而多一个依赖要一直跟着升级和审计。代价是日期格式与命名空间得自己认，都在本模块里。

**解析只吃已下载的字节**，地址由调用方自己取（`peach.http` 的 transport 加主机限流）。
把地址交给一个会自己发 HTTP 的解析器，等于绕过项目的代理、限流、超时与预算闸门。
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from xml.etree import ElementTree

from .catalog_rules import normalise_code_key, release_code_from_text
from .entities import normalize_entity_name

#: 原生 RSS/Atom。
KIND_RSS = "rss"
#: JavDB 演员页当伪 Feed 抓。它按发行日排在前面，所以「还没发行的作品」会先出现。
KIND_JAVDB_ACTOR = "javdb-actor"
KINDS = (KIND_RSS, KIND_JAVDB_ACTOR)

KIND_LABELS = {KIND_RSS: "RSS / Atom", KIND_JAVDB_ACTOR: "JavDB 演员页"}

#: 拉取间隔的上下界。下界 30 分钟不是性能考虑：JavDB 按出口 IP 计配额，比这更密只会
#: 把配额花在一个一天才更新几条的页面上。
MIN_INTERVAL_MINUTES = 30
MAX_INTERVAL_MINUTES = 7 * 24 * 60
DEFAULT_INTERVAL_MINUTES = 360

#: 一次拉取最多解析多少条。源正常一页几十条，异常的那种（被替换成别的页面、
#: 被镜像站塞进整站索引）会给出几千条，那不该变成几千个壳。
MAX_ENTRIES = 200

#: 一轮拉取最多派多少条刮削后继。真正的上限由 `task_runs.MAX_FOLLOWUPS` 判，
#: 这里先截一刀是为了让第一次订阅不至于把整页历史都排成任务。
MAX_NEW_PER_POLL = 20

_ATOM = "{http://www.w3.org/2005/Atom}"

#: 切词元用的分隔符。标题里的番号被中文剧情简介夹着，整段丢给
#: `release_code_from_text` 认不出来（2026-09-22 实测 sukebei 75 条里只认出 3 条）。
_TOKEN = re.compile(r"[^\s\[\]()（）【】{}、,，/|_+]+")

#: JavDB 演员页的一部作品：`/v/<id>` 是条目身份，`<strong>` 里是干净的番号，
#: `.meta` 是发行日。固件照抓回来的那份 HTML 写，不按记忆重画。
_JAVDB_BOX = re.compile(
    r'<a href="(?P<href>/v/[A-Za-z0-9]+)" class="box"'
    r'.*?<div class="video-title"><strong>(?P<code>[^<]*)</strong>(?P<title>.*?)</div>'
    r'.*?<div class="meta">\s*(?P<date>\d{4}-\d{2}-\d{2})',
    re.S)
_TAGS = re.compile(r"<[^>]+>")


def stamp(moment: datetime | None = None) -> str:
    """ISO-8601 UTC 文本，与 `task_run`、`entity` 同一种写法。"""
    return (moment or datetime.now(timezone.utc)).astimezone(
        timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def scan_code(text: str | None) -> str | None:
    """从一段文本里找出番号：整段先试一次，不成再逐词元试。

    番号的判据一个字都不新写，全部转给 `catalog_rules.release_code_from_text`——
    两份实现漂移会产生两个封面缓存键，那是 `catalog_rules` 自己注释里记着的旧伤。
    这里加的只是「标题里夹着简介时也要能找到」这一层。
    """
    if not text:
        return None
    whole = release_code_from_text(text)
    if whole:
        return whole
    for token in _TOKEN.findall(str(text)):
        found = release_code_from_text(token)
        if found:
            return found
    return None


@dataclass(frozen=True)
class FeedEntry:
    """一条已解析的条目。`item_key` 是这个源内部的去重真值。"""

    item_key: str
    title: str
    link: str | None = None
    published_at: str | None = None

    @property
    def code(self) -> str | None:
        return scan_code(self.title) or None


@dataclass(frozen=True)
class ParsedFeed:
    title: str | None
    entries: tuple[FeedEntry, ...]


def _text(node, *paths: str) -> str | None:
    for path in paths:
        value = node.findtext(path)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _as_utc(moment: datetime) -> str:
    """没带时区的时间按 UTC 读，不按本机时区。

    两种来源都会给出这种值：RSS 的 `-0000` 按 RFC 5322 表示「时区未知」，
    `parsedate_to_datetime` 于是返回 naive；JavDB 的 `.meta` 只有一个日期。
    naive 值交给 `astimezone` 会被当成本机时间，于是同一份 feed 在 UTC+8 的机器上
    整体前移八小时——发行日 2026-10-20 变成 10-19，而排序和「这一天发了什么」都按它算。
    """
    return stamp(moment if moment.tzinfo is not None
                 else moment.replace(tzinfo=timezone.utc))


def _published(value: str | None) -> str | None:
    """RSS 的 RFC 822 与 Atom 的 ISO-8601 都认，认不出就当没有。

    发布时间是排序真值：拿不到它才回退到首次见到的时间。把认不出的日期当成「现在」
    会让一整页历史条目全部挤在同一秒，那之后就再也分不出先后了。
    """
    if not value:
        return None
    raw = value.strip()
    try:
        return _as_utc(parsedate_to_datetime(raw))
    except (TypeError, ValueError):
        pass
    try:
        return _as_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
    except ValueError:
        return None


def parse_feed(body: bytes) -> ParsedFeed | None:
    """RSS 2.0 或 Atom 的字节 → 条目。不是 feed 时返回 None。

    条目为空但文档本身合法不算失败：源这一刻确实没有新东西。
    """
    if not body or not body.strip():
        return None
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return None
    tag = root.tag.split("}")[-1]
    rows: list[FeedEntry] = []
    if tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return None
        for item in channel.findall("item")[:MAX_ENTRIES]:
            title = _text(item, "title") or ""
            link = _text(item, "link")
            key = _text(item, "guid") or link or title
            if not key:
                continue
            rows.append(FeedEntry(key, title, link,
                                  _published(_text(item, "pubDate"))))
        return ParsedFeed(_text(channel, "title"), tuple(rows))
    if tag == "feed":
        for item in root.findall(f"{_ATOM}entry")[:MAX_ENTRIES]:
            title = _text(item, f"{_ATOM}title") or ""
            anchor = item.find(f"{_ATOM}link")
            link = anchor.get("href") if anchor is not None else None
            key = _text(item, f"{_ATOM}id") or link or title
            if not key:
                continue
            rows.append(FeedEntry(key, title, link,
                                  _published(_text(item, f"{_ATOM}published",
                                                   f"{_ATOM}updated"))))
        return ParsedFeed(_text(root, f"{_ATOM}title"), tuple(rows))
    return None


def parse_javdb_actor(html: str, base_url: str) -> ParsedFeed | None:
    """JavDB 演员页 → 条目。一条作品都解不出时返回 None。

    解不出不等于这个人没作品：同一轮里带查询串的地址会回一份 27 KB、一条作品都没有的
    页面（2026-09-22 实测），而不带参数的仍是 78 KB 的完整页。所以这种情况按拉取失败
    报出来，而不是当成「这次没有新作」——后者会把一个坏掉的源伪装成安静的源。
    """
    if not html:
        return None
    rows: list[FeedEntry] = []
    for found in list(_JAVDB_BOX.finditer(html))[:MAX_ENTRIES]:
        href = found.group("href")
        code = found.group("code").strip()
        tail = _TAGS.sub("", found.group("title")).strip()
        title = f"{code} {tail}".strip() if code else tail
        rows.append(FeedEntry(href, title, urljoin(base_url, href),
                              _published(found.group("date"))))
    if not rows:
        return None
    return ParsedFeed(None, tuple(rows))


def parse(kind: str, body: bytes, url: str) -> ParsedFeed | None:
    if kind == KIND_JAVDB_ACTOR:
        return parse_javdb_actor(body.decode("utf-8", "replace"), url)
    return parse_feed(body)


# -- 订阅 ------------------------------------------------------------------


def normalize_url(value: object) -> str:
    """订阅地址只收 HTTPS。

    明文地址在这里没有可用的场景：两类可用来源都是 HTTPS，而 Feed 拉回来的东西会直接
    变成用户看见的新作——中途被改写的内容没有任何一步会被察觉。地址解析到内网的那一层
    由 `http.public_https_url` 在真正发请求时挡住。
    """
    url = str(value or "").strip()
    if not url.startswith("https://"):
        raise ValueError("订阅地址必须以 https:// 开头")
    return url


def normalize_interval(value: object) -> int:
    try:
        minutes = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("拉取间隔必须是整数分钟") from error
    if not MIN_INTERVAL_MINUTES <= minutes <= MAX_INTERVAL_MINUTES:
        raise ValueError(
            f"拉取间隔必须在 {MIN_INTERVAL_MINUTES} 到 {MAX_INTERVAL_MINUTES} 分钟之间")
    return minutes


def add_source(connection: sqlite3.Connection, *, kind: str, url: str, name: str = "",
               entity_id: int | None = None,
               interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
               enabled: bool = True) -> int:
    """登记一条订阅。地址重复直接拒绝——同一个源订两遍只会让同一条新作出现两次。"""
    if kind not in KINDS:
        raise ValueError(f"认不出这种订阅源：{kind}")
    address = normalize_url(url)
    minutes = normalize_interval(interval_minutes)
    if connection.execute("SELECT 1 FROM feed_source WHERE url=?", (address,)).fetchone():
        raise ValueError("这个订阅地址已经在列表里了")
    cursor = connection.execute(
        "INSERT INTO feed_source(kind,name,url,entity_id,enabled,interval_minutes,"
        "created_at) VALUES(?,?,?,?,?,?,?)",
        (kind, str(name or "").strip(), address, entity_id, 1 if enabled else 0,
         minutes, stamp()))
    return int(cursor.lastrowid)


def remove_source(connection: sqlite3.Connection, source_id: int) -> None:
    connection.execute("DELETE FROM feed_source WHERE id=?", (int(source_id),))


def set_enabled(connection: sqlite3.Connection, source_id: int, enabled: bool) -> None:
    connection.execute("UPDATE feed_source SET enabled=? WHERE id=?",
                       (1 if enabled else 0, int(source_id)))


def sources(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        "SELECT s.*, e.canonical_name AS entity_name,"
        " (SELECT count(*) FROM feed_item i WHERE i.source_id=s.id) AS seen"
        " FROM feed_source s LEFT JOIN entity e ON e.id=s.entity_id"
        " ORDER BY s.kind, s.name, s.id").fetchall()
    return [{
        "id": int(row["id"]),
        "kind": row["kind"],
        "kind_label": KIND_LABELS.get(row["kind"], row["kind"]),
        "name": row["name"] or row["entity_name"] or "",
        "url": row["url"],
        "entity_id": row["entity_id"],
        "entity_name": row["entity_name"],
        "enabled": bool(row["enabled"]),
        "interval_minutes": int(row["interval_minutes"]),
        "last_fetched_at": row["last_fetched_at"],
        "next_fetch_at": row["next_fetch_at"],
        "last_error": row["last_error"],
        "last_seen_count": int(row["last_seen_count"]),
        "last_new_count": int(row["last_new_count"]),
        "seen": int(row["seen"] or 0),
    } for row in rows]


def due_sources(connection: sqlite3.Connection, now: str | None = None) -> list[sqlite3.Row]:
    """到期该拉的源。从没拉过的（`next_fetch_at` 为空）总是到期。"""
    moment = now or stamp()
    return list(connection.execute(
        "SELECT * FROM feed_source WHERE enabled=1"
        " AND (next_fetch_at IS NULL OR next_fetch_at<=?) ORDER BY id", (moment,)))


def settle(connection: sqlite3.Connection, source_id: int, *, error: str | None = None,
           etag: str | None = None, last_modified: str | None = None,
           interval_minutes: int, seen: int = 0, new: int = 0,
           now: datetime | None = None) -> None:
    """结算一次拉取。

    失败也按同一间隔排下一次，不做指数退避——退避要么在这里写第二套判据，要么让一个
    临时挡回来的源沉默半天。下次时间在所有返回路径上都写，任何一种结局都不会让源卡住。
    """
    moment = now or datetime.now(timezone.utc)
    connection.execute(
        "UPDATE feed_source SET last_error=?,last_fetched_at=?,next_fetch_at=?,"
        "etag=COALESCE(?,etag),last_modified=COALESCE(?,last_modified),"
        "last_seen_count=?,last_new_count=? WHERE id=?",
        (error, stamp(moment), stamp(moment + timedelta(minutes=interval_minutes)),
         etag, last_modified, int(seen), int(new), int(source_id)))


# -- 条目与壳 --------------------------------------------------------------


def seen_keys(connection: sqlite3.Connection, source_id: int) -> set[str]:
    return {str(row[0]) for row in connection.execute(
        "SELECT item_key FROM feed_item WHERE source_id=?", (int(source_id),))}


def in_library(connection: sqlite3.Connection, code: str) -> bool:
    """这个番号已经入库了没有。

    比的是归一化之后的键：账本里写的是 `SSIS-950`，源里可能给 `ssis00950`，
    按原文比会把同一部片当成两部。`normalise_code_key` 由 `LedgerDatabase.connect`
    注册成 SQL 函数，两侧因此是同一份实现。
    """
    key = normalise_code_key(code)
    if not key:
        return False
    row = connection.execute(
        "SELECT 1 FROM asset WHERE code IS NOT NULL AND normalise_code_key(code)=? LIMIT 1",
        (key,)).fetchone()
    return row is not None


def record_entry(connection: sqlite3.Connection, source_id: int, entry: FeedEntry,
                 *, code: str | None, now: str | None = None) -> bool:
    """记下「这个源见过这一条」。已经见过返回 False。"""
    moment = now or stamp()
    try:
        connection.execute(
            "INSERT INTO feed_item(source_id,item_key,code,title,link,published_at,"
            "first_seen) VALUES(?,?,?,?,?,?,?)",
            (int(source_id), entry.item_key, code, entry.title or None, entry.link,
             entry.published_at, moment))
    except sqlite3.IntegrityError:
        return False
    return True


def create_shell(connection: sqlite3.Connection, code: str, *, source_id: int | None,
                 title: str | None = None, link: str | None = None,
                 release_date: str | None = None,
                 entity_id: int | None = None, now: str | None = None) -> int | None:
    """给一个还没入库的番号建壳。已入库或已有壳时返回 None。

    两层去重里的第二层就在这三行：先查 `asset`，再靠 `code` 上的唯一约束兜住并发。
    """
    if in_library(connection, code):
        return None
    moment = now or stamp()
    try:
        cursor = connection.execute(
            "INSERT INTO feed_discovery(code,source_id,title,link,release_date,"
            "discovered_at) VALUES(?,?,?,?,?,?)",
            (code, source_id, title, link, release_date, moment))
    except sqlite3.IntegrityError:
        return None
    discovery_id = int(cursor.lastrowid)
    if entity_id:
        link_entity(connection, discovery_id, int(entity_id))
    return discovery_id


def link_entity(connection: sqlite3.Connection, discovery_id: int, entity_id: int) -> None:
    connection.execute(
        "INSERT OR IGNORE INTO feed_discovery_entity(discovery_id,entity_id) VALUES(?,?)",
        (int(discovery_id), int(entity_id)))


def match_performers(connection: sqlite3.Connection, names) -> list[int]:
    """按女优名找账本里的实体。正名与别名都查，认不出的名字直接丢掉。

    这里只做关联，不建实体：Feed 发现的是番号，不是人。凭一个来源给的名字往账本里
    加一个人，等于让未经复核的断言变成实体。
    """
    found: list[int] = []
    for name in names or []:
        key = normalize_entity_name(str(name or ""))
        if not key:
            continue
        row = connection.execute(
            "SELECT id FROM entity WHERE kind='performer' AND normalized_name=?",
            (key,)).fetchone()
        if row is None:
            row = connection.execute(
                "SELECT entity_id AS id FROM entity_alias a"
                " JOIN entity e ON e.id=a.entity_id AND e.kind='performer'"
                " WHERE a.normalized_alias=? LIMIT 1", (key,)).fetchone()
        if row is not None and int(row["id"]) not in found:
            found.append(int(row["id"]))
    return found


def poll(connection: sqlite3.Connection, source: sqlite3.Row,
         parsed: ParsedFeed) -> dict:
    """把一次拉取的解析结果落库，返回这一轮的账。

    写入顺序是源给出的倒序：无日期的条目按旧→新拿到递增的 id，于是「没有发布时间」
    的那些在列表里也还排得出先后。建壳仍按源给出的顺序，最新的先排上刮削。
    """
    source_id = int(source["id"])
    entity_id = source["entity_id"]
    already = seen_keys(connection, source_id)
    fresh = [entry for entry in parsed.entries if entry.item_key not in already]
    moment = stamp()
    codes: list[tuple[FeedEntry, str | None]] = []
    for entry in reversed(fresh):
        code = entry.code
        record_entry(connection, source_id, entry, code=code, now=moment)
        codes.append((entry, code))
    created: list[tuple[int, str]] = []
    skipped = 0
    for entry, code in reversed(codes):
        if code is None:
            skipped += 1
            continue
        if len(created) >= MAX_NEW_PER_POLL:
            break
        shell = create_shell(connection, code, source_id=source_id,
                             title=entry.title or None, link=entry.link,
                             release_date=(entry.published_at or "")[:10] or None,
                             entity_id=entity_id, now=moment)
        if shell is not None:
            created.append((shell, code))
    return {"seen": len(parsed.entries), "fresh": len(fresh),
            "without_code": skipped, "created": created}
