from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from scripts import agent_worktree as coordinator
from scripts import test_evidence as evidence
from scripts import test_runner as runner


class VerificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "master")
        self.git("config", "user.name", "Peach Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / ".gitignore").write_text("build/\n", encoding="utf-8")
        (self.repo / "README.md").write_text("内容\n", encoding="utf-8")
        (self.repo / "src/peach").mkdir(parents=True)
        (self.repo / "src/peach/__init__.py").write_text('__version__ = "0.7.30"\n')
        self.git("add", ".gitignore", "README.md", "src/peach/__init__.py")
        self.git("commit", "-m", "seed")

    def git(self, *args):
        return evidence.git(self.repo, *args)

    def worker(self):
        item = coordinator.create(self.repo, "codex", "verification", self.root / "worktrees")
        worker = Path(item["path"])
        (worker / "README.md").write_text("测试内容\n", encoding="utf-8")
        evidence.git(worker, "add", "README.md")
        evidence.git(worker, "commit", "-m", "docs: test")
        return worker, item["branch"]

    def certify(self, worker, scopes=("checks",), success=True):
        state = evidence.key(worker)
        evidence.write(worker, state, scopes, success=success, elapsed=1, slowest=[], count=1)
        return state

    def test_gate_requires_matching_successful_coverage(self):
        worker, branch = self.worker()
        before = self.git("rev-parse", "HEAD")
        with self.assertRaisesRegex(coordinator.WorkspaceError, "有效测试记录"):
            coordinator.integrate(self.repo, branch)
        self.certify(worker, ("web",))
        with self.assertRaisesRegex(coordinator.WorkspaceError, "有效测试记录"):
            coordinator.ready(worker)
        self.certify(worker, success=False)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.certify(worker)
        coordinator.ready(worker)
        result = coordinator.integrate(self.repo, branch)
        self.assertFalse(result["bumped"])
        entries = coordinator._worktree_entries(self.repo)
        self.assertFalse(next(e for e in entries if e.get("branch") == branch).get("locked"))

    def test_target_advance_requires_combined_tree_verification(self):
        worker, branch = self.worker()
        self.certify(worker)
        (self.repo / "another.md").write_text("并行任务\n", encoding="utf-8")
        self.git("add", "another.md")
        self.git("commit", "-m", "docs: parallel")
        with self.assertRaisesRegex(coordinator.WorkspaceError, "已前进"):
            coordinator.integrate(self.repo, branch)

    def test_target_change_during_verification_prevents_merge(self):
        worker, branch = self.worker()
        self.certify(worker)
        verify = coordinator.require_verified
        def advance(*args):
            verify(*args)
            (self.repo / "parallel.md").write_text("并发改动\n", encoding="utf-8")
            self.git("add", "parallel.md")
            self.git("commit", "-m", "docs: concurrent")
        with mock.patch.object(coordinator, "require_verified", side_effect=advance):
            with self.assertRaisesRegex(coordinator.WorkspaceError, "集成工作树改变"):
                coordinator.integrate(self.repo, branch)
        self.assertEqual((self.repo / "README.md").read_text(encoding="utf-8"), "内容\n")

    def test_scope_refresh_preserves_expiry_of_other_scopes(self):
        state = evidence.key(self.repo)
        with mock.patch.object(evidence.time, "time", return_value=100):
            self.certify(self.repo, ("full",))
        with mock.patch.object(evidence.time, "time", return_value=86450):
            self.certify(self.repo, ("checks",))
        with mock.patch.object(evidence.time, "time", return_value=86550):
            record = evidence.read(self.repo, state)
            self.assertTrue(evidence.covers(record, ("checks",)))
            self.assertFalse(evidence.covers(record, ("web",)))

    def test_snapshot_tracks_untracked_deleted_and_modified_content(self):
        baseline = evidence.snapshot(self.repo)
        path = self.repo / "extra.md"
        path.write_text("未跟踪\n", encoding="utf-8")
        self.assertNotEqual(baseline, evidence.snapshot(self.repo))
        path.unlink()
        self.assertEqual(baseline, evidence.snapshot(self.repo))
        (self.repo / "README.md").unlink()
        self.assertNotEqual(baseline, evidence.snapshot(self.repo))

    def test_commit_metadata_preserves_content_record(self):
        worker, _ = self.worker()
        state = self.certify(worker)
        evidence.git(worker, "commit", "--amend", "-m", "docs: wording")
        self.assertEqual(evidence.key(worker), state)
        self.assertTrue(evidence.covers(evidence.read(worker, state), ("checks",)))
        (worker / "README.md").write_text("不同内容\n", encoding="utf-8")
        self.assertNotEqual(evidence.key(worker), state)

    def test_environment_change_expiry_and_failure_invalidate_records(self):
        state = self.certify(self.repo, ("full",))
        with mock.patch.object(evidence, "environment", return_value="different"):
            self.assertNotEqual(evidence.key(self.repo), state)
        with mock.patch.object(evidence.time, "time", return_value=10**12):
            self.assertFalse(evidence.covers(evidence.read(self.repo, state), ("web",)))
        self.certify(self.repo, ("web",), success=False)
        self.assertFalse(evidence.covers(evidence.read(self.repo, state), ("web",)))

    def test_cross_process_integration_lock_refuses_mutation(self):
        _, branch = self.worker()
        folder = evidence.evidence_dir(self.repo)
        folder.mkdir(parents=True)
        before = self.git("rev-parse", "HEAD")
        command = [sys.executable, str(Path(coordinator.__file__)), "--repo", str(self.repo),
                   "integrate", "--branch", branch]
        with evidence.FileLock(folder / "integration.lock"):
            result = subprocess.run(command, capture_output=True, text=True,
                                    encoding="utf-8", timeout=15,
                                    env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("另一任务正在集成", json.loads(result.stdout)["error"])
        self.assertEqual(self.git("rev-parse", "HEAD"), before)

    def test_empty_active_worktree_survives_prune(self):
        item = coordinator.create(self.repo, "codex", "active", self.root / "worktrees")
        report = coordinator.prune(self.repo, apply=True)
        self.assertTrue(Path(item["path"]).is_dir())
        self.assertTrue(any(row["path"] == item["path"] for row in report["kept"]))

    def test_auto_uses_scope_union_and_full_for_shared_inputs(self):
        self.assertEqual(runner.scopes_for_changes([])[0], ("checks",))
        self.assertEqual(runner.scopes_for_changes(["docs/HANDOFF.md"])[0], ("checks",))
        self.assertEqual(runner.scopes_for_changes(["web/app.js", "src/peach/follow.py"])[0],
                         ("follow", "web"))
        for path in ("pyproject.toml", "scripts/test_runner.py", "scripts/test_evidence.py",
                     "scripts/build_windows.ps1", "src/peach/unknown.py"):
            self.assertEqual(runner.scopes_for_changes([path])[0], ("full",))

    def test_runner_reuses_success_and_fresh_failure_invalidates_it(self):
        def suite(*_):
            return unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()), \
                mock.patch.object(runner, "ROOT", self.repo), \
                mock.patch.object(runner, "build_suite", side_effect=suite) as build:
            self.assertEqual(runner.main(["--scope", "checks"]), 0)
            self.assertEqual(runner.main(["--scope", "checks"]), 0)
            self.assertEqual(build.call_count, 1)
            def failing(*_):
                return unittest.TestSuite([unittest.FunctionTestCase(lambda: self.fail("fixture"))])
            build.side_effect = failing
            self.assertEqual(runner.main(["--scope", "checks", "--fresh"]), 1)
            self.assertFalse(evidence.covers(evidence.read(self.repo, evidence.key(self.repo)), ("checks",)))

    def test_runner_rejects_changes_during_verification(self):
        def mutate():
            (self.repo / "README.md").write_text("测试期间改动\n", encoding="utf-8")
        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()), \
                mock.patch.object(runner, "ROOT", self.repo), \
                mock.patch.object(runner, "build_suite", return_value=unittest.TestSuite([
                    unittest.FunctionTestCase(mutate)])):
            self.assertEqual(runner.main(["--scope", "checks"]), 1)
        self.assertFalse(evidence.covers(evidence.read(self.repo, evidence.key(self.repo)), ("checks",)))


if __name__ == "__main__":
    unittest.main()
