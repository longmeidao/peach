"""Seesaa 上的素人系総合 Wiki：厂牌作品表里的精确番号证据。

厂牌页是一张 `NO` / `PHOTO` / `TITLE` / `ACTRESS` / `RELEASE` / `NOTE` 的作品表，一页几十上百行，
一行一部作品。`rows()` 把一页的每一行各读成一份 `SiteRecord`，读过的页记在 `tables` 里，后面的番号
先在那里找：`--wiki-pages-file` 预取的目录页上全部作品复用同一次请求。找不到才问站内搜索，结果页
逐页读，人物页上「レーベル一覧」链到的厂牌页再读。

身份与出演只认作品表：番号按 `NO` 列经 `same_release_code` 精确回配（`390JAC-040` 与 `JAC-040`
是两件商品、两行），推荐、评论与人物页的履历不算整片出演证据。`ACTRESS` 栏里带人物页链接的
显示名才是出演候选，栏里还剩认不出的名字、`？`、`不明`、`未確認` 时整份名单只留原文证据。

取页层 `WikiPages` 是这一站的 `Session.transport`：不收凭据，成功页落盘缓存可续跑，请求限额与
撞墙停网只在本批内。它抛的 `MetadataProviderError` 与链上站的 `SourcePaused` 一样是传输层信号，
契约原样放过；分档（`budget`、`blocked`、`size_limit`、`redirect`、`ambiguous`、`incomplete_search`
等）落进 `scrape_codes` 的错误表与健康表，`budget` 与 403/429 还决定本批停网，所以不折成
`FailureReason` 的三档。搜索范围内没找到是 `incomplete_search` 且可重试：没问到不等于站上没有，
不能按 `not_found` 冻成定论。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from ..catalog_rules import normalise_code_key, same_release_code
from ..http import HttpRequest, HttpxTransport, body_text
from ..metadata import MetadataProviderError, auth_error, auth_wall_reason, validate_provider_code
from ..scripting import HostLimiter
from .base import Page, Session, SiteConfig, SiteRecord, SiteSource

#: 社区 Wiki，按社区来源登记。主机间隔用默认的 2 秒，单页上限用默认的 4 MiB（真实 Flower 页
#: 253975 字节）。不带 Cookie，也不在 `scraping_access.SOURCES` 里：采集设置页没有这一站的卡片。
SEESAA = SiteConfig(name="sougouwiki", label="素人系総合 Wiki", provider="sougouwiki",
                    base_url="https://seesaawiki.jp", domains=("seesaawiki.jp",), stage="community")
ROOT = SEESAA.base_url + "/w/sougouwiki/"
#: 本批 HTTP 请求上限的默认值（`scrape_codes --wiki-max-requests`）。
MAX_REQUESTS = 80
#: 单次请求的超时（秒）。
TIMEOUT = 20
#: 搜索结果取前几条，人物页上的厂牌目录至多再读几页。
SEARCH_PAGES = 8
LABEL_PAGES = 4

REVIEW_WARNING = '社区 Wiki 的出演断言需要人工复核；人物页链接不自动合并艺名'
INCOMPLETE_WARNING = '出演栏含未识别或不确定内容，完整出演名单未取得'
NOT_IN_SEARCH = 'Wiki 搜索范围内未取得精确作品表格行'
#: 出演栏里这些写法说明名单不确定，整份名单只留原文证据。
_UNCERTAIN_NAME = re.compile(r'[?？�]|不明|未確認')
#: 链接名摘掉之后剩下的分隔符与「出演順」不算未识别内容。
_SEPARATORS = re.compile(r'[\s／/、,・]+|出演順')
_PHOTO = re.compile(r'\.(?:jpg|png|webp)(?:\?|$)', re.I)


def page_url(url: str) -> str:
    """仅接受这个 Wiki 的公开详情页，保留 EUC-JP 百分号编码。"""
    absolute = urljoin(ROOT, url).split('#', 1)[0]
    parsed = urlsplit(absolute)
    if (parsed.scheme != 'https' or parsed.netloc != 'seesaawiki.jp'
            or not parsed.path.startswith('/w/sougouwiki/d/') or parsed.query):
        raise ValueError('需要素人系総合 Wiki 公开详情页')
    return absolute


def _soup(body: bytes) -> BeautifulSoup:
    # 这个 Wiki 两种编码的页面并存，声明写在页面自己的 `<meta>` 里；不声明的按
    # EUC-JP 解（站点的历史编码）。判据走共享的 `body_text`，不在这里另写一份。
    return BeautifulSoup(body_text(body, default='euc_jp'), 'html.parser')


def _signature(row: SiteRecord) -> str:
    return json.dumps({'title': row.title, 'actresses': [dict(p) for p in row.performers],
                       'release_date': row.release_date}, ensure_ascii=False, sort_keys=True)


def _one(code: str, rows) -> SiteRecord | None:
    """`rows` 里这个番号的那一行；没有回 `None`，几行说法不一报 `ambiguous`。"""
    matches = [row for row in rows if same_release_code(code, row.code)]
    if not matches:
        return None
    if len({_signature(row) for row in matches}) != 1:
        raise MetadataProviderError('Wiki 精确番号存在冲突行，需复核原页', kind='ambiguous')
    return matches[0]


class WikiPages:
    """这一站的取页层，一批共用一个：成功页落盘缓存、请求限额、撞墙后整批停网。

    缓存键是地址的 SHA-256，一页一个 `{url, body_hex}` 的 JSON，`--refresh` 才重取。403、429、
    登录墙与机器人验证之后本批不再联网，后面每一页都报 `budget`。
    """

    def __init__(self, cache_dir: Path, *, config: SiteConfig = SEESAA, transport=None, limiter=None,
                 max_requests: int = MAX_REQUESTS, refresh: bool = False):
        self.cache_dir = Path(cache_dir)
        self.config = config
        self.transport = transport or HttpxTransport()
        self.limiter = limiter or HostLimiter({}, default_interval=config.interval)
        self.max_requests = max_requests
        self.refresh = refresh
        self.requests = 0
        self.blocked = False

    def get(self, url: str) -> Page:
        limit = self.config.page_limit
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / (key + '.json')
        if not self.refresh and path.is_file():
            try:
                cached = json.loads(path.read_text(encoding='utf8'))
                body = bytes.fromhex(cached['body_hex'])
                if cached['url'] == url and len(body) <= limit:
                    return Page(url, body)
            except (ValueError, KeyError, TypeError):
                pass
        if self.blocked or self.requests >= self.max_requests:
            raise MetadataProviderError('Wiki 本批请求已停止或达到限额', kind='budget', retryable=True)
        self.limiter.wait(url)
        self.requests += 1
        try:
            response = self.transport(HttpRequest('GET', url, {}), TIMEOUT, limit)
        except (OSError, RuntimeError, httpx.HTTPError) as error:
            raise MetadataProviderError('Wiki 网络请求未取得', kind='unavailable', retryable=True) from error
        if response.status in {403, 429}:
            self.blocked = True
        # 鉴权失败先判：401/403 与「跳到登录页」都是同一把锁，本批再问多少次都是它。
        # 判成 unavailable 的话它会被当成网络抖动，几百个番号各自再撞一次。
        reason = auth_wall_reason(status_code=response.status, final_url=response.url)
        if reason:
            self.blocked = True
            raise auth_error(self.config.name, reason, status_code=response.status)
        if response.status != 200:
            raise MetadataProviderError('Wiki HTTP 请求未取得', kind='unavailable',
                                        status_code=response.status, retryable=True)
        if len(response.body) > limit:
            raise MetadataProviderError('Wiki 页面超过读取上限', kind='size_limit')
        if response.url and response.url != url:
            raise MetadataProviderError('Wiki 重定向页面未取得身份验证', kind='redirect')
        if b'cf-chl-' in response.body or b'Just a moment' in response.body:
            self.blocked = True
            raise MetadataProviderError('Wiki 机器人验证未取得', kind='blocked', status_code=403)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps({'url': url, 'body_hex': response.body.hex()}), encoding='utf8')
        temp.replace(path)
        return Page(url, response.body)

    def close(self) -> None:
        close = getattr(self.transport, 'close', None)
        if close:
            close()


class SeesaaSource(SiteSource):
    """一批一个实例：`tables` 记着读过的作品表，`session.transport` 须是 `WikiPages`。

    `pages` 是预取的目录页，每个番号先把它们读进 `tables` 再找。
    """

    DEFAULT = SEESAA

    def __init__(self, config: SiteConfig | None = None, *, pages=()) -> None:
        super().__init__(config)
        self.pages = tuple(page_url(url) for url in pages)
        #: 读过的页 → 页上作品表的每一行。
        self.tables: dict[str, list[SiteRecord]] = {}
        self._read: dict[str, Page] = {}

    def search_url(self, code: str) -> str:
        return ROOT + 'search?' + urlencode({'keywords': code})

    def rows(self, page: Page) -> list[SiteRecord]:
        """页上作品表的每一行各一份记录。只认带 `NO` 与 `ACTRESS` 列名的表，合并单元格的行不取。"""
        url = page_url(page.url)
        area = _soup(page.body).select_one('#page-body .user-area')
        if area is None:
            return []
        records = []
        for table in area.select('table'):
            header = table.find('tr')
            if header is None:
                continue
            columns = [c.get_text(' ', strip=True).upper() for c in header.find_all(['th', 'td'], recursive=False)]
            if 'NO' not in columns or 'ACTRESS' not in columns:
                continue
            for row_index, row in enumerate(table.find_all('tr')[1:], 1):
                cells = row.find_all(['td', 'th'], recursive=False)
                if len(cells) != len(columns) or any(c.has_attr('rowspan') or c.has_attr('colspan') for c in cells):
                    continue
                record = self._row(url, table, row_index, dict(zip(columns, cells)))
                if record is not None:
                    records.append(record)
        return records

    def _row(self, url: str, table, row_index: int, by_name: dict) -> SiteRecord | None:
        try:
            code = validate_provider_code(normalise_code_key(by_name['NO'].get_text(' ', strip=True)))
        except ValueError:
            return None
        performers, person_links = [], []
        actress = by_name['ACTRESS']
        residual = BeautifulSoup(str(actress), 'html.parser')
        for anchor in actress.select('a[href]'):
            name = anchor.get_text(' ', strip=True)
            try:
                target = page_url(anchor['href'])
            except ValueError:
                continue
            if not name or _UNCERTAIN_NAME.search(name):
                continue
            performers.append({'japanese_name': name})
            person_links.append({'name': name, 'source_url': target})
            for link in residual.select('a'):
                if link.get_text(' ', strip=True) == name:
                    link.decompose()
        remainder = _SEPARATORS.sub('', residual.get_text())
        warnings = [REVIEW_WARNING]
        if remainder:
            warnings.append(INCOMPLETE_WARNING)
        evidence = {'table': str(table.get('id') or ''), 'row': row_index,
                    'performer_links': person_links, 'performers_complete': not bool(remainder),
                    'actress_text': actress.get_text(' ', strip=True)}
        text = lambda column: by_name[column].get_text(' ', strip=True) if column in by_name else ''
        if 'NOTE' in by_name:
            evidence['notes'] = text('NOTE')
        product = by_name['NO'].find('a', href=True)
        if product:
            evidence['product_url'] = product['href']
        covers = ()
        if 'PHOTO' in by_name:
            covers = tuple(anchor['href'] for anchor in by_name['PHOTO'].select('a[href]')
                           if _PHOTO.search(anchor['href']))[:1]
        return SiteRecord(source=self.config.name, provenance=self.config.provider, code=code, source_url=url,
                          title=text('TITLE'), performers=tuple(performers) if not remainder else (),
                          release_date=text('RELEASE').replace('/', '-'), cover_urls=covers,
                          extra={'source_warnings': warnings, 'wiki_evidence': evidence})

    def remember(self, page: Page) -> list[SiteRecord]:
        """把一页的作品表记进 `tables`，后面的番号先在这里找。"""
        url = page_url(page.url)
        self._read[url] = page
        self.tables[url] = self.rows(page)
        return self.tables[url]

    def load(self, url: str, *, session: Session) -> list[SiteRecord]:
        """读一页作品表；读过的不再取。"""
        url = page_url(url)
        if url not in self.tables:
            self.remember(session.transport.get(url))
        return self.tables[url]

    def match(self, code: str) -> SiteRecord | None:
        """读过的全部作品表里这个番号的那一行；几张表说法不一（标题、出演、日期任一不同）报 `ambiguous`。"""
        return _one(code, [row for rows in self.tables.values() for row in rows])

    def _located(self, code: str) -> Page | None:
        found = self.match(code)
        return self._read[found.source_url] if found else None

    def fetch(self, code: str, *, session: Session) -> Page:
        """载有这个番号那一行的作品表页。

        先读预取的目录页；读过的表里没有就问站内搜索，结果按厂牌页在前（地址不带百分号编码的
        是厂牌目录）取前几条逐页读。厂牌页能同时核验合集的全体出演者；人物页只用来发现它链到
        的「レーベル一覧」，那几页再读，不拿人物页的履历当整片出演名单。
        """
        code = validate_provider_code(code)
        for url in self.pages:
            self.load(url, session=session)
        found = self._located(code)
        if found:
            return found
        links = []
        for anchor in _soup(session.transport.get(self.search_url(code)).body).select('.result-box .body h3 a[href]'):
            try:
                links.append(page_url(anchor['href']))
            except ValueError:
                continue
        links = sorted(dict.fromkeys(links), key=lambda url: '%' in url)
        label_visits = 0
        for url in links[:SEARCH_PAGES]:
            page = session.transport.get(url)
            self.remember(page)
            found = self._located(code)
            if found:
                return found
            for anchor in _soup(page.body).select('#page-body .user-area a[href]'):
                if 'レーベル一覧' not in anchor.get_text():
                    continue
                try:
                    target = page_url(anchor['href'])
                except ValueError:
                    continue
                if target not in self.tables:
                    if label_visits >= LABEL_PAGES:
                        break
                    label_visits += 1
                    self.load(target, session=session)
                found = self._located(code)
                if found:
                    return found
        raise MetadataProviderError(NOT_IN_SEARCH, kind='incomplete_search', retryable=True)

    def parse(self, page: Page, code: str) -> SiteRecord:
        """页上这个番号的那一行。"""
        code = validate_provider_code(code)
        url = page_url(page.url)
        rows = self.tables[url] if self._read.get(url) is page else self.rows(page)
        found = _one(code, rows)
        if found is None:
            raise MetadataProviderError(NOT_IN_SEARCH, kind='incomplete_search', retryable=True)
        return found
