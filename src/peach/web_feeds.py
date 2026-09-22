"""番号发现源的读写契约：订阅管理、拉取、未入库新作的列表与已读/忽略（ADR-0042）。

这里是 Feed 唯一会向站点发请求的地方。HTTP 走 `scraping_access.SourceTransport`
（按来源的凭据、代理与冷却）套 `HostLimitedTransport`（按主机的间隔），
和刮削链同一套预算——Feed 是后台跑的，不因此另开一套限流。
"""
from __future__ import annotations

import threading
import time
import uuid

from . import feed_followup, feeds
from .http import HttpRequest, public_https_url

#: 一次拉取的超时与体积上限。一份 RSS 正常几十到几百 KB；JavDB 演员页 78 KB。
#: 2 MiB 之外的东西不是 feed，是被替换成了别的页面。
FETCH_TIMEOUT = 30.0
FETCH_MAX_BYTES = 2 * 1024 * 1024

#: 一轮里最多拉几个源。源多的时候分几轮拉完，而不是让一轮跑到限流上去。
MAX_SOURCES_PER_RUN = 20

_NOT_MODIFIED = 304


def _transport(contract):
    from .jav_cover_fetch import HostLimitedTransport
    from .library_processing import SOURCE_INTERVALS
    from .scraping_access import SourceTransport

    return HostLimitedTransport(
        SourceTransport(contract.follow_secrets_root), 2.0, intervals=SOURCE_INTERVALS)


def fetch(transport, url: str, *, etag: str | None = None,
          last_modified: str | None = None):
    """取一次订阅地址。304 不是失败，原样交给调用方判。"""
    if not public_https_url(url):
        raise ValueError("订阅地址必须是解析到公网的 HTTPS 地址")
    headers = {"Accept": "application/rss+xml, application/atom+xml, application/xml,"
                         " text/xml;q=0.9, text/html;q=0.8"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    return transport(HttpRequest("GET", url, headers), FETCH_TIMEOUT, FETCH_MAX_BYTES)


def poll_source(contract, transport, source) -> dict:
    """拉一个源并落库，返回这一轮的账。任何失败都写进源的 `last_error`。

    四条返回路径（请求失败、304、解析失败、正常）都经 `feeds.settle` 写下次时间，
    所以任何一种结局都不会让这个源卡住不再排队。
    """
    source_id = int(source["id"])
    interval = int(source["interval_minutes"])
    # `ok` 与 `added` 两个键名跟着 `follow_scheduler` 读结果的那一套写：它按
    # `ok` 数失败、按 `added` 数新增，两个调度对象共用同一段结算。
    report = {"source": source_id, "name": source["name"] or source["url"],
              "ok": True, "seen": 0, "added": 0, "without_code": 0, "error": None}
    try:
        response = fetch(transport, source["url"], etag=source["etag"],
                         last_modified=source["last_modified"])
    except Exception as error:  # noqa: BLE001 - 原因写到源那一行上给人看
        report.update(ok=False, error=str(error))
        with contract.database.write_transaction() as connection:
            feeds.settle(connection, source_id, error=str(error),
                         interval_minutes=interval)
        return report
    if response.status == _NOT_MODIFIED:
        with contract.database.write_transaction() as connection:
            feeds.settle(connection, source_id, error=None, interval_minutes=interval)
        report["not_modified"] = True
        return report
    if response.status != 200:
        message = f"来源回了 HTTP {response.status}"
        report.update(ok=False, error=message)
        with contract.database.write_transaction() as connection:
            feeds.settle(connection, source_id, error=message, interval_minutes=interval)
        return report
    parsed = feeds.parse(source["kind"], response.body, source["url"])
    if parsed is None:
        # 解不出不等于「这次没有新作」：JavDB 那种回了一份不含作品的页面也是这条路。
        # 当成安静的源会让一个坏掉的订阅永远不报错。
        message = "这一页解不出任何条目"
        report.update(ok=False, error=message)
        with contract.database.write_transaction() as connection:
            feeds.settle(connection, source_id, error=message, interval_minutes=interval)
        return report
    headers = {key.lower(): value for key, value in (response.headers or {}).items()}
    with contract.database.write_transaction() as connection:
        outcome = feeds.poll(connection, source, parsed)
        feeds.settle(connection, source_id, error=None,
                     etag=headers.get("etag"), last_modified=headers.get("last-modified"),
                     interval_minutes=interval, seen=outcome["seen"],
                     new=len(outcome["created"]))
    report.update(seen=outcome["seen"], fresh=outcome["fresh"],
                  without_code=outcome["without_code"],
                  added=len(outcome["created"]),
                  codes=[code for _id, code in outcome["created"]])
    return report


def _execute_check(contract, body, job_id: str) -> dict:
    only = body.get("sources")
    with contract.database.read_connection() as connection:
        if isinstance(only, list) and only:
            wanted = {int(value) for value in only}
            rows = [row for row in connection.execute(
                "SELECT * FROM feed_source ORDER BY id") if int(row["id"]) in wanted]
        elif body.get("all"):
            rows = list(connection.execute(
                "SELECT * FROM feed_source WHERE enabled=1 ORDER BY id"))
        else:
            rows = feeds.due_sources(connection)
    rows = rows[:MAX_SOURCES_PER_RUN]
    transport = _transport(contract)
    results, codes = [], []
    try:
        for index, source in enumerate(rows):
            contract.feed_job.update(job_id, checked=index, total=len(rows),
                                     current=source["name"] or source["url"])
            report = poll_source(contract, transport, source)
            results.append(report)
            codes.extend(report.get("codes") or [])
    finally:
        close = getattr(transport, "close", None)
        if close:
            close()
    contract.cache_bust()
    return {"ok": True, "checked": len(rows), "total": len(rows), "results": results,
            "added": len(codes),
            # 后继由结果声明，调度端统一派（ADR-0040）：这里只把清单交出去。
            "followups": [dict(key=item.key, task_key=item.task_key, label=item.label)
                          for item in feed_followup.plan(codes)]}


def w_feed_check(contract, body) -> dict:
    """拉一轮订阅。不带参数只拉到期的源，`all` 拉全部启用的源。"""
    finished = threading.Event()
    request_id = uuid.uuid4().hex

    def work(job_id):
        try:
            result = _execute_check(contract, body, job_id)
            contract.feed_job.update(job_id, **result, status="complete",
                                     current=None, completed_at=time.time())
        finally:
            finished.set()

    started = contract.feed_job.start(
        work, restart=True,
        trigger="scheduled" if body.get("automatic") else "manual",
        initial={"ok": True, "checked": 0, "total": 0, "results": [], "added": 0,
                 "request_id": request_id, "current": None})
    if body.get("background"):
        return started
    if started["request_id"] != request_id:
        return {"ok": False, "busy": True, "checked": 0, "results": []}
    finished.wait()
    return contract.feed_job.snapshot() or started


def q_feed_check(contract, args) -> dict:
    return contract.feed_job.snapshot() or {"status": "idle"}


def q_feeds(contract, args) -> dict:
    """设置页「订阅源」小节的首屏。"""
    with contract.database.read_connection() as connection:
        rows = feeds.sources(connection)
        pending = connection.execute(
            "SELECT count(*) FROM feed_discovery WHERE ignored_at IS NULL"
            " AND read_at IS NULL").fetchone()[0]
    return {"ok": True, "sources": rows, "unread": int(pending or 0),
            "kinds": [{"value": kind, "label": feeds.KIND_LABELS[kind]}
                      for kind in feeds.KINDS],
            "min_interval_minutes": feeds.MIN_INTERVAL_MINUTES,
            "max_interval_minutes": feeds.MAX_INTERVAL_MINUTES}


def w_feed_source(contract, body) -> dict:
    """增删订阅与开关。新增不当场拉取：第一轮由到期扫描带上，错误显示在那一行。"""
    action = str(body.get("action") or "add")
    if action == "remove":
        source_id = body.get("id")
        if not isinstance(source_id, int):
            raise ValueError("id must be an integer feed source id")
        with contract.database.write_transaction() as connection:
            feeds.remove_source(connection, source_id)
        return {"ok": True, "removed": source_id}
    if action == "enabled":
        source_id, enabled = body.get("id"), body.get("enabled")
        if not isinstance(source_id, int) or not isinstance(enabled, bool):
            raise ValueError("id must be an integer and enabled must be a boolean")
        with contract.database.write_transaction() as connection:
            feeds.set_enabled(connection, source_id, enabled)
        return {"ok": True, "source": source_id, "enabled": enabled}
    if action != "add":
        raise ValueError(f"unknown feed source action: {action}")
    entity_id = body.get("entity_id")
    with contract.database.write_transaction() as connection:
        source_id = feeds.add_source(
            connection, kind=str(body.get("kind") or feeds.KIND_RSS),
            url=body.get("url"), name=str(body.get("name") or ""),
            entity_id=int(entity_id) if isinstance(entity_id, int) else None,
            interval_minutes=body.get("interval_minutes", feeds.DEFAULT_INTERVAL_MINUTES))
    return {"ok": True, "source": source_id}


#: 列表一次给多少条。首页那一块只放一行，人物页给一屏。
DISCOVERY_LIMIT = 24


def q_feed_discoveries(contract, args) -> dict:
    """未入库的新作。`entity` 限定到某个人，`state` 切换忽略视图。

    「已入库」是现算的：壳上不存这个布尔，它的真相在 `asset` 那一侧（ADR-0042 第三条）。
    已经入库的番号不出现在列表里——那条新作的使命已经完成了。
    """
    entity_id = args.get("entity")
    state = str(args.get("state") or "active")
    try:
        limit = min(int(args.get("limit") or DISCOVERY_LIMIT), 100)
    except (TypeError, ValueError):
        limit = DISCOVERY_LIMIT
    where = ["NOT EXISTS (SELECT 1 FROM asset a WHERE a.code IS NOT NULL"
             " AND normalise_code_key(a.code)=normalise_code_key(d.code))"]
    params: list[object] = []
    if state == "ignored":
        where.append("d.ignored_at IS NOT NULL")
    elif state != "all":
        where.append("d.ignored_at IS NULL")
    if entity_id:
        where.append("EXISTS (SELECT 1 FROM feed_discovery_entity de"
                     " WHERE de.discovery_id=d.id AND de.entity_id=?)")
        params.append(int(entity_id))
    with contract.database.read_connection() as connection:
        rows = connection.execute(
            "SELECT d.*, s.name AS source_name, s.kind AS source_kind"
            " FROM feed_discovery d LEFT JOIN feed_source s ON s.id=d.source_id"
            f" WHERE {' AND '.join(where)}"
            " ORDER BY COALESCE(d.release_date,d.discovered_at) DESC, d.id DESC"
            " LIMIT ?", (*params, limit + 1)).fetchall()
    more = len(rows) > limit
    return {"ok": True, "more": more, "items": [{
        "id": int(row["id"]),
        "code": row["code"],
        "title": row["title"],
        "link": row["link"],
        "cover_url": row["cover_url"],
        "release_date": row["release_date"],
        "studio": row["studio"],
        "performers": row["performers"],
        "source_name": row["source_name"],
        "read": bool(row["read_at"]),
        "ignored": bool(row["ignored_at"]),
        "scrape_error": row["scrape_error"],
    } for row in rows[:limit]]}


#: 允许的状态动作。已读与忽略彼此正交，各写各的列，都不改变去重（ADR-0042 第五条）。
ACTIONS = {"read": ("read_at", True), "unread": ("read_at", False),
           "ignore": ("ignored_at", True), "unignore": ("ignored_at", False)}


def w_feed_discovery(contract, body) -> dict:
    """把一条或几条新作标成已读/未读、忽略/取消忽略。幂等。"""
    action = str(body.get("action") or "")
    if action not in ACTIONS:
        raise ValueError(f"unknown feed discovery action: {action}")
    raw = body.get("ids")
    ids = [value for value in (raw if isinstance(raw, list) else [raw])
           if type(value) is int]
    if not ids:
        raise ValueError("ids must be a nonempty list of feed discovery ids")
    column, setting = ACTIONS[action]
    value = feeds.stamp() if setting else None
    marks = ",".join("?" for _ in ids)
    with contract.database.write_transaction() as connection:
        cursor = connection.execute(
            f"UPDATE feed_discovery SET {column}=? WHERE id IN ({marks})",
            (value, *ids))
    contract.cache_bust()
    return {"ok": True, "action": action, "affected": int(cursor.rowcount or 0)}
