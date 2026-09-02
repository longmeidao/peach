"""仓库与顶层目录的卫生门槛。

这里守的都是「清理过一次、过几天又长回来」的东西。一次性清理解决不了它们：
2026-08-29 把顶层收敛到 4 个运行时目录、工作树清到 3 个，两天后顶层多出三个违规目录、
工作树长回 74 个。原因是规则只写在 `../attic/README.md`——仓库外、不进 Git、AGENTS.md
也没提，在 peach-app 里干活的人根本看不到。约定不是门槛。
"""
import pathlib
import re
import subprocess
import unittest

import peach

REPO = pathlib.Path(peach.__file__).resolve().parents[2]
DOCS = REPO / "docs"

#: ADR-0017 定义的四个运行时目录，加一个归置处。顶层只允许这五项。
TOP_LEVEL_ALLOWED = {"peach-app", "peach-data", "peach-sync", "peach-worktrees", "attic"}


class TopLevelLayoutTests(unittest.TestCase):
    """顶层只放四个运行时目录加 attic/，且不放散落文件。

    在别的机器或 CI 上这个布局不成立（只 clone 了 peach-app），那里跳过——门槛要能在
    真实布局上拦住人，不能因为环境不同就把整套测试拖红。
    """

    def setUp(self):
        # 往上找真正的顶层，而不是 `REPO.parent`：测试几乎总是在隔离工作树里跑，那时
        # 上一级是 `peach-worktrees/`，判据不成立就会永远跳过——一个永远跳过的门槛
        # 等于没有，和它要防的失效是同一种。
        self.top = None
        for candidate in [REPO, *REPO.parents]:
            if all((candidate / name).is_dir()
                   for name in ("peach-app", "peach-data", "peach-worktrees")):
                self.top = candidate
                break
        if self.top is None:
            self.skipTest("不是双盘运行时布局（只 clone 了 peach-app），跳过")

    def test_only_the_runtime_directories_and_attic_live_at_the_top(self):
        extra = sorted(p.name for p in self.top.iterdir()
                       if p.is_dir() and p.name not in TOP_LEVEL_ALLOWED)
        self.assertEqual(
            extra, [],
            "顶层多了目录：`peach-` 前缀专属那四个运行时目录，别的东西进 attic/ 的"
            " builds／evidence／instances／tools／reviews，目录名写成 YYYYMMDD-主题",
        )

    def test_no_loose_files_at_the_top(self):
        loose = sorted(p.name for p in self.top.iterdir() if p.is_file())
        self.assertEqual(loose, [],
                         "顶层不放散落文件：文档进 attic/reviews/，产物进 attic/evidence/")


class BuiltInWorktreeTests(unittest.TestCase):
    """`.claude/worktrees/` 里不许留下未登记的目录。

    Claude Code 内置的工作树在分支被集成后会被回收，目录却留在原地，成了主检出里一份
    看不出区别的旧副本——在里面跑 git 全部作用于主检出的 master。别的会话此刻可能正
    合法地占着一个内置工作树，所以判据是「有没有登记」而不是「有没有目录」，登记过的
    放行，本测试也从不删东西。
    """

    def _git(self, *args: str) -> str:
        done = subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", check=False)
        if done.returncode != 0:
            self.skipTest(f"git 不可用或不是仓库：{done.stderr.strip()}")
        return done.stdout

    def test_no_unregistered_directory_lingers_under_claude_worktrees(self):
        # 主检出才有 `.claude/worktrees/`。`--git-common-dir` 在工作树里指向主检出的
        # `.git`，在主检出里是相对路径，所以统一按 REPO 解析再取上一级。
        common = pathlib.Path(self._git("rev-parse", "--git-common-dir").strip())
        main = (REPO / common).resolve().parent
        builtin = main / ".claude" / "worktrees"
        if not builtin.is_dir():
            return
        registered = {
            pathlib.Path(line[len("worktree "):]).resolve()
            for line in self._git("worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        }
        residue = sorted(child.name for child in builtin.iterdir()
                         if child.is_dir() and child.resolve() not in registered)
        self.assertEqual(
            residue, [],
            f"{builtin} 下有未登记的工作树残留：确认没人在用后手动删除，"
            "新工作树用 scripts/agent_worktree.py create 建在 peach-worktrees/",
        )


class BacklogSelfConsistencyTests(unittest.TestCase):
    """产品待办自己报的数必须和它列的条目对得上。

    测试逼不出「有人去更新 prose」，但能逼出「改了条目却忘了改总数」——那是这份文档
    最常见的失真，而且一旦失真，后面每次读它的人都会被那个总数误导。
    """

    def setUp(self):
        self.text = (DOCS / "PRODUCT_BACKLOG.md").read_text(encoding="utf-8")

    def _numbered(self, heading: str) -> int:
        body = self.text.split(heading, 1)[1].split("\n## ", 1)[0]
        return len(re.findall(r"^\d+\. ", body, re.M))

    def test_the_stated_totals_match_the_items_listed(self):
        skeleton = self._numbered("## 已有骨架、尚未完成")
        unbuilt = self._numbered("## 尚未实现")
        claimed = re.search(r"合计：\*\*(\d+) 项开放需求\*\*，其中 (\d+) 项已有骨架，(\d+) 项尚未实现",
                            self.text)
        self.assertIsNotNone(claimed, "结尾那句合计被改写了，请保持可核对的写法")
        total, said_skeleton, said_unbuilt = (int(g) for g in claimed.groups())
        self.assertEqual((said_skeleton, said_unbuilt), (skeleton, unbuilt),
                         "分项数和实际列出的条目对不上")
        self.assertEqual(total, skeleton + unbuilt, "合计和分项加起来对不上")

    def test_the_section_headings_declare_their_own_counts(self):
        for heading, actual in (("已有骨架、尚未完成", self._numbered("## 已有骨架、尚未完成")),
                                ("尚未实现", self._numbered("## 尚未实现"))):
            declared = re.search(rf"## {heading}（(\d+) 项）", self.text)
            self.assertIsNotNone(declared, f"「{heading}」的标题应当带上条数，便于一眼核对")
            self.assertEqual(int(declared.group(1)), actual,
                             f"「{heading}」标题写的条数和实际列出的对不上")


class ArchitectureDriftTests(unittest.TestCase):
    """架构文档点名的模块必须真的存在。

    它逼不出「架构变了要重写描述」，但能逼出「模块改名或删掉之后文档还在指它」——
    那种失真最难发现，因为文档读起来一切正常。
    """

    def test_every_module_the_document_names_still_exists(self):
        text = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
        source = pathlib.Path(peach.__file__).parent
        missing = sorted({
            name for name in re.findall(r"`src/peach/(\w+)\.py`", text)
            if not (source / f"{name}.py").is_file()
        })
        self.assertEqual(missing, [],
                         "架构文档还在指已经不存在的模块，改名或删除时请一起改")


if __name__ == "__main__":
    unittest.main()
