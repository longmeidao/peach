#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
115 目录归类（零成本，纯路径文本）—— 在花抽帧成本之前，先榨干免费信号。

把第二层目录分成四类：
  A 已知创作者   目录名命中库里已有的 Performer/别名 → 直接归属
  B 疑似创作者   像人名/账号（短、无番号特征、无合集措辞）→ 建 Performer 候选
  C 番号/系列    FC2PPV-xxx、MIDE-925、SSNI-392 这类 → 归「系列」，不建 Performer
  D 需要抽帧     auto_create@、日期串、纯数字、合集描述 → 只有这批需要关键帧识别

用法: python rm-115classify.py [--out 报告.csv]
"""
import os, re, sys, csv, json, sqlite3, urllib.request
from collections import Counter, defaultdict

DB = r"R:\Resources\Intake\ledger.db"
A = sys.argv[1:]
def _o(n, d): return A[A.index(n) + 1] if n in A else d
LOC = _o("--loc", "115")            # ledger 里的 location
DRIVE = _o("--drive", "B:\\")       # 挂载盘符
TAG = _o("--tag", LOC)              # 产物文件名前缀
OUT = _o("--out", rf"R:\Resources\Migration_Logs\{TAG}-目录归类.csv")

# ── 已知创作者（Stash）──
known = {}
try:
    r = urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:9999/graphql",
        data=json.dumps({"query": '{findPerformers(filter:{per_page:-1}){performers{name alias_list}}}'}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    for p in json.loads(r.read())["data"]["findPerformers"]["performers"]:
        known[p["name"].lower()] = p["name"]
        for a in (p.get("alias_list") or []):
            a = a.lower().lstrip("@").strip()
            if len(a) >= 3:
                known[a] = p["name"]
    print(f"Stash 已知创作者名/别名 {len(known)} 条")
except Exception as e:
    print("连不上 Stash:", e)

# ── 特征正则 ──
# ⚠️ 无分隔符的通用形必须限制字母段长度，否则创作者账号会被当成番号：
#    `[A-Z]{2,6}[-_]?\d{2,5}` 把 tuki_1154 和 Raikun325（myfans 创作者）都吃进来了。
#    真番号的字母段基本 ≤4（ABW123 / MIDE925）；RAIKUN 是 6 位，排除。
CODE = re.compile(r"^\s*(?:\[[^\]]*\]\s*)?"
                  r"(FC2[\-_. ]?(?:PPV[\-_. ]?)?\d{5,}|"
                  r"[A-Z]{2,6}-\d{2,5}|"          # 带连字符：ABW-123
                  r"[A-Z]{2,4}\d{3,5}|"           # 无分隔符但字母段 ≤4：ABW123
                  r"\d{3}[A-Z]{2,6}[-_]?\d{2,5}|RJ\d{6,}|n\d{4})\b", re.I)
AUTO = re.compile(r"auto_create@|^\d{4}[-_.]?\d{2}[-_.]?\d{2}|^\d{6,}$|^新建文件夹|^未命名", re.I)
COLLECTION = re.compile(r"合集|全集|大合集|精选|整理|打包|系列|收集|资源|\d+\s*[vVpP]\b|"
                        r"\[\d+[vVpP]|持续更新|最全|典藏|珍藏|福利", re.I)
NOISE_SITE = re.compile(r"^(www\.)?(98t|hhd800|hjd2048|bbs2048|22sht|fulibl|7sht|mtfdz|aaxv)", re.I)

def classify(name):
    n = name.strip()
    low = n.lower()
    # A 已知
    for k, v in known.items():
        if k in low:
            return "A-已知创作者", v
    # C 番号
    if CODE.match(n):
        return "C-番号系列", CODE.match(n).group(1).upper()
    # D 无意义
    if AUTO.search(n) or NOISE_SITE.match(n):
        return "D-需抽帧", ""
    # 合集描述：长且带合集措辞 → 需抽帧
    if COLLECTION.search(n) and len(n) > 14:
        return "D-需抽帧", ""
    # B 疑似创作者：短、无空格过多、不含大段描述
    if len(n) <= 24 and n.count(" ") <= 3:
        return "B-疑似创作者", n
    return "D-需抽帧", ""

c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = c.execute("SELECT path,name,size FROM asset WHERE location=? AND medium='video'",
                 (LOC,)).fetchall()
c.close()

# ── 自适应分层 ──
# 写死「取第二层」会出事：PikPak 的 `Pack From Shared\pen` 底下有 136 个子目录，
# 那一层才是创作者（secret_japan / retsu_dao / ukiru…），而 pen 只是个容器。
# 规则：某个二层目录的直接子目录数 ≥ CONTAINER，就认为它是容器，改用第三层。
CONTAINER = int(_o("--container", "10"))
parts = []
for p, nm, sz in rows:
    parts.append(([x for x in p.replace(DRIVE, "").split("\\") if x], sz))
children = defaultdict(set)
for ps, _ in parts:
    if len(ps) >= 3:
        children["\\".join(ps[:2])].add(ps[2])
# ⚠️ 光看「子目录多」会误伤：`123\www.98T.la@luckydog11` 有一堆分集目录，
#    但它本身就是创作者，下沉会把一个人拆成上百条。
#    也不能只在「本层认不出归属」时下沉 —— `pen` 只有三个字母，会被判成 B。
#    真正的判据是**子目录名的异质性**：
#      容器（pen）的孩子是 secret_japan / COSH こすっち / retsu_dao —— 各不相干的名字
#      创作者（luckydog11）的孩子是 19 / 25 / 2024-08 —— 纯数字或日期的分集
#    子目录数量也不行 —— 实测 SexySaffron（创作者）327 个子目录，pen（容器）只有 136 个。
#    子目录名的「异质性」也不行 —— 创作者的分集目录也是带标题的正常名字。
#
#    真正管用的是**每个子目录的平均体积**：
#      容器  pen              136 子目录 / 4,040 GB → 29.7 GB/个（孩子是一个个合集）
#      创作者 SexySaffron      327 子目录 /   191 GB →  0.6 GB/个（孩子是一集集片子）
#      创作者 轩轩合集          297 子目录 /    38 GB →  0.13 GB/个
#    再加一条独立判据：孩子大多是番号的也是容器（fc2 目录下全是 FC2-PPV-xxx）。
AVG_GB = float(_o("--container-avg-gb", "10"))
csize = defaultdict(int)
for ps, sz in parts:
    if len(ps) >= 3: csize["\\".join(ps[:2])] += sz or 0

containers, why = set(), {}
for k, v in children.items():
    if len(v) < CONTAINER: continue
    avg = csize[k] / len(v) / 1024**3
    code_ratio = sum(1 for x in v if classify(x)[0] == "C-番号系列") / len(v)
    if avg >= AVG_GB:
        containers.add(k); why[k] = f"{avg:.1f}GB/子目录"
    elif code_ratio >= 0.5:
        containers.add(k); why[k] = f"{code_ratio*100:.0f}% 子目录是番号"
if containers:
    print(f"判为容器目录（下沉一层）{len(containers)} 个:")
    for k in sorted(containers, key=lambda x: -csize[x])[:12]:
        print(f"  {csize[k]/1024**3:>8.1f}GB  {len(children[k]):>4} 子目录  {why[k]:<22} {k[:48]}")

dirs = defaultdict(lambda: {"n": 0, "sz": 0})
for ps, sz in parts:
    lvl = 3 if ("\\".join(ps[:2]) in containers and len(ps) >= 3) else 2
    key = "\\".join(ps[:lvl]) if len(ps) >= lvl else "\\".join(ps[:-1] or ps)
    d = dirs[key]; d["n"] += 1; d["sz"] += sz or 0

out = []
for key, v in dirs.items():
    leaf = key.split("\\")[-1]
    kind, who = classify(leaf)
    out.append({"分类": kind, "归属": who, "视频数": v["n"],
                "体积GB": round(v["sz"] / 1024**3, 2), "目录": key})
out.sort(key=lambda x: (x["分类"], -x["体积GB"]))

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["分类", "归属", "视频数", "体积GB", "目录"])
    w.writeheader(); w.writerows(out)

print(f"\n第二层目录 {len(out):,} 个 / 视频 {sum(o['视频数'] for o in out):,} 个\n")
agg = defaultdict(lambda: [0, 0, 0])
for o in out:
    a = agg[o["分类"]]; a[0] += 1; a[1] += o["视频数"]; a[2] += o["体积GB"]
for k in sorted(agg):
    d, n, g = agg[k]
    print(f"  {k:<14}{d:>5} 个目录{n:>7,} 个视频{g/1024:>8.2f} TB")

print("\n=== A 已知创作者（可直接归属）===")
for o in [x for x in out if x["分类"] == "A-已知创作者"][:20]:
    print(f"  {o['体积GB']:>8.1f} GB {o['视频数']:>5} 个  {o['归属']:<16} ← {o['目录'][:52]}")
print("\n=== B 疑似创作者（建 Performer 候选）Top 20 ===")
for o in [x for x in out if x["分类"] == "B-疑似创作者"][:20]:
    print(f"  {o['体积GB']:>8.1f} GB {o['视频数']:>5} 个  {o['归属'][:44]}")
print(f"\n→ {OUT}")
