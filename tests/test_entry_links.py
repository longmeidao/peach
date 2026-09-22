"""人物资料页的外部入口：地址怎么拼、摆在哪个栏位、什么时候不出。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from peach import entry_links


def ref(provider: str, external_id: str, kind: str = "performer") -> dict:
    return {"provider": provider, "external_kind": kind, "external_id": external_id}


def alias(written: str, source: str = "r18:performer") -> dict:
    return {"alias": written, "source": source}


class EntryLinkAddressTests(unittest.TestCase):
    def test_every_site_lines_up_in_its_own_section(self):
        rows = entry_links.build(entry_links.defaults(), "河合あすな",
                                 [ref("javdb", "QDvG"), ref("minnano-av", "155084")])
        self.assertEqual([row["site"] for row in rows],
                         ["minnano-av", "javdb-home", "missav", "javdb"])
        self.assertEqual([row["section"] for row in rows],
                         ["演员主页", "演员主页", "在线观看", "在线片库"])
        # 作品列表另起一行，前三枚同一行。
        self.assertEqual([row["line"] for row in rows], [1, 1, 1, 2])
        self.assertEqual(rows[0]["url"], "https://www.minnano-av.com/actress155084.html")
        self.assertEqual(rows[1]["url"], "https://javdb.com/actors/QDvG")
        self.assertEqual(rows[3]["url"], "https://javdb.com/actors/QDvG?sort_type=4")
        self.assertEqual([row["label"] for row in rows],
                         ["minnano-av", "JavDB", "MISSAV", "JavDB"])
        self.assertEqual([row["icon"] for row in rows],
                         ["brand-minnano", "brand-javdb", "brand-missav", "brand-javdb"])

    def test_two_pages_on_the_same_site_each_get_an_entry(self):
        """javdb 上同一位女优有两个演员页，两边挂的作品不同，都要能点进去。"""
        rows = entry_links.build(entry_links.defaults(), "释爱丽丝",
                                 [ref("javdb", "d45k9"), ref("javdb", "ZX5z7")],
                                 [alias("釈アリス", "avdb-actor-mapping@8e2d")])
        home = [row for row in rows if row["site"] == "javdb-home"]
        self.assertEqual([row["label"] for row in home], ["JavDB", "JavDB ②"])
        self.assertEqual([row["url"] for row in home],
                         ["https://javdb.com/actors/d45k9", "https://javdb.com/actors/ZX5z7"])
        works = [row for row in rows if row["site"] == "javdb"]
        self.assertEqual([row["label"] for row in works], ["JavDB", "JavDB ②"])

    def test_a_site_without_an_id_is_absent_instead_of_a_search_address(self):
        rows = entry_links.build(entry_links.defaults(), "深田えいみ", [])
        self.assertEqual([row["site"] for row in rows], ["missav"])
        self.assertNotIn("search", rows[0]["url"])

    def test_missav_uses_the_japanese_stage_name(self):
        """规范名是中文译名时，MISSAV 那条按别名里的日文艺名拼。

        实测 `/cn/actresses/釈アリス` 返回 200，中文译名与纯平假名读音都是 404。
        """
        rows = entry_links.build(entry_links.defaults(), "释爱丽丝", [], [
            alias("Alice Shaku", "avdb-actor-mapping@8e2d"),
            alias("しゃくありす", "r18:performer"),
            alias("釈アリス", "avdb-actor-mapping@8e2d"),
        ])
        self.assertEqual(
            rows[0]["url"],
            "https://missav.ws/cn/actresses/%E9%87%88%E3%82%A2%E3%83%AA%E3%82%B9")

    def test_a_reading_in_plain_hiragana_loses_to_the_written_stage_name(self):
        rows = entry_links.build(entry_links.defaults(), "天川空", [], [
            alias("あまかわそら", "r18:performer"),
            alias("天川そら", "avdb-actor-mapping@8e2d"),
        ])
        self.assertTrue(rows[0]["url"].endswith("/%E5%A4%A9%E5%B7%9D%E3%81%9D%E3%82%89"))

    def test_a_stage_name_source_wins_among_writings_of_the_same_shape(self):
        rows = entry_links.build(entry_links.defaults(), "佐佐木纱希", [], [
            alias("佐々木サキ", "stash:performer"),
            alias("佐々木さき", "avdb-actor-mapping@8e2d"),
        ])
        self.assertTrue(rows[0]["url"].endswith(
            "/%E4%BD%90%E3%80%85%E6%9C%A8%E3%81%95%E3%81%8D"))

    def test_the_canonical_name_stands_in_when_no_alias_reads_as_japanese(self):
        rows = entry_links.build(entry_links.defaults(), "楪 カレン", [],
                                 [alias("Karen Yuzuriha", "r18:performer")])
        self.assertEqual(
            rows[0]["url"],
            "https://missav.ws/cn/actresses/%E6%A5%AA%20%E3%82%AB%E3%83%AC%E3%83%B3")

    def test_ids_from_another_entity_kind_do_not_count(self):
        # 事务所那 55 条 minnano-av 引用记的是 `production`，不是这个人在站上的号。
        rows = entry_links.build(entry_links.defaults(), "七沢みあ",
                                 [ref("minnano-av", "110", kind="production")])
        self.assertEqual([row["site"] for row in rows], ["missav"])

    def test_a_closed_site_drops_out(self):
        settings = entry_links.defaults()
        settings["missav"]["enabled"] = False
        settings["javdb-home"]["enabled"] = False
        rows = entry_links.build(settings, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual([row["site"] for row in rows], ["javdb"])

    def test_a_custom_template_is_used_as_written(self):
        settings = entry_links.defaults()
        settings["javdb"]["template"] = "https://javdb.com/actors/{javdb_id}/reviews"
        rows = entry_links.build(settings, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual(rows[-1]["url"], "https://javdb.com/actors/NPD3/reviews")


class EntryLinkSettingsFileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_an_absent_file_reads_as_every_site_open(self):
        saved = entry_links.read(self.root)
        self.assertEqual(sorted(saved), ["javdb", "javdb-home", "minnano-av", "missav"])
        self.assertTrue(all(row["enabled"] for row in saved.values()))

    def test_saving_round_trips_through_the_snapshot(self):
        body = {"sites": {site.key: {"enabled": True, "template": site.template}
                          for site in entry_links.SITES}}
        body["sites"]["javdb"] = {"enabled": False,
                                  "template": "https://javdb.com/actors/{javdb_id}"}
        entry_links.save(self.root, body)
        rows = {row["key"]: row for row in entry_links.snapshot(self.root)["sites"]}
        self.assertFalse(rows["javdb"]["enabled"])
        self.assertEqual(rows["javdb"]["template"], "https://javdb.com/actors/{javdb_id}")
        self.assertEqual(rows["javdb"]["default_template"],
                         "https://javdb.com/actors/{javdb_id}?sort_type=4")
        self.assertEqual(rows["missav"]["placeholder"], "name")
        # 同一个站在两个栏位各有一枚，配置页那一行得自己说清是哪一枚。
        self.assertEqual(rows["javdb"]["label"], "JavDB 作品列表")
        self.assertEqual(rows["javdb-home"]["label"], "JavDB 演员主页")

    def test_a_template_without_its_placeholder_is_refused(self):
        body = {"sites": {site.key: {"enabled": True, "template": site.template}
                          for site in entry_links.SITES}}
        body["sites"]["javdb"]["template"] = "https://javdb.com/actors/"
        with self.assertRaises(ValueError) as caught:
            entry_links.save(self.root, body)
        self.assertIn("{javdb_id}", str(caught.exception))

    def test_a_plain_http_template_is_refused(self):
        body = {"sites": {site.key: {"enabled": True, "template": site.template}
                          for site in entry_links.SITES}}
        body["sites"]["missav"]["template"] = "http://missav.ws/cn/actresses/{name}"
        with self.assertRaises(ValueError) as caught:
            entry_links.save(self.root, body)
        self.assertIn("https://", str(caught.exception))

    def test_a_hand_broken_file_falls_back_instead_of_emptying_the_row(self):
        (self.root / entry_links.FILENAME).write_text(
            json.dumps({"sites": {"javdb": {"template": "not a url"}}}), encoding="utf-8")
        saved = entry_links.read(self.root)
        self.assertEqual(saved["javdb"]["template"],
                         "https://javdb.com/actors/{javdb_id}?sort_type=4")
        self.assertTrue(saved["javdb"]["enabled"])


if __name__ == "__main__":
    unittest.main()
