#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 115 目录归类结果落地：
  A 已知创作者 → ledger.creator = 库里规范名
  B 疑似创作者 → ledger.creator = 目录名，并在 Stash 建 Performer 实体
  C 番号系列   → ledger.code = 番号，ledger.studio = 厂牌（前缀映射，零成本）
                 ⚠ 番号**是有女优的**，只是光凭目录名拿不到（实测 99% 的目录只有番号没人名）。
                    女优需要「番号联网反查」这一独立步骤，不在本脚本范围。
  D 需抽帧     → 不动，留给关键帧识别

⚠ 115 的文件不在 Stash 里（Stash 只索引本地 R:\Media），所以归属写进 **ledger**；
   Stash 那边只建 Performer 实体，供以后本地/网盘统一查询。

用法: python rm-115apply.py [--apply]
"""
import os, re, sys, csv, json, sqlite3, urllib.request, urllib.error
from collections import Counter

DB = r"R:\Resources\Intake\ledger.db"
CSVF = r"R:\Resources\Migration_Logs\115-目录归类.csv"
APPLY = "--apply" in sys.argv

# ── B 类里其实是「合集描述 / 站点标记 / 番号混合」的，降级为 D ──
NOT_CREATOR = re.compile(
    r"合集|全集|精选|整理|打包|收集|资源|天花板|新流|流出|"
    r"演艺圈|做种|桃花族|^kj$|^MIB$|^www\.|@|\.mp4$|\.mkv$|\.wmv$|\.avi$|"
    # 无码厂牌番号（格式与有码不同，前面的 CODE 正则抓不到）
    r"^1pon|^1pondo|^carib|^caribbean|^heyzo|^10mu|^10musume|^muramura|"
    r"^pacopacomama|^paco|^gachi|^tokyohot|^n\d{4}|"
    # 素人系番号
    r"\d{3}?LUXU|\d{3}?GANA|\d{3}?MIUM|\d{3}?SIRO|\d{3}?MAAN|\d{3}?NTK|"
    # 有码番号（补一道，防漏）
    r"^(FC2|MIDE|SSNI|SSIS|ABW|ABP|IPX|IPZ|STARS|FSDSS|ATID|SHKD|NHDTB|MIAA|"
    r"WAAA|DVDMS|MISM|PRED|JUL|JUQ|CAWD|MEYD|MVSD|MIDV|EBOD|HND|HMN|ADN|URE)[-_ ]?\d|"
    # 日期型目录：0208 (23) / 2021-5-1 (8) / 20240315
    r"^\d{4}\s*[\(（]|^\d{4}[-_.]\d{1,2}[-_.]\d{1,2}|^\d{6,8}$|^\d{3,4}\s|"
    # 数字占比过高（如「3」「2」「4」这种）
    r"^\d{1,3}$", re.I)
# 通用番号形态：字母后紧跟 3–5 位数字（不锚定位置，能抓 HD-abp-758 / Jav.li_MIAD573 / KBI044C / G3104）
# 这一条比逐个列厂牌可靠得多 —— 番号的本质就是「字母代号 + 序号」
CODE_SHAPE = re.compile(r"[A-Za-z]{1,8}[-_. ]?\d{3,6}(?![0-9])")
# 明确保留的（虽然可能命中上面但确实是人名）
KEEP = {"足交仙人", "按摩小子", "捅主任", "石川祐奈", "爱丝小仙女思研全集",
        "LegsJapan", "HIP-ANGEL", "BellaMurr", "DemiFairyTW", "91大黄鸭",
        "Fengyue_haitang", "SexySaffron", "gattouz0", "asce", "rina_vlog",
        "pandor_a", "sunwall", "ruth_lee", "loliburin", "oscarkim123"}

# 少数确实有人名、但被站点前缀或番号包裹的目录，手工指定
RENAME = {
    "[红馆97hg.me 51hg.in]上本莉央": "上本莉央",
    "FC2PPV-音梓-4K": "音梓",
    "MVP\\FC2PPV-音梓-4K": "音梓",
}

rows = list(csv.DictReader(open(CSVF, encoding="utf-8-sig")))
print(f"归类表 {len(rows)} 行")

# 重新判定 B
downgraded = []
for r in rows:
    if r["分类"] != "B-疑似创作者":
        continue
    nm = r["归属"].strip()
    if nm in KEEP:
        continue
    # 注意：试过用正则「把人名从站点前缀/番号里剥出来」，结果剥出一堆
    # '1 001' / '1 12 mp4' / '048【…】mp4' 的残渣，比不剥更糟。
    # 结论：宁可漏，不可脏 —— 少数能救的用下面 RENAME 手工列。
    if nm in RENAME:
        r["归属"] = RENAME[nm]; continue
    if NOT_CREATOR.search(nm) or CODE_SHAPE.search(nm) or len(nm) < 2:
        r["分类"] = "D-需抽帧"; downgraded.append((nm, float(r["体积GB"])))
downgraded.sort(key=lambda x: -x[1])
print(f"\nB 类降级为 D 的 {len(downgraded)} 个（合集描述/番号/站点标记，不是人名）：")
for nm, g in downgraded[:12]:
    print(f"    {g:>8.1f} GB  {nm[:60]}")

A = [r for r in rows if r["分类"] == "A-已知创作者"]
B = [r for r in rows if r["分类"] == "B-疑似创作者"]
C = [r for r in rows if r["分类"] == "C-番号系列"]
D = [r for r in rows if r["分类"] == "D-需抽帧"]
tot = lambda L: (sum(int(x["视频数"]) for x in L), sum(float(x["体积GB"]) for x in L))
for nm, L in (("A 已知", A), ("B 疑似", B), ("C 番号", C), ("D 抽帧", D)):
    n, g = tot(L)
    print(f"  {nm:<8}{len(L):>5} 目录{n:>7,} 视频{g/1024:>8.2f} TB")

# ── Stash：给 B 类建 Performer ──
def gq(q, v=None):
    b = {"query": q}
    if v: b["variables"] = v
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:9999/graphql", data=json.dumps(b).encode(),
            headers={"Content-Type": "application/json"}), timeout=90).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode("utf-8", "ignore")[:200])
    if "errors" in r: raise RuntimeError(r["errors"][0].get("message", "")[:200])
    return r["data"]

perfs = {p["name"].lower(): p["name"] for p in
         gq('{findPerformers(filter:{per_page:-1}){performers{name alias_list}}}')["findPerformers"]["performers"]}
newnames = sorted({r["归属"].strip() for r in B} - set())
tocreate = [n for n in newnames if n.lower() not in perfs]
print(f"\nB 类不同创作者 {len(newnames)} 个，其中 Stash 里没有的 {len(tocreate)} 个")
for n in tocreate[:15]:
    print(f"    {'[建]' if not APPLY else '✓'} {n}")
if len(tocreate) > 15:
    print(f"    …… 另外 {len(tocreate)-15} 个")

if APPLY:
    for n in tocreate:
        try:
            gq('mutation($n:String!){performerCreate(input:{name:$n}){id}}', {"n": n})
        except RuntimeError as e:
            print(f"    ⚠ 建 {n} 失败: {e}")

# ── ledger：写归属 ──
conn = sqlite3.connect(DB, timeout=120)
cur = conn.cursor()
cols = {r[1] for r in cur.execute("PRAGMA table_info(asset)")}
for col in ("series", "code", "studio"):
    if col not in cols:
        if APPLY:
            cur.execute(f"ALTER TABLE asset ADD COLUMN {col} TEXT"); conn.commit()
        print(f"(ledger 缺 {col} 列，已" + ("添加" if APPLY else "待添加") + ")")

# ── 日本 AV 厂牌前缀 → Studio。这是行业标准编号，稳定且零成本 ──
LABEL = {
    "ABW": "Prestige", "ABP": "Prestige", "PXH": "Prestige", "CHN": "Prestige",
    "MIDE": "Moodyz", "MIAA": "Moodyz", "MIDV": "Moodyz", "MIFD": "Moodyz",
    "SSNI": "S1 No.1 Style", "SSIS": "S1 No.1 Style", "SNIS": "S1 No.1 Style",
    "IPX": "Idea Pocket", "IPZ": "Idea Pocket", "IPZZ": "Idea Pocket",
    "STARS": "SOD Create", "STAR": "SOD Create", "SDDE": "SOD Create",
    "SDNM": "SOD Create", "SDAB": "SOD Create", "SDJS": "SOD Create",
    "FSDSS": "Faleno", "FLNS": "Faleno",
    "ATID": "Attackers", "SHKD": "Attackers", "RBD": "Attackers", "ADN": "Attackers",
    "NHDTB": "Natural High", "NHDTA": "Natural High",
    "PRED": "Premium", "PRTD": "Premium",
    "JUL": "Madonna", "JUQ": "Madonna", "JUY": "Madonna", "URE": "Madonna",
    "CAWD": "kawaii", "KAWD": "kawaii", "CAWD": "kawaii",
    "MEYD": "Tameike Goro", "MVSD": "M's Video Group",
    "DVDMS": "Deep's", "DVMM": "Deep's",
    "MISM": "Mister Sadistic", "WAAA": "Wanz Factory", "WANZ": "Wanz Factory",
    "DPMI": "Dogma", "DDT": "Dogma", "MIST": "Mist",
    "IDBD": "Ideapocket BEST", "HND": "Honnaka", "HMN": "Honnaka",
    "EBOD": "E-BODY", "EBWH": "E-BODY", "MIRD": "Moodyz Real",
    "OFJE": "S1 BEST", "TEK": "Tameike", "ROYD": "Royal",
    "FC2": "FC2-PPV", "FC": "FC2-PPV",
    "259LUXU": "Luxu TV", "LUXU": "Luxu TV", "200GANA": "Nampa TV",
    "300MIUM": "Nampa TV", "SIRO": "Shirouto TV",
}
CODE_RE = re.compile(r"(FC2[\-_ ]?(?:PPV[\-_ ]?)?\d{5,}|\d{3}[A-Z]{2,7}[-_]?\d{2,5}|"
                     r"[A-Z]{2,7}[-_]?\d{2,5}|RJ\d{6,})", re.I)

def upd(items, field, label):
    n = 0
    for r in items:
        d = r["目录"]
        who = r["归属"].strip()
        if not who:
            continue
        pat = "B:\\" + d + "\\%"
        pat2 = "B:\\" + d          # 目录本身就是文件的情况
        if APPLY:
            cur.execute(f"UPDATE asset SET {field}=? WHERE location='115' AND medium='video' "
                        f"AND (path LIKE ? OR path LIKE ?)", (who, pat, pat2 + "%"))
            n += cur.rowcount
        else:
            n += cur.execute("SELECT COUNT(*) FROM asset WHERE location='115' AND medium='video' "
                             "AND (path LIKE ? OR path LIKE ?)", (pat, pat2 + "%")).fetchone()[0]
    print(f"  {label}: {n:,} 个视频")
    return n

print("\n── 写入 ledger ──")
nA = upd(A, "creator", "A 已知创作者 → creator")
nB = upd(B, "creator", "B 疑似创作者 → creator")

# C 类：番号 + 厂牌
nC = nS = 0
labels = Counter()
for r in C:
    leaf = r["目录"].split("\\")[-1]
    m = CODE_RE.search(leaf)
    if not m:
        continue
    code = m.group(1).upper().replace("_", "-")
    pm = re.match(r"^(FC2|\d{3}[A-Z]{2,7}|[A-Z]{2,7})", code)
    label = LABEL.get(pm.group(1), "") if pm else ""
    if label:
        labels[label] += int(r["视频数"])
    pat = "B:\\" + r["目录"] + "%"
    if APPLY:
        cur.execute("UPDATE asset SET code=?, studio=? WHERE location='115' AND medium='video' "
                    "AND path LIKE ?", (code, label or None, pat))
        nC += cur.rowcount
        if label: nS += cur.rowcount
    else:
        k = cur.execute("SELECT COUNT(*) FROM asset WHERE location='115' AND medium='video' "
                        "AND path LIKE ?", (pat,)).fetchone()[0]
        nC += k
        if label: nS += k
print(f"  C 番号 → code: {nC:,} 个视频")
print(f"  C 厂牌 → studio: {nS:,} 个视频（{len(labels)} 个厂牌）")
for k, v in labels.most_common(12):
    print(f"      {v:>5}  {k}")

if APPLY:
    conn.commit()
    print(f"\n已提交。归属合计 {nA+nB:,} 个视频，系列 {nC:,} 个")
    got = cur.execute("SELECT COUNT(*) FROM asset WHERE location='115' AND creator IS NOT NULL AND creator!=''").fetchone()[0]
    print(f"115 现有创作者归属: {got:,} / 13,219")
else:
    print("\n== 预览模式，加 --apply 执行 ==")
conn.close()

