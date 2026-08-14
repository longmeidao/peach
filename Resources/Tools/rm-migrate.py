#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path

from peach.migrations import plan, upgrade


HERE = Path(__file__).resolve().parent
DEFAULT_DB = Path(r"R:\Resources\Intake\ledger.db")
DEFAULT_MIGRATIONS = HERE / "migrations"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Peach SQLite 正式迁移器（默认只读 status）")
    parser.add_argument("command", choices=("status", "upgrade"), nargs="?", default="status")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--migrations", type=Path, default=DEFAULT_MIGRATIONS)
    parser.add_argument("--yes", action="store_true", help="允许修改默认真实 ledger.db")
    args = parser.parse_args(argv)

    all_migrations, pending = plan(args.db, args.migrations)
    print(f"数据库: {args.db}")
    print(f"迁移: {len(all_migrations)} 个，待应用: {len(pending)} 个")
    for migration in pending:
        print(f"  PENDING {migration.version} {migration.name}")
    if args.command == "status" or not pending:
        return 0

    is_real = args.db.resolve() == DEFAULT_DB.resolve()
    if is_real and not args.yes:
        raise SystemExit("拒绝修改真实 ledger.db；确认维护窗口后显式加 --yes")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = args.db.with_name(f"{args.db.stem}.pre-migrate-{stamp}{args.db.suffix}")
    done = upgrade(args.db, args.migrations, backup)
    print(f"备份: {backup}")
    print("已应用: " + ", ".join(m.version for m in done))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
