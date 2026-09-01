r"""人脸检出：OpenCV 的 YuNet，取代已经跑不起来的 Haar 级联。

**先说清一件常被混淆的事：YuNet 不是 OpenCV 的替代品，它就是 OpenCV 的一部分。**
`cv2.FaceDetectorYN` 是 OpenCV 的 API，YuNet 是它跑的那个模型。解码、色彩转换、
缩放仍然要 OpenCV。这里换掉的只是「检出器」这一层：

- Haar 级联：2001 年的算法，模型是随 wheel 分发的 XML。
- YuNet：2021 年的小型 CNN，模型是一个 232 KB 的 ONNX，走 OpenCV 的 DNN 模块。

换的直接原因是旧路径已经跑不起来。`pyproject.toml` 钉的是
`opencv-python-headless==5.0.0.93`，而 OpenCV 5 把 Haar 级联移出了 Python wheel：
`cv2.CascadeClassifier` 不存在，`cv2/data/` 只剩 `__init__.py`。两个取景脚本因此
直接抛 `AttributeError`，954 张封面一个 sidecar 都没有，「人脸取景」从来没生效过。

换的第二个原因是召回。`docs/REUSE.md` 记过一次实测：512 张头像 Haar 检出 313；
封面脚本自己的注释也写着 46 张检出 24。也就是漏掉三分之一以上，还得靠额外规则
丢掉假阳性（`278GYAN-017` 检到画面最左的剧照拼贴，`KAVR-428` 一张图检出 7 个框）。
YuNet 给的是框 + 5 个关键点 + 置信度，可以按分数卡，不必靠位置猜。

模型不进 Git：它是二进制资产，和 ffmpeg 一样放 `peach-data/tools/`。首次运行按
固定 URL 取一次并校验 sha256——版本要能复现，不能「取到什么算什么」。
"""
from __future__ import annotations

import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .config import TOOLS_DIR

#: opencv_zoo 的 YuNet 定版模型。走 media. 域名是因为仓库用 Git LFS，
#: raw. 域名只会回一个 131 字节的指针文件。
MODEL_URL = (
    "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
MODEL_BYTES = 232589
MODEL_PATH = TOOLS_DIR / "yunet" / "face_detection_yunet_2023mar.onnx"

#: 低于这个分数的检出不算数。YuNet 会给出置信度，不必再靠「落在左半边就是假阳性」
#: 这类位置规则去猜——那条规则只在长封套上成立，换个版式就不成立。
DEFAULT_SCORE = 0.6
#: NMS 阈值沿用 opencv_zoo 示例的默认值。
DEFAULT_NMS = 0.3
#: 送进网络前的长边上限。YuNet 是定尺寸输入，超大图先缩再检更快且不掉召回；
#: 坐标按缩放比还原回原图。
MAX_SIDE = 1280


class FaceModelUnavailable(RuntimeError):
    """模型取不到。调用方据此决定是跳过还是整轮停下，不要静默当成「没有脸」。"""


@dataclass(frozen=True)
class Face:
    """一张脸在原图里的归一化位置。`score` 是模型给的置信度。"""

    cx: float
    cy: float
    width: float
    height: float
    score: float

    @property
    def area(self) -> float:
        return self.width * self.height


def ensure_model(path: Path | None = None, *, allow_download: bool = True) -> Path:
    """返回可用的模型路径；本地没有且允许联网时取一次。

    校验 sha256 而不是只看文件在不在：半个下载同样留下一个文件，而它会让
    `FaceDetectorYN_create` 抛一个和网络毫无关系的错。
    """
    target = Path(path) if path is not None else MODEL_PATH
    if target.is_file() and _digest(target) == MODEL_SHA256:
        return target
    if target.is_file():
        target.unlink()
    if not allow_download:
        raise FaceModelUnavailable(f"缺少人脸模型：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".part")
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
            payload = response.read()
    except OSError as error:
        raise FaceModelUnavailable(f"取人脸模型失败：{error}") from error
    digest = hashlib.sha256(payload).hexdigest()
    if digest != MODEL_SHA256:
        raise FaceModelUnavailable(
            f"人脸模型校验不符：期望 {MODEL_SHA256}，实际 {digest}")
    temporary.write_bytes(payload)
    temporary.replace(target)
    return target


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FaceDetector:
    """YuNet 检出器。一次构造反复使用，输入尺寸每张图现设。"""

    def __init__(self, model: Path | None = None, *, score: float = DEFAULT_SCORE,
                 nms: float = DEFAULT_NMS, allow_download: bool = True) -> None:
        import cv2

        self._cv2 = cv2
        self.score = score
        self.model_path = ensure_model(model, allow_download=allow_download)
        create = getattr(cv2, "FaceDetectorYN_create", None)
        if create is None:                       # pragma: no cover - 依赖版本兜底
            raise FaceModelUnavailable(
                "当前 OpenCV 没有 FaceDetectorYN；需要 4.5.4 以上")
        self._detector = create(str(self.model_path), "", (320, 320), score, nms, 5000)

    def detect(self, image) -> list[Face]:
        """返回归一化坐标的人脸，按面积从大到小。

        送进网络前按长边缩到 `MAX_SIDE`：YuNet 的输入尺寸是现设的，超大图直接喂
        既慢又不涨召回。坐标先在缩放图上算，再按同一个比例还原——归一化之后
        缩放比自然抵消，所以只要保证宽高用的是同一张图的。
        """
        cv2 = self._cv2
        height, width = image.shape[:2]
        if not height or not width:
            return []
        scale = min(1.0, MAX_SIDE / max(height, width))
        source = (cv2.resize(image, (max(1, int(width * scale)),
                                     max(1, int(height * scale))))
                  if scale < 1.0 else image)
        rows, cols = source.shape[:2]
        self._detector.setInputSize((cols, rows))
        _, raw = self._detector.detect(source)
        if raw is None:
            return []
        faces = []
        for row in raw:
            x, y, w, h, *_rest = row.tolist()
            confidence = float(row[-1])
            if confidence < self.score or w <= 0 or h <= 0:
                continue
            faces.append(Face(
                cx=round(min(1.0, max(0.0, (x + w / 2) / cols)), 3),
                cy=round(min(1.0, max(0.0, (y + h / 2) / rows)), 3),
                width=round(min(1.0, w / cols), 3),
                height=round(min(1.0, h / rows), 3),
                score=round(confidence, 3),
            ))
        faces.sort(key=lambda face: face.area, reverse=True)
        return faces
