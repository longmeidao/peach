#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全库关键帧接触表 —— 无人值守。给 ledger 里每个视频抽 9 帧拼成一张图。

用途：日后不打开文件就能认内容；识别创作者水印；判定行为标签。
成本：实测 seek 抽帧 0.37–1.36 秒/帧且与文件大小无关，一个视频 6–14 秒。

与 scripts/probe.py 一样设计成可随时中断重启：
  * 只处理 snapshot_path IS NULL 的记录
  * 产物落地后才写库，进程被杀不会留下"记了但没图"的空档
  * 图已存在则直接补登记，不重复抽帧

用法（双击 run-sheets.cmd，或）：
    python scripts/sheets.py [--workers 4] [--location 115] [--frames 9] [--limit N]
"""
import os, sys, time, hashlib, sqlite3, subprocess, threading, queue, tempfile, shutil

from peach.config import FFMPEG_DIR
from peach.ffmpeg import FFmpegResolver

DB = r"R:\peach-data\database\ledger.db"
_FFMPEG_RESOLVER = FFmpegResolver(FFMPEG_DIR)
_FFMPEG_CHOICE = _FFMPEG_RESOLVER.ffmpeg()
_FFPROBE_CHOICE = _FFMPEG_RESOLVER.ffprobe()
if _FFMPEG_CHOICE is None or _FFPROBE_CHOICE is None:
    raise RuntimeError("ffmpeg/ffprobe are unavailable; install them under Peach data tools or PATH")
FFMPEG, FFPROBE = str(_FFMPEG_CHOICE.path), str(_FFPROBE_CHOICE.path)
OUTROOT = r"R:\peach-data\generated\snapshots\cloud"
LOG = r"R:\peach-data\logs\sheets-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))

a = sys.argv[1:]
def opt(n, d, cast=str): return cast(a[a.index(n) + 1]) if n in a else d
WORKERS = opt("--workers", 4, int)
LOCATION = opt("--location", None)
FRAMES = opt("--frames", 9, int)
LIMIT = opt("--limit", 0, int)
COLS = 3
TILE_W = 480

os.makedirs(OUTROOT, exist_ok=True)
logf = open(LOG, "w", encoding="utf-8", buffering=1)
lock = threading.RLock()   # 必须可重入：worker 持锁时会调 log()，而 log() 内部还要再拿一次锁
def log(s):
    with lock:
        line = f"[{time.strftime('%H:%M:%S')}] {s}"
        print(line, flush=True); logf.write(line + "\n")

def outpath(location, path):
    h = hashlib.sha1(path.encode("utf-8", "ignore")).hexdigest()[:16]
    d = os.path.join(OUTROOT, location, h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, h + ".jpg")

def make_sheet(path, dur, dst):
    """抽 N 帧拼接成接触表。

    ⚠ 不能用 select 滤镜按时间戳挑帧 —— 那会**线性解码整个视频**，实测 4 分钟只出 3 张图。
    必须用 -ss 放在 -i 之前做输入端 seek：ffmpeg 只读 moov atom + 目标 GOP，
    实测 0.37~1.36 秒/帧且与文件大小无关（8.5 GB 和 0.36 GB 一样快）。
    """
    if not dur or dur < 2:
        return False
    tmpd = tempfile.mkdtemp(prefix="sheet_")
    try:
        got = []
        for i in range(FRAMES):
            ts = dur * (0.03 + 0.94 * (i + 0.5) / FRAMES)
            f = os.path.join(tmpd, f"{i:02d}.jpg")
            r = subprocess.run(
                [FFMPEG, "-y", "-v", "error", "-rw_timeout", "8000000",
                 "-ss", f"{ts:.2f}", "-i", path,
                 "-frames:v", "1", "-vf", f"scale={TILE_W}:-1", "-q:v", "4", f],
                capture_output=True, timeout=45)
            if os.path.exists(f) and os.path.getsize(f) > 1024:
                got.append(f)
        if len(got) < 2:
            return False
        # 重排成连续编号供 image2 读取
        for n, f in enumerate(got):
            tgt = os.path.join(tmpd, f"s{n:02d}.jpg")
            if f != tgt:
                os.replace(f, tgt)
        rows = (len(got) + COLS - 1) // COLS
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-i", os.path.join(tmpd, "s%02d.jpg"),
             "-filter_complex", f"tile={COLS}x{rows}", "-q:v", "4", dst],
            capture_output=True, timeout=60)
        return os.path.exists(dst) and os.path.getsize(dst) > 4096
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

# ---------- 取任务 ----------
c = sqlite3.connect(DB)
# -- 磁盘闸门（2026-08-14 加）--------------------------------
# 教训：这些任务读网盘会把块缓存写到 CloudDrive.WinUI\file_buffer_cache。
#       跑了一整天后该目录涨到 910 GB（配置上限写的 32 GB，LRU 没拦住），
#       C 盘从 22 GB 可用掉到 0.1 GB，我全程没发现，是用户报错才查出来。
#       所以：启动前检查，低于阈值直接拒绝。
import shutil as _sh
MIN_FREE_GB = float(sys.argv[sys.argv.index("--min-free") + 1]) if "--min-free" in sys.argv else 40.0
def _free_gb(drive="C:" + chr(92)):
    try:
        return _sh.disk_usage(drive).free / 1024**3
    except Exception:
        return 999.0
def disk_guard():
    f = _free_gb()
    if f < MIN_FREE_GB:
        print("[stop] C 盘仅剩 %.1f GB（阈值 %.0f GB）—— 拒绝启动。"
              "先清 CloudDrive 的 file_buffer_cache" % (f, MIN_FREE_GB))
        return False
    return True
if not disk_guard():
    sys.exit(3)
# -----------------------------------------------------------

# ── 计费来源闸门（2026-08-14 加）──────────────────────────────
# 教训：这两个脚本不带 --location 启动了一次，覆盖到 PikPak，
#       11 小时烧掉 677 GB 代理流量。知道要限制、脚本也支持，就是启动时没加。
#       所以把限制写死：默认拒绝计费来源，要跑必须显式 --allow-metered。
METERED = {"pikpak", "online"}
ALLOW_METERED = "--allow-metered" in sys.argv
if not LOCATION:
    LOCATION = None
if not ALLOW_METERED:
    _excl = " AND location NOT IN ('" + "','".join(sorted(METERED)) + "')"
    if LOCATION in METERED:
        print(f"拒绝：{LOCATION} 是计费来源。确认要花流量再加 --allow-metered")
        sys.exit(2)
else:
    _excl = ""
    print("⚠️  已开启 --allow-metered：将读取 PikPak，产生计费流量")
# ─────────────────────────────────────────────────────────────

sql = ("SELECT id,location,path,duration FROM asset WHERE medium='video' "
       "AND snapshot_path IS NULL AND location != 'online' AND duration > 2")
if LOCATION: sql += f" AND location='{LOCATION}'"
sql += _excl
sql += " ORDER BY size DESC"
if LIMIT: sql += f" LIMIT {LIMIT}"
tasks = c.execute(sql).fetchall()
c.close()
total = len(tasks)
log(f"待处理 {total:,} 个视频  workers={WORKERS} frames={FRAMES}  日志={LOG}")
if not total:
    log("没有待处理项（可能需要先跑 scripts/probe.py 拿到 duration）"); sys.exit(0)

q = queue.Queue()
for t in tasks: q.put(t)
results = queue.Queue()
done = [0]; failed = [0]; skipped = [0]; t0 = time.time()

def worker():
    while True:
        try:
            aid, loc, path, dur = q.get_nowait()
        except queue.Empty:
            return
        dst = outpath(loc, path)
        try:
            if os.path.exists(dst) and os.path.getsize(dst) > 4096:
                results.put((dst, aid));
                with lock: skipped[0] += 1
            elif make_sheet(path, dur, dst):
                results.put((dst, aid))
            else:
                with lock: failed[0] += 1
        except Exception:
            with lock: failed[0] += 1
        finally:
            with lock:
                done[0] += 1
                if done[0] % 100 == 0:
                    el = time.time() - t0
                    rate = done[0] / el if el else 0
                    log(f"{done[0]:,}/{total:,}  失败 {failed[0]}  已存在 {skipped[0]}  "
                        f"{rate*60:.0f} 个/分  预计剩余 {(total-done[0])/rate/3600 if rate else 0:.1f} 小时")

threads = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
for t in threads: t.start()

conn = sqlite3.connect(DB, timeout=60)
buf = []
while any(t.is_alive() for t in threads) or not results.empty():
    try: buf.append(results.get(timeout=2))
    except queue.Empty: pass
    if len(buf) >= 50:
        conn.executemany("UPDATE asset SET snapshot_path=? WHERE id=?", buf); conn.commit(); buf.clear()
if buf:
    conn.executemany("UPDATE asset SET snapshot_path=? WHERE id=?", buf); conn.commit()

el = time.time() - t0
log(f"完成 {done[0]:,}  失败 {failed[0]}  已存在 {skipped[0]}  耗时 {el/3600:.2f} 小时")
n = conn.execute("SELECT COUNT(*) FROM asset WHERE snapshot_path IS NOT NULL").fetchone()[0]
log(f"账本中已有接触表的资产: {n:,}")
conn.close(); logf.close()
