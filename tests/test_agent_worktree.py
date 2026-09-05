import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import agent_worktree
from scripts.agent_worktree import (
    WorkspaceError, _git, _lines, bump_part_for, bump_version, create, integrate, prune, read_version,
    ready, runtime_inputs_changed,
)

#: 版本号的唯一来源，`src/peach/__init__.py` 在测试仓库里的最小复刻。
VERSION_SEED = b'"""Peach application package."""\n\n__version__ = "0.7.14"\n'


class StuckRemoval:
    """复刻 2026-09-01 Windows 上的实测：目录句柄被别的进程占着，
    `git worktree remove` 报 Permission denied。

    `residue`：git 已经把文件删光、注册也摘掉了，只剩一个空目录删不掉。
    `stuck`：注册还在，工作树整个没摘掉。
    """

    def __init__(self, real, modes: dict[Path, str]):
        self.real = real
        self.modes = {path.resolve(): mode for path, mode in modes.items()}

    def __call__(self, repo, *args, **kwargs):
        mode = None
        if args[:2] == ("worktree", "remove"):
            mode = self.modes.get(Path(args[-1]).resolve())
        if mode is None:
            return self.real(repo, *args, **kwargs)
        path = Path(args[-1])
        if mode == "residue":
            self.real(repo, *args, check=False)
            path.mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(
            list(args), 1, "", f"fatal: failed to delete '{path}': Permission denied")


def commit(repo: Path, message: str) -> None:
    _git(repo, "add", "tracked.txt", "worker.txt")
    _git(repo, "commit", "-m", message)


class AgentWorktreeTests(unittest.TestCase):
    def setUp(self):
        self.verification = mock.patch.object(agent_worktree, "require_verified")
        self.verification.start()
        self.addCleanup(self.verification.stop)
        self.tmp = tempfile.TemporaryDirectory()
        # 先 resolve：prune 报告的是 git worktree list 给出的真实路径，而 CI runner 的
        # 临时目录是别名（macOS /var 软链到 /private/var，Windows 的 RUNNER~1 短名展开
        # 成 runneradmin）。拿未 resolve 的路径去比对，本机全绿、CI 全红。
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-b", "master", str(self.repo)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _git(self.repo, "config", "user.email", "test@example.invalid")
        _git(self.repo, "config", "user.name", "Peach Test")
        (self.repo / ".gitignore").write_text("build/\n", encoding="utf-8")
        _git(self.repo, "add", ".gitignore")
        (self.repo / "tracked.txt").write_text("base\n", encoding="utf-8")
        (self.repo / "worker.txt").write_text("base\n", encoding="utf-8")
        (self.repo / "src" / "peach").mkdir(parents=True)
        (self.repo / "src" / "peach" / "__init__.py").write_bytes(VERSION_SEED)
        _git(self.repo, "add", "src/peach/__init__.py")
        commit(self.repo, "base")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_ready_and_integrate_non_overlapping_branch(self):
        result = create(self.repo, "Claude", "metadata batch", self.root / "worktrees")
        worker = Path(result["path"])
        (worker / "worker.txt").write_text("worker\n", encoding="utf-8")
        commit(worker, "worker change")
        report = ready(worker)
        self.assertEqual(report["same_file_changes"], [])
        merged = integrate(self.repo, str(result["branch"]))
        self.assertIn("worker.txt", merged["files"])
        self.assertEqual((self.repo / "worker.txt").read_text(encoding="utf-8"), "worker\n")

    def test_ready_rejects_dirty_worker(self):
        result = create(self.repo, "Codex", "dirty task", self.root / "worktrees")
        worker = Path(result["path"])
        (worker / "worker.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(WorkspaceError, "dirty"):
            ready(worker)

    def test_integrate_refuses_same_file_changed_on_both_branches(self):
        result = create(self.repo, "Claude", "overlap", self.root / "worktrees")
        worker = Path(result["path"])
        (worker / "tracked.txt").write_text("worker\n", encoding="utf-8")
        commit(worker, "worker overlap")
        (self.repo / "tracked.txt").write_text("main\n", encoding="utf-8")
        commit(self.repo, "main overlap")
        with self.assertRaisesRegex(WorkspaceError, "same-file"):
            integrate(self.repo, str(result["branch"]))


if __name__ == "__main__":
    unittest.main()


class PruneTests(AgentWorktreeTests):
    """回收已经并入 master 的隔离工作树。

    `create` 一直有人用，回收却从来没有入口——2026-08-29 清到 3 个，两天后长回 74 个、
    占 868 MB。一次性清理解决不了这个问题，所以把回收做成命令，并在这里锁住它的边界。
    """

    def _integrated(self, name: str) -> Path:
        result = create(self.repo, "Codex", name, self.root / "worktrees")
        worker = Path(result["path"])
        (worker / "worker.txt").write_text(name + " done\n", encoding="utf-8")
        commit(worker, f"{name} change")
        integrate(self.repo, str(result["branch"]))
        return worker

    def test_reporting_does_not_remove_anything(self):
        """默认只报告。回收不可逆，不该是运行一下就顺手做了的事。"""
        worker = self._integrated("reportable")
        report = prune(self.repo)
        self.assertIn(str(worker), report["reclaimed"])
        self.assertFalse(report["applied"])
        self.assertTrue(worker.is_dir(), "没给 --apply 就不该动手")

    def test_apply_reclaims_the_worktree_and_its_branch(self):
        worker = self._integrated("reclaimable")
        branch = _git(self.repo, "branch", "--list", "agent/codex/reclaimable").stdout
        self.assertIn("reclaimable", branch)
        prune(self.repo, apply=True)
        self.assertFalse(worker.exists(), "工作树应当被回收")
        self.assertNotIn("reclaimable",
                         _git(self.repo, "branch", "--list", "agent/codex/reclaimable").stdout,
                         "已并入的分支也应一并删掉")

    def test_a_dirty_worktree_is_refused_even_when_its_branch_is_merged(self):
        """分支已合入不等于工作区里没东西。

        实测就有这样的工作树：分支早已并入 master，里面却躺着一份成形的未提交改动
        （按钮等待态改用 aria-busy，还配了对应的测试）。所以脏的一律拒收并单独列出，
        交给人看，不给 --force 这个口子。
        """
        worker = self._integrated("has-wip")
        (worker / "worker.txt").write_text("未提交的后续改动\n", encoding="utf-8")
        report = prune(self.repo, apply=True)
        self.assertTrue(worker.is_dir(), "脏工作树不能被回收")
        self.assertEqual([row["path"] for row in report["dirty"]], [str(worker)])
        self.assertEqual(report["reclaimed"], [])

    def test_an_unmerged_branch_is_kept_with_a_reason(self):
        result = create(self.repo, "Codex", "still-open", self.root / "worktrees")
        worker = Path(result["path"])
        (worker / "worker.txt").write_text("still open wip\n", encoding="utf-8")
        commit(worker, "still open")
        report = prune(self.repo, apply=True)
        self.assertTrue(worker.is_dir())
        self.assertEqual([row["branch"] for row in report["kept"]], ["agent/codex/still-open"])

    def test_the_main_worktree_is_never_a_candidate(self):
        self._integrated("bystander")
        report = prune(self.repo)
        listed = report["reclaimed"] + [row["path"] for row in report["dirty"] + report["kept"]]
        self.assertNotIn(str(self.repo), listed, "主检出不能出现在回收清单里")

    def test_a_directory_git_could_not_delete_is_deleted_by_the_script(self):
        """git 摘了注册却删不掉目录时，脚本自己把目录删掉，不留给人。

        2026-09-01 实测：连跑 5 次 prune --apply 才把 5 个工作树摘完，5 条分支一条没删，
        最后是手工 `git branch -d` 收的尾——因为 remove 一失败就抛错中止了整轮。分支的
        那半边当时补上了，目录这半边还写着「待人工清理」，于是残留目录照样留在原地：
        长得和真工作树一样，在里面跑 git 全作用于主检出的 master。
        """
        worker = self._integrated("stuck-handle")
        with mock.patch.object(agent_worktree, "_git",
                               StuckRemoval(agent_worktree._git, {worker: "residue"})):
            report = prune(self.repo, apply=True)
        self.assertTrue(report["ok"], "一个目录删不掉不该把整轮判成失败")
        self.assertFalse(worker.exists(), "git 删不掉的空目录由脚本删掉")
        self.assertEqual(report["residue"], [], "删掉了就不是残留")
        self.assertEqual(report["reclaimed"], [str(worker)])
        self.assertNotIn("stuck-handle",
                         _git(self.repo, "branch", "--list", "agent/codex/stuck-handle").stdout,
                         "注册已经摘掉了，分支就该跟着删")

    def test_a_directory_nobody_can_delete_is_reported_with_the_reason(self):
        """脚本也删不掉才算残留：报出原因交给人，分支照删。"""
        worker = self._integrated("locked-handle")
        with mock.patch.object(agent_worktree, "_git",
                               StuckRemoval(agent_worktree._git, {worker: "residue"})), \
                mock.patch.object(agent_worktree, "_delete_tree",
                                  return_value="PermissionError: 目录被别的进程占着"):
            report = prune(self.repo, apply=True)
        self.assertTrue(worker.is_dir(), "删不掉就还在原地")
        self.assertEqual([row["path"] for row in report["residue"]], [str(worker)])
        self.assertIn("目录被别的进程占着", report["residue"][0]["why"])
        self.assertEqual(report["reclaimed"], [])
        self.assertNotIn("locked-handle",
                         _git(self.repo, "branch", "--list", "agent/codex/locked-handle").stdout)

    def test_one_stuck_worktree_does_not_block_the_others(self):
        """回收失败只波及它自己，剩下的工作树照常处理，不用人反复重跑。"""
        stuck = self._integrated("stuck-first")
        other = self._integrated("second-in-line")
        with mock.patch.object(agent_worktree, "_git",
                               StuckRemoval(agent_worktree._git, {stuck: "stuck"})):
            report = prune(self.repo, apply=True)
        self.assertEqual(report["reclaimed"], [str(other)])
        self.assertFalse(other.exists())
        self.assertNotIn("second-in-line",
                         _git(self.repo, "branch", "--list", "agent/codex/second-in-line").stdout)
        self.assertEqual([row["branch"] for row in report["failed"]], ["agent/codex/stuck-first"])
        self.assertTrue(stuck.is_dir())
        self.assertIn("stuck-first",
                      _git(self.repo, "branch", "--list", "agent/codex/stuck-first").stdout,
                      "注册还在就是没回收成，分支不能删")


class BuiltinLeftoverTests(AgentWorktreeTests):
    """清掉 `.claude/worktrees/` 里已经不登记的残留目录。

    Claude Code 内置的工作树机制建在主检出里，分支集成后目录不会自己收。它不在
    `git worktree list` 里，所以按登记项遍历的那轮回收永远碰不到它；人却会走进去当
    工作树用，而在里面跑 git 全部作用于主检出的 master。
    """

    def leftover(self, name: str) -> Path:
        path = self.repo / ".claude" / "worktrees" / name
        path.mkdir(parents=True)
        return path

    def test_an_unregistered_empty_leftover_is_swept(self):
        empty = self.leftover("distracted-lamarr")
        report = prune(self.repo, apply=True)
        self.assertEqual(report["swept"], [str(empty)])
        self.assertFalse(empty.exists())

    def test_reporting_lists_the_leftover_without_deleting_it(self):
        empty = self.leftover("reportable-leftover")
        report = prune(self.repo)
        self.assertEqual(report["swept"], [str(empty)])
        self.assertTrue(empty.is_dir(), "没给 --apply 就不该动手")

    def test_a_leftover_that_still_holds_files_is_left_alone(self):
        """空目录才扫。里面还有文件就可能是别人正开着的检出或没提交的东西。"""
        used = self.leftover("sweet-newton")
        (used / "worker.txt").write_text("别人正在用\n", encoding="utf-8")
        report = prune(self.repo, apply=True)
        self.assertEqual(report["swept"], [])
        self.assertTrue(used.is_dir())
        self.assertEqual([row["path"] for row in report["kept"]], [str(used)])

    def test_a_registered_worktree_under_that_directory_is_not_swept(self):
        """登记着的工作树归上面那轮按分支状态处理，扫残留这步不许碰。"""
        result = create(self.repo, "Claude", "in-place",
                        self.repo / ".claude" / "worktrees")
        worker = Path(result["path"])
        (worker / "worker.txt").write_text("还在做\n", encoding="utf-8")
        commit(worker, "in place wip")
        report = prune(self.repo, apply=True)
        self.assertEqual(report["swept"], [])
        self.assertTrue(worker.is_dir())
        self.assertEqual([row["branch"] for row in report["kept"]], ["agent/claude/in-place"])


class VersionBumpTests(AgentWorktreeTests):
    """集成时本地版本号跟着走一格。

    这台机器既是开发机又是生产机：提交先落本地再推 GitHub，本地永远领先，所以版本号
    必须在集成时就动。手工改那一行的结果是它长期停在同一个值上，托盘、发布 tag 与
    GitHub Release 全都指着一个说明不了任何事的数字。
    """

    def worker_touching(self, name: str, path: str, text: str = "改了\n", *,
                        subject: str | None = None) -> str:
        result = create(self.repo, "Claude", name, self.root / "worktrees")
        worker = Path(result["path"])
        target = worker / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        _git(worker, "add", path)
        _git(worker, "commit", "-m", subject or f"fix: {name}")
        return str(result["branch"])

    def test_the_bump_part_follows_commit_types_and_new_migrations(self):
        """feat 与破坏性标记推 minor，新迁移文件推 minor，其余都是 patch；major 不自动判。"""
        self.assertEqual(bump_part_for(["fix: 抽屉重画只写滚动层"], []), "patch")
        self.assertEqual(bump_part_for(["docs: 记录运行状态", "chore(release): 版本 0.7.27"], []), "patch")
        self.assertEqual(bump_part_for(["refactor(follow): 来源登记表变成唯一真相"], []), "patch")
        self.assertEqual(bump_part_for(["feat: 配置页并入主站管理菜单"], []), "minor")
        self.assertEqual(bump_part_for(["feat(web): 滚动条改成自绘覆盖式"], []), "minor")
        self.assertEqual(bump_part_for(["fix!: 账本路径改成 location 键"], []), "minor")
        self.assertEqual(bump_part_for(["refactor(config)!: 删掉盘符键"], []), "minor")
        self.assertEqual(bump_part_for(["fix: 补迁移"], ["migrations/0027_thing.sql"]), "minor")
        self.assertEqual(bump_part_for(["fix: 补迁移"], [r"migrations\0027_thing.sql"]), "minor")
        self.assertEqual(bump_part_for(["fix: 改了旧迁移的注释"], ["src/peach/tray.py"]), "patch")
        self.assertEqual(bump_part_for(["Merge branch 'master' into agent/claude/x", "feature: 新东西"], []), "minor")
        self.assertEqual(bump_part_for([], []), "patch")

    def test_a_feature_commit_publishes_the_next_minor_version_by_default(self):
        branch = self.worker_touching("feature-work", "src/peach/module.py", subject="feat: 新功能")
        report = integrate(self.repo, branch)
        self.assertEqual((report["bumped"], report["bump"], report["version"]), (True, "minor", "0.8.0"))
        self.assertEqual(read_version(self.repo), "0.8.0")

    def test_a_new_migration_publishes_the_next_minor_version_even_under_a_fix_subject(self):
        branch = self.worker_touching("schema", "migrations/0099_new.sql", subject="fix: 补一列")
        report = integrate(self.repo, branch)
        self.assertEqual((report["bump"], report["version"]), ("minor", "0.8.0"))

    def test_a_feature_that_never_reaches_the_runtime_leaves_the_version_alone(self):
        branch = self.worker_touching("skill-feature", ".claude/skills/x/SKILL.md", subject="feat: 新技能")
        report = integrate(self.repo, branch)
        self.assertEqual((report["bumped"], report["bump"], report["version"]), (False, "none", "0.7.14"))

    def test_runtime_inputs_are_told_apart_from_development_only_paths(self):
        self.assertTrue(runtime_inputs_changed(["src/peach/tray.py"]))
        self.assertTrue(runtime_inputs_changed(["web/app.js"]))
        self.assertTrue(runtime_inputs_changed(["frontend/src/main.ts"]))
        self.assertTrue(runtime_inputs_changed(["migrations/0042_thing.sql"]))
        self.assertTrue(runtime_inputs_changed(["resources/peach.ico"]))
        self.assertTrue(runtime_inputs_changed(["scripts/build_windows.ps1"]))
        self.assertTrue(runtime_inputs_changed(["scripts/build_app_entry.py"]))
        self.assertTrue(runtime_inputs_changed(["pyproject.toml"]))
        self.assertTrue(runtime_inputs_changed([r"src\peach\tray.py"]))

        self.assertFalse(runtime_inputs_changed([]))
        self.assertFalse(runtime_inputs_changed(["docs/STATUS.md", "AGENTS.md"]))
        self.assertFalse(runtime_inputs_changed(["tests/test_tray.py"]))
        self.assertFalse(runtime_inputs_changed([".claude/skills/peach-worktree/SKILL.md"]))
        self.assertFalse(runtime_inputs_changed(["scripts/agent_worktree.py"]))

    def test_only_the_version_line_moves(self):
        updated, version = bump_version(VERSION_SEED.decode("utf-8"), "patch")
        self.assertEqual(version, "0.7.15")
        self.assertEqual(updated,
                         '"""Peach application package."""\n\n__version__ = "0.7.15"\n')

        self.assertEqual(bump_version('__version__ = "0.7.14"', "minor")[1], "0.8.0")
        self.assertEqual(bump_version('__version__ = "0.7.14"', "major")[1], "1.0.0")
        with self.assertRaisesRegex(WorkspaceError, "unknown bump part"):
            bump_version('__version__ = "0.7.14"', "epoch")
        with self.assertRaisesRegex(WorkspaceError, "__version__"):
            bump_version("nothing here\n", "patch")

    def test_integrating_a_runtime_fix_publishes_the_next_patch_version(self):
        branch = self.worker_touching("runtime-change", "src/peach/module.py")
        report = integrate(self.repo, branch)
        self.assertTrue(report["bumped"])
        self.assertEqual(report["bump"], "patch")
        self.assertEqual(report["version"], "0.7.15")
        self.assertEqual(read_version(self.repo), "0.7.15")
        subject = _git(self.repo, "log", "-1", "--format=%s").stdout.strip()
        self.assertEqual(subject, "chore(release): 版本 0.7.15")
        touched = _lines(_git(self.repo, "show", "--name-only", "--format=", "HEAD"))
        self.assertEqual(touched, ["src/peach/__init__.py"])

    def test_documentation_only_work_leaves_the_version_alone(self):
        branch = self.worker_touching("docs-change", "docs/STATUS.md")
        report = integrate(self.repo, branch)
        self.assertFalse(report["bumped"])
        self.assertEqual(report["version"], "0.7.14")
        self.assertEqual(read_version(self.repo), "0.7.14")
        self.assertEqual(_git(self.repo, "log", "-1", "--format=%s").stdout.strip(),
                         f"Merge branch '{branch}'")

    def test_an_explicit_none_keeps_the_version_even_for_runtime_changes(self):
        branch = self.worker_touching("held-back", "src/peach/module.py")
        report = integrate(self.repo, branch, bump="none")
        self.assertFalse(report["bumped"])
        self.assertEqual(read_version(self.repo), "0.7.14")

    def test_an_explicit_part_overrides_the_commit_type(self):
        branch = self.worker_touching("feature-set", "src/peach/module.py", subject="feat: 大功能")
        report = integrate(self.repo, branch, bump="patch")
        self.assertEqual((report["bump"], report["version"]), ("patch", "0.7.15"))
        self.assertEqual(read_version(self.repo), "0.7.15")

    def test_integration_never_creates_a_version_tag_itself(self):
        """打标签只有 `scripts/release_tag.py` 一个入口，它遇到同名本地标签就拒绝。

        集成这一步再造一个本地标签，等于把唯一的发布入口挡在门外；这里只把
        `__version__` 推到位，那正是它读的东西。
        """
        branch = self.worker_touching("taggable", "src/peach/module.py")
        report = integrate(self.repo, branch)
        self.assertEqual(report["version"], "0.7.15")
        self.assertEqual(report["release_tag_entry"], "scripts/release_tag.py")
        self.assertEqual(_lines(_git(self.repo, "tag", "--list")), [])
