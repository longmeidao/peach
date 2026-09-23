"""番号发现源的契约层：拉取一轮、建壳、列表、已读与忽略（ADR-0042）。"""
from __future__ import annotations

import io
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from peach import feed_followup, feeds, web_feeds, web_settings  # noqa: E402
from peach.http import HttpResponse  # noqa: E402
from peach.web_contract import WebContract  # noqa: E402
from peach.web_router import dispatch_api_get, dispatch_api_post  # noqa: E402
from support.ledger import fresh_ledger  # noqa: E402

#: 端到端那一趟读的是临时数据根里的这份文件：拉取只吃已下载的字节，
#: 字节从网络来还是从盘上来与解析、去重、建壳那几步无关。
SAMPLE = """
<a href="/v/Ab2" class="box" title="x"><div class="video-title"><strong>SSIS-950</strong>
 作品标题</div><div class="meta">
 2026-09-21</div></a>
<a href="/v/Ab1" class="box" title="x"><div class="video-title"><strong>HMN-071</strong>
 另一部作品</div><div class="meta">
 2026-09-20</div></a>
<a href="/v/Ab0" class="box" title="x"><div class="video-title"><strong></strong>
 合集 30 部打包</div><div class="meta">
 2026-09-19</div></a>
"""


class FakeTransport:
    """按地址回一份事先备好的响应。记下每次请求，好核对条件请求头。"""

    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def __call__(self, request, timeout, max_bytes):
        self.requests.append(request)
        return self.responses[request.url]


class FeedWebFixture(unittest.TestCase):
    """临时账本、本地 feed 字节和替掉的取资料一步。不带用例，两个套件共用。"""

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
        self.url = "https://javdb.com/actors/Smp1"
        sample = Path(self.temporary.name) / "feed-sample.html"
        sample.write_text(SAMPLE, encoding="utf-8")
        self.transport = FakeTransport({self.url: HttpResponse(
            200, {"ETag": 'W/"abc"', "Content-Type": "text/html"},
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
        # 封面装进临时封面目录；取图那一步同样替掉，换成一张现画的横版封套。
        self.contract.cover_root = Path(self.temporary.name) / "covers"
        self.cover_misses: set[str] = set()
        self.cover_unreachable: set[str] = set()
        self.cover_urls: dict[str, str | None] = {}
        self._fetch_cover = feed_followup.fetch_cover
        feed_followup.fetch_cover = self._fake_cover
        self.addCleanup(lambda: setattr(feed_followup, "fetch_cover", self._fetch_cover))

    def _fake_cover(self, contract, code, cover_url=None):
        self.cover_urls[code] = cover_url
        if code in self.cover_misses:
            raise RuntimeError("官方渠道没有这个番号的封面")
        if code in self.cover_unreachable:
            from peach.jav_cover_fetch import HOSTS_UNREACHABLE, CoverConnectError
            raise CoverConnectError(HOSTS_UNREACHABLE)
        from PIL import Image
        image = Image.new("RGB", (800, 538), (40, 40, 40))
        image.paste((200, 120, 150), (420, 0, 800, 538))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue(), (800, 538), {"code": code, "source": "test"}

    def _fetch(self, transport, url, *, etag=None, last_modified=None):
        # 真实路径上的 SSRF 闸门要做 DNS，这里替换掉的正是那一层；条件请求头仍原样传下去。
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        from peach.http import HttpRequest
        return transport(HttpRequest("GET", url, headers), 30.0, 1 << 21)

    def _add(self, entity_id=None):
        with self.contract.database.write_transaction() as connection:
            return feeds.add_source(connection, url=self.url, name="示例源",
                                    entity_id=entity_id)

    def _check(self, **body):
        original = web_feeds._transport
        web_feeds._transport = lambda contract: self.transport
        try:
            return dispatch_api_post(self.contract, "/api/feeds/check", {"all": True, **body})
        finally:
            web_feeds._transport = original


class FeedWebTest(FeedWebFixture):
    def test_settings_snapshot_lists_the_source(self):
        self._add()
        snapshot = dispatch_api_get(self.contract, "/api/feeds", {})
        self.assertEqual(len(snapshot["sources"]), 1)
        self.assertEqual(snapshot["sources"][0]["name"], "示例源")
        self.assertEqual(snapshot["sources"][0]["kind_label"], "JavDB 演员页")
        self.assertTrue(snapshot["sources"][0]["enabled"])

    def test_the_source_endpoint_takes_no_address_from_the_page(self):
        # 订阅只从人物页进，地址由服务端现拼（ADR-0047）；页面送来的地址一律不收。
        with self.assertRaises(ValueError):
            dispatch_api_post(self.contract, "/api/feeds/source",
                              {"action": "add", "url": "https://example.test/rss"})
        self.assertEqual(dispatch_api_get(self.contract, "/api/feeds", {})["sources"], [])

    def test_one_round_turns_a_local_feed_into_unfiled_new_releases(self):
        self._add()
        result = self._check()
        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["results"][0]["error"], None)
        self.assertEqual(result["added"], 2)
        # 后继由结果声明，调度端统一派（ADR-0040）；同一轮发现的合成一条。
        self.assertEqual([(item["task_key"], item["key"]) for item in result["followups"]],
                         [("feed-scrape", "feed-scrape:SSIS-950,HMN-071")])
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

    def _compilation(self, performers: str) -> None:
        self._add()
        self._check()
        self._drain(1)
        with self.contract.database.write_transaction() as connection:
            connection.execute("UPDATE feed_discovery SET title='8時間 BEST',performers=?,"
                               "scraped_at=NULL WHERE code='SSIS-950'", (performers,))

    def _listed(self) -> list[str]:
        return [item["code"] for item in
                dispatch_api_get(self.contract, "/api/feeds/discoveries", {})["items"]]

    def _backlog(self) -> list[str]:
        hidden = web_settings.hidden_compilations(self.contract.database)
        with self.contract.database.read_connection() as connection:
            return feed_followup.backlog(connection, self.contract.cover_root, hidden=hidden)

    def test_a_group_compilation_is_neither_listed_counted_nor_rescheduled(self):
        self._compilation("波多野結衣、篠田ゆう")
        listing = dispatch_api_get(self.contract, "/api/feeds/discoveries", {"limit": 1})
        # 分页按筛过的条数算：合集排在前面，要一条也还是拿到下一部，不是空页。
        self.assertEqual([item["code"] for item in listing["items"]], ["HMN-071"])
        self.assertFalse(listing["more"])
        self.assertEqual(dispatch_api_get(self.contract, "/api/feeds", {})["unread"], 1)
        self.assertEqual(self._backlog(), [])

    def test_the_two_switches_each_decide_their_own_kind(self):
        self._compilation("深田えいみ")
        # 单人合集默认照列，也照样补资料与封面。
        self.assertCountEqual(self._listed(), ["SSIS-950", "HMN-071"])
        self.assertEqual(self._backlog(), ["SSIS-950"])
        dispatch_api_post(self.contract, "/api/settings", {"feedHideSoloCompilations": True})
        self.assertEqual(self._listed(), ["HMN-071"])
        self.assertEqual(dispatch_api_get(self.contract, "/api/feeds", {})["unread"], 1)
        self.assertEqual(self._backlog(), [])
        # 换成大合集：默认收起；关掉大合集那个开关就回来，单人那个开关不管它。
        with self.contract.database.write_transaction() as connection:
            connection.execute("UPDATE feed_discovery SET performers='波多野結衣、篠田ゆう'"
                               " WHERE code='SSIS-950'")
        self.assertEqual(self._listed(), ["HMN-071"])
        dispatch_api_post(self.contract, "/api/settings", {"feedHideGroupCompilations": False})
        settings = dispatch_api_get(self.contract, "/api/settings", {})
        self.assertEqual((settings["feedHideGroupCompilations"],
                          settings["feedHideSoloCompilations"]), (False, True))
        self.assertCountEqual(self._listed(), ["SSIS-950", "HMN-071"])
        self.assertEqual(self._backlog(), ["SSIS-950"])

    def test_a_highlight_excerpt_is_hidden_by_studio_until_its_switch_is_off(self):
        self._compilation("篠田ゆう")
        with self.contract.database.write_transaction() as connection:
            connection.execute("UPDATE feed_discovery SET title='愛する妻が…',studio='ハイライト'"
                               " WHERE code='SSIS-950'")
        self.assertEqual(self._listed(), ["HMN-071"])
        self.assertEqual(self._backlog(), [])
        dispatch_api_post(self.contract, "/api/settings", {"feedHideExcerpts": False})
        self.assertCountEqual(self._listed(), ["SSIS-950", "HMN-071"])
        self.assertEqual(self._backlog(), ["SSIS-950"])

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

    def test_the_shape_list_names_whoever_still_has_a_listed_new_release(self):
        with self.contract.database.write_transaction() as connection:
            entity_id = int(connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES('performer','深田えいみ',peach_normalize('深田えいみ'),?,?)",
                (feeds.stamp(), feeds.stamp())).lastrowid)
            connection.execute(
                "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source)"
                " VALUES(?,'Eimi Fukada',peach_normalize('Eimi Fukada'),'test')", (entity_id,))
        def rows():
            return [entity for entity in dispatch_api_get(
                self.contract, "/api/entity/shapes", {})["entities"] if "feed" in entity["parts"]]

        self.assertEqual(rows(), [])
        self._add(entity_id=entity_id)
        self._check()
        self.assertEqual(rows(), [{"id": entity_id, "kind": "performer",
                                   "names": ["深田えいみ", "Eimi Fukada"], "parts": ["feed"]}])
        # 那几部都忽略掉，她的页面上就没有那一行了，名单跟着不再有她。
        ids = [item["id"] for item in dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {"entity": entity_id})["items"]]
        dispatch_api_post(self.contract, "/api/feeds/discovery", {"action": "ignore", "ids": ids})
        self.assertEqual(rows(), [])

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
        self.assertEqual(self._drain(1), 1)
        items = {row["code"]: row for row in dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {})["items"]}
        item = items["SSIS-950"]
        self.assertEqual(item["title"], "SSIS-950 的标题")
        self.assertEqual(item["studio"], "示例厂牌")
        self.assertEqual(item["performers"], "深田えいみ")
        # 壳只认已有的人，不新建实体；关联上了人物页那一块才看得到。
        self.assertEqual(len(dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {"entity": 1})["items"]), 2)

    def test_the_card_names_the_studio_the_way_the_library_does(self):
        """来源给的是日文厂牌名，卡片上写账本里那个厂牌的规范名；壳上仍存原文。"""
        with self.contract.database.write_transaction() as connection:
            connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES('studio','Sample Studio',peach_normalize('Sample Studio'),?,?)",
                (feeds.stamp(), feeds.stamp()))
            connection.execute(
                "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source)"
                " VALUES(last_insert_rowid(),'示例厂牌',peach_normalize('示例厂牌'),'test')")
        self._add()
        self._check()
        self._drain(1)
        items = dispatch_api_get(self.contract, "/api/feeds/discoveries", {})["items"]
        self.assertEqual({item["studio"] for item in items}, {"Sample Studio"})
        with self.contract.database.read_connection() as connection:
            self.assertEqual({row[0] for row in connection.execute(
                "SELECT studio FROM feed_discovery")}, {"示例厂牌"})

    def test_one_batch_installs_each_cover_with_the_sidecars_the_cards_frame_by(self):
        self.cover_misses.add("HMN-071")
        self._add()
        self._check()
        self.assertEqual(self._drain(1), 1)
        [run] = self.contract.task_runs.query(task_key=feed_followup.TASK_KEY)
        self.assertEqual(run.result_summary, {"total": 2, "ok": 2, "miss": 0, "covers": 1})
        covers = self.contract.cover_root
        self.assertTrue((covers / "SSIS-950.jpg").is_file())
        self.assertTrue((covers / "SSIS-950.poster.json").is_file())
        self.contract.cache_bust()
        items = {row["code"]: row for row in dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {})["items"]}
        # 装上的那部带着正封框，页面按资产卡同一套取景；没装上的只有来源地址。
        self.assertTrue(items["SSIS-950"]["has_cover"])
        self.assertEqual(items["SSIS-950"]["poster_box"]["px"], [800, 538])
        self.assertFalse(items["HMN-071"]["has_cover"])
        self.assertIsNone(items["HMN-071"]["poster_box"])

    def test_covers_cut_off_at_the_connection_are_counted_for_the_new_release_row(self):
        """连不上图片主机的几部单独记数，列表把最近一轮的数带给页面去提示换线路；
        官方没图的那几部不算进去。"""
        self.assertEqual(dispatch_api_get(self.contract, "/api/feeds/discoveries", {})["cover_network"], 0)
        self.cover_unreachable.add("SSIS-950")
        self.cover_misses.add("HMN-071")
        self._add()
        self._check()
        self.assertEqual(self._drain(1), 1)
        [run] = self.contract.task_runs.query(task_key=feed_followup.TASK_KEY)
        self.assertEqual(run.result_summary,
                         {"total": 2, "ok": 2, "miss": 0, "covers": 0, "cover_network": 1})
        self.assertEqual(dispatch_api_get(self.contract, "/api/feeds/discoveries", {})["cover_network"], 1)

    def test_the_cover_step_gets_the_address_the_scrape_just_wrote(self):
        """封面地址是同一轮取资料才写上壳的，取图那一步拿到的得是它，不是空的。"""
        self._add()
        self._check()
        self._drain(1)
        self.assertEqual(self.cover_urls, {
            "SSIS-950": "https://images.example.test/cover.jpg",
            "HMN-071": "https://images.example.test/cover.jpg"})

    def test_a_shell_still_missing_its_cover_rejoins_a_batch_after_the_retry_window(self):
        self.cover_misses.add("HMN-071")
        self._add()
        self._check()
        self._drain(1)
        self.transport.responses[self.url] = HttpResponse(304, {}, b"", self.url)
        # 定时那一轮：刚试过的不再排；已经有封面、资料也齐的那部永远不再排。
        self.assertEqual(self._check(automatic=True)["followups"], [])
        earlier = feeds.stamp(datetime.now(timezone.utc)
                              - feed_followup.RETRY_AFTER - timedelta(minutes=1))
        with self.contract.database.write_transaction() as connection:
            connection.execute("UPDATE feed_discovery SET scraped_at=?", (earlier,))
        self.assertEqual([item["key"] for item in self._check(automatic=True)["followups"]],
                         ["feed-scrape:HMN-071"])
        # 人说了不想看的，不再替它花配额。
        first = {row["code"]: row for row in dispatch_api_get(
            self.contract, "/api/feeds/discoveries", {})["items"]}["HMN-071"]
        dispatch_api_post(self.contract, "/api/feeds/discovery",
                          {"action": "ignore", "ids": [first["id"]]})
        self.assertEqual(self._check()["followups"], [])

    def test_a_manual_check_retries_a_missing_cover_without_waiting_out_the_window(self):
        """人手点的那一轮不等重试窗口：点「检查」就是要现在取。"""
        self.cover_misses.add("HMN-071")
        self._add()
        self._check()
        self._drain(1)
        self.transport.responses[self.url] = HttpResponse(304, {}, b"", self.url)
        self.assertEqual([item["key"] for item in self._check()["followups"]],
                         ["feed-scrape:HMN-071"])

    def test_an_unknown_action_is_refused(self):
        with self.assertRaises(ValueError):
            dispatch_api_post(self.contract, "/api/feeds/discovery",
                              {"action": "delete", "ids": [1]})


#: JavDB 演员页里两部作品，形状照 `test_feeds.JAVDB_ACTOR` 那份抓回来的 HTML。
JAVDB_PAGE = """
<a href="/v/5nr8mp" class="box" title="x"><div class="video-title"><strong>PBD-528</strong>
 気高きお姉さん達</div><div class="meta">
 2026-10-20</div></a>
<a href="/v/RkPb5z" class="box" title="x"><div class="video-title"><strong>BBSS-106</strong>
 別の作品</div><div class="meta">
 2026-10-13</div></a>
"""

#: 隐退的人：主页最近只剩大合集，「單體作品」页才翻得到她自己的正片。
RETIRED_PAGE = """
<a href="/v/Rt0001" class="box" title="x"><div class="video-title"><strong>JKSR-736</strong>
 デカパイ奥様 16人4時間</div><div class="meta">
 2026-05-23</div></a>
"""
SOLO_PAGE = """
<a href="/v/Rt0001" class="box" title="x"><div class="video-title"><strong>JKSR-736</strong>
 デカパイ奥様 16人4時間</div><div class="meta">
 2026-05-23</div></a>
<a href="/v/Rt0002" class="box" title="x"><div class="video-title"><strong>MCSR-191</strong>
 欲情不倫妻</div><div class="meta">
 2025-07-19</div></a>
<a href="/v/Rt0003" class="box" title="x"><div class="video-title"><strong>CLO-350</strong>
 今晩、何回シテくれるか</div><div class="meta">
 2025-06-06</div></a>
"""


class PerformerFeedSwitchTest(FeedWebFixture):
    """人物页「订阅新作」开关：地址由服务端按 JavDB 演员页拼，页面只送开和关。"""

    def setUp(self):
        super().setUp()
        self.page = "https://javdb.com/actors/pRMq"
        self.transport.responses[self.page] = HttpResponse(
            200, {"Content-Type": "text/html"}, JAVDB_PAGE.encode("utf-8"), self.page)
        original = web_feeds._transport
        web_feeds._transport = lambda contract: self.transport
        self.addCleanup(lambda: setattr(web_feeds, "_transport", original))
        self.performer = self._performer("凉森れむ", ["pRMq"])

    def _performer(self, name, javdb_ids):
        with self.contract.database.write_transaction() as connection:
            entity_id = int(connection.execute(
                "INSERT INTO entity(kind,canonical_name,normalized_name,created_at,updated_at)"
                " VALUES('performer',?,peach_normalize(?),?,?)",
                (name, name, feeds.stamp(), feeds.stamp())).lastrowid)
            for external_id in javdb_ids:
                connection.execute(
                    "INSERT INTO entity_external_ref(entity_id,provider,external_kind,"
                    "external_id) VALUES(?,'javdb','performer',?)", (entity_id, external_id))
        return entity_id

    def _switch(self, enabled, entity_id=None):
        return dispatch_api_post(self.contract, "/api/feeds/source", {
            "action": "follow", "entity_id": entity_id or self.performer,
            "enabled": enabled})

    def _settled(self):
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            state = self.contract.feed_job.snapshot() or {}
            if state.get("status") not in ("running", None):
                return state
            time.sleep(0.02)
        self.fail("订阅拉取没有在 5 秒内跑完")

    def _sources(self):
        return dispatch_api_get(self.contract, "/api/feeds", {})["sources"]

    def test_switching_on_subscribes_her_javdb_page_and_fetches_it_now(self):
        result = self._switch(True)
        self.assertTrue(result["following"])
        [source] = self._sources()
        self.assertEqual((source["kind"], source["url"], source["entity_id"]),
                         (feeds.KIND_JAVDB_ACTOR, self.page, self.performer))
        # 名字不另存，跟着人物走。
        self.assertEqual(source["name"], "凉森れむ")
        self.assertEqual(self._settled()["added"], 2)
        mine = dispatch_api_get(self.contract, "/api/feeds/discoveries",
                                {"entity": self.performer})
        self.assertEqual([item["code"] for item in mine["items"]], ["PBD-528", "BBSS-106"])

    def test_a_page_of_only_compilations_is_backfilled_from_her_solo_works(self):
        retired = self._performer("篠田ゆう", ["WE4e"])
        page = "https://javdb.com/actors/WE4e"
        self.transport.responses[page] = HttpResponse(
            200, {"Content-Type": "text/html"}, RETIRED_PAGE.encode("utf-8"), page)
        self.transport.responses[page + "?t=s"] = HttpResponse(
            200, {"Content-Type": "text/html"}, SOLO_PAGE.encode("utf-8"), page + "?t=s")
        self._switch(True, retired)
        state = self._settled()
        [report] = state["results"]
        self.assertTrue(report["ok"])
        self.assertEqual(report["backfilled"], 2)
        mine = dispatch_api_get(self.contract, "/api/feeds/discoveries", {"entity": retired})
        self.assertEqual([item["code"] for item in mine["items"]], ["MCSR-191", "CLO-350"])

    def test_a_missing_solo_page_leaves_the_round_itself_successful(self):
        self._switch(True)
        [report] = self._settled()["results"]
        self.assertTrue(report["ok"])
        self.assertIn("backfill_error", report)
        self.assertIsNone(report["error"])

    def test_switching_off_pauses_and_switching_on_again_reuses_the_source(self):
        self._switch(True)
        self._settled()
        self._switch(False)
        [paused] = self._sources()
        self.assertFalse(paused["enabled"])
        self._switch(True)
        self._settled()
        [again] = self._sources()
        self.assertEqual(again["id"], paused["id"])
        self.assertTrue(again["enabled"])

    def test_a_listed_page_without_a_person_is_adopted_instead_of_duplicated(self):
        with self.contract.database.write_transaction() as connection:
            feeds.add_source(connection, url=self.page)
        self._switch(True)
        self._settled()
        [source] = self._sources()
        self.assertEqual(source["entity_id"], self.performer)

    def test_every_javdb_page_of_hers_gets_its_own_source(self):
        twice = self._performer("释爱丽丝", ["d45k9", "ZX5z7"])
        result = self._switch(True, twice)
        self._settled()
        self.assertEqual(len(result["sources"]), 2)
        self.assertEqual(sorted(source["url"] for source in self._sources()),
                         ["https://javdb.com/actors/ZX5z7", "https://javdb.com/actors/d45k9"])

    def test_the_profile_carries_the_switch_only_when_she_has_a_javdb_page(self):
        profile = dispatch_api_get(self.contract, "/api/entity",
                                   {"kind": "performer", "name": "凉森れむ"})
        self.assertEqual(profile["feed"], {"following": False})
        self._switch(True)
        self._settled()
        profile = dispatch_api_get(self.contract, "/api/entity",
                                   {"kind": "performer", "name": "凉森れむ"})
        self.assertEqual(profile["feed"], {"following": True})
        self._performer("無名の人", [])
        bare = dispatch_api_get(self.contract, "/api/entity",
                                {"kind": "performer", "name": "無名の人"})
        self.assertNotIn("feed", bare)

    def test_a_performer_without_a_javdb_page_is_refused(self):
        bare = self._performer("無名の人", [])
        with self.assertRaises(ValueError):
            self._switch(True, bare)
        self.assertEqual(self._sources(), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
