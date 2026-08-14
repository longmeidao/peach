#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带流量计量的 ffprobe 试跑 —— 先量清楚每个文件到底吃多少流量，再决定要不要全库跑。

背景（血的教训）：之前只测了**耗时**（0.37~1.36 秒/帧），据此在方案里写下
「seek 抽帧成本与文件大小无关，可以全库做」。但耗时快 ≠ 流量小 ——
CloudDrive2 按块预读，实测每个文件产生约 34 MB 流量，13,000 个文件烧掉 566 GB。

本脚本在探测前后读网卡计数器和 CloudDrive 缓存实际落盘量，给出真实的
「每文件流量」，用来外推全库成本。

用法: python rm-trafficprobe.py [--n 50] [--location 115] [--workers 4]
"""
import os, sys, time, json, sqlite3, subprocess, ctypes, threading, queue
from ctypes import wintypes

FFPROBE = r"C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe"
DB = r"R:\Resources\Intake\ledger.db"
CACHE = os.path.expandvars(r"%LOCALAPPDATA%\CloudDrive.WinUI\file_buffer_cache")

a = sys.argv[1:]
def opt(n, d, cast=str): return cast(a[a.index(n) + 1]) if n in a else d
N = opt("--n", 50, int)
LOC = opt("--location", None)
W = opt("--workers", 4, int)

# ---- 计量工具 ----
GetCompressedFileSizeW = ctypes.windll.kernel32.GetCompressedFileSizeW
GetCompressedFileSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
GetCompressedFileSizeW.restype = wintypes.DWORD

def cache_ondisk():
    tot = 0
    for root, _, fs in os.walk(CACHE):
        for f in fs:
            hi = wintypes.DWORD(0)
            lo = GetCompressedFileSizeW(os.path.join(root, f), ctypes.byref(hi))
            if lo != 0xFFFFFFFF:
                tot += (hi.value << 32) + lo
    return tot

def nic_rx():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
        "(Get-NetAdapterStatistics | Measure-Object ReceivedBytes -Sum).Sum"],
        capture_output=True, text=True).stdout.strip()
    try: return int(out)
    except ValueError: return 0

# ---- 取样本 ----
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
sql = ("SELECT id,path,size FROM asset WHERE medium='video' AND duration IS NULL "
       "AND location != 'online'")
if LOC: sql += f" AND location='{LOC}'"
sql += f" ORDER BY RANDOM() LIMIT {N}"
rows = c.execute(sql).fetchall()
c.close()
if not rows:
    print("没有待处理样本"); sys.exit(0)
print(f"样本 {len(rows)} 个   位置={LOC or '全部'}   并发={W}")
print(f"样本总体积 {sum(r[2] or 0 for r in rows)/1024**3:.2f} GB\n")

print("测量基线…")
rx0, cache0 = nic_rx(), cache_ondisk()
t0 = time.time()

q = queue.Queue()
for r in rows: q.put(r)
res = []
lock = threading.Lock()

def probe(path):
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-rw_timeout", "8000000", "-select_streams", "v:0",
         "-show_entries", "format=duration:stream=width,height,codec_name",
         "-of", "json", path], capture_output=True, timeout=25)
    return json.loads(r.stdout or b"{}")

def worker():
    while True:
        try: aid, path, size = q.get_nowait()
        except queue.Empty: return
        ok = False
        try:
            j = probe(path)
            ok = bool((j.get("format") or {}).get("duration"))
        except Exception:
            pass
        with lock: res.append(ok)

ts = [threading.Thread(target=worker) for _ in range(W)]
for t in ts: t.start()
for t in ts: t.join()

el = time.time() - t0
time.sleep(3)          # 等 CloudDrive 把缓存落盘
rx1, cache1 = nic_rx(), cache_ondisk()

n = len(res); ok = sum(res)
d_rx = max(0, rx1 - rx0); d_cache = max(0, cache1 - cache0)
print(f"\n完成 {n} 个（成功 {ok}，失败 {n-ok}），耗时 {el:.0f}s")
print(f"\n{'':<20}{'总量':>12}{'每文件':>12}")
print(f"  {'网卡下行':<18}{d_rx/1024**3:>10.2f} GB{d_rx/n/1024**2:>10.1f} MB")
print(f"  {'缓存落盘增量':<18}{d_cache/1024**3:>10.2f} GB{d_cache/n/1024**2:>10.1f} MB")

rest = 0
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
q2 = ("SELECT COUNT(*) FROM asset WHERE medium='video' AND duration IS NULL AND location!='online'")
if LOC: q2 += f" AND location='{LOC}'"
rest = c.execute(q2).fetchone()[0]
c.close()
per = d_rx / n if n else 0
print(f"\n外推：剩余 {rest:,} 个未探测 → 预计还需 {rest*per/1024**3:.0f} GB 流量")
print(f"（改配置前实测是 34 MB/文件；现在是 {per/1024**2:.1f} MB/文件）")
