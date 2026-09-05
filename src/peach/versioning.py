from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__
from .config import PROJECT_ROOT


def discover_repository_root(
    resource_root: Path = PROJECT_ROOT,
    *,
    executable: Path | None = None,
) -> Path:
    """Find the source repository used by the tray without inventing one."""

    resource_root = resource_root.resolve()
    if (resource_root / ".git").exists():
        return resource_root

    executable = (executable or Path(sys.executable)).resolve()
    for parent in executable.parents:
        if (parent / ".git").exists():
            return parent
    return resource_root


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
    #: 这次快进改动了哪些仓库相对路径。只有 `updated` 会非空，调用方据此判断
    #: 光重启子服务够不够。
    changed_paths: tuple[str, ...] = ()


class VersionManager:
    """Read-only Git/package version inspection and explicit update checks."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        execute: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.root = (root if root is not None else discover_repository_root()).resolve()
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
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=creationflags,
        )

    def _text(self, *args: str) -> str:
        result = self._git(*args)
        return result.stdout.strip() if result.returncode == 0 else ""

    def inspect(self) -> VersionSnapshot:
        package_version = __version__
        from .distribution import standalone
        if standalone():
            return VersionSnapshot(package_version, "测试包", "release", False, False, None)
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
        from .distribution import standalone
        if standalone():
            return UpdateResult("manual", "测试包请从 GitHub Releases 下载新版并完整解压替换程序目录；数据保存在用户目录。", before)
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

    def update(self) -> UpdateResult:
        """把本地检出快进到更新通道，只做快进。

        不 stash、不 rebase、不 `--force`：并行工作树和主检出共用同一个对象库与
        reflog，任何一种改写历史的「顺手解决」都会把别的分支一起拖下水。凡是快进
        做不到的，一律原样报出来交给人。

        `check()` 已经 fetch 过并给出了状态，这里只在 `available` 时才动工作区；
        其余状态（未配置、无跟踪分支、已最新、本地领先、两边分叉）直接透传，
        调用方不需要再分一次类。
        """
        checked = self.check()
        if checked.state != "available":
            return checked
        snapshot = checked.snapshot
        if snapshot.dirty:
            return UpdateResult(
                "blocked",
                f"更新通道有 {checked.behind} 个新提交，但本地检出有未提交修改；"
                "先处理掉再同步。",
                snapshot, behind=checked.behind,
            )
        before = self._text("rev-parse", "HEAD")
        merged = self._git("merge", "--ff-only", str(snapshot.upstream), timeout=60)
        if merged.returncode != 0:
            return UpdateResult(
                "blocked",
                f"无法快进到 {snapshot.upstream}；本地检出未改变，需要人工处理。",
                snapshot, behind=checked.behind,
            )
        current = self.inspect()
        changed = tuple(
            line for line in self._text("diff", "--name-only", f"{before}..HEAD").splitlines()
            if line
        )
        return UpdateResult(
            "updated",
            f"已同步 {checked.behind} 个提交：{before[:8]} → {current.commit}。",
            current, behind=checked.behind, changed_paths=changed,
        )
