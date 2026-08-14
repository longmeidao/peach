#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番号反查 —— 把 C 类目录的番号换成女优名 + 厂牌 + 内容标签。

多源级联（借鉴 JavSP 的做法，单源必被限流）：
  1. r18.dev      JSON API，无 Cloudflare，有码片主力，附带 categories 可直接做 Tag
  2. avsox        无码 / FC2 主力
  3. javbus       兜底（易 403，放最后并带退避）

边界（必须守住）：
  · 出网的只有番号本身（如 "ABW-123"），不带任何本地路径、文件名、目录结构
  · 单线程 + 固定间隔，不并发不加速；连续限流即退避，再连续即停
  · 结果只落 CSV，不自动写 Stash —— 由 rm-assign.py 二次确认后再入库
  · 断点续跑：CSV 里已有的番号直接跳过

用法: python rm-javlookup.py [--limit N] [--delay 1.2]
"""
import os, re, sys, csv, time, json, random, urllib.parse, urllib.request, urllib.error

SRC = r"R:\Resources\Migration_Logs\115-目录归类.csv"
OUT = r"R:\Resources\Migration_Logs\番号反查结果.csv"
LOG = r"R:\Resources\Migration_Logs\javlookup-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))

a = sys.argv[1:]
def opt(n, d, cast=str): return cast(a[a.index(n) + 1]) if n in a else d
LIMIT = opt("--limit", 0, int)
DELAY = opt("--delay", 1.2, float)

logf = open(LOG, "w", encoding="utf-8", buffering=1)
def log(s):
    line = f"[{time.strftime('%H:%M:%S')}] {s}"
    print(line, flush=True); logf.write(line + "\n")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

def get(url, headers=None, timeout=20):
    h = {"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

TAG = re.compile(r"<[^>]+>")
def txt(h): return re.sub(r"\s+", " ", TAG.sub("", h)).strip()
def nm(v): return (v or {}).get("name", "") if isinstance(v, dict) else (v or "")

BLANK = {"女优": "", "厂牌": "", "发行": "", "系列": "", "标题": "", "标签": "", "来源": ""}

# ── 源 1: r18.dev（有码主力，JSON）──
def src_r18(code):
    d = json.loads(get(f"https://r18.dev/videos/vod/movies/detail/-/dvd_id="
                       f"{urllib.parse.quote(code)}/json"))
    acts = [a.get("name", "").strip() for a in (d.get("actresses") or []) if a.get("name")]
    if not acts and not d.get("maker"):
        return None
    return {"女优": "|".join(acts), "厂牌": nm(d.get("maker")), "发行": nm(d.get("label")),
            "系列": nm(d.get("series")), "标题": (d.get("title") or "")[:200],
            "标签": "|".join(c.get("name", "") for c in (d.get("categories") or []))[:300],
            "来源": "r18"}

# ── 源 2: avsox（无码 / FC2 主力，HTML）──
def src_avsox(code):
    h = get("https://avsox.click/cn/search/" + urllib.parse.quote(code))
    m = re.search(r'href="(https?://[^"]*/cn/movie/[^"]+)"', h)
    if not m:
        return None
    p = get(m.group(1))
    acts = [txt(x) for x in re.findall(r'/cn/star/[^"]*"[^>]*>\s*<[^>]*>\s*<[^>]*>\s*'
                                       r'<span>([^<]{1,30})</span>', p)]
    if not acts:
        acts = [txt(x) for x in re.findall(r'class="avatar-box"[^>]*>.{0,400}?<span>([^<]{1,30})</span>',
                                           p, re.S)]
    mk = re.search(r'制作商.{0,300}?<a[^>]*>([^<]{1,60})</a>', p, re.S)
    ti = re.search(r"<h3>(.*?)</h3>", p, re.S)
    if not (acts or mk):
        return None
    return {"女优": "|".join(dict.fromkeys(a for a in acts if a)), "厂牌": mk.group(1).strip() if mk else "",
            "发行": "", "系列": "", "标题": txt(ti.group(1))[:200] if ti else "",
            "标签": "", "来源": "avsox"}

# ── 源 3: javbus（兜底，易 403）──
def src_javbus(code):
    h = get("https://www.javbus.com/" + urllib.parse.quote(code),
            headers={"Cookie": "existmag=all"})
    acts = [txt(b) for b in re.findall(r'class="star-name"[^>]*>(.*?)</span>', h, re.S)]
    if not acts:
        acts = [x.strip() for x in re.findall(r'href="[^"]*/star/[^"]*"[^>]*>([^<]{1,30})</a>', h)]
    out = dict(BLANK)
    out["女优"] = "|".join(dict.fromkeys(a for a in acts if a))
    for key, f in (("製作商", "厂牌"), ("發行商", "发行"), ("系列", "系列")):
        m = re.search(key + r'.{0,200}?href="[^"]*"[^>]*>([^<]{1,60})</a>', h, re.S)
        if m: out[f] = m.group(1).strip()
    t = re.search(r"<h3>(.*?)</h3>", h, re.S)
    if t: out["标题"] = txt(t.group(1))[:200]
    out["来源"] = "javbus"
    return out if (out["女优"] or out["厂牌"]) else None

def norm(code):
    """FC2PPV-1234567 → FC2-PPV-1234567 ; ABW123 → ABW-123 ; IPVR00296 → IPVR-296"""
    c = code.upper().replace("_", "-").replace(" ", "-")
    if c.startswith("FC2"):
        n = re.search(r"(\d{5,})", c)
        return f"FC2-PPV-{n.group(1)}" if n else c
    m = re.match(r"^([A-Z]+)-?(\d+)$", c)
    if not m: return c
    d = m.group(2)
    if len(d) > 3 and d.startswith("0"): d = d.lstrip("0").zfill(3)
    return f"{m.group(1)}-{d}"

# ── 待查番号（按体积降序，先啃大的）──
rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8-sig"))
        if r["分类"] == "C-番号系列" and r["归属"]]
codes, seen = [], set()
for r in rows:
    c = r["归属"].upper().strip()
    if c not in seen:
        seen.add(c); codes.append((c, float(r["体积GB"]), int(r["视频数"])))
codes.sort(key=lambda x: -x[1])

done = set()
if os.path.exists(OUT):
    done = {r["番号"] for r in csv.DictReader(open(OUT, encoding="utf-8-sig"))}
    log(f"已有结果 {len(done)} 条，跳过")

todo = [c for c in codes if c[0] not in done]
if LIMIT: todo = todo[:LIMIT]
log(f"待查 {len(todo)} 个番号（去重后共 {len(codes)}），间隔 {DELAY}s，"
    f"预计 {len(todo)*DELAY*1.4/60:.0f} 分钟")

fields = ["番号", "查询式", "女优", "厂牌", "发行", "系列", "标题", "标签", "来源", "状态", "体积GB", "视频数"]
fh = open(OUT, "a", newline="", encoding="utf-8-sig")
w = csv.DictWriter(fh, fieldnames=fields)
if not done: w.writeheader()

# FC2/无码走 avsox 优先，其余走 r18 优先
def chain(code):
    if code.startswith("FC2") or re.match(r"^\d{6}[-_]\d{3}$", code):
        return [("avsox", src_avsox), ("javbus", src_javbus), ("r18", src_r18)]
    return [("r18", src_r18), ("avsox", src_avsox), ("javbus", src_javbus)]

cool = {}          # 源 → 冷却截止时间戳
hit = miss = 0
srcstat = {}
t0 = time.time()
for i, (code, gb, nv) in enumerate(todo, 1):
    q = norm(code)
    rec = dict(BLANK); rec.update({"番号": code, "查询式": q, "状态": "",
                                   "体积GB": gb, "视频数": nv})
    for sname, fn in chain(q):
        if time.time() < cool.get(sname, 0):
            continue
        try:
            r = fn(q)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                cool[sname] = time.time() + 300
                log(f"  {sname} 限流 {e.code}，冷却 5 分钟")
            continue
        except Exception:
            continue
        if r:
            rec.update(r); rec["状态"] = "ok" if r["女优"] else "no_actress"
            srcstat[sname] = srcstat.get(sname, 0) + 1
            break
        time.sleep(0.4)
    if rec["女优"]: hit += 1
    else:
        miss += 1
        if not rec["状态"]: rec["状态"] = "not_found"
    w.writerow(rec); fh.flush()
    if i % 25 == 0:
        el = time.time() - t0
        log(f"{i}/{len(todo)}  命中 {hit}  未果 {miss}  "
            f"剩余 {(len(todo)-i)*el/i/60:.0f} 分钟  源:{srcstat}")
    time.sleep(DELAY + random.uniform(0, 0.5))

fh.close()
log(f"完成：查 {hit+miss} 个，拿到女优 {hit} 个（{hit/max(hit+miss,1)*100:.0f}%）  源分布:{srcstat}")
log(f"→ {OUT}")
