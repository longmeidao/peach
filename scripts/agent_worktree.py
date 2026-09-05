from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
import subprocess
import time
from collections.abc import Iterable
from pathlib import Path

#: Claude Code 内置工作树的落点。分支集成后它自己不收：目录留在主检出里，成了一份看不出
#: 区别的旧副本（见 CLAUDE.md）。`tests/test_repo_hygiene.py` 拦得住，但拦住之后没有任何
#: 入口能清掉已经在那儿的，只能让人手删——`prune --apply` 顺带扫掉这块。
BUILTIN_WORKTREES = Path(".claude") / "worktrees"

#: 版本号的唯一来源。GitHub Release 的 `v<版本>` tag 必须与它相等。
VERSION_FILE = "src/peach/__init__.py"
VERSION_PATTERN = re.compile(r'(__version__\s*=\s*")(\d+)\.(\d+)\.(\d+)(")')

#: 进入运行时产物的输入。改到这些位置就意味着「跑起来的东西变了」，本地版本号跟着走一格；
#: 文档、技能和测试只改开发过程，版本号不动。清单与 `WINDOWS_TRAY_INPUTS` 各自服务不同的
#: 问题：那份决定要不要重建 EXE，这份决定要不要发新版本号。
RUNTIME_INPUTS = (
    "src/peach/",
    "web/",
    "frontend/",
    "migrations/",
    "resources/",
    "scripts/build_app_entry.py",
    "scripts/build_windows.ps1",
    "pyproject.toml",
)


class WorkspaceError(RuntimeError):
    pass


def runtime_inputs_changed(paths: Iterable[str]) -> bool:
    """这批改动里有没有会进到运行时产物的。"""
    normalized = [str(path).replace("\\", "/").strip("/") for path in paths]
    return any(path == prefix.rstrip("/") or path.startswith(prefix)
               for path in normalized for prefix in RUNTIME_INPUTS)


#: Conventional Commits 的功能类型；`!` 是破坏性标记。pre-1.0 阶段两者都只推 minor（ADR-0012）。
FEATURE_SUBJECT = re.compile(r"^(feat|feature)(\(.*\))?!?:|^\w+(\(.*\))?!:")


def bump_part_for(subjects: Iterable[str], added_paths: Iterable[str]) -> str:
    """这批提交该推版本号的哪一位。

    有功能提交（`feat:`）或破坏性标记（`type!:`），或者新增了迁移文件，就是 minor；
    其余（修复、重构、文案、构建）是 patch。major 只在 1.0 那一次手工给，这里不判。
    """
    if any(FEATURE_SUBJECT.match(subject.strip()) for subject in subjects):
        return "minor"
    normalized = [str(path).replace("\\", "/").strip("/") for path in added_paths]
    if any(path.startswith("migrations/") for path in normalized):
        return "minor"
    return "patch"


def bump_version(text: str, part: str) -> tuple[str, str]:
    """把 `__version__` 那一行往前推一格，返回新正文与新版本号。

    纯函数，只认那一行：整份文件其余部分逐字节保留，换行也不碰。
    """
    match = VERSION_PATTERN.search(text)
    if match is None:
        raise WorkspaceError(f"{VERSION_FILE} does not declare __version__")
    major, minor, patch = (int(match.group(index)) for index in (2, 3, 4))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        raise WorkspaceError(f"unknown bump part: {part}")
    version = f"{major}.{minor}.{patch}"
    updated = text[:match.start()] + f"{match.group(1)}{version}{match.group(5)}" \
        + text[match.end():]
    return updated, version


def read_version(main: Path) -> str:
    match = VERSION_PATTERN.search((main / VERSION_FILE).read_bytes().decode("utf-8"))
    if match is None:
        raise WorkspaceError(f"{VERSION_FILE} does not declare __version__")
    return f"{match.group(2)}.{match.group(3)}.{match.group(4)}"


def _commit_version_bump(main: Path, part: str) -> str:
    path = main / VERSION_FILE
    updated, version = bump_version(path.read_bytes().decode("utf-8"), part)
    path.write_bytes(updated.encode("utf-8"))
    _git(main, "add", VERSION_FILE)
    _git(main, "commit", "-m", f"chore(release): 版本 {version}")
    return version


#: 打版本标签的唯一入口。它核对本地与 GitHub master 一致、同提交 CI 全绿、标签不可覆盖，
#: 并且遇到同名本地标签就拒绝——集成这一步再造一个本地标签会直接把它挡住。所以这里只推进
#: `__version__`，标签留给它。
RELEASE_TAG_ENTRY = "scripts/release_tag.py"


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


def integrate(repo: Path, worker_branch: str, target_branch: str = "master", *,
              bump: str = "auto") -> dict[str, object]:
    """把工作者分支并进 target，并让本地版本号跟着这次集成走。

    这台机器既是开发机又是生产机：提交先落本地再推 GitHub，本地永远领先。版本号因此
    必须在集成时就动，不能等发布——发布点仍然是 `RELEASE_TAG_ENTRY` 推上去的那个
    `v<版本>` tag，它读的正是这里推进后的 `__version__`。

    `bump="auto"` 由 `bump_part_for()` 按这批提交的类型定档；显式传 patch／minor／major
    是覆盖，`none` 表示不动版本号。
    """
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
    subjects = _lines(_git(main, "log", "--no-merges", "--format=%s", f"{base}..{worker_branch}"))
    _git(main, "merge", "--no-ff", "--no-edit", worker_branch)
    merged_files = set(_lines(_git(main, "diff", "--name-only", f"{base}..HEAD")))
    added_files = _lines(_git(main, "diff", "--name-only", "--diff-filter=A", f"{base}..HEAD"))
    part = bump_part_for(subjects, added_files) if bump == "auto" else bump
    version = read_version(main)
    bumped = part != "none" and runtime_inputs_changed(merged_files)
    if bumped:
        version = _commit_version_bump(main, part)
    return {
        "ok": True,
        "action": "integrate",
        "branch": worker_branch,
        "before": before,
        "after": _git(main, "rev-parse", "HEAD").stdout.strip(),
        "files": sorted(worker_files),
        "version": version,
        "bumped": bumped,
        "bump": part if bumped else "none",
        "release_tag_entry": RELEASE_TAG_ENTRY,
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


def _force_writable(func, path, _exc) -> None:
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def _delete_tree(path: Path) -> str:
    """删掉回收之后剩下的目录。删掉了返回空串，否则返回失败原因。

    Windows 上删不掉多半不是权限而是句柄：另一个进程正把它当工作目录开着。短暂重试
    能等到杀毒、索引器一类的临时句柄放手，等不到一个 cd 在里面的 shell——所以只重试
    很短一会儿就如实报出来，不做无限等待，也不去猜是谁占着。
    """
    why = ""
    for attempt in range(4):
        if not path.exists():
            return ""
        try:
            shutil.rmtree(path, onexc=_force_writable)
            return ""
        except OSError as error:
            why = f"{type(error).__name__}: {error}"
            time.sleep(0.2 * (attempt + 1))
    return why


def _reclaim(main: Path, path: Path, branch: str) -> tuple[str, dict[str, str]]:
    """回收单个工作树，把结果归到 reclaimed / residue / failed 之一。

    2026-09-01 实测：Windows 上 `.claude/worktrees/*` 的目录句柄被别的进程占着，
    `git worktree remove` 报 Permission denied，而 git 已经把文件删光、注册也摘掉了，
    只剩一个空目录。所以失败只波及它自己：注册已经摘掉的照常删分支，目录自己再删一遍；
    注册还在才算真没回收成。这一步抛错中止整轮的话，分支一条没删、后面的工作树一个没碰，
    要靠人反复重跑 prune，跑一次才推进一个。

    「注册摘了、目录还在」不该留给人：那个目录在主检出里长得和真工作树一模一样，`git`
    在里面全作用于主检出的 master。git 删不动就自己删，删完才算回收；真删不掉才进
    residue，那时候确实需要人去看是谁占着。
    """
    removal = _git(main, "worktree", "remove", str(path), check=False)
    why = (removal.stderr or removal.stdout).strip()
    registered = {Path(item["path"]).resolve() for item in _worktree_entries(main)}
    if removal.returncode and path.resolve() in registered:
        return "failed", {"path": str(path), "branch": branch, "why": why}
    if branch:
        _git(main, "branch", "-d", branch, check=False)
    if removal.returncode:
        left = _delete_tree(path)
        if left:
            return "residue", {"path": str(path), "branch": branch,
                               "why": f"注册已摘掉，目录删不掉，确认没人占用后手动删：{left}（{why}）"}
    return "reclaimed", {"path": str(path), "branch": branch}


def _sweep_builtin(main: Path, here: Path, *, apply: bool
                   ) -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    """扫掉 `.claude/worktrees/` 里已经不登记的空目录。

    这些目录不在 `git worktree list` 里，上面那轮按登记项遍历的回收永远碰不到它们，
    人却会走进去当工作树用。只删空的：里面还有文件就可能是别人正在用的检出，或者是
    没提交的东西，那种一律留着报出来，不替人做判断。
    """
    swept: list[str] = []
    residue: list[dict[str, str]] = []
    kept: list[dict[str, str]] = []
    root = main / BUILTIN_WORKTREES
    if not root.is_dir():
        return swept, residue, kept
    registered = {Path(item["path"]).resolve() for item in _worktree_entries(main)}
    for path in sorted(root.iterdir()):
        if not path.is_dir() or path.resolve() in registered or path.resolve() == here:
            continue
        if any(child.is_file() for child in path.rglob("*")):
            kept.append({"path": str(path), "branch": "",
                         "why": "未登记的目录里还有文件，确认没人在用后手动删"})
            continue
        if not apply:
            swept.append(str(path))
            continue
        left = _delete_tree(path)
        if left:
            residue.append({"path": str(path), "branch": "", "why": "目录删不掉：" + left})
        else:
            swept.append(str(path))
    return swept, residue, kept


def prune(repo: Path, target_branch: str = "master", *,
          apply: bool = False) -> dict[str, object]:
    """回收分支已并入 target、且工作区干净的隔离工作树。

    这个命令存在的理由：`create` 一直有人用，回收却从来没有入口。2026-08-29 清过一次
    到 3 个，两天后又长回 74 个、占 868 MB——因为那次是一次性动作，不是常设机制。

    默认只报告不动手。回收不可逆，而「分支已合入」并不等于「工作区里没有东西」：
    实测就有工作树的分支早已并入 master，里面却躺着一份成形的未提交改动。所以脏的
    一律拒收并单独列出，交给人看，不给 `--force` 这个口子。

    单个工作树回收失败不影响其它工作树：结果分成 reclaimed / swept / residue / failed /
    dirty / kept 六组，整轮照样 ok。理由见 `_reclaim`。`swept` 是 `.claude/worktrees/`
    里已经不登记的空目录，见 `_sweep_builtin`。
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

    swept, swept_residue, swept_kept = _sweep_builtin(main, here, apply=apply)

    return {
        "ok": True,
        "action": "prune",
        "applied": apply,
        "reclaimed": sorted(reclaimed),
        "swept": sorted(swept),
        "residue": residue + swept_residue,
        "failed": failed,
        "dirty": dirty,
        "kept": kept + swept_kept,
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
    merge.add_argument("--bump", choices=("auto", "patch", "minor", "major", "none"),
                       default="auto",
                       help="auto 按提交类型定档：feat 或新迁移推 minor，其余推 patch；"
                            "改动没进运行时产物时不动。显式档位是覆盖，none 表示不动")
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
            result = integrate(args.repo, args.branch, args.target, bump=args.bump)
    except WorkspaceError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
