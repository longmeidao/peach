"""搜索栏补全：补出来的每一项都点得开，口径与 `/api/items` 同源。

这一域最容易出的不是报错，是两侧漂开：补全按一套判据取词、搜索按另一套判据找片，
于是下拉里给出的名字搜出零条，或者搜得到的标签补不出来。所以这里的断言分两层——
一层钉具体行为，一层遍历每个补全项拿它去真的搜一次。
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach import web_contract as rm_web
from peach.web_entity import SUGGEST_GROUPS

from support.ledger import fresh_ledger

STAMP = "2026-09-07T00:00:00Z"


class LedgerFixture(unittest.TestCase):
    """一份小账本：几部片挂着一位有别名的女优，另有厂牌、系列、标签和事务所。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.db = fresh_ledger(root)
        self.con = sqlite3.connect(self.db)
        self.con.row_factory = sqlite3.Row
        self.addCleanup(self.con.close)
        self.con.executemany(
            "INSERT INTO asset(id,location,path,name,medium,size,first_seen,code,"
            "catalog_title,disposal) VALUES(?,'local',?,?,'video',100,'2026-01-01',?,?,?)",
            [(1, r"R:\Media\one.mp4", "one.mp4", None, None, None),
             (2, r"R:\Media\two.mp4", "two.mp4", None, None, None),
             (3, r"R:\Media\three.mp4", "three.mp4", None, None, None),
             (4, r"R:\Media\ABW-123.mp4", "ABW-123.mp4", "ABW-123", "潜入取材の一日", None),
             (5, r"R:\Media\ABW-999.mp4", "ABW-999.mp4", "ABW-999", "已删除的一部", "trash"),
             # 既无番号也无发行标题，只有一个相机文件名。
             (6, r"R:\Media\IMG_2757_682.MOV", "IMG_2757_682.MOV", None, None, None),
             # 文件名里有别人的番号，它自己没有番号。
             (7, r"R:\Media\old-ABW-clip.mp4", "old-ABW-clip.mp4", None, None, None)],
        )
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,created_at,updated_at)"
            " VALUES(?,?,?,?,'t','t')",
            [(11, "performer", "涼森れむ", "涼森れむ"),
             (12, "performer", "神雪", "神雪"),
             (13, "studio", "ラグジュTV", "ラグジュtv"),
             (14, "series", "ドキュメント", "ドキュメント"),
             (15, "tag", "足交", "足交"),
             # 与女优同名的标签是另一个身份的冒充，标签组不该收它。
             (16, "tag", "神雪", "神雪"),
             # 时长标签是筛选控件，不是可搜的词。
             (17, "tag", "短片-2分内", "短片-2分内"),
             (18, "agency", "Capsule Agency", "capsule agency"),
             # 名下没有任何作品的人和事务所：账本里有身份，按名字搜是空的。
             (19, "performer", "涼森みつ", "涼森みつ"),
             (20, "agency", "Capsule Reserve", "capsule reserve"),
             # 只出现在回收站那条上的标签。
             (21, "tag", "足底", "足底"),
             # 三个字的标签落在搜索的 FTS 分支上，两个字的落在 LIKE 分支上。
             (22, "tag", "巨乳系", "巨乳系"),
             # 同一个字头的一批标签，用来看每组的条数上限。
             (23, "tag", "足元", "足元"), (24, "tag", "足指", "足指"),
             (25, "tag", "足首", "足首"), (26, "tag", "足裏", "足裏"),
             (27, "tag", "足音", "足音"),
             # 「MO」是 MOODYZ 的词首、SO MODEL AGENT 里一个词的词首，
             # 而在 kemonokai 中间。两个字母的拉丁输入只该命中前两个。
             (28, "studio", "MOODYZ", "moodyz"),
             (29, "creator", "kemonokai", "kemonokai"),
             (30, "agency", "SO MODEL AGENT", "so model agent")],
        )
        self.con.executemany(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source)"
            " VALUES(?,?,?,'test')",
            [(11, "凉森", "凉森"), (18, "カプセル", "カプセル")],
        )
        self.con.execute(
            "INSERT INTO entity_search_term(entity_id,term,purpose,source,created_at)"
            " VALUES(11,'Remu','discovery','test',?)", (STAMP,))
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence)"
            " VALUES(?,?,?,'test',1.0)",
            [(1, 11, "performer"), (2, 11, "performer"), (3, 11, "performer"),
             (1, 12, "performer"), (1, 13, "studio"), (2, 13, "studio"),
             (2, 14, "series"), (1, 15, "tag"), (2, 15, "tag"), (3, 16, "tag"),
             (3, 17, "tag"), (5, 21, "tag"), (1, 22, "tag"), (2, 22, "tag"),
             (1, 23, "tag"), (1, 24, "tag"), (1, 25, "tag"), (1, 26, "tag"),
             (1, 27, "tag"), (3, 28, "studio"), (3, 29, "creator")],
        )
        self.con.executemany(
            "INSERT INTO entity_membership(member_id,agency_id,source,checked_at)"
            " VALUES(?,?,'test',?)",
            [(11, 18, STAMP), (12, 18, STAMP), (19, 20, STAMP), (29, 30, STAMP)],
        )
        self.con.commit()
        self.contract = rm_web.WebContract(self.db)

    def suggest(self, query, limit=5):
        return rm_web.q_suggest(self.contract, query, limit)

    def group(self, query, kind, limit=5):
        for group in self.suggest(query, limit)["groups"]:
            if group["kind"] == kind:
                return group["items"]
        return []

    def values(self, query, kind, limit=5):
        return [item["value"] for item in self.group(query, kind, limit)]

    def total(self, query):
        return rm_web.q_items(self.contract, {"q": query, "limit": "10"})["total"]


class SuggestTests(LedgerFixture):
    """补全按输入给出馆藏里的身份与作品。"""

    def test_a_canonical_name_completes_from_its_first_characters(self):
        self.assertEqual(self.values("涼森", "performer"), ["涼森れむ"])

    def test_the_suggestion_carries_how_many_works_are_behind_it(self):
        self.assertEqual(self.group("涼森", "performer")[0]["n"], 3)

    def test_an_alias_completes_to_the_canonical_name(self):
        """输入的写法是别名，补出来的必须是这个人在馆藏里的统称。"""
        self.assertEqual(self.values("凉森", "performer"), ["涼森れむ"])

    def test_a_hit_on_an_alias_says_which_writing_matched(self):
        """不说明凭什么，用户会以为补错了人。"""
        self.assertEqual(self.group("凉森", "performer")[0]["matched"], "凉森")

    def test_a_hit_on_the_canonical_name_says_nothing_extra(self):
        self.assertEqual(self.group("涼森", "performer")[0]["matched"], "")

    def test_a_search_term_reaches_the_same_person(self):
        self.assertEqual(self.values("Remu", "performer"), ["涼森れむ"])

    def test_a_person_with_no_works_never_shows_up(self):
        """`涼森みつ` 的名字也以「涼森」开头，但她名下一部片都没有。"""
        self.assertNotIn("涼森みつ", self.values("涼森", "performer"))

    def test_studios_and_series_have_their_own_groups(self):
        self.assertEqual(self.values("ラグジュ", "studio"), ["ラグジュTV"])
        self.assertEqual(self.values("ドキュ", "series"), ["ドキュメント"])

    def test_an_agency_counts_the_works_of_its_members(self):
        self.assertEqual(self.group("Capsule", "agency")[0]["n"], 3)

    def test_an_agency_reachable_only_by_its_former_name_still_completes(self):
        self.assertEqual(self.values("カプセル", "agency"), ["Capsule Agency"])

    def test_an_agency_whose_roster_has_no_works_never_shows_up(self):
        self.assertNotIn("Capsule Reserve", self.values("Capsule", "agency"))

    def test_a_tag_completes_like_any_other_identity(self):
        self.assertIn("足交", self.values("足交", "tag"))

    def test_a_tag_that_is_really_a_performer_name_stays_out(self):
        self.assertEqual(self.values("神雪", "tag"), [])
        self.assertEqual(self.values("神雪", "performer"), ["神雪"])

    def test_a_length_tag_is_a_filter_control_not_a_word(self):
        self.assertEqual(self.values("短片", "tag"), [])

    def test_a_tag_only_seen_in_the_trash_stays_out(self):
        self.assertEqual(self.values("足底", "tag"), [])

    def test_a_code_completes_to_a_work_that_can_be_opened(self):
        items = self.group("ABW", "asset")
        self.assertEqual(items[0]["value"], "ABW-123")
        self.assertEqual(items[0]["id"], 4)

    def test_a_work_in_the_trash_is_not_offered(self):
        self.assertNotIn("ABW-999", self.values("ABW", "asset"))

    def test_a_work_completes_by_its_release_title_too(self):
        self.assertEqual(self.values("潜入", "asset"), ["ABW-123"])

    def test_a_hit_in_the_file_name_ranks_last(self):
        """`old-ABW-clip.mp4` 里有别人的番号。它排在真的叫这个番号的那条之后。"""
        self.assertEqual(self.values("ABW", "asset"), ["ABW-123", "old-ABW-clip"])

    def test_a_file_name_loses_its_extension(self):
        """`.MOV` 是存储事实，不是这部片叫什么。"""
        self.assertEqual(self.values("IMG", "asset"), ["IMG_2757_682"])

    def test_an_empty_query_offers_nothing(self):
        """空输入下该出现的是搜索记录和推荐，不是补全。"""
        self.assertEqual(self.suggest("")["groups"], [])

    def test_groups_come_back_in_the_declared_order(self):
        order = [kind for kind, _ in SUGGEST_GROUPS]
        kinds = [group["kind"] for group in self.suggest("涼")["groups"]]
        self.assertEqual(kinds, sorted(kinds, key=order.index))

    def test_each_group_carries_its_own_label(self):
        labels = {group["kind"]: group["label"] for group in self.suggest("涼森")["groups"]}
        self.assertEqual(labels["performer"], "女优")

    def test_a_group_never_exceeds_the_asked_for_size(self):
        """六个标签以「足」开头，一组只给得下五个。"""
        self.assertEqual(len(self.group("足", "tag", limit=5)), 5)
        self.assertEqual(len(self.group("足", "tag", limit=2)), 2)

    def test_a_prefix_hit_outranks_a_hit_in_the_middle(self):
        """「足交」是前缀命中，其余几个是同一个字打头的同辈。"""
        self.assertEqual(self.values("足交", "tag")[0], "足交")

    def test_every_suggestion_finds_something_when_actually_searched(self):
        """补全与搜索同源的唯一验收方式：拿补出来的词去真的搜一次。

        逐条搜是这条测试的成本，也是它的意义——两侧判据漂开时，别的断言都还绿着。
        """
        for query in ("涼森", "凉森", "Remu", "ラグジュ", "ドキュ", "Capsule",
                      "カプセル", "足", "足交", "巨乳", "ABW", "潜入",
                      "MO", "mon", "IMG"):
            for group in self.suggest(query)["groups"]:
                for item in group["items"]:
                    with self.subTest(query=query, kind=group["kind"], value=item["value"]):
                        self.assertGreater(
                            self.total(item["value"]), 0,
                            f"补全给出 {item['value']}，搜它却是空的")

    def test_a_suggested_work_opens_the_row_it_points_at(self):
        for item in self.group("ABW", "asset"):
            self.assertEqual(rm_web.q_item(self.contract, item["id"])["id"], item["id"])


class ShortLatinQueryTests(LedgerFixture):
    """两个字母的拉丁输入比词首，不比子串。

    子串比出来的多半是别的词中间那两个字母：真实账本上「MO」会捞出 `kemonokai`、
    「Pr」会捞出 `chf3_prob4`，而用户在打的是 MOODYZ 和 Prestige。汉字和假名没有
    分词空格，那一侧仍按子串，否则「凉森」这种两字输入连自己都补不出来。
    """

    def test_a_two_letter_query_completes_a_name_that_starts_with_it(self):
        self.assertEqual(self.values("MO", "studio"), ["MOODYZ"])

    def test_a_two_letter_query_reaches_the_head_of_an_inner_word(self):
        self.assertEqual(self.values("MO", "agency"), ["SO MODEL AGENT"])

    def test_a_two_letter_query_skips_the_middle_of_a_word(self):
        self.assertEqual(self.values("MO", "creator"), [])

    def test_a_third_letter_brings_the_substring_match_back(self):
        self.assertEqual(self.values("mon", "creator"), ["kemonokai"])

    def test_an_extension_in_a_file_name_is_not_a_word_head(self):
        """`IMG_2757_682.MOV` 里的 `.MOV` 不该让这条片出现在「MO」的补全里。"""
        self.assertEqual(self.values("MO", "asset"), [])

    def test_two_han_characters_still_match_inside_a_name(self):
        self.assertEqual(self.values("乳系", "tag"), ["巨乳系"])

    def test_two_kana_still_match_inside_a_name(self):
        self.assertEqual(self.values("ュメ", "series"), ["ドキュメント"])


class ShortQueryReachesEveryKindTests(LedgerFixture):
    """搜索的两条分支必须覆盖同样的 kind。

    三字以上走 FTS，它索引的 `entities` 聚合作品名下的全部实体、不挑 kind；两字以内
    走 LIKE。两边认的 kind 不一样时，同一个标签写三个字搜得到、写两个字搜不到，
    用户看到的是搜索时灵时不灵，而补全会照样把那个词补出来。
    """

    def test_a_two_character_tag_query_finds_its_works(self):
        self.assertEqual(self.total("足交"), 2)

    def test_a_three_character_tag_query_finds_its_works(self):
        self.assertEqual(self.total("巨乳系"), 2)

    def test_both_branches_agree_on_the_same_tag(self):
        """`巨乳系` 三个字走 FTS，`巨乳` 两个字走 LIKE，命中的是同一批作品。"""
        self.assertEqual(self.total("巨乳"), self.total("巨乳系"))

    def test_a_two_character_series_query_finds_its_works(self):
        self.assertEqual(self.total("ドキ"), 1)

    def test_a_two_character_performer_query_still_works(self):
        self.assertEqual(self.total("凉森"), 3)


if __name__ == "__main__":
    unittest.main()
