"""实体事实种子包的导出与导入（ADR-0073）。

    seed_pack.py export --version 2026-09-25
    seed_pack.py import
    seed_pack.py import --apply --backup peach-data/database/ledger.pre-seed-<时间戳>.db

`export` 只读账本，把女优、厂牌与事务所的公开事实写成 `resources/seed/entities.json`；
同一账本、同一版本号两次导出逐字节一致。内容变了就必须换版本串：`seed-import:<版本>` 是导入
的幂等键，导过旧内容的机器会把同版本的新包当作已导过而跳过，所以版本串不比现有文件新的导出被
拒绝、不动文件、退出码 2。`import` 默认 dry-run，只报会补多少；
`--apply` 必须同时给 `--backup`。撤回：`revert_auto_landing.py --source auto:seed`。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import seed_pack  # noqa: E402
from peach.config import DATABASE_PATH  # noqa: E402
from peach.scripting import add_ledger_write_args, open_for_write, open_readonly, verify_after_write  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="从本机账本导出种子包")
    export.add_argument("--db", type=Path, default=DATABASE_PATH, help="账本路径")
    export.add_argument("--version", default=date.today().isoformat(),
                        help="包版本号，也是批次号的后半段；默认当天日期")
    export.add_argument("--out", type=Path, default=seed_pack.DEFAULT_PACK, help="落盘路径")
    landing = commands.add_parser("import", help="把种子包补进本机账本")
    add_ledger_write_args(landing)
    landing.add_argument("--pack", type=Path, default=seed_pack.DEFAULT_PACK, help="种子包路径")
    return parser


def _version_in(text: str) -> str | None:
    """现有文件里的版本串；文件不是种子包就当没有版本，让导出照常覆盖。"""
    try:
        return str(json.loads(text)["version"])
    except (ValueError, KeyError, TypeError):
        return None


def export(args: argparse.Namespace) -> int:
    connection = open_readonly(args.db)
    try:
        pack = seed_pack.export_pack(connection, version=args.version)
    finally:
        connection.close()
    text = seed_pack.dump(pack)
    existing = args.out.read_text(encoding="utf-8") if args.out.is_file() else None
    changed = existing != text
    summary = {"out": str(args.out), "version": pack["version"], "changed": changed, **pack["counts"]}
    current = _version_in(existing) if existing is not None else None
    # 版本串按字典序比：ISO 日期加 `.n` 后缀在同一天十次以内单调；缺省的当天日期退不回已发过的 `.1`。
    if changed and current is not None and pack["version"] <= current:
        print(json.dumps({**summary, "written": False,
                          "error": f"内容变了而版本串 {pack['version']} 不比文件里的 {current} 新：导入以"
                                   " seed-import:<版本> 判有没有导过，导过旧内容的机器会跳过这份新内容；换一个新版本串再导"},
                         ensure_ascii=False))
        return 2
    if changed:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def land(args: argparse.Namespace) -> int:
    pack = seed_pack.load(args.pack)
    connection = open_for_write(args)
    try:
        if not args.apply:
            report = seed_pack.plan(connection, pack)
            print(json.dumps(report, ensure_ascii=False))
            print("dry-run；确认无误后加 --apply --backup <路径>")
            return 0
        with connection:
            report = seed_pack.land(connection, pack)
        integrity, orphans = verify_after_write(connection)
    finally:
        connection.close()
    print(json.dumps({**report, "integrity_check": integrity, "foreign_key_check": orphans},
                     ensure_ascii=False))
    return 0 if integrity == "ok" and orphans == 0 else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return export(args) if args.command == "export" else land(args)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
