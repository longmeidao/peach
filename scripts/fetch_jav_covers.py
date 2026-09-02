#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""按番号抓官方封套：把所有候选量一遍，留像素最多的那张。

**不用固定优先级链**，因为实测证明没有哪个源恒定最好：

    GYAN-017   awsimgsrc 2184x1464   有数字版，DMM 自己的高清路径最好
    ABW-232    duga      1000x674    没有数字版，awsimgsrc 四种写法全 404
    PPT-018    pics.dmm   800x539    只有低清

同一个 DMM 有两条路径，差 7.4 倍像素——之前一直用的是低清那条：

    低清  pics.dmm.co.jp/mono/movie/adult/<cid>/<cid>pl.jpg            800x539
    高清  awsimgsrc.dmm.co.jp/pics_dig/digital/video/<cid>/<cid>pl.jpg 2184x1464

候选不是固定优先级，而是汇总后量像素：

- 已保存的 Javinizer-Go 原始证据，离线复用 cover URL 与 content_id；
- r18.dev 官方 DMM jacket（本地没有成功快照时才联网补）；
- DMM 新旧 awsimgsrc CDN 的 digital/video、digital/amateur、mono/movie 路径；
- 有 Prestige 厂牌证据时，直连 Prestige API 与 MGS EnlargeImage；
- 上轮成功日志里的原 URL，保住已经发现但当前无法重新检索的 DUGA 等官方图。

AVBase 已返回 Cloudflare 验证页，不再进入批量流程，也不尝试绕过。DUGA 批量搜索 API
需要代理店应用 ID，未配置前只复用成功日志中已经取得的精确图片 URL。

两条番号改写规则，都由实测得出：

- cid 数字段必须补到 5 位。`waaa415` 404，`waaa00415` 命中 2184x1468。
- 素人系要去掉三位厂牌前缀。`278GYAN-017` 查不到，`GYAN-017` 能查到。

为省流量，先用 Range 只取前 64 KiB 量尺寸，只有胜出的那张才整张下载。

存原图不裁：4:3 与 16:9 两种版式在界面上靠 `object-fit` / `object-position` 取景，
切版式零成本也不重新下载。官方那张独立正封 `ps.jpg` 只有 147x200，比裁出来的还小。
"""
from __future__ import annotations

import argparse
import io
import json
import re
import time
import urllib.parse
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image, UnidentifiedImageError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.review_csv import ENCODING, read_rows, write_rows
from peach.scripting import USER_AGENT, open_readonly
from peach.config import COVER_DIR, DATABASE_PATH, GENERATED_DIR, SOURCES_DIR
from peach.http import HttpRequest, HttpTransport, HttpxTransport
from peach.jobs import DiskGuard, JobPolicyError
from peach.platform import system_volume
from peach.catalog_rules import is_jav_code, normalise_code_key

AWS_LEGACY_DIGITAL = (
    "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/{cid}/{cid}pl.jpg"
)
AWS_MODERN = "https://awsimgsrc.dmm.com/dig/{kind}/{cid}/{cid}pl.jpg"
AWS_LEGACY = "https://awsimgsrc.dmm.co.jp/pics_dig/{kind}/{cid}/{cid}pl.jpg"
R18_DETAIL = "https://r18.dev/videos/vod/movies/detail/-/dvd_id={code}/json"
MGS_DETAIL = "https://www.mgstage.com/product/product_detail/{code}/"
PRESTIGE_SEARCH = "https://www.prestige-av.com/api/search"
PRESTIGE_PRODUCT = "https://www.prestige-av.com/api/product/{uuid}"
PRESTIGE_MEDIA = "https://www.prestige-av.com/api/media/{path}"
DEFAULT_METADATA_ROOT = SOURCES_DIR / "metadata" / "javinizer-go"
DEFAULT_FC2_METADATA_LOG = GENERATED_DIR / "fc2-candidate-log.csv"

#: 低于这个宽度的是缩略图或占位图，不当封套。实测最低的正片封套是 800 宽。
MIN_WIDTH = 700
#: 量尺寸只需要 JPEG 头部，别把整张 1 MB 的图拉下来。
PROBE_BYTES = 64 * 1024
# 瞬时 TLS EOF / 连接重置不能落成“官方没有封面”。按项目外网退避规则重试，
# 只有 2/4/6/8 秒四次重试全部失败后，才把网络异常交给逐条日志记录。
NETWORK_RETRY_DELAYS = (2, 4, 6, 8)
#: 页面与上游证据里可能混着剧照与缩略图，按文件名排除。
THUMBNAIL = re.compile(r"(thumb|small|icon|/ts/|-s\d|_s\.)", re.I)
FC2_HIRES = re.compile(r"https://contents-thumbnail\d*\.fc2\.com/w(?:7\d\d|[89]\d\d|\d{4,})/", re.I)
IMAGE_URL = re.compile(r"https?://[^\"'\\ )]+?\.(?:jpg|jpeg|png|webp)")


@dataclass(frozen=True)
class Candidate:
    source: str
    url: str
    referer: str = "https://www.dmm.co.jp/"


@dataclass(frozen=True)
class MetadataEvidence:
    candidates: tuple[Candidate, ...] = ()
    makers: frozenset[str] = frozenset()
    sources: frozenset[str] = frozenset()


class Unavailable(RuntimeError):
    pass


class HostLimitedTransport:
    """把请求间隔按主机分别计算；不同官方站点互不阻塞。"""

    def __init__(self, inner: HttpxTransport, interval: float, *,
                 clock=time.monotonic, sleeper=time.sleep) -> None:
        self.inner = inner
        self.interval = max(0.0, interval)
        self.clock = clock
        self.sleeper = sleeper
        self.next_request: dict[str, float] = {}

    def __call__(self, request: HttpRequest, timeout: float, limit: int):
        host = urlparse(request.url).netloc.lower()
        now = self.clock()
        wait = self.next_request.get(host, now) - now
        if wait > 0:
            self.sleeper(wait)
            now = self.clock()
        self.next_request[host] = now + self.interval
        return self.inner(request, timeout, limit)

    def renew(self) -> None:
        self.inner.close()
        self.inner = HttpxTransport()

    def close(self) -> None:
        self.inner.close()


class _MGSDetailParser(HTMLParser):
    """只读取 MGS 的放大图链接；列表缩略图和剧照不进入候选。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        url = None
        if tag.lower() == "a" and values.get("id") == "EnlargeImage":
            url = values.get("href")
        elif tag.lower() == "a" and "link_magnify" in (values.get("class") or "").split():
            url = values.get("href")
        elif tag.lower() == "img" and any(
                token in (values.get("src") or "").lower()
                for token in ("jacket", "cover")):
            url = values.get("src") or values.get("data-src")
            if url:
                url = url.replace("ps.", "pl.", 1)
        if url and (IMAGE_URL.fullmatch(url)
                    or re.search(r"\.(?:jpg|jpeg|png|webp)(?:\?.*)?$", url, re.I)):
            self.urls.append(url)


def _fetch(transport: HttpTransport, url: str, *, referer: str,
           limit: int, ranged: bool = False,
           extra_headers: dict[str, str] | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Referer": referer,
               "Accept-Language": "ja,en;q=0.9"}
    if extra_headers:
        headers.update(extra_headers)
    if ranged:
        headers["Range"] = f"bytes=0-{PROBE_BYTES - 1}"
    request = HttpRequest("GET", url, headers)
    for attempt in range(len(NETWORK_RETRY_DELAYS) + 1):
        try:
            response = transport(request, 30, limit)
            break
        except httpx.TransportError:
            if attempt == len(NETWORK_RETRY_DELAYS):
                raise
            time.sleep(NETWORK_RETRY_DELAYS[attempt])
    if response.status not in (200, 206):
        raise Unavailable(f"HTTP {response.status}")
    return response.body


def code_variants(code: str) -> list[str]:
    """素人系番号带三位厂牌前缀，去掉才查得到：`278GYAN-017` -> `GYAN-017`。"""
    value = normalise_code_key(code)
    out = [value]
    stripped = re.sub(r"^\d{3}(?=[A-Z])", "", value)
    if stripped != value:
        out.append(stripped)
    return out


def cid_variants(content_id: str) -> list[str]:
    """数字段补到 5 位是必须的；带厂牌数字前缀的多半没有数字版，但仍试一次。"""
    cid = (content_id or "").strip().lower()
    if not cid:
        return []
    out = [cid]
    shape = re.match(r"^(\d{2,4})?([a-z]+)(\d+)$", cid)
    if shape:
        letters, digits = shape.group(2), shape.group(3)
        out.append(f"{letters}{int(digits):05d}")
        out.append(f"{letters}{digits}")
    seen: set[str] = set()
    return [c for c in out if not (c in seen or seen.add(c))]


def _referer_for(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "mgstage.com" in host:
        return "https://www.mgstage.com/"
    if "prestige-av.com" in host:
        return "https://www.prestige-av.com/"
    if "duga.jp" in host:
        return "https://duga.jp/"
    return "https://www.dmm.co.jp/"


def candidate_for(url: str) -> Candidate:
    return Candidate(urlparse(url).netloc.lower(), url, _referer_for(url))


def fc2_cover_candidates(path: Path | None) -> dict[str, Candidate]:
    """Reuse FC2CMADB article evidence, upgrading its listing thumb to measured w1200."""
    if path is None or not path.is_file():
        return {}
    found = {}
    for row in read_rows(path):
        url = re.sub(r"(/w)\d+(/)", r"\g<1>1200\2", str(row.get("cover_url") or ""), count=1)
        code = normalise_code_key(str(row.get("code") or ""))
        if (row.get("result") == "取得" and not row.get("is_collection")
                and code.startswith("FC2-PPV-") and IMAGE_URL.fullmatch(url)):
            found[code] = Candidate(urlparse(url).netloc.lower(), url, "https://fc2cmadb.com/")
    return found


def _unique_candidates(candidates: list[Candidate]) -> list[Candidate]:
    seen: set[str] = set()
    return [candidate for candidate in candidates
            if candidate.url and not (candidate.url in seen or seen.add(candidate.url))]


def dmm_cdn_images(url: str) -> list[Candidate]:
    """按 Javinizer-Go 当前已验证映射生成 DMM 新旧 CDN 候选。

    主机名和路径不能当清晰度：同一 CID 的 legacy、modern、原始 URL 都要量尺寸。
    """
    clean = (url or "").split("?", 1)[0]
    parsed = urlparse(clean)
    match = re.search(
        r"/(?:pics_dig/|dig/)?(?P<kind>digital/(?:video|amateur)|mono/movie)"
        r"(?:/adult)?/(?P<cid>[^/]+)/",
        parsed.path,
        re.I,
    )
    candidates = [candidate_for(clean)] if IMAGE_URL.fullmatch(clean) else []
    if not match:
        return candidates
    kind = match.group("kind").lower()
    cid = match.group("cid").lower()
    candidates.extend([
        candidate_for(AWS_MODERN.format(kind=kind, cid=cid)),
        candidate_for(AWS_LEGACY.format(kind=kind, cid=cid)),
    ])
    return _unique_candidates(candidates)


def content_id_images(content_id: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    for cid in cid_variants(content_id):
        candidates.extend([
            candidate_for(AWS_MODERN.format(kind="digital/video", cid=cid)),
            candidate_for(AWS_LEGACY_DIGITAL.format(cid=cid)),
        ])
    return _unique_candidates(candidates)


def cached_metadata(metadata_root: Path | None, code: str) -> MetadataEvidence:
    """复用已落盘的 Javinizer 原始快照，不把网络缓存伪装成实时查询。"""
    if metadata_root is None:
        return MetadataEvidence()
    candidates: list[Candidate] = []
    makers: set[str] = set()
    sources: set[str] = set()
    for variant in code_variants(code):
        folder = metadata_root / variant
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            try:
                wrapper = json.loads(path.read_text(encoding=ENCODING))
            except (OSError, ValueError):
                continue
            result = wrapper.get("result")
            if not isinstance(result, dict):
                continue
            source = str(result.get("source") or wrapper.get("source") or path.stem)
            sources.add(source.lower())
            for value in (result.get("maker"), result.get("label")):
                if isinstance(value, str) and value.strip():
                    makers.add(value.strip().lower())
            cover_url = result.get("cover_url")
            if isinstance(cover_url, str) and IMAGE_URL.fullmatch(cover_url.strip()):
                candidates.extend(dmm_cdn_images(cover_url.strip()))
            candidates.extend(content_id_images(str(result.get("content_id") or "")))
    return MetadataEvidence(
        tuple(_unique_candidates(candidates)), frozenset(makers), frozenset(sources),
    )


def logged_success_evidence(
        rows: list[dict], code: str,
        ) -> tuple[Candidate, tuple[int, int]] | None:
    """复用历史精确 URL 与已量尺寸；DUGA 等无需重复探同一张图。"""
    for row in reversed(rows):
        if (normalise_code_key(str(row.get("code") or "")) == code
                and row.get("result") == "取得"
                and isinstance(row.get("url"), str)
                and IMAGE_URL.fullmatch(str(row["url"]))):
            try:
                size = (int(row.get("width") or 0), int(row.get("height") or 0))
            except (TypeError, ValueError):
                size = (0, 0)
            return candidate_for(str(row["url"])), size
    return None


def logged_success_candidate(rows: list[dict], code: str) -> Candidate | None:
    """兼容只需要历史 URL 的调用方。"""
    evidence = logged_success_evidence(rows, code)
    return evidence[0] if evidence is not None else None


def _is_prestige(evidence: MetadataEvidence) -> bool:
    return any("prestige" in value or "プレステージ" in value
               for value in evidence.makers)


def r18_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """读取 r18 返回的官方封套，并保留旧数字版高清 URL 探测。

    `content_id` 不是稳定的数字版路径。Prestige 的 ABW 系列会返回
    `118abw232`，对应 `pics.dmm.co.jp/mono/.../118abw232pl.jpg`；把它补零后
    拼到 `awsimgsrc.../digital/video` 只会得到 404。r18 已在
    `images.jacket_image` 给出官方原图 URL，必须优先把这个证据加入候选。
    """
    for variant in code_variants(code):
        try:
            payload = json.loads(_fetch(
                transport, R18_DETAIL.format(code=urllib.parse.quote(variant)),
                referer="https://r18.dev/", limit=2 * 1024 * 1024,
            ).decode("utf-8", "ignore"))
        except (Unavailable, ValueError, httpx.TransportError):
            continue
        found: list[Candidate] = []
        jacket = ((payload.get("images") or {}).get("jacket_image") or {})
        if isinstance(jacket, dict):
            for raw_url in jacket.values():
                url = raw_url.strip() if isinstance(raw_url, str) else ""
                if url and IMAGE_URL.fullmatch(url) and not THUMBNAIL.search(url):
                    found.extend(dmm_cdn_images(url))
        cid = str(payload.get("content_id") or "")
        found.extend(content_id_images(cid))
        return _unique_candidates(found)
    return []


def mgstage_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """直取 MGS 商品页 EnlargeImage；年龄确认只用公开 cookie，不绕挑战。"""
    for variant in code_variants(code):
        try:
            page = _fetch(
                transport,
                MGS_DETAIL.format(code=urllib.parse.quote(variant)),
                referer="https://www.mgstage.com/",
                limit=4 * 1024 * 1024,
                extra_headers={"Cookie": "adc=1"},
            ).decode("utf-8", "ignore")
        except (Unavailable, httpx.TransportError):
            continue
        parser = _MGSDetailParser()
        parser.feed(page)
        found: list[Candidate] = []
        for url in parser.urls:
            absolute = urllib.parse.urljoin("https://www.mgstage.com/", url)
            if THUMBNAIL.search(absolute):
                continue
            found.append(candidate_for(absolute))
        if found:
            return _unique_candidates(found)
    return []


def prestige_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """按 MDCX 固定 revision 的公开 API 模型直取 Prestige packageImage。"""
    query = urllib.parse.urlencode({
        "isEnabledQuery": "true",
        "searchText": code,
        "isEnableAggregation": "false",
        "release": "false",
        "reservation": "false",
        "soldOut": "false",
        "from": 0,
        "aggregationTermsSize": 0,
        "size": 20,
    })
    try:
        payload = json.loads(_fetch(
            transport, f"{PRESTIGE_SEARCH}?{query}",
            referer="https://www.prestige-av.com/", limit=4 * 1024 * 1024,
        ).decode("utf-8", "ignore"))
    except (Unavailable, ValueError, httpx.TransportError):
        return []
    hits = (((payload.get("hits") or {}).get("hits")) or [])
    exact: list[str] = []
    fallback: list[str] = []
    for hit in hits:
        source = hit.get("_source") if isinstance(hit, dict) else None
        if not isinstance(source, dict):
            continue
        item_id = normalise_code_key(str(source.get("deliveryItemId") or ""))
        uuid = str(source.get("productUuid") or "").strip()
        if not uuid:
            continue
        if item_id == normalise_code_key(code):
            exact.append(uuid)
        elif str(source.get("deliveryItemId") or "").upper().endswith(code.upper()):
            fallback.append(uuid)
    uuids = list(dict.fromkeys(exact or fallback))
    for uuid in uuids:
        try:
            product = json.loads(_fetch(
                transport, PRESTIGE_PRODUCT.format(uuid=urllib.parse.quote(uuid)),
                referer="https://www.prestige-av.com/", limit=4 * 1024 * 1024,
            ).decode("utf-8", "ignore"))
        except (Unavailable, ValueError, httpx.TransportError):
            continue
        package = product.get("packageImage") or {}
        path = package.get("path") if isinstance(package, dict) else ""
        if isinstance(path, str) and path.strip():
            url = PRESTIGE_MEDIA.format(path=path.strip().lstrip("/"))
            if IMAGE_URL.fullmatch(url):
                return [candidate_for(url)]
    return []


def prestige_group_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """Prestige 官方 API 命中后不再等待较小的 MGS 图；未命中才回退 MGS。"""
    official = prestige_images(transport, code)
    return official if official else mgstage_images(transport, code)


def probe_size(transport: HttpTransport, candidate: Candidate) -> tuple[int, int]:
    head = _fetch(transport, candidate.url, referer=candidate.referer,
                  limit=PROBE_BYTES * 2, ranged=True)
    return Image.open(io.BytesIO(head)).size


def best_cover(transport: HttpTransport, code: str, delay: float, *,
               metadata_root: Path | None = None,
               prior_candidates: tuple[Candidate, ...] = (),
               known_sizes: dict[str, tuple[int, int]] | None = None,
               minimum_pixels: int = 0,
               ) -> tuple[Candidate, tuple[int, int], bytes]:
    # 来源一律记主机名。缓存、构造路径和官方页常指向同一个主机，记成多个名字
    # 会让覆盖率统计凭空多出「渠道」。
    evidence = cached_metadata(metadata_root, code)
    candidates = list(prior_candidates) + list(evidence.candidates)
    is_fc2 = code.upper().startswith("FC2-PPV-")
    # 有成功快照时不重复打 r18；失败快照不算证据，仍允许联网刷新。
    if not is_fc2 and "r18dev" not in evidence.sources:
        candidates += r18_images(transport, code)
        time.sleep(delay)
    # MGS 与 Prestige 都是 Prestige 集团的官方供给面。只在本地厂牌证据命中时
    # 查询，避免把全库 960 个番号无差别打到两个站点。
    if not is_fc2 and _is_prestige(evidence):
        candidates += prestige_group_images(transport, code)
        time.sleep(delay)
    elif not is_fc2 and "mgstage" in evidence.sources:
        candidates += mgstage_images(transport, code)
        time.sleep(delay)
    candidates = _unique_candidates([
        candidate for candidate in candidates
        if not THUMBNAIL.search(candidate.url) or FC2_HIRES.match(candidate.url)
    ])
    # 升级模式已在成功日志中量过的精确 URL，若像素不大于当前本地图，就不再
    # 发 Range 请求。其他 URL 和尺寸未知的候选仍完整探测，不改变择优语义。
    known_sizes = known_sizes or {}
    candidates = [
        candidate for candidate in candidates
        if candidate.url not in known_sizes
        or known_sizes[candidate.url][0] * known_sizes[candidate.url][1]
        > minimum_pixels
    ]
    if not candidates:
        raise Unavailable("所有渠道都没有候选")

    measured: list[tuple[int, Candidate, tuple[int, int]]] = []
    for candidate in candidates:
        try:
            width, height = probe_size(transport, candidate)
        except (Unavailable, UnidentifiedImageError, OSError, httpx.TransportError):
            continue
        finally:
            time.sleep(delay)
        if width >= MIN_WIDTH:
            measured.append((width * height, candidate, (width, height)))
    if not measured:
        raise Unavailable("候选都不是可用封套")

    for _pixels, winner, size in sorted(measured, key=lambda item: item[0], reverse=True):
        try:
            data = _fetch(transport, winner.url, referer=winner.referer,
                          limit=16 * 1024 * 1024)
        except (Unavailable, httpx.TransportError):
            continue
        return winner, size, data
    raise Unavailable("可用候选完整下载都失败")


FIELDS = ("code", "result", "source", "width", "height", "kb", "url", "note")


#: 判定为「所有渠道都没有」的落空，续跑时不必重来；连接类失败必须重试。
#: 三态口径：一次超时不等于确认没有，不能靠它把番号永久踢出队列。
TRANSIENT = re.compile(r"(Error|Timeout|SSL|Connect|Proxy|Protocol)", re.I)


def settled_misses(log: Path) -> set[str]:
    """上一轮已经把所有源探完、确认没有封套的番号。

    这类落空是最贵的：每条都要把全部候选源挨个试完才能确定。实测 194 条里
    150 条落空，重探一遍就是好几个小时，而结论不会变。
    """
    rows = logged_rows(log)
    return {str(row.get("code") or "").strip() for row in rows
            if row.get("result") == "未取得"
            and not TRANSIENT.search(str(row.get("note") or ""))
            and str(row.get("code") or "").strip()}


def carried_rows(log: Path, keep: set[str]) -> list[dict]:
    """把这轮跳过的番号的上轮记录原样带进新日志。"""
    if not keep:
        return []
    return [{field: row.get(field, "") for field in FIELDS}
            for row in logged_rows(log)
            if str(row.get("code") or "").strip() in keep]


def logged_rows(log: Path) -> list[dict]:
    if not log.is_file():
        return []
    return read_rows(log)


def restore_logged_successes(transport: HttpTransport, log: Path, root: Path,
                             delay: float = 0.0, guard: DiskGuard | None = None) -> dict:
    """Re-download missing covers from the exact successful URLs already in the audit log.

    This is intentionally narrower than a fresh scrape: it makes no discovery requests,
    preserves the existing audit log and refuses an upstream image whose dimensions changed.
    """
    root.mkdir(parents=True, exist_ok=True)
    restored = skipped = 0
    failed: list[dict[str, str]] = []
    successes = [row for row in logged_rows(log)
                 if row.get("result") == "取得" and row.get("code") and row.get("url")]
    for index, row in enumerate(successes, 1):
        if guard is not None:
            guard.check()
        code = normalise_code_key(str(row["code"]))
        target = root / f"{code}.jpg"
        if target.is_file():
            skipped += 1
            continue
        temporary = target.with_suffix(".restore.tmp")
        try:
            data = _fetch(transport, str(row["url"]), referer=_referer_for(str(row["url"])),
                          limit=16 * 1024 * 1024)
            with Image.open(io.BytesIO(data)) as image:
                size = image.size
                image.verify()
            expected = (int(row["width"]), int(row["height"]))
            if size != expected or size[0] < MIN_WIDTH:
                raise Unavailable(f"尺寸变化：日志 {expected[0]}x{expected[1]}，当前 {size[0]}x{size[1]}")
            temporary.write_bytes(data)
            temporary.replace(target)
            restored += 1
            print(f"[{index}/{len(successes)}] 恢复 {code}  {size[0]}x{size[1]}", flush=True)
        # 与完整抓取同一条长跑边界：单张网络异常降级成失败记录，不能让余下恢复归零；
        # KeyboardInterrupt 等 BaseException 仍会正常中断。
        except Exception as exc:
            failed.append({"code": code, "error": f"{type(exc).__name__}: {exc}"[:120]})
            print(f"[{index}/{len(successes)}] 未恢复 {code}：{type(exc).__name__} {exc}",
                  flush=True)
        finally:
            temporary.unlink(missing_ok=True)
            if delay:
                time.sleep(delay)
    return {"logged": len(successes), "restored": restored, "skipped": skipped,
            "failed": failed}


def pending(database: Path, root: Path, only_shaped: bool,
            location: str | None = None, *, existing: bool = False,
            max_width: int = 0, fc2_only: bool = False) -> list[str]:
    connection = open_readonly(database)
    try:
        location_sql = " AND location=?" if location else ""
        parameters: tuple[object, ...] = (location,) if location else ()
        rows = connection.execute(
            "SELECT code, COUNT(*) FROM asset WHERE medium='video' "
            "AND code IS NOT NULL AND code<>''" + location_sql
            + " GROUP BY code ORDER BY 2 DESC",
            parameters,
        ).fetchall()
    finally:
        connection.close()
    result = []
    for code, _count in rows:
        if fc2_only and not str(code).upper().startswith("FC2"):
            continue
        # 判形态必须看原值。`normalise_code_key` 会补上分隔符，把 `RAIKUN325`
        # （myfans 账号名，241 个文件）改写成 `RAIKUN-325` 并通过形态检查，
        # 于是队列里全是查不到的账号名。判据与 web_contract 共用一份实现。
        if only_shaped and not is_jav_code(str(code)):
            continue
        # FC2 在 r18/avsox/javbus 三源实测零命中（见 HANDOFF），本抓取器用的是
        # 同一批来源。默认跳过 400 个必然落空的请求；`--all-codes` 仍可强制尝试。
        if only_shaped and str(code).upper().startswith("FC2"):
            continue
        key = normalise_code_key(str(code))
        target = root / f"{key}.jpg"
        if existing:
            if not target.is_file():
                continue
            try:
                with Image.open(target) as image:
                    width = image.size[0]
            except (UnidentifiedImageError, OSError):
                width = 0
            if max_width and width > max_width:
                continue
            result.append(key)
        elif not target.is_file():
            result.append(key)
    return result


def audit_state(database: Path, root: Path, log: Path) -> dict[str, object]:
    """只读盘点当前 JAV 封面；用于批次前后使用同一统计口径。"""
    connection = open_readonly(database)
    try:
        raw_codes = [str(row[0]) for row in connection.execute(
            "SELECT DISTINCT code FROM asset WHERE medium='video' "
            "AND code IS NOT NULL AND code<>''"
        )]
    finally:
        connection.close()
    codes = {
        normalise_code_key(code) for code in raw_codes
        if is_jav_code(code) and not code.upper().startswith("FC2")
    }
    dimensions: dict[str, tuple[int, int]] = {}
    invalid: list[str] = []
    for path in sorted(root.glob("*.jpg")) if root.is_dir() else []:
        try:
            with Image.open(path) as image:
                dimensions[path.stem] = image.size
        except (UnidentifiedImageError, OSError):
            invalid.append(path.name)
    widths = {
        "le_800": sum(width <= 800 for width, _height in dimensions.values()),
        "801_999": sum(801 <= width <= 999 for width, _height in dimensions.values()),
        "1000_1199": sum(1000 <= width <= 1199
                         for width, _height in dimensions.values()),
        "ge_1200": sum(width >= 1200 for width, _height in dimensions.values()),
    }
    rows = logged_rows(log)
    return {
        "jav_codes": len(codes),
        "decoded_covers": len(dimensions),
        "missing": len(codes - set(dimensions)),
        "invalid": invalid,
        "width_buckets": widths,
        "log_successes": sum(row.get("result") == "取得" for row in rows),
        "log_misses": sum(row.get("result") == "未取得" for row in rows),
        "settled_misses": len(settled_misses(log)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按番号抓最高清的官方封套")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--out", type=Path, default=COVER_DIR)
    parser.add_argument("--log", type=Path,
                        default=GENERATED_DIR / "cover-fetch-log.csv")
    parser.add_argument(
        "--metadata-root", type=Path, default=DEFAULT_METADATA_ROOT,
        help="Javinizer-Go 原始快照目录；先离线复用成功证据，再补联网来源",
    )
    parser.add_argument("--fc2-metadata-log", type=Path, default=DEFAULT_FC2_METADATA_LOG,
                        help="fc2cmadb 文章封面证据，只对 --fc2-only 生效")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--code", help="只处理一个已归一化番号，用于定点重试")
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--min-free", type=float, default=40.0,
                        help="系统盘最低可用 GiB；运行中每隔一段时间复查")
    parser.add_argument("--disk-check-secs", type=float, default=20.0)
    parser.add_argument("--location",
                        help="只抓指定来源的番号封套，例如 pikpak；封套仍按番号共享")
    parser.add_argument("--retry-misses", action="store_true",
                        help="连上轮确认没有封套的番号也重探一遍")
    parser.add_argument("--restore-successes", action="store_true",
                        help="只按成功日志中的原 URL 恢复缺失封套，不重新探测来源")
    parser.add_argument("--upgrade-existing", action="store_true",
                        help="重探已有封套；只有候选像素更多时才原子替换")
    parser.add_argument("--upgrade-max-width", type=int, default=0,
                        help="升级模式只重探不超过此宽度的已有封套；0 表示全部")
    parser.add_argument("--all-codes", action="store_true",
                        help="连 FC2/日期番号一起试；默认只跑片商与素人形态")
    parser.add_argument("--fc2-only", action="store_true",
                        help="只用 fc2cmadb 已存证据抓 FC2 官方 CDN 封面")
    parser.add_argument("--audit", action="store_true",
                        help="只读输出封面数量、缺失、损坏和尺寸分布，不联网不写文件")
    return parser


def _write_log(path: Path, rows: list[dict]) -> None:
    """每条都落盘：这个任务要跑三四个小时，只在结束时写等于全程看不见进度。"""
    write_rows(path, FIELDS, rows)


def _renew_transport_after_error(transport: HttpTransport,
                                 error: Exception) -> HttpTransport:
    """永久 transport 失败后丢弃连接池，避免后续番号连续 PoolTimeout。"""
    if not isinstance(error, httpx.TransportError):
        return transport
    if isinstance(transport, HostLimitedTransport):
        transport.renew()
        return transport
    transport.close()
    return HttpxTransport()


def _replace_log_row(rows: list[dict], code: str, replacement: dict) -> None:
    """一个番号只保留一条最新成功证据，不扰动其他番号。"""
    rows[:] = [row for row in rows
               if str(row.get("code") or "").strip() != code]
    rows.append({field: replacement.get(field, "") for field in FIELDS})


def run(args: argparse.Namespace) -> int:
    if args.audit:
        print(json.dumps(audit_state(args.db, args.out, args.log),
                         ensure_ascii=False, indent=2))
        return 0
    if args.upgrade_max_width < 0:
        print("[stop] --upgrade-max-width 不能小于 0")
        return 2
    if args.upgrade_max_width and not args.upgrade_existing:
        print("[stop] --upgrade-max-width 只能与 --upgrade-existing 一起使用")
        return 2
    if args.upgrade_existing and args.retry_misses:
        print("[stop] --upgrade-existing 与 --retry-misses 不能同时使用")
        return 2
    if args.restore_successes and args.upgrade_existing:
        print("[stop] --restore-successes 与 --upgrade-existing 不能同时使用")
        return 2
    if args.fc2_only and args.all_codes:
        print("[stop] --fc2-only 与 --all-codes 不能同时使用")
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    guard = DiskGuard(system_volume(), args.min_free, args.disk_check_secs)
    try:
        free_gb = guard.check(force=True)
    except JobPolicyError as exc:
        print(f"[stop] {exc}")
        return exc.exit_code
    print(f"系统盘可用 {free_gb:.1f} GiB，运行期阈值 {args.min_free:.1f} GiB")
    if args.restore_successes:
        transport = HttpxTransport()
        try:
            result = restore_logged_successes(
                transport, args.log, args.out, args.delay, guard=guard,
            )
        except JobPolicyError as exc:
            print(f"[stop] {exc}")
            return exc.exit_code
        finally:
            transport.close()
        print(f"成功日志 {result['logged']}，恢复 {result['restored']}，"
              f"已存在 {result['skipped']}，失败 {len(result['failed'])} → {args.out}")
        return 2 if result["failed"] else 0

    todo = pending(
        args.db, args.out, not args.all_codes and not args.fc2_only, args.location,
        existing=args.upgrade_existing, max_width=args.upgrade_max_width,
        fc2_only=args.fc2_only,
    )
    if args.code:
        wanted = normalise_code_key(args.code)
        todo = [code for code in todo if code == wanted]
    skipped = set()
    if not args.upgrade_existing and not args.retry_misses:
        skipped = settled_misses(args.log) & set(todo)
        todo = [code for code in todo if code not in skipped]
    if args.limit:
        todo = todo[:args.limit]
    selected = set(todo)
    if args.upgrade_existing:
        width_note = (f"，当前宽度不超过 {args.upgrade_max_width}"
                      if args.upgrade_max_width else "")
        print(f"待重探已有封套 {len(todo)} 个{width_note}；只在像素更多时替换")
    else:
        print(f"待抓番号 {len(todo)} 个（已落盘的跳过，"
              f"上轮确认没有的跳过 {len(skipped)} 个，--retry-misses 可重试）")

    transport = HostLimitedTransport(HttpxTransport(), args.delay)
    # 日志是整份重写：这轮只跑 pikpak 或只跑 --limit 时，未选中的旧记录也必须保留；
    # 只删除本轮会重新生成的番号。否则一次来源小批次就会抹掉其他来源的复核证据。
    previous_rows = logged_rows(args.log)
    fc2_candidates = fc2_cover_candidates(args.fc2_metadata_log) if args.fc2_only else {}
    rows: list[dict] = [
        {field: row.get(field, "") for field in FIELDS}
        for row in previous_rows
        if args.upgrade_existing
        or str(row.get("code") or "").strip() not in selected
    ]
    stats = {"ok": 0, "miss": 0, "kept": 0}
    stopped: JobPolicyError | None = None
    try:
        for index, code in enumerate(todo, 1):
            try:
                guard.check()
            except JobPolicyError as exc:
                stopped = exc
                print(f"[stop] {exc}", flush=True)
                break
            try:
                target = args.out / f"{code}.jpg"
                current_size = (0, 0)
                if args.upgrade_existing:
                    try:
                        with Image.open(target) as image:
                            current_size = image.size
                    except (UnidentifiedImageError, OSError):
                        pass
                previous = logged_success_evidence(previous_rows, code)
                prior = tuple(candidate for candidate in (
                    fc2_candidates.get(code), previous[0] if previous is not None else None,
                ) if candidate is not None)
                known_sizes = ({previous[0].url: previous[1]}
                               if previous is not None else {})
                winner, (width, height), data = best_cover(
                    transport, code, 0,
                    metadata_root=args.metadata_root, prior_candidates=prior,
                    known_sizes=known_sizes,
                    minimum_pixels=current_size[0] * current_size[1],
                )
            # 网络异常必须按条吞掉。一次 SSL 抖动
            # （httpx.ConnectError: UNEXPECTED_EOF_WHILE_READING）此前直接打死了
            # 整个三小时的任务，而且死得很安静——日志停在半路，看起来像跑完了。
            # 长跑批处理不能因为一个番号的连接问题就整体退出。
            # `Exception` 已涵盖 Unavailable 与网络异常；Ctrl-C 是 BaseException
            # 的另一支，不会被这里吞掉，仍能正常中断。
            except Exception as exc:
                transport = _renew_transport_after_error(transport, exc)
                stats["miss"] += 1
                if args.upgrade_existing:
                    print(f"[{index}/{len(todo)}] 保留 {code}：重探失败 "
                          f"{type(exc).__name__} {exc}", flush=True)
                else:
                    rows.append({"code": code, "result": "未取得", "source": "",
                                 "width": "", "height": "", "kb": "", "url": "",
                                 "note": f"{type(exc).__name__}: {exc}"[:80]})
                    print(f"[{index}/{len(todo)}] 未取得 {code}："
                          f"{type(exc).__name__} {exc}", flush=True)
            else:
                if (args.upgrade_existing
                        and width * height <= current_size[0] * current_size[1]):
                    stats["kept"] += 1
                    print(f"[{index}/{len(todo)}] 保留 {code}  "
                          f"{current_size[0]}x{current_size[1]} >= {width}x{height}",
                          flush=True)
                else:
                    temporary = target.with_suffix(".tmp")
                    temporary.write_bytes(data)
                    try:
                        temporary.replace(target)
                    finally:
                        temporary.unlink(missing_ok=True)
                    stats["ok"] += 1
                    row = {"code": code, "result": "取得", "source": winner.source,
                           "width": width, "height": height, "kb": len(data) // 1024,
                           "url": winner.url, "note": ""}
                    if args.upgrade_existing:
                        _replace_log_row(rows, code, row)
                    else:
                        rows.append(row)
                    verb = "升级" if args.upgrade_existing else "取得"
                    print(f"[{index}/{len(todo)}] {verb} {code}  {width}x{height} "
                          f"{len(data)//1024} KB  <- {winner.source}", flush=True)
            # 落空的行也要落盘。原来这句只在取得分支里，连续落空时 CSV 整段不动；
            # 被强杀时 finally 也来不及跑，那一串判定就白做了——而「查不到」恰恰
            # 是最贵的一类：每条都要把所有候选源挨个探完才能确定。
            _write_log(args.log, rows)
    finally:
        transport.close()
        _write_log(args.log, rows)

    if args.upgrade_existing:
        print(f"\n升级 {stats['ok']}，保留 {stats['kept']}，"
              f"重探失败但保留原图 {stats['miss']} → {args.out}")
    else:
        print(f"\n取得 {stats['ok']}，未取得 {stats['miss']} → {args.out}")
    print(f"逐条记录 → {args.log}")
    return stopped.exit_code if stopped is not None else 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
