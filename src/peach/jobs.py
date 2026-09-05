"""Peach 批处理任务共享的安全与成本策略，以及服务内后台任务的状态机。"""
from __future__ import annotations

import copy
import shutil
import os
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class JobPolicyError(RuntimeError):
    exit_code = 1


class MeteredSourceDenied(JobPolicyError):
    exit_code = 2


class DiskSpaceDenied(JobPolicyError):
    exit_code = 3


class JobAlreadyRunning(JobPolicyError):
    exit_code = 0


@dataclass(frozen=True)
class SourceAccessPolicy:
    metered_locations: frozenset[str] = frozenset({"pikpak", "online"})

    def sql_filter(
        self,
        location: str | None,
        allow_metered: bool,
        column: str = "location",
    ) -> tuple[str, tuple[str, ...]]:
        """返回参数化 location 条件；显式计费授权是唯一放行入口。"""
        if location in self.metered_locations and not allow_metered:
            raise MeteredSourceDenied(
                f"{location} 是计费来源；确认预算后显式加 --allow-metered"
            )

        clauses: list[str] = []
        parameters: list[str] = []
        if location:
            clauses.append(f"{column}=?")
            parameters.append(location)
        if not allow_metered:
            metered = tuple(sorted(self.metered_locations))
            placeholders = ",".join("?" for _ in metered)
            clauses.append(f"{column} NOT IN ({placeholders})")
            parameters.extend(metered)
        if not clauses:
            return "", ()
        return " AND " + " AND ".join(clauses), tuple(parameters)


def require_free_space(path: Path | str, minimum_gb: float) -> float:
    """返回可用 GiB；无法读取或低于阈值都拒绝启动，避免静默失去磁盘闸门。"""
    try:
        free_gb = shutil.disk_usage(path).free / 1024**3
    except OSError as exc:
        raise DiskSpaceDenied(f"无法读取 {path} 的磁盘余量") from exc
    if free_gb < minimum_gb:
        raise DiskSpaceDenied(
            f"{path} 仅剩 {free_gb:.1f} GiB（阈值 {minimum_gb:.1f} GiB）"
        )
    return free_gb


class DiskGuard:
    """运行期磁盘闸门：长任务必须在跑的过程中反复检查，不能只查起跑线。

    2026-08-15 的实际事故：抽帧启动时 C: 还有几百 GB，`require_free_space` 放行，
    随后 CloudDrive 把下载块缓存到系统盘直到 0 字节可用，而任务全程没有再看一眼。
    消耗方是第三方软件、落点也不是本任务的产物目录，所以"只盯自己写的文件"同样拦不住。
    这里按墙钟节流地复查真实可用空间，触线就让调用方停下来。
    """

    def __init__(self, path: Path | str, minimum_gb: float, interval_secs: float = 20.0):
        self.path = Path(path)
        self.minimum_gb = float(minimum_gb)
        self.interval_secs = float(interval_secs)
        self._next_check = 0.0

    def free_gb(self) -> float:
        return shutil.disk_usage(self.path).free / 1024**3

    def check(self, force: bool = False) -> float | None:
        """到期就复查；返回本次读到的可用 GiB，未到期返回 None。触线抛 DiskSpaceDenied。"""
        now = time.monotonic()
        if not force and now < self._next_check:
            return None
        self._next_check = now + self.interval_secs
        try:
            free_gb = self.free_gb()
        except OSError as exc:
            raise DiskSpaceDenied(f"无法读取 {self.path} 的磁盘余量") from exc
        if free_gb < self.minimum_gb:
            raise DiskSpaceDenied(
                f"运行中 {self.path} 仅剩 {free_gb:.1f} GiB（阈值 {self.minimum_gb:.1f} GiB）；"
                "已停止任务。检查第三方缓存目录，本任务的产物目录未必是消耗方"
            )
        return free_gb


class PidFileLock:
    """进程级独占锁；只清理确认已经不存在的旧 PID。"""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._acquired = False

    @staticmethod
    def _running(pid: int) -> bool:
        if pid <= 0:
            return False
        if os.name == "nt":
            return PidFileLock._running_windows(pid)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OverflowError:
            # 锁文件可能是 Windows 那台写的，PID 会超出 POSIX 的 pid_t 范围。
            # 超界的 PID 一定不是本机活进程，按「已死」清理，而不是让整轮任务崩掉。
            return False
        return True

    @staticmethod
    def _running_windows(pid: int) -> bool:
        """用 OpenProcess 查存活，绝不能用 `os.kill(pid, 0)`。

        Windows 上 `signal.CTRL_C_EVENT == 0`，所以 Unix 那个探测存活的经典写法
        `os.kill(pid, 0)` 实际会调用 `GenerateConsoleCtrlEvent(CTRL_C_EVENT, ...)`，
        把 Ctrl+C 发给整个控制台进程组——包括调用者自己。锁里写的又是自己的 PID，
        于是「检查锁是否还活着」会当场把自己打断：在真实控制台里跑批处理或测试时
        表现为毫无征兆的 KeyboardInterrupt；重定向、无控制台的环境反而不复现，
        因为控制台事件无处投递。
        """
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        ERROR_ACCESS_DENIED = 5
        STILL_ACTIVE = 259

        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            # 拒绝访问说明进程存在但不归我们管；其余错误一律视为已消失。
            return ctypes.get_last_error() == ERROR_ACCESS_DENIED
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                old_pid = int(self.path.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                old_pid = 0
            if old_pid and self._running(old_pid):
                raise JobAlreadyRunning(f"已有实例在跑（PID {old_pid}）")
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            handle.write(str(os.getpid()))
        self._acquired = True

    def release(self) -> None:
        if self._acquired:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self._acquired = False

    def __enter__(self) -> "PidFileLock":
        self.acquire()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()


class BackgroundJob:
    """服务里一次「点一下、后台跑、前端轮询」的任务：锁、状态和线程都在这里。

    死链检查和资源对账各写了一份逐字相同的这个形状：一把锁、一个带 uuid 的状态字典、
    `status_only` 与 `restart` 两个开关、一个 daemon 线程，以及一个把异常翻成
    `status="failed"` 的 except。共用的不只是形状，还有三条容易漏的约定：

    1. **状态里必须带任务 id，而且每次改状态前都要核对**。轮询期间用户可以按
       `restart` 顶掉在跑的那一轮；被顶掉的线程如果还继续写状态，前端看到的就是
       新一轮的 id 配旧一轮的进度。
    2. **后台异常必须变成可轮询的状态**。只写日志的话，界面会永远停在「进行中」。
    3. **`thread.start()` 不能在锁里**。

    `snapshot()` 返回深拷贝：域模块的公开投影（挑字段、`[dict(x) for x in ...]`）
    因此可以在锁外安全地算，不必让每个域都自己记得「投影要在锁里做」。状态只装
    JSON 形态的数据，拷贝很便宜。
    """

    def __init__(self, name: str, *, id_key: str = "job_id"):
        #: 线程名，出现在崩溃栈和进程视图里，所以取和端点一致的名字。
        self.name = name
        #: 状态字典里存任务 id 的键名。域模块的公开投影直接下发它，所以沿用各域原有的
        #: 名字（`check_id`／`scan_id`）而不是统一改名——那是前端契约。
        self.id_key = id_key
        self.lock = threading.Lock()
        self.state: dict | None = None
        self.thread: threading.Thread | None = None

    def snapshot(self) -> dict | None:
        """当前状态的深拷贝；一次都没跑过返回 None。"""
        with self.lock:
            return copy.deepcopy(self.state) if self.state is not None else None

    def update(self, job_id: str, **fields: object) -> bool:
        """状态仍属于 `job_id` 时改字段；已经被顶掉就什么都不做并返回 False。"""
        with self.editing(job_id) as state:
            if state is None:
                return False
            state.update(fields)
            return True

    @contextmanager
    def editing(self, job_id: str) -> Iterator[dict | None]:
        """拿住锁产出仍属于 `job_id` 的状态；被顶掉则产出 None。

        进度是往列表里追加、给计数加一，不都是整字段替换，所以除了 `update` 还要
        有这个原地改的入口。
        """
        with self.lock:
            state = self.state
            yield state if state is not None and state[self.id_key] == job_id else None

    def start(self, fn: Callable[[str], None], *, initial: dict | None = None,
              restart: bool = False) -> dict:
        """跑一轮，返回启动后（或原有）状态的深拷贝。

        已经在跑，或者已经有结果而调用方没要求 `restart`，都原样返回现状——重复点击
        不该把一轮跑到一半的检查丢掉。`fn` 收到本轮的任务 id，自己负责把 `status`
        推到 `complete`：完成时要落什么结果字段是域的事。
        """
        thread = None
        with self.lock:
            state = self.state
            if state is None or (restart and state["status"] != "running"):
                job_id = uuid.uuid4().hex
                state = {self.id_key: job_id, "status": "running",
                         "started_at": time.time(), "error": "", **(initial or {})}
                self.state = state
                thread = threading.Thread(target=self._run, args=(fn, job_id),
                                          daemon=True, name=self.name)
                self.thread = thread
            snapshot = copy.deepcopy(state)
        if thread is not None:
            thread.start()
        return snapshot

    def stop(self, timeout: float | None = 2.0) -> None:
        """丢掉状态并等线程收工，用于服务关停。

        线程是 daemon，本来也挡不住进程退出；清状态的意义是让在途的 worker 下一次
        拿锁时发现自己已被顶掉，从而安静返回，而不是在解释器拆卸期间继续查库、
        往一个没人读的状态里写进度。等不到就不等——一次外部 HTTP 探测可以是十几秒，
        关停不该被它拖住。
        """
        with self.lock:
            self.state = None
            thread = self.thread
            self.thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout)

    def start_result(self, fn: Callable[[], dict]) -> dict:
        """执行一次操作并保存终态回执；重复提交只返回进行中的同一任务。"""
        def work(job_id):
            result = fn()
            self.update(job_id, **result, status=(
                "complete" if result.get("ok", True) else "failed"),
                completed_at=time.time())
        return self.start(work, restart=True)

    def _run(self, fn: Callable[[str], None], job_id: str) -> None:
        try:
            fn(job_id)
        except Exception as error:   # 后台失败必须变成可轮询的状态，不能只留在日志里
            self.update(job_id, status="failed",
                        error=f"{type(error).__name__}: {error}",
                        completed_at=time.time())


def job_main(build_parser, run, argv: list[str] | None = None) -> int:
    """长跑批处理脚本的统一入口收尾。

    解析参数、拿住 pid 锁、跑 `run(args)`；被磁盘或来源策略拦下时打印一行 `[stop]`
    并交出策略自己的退出码，而不是抛栈——批处理是无人值守跑的，退出码才是被读的那个。

    这段此前在 creator_boards、probe、sheets 三个脚本里逐字相同地各写了一份。它们
    共用的不只是形状，还有「pid 锁必须包住整个 run」和「策略异常不算崩溃」这两条
    约定；散成三份，下一个脚本照抄时漏掉锁或吞掉退出码都不会有人发现。
    """
    args = build_parser().parse_args(argv)
    try:
        with PidFileLock(args.lock):
            return run(args)
    except JobPolicyError as exc:
        print(f"[stop] {exc}")
        return exc.exit_code
