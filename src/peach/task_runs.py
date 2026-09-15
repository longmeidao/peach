"""任务中心：一张 `task_run` 表的写入、互斥、租约与查询。

各域的执行细节仍归各域（`BackgroundJob` 的状态字典、`library_processing` 的动作预算、
追更调度器的退避计数）。这里只维护对外那一层：谁在跑、跑到哪、什么时候结束的、
为什么没跑。表的取舍写在 `migrations/0028_task_runs.sql`。

三条不变量，全部由这个模块和那张表一起守住：

1. **终态一次性**。`finish` 是一条带 `WHERE status IN (活跃态)` 的 UPDATE，从终态改回
   活跃态不可能发生，重复结算也只有第一次生效。租约回收和任务自己收尾撞在一起时，
   落地的是先到的那一个。
2. **互斥由 `INSERT` 判**。撞上部分唯一索引才算冲突，不先查一遍——先查再插之间那个
   时间窗正是「两轮同时开跑」的来源。
3. **跳过也是一条记录**。定时触发撞上在跑的那轮会写一条 `cancelled`，带上挡路那条的
   id。跳过只留在内存里的话，「刚才那轮为什么没跑」就永远答不出来。
"""
from __future__ import annotations

import json
import os
import socket
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from .jobs import TaskRunConflict, process_alive
from .repository import LedgerDatabase

__all__ = [
    "ACTIVE_STATUSES", "DEFAULT_KEEP", "LEASE_SECONDS", "PROGRESS_INTERVAL",
    "TASK_LABELS", "TERMINAL_STATUSES", "TRIGGERS", "TaskRun", "TaskRunConflict",
    "TaskRunHandle", "TaskRunStore", "cli_run", "stamp", "task_label",
]

#: 未结束的两种状态。部分唯一索引和每一条 CAS 的 WHERE 都用这一份。
ACTIVE_STATUSES = ("pending", "running")
#: 终态。只有这四种能进 `finish`，也只有这四种会被 `prune` 回收。
TERMINAL_STATUSES = ("succeeded", "failed", "cancelled", "interrupted")
TRIGGERS = ("manual", "scheduled", "startup", "cli")

#: 心跳超过这么久没续，且进程也不在了，就按被打断处理。
#: 取 5 分钟不是因为任务不会更久——单项外部动作的预算是 240 秒（`library_processing`
#: 的 `ACTION_BUDGETS`），比它短就会把正常的慢任务判成死掉的。
LEASE_SECONDS = 300.0

#: 进度与心跳的默认写入间隔。扫描一万个文件时每项都写一次库，等于给每一项加一次
#: 写事务；页面两秒轮询一次，比这更密的进度没有读者。
PROGRESS_INTERVAL = 2.0

#: 每个 task_key 默认保留多少条终态记录。活动页只看最近几轮，更早的属于日志。
DEFAULT_KEEP = 20

#: 任务登记表：key → 给人看的名字。不在表里的 key 由界面原样显示，不猜。
TASK_LABELS = {
    "follow-check": "追更检查",
    "follow-resolve": "关注来源查找",
    "library-processing": "扫描与采集",
    "taste-refresh": "口味分析",
    "link-check": "链接检查",
    "link-prune": "失效链接清理",
    "resource-scan": "资源对账扫描",
    "resource-apply": "资源对账执行",
    "scraping-cover": "封面采集",
    "media-repair": "播放兼容修复",
    "batch": "批量操作",
    "scrape-codes": "番号资料刮削",
    "jav-covers": "封面批量抓取",
}


#: 触发方式的中文名。跳过原因是给人看的一句话，里面不留英文枚举值。
TRIGGER_LABELS = {
    "manual": "手动", "scheduled": "定时", "startup": "启动", "cli": "命令行",
}


def task_label(task_key: str) -> str:
    return TASK_LABELS.get(task_key, task_key)


def trigger_label(trigger: str) -> str:
    return TRIGGER_LABELS.get(trigger, trigger)


def stamp(moment: datetime | None = None) -> str:
    """ISO-8601 UTC 文本，与 `entity`、`follow_schedule` 同一种写法。"""
    return (moment or datetime.now(timezone.utc)).astimezone(
        timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class TaskRun:
    id: int
    task_key: str
    trigger: str
    status: str
    mutex_key: str | None
    pid: int | None
    host: str
    started_at: str | None
    finished_at: str | None
    heartbeat_at: str | None
    progress_current: int | None
    progress_total: int | None
    progress_label: str
    result_summary: dict
    error: str

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def payload(self) -> dict:
        """API 与页面共用的投影。派生字段在这里算一次，不让每个读者各算一份。"""
        started, finished = _parse(self.started_at), _parse(self.finished_at)
        end = finished or (datetime.now(timezone.utc) if self.active else None)
        return {
            "id": self.id,
            "task_key": self.task_key,
            "task_label": task_label(self.task_key),
            "trigger": self.trigger,
            "status": self.status,
            "mutex_key": self.mutex_key,
            "pid": self.pid,
            "host": self.host,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "heartbeat_at": self.heartbeat_at,
            "elapsed_seconds": (
                round((end - started).total_seconds(), 1)
                if started and end else None),
            "progress_current": self.progress_current,
            "progress_total": self.progress_total,
            "progress_label": self.progress_label,
            "result_summary": self.result_summary,
            "error": self.error,
        }


_COLUMNS = ("id,task_key,trigger,status,mutex_key,pid,host,started_at,finished_at,"
            "heartbeat_at,progress_current,progress_total,progress_label,"
            "result_summary,error")


def _row(row: sqlite3.Row) -> TaskRun:
    try:
        summary = json.loads(row["result_summary"] or "{}")
    except ValueError:
        summary = {}
    return TaskRun(
        id=row["id"], task_key=row["task_key"], trigger=row["trigger"],
        status=row["status"], mutex_key=row["mutex_key"], pid=row["pid"],
        host=row["host"] or "", started_at=row["started_at"],
        finished_at=row["finished_at"], heartbeat_at=row["heartbeat_at"],
        progress_current=row["progress_current"], progress_total=row["progress_total"],
        progress_label=row["progress_label"] or "",
        result_summary=summary if isinstance(summary, dict) else {},
        error=row["error"] or "",
    )


class TaskRunStore:
    """`task_run` 的唯一写入口。

    `enabled=False` 时所有写入是空操作而读取照常：只读端（macOS）的账本是写入端的
    副本，在那里写一行任务记录等于制造一处永远合不回去的分叉。读得到写入端在跑什么
    仍然有用，所以只关写。
    """

    def __init__(self, database: LedgerDatabase | Path | str, *,
                 enabled: bool = True, host: str | None = None):
        self.database = (database if isinstance(database, LedgerDatabase)
                         else LedgerDatabase(Path(database)))
        self.enabled = bool(enabled)
        self.host = host if host is not None else socket.gethostname()
        self._lock = threading.Lock()
        #: run_id → 上一次写进度的单调时钟。节流只看这一份，不查库。
        self._last_write: dict[int, float] = {}

    def available(self) -> bool:
        """这本账本上有没有 `task_run` 表。

        迁移不是服务启动时自动跑的（`peach migrate --apply` 是单独一步），所以升级
        之后第一次启动完全可能撞上没有这张表的账本。那时候不能让每个按钮都炸成 500：
        调用方据此把整个任务中心关掉，各域的任务照常能跑，只是这一轮不留记录。
        """
        try:
            self.query(limit=1)
            return True
        except sqlite3.OperationalError:
            return False

    # -- 写入 --------------------------------------------------------------

    def start(self, task_key: str, *, trigger: str, mutex_key: str | None = None,
              conflict: str = "skip", total: int | None = None,
              label: str = "", pid: int | None = None) -> TaskRun | None:
        """开一轮。互斥冲突时按 `conflict` 处理，返回 None 或抛 `TaskRunConflict`。

        `conflict="skip"` 是定时触发的语义：本轮不跑，但要留下一条记录说明被谁挡了。
        `conflict="raise"` 是手动触发的语义：告诉用户是哪一轮挡着，让他自己决定。
        """
        if trigger not in TRIGGERS:
            raise ValueError(f"未知的触发方式：{trigger}")
        if conflict not in ("skip", "raise"):
            raise ValueError(f"未知的冲突处理方式：{conflict}")
        if not self.enabled:
            return None
        moment = stamp()
        try:
            with self.database.write_transaction(notify=False) as connection:
                cursor = connection.execute(
                    "INSERT INTO task_run(task_key,trigger,status,mutex_key,pid,host,"
                    "started_at,heartbeat_at,progress_current,progress_total,"
                    "progress_label,result_summary) "
                    "VALUES(?,?,'running',?,?,?,?,?,0,?,?,'{}')",
                    (task_key, trigger, mutex_key, pid if pid is not None else os.getpid(),
                     self.host, moment, moment, total, label))
                run_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            if mutex_key is None:
                # 没声明互斥还撞上约束，说明坏的是别的东西（CHECK、列约束），
                # 把它当成冲突就是把真故障藏起来。
                raise
            blocking = self.blocking(mutex_key)
            if conflict == "raise":
                raise TaskRunConflict(
                    task_key, blocking.id if blocking else None) from None
            self._record_skip(task_key, trigger, mutex_key, blocking)
            return None
        # 这里刻意不给节流打时间戳：开工那一刻还不知道要做多少件，第一次进度报上来的
        # 才是真正能看的那一行。把它一起节流掉，活动页开头两秒只有一句「进行中」。
        return self.get(run_id)

    def _record_skip(self, task_key: str, trigger: str, mutex_key: str,
                     blocking: TaskRun | None) -> None:
        """把一次静默跳过写成终态记录。它没有 `started_at`——这一轮从没开跑。"""
        reason = (f"与第 {blocking.id} 轮（{trigger_label(blocking.trigger)}触发）冲突，本次跳过"
                  if blocking else "已有一轮在进行，本次跳过")
        summary = json.dumps({"blocked_by": blocking.id if blocking else None},
                             ensure_ascii=False)
        with self.database.write_transaction(notify=False) as connection:
            connection.execute(
                "INSERT INTO task_run(task_key,trigger,status,mutex_key,pid,host,"
                "finished_at,result_summary,error) "
                "VALUES(?,?,'cancelled',?,?,?,?,?,?)",
                (task_key, trigger, mutex_key, os.getpid(), self.host,
                 stamp(), summary, reason))

    def progress(self, run_id: int | None, *, current: int | None = None,
                 total: int | None = None, label: str | None = None,
                 throttle: float = PROGRESS_INTERVAL) -> bool:
        """推进度并顺带续租。已经进终态的行不再接受进度。

        `throttle` 是墙钟节流：页面两秒轮询一次，比这更密的写入没有读者，只有代价。
        收尾前那一次要看到真实的最终计数，调用方传 `throttle=0`。
        """
        if not self.enabled or run_id is None or not self._due(run_id, throttle):
            return False
        assignments = ["heartbeat_at=?"]
        values: list[object] = [stamp()]
        for column, value in (("progress_current", current),
                              ("progress_total", total),
                              ("progress_label", label)):
            if value is not None:
                assignments.append(f"{column}=?")
                values.append(value)
        return self._update_active(run_id, assignments, values)

    def heartbeat(self, run_id: int | None, *,
                  throttle: float = PROGRESS_INTERVAL) -> bool:
        """只续租。没有计数可报、但确实还活着的阶段用它。"""
        if not self.enabled or run_id is None or not self._due(run_id, throttle):
            return False
        return self._update_active(run_id, ["heartbeat_at=?"], [stamp()])

    def finish(self, run_id: int | None, status: str, *, summary: dict | None = None,
               error: str = "") -> bool:
        """结算。只能从活跃态进终态，一条 UPDATE 带 WHERE 做 CAS。

        返回是否由本次调用落地。`False` 表示这一轮已经被别人结算过——租约回收和任务
        自己收尾撞在一起就是这种情形，后到的那个不许覆盖。
        """
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"{status} 不是终态")
        if not self.enabled or run_id is None:
            return False
        moment = stamp()
        done = self._update_active(
            run_id,
            ["status=?", "finished_at=?", "heartbeat_at=?", "result_summary=?", "error=?"],
            [status, moment, moment,
             json.dumps(summary or {}, ensure_ascii=False), error])
        with self._lock:
            self._last_write.pop(run_id, None)
        return done

    def _due(self, run_id: int, throttle: float) -> bool:
        """节流闸门。放行的那一次也记时间——不记的话下一次拿 0 当基准，节流形同虚设。"""
        now = time.monotonic()
        with self._lock:
            if throttle > 0 and now - self._last_write.get(run_id, 0.0) < throttle:
                return False
            self._last_write[run_id] = now
        return True

    def _update_active(self, run_id: int, assignments: list[str],
                       values: list[object]) -> bool:
        marks = ",".join(f"'{name}'" for name in ACTIVE_STATUSES)
        with self.database.write_transaction(notify=False) as connection:
            cursor = connection.execute(
                f"UPDATE task_run SET {','.join(assignments)} "
                f"WHERE id=? AND status IN ({marks})",
                [*values, run_id])
        return cursor.rowcount > 0

    # -- 启动恢复与回收 ----------------------------------------------------

    def recover_interrupted(self, *, stale_after: float = LEASE_SECONDS) -> list[int]:
        """把上一个进程留下的活跃行改成 `interrupted`。服务启动时调用一次。

        判据分两种，本机与别的机器不能共用一条：

        - **本机写的行**：进程不在了就是被打断，不必等租约到期。PID 与我们自己相同
          也算——启动恢复跑在建任何一轮之前，那必然是一个被复用的 PID。
        - **别的机器写的行**：账本是复制过来的，那台机器上的进程存活与否这里查不到，
          只能按租约判。

        写成 `interrupted` 而不是 `failed`：任务没有失败，是没跑完；两者在「要不要
        去查为什么」上是相反的结论。
        """
        if not self.enabled:
            return []
        deadline = datetime.now(timezone.utc) - timedelta(seconds=stale_after)
        recovered: list[int] = []
        for run in self.query(status="active", limit=1000):
            local = run.host == self.host
            alive = (local and run.pid is not None and run.pid != os.getpid()
                     and process_alive(run.pid))
            beat = _parse(run.heartbeat_at) or _parse(run.started_at)
            expired = beat is None or beat < deadline
            if alive or (not local and not expired):
                continue
            if self.finish(run.id, "interrupted",
                           error="服务重启，这一轮没有跑完"):
                recovered.append(run.id)
        return recovered

    def prune(self, task_key: str, keep: int = DEFAULT_KEEP) -> int:
        """每个 task_key 只留最近 `keep` 条终态记录，返回删掉多少条。

        活跃行一条都不动：它们不是历史。阈值用 `LIMIT 1 OFFSET keep` 取「第 keep+1 新
        的那条 id」，不用窗口函数——这张表上要的只是一个分界点。
        """
        if not self.enabled or keep < 0:
            return 0
        marks = ",".join(f"'{name}'" for name in TERMINAL_STATUSES)
        with self.database.write_transaction(notify=False) as connection:
            threshold = connection.execute(
                f"SELECT id FROM task_run WHERE task_key=? AND status IN ({marks}) "
                "ORDER BY id DESC LIMIT 1 OFFSET ?", (task_key, keep)).fetchone()
            if threshold is None:
                return 0
            cursor = connection.execute(
                f"DELETE FROM task_run WHERE task_key=? AND status IN ({marks}) "
                "AND id<=?", (task_key, threshold["id"]))
        return cursor.rowcount

    # -- 查询 --------------------------------------------------------------

    def get(self, run_id: int) -> TaskRun | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM task_run WHERE id=?", (run_id,)).fetchone()
        return _row(row) if row else None

    def blocking(self, mutex_key: str) -> TaskRun | None:
        """当前占着这把锁的那一轮。冲突时用它回答「是谁挡的」。"""
        marks = ",".join(f"'{name}'" for name in ACTIVE_STATUSES)
        with self.database.read_connection() as connection:
            row = connection.execute(
                f"SELECT {_COLUMNS} FROM task_run WHERE mutex_key=? "
                f"AND status IN ({marks}) ORDER BY id LIMIT 1", (mutex_key,)).fetchone()
        return _row(row) if row else None

    def query(self, *, status: str = "", task_key: str = "",
              limit: int = 50) -> list[TaskRun]:
        """按状态与任务筛最近的若干轮。`status` 另收 `active`／`finished` 两个合集。"""
        clauses: list[str] = []
        values: list[object] = []
        if status == "active":
            clauses.append("status IN (%s)" % ",".join(f"'{s}'" for s in ACTIVE_STATUSES))
        elif status == "finished":
            clauses.append("status IN (%s)" % ",".join(f"'{s}'" for s in TERMINAL_STATUSES))
        elif status:
            if status not in (*ACTIVE_STATUSES, *TERMINAL_STATUSES):
                raise ValueError(f"未知的状态：{status}")
            clauses.append("status=?")
            values.append(status)
        if task_key:
            clauses.append("task_key=?")
            values.append(task_key)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.database.read_connection() as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM task_run{where} ORDER BY id DESC LIMIT ?",
                [*values, max(1, min(int(limit), 500))]).fetchall()
        return [_row(row) for row in rows]

    # -- 调用方的便利入口 --------------------------------------------------

    @contextmanager
    def track(self, task_key: str, *, trigger: str, mutex_key: str | None = None,
              conflict: str = "skip", total: int | None = None,
              label: str = "", keep: int = DEFAULT_KEEP) -> Iterator["TaskRunHandle"]:
        """同步代码用的一段式接线：进去开一轮，出来按有没有异常自动结算。

        被互斥挡住时产出一个不记录任何东西的 handle（`run_id is None`），调用方自己
        决定要不要继续干活——定时触发应当直接返回，命令行脚本通常也一样。
        """
        run = self.start(task_key, trigger=trigger, mutex_key=mutex_key,
                         conflict=conflict, total=total, label=label)
        handle = TaskRunHandle(self, run.id if run else None)
        try:
            yield handle
        except BaseException as error:
            handle.finish("failed", error=f"{type(error).__name__}: {error}")
            raise
        else:
            handle.finish("succeeded")
        finally:
            if run is not None:
                self.prune(task_key, keep)


def inert_handle() -> "TaskRunHandle":
    """一个什么都不登记的句柄。给「这一趟不进任务中心」和默认参数用。"""
    return TaskRunHandle(TaskRunStore(Path("."), enabled=False), None)


@contextmanager
def cli_run(task_key: str, db_path: Path | str | None, *, label: str = "",
            mutex_key: str | None = None) -> Iterator["TaskRunHandle"]:
    """命令行脚本的一段式接线：账本上记一轮，异常时记成失败。

    账本还没建、或者还没跑到 0028 时不记录，只在标准输出上说一句。批处理是无人值守
    跑的，因为「这一趟没法登记」就整个不跑，代价比不登记大得多；而静默跳过又会让人
    以为记上了，所以那一句必须打出来。

    脚本被强杀时这里什么也做不了，那一行会停在 `running`：服务下次启动的
    `recover_interrupted` 按 PID 把它收成 `interrupted`，两处判据是同一个。
    """
    store = None
    if db_path is not None and Path(db_path).is_file():
        candidate = TaskRunStore(Path(db_path))
        try:
            candidate.query(limit=1)
            store = candidate
        except sqlite3.OperationalError:
            print(f"[task-run] {db_path} 没有 task_run 表，本趟不登记进任务中心")
    if store is None:
        yield TaskRunHandle(TaskRunStore(Path(db_path or ":memory:"), enabled=False), None)
        return
    with store.track(task_key, trigger="cli", mutex_key=mutex_key,
                     conflict="skip", label=label) as handle:
        yield handle


@dataclass
class TaskRunHandle:
    """一轮任务的句柄。`run_id is None` 表示这一轮没有被记录，所有方法都是空操作。"""

    store: TaskRunStore
    run_id: int | None
    settled: bool = False

    def progress(self, current: int | None = None, total: int | None = None,
                 label: str | None = None, *,
                 throttle: float = PROGRESS_INTERVAL) -> None:
        self.store.progress(self.run_id, current=current, total=total,
                            label=label, throttle=throttle)

    def heartbeat(self) -> None:
        self.store.heartbeat(self.run_id)

    def finish(self, status: str, *, summary: dict | None = None,
               error: str = "") -> bool:
        """结算一次。重复调用不再写入——终态一次性这条约束在句柄这一层也要成立。"""
        if self.settled:
            return False
        self.settled = True
        return self.store.finish(self.run_id, status, summary=summary, error=error)
