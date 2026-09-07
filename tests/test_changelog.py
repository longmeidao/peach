import unittest
from pathlib import Path

from scripts import changelog
from scripts.changelog import Commit, entry_for, group_entries, has_section, promote, render_body
from scripts.version_bump import VersionError

REPO = "owner/repo"

#: 一份最小的 `CHANGELOG.md`：头部、润色过的未发布节、一个发布节、底部链接块。
DOCUMENT = """# 变更日志

说明段。

## [未发布]

### 新增

- 配置页新增桌面快捷方式开关。

### 修复

- 忙态提示会说明正在进行的动作。

## [0.27.1] - 2026-09-06

第四个预发布。

[未发布]: https://github.com/owner/repo/compare/v0.27.1...HEAD
[0.27.1]: https://github.com/owner/repo/releases/tag/v0.27.1
"""


class EntryTests(unittest.TestCase):
    def test_only_user_facing_types_become_entries(self):
        self.assertEqual(entry_for(Commit("feat: 配置页并入管理菜单", "")),
                         ("新增", "配置页并入管理菜单"))
        self.assertEqual(entry_for(Commit("fix(web): 忙态提示说明在做什么", "")),
                         ("修复", "web：忙态提示说明在做什么"))
        self.assertEqual(entry_for(Commit("perf(media): 首段缩到 0.67 秒", "")),
                         ("变更", "media：首段缩到 0.67 秒"))
        for subject in ("docs: 记一笔", "test: 补断言", "chore(release): 版本 0.29.1",
                        "refactor(follow): 登记表收口", "style: 空行", "随手写的主题"):
            with self.subTest(subject=subject):
                self.assertIsNone(entry_for(Commit(subject, "")))

    def test_development_only_scopes_stay_out_even_under_fix(self):
        self.assertIsNone(entry_for(Commit("fix(tests): 断言跟上新名字", "")))
        self.assertIsNone(entry_for(Commit("fix(docs): 链接失效", "")))

    def test_breaking_changes_are_told_by_the_bang_or_the_footer(self):
        self.assertEqual(entry_for(Commit("fix!: 账本路径改成 location 键", "")),
                         ("破坏性变化", "账本路径改成 location 键"))
        self.assertEqual(
            entry_for(Commit("feat(config): 换掉盘符键", "BREAKING CHANGE: 设置文件要重写")),
            ("破坏性变化", "config：设置文件要重写"))

    def test_security_work_gets_its_own_group(self):
        self.assertEqual(entry_for(Commit("fix(security): 凭据不再进日志", "")),
                         ("安全", "凭据不再进日志"))

    def test_groups_keep_the_documented_order_and_drop_duplicates(self):
        grouped = group_entries([
            Commit("fix: 同一句", ""), Commit("feat: 新东西", ""),
            Commit("fix: 同一句", ""), Commit("fix!: 破坏性的", ""),
        ])
        self.assertEqual(list(grouped), ["破坏性变化", "新增", "修复"])
        self.assertEqual(grouped["修复"], ["同一句"])

    def test_the_body_is_markdown_with_one_blank_line_between_groups(self):
        body = render_body(group_entries([Commit("feat: 甲", ""), Commit("fix: 乙", "")]))
        self.assertEqual(body, "### 新增\n\n- 甲\n\n### 修复\n\n- 乙")


class PromoteTests(unittest.TestCase):
    def promoted(self, document: str = DOCUMENT, **overrides) -> str:
        options = {"date": "2026-09-07", "repo": REPO, "previous": "v0.27.1"}
        return promote(document, overrides.pop("version", "0.28.0"),
                       **{**options, **overrides})

    def test_the_unreleased_wording_moves_into_the_new_section(self):
        updated = self.promoted()
        self.assertIn("## [0.28.0] - 2026-09-07", updated)
        self.assertIn("- 配置页新增桌面快捷方式开关。", updated.split("## [0.28.0]")[1])
        self.assertTrue(has_section(updated, "0.28.0"))

    def test_an_empty_unreleased_section_is_left_behind_at_the_top(self):
        updated = self.promoted()
        between = updated.split(f"## [{changelog.UNRELEASED}]")[1].split("## [0.28.0]")[0]
        self.assertEqual(between.strip(), "")

    def test_the_sections_stay_in_descending_order(self):
        updated = self.promoted()
        self.assertLess(updated.index("## [0.28.0]"), updated.index("## [0.27.1]"))

    def test_both_compare_links_are_written(self):
        updated = self.promoted()
        self.assertIn("[未发布]: https://github.com/owner/repo/compare/v0.28.0...HEAD", updated)
        self.assertIn("[0.28.0]: https://github.com/owner/repo/compare/v0.27.1...v0.28.0",
                      updated)
        self.assertIn("[0.27.1]: https://github.com/owner/repo/releases/tag/v0.27.1", updated)

    def test_the_first_release_links_to_its_own_tag(self):
        document = DOCUMENT.replace(
            "## [0.27.1] - 2026-09-06\n\n第四个预发布。\n\n", "").replace(
            "[0.27.1]: https://github.com/owner/repo/releases/tag/v0.27.1\n", "").replace(
            "compare/v0.27.1...HEAD", "compare/v0.1.0...HEAD")
        updated = self.promoted(document, version="0.1.0", previous=None)
        self.assertIn("[0.1.0]: https://github.com/owner/repo/releases/tag/v0.1.0", updated)

    def test_a_draft_fills_in_when_nobody_wrote_the_unreleased_section(self):
        bare = DOCUMENT.replace(
            "### 新增\n\n- 配置页新增桌面快捷方式开关。\n\n"
            "### 修复\n\n- 忙态提示会说明正在进行的动作。\n\n", "")
        updated = promote(bare, "0.28.0", date="2026-09-07", repo=REPO, previous="v0.27.1",
                          fallback="### 新增\n\n- 起草出来的那条")
        self.assertIn("- 起草出来的那条", updated)

    def test_a_release_with_nothing_to_say_is_refused(self):
        bare = DOCUMENT.replace(
            "### 新增\n\n- 配置页新增桌面快捷方式开关。\n\n"
            "### 修复\n\n- 忙态提示会说明正在进行的动作。\n\n", "")
        with self.assertRaisesRegex(VersionError, "没有可记录的变化"):
            promote(bare, "0.28.0", date="2026-09-07", repo=REPO, previous="v0.27.1")

    def test_the_same_version_cannot_be_promoted_twice(self):
        with self.assertRaisesRegex(VersionError, "已经有 0.27.1"):
            self.promoted(version="0.27.1")

    def test_a_document_without_the_required_anchors_is_refused(self):
        with self.assertRaisesRegex(VersionError, "未发布"):
            self.promoted("# 变更日志\n\n## [0.27.1] - 2026-09-06\n")
        without_link = DOCUMENT.replace(
            "[未发布]: https://github.com/owner/repo/compare/v0.27.1...HEAD\n", "")
        with self.assertRaisesRegex(VersionError, "链接"):
            self.promoted(without_link)


class ShippedChangelogTests(unittest.TestCase):
    """仓库里那份 `CHANGELOG.md` 自己要符合脚本认的形状。"""

    def setUp(self):
        self.document = (Path(changelog.ROOT) / changelog.CHANGELOG).read_text(encoding="utf-8")

    def test_the_anchors_the_release_entry_needs_are_all_present(self):
        self.assertRegex(self.document, r"(?m)^## \[未发布\]$")
        self.assertRegex(self.document, r"(?m)^\[未发布\]: https://github\.com/")
        self.assertIn("keepachangelog.com", self.document)
        self.assertIn("semver.org", self.document)

    def test_every_released_section_carries_an_iso_date(self):
        headings = [line for line in self.document.splitlines()
                    if line.startswith("## [") and not line.startswith("## [未发布]")]
        self.assertTrue(headings, "至少要留一节已发布版本，compare 链条才接得上")
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertRegex(heading, r"^## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
