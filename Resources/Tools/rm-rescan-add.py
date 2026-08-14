#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只补不删的扫描 —— 修复「基于单次遍历删死行」造成的误删。

背景：PikPak 经 CloudDrive2/WebDAV 列目录不确定，同一子树连数三遍
      41,601 / 38,497 / 41,728（±8%，且是漏不是多）。
      `rm-reconcile.py` 第一版基于单次遍历删掉 41,913 条 pikpak 行，
      其中约 3,000 条是列目录漏报导致的误删（文件本身从未被动过）。

本脚本：多遍遍历取并集 → 把账本里没有的路径 INSERT 回去 → **不删任何行**。
        归属能从新目录结构反推的顺手补上（B:\\创作者\\{人}\\… ）。

用法: python rm-rescan-add.py --loc pikpak [--passes 3] [--apply]
"""
import os, sys, time, sqlite3

DB = r"R:\Resources\Intake\ledger.db"
A = sys.argv[1:]
def _o(n, d, c=str): return c(A[A.index(n) + 1]) if n in A else d
LOC = _o("--loc", "pikpak")
DRIVE = {"115": "B:\\", "pikpak": "A:\\", "local": "R:\\Media\\"}[LOC]
PASSES = _o("--passes", 3, int)
APPLY = "--apply" in A

VID = {".mp4",".mkv",".avi",".wmv",".mov",".m4v",".ts",".flv",".rmvb",".mpg",".mpeg",
       ".webm",".m2ts",".vob",".3gp",".asf",".divx",".f4v",".mts",".ogv",".rm"}
IMG = {".jpg",".jpeg",".png",".gif",".webp",".bmp",".heic",".tif",".tiff"}
ARC = {".zip",".rar",".7z",".tar",".gz",".iso"}
AUD = {".mp3",".flac",".wav",".m4a",".aac",".ogg"}
def medium(e):
    e = e.lower()
    return ("video" if e in VID else "image" if e in IMG else
            "archive" if e in ARC else "audio" if e in AUD else "other")

seen = {}
t0 = time.time()
for k in range(PASSES):
    n = 0
    for dp, dns, fns in os.walk(DRIVE):
        for f in fns:
            p = os.path.join(dp, f)
            n += 1
            if p.lower() not in seen:
                try:
                    st = os.stat(p)
                    seen[p.lower()] = (p, f, st.st_size, st.st_mtime)
                except Exception:
                    pass
    print(f"  第 {k+1}/{PASSES} 遍：本遍 {n:,}，并集累计 {len(seen):,}（{time.time()-t0:.0f}s）")

con = sqlite3.connect(DB)
cur = con.cursor()
have = {p.lower() for (p,) in cur.execute("SELECT path FROM asset WHERE location=?", (LOC,))}
missing = [v for kk, v in seen.items() if kk not in have]
print(f"\n账本 {len(have):,} 行，磁盘并集 {len(seen):,} 个 → 账本缺 {len(missing):,} 个")

from collections import Counter
mc = Counter(medium(os.path.splitext(v[1])[1]) for v in missing)
mb = sum(v[2] for v in missing) / 1024**4
print(f"  缺失分布: {dict(mc)}   合计 {mb:.2f} TB")
for v in missing[:8]:
    print(f"    {v[2]/1024**2:>9.1f} MB  {v[0][:88]}")

if not APPLY:
    print("\n加 --apply 补写（只 INSERT，不删任何行）"); sys.exit(0)

def attrib(p):
    """从新目录结构反推归属：{drive}\\创作者\\{人}\\… / 番号\\{厂牌}\\{番号}\\… / 西方\\{Studio}\\…"""
    rel = p[len(DRIVE):] if p.lower().startswith(DRIVE.lower()) else p
    parts = [x for x in rel.split("\\") if x]
    if len(parts) >= 2:
        if parts[0] == "创作者": return parts[1], None, None
        if parts[0] == "西方":   return None, parts[1], None
        if parts[0] == "番号" and len(parts) >= 3:
            return None, (None if parts[1].startswith("_") else parts[1]), parts[2]
    return None, None, None

rows = []
for p, name, size, mtime in missing:
    cr, st, cd = attrib(p)
    rows.append((LOC, p, name, medium(os.path.splitext(name)[1]), size, mtime, cr, st, cd))
cur.executemany(
    "INSERT INTO asset(location,path,name,medium,size,mtime,creator,studio,code) "
    "VALUES(?,?,?,?,?,?,?,?,?)", rows)
con.commit()
print(f"\n已补写 {len(rows):,} 行")
a = cur.execute("SELECT count(*),COALESCE(sum(size),0) FROM asset WHERE location=?", (LOC,)).fetchone()
v = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video'", (LOC,)).fetchone()[0]
vc = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video' "
                 "AND creator IS NOT NULL AND creator<>''", (LOC,)).fetchone()[0]
print(f"{LOC}: {a[0]:,} 行 / {a[1]/1024**4:.2f} TB   视频 {v:,}，有创作者 {vc:,} ({vc/max(v,1)*100:.0f}%)")
con.close()
