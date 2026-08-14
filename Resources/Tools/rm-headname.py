#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头部人名回捞（第五轮文本回捞）—— 目录名反复出现同一个形状：**人名 + 合集措辞后缀**。

  tiakun_404合集              → tiakun_404
  muchi_tina更新至九月          → muchi_tina
  轩轩合集                     → 轩轩
  EddyS__z（10G230V）时长去重    → EddyS__z
  Bulging Senpai Compilation → Bulging Senpai
  推特大神EDC【146部合集】        → EDC
  Homemadevideosxx合集截止到2025年1月 → Homemadevideosxx
  我的枪好长原版➕收集(1)         → 我的枪好长

做法：剥站点前缀 → 剥渠道称谓（推特/网红/大神…）→ 从**第一个合集措辞处截断** → 判是否像名字。

⚠️ 这是第五轮文本回捞了，过拟合风险高，所以：
   · 必须先出预览，逐条看过再 --apply
   · 截断后剩余长度 > 20 的一律丢弃（长 = 还是描述）
   · 只写 ledger（软元数据、可改），**不做物理移动**

用法: python rm-headname.py [--loc 115|pikpak] [--apply]
"""
import os, re, csv, sys, json, sqlite3, urllib.request
from collections import defaultdict

DB = r"R:\Resources\Intake\ledger.db"
A = sys.argv[1:]
def _o(n, d): return A[A.index(n) + 1] if n in A else d
LOC = _o("--loc", "115")
DRIVE = {"115": "B:\\", "pikpak": "A:\\"}[LOC]
OUT = rf"R:\Resources\Migration_Logs\{LOC}-头部人名回捞.csv"
APPLY = "--apply" in A

SITE = re.compile(r"^\s*(?:www\.)?[A-Za-z0-9\-]{2,20}\.(?:la|com|net|cc|me|in|tv|xyz|club|vip|top|li|cn|org)\s*[@\-_ ]\s*", re.I)
LEAD = re.compile(r"^\s*[-—_·★☆✨►◄※⚡\[\(（【]*\s*"
                  r"(?:\d{1,4}[_\-.]\s*)?"                       # 前置编号 0493_-
                  r"(?:最新|新晋|新品|新流|顶级|顶流|超顶|极品|独家|首发|原创|无损|无水印|"
                  r"推特|微博|抖音|快手|网红|网黄|主播|大神|福利姬|模特|潮吹女神|女神|"
                  r"\d{4}年|\d{1,2}月|\d+\s*月新品|[（(]?\d+[VvPp][^)）]*[)）]?)*\s*", re.I)
# 合集措辞：从这里开始截断
CUT = re.compile(
    r"(合集|全集|大合集|总集|精选|打包|整理|收集|收藏|典藏|珍藏|"
    r"更新至|截止|持续更新|最新|原版|去重|时长去重|私拍|订阅|付费|资源|下载|"
    r"compilation|collection|selected|presents|pack|archive|"
    r"[（(]\s*\d+\s*[GgVvPp]|\[\s*\d+\s*[GgVvPp]|[（(]\d+[^)）]{0,12}[)）]\s*$)", re.I)
TAIL = re.compile(r"[\s\-—_·、，,。.＋+➕/\\|]+$")
DESCRIPTIVE = re.compile(
    r"(视角|内射|中出|口交|足交|自慰|高潮|无套|外流|流出|泄密|探花|偷拍|偷窥|直播|录播|"
    r"系列|专辑|作品|影片|视频|图片|写真|番号|福利|门槛|事件|做种|论坛|論壇|文宣|宣傳|宣传|"
    r"反差|母狗|骚|淫|婊|奶|穴|屌|鸡巴|操|肏|射|body|平台|演艺圈|"
    # 韩语内容词 —— 上一版把 맨발_풋잡.mp4（赤足足交）当成了人名
    r"풋잡|맨발|스타킹|레깅스|페디|검스|유출|노출|자위|흰색|노란|주황|나이키|레드슈즈|"
    # 日语内容词
    r"ハメ撮り|中出し|フェラ|素人|動画|お姉さん|おっぱい|コス)", re.I)
MEDIA_EXT = re.compile(r"\.(mp4|mkv|avi|wmv|mov|m4v|ts|flv|rmvb|jpg|png|zip|rar|7z)$", re.I)
FORMAT_WORD = re.compile(r"^(fc2|jav|vr|4k|hd|fhd|uhd|mp4|new|old|pen|misc|tmp|temp)$", re.I)
DATE_TAIL = re.compile(r"\s*\d{1,2}\s*月\s*\d{1,2}\s*[日号]?\s*$")
NAMEISH = re.compile(r"^[\w\u3040-\u30ff\u4e00-\u9fff][\w\u3040-\u30ff\u4e00-\u9fff .＿_'’\-]{1,19}$")

def head(name):
    if MEDIA_EXT.search(name.strip()):      # 整串是个文件名，不是目录名式的人名
        return None
    s = name.strip()
    for _ in range(3):                      # madoubt.com 268323.xyz SQTE-676 有两层站点前缀
        s2 = SITE.sub("", s).strip()
        if s2 == s: break
        s = s2
    s = LEAD.sub("", s).strip()
    s = DATE_TAIL.sub("", s).strip()
    m = CUT.search(s)
    if m:
        s = s[:m.start()]
    s = TAIL.sub("", s).strip(" 【】[]（）()「」『』")
    s = re.sub(r"\s{2,}", " ", s).strip()
    if not s or len(s) > 20 or len(s) < 2: return None
    if DESCRIPTIVE.search(s): return None
    if re.fullmatch(r"[\d\W_]+", s): return None
    if FORMAT_WORD.match(s): return None
    if re.fullmatch(r"[A-Za-z]{2,7}-\d{2,5}", s): return None   # 番号不是人名
    if not NAMEISH.match(s): return None
    return s

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
d = defaultdict(lambda: [0, 0])
for p, s in con.execute(
        "SELECT path,size FROM asset WHERE location=? AND medium='video' "
        "AND (creator IS NULL OR creator='') AND (code IS NULL OR code='')", (LOC,)):
    ps = [x for x in p.replace(DRIVE, "").split("\\") if x]
    k = "\\".join(ps[:2]) if len(ps) >= 2 else (ps[0] if ps else "?")
    d[k][0] += 1; d[k][1] += s or 0
con.close()

SUBNAME = re.compile(r"^[\w぀-ヿ一-鿿\[]", re.I)
def is_container(full):
    """结构性判据（比正则可靠）：子目录里有 >=3 个像创作者名的 → 这是筐不是人。
    发现经过：A:\Pack From Shared\pen 746 GB，正则截出 'pen' 当创作者；
    实际里面有 16 个创作者子目录（banbi_555 / raikun325 / [myfans]ukiru / yn_3 …）。"""
    try:
        subs = [c for c in os.listdir(full) if os.path.isdir(os.path.join(full, c))]
    except Exception:
        return False
    return sum(1 for c in subs if head(c)) >= 3

hits, miss = [], []
for k, (n, sz) in d.items():
    leaf = k.split("\\")[-1]
    h = head(leaf)
    if h and is_container(os.path.join(DRIVE, k)):
        h = None
    (hits if h else miss).append({"归属": h or "", "视频数": n,
                                  "体积GB": round(sz / 1024**3, 2), "目录": k})
hits.sort(key=lambda x: -x["体积GB"])
miss.sort(key=lambda x: -x["体积GB"])

print(f"{LOC}: 无归属目录 {len(d):,} 个")
print(f"  截出人名 {len(hits):,} 个 / {sum(h['视频数'] for h in hits):,} 视频 / "
      f"{sum(h['体积GB'] for h in hits)/1024:.2f} TB")
print(f"  仍截不出 {len(miss):,} 个 / {sum(h['视频数'] for h in miss):,} 视频 / "
      f"{sum(h['体积GB'] for h in miss)/1024:.2f} TB  ← 这批才真要读图\n")
print("=== 截出的（按体积，逐条看）===")
for h in hits[:26]:
    print(f"  {h['体积GB']:>7.1f}GB {h['视频数']:>4}个  {h['归属'][:22]:<24} ← {h['目录'].split(chr(92))[-1][:48]}")
print("\n=== 截不出、需读图的 Top 10 ===")
for h in miss[:10]:
    print(f"  {h['体积GB']:>7.1f}GB {h['视频数']:>4}个  {h['目录'][:64]}")

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["归属", "视频数", "体积GB", "目录"])
    w.writeheader(); w.writerows(hits)
print(f"\n→ {OUT}")
if not APPLY:
    print("逐条核对后加 --apply 写入 ledger（不做物理移动）"); sys.exit(0)

con = sqlite3.connect(DB); cur = con.cursor()
n_up = 0
for h in hits:
    ids = [r[0] for r in cur.execute(
        "SELECT id FROM asset WHERE location=? AND (creator IS NULL OR creator='') "
        "AND (path LIKE ? OR path = ?)", (LOC, DRIVE + h["目录"] + "\\%", DRIVE + h["目录"]))]
    if not ids: continue
    qm = ",".join("?" * len(ids))
    cur.execute(f"UPDATE asset SET creator=? WHERE id IN ({qm})", [h["归属"]] + ids)
    n_up += len(ids)
con.commit(); con.close()
print(f"ledger 更新 {n_up:,} 个资产")

GQL = "http://127.0.0.1:9999/graphql"
def gql(q, v=None):
    r = urllib.request.urlopen(urllib.request.Request(
        GQL, data=json.dumps({"query": q, "variables": v or {}}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    return json.loads(r.read())
have = {p["name"].lower() for p in
        gql('{findPerformers(filter:{per_page:-1}){performers{name}}}')["data"]["findPerformers"]["performers"]}
new = 0
for h in hits:
    if h["归属"].lower() in have: continue
    try:
        gql('mutation($n:String!){performerCreate(input:{name:$n}){id}}', {"n": h["归属"]})
        have.add(h["归属"].lower()); new += 1
    except Exception as e:
        print("  失败:", h["归属"], e)
print(f"Stash 新建 Performer {new}")
