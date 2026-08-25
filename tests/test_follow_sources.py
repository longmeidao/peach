"""站点追更连接器的隔离测试。

夹具的字段名与 DOM 结构取自 2026-08-25 对真实站点的实测响应（kemono.cr
`fanbox/30917150`、rule34video.com `/models/lazyprocrastinator/`、f95zone
thread 50685），不是凭记忆构造的形状。测试本身不联网：transport 全部注入。
"""
import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from peach.follow import FollowSourceError
from peach.follow_secrets import Credential, CredentialError, CredentialStore
from peach.follow_sources import (
    USER_AGENT, F95ZoneConnector, KemonoConnector, Rule34VideoConnector,
    Rule34XxxConnector, SimpCityConnector, build_connector, _iso_from_relative,
)
from peach.http import HttpResponse


def _transport(status=200, headers=None, body=b"", record=None):
    def call(request, timeout, max_bytes):
        if record is not None:
            record.append(request)
        return HttpResponse(status, headers or {}, body)
    return call


KEMONO_POSTS = json.dumps([
    {"id": "11406814", "user": "30917150", "service": "fanbox",
     "title": "Villainous Valentine's Day 7", "substring": "",
     "published": "2026-02-14T21:51:10", "edited": None,
     "file": {"name": "a.png", "path": "/1c/fa/1cfae7.png"},
     "attachments": [{"name": "a.zip", "path": "/1c/fa/1cfae7.zip"}]},
    {"id": "11400490", "user": "30917150", "service": "fanbox",
     "title": "Villainous Valentine's Day 6", "published": "2026-02-13T21:30:28",
     "file": {}, "attachments": []},
]).encode()

RULE34VIDEO_HTML = b"""<html><body>
<a class="th js-open-popup" href="https://rule34video.com/video/4542721/fiona-paizuri-nude/"
   title="Fiona - Paizuri (Nude)">
  <div class="img wrap_image" data-preview="https://rule34video.com/get_file/51/aa/4542721_preview.mp4/">
    <img class="thumb lazy-load" src="data:image/gif;base64,R0lGOD"
         data-original="https://rule34video.com/contents/videos_screenshots/4542000/4542721/320x180/3.jpg"/>
    <div class="time">0:20</div>
  </div>
  <div class="thumb_title">Fiona - Paizuri (Nude)</div>
  <div class="thumb_info"><div class="added" title="Submitted: 1 week ago">1 week ago</div></div>
</a>
<a class="th" href="https://rule34video.com/video/4542713/fiona-paizuri/" title="Fiona - Paizuri">
  <div class="img"><div class="time">7:13</div></div>
  <div class="added">4 weeks ago</div>
</a>
<a class="th" href="https://rule34video.com/video/4542713/fiona-paizuri/" title="dup ignored"></a>
</body></html>"""

F95_HTML = b"""<html><head><title>Collection - Video - Lazy | F95zone</title></head><body>
<h1 class="p-title-value"><span class="label">Collection</span><span class="label">Video</span>
Lazy Procrastinator Collection [2026-06-28] [LazyProcrastinator/LazyProcrast]</h1>
<article data-content="post-21383374" data-author="Jkhomie1198">
  <time datetime="2026-08-21T05:14:09+0100">Aug 21, 2026</time>
  <div class="bbWrapper">New batch up <a href="/goto/post?id=1">quoted</a>
  <a href="https://f95zone.to/masked/gofile.io/50685/abc">Gofile</a></div>
</article>
<article data-content="post-21394555" data-author="kim2311">
  <time datetime="2026-08-22T19:09:23+0100">Aug 22, 2026</time>
  <div class="bbWrapper">Genre spoilers first page have futa spoiler.</div>
</article>
</body></html>"""

RULE34XXX_JSON = json.dumps([
    {"id": 9988776, "image": "fiona_paizuri_nude.mp4", "parent_id": 9988770,
     "tags": "lazyprocrastinator fiona nude", "change": 1787000000,
     "file_url": "https://api-cdn.rule34.xxx/images/1/abc.mp4",
     "preview_url": "https://api-cdn.rule34.xxx/thumbnails/1/abc.jpg",
     "score": 42, "source": "https://rule34video.com/video/4542721/"},
    {"id": 9988770, "image": "fiona_paizuri.mp4", "parent_id": 0,
     "tags": "lazyprocrastinator fiona", "change": 1786990000,
     "file_url": "https://api-cdn.rule34.xxx/images/1/def.mp4", "score": 40},
]).encode()


class KemonoConnectorTests(unittest.TestCase):
    def test_fetch_normalizes_posts_and_sends_the_documented_accept_header(self):
        seen = []
        connector = KemonoConnector(transport=_transport(body=KEMONO_POSTS, record=seen,
                                                         headers={"ETag": '"k1"'}))
        result = connector.fetch("fanbox/30917150")
        self.assertEqual(seen[0].url,
                         "https://kemono.cr/api/v1/fanbox/user/30917150/posts")
        # 站点自己在 403 响应体里要求抓取带这个头，不是绕过防护。
        self.assertEqual(seen[0].headers["Accept"], "text/css")
        self.assertEqual(seen[0].headers["User-Agent"], USER_AGENT)
        self.assertEqual(result.etag, '"k1"')
        self.assertEqual(result.semantics, "work")
        self.assertEqual(len(result.candidates), 2)
        first = result.candidates[0]
        self.assertEqual(first.external_id, "11406814")
        self.assertEqual(first.published_at, "2026-02-14T21:51:10Z")
        self.assertEqual(first.url,
                         "https://kemono.cr/fanbox/user/30917150/post/11406814")
        self.assertEqual(first.media_url, "https://kemono.cr/1c/fa/1cfae7.png")
        self.assertEqual(first.extra["attachment_count"], 1)

    def test_pawchive_returns_a_bare_list_and_uses_its_own_host(self):
        seen = []
        connector = KemonoConnector(provider="pawchive",
                                    transport=_transport(body=KEMONO_POSTS, record=seen))
        result = connector.fetch("fanbox/30917150")
        self.assertTrue(seen[0].url.startswith("https://pawchive.pw/"))
        self.assertEqual(result.provider, "pawchive")
        self.assertEqual(len(result.candidates), 2)

    def test_dict_shaped_payload_is_accepted(self):
        body = json.dumps({"posts": json.loads(KEMONO_POSTS)}).encode()
        result = KemonoConnector(transport=_transport(body=body)).fetch("fanbox/1")
        self.assertEqual(len(result.candidates), 2)

    def test_max_items_bounds_the_result(self):
        connector = KemonoConnector(max_items=1, transport=_transport(body=KEMONO_POSTS))
        self.assertEqual(len(connector.fetch("fanbox/1").candidates), 1)

    def test_not_modified_returns_no_candidates(self):
        connector = KemonoConnector(transport=_transport(status=304))
        result = connector.fetch("fanbox/1", etag='"k1"')
        self.assertTrue(result.not_modified)
        self.assertEqual(result.candidates, ())

    def test_malformed_ref_is_rejected_before_any_request(self):
        seen = []
        connector = KemonoConnector(transport=_transport(record=seen))
        for bad in ("30917150", "fanbox/", "../etc/passwd", "fanbox/a b"):
            with self.assertRaises(FollowSourceError):
                connector.fetch(bad)
        self.assertEqual(seen, [])

    def test_forbidden_status_names_credentials_or_bot_check(self):
        connector = KemonoConnector(transport=_transport(status=403))
        with self.assertRaises(FollowSourceError) as caught:
            connector.fetch("fanbox/1")
        self.assertIn("403", str(caught.exception))

    def test_unknown_kemono_host_is_rejected(self):
        with self.assertRaises(FollowSourceError):
            KemonoConnector(provider="nope")


class Rule34VideoConnectorTests(unittest.TestCase):
    def _fetch(self, body=RULE34VIDEO_HTML, **kwargs):
        return Rule34VideoConnector(transport=_transport(body=body), **kwargs).fetch(
            "lazyprocrastinator")

    def test_creator_page_yields_deduplicated_videos_with_duration(self):
        result = self._fetch()
        self.assertEqual([c.external_id for c in result.candidates],
                         ["4542721", "4542713"])
        self.assertEqual(result.candidates[0].duration, 20.0)
        self.assertEqual(result.candidates[1].duration, 433.0)

    def test_data_uri_placeholder_is_not_used_as_a_thumbnail(self):
        first = self._fetch().candidates[0]
        self.assertTrue(first.thumb_url.endswith("/3.jpg"))
        self.assertTrue(first.media_url.endswith("_preview.mp4/"))

    def test_relative_dates_are_marked_approximate(self):
        first = self._fetch().candidates[0]
        self.assertEqual(first.extra["published_precision"], "approximate")
        self.assertEqual(first.extra["added_text"], "1 week ago")
        self.assertIsNotNone(first.published_at)

    def test_missing_dates_are_reported_as_unknown_not_guessed(self):
        body = b'<a class="th" href="https://rule34video.com/video/1/x/" title="X"></a>'
        candidate = self._fetch(body=body).candidates[0]
        self.assertIsNone(candidate.published_at)
        self.assertEqual(candidate.extra["published_precision"], "unknown")

    def test_empty_parse_is_an_error_not_an_empty_success(self):
        # 结构变了却报「本次没有更新」，会把站点改版静默吞掉。
        with self.assertRaises(FollowSourceError):
            self._fetch(body=b"<html><body>no videos here</body></html>")

    def test_slug_is_validated(self):
        connector = Rule34VideoConnector(transport=_transport(body=RULE34VIDEO_HTML))
        with self.assertRaises(FollowSourceError):
            connector.fetch("../models")


class F95ZoneConnectorTests(unittest.TestCase):
    def test_latest_page_yields_replies_not_just_the_opening_post(self):
        seen = []
        result = F95ZoneConnector(
            transport=_transport(body=F95_HTML, record=seen)).fetch("50685")
        self.assertEqual(seen[0].url, "https://f95zone.to/threads/50685/latest")
        self.assertEqual(result.semantics, "release")
        self.assertEqual([c.external_id for c in result.candidates],
                         ["21383374", "21394555"])
        self.assertEqual(result.candidates[0].author, "Jkhomie1198")
        self.assertEqual(result.candidates[0].published_at, "2026-08-21T04:14:09Z")

    def test_thread_title_drops_prefix_labels_and_keeps_the_version(self):
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        title = result.candidates[0].title
        self.assertTrue(title.startswith("Lazy Procrastinator Collection"))
        self.assertNotIn("F95zone", title)
        self.assertIn("[2026-06-28]", title)

    def test_media_is_flagged_as_needing_a_login_session(self):
        # 发现不需要 cookie，取附件需要。下载动作必须先看这个标志。
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        self.assertTrue(result.candidates[0].extra["media_needs_credential"])

    def test_only_absolute_links_count_as_media(self):
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        self.assertEqual(result.candidates[0].media_url,
                         "https://f95zone.to/masked/gofile.io/50685/abc")
        self.assertIsNone(result.candidates[1].media_url)

    def test_cookie_is_sent_only_when_supplied(self):
        seen = []
        F95ZoneConnector(transport=_transport(body=F95_HTML, record=seen)).fetch("50685")
        self.assertNotIn("Cookie", seen[0].headers)
        seen.clear()
        F95ZoneConnector(transport=_transport(body=F95_HTML, record=seen),
                         credential=Credential("f95zone", {"cookie": "xf=1"})).fetch("50685")
        self.assertEqual(seen[0].headers["Cookie"], "xf=1")

    def test_thread_ref_must_be_numeric(self):
        connector = F95ZoneConnector(transport=_transport(body=F95_HTML))
        with self.assertRaises(FollowSourceError):
            connector.fetch("lazy-procrastinator-collection.50685")

    def test_thread_index_rejects_unknown_categories(self):
        connector = F95ZoneConnector(transport=_transport(body=b"{}"))
        with self.assertRaises(FollowSourceError):
            connector.thread_index("movies", "lazy")

    def test_thread_index_returns_rows(self):
        body = json.dumps({"status": "ok", "msg": {"data": [
            {"thread_id": 50685, "title": "Lazy Procrastinator Collection",
             "version": "2026-06-28"}]}}).encode()
        rows = F95ZoneConnector(transport=_transport(body=body)).thread_index(
            "animations", "lazy procrastinator")
        self.assertEqual(rows[0]["thread_id"], 50685)


class Rule34XxxConnectorTests(unittest.TestCase):
    def _connector(self, record=None, body=RULE34XXX_JSON, status=200):
        return Rule34XxxConnector(
            transport=_transport(status=status, body=body, record=record),
            credential=Credential("rule34xxx", {"user_id": "42", "api_key": "sekret"}))

    def test_credentials_are_required_and_never_enter_the_recorded_url(self):
        seen = []
        result = self._connector(record=seen).fetch("lazyprocrastinator")
        self.assertIn("api_key=sekret", seen[0].url)
        self.assertNotIn("api_key", result.request_url)
        self.assertNotIn("sekret", result.request_url)

    def test_missing_credential_fails_before_the_request(self):
        seen = []
        connector = Rule34XxxConnector(transport=_transport(record=seen))
        with self.assertRaises(CredentialError):
            connector.fetch("lazyprocrastinator")
        self.assertEqual(seen, [])

    def test_parent_id_becomes_the_group_hint(self):
        candidates = self._connector().fetch("lazyprocrastinator").candidates
        self.assertEqual(candidates[0].group_hint, "9988770")
        self.assertIsNone(candidates[1].group_hint)

    def test_filename_is_preferred_over_the_tag_string_as_a_title(self):
        first = self._connector().fetch("lazyprocrastinator").candidates[0]
        self.assertEqual(first.title, "fiona paizuri nude")
        self.assertEqual(first.extra["title_from"], "image")
        self.assertEqual(first.published_at, "2026-08-17T20:53:20Z")

    def test_authentication_rejection_is_reported_as_a_credential_error(self):
        connector = self._connector(
            body=b'"Missing authentication. Go to api.rule34.xxx for more information"')
        with self.assertRaises(CredentialError):
            connector.fetch("lazyprocrastinator")


class SimpCityConnectorTests(unittest.TestCase):
    def test_blocked_source_refuses_instead_of_defeating_the_bot_check(self):
        with self.assertRaises(FollowSourceError) as caught:
            SimpCityConnector().fetch("123")
        self.assertIn("DDoS-Guard", str(caught.exception))


class BuildConnectorTests(unittest.TestCase):
    def test_registry_maps_the_three_kemono_hosts_to_distinct_providers(self):
        for provider in ("kemono", "coomer", "pawchive"):
            self.assertEqual(build_connector(provider).provider, provider)

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(FollowSourceError):
            build_connector("nyaa")


class RelativeDateTests(unittest.TestCase):
    def test_units_are_converted_against_an_injected_reference(self):
        now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(_iso_from_relative("1 week ago", now=now), "2026-08-18T12:00:00Z")
        self.assertEqual(_iso_from_relative("2 days", now=now), "2026-08-23T12:00:00Z")
        self.assertIsNone(_iso_from_relative("just now", now=now))
        self.assertIsNone(_iso_from_relative(None, now=now))


class CredentialStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = CredentialStore(self.root)
        (self.root / "follow").mkdir(parents=True)
        self.addCleanup(self.temporary.cleanup)

    def _write(self, provider, payload, mode=0o600):
        path = self.root / "follow" / f"{provider}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        os.chmod(path, mode)
        return path

    def test_missing_credential_is_none_not_an_error(self):
        self.assertIsNone(self.store.load("rule34xxx"))
        described = self.store.describe("rule34xxx")
        self.assertFalse(described["present"])

    def test_describe_reports_field_names_but_never_values(self):
        self._write("rule34xxx", {"user_id": "42", "api_key": "sekret"})
        described = self.store.describe("rule34xxx")
        self.assertEqual(described["fields"], ["api_key", "user_id"])
        self.assertNotIn("sekret", json.dumps(described))
        self.assertFalse(described["world_readable"])

    def test_group_or_world_readable_permissions_are_reported(self):
        self._write("f95zone", {"cookie": "xf=1"}, mode=0o644)
        self.assertTrue(self.store.describe("f95zone")["world_readable"])

    def test_require_lists_every_missing_field(self):
        self._write("rule34xxx", {"user_id": "42"})
        credential = self.store.load("rule34xxx")
        with self.assertRaises(CredentialError) as caught:
            credential.require("user_id", "api_key")
        self.assertIn("api_key", str(caught.exception))

    def test_unparsable_file_is_an_error(self):
        (self.root / "follow" / "kemono.json").write_text("{oops", encoding="utf-8")
        with self.assertRaises(CredentialError):
            self.store.load("kemono")

    def test_provider_name_cannot_escape_the_secrets_directory(self):
        for bad in ("../ledger", "a/b", ".hidden"):
            with self.assertRaises(CredentialError):
                self.store.path_for(bad)


if __name__ == "__main__":
    unittest.main()
