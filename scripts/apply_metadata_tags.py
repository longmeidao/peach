#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把字段候选 CSV 里的标签直接写进 ledger，不经 `/review` 排队。

这条路是用户当轮明确授权的批量写入，不是默认流程。默认流程仍然是 `/review`：
候选带出处和置信度，由人一条条批。这里只是把同一份写入映射批量跑一遍。

写入映射复用 `peach.web_review._apply_metadata_candidate`——就是 `/review` 批准时
走的那一份。它管着删旧的 `javinizer:%` 标签行、规范化标签名、收敛被取代的口味标签，
以及 `asset_tag` 与 `asset_entity` 两处一起写。抄一份出来只会漂。

默认只统计，`--apply` 才写库且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from peach.config import DATABASE_PATH
from peach.migrations import sqlite_backup
from peach.review_csv import read_rows
from peach.web_review import _apply_metadata_candidate


def select_candidate(row: dict, source: str) -> dict | None:
    """取这一组里指定来源的候选；没有就返回 None。"""
    try:
        candidates = json.loads(str(row.get("candidates_json") or "[]"))
    except (TypeError, ValueError):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and str(candidate.get("source") or "") == source:
            return candidate
    return None


def plan(rows: list[dict], source: str, field: str) -> list[tuple[dict, dict]]:
    selected: list[tuple[dict, dict]] = []
    for row in rows:
        if str(row.get("field") or "").strip() != field:
            continue
        if str(row.get("status") or "").strip() != "candidate":
            continue
        candidate = select_candidate(row, source)
        if candidate is not None:
            selected.append((row, candidate))
    return selected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把字段候选里的标签直接写进 ledger")
    parser.add_argument("candidates", type=Path, help="scrape_codes 产出的字段候选 CSV")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--source", default="javbus", help="只写这个来源的候选值")
    parser.add_argument("--field", default="tags", help="只写这个字段")
    parser.add_argument("--apply", action="store_true", help="写库；默认只统计")
    parser.add_argument("--backup", type=Path, help="--apply 必需：写库前的 SQLite 备份路径")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    rows = list(read_rows(args.candidates))
    selected = plan(rows, args.source, args.field)
    print(f"候选 {len(rows)} 组，来源 {args.source} 的 {args.field} 候选 {len(selected)} 组")
    if not selected:
        return 0
    if not args.apply:
        print("  未写库（加 --apply --backup 才执行）")
        return 0

    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    try:
        before = connection.execute(
            "SELECT count(*) FROM asset_tag WHERE source LIKE 'javinizer:%:tag'"
        ).fetchone()[0]
        connection.close()
        sqlite_backup(args.db, args.backup)
        print(f"  已备份到 {args.backup}")
        connection = sqlite3.connect(args.db)
        connection.row_factory = sqlite3.Row

        now = datetime.now(timezone.utc).isoformat()
        applied = assets = 0
        failures: list[str] = []
        with connection:
            for group, candidate in selected:
                try:
                    assets += _apply_metadata_candidate(connection, group, candidate, now)
                    applied += 1
                except ValueError as error:
                    # 逐组失败不该拖垮整批：番号已清库、候选值不规范都是常态。
                    failures.append(f"{group.get('item_key')}: {error}")
        after = connection.execute(
            "SELECT count(*) FROM asset_tag WHERE source LIKE 'javinizer:%:tag'"
        ).fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"  写入 {applied} 组、覆盖资产 {assets} 条；"
              f"javinizer 标签行 {before} -> {after}；integrity_check {integrity}")
        if failures:
            print(f"  跳过 {len(failures)} 组：")
            for line in failures[:10]:
                print(f"    {line}")
        return 0 if integrity == "ok" else 1
    finally:
        connection.close()


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
