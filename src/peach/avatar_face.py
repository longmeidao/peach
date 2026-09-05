# -*- coding: utf-8 -*-
r"""实体图的人脸记录：一张图检一次，两处用。

同一次 YuNet 检出既是圆头像的取景依据（`<kind>-<id>.face.json` sidecar），也是选图
时「这张脸有多少像素」的判据。两处分头各检一遍不只是浪费，还会给出互相矛盾的答案：
`harvest_social_avatars.py` 按脸挑赢家、`detect_avatar_faces.py` 另算一份 sidecar，
中间隔着一次落盘，两边看到的可以是不同的图。

sidecar 的形状是契约的一部分，读它的是 `peach.web_state.avatar_focus`：`px` 给源图
像素，归一化的 `face` 配上它才还得出脸的像素数——放大到几倍还清楚问的是像素。未检出
写 `"face": null` 并省略 `focus`，页面维持几何居中。
"""
from __future__ import annotations

import json
from pathlib import Path

from peach.catalog_rules import face_focus
from peach.face_detect import FaceDetector, main_face

#: sidecar 与实体图同名，换后缀。`performer-8711.img` → `performer-8711.face.json`。
SIDECAR_SUFFIX = ".face.json"


def sidecar_path(image_path: Path) -> Path:
    return Path(image_path).with_suffix(SIDECAR_SUFFIX)


def face_record(image_path: Path, detector: FaceDetector) -> dict | None:
    """检一张图，返回可直接落盘的 sidecar 内容；读不出图返回 None。"""
    import cv2

    image = cv2.imread(str(image_path))
    if image is None:
        return None
    height, width = image.shape[:2]
    ratio = round(width / height, 3) if height else 0
    record: dict = {"ratio": ratio, "px": [width, height], "face": None}
    faces = detector.detect(image)
    if not faces:
        return record
    # 多张脸时挑主角：先卡分数再取最大，判据在 peach.face_detect.main_face。
    best = main_face(faces)
    record["face"] = {"cx": best.cx, "cy": best.cy, "w": best.width,
                      "h": best.height, "score": best.score}
    focus = face_focus(ratio, best.cx, best.cy)
    if focus:
        record["focus"] = focus
    return record


def face_px_width(record: dict | None) -> int:
    """记录里那张脸有多少像素宽。没有脸、没有记录都是 0。"""
    if not record:
        return 0
    face = record.get("face") or {}
    px = record.get("px") or [0, 0]
    try:
        return round(float(face["w"]) * float(px[0]))
    except (KeyError, TypeError, ValueError, IndexError):
        return 0


def write_sidecar(image_path: Path, record: dict) -> Path:
    path = sidecar_path(image_path)
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    return path


def read_sidecar(image_path: Path) -> dict | None:
    path = sidecar_path(image_path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def drop_sidecar(image_path: Path) -> None:
    """换了图又给不出新记录时，宁可没有 sidecar。

    留着旧的比没有更糟：页面会拿上一张图的脸框去给这一张取景，放大到一个空位置上，
    而这在界面上与「这张图本来就该这么显示」看不出区别。
    """
    sidecar_path(image_path).unlink(missing_ok=True)


class FaceProbe:
    """按需构造模型的人脸探针，检不出与检不了分得开。

    模型是懒构造的：这一趟一个候选都没走到就不必去下 232 KB 的 ONNX。取不到模型也不
    让整轮停下——那会把「今天没网」变成「所有人都没有头像」——但要把原因记进 `unavailable`
    让调用方报出来，不然一次下载失败会静悄悄地把整批退回不看脸的旧判据。
    """

    def __init__(self):
        self._detector: FaceDetector | None = None
        self._unavailable = ""

    @property
    def unavailable(self) -> str:
        return self._unavailable

    def __call__(self, image_path: Path) -> dict | None:
        if self._unavailable:
            return None
        if self._detector is None:
            try:
                self._detector = FaceDetector()
            except Exception as error:          # 缺模型、缺 OpenCV、下载失败
                self._unavailable = str(error)
                return None
        try:
            return face_record(Path(image_path), self._detector)
        except Exception:                       # 单张图解不开不该拖垮整轮
            return None
