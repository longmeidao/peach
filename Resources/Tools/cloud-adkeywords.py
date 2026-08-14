#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不靠预设词表发现广告文件，并产出「可直接拿去客户端筛选的关键词清单」。

原理：广告/引流文件的特征是**同一个文件名散布在大量不同目录**，而正片文件名几乎不重复。
再叠加体积门槛（广告体积小）和扩展名门槛。

用法: python cloud-adkeywords.py <inventory.csv> [--min-dirs 4] [--out 报告.txt]
"""
import csv, os, re, sys
from collections import Counter, defaultdict

args = sys.argv[1:]
MIN_DIRS = 4
OUT = os.path.expandvars(r"%USERPROFILE%\Desktop\广告关键词.txt")
if "--min-dirs" in args:
    i = args.index("--min-dirs"); MIN_DIRS = int(args[i + 1]); del args[i:i + 2]
if "--out" in args:
    i = args.index("--out"); OUT = args[i + 1]; del args[i:i + 2]
INV = args[0] if args else os.path.expandvars(r"%USERPROFILE%\Desktop\pikpak-inventory.csv")

VIDEO = {".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".mov", ".ts", ".flv", ".rmvb"}
IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
TEXTLIKE = {".txt", ".html", ".htm", ".url", ".mht", ".lnk", ".nfo", ".chm", ".doc", ".docx"}

rows = []
with open(INV, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f):
        try:
            r["size"] = int(r["size"])
        except (TypeError, ValueError):
            r["size"] = 0
        rows.append(r)
print(f"读入 {len(rows):,} 个文件 / {sum(r['size'] for r in rows)/1024**4:.2f} TB")

# 同名文件出现在多少个不同目录
byname = defaultdict(set)
bysize = defaultdict(list)
for r in rows:
    byname[r["name"]].add(r["path"])
    bysize[r["name"]].append(r["size"])

spread = []
for name, dirs in byname.items():
    if len(dirs) < MIN_DIRS:
        continue
    ext = os.path.splitext(name)[1].lower()
    sizes = bysize[name]
    avg = sum(sizes) / len(sizes)
    # 体积门槛：视频 <100MB、图片 <5MB、文本不限、其他 <100MB
    if ext in VIDEO and avg > 100 * 1024**2:
        continue
    if ext in IMAGE and avg > 5 * 1024**2:
        continue
    if ext not in VIDEO and ext not in IMAGE and ext not in TEXTLIKE and avg > 100 * 1024**2:
        continue
    spread.append((len(dirs), len(sizes), avg, sum(sizes), name))
spread.sort(key=lambda x: -x[1])

R, w = [], None
R = []; w = R.append
w(f"广告/引流文件发现报告 —— {os.path.basename(INV)}")
w(f"判据：同一文件名出现在 >= {MIN_DIRS} 个不同目录，且体积在广告区间")
w(f"总体量 {len(rows):,} 文件 / {sum(r['size'] for r in rows)/1024**4:.2f} TB")
w("")
w("=" * 78)
w("一、疑似广告文件（按出现次数排序）")
w("=" * 78)
w(f"  {'次数':>6}{'目录数':>7}{'单个MB':>9}{'合计MB':>10}  文件名")
tot_files = tot_bytes = 0
for ndir, ncopy, avg, tots, name in spread[:200]:
    w(f"  {ncopy:>6,}{ndir:>7,}{avg/1024**2:>9.2f}{tots/1024**2:>10.1f}  {name[:60]}")
    tot_files += ncopy; tot_bytes += tots
w("")
w(f"  合计 {tot_files:,} 个文件 / {tot_bytes/1024**3:.2f} GB")

# ---------- 提炼关键词 ----------
# 从这些文件名里抽公共子串，产出可直接拿去客户端搜索的词
w("")
w("=" * 78)
w("二、可直接用于客户端筛选的关键词")
w("=" * 78)
w("  用法：在 PikPak 网页/客户端的全盘搜索里逐个搜下面的词，确认后批量删。")
w("  「安全」列 = 该词在所有 >100MB 的视频文件名里出现过几次；应为 0，否则可能误伤正片。")
w("")

CJK = re.compile(r"[一-鿿぀-ヿ]{2,10}")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9\.\-]{3,25}")
cand = Counter()
for ndir, ncopy, avg, tots, name in spread:
    base = os.path.splitext(name)[0]
    for m in CJK.findall(base):
        cand[m] += ncopy
    for m in LATIN.findall(base):
        if not re.fullmatch(r"(mp4|jpg|png|avi|wmv|mkv|txt|url|html|zip|rar|part\d*|cd\d|hd|fhd)", m, re.I):
            cand[m.lower()] += ncopy

# 安全性检查：该关键词是否出现在大视频（>100MB）里
bigvids = [r["name"].lower() for r in rows
           if os.path.splitext(r["name"])[1].lower() in VIDEO and r["size"] > 100 * 1024**2]
big_join = "\n".join(bigvids)

w(f"  {'命中数':>7}{'安全':>7}  关键词")
safe_kw = []
for kw, n in cand.most_common(120):
    if n < 3 or len(kw) < 2:
        continue
    risk = big_join.count(kw.lower())
    flag = "OK" if risk == 0 else f"!{risk}"
    w(f"  {n:>7,}{flag:>7}  {kw}")
    if risk == 0:
        safe_kw.append(kw)

w("")
w("=" * 78)
w("三、零风险关键词（在大视频文件名里一次都没出现过，可放心筛选）")
w("=" * 78)
w("  " + " | ".join(safe_kw[:60]))

open(OUT, "w", encoding="utf-8").write("\n".join(R))
print(f"\n疑似广告 {tot_files:,} 个 / {tot_bytes/1024**3:.2f} GB；零风险关键词 {len(safe_kw)} 个")
print(f"→ {OUT}")
