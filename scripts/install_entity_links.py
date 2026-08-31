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
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.review_csv import read_rows   # noqa: E402

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
    parser.add_argument("--input", type=Path, required=True,
                        help=f"复核表，列：{','.join(FIELDS)}")
    parser.add_argument("--apply", action="store_true", help="真正写入；必须同时给 --backup")
    parser.add_argument("--backup", type=Path, help="写入前的 SQLite 备份落点")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.apply and not args.backup:
        print("[stop] --apply 是真实账本写入，必须同时给 --backup")
        return 2

    rows = read_rows(args.input)
    connection = sqlite3.connect(args.database)
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        before = connection.execute("SELECT count(*) FROM entity_link").fetchone()[0]
        planned = plan(connection, rows)
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
