#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""映射表改了去向之后，把已落库的 javinizer 标签按这次的改动跟上。

标签候选在抓取那一刻就映射成了中文。映射表后来改了去向（`巨尻` 从「美臀」分出「巨臀」、
`可愛い` 从「高颜值」分出「可爱」），已落库的行不会自己跟着变。这里从每条标签行记着的
`raw_snapshot` 读回来源原词，用 `--since` 那一版的映射和现在的映射各算一遍整套，只把两者
的差加减到账本现有的那一套上：按整套比，同一部片 `巨尻` 与 `美尻` 都在时「美臀」留下；
只套差，账本与快照之间早就存在、和这次改动无关的出入原样不动。

写入复用 `/review` 批准时的那一份 `_apply_metadata_candidate`，写出来的行与批准的一样；
不登记 review_decision，这不是新的批准。快照缺失或读不了、没有 genre 字段、套完一个
标签都不剩的，原样不动并报数。

默认只产出复核 CSV，`--apply` 才写 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import types
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR
from peach.field_owners import script_owner
from peach.genre_decisions import load_genre_decisions
from peach.genre_taxonomy import map_genres
from peach.metadata_auto_apply import _apply_metadata_candidate
from peach.review_csv import write_rows
from peach.scripting import add_ledger_write_args, counts_of, open_for_write, verify_after_write

OWNER = script_owner("reproject_snapshot_tags")
FIELDS = ("asset_id", "code", "source", "status", "removed", "added", "snapshot")
#: 每组的去向；只有 `REWRITE` 会写库。
REWRITE, SAME, NO_SNAPSHOT, NO_GENRES, EMPTY = "重写", "不受影响", "快照缺失", "无 genre", "套完为空"
TAXONOMY = "src/peach/genre_taxonomy.py"


def taxonomy_at(revision: str) -> types.ModuleType:
    """`revision` 那一版的映射模块。它只依赖标准库，取出源码直接执行就是当时的行为。"""
    source = subprocess.run(["git", "show", f"{revision}:{TAXONOMY}"], cwd=PROJECT_ROOT,
                            capture_output=True, text=True, encoding="utf-8", check=True).stdout
    module = types.ModuleType(f"genre_taxonomy_at_{revision}")
    exec(compile(source, f"{revision}:{TAXONOMY}", "exec"), module.__dict__)
    return module


def snapshot_genres(path: str) -> list | None:
    """快照里的来源原词。javinizer-go 的快照外面包一层 `result`，资料快照直接就是正文。"""
    try:
        wrapper = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(wrapper, dict):
        return None
    payload = wrapper.get("result") if isinstance(wrapper.get("result"), dict) else wrapper
    genres = payload.get("genres")
    return genres if isinstance(genres, list) else None


def ledger_groups(connection: sqlite3.Connection) -> list[dict]:
    """每条资产在每个 javinizer 来源下的现有标签，连同那批标签落库时记下的出处。"""
    groups: dict[tuple[int, str], dict] = {}
    for asset_id, code, path, source, confidence, tag in connection.execute(
            "SELECT t.asset_id,a.code,a.path,t.source,t.confidence,t.tag FROM asset_tag t "
            "JOIN asset a ON a.id=t.asset_id WHERE t.source LIKE 'javinizer:%:tag' "
            "ORDER BY t.asset_id,t.source"):
        group = groups.setdefault((asset_id, source), {
            "asset_id": asset_id, "code": code or "", "path": path, "source": source,
            "confidence": confidence, "tags": set(), "metadata": {}})
        group["tags"].add(tag)
    for asset_id, source, metadata_json in connection.execute(
            "SELECT asset_id,source,metadata_json FROM asset_entity "
            "WHERE role='tag' AND source LIKE 'javinizer:%:tag'"):
        group = groups.get((asset_id, source))
        if group is not None and not group["metadata"]:
            group["metadata"] = json.loads(metadata_json or "{}")
    return list(groups.values())


def judge(group: dict, before: types.ModuleType, decisions: dict) -> dict:
    """一组标签的去向与增减；`new` 是套完差之后的整套，只在 `REWRITE` 时有用。"""
    snapshot = str(group["metadata"].get("raw_snapshot") or "")
    genres = snapshot_genres(snapshot) if snapshot else None
    old = set(before.map_genres(genres, decisions)[0]) if genres else set()
    now = map_genres(genres, decisions)[0] if genres else []
    removed = (old - set(now)) & group["tags"]
    added = [tag for tag in now if tag not in old and tag not in group["tags"]]
    new = sorted(group["tags"] - removed) + added
    if not snapshot or not Path(snapshot).is_file():
        status = NO_SNAPSHOT
    elif genres is None:
        status = NO_GENRES
    elif not (removed or added):
        status = SAME
    else:
        status = REWRITE if new else EMPTY
    changed = status == REWRITE
    return {**group, "status": status, "new": new, "snapshot": snapshot,
            "removed": "、".join(sorted(removed)) if changed else "",
            "added": "、".join(added) if changed else ""}


def rewrite(connection: sqlite3.Connection, row: dict, now: str) -> None:
    """把重算出的整套写回去，形状与 `/review` 批准的候选一致。"""
    metadata = row["metadata"]
    site = row["source"].split(":")[1]
    group = {"field": "tags", "code": row["code"], "query": row["code"],
             "asset_id": row["asset_id"], "asset_path": row["path"],
             "item_key": metadata.get("review_item") or f"{row['code']}:tags"}
    candidate = {key: metadata.get(key) for key in (
        "provider", "source_url", "provider_id", "content_id", "raw_snapshot", "candidate_key")}
    candidate.update(source=site, confidence=row["confidence"], value=row["new"],
                     candidate_key=metadata.get("candidate_key") or f"reproject:{row['asset_id']}:{site}")
    _apply_metadata_candidate(connection, group, candidate, now, OWNER)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="映射表改了去向之后，把已落库的 javinizer 标签跟上")
    add_ledger_write_args(parser)
    parser.add_argument("--since", required=True,
                        help="改动之前的那一版（git 提交或分支），只套它与现在之间的映射差")
    parser.add_argument("--review-csv", type=Path,
                        default=GENERATED_DIR / "snapshot-tag-reprojection.csv")
    return parser


def run(args: argparse.Namespace) -> int:
    before = taxonomy_at(args.since)
    connection = open_for_write(args)
    connection.row_factory = sqlite3.Row
    try:
        decisions = load_genre_decisions(connection)
        rows = [judge(group, before, decisions) for group in ledger_groups(connection)]
        tally = Counter(row["status"] for row in rows)
        print("资产×来源 {} 组：".format(len(rows))
              + "，".join(f"{status} {count}" for status, count in tally.most_common()))
        changes = Counter((kind, tag) for row in rows for kind in ("removed", "added")
                          for tag in row[kind].split("、") if tag)
        for (kind, tag), count in changes.most_common():
            print(f"  {'去掉' if kind == 'removed' else '加上'} {tag}：{count} 组")
        if args.apply:
            apply_rows(connection, [row for row in rows if row["status"] == REWRITE])
    finally:
        connection.close()
    write_rows(args.review_csv, FIELDS, [{field: row[field] for field in FIELDS}
                                         for row in rows if row["status"] != SAME])
    print(f"复核 CSV → {args.review_csv}")
    if not args.apply:
        print("这是预览：未写 ledger。确认后再加 --apply --backup。")
    return 0


def apply_rows(connection: sqlite3.Connection, rows: list[dict]) -> None:
    extra = {"javinizer_tag": "SELECT count(*) FROM asset_tag WHERE source LIKE 'javinizer:%:tag'"}
    before = counts_of(connection, extra)
    now = datetime.now(timezone.utc).isoformat()
    failures: list[str] = []
    with connection:
        for row in rows:
            try:
                rewrite(connection, row, now)
            except ValueError as error:
                failures.append(f"{row['code'] or row['asset_id']} {row['source']}：{error}")
    after = counts_of(connection, extra)
    integrity, violations = verify_after_write(connection)
    print(f"已重写 {len(rows) - len(failures)} 组；javinizer 标签行 "
          f"{before['javinizer_tag']} → {after['javinizer_tag']}")
    print(f"  自检：integrity_check={integrity}，外键违规 {violations} 条")
    for line in failures:
        print(f"  跳过 {line}")


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
