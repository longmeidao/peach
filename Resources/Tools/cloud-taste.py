#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从网盘清单的「路径文本」提取口味信号与标签。纯文本分析，不读文件内容。

用法: python cloud-taste.py <inventory.csv> [inventory2.csv ...] --out <报告.txt>
"""
import csv, os, re, sys, json, urllib.request
from collections import Counter, defaultdict

args = sys.argv[1:]
OUT = os.path.expandvars(r"%USERPROFILE%\Desktop\网盘口味分析.txt")
if "--out" in args:
    i = args.index("--out"); OUT = args[i + 1]; del args[i:i + 2]
INVS = args or [os.path.expandvars(r"%USERPROFILE%\Desktop\115-inventory.csv")]

# ---------- 标签词典：维度层（已由五源交叉印证确立）----------
DIMENSIONS = {
    "足交/足控": r"足交|足控|恋足|戀足|丝足|絲足|footjob|foot\s?fetish|美足|脚|腳|"
                r"丝袜|絲襪|黑丝|黑絲|白丝|白絲|肉丝|肉絲|连裤袜|褲襪|pantyhose|stocking|"
                r"高跟|高跟鞋|heel|五指袜|瑜伽裤|足榨|踩踏",
    "马眼/尿道/龟头": r"马眼|馬眼|尿道|龟头|龜頭|鈴口|铃口|urethra|glans|虾线|蝦線|系带|繫帶",
    # 注意 \b69\b：不加边界会命中 569.avi / 669.mp4 这类纯数字文件名
    "口交/深喉/吞精": r"口交|口爆|吞精|深喉|颜射|顏射|blowjob|deepthroat|口活|口技|奶交|\b69\b",
    "毒龙/肛": r"毒龙|毒龍|舔肛|rimjob|analingus|肛交|后庭|後庭|菊|anal|屁眼|爆菊",
    "反差": r"反差|婊|表里|表裏|清纯|清純|学生|學生|校花|人前|背德",
    # 绝不能放 ts —— 会命中 GETS / TITS / .ts 扩展名，实测误判 1500 GB
    "扶她/伪娘": r"扶她|扶他|futanari|\bfuta\b|伪娘|偽娘|shemale|人妖|女装癖|女裝癖|newhalf|"
                r"ladyboy|\bts人|变性|變性|双性|雙性|蘑菇头|扶她自撸",
    "ASMR/音声": r"asmr|音声|音聲|耳舐|耳搔|催眠音|助眠|rj\d{6,}|同人音声",
    "NTR/绿帽": r"ntr|netorare|绿帽|綠帽|cuckold|寝取|睡取|出轨|出軌|淫妻|换妻|換妻|分享女友|分享老婆",
    "调教/束缚": r"调教|調教|束缚|束縛|捆绑|捆綁|bdsm|sm|femdom|女王|奴|羞辱|露出|野外",
    "制服/角色扮演": r"cos|cosplay|制服|jk|水手服|女仆|女僕|maid|护士|護士|空姐|教师|教師|"
                    r"ol|秘书|秘書|旗袍|兔女郎|bunny|洛丽塔|蘿莉塔|lolita",
    "萝莉/幼": r"萝莉|蘿莉|loli|嫩|白虎|贫乳|貧乳|幼|小只马|洛丽",
    "熟女/人妻": r"人妻|熟女|少妇|少婦|milf|母亲|母親|阿姨|御姐|姐姐",
    # \b3d\b 防止命中 UUID 里的十六进制（e3d92a4c 这种）
    "3D/动画": r"\b3d\b|3dcg|sfm|blender|koikatsu|honey\s?select|\bmmd\b|动画|動畫|同人|"
              r"hentai|里番|番剧|番劇|acg|galgame|黄油|黃油",
    "探花/约炮": r"探花|约炮|約炮|外围|外圍|嫖|楼凤|樓鳳|会所|會所|按摩|spa|技师|技師",
    "泄密/流出": r"泄密|洩密|流出|自拍|偷拍|私拍|不雅|门事件|門事件|网爆|網爆|绿播|裸聊",
    "内射/中出": r"内射|內射|中出|creampie|无套|無套|怀孕|懷孕|受孕",
    "多人/群": r"3p|4p|双飞|雙飛|群p|多人|轮|輪|乱交|亂交|harem|多女",
}
DIM_RE = {k: re.compile(v, re.I) for k, v in DIMENSIONS.items()}

VIDEO = {".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".mov", ".ts", ".flv", ".rmvb", ".mpg"}
JAVCODE = re.compile(r"\b([A-Z]{2,6}|\d{3}[A-Z]{2,6})-?(\d{2,4})\b")
FC2 = re.compile(r"FC2[\-_ ]?(?:PPV[\-_ ]?)?(\d{6,8})", re.I)
RJ = re.compile(r"\b(RJ\d{6,8})\b", re.I)

# ---------- 读清单 ----------
rows = []
for inv in INVS:
    if not os.path.exists(inv):
        print(f"跳过不存在: {inv}"); continue
    src = "115" if "115" in os.path.basename(inv) else ("pikpak" if "pikpak" in os.path.basename(inv).lower() else "?")
    with open(inv, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            try:
                r["size"] = int(r["size"])
            except (TypeError, ValueError):
                r["size"] = 0
            r["src"] = src
            r["full"] = os.path.join(r["path"], r["name"])
            rows.append(r)
print(f"读入 {len(rows):,} 条 / {sum(r['size'] for r in rows)/1024**4:.2f} TB")

vids = [r for r in rows if os.path.splitext(r["name"])[1].lower() in VIDEO]
print(f"其中视频 {len(vids):,} 个 / {sum(r['size'] for r in vids)/1024**4:.2f} TB")

# ---------- Stash 库存（用于差集）----------
stash_names = set()
stash_tags = {}
try:
    req = urllib.request.Request("http://127.0.0.1:9999/graphql",
        data=json.dumps({"query": "{findPerformers(filter:{per_page:-1}){performers{name alias_list scene_count}}"
                                  " findTags(filter:{per_page:-1}){tags{name scene_count}}}"}).encode(),
        headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())["data"]
    for p in d["findPerformers"]["performers"]:
        stash_names.add(p["name"].lower())
        for a in (p.get("alias_list") or []):
            stash_names.add(a.lower().lstrip("@"))
    stash_tags = {t["name"]: t["scene_count"] for t in d["findTags"]["tags"]}
    print(f"Stash: {len(stash_names)} 个名字, {len(stash_tags)} 个标签")
except Exception as e:
    print(f"Stash 未连上（{e}），跳过差集")

R, w = [], None
R = []; w = R.append
w("网盘口味与标签分析")
w(f"数据源: {', '.join(os.path.basename(i) for i in INVS)}")
w(f"规模: {len(rows):,} 文件 / {sum(r['size'] for r in rows)/1024**4:.2f} TB"
  f"（视频 {len(vids):,} 个 / {sum(r['size'] for r in vids)/1024**4:.2f} TB）")
w("说明: 纯路径文本分析，未读取任何文件内容。")
w("")

# ---------- 一、维度命中 ----------
w("=" * 78)
w("一、口味维度命中（按视频体积加权 —— 体积比文件数更能代表投入）")
w("=" * 78)
dim_n = Counter(); dim_sz = Counter(); dim_ex = defaultdict(list)
for r in vids:
    hay = r["full"]
    for k, rx in DIM_RE.items():
        if rx.search(hay):
            dim_n[k] += 1; dim_sz[k] += r["size"]
            if len(dim_ex[k]) < 4:
                dim_ex[k].append(r["name"][:70])
w(f"  {'维度':<18}{'文件数':>8}{'体积GB':>11}   库里对应标签")
for k, sz in dim_sz.most_common():
    st = ""
    for tn, tc in stash_tags.items():
        if tn in k or k.split("/")[0] in tn:
            st = f"{tn}({tc})"; break
    w(f"  {k:<18}{dim_n[k]:>8,}{sz/1024**3:>11.1f}   {st}")
w("")
w("  各维度样本：")
for k in dim_sz:
    w(f"    [{k}]")
    for e in dim_ex[k]:
        w(f"        {e}")

# ---------- 二、创作者 ----------
w("")
w("=" * 78)
w("二、创作者（第二层目录名，按体积）")
w("=" * 78)
lv2 = Counter(); lv2_n = Counter()
for r in vids:
    parts = [p for p in r["path"].split("\\") if p and not p.endswith(":")]
    if len(parts) >= 1:
        key = parts[0] if len(parts) == 1 else parts[1] if len(parts) >= 2 else parts[0]
        lv2[key] += r["size"]; lv2_n[key] += 1
w(f"  {'体积GB':>9}{'文件':>7}  {'在库':<6}目录名")
for k, sz in lv2.most_common(80):
    inlib = "✓" if any(s and s in k.lower() for s in stash_names if len(s) > 2) else ""
    w(f"  {sz/1024**3:>9.1f}{lv2_n[k]:>7}  {inlib:<6}{k[:60]}")

# ---------- 三、番号 ----------
w("")
w("=" * 78)
w("三、番号与作品号")
w("=" * 78)
jav = Counter(); fc2 = Counter(); rj = Counter()
for r in rows:
    n = r["name"]
    for m in FC2.finditer(n):
        fc2[f"FC2-{m.group(1)}"] += 1
    for m in RJ.finditer(n):
        rj[m.group(1).upper()] += 1
    base = re.sub(r"^(www\.)?[a-z0-9]+\.(la|com|net|org|me)@", "", os.path.splitext(n)[0], flags=re.I)
    m = JAVCODE.search(base.upper())
    if m and not re.match(r"^(MP|AV|HD|FHD|CD|PART|VOL|EP|SET|IMG|DSC|VID|GOPRO)$", m.group(1)):
        jav[f"{m.group(1)}-{m.group(2)}"] += 1
for label, c in (("JAV 番号", jav), ("FC2", fc2), ("DLsite RJ", rj)):
    w(f"\n  --- {label}：{len(c)} 个 ---")
    for k, v in c.most_common(60):
        w(f"      {v:>3}x  {k}")

# ---------- 四、与库存的差集 ----------
if stash_names:
    w("")
    w("=" * 78)
    w("四、网盘有、Stash 库里没有的创作者目录（按体积，前 60）")
    w("=" * 78)
    miss = [(k, sz) for k, sz in lv2.most_common()
            if not any(s and s in k.lower() for s in stash_names if len(s) > 2)]
    w(f"  共 {len(miss)} 个")
    for k, sz in miss[:60]:
        w(f"  {sz/1024**3:>9.1f} GB  {k[:70]}")

open(OUT, "w", encoding="utf-8").write("\n".join(R))
print(f"\n维度命中 {len(dim_sz)} 个 / 创作者目录 {len(lv2)} / JAV {len(jav)} / FC2 {len(fc2)} / RJ {len(rj)}")
print(f"→ {OUT}")
