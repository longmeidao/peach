#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理旧误判标签 —— 按当前 rm-tagmap.ps1 重算每个场景应有的标签，移除多余的。

背景：rm-import 只加不删，所以旧词典里 3p / cn / OL / 2d / 91 / TG / sm 这些
      无词边界的短关键词造成的误判标签一直挂在场景上。

安全：
  - 只移除「当前词典不会赋予、且来源是脚本可推导的」标签
  - 技术类标签（画质/时长/屏向/帧率）由元数据推导，不在本脚本管辖范围，一律保留
  - 目录级标签（DirTags）也重算
  - 默认 --dry，加 --apply 才真的动

用法: python rm-tagclean.py [--apply]
"""
import json, re, subprocess, sys, urllib.request, urllib.error
from collections import Counter

URL = "http://127.0.0.1:9999/graphql"
APPLY = "--apply" in sys.argv
PREFIX = "R:\\Media\\创作者\\"

# 由元数据推导、与文件名无关的标签，一律不碰
PROTECTED = {"真人", "4K", "2K", "1080P", "720P", "低画质", "横屏", "竖屏", "高帧率",
             "短片-2分内", "中片-10分内", "长片-30分内", "长片-30分上"}


def gq(q, v=None):
    b = {"query": q}
    if v: b["variables"] = v
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request(
            URL, data=json.dumps(b).encode(), headers={"Content-Type": "application/json"}), timeout=120).read())["data"]
    except urllib.error.HTTPError as e:
        print("Stash 错误:", e.read().decode("utf-8", "ignore")[:300]); sys.exit(1)


# 从 PowerShell 词典里读出 TagMap / DirTags
def parse_ps_hashtable(text, varname):
    """直接解析 rm-tagmap.ps1 里的 $Global:XXX = [ordered]@{ 'k' = @('a','b') ... }
    不依赖 PowerShell 子进程 —— 那条路在本机不稳定。"""
    m = re.search(r"\$Global:" + varname + r"\s*=\s*\[ordered\]@\{", text)
    if not m:
        return {}
    i = m.end(); depth = 1
    while i < len(text) and depth:                 # 找到配对的右花括号
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        i += 1
    body = text[m.end():i - 1]
    body = re.sub(r"#[^\n]*", "", body)            # 去注释
    out = {}
    for km, in_ in re.findall(r"'((?:[^']|'')+)'\s*=\s*@\(([^)]*)\)", body, re.S):
        vals = [v.strip().strip("'").replace("''", "'")
                for v in re.findall(r"'(?:[^']|'')*'", in_)]
        out[km.replace("''", "'")] = [v for v in vals if v]
    return out


NEWF = r"R:\Resources\Tools\rm-tagmap.ps1"
OLDF = r"R:\Resources\Migration_Logs\rm-tagmap-备份-20260813.ps1"
new_src = open(NEWF, encoding="utf-8").read()
old_src = open(OLDF, encoding="utf-8").read()
d = {"TagMap": parse_ps_hashtable(new_src, "TagMap"), "DirTags": parse_ps_hashtable(new_src, "DirTags")}
OLD = {"TagMap": parse_ps_hashtable(old_src, "TagMap"), "DirTags": parse_ps_hashtable(old_src, "DirTags")}
if len(d["TagMap"]) < 50 or len(OLD["TagMap"]) < 50:
    print("词典解析异常，中止"); sys.exit(1)
print(f"新词典 {len(d['TagMap'])} 条 / 旧词典 {len(OLD['TagMap'])} 条")
TAGMAP = {k: (v if isinstance(v, list) else [v]) for k, v in d["TagMap"].items()}
DIRTAGS = {k: (v if isinstance(v, list) else [v]) for k, v in d["DirTags"].items()}
print(f"词典: {len(TAGMAP)} 个标签规则 / {len(DIRTAGS)} 个目录规则")

scenes = gq('{findScenes(filter:{per_page:-1}){scenes{id files{path} tags{id name}}}}')["findScenes"]["scenes"]
print(f"场景 {len(scenes):,}")

removed = Counter()
plan = []
for s in scenes:
    if not s.get("files"): continue
    p = s["files"][0]["path"]
    rel = p[len(PREFIX):] if p.startswith(PREFIX) else p
    top = rel.split("\\")[0]
    low = rel.lower()

    def assign(tm, dt):
        r = set()
        for tag, kws in tm.items():
            for kw in kws:
                if kw and kw.lower() in low:
                    r.add(tag); break
        for t in dt.get(top, []):
            r.add(t)
        return r

    should = assign(TAGMAP, DIRTAGS)
    was = assign(OLD["TagMap"], OLD["DirTags"])
    # 只删「旧词典会给、新词典不给」的 —— 即被修掉的短关键词造成的误判。
    # 人工标注（多女出镜/男主频道/身份待确认…）两边都不会给，因此不受影响。
    bogus = was - should

    have = {t["name"]: t["id"] for t in (s.get("tags") or [])}
    extra = [n for n in have if n in bogus and n not in PROTECTED]
    if extra:
        plan.append((s["id"], [have[n] for n in extra], extra,
                     [have[n] for n in have if n not in extra]))
        for n in extra: removed[n] += 1

print(f"\n将移除的标签（{len(plan):,} 个场景受影响）：")
for n, c in removed.most_common(40):
    print(f"  {c:>5}  {n}")
print(f"\n合计移除 {sum(removed.values()):,} 条标签关联")

if not APPLY:
    print("\n== 预览模式，未改动。加 --apply 执行 ==")
    sys.exit(0)

print("\n=== 执行 ===")
done = 0
for sid, _, extra, keep_ids in plan:
    gq('mutation($id:ID!,$t:[ID!]){sceneUpdate(input:{id:$id,tag_ids:$t}){id}}',
       {"id": sid, "t": keep_ids})
    done += 1
    if done % 200 == 0: print(f"  {done}/{len(plan)}")
print(f"完成 {done} 个场景")
st = gq('{stats{scene_count tag_count}}')["stats"]
print(f"现状: 场景 {st['scene_count']} / Tag {st['tag_count']}")
