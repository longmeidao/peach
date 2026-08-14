#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mac 侧 Zen + Safari 浏览历史 —— 用两层模型重跑。

严格遵循 R:\Resources\Sources\mac\README.md 的要求：
  1. 不把上一版的九个维度当输入（那是从 3D 媒介样本长出来的词汇）
  2. 两个浏览器时间窗口不同，绝对量不可直接比 —— 比较时截到共同区间
  3. 清洗：Zen 剔除 visit_type 4/5/6；Safari 剔除 redirect_*/synthesized=1
  4. 先从原始分布长出第一层（媒介/场景分层），再在层内谈偏好

用法: python mac-taste.py [--out 报告.txt]
"""
import os, re, sys, csv, datetime as dt
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs, unquote

D = r"R:\Resources\Sources\mac"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else \
      os.path.expandvars(r"%USERPROFILE%\Desktop\mac-口味分析.txt")
COMMON_LO, COMMON_HI = dt.date(2026, 2, 10), dt.date(2026, 8, 11)   # 共同区间

def rd(name):
    p = os.path.join(D, name)
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line.rstrip("\n").split("\t")

host = lambda u: (urlparse(u).hostname or "").lower().lstrip("www.")

# ---------- 读取 + 清洗 ----------
# Zen visits: visit_date, visit_type, url
zen_v, zen_typed = [], Counter()
DROP_ZEN = {"4", "5", "6"}          # embed / 永久重定向 / 临时重定向
for r in rd("zen-visits.tsv"):
    if len(r) < 3: continue
    d, t, u = r[0], r[1], r[2]
    if t in DROP_ZEN: continue
    try: day = dt.date.fromisoformat(d[:10])
    except ValueError: continue
    h = host(u)
    if not h: continue
    zen_v.append((day, h, u, t))
    if t in ("2", "3"):             # typed / bookmark = 主动意图
        zen_typed[h] += 1

# Safari visits: visit_time, kind, synthesized, load_successful, url
saf_v, saf_direct = [], Counter()
for r in rd("safari-visits.tsv"):
    if len(r) < 5: continue
    d, kind, syn, ok, u = r[0], r[1], r[2], r[3], r[4]
    if kind != "direct" or syn == "1": continue
    try: day = dt.date.fromisoformat(d[:10])
    except ValueError: continue
    h = host(u)
    if not h: continue
    saf_v.append((day, h, u, kind))
    saf_direct[h] += 1

# 标题（用于内容信号）
zen_title = {}
for r in rd("zen-history.tsv"):
    if len(r) >= 2 and r[0]: zen_title[r[0]] = r[1]
saf_title = {}
for r in rd("safari-history.tsv"):
    if len(r) >= 2 and r[0]: saf_title[r[0]] = r[1]

R, w = [], None
R = []; w = R.append
w("Mac 侧 Zen + Safari —— 两层模型重跑")
w(f"生成 {dt.datetime.now():%Y-%m-%d %H:%M}   全程本地，未外传")
w("")
w("清洗口径：Zen 剔除 visit_type 4(embed)/5/6(重定向)；Safari 只保留 kind=direct 且 synthesized=0")
w("")
w("=" * 78)
w("〇、规模与时间窗口")
w("=" * 78)
for nm, v in (("Zen", zen_v), ("Safari", saf_v)):
    days = [d for d, _, _, _ in v]
    w(f"  {nm:<8}清洗后 {len(v):>7,} 次访问   {min(days)} → {max(days)}")
zc = sum(1 for d, *_ in zen_v if COMMON_LO <= d <= COMMON_HI)
sc = sum(1 for d, *_ in saf_v if COMMON_LO <= d <= COMMON_HI)
w(f"\n  共同区间 {COMMON_LO} → {COMMON_HI}：Zen {zc:,} 次 / Safari {sc:,} 次"
  f"（比 {zc/max(sc,1):.1f} : 1）")

# ---------- 第一层：从原始分布长出场景分层 ----------
NOISE = re.compile(
    r"^(google|gstatic|googleapis|youtube|ytimg|doubleclick|mozilla|apple|icloud|"
    r"cloudflare|jsdelivr|unpkg|github|githubusercontent|stackoverflow|npmjs|"
    r"microsoft|live|bing|office|zhihu|csdn|juejin|taobao|jd|tmall|alipay|"
    r"feishu|larksuite|notion|slack|claude|anthropic|openai|doubao|gemini|"
    r"wikipedia|wikimedia|baike\.baidu|bilibili|hdslb|douyu|huya|nga\.178|bbs\.nga)", re.I)

def top_hosts(v, lo=None, hi=None, n=45):
    c = Counter()
    for d, h, u, t in v:
        if lo and not (lo <= d <= hi): continue
        if NOISE.match(h): continue
        c[h] += 1
    return c

w("")
w("=" * 78)
w("一、第一层 —— 两个浏览器各自的主干分布（共同区间内，已滤大厂/日常站）")
w("=" * 78)
zt = top_hosts(zen_v, COMMON_LO, COMMON_HI)
st = top_hosts(saf_v, COMMON_LO, COMMON_HI)
w(f"\n  --- Zen Top 45（共 {len(zt):,} 个域名）---")
for h, n in zt.most_common(45):
    w(f"    {n:>7,}  {h}")
w(f"\n  --- Safari Top 45（共 {len(st):,} 个域名）---")
for h, n in st.most_common(45):
    w(f"    {n:>7,}  {h}")

# 场景分工：同一域名在两边的占比差
w("")
w("=" * 78)
w("二、场景分工 —— 同一域名在两个浏览器里的相对偏好")
w("=" * 78)
w("  指标 = 该域名在本浏览器内的占比 ÷ 在另一浏览器内的占比。")
w("  >1 表示更常在这个浏览器上用。这一栏直接回答「两者是不是分工」。")
zsum, ssum = sum(zt.values()), sum(st.values())
both = [h for h in set(zt) | set(st) if zt.get(h, 0) + st.get(h, 0) >= 30]
rows = []
for h in both:
    pz = zt.get(h, 0) / zsum if zsum else 0
    ps = st.get(h, 0) / ssum if ssum else 0
    ratio = (pz + 1e-9) / (ps + 1e-9)
    rows.append((ratio, h, zt.get(h, 0), st.get(h, 0)))
rows.sort(reverse=True)
w(f"\n  --- 明显偏 Zen（桌面）---")
for ratio, h, z, s in rows[:25]:
    w(f"    {ratio:>8.1f}x   Zen {z:>6,} / Safari {s:>6,}   {h}")
w(f"\n  --- 明显偏 Safari（移动）---")
for ratio, h, z, s in rows[-25:][::-1]:
    w(f"    {1/ratio:>8.1f}x   Safari {s:>6,} / Zen {z:>6,}   {h}")

# ---------- 主动意图 ----------
w("")
w("=" * 78)
w("三、主动意图（Zen: typed/bookmark；Safari: direct）—— 比被动访问更接近真实偏好")
w("=" * 78)
w(f"\n  --- Zen 手输/书签 Top 40（共 {sum(zen_typed.values()):,} 次）---")
for h, n in zen_typed.most_common(60):
    if NOISE.match(h): continue
    w(f"    {n:>6,}  {h}")

# ---------- 第二层：层内的内容信号 ----------
w("")
w("=" * 78)
w("四、第二层 —— 层内内容信号（站内搜索词与标签，不套用预设维度）")
w("=" * 78)
KEYS = ("q", "query", "s", "search", "keyword", "kw", "wd", "word", "tags", "tag",
        "f_search", "srchtxt", "text", "searchword")
for nm, v, titles in (("Zen", zen_v, zen_title), ("Safari", saf_v, saf_title)):
    sq = defaultdict(Counter)
    for d, h, u, t in v:
        if NOISE.match(h): continue
        try: qs = parse_qs(urlparse(u).query)
        except Exception: continue
        for k in KEYS:
            for val in qs.get(k, []):
                val = unquote(val).strip()
                if 1 < len(val) < 60 and not val.isdigit():
                    sq[h][val] += 1
        for m in re.finditer(r"/(?:search|tag|tags|searchword)/([^/?#]{2,40})", u, re.I):
            val = unquote(m.group(1))
            if not val.lower().endswith((".js", ".css", ".png", ".jpg")):
                sq[h][val] += 1
    w(f"\n  ══════ {nm} ══════")
    for h in sorted(sq, key=lambda x: -sum(sq[x].values()))[:14]:
        tot = sum(sq[h].values())
        if tot < 3: continue
        w(f"\n    --- {h}  ({tot}) ---")
        for k, n in sq[h].most_common(35):
            w(f"        {n:>5}  {k}")

# ---------- 重点站点标题 ----------
w("")
w("=" * 78)
w("五、Top 站点的页面标题（内容信号最密集处）")
w("=" * 78)
for nm, v, titles in (("Zen", zen_v, zen_title), ("Safari", saf_v, saf_title)):
    byh = defaultdict(Counter)
    for d, h, u, t in v:
        ti = titles.get(u, "")
        if ti and not NOISE.match(h):
            byh[h][ti[:110]] += 1
    w(f"\n  ══════ {nm} ══════")
    tops = [h for h, _ in (zt if nm == "Zen" else st).most_common(12)]
    for h in tops:
        if h not in byh: continue
        w(f"\n    ─── {h} ───")
        for ti, n in byh[h].most_common(22):
            w(f"        {n:>4}  {ti}")

# ---------- 时段 ----------
w("")
w("=" * 78)
w("六、时段分布（会话场景的另一个信号）")
w("=" * 78)
for nm, fn, icol in (("Zen", "zen-visits.tsv", 0), ("Safari", "safari-visits.tsv", 0)):
    hr = Counter()
    for r in rd(fn):
        if len(r) <= icol: continue
        try: hr[int(r[icol][11:13])] += 1
        except (ValueError, IndexError): pass
    tot = sum(hr.values()) or 1
    w(f"\n  {nm}:")
    for h in range(24):
        n = hr.get(h, 0)
        w(f"    {h:02d}时  {n:>7,}  {'█' * int(n / tot * 300)}")

open(OUT, "w", encoding="utf-8").write("\n".join(R))
print("\n".join(R[:24]))
print(f"\n... 完整报告 → {OUT}")
