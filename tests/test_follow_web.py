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

from peach import follow_store, web_follow
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
              semantics="work", label="LazyProcrastinator"):
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
                provider=provider, ref=ref, label=label,
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
        web_follow.build_connector = lambda provider, **kwargs: _Recorder()
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
                            extra={"tags": "miqo&#039;te y&#039;shtola barnabas&#039;_mother",
                                   "tag_types": {"miqo&#039;te": "general",
                                                 "y&#039;shtola": "general",
                                                 "barnabas&#039;_mother": "general"}}),
        ), provider="rule34xxx", ref="final_fantasy")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["tags"], ["miqo'te", "y'shtola", "barnabas'_mother"])
        self.assertEqual(item["tag_types"],
                         {"miqo'te": "general", "y'shtola": "general",
                          "barnabas'_mother": "general"})
        self.assertEqual(item["detail_tags"],
                         ["miqo'te", "y'shtola", "barnabas'_mother"])
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
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "f95zone.json").write_text(
            '{"cookie": "xf_session=saved"}', encoding="utf-8")
        self._seed(candidates=(FollowCandidate(
            provider="f95zone", external_id="21435167", title="Image set",
            url="https://f95zone.to/threads/160190/post-21435167",
            media_url="https://pixeldrain.com/l/verified",
            thumb_url="https://attachments.f95zone.to/2026/08/one.jpg",
            extra={"links": ["https://pixeldrain.com/l/verified"],
                   "media_needs_credential": True,
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
        self.assertTrue(item["media_needs_credential"])
        self.assertTrue(all("url" not in media for media in item["media_items"]))

    def test_saved_f95_session_forces_one_reparse_instead_of_accepting_304(self):
        source_id = self._seed(candidates=(FollowCandidate(
            provider="f95zone", external_id="21435168", title="Image set",
            url="https://f95zone.to/threads/160190/post-21435168",
            extra={"media_needs_credential": True},
        ),), provider="f95zone", ref="160190", semantics="release")
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "f95zone.json").write_text(
            '{"cookie": "xf_session=saved"}', encoding="utf-8")
        with self.contract.database.write_transaction() as connection:
            connection.execute(
                "UPDATE follow_source SET etag='old',last_modified='yesterday' WHERE id=?",
                (source_id,),
            )
        conditional = []

        class _Recorder:
            def fetch(self, ref, *, etag=None, last_modified=None, page=0):
                conditional.append((etag, last_modified, page))
                return SourceFetch(
                    provider="f95zone", ref=ref,
                    request_url="https://f95zone.to/threads/160190/latest",
                    semantics="release", candidates=(), raw_body=b"<html/>")

        with mock.patch.object(web_follow, "build_connector", return_value=_Recorder()):
            result = self._post("/api/follow/check", {"source": source_id})

        self.assertTrue(result["results"][0]["ok"])
        self.assertEqual(conditional, [(None, None, 0)])

    def test_media_collections_expose_only_safe_display_fields_and_indices(self):
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="12228983", title="Poll Results",
            url="https://lazyprocrast.fanbox.cc/posts/12228983",
            extra={"media_items": [
                {"id": "one", "name": "one.mp4", "media_kind": "video",
                 "url": "https://store1.gofile.io/download/one.mp4",
                 "thumb_url": "https://store1.gofile.io/one.jpg",
                 "resource_provider": "gofile",
                 "resource_group": "gofile:OS2Qz9",
                 "resource_group_label": "Poll"},
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
        self.assertEqual(item["media_items"][0]["resource_group"], "gofile:OS2Qz9")
        self.assertEqual(item["media_items"][0]["resource_group_label"], "Poll")
        self.assertIsNone(item["media_items"][1]["media_type"])
        self.assertNotIn("url", item["media_items"][0])
        self.assertNotIn("store1.gofile.io/download", json.dumps(item))

    def test_online_image_details_have_safe_display_metadata(self):
        """灯箱需要来源和标题，但不得因此把远端媒体 URL 投影到 JSON。"""
        self._seed(candidates=(FollowCandidate(
            provider="rule34xxx", external_id="image-info", title="Source image",
            url="https://rule34.xxx/index.php?page=post&s=view&id=1",
            media_url="https://api-cdn.rule34.xxx/images/1/source.jpeg",
            extra={"media_kind": "image"}),), provider="rule34xxx", ref="artist")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["provider_label"], "Rule34.xxx")
        self.assertEqual(item["title"], "Source image")
        self.assertEqual(item["media_kind"], "image")
        self.assertTrue(item["playable"])
        self.assertNotIn("media_url", item)

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
            item["thumb_url"], "https://img.kemono.cr/thumbnail/data/ab/cd/image.jpg")
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

    def test_all_follow_surfaces_share_the_content_tag_projection(self):
        """卡片、详情、筛选条与标签页不能各自保留一套噪声判定。"""
        page = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("const followCardTags=item=>item.tags||[]", page)
        self.assertIn("const tags=followCardTags(item).slice(0,3)", page,
                      "卡片必须走过滤后的标签")
        self.assertIn("data-follow-tag=\"${esc(key)}\"", page,
                      "筛选条必须直接消费服务端投影")
        self.assertNotIn("FOLLOW_TAG_NOISE", page)
        self.assertNotIn("FOLLOW_TAG_TOPICAL", page)

    def test_generated_media_is_cached_for_a_month_not_a_day(self):
        """按 id 取的生成物内容不会变，一天太短。

        换了图 id 也就换了：封面重生成写的是新文件、头像换了会解析到新 URL。
        不加 immutable——那会让浏览器连刷新都不回源。
        """
        from peach import api

        self.assertEqual(api.MEDIA_CACHE_SECONDS, 365 * 24 * 3600)
        # 头像单独短一档：id 不变但人会换头像。
        self.assertEqual(api.AVATAR_CACHE_SECONDS, 30 * 24 * 3600)
        self.assertLess(api.AVATAR_CACHE_SECONDS, api.MEDIA_CACHE_SECONDS)
        source = (ROOT / "src" / "peach" / "api.py").read_text(encoding="utf-8")
        self.assertNotIn('max-age=86400', source,
                         "媒体端点不该再写死一天")
        self.assertNotIn('immutable"', source.replace(
            '"public, max-age=31536000, immutable"', ''),
            "只有 /vendor/ 那条可以 immutable")

    def test_archive_file_urls_get_the_data_prefix_and_the_right_host(self):
        """原始文件和缩略图走不同主机与路径，三站规则还不一样。

        2026-08-30 实测（取证见 docs/reference-snapshots/kemono-archive-media-host.md）：
        旧代码拼的是 `https://<主域><path>`，少了 `/data` 前缀——三站的原始文件都取不到，
        不只是 pawchive。pawchive 主域对 /data 也直接 404，必须点名 file. 子域；
        kemono/coomer 走主域让站点自己 302 到当前的 nX 节点（编号会变，不写死）。
        """
        from peach.follow_sources import archive_file_url

        self.assertEqual(
            archive_file_url("pawchive", "https://pawchive.pw/b7/d5/x.mp4"),
            "https://file.pawchive.pw/data/b7/d5/x.mp4")
        self.assertEqual(
            archive_file_url("kemono", "https://kemono.cr/7e/6b/y.jpg"),
            "https://kemono.cr/data/7e/6b/y.jpg")
        self.assertEqual(
            archive_file_url("coomer", "https://coomer.st/aa/bb/z.jpg"),
            "https://coomer.st/data/aa/bb/z.jpg")
        # 已经带 /data 的不再叠加
        self.assertEqual(
            archive_file_url("pawchive", "https://pawchive.pw/data/b7/d5/x.mp4"),
            "https://file.pawchive.pw/data/b7/d5/x.mp4")
        # 别的站点原样返回
        self.assertEqual(
            archive_file_url("rule34video", "https://rule34video.com/a.mp4"),
            "https://rule34video.com/a.mp4")

    def test_archive_file_subdomains_stay_inside_the_host_allowlist(self):
        """改写后的主机仍要过播放代理的白名单，安全边界不许因此放宽。"""
        from peach.follow_stream import _allowed

        self.assertTrue(_allowed("pawchive", "https://file.pawchive.pw/data/a.mp4"))
        self.assertTrue(_allowed("kemono", "https://n1.kemono.cr/data/a.jpg"))
        self.assertFalse(_allowed("pawchive", "https://evil.test/data/a.mp4"))
        self.assertFalse(_allowed("pawchive", "http://file.pawchive.pw/data/a.mp4"))

    def _tagged(self, external_id, tags):
        return FollowCandidate(provider="rule34video", external_id=external_id,
                               title=f"Clip {external_id}",
                               url=f"https://rule34video.com/video/{external_id}/x/",
                               extra={"tags": list(tags),
                                      "tag_types": {tag: "general" for tag in tags}})

    def test_counts_follow_the_active_author_filter(self):
        """筛掉一个作者，药丸上的数字必须跟着变。

        用户实测：换作者、换来源、换标签，下面的列表变了，状态条上的数字一动不动。
        原因是两个口径——数字来自一句全库 SQL，列表由浏览器在已加载的几页上筛。
        作者身份不是库里的列（要经实体绑定和别名映射推导），所以筛选整个搬到服务端，
        数字和列表从同一份数据出来。
        """
        self._seed(ref="a", label="Author A")
        self._seed(ref="b", label="Author B", candidates=(
            FollowCandidate(provider="rule34video", external_id="9001", title="B one",
                            url="https://rule34video.com/video/9001/x/"),))
        whole = self._get()
        self.assertEqual(sum(whole["counts"].values()), 3)
        key = next(source["author_key"] for source in whole["sources"]
                   if source["ref"] == "b")
        narrowed = self._get(author=key)
        self.assertEqual(sum(narrowed["counts"].values()), 1,
                         "选中一个作者后，数字仍是全库的——这正是用户报的那个 bug")
        self.assertEqual([group["primary"]["title"] for group in narrowed["groups"]],
                         ["B one"])

    def test_the_tag_filter_takes_the_intersection_not_the_union(self):
        """多选标签是「同时具备」，不是「任意一个」。

        并集会把筛选变成越点越多，跟用户的意图正好相反。
        """
        self._seed(candidates=(self._tagged("1", ["anal", "pov"]),
                               self._tagged("2", ["anal"]),
                               self._tagged("3", ["pov"])))
        both = self._get(tag="anal,pov")
        self.assertEqual(sum(both["counts"].values()), 1)
        self.assertEqual([group["primary"]["external_id"] for group in both["groups"]], ["1"])
        self.assertEqual(sum(self._get(tag="anal")["counts"].values()), 2)

    def test_filter_options_stay_whole_library_so_the_bar_does_not_collapse(self):
        """可选项按全库算，不按筛后结果。

        否则选中一个作者之后，服务端只回他的条目，作者栏里就只剩他一个人——
        用户再也切不回去，只能刷新页面。标签和来源同理。
        """
        self._seed(ref="a", label="Author A", candidates=(self._tagged("1", ["anal"]),))
        self._seed(ref="b", label="Author B", candidates=(self._tagged("2", ["pov"]),))
        whole = self._get()
        key = next(source["author_key"] for source in whole["sources"]
                   if source["ref"] == "b")
        narrowed = self._get(author=key)
        self.assertEqual(narrowed["facets"]["authors"], whole["facets"]["authors"],
                         "选中一个作者后另一个作者从筛选条上消失了")
        self.assertEqual(dict(narrowed["facets"]["tags"]), {"anal": 1, "pov": 1},
                         "标签选项也必须留着，否则换不了标签")

    def test_online_tag_vocabulary_matches_the_follow_filter_bar(self):
        """标签页列出的在线标签必须和关注页筛选条上的完全一致。

        两处都从 `_follow_facets` 出来，不是各写一份统计——否则标签页说某个标签有
        12 条，点进关注页只有 9 条，而两个数都「对」，只是口径不同。这类不一致在
        counts 上已经犯过一次了。
        """
        self._seed(candidates=(self._tagged("1", ["anal", "pov"]),
                               self._tagged("2", ["anal"])))
        page = self._get("/api/follow/tags")
        self.assertEqual(page["scope"], "online")
        self.assertEqual([(row["k"], row["n"]) for row in page["items"]],
                         [("anal", 2), ("pov", 1)])
        self.assertEqual([(row["k"], row["n"]) for row in page["items"]],
                         [tuple(pair) for pair in self._get()["facets"]["tags"]])

    def test_online_tags_page_supports_search_and_paging(self):
        """形状刻意与 /api/index 一致：标签页的分页和搜索是现成的，换个地址就能用。"""
        self._seed(candidates=(self._tagged("1", ["anal", "pov"]),
                               self._tagged("2", ["anal"]),
                               self._tagged("3", ["blowjob"])))
        self.assertEqual([row["k"] for row in self._get("/api/follow/tags", q="an")["items"]],
                         ["anal"])
        first = self._get("/api/follow/tags", limit=1)
        self.assertEqual([row["k"] for row in first["items"]], ["anal"])
        self.assertTrue(first["has_more"])
        last = self._get("/api/follow/tags", limit=1, offset=2)
        self.assertEqual([row["k"] for row in last["items"]], ["pov"])
        self.assertFalse(last["has_more"])

    def test_online_tag_index_exposes_recorded_rule34_types_and_filters_them(self):
        candidate = FollowCandidate(
            provider="rule34xxx", external_id="typed", title="Typed",
            url="https://rule34.xxx/index.php?page=post&s=view&id=1",
            extra={"tags": ["pose", "artist_name", "hero", "series_name", "animated"],
                   "tag_types": {"pose": "general", "artist_name": "artist",
                                 "hero": "character", "series_name": "copyright",
                                 "animated": "metadata"}},
        )
        self._seed(candidates=(candidate,), provider="rule34xxx", ref="typed")
        page = self._get("/api/follow/tags", types="all")
        self.assertEqual({row["k"]: row["cat"] for row in page["items"]}, {
            "pose": "general", "artist_name": "artist", "hero": "character",
            "series_name": "copyright", "animated": "metadata",
        })
        artists = self._get("/api/follow/tags", types="all", type="artist")
        self.assertEqual([(row["k"], row["cat"]) for row in artists["items"]],
                         [("artist_name", "artist")])
        self.assertEqual(sum(self._get(tag="artist_name")["counts"].values()), 1,
                         "在线索引里的非 general 标签点入后必须能筛到原条目")

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

    def test_a_busy_check_lock_says_registered_instead_of_staying_silent(self):
        """自动检查正好占着锁的时候，顺带的首次检查做不了。

        以前这里回 `checked: null`，调用方分不清「查过了什么都没有」和「根本
        没查」，界面上就是登记完一片空白。现在明说：已登记，稍后再查。
        """
        self.contract.follow_check_lock.acquire()
        self.addCleanup(self.contract.follow_check_lock.release)
        with mock.patch.object(web_follow, "build_connector") as factory:
            result = self._post("/api/follow/source", {
                "action": "add",
                "url": "https://rule34video.com/models/lazyprocrastinator/"})
        self.assertTrue(result["ok"])
        self.assertTrue(result["checked"]["deferred"])
        self.assertTrue(result["checked"]["ok"])
        self.assertIn("已登记", result["checked"]["message"])
        factory.assert_not_called()
        # 来源本身必须已经落库，稍后的自动检查才有东西可查。
        self.assertEqual(self._get()["sources"][0]["ref"], "lazyprocrastinator")

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


def _source_row(**kwargs):
    row = {"id": 7, "provider": "kemono", "ref": "fanbox/1", "label": "L",
            "url": "https://kemono.cr/fanbox/user/1", "semantics": "work",
            "enabled": 1, "entity_id": None, "entity_name": None,
            "backfill_page": 0, "created_at": "2026-08-01T00:00:00Z",
            "last_checked_at": "2026-08-30T00:00:00Z",
            "last_status": "ok", "last_error": None}
    row.update(kwargs)
    return row


class LegacyHistoryEndPayloadTests(unittest.TestCase):
    """回填到底的来源不能显示成红色错误行。

    `record_history_end` 之前的版本把「往回翻到尽头」记成了 `error`，那些行还在库里。
    判据现在来自连接器声明的 `HISTORY_END_STATUSES`，不再是 Web 层按站点名硬编码的
    中文串比较——新增一个可回填来源时没人会想到还要改那一处。
    """

    def test_a_terminal_backfill_error_is_reported_as_exhausted(self):
        payload = web_follow._source_payload(_source_row(
            backfill_page=3, last_status="error", last_error="kemono 返回 HTTP 400"))
        self.assertTrue(payload["history_exhausted"])
        self.assertEqual(payload["last_status"], "not_modified")
        self.assertIsNone(payload["last_error"])

    def test_a_real_failure_stays_a_failure(self):
        payload = web_follow._source_payload(_source_row(
            backfill_page=3, last_status="error", last_error="kemono 返回 HTTP 503"))
        self.assertFalse(payload["history_exhausted"])
        self.assertEqual(payload["last_status"], "error")
        self.assertEqual(payload["last_error"], "kemono 返回 HTTP 503")

    def test_the_same_message_on_the_first_page_is_a_real_failure(self):
        """没往回翻过页就不可能是「翻到尽头」，那是站点真的挂了。"""
        payload = web_follow._source_payload(_source_row(
            backfill_page=0, last_status="error", last_error="kemono 返回 HTTP 400"))
        self.assertFalse(payload["history_exhausted"])
        self.assertEqual(payload["last_status"], "error")

    def test_a_provider_that_never_pages_back_is_never_exhausted(self):
        payload = web_follow._source_payload(_source_row(
            provider="f95zone", ref="50685", backfill_page=3, last_status="error",
            last_error="f95zone 返回 HTTP 404"))
        self.assertFalse(payload["history_exhausted"])


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
        # 关注入口的路径、导航键和高亮都在路由表那一条里（web/app.js 的 ROUTES），
        # 不再是 navTo／navOn 各写一条 `k==='follow'` 分支。
        self.assertPageContains("{match:'/follow',nav:'follow',title:'关注',refresh:'skip',")
        self.assertPageContains("open:(params,push)=>openFollow(push),reload:()=>openFollow(false)},")
        # 管理区这一项得在 MANAGE_SECTIONS 里找，否则它被删了测试照样绿。名字也不再
        # 跟左栏那条相同：左栏的「关注」是看更新，这里的「关注管理」是 /follow-manage。
        manage = self.page[self.page.index("const MANAGE_SECTIONS=["):]
        manage = manage[:manage.index("];")]
        self.assertIn("['follow','关注管理','rss']", manage)
        self.assertPageContains('<symbol id="i-rss"')
        # 管理区身份同理：`section` 写在路由表上，`openManage('follow')` 按它查表。
        self.assertPageContains("{match:'/follow-manage',section:'follow',title:'关注管理',refresh:'skip',")
        self.assertPageContains("open:(params,push)=>openFollowManage(push)},")

    def test_follow_routes_restore_on_reload(self):
        # 恢复只有一个派发点：路径匹配到哪条路由，就打开那一屏。
        self.assertPageContains("const hit=matchRoute(ROUTES,path);")
        self.assertPageContains("if(hit)await hit.route.open(hit.params,false);")
        self.assertPageContains("open:(params,push)=>openFollow(push),reload:()=>openFollow(false)},")
        self.assertPageContains("open:(params,push)=>openFollowManage(push)},")
        self.assertPageContains(
            "await openFollow(push,true);await openFollowDetail(params.id,push)")
        self.assertPageContains("api(`/api/follow?item=${encodeURIComponent(id)}`)")
        self.assertPageContains(".then(async()=>{buildEdge();wireAllDrag();await restoreRoute();scheduleStickySurfaces()})")

    def test_the_add_state_is_looked_up_outside_the_form(self):
        # 提示行在表单外面。在 form 里找它会拿到 null，第一次赋值就抛 TypeError，
        # 整个提交静默失败——实测踩过。
        self.assertPageContains("const state=root.querySelector('[data-follow-add-state]')")

    def test_sources_are_added_by_pasting_not_by_a_command(self):
        self.assertPageContains('id="followAdd"')
        self.assertPageContains('name="line"')
        self.assertPageContains("'/api/follow/source'")
        self.assertPageContains("data-follow-remove")

    def test_the_lookup_is_one_line_submitted_by_enter_without_a_button(self):
        """查找不改任何东西，按 Vercel 表单规范就不该配提交按钮。

        规范原话是「输入框获得焦点时，若它是唯一控件，回车即提交」。原来非配按钮
        不可，是因为字段是 textarea——那里回车按规范要插入换行，回车提交就没法用。
        多行批量本身也不成立：一个作者就要几十秒，一次粘五行等于把这个等待乘五，
        中途还看不出走到哪一行。所以字段收成单行 search input，回车原生提交。
        """
        page = self.page
        form = page[page.index('<form class="faddform" id="followAdd">'):]
        form = form[:form.index("</form>")]
        self.assertIn('<input type="search" name="line" required', form)
        self.assertNotIn("textarea", form)
        self.assertNotIn('type="submit"', form)
        # 忙态没有按钮可以变灰，就落在表单自己身上：前缀图标原位换 Spinner。
        handler = page[page.index("if(form)form.onsubmit=async event=>{"):]
        handler = handler[:handler.index("\n  };")]
        self.assertIn("form.dataset.busy='true';form.setAttribute('aria-busy','true')", handler)
        self.assertIn("if(prefix)prefix.innerHTML=spinnerHtml('查找中')", handler)
        self.assertIn("form.removeAttribute('aria-busy')", handler)
        self.assertNotIn("setActionBusy", handler)
        # 隐式提交在这个表单上不成立：来源筛选的复选框和输入框住在同一个 <form> 里，
        # 浏览器只在「仅有一个文本字段」时才替你提交。回车必须自己接管。
        self.assertPageContains("if(event.key!=='Enter'||event.isComposing)return;")
        self.assertPageContains("event.preventDefault();form.requestSubmit();")
        # 单行以后不再有拆行与自增高。
        self.assertNotIn("box.style.height", page)
        self.assertIn("const lines=[line];", handler)

    def test_reader_management_is_locked_and_points_to_the_writer(self):
        # 读请求带上表面的 signal（surfaceApi），切页时会被取消。
        self.assertPageContains("surfaceApi(surface,'/healthz')")
        self.assertPageContains("followRuntime?.ledger_read_only")
        self.assertPageContains("前往写入端管理关注")
        self.assertPageContains("#followAdd input,#followAdd button")

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

    def test_follow_author_groups_use_fixed_scrolling_cards_and_link_to_the_original_page(self):
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
        author_rule = author[:author.index("}")]
        self.assertIn("height:280px", author_rule)
        self.assertIn("border:1px solid var(--border-10)", author_rule)
        self.assertIn("grid-template-rows:auto minmax(0,1fr)", author_rule)
        self.assertPageContains("scrollerHtml(group.map(followSourceRow).join(''),{")
        self.assertPageContains("className:'fauthorsources',label:`${name} 的关注来源`")
        self.assertPageContains(".fauthorsources .geist-scroller-container{padding-right:12px;scrollbar-width:thin}")
        self.assertPageContains(".fauthorsources .geist-scroller-container::-webkit-scrollbar{display:block}")
        self.assertPageContains("wireScrollers(root)")

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
        self.assertPageContains('data-follow-enabled="${source.id}"')
        self.assertPageContains("{action:'enabled',id:Number(control.dataset.followEnabled),enabled}")
        # 框本身归共用的 .pcheck，.fchannelcheck 只剩这一行在行里的摆放。
        self.assertPageContains(".fchannelcheck{display:grid;place-items:center;align-self:center}")
        self.assertPageContains(".pcheck input{position:absolute;width:1px;height:1px;opacity:0")
        # Geist Checkbox 选中态实测：框底不变，勾是墨色；不再用蓝底。
        self.assertPageContains(".pcheck input:checked+span{border-color:var(--ink-2);color:var(--ink)}")
        self.assertPageContains("${icon('check')}")

    def test_official_channel_icons_and_alias_manager_are_visible(self):
        icons = self.page.split("const SOURCE_ICONS={", 1)[1].split("};", 1)[0]
        for provider in ("fanbox", "patreon", "subscribestar"):
            self.assertIn(provider, icons)
        self.assertIn("assets.subscribestar.com/assets/public/images/favicons/favicon-32x32-", icons)
        self.assertPageContains("followAliasManager(followData.author_aliases,followData.alias_suggestions)")
        self.assertPageContains("'/api/follow/author-alias'")

    def test_a_multi_source_author_head_shows_only_favicons(self):
        """图标已经说清是哪几个来源，再补一句「N 个来源」就要和它们抢同一行。

        窄卡片里那句话先把图标挤到贴脸，再把作者名压没。数量本来就能数出来，
        真要确认就读 title。
        """
        page = self.page
        block = page[page.index('return `<div class="fauthor${bad?\' bad\':\'\'}">'):]
        block = block[:block.index("${sources}")]
        self.assertIn("? group.map(source=>sourceIcon(source.provider)).join('')", block)
        self.assertNotIn("个来源`", block)
        self.assertIn('title="${group.length} 个来源"', block)
        rule = page[page.index(".fauthorhead .fmeta{"):]
        self.assertIn("flex:0 1 auto;min-width:0", rule[:rule.index("}")])

    def test_already_followed_candidates_are_shown_but_not_selectable(self):
        # 灰掉但仍显示，免得人以为没查到。
        self.assertPageContains("c.known?' known':''")
        self.assertPageContains("'已经关注'")

    def test_the_first_name_lookup_warns_about_the_index_download(self):
        self.assertPageContains("首次按名字查要下载创作者索引，可能几十秒")

    def test_the_input_and_its_button_are_the_same_height(self):
        # 输入框和旁边的来源筛选按钮齐平；单行以后没有 min-height 与 resize。
        page = self.page
        self.assertEqual(page.count('.faddform input[type="search"]{'), 1,
                         "旧规则留在后面会覆盖新输入框样式")
        rule = page[page.index('.faddform input[type="search"]{'):]
        rule = rule[:rule.index("}")]
        self.assertIn("height:38px", rule)
        self.assertIn("padding:0 12px 0 38px", rule)
        self.assertIn("line-height:20px", rule)
        self.assertNotIn("resize:", rule)
        button = page[page.index("\n.fbtn{"):]
        self.assertIn("height:32px", button[:button.index("}")])
        # faddform 里的按钮随输入栏同高（Geist 输入 32px 基线之上的一档）。
        add_button = page[page.index(".faddform .fbtn{"):]
        self.assertIn("height:38px", add_button[:add_button.index("}")])

    def test_source_filter_uses_the_project_toolbar_layout_without_menu_motion(self):
        # Vercel Projects：搜索占剩余宽度，筛选带明确标签，主操作在右；
        # 菜单没有展开动画，并在自己的视口内滚动。
        self.assertPageContains(
            ".faddform{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px")
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

    def test_the_page_is_one_narrow_column_with_credentials_inline(self):
        """侧栏在哪个宽度上都不对：宽屏把凭据推出视线，窄屏又整个塌到最底下。

        三块内容本来就有先后——先添加、再看列表、要配凭据时才往下翻——那就按顺序
        排成一列，宽度跟数据管理页同样收到 812px，别让一行横跨整个显示器。
        """
        page = self.page
        rule = page[page.index(".followmanage{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("width:min(812px,100%)", rule)
        self.assertIn("margin-left:auto;margin-right:auto", rule)
        self.assertNotIn("grid-template-columns", rule)
        self.assertNotIn("faside", page)
        self.assertNotIn("@media (max-width:1080px){.followmanage{", page)
        # 标题与说明跟内容列同宽，否则标题悬空在更宽的位置上。
        self.assertPageContains(
            ".follow-manage-layout .managetitle,.follow-manage-layout .pagelede{width:min(812px,100%)")
        self.assertPageContains(
            "document.body.classList.toggle('follow-manage-layout',"
            "decodeURIComponent(location.pathname)==='/follow-manage')")
        # 凭据现在是主列里的第三块，不再是 aside。
        body = page[page.index("function renderFollowManage("):
                    page.index("function wireFollowManage(")]
        self.assertLess(body.index("<h3>关注列表</h3>"), body.index("<h3>凭据</h3>"))

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

        推荐不能退化成 placeholder：占位文字点不了。占位文字只负责说清该输入什么
        格式（Vercel Forms：以省略号收尾、给出示例样式），不许塞进具体创作者名。
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
        form = body[body.index('<form class="faddform"'):body.index("</form>")]
        hint = form[form.index("placeholder="):form.index("aria-label=")]
        self.assertIn("粘贴来源链接，或输入作者名、id…", hint)
        self.assertNotIn("${", hint, "占位文字不许由数据拼出来——那就是把推荐塞进去了")
        self.assertEqual(body.count("placeholder="), 1)

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
        # chevron 是 16px SVG，不是靠字号撑大的 › 字形：本页字阶只有三档，
        # 图标尺寸混进去就会把「没有随意字号」这条门槛顶穿。
        self.assertPageContains(".faliasmanager>summary>svg{flex:none;width:16px;height:16px")
        self.assertPageLacks('.faliasmanager>summary::before{')
        self.assertPageContains("transition:transform .2s ease-in-out")
        # 内边距放在内层 .fcollapsebody：.fcollapse 自己带 padding 时 border-box 让
        # height 过渡卡在 20px，收起末尾会跳一下，展开开头也先露出一截空白。
        self.assertPageContains("inner.className='fcollapsebody'")
        self.assertPageContains(".faliasmanager .fcollapsebody{padding:4px 16px 16px}")
        self.assertPageLacks(".faliasmanager>.fcollapse{padding")
        # 别名行是 Fieldset 的最后一行：负外边距吃掉 .fsec 的底部内边距，收起时底角与
        # 卡片同心，否则整行下面多出一层 16px 的空带。
        self.assertPageContains(".faliasmanager{margin:12px -16px -16px;")
        self.assertPageContains('.faliasmanager>summary[aria-expanded="false"]{border-radius:0 0 calc(var(--surface-radius) - 1px) calc(var(--surface-radius) - 1px)}')
        self.assertPageContains(".faliasmanager .fcollapsebody{padding:4px 13px 14px}")

    def test_credential_rows_share_the_alias_collapse_motion(self):
        """凭据行早先是 flex 行布局接不上 Collapse。

        `details.fcred` 已经统一成 block，两处就该是同一份实现——展开一段正文这件事
        不该有第二套开合逻辑。
        """
        self.assertPageContains("export function wireCollapse(root,selector,idPrefix)")
        self.assertPageContains("wireCollapse(root,'details.faliasmanager','follow-alias-collapse')")
        self.assertPageContains("wireCollapse(root,'details.fcred','follow-cred-collapse')")
        self.assertEqual(self.page.count("body.style.height=body.scrollHeight+'px'"), 1,
                         "开合逻辑只该有一份")
        # 内边距归 .fcollapsebody：留在 .fcred[open] 上的话，收起那一帧高度已经归零、
        # 内边距还在，行尾会跳一下。
        self.assertPageContains(".fcred .fcollapsebody{padding:8px 0 12px}")
        self.assertPageLacks(".fcred[open]{padding-bottom")
        # 首段自己的上边距换成容器内边距，否则它跟容器外边距合并，scrollHeight 量矮一截。
        self.assertPageContains(".fcred .fcollapsebody>p:first-child{margin-top:0}")

    def test_credential_rows_carry_the_same_favicon_as_their_source(self):
        """凭据配的就是那个站，用来源行同一枚 favicon 指认它。"""
        self.assertPageContains(
            'const mark=`<span class="ficonslot" aria-hidden="true">${sourceIcon(row.provider)}</span>`')
        self.assertPageContains('<div class="frow fcred none">${mark}<b>${esc(row.provider_label)}</b>')
        self.assertPageContains("<summary>${mark}<b>${esc(row.provider_label)}</b>")
        # 槽位占住 14px，不看里面有没有图：没登记 favicon 的站本来就没有，取不下来的
        # 那些还会被 data-drop="self" 整个丢掉，两种情况都会让名字的左边缘参差。
        self.assertPageContains(".fcred .ficonslot{flex:none;display:block;width:14px;height:14px}")
        self.assertPageContains(".fcred .ficon{margin-right:0}")
        self.assertIn('data-drop="self"', self.page)

    def test_the_follow_list_has_a_compact_switch_that_puts_two_per_row(self):
        """两个互斥视图用 Switch（共享 name 的 radio），不是 Toggle。"""
        self.assertPageContains(
            "const FOLLOW_LAYOUTS=[['cozy','舒适 · 一行一个','maximize'],"
            "['compact','紧凑 · 一行两个','layout-grid']]")
        self.assertPageContains(
            "iconSwitchHtml('follow-layout','关注列表版式',FOLLOW_LAYOUTS,followListLayout()")
        self.assertPageContains("{attr:'data-follow-layout'}")
        self.assertPageContains("${followLayoutButtons()}")
        self.assertPageContains("wireIconSwitch(root,'data-follow-layout',setFollowListLayout)")
        # 版式是纯展示层的事：改容器上的一个属性就够，不重画列表，也不重新请求。
        self.assertPageContains('<div class="frows fsources" data-layout="${followListLayout()}">')
        self.assertPageContains("node.dataset.layout=followListLayout()")
        # 紧凑就是一行两个；半幅宽度放不下六列，收掉最不影响判断的「上次检查」。
        self.assertPageContains(
            '.fsources[data-layout="compact"]{grid-template-columns:repeat(2,minmax(0,1fr))}')
        self.assertPageContains('.fsources[data-layout="compact"] .fsource .fchecked{display:none}')
        # 窄屏两栏塞不下，仍旧回到一栏——媒体查询要连紧凑一起覆盖，否则属性选择器更具体。
        self.assertPageContains('.fsources,.fsources[data-layout="compact"]{grid-template-columns:1fr}')
        # 窄屏两栏不成立，开关一起收起，不留一个按了没反应的控件。
        self.assertPageContains('.fsechead .iconswitch{display:none}')
        # 选择要留下来，和 JAV 版式一样存进设置。
        self.assertPageContains("javLayout:'big',followLayout:'cozy'")
        self.assertPageContains("appSettings.followLayout=value")
        self.assertPageContains(
            "allowedSetting(appSettings.followLayout,FOLLOW_LAYOUTS.map(([k])=>k),'cozy')")

    def test_the_layout_switch_lines_up_with_the_sort_box(self):
        """开关和排序框、按钮同处分区标题行，高度必须是同一档。"""
        rule = self.page[self.page.index(".fsechead .iconswitch{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("flex:none", rule)
        self.assertIn("padding:2px", rule)
        self.assertPageContains(".fsechead .iconswitch label{width:32px;height:26px}")

    def test_alias_count_badge_is_neutral_metadata(self):
        """「3 组」只是计数，不是待处理提醒：徽章走 Geist gray badge 的中性灰。

        实测 Geist Badge gray：#1A1A1A 底、#292929 细边、#A1A1A1 字、6px 圆角。此前用
        蓝底蓝字的 pill，和主按钮同色，读起来像有事要处理。
        """
        badge = self.page[self.page.index(".faliasbadge{"):]
        badge = badge[:badge.index("}")]
        self.assertIn("border:1px solid var(--border-15)", badge)
        self.assertIn("border-radius:var(--control-radius)", badge)
        self.assertIn("background:var(--overlay-5)", badge)
        self.assertIn("color:var(--muted)", badge)
        self.assertIn("font-weight:400", badge)
        self.assertNotIn("tungsten", badge)
        self.assertNotIn("pill-radius", badge)

    def test_follow_source_icons_fail_back_to_plain_text(self):
        icons = self.page.split("const SOURCE_ICONS={", 1)[1].split("};", 1)[0]
        self.assertIn("kemono.cr/assets/favicon-", icons)
        self.assertIn("pawchive.pw/static/favicon.png", icons)
        self.assertNotIn("kemono.cr/favicon.ico", icons)
        # 取不到图标就把 <img> 摘掉，露出纯文字；收场动作由 image-fallback 的
        # 委托监听执行，模板里只声明 `data-drop`。
        self.assertPageContains('data-drop="self"')

    def test_follow_watch_filters_use_the_source_identity(self):
        # 判定本身搬去了服务端（见 FollowContractTests 里的筛选用例）；页面这一侧要
        # 保证的是把身份原样交出去，而不是把显示名或来源标签当筛选值送过去。
        self.assertPageContains("+(followAuthor?`&author=${encodeURIComponent(followAuthor)}`:'')")
        self.assertPageContains("+(followProvider?`&provider=${encodeURIComponent(followProvider)}`:'')")
        self.assertPageContains('class="tier followauthors"')
        self.assertPageContains('class="tagbar followfilters"')
        self.assertPageContains('class="pill sourcepill" data-follow-provider=')
        self.assertPageLacks("内容标签目前由 ${")
        self.assertPageContains("const randomizedAuthors=followRandomOrder([...authors],row=>row[0])")
        self.assertPageContains("const topTagRows=followRandomOrder([...tagCounts],row=>row[0]).slice(0,20)")
        self.assertPageContains("if(push)followDiscoverySeed=Math.floor(Math.random()*0xffffffff)")
        self.assertPageContains("topTagRows.push([tag,tagCounts.get(tag)||allCount])")

    def test_follow_tags_are_multi_select_and_use_rule34_property_colours(self):
        self.assertPageContains("let followAuthor='',followProvider='',followTags=new Set()")
        # 取交集的判定在服务端；页面负责把多选的标签一次全交出去。
        self.assertPageContains("+(followTags.size?`&tag=${encodeURIComponent([...followTags].join(','))}`:'')")
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
        self.assertPageContains(".fnote.followmediaissue{margin:18px 0 8px;color:var(--drop)}")
        self.assertPageContains("followAuthorAvatar(authorSources)")
        self.assertPageContains("followTagChip(item,tag,'button')")
        self.assertPageContains("item.detail_tags||item.tags||[]")
        self.assertPageContains(".followdetailtags .tg{max-width:none")
        self.assertPageContains("const postedBy=item.author&&foldName(item.author)!==foldName(author)")
        self.assertPageContains("openFollowDetail(id);")
        self.assertNotIn('class="cardopenhit" href=', self.page)
        self.assertNotIn('class="t cardtitle" href=', self.page)
        self.assertNotIn('class="fcollectionthumb" href=', self.page)
        self.assertPageContains("route(followDetailReturnPath||'/follow')")
        self.assertPageContains(".followitem a{text-decoration:none}")

    def test_one_fanbox_collection_keeps_its_gofile_folder_sections(self):
        self.assertPageContains("const followGroupedMediaOwner=group=>")
        self.assertPageContains("(item.media_items||[]).some(media=>media.resource_group)")
        self.assertPageContains("const key=media.resource_group||'ungrouped'")
        self.assertPageContains('class="mixgrouplabel"')
        self.assertPageContains('data-follow-media-owner="${item.id}"')

    def test_follow_video_uses_the_shared_videojs_player_and_quality_control(self):
        self.assertPageContains('class="video-js vjs-big-play-centered" controls playsinline preload="metadata"')
        self.assertPageContains("if(followVideo){")
        self.assertPageContains("const followPlayer=await mountDetailPlayer(item,followVideo,false,{")
        self.assertPageContains("source:{src,type:selectedMedia?.media_type||item.media_type||'video/mp4'}")
        # 第四个参数是来源自己给的清晰度表：rule34video 把每档写成独立 mp4 字段，
        # videojs 的 qualityLevels 只认 HLS/DASH 的自适应轨道，看不到它们。
        self.assertPageContains(
            "function mountPlayerQualityControl(player,video,fallbackHeight=0,initialSourceQualities=null)")
        self.assertPageContains("const qualitiesPromise=api(`/follow-qualities?id=${encodeURIComponent(item.id)}`)")
        self.assertPageContains("qualitiesPromise",
                                "关注详情要异步补上来源档位")
        detail = self.page.split("async function openFollowDetail", 1)[1].split(
            "function renderFollow", 1)[0]
        self.assertNotIn("await api(`/follow-qualities", detail,
                         "清晰度回源不能挡住默认视频挂载")
        self.assertLess(detail.index("const followPlayer=await mountDetailPlayer"),
                        detail.index("wireFollowTelemetry"))
        self.assertPageContains('aria-label="播放器设置"')
        self.assertPageContains("data-player-quality-badge")
        self.assertPageContains("currentTimeDisplay:true,timeDivider:true")
        self.assertPageContains("levels[index].enabled=selectedQuality==='auto'||selectedQuality===String(index)")
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
        self.assertPageContains('class="media-circle media-overlay followimagearrow prev"')
        self.assertPageContains('class="media-circle media-overlay followimagearrow next"')
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
        self.assertPageContains("await openFollow(push,true);await openFollowDetail(params.id,push)")
        self.assertPageContains("const followList=$('#stats').querySelector('.followlist')")
        # 就近展开：插在被点击那张卡片所在的一行之后，不是整个列表之前。
        # 插在列表前等于每次都把视线拽回页面顶部，翻了几屏点开一条尤其明显。
        self.assertPageContains("last.after($('#stage'))")
        self.assertPageContains("Math.abs(card.offsetTop-row)<2",
                                "按行插入，避免把卡片那一行截断")
        # 列表还没渲染出来时（直达详情链接）仍回退到列表前
        self.assertPageContains("followList.before($('#stage'))")
        self.assertPageContains("followList?.classList.contains('followphotowall')")
        self.assertPageContains(".followlist>.stage{grid-column:1/-1;width:100%;min-width:0}")
        self.assertPageContains("scrollItemDetailIntoView();",
                                "滚到舞台本身而不是页面头部")
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

    def test_release_time_is_not_reused_as_a_variant_label(self):
        self.assertPageContains("if(!label&&group.is_release)label=item.variant_label||item.variant_kind||''")
        body = self.page[self.page.index("function followCollectionCopy("):
                         self.page.index("function followQueueHtml(")]
        self.assertNotIn("localTime(item.published_at)", body)

    def test_release_rows_show_the_reply_body_not_the_thread_title(self):
        self.assertPageContains("const body=group.is_release")
        self.assertPageContains("'（仅附件）'")

    def test_thread_activity_is_not_called_a_version(self):
        """线程动态叫「条动态」，作品版本叫「个版本」，两者都含主条目。

        计数以前是分开写的：release 记 `variants.length+1`、work 记 `variants.length`。
        同一份数据两种口径，两个视频的组会显示成「1 个版本」。现在共用一个表达式，
        只有量词不同。
        """
        self.assertPageContains("`${count} ${group.is_release?'条动态':'个版本'}`")
        self.assertPageLacks(
            "`${group.variants.length} 个版本`",
            "版本数必须含主条目，否则两个视频显示成 1 个版本")
        # 计数来源换成了「点开真能看到的那一组」，量词的分工不变。
        self.assertPageContains("const count=(openable||followOpenableItems(group)).length;")

    def test_cross_site_duplicates_are_shown_as_another_source(self):
        self.assertPageContains("另见 ")
        self.assertPageContains("fbadge dup")

    def test_wip_has_its_own_badge(self):
        self.assertPageContains('<span class="fbadge wip">WIP</span>')

    def test_network_check_is_an_explicit_button_not_an_auto_refresh(self):
        self.assertPageContains("data-follow-check")
        # 「换一批」自动刷新绝不能顺手触发一次联网检查。这件事现在由路由表上的
        # `refresh:'skip'` 表达：refreshAll 只认这个标记，两个关注页各自带一个。
        self.assertPageContains("if(hit?.route.refresh==='skip')return;")
        self.assertPageContains("{match:'/follow',nav:'follow',title:'关注',refresh:'skip',")
        self.assertPageContains("{match:'/follow-manage',section:'follow',title:'关注管理',refresh:'skip',")

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

        tags = web_follow._item_tags(_Item({
            "tag": "lazyprocrastinator",
            "tags": "lazyprocrastinator 1girls animated sound riding lazyprocrastinator",
            "tag_types": {"lazyprocrastinator": "artist", "1girls": "general",
                          "animated": "metadata", "sound": "general", "riding": "general"},
        }))
        # 作者手柄本身不算标签：按作者筛已经有专门的筛选条，重复出现没有信息量。
        self.assertEqual(tags, ["riding"])
        video_tags = web_follow._item_tags(_Item({
            "tags": ["deep throat", "3D", "3d_animation", "breast squeeze"],
            "categories": ["2D", "Final Fantasy"],
            "tag_types": {"deep throat": "general", "3D": "metadata",
                          "3d_animation": "metadata", "breast squeeze": "general",
                          "2D": "metadata", "Final Fantasy": "copyright"},
        }))
        self.assertEqual(video_tags, ["deep throat", "breast squeeze"])
        screenshot_tags = web_follow._item_tags(_Item({
            "tags": "beach dead_or_alive 16:9 2026 female 1boy 1girls breasts "
                    "final_fantasy male ass blender 3d 3d_model pov blowjob",
            "tag_types": {**{tag: "general" for tag in
                "beach 16:9 2026 female 1boy 1girls breasts male ass pov blowjob".split()},
                "dead_or_alive": "copyright", "final_fantasy": "copyright",
                "blender": "metadata", "3d": "metadata", "3d_model": "metadata"},
        }))
        self.assertEqual(screenshot_tags, ["pov", "blowjob"])
        typed = web_follow._item_tags(_Item({
            "tags": ["artist name", "some character", "some series", "handjob"],
            "tag_types": {"artist name": "Artist", "some character": "character",
                          "some series": "copyright", "handjob": "general"},
        }))
        self.assertEqual(typed, ["handjob"])
        self.assertEqual(web_follow._item_tags(_Item({})), [])
        self.assertEqual(web_follow._item_tags(_Item({"tags": "   "})), [])
        # rule34.xxx 旧行存的是 HTML 转义形态；出口归一后与反转义的新写法
        # 是同一个身份，脏/净并存的重复项也合并成一个。
        legacy = web_follow._item_tags(_Item({
            "tags": "miqo&#039;te y&#039;shtola miqo&#039;te",
            "tag_types": {"miqo&#039;te": "general", "y&#039;shtola": "general"},
        }))
        self.assertEqual(legacy, ["miqo'te", "y'shtola"])
        # 旧行没有来源类型时不猜成 general；详情仍可显示全部原始标签。
        untyped = _Item({"tags": "blender reverse_cowgirl_position"})
        self.assertEqual(web_follow._item_tags(untyped), [])
        self.assertEqual(web_follow._item_all_tags(untyped),
                         ["blender", "reverse_cowgirl_position"])
        # 热门帖能带上百个标签，整串发下去会把筛选条撑爆。
        many_values = [f"t{n}" for n in range(200)]
        many = _Item({"tags": " ".join(many_values),
                      "tag_types": {tag: "general" for tag in many_values}})
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

    def test_collection_is_container_copy_not_part_of_the_author_display_name(self):
        self.assertEqual(follow_store.author_display_text("Billyhhyb Collection"),
                         "Billyhhyb")
        self.assertEqual(follow_store.author_display_text("Billyhhyb · patreon"),
                         "Billyhhyb")

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
        self.assertPageContains("if(act)act.onclick=()=>{setActionBusy(act);action.run()};")
        self.assertPageLacks("条详情")

    def test_detail_tags_follow_rule34s_own_category_order(self):
        """详情标签按 rule34.xxx 帖子页 `#tag-sidebar` 的类型顺序分组，不按字母。

        2026-09-01 实测两个帖子页（18622796 / 18622794），`li.tag-type-*` 的出现
        顺序都是 copyright → character → artist → general → metadata，组内按名升序；
        缺的类型直接跳过不占位。证据见
        docs/reference-snapshots/rule34-follow-tags-and-collections.md。
        """
        self.assertPageContains(
            "const FOLLOW_TAG_ORDER=['copyright','character','artist','general','metadata'];")
        self.assertPageContains("function followDetailTags(item)")
        self.assertPageContains("return at<0?FOLLOW_TAG_ORDER.length:at};")
        self.assertPageContains(
            "return [...tags].sort((a,b)=>rank(a)-rank(b)||tagLabel(a).localeCompare(tagLabel(b)));")
        self.assertPageContains(
            "const tags=followDetailTags(item).map(tag=>followTagChip(item,tag,'button')).join('');")
        # 来源没记类型的排最后、保持中性色：不按词形猜类型是关注标签的既有门槛。
        self.assertPageContains(".followdetailtags .r34-unknown{--r34-tag:var(--muted)}")

    def test_version_badge_counts_what_opening_the_card_actually_shows(self):
        """角标数和点开后能看到的条数必须来自同一个集合。

        实测两处对不上：paheal 一组 9 条里有 1 张图，卡上写「9 个版本」、播放角标
        写「8 个视频」；`2B Camp [4K]` 卡上写「2 个版本」，同组另一条不是可播视频，
        `collection` 因此为 null，点开只有 1 条。
        """
        self.assertPageContains("function followOpenableItems(group)")
        self.assertPageContains("if(followMediaView==='videos')return followVideoItems(group);")
        self.assertPageContains("const count=(openable||followOpenableItems(group)).length;")
        self.assertPageContains("if(count>1)badges.push(")
        self.assertPageLacks("${group.variants.length+1} ${group.is_release?'条动态':'个版本'}")

    def test_wip_badge_describes_this_item_not_its_siblings(self):
        """`2B Camp [4K]` 判的是 alt，只因为同组还有一条 `[WIP]` 就挂上 WIP。

        `has_wip` 是组属性（`any(item.variant_kind == "wip" for item in self.variants)`），
        角标却贴在主条目标题旁边，读起来就是「这一条是半成品」。
        """
        self.assertPageContains(
            "if(group.primary.variant_kind==='wip')badges.push('<span class=\"fbadge wip\">WIP</span>');")
        self.assertPageContains(
            "else if(group.has_wip)badges.push('<span class=\"fbadge wip partial\">含 WIP</span>');")
        self.assertPageContains(".fbadge.wip.partial{border-color:var(--border-15);color:var(--muted)}")

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
        self.assertPageContains(".replace(/\\s+collections?\\s*$/i,'').trim()")
        # 取不到图片时回退作者首字母；不能从来源标签切出中文“初”“一”。
        self.assertPageContains("function followAvatarInitial(group)")
        self.assertPageContains('title="没有可用头像"')
        avatar = self.page[self.page.index("function followAuthorAvatar(group)"):]
        avatar = avatar[:avatar.index("function followAuthorBlock")]
        self.assertIn("followAvatarInitial(group)", avatar)
        self.assertIn("source.avatar_url", avatar)
        self.assertIn("source.official_avatar_url", avatar)
        # 镜像头像是官方头像的下一个候选，声明在 `data-fallbacks` 里；两条都取不到
        # 才换成首字母垫底。
        self.assertIn("fallbacks:[fallback]", avatar)
        self.assertIn("drop:'initial'", avatar)

    def test_discovered_sources_keep_the_search_term_as_the_author_identity(self):
        self.assertPageContains('data-author="${esc(c.author||\'\')}"')
        self.assertPageContains("author:input.dataset.author")

    def test_only_actionable_media_failures_enter_the_information_stream(self):
        self.assertPageContains("媒体未取得：需要 F95 登录会话解析")
        self.assertPageContains("部分媒体未取得：需要 F95 登录会话解析")
        self.assertPageLacks("已显示可读取附件；F95 登录会话已保存")
        self.assertPageLacks("这条旧记录的受保护资源会在下次检查重新解析")
        self.assertPageContains("followCredentialProviders=new Set")
        self.assertPageContains("surfaceApi(surface,'/api/follow/credentials').catch")
        self.assertPageLacks("个外部文件页；视频列表未取得")
        self.assertPageContains("function followMediaIssue(item)")
        self.assertPageContains('class="fnote followmediaissue"')
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
        self.assertPageContains("spinnerHtml('抓取中')")
        self.assertPageContains("setActionBusy(button);button.title='检查中…'")
        self.assertPageContains("c.known?'已经关注':c.evidence")
        self.assertPageLacks("已经在追")

    def test_follow_styles_exist_for_the_card_surface(self):
        for selector in (".followlist{", ".followitem{", ".fbadge{", ".followqueue"):
            self.assertPageContains(selector)

    def test_follow_cards_reuse_home_cards_hover_actions_and_mix_stacks(self):
        self.assertPageContains("function followVideoItems(group)")
        self.assertPageContains("function followCollectionItemsNewest(group)")
        self.assertPageContains("Date.parse(b.published_at||'')")
        self.assertPageContains("followCollectionItemsNewest(group).filter")
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
        self.assertPageContains("return mediaViewButtonsHtml({active:followMediaView,videoCount:counts.videos,imageCount:counts.images})")
        self.assertPageContains("button.dataset.mediaView")
        self.assertPageLacks('class="insightswitch followmediaswitch"')
        self.assertPageLacks("params.set('media-ui','switch')")
        self.assertPageLacks('class="followmediaicons"')
        self.assertPageLacks('data-follow-media=')
        self.assertPageContains("params.set('author',followAuthor)")
        self.assertPageContains("route(followViewPath());renderFollow()")
        self.assertPageContains("if(!counts.images&&followMediaView!=='images')return ''")
        self.assertPageLacks("if(followMediaView==='images'&&!mediaCounts.images)followMediaView='videos'")
        self.assertPageLacks("if(followMediaView==='videos'&&!mediaCounts.videos&&mediaCounts.images)followMediaView='images'")
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
        self.assertPageContains(".followlist.followphotowall{grid-template-columns:repeat(5,minmax(0,1fr))")
        self.assertPageLacks(".followlist.followphotowall>.stage{column-span:all}")
        self.assertPageContains("followList?.classList.contains('followphotowall')",
                                "图片详情必须脱离图片网格，避免改变所有行的排列")
        self.assertPageContains(".followitem.imagecard .pic{aspect-ratio:4/3;min-height:0")
        self.assertPageContains(".followitem.imagecard .followvisual .pic>img{position:absolute")
        self.assertPageLacks(".followlist.followphotowall{display:block;column-count:5")
        self.assertPageLacks(".followitem.imagecard .pic{aspect-ratio:auto")
        self.assertPageLacks(".followitem.imagecard{display:inline-flex;width:100%;margin:0 0 14px;break-inside:avoid}")

    def test_external_file_pages_do_not_default_to_video_and_paging_actions_share_one_row(self):
        self.assertPageContains("else if(item.media_kind==='image'||item.media_kind==='video')kinds.add(item.media_kind)")
        self.assertPageLacks("else kinds.add(item.media_kind==='image'?'image':'video')")
        self.assertPageContains('class="followpagination"')
        self.assertPageContains("${icon('refresh-cw')}加载更多")
        self.assertPageLacks("${icon('plus')}加载更多")
        self.assertPageContains("${icon('history')}抓更早的一页")
        self.assertPageContains("spinnerHtml('加载更多')")
        self.assertPageContains("spinnerHtml('抓取中')")

    def test_follow_management_list_has_routed_sorting(self):
        self.assertPageContains('data-follow-sort aria-label="关注列表排序"')
        self.assertPageContains('<option value="checked"')
        self.assertPageContains('<option value="added"')
        self.assertPageContains('<option value="name"')
        self.assertPageContains('<option value="sources"')
        self.assertPageContains("followManageSort=['checked','added','name','sources'].includes(requested)?requested:'checked'")
        self.assertPageContains("const added=group=>Math.max(...group.map(source=>Date.parse(source.created_at||'')||0))")
        self.assertPageContains("if(followManageSort==='added')return added(b)-added(a)")
        backend = (ROOT / "src" / "peach" / "web_follow.py").read_text(encoding="utf-8")
        self.assertIn('"created_at": row["created_at"]', backend)
        self.assertPageContains("return groups.sort((a,b)=>{")

    def test_mix_and_follow_queues_stay_below_media_with_details_on_the_right(self):
        self.assertPageContains('grid-template-areas:"media side" "queue queue"')
        self.assertPageContains('.sgrid.mixgrid>.vwrap{grid-area:media}')
        self.assertPageContains('.sgrid.mixgrid>.side{grid-area:side;background:var(--detail-surface)}')
        self.assertPageContains('.sgrid.mixgrid>.mixqueue{grid-area:queue;max-height:360px')
        self.assertPageContains('grid-template-areas:"media" "side" "queue"')
        self.assertPageContains('background:var(--detail-surface)')
        self.assertPageContains("const kindLabel={mix:'Mix',parts:'分卷',editions:'版本',playlist:'播放列表'}")
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

    def test_detail_images_open_the_same_lightbox_as_the_performer_page(self):
        """关注详情的图要能点开大图，用的必须是同一个灯箱，不是另写一套。

        灯箱原本写死了 `/photo?id=`：那是本地 ledger 资产的取图口，在线图没有
        asset id，套不进去。所以按 slide 归一化，在线图直接给 URL。
        """
        self.assertPageContains("poster.onclick=()=>openPhotoLightbox(Math.max(0,imagePosition),followSlides)",
                                "详情图片没有接上灯箱")
        self.assertPageContains("async function openPhotoLightbox(index,source=null)",
                                "灯箱仍只认自己的照片墙，收不下外部图集")
        self.assertPageLacks('<img src="/photo?id=${item.id}"',
                             "灯箱模板仍写死本地取图口")
        self.assertPageContains(".followdetailposter.zoomable{cursor:zoom-in}",
                                "可点开的图要有光标提示，否则没人知道能点")

    def test_a_multi_image_post_hands_the_whole_set_to_the_lightbox(self):
        """一条帖子有多张图时应当能在灯箱里左右翻完，而不是退出去再点下一张。"""
        self.assertPageContains("const followSlides=imageMedia.length")
        self.assertPageContains("src:`/follow-stream?id=${item.id}&media=${image.index}`")

    def test_online_images_show_image_info_without_the_local_reveal_action(self):
        """在线图保留图片信息入口，但不显示只对本地文件成立的资源管理器动作。"""
        self.assertPageContains("source:followMediaSourceLabel(image,item)")
        self.assertPageContains("const resolution=image?.naturalWidth&&image?.naturalHeight")
        self.assertPageContains("reveal.hidden=!asset")
        self.assertPageContains("const target=reveal.hidden?title:reveal;target.focus()")
        self.assertPageContains(".photodetail>button[hidden]{display:none}")
        self.assertPageLacks("if(!asset){toggle.hidden=true;dismiss();return}",
                             "在线图片的整个信息入口仍被隐藏")



if __name__ == "__main__":
    unittest.main()
