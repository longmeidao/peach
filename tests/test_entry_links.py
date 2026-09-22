"""人物资料页那三枚外部入口：地址怎么拼，什么时候不出。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from peach import entry_links


def ref(provider: str, external_id: str, kind: str = "performer") -> dict:
    return {"provider": provider, "external_kind": kind, "external_id": external_id}


class EntryLinkAddressTests(unittest.TestCase):
    def test_three_sites_line_up_when_both_ids_are_known(self):
        rows = entry_links.build(entry_links.defaults(), "河合あすな",
                                 [ref("javdb", "QDvG"), ref("minnano-av", "155084")])
        self.assertEqual([row["site"] for row in rows], ["javdb", "minnano-av", "missav"])
        self.assertEqual(rows[0]["url"], "https://javdb.com/actors/QDvG?sort_type=4")
        self.assertEqual(rows[1]["url"], "https://www.minnano-av.com/actress155084.html")
        self.assertEqual([row["label"] for row in rows], ["JavDB", "minnano-av", "MISSAV"])

    def test_a_site_without_an_id_is_absent_instead_of_a_search_address(self):
        rows = entry_links.build(entry_links.defaults(), "深田えいみ", [])
        self.assertEqual([row["site"] for row in rows], ["missav"])
        self.assertNotIn("search", rows[0]["url"])

    def test_the_name_is_percent_encoded(self):
        rows = entry_links.build(entry_links.defaults(), "楪 カレン", [])
        self.assertEqual(
            rows[0]["url"],
            "https://missav.ws/dm42/cn/actresses/%E6%A5%AA%20%E3%82%AB%E3%83%AC%E3%83%B3")

    def test_ids_from_another_entity_kind_do_not_count(self):
        # 事务所那 55 条 minnano-av 引用记的是 `production`，不是这个人在站上的号。
        rows = entry_links.build(entry_links.defaults(), "七沢みあ",
                                 [ref("minnano-av", "110", kind="production")])
        self.assertEqual([row["site"] for row in rows], ["missav"])

    def test_a_closed_site_drops_out(self):
        settings = entry_links.defaults()
        settings["missav"]["enabled"] = False
        rows = entry_links.build(settings, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual([row["site"] for row in rows], ["javdb"])

    def test_a_custom_template_is_used_as_written(self):
        settings = entry_links.defaults()
        settings["javdb"]["template"] = "https://javdb.com/actors/{javdb_id}"
        rows = entry_links.build(settings, "七沢みあ", [ref("javdb", "NPD3")])
        self.assertEqual(rows[0]["url"], "https://javdb.com/actors/NPD3")


class EntryLinkSettingsFileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_an_absent_file_reads_as_three_sites_open(self):
        saved = entry_links.read(self.root)
        self.assertEqual(sorted(saved), ["javdb", "minnano-av", "missav"])
        self.assertTrue(all(row["enabled"] for row in saved.values()))

    def test_saving_round_trips_through_the_snapshot(self):
        entry_links.save(self.root, {"sites": {
            "javdb": {"enabled": False, "template": "https://javdb.com/actors/{javdb_id}"},
            "minnano-av": {"enabled": True,
                           "template": "https://www.minnano-av.com/actress{minnano_id}.html"},
            "missav": {"enabled": True, "template": "https://missav.ws/dm42/cn/actresses/{name}"},
        }})
        rows = {row["key"]: row for row in entry_links.snapshot(self.root)["sites"]}
        self.assertFalse(rows["javdb"]["enabled"])
        self.assertEqual(rows["javdb"]["template"], "https://javdb.com/actors/{javdb_id}")
        self.assertEqual(rows["javdb"]["default_template"],
                         "https://javdb.com/actors/{javdb_id}?sort_type=4")
        self.assertEqual(rows["missav"]["placeholder"], "name")

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
        body["sites"]["missav"]["template"] = "http://missav.ws/dm42/cn/actresses/{name}"
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
