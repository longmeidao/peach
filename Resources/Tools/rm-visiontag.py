#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉打标落库 —— 把「读接触印相得到的标签」写进 ledger。

为什么需要：文件名打标只覆盖 41%，剩下 5,467 个视频的名字不含内容信息
（`001.mp4`、UUID、Telegram 媒体 ID）。这批只能看画面。

杠杆：这 5,467 个归到 167 个创作者，**前 60 个覆盖 96%**。
读一张代表图平均能覆盖 88 个视频。

⚠️ 创作者级标签只是「典型内容」，不代表该创作者每条都符合。
   所以写成 source='vision-creator' + confidence 0.6，
   与逐条读的 source='vision'（0.95）区分，将来逐条读到可以覆盖。

用法:
  python rm-visiontag.py --file 标注.json          预览
  python rm-visiontag.py --file 标注.json --apply  写入

标注.json 格式：
  {"creator": {"luckydog22": ["丝袜","后入","美臀"], ...},
   "asset":   {"12345": ["足交","主观视角"], ...}}
"""
import json, sys, sqlite3
from collections import Counter

DB = r"R:\Resources\Intake\ledger.db"
A = sys.argv[1:]
def _o(n, d=None): return A[A.index(n) + 1] if n in A else d
FILE = _o("--file")
APPLY = "--apply" in A
if not FILE:
    print(__doc__); sys.exit(1)

data = json.load(open(FILE, encoding="utf-8"))
con = sqlite3.connect(DB); cur = con.cursor()

rows = []          # (asset_id, tag, conf, source)
stat = Counter()

# 创作者级
for creator, tags in (data.get("creator") or {}).items():
    ids = [r[0] for r in cur.execute(
        "SELECT id FROM asset WHERE medium='video' AND creator=?", (creator,))]
    if not ids:
        print(f"  ⚠️ 找不到创作者「{creator}」，跳过"); continue
    for aid in ids:
        for t in tags:
            rows.append((aid, t, 0.6, "vision-creator"))
    stat[creator] = len(ids)
    print(f"  {len(ids):>5} 个  {creator[:28]:<30} → {'、'.join(tags)}")

# 单条级
for aid, tags in (data.get("asset") or {}).items():
    for t in tags:
        rows.append((int(aid), t, 0.95, "vision"))

print(f"\n合计将写入 {len(rows):,} 条标签，覆盖 {len(set(r[0] for r in rows)):,} 个视频")
tagc = Counter(r[1] for r in rows)
print("标签分布:", "、".join(f"{k}({v})" for k, v in tagc.most_common(14)))

if not APPLY:
    print("\n预览。加 --apply 写入。")
    con.close(); sys.exit(0)

cur.executemany(
    "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)", rows)
con.commit()
print(f"\n已写入。")
v = cur.execute("SELECT count(*) FROM asset WHERE medium='video'").fetchone()[0]
cov = cur.execute("SELECT count(DISTINCT asset_id) FROM asset_tag "
                  "WHERE source IN ('name','r18','vision','vision-creator')").fetchone()[0]
print(f"内容标签覆盖：{cov:,}/{v:,} = {cov/v*100:.0f}%")
con.close()
