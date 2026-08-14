#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firefox / Zen（places.sqlite）浏览历史 → 口味分析。

只读打开（mode=ro&nolock=1），浏览器开着也能读，不干扰它。
沿用与 Takeout 分析同一套维度词典，保证结果可比。

用法: python firefox-taste.py [--out 报告.txt]
"""
import os, re, sys, json, sqlite3, glob, datetime as dt
from collections import Counter, defaultdict
from urllib.parse import urlparse, parse_qs, unquote

OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else \
      os.path.expandvars(r"%USERPROFILE%\Desktop\firefox-口味分析.txt")

ROOTS = [os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles"),
         os.path.expandvars(r"%APPDATA%\zen\Profiles"),
         os.path.expandvars(r"%APPDATA%\LibreWolf\Profiles"),
         os.path.expandvars(r"%APPDATA%\Waterfox\Profiles"),
         os.path.expandvars(r"%APPDATA%\Floorp\Profiles")]

profiles = []
for r in ROOTS:
    for p in glob.glob(os.path.join(r, "*", "places.sqlite")):
        brand = "Zen" if "\\zen\\" in p.lower() else \
                "LibreWolf" if "librewolf" in p.lower() else \
                "Waterfox" if "waterfox" in p.lower() else \
                "Floorp" if "floorp" in p.lower() else "Firefox"
        profiles.append((brand, os.path.basename(os.path.dirname(p)), p))

rows = []
meta = []
for brand, name, path in profiles:
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro&nolock=1&immutable=1", uri=True)
        got = c.execute("""SELECT url, COALESCE(title,''), COALESCE(visit_count,0),
                                  last_visit_date
                           FROM moz_places WHERE url LIKE 'http%'""").fetchall()
        c.close()
    except Exception as e:
        meta.append((brand, name, -1, "", "", str(e)[:60])); continue
    days = [dt.datetime.fromtimestamp(t / 1e6).date() for _, _, _, t in got if t]
    meta.append((brand, name, len(got), str(min(days)) if days else "-",
                 str(max(days)) if days else "-", ""))
    for u, t, vc, ts in got:
        rows.append((brand, u, t, vc or 0,
                     dt.datetime.fromtimestamp(ts / 1e6).date() if ts else None))

R, w = [], None
R = []; w = R.append
w("Firefox / Zen 浏览历史 —— 口味分析")
w(f"生成 {dt.datetime.now():%Y-%m-%d %H:%M}   只读打开，全程本地，未外传")
w("")
w("=" * 78)
w("〇、各 profile")
w("=" * 78)
w(f"  {'浏览器':<10}{'profile':<34}{'URL数':>9}  时间跨度")
for brand, name, n, lo, hi, err in meta:
    if n < 0:
        w(f"  {brand:<10}{name[:32]:<34}{'读取失败':>9}  {err}")
    else:
        w(f"  {brand:<10}{name[:32]:<34}{n:>9,}  {lo} → {hi}")
w(f"\n  合计 {len(rows):,} 条 URL 记录")

bym = Counter(f"{d:%Y-%m}" for _, _, _, _, d in rows if d)
w("\n  按月分布（全部 profile 合并）：")
for k in sorted(bym):
    w(f"    {k}  {bym[k]:>7,}  {'█' * min(58, bym[k] // 400)}")

host = lambda u: (urlparse(u).hostname or "").lower()
NOISE = re.compile(
    r"^(www\.)?(google|gstatic|googleapis|youtube|ytimg|doubleclick|mozilla|firefox|"
    r"microsoft|live|bing|office|apple|icloud|cloudflare|jsdelivr|unpkg|github|"
    r"stackoverflow|npmjs|python|docker|zhihu|csdn|juejin|"
    r"taobao|jd|tmall|alipay|cmbchina|feishu|larksuite|notion|slack|claude|anthropic|"
    r"openai|doubao|gemini|wikipedia|wikimedia|baike\.baidu)\.", re.I)

hosts = Counter(); hosts_w = Counter()
titles_by_host = defaultdict(Counter)
for brand, u, t, vc, d in rows:
    h = host(u)
    if not h: continue
    hosts[h] += 1
    hosts_w[h] += max(vc, 1)
    if t: titles_by_host[h][t[:120]] += max(vc, 1)
inter = Counter({h: n for h, n in hosts_w.items() if not NOISE.match(h)})
w("")
w("=" * 78)
w(f"一、域名 Top 150（按访问次数加权；共 {len(inter):,} 个）")
w("=" * 78)
for h, n in inter.most_common(150):
    w(f"  {n:>7,}  {h}   ({hosts[h]:,} 个不同 URL)")

# ---- 维度（与 cloud-taste.py 同一套，保证可比）----
DIM = {
    "足系": r"足交|足控|恋足|戀足|丝足|絲足|footjob|foot\s?fetish|美足|裸足|足裏|足指|"
           r"丝袜|絲襪|黑丝|黑絲|白丝|白絲|肉丝|连裤袜|pantyhose|stocking|高跟|heel|五指袜|踩踏",
    "马眼尿道": r"马眼|馬眼|尿道|龟头|龜頭|鈴口|铃口|urethra|glans|虾线|蝦線|系带|繫帶|glansjob",
    "口交深喉": r"口交|口爆|吞精|深喉|颜射|顏射|blowjob|deepthroat|奶交|\b69\b",
    "毒龙肛": r"毒龙|毒龍|舔肛|rimjob|analingus|肛交|后庭|anal|爆菊",
    "反差泄密": r"反差|泄密|洩密|流出|不雅|网爆|網爆|门事件|清纯|清純",
    "扶她": r"扶她|扶他|futanari|ふたなり",
    "ASMR音声": r"asmr|音声|音聲|耳舐|同人音声|\bRJ\d{6,}",
    "NTR": r"ntr|netorare|绿帽|綠帽|cuckold|寝取|淫妻|换妻",
    "调教束缚": r"调教|調教|束缚|捆绑|bdsm|femdom|女王|奴|羞辱|露出",
    "制服cos": r"cosplay|コスプレ|制服|jk|水手服|女仆|女僕|maid|护士|護士|空姐|洛丽塔|lolita",
    "萝莉": r"萝莉|蘿莉|\bloli\b|ロリ|白虎|贫乳|貧乳|嫩",
    "熟女人妻": r"人妻|熟女|少妇|少婦|milf|継母|継母|御姐",
    "3D动画": r"\b3d\b|sfm|blender|koikatsu|mmd|hentai|里番|同人|doujin",
    "探花约炮": r"探花|约炮|約炮|外围|外圍|楼凤|樓鳳|会所|按摩|技师",
    "内射": r"内射|內射|中出|creampie|无套|無套",
    "多人": r"双飞|雙飛|群交|轮流|輪流|乱交|3P视频|多女",
    "游戏同人": r"原神|星铁|崩坏|崩壊|绝区零|碧蓝|明日方舟|鸣潮|nikke|ブルアカ|blue\s?archive|"
              r"overwatch|守望|dva|d\.va|tracer|2b|yorha|nier|tifa|marie\s?rose|doa",
    "VTuber": r"vtuber|virtual\s?youtuber|ホロライブ|hololive|にじさんじ|虚拟主播",
}
DIMR = {k: re.compile(v, re.I) for k, v in DIM.items()}
dim_n = Counter(); dim_ex = defaultdict(list)
for brand, u, t, vc, d in rows:
    h = host(u)
    if NOISE.match(h): continue
    hay = f"{u} {t}"
    for k, rx in DIMR.items():
        if rx.search(hay):
            dim_n[k] += max(vc, 1)
            if len(dim_ex[k]) < 3 and t:
                dim_ex[k].append(f"{h} | {t[:70]}")
w("")
w("=" * 78)
w("二、口味维度命中（按访问次数加权）")
w("=" * 78)
for k, n in dim_n.most_common():
    w(f"  {n:>7,}  {k}")
w("\n  样本：")
for k, _ in dim_n.most_common():
    w(f"    [{k}]")
    for e in dim_ex[k]:
        w(f"        {e}")

# ---- 站内搜索词 ----
site_q = defaultdict(Counter)
for brand, u, t, vc, d in rows:
    h = host(u)
    if NOISE.match(h) or not h: continue
    try: qs = parse_qs(urlparse(u).query)
    except Exception: continue
    for key in ("q", "query", "s", "search", "keyword", "kw", "wd", "word", "f_search",
                "srchtxt", "tags", "tag", "searchword", "text"):
        for v in qs.get(key, []):
            v = unquote(v).strip()
            if 1 < len(v) < 60 and not v.isdigit():
                site_q[h][v] += max(vc, 1)
    for m in re.finditer(r"/(?:search|tag|tags|searchword)/([^/?#]{2,40})", u, re.I):
        v = unquote(m.group(1))
        if not v.lower().endswith((".js", ".css", ".png", ".jpg")):
            site_q[h][v] += max(vc, 1)
w("")
w("=" * 78)
w("三、站内搜索词（成人/媒体站）")
w("=" * 78)
for h in sorted(site_q, key=lambda x: -sum(site_q[x].values())):
    tot = sum(site_q[h].values())
    if tot < 3: continue
    w(f"\n  --- {h}  ({tot}) ---")
    for k, v in site_q[h].most_common(40):
        w(f"      {v:>5}  {k}")

# ---- 重点站点标题 ----
FOCUS = [h for h, _ in inter.most_common(40)]
w("")
w("=" * 78)
w("四、Top 站点的页面标题（内容信号最密集处）")
w("=" * 78)
for h in FOCUS[:22]:
    if h not in titles_by_host: continue
    w(f"\n  ─── {h} ───")
    for t, n in titles_by_host[h].most_common(25):
        w(f"      {n:>5}  {t[:96]}")

open(OUT, "w", encoding="utf-8").write("\n".join(R))
print("\n".join(R[:26]))
print(f"\n... 完整报告 → {OUT}")
print(f"域名 {len(inter):,} / 维度 {len(dim_n)} / 有搜索词的站 {len(site_q)}")
