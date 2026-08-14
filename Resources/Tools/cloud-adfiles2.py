#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广告识别 v2 —— 从 ledger 读，三条判据任一命中即为候选。不读文件内容。

  A. 文件名里嵌了域名（uum58.com / TY996.COM / js666.site 这类），且体积小
     —— 先剥掉 "www.98T.la@" 这种前缀形态，那是转载标记不是广告
  B. 命中推广特征词（比 v1 大幅扩充）
  C. 同名出现在 >=3 个不同目录，且名字不是纯数字（图集通用命名不算）

体积门槛：视频 <80MB、图片 <3MB、文本不限。正片不会这么小。

用法: python cloud-adfiles2.py [--location 115] [--out out.csv] [--apply]
"""
import os, re, sys, csv, sqlite3
from collections import Counter, defaultdict

DB = r"R:\Resources\Intake\ledger.db"
a = sys.argv[1:]
LOC = a[a.index("--location") + 1] if "--location" in a else None
OUT = a[a.index("--out") + 1] if "--out" in a else os.path.expandvars(r"%USERPROFILE%\Desktop\广告候选-v2.csv")
APPLY = "--apply" in a

# 先剥掉转载方前缀：www.98T.la@ / hhd800.com@ / [22sht.me] 等
PREFIX = re.compile(r"^\s*(\[[^\]]{2,20}\]|\(?(www\.)?[a-z0-9\-]{2,20}\.(com|net|org|cc|la|me|xyz|club|site|vip|top|info|tv)\)?\s*[@\-_]+)\s*", re.I)
DOMAIN = re.compile(r"\b[a-z0-9\-]{2,20}\.(com|net|cc|xyz|club|site|vip|top|la|me|info|tv|fun|bid|link|shop|online)\b", re.I)
KW = re.compile(
    r"信誉|信譽|保证|保證|服务全球|服務全球|裸聊|直播间|直播間|约炮神器|娱乐城|娛樂城|棋牌|博彩|彩票|菠菜|"
    r"彩金|首存|注册送|註冊送|优惠|優惠|试玩|試玩|免费试看|免費試看|可先试看|开户|開戶|投注|"
    r"加QQ|加微信|加群|进群|進群|扫码|掃碼|二维码|二維碼|"
    r"最新地址|地址获取|发布页|發布頁|发布器|發布器|防走失|防丢失|防失联|防河蟹|永久地址|备用地址|備用網址|"
    r"论坛地址|論壇地址|下载地址|下載地址|访问地址|訪問地址|请收藏|請收藏|收藏我们|导航|導航|"
    r"APP下载|app下载|客户端下载|安装包|扫描二维码|"
    r"社\s*區|社\s*区|最\s*新\s*情\s*報|最\s*新\s*情\s*报|加入我们|加入我們|电报群|電報群|"
    r"招商|赞助商|贊助商|广告位|廣告位|招租|推广|推廣", re.I)

VIDEO = {".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".mov", ".ts", ".flv", ".rmvb"}
IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
TEXT = {".txt", ".html", ".htm", ".url", ".mht", ".lnk", ".nfo", ".chm", ".apk", ".torrent"}
VMAX, IMAX = 80 * 1024**2, 3 * 1024**2

c = sqlite3.connect(DB)
sql = "SELECT id,location,path,name,size FROM asset WHERE location != 'online'"
if LOC:
    sql += f" AND location='{LOC}'"
rows = c.execute(sql).fetchall()
print(f"读入 {len(rows):,} 条")

# C 判据：同名跨目录
dirs_of = defaultdict(set)
for _, loc, p, n, sz in rows:
    dirs_of[(loc, n)].add(os.path.dirname(p))

hits = []
why_c = Counter()
for aid, loc, p, n, sz in rows:
    sz = sz or 0
    ext = os.path.splitext(n)[1].lower()
    if ext in VIDEO and sz > VMAX:   continue
    if ext in IMAGE and sz > IMAX:   continue
    if ext not in VIDEO and ext not in IMAGE and ext not in TEXT and sz > VMAX: continue

    base = os.path.splitext(n)[0]
    stripped = PREFIX.sub("", base)          # 剥掉转载前缀后再看有没有域名
    why = []
    if DOMAIN.search(stripped):              # A
        why.append("嵌域名")
    if KW.search(base):                      # B
        why.append("推广词")
    if (len(dirs_of[(loc, n)]) >= 3 and not re.fullmatch(r"[\d\s\(\)\.\-_]+", base)
            and len(base) >= 4):             # C
        why.append(f"同名{len(dirs_of[(loc,n)])}目录")
    if why:
        hits.append((aid, loc, p, n, sz, "+".join(why)))
        for w in why: why_c[w] += 1

hits.sort(key=lambda x: -x[4])
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["动作", "判据", "大小MB", "位置", "路径"])
    for aid, loc, p, n, sz, why in hits:
        w.writerow(["删除", why, round(sz / 1024**2, 2), loc, p])

print(f"\n命中 {len(hits):,} 个 / {sum(h[4] for h in hits)/1024**3:.2f} GB")
for k, v in why_c.most_common():
    print(f"  {v:>6,}  {k}")
print(f"\n体积最大的 20 个（重点核对）：")
for aid, loc, p, n, sz, why in hits[:20]:
    print(f"  {sz/1024**2:7.1f} MB [{why}]  {n[:66]}")
print(f"\n→ {OUT}")

if APPLY:
    print("\n=== 执行删除 ===")
    ok = fail = 0; freed = 0
    for aid, loc, p, n, sz, why in hits:
        try:
            os.remove(p); ok += 1; freed += sz
            c.execute("DELETE FROM asset WHERE id=?", (aid,))
        except OSError as e:
            fail += 1
    c.commit()
    print(f"删除 {ok}  失败 {fail}  回收 {freed/1024**3:.2f} GB")
c.close()
