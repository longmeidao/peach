#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""给已落盘的封面算人脸位置，供卡片取景用。

写死的锚点在多数封套上够用，但人物在画面里的位置差别很大。`object-fit:cover`
一次只裁一个轴，所以两个轴都要算，用哪个交给页面按版式挑：

- 双页封套在 16:9 容器里被纵向裁，纵向锚点决定会不会切掉下巴或留出大片空白；
  横向仍由几何规则定死（正封贴着封套右边缘），不交给检出结果。
- 16:9 官方剧照在大图容器里被横向裁，整幅都是画面，没有「正封那一块」可推。
  横向锚点不跟着人走的话，偏在一侧的人物会整个落到可见窗口外面。

判据来自 46 张真实封面的实测：检出集中在长封套右侧正封的人脸位置（x 68~90%、
y 12~33%）；封套最左的剧照拼贴里也有真脸（`278GYAN-017`、`KAVR-428`），所以
**长封套上落在左半边的检出一律丢弃**——那是拼贴区，不是正封。剧照没有拼贴区，
不套这条。检出不是取景的前提，取不到就退回固定值。

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
#: 上限之外是 16:9 官方剧照。这个值和 `web/app.js` 的 `COVER_FRAME` 必须是同一个，
#: 否则脚本按封套丢掉左半边的脸，页面却拿这张图当剧照按人脸取景，两边对不上。
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
