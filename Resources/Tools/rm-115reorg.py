#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
115 目录重组 —— 把无语义的上传批次顶层（云下载 / MVP / xxr / New / kkg / tzr / 123…）
换成按归属分的结构，与本地 R:\\Media 的约定一致（创作者只分一层，类型全走标签）。

目标结构:
  B:\\创作者\\{创作者}\\{原目录名}\\…      A/B 类
  B:\\番号\\{厂牌}\\{番号}\\…             C 类（无厂牌则放 B:\\番号\\_未知厂牌\\）
  B:\\西方\\{Studio}\\{原目录名}\\…       E 类
  其余原地不动 —— **留在旧顶层的，按定义就是待识别的那批**，不另造筐

原则:
  · 按**目录整体**搬，不挑文件 —— 115 上还有 1,019 个压缩包和 13,896 张图片，
    只搬视频会把目录拆散
  · 多个源目录归到同一人时，保留原目录名作为子层（tuki_1154-01/-02/… → 创作者\\tuki_1154\\tuki_1154-01\\）
  · 单文件（直接挂在顶层的）单独搬
  · 目标已存在 → 跳过，绝不覆盖
  · 路径超长（>250）→ 跳过并列出，不截断

⚠️ 移动后 ledger 里的路径全部失效，必须重扫。
⚠️ 已实测 115 的跨目录移动是服务端元数据操作（64 MB / 0.39 s），不搬数据。

用法:
  python rm-115reorg.py            出预览 CSV
  python rm-115reorg.py --apply    执行（读上一步的 CSV）
"""
import os, re, sys, csv, time, shutil, sqlite3
from collections import defaultdict, Counter

DB = r"R:\Resources\Intake\ledger.db"
_A = sys.argv[1:]
def _o(n, d): return _A[_A.index(n) + 1] if n in _A else d
TAG = _o("--tag", "115")
ROOT = _o("--drive", "B:\\")
RECLASS = _o("--reclass", rf"R:\Resources\Migration_Logs\{TAG}-D类回捞.csv")
FIRST = _o("--first", rf"R:\Resources\Migration_Logs\{TAG}-目录归类.csv")
JAV = r"R:\Resources\Migration_Logs\番号反查结果.csv"
CSVF = rf"R:\Resources\Migration_Logs\{TAG}-重组计划.csv"
LOG = rf"R:\Resources\Migration_Logs\{TAG}reorg-{time.strftime('%Y%m%d-%H%M%S')}.log"
APPLY = "--apply" in sys.argv
MAXPATH = 250

BADNAME = re.compile(
    r"(集全|做种|事件|合集|全集|精选|打包|下载|资源|整理|更新|系列|专辑|作品|影片|视频|"
    r"图片|写真|番号|门槛|福利|未分类|新建文件夹|未命名|持续|收集|典藏|珍藏|"
    r"selected|collection|compilation|homemade|videos|presents|pack|uncensored)", re.I)
INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

MEDIA_EXT = re.compile(r"\.(mp4|mkv|avi|wmv|mov|m4v|ts|flv|rmvb|jpg|png|zip|rar|7z)$", re.I)
# 剧情/描述性措辞 —— 这些不是创作者名，是内容描述
DESCRIPTIVE = re.compile(
    r"(车震|聋哑|前女友|未婚妻|新娘|管理员|妹子|女友|老婆|人妻|少妇|学生|护士|空姐|"
    r"被操|被肏|爆操|内射|中出|口交|足交|自慰|高潮|无套|露脸|反差|流出|泄密|偷拍|"
    r"缺钱|约炮|双飞|极品|嫩模|女神|母狗|骚|淫"
    r"|풋잡|맨발|스타킹|검스|페디|모음|사정)")   # 韩语：足交/裸足/丝袜/黑丝/脚趾甲/合集/射精

def okname(n):
    """物理移动用的严格闸门 —— 比 ledger 归属严得多。
    原则：ledger 归属可以宽松（软元数据、随时可改），物理移动必须严格（动了不好回）。"""
    n = (n or "").strip()
    if not n or len(n) > 24: return False
    if MEDIA_EXT.search(n): return False          # 'ic1(12).mp4' 是文件名不是人名
    if BADNAME.search(n): return False
    if DESCRIPTIVE.search(n): return False        # 剧情描述，留给关键帧识别
    if re.fullmatch(r"[\d\W_]+", n): return False
    return True

def safe(n):
    n = INVALID.sub("_", (n or "").strip()).rstrip(". ")
    return n[:60] or "_"

# 与 rm-cleanname.py 同一套净化规则 —— 用来把分类 CSV 里的旧文件名映射到净化后的名字
_PREFIX = [
    re.compile(r"^\s*(?:www\.)?[A-Za-z0-9\-]{2,20}\.(?:la|com|net|cc|me|in|tv|xyz|club|vip|top|li|cn|org)\s*[@\-_ ]\s*", re.I),
    re.compile(r"^\s*第一[會会]所[^@]*@\s*SIS\d+\s*@\s*", re.I),
    re.compile(r"^\s*\[JAV\]\s*", re.I),
    re.compile(r"^\s*[►◄◆◇■□●○★☆※]+\s*", re.I),
]
_DBL = re.compile(r"(\.(?:mp4|mkv|avi|wmv|mov|m4v|ts|flv|jpg|png|zip|rar))\1+$", re.I)
def cleaned(name):
    full = name
    m = _DBL.search(full)
    if m: full = full[:m.start()] + m.group(1)
    base, ext = os.path.splitext(full)
    prev = None
    while prev != base:
        prev = base
        for rx in _PREFIX: base = rx.sub("", base)
    base = re.sub(r"[\[\(【（]\s*[\]\)】）]", "", base).replace("　", " ")
    base = re.sub(r"\s{2,}", " ", base).strip(" .-_")
    return (base + ext.strip()) if base else name

# ── 番号 → 厂牌 ──
maker = {}
if os.path.exists(JAV):
    for r in csv.DictReader(open(JAV, encoding="utf-8-sig")):
        if r["厂牌"]:
            maker[r["番号"].upper()] = r["厂牌"]
            maker[r["查询式"].upper()] = r["厂牌"]

def mk_of(code):
    """番号 → 厂牌桶。FC2 / 无码厂标本身就是厂牌，不该扔进 _未知厂牌。"""
    c = (code or "").upper()
    m = maker.get(c)
    if m: return m
    if c.startswith("FC2"): return "FC2-PPV"
    if c.startswith("HEYZO"): return "HEYZO"
    if c.startswith(("CARIB", "1PON", "10MU", "MKBD", "TOKYOHOT", "TOKYO")): return "无码厂标"
    return "_未知厂牌"

# ── 归属：回捞结果优先，其次第一版分类 ──
plan = {}
for r in (csv.DictReader(open(RECLASS, encoding="utf-8-sig")) if os.path.exists(RECLASS) else []):
    k, who, d = r["新分类"], r["归属"], r["目录"]
    if k in ("A-已知创作者", "B-疑似创作者") and okname(who):
        plan[d] = ("创作者", safe(who), "")
    elif k == "C-番号系列" and who:
        plan[d] = ("番号", safe(mk_of(who)), safe(who))
    elif k == "E-西方发布" and who:
        st, _, pf = who.partition("|")
        if st.strip(): plan[d] = ("西方", safe(st), "")
for r in csv.DictReader(open(FIRST, encoding="utf-8-sig")):
    d = r["目录"]
    if d in plan: continue
    if r["分类"] == "C-番号系列" and r["归属"]:
        plan[d] = ("番号", safe(mk_of(r["归属"])), safe(r["归属"]))
    elif r["分类"] == "A-已知创作者" and okname(r["归属"]):
        plan[d] = ("创作者", safe(r["归属"]), "")
    # ⚠️ 第一版分类器的 B-疑似创作者**不参与物理移动**。
    # 它把 '前女友' / '五一车震06年聋哑人女孩' / '缺钱的妹子' 这类剧情描述判成了创作者。
    # 这批的归属已作为软元数据写进 ledger，物理位置等关键帧识别出结果再定。

print(f"有归属的二层目录 {len(plan):,} 个")

# ── 源在磁盘上是目录还是文件？──
rows = []
stat = Counter()
for d, (bucket, a, b) in sorted(plan.items()):
    src = os.path.join(ROOT, d)
    leaf = d.split("\\")[-1]
    if bucket == "番号":
        dst_dir = os.path.join(ROOT, "番号", a, b)
    elif bucket == "西方":
        dst_dir = os.path.join(ROOT, "西方", a)
    else:
        dst_dir = os.path.join(ROOT, "创作者", a)

    if not os.path.exists(src):
        # 净化改过文件名 → 分类 CSV 里的单文件路径失效，按同样规则算出净化后的名字再找一次
        alt = os.path.join(os.path.dirname(src), cleaned(os.path.basename(src)))
        if alt != src and os.path.exists(alt):
            src, leaf = alt, os.path.basename(alt)
            stat["路径已按净化后修正"] += 1
        else:
            stat["源不存在"] += 1; continue
    isdir = os.path.isdir(src)
    if isdir:
        # 同一归属下多个源目录 → 保留原目录名作子层；
        # 但目录名本身就等于归属名时，不再多套一层（创作者\前女友\前女友\ 是废的）
        sl = safe(leaf)
        dst = dst_dir if sl == os.path.basename(dst_dir) else os.path.join(dst_dir, sl)
    else:
        dst = os.path.join(dst_dir, os.path.basename(src))

    note = ""
    if len(dst) > MAXPATH:
        note = f"路径超长({len(dst)})-跳过"; stat["路径超长"] += 1
    elif os.path.exists(dst):
        note = "目标已存在-跳过"; stat["目标已存在"] += 1
    elif os.path.normcase(dst).startswith(os.path.normcase(src) + os.sep):
        note = "目标嵌套在源内-跳过"; stat["自嵌套"] += 1
    else:
        stat["可执行"] += 1
    rows.append({"类型": "目录" if isdir else "文件", "桶": bucket,
                 "源": src, "目标": dst, "备注": note})

print(f"\n计划 {len(rows):,} 条:")
for k, v in stat.most_common():
    print(f"  {k:<12} {v:,}")
bk = Counter(r["桶"] for r in rows if not r["备注"])
print("  分桶:", dict(bk))

if not APPLY:
    with open(CSVF, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["类型", "桶", "源", "目标", "备注"])
        w.writeheader(); w.writerows(rows)
    print(f"\n预览 → {CSVF}\n样例:")
    for r in [x for x in rows if not x["备注"]][:12]:
        print(f"  [{r['桶']}] {r['源'][:58]}\n      → {r['目标'][:70]}")
    if stat["路径超长"]:
        print("\n路径超长被跳过的（前 5）:")
        for r in [x for x in rows if "超长" in x["备注"]][:5]:
            print(f"  {r['目标'][:110]}…")
    print("\n核对无误后加 --apply 执行")
    sys.exit(0)

# ── 执行 ──
if not os.path.exists(CSVF):
    print("找不到预览 CSV，先不带 --apply 跑一次"); sys.exit(2)
todo = [r for r in csv.DictReader(open(CSVF, encoding="utf-8-sig")) if not r["备注"]]
logf = open(LOG, "w", encoding="utf-8", buffering=1)
ok = skip = err = 0
t0 = time.time()
for i, r in enumerate(todo, 1):
    src, dst = r["源"], r["目标"]
    if not os.path.exists(src):
        skip += 1; logf.write(f"SKIP\t源不存在\t{src}\n"); continue
    if os.path.exists(dst):
        skip += 1; logf.write(f"SKIP\t目标已存在\t{dst}\n"); continue
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(src, dst)
        ok += 1; logf.write(f"OK\t{src}\t→\t{dst}\n")
    except Exception as e:
        err += 1; logf.write(f"ERR\t{type(e).__name__}\t{src}\t→\t{dst}\t{e}\n")
    if i % 50 == 0:
        el = time.time() - t0
        print(f"  {i}/{len(todo)}  成功 {ok} 跳过 {skip} 失败 {err}  "
              f"剩余 {(len(todo)-i)*el/i/60:.0f} 分钟", flush=True)
print(f"\n完成：成功 {ok}，跳过 {skip}，失败 {err}")
print(f"日志 → {LOG}")
print("⚠️ 下一步必须重扫 ledger —— 路径已全部变更")
