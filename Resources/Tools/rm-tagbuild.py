#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容标签重建 —— 从文件名/路径抽取行为、部位、服饰、身份、场景、属性六个维度。

为什么要做：库里 5,611 个标签，头部全是画质/时长/画幅这类技术标签，
真正的内容维度极稀薄（足交 172、中出内射 209、肛交 0）。
筛选、卡片信息、命名模板三件事全卡在这里。

词典怎么来的：先跑 tagsurvey 统计 24,980 个文件名里**实际出现**的词及频次，
只收命中 >=30 的，不凭空写。

⚠️ 匹配必须带边界，血泪教训：
   · `3P` 会命中 `[13P+5V]`  → 用 (?<![0-9A-Za-z])3P
   · `足`  会命中「满足/不足」 → 只收 足交/裸足/玉足/美足/丝足
   · `cos` 会命中 cost/Costa  → 要求 cosplay 或 cos + 分隔符
   · `VR`  会命中 VRAM        → 前后不接字母

用法:
  python rm-tagbuild.py              出预览（不写库）
  python rm-tagbuild.py --apply      写入 asset_tag，source='name'
  python rm-tagbuild.py --clear      先清掉上次本脚本写的，再写
"""
import re, sys, sqlite3
from collections import Counter, defaultdict

DB = r"R:\Resources\Intake\ledger.db"
SRC = "name"                     # 本脚本写入的 asset_tag.source 标记，便于回滚
A = sys.argv[1:]
APPLY = "--apply" in A
CLEAR = "--clear" in A

def W(*alts):                    # 中文词：直接拼
    return "(?:" + "|".join(alts) + ")"
def L(word):                     # 拉丁词：前后不接字母数字
    return r"(?<![0-9A-Za-z])" + word + r"(?![0-9A-Za-z])"

# 维度 → 标签 → 匹配式。标签名是最终写进库的规范名。
DICT = {
"行为": {
  "口交":   W("口交","吹箫","咬吹","blowjob","deepthroat"),
  "深喉":   W("深喉","deepthroat","イラマ"),
  "颜射":   W("颜射","顏射","facial"),
  "吞精":   W("吞精","飲精"),
  "足交":   W("足交","脚交","踩踏","踏射","footjob","풋잡"),
  "手交":   W("手交","打飞机","handjob"),
  "乳交":   W("乳交","パイズリ","titfuck"),
  "肛交":   W("肛交","后庭","肛门开发","anal","アナル"),
  "后入":   W("后入","後入","背后位","doggy"),
  "骑乘":   W("骑乘","騎乗","cowgirl"),
  "中出内射": W("中出","内射","內射","中だし","creampie"),
  "潮吹":   W("潮吹","喷水","噴水","失禁","squirt"),
  "调教":   W("调教","調教","捆绑","束缚","縛","bdsm","bondage"),
  "多人":   W("多人","双龙","轮姦","輪姦","群交","orgy","threesome") + "|" + L("3P") + "|" + L("4P") + "|" + L("5P"),
  "自慰":   W("自慰","紫薇","手淫","オナニー","masturbat"),
  "舔阴":   W("舔阴","舔穴","口爱","cunnilingus"),
  "按摩":   W("按摩","マッサージ","massage"),
  "榨精":   W("榨精","搾精"),
  "打桩":   W("打桩","抽插","猛肏","爆操","爆肏"),
  "射精":   W("射精","爆射","射了"),
},
"部位": {
  "足系":   W("足交","裸足","玉足","美足","丝足","絲足","脚交","美腿丝袜","foot","풋잡","맨발"),
  "美腿":   W("美腿","长腿","長腿","大腿","黑丝腿"),
  "美臀":   W("美臀","翘臀","蜜桃臀","肥臀","大屁股","巨臀"),
  "乳系":   W("巨乳","美乳","爆乳","贫乳","豊乳","おっぱい","big tits"),
  "马眼":   W("马眼","馬眼","尿道","铃口","鈴口","龟头责","龜頭"),
},
"服饰": {
  "丝袜":   W("丝袜","絲襪","黑丝","白丝","肉丝","灰丝","过膝袜","连裤袜","裤袜","渔网袜","stocking","pantyhose"),
  "制服":   W("制服","校服","水手服","OL制服","职业装") + "|" + L("JK"),
  "护士":   W("护士","護士","nurse"),
  "女仆":   W("女仆","女僕","メイド","maid"),
  "泳装":   W("泳装","泳裝","比基尼","bikini","水着"),
  "情趣内衣": W("情趣内衣","情趣内裤","情趣裝","开裆","開襠","无内","無內"),
  "角色扮演": W("cosplay","コスプレ","角色扮演","女装","换装") + r"|(?<![0-9A-Za-z])cos(?=[\s_\-\]\)【（])",
  "洛丽塔": W("洛丽塔","lolita","ロリータ","lo娘"),
  "高跟":   W("高跟","ハイヒール","heels"),
  "眼镜":   W("眼镜","眼鏡","メガネ","glasses"),
},
"身份": {
  "人妻":   W("人妻","少妇","少婦","熟女","若妻","主妇","主婦"),
  "萝莉":   W("萝莉","蘿莉","ロリ","loli"),
  "学生":   W("学生","學生","校花","女大学生") + "|" + L("JK"),
  "御姐":   W("御姐","女王","女神级","高冷"),
  "痴女":   W("痴女","淫女","浪女","母狗","母犬"),
  "素人":   W("素人","良家","邻家","鄰家","amateur"),
  "网红主播": W("网红","網紅","主播","直播","福利姬","嫩模","模特","推特网黄"),
  "绿帽NTR": W("绿帽","綠帽","淫妻","出轨","出軌") + "|" + L("NTR") + "|" + L("ntr"),
  "近亲":   W("近亲","近親","乱伦","亂倫","继母","繼母","姐弟","step ?sis","step ?mom"),
  "老师":   W("女老师","女教师","女教師","教师","老师"),
  "空姐":   W("空姐","空乘","客室乗務"),
  "秘书OL": W("秘书","秘書") + "|" + L("OL"),
},
"场景": {
  "户外露出": W("户外","戶外","露出","野外","公园","公園","街拍"),
  "车震":   W("车震","車震","车内","車內"),
  "浴室":   W("浴室","浴缸","洗澡","温泉","溫泉","风吕","風呂"),
  "酒店":   W("酒店","宾馆","賓館","hotel"),
  "办公室": W("办公室","辦公室","会议室","會議室","office"),
  "偷拍偷窥": W("偷拍","偷窥","偷窺","盗撮","盜攝","抄底","voyeur"),
},
"属性": {
  "无码":   W("无码","無碼","无修","無修","uncensored","流出无码"),
  "中文字幕": W("中文字幕","中字","字幕","subtitle"),
  "反差":   W("反差","日常反差","反差婊"),
  "泄密流出": W("泄密","洩密","流出","外流","私拍流出","leak"),
  "探花":   W("探花","猎艳","獵豔"),
  "露脸":   W("露脸","露臉","完全顔出","顔出し"),
  "主观视角": W("主观视角","主觀視角","第一视角","一人称") + "|" + L("POV"),
  "VR":     L("VR") + "|" + W("虚拟现实","180x180","3dh"),
  "合集":   W("合集","全集","大合集","精选","精選","compilation","collection"),
}}

# 预编译
PAT = {(dim, tag): re.compile(p, re.I) for dim, d in DICT.items() for tag, p in d.items()}
print(f"词典：{len(DICT)} 个维度 / {len(PAT)} 个标签\n")

con = sqlite3.connect(DB)
cur = con.cursor()
rows = cur.execute("SELECT id, name, path FROM asset WHERE medium='video'").fetchall()
print(f"扫描 {len(rows):,} 个视频…")

hits = defaultdict(list)          # (dim,tag) → [asset_id]
per_asset = Counter()
samples = defaultdict(list)
for aid, name, path in rows:
    text = ((name or "") + " " + (path or "")).lower()
    for key, rx in PAT.items():
        if rx.search(text):
            hits[key].append(aid)
            per_asset[aid] += 1
            if len(samples[key]) < 2:
                samples[key].append(name or "")

print(f"\n{'维度':<6}{'标签':<12}{'命中':>7}   样例")
print("-" * 88)
for dim in DICT:
    ks = sorted(((k, v) for k, v in hits.items() if k[0] == dim), key=lambda x: -len(x[1]))
    for (d, tag), ids in ks:
        s = (samples[(d, tag)][0] or "")[:40]
        print(f"{dim:<6}{tag:<12}{len(ids):>7}   {s}")
    print()

covered = len(per_asset)
print("=" * 88)
print(f"覆盖：{covered:,} / {len(rows):,} 个视频有了内容标签（{covered/len(rows)*100:.0f}%）")
print(f"平均每个 {sum(per_asset.values())/max(covered,1):.1f} 个标签，总计 {sum(len(v) for v in hits.values()):,} 条")

if not APPLY:
    print("\n以上为预览。逐条看过没有误命中，再加 --apply 写入。")
    con.close(); sys.exit(0)

if CLEAR:
    n = cur.execute("DELETE FROM asset_tag WHERE source=?", (SRC,)).rowcount
    print(f"\n已清除上次本脚本写入的 {n:,} 条")

batch = [(aid, tag, 0.85, SRC) for (dim, tag), ids in hits.items() for aid in ids]
cur.executemany("INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)", batch)
con.commit()
print(f"\n写入 {len(batch):,} 条（source='{SRC}'，可整体回滚）")
tot = cur.execute("SELECT count(DISTINCT tag) FROM asset_tag").fetchone()[0]
print(f"库里标签种类：{tot:,}")
con.close()
