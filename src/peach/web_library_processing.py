"""统一处理任务的启动与只读状态查询。"""
from . import settings_file
from .library_processing import process_library, snapshot


def q_library_processing(contract, _args):
    live = contract.library_processing_job.snapshot()
    return live if live and live.get('status') == 'running' else snapshot(settings_file.active())


def w_library_processing(contract, _body):
    config = settings_file.active()
    if not config.configured or not config.locations:
        raise ValueError('请先添加媒体文件夹')
    if contract.db_path.resolve() != (config.directory('database') / 'ledger.db').resolve():
        raise ValueError('当前馆藏与媒体配置不一致')
    previous = snapshot(config)
    if previous.get('status') == 'running':
        return previous
    def work(job_id):
        try:
            result = process_library(config, contract.db_path, contract.candidate_root, contract.cover_root,
                job_id=job_id,
                active=lambda: (contract.library_processing_job.snapshot() or {}).get('job_id') == job_id,
                report=lambda state: contract.library_processing_job.update(job_id, **{
                    key: value for key, value in state.items() if key != 'job_id'}))
            contract.library_processing_job.update(job_id, **{key: value for key, value in result.items() if key != 'job_id'})
        finally:
            contract.cache_bust()
    return contract.library_processing_job.start(work, restart=True, initial={'stage': '准备处理'})
