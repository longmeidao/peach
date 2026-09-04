#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把一格装了多个艺名的别名拆成一人多名。

r18.dev 的罗马字字段本身就是 `现用名 (曾用名, 曾用名)` 这个渲染格式，导入时一个字段
写一行，于是 `Ako Momona (Kou Akemi, Mari Koizumi)` 整串成了一条别名。它做别名是死的：
按任何一段都搜不到，选成统称更不成立。同一条实体的假名和汉字写法本来就各自成行，缺的
只是这几个罗马字，所以拆开是补信息，不是丢信息。

**只拆罗马字人名这一种形状**（判据见 `peach.entities.COMPOSITE_PERSON_NAME`）。账本里
「名字后面跟一对括号」的还有四类完全不同的东西，一律不动，只写进复核 CSV 交人工：

- `AV DEBUT（本物人妻）`：括号里是厂牌，用来把三个同名系列分开。拆了就撞成一个。
- `アスナ(SAO)`：角色标签的出处消歧，账本里有五百多条。
- `快慢扳机（接稿中）`、`るかぴあ（X：復帰しました）`：括号里是接稿状态或公告。
- `kitty(1)`、`Mana(23)`：去重后缀或数字。

拆分不可逆。默认只产出复核 CSV，`--apply` 才写 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR   # noqa: E402
from peach.entities import (   # noqa: E402
    normalize_entity_name, split_composite_person_name,
)
from peach.review_csv import write_rows   # noqa: E402
from peach.scripting import (   # noqa: E402
    add_ledger_write_args, counts_of, open_for_write, verify_after_write,
)

#: 只有人名实体才可能出现「一个人的多个艺名」。系列、厂牌和标签的括号是别的意思。
PERSON_KINDS = ("performer", "creator")

FIELDS = ("verdict", "kind", "entity_id", "canonical_name", "field",
          "value", "source", "parts", "note")

EXTRA_COUNTS = {
    "composite_alias": (
        "SELECT count(*) FROM entity_alias WHERE alias LIKE '%(%' OR alias LIKE '%（%'"),
}


def _collision(connection: sqlite3.Connection, entity_id: int, part: str) -> str:
    """这一段是不是别的实体的规范名。是的话整行不拆，交人工。

    拆出来的名字撞上另一条实体的规范名，意味着两条实体可能是同一个人——那是合并要
    回答的问题，不是拆别名顺手能定的。悄悄插进去只会让两边都持有对方的名字。
    """
    row = connection.execute(
        "SELECT id, kind, canonical_name FROM entity "
        "WHERE normalized_name=? AND id<>?",
        (normalize_entity_name(part), entity_id)).fetchone()
    return "" if row is None else f"撞 entity {row[0]}（{row[1]}）{row[2]}"


def collect(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """账本里所有带括号的实体名与别名，标好判定。"""
    rows: list[dict[str, object]] = []
    scans = (
        ("alias", "SELECT a.entity_id, e.kind, e.canonical_name, a.alias, a.source "
                  "FROM entity_alias a JOIN entity e ON e.id=a.entity_id "
                  "WHERE a.alias LIKE '%(%' OR a.alias LIKE '%（%'"),
        ("canonical", "SELECT id, kind, canonical_name, canonical_name, '' FROM entity "
                      "WHERE canonical_name LIKE '%(%' OR canonical_name LIKE '%（%'"),
    )
    for field, sql in scans:
        for entity_id, kind, canonical, value, source in connection.execute(sql):
            parts = split_composite_person_name(value)
            note, verdict = "", "review"
            # 判据是「签名匹配上了」，不是「拆出几段」。`Rei Mizuna (Rei Mizuna)` 去重后
            # 只剩一段，但它照样是那个打包字段，照样得换成干净的一行。
            if parts == [value.strip()]:
                note = "不是罗马字复合人名"
            elif kind not in PERSON_KINDS:
                note = f"{kind} 的括号不是艺名"
            elif field == "canonical":
                note = "规范名要人工定留哪一个"
            else:
                collisions = [c for c in (_collision(connection, int(entity_id), part)
                                          for part in parts) if c]
                if collisions:
                    note = "；".join(collisions)
                else:
                    verdict = "auto"
            rows.append({
                "verdict": verdict, "kind": kind, "entity_id": int(entity_id),
                "canonical_name": canonical, "field": field, "value": value,
                "source": source or "", "parts": " | ".join(parts), "note": note,
            })
    rows.sort(key=lambda row: (row["verdict"] != "auto", str(row["kind"]),
                               int(row["entity_id"])))
    return rows


def apply_rows(connection: sqlite3.Connection,
               rows: list[dict[str, object]]) -> dict[str, int]:
    """把 `auto` 行拆开：先补上各段，再删掉那条复合别名。

    每一段都记在提供它的那个来源名下。它们确实是它给的，只是被打包在一个字段里；改写成
    「本脚本」会让下一个人查不到这几个罗马字是谁提供的。
    """
    added = removed = 0
    for row in rows:
        if row["verdict"] != "auto":
            continue
        entity_id, source = int(row["entity_id"]), str(row["source"])
        for part in str(row["parts"]).split(" | "):
            connection.execute(
                "INSERT OR IGNORE INTO entity_alias"
                "(entity_id,alias,normalized_alias,source) VALUES(?,?,?,?)",
                (entity_id, part, normalize_entity_name(part), source))
            added += connection.execute("SELECT changes()").fetchone()[0]
        connection.execute(
            "DELETE FROM entity_alias WHERE entity_id=? AND alias=? AND source=?",
            (entity_id, row["value"], source))
        removed += connection.execute("SELECT changes()").fetchone()[0]
    return {"added": added, "removed": removed}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    add_ledger_write_args(parser)
    parser.add_argument("--review-csv", type=Path,
                        default=GENERATED_DIR / "review" / "composite-names.csv",
                        help="复核 CSV 输出路径")
    return parser


def run(args: argparse.Namespace) -> int:
    connection = open_for_write(args)
    try:
        rows = collect(connection)
        write_rows(args.review_csv, FIELDS, rows)
        verdicts = Counter(str(row["verdict"]) for row in rows)
        print(f"带括号的名字 {len(rows)} 条，复核 CSV：{args.review_csv}")
        print("  判定分布：", dict(verdicts))
        for row in rows:
            if row["verdict"] == "auto":
                print(f"    拆 [{row['entity_id']}] {row['canonical_name']}："
                      f"{row['value']} -> {row['parts']}")
        by_kind = Counter(f"{row['kind']}/{row['field']}" for row in rows
                          if row["verdict"] != "auto")
        print("  交人工：", dict(by_kind))
        if not args.apply:
            print("  未写 ledger（加 --apply --backup 才写）")
            return 0

        print(f"  已备份到 {args.backup}")
        before = counts_of(connection, EXTRA_COUNTS)
        with connection:
            moved = apply_rows(connection, rows)
        after = counts_of(connection, EXTRA_COUNTS)
        _integrity, violations = verify_after_write(connection)
        print("  拆分结果：", moved)
        for key in before:
            mark = "" if before[key] == after[key] else "  <-- 变化"
            print(f"    {key}: {before[key]} -> {after[key]}{mark}")
        print(f"  foreign_key_check 违规 {violations} 条")
        return 1 if violations else 0
    finally:
        connection.close()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
