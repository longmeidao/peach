import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach import web_contract as rm_web


BASE_SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY,
  location TEXT NOT NULL,
  path TEXT NOT NULL,
  name TEXT,
  medium TEXT,
  size INTEGER,
  creator TEXT,
  studio TEXT,
  series TEXT,
  code TEXT,
  duration REAL,
  width INTEGER,
  height INTEGER,
  ctx_length TEXT,
  ctx_orient TEXT,
  ctx_quality TEXT,
  play_count INTEGER DEFAULT 0,
  last_played TEXT,
  rating INTEGER,
  o_count INTEGER,
  snapshot_path TEXT,
  first_seen TEXT,
  feedback TEXT,
  disposal TEXT,
  leave_ratio REAL,
  play_seconds REAL,
  feedback_at REAL,
  seek_count INTEGER,
  max_reached REAL,
  UNIQUE(location, path)
);
CREATE TABLE asset_tag(
  asset_id INTEGER,
  tag TEXT,
  confidence REAL DEFAULT 1.0,
  source TEXT,
  UNIQUE(asset_id, tag)
);
CREATE TABLE entity(
  id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT, normalized_name TEXT,
  metadata_json TEXT DEFAULT '{}', created_at TEXT, updated_at TEXT,
  UNIQUE(kind,normalized_name)
);
CREATE TABLE asset_entity(
  asset_id INTEGER, entity_id INTEGER, role TEXT, source TEXT, confidence REAL,
  metadata_json TEXT DEFAULT '{}', first_seen_at TEXT, last_seen_at TEXT,
  UNIQUE(asset_id,entity_id,role,source)
);
CREATE TABLE entity_alias(entity_id INTEGER,alias TEXT,normalized_alias TEXT,source TEXT,confidence REAL);
CREATE TABLE entity_external_ref(entity_id INTEGER,provider TEXT,external_kind TEXT,external_id TEXT,
  metadata_json TEXT DEFAULT '{}',last_synced_at TEXT);
CREATE TABLE entity_link(id INTEGER PRIMARY KEY,entity_id INTEGER,link_kind TEXT,label TEXT,url TEXT,
  hostname TEXT,is_sensitive INTEGER DEFAULT 0,metadata_json TEXT DEFAULT '{}',created_at TEXT,updated_at TEXT);
CREATE TABLE entity_search_term(entity_id INTEGER,term TEXT,purpose TEXT,source TEXT,created_at TEXT);
CREATE TABLE watch_queue(profile_id TEXT,asset_id INTEGER,added_at TEXT,source TEXT,
  PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_preference(profile_id TEXT,asset_id INTEGER,liked INTEGER,reason TEXT,
  source TEXT,updated_at TEXT,PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_tag_preference(profile_id TEXT,asset_id INTEGER,normalized_tag TEXT,
  hidden INTEGER,updated_at TEXT,PRIMARY KEY(profile_id,asset_id,normalized_tag));
"""


class WebDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
        con = sqlite3.connect(self.db_path)
        con.executescript(BASE_SCHEMA)
        con.executemany(
            """INSERT INTO asset(
                 id,location,path,name,medium,size,creator,studio,code,duration,
                 width,height,ctx_length,ctx_orient,ctx_quality,first_seen)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                (1, "local", r"R:\\Media\\one.mp4", "one.mp4", "video", 100,
                 "Alice", "Studio A", "ABC-001", 100, 1920, 1080, "速食", "横屏", "2K", "2026-08-14"),
                (2, "115", r"B:\\two.mp4", "two.mp4", "video", 200,
                 "Bob", None, None, 200, 1080, 1920, "速食", "竖屏", "1080P", "2026-08-13"),
                (3, "local", r"R:\\Media\\cover.jpg", "cover.jpg", "image", 10,
                 "Alice", None, None, None, None, None, None, None, None, "2026-08-12"),
            ],
        )
        con.executemany(
            "INSERT INTO asset_tag(asset_id,tag,source) VALUES(?,?,?)",
            [(1, "足交", "name"), (1, "演员:Alice", "performer"), (2, "竖屏", "probe")],
        )
        con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(?,?,?,?)",
            [(10, "tag", "足交", "足交"),
             (11, "performer", "Canonical Alice", "canonical alice"),
             (12, "creator", "Canonical Creator", "canonical creator"),
             (13, "studio", "Canonical Studio", "canonical studio")],
        )
        con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(?,?,?,?,?)",
            [(1, 10, "tag", "test", 1.0),
             (1, 11, "performer", "test", 1.0),
             (1, 12, "creator", "test", 1.0),
             (2, 12, "creator", "test", 1.0),
             (1, 13, "studio", "test", 1.0),
             (2, 13, "studio", "test", 1.0)],
        )
        con.commit()
        con.close()
        self.contract = rm_web.WebContract(Path(self.db_path))

    def tearDown(self):
        self.tmp.cleanup()

    def row(self, aid=1):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM asset WHERE id=?", (aid,)).fetchone()
        con.close()
        return row

    def test_default_database_connection_is_readonly(self):
        con = self.contract.db()
        with self.assertRaises(sqlite3.OperationalError):
            con.execute("UPDATE asset SET name='must-not-write' WHERE id=1")
        con.close()

    def test_items_are_filtered_and_do_not_expose_paths(self):
        result = rm_web.q_items(
            self.contract, {"loc": "local", "sort": "new", "limit": "10"},
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], 1)
        self.assertEqual(result["items"][0]["performers"], ["Canonical Alice"])
        self.assertEqual(result["items"][0]["performer_entities"], [
            {"id": 11, "name": "Canonical Alice"},
        ])
        self.assertNotIn("path", result["items"][0])
        self.assertNotIn("snapshot_path", result["items"][0])

    def test_items_support_duration_range(self):
        result = rm_web.q_items(
            self.contract, {"dur_min": "90", "dur_max": "110", "limit": "10"},
        )
        self.assertEqual([item["id"] for item in result["items"]], [1])

    def test_legacy_length_tags_are_hidden_in_favor_of_numeric_minutes(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(14,'tag','短片-2分内','短片-2分内')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,14,'tag','test',1.0)"
        )
        con.commit(); con.close()
        self.assertNotIn("短片-2分内", [tag["k"] for tag in rm_web.q_item(self.contract, 1)["tags"]])
        facets = rm_web.q_facets(self.contract)
        visible = {row["k"] for row in facets["tags"] + facets["tech"]}
        self.assertNotIn("短片-2分内", visible)

    def test_activity_accumulates_real_play_time_and_max_position(self):
        first = rm_web.w_activity(self.contract, {
            "id": 1, "position": 50, "duration": 100, "delta": 12, "seeks": 2,
        })
        second = rm_web.w_activity(self.contract, {
            "id": 1, "position": 20, "duration": 100, "delta": 3, "seeks": 1,
        })
        self.assertEqual(first["max_reached"], 0.5)
        self.assertEqual(second["play_seconds"], 15)
        self.assertEqual(second["max_reached"], 0.5)
        self.assertEqual(second["seek_count"], 3)

    def test_feedback_and_disposal_toggle_independently(self):
        self.assertEqual(rm_web.w_feedback(
            self.contract, {"id": 1, "kind": "dislike"},
        )["feedback"], "dislike")
        self.assertEqual(rm_web.w_feedback(
            self.contract, {"id": 1, "kind": "dispose"},
        )["disposal"], "pending")
        self.assertEqual(self.row()["feedback"], "dislike")
        self.assertIsNone(rm_web.w_feedback(
            self.contract, {"id": 1, "kind": "dislike"},
        )["feedback"])
        self.assertEqual(self.row()["disposal"], "pending")

    def test_like_and_reason_are_independent_profile_preferences(self):
        saved = rm_web.w_preference(self.contract, {
            "id": 1, "liked": True, "reason": "喜欢自然的节奏和镜头",
        })
        self.assertTrue(saved["liked"])
        self.assertEqual(saved["like_reason"], "喜欢自然的节奏和镜头")
        item = rm_web.q_item(self.contract, 1)
        self.assertTrue(item["liked"])
        self.assertEqual(item["like_reason"], "喜欢自然的节奏和镜头")
        self.assertEqual(item["entity_refs"]["performer"], [
            {"id": 11, "name": "Canonical Alice"},
        ])
        self.assertIsNone(self.row()["feedback"])

        cleared = rm_web.w_preference(self.contract, {
            "id": 1, "liked": False, "reason": "",
        })
        self.assertFalse(cleared["liked"])
        self.assertEqual(cleared["like_reason"], "")

    def test_application_contract_instances_do_not_share_cache(self):
        other = rm_web.WebContract(Path(self.tmp.name) / "other.db")
        self.assertEqual(self.contract.cached("same", lambda: "first"), "first")
        self.assertEqual(other.cached("same", lambda: "second"), "second")

    def test_item_tag_add_and_remove_preserve_source_evidence(self):
        added = rm_web.w_item_tag(self.contract, {
            "id": 1, "operation": "add", "tag": "新标签",
        })
        self.assertIn("新标签", added["tags"])
        removed = rm_web.w_item_tag(self.contract, {
            "id": 1, "operation": "remove", "tag": "足交",
        })
        self.assertNotIn("足交", removed["tags"])
        con = sqlite3.connect(self.db_path)
        self.assertEqual(
            con.execute("SELECT source FROM asset_tag WHERE asset_id=1 AND tag='足交'").fetchone()[0],
            "name",
        )
        self.assertEqual(
            con.execute("SELECT hidden FROM asset_tag_preference WHERE asset_id=1").fetchone()[0],
            1,
        )
        con.close()

    def test_batch_markers_are_bounded_and_preserve_like_reason(self):
        rm_web.w_preference(self.contract, {"id": 1, "liked": False, "reason": "保留原文"})
        result = rm_web.w_batch(self.contract, {"ids": [1, 2, 2], "operation": "like"})
        self.assertEqual(result["changed"], 2)
        self.assertEqual(rm_web.q_item(self.contract, 1)["like_reason"], "保留原文")
        rm_web.w_batch(self.contract, {"ids": [1, 2], "operation": "dispose"})
        self.assertEqual(self.row(1)["disposal"], "pending")
        with self.assertRaises(ValueError):
            rm_web.w_batch(self.contract, {"ids": list(range(201)), "operation": "seen"})

    def test_top_lists_and_related_items_use_canonical_entities(self):
        tops = rm_web.q_tops(self.contract, 10)
        self.assertEqual(tops["performers"][0]["k"], "Canonical Alice")
        self.assertEqual(tops["performers"][0]["n"], 1)
        self.assertEqual(tops["studios"][0]["k"], "Canonical Studio")

        related = rm_web.q_related(self.contract, 1, 10)
        self.assertEqual(related["items"][0]["id"], 2)
        self.assertEqual(related["items"][0]["why"], "同创作者")
        self.assertEqual(related["items"][0]["performer_entities"], [])

        reverse_related = rm_web.q_related(self.contract, 2, 10)
        self.assertEqual(reverse_related["items"][0]["performer_entities"], [
            {"id": 11, "name": "Canonical Alice"},
        ])

    def test_creator_filters_indexes_and_stats_use_canonical_entities(self):
        by_creator = rm_web.q_items(self.contract, {
            "creator": "Canonical Creator", "limit": "10",
        })
        by_studio = rm_web.q_items(self.contract, {
            "studio": "Canonical Studio", "limit": "10",
        })
        search = rm_web.q_items(self.contract, {
            "q": "Canonical Creator", "limit": "10",
        })
        self.assertEqual(by_creator["total"], 2)
        self.assertEqual(by_studio["total"], 2)
        self.assertEqual(search["total"], 2)
        self.assertEqual(rm_web.q_items(
            self.contract, {"creator": "Alice", "limit": "10"},
        )["total"], 0)

        creators = rm_web.q_index(self.contract, "creators", limit=10)
        self.assertEqual(creators["items"][0]["k"], "Canonical Creator")
        self.assertEqual(creators["items"][0]["n"], 2)
        performers = rm_web.q_index(self.contract, "performers", limit=10)
        self.assertEqual(performers["items"][0]["k"], "Canonical Alice")
        self.assertEqual(performers["items"][0]["n"], 1)
        stats = rm_web.q_stats(self.contract)
        self.assertEqual(stats["attribution"]["creator"], 2)
        self.assertEqual(stats["attribution"]["studio"], 2)
        facets = rm_web.q_facets(self.contract)
        self.assertEqual(facets["creators"][0]["k"], "Canonical Creator")

    def test_performer_entity_page_and_watch_queue(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO entity_alias VALUES(11,'Alice','alice','test',1.0)"
        )
        con.execute(
            "INSERT INTO entity_link(entity_id,link_kind,label,url,hostname,is_sensitive) "
            "VALUES(11,'official','Official','https://example.com/alice','example.com',0),"
            "(11,'source_reference','Private source','https://source.invalid/a','source.invalid',1)"
        )
        con.execute(
            "INSERT INTO entity_search_term(entity_id,term,purpose,source) "
            "VALUES(11,'Alice code','source_lookup','user')"
        )
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(15,'performer','Related Bob','related bob')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,15,'performer','test',1.0)"
        )
        con.commit(); con.close()
        page = rm_web.q_entity(self.contract, {"kind": "performer", "name": "Alice"})
        self.assertEqual(page["canonical_name"], "Canonical Alice")
        self.assertEqual(page["asset_count"], 1)
        self.assertEqual(page["tags"], [{"id": 10, "k": "足交", "n": 1}])
        self.assertEqual(page["related_performers"][0]["k"], "Related Bob")
        self.assertEqual(page["related_performers"][0]["n"], 1)
        self.assertTrue(page["links"][0]["clickable"])
        self.assertFalse(page["links"][1]["clickable"])
        self.assertIsNone(page["links"][1]["url"])
        self.assertEqual(rm_web.q_items(
            self.contract, {"performer": "Canonical Alice", "limit": "10"},
        )["total"], 1)
        self.assertTrue(rm_web.w_watch_later(
            self.contract, {"id": 1},
        )["watch_later"])
        self.assertTrue(rm_web.q_item(self.contract, 1)["watch_later"])
        self.assertFalse(rm_web.w_watch_later(
            self.contract, {"id": 1},
        )["watch_later"])

if __name__ == "__main__":
    unittest.main()
