"""目录型来源的社媒采集：整站翻一遍，按名字对回账本，X 账号再验一次活。

minnano-av 采集器是「拿名字去搜」。laoshi.ink（686 位）和事务所官网 bstar-pro（22 位）
反过来：页面数有限，一次全部抓下来缓存在本地，再拿每页的名字去账本里找人。比对不花
网络，同一批页面能反复对比；「同名多人」「同平台另有账号」都能在离线阶段判出来，
不会静默装错人。

来源本身可能是旧数据（用户 2026-09-02 指出：抄来的 X / Instagram 账号点进去已经封停，
本人一般早换了新号）。所以采到的 X 账号逐个取登出页验活：有 og:title 且 og:image 指向
profile_images 才算活。Instagram / TikTok / YouTube 登出页给不出可靠信号，标「未验」。
只有「活」和「未验」的进安装队列；「疑似失效」只进复核表。冲突行两边都验，证据里写明
账本旧号是死是活——旧号死、新号活，就是用户说的「一般都会有新的」。

判定（verdict）：
    ok            账本唯一命中，该平台该账号账本还没有
    已有          同账号已在账本（twitter.com/x.com 视为同一主机，handle 不分大小写）
    conflict      同平台账本另有账号——用户要的「交叉对比」，只报不装
    需人工消歧    页面名字对上不止一位 performer
    未取得        页面抓不到，或命中的人页面上没有社交链接

输出两份 CSV：`<output>` 只含可装的 ok 行，直接喂 install_entity_links.py；
`<stem>-review.csv` 含全部判定，是复核产物。

jae.tokyo 是第三个这样的来源：Japan Adult Expo 的参展女优名录，2014／2015／2017 三届
各一套厂商自己交的资料，页面上写明本人的博客与官网（`公式ブログ`／`ツイッター`）。
名录同时带一张人像，所以这个来源多产一份 `<stem>-portraits.csv`，由
harvest_social_avatars.py 的 jae 路线接着走——头像与链接出自同一批页面、同一次名字判定。

laoshi.ink 与 bstar-pro.com 直连（经代理握手失败，站点本身可达）；x.com 与 jae.tokyo 走代理。
bstar-pro 的 models.html 有年龄门：同一会话先 `POST age_check=yes`，之后的 GET 才给列表。
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.config import STATE_DIR   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.page_cache import HttpStatusError, Site, USER_AGENT   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.social_links import (   # noqa: E402
    canonical_url, classify, handle, load_performers, name_key, platform, under,
    x_profile_state,
)

HREF = re.compile(r'href=["\']([^"\']+)["\']')
TAG = re.compile(r"<[^>]+>")
COMMENT = re.compile(r"<!--.*?-->", re.S)
FIELDS = ("entity_id", "kind", "name", "link_kind", "label", "url", "evidence",
          "source", "page", "matched_name", "verdict", "alive")
#: 人像候选表：喂 harvest_social_avatars.py 的 jae 路线，不直接落盘头像。
PORTRAIT_FIELDS = ("entity_id", "kind", "name", "matched_name", "portrait_url",
                   "source", "page", "verdict")
SOURCES = ("laoshi", "bstar", "jae")
#: 直连被对端重置（`WinError 10054`），这个来源走代理。
PROXY_SOURCES = ("jae",)
ALIVE, GONE, UNVERIFIED, UNKNOWN = "活", "疑似失效", "未验", "未取得"

LAOSHI = "https://laoshi.ink/"
LAOSHI_OWN = ("laoshi.ink",)
LAOSHI_ACTOR = re.compile(r"https://laoshi\.ink/actresses/actor-\d+\.html")
LAOSHI_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
LAOSHI_FACT = re.compile(r"<span>([^<]+)</span>\s*<strong>(.*?)</strong>", re.S)
LAOSHI_NAME_FIELDS = ("中文名", "日文名", "别名")
LAOSHI_BLANK = {"", "待补充", "暂无", "-", "—", "无"}
LD_JSON = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

BSTAR = "https://bstar-pro.com/"
BSTAR_OWN = ("bstar-pro.com",)
BSTAR_MODELS = BSTAR + "models.html"
BSTAR_LABEL = "Bstar"
BSTAR_ENTRY = re.compile(r'<a href="(model\.html\?mid=\d+)"[^>]*>(.*?)</a>', re.S)
BSTAR_ALT = re.compile(r'alt="([^"]*)"')
BSTAR_SPAN = re.compile(r"<span[^>]*>(.*?)</span>", re.S)
BSTAR_GATE = re.compile(r'name=["\']age_check["\']')

JAE = "http://www.jae.tokyo/"
JAE_OWN = ("jae.tokyo",)
#: 三届的女优名录，每届结构都不一样。2016 那届 `actress.html` 只剩导航，页面上没有人。
JAE_2014_LISTS = ("jae2014/performer/",) + tuple(
    f"jae2014/performer/index_{row}.html"
    for row in ("k", "s", "t", "n", "h", "m", "y", "r"))
JAE_2015_LIST = "jae2015/actress.html"
JAE_2017_LIST = "jae2017/actress.html"
JAE_2017_DETAIL = re.compile(r'href="(actress/[\w-]+\.html)"')
JAE_2014_ENTRY = re.compile(r'<li id="([^"]+)">(.*?)</li>', re.S)
JAE_2014_ROMAJI = re.compile(r'<p class="alignright">(.*?)</p>', re.S)
JAE_2014_IMG = re.compile(r'<img src="(images/[^"]+)"')
#: 每个女优是一个 `class="off"` 的隐藏层，下一个同类 div 或文末就是它的边界。
JAE_2015_ENTRY = re.compile(
    r'<div id="([^"]+)" class="off">(.*?)(?=<div id="[^"]+" class="off">|\Z)', re.S)
JAE_2015_LINKS = re.compile(r'<div class="actLink[^"]*">(.*?)</div>', re.S)
JAE_2015_IMG = re.compile(r'<img src="([^"]+)" class="textLeft"')
JAE_2017_NAME = re.compile(r'<div class="name_area">(.*?)</div>', re.S)
JAE_2017_LINKS = re.compile(r'<div class="girls_area_right">.*?<ul>(.*?)</ul>', re.S)
JAE_2017_IMG = re.compile(r'<a class="group pop" href="([^"]+)"')
JAE_H2 = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)
JAE_H3 = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S)
JAE_H4 = re.compile(r"<h4[^>]*>(.*?)</h4>", re.S)
JAE_P = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
JAE_ANCHOR = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
#: 没交照片的位置放的是占位图，不是这个人的像。
JAE_PLACEHOLDER = ("nophoto", "noimage", "no_photo", "comingsoon")


X_PROFILE = "https://x.com/{}"
#: 对照账号：X 官方号，登出页永远有 og:image。用来区分「账号没了」和「我们被限流」。
X_CONTROL = "X"


# ---------------------------------------------------------------- 解析

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(TAG.sub(" ", text)).replace("\xa0", " ")).strip()


def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def split_names(text: str) -> list[str]:
    """`别名` 一栏可能塞好几个名字；分隔符不分中日文标点。不按空格拆——罗马字里有空格。"""
    return [part.strip() for part in re.split(r"[、,，/／|｜;；]", text)
            if part.strip() and part.strip() not in LAOSHI_BLANK]


def external_links(html: str, own_hosts: tuple[str, ...], base: str = "") -> list[str]:
    """页面上的站外绝对链接，去掉本站与相对路径。

    bstar-pro 的页脚有 `href="/https://x.com/bstar_pro/"` 这种写坏的相对路径，
    urljoin 之后落在本站主机上，正好被本站过滤掉——不必单独处理。
    """
    out = []
    for href in HREF.findall(html):
        url = html_lib.unescape(href).strip()
        if base:
            url = urljoin(base, url)
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            continue
        if under(parts.hostname.casefold(), own_hosts):
            continue
        out.append(url)
    return dedupe(out)


def laoshi_listing(sitemap_xml: str) -> list[str]:
    """sitemap 里的女优页；站内搜索是纯前端 JS，服务端没有可用的检索入口。"""
    return sorted(set(LAOSHI_ACTOR.findall(sitemap_xml)))


def laoshi_names(html: str) -> list[str]:
    """标题 `中文名（日文名 / Romaji）` 加「基本资料」里的中文名、日文名、别名。

    标题有时只有一种写法（`桃園怜奈`、`西田カリナ（Karina Nishida）`），所以两处都取；
    「待补充」这类占位词不是名字。
    """
    names: list[str] = []
    title = LAOSHI_TITLE.search(html)
    if title:
        head = clean(title.group(1)).split("｜")[0].split("|")[0]
        main, _, rest = (re.split(r"([（(])", head, maxsplit=1) if re.search(r"[（(]", head)
                         else (head, "", ""))
        names += split_names(main) + split_names(rest.rstrip("）)"))
    for label, value in LAOSHI_FACT.findall(html):
        if clean(label) in LAOSHI_NAME_FIELDS:
            names += split_names(clean(value))
    return dedupe(names)


def _same_as(node) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        same = node.get("sameAs")
        if isinstance(same, str):
            found.append(same)
        elif isinstance(same, list):
            found += [item for item in same if isinstance(item, str)]
        for value in node.values():
            found += _same_as(value)
    elif isinstance(node, list):
        for item in node:
            found += _same_as(item)
    return found


def laoshi_links(html: str) -> list[str]:
    """ld+json 的 sameAs 加正文外链。sameAs 是站方明确声明的「本人主页」，正文锚点作补充。"""
    urls: list[str] = []
    for block in LD_JSON.findall(html):
        try:
            urls += _same_as(json.loads(block))
        except ValueError:
            continue
    return dedupe(urls + external_links(html, LAOSHI_OWN))


def bstar_gated(html: str) -> bool:
    return bool(BSTAR_GATE.search(html)) and not BSTAR_ENTRY.search(html)


def bstar_listing(html: str) -> list[tuple[str, list[str]]]:
    """models.html → [(模特页 URL, [日文名, 罗马字])]。名字来自缩略图 alt 与两行说明。"""
    out: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for href, inner in BSTAR_ENTRY.findall(html):
        url = urljoin(BSTAR, html_lib.unescape(href))
        if url in seen:
            continue
        seen.add(url)
        names: list[str] = []
        alt = BSTAR_ALT.search(inner)
        if alt:
            names.append(clean(alt.group(1)))
        names += [clean(span) for span in BSTAR_SPAN.findall(inner)]
        out.append((url, dedupe(names)))
    return out


# ---------------------------------------------------------------- 采集

def page_record(source: str, url: str, names: list[str], links: list[str], *,
                official: tuple[str, str] | None = None,
                owned: list[tuple[str, str]] | None = None,
                portrait: str = "", note: str = "") -> dict:
    """`links` 走平台账号那一路；`owned` 是资料页写明的本人博客与官网，带页面上的链接文字。"""
    return {"source": source, "page": url, "names": names, "links": links,
            "official": official, "owned": list(owned or ()), "portrait": portrait,
            "note": note}


def failed(source: str, url: str, exc: Exception) -> dict:
    return page_record(source, url, [], [], note=f"未取得：{type(exc).__name__}: {exc}"[:160])


def collect_laoshi(site: Site, limit: int = 0) -> tuple[list[str], list[dict]]:
    """返回（站点自身的社交链接, 页面记录）。首页上的账号是站方的，不是任何女优的。"""
    site_links = [url for url in external_links(site.get(LAOSHI), LAOSHI_OWN) if platform(url)]
    urls = laoshi_listing(site.get(LAOSHI + "sitemap.xml"))
    if limit:
        urls = urls[:limit]
    pages = []
    for url in urls:
        try:
            html = site.get(url)
            pages.append(page_record("laoshi", url, laoshi_names(html), laoshi_links(html)))
        except Exception as exc:   # 单页失败只记未取得，不拖垮整批
            pages.append(failed("laoshi", url, exc))
    return site_links, pages


def bstar_pass_gate(site: Site) -> None:
    site.request("POST", BSTAR_MODELS, body=b"age_check=yes",
                 headers={"Content-Type": "application/x-www-form-urlencoded"})


def bstar_page(site: Site, url: str) -> str:
    html = site.get(url)
    if bstar_gated(html):
        bstar_pass_gate(site)
        html = site.get(url, refresh=True)
        if bstar_gated(html):
            raise RuntimeError("年龄门没过")
    return html


def collect_bstar(site: Site, limit: int = 0) -> tuple[list[str], list[dict]]:
    """事务所官网：列表页给名字，模特页给 SNS。列表页上的账号是事务所的，要从每页里减掉。"""
    listing = bstar_page(site, BSTAR_MODELS)
    site_links = [url for url in external_links(listing, BSTAR_OWN, BSTAR) if platform(url)]
    entries = bstar_listing(listing)
    if limit:
        entries = entries[:limit]
    pages = []
    for url, names in entries:
        try:
            html = bstar_page(site, url)
            pages.append(page_record("bstar", url, names, external_links(html, BSTAR_OWN, BSTAR),
                                     official=(url, BSTAR_LABEL)))
        except Exception as exc:
            pages.append(failed("bstar", url, exc))
    return site_links, pages


def strip_comments(html: str) -> str:
    """注释里的东西不属于这一页。

    jae 的女优页是同一份模板复制出来的，上一位的资料整段留在注释里：2017 那届
    `actress/04.html` 是 AIKA，注释里躺着 `blog.livedoor.jp/sonoda_mion/` 和
    `instagram.com/kamisaki_shiori/`——不先去注释，AIKA 名下会装上另外两个人的账号。
    2014 那届的 `<li id="AyamiShunka">` 是填好数据的模板样例，同样在注释里。
    """
    return COMMENT.sub(" ", html)


def jae_anchors(fragment: str, base: str) -> list[tuple[str, str]]:
    """片段里的站外链接 → [(URL, 链接文字)]。文字取页面上写的那行（`公式ブログ`）。"""
    out: dict[str, str] = {}
    for href, inner in JAE_ANCHOR.findall(fragment):
        url = urljoin(base, html_lib.unescape(href).strip())
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            continue
        if under(parts.hostname.casefold(), JAE_OWN):
            continue
        out.setdefault(url, clean(inner))
    return list(out.items())


def jae_portrait(src: str, base: str) -> str:
    if not src or any(mark in src.casefold() for mark in JAE_PLACEHOLDER):
        return ""
    return urljoin(base, html_lib.unescape(src).strip())


def jae_entry(anchor: str, names: list[str], links: list[tuple[str, str]],
              portrait: str) -> dict:
    return {"anchor": anchor, "names": dedupe(names), "links": links,
            "portrait": portrait}


def jae_2014_entries(html: str, base: str) -> list[dict]:
    """`<li id="…">` 一位一条：`h2` 是日文名，`alignright` 是罗马字，资料表末尾是本人的站。"""
    out = []
    for anchor, block in JAE_2014_ENTRY.findall(strip_comments(html)):
        names = [clean(text) for text in JAE_H2.findall(block)]
        names += [clean(text) for text in JAE_2014_ROMAJI.findall(block)]
        image = JAE_2014_IMG.search(block)
        out.append(jae_entry(anchor, names, jae_anchors(block, base),
                             jae_portrait(image.group(1) if image else "", base)))
    return out


def jae_2015_entries(html: str, base: str) -> list[dict]:
    """`class="off"` 的隐藏层一位一条：`bigName` 日文名、`smallName` 罗马字。

    链接只取 `actLink*` 那一格。同一层的资料表里还有一条「おすすめの作品タイトル」，
    那是片商的商品页（`ec.sod.co.jp/detail/…`），不是本人的链接。
    """
    out = []
    for anchor, block in JAE_2015_ENTRY.findall(strip_comments(html)):
        names = [clean(text) for text in JAE_H3.findall(block)]
        names += [clean(text) for text in JAE_H4.findall(block)]
        links: list[tuple[str, str]] = []
        for fragment in JAE_2015_LINKS.findall(block):
            links += jae_anchors(fragment, base)
        image = JAE_2015_IMG.search(block)
        out.append(jae_entry(anchor, names, links,
                             jae_portrait(image.group(1) if image else "", base)))
    return out


def jae_2017_pages(html: str, base: str) -> list[str]:
    """名录页 → 详情页 URL。详情页文件名有的是编号有的是罗马字，一律照写。"""
    return sorted({urljoin(base, href) for href in JAE_2017_DETAIL.findall(html)})


def jae_2017_entry(html: str, url: str) -> dict:
    """详情页一位一条：`name_area` 给名字，`girls_area_right` 的图标列表给账号。

    人像取 `class="group pop"` 那个大图，不取旁边 `m.jpg` 的缩略图。
    """
    body = strip_comments(html)
    area = JAE_2017_NAME.search(body)
    names: list[str] = []
    if area:
        names = [clean(text) for text in JAE_H2.findall(area.group(1))]
        names += [clean(text) for text in JAE_P.findall(area.group(1))]
    links: list[tuple[str, str]] = []
    for fragment in JAE_2017_LINKS.findall(body):
        links += jae_anchors(fragment, url)
    image = JAE_2017_IMG.search(body)
    return jae_entry(url.rsplit("/", 1)[-1], names, links,
                     jae_portrait(image.group(1) if image else "", url))


def take(items: list, limit: int) -> list:
    return items[:limit] if limit else items


def collect_jae(site: Site, limit: int = 0) -> tuple[list[str], list[dict]]:
    """展会名录三届。名录页上没有女优的账号，站方链接一栏为空。

    链接文字（`公式ブログ`／`ツイッター`）当标签；平台账号照常走 `links`，
    博客与本人官网走 `owned`。人像同批带出，判定与链接同一次。
    """
    pages: list[dict] = []
    entries: list[tuple[str, dict]] = []

    for path in JAE_2014_LISTS:
        url = JAE + path
        try:
            html = site.get(url)
        except Exception as exc:
            pages.append(failed("jae", url, exc))
            continue
        entries += [(f"{url}#{entry['anchor']}", entry)
                    for entry in take(jae_2014_entries(html, url), limit)]

    url = JAE + JAE_2015_LIST
    try:
        html = site.get(url)
    except Exception as exc:
        pages.append(failed("jae", url, exc))
    else:
        entries += [(f"{url}#{entry['anchor']}", entry)
                    for entry in take(jae_2015_entries(html, url), limit)]

    url = JAE + JAE_2017_LIST
    detail_urls: list[str] = []
    try:
        listing = site.get(url)
    except Exception as exc:
        pages.append(failed("jae", url, exc))
    else:
        detail_urls = take(jae_2017_pages(listing, url), limit)
    for detail in detail_urls:
        try:
            html = site.get(detail)
        except Exception as exc:
            pages.append(failed("jae", detail, exc))
            continue
        entries.append((detail, jae_2017_entry(html, detail)))

    for page_url, entry in entries:
        owned = [(url, label) for url, label in entry["links"] if not platform(url)]
        pages.append(page_record("jae", page_url, entry["names"],
                                 [url for url, _ in entry["links"]],
                                 owned=owned, portrait=entry["portrait"]))
    return [], pages


COLLECTORS = {"laoshi": collect_laoshi, "bstar": collect_bstar,
              "jae": collect_jae}


# ---------------------------------------------------------------- 判定

def row(**values) -> dict:
    record = {field: "" for field in FIELDS}
    record.update(values)
    return record


def index_names(performers: list[dict]) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {}
    for record in performers:
        for name in [record["name"], *record["chain"]]:
            key = name_key(name)
            if key:
                index.setdefault(key, set()).add(record["entity_id"])
    return index


def matched_ids(names: list[str], index: dict[str, set[int]]) -> tuple[set[int], list[str]]:
    """页面上的名字 → （命中的 entity_id, 真正对上的那几个名字）。"""
    matched: set[int] = set()
    used: list[str] = []
    for name in names:
        ids = index.get(name_key(name))
        if ids:
            matched |= ids
            used.append(name)
    return matched, used


def load_existing(connection: sqlite3.Connection) -> tuple[dict, dict]:
    """账本现有链接 → ({entity_id: {(平台, handle): url}}, {entity_id: {url}})。"""
    handles: dict[int, dict[tuple[str, str], str]] = {}
    urls: dict[int, set[str]] = {}
    for entity_id, url in connection.execute("SELECT entity_id, url FROM entity_link"):
        urls.setdefault(entity_id, set()).add(url)
        name, account = platform(url), handle(url)
        if name and account:
            handles.setdefault(entity_id, {})[(name, account)] = url
    return handles, urls


def judge(pages: list[dict], site_links: list[str], performers: list[dict],
          existing_handles: dict, existing_urls: dict) -> tuple[list[dict], Counter]:
    """页面记录 → 复核行。会把本轮判 ok 的账号记进 existing_handles，后来的来源据此判已有/冲突。

    冲突只对「进这页之前」账本已有的账号判：同一页上列两个 X 账号是主号加副号，
    不是两处资料打架。
    """
    by_id = {record["entity_id"]: record for record in performers}
    index = index_names(performers)
    ignore = {(platform(url), handle(url)) for url in site_links}
    rows: list[dict] = []
    stats: Counter = Counter()
    for page in pages:
        base = {"kind": "performer", "source": page["source"], "page": page["page"]}
        if page["note"]:
            rows.append(row(**base, verdict="未取得", evidence=page["note"]))
            stats["页面未取得"] += 1
            continue
        matched, used = matched_ids(page["names"], index)
        socials = []
        seen: set[tuple[str, str]] = set()
        for url in page["links"]:
            key = (platform(url), handle(url))
            if not key[0] or not key[1] or key in ignore or key in seen:
                continue
            seen.add(key)
            socials.append((canonical_url(url), *key))
        if not matched:
            stats["页面不在账本"] += 1
            continue
        matched_name = "、".join(used)
        if len(matched) > 1:
            names = "、".join(by_id[entity_id]["name"] for entity_id in sorted(matched))
            for url, _, _ in socials:
                link_kind, label = classify(url)
                rows.append(row(**base, link_kind=link_kind, label=label, url=url,
                                matched_name=matched_name, verdict="需人工消歧",
                                evidence=f"页面名「{matched_name}」对上多位：{names}"))
                stats["需人工消歧"] += 1
            continue
        entity_id = matched.pop()
        record = by_id[entity_id]
        base.update(entity_id=entity_id, name=record["name"], matched_name=matched_name)
        where = f"{page['source']} {page['page']}；页面名「{matched_name}」对上账本「{record['name']}」"
        if not socials and not page["official"] and not page["owned"]:
            rows.append(row(**base, verdict="未取得", evidence=f"{where}；页面上没有社交链接"))
            stats["命中但无社媒"] += 1
            continue
        held = existing_handles.setdefault(entity_id, {})
        prior = dict(held)
        for url, name, account in socials:
            link_kind, label = classify(url)
            item = row(**base, link_kind=link_kind, label=label, url=url)
            if (name, account) in prior:
                item.update(verdict="已有", evidence=f"{where}；账本已有 {prior[(name, account)]}")
            else:
                others = [held_url for (held_name, _), held_url in prior.items() if held_name == name]
                if others:
                    item.update(verdict="conflict",
                                evidence=f"{where}；账本同平台另有 {'、'.join(others)}，需交叉核对")
                else:
                    item.update(verdict="ok", evidence=where)
                    held[(name, account)] = url
            rows.append(item)
            stats[item["verdict"]] += 1
        # 博客与本人官网没有 handle 可比，只按 URL 判重；标签用页面上写的那行链接文字。
        for url, shown in page["owned"]:
            link_kind, fallback = classify(url)
            item = row(**base, link_kind=link_kind, label=shown or fallback, url=url)
            if url in existing_urls.get(entity_id, set()):
                item.update(verdict="已有", evidence=f"{where}；账本已有此地址")
            else:
                item.update(verdict="ok",
                            evidence=f"{where}；资料页写明的本人链接「{shown or fallback}」")
                existing_urls.setdefault(entity_id, set()).add(url)
            rows.append(item)
            stats[item["verdict"]] += 1
        if page["official"]:
            url, label = page["official"]
            if url in existing_urls.get(entity_id, set()):
                rows.append(row(**base, link_kind="official", label=label, url=url,
                                verdict="已有", evidence=f"{where}；账本已有此页"))
                stats["已有"] += 1
            else:
                rows.append(row(**base, link_kind="official", label=label, url=url,
                                verdict="ok", evidence=f"{where}；本人在事务所官网的页面"))
                existing_urls.setdefault(entity_id, set()).add(url)
                stats["ok"] += 1
    return rows, stats


def portrait_rows(pages: list[dict], performers: list[dict]) -> list[dict]:
    """名录页上的人像 → 头像候选行，喂 harvest_social_avatars.py 的 jae 路线。

    与链接队列同一批页面、同一次名字判定：唯一命中才出行，对上多位的不出——
    头像装错人和链接装错人是同一个错误，判据不能两套。
    """
    by_id = {record["entity_id"]: record for record in performers}
    index = index_names(performers)
    out: list[dict] = []
    for page in pages:
        if page["note"] or not page["portrait"]:
            continue
        matched, used = matched_ids(page["names"], index)
        if len(matched) != 1:
            continue
        entity_id = next(iter(matched))
        out.append({"entity_id": str(entity_id), "kind": "performer",
                    "name": by_id[entity_id]["name"], "matched_name": "、".join(used),
                    "portrait_url": page["portrait"], "source": page["source"],
                    "page": page["page"], "verdict": "命中"})
    return out


# ---------------------------------------------------------------- 验活

def probe_x(site: Site, account: str, memo: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """X 账号活不活 → (状态, 显示名)。同一账号只查一次。"""
    key = account.casefold()
    if key not in memo:
        try:
            state, display = x_profile_state(site.get(X_PROFILE.format(account)))
            if state == "unknown":
                # 实测 2026-09-02：不存在的账号登出页也是 200，只是没有任何 og 标签——和限流
                # 回的 JS 壳长得一样。同一时刻不走缓存再取对照账号：对照有 og，这个就是真没了；
                # 对照也没有，是我们被限流，只能记未取得。
                control, _ = x_profile_state(site.get(X_PROFILE.format(X_CONTROL), refresh=True))
                state = "gone" if control == "alive" else "unknown"
                display = "登出页无资料，对照账号正常" if state == "gone" else "登出页无资料，对照账号也无（限流）"
            memo[key] = ({"alive": ALIVE, "gone": GONE}.get(state, UNKNOWN), display)
        except HttpStatusError as exc:
            memo[key] = (GONE if exc.status == 404 else UNKNOWN, f"HTTP {exc.status}")
        except Exception as exc:
            memo[key] = (UNKNOWN, type(exc).__name__)
    return memo[key]


def probe_rows(rows: list[dict], existing_handles: dict, site: Site | None) -> Counter:
    """给 ok / conflict 的社交行填 `alive`；冲突行连账本那边的旧号一起验，证据里写明。

    site 为 None 表示本轮不验（`--no-probe`），全部标未验——列不能空着，空着看不出
    是「没验」还是「验了没结论」。
    """
    memo: dict[str, tuple[str, str]] = {}
    stats: Counter = Counter()
    for item in rows:
        if item["verdict"] not in {"ok", "conflict"} or item["link_kind"] != "social":
            continue
        name = platform(item["url"])
        if name != "X" or site is None:
            item["alive"] = UNVERIFIED
            continue
        state, display = probe_x(site, handle(item["url"]), memo)
        item["alive"] = state
        stats[state] += 1
        if display:
            item["evidence"] += (f"；X 显示名「{display}」" if state == ALIVE else f"；X 验活：{display}")
        if item["verdict"] == "conflict":
            olds = [url for (held_name, _), url in existing_handles.get(item["entity_id"], {}).items()
                    if held_name == "X" and handle(url) != handle(item["url"])]
            for old in olds:
                old_state, _ = probe_x(site, handle(old), memo)
                item["evidence"] += f"；账本旧号 {old}：{old_state}"
    return stats


def installable(rows: list[dict]) -> list[dict]:
    """只有 ok 且没被验成失效的行进安装队列。"""
    return [item for item in rows if item["verdict"] == "ok" and item["alive"] != GONE]


# ---------------------------------------------------------------- 入口

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="安装队列 CSV；复核表写到同目录的 <stem>-review.csv")
    parser.add_argument("--source", choices=("all", *SOURCES), default="all")
    parser.add_argument("--min-assets", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0, help="每个来源最多看几页（试跑用）")
    parser.add_argument("--interval", type=float, default=1.2)
    parser.add_argument("--x-interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--refresh", action="store_true", help="忽略本地缓存重新抓")
    parser.add_argument("--no-probe", action="store_true", help="不去 x.com 验活")
    parser.add_argument("--cache-dir", type=Path, default=STATE_DIR / "directory-links")
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".directory-links.lock")
    return parser


def run(args) -> int:
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    try:
        performers = load_performers(connection, args.min_assets)
        existing_handles, existing_urls = load_existing(connection)
    finally:
        connection.close()
    print(f"账本可比对 performer {len(performers)} 位")

    rows: list[dict] = []
    portraits: list[dict] = []
    totals: Counter = Counter()
    sources = SOURCES if args.source == "all" else (args.source,)
    for source in sources:
        site = Site(args.cache_dir / source, args.interval, args.timeout, refresh=args.refresh,
                    via_proxy=source in PROXY_SOURCES)
        try:
            site_links, pages = COLLECTORS[source](site, args.limit)
        except Exception as exc:
            print(f"[{source}] 未取得：{type(exc).__name__}: {exc}")
            continue
        finally:
            site.close()
        source_rows, stats = judge(pages, site_links, performers, existing_handles, existing_urls)
        rows += source_rows
        portraits += portrait_rows(pages, performers)
        totals.update(stats)
        print(f"[{source}] 页面 {len(pages)}，网络 {site.fetched} / 缓存 {site.cached}，"
              f"站方账号 {len(site_links)} 条已剔除，{dict(stats)}")

    x_site = None if args.no_probe else Site(args.cache_dir / "x", args.x_interval, args.timeout,
                                              refresh=args.refresh, via_proxy=True)
    try:
        alive = probe_rows(rows, existing_handles, x_site)
    finally:
        if x_site is not None:
            x_site.close()
    print(f"X 验活 {dict(alive)}" if x_site is not None else "本轮未验活")

    order = {"conflict": 0, "ok": 1, "需人工消歧": 2, "已有": 3, "未取得": 4}
    rows.sort(key=lambda item: (order.get(item["verdict"], 9), str(item["name"]), item["url"]))
    review = args.output.with_name(args.output.stem + "-review.csv")
    queue = installable(rows)
    write_rows(args.output, FIELDS, queue)
    write_rows(review, FIELDS, rows)
    result = {"安装队列": len(queue), "复核行": len(rows), **totals,
              "output": str(args.output), "review": str(review)}
    if portraits:
        portrait_path = args.output.with_name(args.output.stem + "-portraits.csv")
        write_rows(portrait_path, PORTRAIT_FIELDS, portraits)
        result.update({"人像候选": len(portraits), "portraits": str(portrait_path)})
    print(result)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(job_main(build_parser, run))
