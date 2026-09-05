"""核对 master 与同提交 CI；显式 --apply 创建并推送不可覆盖的版本标签。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

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


def plan(repo: str) -> dict:
    if command("git", "status", "--porcelain"):
        raise ValueError("工作区不干净")
    if command("git", "branch", "--show-current") != "master":
        raise ValueError("请从 master 主检出执行")
    sha = command("git", "rev-parse", "HEAD")
    if api(repo, "git/ref/heads/master")["object"]["sha"] != sha:
        raise ValueError("本地 HEAD 与 GitHub master 不一致，请先完成同步")
    source = (ROOT / "src/peach/__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "(\d+\.\d+\.\d+)"$', source, re.M)
    if not match:
        raise ValueError("版本必须是 X.Y.Z")
    tag = "v" + match[1]
    # matching-refs 返回空列表代表不存在；网络或权限错误不能被当成空列表。
    if any(ref["ref"] == f"refs/tags/{tag}" for ref in api(repo, f"git/matching-refs/tags/{tag}")):
        raise ValueError(f"{tag} 已存在，不覆盖；发布新版本请先更新 __version__")
    if command("git", "tag", "--list", tag):
        raise ValueError(f"本地 {tag} 已存在，请先检查它的归属")
    return {**verify(repo, sha), "tag": tag, "repo": repo}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="longmeidao/peach")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="创建并推送标签，触发预发布")
    mode.add_argument("--verify-sha", help="仅核对指定提交的主线归属与 CI，供 Release 工作流使用")
    args = parser.parse_args(argv)
    try:
        result = verify(args.repo, args.verify_sha) if args.verify_sha else plan(args.repo)
        if args.apply:
            # 创建前再次查询远端主线，拒绝把并发推进的 master 当成已核验版本。
            if api(args.repo, "git/ref/heads/master")["object"]["sha"] != result["sha"]:
                raise ValueError("检查期间 master 已更新，请重新执行")
            command("git", "tag", "-a", result["tag"], result["sha"],
                    "-m", f"Peach {result['tag']} Windows 测试版")
            command("git", "push", f"https://github.com/{args.repo}.git", f"refs/tags/{result['tag']}")
        print(json.dumps({**result, "applied": args.apply}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"发布检查未通过：{detail}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
