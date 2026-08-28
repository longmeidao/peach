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
