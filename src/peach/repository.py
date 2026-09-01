from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .catalog_rules import is_jav_code, normalise_code_key
from .entities import normalize_entity_name


class LedgerDatabase:
    """Shared SQLite connection and transaction boundary for one Peach app."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.write_lock = threading.Lock()

    def connect(self, *, write: bool = False) -> sqlite3.Connection:
        target = (
            str(self.db_path)
            if write
            else self.db_path.resolve().as_uri() + "?mode=ro"
        )
        connection = sqlite3.connect(
            target, timeout=30, check_same_thread=False, uri=not write,
        )
        connection.row_factory = sqlite3.Row
        connection.create_function("is_jav_code", 1, is_jav_code, deterministic=True)
        connection.create_function(
            "normalise_code_key", 1, normalise_code_key, deterministic=True)
        # 标签归一化必须两边同一份。SQLite 自带的 lower() 只认 ASCII：西里尔、
        # 罗马数字 Ⅱ 这类字符它原样放过，而写入时用的是 Python 的 casefold，
        # 于是「隐藏这个标签」写进去的值和查询时算出的值对不上，隐藏静默失效。
        connection.create_function(
            "peach_normalize", 1, normalize_entity_name, deterministic=True)
        return connection

    @contextmanager
    def read_connection(self):
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def write_transaction(self):
        with self.write_lock:
            connection = self.connect(write=True)
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()
            finally:
                connection.close()


@dataclass(frozen=True)
class MediaAsset:
    id: int
    path: str | None
    snapshot_path: str | None
    location: str | None = None
    name: str | None = None
    duration: float | None = None
    size: int | None = None


class LedgerRepository:
    def __init__(self, database: Path | LedgerDatabase):
        self.database = (
            database if isinstance(database, LedgerDatabase) else LedgerDatabase(database)
        )
        self.db_path = self.database.db_path

    def media_asset(self, asset_id: int) -> MediaAsset | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                "SELECT id,path,snapshot_path,location,name,duration,size "
                "FROM asset WHERE id=?",
                (asset_id,),
            ).fetchone()
        if row is None:
            return None
        return MediaAsset(
            row["id"],
            row["path"],
            row["snapshot_path"],
            row["location"],
            row["name"],
            row["duration"],
            row["size"],
        )
