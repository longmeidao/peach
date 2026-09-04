"""厂牌重名合并：配错一对就是把两家厂牌的作品搅在一起，而且不可逆。

这里守的是「什么才算证据」。两条判据都不许退化成转写或形状猜测。
"""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load_module():
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(
        "merge_studio_name_variants", REPO / "scripts" / "merge_studio_name_variants.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VariantKeyTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_two_different_japanese_names_never_share_a_key(self):
        """真实陷阱：只留 ASCII 的折法把这两家都折成 `tv`，凭空造出一对。

        `シロウトTV` 是素人企划，`ラグジュTV`（16 部）是另一家。合并它们不可逆。
        """
        self.assertNotEqual(self.module.variant_key("シロウトTV"),
                            self.module.variant_key("ラグジュTV"))
        self.assertNotEqual(self.module.variant_key("プレステージ"),
                            self.module.variant_key("ムーディーズ"))

    def test_quote_star_and_fullwidth_spellings_fold_together(self):
        for left, right in (("AVS collector's", "AVS collector’s"),
                            ("OFFICE K'S", "OFFICE K’S"),
                            ("D*Collection", "D☆Collection"),
                            ("kira*kira", "kira☆kira"),
                            ("V&R PRODUCE", "V＆R PRODUCE")):
            with self.subTest(left=left):
                self.assertEqual(self.module.variant_key(left),
                                 self.module.variant_key(right))

    def test_unrelated_latin_studios_keep_their_own_keys(self):
        self.assertNotEqual(self.module.variant_key("Fitch"),
                            self.module.variant_key("Fetish Box"))


class SpellingVariantTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_the_ascii_spelling_survives(self):
        """用户 2026-09-04 定的口径：统一为英文、罗马音。"""
        names = {1: "AVS collector's", 2: "AVS collector’s"}
        rows = self.module.spelling_variants(names, {1: 6, 2: 6})
        self.assertEqual([(row["keep_id"], row["drop_id"]) for row in rows], [(1, 2)])

    def test_the_ascii_side_wins_even_with_fewer_assets(self):
        """作品数不参与这一类判断：写法才是这里唯一的取舍点。"""
        names = {1: "D*Collection", 2: "D☆Collection"}
        rows = self.module.spelling_variants(names, {1: 1, 2: 99})
        self.assertEqual(rows[0]["keep_name"], "D*Collection")

    def test_two_ascii_spellings_fall_back_to_the_asset_count(self):
        names = {1: "Hey Hey", 2: "HEYHEY"}
        rows = self.module.spelling_variants(names, {1: 2, 2: 40})
        self.assertEqual(rows[0]["keep_id"], 2)

    def test_three_entities_on_one_key_are_left_to_a_human(self):
        """两条能配成一对，三条要先决定谁并进谁——那不是脚本该替人做的。"""
        names = {1: "kira*kira", 2: "kira☆kira", 3: "kira★kira"}
        self.assertEqual(len({self.module.variant_key(n) for n in names.values()}), 1)
        self.assertEqual(self.module.spelling_variants(names, {}), [])

    def test_a_studio_without_a_twin_is_not_a_pair(self):
        self.assertEqual(self.module.spelling_variants({1: "Prestige"}, {1: 425}), [])


class ScriptVariantTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.names = {1: "MOODYZ", 2: "ムーディーズ", 3: "Prestige", 4: "プレステージ"}
        self.counts = {1: 122, 2: 7, 3: 425, 4: 9}

    def rows(self, prefixes):
        return self.module.script_variants(self.names, self.counts, prefixes, set())

    def test_a_shared_code_prefix_is_the_evidence(self):
        """前缀属于厂牌。`ムーディーズ` 的 MIDV 也出现在 `MOODYZ` 名下就是同一家。"""
        rows = self.rows({1: {"MIDE", "MIDV"}, 2: {"MIDV"}})
        self.assertEqual([(row["keep_name"], row["drop_name"]) for row in rows],
                         [("MOODYZ", "ムーディーズ")])
        self.assertIn("MIDV", str(rows[0]["evidence"]))

    def test_the_latin_side_is_kept_regardless_of_asset_count(self):
        rows = self.module.script_variants(
            self.names, {1: 1, 2: 999}, {1: {"MIDV"}, 2: {"MIDV"}}, set())
        self.assertEqual(rows[0]["keep_name"], "MOODYZ")

    def test_no_shared_prefix_means_no_pair(self):
        """名字读起来像不算证据。这条捷径唯一的身份保证就是前缀。"""
        self.assertEqual(self.rows({1: {"MIDE"}, 2: {"ABP"}}), [])

    def test_a_prefix_shared_with_two_latin_studios_is_left_to_a_human(self):
        rows = self.rows({1: {"ABP"}, 2: {"ABP"}, 3: {"ABP"}})
        self.assertEqual(rows, [])

    def test_a_japanese_studio_with_no_codes_at_all_is_left_alone(self):
        """`ヒビノ` 这类只有 1 部、番号取不出前缀的，没有可核验的证据。"""
        self.assertEqual(self.rows({1: {"MIDV"}, 2: set()}), [])

    def test_entities_already_paired_by_spelling_are_skipped(self):
        taken = {1, 2}
        self.assertEqual(
            self.module.script_variants(self.names, self.counts,
                                        {1: {"MIDV"}, 2: {"MIDV"}}, taken), [])


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name).resolve() / "ledger.db"
        self.connection = sqlite3.connect(self.path)
        self.connection.executescript(
            "CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT,"
            " normalized_name TEXT, updated_at TEXT);"
            "CREATE TABLE entity_alias(entity_id INTEGER, alias TEXT,"
            " normalized_alias TEXT, source TEXT, confidence REAL,"
            " UNIQUE(entity_id, normalized_alias));"
            "CREATE TABLE entity_external_ref(entity_id INTEGER, provider TEXT,"
            " external_kind TEXT, external_id TEXT,"
            " UNIQUE(entity_id, provider, external_kind));"
            "CREATE TABLE entity_link(entity_id INTEGER, link_kind TEXT, label TEXT,"
            " url TEXT, hostname TEXT, is_sensitive INTEGER, metadata_json TEXT,"
            " created_at TEXT, updated_at TEXT, UNIQUE(entity_id, url));"
            "CREATE TABLE entity_search_term(entity_id INTEGER, term TEXT,"
            " purpose TEXT, source TEXT, created_at TEXT, UNIQUE(entity_id, term));"
            "CREATE TABLE asset(id INTEGER PRIMARY KEY, code TEXT, studio TEXT);"
            "CREATE TABLE asset_entity(asset_id INTEGER, entity_id INTEGER, role TEXT,"
            " source TEXT, confidence REAL, metadata_json TEXT, first_seen_at TEXT,"
            " last_seen_at TEXT, UNIQUE(asset_id, entity_id, role));")
        self.connection.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(?,?,?,?)",
            [(1, "studio", "MOODYZ", "moodyz"), (2, "studio", "ムーディーズ", "ムーディーズ")])
        self.connection.executemany(
            "INSERT INTO asset(id,code,studio) VALUES(?,?,?)",
            [(10, "MIDE-100", "MOODYZ"), (11, "MIDV-200", "ムーディーズ")])
        self.connection.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role) VALUES(?,?,'studio')",
            [(10, 1), (11, 2)])
        self.connection.commit()
        self.row = {"keep_id": 1, "keep_name": "MOODYZ", "keep_assets": 1,
                    "drop_id": 2, "drop_name": "ムーディーズ", "drop_assets": 1,
                    "klass": "日文名／罗马字名", "evidence": "共用番号前缀 MIDV"}

    def tearDown(self):
        self.connection.close()
        self.tmp.cleanup()

    def test_the_flat_projection_follows_the_canonical_relation(self):
        """只改实体不改投影，下一次刮削会照着 `asset.studio` 把旧实体再建一遍。"""
        with self.connection:
            moved = self.module.apply_rows(self.connection, [self.row])
        self.assertEqual(moved["flat_rewritten"], 1)
        self.assertEqual(
            sorted(row[0] for row in self.connection.execute("SELECT studio FROM asset")),
            ["MOODYZ", "MOODYZ"])

    def test_the_discarded_name_survives_as_an_alias(self):
        """旧名一律留作别名，否则按旧名搜索会落空。"""
        with self.connection:
            self.module.apply_rows(self.connection, [self.row])
        aliases = [row[0] for row in self.connection.execute(
            "SELECT alias FROM entity_alias WHERE entity_id=1")]
        self.assertIn("ムーディーズ", aliases)

    def test_every_asset_ends_up_on_the_surviving_entity(self):
        with self.connection:
            self.module.apply_rows(self.connection, [self.row])
        self.assertEqual(
            [row[0] for row in self.connection.execute(
                "SELECT count(*) FROM asset_entity WHERE entity_id=1")], [2])
        self.assertEqual(
            [row[0] for row in self.connection.execute(
                "SELECT count(*) FROM entity WHERE id=2")], [0])


if __name__ == "__main__":
    unittest.main()
