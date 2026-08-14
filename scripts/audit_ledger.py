#!/usr/bin/env python3
"""只读核对真实账本的 schema 与行为水位，不执行 PRAGMA 或写操作。"""
import json
import sqlite3
from pathlib import Path


DB = Path(r"R:\Resources\Intake\ledger.db")


def main():
    connection = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        scalar = lambda sql: connection.execute(sql).fetchone()[0]
        has_events = scalar(
            "SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name='activity_event'"
        )
        result = {
            "schema_migration": scalar(
                "SELECT COUNT(*) FROM sqlite_schema WHERE type='table' AND name='schema_migration'"
            ),
            "assets": scalar("SELECT COUNT(*) FROM asset"),
            "played": scalar("SELECT COUNT(*) FROM asset WHERE COALESCE(play_count,0)>0"),
            "feedback": scalar("SELECT COUNT(*) FROM asset WHERE feedback IS NOT NULL"),
            "latest_feedback_at": scalar("SELECT MAX(feedback_at) FROM asset"),
            "latest_last_played_numeric": scalar("SELECT MAX(CAST(last_played AS REAL)) FROM asset"),
            "activity_events": scalar("SELECT COUNT(*) FROM activity_event") if has_events else None,
            "recent_play_rows": [
                {"id": row[0], "play_count": row[1], "last_played": row[2], "name": row[3]}
                for row in connection.execute(
                    """SELECT id,play_count,last_played,name FROM asset
                       WHERE CAST(last_played AS REAL)>0
                       ORDER BY CAST(last_played AS REAL) DESC LIMIT 10"""
                )
            ],
        }
    finally:
        connection.close()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
