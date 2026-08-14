#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio 迁移 —— 把「创作者目录」建成 Stash 的 Studio 并绑定场景。

背景：原方案把所有创作者（含 3D 社团、男主频道）都塞进 Performer，Studio 维度完全没用（studio_count=0）。
      Stash 的模型是 Studio=制作方/频道，Performer=出镜者。混在一起导致「按制作者找」和「按出镜者找」分不开。

本脚本**只新增，不删除**：
  - 每个顶层创作者目录 → 一个 Studio
  - 每个场景 → 绑定到其顶层目录对应的 Studio
  - Performer 一律不动（3D 社团那些冗余的 Performer 留给人工确认后再删）

用法: python rm-studio.py [--dry]
"""
import json, sys, urllib.request

URL = "http://127.0.0.1:9999/graphql"
DRY = "--dry" in sys.argv
PREFIX = "R:\\Media\\创作者\\"


def gq(query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if "errors" in r:
        raise RuntimeError(r["errors"])
    return r["data"]


print(f"{'== 预览模式 ==' if DRY else '== 正式执行 =='}")

scenes = gq('{findScenes(filter:{per_page:-1}){scenes{id studio{id name} files{path}}}}')["findScenes"]["scenes"]
print(f"场景 {len(scenes)}")

# 场景 -> 顶层目录
by_dir = {}
skipped = 0
for s in scenes:
    p = s["files"][0]["path"] if s.get("files") else ""
    if not p.startswith(PREFIX):
        skipped += 1
        continue
    top = p[len(PREFIX):].split("\\")[0]
    by_dir.setdefault(top, []).append(s)
print(f"顶层目录 {len(by_dir)} 个，不在创作者目录下的场景 {skipped} 个")

existing = {st["name"]: st["id"] for st in gq('{findStudios(filter:{per_page:-1}){studios{id name}}}')["findStudios"]["studios"]}
print(f"已有 Studio {len(existing)} 个")

created = bound = already = 0
for top, ss in sorted(by_dir.items(), key=lambda kv: -len(kv[1])):
    sid = existing.get(top)
    if not sid:
        if DRY:
            print(f"  [建] {top:<34} ({len(ss)} 场景)")
            created += 1
            continue
        sid = gq('mutation($n:String!){studioCreate(input:{name:$n}){id}}', {"n": top})["studioCreate"]["id"]
        existing[top] = sid
        created += 1

    need = [s["id"] for s in ss if not (s.get("studio") and s["studio"]["name"] == top)]
    already += len(ss) - len(need)
    if not need:
        continue
    if DRY:
        print(f"  [绑] {top:<34} {len(need)} 个场景")
        bound += len(need)
        continue
    for i in range(0, len(need), 200):
        chunk = need[i:i + 200]
        gq('mutation($ids:[ID!],$sid:ID){bulkSceneUpdate(input:{ids:$ids,studio_id:$sid}){id}}',
           {"ids": chunk, "sid": sid})
        bound += len(chunk)
    print(f"  ✓ {top:<34} 建Studio+绑定 {len(need)} 个场景")

print(f"\n新建 Studio {created}   绑定场景 {bound}   本已正确 {already}")

if not DRY:
    st = gq('{stats{scene_count performer_count tag_count studio_count}}')["stats"]
    print(f"现状: 场景 {st['scene_count']} / Performer {st['performer_count']} / "
          f"Tag {st['tag_count']} / Studio {st['studio_count']}")

# 提示哪些 Performer 现在是冗余的（纯制作方，不出镜）
PURE_MAKER = ["梅麻呂3D", "アトリエこぶ", "ドールハウス", "フリム", "ぬるぬる坊主",
              "不燃ごみ太郎", "PastaPaprika", "楠里xiaosibao", "Haadxee"]
perfs = {p["name"]: p for p in gq('{findPerformers(filter:{per_page:-1}){performers{id name scene_count}}}')["findPerformers"]["performers"]}
print("\n--- 以下 Performer 现在与同名 Studio 重复（纯制作方，不出镜），建议人工确认后删除 ---")
for n in PURE_MAKER:
    if n in perfs:
        print(f"    id={perfs[n]['id']:<5} {n:<24} {perfs[n]['scene_count']} 场景")
print("    （本脚本不自动删。删除命令：mutation{performerDestroy(id:\"<id>\")} ）")
