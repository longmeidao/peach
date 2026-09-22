"""扫描、本地资料和缺失元数据采集共用一次有状态的处理任务。"""
from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import time
import uuid
import xml.etree.ElementTree as ET
from contextlib import closing
from pathlib import Path
from urllib.parse import quote, urlparse

from filelock import FileLock, Timeout
from PIL import Image

from .catalog_rules import (is_jav_code, is_korean_mib_code, normalise_code_key,
                            release_code_from_filename, same_release_code, scrapes_as_jav)
from .field_owners import SCAN_FILENAME, write_owned_fields
from .jav_cover_fetch import DeadlineExceeded, NotFound
from .library_nfo import directory_files, read_nfo, sidecars, local_art
from .genre_decisions import load_genre_decisions
from .metadata import extract_catalog_evidence, extract_peach_fields, identifies_code, validate_provider_code
from . import metadata_routes
from .metadata_policy import SOURCE_SPECS
from .platform import root_online, translate_ledger_path
from .review_csv import read_rows, write_rows
from .scan import scan_location
from .jobs import DiskGuard

FIELDS = ('item_key', 'code', 'query', 'asset_id', 'asset_path', 'field', 'field_label', 'current_value',
          'candidates_json', 'source_count', 'source_profile', 'policy_version', 'status',
          'size_gb', 'videos', 'fetched_at')
LABELS = dict(title='标题', original_title='原标题', performers='演员', studio='厂牌',
              series='系列', release_date='发行日期', tags='内容标签')

#: 状态里最多保留这么多条问题；完整问题写在任务专属 JSONL 里，接口分页读取。
ISSUE_PREVIEW_LIMIT = 20

#: 这条链能分开跑的两段，和一次跑完。名字进接口也进页面，改这里就是改契约。
SCAN_STAGE, COLLECT_STAGE, ALL_STAGES = 'scan', 'collect', 'all'
STAGES = (ALL_STAGES, SCAN_STAGE, COLLECT_STAGE)

#: 没有动作截止时间的阶段（本地读取）超过这么久没有心跳就在页面上预警。
STALL_AFTER_SECONDS = 120.0

#: 单项外部动作预算：资料查询覆盖一次请求加一轮重试，封面覆盖证据查询与候选往返。
#: 到点只结束当前项目并记为可重试，不让一个来源拖住整批任务。
ACTION_BUDGETS = {'querying_metadata': 90.0, 'fetching_cover': 240.0}

#: 来源明确答复「没有」之后多久不再问。「没有」不是永久的：来源会补录，片子可能后来上架。
MISS_TTL_SECONDS = 7 * 24 * 3600

#: 主机间隔。默认 2 秒；javdb 按出口 IP 计配额，这一档由用户定（2026-09-22 定为 3 秒，
#: 每分钟 20 页）。参照面：每分钟 40～50 页实测会招来 3～7 天的封 IP，`harvest_directory_links`
#: 那条批量线仍按 5 秒跑。撞上 403 不再是盲等 24 小时——`scraping_access.FIRST_BLOCKED_PAUSE`
#: 先停 15 分钟，连着再撞才翻倍，所以这一档收紧的代价是有限且可观测的（docs/SOURCING.md）。
SOURCE_INTERVALS = {'javdb.com': 3.0, 'jdbstatic.com': 3.0}
SOURCE_LABELS = {'r18dev': 'r18.dev', 'avbase': 'AVBase', 'javbus': 'JavBus', 'javdb': 'javdb',
                 'fc2': 'FC2', 'fc2cmadb': 'FC2CMADB', 'javarchive': 'JavArchive',
                 '1pondo': '一本道', 'local_nfo': '本地 NFO'}
PROVIDER_NAMES = {'local_nfo': 'local-nfo', 'r18dev': 'r18-json', 'avbase': 'avbase-search',
                  'javbus': 'javbus-page', 'javdb': 'javdb-page', 'fc2': 'fc2-article',
                  'fc2cmadb': 'fc2cmadb-article', 'javarchive': 'javarchive-page',
                  '1pondo': '1pondo-json'}
#: FC2 商品页实测 300～320 KB，fc2cmadb 那页 90 KB；说明与评论都在同一页里。
FC2_PAGE_LIMIT = 2 * 1024 * 1024
#: 一本道的作品 JSON 实测 6～8 KB，带样片清单也只有十几 KB。
ONE_PONDO_LIMIT = 1024 * 1024
R18_ACTRESS_IMAGE = "https://pics.dmm.co.jp/mono/actjpgs/{filename}"


def _r18_actresses(rows):
    actresses = []
    for row in rows or []:
        image = str(row.get('image_url') or '').strip()
        thumb_url = (R18_ACTRESS_IMAGE.format(filename=quote(image, safe=''))
                     if image and '/' not in image and '\\' not in image else '')
        actresses.append({
            'japanese_name': row.get('name_kanji') or row.get('name_romaji') or '',
            'name_kana': row.get('name_kana') or '',
            'name_romaji': row.get('name_romaji') or '',
            'dmm_id': row.get('id') or '',
            'thumb_url': thumb_url,
            'profile_source': 'r18dev',
        })
    return actresses


def describe_failure(error):
    """把来源失败写成问题清单里能直接读懂的一句。"""
    import httpx
    from .avatar_picker import PickerError
    from .jav_cover_fetch import Unavailable
    from .scraping_access import SourcePaused
    text = str(error).strip()
    if isinstance(error, Unavailable) and text.startswith('HTTP '):
        return f'来源返回 {text}'
    # 这几个的消息本来就是写给人看的，原样用；别的只报类型，免得把内部细节贴到界面上。
    if isinstance(error, (Unavailable, SourcePaused, PickerError, httpx.TransportError)) and text:
        return text
    return f'处理出错（{type(error).__name__}）'
#: 来源说「没有」不是待办：馆藏里本来就有大量独立资源和创作者作品，任何目录站都收不到
#: 它们。逐条记在日志里备查，界面只按这两类各报一个数（`state['notes']`），不进问题清单。
MISS_MESSAGES = {'querying_metadata': '外部来源没有这部片的资料，7 天内不再问',
                 'fetching_cover': '外部来源没有这部片的封面，7 天内不再问'}
#: 日志里的写法反查回上面的键，界面按键取自己的短标签。
NOTE_KEYS = {message: key for key, message in MISS_MESSAGES.items()}

#: 状态文件与候选 CSV 的落盘节流。页面轮询读的是内存里的任务快照，文件只为进程没了
#: 之后还能看到最后状态；候选 CSV 随处理进度越写越大，每条资产都重写一遍是平方级开销。
STATE_FLUSH_SECONDS = 0.5
CANDIDATE_FLUSH_SECONDS = 5.0

#: 采集要补的字段，以及它们在 `asset` 表里的列名（没列出的与字段同名或不在表里）。
COLLECTED_FIELDS = ('title', 'performers', 'studio', 'release_date', 'tags')
COLUMN_OF = {'title': 'catalog_title'}

#: 一趟任务向外部来源要的总量。三条闸门里谁先到谁生效，之后每部片只记「本趟…已用完」。
#: 一部片问三家目录站、每家 1～2 次，所以 6000 次约等于 1500 部；按 `SOURCE_INTERVALS`
#: 的每来源 2 秒间隔，三家并行也正好要 4 小时才用得完，时间不会先把它掐断。
#: 封面与资料页合计每次约 250 KB，1 GiB 装得下这 6000 次。
MAX_SOURCE_REQUESTS = 6000
MAX_SOURCE_BYTES = 1024 * 1024 * 1024
MAX_SOURCE_SECONDS = 4 * 3600


class LibraryMetadataProvider:
    """复用封面采集的 R18 JSON 入口与按来源配置的传输。

    `secrets_root` 是凭据根本身（`peach-data/secrets`），不是它底下的 `follow`：
    `CredentialStore` 自己会拼上那一层。多给一层的表现不是报错，是每个来源都读成
    「没有凭据」——采集设置里贴好的 JavBus、javdb Cookie 一条都不会被带上。
    """
    def __init__(self, secrets_root):
        from .scraping_access import SourceTransport
        from .jav_cover_fetch import HostLimitedTransport
        self.transport = HostLimitedTransport(
            SourceTransport(secrets_root, max_requests=MAX_SOURCE_REQUESTS,
                            max_bytes=MAX_SOURCE_BYTES, max_seconds=MAX_SOURCE_SECONDS),
            2.0, intervals=SOURCE_INTERVALS)

    def community(self, code, *, deadline=None, route=None):
        """官方渠道落空时问综合索引那一档，返回 `[(来源, 资料)]`。

        问哪几家按 `community_catalog.community_sources_for`，它转手问
        `metadata_routes.community_route`：有码与素人问 AVBase、JavBus 与 javdb，
        FC2 的商品号只问 javdb。`route` 是调用方已经算好的那一档成员，给了就不再算
        （那一步要本机证据，provider 手上没有）。资料和封面两步都可能要它，同一个
        番号只问一次：javdb 的配额经不起每部片问两遍。
        几家都明确说没有才是 `NotFound`；有一家出错且谁都没给资料时，带着原因报 `Unavailable`。
        """
        from .community_catalog import community_sources_for
        from .jav_cover_fetch import Unavailable
        cache = self.__dict__.setdefault('_community', {})
        if code not in cache:
            found, problems = [], []
            for source, fetch in community_sources_for(code, route=route):
                try:
                    found.append((source, fetch(self.transport, code, deadline=deadline)))
                except DeadlineExceeded:
                    raise
                except NotFound:
                    continue
                except Exception as error:
                    text = describe_failure(error)
                    problems.append(text if text.startswith(SOURCE_LABELS[source]) else f'{SOURCE_LABELS[source]}：{text}')
            cache[code] = (found or (Unavailable('；'.join(problems)) if problems
                                     else NotFound('社区来源都没有这个番号')))
        if isinstance(cache[code], Exception):
            raise type(cache[code])(str(cache[code]))
        return cache[code]

    def fc2(self, code, *, deadline=None, route=None):
        """FC2 自己那一页，下架了就依次问两个存档站；返回 `[(来源, 资料)]`。

        资料和封面两步都要它，同一个番号只问一次：商品页约 300 KB，问两遍白花一份流量。
        已下架的商品仍回 200，解析器认不出那份 Product 就回 None——那不是抓取失败，是这部
        片在站上没有了。本地这批没封面的 FC2 多数是这种，所以接着问 fc2cmadb：它留着下架
        作品的标题、卖家、标签与封面原图。它也没有的才落到 JavArchive，那一档只给标题和
        一张转存封面，比官方原图差一档，所以排在最后（2026-09-22 实测 `FC2-PPV-4137487`
        在 fc2cmadb 是 404，JavArchive 上有）。三处都没有才按 `NotFound` 交出去，记进
        「没有」的记忆，一周内不再问。

        `route` 是这个番号的完整来源链（`metadata_routes.route_for_code`）：链上摘掉哪一处
        就不问哪一处，不给就三处按上面的顺序都问。
        """
        from .metadata_fc2 import (ARCHIVE_SOURCE, MIRROR_SOURCE, ROOT, SOURCE,
                                   article_url, parse_article)
        cache = self.__dict__.setdefault('_fc2', {})
        if code not in cache:
            if not article_url(code):
                cache[code] = NotFound('这个番号认不出 FC2 商品号')
            else:
                found, problems = None, []
                attempts = [attempt for name, attempt in (
                    (SOURCE, lambda: self._fc2_page(SOURCE, ROOT, article_url(code), parse_article,
                                                    code, deadline=deadline)),
                    (MIRROR_SOURCE, lambda: self._fc2_mirror(code, deadline=deadline)),
                    (ARCHIVE_SOURCE, lambda: self._fc2_archive(code, deadline=deadline)))
                    if route is None or name in route]
                for attempt in attempts:
                    try:
                        found = attempt()
                    except DeadlineExceeded as error:
                        cache[code] = error
                        break
                    except NotFound:
                        continue
                    except Exception as error:  # noqa: BLE001 - 原因由调用方汇总成一句话
                        problems.append(error)
                        continue
                    break
                if code not in cache:
                    # 一处报错、另一处说没有时报错误：那个番号在报错那处有没有，还没问出来。
                    cache[code] = found or (problems[0] if problems
                                            else NotFound('FC2、fc2cmadb 与 JavArchive 上都没有这个商品'))
        if isinstance(cache[code], Exception):
            raise type(cache[code])(str(cache[code]))
        return cache[code]

    def _fc2_mirror(self, code, *, deadline=None):
        """fc2cmadb 那一档要两跳：作品页给完整资料，女优那一栏得单独再问一次。

        女优是这一页的延迟 prop，首屏那份 HTML 里根本没有。第二跳只要一千来字节，握手
        版本号取自刚拿到的这一页。问不出来就按没有女优落——其余那些字段是站上最全的一
        份，不该被这一跳的失败拖着一起丢。
        """
        from .jav_cover_fetch import Unavailable, _fetch
        from .metadata_fc2 import (MIRROR_ROOT, MIRROR_SOURCE, mirror_partial_headers,
                                   mirror_url, parse_mirror, parse_mirror_actresses)
        from .scraping_access import SourcePaused
        url = mirror_url(code)
        page = _fetch(self.transport, url, referer=MIRROR_ROOT + '/',
                      limit=FC2_PAGE_LIMIT, deadline=deadline)
        headers = mirror_partial_headers(page)
        actresses = ()
        if headers:
            try:
                partial = _fetch(self.transport, url, referer=url, limit=FC2_PAGE_LIMIT,
                                 extra_headers=headers, deadline=deadline)
            except (SourcePaused, Unavailable):
                partial = b''
            actresses = parse_mirror_actresses(partial)
        payload = parse_mirror(page, code, actresses=actresses)
        if not payload:
            raise NotFound(f'{SOURCE_LABELS[MIRROR_SOURCE]} 上没有这个商品')
        return [(MIRROR_SOURCE, payload)]

    def _fc2_archive(self, code, *, deadline=None):
        """JavArchive 那一档要先搜再取作品页：作品地址里夹着站内文章号和标题，拼不出来。

        搜索结果那一条只有标题和一张缩略图，作品页才有标签、发行日、时长和真正的封面
        位。省掉这一跳换来的是三个字段全空、封面地址靠文件名硬推——站上的命名没有统一，
        推出来的多半不存在。搜不着就是没有，不当抓取失败。
        """
        from .jav_cover_fetch import _fetch
        from .metadata_fc2 import (ARCHIVE_ROOT, ARCHIVE_SOURCE, archive_link,
                                   archive_search_url, parse_archive)
        results = _fetch(self.transport, archive_search_url(code), referer=ARCHIVE_ROOT + '/',
                         limit=FC2_PAGE_LIMIT, deadline=deadline)
        link = archive_link(results, code)
        if not link:
            raise NotFound(f'{SOURCE_LABELS[ARCHIVE_SOURCE]} 上没有这个商品')
        return self._fc2_page(ARCHIVE_SOURCE, ARCHIVE_ROOT, ARCHIVE_ROOT + link,
                              parse_archive, code, deadline=deadline)

    def _fc2_page(self, source, root, url, parse, code, *, deadline=None):
        """抓一页并解析成 `[(来源, 资料)]`；页面在、但那份数据对不上这个商品时报没有。"""
        from .jav_cover_fetch import _fetch
        page = _fetch(self.transport, url, referer=root + '/',
                      limit=FC2_PAGE_LIMIT, deadline=deadline)
        payload = parse(page, code)
        if not payload:
            raise NotFound(f'{SOURCE_LABELS[source]} 上没有这个商品')
        return [(source, payload)]

    def one_pondo(self, code, *, deadline=None):
        """一本道自己那份作品 JSON，返回 `[('1pondo', 资料)]`。

        资料和封面两步都要它，同一个番号只问一次。下架的作品官网直接回 404，那就是
        「站上没有」，记进「没有」的记忆，一周内不再问。
        """
        from .jav_cover_fetch import _fetch
        from .metadata_1pondo import ROOT, SOURCE, detail_url, parse_details
        cache = self.__dict__.setdefault('_1pondo', {})
        if code not in cache:
            url = detail_url(code)
            if not url:
                cache[code] = NotFound('这个番号不是一本道的写法')
            else:
                try:
                    document = _fetch(self.transport, url, referer=ROOT + '/',
                                      limit=ONE_PONDO_LIMIT, deadline=deadline)
                except (DeadlineExceeded, NotFound) as error:
                    cache[code] = error if isinstance(error, DeadlineExceeded) \
                        else NotFound('一本道站上没有这部片')
                except Exception as error:  # noqa: BLE001 - 原因由调用方汇总成一句话
                    cache[code] = error
                else:
                    payload = parse_details(document, code)
                    cache[code] = ([(SOURCE, payload)] if payload
                                   else NotFound('一本道回的作品号对不上这个番号'))
        if isinstance(cache[code], Exception):
            raise type(cache[code])(str(cache[code]))
        return cache[code]

    def _official_candidates(self, code, evidence=(), *, deadline=None):
        """发行方自己那张封面，交给 `best_cover` 当候选。

        只有 FC2 和一本道走这里：别的番号的官方面 `best_cover` 自己会找（r18、MGS、
        Prestige），这两家它一处都不问。资料那步问过的同一份缓存，这里不再发请求。
        """
        from .jav_cover_fetch import Candidate, Unavailable
        from .metadata_1pondo import ROOT as PONDO_ROOT
        from .metadata_fc2 import ROOT as FC2_ROOT
        sources = _sources_for(code, *evidence)
        if 'fc2' in sources:
            source, ask, referer = 'fc2', self.fc2, FC2_ROOT + '/'
        elif '1pondo' in sources:
            source, ask, referer = '1pondo', self.one_pondo, PONDO_ROOT + '/'
        else:
            return ()
        try:
            found = ask(code, deadline=deadline)
        except (NotFound, DeadlineExceeded):
            raise
        except Exception as error:  # noqa: BLE001 - 交给 `cover()` 汇总成一句话
            raise Unavailable(f'{SOURCE_LABELS[source]}：{describe_failure(error)}') from error
        return tuple(Candidate(urlparse(payload['cover_url']).netloc.lower(),
                               payload['cover_url'], referer)
                     for _, payload in found if payload.get('cover_url'))

    def query(self, code, source='r18dev', *, deadline=None):
        from .jav_cover_fetch import R18_DETAIL, _fetch
        from urllib.parse import quote
        url = R18_DETAIL.format(code=quote(code))
        raw = json.loads(_fetch(self.transport, url, referer='https://r18.dev/',
                                limit=2 * 1024 * 1024, deadline=deadline))
        if not identifies_code(code, {'content_id': raw.get('content_id')}):
            raise ValueError('来源返回的番号不匹配')
        name = lambda key: (raw.get(key) or {}).get('name', '')
        payload = dict(id=code, content_id=raw.get('content_id'), source_url=url,
                       title=raw.get('title'), maker=name('maker'), series=name('series'),
                       release_date=raw.get('release_date'),
                       director=raw.get('director'), label=name('label'), runtime=raw.get('runtime_minutes'),
                       cover_url=(raw.get('images') or {}).get('jacket_image'),
                       actresses=[{'japanese_name': row.get('name', '')} for row in raw.get('actresses', [])],
                       genres=[row.get('name', '') for row in raw.get('categories', [])], raw=raw)
        return self._with_japanese(payload, deadline=deadline)

    def _with_japanese(self, payload, *, deadline=None):
        """补上 r18 combined 页的日文写法，形状与 Javinizer-Go 快照的 `translations` 一致。

        `dvd_id` 入口只给英文，标题和系列多是机翻（ABW-358 的 `title_en_is_machine_translation`
        为真），演员只有罗马字。日文在 `combined=<content_id>` 那一页：`title_ja`、
        `series_name_ja`、演员 `name_kanji`。厂牌不取日文——账本的厂牌实体用品牌名
        （`Prestige`、`MOODYZ`），换成 `プレステージ` 会另起一个实体。
        这一页取不到时照旧交英文，不让一次失败吞掉整条资料。

        genre 取 `categories[].name_ja`，也就是 DMM 自己那套词。英文是 r18 在它上面
        再译一层，词根在那一层会丢：`その他フェチ` 一眼看得出是「フェチ」那一格的兜底，
        从 `Other Fetishes` 反推不回去。取日文原词，一个词只登记一次就覆盖整个来源；
        取英文则每个写法都得另外逐条登记才追得平。
        """
        from .jav_cover_fetch import R18_COMBINED, Unavailable, _fetch
        from urllib.parse import quote
        import httpx
        content_id = str(payload.get('content_id') or '')
        if not content_id:
            return payload
        try:
            combined = json.loads(_fetch(self.transport, R18_COMBINED.format(content_id=quote(content_id)),
                                         referer='https://r18.dev/', limit=2 * 1024 * 1024, deadline=deadline))
        except (Unavailable, ValueError, httpx.TransportError):
            return payload
        if not isinstance(combined, dict) or combined.get('content_id') != content_id:
            return payload
        directors = [row.get('name_kanji') for row in combined.get('directors') or [] if row.get('name_kanji')]
        payload['translations'] = [dict(language='ja', title=combined.get('title_ja') or '',
                                        series=combined.get('series_name_ja') or '',
                                        label=combined.get('label_name_ja') or '',
                                        director=directors[0] if directors else '')]
        actresses = _r18_actresses(combined.get('actresses'))
        if any(row['japanese_name'] for row in actresses):
            payload['actresses'] = actresses
        japanese = [row.get('name_ja') or row.get('name_en') or ''
                    for row in combined.get('categories') or []]
        if any(japanese):
            payload['genres'] = [name for name in japanese if name]
        payload['combined'] = combined
        return payload

    def cover(self, code, cover_root, *, deadline=None, evidence=()):
        """官方大图优先；没有就用社区来源里两个图源对得上的那张；再没有就用官方小图。

        小图也比没有封面强（素人系官方图只有 300×300），但社区来源的大图只有被另一个
        图源印证过才用，官方小图本身也算一个图源（ADR-0030）。

        FC2 与一本道的那张走官方这一档而不是社区那一档：`storage*.contents.fc2.com` 上的图
        是卖家自己传的商品图（实测 2350×2352），一本道那张是站点自己的剧照（960×540），
        两处都是发行方，没有第二个图源可印证也不该被扣住。`evidence` 见 `_sources_for`。
        """
        from .community_catalog import verified_cover
        from .jav_cover_fetch import MIN_WIDTH, SMALL_MIN_WIDTH, Unavailable, best_cover
        target = cover_root / (code + '.jpg')
        if target.is_file():
            return False
        official, verified_by, problems = None, (), []
        try:
            official = best_cover(self.transport, code, 0, deadline=deadline,
                                  prior_candidates=self._official_candidates(code, evidence, deadline=deadline),
                                  minimum_width=SMALL_MIN_WIDTH)
        except NotFound:
            pass
        except Unavailable as error:
            problems.append(describe_failure(error))
        chosen = official
        if official is None or official[1][0] < MIN_WIDTH:
            try:
                *picked, verified_by = verified_cover(self.transport, code, self.community(code, deadline=deadline),
                                                      reference=official, deadline=deadline)
                chosen = tuple(picked)
            except NotFound:
                pass
            except Unavailable as error:
                problems.append(describe_failure(error))
        if chosen is None:
            raise Unavailable('；'.join(problems)) if problems else NotFound('官方与社区来源都没有这部片的封面')
        candidate, size, data = chosen
        from .cover_artwork import install_cover
        install_cover(target, code, data, size, evidence=dict(source=candidate.source,
            source_url=candidate.url, width=size[0], height=size[1], verified_by=list(verified_by),
            raw_sha256=hashlib.sha256(data).hexdigest(), checked_at=time.time()))
        return True

    def reset(self):
        """丢弃可能卡住的连接；下一个项目从新传输开始。"""
        self.transport.renew()

    def close(self):
        self.transport.close()


def state_path(config):
    return config.directory('state') / 'library-processing.json'


def issues_path(config, job_id):
    return config.directory('state') / f'library-processing-{job_id}.issues.jsonl'


def misses_path(config):
    return config.directory('state') / 'library-metadata-misses.json'


def _save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def decorate(state, *, now=None):
    """把状态投影成当前契约，并给运行中的副本补上等待时长与「长时间没有进展」标记。

    旧状态文件把完整问题存在 `issues` 数组里；投影只留计数与前 20 条预览，
    其余照旧可读，也不把上千条问题重新塞回每次轮询的响应。读取只改副本，
    写入者还拿着锁时 GET 不会把任务改成失败，慢与卡死由人判断。
    """
    state = dict(state)
    legacy = state.pop('issues', None)
    if legacy and 'issue_count' not in state:
        state['issue_count'] = len(legacy)
        state['issue_preview'] = [dict(asset_id=row.get('asset_id'), title=str(row.get('title') or ''),
                                       path=str(row.get('path') or ''), message=str(row.get('message') or ''))
                                  for row in legacy[:ISSUE_PREVIEW_LIMIT]]
        state['issues_truncated'] = len(legacy) > ISSUE_PREVIEW_LIMIT
    if state.get('status') != 'running':
        return state
    now = time.time() if now is None else now
    started = state.get('current_started_at') or state.get('last_progress_at') or state.get('started_at')
    if started:
        state['waited_seconds'] = max(0, int(now - started))
    deadline = state.get('current_deadline_at')
    last = state.get('last_progress_at') or state.get('started_at')
    if deadline:
        state['stalled'] = now >= deadline
    else:
        state['stalled'] = bool(last and now - last >= STALL_AFTER_SECONDS)
    return state


def _issue_classification(message, retryable):
    """这条记录写进日志的级别，以及它值不值得重试。告知项两样都不是问题。"""
    note = NOTE_KEYS.get(message)
    return 'info' if note else 'error', retryable and not note


def _record_issue(state, log_path, record):
    """把一条记录写进日志，并按类型计进状态。

    告知项只按类型各记一个数：它们占着那 20 条预览的话，一条真问题就被几百条
    「来源没有这部片」挤出屏幕，而全库有大量片子任何目录站都收不到。
    """
    with open(log_path, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    note = NOTE_KEYS.get(record['message'])
    if note:
        state['notes'][note] = state['notes'].get(note, 0) + 1
        return
    state['issue_count'] += 1
    if len(state['issue_preview']) < ISSUE_PREVIEW_LIMIT:
        state['issue_preview'].append({key: record[key] for key in
                                       ('asset_id', 'title', 'path', 'message', 'severity')})
    else:
        state['issues_truncated'] = True
    asset_id = record['asset_id']
    if record['retryable'] and asset_id is not None and asset_id not in state['retryable_asset_ids']:
        state['retryable_asset_ids'].append(asset_id)


def snapshot(config):
    try:
        state = json.loads(state_path(config).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'status': 'idle'}
    if state.get('status') == 'running':
        try:
            # 锁覆盖 CLI 与 HTTP；进程退出后系统会释放它。
            with FileLock(str(state_path(config)) + '.lock', timeout=0):
                state = json.loads(state_path(config).read_text(encoding='utf-8'))
                if state.get('status') == 'running':
                    # 拿得到锁说明写入者已经不在了。结论写回文件：只改副本的话，另一个读取者
                    # 正好短暂占着锁时会读到原样的「运行中」，界面就在两种状态之间来回跳。
                    state.update(status='failed', error='处理被中断，可重试未完成的部分。',
                                 completed_at=state.get('last_progress_at') or time.time())
                    _save(state_path(config), state)
        except Timeout:
            pass
    # 状态文件没有 `notes` 时按日志重算：每条记录都在日志里，告知项和问题分得开。
    # 行数对不上说明日志被截断过，那时宁可原样显示。
    if 'notes' not in state and state.get('status') in ('complete', 'failed') and state.get('job_id'):
        try:
            count, problems, notes, retryable = 0, 0, {}, set()
            with issues_path(config, state['job_id']).open(encoding='utf-8') as handle:
                for line in handle:
                    item = json.loads(line)
                    count += 1
                    key = NOTE_KEYS.get(item.get('message'))
                    if key:
                        notes[key] = notes.get(key, 0) + 1
                        continue
                    problems += 1
                    if item.get('retryable') and item.get('asset_id') is not None:
                        retryable.add(item['asset_id'])
            if count == state.get('issue_count'):
                preview = [item for item in state.get('issue_preview', [])
                           if item.get('message') not in NOTE_KEYS]
                state.update(notes=notes, issue_count=problems, issue_preview=preview,
                             issues_truncated=problems > len(preview),
                             retryable_asset_ids=sorted(retryable))
                if state.get('error') == f'{count} 项需要处理，可重试未完成的部分。':
                    state['status'] = 'failed' if problems else 'complete'
                    state['error'] = f'{problems} 项需要处理，可重试未完成的部分。' if problems else ''
        except (OSError, ValueError, TypeError):
            pass
    return decorate(state)


def _local_poster(video, code, cover_root, payload=None, posters=None):
    """`posters` 是调用方已经从同目录索引里挑出的海报候选，给了就不再列目录。"""
    target = cover_root / (code + '.jpg')
    if target.is_file():
        return False
    if posters is None:
        _, posters = sidecars(video)
    posters = list(posters)
    reference = local_art(video, payload or {})
    if reference:
        posters.insert(0, reference)
    if not posters:
        return False
    poster = posters[0]
    if poster.stat().st_size > 32 * 1024 * 1024:
        return False
    with Image.open(poster) as image:
        image.load()
        output = io.BytesIO()
        image.convert('RGB').save(output, format='JPEG', quality=95)
        data, size = output.getvalue(), image.size
    from .cover_artwork import install_cover
    install_cover(target, code, data, size)
    return True


def _fields(payload, genre_decisions=None):
    fields = extract_peach_fields(payload, genre_decisions)
    evidence = extract_catalog_evidence(payload)
    for key in ('title', 'original_title'):
        if key in evidence:
            fields[key] = evidence[key]
    if payload.get('local_tags'):
        from .entities import canonicalize_entity_name
        from .genre_taxonomy import UNMAPPED, resolve_genre
        # NFO 的 tag 既可能是来源 genre，也可能是用户自己的本地标签。认得出的统一
        # 投影成 Peach 中文标签，明确的画质／促销／发行属性丢掉；词表不认识的原样
        # 保留，不能把用户自己的分类当成「未知 genre」静默吞掉。
        values = []
        for raw in payload['local_tags']:
            resolved = resolve_genre(raw, genre_decisions)
            if resolved is None:
                continue
            value = raw if resolved == UNMAPPED else resolved
            value = canonicalize_entity_name('tag', value)
            if value and value not in values:
                values.append(value)
        values = [value for value in values if value]
        if values:
            fields['tags'] = dict(value=values, display_value='、'.join(values), warnings=[])
    return fields


def _require_writer(config, db_path):
    if config.replication.enabled:
        from .sync import writer_device
        device_path = config.directory('state') / 'device-id'
        device = device_path.read_text(encoding='utf-8').strip() if device_path.is_file() else ''
        if not device or writer_device(Path(db_path), config.shared_root / 'database' / 'ledger.db') != device:
            raise ValueError('这台电脑是只读端，请在写入端扫描和导入资料')


def _text(raw):
    """比对取值用的写法：空白差异和大小写不算两个值。"""
    return ' '.join(str(raw or '').split()).casefold()


def _provider_code(raw):
    """能拿去问来源的番号；不是发行番号的写法返回空串。

    `asset.code` 里有一部分存的是目录名而不是番号：创作者账号（`BANBI_555`、
    `RAIKUN325`）、片源站编号（`WX17`）和创作者自编号（`DTW003`）。2026-09-16 只读
    盘点，本机账本 617 行是这样的值。它们问哪家来源都只会查空，拿番号形态逐行校验
    还会把这 617 行全报成问题项，真正要处理的几十条就此淹掉。当作没有番号处理：
    这些行本来就只登记本地海报。
    """
    if not is_jav_code(raw):
        return ''
    try:
        return validate_provider_code(normalise_code_key(raw))
    except ValueError:
        # 形态两把尺（`is_jav_code` 与 `metadata._SAFE_CODE`）对不上的写法，本机账本
        # 1673 个番号里一个都没有；真出现也只能当作没有番号，采集不为一行停摆。
        return ''


def _candidate_identity(source, value):
    """候选的身份：来源加取值。取值变了身份就得跟着变，否则「批准的是哪一版」答不出来。"""
    return hashlib.sha256(json.dumps([source, value], ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()


def _merge_candidates(groups, row, code, source, document, evidence_path, genre_decisions, local_fields=()):
    """把 `document` 里认得出的字段并进 `groups`：同来源的旧候选换掉，别的来源保留。

    本地 NFO 已给出的字段只收 NFO 这一条（ADR-0029）。NFO 的番号已经和文件名对过，
    是用户自己刮削留下的；在线来源再给一条同字段候选，唯一的效果是把「英文机翻标题
    对日文原题」这种写法差异变成一道人工复核题。

    账本已经有值的字段，联网来源同样不给候选，取值与现值相同的谁给都不要（ADR-0033）。
    一次抓取回来的是整份资料，缺 tags 也会顺带带回标题、厂牌、发行日期；不拦住就是
    每部片多出几道「英文机翻对日文原题」和「同一个值对同一个值」。
    """
    local = source == 'local_nfo'
    spec = SOURCE_SPECS.get(source)
    official = bool(spec and spec.official)
    for field, value in _fields(document, genre_decisions).items():
        current = _text(row.get(COLUMN_OF.get(field, field)))
        key = f"asset:{row['id']}:{field}"
        if not local and field == 'performers' and field in local_fields:
            _merge_local_performer_profiles(groups, key, value, source)
            continue
        if not local and (field in local_fields or current):
            continue
        if current and current == _text(value.get('display_value', value['value'])):
            continue
        identity = _candidate_identity(source, value['value'])
        # 来源自报的番号跟着候选走：落库前要再核一次身份，javdb 的详情页地址里没有番号。
        candidate = dict(candidate_key=identity, source=source, provider=PROVIDER_NAMES.get(source, source),
                         value=value['value'], display_value=value.get('display_value', str(value['value'])),
                         warnings=value.get('warnings', []),
                         confidence=0.9 if local else 0.75 if official else 0.6,
                         source_url=document.get('source_url', ''), raw_snapshot=str(evidence_path),
                         provider_id=str(document.get('id') or ''), content_id=str(document.get('content_id') or ''),
                         source_kind='local' if local else spec.kind if spec else 'community', official=official,
                         catalog_evidence=extract_catalog_evidence(document))
        # 只有 tags 字段有未收录原文；别的字段挂一个空列表只是让每条候选都胖一圈。
        if value.get('unmapped_genres'):
            candidate['unmapped_genres'] = value['unmapped_genres']
        group = groups.get(key, dict(item_key=key, code=code or '', query=code or row['name'],
            asset_id=row['id'], asset_path=row['path'], field=field,
            field_label=LABELS[field], current_value=row.get(COLUMN_OF.get(field, field)) or '',
            candidates_json='[]', source_count=0, source_profile='library', policy_version='library-v1',
            status='candidate', size_gb=round((row['size'] or 0)/1024**3, 2), videos=1, fetched_at=''))
        choices = [entry for entry in json.loads(group['candidates_json'])
                   if entry['source'] != source and not (local and entry['source'] != 'local_nfo')]
        choices.append(candidate)
        group.update(candidates_json=json.dumps(choices, ensure_ascii=False), source_count=len(choices),
                     fetched_at=time.strftime('%Y-%m-%d %H:%M:%S'))
        groups[key] = group


def _merge_local_performer_profiles(groups, key, remote, source):
    """NFO 的演员值不让在线来源替换，但收下同名人物的资料页证据。

    r18 combined 页同一个人物对象里带 DMM id、假名、罗马字和官方头像；此前因为
    NFO 已给演员，整条在线候选被跳过，这些不改变演员真值的资料也一起丢了。只在
    规范化主名逐字匹配时合并，来源给了另一个人时仍按 ADR-0029 保留 NFO 一条。
    """
    from .entities import normalize_entity_name

    group = groups.get(key)
    if group is None:
        return
    try:
        candidates = json.loads(group['candidates_json'])
    except (KeyError, TypeError, ValueError):
        return
    remote_people = {
        normalize_entity_name(person.get('name')): person
        for person in remote.get('value') or [] if isinstance(person, dict)
    }
    changed = False
    for candidate in candidates:
        if candidate.get('source') != 'local_nfo':
            continue
        people = candidate.get('value')
        if not isinstance(people, list):
            continue
        before = json.dumps(people, ensure_ascii=False, sort_keys=True)
        for person in people:
            if not isinstance(person, dict):
                continue
            matched = remote_people.get(normalize_entity_name(person.get('name')))
            if matched is None:
                continue
            for field in ('external_id', 'thumb_url', 'aliases'):
                if matched.get(field) and person.get(field) != matched[field]:
                    person[field] = matched[field]
                    changed = True
            if matched.get('profile_source') or source:
                profile_source = matched.get('profile_source') or source
                if person.get('profile_source') != profile_source:
                    person['profile_source'] = profile_source
                    changed = True
        # 取值变了，身份就得重算：`candidate_key` 是「用户批准的是哪一版」的唯一凭据，
        # 补进资料却留着旧键，事后按键回溯拿到的是没有这些证据的那一版。
        if json.dumps(people, ensure_ascii=False, sort_keys=True) != before:
            candidate['candidate_key'] = _candidate_identity(candidate.get('source'), people)
    if changed:
        group['candidates_json'] = json.dumps(candidates, ensure_ascii=False)
        groups[key] = group


def _sources_for(code, *evidence, route_overrides=None):
    """按这个番号问哪几**档**资料来源，从左到右；链本身在 `metadata_routes`。

    这里只把「按内容类型的来源链」摊成这条采集路认得的档名：官方与发行方那几家逐个
    成档，三家综合索引合成一档 `community`（那一档不逐家短路，理由见
    `metadata_routes.COMMUNITY_STAGE`）。`evidence` 是这一行的路径、文件名与账本
    厂牌——一本道与カリビアンコム 的番号同形，只有本机证据指着一本道时才问它。
    """
    return metadata_routes.stages_for_code(code, *evidence, overrides=route_overrides)


def _given_fields(entries):
    """这些证据条目一共给出了哪几个非空 Peach 字段。链上何时停手按它判。"""
    return {field for _, payload, _ in entries
            for field, value in extract_peach_fields(payload).items() if value}


def _asks_cover(code):
    """这个番号要不要问外部封面。MIB 同样不问，理由见 `_sources_for`。"""
    return bool(code) and not is_korean_mib_code(code)


def _scrapes_as_jav(row, code):
    """把账本行摊成 `catalog_rules.scrapes_as_jav` 要的那几样发行证据。

    `performers` 是取行时用 group_concat 带上的出演者投影；`asset` 上没有这一列。
    """
    return scrapes_as_jav(code, row.get('studio'), row.get('creator'), row.get('release_date'),
                          ('performer',) if row.get('performers') else (), row.get('region'))


def _studio_evidence(row):
    """判片商时本机手上有的证据：文件路径、文件名和账本里已记的厂牌。"""
    return (row.get('path'), row.get('name'), row.get('studio'))


def _missing_fields(row, target_key, groups, local_fields=()):
    """这一行还缺、本地资料没给、候选表里也还没有的字段。"""
    return [field for field in COLLECTED_FIELDS
            if field not in local_fields and f'{target_key}:{field}' not in groups
            and not row.get(COLUMN_OF.get(field, field))]


class _DirectoryIndex:
    """同一个文件夹只列一次。账本按 id 排，同目录的片子挨在一起，缓存几个目录就够。"""

    def __init__(self, limit=8):
        self._limit = limit
        self._cache: dict[str, dict[str, Path]] = {}

    def files(self, directory: Path) -> dict[str, Path]:
        key = str(directory)
        found = self._cache.get(key)
        if found is None:
            if len(self._cache) >= self._limit:
                del self._cache[next(iter(self._cache))]
            found = self._cache[key] = directory_files(directory)
        return found


def sources_fingerprint():
    """当前认得哪几家来源。记忆按它作废，接上新来源就不必等 TTL。

    `cover` 那条记的是「所有封面来源加起来都没有」，`community` 那条记的是「逐家问过
    都说没有」——两句话都以「当时会问哪几家」为前提。2026-09-21 接上 FC2 商品页与
    fc2cmadb 之后，430 个 FC2 番号手上还压着一条「封面没有」，按番号问是问不动的：
    答案没变，能问的人变了。
    """
    return hashlib.sha256('\n'.join(sorted(SOURCE_SPECS)).encode('utf-8')).hexdigest()[:12]


class _MissCache:
    """来源明确答复「没有」的番号，按来源分开记，期内不再问。

    r18.dev 不认识的番号每轮「只采集」都重问一遍，每条卡在主机 2 秒间隔上，答案永远一样；
    真实账本上这样的行有六百多条，一轮就是几十分钟。只记 `NotFound`：网络故障与超时
    下次可能就好了，不该记。每记一条就落盘，任务被打断也不丢。

    记忆还绑着写下它时的来源目录（`sources_fingerprint`）：目录一变整份作废，
    因为每条「没有」都是那一批来源给的答案。
    """

    def __init__(self, path, *, ttl=MISS_TTL_SECONDS, now=time.time,
                 fingerprint=None):
        self._path = path
        self._ttl = ttl
        self._now = now
        self._fingerprint = fingerprint if fingerprint is not None else sources_fingerprint()
        try:
            loaded = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            loaded = {}
        if not isinstance(loaded, dict) or loaded.get('sources') != self._fingerprint:
            loaded = {}
        self._entries = {}
        for source, codes in (loaded.get('misses') or {}).items():
            if isinstance(codes, dict):
                self._entries[source] = {code: float(stamp) for code, stamp in codes.items()
                                         if isinstance(stamp, (int, float))}

    def fresh(self, source, code):
        stamp = self._entries.get(source, {}).get(code)
        return stamp is not None and self._now() - stamp < self._ttl

    def record(self, source, code):
        now = self._now()
        self._entries.setdefault(source, {})[code] = now
        _save(self._path, {'sources': self._fingerprint, 'misses': {
            name: {key: stamp for key, stamp in codes.items() if now - stamp < self._ttl}
            for name, codes in self._entries.items()}})


class _RemoteSession:
    """一个任务共用的外部来源连接，加上来源说过「没有」的记忆。"""

    def __init__(self, config, provider_factory, misses, *, retrying, routes=None):
        self._config = config
        self._factory = provider_factory
        self._provider = None
        self.misses = misses
        #: 用户对每种内容类型的来源链覆盖，形状见 `metadata_routes.parse_route_overrides`。
        self._routes = routes or None
        # 「重试未完成项」按上一任务的失败集合强制重试，不看记忆；答复仍照记。
        self._consult = not retrying

    def provider(self):
        if self._provider is None:
            self._provider = (self._factory() if self._factory
                              else LibraryMetadataProvider(self._config.directory('secrets')))
        return self._provider

    def reset(self):
        if self._provider is not None and hasattr(self._provider, 'reset'):
            self._provider.reset()

    def close(self):
        if self._provider is not None and hasattr(self._provider, 'close'):
            self._provider.close()

    def collect(self, row, code, missing, cover_root, *, update, issue):
        """给这一行补外部资料与封面；返回 (证据条目, 新落盘的封面数)。

        文件名被读成番号的创作者作品一家都不问，判据见 `catalog_rules.scrapes_as_jav`；
        本地海报在调用方那一步已经登记过，这里跳过的只是外部来源。
        """
        entries, covers = [], 0
        if not _scrapes_as_jav(row, code):
            return entries, covers
        if missing and _sources_for(code, *_studio_evidence(row),
                                    route_overrides=self._routes):
            entries = self._metadata(row, code, missing, update=update, issue=issue)
        if _asks_cover(code) and not (cover_root / (code + '.jpg')).is_file():
            covers = self._cover(row, code, cover_root, update=update, issue=issue)
        return entries, covers

    def _evidence(self, source, code, payload):
        _save(self._evidence_path(code, source), payload)
        return (source, payload, self._evidence_path(code, source))

    def _evidence_path(self, code, source):
        return self._config.directory('sources') / 'library-metadata' / f'{code}-{source}.json'

    def _cached_evidence(self, names, code):
        """这一档上次答过的原始快照；命中就不发请求。

        有效期与「说过没有」的记忆同一个（`MISS_TTL_SECONDS`，7 天）：来源会补录、
        片子可能后来上架，两边同时到期才不会出现「没有」已经过期、「有」还压着旧值。
        「重试未完成项」强制重问，判据同 `self._consult`——那一趟要的就是新答复。
        """
        found = []
        for name in names:
            path = self._evidence_path(code, name)
            try:
                if time.time() - path.stat().st_mtime > MISS_TTL_SECONDS:
                    continue
                found.append((name, json.loads(path.read_text(encoding='utf-8')), path))
            except (OSError, ValueError):
                continue
        return found

    def _metadata(self, row, code, missing, *, update, issue):
        """按内容类型的来源链逐档问，必填标量字段够了就不问下一档。

        链在 `metadata_routes`：有码与素人先问 r18.dev，无码问一本道官网（本机证据指着
        它时），FC2 问发行方商品页与下架镜像，问不着才落到 AVBase、JavBus 与 javdb 那一档。

        短路判据是**这一行还缺的必填标量**（标题、演员、厂牌、发行日期），不是「有人答了
        就算」：r18.dev 少给演员时照旧往下问，否则那一行只能等人工去填。列表字段（标签、
        封面）不参与短路——多一家就多一批标签和一个图源，而免复核本来就要两家一致
        （ADR-0030、ADR-0034）、封面互证要两个图源（ADR-0032）。

        社区那一档的值照常进候选，只剩一家也补空，几家不一时取 javdb 的（ADR-0034）。
        每档各自记「没有」的记忆：说过没有的番号，一周内直接问下一档。
        """
        action = 'querying_metadata'
        budget = ACTION_BUDGETS[action]
        update(stage='采集缺失资料', current_action=action,
               current_started_at=time.time(), current_deadline_at=time.time() + budget)
        deadline = time.monotonic() + budget
        evidence = _studio_evidence(row)
        chain = metadata_routes.route_for_code(code, *evidence, overrides=self._routes)
        required = list(metadata_routes.required_scalars(missing))
        problems, entries = [], []
        for source in _sources_for(code, *evidence, route_overrides=self._routes):
            if self._consult and self.misses.fresh(source, code):
                continue
            cached = (self._cached_evidence(metadata_routes.stage_members(source, chain), code)
                      if self._consult else [])
            if cached:
                entries.extend(cached)
                if metadata_routes.settles(required, _given_fields(entries)):
                    break
                continue
            try:
                if source == 'r18dev':
                    found = [('r18dev', self.provider().query(code, 'r18dev', deadline=deadline))]
                elif source == 'fc2':
                    found = self.provider().fc2(code, deadline=deadline, route=chain)
                elif source == '1pondo':
                    found = self.provider().one_pondo(code, deadline=deadline)
                else:
                    found = self.provider().community(
                        code, deadline=deadline,
                        route=metadata_routes.community_route(
                            code, *evidence, overrides=self._routes))
            except DeadlineExceeded:
                self.reset()
                if entries:
                    break
                issue(row, '外部资料在预算时间内未取得，可稍后重试', action=action, retryable=True)
                return []
            except NotFound:
                self.misses.record(source, code)
                continue
            except Exception as error:
                # 社区那一档的原因里已经写明是哪一家了（`community()` 逐家拼过），再套一层
                # 就成了「社区来源：javdb：…」。单家来源的原因不带来源名，这里补上。
                problems.append(describe_failure(error) if source == 'community'
                                else f'{SOURCE_LABELS.get(source, source)}：{describe_failure(error)}')
                continue
            update(stage='保存资料候选')
            entries.extend(self._evidence(name, code, payload) for name, payload in found)
            if metadata_routes.settles(required, _given_fields(entries)):
                break
        if entries:
            return entries
        issue(row, '外部资料未取得：' + '；'.join(problems) if problems else MISS_MESSAGES[action],
              action=action, retryable=True)
        return []

    def _cover(self, row, code, cover_root, *, update, issue):
        action = 'fetching_cover'
        if self._consult and self.misses.fresh('cover', code):
            issue(row, MISS_MESSAGES[action], action=action, retryable=True)
            return 0
        budget = ACTION_BUDGETS[action]
        update(stage='采集缺失封面', current_action=action,
               current_started_at=time.time(), current_deadline_at=time.time() + budget)
        try:
            return int(self.provider().cover(code, cover_root, deadline=time.monotonic() + budget,
                                             evidence=_studio_evidence(row)))
        except DeadlineExceeded:
            self.reset()
            issue(row, '封面在预算时间内未取得，可稍后重试', action=action, retryable=True)
        except NotFound:
            self.misses.record('cover', code)
            issue(row, MISS_MESSAGES[action], action=action, retryable=True)
        except Exception as error:
            issue(row, f'封面未取得：{describe_failure(error)}', action=action, retryable=True)
        return 0


def _apply_finished_candidates(database, candidate_root, active):
    """候选落盘后立即执行窄规则自动落库；没有账本实例时只采集候选。

    停止后一条都不再写：任务已经不属于这次运行，用户按下停止之后账本还在变，
    是这个功能最难解释的一种表现。
    """
    if database is None or not active():
        return {'applied': 0}
    from .jav_cover_fetch import DEFAULT_METADATA_ROOT
    from .metadata_auto_apply import auto_apply_metadata
    # 快照目录是企划名义解析的证据来源（ADR-0038）。路径只有 `DEFAULT_METADATA_ROOT`
    # 一份定义，这里传它而不是再拼一次：两处各拼一份，改数据根时会有一处留在原地。
    return auto_apply_metadata(database, Path(candidate_root), active=active,
                               snapshot_root=DEFAULT_METADATA_ROOT)


def _enrich_finished_performers(database, groups, config, candidate_root, remote, active,
                                update=lambda **values: None,
                                issue=lambda asset, message, **options: None):
    """自动落库启用时补同一人物的资料；只采集候选时保持完全只读。"""
    empty = {'aliases': 0, 'avatars': 0, 'conflicts': 0, 'failed': 0}
    if database is None or not active():
        return empty
    from .metadata_performer_profiles import enrich_performer_profiles
    # 问题清单要的是这条资产的 id 和路径，候选行上都有。
    rows = {int(group['asset_id']): {'id': int(group['asset_id']),
                                     'path': group.get('asset_path') or ''}
            for group in groups.values() if str(group.get('asset_id') or '').isdigit()}
    return enrich_performer_profiles(
        database, groups.values(), config.directory('generated') / 'avatars',
        candidate_root / 'provider-cache' / 'performer-avatars',
        transport_factory=lambda: getattr(remote.provider(), 'transport', None),
        active=active, progress=update,
        # 头像取不到是可重试的：下一次「重试失败项」会连着这条资产一起再来一遍。
        issue=lambda asset_id, message: issue(rows.get(asset_id), message,
                                              action='fetching_cover', retryable=True),
    )


def _entity_watermark(database):
    """刮削开工前实体表的水位。拿不到就返回 None，后面据此整段跳过。"""
    if database is None:
        return None
    try:
        with database.read_connection() as connection:
            row = connection.execute("SELECT max(id) FROM entity").fetchone()
    except sqlite3.Error:
        return None
    return int(row[0] or 0)


def _avatar_followups(database, config, watermark):
    """这一轮新登记又没有头像的实体，一个一条补头像后继（ADR-0040）。

    只声明，不执行：派发在调用方结算这一轮时发生，真正去跑的是 `followups` 那一层。
    这里出任何问题都只让这一轮不派后继，不影响刮削本身的结论。
    """
    if database is None or watermark is None:
        return []
    from .avatar_followup import plan
    try:
        with database.read_connection() as connection:
            found = plan(connection, config.directory('generated') / 'avatars',
                         since_entity_id=watermark)
    except sqlite3.Error:
        return []
    return [{'key': item.key, 'task_key': item.task_key, 'label': item.label}
            for item in found]


def process_library(config, db_path, candidate_root, cover_root, *, location='configured',
                    report=lambda state: None, provider_factory=None, job_id=None,
                    retry_ids=None, active=lambda: True, stage=ALL_STAGES,
                    database=None, route_overrides=None):
    """登记文件与确定的番号，外部资料保留为可复核候选。

    `retry_ids` 为 `None` 时处理整个馆藏；给定时只处理这些项目（上一任务记录的
    可重试失败），不重新扫描来源目录，已有候选与封面照常复用。

    `stage` 把这条链分两段跑：`scan` 只走一遍来源目录把文件登记进馆藏，`collect`
    跳过那一遍、直接读本地资料并采集缺失的。新盘刚接上时要的是前者——几万个
    文件登记完就能用，不必等采集；采集被网络拖住时要的是后者，重跑不必再扫一遍
    磁盘。缺省两段都跑。

    `database` 是调用方已经在用的 `LedgerDatabase`。给了它才做收尾的自动落库与人物
    资料补齐，并且与调用方共用同一把进程内写锁；不给就只采集候选。

    `route_overrides` 覆盖某几种内容类型的来源链，形状与判据见
    `metadata_routes.parse_route_overrides`；不给就用内建那张表。
    """
    _require_writer(config, db_path)
    routes = metadata_routes.parse_route_overrides(route_overrides)
    path = state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    retrying = retry_ids is not None
    chosen_ids = list(dict.fromkeys(int(value) for value in (retry_ids or [])))
    with FileLock(str(path) + '.lock', timeout=0):
        state = dict(job_id=job_id or uuid.uuid4().hex, status='running',
                     stage='读取本地资料' if retrying else '扫描文件',
                     checked=0, total=0, scanned=0, identified=0, candidates=0, covers=0,
                     issue_count=0, issue_preview=[], issues_truncated=False, notes={},
                     retryable_asset_ids=[],
                     last_progress_at=time.time(), progress_seq=0,
                     current_asset_id=None, current_asset_name='', current_action='',
                     current_started_at=None, current_deadline_at=None,
                     followups=[],
                     started_at=time.time(), error='')
        # 实体表的水位在开工前记一次：比它大的实体就是这一轮建出来的（`_avatar_followups`）。
        entity_watermark = _entity_watermark(database)
        log_path = issues_path(config, state['job_id'])
        # 界面只展示前 20 条，完整清单在这个文件里；地址跟着状态一起给出，
        # 不让人按 job_id 自己去拼路径。
        state['issues_log'] = str(log_path)
        for stale in log_path.parent.glob('library-processing-*.issues.jsonl'):
            stale.unlink(missing_ok=True)

        saved_at = 0.0

        def flush_state(force=False):
            nonlocal saved_at
            if force or time.time() - saved_at >= STATE_FLUSH_SECONDS:
                _save(path, state)
                saved_at = time.time()

        def update(**values):
            _require_writer(config, db_path)
            if not active():
                raise InterruptedError('处理任务已停止')
            state.update(values)
            state['last_progress_at'] = time.time()
            state['progress_seq'] += 1
            flush_state(force='status' in values)
            report(dict(state))

        def issue(asset, message, *, action='', retryable=False):
            """`asset` 是这一项的馆藏行，来源离线一类与具体项目无关的问题给 `None`。

            每条问题都带上标题与路径：光有「NFO 无法解析」和一个链接，人得逐个点开
            才知道是哪个文件，而路径才是去磁盘上确认或改名时真正要用的东西。
            """
            asset = asset or {}
            asset_id = asset.get('id')
            title = str(asset.get('catalog_title') or '') or Path(str(asset.get('name') or '')).name
            asset_path = str(asset.get('path') or '')
            severity, retryable = _issue_classification(message, retryable)
            _record_issue(state, log_path, {
                'asset_id': asset_id, 'title': title, 'path': asset_path, 'message': message,
                'severity': severity, 'failed_action': action, 'retryable': retryable,
                'last_failed_at': time.time()})
            state['last_progress_at'] = time.time()
            flush_state()
            report(dict(state))

        update()
        remote = _RemoteSession(config, provider_factory, _MissCache(misses_path(config)),
                                retrying=retrying, routes=routes)
        flush_candidates = lambda force=False: None

        try:
            guard = DiskGuard(config.data_root, 1)
            guard.check(force=True)
            locations = config.locations if location == 'configured' else {location: config.locations[location]}
            mounts = {key: tuple(str(value) for value in values) for key, values in config.mounts.items()}
            online_roots = []
            for source, roots in locations.items():
                for root in roots:
                    guard.check()
                    if not root_online(translate_ledger_path(root)):
                        issue(None, f'{source} 来源离线', action='reading_local')
                        continue
                    online_roots.append(translate_ledger_path(root))
                    if not retrying and stage != COLLECT_STAGE:
                        result = scan_location(db_path, source, root, declared_roots=config.locations,
                                               mounts=mounts, report=lambda line: update(stage='扫描文件'))
                        state['scanned'] += result.files
            if stage == SCAN_STAGE:
                update(status='failed' if state['issue_count'] else 'complete',
                       stage='处理结束', completed_at=time.time(),
                       error=f"{state['issue_count']} 项需要处理，可重试未完成的部分。"
                             if state['issue_count'] else '')
                return state
            # 演员和标签是另外两张表，`asset` 上没有这两列。不带上它们，采集就把每部片都
            # 当成缺演员缺标签，逐个去问 r18，再把账本早就有的写法变成一道复核题。
            # `演员:` 是出演者在 `asset_tag` 上的扁平投影（ADR-0005），不算内容标签：
            # 算进来的话，一部片只要有演员就永远不缺标签，它的 genre 再也采不回来。
            # 本机实测 110 部片正好卡在这上面，`asset_tag` 里只有 `演员:` 那几行。
            multi = ("(SELECT group_concat(entity.canonical_name) FROM asset_entity"
                     " JOIN entity ON entity.id=asset_entity.entity_id"
                     " WHERE asset_entity.asset_id=asset.id AND entity.kind='performer') AS performers,"
                     " (SELECT group_concat(asset_tag.tag) FROM asset_tag"
                     " WHERE asset_tag.asset_id=asset.id AND asset_tag.tag NOT LIKE '演员:%') AS tags")
            if retrying:
                placeholders = ','.join('?' * len(chosen_ids))
                query = (f"SELECT asset.*, {multi} FROM asset WHERE id IN ({placeholders}) AND medium='video' "
                         "AND (disposal IS NULL OR disposal<>'trash') ORDER BY id")
                parameters = chosen_ids
            else:
                query = (f"SELECT asset.*, {multi} FROM asset "
                         "WHERE medium='video' AND (disposal IS NULL OR disposal<>'trash') ORDER BY id")
                parameters = []
            with closing(sqlite3.connect(db_path, timeout=30)) as connection:
                connection.row_factory = sqlite3.Row
                # 归属判断只比路径字面：声明根与账本路径同出一个口径，`resolve()` 在网盘
                # 挂载上是每行一次往返，几万行就是几分钟还没开始干活。
                rows = [dict(row) for row in connection.execute(query, parameters)
                        if row['location'] in locations
                        and any(translate_ledger_path(row['path']).is_relative_to(root) for root in online_roots)]
                # 用户在复核页收录过的 genre 从这一批起就是已知词，不该再作为未收录回来问一遍。
                genre_decisions = load_genre_decisions(connection)
            output = candidate_root / 'library-metadata-field-candidates.csv'
            groups = {row['item_key']: row for row in read_rows(output, missing_ok=True)}
            listing = _DirectoryIndex()
            csv_dirty = False
            csv_written_at = time.monotonic()

            def flush_candidates(force=False):
                nonlocal csv_dirty, csv_written_at
                if csv_dirty and (force or time.monotonic() - csv_written_at >= CANDIDATE_FLUSH_SECONDS):
                    write_rows(output, FIELDS, groups.values(), atomic=True)
                    csv_dirty = False
                    csv_written_at = time.monotonic()

            for index, row in enumerate(rows):
                guard.check()
                update(stage='读取本地资料', checked=index, total=len(rows),
                       current_asset_id=row['id'], current_asset_name=Path(str(row['name'] or '')).name,
                       current_action='reading_local', current_started_at=time.time(),
                       current_deadline_at=None)
                target_key = f"asset:{row['id']}"
                # 番号早已落库、字段都有着落、封面在位的行没有可采集的东西，连磁盘都不碰。
                # 重跑「只采集」时这是绝大多数行，每行省下的是网盘上的一次 stat 和一次列目录。
                if row['code'] and not _missing_fields(row, target_key, groups) and (
                        is_korean_mib_code(row['code']) or (cover_root / (row['code'] + '.jpg')).is_file()):
                    update(checked=index + 1, candidates=len(groups),
                           current_asset_id=None, current_asset_name='', current_action='',
                           current_started_at=None, current_deadline_at=None)
                    continue
                video = translate_ledger_path(row['path'])
                # 文件在不在看目录列表，不单独 stat：一部片一个文件夹的网盘上，那是每行一半的往返。
                try:
                    files = listing.files(video.parent)
                except OSError:
                    files = {}
                if video.name.casefold() not in files:
                    issue(row, '媒体文件不可访问', action='reading_local', retryable=True)
                    continue
                code = _provider_code(row['code']) or release_code_from_filename(row['name'])
                payload = None
                nfo, posters = sidecars(video, files)
                if nfo:
                    try:
                        payload, raw = read_nfo(nfo)
                        if payload['id'] and code and not same_release_code(code, payload['id']):
                            raise ValueError('文件名与 NFO 番号冲突，请复核')
                        code = code or _provider_code(payload['id'])
                    except (OSError, ValueError, ET.ParseError) as error:
                        issue(row, str(error), action='reading_local')
                        continue
                if not code and not payload:
                    # 没有番号不是问题项：账本里两万多行是创作者作品，本来就没有番号，
                    # 逐行报「未识别到番号」只会把真正要处理的几十条淹掉。它们只登记本地海报：
                    # 正片旁边的同名 PNG／JPG 落在 `{id}_4.jpg` 后卡片和详情直接用这一张。
                    try:
                        state['covers'] += int(_local_poster(
                            video, f"{row['id']}_4",
                            config.directory('generated') / 'posters', posters=posters))
                    except (OSError, ValueError):
                        issue(row, '本地封面无法读取', action='reading_local', retryable=True)
                    update(checked=index + 1, candidates=len(groups),
                           current_asset_id=None, current_asset_name='', current_action='',
                           current_started_at=None, current_deadline_at=None)
                    continue
                if code and not row['code']:
                    with closing(sqlite3.connect(db_path, timeout=30)) as connection, connection:
                        write_owned_fields(connection, [row['id']], {'code': code},
                                           SCAN_FILENAME, require_empty=True)
                    state['identified'] += 1
                try:
                    poster_root = cover_root if code else config.directory('generated') / 'posters'
                    state['covers'] += int(_local_poster(video, code or f"{row['id']}_4", poster_root, payload,
                                                         posters=posters))
                except (OSError, ValueError):
                    issue(row, '本地封面无法读取', action='reading_local', retryable=True)
                entries = []
                if payload:
                    evidence_path = config.directory('sources') / 'library-metadata' / (hashlib.sha256(raw).hexdigest() + '.nfo')
                    evidence_path.parent.mkdir(parents=True, exist_ok=True)
                    evidence_path.write_bytes(raw)
                    entries.append(('local_nfo', payload, evidence_path))
                local_fields = _fields(payload, genre_decisions) if payload else {}
                missing = _missing_fields(row, target_key, groups, local_fields)
                found, covers = remote.collect(row, code, missing, cover_root, update=update, issue=issue)
                entries.extend(found)
                state['covers'] += covers
                update(stage='保存资料候选', current_action='writing_candidates',
                       current_started_at=time.time(), current_deadline_at=None)
                for source, document, evidence_path in entries:
                    _merge_candidates(groups, row, code, source, document, evidence_path, genre_decisions,
                                      local_fields)
                if entries:
                    csv_dirty = True
                flush_candidates()
                update(checked=index + 1, candidates=len(groups),
                       current_asset_id=None, current_asset_name='', current_action='',
                       current_started_at=None, current_deadline_at=None)
            flush_candidates(force=True)
            # 候选完整落盘后立即执行调用方注入的窄规则，不再等人打开复核页才触发。
            # 核心处理层不反向依赖 Web 复核层；CLI 与 Web 两个组装入口都传入同一实现。
            auto_apply = _apply_finished_candidates(database, candidate_root, active)
            profiles = _enrich_finished_performers(
                database, groups, config, candidate_root, remote, active, update, issue)
            update(status='failed' if state['issue_count'] else 'complete', stage='处理结束',
                   checked=len(rows),
                   followups=_avatar_followups(database, config, entity_watermark),
                   auto_applied=auto_apply['applied'],
                   performer_aliases=profiles['aliases'], performer_avatars=profiles['avatars'],
                   performer_profile_conflicts=profiles['conflicts'],
                   performer_profile_failed=profiles['failed'],
                   error=f"{state['issue_count']} 项需要处理，可重试未完成的部分。" if state['issue_count'] else '',
                   completed_at=time.time(), current_asset_id=None, current_asset_name='',
                   current_action='', current_started_at=None, current_deadline_at=None)
        except Exception:
            state.update(status='failed', error='处理被中断。核对媒体目录后重试。', completed_at=time.time())
            _save(path, state)
            raise
        finally:
            # 被打断也把已经攒下的候选写全：文件里要么是上一份完整的，要么是这一份完整的。
            flush_candidates(force=True)
            remote.close()
        return state
