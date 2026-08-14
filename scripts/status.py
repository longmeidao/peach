#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一屏看完项目状态。无副作用，随时可跑。"""
import os, sqlite3, glob, time, subprocess

DB = r"R:\peach-data\database\ledger.db"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
q1 = lambda s: c.execute(s).fetchone()[0]
qa = lambda s: c.execute(s).fetchall()

print("=" * 62)
print("  账本")
print("=" * 62)
for loc, n, sz in qa("SELECT location,COUNT(*),COALESCE(SUM(size),0) FROM asset GROUP BY 1 ORDER BY 3 DESC"):
    print(f"  {loc:<10}{n:>9,} 条{sz/1024**4:>10.2f} TB")
print(f"  {'合计':<10}{q1('SELECT COUNT(*) FROM asset'):>9,} 条"
      f"{q1('SELECT COALESCE(SUM(size),0) FROM asset')/1024**4:>10.2f} TB")

print("\n  媒介构成：")
for m, n, sz in qa("SELECT medium,COUNT(*),COALESCE(SUM(size),0) FROM asset GROUP BY 1 ORDER BY 2 DESC"):
    print(f"    {m or '?':<14}{n:>8,}{sz/1024**3:>11.1f} GB")

print("\n" + "=" * 62)
print("  加工进度")
print("=" * 62)
tv = q1("SELECT COUNT(*) FROM asset WHERE medium='video' AND location!='online'")
for label, sql in (
    ("有时长 (ffprobe)", "SELECT COUNT(*) FROM asset WHERE medium='video' AND location!='online' AND duration IS NOT NULL"),
    ("有接触表",         "SELECT COUNT(*) FROM asset WHERE medium='video' AND location!='online' AND snapshot_path IS NOT NULL"),
    ("有哈希",           "SELECT COUNT(*) FROM asset WHERE medium='video' AND location!='online' AND hash IS NOT NULL"),
    ("有创作者归属",     "SELECT COUNT(*) FROM asset WHERE medium='video' AND location!='online' AND creator IS NOT NULL AND creator!=''"),
    ("有消费记录",       "SELECT COUNT(*) FROM asset WHERE medium='video' AND location!='online' AND (play_count>0 OR rating IS NOT NULL)"),
):
    n = q1(sql)
    pct = n / tv * 100 if tv else 0
    bar = "█" * int(pct / 4)
    print(f"  {label:<18}{n:>8,} / {tv:,}  {pct:5.1f}%  {bar}")

print("\n  情境层：")
for col, nm in (("ctx_length", "时长档"), ("ctx_orient", "屏向"), ("ctx_quality", "画质")):
    rows = qa(f"SELECT {col},COUNT(*) FROM asset WHERE {col} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
    if rows:
        print(f"    {nm:<8}" + "  ".join(f"{k}={v:,}" for k, v in rows))

print("\n" + "=" * 62)
print("  正在跑的后台任务")
print("=" * 62)
try:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq ffprobe.exe"],
                         capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    n = out.lower().count("ffprobe.exe")
    out2 = subprocess.run(["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe"],
                          capture_output=True, text=True, encoding="gbk", errors="ignore").stdout
    m = out2.lower().count("ffmpeg.exe")
    print(f"  ffprobe 进程 {n}   ffmpeg 进程 {m}")
except Exception:
    pass

for pat, nm in (("probe-*.log", "ffprobe"), ("sheets-*.log", "接触表"),
                ("sha1-*.log", "SHA1"), ("cloud-delete-*.log", "删除")):
    fs = sorted(glob.glob(rf"R:\peach-data\logs\{pat}"), key=os.path.getmtime)
    if not fs:
        continue
    f = fs[-1]
    age = (time.time() - os.path.getmtime(f)) / 60
    tail = [l.rstrip() for l in open(f, encoding="utf-8", errors="replace").readlines()[-1:]]
    print(f"\n  [{nm}] {os.path.basename(f)}  ({age:.0f} 分钟前更新)")
    for t in tail:
        print(f"    {t[:100]}")
c.close()
