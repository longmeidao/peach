"""把一格装了多个艺名的别名拆成一人多名，以及不该被拆的四类括号。"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.entities import split_composite_person_name
from peach.migrations import upgrade
from scripts.split_composite_aliases import apply_rows, collect

ROOT = Path(__file__).resolve().parents[1]


class CompositePersonNameTests(unittest.TestCase):
    def test_a_packed_romaji_field_becomes_one_name_per_person(self):
        self.assertEqual(
            split_composite_person_name("Ako Momona (Kou Akemi, Mari Koizumi)"),
            ["Ako Momona", "Kou Akemi", "Mari Koizumi"])
        self.assertEqual(split_composite_person_name("Nao (Hitomi Koike)"),
                         ["Nao", "Hitomi Koike"])

    def test_a_bracket_repeating_the_name_collapses_to_one(self):
        # 上游把括号无条件填满，`Rei Mizuna (Rei Mizuna)` 是模板产物不是两个人。
        self.assertEqual(split_composite_person_name("Rei Mizuna (Rei Mizuna)"),
                         ["Rei Mizuna"])

    def test_names_carrying_dots_apostrophes_and_hyphens_still_split(self):
        self.assertEqual(split_composite_person_name("A.J. O'Neil (Mary-Ann Doe)"),
                         ["A.J. O'Neil", "Mary-Ann Doe"])

    def test_the_other_four_kinds_of_bracket_are_left_whole(self):
        # 括号里是厂牌消歧、角色出处、接稿状态、去重后缀——都不是这个人的另一个名字。
        for name in ("AV DEBUT（本物人妻）", "アスナ(SAO)", "快慢扳机（接稿中）",
                     "kitty(1)", "Mana(23)", "プレステージプレミアム(PRESTIGEPREMIUM)",
                     "Egami(えがみ)", "Z(指定)ERO"):
            self.assertEqual(split_composite_person_name(name), [name])

    def test_a_plain_name_comes_back_as_itself(self):
        self.assertEqual(split_composite_person_name("  白石亚子 "), ["白石亚子"])
        self.assertEqual(split_composite_person_name(""), [])


class CompositeAliasSplitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name).resolve() / "ledger.db"
        upgrade(self.db, ROOT / "migrations")
        self.con = sqlite3.connect(self.db)
        self.addCleanup(self.con.close)
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
            " VALUES(?,?,?,?,'t','t')",
            [(10, "performer", "藤木美夏", "藤木美夏"),
             (11, "performer", "里中静香", "里中静香"),
             (12, "series", "AV DEBUT（本物人妻）", "av debut（本物人妻）"),
             (13, "tag", "アスナ(SAO)", "アスナ(sao)"),
             (14, "performer", "Kou Akemi", "kou akemi"),
             (15, "performer", "新井爱丽", "新井爱丽")])
        self.con.executemany(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
            " VALUES(?,?,?,?,1.0)",
            [(10, "Ako Momona (Kou Akemi, Mari Koizumi)",
              "ako momona (kou akemi, mari koizumi)", "r18:performer"),
             (11, "Rei Mizuna (Rei Mizuna)", "rei mizuna (rei mizuna)", "r18:performer"),
             (12, "AV DEBUT (Real Married Woman)", "av debut (real married woman)",
              "r18dev:series-localization"),
             (15, "Elly Akira (Elly Arai)", "elly akira (elly arai)",
              "merge:duplicate-identity")])
        self.con.commit()

    def _rows(self):
        return {str(row["value"]): row for row in collect(self.con)}

    def test_only_the_romaji_person_shape_is_marked_auto(self):
        rows = self._rows()
        self.assertEqual(rows["Elly Akira (Elly Arai)"]["verdict"], "auto")
        self.assertEqual(rows["Rei Mizuna (Rei Mizuna)"]["verdict"], "auto")
        # 系列别名的括号里是厂牌，标签的括号里是作品出处。
        self.assertEqual(rows["AV DEBUT (Real Married Woman)"]["verdict"], "review")
        self.assertEqual(rows["AV DEBUT（本物人妻）"]["verdict"], "review")
        self.assertEqual(rows["アスナ(SAO)"]["verdict"], "review")

    def test_a_part_that_is_another_entitys_canonical_name_goes_to_review(self):
        # `Kou Akemi` 已经自己占了一条实体：那意味着可能要合并，不是拆别名顺手能定的。
        row = self._rows()["Ako Momona (Kou Akemi, Mari Koizumi)"]
        self.assertEqual(row["verdict"], "review")
        self.assertIn("撞 entity 14", str(row["note"]))

    def test_applying_replaces_the_packed_row_with_one_row_per_name(self):
        moved = apply_rows(self.con, collect(self.con))
        self.assertEqual(moved, {"added": 3, "removed": 2})
        self.assertEqual(
            self.con.execute("SELECT alias,source FROM entity_alias WHERE entity_id=15"
                             " ORDER BY alias").fetchall(),
            [("Elly Akira", "merge:duplicate-identity"),
             ("Elly Arai", "merge:duplicate-identity")])
        # 每一段都记在提供它的那个来源名下：这几个罗马字确实是它给的，只是被打包在一个字段里。
        self.assertEqual(
            self.con.execute("SELECT alias,source FROM entity_alias WHERE entity_id=11")
            .fetchall(), [("Rei Mizuna", "r18:performer")])

    def test_applying_leaves_every_review_row_untouched(self):
        apply_rows(self.con, collect(self.con))
        for entity_id, alias in ((10, "Ako Momona (Kou Akemi, Mari Koizumi)"),
                                 (12, "AV DEBUT (Real Married Woman)")):
            self.assertEqual(
                self.con.execute("SELECT count(*) FROM entity_alias"
                                 " WHERE entity_id=? AND alias=?",
                                 (entity_id, alias)).fetchone()[0], 1)
        self.assertEqual(
            self.con.execute("SELECT canonical_name FROM entity WHERE id=13")
            .fetchone()[0], "アスナ(SAO)")


if __name__ == "__main__":
    unittest.main()
