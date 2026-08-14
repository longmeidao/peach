#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
厂牌 logo 抓取 —— 正规厂牌用官网图标，素人/个人创作者退回预览图裁切。

边界：
  · 只对**公开站点的图标 URL** 发 GET，不带任何本地信息（没有 referer、没有查询参数）
  · 抓一次就缓存到 R:\\Resources\\Intake\\logos\\，之后永不出网
  · 域名表是人工维护的；抓不到就留空，前端自动退回接触印相裁切 —— 不需要全猜对

用法:
  python rm-logos.py            抓所有还没有的
  python rm-logos.py --force    重抓
  python rm-logos.py --list     只列出待抓的厂牌
"""
import os, re, sys, time, json, sqlite3, urllib.request, urllib.parse

OUT = r"R:\Resources\Intake\logos"
DB = r"R:\Resources\Intake\ledger.db"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 人工维护：厂牌 → 官网域名。不确定的宁可不写，让它退回预览图。
DOMAINS = {
    # 日本片商
    "MOODYZ": "moodyz.com", "Prestige": "prestige-av.com", "S1 NO.1 STYLE": "s1s1s1.com",
    "Idea Pocket": "ideapocket.com", "SOD Create": "sod.co.jp", "Faleno": "faleno.jp",
    "Attackers": "attackers.net", "kawaii": "kawaii-av.com", "MADONNA": "madonna-av.com",
    "Natural High": "naturalhigh.co.jp", "Wanz Factory": "wanz-factory.com",
    "Tameike Goro": "tameikegoro.jp", "Das!": "das-av.com", "Das": "das-av.com",
    "BAZOOKA": "bazooka-av.com", "HEYZO": "heyzo.com", "FC2-PPV": "fc2.com",
    "Fitch": "fitch-av.com", "E-BODY": "ebody.jp", "Premium": "premium-beauty.com",
    "PREMIUM": "premium-beauty.com", "Alice Japan": "alicejapan.co.jp",
    "Honnaka": "honnaka.jp", "Oppai": "oppai-av.com", "Venus": "venus-av.com",
    "Dogma": "dogma-av.com", "Maxing": "maxing.jp", "Waap Entertainment": "waap.co.jp",
    "Muku": "muku-av.com", "Kira Kira": "kirakira-av.com", "Rocket": "rocket-av.jp",
    "Katsu-do": "katsu-do.jp", "Kanbi": "kanbi-av.com",
    # 欧美
    "Vixen": "vixen.com", "Blacked": "blacked.com", "Tushy": "tushy.com",
    "Deeper": "deeper.com", "Slayed": "slayed.com", "Brazzers": "brazzers.com",
    "BangBros": "bangbros.com", "BangBus": "bangbros.com", "BangBros18": "bangbros.com",
    "MonstersOfCock": "bangbros.com", "TeamSkeet": "teamskeet.com",
    "TeamSkeetXReislin": "teamskeet.com", "TeenFidelity": "teenfidelity.com",
    "RealityKings": "realitykings.com", "EvilAngel": "evilangel.com",
    "JulesJordan": "julesjordan.com", "DorcelClub": "dorcelclub.com",
    "Dorcel": "dorcelclub.com", "Private": "private.com", "NaughtyAmerica": "naughtyamerica.com",
    "Nubiles": "nubiles.net", "NubileFilms": "nubilefilms.com", "AdultTime": "adulttime.com",
    "WowGirls": "wowgirls.com", "UltraFilms": "ultrafilms.com",
    # VR
    "WankzVR": "wankzvr.com", "VirtualTaboo": "virtualtaboo.com",
    "DarkRoomVR": "darkroomvr.com", "BadoinkVR": "badoinkvr.com",
    # 平台
    "OnlyFans": "onlyfans.com", "Myfans": "myfans.jp", "Fantia": "fantia.jp",
    "Patreon": "patreon.com", "Pixiv": "pixiv.net", "DLsite": "dlsite.com",
}

A = sys.argv[1:]
FORCE = "--force" in A
LIST_ONLY = "--list" in A
os.makedirs(OUT, exist_ok=True)
safe = lambda s: re.sub(r"[^A-Za-z0-9_-]", "_", s)[:60]

def get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")

def fetch_icon(domain):
    """优先拿**站点真正的 logo**，不是 16px 的 favicon。

    上一版只取 favicon.ico，32px 显示就糊。按优先级找：
      内联 <svg> logo > <img> 带 logo 特征 > apple-touch-icon(180px)
      > og:image > 带 sizes 的大 icon > 常见 logo 路径 > favicon.ico
    """
    LOGOISH = re.compile(r"(logo|brand|site[-_]?title)", re.I)
    cands = []                       # (优先级, url 或 data:svg,)
    for base in (f"https://{domain}/", f"https://www.{domain}/"):
        try:
            html = get(base, 14)[0].decode("utf-8", "ignore")
        except Exception:
            continue
        for m2 in re.finditer(
                r"<(?:a|div|span|h1)[^>]*(?:class|id)=[\"'][^\"']*logo[^\"']*[\"'][^>]*>\s*"
                r"(<svg[\s\S]{60,8000}?</svg>)", html, re.I):
            cands.append((22, "data:svg," + m2.group(1)))
        for m2 in re.finditer(r"<img[^>]+>", html, re.I):
            tag = m2.group(0)
            src = re.search(r"src=[\"']([^\"']+)", tag, re.I)
            if src and LOGOISH.search(tag) and not src.group(1).lower().endswith(".gif"):
                cands.append((20, urllib.parse.urljoin(base, src.group(1))))
        for m2 in re.finditer(
                r"<link[^>]+rel=[\"'][^\"']*apple-touch-icon[^\"']*[\"'][^>]*href=[\"']([^\"']+)",
                html, re.I):
            cands.append((12, urllib.parse.urljoin(base, m2.group(1))))
        for m2 in re.finditer(
                r"<meta[^>]+property=[\"']og:image[\"'][^>]*content=[\"']([^\"']+)", html, re.I):
            cands.append((10, urllib.parse.urljoin(base, m2.group(1))))
        for m2 in re.finditer(r"<link[^>]+rel=[\"'][^\"']*icon[^\"']*[\"'][^>]*>", html, re.I):
            tag = m2.group(0)
            href = re.search(r"href=[\"']([^\"']+)", tag, re.I)
            if not href:
                continue
            sz = re.search(r"sizes=[\"'](\d+)", tag, re.I)
            n = int(sz.group(1)) if sz else 16
            cands.append((min(9, n // 32 + 1), urllib.parse.urljoin(base, href.group(1))))
        if cands:
            break
    root = f"https://{domain}/"
    for pth in ("images/logo.png", "img/logo.png", "assets/logo.png", "images/logo.svg",
                "img/logo.svg", "static/logo.png", "logo.png", "logo.svg"):
        cands.append((6, urllib.parse.urljoin(root, pth)))
    cands.append((1, urllib.parse.urljoin(root, "favicon.ico")))

    cands.sort(key=lambda x: -x[0])
    seen = set()
    for _, u in cands:
        if u in seen:
            continue
        seen.add(u)
        if u.startswith("data:svg,"):
            return u[9:].encode("utf-8"), "image/svg+xml"
        try:
            b, ct = get(u)
        except Exception:
            continue
        if b and len(b) > 400 and b[:4] != b"<!DO" and b"<html" not in b[:200].lower():
            return b, ct
    return None, None
# 库里实际有哪些厂牌
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
studios = [r[0] for r in c.execute(
    "SELECT studio FROM asset WHERE medium='video' AND studio IS NOT NULL AND studio<>'' "
    "GROUP BY studio ORDER BY count(*) DESC")]
c.close()

todo = []
for s in studios:
    dom = DOMAINS.get(s) or DOMAINS.get(s.replace("!", "")) or DOMAINS.get(s.title())
    if not dom:
        continue
    dst = os.path.join(OUT, safe(s) + ".img")
    if os.path.exists(dst) and not FORCE:
        continue
    todo.append((s, dom, dst))

print(f"库里厂牌 {len(studios)} 个，域名表覆盖 {sum(1 for s in studios if DOMAINS.get(s))} 个，"
      f"待抓 {len(todo)} 个")
if LIST_ONLY:
    for s, d, _ in todo: print(f"  {s:<24} {d}")
    print("\n没有域名的（将退回预览图裁切）:")
    for s in studios[:40]:
        if not DOMAINS.get(s): print(f"  {s}")
    sys.exit(0)

ok = fail = 0
for i, (s, dom, dst) in enumerate(todo, 1):
    b, ct = fetch_icon(dom)
    if b:
        with open(dst, "wb") as f: f.write(b)
        with open(dst + ".ct", "w", encoding="utf-8") as f: f.write(ct or "image/x-icon")
        ok += 1; print(f"  [{i}/{len(todo)}] ✅ {s:<22} {dom}  {len(b)/1024:.1f} KB")
    else:
        fail += 1; print(f"  [{i}/{len(todo)}] ✗  {s:<22} {dom}  → 退回预览图")
    time.sleep(0.8)          # 控频，别把人家站点打疼
print(f"\n完成：拿到 {ok} 个，失败 {fail} 个（失败的前端会自动用接触印相裁切）")
print(f"→ {OUT}")
