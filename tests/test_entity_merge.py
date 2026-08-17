"""实体合并：同一位女优的旧艺名与现用艺名各成一个实体时的归并。

合并不可逆，所以关系迁移、别名保留和唯一约束冲突的处理都要有回归。
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.entities import merge_entity
from peach.migrations import upgrade

ROOT = Path(__file__).resolve().parents[1]


class EntityMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        upgrade(self.db, ROOT / "migrations")
        self.con = sqlite3.connect(self.db)
        for asset_id in (1, 2, 3):
            self.con.execute(
                "INSERT INTO asset(id,location,path,name,medium) VALUES(?,?,?,?,'video')",
                (asset_id, "local", f"/x/{asset_id}.mp4", f"{asset_id}.mp4"))
        for entity_id, name in ((10, "橋本ありな"), (11, "新ありな")):
            self.con.execute(
                "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES(?,'performer',?,?,'t','t')", (entity_id, name, name.lower()))
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)"
            " VALUES(?,?,'performer','r18',1.0)",
            [(1, 10), (2, 10), (2, 11), (3, 11)])
        self.con.commit()

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_merge_moves_relations_and_keeps_the_old_name_searchable(self):
        moved = merge_entity(self.con, target_id=10, source_id=11,
                             source_name="新ありな", alias_source="r18:performer")
        self.con.commit()

        assets = {r[0] for r in self.con.execute(
            "SELECT asset_id FROM asset_entity WHERE entity_id=10")}
        self.assertEqual(assets, {1, 2, 3}, "三条关系都应归到保留实体")
        self.assertEqual(moved["assets"], 1, "asset 2 两边都有，去重后只迁移 asset 3")
        self.assertIsNone(self.con.execute(
            "SELECT 1 FROM entity WHERE id=11").fetchone(), "被并入的实体应删除")
        aliases = {r[0] for r in self.con.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=10")}
        self.assertIn("新ありな", aliases, "旧名必须留作别名，否则按它搜索会落空")
        self.assertEqual(moved["aliases"], 0, "source 无别名时计数应为 0")

    def test_merge_moves_source_aliases_and_counts_them(self):
        self.con.execute(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
            " VALUES(11,'ありな','ありな','r18',1.0)")
        self.con.commit()
        moved = merge_entity(self.con, target_id=10, source_id=11,
                             source_name="新ありな", alias_source="r18:performer")
        self.con.commit()
        self.assertEqual(moved["aliases"], 1, "source 的别名应被迁移并计数")

    def test_conflicting_external_refs_are_dropped_not_overwritten(self):
        """UNIQUE(entity_id,provider,external_kind) 决定同源只能留一条。"""
        self.con.executemany(
            "INSERT INTO entity_external_ref(entity_id,provider,external_kind,external_id)"
            " VALUES(?,'stash','performer',?)", [(10, "450"), (11, "461")])
        self.con.commit()
        moved = merge_entity(self.con, target_id=10, source_id=11,
                             source_name="新ありな", alias_source="r18:performer")
        self.con.commit()
        self.assertEqual(moved["dropped_refs"], 1, "同 provider 的第二条要被丢弃并报告")
        kept = self.con.execute(
            "SELECT external_id FROM entity_external_ref WHERE entity_id=10").fetchall()
        self.assertEqual(kept, [("450",)], "保留目标实体原有的引用")

    def test_merge_leaves_no_dangling_rows(self):
        merge_entity(self.con, target_id=10, source_id=11,
                     source_name="新ありな", alias_source="r18:performer")
        self.con.commit()
        for table in ("asset_entity", "entity_alias", "entity_external_ref",
                      "entity_link", "entity_search_term"):
            left = self.con.execute(
                f"SELECT count(*) FROM {table} WHERE entity_id=11").fetchone()[0]
            self.assertEqual(left, 0, f"{table} 不应残留被删实体的行")
        self.assertEqual(
            self.con.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
