"""检查智能体上下文文件的结构与预算。

判据与清退机制见 `docs/adr/0015-agent-context-layering.md`。

- 结构与预算错误：退出码 1
- 只有 `最后复核` 超期：退出码 3
- 全部通过：退出码 0

导入本模块无任何文件、网络或数据库副作用。
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 不可越过的天花板。`SKILL.md` 与 description 用 Anthropic 官方 skill authoring 的值
# （正文 500 行、description 1024 字符硬校验）；入口文件没有官方值，由本项目定死为 200 行。
# 改这里等于取消闸门，只有在官方值变化时才动。
MAX_EVER = {
    "AGENTS.md": 200,
    "docs/HANDOFF.md": 260,
    "SKILL.md": 500,
    "description": 1024,
}

# 入口文件行数预算的变更记录：(值, 日期, 理由)。当前预算取每项最后一条。
# 预算只能降不能升。上调必须在同一改动里追加一条记录，写明这些内容为什么无法下沉到
# docs/ 或某个技能；理由为空或仍写「初始值」的上调会被判为错误。
BUDGET_CHANGES = {
    "AGENTS.md": [
        (70, "2026-08-17", "初始值"),
        (90, "2026-08-17", "术语表与覆盖声明是每个任务都要成立的常驻构件，下沉到技能即失效"),
    ],
    "docs/HANDOFF.md": [
        (260, "2026-08-17", "初始值"),
    ],
}

LINE_BUDGET = {name: changes[-1][0] for name, changes in BUDGET_CHANGES.items()}

SKILL_MAX_LINES = 120
DESCRIPTION_MAX_CHARS = 200
REVIEW_MAX_DAYS = 180

REVIEW_PATTERN = re.compile(r"^最后复核：(\d{4})-(\d{2})-(\d{2})\s*$", re.MULTILINE)
SKILL_LINK_PATTERN = re.compile(r"`(\.claude/skills/[^`]+/SKILL\.md)`")


def _count_lines(text: str) -> int:
    return len(text.splitlines())


def _parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, sep, value = line.partition(":")
        if sep and not key.startswith(" "):
            fields[key.strip()] = value.strip()
    return None


def _skill_files(root: Path) -> list[Path]:
    skills = root / ".claude" / "skills"
    if not skills.is_dir():
        return []
    return sorted(skills.glob("*/SKILL.md"))


def check_budget_history() -> list[str]:
    """预算只能降不能升；上调必须留下理由；任何值都不得越过天花板。"""
    problems: list[str] = []
    for name, changes in BUDGET_CHANGES.items():
        if not changes:
            problems.append(f"{name}: 缺少预算变更记录")
            continue
        ceiling = MAX_EVER.get(name)
        previous = None
        for value, date, reason in changes:
            if ceiling is not None and value > ceiling:
                problems.append(f"{name}: 预算 {value} 越过天花板 {ceiling}（{date}）")
            if previous is not None and value > previous:
                if not reason.strip() or reason.strip() == "初始值":
                    problems.append(
                        f"{name}: {previous} → {value}（{date}）是上调，必须写明"
                        "这些内容为什么无法下沉到 docs/ 或技能"
                    )
            previous = value

    if SKILL_MAX_LINES > MAX_EVER["SKILL.md"]:
        problems.append(
            f"SKILL.md 预算 {SKILL_MAX_LINES} 越过天花板 {MAX_EVER['SKILL.md']}"
        )
    if DESCRIPTION_MAX_CHARS > MAX_EVER["description"]:
        problems.append(
            f"description 预算 {DESCRIPTION_MAX_CHARS} 越过天花板 {MAX_EVER['description']}"
        )
    return problems


def check_line_budgets(root: Path) -> list[str]:
    problems: list[str] = []
    for name, budget in LINE_BUDGET.items():
        path = root / name
        if not path.is_file():
            problems.append(f"{name}: 文件缺失")
            continue
        count = _count_lines(path.read_text(encoding="utf-8"))
        if count > budget:
            problems.append(f"{name}: {count} 行，超出预算 {budget} 行")
    return problems


def check_skills(root: Path) -> tuple[list[str], list[tuple[str, datetime.date]]]:
    problems: list[str] = []
    reviewed: list[tuple[str, datetime.date]] = []
    for path in _skill_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")

        count = _count_lines(text)
        if count > SKILL_MAX_LINES:
            problems.append(f"{rel}: {count} 行，超出技能预算 {SKILL_MAX_LINES} 行")

        fields = _parse_frontmatter(text)
        if fields is None:
            problems.append(f"{rel}: 缺少 --- 包裹的 frontmatter")
            continue

        name = fields.get("name", "")
        if name != path.parent.name:
            problems.append(f"{rel}: name `{name}` 与目录名 `{path.parent.name}` 不一致")

        description = fields.get("description", "")
        if not description:
            problems.append(f"{rel}: 缺少 description")
        elif len(description) > DESCRIPTION_MAX_CHARS:
            problems.append(
                f"{rel}: description {len(description)} 字符，超出 {DESCRIPTION_MAX_CHARS}"
            )

        match = REVIEW_PATTERN.search(text)
        if match is None:
            problems.append(f"{rel}: 缺少 `最后复核：YYYY-MM-DD` 行")
        else:
            try:
                reviewed.append((rel, datetime.date(*(int(part) for part in match.groups()))))
            except ValueError:
                problems.append(f"{rel}: `最后复核` 不是合法日期")
    return problems, reviewed


def check_skill_index(root: Path) -> list[str]:
    """`AGENTS.md` 的技能索引必须与实际文件一一对应。"""
    entry = root / "AGENTS.md"
    if not entry.is_file():
        return ["AGENTS.md: 文件缺失"]
    listed = set(SKILL_LINK_PATTERN.findall(entry.read_text(encoding="utf-8")))
    actual = {path.relative_to(root).as_posix() for path in _skill_files(root)}
    problems = [f"AGENTS.md 索引指向不存在的技能：{item}" for item in sorted(listed - actual)]
    problems += [f"技能未登记进 AGENTS.md 索引：{item}" for item in sorted(actual - listed)]
    return problems


def stale_reviews(
    reviewed: list[tuple[str, datetime.date]], today: datetime.date
) -> list[tuple[str, int]]:
    stale = []
    for rel, reviewed_on in reviewed:
        days = (today - reviewed_on).days
        if days > REVIEW_MAX_DAYS:
            stale.append((rel, days))
    return stale


def check_repo(root: Path) -> tuple[list[str], list[tuple[str, datetime.date]]]:
    problems = check_budget_history()
    problems += check_line_budgets(root)
    skill_problems, reviewed = check_skills(root)
    problems += skill_problems
    problems += check_skill_index(root)
    return problems, reviewed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查上下文文件的结构、预算与复核日期")
    parser.add_argument("--root", type=Path, default=ROOT, help="仓库根目录")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    problems, reviewed = check_repo(root)
    stale = stale_reviews(reviewed, datetime.date.today())

    for problem in problems:
        print(f"[错误] {problem}")
    for rel, days in stale:
        print(f"[超期] {rel}: 距最后复核 {days} 天，超过 {REVIEW_MAX_DAYS} 天，请复核或清退")

    if problems:
        return 1
    if stale:
        return 3
    print(f"上下文预算检查通过：{len(reviewed)} 个技能，{len(LINE_BUDGET)} 个入口文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
