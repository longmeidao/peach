"""变更日志：从 Conventional Commits 起草，发布时把未发布节定版。

格式遵循 Keep a Changelog 1.1.0（https://keepachangelog.com/zh-CN/1.1.0/），版本号遵循
Semantic Versioning 2.0.0（https://semver.org/lang/zh-CN/spec/v2.0.0.html）：`## [未发布]`
常在，每个发布一节 `## [X.Y.Z] - YYYY-MM-DD`，分组标题固定，底部给 compare 链接。

草稿按提交主题分组，措辞要人改成使用者读得懂的话——规范的第一条原则就是变更日志写给
人看，不是 `git log` 的转储。只改开发过程的提交（`docs`、`test`、`chore`、`refactor`）
不进日志。定版时未发布节里人润色过的内容整段搬进版本节，那一节空着才用草稿兜底。

    python scripts/changelog.py                                # 起草未发布区间
    python scripts/changelog.py --range v0.16.0..v0.27.1       # 起草任意区间
    python scripts/changelog.py --release 0.30.0 --apply       # 把未发布节定版为 0.30.0
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "scripts"
from . import version_bump

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = "CHANGELOG.md"

#: 未发布节的标题。Keep a Changelog 要求它常驻，让人随时知道主线上攒了什么。
UNRELEASED = "未发布"

#: Conventional Commits 的主题形状：`type(scope)!: 描述`。
SUBJECT = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!)?:\s*(?P<text>.+)$")

#: 破坏性变化的脚注写法，与主题里的 `!` 等效。
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE:\s*(?P<text>.+)$", re.M)

#: 提交类型到分组的映射。落在这里之外的类型只改开发过程，不进日志。
TYPE_GROUPS = {"feat": "新增", "feature": "新增", "fix": "修复", "perf": "变更"}

#: 这些 scope 下的改动只动开发过程，即使打成 `fix` 也不进面向使用者的日志。
SILENT_SCOPES = frozenset({"tests", "test", "docs", "doc", "ci", "skills", "agents"})

#: 分组的渲染顺序。空分组不渲染；「弃用」「移除」「安全」由人按需补，脚本不猜。
GROUP_ORDER = ("破坏性变化", "新增", "变更", "弃用", "移除", "修复", "安全")

#: 安全相关的提交：类型或 scope 点名 security 的一律进「安全」组。
SECURITY = "security"

#: 未发布节：标题到下一节标题或底部链接块之间的全部内容。
UNRELEASED_BLOCK = re.compile(
    rf"^## \[{UNRELEASED}\]\n(?P<body>.*?)(?=^## \[|^\[{UNRELEASED}\]:|\Z)", re.M | re.S)

#: 底部那条未发布链接。定版时它跟着指向新标签，新版本的链接紧跟其后。
UNRELEASED_LINK = re.compile(rf"^\[{UNRELEASED}\]:.*$", re.M)


@dataclass(frozen=True)
class Commit:
    subject: str
    body: str


def read_commits(root: Path, spec: str) -> list[Commit]:
    raw = version_bump.git(root, "log", "--no-merges", "--format=%s%x1f%b%x00", spec)
    commits = []
    for record in raw.split("\0"):
        if not record.strip():
            continue
        subject, _, body = record.strip("\n").partition("\x1f")
        commits.append(Commit(subject.strip(), body))
    return commits


def entry_for(commit: Commit) -> tuple[str, str] | None:
    """一个提交对应的（分组，条目文本）；不进日志的返回 None。"""
    match = SUBJECT.match(commit.subject)
    if match is None:
        return None
    kind, scope = match["type"], (match["scope"] or "").strip()
    if scope in SILENT_SCOPES:
        return None
    text = match["text"].strip().rstrip("。")
    footer = BREAKING_FOOTER.search(commit.body or "")
    if match["bang"] or footer:
        return "破坏性变化", _label(scope, footer["text"].strip() if footer else text)
    if SECURITY in (kind, scope):
        return "安全", _label(scope if scope != SECURITY else "", text)
    group = TYPE_GROUPS.get(kind)
    return (group, _label(scope, text)) if group else None


def _label(scope: str, text: str) -> str:
    return f"{scope}：{text}" if scope else text


def group_entries(commits) -> dict[str, list[str]]:
    """按分组收条目，保留首次出现的顺序并去掉重复措辞。"""
    grouped: dict[str, list[str]] = {}
    for commit in commits:
        found = entry_for(commit)
        if found is None:
            continue
        group, text = found
        bucket = grouped.setdefault(group, [])
        if text not in bucket:
            bucket.append(text)
    return {group: grouped[group] for group in GROUP_ORDER if group in grouped}


def render_body(grouped: dict[str, list[str]]) -> str:
    """分组与条目，不含节标题。"""
    parts: list[str] = []
    for group, entries in grouped.items():
        parts.extend((f"### {group}", ""))
        parts.extend(f"- {entry}" for entry in entries)
        parts.append("")
    return "\n".join(parts).rstrip("\n")


def draft(root: Path, spec: str) -> str:
    return render_body(group_entries(read_commits(root, spec)))


def compare_link(repo: str, previous: str | None, tag: str) -> str:
    base = f"https://github.com/{repo}"
    return f"{base}/compare/{previous}...{tag}" if previous else f"{base}/releases/tag/{tag}"


def has_section(document: str, version: str) -> bool:
    return re.search(rf"^## \[{re.escape(version)}\]", document, re.M) is not None


def promote(document: str, version: str, *, date: str, repo: str, previous: str | None,
            fallback: str = "") -> str:
    """把未发布节定版成 `version` 一节，并在它上面留一个空的未发布节。

    人在未发布节里润色过的措辞整段搬下去；那一节没有条目时才用 `fallback` 兜底。
    """
    if has_section(document, version):
        raise version_bump.VersionError(f"{CHANGELOG} 里已经有 {version} 这一节")
    match = UNRELEASED_BLOCK.search(document)
    if match is None:
        raise version_bump.VersionError(f"{CHANGELOG} 缺少 `## [{UNRELEASED}]` 这一节")
    body = match["body"].strip("\n")
    if "- " not in body:
        body = fallback.strip("\n")
    if not body.strip():
        raise version_bump.VersionError(f"{UNRELEASED}节是空的，这次发布没有可记录的变化")
    block = f"## [{UNRELEASED}]\n\n## [{version}] - {date}\n\n{body}\n\n"
    updated = document[:match.start()] + block + document[match.end():]
    return _relink(updated, repo=repo, version=version, previous=previous)


def _relink(document: str, *, repo: str, version: str, previous: str | None) -> str:
    tag = f"v{version}"
    if not UNRELEASED_LINK.search(document):
        raise version_bump.VersionError(f"{CHANGELOG} 缺少 `[{UNRELEASED}]:` 那条链接")
    document = UNRELEASED_LINK.sub(f"[{UNRELEASED}]: {compare_link(repo, tag, 'HEAD')}",
                                   document, count=1)
    definition = f"[{version}]: {compare_link(repo, previous, tag)}"
    return UNRELEASED_LINK.sub(lambda found: f"{found[0]}\n{definition}", document, count=1)


def release(root: Path, version: str, *, repo: str, spec: str, today: str | None = None) -> None:
    """把 `CHANGELOG.md` 的未发布节定版并落盘。"""
    path = root / CHANGELOG
    previous = spec.split("..")[0] if ".." in spec else version_bump.last_tag(root)
    updated = promote(path.read_text(encoding="utf-8"), version,
                      date=today or dt.date.today().isoformat(), repo=repo,
                      previous=previous, fallback=draft(root, spec))
    path.write_bytes(updated.encode("utf-8"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default="longmeidao/peach")
    parser.add_argument("--range", dest="spec", help="提交区间，默认上一个版本标签到 HEAD")
    parser.add_argument("--release", help=f"把{UNRELEASED}节定版成这个版本号")
    parser.add_argument("--apply", action="store_true", help=f"写进 {CHANGELOG}")
    args = parser.parse_args(argv)
    try:
        spec = args.spec or version_bump.release_range(ROOT)
        if not args.apply:
            heading = args.release or UNRELEASED
            body = draft(ROOT, spec) or "暂无面向使用者的变化。"
            print(f"## [{heading}]\n\n{body}")
            return 0
        if not args.release:
            raise version_bump.VersionError("--apply 必须同时给 --release")
        release(ROOT, args.release, repo=args.repo, spec=spec)
        print(f"{CHANGELOG} 的{UNRELEASED}节已定版成 {args.release}，请核对措辞。")
        return 0
    except version_bump.VersionError as error:
        print(f"变更日志未更新：{error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
