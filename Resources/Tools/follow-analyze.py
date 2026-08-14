#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 X / Pixiv 关注列表，提取口味信号，并与已有库存做差集。"""
import json, os, re, csv, urllib.request
from collections import Counter, defaultdict

DL = os.path.expandvars(r"%USERPROFILE%\Downloads")
OUT = os.path.expandvars(r"%USERPROFILE%\Desktop\关注列表分析.txt")
R, w = [], None
R = []; w = R.append

# ---------- 载入 ----------
px = json.load(open(os.path.join(DL, "pixiv-following.json"), encoding="utf-8"))
xf = json.load(open(os.path.join(DL, "x-following.json"), encoding="utf-8"))
print(f"pixiv 关注 {len(px)}  |  X 关注 {len(xf)}")

# ---------- 已有库存（Stash + 网盘清单）----------
have = set()
try:
    req = urllib.request.Request("http://127.0.0.1:9999/graphql",
        data=json.dumps({"query": "{findPerformers(filter:{per_page:-1}){performers{name alias_list}}}"}).encode(),
        headers={"Content-Type": "application/json"})
    for p in json.loads(urllib.request.urlopen(req, timeout=20).read())["data"]["findPerformers"]["performers"]:
        have.add(p["name"].lower())
        for a in (p.get("alias_list") or []):
            have.add(a.lower().lstrip("@"))
except Exception as e:
    print("Stash 未连上:", e)

cloud_text = ""
for inv in ("115-inventory.csv", "pikpak-inventory.csv"):
    p = os.path.expandvars(rf"%USERPROFILE%\Desktop\{inv}")
    if os.path.exists(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            cloud_text += "\n".join(r["path"] + "\\" + r["name"] for r in csv.DictReader(f)).lower()
print(f"库存名字 {len(have)} 个，网盘文本 {len(cloud_text)/1024**2:.1f} MB")

w("X / Pixiv 关注列表分析")
w(f"pixiv 关注 {len(px)} 位  |  X 关注 {len(xf)} 个账号")
w("")

# ================= PIXIV =================
w("=" * 78)
w("一、Pixiv")
w("=" * 78)
pub = [u for u in px if u.get("rest") == "show"]
pri = [u for u in px if u.get("rest") == "hide"]
w(f"  公开关注 {len(pub)}   私密关注 {len(pri)}")
w("  （私密关注通常是更「不想被看到」的那批，口味信号更强）")

tag_all, tag_pri = Counter(), Counter()
for u in px:
    for wk in (u.get("recentWorks") or []):
        for t in (wk.get("tags") or []):
            tag_all[t] += 1
            if u.get("rest") == "hide":
                tag_pri[t] += 1

NOISE_TAG = re.compile(r"^(オリジナル|original|イラスト|illustration|漫画|manga|東方|R-?18|"
                       r"女の子|girl|オリキャラ|創作|落書き|らくがき)$", re.I)
w(f"\n  --- 关注作者作品的标签 Top 60（共 {len(tag_all)} 个）---")
for t, n in tag_all.most_common(60):
    mark = "  ←私密关注也高频" if tag_pri.get(t, 0) >= max(2, n * 0.4) else ""
    w(f"    {n:>4}  {t}{mark}")

if tag_pri:
    w(f"\n  --- 只看私密关注的标签 Top 40 ---")
    for t, n in tag_pri.most_common(40):
        w(f"    {n:>4}  {t}")

# 差集：关注了但库里/网盘里没有的作者
w(f"\n  --- 关注了、但本地和网盘都找不到的作者（前 80）---")
miss = []
for u in px:
    nm = (u.get("name") or "").lower().strip()
    uid = str(u.get("userId"))
    if not nm:
        continue
    if nm in have or (len(nm) > 2 and nm in cloud_text) or uid in cloud_text:
        continue
    miss.append(u)
w(f"  共 {len(miss)} / {len(px)} 位关注作者在库存里查无对应")
for u in miss[:80]:
    tags = Counter()
    for wk in (u.get("recentWorks") or []):
        for t in (wk.get("tags") or []):
            if not NOISE_TAG.match(t):
                tags[t] += 1
    tg = "、".join(t for t, _ in tags.most_common(6))
    w(f"    [{u.get('rest')}] {u.get('name','')[:28]:<30} {u.get('homepage')}   {tg[:60]}")

# ================= X =================
w("")
w("=" * 78)
w("二、X（已剔除正经账号）")
w("=" * 78)

ADULT = re.compile(
    r"r-?18|r18|nsfw|18\+|成人|エロ|えろ|裸|ヌード|nude|porn|hentai|"
    r"涩|瑟|色图|色圖|福利|无码|無碼|番号|番號|探花|约炮|約砲|約炮|反差|"
    r"足|脚|腳|丝袜|絲襪|黑丝|黑絲|高跟|恋足|戀足|foot|feet|"
    r"onlyfans|fansly|fanbox|fantia|patreon|subscribestar|ci-en|dlsite|"
    r"巨乳|爆乳|貧乳|人妻|熟女|萝莉|蘿莉|loli|jk|制服|cos|コス|"
    r"中出|内射|內射|口交|调教|調教|ntr|寝取|自慰|オナ|射|淫|骚|騷|欲|"
    r"直播|定制|定製|私信|空降|上门|上門|外围|外圍|资源|資源|合集|"
    r"3d|sfm|blender|koikatsu|同人|doujin|ふたなり|futa", re.I)
CLEAN = re.compile(
    r"news|新闻|新聞|官方|official|政府|gov|開發|开发|developer|github|"
    r"tech|科技|programming|编程|編程|前端|后端|後端|linux|docker|k8s|"
    r"投资|投資|股票|基金|经济|經濟|财经|財經|apple|google|microsoft|"
    r"设计|設計|摄影|攝影|旅行|美食|健身|读书|讀書|学习|學習", re.I)

adult, clean, unsure = [], [], []
for a in xf:
    hay = f"{a.get('name','')} {a.get('handle','')} {a.get('bio','')}"
    hnd = (a.get("handle") or "").lstrip("@").lower()
    in_lib = hnd in have or (len(hnd) > 3 and hnd in cloud_text)
    if in_lib:
        a["_why"] = "库存里有同名"
        adult.append(a)
    elif ADULT.search(hay):
        a["_why"] = "特征词命中"
        adult.append(a)
    elif CLEAN.search(hay):
        clean.append(a)
    else:
        unsure.append(a)

w(f"  总计 {len(xf)}：判定成人向 {len(adult)}，正经账号 {len(clean)}（已排除），无法判定 {len(unsure)}")

w(f"\n  --- 成人向关注（{len(adult)}）---")
for a in adult:
    lib = "✓在库" if a["_why"] == "库存里有同名" else "  "
    w(f"    {lib} {a.get('handle',''):<22}{a.get('name','')[:22]:<24}{(a.get('bio') or '')[:70]}")

w(f"\n  --- 无法判定（{len(unsure)}）—— 你扫一眼，可能有漏网的 ---")
for a in unsure[:60]:
    w(f"       {a.get('handle',''):<22}{a.get('name','')[:22]:<24}{(a.get('bio') or '')[:70]}")

w(f"\n  --- 已排除的正经账号（{len(clean)}，仅列名）---")
w("    " + "  ".join(a.get("handle", "") for a in clean))

# X 里成人向但库存查无的
w(f"\n  --- 成人向、且库存查无对应的（这批是待补重点）---")
xmiss = [a for a in adult if a["_why"] != "库存里有同名"]
w(f"  共 {len(xmiss)}")
for a in xmiss:
    w(f"    {a.get('handle',''):<22}{a.get('name','')[:24]:<26}{(a.get('bio') or '')[:60]}")

open(OUT, "w", encoding="utf-8").write("\n".join(R))
print(f"\npixiv 差集 {len(miss)} / X 成人向 {len(adult)}（其中库存查无 {len(xmiss)}）")
print(f"→ {OUT}")
