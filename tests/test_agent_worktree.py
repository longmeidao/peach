import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.agent_worktree import WorkspaceError, _git, create, integrate, ready


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
