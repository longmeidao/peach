"""采集任务的社区来源：AVBase、JavBus 与 javdb 三家问哪几家、按什么顺序，以及社区封面的互相比对。

官方渠道（r18.dev、DMM CDN、MGS、Prestige）落空时才问这三家，决策见 ADR-0030 与 ADR-0032。
三家各是 `peach.sources` 契约下的一个站（`sources/avbase.py`、`sources/javbus.py`、`sources/javdb.py`）：
取页、解析、防封间隔、Cookie 与页面上限都在那里，`LibraryMetadataProvider.community` 与
`scripts/scrape_codes.py` 按 `SITE_SOURCES` 取站。几家的值常有出入：ABW-358 在 javdb 上发行日期是
MGS 的 5/23、标题带 MGS 附注、演员里有男优，所以社区来源的资料一律要两家一致才免复核。

封面比对用 dHash：两张图宽高比相差不超过 4%、64 位指纹相差不超过 10 位就算同一张。
同一张图出现在两个不同的图源（DMM、DUGA、MGS、JavBus、javdb 各算一个）就算印证；官方渠道
只取到小图时，那张小图也参加比对。可用的图全出自一个图源、没有别家可比时，取其中最大的
那张，印证图源留空（ADR-0032）；两个图源各给了图却对不上，是有证据的冲突，不用。
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import httpx
from PIL import Image

from .jav_cover_fetch import (SMALL_MIN_WIDTH, Candidate, NotFound, Unavailable, _fetch, candidate_for,
                              is_cross_product_cover)
from .scraping_access import SourcePaused
from .scripting import host_under, hostname_of
from .sources import AVBASE, JAVBUS, JAVDB

IMAGE_LIMIT = 16 * 1024 * 1024

#: 图源按店铺算，不按主机名：`pics.dmm.co.jp` 与 `awsimgsrc.dmm.co.jp` 是同一家的两条路径。
IMAGE_ORIGINS = (("dmm", ("dmm.co.jp", "dmm.com")), ("duga", ("duga.jp",)),
                 ("mgstage", ("mgstage.com",)), (JAVBUS.name, JAVBUS.domains), (JAVDB.name, JAVDB.domains))
#: 社区站自己的图要带站内 Referer；店铺的图按 `candidate_for` 取官方 Referer。
ORIGIN_REFERERS = {JAVBUS.name: JAVBUS.referer, JAVDB.name: JAVDB.referer}
ASPECT_TOLERANCE = 0.04
HASH_DISTANCE = 10

#: 采集任务问社区来源的顺序。AVBase 与 JavBus 各一次请求，javdb 两次且配额紧，排在最后。
COMMUNITY_SOURCES = (AVBASE.name, JAVBUS.name, JAVDB.name)


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
    return tuple(name for name in COMMUNITY_SOURCES if name in members)


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
    """下载到的一张图。动图不算封面：JavArchive 的图床给 FC2 存的常是 GIF 预览动画，
    落进 `.jpg` 之后卡片就一直在动。"""
    with Image.open(io.BytesIO(data)) as image:
        if getattr(image, "is_animated", False):
            raise ValueError(f"{candidate.url} 是动图")
        image.load()
        return Picture(candidate, image.size, data, fingerprint(image))


def same_picture(one: Picture, other: Picture) -> bool:
    ratio, other_ratio = one.size[0] / one.size[1], other.size[0] / other.size[1]
    return (abs(ratio - other_ratio) <= ASPECT_TOLERANCE * ratio
            and bin(one.fingerprint ^ other.fingerprint).count("1") <= HASH_DISTANCE)


def _pictures(transport, urls: dict[str, Candidate], reference, *,
              deadline: float | None) -> tuple[list[Picture], int]:
    """官方小图（有的话）加上社区来源里下载得到、宽度够小图门槛的静态图；再报下载到了几张。

    下载到了却不能用（动图、太窄）和没下载到是两回事：前者再问一遍还是这几张。
    """
    pool = [picture(reference[0], reference[2])] if reference is not None else []
    fetched = 0
    for url, candidate in urls.items():
        if reference is not None and url == reference[0].url:
            continue
        try:
            data = _fetch(transport, url, referer=candidate.referer, limit=IMAGE_LIMIT, deadline=deadline)
        except (NotFound, Unavailable, SourcePaused, httpx.TransportError, OSError):
            continue
        fetched += 1
        try:
            found = picture(candidate, data)
        except (OSError, ValueError, Image.DecompressionBombError):
            continue
        if found.size[0] >= SMALL_MIN_WIDTH:
            pool.append(found)
    return pool, fetched


def _unverified(pool: list[Picture], usable: int,
                fetched: int) -> tuple[Candidate, tuple[int, int], bytes, tuple[str, ...]]:
    """没有两个图源对得上时的退路：图全出自一个图源就取最大那张，印证图源留空。

    `usable` 是池子里社区来源那几张，不算官方小图。"""
    if not usable:
        if fetched:
            raise NotFound("社区来源给的封面都是动图或太小")
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
    urls = {url: _candidate(url) for _source, payload in works for url in payload.get("cover_urls") or []
            if not is_cross_product_cover(code, url)}
    if not urls:
        raise NotFound("社区来源没有这部片的封面")
    pool, fetched = _pictures(transport, urls, reference, deadline=deadline)
    best = None
    for one in pool:
        origins = {other.origin for other in pool if same_picture(one, other)}
        if len(origins) >= 2 and (best is None or one.pixels > best[0].pixels):
            best = (one, tuple(sorted(origins)))
    if best is None:
        return _unverified(pool, len(pool) - (reference is not None), fetched)
    return best[0].candidate, best[0].size, best[0].data, best[1]
