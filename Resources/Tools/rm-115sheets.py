#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
115 D 类目录批量识别页 —— 每个目录出一张（最多 9 个视频，每视频抽 1 帧）。

目的：一张图认一个目录的归属，而不是一张图认一个文件。
1,444 个 D 类目录太多，按体积降序处理，先啃大的。

115 直连不计费，只花时间。可随时中断重开（已生成的跳过）。

用法: python rm-115sheets.py [--top 80] [--workers 4]
"""
import os, sys, csv, time, math, sqlite3, subprocess, tempfile, shutil, threading, queue

BIN = r"C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin"
FFMPEG = os.path.join(BIN, "ffmpeg.exe")
DB = r"R:\Resources\Intake\ledger.db"
CSVF = r"R:\Resources\Migration_Logs\115-目录归类.csv"
OUTROOT = r"R:\Resources\Intake\snapshots\idsheets-115"
LOG = r"R:\Resources\Migration_Logs\115sheets-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))

a = sys.argv[1:]
def opt(n, d, cast=str): return cast(a[a.index(n) + 1]) if n in a else d
TOP = opt("--top", 80, int)
W = opt("--workers", 4, int)
PER, COLS, TW, TH = 9, 3, 760, 560

os.makedirs(OUTROOT, exist_ok=True)
logf = open(LOG, "w", encoding="utf-8", buffering=1)
lock = threading.RLock()      # 必须可重入：worker 持锁时会调 log()
def log(s):
    with lock:
        line = f"[{time.strftime('%H:%M:%S')}] {s}"
        print(line, flush=True); logf.write(line + "\n")

# ── D 类目录，按体积降序 ──
dirs = [r for r in csv.DictReader(open(CSVF, encoding="utf-8-sig"))
        if r["分类"] == "D-需抽帧"]
dirs.sort(key=lambda r: -float(r["体积GB"]))
dirs = dirs[:TOP]
log(f"D 类目录取前 {len(dirs)} 个（按体积），合计 {sum(float(r['体积GB']) for r in dirs)/1024:.2f} TB")

c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
tasks = []
for r in dirs:
    d = r["目录"]
    rows = c.execute("""SELECT path,duration FROM asset WHERE location='115' AND medium='video'
                        AND duration>5 AND path LIKE ? ORDER BY size DESC LIMIT ?""",
                     ("B:\\" + d + "%", PER)).fetchall()
    if rows:
        tasks.append((d, rows))
c.close()
log(f"可出图的目录 {len(tasks)} 个")

safe = lambda s: "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s)[:60]
q = queue.Queue()
for t in tasks: q.put(t)
done = [0]; made = [0]; t0 = time.time()

def worker():
    while True:
        try: d, rows = q.get_nowait()
        except queue.Empty: return
        dst = os.path.join(OUTROOT, safe(d) + ".jpg")
        if os.path.exists(dst) and os.path.getsize(dst) > 4096:
            with lock: done[0] += 1
            continue
        tmpd = tempfile.mkdtemp(prefix="s115_")
        try:
            n = 0
            for path, dur in rows:
                f = os.path.join(tmpd, f"s{n:02d}.jpg")
                try:
                    subprocess.run(
                        [FFMPEG, "-y", "-v", "error", "-rw_timeout", "8000000",
                         "-ss", f"{dur*0.45:.2f}", "-i", path, "-frames:v", "1",
                         "-vf", f"scale={TW}:{TH}:force_original_aspect_ratio=decrease,"
                                f"pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2:black",
                         "-q:v", "3", f], capture_output=True, timeout=60)
                except Exception:
                    pass
                if os.path.exists(f) and os.path.getsize(f) > 1024: n += 1
                elif os.path.exists(f): os.remove(f)
            if n:
                rowsn = math.ceil(n / COLS)
                subprocess.run([FFMPEG, "-y", "-v", "error",
                                "-i", os.path.join(tmpd, "s%02d.jpg"),
                                "-filter_complex", f"tile={COLS}x{rowsn}", "-q:v", "3", dst],
                               capture_output=True, timeout=120)
                if os.path.exists(dst):
                    with lock: made[0] += 1
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
        with lock:
            done[0] += 1
            if done[0] % 10 == 0:
                el = time.time() - t0
                log(f"{done[0]}/{len(tasks)}  出图 {made[0]}  {done[0]/el*60:.0f} 个/分  "
                    f"剩余 {(len(tasks)-done[0])/(done[0]/el)/60:.0f} 分钟")

ts = [threading.Thread(target=worker, daemon=True) for _ in range(W)]
for t in ts: t.start()
for t in ts: t.join()
log(f"完成 {done[0]} 个目录，出图 {made[0]} 张，耗时 {(time.time()-t0)/60:.1f} 分钟")
log(f"→ {OUTROOT}")
