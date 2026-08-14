import sqlite3
import shutil
import tempfile
import unittest
from pathlib import Path

from peach.migrations import plan, upgrade


MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "ledger.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_database_upgrades_and_is_idempotent(self):
        sqlite3.connect(self.db).close()
        backup = self.root / "before.db"
        done = upgrade(self.db, MIGRATIONS, backup)
        self.assertEqual([m.version for m in done], ["0000", "0001", "0002", "0003"])
        self.assertTrue(backup.exists())
        con = sqlite3.connect(self.db)
        tables = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_schema WHERE type='table'"
        )}
        versions = [row[0] for row in con.execute(
            "SELECT version FROM schema_migration ORDER BY version"
        )]
        con.close()
        self.assertTrue({"asset", "profile", "media_binding", "activity_event",
                         "provider_profile", "entity", "entity_alias",
                         "entity_external_ref", "asset_entity", "entity_link",
                         "entity_search_term", "watch_queue", "schema_migration"} <= tables)
        self.assertEqual(versions, ["0000", "0001", "0002", "0003"])
        self.assertEqual(upgrade(self.db, MIGRATIONS), [])
        self.assertEqual(plan(self.db, MIGRATIONS)[1], [])

    def test_old_schema_columns_are_reconciled(self):
        con = sqlite3.connect(self.db)
        con.executescript("""
          CREATE TABLE asset(
            id INTEGER PRIMARY KEY,
            location TEXT NOT NULL, path TEXT NOT NULL, name TEXT, medium TEXT,
            size INTEGER, mtime TEXT, hash_kind TEXT, hash TEXT,
            creator TEXT, series TEXT, code TEXT,
            duration REAL, width INTEGER, height INTEGER, vcodec TEXT, fps REAL,
            has_audio INTEGER, ctx_length TEXT, ctx_orient TEXT, ctx_quality TEXT,
            ctx_pace TEXT, ctx_people TEXT, play_count INTEGER DEFAULT 0,
            last_played TEXT, rating INTEGER, o_count INTEGER, watch_ratio REAL,
            source_id INTEGER, stash_scene_id INTEGER, snapshot_path TEXT,
            first_seen TEXT, last_seen TEXT, UNIQUE(location,path));
          CREATE TABLE asset_tag(asset_id INTEGER,tag TEXT,confidence REAL,source TEXT,
                                 UNIQUE(asset_id,tag));
        """)
        con.close()
        upgrade(self.db, MIGRATIONS)
        con = sqlite3.connect(self.db)
        columns = {row[1] for row in con.execute("PRAGMA table_info(asset)")}
        con.close()
        self.assertTrue({"studio", "feedback", "disposal", "leave_ratio", "play_seconds",
                         "feedback_at", "seek_count", "max_reached"} <= columns)

    def test_checksum_change_is_rejected(self):
        sqlite3.connect(self.db).close()
        upgrade(self.db, MIGRATIONS)
        con = sqlite3.connect(self.db)
        con.execute("UPDATE schema_migration SET checksum='changed' WHERE version='0001'")
        con.commit()
        con.close()
        with self.assertRaises(RuntimeError):
            plan(self.db, MIGRATIONS)

    def test_entity_migration_backfills_flattened_relations(self):
        base_migrations = self.root / "base-migrations"
        base_migrations.mkdir()
        for name in ("0000_legacy_schema.sql", "0001_core_boundaries.sql"):
            shutil.copyfile(MIGRATIONS / name, base_migrations / name)
        sqlite3.connect(self.db).close()
        upgrade(self.db, base_migrations)
        con = sqlite3.connect(self.db)
        con.executescript("""
          INSERT INTO asset(id,location,path,name,medium,creator,studio,series)
          VALUES(1,'local','one.mp4','one.mp4','video','Owner A','Studio A','Series A');
          INSERT INTO asset_tag(asset_id,tag,confidence,source)
          VALUES(1,'演员:Performer A',1.0,'stash:performer'),
                (1,'Tag A',0.9,'stash:tag');
        """)
        con.close()
        upgrade(self.db, MIGRATIONS)
        con = sqlite3.connect(self.db)
        entities = set(con.execute("SELECT kind,canonical_name FROM entity"))
        relations = set(con.execute(
            "SELECT e.kind,ae.role,ae.source FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=1"
        ))
        con.close()
        self.assertTrue({('performer','Performer A'),('tag','Tag A'),
                         ('studio','Studio A'),('creator','Owner A'),
                         ('series','Series A')} <= entities)
        self.assertTrue({('performer','performer','stash:performer'),
                         ('tag','tag','stash:tag'),('studio','studio','legacy:asset'),
                         ('creator','creator','legacy:asset'),
                         ('series','series','legacy:asset')} <= relations)


if __name__ == "__main__":
    unittest.main()
