"""只读就绪检查；不创建账本，不修复或迁移数据。"""
import sqlite3
from contextlib import closing

from .config import MIGRATIONS_DIR, PeachSettings
from .migrations import applied, discover


def database_status(path) -> str:
    if not path.is_file():
        return "missing"
    try:
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True,
                                     timeout=1)) as connection:
            connection.execute("PRAGMA query_only=ON")
            return "available" if applied(connection) else "empty"
    except (sqlite3.Error, OSError):
        return "unavailable"


def readiness(settings: PeachSettings) -> dict:
    checks = {"configured": bool(settings.configured),
              "web": settings.page_path.is_file(), "database": False, "schema": False}
    try:
        with closing(sqlite3.connect(settings.db_path.resolve().as_uri() + "?mode=ro",
                                     uri=True, timeout=1)) as connection:
            connection.execute("PRAGMA query_only=ON")
            connection.execute("SELECT id FROM asset LIMIT 1").fetchone()
            checks["database"] = True
            installed = applied(connection)
            expected = discover(MIGRATIONS_DIR)
            checks["schema"] = bool(expected) and all(
                installed.get(m.version) == m.checksum for m in expected)
    except (sqlite3.Error, OSError, ValueError):
        pass
    return {"ready": all(checks.values()), "checks": checks}
