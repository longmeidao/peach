"""creator / performer 跨类重复身份审计与兼容投影回归。"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.migrations import upgrade
from scripts.merge_duplicate_identities import (
    apply_repeated_projections,
    apply_rows,
    collect,
    collect_repeated_projections,
)

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
             (3, "/x/3.mp4", "3.mp4", "NOZOMI NOZOMI"),
             (4, "/x/4.mp4", "4.mp4", "NOZOMI NOZOMI")])
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
             (4, 13, "performer", "javbus:performer"),
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
        self.assertEqual(self.con.execute(
            "SELECT creator FROM asset WHERE id=4").fetchone()[0], None,
            "兼容字段要按坏名字全量清，不能只清旧 creator 关系覆盖的资产")
        tags = dict(self.con.execute(
            "SELECT asset_id,tag FROM asset_tag ORDER BY asset_id"))
        self.assertNotIn(1, tags)
        self.assertNotIn(2, tags)
        self.assertEqual(tags[3], "演员:NOZOMI")
        self.assertEqual(counts["actor_tags_removed"], 2)
        self.assertEqual(counts["actor_tags_rewritten"], 1)
        self.assertEqual(self.con.execute(
            "PRAGMA foreign_key_check").fetchall(), [])

    def _seed_same_kind_projection(self):
        """`小桃` / `小桃 shixiaotaone` 这类同 kind 目录名投影。

        20 号是规范实体：带两个账号别名，作品集合是 {20,21,22}。21 号是
        `R:\\Media\\<本名 + 账号名>` 投影出来的第二条 creator，作品 {20,21} 全落在 20 号里。
        22 号名字同样由 20 号的本名和别名拼成，但作品 {22,23} 越出了 20 号的集合。
        """
        self.con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,creator) "
            "VALUES(?,'local',?,?,'video',?)",
            [(20, "/x/20.mp4", "20.mp4", "小桃 shixiaotaone"),
             (21, "/x/21.mp4", "21.mp4", "小桃 shixiaotaone"),
             (22, "/x/22.mp4", "22.mp4", "小桃 taomi"),
             (23, "/x/23.mp4", "23.mp4", "小桃 taomi")])
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
            "VALUES(?,?,?,?, 't','t')",
            [(20, "creator", "小桃", "小桃"),
             (21, "creator", "小桃 shixiaotaone", "小桃 shixiaotaone"),
             (22, "creator", "小桃 taomi", "小桃 taomi")])
        self.con.executemany(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
            "VALUES(?,?,?,'stash:performer',0.9)",
            [(20, "shixiaotaone", "shixiaotaone"), (20, "taomi", "taomi")])
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(?,?,?,?,1.0)",
            [(20, 20, "performer", "performer"), (21, 20, "performer", "performer"),
             (22, 20, "performer", "performer"),
             (20, 21, "creator", "legacy:asset"), (21, 21, "creator", "legacy:asset"),
             (22, 22, "creator", "legacy:asset"), (23, 22, "creator", "legacy:asset")])
        self.con.commit()

    def test_collect_merges_same_kind_directory_projection(self):
        self._seed_same_kind_projection()
        rows = [row for row in collect(self.con) if row["drop_id"] == 21]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["keep_id"], 20)
        self.assertEqual(rows[0]["keep_kind"], "creator")
        self.assertEqual(rows[0]["drop_kind"], "creator")
        self.assertIn("同 kind", rows[0]["match_evidence"])

    def test_collect_skips_same_kind_without_asset_or_provenance_evidence(self):
        self._seed_same_kind_projection()
        # 21 号一旦有了自己的外部引用就不再是纯目录投影，留给人工。
        self.con.execute(
            "INSERT INTO entity_external_ref(entity_id,provider,external_kind,external_id) "
            "VALUES(21,'stash','performer','777')")
        self.con.commit()
        drops = {row["drop_id"] for row in collect(self.con)}
        self.assertNotIn(21, drops, "带外部引用的实体不是目录投影")
        self.assertNotIn(22, drops, "作品集合越出保留方时，拼名不足以判同人")

    def test_apply_rewrites_flat_creator_for_same_kind_merge(self):
        self._seed_same_kind_projection()
        rows = [row for row in collect(self.con) if row["drop_id"] == 21]
        counts = apply_rows(self.con, rows)
        self.con.commit()

        self.assertIsNone(self.con.execute("SELECT 1 FROM entity WHERE id=21").fetchone())
        self.assertEqual([row[0] for row in self.con.execute(
            "SELECT creator FROM asset WHERE id IN (20,21) ORDER BY id")], ["小桃", "小桃"])
        self.assertEqual(counts["flat_rewritten"], 2)
        self.assertEqual(self.con.execute(
            "SELECT creator FROM asset WHERE id=22").fetchone()[0], "小桃 taomi",
            "只改写被丢弃的那个名字，不动别的目录名")
        self.assertIn("小桃 shixiaotaone", [row[0] for row in self.con.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=20")])
        self.assertEqual(self.con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_projection_audit_repairs_orphan_flat_fields_tags_and_aliases(self):
        self.con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,creator) "
            "VALUES(?,'local',?,?,'video',?)",
            [(5, "/x/5.mp4", "5.mp4", "瀬奈まお 瀬奈まお"),
             (6, "/x/6.mp4", "6.mp4", "画像を拡大する 画像を拡大する")],
        )
        self.con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
            "VALUES(15,'performer','瀬奈まお','瀬奈まお','t','t')"
        )
        self.con.execute(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
            "VALUES(15,'瀬奈まお 瀬奈まお','瀬奈まお 瀬奈まお','user:merge',1.0)"
        )
        self.con.execute(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(5,15,'performer','javbus:performer',1.0)"
        )
        self.con.executemany(
            "INSERT INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,1.0,'javbus:performer')",
            [(5, "演员:瀬奈まお 瀬奈まお"),
             (6, "演员:画像を拡大する 画像を拡大する")],
        )
        rows = collect_repeated_projections(self.con)
        by_name = {row["bad_name"]: row for row in rows}
        self.assertEqual(by_name["瀬奈まお 瀬奈まお"]["action"], "use-performer")
        self.assertEqual(by_name["画像を拡大する 画像を拡大する"]["action"], "remove-invalid")
        counts = apply_repeated_projections(self.con, rows)
        self.con.commit()
        self.assertEqual(self.con.execute(
            "SELECT creator FROM asset WHERE id=5").fetchone()[0], None)
        self.assertEqual(self.con.execute(
            "SELECT creator FROM asset WHERE id=6").fetchone()[0], None)
        self.assertEqual([row[0] for row in self.con.execute(
            "SELECT tag FROM asset_tag WHERE asset_id=5")], ["演员:瀬奈まお"])
        self.assertEqual([row[0] for row in self.con.execute(
            "SELECT tag FROM asset_tag WHERE asset_id=6")], [])
        self.assertEqual([row[0] for row in self.con.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=15")], [])
        self.assertGreaterEqual(counts["flat_cleared"], 2)


if __name__ == "__main__":
    unittest.main()
