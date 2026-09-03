"""番号体系女优中译：来源匹配、同人合并、日本字形归一与兼容标签同步。"""
import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.migrations import upgrade
from scripts.localize_performer_names import (
    KANJI_ALIAS_SOURCE, apply_rows, collect, main, read_identity_review, read_mapping,
    report_conflicts, resolve_sai, simplify_kanji, strip_zero_width,
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
             (3, "/x/3.mp4", "3.mp4"), (4, "/x/4.mp4", "4.mp4"),
             (5, "/x/5.mp4", "5.mp4"), (6, "/x/6.mp4", "6.mp4"),
             (7, "/x/7.mp4", "7.mp4"), (8, "/x/8.mp4", "8.mp4"),
             (9, "/x/9.mp4", "9.mp4"), (10, "/x/10.mp4", "10.mp4"),
             (11, "/x/11.mp4", "11.mp4")])
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
            "VALUES(?,'performer',?,?, 't','t')",
            [(10, "Alice Shaku", "alice shaku"),
             (11, "Mio Hayakawa", "mio hayakawa"),
             (12, "吉川蓮", "吉川蓮"),
             (13, "Unknown Roman", "unknown roman"),
             (14, "account_01", "account_01"),
             (15, "Hitomi Hoshiya", "hitomi hoshiya"),
             (16, "斎藤満里奈", "斎藤満里奈"),
             (17, "野々宮蘭", "野々宮蘭"),
             (18, "飯岡かなこ", "飯岡かなこ"),
             (20, "安斋拉拉", "安斋拉拉"),
             (21, "\u200c斋藤亚美里", "\u200c斋藤亚美里"),
             (22, "斋藤未来", "斋藤未来")])
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence) "
            "VALUES(?,?,'performer',?,1.0)",
            [(1, 10, "r18:performer"), (2, 11, "r18:performer"),
             (3, 12, "r18:performer"), (4, 13, "r18:performer"),
             (4, 14, "performer"), (5, 15, "r18:performer"),
             (6, 16, "r18:performer"), (7, 17, "performer"),
             (8, 18, "r18:performer"), (9, 20, "r18:performer"),
             (10, 21, "r18:performer"), (11, 22, "r18:performer")])
        self.con.executemany(
            "INSERT INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,1.0,'r18:performer')",
            [(1, "演员:Alice Shaku"), (2, "演员:Mio Hayakawa"),
             (3, "演员:吉川蓮"), (4, "演员:Unknown Roman"),
             (5, "演员:Hitomi Hoshiya"), (6, "演员:斎藤満里奈"),
             (7, "演员:野々宮蘭"), (8, "演员:飯岡かなこ"),
             (9, "演员:安斋拉拉"), (10, "演员:\u200c斋藤亚美里"),
             (11, "演员:斋藤未来")])
        self.con.execute(
            "INSERT INTO entity_external_ref(entity_id,provider,external_kind,external_id) "
            "VALUES(15,'r18','performer_name','星谷瞳')")
        self.con.executemany(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
            "VALUES(?,?,?,'r18:performer',0.9)",
            [(20, "安齋らら", "安齋らら"), (21, "斎藤あみり", "斎藤あみり"),
             (22, "さいとうみらい", "さいとうみらい")])
        self.con.commit()

        self.mapping = root / "actors.xml"
        self.mapping.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<actor-mapping><actor>
<a zh_cn="釈アリス" zh_tw="釋愛麗絲" jp="釈アリス"
 keyword="釈アリス,釋愛麗絲,释爱丽丝,Shaku Alice" tmdb_id="5294947" verified="1" />
<a zh_cn="吉川莲" zh_tw="吉川蓮" jp="吉川蓮"
 keyword="Mio Hayakawa,早川美緒,吉川蓮" tmdb_id="123" verified="1" />
<a zh_cn="Hitomi Hoshiya" zh_tw="星谷瞳" jp="星谷瞳"
 keyword="Hitomi Hoshiya,星谷瞳" tmdb_id="456" verified="1" />
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
                {"entity_id": 15, "current_name": "Hitomi Hoshiya", "japanese_name": "星谷瞳",
                 "kana": "ほしやひとみ", "former_names": ""},
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
        self.assertEqual(rows[15]["target_name"], "星谷瞳")
        self.assertEqual(rows[15]["action"], "localize")
        self.assertIn("r18-nonlatin-release-name", rows[15]["resolution"])

    def test_apply_preserves_aliases_and_rewrites_actor_tags(self):
        counts = apply_rows(self.con, self.plan(), "abc123")
        self.con.commit()
        names = dict(self.con.execute("SELECT id,canonical_name FROM entity WHERE kind='performer'"))
        self.assertEqual(names[10], "释爱丽丝")
        self.assertEqual(names[11], "吉川莲")
        self.assertNotIn(12, names)
        self.assertEqual(names[13], "未収録花子")
        self.assertEqual(names[14], "account_01")
        self.assertEqual(names[15], "星谷瞳")
        aliases = {row[0] for row in self.con.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=10")}
        self.assertTrue({"Alice Shaku", "釈アリス", "しゃくありす", "釋愛麗絲"} <= aliases)
        tags = dict(self.con.execute("SELECT asset_id,tag FROM asset_tag ORDER BY asset_id"))
        self.assertEqual(tags[1], "演员:释爱丽丝")
        self.assertEqual(tags[2], "演员:吉川莲")
        self.assertEqual(tags[3], "演员:吉川莲")
        self.assertEqual(tags[4], "演员:未収録花子")
        self.assertEqual(tags[5], "演员:星谷瞳")
        self.assertEqual(counts["merged"], 1)
        self.assertEqual(self.con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_kanji_simplification_only_touches_names_it_can_finish(self):
        """字形归一只处理纯汉字名；假名和罗马字要的是译名，不是逐字换。"""
        self.assertEqual(simplify_kanji("高山涼音"), "高山凉音")
        self.assertEqual(simplify_kanji("斎藤満里奈"), "齐藤满里奈")
        self.assertEqual(simplify_kanji("浜崎真緒"), "滨崎真绪")
        # 「々」是叠字符号，展开成前一个字，否则名字还是半个日文。
        self.assertEqual(simplify_kanji("野々宮蘭"), "野野宫兰")
        # 简体没有对应字形的日本汉字原样留下，中文资料页也是这么写的。
        self.assertEqual(simplify_kanji("桜咲姫莉"), "樱咲姬莉")
        self.assertEqual(simplify_kanji("辻井穂香"), "辻井穗香")
        # 逐字换只会得到半中半日的名字，这类名字留给映射 XML。
        self.assertEqual(simplify_kanji("飯岡かなこ"), "飯岡かなこ")
        self.assertEqual(simplify_kanji("Alice Shaku"), "Alice Shaku")
        # 已经是简体的名字不该被再动一次。
        self.assertEqual(simplify_kanji("凉森玲梦"), "凉森玲梦")

    def test_collect_simplifies_kanji_without_any_mapping_entry(self):
        """映射里没有这个人，字形照样要归一——这一道不需要外部来源。"""
        rows = {int(row["entity_id"]): row for row in collect(
            self.con, [], read_identity_review(self.review), "kanji-only")}
        self.assertEqual(rows[16]["target_name"], "齐藤满里奈")
        self.assertEqual(rows[16]["action"], "localize-kanji")
        self.assertIn("kanji-simplification", rows[16]["resolution"])
        # 账号型 performer 不翻译，但换字形不是翻译：同一个字的两种写法而已。
        self.assertEqual(rows[17]["target_name"], "野野宫兰")
        self.assertEqual(rows[17]["action"], "localize-kanji")
        self.assertEqual(rows[18]["action"], "keep-unresolved")
        self.assertEqual(rows[18]["target_name"], "飯岡かなこ")

    def test_upstream_glyph_noise_in_the_canonical_name_is_normalised(self):
        """`斎`／`齋` 的简体是 `齐`，`斋` 是另一个字；零宽字符根本不该出现在名字里。"""
        self.assertEqual(strip_zero_width("\u200c斋藤亚美里"), "斋藤亚美里")
        self.assertEqual(resolve_sai("安斋拉拉", ["安齋らら"]), "安齐拉拉")
        # 日文一侧不是 `斎`／`齋` 就没有证据说这个 `斋` 写错了，原样留着。
        self.assertEqual(resolve_sai("安斋拉拉", ["Rara Anzai"]), "安斋拉拉")
        rows = {int(row["entity_id"]): row for row in collect(
            self.con, [], read_identity_review(self.review), "kanji-only")}
        self.assertEqual(rows[20]["target_name"], "安齐拉拉")
        self.assertEqual(rows[21]["target_name"], "齐藤亚美里")
        self.assertEqual(rows[21]["action"], "localize-kanji")
        self.assertEqual(rows[22]["target_name"], "斋藤未来")
        self.assertEqual(rows[22]["action"], "keep-unresolved")

    def test_apply_records_kanji_rows_under_their_own_alias_source(self):
        plan = collect(self.con, [], read_identity_review(self.review), "kanji-only")
        apply_rows(self.con, plan, "kanji-only")
        self.con.commit()
        names = dict(self.con.execute("SELECT id,canonical_name FROM entity"))
        self.assertEqual(names[16], "齐藤满里奈")
        self.assertEqual(names[17], "野野宫兰")
        self.assertEqual(names[18], "飯岡かなこ")
        aliases = dict(self.con.execute(
            "SELECT alias,source FROM entity_alias WHERE entity_id=16"))
        # 旧字形留成别名，否则来源那边再抓一次就又建一个新实体。
        self.assertEqual(aliases["斎藤満里奈"], KANJI_ALIAS_SOURCE)
        tags = dict(self.con.execute("SELECT asset_id,tag FROM asset_tag ORDER BY asset_id"))
        self.assertEqual(tags[6], "演员:齐藤满里奈")
        self.assertEqual(tags[7], "演员:野野宫兰")

    def test_simplified_name_colliding_with_an_existing_entity_is_a_conflict(self):
        """换完字形撞上库里已有的同名实体时不猜，交给人合并。"""
        self.con.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at) "
            "VALUES(19,'performer','齐藤满里奈','齐藤满里奈','t','t')")
        self.con.commit()
        rows = {int(row["entity_id"]): row for row in collect(
            self.con, [], read_identity_review(self.review), "kanji-only")}
        self.assertEqual(rows[16]["action"], "conflict")
        self.assertIn("target-name-conflict", rows[16]["resolution"])
        # 待裁决的那一行只挡住自己：同一批里其它人的字形照样归一，
        # 否则库里一处未合并的同人就能无限期冻住全部改名。
        counts = apply_rows(self.con, list(rows.values()), "kanji-only")
        self.assertEqual(counts["conflicts_skipped"], 1)
        names = dict(self.con.execute("SELECT id,canonical_name FROM entity"))
        self.assertEqual(names[16], "斎藤満里奈")
        self.assertEqual(names[17], "野野宫兰")
        self.assertEqual(report_conflicts(list(rows.values())), 1)

    def test_mapping_xml_is_optional_and_its_revision_is_not(self):
        """那份 XML 不在仓库里，也可能已经不在这台机器上；缺了它字形归一仍要能跑。"""
        out = Path(self.tmp.name) / "plan.csv"
        main(["--db", str(self.db), "--identity-review", str(self.review),
              "--review-csv", str(out)])
        planned = {row["current_name"]: row for row in csv.DictReader(
            out.open(encoding="utf-8-sig"))}
        self.assertEqual(planned["斎藤満里奈"]["target_name"], "齐藤满里奈")
        self.assertEqual(planned["斎藤満里奈"]["revision"], "kanji-only")
        with self.assertRaises(SystemExit):
            main(["--db", str(self.db), "--mapping-xml", str(self.mapping),
                  "--review-csv", str(out)])


if __name__ == "__main__":
    unittest.main()
