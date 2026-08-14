#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
创作者风格板 —— 把一位创作者名下多个视频的抽帧图各取一格，拼成一张 3x3。

为什么不直接读单个视频的抽帧图：一位创作者动辄几百条视频，逐条读不现实；
读单张又只代表一个片子。风格板从 9 个不同视频各取首格，一张图就能看出这位
创作者的稳定风格（拍摄场景、人数、镜头语言），归属也不会串。

抽帧图版式：宽固定 1440，3 列。横屏片一行（高 ~810），竖屏片三行（高 ~2544）。
据此推算单格高度后裁首格。

两种取帧来源：
  * 默认用已生成的抽帧图裁首格，不产生任何网络流量。
  * --from-video 在没有抽帧图时直接从视频取 1 帧。给 PikPak 用的：实测那边
    单帧 seek 要 25~40 秒（115 只要 0.4~1.4 秒），全量抽帧 9 帧/条要 14 天，
    而打标只需要"每位创作者 9 个采样"，直接取帧便宜三个数量级。计费来源，
    必须显式加 --allow-metered。延迟型瓶颈，并发接近线性，默认开 16 路。

用法:
    python scripts/creator_boards.py [--top N] [--per 9]
    python scripts/creator_boards.py --from-video --allow-metered [--workers 16]
输出:
    R:\peach-data\generated\boards\<序号>_<创作者>.jpg
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import hashlib
import os
import random
import re
import sqlite3
import subprocess
import sys
import time

DB = r"R:\peach-data\database\ledger.db"
OUTDIR = r"R:\peach-data\generated\boards"
FFMPEG = r"R:\peach-data\tools\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"R:\peach-data\tools\ffmpeg\bin\ffprobe.exe"

ARGV = sys.argv[1:]
TOP = int(ARGV[ARGV.index("--top") + 1]) if "--top" in ARGV else 40
PER = int(ARGV[ARGV.index("--per") + 1]) if "--per" in ARGV else 9
WORKERS = int(ARGV[ARGV.index("--workers") + 1]) if "--workers" in ARGV else 16
FROM_VIDEO = "--from-video" in ARGV
ALLOW_METERED = "--allow-metered" in ARGV
FRAME_CACHE = r"R:\peach-data\generated\boards\_frames"

LEGACY = r"R:\Resources\Intake\snapshots"
CURRENT = r"R:\peach-data\generated\snapshots"


def rebase(path: str) -> str:
    return CURRENT + path[len(LEGACY):] if path.startswith(LEGACY) else path


def cell_height(path: str) -> int | None:
    """抽帧图宽固定 1440 / 3 列；高 <1000 视为单行，否则按三行推算格高。

    返回 None 表示这张不是接触表（比如直接从视频取的单帧），整张用即可。
    """
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


def grab_frame(job: tuple[str, float]) -> str | None:
    """\u4ece\u89c6\u9891\u53d6\u4e00\u5e27\u5b58\u8fdb\u7f13\u5b58\uff0c\u8fd4\u56de\u56fe\u7247\u8def\u5f84\u3002\u5df2\u7f13\u5b58\u5219\u76f4\u63a5\u8fd4\u56de\uff0c\u4e0d\u91cd\u590d\u8d70\u7f51\u7edc\u3002"""
    path, duration = job
    dst = os.path.join(FRAME_CACHE, hashlib.sha1(path.encode("utf-8", "ignore")).hexdigest()[:16] + ".jpg")
    if os.path.exists(dst):
        return dst
    seek = int((duration or 60) * 0.3)
    try:
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-ss", str(seek), "-i", path,
             "-frames:v", "1", "-vf", "scale=480:-1", dst],
            capture_output=True, timeout=240)
    except subprocess.TimeoutExpired:
        return None
    return dst if os.path.exists(dst) and os.path.getsize(dst) > 0 else None


def build(paths: list[str], dst: str) -> bool:
    """每张裁首格 → 统一装进 360x360 → 拼 3x3。"""
    inputs, filters, labels = [], [], []
    for src in paths:
        ch = cell_height(src)
        idx = len(labels)
        inputs += ["-i", src]
        # 接触表裁首格；直接取的单帧整张用
        crop = f"crop=480:{ch}:0:0," if ch else ""
        filters.append(
            f"[{idx}:v]{crop}"
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


def from_video() -> int:
    """给还没有抽帧图的创作者出板：每人抽 9 个视频各取 1 帧。"""
    if not ALLOW_METERED:
        print("拒绝：--from-video 会读云端视频，PikPak 是计费来源。确认要花流量再加 --allow-metered")
        return 1
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(FRAME_CACHE, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT creator, path, duration FROM asset WHERE medium='video' "
        "AND creator IS NOT NULL AND creator<>'' "
        "AND id NOT IN (SELECT asset_id FROM asset_tag)").fetchall()
    conn.close()

    by_creator: dict[str, list[tuple[str, float]]] = collections.defaultdict(list)
    for creator, path, duration in rows:
        by_creator[creator].append((path, duration or 60))

    ranked = sorted(by_creator.items(), key=lambda kv: -len(kv[1]))[:TOP]
    done = {f.split("_", 1)[1].rsplit("_", 1)[0] for f in os.listdir(OUTDIR)
            if f.endswith(".jpg")}
    ranked = [(c, v) for c, v in ranked if safe(c) not in done]
    print(f"待出板 {len(ranked)} 位，覆盖 {sum(len(v) for _, v in ranked)} 条待打标视频；"
          f"并发 {WORKERS}")

    # 先把所有需要的帧一次性并发抓完 —— 逐个创作者串行会浪费掉并发
    jobs: list[tuple[str, float]] = []
    for creator, items in ranked:
        random.Random(creator).shuffle(items)
        jobs += items[:PER]
    print(f"需要 {len(jobs)} 帧，单帧实测 25~40 秒，预计 {len(jobs)*32/WORKERS/60:.0f} 分钟")

    got: dict[tuple[str, float], str] = {}
    t0 = time.time()
    with cf.ThreadPoolExecutor(WORKERS) as pool:
        for i, (job, out) in enumerate(zip(jobs, pool.map(grab_frame, jobs)), 1):
            if out:
                got[job] = out
            if i % 25 == 0:
                rate = i / max(time.time() - t0, 1) * 60
                print(f"  {i}/{len(jobs)} 帧  成功 {len(got)}  {rate:.1f} 帧/分  "
                      f"剩 {(len(jobs)-i)/max(rate,0.1):.0f} 分钟", flush=True)

    made = 0
    for rank, (creator, items) in enumerate(ranked, 1):
        frames = [got[j] for j in items[:PER] if j in got]
        if len(frames) < 4:
            print(f"  {rank:>2}. {creator[:26]:<26} 可用帧仅 {len(frames)}，跳过")
            continue
        dst = os.path.join(OUTDIR, f"v{rank:02d}_{safe(creator)}_{len(items)}.jpg")
        if build(frames, dst):
            made += 1
            print(f"  {rank:>2}. {creator[:26]:<26} 视频{len(items):>4}  帧{len(frames)}  → {os.path.basename(dst)}")
    print(f"\n生成 {made} 张 → {OUTDIR}")
    return 0


def main() -> int:
    if FROM_VIDEO:
        return from_video()
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
