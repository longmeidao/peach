"""Peach 批处理任务共享的安全与成本策略。"""
from __future__ import annotations

import shutil
import os
import time
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
