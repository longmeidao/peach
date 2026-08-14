#!/usr/bin/env python3
"""在真实 ledger 的临时 SQLite backup 上演练迁移；源库只读。"""
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from peach.migrations import sqlite_backup, upgrade


SOURCE = Path(r"R:\Resources\Intake\ledger.db")
MIGRATIONS = PROJECT_ROOT / "migrations"


def counts(path: Path) -> tuple[int, int]:
    con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return (
            con.execute("SELECT COUNT(*) FROM asset").fetchone()[0],
            con.execute("SELECT COUNT(*) FROM asset_tag").fetchone()[0],
        )
    finally:
        con.close()


def main():
    with tempfile.TemporaryDirectory(prefix="peach-migration-copy-") as tmp:
        root = Path(tmp)
        copy = root / "ledger-copy.db"
        backup = root / "ledger-before-upgrade.db"
        sqlite_backup(SOURCE, copy)
        before = counts(copy)
        done = upgrade(copy, MIGRATIONS, backup)
        after = counts(copy)
        con = sqlite3.connect(copy)
        try:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            versions = [row[0] for row in con.execute(
                "SELECT version FROM schema_migration ORDER BY version"
            )]
        finally:
            con.close()
        if before != after:
            raise SystemExit(f"计数变化：{before} -> {after}")
        if integrity != "ok":
            raise SystemExit(f"integrity_check: {integrity}")
        print({"asset": after[0], "asset_tag": after[1], "versions": versions,
               "applied": [m.version for m in done], "integrity": integrity})


if __name__ == "__main__":
    main()
