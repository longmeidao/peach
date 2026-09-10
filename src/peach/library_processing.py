"""扫描、本地资料和缺失元数据采集共用一次有状态的处理任务。"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
import xml.etree.ElementTree as ET
from contextlib import closing
from pathlib import Path

from filelock import FileLock, Timeout
from PIL import Image

from .catalog_rules import is_korean_mib_code, release_code_from_filename, same_release_code
from .jav_cover_fetch import DeadlineExceeded
from .library_nfo import read_nfo, sidecars, local_art
from .metadata import extract_catalog_evidence, extract_peach_fields, identifies_code, validate_provider_code
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

#: 没有动作截止时间的阶段（本地读取）超过这么久没有心跳就在页面上预警。
STALL_AFTER_SECONDS = 120.0

#: 单项外部动作预算：资料查询覆盖一次请求加一轮重试，封面覆盖证据查询与候选往返。
#: 到点只结束当前项目并记为可重试，不让一个来源拖住整批任务。
ACTION_BUDGETS = {'querying_metadata': 90.0, 'fetching_cover': 240.0}


class LibraryMetadataProvider:
    """复用封面采集的 R18 JSON 入口与按来源配置的传输。"""
    def __init__(self, secrets_root):
        from .scraping_access import SourceTransport
        from .jav_cover_fetch import HostLimitedTransport
        self.transport = HostLimitedTransport(SourceTransport(secrets_root, max_requests=1000,
            max_bytes=128 * 1024 * 1024, max_seconds=3600), 2.0)

    def query(self, code, source='r18dev', *, deadline=None):
        from .jav_cover_fetch import R18_DETAIL, _fetch
        from urllib.parse import quote
        url = R18_DETAIL.format(code=quote(code))
        raw = json.loads(_fetch(self.transport, url, referer='https://r18.dev/',
                                limit=2 * 1024 * 1024, deadline=deadline))
        if not identifies_code(code, {'content_id': raw.get('content_id')}):
            raise ValueError('来源返回的番号不匹配')
        name = lambda key: (raw.get(key) or {}).get('name', '')
        return dict(id=code, content_id=raw.get('content_id'), source_url=url,
                    title=raw.get('title'), maker=name('maker'), series=name('series'),
                    release_date=raw.get('release_date'),
                    director=raw.get('director'), label=name('label'), runtime=raw.get('runtime_minutes'),
                    cover_url=(raw.get('images') or {}).get('jacket_image'),
                    actresses=[{'japanese_name': row.get('name', '')} for row in raw.get('actresses', [])],
                    genres=[row.get('name', '') for row in raw.get('categories', [])], raw=raw)

    def cover(self, code, cover_root, *, deadline=None):
        from .jav_cover_fetch import best_cover
        target = cover_root / (code + '.jpg')
        if target.is_file():
            return False
        candidate, size, data = best_cover(self.transport, code, 0, deadline=deadline)
        cover_root.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.processing.tmp')
        temporary.write_bytes(data)
        temporary.replace(target)
        _save(target.with_suffix('.scraping.json'), dict(source=candidate.source,
            source_url=candidate.url, width=size[0], height=size[1],
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
                    state.update(status='failed', error='处理被中断，请重试。',
                                 completed_at=state.get('last_progress_at') or time.time())
                    _save(state_path(config), state)
        except Timeout:
            pass
    return decorate(state)


def _local_poster(video, code, cover_root, payload=None):
    target = cover_root / (code + '.jpg')
    if target.is_file():
        return False
    _, posters = sidecars(video)
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
        cover_root.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.processing.tmp')
        image.convert('RGB').save(temporary, format='JPEG', quality=95)
        temporary.replace(target)
    return True


def _fields(payload):
    fields = extract_peach_fields(payload)
    evidence = extract_catalog_evidence(payload)
    for key in ('title', 'original_title'):
        if key in evidence:
            fields[key] = evidence[key]
    if payload.get('local_tags'):
        from .entities import canonicalize_entity_name
        values = list(dict.fromkeys(canonicalize_entity_name('tag', value) for value in payload['local_tags']))
        values = [value for value in values if value]
        if values:
            fields['tags'] = dict(value=values, display_value='、'.join(values), warnings=[])
    return fields


def process_library(config, db_path, candidate_root, cover_root, *, location='configured',
                    report=lambda state: None, provider_factory=None, job_id=None,
                    retry_ids=None, active=lambda: True):
    """登记文件与确定的番号，外部资料保留为可复核候选。

    `retry_ids` 为 `None` 时处理整个馆藏；给定时只处理这些项目（上一任务记录的
    可重试失败），不重新扫描来源目录，已有候选与封面照常复用。
    """
    def require_writer():
        if config.replication.enabled:
            from .sync import writer_device
            device_path = config.directory('state') / 'device-id'
            device = device_path.read_text(encoding='utf-8').strip() if device_path.is_file() else ''
            if not device or writer_device(Path(db_path), config.shared_root / 'database' / 'ledger.db') != device:
                raise ValueError('这台电脑是只读端，请在写入端扫描和导入资料')
    require_writer()
    path = state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    retrying = retry_ids is not None
    chosen_ids = list(dict.fromkeys(int(value) for value in (retry_ids or [])))
    with FileLock(str(path) + '.lock', timeout=0):
        state = dict(job_id=job_id or uuid.uuid4().hex, status='running',
                     stage='读取本地资料' if retrying else '扫描文件',
                     checked=0, total=0, scanned=0, identified=0, candidates=0, covers=0,
                     issue_count=0, issue_preview=[], issues_truncated=False,
                     retryable_asset_ids=[],
                     last_progress_at=time.time(), progress_seq=0,
                     current_asset_id=None, current_asset_name='', current_action='',
                     current_started_at=None, current_deadline_at=None,
                     started_at=time.time(), error='')
        log_path = issues_path(config, state['job_id'])
        # 界面只展示前 20 条，完整清单在这个文件里；地址跟着状态一起给出，
        # 不让人按 job_id 自己去拼路径。
        state['issues_log'] = str(log_path)
        for stale in log_path.parent.glob('library-processing-*.issues.jsonl'):
            stale.unlink(missing_ok=True)

        def update(**values):
            require_writer()
            if not active():
                raise InterruptedError('处理任务已停止')
            state.update(values)
            state['last_progress_at'] = time.time()
            state['progress_seq'] += 1
            _save(path, state)
            report(dict(state))

        def issue(asset, message, *, action='', retryable=False):
            """`asset` 是这一项的馆藏行，来源离线一类与具体项目无关的问题给 `None`。

            每条问题都带上标题与路径：光有「未识别到番号」和一个链接，人得逐个点开
            才知道是哪个文件，而路径才是去磁盘上确认或改名时真正要用的东西。
            """
            asset = asset or {}
            asset_id = asset.get('id')
            title = str(asset.get('catalog_title') or '') or Path(str(asset.get('name') or '')).name
            asset_path = str(asset.get('path') or '')
            with open(log_path, 'a', encoding='utf-8') as handle:
                handle.write(json.dumps({'asset_id': asset_id, 'title': title, 'path': asset_path,
                    'message': message, 'failed_action': action, 'retryable': retryable,
                    'last_failed_at': time.time()}, ensure_ascii=False) + '\n')
            state['issue_count'] += 1
            if len(state['issue_preview']) < ISSUE_PREVIEW_LIMIT:
                state['issue_preview'].append(dict(asset_id=asset_id, title=title,
                                                   path=asset_path, message=message))
            else:
                state['issues_truncated'] = True
            if retryable and asset_id is not None and asset_id not in state['retryable_asset_ids']:
                state['retryable_asset_ids'].append(asset_id)
            state['last_progress_at'] = time.time()
            _save(path, state)
            report(dict(state))

        update()
        provider = None

        def reset_provider():
            if provider is not None and hasattr(provider, 'reset'):
                provider.reset()

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
                    online_roots.append(translate_ledger_path(root).resolve())
                    if not retrying:
                        result = scan_location(db_path, source, root, declared_roots=config.locations,
                                               mounts=mounts, report=lambda line: update(stage='扫描文件'))
                        state['scanned'] += result.files
            if retrying:
                placeholders = ','.join('?' * len(chosen_ids))
                query = (f"SELECT * FROM asset WHERE id IN ({placeholders}) AND medium='video' "
                         "AND (disposal IS NULL OR disposal<>'trash') ORDER BY id")
                parameters = chosen_ids
            else:
                query = ("SELECT * FROM asset WHERE medium='video' AND (disposal IS NULL OR disposal<>'trash') "
                         "ORDER BY id")
                parameters = []
            with closing(sqlite3.connect(db_path, timeout=30)) as connection:
                connection.row_factory = sqlite3.Row
                rows = [dict(row) for row in connection.execute(query, parameters)
                        if row['location'] in locations
                        and any(translate_ledger_path(row['path']).resolve().is_relative_to(root) for root in online_roots)]
            output = candidate_root / 'library-metadata-field-candidates.csv'
            groups = {row['item_key']: row for row in read_rows(output, missing_ok=True)}
            for index, row in enumerate(rows):
                guard.check()
                update(stage='读取本地资料', checked=index, total=len(rows),
                       current_asset_id=row['id'], current_asset_name=Path(str(row['name'] or '')).name,
                       current_action='reading_local', current_started_at=time.time(),
                       current_deadline_at=None)
                video = translate_ledger_path(row['path'])
                if not video.is_file():
                    issue(row, '媒体文件不可访问', action='reading_local', retryable=True)
                    continue
                code = row['code'] or release_code_from_filename(row['name'])
                payload = None
                nfo, _ = sidecars(video)
                if nfo:
                    try:
                        payload, raw = read_nfo(nfo)
                        if payload['id'] and code and not same_release_code(code, payload['id']):
                            raise ValueError('文件名与 NFO 番号冲突，请复核')
                        code = code or payload['id']
                    except (OSError, ValueError, ET.ParseError) as error:
                        issue(row, str(error), action='reading_local')
                        continue
                if not code and not payload:
                    # 番号认不出不影响本地封面：正片旁边的同名 PNG／JPG 就是它的海报，
                    # 落在 `{id}_4.jpg` 后卡片和详情直接用这一张，不再回退九宫格。
                    try:
                        state['covers'] += int(_local_poster(
                            video, f"{row['id']}_4",
                            config.directory('generated') / 'posters'))
                    except (OSError, ValueError):
                        issue(row, '本地封面无法读取', action='reading_local', retryable=True)
                    issue(row, '未识别到番号，请在详情中补充资料', action='reading_local')
                    continue
                if code:
                    try:
                        code = validate_provider_code(code)
                    except ValueError:
                        issue(row, '番号格式无效，请复核影片资料', action='reading_local')
                        continue
                if code and not row['code']:
                    with closing(sqlite3.connect(db_path, timeout=30)) as connection, connection:
                        connection.execute("UPDATE asset SET code=? WHERE id=? AND (code IS NULL OR code='')", (code, row['id']))
                    state['identified'] += 1
                try:
                    poster_root = cover_root if code else config.directory('generated') / 'posters'
                    state['covers'] += int(_local_poster(video, code or f"{row['id']}_4", poster_root, payload))
                except (OSError, ValueError):
                    issue(row, '本地封面无法读取', action='reading_local', retryable=True)
                entries = []
                if payload:
                    evidence_path = config.directory('sources') / 'library-metadata' / (hashlib.sha256(raw).hexdigest() + '.nfo')
                    evidence_path.parent.mkdir(parents=True, exist_ok=True)
                    evidence_path.write_bytes(raw)
                    entries.append(('local_nfo', payload, evidence_path))
                local_fields = _fields(payload) if payload else {}
                target_key = f"asset:{row['id']}"
                missing = [field for field in ('title', 'performers', 'studio', 'release_date', 'tags')
                           if field not in local_fields and f'{target_key}:{field}' not in groups
                           and not row.get({'title': 'catalog_title'}.get(field, field))]
                # 韩国 MIB 的编号不在 JAV 目录站上，资料与封面都不问：番号相同的日本作品
                # 会原样通过番号核验，取回来的是别的片。
                jav_catalog = bool(code) and not is_korean_mib_code(code)
                if missing and jav_catalog:
                    budget = ACTION_BUDGETS['querying_metadata']
                    update(stage='采集缺失资料', current_action='querying_metadata',
                           current_started_at=time.time(),
                           current_deadline_at=time.time() + budget)
                    try:
                        if provider is None:
                            provider = provider_factory() if provider_factory else LibraryMetadataProvider(config.directory('secrets') / 'follow')
                        external = provider.query(code, 'r18dev',
                                                  deadline=time.monotonic() + budget)
                        update(stage='保存资料候选')
                        evidence_path = config.directory('sources') / 'library-metadata' / (code + '-r18dev.json')
                        _save(evidence_path, external)
                        entries.append(('r18dev', external, evidence_path))
                    except DeadlineExceeded:
                        reset_provider()
                        issue(row, '外部资料在预算时间内未取得，可稍后重试',
                              action='querying_metadata', retryable=True)
                    except Exception:
                        issue(row, '外部资料未取得，请检查采集来源后重试',
                              action='querying_metadata', retryable=True)
                if jav_catalog and not (cover_root / (code + '.jpg')).is_file():
                    budget = ACTION_BUDGETS['fetching_cover']
                    update(stage='采集缺失封面', current_action='fetching_cover',
                           current_started_at=time.time(),
                           current_deadline_at=time.time() + budget)
                    try:
                        if provider is None:
                            provider = provider_factory() if provider_factory else LibraryMetadataProvider(config.directory('secrets') / 'follow')
                        state['covers'] += int(provider.cover(code, cover_root,
                                                              deadline=time.monotonic() + budget))
                    except DeadlineExceeded:
                        reset_provider()
                        issue(row, '封面在预算时间内未取得，可稍后重试',
                              action='fetching_cover', retryable=True)
                    except Exception:
                        issue(row, '封面未取得，请检查采集来源后重试',
                              action='fetching_cover', retryable=True)
                update(stage='保存资料候选', current_action='writing_candidates',
                       current_started_at=time.time(), current_deadline_at=None)
                for source, document, evidence_path in entries:
                    for field, value in _fields(document).items():
                        key = f'{target_key}:{field}'
                        identity = hashlib.sha256(json.dumps([source, value['value']], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                        candidate = dict(candidate_key=identity, source=source, provider='local-nfo' if source == 'local_nfo' else 'r18-json',
                                         value=value['value'], display_value=value.get('display_value', str(value['value'])),
                                         warnings=value.get('warnings', []), confidence=0.9 if source == 'local_nfo' else 0.75,
                                         source_url=document.get('source_url', ''), raw_snapshot=str(evidence_path),
                                         source_kind='local' if source == 'local_nfo' else 'official_mirror', official=False,
                                         catalog_evidence=extract_catalog_evidence(document))
                        group = groups.get(key, dict(item_key=key, code=code or '', query=code or row['name'],
                            asset_id=row['id'], asset_path=row['path'], field=field,
                            field_label=LABELS[field], current_value=row.get({'title': 'catalog_title'}.get(field, field)) or '',
                            candidates_json='[]', source_count=0, source_profile='library', policy_version='library-v1',
                            status='candidate', size_gb=round((row['size'] or 0)/1024**3, 2), videos=1, fetched_at=''))
                        choices = [entry for entry in json.loads(group['candidates_json']) if entry['source'] != source]
                        choices.append(candidate)
                        group.update(candidates_json=json.dumps(choices, ensure_ascii=False), source_count=len(choices),
                                     fetched_at=time.strftime('%Y-%m-%d %H:%M:%S'))
                        groups[key] = group
                write_rows(output, FIELDS, groups.values(), atomic=True)
                update(checked=index + 1, candidates=len(groups),
                       current_asset_id=None, current_asset_name='', current_action='',
                       current_started_at=None, current_deadline_at=None)
            update(status='failed' if state['issue_count'] else 'complete', stage='处理结束',
                   checked=len(rows),
                   error=f"{state['issue_count']} 项需要处理，请查看详情并重试。" if state['issue_count'] else '',
                   completed_at=time.time(), current_asset_id=None, current_asset_name='',
                   current_action='', current_started_at=None, current_deadline_at=None)
        except Exception:
            state.update(status='failed', error='处理被中断，请检查媒体目录后重试。', completed_at=time.time())
            _save(path, state)
            raise
        finally:
            if provider is not None and hasattr(provider, 'close'):
                provider.close()
        return state

