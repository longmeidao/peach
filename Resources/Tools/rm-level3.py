#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三层回捞 —— 分类器只看两层，漏掉了 {批次}\{合集}\{人名}\ 这种结构。

发现经过：读 `MVP\FC2-Selected collection-2`（245 GB）的识别页时看到三个不同的
FC2 卖家水印，怀疑是混合集；一看下一层，19 个子目录全是女优名
（七瀬アリス@市島亜美 / 白桃はな@白桃花 / 石川祐奈 …）。

顺带：目录名里的 `@` 是**别名标记**（日文名@中文名），可以直接补 Stash 的 alias_list。

只处理仍留在旧顶层（未被重组搬走）的 D 类目录。
用法: python rm-level3.py [--apply]
"""
import os, re, csv, sys, json, sqlite3, urllib.request
from collections import Counter

DB = r"R:\Resources\Intake\ledger.db"
A = sys.argv[1:]
def _o(n, d): return A[A.index(n) + 1] if n in A else d
LOC = _o("--loc", "115")
DRIVE = {"115": "B:\\", "pikpak": "A:\\"}[LOC]
OUT = rf"R:\Resources\Migration_Logs\{LOC}-三层回捞.csv"
APPLY = "--apply" in A

# 判人名：日文假名/汉字 2–12 字，或拉丁账号；且不含描述性措辞
JP_NAME = re.compile(r"^[\u3040-\u30ff\u4e00-\u9fff][\u3040-\u30ff\u4e00-\u9fff]{1,11}$")
LAT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.\- ]{2,26}$")
DESCRIPTIVE = re.compile(
    r"(合集|全集|精选|打包|下载|资源|整理|更新|系列|专辑|作品|影片|视频|图片|写真|番号|"
    r"宣傳|宣传|文件|说明|readme|新建|未命名|未分类|封面|截图|预览|样品|"
    r"内射|中出|口交|足交|自慰|高潮|无套|露脸|反差|流出|泄密|偷拍|直播|"
    r"^\d+$|^\d{4}$|selected|collection|compilation|pack|part|cd\d|disc)", re.I)

def looks_like_name(n):
    n = n.strip()
    if not n or len(n) > 28: return False
    if DESCRIPTIVE.search(n): return False
    # 别名写法 A@B → 取第一段判断
    head = n.split("@")[0].strip()
    return bool(JP_NAME.match(head) or LAT_NAME.match(head))

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
# 仍在旧顶层的 115 资产（重组过的已经在 创作者\ 番号\ 西方\ 下）
rows = con.execute(
    "SELECT path FROM asset WHERE location=? AND medium='video' "
    "AND (creator IS NULL OR creator='') "
    "AND path NOT LIKE ? AND path NOT LIKE ? AND path NOT LIKE ?",
    (LOC, DRIVE + "创作者\\%", DRIVE + "番号\\%", DRIVE + "西方\\%")).fetchall()
con.close()

# 收集三层目录：B:\{顶层}\{二层}\{三层}\…
lvl3 = Counter()
parent = {}
for (p,) in rows:
    ps = [x for x in p.replace(DRIVE, "").split("\\") if x]
    if len(ps) >= 4:                      # 顶层/二层/三层/文件
        key = "\\".join(ps[:3])
        lvl3[key] += 1
        parent[key] = "\\".join(ps[:2])

print(f"仍在旧顶层的视频 {len(rows):,} 个，涉及三层目录 {len(lvl3):,} 个")

# ⚠️ 关键闸门：父目录本身已是识别出的创作者时，第三层是「来源/系列」分组不是新人。
#    gattouz0\gattouz0 - Coomer、OBOKOZU\video、捅主任\TokyoDolls、SexySaffron\Snapchat Saturdays
#    都属此类。只有父目录**不是**创作者时（如 FC2-Selected collection-2），第三层才是人名。
known_parent = set()
try:
    _r = urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:9999/graphql",
        data=json.dumps({"query": '{findPerformers(filter:{per_page:-1}){performers{name alias_list}}}'}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    for p in json.loads(_r.read())["data"]["findPerformers"]["performers"]:
        known_parent.add(p["name"].lower())
        for a in (p.get("alias_list") or []):
            if len(a.strip()) >= 4: known_parent.add(a.strip().lower())
except Exception as e:
    print("连不上 Stash:", e)

def parent_is_creator(par):
    leaf = par.split("\\")[-1].lower()
    return any(k in leaf for k in known_parent)

# 明显不是人名的分组词
NOTNAME3 = re.compile(r"^(fc2|video|videos|dead|new|old|pic|pics|photo|photos|misc|"
                      r"视图|视频|图片|其他|其它|正片|成品)$", re.I)

hits = []
skipped_parent = 0
for key, n in lvl3.items():
    leaf = key.split("\\")[-1]
    if parent_is_creator(parent[key]):
        skipped_parent += 1; continue
    if NOTNAME3.match(leaf.strip()):
        continue
    if looks_like_name(leaf):
        names = [x.strip() for x in leaf.split("@") if x.strip()]
        hits.append({"归属": names[0], "别名": "|".join(names[1:]),
                     "视频数": n, "目录": key, "父目录": parent[key]})

hits.sort(key=lambda x: -x["视频数"])
byparent = Counter(h["父目录"] for h in hits)
print(f"\n三层是人名的目录 {len(hits):,} 个 / {sum(h['视频数'] for h in hits):,} 个视频")
print(f"来自 {len(byparent)} 个父目录，Top 8:")
for k, v in byparent.most_common(8):
    print(f"  {v:>4} 个人名子目录  {k[:60]}")
print(f"\n有别名的 {sum(1 for h in hits if h['别名'])} 个，样例:")
for h in [x for x in hits if x["别名"]][:8]:
    print(f"  {h['归属']:<16} ← 别名 {h['别名']}")
print(f"\n人名样例（按视频数）:")
for h in hits[:14]:
    print(f"  {h['视频数']:>4} 个  {h['归属'][:22]:<24} ← {h['目录'][:58]}")

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["归属", "别名", "视频数", "目录", "父目录"])
    w.writeheader(); w.writerows(hits)
print(f"\n→ {OUT}")

if not APPLY:
    print("加 --apply 写入 ledger + Stash")
    sys.exit(0)

# ── 写 ledger ──
con = sqlite3.connect(DB); cur = con.cursor()
n_up = 0
for h in hits:
    ids = [r[0] for r in cur.execute(
        "SELECT id FROM asset WHERE location=? AND (creator IS NULL OR creator='') "
        "AND path LIKE ?", (LOC, DRIVE + h["目录"] + "\\%"))]
    if not ids: continue
    qm = ",".join("?" * len(ids))
    cur.execute(f"UPDATE asset SET creator=? WHERE id IN ({qm})", [h["归属"]] + ids)
    n_up += len(ids)
con.commit()
print(f"ledger 更新 {n_up:,} 个资产")

# ── Stash 建 Performer + 写别名 ──
GQL = "http://127.0.0.1:9999/graphql"
def gql(q, v=None):
    r = urllib.request.urlopen(urllib.request.Request(
        GQL, data=json.dumps({"query": q, "variables": v or {}}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    return json.loads(r.read())

have = {p["name"].lower(): p for p in
        gql('{findPerformers(filter:{per_page:-1}){performers{id name alias_list}}}'
            )["data"]["findPerformers"]["performers"]}
new = alias = 0
for h in hits:
    nm = h["归属"]
    al = [x for x in h["别名"].split("|") if x]
    ex = have.get(nm.lower())
    try:
        if not ex:
            gql('mutation($n:String!,$a:[String!]){performerCreate(input:{name:$n,alias_list:$a}){id}}',
                {"n": nm, "a": al})
            new += 1
        elif al:
            merged = sorted(set((ex.get("alias_list") or []) + al))
            if merged != sorted(ex.get("alias_list") or []):
                gql('mutation($i:ID!,$a:[String!]){performerUpdate(input:{id:$i,alias_list:$a}){id}}',
                    {"i": ex["id"], "a": merged})
                alias += 1
    except Exception as e:
        print("  失败:", nm, e)
print(f"Stash：新建 Performer {new}，补别名 {alias}")
con.close()
