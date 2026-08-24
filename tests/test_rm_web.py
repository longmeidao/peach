import csv
import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
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
  hash TEXT,
  creator TEXT,
  studio TEXT,
  series TEXT,
  code TEXT,
  release_date TEXT,
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

    def test_canonical_creator_beats_same_named_legacy_performer_tag(self):
        """1065 类数据不能被旧 `演员:` 投影改成艺人。"""
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO asset_tag(asset_id,tag,source) "
            "VALUES(2,'演员:Canonical Creator','performer')"
        )
        con.commit(); con.close()

        item = rm_web.q_item(self.contract, 2)
        self.assertEqual(item["creator"], "Canonical Creator")
        self.assertEqual(item["entities"]["creator"], ["Canonical Creator"])
        self.assertEqual(item["entity_refs"]["creator"], [
            {"id": 12, "name": "Canonical Creator"},
        ])
        self.assertEqual(item["performers"], [])
        self.assertEqual(item["entity_refs"]["performer"], [])

    def test_reviewed_creator_tags_are_included_in_tag_coverage(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            "INSERT INTO asset_tag(asset_id,tag,source) VALUES(2,'审核标签','vision_creator_review')"
        )
        con.commit(); con.close()
        stats = rm_web.q_stats(self.contract)
        self.assertEqual(stats["tag_cov"], 2)
        self.assertIn("审核标签", {row["k"] for row in stats["top_tags"]})

    def test_stats_use_the_platform_system_volume_and_keep_the_old_alias(self):
        usage = type("Usage", (), {"free": 20, "total": 100})
        with mock.patch.object(rm_web, "system_volume", return_value=Path("X:/")), mock.patch(
            "shutil.disk_usage", return_value=usage,
        ):
            stats = rm_web.q_stats(self.contract)
        self.assertEqual(stats["system_disk"], {"root": "X:\\", "free": 20, "total": 100})
        self.assertIs(stats["disk_c"], stats["system_disk"])

    def test_items_support_duration_range(self):
        result = rm_web.q_items(
            self.contract, {"dur_min": "90", "dur_max": "110", "limit": "10"},
        )
        self.assertEqual([item["id"] for item in result["items"]], [1])

    def test_facets_are_scoped_to_the_current_entity_or_item(self):
        creator = rm_web.q_facets(
            self.contract, scope_kind="creator", scope_name="Canonical Creator",
        )
        self.assertEqual({row["k"] for row in creator["locations"]}, {"local", "115"})
        self.assertEqual({row["k"] for row in creator["orientations"]}, {"横屏", "竖屏"})
        self.assertEqual(creator["stats"]["duration"], 2)

        item = rm_web.q_facets(self.contract, asset_id=1)
        self.assertEqual(item["locations"], [{"k": "local", "n": 1, "played": 0}])
        self.assertEqual(item["orientations"], [{"k": "横屏", "n": 1}])
        self.assertEqual([row["k"] for row in item["creators"]], ["Canonical Creator"])
        self.assertEqual([row["k"] for row in item["tags"]], ["足交"])
        self.assertEqual(item["stats"]["duration"], 1)

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

    def test_every_technical_tag_uses_the_same_facets_classification(self):
        connection = sqlite3.connect(self.db_path)
        for entity_id, tag in enumerate(("2K", "有码", "无码"), start=201):
            connection.execute(
                "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(?, 'tag', ?, ?)",
                (entity_id, tag, tag.lower()),
            )
            connection.execute(
                "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                "VALUES(1,?,'tag','test',1.0)",
                (entity_id,),
            )
        connection.commit()
        connection.close()

        facets = rm_web.q_facets(self.contract)
        tech = {row["k"] for row in facets["tech"]}
        content = {row["k"] for row in facets["tags"]}
        self.assertTrue({"2K", "有码", "无码"} <= tech)
        self.assertTrue({"2K", "有码", "无码"}.isdisjoint(content))

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

    def test_contract_handler_registries_are_complete_and_unknown_routes_fail(self):
        self.assertEqual(set(rm_web.GET_HANDLERS), {
            "/api/items", "/api/item", "/api/entity", "/api/index", "/api/duplicates",
            "/api/stats", "/api/tops", "/api/ads", "/api/related", "/api/facets",
            "/api/search-history", "/api/review",
        })
        self.assertEqual(set(rm_web.POST_HANDLERS), {
            "/api/activity", "/api/play", "/api/feedback", "/api/watch-later",
            "/api/preference", "/api/quality-goal", "/api/item-tag", "/api/batch",
            "/api/search-history", "/api/trash/empty", "/api/review/decision",
        })
        with self.assertRaises(rm_web.ContractRouteNotFound):
            rm_web.dispatch_api_get(self.contract, "/api/typo", {})

    def test_write_transaction_rolls_back_and_closes_on_failure(self):
        opened = []
        real_db = self.contract.db

        def capture(write=False):
            connection = real_db(write)
            opened.append(connection)
            return connection

        with mock.patch.object(self.contract, "db", side_effect=capture):
            with self.assertRaisesRegex(RuntimeError, "abort"):
                with self.contract.write_transaction() as connection:
                    connection.execute("UPDATE asset SET name='changed' WHERE id=1")
                    raise RuntimeError("abort")

        self.assertEqual(self.row(1)["name"], "one.mp4")
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute("SELECT 1")

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

    def test_failed_database_commit_restores_quarantined_media(self):
        path = self.stage_media(1, "commit-failure.mp4")
        rm_web.w_feedback(self.contract, {"id": 1, "kind": "dispose"})

        @contextmanager
        def fail_after_body():
            connection = self.contract.db(write=True)
            try:
                yield connection
                connection.rollback()
                raise sqlite3.OperationalError("simulated commit failure")
            finally:
                connection.close()

        with mock.patch.object(self.contract, "write_transaction", fail_after_body):
            with self.assertRaisesRegex(sqlite3.OperationalError, "commit failure"):
                rm_web.w_batch(self.contract, {"ids": [1], "operation": "delete"})

        self.assertTrue(path.is_file(), "数据库失败后媒体必须恢复原名")
        self.assertEqual(self.row(1)["disposal"], "trash")
        self.assertEqual(list(path.parent.glob(".*.peach-purge-*.tmp")), [])

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

    def _add_performers(self, asset_id, names, start_id=200):
        con = sqlite3.connect(self.db_path)
        for offset, name in enumerate(names):
            entity_id = start_id + offset
            con.execute(
                "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
                "VALUES(?,'performer',?,?)", (entity_id, name, name.casefold()))
            con.execute(
                "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                "VALUES(?,?,'performer','test',1.0)", (asset_id, entity_id))
        con.commit()
        con.close()

    def test_co_starred_work_carries_every_performer_not_just_the_first(self):
        self._add_performers(1, ["Canonical Bea", "Canonical Cleo"])
        item = rm_web.q_items(self.contract, {"limit": "10"})["items"]
        row = next(row for row in item if row["id"] == 1)
        self.assertEqual(row["performers"],
                         ["Canonical Alice", "Canonical Bea", "Canonical Cleo"])
        self.assertEqual([ref["name"] for ref in row["performer_entities"]],
                         ["Canonical Alice", "Canonical Bea", "Canonical Cleo"])
        self.assertEqual(row["performer_total"], 3)
        # 出镜者名不得再作为内容标签重复出现在同一张卡片上。
        self.assertNotIn("Canonical Bea", row["tags"])

    def test_card_performers_are_capped_but_the_total_is_still_reported(self):
        extra = [f"Cast {index:02d}" for index in range(rm_web.CARD_PERFORMERS + 3)]
        self._add_performers(2, extra)
        row = next(row for row in rm_web.q_items(self.contract, {"limit": "10"})["items"]
                   if row["id"] == 2)
        self.assertEqual(len(row["performer_entities"]), rm_web.CARD_PERFORMERS)
        self.assertEqual(row["performer_total"], len(extra))

    def test_detail_returns_the_full_cast_without_the_card_cap(self):
        extra = [f"Cast {index:02d}" for index in range(rm_web.CARD_PERFORMERS + 3)]
        self._add_performers(1, extra)
        detail = rm_web.q_item(self.contract, 1)
        self.assertEqual(len(detail["entity_refs"]["performer"]), len(extra) + 1)
        self.assertEqual(len(detail["performers"]), len(extra) + 1)

    def test_related_cards_report_the_same_performer_shape_as_the_home_grid(self):
        self._add_performers(2, ["Canonical Bea"])
        related = rm_web.q_related(self.contract, 1, 10)
        row = related["items"][0]
        self.assertEqual(row["performer_total"], len(row["performer_entities"]))

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
  duration REAL,creator TEXT,studio TEXT,series TEXT,code TEXT,release_date TEXT,
  snapshot_path TEXT,disposal TEXT);
CREATE TABLE asset_tag(asset_id INTEGER,tag TEXT,confidence REAL DEFAULT 1.0,source TEXT,
  PRIMARY KEY(asset_id,tag,source));
CREATE TABLE entity(id INTEGER PRIMARY KEY,kind TEXT,canonical_name TEXT,normalized_name TEXT,
  metadata_json TEXT DEFAULT '{}',created_at TEXT,updated_at TEXT,UNIQUE(kind,normalized_name));
CREATE TABLE entity_alias(entity_id INTEGER,alias TEXT,normalized_alias TEXT,source TEXT,
  confidence REAL DEFAULT 1.0);
CREATE TABLE asset_entity(asset_id INTEGER,entity_id INTEGER,role TEXT,source TEXT,
  confidence REAL,metadata_json TEXT,first_seen_at TEXT,last_seen_at TEXT,
  UNIQUE(asset_id,entity_id,role,source));
CREATE TABLE entity_external_ref(entity_id INTEGER,provider TEXT,external_kind TEXT,external_id TEXT,
  metadata_json TEXT DEFAULT '{}',last_synced_at TEXT,
  PRIMARY KEY(provider,external_kind,external_id),UNIQUE(entity_id,provider,external_kind));
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

    def write_metadata_candidates(self, rows):
        path = self.candidates / "metadata-field-candidates-20260822.csv"
        fields = ["item_key", "code", "query", "field", "field_label", "current_value",
                  "candidates_json", "source_count", "status", "size_gb", "videos", "fetched_at"]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        return path

    def test_metadata_field_approval_uses_selected_candidate_and_never_writes_creator(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001',creator='Folder Creator' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:performers:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "value": [{"name": "木村さん", "external_id": "7", "thumb_url": ""}],
            "display_value": "木村さん", "warnings": [], "raw_snapshot": "/evidence.json",
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:performers", "code": "ABC-001", "query": "ABC-001",
            "field": "performers", "field_label": "演员", "current_value": "",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        queue = rm_web.q_review(self.contract)["sections"]["metadata_fields"]
        self.assertEqual(queue[0]["candidates"][0]["display_value"], "木村さん")
        result = rm_web.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:performers",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT creator FROM asset WHERE id=1").fetchone()[0], "Folder Creator")
        self.assertEqual(con.execute(
            "SELECT e.kind,e.canonical_name,ae.role FROM asset_entity ae "
            "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=1 AND ae.role='performer'"
        ).fetchall(), [("performer", "木村さん", "performer")])
        self.assertEqual(con.execute(
            "SELECT tag FROM asset_tag WHERE asset_id=1 AND source='javinizer:r18dev:performer'"
        ).fetchall(), [("演员:木村さん",)])
        self.assertEqual(con.execute(
            "SELECT provider,external_id FROM entity_external_ref"
        ).fetchall(), [("r18dev", "7")])
        note = con.execute(
            "SELECT note FROM review_decision WHERE category='metadata_fields'"
        ).fetchone()[0]
        con.close()
        self.assertEqual(json.loads(note)["candidate_key"], candidate["candidate_key"])

    def test_metadata_release_date_approval_writes_the_date_field(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "ABC-001:release_date:r18dev:abc", "source": "r18dev",
            "source_url": "https://r18.dev/example", "confidence": 0.9,
            "value": "2020-09-13", "display_value": "2020-09-13", "warnings": [],
            "raw_snapshot": "/evidence.json",
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:release_date", "code": "ABC-001", "query": "ABC-001",
            "field": "release_date", "field_label": "发行日期", "current_value": "",
            "candidates_json": json.dumps([candidate]), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        result = rm_web.w_review_decision(self.contract, {
            "category": "metadata_fields", "item_key": "ABC-001:release_date",
            "candidate_key": candidate["candidate_key"], "status": "approved",
        })
        self.assertEqual(result["applied_assets"], 1)
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT release_date FROM asset WHERE id=1").fetchone()[0], "2020-09-13")
        con.close()

    def test_metadata_approval_rejects_repeated_name_even_if_csv_is_tampered(self):
        con = sqlite3.connect(self.db_path)
        con.execute("UPDATE asset SET code='ABC-001' WHERE id=1")
        con.commit(); con.close()
        candidate = {
            "candidate_key": "bad", "source": "r18dev", "confidence": 0.9,
            "value": [{"name": "木村さん 木村さん", "external_id": "7"}],
        }
        self.write_metadata_candidates([{
            "item_key": "ABC-001:performers", "code": "ABC-001", "query": "ABC-001",
            "field": "performers", "field_label": "演员", "current_value": "",
            "candidates_json": json.dumps([candidate], ensure_ascii=False), "source_count": "1",
            "status": "candidate", "size_gb": "1", "videos": "1", "fetched_at": "now",
        }])
        with self.assertRaises(ValueError):
            rm_web.w_review_decision(self.contract, {
                "category": "metadata_fields", "item_key": "ABC-001:performers",
                "candidate_key": "bad", "status": "approved",
            })
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute(
            "SELECT count(*) FROM review_decision WHERE category='metadata_fields'"
        ).fetchone()[0], 0)
        con.close()

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

    def test_skip_candidate_cannot_be_approved(self):
        """机械批次明确跳过的聚合目录不能从复核页误批准回真相层。"""
        self.write_candidates("creator-tags-candidate-20260817.csv",
                              [{"board": "b1", "creator": "ukiru", "tags": "足系", "status": "skip"}])
        with self.assertRaises(ValueError):
            rm_web.w_review_decision(self.contract, {
                "category": "creator_tags", "item_key": "b1", "status": "approved",
            })
        con = sqlite3.connect(self.db_path)
        self.assertEqual(con.execute("SELECT count(*) FROM asset_tag").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM review_decision").fetchone()[0], 0)
        con.close()

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

    def _csv(self, name, fields, rows):
        path = self.candidates / name
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        return path

    def test_settled_western_identity_rows_stay_out_of_the_queue(self):
        # 168 条里 143 条是「确认无档案」，站上确实没有这个人，没有可判断的东西。
        fields = ["entity_id", "creator", "videos", "verdict", "matched_variant",
                  "babepedia_name", "token_overlap", "portrait_url", "profile_url"]
        self._csv("babepedia-candidates.csv", fields, [
            {"entity_id": "1", "creator": "ruth_lee", "videos": "336", "verdict": "命中",
             "matched_variant": "ruth_lee", "babepedia_name": "Ruth Lee",
             "token_overlap": "1.0", "portrait_url": "https://x/p.jpg", "profile_url": ""},
            {"entity_id": "2", "creator": "minhie", "videos": "17", "verdict": "需人工确认",
             "matched_variant": "minhie", "babepedia_name": "Aryminh",
             "token_overlap": "0.0", "portrait_url": "", "profile_url": ""},
            {"entity_id": "3", "creator": "luckydog22", "videos": "496",
             "verdict": "确认无档案", "matched_variant": "", "babepedia_name": "",
             "token_overlap": "0.0", "portrait_url": "", "profile_url": ""},
        ])
        rows = rm_web.q_review(self.contract)["sections"]["western_identity"]
        self.assertEqual({r["creator"] for r in rows}, {"ruth_lee", "minhie"})

    def test_western_identity_rows_carry_a_readable_evidence_line(self):
        fields = ["entity_id", "creator", "videos", "verdict", "matched_variant",
                  "babepedia_name", "token_overlap", "portrait_url"]
        self._csv("babepedia-candidates.csv", fields, [
            {"entity_id": "1", "creator": "SexySaffron", "videos": "357", "verdict": "命中",
             "matched_variant": "Sexy Saffron", "babepedia_name": "Saffron Bacchus",
             "token_overlap": "0.33", "portrait_url": "https://x/s.jpg"}])
        row = rm_web.q_review(self.contract)["sections"]["western_identity"][0]
        self.assertIn("Saffron Bacchus", row["reason"])
        self.assertIn("写法 Sexy Saffron", row["reason"], "别名跳转必须写明用了哪个写法")
        self.assertEqual(row["preview_url"], "https://x/s.jpg")

    def test_cover_sources_only_surface_gaps_and_low_resolution(self):
        fields = ["code", "result", "source", "width", "height", "kb", "url", "note"]
        self._csv("cover-fetch-log.csv", fields, [
            {"code": "BAZX-302", "result": "取得", "source": "awsimgsrc.dmm.co.jp",
             "width": "2184", "height": "1459", "kb": "1065", "url": "u", "note": ""},
            {"code": "PPT-018", "result": "取得", "source": "pics.dmm.co.jp",
             "width": "800", "height": "539", "kb": "165", "url": "u", "note": ""},
            {"code": "HEYZO-1380", "result": "未取得", "source": "", "width": "",
             "height": "", "kb": "", "url": "", "note": "所有渠道都没有候选"},
        ])
        rows = rm_web.q_review(self.contract)["sections"]["cover_sources"]
        self.assertEqual({r["code"] for r in rows}, {"PPT-018", "HEYZO-1380"},
                         "2184 宽的高清图不需要人确认")

    def test_stored_cover_previews_from_disk_not_the_origin(self):
        fields = ["code", "result", "source", "width", "height", "kb", "url", "note"]
        self._csv("cover-fetch-log.csv", fields, [
            {"code": "PPT-018", "result": "取得", "source": "pics.dmm.co.jp",
             "width": "800", "height": "539", "kb": "165", "url": "https://far/away.jpg",
             "note": ""}])
        row = rm_web.q_review(self.contract)["sections"]["cover_sources"][0]
        self.assertEqual(row["preview_url"], "/cover?code=PPT-018")

    FC2_FIELDS = ["code", "video_id", "result", "title", "release_date", "duration",
                  "censored", "writer", "writer_slug", "tags", "performers",
                  "performer_votes", "is_collection", "collection_parts",
                  "equivalents", "cover_url", "note"]

    def _fc2_row(self, code, **over):
        row = {field: "" for field in self.FC2_FIELDS}
        row.update({"code": code, "video_id": code.split("-")[-1], "result": "取得"})
        row.update(over)
        return row

    def test_fc2_markings_only_surface_rows_that_carry_a_marking(self):
        """FC2 大多数作品页评论区是空的，全列出来会淹掉真正有标记的那几十条。"""
        self._csv("fc2-candidate-log.csv", self.FC2_FIELDS, [
            self._fc2_row("FC2-PPV-2355314", performers="真夏",
                          performer_votes="真夏:2"),
            self._fc2_row("FC2-PPV-3701252", equivalents="2407240"),
            self._fc2_row("FC2-PPV-3788093"),
            self._fc2_row("FC2-PPV-4078398", result="未取得", note="连接失败"),
        ])
        rows = rm_web.q_review(self.contract)["sections"]["fc2_markings"]
        self.assertEqual({r["code"] for r in rows},
                         {"FC2-PPV-2355314", "FC2-PPV-3701252"})

    def test_fc2_evidence_line_shows_how_many_comments_agree(self):
        self._csv("fc2-candidate-log.csv", self.FC2_FIELDS, [
            self._fc2_row("FC2-PPV-2355314", performers="真夏",
                          performer_votes="真夏:2", writer="陸王24")])
        row = rm_web.q_review(self.contract)["sections"]["fc2_markings"][0]
        self.assertIn("真夏:2", row["reason"], "票数是这批候选唯一的置信度信号")
        self.assertIn("陸王24", row["reason"])

    def test_a_collection_says_its_cover_is_withheld(self):
        """合集封面套给每个分片会让 21 段不同内容显示同一张图。"""
        self._csv("fc2-candidate-log.csv", self.FC2_FIELDS, [
            self._fc2_row("FC2PPV-3312576", is_collection="1",
                          collection_parts="19", cover_url="")])
        row = rm_web.q_review(self.contract)["sections"]["fc2_markings"][0]
        self.assertIn("19 个分片", row["reason"])
        self.assertIn("封面不下发", row["reason"])

    def test_code_creator_candidates_reach_the_review_page(self):
        fields = ["entity_id", "creator", "verdict", "identity", "assets",
                  "sample_path", "code_action", "reason"]
        self._csv("code-creator-review.csv", fields, [
            {"entity_id": "6869", "creator": "banbi_555", "verdict": "存疑",
             "identity": "BANBI-555", "assets": "69", "sample_path": "A:/x.mp4",
             "code_action": "", "reason": "名字像番号，但目录内没有同番号文件"}])
        rows = rm_web.q_review(self.contract)["sections"]["code_creators"]
        self.assertEqual(rows[0]["item_key"], "6869")
        self.assertIn("没有同番号文件", rows[0]["reason"])




class ChineseSearchTermTests(unittest.TestCase):
    """短查询必须能通过别名和检索词命中日文汉字身份。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
        con = sqlite3.connect(self.db_path)
        con.executescript(BASE_SCHEMA)
        con.execute(
            "INSERT INTO asset(id,location,path,name,medium,duration,first_seen) "
            "VALUES(1,'local',?,'ABW-232.mp4','video',100,'2026-08-18')",
            (r"R:\Media\ABW-232.mp4",))
        con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) "
            "VALUES(11,'performer','涼森れむ','涼森れむ')")
        con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(1,11,'performer','test',1.0)")
        con.commit(); con.close()
        self.contract = rm_web.WebContract(Path(self.db_path))

    def found(self, query):
        return [row["id"] for row in
                rm_web.q_items(self.contract, {"q": query, "limit": "10"})["items"]]

    def _add_term(self, term):
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity_search_term(entity_id,term,purpose,source) "
                    "VALUES(11,?,'search','hanzi-simplified')", (term,))
        con.commit(); con.close()

    def test_simplified_query_misses_before_a_term_exists(self):
        self.assertEqual(self.found("凉森"), [])

    def test_simplified_query_hits_through_the_search_term(self):
        # 「凉森」只有两字，trigram 用不上，永远走 LIKE 分支。
        self._add_term("凉森れむ")
        self.assertEqual(self.found("凉森"), [1])

    def test_original_japanese_spelling_still_works(self):
        self._add_term("凉森れむ")
        self.assertEqual(self.found("涼森"), [1])

    def test_alias_is_matched_by_short_queries_too(self):
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
                    " VALUES(11,'Remu Suzumori','remu suzumori','r18',1.0)")
        con.commit(); con.close()
        self.assertEqual(self.found("Suzumori"), [1])

    def test_unrelated_query_still_finds_nothing(self):
        self._add_term("凉森れむ")
        self.assertEqual(self.found("凉宫"), [])


class JavModeAndCoverTests(unittest.TestCase):
    """JAV 模式的边界与封面查找。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.covers = root / "covers"
        self.covers.mkdir()
        self.db_path = str(root / "ledger.db")
        con = sqlite3.connect(self.db_path)
        con.executescript(BASE_SCHEMA)
        # 前四条是真番号的四种形态，后三条是 `code` 里实际混着的非番号值。
        con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,code,duration,first_seen) "
            "VALUES(?,'local',?,?,'video',?,100,'2026-08-18')",
            [(1, r"R:\a.mp4", "a.mp4", "ABW-232"),
             (2, r"R:\b.mp4", "b.mp4", "259LUXU-1468"),
             (3, r"R:\c.mp4", "c.mp4", "FC2-PPV-1234567"),
             (4, r"R:\d.mp4", "d.mp4", "040221-001"),
             (5, r"R:\e.mp4", "e.mp4", "RAIKUN325"),
             (6, r"R:\f.mp4", "f.mp4", "HHD800"),
             (7, r"R:\g.mp4", "g.mp4", None)],
        )
        con.commit(); con.close()
        self.contract = rm_web.WebContract(Path(self.db_path), cover_root=self.covers)

    def ids(self, args):
        return sorted(row["id"] for row in
                      rm_web.q_items(self.contract, {**args, "limit": "20"})["items"])

    def test_jav_mode_keeps_only_real_code_shapes(self):
        self.assertEqual(self.ids({"jav": "1"}), [1, 2, 3, 4])

    def test_uploader_handles_in_the_code_column_are_excluded(self):
        # `RAIKUN325` 是 myfans 账号名、`HHD800` 是站点水印，都不是番号。
        self.assertNotIn(5, self.ids({"jav": "1"}))
        self.assertNotIn(6, self.ids({"jav": "1"}))

    def test_without_the_flag_nothing_is_filtered(self):
        self.assertEqual(self.ids({}), [1, 2, 3, 4, 5, 6, 7])

    def test_shape_predicate_matches_the_documented_forms(self):
        for good in ("ABW-232", "259LUXU-1468", "FC2-PPV-1234567", "040221-001"):
            self.assertTrue(rm_web.is_jav_code(good), good)
        for bad in ("RAIKUN325", "HHD800", "WX17", "BANBI_555", "", None):
            self.assertFalse(rm_web.is_jav_code(bad), repr(bad))

    def test_cover_key_normalises_the_same_way_as_the_fetcher(self):
        self.assertEqual(rm_web.normalise_code_key("abw232"), "ABW-232")
        self.assertEqual(rm_web.normalise_code_key("ABW-0232"), "ABW-232")
        self.assertEqual(rm_web.normalise_code_key("278gyan17"), "278GYAN-017")

    def test_cards_report_whether_a_cover_is_on_disk(self):
        (self.covers / "ABW-232.jpg").write_bytes(b"x")
        rows = {row["id"]: row for row in
                rm_web.q_items(self.contract, {"jav": "1", "limit": "20"})["items"]}
        self.assertTrue(rows[1]["has_cover"])
        self.assertFalse(rows[2]["has_cover"])

    def test_missing_cover_resolves_to_none_not_a_broken_path(self):
        self.assertIsNone(self.contract.cover_path("ABW-232"))
        self.assertIsNone(self.contract.cover_path(None))

    def test_cover_frame_reads_the_face_sidecar(self):
        (self.covers / "ABW-232.jpg").write_bytes(b"x")
        (self.covers / "ABW-232.face.json").write_text(
            '{"ratio":1.49,"face":{"cx":0.82,"cy":0.19}}', encoding="utf-8")
        self.assertEqual(self.contract.cover_frame("ABW-232"), {"cy": 0.19})

    def test_a_cover_without_a_sidecar_falls_back_silently(self):
        (self.covers / "ABW-232.jpg").write_bytes(b"x")
        self.assertIsNone(self.contract.cover_frame("ABW-232"))

    def test_a_sidecar_reporting_no_face_is_not_a_frame(self):
        # 检出率约 48%，没检出是常态而不是错误——必须安静回落。
        (self.covers / "ABW-232.jpg").write_bytes(b"x")
        (self.covers / "ABW-232.face.json").write_text(
            '{"ratio":1.49,"face":null}', encoding="utf-8")
        self.assertIsNone(self.contract.cover_frame("ABW-232"))

    def test_a_corrupt_sidecar_never_breaks_the_card(self):
        (self.covers / "ABW-232.jpg").write_bytes(b"x")
        (self.covers / "ABW-232.face.json").write_text("{not json", encoding="utf-8")
        self.assertIsNone(self.contract.cover_frame("ABW-232"))




class FaceFocusMathTests(unittest.TestCase):
    """人脸中心 → 圆框 object-position 的换算。"""

    def test_a_portrait_centers_the_face_vertically(self):
        # 640x960（ratio 2/3）、脸心在 cy=0.45：窗口应从余量的 35% 处开始。
        self.assertEqual(rm_web.face_focus(0.667, 0.5, 0.45),
                         {"axis": "y", "pct": 35})

    def test_the_centered_face_keeps_the_default_position(self):
        self.assertEqual(rm_web.face_focus(2 / 3, 0.5, 0.5),
                         {"axis": "y", "pct": 50})

    def test_faces_too_close_to_an_edge_clamp_instead_of_overflowing(self):
        self.assertEqual(rm_web.face_focus(0.667, 0.5, 0.0),
                         {"axis": "y", "pct": 0})
        self.assertEqual(rm_web.face_focus(0.667, 0.5, 1.0),
                         {"axis": "y", "pct": 100})

    def test_a_landscape_image_takes_its_margin_horizontally(self):
        # 1500x1000、脸心在 cx=0.6：窗口应从余量的 80% 处开始。
        self.assertEqual(rm_web.face_focus(1.5, 0.6, 0.4),
                         {"axis": "x", "pct": 80})
        # 脸太靠右时夹取到边缘，不越界。
        self.assertEqual(rm_web.face_focus(1.5, 0.9, 0.4),
                         {"axis": "x", "pct": 100})

    def test_near_square_images_have_no_margin_to_reframe(self):
        self.assertIsNone(rm_web.face_focus(1.0, 0.5, 0.3))
        self.assertIsNone(rm_web.face_focus(1.03, 0.5, 0.3))

    def test_unreadable_numbers_return_none_not_an_exception(self):
        self.assertIsNone(rm_web.face_focus(None, 0.5, 0.3))
        self.assertIsNone(rm_web.face_focus("x", 0.5, 0.3))
        self.assertIsNone(rm_web.face_focus(-1, 0.5, 0.3))


class AvatarFocusTests(unittest.TestCase):
    """资料页实体图的人脸取景 sidecar。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.avatars = root / "avatars"
        self.avatars.mkdir()
        self.contract = rm_web.WebContract(
            Path(str(root / "ledger.db")), avatar_root=self.avatars)

    def test_the_sidecar_focus_is_passed_through(self):
        (self.avatars / "performer-7900.img").write_bytes(b"x")
        (self.avatars / "performer-7900.face.json").write_text(
            '{"ratio":0.667,"face":{"cx":0.5,"cy":0.45},'
            '"focus":{"axis":"y","pct":35}}', encoding="utf-8")
        self.assertEqual(self.contract.avatar_focus("performer", 7900),
                         {"axis": "y", "pct": 35})

    def test_no_sidecar_falls_back_silently(self):
        (self.avatars / "performer-7900.img").write_bytes(b"x")
        self.assertIsNone(self.contract.avatar_focus("performer", 7900))

    def test_a_sidecar_without_a_detection_is_not_a_focus(self):
        # Haar 对侧脸、低头会漏检，没检出是常态而不是错误——必须安静回落。
        (self.avatars / "performer-7900.img").write_bytes(b"x")
        (self.avatars / "performer-7900.face.json").write_text(
            '{"ratio":0.667,"face":null}', encoding="utf-8")
        self.assertIsNone(self.contract.avatar_focus("performer", 7900))

    def test_a_corrupt_sidecar_never_breaks_the_page(self):
        (self.avatars / "performer-7900.img").write_bytes(b"x")
        (self.avatars / "performer-7900.face.json").write_text(
            "{not json", encoding="utf-8")
        self.assertIsNone(self.contract.avatar_focus("performer", 7900))

    def test_a_malformed_focus_is_rejected(self):
        (self.avatars / "performer-7900.face.json").write_text(
            '{"focus":{"axis":"z","pct":50}}', encoding="utf-8")
        (self.avatars / "studio-12.face.json").write_text(
            '{"focus":{"axis":"y","pct":"high"}}', encoding="utf-8")
        (self.avatars / "creator-13.face.json").write_text(
            '{"focus":{"axis":"x","pct":-20}}', encoding="utf-8")
        (self.avatars / "series-14.face.json").write_text(
            '{"focus":{"axis":"y","pct":true}}', encoding="utf-8")
        self.assertIsNone(self.contract.avatar_focus("performer", 7900))
        self.assertIsNone(self.contract.avatar_focus("studio", 12))
        self.assertIsNone(self.contract.avatar_focus("creator", 13))
        self.assertIsNone(self.contract.avatar_focus("series", 14))


class DuplicateDetectionTests(unittest.TestCase):
    """同番号不等于重复：合集、分卷和混入的广告都会共用一个 code。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
        self.con = sqlite3.connect(self.db_path)
        # 后进先出：这条要在临时目录清理之后注册，才会先关连接。Windows 上没关
        # 的 SQLite 句柄会让 TemporaryDirectory 删不掉文件。
        self.addCleanup(self.con.close)
        self.con.executescript(BASE_SCHEMA)
        self.next_id = 1
        self.contract = rm_web.WebContract(Path(self.db_path))

    def add(self, code, duration, size, drive="B", name=None, hash_=None):
        asset_id = self.next_id
        self.next_id += 1
        self.con.execute(
            "INSERT INTO asset(id,location,path,name,medium,code,size,duration,"
            "hash,first_seen) VALUES(?,'local',?,?,'video',?,?,?,?,'2026-08-19')",
            # 默认名不能以数字结尾：`ABW-232-1.mp4` 会被正确识别成分卷标记，
            # 于是每个夹具文件都成了「不同部分」。用 ripN 避开这个约定。
            (asset_id, rf"{drive}:\{asset_id}.mp4", name or f"{code} rip{asset_id}.mp4",
             code, size, duration, hash_))
        self.con.commit()
        return asset_id

    def groups(self):
        return rm_web.q_duplicates(self.contract, {"limit": "50"})

    def test_same_duration_rips_are_a_duplicate_cluster(self):
        self.add("ABW-232", 7200, 5_000_000_000)
        self.add("ABW-232", 7200, 3_000_000_000)
        result = self.groups()
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["groups"][0]["count"], 2)

    def test_multi_part_releases_never_collapse_into_one_cluster(self):
        # PPT-018 实测：109.2/175.2/196.4 分各两份。按番号只留最大会删掉两个部分。
        for minutes in (109.2, 175.2, 196.4):
            self.add("PPT-018", minutes * 60, int(minutes * 5e7))
            self.add("PPT-018", minutes * 60, int(minutes * 4e7))
        result = self.groups()
        self.assertEqual(result["total"], 3, "三个部分必须各成一簇")
        self.assertTrue(all(g["count"] == 2 for g in result["groups"]))

    def test_a_collection_is_not_a_pile_of_duplicates(self):
        # FC2-PPV-3312576 一个番号 19 个文件，是 19 部不同作品。
        for index in range(6):
            self.add("FC2-PPV-3312576", 3000 + index * 600, 1_000_000_000)
        self.assertEqual(self.groups()["total"], 0)

    def test_advertisements_sharing_the_code_do_not_touch_the_real_work(self):
        real = self.add("BAZX-302", 11994, 9_000_000_000)
        self.add("BAZX-302", 78, 20_000_000, name="妹妹直播.mp4")
        self.add("BAZX-302", 80, 21_000_000, name="N房间的精彩直播.mp4")
        result = self.groups()
        flagged = {f["id"] for g in result["groups"] for f in g["files"]}
        self.assertNotIn(real, flagged, "199 分钟的正片不该被判成重复")

    def test_largest_and_longest_are_marked_separately(self):
        # 时长差必须落在容差内才是同一簇；体积最大与时长最长可以是不同文件，
        # 实测 MEYD-692 里最长的那个反而是码率更低的 nyap2p 版本。
        big = self.add("MEYD-692", 7000, 9_000_000_000)
        long_ = self.add("MEYD-692", 7020, 8_000_000_000)
        files = {f["id"]: f for f in self.groups()["groups"][0]["files"]}
        self.assertTrue(files[big]["is_largest"])
        self.assertFalse(files[big]["is_longest"])
        self.assertTrue(files[long_]["is_longest"])

    def test_identical_needs_a_hash_on_every_file(self):
        self.add("DASD-839", 7200, 5_000_000_000, hash_="abc")
        self.add("DASD-839", 7200, 5_000_000_000, hash_="abc")
        self.assertTrue(self.groups()["groups"][0]["identical"])

    def test_a_missing_hash_downgrades_the_claim_to_inference(self):
        self.add("DASD-839", 7200, 5_000_000_000, hash_="abc")
        self.add("DASD-839", 7200, 5_000_000_000, hash_=None)
        self.assertFalse(self.groups()["groups"][0]["identical"])

    def test_cross_drive_duplicates_are_flagged(self):
        self.add("SSIS-057", 7200, 5_000_000_000, drive="A")
        self.add("SSIS-057", 7200, 4_000_000_000, drive="B")
        group = self.groups()["groups"][0]
        self.assertTrue(group["cross_drive"])
        self.assertEqual(group["drives"], ["A:", "B:"])

    def test_reclaimable_keeps_the_largest_of_each_cluster(self):
        self.add("WAAA-415", 7200, 5_000_000_000)
        self.add("WAAA-415", 7200, 3_000_000_000)
        self.assertEqual(self.groups()["reclaimable"], 3_000_000_000)

    def test_unknown_duration_is_never_merged_into_a_cluster(self):
        self.add("HMN-145", 0, 5_000_000_000)
        self.add("HMN-145", 0, 5_000_000_000)
        self.assertEqual(self.groups()["total"], 0, "没有时长证据就不判重复")

    def test_recycle_bin_items_are_excluded(self):
        first = self.add("TRE-080", 7200, 5_000_000_000)
        self.add("TRE-080", 7200, 4_000_000_000)
        self.con.execute("UPDATE asset SET disposal='trash' WHERE id=?", (first,))
        self.con.commit()
        self.assertEqual(self.groups()["total"], 0)

    def test_long_films_do_not_merge_across_a_percentage_tolerance(self):
        # HRV-041 实测：237 分与 239 分是两个部分。3% 容差在 4 小时片子上等于
        # ±7 分钟，会把它们并成一簇，「留最大」就删掉了一个部分。
        self.add("HRV-041", 237 * 60, 10_000_000_000, name="HRV-041-1.mp4")
        self.add("HRV-041", 239 * 60, 10_100_000_000, name="HRV-041-2.mp4")
        self.add("HRV-041", 237 * 60, 4_400_000_000, name="HD_hrv-041-1.mp4")
        self.add("HRV-041", 239 * 60, 4_460_000_000, name="HD_hrv-041-2.mp4")
        result = self.groups()
        self.assertEqual(result["total"], 2, "两个部分必须各成一簇")
        for group in result["groups"]:
            durations = {round(f["duration"]) for f in group["files"]}
            self.assertEqual(len(durations), 1, "同簇内时长必须一致")

    def test_distinct_part_markers_never_share_a_cluster(self):
        # FCDSS-021 的 -1/-2/-3 时长只差 12 秒，却是三个部分。
        self.add("FCDSS-021", 14496, 10_140_000_000, name="FCDSS-021-1.mp4")
        self.add("FCDSS-021", 14500, 10_140_000_000, name="FCDSS-021-2.mp4")
        self.add("FCDSS-021", 14508, 10_130_000_000, name="FCDSS-021-3.mp4")
        self.assertEqual(self.groups()["total"], 0, "分卷标记不同不算重复")

    def test_unmarked_rips_of_the_same_part_still_cluster(self):
        # 没有分卷标记的同时长文件仍应判为重复：站点前缀不是分卷标记。
        self.add("MEYD-692", 9192, 6_580_000_000, name="hhd800.com@MEYD-692.mp4")
        self.add("MEYD-692", 9192, 6_570_000_000, name="MEYD-692.mp4")
        self.add("MEYD-692", 9192, 6_570_000_000, name="meyd-692.mp4")
        self.assertEqual(self.groups()["groups"][0]["count"], 3)

    def test_part_marker_extraction(self):
        self.assertEqual(rm_web.part_marker("HRV-041-1.mp4"), "1")
        self.assertEqual(rm_web.part_marker("HD_hrv-041-2.mp4"), "2")
        self.assertEqual(rm_web.part_marker("MEYD-692.mp4"), "")
        self.assertEqual(rm_web.part_marker("hhd800.com@MEYD-692.mp4"), "")


class TopsRotationTests(unittest.TestCase):
    """顶部三层要跟着「换一批」真的换人，否则刷新后上面纹丝不动。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
        con = sqlite3.connect(self.db_path)
        self.addCleanup(con.close)
        con.executescript(BASE_SCHEMA)
        # 候选池要大于展示位，抽样才有意义（TOPS_POOL_FACTOR 倍）。
        for index in range(40):
            con.execute("INSERT INTO entity(id,kind,canonical_name,normalized_name) "
                        "VALUES(?,'performer',?,?)",
                        (100 + index, f"P{index:02d}", f"p{index:02d}"))
            for copy in range(40 - index):          # 让数量各不相同，排序稳定
                asset_id = index * 100 + copy
                con.execute("INSERT INTO asset(id,location,path,name,medium,first_seen) "
                            "VALUES(?,'local',?,?,'video','2026-08-19')",
                            (asset_id, f"/x/{asset_id}.mp4", f"{asset_id}.mp4"))
                con.execute("INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
                            "VALUES(?,?,'performer','test',1.0)", (asset_id, 100 + index))
        con.commit()
        self.contract = rm_web.WebContract(Path(self.db_path))

    def names(self, **kwargs):
        return [row["k"] for row in rm_web.q_tops(self.contract, 8, **kwargs)["performers"]]

    def test_without_a_seed_it_stays_the_strict_top_list(self):
        self.assertEqual(self.names(), self.names())
        self.assertEqual(self.names()[0], "P00", "无种子时仍按数量取前 N")

    def test_a_seed_changes_who_appears(self):
        self.assertNotEqual(self.names(seed="111"), self.names(seed="222"))

    def test_the_same_seed_is_repeatable(self):
        # 翻页和重绘之间不能抖动，否则同一批里会看到两套人。
        self.assertEqual(self.names(seed="111"), self.names(seed="111"))

    def test_a_seeded_batch_is_still_full_and_ordered_by_count(self):
        rows = rm_web.q_tops(self.contract, 8, seed="111")["performers"]
        self.assertEqual(len(rows), 8)
        counts = [row["n"] for row in rows]
        self.assertEqual(counts, sorted(counts, reverse=True), "抽完仍按数量排序")

    def test_a_small_pool_degrades_to_everything_available(self):
        rows = rm_web.q_tops(self.contract, 100, seed="111")["performers"]
        self.assertEqual(len(rows), 40, "候选不足时不能抽空，也不能报错")


if __name__ == "__main__":
    unittest.main()
