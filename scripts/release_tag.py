"""版本号推进与版本标签：发布的唯一入口。

一次发布走两步。先 `--bump auto --apply` 把 `__version__` 推一格并起草 `CHANGELOG.md`
的新一节，人把措辞改成使用者读得懂的话，提交推上去；等这个提交的 CI 绿了，再 `--apply`
创建并推送不可覆盖的 `v<版本>` 标签，触发预发布。

版本号只在这里动：每个 `X.Y.Z` 都对应一份可下载的制品，日常集成的提交由 commit
标识（ADR-0012）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "scripts"
from . import changelog, version_bump

ROOT = Path(__file__).resolve().parents[1]


def command(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout.strip()


def api(repo: str, endpoint: str):
    return json.loads(command("gh", "api", f"repos/{repo}/{endpoint}"))


def require_success(runs: list[dict], sha: str) -> dict:
    matching = [run for run in runs if run.get("head_sha") == sha
                and run.get("head_branch") == "master" and run.get("event") == "push"]
    if not matching:
        raise ValueError("此提交没有 master 的 Test 工作流记录")
    latest = max(matching, key=lambda run: (run["id"], run.get("run_attempt", 1)))
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise ValueError(f"此提交最新 Test 尚未通过：{latest.get('html_url', '')}")
    return latest


def verify(repo: str, sha: str) -> dict:
    comparison = api(repo, f"compare/master...{sha}")
    if comparison["status"] not in {"identical", "behind"}:
        raise ValueError("发布提交不属于远端 master 历史")
    runs = api(repo, f"actions/workflows/test.yml/runs?head_sha={sha}&event=push&per_page=100")
    checked = require_success(runs["workflow_runs"], sha)
    return {"sha": sha, "test": checked["html_url"]}


def _require_clean_master() -> None:
    if command("git", "status", "--porcelain"):
        raise ValueError("工作区不干净")
    if command("git", "branch", "--show-current") != "master":
        raise ValueError("请从 master 主检出执行")


def _require_free_tag(repo: str, tag: str) -> None:
    # matching-refs 返回空列表代表不存在；网络或权限错误不能被当成空列表。
    if any(ref["ref"] == f"refs/tags/{tag}" for ref in api(repo, f"git/matching-refs/tags/{tag}")):
        raise ValueError(f"{tag} 已存在，不覆盖；发布新版本请先推进 __version__")


def prepare(repo: str, part: str, *, apply: bool) -> dict:
    """为下一次发布推进版本号并起草变更日志。

    只写文件，不提交：变更日志的措辞要人过一遍，脚本自己提交等于鼓励不看。
    """
    _require_clean_master()
    planned = version_bump.plan_bump(ROOT, part)
    version = str(planned["version"])
    tag = f"v{version}"
    _require_free_tag(repo, tag)
    result = {**planned, "tag": tag, "repo": repo, "applied": apply}
    if not apply:
        return result
    version_bump.write_version(ROOT, str(planned["bump"]))
    changelog.release(ROOT, version, repo=repo, spec=str(planned["range"]))
    result["next"] = [
        f"核对 {changelog.CHANGELOG} 里 {version} 那一节的措辞，它是使用者唯一读到的说明",
        f"提交 {version_bump.VERSION_FILE} 与 {changelog.CHANGELOG}，"
        f"消息 chore(release): 版本 {version}",
        "推到 GitHub，等这个提交的 Test 工作流转绿",
        "回来跑 --apply 打标签",
    ]
    return result


def plan(repo: str) -> dict:
    _require_clean_master()
    sha = command("git", "rev-parse", "HEAD")
    if api(repo, "git/ref/heads/master")["object"]["sha"] != sha:
        raise ValueError("本地 HEAD 与 GitHub master 不一致，请先完成同步")
    version = version_bump.read_version(ROOT)
    tag = "v" + version
    document = (ROOT / changelog.CHANGELOG).read_text(encoding="utf-8")
    if not changelog.has_section(document, version):
        raise ValueError(f"{changelog.CHANGELOG} 缺少 {version} 一节；先用 --bump 起草再润色")
    _require_free_tag(repo, tag)
    if command("git", "tag", "--list", tag):
        raise ValueError(f"本地 {tag} 已存在，请先检查它的归属")
    return {**verify(repo, sha), "tag": tag, "repo": repo}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default="longmeidao/peach")
    parser.add_argument("--apply", action="store_true",
                        help="真的动手：带 --bump 时写版本号与变更日志，否则创建并推送标签")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bump", choices=("auto", "patch", "minor", "major"),
                      help="推进 __version__ 并起草变更日志，为下一次发布做准备")
    mode.add_argument("--verify-sha", help="仅核对指定提交的主线归属与 CI，供 Release 工作流使用")
    args = parser.parse_args(argv)
    try:
        if args.verify_sha:
            print(json.dumps(verify(args.repo, args.verify_sha), ensure_ascii=False, indent=2))
            return 0
        if args.bump:
            print(json.dumps(prepare(args.repo, args.bump, apply=args.apply),
                             ensure_ascii=False, indent=2))
            return 0
        result = plan(args.repo)
        if args.apply:
            # 创建前再次查询远端主线，拒绝把并发推进的 master 当成已核验版本。
            if api(args.repo, "git/ref/heads/master")["object"]["sha"] != result["sha"]:
                raise ValueError("检查期间 master 已更新，请重新执行")
            command("git", "tag", "-a", result["tag"], result["sha"],
                    "-m", f"Peach {result['tag']} Windows 测试版")
            command("git", "push", f"https://github.com/{args.repo}.git",
                    f"refs/tags/{result['tag']}")
        print(json.dumps({**result, "applied": args.apply}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, version_bump.VersionError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"发布检查未通过：{detail}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
