"""把 Dependabot 的清单升级接管到本地分支，顺手重算派生产物。默认只列计划，`--apply` 才提交。

Dependabot 只改 manifest 和 lock。根 `package.json` 的 npm 包还有一层派生产物——
`web/vendor/**` 的字节、`web/index.html` 里那行版本注释、每个 `ORIGIN.md` 的哈希与
lock integrity——它算不出来，于是 `npm run check:vendor` 在它的 PR 上必红（实际发生过：
lucide-static 1.38.0 → 1.40.0 的 PR #4）。`frontend/package.json` 同理，产物是
`web/dist/peach-ui.js`。

修不了那个 PR 本身：Dependabot 触发的 workflow 拿到的 token 是只读的，往
`dependabot/**` 推回重算的产物得靠 `pull_request_target` 或一个 PAT，两条都是给 CI 加
提权面。所以接管在本地做——凭据是你自己的，CI 一行都不用改。它做完这些：

1. 取那个 PR 的 head 分支，只把 manifest 与 lock 签出到当前分支；
2. `npm ci --ignore-scripts` 后重算这份清单对应的派生产物；
3. 列出真实改动的文件，`--apply` 时只暂存这些并提交。

测试不在这里跑：仓库只有一个测试入口，另拼一条会让 `test_evidence` 的记录对不上。
脚本最后印出该跑的命令与收尾的 `gh pr close`。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "scripts"
from . import co_author

ROOT = Path(__file__).resolve().parents[1]

#: 每份 manifest 的接管方式。`manifests` 是从 Dependabot 分支签出的文件，`derived` 是
#: 重算后可能变的路径前缀，`commands` 是重算命令。uv 与 github-actions 不在表里：
#: 它们没有派生产物，Dependabot 的 PR 直接合就行，接管反而多绕一圈。
RECIPES = {
    "web": {
        "label": "根 package.json（手工 vendor 的四个 web 包）",
        "manifests": ("package.json", "package-lock.json"),
        "derived": ("web/vendor/", "web/index.html"),
        "commands": (("npm", "ci", "--ignore-scripts"), ("npm", "run", "vendor:web")),
    },
    "frontend": {
        "label": "frontend/package.json（island 层构建依赖）",
        "manifests": ("frontend/package.json", "frontend/package-lock.json"),
        "derived": ("web/dist/",),
        "commands": (("npm", "--prefix", "frontend", "ci"),
                     ("npm", "--prefix", "frontend", "run", "build")),
    },
}


def run(command: tuple[str, ...] | list[str], *, capture: bool = True) -> str:
    """在仓库根目录跑一条命令，失败即抛。

    第一个词过一遍 `shutil.which`：Windows 上 `npm` 是 `npm.cmd`，而 `CreateProcess`
    不查 `PATHEXT`，照字面传就是 FileNotFoundError。
    """
    executable = shutil.which(command[0]) or command[0]
    result = subprocess.run([executable, *command[1:]], cwd=ROOT, capture_output=capture,
                            text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() if capture else ""
        raise RuntimeError(f"{' '.join(command)} 退出码 {result.returncode}\n{detail}")
    return (result.stdout or "") if capture else ""


def recipe_for(paths: list[str]) -> tuple[str, dict]:
    """一批改动文件属于哪份清单。

    同时动了两份就拒绝：那不是 Dependabot 的形状（一个 PR 只碰一个 ecosystem 的一个
    directory），硬按一份重算会把另一份的产物留在旧版本上。
    """
    matched = [key for key, recipe in RECIPES.items()
               if any(path in recipe["manifests"] for path in paths)]
    if not matched:
        known = "、".join(name for recipe in RECIPES.values() for name in recipe["manifests"])
        raise RuntimeError(f"这个分支没有改动带派生产物的清单（认得的是 {known}）。"
                           "uv 与 github-actions 的升级没有派生产物，直接合并那个 PR 即可。")
    if len(matched) > 1:
        raise RuntimeError(f"这个分支同时改了 {len(matched)} 份清单，逐份接管：{matched}")
    return matched[0], RECIPES[matched[0]]


def head_branch(pr: str) -> str:
    payload = json.loads(run(("gh", "pr", "view", pr, "--json", "headRefName,state")))
    if payload["state"] != "OPEN":
        raise RuntimeError(f"PR #{pr} 状态是 {payload['state']}，不是 OPEN")
    return payload["headRefName"]


def branch_changes(branch: str) -> list[str]:
    """那个分支自己改了哪些文件。

    判据是它与 `HEAD` 的合并基，不是 `HEAD` 本身：Dependabot 的分支从几天前的 master
    分出去，直接 `git diff origin/<branch>` 会把这几天 master 上的每一次改动也算进来，
    于是每个 PR 看上去都动了清单。
    """
    return [line for line in
            run(("git", "diff", "--name-only", "--merge-base", "HEAD", f"origin/{branch}")).splitlines()
            if line]


def working_changes() -> list[str]:
    return [line for line in run(("git", "diff", "--name-only", "HEAD")).splitlines() if line]


def commit_message(key: str, versions: list[str], pr: str | None,
                   signature: str) -> str:
    """接管提交的说明。README-Impact 与 Co-Authored-By 必须同一个 trailer 块、中间不空行。

    署名由 `--co-author` 传进来，脚本不替谁署名：跑它的可能是任一个智能体，写死一个
    工具名就是往提交历史里记错人。形态由 `co_author.FORM` 判，这里提前判一次，免得
    错在 `ready` 才报出来。
    """
    if co_author.FORM.fullmatch(signature) is None:
        raise ValueError("--co-author 形态须为 工具 (模型 版本) <厂商 noreply>，如 "
                         + co_author.EXAMPLE.partition(": ")[2])
    origin = f"Dependabot PR #{pr}" if pr else "Dependabot 分支"
    rebuild = "`" + "`、`".join(" ".join(item) for item in RECIPES[key]["commands"]) + "`"
    return (f"chore(deps): 接管 {RECIPES[key]['label']} 的升级\n\n"
            f"{origin} 只改了 manifest 与 lock。派生产物由 {rebuild} 重算，"
            "它在只读 token 下算不出来，所以接管到本地分支一起提交。\n\n"
            + ("升级：" + "、".join(versions) + "\n\n" if versions else "")
            + "README-Impact: none; 依赖版本与派生产物，README 不涉及。\n"
            + f"Co-Authored-By: {signature}\n")


def manifest_versions(key: str) -> list[str]:
    """从签出的清单里读出被改掉的版本，只为写进提交说明。"""
    lines = []
    for name in RECIPES[key]["manifests"]:
        if not name.endswith("package.json"):
            continue
        before = json.loads(run(("git", "show", f"HEAD:{name}")) or "{}")
        after = json.loads((ROOT / name).read_text(encoding="utf-8"))
        for section in ("dependencies", "devDependencies"):
            old, new = before.get(section, {}), after.get(section, {})
            lines += [f"{package} {old.get(package, '新增')} → {version}"
                      for package, version in new.items() if old.get(package) != version]
    return lines


def owned_by(recipe: dict, path: str) -> bool:
    """这个路径是不是本次接管该动的。以 `/` 结尾的 `derived` 是目录，其余按整条比。"""
    return path in recipe["manifests"] or any(
        path.startswith(prefix) if prefix.endswith("/") else path == prefix
        for prefix in recipe["derived"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="Dependabot 的 PR 编号")
    source.add_argument("--branch", help="Dependabot 的分支名，跳过 gh 查询")
    parser.add_argument("--apply", action="store_true", help="暂存并提交；缺省只列计划")
    parser.add_argument("--co-author", required=True,
                        help="本次提交的署名，形如 "
                             "Claude Code (Opus 5) <noreply@anthropic.com>")
    args = parser.parse_args(argv)

    try:
        if run(("git", "rev-parse", "--git-dir")).strip() == run(("git", "rev-parse", "--git-common-dir")).strip():
            raise RuntimeError("这是主检出。主检出只做集成，先 "
                               "`scripts/agent_worktree.py create --agent <名> --task deps-<包名>`。")
        if run(("git", "status", "--porcelain")).strip():
            raise RuntimeError("工作区不干净。接管会往里写重算出来的产物，先把手上的改动收掉。")
        branch = args.branch or head_branch(args.pr)
        run(("git", "fetch", "origin", branch))
        key, recipe = recipe_for(branch_changes(branch))
        run(("git", "checkout", f"origin/{branch}", "--", *recipe["manifests"]))
        run(("git", "reset", "--quiet", "--", *recipe["manifests"]))
        versions = manifest_versions(key)
        for command in recipe["commands"]:
            run(command, capture=False)
        # 只认真实变了的那些。清单动了产物却一个字节没变是常事（补丁版没碰 vendored 的
        # 那几个文件），照 `derived` 前缀盲暂存会把无关文件带上。
        touched = working_changes()
        landed = sorted(path for path in touched if owned_by(recipe, path))
        stray = sorted(path for path in touched if not owned_by(recipe, path))
        plan = {"ok": not stray, "branch": branch, "recipe": key, "versions": versions,
                "files": landed, "unexpected": stray, "applied": False,
                "next": ["测试：& .\\scripts\\test.ps1 full（清单在 FULL_ONLY_PREFIXES 里）",
                         "交付：scripts/agent_worktree.py ready，再由协调者 integrate"]}
        if stray:
            plan["error"] = "重算动到了清单与派生产物之外的文件，先看清楚这些改动再决定"
        elif args.apply:
            run(("git", "add", "--", *landed))
            message = ROOT / "build" / f"adopt-{key}.txt"
            message.parent.mkdir(parents=True, exist_ok=True)
            message.write_text(commit_message(key, versions, args.pr, args.co_author), encoding="utf-8", newline="\n")
            run(("git", "commit", "--quiet", "-F", str(message)))
            message.unlink()
            plan["applied"] = True
            plan["head"] = run(("git", "rev-parse", "HEAD")).strip()
            if args.pr:
                plan["next"].append(f"收尾：gh pr close {args.pr} --delete-branch "
                                    '--comment "派生产物需要本地重算，已接管进 master"')
        else:
            plan["next"].insert(0, "重算的产物留在工作区未暂存："
                                   f"`git restore -- {' '.join(landed)}` 撤销，加 --apply 提交")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0 if plan["ok"] else 1
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
