# -*- coding: utf-8 -*-
r"""横版封套里正封那一块在哪。

JAV 的官方封套是「背面 | 书脊 | 正面」拼成的一整张横图，正面在右侧。Peach 原样
保存这张图（`jav_cover_fetch` 的约定），所以正封不是一张新图片，而是一组坐标：
算出来的框写进 sidecar，页面按它取景。原图一个字节都不动。

框就是正封本身——从折痕一路到右缘、满高。页面要的正是这一块：按折痕切掉封底，
正封整块摆进卡片。框里不另取固定形状的子区域，因为卡片的容器比例是页面的事，
源图这一侧无从知道；在这里先按某个形状切一刀，只会把正封两侧各削掉一圈。

三种取景方式，写在框的 `method` 里：

- `fold`：Sobel 找到了书脊折痕那道竖直峭壁，正面从折痕右侧开始。
- `ratio`：没找到折痕，按正封宽高比的先验从右缘量回去。
- `none`：这张图不该裁。整图框原样返回，页面维持现有的封面取景。

折痕的判据是「切出来的正封形状对不对」，不是「折痕落在全宽的百分之几」：DVD 封套
正面印刷面 135×190mm，宽高比 0.711；本机 637 张实测中位数 0.704、1% 分位 0.684、
99% 分位 0.725，比折痕在全宽里的位置稳得多——后者还要受背面留白与书脊厚度影响。
所以只在「切出来的正封落在 `PANEL_ASPECT_MIN`～`PANEL_ASPECT_MAX` 之间」的那几十
列里找峭壁，窗里够强的边不止一条时按形状定夺，不按谁更强。

外部实现的实测值登记在 `docs/REUSE.md`，这里留作来路：

- NeoAVDC `c7a430c64013c97a0213cd8a57e2ff5696793a86`（MIT）量 DMM/JavBus 封套，
  折痕落在全宽约 52.5%。这个数和本机实测对得上，但它是结果不是判据——拿它反过来
  卡位置，封套一宽一窄就落空。
- sakuramediabe `7e40ef87c7518c1dc2b6c8c299170ad7395fec6d`（GPL-3.0，只作算法边界
  参考，不引入代码与运行时）用列向 Sobel 梯度找切点，接受条件是「左右两个峰关于
  中线对称」或「右峰离中线约 20 像素」。这两条都不采用：对称那一条在本机实测里会
  误收，KBI-036 的背面有一条竖直分栏线，与正封内部的一道强边恰好关于中线对称，按
  它切会切到正封里面 52 像素处，把大标题削掉一截；宽高比窗口把这张定在 421 列，
  正封宽高比 0.703。

OpenCV 不在（`vision` 是可选依赖组）或图读不出来时直接走 `ratio`：取景退化成先验
几何，仍然给得出框，不会让整批停下。
"""
from __future__ import annotations

import json
import statistics
from collections.abc import Callable, Sequence
from pathlib import Path

from .catalog_rules import (
    is_jav_code,
    is_korean_mib_code,
    is_uncensored_code,
    normalise_code_key,
)

#: 封套的宽高比下限。低于它按竖版正封处理：整张就是正封，没有可裁的横向余量。
#: 这个数和 `SLEEVE_RATIO_MAX` 是 `scripts/detect_cover_faces.py` 与 `web/app.js`
#: 的 `coverAnchor` 共用的同一对判据，三处必须是同一对值，由
#: `tests/test_web_ui.py` 的 `CoverSleeveThresholdTests` 守住。
SLEEVE_RATIO_MIN = 1.2
#: 上限之外是 16:9 官方剧照。整幅都是画面，没有「正面那一块」可推，按先验切会裁出
#: 半张背景，所以这一档不给框。NeoAVDC 对 HEYZO、FC2 与欧美片标 `posterNoCrop`
#: 是同一条判据的另一面：那些封面本身就是成品横版剧照。
SLEEVE_RATIO_MAX = 1.65

#: 正封宽高比的可信区间，折痕只在切出这个形状的那几十列里找。区间取自本机 637 张
#: 实测（1% 分位 0.684、中位 0.704、99% 分位 0.725）并向外各留出余量：书脊厚的封套
#: 两条边都要落在窗里，`FOLD_RIVAL_RATIO` 那一关才看得见它们、才挑得出右边那条。
PANEL_ASPECT_MIN = 0.68
PANEL_ASPECT_MAX = 0.76
#: 峰值要达到全图最强列梯度的这个比例才算一道峭壁。挡住的是平缓横图：那种图在窗里
#: 照样有一个最大值，但它只是噪声的最高点，按它切会把画面拦腰截断。
FOLD_MIN_STRENGTH = 0.35
#: 强度达到窗内最强边这个比例的列都算候选折痕。书脊有左右两条边，窗口装得下一整条
#: 书脊时两条都在候选里，而左边那条常常更强：它挨着封底的留白，右边那条挨着正封的
#: 画面。谁更强不说明哪条是折痕，所以候选之间按「切出来的正封形状」定夺。
FOLD_RIVAL_RATIO = 0.7
#: 候选按相邻归并成边：一道边在梯度上响应好几列，相距不超过源图宽这个比例的算一条。
FOLD_EDGE_SPAN = 0.005
#: 折痕是一道有宽度的斜坡，梯度的峰落在斜坡最陡处，也就是斜坡当中；书脊的最后一两
#: 列还在峰的右边。切点从峰往右走到梯度落回窗内中位数为止，最多走源图宽的这个比例。
#: 本机 637 张实测位移中位 2 列、90% 分位 3 列。
FOLD_SETTLE_LIMIT = 0.01
#: 没找到折痕时按这个宽高比从右缘量回去，也是候选之间定夺用的形状。本机 637 张命中
#: 折痕的封套实测中位数，贴着 135×190mm 的物理值；比「取右半」准——右半的形状随
#: 封套总宽在 0.60～0.82 之间飘。
PANEL_ASPECT = 0.704

FOLD = "fold"
RATIO = "ratio"
NONE = "none"

#: 算法版本号。sidecar 记着它，落后的重算。改动判据、常数或框的形状都要进位。
ALGORITHM_VERSION = "poster-crop-v4"
#: sidecar 与封面同名换后缀：`ABW-232.jpg` → `ABW-232.poster.json`。人脸取景是
#: `.face.json`，两者同目录、同命名风格，各描述一件事：一个是脸在哪，一个是正封在哪。
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


def front_panel_box(width: int, height: int,
                    gradient_source: GradientSource = None) -> dict:
    """源图尺寸加列梯度 → 正封那一块的取景框。纯函数，不碰文件也不碰 OpenCV。

    返回 `{"x0", "y0", "x1", "y1", "method"}`，坐标是源图像素，右下开区间。
    框的右下角永远是源图的右下角，`x0` 就是折痕所在的列——正封是「折痕右边的全部」，
    不是它里面某个形状的子区域。`method` 为 `none` 时框是整张图：没有可裁的形状，
    调用方照原图处理。
    """
    width, height = int(width or 0), int(height or 0)
    if width <= 0 or height <= 0:
        return {"x0": 0, "y0": 0, "x1": 0, "y1": 0, "method": NONE}
    ratio = width / height
    if not SLEEVE_RATIO_MIN <= ratio < SLEEVE_RATIO_MAX:
        return _whole(width, height)
    fold = fold_column(width, height, gradient_source)
    start = fold if fold is not None else round(width - PANEL_ASPECT * height)
    return _panel(width, height, start, FOLD if fold is not None else RATIO)


def fold_column(width: int, height: int,
                gradient_source: GradientSource = None) -> int | None:
    """列梯度里那道书脊折痕所在的列；不成立返回 None。

    只在「折痕右边那块的宽高比落在 `PANEL_ASPECT_MIN`～`PANEL_ASPECT_MAX`」的那几十
    列里找。窗口由源图高度定，所以高清图和低清图用的是同一条判据；窗口之外再强的边
    也不看——那是画面内容，按它切会切进正面或带出封底。

    窗里够强的边不止一条时，取切出来的正封最贴近 `PANEL_ASPECT` 的那条，不是最强的
    那条：书脊厚到两条边都落进窗里时，左边那条往往更强，按它切整条书脊都在框里。

    选中的那一列是斜坡最陡处，不是斜坡尽头，所以还要往右走到梯度落回基线：基线取窗
    内梯度的中位数，每张图各算各的，画面忙的封套门槛自然就高。
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
    width, height = int(width), int(height)
    low = max(0, round(width - PANEL_ASPECT_MAX * height))
    high = min(width - 1, round(width - PANEL_ASPECT_MIN * height))
    window = range(low, high + 1)
    if not window:
        return None
    top = max(window, key=profile.__getitem__)
    if profile[top] < peak * FOLD_MIN_STRENGTH:
        return None
    edges = _rival_edges(profile, window, profile[top],
                         round(width * FOLD_EDGE_SPAN))
    found = min(edges, key=lambda column: abs((width - column) / height - PANEL_ASPECT))
    baseline = statistics.median(profile[low:high + 1])
    return _settled(profile, found, baseline, round(width * FOLD_SETTLE_LIMIT))


def _rival_edges(profile: list[float], window: range, top: float,
                 span: int) -> list[int]:
    """窗里强度和最强边相当的那几条边，一条边只留最强的那一列。"""
    ranked = sorted((column for column in window
                     if profile[column] >= top * FOLD_RIVAL_RATIO),
                    key=profile.__getitem__, reverse=True)
    kept: list[int] = []
    for column in ranked:
        if all(abs(column - other) > span for other in kept):
            kept.append(column)
    return kept


def _settled(profile: list[float], found: int, baseline: float, limit: int) -> int:
    """从斜坡最陡的那一列往右走到梯度落回基线，书脊的最后几列留在框外。"""
    stop = min(found + limit, len(profile) - 1)
    for column in range(found + 1, stop + 1):
        if profile[column] <= baseline:
            return column
    return stop


def _whole(width: int, height: int) -> dict:
    return {"x0": 0, "y0": 0, "x1": width, "y1": height, "method": NONE}


def _panel(width: int, height: int, start: int, method: str) -> dict:
    """折痕右边的全部就是正封。切不出宽度的按整图处理。"""
    start = max(0, min(int(start), width))
    if width - start <= 0:
        return _whole(width, height)
    return {"x0": start, "y0": 0, "x1": width, "y1": height, "method": method}


def crop_record(code: str | None, width: int, height: int,
                gradient_source: GradientSource = None) -> dict:
    """可直接落盘的 sidecar 内容：算法版本、源图尺寸、框。

    番号形态先判：不该裁的图连梯度都不算，`gradient_source` 是惰性的就一次都不解码。
    """
    width, height = int(width or 0), int(height or 0)
    box = (front_panel_box(width, height, gradient_source)
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

    给出源图像素坐标加源图尺寸 `px`，消费方据此自己换算。页面只用到 `x0`：那是
    折痕所在的列，`x0 / px[0]` 就是要从左边切掉的那一段占全宽的比例。
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
