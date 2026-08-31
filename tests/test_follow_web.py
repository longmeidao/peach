"""追更的 Web 契约与页面源测试。

契约层测试用临时数据库；页面源测试守的是「追更表面」这一个语义契约，
不是某个文件——判据同 `tests/test_web_ui.py`。
"""
import json
import os
import re
import sqlite3
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from peach import web_follow
from peach.follow import FollowHistoryEnd
from peach.follow import FollowSourceError
from peach.follow_discovery import Discovery, ExternalSearch
from peach.follow_secrets import CredentialError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.follow_store import FollowStore
from peach.migrations import discover
from peach.web_contract import WebContract, dispatch_api_get, dispatch_api_post
from peach.web_follow import _credential_store


ROOT = Path(__file__).resolve().parents[1]
MOMENT = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)


class FollowContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.db = self.root / "ledger.db"
        connection = sqlite3.connect(self.db)
        for migration in discover(ROOT / "migrations"):
            connection.executescript(migration.sql)
        connection.commit()
        connection.close()
        self.contract = WebContract(
            self.db, follow_sources_root=self.root / "sources",
            follow_secrets_root=self.root / "secrets",
            follow_shared_root=self.root / "shared")

    def _seed(self, candidates=None, provider="rule34video", ref="lazyprocrastinator",
              semantics="work"):
        candidates = candidates if candidates is not None else (
            FollowCandidate(provider=provider, external_id="4542713",
                            title="Fiona - Paizuri", duration=20.0,
                            url="https://rule34video.com/video/4542713/x/",
                            thumb_url="https://rule34video.com/t/4542713.jpg",
                            extra={"published_precision": "approximate"},
                            published_at="2026-08-18T00:00:00Z"),
            FollowCandidate(provider=provider, external_id="4542721",
                            title="Fiona - Paizuri (Nude)",
                            url="https://rule34video.com/video/4542721/x/"),
        )
        with self.contract.database.write_transaction() as connection:
            store = FollowStore(lambda: connection,
                                sources_root=self.contract.follow_sources_root)
            source_id = store.register(
                provider=provider, ref=ref, label="LazyProcrastinator",
                url=f"https://{provider}.test/{ref}", semantics=semantics, moment=MOMENT)
            store.record(source_id, SourceFetch(
                provider=provider, ref=ref, request_url=f"https://{provider}.test/{ref}",
                semantics=semantics, candidates=candidates, raw_body=b"<html/>"),
                moment=MOMENT)
        return source_id

    def _get(self, path="/api/follow", **args):
        return dispatch_api_get(self.contract, path, args)

    def _post(self, path, body):
        return dispatch_api_post(self.contract, path, body)

    def test_paging_back_advances_the_cursor_without_touching_the_etag(self):
        """往回抓推进游标，但**绝不覆盖 etag**。

        etag 和 last_modified 是第一页的条件请求凭据。拿第 3 页的 etag 覆盖掉，
        下次常规检查就会拿它去问第一页、站点回 304，新的更新从此再也进不来——
        一个「往回看历史」的功能会安静地把追更本身弄坏。
        """
        source_id = self._seed()

        def record(etag, page):
            with self.contract.database.write_transaction() as connection:
                FollowStore(lambda: connection,
                            sources_root=self.contract.follow_sources_root).record(
                    source_id, SourceFetch(
                        provider="rule34video", ref="lazyprocrastinator",
                        request_url="https://rule34video.test/x", semantics="work",
                        # 证据文件名取自「时间戳 + 正文摘要」。这个测试里时间戳是
                        # 固定的 MOMENT，正文再一样就会撞名，所以让正文随 etag 变。
                        candidates=(), etag=etag,
                        raw_body=f"<html>{etag}{page}</html>".encode()),
                    moment=MOMENT, page=page)

        def state():
            with self.contract.database.read_connection() as connection:
                return dict(connection.execute(
                    "SELECT etag, backfill_page FROM follow_source WHERE id=?",
                    (source_id,)).fetchone())

        record('"first-page"', 0)
        self.assertEqual(state()["etag"], '"first-page"')

        record('"third-page"', 2)
        self.assertEqual(state()["etag"], '"first-page"', "往回抓不该动第一页的 etag")
        self.assertEqual(state()["backfill_page"], 2)

        # 常规检查照常更新 etag，而且不会让游标倒退。
        record('"newer"', 0)
        self.assertEqual(state()["etag"], '"newer"')
        self.assertEqual(state()["backfill_page"], 2)

    def test_the_check_endpoint_pages_back_only_when_asked(self):
        """常规检查永远只看第一页，往回抓必须是显式的。"""
        self._seed()
        pages = []

        class _Recorder:
            provider, semantics = "rule34video", "work"

            def fetch(self, ref, *, etag=None, last_modified=None, page=0):
                pages.append(page)
                return SourceFetch(provider="rule34video", ref=ref,
                                   request_url="https://rule34video.test/x",
                                   semantics="work", candidates=(), raw_body=b"<html/>")

        original = web_follow.build_connector
        web_follow.build_connector = lambda provider, credential=None: _Recorder()
        self.addCleanup(setattr, web_follow, "build_connector", original)

        self._post("/api/follow/check", {})
        self._post("/api/follow/check", {"older": True})
        self._post("/api/follow/check", {"older": True})
        # 第一次常规检查 → 0；两次往回抓 → 1、2，游标一次只走一页。
        self.assertEqual(pages, [0, 1, 2])

    def test_paging_back_skips_sources_without_a_history_endpoint(self):
        self._seed(provider="f95zone", ref="50685", semantics="release")
        factory = mock.Mock()
        with mock.patch.object(web_follow, "build_connector", factory):
            result = self._post("/api/follow/check", {"older": True})
        self.assertEqual(result["checked"], 0)
        factory.assert_not_called()
        source = next(row for row in self._get()["sources"]
                      if row["provider"] == "f95zone")
        self.assertFalse(source["can_backfill"])

    def test_history_end_is_a_neutral_success_and_does_not_advance_cursor(self):
        source_id = self._seed()

        class _Ended:
            provider, semantics = "rule34video", "work"

            def fetch(self, ref, *, etag=None, last_modified=None, page=0):
                raise FollowHistoryEnd("没有更多历史内容")

        with mock.patch.object(web_follow, "build_connector", return_value=_Ended()):
            result = self._post("/api/follow/check", {"older": True})
        row = result["results"][0]
        self.assertTrue(row["ok"])
        self.assertTrue(row["exhausted"])
        self.assertEqual(row["message"], "没有更多历史内容")
        with self.contract.database.read_connection() as connection:
            state = dict(connection.execute(
                "SELECT backfill_page,last_status,last_error FROM follow_source WHERE id=?",
                (source_id,)).fetchone())
        self.assertEqual(state["backfill_page"], 0)
        self.assertEqual(state["last_status"], "not_modified")
        self.assertIsNone(state["last_error"])

    def test_feed_groups_variants_under_one_card(self):
        self._seed()
        payload = self._get()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["groups"]), 1)
        group = payload["groups"][0]
        self.assertEqual(group["primary"]["title"], "Fiona - Paizuri")
        self.assertEqual([v["variant_label"] for v in group["variants"]], ["nude"])
        self.assertEqual(group["providers"], ["rule34video"])
        self.assertFalse(group["has_wip"])

    def test_feed_reports_approximate_publication_precision(self):
        self._seed()
        primary = self._get()["groups"][0]["primary"]
        self.assertEqual(primary["published_precision"], "approximate")

    def test_feed_can_restore_one_exact_item_outside_the_recent_limit(self):
        self._seed()
        item_id = self._get()["groups"][0]["primary"]["id"]
        payload = self._get(item=str(item_id), limit="1")
        self.assertEqual(payload["groups"][0]["primary"]["id"], item_id)
        self.assertEqual(len(payload["groups"][0]["variants"]), 1)

    def test_feed_never_exposes_the_raw_media_url(self):
        # 界面只需要知道有没有媒体；直链是来源层的事，不进公共 JSON。
        self._seed()
        payload = json.dumps(self._get(), ensure_ascii=False)
        self.assertNotIn("media_url", payload)
        self.assertIn('"has_media"', payload)

    def test_feed_unescapes_html_entities_in_tags_and_titles(self):
        """关注出口的标签与标题统一反转义。

        rule34.xxx 的 dapi 曾把 `miqo&#039;te` 这类 HTML 转义形态直接写进
        metadata，页面转义后用户看到的就是 `&#039;` 字面量，同一个标签还会和
        反转义后的写法分裂成两个身份。出口归一是幂等的：旧行不修账本也能正常
        显示与筛选，新入库由连接器反转义，不再产生脏数据。
        """
        self._seed(candidates=(
            FollowCandidate(provider="rule34xxx", external_id="18534401",
                            title="barnabas&#039; mother · biting lip",
                            url="https://rule34.xxx/index.php?page=post&s=view&id=18534401",
                            extra={"tags": "miqo&#039;te y&#039;shtola barnabas&#039;_mother"}),
        ), provider="rule34xxx", ref="final_fantasy")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["tags"], ["miqo'te", "y'shtola", "barnabas'_mother"])
        self.assertEqual(item["tag_types"],
                         {"miqo'te": "general", "y'shtola": "general",
                          "barnabas'_mother": "general"})
        self.assertEqual(item["title"], "barnabas' mother · biting lip")

    def test_external_file_pages_are_exposed_without_leaking_raw_media_urls(self):
        self._seed(candidates=(FollowCandidate(
            provider="f95zone", external_id="21435166", title="InitialA Collection",
            url="https://f95zone.to/threads/160190/post-21435166",
            media_url="https://gofile.io/d/verified",
            extra={"links": ["https://gofile.io/d/verified",
                             "https://pixeldrain.com/l/also-verified",
                             "https://gofile.io.evil.example/no"]},
        ),), provider="f95zone", ref="160190", semantics="release")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["resource_urls"], [
            "https://gofile.io/d/verified",
            "https://pixeldrain.com/l/also-verified",
        ])
        self.assertNotIn("media_url", item)

    def test_legacy_f95_image_attachments_are_projected_without_a_ledger_write(self):
        self._seed(candidates=(FollowCandidate(
            provider="f95zone", external_id="21435167", title="Image set",
            url="https://f95zone.to/threads/160190/post-21435167",
            media_url="https://pixeldrain.com/l/verified",
            thumb_url="https://attachments.f95zone.to/2026/08/one.jpg",
            extra={"links": ["https://pixeldrain.com/l/verified"],
                   "attachments": [
                       "https://attachments.f95zone.to/2026/08/one.jpg",
                       "https://attachments.f95zone.to/2026/08/two.png",
                   ]},
        ),), provider="f95zone", ref="160190", semantics="release")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual([media["media_kind"] for media in item["media_items"]],
                         ["image", "image"])
        self.assertEqual(item["media_kind"], "image")
        self.assertTrue(item["playable"])
        self.assertTrue(all("url" not in media for media in item["media_items"]))

    def test_media_collections_expose_only_safe_display_fields_and_indices(self):
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="12228983", title="Poll Results",
            url="https://lazyprocrast.fanbox.cc/posts/12228983",
            extra={"media_items": [
                {"id": "one", "name": "one.mp4", "media_kind": "video",
                 "url": "https://store1.gofile.io/download/one.mp4",
                 "thumb_url": "https://store1.gofile.io/one.jpg",
                 "resource_provider": "gofile"},
                {"id": "two", "name": "two.jpg", "media_kind": "image",
                 "url": "https://store1.gofile.io/download/two.jpg",
                 "resource_provider": "gofile"},
            ]},
        ),), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        self.assertTrue(item["playable"])
        self.assertEqual([media["index"] for media in item["media_items"]], [0, 1])
        self.assertEqual([media["media_kind"] for media in item["media_items"]],
                         ["video", "image"])
        self.assertEqual(item["media_items"][0]["name"], "one.mp4")
        self.assertEqual(item["media_items"][0]["media_type"], "video/mp4")
        self.assertIsNone(item["media_items"][1]["media_type"])
        self.assertNotIn("url", item["media_items"][0])
        self.assertNotIn("store1.gofile.io/download", json.dumps(item))

    def test_f95_discussion_and_inline_memes_are_hidden(self):
        self._seed(candidates=(
            FollowCandidate(
                provider="f95zone", external_id="discussion", title="Thread",
                url="https://f95zone.to/threads/50685/post-discussion",
                summary="Thanks for sharing"),
            FollowCandidate(
                provider="f95zone", external_id="attachment", title="Thread",
                url="https://f95zone.to/threads/50685/post-attachment",
                thumb_url="https://attachments.f95zone.to/preview.png",
                extra={"attachment_count": 1,
                       "attachments": ["https://attachments.f95zone.to/preview.png"]}),
            FollowCandidate(
                provider="f95zone", external_id="download", title="Thread",
                url="https://f95zone.to/threads/50685/post-download",
                extra={"attachment_count": 1,
                       "attachments": ["https://attachments.f95zone.to/archive.zip"]}),
        ), provider="f95zone", ref="50685", semantics="release")
        payload = self._get()
        items = [group["primary"] for group in payload["groups"]]
        self.assertEqual([item["external_id"] for item in items], ["download"])
        self.assertEqual(payload["counts"]["new"], 1)

    def test_old_archive_images_get_a_thumbnail_without_rewriting_the_ledger(self):
        self._seed(candidates=(FollowCandidate(
            provider="kemono", external_id="1", title="Image release",
            url="https://kemono.cr/fanbox/user/1/post/1",
            media_url="https://kemono.cr/ab/cd/image.jpg",
        ),), provider="kemono", ref="fanbox/1")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(
            item["thumb_url"], "https://kemono.cr/thumbnail/data/ab/cd/image.jpg")
        self.assertEqual(item["media_kind"], "image")
        self.assertTrue(item["playable"])

    def test_old_rule34xxx_previews_are_upgraded_without_rewriting_the_ledger(self):
        self._seed(candidates=(FollowCandidate(
            provider="rule34xxx", external_id="1", title="Remote video",
            url="https://rule34.xxx/index.php?page=post&s=view&id=1",
            media_url="https://api-cdn-mp4.rule34.xxx/images/42/"
                      "0123456789abcdef0123456789abcdef.mp4",
            thumb_url="https://api-cdn.rule34.xxx/thumbnails/42/"
                      "thumbnail_0123456789abcdef0123456789abcdef.jpg",
            extra={"media_kind": "video"},
        ),), provider="rule34xxx", ref="artist")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["media_type"], "video/mp4")
        self.assertEqual(
            item["thumb_url"],
            "https://api-cdn.rule34.xxx/images/42/"
            "0123456789abcdef0123456789abcdef.jpg")

    def test_paheal_cards_use_same_origin_clear_cover_routes(self):
        self._seed(candidates=(
            FollowCandidate(
                provider="rule34paheal", external_id="video", title="Video",
                media_url="https://r34i.paheal-cdn.net/ab/cd/video",
                thumb_url="https://r34t.paheal.net/ab/cd/video",
                extra={"media_kind": "video"}),
            FollowCandidate(
                provider="rule34paheal", external_id="image", title="Image",
                media_url="https://r34i.paheal-cdn.net/ab/cd/image",
                thumb_url="https://r34t.paheal.net/ab/cd/image",
                extra={"media_kind": "image"}),
        ), provider="rule34paheal", ref="artist")
        items = {group["primary"]["external_id"]: group["primary"]
                 for group in self._get()["groups"]}
        self.assertEqual(items["video"]["thumb_url"],
                         f"/follow-cover?id={items['video']['id']}")
        self.assertEqual(items["image"]["thumb_url"],
                         f"/follow-stream?id={items['image']['id']}")
        self.assertNotIn("r34i.paheal-cdn.net", json.dumps(items))

    def test_named_large_collection_is_hidden_but_not_deleted(self):
        self._seed(candidates=(FollowCandidate(
            provider="rule34video", external_id="4533145", title="Large collection",
            url="https://rule34video.com/video/4533145/x/",
            media_url="https://rule34video.com/get_file/x.mp4/",
        ),))
        payload = self._get()
        self.assertEqual(payload["groups"], [])
        self.assertEqual(payload["counts"]["new"], 0)
        with self.contract.database.read_connection() as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM follow_item WHERE external_id='4533145'"
            ).fetchone()[0], 1)

    def test_feed_filters_by_status_and_reports_counts(self):
        self._seed()
        first = self._get()["groups"][0]["primary"]["id"]
        self._post("/api/follow/status", {"item": first, "to": "ignored"})
        self.assertEqual(self._get(status="new")["counts"],
                         {"new": 1, "seen": 0, "saved": 0, "ignored": 1})
        self.assertEqual(len(self._get(status="ignored")["groups"]), 1)

    def test_feed_status_accepts_a_multi_selection(self):
        self._seed()
        group = self._get()["groups"][0]
        items = [group["primary"]["id"], group["variants"][0]["id"]]
        result = self._post("/api/follow/status", {"items": items, "to": "seen"})
        self.assertEqual(result["items"], items)
        self.assertEqual(self._get(status="seen")["counts"]["seen"], 2)

    def test_direct_online_play_counts_without_saving_an_asset(self):
        self._seed()
        item = self._get()["groups"][0]["primary"]["id"]

        started = self._post("/api/follow/play", {"item": item})
        activity = self._post("/api/follow/activity", {
            "item": item, "position": 12, "duration": 20, "delta": 10,
        })

        self.assertEqual(started["status"], "seen")
        self.assertEqual(activity["play_seconds"], 10)
        self.assertEqual(activity["max_reached"], 0.6)
        with self.contract.database.read_connection() as connection:
            row = dict(connection.execute(
                "SELECT play_count,play_seconds,max_reached FROM follow_playback "
                "WHERE follow_item_id=?", (item,),
            ).fetchone())
        self.assertEqual(row, {"play_count": 1, "play_seconds": 10.0,
                               "max_reached": 0.6})

        stats = self._get("/api/stats")
        self.assertEqual(stats["consumption"]["online_played"], 1)
        self.assertEqual(stats["consumption"]["played"], 1)
        self.assertEqual(stats["consumption"]["online_play_seconds"], 10)
        self.assertEqual(stats["recent"][0]["kind"], "online")

    def test_feed_ignores_a_nonsense_limit_instead_of_failing(self):
        self._seed()
        self.assertEqual(len(self._get(limit="nope")["groups"]), 1)

    def test_counts_are_whole_library_while_groups_are_one_page(self):
        """计数是全库口径，列表只有一页——界面并排显示这两个数时看起来像自相矛盾。

        用户实测：状态条写着「未看 2292」，下面视频 220 + 图片 11 只有 231。
        两个数都对，差的是口径，所以响应必须带上 has_more 让界面能说清楚、能续取。
        """
        self._seed()
        page = self._get(limit=1)
        self.assertEqual(page["limit"], 1)
        self.assertEqual(page["offset"], 0)
        self.assertTrue(page["has_more"], "还有条目没取，has_more 必须为真")
        # counts 不随分页缩小：它统计的是整库。
        self.assertGreater(sum(page["counts"].values()), len(page["groups"]))

    def test_the_last_page_reports_no_more(self):
        self._seed()
        full = self._get()
        self.assertFalse(full["has_more"], "一页装得下时不该说还有下一页")

    def test_paging_does_not_repeat_or_skip_items(self):
        """翻页靠 OFFSET，排序必须绝对稳定，否则两页之间会重复或漏掉条目。"""
        self._seed()
        everything = [item["id"] for group in self._get()["groups"]
                      for item in [group["primary"], *group["variants"]]]
        seen, offset = [], 0
        while True:
            page = self._get(limit=1, offset=offset)
            for group in page["groups"]:
                seen.extend(item["id"] for item in [group["primary"], *group["variants"]])
            if not page["has_more"]:
                break
            offset += 1
            self.assertLess(offset, 50, "分页没有收敛")
        self.assertEqual(sorted(set(seen)), sorted(set(everything)),
                         "逐页取回的条目集合必须和一次取全一致")

    def test_sources_are_listed_with_their_last_status(self):
        self._seed()
        source = self._get()["sources"][0]
        self.assertEqual(source["provider_label"], "Rule34Video")
        self.assertEqual(source["last_status"], "ok")
        self.assertTrue(source["enabled"])

    def test_status_write_rejects_a_non_integer_item(self):
        with self.assertRaises(ValueError):
            self._post("/api/follow/status", {"item": "1", "to": "seen"})

    def test_saving_writes_one_online_asset(self):
        self._seed()
        item = self._get()["groups"][0]["primary"]["id"]
        result = self._post("/api/follow/save", {"item": item})
        self.assertTrue(result["ok"])
        with self.contract.database.read_connection() as connection:
            row = connection.execute(
                "SELECT location,path FROM asset WHERE id=?",
                (result["asset_id"],)).fetchone()
        self.assertEqual(row["location"], "online")
        self.assertEqual(self._get(status="saved")["counts"]["saved"], 1)

    def test_saving_accepts_a_multi_selection_atomically(self):
        self._seed()
        group = self._get()["groups"][0]
        items = [group["primary"]["id"], group["variants"][0]["id"]]
        result = self._post("/api/follow/save", {"items": items})
        self.assertEqual(result["items"], items)
        self.assertEqual(len(result["asset_ids"]), 2)
        with self.contract.database.read_connection() as connection:
            count = connection.execute(
                "SELECT count(*) FROM asset WHERE id IN (?, ?)",
                result["asset_ids"],
            ).fetchone()[0]
        self.assertEqual(count, 2)

    def test_check_is_the_only_endpoint_that_reaches_the_network(self):
        self._seed()
        fetch = SourceFetch(
            provider="rule34video", ref="lazyprocrastinator",
            request_url="https://rule34video.com/models/lazyprocrastinator/",
            semantics="work", raw_body=b"<html>2</html>",
            candidates=(FollowCandidate(provider="rule34video", external_id="999",
                                        title="Sayuri - Handy"),))
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch
            result = self._post("/api/follow/check", {})
        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["results"][0]["added"], 1)

    def test_one_failing_source_does_not_hide_the_others(self):
        self._seed()
        self._seed(provider="rule34xxx", ref="lazyprocrastinator", candidates=())

        def factory(provider, **kwargs):
            connector = mock.Mock()
            if provider == "rule34xxx":
                connector.fetch.side_effect = CredentialError("需要 user_id 与 api_key")
            else:
                connector.fetch.return_value = SourceFetch(
                    provider="rule34video", ref="lazyprocrastinator",
                    request_url="https://rule34video.test/", semantics="work",
                    not_modified=True)
            return connector

        with mock.patch.object(web_follow, "build_connector", factory):
            result = self._post("/api/follow/check", {})
        outcomes = {row["provider"]: row for row in result["results"]}
        self.assertFalse(outcomes["rule34xxx"]["ok"])
        self.assertEqual(outcomes["rule34xxx"]["status"], "unauthorized")
        self.assertTrue(outcomes["rule34video"]["ok"])
        self.assertTrue(outcomes["rule34video"]["not_modified"])

    def test_an_unwritable_evidence_root_is_reported_without_failing_the_check(self):
        self._seed()
        contract = self.contract
        contract.follow_sources_root = self.root / "evidence"
        # 用普通文件占住路径构造同一个 FileExistsError：symlink 在非管理员 Windows 上建不了。
        (self.root / "evidence").write_text("not a directory", encoding="utf-8")
        fetch = SourceFetch(
            provider="rule34video", ref="lazyprocrastinator",
            request_url="https://rule34video.com/models/lazyprocrastinator/",
            semantics="work", raw_body=b"<html>2</html>",
            candidates=(FollowCandidate(provider="rule34video", external_id="999",
                                        title="Sayuri - Handy"),))
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch
            result = self._post("/api/follow/check", {})
        outcome = result["results"][0]
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["added"], 1)
        self.assertIn("证据未取得", outcome["evidence_error"])
        self.assertEqual(self._get()["sources"][0]["last_status"], "ok")

    def test_source_errors_are_recorded_for_later_inspection(self):
        self._seed()
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.side_effect = FollowSourceError("HTTP 503")
            self._post("/api/follow/check", {})
        self.assertEqual(self._get()["sources"][0]["last_status"], "error")
        self.assertIn("503", self._get()["sources"][0]["last_error"])

    def test_credentials_say_what_each_source_actually_needs(self):
        payload = self._get("/api/follow/credentials")
        by_provider = {row["provider"]: row for row in payload["providers"]}
        self.assertEqual(by_provider["kemono"]["requirement"], "none")
        self.assertEqual(by_provider["rule34xxx"]["requirement"], "required")
        self.assertEqual(by_provider["rule34xxx"]["needs"], ["user_id", "api_key"])
        self.assertEqual(by_provider["rule34xxx"]["missing"], ["user_id", "api_key"])
        self.assertEqual(by_provider["f95zone"]["requirement"], "optional")
        self.assertEqual(by_provider["fanbox"]["requirement"], "optional")
        self.assertEqual(by_provider["fanbox"]["needs"], ["cookie"])
        self.assertTrue(by_provider["fanbox"]["path"].endswith("fanbox.json"))
        self.assertEqual(by_provider["gofile"]["requirement"], "optional")
        self.assertEqual(by_provider["gofile"]["needs"], ["api_token"])
        self.assertTrue(by_provider["gofile"]["path"].endswith("gofile.json"))
        self.assertEqual(by_provider["simpcity"]["requirement"], "blocked")
        self.assertIn("DDoS-Guard", by_provider["simpcity"]["why"])
        self.assertTrue(by_provider["rule34xxx"]["path"].endswith("rule34xxx.json"))

    def test_a_configured_credential_reports_nothing_missing(self):
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "sekret"}', encoding="utf-8")
        row = next(r for r in self._get("/api/follow/credentials")["providers"]
                   if r["provider"] == "rule34xxx")
        self.assertEqual(row["missing"], [])
        self.assertNotIn("sekret", json.dumps(row))

    def test_saving_a_credential_writes_it_without_echoing_the_value(self):
        result = self._post("/api/follow/credential", {
            "provider": "rule34xxx",
            "values": {"user_id": "42", "api_key": "sekret"}})
        self.assertTrue(result["ok"])
        self.assertNotIn("sekret", json.dumps(result))
        self.assertEqual(result["saved"]["fields"], ["api_key", "user_id"])
        path = self.root / "secrets" / "follow" / "rule34xxx.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                         {"user_id": "42", "api_key": "sekret"})
        if os.name == "nt":
            # Windows 的 chmod 只能拨只读位，NTFS 权限走 ACL——这里不假装收紧过。
            self.assertFalse(result["permissions_tightened"])
        else:
            self.assertTrue(result["permissions_tightened"])
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_clearing_a_credential_removes_the_file(self):
        self._post("/api/follow/credential", {
            "provider": "rule34xxx", "values": {"user_id": "42", "api_key": "k"}})
        result = self._post("/api/follow/credential",
                            {"provider": "rule34xxx", "values": {}})
        self.assertTrue(result["cleared"])
        self.assertFalse((self.root / "secrets" / "follow" / "rule34xxx.json").exists())

    def test_clearing_also_removes_the_shared_copy(self):
        """撤销必须两边一起撤，否则等于撤不掉。

        只删本机那份的话，`load()` 会从共享副本把 key 重新拼回来；而共享副本还会跟着
        peach-sync 传到另一台，结果是**在任何一台上都撤不掉**。给得出「配上」就要
        给得出「撤掉」，同步这个功能不能把那个保证破坏掉。
        """
        self.contract.follow_shared_root = self.root / "shared"
        (self.root / "shared").mkdir()
        self._post("/api/follow/credential", {
            "provider": "rule34xxx", "values": {"user_id": "42", "api_key": "k"}})
        shared = self.root / "shared" / "secrets" / "follow" / "rule34xxx.json"
        self.assertTrue(shared.exists())

        result = self._post("/api/follow/credential",
                            {"provider": "rule34xxx", "values": {}})
        self.assertEqual(result["shared_cleared"], "removed")
        self.assertFalse(shared.exists())
        self.assertIsNone(_credential_store(self.contract).load("rule34xxx"),
                          "撤销之后连接器不该还拿得到 key")

    def test_a_shared_only_credential_reports_present_not_missing(self):
        """`describe()` 和 `load()` 必须看同一份事实。

        早先 `describe()` 只看本机文件、`load()` 会从共享副本回填，于是页面报「未配置」
        而请求照样带着共享里那把 key 发出去。用户看到的状态和系统实际用的凭据不一致，
        比撤不掉更糟——他会以为已经撤了。
        """
        self.contract.follow_shared_root = self.root / "shared"
        shared = self.root / "shared" / "secrets" / "follow"
        shared.mkdir(parents=True)
        (shared / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "fromshared"}', encoding="utf-8")
        described = _credential_store(self.contract).describe("rule34xxx")
        self.assertTrue(described["present"])
        self.assertEqual(described["fields"], ["api_key", "user_id"])
        self.assertEqual(described["local_fields"], [])
        # 用户得知道这几个字段是从共享回填的，否则不知道该去哪台机器上撤。
        self.assertEqual(described["shared_fields"], ["api_key", "user_id"])

    def test_clearing_says_so_when_the_shared_root_is_offline(self):
        """共享盘不在时不能静默跳过：那等于让用户以为撤了其实没撤。"""
        self.contract.follow_shared_root = self.root / "no-such-volume"
        self._post("/api/follow/credential", {
            "provider": "rule34xxx", "values": {"user_id": "42", "api_key": "k"}})
        result = self._post("/api/follow/credential",
                            {"provider": "rule34xxx", "values": {}})
        self.assertEqual(result["shared_cleared"], "offline")
        self.assertIn("只撤掉了本机", result["note"])

    def test_only_fields_declared_syncable_reach_the_shared_copy(self):
        """可同步是逐字段声明的，不按字段名猜。

        用户定的口径是「就同步 apikey，cookie 不同步」——cookie 绑会话和客户端 IP，
        同步过去也会失效。但判据不能写成「名字里有 cookie 就不同步」：明天来一个
        `session_token` 就会落到错误的一侧。
        """
        self.contract.follow_shared_root = self.root / "shared"
        (self.root / "shared").mkdir()
        result = self._post("/api/follow/credential", {
            "provider": "rule34xxx",
            "values": {"user_id": "42", "api_key": "sekret"}})
        self.assertTrue(result["synced"])
        shared = self.root / "shared" / "secrets" / "follow" / "rule34xxx.json"
        self.assertEqual(json.loads(shared.read_text(encoding="utf-8")),
                         {"user_id": "42", "api_key": "sekret"})

        cookie = self._post("/api/follow/credential", {
            "provider": "f95zone", "values": {"cookie": "xf=1"}})
        self.assertFalse(cookie["synced"], "cookie 不该进共享副本")
        self.assertFalse(
            (self.root / "shared" / "secrets" / "follow" / "f95zone.json").exists())
        # 本机那份照常写了。
        self.assertTrue(
            (self.root / "secrets" / "follow" / "f95zone.json").exists())

    def test_a_synced_field_is_read_back_when_the_local_copy_lacks_it(self):
        self.contract.follow_shared_root = self.root / "shared"
        shared = self.root / "shared" / "secrets" / "follow"
        shared.mkdir(parents=True)
        (shared / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "fromshared", "cookie": "nope"}',
            encoding="utf-8")
        store = _credential_store(self.contract)
        loaded = store.load("rule34xxx")
        self.assertEqual(loaded.values["api_key"], "fromshared")
        # 共享副本里混进未声明的字段也不会被采纳。
        self.assertNotIn("cookie", loaded.values)

    def test_the_local_copy_wins_over_the_shared_one(self):
        self.contract.follow_shared_root = self.root / "shared"
        shared = self.root / "shared" / "secrets" / "follow"
        shared.mkdir(parents=True)
        (shared / "rule34xxx.json").write_text(
            '{"user_id": "old", "api_key": "old"}', encoding="utf-8")
        local = self.root / "secrets" / "follow"
        local.mkdir(parents=True)
        (local / "rule34xxx.json").write_text(
            '{"user_id": "mine", "api_key": "mine"}', encoding="utf-8")
        loaded = _credential_store(self.contract).load("rule34xxx")
        self.assertEqual(loaded.values["api_key"], "mine")

    def test_an_unreachable_shared_root_does_not_fail_the_save(self):
        self.contract.follow_shared_root = self.root / "no-such-volume"
        result = self._post("/api/follow/credential", {
            "provider": "rule34xxx", "values": {"user_id": "42", "api_key": "k"}})
        self.assertTrue(result["ok"])
        self.assertFalse(result["synced"])
        self.assertTrue((self.root / "secrets" / "follow" / "rule34xxx.json").exists())

    def test_only_declared_providers_and_fields_are_accepted(self):
        for body in ({"provider": "kemono", "values": {"x": "1"}},
                     {"provider": "../escape", "values": {"x": "1"}},
                     {"provider": "rule34xxx", "values": {"evil": "1"}},
                     {"provider": "rule34xxx", "values": "notadict"}):
            with self.assertRaises(ValueError):
                self._post("/api/follow/credential", body)
        self.assertFalse((self.root / "secrets").exists())

    def _write_taste(self, rows):
        root = self.root / "taste"
        root.mkdir(exist_ok=True)
        lines = ["candidate,kind,visits,distinct_urls,source_count,sources,status"]
        lines += [f"{n},creator,{v},1,1,safari:iCloud,candidate" for n, v in rows]
        (root / "taste-creator-candidates-20260826-193252.csv").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
        self.contract.taste_history_root = root

    def test_suggestions_come_from_the_browsing_taste_analysis(self):
        """真正的信号是浏览历史分析，不是账本里已有什么。

        `facets.creators` 是「他有谁的文件」，`location='online'` 的资产是「他关注过谁」，
        两者都不是「他常搜谁」——用户举的名字在前两者里要么没有、要么在目标站上找不到。
        """
        self._write_taste([("lazyprocrastinator", 28), ("ffxivinitiala", 13)])
        with self.contract.database.write_transaction() as connection:
            connection.execute(
                "INSERT INTO asset(location,path,name,medium) VALUES"
                "('local','R:/x.mp4','SomeLocalCreator','video')")
        suggestions = self._get()["suggestions"]
        self.assertEqual([s["name"] for s in suggestions],
                         ["lazyprocrastinator", "ffxivinitiala"])
        self.assertEqual(suggestions[0]["visits"], 28)
        self.assertNotIn("SomeLocalCreator", [s["name"] for s in suggestions])

    def test_suggestions_are_ordered_by_how_often_he_looked(self):
        self._write_taste([("rarely", 2), ("often", 40), ("sometimes", 9)])
        self.assertEqual([s["name"] for s in self._get()["suggestions"]],
                         ["often", "sometimes", "rarely"])

    def test_no_analysis_means_no_suggestions_rather_than_a_substitute(self):
        self.contract.taste_history_root = self.root / "never-run"
        self.assertEqual(self._get()["suggestions"], [])

    def test_suggestions_skip_sources_already_followed(self):
        self._write_taste([("lazyprocrastinator", 28), ("bewyx", 21)])
        with self.contract.database.write_transaction() as connection:
            FollowStore(lambda: connection).register(
                provider="kemono", ref="fanbox/30917150",
                label="lazyprocrastinator", url="https://kemono.cr/fanbox/30917150",
                moment=MOMENT)
        names = [s["name"] for s in self._get()["suggestions"]]
        self.assertEqual(names, ["bewyx"], "已经在追的不该再建议")

    def test_credentials_endpoint_reports_fields_but_never_values(self):
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "sekret"}', encoding="utf-8")
        payload = self._get("/api/follow/credentials")
        rule34 = next(row for row in payload["providers"]
                      if row["provider"] == "rule34xxx")
        self.assertTrue(rule34["present"])
        self.assertEqual(rule34["fields"], ["api_key", "user_id"])
        self.assertNotIn("sekret", json.dumps(payload))

    def test_f95_resource_replies_are_returned_as_independent_items(self):
        self._seed(provider="f95zone", ref="50685", semantics="release", candidates=(
            FollowCandidate(provider="f95zone", external_id="21383374",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            url="https://f95zone.to/threads/50685/post-21383374",
                            published_at="2026-08-21T04:14:09Z", author="Jkhomie1198",
                            summary="New batch up Gofile",
                            media_url="https://f95zone.to/masked/gofile.io/50685/abc",
                            extra={"links": [
                                "https://f95zone.to/masked/gofile.io/50685/abc"],
                                "media_needs_credential": True}),
            FollowCandidate(provider="f95zone", external_id="21394555",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            url="https://f95zone.to/threads/50685/post-21394555",
                            published_at="2026-08-22T18:09:23Z",
                            extra={"attachment_count": 1, "attachments": [
                                "https://attachments.f95zone.to/2026/08/archive.zip"]}),
        ))
        groups = self._get()["groups"]
        self.assertEqual(len(groups), 2)
        self.assertEqual([group["primary"]["external_id"] for group in groups],
                         ["21394555", "21383374"])
        self.assertTrue(all(group["is_release"] for group in groups))
        self.assertTrue(all(group["variants"] == [] for group in groups))
        older = groups[1]["primary"]
        self.assertTrue(older["media_needs_credential"])
        self.assertEqual(older["author"], "Jkhomie1198")
        self.assertEqual(older["summary"], "New batch up Gofile")


class FollowSourceAddTests(FollowContractTests):
    """粘链接登记来源。首次检查用注入的连接器，测试不联网。"""

    def _add(self, url, fetch=None):
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch or SourceFetch(
                provider="rule34video", ref="x", request_url="https://x.test/",
                semantics="work", not_modified=True)
            return self._post("/api/follow/source", {"action": "add", "url": url})

    def test_pasting_a_creator_link_registers_and_checks_it(self):
        result = self._add("https://rule34video.com/models/lazyprocrastinator/")
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "rule34video")
        self.assertEqual(result["ref"], "lazyprocrastinator")
        self.assertTrue(result["checked"]["ok"])
        self.assertEqual(self._get()["sources"][0]["url"],
                         "https://rule34video.com/models/lazyprocrastinator/")

    def test_a_discovery_author_hint_is_persisted_for_cross_site_grouping(self):
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = SourceFetch(
                provider="rule34video", ref="lazyprocrastinator",
                request_url="https://rule34video.test/x", semantics="work",
                not_modified=True)
            self._post("/api/follow/source", {
                "action": "add",
                "url": "https://rule34video.com/models/lazyprocrastinator/",
                "author": "Lazy Procrastinator",
            })
        source = self._get()["sources"][0]
        self.assertEqual(source["author_key"], "name:lazyprocrastinator")

    def test_a_name_miss_exposes_the_google_f95_fallback_without_adding_it(self):
        fallback = ExternalSearch(
            provider="f95zone", label="用 Google 继续查找 F95zone",
            query="initial_a f95zone",
            url="https://www.google.com/search?q=initial_a+f95zone",
            evidence="F95zone 站内索引未命中，请核对搜索结果里的真实线程链接",
        )
        with mock.patch.object(web_follow, "discover", return_value=Discovery(
                "initial_a", external_searches=(fallback,))):
            result = self._post("/api/follow/resolve", {"lines": ["initial_a"]})
        row = result["results"][0]
        self.assertEqual(row["candidates"], [])
        self.assertEqual(row["external_searches"], [{
            "provider": "f95zone", "provider_label": "F95zone",
            "label": "用 Google 继续查找 F95zone",
            "query": "initial_a f95zone",
            "url": "https://www.google.com/search?q=initial_a+f95zone",
            "evidence": "F95zone 站内索引未命中，请核对搜索结果里的真实线程链接",
        }])
        self.assertEqual(self._get()["sources"], [], "查找入口不能自动登记来源")

    def test_a_fanbox_subdomain_url_is_shown_as_an_addable_candidate(self):
        result = self._post("/api/follow/resolve", {
            "lines": ["https://lazyprocrast.fanbox.cc/"]})

        row = result["results"][0]
        self.assertEqual(row["kind"], "url")
        self.assertEqual(row["candidates"], [{
            "provider": "fanbox", "provider_label": "FANBOX",
            "ref": "lazyprocrast", "url": "https://lazyprocrast.fanbox.cc/",
            "label": "lazyprocrast", "author": "", "semantics": "work",
            "evidence": "链接直接指明", "known": False,
        }])

    def test_a_thread_link_is_registered_with_release_semantics(self):
        self._add("https://f95zone.to/threads/"
                  "lazy-procrastinator-collection-2026-06-28-lazyprocrast.50685/")
        source = self._get()["sources"][0]
        self.assertEqual(source["provider"], "f95zone")
        self.assertEqual(source["ref"], "50685")
        self.assertEqual(source["semantics"], "release")
        self.assertEqual(source["label"], "lazy procrastinator collection")

    def test_a_kemono_link_keeps_its_service_and_user(self):
        self._add("https://kemono.cr/fanbox/user/30917150")
        source = self._get()["sources"][0]
        self.assertEqual(source["provider"], "kemono")
        self.assertEqual(source["ref"], "fanbox/30917150")

    def test_the_same_link_twice_does_not_duplicate_the_source(self):
        self._add("https://rule34video.com/models/lazyprocrastinator/")
        self._add("https://rule34video.com/models/lazyprocrastinator/")
        self.assertEqual(len(self._get()["sources"]), 1)

    def test_rule34_case_variants_do_not_duplicate_the_source(self):
        self._add(
            "https://rule34.xxx/index.php?page=post&s=list&tags=LazyProcrastinator")
        self._add(
            "https://rule34.xxx/index.php?page=post&s=list&tags=lazyprocrastinator")
        sources = [row for row in self._get()["sources"]
                   if row["provider"] == "rule34xxx"]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["ref"], "lazyprocrastinator")

    def test_a_failing_first_check_still_leaves_the_source_registered(self):
        # rule34.xxx 缺 key 就是这种情况。整个回滚掉反而让人不知道发生了什么。
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.side_effect = CredentialError("需要 user_id")
            result = self._post("/api/follow/source", {
                "action": "add",
                "url": "https://rule34.xxx/index.php?page=post&s=list&tags=lazy"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["checked"]["ok"])
        source = self._get()["sources"][0]
        self.assertEqual(source["last_status"], "unauthorized")
        self.assertIn("user_id", source["last_error"])

    def test_an_unknown_host_is_refused_with_the_supported_list(self):
        with self.assertRaises(FollowSourceError) as caught:
            self._post("/api/follow/source",
                       {"action": "add", "url": "https://example.test/creator"})
        self.assertIn("kemono.cr", str(caught.exception))

    def test_simpcity_is_refused_with_the_bot_check_reason(self):
        with self.assertRaises(FollowSourceError) as caught:
            self._post("/api/follow/source",
                       {"action": "add", "url": "https://simpcity.cr/threads/x.1/"})
        self.assertIn("DDoS-Guard", str(caught.exception))

    def test_removing_a_source_takes_its_items_with_it(self):
        self._seed()
        source_id = self._get()["sources"][0]["id"]
        self.assertTrue(self._get()["groups"])
        self._post("/api/follow/source", {"action": "remove", "id": source_id})
        payload = self._get()
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["groups"], [])

    def test_remove_requires_an_integer_id(self):
        with self.assertRaises(ValueError):
            self._post("/api/follow/source", {"action": "remove", "id": "1"})

    def test_unknown_actions_are_rejected(self):
        with self.assertRaises(ValueError):
            self._post("/api/follow/source", {"action": "explode"})

    def test_a_source_can_be_excluded_from_update_checks(self):
        source_id = self._seed()
        result = self._post("/api/follow/source", {
            "action": "enabled", "id": source_id, "enabled": False})
        self.assertFalse(result["enabled"])
        payload = self._get()
        self.assertFalse(payload["sources"][0]["enabled"])
        self.assertEqual(payload["groups"], [], "暂停的来源不应继续出现在关注流")
        self.assertEqual(payload["counts"]["new"], 0)
        with mock.patch.object(web_follow, "build_connector") as factory:
            checked = self._post("/api/follow/check", {})
        self.assertEqual(checked["checked"], 0)
        factory.assert_not_called()

    def test_source_enabled_requires_typed_values_and_an_existing_source(self):
        for body in ({"action": "enabled", "id": "1", "enabled": False},
                     {"action": "enabled", "id": 1, "enabled": 0},
                     {"action": "enabled", "id": 999, "enabled": True}):
            with self.assertRaises(ValueError):
                self._post("/api/follow/source", body)
    def _source(self, provider, ref, label):
        with self.contract.database.write_transaction() as connection:
            return FollowStore(lambda: connection).register(
                provider=provider, ref=ref, label=label,
                url=f"https://{provider}.test/{ref}", moment=MOMENT)

    def test_similar_cross_platform_names_are_suggested_but_not_auto_merged(self):
        self._source("fanbox", "initiala", "InitialA")
        self._source("rule34video", "ffxivinitiala", "FFXIVInitialA")
        payload = self._get()
        self.assertEqual(len({row["author_key"] for row in payload["sources"]}), 2)
        self.assertEqual(payload["alias_suggestions"], [{
            "canonical": "InitialA", "alias": "FFXIVInitialA",
            "evidence": "规范化名称存在包含关系，仅供人工确认",
        }])

    def test_confirmed_alias_merges_sources_and_can_be_removed(self):
        self._source("fanbox", "initiala", "InitialA")
        self._source("rule34video", "ffxivinitiala", "FFXIVInitialA")
        added = self._post("/api/follow/author-alias", {
            "action": "add", "canonical": "InitialA", "alias": "FFXIVInitialA"})
        self.assertTrue(added["ok"])
        payload = self._get()
        self.assertEqual({row["author_key"] for row in payload["sources"]},
                         {"name:initiala"})
        self.assertEqual(payload["author_aliases"][0]["canonical_name"], "InitialA")
        self.assertEqual(payload["author_aliases"][0]["aliases"][0]["name"],
                         "FFXIVInitialA")
        removed = self._post("/api/follow/author-alias", {
            "action": "remove", "alias": "FFXIVInitialA"})
        self.assertTrue(removed["ok"])
        self.assertEqual(len({row["author_key"] for row in self._get()["sources"]}), 2)

    def test_an_official_profile_learns_its_handle_as_an_alias(self):
        self._source("rule34video", "ffxivinitiala", "FFXIVInitialA")
        fetch = SourceFetch(
            provider="fanbox", ref="ffxivinitiala",
            request_url="https://api.fanbox.cc/post.listCreator",
            semantics="work", candidates=(FollowCandidate(
                provider="fanbox", external_id="1", title="Free post",
                url="https://ffxivinitiala.fanbox.cc/posts/1", author="InitialA",
            ),),
        )
        result = self._add("https://ffxivinitiala.fanbox.cc/", fetch=fetch)
        self.assertEqual(result["checked"]["author_alias_learned"], {
            "canonical": "InitialA", "alias": "ffxivinitiala",
            "source": "official:fanbox",
        })
        payload = self._get()
        self.assertEqual({row["author_key"] for row in payload["sources"]},
                         {"name:initiala"})
        self.assertEqual(payload["author_aliases"][0]["aliases"][0]["source"],
                         "official:fanbox")

    def test_ambiguous_official_profile_does_not_learn_an_alias(self):
        fetch = SourceFetch(
            provider="fanbox", ref="shared-handle",
            request_url="https://api.fanbox.cc/post.listCreator",
            semantics="work", candidates=(
                FollowCandidate(provider="fanbox", external_id="1", title="One",
                                author="First"),
                FollowCandidate(provider="fanbox", external_id="2", title="Two",
                                author="Second"),
            ),
        )
        result = self._add("https://shared-handle.fanbox.cc/", fetch=fetch)
        self.assertIsNone(result["checked"]["author_alias_learned"])
        self.assertEqual(self._get()["author_aliases"], [])

    def test_official_evidence_never_overwrites_a_manual_alias(self):
        self._source("rule34video", "shared-handle", "SharedHandle")
        self._post("/api/follow/author-alias", {
            "action": "add", "canonical": "KnownAuthor", "alias": "SharedHandle"})
        fetch = SourceFetch(
            provider="fanbox", ref="shared-handle",
            request_url="https://api.fanbox.cc/post.listCreator",
            semantics="work", candidates=(FollowCandidate(
                provider="fanbox", external_id="1", title="One", author="OtherAuthor",
            ),),
        )
        result = self._add("https://shared-handle.fanbox.cc/", fetch=fetch)
        self.assertIsNone(result["checked"]["author_alias_learned"])
        aliases = self._get()["author_aliases"]
        self.assertEqual(aliases[0]["canonical_name"], "KnownAuthor")
        self.assertEqual(aliases[0]["aliases"][0]["source"], "manual")

    def test_alias_names_must_be_distinct_and_nonempty(self):
        for body in ({"canonical": "InitialA", "alias": "initial-a"},
                     {"canonical": "", "alias": "FFXIVInitialA"}):
            with self.assertRaises(ValueError):
                self._post("/api/follow/author-alias", body)


class FollowWebSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 和 test_web_ui 同一口径：Web 表面是拼起来的一个契约，不是某个文件。
        # web/js 下的 ES module 用 glob 收，拆出新模块时不必回头改这里。
        web = ROOT / "web"
        sources = [web / "index.html", web / "app.css", web / "app.js"]
        sources.extend(sorted((web / "js").glob("*.js")))
        cls.page = chr(10).join(
            path.read_text(encoding="utf-8") for path in sources)

    def assertPageContains(self, needle, message=""):
        if needle not in self.page:
            self.fail(f"Web 表面缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def assertPageLacks(self, needle, message=""):
        if needle in self.page:
            self.fail(f"Web 表面不应出现：{needle!r}" + (f"（{message}）" if message else ""))

    def test_watching_lives_in_the_left_rail_and_managing_stays_in_the_manage_area(self):
        # 看和管是两件事，两个页面：左侧导航进「看」，管理区进「管」。
        # 断言「相邻」这件事本身，不要连换行和缩进一起写死——那种断言一改格式就红，
        # 红的原因还和它想守的契约无关。
        rail = self.page[self.page.index("const EDGE_ICONS=["):]
        rail = rail[:rail.index("];")]
        keys = re.findall(r"\['([a-z]*)'", rail)
        self.assertIn("follow", keys)
        self.assertEqual(keys[keys.index("follow") + 1], "immerse",
                         "关注入口应当排在沉浸模式前面")
        self.assertPageContains("['follow','关注','rss']")
        self.assertPageContains("if(k==='follow'){openFollow();return}")
        self.assertPageContains("if(k==='follow')return path==='/follow';")
        # 两个数组现在同名，字面量断言分不出是哪一个：
        # 管理区这一项得在 MANAGE_SECTIONS 里找，否则它被删了测试照样绿。
        manage = self.page[self.page.index("const MANAGE_SECTIONS=["):]
        manage = manage[:manage.index("];")]
        self.assertIn("['follow','关注','rss']", manage)
        self.assertPageContains('<symbol id="i-rss"')
        self.assertPageContains("if(path==='/follow-manage')return 'follow'")
        self.assertPageContains("if(section==='follow'){openFollowManage();return}")

    def test_follow_routes_restore_on_reload(self):
        self.assertPageContains("if(path==='/follow'){await openFollow(false);return}")
        self.assertPageContains(
            "if(path==='/follow-manage'){await openFollowManage(false);return}")
        self.assertPageContains(
            "await openFollow(false,true);await openFollowDetail(+parts[2],false)")
        self.assertPageContains("api(`/api/follow?item=${encodeURIComponent(id)}`)")
        self.assertPageContains(".then(async()=>{buildEdge();wireAllDrag();await restoreRoute();scheduleStickySurfaces()})")

    def test_the_add_state_is_looked_up_outside_the_form(self):
        # 提示行在表单外面。在 form 里找它会拿到 null，第一次赋值就抛 TypeError，
        # 整个提交静默失败——实测踩过。
        self.assertPageContains("const state=root.querySelector('[data-follow-add-state]')")

    def test_sources_are_added_by_pasting_not_by_a_command(self):
        self.assertPageContains('id="followAdd"')
        self.assertPageContains('name="lines"')
        self.assertPageContains("'/api/follow/source'")
        self.assertPageContains("data-follow-remove")

    def test_reader_management_is_locked_and_points_to_the_writer(self):
        self.assertPageContains("api('/healthz')")
        self.assertPageContains("followRuntime?.ledger_read_only")
        self.assertPageContains("前往写入端管理关注")
        self.assertPageContains("#followAdd textarea,#followAdd button")

    def test_failed_source_adds_stay_visible_instead_of_being_erased_by_reload(self):
        block = self.page[self.page.index("if(addButton)addButton.onclick=async()=>"):
                          self.page.index("async function followWrite(")]
        self.assertIn("const failures=[]", block)
        self.assertIn("state.textContent=failures.join('；')", block)
        self.assertLess(block.index("if(failures.length)"),
                        block.index("await openFollowManage(false)"))
        self.assertIn("return;", block[block.index("if(failures.length)"):])

    def test_a_bare_name_or_id_is_looked_up_across_sources(self):
        self.assertPageContains("'/api/follow/resolve'")
        self.assertPageContains("function renderFollowPicks(")
        # 结果先勾选再落地，不自动登记。
        self.assertPageContains("data-pick-add")
        self.assertPageContains("data-pick-cancel")

    def test_lookup_results_stay_inside_the_add_section_with_one_title_scale(self):
        page = self.page
        manage = page[page.index("function renderFollowManage("):
                      page.index("function wireFollowItems(")]
        add_section = manage[manage.index('<section class="fsec">'):
                             manage.index('</section>')]
        self.assertIn('id="followPicks"', add_section)
        self.assertNotIn('</section>\n      <div id="followPicks">', manage)
        self.assertPageContains(
            '<div class="fpicks"><div class="fpickhead"><h3>查找结果</h3>')
        self.assertPageContains('<p class="fpickempty">站内没有查到来源</p>')
        self.assertPageContains("box.scrollIntoView({block:'nearest',behavior:'smooth'})")
        self.assertNotIn(".fpicks h3{", page,
                         "查找结果不应另起一套标题字号")

    def test_f95_misses_offer_a_clickable_google_query(self):
        self.assertPageContains("row.external_searches||[]")
        self.assertPageContains('class="fpicksearch" href="${esc(search.url)}"')
        self.assertPageContains('target="_blank" rel="noreferrer noopener"')
        self.assertPageContains("${esc(search.query)}")

    def test_follow_author_groups_use_multiple_columns_and_link_to_the_original_page(self):
        self.assertPageContains('class="frows fsources"')
        grid = self.page[self.page.index(".fsources{"):]
        self.assertIn("repeat(auto-fit,minmax(430px,1fr))", grid[:grid.index("}")])
        self.assertPageContains("followAuthorGroups(sources).map(followAuthorBlock).join('')")
        self.assertNotIn(".fsources>.fauthor{display:grid", self.page,
                         "多栏单位是作者组，不能拆开作者下面的来源行")
        self.assertPageContains('class="fsourcelink" href="${esc(source.url)}"')
        self.assertPageContains('title="打开原来源"')
        self.assertPageContains('rel="noreferrer noopener"')
        author = self.page[self.page.index(".fauthor{"):]
        self.assertIn("border-top:0", author[:author.index("}")],
                      "每一栏首个作者上方都不应出现横线")

    def test_source_actions_are_icon_only_and_stay_on_one_row(self):
        row = self.page[self.page.index("function followSourceRow(source)"):]
        row = row[:row.index("function followAliasManager")]
        self.assertIn("data-follow-check", row)
        self.assertIn("data-follow-remove", row)
        self.assertIn("${icon('refresh-cw')}", row)
        self.assertIn("${icon('trash')}", row)
        self.assertNotIn(">检查</button>", row)
        self.assertNotIn(">移除</button>", row)
        rule = self.page[self.page.index(".fauthor .fsource.frow{"):]
        self.assertIn("flex-wrap:nowrap", rule[:rule.index("}")])

    def test_each_channel_has_a_styled_update_checkbox(self):
        self.assertPageContains('class="fchannelcheck"')
        self.assertPageContains('type="checkbox" data-follow-enabled=')
        self.assertPageContains("{action:'enabled',id:Number(control.dataset.followEnabled),enabled}")
        self.assertPageContains(".fchannelcheck input{position:absolute;width:1px;height:1px;opacity:0")
        self.assertPageContains(".fchannelcheck input:checked+span{")
        self.assertPageContains("${icon('check')}")

    def test_official_channel_icons_and_alias_manager_are_visible(self):
        icons = self.page.split("const SOURCE_ICONS={", 1)[1].split("};", 1)[0]
        for provider in ("fanbox", "patreon", "subscribestar"):
            self.assertIn(provider, icons)
        self.assertIn("assets.subscribestar.com/assets/public/images/favicons/favicon-32x32-", icons)
        self.assertPageContains("followAliasManager(followData.author_aliases,followData.alias_suggestions)")
        self.assertPageContains("'/api/follow/author-alias'")

    def test_already_followed_candidates_are_shown_but_not_selectable(self):
        # 灰掉但仍显示，免得人以为没查到。
        self.assertPageContains("c.known?' known':''")
        self.assertPageContains("'已经关注'")

    def test_the_first_name_lookup_warns_about_the_index_download(self):
        self.assertPageContains("首次按名字查要下载创作者索引，可能几十秒")

    def test_the_input_and_its_button_are_the_same_height(self):
        # 静止时输入框就该和按钮齐平；固定多行的话按钮只有它一小截高。
        page = self.page
        self.assertEqual(page.count(".faddform textarea{"), 1,
                         "旧规则留在后面会覆盖新输入框样式")
        rule = page[page.index(".faddform textarea{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("height:38px", rule)
        self.assertIn("min-height:38px", rule)
        # 38px - 2px 边框 - 16px 内边距 = 20px 行高；textarea 会从内容区
        # 顶部排第一行，留下额外内容高度就会让文字视觉上偏上。
        self.assertIn("padding:8px 12px 8px 38px", rule)
        self.assertIn("line-height:20px", rule)
        button = page[page.index("\n.fbtn{"):]
        self.assertIn("height:32px", button[:button.index("}")])
        # faddform 里的按钮随输入栏同高（Geist 输入 32px 基线之上的一档）。
        add_button = page[page.index(".faddform .fbtn{"):]
        self.assertIn("height:38px", add_button[:add_button.index("}")])

    def test_source_filter_uses_the_project_toolbar_layout_without_menu_motion(self):
        # Vercel Projects：搜索占剩余宽度，筛选带明确标签，主操作在右；
        # 菜单没有展开动画，并在自己的视口内滚动。
        self.assertPageContains(
            ".faddform{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px")
        self.assertPageContains(
            ".faddform .fsrcfilter .fbtn{width:auto;height:38px;min-height:38px;padding:0 11px}")
        self.assertPageContains('aria-expanded="false" aria-haspopup="menu"')
        self.assertPageContains('aria-label="${esc(label())}" title="${esc(label())}"')
        self.assertPageContains("data-srcfilter-label")
        self.assertPageContains("'全部来源'")
        menu = self.page[self.page.index(".fsrcmenu{"):]
        menu = menu[:menu.index("}")]
        self.assertIn("position:fixed", menu)
        self.assertIn("width:min(250px,calc(100vw - 16px))", menu)
        self.assertIn("overflow-x:hidden", menu)
        self.assertIn("overflow-y:auto", menu)
        self.assertIn("overscroll-behavior:contain", menu)
        self.assertNotIn("transition", menu)
        source_filter = self.page[self.page.index("function renderFollowSrcFilter("):
                                  self.page.index("function renderFollowPicks(")]
        self.assertNotIn("transitionend", source_filter)
        self.assertNotIn("style.height", source_filter)
        self.assertIn("innerWidth-width-8", source_filter)
        self.assertIn("innerHeight-8", source_filter)

    def test_the_manage_page_is_ordered_by_what_you_do_first(self):
        # 只看管理页那一段：同样的标题在别的页面上也出现过，全页搜索会命中错的那个。
        page = self.page
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowItems(")]
        order = [body.index(f'<h3>{heading}')
                 for heading in ("添加关注", "关注列表", "凭据")]
        self.assertEqual(order, sorted(order), "管理页分区顺序应为 加关注 → 关注列表 → 凭据")

    def test_counts_are_a_footnote_not_their_own_section(self):
        # 四个数字单独占一张通栏卡片，在宽屏上就是一条空长条。
        page = self.page
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowItems(")]
        self.assertNotIn("<h3>内容", body)
        self.assertIn("条未看", body)

    def test_the_page_uses_two_columns_so_the_width_is_not_wasted(self):
        page = self.page
        rule = page[page.index(".followmanage{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("grid-template-columns:minmax(0,1fr)", rule)
        self.assertPageContains(".followmanage>.runtimegate{grid-column:1/-1")

    def test_sections_have_a_frame_but_their_rows_do_not(self):
        """反模式是卡片**套**卡片，不是「不要任何容器」。

        上一版把两者混为一谈，做成了没有可读性的裸列表——而同一份文档明确警告过
        不要因为躲开那些默认套路就做出一个无设计的模板。所以：分区有框，
        框里的行只用分隔线。
        """
        page = self.page
        section = page[page.index(".fsec{"):]
        section = section[:section.index("}")]
        self.assertIn("border:1px solid", section)
        self.assertIn("border-radius", section)
        self.assertIn("background:var(--surface)", section)

        self.assertNotIn(".fcard{", page)
        self.assertNotIn(".fsource{", page,
                         "旧来源卡片规则会给新行重新套上边框和圆角")
        row = page[page.index(".frow{"):]
        row = row[:row.index("}")]
        self.assertIn("border-bottom:1px solid", row)
        self.assertNotIn("border-radius", row)

    def test_narrow_column_rows_can_actually_shrink(self):
        """grid 项默认 `min-width:auto`，最宽的一行会把整列撑出容器。

        实测右栏 320px，凭据行却量到 438px，整页横向溢出 119px。容器和每一项
        都要显式 `min-width:0`。
        """
        page = self.page
        rule = page[page.index(".frows{"):]
        self.assertIn("min-width:0", rule[:rule.index("}")])
        self.assertPageContains(".frows>*{min-width:0}")

    def test_credential_states_are_not_all_the_same_colour(self):
        """缺凭据是待办，配好了是完成态。同色就等于没说。"""
        page = self.page
        colours = {}
        for name in ("done", "req", "opt", "none"):
            rule = page[page.index(f".fcstate.{name}"):]
            colours[name] = rule[:rule.index("}")]
        self.assertNotEqual(colours["done"], colours["req"],
                            "已配置和缺凭据必须能一眼分开")
        self.assertNotEqual(colours["done"], colours["none"])

    def test_suggestions_come_from_the_real_library_and_are_clickable(self):
        """「猜你喜欢」取账本里真实存在的创作者，点一下直接拿去查。

        不用 placeholder：占位文字点不了，还占着输入框的语义。
        """
        self.assertPageContains("function followSuggestionChips(")
        self.assertPageContains("followData.suggestions")
        self.assertPageContains("item.visits")
        self.assertPageContains("data-follow-guess")
        # 不能退回本地文件的创作者：那是「他有谁的文件」，不是「他喜欢谁」。
        # 只看关注管理那一段——首页搜索推荐用 facets.creators 是另一回事，合法。
        page = self.page
        block = page[page.index("function followSuggestionChips("):
                     page.index("function wireFollowItems(")]
        self.assertNotIn("facets.creators", block)
        self.assertPageContains("form.requestSubmit()")
        page = self.page
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowItems(")]
        self.assertNotIn("placeholder=", body, "输入框不再放占位文字")

    def test_every_credential_state_sits_in_the_same_column(self):
        """summary 是 .frow 的 flex 子项，默认不撑满整行——于是有折叠体的那几行
        状态贴在名字后面，没折叠体的却靠右，同一列两种对齐。"""
        page = self.page
        rule = page[page.index(".fcred summary{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("flex:1 1 auto", rule)
        self.assertIn("min-width:0", rule)
        # 两个分支必须用同一个状态类，否则同一列出现两套样式和两种对齐。
        self.assertNotIn('<span class="fmeta">${esc(label)}</span>', page)
        self.assertPageContains('<span class="fcstate none">${esc(label)}</span>')
        state = page[page.index(".fcstate{"):]
        self.assertIn("margin-left:auto", state[:state.index("}")])
        # 折叠/展开两种几何下 summary 的可用宽度必须一致，否则状态列差一个 gap。
        self.assertPageContains("details.fcred{display:block}")

    def test_the_add_box_carries_no_standing_how_to_prose(self):
        # 空态保留状态和结果去向；操作说明常驻就是噪音。
        page = self.page
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowItems(")]
        self.assertNotIn("要一次加多个就每行一条", body)
        self.assertNotIn("把链接或名字粘进上面的输入框", body)
        self.assertIn("emptyState('rss','还没有关注来源'", body)
        self.assertIn("关注来源及其检查状态会显示在这里。", body)

    def test_the_panel_cites_the_registered_report_design_source(self):
        self.assertPageContains("docs/reference-sources.json")
        self.assertPageContains("vercel-report-design")
        self.assertNotIn("e3d624baaf29dc1fc645aff3e38f03e564d2d6b1", self.page)

    def test_the_type_scale_has_no_arbitrary_in_between_sizes(self):
        """同一份文档点名的另一条：细小灰字加随意字号。

        管理页只用 14 正文 / 13 次要 / 12 元信息三档。这三档现在是全站刻度里的
        `--fs-md` / `--fs-sm` / `--fs-xs`，不再是写死的像素——面板当初收敛出的那三档
        本来就该是全站的下三档，各写各的迟早会漂开。所以这里断言的是「只用这三个
        token，且一个字面像素都不留」。
        """
        page = self.page
        # 查找结果现在属于同一个管理分区，所以字号检查也要覆盖这一段，直到关注页脚。
        block = page[page.index("/* ── 关注管理页 ──"):page.index("/* 关注页底部")]
        self.assertEqual(re.findall(r"font-size:[\d.]+px", block), [],
                         "面板里不该再有写死的字号")
        steps = sorted({m for m in re.findall(r"font-size:var\(--fs-([a-z0-9]+)\)", block)})
        self.assertEqual(steps, ["md", "sm", "xs"], f"字号档位应只有三档，实际 {steps}")

    def test_credential_rows_say_whether_they_are_needed_at_all(self):
        # 「未配置」本身不是信息：要说清需不需要、需要什么、去哪儿拿。
        self.assertPageContains("required:['需要'")
        self.assertPageContains("none:['不需要'")
        self.assertPageContains("blocked:['接不进来'")
        self.assertPageContains("row.where")
        self.assertPageContains("row.howto")

    def test_the_page_says_where_the_credential_actually_lands(self):
        # 从 Mac 浏览 Windows 实例时，凭据落在 Windows 上——不能写成「本机」。
        self.assertPageContains("运行 Peach 的那台机器")
        self.assertPageContains("Windows 上不收紧文件权限")
        self.assertPageContains("row.path")
        self.assertPageContains("row.world_readable")

    def test_credential_explanation_uses_an_accessible_viewport_clamped_tooltip(self):
        self.assertPageContains('class="fdescinfo" data-fdesc-tooltip')
        self.assertPageContains('aria-label="凭据存放位置说明"')
        self.assertPageContains('id="follow-credential-tooltip" role="tooltip" hidden')
        self.assertPageContains("tooltipTrigger.setAttribute('aria-describedby',tooltip.id)")
        self.assertPageContains("tooltipTrigger.removeAttribute('aria-describedby')")
        self.assertPageContains("event.key==='Escape'")
        tooltip = self.page[self.page.index(".fdescpop{"):]
        tooltip = tooltip[:tooltip.index("}")]
        self.assertIn("position:fixed", tooltip)
        self.assertIn("max-width:min(250px,calc(100vw - 16px))", tooltip)
        self.assertIn("pointer-events:none", tooltip)
        self.assertNotIn("340px", tooltip)
        self.assertPageContains("innerWidth-box.width-8")

    def test_author_aliases_use_the_real_geist_collapse_motion(self):
        self.assertPageContains(".fcollapse{overflow:hidden;transition:height .2s ease-in-out}")
        self.assertPageContains("summary.setAttribute('aria-controls',body.id)")
        self.assertPageContains("summary.setAttribute('aria-expanded',String(expanded))")
        self.assertPageContains("body.inert=!expanded")
        self.assertPageContains("body.inert=true")
        self.assertPageContains("body.style.height=body.scrollHeight+'px'")
        self.assertPageContains(".faliasmanager>summary::before")
        self.assertPageContains("transition:transform .2s ease-in-out")

    def test_follow_source_icons_fail_back_to_plain_text(self):
        icons = self.page.split("const SOURCE_ICONS={", 1)[1].split("};", 1)[0]
        self.assertIn("kemono.cr/assets/favicon-", icons)
        self.assertIn("pawchive.pw/static/favicon.png", icons)
        self.assertNotIn("kemono.cr/favicon.ico", icons)
        self.assertPageContains('onerror="this.remove()"')

    def test_follow_watch_filters_use_the_source_identity(self):
        self.assertPageContains("if(followAuthor&&source.author_key!==followAuthor)return false;")
        self.assertPageContains("if(followProvider&&source.provider!==followProvider)return false;")
        self.assertPageContains('class="tier followauthors"')
        self.assertPageContains('class="tagbar followfilters"')
        self.assertPageContains('class="pill sourcepill" data-follow-provider=')
        self.assertPageLacks("内容标签目前由 ${")
        self.assertPageContains("const rankedTags=[...tagCounts].sort((a,b)=>b[1]-a[1])")
        self.assertPageContains("const topTagRows=rankedTags.slice(0,20)")
        self.assertPageContains("topTagRows.push([tag,tagCounts.get(tag)])")

    def test_follow_tags_are_multi_select_and_use_rule34_property_colours(self):
        self.assertPageContains("let followAuthor='',followProvider='',followTags=new Set()")
        self.assertPageContains("![...followTags].every(tag=>")
        self.assertPageContains("aria-pressed=\"${followTags.has(key)}\"")
        self.assertPageContains(".r34-artist")
        self.assertPageContains(".r34-character")
        self.assertPageContains(".r34-copyright")
        self.assertPageContains(".r34-metadata")
        self.assertPageContains('[class*="r34-"][aria-pressed="true"]')

    def test_follow_cards_use_author_avatars_and_open_details_inside_peach(self):
        self.assertPageContains("return followCard(group,siblings)")
        self.assertPageContains('title="作者头像">${followAuthorAvatar(authorSources)}')
        self.assertNotIn(
            'class="mav fsourceavatar" title="${esc(item.provider_label)}">${sourceIcon(item.provider)}',
            self.page,
        )
        self.assertPageContains("async function openFollowDetail(id,push=true,mediaIndex=null,preserveReturn=false)")
        self.assertPageContains("const src=item.playable?`/follow-stream?id=${item.id}${selectedMedia?")
        self.assertPageContains('data-follow-detail="${item.id}"')
        self.assertPageContains("route(`/follow/item/${item.id}`)")
        self.assertPageContains('class="sgrid followdetailgrid${collection||embeddedQueue?\' mixgrid\':\'\'}"')
        self.assertPageContains('class="followorigin" href="${esc(item.url)}" target="_blank"')
        self.assertPageContains('title="打开来源页面" aria-label="打开来源页面"')
        self.assertNotIn('打开来源页面</a>', self.page)
        self.assertPageContains(".followdetailtitle{display:flex;gap:5px")
        self.assertPageContains(".fnote.followmedianote{margin:18px 0 8px}")
        self.assertPageContains("followAuthorAvatar(authorSources)")
        self.assertPageContains("followTagChip(item,tag,'button')")
        self.assertPageContains(".followdetailtags .tg{max-width:none")
        self.assertPageContains("const postedBy=item.author&&foldName(item.author)!==foldName(author)")
        self.assertPageContains("openFollowDetail(id);")
        self.assertNotIn('class="cardopenhit" href=', self.page)
        self.assertNotIn('class="t cardtitle" href=', self.page)
        self.assertNotIn('class="fcollectionthumb" href=', self.page)
        self.assertPageContains("route(followDetailReturnPath||'/follow')")
        self.assertPageContains(".followitem a{text-decoration:none}")

    def test_follow_video_uses_the_shared_videojs_player_and_quality_control(self):
        self.assertPageContains('class="video-js vjs-big-play-centered" controls playsinline preload="metadata"')
        self.assertPageContains("if(followVideo){")
        self.assertPageContains("const followPlayer=mountDetailPlayer(item,followVideo,false,{")
        self.assertPageContains("source:{src,type:selectedMedia?.media_type||item.media_type||'video/mp4'}")
        self.assertPageContains("function mountPlayerQualityControl(player,video,fallbackHeight=0)")
        self.assertPageContains('aria-label="播放器设置"')
        self.assertPageContains("data-player-quality-badge")
        self.assertPageContains("currentTimeDisplay:true,timeDivider:true")
        self.assertPageContains("levels[index].enabled=selected==='auto'||selected===String(index)")
        self.assertPageContains("const stopFollowAmbient=mountPlayerAmbient(followVideo)")
        self.assertPageContains("followPlayer?.one?.('dispose',stopFollowAmbient)")
        self.assertPageContains("mountPlayerTheaterControl(player,root)")
        self.assertPageContains("wireFollowTelemetry(item,followVideo)")
        self.assertPageContains("api('/api/follow/play'")
        self.assertPageContains("api('/api/follow/activity'")

    def test_follow_detail_save_keeps_the_button_after_the_async_request(self):
        self.assertPageContains("const button=event.currentTarget;")
        self.assertPageContains("write(button,'/api/follow/save',{item:item.id},()=>{")
        self.assertPageContains("button.innerHTML=icon('check')")
        self.assertPageContains("button.setAttribute('aria-label','已保存')")
        self.assertPageLacks("event.currentTarget.innerHTML=icon('check')")

    def test_follow_image_collections_use_buttons_dots_and_arrow_keys(self):
        self.assertPageContains('class="followimagearrow prev"')
        self.assertPageContains('class="followimagedots" role="group"')
        self.assertPageContains('data-follow-image-item="${image.index}"')
        self.assertPageContains("imageDots.length&&(e.key==='ArrowLeft'||e.key==='ArrowRight')")
        self.assertPageContains("openFollowDetail(item.id,false,+index,true)")
        self.assertPageContains(".followimagedots button[aria-current=\"true\"]")
        self.assertPageContains("function alignFollowImageControls()")
        self.assertPageContains("const renderedWidth=Math.min(box.width,box.height*ratio)")
        self.assertPageContains("--follow-image-arrow-inset")

    def test_follow_detail_keeps_filter_context_and_clears_initial_loading(self):
        self.assertPageContains("async function openFollow(push=true,renderForDetail=false)")
        self.assertPageContains("const surface=claimSurface(renderForDetail?surfacePath():'/follow')")
        self.assertPageContains("if(!surfaceCurrent(surface))return")
        self.assertPageContains("await openFollow(false,true);await openFollowDetail(+parts[2],false)")
        self.assertPageContains("const followList=$('#stats').querySelector('.followlist')")
        self.assertPageContains("if(followList)followList.before($('#stage'))")
        self.assertPageContains("if(stage.parentElement!==main)main.insertBefore(stage,combo)")

    def test_follow_filters_put_all_first_and_sources_are_icon_only(self):
        self.assertPageContains("const FOLLOW_FILTERS=[['','全部'],['new','未看']")
        self.assertPageContains('title="${esc(label)}" aria-label="来源：${esc(label)}">${sourceIcon(key)}</button>')
        watch = self.page.split("function renderFollow(){", 1)[1].split(
            "function followBackfillState", 1)[0]
        self.assertNotIn("全部来源", watch)
        self.assertNotIn("全部标签", watch)
        self.assertPageContains("followProvider=followProvider===button.dataset.followProvider?'':button.dataset.followProvider")
        self.assertPageContains(
            "if(followTags.has(tag))followTags.delete(tag);else followTags.add(tag)")

    def test_follow_horizontal_rails_are_wired_after_each_render(self):
        self.assertPageContains("wireDrag($('#stats').querySelector('.followauthors'))")
        self.assertPageContains("wireDrag($('#stats').querySelector('.followfilters'))")
        self.assertPageContains(".followauthors{padding:3px 0 10px")
        self.assertPageContains(".followfilters::-webkit-scrollbar{display:none}")

    def test_credentials_are_typed_into_the_page_not_into_a_file_by_hand(self):
        self.assertPageContains('data-cred-form=')
        self.assertPageContains("'/api/follow/credential'")
        self.assertPageContains('type="password"')
        self.assertPageContains("const fields=(row.needs||[]).map")
        # 值只往磁盘走：保存后清空输入框，页面上再也看不到。
        self.assertPageContains("form.reset();await openFollowManage(false)")
        self.assertPageContains("data-cred-clear")

    def test_only_a_missing_required_credential_demands_attention(self):
        # 可选的、不需要的、站点接不进来的都收起来；永远展开就是永久噪音。
        self.assertPageContains("row.requirement==='required'&&!configured")
        self.assertPageContains("${needsAttention?' open':''}")

    def test_the_watch_page_does_not_carry_source_management(self):
        # 输入框、移除、凭据都只属于管理页；看的那页保持干净。
        page = self.page
        watch = page[page.index("function renderFollow(){"):page.index("async function openFollow")]
        for management in ("followAdd", "data-follow-remove", "fcreds", "data-follow-bulk"):
            if management in watch:
                self.fail(f"看的那一页不应出现管理控件：{management!r}")

    def test_times_are_rendered_in_the_viewer_timezone_not_raw_utc(self):
        # 账本存 UTC；直接把那串字面量印出来，UTC+8 的人看到的每个时间都早 8 小时。
        self.assertPageContains("function localTime(iso)")
        self.assertPageContains("new Date(text)")
        self.assertPageContains("when.getHours()")
        page = self.page
        body = page[page.index("function followWhen("):page.index("function followBadges(")]
        self.assertNotIn(".replace('T',' ').slice(0,16)", body)

    def test_approximate_timestamps_keep_precision_without_the_visible_prefix(self):
        # 精度留在 API，列表按用户要求不显示「约」。
        body = self.page[self.page.index("function followWhen("):
                         self.page.index("function followBadges(")]
        self.assertNotIn("约 ${text}", body)
        self.assertIn("return text", body)

    def test_release_variant_rows_show_when_not_a_meaningless_kind(self):
        self.assertPageContains("if(!label&&group.is_release)label=localTime(item.published_at).slice(5,10)")

    def test_release_rows_show_the_reply_body_not_the_thread_title(self):
        self.assertPageContains("const body=group.is_release")
        self.assertPageContains("'（仅附件）'")

    def test_thread_activity_is_not_called_a_version(self):
        self.assertPageContains("group.is_release?`${group.variants.length+1} 条动态`")

    def test_cross_site_duplicates_are_shown_as_another_source(self):
        self.assertPageContains("另见 ")
        self.assertPageContains("fbadge dup")

    def test_wip_has_its_own_badge(self):
        self.assertPageContains('<span class="fbadge wip">WIP</span>')

    def test_network_check_is_an_explicit_button_not_an_auto_refresh(self):
        self.assertPageContains("data-follow-check")
        # 「换一批」自动刷新绝不能顺手触发一次联网检查。
        self.assertPageContains(
            "if(location.pathname==='/follow'||location.pathname==='/follow-manage')return;")

    def test_every_entered_state_can_be_left_again(self):
        self.assertPageContains("""item.status==='seen'||item.status==='ignored'""")
        self.assertPageContains('data-to="new" title="恢复未看" aria-label="恢复未看"')

    def test_rule34_sources_carry_content_first_tags(self):
        """Rule34Video 与 Rule34.xxx 都提供标签，载体标签不挤占内容标签。

        Rule34.xxx 是空格分隔串，Rule34Video 是保留空格的列表；两者都从
        `metadata_json` 投影，原始证据不被改写。
        """
        class _Item:
            def __init__(self, metadata):
                self.metadata = metadata

        tags = web_follow._item_tags(
            _Item({"tag": "lazyprocrastinator",
                   "tags": "lazyprocrastinator 1girls animated sound lazyprocrastinator"}))
        # 作者手柄本身不算标签：按作者筛已经有专门的筛选条，重复出现没有信息量。
        self.assertEqual(tags, ["1girls"])
        video_tags = web_follow._item_tags(_Item({
            "tags": ["deep throat", "3D", "3d_animation", "breast squeeze"],
            "categories": ["2D", "Final Fantasy"],
        }))
        self.assertEqual(video_tags,
                         ["deep throat", "breast squeeze", "Final Fantasy"])
        self.assertEqual(web_follow._item_tags(_Item({})), [])
        self.assertEqual(web_follow._item_tags(_Item({"tags": "   "})), [])
        # rule34.xxx 旧行存的是 HTML 转义形态；出口归一后与反转义的新写法
        # 是同一个身份，脏/净并存的重复项也合并成一个。
        legacy = web_follow._item_tags(
            _Item({"tags": "miqo&#039;te y&#039;shtola miqo&#039;te"}))
        self.assertEqual(legacy, ["miqo'te", "y'shtola"])
        # 热门帖能带上百个标签，整串发下去会把筛选条撑爆。
        many = _Item({"tags": " ".join(f"t{n}" for n in range(200))})
        self.assertEqual(len(web_follow._item_tags(many)), web_follow.MAX_ITEM_TAGS)

    def test_the_author_key_merges_one_person_across_sites(self):
        """归组判据：实体优先，其次名字归一化，绝不模糊匹配。

        把两个碰巧相似的名字并成一个人，比让用户自己看到两行严重得多——
        前者会把别人的更新混进来且很难发现。
        """
        def key(**row):
            row.setdefault("entity_id", None)
            row.setdefault("id", 1)
            row.setdefault("ref", "")
            row.setdefault("provider", "rule34video")
            row.setdefault("metadata_json", "{}")
            return web_follow.author_key(row)

        # 「· 服务名」只说明他在哪个平台连载，不是身份的一部分。
        same = {key(label="LazyProcrastinator · fanbox"),
                key(label="lazyprocrastinator"),
                key(label="Lazy-Procrastinator")}
        self.assertEqual(len(same), 1, f"应归成同一个作者，实际 {same}")
        # 实体绑上之后以实体为准，名字再怎么写都不影响。
        self.assertEqual(key(label="随便写", entity_id=7), "entity:7")
        self.assertEqual(key(label="別の人", entity_id=7),
                         key(label="LazyProcrastinator", entity_id=7))
        # 不同的人不许并。
        self.assertNotEqual(key(label="bewyx"), key(label="bewyx2"))
        self.assertEqual(
            key(label="Lazy Procrastinator Collection", provider="f95zone"),
            key(label="lazyprocrastinator"),
        )
        self.assertEqual(
            key(label="unrelated", provider="f95zone",
                metadata_json='{"author_key":"lazyprocrastinator"}'),
            "name:lazyprocrastinator",
        )
        # 名字为空时退回来源 id，不能让所有空名字挤成一组。
        self.assertNotEqual(key(label="", id=1), key(label="", id=2))

    def test_avatars_only_come_from_providers_that_actually_serve_one(self):
        """头像按 peach-reference-evidence：实测拿得到才给，取不到写「未取得」。

        2026-08-27 实测 `https://kemono.cr/icons/fanbox/30917150` → 302 →
        `img.kemono.cr`，200 `image/webp` 160×160；pawchive.pw 同路径 200。
        rule34 系没有可用样本可测，所以不给 URL——不猜一个路径。
        """
        self.assertEqual(web_follow._avatar_url("kemono", "fanbox/30917150"),
                         "https://kemono.cr/icons/fanbox/30917150")
        self.assertEqual(web_follow._avatar_url("pawchive", "fanbox/30917150"),
                         "https://pawchive.pw/icons/fanbox/30917150")
        self.assertEqual(
            web_follow._official_avatar_url("kemono", "fanbox/30917150"),
            "/follow-avatar?service=fanbox&id=30917150",
        )
        for provider, ref in (("rule34video", "1290582"),
                              ("rule34xxx", "lazyprocrastinator"),
                              ("f95zone", "50685"),
                              ("kemono", "no-slash")):
            self.assertIsNone(web_follow._avatar_url(provider, ref),
                              f"{provider} 没有实测过的头像来源，不该猜一个")

    def test_a_missing_evidence_archive_is_shown_not_swallowed(self):
        # 证据未存档现在并进那块检查报告，不再单独弹一层——但话不能少说。
        self.assertPageContains("候选已入库，但这一次的原始响应没有留档")
        self.assertPageContains("r.evidence_error")

    def test_a_check_says_what_it_actually_found(self):
        """检查完必须报结果。

        用户的原话是「完全没返回任何结果」：接口每条来源都回了
        added/updated/not_modified/error，而界面拿到之后只是整页重画，
        那些数字一个都没露面，看起来就是点了一下什么都没发生。

        「没有更新」和「检查失败」在界面上都像「什么都没发生」，但一个不用管，
        另一个再不管就会一直漏更新——所以失败必须单独列出来并带上原因。
        回执走 toast（非阻塞、自动消失），失败明细留在页内持久行上。
        """
        self.assertPageContains("function followCheckToast(report)")
        self.assertPageContains("function followCheckFailNote(report)")
        # 重画会把结果冲掉，所以先存再画。
        self.assertPageContains("followCheckReport=result;")
        self.assertPageContains("${followCheckReport?followCheckFailNote(followCheckReport):''}")
        for needle in ("新增 <b>", "更新 <b>", "个来源没有更新", "没有任何更新",
                       "个失败", "fcheckfail", "没有更多历史内容",
                       "data-follow-report-dismiss"):
            self.assertPageContains(needle)
        # 失败要说清是哪个站，不能让用户去猜 `rule34xxx` 是什么。
        self.assertPageContains("row.provider_label||row.provider")
        # 回执带一个具名的后续动作：光摆数字会让人去点「…条详情」那半句，
        # 文案里不再留悬空的「详情」，去看更新作为显式按钮接住这个意图。
        self.assertPageContains("action:{label:'去看更新',run:()=>openFollow()}")
        self.assertPageContains("if(action)item.querySelector('.tact')")
        self.assertPageLacks("条详情")

    def test_follow_bulk_actions_are_buttons_not_inline_links(self):
        """批量标记已看／全部忽略是 2292 条级别的操作，不能长得像行内文字链接。

        裸蓝字链接和旁边的计数文本混在一行里，看起来像一句说明文字；
        分不清哪半句是统计、哪半句可以点。改成 .fbtn 次级按钮——与本页
        「检查全部／去看更新」同一套控件语言——按钮的边界让「这会改状态」
        在点击之前就看得见。
        """
        self.assertPageContains('<button class="fbtn" data-follow-bulk="seen">全部标记已看</button>')
        self.assertPageContains('<button class="fbtn" data-follow-bulk="ignored">全部忽略</button>')
        self.assertPageLacks('class="flink" data-follow-bulk')
        # 不另起一行：按钮内联在计数行里（用户回执）。
        self.assertPageContains('.fbulk{display:inline-flex;gap:8px;margin-left:auto}')

    def test_sources_by_the_same_author_are_one_block(self):
        """同一个作者在几个站上是几条来源、一个人。

        用户截图里 `LazyProcrastinator · fanbox` 出现两次（Kemono / Pawchive）、
        `lazyprocrastinator` 出现两次（Rule34Video / Rule34.xxx），四行读起来像四个人。
        归组用后端算好的 `author_key`，前端不二次猜。
        """
        self.assertPageContains("function followAuthorGroups(sources)")
        self.assertPageContains("source.author_key")
        self.assertPageContains("followAuthorGroups(sources).map(followAuthorBlock)")
        # 组标题用作者本人的名字：四条来源合成一组之后还挂着其中一条的平台后缀，
        # 等于说这一组只属于 fanbox，正是这次要消掉的误读。
        self.assertPageContains("function followAuthorName(group)")
        self.assertPageContains("const name=followAuthorName(group);")
        self.assertPageContains("const official=group.find(source=>source.official_avatar_url);")
        self.assertPageContains("if(officialName)return officialName;")
        # 取不到图片时回退作者首字母；不能从来源标签切出中文“初”“一”。
        self.assertPageContains("function followAvatarInitial(group)")
        self.assertPageContains('title="没有可用头像"')
        avatar = self.page[self.page.index("function followAuthorAvatar(group)"):]
        avatar = avatar[:avatar.index("function followAuthorBlock")]
        self.assertIn("followAvatarInitial(group)", avatar)
        self.assertIn("source.avatar_url", avatar)
        self.assertIn("source.official_avatar_url", avatar)
        self.assertIn("data-fallback", avatar)

    def test_discovered_sources_keep_the_search_term_as_the_author_identity(self):
        self.assertPageContains('data-author="${esc(c.author||\'\')}"')
        self.assertPageContains("author:input.dataset.author")

    def test_credential_dependent_media_is_called_out(self):
        self.assertPageContains("媒体链接需要 F95 登录会话解析")
        self.assertPageContains("已保存 F95 登录会话，等待下次检查重新解析资源")
        self.assertPageContains("followCredentialProviders=new Set")
        self.assertPageContains("api('/api/follow/credentials').catch")
        self.assertPageContains("个外部文件页；视频列表未取得")
        self.assertPageContains("function followResourceLinks(item)")
        self.assertPageContains('class="followresources"')
        self.assertPageContains("${followResourceLinks(item)}")

    def test_follow_external_links_have_a_real_icon_and_no_underlines(self):
        self.assertPageContains('<symbol id="i-external-link"')
        self.assertPageContains("icon('external-link')")
        self.assertPageContains(".followresources a:hover")
        self.assertPageContains("text-decoration:none")

    def test_loading_semantics_and_known_copy_says_followed(self):
        self.assertPageContains("@keyframes geist-spinner-opacity")
        self.assertPageContains("@keyframes geist-loading-dot")
        self.assertPageContains("spinnerHtml('查找中')")
        self.assertPageContains("loadingDotsHtml('抓取中…')")
        self.assertPageContains("c.known?'已经关注':c.evidence")
        self.assertPageLacks("已经在追")

    def test_follow_styles_exist_for_the_card_surface(self):
        for selector in (".followlist{", ".followitem{", ".fbadge{", ".followqueue"):
            self.assertPageContains(selector)

    def test_follow_cards_reuse_home_cards_hover_actions_and_mix_stacks(self):
        self.assertPageContains("function followVideoItems(group)")
        self.assertPageContains("item.playable&&item.media_kind==='video'")
        self.assertPageContains('class="card followitem${isMix?\' collection\':\'\'}${imageView?\' imagecard\':\'\'}"')
        self.assertPageContains("isMix?'mixstack '")
        self.assertPageContains('class="mixbadge" data-follow-collection=')
        self.assertPageContains("${mixCount} 个${mixKind}")
        self.assertPageContains("function followEmbeddedQueueHtml(item,mediaIndex)")
        self.assertPageContains("data-follow-media-item=")
        self.assertPageContains("const collection=!embedded.length&&group&&followVideoItems(group).length>1?group:null")
        self.assertPageContains("const items=followVideoItems(group)")
        self.assertPageContains(".factions{position:absolute;right:10px;top:10px")
        self.assertPageContains("@media (hover:hover) and (pointer:fine){.followitem:hover .factions")
        self.assertPageContains("function followQueueHtml(group,itemId)")
        self.assertPageContains('data-follow-queue-item="${item.id}"')
        self.assertPageContains("openFollowDetail(+button.dataset.followCollection)")

    def test_follow_reuses_entity_media_buttons_at_the_far_left_without_separator(self):
        self.assertPageContains("const followMediaKinds=group=>")
        self.assertPageContains("function followItemMediaKinds(item)")
        self.assertPageContains("const item=followItemForMedia(group)")
        self.assertPageContains('class="followmediaicons"')
        self.assertPageContains('class="entitymediatoggle" type="button" data-follow-media="videos"')
        self.assertPageContains('data-follow-media="videos"')
        self.assertPageContains('data-follow-media="images"')
        self.assertPageLacks('class="insightswitch followmediaswitch"')
        self.assertPageLacks("params.set('media-ui','switch')")
        self.assertPageContains("params.set('author',followAuthor)")
        self.assertPageContains("route(followViewPath());renderFollow()")
        self.assertPageContains("const preferredKind=followMediaView==='images'?'image':'video'")
        watch = self.page.split("function renderFollow(){", 1)[1].split(
            "function followBackfillState", 1)[0]
        self.assertIn(
            'class="tagbar followfilters" aria-label="关注筛选">${followMediaControl(mediaCounts)}${FOLLOW_FILTERS.map',
            watch,
        )
        self.assertNotIn(
            '<span class="sep" aria-hidden="true"></span>${followMediaControl(mediaCounts)}',
            watch,
        )
        self.assertPageContains("followMediaView==='images'?' followphotowall':''")
        self.assertPageContains(".followlist.followphotowall{display:block;column-count:5")
        self.assertPageContains(".followitem.imagecard .followvisual .pic>img{position:relative")

    def test_external_file_pages_do_not_default_to_video_and_paging_actions_share_one_row(self):
        self.assertPageContains("else if(item.media_kind==='image'||item.media_kind==='video')kinds.add(item.media_kind)")
        self.assertPageLacks("else kinds.add(item.media_kind==='image'?'image':'video')")
        self.assertPageContains('class="followpagination"')
        self.assertPageContains("${icon('plus')}加载更多")
        self.assertPageContains("${icon('history')}抓更早的一页")
        self.assertPageContains("spinnerHtml('加载更多')")
        self.assertPageContains("loadingDotsHtml('抓取中…')")

    def test_follow_management_list_has_routed_sorting(self):
        self.assertPageContains('data-follow-sort aria-label="关注列表排序"')
        self.assertPageContains('<option value="checked"')
        self.assertPageContains('<option value="name"')
        self.assertPageContains('<option value="sources"')
        self.assertPageContains("followManageSort=['checked','name','sources'].includes(requested)?requested:'checked'")
        self.assertPageContains("return groups.sort((a,b)=>{")

    def test_mix_and_follow_queues_stay_below_media_with_details_on_the_right(self):
        self.assertPageContains('grid-template-areas:"media side" "queue queue"')
        self.assertPageContains('.sgrid.mixgrid>.vwrap{grid-area:media}')
        self.assertPageContains('.sgrid.mixgrid>.side{grid-area:side;background:var(--detail-surface)}')
        self.assertPageContains('.sgrid.mixgrid>.mixqueue{grid-area:queue;max-height:360px')
        self.assertPageContains('grid-template-areas:"media" "side" "queue"')
        self.assertPageContains('background:var(--detail-surface)')
        self.assertPageContains("const kindLabel={mix:'Mix',parts:'分卷',playlist:'播放列表'}")
        self.assertPageContains('<h2>视频合集</h2>')
        self.assertPageContains('<h2>多媒体</h2>')
        self.assertPageContains('.sgrid.mixgrid>.mixqueue .mixlist{display:grid;grid-auto-flow:column')
        self.assertPageContains('.sgrid.mixgrid>.vwrap>.gate{height:100%;aspect-ratio:auto}')
        self.assertPageContains('.sgrid.mixgrid>.mixqueue .mixqueuehead>div:first-child{min-width:0}')
        self.assertPageContains('.sgrid.mixgrid>.mixqueue .mixqueueactions{grid-column:2;grid-row:1;align-self:center}')
        self.assertPageContains("wireDrag($('#stage').querySelector('.mixlist'))")
        self.assertPageContains("followdetailmedia${selectedKind==='image'?' image':''}")
        self.assertPageContains('.followdetailmedia.image{min-height:0;background:')

    def test_follow_uses_the_global_multi_select_mode(self):
        self.assertPageContains("const selected=new Set(),followSelected=new Set();")
        self.assertPageContains("function toggleFollowSelection(id,range=false)")
        self.assertPageContains("path==='/tags'||path==='/follow'")
        self.assertPageContains('data-follow-batch="save"')
        self.assertPageContains("const body=action==='save'?{items}:{items,to:action};")

    def test_ignore_actions_do_not_reuse_the_close_icon(self):
        self.assertPageContains('<symbol id="i-eye-off"')
        self.assertPageContains('data-follow-batch="ignored" hidden><svg viewBox="0 0 24 24"><use href="#i-eye-off"')
        self.assertPageContains('data-follow-detail-status="ignored" aria-label="忽略" title="忽略"')
        self.assertPageContains("${icon('eye-off')}</button>")

    def test_the_check_button_stays_visible_on_a_narrow_viewport(self):
        # 管理入口不再混进横滚筛选条；390 宽下始终留在标题右侧。
        self.assertPageContains(".followhead{display:flex;align-items:center;justify-content:space-between")
        self.assertPageContains('@media (max-width:640px){.followhead{align-items:center}')

    def test_manage_follow_is_a_geist_action_not_a_filter_pill(self):
        self.assertPageContains('class="fbtn primary fcheck" data-follow-manage')
        rule = self.page[self.page.index(".follow .fcheck{"):
                         self.page.index("}", self.page.index(".follow .fcheck{"))]
        self.assertNotIn("--pill-radius", rule)
        self.assertNotIn("height:40px", rule)


if __name__ == "__main__":
    unittest.main()
