r"""人脸比对：OpenCV 的 SFace，回答「这两张脸是不是同一个人」。

检出（`face_detect`，YuNet）回答的是「脸在哪」，这里回答的是「脸是谁」。两者同属
opencv_zoo，走同一个 `cv2` 包：`cv2.FaceRecognizerSF` 先按 YuNet 给的五个关键点把脸
摆正、切成 112×112（`alignCrop`），再提一条 128 维特征（`feature`）。两条特征的余弦
相似度过 `COSINE_THRESHOLD` 就算同一个人。

用它的地方只有一处：补头像后继在图库同名多张时，拿每张候选上的脸和她单人作品封面上
截到的脸比，挑出是她本人的那几张（ADR-0056）。

模型不进 Git：37 MB 的 ONNX，与 YuNet 一样放 `peach-data/tools/`，首次用到时按固定
地址取一次、校验 sha256（`face_detect.fetch_model`）。取不到时 `FaceMatcher` 记下原因、
一张都不比，调用方退回不看脸的旧判据——一次下载失败不能变成「装了一张别人的脸」。
"""
from __future__ import annotations

from pathlib import Path

from . import face_detect
from .config import TOOLS_DIR
from .face_detect import FaceDetector, main_face

#: opencv_zoo 的 SFace 定版模型。走 media. 域名的原因和 YuNet 一样：仓库用 Git LFS，
#: raw. 域名只回一个指针文件——那个指针里的 oid 就是下面这个哈希。
MODEL_URL = (
    "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
    "models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
)
MODEL_SHA256 = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
MODEL_PATH = TOOLS_DIR / "sface" / "face_recognition_sface_2021dec.onnx"
#: 记进头像边车的模型名，回溯时要答得出「这个分是哪一版模型给的」。
MODEL_NAME = "sface_2021dec"
#: SFace 官方给的余弦阈值（opencv_zoo `face_recognition_sface` 的 README 与示例）：
#: 过它算同一个人。不自己调：本库没有带真值的样本集，调出来的数没有依据。
COSINE_THRESHOLD = 0.363


def ensure_model(path: Path | None = None, *, allow_download: bool = True) -> Path:
    target = Path(path) if path is not None else MODEL_PATH
    return face_detect.fetch_model(target, MODEL_URL, MODEL_SHA256,
                                   allow_download=allow_download, label="人脸比对模型")


def cosine(one, other) -> float:
    """两条特征的余弦相似度。任一条是零向量就是 0。"""
    import numpy

    first = numpy.asarray(one, dtype=numpy.float64).ravel()
    second = numpy.asarray(other, dtype=numpy.float64).ravel()
    norm = float(numpy.linalg.norm(first) * numpy.linalg.norm(second))
    return float(first @ second) / norm if norm > 0 else 0.0


class FaceEmbedder:
    """SFace 特征提取器。一次构造反复使用；检脸借同一套 YuNet。"""

    def __init__(self, model: Path | None = None, *, detector: FaceDetector | None = None,
                 allow_download: bool = True) -> None:
        import cv2

        self._cv2 = cv2
        self.model_path = ensure_model(model, allow_download=allow_download)
        create = getattr(getattr(cv2, "FaceRecognizerSF", None), "create", None)
        if create is None:                       # pragma: no cover - 依赖版本兜底
            raise face_detect.FaceModelUnavailable(
                "当前 OpenCV 没有 FaceRecognizerSF；需要 4.5.4 以上")
        self._recognizer = create(str(self.model_path), "")
        self._detector = detector or FaceDetector(allow_download=allow_download)

    def embed(self, image):
        """这张图上主脸的特征；检不出脸、或检出的框没带关键点就是 None。

        主脸按 `main_face` 挑，和取景、截脸是同一张。小图先放大到检出器认得出的尺寸，
        关键点换算回放大后那张图的像素，摆正也在那张图上做。
        """
        import numpy

        source = face_detect._upscale(image)
        best = main_face(self._detector.detect(source))
        if best is None or len(best.landmarks) != 10:
            return None
        rows, cols = source.shape[:2]
        points = [value * (cols if index % 2 == 0 else rows)
                  for index, value in enumerate(best.landmarks)]
        box = numpy.array([[(best.cx - best.width / 2) * cols,
                            (best.cy - best.height / 2) * rows,
                            best.width * cols, best.height * rows,
                            *points, best.score]], dtype=numpy.float32)
        aligned = self._recognizer.alignCrop(source, box)
        feature = self._recognizer.feature(aligned)
        return tuple(float(value) for value in numpy.asarray(feature).ravel())


class FaceMatcher:
    """按需构造模型的比对器，「比不出」与「比不了」分得开。

    和 `avatar_face.FaceProbe` 同一个立场：模型懒构造，这一趟用不上就不去下 37 MB；
    取不到不让整轮停下，但原因记进 `unavailable`，调用方据此退回旧判据并报出来。
    """

    def __init__(self):
        self._embedder: FaceEmbedder | None = None
        self._unavailable = ""

    @property
    def unavailable(self) -> str:
        return self._unavailable

    def _ready(self) -> FaceEmbedder | None:
        if self._unavailable:
            return None
        if self._embedder is None:
            try:
                self._embedder = FaceEmbedder()
            except Exception as error:          # 缺模型、缺 OpenCV、下载失败
                self._unavailable = str(error) or type(error).__name__
                return None
        return self._embedder

    def embedding(self, payload: bytes):
        """一串图片字节上主脸的特征；解不开、检不出脸、模型不可用都是 None。"""
        embedder = self._ready()
        if embedder is None:
            return None
        try:
            image = face_detect.decode(payload)
            return None if image is None else embedder.embed(image)
        except Exception:                       # 单张图解不开不该拖垮整轮
            return None
