#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
115 零成本去重 —— 只吃 115-inventory.csv，不调任何 API、不读文件内容、不下载。

用法:
    python cloud-dedup.py <inventory.csv> <输出目录>

产出四个 CSV，全部是「候选」，需人工过目后再执行删除：
    junk.csv            垃圾文件（.url/.txt/.torrent/.html/.mht）
    dup-exact.csv       同名同大小
    dup-normalized.csv  归一化名 + 同大小
    dup-dir.csv         目录包含率 >= 阈值（专治合集重复）
"""
import csv, os, re, sys
from collections import defaultdict

INV = sys.argv[1] if len(sys.argv) > 1 else os.path.expandvars(r"%USERPROFILE%\Desktop\115-inventory.csv")
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.expandvars(r"%USERPROFILE%\Desktop\115-dedup")
os.makedirs(OUTDIR, exist_ok=True)

JUNK_EXT = {".url", ".txt", ".torrent", ".html", ".htm", ".mht", ".chm", ".lnk", ".nfo", ".db"}
MIN_DUP = 20 * 1024 * 1024        # 小于 20 MB 的不参与去重，收益低噪音大
DIR_THRESHOLD = 0.90              # 目录包含率阈值

# 文件名归一化：去掉站点前缀 / 画质后缀 / 序号 / 转载标记
SITE = re.compile(
    r"^(www[\.\-]?)?(98t\.la|hhd800\.com|hjd2048\.com|52ywy\.com|5snn\.com|9p3456\.com|"
    r"javdb\.com|18p2p|sexinsex|t66y|xsijishe)[@\-_\s]*", re.I)
QUALITY = re.compile(r"[\[\(\-_\s]*(4k|2k|1080p?|720p?|480p?|60fps|hevc|x265|h264|uncensored|"
                     r"中文字幕|无码|無碼|破解|流出|修复|增强|重制|重製)[\]\)\-_\s]*", re.I)
SEQ = re.compile(r"[\s_]*[\(\[]\d{1,3}[\)\]]\s*$")
TAG = re.compile(r"@[A-Za-z0-9_]{2,20}")
SEP = re.compile(r"[\s\-_\.·、，,]+")


def norm(name):
    base, ext = os.path.splitext(name)
    b = SITE.sub("", base)
    b = TAG.sub("", b)
    b = QUALITY.sub(" ", b)
    b = SEQ.sub("", b)
    b = SEP.sub("", b).lower()
    return b + ext.lower()


def score(path):
    """给保留优先级打分，越高越该留。"""
    s = 0
    low = path.lower()
    if "\\云下载" in path:
        s -= 50                       # 离线落地区，最该删
    if re.search(r"auto_create@", low):
        s -= 40
    if re.search(r"\\(mvp|xxr|kkg|new|123|4\.7|tzr)\\", low):
        s -= 10                       # 无语义批次目录
    s -= path.count("\\") * 2         # 越浅越好
    s -= len(path) // 40
    return s


rows = []
with open(INV, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f):
        try:
            r["size"] = int(r["size"])
        except (TypeError, ValueError):
            r["size"] = 0
        r["full"] = os.path.join(r["path"], r["name"])
        rows.append(r)
print(f"读入 {len(rows):,} 个文件 / {sum(r['size'] for r in rows)/1024**4:.2f} TB")

# ---------- 0. 垃圾 ----------
junk = [r for r in rows if os.path.splitext(r["name"])[1].lower() in JUNK_EXT]
with open(os.path.join(OUTDIR, "junk.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["动作", "大小MB", "路径"])
    for r in sorted(junk, key=lambda x: x["full"]):
        w.writerow(["删除", round(r["size"] / 1024**2, 2), r["full"]])
print(f"[垃圾]     {len(junk):,} 个  {sum(r['size'] for r in junk)/1024**2:.1f} MB")


def emit(groups, fname, label):
    """groups: {key: [row,...]}，写出保留/删除建议。"""
    n_grp = n_del = 0
    saved = 0
    with open(os.path.join(OUTDIR, fname), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["组号", "动作", "大小GB", "路径", "判据"])
        gid = 0
        for key, items in sorted(groups.items(), key=lambda kv: -sum(i["size"] for i in kv[1])):
            if len(items) < 2:
                continue
            gid += 1
            n_grp += 1
            items = sorted(items, key=lambda r: -score(r["full"]))
            for i, r in enumerate(items):
                act = "保留" if i == 0 else "删除"
                if i:
                    n_del += 1
                    saved += r["size"]
                w.writerow([gid, act, round(r["size"] / 1024**3, 3), r["full"], str(key)[:80]])
    print(f"[{label}] {n_grp:,} 组  可删 {n_del:,} 个  回收 {saved/1024**3:.1f} GB  → {fname}")
    return saved


# ---------- 1. 同名同大小 ----------
g1 = defaultdict(list)
for r in rows:
    if r["size"] >= MIN_DUP:
        g1[(r["name"], r["size"])].append(r)
s1 = emit(g1, "dup-exact.csv", "同名同大小")

# ---------- 2. 归一化名 + 同大小 ----------
seen_exact = {k for k, v in g1.items() if len(v) > 1}
g2 = defaultdict(list)
for r in rows:
    if r["size"] >= MIN_DUP and (r["name"], r["size"]) not in seen_exact:
        g2[(norm(r["name"]), r["size"])].append(r)
s2 = emit(g2, "dup-normalized.csv", "归一化名")

# ---------- 3. 目录包含率 ----------
# 关键：用 (归一化名, 大小) 二元组而不是只用名字，否则小目录极易误判为包含
MIN_DIR_FILES = 5                 # 目录至少 5 个大文件才参与，少于此噪音太大
dirs = defaultdict(set)
dirsize = defaultdict(int)
for r in rows:
    if r["size"] >= MIN_DUP:
        dirs[r["path"]].add((norm(r["name"]), r["size"]))
        dirsize[r["path"]] += r["size"]
cand = [(p, s) for p, s in dirs.items() if len(s) >= MIN_DIR_FILES]
cand.sort(key=lambda x: -len(x[1]))
print(f"[目录]     参与比对的目录 {len(cand):,} 个（>={MIN_DIR_FILES} 个大文件，按名+大小比对）")

pairs = []
for i, (pa, sa) in enumerate(cand):
    for pb, sb in cand[i + 1:]:
        if pa == pb or not sb:
            continue
        inter = len(sa & sb)
        if inter < MIN_DIR_FILES:      # 交集也必须够大，否则不算包含
            continue
        cover = inter / len(sb)
        if cover >= DIR_THRESHOLD and len(sa) >= len(sb):
            pairs.append((cover, pa, pb, len(sa), len(sb), dirsize[pb]))
pairs.sort(key=lambda x: -x[5])
with open(os.path.join(OUTDIR, "dup-dir.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["包含率", "被包含目录(建议删)", "体积GB", "文件数", "包含它的目录(保留)", "文件数"])
    for cover, pa, pb, na, nb, szb in pairs:
        w.writerow([f"{cover:.0%}", pb, round(szb / 1024**3, 2), nb, pa, na])
s3 = sum(p[5] for p in pairs)
print(f"[目录包含] {len(pairs):,} 对  回收 {s3/1024**3:.1f} GB  → dup-dir.csv")

print(f"\n三层合计可回收约 {(s1+s2+s3)/1024**3:.1f} GB")
print(f"输出目录: {OUTDIR}")
print("\n⚠ 全部是候选，执行删除前必须人工过目。dup-dir.csv 的重叠部分可能与前两层重复计算。")
