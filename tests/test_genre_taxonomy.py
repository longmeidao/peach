import unittest

from peach import catalog_rules
from peach.genre_taxonomy import (
    CONTENT_GENRES,
    NON_CONTENT_GENRES,
    is_non_content_genre,
    map_genres,
    normalise_genre,
)


def _catalog_vocabulary() -> set[str]:
    names = (
        "LENGTH_TAGS", "TECH_TAGS", "ATTRIBUTE_TAGS", "RELATIONSHIP_TAGS",
        "ROLE_TAGS", "APPEARANCE_TAGS", "SCENE_TAGS", "STORY_TAGS", "POSITION_TAGS",
    )
    vocabulary: set[str] = set()
    for name in names:
        vocabulary |= set(getattr(catalog_rules, name))
    return vocabulary


class GenreTaxonomyTests(unittest.TestCase):
    def test_every_projection_lands_in_the_existing_catalog_vocabulary(self):
        """投影只能落在既有词表上。

        映射表凭翻译造一个新标签不会报错，只会让这个标签在筛选面板、同义词
        取代和统计里全部缺席——写进 ledger 后才发现，就已经是一次真实写入。
        """
        vocabulary = _catalog_vocabulary()
        unknown = sorted({tag for tag in CONTENT_GENRES.values() if tag not in vocabulary})
        self.assertEqual(unknown, [], "这些标签不在 catalog_rules 词表里，先决定收录还是改投影")

    def test_japanese_and_english_keys_share_one_table_and_one_value_space(self):
        """javbus/javdb 给日文类型词，r18dev 给英文；两套键共用一张表、一套值。

        身体尺寸与发行／营销／规格分类一概不进 `CONTENT_GENRES`，和既有的
        「`Featured Actress` 不入库」是同一条线。
        """
        self.assertEqual(CONTENT_GENRES["中出し"], "中出内射")
        self.assertEqual(CONTENT_GENRES["パイパン"], "白虎")
        self.assertEqual(CONTENT_GENRES["女子校生"], "学生")
        self.assertEqual(CONTENT_GENRES["寝取り・寝取られ"], "绿帽NTR")
        self.assertEqual(CONTENT_GENRES["巨乳"], "巨乳")
        self.assertEqual(CONTENT_GENRES["美乳"], "美乳")
        for measurement in ("Dカップ", "Gカップ", "Jカップ", "巨大乳輪"):
            self.assertNotIn(measurement, CONTENT_GENRES,
                             f"{measurement} 是身体尺寸，词表里没有对应分类")
        for marketing in ("独占配信", "配信専用", "単体作品", "企画", "店長推薦作品",
                          "ハイビジョン", "フルハイビジョン(FHD)", "1080p", "60fps",
                          "4時間以上作品", "AV女優"):
            self.assertNotIn(marketing, CONTENT_GENRES,
                             f"{marketing} 是发行/营销/规格分类，不是内容标签")
        self.assertTrue({key for key in CONTENT_GENRES if not key.isascii()})

    def test_no_specific_genre_maps_up_into_a_superseded_broad_bucket(self):
        """来源给了具体标签就照抄，不许升成 `乳系`、`足系` 这种粗桶。

        `TAG_SUPERSESSION` 的定义正是「有具体标签时把粗桶删掉」，所以把
        javbus 的 `巨乳` 映成 `乳系` 等于写入系统随后要丢弃的那个值。2026-09-02
        真写进了账本 57 条，连带暴露出更早的 `"Big Tits": "乳系"` 是同一个错。

        例外只有一种：来源词本身就只说到粗桶那一级。`おっぱい` 没说是巨乳还是
        美乳，映到 `乳系` 才是「取来源给出的那一级」；粗桶在没有具体标签时会被
        保留，所以这一条不是升级。要加新例外，先说出来源词凭什么无法再具体。
        """
        broad_only_sources = {"おっぱい"}
        offenders = sorted(
            f"{source} -> {mapped}"
            for source, mapped in CONTENT_GENRES.items()
            if mapped in catalog_rules.TAG_SUPERSESSION
            and source not in broad_only_sources)
        self.assertEqual(offenders, [], "这些映射升到了粗桶，应映射到来源给出的那一级")
        for source in sorted(broad_only_sources):
            self.assertIn(source, CONTENT_GENRES, f"{source} 已不在表里，例外该跟着去掉")

    def test_content_and_non_content_tables_do_not_overlap(self):
        both = {normalise_genre(key) for key in CONTENT_GENRES} & {
            normalise_genre(value) for value in NON_CONTENT_GENRES
        }
        self.assertEqual(both, set(), "同一个 genre 不能既是内容又被排除")

    def test_case_and_width_variants_hit_the_same_entry(self):
        self.assertEqual(map_genres(["Deep Throat"])[0], ["深喉"])
        self.assertEqual(map_genres(["deep throat"])[0], ["深喉"])
        self.assertEqual(map_genres(["ＤＥＥＰ　ＴＨＲＯＡＴ"])[0], ["深喉"])
        self.assertEqual(map_genres(["３Ｐ"])[0], ["3P多人"])

    def test_japanese_and_english_sources_project_to_one_tag(self):
        """dmm/mgstage 只给日文，r18dev 只给英文；两边必须落到同一个标签。

        这正是官方 tag 长期缺口的成因：抓取脚本各带一份英文表，日文官方来源
        排在 policy 第一位却一个标签也产不出来。
        """
        self.assertEqual(map_genres(["Creampie"])[0], map_genres(["中出し"])[0])
        self.assertEqual(map_genres(["Blowjob"])[0], map_genres(["フェラチオ"])[0])
        self.assertEqual(map_genres(["Big Tits"])[0], map_genres(["巨乳"])[0])

    def test_marketing_and_format_categories_are_excluded_not_missing(self):
        tags, unmapped = map_genres(["AV女優", "単体作品", "サンプル動画", "ハイビジョン"])
        self.assertEqual(tags, [])
        self.assertEqual(unmapped, [], "已判定的非内容分类不该再当成待补条目")
        self.assertTrue(is_non_content_genre("Featured Actress"))

    def test_unrecognised_genres_come_back_for_registration(self):
        tags, unmapped = map_genres(["Creampie", "まだ知らない分類", "Creampie"])
        self.assertEqual(tags, ["中出内射"])
        self.assertEqual(unmapped, ["まだ知らない分類"], "未收录不等于非内容，必须回传登记")

    def test_order_is_first_appearance_and_duplicates_collapse(self):
        tags, _ = map_genres(["巨乳", "Creampie", "Big Tits", "中出し"])
        self.assertEqual(tags, ["巨乳", "中出内射"])


if __name__ == "__main__":
    unittest.main()
