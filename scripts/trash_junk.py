#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把高置信度的广告残留移进回收站。

候选来自 `peach.web_batch.q_ads`，与垃圾复核页是同一套评分与判据；这里只按分数
与来源过滤，然后写 `disposal='trash'`——文件不动、账本行保留，清空回收站才真正
删除，误判可以随时从回收站恢复。默认 dry-run 只出清单，`--apply` 必须同时给
`--backup`。

用法:
    python scripts/trash_junk.py --min-score 60
    python scripts/trash_junk.py --min-score 60 --apply --backup <落点>
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.review_csv import write_rows
from peach.scripting import (
    add_ledger_write_args, counts_of, open_for_write, open_readonly, verify_after_write,
)
from peach.web_batch import q_ads
from peach.web_contract import WebContract

FIELDS = ["id", "score", "location", "medium", "size_mb", "name", "why", "path"]
TRASHABLE_LOCATIONS = ("local", "115", "pikpak")


def select_candidates(db_path: Path, *, min_score: int, locations: tuple[str, ...] = (),
                      kind: str = "") -> list[dict]:
    """只读跑一遍垃圾判据，按分数与来源过滤，并补上路径供人核对。"""
    contract = WebContract(Path(db_path))
    result = q_ads(contract, limit=100000, kind=kind)
    items = [item for item in result["items"] if int(item["score"]) >= min_score]
    if locations:
        items = [item for item in items if item["location"] in locations]
    connection = open_readonly(db_path)
    try:
        paths = {row["id"]: row["path"] for row in connection.execute("SELECT id,path FROM asset")}
    finally:
        connection.close()
    for item in items:
        item["path"] = paths.get(item["id"], "")
    return items


def trash_assets(connection, asset_ids: list[int]) -> int:
    """与复核页「移入回收站」同义：只改 `disposal`，不动文件与引用关系。"""
    ids = list(dict.fromkeys(int(value) for value in asset_ids))
    if not ids:
        return 0
    marks = ",".join("?" * len(ids))
    cursor = connection.execute(
        f"UPDATE asset SET disposal='trash', feedback_at=? WHERE id IN ({marks}) "
        "AND disposal IS NULL AND location IN ('local','115','pikpak')",
        [time.time(), *ids],
    )
    connection.commit()
    return cursor.rowcount


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把高置信广告残留移入回收站")
    add_ledger_write_args(parser, db_default=DATABASE_PATH)
    parser.add_argument("--min-score", type=int, default=60,
                        help="垃圾评分下限；默认 60（整个名字都是推广语一档）")
    parser.add_argument("--location", action="append", choices=TRASHABLE_LOCATIONS)
    parser.add_argument("--kind", choices=("video", "image", "audio", "archive", "url", "other"),
                        default="")
    parser.add_argument("--out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    locations = tuple(args.location or ())
    selected = select_candidates(args.db, min_score=args.min_score,
                                 locations=locations, kind=args.kind)
    output = args.out or GENERATED_DIR / time.strftime("junk-trash-%Y%m%d-%H%M%S.csv")
    rows = [{field: item.get(field, "") for field in FIELDS} for item in selected]
    for row, item in zip(rows, selected):
        row["size_mb"] = round((item.get("size") or 0) / 1048576, 1)
    write_rows(output, FIELDS, rows, atomic=True)

    total_gb = sum((item.get("size") or 0) for item in selected) / 1024 ** 3
    counts: dict[str, int] = {}
    for item in selected:
        counts[item["location"]] = counts.get(item["location"], 0) + 1
    print(f"评分≥{args.min_score} 的候选 {len(selected)} 条 / {total_gb:.2f} GB，"
          f"按来源 {counts or '无'} → {output}")
    for item in selected[:15]:
        print(f"  {item['score']:>3} {item['location']:<6} {item['medium']:<6} "
              f"{(item.get('size') or 0)/1048576:>9.1f}MB {str(item.get('name'))[:44]!r}"
              f" | {item.get('why')}")
    if len(selected) > 15:
        print(f"  …… 其余 {len(selected) - 15} 条见 CSV")

    if not args.apply:
        print("未加 --apply，只出清单；文件仍在原处。")
        return 0

    connection = open_for_write(args)
    try:
        before = counts_of(connection, {
            "trash": "SELECT count(*) FROM asset WHERE disposal='trash'",
        })
        changed = trash_assets(connection, [int(item["id"]) for item in selected])
        after = counts_of(connection, {
            "trash": "SELECT count(*) FROM asset WHERE disposal='trash'",
        })
        integrity, foreign_keys = verify_after_write(connection)
    finally:
        connection.close()
    if integrity != "ok" or foreign_keys:
        raise RuntimeError(f"写入后 ledger 校验失败：integrity={integrity} foreign_keys={foreign_keys}")
    print(f"已移入回收站 {changed} 条；回收站 {before['trash']} → {after['trash']}。"
          f"备份 {args.backup}；文件未删除，清空回收站才会真正删除。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
