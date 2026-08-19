#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""去掉本地媒体根下多余的一层分类目录。

本地库的实际形态是 `R:\Media\创作者\<名字>\<文件>`，而 `R:\Media` 下**只有**
`创作者` 一个子目录，2552 条本地资产 100% 落在它下面。这一层既不分类也不区分，
只是把每条路径都加长一段。

它甚至已经名不副实：`合集-洛丽塔 多创作者`、`合集-足交 多创作者`、`桉X合集` 是
合集而不是创作者，却也放在 `创作者\` 底下。番号发行物则全在网盘挂载（`A:`/`B:`）
上，不在本地盘。

按 ADR-0013，目录名本来就只是候选证据、不是身份真相——真相在 `asset_entity` 的
关系和 provenance 里，所以删掉这一层不会丢任何身份信号。

顺序固定：先备份 SQLite，再移动目录，最后改账本；账本写失败就把目录移回去。
反过来先改账本会留下一批指向不存在路径的行。

默认只产出改动计划，`--apply` 才动文件和 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path, PureWindowsPath

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.migrations import sqlite_backup
from peach.platform import translate_ledger_path


#: 要去掉的那一层。账本里是 Windows 形态，比较时不区分大小写。
LEVEL = "创作者"
#: 只处理本地盘上的资产；网盘挂载的路径不在这次范围内。
LEDGER_PREFIX = r"R:\Media"


def plan_paths(connection: sqlite3.Connection) -> list[dict[str, str]]:
    """列出要改写的账本路径。返回空表示已经是扁平结构。"""
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT id, path FROM asset WHERE location='local' ORDER BY id"
    ).fetchall()
    plan: list[dict[str, str]] = []
    for row in rows:
        parts = PureWindowsPath(row["path"]).parts
        # ('R:\\', 'Media', '创作者', '<名字>', ...)
        if len(parts) < 4 or parts[1].casefold() != "media" or parts[2] != LEVEL:
            continue
        plan.append({
            "id": str(row["id"]),
            "old_path": row["path"],
            "new_path": str(PureWindowsPath(parts[0], parts[1], *parts[3:])),
        })
    return plan


def plan_moves(media_root: Path) -> list[tuple[Path, Path]]:
    """`media/创作者/<X>` -> `media/<X>`。同卷改名，只动元数据。"""
    level = media_root / LEVEL
    if not level.is_dir():
        return []
    return [(child, media_root / child.name) for child in sorted(level.iterdir())
            if not child.name.startswith(".")]


def collisions(moves: list[tuple[Path, Path]]) -> list[Path]:
    return [target for _, target in moves if target.exists()]


def apply_moves(moves: list[tuple[Path, Path]]) -> list[tuple[Path, Path]]:
    done: list[tuple[Path, Path]] = []
    for source, target in moves:
        source.rename(target)
        done.append((source, target))
    return done


def rollback_moves(done: list[tuple[Path, Path]]) -> None:
    for source, target in reversed(done):
        try:
            target.rename(source)
        except OSError:
            print(f"  回滚失败，需要人工处理：{target} -> {source}")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "old_path", "new_path"])
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="去掉本地媒体根下的一层分类目录")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--media-root", type=Path,
                        default=translate_ledger_path(LEDGER_PREFIX))
    parser.add_argument("--plan-csv", type=Path,
                        default=GENERATED_DIR / "flatten-media-level.csv")
    parser.add_argument("--apply", action="store_true", help="动文件和 ledger；默认只出计划")
    parser.add_argument("--backup", type=Path, help="--apply 必需：写库前的 SQLite 备份路径")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    connection = sqlite3.connect(args.db)
    try:
        rows = plan_paths(connection)
        moves = plan_moves(args.media_root)
        write_csv(args.plan_csv, rows)
        print(f"媒体根：{args.media_root}")
        print(f"待改写账本路径 {len(rows)} 条，待移动目录 {len(moves)} 个，计划 CSV：{args.plan_csv}")
        clashes = collisions(moves)
        if clashes:
            raise SystemExit(f"目标已存在，拒绝移动：{clashes[:5]}")
        if not rows and not moves:
            print("  已经是扁平结构，无需处理")
            return 0
        if not args.apply:
            print("  未改动任何东西（加 --apply --backup 才执行）")
            return 0

        before = connection.execute(
            "SELECT count(*) FROM asset WHERE location='local'").fetchone()[0]
        sqlite_backup(args.db, args.backup)
        print(f"  已备份到 {args.backup}")

        done = apply_moves(moves)
        print(f"  已移动目录 {len(done)} 个")
        try:
            with connection:
                for row in rows:
                    connection.execute(
                        "UPDATE asset SET path=? WHERE id=? AND path=?",
                        (row["new_path"], int(row["id"]), row["old_path"]))
        except Exception:
            print("  账本写入失败，回滚目录移动")
            rollback_moves(done)
            raise

        after = connection.execute(
            "SELECT count(*) FROM asset WHERE location='local'").fetchone()[0]
        left = connection.execute(
            "SELECT count(*) FROM asset WHERE location='local' AND path LIKE ?",
            (f"%\\{LEVEL}\\%",)).fetchone()[0]
        empty = args.media_root / LEVEL
        if empty.is_dir() and not any(empty.iterdir()):
            empty.rmdir()
            print(f"  已删除空目录 {empty}")
        print(f"  本地资产 {before} -> {after}；仍含 `{LEVEL}` 层的路径 {left} 条")
        return 1 if (before != after or left) else 0
    finally:
        connection.close()


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
