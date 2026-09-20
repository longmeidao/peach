"""追更的 Web 契约与页面源测试。

契约层测试用临时数据库；页面源测试守的是「追更表面」这一个语义契约，
不是某个文件——判据同 `tests/test_web_ui.py`。
"""
import hashlib
import json
import os
import re
import sqlite3
import stat
import tempfile
import threading
import unittest
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from peach import (avatar_face, follow_assets, follow_discovery, follow_store,
                   web_follow, web_stats)
from peach.follow import FollowHistoryEnd
from peach.follow import FollowSourceError
from peach.follow_discovery import Discovery, ExternalSearch
from peach.follow_secrets import CredentialError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.follow_store import FollowStore
from peach.http import HttpResponse
from support.backoff import no_real_backoff
from support.ledger import fresh_ledger
from peach.web_contract import WebContract, dispatch_api_get, dispatch_api_post
from peach.web_follow import _credential_store


ROOT = Path(__file__).resolve().parents[1]
MOMENT = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)


class FollowContractTests(unittest.TestCase):
    def test_background_check_exposes_progress_and_deduplicates(self):
        self._seed()
        entered, release = threading.Event(), threading.Event()
        original = web_follow.run_check
        def slow(*args, **kwargs):
            entered.set()
            release.wait(5)
            return original(*args, **kwargs)
        with mock.patch.object(web_follow, 'run_check', side_effect=slow), \
             mock.patch.object(web_follow, 'build_connector') as factory:
            factory.return_value.fetch.side_effect = FollowSourceError('offline')
            started = self._post('/api/follow/check', {'background': True})
            try:
                self.assertTrue(entered.wait(2))
                snapshot = web_follow.q_follow_check(self.contract, {})
                self.assertEqual(snapshot['job_id'], started['job_id'])
                self.assertEqual(snapshot['total'], 1)
                self.assertEqual(snapshot['checked'], 0)
                duplicate = self._post('/api/follow/check', {'background': True, 'older': True})
                self.assertEqual(duplicate['job_id'], started['job_id'])
            finally:
                release.set()
                self.contract.follow_job.thread.join(5)
        final = web_follow.q_follow_check(self.contract, {})
        self.assertEqual(final['status'], 'complete')
        self.assertEqual(final['checked'], 1)
        self.assertFalse(final['results'][0]['ok'])
        self.assertEqual(factory.call_count, 1)

    def test_discovery_result_can_be_read_after_request_returns(self):
        started = self._post('/api/follow/resolve', {'background': True,
            'lines': ['https://rule34video.com/models/sample/']})
        self.contract.follow_resolve_job.thread.join(5)
        final = dispatch_api_get(self.contract, '/api/follow/resolve', {})
        self.assertEqual(final['job_id'], started['job_id'])
        self.assertEqual(final['status'], 'complete')
        self.assertEqual(len(final['results']), 1)

    def test_background_check_records_unexpected_failure(self):
        self._seed()
        with mock.patch.object(web_follow, 'run_check', side_effect=RuntimeError('test failure')):
            self._post('/api/follow/check', {'background': True})
            self.contract.follow_job.thread.join(5)
        state = web_follow.q_follow_check(self.contract, {})
        self.assertEqual(state['status'], 'failed')
        self.assertIn('test failure', state['error'])
        self.assertFalse(self.contract.follow_check_lock.locked())

    def test_background_taste_refresh_has_a_readable_result(self):
        self.contract.taste_history_store = self.root / 'missing-history.sqlite'
        with mock.patch.object(web_stats, 'discover_history_sources', return_value=[]), \
             mock.patch.object(web_stats, 'q_taste', return_value={'demo': True}):
            started = self._post('/api/taste/refresh', {'background': True})
            self.contract.taste_refresh_job.thread.join(5)
        final = dispatch_api_get(self.contract, '/api/taste/refresh', {})
        self.assertEqual(final['job_id'], started['job_id'])
        self.assertEqual(final['status'], 'complete')
        self.assertEqual(final['dashboard'], {'demo': True})

    def test_selected_sources_do_not_expand_to_the_whole_follow_list(self):
        selected = self._seed(ref='selected')
        self._seed(ref='unrelated')
        with mock.patch.object(web_follow, 'build_connector') as factory:
            factory.return_value.fetch.side_effect = FollowSourceError('offline')
            result = self._post('/api/follow/check', {'sources': [selected]})
        self.assertEqual([row['source'] for row in result['results']], [selected])
        self.assertEqual(factory.call_count, 1)

    def test_failed_numeric_source_has_a_readable_author(self):
        source = self._seed(ref='patreon/12387984', label='Pantsushi · patreon')
        with mock.patch.object(web_follow, 'build_connector') as factory:
            factory.return_value.fetch.side_effect = FollowSourceError('offline')
            result = self._post('/api/follow/check', {'sources': [source]})
        self.assertEqual(result['results'][0]['author'], 'Pantsushi')

    def test_background_prune_keeps_the_confirmation_and_expiry_gate(self):
        refused = self._post('/api/links/prune', {'background': True})
        self.assertFalse(refused['ok'])
        self.assertIsNone(self.contract.link_prune_job.snapshot())
        self._post('/api/links/prune', {'background': True, 'confirm': True, 'check_id': 'expired'})
        self.contract.link_prune_job.thread.join(5)
        final = dispatch_api_get(self.contract, '/api/links/prune', {})
        self.assertEqual(final['status'], 'failed')
        self.assertFalse(final['ok'])

    def test_background_resource_apply_has_a_queryable_receipt(self):
        from peach import web_resource_sync
        with mock.patch.object(web_resource_sync, '_scan_missing_resources',
                               return_value={'sources': [], 'missing_ids': []}), \
             mock.patch.object(web_resource_sync, 'clean_resource_orphans',
                               return_value={'cache_removed': 0, 'bytes_reclaimed': 0}):
            started = self._post('/api/resource-sync/apply', {'background': True, 'confirm': True})
            self.contract.resource_apply_job.thread.join(5)
        final = dispatch_api_get(self.contract, '/api/resource-sync/apply', {})
        self.assertEqual(final['job_id'], started['job_id'])
        self.assertEqual(final['status'], 'complete')
        self.assertEqual(final['moved_to_trash'], 0)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.db = fresh_ledger(self.root)
        self.contract = WebContract(
            self.db, follow_sources_root=self.root / "sources",
            follow_secrets_root=self.root / "secrets",
            follow_shared_root=self.root / "shared",
            # 题材圆标的取景从这个目录下的 sidecar 读。不给临时目录的话，判据变成
            # 「这台机器上碰巧缓存过哪些题材图」，同一份代码换台机器就是另一个结果。
            candidate_root=self.root / "generated",
            # 状态根同理：创作者清单在那里，不给就会读到这台机器上的 42 万个名字，
            # 快慢和结果都由本机状态决定。
            follow_state_root=self.root / "state")

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

    def test_saved_catalog_media_uses_the_follow_cover_and_content_tags(self):
        self._seed(candidates=(FollowCandidate(
            provider='rule34video', external_id='saved-media', title='Demo video',
            url='https://example.test/post', media_url='https://example.test/movie.mp4',
            thumb_url='https://example.test/cover.jpg', duration=20,
            extra={'tags': ['animation', 'artist_name'],
                   'tag_types': {'animation': 'general', 'artist_name': 'artist'}},
        ),))
        with self.contract.database.write_transaction() as connection:
            store = FollowStore(lambda: connection)
            item = store.items()[0]
            asset_id = store.save_asset(item.id, confirm=True)
        follow = self._get(item=str(item.id))['groups'][0]['primary']
        catalog = self._get('/api/items', loc='online')['items'][0]
        self.assertEqual(catalog['id'], asset_id)
        self.assertEqual(catalog['follow_item_id'], item.id)
        self.assertEqual(catalog['follow_thumb_url'], follow['thumb_url'])
        self.assertEqual(catalog['follow_tags'], follow['tags'])
        self.assertNotIn('artist_name', catalog['follow_tags'])
        detail = self._get('/api/item', id=str(asset_id))
        self.assertEqual(detail['follow_item_id'], item.id)
        online = self._get('/api/facets', loc='online')
        self.assertEqual([row['k'] for row in online['follow_tags']], follow['tags'])
        self.assertEqual(self._get('/api/facets', loc='local')['follow_tags'], [])

    def test_unsaved_follow_tags_do_not_enter_catalog_facets(self):
        self._seed(candidates=(FollowCandidate(
            provider='rule34video', external_id='unsaved', title='Demo video',
            url='https://example.test/unsaved', duration=20,
            extra={'tags': ['animation'], 'tag_types': {'animation': 'general'}},
        ),))
        self.assertTrue(self._get('/api/follow/tags')['items'])
        self.assertEqual(self._get('/api/facets')['tags'], [])
        self.assertEqual(self._get('/api/facets')['follow_tags'], [])

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

    def test_history_walk_flags_are_refused_without_older(self):
        # 不带 older 时这两个参数什么都不做；拒收，免得一轮常规检查被当成重抓过了。
        self._seed()
        factory = mock.Mock()
        with mock.patch.object(web_follow, "build_connector", factory):
            for body in ({"backfill_all": True}, {"rewind": True},
                         {"backfill_all": True, "rewind": True}):
                with self.subTest(body=body), self.assertRaises(ValueError):
                    self._post("/api/follow/check", body)
        factory.assert_not_called()

    def test_backfill_all_walks_pages_until_history_ends(self):
        self._seed()
        pages = []

        class _Paged:
            provider, semantics = "rule34video", "work"

            def fetch(self, ref, *, etag=None, last_modified=None, page=0):
                pages.append(page)
                if page > 3:
                    raise FollowHistoryEnd("没有更多历史内容")
                return SourceFetch(provider="rule34video", ref=ref,
                                   request_url="https://rule34video.test/x",
                                   semantics="work", candidates=(), raw_body=b"<html/>")

        original = web_follow.build_connector
        web_follow.build_connector = lambda provider, **kwargs: _Paged()
        self.addCleanup(setattr, web_follow, "build_connector", original)

        result = self._post("/api/follow/check", {"older": True, "backfill_all": True})
        # 从游标 0 起步：抓 1、2、3，第 4 页就是尽头；游标停在最后成功的那页。
        self.assertEqual(pages, [1, 2, 3, 4])
        self.assertTrue(result["results"][0]["exhausted"])
        with self.contract.database.read_connection() as connection:
            state = connection.execute(
                "SELECT backfill_page FROM follow_source WHERE id=?",
                (self._get()["groups"][0]["primary"]["source_id"],)).fetchone()[0]
        self.assertEqual(state, 3)

    def test_rewind_walks_from_the_first_page_again(self):
        self._seed()
        pages = []

        class _Paged:
            provider, semantics = "rule34video", "work"

            def fetch(self, ref, *, etag=None, last_modified=None, page=0):
                pages.append(page)
                if page > 2:
                    raise FollowHistoryEnd("没有更多历史内容")
                return SourceFetch(provider="rule34video", ref=ref,
                                   request_url="https://rule34video.test/x",
                                   semantics="work", candidates=(), raw_body=b"<html/>")

        original = web_follow.build_connector
        web_follow.build_connector = lambda provider, **kwargs: _Paged()
        self.addCleanup(setattr, web_follow, "build_connector", original)

        # 游标已经走到尽头（backfill_page=3）；rewind 把起点拨回页首重走一遍，
        # ledger 里的游标由 record 的 max() 守着，不倒退。
        source_id = self._get()["groups"][0]["primary"]["source_id"]
        with self.contract.database.write_transaction() as connection:
            connection.execute("UPDATE follow_source SET backfill_page=3 WHERE id=?",
                               (source_id,))

        result = self._post("/api/follow/check",
                            {"older": True, "backfill_all": True, "rewind": True})
        self.assertEqual(pages, [1, 2, 3])
        self.assertTrue(result["results"][0]["exhausted"])
        with self.contract.database.read_connection() as connection:
            state = connection.execute(
                "SELECT backfill_page FROM follow_source WHERE id=?", (source_id,)
            ).fetchone()[0]
        self.assertEqual(state, 3)

    def test_a_pending_first_page_replays_once_before_walking_older_pages(self):
        # 首轮检查按时间窗跳过过历史的来源，回抓先把第 0 页重放一次；之后从第 1 页往下走，
        # 不能每一轮都重放第 0 页。
        self._seed()
        pages = []

        class _Paged:
            provider, semantics = "rule34video", "work"

            def fetch(self, ref, *, etag=None, last_modified=None, page=0):
                pages.append(page)
                if len(pages) > 6 or page > 2:
                    raise FollowHistoryEnd("没有更多历史内容")
                return SourceFetch(provider="rule34video", ref=ref,
                                   request_url="https://rule34video.test/x",
                                   semantics="work", candidates=(), raw_body=b"<html/>")

        original = web_follow.build_connector
        web_follow.build_connector = lambda provider, **kwargs: _Paged()
        self.addCleanup(setattr, web_follow, "build_connector", original)
        source_id = self._get()["groups"][0]["primary"]["source_id"]
        with self.contract.database.write_transaction() as connection:
            connection.execute(
                "UPDATE follow_source SET metadata_json=json_set(COALESCE(metadata_json,'{}'),"
                " '$.initial_history_first_page_pending', json('true')) WHERE id=?",
                (source_id,))

        result = self._post("/api/follow/check",
                            {"older": True, "backfill_all": True, "rewind": True})
        self.assertEqual(pages, [0, 1, 2, 3])
        self.assertTrue(result["results"][0]["exhausted"])

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

    def test_confirmed_discussion_attachment_projects_a_gofile_placeholder(self):
        image = "https://attachments.f95zone.to/2026/09/6456143_attachment-3.gif"
        self._seed(candidates=(FollowCandidate(
            provider="f95zone", external_id="21521132", title="Collection",
            url="https://f95zone.to/threads/62305/post-21521132",
            media_url="https://f95zone.to/masked/gofile.io/62305/resource",
            thumb_url=image,
            extra={"attachments": [image], "links": ["https://gofile.io/d/resource"],
                   "media_items": [{"url": image, "thumb_url": image,
                                    "media_kind": "image", "resource_provider": "f95zone"}]},
        ),), provider="f95zone", ref="62305", semantics="release")
        item = self._get()["groups"][0]["primary"]
        self.assertIsNone(item["thumb_url"])
        self.assertEqual(item["media_items"], [])
        self.assertEqual(item["media_kind"], "external")
        self.assertEqual(item["resource_provider"], "gofile")
        self.assertFalse(item["playable"])
        self.assertEqual(item["resource_urls"], ["https://gofile.io/d/resource"])

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

    def test_fanbox_video_poster_uses_cover_when_missing_or_a_video_url(self):
        video = "https://downloads.fanbox.cc/files/example.mp4"
        image = "https://downloads.fanbox.cc/images/example.jpeg"
        self._seed(candidates=tuple(FollowCandidate(
            provider="fanbox", external_id=str(index), title=f"Clip {index}",
            url=f"https://creator.fanbox.cc/posts/{index}", thumb_url=thumb,
            extra={"media_items": [{"media_kind": "video", "resource_provider": "fanbox", "url": video}]},
        ) for index, thumb in enumerate((None, video, image), 1)), provider="fanbox", ref="creator")
        items = {group["primary"]["external_id"]: group["primary"] for group in self._get()["groups"]}
        for key in ("1", "2"):
            self.assertEqual(items[key]["thumb_url"], f"/follow-cover?id={items[key]['id']}")
        self.assertEqual(items["3"]["thumb_url"], image)

    def test_fanbox_card_thumb_prefers_the_author_cover(self):
        chart = "https://downloads.fanbox.cc/images/post/1/w/1200/chart.jpeg"
        art = "https://downloads.fanbox.cc/images/post/1/w/1200/art.jpeg"
        cover = ("https://pixiv.pximg.net/c/1200x630_90_a2_g5/fanbox/public/"
                 "images/post/1/cover/abc.jpeg")
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="1", title="Post",
            url="https://lazyprocrast.fanbox.cc/posts/1", thumb_url=chart,
            extra={"media_items": [
                {"id": "chart", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/chart.png",
                 "thumb_url": chart},
                {"id": "art", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/art.png",
                 "thumb_url": art},
                {"id": "cover", "media_kind": "image", "resource_provider": "fanbox",
                 "url": cover, "thumb_url": cover},
            ]}),), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["thumb_url"], cover)

        self._post("/api/follow/media/hide", {"item": item["id"], "media": 2, "hidden": True})
        item = self._get()["groups"][0]["primary"]
        # 封面被隐藏后卡面退回正文首图。
        self.assertEqual(item["thumb_url"], chart)

    def test_poll_post_drops_the_leading_chart_for_its_author(self):
        chart = "https://downloads.fanbox.cc/images/post/1/w/1200/chart.jpeg"
        art = "https://downloads.fanbox.cc/images/post/1/w/1200/art.jpeg"
        cover = ("https://pixiv.pximg.net/c/1200x630_90_a2_g5/fanbox/public/"
                 "images/post/1/cover/abc.jpeg")
        media = [
            {"id": "chart", "media_kind": "image", "resource_provider": "fanbox",
             "url": "https://downloads.fanbox.cc/images/post/1/chart.png",
             "thumb_url": chart},
            {"id": "art", "media_kind": "image", "resource_provider": "fanbox",
             "url": "https://downloads.fanbox.cc/images/post/1/art.png",
             "thumb_url": art},
            {"id": "cover", "media_kind": "image", "resource_provider": "fanbox",
             "url": cover, "thumb_url": cover},
        ]
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="1", title="Poll Results + Scheduling Talk",
            url="https://lazyprocrast.fanbox.cc/posts/1", thumb_url=chart,
            extra={"media_items": media}),), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        # 首位图表不投影；序号保持原始下标，卡面用作者封面。
        self.assertEqual([media_["index"] for media_ in item["media_items"]], [1, 2])
        self.assertEqual(item["thumb_url"], cover)

        self._post("/api/follow/media/hide", {"item": item["id"], "media": 2, "hidden": True})
        item = self._get()["groups"][0]["primary"]
        # 封面被隐藏后卡面跳过首位的图表，落在正文第二张。
        self.assertEqual(item["thumb_url"], art)

    def test_poll_leading_chart_stays_for_other_creators(self):
        chart = "https://downloads.fanbox.cc/images/post/1/w/1200/chart.jpeg"
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="2", title="Poll Results",
            url="https://someoneelse.fanbox.cc/posts/2", thumb_url=chart,
            extra={"media_items": [
                {"id": "chart", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/chart.png",
                 "thumb_url": chart},
            ]}),), provider="fanbox", ref="someoneelse")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual([media_["index"] for media_ in item["media_items"]], [0])

    def test_media_projection_carries_intrinsic_dimensions(self):
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="1", title="Post",
            url="https://lazyprocrast.fanbox.cc/posts/1",
            extra={"media_items": [
                {"id": "art", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/art.png",
                 "thumb_url": "https://downloads.fanbox.cc/images/post/1/w/1200/art.jpeg",
                 "width": 1920, "height": 1080},
                {"id": "mystery", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/m.png"},
            ]}),), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["media_items"][0]["width"], 1920)
        self.assertEqual(item["media_items"][0]["height"], 1080)
        self.assertIsNone(item["media_items"][1]["width"])
        self.assertIsNone(item["media_items"][1]["height"])

    def _items_by_external_id(self) -> dict:
        found = {}
        for group in self._get()["groups"]:
            for item in (group["primary"], *group["variants"], *group["duplicates"]):
                found[item["external_id"]] = item
        return found

    def _rule34_image(self, external_id, **extra):
        return FollowCandidate(
            provider="rule34xxx", external_id=external_id, title="fiona",
            url=f"https://rule34.xxx/index.php?page=post&s=view&id={external_id}",
            media_url=f"https://api-cdn.rule34.xxx/images/1/{external_id}.jpg",
            thumb_url=f"https://api-cdn.rule34.xxx/samples/1/{external_id}.jpg",
            extra={"tag": "lazyprocrastinator", **extra})

    def test_item_level_dimensions_come_from_the_listing_and_the_browser_fills_the_gaps(self):
        """直链图片的宽高与 media_items 里那对同义；没有的条目由界面加载完回写，只补空缺。"""
        self._seed(candidates=(self._rule34_image("1", width=1280, height=720),
                               self._rule34_image("2")),
                   provider="rule34xxx", ref="lazyprocrastinator")
        items = self._items_by_external_id()
        self.assertEqual((items["1"]["width"], items["1"]["height"]), (1280, 720))
        self.assertIsNone(items["2"]["width"])
        self.assertIsNone(items["2"]["height"])

        result = self._post("/api/follow/image-dims", {"entries": [
            {"item": items["2"]["id"], "width": 900, "height": 1600},
            {"item": items["1"]["id"], "width": 1, "height": 1},
            {"item": items["2"]["id"] + 500, "width": 10, "height": 10},
        ]})

        self.assertEqual(result["learned"], 1, "已有尺寸的与不存在的条目都不算学到")
        items = self._items_by_external_id()
        self.assertEqual((items["2"]["width"], items["2"]["height"]), (900, 1600))
        self.assertEqual((items["1"]["width"], items["1"]["height"]), (1280, 720))

    def test_media_level_dimensions_are_learned_by_media_index(self):
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="1", title="Post",
            url="https://lazyprocrast.fanbox.cc/posts/1",
            extra={"media_items": [
                {"id": "art", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/art.png"},
                {"id": "sketch", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/sketch.png"},
            ]}),), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        result = self._post("/api/follow/image-dims", {"entries": [
            {"item": item["id"], "media": 1, "width": 1200, "height": 1600}]})
        self.assertEqual(result["learned"], 1)
        item = self._get()["groups"][0]["primary"]
        self.assertIsNone(item["media_items"][0]["width"])
        self.assertEqual((item["media_items"][1]["width"], item["media_items"][1]["height"]),
                         (1200, 1600))
        self.assertIsNone(item["width"], "媒体级尺寸不落到条目级")

    def test_image_dims_refuse_malformed_batches(self):
        self._seed()
        item = self._get()["groups"][0]["primary"]
        for body in ({"entries": {"item": item["id"]}},
                     {"entries": [{"item": item["id"], "width": 0, "height": 10}]},
                     {"entries": [{"item": item["id"], "width": "x", "height": 10}]},
                     {"entries": [{"item": item["id"], "width": 1, "height": 1}] * 201}):
            with self.subTest(body=str(body)[:60]), self.assertRaises(ValueError):
                self._post("/api/follow/image-dims", body)

    def test_hidden_media_leaves_the_feed_and_the_card_thumb(self):
        chart = "https://downloads.fanbox.cc/images/post/1/w/1200/chart.jpeg"
        art = "https://downloads.fanbox.cc/images/post/1/w/1200/art.jpeg"
        self._seed(candidates=(FollowCandidate(
            provider="fanbox", external_id="12565427", title="Public Release Notes",
            url="https://lazyprocrast.fanbox.cc/posts/12565427", thumb_url=chart,
            extra={"media_items": [
                {"id": "chart", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/chart.png",
                 "thumb_url": chart},
                {"id": "art", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/art.png",
                 "thumb_url": art},
            ]}),), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        self.assertEqual(item["thumb_url"], chart)

        result = self._post("/api/follow/media/hide",
                            {"item": item["id"], "media": 0, "hidden": True})

        self.assertEqual(result["hidden_media"], ["chart"])
        item = self._get()["groups"][0]["primary"]
        # 序号不重排：剩下的那张仍报它在原始清单里的 1，`/follow-stream?media=1` 才不会错位。
        self.assertEqual([media["index"] for media in item["media_items"]], [1])
        self.assertEqual([media["index"] for media in item["hidden_media"]], [0])
        self.assertEqual(item["thumb_url"], art)

        # 两张都藏起来：卡面不再挂任何一张被隐藏的图，走无图占位。
        self._post("/api/follow/media/hide", {"item": item["id"], "media": 1, "hidden": True})
        self.assertIsNone(self._get()["groups"][0]["primary"]["thumb_url"])
        self._post("/api/follow/media/hide", {"item": item["id"], "media": 1, "hidden": False})

        self._post("/api/follow/media/hide",
                   {"item": item["id"], "media": 0, "hidden": False})
        item = self._get()["groups"][0]["primary"]
        self.assertEqual([media["index"] for media in item["media_items"]], [0, 1])
        self.assertEqual(item["hidden_media"], [])
        self.assertEqual(item["thumb_url"], chart)

    def test_media_hidden_state_survives_a_refetch(self):
        candidate = FollowCandidate(
            provider="fanbox", external_id="12565427", title="Public Release Notes",
            url="https://lazyprocrast.fanbox.cc/posts/12565427",
            extra={"media_items": [
                {"id": "chart", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/chart.png"},
                {"id": "art", "media_kind": "image", "resource_provider": "fanbox",
                 "url": "https://downloads.fanbox.cc/images/post/1/art.png"},
            ]})
        self._seed(candidates=(candidate,), provider="fanbox", ref="lazyprocrast")
        item = self._get()["groups"][0]["primary"]
        self._post("/api/follow/media/hide", {"item": item["id"], "media": 0, "hidden": True})

        # 下一轮检查更新把整行重写一遍（完整候选走全量 SET）；
        # 用户按掉的隐藏状态在独立的列里，不在被重写的 metadata 里。
        self._seed(candidates=(candidate,), provider="fanbox", ref="lazyprocrast")

        item = self._get()["groups"][0]["primary"]
        self.assertEqual([media["index"] for media in item["media_items"]], [1])
        self.assertEqual([media["index"] for media in item["hidden_media"]], [0])

    def test_media_hide_rejects_an_out_of_range_index(self):
        self._seed()
        item = self._get()["groups"][0]["primary"]
        with self.assertRaises(ValueError):
            self._post("/api/follow/media/hide", {"item": item["id"], "media": 9})

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
        self.assertIn("attr:'data-follow-tag',value:key", page,
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

    def test_author_and_provider_filters_take_several_values_as_any_of_them(self):
        """作者与来源多选是「任一」：选两个作者就看两个人的更新。

        标签那一维是交集，这里不是：作者之间没有「同时是两个人」这回事。
        """
        self._seed(ref="a", label="Author A")
        self._seed(ref="b", label="Author B", candidates=(
            FollowCandidate(provider="rule34video", external_id="9001", title="B one",
                            url="https://rule34video.com/video/9001/x/"),))
        self._seed(ref="c", label="Author C", candidates=(
            FollowCandidate(provider="rule34video", external_id="9002", title="C one",
                            url="https://rule34video.com/video/9002/x/"),))
        whole = self._get()
        keys = {source["ref"]: source["author_key"] for source in whole["sources"]}
        two = self._get(author=f"{keys['b']},{keys['c']}")
        self.assertEqual(sorted(group["primary"]["title"] for group in two["groups"]),
                         ["B one", "C one"])
        self.assertEqual(sum(two["counts"].values()), 2)
        self.assertEqual(sum(self._get(provider="rule34video,f95zone")["counts"].values()),
                         sum(whole["counts"].values()))
        self.assertEqual(sum(self._get(provider="f95zone")["counts"].values()), 0)

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

    def _clip(self, external_id, *, duration=None, score=None, published_at=None):
        extra = {"tags": ["anal"], "tag_types": {"anal": "general"}}
        if score is not None:
            extra["score"] = score
        return FollowCandidate(
            provider="rule34video", external_id=external_id, title=f"Clip {external_id}",
            url=f"https://rule34video.com/video/{external_id}/x/",
            duration=duration, published_at=published_at, extra=extra)

    def test_the_feed_sorts_by_the_requested_column_all_the_way_to_the_groups(self):
        """排序要一直排到摆出来的那一批，不只是「取哪些条目」。

        `store.group()` 结尾无条件按 newest_at 倒序，那是它自己的默认次序。只在条目那
        一层排的话，选「时长」看到的确实是一页长片，但页面上它们内部照旧按更新时间排，
        用户看到的就是「点了没反应」。
        """
        self._seed(candidates=(
            self._clip("s1", duration=10.0, score=300, published_at="2026-01-03T00:00:00Z"),
            self._clip("s2", duration=90.0, score=100, published_at="2026-01-02T00:00:00Z"),
            self._clip("s3", duration=50.0, score=200, published_at="2026-01-01T00:00:00Z"),
        ))
        titles = lambda page: [group["primary"]["title"] for group in page["groups"]]
        self.assertEqual(titles(self._get(sort="dur")), ["Clip s2", "Clip s3", "Clip s1"])
        self.assertEqual(titles(self._get(sort="dur", dir="asc")),
                         ["Clip s1", "Clip s3", "Clip s2"])
        # 热度取来源自己的分数；没有这个字段的来源一律并列垫底，不按别的东西悄悄排。
        self.assertEqual(titles(self._get(sort="hot")), ["Clip s1", "Clip s3", "Clip s2"])
        self.assertEqual(titles(self._get(sort="new")), ["Clip s1", "Clip s2", "Clip s3"])
        self.assertEqual(titles(self._get(sort="new", dir="asc")),
                         ["Clip s3", "Clip s2", "Clip s1"])

    def test_shuffle_orders_the_feed_by_a_seed_that_holds_across_pages(self):
        """「换一批」是 `sort=rand` 加一粒种子：同一粒种子翻页不重不漏，换一粒才换一批。

        排到分组那一层，跟别的列一样；种子不是数字时按 1，手敲的地址少了它也能开。
        """
        self._seed(candidates=tuple(
            self._clip(f"r{index}", duration=float(index), published_at=f"2026-01-{index:02d}T00:00:00Z")
            for index in range(1, 8)))
        titles = lambda page: [group["primary"]["title"] for group in page["groups"]]
        first = self._get(sort="rand", seed="60000")
        self.assertEqual((first["sort"], first["seed"]), ("rand", 60000))
        self.assertEqual(titles(first), titles(self._get(sort="rand", seed="60000")))
        self.assertEqual(sorted(titles(first)), sorted(titles(self._get(sort="new"))))
        self.assertNotEqual(titles(first), titles(self._get(sort="new")))
        paged = [title for offset in ("0", "3", "6")
                 for title in titles(self._get(sort="rand", seed="60000", limit="3", offset=offset))]
        self.assertEqual(paged, titles(first))
        self.assertNotEqual(titles(self._get(sort="rand", seed="77777")), titles(first))
        self.assertEqual(self._get(sort="rand", seed="abc")["seed"], 1)

    def test_an_unknown_sort_or_direction_falls_back_without_an_error(self):
        """地址栏里存着的旧参数不该报错，也不该悄悄换成另一种排序。"""
        self._seed(candidates=(self._clip("u1", duration=10.0),))
        page = self._get(sort="size", dir="sideways")
        self.assertEqual((page["sort"], page["dir"]), ("new", "desc"))

    def test_the_online_roster_lists_follow_authors_with_the_follow_page_count(self):
        """艺人页「在线」那一档列的是关注来源里的人，每格那个数跟关注页读数同源。

        点开一位作者去关注页，那里写着多少项更新，名册上就得是同一个数；两处各按各的
        口径数（一边数发布组、一边数条目），用户看到的是两个都对、却对不上的数字。
        """
        self._seed(ref="a", label="Author A", candidates=(
            self._clip("a1", duration=10.0), self._clip("a2", duration=20.0)))
        self._seed(ref="b", label="Author B", candidates=(self._clip("b1", duration=30.0),))
        page = self._get("/api/follow/authors")
        self.assertEqual(page["kind"], "performers")
        self.assertEqual(page["scope"], "online")
        self.assertEqual([(row["k"], row["n"]) for row in page["items"]],
                         [("Author A", 2), ("Author B", 1)])
        key = next(row["key"] for row in page["items"] if row["k"] == "Author A")
        self.assertEqual(sum(self._get(author=key)["counts"].values()), 2)

    def test_the_online_roster_folds_one_persons_sources_into_one_row(self):
        """同一个人在两个站点上是两条来源、一行——身份口径跟关注页筛选条完全一样。"""
        self._seed(provider="rule34video", ref="lazyprocrastinator",
                   label="LazyProcrastinator", candidates=(self._clip("x1"),))
        self._seed(provider="rule34xxx", ref="lazyprocrastinator",
                   label="lazyprocrastinator", candidates=(FollowCandidate(
                       provider="rule34xxx", external_id="x2", title="Clip x2",
                       url="https://rule34.xxx/index.php?page=post&s=view&id=2"),))
        page = self._get("/api/follow/authors")
        self.assertEqual(len(page["items"]), 1)
        row = page["items"][0]
        self.assertEqual(row["n"], 2)
        # 同名的几种写法里取大写最多的那个：那更像作者自己写的名字。
        self.assertEqual(row["k"], "LazyProcrastinator")
        self.assertEqual(sorted(row["providers"]), ["rule34video", "rule34xxx"])

    def test_the_online_roster_supports_search_and_paging(self):
        """形状与 /api/index 一致：艺人页的分页、过滤和「载入更多」换个地址就能用。"""
        self._seed(ref="a", label="Author A", candidates=(self._clip("a1"),))
        self._seed(ref="b", label="Bravo", candidates=(self._clip("b1"),))
        self.assertEqual([row["k"] for row in
                          self._get("/api/follow/authors", q="brav")["items"]], ["Bravo"])
        first = self._get("/api/follow/authors", limit=1)
        self.assertEqual(len(first["items"]), 1)
        self.assertTrue(first["has_more"])
        self.assertFalse(self._get("/api/follow/authors", limit=1, offset=1)["has_more"])

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

    def _typed(self, external_id, tag_types, preview=""):
        extra = {"tags": list(tag_types), "tag_types": dict(tag_types)}
        if preview:
            extra["preview_url"] = preview
        return FollowCandidate(
            provider="rule34xxx", external_id=external_id, title=f"Clip {external_id}",
            url=f"https://rule34.xxx/index.php?page=post&s=view&id={external_id}",
            extra=extra)

    def test_the_works_row_only_lists_what_the_source_typed_as_a_work(self):
        """题材那一排收的是来源记成 copyright 的作品和记成 character 的人物，不按词形猜。

        `lazyprocrastinator` 是画师，字面上跟作品名没有区别，猜一次就会把它摆进
        题材那一排；`tifa_lockhart` 是人物，跟作品同排——用户追的常常是这一个人。
        写法差别不算两部作品：`zenless_zone_zero` 和 `zenless zone zero` 归到同一枚，
        键是归一后的身份，显示名把下划线换成空格、罗马数字整词大写。
        """
        self._seed(provider="rule34xxx", ref="typed", candidates=(
            self._typed("1", {"final_fantasy_vii": "copyright",
                              "tifa_lockhart": "character",
                              "lazyprocrastinator": "artist",
                              "animated": "metadata", "pov": "general"}),
            self._typed("2", {"zenless_zone_zero": "copyright"},
                        preview="https://api-cdn.rule34.xxx/thumbnails/9/z.jpg"),
            self._typed("3", {"zenless zone zero": "copyright"}),
        ))
        works = self._get()["facets"]["works"]
        # 第四位说这一枚挑不挑得出代表图，页面据它决定出不出 `<img>`；第五位是那张图
        # 检出的取景，还没取过图时是 None。
        self.assertEqual(works,
                         [["zenless zone zero", "Zenless Zone Zero", 2, 1, None],
                          ["final fantasy", "Final Fantasy", 1, 0, None],
                          ["tifa lockhart", "Tifa Lockhart", 1, 0, None]])

    def test_characters_sit_on_the_works_row_in_their_own_spelling(self):
        """人物跟作品同排，显示名按人写的形态提：`d.va` 是 D.Va，`yorha_2b` 是 Yorha 2B。

        站上末尾的括号是消歧不是名字，可能叠几层：`raven_(stellar_blade)` 摆出来是
        Raven，跟 `raven` 归到同一枚，`mona_(genshin_impact)_(cosplay)` 是 Mona。来源
        写成 `megami Tensei` 时按词提首字母，不因为后一个词带大写就整串放行；已经是
        人写形态的 `Genshin Impact` 原样留着；名字里的介词和连字符后的敬称保持小写。
        占位词和被记成 character 的种族不是人物。
        """
        self._seed(provider="rule34xxx", ref="typed", candidates=(
            self._typed("1", {"d.va": "character", "chun-li": "character",
                              "hyur": "character", "original_character": "character",
                              "you": "character"}),
            self._typed("2", {"yorha_2b": "character", "megami Tensei": "copyright",
                              "hasshaku-sama": "character"}),
            self._typed("3", {"raven_(stellar_blade)": "character",
                              "mona_(genshin_impact)_(cosplay)": "character"}),
            self._typed("4", {"raven": "character", "Genshin Impact": "copyright",
                              "emilie_de_rochefort": "character"}),
        ))
        self.assertEqual(self._get()["facets"]["works"], [
            ["raven", "Raven", 2, 0, None],
            ["chun-li", "Chun-Li", 1, 0, None],
            ["d.va", "D.Va", 1, 0, None],
            ["emilie de rochefort", "Emilie de Rochefort", 1, 0, None],
            ["genshin impact", "Genshin Impact", 1, 0, None],
            ["hasshaku-sama", "Hasshaku-sama", 1, 0, None],
            ["megami tensei", "Megami Tensei", 1, 0, None],
            ["mona", "Mona", 1, 0, None],
            ["yorha 2b", "Yorha 2B", 1, 0, None],
        ])
        self.assertEqual(sum(self._get(work="raven")["counts"].values()), 2,
                         "带消歧括号和不带的是同一个人，按下要一起筛到")
        self.assertEqual(sum(self._get(work="d.va")["counts"].values()), 1)

    def test_the_works_row_hands_the_page_the_framing_of_the_cover_it_has(self):
        """取过图的题材带上那张图的取景：挪到哪，还有那张脸有多少像素。

        圆标只有 28px，而圆里是一整张作品图不是烤好边距的头像：只挪不放大的话，脸在
        图里占多少、在这枚圆里就占多少。两样都按实体图那套 sidecar 的形状给，页面于是
        走同一个放大函数。
        """
        self._seed(provider="rule34xxx", ref="typed", candidates=(
            self._typed("1", {"stellar blade": "copyright"},
                        preview="https://api-cdn.rule34.xxx/thumbnails/9/s.jpg"),
        ))
        cached = follow_assets.cache_path(
            self.contract.candidate_root / follow_assets.ROOT_NAME, "works",
            "stellar blade")
        cached.parent.mkdir(parents=True, exist_ok=True)
        avatar_face.write_sidecar(cached, {
            "ratio": 0.563, "px": [144, 256],
            "face": {"cx": 0.5, "cy": 0.2, "w": 0.2, "h": 0.18, "score": 0.9},
            "focus": {"axis": "y", "pct": 17}})
        self.assertEqual(
            self._get()["facets"]["works"],
            [["stellar blade", "Stellar Blade", 1, 1,
              {"axis": "y", "pct": 17,
               "box": {"cx": 0.5, "cy": 0.2, "faceW": 29, "imgW": 144, "imgH": 256}}]])

    def test_one_series_is_one_pill_however_the_source_spells_each_installment(self):
        """一个系列在那一排上只占一枚。

        来源给每一代都发一个 copyright 标签，`Final Fantasy VII`、`FFXIV`、
        `Stranger of Paradise: Final Fantasy Origin` 各占一格时，那一排读起来是
        版本号列表而不是题材。一条更新同时带系列名和代号也只算一次。
        """
        self._seed(provider="rule34xxx", ref="typed", candidates=(
            self._typed("1", {"final_fantasy": "copyright",
                              "final_fantasy_vii": "copyright"}),
            self._typed("2", {"final fantasy xiv": "copyright"}),
            self._typed("3", {"ffxiv": "copyright"}),
            self._typed("4", {"stranger of paradise: final fantasy origin":
                              "copyright"}),
        ))
        self.assertEqual(self._get()["facets"]["works"],
                         [["final fantasy", "Final Fantasy", 4, 0, None]])
        self.assertEqual(sum(self._get(work="final fantasy")["counts"].values()), 4)
        self.assertEqual(sum(self._get(work="final fantasy vii")["counts"].values()), 4,
                         "书签里存着的旧写法要落在合并后的同一枚上")

    def test_publishers_holidays_and_placeholders_never_reach_the_works_row(self):
        """发行商、节庆和占位词不是题材。

        来源把它们和作品名一样记成 copyright。带法人后缀或以 Entertainment、
        Interactive、Studios、Pictures 收尾的按形态认，不用等它出现了再进名单；
        Tencent、Sonnori 这类裸名字形态上分不出来，只能按名单剔。留着的话那一排
        头几格会被 Square Enix 和 Christmas 占掉。
        """
        self._seed(provider="rule34xxx", ref="typed", candidates=(
            self._typed("1", {"stellar blade": "copyright",
                              "shift up": "copyright"}),
            self._typed("2", {"square enix": "copyright"}),
            self._typed("3", {"christmas": "copyright", "original": "copyright"}),
            self._typed("4", {"iwara": "copyright"}),
            self._typed("5", {"tencent": "copyright", "sonnori": "copyright"}),
            self._typed("6", {"sony_interactive_entertainment": "copyright",
                              "tencent_pictures": "copyright", "netflix": "copyright",
                              "some_studio_co._ltd.": "copyright"}),
        ))
        self.assertEqual(self._get()["facets"]["works"],
                         [["stellar blade", "Stellar Blade", 1, 0, None]])

    def test_a_work_filters_every_spelling_and_two_works_mean_either(self):
        """按题材筛是「任一」，而且两种写法都要筛得到。

        作者、来源也是任一；只有标签是交集。题材取交集的话，点第二枚列表就空了——
        同时属于两部作品的条目本来就几乎没有。
        """
        self._seed(provider="rule34xxx", ref="typed", candidates=(
            self._typed("1", {"zenless_zone_zero": "copyright"}),
            self._typed("2", {"zenless zone zero": "copyright"}),
            self._typed("3", {"final_fantasy_vii": "copyright"}),
            self._typed("4", {"pov": "general"}),
        ))
        self.assertEqual(sum(self._get(work="zenless zone zero")["counts"].values()), 2,
                         "两种写法是同一部作品，必须一起筛到")
        self.assertEqual(
            sum(self._get(work="zenless zone zero,final fantasy")["counts"].values()), 3,
            "选两部作品是两部都看，不是只看同时占两部的")
        self.assertEqual(
            sorted(self._get()["facets"]["works"]),
            sorted(self._get(work="final fantasy")["facets"]["works"]),
            "选中一部作品后另一部不能从那一排上消失，否则换不了题材")

    def _scored(self, item_id, score, tags, cover, preview=None, title=""):
        return SimpleNamespace(
            id=item_id, provider="rule34xxx", external_id=str(item_id),
            # 标题参与读取端的排除判据（音乐剪辑不当题材圆标），库里的行都有这一列。
            title=title, media_url=None, thumb_url=cover,
            metadata={"score": score, "preview_url": preview,
                      "tags": list(tags),
                      "tag_types": {tag: ("general" if tag == "3d" else "copyright")
                                    for tag in tags}})

    def test_the_work_icon_takes_the_cover_not_the_250px_thumbnail(self):
        """候选取的是卡片上那张高清封面，不是 250px 的缩略图。

        圆标只有 28px，两层看起来一样；差别在检脸——250px 里一张脸只剩十几个像素。
        实测本库 77 个题材，高清那层检出 58 张脸，缩略那层 49 张。没有封面的旧行才
        退回缩略图，那也好过这一枚圆标空着。
        """
        host = "https://api-cdn.rule34.xxx"
        store = SimpleNamespace(items=lambda **kwargs: (
            self._scored(1, 9, ("stellar blade", "3d"), f"{host}/samples/1/a.jpg",
                         f"{host}/thumbnails/1/a.jpg"),
            self._scored(2, 9, ("miside", "3d"), None, f"{host}/thumbnails/2/b.jpg"),
        ))
        table = web_follow._work_icon_table(store)
        self.assertEqual(table["stellar blade"]["urls"], [f"{host}/samples/1/a.jpg"])
        self.assertEqual(table["miside"]["urls"], [f"{host}/thumbnails/2/b.jpg"])

    def test_the_work_icon_candidates_are_this_librarys_hottest_3d_clips(self):
        """题材头像的候选是本库里这个题材热度最高的几条，带 `3d` 的优先。

        rule34 的 score 是站点自己的热度排序，本库里现成存着，先用它：这几张属于用户
        关注的那几位作者，不出网就能拿到。给的是一串而不是一条：最热那张常常是身体
        特写，取图那一端要顺着往下找第一张看得见脸的。地址只认登记过的图床主机：它
        来自来源记录，而记录里存的是站点回的 JSON，不该把任意主机带进出网路径。
        """
        host = "https://api-cdn.rule34.xxx/thumbnails/1"
        store = SimpleNamespace(items=lambda **kwargs: (
            self._scored(1, 900, ("stellar blade",), f"{host}/flat.jpg"),
            self._scored(2, 40, ("stellar blade", "3d"), f"{host}/spatial.jpg"),
            self._scored(3, 5, ("stellar blade", "3d"), f"{host}/quiet.jpg"),
            self._scored(4, 999, ("stellar blade", "3d"),
                         "https://images.example.invalid/best.jpg"),
            self._scored(5, 999, ("zenless zone zero", "3d"), f"{host}/other.jpg"),
        ))
        table = web_follow._work_icon_table(store)
        self.assertEqual(table["stellar blade"]["urls"],
                         [f"{host}/spatial.jpg", f"{host}/quiet.jpg",
                          f"{host}/flat.jpg"])
        self.assertEqual(table["zenless zone zero"]["urls"], [f"{host}/other.jpg"])
        self.assertNotIn("miside", table,
                         "本库里没有这个题材时不编一张图出来，那一排退回首字母")

    def test_a_work_offers_a_few_candidates_not_the_whole_library(self):
        """候选就那么几个。

        热门题材本库里有上千条，全排出来既是白排，也意味着一枚圆标最坏要去站点取
        上千次才停——一张都检不出脸时，下一张的收益早就没了。
        """
        host = "https://api-cdn.rule34.xxx/thumbnails/4"
        store = SimpleNamespace(items=lambda **kwargs: tuple(
            self._scored(index, index, ("stellar blade", "3d"), f"{host}/{index}.jpg")
            for index in range(1, 40)))
        self.assertEqual(len(web_follow._work_icon_table(store)["stellar blade"]["urls"]),
                         web_follow._WORK_ICON_CANDIDATES)

    def test_the_work_icon_follows_the_merged_series_not_one_installment(self):
        """题材头像跟着合并后的系列走。

        `Final Fantasy VII` 那一枚已经并进 `Final Fantasy`，头像要在整个系列里挑
        最热的那几条，而不是只看恰好写着系列名的那几条。
        """
        host = "https://api-cdn.rule34.xxx/thumbnails/2"
        store = SimpleNamespace(items=lambda **kwargs: (
            self._scored(1, 10, ("final fantasy", "3d"), f"{host}/series.jpg"),
            self._scored(2, 700, ("final fantasy vii remake", "3d"),
                         f"{host}/remake.jpg"),
        ))
        self.assertEqual(web_follow._work_icon_table(store)["final fantasy"]["urls"],
                         [f"{host}/remake.jpg", f"{host}/series.jpg"])

    def test_one_scan_answers_every_work_icon_asked_for_in_the_same_minute(self):
        """整排头像同时到期时只扫一遍库。

        那一排二十几枚，浏览器会并排发来同样多个 `/work-icon`；每个都从头扫一遍
        全库、把几千条 metadata 重解析一次的话，服务在这段时间里干不了别的。
        """
        host = "https://api-cdn.rule34.xxx/thumbnails/3"
        scans = []

        def items(**kwargs):
            scans.append(1)
            return (self._scored(1, 5, ("stellar blade", "3d"), f"{host}/a.jpg"),
                    self._scored(2, 5, ("miside", "3d"), f"{host}/b.jpg"))

        web_follow._work_icon_memo = (0.0, {})
        try:
            store = SimpleNamespace(items=items)
            self.assertEqual(web_follow.work_icon_urls(store, "stellar blade"),
                             [f"{host}/a.jpg"])
            self.assertEqual(web_follow.work_icon_urls(store, "miside"),
                             [f"{host}/b.jpg"])
            self.assertEqual(len(scans), 1)
        finally:
            web_follow._work_icon_memo = (0.0, {})

    def test_the_site_tag_is_the_spelling_this_library_recorded_not_the_identity(self):
        """去站上查用的是本库记下的那个写法。

        题材身份是把 `the_witcher_(series)` 这类写法抹平之后的结果，照着它拼出来的
        标签在站上是零命中。同一个题材记着几种写法时取用得最多的那个：它才是这个库
        实际在追的那条线。
        """
        host = "https://api-cdn.rule34.xxx/thumbnails/5"
        store = SimpleNamespace(items=lambda **kwargs: (
            self._scored(1, 9, ("the witcher (series)", "3d"), f"{host}/a.jpg"),
            self._scored(2, 8, ("the witcher (series)", "3d"), f"{host}/b.jpg"),
            self._scored(3, 7, ("the witcher", "3d"), f"{host}/c.jpg"),
        ))
        self.assertEqual(web_follow._work_icon_table(store)["the witcher"]["tag"],
                         "the_witcher_(series)")

    def test_a_work_the_library_never_recorded_falls_back_to_its_own_name(self):
        """本库没记下写法时按题材身份拼一个，总好过不去问。"""
        web_follow._work_icon_memo = (0.0, {})
        self.addCleanup(setattr, web_follow, "_work_icon_memo", (0.0, {}))
        store = SimpleNamespace(items=lambda **kwargs: ())
        self.assertEqual(web_follow.work_icon_tag(store, "stellar blade"),
                         "stellar_blade")

    def _rule34_credential(self):
        self._post("/api/follow/credential", {
            "provider": "rule34xxx", "values": {"user_id": "42", "api_key": "sekret"}})

    @staticmethod
    def _posts(*urls):
        return json.dumps([{"id": index, "image": f"{index}.jpg",
                            "tags": "the_witcher_(series) 3d", "sample_url": url}
                           for index, url in enumerate(urls, 1)]).encode()

    def test_a_work_with_no_usable_cover_here_asks_the_site_for_one(self):
        """本库那几张都看不清脸时，去站上问这个题材最热的几张。

        库里存的是用户关注的那几位作者发的东西，一个题材常常只有一两条，那一两条
        未必有正脸；站上同一个标签下有成千上万帖，按热度往下找总能找到一张。先只要
        3D——这一排要的是 3D 作品。地址仍只认登记过的图床主机：它来自站点回的 JSON，
        不该把任意主机带进出网路径。
        """
        self._rule34_credential()
        seen = []

        def transport(request, timeout, max_bytes):
            seen.append(request.url)
            return HttpResponse(200, {}, self._posts(
                "https://api-cdn.rule34.xxx/images/1/a.jpg",
                "https://images.example.invalid/b.jpg"))

        urls = web_follow.work_icon_search_urls(
            self.contract, "the_witcher_(series)", transport=transport, limit=4)
        self.assertEqual(urls, ["https://api-cdn.rule34.xxx/images/1/a.jpg"])
        self.assertEqual(len(seen), 1, "3D 那一问有结果就不再问第二遍")
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(seen[0]).query)
        self.assertEqual(query["tags"], ["the_witcher_(series) 3d sort:score"])
        self.assertEqual(query["limit"], ["4"])

    def test_a_work_with_nothing_tagged_3d_asks_again_without_that_tag(self):
        """`3d` 下一张都没有时再问一次不限形式的，总好过让这一枚空着。"""
        self._rule34_credential()
        seen = []

        def transport(request, timeout, max_bytes):
            seen.append(request.url)
            # rule34.xxx 的零命中响应是 HTTP 200 加空正文，不是 JSON `[]`。
            if "3d" in request.url:
                return HttpResponse(200, {}, b" \r\n")
            return HttpResponse(200, {}, self._posts(
                "https://api-cdn.rule34.xxx/images/2/c.jpg"))

        urls = web_follow.work_icon_search_urls(
            self.contract, "the_witcher_(series)", transport=transport)
        self.assertEqual(urls, ["https://api-cdn.rule34.xxx/images/2/c.jpg"])
        self.assertEqual(len(seen), 2)

    def test_without_a_rule34_credential_the_icon_never_reaches_the_site(self):
        seen = []

        def transport(request, timeout, max_bytes):
            seen.append(request.url)
            return HttpResponse(200, {}, b"[]")

        self.assertEqual(web_follow.work_icon_search_urls(
            self.contract, "the_witcher_(series)", transport=transport), [])
        self.assertEqual(seen, [], "没有凭据就不出网，圆标退回首字母")

    def test_the_site_being_unreachable_leaves_the_icon_to_the_letter(self):
        """站点报错或网络不通时立刻返回空——这一枚退回首字母，不是一个 500，也不等退避。"""
        self._rule34_credential()

        def transport(request, timeout, max_bytes):
            raise OSError("网络不通")

        with no_real_backoff():
            self.assertEqual(web_follow.work_icon_search_urls(
                self.contract, "the_witcher_(series)", transport=transport), [])

    def test_counts_are_whole_library_while_groups_are_one_page(self):
        """计数是全库口径，列表只有一页——界面并排显示这两个数时看起来像自相矛盾。

        用户实测：状态条写着「未看 2292」，下面视频 220 + 图片 11 只有 231。
        两个数都对，差的是口径，所以响应必须带上 has_more 让界面能说清楚、能续取。
        """
        # 一页数的是组：种两部作品，一页只装一部。
        self._seed(candidates=(
            FollowCandidate(provider="rule34video", external_id="1", title="Fiona - Paizuri",
                            published_at="2026-08-18T00:00:00Z"),
            FollowCandidate(provider="rule34video", external_id="2", title="Sayuri - Cowgirl",
                            published_at="2026-08-17T00:00:00Z"),
        ))
        page = self._get(limit=1)
        self.assertEqual(page["limit"], 1)
        self.assertEqual(page["offset"], 0)
        self.assertTrue(page["has_more"], "还有作品没取，has_more 必须为真")
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

    def test_a_page_counts_groups_so_one_work_never_splits_across_pages(self):
        """按条目切页再分组的话，同一作品夹着别的条目时会落在两页，页面上是两张卡。"""
        self._seed(candidates=(
            FollowCandidate(provider="rule34video", external_id="1", title="Sunset [4K]",
                            published_at="2026-08-20T00:00:00Z"),
            FollowCandidate(provider="rule34video", external_id="2", title="Beach",
                            published_at="2026-08-19T00:00:00Z"),
            FollowCandidate(provider="rule34video", external_id="3", title="Sunset [1080p]",
                            published_at="2026-08-18T00:00:00Z"),
        ))
        page = self._get(limit=1)
        self.assertTrue(page["has_more"])
        self.assertEqual([sorted(row["external_id"] for row in (group["primary"], *group["variants"]))
                          for group in page["groups"]], [["1", "3"]])
        self.assertFalse(self._get(limit=2)["has_more"])

    def test_one_work_the_author_uploaded_to_two_sites_is_one_card(self):
        """rule34video 的标题里夹着作者名，FANBOX 镜像上没有；两条来源都没绑实体。"""
        self._seed(candidates=(FollowCandidate(
            provider="kemono", external_id="f1", title="2B Love at Sunset - 1080p",
            published_at="2026-08-31T23:59:24Z"),), provider="kemono",
            ref="fanbox/30917150", label="Pantsushi · fanbox")
        self._seed(candidates=(FollowCandidate(
            provider="rule34video", external_id="v1", title="2B Love at Sunset [pantsushi] 4K",
            url="https://rule34video.com/video/1/x/", published_at="2026-09-02T00:00:00Z"),),
            ref="pantsushi", label="pantsushi")
        groups = self._get()["groups"]
        self.assertEqual(len(groups), 1)
        members = [groups[0]["primary"], *groups[0]["variants"], *groups[0]["duplicates"]]
        self.assertEqual(sorted(row["external_id"] for row in members), ["f1", "v1"])
        for row in members:
            with self.subTest(item=row["external_id"]):
                direct = self._get(item=str(row["id"]))["groups"]
                self.assertEqual(sorted(member["external_id"] for member in (
                    direct[0]["primary"], *direct[0]["variants"], *direct[0]["duplicates"])),
                    ["f1", "v1"])

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
        self.assertFalse(by_provider["gofile"]["followable"])
        self.assertTrue(by_provider["fanbox"]["followable"])
        self.assertTrue(by_provider["f95zone"]["followable"])
        self.assertTrue(by_provider["gofile"]["path"].endswith("gofile.json"))
        self.assertEqual(by_provider["simpcity"]["requirement"], "required")
        self.assertEqual(by_provider["simpcity"]["needs"], ["cookie"])
        self.assertIn("游客", by_provider["simpcity"]["why"])
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

        `describe()` 只看本机文件而 `load()` 从共享副本回填的话，页面报「未配置」
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


class FollowFeedExclusionTests(unittest.TestCase):
    """读取关注流时挡掉的几类，判据和采集端、清退脚本是同一份。"""

    # 借夹具不继承：继承会把上面那一整套契约用例再跑一遍，这一组只要临时库和
    # 一份种子数据。
    setUp = FollowContractTests.setUp
    _seed = FollowContractTests._seed
    _get = FollowContractTests._get

    def _listed(self, *candidates):
        self._seed(candidates=candidates)
        return {row["external_id"] for group in self._get()["groups"]
                for row in (group["primary"], *group["variants"])}

    @staticmethod
    def _candidate(external_id, title, models=(), **extra):
        return FollowCandidate(
            provider="rule34video", external_id=external_id, title=title,
            url=f"https://rule34video.com/video/{external_id}/x/",
            extra={"models": list(models), "model_count": len(models), **extra})

    def test_a_music_edit_is_kept_out_by_its_title(self):
        """PMV、HMV 是把许多人的片段剪到一首曲子上，署名数量拦不住也要挡。"""
        self.assertEqual(
            self._listed(self._candidate("1", "Fuck Track / Futa PMV / Dope Track"),
                         self._candidate("2", "Ahri pmvideo review")),
            {"2"}, "独立词才算，`pmvideo` 里的那三个字母不是")

    def test_a_pack_saved_before_the_count_existed_is_recounted_on_read(self):
        """历史条目的 metadata 里只有 `models`，按同一份判据当场数一遍。

        采集端的门槛读 `visual_model_count`，库里有一批行没有这个字段：超出探测
        上限、详情没取到的那些。门槛在它们身上不生效，读取时就得自己数。
        """
        self.assertEqual(
            self._listed(self._candidate("3", "Resident Evil - The Fallen Saga",
                                         [f"M{n}" for n in range(14)])),
            set())

    def test_voice_and_audio_credits_do_not_make_a_work_a_pack(self):
        """配音和音效记在同一份 Artist 名单里，只数画面作者。

        门槛是超过 3 位：复核 623 条的结论是普通作品剔掉配音后剩 1 到 2 位。
        收到「超过 1 位就算」会把两个人合作的普通作品一起扫掉。
        """
        self.assertEqual(
            self._listed(self._candidate(
                "4", "Yunara Showing Ahri Some Discipline",
                ["Iidssm", "Adaline (VA)", "GeminiStarsign1 (VA)",
                 "Huntress___ (Audio/SFX)", "HentAudio (Audio)"]),
                self._candidate("5", "Two artists, one scene", ["Iidssm", "Adaline"])),
            {"4", "5"})


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

    def test_discovery_profile_aliases_are_saved_with_the_source_in_one_step(self):
        """勾选登记名片手柄查到的来源就是确认；别名不再落进待合并等第二次点。"""
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.return_value = SourceFetch(
                provider="rule34xxx", ref="ceeeeekc",
                request_url="https://rule34.xxx/x", semantics="work",
                not_modified=True)
            added = self._post("/api/follow/source", {
                "action": "add",
                "url": "https://rule34.xxx/index.php?page=post&s=list&tags=ceeeeekc",
                "author": "cekc", "aliases": ["Ceeeeekc", "cekc"],
            })
        self.assertEqual(added["author_aliases_learned"], [
            {"canonical": "cekc", "alias": "Ceeeeekc", "source": "profile:f95zone"}])
        payload = self._get()
        self.assertEqual(payload["sources"][0]["author_key"], "name:cekc")
        self.assertEqual([alias["name"] for alias in payload["author_aliases"][0]["aliases"]],
                         ["Ceeeeekc"])
        self.assertEqual(payload["alias_suggestions"], [])
        with self.assertRaises(ValueError):
            self._post("/api/follow/source", {"action": "add", "aliases": "Ceeeeekc",
                                              "url": "https://rule34video.com/models/x/"})

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
            "label": "lazyprocrast", "author": "", "aliases": [], "semantics": "work",
            "evidence": "链接直接指明", "known": False,
        }])

    def test_resolve_progress_counts_sources_instead_of_lines(self):
        """一行的背后是十几个来源在查：进度按来源数走，环才会逐个涨过去。"""
        ticks = []

        def fake_discover(line, **kwargs):
            note = kwargs["on_progress"]
            note("kemono", 0, 8)
            note("f95zone", 7, 8)
            return Discovery(line, external_searches=())

        with mock.patch.object(web_follow, "discover", side_effect=fake_discover):
            web_follow.w_follow_resolve(self.contract, {
                "lines": ["suzutaro3d", "https://kemono.cr/fanbox/user/30917150"],
            }, progress=lambda **fields: ticks.append(fields))
        self.assertEqual([tick["checked"] for tick in ticks], [0, 7, 9])
        self.assertTrue(all(tick["total"] == 9 for tick in ticks))
        self.assertIn("Kemono", ticks[0]["message"])
        self.assertIn("F95zone", ticks[1]["message"])

    def test_a_line_that_fails_still_advances_the_ring_by_its_own_sources(self):
        """来源是开查前报一次，报的是 `position`，所以查完最后一个来源分子停在 total-1；
        查失败的行一个来源都不报。两样都不补，环就走不满，后面的行还一路偏低。
        """
        ticks = []

        def fake_discover(line, **kwargs):
            if line == "suzutaro3d":
                raise FollowSourceError("索引下不来")
            kwargs["on_progress"]("kemono", 0, 8)
            return Discovery(line, external_searches=())

        with mock.patch.object(web_follow, "discover", side_effect=fake_discover):
            result = web_follow.w_follow_resolve(self.contract, {
                "lines": ["suzutaro3d", "lazyprocrastinator"],
            }, progress=lambda **fields: ticks.append(fields))
        self.assertEqual(result["results"][0]["kind"], "error")
        # 两行各 8 个来源：第二行开查时分子已经是第一行的 8，收尾走满 16。
        self.assertEqual([tick["checked"] for tick in ticks], [8, 16])
        self.assertTrue(all(tick["total"] == 16 for tick in ticks))

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

        这里回 `checked: null` 的话，调用方分不清「查过了什么都没有」和「根本
        没查」，界面上就是登记完一片空白。所以明说：已登记，稍后再查。
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

    def test_a_simpcity_thread_registers_and_the_first_check_asks_for_the_cookie(self):
        # 没有 cookie 时来源照样登记，首次检查报「未授权」而不是把整次登记回滚。
        result = self._post("/api/follow/source",
                            {"action": "add", "url": "https://simpcity.cr/threads/x.4242/"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["checked"]["ok"])
        self.assertEqual(result["checked"]["status"], "unauthorized")
        self.assertIn("cookie", result["checked"]["error"])
        source = self._get()["sources"][0]
        self.assertEqual((source["provider"], source["ref"]), ("simpcity", "4242"))

    def test_simpcity_images_are_playable_only_when_the_media_proxy_can_fetch_them(self):
        # 帖子里的图不论挂在站方图床还是哪家第三方图站，都经 /follow-stream 就地看；
        # 「可播」必须与代理同一口径，说可播再让代理拒收就会渲染成一张打不开的图。
        self._seed(candidates=(
            FollowCandidate(provider="simpcity", external_id="51632037", title="Solazola / baby_sue",
                            url="https://simpcity.cr/threads/17401/post-51632037",
                            media_url="https://simp6.cuckcapital.cr/images4/b73b.png",
                            thumb_url="https://simp6.cuckcapital.cr/images4/b73b.png",
                            extra={"images": ["https://simp6.cuckcapital.cr/images4/b73b.png"]}),
            FollowCandidate(provider="simpcity", external_id="51632038", title="Solazola / baby_sue",
                            url="https://simpcity.cr/threads/17401/post-51632038",
                            media_url="https://jpg5.su/img/abc.jpg",
                            thumb_url="https://jpg5.su/img/abc.md.jpg",
                            extra={"images": ["https://jpg5.su/img/abc.jpg"]}),
            FollowCandidate(provider="simpcity", external_id="51632039", title="Solazola / baby_sue",
                            url="https://simpcity.cr/threads/17401/post-51632039",
                            media_url="https://gofile.io/d/rFyusPzL",
                            thumb_url="https://simp6.cuckcapital.cr/images4/c0de.png",
                            extra={"links": ["https://gofile.io/d/rFyusPzL",
                                             "https://pixeldrain.com/u/zF3PqTJF"]}),
        ), provider="simpcity", ref="17401", semantics="release", label="Solazola / baby_sue")
        # 每个带资源的楼层各自成组，线程标题只是容器名。
        items = {group["primary"]["external_id"]: group["primary"] for group in self._get()["groups"]}
        self.assertEqual(sorted(items), ["51632037", "51632038", "51632039"])
        self.assertTrue(items["51632037"]["playable"])
        self.assertEqual(items["51632037"]["media_kind"], "image")
        self.assertTrue(items["51632038"]["playable"])
        self.assertEqual(items["51632038"]["media_kind"], "image")
        self.assertEqual(items["51632038"]["thumb_url"], "https://jpg5.su/img/abc.md.jpg")
        # 只有网盘链接的楼层不是图：不可播，链接显示成按钮。
        self.assertFalse(items["51632039"]["playable"])
        self.assertEqual(items["51632039"]["resource_urls"],
                         ["https://gofile.io/d/rFyusPzL", "https://pixeldrain.com/u/zF3PqTJF"])

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


class FollowSuggestTests(FollowContractTests):
    """添加框敲字时的建议。每组各自独立成败，任何一组缺席都不影响别的组。"""

    TAGS = json.dumps([{"label": "lewdgatta (380)", "value": "lewdgatta"},
                       {"label": "lewdgazer (237)", "value": "lewdgazer"}]).encode()
    #: 1 是 artist、4 是 character。dapi 的 tag 接口只回 XML。
    TAG_TYPES = {
        "lewdgatta": b'<tags type="array"><tag type="1" count="380" name="lewdgatta"/></tags>',
        "lewdgazer": b'<tags type="array"><tag type="4" count="237" name="lewdgazer"/></tags>',
    }

    def setUp(self):
        super().setUp()
        # 分类缓存是模块级的，留到下一个用例里就会让它凭空少打几次请求。
        follow_discovery._TAG_TYPES.clear()
        self.addCleanup(follow_discovery._TAG_TYPES.clear)

    def _tag_transport(self, body=None):
        def call(_request, _timeout, _max_bytes):
            return HttpResponse(200, {"content-type": "text/html"},
                                self.TAGS if body is None else body)
        return call

    def _typed_transport(self):
        def call(request, _timeout, _max_bytes):
            if "autocomplete.php" in request.url:
                return HttpResponse(200, {}, self.TAGS)
            name = urllib.parse.parse_qs(
                urllib.parse.urlsplit(request.url).query)["name"][0]
            return HttpResponse(200, {}, self.TAG_TYPES[name])
        return call

    def _write_credential(self):
        path = self.contract.follow_secrets_root / "follow" / "rule34xxx.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"user_id": "1", "api_key": "k"}),
                        encoding="utf-8")

    def _write_creator_index(self, provider, rows):
        path = self.contract.follow_state_root / "follow" / f"creators-{provider}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows), encoding="utf-8")

    def _suggest(self, query, **kwargs):
        return web_follow.q_follow_suggest(self.contract, query, **kwargs)

    def test_half_a_name_suggests_the_creator_behind_it(self):
        """打 `lewdga` 要出 `lewdgazer`：这是建议存在的全部理由。

        名字从没关注过也要出得来——本机见过的那一组只认识已经关注的人。
        """
        self._write_creator_index("kemono", [
            {"id": "1", "name": "lewdgazer", "service": "fanbox"}])
        payload = self._suggest("lewdga", transport=self._tag_transport())
        self.assertEqual(payload["q"], "lewdga")
        self.assertEqual([(group["kind"], [item["value"] for item in group["items"]])
                          for group in payload["groups"]],
                         [("archive", ["lewdgazer"]),
                          ("tag", ["lewdgatta", "lewdgazer"])])

    def test_the_group_order_is_decided_here_not_in_the_page(self):
        # 两侧各排一次的话，改了一侧就会有一组显示在它不该在的位置上。
        self._seed(label="lewdgazer")
        self._write_creator_index("kemono", [
            {"id": "1", "name": "lewdgamesdev", "service": "fanbox"}])
        self._write_credential()
        payload = self._suggest("lewdga", transport=self._typed_transport())
        self.assertEqual([group["kind"] for group in payload["groups"]],
                         ["followed", "archive", "tag_artist", "tag"])
        self.assertEqual([group["label"] for group in payload["groups"]],
                         ["已关注", "归档站的创作者",
                          "Rule34.xxx 的创作者", "Rule34.xxx 标签"])

    def test_the_site_authors_are_split_out_from_the_plain_tags(self):
        """rule34.xxx 上作者本来就是一个标签，差别只在站方给它的分类。

        `lewdgatta` 是 artist、`lewdgazer` 在这批数据里是 character，两条挨着躺在
        同一组时没人分得出哪个是人。留在标签组的那条要照实写出它是什么。
        """
        self._write_credential()
        groups = {group["kind"]: group["items"]
                  for group in self._suggest(
                      "lewdga", transport=self._typed_transport())["groups"]}
        self.assertEqual([row["value"] for row in groups["tag_artist"]], ["lewdgatta"])
        self.assertEqual([(row["value"], row["matched"]) for row in groups["tag"]],
                         [("lewdgazer", "角色")])
        # 作者组里逐条再标一次「作者」是同一个词并排两次，组名已经说过了。
        self.assertEqual(groups["tag_artist"][0]["matched"], "")

    def test_without_a_credential_nobody_is_called_an_author(self):
        """分类接口要凭据。问不出来时全落在标签组里，照实说不知道谁是作者。

        按名字猜会错：实测 `lewdchuu_(artist)` 名字里带 `artist` 只是巧合，
        `lewdtuber` 是 metadata。
        """
        payload = self._suggest("lewdga", transport=self._tag_transport())
        groups = {group["kind"]: group["items"] for group in payload["groups"]}
        self.assertNotIn("tag_artist", groups)
        self.assertEqual([(row["value"], row["matched"]) for row in groups["tag"]],
                         [("lewdgatta", ""), ("lewdgazer", "")])

    def test_someone_already_followed_is_not_offered_twice(self):
        self._seed(label="lewdgazer")
        self._write_creator_index("kemono", [
            {"id": "1", "name": "LewdGazer", "service": "fanbox"}])
        groups = {group["kind"]: [item["value"] for item in group["items"]]
                  for group in self._suggest(
                      "lewdga", transport=self._tag_transport(b"[]"))["groups"]}
        self.assertEqual(groups, {"followed": ["lewdgazer"]})

    def test_the_tag_group_carries_the_post_count(self):
        # 标签下有多少件作品是判断「是不是他」的依据，照实给。
        items = {group["kind"]: group["items"] for group in self._suggest(
            "lewdga", transport=self._tag_transport())["groups"]}["tag"]
        self.assertEqual([(row["value"], row["n"]) for row in items],
                         [("lewdgatta", 380), ("lewdgazer", 237)])

    def test_a_pasted_link_asks_nobody(self):
        """地址不进建议这条路：那时该做的是解析链接，不是猜名字。

        判据在 `follow_discovery.suggest_term` 一处，这里只确认没有绕过它。
        """
        calls = []

        def call(request, _timeout, _max_bytes):
            calls.append(request.url)
            return HttpResponse(200, {}, self.TAGS)

        for query in ("https://kemono.cr/fanbox/user/1", "l", ""):
            payload = self._suggest(query, transport=call)
            self.assertEqual(payload["groups"], [], query)
        self.assertEqual(calls, [])

    def test_a_dead_site_still_leaves_the_local_groups(self):
        # 站点挂了只少它那一组，而且是立刻少：联想不等连接器的退避。
        def call(_request, _timeout, _max_bytes):
            raise OSError("connection reset")

        self._seed(label="lewdgazer")
        with no_real_backoff():
            payload = self._suggest("lewdga", transport=call)
        self.assertEqual([group["kind"] for group in payload["groups"]], ["followed"])

    def test_the_endpoint_is_a_read_and_needs_no_credential(self):
        """建议不写任何东西，也不为它下载整站清单。

        rule34.xxx 那一组走的是站方的公开补全；凭据仍然是**抓取**那条订阅的前提。
        """
        self._seed(label="lewdgazer")
        with mock.patch.object(web_follow, "tag_suggestions", return_value=()):
            payload = self._get("/api/follow/suggest", q="lewdga")
        self.assertEqual([item["value"] for item in payload["groups"][0]["items"]],
                         ["lewdgazer"])
        self.assertEqual(self._get("/api/follow/suggest", q="")["groups"], [])


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
        sources = [web / "index.html"]
        sources.extend(sorted((web / "css").glob("*.css")))
        sources.append(web / "app.js")
        sources.extend(sorted((web / "js").glob("*.js")))
        cls.page = chr(10).join(
            path.read_text(encoding="utf-8") for path in sources)

    def assertPageContains(self, needle, message=""):
        if needle not in self.page:
            self.fail(f"Web 表面缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def assertBoardContains(self, needle):
        # Board 层的覆盖单独一张表，不在上面那份页面里；按 test_web_ui 的写法直接读它。
        board = (ROOT / "web" / "board.css").read_text(encoding="utf-8")
        if needle not in board:
            self.fail(f"board.css 缺少：{needle!r}")

    def read_react(self, relative):
        """React 子树里的一份源码（ADR-0031）。关注管理页的正文不在 `web/` 里。"""
        return (ROOT / "frontend" / "src" / "react" / relative).read_text(encoding="utf-8")

    def read_front(self, relative):
        """`frontend/src` 下的一份源码：骨架、island 注册表这类不在 `react/` 子树里的。"""
        return (ROOT / "frontend" / "src" / relative).read_text(encoding="utf-8")

    def assertReactContains(self, relative, needle, message=""):
        source = self.read_react(relative)
        if needle not in source:
            self.fail(f"{relative} 缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def test_a_failed_check_names_the_author_not_just_the_source_id(self):
        """检查失败要说清是谁的哪一条，光给一个来源 id 等于让人自己回去翻。

        创作者名不一定在哪个字段上：官方来源给 `author`，归档来源只有 `label`，
        再不济还有 `ref`。三个依次取，取到哪个说哪个。
        """
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("{`${row.provider_label || row.provider || ''} "
                      "${row.author || row.label || row.ref || ''}：${row.error || '未说明原因'}`}",
                      source_list)
        # 创作者卡上那一枚检查的是这位创作者还开着的那几条，暂停的不去打扰。
        self.assertIn("const enabled = group.filter((source) => source.enabled).map((source) => source.id);",
                      source_list)
        self.assertIn("aria-label={`检查 ${name} 的全部来源`}", source_list)

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
        # 管理页的工具条不再挂一枚回「看」那一屏的按钮：左栏那条常驻入口一直在，
        # 同一个去处在一屏里摆两个只是把工具条上真正的动作挤窄。检查完那一下的
        # Toast 仍然给「去看更新」，因为那时人刚做完一件事、下一步确实在另一屏。
        self.assertPageLacks("data-follow-view")
        self.assertPageContains("action:{label:'去看更新',run:()=>openFollow()}")

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

    def test_sources_are_added_by_pasting_not_by_a_command(self):
        """加一条关注就是把地址粘进去，不用记命令；移除也在同一张清单上。"""
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const FOLLOW_SOURCE_URL = '/api/follow/source';", data)
        self.assertIn("export const addSource = (candidate: ResolveCandidate) =>", data)
        self.assertIn("export const removeSource = (id: number) =>", data)
        self.assertReactContains("follow-manage/add-source.tsx",
                                 '<Input aria-label="来源链接、名字或 id" placeholder={PLACEHOLDER} value={line}')
        self.assertReactContains("follow-manage/source-list.tsx", "aria-label={`移除 ${source.label}`}")

    def test_the_lookup_takes_one_line_and_never_grows_into_a_batch_box(self):
        """查找字段是一行，不是可以粘一叠地址的多行框。

        多行批量本身不成立：一个作者就要几十秒，一次粘五行等于把这个等待乘五，
        中途还看不出走到哪一行。所以字段是单行 `Input`，回车和旁边那颗「查找」
        走同一个入口。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn('<Input aria-label="来源链接、名字或 id"', add)
        self.assertNotIn("textarea", add)
        self.assertIn("if (event.key !== 'Enter') return;", add)
        self.assertIn("onClick={() => search(line)}>查找</Button>", add)
        # 一趟查找在跑的时候不再起第二趟，按钮和输入框都进忙态。
        self.assertIn("if (!query || running || resolve.isPending) return;", add)
        self.assertIn("{...busyProps(running || resolve.isPending)}", add)

    def test_reader_management_is_locked_and_points_to_the_writer(self):
        """本机只能浏览时，管理页说清楚并给出写入端的去处。"""
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        self.assertIn('<Note tone="warning" title="本机只能浏览"', page)
        self.assertIn("前往写入端管理关注", page)
        self.assertIn("{readOnlyMessage}", page)
        # 只读这一位由壳从 runtime 读出来交进 island，React 不自己再判一次。
        self.assertPageContains("readOnly:!!runtime?.ledger_read_only,")
        self.assertPageContains("surfaceApi(surface,'/healthz')")
        # 写操作一律停用，不是点下去才报错。
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("disabled={readOnly}", source_list)

    def test_failed_source_adds_stay_visible_instead_of_being_erased_by_reload(self):
        """一批候选里有几条登记失败时，失败原因留在页面上。

        逐条登记，失败的收进清单接着登记下一条；成功那几条会让清单重取，可重取
        不该把刚才那几行失败一起冲掉——那正是人还没来得及读的东西。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("failures.push(`${item.candidate.label}：${errorMessage(cause)}`);", add)
        self.assertIn("if (result.failures.length) { setProblem(result.failures.join('；')); return }",
                      add)
        # 重取排在报错之前，且报错这一支直接 return，不会再往下清空。
        register = add[add.index("const register = useMutation({"):]
        register = register[:register.index("\n  });")]
        self.assertLess(register.index("void reloadFollowManage();"),
                        register.index("if (result.failures.length)"))
        self.assertIn('<Note tone="error" title="这一次没有完成">{problem}</Note>', add)

    def test_a_bare_name_or_id_is_looked_up_across_sources(self):
        """光给一个名字或 id 也能查，查完列候选、勾选之后才真的登记。"""
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const FOLLOW_RESOLVE_URL = '/api/follow/resolve';", data)
        self.assertIn("export const startResolve = (lines: string[]) =>", data)
        add = self.read_react("follow-manage/add-source.tsx")
        # 候选默认勾上，但登记是单独一颗键；查完不自动写。
        self.assertIn("onClick={() => register.mutate(picked)}", add)
        self.assertIn("isSelected={!candidate.known && !unpicked.has(key)}", add)

    def test_lookup_results_stay_inside_the_add_section(self):
        """查找结果留在「添加关注」这一栏里，不另开一屏。

        三栏是三件事，结果跑到别的栏去就得来回切；标题层级也只有一档，结果块不
        自己再起一套字号。
        """
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        panel = page[page.index('<TabPanel id="add"'):page.index('<TabPanel id="source"')]
        self.assertIn("<AddSource data={data}", panel)
        add = self.read_react("follow-manage/add-source.tsx")
        heading = re.search(r'<h3 className="([^"]*)">添加关注</h3>', add)
        self.assertIsNotNone(heading, "「添加关注」是这一栏的抬头")
        # 标题层级只有一档：抬头那一档字阶在这一栏里只出现这一次。
        self.assertEqual(add.count(heading.group(1)), 1, "查找结果不另起一套标题字号")
        self.assertEqual(add.count("<h3"), 1, "查找结果不另起一个标题")

    def test_f95_misses_offer_a_clickable_google_query(self):
        add = self.read_react("follow-manage/add-source.tsx")
        block = add[add.index("{(row.external_searches || []).map((search) => ("):]
        block = block[:block.index("{failures.length ? (")]
        self.assertIn('<small className="text-caption-1-regular text-text-secondary">{search.evidence}</small>',
                      block)
        self.assertIn("<ExternalLink href={search.url}>{`${search.label}：${search.query}`}</ExternalLink>", block)
        # 说明先行、不在链接里；链接在其后，带外链标。
        self.assertLess(block.index("{search.evidence}"), block.index("<ExternalLink"))
        self.assertReactContains("settings/section.tsx", "trailingIcon={RiExternalLinkLine}")

    def test_follow_author_groups_are_one_card_per_author_and_link_to_the_original_page(self):
        """一位创作者一张卡，卡里是他在各个站上的来源，来源名连回原页面。"""
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn('<section aria-label={`${name} 的关注来源`}', source_list)
        self.assertIn("<AuthorCard key={key} group={group} name={authorName(group, aliases)}", source_list)
        # 卡片里那一叠来源行是同一位创作者的，展开与否由卡自己记。
        self.assertIn("<div id={panel} hidden={!open} data-source-divider>", source_list)
        self.assertIn("const panel = `follow-author-${group[0]!.id}`;", source_list)
        self.assertReactContains(
            "follow-manage/source-view.tsx",
            '<a href={source.url} target="_blank" rel="noreferrer noopener" title="打开原来源"')

    def test_source_actions_are_icon_only_and_stay_on_one_row(self):
        """行尾那两颗动作只有字形，名字交给无障碍名称，一行摆得下。

        写上「检查」「移除」两个词的话，窄一点的卡片里这一行就断成两行，而断开的
        正是每条来源都要看的状态和上次检查时间。
        """
        source_list = self.read_react("follow-manage/source-list.tsx")
        row = source_list[source_list.index("function SourceRow("):
                          source_list.index("function AuthorCard(")]
        self.assertIn("iconOnly leadingIcon={RiRefreshLine}", row)
        self.assertIn("aria-label={`检查 ${source.label} 的更新`}", row)
        self.assertIn("iconOnly leadingIcon={RiDeleteBinLine}", row)
        self.assertIn("aria-label={`移除 ${source.label}`}", row)
        self.assertNotIn(">检查<", row)
        self.assertNotIn(">移除<", row)
        # 这两颗自己不换行，行里要挤也是挤前面那几段文字。
        self.assertIn('<span className="flex shrink-0 items-center gap-1">', row)

    def test_a_row_is_picked_by_its_own_checkbox_and_written_one_row_at_a_time(self):
        """每行第一格是勾选框，改这一条的状态只换这一条的那一份数据。

        启用与暂停是对选中的那一批说的，写回按单行交换：整张清单重取一遍的话，
        正在看的那一屏会整个跳一下，而变的只有一个字。
        """
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("<Checkbox isSelected={selected} onChange={onToggle} "
                      "aria-label={`选择 ${source.label}`} />", source_list)
        self.assertIn("else for (const id of result.done) patchSource(id, "
                      "{ enabled: result.action === 'enabled' });", source_list)
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export function patchSource(id: number, patch: Partial<FollowSource>): void {", data)
        self.assertIn("queryClient.setQueryData<FollowData>(FOLLOW_MANAGE_KEY, (data) => (data ? {", data)

    def test_official_channel_icons_and_alias_manager_are_visible(self):
        """官方站有自己的圆标；作者别名有一块自己的管理区。"""
        data = self.read_react("follow-manage/follow-manage.ts")
        icons = data.split("export const SOURCE_ICON_PROVIDERS = new Set([", 1)[1].split("]);", 1)[0]
        for provider in ("fanbox", "patreon", "subscribestar"):
            self.assertIn(f"'{provider}'", icons)
        self.assertIn("export const FOLLOW_ALIAS_URL = '/api/follow/author-alias';", data)
        self.assertReactContains("follow-manage/follow-manage-page.tsx",
                                 "<AliasManager groups={data.author_aliases || []}")

    def test_the_author_head_shows_its_sites_as_favicons(self):
        """作者卡这一行只出图标：站名在下面每条来源自己那一行上都写着。

        写进标题栏就是同一个词并排两次，窄卡片里它先把图标挤到贴脸，再把作者名压没。
        站名落在 title 和读屏读的那一段里，真要确认的人读得到。
        """
        source_list = self.read_react("follow-manage/source-list.tsx")
        head = source_list[source_list.index("function AuthorCard("):
                           source_list.index("export function SourceList(")]
        self.assertIn("{group.map((source) => <SourceIcon key={source.id} provider={source.provider} />)}",
                      head)
        self.assertIn('<span className="flex shrink-0 items-center gap-1" title={providers}>', head)
        # 只读屏的那一段走 `VisuallyHidden`：它把样式写在元素上，不生成一个和旧样式表
        # 同名的工具类（`frontend/test/legacy-class-names.test.ts` 盯着这条）。
        self.assertIn("<VisuallyHidden>{`来源：${providers}`}</VisuallyHidden>", head)

    def test_already_followed_candidates_are_shown_but_not_selectable(self):
        """已经关注的候选照样列出来，但勾不动——不然人以为没查到。"""
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("isDisabled={candidate.known}", add)
        self.assertIn("{candidate.known ? '已经关注' : candidate.evidence}", add)

    def test_the_first_name_lookup_warns_about_the_index_download(self):
        """按名字查第一次要先下载创作者索引，这一等得说清楚。"""
        self.assertReactContains("follow-manage/add-source.tsx",
                                 "首次按名字查要下载创作者索引，可能几十秒")

    def test_the_input_and_its_button_are_the_same_height(self):
        # 输入框和旁边的来源筛选按钮齐平；单行以后没有 min-height 与 resize。
        # 几何住在共用的 .geist-search 里，关注页不再复制一份自己的输入框样式。
        page = self.page
        self.assertEqual(page.count('.geist-search input[type="search"]{'), 1,
                         "旧规则留在后面会覆盖新输入框样式")
        self.assertEqual(page.count('.faddform input[type="search"]{'), 0,
                         "关注页私有的输入框几何已经上提到 .geist-search")
        rule = page[page.index('.geist-search input[type="search"]{'):]
        rule = rule[:rule.index("}")]
        self.assertIn("height:38px", rule)
        self.assertIn("padding:0 12px 0 38px", rule)
        self.assertIn("line-height:20px", rule)
        self.assertNotIn("resize:", rule)
        button = page[page.index("\n.fbtn{"):]
        self.assertIn("height:32px", button[:button.index("}")])
        # 添加表单没有自己的按钮高度规则：输入框几何由 .geist-search 统一给。
        self.assertNotIn(".faddform .fbtn{", page)

    def test_the_source_filter_is_a_labelled_popover_beside_the_lookup_field(self):
        """来源筛选是查找行右边一颗带名字的按钮，点开是一块弹层。

        按钮上写着当前筛到哪几个站，不必点开才知道；弹层自己是一块 `Dialog`，
        有名字、能用键盘关掉，弹层位置由 BoardUI 的 `Popover` 定。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn('aria-haspopup="dialog" aria-expanded={open} aria-label={label}', add)
        self.assertIn("leadingIcon={RiFilter3Line}", add)
        self.assertIn('<Dialog aria-label="来源筛选"', add)
        self.assertIn('placement="bottom end" offset={4} className={MENU_POPOVER_SURFACE}', add)
        # 按钮上那句话说的是筛完剩几个站，全留着就直说「全部来源」。
        self.assertIn("'全部来源'", add)

    def test_source_filter_menu_offers_select_all_and_select_none(self):
        """弹层顶上给「全选」和「全不选」，它们是对整张清单说的，所以排在逐站那几行上面。

        真相只有 `hidden` 一份：两颗键改的也是它，不去逐个翻勾选框的 DOM 状态。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        filter_block = add[add.index("function SourceFilter("):add.index("function PickRow(")]
        self.assertIn("onClick={() => onHidden(new Set())}>全选</Button>", filter_block)
        self.assertIn("onClick={() => onHidden(new Set(rows.map((row) => row.provider_label)))}"
                      ">全不选</Button>", filter_block)
        self.assertLess(filter_block.index(">全选</Button>"),
                        filter_block.index("<Checkbox isSelected={!hidden.has(row.provider_label)}"))

    def test_follow_filter_rows_are_multi_select_without_bulk_keys(self):
        """关注页的作者、来源、标签三行都是多选，行首不配「全选／全不选」：这一页是浏览用的。

        选中状态只有三个 Set 一份真相，URL 里按逗号拼；服务端同样按逗号拆。
        """
        self.assertIn("let followAuthors=new Set(),followProviders=new Set(),followTags=new Set()",
                      self.page)
        self.assertNotIn("followAuthor=", self.page.replace("followAuthors=", ""))
        self.assertNotIn("followProvider=", self.page.replace("followProviders=", ""))
        render = self.page[self.page.index("function renderFollow("):
                           self.page.index("function followBackfillState(")]
        self.assertIn('aria-pressed="${followAuthors.has(key)}"', render)
        self.assertIn('aria-pressed="${followProviders.has(key)}"', render)
        self.assertIn('selected:followTags.has(key)', render)
        self.assertNotIn("followBulkButtons", self.page)
        self.assertNotIn("data-bulk-all", self.page)
        self.assertNotIn(".followauthors .fbulk{", self.page)
        self.assertIn("params.set('author',[...followAuthors].join(','))", self.page)
        self.assertIn("params.set('provider',[...followProviders].join(','))", self.page)

    def test_the_manage_page_is_ordered_by_what_you_do_first(self):
        """三栏按做事的先后排：关注列表在最前，其次添加关注，最后才是来源和凭证。

        凭据是出问题时才去配的东西，摆在第一栏就等于每次进来都先看一眼跟这次无关的
        表单。栏的顺序同时也是地址栏里 `tab` 的取值顺序，壳那边照着同一份。
        """
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        self.assertIn("const TABS = [['list', '关注列表'], ['add', '添加关注'], "
                      "['source', '来源和凭证']] as const;", page)
        self.assertPageContains("const FOLLOW_MANAGE_TABS=['list','add','source'];")

    def test_counts_are_a_footnote_not_their_own_section(self):
        """四段计数跟在列表末尾，不自己占一整块。

        单独占一张通栏卡片的话，宽屏上就是一条空长条；而这四个数只在还有未看的时候
        才有人读，没有未看时它整块不出现。
        """
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("{counts.new ? (", source_list)
        self.assertIn("{`未看 ${counts.new} · 已看 ${counts.seen || 0} · 已保存 "
                      "${counts.saved || 0} · 已忽略 ${counts.ignored || 0}`}", source_list)
        # 页顶那四格读数是另一件事：它说的是整个关注面的规模，不是某一次筛选的结果。
        self.assertReactContains("follow-manage/follow-manage-page.tsx",
                                 '<Reading term="关注创作者" figure={groups.length} unit="位" />')

    def test_the_page_is_one_narrow_column_with_credentials_inline(self):
        """侧栏在哪个宽度上都不对：宽屏把凭据推出视线，窄屏又整个塌到最底下。

        三块内容本来就有先后，那就按顺序排成一列，宽度跟数据管理页同样收窄，别让一行
        横跨整个显示器。骨架照这个宽度画，换页时不会先宽一下再收回去。
        """
        page = self.page
        rule = page[page.index(".followmanage{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("width:min(812px,100%)", rule)
        self.assertIn("margin-left:auto;margin-right:auto", rule)
        self.assertNotIn("grid-template-columns", rule)
        self.assertNotIn("faside", page)
        # 标题与说明跟内容列同宽，否则标题悬空在更宽的位置上。
        self.assertPageContains(
            ".follow-manage-layout .managetitle,.follow-manage-layout .pagelede{width:min(812px,100%)")
        self.assertPageContains(
            "document.body.classList.toggle('follow-manage-layout',"
            "decodeURIComponent(location.pathname)==='/follow-manage')")
        # React 那一侧同宽：`Page` 是这一族页面共用的那一层。
        self.assertReactContains("follow-manage/follow-manage-page.tsx", "<Page>")
        # 凭据在「来源和凭证」那一栏里，每个站一行。
        self.assertReactContains(
            "follow-manage/credentials.tsx",
            "<CredentialSection key={row.provider} row={row} readOnly={readOnly} toast={toast} />")

    def test_sections_have_a_frame_but_their_rows_do_not(self):
        """反模式是卡片**套**卡片，不是「不要任何容器」。

        把两者混为一谈就会做成没有可读性的裸列表——而同一份文档明确警告过不要
        因为躲开那些默认套路就做出一个无设计的模板。所以：分区有框，框里的行
        只用分隔线。
        """
        page = self.page
        section = page[page.index(".fsec{"):]
        section = section[:section.index("}")]
        self.assertIn("border:1px solid", section)
        self.assertIn("border-radius", section)
        self.assertIn("background:var(--ground)", section)

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
        """缺凭据是待办，配好了是完成态，接不进来是坏掉了。同色就等于没说。"""
        creds = self.read_react("follow-manage/credentials.tsx")
        chip = creds[creds.index("function StateChip("):creds.index("function CredentialForm(")]
        self.assertIn('if (done) return <Chip variant="caption" color="lime">已配置</Chip>;', chip)
        self.assertIn("const color = row.requirement === 'required' ? 'yellow'", chip)
        self.assertIn(": row.requirement === 'blocked' ? 'rose' : 'neutral';", chip)
        colours = set(re.findall(r"['\"](lime|yellow|rose|neutral)['\"]", chip))
        self.assertEqual(len(colours), 4, "四种处境要有四副长相")

    def test_suggestions_come_from_the_real_library_and_are_clickable(self):
        """「猜你喜欢」取账本里真实存在的创作者，点一下直接拿去查。

        推荐不能退化成 placeholder：占位文字点不了。占位文字只负责说清该输入什么
        格式（Vercel Forms：以省略号收尾、给出示例样式），不许塞进具体创作者名。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("const guesses = data.suggestions || [];", add)
        # 点一下就是拿这个名字去查，不是往输入框里填半句话让人再点一次。
        self.assertIn("onClick={() => search(guess.name)}>{guess.name}</Button>", add)
        self.assertIn("title={`浏览历史里出现 ${guess.visits} 次", add)
        # 不能退回本地文件的创作者：那是「他有谁的文件」，不是「他喜欢谁」。
        self.assertNotIn("facets", add)
        # 占位文字只说该输入什么格式，不塞具体创作者名。
        self.assertIn("const PLACEHOLDER = '粘贴来源链接，或输入创作者名、id…';", add)
        self.assertEqual(add.count("placeholder={"), 1)
        self.assertEqual(add.count("placeholder='"), 0, "占位文字只有具名常量那一处")

    def test_every_credential_state_sits_in_the_same_column(self):
        """能填的那几行有折叠体、不能填的没有，但抬头是同一段。

        抬头一旦写成两份，两个分支就会各自漂：一边状态贴着名字，一边靠右，同一列两种
        对齐。所以 `head` 只算一次，两个分支都摆同一个它。"""
        creds = self.read_react("follow-manage/credentials.tsx")
        section = creds[creds.index("function CredentialSection("):creds.index("export function Credentials(")]
        self.assertIn("const head = (", section)
        self.assertEqual(section.count("{head}"), 2, "两个分支要摆同一段抬头")
        self.assertEqual(section.count("<StateChip row={row} />"), 1, "状态徽章只该有一处")
        # 抬头自己是 flex 行：名字可缩、图标和徽章不缩，名字再长也不把状态挤出这一列。
        self.assertIn('<span className="flex min-w-0 items-center gap-2">', section)

    def test_the_add_box_carries_no_standing_how_to_prose(self):
        # 空态保留状态和结果去向；操作说明常驻就是噪音。
        add = self.read_react("follow-manage/add-source.tsx")
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertNotIn("要一次加多个就每行一条", add)
        self.assertNotIn("把链接或名字粘进上面的输入框", add)
        # 钉的是这段空态说了什么，不是它写成什么样：外壳与图标属于控件层，改那里不该红。
        self.assertIn('title="还没有关注来源"', sources)
        self.assertIn("关注来源及其检查状态会显示在这里。</EmptyState>", sources)

    def test_the_panel_cites_the_registered_report_design_source(self):
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        self.assertIn("docs/reference-sources.json", page)
        self.assertIn("vercel-report-design", page)
        self.assertNotIn("e3d624baaf29dc1fc645aff3e38f03e564d2d6b1", page)

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
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("required: '需要', optional: '可选', none: '不需要', blocked: '接不进来',", data)
        creds = self.read_react("follow-manage/credentials.tsx")
        # 需要什么：缺的字段名直接列出来，不让人点开才知道。
        self.assertIn('<Chip variant="caption" color="rose">{`缺 ${row.missing.join(\'、\')}`}</Chip>', creds)
        # 去哪儿拿：说明加一条跳到那个站自己的页面的链接。
        self.assertIn("{row.where ? <> <ExternalLink href={row.where}>去取</ExternalLink></> : null}", creds)
        self.assertIn("{row.howto ? <Help>{row.howto}</Help> : null}", creds)

    def test_the_page_says_where_the_credential_actually_lands(self):
        creds = self.read_react("follow-manage/credentials.tsx")
        # 从 Mac 浏览 Windows 实例时，凭据落在 Windows 上——不能写成「本机」。
        self.assertIn("存成运行 Peach 那台电脑上的一个文件。", creds)
        # Windows 那句要把后果说出来，不能只报一个「不收紧权限」的动作。
        self.assertIn("在 Windows 上它不额外加锁，能登录那台电脑的人都能打开。", creds)
        self.assertIn('<p className="font-mono text-caption-1-regular break-all text-text-tertiary">{row.path}</p>',
                      creds)
        self.assertIn('{row.world_readable ? <Note tone="error" title="凭据文件权限过宽">', creds)

    def test_credential_information_card_stays_inside_the_viewport(self):
        """存放位置是一段常驻说明，排在凭据列表末尾，不是一枚要点开的浮层。

        浮层要自己算位置才不越界，而这段字每次都该被读到——它讲的是凭据会落在哪台机器、
        权限有多宽。排进正文流就没有越界这回事了。"""
        creds = self.read_react("follow-manage/credentials.tsx")
        tail = creds[creds.index("export function Credentials("):]
        self.assertIn("<b className=\"text-body-medium text-text-primary\">{STORAGE_TITLE}</b>", tail)
        self.assertIn("{`凭据文件在 ${data.root}`}", tail)
        # 排在凭据列表末尾：先是逐站那一叠，这段说明跟在它后面，同在正文流里。
        self.assertLess(tail.index("<CredentialSection"), tail.index("{STORAGE_TITLE}"))
        for machinery in ("popover", "role=\"dialog\"", "innerWidth"):
            self.assertNotIn(machinery, creds, "这段说明不该有浮层定位逻辑")

    def test_expanding_prose_animates_a_measured_height(self):
        """展开是量出来的高度过渡，不是一帧之间蹦出来。

        `height:auto` 不可过渡，所以要先量再写值；收起那半程也要把正文设成 `inert`，
        否则键盘还能 Tab 进一段看不见的表单。"""
        self.assertPageContains(".fcollapse{overflow:hidden;transition:height .2s ease-in-out}")
        self.assertPageContains("summary.setAttribute('aria-controls',body.id)")
        self.assertPageContains("summary.setAttribute('aria-expanded',String(expanded))")
        self.assertPageContains("body.inert=!expanded")
        self.assertPageContains("body.inert=true")
        self.assertPageContains("body.style.height=body.scrollHeight+'px'")
        self.assertEqual(self.page.count("body.style.height=body.scrollHeight+'px'"), 1,
                         "开合逻辑只该有一份")
        # 箭头跟着一起转：正文在动、指示方向的那一枚却一帧跳过去，两处说的就不是同一件事。
        self.assertIn("rotate-90 transition-transform", self.read_front("react/settings/section.tsx"))

    def test_credential_rows_expand_through_the_shared_collapse(self):
        """展开一段正文这件事不该有第二套开合逻辑。

        React 这边的 `Disclosure` 把开合交回遗留的 `setCollapseOpen`：同一份量高度、同一段
        过渡、同一套 `aria-expanded`/`inert`。内边距放在里层，高度才收得到 0——留在外层的话
        border-box 会让它卡在一截空白上，收尾跳一下。"""
        section = self.read_front("react/settings/section.tsx")
        self.assertIn("import { setCollapseOpen } from '@peach/legacy/ui';", section)
        self.assertIn("setCollapseOpen(details.current, body.current, !open);", section)
        self.assertIn('<div ref={body} id={id} inert={!open}>', section)
        self.assertIn('<div className="flex flex-col gap-2 pt-3">{children}</div>', section)
        creds = self.read_react("follow-manage/credentials.tsx")
        self.assertIn("import { Disclosure, ErrorText, ExternalLink, Help } from '../settings/section';", creds)
        self.assertIn("<Disclosure summary={credentialDone(row) ? '修改凭据' : '填写凭据'}", creds)
        self.assertIn("defaultOpen={row.requirement === 'required' && !credentialDone(row)}>", creds)

    def test_credential_rows_carry_the_same_favicon_as_their_source(self):
        """凭据配的就是那个站，用来源行同一枚 favicon 指认它。"""
        creds = self.read_react("follow-manage/credentials.tsx")
        self.assertIn("import { SourceIcon } from './source-view';", creds)
        self.assertIn("<SourceIcon provider={row.provider} />", creds)
        # 槽位占住 14px，不看里面有没有图：没登记 favicon 的站本来就没有，取不下来的
        # 那些还会被整个丢掉，两种情况都会让名字的左边缘参差。
        self.assertIn('<span className="inline-flex size-3.5 shrink-0 items-center justify-center">', creds)
        # 取不下来的那一枚自己撤掉，槽位留着：遗留层靠 `data-drop="self"` 做这件事，React 这边
        # 是组件自己记下失败。两条路都不能把一个碎图标留在名字左边。
        self.assertIn("onError={() => setBroken(true)}", self.read_react("follow-manage/source-view.tsx"))

    def test_the_follow_list_has_a_default_view_and_a_table_view(self):
        """同一批来源两种看法：默认按作者分卡，表格一行一条。

        两种视图共用一个勾选集合和一份排序状态——换视图不该让「我选中的那批」或者
        「现在按什么排」变一次。版式是这台浏览器的个人偏好，存进 `appSettings`，不进地址栏。
        """
        self.assertReactContains(
            "follow-manage/follow-manage.ts",
            "export const LAYOUTS = [['default', '默认视图'], ['table', '表格视图']] as const;")
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("const asTable = layout === 'table';", sources)
        self.assertIn("aria-label={LAYOUTS[0][1]} aria-pressed={!asTable}", sources)
        self.assertIn("aria-label={LAYOUTS[1][1]} aria-pressed={asTable}", sources)
        # 勾选集合只有一份，两种视图都读它；表格那份 rowSelection 是由它派生的投影。
        self.assertIn("const rowSelection: RowSelectionState = useMemo(\n"
                      "    () => Object.fromEntries([...selected].map((id) => [String(id), true])), [selected]);",
                      sources)
        self.assertIn("const pageIds = asTable", sources)
        # 排序也只有一份：两种视图读同一个 sort/dir，表格自己不再排一遍。
        self.assertIn("manualSorting: true,", sources)
        # 版式存进设置，不写地址栏。
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        self.assertIn("savePreference({ layout: next });", page)
        self.assertNotIn("go({ layout", page)
        self.assertIn("const [layout, setLayout] = useState<Layout>", page)

    def test_selected_rows_keep_the_divider_only_surface_in_both_views(self):
        """卡片来源行保持透明并以 divider 分隔，表格底色仍归 BoardUI Table。"""
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("<div data-selected={selected || undefined}", sources)
        row_open = sources[sources.index("<div data-selected={selected || undefined}"):]
        row_open = row_open[:row_open.index('">') + 2]
        self.assertNotIn("data-selected:bg-", row_open)
        self.assertIn("data-source-divider", sources)
        # 表格行不带额外底色类：那一层归 Table。
        table_block = sources[sources.index("{asTable ? ("):]
        self.assertNotIn("data-selected:bg", table_block)
        self.assertIn("<TableRow key={row.id} id={row.id}>", table_block)

    def test_both_views_render_the_same_source_cells(self):
        """一条来源的格子只有一份写法：默认视图排成一行，表格视图各放一个单元格。

        站标、外链、状态徽章、上次检查这四样两边都从同一组组件和同一个纯函数来——各写一份
        的话，同一条来源在两个视图里迟早读出两个样子。
        """
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("import { AuthorAvatar, SourceIcon, SourceLink, StatusBadge } from './source-view';",
                      sources)
        for shared, times in (("<SourceLink source=", 2), ("<StatusBadge source=", 2),
                              ("checkedText(", 2), ("<AuthorAvatar ", 2)):
            self.assertGreaterEqual(sources.count(shared), times,
                                    f"两种视图都要用同一份 {shared!r}")
        # 行上那两个动作也是同一对，无障碍名称的写法也一样。
        self.assertEqual(sources.count("aria-label={`移除 ${source.label}`}"), 1)
        self.assertEqual(sources.count("aria-label={`移除 ${context.row.original.source.label}`}"), 1)
        view = self.read_react("follow-manage/source-view.tsx")
        self.assertIn("export function SourceLink(", view)
        self.assertIn("export function StatusBadge(", view)
        self.assertIn("export function SourceIcon(", view)
        self.assertIn("export function AuthorAvatar(", view)

    def test_the_table_view_follows_the_boardui_data_table(self):
        """表格视图用的就是 boardui 注册表里 `table` 那一份源码，不是照着它再写一张表。

        `data-table` 条目本身是 `registry:block`，只有一份示例、依赖的条目 Peach 都没有；它演示
        的正是「`table` 配 TanStack Table」这套接法，所以这里照接法做、把 `table` 逐字搬进来。
        外观全在 `.bui-table` 那一组规则里，一起逐字搬进 `react/styles.css`。
        """
        boardui = ROOT / "frontend" / "src" / "react" / "boardui"
        origin = (boardui / "ORIGIN.md").read_text(encoding="utf-8")
        self.assertIn("| `table` |", origin)
        self.assertIn("`components/base/table/table.tsx` |", origin)
        self.assertIn("| `data-table`", origin)
        copied = (boardui / "components" / "base" / "table" / "table.tsx").read_bytes()
        digest = hashlib.sha256(copied).hexdigest()
        recorded = (boardui / "UPSTREAM.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{digest}  components/base/table/table.tsx", recorded,
                      "逐字复制的源码要和 UPSTREAM.sha256 对得上")
        # 外观不在这里重写：页面只用组件，规则逐字落在 styles.css。
        styles = self.read_front("react/styles.css")
        self.assertIn(".bui-table th {", styles)
        self.assertIn("border-top: 1px solid var(--color-separator-border);", styles)
        self.assertIn(".bui-table tbody tr:not(:last-child) {", styles)
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("import {\n  Table, TableBody, TableCell, TableColumn, TableHeader, TableRow,\n"
                      "} from '@/components/base/table/table';", sources)
        self.assertNotIn("<table", sources, "表格标签归复制过来的那份组件")
        self.assertIn('<Table aria-label="关注来源"', sources)
        self.assertIn('<TableBody renderEmptyState={() => \'这一页没有来源\'}>', sources)

    def test_the_table_header_sorts_by_the_toolbar_sort_keys(self):
        """表头五列与工具栏下拉是同一份维度，点列头就是换工具栏里那一档。

        排序算在**全集**上，分页只切最后一步：TanStack Table 拿到的 `data` 已经是排好的全部
        结果，`manualSorting` 让它别再排一遍——否则「排序」就退化成「只排当前页」，翻页看到
        的不是真的下一批。
        """
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const COLUMN_SORT = {\n"
                      "  author: 'name', source: 'source', provider: 'provider', status: 'status',"
                      " checked: 'checked',\n} as const satisfies Record<string, SortKey>;", data)
        # 状态正序是「先看要处理的」：失败、暂停、未检查、正常。
        self.assertIn("if (state === 'error' || state === 'unauthorized') return 0;", data)
        self.assertIn("if (!source.enabled) return 1;", data)
        self.assertIn("return state === 'ok' ? 3 : 2;", data)
        sources = self.read_react("follow-manage/source-list.tsx")
        # 两边共用一张对照表，方向也共用一个值。
        self.assertIn("const SORT_COLUMN = Object.fromEntries(\n"
                      "  Object.entries(COLUMN_SORT).map(([column, sort]) => [sort, column]),\n"
                      ") as Partial<Record<SortKey, string>>;", sources)
        self.assertIn("const sortable = header.column.id in COLUMN_SORT;", sources)
        self.assertIn("allowsSorting={sortable}", sources)
        self.assertIn("manualSorting: true,", sources)
        # 排好的是全集，分页模型只负责切窗口。
        self.assertIn("const rows = useMemo(() => tableRows(groups, sort, dir, aliases),", sources)
        self.assertIn("data: rows,", sources)
        self.assertIn("getPaginationRowModel: getPaginationRowModel(),", sources)
        # 点列头改的是页面那份 sort/dir，卡片视图跟着一起变。
        self.assertIn("const key = COLUMN_SORT[first.id as keyof typeof COLUMN_SORT];\n"
                      "      if (key) onSort(key, first.desc ? 'desc' : 'asc');", sources)

    def test_the_layout_switch_lines_up_with_the_sort_box(self):
        """版式开关、排序框和方向键同处一行，高度必须是同一档。"""
        sources = self.read_react("follow-manage/source-list.tsx")
        toolbar = sources[sources.index("关注列表</h3>"):sources.index("{/* 这一趟在后台跑")]
        # 工具条都走默认 medium（36px 高），排序下拉再由专用钩子锁到同一高度。
        self.assertNotIn('size="small"', toolbar)
        self.assertNotIn('size="sm"', toolbar)
        self.assertNotIn('size="xs"', toolbar)
        self.assertIn("data-button-group", toolbar)
        self.assertIn("data-follow-sort-control", toolbar)

    def test_the_sort_direction_key_is_a_square_icon_button(self):
        """纯图标键是正方形，边长与同排控件同高，图标不被内边距压扁。

        `.fbtn` 自带 `padding:0 12px` 且排在样式表更后面，单类名的 `.fmanagedir`
        压不过它：32px 宽减掉 24px 内边距只剩 8px 内容宽，14px 的箭头会被挤成一条
        6px 的竖线——按钮不方，图标也不成比例。
        """
        self.assertPageContains(".fsechead .fmanagedir{width:var(--control-h);padding:0}")
        self.assertPageContains(".fsechead .fmanagedir svg{width:16px;height:16px}")

    def test_the_list_toolbar_collapses_to_icons_before_it_breaks_into_two_rows(self):
        """放不下时带文字的按钮与下拉只留图标，名字交给 title 与 aria-label。

        判据是这一行自己的宽度：同一个视口下侧栏收起与展开留给它的宽度差两百像素，
        视口断点会在一边早折、在另一边照样超框。
        """
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("const TOOLBAR_COMPACT_PX = 740;", sources)
        self.assertIn("const watch = new ResizeObserver(() => "
                      "setCompact(node.clientWidth < TOOLBAR_COMPACT_PX));", sources)
        self.assertIn("const [toolbar, compact] = useCompactToolbar();", sources)
        self.assertIn('<div ref={toolbar} className="flex flex-wrap items-center gap-2">', sources)
        # 塌下去走 `Button` 自己的 `iconOnly`：从外面改它的内外边距会被 `no-restyle` 挡下。
        self.assertEqual(sources.count("iconOnly={compact}"), 2)
        self.assertNotIn("className={COLLAPSING", sources)
        # 收起后名字还有人说，也还有字形可看，不能剩一个空框。
        self.assertIn('aria-label="检查全部" iconOnly={compact}', sources)
        self.assertIn("aria-label={allCollapsed ? '全部展开' : '全部收起'}", sources)
        self.assertIn("leadingIcon={allCollapsed ? RiArrowDownSLine : RiArrowUpSLine}", sources)

    def test_alias_count_is_neutral_metadata(self):
        """「3 组」只是计数，不是待处理提醒：它是次要字色的一行小字，不是徽章。

        此前是蓝底蓝字的 pill，和主按钮同色，读起来像有事要处理。要处理的事由旁边那两个
        合并按钮说。"""
        alias = self.read_react("follow-manage/alias-manager.tsx")
        self.assertEqual(
            alias.count('<span className="text-body-2-regular text-text-secondary">{`${groups.length} 组`}</span>'), 1)
        self.assertIn('<span className="mr-auto text-body-2-regular text-text-secondary">\n'
                      "              {`${suggestions.length} 组`}\n            </span>", alias)
        for loud in ("<Chip", "text-text-error", "bg-button-primary"):
            self.assertNotIn(loud, alias, "计数不该借用提醒或主按钮的颜色")

    def test_follow_source_icons_fail_back_to_plain_text(self):
        """图标由服务端取回落盘（follow_assets.SOURCE_ICON_URLS），页面只认名单、只请求本机。"""
        icons = self.page.split("const SOURCE_ICON_PROVIDERS=new Set([", 1)[1].split("]);", 1)[0]
        for provider in ("kemono", "pawchive", "simpcity"):
            self.assertIn(f"'{provider}'", icons)
        self.assertNotIn("https://", icons)
        self.assertPageContains(
            'src="/source-icon?provider=${encodeURIComponent(provider)}" alt="" loading="lazy" data-drop="self"')
        # 取不到图标就把 <img> 摘掉，露出纯文字；收场动作由 image-fallback 的
        # 委托监听执行，模板里只声明 `data-drop`。
        self.assertPageContains('data-drop="self"')

    def test_follow_watch_filters_use_the_source_identity(self):
        # 判定本身搬去了服务端（见 FollowContractTests 里的筛选用例）；页面这一侧要
        # 保证的是把身份原样交出去，而不是把显示名或来源标签当筛选值送过去。
        self.assertPageContains("+(followAuthors.size?`&author=${encodeURIComponent([...followAuthors].join(','))}`:'')")
        self.assertPageContains("+(followProviders.size?`&provider=${encodeURIComponent([...followProviders].join(','))}`:'')")
        self.assertPageContains('class="tier followauthors"')
        self.assertPageContains('class="tagbar followfilters"')
        self.assertPageContains('class="pill sourcepill" data-follow-provider=')
        self.assertPageLacks("内容标签目前由 ${")
        self.assertPageContains("const randomizedAuthors=followRandomOrder([...authors],row=>row[0])")
        self.assertPageContains("const topTagRows=followRandomOrder([...tagCounts],row=>row[0]).slice(0,20)")
        self.assertPageContains("if(push)followDiscoverySeed=Math.floor(Math.random()*0xffffffff)")
        self.assertPageContains("topTagRows.push([tag,tagCounts.get(tag)||allCount])")

    def test_follow_tags_are_multi_select_and_use_rule34_property_colours(self):
        self.assertPageContains("let followAuthors=new Set(),followProviders=new Set(),followTags=new Set()")
        # 取交集的判定在服务端；页面负责把多选的标签一次全交出去。
        self.assertPageContains("+(followTags.size?`&tag=${encodeURIComponent([...followTags].join(','))}`:'')")
        self.assertPageContains("selected:followTags.has(key)")
        self.assertPageContains(".r34-artist")
        self.assertPageContains(".r34-character")
        self.assertPageContains(".r34-copyright")
        self.assertPageContains(".r34-metadata")
        self.assertPageContains('[class*="r34-"][aria-pressed="true"]')

    def test_follow_cards_use_author_avatars_and_open_details_inside_peach(self):
        self.assertPageContains("return followCard(group,siblings)")
        self.assertPageContains('title="创作者头像">${followAuthorAvatar(authorSources)}')
        self.assertNotIn(
            'class="mav fsourceavatar" title="${esc(item.provider_label)}">${sourceIcon(item.provider)}',
            self.page,
        )
        self.assertPageContains("async function openFollowDetail(id,push=true,mediaIndex=null,preserveReturn=false)")
        self.assertPageContains("const src=item.playable?`/follow-stream?id=${item.id}${selectedMedia?")
        self.assertPageContains('data-follow-detail="${item.id}"')
        self.assertPageContains("route(`/follow/item/${item.id}`)")
        self.assertPageContains('class="sgrid followdetailgrid${collection||embeddedQueue?\' mixgrid\':\'\'}"')
        self.assertPageContains('class="followorigin externallink" href="${esc(item.url)}" target="_blank"')
        self.assertPageContains('title="打开来源页面" aria-label="打开来源页面"')
        self.assertNotIn('打开来源页面</a>', self.page)
        self.assertPageContains(".followdetailtitle{display:flex;gap:5px")
        self.assertPageContains(".fnote.followmediaissue{margin:18px 0 8px;color:var(--drop)}")
        self.assertPageContains("followAuthorAvatar(authorSources)")
        self.assertPageContains("followTagChip(item,tag,'button')")
        self.assertPageContains("item.detail_tags||item.tags||[]")
        self.assertPageContains(".followdetailtags .tg{max-width:none")
        # 标签是按钮，点下去按这个标签筛选，必须有悬停反馈。通用 `.tg:hover` 的填充和
        # 文字色被按类型着色那两条同权重规则压掉了，只能按标签自己那个类型色加深一档。
        self.assertPageContains(
            ".followdetailtags .tg:hover{border-color:color-mix(in srgb,var(--r34-tag) 68%,transparent)")
        self.assertPageContains(
            "background:color-mix(in srgb,var(--r34-tag) 18%,transparent);color:var(--ink)}")
        self.assertPageContains("const postedBy=item.author&&foldName(item.author)!==foldName(author)")
        self.assertPageContains("openFollowDetail(id);")
        self.assertNotIn('class="cardopenhit" href=', self.page)
        self.assertNotIn('class="t cardtitle" href=', self.page)
        self.assertNotIn('class="fcollectionthumb" href=', self.page)
        self.assertPageContains("route(followDetailReturnPath||'/follow')")
        self.assertPageContains(".followitem a{text-decoration:none}")
        # 标签紧跟动作条。错误行 `.fstate` 带着 `flex:1 1 100%`，在纵向 flex 的右栏里
        # 会把剩余高度全算给自己，把标签压到栏底、中间空一大段。
        self.assertPageContains(".followdetailside .fstate{flex:none}")

    def test_one_fanbox_collection_keeps_its_gofile_folder_sections(self):
        self.assertPageContains("const followGroupedMediaOwner=group=>")
        self.assertPageContains("(item.media_items||[]).some(media=>media.resource_group)")
        self.assertPageContains("const key=media.resource_group||'ungrouped'")
        self.assertPageContains('class="mixgrouplabel"')
        self.assertPageContains('data-follow-media-owner="${item.id}"')

    def test_follow_video_uses_the_shared_videojs_player_and_quality_control(self):
        self.assertPageContains('class="video-js vjs-big-play-centered" controls playsinline preload="metadata"')
        self.assertPageContains("if(followVideo){")
        self.assertPageContains("const followPlayer=await mountDetailPlayer(item,followVideo,appSettings.detailAutoplay,{")
        self.assertPageContains("source:{src,type:selectedMedia?.media_type||item.media_type||'video/mp4'}")
        # 第四个参数是来源自己给的清晰度表：rule34video 把每档写成独立 mp4 字段，
        # videojs 的 qualityLevels 只认 HLS/DASH 的自适应轨道，看不到它们。
        self.assertPageContains(
            "function mountPlayerQualityControl(player,video,fallbackHeight=0,initialSourceQualities=null)")
        self.assertPageContains(
            "const mediaPromise=api(`/follow-qualities?id=${encodeURIComponent(item.id)}`).catch(()=>null);")
        self.assertPageContains("mediaPromise",
                                "关注详情要异步补上来源档位和字节数")
        # 档位和字节数是同一趟回源的产物，播放器两样都从这个应答里取。
        self.assertPageContains("updateQualities?.(next?.qualities?.length?next.qualities:null);")
        self.assertPageContains("const size=Number(next?.size)||0;")
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
        self.assertPageContains("placeItemDetail(detailOriginAnchor,detailOriginAbove);")
        self.assertPageContains("if(!stage.open)stage.showModal();")
        self.assertPageLacks("last.after($('#stage'))")
        self.assertPageContains("if(!$('#stats .followlist')){if(followData)renderFollow();else await openFollow(false)}")
        self.assertPageContains("if(stage.parentElement!==main)main.insertBefore(stage,combo)")

    def test_follow_filters_put_all_first_and_sources_are_icon_only(self):
        self.assertPageContains("const FOLLOW_FILTERS=[['','全部'],['new','未看']")
        self.assertPageContains('title="${esc(label)}" aria-label="来源：${esc(label)}">${sourceIcon(key)}</button>')
        watch = self.page.split("function renderFollow(){", 1)[1].split(
            "function followBackfillState", 1)[0]
        self.assertNotIn("全部来源", watch)
        self.assertNotIn("全部标签", watch)
        self.assertPageContains("pick(followProviders,button.dataset.followProvider);applyFollowView()")
        self.assertPageContains("toggle(followTags,button.dataset.followTag);applyFollowView()")

    def test_follow_horizontal_rails_are_wired_after_each_render(self):
        self.assertPageContains("wireDrag($('#stats').querySelector('.followauthors'))")
        # 筛选条挂进首页那块浮层之后，横滚的是里面的 `.filterscroll`／`.tagscroll`，不是整条。
        self.assertPageContains("wireDrag(filterRow.querySelector('.filterscroll'));wireDrag(filterRow.querySelector('.tagscroll'))")
        self.assertPageContains("wireHorizontalScroller(filterRow.querySelector('.tagscroll'))")
        self.assertPageContains(".followauthors{padding:3px 0 10px")
        self.assertPageContains(".tagscroll::-webkit-scrollbar{display:none}")
        self.assertPageLacks(".followfilters{position:relative")

    def test_credentials_are_typed_into_the_page_not_into_a_file_by_hand(self):
        self.assertReactContains("follow-manage/follow-manage.ts",
                                 "export const FOLLOW_CREDENTIAL_URL = '/api/follow/credential';")
        creds = self.read_react("follow-manage/credentials.tsx")
        self.assertIn("<Input key={name} type=\"password\" label={name} placeholder={fieldHint(row, name)}", creds)
        self.assertIn("{(row.needs || []).map((name) => (", creds)
        # 值只往磁盘走：保存成功就清空输入框，页面上再也看不到。
        self.assertIn("setValues({});", creds)
        self.assertIn(">保存配置</Button>", creds)
        self.assertIn(">清除</Button>", creds)

    def test_required_credentials_expand_and_the_source_menu_offers_configuration(self):
        """非配不可的那几行一进来就是敞开的；在别处撞见缺凭据，也能一步跳过去配。"""
        creds = self.read_react("follow-manage/credentials.tsx")
        self.assertIn("defaultOpen={row.requirement === 'required' && !credentialDone(row)}>", creds)
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("onClick={() => { setOpen(false); openCredentials() }}>需要配置凭据</Button>", add)
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        self.assertIn("openCredentials={() => { setTab('source'); go({ tab: 'source' }) }}", page)

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

        两种计数共用一个表达式，只有量词不同。分开写成 release 记
        `variants.length+1`、work 记 `variants.length` 的话，同一份数据两种口径，
        两个视频的组会显示成「1 个版本」。
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
        # 联网只发生在按下这个键的那一刻。
        self.assertReactContains("follow-manage/source-list.tsx",
                                 "onClick={() => startChecking([])}>")
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

    def test_the_thread_title_is_not_the_author_name(self):
        """F95 的标签是整个线程标题，作者在它末尾的方括号里。

        用户看到的是关注列表上一整串 `Strauzek Collection [2026-09-04] [Mr_Strauz]`
        顶着作者那一行。
        """
        row = {"entity_id": None, "entity_name": None, "provider": "f95zone",
               "ref": "63802", "label": "Strauzek Collection [2026-09-04] [Mr_Strauz]"}
        self.assertEqual(web_follow._author_display_name(row), "Mr_Strauz")
        # 页面不再自己解析标签，那份口径只在服务端一处。
        self.assertPageContains("source.author_name")

    def test_the_card_in_the_opening_post_suggests_the_other_spelling(self):
        """`strauzek` 与 `Mr_Strauz` 是同一张名片上并列的两个写法。

        证据比字符串包含硬，但仍然只是提议：合不合由人点。
        """
        rows = [{
            "id": 1, "entity_id": None, "entity_name": None, "provider": "f95zone",
            "ref": "63802", "label": "Strauzek Collection [2026-09-04] [Mr_Strauz]",
            "metadata_json": json.dumps({"official_links": [
                {"service": "twitter", "handle": "strauzek"},
                {"service": "f95zone", "handle": "strauzek"},
                {"service": "pixiv", "handle": "1881751"}]}),
        }]
        suggestions = web_follow._profile_link_suggestions(rows, {})
        self.assertEqual([(row["canonical"], row["alias"]) for row in suggestions],
                         [("Mr_Strauz", "strauzek")])
        # 论坛账号名常是搬运工自己的，pixiv 的身份是一串数字：都不当别名提。
        self.assertEqual(
            web_follow._profile_link_suggestions(rows, {"strauzek": "mrstrauz"}), [])

    def test_the_add_box_suggests_names_while_you_type(self):
        """敲半个名字就要有下拉，而且分组和排序由服务端说了算。

        记得住 `strauzek` 的人不一定记得住 `Mr_Strauz`，从没关注过的 `lewdgazer`
        更是只有站点那边知道——所以这里问的是接口，不是页面自己手里那份列表。
        """
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const FOLLOW_SUGGEST_URL = '/api/follow/suggest';", data)
        add = self.read_react("follow-manage/add-source.tsx")
        # 分组的名字和次序照服务端回的来，页面不自己排。
        self.assertIn("const options = useMemo(() => (suggest.data?.groups || []).flatMap((group) => (\n"
                      "    group.items.map((item) => "
                      "({ value: item.value, label: item.matched || item.value, group: group.label }))\n"
                      "  )), [suggest.data]);", add)
        self.assertIn('<span className="shrink-0 text-caption-1-regular text-text-tertiary">{option.group}</span>',
                      add)
        # 地址不进这条路：服务端认得出里面的 `/`，那时该做的是解析链接。
        self.assertIn("if (!text || text.includes('/')) { setTerm(''); return }", add)

    def test_the_dropdown_says_it_is_working_while_the_site_answers(self):
        """站上那一路要问补全再问分类，实测一秒上下，这段时间必须看得出在做事。

        空着像是敲了没反应；挂着上一个字的结果更糟——那看着就是新结果，而它属于另一个词。
        所以忙的时候下拉照样掀开，里面是一行独立的等待态，旧结果不留。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("const suggesting = suggest.isFetching;", add)
        self.assertIn("const menuOpen = focused && (options.length > 0 || suggesting);", add)
        self.assertIn('? <div className="px-2 py-1.5"><LoadingDots label="正在查找建议" /></div>', add)
        # 忙态那一行不是候选：上下键和回车这时不该选中一个「正在查找建议」。
        self.assertIn("if (!options.length) return;", add)
        self.assertIn("search(options[active]?.value || line);", add)
        # 每个词各有各的缓存键，上一个词的答案不会盖到这一个词上。
        self.assertReactContains(
            "follow-manage/follow-manage.ts",
            "export const followSuggestKey = (term: string) => ['follow-manage', 'suggest', term] as const;")

    def test_typing_fast_sends_one_request_and_ignores_the_stale_answer(self):
        """联网那一路每敲一下打一枪就是拿站点当键盘缓冲；先回的旧答案还会盖掉新的。"""
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const SUGGEST_DEBOUNCE_MS = 250;", data)
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("const timer = setTimeout(() => setTerm(text), SUGGEST_DEBOUNCE_MS);\n"
                      "    return () => clearTimeout(timer);", add)
        # 只在输入框有焦点时问：焦点已经走了就不再掀开。
        self.assertIn("enabled: term.length > 0 && focused,", add)
        # 取消也交给缓存层：换词时上一次请求带着 signal 一起撤掉。
        self.assertIn("queryFn: ({ signal }) => fetchSuggestions(term, signal),", add)

    def test_a_suggestion_can_be_taken_by_keyboard_or_by_mouse(self):
        """下拉两种拿法都要通，而且拿到的名字直接进查找框。

        鼠标那一路先 `preventDefault` 才行：让下拉抢走焦点就会触发失焦，菜单被收掉，
        click 落到空处。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("onMouseDown={(event) => event.preventDefault()}", add)
        self.assertIn("onClick={() => onPick(option.value)}>", add)
        self.assertIn("if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {", add)
        self.assertIn("search(options[active]?.value || line);", add)
        # 选字中的回车和方向键归输入法，不归这里。
        self.assertIn("if (event.nativeEvent.isComposing) return;", add)
        # 下拉贴着输入框定位，不能贴到整个表单上——那样会落在筛选按钮下面。
        self.assertIn('<div className="relative min-w-64 grow" onFocus={() => setFocused(true)}', add)
        self.assertIn("'absolute top-full z-10 mt-1 flex w-full flex-col gap-1'", add)

    def test_the_source_row_shows_the_site_as_an_icon_only(self):
        """作者卡里站名紧挨着作者名和状态徽章，写出来就是同一个词并排两次。

        表格视图的「站点」是独立一列，列头就叫这个名字，那里出文字。站名两种形态都在：
        图标画得出来时它交给读屏，没登记图标或者那一枚取不下来时它自己显出来。
        """
        view = self.read_react("follow-manage/source-view.tsx")
        self.assertIn("export function SourceIcon({ provider, label }: "
                      "{ provider: string; label?: string }) {", view)
        self.assertIn("if (!src || broken) return label ? <>{label}</> : null;", view)
        self.assertIn("{label ? <VisuallyHidden>{label}</VisuallyHidden> : null}", view)
        sources = self.read_react("follow-manage/source-list.tsx")
        # 卡片行只给图标看；表格那一列照常出文字。
        self.assertIn("<SourceIcon provider={source.provider} label={source.provider_label} />", sources)
        self.assertIn("<SourceIcon provider={context.row.original.source.provider} />\n"
                      "            {context.row.original.source.provider_label}", sources)

    def test_avatars_are_local_urls_and_only_for_providers_that_serve_one(self):
        """头像是元数据，经 Peach 落盘再给页面：两个字段都是本机地址，浏览器不碰对方站点。

        哪些来源实测拿得到由 `follow_assets.mirror_avatar_url` 判定（证据在它的测试里）；
        拿不到的这里也是 None，页面退回首字母，不猜一个路径。
        """
        self.assertEqual(web_follow._avatar_url("kemono", "fanbox/30917150"),
                         "/follow-avatar?provider=kemono&ref=fanbox%2F30917150")
        self.assertEqual(web_follow._avatar_url("pawchive", "fanbox/30917150"),
                         "/follow-avatar?provider=pawchive&ref=fanbox%2F30917150")
        def source_row(provider, ref, metadata="{}"):
            return {"provider": provider, "ref": ref, "metadata_json": metadata}

        self.assertEqual(
            web_follow._official_avatar_url(
                source_row("kemono", "fanbox/30917150")),
            "/follow-avatar?service=fanbox&id=30917150",
        )
        # 论坛来源没有这种 ref，身份只能来自首楼名片：FANBOX 的创作者 id 一步到位，
        # pixiv 的数字 id 要多绕一次官方页，所以排在后面。
        self.assertEqual(
            web_follow._official_avatar_url(source_row(
                "f95zone", "87212",
                '{"official_links":[{"service":"patreon","handle":"jul3dnsfw"},'
                '{"service":"fanbox","handle":"jul3dnsfw"}]}')),
            "/follow-avatar?service=fanbox&id=jul3dnsfw",
        )
        self.assertEqual(
            web_follow._official_avatar_url(source_row(
                "f95zone", "50685",
                '{"official_links":[{"service":"pixiv","handle":"30917150"}]}')),
            "/follow-avatar?service=fanbox&id=30917150",
        )
        # 没有 FANBOX 时交给 X 与 Patreon：几家都递给服务端去比谁更清楚，
        # 取不到头像的 SubscribeStar 和形状不对的手柄不进这串。
        self.assertEqual(
            web_follow._official_avatar_url(source_row(
                "f95zone", "13899",
                '{"official_links":[{"service":"twitter","handle":"Rekin3D"},'
                '{"service":"patreon","handle":"sharkarts"},'
                '{"service":"subscribestar","handle":"sharkart"},'
                '{"service":"twitter","handle":"not a handle"}]}')),
            "/follow-avatar?service=profile&id=twitter%3ARekin3D%2Cpatreon%3Asharkarts",
        )
        self.assertIsNone(web_follow._official_avatar_url(
            source_row("f95zone", "63802")))
        for provider, ref in (("rule34video", "1290582"),
                              ("rule34xxx", "lazyprocrastinator"),
                              ("f95zone", "50685"),
                              ("kemono", "no-slash")):
            self.assertIsNone(web_follow._avatar_url(provider, ref),
                              f"{provider} 没有实测过的头像来源，不该猜一个")

    def test_a_missing_evidence_archive_is_shown_not_swallowed(self):
        # 证据未存档并进那块检查报告，不单独弹一层——但话不能少说。
        self.assertReactContains(
            "follow-manage/source-list.tsx",
            "{evidence ? <Note tone=\"warning\">{`候选已入库，但这一次的原始响应没有留档：${evidence}`}</Note> : null}")
        self.assertReactContains(
            "follow-manage/follow-manage.ts",
            "(job?.results || []).find((row) => row.evidence_error)?.evidence_error || '';")

    def test_a_check_says_what_it_actually_found(self):
        """检查完必须报结果。

        用户的原话是「完全没返回任何结果」：接口每条来源都回了
        added/updated/not_modified/error，而界面拿到之后只是整页重画，
        那些数字一个都没露面，看起来就是点了一下什么都没发生。

        「没有更新」和「检查失败」在界面上都像「什么都没发生」，但一个不用管，
        另一个再不管就会一直漏更新——所以失败必须单独列出来并带上原因。
        回执走 toast（非阻塞、自动消失），失败明细留在页内持久行上。
        """
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export function checkSummary(job: CheckJob): string {", data)
        for needle in ("`新增 ${added} 条`", "`更新 ${updated} 条`", "`${quiet} 个来源没有更新`",
                       "'没有任何更新'",
                       # 「没有更多内容」只跟着回执走，页内不铺它的明细条。
                       "`${exhausted} 个没有更多内容`", "`${failed} 个失败`"):
            self.assertIn(needle, data)
        self.assertNotIn("没有更多历史内容", data)
        sources = self.read_react("follow-manage/source-list.tsx")
        # 跟完这一趟才报，而且报的是这一趟的结果：重画不会把它冲掉，它自己存着。
        self.assertIn("setOutcome(state);", sources)
        self.assertIn("toast(state.status === 'failed' ? (state.error || '检查失败') : checkSummary(state));",
                      sources)
        # 失败明细留在页内，且要说清是哪个站，不能让用户去猜 `rule34xxx` 是什么。
        self.assertIn("export const checkFailures = (job: CheckJob | null): CheckResult[] =>", data)
        self.assertIn("`${failures.length} 个来源检查失败`", sources)
        self.assertIn("{`${row.provider_label || row.provider || ''} "
                      "${row.author || row.label || row.ref || ''}：${row.error || '未说明原因'}`}", sources)
        # 光摆数字会让人去找「详情」，所以给一个具名的后续动作。
        self.assertIn("<Button variant=\"secondary\" size=\"small\" onClick={openFollow}>去看更新</Button>",
                      sources)
        self.assertNotIn("条详情", sources)

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
        「检查全部」同一套控件语言——按钮的边界让「这会改状态」
        在点击之前就看得见。
        """
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn(">全部标记已看</Button>", sources)
        self.assertIn(">全部忽略</Button>", sources)
        # 与本页「检查全部」同一套控件语言、同一档尺寸。
        self.assertEqual(sources.count('<Button variant="secondary" size="small" disabled={readOnly} '
                                       '{...busyProps(markAll.isPending)}'), 2)
        # 不另起一行：按钮就在计数行里，只有计数那半句参与收缩（用户回执）。
        foot = sources[sources.index("{counts.new ? ("):]
        foot = foot[:foot.index(") : null}")]
        self.assertEqual(foot.count("<div"), 1, "计数与两颗按钮同处一行")
        for inside in (">全部标记已看</Button>", ">全部忽略</Button>", 'className="mr-auto'):
            self.assertIn(inside, foot)
        self.assertIn('<span className="mr-auto text-body-2-regular text-text-secondary">\n'
                      "            {`未看 ${counts.new} · 已看 ${counts.seen || 0} ·"
                      " 已保存 ${counts.saved || 0} · 已忽略 ${counts.ignored || 0}`}", sources)

    def test_sources_by_the_same_author_are_one_block(self):
        """同一个作者在几个站上是几条来源、一个人。

        用户截图里 `LazyProcrastinator · fanbox` 出现两次（Kemono / Pawchive）、
        `lazyprocrastinator` 出现两次（Rule34Video / Rule34.xxx），四行读起来像四个人。
        归组用后端算好的 `author_key`，前端不二次猜。
        """
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export function groupByAuthor(sources: FollowSource[]): FollowSource[][] {", data)
        self.assertIn("const key = source.author_key || `source:${source.id}`;", data)
        self.assertReactContains("follow-manage/source-list.tsx",
                                 "{groups.slice(win.start, win.end).map((group) => {")
        # 组标题用作者本人的名字：四条来源合成一组之后还挂着其中一条的平台后缀，
        # 等于说这一组只属于 fanbox，正是这次要消掉的误读。
        self.assertIn("export function authorName(group: FollowSource[], aliases: AliasGroup[] = []): string {",
                      data)
        self.assertIn("const official = group.find((source) => source.official_avatar_url);", data)
        self.assertIn("if (official && authored(official)) return authored(official);", data)
        self.assertIn("/\\s+collections?\\s*$/i", data)
        # 取不到图片时回退作者首字母；不能从来源标签切出中文“初”“一”。
        self.assertIn("export function authorInitial(name: string): string {", data)
        # 镜像头像是官方头像的下一个候选；两条都取不到才换成首字母垫底。
        self.assertIn("export function authorAvatar(group: FollowSource[]): "
                      "{ src: string; fallback: string } {", data)
        view = self.read_react("follow-manage/source-view.tsx")
        self.assertIn("const chain = [src, fallback].filter(Boolean);", view)
        self.assertIn("onError={() => setAt(at + 1)}", view)
        self.assertIn('<span title="没有可用头像"', view)
        self.assertIn("{authorInitial(name)}", view)

    def test_discovered_sources_keep_the_search_term_as_the_author_identity(self):
        """查出来的候选带着「当初是按谁查的」一起写回去。

        同一个人在几个站上的几条来源，就是靠这个身份归成一组；候选上的 `author` 掉了，
        新加进来的来源就各成一组。"""
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const addSource = (candidate: ResolveCandidate) =>", data)
        self.assertIn("author: candidate.author || '', aliases: candidate.aliases || [], defer_check: true,",
                      data)

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
        self.assertPageContains("icon('external-link','externalmark')")
        self.assertPageContains(".followresources a:hover")
        self.assertPageContains("text-decoration:none")

    def test_loading_semantics_and_known_copy_says_followed(self):
        """等待态分两档：说得出进度的画进度条，说不出的画三个点。

        「已经关注」是这一条候选此刻的处境，不是一句口语。"""
        dots = self.read_front("react/components/loading-dots.tsx")
        self.assertIn('<i className="dot-wave-0 size-1 rounded-full bg-current" />', dots)
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("? <Progress label={job.data.message || `查找中：${job.data.checked || 0}/${job.data.total}`}",
                      add)
        self.assertIn("<LoadingDots label={byName ? BY_NAME_HINT : BY_LINK_HINT} />", add)
        self.assertIn("{candidate.known ? '已经关注' : candidate.evidence}", add)
        self.assertNotIn("已经在追", add)
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("<LoadingDots label={job.data?.message || '正在准备检查任务'} />", sources)
        self.assertIn("{...busyProps(rowHandlers.busy)}", sources)

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

    def test_follow_puts_the_media_buttons_at_the_top_row_left_behind_a_separator(self):
        """媒体类型在上排最左，隔一道竖线才是状态——跟资料页那条同一个次序。

        它问的是「这一页现在摆的是哪一类东西」，比右边那五枚粗一级：视频和图片各是
        一整批内容，状态是在这一批里再挑一档。摆在下排右端的话，它挨着的是排序键和
        动作键，读起来像给当前这批加的又一个条件，而它换掉的是整页内容。
        """
        self.assertPageContains("const followMediaKinds=group=>")
        self.assertPageContains("function followItemMediaKinds(item)")
        self.assertPageContains("const item=followItemForMedia(group)")
        self.assertPageContains("return mediaViewButtonsHtml({active:followMediaView,videoCount:counts.videos,imageCount:counts.images,\n"
                                "    className:'followmediaview'});")
        self.assertPageContains("button.dataset.mediaView")
        self.assertPageLacks('class="insightswitch followmediaswitch"')
        self.assertPageLacks("params.set('media-ui','switch')")
        self.assertPageLacks('class="followmediaicons"')
        self.assertPageLacks('data-follow-media=')
        self.assertPageContains("params.set('author',[...followAuthors].join(','))")
        self.assertPageContains("route(followViewPath());renderFollow()")
        self.assertPageContains("if(!counts.images&&followMediaView!=='images')return ''")
        self.assertPageLacks("if(followMediaView==='images'&&!mediaCounts.images)followMediaView='videos'")
        self.assertPageLacks("if(followMediaView==='videos'&&!mediaCounts.videos&&mediaCounts.images)followMediaView='images'")
        self.assertPageContains("const preferredKind=followMediaView==='images'?'image':'video'")
        watch = self.page.split("function renderFollow(){", 1)[1].split(
            "function followBackfillState", 1)[0]
        # 媒体那两枚在最左、自己一段；竖线之后才是横滚那一截里的五枚状态。
        self.assertIn(
            '''class="tagbar followfilters" aria-label="${mediaControl?'媒体与关注筛选':'关注筛选'}">'''
            '''${mediaControl}${mediaControl?'<span class="sep" aria-hidden="true"></span>':''}'''
            '<div class="filterscroll">'
            '<div class="viewpills followviews" role="group" aria-label="状态">${FOLLOW_FILTERS.map',
            watch,
        )
        # 媒体那一档另有一块滑过去的玻璃，跟状态那五枚不共用：共用的话点一下图片，
        # 玻璃会从「未看」那儿飞过来。
        self.assertIn("const mediaRow=filterRow.querySelector('.followmediaview');", watch)
        self.assertIn("if(mediaRow)wireViewGlideRow(mediaRow,[...mediaRow.querySelectorAll('[data-media-view]')],'media');", watch)
        self.assertIn("const mediaControl=followMediaControl(mediaCounts);", watch)
        self.assertIn("mountFilterFrame(filterRow,countRow,{views:filterRow.querySelector('.followviews'),", watch)
        self.assertNotIn("${followMediaControl(mediaCounts)}${FOLLOW_FILTERS", watch)
        self.assertPageContains("followMediaView==='images'?' followphotowall':''")
        self.assertPageContains(".followlist.followphotowall{grid-template-columns:repeat(5,minmax(0,1fr))")
        self.assertPageLacks(".followlist.followphotowall>.stage{column-span:all}")
        self.assertPageContains("placeItemDetail(detailOriginAnchor,detailOriginAbove);",
                                "图片详情复用独立浮窗，保持图片墙布局")
        self.assertPageContains(".followitem.imagecard .pic{aspect-ratio:4/3;min-height:0")
        self.assertPageContains(".followitem.imagecard .followvisual .pic>img{position:absolute")
        self.assertPageLacks(".followlist.followphotowall{display:block;column-count:5")
        self.assertPageLacks(".followitem.imagecard .pic{aspect-ratio:auto")
        self.assertPageLacks(".followitem.imagecard{display:inline-flex;width:100%;margin:0 0 14px;break-inside:avoid}")

    def test_external_file_pages_do_not_default_to_video_and_paging_actions_share_one_row(self):
        self.assertPageContains("else if(item.media_kind==='image'||item.media_kind==='video')kinds.add(item.media_kind)")
        self.assertPageLacks("else kinds.add(item.media_kind==='image'?'image':'video')")
        self.assertPageContains('class="followpagination"')
        self.assertPageContains("${icon('chevron-down')}加载更多")
        self.assertPageLacks("${icon('plus')}加载更多")
        self.assertPageContains("${icon('history')}抓更早的一页")
        self.assertPageContains("wireLoadMore(more,{")
        self.assertPageContains("isCurrent:()=>surfaceCurrent(surface)&&followData===page")
        self.assertPageContains("spinnerHtml('抓取中')")

    def test_follow_management_list_has_routed_sorting(self):
        """排序和页码一起挂在地址栏上：排序决定了哪些来源落在第二页，两者是同一件事的两半。

        换排序只是把手里这份数据重排一次，不重取接口、不换骨架。"""
        data = self.read_react("follow-manage/follow-manage.ts")
        self.assertIn("export const SORT_OPTIONS = [\n"
                      "  ['checked', '检查时间'], ['added', '添加时间'], ['name', '创作者名称'],"
                      " ['sources', '来源数量'],\n"
                      "  ['source', '来源名称'], ['provider', '站点'], ['status', '状态'],\n"
                      "] as const;", data)
        self.assertIn("export const isSortKey = (value: unknown): value is SortKey =>\n"
                      "  SORT_OPTIONS.some(([key]) => key === value);", data)
        self.assertIn("const added = (group: FollowSource[]) => "
                      "Math.max(...group.map((s) => timeOf(s.created_at)));", data)
        self.assertIn("if (sort === 'added') return flip * (added(b) - added(a)) || byName(a, b);", data)
        # 每条比较器写的都是该列的默认方向，`flip` 只在方向偏离默认时取反：写成
        # 「asc 就取反」的话，创作者名称默认本来就是正序，一进页面就被翻成倒序。
        self.assertIn("const flip = dir === SORT_DEFAULT_DIR[sort] ? 1 : -1;", data)
        self.assertIn("export const SORT_DEFAULT_DIR: Record<SortKey, SortDir> = {\n"
                      "  checked: 'desc', added: 'desc', name: 'asc', sources: 'desc',\n"
                      "  source: 'asc', provider: 'asc', status: 'asc',\n};", data)
        # 方向键与排序下拉并排，名称播报点下去会得到什么。
        sources = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("leadingIcon={dir === 'asc' ? RiArrowUpLine : RiArrowDownLine}", sources)
        self.assertIn("aria-label={sortLabel(sort, dir)}", sources)
        # 是默认值就不写进地址，免得挂一个和默认完全一样的参数。判据只有数据层知道。
        page = self.read_react("follow-manage/follow-manage-page.tsx")
        self.assertIn("sort: nextSort === DEFAULT_SORT ? '' : nextSort,\n"
                      "      dir: nextDir === SORT_DEFAULT_DIR[nextSort] ? '' : nextDir,", page)
        self.assertIn("setSort(nextSort);\n              setDir(nextDir);\n"
                      "              setPage(1);\n"
                      "              go({ sort: nextSort, dir: nextDir, page: 1 });", page)
        backend = (ROOT / "src" / "peach" / "web_follow.py").read_text(encoding="utf-8")
        self.assertIn('"created_at": row["created_at"]', backend)

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
        self.assertPageContains('.followdetailmedia.image{background:')
        # 媒体框不给视口高度的地板：里面的播放器高度由 16:9 和自己的宽度推出来，地板挂在
        # vh 上时两个量在窄屏上朝相反方向走，框比画面高出一大截，上下各空一片。
        self.assertPageContains('.followdetailmedia{--follow-image-arrow-inset:16px}')
        self.assertPageLacks('min-height:min(62vh,640px)')
        self.assertPageContains('.followdetailplaceholder{aspect-ratio:16/9;display:grid;place-items:center;')

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
        # 它是去另一页的入口，不是这一页的主动作：蓝色留给它右边那枚「检查更新」。
        self.assertPageContains('class="fbtn fcheck" data-follow-manage')
        self.assertPageLacks('class="fbtn primary fcheck"')
        rule = self.page[self.page.index(".follow .fcheck{"):
                         self.page.index("}", self.page.index(".follow .fcheck{"))]
        self.assertNotIn("--pill-radius", rule)
        self.assertNotIn("height:40px", rule)

    def test_detail_images_open_the_same_lightbox_as_the_performer_page(self):
        """关注详情的图要能点开大图，用的必须是同一个灯箱，不是另写一套。

        灯箱不写死 `/photo?id=`：那是本地 ledger 资产的取图口，在线图没有 asset id，
        套不进去。所以按 slide 归一化，在线图直接给 URL。
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
        self.assertPageContains("wireContextCard(")
        self.assertPageContains(".photodetail>button[hidden]{display:none}")
        self.assertPageLacks("if(!asset){toggle.hidden=true;dismiss();return}",
                             "在线图片的整个信息入口仍被隐藏")



if __name__ == "__main__":
    unittest.main()
