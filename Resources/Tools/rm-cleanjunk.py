#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清掉 rm-115apply2.py 造出来的垃圾 Performer 和 ledger 里同形状的 creator 值。

根因：apply2 的 okname() 只挡了「合集措辞」，没挡「文件名」。
于是 `1(12).mp4` / `[emailprotected](3).mp4` / `3.mp4` 这类全被建成了 Performer，
再被下一轮分类器当成「已知创作者」，污染 PikPak 的分类结果。

只删：场景数为 0 且名字明显是文件名/垃圾的。
不删：任何绑了场景的；任何形状正常的短名（小桃、桉X、哆米 这些是真创作者）。

用法: python rm-cleanjunk.py [--apply]
"""
import re, sys, json, sqlite3, urllib.request

APPLY = "--apply" in sys.argv
DB = r"R:\Resources\Intake\ledger.db"

def gql(q, v=None):
    r = urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:9999/graphql",
        data=json.dumps({"query": q, "variables": v or {}}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    return json.loads(r.read())

# 明确是文件名/垃圾的形状
JUNK = re.compile(
    r"(\.(?:mp4|mkv|avi|wmv|mov|m4v|ts|flv|rmvb|mpg|jpg|jpeg|png|zip|rar|7z|part\d+)$"   # 带媒体扩展名
    r"|^\[emailprotected\]"                                                              # 网页抓来的混淆邮箱
    r"|^(?!@)[\d\W_]+$"        # 纯数字/符号 —— 但 @033158777 是账号，@ 是 handle 标记，排除
    r"|^(?:myfans|onlyfans|fansly|patreon|fanbox|jav|uncensored|selected|collection|"
    r"compilation|pack|videos|homemade|tokyo|funky)$)", re.I)

ps = gql('{findPerformers(filter:{per_page:-1}){performers{id name scene_count}}}')\
     ["data"]["findPerformers"]["performers"]
kill = [p for p in ps if p["scene_count"] == 0 and JUNK.search(p["name"])]
print(f"Performer 总数 {len(ps)}，判为垃圾且 0 场景的 {len(kill)} 个")
for p in kill[:12]:
    print(f"  #{p['id']:<5} {p['name'][:44]}")
if len(kill) > 12:
    print(f"  …共 {len(kill)} 个")

con = sqlite3.connect(DB); cur = con.cursor()
bad = [r[0] for r in cur.execute(
    "SELECT DISTINCT creator FROM asset WHERE creator IS NOT NULL AND creator<>''")
    if JUNK.search(r[0])]
n_asset = 0
if bad:
    qm = ",".join("?" * len(bad))
    n_asset = cur.execute(f"SELECT count(*) FROM asset WHERE creator IN ({qm})", bad).fetchone()[0]
print(f"\nledger 里同形状的 creator 值 {len(bad)} 种，涉及 {n_asset:,} 个资产")
for b in bad[:10]:
    print(f"  {b[:52]}")

if not APPLY:
    print("\n预演。确认后加 --apply 执行。")
    con.close(); sys.exit(0)

ok = 0
for p in kill:
    try:
        gql("mutation($i:ID!){performerDestroy(input:{id:$i})}", {"i": p["id"]}); ok += 1
    except Exception as e:
        print("  删除失败", p["name"], e)
print(f"\n已删 Performer {ok} 个")

if bad:
    qm = ",".join("?" * len(bad))
    cur.execute(f"UPDATE asset SET creator=NULL WHERE creator IN ({qm})", bad)
    con.commit()
    print(f"ledger 已清空 {cur.rowcount:,} 个资产的 creator")
tot = cur.execute("SELECT count(*) FROM asset WHERE location='115' AND medium='video' "
                  "AND creator IS NOT NULL AND creator<>''").fetchone()[0]
print(f"115 视频仍有归属：{tot:,}")
con.close()
