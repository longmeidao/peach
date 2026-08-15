from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__
from .config import PROJECT_ROOT


@dataclass(frozen=True)
class VersionSnapshot:
    package_version: str
    branch: str
    commit: str
    dirty: bool
    remote_configured: bool
    upstream: str | None

    @property
    def build_label(self) -> str:
        dirty = " · 有未提交修改" if self.dirty else ""
        return f"{self.branch}@{self.commit}{dirty}"

    @property
    def channel_label(self) -> str:
        if not self.remote_configured:
            return "本地开发版 · 未配置更新源"
        if not self.upstream:
            return "已配置更新源 · 未跟踪分支"
        return f"更新通道 · {self.upstream}"


@dataclass(frozen=True)
class UpdateResult:
    state: str
    message: str
    snapshot: VersionSnapshot
    ahead: int = 0
    behind: int = 0


class VersionManager:
    """Read-only Git/package version inspection and explicit update checks."""

    def __init__(
        self,
        root: Path = PROJECT_ROOT,
        *,
        execute: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.root = root.resolve()
        self._execute = execute

    def _git(self, *args: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        return self._execute(
            [
                "git", "-c", f"safe.directory={self.root.as_posix()}",
                "-C", str(self.root), *args,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=creationflags,
        )

    def _text(self, *args: str) -> str:
        result = self._git(*args)
        return result.stdout.strip() if result.returncode == 0 else ""

    def inspect(self) -> VersionSnapshot:
        package_version = __version__
        commit = self._text("rev-parse", "--short=8", "HEAD") or "unknown"
        branch = self._text("branch", "--show-current") or "detached"
        dirty = bool(self._text("status", "--porcelain"))
        remote_configured = self._git("remote", "get-url", "origin").returncode == 0
        upstream = self._text("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") or None
        if remote_configured and upstream is None and branch != "detached":
            candidate = f"origin/{branch}"
            if self._git("show-ref", "--verify", f"refs/remotes/{candidate}").returncode == 0:
                upstream = candidate
        return VersionSnapshot(package_version, branch, commit, dirty, remote_configured, upstream)

    def check(self) -> UpdateResult:
        before = self.inspect()
        if not before.remote_configured:
            return UpdateResult(
                "unconfigured",
                f"Peach {before.package_version}（{before.build_label}）\n未配置更新源；当前为本地开发版。",
                before,
            )
        fetched = self._git("fetch", "--quiet", "--prune", "origin", timeout=30)
        if fetched.returncode != 0:
            return UpdateResult("error", "无法连接更新源；本地版本未改变。", before)
        current = self.inspect()
        if not current.upstream:
            return UpdateResult(
                "untracked",
                "更新源已连接，但当前分支没有对应的跟踪分支。",
                current,
            )
        counts = self._text("rev-list", "--left-right", "--count", f"HEAD...{current.upstream}").split()
        if len(counts) != 2 or not all(value.isdigit() for value in counts):
            return UpdateResult("error", "更新源已连接，但无法比较版本。", current)
        ahead, behind = map(int, counts)
        if behind and ahead:
            state = "diverged"
            message = f"本地领先 {ahead} 个提交，远端领先 {behind} 个提交；需要人工合并。"
        elif behind:
            state = "available"
            message = f"发现 {behind} 个新提交。为保护并行工作树，只检查、不自动安装。"
        elif ahead:
            state = "ahead"
            message = f"当前已比更新通道领先 {ahead} 个提交。"
        else:
            state = "current"
            message = f"Peach {current.package_version} 已是当前更新通道的最新版本。"
        return UpdateResult(state, message, current, ahead=ahead, behind=behind)
