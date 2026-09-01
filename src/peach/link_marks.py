"""外链图标：把站点 favicon 做成资料页上能看的一枚圆标。

用户指出资料页上的 favicon 不好看，并给了 beeg 的做法作参照——
`cdn.../tag_full/34.svg` 是一块品牌色实心底 + 白色 logo 路径。那是 beeg 逐个平台
手工做的 SVG；我们有八十多个不同主机，只能自动近似。

**只在有把握时才套这个处理。** 实测三种形态：

    T-POWERS   48×48，带透明通道，不透明像素只有一种绿   → alpha 就是现成遮罩，效果好
    HEYZO      32×32，全不透明，白底 + 品牌粉的多色字形   → 抠图会反转，出来一团糟
    MOODYZ     favicon 根本不是有效图片                  → 什么都做不了

所以判据是「单色字形 + 有真透明」。不满足就原样转出 favicon——半吊子的抠图比原图更难看。

服务端做还有两个附带好处：浏览器不再直接向对方站点发请求（不泄露正在看谁的资料页），
以及结果可以按主机缓存，不必每次开页都去取一遍。
"""
from __future__ import annotations

import colorsys
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import urlsplit

MARK_SIZE = 64
#: 主体像素的色相要多集中才算「单色字形」。实测 T-POWERS 是 1 簇，HEYZO 是 4 簇。
MAX_HUE_BUCKETS = 2
#: 透明像素要占到这么多，alpha 才算真的是遮罩而不是压缩噪点。
MIN_TRANSPARENT = 0.15
CACHE_TTL = 30 * 24 * 3600


def cache_key(url: str) -> str:
    """按主机缓存，不按完整地址——同一个站的每条链接共用一枚图标。"""
    host = (urlsplit(url).hostname or "").casefold().removeprefix("www.")
    return hashlib.sha256(host.encode("utf-8")).hexdigest()[:32] if host else ""


def _body_pixels(image):
    """返回 (主体坐标, 是否靠 alpha 判定的)。"""
    width, height = image.size
    pixels = image.load()
    transparent = sum(1 for y in range(height) for x in range(width)
                      if pixels[x, y][3] < 128)
    if transparent > MIN_TRANSPARENT * width * height:
        return [(x, y) for y in range(height) for x in range(width)
                if pixels[x, y][3] >= 128], True
    # 全不透明时只能拿四角当底色去猜主体。实测这条路在多色 logo 上会反转，
    # 所以它的结果不参与「有把握」的判定，只用来兜底。
    corners = [pixels[0, 0], pixels[width - 1, 0],
               pixels[0, height - 1], pixels[width - 1, height - 1]]
    background = tuple(sum(corner[i] for corner in corners) // 4 for i in range(3))
    return [(x, y) for y in range(height) for x in range(width)
            if sum(abs(pixels[x, y][i] - background[i]) for i in range(3)) > 110], False


def brand_colour(image, body) -> tuple[tuple[int, int, int], int]:
    """主体里最常见的那个饱和色，以及色相簇的个数。

    簇数就是「这是不是单色字形」的度量：纯黑白 logo 没有可用色，多色 logo 簇数会散开。
    """
    pixels = image.load()
    buckets: dict[tuple[int, int, int], int] = {}
    for x, y in body:
        red, green, blue = pixels[x, y][:3]
        _hue, light, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
        if saturation > 0.25 and 0.15 < light < 0.85:
            key = (red // 32 * 32, green // 32 * 32, blue // 32 * 32)
            buckets[key] = buckets.get(key, 0) + 1
    if not buckets:
        return (60, 60, 64), 0
    return max(buckets, key=buckets.get), len(buckets)


def render_mark(data: bytes, size: int = MARK_SIZE) -> bytes | None:
    """favicon → 「品牌色圆底 + 白色主体」的 PNG；没把握就返回 None。"""
    from PIL import Image, ImageDraw

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        return None
    image = image.convert("RGBA")
    body, from_alpha = _body_pixels(image)
    if not body or not from_alpha:
        return None
    colour, clusters = brand_colour(image, body)
    if clusters == 0 or clusters > MAX_HUE_BUCKETS:
        return None

    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    painter = mask.load()
    for x, y in body:
        painter[x, y] = 255
    mask = mask.resize((size, size), Image.LANCZOS)

    # 圆用四倍尺寸画再缩，边缘才不是锯齿。
    circle = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(circle).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    circle = circle.resize((size, size), Image.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(Image.new("RGBA", (size, size), colour + (255,)), (0, 0), circle)
    out.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0), mask)
    buffer = io.BytesIO()
    out.save(buffer, format="PNG")
    return buffer.getvalue()


def plain_mark(data: bytes, size: int = MARK_SIZE) -> bytes | None:
    """做不了品牌处理时的回落：把 favicon 原样缩成 PNG。"""
    from PIL import Image

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception:
        return None
    return _encode(image.convert("RGBA").resize((size, size), Image.LANCZOS))


def _encode(image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def cached_path(root: Path, url: str) -> Path | None:
    key = cache_key(url)
    return (root / f"{key}.png") if key else None


def is_fresh(path: Path, now: float | None = None) -> bool:
    """缓存还新鲜吗。

    图标会随站点改版变，但不必每次开页都重取；一个月是「站点改了版早晚会跟上」和
    「不要每开一页就打一遍别人的服务器」之间的折中。
    """
    try:
        age = (now if now is not None else time.time()) - path.stat().st_mtime
    except OSError:
        return False
    return 0 <= age < CACHE_TTL
