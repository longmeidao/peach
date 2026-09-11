# -*- coding: utf-8 -*-
r"""横版封套里那块 2:3 竖海报的取景框。

JAV 的官方封套是「背面 | 书脊 | 正面」拼成的一整张横图，正面在右侧。Peach 原样
保存这张图（`jav_cover_fetch` 的约定），所以竖海报不是一张新图片，而是一组坐标：
算出来的框写进 sidecar，页面按它取景。原图一个字节都不动。

三种取景方式，写在框的 `method` 里：

- `fold`：Sobel 找到了书脊折痕那道竖直峭壁，正面从折痕右侧开始。
- `ratio`：没找到折痕，退回「右半居中」——正面占右半是封套版式的先验。
- `none`：这张图不该裁。整图框原样返回，页面维持现有的封面取景。

折痕位置的先验来自两份外部实现的实测值，登记在 `docs/REUSE.md`：

- NeoAVDC `c7a430c64013c97a0213cd8a57e2ff5696793a86`（MIT）量 DMM/JavBus 封套，
  折痕落在全宽约 52.5%，也就是中线右侧 2.5% 宽处；它的 `right` 模式先取右半再
  居中取 2:3。
- sakuramediabe `7e40ef87c7518c1dc2b6c8c299170ad7395fec6d`（GPL-3.0，只作算法边界
  参考，不引入代码与运行时）用列向 Sobel 梯度找切点，接受条件是「左右两个峰关于
  中线对称」或「右峰离中线约 20 像素」。

那个 20 像素是在 800×539 的 DMM 低清封套上量的，换算过来正是 2.5% 宽。所以这里
把它写成宽度比例而不是像素常数：在 2184×1464 的高清图上，同一道折痕离中线 55 像素，
拿 20 像素去卡只会把高清图全判成没有折痕。

OpenCV 不在（`vision` 是可选依赖组）或图读不出来时直接走 `ratio`：取景退化成先验
几何，仍然给得出框，不会让整批停下。
"""
from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

from .catalog_rules import (
    is_jav_code,
    is_korean_mib_code,
    is_uncensored_code,
    normalise_code_key,
)

#: 竖海报的宽高比。三处共用：框的形状、`ratio` 回退、越界收缩。
POSTER_ASPECT = 2 / 3

#: 封套的宽高比下限。低于它按竖版正封处理：整张就是正封，没有可裁的横向余量。
#: 这个数和 `SLEEVE_RATIO_MAX` 是 `scripts/detect_cover_faces.py` 与 `web/app.js`
#: 的 `coverAnchor` 共用的同一对判据，三处必须是同一对值，由
#: `tests/test_web_ui.py` 的 `CoverSleeveThresholdTests` 守住。
SLEEVE_RATIO_MIN = 1.2
#: 上限之外是 16:9 官方剧照。整幅都是画面，没有「正面那一块」可推，右半居中会裁出
#: 半张背景，所以这一档不给框。NeoAVDC 对 HEYZO、FC2 与欧美片标 `posterNoCrop`
#: 是同一条判据的另一面：那些封面本身就是成品横版剧照。
SLEEVE_RATIO_MAX = 1.65

#: 找折痕的宽度带。折痕在中线附近，带的右边界放宽到 65% 是为了容纳正面偏窄的封套。
FOLD_BAND = (0.40, 0.65)
#: 折痕相对中线的先验偏移，占全宽的比例（全宽 52.5% 处减去中线 50%）。
SPINE_OFFSET_RATIO = 0.025
#: 偏移与对称两项判据共用的容差，占全宽的比例。在 800 像素宽的封套上等于 10 像素。
FOLD_TOLERANCE_RATIO = 0.0125
#: 峰值要达到全图最强列梯度的这个比例才算一道峭壁。挡住的是平缓横图：那种图在带里
#: 照样有一个最大值，但它只是噪声的最高点，按它切会把画面拦腰截断。
FOLD_MIN_STRENGTH = 0.35
#: 没有折痕时正面的起始位置，占全宽的比例。
RIGHT_HALF = 0.5

FOLD = "fold"
RATIO = "ratio"
NONE = "none"

#: 算法版本号。sidecar 记着它，落后的重算。改动判据、常数或框的形状都要进位。
ALGORITHM_VERSION = "poster-crop-v1"
#: sidecar 与封面同名换后缀：`ABW-232.jpg` → `ABW-232.poster.json`。人脸取景是
#: `.face.json`，两者同目录、同命名风格，各描述一件事：一个是脸在哪，一个是竖框在哪。
SIDECAR_SUFFIX = ".poster.json"

#: 列梯度的来源：一条长度等于图宽的序列，或一个返回它的可调用对象，或 None。
#: 收可调用对象是为了惰性：番号形态或宽高比就能定下 `none` 的图不必解码。
GradientSource = Sequence[float] | Callable[[], Sequence[float] | None] | None


def crops_to_portrait(code: str | None) -> bool:
    """这个番号的封面是横版封套吗。

    判据全部走 `catalog_rules` 现有函数，不在这里另立一套番号形态：

    - 不是 JAV 番号的（欧美片目录名、转载站水印）没有封套版式可言；
    - FC2 是个人投稿，封面是投稿者自选的一张横图；
    - HEYZO 与六位日期式的无码番号（`is_uncensored_code`）走成品横版剧照；
    - 韩国 MIB 不是 JAV，发行物的封面版式另算。
    """
    key = normalise_code_key(code)
    if not key or not is_jav_code(key):
        return False
    if key.startswith("FC2"):
        return False
    return not (is_uncensored_code(key) or is_korean_mib_code(key))


def column_gradient(image) -> list[float] | None:
    """一张 BGR 图按列求和的横向 Sobel 梯度，归一化到 0～1；量不出来返回 None。

    竖直的折痕在横向梯度上是一整列的强响应，按列求和之后它是一根尖峰；横向的构图
    边界（地平线、色带）在横向梯度上几乎没有响应，不会混进来。
    """
    try:
        import cv2
        import numpy
    except ImportError:                         # pragma: no cover - 缺 vision 依赖组
        return None
    if image is None or not getattr(image, "size", 0):
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    columns = numpy.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)).sum(axis=0)
    peak = float(columns.max()) if columns.size else 0.0
    if peak <= 0:
        return None
    return (columns / peak).tolist()


def file_gradient(path: Path | str) -> Callable[[], list[float] | None]:
    """把一张封面包成惰性的列梯度来源：真要用到时才解码。"""
    def source() -> list[float] | None:
        try:
            import cv2
        except ImportError:                     # pragma: no cover - 缺 vision 依赖组
            return None
        return column_gradient(cv2.imread(str(path)))
    return source


def portrait_crop_box(width: int, height: int,
                      gradient_source: GradientSource = None) -> dict:
    """源图尺寸加列梯度 → 2:3 竖海报的取景框。纯函数，不碰文件也不碰 OpenCV。

    返回 `{"x0", "y0", "x1", "y1", "method"}`，坐标是源图像素，右下开区间。
    `method` 为 `none` 时框是整张图：没有可裁的形状，调用方照原图处理。

    框严格 2:3——边长按 `(2k, 3k)` 取整，所以比例是精确的而不是四舍五入出来的。
    `k` 取「高度」与「正面宽度」两者允许的较小值，框因此只会向内收，不会探出源图，
    也不会探出正面那一块。
    """
    width, height = int(width or 0), int(height or 0)
    if width <= 0 or height <= 0:
        return {"x0": 0, "y0": 0, "x1": 0, "y1": 0, "method": NONE}
    ratio = width / height
    if not SLEEVE_RATIO_MIN <= ratio < SLEEVE_RATIO_MAX:
        return _whole(width, height)
    fold = fold_column(width, gradient_source)
    start = fold if fold is not None else round(width * RIGHT_HALF)
    return _fit(width, height, start, FOLD if fold is not None else RATIO)


def fold_column(width: int, gradient_source: GradientSource = None) -> int | None:
    """列梯度里那道书脊折痕所在的列；不成立返回 None。

    带内中线两侧各取一个最大值：右峰是折痕本体的候选，左峰用来判对称。两条判据
    任一成立就采信——折痕压在中线上时两侧峰离中线一样远（折痕有两条边），折痕落在
    先验位置时右峰离中线约 `SPINE_OFFSET_RATIO` 宽。都不成立说明带里那个最大值只是
    画面内容，按它切会切进正面。
    """
    profile = gradient_source() if callable(gradient_source) else gradient_source
    if profile is None:
        return None
    profile = list(profile)
    if len(profile) != int(width) or not profile:
        return None
    peak = max(profile)
    if peak <= 0:
        return None
    center = int(width) // 2
    low = max(0, int(width * FOLD_BAND[0]))
    high = min(int(width), int(width * FOLD_BAND[1]))
    left_span = range(low, center)
    right_span = range(center, high)
    if not left_span or not right_span:
        return None
    left_point = max(left_span, key=profile.__getitem__)
    right_point = max(right_span, key=profile.__getitem__)
    if profile[right_point] < peak * FOLD_MIN_STRENGTH:
        return None
    tolerance = int(width) * FOLD_TOLERANCE_RATIO
    symmetric = abs((center - left_point) - (right_point - center)) <= tolerance
    at_spine = abs((right_point - center) - int(width) * SPINE_OFFSET_RATIO) <= tolerance
    return right_point if symmetric or at_spine else None


def _whole(width: int, height: int) -> dict:
    return {"x0": 0, "y0": 0, "x1": width, "y1": height, "method": NONE}


def _fit(width: int, height: int, start: int, method: str) -> dict:
    """在 `[start, width)` 这一段里放下最大的 2:3 框，居中，越界就收缩。"""
    start = max(0, min(int(start), width))
    panel = width - start
    unit = min(height // 3, panel // 2)
    if unit <= 0:
        return _whole(width, height)
    box_width, box_height = unit * 2, unit * 3
    x0 = start + (panel - box_width) // 2
    y0 = (height - box_height) // 2
    return {"x0": x0, "y0": y0, "x1": x0 + box_width, "y1": y0 + box_height,
            "method": method}


def crop_record(code: str | None, width: int, height: int,
                gradient_source: GradientSource = None) -> dict:
    """可直接落盘的 sidecar 内容：算法版本、源图尺寸、框。

    番号形态先判：不该裁的图连梯度都不算，`gradient_source` 是惰性的就一次都不解码。
    """
    width, height = int(width or 0), int(height or 0)
    box = (portrait_crop_box(width, height, gradient_source)
           if crops_to_portrait(code) else _whole(width, height))
    return {"version": ALGORITHM_VERSION, "px": [width, height], "box": box}


def sidecar_path(image_path: Path | str) -> Path:
    return Path(image_path).with_suffix(SIDECAR_SUFFIX)


def read_sidecar(image_path: Path | str) -> dict | None:
    try:
        data = json.loads(sidecar_path(image_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_sidecar(image_path: Path | str, record: dict) -> Path:
    path = sidecar_path(image_path)
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    return path


def is_current(record: dict | None, width: int, height: int) -> bool:
    """这份 sidecar 还作数吗：版本要对得上，源图尺寸也要对得上。

    尺寸也要对，是因为封面会被更大的那张原子替换（`jav_cover_fetch` 只升不降）。
    版本没变而图换了的话，框仍然是按旧尺寸算的，落在新图上是一块错位的区域——
    而错位在页面上和「这张图本来就该这么取景」看不出区别。
    """
    if not isinstance(record, dict) or record.get("version") != ALGORITHM_VERSION:
        return False
    return list(record.get("px") or []) == [int(width), int(height)]


def projection(record: dict | None) -> dict | None:
    """sidecar → API 的 `poster_box` 字段；不该裁、算不出、读不出都是 None。

    给出源图像素坐标加源图尺寸 `px`，消费方据此自己换算：竖框容器用
    `object-fit: cover` 时，横向 `object-position` 的百分比是 `x0 / (px[0] - 框宽)`。
    """
    if not isinstance(record, dict) or record.get("version") != ALGORITHM_VERSION:
        return None
    box = record.get("box")
    size = record.get("px")
    if not isinstance(box, dict) or box.get("method") in (None, NONE):
        return None
    try:
        edges = {name: int(box[name]) for name in ("x0", "y0", "x1", "y1")}
        width, height = int(size[0]), int(size[1])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    if edges["x1"] <= edges["x0"] or edges["y1"] <= edges["y0"]:
        return None
    if edges["x1"] > width or edges["y1"] > height:
        return None
    return {**edges, "method": str(box["method"]), "px": [width, height]}
