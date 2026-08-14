"""Merge only reviewed, unambiguous studio duplicates.

Dry-run is the default. ``--apply`` requires a fresh SQLite backup path.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from peach.config import DATABASE_PATH
from peach.migrations import sqlite_backup


MERGES = {
    "Prestige": (
        "プレステージ",
        "プレステージプレミアム(PRESTIGEPREMIUM)",
    ),
    "ABC / Mousouzoku": ("ABC _ Mousouzoku",),
    "Asia / Mousouzoku": ("Asia _ Mousouzoku",),
    "D*Collection": ("D_Collection",),
    "Deep's": ("Deep's\n",),
    "Fetish Box / Mousouzoku": ("Fetish Box _ Mousouzoku",),
    "Fresh Gordon/Daydream Tribe": ("Fresh Gordon_Daydream Tribe",),
    "Kahanshin Tigers /Fetika": ("Kahanshin Tigers _Fetika",),
    "Kahanshin Tigers /Mousouzoku": ("Kahanshin Tigers _Mousouzoku",),
    "kira*kira": ("kira_kira",),
    "Teacher / Mousouzoku": ("Teacher _ Mousouzoku",),
    "Yuriecchi/Daydreamers": ("Yuriecchi_Daydreamers",),
}

EXTRA_ALIASES = {"Prestige": ("Prestige Premium", "PRESTIGEPREMIUM")}


def _entity(connection: sqlite3.Connection, name: str):
    return connection.execute(
        "SELECT id,canonical_name FROM entity WHERE kind='studio' AND canonical_name=?",
        (name,),
    ).fetchone()


def preview(connection: sqlite3.Connection) -> list[dict]:
    result = []
    for target_name, source_names in MERGES.items():
        target = _entity(connection, target_name)
        if not target:
            continue
        for source_name in source_names:
            source = _entity(connection, source_name)
            if not source:
                continue
            assets = connection.execute(
                "SELECT count(DISTINCT asset_id) FROM asset_entity WHERE entity_id=?",
                (source[0],),
            ).fetchone()[0]
            result.append({"source": source_name, "target": target_name, "assets": assets})
    return result


def apply(connection: sqlite3.Connection) -> list[dict]:
    changes = preview(connection)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("BEGIN IMMEDIATE")
    try:
        for change in changes:
            target = _entity(connection, change["target"])
            source = _entity(connection, change["source"])
            target_id, source_id = target[0], source[0]
            conflict = connection.execute(
                "SELECT 1 FROM entity_external_ref s JOIN entity_external_ref t "
                "ON t.entity_id=? AND t.provider=s.provider AND t.external_kind=s.external_kind "
                "WHERE s.entity_id=? LIMIT 1", (target_id, source_id),
            ).fetchone()
            if conflict:
                raise RuntimeError(f"external ref conflict: {change['source']}")
            connection.execute(
                "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
                "VALUES(?,?,lower(trim(?)),'peach:canonicalization',1.0)",
                (target_id, change["source"], change["source"]),
            )
            connection.execute(
                "INSERT OR IGNORE INTO entity_alias "
                "SELECT ?,alias,normalized_alias,source,confidence FROM entity_alias WHERE entity_id=?",
                (target_id, source_id),
            )
            connection.execute(
                "INSERT OR IGNORE INTO asset_entity "
                "SELECT asset_id,?,role,source,confidence,metadata_json,first_seen_at,last_seen_at "
                "FROM asset_entity WHERE entity_id=?", (target_id, source_id),
            )
            connection.execute("DELETE FROM asset_entity WHERE entity_id=?", (source_id,))
            connection.execute(
                "UPDATE entity_external_ref SET entity_id=? WHERE entity_id=?", (target_id, source_id),
            )
            connection.execute(
                "INSERT OR IGNORE INTO entity_link(entity_id,link_kind,label,url,hostname,is_sensitive,"
                "metadata_json,created_at,updated_at) SELECT ?,link_kind,label,url,hostname,is_sensitive,"
                "metadata_json,created_at,updated_at FROM entity_link WHERE entity_id=?",
                (target_id, source_id),
            )
            connection.execute("DELETE FROM entity_link WHERE entity_id=?", (source_id,))
            connection.execute(
                "INSERT OR IGNORE INTO entity_search_term(entity_id,term,purpose,source,created_at) "
                "SELECT ?,term,purpose,source,created_at FROM entity_search_term WHERE entity_id=?",
                (target_id, source_id),
            )
            connection.execute("DELETE FROM entity_search_term WHERE entity_id=?", (source_id,))
            connection.execute(
                "UPDATE asset SET studio=? WHERE studio=?", (change["target"], change["source"]),
            )
            connection.execute("DELETE FROM entity WHERE id=?", (source_id,))
        for target_name, aliases in EXTRA_ALIASES.items():
            target = _entity(connection, target_name)
            if not target:
                continue
            for alias in aliases:
                connection.execute(
                    "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
                    "VALUES(?,?,lower(trim(?)),'peach:canonicalization',1.0)",
                    (target[0], alias, alias),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    connection = sqlite3.connect(args.db)
    try:
        changes = preview(connection)
        print({"mode": "apply" if args.apply else "dry-run", "merges": changes,
               "asset_relations": sum(item["assets"] for item in changes)})
        if not args.apply:
            return
        if not args.backup:
            raise SystemExit("--apply requires --backup")
        connection.close()
        sqlite_backup(args.db, args.backup)
        connection = sqlite3.connect(args.db)
        applied = apply(connection)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign = connection.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign:
            raise RuntimeError({"integrity": integrity, "foreign_key_errors": foreign})
        print({"applied": len(applied), "integrity": integrity, "foreign_key_errors": len(foreign),
               "backup": str(args.backup)})
    finally:
        connection.close()


if __name__ == "__main__":
    main()
