#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「D 类回捞」+「番号反查」两批结果写进 ledger，并在 Stash 建对应 Performer/Studio。

输入:
  R:\Resources\Migration_Logs\115-D类回捞.csv      A/B/C/E 四类
  R:\Resources\Migration_Logs\番号反查结果.csv       番号 → 女优/厂牌/标签
  R:\Resources\Migration_Logs\115-目录归类.csv      第一轮的 C 类（番号）也要吃进来

写入:
  ledger.asset.creator / code / studio
  ledger.asset_tag      （r18 categories → 中文标签，source='r18'）
  Stash Performer / Studio（只建不删）

边界：不删任何东西；先 --dry 出统计，确认后再 --apply。
用法: python rm-115apply2.py [--dry|--apply]
"""
import os, re, sys, csv, json, sqlite3, urllib.request
from collections import Counter, defaultdict

DB = r"R:\Resources\Intake\ledger.db"
_A = sys.argv[1:]
def _o(n, d): return _A[_A.index(n) + 1] if n in _A else d
LOC = _o("--loc", "115")
DRIVE = _o("--drive", "B:\\")
TAG = _o("--tag", LOC)
RECLASS = _o("--reclass", rf"R:\Resources\Migration_Logs\{TAG}-D类回捞.csv")
FIRST = _o("--first", rf"R:\Resources\Migration_Logs\{TAG}-目录归类.csv")
JAV = r"R:\Resources\Migration_Logs\番号反查结果.csv"
APPLY = "--apply" in sys.argv

GQL = "http://127.0.0.1:9999/graphql"
def gql(q, v=None):
    r = urllib.request.urlopen(urllib.request.Request(
        GQL, data=json.dumps({"query": q, "variables": v or {}}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    return json.loads(r.read())

# ── r18 分类 → 本地标签词汇（只映射有意义的，其余丢弃）──
CAT = {
    "Foot Fetish": "足系", "Legs": "美腿", "Pantyhose": "丝袜", "Stockings": "丝袜",
    "Creampie": "中出内射", "Squirting": "潮吹", "Blowjob": "口交", "Deep Throat": "深喉",
    "Facial": "颜射", "Cum Swallowing": "吞精", "Handjob": "手交",
    "Big Tits": "巨乳", "Beautiful Tits": "美乳", "Small Tits": "贫乳", "Titty Fuck": "乳交",
    "Slender": "苗条", "Chubby": "丰满", "Beautiful Girl": "高颜值",
    "Office Lady": "OL制服", "School Girls": "学生制服", "Nurse": "护士",
    "Uniform": "制服", "Cosplay": "角色扮演", "Maid": "女仆", "Swimsuit": "泳装",
    "Married Woman": "人妻", "Mature Woman": "熟女", "Big Tits Lover": "巨乳",
    "Threesome / Foursome": "多人", "Orgy": "多人", "Lesbian": "百合",
    "Anal": "肛交", "Bondage": "捆绑", "Torture": "调教", "Training": "调教",
    "Slut": "痴女", "Nymphomaniac": "痴女", "Cuckold": "绿帽", "Voyeur": "偷窥",
    "Hidden Camera": "偷拍", "Amateur": "素人", "Debut Production": "出道作",
    "Massage": "按摩", "Bath": "浴室", "Outdoor": "户外", "Car Sex": "车震",
    "Ass Lover": "美臀", "Butt": "美臀", "Kimono": "和服", "Glasses": "眼镜",
    "Virtual Reality": "VR", "POV": "主观视角", "Solowork": "单体作品",
    "Restraint": "束缚", "Drama": "剧情", "Incest": "近亲", "Cheating Wife": "出轨",
}
DROP = {"Featured Actress", "Hi-Def", "Exclusive Distribution", "Sample Video",
        "Digital Mosaic", "Female Porn Star", "Over 4 Hours", "Best Compilation",
        "Non-nude Erotica", "Older Sister", "Younger Sister", "Hi-Def "}

# ── 读入 ──
reclass = list(csv.DictReader(open(RECLASS, encoding="utf-8-sig"))) if os.path.exists(RECLASS) else []
first = list(csv.DictReader(open(FIRST, encoding="utf-8-sig")))
jav = {r["番号"].upper(): r for r in csv.DictReader(open(JAV, encoding="utf-8-sig"))}
# 查询式也做一份索引（番号被规范化过）
javq = {r["查询式"].upper(): r for r in jav.values()}

def look(code):
    c = (code or "").upper()
    return jav.get(c) or javq.get(c) or javq.get(re.sub(r"[\s_.]+", "-", c))

# 创作者名合法性闸门 —— 第一版分类器的 B 类混进了论坛帖名
# （'桃花族重新高速做种演艺圈事件39集全' 这种，490 个资产全被判给它）
BADNAME = re.compile(
    r"(集全|做种|事件|合集|全集|精选|打包|下载|资源|整理|更新|系列|专辑|作品|影片|视频|"
    r"图片|写真|番号|门槛|福利|未分类|新建文件夹|未命名|持续|收集|典藏|珍藏|"
    r"selected|collection|compilation|homemade|videos|presents|pack|uncensored)", re.I)
MEDIA_EXT = re.compile(r"\.(mp4|mkv|avi|wmv|mov|m4v|ts|flv|rmvb|jpg|png|zip|rar|7z)$", re.I)
def okname(n):
    """⚠️ 第一版只挡了「合集措辞」，没挡「文件名」——
    结果 1(12).mp4 / [emailprotected](3).mp4 / 3.mp4 全被建成了 Performer（111 个），
    再被下一轮分类器当成「已知创作者」，污染了 PikPak 的分类。见 rm-cleanjunk.py。"""
    n = (n or "").strip()
    if not n or len(n) > 24: return False
    if MEDIA_EXT.search(n): return False
    if n.startswith("[emailprotected]"): return False
    if BADNAME.search(n): return False
    if not n.startswith("@") and re.fullmatch(r"[\d\W_]+", n): return False
    return True

# 目录 → (creator, code, studio)
plan = {}
for r in reclass:
    k, who, d = r["新分类"], r["归属"], r["目录"]
    if k in ("A-已知创作者", "B-疑似创作者"):
        if not okname(who): continue
        plan[d] = {"creator": who, "code": "", "studio": ""}
    elif k == "C-番号系列":
        plan[d] = {"creator": "", "code": who, "studio": ""}
    elif k == "E-西方发布":
        st, _, pf = who.partition("|")
        plan[d] = {"creator": pf.strip(), "code": "", "studio": st.strip()}
# 第一轮的 A/C 也吃进来（番号那批要补女优）
for r in first:
    d = r["目录"]
    if d in plan: continue
    if r["分类"] == "C-番号系列" and r["归属"]:
        plan[d] = {"creator": "", "code": r["归属"], "studio": ""}
    elif r["分类"] in ("A-已知创作者", "B-疑似创作者") and okname(r["归属"]):
        plan[d] = {"creator": r["归属"], "code": "", "studio": ""}

# 番号 → 补女优/厂牌/标签
for d, p in plan.items():
    if not p["code"]: continue
    j = look(p["code"])
    if not j: continue
    if j["女优"] and not p["creator"]:
        p["creator"] = j["女优"].split("|")[0]      # 主演取第一个
        p["extra"] = j["女优"].split("|")[1:]
    if j["厂牌"]:
        p["studio"] = j["厂牌"]
    p["tags"] = [CAT[t] for t in (j["标签"] or "").split("|")
                 if t and t not in DROP and t in CAT]

con = sqlite3.connect(DB)
cur = con.cursor()
stat = Counter()
touch_assets = 0
creators = Counter(); studios = Counter(); tagc = Counter()
updates = []
for d, p in plan.items():
    rows = cur.execute("SELECT id FROM asset WHERE location=? AND path LIKE ?",
                       (LOC, DRIVE + d + "\\%")).fetchall()
    rows += cur.execute("SELECT id FROM asset WHERE location=? AND path = ?",
                        (LOC, DRIVE + d)).fetchall()
    if not rows:
        stat["目录无资产"] += 1; continue
    ids = [r[0] for r in rows]
    touch_assets += len(ids)
    if p["creator"]: creators[p["creator"]] += len(ids)
    if p["studio"]: studios[p["studio"]] += len(ids)
    for t in p.get("tags", []): tagc[t] += len(ids)
    updates.append((ids, p))
    stat["计划更新目录"] += 1

print(f"计划：{stat['计划更新目录']} 个目录 / {touch_assets:,} 个资产")
print(f"  跳过（目录在 ledger 里没有资产）{stat['目录无资产']}")
print(f"  涉及创作者/女优 {len(creators)} 位，厂牌 {len(studios)} 家，标签 {len(tagc)} 种")
print("\n创作者 Top 12:")
for k, v in creators.most_common(12): print(f"   {v:>5} 个资产  {k}")
print("\n厂牌 Top 12:")
for k, v in studios.most_common(12): print(f"   {v:>5} 个资产  {k}")
print("\n标签 Top 15:")
for k, v in tagc.most_common(15): print(f"   {v:>5} 个资产  {k}")

if not APPLY:
    print("\n以上为预演。确认后加 --apply 执行。")
    con.close(); sys.exit(0)

# ── 写 ledger ──
n_up = n_tag = 0
CHUNK = 500          # SQLite 默认变量上限 999，森萝财团那个目录一次有 33,882 个 id
for ids, p in updates:
    for i in range(0, len(ids), CHUNK):
        part = ids[i:i + CHUNK]
        qm = ",".join("?" * len(part))
        if p["creator"]:
            cur.execute(f"UPDATE asset SET creator=? WHERE id IN ({qm}) "
                        f"AND (creator IS NULL OR creator='')", [p["creator"]] + part)
        if p["code"]:
            cur.execute(f"UPDATE asset SET code=? WHERE id IN ({qm})", [p["code"]] + part)
        if p["studio"]:
            cur.execute(f"UPDATE asset SET studio=? WHERE id IN ({qm})", [p["studio"]] + part)
    n_up += len(ids)
    for t in p.get("tags", []):
        cur.executemany("INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)",
                        [(i, t, 0.9, "r18") for i in ids])
        n_tag += len(ids)
con.commit()
print(f"\nledger：更新 {n_up:,} 个资产，写入标签 {n_tag:,} 条")

# ── Stash 建 Performer / Studio（只建不删）──
have_p = {p["name"].lower() for p in
          gql('{findPerformers(filter:{per_page:-1}){performers{name}}}')["data"]["findPerformers"]["performers"]}
have_s = {s["name"].lower() for s in
          gql('{findStudios(filter:{per_page:-1}){studios{name}}}')["data"]["findStudios"]["studios"]}
new_p = new_s = 0
for name in creators:
    if not name or name.lower() in have_p: continue
    try:
        gql('mutation($n:String!){performerCreate(input:{name:$n}){id}}', {"n": name})
        have_p.add(name.lower()); new_p += 1
    except Exception as e:
        print("  建 Performer 失败:", name, e)
for name in studios:
    if not name or name.lower() in have_s: continue
    try:
        gql('mutation($n:String!){studioCreate(input:{name:$n}){id}}', {"n": name})
        have_s.add(name.lower()); new_s += 1
    except Exception as e:
        print("  建 Studio 失败:", name, e)
print(f"Stash：新建 Performer {new_p}，Studio {new_s}")

tot = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video' "
                  "AND creator IS NOT NULL AND creator<>''", (LOC,)).fetchone()[0]
allv = cur.execute("SELECT count(*) FROM asset WHERE location=? AND medium='video'",
                   (LOC,)).fetchone()[0]
print(f"\n{LOC} 视频有创作者归属：{tot:,} / {allv:,}")
con.close()
