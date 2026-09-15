"""函数复杂度棘轮：已经很复杂的函数不许再长，新函数不许长到那个程度。

2026-09-13 全仓盘点，`src/peach/` 与 `scripts/` 里分支数达到 30 的函数有 42 个，
最大的两个（`library_processing.process_library`、`web_batch.q_ads`）分别是 91 与 85。
它们不是一次写成的，是每次「顺手加一个 if」堆出来的；这个门槛拦的就是那一个 if。

计数是纯 AST 分支数：每个 `if`／`elif`／`for`／`while`／`except`／`with`／`assert`、
每个推导式子句、每个 `and`／`or`、每个 `case` 与条件表达式各计 1，嵌套函数算进
外层。数值只和它自己比，不和别的工具比。

基线只能降：函数变简单了就把基线改小，降到限值以下就把它从表里删掉；想调大要么
拆函数，要么在同一次改动里写明为什么这一处非长不可。
"""
import ast
import pathlib
import unittest

import peach

REPO = pathlib.Path(peach.__file__).resolve().parents[2]
SOURCE_ROOTS = (REPO / "src" / "peach", REPO / "scripts")

#: 达到这个分支数的函数进入基线；基线之外的函数不许长到这里。
LIMIT = 30

#: 键是 `<仓库相对路径>:<限定名>`，值是盘点当天的分支数。
BASELINE: dict[str, int] = {
    "src/peach/library_processing.py:process_library": 74,
    "src/peach/web_batch.py:q_ads": 85,
    "scripts/scrape_codes.py:_scrape": 77,
    "scripts/localize_performer_names.py:collect": 64,
    "src/peach/web_review.py:_review_rows": 61,
    "src/peach/web_resource_sync.py:_resource_orphan_plan": 60,
    "src/peach/fanbox.py:normalize_fanbox_post": 59,
    "src/peach/web_follow.py:q_follow": 52,
    "scripts/merge_duplicate_identities.py:collect": 50,
    "src/peach/jav_cover_fetch.py:run": 50,
    "src/peach/web_review.py:_apply_metadata_candidate": 48,
    "src/peach/web_review.py:_attach_review_asset_context": 46,
    "src/peach/web_review.py:w_review_decision": 46,
    "scripts/harvest_social_avatars.py:run": 45,
    "scripts/fetch_studio_avatar_candidates.py:main": 44,
    "src/peach/web_catalog.py:q_item": 44,
    "src/peach/web_follow.py:q_follow_authors": 44,
    "scripts/test_runner.py:main": 43,
    "scripts/sheets.py:run": 40,
    "src/peach/api.py:create_app": 40,
    "src/peach/taste_history.py:_taste_analysis": 40,
    "src/peach/web_catalog.py:catalog_filter": 40,
    "scripts/audit_domain_codes.py:collect": 39,
    "src/peach/web_catalog.py:q_items": 38,
    "scripts/harvest_social_avatars.py:harvest_entity": 37,
    "scripts/probe.py:run": 36,
    "src/peach/web_scraping.py:_fetch_cover": 35,
    "scripts/merge_duplicate_identities.py:collect_repeated_projections": 34,
    "src/peach/fc2_similarity.py:media_evidence": 34,
    "scripts/clean_names.py:run": 33,
    "scripts/harvest_studio_icons.py:icon_row": 32,
    "scripts/smoke_desktop.py:main": 32,
    "src/peach/jav_cover_fetch.py:best_cover": 32,
    "scripts/find_ads.py:find_candidates": 31,
    "scripts/rehome_unknown_jav.py:build_plan": 31,
    "src/peach/media_configuration.py:validate": 30,
    "src/peach/resource_identification.py:ingest_results": 30,
}

BRANCHES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
            ast.With, ast.AsyncWith, ast.Assert, ast.IfExp, ast.match_case)


def complexity(node: ast.AST) -> int:
    """`node` 的分支数加一：一条直线的函数是 1。"""
    total = 1
    for child in ast.walk(node):
        if isinstance(child, BRANCHES):
            total += 1
        elif isinstance(child, ast.comprehension):
            total += 1 + len(child.ifs)
        elif isinstance(child, ast.BoolOp):
            total += len(child.values) - 1
    return total


def functions(path: pathlib.Path):
    """`path` 里每个函数与方法的 `(限定名, 分支数)`；嵌套函数并进外层，不单列。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def walk(body, prefix):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield prefix + node.name, complexity(node)
            elif isinstance(node, ast.ClassDef):
                yield from walk(node.body, prefix + node.name + ".")

    yield from walk(tree.body, "")


def survey() -> dict[str, int]:
    """当前树里每个函数的分支数，键与 `BASELINE` 同形。"""
    found = {}
    for root in SOURCE_ROOTS:
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(REPO).as_posix()
            for name, value in functions(path):
                found[f"{relative}:{name}"] = value
    return found


class ComplexityRatchetTests(unittest.TestCase):
    def test_the_counter_counts_the_shapes_it_names(self):
        source = (
            "def f(items):\n"
            "    for item in items:\n"
            "        if item and item.ok or item.forced:\n"
            "            try:\n"
            "                pass\n"
            "            except ValueError:\n"
            "                pass\n"
            "    return [x for x in items if x]\n"
        )
        node = ast.parse(source).body[0]
        # 1 + for + if + and + or + except + 推导式 + 推导式的 if
        self.assertEqual(complexity(node), 8)

    def test_no_function_grew_past_its_baseline(self):
        current = survey()
        grown = sorted(
            f"{key}: {value}（基线 {BASELINE.get(key, LIMIT - 1)}）"
            for key, value in current.items()
            if value > BASELINE.get(key, LIMIT - 1))
        self.assertEqual(grown, [],
                         "这些函数的分支数超过了基线，拆出去或在同一次改动里说明理由：\n  "
                         + "\n  ".join(grown))

    def test_the_baseline_only_ratchets_down(self):
        current = survey()
        stale = sorted(
            f"{key}: 现在 {current.get(key, '不存在')}，基线 {value}"
            for key, value in BASELINE.items()
            if key not in current or current[key] < value)
        self.assertEqual(stale, [],
                         "基线落后于代码：函数变简单或删掉了就把这里改小或删掉，"
                         "基线不能替将来的增长留余量：\n  " + "\n  ".join(stale))

    def test_the_baseline_holds_only_functions_at_or_over_the_limit(self):
        below = sorted(key for key, value in BASELINE.items() if value < LIMIT)
        self.assertEqual(below, [], f"低于 {LIMIT} 的函数不该进基线：{below}")


if __name__ == "__main__":
    unittest.main()
