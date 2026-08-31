import unittest
from types import SimpleNamespace

from peach.follow_stream import FollowMediaResolver, FollowMediaUnavailable
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


if __name__ == "__main__":
    unittest.main()


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
