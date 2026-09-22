"""人物资料页的外部入口：地址怎么拼、摆在哪个位置、什么时候不出。"""
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
    def test_each_site_lands_in_the_slot_it_belongs_to(self):
        rows = entry_links.build(entry_links.defaults(), "河合あすな",
                                 [ref("javdb", "QDvG"), ref("minnano-av", "155084")])
        self.assertEqual([row["site"] for row in rows],
                         ["minnano-av", "javdb", "missav"])
        # minnano-av 是一份资料页，排进上面那排链接；看片那两枚自己一行。
        self.assertEqual([row["slot"] for row in rows], ["pill", "mark", "mark"])
        self.assertEqual(rows[0]["url"], "https://www.minnano-av.com/actress155084.html")
        self.assertEqual(rows[1]["url"], "https://javdb.com/actors/QDvG")
        # 药丸上写站点自己的名字，取自 minnano-av 官网的 title。
        self.assertEqual([row["label"] for row in rows],
                         ["みんなのAV", "JavDB", "MISSAV"])
        # MISSAV 没有可用的图形标识，那一枚由前端按它站上的排版规则排字。
        self.assertEqual([row["mark"] for row in rows],
                         ["brand-minnano", "mark-javdb", ""])

    def test_two_pages_on_the_same_site_each_get_an_entry(self):
        """javdb 上同一位女优有两个演员页，两边挂的作品不同，都要能点进去。"""
        rows = entry_links.build(entry_links.defaults(), "释爱丽丝",
                                 [ref("javdb", "d45k9"), ref("javdb", "ZX5z7")],
                                 [alias("釈アリス", "avdb-actor-mapping@8e2d")])
        pages = [row for row in rows if row["site"] == "javdb"]
        self.assertEqual([row["label"] for row in pages], ["JavDB", "JavDB ②"])
        self.assertEqual([row["ordinal"] for row in pages], ["", "②"])
        self.assertEqual([row["url"] for row in pages],
                         ["https://javdb.com/actors/d45k9",
                          "https://javdb.com/actors/ZX5z7"])

    def test_a_site_without_an_id_is_absent_instead_of_a_search_address(self):
        rows = entry_links.build(entry_links.defaults(), "深田えいみ",
                                 [ref("r18dev", "1041521")])
        self.assertEqual([row["site"] for row in rows], ["missav"])
        self.assertNotIn("search", rows[0]["url"])

    def test_a_performer_outside_the_jav_directories_gets_no_watch_row(self):
        """`145cm色白お嬢様` 这类 FC2 个人摄创作者，账本 kind 也是 performer。

        JavDB 与 MISSAV 只收商业 AV 女优；本机 Stash 的 id 与 r18 的名字映射每个人都有，
        它们不是「别处收录过她」的证据，所以不能拿来开这一行。
        """
        rows = entry_links.build(entry_links.defaults(), "145cm色白お嬢様",
                                 [ref("stash", "912"),
                                  ref("r18", "145cm", kind="performer_name")])
        self.assertEqual(rows, [])

    def test_an_agency_roster_id_does_not_open_the_watch_row(self):
        """K-MIB 那类事务所站收的是所属艺人，不是 JAV 的作品目录。

        名册上有她，说明这家公司签了她；她拍的是不是商业 AV、JavDB 与 MISSAV 上有没有
        她的页面，这条引用一个字都没说。
        """
        rows = entry_links.build(entry_links.defaults(), "神木ほのか",
                                 [ref("kmib", "218")])
        self.assertEqual(rows, [])

    def test_missav_uses_the_japanese_stage_name(self):
        """规范名是中文译名时，MISSAV 那条按别名里的日文艺名拼。

        实测 `/cn/actresses/釈アリス` 返回 200，中文译名与纯平假名读音都是 404。
        """
        rows = entry_links.build(entry_links.defaults(), "释爱丽丝",
                                 [ref("r18dev", "1096544")], [
            alias("Alice Shaku", "avdb-actor-mapping@8e2d"),
            alias("しゃくありす", "r18:performer"),
            alias("釈アリス", "avdb-actor-mapping@8e2d"),
        ])
        self.assertEqual(
            rows[0]["url"],
            "https://missav.ws/cn/actresses/%E9%87%88%E3%82%A2%E3%83%AA%E3%82%B9")

    def test_a_reading_in_plain_hiragana_loses_to_the_written_stage_name(self):
        rows = entry_links.build(entry_links.defaults(), "天川空",
                                 [ref("r18dev", "1091104")], [
            alias("あまかわそら", "r18:performer"),
            alias("天川そら", "avdb-actor-mapping@8e2d"),
        ])
        self.assertTrue(rows[0]["url"].endswith("/%E5%A4%A9%E5%B7%9D%E3%81%9D%E3%82%89"))

    def test_a_stage_name_source_wins_among_writings_of_the_same_shape(self):
        rows = entry_links.build(entry_links.defaults(), "佐佐木纱希",
                                 [ref("r18dev", "1075533")], [
            alias("佐々木サキ", "stash:performer"),
            alias("佐々木さき", "avdb-actor-mapping@8e2d"),
        ])
        self.assertTrue(rows[0]["url"].endswith(
            "/%E4%BD%90%E3%80%85%E6%9C%A8%E3%81%95%E3%81%8D"))

    def test_the_canonical_name_stands_in_when_no_alias_reads_as_japanese(self):
        rows = entry_links.build(entry_links.defaults(), "楪 カレン",
                                 [ref("r18dev", "1058712")],
                                 [alias("Karen Yuzuriha", "r18:performer")])
        self.assertEqual(
            rows[0]["url"],
            "https://missav.ws/cn/actresses/%E6%A5%AA%20%E3%82%AB%E3%83%AC%E3%83%B3")

    def test_ids_from_another_entity_kind_do_not_count(self):
        # 事务所那 55 条 minnano-av 引用记的是 `production`，不是这个人在站上的号；
        # 它既拼不出 minnano 的资料页，也不足以说明这个人是 JAV 女优。
        rows = entry_links.build(entry_links.defaults(), "七沢みあ",
                                 [ref("minnano-av", "110", kind="production")])
        self.assertEqual(rows, [])

    def test_a_mirror_domain_replaces_only_the_host(self):
        settings = entry_links.defaults()
        settings["javdb"]["host"] = "javdb521.com"
        rows = entry_links.build(settings, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual(rows[0]["url"], "https://javdb521.com/actors/NPD3")

    def test_a_broken_domain_falls_back_to_the_default_site(self):
        """手改坏的域名拼出来是个不存在的主机名，那比退回默认站更难看出问题。"""
        settings = entry_links.defaults()
        settings["javdb"]["host"] = "javdb.com/actors"
        rows = entry_links.build(settings, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual(rows[0]["url"], "https://javdb.com/actors/NPD3")

    def test_an_empty_domain_means_the_default_one(self):
        """配置页那个框默认就是空的：留空是「没换过」，不是「没有地址」。"""
        rows = entry_links.build({"javdb": {"host": ""}}, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual(rows[0]["url"], "https://javdb.com/actors/NPD3")


class EntryLinkSettingsFileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def body(self, **changed: dict) -> dict:
        """配置页提交的形状：能换域名的那几站各一行，值就是框里写的那串。"""
        sites = {site.key: {"host": ""} for site in entry_links.SITES if site.mirrored}
        sites.update(changed)
        return {"sites": sites}

    def test_an_absent_file_reads_as_no_domain_changed(self):
        """配置页只管能换域名的那两站；みんなのAV 只此一家，不在这份设置里。"""
        saved = entry_links.read(self.root)
        self.assertEqual(sorted(saved), ["javdb", "missav"])
        self.assertTrue(all(row["host"] == "" for row in saved.values()))

    def test_saving_round_trips_through_the_snapshot(self):
        entry_links.save(self.root, self.body(javdb={"host": "javdb521.com"}))
        rows = {row["key"]: row for row in entry_links.snapshot(self.root)["sites"]}
        self.assertEqual(sorted(rows), ["javdb", "missav"])
        self.assertEqual(rows["javdb"]["host"], "javdb521.com")
        self.assertEqual(rows["javdb"]["default_host"], "javdb.com")
        self.assertEqual(rows["javdb"]["label"], "JavDB")
        # 没动过的那一站留空：框里显示的是占位符，不是一串要人去认的默认值。
        self.assertEqual(rows["missav"]["host"], "")
        self.assertEqual(rows["missav"]["default_host"], "missav.ws")

    def test_a_pasted_address_is_trimmed_down_to_its_domain(self):
        """镜像地址多半是整条复制过来的，前缀与末尾的斜杠不值得弹一条错误。"""
        entry_links.save(self.root, self.body(missav={"host": "https://missav.ai/"}))
        self.assertEqual(entry_links.read(self.root)["missav"]["host"], "missav.ai")

    def test_an_address_with_a_path_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            entry_links.save(self.root, self.body(
                javdb={"host": "javdb.com/actors/{javdb_id}"}))
        self.assertIn("只写域名本身", str(caught.exception))

    def test_clearing_the_box_goes_back_to_the_default_domain(self):
        entry_links.save(self.root, self.body(missav={"host": "missav.ai"}))
        entry_links.save(self.root, self.body(missav={"host": "  "}))
        self.assertEqual(entry_links.read(self.root)["missav"]["host"], "")

    def test_a_hand_broken_file_falls_back_instead_of_emptying_the_row(self):
        (self.root / entry_links.FILENAME).write_text(
            json.dumps({"sites": {"javdb": {"host": "not a domain"}}}), encoding="utf-8")
        self.assertEqual(entry_links.read(self.root)["javdb"]["host"], "")


if __name__ == "__main__":
    unittest.main()
