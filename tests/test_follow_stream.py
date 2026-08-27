import unittest
from types import SimpleNamespace

from peach.follow_stream import FollowMediaResolver, FollowMediaUnavailable
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


if __name__ == "__main__":
    unittest.main()
