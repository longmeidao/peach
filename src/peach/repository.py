from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaAsset:
    id: int
    path: str | None
    snapshot_path: str | None
    stash_scene_id: int | None


class LedgerRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def media_asset(self, asset_id: int) -> MediaAsset | None:
        connection = sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                "SELECT id,path,snapshot_path,stash_scene_id FROM asset WHERE id=?",
                (asset_id,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return MediaAsset(row["id"], row["path"], row["snapshot_path"], row["stash_scene_id"])
