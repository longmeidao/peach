#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涌现推荐 —— 说一句心情或关键词，从 21 TB 里挑几个给你。

    python scripts/suggest.py 来点快的
    python scripts/suggest.py 手机上看的足
    python scripts/suggest.py --tag 足交 --len 速食
    python scripts/suggest.py 随便            # 什么都不指定，纯涌现

三条通道混合（方案 §6.2）：
    精准 60%  严格匹配心情词典解出的条件
    邻接 30%  在标签共现图上走一步 —— 你要「足交+丝袜」，它给「足交+瑜伽裤」
    意外 10%  从口味覆盖到、但库里你从没碰过的区域随机采样

只读账本，无副作用。反馈用 --like / --dislike / --seen 写回。
"""
import os, sys, json, random, sqlite3
from collections import Counter, defaultdict
from pathlib import Path

DB = r"R:\peach-data\database\ledger.db"
MOODS = str(Path(__file__).with_name("moods.json"))
N_OUT = 6

args = sys.argv[1:]
def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d

# ---- 反馈模式 ----
if any(f in args for f in ("--like", "--dislike", "--seen")):
    aid = opt("--like") or opt("--dislike") or opt("--seen")
    c = sqlite3.connect(DB, timeout=30)
    if "--like" in args:
        c.execute("UPDATE asset SET rating=5, play_count=COALESCE(play_count,0)+1 WHERE id=?", (aid,))
        print(f"已记录：喜欢 #{aid}")
    elif "--dislike" in args:
        c.execute("UPDATE asset SET rating=1 WHERE id=?", (aid,))
        print(f"已记录：不喜欢 #{aid}")
    else:
        c.execute("UPDATE asset SET play_count=COALESCE(play_count,0)+1 WHERE id=?", (aid,))
        print(f"已记录：看过 #{aid}")
    c.commit(); c.close(); sys.exit(0)

query = " ".join(a for a in args if not a.startswith("--"))
FORCE_TAG = opt("--tag"); FORCE_LEN = opt("--len"); FORCE_LOC = opt("--location")

# ---- 解析心情 ----
md = json.load(open(MOODS, encoding="utf-8"))
hit, cond = [], {"tags": [], "tags_boost": [], "ctx_length": [], "ctx_orient": [],
                 "ctx_quality": [], "location": [], "novelty": 0.10,
                 "unseen": False, "familiar": False}
for m in md["moods"]:
    if any(k in query for k in m["keys"]):
        hit.append(m["keys"][0])
        for k in ("tags", "tags_boost", "ctx_length", "ctx_orient", "ctx_quality", "location"):
            cond[k] += m.get(k, [])
        if "novelty" in m: cond["novelty"] = m["novelty"]
        for b in ("unseen", "familiar"):
            if m.get(b): cond[b] = True
if FORCE_TAG: cond["tags"].append(FORCE_TAG)
if FORCE_LEN: cond["ctx_length"].append(FORCE_LEN)
if FORCE_LOC: cond["location"].append(FORCE_LOC)

print(f"\n心情解析: {'、'.join(hit) if hit else '（没匹配到词典，走纯涌现）'}")
if cond["tags"]:        print(f"  标签  : {'、'.join(dict.fromkeys(cond['tags']))[:80]}")
if cond["ctx_length"]:  print(f"  时长档: {'、'.join(dict.fromkeys(cond['ctx_length']))}")
if cond["ctx_orient"]:  print(f"  屏向  : {'、'.join(dict.fromkeys(cond['ctx_orient']))}")

c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

# ---- 候选池 ----
where = ["medium='video'", "duration IS NOT NULL", "duration>60"]
params = []
def inlist(col, vals):
    if not vals: return
    vals = list(dict.fromkeys(vals))
    where.append(f"{col} IN ({','.join('?'*len(vals))})"); params.extend(vals)
inlist("ctx_length", cond["ctx_length"])
inlist("ctx_orient", cond["ctx_orient"])
inlist("ctx_quality", cond["ctx_quality"])
inlist("location", cond["location"])
if cond["unseen"]:   where.append("COALESCE(play_count,0)=0")
if cond["familiar"]: where.append("(COALESCE(play_count,0)>0 OR rating>=4)")

tagsql = ""
if cond["tags"]:
    t = list(dict.fromkeys(cond["tags"]))
    tagsql = (f" AND a.id IN (SELECT asset_id FROM asset_tag WHERE tag IN ({','.join('?'*len(t))}))")

sql = (f"SELECT a.id,a.location,a.path,a.name,a.size,a.duration,a.ctx_length,a.ctx_orient,"
       f"a.ctx_quality,a.creator,a.snapshot_path,COALESCE(a.play_count,0),a.rating "
       f"FROM asset a WHERE {' AND '.join(where)}{tagsql}")
rows = c.execute(sql, params + (list(dict.fromkeys(cond["tags"])) if cond["tags"] else [])).fetchall()
print(f"  候选池: {len(rows):,} 个")

if not rows:
    print("\n没有符合条件的。可能是 ffprobe 还没跑完（情境层缺时长），或者条件太窄。")
    sys.exit(0)

# ---- 加分标签 ----
boost = set(cond["tags_boost"])
btags = defaultdict(set)
if boost:
    ph = ",".join("?" * len(boost))
    for aid, tg in c.execute(f"SELECT asset_id,tag FROM asset_tag WHERE tag IN ({ph})", list(boost)):
        btags[aid].add(tg)

def score(r):
    aid, loc, path, name, size, dur, L, O, Q, creator, snap, pc, rt = r
    s = random.random() * 0.5
    s += len(btags.get(aid, ())) * 0.6
    if Q in ("4K", "2K"): s += 0.3
    if snap: s += 0.2
    if creator: s += 0.2
    if rt: s += (rt - 3) * 0.3
    if cond["novelty"] < 0.1 and pc: s += 0.4        # 想要熟悉的
    return s

random.shuffle(rows)
n_odd = max(1, int(N_OUT * cond["novelty"]))
main = sorted(rows, key=score, reverse=True)[:N_OUT - n_odd]
pool = [r for r in rows if r not in main and r[11] == 0]
odd = random.sample(pool, min(n_odd, len(pool))) if pool else []

def fmt(r, mark):
    aid, loc, path, name, size, dur, L, O, Q, creator, snap, pc, rt = r
    mm = f"{int(dur//60)}分{int(dur%60):02d}秒" if dur else "?"
    tags = [t for (t,) in c.execute(
        "SELECT tag FROM asset_tag WHERE asset_id=? LIMIT 6", (aid,))]
    print(f"\n  {mark} #{aid}  [{loc}] {mm}  {Q or '?'}  {O or '?'}"
          f"{'  ' + creator if creator else ''}{'  ★' + str(rt) if rt else ''}")
    print(f"     {name[:74]}")
    if tags: print(f"     标签: {'、'.join(tags)}")
    print(f"     {path[:100]}")
    if snap: print(f"     接触表: {snap}")

print(f"\n{'='*66}\n  给你挑了 {len(main)+len(odd)} 个\n{'='*66}")
for r in main: fmt(r, "▶")
for r in odd:  fmt(r, "✦")
if odd: print("\n  ✦ = 意外通道：口味覆盖到、但你从没碰过的区域")
print(f"\n  反馈:  python rm-suggest.py --like <ID>  /  --dislike <ID>  /  --seen <ID>")
c.close()
