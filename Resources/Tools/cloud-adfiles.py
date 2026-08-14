#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识别网盘里的广告/引流文件。纯文件名+大小判断，不读内容。

判定逻辑（两者必须同时成立，避免误伤正片）：
  1. 文件名命中广告特征词
  2. 且满足体积门槛：文本/网页类不限大小；视频/图片类必须小于阈值
     （广告视频通常几十秒，正片不会这么小）

用法: python cloud-adfiles.py <inventory.csv> <输出目录> [盘符替换 旧 新]
"""
import csv, os, re, sys
from collections import Counter

INV = sys.argv[1] if len(sys.argv) > 1 else os.path.expandvars(r"%USERPROFILE%\Desktop\115-inventory.csv")
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.expandvars(r"%USERPROFILE%\Desktop\115-dedup")
OLD, NEW = (sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else ("Z:\\115open\\", "B:\\")
os.makedirs(OUTDIR, exist_ok=True)

# 广告特征词。分组是为了产出时能说明「为什么判它是广告」
PATTERNS = [
    ("地址引流", r"最新地址|地址获取|发布页|防走失|防丢失|防失联|永久地址|备用地址|备用网址|"
                 r"论坛地址|下载地址|網址|网址|访问地址|入口|请访问|打开网站|收藏我们|请收藏"),
    ("APP推广", r"APP下载|app下载|客户端下载|安装包|下载安装|扫码下载|扫描二维码|二维码"),
    ("社群引流", r"社\s*區|社\s*区|最\s*新\s*情\s*報|最\s*新\s*情\s*报|加入我们|加入我們|"
                 r"电报群|電報群|telegram群|tg群|微信群|QQ群|q群|加群|进群|频道"),
    # 注意：站点前缀（www.98T.la@ 之类）不是广告判据 —— 那是转载方给正片打的标记，
    # 该做的是改名去掉前缀，不是删文件。误当广告会删掉数千个正片。
    ("推广话术", r"约炮神器|裸聊|博彩|棋牌|彩票|菠菜|注册送|开户|信誉平台|娱乐城|"
                 r"招商|赞助商|广告位|廣告位|招租"),
    ("说明文件", r"^(必看|说明|請看|请看|readme|read me|注意事项|使用说明|温馨提示|溫馨提示)"),
]
COMPILED = [(n, re.compile(p, re.I)) for n, p in PATTERNS]

TEXTLIKE = {".txt", ".html", ".htm", ".url", ".mht", ".chm", ".lnk", ".nfo", ".doc", ".docx", ".md"}
MEDIA = {".mp4", ".avi", ".wmv", ".mkv", ".m4v", ".mov", ".ts", ".flv", ".rmvb"}
IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

MEDIA_MAX = 80 * 1024 * 1024      # 广告视频阈值：80 MB
IMAGE_MAX = 3 * 1024 * 1024       # 广告图阈值：3 MB

rows = []
with open(INV, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f):
        try:
            r["size"] = int(r["size"])
        except (TypeError, ValueError):
            r["size"] = 0
        r["full"] = os.path.join(r["path"], r["name"]).replace(OLD, NEW)
        rows.append(r)
print(f"读入 {len(rows):,} 个文件")

hits = []
why = Counter()
for r in rows:
    name = r["name"]
    ext = os.path.splitext(name)[1].lower()
    matched = [n for n, p in COMPILED if p.search(name)]
    if not matched:
        continue
    # 体积门槛
    if ext in TEXTLIKE:
        pass                                   # 文本类不限大小
    elif ext in MEDIA:
        if r["size"] > MEDIA_MAX:
            continue                           # 太大，可能是正片，放过
    elif ext in IMAGE:
        if r["size"] > IMAGE_MAX:
            continue
    else:
        if r["size"] > MEDIA_MAX:
            continue
    r["why"] = "+".join(matched)
    why[matched[0]] += 1
    hits.append(r)

out = os.path.join(OUTDIR, "adfiles-B.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["动作", "判据", "大小MB", "路径"])
    for r in sorted(hits, key=lambda x: (-x["size"], x["full"])):
        w.writerow(["删除", r["why"], round(r["size"] / 1024**2, 2), r["full"]])

print(f"\n命中 {len(hits):,} 个广告/引流文件，合计 {sum(r['size'] for r in hits)/1024**3:.2f} GB")
print("\n按判据分布：")
for k, v in why.most_common():
    print(f"  {v:>6,}  {k}")
print(f"\n体积最大的 15 个（重点核对，别误伤正片）：")
for r in sorted(hits, key=lambda x: -x["size"])[:15]:
    print(f"  {r['size']/1024**2:8.1f} MB  [{r['why']}]  {r['name'][:70]}")
print(f"\n→ {out}")
