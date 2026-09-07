"""候选图片的实测、取舍与方形归一。

界面把厂牌 Logo 和女优头像都渲染成方框（厂牌方图、资料页 160×160 圆头像）。
候选按实际像素比例处理：接近正方形的直接用，长条形的补背景填成正方形，
只有小到缩进方框会糊的才拒绝。

厂牌标识另有一层：页面三处取图位（品牌小圆片、身份格、厂牌页大位）都用
`object-fit: cover` 铺满方框，所以文件本身必须是不透明方图。`bake_square` 是
位图这条规则的唯一入口，`classify_plate` 给出它据以分流的判定。矢量标识走
`bake_square_vector`：同样的边距，但方底用外层 SVG 包出来，不栅格化；底色按内容
明暗判，白字标配深底。
女优头像等照片不走这条路径，只走 `classify` 与 `pad_to_square`。
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ElementTree
from collections import Counter

from PIL import Image, ImageChops

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
# 给浅色标识配的深底。这些站点的字标本来就是给深色页面画的，配白底等于把它抹掉。
PLATE_DARK_BACKGROUND = (17, 17, 17, 255)
# 内容里在白底上还看得见的比例低于这个数就改配深底。四张真实矢量标识实测：
# DarkRoomVR 0.20、TeamSkeetXReislin 0.52 会被白底吞掉，TeenFidelity 0.82、
# VirtualTaboo 1.00 不受影响，阈值落在中间两侧都有余量。
PLATE_VISIBLE_RATIO = 0.7
# 判底色用的探针尺寸。只用来数像素，产物仍是原矢量。
PLATE_PROBE_SIZE = 256
# 亮度离白多远才算「在白底上看得见」。
PLATE_INK_CONTRAST = 40

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
# 方底是外层 SVG 包出来的，标记记在它的根元素上：矢量没有像素可读，再跑一遍时
# 只能靠这个标记认出「已经补过白」，否则每跑一次就多套一层白框。
VECTOR_PLATE_MARK = "data-peach-plate"
# 标识文件实测都在几十 KB 以内。上限挡住构造出来的深嵌套 XML，解析前就拒收。
VECTOR_MAX_BYTES = 1 << 20
# 无单位和 px 都直接是用户坐标；pt、em、% 这些换算基准不在文件里，套进外层
# 会缩错，宁可原样留着。
_SVG_LENGTH = re.compile(r"^([-+]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?)(px)?$")

ElementTree.register_namespace("", SVG_NS)
ElementTree.register_namespace("xlink", XLINK_NS)


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


def _svg_number(value: float) -> str:
    """用户坐标写成十进制；整数不留 `.0`，小数留够位数不改变比例。"""
    return f"{value:.10g}"


def _vector_plate_color(payload: bytes) -> tuple[int, int, int, int]:
    """这张矢量标识该配白底还是深底。

    栅格化只用来数像素，产物仍是矢量：把它渲染一遍，看内容里有多少在白底上还
    看得见。DarkRoomVR 的「DARK ROOM」和 TeamSkeetXReislin 的「TEAM」都是白字，
    配白底等于把半个标识抹掉——实测白底可见率 0.20 与 0.52，深底才是它们的本相。
    渲染不出来（`resvg_py` 缺席或图有问题）按白底走，和位图的 `MARK` 一致。
    """
    from .link_marks import rasterize_svg

    rendered = rasterize_svg(payload, PLATE_PROBE_SIZE)
    image = _open_rgba(rendered) if rendered else None
    if image is None:
        return PLATE_BACKGROUND
    ink = image.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    lit = image.convert("L").point(
        lambda value: 255 if value < 255 - PLATE_INK_CONTRAST else 0)
    total = ink.histogram()[255]
    if not total:
        return PLATE_BACKGROUND
    visible = ImageChops.multiply(ink, lit).histogram()[255]
    if visible / total >= PLATE_VISIBLE_RATIO:
        return PLATE_BACKGROUND
    return PLATE_DARK_BACKGROUND


def _svg_length(value: str | None) -> float | None:
    matched = _SVG_LENGTH.match((value or "").strip())
    if matched is None:
        return None
    number = float(matched.group(1))
    return number if number > 0 else None


def _svg_content_box(root: ElementTree.Element) -> tuple[float, float] | None:
    """标识内容在自己坐标系里的宽高；定不出来返回 None。

    `viewBox` 是第一判据：它是作者声明的内容框，而 `width`／`height` 常被下游改成
    展示尺寸。两个都没有（`<svg/>` 这种空壳）就没有可依据的比例，方框边长无从算起。
    """
    box = (root.get("viewBox") or "").replace(",", " ").split()
    if len(box) == 4:
        try:
            width, height = float(box[2]), float(box[3])
        except ValueError:
            return None
        if width > 0 and height > 0:
            return width, height
        return None
    width = _svg_length(root.get("width"))
    height = _svg_length(root.get("height"))
    if width is None or height is None:
        return None
    return width, height


def _parse_svg(payload: bytes) -> ElementTree.Element | None:
    """SVG 根元素；不是 SVG、解析不了或过大都返回 None。"""
    if len(payload) > VECTOR_MAX_BYTES:
        return None
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return None
    return root if root.tag == f"{{{SVG_NS}}}svg" else None


def vector_image_size(payload: bytes) -> tuple[float, float] | None:
    """矢量标识的内容宽高，单位是它自己的用户坐标；量不出来返回 None。

    位图的 `measure_image_size` 给的是像素，这里给的是比例基准：矢量没有固有像素，
    方框边长只能从这个框推。
    """
    root = _parse_svg(payload)
    return None if root is None else _svg_content_box(root)


def bake_square_vector(payload: bytes) -> bytes | None:
    """把矢量标识包进白色方底，返回 SVG 字节；不是可归一的 SVG 时返回 None。

    位图那条路要先栅格化才能取外接框，矢量不必：原文档整个塞进外层 SVG 的一个
    嵌套 `<svg>`，长边占方框 `PLATE_CONTENT_RATIO`，居中，四周是白底矩形。原文档
    一个节点都不改写，放多大仍然清晰。已经包过的原样返回，重复跑不会越套越多。

    内容框直接取 `viewBox`，不像位图那样按 alpha 裁一遍：真实目录里 4 张矢量标识
    渲染后实测，决定方框边长的那条长边都是 tight 的（横向占满 0.97～1.00），
    纵向留白只影响居中，肉眼看不出。底色由 `_vector_plate_color` 判，白字标配深底。
    """
    inner = _parse_svg(payload)
    if inner is None:
        return None
    if inner.get(VECTOR_PLATE_MARK) is not None:
        return payload
    box = _svg_content_box(inner)
    if box is None:
        return None
    width, height = box
    side = max(width, height) / PLATE_CONTENT_RATIO
    # 嵌套 `<svg>` 的 x／y／width／height 说的是它在外层坐标里占哪一块，viewBox 说的
    # 是自己的坐标怎么映射进去。原文档缺 viewBox 时按它的 width／height 补一个，
    # 否则嵌套之后内容会按外层坐标重新量，比例就散了。
    if not (inner.get("viewBox") or "").strip():
        inner.set("viewBox", f"0 0 {_svg_number(width)} {_svg_number(height)}")
    inner.set("x", _svg_number((side - width) / 2))
    inner.set("y", _svg_number((side - height) / 2))
    inner.set("width", _svg_number(width))
    inner.set("height", _svg_number(height))
    edge = _svg_number(side)
    plate = ElementTree.Element(f"{{{SVG_NS}}}svg", {
        "width": edge, "height": edge, "viewBox": f"0 0 {edge} {edge}",
        VECTOR_PLATE_MARK: "1",
    })
    red, green, blue = _vector_plate_color(payload)[:3]
    ElementTree.SubElement(plate, f"{{{SVG_NS}}}rect", {
        "x": "0", "y": "0", "width": edge, "height": edge,
        "fill": f"#{red:02x}{green:02x}{blue:02x}",
    })
    plate.append(inner)
    return ElementTree.tostring(plate, encoding="utf-8", xml_declaration=True)


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
