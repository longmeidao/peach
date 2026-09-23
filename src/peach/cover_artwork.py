"""原子安装 JAV 封面及与当前图片匹配的取景 sidecar。"""
from __future__ import annotations

import json
import os
import threading
import uuid
from functools import lru_cache
from pathlib import Path

from filelock import FileLock

from . import jav_poster_crop
from .face_detect import FaceDetector, FaceModelUnavailable, decode, main_face

FRONT_START = 0.468
MIN_FACE_Y, MAX_FACE_Y = 0.05, 0.60
_INSTALL_LOCK = threading.RLock()


@lru_cache(maxsize=1)
def _default_detector() -> FaceDetector:
    return FaceDetector(allow_download=False)


def face_record(image, detector) -> dict | None:
    """已解码的封面 → 页面取景记录；无法解码时不生成记录。

    脸框宽高与源图尺寸 `px` 也记下，形状与头像边车（`avatar_face.face_record_of`）
    一致：卡片取景只用脸心，换头像要按脸宽在封面上框出一块方图
    （`avatar_cover_face.face_square`），而 `px` 对不上当前这张图时那一块不作数。
    """
    if image is None or not getattr(image, "size", 0):
        return None
    height, width = image.shape[:2]
    ratio = width / height if height else 0
    faces = detector.detect(image)
    if jav_poster_crop.SLEEVE_RATIO_MIN <= ratio < jav_poster_crop.SLEEVE_RATIO_MAX:
        faces = [face for face in faces if face.cx >= FRONT_START]
    faces = [face for face in faces if MIN_FACE_Y <= face.cy <= MAX_FACE_Y]
    best = main_face(faces)
    return {"ratio": round(ratio, 3), "px": [int(width), int(height)], "face": (
        {"cx": best.cx, "cy": best.cy, "w": best.width, "h": best.height,
         "score": best.score} if best else None)}


def _sidecars(code: str, payload: bytes, size: tuple[int, int], detector=None) -> dict[str, bytes]:
    image = None
    try:
        image = decode(payload)
    except ImportError:
        pass
    poster = jav_poster_crop.crop_record(
        code, size[0], size[1],
        (lambda: jav_poster_crop.column_gradient(image)) if image is not None else None,
    )
    records = {jav_poster_crop.SIDECAR_SUFFIX: poster}
    try:
        active = detector if detector is not None else _default_detector()
        face = face_record(image, active)
    except (FaceModelUnavailable, ImportError):
        face = None
    if face is not None:
        records[".face.json"] = face
    return {suffix: json.dumps(record, ensure_ascii=False).encode("utf-8")
            for suffix, record in records.items()}


def install_cover(target: Path, code: str, payload: bytes, size: tuple[int, int], *,
                  evidence: dict | None = None, detector=None) -> None:
    """准备完成后安装整组文件；失败时还原旧组，避免图片与取景跨版本。"""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    prepared = _sidecars(code, payload, size, detector)
    if evidence is not None:
        prepared[".scraping.json"] = json.dumps(evidence, ensure_ascii=False).encode("utf-8")
    token = uuid.uuid4().hex
    managed = [target, *(target.with_suffix(suffix) for suffix in (
        ".face.json", jav_poster_crop.SIDECAR_SUFFIX, ".scraping.json"))]
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    try:
        image_temp = target.with_name(f".{target.name}.{token}.tmp")
        image_temp.write_bytes(payload)
        staged[target] = image_temp
        for suffix, data in prepared.items():
            temporary = target.with_name(f".{target.stem}{suffix}.{token}.tmp")
            temporary.write_bytes(data)
            staged[target.with_suffix(suffix)] = temporary
        with _INSTALL_LOCK, FileLock(
                str(target.parent / ".cover-install.lock"), thread_local=False):
            try:
                for current in managed:
                    if current.exists():
                        backup = current.with_name(f".{current.name}.{token}.bak")
                        os.replace(current, backup)
                        backups[current] = backup
                for current, temporary in staged.items():
                    os.replace(temporary, current)
            except Exception:
                for current in managed:
                    current.unlink(missing_ok=True)
                for current, backup in backups.items():
                    os.replace(backup, current)
                raise
            for backup in backups.values():
                backup.unlink(missing_ok=True)
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
