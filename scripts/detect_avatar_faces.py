#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""给已落盘的实体图算人脸位置，供圆形头像取景用。

实体图多为竖版人像（当前 512 张里 458 张竖版），圆框按几何中心裁切会切掉头顶、
把脸压到下半圈。这里用与封面同一套 Haar 级联检出最大的人脸，把归一化中心和换算
好的 object-position 写进 sidecar（`<kind>-<id>.face.json`）；取景公式只有一份，
在 `peach.web_contract.face_focus`，契约层读 sidecar 原样下发。

结果写成每张图一个 sidecar，不写单一索引文件，理由与封面相同：导入任务可能并发
写同目录。脚本可反复运行，已算过的默认跳过；新增头像后重跑一次即可补齐。未检出
的写 `"face": null` 且省略 `focus`，页面维持几何居中。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR
from peach.face_detect import FaceDetector, FaceModelUnavailable
from peach.web_contract import face_focus


def detect(path: Path, detector: FaceDetector) -> dict | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    height, width = image.shape[:2]
    ratio = round(width / height, 3) if height else 0
    faces = detector.detect(image)
    record: dict = {"ratio": ratio, "face": None}
    if not faces:
        return record
    # 多张脸时取最大的：实体图的主角通常占画面最大，其余是拼贴或背景人物。
    best = faces[0]
    cx, cy = best.cx, best.cy
    record["face"] = {"cx": cx, "cy": cy, "score": best.score}
    focus = face_focus(ratio, cx, cy)
    if focus:
        record["focus"] = focus
    return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="给实体图算人脸位置，供圆头像取景")
    parser.add_argument("--avatars", type=Path, default=GENERATED_DIR / "avatars",
                        help="实体图目录（默认 generated/avatars）")
    parser.add_argument("--redo", action="store_true", help="重算已有的 sidecar")
    parser.add_argument("--limit", type=int, default=0)
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        detector = FaceDetector()
    except FaceModelUnavailable as error:
        raise SystemExit(str(error))

    images = sorted(args.avatars.glob("*.img"))
    todo = [p for p in images
            if args.redo or not p.with_suffix(".face.json").is_file()]
    if args.limit:
        todo = todo[:args.limit]
    print(f"实体图 {len(images)} 张，待处理 {len(todo)} 张")

    stats = {"focus": 0, "face": 0, "none": 0, "unreadable": 0}
    for index, path in enumerate(todo, 1):
        result = detect(path, detector)
        if result is None:
            stats["unreadable"] += 1
            print(f"[{index}/{len(todo)}] 读图失败 {path.name}", flush=True)
            continue
        stats["face" if result["face"] else "none"] += 1
        if result.get("focus"):
            stats["focus"] += 1
        path.with_suffix(".face.json").write_text(
            json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(f"\n检出 {stats['face']}（其中可取景 {stats['focus']}），"
          f"未检出 {stats['none']}，读图失败 {stats['unreadable']}")
    print("未检出的维持几何居中，不影响显示。")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
