"""候选图片的实测、取舍与方形归一。

界面把厂牌 Logo 和女优头像都渲染成方框（厂牌方图、资料页 160×160 圆头像）。
候选按实际像素比例处理：接近正方形的直接用，长条形的补背景填成正方形，
只有小到缩进方框会糊的才拒绝。

厂牌标识另有一层：页面三处取图位（品牌小圆片、身份格、厂牌页大位）都用
`object-fit: cover` 铺满方框，所以文件本身必须是不透明方图。`bake_square` 是
这条规则的唯一入口，`classify_plate` 给出它据以分流的判定。女优头像等照片不走
这条路径，只走 `classify` 与 `pad_to_square`。
"""
from __future__ import annotations

import io
from collections import Counter

from PIL import Image

# 长边/短边在这个值以内视为「已经够方」，直接用原图。
MAX_ASPECT = 1.35
# 缩到方框里仍然清晰的最小短边。低于这个值补白也救不回来。
MIN_SHORT_EDGE = 128

SQUARE = "square"
PAD = "pad"
REJECT = "reject"

# 独立图标：带透明像素，主体之外没有属于它自己的底，烤方图时配白底。
MARK = "mark"
# 整块底图：完全不透明，底色是设计的一部分。照片也归这一类。
TILE = "tile"

# 烤白底时内容占方图边长的比例，四周各留约 12% 边距。
PLATE_CONTENT_RATIO = 0.76
PLATE_BACKGROUND = (255, 255, 255, 255)


def measure_image_size(payload: bytes) -> tuple[int, int] | None:
    """只读图片头部拿尺寸；解析失败返回 None，不抛给调用方。"""
    try:
        with Image.open(io.BytesIO(payload)) as image:
            return image.size
    except Exception:
        return None


def classify(width: int, height: int) -> tuple[str, float, str]:
    """返回（判定, 长宽比, 说明）。判定为 square / pad / reject。"""
    if not width or not height:
        return REJECT, 0.0, "尺寸未知"
    aspect = max(width, height) / min(width, height)
    if min(width, height) < MIN_SHORT_EDGE:
        return REJECT, aspect, f"短边 {min(width, height)} < {MIN_SHORT_EDGE}"
    if aspect <= MAX_ASPECT:
        return SQUARE, aspect, "接近正方形"
    return PAD, aspect, f"长宽比 {aspect:.2f}，补背景填成正方形"


def _has_transparency(image: Image.Image) -> bool:
    return image.getchannel("A").getextrema()[0] < 255


def _open_rgba(payload: bytes) -> Image.Image | None:
    try:
        with Image.open(io.BytesIO(payload)) as opened:
            return opened.convert("RGBA")
    except Exception:
        return None


def classify_plate(payload: bytes) -> str | None:
    """这张图是独立图标（`MARK`）还是整块底图（`TILE`）；解析失败返回 None。

    判据是有没有透明像素。带透明的（PREMIUM 那种全透明底蓝色字标）主体之外
    没有属于它的底，铺进方框前得先配一块；完全不透明的（M's Video Group 的
    黑底方块、Natural High 的红底）自带底色，那块底就是设计的一部分。
    """
    image = _open_rgba(payload)
    if image is None:
        return None
    return MARK if _has_transparency(image) else TILE


def bake_square(payload: bytes) -> bytes | None:
    """把厂牌标识烤成不透明方图，返回 PNG 字节；解析失败返回 None。

    独立图标裁掉透明边后居中放到白色方底上，内容占边长
    `PLATE_CONTENT_RATIO`。整块底图接近方形就原样返回原字节，长条按边缘主色
    补方。原始像素一律不缩放，方图边长由内容尺寸推出来。
    """
    image = _open_rgba(payload)
    if image is None:
        return None
    width, height = image.size
    if not width or not height:
        return None
    if not _has_transparency(image):
        if max(width, height) / min(width, height) <= MAX_ASPECT:
            return payload
        return pad_to_square(payload)
    box = image.getchannel("A").getbbox()
    if box is None:
        return None
    content = image.crop(box)
    side = max(max(content.size), round(max(content.size) / PLATE_CONTENT_RATIO))
    canvas = Image.new("RGBA", (side, side), PLATE_BACKGROUND)
    canvas.paste(content, ((side - content.width) // 2, (side - content.height) // 2),
                 content)
    buffer = io.BytesIO()
    canvas.convert("RGB").save(buffer, "PNG")
    return buffer.getvalue()


def _background_color(image: Image.Image) -> tuple[int, int, int, int]:
    """取边缘主色当不透明底色；图片带透明像素时继续保持透明。

    Logo 字样可能贴到四角，不能把某个角上的文字颜色误当成背景。只要原图有
    透明像素，补边就保持透明；完全不透明时再从整圈边缘取出现最多的颜色。
    """
    width, height = image.size
    if _has_transparency(image):
        return (0, 0, 0, 0)
    border = [image.getpixel((x, 0)) for x in range(width)]
    border.extend(image.getpixel((x, height - 1)) for x in range(width))
    border.extend(image.getpixel((0, y)) for y in range(1, height - 1))
    border.extend(image.getpixel((width - 1, y)) for y in range(1, height - 1))
    return Counter(border).most_common(1)[0][0]


def pad_to_square(payload: bytes) -> bytes | None:
    """把长条形图片居中放到正方形画布上，返回 PNG 字节；失败返回 None。"""
    image = _open_rgba(payload)
    if image is None:
        return None
    width, height = image.size
    side = max(width, height)
    canvas = Image.new("RGBA", (side, side), _background_color(image))
    canvas.paste(image, ((side - width) // 2, (side - height) // 2), image)
    buffer = io.BytesIO()
    canvas.save(buffer, "PNG")
    return buffer.getvalue()
