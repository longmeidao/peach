import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
CREATE TABLE asset_quality_goal(profile_id TEXT,asset_id INTEGER,wanted INTEGER,reason TEXT,
  updated_at TEXT,PRIMARY KEY(profile_id,asset_id));
CREATE TABLE asset_tag_preference(profile_id TEXT,asset_id INTEGER,normalized_tag TEXT,
  hidden INTEGER,updated_at TEXT,PRIMARY KEY(profile_id,asset_id,normalized_tag));
CREATE TABLE media_binding(asset_id INTEGER,backend TEXT,external_id TEXT,metadata_json TEXT,
  last_synced_at TEXT,PRIMARY KEY(asset_id,backend));
CREATE TABLE activity_event(id INTEGER PRIMARY KEY,asset_id INTEGER,kind TEXT,created_at TEXT);
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
            [(1, "足交", "name"), (1, "演员:Alice", "performer"),
             (1, "Canonical Alice", "vision"), (2, "竖屏", "probe")],
        )
        con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(?,?,?,?)",
            [(10, "tag", "足交", "足交"),
             (11, "performer", "Canonical Alice", "canonical alice"),
             (12, "creator", "Canonical Creator", "canonical creator"),
             (13, "studio", "Canonical Studio", "canonical studio"),
             (90, "tag", "Canonical Alice", "canonical alice")],
        )
        con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(?,?,?,?,?)",
            [(1, 10, "tag", "test", 1.0),
             (1, 11, "performer", "test", 1.0),
             (1, 12, "creator", "test", 1.0),
             (2, 12, "creator", "test", 1.0),
             (1, 13, "studio", "test", 1.0),
             (2, 13, "studio", "test", 1.0),
             (1, 90, "tag", "test", 1.0)],
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
        self.assertEqual(result["items"][0]["tags"], ["足交"])
        self.assertNotIn("Canonical Alice", [tag["k"] for tag in rm_web.q_item(self.contract, 1)["tags"]])
        self.assertNotIn("Canonical Alice", [tag["k"] for tag in rm_web.q_facets(self.contract)["tags"]])
        self.assertNotIn("Canonical Alice", [tag["k"] for tag in rm_web.q_index(self.contract, "tags")["items"]])
        self.assertNotIn("Canonical Alice", [tag["k"] for tag in rm_web.q_stats(self.contract)["top_tags"]])
        self.assertNotIn("path", result["items"][0])
        self.assertNotIn("snapshot_path", result["items"][0])

    def test_items_support_duration_range(self):
        result = rm_web.q_items(
            self.contract, {"dur_min": "90", "dur_max": "110", "limit": "10"},
        )
        self.assertEqual([item["id"] for item in result["items"]], [1])

    def test_items_can_skip_repeated_total_count_on_later_pages(self):
        result = rm_web.q_items(
            self.contract, {"limit": "1", "offset": "0", "count": "0"},
        )
        self.assertIsNone(result["total"])
        self.assertEqual(len(result["items"]), 1)
        self.assertTrue(result["has_more"])

    def test_legacy_length_tags_are_hidden_in_favor_of_numeric_minutes(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(14,'tag','短片-2分内','短片-2分内')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,14,'tag','test',1.0)"
        )
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(15,'tag','测试分页标签','测试分页标签')"
        )
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,15,'tag','test',1.0)"
        )
        con.commit(); con.close()
        self.assertNotIn("短片-2分内", [tag["k"] for tag in rm_web.q_item(self.contract, 1)["tags"]])
        facets = rm_web.q_facets(self.contract)
        visible = {row["k"] for row in facets["tags"] + facets["tech"]}
        self.assertNotIn("短片-2分内", visible)
        index = rm_web.q_index(self.contract, "tags")
        self.assertNotIn("短片-2分内", {row["k"] for row in index["items"]})
        self.assertIn("超长片-30分上", rm_web.LENGTH_TAGS)
        first_page = rm_web.q_index(self.contract, "tags", limit=1)
        second_page = rm_web.q_index(self.contract, "tags", limit=1, offset=1)
        self.assertTrue(first_page["has_more"])
        self.assertNotEqual(first_page["items"][0]["k"], second_page["items"][0]["k"])

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
        )["disposal"], "trash")
        self.assertEqual(self.row()["feedback"], "dislike")
        self.assertIsNone(rm_web.w_feedback(
            self.contract, {"id": 1, "kind": "dislike"},
        )["feedback"])
        self.assertEqual(self.row()["disposal"], "trash")

    def test_flagged_means_positive_marks_not_disposal_or_negative_feedback(self):
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dislike"})
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dispose"})
        rm_web.w_preference(self.contract, {"id": 2, "liked": True, "reason": ""})
        self.assertEqual(
            [item["id"] for item in rm_web.q_items(self.contract, {"state": "flagged", "limit": "10"})["items"]],
            [2],
        )
        self.assertEqual(rm_web.q_facets(self.contract)["stats"]["flagged"], 1)

        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET o_count=2 WHERE id=1")
        con.commit(); con.close()
        flagged = lambda: {item["id"] for item in rm_web.q_items(
            self.contract, {"state": "flagged", "limit": "10"})["items"]}
        # o_count 让 1 变成正向标记，但它还在回收站里，所以不该出现在任何普通列表。
        self.assertEqual(flagged(), {2})
        self.assertEqual(rm_web.q_facets(self.contract)["stats"]["flagged"], 1)

        # 还原后立刻重新计入：证明上面漏掉 1 的原因是回收站，而不是“已标记”的定义变了。
        rm_web.w_batch(self.contract, {"ids": [1], "operation": "restore"})
        self.assertEqual(flagged(), {1, 2})
        self.assertEqual(rm_web.q_facets(self.contract)["stats"]["flagged"], 2)

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

    def stage_media(self, aid, name="clip.mp4"):
        """把某条资产指向真实的临时文件，物理删除才有东西可删。"""
        path = Path(self.tmp.name) / name
        path.write_bytes(b"media")
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET path=?,snapshot_path=NULL WHERE id=?", (str(path), aid))
        con.commit(); con.close()
        return path

    def test_recycle_bin_delete_removes_the_media_and_every_ledger_reference(self):
        path = self.stage_media(1)
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dispose"})
        result = rm_web.w_batch(self.contract, {"ids": [1], "operation": "delete"})

        self.assertEqual((result["purged"], result["blocked"]), (1, []))
        self.assertFalse(path.exists(), "回收站的彻底删除必须真的删掉文件")
        self.assertIsNone(self.row(1), "账本行也要一起消失")
        con = sqlite3.connect(self.db_path)
        for table in rm_web.ASSET_REFERENCE_TABLES:
            left = con.execute(f"SELECT count(*) FROM {table} WHERE asset_id=1").fetchone()[0]
            self.assertEqual(left, 0, f"{table} 残留了已删资产的引用")
        con.close()

    def test_delete_and_restore_refuse_assets_outside_the_recycle_bin(self):
        """彻底删除只能作用于回收站，否则一次误选就能删掉在库作品。"""
        for operation in ("delete", "restore"):
            with self.assertRaises(ValueError):
                rm_web.w_batch(self.contract, {"ids": [1], "operation": operation})
        self.assertIsNotNone(self.row(1))

    def test_restore_returns_an_asset_to_normal_listings(self):
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dispose"})
        listed = {item["id"] for item in rm_web.q_items(self.contract, {"limit": "10"})["items"]}
        self.assertNotIn(1, listed, "回收站条目不该出现在普通列表")

        rm_web.w_batch(self.contract, {"ids": [1], "operation": "restore"})
        self.assertIsNone(self.row(1)["disposal"])
        listed = {item["id"] for item in rm_web.q_items(self.contract, {"limit": "10"})["items"]}
        self.assertIn(1, listed)

    def test_empty_trash_purges_only_the_bin(self):
        binned = self.stage_media(1, "binned.mp4")
        kept = self.stage_media(2, "kept.mp4")
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dispose"})

        result = rm_web.w_empty_trash(self.contract)

        self.assertEqual(result["purged"], 1)
        self.assertFalse(binned.exists())
        self.assertIsNone(self.row(1))
        self.assertTrue(kept.exists(), "不在回收站的媒体一个都不能碰")
        self.assertIsNotNone(self.row(2))

    def test_undeletable_media_keeps_its_row_in_the_bin_instead_of_orphaning_the_file(self):
        """文件删不掉时保留账本行：留一条能重试的回收站条目，好过留一个没人认领的文件。"""
        blocked_path = Path(self.tmp.name) / "locked"
        blocked_path.mkdir()          # 目录删不掉，等价于文件被占用/网盘离线
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET path=? WHERE id=1", (str(blocked_path),))
        con.commit(); con.close()
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dispose"})

        result = rm_web.w_empty_trash(self.contract)

        self.assertEqual(result["purged"], 0)
        self.assertEqual([item["id"] for item in result["blocked"]], [1])
        self.assertTrue(blocked_path.exists())
        self.assertEqual(self.row(1)["disposal"], "trash", "删不掉就该留在回收站里等重试")

    def test_batch_markers_are_bounded_and_preserve_like_reason(self):
        rm_web.w_preference(self.contract, {"id": 1, "liked": False, "reason": "保留原文"})
        result = rm_web.w_batch(self.contract, {"ids": [1, 2, 2], "operation": "like"})
        self.assertEqual(result["changed"], 2)
        self.assertEqual(rm_web.q_item(self.contract, 1)["like_reason"], "保留原文")

    def test_better_version_goal_is_independent_and_reversible(self):
        saved = rm_web.w_quality_goal(self.contract, {
            "id": 1, "wanted": True, "reason": "有水印，寻找高清无水印版",
        })
        self.assertTrue(saved["better_version"])
        item = rm_web.q_item(self.contract, 1)
        self.assertTrue(item["better_version"])
        self.assertEqual(item["better_version_reason"], "有水印，寻找高清无水印版")
        cleared = rm_web.w_quality_goal(self.contract, {"id": 1, "wanted": False})
        self.assertFalse(cleared["better_version"])
        self.assertFalse(rm_web.q_item(self.contract, 1)["better_version"])
        rm_web.w_batch(self.contract, {"ids": [1, 2], "operation": "dispose"})
        self.assertEqual(self.row(1)["disposal"], "trash")
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

REVIEW_SCHEMA = """
CREATE TABLE asset(id INTEGER PRIMARY KEY,location TEXT,path TEXT,name TEXT,medium TEXT,
  duration REAL,creator TEXT,snapshot_path TEXT,disposal TEXT);
CREATE TABLE asset_tag(asset_id INTEGER,tag TEXT,confidence REAL DEFAULT 1.0,source TEXT,
  PRIMARY KEY(asset_id,tag,source));
CREATE TABLE entity(id INTEGER PRIMARY KEY,kind TEXT,canonical_name TEXT,normalized_name TEXT,
  metadata_json TEXT DEFAULT '{}',created_at TEXT,updated_at TEXT,UNIQUE(kind,normalized_name));
CREATE TABLE entity_alias(entity_id INTEGER,alias TEXT,normalized_alias TEXT,source TEXT,
  confidence REAL DEFAULT 1.0);
CREATE TABLE asset_entity(asset_id INTEGER,entity_id INTEGER,role TEXT,source TEXT,
  confidence REAL,metadata_json TEXT,first_seen_at TEXT,last_seen_at TEXT,
  UNIQUE(asset_id,entity_id,role,source));
CREATE TABLE review_decision(category TEXT,item_key TEXT,status TEXT,reviewer TEXT DEFAULT 'local-default',
  note TEXT DEFAULT '',updated_at TEXT,PRIMARY KEY(category,item_key));
"""


class ReviewQueueTests(unittest.TestCase):
    """复核队列：候选来源、稳定主键、批准的权威值与写入边界。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.candidates = root / "generated"
        self.candidates.mkdir()
        self.db_path = str(root / "ledger.db")
        con = sqlite3.connect(self.db_path)
        con.executescript(REVIEW_SCHEMA)
        con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name) "
                    "VALUES(1,'creator','ukiru','ukiru')")
        for asset_id in (1, 2, 3):
            con.execute("INSERT INTO asset(id,location,path,name,medium,snapshot_path) "
                        "VALUES(?,'local',?,?,'video','s.jpg')",
                        (asset_id, f"/x/{asset_id}.mp4", f"{asset_id}.mp4"))
            con.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                        "VALUES(?,1,'creator','board',1.0)", (asset_id,))
        con.commit(); con.close()
        self.contract = rm_web.WebContract(Path(self.db_path), candidate_root=self.candidates)

    def tearDown(self):
        self.tmp.cleanup()

    def write_candidates(self, name, rows):
        path = self.candidates / name
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["board", "creator", "tags", "status"])
            writer.writeheader(); writer.writerows(rows)
        return path

    def test_latest_batch_is_used_instead_of_a_hardcoded_date(self):
        """候选文件名带批次日期；把日期写死在源码里会让下一批生成后页面静默变空。"""
        self.write_candidates("creator-tags-candidate-20260101.csv",
                              [{"board": "old", "creator": "ukiru", "tags": "旧", "status": "candidate"}])
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "new", "creator": "ukiru", "tags": "新", "status": "candidate"}])
        rows, source, _ = rm_web.read_candidates("creator_tags", self.candidates)
        self.assertEqual(source, "creator-tags-candidate-20260817.csv")
        self.assertEqual([row["item_key"] for row in rows], ["new"])

    def test_rows_without_a_stable_key_are_dropped_and_counted(self):
        """缺主键的行绝不能退化成行号：CSV 一重排，历史决定就挪到别的条目上了。"""
        self.write_candidates("creator-tags-candidate-20260817.csv", [
            {"board": "", "creator": "ukiru", "tags": "足系", "status": "candidate"},
            {"board": "ok", "creator": "ukiru", "tags": "足系", "status": "candidate"},
        ])
        rows, _, skipped = rm_web.read_candidates("creator_tags", self.candidates)
        self.assertEqual([row["item_key"] for row in rows], ["ok"])
        self.assertEqual(skipped, 1)

    def test_approval_takes_creator_and_tags_from_the_candidate_not_the_body(self):
        """否则「批准候选 X」能写入与 X 无关的标签，而留痕仍写着 X 通过。"""
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        with self.assertRaises(ValueError):
            rm_web.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "b1", "status": "approved",
                "creator": "别的创作者", "tags": "伪造标签",
            })
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM review_decision").fetchone()[0], 0)
        con.close()

    def test_approval_refuses_candidates_outside_the_current_batch(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        with self.assertRaises(ValueError):
            rm_web.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "已消失的候选", "status": "approved",
            })

    def test_unselected_approval_is_capped_instead_of_tagging_everything(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        with mock.patch.object(rm_web, "REVIEW_APPLY_LIMIT", 2):
            with self.assertRaises(ValueError) as caught:
                rm_web.w_review_decision(self.contract, {
                    "category": "creator_tags", "item_key": "b1", "status": "approved",
                })
        self.assertIn("显式勾选", str(caught.exception))
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 0)
        con.close()

    def test_approval_writes_both_projections_and_reports_the_real_count(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系|素人", "status": "candidate"}])
        result = rm_web.w_review_decision(self.contract, {
            "category": "creator_tags", "item_key": "b1", "status": "approved",
            "creator": "ukiru", "tags": "足系|素人",
        })
        self.assertEqual(result["applied_assets"], 3)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 6)
        self.assertEqual(con.execute(
            "SELECT count(*) FROM asset_entity WHERE role='tag'").fetchone()[0], 6)
        self.assertEqual(con.execute(
            "SELECT status FROM review_decision WHERE item_key='b1'").fetchone()[0], "approved")
        con.close()

    def test_selected_ids_must_belong_to_the_reviewed_creator(self):
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "candidate"}])
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO asset(id,location,path,name,medium) "
                    "VALUES(99,'local','/x/99.mp4','99.mp4','video')")
        con.commit(); con.close()
        with self.assertRaises(ValueError):
            rm_web.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "b1", "status": "approved",
                "selected_ids": [1, 99],
            })


if __name__ == "__main__":
    unittest.main()
