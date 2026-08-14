#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
括号人名回捞 —— 中文发布名里 「」『』 括起来的几乎必然是出镜者。

  「小野猫」「kiki酱」      → 两位
  【山东临沂齐鲁屌王】       → 一位（但 【】 也常放描述，要过滤）
  【aryminh】             → 一位
  推特大神EDC【146部合集】   → EDC（描述部分丢弃）

精度分级：
  「」『』  高 —— 这对括号在中文成人发布命名里专用于人名/账号，几乎不放描述
  【】      中 —— 既放人名也放描述（【无套内射】【淫水横飞】），必须过描述词闸门

只处理仍留在旧顶层（未被重组搬走）的 115 资产。
用法: python rm-bracket.py [--apply]
"""
import os, re, csv, sys, json, sqlite3, urllib.request
from collections import Counter, defaultdict

DB = r"R:\Resources\Intake\ledger.db"
OUT = r"R:\Resources\Migration_Logs\115-括号回捞.csv"
APPLY = "--apply" in sys.argv

HIGH = re.compile(r"[「『]([^」』]{2,20})[」』]")
MID = re.compile(r"[【\[]([^】\]]{2,20})[】\]]")

DESCRIPTIVE = re.compile(
    r"(视角|内射|中出|口交|足交|自慰|高潮|无套|外流|流出|泄密|探花|偷拍|偷窥|直播|录播|"
    r"合集|全集|精选|打包|下载|资源|整理|更新|系列|专辑|作品|影片|视频|图片|写真|番号|"
    r"福利|门槛|新品|新流|无水印|高清|修复|重制|完整|原创|首发|独家|订阅|私拍|"
    r"极品|嫩模|女神|母狗|反差|骚|淫|大神|平台|部|集|版|GB|G\b|V\b|P\b|"
    r"特輯|特辑|特别篇|番外|上篇|下篇|前篇|後篇|后篇|第[一二三四五六七八九十\d]+[期部集话話]|"
    r"\d{4}年|\d+月|\d+号|^\d+$|^[A-Z]{2,6}-?\d{2,5}$|"
    r"uncensored|jav|fhd|uhd|4k|1080p|720p|hevc|x265)", re.I)

def clean_name(s):
    s = s.strip().strip("-—_·、,，.。 ")
    s = re.sub(r"^(推特|微博|抖音|快手|网红|网黄|主播|大神|福利姬|模特)", "", s).strip()
    return s

def ok(s):
    s = clean_name(s)
    if not s or len(s) < 2 or len(s) > 20: return None
    if DESCRIPTIVE.search(s): return None
    if re.fullmatch(r"[\d\W_]+", s): return None
    return s

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = con.execute(
    "SELECT path FROM asset WHERE location='115' AND medium='video' "
    "AND (creator IS NULL OR creator='') "
    "AND path NOT LIKE 'B:\\创作者\\%' AND path NOT LIKE 'B:\\番号\\%' "
    "AND path NOT LIKE 'B:\\西方\\%'").fetchall()
con.close()

# 按二层目录聚合
dirs = defaultdict(int)
for (p,) in rows:
    ps = [x for x in p.replace("B:\\", "").split("\\") if x]
    dirs["\\".join(ps[:2]) if len(ps) >= 2 else ps[0]] += 1

print(f"无归属且仍在旧顶层的视频 {len(rows):,} 个，涉及二层目录 {len(dirs):,} 个")

hits = []
for d, n in dirs.items():
    leaf = d.split("\\")[-1]
    names, prec = [], ""
    for m in HIGH.findall(leaf):
        v = ok(m)
        if v and v not in names: names.append(v); prec = "高「」"
    if not names:
        for m in MID.findall(leaf):
            v = ok(m)
            if v and v not in names: names.append(v); prec = "中【】"
    if names:
        hits.append({"精度": prec, "归属": names[0], "同框": "|".join(names[1:]),
                     "视频数": n, "目录": d})

hits.sort(key=lambda x: (x["精度"], -x["视频数"]))
c = Counter(h["精度"] for h in hits)
print(f"\n命中 {len(hits)} 个目录 / {sum(h['视频数'] for h in hits):,} 个视频   {dict(c)}")
for lab in ("高「」", "中【】"):
    sel = [h for h in hits if h["精度"] == lab]
    if not sel: continue
    print(f"\n=== {lab}  {len(sel)} 个 ===")
    for h in sorted(sel, key=lambda x: -x["视频数"])[:14]:
        extra = f"  +同框 {h['同框']}" if h["同框"] else ""
        print(f"  {h['视频数']:>4} 个  {h['归属'][:18]:<20}{extra:<22} ← {h['目录'].split(chr(92))[-1][:44]}")

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["精度", "归属", "同框", "视频数", "目录"])
    w.writeheader(); w.writerows(hits)
print(f"\n→ {OUT}")

if not APPLY:
    print("加 --apply 写入"); sys.exit(0)

con = sqlite3.connect(DB); cur = con.cursor()
n_up = 0
for h in hits:
    ids = [r[0] for r in cur.execute(
        "SELECT id FROM asset WHERE location='115' AND (creator IS NULL OR creator='') "
        "AND path LIKE ?", ("B:\\" + h["目录"] + "\\%",))]
    ids += [r[0] for r in cur.execute(
        "SELECT id FROM asset WHERE location='115' AND (creator IS NULL OR creator='') "
        "AND path = ?", ("B:\\" + h["目录"],))]
    if not ids: continue
    qm = ",".join("?" * len(ids))
    cur.execute(f"UPDATE asset SET creator=? WHERE id IN ({qm})", [h["归属"]] + ids)
    n_up += len(ids)
con.commit()
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
    for nm in [h["归属"]] + [x for x in h["同框"].split("|") if x]:
        if nm.lower() in have: continue
        try:
            gql('mutation($n:String!){performerCreate(input:{name:$n}){id}}', {"n": nm})
            have.add(nm.lower()); new += 1
        except Exception as e:
            print("  失败:", nm, e)
print(f"Stash 新建 Performer {new}")
con.close()
