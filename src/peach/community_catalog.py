"""采集任务的社区来源：AVBase 与 javdb 按番号取作品资料和封面，封面要互相比对才用。

官方渠道（r18.dev、DMM CDN、MGS、Prestige）落空时才问这两家，决策见 ADR-0030。

**AVBase**（2026-09-14 实测）：`/works?q=<番号>` 是 Next.js 页，`__NEXT_DATA__` 里
`props.pageProps.works[]` 就是命中的作品，每部带 `work_id`、日文 `title`、`actors[]`，
以及它在各家店铺的商品 `products[]`（`source` 为 `fanza`、`duga` 等，各自给
`image_url`、`maker`、`label`、`series`、`date`、`iteminfo.director`）。一次请求就够，
不必再进作品页。商品里可能混着收录这段内容的合集（素人系常见），合集的标题和番号
都对不上本作，按这两条筛掉。

**javdb**：搜索页 `/search?q=<番号>&f=all` 的结果卡片带番号，番号一致的那张进详情页；
详情页 `?locale=zh` 下面板字段是 `番號`、`日期`、`片商`、`發行`、`系列`、`導演`、`演員`，
演员里女优带 `actor-female`。它按出口 IP 计配额，限速与封禁的处理在 `scraping_access`
和调用方的主机间隔里，这里只管解析。两家的值常有出入：ABW-358 在 javdb 上发行日期是
MGS 的 5/23、标题带 MGS 附注、演员里有男优，所以社区来源的资料一律要两家一致才免复核。

封面比对用 dHash：两张图宽高比相差不超过 4%、64 位指纹相差不超过 10 位就算同一张。
同一张图要出现在两个不同的图源（DMM、DUGA、MGS、javdb 各算一个）才采用；官方渠道
只取到小图时，那张小图也参加比对。
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
JAVDB_BASE = "https://javdb.com"
JAVDB_SEARCH = JAVDB_BASE + "/search?q={code}&f=all"
PAGE_LIMIT = 4 * 1024 * 1024
IMAGE_LIMIT = 16 * 1024 * 1024

#: 同一部作品在多家店铺上架时，资料先取 FANZA 那条：它与 r18.dev 同源，写法和账本最接近。
AVBASE_PRODUCT_ORDER = ("fanza", "mgs", "duga")
#: 图源按店铺算，不按主机名：`pics.dmm.co.jp` 与 `awsimgsrc.dmm.co.jp` 是同一家的两条路径。
IMAGE_ORIGINS = (("dmm", ("dmm.co.jp", "dmm.com")), ("duga", ("duga.jp",)),
                 ("mgstage", ("mgstage.com",)), ("javdb", ("jdbstatic.com", "jdbimgs.com", "javdb.com")))
ASPECT_TOLERANCE = 0.04
HASH_DISTANCE = 10

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
_AVBASE_DATE = re.compile(r"^[A-Za-z]{3} ([A-Za-z]{3}) (\d{1,2}) (\d{4})")
_MONTHS = {name: index for index, name in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
_JAVDB_BOX = re.compile(r'<a href="(/v/[A-Za-z0-9]+)" class="box" title="[^"]*">.*?<strong>([^<]+)</strong>', re.S)
_JAVDB_PANEL = re.compile(r'<div class="panel-block[^"]*">\s*<strong>([^<:：]+)[:：]</strong>\s*(?:&nbsp;)?\s*'
                          r'<span class="value">(.*?)</span>', re.S)
_JAVDB_TITLE = re.compile(r'<strong class="current-title">([^<]*)</strong>')
_JAVDB_COVER = re.compile(r'<img src="(https://[^"]+)" class="video-cover"')
_JAVDB_ACTRESS = re.compile(r'<a[^>]*class="actor-female"[^>]*>([^<]+)</a>')
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


def _own_product(code: str, work: dict, product: dict) -> bool:
    """这条商品卖的是本作，不是收录本作的合集。"""
    if str(product.get("title") or "").strip() == str(work.get("title") or "").strip():
        return True
    return identifies_code(code, {"content_id": product.get("product_id")})


def _avbase_products(code: str, work: dict) -> list[dict]:
    """本作自己的商品条目，按 `AVBASE_PRODUCT_ORDER` 排。"""
    rank = {source: index for index, source in enumerate(AVBASE_PRODUCT_ORDER)}
    return sorted((product for product in work.get("products") or []
                   if isinstance(product, dict) and _own_product(code, work, product)),
                  key=lambda product: rank.get(product.get("source"), len(rank)))


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
                title=str(work.get("title") or "").strip(),
                actresses=[{"japanese_name": _named(actor)} for actor in work.get("actors") or [] if _named(actor)],
                maker=first(lambda product: _named(product.get("maker"))),
                label=first(lambda product: _named(product.get("label"))),
                series=first(lambda product: _named(product.get("series"))),
                director=first(info("director")),
                release_date=_avbase_date(products[0].get("date") if products else work.get("min_date")),
                cover_urls=covers, cover_url=covers[0] if covers else "")


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
                actresses=[{"japanese_name": clean(name)} for name in _JAVDB_ACTRESS.findall(panel.get("演員", ""))],
                maker=_maker_writing(clean(panel.get("片商", ""))), label=clean(panel.get("發行", "")),
                series=clean(panel.get("系列", "")), director=clean(panel.get("導演", "")),
                release_date=clean(panel.get("日期", "")), runtime=int(runtime.group()) if runtime else None,
                cover_urls=[cover.group(1)] if cover else [], cover_url=cover.group(1) if cover else "")


#: 采集任务问社区来源的顺序。AVBase 一次请求，javdb 两次且配额紧，排在后面。
COMMUNITY_SOURCES = (("avbase", avbase_work), ("javdb", javdb_work))


@dataclass(frozen=True)
class Picture:
    candidate: Candidate
    size: tuple[int, int]
    data: bytes
    fingerprint: int

    @property
    def origin(self) -> str:
        host = hostname_of(self.candidate.url)
        return next((name for name, domains in IMAGE_ORIGINS if host_under(host, domains)), host)

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


def verified_cover(transport, code: str, works: list[tuple[str, dict]], *,
                   reference: tuple[Candidate, tuple[int, int], bytes] | None = None,
                   deadline: float | None = None) -> tuple[Candidate, tuple[int, int], bytes, tuple[str, ...]]:
    """社区来源给的封面里，至少两个图源对得上的最大那张；返回值末尾是参与印证的图源。

    `reference` 是官方渠道取到的小图，它也算一个图源：javdb 的大图和 DMM 的小图是同一张
    时，大图就有了官方印证。
    """
    urls: dict[str, Candidate] = {}
    for source, payload in works:
        for url in payload.get("cover_urls") or []:
            urls.setdefault(url, Candidate(hostname_of(url), url, JAVDB_BASE + "/") if source == "javdb"
                            else candidate_for(url))
    if not urls:
        raise NotFound("社区来源没有这部片的封面")
    pool = []
    if reference is not None:
        pool.append(picture(reference[0], reference[2]))
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
    best = None
    for one in pool:
        origins = {other.origin for other in pool if same_picture(one, other)}
        if len(origins) >= 2 and (best is None or one.pixels > best[0].pixels):
            best = (one, tuple(sorted(origins)))
    if best is None:
        raise Unavailable("社区来源的封面没有第二个图源能对上" if len(pool) > (reference is not None)
                          else "社区来源的封面下载失败")
    return best[0].candidate, best[0].size, best[0].data, best[1]
