"""外部入口 id 回填：一位对上几个 id 就登记几条，已登记的跳过，撞号的点名等人判。"""
import argparse
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.entry_links import EXTERNAL_KIND
from peach.migrations import upgrade
from scripts.backfill_performer_entry_ids import (
    CONFLICT, HAVE, JAVDB, OK, TAKEN, apply_rows, plan,
)

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


class EntryIdBackfillTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.db = self.root / "ledger.db"
        sqlite3.connect(self.db).close()
        upgrade(self.db, MIGRATIONS)
        self.connection = sqlite3.connect(self.db)
        self.addCleanup(self.connection.close)
        for entity_id, name in ((10, "释爱丽丝"), (11, "天川空")):
            self.connection.execute(
                "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES(?,'performer',?,?,'t','t')", (entity_id, name, name))
        self.connection.commit()
        self.cache = self.root / "javdb"
        self.cache.mkdir()

    def page(self, name: str, actor: str) -> None:
        """一页 javdb 资料页：名字在标题里，演员 id 在收藏那条链接里。"""
        (self.cache / f"{actor}.html").write_text(
            f'<html><body><span class="actor-section-name">{name}</span>'
            f'<a href="/actors/{actor}/collect"></a></body></html>',
            encoding="utf-8")

    def rows(self) -> list[dict]:
        args = argparse.Namespace(javdb_cache=self.cache, csv=[])
        return plan(self.connection, args)

    def saved(self) -> list[tuple]:
        return self.connection.execute(
            "SELECT entity_id,external_id FROM entity_external_ref"
            " WHERE provider=? AND external_kind=? ORDER BY external_id",
            (JAVDB, EXTERNAL_KIND)).fetchall()

    def test_one_performer_with_two_pages_gets_both_registered(self):
        self.page("释爱丽丝", "d45k9")
        self.page("释爱丽丝", "ZX5z7")
        rows = self.rows()
        self.assertEqual([row["verdict"] for row in rows], [OK, OK])
        self.assertEqual(apply_rows(self.connection, rows), (2, 2))
        self.assertEqual(self.saved(), [(10, "ZX5z7"), (10, "d45k9")])

    def test_a_row_already_in_the_ledger_is_skipped_and_the_rest_still_land(self):
        """同一批证据可以重复跑：已登记的那条不报错、不重写、也不算冲突。"""
        self.page("释爱丽丝", "d45k9")
        apply_rows(self.connection, self.rows())
        self.page("释爱丽丝", "ZX5z7")
        rows = self.rows()
        self.assertEqual([row["verdict"] for row in rows], [OK, HAVE])
        self.assertEqual(apply_rows(self.connection, rows), (1, 1))
        self.assertEqual(self.saved(), [(10, "ZX5z7"), (10, "d45k9")])

    def test_an_id_held_by_another_performer_is_named_not_swallowed(self):
        """主键决定一个 id 只属于一位，所以这一条要写出占有者等人判。"""
        self.connection.execute(
            "INSERT INTO entity_external_ref(entity_id,provider,external_kind,external_id)"
            " VALUES(11,?,?,'d45k9')", (JAVDB, EXTERNAL_KIND))
        self.connection.commit()
        self.page("释爱丽丝", "d45k9")
        rows = self.rows()
        self.assertEqual([row["verdict"] for row in rows], [TAKEN])
        self.assertIn("11", rows[0]["evidence"])
        self.assertEqual(apply_rows(self.connection, rows), (0, 0))

    def test_two_performers_claiming_one_page_are_left_to_a_person(self):
        self.connection.execute(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
            " VALUES(11,'释爱丽丝','释爱丽丝','test',1.0)")
        self.connection.commit()
        self.page("释爱丽丝", "d45k9")
        rows = self.rows()
        self.assertEqual([row["verdict"] for row in rows], [CONFLICT, CONFLICT])
        self.assertEqual(apply_rows(self.connection, rows), (0, 0))


if __name__ == "__main__":
    unittest.main()
