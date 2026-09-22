"""番号发现源的契约层：拉取一轮、建壳、列表、已读与忽略（ADR-0042）。"""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from peach import feed_followup, feeds, web_feeds  # noqa: E402
from peach.http import HttpResponse  # noqa: E402
from peach.web_contract import WebContract  # noqa: E402
from peach.web_router import dispatch_api_get, dispatch_api_post  # noqa: E402
from support.ledger import fresh_ledger  # noqa: E402

#: 端到端那一趟读的是临时数据根里的这份文件：拉取只吃已下载的字节，
#: 字节从网络来还是从盘上来与解析、去重、建壳那几步无关。
SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>示例新作</title>
  <item>
    <title>SSIS-950 作品标题</title>
    <link>https://feeds.example.test/view/2</link>
    <guid>https://feeds.example.test/view/2</guid>
    <pubDate>Mon, 21 Sep 2026 03:00:00 +0000</pubDate>
  </item>
  <item>
    <title>HMN-071 另一部作品[有碼高清中文字幕]</title>
    <link>https://feeds.example.test/view/1</link>
    <guid>https://feeds.example.test/view/1</guid>
    <pubDate>Sun, 20 Sep 2026 03:00:00 +0000</pubDate>
  </item>
  <item>
    <title>合集 30 部打包</title>
    <link>https://feeds.example.test/view/0</link>
    <guid>https://feeds.example.test/view/0</guid>
    <pubDate>Sat, 19 Sep 2026 03:00:00 +0000</pubDate>
  </item>
</channel></rss>
"""


class FakeTransport:
    """按地址回一份事先备好的响应。记下每次请求，好核对条件请求头。"""

    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def __call__(self, request, timeout, max_bytes):
        self.requests.append(request)
        return self.responses[request.url]


class FeedWebTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db_path = fresh_ledger(self.temporary.name)
        self.contract = WebContract(self.db_path)
        self.addCleanup(self.contract.stop_background_jobs)
        # 后继在服务里由后台线程领走，在测试里那是一个和断言赛跑的线程：它可能在
        # assert 之后才写完，也可能在临时目录删掉之后才醒。这里关掉自动领取，
        # 要跑后继的用例自己 `drain()`。
        self.contract.followups.stop()
        self.url = "https://feeds.example.test/new.xml"
        sample = Path(self.temporary.name) / "feed-sample.xml"
        sample.write_text(SAMPLE, encoding="utf-8")
        self.transport = FakeTransport({self.url: HttpResponse(
            200, {"ETag": 'W/"abc"', "Content-Type": "application/xml"},
            sample.read_bytes(), self.url)})
        self._patched = web_feeds.fetch
        web_feeds.fetch = self._fetch
        self.addCleanup(lambda: setattr(web_feeds, "fetch", self._patched))
        # 建壳会派取资料后继，后继由契约自己的 runner 领走。不替掉问来源那一步的话，
        # 这个套件每跑一次就朝真实来源发一轮请求——番号是假的，配额是真的。
        self._collect = feed_followup.collect
        feed_followup.collect = lambda provider, code: (
            {"title": f"{code} 的标题", "studio": "示例厂牌",
             "release_date": "2026-09-20",
             "performers": [{"name": "深田えいみ"}]},
            "https://images.example.test/cover.jpg")
        self.addCleanup(lambda: setattr(feed_followup, "collect", self._collect))

    def _fetch(self, transport, url, *, etag=None, last_modified=None):
        # 真实路径上的 SSRF 闸门要做 DNS，这里替换掉的正是那一层；条件请求头仍原样传下去。
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        from peach.http import HttpRequest
        return transport(HttpRequest("GET", url, headers), 30.0, 1 << 21)

    def _add(self, **body):
        return dispatch_api_post(self.contract, "/api/feeds/source",
                                 {"action": "add", "url": self.url, "name": "示例源",
                                  **body})

    def _check(self):
        original = web_feeds._transport
        web_feeds._transport = lambda contract: self.transport
        try:
            return dispatch_api_post(self.contract, "/api/feeds/check", {"all": True})
        finally:
            web_feeds._transport = original

    def test_settings_snapshot_lists_the_source_and_its_kinds(self):
        self._add()
        snapshot = dispatch_api_get(self.contract, "/api/feeds", {})
        self.assertEqual(len(snapshot["sources"]), 1)
        self.assertEqual(snapshot["sources"][0]["name"], "示例源")
        self.assertTrue(snapshot["sources"][0]["enabled"])
        self.assertEqual([kind["value"] for kind in snapshot["kinds"]],
                         list(feeds.KINDS))

    def test_one_round_turns_a_local_feed_into_unfiled_new_releases(self):
        self._add()
        result = self._check()
        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["results"][0]["error"], None)
        self.assertEqual(result["added"], 2)
        # 后继由结果声明，调度端统一派（ADR-0040）。
        self.assertEqual([item["task_key"] for item in result["followups"]],
                         ["feed-scrape", "feed-scrape"])
        listing = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        self.assertEqual([item["code"] for item in listing["items"]],
                         ["SSIS-950", "HMN-071"])
        self.assertFalse(listing["items"][0]["read"])

    def test_the_second_round_uses_the_stored_validators_and_adds_nothing(self):
        self._add()
        self._check()
        self.transport.responses[self.url] = HttpResponse(304, {}, b"", self.url)
        result = self._check()
        self.assertTrue(result["results"][0]["not_modified"])
        self.assertEqual(self.transport.requests[-1].headers["If-None-Match"], 'W/"abc"')
        listing = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        self.assertEqual(len(listing["items"]), 2)

    def test_a_failing_source_reports_on_its_own_row_and_stays_scheduled(self):
        self._add()
        self.transport.responses[self.url] = HttpResponse(503, {}, b"", self.url)
        result = self._check()
        self.assertFalse(result["results"][0]["ok"])
        row = dispatch_api_get(self.contract, "/api/feeds", {})["sources"][0]
        self.assertEqual(row["last_error"], "来源回了 HTTP 503")
        self.assertIsNotNone(row["next_fetch_at"])

    def test_read_and_ignore_are_separate_and_idempotent(self):
        self._add()
        self._check()
        first = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})["items"][0]
        dispatch_api_post(self.contract, "/api/feeds/discovery",
                          {"action": "read", "ids": [first["id"]]})
        dispatch_api_post(self.contract, "/api/feeds/discovery",
                          {"action": "read", "ids": [first["id"]]})
        listing = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        self.assertTrue(listing["items"][0]["read"])
        self.assertFalse(listing["items"][0]["ignored"])

        dispatch_api_post(self.contract, "/api/feeds/discovery",
                          {"action": "ignore", "ids": [first["id"]]})
        active = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        self.assertEqual([item["code"] for item in active["items"]], ["HMN-071"])
        ignored = dispatch_api_get(self.contract, "/api/feeds/discoveries",
                                   {"state": "ignored"})
        self.assertEqual([item["code"] for item in ignored["items"]], ["SSIS-950"])

        dispatch_api_post(self.contract, "/api/feeds/discovery",
                          {"action": "unignore", "ids": [first["id"]]})
        back = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        # 取消忽略只恢复可见性，已读状态不跟着变。
        self.assertEqual([item["code"] for item in back["items"]],
                         ["SSIS-950", "HMN-071"])
        self.assertTrue(back["items"][0]["read"])

    def test_a_code_that_reaches_the_library_leaves_the_list(self):
        self._add()
        self._check()
        with self.contract.database.write_transaction() as connection:
            connection.execute(
                "INSERT INTO asset(location,path,name,medium,code) "
                "VALUES('R','R:\\\\media\\\\ssis950.mp4','ssis950.mp4','video','SSIS-950')")
        listing = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        self.assertEqual([item["code"] for item in listing["items"]], ["HMN-071"])

    def test_the_entity_filter_only_returns_that_person(self):
        with self.contract.database.write_transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES('performer','深田えいみ',peach_normalize('深田えいみ'),?,?)",
                (feeds.stamp(), feeds.stamp()))
            entity_id = int(cursor.lastrowid)
        self._add(entity_id=entity_id)
        self._check()
        mine = dispatch_api_get(self.contract, "/api/feeds/discoveries",
                                {"entity": entity_id})
        self.assertEqual(len(mine["items"]), 2)
        nobody = dispatch_api_get(self.contract, "/api/feeds/discoveries",
                                  {"entity": entity_id + 1})
        self.assertEqual(nobody["items"], [])

    def test_removing_a_source_keeps_the_new_releases_it_found(self):
        self._add()
        self._check()
        source_id = dispatch_api_get(self.contract, "/api/feeds", {})["sources"][0]["id"]
        dispatch_api_post(self.contract, "/api/feeds/source",
                          {"action": "remove", "id": source_id})
        listing = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})
        self.assertEqual(len(listing["items"]), 2)

    def _drain(self, expected):
        """等后继排上再跑掉它们。

        `w_feed_check` 在任务体收尾时就放行调用方，而声明的后继是任务包装那一层在
        之后派的（ADR-0040）。直接 `drain()` 会赶在入队之前，跑到零条。
        """
        deadline = time.monotonic() + 5.0
        done = 0
        while done < expected and time.monotonic() < deadline:
            done += self.contract.followups.drain()
        return done

    def test_the_scrape_followup_fills_the_shell_and_links_the_performer(self):
        with self.contract.database.write_transaction() as connection:
            connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES('performer','深田えいみ',peach_normalize('深田えいみ'),?,?)",
                (feeds.stamp(), feeds.stamp()))
        self._add()
        self._check()
        self.assertEqual(self._drain(2), 2)
        items = {row["code"]: row for row in dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {})["items"]}
        item = items["SSIS-950"]
        self.assertEqual(item["title"], "SSIS-950 的标题")
        self.assertEqual(item["studio"], "示例厂牌")
        self.assertEqual(item["performers"], "深田えいみ")
        # 壳只认已有的人，不新建实体；关联上了人物页那一块才看得到。
        self.assertEqual(len(dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {"entity": 1})["items"]), 2)

    def test_an_unknown_action_is_refused(self):
        with self.assertRaises(ValueError):
            dispatch_api_post(self.contract, "/api/feeds/discovery",
                              {"action": "delete", "ids": [1]})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
