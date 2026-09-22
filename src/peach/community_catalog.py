"""采集任务的社区来源：AVBase、JavBus 与 javdb 按番号取作品资料和封面，封面先求互相比对。

官方渠道（r18.dev、DMM CDN、MGS、Prestige）落空时才问这三家，决策见 ADR-0030 与 ADR-0032。

**AVBase**（2026-09-14 实测）：`/works?q=<番号>` 是 Next.js 页，`__NEXT_DATA__` 里
`props.pageProps.works[]` 就是命中的作品，每部带 `work_id`、日文 `title`、`actors[]`，
以及它在各家店铺的商品 `products[]`（`source` 为 `fanza`、`duga` 等，各自给
`image_url`、`maker`、`label`、`series`、`date`、`iteminfo.director`）。一次请求就够，
不必再进作品页。商品里可能混着收录这段内容的合集（素人系常见），合集的标题和番号
都对不上本作，按这两条筛掉。

**JavBus**：作品页就是 `/<番号>`（厂牌回查留下的 126 页缓存为证），字段在
`<p><span class="header">識別碼:</span> …</p>` 这样的行里，封面是 `bigImage` 链接
（`/pics/cover/<id>_b.jpg`），女优在 `star-name`。它有年龄门，要带用户在采集设置里贴的
Cookie；门页上没有「識別碼」，按这一点报错。

**javdb**：搜索页 `/search?q=<番号>&f=all` 的结果卡片带番号，番号一致的那张进详情页；
详情页 `?locale=zh` 下面板字段是 `番號`、`日期`、`片商`、`發行`、`系列`、`導演`、`演員`，
演员里女优带 `actor-female`。它按出口 IP 计配额，限速与封禁的处理在 `scraping_access`
和调用方的主机间隔里，这里只管解析。几家的值常有出入：ABW-358 在 javdb 上发行日期是
MGS 的 5/23、标题带 MGS 附注、演员里有男优，所以社区来源的资料一律要两家一致才免复核。

封面比对用 dHash：两张图宽高比相差不超过 4%、64 位指纹相差不超过 10 位就算同一张。
同一张图出现在两个不同的图源（DMM、DUGA、MGS、JavBus、javdb 各算一个）就算印证；官方渠道
只取到小图时，那张小图也参加比对。可用的图全出自一个图源、没有别家可比时，取其中最大的
那张，印证图源留空（ADR-0032）；两个图源各给了图却对不上，是有证据的冲突，不用。
"""
from __future__ import annotations

import io
import json
import re
import urllib.parse
from dataclasses import dataclass

import httpx
from PIL import Image

from .catalog_rules import same_release_code
from .jav_cover_fetch import (SMALL_MIN_WIDTH, THUMBNAIL, Candidate, NotFound, Unavailable,
                              _fetch, candidate_for, is_cross_product_cover)
from .javdb import LOGIN as JAVDB_LOGIN, clean
from .metadata import identifies_code
from .scraping_access import SourcePaused
from .scripting import host_under, hostname_of

AVBASE_SEARCH = "https://www.avbase.net/works?q={code}"
AVBASE_WORK = "https://www.avbase.net/works/{key}"
JAVBUS_BASE = "https://www.javbus.com"
JAVBUS_WORK = JAVBUS_BASE + "/{code}"
JAVDB_BASE = "https://javdb.com"
JAVDB_SEARCH = JAVDB_BASE + "/search?q={code}&f=all"
PAGE_LIMIT = 4 * 1024 * 1024
IMAGE_LIMIT = 16 * 1024 * 1024

#: 同一部作品在多家店铺上架时，资料先取 FANZA 那条：它与 r18.dev 同源，写法和账本最接近。
#: 店铺名用 AVBase 自己在 `products[].source` 里写的值（2026-09-16 实测 `fanza`、
#: `mgstage`、`duga`）；写错的名字不会报错，只是那家店排到末位。
AVBASE_PRODUCT_ORDER = ("fanza", "mgstage", "duga")
#: 图源按店铺算，不按主机名：`pics.dmm.co.jp` 与 `awsimgsrc.dmm.co.jp` 是同一家的两条路径。
IMAGE_ORIGINS = (("dmm", ("dmm.co.jp", "dmm.com")), ("duga", ("duga.jp",)),
                 ("mgstage", ("mgstage.com",)), ("javbus", ("javbus.com",)),
                 ("javdb", ("jdbstatic.com", "jdbimgs.com", "javdb.com")))
#: 社区站自己的图要带站内 Referer；店铺的图按 `candidate_for` 取官方 Referer。
ORIGIN_REFERERS = {"javbus": JAVBUS_BASE + "/", "javdb": JAVDB_BASE + "/"}
ASPECT_TOLERANCE = 0.04
HASH_DISTANCE = 10

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
_AVBASE_DATE = re.compile(r"^[A-Za-z]{3} ([A-Za-z]{3}) (\d{1,2}) (\d{4})")
_MONTHS = {name: index for index, name in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
_JAVBUS_FIELD = re.compile(r'<p><span class="header">([^<:：]+)[:：]</span>(.*?)</p>', re.S)
_JAVBUS_TITLE = re.compile(r"<h3>([^<]*)</h3>")
_JAVBUS_COVER = re.compile(r'<a class="bigImage" href="([^"]+)"')
_JAVBUS_ACTRESS = re.compile(r'<div class="star-name"><a[^>]*>([^<]+)</a>')
_JAVDB_BOX = re.compile(r'<a href="(/v/[A-Za-z0-9]+)" class="box" title="[^"]*">.*?<strong>([^<]+)</strong>', re.S)
_JAVDB_PANEL = re.compile(r'<div class="panel-block[^"]*">\s*<strong>([^<:：]+)[:：]</strong>\s*(?:&nbsp;)?\s*'
                          r'<span class="value">(.*?)</span>', re.S)
_JAVDB_TITLE = re.compile(r'<strong class="current-title">([^<]*)</strong>')
_JAVDB_COVER = re.compile(r'<img src="(https://[^"]+)" class="video-cover"')
_JAVDB_ACTRESS = re.compile(r'<a\s([^>]*)>([^<]+)</a>')
#: 演員一栏里每个人名都挂着自己的资料页。那串 id 正是人物页 JavDB 入口要的东西，
#: 取名字时顺手带出来——另走一趟演员页只是把同一页再取一遍，而 javdb 的配额最紧。
_JAVDB_ACTOR_HREF = re.compile(r'href="/actors/([A-Za-z0-9]+)"')
_JAPANESE = re.compile(r"[぀-ヿ一-鿿]")


def _text(body: bytes) -> str:
    return body.decode("utf-8", "replace")


def _avbase_date(raw: object) -> str:
    """`Fri May 26 2023 09:00:00 GMT+0900` 是日本时间，日期直接取字面。"""
    found = _AVBASE_DATE.match(str(raw or ""))
    if not found or found.group(1) not in _MONTHS:
        return ""
    return f"{found.group(3)}-{_MONTHS[found.group(1)]:02d}-{int(found.group(2)):02d}"


def _named(value: object) -> str:
    return str(value.get("name") or "").strip() if isinstance(value, dict) else ""


def _avbase_products(code: str, work: dict) -> list[dict]:
    """本作自己的商品条目，按 `AVBASE_PRODUCT_ORDER` 排。

    商品号认得出这个番号的说了算，标题相等只是退路。AVBase 的作品标题取自名寄せ里的
    某一件商品，而那一件可能是收录本作的合集：259LUXU-1514 的作品标题就是 FANZA 合集
    `118sng013` 的『FIRST CLASS ファーストクラス File/006』，按标题相等收下它，片名、
    厂牌、系列和发行日就全成了那张合集的（正确的是 MGStage 那条『ラグジュTV 1485』，
    2021-11-19）。一件商品号都认不出时才比标题——DUGA 的 `prestige-6584` 这类自编号
    与番号无关，那时只有标题能认。
    """
    products = [product for product in work.get("products") or [] if isinstance(product, dict)]
    named = [product for product in products
             if identifies_code(code, {"content_id": product.get("product_id")})]
    if not named:
        title = str(work.get("title") or "").strip()
        named = [product for product in products
                 if str(product.get("title") or "").strip() == title]
    rank = {source: index for index, source in enumerate(AVBASE_PRODUCT_ORDER)}
    return sorted(named, key=lambda product: rank.get(product.get("source"), len(rank)))


def _avbase_covers(code: str, products: list[dict]) -> list[str]:
    urls = (str(product.get("image_url") or "").strip() for product in products)
    return list(dict.fromkeys(url for url in urls if url.startswith("https://")
                              and not THUMBNAIL.search(url) and not is_cross_product_cover(code, url)))


def avbase_work(transport, code: str, *, deadline: float | None = None) -> dict:
    page = _text(_fetch(transport, AVBASE_SEARCH.format(code=urllib.parse.quote(code)),
                        referer="https://www.avbase.net/", limit=PAGE_LIMIT, deadline=deadline))
    found = _NEXT_DATA.search(page)
    try:
        props = json.loads(found.group(1))["props"]["pageProps"] if found else None
    except (ValueError, KeyError, TypeError):
        props = None
    if not isinstance(props, dict):
        raise Unavailable("AVBase 页面结构未识别，可能在验证访问")
    works = [work for work in props.get("works") or []
             if isinstance(work, dict) and same_release_code(code, str(work.get("work_id") or ""))]
    if not works:
        raise NotFound("AVBase 没有这个番号")
    work = works[0]
    products = _avbase_products(code, work)
    first = lambda pick: next((value for value in map(pick, products) if value), "")
    info = lambda key: lambda product: str((product.get("iteminfo") or {}).get(key) or "").strip()
    covers = _avbase_covers(code, products)
    key = f"{work['prefix']}:{work['work_id']}" if work.get("prefix") else str(work.get("work_id"))
    return dict(id=str(work.get("work_id") or code), source_url=AVBASE_WORK.format(key=urllib.parse.quote(key, safe=":")),
                title=first(lambda product: str(product.get("title") or "").strip())
                or str(work.get("title") or "").strip(),
                actresses=[{"japanese_name": _named(actor)} for actor in work.get("actors") or [] if _named(actor)],
                maker=first(lambda product: _named(product.get("maker"))),
                label=first(lambda product: _named(product.get("label"))),
                series=first(lambda product: _named(product.get("series"))),
                director=first(info("director")),
                release_date=_avbase_date(products[0].get("date") if products else work.get("min_date")),
                cover_urls=covers, cover_url=covers[0] if covers else "")


def javbus_work(transport, code: str, *, deadline: float | None = None) -> dict:
    url = JAVBUS_WORK.format(code=urllib.parse.quote(code))
    try:
        page = _text(_fetch(transport, url, referer=JAVBUS_BASE + "/", limit=PAGE_LIMIT, deadline=deadline))
    except NotFound:
        raise NotFound("JavBus 没有这个番号") from None
    fields = {clean(label): clean(value) for label, value in _JAVBUS_FIELD.findall(page)}
    shown = fields.get("識別碼", "").replace(" ", "")
    if not shown:
        raise Unavailable("JavBus 回的不是作品页，多半是年龄确认页：到采集设置给 JavBus 贴上浏览器里的 Cookie")
    if not same_release_code(code, shown):
        raise NotFound("JavBus 没有这个番号")
    heading = _JAVBUS_TITLE.search(page)
    cover = _JAVBUS_COVER.search(page)
    covers = [urllib.parse.urljoin(JAVBUS_BASE, cover.group(1))] if cover else []
    runtime = re.search(r"\d+", fields.get("長度", ""))
    return dict(id=shown, source_url=url,
                title=clean(heading.group(1)).removeprefix(shown).strip() if heading else "",
                actresses=[{"japanese_name": clean(name)} for name in _JAVBUS_ACTRESS.findall(page)],
                maker=fields.get("製作商", ""), label=fields.get("發行商", ""),
                series=fields.get("系列", ""), director=fields.get("導演", ""),
                release_date=fields.get("發行日期", ""), runtime=int(runtime.group()) if runtime else None,
                cover_urls=covers, cover_url=covers[0] if covers else "")


def javdb_actresses(value: str) -> list[dict]:
    """演員一栏里的女优：名字，以及她在 javdb 的演员 id。

    男优挂的是同样的 `/actors/` 链接，靠 `actor-female` 分开。href 与 class 在标签里的
    先后不固定，所以先取整段属性再判，不假设它们的次序。
    """
    found = []
    for attributes, name in _JAVDB_ACTRESS.findall(value):
        if "actor-female" not in attributes:
            continue
        actor = _JAVDB_ACTOR_HREF.search(attributes)
        found.append({"japanese_name": clean(name), "profile_source": "javdb",
                      "external_id": actor.group(1) if actor else ""})
    return found


def _javdb_page(transport, url: str, *, deadline: float | None) -> str:
    page = _text(_fetch(transport, url, referer=JAVDB_BASE + "/", limit=PAGE_LIMIT, deadline=deadline))
    if JAVDB_LOGIN.search(page):
        raise Unavailable("javdb 要求登录")
    return page


def _maker_writing(value: str) -> str:
    """片商一栏并列英文与日文（`PRESTIGE,プレステージ`），取日文那一种。"""
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return next((part for part in parts if _JAPANESE.search(part)), parts[0] if parts else "")


def javdb_work(transport, code: str, *, deadline: float | None = None) -> dict:
    search = _javdb_page(transport, JAVDB_SEARCH.format(code=urllib.parse.quote(code)), deadline=deadline)
    path = next((path for path, shown in _JAVDB_BOX.findall(search) if same_release_code(code, clean(shown))), None)
    if path is None:
        raise NotFound("javdb 没有这个番号")
    url = JAVDB_BASE + path
    page = _javdb_page(transport, url + "?locale=zh", deadline=deadline)
    panel = {clean(label): value for label, value in _JAVDB_PANEL.findall(page)}
    shown = clean(panel.get("番號", "")).replace(" ", "")
    if not same_release_code(code, shown):
        raise Unavailable("javdb 详情页的番号与搜索结果不一致")
    runtime = re.search(r"\d+", clean(panel.get("時長", "")))
    title = _JAVDB_TITLE.search(page)
    cover = _JAVDB_COVER.search(page)
    return dict(id=shown, source_url=url, title=clean(title.group(1)) if title else "",
                actresses=javdb_actresses(panel.get("演員", "")),
                maker=_maker_writing(clean(panel.get("片商", ""))), label=clean(panel.get("發行", "")),
                series=clean(panel.get("系列", "")), director=clean(panel.get("導演", "")),
                release_date=clean(panel.get("日期", "")), runtime=int(runtime.group()) if runtime else None,
                cover_urls=[cover.group(1)] if cover else [], cover_url=cover.group(1) if cover else "")


#: 采集任务问社区来源的顺序。AVBase 与 JavBus 各一次请求，javdb 两次且配额紧，排在最后。
COMMUNITY_SOURCES = (("avbase", avbase_work), ("javbus", javbus_work), ("javdb", javdb_work))


def community_sources_for(code: str, *hints: str, route=None):
    """这个番号问社区里的哪几家，顺序同这个番号的来源链。

    成员与顺序的真相在 `metadata_routes`：有码与素人问 AVBase、JavBus 与 javdb，
    FC2 的商品号只问 javdb，韩国 MIB 一家都不问。`route` 是调用方已经算好的那一档成员
    （算它要本机路径与厂牌证据，这里手上没有），给了就直接用。

    FC2 只问 javdb 的依据：2026-09-22 清点本机攒下的 1213 份来源证据，AVBase 那 86 份、
    JavBus 那 37 份全是厂牌番号，对 FC2 番号一份都没给过，javdb 则给了 166 份。问了只是
    各撞一次空搜索，白花两家的配额，还多两次被 Cloudflare 记上的机会。

    省不出时间是预料之中的：`HostLimiter` 等的是「距上次满 5 秒」，这两家的往返本来就落在
    等 javdb 的窗口里。一轮采集的长短由 javdb 的请求数乘 5 秒定死，这里改的是请求次数。
    """
    from .metadata_routes import community_route
    members = community_route(code, *hints) if route is None else tuple(route)
    return tuple(entry for entry in COMMUNITY_SOURCES if entry[0] in members)


def origin_of(url: str) -> str:
    host = hostname_of(url)
    return next((name for name, domains in IMAGE_ORIGINS if host_under(host, domains)), host)


def _candidate(url: str) -> Candidate:
    origin = origin_of(url)
    if origin in ORIGIN_REFERERS:
        return Candidate(hostname_of(url), url, ORIGIN_REFERERS[origin])
    return candidate_for(url)


@dataclass(frozen=True)
class Picture:
    candidate: Candidate
    size: tuple[int, int]
    data: bytes
    fingerprint: int

    @property
    def origin(self) -> str:
        return origin_of(self.candidate.url)

    @property
    def pixels(self) -> int:
        return self.size[0] * self.size[1]


def fingerprint(image: Image.Image) -> int:
    """dHash：缩到 9×8 灰度，逐行比较相邻像素。重压缩与缩放不改它，换一张图就变。"""
    small = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    bits = 0
    for row in range(8):
        for column in range(8):
            bits = bits << 1 | (pixels[row * 9 + column] > pixels[row * 9 + column + 1])
    return bits


def picture(candidate: Candidate, data: bytes) -> Picture:
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        return Picture(candidate, image.size, data, fingerprint(image))


def same_picture(one: Picture, other: Picture) -> bool:
    ratio, other_ratio = one.size[0] / one.size[1], other.size[0] / other.size[1]
    return (abs(ratio - other_ratio) <= ASPECT_TOLERANCE * ratio
            and bin(one.fingerprint ^ other.fingerprint).count("1") <= HASH_DISTANCE)


def _pictures(transport, urls: dict[str, Candidate], reference, *, deadline: float | None) -> list[Picture]:
    """官方小图（有的话）加上社区来源里下载得到、宽度够小图门槛的图。"""
    pool = [picture(reference[0], reference[2])] if reference is not None else []
    for url, candidate in urls.items():
        if reference is not None and url == reference[0].url:
            continue
        try:
            found = picture(candidate, _fetch(transport, url, referer=candidate.referer,
                                              limit=IMAGE_LIMIT, deadline=deadline))
        except (NotFound, Unavailable, SourcePaused, httpx.TransportError, OSError, ValueError,
                Image.DecompressionBombError):
            continue
        if found.size[0] >= SMALL_MIN_WIDTH:
            pool.append(found)
    return pool


def _unverified(pool: list[Picture], downloaded: bool) -> tuple[Candidate, tuple[int, int], bytes, tuple[str, ...]]:
    """没有两个图源对得上时的退路：图全出自一个图源就取最大那张，印证图源留空。"""
    if not downloaded:
        raise Unavailable("社区来源的封面下载失败")
    origins = sorted({one.origin for one in pool})
    if len(origins) > 1:
        raise Unavailable(f"{'、'.join(origins)} 给的封面不是同一张图，无法互相印证")
    largest = max(pool, key=lambda one: one.pixels)
    return largest.candidate, largest.size, largest.data, ()


def verified_cover(transport, code: str, works: list[tuple[str, dict]], *,
                   reference: tuple[Candidate, tuple[int, int], bytes] | None = None,
                   deadline: float | None = None) -> tuple[Candidate, tuple[int, int], bytes, tuple[str, ...]]:
    """社区来源给的封面里，至少两个图源对得上的最大那张；返回值末尾是参与印证的图源。

    `reference` 是官方渠道取到的小图，它也算一个图源：javdb 的大图和 DMM 的小图是同一张
    时，大图就有了官方印证。没有第二个图源可比时按 `_unverified` 取图，末尾为空。
    """
    urls = {url: _candidate(url) for _source, payload in works for url in payload.get("cover_urls") or []}
    if not urls:
        raise NotFound("社区来源没有这部片的封面")
    pool = _pictures(transport, urls, reference, deadline=deadline)
    best = None
    for one in pool:
        origins = {other.origin for other in pool if same_picture(one, other)}
        if len(origins) >= 2 and (best is None or one.pixels > best[0].pixels):
            best = (one, tuple(sorted(origins)))
    if best is None:
        return _unverified(pool, downloaded=len(pool) > (reference is not None))
    return best[0].candidate, best[0].size, best[0].data, best[1]
