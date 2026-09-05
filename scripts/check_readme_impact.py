"""核对一次分支交付的 README 影响声明。"""

from __future__ import annotations

import subprocess
from pathlib import Path

READMES = {"README.md", "README.en.md"}
PREFIXES = ("src/peach/", "web/", "frontend/", "migrations/", "resources/")
FILES = {
    "pyproject.toml", "package.json", "package-lock.json",
    ".github/workflows/release.yml", "docs/FRONTEND.md",
    "docs/TESTING_DESKTOP.md", "docs/OPERATIONS.md", "docs/SOURCING.md",
    "scripts/build_windows.ps1", "scripts/build_app_entry.py",
}


def git(repo: Path, *args: str, message: str | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], input=message, capture_output=True,
        text=True, encoding="utf-8", check=True,
    ).stdout


def check(repo: Path, base: str, head: str = "HEAD") -> list[str]:
    """以实际交付差异和最后提交的 Git trailer 为依据。"""
    paths = set(git(repo, "diff", "--name-only", "--no-renames", "-z",
                    base, head).rstrip("\0").split("\0")) - {""}
    touched = paths & READMES
    relevant = any(path in FILES or path.startswith(PREFIXES) for path in paths)
    if not touched and not relevant:
        return []
    message = git(repo, "show", "-s", "--format=%B", head)
    trailers = git(repo, "interpret-trailers", "--parse", message=message)
    values = [line.partition(":")[2].strip() for line in trailers.splitlines()
              if line.partition(":")[0].casefold() == "readme-impact"]
    if len(values) != 1:
        return ["交付提交须有唯一 README-Impact: updated; 说明 或 README-Impact: none; 原因"]
    status, separator, reason = values[0].partition(";")
    if status not in {"updated", "none"} or not separator or not reason.strip():
        return ["README-Impact 需使用 updated/none，并在英文分号后写具体原因"]
    if touched and touched != READMES:
        return ["README.md 与 README.en.md 必须同批维护"]
    if status == "updated" and touched != READMES:
        return ["README-Impact 声明 updated，但交付差异未包含两份 README"]
    if status == "none" and touched:
        return ["README-Impact 声明 none，但交付差异包含 README"]
    return []
