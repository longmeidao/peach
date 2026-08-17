from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaAsset:
    id: int
    path: str | None
    snapshot_path: str | None
    bindings: tuple[tuple[str, str], ...] = ()
    location: str | None = None
    name: str | None = None
    duration: float | None = None
    size: int | None = None

    def external_id(self, backend: str) -> str | None:
        return next((value for name, value in self.bindings if name == backend), None)


class LedgerRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def media_asset(self, asset_id: int) -> MediaAsset | None:
        connection = sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                "SELECT id,path,snapshot_path,location,name,duration,size "
                "FROM asset WHERE id=?",
                (asset_id,),
            ).fetchone()
            bindings = connection.execute(
                "SELECT backend,external_id FROM media_binding WHERE asset_id=? "
                "ORDER BY backend,external_id",
                (asset_id,),
            ).fetchall() if row is not None else ()
        finally:
            connection.close()
        if row is None:
            return None
        return MediaAsset(
            row["id"],
            row["path"],
            row["snapshot_path"],
            tuple((item["backend"], item["external_id"]) for item in bindings),
            row["location"],
            row["name"],
            row["duration"],
            row["size"],
        )
