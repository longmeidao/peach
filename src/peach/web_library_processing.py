"""统一处理任务的启动、只读状态查询与失败项重试。"""
import json

from . import settings_file
from .library_processing import decorate, issues_path, process_library, snapshot


def _current(contract):
    live = contract.library_processing_job.snapshot()
    return live if live and live.get('status') == 'running' else snapshot(settings_file.active())


def q_library_processing(contract, _args):
    state = decorate(_current(contract))
    # 上一趟任务的状态文件里没有这个字段，而它那份完整清单还在磁盘上：按 job_id
    # 推出地址补回去，界面才有得可给。
    if state.get('issue_count') and state.get('job_id') and not state.get('issues_log'):
        path = issues_path(settings_file.active(), str(state['job_id']))
        if path.is_file():
            state['issues_log'] = str(path)
    return state


def q_library_processing_issues(contract, args):
    state = _current(contract)
    job_id = str(args.get('job_id') or '')
    if not job_id or job_id != str(state.get('job_id') or ''):
        raise ValueError('任务已变化，请刷新页面后重试')
    rows = []
    path = issues_path(settings_file.active(), job_id)
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    offset = max(0, int(args.get('offset') or 0))
    limit = max(1, min(200, int(args.get('limit') or 50)))
    return {'job_id': job_id, 'total': len(rows), 'offset': offset,
            'rows': rows[offset:offset + limit]}


def _retry_ids(previous, body):
    """请求带 `retry` 时按上一任务的失败集合重试；普通启动仍处理整个馆藏。

    返回 `None` 表示全量任务；返回列表表示只处理这些资产。空列表由调用方
    按「没有可重试项」处理，不允许滑回全库重跑。
    """
    if not body or 'retry' not in body:
        return None
    job_id = str(body.get('job_id') or '')
    if not job_id or job_id != str(previous.get('job_id') or ''):
        raise ValueError('原任务已变化，请刷新页面后重试')
    requested = body.get('retry')
    if not isinstance(requested, list):
        raise ValueError('重试项目格式无效')
    allowed = list(previous.get('retryable_asset_ids') or [])
    if not requested:
        return allowed
    chosen = []
    for value in requested:
        if not isinstance(value, int) or value not in allowed:
            raise ValueError('重试项目不属于原任务的失败集合')
        chosen.append(value)
    return chosen


def w_library_processing(contract, body):
    config = settings_file.active()
    if not config.configured or not config.locations:
        raise ValueError('请先添加媒体文件夹')
    if contract.db_path.resolve() != (config.directory('database') / 'ledger.db').resolve():
        raise ValueError('当前馆藏与媒体配置不一致')
    previous = snapshot(config)
    if previous.get('status') == 'running':
        return previous
    retry_ids = _retry_ids(previous, body)
    if retry_ids is not None and not retry_ids:
        return previous
    def work(job_id):
        try:
            result = process_library(config, contract.db_path, contract.candidate_root, contract.cover_root,
                job_id=job_id, retry_ids=retry_ids,
                active=lambda: (contract.library_processing_job.snapshot() or {}).get('job_id') == job_id,
                report=lambda state: contract.library_processing_job.update(job_id, **{
                    key: value for key, value in state.items() if key != 'job_id'}))
            contract.library_processing_job.update(job_id, **{key: value for key, value in result.items() if key != 'job_id'})
        finally:
            contract.cache_bust()
    return contract.library_processing_job.start(work, restart=True, initial={'stage': '准备处理'})
