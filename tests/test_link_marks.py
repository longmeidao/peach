"""外链圆标：只在有把握时上色，其余原样放行。"""
import io
import sys
import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import link_marks   # noqa: E402


def ico(pixels, size=32, mode="RGBA"):
    image = Image.new(mode, (size, size), (0, 0, 0, 0) if mode == "RGBA" else (255, 255, 255))
    painter = image.load()
    for (x, y), colour in pixels.items():
        painter[x, y] = colour
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def glyph(colour, size=32, opaque_background=None):
    """中间一块实心方块当字形；`opaque_background` 不为 None 时整张图不透明。"""
    pixels = {}
    if opaque_background is not None:
        for x in range(size):
            for y in range(size):
                pixels[(x, y)] = opaque_background + (255,)
    for x in range(8, 24):
        for y in range(8, 24):
            pixels[(x, y)] = colour + (255,)
    return ico(pixels, size)


class RenderTests(unittest.TestCase):
    def test_a_single_colour_glyph_with_transparency_is_recoloured(self):
        """T-POWERS 就是这个形态：48×48、带透明、不透明像素只有一种绿。

        alpha 直接就是遮罩，所以能稳稳做出「品牌色底 + 白色主体」。
        """
        made = link_marks.render_mark(glyph((72, 168, 24)))
        self.assertIsNotNone(made)
        image = Image.open(io.BytesIO(made)).convert("RGBA")
        self.assertEqual(image.size, (link_marks.MARK_SIZE, link_marks.MARK_SIZE))
        centre = image.getpixel((image.width // 2, image.height // 2))
        self.assertEqual(centre[:3], (255, 255, 255), "主体应当是白的")
        edge = image.getpixel((image.width // 2, 3))
        self.assertGreater(edge[1], edge[0], "圆底应当是那个绿")

    def test_an_opaque_favicon_is_left_alone(self):
        """HEYZO 是白底 + 多色字形。

        全不透明时只能拿四角猜主体，实测这条路会把白字反转成一团糟——
        半吊子的抠图比原图更难看，所以直接不做。
        """
        self.assertIsNone(link_marks.render_mark(glyph((240, 0, 96), opaque_background=(240, 240, 240))))

    def test_a_multi_hue_glyph_is_left_alone(self):
        """多色 logo 没有单一品牌色可取，硬取会挑出其中一块，看起来像认错了牌子。"""
        pixels = {}
        for x in range(8, 24):
            for y in range(8, 24):
                pixels[(x, y)] = ((240, 0, 0, 255) if x < 12 else
                                  (0, 200, 0, 255) if x < 16 else
                                  (0, 0, 240, 255) if x < 20 else (240, 200, 0, 255))
        self.assertIsNone(link_marks.render_mark(ico(pixels)))

    def test_a_broken_image_yields_nothing_instead_of_raising(self):
        """MOODYZ 的 favicon 根本不是有效图片。

        端点在页面加载时被调用，抛异常会变成 500；返回 None 让它回落到地球图标。
        """
        self.assertIsNone(link_marks.render_mark(b"<html>not an image</html>"))
        self.assertIsNone(link_marks.plain_mark(b"<html>not an image</html>"))

    def test_the_fallback_still_produces_a_png_at_the_mark_size(self):
        made = link_marks.plain_mark(glyph((240, 0, 96), opaque_background=(240, 240, 240)))
        self.assertIsNotNone(made)
        self.assertEqual(Image.open(io.BytesIO(made)).size,
                         (link_marks.MARK_SIZE, link_marks.MARK_SIZE))


class CacheTests(unittest.TestCase):
    def test_the_cache_key_is_per_host_not_per_link(self):
        """同一个站的每条链接共用一枚图标；按完整地址缓存会为同一张图存几十份。"""
        self.assertEqual(link_marks.cache_key("https://www.t-powers.co.jp/talent/a/"),
                         link_marks.cache_key("http://t-powers.co.jp/talent/b/"))
        self.assertNotEqual(link_marks.cache_key("https://t-powers.co.jp/"),
                            link_marks.cache_key("https://x.com/"))

    def test_a_url_without_a_host_has_no_cache_key(self):
        self.assertEqual(link_marks.cache_key("not a url"), "")
        self.assertIsNone(link_marks.cached_path(Path("/tmp"), "not a url"))

    def test_freshness_expires_and_a_missing_file_is_never_fresh(self):
        tmp = Path(tempfile.mkdtemp()) / "mark.png"
        self.assertFalse(link_marks.is_fresh(tmp))
        tmp.write_bytes(b"x")
        self.assertTrue(link_marks.is_fresh(tmp))
        self.assertFalse(link_marks.is_fresh(
            tmp, now=time.time() + link_marks.CACHE_TTL + 1))


if __name__ == "__main__":
    unittest.main()
