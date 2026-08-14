#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按归属映射 CSV 给 Stash 场景绑定 Performer。

CSV 字段: 页, 格位, 判定类型, 归属, 文件名
  判定类型 = 创作者 → 绑 Performer
  判定类型 = 转载渠道 / 待识别 → 跳过（渠道不建 Performer，见识别台账）

**只加不删**：已有的 Performer 关联保留，新的追加上去。
用法: python rm-assign.py <映射.csv> [--apply]
"""
import json, sys, os, csv, urllib.request, urllib.error
from collections import Counter

URL = "http://127.0.0.1:9999/graphql"
CSVF = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else \
       r"R:\Resources\Migration_Logs\足交合集-归属映射.csv"
APPLY = "--apply" in sys.argv


def gq(q, v=None):
    b = {"query": q}
    if v:
        b["variables"] = v
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            URL, data=json.dumps(b).encode(),
            headers={"Content-Type": "application/json"}), timeout=90).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode("utf-8", "ignore")[:300])
    if "errors" in r:
        raise RuntimeError(r["errors"][0].get("message", "")[:300])
    return r["data"]


rows = list(csv.DictReader(open(CSVF, encoding="utf-8-sig")))
want = [r for r in rows if r["判定类型"] == "创作者" and r["归属"]]
want_st = [r for r in rows if r["判定类型"] == "制作公司" and r["归属"]]
print(f"{os.path.basename(CSVF)}: {len(rows)} 行 → Performer {len(want)} 条 / Studio {len(want_st)} 条")

# ── 1. 确保 Performer 都存在 ──
perfs = {p["name"]: p for p in gq(
    '{findPerformers(filter:{per_page:-1}){performers{id name alias_list}}}')["findPerformers"]["performers"]}
alias2name = {}
for n, p in perfs.items():
    alias2name[n.lower()] = n
    for a in (p.get("alias_list") or []):
        alias2name[a.lower().lstrip("@")] = n

need = sorted({r["归属"] for r in want})
missing = [n for n in need if n.lower() not in alias2name]
if missing:
    print(f"\n缺失的 Performer（将新建）: {', '.join(missing)}")
    for n in missing:
        if APPLY:
            gq('mutation($n:String!,$a:[String!]){performerCreate(input:{name:$n,alias_list:$a}){id}}',
               {"n": n, "a": [f"@{n}"]})
            print(f"  ✓ 建 {n}")
        else:
            print(f"  [建] {n}")
    if APPLY:
        perfs = {p["name"]: p for p in gq(
            '{findPerformers(filter:{per_page:-1}){performers{id name alias_list}}}')["findPerformers"]["performers"]}
        alias2name = {}
        for n, p in perfs.items():
            alias2name[n.lower()] = n
            for a in (p.get("alias_list") or []):
                alias2name[a.lower().lstrip("@")] = n

# ── 2. 文件名 → 场景 ──
scenes = gq('{findScenes(filter:{per_page:-1}){scenes{id files{path basename} performers{id name}}}}'
            )["findScenes"]["scenes"]
by_base = {}
for s in scenes:
    for f in (s.get("files") or []):
        b = f.get("basename") or os.path.basename(f.get("path", ""))
        by_base.setdefault(b, []).append(s)
print(f"Stash 场景 {len(scenes)}，可按文件名索引 {len(by_base)}")

plan, miss_scene, miss_perf = [], [], []
for r in want:
    fn = r["文件名"]
    cands = by_base.get(fn)
    if not cands:
        miss_scene.append(fn); continue
    pname = alias2name.get(r["归属"].lower())
    if not pname or pname not in perfs:
        miss_perf.append(r["归属"]); continue
    s = cands[0]
    pid = perfs[pname]["id"]
    have = {p["id"] for p in (s.get("performers") or [])}
    if pid in have:
        continue
    plan.append((s["id"], sorted(have | {pid}), pname, fn))

print(f"\n匹配上场景 {len(want)-len(miss_scene)} / {len(want)}")
if miss_scene:
    print(f"  ⚠ 找不到对应场景的文件 {len(miss_scene)} 个，例：")
    for f in miss_scene[:4]:
        print(f"      {f[:80]}")
if miss_perf:
    print(f"  ⚠ 找不到 Performer: {set(miss_perf)}")
print(f"需要新增关联 {len(plan)} 条（已正确的不重复处理）")

c = Counter(p[2] for p in plan)
for k, v in c.most_common():
    print(f"    {v:>3}  {k}")

# ── 3. 制作公司 → Studio ──
# 注意：Stash 一个场景只能有一个 Studio。这些场景当前挂的是按目录建的
# 「合集-洛丽塔 多创作者」，用真实制作方（糖心VLOG 等）覆盖是语义上的改进。
st_plan = []
if want_st:
    studios = {s["name"]: s for s in gq(
        '{findStudios(filter:{per_page:-1}){studios{id name}}}')["findStudios"]["studios"]}
    sc_studio = {s["id"]: (s.get("studio") or {}).get("name") for s in
                 gq('{findScenes(filter:{per_page:-1}){scenes{id studio{name}}}}')["findScenes"]["scenes"]}
    for r in want_st:
        cands = by_base.get(r["文件名"])
        if not cands:
            continue
        st = studios.get(r["归属"])
        if not st:
            print(f"  ⚠ 找不到 Studio: {r['归属']}"); continue
        s = cands[0]
        if sc_studio.get(s["id"]) == r["归属"]:
            continue
        st_plan.append((s["id"], st["id"], r["归属"], sc_studio.get(s["id"]), r["文件名"]))
    print(f"\nStudio 需改绑 {len(st_plan)} 条")
    for sid, stid, newn, oldn, fn in st_plan[:6]:
        print(f"    {oldn} → {newn}   {fn[:56]}")

if not APPLY:
    print("\n== 预览模式，加 --apply 执行 ==")
    sys.exit(0)

print("\n=== 执行 Performer ===")
done = 0
for sid, pids, pname, fn in plan:
    gq('mutation($id:ID!,$p:[ID!]){sceneUpdate(input:{id:$id,performer_ids:$p}){id}}',
       {"id": sid, "p": pids})
    done += 1
    if done % 20 == 0:
        print(f"  {done}/{len(plan)}")
print(f"完成 {done} 条 Performer 关联")

if st_plan:
    print("\n=== 执行 Studio ===")
    d2 = 0
    for sid, stid, newn, oldn, fn in st_plan:
        gq('mutation($id:ID!,$s:ID){sceneUpdate(input:{id:$id,studio_id:$s}){id}}',
           {"id": sid, "s": stid})
        d2 += 1
    print(f"完成 {d2} 条 Studio 改绑")
