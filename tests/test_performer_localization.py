"""番号体系女优中译：来源匹配、同人合并与兼容标签同步。"""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.migrations import upgrade
from scripts.localize_performer_names import (
    apply_rows, collect, read_identity_review, read_mapping,
)

ROOT = Path(__file__).resolve().parents[1]


class PerformerLocalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.db = root / "ledger.db"
        upgrade(self.db, ROOT / "migrations")
        self.con = sqlite3.connect(self.db)
        self.con.executemany(
            "INSERT INTO asset(id,location,path,name,medium) VALUES(?,'local',?,?,'video')",
            [(1, "/x/1.mp4", "1.mp4"), (2, "/x/2.mp4", "2.mp4"),
             (3, "/x/3.mp4", "3.mp4"), (4, "/x/4.mp4", "4.mp4")])
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
            "VALUES(?,'performer',?,?, 't','t')",
            [(10, "Alice Shaku", "alice shaku"),
             (11, "Mio Hayakawa", "mio hayakawa"),
             (12, "吉川蓮", "吉川蓮"),
             (13, "Unknown Roman", "unknown roman"),
             (14, "account_01", "account_01")])
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(?,?,'performer',?,1.0)",
            [(1, 10, "r18:performer"), (2, 11, "r18:performer"),
             (3, 12, "r18:performer"), (4, 13, "r18:performer"),
             (4, 14, "performer")])
        self.con.executemany(
            "INSERT INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,1.0,'r18:performer')",
            [(1, "演员:Alice Shaku"), (2, "演员:Mio Hayakawa"),
             (3, "演员:吉川蓮"), (4, "演员:Unknown Roman")])
        self.con.commit()

        self.mapping = root / "actors.xml"
        self.mapping.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<actor-mapping><actor>
<a zh_cn="釈アリス" zh_tw="釋愛麗絲" jp="釈アリス"
 keyword="釈アリス,釋愛麗絲,释爱丽丝,Shaku Alice" tmdb_id="5294947" verified="1" />
<a zh_cn="吉川莲" zh_tw="吉川蓮" jp="吉川蓮"
 keyword="Mio Hayakawa,早川美緒,吉川蓮" tmdb_id="123" verified="1" />
</actor></actor-mapping>""", encoding="utf-8")
        self.review = root / "review.csv"
        with self.review.open("w", encoding="utf-8-sig", newline="") as handle:
            fields = ("entity_id", "current_name", "japanese_name", "kana", "former_names")
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows([
                {"entity_id": 10, "current_name": "Alice Shaku", "japanese_name": "釈アリス",
                 "kana": "しゃくありす", "former_names": ""},
                {"entity_id": 11, "current_name": "Mio Hayakawa", "japanese_name": "早川美緒",
                 "kana": "はやかわみお", "former_names": ""},
                {"entity_id": 12, "current_name": "Ren Yoshikawa", "japanese_name": "吉川蓮",
                 "kana": "よしかわれん", "former_names": ""},
                {"entity_id": 13, "current_name": "Unknown Roman", "japanese_name": "未収録花子",
                 "kana": "", "former_names": ""},
            ])

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def plan(self):
        return collect(
            self.con, read_mapping(self.mapping), read_identity_review(self.review), "abc123")

    def test_collect_localizes_alice_merges_one_identity_and_skips_accounts(self):
        rows = {int(row["entity_id"]): row for row in self.plan()}
        self.assertEqual(rows[10]["target_name"], "释爱丽丝")
        self.assertEqual(rows[10]["action"], "localize")
        self.assertEqual(rows[11]["target_name"], "吉川莲")
        self.assertEqual(rows[11]["action"], "merge-and-localize")
        self.assertEqual(rows[12]["action"], "merge-drop")
        self.assertEqual(rows[12]["merge_target_id"], 11)
        self.assertEqual(rows[13]["target_name"], "未収録花子")
        self.assertEqual(rows[13]["action"], "localize-jp-fallback")
        self.assertEqual(rows[14]["action"], "keep-non-release")

    def test_apply_preserves_aliases_and_rewrites_actor_tags(self):
        counts = apply_rows(self.con, self.plan(), "abc123")
        self.con.commit()
        names = dict(self.con.execute("SELECT id,canonical_name FROM entity WHERE kind='performer'"))
        self.assertEqual(names[10], "释爱丽丝")
        self.assertEqual(names[11], "吉川莲")
        self.assertNotIn(12, names)
        self.assertEqual(names[13], "未収録花子")
        self.assertEqual(names[14], "account_01")
        aliases = {row[0] for row in self.con.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=10")}
        self.assertTrue({"Alice Shaku", "釈アリス", "しゃくありす", "釋愛麗絲"} <= aliases)
        tags = dict(self.con.execute("SELECT asset_id,tag FROM asset_tag ORDER BY asset_id"))
        self.assertEqual(tags[1], "演员:释爱丽丝")
        self.assertEqual(tags[2], "演员:吉川莲")
        self.assertEqual(tags[3], "演员:吉川莲")
        self.assertEqual(tags[4], "演员:未収録花子")
        self.assertEqual(counts["merged"], 1)
        self.assertEqual(self.con.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
