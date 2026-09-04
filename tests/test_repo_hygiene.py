"""仓库与顶层目录的卫生门槛。

这里守的都是「清理过一次、过几天又长回来」的东西。一次性清理解决不了它们：
2026-08-29 把顶层收敛到 4 个运行时目录、工作树清到 3 个，两天后顶层多出三个违规目录、
工作树长回 74 个。原因是规则只写在 `../attic/README.md`——仓库外、不进 Git、AGENTS.md
也没提，在 peach-app 里干活的人根本看不到。约定不是门槛。
"""
import ast
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

    def test_pending_operations_do_not_creep_back_into_the_entry_file(self):
        """编号待办只许住在这份文档里。

        `docs/STATUS.md` 每次会话开头都要读，23 条待办要占掉它三分之一的字节预算，
        其中十条还是「另行授权后才能跑」的操作，绝大多数任务读到它们只是白读。
        搬出去容易，长回来更容易，所以在这里钉住。
        """
        status = (DOCS / "STATUS.md").read_text(encoding="utf-8")
        self.assertNotIn("## 下一批工作", status, "待办去 docs/PRODUCT_BACKLOG.md，别放回入口文件")
        self.assertEqual(
            re.findall(r"^\d+\. ", status, re.M), [],
            "入口文件不留编号待办：写现状用无序列表，要做的事去 docs/PRODUCT_BACKLOG.md",
        )

    def test_the_section_headings_declare_their_own_counts(self):
        for heading, actual in (("已有骨架、尚未完成", self._numbered("## 已有骨架、尚未完成")),
                                ("尚未实现", self._numbered("## 尚未实现")),
                                ("待执行的操作", self._numbered("## 待执行的操作"))):
            declared = re.search(rf"## {heading}（(\d+) 项）", self.text)
            self.assertIsNotNone(declared, f"「{heading}」的标题应当带上条数，便于一眼核对")
            self.assertEqual(int(declared.group(1)), actual,
                             f"「{heading}」标题写的条数和实际列出的对不上")


#: 只属于某一台机器的字面量。它们要么住在设置文件里，要么由用户在命令行给，
#: 不能编译进 `src/peach/`——否则第一个陌生用户跑起来就连着别人家的坐标（ADR-0023）。
#: 挂载点与项目位置只在源码里拦：说明文档要讲清双机布局，就得点出具体落点。
PERSONAL_LITERAL = re.compile(
    r"""(?xi)
    Desktop[\\/]peach                                # 某一台机器的项目位置
    | lmd\.gg                                        # macOS 侧的目录名
    | [\\/]Users[\\/]longm                           # 用户目录
    | peach-win                                      # Windows 那台的 mDNS 名
    | peachsync                                      # SMB 账号名
    | Volumes[\\/](peach-sync|RESOURCES)             # macOS 上的具体挂载点
    | [\\/]IMSL[\\/]                                 # CloudDrive 挂载目录
    | \b192\.168\.\d{1,3}\.\d{1,3}                   # 局域网地址
    | \b10\.\d{1,3}\.\d{1,3}\.\d{1,3}
    | \b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}
    """
)

#: 全树一律不许出现的机器坐标：私网地址的具体一台、本机用户名、个人目录名、SMB 账号名，
#: 以及某一台机器的 mDNS 名。仓库公开后它们既是别人家的坐标又是个人信息（ADR-0023
#: 第四阶段）。要举例子就用 RFC 5737 的 192.0.2.0/24、198.51.100.0/24、203.0.113.0/24
#: 与中性主机名，那些地址不属于任何人，读者也不会照抄进自己的配置。
MACHINE_COORDINATE = re.compile(
    r"""(?xi)
    \b192\.168\.\d{1,3}\.\d{1,3}                     # 私网地址
    | \b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b
    | \b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}
    | longm                                          # 本机用户名与由它派生的账号
    | lmd[.-]gg                                      # 个人目录名与同名的托管项目
    | peachsync                                      # SMB 账号名
    | peach-win                                      # 某一台机器的 mDNS 名
    """
)

#: 门槛自身要写出它拦的形状，所以只有它自己豁免。
COORDINATE_EXEMPT_FILES = frozenset({"tests/test_repo_hygiene.py"})

#: 第三方代码与构建产物的措辞不由本仓库决定：Video.js 压缩产物里的 `longmapsto`
#: 就是一个 MathML 实体名，扫它只会得到噪声。
COORDINATE_EXEMPT_PREFIXES = ("web/vendor/", "web/dist/")


def _live_strings(path: pathlib.Path) -> list[tuple[int, str]]:
    """源码里真正会被当值用的字符串常量，去掉文档串。

    文档串和注释留给解释：说明「哪一台机器是 writer」时提到具体名字是有信息量的，
    把它编译成默认值才是问题。判据因此是 AST 而不是 grep。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef))
        and node.body and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return [(node.lineno, node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in docstrings]


class PersonalLiteralTests(unittest.TestCase):
    """`src/peach/` 里不许留只对某一台机器成立的默认值。"""

    def test_no_module_hardcodes_a_personal_coordinate(self):
        source = pathlib.Path(peach.__file__).parent
        offenders = []
        for path in sorted(source.rglob("*.py")):
            offenders += [
                f"{path.relative_to(source).as_posix()}:{line}：{text[:60]}"
                for line, text in _live_strings(path)
                if PERSONAL_LITERAL.search(text)
            ]
        self.assertEqual(offenders, [],
                         "把它搬进 <数据根>/config.toml（peach init --from-existing 会生成），"
                         "或者做成命令行参数")

    def test_the_guard_catches_the_shape_it_describes(self):
        """门槛自身也要能被证伪，否则它可能只是一段永远为真的代码。"""
        for sample in (r"C:\Users\longm\Desktop\peach\peach-data",
                       "~/Desktop/lmd.gg/peach", "peach-win.local", "peachsync",
                       "/Volumes/peach-sync", "https://192.168.50.162",
                       "/Volumes/RESOURCES/media", "/Users/x/Desktop/IMSL/115"):
            self.assertTrue(PERSONAL_LITERAL.search(sample), sample)
        for allowed in ("127.0.0.1", "0.0.0.0", "peach.local", "224.0.0.251",
                        "192.0.2.1", r"R:\media", "peach-data", "peach-sync",
                        "Chrome/131.0.0.0"):
            self.assertIsNone(PERSONAL_LITERAL.search(allowed), allowed)


class ReleaseFilesTests(unittest.TestCase):
    """公开发布必须齐备的治理文件（ADR-0023 第 4 阶段）。

    仓库一旦公开，许可证、贡献说明、安全说明和 issue/PR 模板就是陌生人判断「能不能用、
    怎么报问题」的唯一依据。缺一份的后果不是报错而是沉默：使用者无从判断授权范围，
    漏洞只能开成公开 issue。它们又都是「一次写好、之后没人再看」的文件，正是重构和
    路径调整时最容易被顺手删掉的那一类，所以在这里钉住存在性。
    """

    #: 相对仓库根的路径。清单只增不减，删除任何一项都要先改 ADR-0023。
    REQUIRED = (
        "LICENSE",
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/config.yml",
    )

    def test_every_release_file_exists_and_has_content(self):
        missing = [name for name in self.REQUIRED if not (REPO / name).is_file()]
        self.assertEqual(missing, [], "公开发布缺少治理文件")
        empty = [name for name in self.REQUIRED
                 if not (REPO / name).read_text(encoding="utf-8").strip()]
        self.assertEqual(empty, [], "治理文件存在但是空的，等于没有")

    def test_the_licence_is_the_agpl_v3(self):
        text = (REPO / "LICENSE").read_text(encoding="utf-8")
        for marker in ("GNU AFFERO GENERAL PUBLIC LICENSE", "Version 3"):
            self.assertIn(marker, text,
                          "许可证是 AGPL-3.0-or-later（ADR-0023 第 4 阶段），换许可证要先改 ADR")


class MachineCoordinateTests(unittest.TestCase):
    """Git 跟踪的每个文本文件都不许写出某一台机器的坐标。

    只管源码的门槛拦不住这件事：真实 IP、用户名和账号名过去散在测试夹具、安装脚本、
    ADR、状态文档与技能里，它们都不是「默认值」，公开仓库后却一样把用户的网络布局
    和账号名交出去。所以判据是 `git ls-files` 的全部文本，不是某个目录。
    """

    def _tracked_text_files(self):
        done = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                              capture_output=True, check=False)
        if done.returncode != 0:
            self.skipTest(f"git 不可用或不是仓库：{done.stderr.decode('utf-8', 'replace')}")
        for name in done.stdout.decode("utf-8").split("\0"):
            if not name or name in COORDINATE_EXEMPT_FILES:
                continue
            if name.startswith(COORDINATE_EXEMPT_PREFIXES):
                continue
            path = REPO / name
            if not path.is_file():
                continue
            raw = path.read_bytes()
            if b"\0" in raw:
                continue
            try:
                yield name, raw.decode("utf-8")
            except UnicodeDecodeError:
                continue

    def test_no_tracked_file_names_a_machine_coordinate(self):
        offenders = []
        for name, text in self._tracked_text_files():
            for number, line in enumerate(text.splitlines(), 1):
                found = MACHINE_COORDINATE.search(line)
                if found:
                    offenders.append(f"{name}:{number}：{found.group(0)}")
        self.assertEqual(
            offenders, [],
            "换成 RFC 5737 的文档地址（192.0.2.0/24、198.51.100.0/24、203.0.113.0/24）"
            "或中性的主机名、账号名、`<用户目录>` 这类占位",
        )

    def test_the_whole_tree_guard_catches_the_shape_it_describes(self):
        """门槛自身也要能被证伪，否则它可能只是一段永远为真的代码。"""
        for sample in ("https://192.168.50.162", "PEACH_SHARED_SMB_HOST=192.168.1.9",
                       "review_writer_origin = 'https://10.0.0.5'", "172.31.112.1",
                       r"C:\Users\longm\Desktop\peach", "~/Desktop/lmd.gg/peach",
                       "smb://peachsync@peach-win.local/peach-sync"):
            self.assertTrue(MACHINE_COORDINATE.search(sample), sample)
        for allowed in ("127.0.0.1", "0.0.0.0", "224.0.0.251", "198.18.0.1",
                        "192.0.2.2", "198.51.100.162", "203.0.113.1",
                        "peach.local", "peach-writer.local", "peach-sync",
                        "Chrome/131.0.0.0", "10.0.26200.1234", r"R:\media"):
            self.assertIsNone(MACHINE_COORDINATE.search(allowed), allowed)


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
