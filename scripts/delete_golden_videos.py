"""Delete the explicitly identified golden videos with a ledger audit trail."""
from __future__ import annotations

import datetime
import os
import sqlite3
from pathlib import Path

from peach.review_csv import write_rows


DATABASE = Path(r"R:\peach-data\database\ledger.db")
REVIEW_DIR = Path(r"R:\peach-data\review")
IDS = (32533, 32534, 32535, 32536, 32537)
ASSET_TABLES = (
    "asset_tag", "media_binding", "activity_event", "asset_entity",
    "watch_queue", "asset_search", "asset_preference",
    "asset_tag_preference", "asset_quality_goal",
)


def main() -> int:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DATABASE.with_name(f"ledger.pre-golden-delete-{stamp}.db")
    report = REVIEW_DIR / f"golden-video-delete-{stamp}.csv"
    connection = sqlite3.connect(DATABASE)
    backup_connection = sqlite3.connect(backup)
    connection.backup(backup_connection)
    backup_connection.close()
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT id,name,location,path,size,snapshot_path FROM asset "
        "WHERE id IN (?,?,?,?,?)", IDS,
    ).fetchall()
    if len(rows) != len(IDS):
        raise RuntimeError(f"expected {len(IDS)} assets, found {len(rows)}")

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    report_rows = []
    for row in rows:
        path = row["path"]
        existed = os.path.isfile(path)
        if existed:
            os.remove(path)
        report_rows.append({
            "id": row["id"], "name": row["name"], "location": row["location"],
            "path": path, "size": row["size"], "snapshot_path": row["snapshot_path"],
            "file_exists": existed, "deleted": not os.path.exists(path),
        })
    if not all(item["deleted"] for item in report_rows):
        raise RuntimeError("one or more media files remain")

    write_rows(report, report_rows[0].keys(), report_rows)

    marks = ",".join("?" * len(IDS))
    try:
        connection.execute("BEGIN IMMEDIATE")
        for table in ASSET_TABLES:
            connection.execute(f"DELETE FROM {table} WHERE asset_id IN ({marks})", IDS)
        connection.execute(f"DELETE FROM asset WHERE id IN ({marks})", IDS)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    print({"backup": str(backup), "report": str(report), "deleted_ids": IDS})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
