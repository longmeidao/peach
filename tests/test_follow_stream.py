import unittest
from types import SimpleNamespace

import httpx

from peach.follow_stream import (
    MAX_PROXY_REDIRECTS, FollowMediaResolver, FollowMediaUnavailable,
    FollowProxyError, ResolvedFollowMedia, open_upstream, proxy_request_headers,
    proxy_response_headers,
)
from peach.follow_secrets import Credential
from peach.http import HttpResponse


class FollowMediaResolverTests(unittest.TestCase):
    def test_rule34video_resolves_the_current_signed_url_and_caches_it(self):
        requests = []

        def transport(request, timeout, max_bytes):
            requests.append(request)
            return HttpResponse(200, {}, b"<script>video_url: 'https:\\/\\/rule34video.com\\/get_file\\/1.mp4\\/?v-acctoken=fresh'</script>")

        item = SimpleNamespace(
            id=7, provider="rule34video",
            url="https://rule34video.com/video/7/work/",
            media_url="https://rule34video.com/get_file/1.mp4/",
            metadata={},
        )
        resolver = FollowMediaResolver(transport)
        first = resolver.resolve(item)
        second = resolver.resolve(item)
        self.assertEqual(first, second)
        self.assertEqual(len(requests), 1)
        self.assertIn("v-acctoken=fresh", first.url)
        self.assertEqual(first.referer, item.url)

    def test_non_rule34_media_uses_the_recorded_source_without_a_network_probe(self):
        resolver = FollowMediaResolver(lambda *_args: self.fail("unexpected network probe"))
        item = SimpleNamespace(
            id=8, provider="kemono", url="https://kemono.cr/post/8",
            media_url="https://img.kemono.cr/data/8.mp4", metadata={},
        )
        self.assertEqual(resolver.resolve(item).url, item.media_url)

    def test_untrusted_or_credentialed_targets_are_rejected(self):
        resolver = FollowMediaResolver(lambda *_args: self.fail("unexpected network probe"))
        bad = SimpleNamespace(
            id=9, provider="kemono", url="https://kemono.cr/post/9",
            media_url="https://127.0.0.1/private.mp4", metadata={},
        )
        with self.assertRaises(FollowMediaUnavailable):
            resolver.resolve(bad)
        locked = SimpleNamespace(
            id=10, provider="f95zone", url="https://f95zone.to/post/10",
            media_url="https://f95zone.to/file.mp4",
            metadata={"media_needs_credential": True},
        )
        with self.assertRaises(FollowMediaUnavailable):
            resolver.resolve(locked)

    def test_fanbox_gallery_selects_an_image_by_index(self):
        item = SimpleNamespace(
            id=11, provider="fanbox", url="https://creator.fanbox.cc/posts/11",
            media_url=None, metadata={"media_items": [
                {"url": "https://downloads.fanbox.cc/one.jpg",
                 "resource_provider": "fanbox"},
                {"url": "https://downloads.fanbox.cc/two.jpg",
                 "resource_provider": "fanbox"},
            ]},
        )
        target = FollowMediaResolver(lambda *_args: None).resolve(item, 1)
        self.assertEqual(target.url, "https://downloads.fanbox.cc/two.jpg")

    def test_legacy_f95_attachment_is_resolved_as_an_image(self):
        item = SimpleNamespace(
            id=13, provider="f95zone", url="https://f95zone.to/threads/1/post-13",
            media_url="https://pixeldrain.com/l/files", metadata={"attachments": [
                "https://attachments.f95zone.to/2026/08/one.jpg",
            ]},
        )
        target = FollowMediaResolver(lambda *_args: None).resolve(item, 0)
        self.assertEqual(target.url,
                         "https://attachments.f95zone.to/2026/08/one.jpg")
        self.assertEqual(target.referer, item.url)

    def test_f95_attachment_stays_available_while_other_links_need_a_session(self):
        item = SimpleNamespace(
            id=14, provider="f95zone", url="https://f95zone.to/threads/1/post-14",
            media_url="https://f95zone.to/masked/gofile.io/1/locked",
            metadata={"media_needs_credential": True, "attachments": [
                "https://attachments.f95zone.to/2026/08/one.jpg",
            ]},
        )
        resolver = FollowMediaResolver(lambda *_args: None).with_credential_loader(
            lambda provider: Credential(provider, {"cookie": "xf_session=saved"}))
        target = resolver.resolve(item, 0)
        self.assertEqual(target.url,
                         "https://attachments.f95zone.to/2026/08/one.jpg")
        self.assertEqual(target.headers, {"Cookie": "xf_session=saved"})

    def test_gofile_media_keeps_the_token_in_the_proxy_header(self):
        item = SimpleNamespace(
            id=12, provider="fanbox", url="https://creator.fanbox.cc/posts/12",
            media_url=None, metadata={"media_items": [
                {"url": "https://store1.gofile.io/download/one.mp4",
                 "resource_provider": "gofile"},
            ]},
        )
        resolver = FollowMediaResolver(lambda *_args: None).with_credential_loader(
            lambda provider: Credential(provider, {"api_token": "secret"}))
        target = resolver.resolve(item, 0)
        self.assertEqual(target.headers, {"Authorization": "Bearer secret"})
        self.assertNotIn("secret", target.url)

    def test_the_resolution_cache_stays_bounded(self):
        """只有 rule34video 会进这个缓存，一次列表几百条；只按 TTL 过期的话，
        进程活多久它就长多久。"""
        def transport(request, timeout, max_bytes):
            return HttpResponse(200, {}, b"<script>video_url: "
                                b"'https://rule34video.com/get_file/1_720p.mp4/'</script>")

        resolver = FollowMediaResolver(transport, max_cache_entries=2)
        for identifier in range(6):
            resolver.resolve(SimpleNamespace(
                id=identifier, provider="rule34video",
                url=f"https://rule34video.com/video/{identifier}/x/",
                media_url=None, metadata={}))
        self.assertEqual(len(resolver._cache), 2)


class Rule34VideoQualityTests(unittest.TestCase):
    """rule34video 把每档清晰度写成独立字段，只解析 video_url 会永远播最低那档。

    2026-08-31 实测 video/4564733 的页面给出四档：

        video_url      -> 4564733_360.mp4
        video_alt_url  -> 4564733_480p.mp4
        video_alt_url2 -> 4564733_720p.mp4
        video_alt_url3 -> 4564733_1080p.mp4
    """

    PAGE = (b"<script>"
            b"video_url: 'https://rule34video.com/get_file/51/a/1/1_360.mp4/?v-acctoken=t0';"
            b"video_alt_url: 'https://rule34video.com/get_file/51/a/1/1_480p.mp4/?v-acctoken=t1';"
            b"video_alt_url2: 'https://rule34video.com/get_file/51/a/1/1_720p.mp4/?v-acctoken=t2';"
            b"video_alt_url3: 'https://rule34video.com/get_file/51/a/1/1_1080p.mp4/?v-acctoken=t3';"
            b"</script>")

    def _resolver(self, body=None):
        def transport(request, timeout, max_bytes):
            return HttpResponse(200, {}, self.PAGE if body is None else body)
        return FollowMediaResolver(transport)

    def _item(self):
        return SimpleNamespace(
            id=11, provider="rule34video",
            url="https://rule34video.com/video/11/x/",
            media_url="https://rule34video.com/get_file/1.mp4/",
            metadata={},
        )

    def test_every_quality_is_parsed_and_the_highest_plays_by_default(self):
        resolved = self._resolver().resolve(self._item())
        self.assertEqual([height for height, _ in resolved.qualities],
                         [1080, 720, 480, 360])
        self.assertIn("1_1080p.mp4", resolved.url,
                      "默认应当是最高一档，旧实现固定播 360")

    def test_a_requested_height_is_honoured(self):
        resolved = self._resolver().resolve(self._item(), None, 480)
        self.assertIn("1_480p.mp4", resolved.url)

    def test_an_unavailable_height_falls_back_instead_of_failing(self):
        """签名 URL 会过期、来源也会改版；选档失败不该中断播放。"""
        resolved = self._resolver().resolve(self._item(), None, 4320)
        self.assertIn("1_1080p.mp4", resolved.url)

    def test_other_providers_report_no_quality_choices(self):
        item = SimpleNamespace(
            id=12, provider="pawchive",
            url="https://pawchive.pw/x",
            media_url="https://pawchive.pw/data/a/b/c.mp4",
            metadata={},
        )
        resolved = self._resolver(body=b"").resolve(item)
        self.assertEqual(resolved.qualities, (),
                         "只有 rule34video 给多档，其余来源只显示原画")


class ProxyUpstreamTests(unittest.TestCase):
    """`/follow-stream` 的代理边界：跟哪些跳、转发哪些头、什么时候干脆不转发。

    生产用的那个 client 开着 `follow_redirects=True`，所以这里的替身也开着：
    要证明的正是「按跳自己判」而不是「靠 client 的默认值」。
    """

    def _client(self, handler):
        client = httpx.Client(transport=httpx.MockTransport(handler),
                              follow_redirects=True)
        self.addCleanup(client.close)
        return client

    def test_a_redirect_out_of_the_whitelist_never_carries_the_credential(self):
        """上游只要回一个指向别处的 Location，httpx 就会把 Cookie 一路带过去。"""
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(302, request=request, headers={
                "location": "https://collector.example/steal.jpg"})

        target = ResolvedFollowMedia(
            "https://attachments.f95zone.to/2026/08/one.jpg",
            "https://f95zone.to/threads/1/post-1",
            {"Cookie": "xf_session=fixture"},
            allowed_hosts=("attachments.f95zone.to",))
        with self.assertRaises(FollowProxyError):
            open_upstream(self._client(handler), "GET", target, incoming={})
        self.assertEqual([str(request.url) for request in seen],
                         ["https://attachments.f95zone.to/2026/08/one.jpg"],
                         "出界的那一跳一次都不能发出去")
        self.assertEqual(seen[0].headers["cookie"], "xf_session=fixture",
                         "第一跳确实带着会话，所以拦住的是真的泄露")

    def test_a_redirect_inside_the_source_domain_is_still_followed(self):
        """归档站主域会 302 到取文件的节点（实测 kemono → n1.），必须跟得上。"""

        def handler(request):
            if request.url.host == "kemono.cr":
                return httpx.Response(302, request=request, headers={
                    "location": "https://n1.kemono.cr/data/7.mp4"})
            return httpx.Response(200, request=request,
                                  stream=httpx.ByteStream(b"frames"),
                                  headers={"content-type": "video/mp4"})

        target = ResolvedFollowMedia("https://kemono.cr/data/7.mp4",
                                     allowed_hosts=("kemono.cr",))
        upstream = open_upstream(self._client(handler), "GET", target, incoming={})
        self.addCleanup(upstream.close)
        self.assertEqual(upstream.read(), b"frames")

    def test_rule34video_is_followed_out_to_its_cdn(self):
        """rule34video 的 `/get_file/…` 只是签名入口，正片在 `*.boomio-cdn.com`。

        这一跳没有凭据可泄露（这条媒体不带 `headers`），拦住它的唯一后果是每条
        视频都停在 502。CDN 后缀登记在 `follow_providers` 的 `hosts` 里，代理照样
        逐跳校验。
        """

        def handler(request):
            if request.url.host == "rule34video.com":
                return httpx.Response(302, request=request, headers={
                    "location": "https://eu-cdn05-prem.boomio-cdn.com/x.mp4"})
            return httpx.Response(206, request=request,
                                  stream=httpx.ByteStream(b"frames"),
                                  headers={"content-type": "video/mp4"})

        target = ResolvedFollowMedia(
            "https://rule34video.com/get_file/1/1080p.mp4/?v-acctoken=fresh",
            "https://rule34video.com/video/1/work/",
            allowed_hosts=("rule34video.com", "boomio-cdn.com"))
        upstream = open_upstream(self._client(handler), "GET", target, incoming={})
        self.addCleanup(upstream.close)
        self.assertEqual(upstream.read(), b"frames")

    def test_an_upstream_error_page_is_refused_instead_of_forwarded(self):
        """403 页面、限流提示、错误 JSON 转发给播放器没有用处，只会把上游的
        主机名和提示语抄给浏览器。"""

        def handler(request):
            return httpx.Response(403, request=request,
                                  content=b"<html>blocked by upstream shield</html>")

        target = ResolvedFollowMedia("https://kemono.cr/data/7.mp4",
                                     allowed_hosts=("kemono.cr",))
        with self.assertRaises(FollowProxyError) as raised:
            open_upstream(self._client(handler), "GET", target, incoming={})
        self.assertIn("403", str(raised.exception))
        self.assertNotIn("shield", str(raised.exception))

    def test_a_redirect_loop_is_bounded(self):
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(302, request=request, headers={
                "location": "https://kemono.cr/data/next.mp4"})

        target = ResolvedFollowMedia("https://kemono.cr/data/7.mp4",
                                     allowed_hosts=("kemono.cr",))
        with self.assertRaises(FollowProxyError):
            open_upstream(self._client(handler), "GET", target, incoming={})
        self.assertEqual(len(seen), MAX_PROXY_REDIRECTS + 1)

    def test_media_without_a_whitelist_is_not_proxied_at_all(self):
        target = ResolvedFollowMedia("https://kemono.cr/data/7.mp4")
        with self.assertRaises(FollowProxyError):
            open_upstream(
                self._client(lambda request: self.fail("不该发出请求")),
                "GET", target, incoming={})

    def test_only_range_headers_come_in_and_only_media_headers_go_back(self):
        target = ResolvedFollowMedia(
            "https://kemono.cr/data/7.mp4", "https://kemono.cr/post/7",
            {"Cookie": "source_session=fixture"}, allowed_hosts=("kemono.cr",))
        headers = proxy_request_headers(target, {
            "range": "bytes=0-1", "accept": "video/*",
            # 浏览器发给 Peach 的凭据不能跟着请求送到上游去。
            "cookie": "peach=token", "authorization": "Bearer peach",
        })
        self.assertEqual(headers["Range"], "bytes=0-1")
        self.assertEqual(headers["Accept"], "video/*")
        self.assertEqual(headers["Referer"], "https://kemono.cr/post/7")
        self.assertEqual(headers["Cookie"], "source_session=fixture")
        self.assertNotIn("Authorization", headers)
        forwarded = proxy_response_headers({
            "content-type": "video/mp4", "content-length": "10",
            "set-cookie": "upstream=1", "server": "nginx",
        })
        self.assertEqual(forwarded, {"content-type": "video/mp4",
                                     "content-length": "10",
                                     "cache-control": "no-store"})
