#!/usr/bin/env python3
"""检查可变外部 Markdown 与 Peach 锁定快照之间的漂移。"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "docs" / "reference-sources.json"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_bytes(url: str, *, timeout: float = 20.0) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/markdown,text/plain;q=0.9,*/*;q=0.1",
            "User-Agent": "Peach-reference-update-check/1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def resolve_git_revision(source: dict, *, timeout: float = 20.0) -> str | None:
    git = source.get("git")
    if not git:
        return None
    result = subprocess.run(
        ["git", "ls-remote", git["repository"], git["ref"]],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=timeout,
    )
    lines = result.stdout.strip().splitlines()
    if len(lines) != 1:
        raise RuntimeError(f"{source['id']} 无法唯一解析 {git['ref']}")
    return lines[0].split()[0]


def validate_registry(root: Path, registry: dict) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for source in registry.get("sources", []):
        source_id = source.get("id", "<missing>")
        if source_id in seen:
            problems.append(f"来源 id 重复：{source_id}")
        seen.add(source_id)
        snapshot = root / source.get("snapshot", "")
        if not snapshot.is_file():
            problems.append(f"{source_id} 缺少锁定快照：{snapshot}")
            continue
        actual = sha256_bytes(snapshot.read_bytes())
        if actual != source.get("sha256"):
            problems.append(
                f"{source_id} 快照校验失败：登记 {source.get('sha256')}，实际 {actual}"
            )
        git = source.get("git")
        if git and len(git.get("revision", "")) != 40:
            problems.append(f"{source_id} 的 Git revision 不是完整 40 位提交")
    return problems


def unified_diff(source: dict, old: bytes, new: bytes) -> str:
    old_lines = old.decode("utf-8", errors="replace").splitlines(keepends=True)
    new_lines = new.decode("utf-8", errors="replace").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{source['id']}@locked",
            tofile=f"{source['id']}@live",
        )
    )


def inspect_source(
    root: Path,
    source: dict,
    *,
    fetcher: Callable[[str], bytes] = fetch_bytes,
    revision_resolver: Callable[[dict], str | None] = resolve_git_revision,
) -> dict:
    snapshot = (root / source["snapshot"]).read_bytes()
    live = fetcher(source["url"])
    live_sha = sha256_bytes(live)
    live_revision = revision_resolver(source)
    pinned_revision = (source.get("git") or {}).get("revision")
    changed = live_sha != source["sha256"] or live_revision != pinned_revision
    return {
        "id": source["id"],
        "changed": changed,
        "pinned_sha256": source["sha256"],
        "live_sha256": live_sha,
        "pinned_revision": pinned_revision,
        "live_revision": live_revision,
        "diff": unified_diff(source, snapshot, live) if changed else "",
        "live": live,
    }


def selected_sources(registry: dict, source_id: str | None) -> list[dict]:
    sources = registry.get("sources", [])
    if source_id is None:
        return sources
    selected = [source for source in sources if source.get("id") == source_id]
    if not selected:
        raise ValueError(f"未知来源：{source_id}")
    return selected


def command_check(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).resolve()
    root = registry_path.parents[1]
    registry = load_registry(registry_path)
    problems = validate_registry(root, registry)
    if problems:
        for problem in problems:
            print(f"错误：{problem}", file=sys.stderr)
        return 2

    changed = False
    for source in selected_sources(registry, args.source):
        result = inspect_source(root, source)
        if result["changed"]:
            changed = True
            print(
                f"有更新：{result['id']}\n"
                f"  SHA-256 {result['pinned_sha256']} -> {result['live_sha256']}"
            )
            if result["pinned_revision"] is not None:
                print(
                    f"  revision {result['pinned_revision']} -> {result['live_revision']}"
                )
            if args.diff:
                print(result["diff"], end="" if result["diff"].endswith("\n") else "\n")
        else:
            suffix = (
                f"，revision {result['live_revision']}"
                if result["live_revision"] is not None
                else ""
            )
            print(f"未变化：{result['id']}，SHA-256 {result['live_sha256']}{suffix}")
    return 1 if changed else 0


def command_accept(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).resolve()
    root = registry_path.parents[1]
    registry = load_registry(registry_path)
    source = selected_sources(registry, args.source)[0]
    result = inspect_source(root, source)
    if result["live_sha256"] != args.expected_sha256.lower():
        print("拒绝接受：线上 SHA-256 与 --expected-sha256 不一致", file=sys.stderr)
        return 2
    if result["live_revision"] is not None:
        if result["live_revision"] != args.expected_revision:
            print("拒绝接受：线上 revision 与 --expected-revision 不一致", file=sys.stderr)
            return 2

    (root / source["snapshot"]).write_bytes(result["live"])
    source["sha256"] = result["live_sha256"]
    source["checked_on"] = dt.date.today().isoformat()
    if result["live_revision"] is not None:
        source["git"]["revision"] = result["live_revision"]
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已锁定 {source['id']}；这一步没有修改任何 Peach 实现。")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    sub = result.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="只读检查上游是否变化")
    check.add_argument("--source")
    check.add_argument("--diff", action="store_true", help="显示与锁定快照的差异")
    check.set_defaults(func=command_check)
    accept = sub.add_parser("accept", help="在人工审阅后更新快照和锁文件")
    accept.add_argument("--source", required=True)
    accept.add_argument("--expected-sha256", required=True)
    accept.add_argument("--expected-revision")
    accept.set_defaults(func=command_accept)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(f"检查失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
