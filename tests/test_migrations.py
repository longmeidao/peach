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
        self.assertEqual([m.version for m in done],
                         ["0000", "0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010", "0011"])
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
                         "entity_search_term", "watch_queue", "asset_preference", "asset_quality_goal",
                         "asset_tag_preference", "asset_search",
                         "schema_migration"} <= tables)
        self.assertEqual(versions, ["0000", "0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010", "0011"])
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

    def test_late_legacy_tags_are_backfilled_by_0005(self):
        base_migrations = self.root / "base-migrations"
        base_migrations.mkdir()
        for name in (
            "0000_legacy_schema.sql", "0001_core_boundaries.sql",
            "0002_canonical_entities.sql", "0003_entity_pages_and_watch_queue.sql",
            "0004_asset_search_fts.sql",
        ):
            shutil.copyfile(MIGRATIONS / name, base_migrations / name)
        sqlite3.connect(self.db).close()
        upgrade(self.db, base_migrations)
        con = sqlite3.connect(self.db)
        con.executescript("""
          INSERT INTO asset(id,location,path,name,medium)
          VALUES(1,'local','late.mp4','late.mp4','video');
          INSERT INTO asset_tag(asset_id,tag,confidence,source)
          VALUES(1,'足交',0.6,'vision_creator'),
                (1,'演员:Late Performer',1.0,'stash:performer');
        """)
        con.close()
        upgrade(self.db, MIGRATIONS)
        con = sqlite3.connect(self.db)
        relations = set(con.execute(
            "SELECT e.kind,e.canonical_name,ae.role,ae.source,ae.confidence "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=1"
        ))
        search_entities = con.execute(
            "SELECT entities FROM asset_search WHERE asset_id=1"
        ).fetchone()[0]
        con.close()
        self.assertIn(('tag', '足交', 'tag', 'vision_creator', 0.6), relations)
        self.assertIn(('performer', 'Late Performer', 'performer',
                       'stash:performer', 1.0), relations)
        self.assertIn('足交', search_entities)
        self.assertIn('Late Performer', search_entities)

    def test_structural_creator_cleanup_keeps_real_creator(self):
        base_migrations = self.root / "base-migrations"
        base_migrations.mkdir()
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if not path.name.startswith(("0007_", "0009_")):
                shutil.copyfile(path, base_migrations / path.name)
        sqlite3.connect(self.db).close()
        upgrade(self.db, base_migrations)
        connection = sqlite3.connect(self.db)
        connection.executescript("""
          INSERT INTO asset(id,location,path,name,medium,creator)
          VALUES(1,'115','B:/xxr/门槛/one.mp4','one.mp4','video','门槛');
          INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)
          VALUES(101,'creator','门槛','门槛','now','now'),
                (102,'creator','Actual Creator','actual creator','now','now');
          INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)
          VALUES(1,101,'creator','legacy:asset',0.8),
                (1,102,'creator','reviewed',1.0);
        """)
        connection.close()
        upgrade(self.db, MIGRATIONS)
        connection = sqlite3.connect(self.db)
        self.assertEqual(connection.execute(
            "SELECT creator FROM asset WHERE id=1"
        ).fetchone()[0], "Actual Creator")
        self.assertEqual(connection.execute(
            "SELECT e.canonical_name FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE ae.asset_id=1 AND e.kind='creator'"
        ).fetchall(), [("Actual Creator",)])
        connection.close()

    def test_asce_cleanup_removes_only_false_creator_board_assertions(self):
        base_migrations = self.root / "base-migrations"
        base_migrations.mkdir()
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if not path.name.startswith("0009_"):
                shutil.copyfile(path, base_migrations / path.name)
        sqlite3.connect(self.db).close()
        upgrade(self.db, base_migrations)
        connection = sqlite3.connect(self.db)
        connection.executescript("""
          INSERT INTO asset(id,location,path,name,medium,creator)
          VALUES(1,'115','B:/kkg/asce/one.mp4','one.mp4','video','asce');
          INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)
          VALUES(101,'creator','asce','asce','now','now'),
                (102,'tag','制服','制服','now','now'),
                (103,'tag','原创','原创','now','now');
          INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)
          VALUES(1,101,'creator','legacy:asset',0.8),
                (1,102,'tag','vision_creator',0.6),
                (1,103,'tag','name',0.9);
          INSERT INTO asset_tag(asset_id,tag,confidence,source)
          VALUES(1,'制服',0.6,'vision_creator'),(1,'原创',0.9,'name');
        """)
        connection.close()
        upgrade(self.db, MIGRATIONS)
        connection = sqlite3.connect(self.db)
        self.assertIsNone(connection.execute(
            "SELECT creator FROM asset WHERE id=1"
        ).fetchone()[0])
        self.assertEqual(connection.execute(
            "SELECT tag,source FROM asset_tag WHERE asset_id=1"
        ).fetchall(), [("原创", "name")])
        self.assertEqual(connection.execute(
            "SELECT e.canonical_name,ae.source FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=1"
        ).fetchall(), [("原创", "name")])
        connection.close()

    def test_folder_attribution_corrections_are_narrow_and_evidence_backed(self):
        base_migrations = self.root / "base-migrations"
        base_migrations.mkdir()
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if not path.name.startswith("0010_"):
                shutil.copyfile(path, base_migrations / path.name)
        sqlite3.connect(self.db).close()
        upgrade(self.db, base_migrations)
        connection = sqlite3.connect(self.db)
        connection.executescript("""
          INSERT INTO asset(id,location,path,name,medium,creator)
          VALUES(1,'115','B:\\云下载\\足交仙人\\feet of Suzyq (1).mp4','one.mp4','video','足交仙人'),
                (2,'115','B:\\MVP\\捅主任\\TokyoDolls\\32.mp4','32.mp4','video','捅主任'),
                (3,'115','B:\\创作者\\捅主任\\real.mp4','real.mp4','video','捅主任');
          INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)
          VALUES(101,'creator','足交仙人','足交仙人','now','now'),
                (102,'creator','捅主任','捅主任','now','now');
          INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)
          VALUES(1,101,'creator','legacy:asset',0.8),
                (2,102,'creator','legacy:asset',0.8),
                (3,102,'creator','legacy:asset',0.8);
        """)
        connection.close()
        upgrade(self.db, MIGRATIONS)
        connection = sqlite3.connect(self.db)
        self.assertEqual(connection.execute(
            "SELECT id,creator FROM asset ORDER BY id"
        ).fetchall(), [(1, "suzuq"), (2, None), (3, "捅主任")])
        relations = connection.execute(
            "SELECT ae.asset_id,e.canonical_name,ae.source,ae.confidence "
            "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
            "WHERE e.kind='creator' ORDER BY ae.asset_id"
        ).fetchall()
        self.assertEqual(relations, [(1, "suzuq", "user:watermark", 1.0),
                                     (3, "捅主任", "legacy:asset", 0.8)])
        self.assertEqual(connection.execute(
            "SELECT alias,source,confidence FROM entity_alias "
            "WHERE entity_id=(SELECT id FROM entity WHERE normalized_name='suzuq')"
        ).fetchall(), [("Suzyq", "filename", 0.95)])
        connection.close()

    def test_fts_tracks_asset_entity_alias_and_search_term_changes(self):
        sqlite3.connect(self.db).close()
        upgrade(self.db, MIGRATIONS)
        connection = sqlite3.connect(self.db)
        connection.executescript("""
          INSERT INTO asset(id,location,path,name,medium,code)
          VALUES(1,'local','one.mp4','Prestige sample.mp4','video','ABW-001');
          INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)
          VALUES(1001,'performer','高桥千凛','高桥千凛','now','now');
          INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)
          VALUES(1,1001,'performer','test',1.0);
          INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)
          VALUES(1001,'Takachi Chisato','takachi chisato','test',1.0);
          INSERT INTO entity_search_term(entity_id,term,purpose,source,created_at)
          VALUES(1001,'private release keyword','source_lookup','test','now');
        """)
        for query in ('"Prestige"', '"高桥千"', '"Takachi"', '"release keyword"'):
            self.assertEqual(connection.execute(
                "SELECT asset_id FROM asset_search WHERE asset_search MATCH ?", (query,)
            ).fetchall(), [(1,)])
        connection.execute("UPDATE asset SET name='Renamed title.mp4' WHERE id=1")
        self.assertEqual(connection.execute(
            "SELECT asset_id FROM asset_search WHERE asset_search MATCH ?", ('"Renamed"',)
        ).fetchall(), [(1,)])
        self.assertEqual(connection.execute(
            "SELECT asset_id FROM asset_search WHERE asset_search MATCH ?", ('"Prestige"',)
        ).fetchall(), [])
        connection.close()


if __name__ == "__main__":
    unittest.main()
