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
    origin_group_key, parse_source_url,
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
  <div class="bbWrapper"><blockquote class="bbCodeBlock">Jkhomie1198 said:
    <a href="https://f95zone.to/masked/gofile.io/50685/abc">Gofile</a>
    Click to expand...</blockquote>
  Genre spoilers first page have futa spoiler.</div>
</article>
</body></html>"""

# 形状取自 2026-08-25 对 api.rule34.xxx 的实测响应：顶层是裸列表，`image` 是 32 位
# 十六进制哈希（15/15），`parent_id` 全是 0（15/15），`source` 13/15 有值。
RULE34XXX_JSON = json.dumps([
    {"id": 18534395, "image": "3df1cbc67e072d6144588d6c80e490ea.mp4", "parent_id": 0,
     "tags": "lazyprocrastinator fiona blush video sound", "change": 1787445373,
     "file_url": "https://api-cdn-mp4.rule34.xxx/images/1232/3df1.mp4",
     "preview_url": "https://api-cdn.rule34.xxx/thumbnails/1232/t_3df1.jpg",
     "score": 72, "source": "https://lazyprocrast.fanbox.cc/posts/12304831"},
    {"id": 18534396, "image": "3bda1572c365b223d8b287c538a38956.mp4", "parent_id": 0,
     "tags": "lazyprocrastinator fiona video", "change": 1787445300,
     "file_url": "https://api-cdn-mp4.rule34.xxx/images/1232/3bda.mp4",
     "score": 70, "source": "https://www.fanbox.cc/@lazyprocrast/posts/12304831"},
    {"id": 18534397, "image": "93eaeadff5effabe078c738aab85b3bc.mp4", "parent_id": 0,
     "tags": "lazyprocrastinator sayuri video", "change": 1787445200,
     "file_url": "https://api-cdn-mp4.rule34.xxx/images/1232/93ea.mp4", "score": 12},
    {"id": 18534398, "image": "fiona_paizuri_nude.mp4", "parent_id": 18534397,
     "tags": "lazyprocrastinator fiona nude", "change": 1787445100,
     "file_url": "https://api-cdn-mp4.rule34.xxx/images/1232/fp.mp4", "score": 9},
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
        # post id 就是原平台的 post id，和别的站点从 source 归一出的键同一个命名空间。
        self.assertEqual(first.group_hint, "fanbox:11406814")

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

    def test_quoted_posts_are_stripped_from_the_reply_body(self):
        # 引用块里的链接是被引用那层发的。不剥掉会把追更信号指向错误的楼层。
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        second = result.candidates[1]
        self.assertEqual(second.summary, "Genre spoilers first page have futa spoiler.")
        self.assertIsNone(second.media_url)
        self.assertEqual(second.extra["link_count"], 0)

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

    def test_the_declared_origin_becomes_a_cross_site_group_key(self):
        # 同一个 fanbox 帖在 source 里有两种写法，必须归一到同一个键——而那串数字
        # 正是 kemono 上同一帖子的 post id，跨站重复因此能精确命中。
        candidates = self._connector().fetch("lazyprocrastinator").candidates
        self.assertEqual(candidates[0].group_hint, "fanbox:12304831")
        self.assertEqual(candidates[1].group_hint, "fanbox:12304831")

    def test_posts_without_an_origin_fall_back_to_the_booru_parent_chain(self):
        candidates = self._connector().fetch("lazyprocrastinator").candidates
        # 父帖用自己的 id，子帖用 parent_id，拼出来是同一个键。
        self.assertEqual(candidates[2].group_hint, "rule34xxx:post:18534397")
        self.assertEqual(candidates[3].group_hint, "rule34xxx:post:18534397")

    def test_a_hash_filename_is_not_used_as_a_title(self):
        # 实测 15/15 的 image 都是哈希。拿它当标题既不可读，又会让每条帖子各自成组。
        first = self._connector().fetch("lazyprocrastinator").candidates[0]
        self.assertNotIn("3df1cbc6", first.title)
        self.assertEqual(first.extra["title_from"], "tags")
        self.assertFalse(first.title_is_name)
        self.assertIn("fiona", first.title)
        self.assertEqual(first.published_at, "2026-08-23T00:36:13Z")

    def test_a_readable_filename_is_still_preferred_and_counts_as_a_name(self):
        last = self._connector().fetch("lazyprocrastinator").candidates[3]
        self.assertEqual(last.title, "fiona paizuri nude")
        self.assertEqual(last.extra["title_from"], "image")
        self.assertTrue(last.title_is_name)

    def test_the_tag_label_drops_the_subject_and_media_words(self):
        first = self._connector().fetch("lazyprocrastinator").candidates[0]
        for noise in ("lazyprocrastinator", "video", "sound"):
            self.assertNotIn(noise, first.title)


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


class OriginGroupKeyTests(unittest.TestCase):
    def test_the_two_fanbox_url_shapes_normalize_together(self):
        self.assertEqual(origin_group_key("https://lazyprocrast.fanbox.cc/posts/12304831"),
                         origin_group_key("https://www.fanbox.cc/@lazyprocrast/posts/12304831"))

    def test_known_platforms_get_their_own_prefix(self):
        self.assertEqual(origin_group_key("https://x.com/a/status/20861277667730761"),
                         "x:20861277667730761")
        self.assertEqual(origin_group_key("https://twitter.com/a/status/12345678"),
                         "x:12345678")
        self.assertEqual(origin_group_key("https://www.patreon.com/posts/98765432"),
                         "patreon:98765432")

    def test_unknown_hosts_and_junk_yield_nothing(self):
        for value in ("https://rule34video.com/video/4542721/", "https://fanbox.cc/",
                      "not a url", "", None, 12345):
            self.assertIsNone(origin_group_key(value))


class ParseSourceUrlTests(unittest.TestCase):
    """粘进来的链接怎么认。纯解析，不联网。"""

    def test_each_supported_host_maps_to_its_provider_and_ref(self):
        cases = {
            "https://kemono.cr/fanbox/user/30917150": ("kemono", "fanbox/30917150"),
            "https://coomer.st/onlyfans/user/abc": ("coomer", "onlyfans/abc"),
            "https://pawchive.pw/patreon/user/123": ("pawchive", "patreon/123"),
            "https://rule34video.com/models/lazyprocrastinator/":
                ("rule34video", "lazyprocrastinator"),
            "https://rule34.xxx/index.php?page=post&s=list&tags=lazyprocrastinator":
                ("rule34xxx", "lazyprocrastinator"),
            "https://f95zone.to/threads/lazy-collection.50685/": ("f95zone", "50685"),
        }
        for url, expected in cases.items():
            parsed = parse_source_url(url)
            self.assertEqual((parsed.provider, parsed.ref), expected, url)

    def test_a_deep_link_is_narrowed_to_the_creator(self):
        parsed = parse_source_url("https://kemono.cr/fanbox/user/30917150/post/11406814")
        self.assertEqual(parsed.ref, "fanbox/30917150")
        self.assertEqual(parsed.url, "https://kemono.cr/fanbox/user/30917150")

    def test_threads_get_release_semantics_and_others_get_work(self):
        self.assertEqual(parse_source_url("https://f95zone.to/threads/x.1/").semantics,
                         "release")
        self.assertEqual(
            parse_source_url("https://rule34video.com/models/abc/").semantics, "work")

    def test_a_bare_host_is_accepted_and_www_is_ignored(self):
        self.assertEqual(parse_source_url("rule34video.com/models/abc/").provider,
                         "rule34video")
        self.assertEqual(parse_source_url("https://www.rule34video.com/models/abc/").ref,
                         "abc")

    def test_the_thread_slug_becomes_a_readable_label(self):
        parsed = parse_source_url(
            "https://f95zone.to/threads/lazy-procrastinator-collection.50685/")
        self.assertEqual(parsed.label, "lazy procrastinator collection")

    def test_the_label_stops_at_the_release_date_not_at_the_end_of_the_slug(self):
        # f95 的 slug 惯例是 `<作品名>-<发布日期>-<作者手柄>`，全取会得到一长串元数据。
        parsed = parse_source_url(
            "https://f95zone.to/threads/"
            "lazy-procrastinator-collection-2026-06-28-lazyprocrastinator-lazyprocrast.50685/")
        self.assertEqual(parsed.label, "lazy procrastinator collection")

    def test_the_right_host_with_the_wrong_path_says_what_shape_is_expected(self):
        for url, hint in (
            ("https://kemono.cr/posts", "fanbox/user"),
            ("https://rule34video.com/latest-updates/", "models"),
            ("https://rule34.xxx/index.php?page=post&s=view&id=1", "tags="),
            ("https://f95zone.to/latest", "threads"),
        ):
            with self.assertRaises(FollowSourceError) as caught:
                parse_source_url(url)
            self.assertIn(hint, str(caught.exception), url)

    def test_credentials_and_non_http_urls_are_refused(self):
        for url in ("https://user:pw@kemono.cr/fanbox/user/1",
                    "ftp://kemono.cr/fanbox/user/1", ""):
            with self.assertRaises(FollowSourceError):
                parse_source_url(url)


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
