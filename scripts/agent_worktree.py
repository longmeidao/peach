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
    result = subprocess.run(command, text=True, encoding="utf-8", errors="replace",
                            capture_output=True, check=False)
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


def _worktree_entries(main: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    entry: dict[str, str] = {}
    for line in _lines(_git(main, "worktree", "list", "--porcelain")):
        if line.startswith("worktree "):
            entry = {"path": line[len("worktree "):]}
            entries.append(entry)
        elif line.startswith("branch "):
            entry["branch"] = line[len("branch "):].replace("refs/heads/", "")
    return entries


def _reclaim(main: Path, path: Path, branch: str) -> tuple[str, dict[str, str]]:
    """回收单个工作树，把结果归到 reclaimed / residue / failed 之一。

    2026-09-01 实测：Windows 上 `.claude/worktrees/*` 的目录句柄被别的进程占着，
    `git worktree remove` 报 Permission denied，而 git 已经把文件删光、注册也摘掉了，
    只剩一个空目录。这一步以前直接抛错中止整轮，于是分支一条没删、后面的工作树一个没碰，
    要靠人反复重跑 prune，跑一次才推进一个。所以失败只波及它自己：注册已经摘掉的照常删
    分支，残留目录单独列出来交给人清；注册还在才算真没回收成。
    """
    removal = _git(main, "worktree", "remove", str(path), check=False)
    why = (removal.stderr or removal.stdout).strip()
    registered = {Path(item["path"]).resolve() for item in _worktree_entries(main)}
    if removal.returncode and path.resolve() in registered:
        return "failed", {"path": str(path), "branch": branch, "why": why}
    if branch:
        _git(main, "branch", "-d", branch, check=False)
    if removal.returncode:
        return "residue", {"path": str(path), "branch": branch,
                           "why": "目录残留，待人工清理：" + why}
    return "reclaimed", {"path": str(path), "branch": branch}


def prune(repo: Path, target_branch: str = "master", *,
          apply: bool = False) -> dict[str, object]:
    """回收分支已并入 target、且工作区干净的隔离工作树。

    这个命令存在的理由：`create` 一直有人用，回收却从来没有入口。2026-08-29 清过一次
    到 3 个，两天后又长回 74 个、占 868 MB——因为那次是一次性动作，不是常设机制。

    默认只报告不动手。回收不可逆，而「分支已合入」并不等于「工作区里没有东西」：
    实测就有工作树的分支早已并入 master，里面却躺着一份成形的未提交改动。所以脏的
    一律拒收并单独列出，交给人看，不给 `--force` 这个口子。

    单个工作树回收失败不影响其它工作树：结果分成 reclaimed / residue / failed /
    dirty / kept 五组，整轮照样 ok。理由见 `_reclaim`。
    """
    main = _main_worktree(repo)
    merged = {line.strip().lstrip("+* ") for line in
              _lines(_git(main, "branch", "--merged", target_branch,
                          "--format=%(refname:short)"))}
    merged.discard(target_branch)
    here = repo.resolve()

    reclaimed: list[str] = []
    residue: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    dirty: list[dict[str, str]] = []
    kept: list[dict[str, str]] = []

    for item in _worktree_entries(main):
        path = Path(item["path"])
        branch = item.get("branch", "")
        if path.resolve() == main.resolve() or path.resolve() == here:
            continue
        if branch not in merged:
            kept.append({"path": str(path), "branch": branch, "why": "分支未并入 " + target_branch})
            continue
        if _git(main, "-C", str(path), "status", "--porcelain",
                check=False).stdout.strip():
            dirty.append({"path": str(path), "branch": branch, "why": "工作区有未提交改动"})
            continue
        if not apply:
            reclaimed.append(str(path))
            continue
        group, record = _reclaim(main, path, branch)
        if group == "reclaimed":
            reclaimed.append(str(path))
        elif group == "residue":
            residue.append(record)
        else:
            failed.append(record)

    return {
        "ok": True,
        "action": "prune",
        "applied": apply,
        "reclaimed": sorted(reclaimed),
        "residue": residue,
        "failed": failed,
        "dirty": dirty,
        "kept": kept,
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
    sweep = sub.add_parser("prune")
    sweep.add_argument("--target", default="master")
    sweep.add_argument("--apply", action="store_true",
                       help="真的回收；不给这个参数就只报告")
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = create(args.repo, args.agent, args.task, args.root)
        elif args.command == "ready":
            result = ready(args.repo, args.target)
        elif args.command == "prune":
            result = prune(args.repo, args.target, apply=args.apply)
        else:
            result = integrate(args.repo, args.branch, args.target)
    except WorkspaceError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
