"""作者头像与来源图标的本地缓存：地址只从固定表拼、字节先认成图再落盘、到期重取失败继续用旧的。"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import follow_assets   # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
ICO = b"\x00\x00\x01\x00\x01\x00" + b"\x00" * 24
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 16
SVG = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"/>'
HTML = b"<!doctype html><html><body>Just a moment...</body></html>"


class SniffTests(unittest.TestCase):
    def test_common_icon_and_avatar_formats_are_recognised(self):
        self.assertEqual(follow_assets.sniff(PNG), "image/png")
        self.assertEqual(follow_assets.sniff(b"\xff\xd8\xff\xe0" + b"\x00" * 8), "image/jpeg")
        self.assertEqual(follow_assets.sniff(ICO), "image/x-icon")
        self.assertEqual(follow_assets.sniff(WEBP), "image/webp")
        self.assertEqual(follow_assets.sniff(SVG), "image/svg+xml")
        self.assertEqual(follow_assets.sniff(b"GIF89a" + b"\x00" * 8), "image/gif")

    def test_challenge_pages_and_empty_bodies_are_not_images(self):
        """站点回的机器人质询页是 HTML，落盘了就是一枚永远碎的图标。"""
        self.assertIsNone(follow_assets.sniff(HTML))
        self.assertIsNone(follow_assets.sniff(b""))
        self.assertIsNone(follow_assets.sniff(b'{"error":"blocked"}'))


class CachePathTests(unittest.TestCase):
    def test_paths_are_stable_and_separated_by_kind(self):
        root = Path("/cache")
        first = follow_assets.cache_path(root, "avatars", "mirror:kemono:fanbox/1")
        self.assertEqual(first, follow_assets.cache_path(root, "avatars", "mirror:kemono:fanbox/1"))
        self.assertEqual(first.parent, root / "avatars")
        self.assertNotEqual(first, follow_assets.cache_path(root, "icons", "mirror:kemono:fanbox/1"))
        self.assertTrue(re.fullmatch(r"[0-9a-f]{32}\.img", first.name), first.name)

    def test_never_refresh_means_a_present_file_is_always_fresh(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.img"
            self.assertFalse(follow_assets.is_fresh(path, None))
            path.write_bytes(PNG)
            modified = path.stat().st_mtime
            self.assertTrue(follow_assets.is_fresh(path, None, now=modified + 10 ** 9))
            self.assertTrue(follow_assets.is_fresh(path, 100, now=modified + 99))
            self.assertFalse(follow_assets.is_fresh(path, 100, now=modified + 100))


class CachedImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.calls = 0
        self.body = PNG

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self):
        self.calls += 1
        return self.body

    def test_the_first_request_fetches_and_later_ones_use_the_file(self):
        path = follow_assets.cached_image(self.root, "icons", "kemono", 3600, self.fetch)
        self.assertEqual(path.read_bytes(), PNG)
        self.assertEqual(follow_assets.content_type(path), "image/png")
        again = follow_assets.cached_image(self.root, "icons", "kemono", 3600, self.fetch)
        self.assertEqual(again, path)
        self.assertEqual(self.calls, 1, "新鲜的缓存不该再出网")

    def test_an_expired_file_is_refetched_and_replaced(self):
        path = follow_assets.cached_image(self.root, "icons", "kemono", 3600, self.fetch)
        modified = path.stat().st_mtime
        self.body = ICO
        refreshed = follow_assets.cached_image(
            self.root, "icons", "kemono", 3600, self.fetch, now=modified + 3600)
        self.assertEqual(refreshed.read_bytes(), ICO)
        self.assertEqual(self.calls, 2)

    def test_a_failed_refresh_keeps_the_old_image_and_backs_off(self):
        """站点挂了不能满屏碎图，也不能每次重绘都去打它几十枪。"""
        path = follow_assets.cached_image(self.root, "icons", "kemono", 3600, self.fetch)
        modified = path.stat().st_mtime
        self.body = None
        stale = follow_assets.cached_image(
            self.root, "icons", "kemono", 3600, self.fetch, now=modified + 3600)
        self.assertEqual(stale, path)
        self.assertEqual(stale.read_bytes(), PNG, "旧图要留着")
        self.assertEqual(self.calls, 2)
        soon = follow_assets.cached_image(
            self.root, "icons", "kemono", 3600, self.fetch,
            now=modified + 3600 + follow_assets.RETRY_SECONDS - 1)
        self.assertEqual(soon, path)
        self.assertEqual(self.calls, 2, "退避期内不再出网")
        self.body = ICO
        later = follow_assets.cached_image(
            self.root, "icons", "kemono", 3600, self.fetch,
            now=modified + 3600 + follow_assets.RETRY_SECONDS + 1)
        self.assertEqual(later.read_bytes(), ICO)
        self.assertEqual(self.calls, 3)
        self.assertFalse(path.with_suffix(".failed").exists(), "成功后清掉失败标记")

    def test_never_fetched_and_unreachable_is_none_until_the_backoff_passes(self):
        self.body = None
        self.assertIsNone(follow_assets.cached_image(self.root, "icons", "kemono", 3600, self.fetch))
        self.assertIsNone(follow_assets.cached_image(self.root, "icons", "kemono", 3600, self.fetch))
        self.assertEqual(self.calls, 1, "第一次失败后退避期内不再试")

    def test_never_refresh_serves_the_file_forever(self):
        path = follow_assets.cached_image(self.root, "icons", "kemono", None, self.fetch)
        modified = path.stat().st_mtime
        follow_assets.cached_image(self.root, "icons", "kemono", None, self.fetch,
                                   now=modified + 10 ** 9)
        self.assertEqual(self.calls, 1)


class FetchImageTests(unittest.TestCase):
    def _client(self, handler):
        return httpx.Client(transport=httpx.MockTransport(handler))

    def test_only_a_200_image_body_counts(self):
        seen = []

        def upstream(request):
            seen.append(request)
            status = int(request.url.params.get("status", "200"))
            body = {"png": PNG, "html": HTML, "big": b"\x89PNG\r\n\x1a\n" + b"\x00" * follow_assets.MAX_BYTES}[
                request.url.params.get("body", "png")]
            return httpx.Response(status, content=body, request=request,
                                  headers={"content-type": "image/png"})

        with self._client(upstream) as client:
            self.assertEqual(follow_assets.fetch_image(client, "https://icons.test/a"), PNG)
            self.assertIsNone(follow_assets.fetch_image(client, "https://icons.test/a?status=404"))
            self.assertIsNone(follow_assets.fetch_image(client, "https://icons.test/a?body=html"),
                              "content-type 说是图也不信，字节认不出就不是图")
            self.assertIsNone(follow_assets.fetch_image(client, "https://icons.test/a?body=big"))
        for request in seen:
            self.assertNotIn("cookie", {k.lower() for k in request.headers})
            self.assertNotIn("authorization", {k.lower() for k in request.headers})

    def test_network_errors_are_a_miss_not_a_crash(self):
        def upstream(request):
            raise httpx.ConnectError("down", request=request)

        with self._client(upstream) as client:
            self.assertIsNone(follow_assets.fetch_image(client, "https://icons.test/a"))


class MirrorAvatarTests(unittest.TestCase):
    def test_avatars_only_come_from_providers_that_actually_serve_one(self):
        """按 peach-reference-evidence：实测拿得到才给，取不到写「未取得」。

        2026-08-27 实测 `https://kemono.cr/icons/fanbox/30917150` → 302 →
        `img.kemono.cr`，200 `image/webp` 160×160；pawchive.pw 同路径 200。
        rule34 系没有可用样本可测，所以不给 URL——不猜一个路径。
        """
        self.assertEqual(follow_assets.mirror_avatar_url("kemono", "fanbox/30917150"),
                         "https://kemono.cr/icons/fanbox/30917150")
        self.assertEqual(follow_assets.mirror_avatar_url("pawchive", "fanbox/30917150"),
                         "https://pawchive.pw/icons/fanbox/30917150")
        for provider, ref in (("rule34video", "1290582"),
                              ("rule34xxx", "lazyprocrastinator"),
                              ("f95zone", "50685"),
                              ("kemono", "no-slash")):
            self.assertIsNone(follow_assets.mirror_avatar_url(provider, ref),
                              f"{provider} 没有实测过的头像来源，不该猜一个")


class SourceIconTableTests(unittest.TestCase):
    def test_icon_addresses_are_https_and_the_page_lists_the_same_providers(self):
        """页面只认名单、服务端只认地址：两边各写一份就会漂，漂了就是一格空白。"""
        for provider, url in follow_assets.SOURCE_ICON_URLS.items():
            self.assertTrue(url.startswith("https://"), (provider, url))
        page = (Path(__file__).resolve().parents[1] / "web" / "app.js").read_text(encoding="utf-8")
        raw = re.search(r"const SOURCE_ICON_PROVIDERS=new Set\(\[(.*?)\]\);", page, re.S).group(1)
        listed = {item.strip().strip("'") for item in raw.split(",") if item.strip()}
        self.assertEqual(listed, set(follow_assets.SOURCE_ICON_URLS))
        # 页面里不再有任何一条站点图标的远端地址：图标全部经 Peach 落盘后再给页面。
        self.assertNotIn("favicon.ico'", page)
        self.assertIn("src=\"/source-icon?provider=${encodeURIComponent(provider)}\"", page)


if __name__ == "__main__":
    unittest.main()
