#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""给日文汉字身份补简体中文检索词。

`涼森れむ` 里的 `涼` 是日文新字体，中文习惯写 `凉`；搜「凉森」搜不到，因为
`entity.canonical_name` 存的是日文写法。同类差异在库里成规模存在：`澤`/`泽`、
`齋`/`斋`、`櫻`/`樱`、`黒`/`黑`。

只做机械的字形归一，不做译名。`涼森れむ` 转出来是 `凉森れむ`，不是 `凉森玲梦`
——后者是圈内约定俗成的译名，必须来自真实词库，编不得。

写入 `entity_search_term`，不动 `canonical_name`。`0004` 的 FTS 视图已经把
`entity_search_term` 纳入 `search_terms` 列，并有 insert/delete/update 触发器，
所以写完即可被三字以上的查询命中；两字查询走 LIKE 分支，需要 `web_contract`
一并把别名和检索词纳入比对。

映射表只覆盖本库身份里实际出现的汉字（实测 398 个不同字），表里没有的字原样保留。
默认只产出复核 CSV，`--apply` 才写库且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.migrations import sqlite_backup

#: `entity_search_term.purpose` 有 CHECK 约束，只接受 `discovery` / `source_lookup`。
#: 简体写法是用来找到这个人的，属于 discovery；既有的 52 条 stash 检索词也是这个取值。
PURPOSE = "discovery"
SOURCE = "hanzi-simplified"

#: 日文新字体／繁体 -> 简体。只列本库身份里出现过、且两侧写法确实不同的字。
#: 日文独有字（`凪`、`辻`、`雫`、`笹`、`咲`、`栞`、`冴`、`榊`）没有简体对应，不列。
HANZI_SIMPLIFIED = {
    "並": "并", "亜": "亚", "倉": "仓", "優": "优", "兎": "兔", "冨": "富",
    "園": "园", "場": "场", "塩": "盐", "夢": "梦", "実": "实", "宮": "宫",
    "寧": "宁", "姫": "姬", "広": "广", "恵": "惠", "愛": "爱", "戸": "户",
    "斉": "齐", "斎": "斋", "齋": "斋", "東": "东", "栄": "荣", "桜": "樱",
    "櫻": "樱", "楓": "枫", "橋": "桥", "歩": "步", "氷": "冰", "沢": "泽",
    "澤": "泽", "涼": "凉", "渋": "涩", "澁": "涩", "滝": "泷", "瀬": "濑",
    "浜": "滨", "瑠": "琉", "稲": "稻", "穂": "穗", "紀": "纪", "納": "纳",
    "紗": "纱", "紺": "绀", "結": "结", "絢": "绚", "緒": "绪", "織": "织",
    "聖": "圣", "華": "华", "葉": "叶", "蒼": "苍", "蓮": "莲", "藍": "蓝",
    "蘭": "兰", "蛍": "萤", "見": "见", "詩": "诗", "賀": "贺", "跡": "迹",
    "輝": "辉", "鈴": "铃", "長": "长", "陽": "阳", "響": "响", "須": "须",
    "飯": "饭", "馬": "马", "鮎": "鲇", "鳥": "鸟", "鳩": "鸠", "黒": "黑",
    "時": "时", "岡": "冈", "島": "岛", "嶋": "岛", "嵐": "岚", "筧": "笕",
    "篠": "筱", "樹": "树", "條": "条", "櫂": "棹", "藝": "艺", "豊": "丰",
}

#: 只给这些身份补检索词。标签走另一套词表，不在本脚本范围内。
KINDS = ("performer", "creator", "studio", "series")


def simplify(name: str) -> str:
    return "".join(HANZI_SIMPLIFIED.get(char, char) for char in (name or ""))


FIELDS = ("entity_id", "kind", "canonical_name", "term", "assets", "action")


def collect(connection: sqlite3.Connection) -> list[dict[str, object]]:
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row
    placeholders = ",".join("?" * len(KINDS))
    rows: list[dict[str, object]] = []
    for entity in cursor.execute(
        f"SELECT id,kind,canonical_name FROM entity WHERE kind IN ({placeholders}) "
        "ORDER BY kind,canonical_name", KINDS,
    ).fetchall():
        term = simplify(str(entity["canonical_name"]))
        if term == entity["canonical_name"]:
            continue                                   # 没有需要归一的字
        existing = cursor.execute(
            "SELECT 1 FROM entity_search_term WHERE entity_id=? AND term=?",
            (entity["id"], term),
        ).fetchone()
        assets = cursor.execute(
            "SELECT COUNT(*) FROM asset_entity WHERE entity_id=?", (entity["id"],)
        ).fetchone()[0]
        rows.append({
            "entity_id": int(entity["id"]), "kind": str(entity["kind"]),
            "canonical_name": str(entity["canonical_name"]), "term": term,
            "assets": int(assets), "action": "已有" if existing else "新增",
        })
    return rows


def apply_rows(connection: sqlite3.Connection, rows: list[dict[str, object]]) -> int:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    written = 0
    for row in rows:
        if row["action"] != "新增":
            continue
        connection.execute(
            "INSERT INTO entity_search_term(entity_id,term,purpose,source,created_at) "
            "VALUES(?,?,?,?,?)",
            (row["entity_id"], row["term"], PURPOSE, SOURCE, stamp))
        written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="给日文汉字身份补简体检索词")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--review-csv", type=Path,
                        default=GENERATED_DIR / "chinese-search-terms.csv")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path, help="--apply 必需")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    connection = sqlite3.connect(args.db)
    rows = collect(connection)
    from collections import Counter
    print(f"需要归一的身份 {len(rows)} 个")
    print("  分布：", dict(Counter(f"{r['kind']}/{r['action']}" for r in rows)))

    if args.apply:
        sqlite_backup(args.db, args.backup)
        print(f"已备份 → {args.backup}")
        connection.execute("BEGIN IMMEDIATE")
        try:
            written = apply_rows(connection, rows)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        print(f"已写入检索词 {written} 条（FTS 由 0004 的触发器同步重建）")
    connection.close()

    args.review_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.review_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"复核 CSV → {args.review_csv}")
    if not args.apply:
        print("这是预览：未写 ledger。确认后再加 --apply --backup。")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
