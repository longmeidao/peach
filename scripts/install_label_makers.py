"""把复核过的「label 属于哪家片商」装进 ledger 的 `label_maker`（ADR-0049）。

输入是复核 CSV，列为 `label,maker,evidence`。两边都按 `kind='studio'` 的规范名或唯一别名
解析；片商在账本里还没有实体（妄想族就是：作品全挂在旗下 label 上）时，加
`--create-makers` 才新建，否则那一行跳过并写明原因。

只有一层：label 不能再挂 label，片商自己也不能是别家的 label。多一层资料页就要递归
展开，而这批数据里没有哪一家真的需要。

默认 dry-run，只打印计划。`--apply` 必须同时给 `--backup`：这是真实账本写入。重跑是
幂等的，已是同一家的跳过；label 转手时覆盖成新片商，计划里写成 update。
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.entities import normalize_entity_name, resolve_entity   # noqa: E402
from peach.review_csv import read_rows   # noqa: E402
from peach.scripting import (   # noqa: E402
    BACKUP_REQUIRED,
    add_ledger_write_args,
    open_for_write,
    verify_after_write,
)


def plan(connection: sqlite3.Connection, rows: list[dict], *,
         create_makers: bool) -> list[dict]:
    """逐行给出动作与原因；不合法的行照样列出，动作写成 skip。"""
    planned: list[dict] = []
    makers_in_plan = {normalize_entity_name(str(row.get("maker") or "").strip())
                      for row in rows}
    labels_in_plan = {normalize_entity_name(str(row.get("label") or "").strip())
                      for row in rows}
    for row in rows:
        label_name = str(row.get("label") or "").strip()
        maker_name = str(row.get("maker") or "").strip()
        item = {"label": label_name, "maker": maker_name, "label_id": None,
                "maker_id": None, "action": "skip", "reason": "",
                "evidence": str(row.get("evidence") or "").strip()}
        planned.append(item)
        if not label_name or not maker_name:
            item["reason"] = "label 或 maker 为空"
            continue
        if not item["evidence"]:
            item["reason"] = "没有证据"
            continue
        label = resolve_entity(connection, "studio", label_name)
        if label is None:
            item["reason"] = f"厂牌「{label_name}」在账本里找不到或别名撞名"
            continue
        item["label_id"] = int(label["id"])
        maker = resolve_entity(connection, "studio", maker_name)
        if maker is None and not create_makers:
            item["reason"] = f"片商「{maker_name}」在账本里没有实体；确认后加 --create-makers"
            continue
        item["maker_id"] = int(maker["id"]) if maker is not None else None
        if item["maker_id"] == item["label_id"]:
            item["reason"] = "label 与片商是同一条实体"
            continue
        if normalize_entity_name(label_name) in makers_in_plan or connection.execute(
                "SELECT 1 FROM label_maker WHERE maker_id=?", (item["label_id"],)).fetchone():
            item["reason"] = "这条 label 自己是别家的片商；只支持一层"
            continue
        if normalize_entity_name(maker_name) in labels_in_plan or (
                item["maker_id"] is not None and connection.execute(
                    "SELECT 1 FROM label_maker WHERE label_id=?", (item["maker_id"],)).fetchone()):
            item["reason"] = "片商自己是别家的 label；只支持一层"
            continue
        current = connection.execute(
            "SELECT maker_id FROM label_maker WHERE label_id=?", (item["label_id"],)).fetchone()
        if current and item["maker_id"] is not None and int(current[0]) == item["maker_id"]:
            item["reason"] = "已是这家，跳过"
        elif current:
            item.update(action="update", reason=f"转手：片商实体 {current[0]} → {maker_name}")
        else:
            item.update(action="insert",
                        reason="新建片商实体" if item["maker_id"] is None else "")
    return planned


def ensure_maker(connection: sqlite3.Connection, name: str, stamp: str) -> int:
    """片商实体不存在时按规范名新建一条 `kind='studio'`，已存在则返回它。"""
    found = resolve_entity(connection, "studio", name)
    if found is not None:
        return int(found["id"])
    connection.execute(
        "INSERT INTO entity(kind,canonical_name,normalized_name,metadata_json,created_at,updated_at) "
        "VALUES('studio',?,?,'{}',?,?)", (name, normalize_entity_name(name), stamp, stamp))
    return int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])


def install(connection: sqlite3.Connection, planned: list[dict], *, source: str) -> int:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    written = 0
    for item in planned:
        if item["action"] not in {"insert", "update"}:
            continue
        maker_id = item["maker_id"] or ensure_maker(connection, item["maker"], stamp)
        connection.execute(
            "INSERT INTO label_maker(label_id,maker_id,source,confidence,checked_at) "
            "VALUES(?,?,?,1.0,?) ON CONFLICT(label_id) DO UPDATE SET "
            "maker_id=excluded.maker_id,source=excluded.source,"
            "confidence=excluded.confidence,checked_at=excluded.checked_at",
            (item["label_id"], maker_id, f"review:{source}", stamp))
        written += 1
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, required=True, help="复核 CSV：label,maker,evidence")
    parser.add_argument("--create-makers", action="store_true",
                        help="片商在账本里没有实体时新建")
    return add_ledger_write_args(parser)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.apply and not args.backup:
        print(f"[stop] {BACKUP_REQUIRED}")
        return 2
    connection = open_for_write(args)
    if args.apply:
        print(f"已备份：{args.backup}")
    connection.execute("PRAGMA foreign_keys=ON")
    rows = read_rows(args.input)
    try:
        before = connection.execute("SELECT count(*) FROM label_maker").fetchone()[0]
        planned = plan(connection, rows, create_makers=args.create_makers)
        for item in planned:
            mark = {"insert": "+", "update": "~"}.get(item["action"], " ")
            print(f" {mark} {item['label'][:24]:<24} → {item['maker'][:14]:<14} {item['reason']}")
        changes = [item for item in planned if item["action"] != "skip"]
        print({"输入": len(rows), "将写入": len(changes), "跳过": len(planned) - len(changes),
               "写入前 label_maker": before})
        if not args.apply:
            print("dry-run；确认无误后加 --apply --backup <路径>")
            return 0
        with connection:
            written = install(connection, planned, source=args.input.name)
        after = connection.execute("SELECT count(*) FROM label_maker").fetchone()[0]
        integrity, orphans = verify_after_write(connection)
        inserted = sum(item["action"] == "insert" for item in planned)
        print({"实际写入": written, "写入后 label_maker": after, "差值": after - before,
               "integrity_check": integrity, "foreign_key_check": orphans})
        if after - before != inserted or integrity != "ok" or orphans:
            print("[warn] 前后差值、完整性或外键与预期不符，请人工核对")
            return 1
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
