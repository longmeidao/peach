"""Seesaa 公开作品表格的精确番号证据，复用共享 HTTP 与元数据候选协议。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlencode

from bs4 import BeautifulSoup
import httpx

from .catalog_rules import normalise_code_key, same_release_code
from .http import HttpRequest, HttpxTransport
from .metadata import MetadataProviderError, validate_provider_code
from .scripting import HostLimiter

ROOT = "https://seesaawiki.jp/w/sougouwiki/"
MAX_BYTES = 4 * 1024 * 1024


def page_url(url: str) -> str:
    """仅接受这个 Wiki 的公开详情页，保留 EUC-JP 百分号编码。"""
    absolute = urljoin(ROOT, url).split('#', 1)[0]
    parsed = urlsplit(absolute)
    if (parsed.scheme != 'https' or parsed.netloc != 'seesaawiki.jp'
            or not parsed.path.startswith('/w/sougouwiki/d/') or parsed.query):
        raise ValueError('需要素人系総合 Wiki 公开详情页')
    return absolute


def parse_page(body: bytes, url: str) -> list[dict]:
    """只从带列名的作品表格取字段；推荐、评论与演员履历不作整片出演证据。"""
    url = page_url(url)
    text = body.decode('utf-8' if b'charset="utf-8"' in body[:3000].lower()
                       else 'euc_jp', errors='replace')
    soup = BeautifulSoup(text, 'html.parser')
    area = soup.select_one('#page-body .user-area')
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
            by_name = dict(zip(columns, cells))
            raw_code = by_name['NO'].get_text(' ', strip=True)
            try:
                code = validate_provider_code(normalise_code_key(raw_code))
            except ValueError:
                continue
            performers, person_links = [], []
            actress = by_name['ACTRESS']
            residual = BeautifulSoup(str(actress), 'html.parser')
            for anchor in actress.select('a[href]'):
                name = anchor.get_text(' ', strip=True)
                try:
                    target = page_url(anchor['href'])
                except ValueError:
                    continue
                if not name or re.search(r'[?？�]|不明|未確認', name):
                    continue
                performers.append({'japanese_name': name})
                person_links.append({'name': name, 'source_url': target})
                for link in residual.select('a'):
                    if link.get_text(' ', strip=True) == name:
                        link.decompose()
            remainder = re.sub(r'[\s／/、,・]+|出演順', '', residual.get_text())
            warnings = ['社区 Wiki 的出演断言需要人工复核；人物页链接不自动合并艺名']
            if remainder:
                warnings.append('出演栏含未识别或不确定内容，完整出演名单未取得')
            record = {'id': code, 'source_url': url, 'actresses': performers if not remainder else [],
                      'source_warnings': warnings,
                      'wiki_evidence': {'table': str(table.get('id') or ''), 'row': row_index,
                                        'performer_links': person_links,
                                        'performers_complete': not bool(remainder),
                                        'actress_text': actress.get_text(' ', strip=True)}}
            title = by_name.get('TITLE')
            if title is not None:
                record['title'] = title.get_text(' ', strip=True)
            release = by_name.get('RELEASE')
            if release is not None:
                record['release_date'] = release.get_text(' ', strip=True).replace('/', '-')
            note = by_name.get('NOTE')
            if note is not None:
                record['wiki_evidence']['notes'] = note.get_text(' ', strip=True)
            product = by_name['NO'].find('a', href=True)
            if product:
                record['wiki_evidence']['product_url'] = product['href']
            photo = by_name.get('PHOTO')
            if photo is not None:
                for anchor in photo.select('a[href]'):
                    if re.search(r'\.(?:jpg|png|webp)(?:\?|$)', anchor['href'], re.I):
                        record['cover_url'] = anchor['href']
                        break
            records.append(record)
    return records


class SeesaaProvider:
    """按页缓存、精确行匹配；网络请求限额及封禁停止在整个实例内共享。"""

    def __init__(self, cache_dir: Path, *, pages=(), transport=None,
                 max_requests: int = 80, refresh: bool = False, limiter=None):
        self.cache_dir = Path(cache_dir)
        self.transport = transport or HttpxTransport()
        self.limiter = limiter or HostLimiter({}, default_interval=2.0)
        self.max_requests = max_requests
        self.refresh = refresh
        self.requests = 0
        self.blocked = False
        self.pages = tuple(page_url(url) for url in pages)
        self.records: dict[str, list[dict]] = {}

    def _fetch(self, url: str) -> bytes:
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / (key + '.json')
        if not self.refresh and path.is_file():
            try:
                cached = json.loads(path.read_text(encoding='utf8'))
                body = bytes.fromhex(cached['body_hex'])
                if cached['url'] == url and len(body) <= MAX_BYTES:
                    return body
            except (ValueError, KeyError, TypeError):
                pass
        if self.blocked or self.requests >= self.max_requests:
            raise MetadataProviderError('Wiki 本批请求已停止或达到限额', kind='budget', retryable=True)
        self.limiter.wait(url)
        self.requests += 1
        try:
            response = self.transport(HttpRequest('GET', url, {}), 20, MAX_BYTES)
        except (OSError, RuntimeError, httpx.HTTPError) as error:
            raise MetadataProviderError('Wiki 网络请求未取得', kind='unavailable', retryable=True) from error
        if response.status in {403, 429}:
            self.blocked = True
        if response.status != 200:
            raise MetadataProviderError('Wiki HTTP 请求未取得', kind='unavailable',
                                        status_code=response.status, retryable=True)
        if len(response.body) > MAX_BYTES:
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
        return response.body

    def load_page(self, url: str) -> list[dict]:
        url = page_url(url)
        if url not in self.records:
            self.records[url] = parse_page(self._fetch(url), url)
        return self.records[url]

    def _match(self, code: str) -> dict | None:
        matches = [r for rows in self.records.values() for r in rows if same_release_code(code, r['id'])]
        if not matches:
            return None
        signatures = {json.dumps({k: r.get(k) for k in ('title', 'actresses', 'release_date')},
                                 ensure_ascii=False, sort_keys=True) for r in matches}
        if len(signatures) != 1:
            raise MetadataProviderError('Wiki 精确番号存在冲突行，需复核原页', kind='ambiguous')
        return matches[0]

    def query(self, code: str, source: str = 'sougouwiki') -> dict:
        code = validate_provider_code(code)
        if source != 'sougouwiki':
            raise ValueError('Wiki provider 不支持此来源')
        for url in self.pages:
            self.load_page(url)
        match = self._match(code)
        if match:
            return match
        search_url = ROOT + 'search?' + urlencode({'keywords': code})
        soup = BeautifulSoup(self._fetch(search_url).decode('euc_jp', errors='replace'), 'html.parser')
        links = []
        for anchor in soup.select('.result-box .body h3 a[href]'):
            try:
                links.append(page_url(anchor['href']))
            except ValueError:
                continue
        # 厂牌页可同时核验合集全体出演者；人物页只用于发现其厂牌目录链接。
        links = sorted(dict.fromkeys(links), key=lambda url: '%' in url)
        label_visits = 0
        for url in links[:8]:
            body = self._fetch(url)
            self.records[url] = parse_page(body, url)
            if self._match(code):
                return self._match(code)
            person = BeautifulSoup(body.decode('euc_jp', errors='replace'), 'html.parser')
            for anchor in person.select('#page-body .user-area a[href]'):
                if 'レーベル一覧' not in anchor.get_text():
                    continue
                try:
                    target = page_url(anchor['href'])
                except ValueError:
                    continue
                if target not in self.records:
                    if label_visits >= 4:
                        break
                    label_visits += 1
                    self.load_page(target)
                if self._match(code):
                    return self._match(code)
        raise MetadataProviderError('Wiki 搜索范围内未取得精确作品表格行', kind='incomplete_search', retryable=True)

    def close(self):
        close = getattr(self.transport, 'close', None)
        if close:
            close()


class RoutedMetadataProvider:
    def __init__(self, javinizer, wiki):
        self.javinizer, self.wiki = javinizer, wiki

    def query(self, code, source):
        return (self.wiki if source == 'sougouwiki' else self.javinizer).query(code, source)
