"""Peach 批处理任务共享的安全与成本策略。"""
from __future__ import annotations

import shutil
import os
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


class PidFileLock:
    """进程级独占锁；只清理确认已经不存在的旧 PID。"""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._acquired = False

    @staticmethod
    def _running(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

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
