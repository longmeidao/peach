#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""摘掉发行物目录上多余的一层，并去掉目录名里的广告标记。

实测形态是 `B:\日本\Prestige\TRE-080\[44x.me]tre-080\TRE-080.mp4`：`TRE-080` 底下
只有一个子目录，名字还是同一个番号、只多挂了个广告前缀。这一层既不分类也不区分，
只是把路径加长一段，还把广告带进了目录树。

判据只有一条，不是「父目录只有一个子目录」——真实数据里 747 个这样的父目录多数是
有意义的（`古川结爱合集` 底下就一个 `FC2-PPV-…`，不能合），而是**名字冗余**：
摘掉广告、抹掉大小写与分隔符之后子目录名等于父目录名，才算多余的一层。

`scripts/clean_names.py` 只处理带扩展名的文件名（没有扩展名直接原样返回），
目录名用不上它；广告正则则复用 `peach.catalog_rules`，不再抄一份。

顺序固定：先备份 SQLite，再动文件，最后改账本；账本写失败就把文件移回去。
反过来先改账本会留下一批指向不存在路径的行。

默认只产出改动计划，`--apply` 才动文件和 ledger 且必须给 `--backup`。
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path, PureWindowsPath

# 仓库既有约定（job_status.py 等 8 个脚本同样写法）：脚本直接跑时把 src 挂上，
# 免得用户必须先设 PYTHONPATH。2026-09-02 就是漏了这段，交出去的命令直接
# ModuleNotFoundError。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.catalog_rules import promo_free_key, strip_promo_markers
from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.migrations import sqlite_backup
from peach.platform import translate_ledger_path
from peach.review_csv import write_rows


PLAN_FIELDS = ["kind", "ledger_dir", "target_dir", "assets", "verified"]


def _directories(connection: sqlite3.Connection) -> dict[str, set[str]]:
    """账本认识的目录树：目录 -> 直接子目录集合。

    账本只记文件，不记目录，所以目录树是从 `asset.path` 反推出来的。它必然不完整
    （旁挂的字幕、封面、空目录都不在里面），所以任何一条计划在落地前都要再用真实
    文件系统核一遍。
    """
    children: dict[str, set[str]] = defaultdict(set)
    for (path,) in connection.execute(
        "SELECT path FROM asset WHERE path IS NOT NULL AND trim(path)<>''"
    ):
        parts = PureWindowsPath(str(path)).parts
        for index in range(1, len(parts) - 1):
            parent = str(PureWindowsPath(*parts[:index + 1]))
            child = str(PureWindowsPath(*parts[:index + 2]))
            children[parent].add(child)
    return children


def plan_operations(connection: sqlite3.Connection) -> list[dict[str, str]]:
    """列出要做的目录操作，深的排前面。

    两种操作：`collapse` 把冗余子目录里的东西提到父目录再删掉它；`rename` 只把
    目录名里的广告标记摘掉。被 collapse 干掉的目录不再参与 rename——它已经不存在了。
    """
    children = _directories(connection)
    counts = _asset_counts(connection)
    collapsed: set[str] = set()
    operations: list[dict[str, str]] = []
    for parent in sorted(children):
        kids = children[parent]
        if len(kids) != 1:
            continue
        child = next(iter(kids))
        child_name = PureWindowsPath(child).name
        parent_name = PureWindowsPath(parent).name
        key = promo_free_key(child_name)
        if not key or key != promo_free_key(parent_name):
            continue
        collapsed.add(child)
        operations.append({
            "kind": "collapse", "ledger_dir": child, "target_dir": parent,
            "assets": str(counts.get(child, 0)), "verified": "",
        })
    for directory in sorted(set(children) | {c for kids in children.values() for c in kids}):
        if directory in collapsed:
            continue
        name = PureWindowsPath(directory).name
        cleaned = strip_promo_markers(name)
        if not cleaned or cleaned == name:
            continue
        parent = PureWindowsPath(directory).parent
        operations.append({
            "kind": "rename", "ledger_dir": directory,
            "target_dir": str(parent / cleaned),
            "assets": str(counts.get(directory, 0)), "verified": "",
        })
    operations.sort(key=lambda row: len(PureWindowsPath(row["ledger_dir"]).parts), reverse=True)
    return operations


def _asset_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for (path,) in connection.execute(
        "SELECT path FROM asset WHERE path IS NOT NULL AND trim(path)<>''"
    ):
        parts = PureWindowsPath(str(path)).parts
        for index in range(1, len(parts)):
            counts[str(PureWindowsPath(*parts[:index + 1]))] += 1
    return counts


def verify(operation: dict[str, str], resolve=translate_ledger_path) -> str:
    """用真实文件系统核一条计划，返回 `ok` 或拒绝原因。

    账本不知道旁挂文件，所以 collapse 前必须确认父目录里除了这个子目录真的什么都没有；
    只按账本判会把父目录里的封面、字幕留在原地，或者在提升时撞名。
    """
    source = resolve(operation["ledger_dir"])
    target = resolve(operation["target_dir"])
    if not source.is_dir():
        return "跳过：源目录不存在或未挂载"
    if operation["kind"] == "collapse":
        try:
            siblings = [entry.name for entry in target.iterdir()]
        except OSError as error:
            return f"跳过：父目录读不到（{error.__class__.__name__}）"
        extra = [name for name in siblings if name != source.name]
        if extra:
            return f"跳过：父目录还有 {len(extra)} 项（{extra[0]}）"
        return "ok"
    if target.exists():
        return "跳过：目标名已存在"
    return "ok"


def _rewrite(path: str, operation: dict[str, str]) -> str | None:
    """把一条资产路径按一个操作改写；不在这个目录下就返回 None。"""
    source = PureWindowsPath(operation["ledger_dir"])
    parts = PureWindowsPath(path).parts
    prefix = source.parts
    if len(parts) <= len(prefix) or tuple(p.casefold() for p in parts[:len(prefix)]) != tuple(
            p.casefold() for p in prefix):
        return None
    rest = parts[len(prefix):]
    return str(PureWindowsPath(operation["target_dir"], *rest))


def plan_paths(connection: sqlite3.Connection,
               operations: list[dict[str, str]]) -> list[dict[str, str]]:
    """按操作顺序（深的在前）逐条改写账本路径，返回真正会变的行。"""
    rows: list[dict[str, str]] = []
    for asset_id, path in connection.execute(
        "SELECT id,path FROM asset WHERE path IS NOT NULL AND trim(path)<>'' ORDER BY id"
    ):
        current = str(path)
        for operation in operations:
            rewritten = _rewrite(current, operation)
            if rewritten is not None:
                current = rewritten
        if current != str(path):
            rows.append({"id": str(asset_id), "old_path": str(path), "new_path": current})
    return rows


def apply_operation(operation: dict[str, str], resolve=translate_ledger_path) -> list[tuple[Path, Path]]:
    """执行一条操作，返回已完成的移动，用于回滚。"""
    source = resolve(operation["ledger_dir"])
    target = resolve(operation["target_dir"])
    if operation["kind"] == "rename":
        source.rename(target)
        return [(source, target)]
    done: list[tuple[Path, Path]] = []
    for entry in sorted(source.iterdir()):
        moved = target / entry.name
        entry.rename(moved)
        done.append((entry, moved))
    source.rmdir()
    done.append((source, source))  # 记一笔，回滚时重建这个目录
    return done


def rollback(done: list[tuple[Path, Path]]) -> None:
    for source, target in reversed(done):
        try:
            if source == target:
                source.mkdir(exist_ok=True)
            else:
                target.rename(source)
        except OSError:
            print(f"  回滚失败，需要人工处理：{target} -> {source}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="摘掉冗余的发行物目录层与目录名广告标记")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--plan-csv", type=Path,
                        default=GENERATED_DIR / "flatten-release-dirs.csv")
    parser.add_argument("--path-csv", type=Path,
                        default=GENERATED_DIR / "flatten-release-dirs-paths.csv")
    parser.add_argument("--kind", choices=["collapse", "rename"],
                        help="只处理一种操作；默认两种都做")
    parser.add_argument("--apply", action="store_true", help="动文件和 ledger；默认只出计划")
    parser.add_argument("--backup", type=Path, help="--apply 必需：写库前的 SQLite 备份路径")
    return parser


def run(args: argparse.Namespace) -> int:
    if args.apply and not args.backup:
        raise SystemExit("--apply 必须同时给 --backup")
    connection = sqlite3.connect(args.db)
    try:
        operations = plan_operations(connection)
        if args.kind:
            operations = [row for row in operations if row["kind"] == args.kind]
        for operation in operations:
            operation["verified"] = verify(operation)
        write_rows(args.plan_csv, PLAN_FIELDS, operations)
        ready = [row for row in operations if row["verified"] == "ok"]
        rows = plan_paths(connection, ready)
        write_rows(args.path_csv, ["id", "old_path", "new_path"], rows)
        collapses = sum(1 for row in ready if row["kind"] == "collapse")
        print(f"计划 {len(operations)} 条，可执行 {len(ready)} 条"
              f"（collapse {collapses}，rename {len(ready) - collapses}），"
              f"影响账本路径 {len(rows)} 条")
        print(f"  计划 CSV：{args.plan_csv}")
        print(f"  路径 CSV：{args.path_csv}")
        # 逐条打印被跳过的路径会在 GBK 控制台上崩掉（媒体名里有 emoji 和生僻字），
        # 而且量级是四位数。原因按类归并打印，明细留在计划 CSV 里。
        skipped: dict[str, int] = defaultdict(int)
        for operation in operations:
            if operation["verified"] != "ok":
                skipped[operation["verified"].split("（")[0]] += 1
        for reason, count in sorted(skipped.items(), key=lambda item: -item[1]):
            print(f"  {reason}：{count} 条")
        if not ready:
            print("  没有可执行的操作")
            return 0
        if not args.apply:
            print("  未改动任何东西（加 --apply --backup 才执行）")
            return 0

        before = connection.execute("SELECT count(*) FROM asset").fetchone()[0]
        sqlite_backup(args.db, args.backup)
        print(f"  已备份到 {args.backup}")

        done: list[tuple[Path, Path]] = []
        try:
            for operation in ready:
                done.extend(apply_operation(operation))
            with connection:
                for row in rows:
                    connection.execute(
                        "UPDATE asset SET path=? WHERE id=? AND path=?",
                        (row["new_path"], int(row["id"]), row["old_path"]))
        except Exception:
            print("  执行失败，回滚已完成的移动")
            rollback(done)
            raise

        after = connection.execute("SELECT count(*) FROM asset").fetchone()[0]
        print(f"  已执行 {len(ready)} 条；资产 {before} -> {after}")
        return 1 if before != after else 0
    finally:
        connection.close()


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
