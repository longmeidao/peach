#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D 类回捞（零成本）—— 在读 700 张识别页之前，先把「名字里其实有归属、只是被前缀挡住」的捞出来。

第一版分类器把带 www.98T.la@ / 合集措辞的一律打成 D，但实际上：
  www.98T.la@luckydog22          → 创作者 luckydog22
  www.98T.la@FC2-PPV-3060929     → 番号
  铃木美咲 (Misaki Suzuki) [38 Sets] → 女优 + 合集措辞
  Onlyfans_chocoletmilkk-FHD     → 创作者 chocoletmilkk

做法：剥掉渠道噪声 → 重新判 A/B/C → 仍判不出的才留 D。

⚠️ 沿用既定教训：宁可漏，不可脏。
   试过用正则「把人名从番号/前缀里剥出来」，结果剥出一堆 '1 001' / '048【…】mp4' 的残渣。
   所以这里只做**剥噪声 + 重判**，不做「拼凑人名」。

用法: python rm-115reclass.py [--out 回捞.csv]
"""
import os, re, sys, csv, json, urllib.request
from collections import defaultdict

SRC = r"R:\Resources\Migration_Logs\115-目录归类.csv"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else \
      r"R:\Resources\Migration_Logs\115-D类回捞.csv"

# ── 已知创作者（Stash）──
known = {}
try:
    r = urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:9999/graphql",
        data=json.dumps({"query": '{findPerformers(filter:{per_page:-1}){performers{name alias_list}}}'}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    # 通用词 Performer 是上一轮 apply 造出来的垃圾，必须排除，否则「…最全视频」会被判给「视频」
    JUNKP = re.compile(r"^(视频|门槛|合集|全集|精选|资源|下载|作品|影片|写真|图片|系列|未分类|"
                       r"uncensored|jav|selected|collection|pack|funky|videos|homemade)$", re.I)
    junk = []
    for p in json.loads(r.read())["data"]["findPerformers"]["performers"]:
        if JUNKP.match(p["name"]):
            junk.append(p["name"]); continue
        known[p["name"].lower()] = p["name"]
        for al in (p.get("alias_list") or []):
            al = al.lower().lstrip("@").strip()
            if len(al) >= 4:            # ≥4 才收，3 字母别名太容易误命中
                known[al] = p["name"]
    if junk: print("已排除通用词垃圾 Performer:", "、".join(junk))
except Exception as e:
    print("连不上 Stash:", e)
print(f"已知创作者名/别名 {len(known)} 条")

# ── 渠道噪声：只剥前缀/包装，不动主体 ──
CHANNEL = [
    re.compile(r"^\s*(?:www\.)?[A-Za-z0-9\-]{2,20}\.(?:la|com|net|cc|me|in|tv|xyz|club|vip|top|li)\s*[@\-_]\s*", re.I),
    re.compile(r"^\s*\[(?:美颜版|无水印|高清修复|重制|HEVC[^\]]*|4K|1080P|中文字幕)\]\s*", re.I),
    re.compile(r"^\s*(?:hhd800\.com@|hjd2048\.com@|jav\.li_|HD-)", re.I),
    # 论坛转载头：第一會所新片@SIS001@URVRSP-457 —— SIS001 是论坛不是番号
    re.compile(r"^\s*第一[會会]所[^@]*@\s*SIS\d+\s*@\s*", re.I),
    re.compile(r"^\s*\[JAV\]\s*(?:\[Uncensored\]\s*)?", re.I),
    re.compile(r"^\s*[►◄★☆■□●○\-–—]+\s*", re.I),
]
# 合集/规格措辞：出现在名字里但不是主体，判 B 前先摘掉
DECOR = re.compile(
    r"(\[[^\]]{0,40}(?:\d+\s*(?:sets?|[vVpP])|G[Bb]?)\s*[^\]]{0,20}\]|"
    r"[\(（][^)）]{0,30}(?:合集|全集|精选|打包|持续更新|截止|重制)[^)）]{0,30}[\)）]|"
    r"[-_ ]?(?:FHD|UHD|4K|1080P|720P|HEVC|X265|H265|PACK|Collection|Selected)\b|"
    r"持续收集中|大合集|超大合集|合集下载|合集|全集|精选|打包|典藏|珍藏|"
    r"\[\d+\s*[vVpP][^\]]*\]|\d+\s*[vVpP]\+[\d.]+G)", re.I)
# 平台/渠道词：不是人名，摘掉但记下来
PLATFORM = re.compile(r"(?i)(?:^|[\s_\-])(onlyfans?|fansly|patreon|fanbox|pixiv|twitter|推特|微博|抖音|快手)[_\-： :]+")

# 番号：⚠️ 下划线只允许出现在 FC2 里。
# 通用形 `[A-Z]{2,7}[-_]?\d{2,5}` 会把创作者账号 tuki_1154 当成番号 —— 踩过。
CODE = re.compile(r"(?:^|[^A-Za-z0-9])("
                  r"FC2[\-_. ]?(?:PPV[\-_. ]?)?\d{5,}|"     # FC2 PPV 1713543 / FC2-PPV-… / FC2-429568
                  r"[A-Z]{2,7}-\d{2,5}|"                    # 必须带连字符：ABP-484
                  r"\d{3}[A-Z]{2,6}-?\d{2,5}|"              # 200GANA-1995
                  r"[A-Z]{2,6}-S\d{2,4}|"                   # 无码厂标：MKBD-S89
                  r"Tokyo[ _-]?Hot[ _-]?n?\d{3,4}|"         # Tokyo Hot n0780
                  r"RJ\d{6,})(?![0-9])", re.I)
# 西方发布名：Studio.YY.MM.DD.Performer.Name  /  Studio - Title - Performer
WEST_DOT = re.compile(r"^([A-Za-z][A-Za-z0-9]{2,20})\.(\d{2}\.\d{2}\.\d{2})\.(.+)$")
WEST_DASH = re.compile(r"^([A-Za-z][A-Za-z0-9]{2,20})\s+-\s+.+\s+-\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})")
# 拉丁账号/人名：字母开头，可含数字下划线，长度 4–28
HANDLE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-.]{3,27}$")
# 中日文人名候选：2–8 字，不含明显描述词
CJK_NAME = re.compile(r"^[\u4e00-\u9fff\u3040-\u30ff][\u4e00-\u9fff\u3040-\u30ffA-Za-z0-9_]{1,11}$")
# 明显不是人名的描述词
NOT_NAME = re.compile(
    r"(视角|内射|中出|口交|足交|自慰|高潮|无套|外流|流出|泄密|探花|偷拍|下载|资源|整理|"
    r"更新|系列|专辑|作品|影片|视频|图片|写真|番号|门槛|福利|未分类|新建文件夹|未命名|"
    r"selected|collection|compilation|homemade|videos|presents|pack|uncensored|"
    r"^jav$|^funky|^town|cam ?\d|^\d)", re.I)
# 西方厂牌：命中就归 Studio，不能当 Performer
WEST_STUDIO = re.compile(
    r"^(vixen|blacked|tushy|deeper|slayed|wankzvr|virtualtaboo|badoinkvr|naughtyamerica|"
    r"brazzers|realitykings|mofos|digitalplayground|evilangel|julesjordan|"
    r"czechav|legalporno|analvids|dorcel|private|sexart|nubilefilms|passionhd|"
    r"tiny4k|povd|holed|hardx|darkx|elegantangel|newsensations)$", re.I)

def clean(name):
    n = name.strip()
    for _ in range(3):
        for rx in CHANNEL:
            n2 = rx.sub("", n)
            if n2 != n: n = n2.strip()
    return n

def core(name):
    """摘掉合集措辞和平台词，留主体"""
    n = DECOR.sub(" ", name)
    n = PLATFORM.sub(" ", n)
    n = re.sub(r"[\[\]（）()【】《》「」]+", " ", n)
    n = re.sub(r"[-_.]{2,}", " ", n)
    return re.sub(r"\s{2,}", " ", n).strip(" -_.")

def reclass(leaf):
    n = clean(leaf)
    low = n.lower()
    # A 已知创作者（在剥完前缀的名字里找）
    for k, v in known.items():
        if k in low:
            return "A-已知创作者", v, "剥前缀后命中已知"
    # C 番号（前缀剥掉后才露出来的）—— 不再要求剩余部分短，番号本身就够定位
    m = CODE.search(n)
    if m:
        code = re.sub(r"[\s_.]+", "-", m.group(1).upper())
        code = re.sub(r"^FC2-?(?:PPV-?)?", "FC2-PPV-", code) if code.startswith("FC2") else code
        return "C-番号系列", code, "剥前缀后露出番号"
    # E 西方发布名：Studio.YY.MM.DD.Performer / Studio - Title - Performer
    m = WEST_DOT.match(n)
    if m:
        who = m.group(3).replace(".", " ").strip()
        who = re.sub(r"\s+(XXX|1080p|2160p|720p|MP4|SD)\b.*$", "", who, flags=re.I).strip()
        return "E-西方发布", f"{m.group(1)}|{who[:40]}", "Studio.日期.演员 格式"
    m = WEST_DASH.match(n)
    if m:
        return "E-西方发布", f"{m.group(1)}|{m.group(2)}", "Studio - 标题 - 演员 格式"
    # B 疑似创作者：摘掉合集措辞后剩下一个像名字的短串
    c = core(n)
    if WEST_STUDIO.match(c):
        return "E-西方发布", c + "|", "整串是西方厂牌名"
    if c and not NOT_NAME.search(c):
        # 整串就是一个账号/人名
        if HANDLE.match(c) or CJK_NAME.match(c):
            # 账号后面挂的分卷号要去掉：tuki_1154-02 / tuki_1154-05 是同一个人
            c = re.sub(r"(?<=\d)-\d{1,2}$", "", c)
            return "B-疑似创作者", c, "摘措辞后是单一名字"
        # 「中文名 (Latin Name)」这种双写
        mm = re.match(r"^([\u4e00-\u9fff\u3040-\u30ff]{2,8})\s+([A-Za-z][A-Za-z .]{2,24})$", c)
        if mm:
            return "B-疑似创作者", mm.group(1), "中英双写"
        # 「Latin_handle 中文描述」→ 取拉丁段
        mm = re.match(r"^([A-Za-z][A-Za-z0-9_\-.]{3,24})\s+\S", c)
        if mm and not NOT_NAME.search(mm.group(1)):
            return "B-疑似创作者", mm.group(1), "拉丁账号在首"
        # 「中文名 Latin_handle …」→ 取拉丁段（如「烈 Retsu_dao 持续收集中」）
        mm = re.search(r"\b([A-Za-z][A-Za-z0-9_\-.]{4,24})\b", c)
        if mm and len(c) <= 32 and not NOT_NAME.search(mm.group(1)):
            return "B-疑似创作者", mm.group(1), "串内拉丁账号"
    return "D-需抽帧", "", ""

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
d_rows = [r for r in rows if r["分类"] == "D-需抽帧"]
print(f"D 类 {len(d_rows)} 个目录 / {sum(int(r['视频数']) for r in d_rows):,} 视频 / "
      f"{sum(float(r['体积GB']) for r in d_rows)/1024:.2f} TB\n")

out, agg = [], defaultdict(lambda: [0, 0, 0.0])
for r in d_rows:
    leaf = r["目录"].split("\\")[-1]
    kind, who, why = reclass(leaf)
    out.append({"新分类": kind, "归属": who, "依据": why, "视频数": r["视频数"],
                "体积GB": r["体积GB"], "目录": r["目录"]})
    a = agg[kind]; a[0] += 1; a[1] += int(r["视频数"]); a[2] += float(r["体积GB"])

out.sort(key=lambda x: (x["新分类"], -float(x["体积GB"])))
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["新分类", "归属", "依据", "视频数", "体积GB", "目录"])
    w.writeheader(); w.writerows(out)

for k in sorted(agg):
    d, n, g = agg[k]
    print(f"  {k:<14}{d:>5} 个目录{n:>7,} 个视频{g/1024:>8.2f} TB")

for kind, title in (("A-已知创作者", "A 回捞（剥前缀后命中已知创作者）"),
                    ("C-番号系列", "C 回捞（剥前缀后露出番号）"),
                    ("E-西方发布", "E 回捞（西方厂牌发布名 → Studio|Performer）"),
                    ("B-疑似创作者", "B 回捞（新建 Performer 候选）")):
    sel = [x for x in out if x["新分类"] == kind]
    if not sel: continue
    print(f"\n=== {title}  {len(sel)} 个 ===")
    for x in sel[:16]:
        print(f"  {float(x['体积GB']):>7.1f}GB {int(x['视频数']):>4}个  {x['归属'][:26]:<28} "
              f"← {x['目录'].split(chr(92))[-1][:50]}")
print(f"\n→ {OUT}")
