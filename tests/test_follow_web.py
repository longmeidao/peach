"""追更的 Web 契约与页面源测试。

契约层测试用临时数据库；页面源测试守的是「追更表面」这一个语义契约，
不是某个文件——判据同 `tests/test_web_ui.py`。
"""
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from peach import web_follow
from peach.follow import FollowSourceError
from peach.follow_secrets import CredentialError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.follow_store import FollowStore
from peach.migrations import discover
from peach.web_contract import WebContract, dispatch_api_get, dispatch_api_post


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
            follow_secrets_root=self.root / "secrets")

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

    def test_feed_never_exposes_the_raw_media_url(self):
        # 界面只需要知道有没有媒体；直链是来源层的事，不进公共 JSON。
        self._seed()
        payload = json.dumps(self._get(), ensure_ascii=False)
        self.assertNotIn("media_url", payload)
        self.assertIn('"has_media"', payload)

    def test_feed_filters_by_status_and_reports_counts(self):
        self._seed()
        first = self._get()["groups"][0]["primary"]["id"]
        self._post("/api/follow/status", {"item": first, "to": "ignored"})
        self.assertEqual(self._get(status="new")["counts"],
                         {"new": 1, "seen": 0, "saved": 0, "ignored": 1})
        self.assertEqual(len(self._get(status="ignored")["groups"]), 1)

    def test_feed_ignores_a_nonsense_limit_instead_of_failing(self):
        self._seed()
        self.assertEqual(len(self._get(limit="nope")["groups"]), 1)

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

    def test_source_errors_are_recorded_for_later_inspection(self):
        self._seed()
        with mock.patch.object(web_follow, "build_connector") as factory:
            factory.return_value.fetch.side_effect = FollowSourceError("HTTP 503")
            self._post("/api/follow/check", {})
        self.assertEqual(self._get()["sources"][0]["last_status"], "error")
        self.assertIn("503", self._get()["sources"][0]["last_error"])

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

    def test_f95_thread_activity_is_labelled_as_a_release_group(self):
        self._seed(provider="f95zone", ref="50685", semantics="release", candidates=(
            FollowCandidate(provider="f95zone", external_id="21383374",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            url="https://f95zone.to/threads/50685/post-21383374",
                            published_at="2026-08-21T04:14:09Z", author="Jkhomie1198",
                            summary="New batch up Gofile",
                            extra={"media_needs_credential": True}),
            FollowCandidate(provider="f95zone", external_id="21394555",
                            title="Lazy Procrastinator Collection [2026-06-28]",
                            url="https://f95zone.to/threads/50685/post-21394555",
                            published_at="2026-08-22T18:09:23Z"),
        ))
        group = self._get()["groups"][0]
        self.assertTrue(group["is_release"])
        self.assertEqual(group["primary"]["external_id"], "21394555")
        self.assertEqual(group["primary"]["version"], "2026-06-28")
        self.assertTrue(group["variants"][0]["media_needs_credential"])
        # 线程动态要说清是谁发的；一个线程里九条回复全标成 main 没有信息量。
        self.assertEqual(group["variants"][0]["author"], "Jkhomie1198")
        self.assertEqual(group["variants"][0]["summary"], "New batch up Gofile")


class FollowWebSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        web = ROOT / "web"
        cls.page = chr(10).join(
            (web / name).read_text(encoding="utf-8")
            for name in ("index.html", "app.css", "app.js"))

    def assertPageContains(self, needle, message=""):
        if needle not in self.page:
            self.fail(f"Web 表面缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def test_follow_is_a_manage_section_with_its_own_route(self):
        self.assertPageContains("['follow','在线追更','globe']")
        self.assertPageContains("if(path==='/follow')return 'follow'")
        self.assertPageContains("if(section==='follow'){openFollow();return}")
        self.assertPageContains("if(path==='/follow'){await openFollow(false);return}")

    def test_approximate_timestamps_are_labelled_as_approximate(self):
        # 站点只给「1 周前」时换算值不是发布时间，界面必须照实说。
        self.assertPageContains("item.published_precision==='approximate'?`约 ${text}`")

    def test_release_variant_rows_show_when_not_a_meaningless_kind(self):
        self.assertPageContains("if(!label&&group.is_release)label=(item.published_at||'').slice(5,10)")

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
        self.assertPageContains("if(location.pathname==='/follow')return;")

    def test_credential_dependent_media_is_called_out(self):
        self.assertPageContains("媒体需要登录会话才能取，发现本身不需要")

    def test_follow_styles_exist_for_the_card_surface(self):
        for selector in (".followlist{", ".followitem{", ".fbadge{", ".fvariants{"):
            self.assertPageContains(selector)


if __name__ == "__main__":
    unittest.main()
