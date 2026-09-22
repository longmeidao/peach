"""任务后继：一轮任务结束时声明，调度端统一派发（ADR-0040）。

这一层只管调度，不管任何一种后继具体做什么。后继的类型在 `REGISTRY` 里登记，登记的
内容是三件事：它在任务中心叫什么、写不写账本、怎么跑。

两条约束由这个模块的形状守住，不靠约定：

1. **后继只能由任务结果声明。** 这里没有「现在就派一条」的入口，派发一律经
   `TaskRunStore.enqueue_followups`，而那是在父任务结算时调用的。任务执行中起线程
   派活，在这套结构里不可表达。
2. **写账本的后继串行。** 通道按 `writes_ledger` 分：写的那些共用 `ledger` 一条通道，
   一次只跑一条；不写的各占一条以自己 task_key 命名的通道。Peach 的账本是单文件
   SQLite，并发写只会撞在写锁上，串行是如实反映约束而不是保守。

后继必须幂等。服务重启时没跑完的那些会重新排队（ADR-0040 第六条），一条后继因此
可能被执行两次；判据放在处理器自己的第一行——补头像先看盘上有没有那张图。
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable

from .task_runs import TaskRunHandle, TaskRunStore

LOGGER = logging.getLogger(__name__)

#: 写账本的后继共用的通道名。它不是任务种类，是「这条路上一次只许过一个」。
LEDGER_LANE = "ledger"


@dataclass(frozen=True)
class Followup:
    """一条待派发的后继。

    `key` 是这件事的全名，带实体 id（`entity-avatar:performer:8022`），不是任务类型：
    去重按它判，同一件事同时只会有一条在排队或在跑。
    """

    key: str
    task_key: str
    label: str = ""

    def as_row(self) -> tuple[str, str, str]:
        return (self.key, self.task_key, self.label)


@dataclass(frozen=True)
class FollowupType:
    """一种后继怎么跑。

    `run(contract, key, handle)` 返回一份摘要字典，异常一律算这一条失败——后继失败
    不回滚也不改判父任务（ADR-0040 第四条），所以这里不往上抛。
    """

    task_key: str
    label: str
    writes_ledger: bool
    run: Callable[[object, str, TaskRunHandle], dict]

    @property
    def lane(self) -> str:
        return LEDGER_LANE if self.writes_ledger else self.task_key


#: task_key → 类型。装配点导入对应模块即完成登记，调度器不认识任何一种后继。
REGISTRY: dict[str, FollowupType] = {}


def register(followup_type: FollowupType) -> FollowupType:
    """登记一种后继。同一个 task_key 只能登记一次——两份实现抢同一个身份时，
    活动页上那条记录说的是哪一个就再也答不出来了。"""
    if followup_type.task_key in REGISTRY:
        raise ValueError(f"后继类型 {followup_type.task_key} 已经登记过")
    REGISTRY[followup_type.task_key] = followup_type
    return followup_type


def lanes() -> dict[str, tuple[str, ...]]:
    """通道 → 它负责的 task_key。"""
    grouped: dict[str, list[str]] = {}
    for followup_type in REGISTRY.values():
        grouped.setdefault(followup_type.lane, []).append(followup_type.task_key)
    return {lane: tuple(sorted(keys)) for lane, keys in grouped.items()}


class FollowupRunner:
    """把库里排着的后继跑掉。每条通道一个线程，通道内串行。

    线程是按需起的，跑空就退出：后继大多数时候一条都没有，常驻线程在这里只是一个
    每隔几秒醒一次的空转。入队之后由调用方 `wake()`，服务启动时 `resume()`。
    """

    def __init__(self, contract, store: TaskRunStore | None = None):
        self.contract = contract
        self.store = store if store is not None else contract.task_runs
        self._lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}
        self._stopping = False

    # -- 对外 --------------------------------------------------------------

    def resume(self) -> list[int]:
        """服务启动时调用一次：把没跑完的后继重新排队，再把通道叫醒。"""
        requeued = self.store.requeue_followups()
        self.wake()
        return requeued

    def wake(self) -> None:
        """有新的后继排上了，确保每条通道都有人在跑。"""
        with self._lock:
            if self._stopping:
                return
            for lane, keys in lanes().items():
                thread = self._threads.get(lane)
                if thread is not None and thread.is_alive():
                    continue
                thread = threading.Thread(
                    target=self._work, args=(keys,), daemon=True,
                    name=f"PeachFollowup-{lane}")
                self._threads[lane] = thread
                thread.start()

    def stop(self, timeout: float | None = 2.0) -> None:
        """不再领新的后继并等在途那一条收工。

        在途那一条不打断：它多半正在写账本，中途掐掉留下的是一条停在 `running` 的行，
        而下次启动的 `requeue_followups` 会把它重新排一遍——那是多跑一次，不是少跑。
        """
        with self._lock:
            self._stopping = True
            threads = list(self._threads.values())
            self._threads.clear()
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout)

    def drain(self) -> int:
        """在当前线程里把所有通道排着的后继跑完，返回跑了几条。

        测试与命令行用这一条：它们要的是「跑完了再往下走」，而不是一个后台线程。
        """
        done = 0
        for keys in lanes().values():
            while True:
                run = self.store.claim_followup(keys)
                if run is None:
                    break
                self._execute(run)
                done += 1
        return done

    # -- 执行 --------------------------------------------------------------

    def _work(self, keys: tuple[str, ...]) -> None:
        while not self._stopping:
            run = self.store.claim_followup(keys)
            if run is None:
                return
            self._execute(run)

    def _execute(self, run) -> None:
        followup_type = REGISTRY.get(run.task_key)
        handle = TaskRunHandle(self.store, run.id)
        if followup_type is None:
            # 登记表里没有这一种：多半是账本里留着上一个版本排下的行。判失败而不是
            # 丢在 `running` 上，否则它的互斥键会一直占着，同一件事再也排不进来。
            handle.finish("failed", error=f"没有登记 {run.task_key} 这种后继")
            return
        try:
            summary = followup_type.run(self.contract, run.followup_key, handle)
        except Exception as error:  # 后继失败只是它自己失败，父任务的结论不动。
            LOGGER.warning("followup failed: %s: %s", run.followup_key, error,
                           exc_info=True)
            handle.finish("failed", error=f"{type(error).__name__}: {error}")
            return
        handle.finish("succeeded", summary=summary if isinstance(summary, dict) else {})
