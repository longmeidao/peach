#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
创作者风格板 —— 把一位创作者名下多个视频的抽帧图各取一格，拼成一张 3x3。

为什么不直接读单个视频的抽帧图：一位创作者动辄几百条视频，逐条读不现实；
读单张又只代表一个片子。风格板从 9 个不同视频各取首格，一张图就能看出这位
创作者的稳定风格（拍摄场景、人数、镜头语言），归属也不会串。

抽帧图版式：宽固定 1440，3 列。横屏片一行（高 ~810），竖屏片三行（高 ~2544）。
据此推算单格高度后裁首格。

用法:
    python scripts/creator_boards.py [--top N] [--per 9]
输出:
    R:\peach-data\generated\boards\<序号>_<创作者>.jpg
"""
from __future__ import annotations

import collections
import os
import random
import re
import sqlite3
import subprocess
import sys

DB = r"R:\peach-data\database\ledger.db"
OUTDIR = r"R:\peach-data\generated\boards"
FFMPEG = r"R:\peach-data\tools\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"R:\peach-data\tools\ffmpeg\bin\ffprobe.exe"

ARGV = sys.argv[1:]
TOP = int(ARGV[ARGV.index("--top") + 1]) if "--top" in ARGV else 40
PER = int(ARGV[ARGV.index("--per") + 1]) if "--per" in ARGV else 9

LEGACY = r"R:\Resources\Intake\snapshots"
CURRENT = r"R:\peach-data\generated\snapshots"


def rebase(path: str) -> str:
    return CURRENT + path[len(LEGACY):] if path.startswith(LEGACY) else path


def cell_height(path: str) -> int | None:
    """抽帧图宽固定 1440 / 3 列；高 <1000 视为单行，否则按三行推算格高。"""
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
        capture_output=True, text=True)
    try:
        width, height = (int(x) for x in out.stdout.strip().split(","))
    except ValueError:
        return None
    if width != 1440:
        return None
    return height if height < 1000 else height // 3


def safe(name: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff-]", "_", name)[:40]


def build(paths: list[str], dst: str) -> bool:
    """每张裁首格 → 统一装进 360x360 → 拼 3x3。"""
    inputs, filters, labels = [], [], []
    for i, src in enumerate(paths):
        ch = cell_height(src)
        if ch is None:
            continue
        idx = len(labels)
        inputs += ["-i", src]
        filters.append(
            f"[{idx}:v]crop=480:{ch}:0:0,"
            f"scale=360:360:force_original_aspect_ratio=decrease,"
            f"pad=360:360:(ow-iw)/2:(oh-ih)/2:color=black[v{idx}]")
        labels.append(f"[v{idx}]")
        if len(labels) == 9:
            break
    if len(labels) < 4:
        return False
    while len(labels) < 9:                     # 不足九格补黑，保持 3x3
        filters.append(f"color=c=black:s=360x360:d=1[v{len(labels)}]")
        labels.append(f"[v{len(labels)}]")
    chain = ";".join(filters) + ";" + "".join(labels) + "xstack=inputs=9:layout=" + \
        "|".join(f"{c*360}_{r*360}" for r in range(3) for c in range(3)) + "[out]"
    run = subprocess.run(
        [FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex", chain,
         "-map", "[out]", "-frames:v", "1", "-q:v", "4", dst],
        capture_output=True, text=True)
    if run.returncode != 0:
        print("  ffmpeg:", run.stderr.strip()[:160])
        return False
    return os.path.exists(dst)


def main() -> int:
    os.makedirs(OUTDIR, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT creator, snapshot_path FROM asset WHERE medium='video' "
        "AND creator IS NOT NULL AND creator<>'' AND snapshot_path IS NOT NULL "
        "AND id NOT IN (SELECT asset_id FROM asset_tag)").fetchall()
    counts = collections.Counter(
        r[0] for r in conn.execute(
            "SELECT creator FROM asset WHERE medium='video' AND creator IS NOT NULL "
            "AND creator<>'' AND id NOT IN (SELECT asset_id FROM asset_tag)"))
    conn.close()

    by_creator: dict[str, list[str]] = collections.defaultdict(list)
    for creator, snap in rows:
        path = rebase(snap)
        if os.path.exists(path):
            by_creator[creator].append(path)

    ranked = [(c, n) for c, n in counts.most_common() if len(by_creator.get(c, [])) >= 4][:TOP]
    print(f"可出板创作者 {len(ranked)} 位，覆盖无标签视频 {sum(n for _, n in ranked)} 条")

    made = 0
    for rank, (creator, n) in enumerate(ranked, 1):
        pool = by_creator[creator]
        random.Random(creator).shuffle(pool)
        dst = os.path.join(OUTDIR, f"{rank:02d}_{safe(creator)}_{n}.jpg")
        if build(pool[:PER], dst):
            made += 1
            print(f"  {rank:>2}. {creator[:26]:<26} 视频{n:>4}  取样{min(len(pool), PER)}  → {os.path.basename(dst)}")
        else:
            print(f"  {rank:>2}. {creator[:26]:<26} 视频{n:>4}  失败")
    print(f"\n生成 {made} 张 → {OUTDIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
