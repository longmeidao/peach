"""候选图片的实测、取舍与方形归一。

界面把厂牌 Logo 和女优头像都渲染成方框（厂牌方图、资料页 160×160 圆头像）。
候选按实际像素比例处理：接近正方形的直接用，长条形的补背景填成正方形，
只有小到缩进方框会糊的才拒绝。
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


def _background_color(image: Image.Image) -> tuple[int, int, int, int]:
    """取边缘主色当不透明底色；图片带透明像素时继续保持透明。

    Logo 字样可能贴到四角，不能把某个角上的文字颜色误当成背景。只要原图有
    透明像素，补边就保持透明；完全不透明时再从整圈边缘取出现最多的颜色。
    """
    width, height = image.size
    if image.getchannel("A").getextrema()[0] < 255:
        return (0, 0, 0, 0)
    border = [image.getpixel((x, 0)) for x in range(width)]
    border.extend(image.getpixel((x, height - 1)) for x in range(width))
    border.extend(image.getpixel((0, y)) for y in range(1, height - 1))
    border.extend(image.getpixel((width - 1, y)) for y in range(1, height - 1))
    return Counter(border).most_common(1)[0][0]


def pad_to_square(payload: bytes) -> bytes | None:
    """把长条形图片居中放到正方形画布上，返回 PNG 字节；失败返回 None。"""
    try:
        with Image.open(io.BytesIO(payload)) as opened:
            image = opened.convert("RGBA")
    except Exception:
        return None
    width, height = image.size
    side = max(width, height)
    canvas = Image.new("RGBA", (side, side), _background_color(image))
    canvas.paste(image, ((side - width) // 2, (side - height) // 2), image)
    buffer = io.BytesIO()
    canvas.save(buffer, "PNG")
    return buffer.getvalue()
