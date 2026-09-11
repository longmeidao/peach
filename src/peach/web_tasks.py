"""任务中心的读取端点：活动页要的那一份，一次请求拿全。

页面一屏上要同时回答三件事——谁在跑、刚才跑完的怎么样、有哪一轮被挡掉了。分成三个
端点意味着三次轮询、三份各自可能过期的快照，还得在前端再拼一次时间线。所以
`/api/tasks` 不带筛选时直接把这三段一起下发；带 `status`／`task_key` 时才退回成一张
普通的筛选列表，留给排查用。
"""
from __future__ import annotations

import sqlite3

from .task_runs import ACTIVE_STATUSES, TERMINAL_STATUSES

#: 不带筛选时「最近完成」那一段的默认条数。一屏看得完，再多就该去筛了。
RECENT_LIMIT = 20

#: 账本还没跑到 0028 时页面上显示这一句。迁移是单独一步，升级后第一次打开活动页
#: 撞上没有这张表是正常路径，不该是一个 500。
NO_TABLE = "账本还没有任务中心的表，执行一次 peach migrate --apply 就好"


def q_tasks(contract, args):
    try:
        return _tasks(contract, args)
    except sqlite3.OperationalError:
        # 只可能是这张表还不存在——这个函数别的地方不碰库。
        return {"ok": True, "filtered": False, "available": False,
                "message": NO_TABLE, "running": [], "skipped": [], "finished": [],
                "statuses": {"active": list(ACTIVE_STATUSES),
                             "finished": list(TERMINAL_STATUSES)}}


def _tasks(contract, args):
    status = str((args or {}).get("status") or "").strip()
    task_key = str((args or {}).get("task_key") or "").strip()
    limit = _limit(args)
    if status or task_key:
        rows = contract.task_runs.query(status=status, task_key=task_key, limit=limit)
        return {"ok": True, "filtered": True, "available": True,
                "runs": [row.payload() for row in rows]}
    running = contract.task_runs.query(status="active", limit=limit)
    finished = contract.task_runs.query(status="finished", limit=limit)
    return {
        "ok": True,
        "filtered": False,
        "available": True,
        "running": [row.payload() for row in running],
        # 被挡掉的那些也在 `finished` 里（它们是 `cancelled`），这里单独再挑一份：
        # 「为什么没跑」是用户来这一页的主要问题，不该让他在完成列表里自己找。
        "skipped": [row.payload() for row in finished
                    if row.status == "cancelled" and "blocked_by" in row.result_summary],
        "finished": [row.payload() for row in finished],
        "statuses": {"active": list(ACTIVE_STATUSES), "finished": list(TERMINAL_STATUSES)},
    }


def q_task(contract, run_id):
    run = contract.task_runs.get(int(run_id))
    if run is None:
        # KeyError 在 API 层被翻成 404；ValueError 会变成 400，那是参数错，不是这里的事。
        raise KeyError(f"没有第 {run_id} 轮任务")
    return {"ok": True, "run": run.payload()}


def _limit(args) -> int:
    raw = (args or {}).get("limit")
    if raw in (None, ""):
        return RECENT_LIMIT
    return max(1, min(int(raw), 500))
