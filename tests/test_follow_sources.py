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
    USER_AGENT, F95ZoneConnector, FanboxConnector, KemonoConnector,
    PatreonConnector, Rule34PahealConnector, Rule34VideoConnector, Rule34XxxConnector,
    SimpCityConnector, SubscribeStarConnector, build_connector,
    _iso_from_relative, origin_group_key, parse_source_url,
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
    # 第二条只有附件、没有正文文件，`media_url` 要能从附件里取到。它原本连附件也没有，
    # 但那种帖子现在会被判为「不是 release」丢掉，别的断言就都少了一条。
    {"id": "11400490", "user": "30917150", "service": "fanbox",
     "title": "Villainous Valentine's Day 6", "published": "2026-02-13T21:30:28",
     "file": {}, "attachments": [{"name": "b.png", "path": "/2f/46/2f468d.png"}]},
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

RULE34VIDEO_DETAIL_HTML = b"""<html><body>
<script type="application/ld+json">{
  "@context":"https://schema.org","@type":"VideoObject",
  "name":"Fiona - Paizuri (Nude)",
  "thumbnailUrl":"https://rule34video.com/contents/videos_screenshots/4542000/4542721/preview.jpg",
  "uploadDate":"2026-08-18","duration":"PT0H7M13S",
  "contentUrl":"https://rule34video.com/get_file/51/aa/4542721/4542721_360.mp4/"
}</script>
<a class="item btn_link video_meta_pill" href="https://rule34video.com/categories/3d/">3D</a>
<a class="item btn_link video_meta_pill" href="https://rule34video.com/categories/final-fantasy/">Final Fantasy</a>
<a class="item btn_link video_meta_pill" href="https://rule34video.com/models/lazyprocrastinator/">LazyProcrastinator</a>
<a class="tag_item" href="https://rule34video.com/tags/1/">deep throat</a>
<a class="tag_item" href="https://rule34video.com/tags/2/">breast squeeze</a>
<script>video_url: 'https://rule34video.com/get_file/51/aa/4542721.mp4/?v-acctoken=test'</script>
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
<article data-content="post-21400001" data-author="LazyProcrastinator">
  <time datetime="2026-08-23T09:00:00+0100">Aug 23, 2026</time>
  <div class="bbWrapper">Preview attached
    <div data-lb-id="attachment6372325"
         data-src="https://attachments.f95zone.to/2026/08/6372325_preview.png">
      <img data-src="https://attachments.f95zone.to/2026/08/6372325_preview.png">
    </div>
    <a href="https://f95zone.to/attachments/6372325/">View attachment</a>
  </div>
</article>
</body></html>"""

FANBOX_JSON = json.dumps({"body": {"posts": [
    {"id": "12489354", "title": "MobiusFF Sarah Animations", "feeRequired": 0,
     "publishedDatetime": "2026-08-26T23:34:51+09:00", "isRestricted": False,
     "user": {"name": "InitialA"}, "cover": {"url": "https://img.test/cover.jpg"},
     "excerpt": "Public release"},
    {"id": "12400000", "title": "Paid preview", "feeRequired": 500,
     "publishedDatetime": "2026-08-20T00:00:00+09:00", "isRestricted": True},
]}}).encode()

FANBOX_DETAIL_JSON = json.dumps({"body": {"post": {"body": {
    "blocks": [
        {"type": "p", "text": "gofile - https://gofile.io/d/OS2Qz9"},
        {"type": "image", "imageId": "one"},
        {"type": "image", "imageId": "two"},
    ],
    "imageMap": {
        "one": {"originalUrl": "https://downloads.fanbox.cc/one.jpg",
                "thumbnailUrl": "https://downloads.fanbox.cc/one-thumb.jpg"},
        "two": {"originalUrl": "https://downloads.fanbox.cc/two.jpg",
                "thumbnailUrl": "https://downloads.fanbox.cc/two-thumb.jpg"},
    },
}}}}).encode()

GOFILE_JSON = json.dumps({"status": "ok", "data": {"type": "folder", "children": {
    "v1": {"id": "v1", "type": "file", "name": "one.mp4", "mimetype": "video/mp4",
           "link": "https://store1.gofile.io/download/one.mp4",
           "thumbnail": "https://store1.gofile.io/one.jpg", "size": 123},
    "v2": {"id": "v2", "type": "file", "name": "two.mp4", "mimetype": "video/mp4",
           "link": "https://store1.gofile.io/download/two.mp4"},
    "txt": {"id": "txt", "type": "file", "name": "readme.txt", "mimetype": "text/plain",
            "link": "https://store1.gofile.io/download/readme.txt"},
}}}).encode()

SUBSCRIBESTAR_HTML = b"""<html><body>
<div class="post is-shown" data-id="2650844">
  <a class="post-user" href="/initiala">InitialA</a>
  <div class="post-date"><a href="/posts/2650844">Aug 26, 2026 02:34 pm</a></div>
  <div class="post-title"><h2>MobiusFF Sarah Animations</h2></div>
  <div class="post-uploads"><img src="https://img.test/one.jpg"></div>
  <div class="post-content">Posted for FREE tiers</div>
</div></body></html>"""

PATREON_HTML = b"""<html><body><div class="card">
<a href="https://www.patreon.com/sample/posts/new-public-work-167576581"></a>
<h3>New public work</h3><p>2 days ago</p><img src="https://img.test/patreon.jpg">
<a href="https://www.patreon.com/sample/posts/new-public-work-167576581">duplicate</a>
</div></body></html>"""


class OfficialConnectorTests(unittest.TestCase):
    def test_fanbox_keeps_only_public_free_posts(self):
        seen = []
        def route(request):
            seen.append(request)
            return HttpResponse(200, {}, FANBOX_DETAIL_JSON if "post.info" in request.url
                                else FANBOX_JSON)
        result = FanboxConnector(transport=_routed(route)).fetch("ffxivinitiala")
        self.assertIn("creatorId=ffxivinitiala", seen[0].url)
        self.assertEqual(seen[0].headers["Origin"], "https://www.fanbox.cc")
        self.assertIn("Mozilla/5.0", seen[0].headers["User-Agent"])
        self.assertIn("Mozilla/5.0", seen[1].headers["User-Agent"])
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.candidates[0].group_hint, "fanbox:12489354")
        self.assertEqual(result.candidates[0].published_at, "2026-08-26T14:34:51Z")
        self.assertEqual(len(result.candidates[0].extra["media_items"]), 2)
        self.assertEqual(result.candidates[0].extra["links"],
                         ["https://gofile.io/d/OS2Qz9"])
        self.assertEqual(result.probed, 1)

    def test_fanbox_uses_gofile_api_token_and_keeps_only_playable_files(self):
        seen = []
        def route(request):
            seen.append(request)
            if "api.gofile.io" in request.url:
                return HttpResponse(200, {}, GOFILE_JSON)
            return HttpResponse(200, {}, FANBOX_DETAIL_JSON if "post.info" in request.url
                                else FANBOX_JSON)
        result = FanboxConnector(
            transport=_routed(route),
            gofile_credential=Credential("gofile", {"api_token": "secret"}),
        ).fetch("ffxivinitiala")
        post = result.candidates[0]
        self.assertEqual(post.extra["gofile_video_count"], 2)
        self.assertEqual(len(post.extra["media_items"]), 4)
        gofile_request = next(request for request in seen if "api.gofile.io" in request.url)
        self.assertEqual(gofile_request.headers["Authorization"], "Bearer secret")
        self.assertNotIn("secret", gofile_request.url)

    def test_fanbox_cookie_stays_on_fanbox_requests(self):
        seen = []
        def route(request):
            seen.append(request)
            if "api.gofile.io" in request.url:
                return HttpResponse(200, {}, GOFILE_JSON)
            return HttpResponse(200, {}, FANBOX_DETAIL_JSON if "post.info" in request.url
                                else FANBOX_JSON)
        FanboxConnector(
            transport=_routed(route),
            credential=Credential("fanbox", {"cookie": "FANBOXSESSID=session"}),
            gofile_credential=Credential("gofile", {"api_token": "secret"}),
        ).fetch("ffxivinitiala")
        fanbox_requests = [request for request in seen if "api.fanbox.cc" in request.url]
        self.assertTrue(fanbox_requests)
        self.assertTrue(all(request.headers.get("Cookie") == "FANBOXSESSID=session"
                            for request in fanbox_requests))
        gofile_request = next(request for request in seen if "api.gofile.io" in request.url)
        self.assertNotIn("Cookie", gofile_request.headers)

    def test_gofile_premium_requirement_is_not_reported_as_a_bad_token(self):
        def route(request):
            if "api.gofile.io" in request.url:
                return HttpResponse(401, {"content-type": "application/json"},
                                    b'{"status":"error-notPremium","data":{}}')
            return HttpResponse(200, {}, FANBOX_DETAIL_JSON if "post.info" in request.url
                                else FANBOX_JSON)
        connector = FanboxConnector(
            transport=_routed(route),
            gofile_credential=Credential("gofile", {"api_token": "valid-token"}),
        )
        with self.assertRaises(FollowSourceError) as caught:
            connector.fetch("ffxivinitiala")
        self.assertIn("Premium", str(caught.exception))
        self.assertIn("token 有效", str(caught.exception))

    def test_one_blocked_detail_keeps_the_public_list_item(self):
        def route(request):
            if "post.info" in request.url:
                return HttpResponse(403, {}, b"challenge")
            return HttpResponse(200, {}, FANBOX_JSON)
        result = FanboxConnector(transport=_routed(route)).fetch("ffxivinitiala")
        self.assertEqual(len(result.candidates), 1)
        self.assertIn("HTTP 403", result.candidates[0].extra["media_error"])
        self.assertEqual(result.candidates[0].extra["media_items"], ())

    def test_subscribestar_reads_public_profile_posts_without_login(self):
        result = SubscribeStarConnector(
            transport=_transport(body=SUBSCRIBESTAR_HTML)).fetch(
                "subscribestar.adult/initiala")
        self.assertEqual(len(result.candidates), 1)
        post = result.candidates[0]
        self.assertEqual(post.external_id, "2650844")
        self.assertEqual(post.title, "MobiusFF Sarah Animations")
        self.assertEqual(post.author, "InitialA")
        self.assertEqual(post.url, "https://subscribestar.adult/posts/2650844")

    def test_patreon_uses_server_rendered_public_cards_and_deduplicates_links(self):
        result = PatreonConnector(transport=_transport(body=PATREON_HTML)).fetch("sample")
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].external_id, "167576581")
        self.assertEqual(result.candidates[0].title, "New public work")
        self.assertEqual(result.candidates[0].group_hint, "patreon:167576581")

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

PAHEAL_LIST_HTML = b"""<div class='shm-image-list'>
<div class='shm-thumb thumb' data-ext='mp4'
 data-tags='amina animated blender final_fantasy_vii initiala tifa_lockhart'
 data-post-id='7428820'><a class='shm-thumb-link' href='/post/view/7428820'>
 <img src='https://r34t.paheal.net/df/fb/thumb'></a>
 <a href='https://r34i.paheal-cdn.net/df/fb/video'>File Only</a></div></div>"""

PAHEAL_DETAIL_HTML = b"""<video id='main_image' poster='https://r34t.paheal.net/df/fb/thumb'>
<source src='https://r34i.paheal-cdn.net/df/fb/video' type='video/mp4'></video>
<table><tr data-row='Uploader'><td><a class='username'>VHSephi</a>
<time datetime='2026-08-26T15:21:00+00:00'></time></td></tr>
<tr data-row='Tags'><td><a class='tag'>Amina</a><a class='tag'>animated</a>
<a class='tag'>Final_Fantasy_VII</a><a class='tag'>InitialA</a>
<a class='tag'>Tifa_Lockhart</a></td></tr>
<tr data-row='Source Link'><th><a href='/source_history/7428820'>Source</a></th>
<td><a href='https://subscribestar.adult/posts/2639932'>origin</a></td></tr>
<tr data-row='Info'><td>1280x720, 28.4s // 6.3MB // mp4</td></tr></table>"""


def _routed(route):
    """按 URL 分派的测试传输。探测详情页的请求要能和列表请求分开回不同的响应。"""
    def call(request, timeout, max_bytes):
        return route(request)
    return call


class Rule34PahealConnectorTests(unittest.TestCase):
    def _connector(self):
        return Rule34PahealConnector(transport=_routed(
            lambda request: HttpResponse(
                200, {}, PAHEAL_DETAIL_HTML if "/post/view/" in request.url
                else PAHEAL_LIST_HTML)))

    def test_tag_page_uses_detail_source_for_exact_cross_site_grouping(self):
        result = self._connector().fetch("initiala")
        self.assertEqual(len(result.candidates), 1)
        item = result.candidates[0]
        self.assertEqual(item.external_id, "7428820")
        self.assertEqual(item.group_hint, "subscribestar:2639932")
        self.assertEqual(item.duration, 28.4)
        self.assertEqual(item.published_at, "2026-08-26T15:21:00Z")
        self.assertEqual(item.media_url,
                         "https://r34i.paheal-cdn.net/df/fb/video")
        self.assertFalse(item.title_is_name)


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

    def test_archive_posts_get_a_cover_thumbnail(self):
        """归档站的卡片以前一律没有封面——不是取不到，是压根没去取。

        2026-08-27 实测 `https://kemono.cr/thumbnail/data<path>` 回 200 `image/jpeg`；
        去掉 `thumbnail/` 前缀则是 404，所以这个前缀是必需的。
        """
        result = KemonoConnector(transport=_transport(body=KEMONO_POSTS)).fetch("fanbox/1")
        self.assertEqual(result.candidates[0].thumb_url,
                         "https://kemono.cr/thumbnail/data/1c/fa/1cfae7.png")

    def test_archive_video_uses_an_image_attachment_as_its_cover(self):
        """主资源是视频/压缩包时，后附的图片仍然是可用封面。"""
        posts = [{
            "id": "cover-after-video", "title": "Animation pack",
            "published": "2026-08-27T00:00:00Z",
            "file": {"path": "/video/release.mp4"},
            "attachments": [
                {"path": "/video/notes.txt"},
                {"path": "/cover/release.webp"},
            ],
        }]
        result = KemonoConnector(
            transport=_transport(body=json.dumps(posts).encode())).fetch("fanbox/1")
        candidate = result.candidates[0]
        self.assertEqual(candidate.media_url, "https://kemono.cr/video/release.mp4")
        self.assertEqual(candidate.thumb_url,
                         "https://kemono.cr/thumbnail/data/cover/release.webp")

    def test_no_thumbnail_is_offered_for_things_that_have_none(self):
        # 视频和压缩包没有缩略图，给了也是 404——那会让卡片显示一张碎图，
        # 比一个干净的占位更糟。
        connector = KemonoConnector()
        self.assertIsNone(connector._thumb_url("/a/b/clip.mp4"))
        self.assertIsNone(connector._thumb_url("/a/b/pack.zip"))
        self.assertIsNone(connector._thumb_url(None))

    def test_a_post_that_only_links_a_file_host_is_a_release(self):
        """用户定的判据：资源贴要么贴附件，要么附上网盘链接。

        只做图的作者也算——一张图片附件就够，不要求压缩包或视频。
        """
        posts = json.loads(KEMONO_POSTS)
        posts.append({"id": "777", "title": "Monthly pack",
                      "published": "2026-02-01T00:00:00", "file": {}, "attachments": [],
                      "substring": "gofile - https://gofile.io/d/xyz"})
        result = KemonoConnector(
            transport=_transport(body=json.dumps(posts).encode())).fetch("fanbox/1")
        self.assertIn("777", [c.external_id for c in result.candidates])
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.probed, 0, "摘要里就能判出来，不该多打一次站点")

    def test_a_post_it_cannot_judge_is_probed_not_guessed(self):
        """列表判不出来时去抓详情，而不是猜。

        列表接口只给 `substring`（正文摘要），网盘链接常常在摘要之外。判不出来直接
        当「不是 release」会删掉真东西，当「是」又等于没过滤——所以判据是三态，
        只有第三种答案才允许下一步联网。
        """
        posts = json.loads(KEMONO_POSTS)
        posts.append({"id": "888", "title": "March pack", "published": "2026-03-01T00:00:00",
                      "file": {}, "attachments": [], "substring": "Here you go"})
        detail = json.dumps({"post": {"id": "888",
                                      "content": "<p>https://mega.nz/folder/abc</p>"}}).encode()
        bodies = {"posts": json.dumps(posts).encode(), "post/888": detail}

        def route(request):
            for key, body in bodies.items():
                if request.url.endswith(key):
                    return HttpResponse(200, {}, body)
            raise AssertionError(f"未预期的请求：{request.url}")

        result = KemonoConnector(transport=_routed(route)).fetch("fanbox/1")
        self.assertIn("888", [c.external_id for c in result.candidates])
        self.assertEqual(result.probed, 1)

    def test_a_post_with_no_resource_at_all_is_dropped(self):
        """公告、感谢这类帖子既没有附件也没有网盘链接，抓了详情之后确认丢掉。"""
        posts = json.loads(KEMONO_POSTS)
        posts.append({"id": "999", "title": "Thanks for 10k followers!",
                      "published": "2026-02-01T00:00:00", "file": {}, "attachments": [],
                      "substring": "You are all wonderful"})
        detail = json.dumps({"post": {"id": "999",
                                      "content": "<p>See you next month</p>"}}).encode()

        def route(request):
            if request.url.endswith("post/999"):
                return HttpResponse(200, {}, detail)
            return HttpResponse(200, {}, json.dumps(posts).encode())

        result = KemonoConnector(transport=_routed(route)).fetch("fanbox/1")
        self.assertEqual(result.skipped, 1)
        self.assertNotIn("999", [c.external_id for c in result.candidates])

    def test_an_unreachable_probe_keeps_the_post(self):
        """抓不到详情就保留。

        网络抖一下就删掉用户的一份更新，是拿一次失败的请求换一次不可见的数据丢失。
        探测额度用完时同理——额度是内部限额，不该变成删数据的理由。
        """
        posts = json.loads(KEMONO_POSTS)
        posts.append({"id": "555", "title": "April pack", "published": "2026-04-01T00:00:00",
                      "file": {}, "attachments": [], "substring": "Here"})

        def route(request):
            if "post/555" in request.url:
                return HttpResponse(503, {}, b"")
            return HttpResponse(200, {}, json.dumps(posts).encode())

        result = KemonoConnector(transport=_routed(route)).fetch("fanbox/1")
        self.assertIn("555", [c.external_id for c in result.candidates])

        # 额度为 0 时不联网，也不删。
        offline = KemonoConnector(max_probes=0,
                                  transport=_transport(body=json.dumps(posts).encode()))
        kept = offline.fetch("fanbox/1")
        self.assertIn("555", [c.external_id for c in kept.candidates])
        self.assertEqual(kept.probed, 0)

    def test_a_release_named_after_a_poll_is_still_a_release(self):
        """**不要按标题关键词丢投票贴。**

        2026-08-27 拿 LazyProcrastinator 的真实 50 条跑过一版
        `poll|vote|survey|…` 正则，丢掉 18 条，其中包括
        `Public Poll Release + Littlest Ramble`、`October Poll Animations Released`
        ——这位作者的正片就是按投票结果命名的。列表接口不给帖子类型字段，
        标题不足以区分「投票贴」和「投票选出的成品」，误删一份 release
        比多出一张卡片糟糕得多。这条测试就是为了挡住那个正则再被加回来。
        """
        posts = json.loads(KEMONO_POSTS)
        posts[0] = {**posts[0], "id": "777",
                    "title": "Public Poll Release + Littlest Ramble"}
        result = KemonoConnector(
            transport=_transport(body=json.dumps(posts).encode())).fetch("fanbox/1")
        self.assertIn("777", [c.external_id for c in result.candidates])
        self.assertEqual(result.skipped, 0)

    def test_paging_back_uses_an_offset_and_drops_the_conditional_headers(self):
        """往回翻要换页，而且**不能带条件请求头**。

        `If-None-Match` 里存的是第一页的 etag。拿它去问第二页，站点很可能回 304，
        用户点了「抓更早的」却什么都没发生——而且看起来和「确实没有更早的了」
        一模一样。

        2026-08-27 实测：kemono 的列表接口一页 50 条，`?o=50` 拿到的是第 51 条起，
        与第一页零重叠。
        """
        seen = []
        connector = KemonoConnector(
            transport=_transport(body=KEMONO_POSTS, record=seen))
        connector.fetch("fanbox/30917150", etag='"k1"', last_modified="then", page=2)
        self.assertEqual(seen[0].url,
                         "https://kemono.cr/api/v1/fanbox/user/30917150/posts?o=100")
        self.assertNotIn("If-None-Match", seen[0].headers)
        self.assertNotIn("If-Modified-Since", seen[0].headers)

    def test_the_first_page_still_sends_conditional_headers(self):
        # 常规检查必须保留条件请求：追更每天都在跑，没变就不该把整页再传一遍。
        seen = []
        KemonoConnector(transport=_transport(body=KEMONO_POSTS, record=seen)).fetch(
            "fanbox/30917150", etag='"k1"')
        self.assertEqual(seen[0].headers.get("If-None-Match"), '"k1"')
        self.assertNotIn("?o=", seen[0].url)

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

    def test_detail_enrichment_adds_full_cover_video_date_and_content_tags(self):
        seen = []

        def transport(request, timeout, max_bytes):
            seen.append(request.url)
            body = (RULE34VIDEO_HTML if "/models/" in request.url
                    else RULE34VIDEO_DETAIL_HTML)
            return HttpResponse(200, {}, body)

        result = Rule34VideoConnector(transport=transport).fetch("lazyprocrastinator")
        first = result.candidates[0]
        self.assertEqual(result.probed, 2)
        self.assertEqual(first.published_at, "2026-08-18T00:00:00Z")
        self.assertEqual(first.extra["published_precision"], "exact")
        self.assertEqual(first.duration, 433.0)
        self.assertEqual(first.extra["tags"], ["deep throat", "breast squeeze"])
        self.assertEqual(first.extra["categories"], ["3D", "Final Fantasy"])
        self.assertEqual(first.extra["tag_types"]["3D"], "metadata")
        self.assertEqual(first.extra["tag_types"]["Final Fantasy"], "copyright")
        self.assertTrue(first.thumb_url.endswith("/preview.jpg"))
        self.assertIn("4542721_360.mp4", first.media_url)

    def test_detail_with_many_credited_models_is_not_collected(self):
        models = "".join(
            f'<a class="item btn_link video_meta_pill" href="https://rule34video.com/models/m{n}/">M{n}</a>'
            for n in range(21)
        ).encode()
        detail = RULE34VIDEO_DETAIL_HTML.replace(b"</body>", models + b"</body>")

        def transport(request, timeout, max_bytes):
            return HttpResponse(200, {},
                                RULE34VIDEO_HTML if "/models/" in request.url else detail)

        result = Rule34VideoConnector(transport=transport).fetch("lazyprocrastinator")
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.skipped, 2)
        self.assertEqual(result.skipped_compilations, 2)


class PagingBackTests(unittest.TestCase):
    """各站往回翻的地址形状。都是 2026-08-27 实测过的端点。"""

    def test_rule34video_uses_the_async_block_endpoint(self):
        # KVS 的分页是异步块请求，`from` 是 1 起的两位页码。实测第 2 页 24 条、
        # 与第 1 页零重叠。
        seen = []
        Rule34VideoConnector(
            transport=_transport(body=RULE34VIDEO_HTML, record=seen)).fetch(
                "lazyprocrastinator", page=1)
        self.assertIn("mode=async", seen[0].url)
        self.assertIn("block_id=custom_list_videos_common_videos", seen[0].url)
        self.assertIn("from=02", seen[0].url)

    def test_rule34xxx_uses_pid_and_still_keeps_the_key_out_of_the_evidence_url(self):
        credential = Credential("rule34xxx", {"user_id": "1", "api_key": "secret"})
        seen = []
        result = Rule34XxxConnector(
            credential=credential,
            transport=_transport(body=RULE34XXX_JSON, record=seen)).fetch(
                "lazyprocrastinator", page=3)
        self.assertIn("pid=3", seen[0].url)
        # 脱敏后的 URL 进证据档案，凭据永远不能出现在那里。
        self.assertIn("pid=3", result.request_url)
        self.assertNotIn("secret", result.request_url)
        self.assertNotIn("api_key", result.request_url)


class F95ZoneConnectorTests(unittest.TestCase):
    @staticmethod
    def _masked_transport(record):
        def call(request, timeout, max_bytes):
            record.append(request)
            if request.method == "GET":
                return HttpResponse(200, {}, F95_HTML)
            return HttpResponse(200, {}, json.dumps({
                "status": "ok", "msg": "https://gofile.io/d/oOdYTK",
            }).encode())
        return call

    def test_latest_page_yields_replies_not_just_the_opening_post(self):
        seen = []
        result = F95ZoneConnector(
            transport=_transport(body=F95_HTML, record=seen)).fetch("50685")
        self.assertEqual(seen[0].url, "https://f95zone.to/threads/50685/latest")
        self.assertEqual(result.semantics, "release")
        self.assertEqual([c.external_id for c in result.candidates],
                         ["21383374", "21400001"])
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.candidates[0].author, "Jkhomie1198")
        self.assertEqual(result.candidates[0].published_at, "2026-08-21T04:14:09Z")

    def test_thread_title_drops_prefix_labels_and_keeps_the_version(self):
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        title = result.candidates[0].title
        self.assertTrue(title.startswith("Lazy Procrastinator Collection"))
        self.assertNotIn("F95zone", title)
        self.assertIn("[2026-06-28]", title)

    def test_quoted_links_and_discussion_only_replies_are_skipped(self):
        # 引用块里的链接是被引用那层发的。不剥掉会把追更信号指向错误的楼层。
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        self.assertNotIn("21394555", [row.external_id for row in result.candidates])
        self.assertEqual(result.skipped, 1)

    def test_reply_with_an_attachment_is_kept_and_gets_a_thumbnail(self):
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        candidate = result.candidates[1]
        self.assertEqual(candidate.external_id, "21400001")
        self.assertEqual(candidate.thumb_url,
                         "https://attachments.f95zone.to/2026/08/6372325_preview.png")
        self.assertEqual(candidate.extra["attachment_count"], 1)
        self.assertEqual(candidate.extra["attachments"], [
            "https://attachments.f95zone.to/2026/08/6372325_preview.png",
        ])

    def test_media_is_flagged_as_needing_a_login_session(self):
        # 发现不需要 cookie，取附件需要。下载动作必须先看这个标志。
        result = F95ZoneConnector(transport=_transport(body=F95_HTML)).fetch("50685")
        self.assertTrue(result.candidates[0].extra["media_needs_credential"])

    def test_cookie_resolves_masked_media_without_leaking_to_the_file_host(self):
        seen = []
        result = F95ZoneConnector(
            transport=self._masked_transport(seen),
            credential=Credential("f95zone", {"cookie": "xf=1"}),
        ).fetch("50685")
        candidate = result.candidates[0]
        self.assertEqual(candidate.media_url, "https://gofile.io/d/oOdYTK")
        self.assertEqual(candidate.extra["links"], ["https://gofile.io/d/oOdYTK"])
        self.assertFalse(candidate.extra["media_needs_credential"])
        self.assertEqual([request.method for request in seen], ["GET", "POST"])
        self.assertEqual(seen[1].url,
                         "https://f95zone.to/masked/gofile.io/50685/abc")
        self.assertEqual(seen[1].headers["Cookie"], "xf=1")
        self.assertEqual(seen[1].body, b"xhr=1&download=1")
        self.assertFalse(any("gofile.io/d/" in request.url for request in seen))

    def test_non_file_links_do_not_turn_a_reply_into_media(self):
        body = F95_HTML.replace(
            b"https://f95zone.to/masked/gofile.io/50685/abc",
            b"https://example.com/creator",
        )
        result = F95ZoneConnector(transport=_transport(body=body)).fetch("50685")
        self.assertEqual([row.external_id for row in result.candidates], ["21400001"])
        self.assertEqual(result.skipped, 2)

    def test_a_valid_page_with_only_discussion_returns_an_empty_fetch(self):
        body = F95_HTML.replace(
            b"https://f95zone.to/masked/gofile.io/50685/abc",
            b"https://example.com/creator",
        ).replace(
            b'<article data-content="post-21400001"',
            b'<article data-content="comment-21400001"',
        )
        result = F95ZoneConnector(transport=_transport(body=body)).fetch("50685")
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.skipped, 2)

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

    def test_an_empty_success_response_means_the_tag_has_no_posts(self):
        # rule34.xxx 的零命中响应是 HTTP 200 + 空正文，不是 JSON `[]`。
        # 不能把普通的「搜不到」显示成红色 JSON 错误。
        result = self._connector(body=b" \r\n").fetch("not-a-real-tag")
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.raw_body, b" \r\n")

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
            "https://rule34.paheal.net/post/view/7428820#search=InitialA":
                ("rule34paheal", "initiala"),
            "https://f95zone.to/threads/lazy-collection.50685/": ("f95zone", "50685"),
            "https://ffxivinitiala.fanbox.cc/posts/12489354":
                ("fanbox", "ffxivinitiala"),
            "https://www.fanbox.cc/@ffxivinitiala/posts/12489354":
                ("fanbox", "ffxivinitiala"),
            "https://subscribestar.adult/initiala":
                ("subscribestar", "subscribestar.adult/initiala"),
            "https://www.patreon.com/cw/somnivagrious":
                ("patreon", "somnivagrious"),
            "https://www.patreon.com/user?u=12345": ("patreon", "user/12345"),
        }
        for url, expected in cases.items():
            parsed = parse_source_url(url)
            self.assertEqual((parsed.provider, parsed.ref), expected, url)

    def test_a_deep_link_is_narrowed_to_the_creator(self):
        parsed = parse_source_url("https://kemono.cr/fanbox/user/30917150/post/11406814")
        self.assertEqual(parsed.ref, "fanbox/30917150")
        self.assertEqual(parsed.url, "https://kemono.cr/fanbox/user/30917150")

    def test_rule34_tags_use_one_case_insensitive_identity(self):
        upper = parse_source_url(
            "https://rule34.xxx/index.php?page=post&s=list&tags=LazyProcrastinator")
        lower = parse_source_url(
            "https://rule34.xxx/index.php?page=post&s=list&tags=lazyprocrastinator")
        self.assertEqual(upper.ref, "lazyprocrastinator")
        self.assertEqual(upper, lower)

    def test_threads_get_release_semantics_and_others_get_work(self):
        self.assertEqual(parse_source_url("https://f95zone.to/threads/x.1/").semantics,
                         "release")
        self.assertEqual(
            parse_source_url("https://rule34video.com/models/abc/").semantics, "work")
        self.assertEqual(parse_source_url("https://creator.fanbox.cc/").semantics,
                         "work")

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
            ("https://rule34.paheal.net/post/view/7428820", "搜索标签"),
            ("https://f95zone.to/latest", "threads"),
            ("https://www.fanbox.cc/", "创作者主页"),
            ("https://subscribestar.adult/posts/1", "创作者主页"),
            ("https://www.patreon.com/posts/123", "创作者主页"),
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

    def test_official_channel_connectors_are_registered(self):
        self.assertIsInstance(build_connector("fanbox"), FanboxConnector)
        self.assertIsInstance(build_connector("patreon"), PatreonConnector)
        self.assertIsInstance(build_connector("subscribestar"), SubscribeStarConnector)
        self.assertIsInstance(build_connector("rule34paheal"), Rule34PahealConnector)


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
        self.assertIn(described["world_readable"], (False, None))

    @unittest.skipIf(os.name == "nt", "NTFS 走 ACL，st_mode 的组/其他读位恒为真")
    def test_group_or_world_readable_permissions_are_reported(self):
        self._write("f95zone", {"cookie": "xf=1"}, mode=0o644)
        self.assertTrue(self.store.describe("f95zone")["world_readable"])

    @unittest.skipUnless(os.name == "nt", "只在 Windows 上成立")
    def test_windows_reports_unknown_rather_than_a_meaningless_permission(self):
        self._write("f95zone", {"cookie": "xf=1"})
        self.assertIsNone(self.store.describe("f95zone")["world_readable"])

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
