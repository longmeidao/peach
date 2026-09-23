"""label 属于片商，但不当片商处理（ADR-0049）。"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach import web_contract as rm_web
from peach.entities import merge_entity
from peach.migrations import upgrade
from scripts.install_label_makers import install, plan

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


class LabelMakerTests(unittest.TestCase):
    """KMP 旗下两个 label、妄想族旗下一个，妄想族自己在账本里还没有实体。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.db = root / "ledger.db"
        upgrade(self.db, MIGRATIONS)
        self.con = sqlite3.connect(self.db)
        self.con.row_factory = sqlite3.Row
        self.addCleanup(self.con.close)
        self.con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,size,first_seen)"
            " VALUES(?,'local',?,?,'video',100,'2026-01-01')",
            [(1, r"R:\Media\a.mp4", "a.mp4"), (2, r"R:\Media\b.mp4", "b.mp4"),
             (3, r"R:\Media\c.mp4", "c.mp4")])
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
            " VALUES(?,'studio',?,?,'t','t')",
            [(5607, "K M Produce", "k m produce"), (5569, "BAZOOKA", "bazooka"),
             (5638, "S級素人", "s級素人"), (8248, "ABC/妄想族", "abc/妄想族")])
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)"
            " VALUES(?,?,'studio','test',1.0)", [(1, 5569), (2, 5607), (3, 8248)])
        self.con.commit()
        self.rows = [
            {"label": "BAZOOKA", "maker": "K M Produce", "evidence": "KMP 名录"},
            {"label": "S級素人", "maker": "K M Produce", "evidence": "KMP 名录"},
            {"label": "ABC/妄想族", "maker": "妄想族", "evidence": "妄想族名录"},
        ]
        logos = root / "logos"; logos.mkdir()
        avatars = root / "avatars"; avatars.mkdir()
        self.contract = rm_web.WebContract(self.db, avatar_root=avatars, logo_root=logos)

    def apply(self, rows=None, *, create_makers=True):
        planned = plan(self.con, rows or self.rows, create_makers=create_makers)
        with self.con:
            install(self.con, planned, source="t.csv")
        return planned

    def maker_of(self, label_id):
        row = self.con.execute(
            "SELECT e.canonical_name FROM label_maker lm JOIN entity e ON e.id=lm.maker_id"
            " WHERE lm.label_id=?", (label_id,)).fetchone()
        return row[0] if row else None

    def test_a_maker_missing_from_the_ledger_is_only_created_when_asked(self):
        planned = plan(self.con, self.rows, create_makers=False)
        self.assertEqual([item["action"] for item in planned], ["insert", "insert", "skip"])
        self.assertIn("--create-makers", planned[2]["reason"])
        self.apply()
        self.assertEqual(self.maker_of(8248), "妄想族")

    def test_rerunning_the_same_table_writes_nothing(self):
        self.apply()
        self.assertEqual({item["action"] for item in self.apply()}, {"skip"})
        self.assertEqual(self.con.execute("SELECT count(*) FROM label_maker").fetchone()[0], 3)

    def test_a_label_changing_hands_is_overwritten_not_added(self):
        self.apply()
        planned = self.apply([{"label": "BAZOOKA", "maker": "妄想族", "evidence": "转手"}])
        self.assertEqual(planned[0]["action"], "update")
        self.assertEqual(self.maker_of(5569), "妄想族")

    def test_only_one_layer_is_accepted(self):
        """label 不能再挂 label，片商自己也不能是别家的 label。"""
        self.apply()
        planned = plan(self.con, [
            {"label": "K M Produce", "maker": "妄想族", "evidence": "x"},
            {"label": "S級素人", "maker": "BAZOOKA", "evidence": "x"},
        ], create_makers=True)
        self.assertEqual([item["action"] for item in planned], ["skip", "skip"])

    def test_the_label_page_points_at_its_maker_and_keeps_its_own_works(self):
        self.apply()
        page = rm_web.q_entity(self.contract, {"kind": "studio", "name": "BAZOOKA"})
        self.assertEqual(page["maker"]["name"], "K M Produce")
        self.assertEqual(page["asset_count"], 1)
        self.assertEqual(page["labels"], [])

    def test_the_maker_page_lists_its_labels_without_absorbing_their_works(self):
        self.apply()
        page = rm_web.q_entity(self.contract, {"kind": "studio", "name": "K M Produce"})
        self.assertEqual([label["name"] for label in page["labels"]], ["BAZOOKA", "S級素人"])
        self.assertEqual(page["asset_count"], 1)
        self.assertIsNone(page["maker"])

    def test_the_detail_carries_the_maker_beside_the_label(self):
        self.apply()
        studio = rm_web.q_item(self.contract, 3)["entity_refs"]["studio"]
        self.assertEqual([ref["name"] for ref in studio], ["ABC/妄想族"])
        self.assertEqual(studio[0]["maker"]["name"], "妄想族")
        self.assertNotIn("maker", rm_web.q_item(self.contract, 2)["entity_refs"]["studio"][0])

    def test_merging_a_label_carries_its_maker_over(self):
        self.apply()
        self.con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
            " VALUES(9000,'studio','BAZOOKA!','bazooka!','t','t')")
        merge_entity(self.con, target_id=9000, source_id=5569, source_name="BAZOOKA", alias_source="test")
        self.assertEqual(self.maker_of(9000), "K M Produce")
        self.assertIsNone(self.maker_of(5569))

    def test_merging_a_maker_moves_its_labels(self):
        self.apply()
        self.con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
            " VALUES(9001,'studio','KMP','kmp','t','t')")
        merge_entity(self.con, target_id=9001, source_id=5607, source_name="K M Produce", alias_source="test")
        self.assertEqual({self.maker_of(5569), self.maker_of(5638)}, {"KMP"})

    def test_merging_a_label_into_its_own_maker_drops_the_self_link(self):
        self.apply()
        merge_entity(self.con, target_id=5607, source_id=5569, source_name="BAZOOKA", alias_source="test")
        self.assertIsNone(self.maker_of(5607))
        self.assertEqual(self.con.execute(
            "SELECT count(*) FROM label_maker WHERE label_id=maker_id").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
