#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命名净化（档 1）—— 只删噪声位，不动信息位。见《命名规范-2026-08-13.md》§二。

会做：
  · 剥渠道前缀    www.98T.la@ / gc2048.com- / hhd800.com@ / jav.li_ / 第一會所新片@SIS001@ / [JAV][Uncensored] / ►► ★
  · 修双扩展名    .mp4.mp4 → .mp4
  · 收连续空格、扩展名前空格、首尾空格
  · 拆全角括号残留的空壳 [] () 【】

绝不做：
  · ⚠️ 不剥 `(N)` —— 它是唯一区分位，剥掉 2,971 个文件会撞名（判断 #16）
  · 不猜人名、不拼凑、不从番号里"抢救"名字（旧版试过，产出 '1 001' / '048【…】mp4' 残渣）
  · 目标名已存在 → 跳过，不覆盖不加后缀

用法:
  python rm-cleanname.py --root "R:\\Media"              出预览 CSV
  python rm-cleanname.py --root "B:\\"                   同上（115）
  python rm-cleanname.py --root "B:\\" --apply           执行（读上一步的 CSV）

注：PikPak 一度被误判为不支持改名，是测错了（用的是没落到云端的自造文件）。实测可用。
"""
import os, re, sys, csv, time, unicodedata

a = sys.argv[1:]
def opt(n, d=None): return a[a.index(n) + 1] if n in a else d
ROOT = opt("--root")
APPLY = "--apply" in a
if not ROOT:
    print(__doc__); sys.exit(1)
# 注：PikPak 一度被判为「不支持改名」，是**测错了** —— 当时拿自己写进去、
# 还没落到云端的文件去 rename。用真实云端文件复测，改名和跨目录移动都正常。

tag = re.sub(r"[^A-Za-z0-9]", "", ROOT) or "root"
CSVF = rf"R:\Resources\Migration_Logs\命名净化-{tag}.csv"
LOG = rf"R:\Resources\Migration_Logs\cleanname-{tag}-{time.strftime('%Y%m%d-%H%M%S')}.log"

MEDIA = {".mp4", ".mkv", ".avi", ".wmv", ".mov", ".m4v", ".ts", ".flv", ".rmvb", ".mpg",
         ".mpeg", ".webm", ".m2ts", ".vob", ".jpg", ".jpeg", ".png", ".gif", ".webp",
         ".zip", ".rar", ".7z"}

PREFIX = [
    # 域名后的分隔符可能是 @ - _ 或**空格**（329932.xyz 推特新晋4年…）
    re.compile(r"^\s*(?:www\.)?[A-Za-z0-9\-]{2,20}\.(?:la|com|net|cc|me|in|tv|xyz|club|vip|top|li|cn|org)\s*[@\-_ ]\s*", re.I),
    re.compile(r"^\s*第一[會会]所[^@]*@\s*SIS\d+\s*@\s*", re.I),
    re.compile(r"^\s*\[JAV\]\s*", re.I),
    re.compile(r"^\s*[►◄◆◇■□●○★☆※]+\s*", re.I),
    # ⚠️ 不要加 `^@+` —— `@meiridasai5868` 里的 @ 是推特账号标记，是信息不是噪声
]
DOUBLE_EXT = re.compile(r"(\.(?:mp4|mkv|avi|wmv|mov|m4v|ts|flv|jpg|png|zip|rar))\1+$", re.I)
EMPTY_BRACKET = re.compile(r"[\[\(【（]\s*[\]\)】）]")

def clean(name):
    base, ext = os.path.splitext(name)
    full = name
    # 双扩展名先修（针对整名）
    m = DOUBLE_EXT.search(full)
    if m:
        full = full[:m.start()] + m.group(1)
    base, ext = os.path.splitext(full)
    prev = None
    while prev != base:
        prev = base
        for rx in PREFIX:
            base = rx.sub("", base)
    base = EMPTY_BRACKET.sub("", base)
    base = base.replace("\u3000", " ")
    base = re.sub(r"\s{2,}", " ", base)
    base = base.strip(" .-_")
    ext = ext.strip()
    if not base:                       # 剥光了 → 放弃，保留原名
        return name
    return base + ext

# ── 扫描 ──
rows = []
n_files = 0
t0 = time.time()
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        n_files += 1
        if os.path.splitext(fn)[1].lower() not in MEDIA:
            continue
        new = clean(fn)
        if new == fn:
            continue
        rows.append({"目录": dirpath, "原名": fn, "新名": new, "状态": ""})
    if n_files and n_files % 20000 == 0:
        print(f"  已扫 {n_files:,} 个文件，命中 {len(rows):,} …", flush=True)

print(f"扫描完成：{n_files:,} 个文件，需净化 {len(rows):,} 个，耗时 {time.time()-t0:.0f}s")

if not APPLY:
    # 预检冲突
    conflict = 0
    for r in rows:
        if os.path.exists(os.path.join(r["目录"], r["新名"])):
            r["状态"] = "目标已存在-将跳过"; conflict += 1
    # 同目录内新名撞车
    seen = {}
    for r in rows:
        k = (r["目录"].lower(), r["新名"].lower())
        if k in seen:
            r["状态"] = "与同批文件重名-将跳过"; conflict += 1
        else:
            seen[k] = r["原名"]
    with open(CSVF, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["目录", "原名", "新名", "状态"]); w.writeheader(); w.writerows(rows)
    print(f"冲突需跳过 {conflict} 个；可执行 {len(rows)-conflict} 个")
    print(f"\n预览 → {CSVF}")
    print("样例:")
    for r in [x for x in rows if not x["状态"]][:15]:
        print(f"  {r['原名'][:62]}\n    → {r['新名'][:62]}")
    print("\n核对无误后加 --apply 执行")
    sys.exit(0)

# ── 执行 ──
if not os.path.exists(CSVF):
    print(f"找不到预览 CSV：{CSVF}，先不带 --apply 跑一次"); sys.exit(3)
plan = [r for r in csv.DictReader(open(CSVF, encoding="utf-8-sig")) if not r["状态"]]
logf = open(LOG, "w", encoding="utf-8", buffering=1)
ok = skip = err = 0
for i, r in enumerate(plan, 1):
    src = os.path.join(r["目录"], r["原名"]); dst = os.path.join(r["目录"], r["新名"])
    if not os.path.exists(src):
        skip += 1; logf.write(f"SKIP\t源不存在\t{src}\n"); continue
    if os.path.exists(dst):
        skip += 1; logf.write(f"SKIP\t目标已存在\t{dst}\n"); continue
    try:
        os.rename(src, dst); ok += 1
        logf.write(f"OK\t{src}\t→\t{r['新名']}\n")
    except Exception as e:
        err += 1; logf.write(f"ERR\t{type(e).__name__}\t{src}\t{e}\n")
    if i % 200 == 0:
        print(f"  {i}/{len(plan)}  成功 {ok} 跳过 {skip} 失败 {err}", flush=True)
print(f"完成：成功 {ok}，跳过 {skip}，失败 {err}")
print(f"日志 → {LOG}")
