"""核对交付提交的署名：哪个工具、哪个模型写的这一段代码。"""

from __future__ import annotations

import re
from pathlib import Path

from .check_readme_impact import git

#: 已登记的工具与它厂商的 noreply 地址。换用别的智能体就在这里加一行，别散着写。
VENDORS = {
    "Claude Code": "noreply@anthropic.com",
    "Codex": "noreply@openai.com",
    "opencode": "noreply@opencode.ai",
}

#: 署名形态：`工具 (模型 版本) <厂商 noreply>`。括号里那一段是重点——同一个工具换代
#: 模型，写出来的代码差别比换工具本身还大，事后翻这一行是要知道哪个模型写的。
FORM = re.compile(r"(?P<tool>[^()<>]+) \((?P<model>[^()]+)\) <(?P<mail>[^<>\s]+)>")

EXAMPLE = "Co-Authored-By: Claude Code (Opus 5) <noreply@anthropic.com>"


def values(repo: Path, head: str = "HEAD") -> list[str]:
    """交付提交末尾那一块里的 Co-Authored-By，原样取值。"""
    message = git(repo, "show", "-s", "--format=%B", head)
    trailers = git(repo, "interpret-trailers", "--parse", message=message)
    return [line.partition(":")[2].strip() for line in trailers.splitlines()
            if line.partition(":")[0].casefold() == "co-authored-by"]


def check(repo: Path, head: str = "HEAD") -> list[str]:
    """交付提交至少要有一条署名，且每一条都合规。

    署名是事后追责唯一的入手处：出问题的那一行是哪个工具的哪个模型写的，只能从这里看。
    所以缺了、形态不对、工具没登记、地址与工具不配，四种都拒收。多条并列是允许的，
    一个提交确实可能由两个智能体接力写成。
    """
    found = values(repo, head)
    if not found:
        return [f"交付提交须有 Co-Authored-By 写明工具与模型，如 {EXAMPLE}"]
    problems = []
    for value in found:
        parsed = FORM.fullmatch(value)
        if parsed is None:
            problems.append(f"署名「{value}」形态不对，须为 工具 (模型 版本) "
                            f"<厂商 noreply>，如 {EXAMPLE}")
        elif parsed["tool"] not in VENDORS:
            problems.append(f"署名里的工具「{parsed['tool']}」未登记，"
                            "已登记：" + "、".join(VENDORS))
        elif parsed["mail"] != VENDORS[parsed["tool"]]:
            problems.append(f"{parsed['tool']} 的署名地址须是 "
                            f"{VENDORS[parsed['tool']]}，不是 {parsed['mail']}")
    return problems
