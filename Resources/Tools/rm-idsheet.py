#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量识别页 —— 每个视频抽 1 帧，12 个拼成一页，供人/AI 肉眼读水印认创作者。

与 rm-sheets.py 的区别：
  rm-sheets  = 每个视频 9 帧 → 看单个视频讲了什么
  rm-idsheet = 每个视频 1 帧 → 一页看 12 个视频的水印，用于批量归属

抽帧点选在 45% 处（片中通常水印最稳定，片头片尾常有转场/黑屏）。

用法:
    python rm-idsheet.py "合集-足交 多创作者"            # 指定目录
    python rm-idsheet.py "xa" --per-page 12 --width 640
"""
import os, sys, subprocess, tempfile, shutil, sqlite3, math

BIN = r"C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin"
FFMPEG = os.path.join(BIN, "ffmpeg.exe")
DB = r"R:\Resources\Intake\ledger.db"
OUTROOT = r"R:\Resources\Intake\snapshots\idsheets"
PREFIX = "R:\\Media\\创作者\\"

a = sys.argv[1:]
if not a:
    print(__doc__); sys.exit(1)
TARGET = a[0]
def opt(n, d, cast=str): return cast(a[a.index(n) + 1]) if n in a else d
PER = opt("--per-page", 9, int)
W = opt("--width", 760, int)
H = opt("--height", 560, int)     # 统一画布，竖屏会左右留黑，但水印仍可读
COLS = opt("--cols", 3, int)
LIMIT = opt("--limit", 0, int)

os.makedirs(OUTROOT, exist_ok=True)
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = c.execute(
    """SELECT path, duration, name FROM asset
       WHERE location='local' AND medium='video' AND duration>5 AND path LIKE ?
       ORDER BY size DESC""", (PREFIX + TARGET + "\\%",)).fetchall()
c.close()
if LIMIT: rows = rows[:LIMIT]
print(f"目标目录: {TARGET}   视频 {len(rows)} 个")
if not rows:
    print("没找到（确认目录名，且已跑过 rm-probe 拿到 duration）"); sys.exit(1)

pages = math.ceil(len(rows) / PER)
safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in TARGET)[:40]
made = []
for pi in range(pages):
    chunk = rows[pi * PER:(pi + 1) * PER]
    tmpd = tempfile.mkdtemp(prefix="idsheet_")
    try:
        n = 0
        for path, dur, name in chunk:
            f = os.path.join(tmpd, f"s{n:02d}.jpg")
            # ⚠ tile 滤镜要求所有输入尺寸完全一致。竖屏/横屏混排时用 scale=W:-1
            #   会得到不同高度，除第一帧外全被丢弃（拼出来一片黑）。
            #   必须 force_original_aspect_ratio=decrease + pad 补成统一画布。
            subprocess.run(
                [FFMPEG, "-y", "-v", "error", "-rw_timeout", "8000000",
                 "-ss", f"{dur*0.45:.2f}", "-i", path, "-frames:v", "1",
                 "-vf", (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                         f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black"),
                 "-q:v", "3", f],
                capture_output=True, timeout=60)
            if os.path.exists(f) and os.path.getsize(f) > 1024:
                n += 1
            elif os.path.exists(f):
                os.remove(f)
        if not n:
            continue
        rowsn = math.ceil(n / COLS)
        dst = os.path.join(OUTROOT, f"{safe}-p{pi+1:02d}.jpg")
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-i", os.path.join(tmpd, "s%02d.jpg"),
             "-filter_complex", f"tile={COLS}x{rowsn}", "-q:v", "3", dst],
            capture_output=True, timeout=120)
        if os.path.exists(dst):
            made.append((dst, [x[2] for x in chunk]))
            print(f"  第 {pi+1}/{pages} 页: {n} 帧 → {os.path.basename(dst)}")
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

idx = os.path.join(OUTROOT, f"{safe}-索引.txt")
with open(idx, "w", encoding="utf-8") as f:
    f.write(f"{TARGET}  共 {len(rows)} 个视频，每页 {PER} 个，{COLS} 列\n")
    f.write("页内顺序：从左到右、从上到下\n\n")
    for p, names in made:
        f.write(f"=== {os.path.basename(p)} ===\n")
        for i, nm in enumerate(names, 1):
            f.write(f"  {i:>2}. {nm}\n")
        f.write("\n")
print(f"\n共 {len(made)} 页 → {OUTROOT}")
print(f"页内文件名对照 → {idx}")
