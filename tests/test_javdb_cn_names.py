"""javdb 资料页取中文名：现名与旧名必须分开，中文写法只认一个。

配错一位就是把另一个人的名字写进真相字段。这里守的是「什么才算证据」。
"""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from peach import javdb

REPO = Path(__file__).resolve().parents[1]

#: 资料页顶部的真实结构（2026-09-04 实测）。现名一栏中日并列，紧随的是旧艺名。
PAGE = """
<div class="column section-title">
  <h2 class="title is-4">
    <span class="actor-section-name">{current}</span>
    <br />
    <span class="section-meta">{former}</span>
    <br>
    <span class="section-meta">324 部影片</span>
  </h2>
</div>
<a id="button-collect-actor" href="/actors/{actor}/collect"></a>
"""


def page(current: str, former: str = "", actor: str = "RJM8") -> str:
    return PAGE.format(current=current, former=former, actor=actor)


def load_script(name: str):
    """按文件路径加载脚本。

    要先登记进 `sys.modules` 再执行：`localize_performer_names` 里有 dataclass，
    而 `dataclasses` 会去 `sys.modules[cls.__module__]` 取模块字典，没登记就是
    `'NoneType' object has no attribute '__dict__'`——报错指向 dataclass，
    真正的原因在这一行。
    """
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_module():
    return load_script("harvest_javdb_cn_names")


class ParseTests(unittest.TestCase):
    def test_the_current_name_and_the_former_names_are_two_different_lists(self):
        """`JULIA` 那页的旧名里有 `京香じゅりあ`。混成一串就分不出这是不是她的中文名。"""
        html = page("JULIA", "京香じゅりあ")
        self.assertEqual(javdb.current_names(html), ["JULIA"])
        self.assertEqual(javdb.former_names(html), ["京香じゅりあ"])

    def test_the_film_count_is_not_a_name(self):
        self.assertNotIn("324 部影片", javdb.former_names(page("深田詠美, 深田えいみ")))

    def test_both_writings_of_the_current_name_come_back_in_order(self):
        self.assertEqual(javdb.current_names(page("深田詠美, 深田えいみ")),
                         ["深田詠美", "深田えいみ"])

    def test_the_actor_id_is_the_page_identity(self):
        self.assertEqual(javdb.actor_id(page("深田詠美, 深田えいみ", actor="Ng03")), "Ng03")

    def test_a_search_result_that_names_nobody_we_want_is_not_a_hit(self):
        html = ('<div class="box actor-box"><a href="/actors/AAA" title="別人, べつじん">'
                '</a></div><div class="box actor-box">'
                '<a href="/actors/BBB" title="深田詠美, 深田えいみ"></a></div>')
        self.assertEqual(javdb.search_hits(html, {"深田えいみ"}), ["/actors/BBB"])

    def test_a_wider_key_can_be_supplied_for_matching(self):
        """账本写 `宫`、站上写 `宮`，字形差别不该让人搜不到自己。"""
        html = ('<div class="box actor-box"><a href="/actors/AAA" title="宮本櫻, 宮本さくら">'
                '</a></div>')
        self.assertEqual(javdb.search_hits(html, {"宫本さくら"}), [])
        self.assertEqual(
            javdb.search_hits(html, {"宫本さくら"}, lambda name: name.replace("宮", "宫")),
            ["/actors/AAA"])

    def test_two_pages_for_one_name_both_come_back(self):
        """同一个名字在站上真有两位时，取第一个是默默替用户挑了一位。"""
        html = ('<div class="box actor-box"><a href="/actors/AAA" title="あおい"></a></div>'
                '<div class="box actor-box"><a href="/actors/BBB" title="あおい"></a></div>')
        self.assertEqual(javdb.search_hits(html, {"あおい"}), ["/actors/AAA", "/actors/BBB"])


class JudgeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.record = {"entity_id": 1, "name": "深田えいみ", "assets": 6,
                       "chain": ["深田えいみ", "天海こころ"]}

    def judge(self, current, former=""):
        return self.module.judge(self.record, page(current, former), "https://javdb.com/x")

    def test_a_name_written_both_ways_on_one_page_is_the_evidence(self):
        row = self.judge("深田詠美, 深田えいみ")
        self.assertEqual(row["verdict"], "ok")
        self.assertEqual(row["zh_tw"], "深田詠美")
        self.assertEqual(row["jp"], "深田えいみ")

    def test_a_ledger_name_found_only_among_former_names_is_left_to_a_human(self):
        """站上已经改了名。用哪个当规范名是人要决定的事，不是这一步该定的。"""
        row = self.judge("JULIA", "深田えいみ")
        self.assertEqual(row["verdict"], "旧名")
        self.assertIn("JULIA", row["evidence"])

    def test_a_page_with_only_a_japanese_name_yields_nothing(self):
        """`長谷川るい` 那页只有日文写法。没有就是没有，不转写。"""
        self.record.update(name="長谷川るい", chain=["長谷川るい"])
        row = self.judge("長谷川るい")
        self.assertEqual(row["verdict"], "同形（站上只有日文名）")
        self.assertEqual(row["zh_tw"], "")

    def test_two_chinese_writings_in_one_field_are_ambiguous(self):
        self.record.update(name="田中レモン", chain=["田中レモン", "楓カレン"])
        row = self.judge("田中檸檬, 田中レモン, 楓花戀")
        self.assertEqual(row["verdict"], "多义")

    def test_two_different_stage_names_in_the_current_field_are_not_a_pair(self):
        """`一之瀨亞美莉, 美空あやか` 是两个艺名。姓对不上，中文那个不是这位的名字。"""
        self.record.update(name="美空あやか", chain=["美空あやか"])
        row = self.judge("一之瀨亞美莉, 美空あやか", "一ノ瀬アメリ")
        self.assertEqual(row["verdict"], "不同名（两栏姓氏对不上）")
        self.assertEqual(row["zh_cn" if "zh_cn" in row else "zh_tw"], "")

    def test_a_shared_single_character_is_not_a_shared_surname(self):
        """`美空` 与 `亞美莉` 都有 `美`。按字取交集会把配错的那一对放过去。"""
        self.assertFalse(self.module.same_person("一之瀨亞美莉", "美空あやか"))
        self.assertTrue(self.module.same_person("深田詠美", "深田えいみ"))

    def test_a_kana_only_japanese_name_has_no_surname_to_compare(self):
        """`あべみかこ` 没有汉字可比。无从判不等于判否。"""
        self.assertTrue(self.module.same_person("安部未華子", "あべみかこ"))

    def test_a_glyph_difference_is_not_a_name_difference(self):
        """`宫本さくら` 与 `宮本さくら` 是一个人，`宮` 与 `宫` 只是字形。"""
        self.record.update(name="宫本さくら", chain=["宫本さくら"])
        self.assertEqual(self.judge("宮本櫻, 宮本さくら")["verdict"], "ok")

    def test_a_page_matched_only_through_an_alias_is_left_to_a_human(self):
        """账本规范名不在现名栏：站上写的是另一个艺名，换不换规范名是人的决定。"""
        self.record.update(name="おっぱい隊長", chain=["おっぱい隊長", "夢見るぅ"])
        row = self.judge("夢見露, 夢見るぅ")
        self.assertEqual(row["verdict"], "改艺名（现名栏是另一个艺名）")
        self.assertIn("おっぱい隊長", row["evidence"])

    def test_a_latin_stage_name_is_not_a_chinese_name(self):
        self.record["name"] = "京香じゅりあ"
        self.record["chain"] = ["京香じゅりあ", "JULIA"]
        row = self.judge("JULIA, 京香じゅりあ")
        self.assertEqual(row["verdict"], "同形（站上只有日文名）")


class SimplifyTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_the_traditional_writing_is_kept_next_to_the_simplified_one(self):
        """复核件要看得出转了什么：只留简体的话，转错了没人能发现。"""
        rows = self.module.localize(
            [{"verdict": "ok", "zh_tw": "永瀨未萌"}, {"verdict": "旧名", "zh_tw": ""}])
        self.assertEqual(rows[0]["zh_cn"], "永濑未萌")
        self.assertEqual(rows[0]["zh_tw"], "永瀨未萌")
        self.assertEqual(rows[1]["zh_cn"], "")


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.con = sqlite3.connect(Path(self.tmp.name).resolve() / "ledger.db")
        self.con.executescript(
            "CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT);"
            "CREATE TABLE entity_alias(entity_id INTEGER, alias TEXT);"
            "CREATE TABLE asset_entity(asset_id INTEGER, entity_id INTEGER, source TEXT);")
        self.con.executemany(
            "INSERT INTO entity(id,kind,canonical_name) VALUES(?,'performer',?)",
            [(1, "深田えいみ"), (2, "三上悠亚"), (3, "MattieDoll"), (4, "河合あすな")])
        self.con.executemany(
            "INSERT INTO asset_entity(asset_id,entity_id,source) VALUES(?,?,?)",
            [(10, 1, "r18:performer"), (11, 2, "r18:performer"),
             (12, 3, "legacy:asset"), (13, 4, "javbus:performer")])
        self.con.execute("INSERT INTO entity_alias VALUES(1,'天海こころ')")
        self.con.commit()

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_only_kana_names_backed_by_release_metadata_are_targets(self):
        """已经是中文的不用查；账号型 performer 不是女优，不翻译。"""
        found = {row["name"] for row in self.module.targets(self.con)}
        self.assertEqual(found, {"深田えいみ", "河合あすな"})

    def test_the_aliases_ride_along_as_search_terms(self):
        """按规范名搜不到时，旧名往往搜得到——名字链是入口，不是装饰。"""
        chain = next(row["chain"] for row in self.module.targets(self.con)
                     if row["name"] == "深田えいみ")
        self.assertEqual(chain, ["深田えいみ", "天海こころ"])


class MappingCsvTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("localize_performer_names")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name).resolve() / "mapping.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *rows):
        from peach.review_csv import write_rows
        write_rows(self.path, load_module().FIELDS, list(rows), fill_missing=True)

    def test_only_the_rows_judged_ok_become_mappings(self):
        self.write({"jp": "深田えいみ", "zh_cn": "深田咏美", "verdict": "ok", "actor_id": "A1"},
                   {"jp": "長谷川るい", "zh_cn": "", "verdict": "同形（站上只有日文名）"})
        mappings = self.module.read_mapping_csv(self.path)
        self.assertEqual([m.jp for m in mappings], ["深田えいみ"])

    def test_the_page_id_becomes_the_provenance_key(self):
        """回溯「这个中文名是谁写的」时，要指得回具体那一页。"""
        self.write({"jp": "深田えいみ", "zh_cn": "深田咏美", "verdict": "ok", "actor_id": "A1"})
        self.assertEqual(self.module.read_mapping_csv(self.path)[0].key, "javdb:A1")

    def test_the_index_points_back_into_the_returned_list(self):
        """`collect` 拿 `index` 当下标回查。跳过的行也算数就会指到别人身上。"""
        self.write({"jp": "跳过", "zh_cn": "", "verdict": "同形（站上只有日文名）"},
                   {"jp": "深田えいみ", "zh_cn": "深田咏美", "verdict": "ok", "actor_id": "A1"})
        mappings = self.module.read_mapping_csv(self.path)
        self.assertEqual(mappings[mappings[0].index].jp, "深田えいみ")

    def test_a_japanese_glyph_left_by_the_traditional_conversion_is_normalized(self):
        """opencc 转的是繁简，不管日本字形：`滝` 中文写 `泷`。字形不需要外部证据。"""
        self.write({"jp": "滝田あゆ", "zh_cn": "滝田亚由", "verdict": "ok", "actor_id": "A2"})
        self.assertEqual(self.module.read_mapping_csv(self.path)[0].zh_cn, "泷田亚由")


if __name__ == "__main__":
    unittest.main()
