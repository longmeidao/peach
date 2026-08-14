#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把关键帧识别结果落地到 Stash：建 Studio / Performer，给已有 Performer 补别名。

数据来源：
  R:\\Resources\\Migration_Logs\\足交合集-识别台账.md
  R:\\Resources\\Migration_Logs\\洛丽塔合集-识别台账.md

**只新增，不删除、不改已有场景的归属。** 幂等：重复运行不会造成重复条目。

用法: python rm-applyid.py [--apply]     # 默认预览
"""
import json, sys, urllib.request, urllib.error

URL = "http://127.0.0.1:9999/graphql"
APPLY = "--apply" in sys.argv


def gq(q, v=None):
    b = {"query": q}
    if v:
        b["variables"] = v
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            URL, data=json.dumps(b).encode(),
            headers={"Content-Type": "application/json"}), timeout=60).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode("utf-8", "ignore")[:300])
    if "errors" in r:
        raise RuntimeError(r["errors"][0].get("message", "")[:300])
    return r["data"]


# ── 专业制作公司 → Studio ─────────────────────────────
STUDIOS = [
    ("麻豆传媒映画", ["麻豆传媒", "麻豆", "MDAPP2", "MDAPP2.COM"]),
    ("糖心VLOG", ["糖心", "TangxinVlog", "txvlog", "txvlog.com",
                  "TX010.TV", "TX011.TV", "TX017.TV", "TX019.TV",
                  "TX028.TV", "TX031.TV", "TX032.TV", "TX033.TV"]),
    ("星空无限传媒", ["星空无限", "xingkong018", "xingkong018.com"]),
    ("扣扣传媒", ["qqcm01", "qqcm02", "qqcm01.com", "qqcm02.com"]),
]

# ── 新创作者 → Performer（名称, 别名）────────────────
NEW_PERFORMERS = [
    # 合集-足交
    ("xuenai99", ["@xuenai99", "xuenai99"]),
    ("MiyanoKoihana", ["@MiyanoKoihana", "MiyanoKoihana", "Miyano Koihana"]),
    ("Jzu77", ["@Jzu77", "Jzu77"]),
    ("xtao09", ["@xtao09", "xtao09"]),
    ("JuicybabyS", ["@JuicybabyS", "JuicybabyS"]),
    ("keke_666", ["@_keke_666", "@keke_666", "keke_666"]),
    ("jiojioyishujia", ["@jiojioyishujia", "jiojioyishujia"]),
    ("meili_s1", ["@meili_s1", "meili_s1"]),
    ("baobaosss", ["@baobaosss", "baobaosss", "baobaossbot", "她媛5原创"]),
    ("030owner", ["@030owner", "030owner", "o3owner"]),
    ("CiciC1j", ["@CiciC1j", "CiciC1j", "CiciCola", "@Cicicola"]),
    ("XiaoSiBao", ["@XiaoSiBao", "XiaoSiBao", "xiaosibao"]),
    # 合集-洛丽塔
    ("pangyedechi", ["@pangyedechi", "pangyedechi", "pangdeixing"]),
    ("又又酱", ["@youyoujiang520", "youyoujiang520", "又又酱"]),
    ("Babybaobaoya", ["@Babybaobaoya", "Babybaobaoya"]),
    ("ouikk蟾蜍", ["@ouikk88x", "ouikk88x", "ouikk", "ouikk蟾蜍"]),
    ("刘总246857", ["刘总246857", "刘总"]),
    ("wanw2002", ["@wanw2002", "wanw2002", "twi:wanw2002"]),
    ("rosemary_xyyyy", ["@rosemary_xyyyy", "rosemary_xyyyy"]),
    ("yukiro913347", ["yukiro913347", "@yukiro913347"]),
    ("Louis00135", ["@Louis00135", "Louis00135", "洛洛幻想屋"]),
    ("XFmugou", ["@XFmugou", "XFmugou"]),
    ("NMTX77", ["@NMTX77", "NMTX77"]),
    ("JK_0571", ["@JK_0571", "JK_0571"]),
    ("王二", ["王二", "小放牛郎织女星"]),
    ("91野猫咪", ["91野猫咪", "野猫咪"]),
    ("fanfan_2023", ["@fanfan_2023", "fanfan_2023"]),
    ("xanax", []),
    # 沐沐是古河君的**搭档**，是另一个人 —— 绝不能当成古河君的别名，
    # 否则两人的内容会混成一个 Performer。
    ("沐沐", ["沐沐"]),
]

# ── 给已有 Performer 补别名（本次识别出的账号）──────
ADD_ALIASES = {
    "哆米":            ["Dollmii24", "@Dollmii24"],
    "aybao52":         ["@aybao52", "aybao522", "@aybao522"],
    "uu_oui":          ["X:uu_oui"],
    "皮皮娘":           ["pipiniang520", "@pipiniang520"],
    # 只放 古河X沐沐（这是合作标记），不放裸的「沐沐」—— 那是另一个人
    "古河君":           ["Furukawajun", "@Furukawajun", "古河X沐沐"],
    "小芽芽不乖":        ["21442644", "91社区21442644"],
    "LovELolita":      ["LoveLolita"],
    "小欣奈":           ["lovewxnn", "@lovewxnn"],
    "wink是可爱的wink": ["winkwink333", "@winkwink333"],
}

print("== 预览模式 ==" if not APPLY else "== 正式执行 ==")

studios = {s["name"]: s for s in gq(
    '{findStudios(filter:{per_page:-1}){studios{id name aliases}}}')["findStudios"]["studios"]}
perfs = {p["name"]: p for p in gq(
    '{findPerformers(filter:{per_page:-1}){performers{id name alias_list}}}')["findPerformers"]["performers"]}
print(f"现有 Studio {len(studios)} / Performer {len(perfs)}\n")

# 1. Studio
print("── 制作公司 → Studio ──")
for name, al in STUDIOS:
    if name in studios:
        print(f"  已存在  {name}")
        continue
    print(f"  {'[建]' if not APPLY else '✓ 建'} {name}   别名 {len(al)} 个")
    if APPLY:
        gq('mutation($n:String!,$a:[String!]){studioCreate(input:{name:$n,aliases:$a}){id}}',
           {"n": name, "a": al})

# 2. 新 Performer
print("\n── 新创作者 → Performer ──")
n_new = 0
for name, al in NEW_PERFORMERS:
    if name in perfs:
        print(f"  已存在  {name}")
        continue
    n_new += 1
    print(f"  {'[建]' if not APPLY else '✓ 建'} {name:<20} 别名: {', '.join(al)}")
    if APPLY:
        gq('mutation($n:String!,$a:[String!]){performerCreate(input:{name:$n,alias_list:$a}){id}}',
           {"n": name, "a": al})

# 3. 给已有 Performer 补别名
print("\n── 已有 Performer 补别名 ──")
for name, add in ADD_ALIASES.items():
    p = perfs.get(name)
    if not p:
        print(f"  ⚠ 找不到 {name}，跳过")
        continue
    cur = set(p.get("alias_list") or [])
    new = [a for a in add if a not in cur]
    if not new:
        print(f"  无需改动  {name}")
        continue
    print(f"  {'[补]' if not APPLY else '✓ 补'} {name:<18} +{', '.join(new)}")
    if APPLY:
        gq('mutation($id:ID!,$a:[String!]){performerUpdate(input:{id:$id,alias_list:$a}){id}}',
           {"id": p["id"], "a": sorted(cur | set(new))})

print(f"\n新建 Studio {sum(1 for n,_ in STUDIOS if n not in studios)} / 新建 Performer {n_new}")
if not APPLY:
    print("\n加 --apply 正式执行")
else:
    s2 = gq('{findStudios(filter:{per_page:1}){count} findPerformers(filter:{per_page:1}){count}}')
    print(f"现状: Studio {s2['findStudios']['count']} / Performer {s2['findPerformers']['count']}")
