"""creator / performer 跨类重复身份审计与兼容投影回归。"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.migrations import upgrade
from scripts.merge_duplicate_identities import apply_rows, collect

ROOT = Path(__file__).resolve().parents[1]


class DuplicateIdentityMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        upgrade(self.db, ROOT / "migrations")
        self.con = sqlite3.connect(self.db)
        self.con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,creator) "
            "VALUES(?,'local',?,?,'video',?)",
            [(1, "/x/1.mp4", "1.mp4", "小千 Qian0791"),
             (2, "/x/2.mp4", "2.mp4", "小千 Qian0791"),
             (3, "/x/3.mp4", "3.mp4", "NOZOMI NOZOMI")])
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
            "VALUES(?,?,?,?, 't','t')",
            [(10, "creator", "小千 Qian0791", "小千 qian0791"),
             (11, "performer", "小千", "小千"),
             (12, "creator", "NOZOMI NOZOMI", "nozomi nozomi"),
             (13, "performer", "NOZOMI", "nozomi"),
             (14, "creator", "无关目录", "无关目录")])
        self.con.executemany(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
            "VALUES(?,?,?,?,1.0)",
            [(11, "Qian0791", "qian0791", "stash:performer"),
             (13, "NOZOMI NOZOMI", "nozomi nozomi", "javbus:performer")])
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(?,?,?,?,1.0)",
            [(1, 10, "creator", "legacy:asset"), (2, 10, "creator", "legacy:asset"),
             (1, 11, "performer", "performer"), (2, 11, "performer", "performer"),
             (3, 12, "creator", "legacy:asset"),
             (3, 13, "performer", "javbus:performer"),
             (1, 14, "creator", "legacy:asset"), (2, 14, "creator", "legacy:asset")])
        self.con.executemany(
            "INSERT INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,1.0,?)",
            [(1, "演员:小千", "performer"), (2, "演员:小千", "performer"),
             (3, "演员:NOZOMI NOZOMI", "javbus:performer")])
        self.con.commit()

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_collect_uses_same_assets_aliases_and_release_provenance(self):
        rows = collect(self.con)
        self.assertEqual(len(rows), 2)
        by_drop = {row["drop_name"]: row for row in rows}
        self.assertEqual(by_drop["小千"]["keep_kind"], "creator")
        self.assertIn("账号别名", by_drop["小千"]["match_evidence"])
        self.assertEqual(by_drop["NOZOMI NOZOMI"]["keep_kind"], "performer")
        self.assertEqual(by_drop["NOZOMI NOZOMI"]["evidence"], "发行元数据")
        self.assertNotIn("无关目录", {row["keep_name"] for row in rows})

    def test_apply_syncs_flat_creator_and_actor_tag_projections(self):
        counts = apply_rows(self.con, collect(self.con))
        self.con.commit()

        self.assertIsNone(self.con.execute(
            "SELECT 1 FROM entity WHERE id=11").fetchone())
        self.assertIsNone(self.con.execute(
            "SELECT 1 FROM entity WHERE id=12").fetchone())
        self.assertEqual(self.con.execute(
            "SELECT creator FROM asset WHERE id=3").fetchone()[0], None)
        tags = dict(self.con.execute(
            "SELECT asset_id,tag FROM asset_tag ORDER BY asset_id"))
        self.assertNotIn(1, tags)
        self.assertNotIn(2, tags)
        self.assertEqual(tags[3], "演员:NOZOMI")
        self.assertEqual(counts["actor_tags_removed"], 2)
        self.assertEqual(counts["actor_tags_rewritten"], 1)
        self.assertEqual(self.con.execute(
            "PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
