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

from .catalog_rules import release_code_from_filename, same_release_code
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


class LibraryMetadataProvider:
    """复用封面采集的 R18 JSON 入口与按来源配置的传输。"""
    def __init__(self, secrets_root):
        from .scraping_access import SourceTransport
        from .jav_cover_fetch import HostLimitedTransport
        self.transport = HostLimitedTransport(SourceTransport(secrets_root, max_requests=1000,
            max_bytes=128 * 1024 * 1024, max_seconds=3600), 2.0)

    def query(self, code, source='r18dev'):
        from .jav_cover_fetch import R18_DETAIL, _fetch
        from urllib.parse import quote
        url = R18_DETAIL.format(code=quote(code))
        raw = json.loads(_fetch(self.transport, url, referer='https://r18.dev/', limit=2 * 1024 * 1024))
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

    def close(self):
        self.transport.close()

    def cover(self, code, cover_root):
        from .jav_cover_fetch import best_cover
        target = cover_root / (code + '.jpg')
        if target.is_file():
            return False
        candidate, size, data = best_cover(self.transport, code, 0)
        cover_root.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.processing.tmp')
        temporary.write_bytes(data)
        temporary.replace(target)
        _save(target.with_suffix('.scraping.json'), dict(source=candidate.source,
            source_url=candidate.url, width=size[0], height=size[1],
            raw_sha256=hashlib.sha256(data).hexdigest(), checked_at=time.time()))
        return True


def state_path(config):
    return config.directory('state') / 'library-processing.json'


def _save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


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
                    state.update(status='failed', error='处理被中断，请重试。')
        except Timeout:
            pass
    return state


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
                    report=lambda state: None, provider_factory=None, job_id=None, active=lambda: True):
    """登记文件与确定的番号，外部资料保留为可复核候选。"""
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
    with FileLock(str(path) + '.lock', timeout=0):
        state = dict(job_id=job_id or uuid.uuid4().hex, status='running', stage='扫描文件',
                     checked=0, total=0, scanned=0, identified=0, candidates=0, covers=0,
                     issues=[], started_at=time.time(), error='')
        def update(**values):
            require_writer()
            if not active():
                raise InterruptedError('处理任务已停止')
            state.update(values)
            _save(path, state)
            report(dict(state))
        def issue(asset_id, message):
            state['issues'].append({'asset_id': asset_id, 'message': message})
        update()
        provider = None
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
                        issue(None, f'{source} 来源离线')
                        continue
                    online_roots.append(translate_ledger_path(root).resolve())
                    result = scan_location(db_path, source, root, declared_roots=config.locations,
                                           mounts=mounts, report=lambda line: update(stage='扫描文件'))
                    state['scanned'] += result.files
            with closing(sqlite3.connect(db_path, timeout=30)) as connection:
                connection.row_factory = sqlite3.Row
                rows = [dict(row) for row in connection.execute(
                    "SELECT * FROM asset WHERE medium='video' AND (disposal IS NULL OR disposal<>'trash') "
                    "ORDER BY id") if row['location'] in locations
                    and any(translate_ledger_path(row['path']).resolve().is_relative_to(root) for root in online_roots)]
            output = candidate_root / 'library-metadata-field-candidates.csv'
            groups = {row['item_key']: row for row in read_rows(output, missing_ok=True)}
            for index, row in enumerate(rows):
                guard.check()
                update(stage='读取本地资料', checked=index, total=len(rows))
                video = translate_ledger_path(row['path'])
                if not video.is_file():
                    issue(row['id'], '媒体文件不可访问')
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
                        issue(row['id'], str(error))
                        continue
                if not code and not payload:
                    issue(row['id'], '未识别到番号，请在详情中补充资料')
                    continue
                if code:
                    try:
                        code = validate_provider_code(code)
                    except ValueError:
                        issue(row['id'], '番号格式无效，请复核影片资料')
                        continue
                if code and not row['code']:
                    with closing(sqlite3.connect(db_path, timeout=30)) as connection, connection:
                        connection.execute("UPDATE asset SET code=? WHERE id=? AND (code IS NULL OR code='')", (code, row['id']))
                    state['identified'] += 1
                try:
                    poster_root = cover_root if code else config.directory('generated') / 'posters'
                    state['covers'] += int(_local_poster(video, code or f"{row['id']}_4", poster_root, payload))
                except (OSError, ValueError):
                    issue(row['id'], '本地封面无法读取')
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
                if missing and code:
                    update(stage='采集缺失资料')
                    try:
                        if provider is None:
                            provider = provider_factory() if provider_factory else LibraryMetadataProvider(config.directory('secrets') / 'follow')
                        external = provider.query(code, 'r18dev')
                        update(stage='保存资料候选')
                        evidence_path = config.directory('sources') / 'library-metadata' / (code + '-r18dev.json')
                        _save(evidence_path, external)
                        entries.append(('r18dev', external, evidence_path))
                    except Exception:
                        issue(row['id'], '外部资料未取得，请检查采集来源后重试')
                if code and not (cover_root / (code + '.jpg')).is_file():
                    update(stage='采集缺失封面')
                    try:
                        if provider is None:
                            provider = provider_factory() if provider_factory else LibraryMetadataProvider(config.directory('secrets') / 'follow')
                        state['covers'] += int(provider.cover(code, cover_root))
                    except Exception:
                        issue(row['id'], '封面未取得，请检查采集来源后重试')
                update(stage='保存资料候选')
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
                update(checked=index + 1, candidates=len(groups))
            update(status='failed' if state['issues'] else 'complete', stage='处理结束', checked=len(rows),
                   error=f"{len(state['issues'])} 项需要处理，请查看详情并重试。" if state['issues'] else '', completed_at=time.time())
        except Exception:
            state.update(status='failed', error='处理被中断，请检查媒体目录后重试。', completed_at=time.time())
            _save(path, state)
            raise
        finally:
            if provider is not None and hasattr(provider, 'close'):
                provider.close()
        return state
