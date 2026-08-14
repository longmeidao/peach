#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全库 ffprobe —— 无人值守。给 ledger 里的视频补事实层与情境层。

设计成可以关掉终端、跑几个小时、随时中断重启：
  * 只处理 duration IS NULL 的记录，所以重启即续跑，不重复劳动
  * 多线程（默认 6），每完成一批就提交，进程被杀也不丢进度
  * 全部输出写日志文件，不依赖终端
  * 对网盘限速（每个请求间隔 workers*interval），避免触发 115 风控
  * 单个文件超时 60s 直接跳过并标记，不卡住整体

用法（双击 run-probe.cmd 即可，或）：
    python scripts/probe.py [--workers 6] [--location 115] [--interval 0.15] [--limit N]
"""
import os, sys, time, json, sqlite3, subprocess, threading, queue

DB = r"R:\peach-data\database\ledger.db"
FFPROBE = r"C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe"
LOG = r"R:\peach-data\logs\probe-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))

a = sys.argv[1:]
def opt(name, default, cast=str):
    return cast(a[a.index(name) + 1]) if name in a else default
WORKERS = opt("--workers", 6, int)
LOCATION = opt("--location", None)
INTERVAL = opt("--interval", 0.15, float)
LIMIT = opt("--limit", 0, int)

# ---------- 单实例保护 ----------
# 多个实例同时跑会互抢 SQLite 写锁，全部卡死（实测踩过：三个实例并存时 ffprobe 数归零）
LOCKFILE = r"R:\peach-data\state\.probe.lock"
try:
    _lock = open(LOCKFILE, "x")
    _lock.write(str(os.getpid()))
    _lock.flush()
except FileExistsError:
    try:
        old = open(LOCKFILE).read().strip()
        alive = subprocess.run(["tasklist", "/FI", f"PID eq {old}"],
                               capture_output=True, text=True, errors="ignore").stdout
        if old and old in alive:
            print(f"已有实例在跑（PID {old}），退出。要强制重来请删除 {LOCKFILE}")
            sys.exit(0)
    except Exception:
        pass
    os.remove(LOCKFILE)
    _lock = open(LOCKFILE, "x"); _lock.write(str(os.getpid())); _lock.flush()

import atexit
def _unlock():
    try:
        _lock.close()
    except Exception:
        pass
    try:
        os.remove(LOCKFILE)
    except OSError:
        pass
atexit.register(_unlock)

logf = open(LOG, "w", encoding="utf-8", buffering=1)
# 必须是 RLock：worker 在持有锁的情况下调用 log()，而 log() 内部还要再拿一次锁。
# 普通 Lock 不可重入，会让第一个触发日志的 worker 自锁死，其余 worker 全部堵在同一把锁上，
# 表现为「进程活着、CPU 接近 0、ffprobe 子进程数为 0、日志不推进」—— 排查了很久才定位。
lock = threading.RLock()
def log(s):
    with lock:
        line = f"[{time.strftime('%H:%M:%S')}] {s}"
        print(line, flush=True); logf.write(line + "\n")

def ctx_of(w, h, dur):
    orient = quality = length = None
    if w and h:
        orient = "竖屏" if h > w else "横屏"
        m = max(w, h)
        quality = ("4K" if m >= 3000 else "2K" if m >= 1900 else "1080P" if m >= 1300
                   else "720P" if m >= 900 else "低画质")
    if dur:
        length = "速食" if dur < 300 else "短" if dur < 900 else "中" if dur < 2400 else "长"
    return length, orient, quality

def probe(path):
    """只读第一条视频流的指定字段。
    实测：不加 -select_streams 的完整 -show_streams 要 0.6~9.6 秒（ffprobe 会深度探测所有流），
    限定后降到 0.04~0.07 秒，快 20~160 倍。音轨检测另算约 1 秒/文件，不值得，留空后续按需补。"""
    # -rw_timeout：网络读卡住时提前放弃（微秒）。坏文件卡满超时是吞吐的头号杀手：
    # 实测 50 个里 4 个坏文件各占满 60 秒，12 个 worker 长期有几个被占着，整体降到 16 个/分钟。
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-rw_timeout", "8000000",
         "-select_streams", "v:0",
         "-show_entries", "format=duration:stream=width,height,codec_name,avg_frame_rate",
         "-of", "json", path],
        capture_output=True, timeout=20)
    j = json.loads(r.stdout or b"{}")
    dur = float((j.get("format") or {}).get("duration") or 0)
    st = (j.get("streams") or [{}])[0]
    fps = 0.0
    try:
        n, d = (st.get("avg_frame_rate") or "0/1").split("/")
        fps = float(n) / float(d) if float(d) else 0.0
    except Exception:
        pass
    return dur, int(st.get("width") or 0), int(st.get("height") or 0), st.get("codec_name"), fps, None

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

sql = ("SELECT id,path FROM asset WHERE medium='video' AND duration IS NULL "
       "AND location != 'online'")
if LOCATION:
    sql += f" AND location='{LOCATION}'"
sql += _excl
# 从小到大：大文件的 moov 常在末尾，要多一次网络往返；小文件先做能更快出成果。
# 实测这是延迟受限而非带宽受限的任务（115 单次 0.87s / PikPak 1.56s），所以并发几乎线性加速。
sql += " ORDER BY size ASC"
if LIMIT:
    sql += f" LIMIT {LIMIT}"
tasks = c.execute(sql).fetchall()
c.close()
total = len(tasks)
log(f"待处理 {total:,} 个视频   workers={WORKERS}  interval={INTERVAL}s  日志={LOG}")
if not total:
    log("没有待处理项，退出"); sys.exit(0)

q = queue.Queue()
for t in tasks: q.put(t)
results = queue.Queue()
done = [0]; failed = [0]; t0 = time.time()

def worker():
    while True:
        try:
            aid, path = q.get_nowait()
        except queue.Empty:
            return
        try:
            dur, w, h, vc, fps, au = probe(path)
            L, O, Q = ctx_of(w, h, dur)
            results.put((dur, w, h, vc, fps, au, L, O, Q, aid))
        except Exception as e:
            results.put((-1, 0, 0, None, 0, 0, None, None, None, aid))
            with lock: failed[0] += 1
        finally:
            with lock:
                done[0] += 1
                if done[0] % 50 == 0:
                    el = time.time() - t0
                    rate = done[0] / el if el else 0
                    eta = (total - done[0]) / rate / 60 if rate else 0
                    log(f"{done[0]:,}/{total:,}  失败 {failed[0]}  "
                        f"{rate:.1f} 个/秒  预计剩余 {eta:.0f} 分钟")
            time.sleep(INTERVAL)

threads = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
for t in threads: t.start()

# 主线程负责写库（sqlite 单写者）
conn = sqlite3.connect(DB, timeout=120)
conn.execute("PRAGMA journal_mode=WAL")     # 允许读者与写者并存，status/suggest 可随时查
conn.execute("PRAGMA busy_timeout=120000")
buf = []
UP = """UPDATE asset SET duration=?,width=?,height=?,vcodec=?,fps=?,has_audio=?,
        ctx_length=?,ctx_orient=?,ctx_quality=? WHERE id=?"""
while any(t.is_alive() for t in threads) or not results.empty():
    try:
        buf.append(results.get(timeout=2))
    except queue.Empty:
        pass
    if len(buf) >= 25:                 # 批次小一点，进度可见，也降低写锁持有时间
        conn.executemany(UP, buf); conn.commit(); buf.clear()
if buf:
    conn.executemany(UP, buf); conn.commit()

el = time.time() - t0
log(f"完成 {done[0]:,} 个，失败 {failed[0]}，耗时 {el/60:.1f} 分钟")
row = conn.execute("""SELECT ctx_length,COUNT(*) FROM asset WHERE ctx_length IS NOT NULL
                      GROUP BY 1 ORDER BY 2 DESC""").fetchall()
log("时长档分布: " + "  ".join(f"{k}={v:,}" for k, v in row))
row = conn.execute("""SELECT ctx_orient,COUNT(*) FROM asset WHERE ctx_orient IS NOT NULL
                      GROUP BY 1""").fetchall()
log("屏向分布: " + "  ".join(f"{k}={v:,}" for k, v in row))
conn.close(); logf.close()
