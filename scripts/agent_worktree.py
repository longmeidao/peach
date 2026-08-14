from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


class WorkspaceError(RuntimeError):
    pass


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = [
        "git", "-c", f"safe.directory={repo.as_posix()}", "-C", str(repo), *args,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise WorkspaceError((result.stderr or result.stdout).strip())
    return result


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        raise WorkspaceError("agent/task must contain letters or numbers")
    return slug


def _main_worktree(repo: Path) -> Path:
    common = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    return common.parent if common.name == ".git" else common


def _lines(result: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in result.stdout.splitlines() if line]


def create(repo: Path, agent: str, task: str, root: Path | None = None) -> dict[str, object]:
    main = _main_worktree(repo)
    agent_slug, task_slug = _slug(agent), _slug(task)
    branch = f"agent/{agent_slug}/{task_slug}"
    target_root = root or (main.parent / "peach-worktrees")
    target = target_root / f"{agent_slug}-{task_slug}"
    if target.exists():
        raise WorkspaceError(f"target exists: {target}")
    if _git(main, "show-ref", "--verify", f"refs/heads/{branch}", check=False).returncode == 0:
        raise WorkspaceError(f"branch exists: {branch}")
    target_root.mkdir(parents=True, exist_ok=True)
    _git(main, "worktree", "add", "-b", branch, str(target), "HEAD")
    return {
        "ok": True,
        "action": "create",
        "path": str(target),
        "branch": branch,
        "base": _git(target, "rev-parse", "HEAD").stdout.strip(),
        "main_dirty": bool(_git(main, "status", "--porcelain").stdout.strip()),
    }


def ready(repo: Path, target_branch: str = "master") -> dict[str, object]:
    branch = _git(repo, "branch", "--show-current").stdout.strip()
    if not branch.startswith("agent/"):
        raise WorkspaceError("ready must run from an agent/* branch")
    dirty = _lines(_git(repo, "status", "--porcelain"))
    if dirty:
        raise WorkspaceError("worktree is dirty; commit only owned paths first")
    base = _git(repo, "merge-base", target_branch, "HEAD").stdout.strip()
    commits = _lines(_git(repo, "rev-list", "--reverse", f"{base}..HEAD"))
    if not commits:
        raise WorkspaceError("branch has no commits")
    worker_files = set(_lines(_git(repo, "diff", "--name-only", f"{base}..HEAD")))
    target_files = set(_lines(_git(repo, "diff", "--name-only", f"{base}..{target_branch}")))
    return {
        "ok": True,
        "action": "ready",
        "branch": branch,
        "base": base,
        "head": _git(repo, "rev-parse", "HEAD").stdout.strip(),
        "commits": commits,
        "files": sorted(worker_files),
        "same_file_changes": sorted(worker_files & target_files),
    }


def integrate(repo: Path, worker_branch: str, target_branch: str = "master") -> dict[str, object]:
    main = _main_worktree(repo)
    if repo.resolve() != main.resolve():
        raise WorkspaceError("integrate must run from the main integration worktree")
    if _git(main, "branch", "--show-current").stdout.strip() != target_branch:
        raise WorkspaceError(f"checkout {target_branch} before integrate")
    if _git(main, "status", "--porcelain").stdout.strip():
        raise WorkspaceError("integration worktree is dirty")
    base = _git(main, "merge-base", target_branch, worker_branch).stdout.strip()
    worker_files = set(_lines(_git(main, "diff", "--name-only", f"{base}..{worker_branch}")))
    target_files = set(_lines(_git(main, "diff", "--name-only", f"{base}..{target_branch}")))
    overlap = sorted(worker_files & target_files)
    if overlap:
        raise WorkspaceError("same-file review required: " + ", ".join(overlap))
    before = _git(main, "rev-parse", "HEAD").stdout.strip()
    _git(main, "merge", "--no-ff", "--no-edit", worker_branch)
    return {
        "ok": True,
        "action": "integrate",
        "branch": worker_branch,
        "before": before,
        "after": _git(main, "rev-parse", "HEAD").stdout.strip(),
        "files": sorted(worker_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Isolated Peach agent worktree coordinator")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("create")
    start.add_argument("--agent", required=True)
    start.add_argument("--task", required=True)
    start.add_argument("--root", type=Path)
    inspect = sub.add_parser("ready")
    inspect.add_argument("--target", default="master")
    merge = sub.add_parser("integrate")
    merge.add_argument("--branch", required=True)
    merge.add_argument("--target", default="master")
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = create(args.repo, args.agent, args.task, args.root)
        elif args.command == "ready":
            result = ready(args.repo, args.target)
        else:
            result = integrate(args.repo, args.branch, args.target)
    except WorkspaceError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
