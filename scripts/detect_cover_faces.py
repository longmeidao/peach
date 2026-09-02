#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""给已落盘的封面算人脸位置，供 4:3 版式取景用。

固定取景（右侧 53%、纵向 22%）在多数封套上够用，但人物在画面里的高低差别很大，
写死的纵向位置会把一部分作品裁掉下巴或留出大片空白。人脸只用来做**纵向微调**，
横向仍由版式决定——横向靠几何规则已经稳定，没必要交给检出结果。

判据来自 46 张真实封面的实测：

- Haar 正脸检出 24/46。检出率不高，所以这是「锦上添花」而不是取景的前提，
  取不到就退回固定值。
- 21/24 个检出落在 x 68~90%、y 12~33%，正是长封套右侧正封上的人脸位置。
- 剩下 3 个是假阳性：`278GYAN-017` 检到 x=2.9%（封套最左的剧照拼贴），
  `KAVR-428` 一张图检出 7 个框。所以**长封套上落在左半边的检出一律丢弃**——
  那必然是剧照区，不是正封。

结果写成每张封面一个 sidecar（`<番号>.face.json`），不写单一索引文件：抓取器
可能正在并发写同目录，单文件会互相覆盖。脚本可反复运行，已算过的默认跳过。
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

from peach.config import COVER_DIR
from peach.face_detect import FaceDetector, FaceModelUnavailable

#: 长封套的宽高比下限。低于它按竖版正封处理（整张就是正封，没有剧照区）。
SLEEVE_RATIO_MIN = 1.2
SLEEVE_RATIO_MAX = 1.65
#: 长封套上正封的起始横向位置。左边是剧照拼贴，检出必然是假阳性。
FRONT_START = 0.468
#: 纵向取景的合理区间。超出这个范围的检出多半不是主体人物。
MIN_Y, MAX_Y = 0.05, 0.60


def detect(path: Path, detector: FaceDetector) -> dict | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    height, width = image.shape[:2]
    ratio = width / height if height else 0
    faces = detector.detect(image)
    # 长封套左半边是剧照拼贴，那里的脸不是正封主体。这条仍然保留：它挡的不是
    # 假阳性（YuNet 给的是真脸），而是「拼贴里的另一个人」——按面积取最大在
    # `ABW-232` 这类图上已经落在右侧正封，但拼贴里偶尔会有更大的一张。
    if SLEEVE_RATIO_MIN <= ratio < SLEEVE_RATIO_MAX:
        faces = [face for face in faces if face.cx >= FRONT_START]
    faces = [face for face in faces if MIN_Y <= face.cy <= MAX_Y]
    if not faces:
        return {"ratio": round(ratio, 3), "face": None}
    best = max(faces, key=lambda face: face.area)
    return {"ratio": round(ratio, 3),
            "face": {"cx": best.cx, "cy": best.cy, "score": best.score}}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="给封面算人脸位置，供取景用")
    parser.add_argument("--covers", type=Path, default=COVER_DIR)
    parser.add_argument("--redo", action="store_true", help="重算已有的 sidecar")
    parser.add_argument("--limit", type=int, default=0)
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        detector = FaceDetector()
    except FaceModelUnavailable as error:
        raise SystemExit(str(error))

    covers = sorted(args.covers.glob("*.jpg"))
    todo = [p for p in covers
            if args.redo or not p.with_suffix(".face.json").is_file()]
    if args.limit:
        todo = todo[:args.limit]
    print(f"封面 {len(covers)} 张，待处理 {len(todo)} 张")

    stats = {"face": 0, "none": 0, "unreadable": 0}
    for index, path in enumerate(todo, 1):
        result = detect(path, detector)
        if result is None:
            stats["unreadable"] += 1
            print(f"[{index}/{len(todo)}] 读图失败 {path.name}", flush=True)
            continue
        stats["face" if result["face"] else "none"] += 1
        path.with_suffix(".face.json").write_text(
            json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(f"\n检出 {stats['face']}，未检出 {stats['none']}，读图失败 {stats['unreadable']}")
    print("未检出的会退回固定取景，不影响显示。")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
