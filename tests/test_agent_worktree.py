import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import agent_worktree
from scripts.agent_worktree import WorkspaceError, _git, create, integrate, prune, ready


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
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-b", "master", str(self.repo)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _git(self.repo, "config", "user.email", "test@example.invalid")
        _git(self.repo, "config", "user.name", "Peach Test")
        (self.repo / "tracked.txt").write_text("base\n", encoding="utf-8")
        (self.repo / "worker.txt").write_text("base\n", encoding="utf-8")
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

    def test_a_directory_that_will_not_delete_still_loses_its_branch(self):
        """注册已经摘掉、只剩目录删不掉时，分支照删，目录列进 residue 交给人清。

        2026-09-01 实测：连跑 5 次 prune --apply 才把 5 个工作树摘完，5 条分支一条没删，
        最后是手工 `git branch -d` 收的尾——因为 remove 一失败就抛错中止了整轮。
        """
        worker = self._integrated("stuck-handle")
        with mock.patch.object(agent_worktree, "_git",
                               StuckRemoval(agent_worktree._git, {worker: "residue"})):
            report = prune(self.repo, apply=True)
        self.assertTrue(report["ok"], "一个目录删不掉不该把整轮判成失败")
        self.assertTrue(worker.is_dir(), "空目录还在原地")
        self.assertEqual([row["path"] for row in report["residue"]], [str(worker)])
        self.assertEqual(report["reclaimed"], [])
        self.assertNotIn("stuck-handle",
                         _git(self.repo, "branch", "--list", "agent/codex/stuck-handle").stdout,
                         "注册已经摘掉了，分支就该跟着删")

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
