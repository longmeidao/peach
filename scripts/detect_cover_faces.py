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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import COVER_DIR
from peach.cover_artwork import face_record
from peach.face_detect import FaceDetector, FaceModelUnavailable


def detect(path: Path, detector: FaceDetector) -> dict | None:
    import cv2
    image = cv2.imread(str(path))
    return face_record(image, detector)


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
