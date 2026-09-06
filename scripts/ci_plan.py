"""按提交影响生成 CI 矩阵；主线全量、Windows 系统回归与独立安装共同验收。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "scripts"
from . import test_runner as runner


def plan(event: str, paths: list[str], contents: dict | None = None) -> dict:
    scopes, _ = runner.scopes_for_changes(paths, contents=contents)
    wide = event == "workflow_dispatch" or "full" in scopes
    rows = []
    for system in ("macos-latest", "windows-latest"):
        scope = "full" if wide or event == "push" and system == "macos-latest" else (
            "core" if system == "windows-latest" else "auto")
        # 独立 runner 承担分片，避免共享文件、端口和全量证据锁。
        shards = 2 if scope == "full" else 1
        for index in range(shards):
            rows.append({"os": system, "python": "3.14", "scope": scope,
                         "shard_index": index, "shard_count": shards})
    # Python 下限覆盖关键兼容性；依赖和基础设施变化额外跑两端。
    rows.append({"os": "windows-latest", "python": "3.12", "scope": "core",
                 "shard_index": 0, "shard_count": 1})
    if wide:
        rows.append({"os": "macos-latest", "python": "3.12", "scope": "core",
                     "shard_index": 0, "shard_count": 1})
    wheels = [{"os": "windows-latest", "python": "3.12"},
              {"os": "macos-latest", "python": "3.14"}]
    if wide:
        wheels += [{"os": "windows-latest", "python": "3.14"},
                   {"os": "macos-latest", "python": "3.12"}]
    return {"matrix": {"include": rows}, "wheel_matrix": {"include": wheels}, "wide": wide}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, choices=("push", "pull_request", "workflow_dispatch"))
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        paths = runner.changed_files(root, args.base)
        result = plan(args.event, paths, runner.changed_contents(root, args.base, paths))
    except subprocess.CalledProcessError:
        # 首次推送、浅克隆或已删除基线：扩大验证，不能把无 diff 当成无需测试。
        result = plan("workflow_dispatch", [])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            for key in ("matrix", "wheel_matrix"):
                stream.write(f"{key}={json.dumps(result[key])}\n")


if __name__ == "__main__":
    main()
