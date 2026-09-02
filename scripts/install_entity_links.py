"""把复核过的实体链接装进 ledger 的 `entity_link`。

这个脚本补的是一条断掉的链路，不是新功能。`entity_link` 表、`q_entity` 的 `links` 契约、
资料页的 favicon 渲染和敏感来源不可点，全都在 2026-08 就写好了；缺的只有「已复核的结果
怎么进库」。结果是 8178 个实体里只有 5 条链接，而 `studio-x-handles.csv` 里 14 个人工
看图确认过的 handle 一条都没生效——采了、复核了、没有安装路径。这是本仓库出现过第四次
的同一个形态（`creator_tags`、`studio_logos`、`performer_avatars` 各犯过一次）。

默认 dry-run，只打印计划。`--apply` 必须同时给 `--backup`：这是真实账本写入。
写入是幂等的（`UNIQUE(entity_id,url)`），重跑不会产生重复行。
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.review_csv import read_rows   # noqa: E402
from peach.scripting import USER_AGENT   # noqa: E402

LINK_KINDS = {"official", "social", "catalog", "source_reference"}
FIELDS = ("entity_id", "kind", "name", "link_kind", "label", "url", "evidence")


def normalise_url(url: str) -> str:
    """补上 scheme 并去掉空白。

    复核表是人和脚本混写的，`moodyz.com` 和 `https://moodyz.com/` 都会出现。不统一的话
    同一个站会因为写法不同绕过 `UNIQUE(entity_id,url)` 建出两行。
    """
    url = url.strip()
    if not url:
        return ""
    if not urlsplit(url).scheme:
        url = "https://" + url
    return url


def resolve_entity(connection: sqlite3.Connection, row: dict) -> tuple[int | None, str]:
    """返回 (entity_id, 说明)。按 id 优先，其次 kind+规范名，最后 kind+别名。"""
    raw = str(row.get("entity_id") or "").strip()
    if raw:
        found = connection.execute("SELECT id FROM entity WHERE id=?", (int(raw),)).fetchone()
        return (found[0], "按 entity_id") if found else (None, f"entity_id {raw} 不存在")
    kind, name = str(row.get("kind") or "").strip(), str(row.get("name") or "").strip()
    if not kind or not name:
        return None, "既没有 entity_id，也没有 kind+name"
    found = connection.execute(
        "SELECT id FROM entity WHERE kind=? AND canonical_name=?", (kind, name)).fetchone()
    if found:
        return found[0], "按规范名"
    found = connection.execute(
        "SELECT e.id FROM entity e JOIN entity_alias a ON a.entity_id=e.id "
        "WHERE e.kind=? AND a.alias=?", (kind, name)).fetchone()
    if found:
        return found[0], "按别名"
    return None, f"{kind} 「{name}」在账本里找不到"


def plan(connection: sqlite3.Connection, rows: list[dict]) -> list[dict]:
    """把复核表变成逐行的写入计划，每行都带上为什么。

    不合法的行不会被悄悄跳过——它们照样出现在计划里，动作写成 skip 并说明原因。
    静默丢行会让「装了 40 条」和「表里有 40 条」这两个数字对不上，而没人知道差在哪。
    """
    planned: list[dict] = []
    for row in rows:
        item = {"studio": row.get("name") or "", "action": "skip", "reason": "",
                "entity_id": None, "link_kind": "", "label": "", "url": "",
                "evidence": (row.get("evidence") or "").strip()}
        url = normalise_url(str(row.get("url") or ""))
        link_kind = str(row.get("link_kind") or "").strip()
        entity_id, note = resolve_entity(connection, row)
        item.update(entity_id=entity_id, link_kind=link_kind, url=url,
                    label=str(row.get("label") or "").strip())
        if entity_id is None:
            item["reason"] = note
        elif link_kind not in LINK_KINDS:
            item["reason"] = f"link_kind 「{link_kind}」不在 {sorted(LINK_KINDS)} 内"
        elif not url or urlsplit(url).scheme not in {"http", "https"}:
            item["reason"] = f"URL 不可用：{url or '空'}"
        elif not item["label"]:
            item["reason"] = "没有 label；资料页要拿它当链接文字"
        elif connection.execute("SELECT 1 FROM entity_link WHERE entity_id=? AND url=?",
                                (entity_id, url)).fetchone():
            item["reason"] = "已存在，跳过"
        else:
            item.update(action="insert", reason=note)
        planned.append(item)
    return planned


#: 「这个页面没了」——上游明确这么说了，才算确证。
GONE_STATUSES = {404, 410}


def resolves(url: str, timeout: float = 12.0) -> tuple[bool, str]:
    """这个地址现在还能打开吗。返回（能不能, 说明）。

    每个请求新建 client 并立刻关掉：这批地址分布在上百个互不相同的主机上，其中不少
    连不上，而失败的连接会在共享池里漏掉槽位，几十个请求之后一切都变成 PoolTimeout。
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout,
                          limits=httpx.Limits(max_connections=4,
                                              max_keepalive_connections=0)) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
    except Exception as exc:
        return False, f"取不到：{type(exc).__name__}"
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}"
    return True, "可打开"


def is_gone(note: str) -> bool:
    """这条「打不开」是不是「页面没了」的确证。

    取不到不等于没了，这两件事只有 404／410 能划清。实测全库 152 条打不开的里面：

        linktr.ee            403   Linktree 挡爬虫，浏览器里能正常打开
        facebook.com         400   同理
        x.com/MomotaEmiri    500   X 的临时错误，账号很可能还在
        diaz-g.com           连接错误    一次探测说明不了什么

    按「非 200 就删」会连这 26 条一起删掉，其中大部分链接本身是好的。5xx、403 和
    超时要留着下次复查，不是删除的理由——这和取证失败时写 `未取得` 而不是写结论是同一条。
    """
    match = re.match(r"HTTP (\d+)$", note)
    return bool(match) and int(match.group(1)) in GONE_STATUSES


def check_links(planned: list[dict], interval: float = 0.4, probe=None) -> None:
    """把打不开的地址从写入计划里剔除，就地改写 `planned`。

    这一步是补上一次真实事故的：首批 703 条链接一条都没验就装进了账本，事后逐条测
    发现 289 条 official 里有 107 条打不开（84 个 404、18 个 502），37% 是死的。
    上游给什么就存什么，等于把 minnano-av 几年前的快照当成现在的事实——T-POWERS 改过
    站，`/official/talent/X` 早已 404，而资料页上它看起来和好链接一模一样。

    门槛放在安装器而不是各个采集器里：这里是所有来源进入账本的唯一入口，一道门管住
    全部，好过给每个采集器各打一个补丁、再漏掉下一个。社媒同样验——实测 X 对真 handle
    回 200、对不存在的回 404，livedoor 上也确实有已经删掉的博客。
    """
    probe = probe or resolves
    for item in planned:
        if item["action"] != "insert":
            continue
        ok, note = probe(item["url"])
        if not ok:
            item.update(action="skip", reason=f"打不开，不写入（{note}）")
        if probe is resolves:
            time.sleep(interval)


def dead_links(connection: sqlite3.Connection, interval: float = 0.4, probe=None) -> list[dict]:
    """已经在库里、但现在打不开的链接。

    可达性门槛只挡住新写入；库里那 703 条是在门槛存在之前进去的，得单独清一遍。
    链接还会随时间烂掉——事务所改版、艺人解约、博客注销——所以这条路要留着复用，
    不是一次性的清理脚本。
    """
    probe = probe or resolves
    out = []
    for link_id, entity, kind, label, url in connection.execute(
            "SELECT l.id, e.canonical_name, l.link_kind, l.label, l.url "
            "FROM entity_link l JOIN entity e ON e.id=l.entity_id ORDER BY l.id"):
        ok, note = probe(url)
        if not ok:
            out.append({"id": link_id, "entity": entity, "link_kind": kind,
                        "label": label, "url": url, "note": note})
        if probe is resolves:
            time.sleep(interval)
    return out


def install(connection: sqlite3.Connection, planned: list[dict], source: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    written = 0
    for item in planned:
        if item["action"] != "insert":
            continue
        metadata = {"source": source, "installed_at": now}
        if item["evidence"]:
            metadata["evidence"] = item["evidence"]
        connection.execute(
            "INSERT OR IGNORE INTO entity_link"
            "(entity_id,link_kind,label,url,hostname,is_sensitive,metadata_json,"
            " created_at,updated_at) VALUES(?,?,?,?,?,0,?,?,?)",
            (item["entity_id"], item["link_kind"], item["label"], item["url"],
             urlsplit(item["url"]).hostname or "", json.dumps(metadata, ensure_ascii=False),
             now, now))
        written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--input", type=Path,
                        help=f"复核表，列：{','.join(FIELDS)}")
    parser.add_argument("--prune-dead", action="store_true",
                        help="改为清理库里已经打不开的链接，不读 --input")
    parser.add_argument("--apply", action="store_true", help="真正写入；必须同时给 --backup")
    parser.add_argument("--no-check", action="store_true",
                        help="跳过「地址能不能打开」的检查。只在离线复核时用——"
                             "首批 703 条就是没验直接装的，事后发现 37%% 是死链")
    parser.add_argument("--backup", type=Path, help="写入前的 SQLite 备份落点")
    return parser


def prune(connection: sqlite3.Connection, args) -> int:
    """列出并（在 --apply 时）删除库里打不开的链接。"""
    before = connection.execute("SELECT count(*) FROM entity_link").fetchone()[0]
    unreachable = dead_links(connection)
    gone = [item for item in unreachable if is_gone(item["note"])]
    unclear = [item for item in unreachable if not is_gone(item["note"])]
    for item in gone:
        print(f" - {item['entity'][:14]:<14} {item['link_kind']:<8} "
              f"{item['label'][:18]:<18} {item['note']:<14} {item['url'][:52]}")
    for item in unclear:
        # 留着不删，但必须看得见——静默保留和静默删除一样，都会让人以为库是干净的。
        print(f" ? {item['entity'][:14]:<14} {item['link_kind']:<8} "
              f"{item['label'][:18]:<18} {item['note']:<14} {item['url'][:52]}")
    print({"库内链接": before, "打不开": len(unreachable),
           "确证已没了（将删除）": len(gone), "取不到但不算证据（保留待复查）": len(unclear)})
    dead = gone
    if not args.apply:
        print("dry-run；确认无误后加 --apply --backup <路径>")
        return 0

    args.backup.parent.mkdir(parents=True, exist_ok=True)
    destination = sqlite3.connect(args.backup)
    with destination:
        connection.backup(destination)
    destination.close()
    print(f"已备份：{args.backup}")

    with connection:
        connection.executemany("DELETE FROM entity_link WHERE id=?",
                               [(item["id"],) for item in dead])
    after = connection.execute("SELECT count(*) FROM entity_link").fetchone()[0]
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    orphans = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    print({"删除前": before, "删除后": after, "差值": before - after,
           "integrity_check": integrity, "foreign_key_check": orphans})
    if before - after != len(dead) or integrity != "ok" or orphans:
        print("[warn] 前后差值、完整性或外键与预期不符，请人工核对")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.apply and not args.backup:
        print("[stop] --apply 是真实账本写入，必须同时给 --backup")
        return 2

    if not args.prune_dead and not args.input:
        print("[stop] 需要 --input（写入复核表）或 --prune-dead（清理死链）")
        return 2

    connection = sqlite3.connect(args.database)
    connection.execute("PRAGMA foreign_keys=ON")
    if args.prune_dead:
        try:
            return prune(connection, args)
        finally:
            connection.close()

    rows = read_rows(args.input)
    try:
        before = connection.execute("SELECT count(*) FROM entity_link").fetchone()[0]
        planned = plan(connection, rows)
        if args.no_check:
            print("[warn] 已跳过可达性检查：打不开的地址会照样写进账本")
        else:
            check_links(planned)
        for item in planned:
            mark = "+" if item["action"] == "insert" else " "
            print(f" {mark} {str(item['studio'])[:18]:<18} {item['link_kind']:<8} "
                  f"{str(item['url'])[:44]:<44} {item['reason']}")
        inserts = [item for item in planned if item["action"] == "insert"]
        print({"输入": len(rows), "将写入": len(inserts),
               "跳过": len(planned) - len(inserts), "写入前 entity_link": before})
        if not args.apply:
            print("dry-run；确认无误后加 --apply --backup <路径>")
            return 0

        args.backup.parent.mkdir(parents=True, exist_ok=True)
        destination = sqlite3.connect(args.backup)
        with destination:
            connection.backup(destination)
        destination.close()
        print(f"已备份：{args.backup}")

        with connection:
            written = install(connection, planned, source=args.input.name)
        after = connection.execute("SELECT count(*) FROM entity_link").fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        orphans = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        print({"实际写入": written, "写入后 entity_link": after, "差值": after - before,
               "integrity_check": integrity, "foreign_key_check": orphans})
        if after - before != written or integrity != "ok" or orphans:
            print("[warn] 前后差值、完整性或外键与预期不符，请人工核对")
            return 1
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
