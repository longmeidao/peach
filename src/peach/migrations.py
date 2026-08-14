from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


MIGRATION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migration(
  version TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  checksum TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path
    sql: str
    checksum: str


def discover(directory: Path) -> list[Migration]:
    migrations: list[Migration] = []
    for path in sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        version, name = path.stem.split("_", 1)
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        migrations.append(Migration(version, name, path, sql, checksum))
    versions = [m.version for m in migrations]
    if len(versions) != len(set(versions)):
        raise ValueError("migration 版本重复")
    return migrations


def applied(connection: sqlite3.Connection) -> dict[str, str]:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='schema_migration'"
    ).fetchone()
    if not exists:
        return {}
    return {row[0]: row[1] for row in connection.execute(
        "SELECT version,checksum FROM schema_migration ORDER BY version"
    )}


def plan(db_path: Path, directory: Path) -> tuple[list[Migration], list[Migration]]:
    all_migrations = discover(directory)
    # status 对既有数据库使用 SQLite 只读 URI，保证不会创建 journal/WAL 或触发隐式写入。
    connection = (sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
                  if db_path.exists() else sqlite3.connect(db_path))
    try:
        done = applied(connection)
    finally:
        connection.close()
    for migration in all_migrations:
        if migration.version in done and done[migration.version] != migration.checksum:
            raise RuntimeError(f"已应用 migration {migration.version} 的 checksum 已变化")
    return all_migrations, [m for m in all_migrations if m.version not in done]


def sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    src = sqlite3.connect(source)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def upgrade(db_path: Path, directory: Path, backup_path: Path | None = None) -> list[Migration]:
    _, pending = plan(db_path, directory)
    if not pending:
        return []
    if backup_path is not None:
        sqlite_backup(db_path, backup_path)

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        for migration in pending:
            stamp = datetime.now(timezone.utc).isoformat()
            reconcile = _legacy_reconcile_sql(connection) if migration.version == "0000" else ""
            script = (
                "BEGIN IMMEDIATE;\n"
                + MIGRATION_TABLE_SQL
                + migration.sql
                + reconcile
                + "\nINSERT INTO schema_migration(version,name,checksum,applied_at) VALUES("
                + ",".join(_quote(x) for x in (migration.version, migration.name, migration.checksum, stamp))
                + ");\nCOMMIT;"
            )
            try:
                connection.executescript(script)
            except Exception:
                if connection.in_transaction:
                    connection.rollback()
                raise
        connection.execute("PRAGMA optimize")
    finally:
        connection.close()
    return pending


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _legacy_reconcile_sql(connection: sqlite3.Connection) -> str:
    """把 Claude 阶段即席列纳入 0000 正式迁移；新库由 0000 SQL 一次创建。"""
    exists = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='asset'"
    ).fetchone()
    if not exists:
        return ""
    have = {row[1] for row in connection.execute("PRAGMA table_info(asset)")}
    expected = {
        "studio": "TEXT",
        "feedback": "TEXT",
        "disposal": "TEXT",
        "leave_ratio": "REAL",
        "play_seconds": "REAL",
        "feedback_at": "REAL",
        "seek_count": "INTEGER",
        "max_reached": "REAL",
    }
    return "".join(
        f"\nALTER TABLE asset ADD COLUMN {name} {declaration};"
        for name, declaration in expected.items() if name not in have
    )
