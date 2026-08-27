import contextlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach.versioning import VersionManager, discover_repository_root


def git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={path.as_posix()}", "-C", str(path), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )


def initialize_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "master", str(path)], capture_output=True, check=True)
    git(path, "config", "user.name", "Peach Tests")
    git(path, "config", "user.email", "tests@peach.local")
    (path / "version.txt").write_text("one\n", encoding="utf-8")
    git(path, "add", "version.txt")
    git(path, "commit", "-m", "initial")


class VersionManagerTests(unittest.TestCase):
    @contextlib.contextmanager
    def tracking_clone(self):
        """一个跟踪 origin/master 的检出，外加一份用来代表「另一台机器」的克隆。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, repo, other = root / "remote.git", root / "repo", root / "other"
            config = root / "gitconfig"
            config.write_text(
                "[safe]\n"
                + "".join(f"\tdirectory = {path.as_posix()}\n"
                          for path in (repo, remote, other)),
                encoding="utf-8",
            )
            git_env = {"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1"}
            with mock.patch.dict(os.environ, git_env):
                subprocess.run(["git", "init", "--bare", str(remote)],
                               capture_output=True, check=True)
                initialize_repo(repo)
                git(repo, "remote", "add", "origin", str(remote))
                git(repo, "push", "-u", "origin", "master")
                subprocess.run(["git", "clone", str(remote), str(other)],
                               capture_output=True, check=True)
                git(other, "config", "user.name", "Peach Tests")
                git(other, "config", "user.email", "tests@peach.local")
            yield repo, other, git_env

    def test_repository_discovery_prefers_source_resource_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            initialize_repo(repo)
            executable = root / "elsewhere" / "Peach.exe"

            self.assertEqual(
                discover_repository_root(repo, executable=executable),
                repo.resolve(),
            )

    def test_repository_discovery_finds_repo_above_packaged_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            initialize_repo(repo)
            bundle_root = root / "pyinstaller" / "_MEI12345"
            executable = repo / "dist" / "Peach" / "Peach.exe"

            self.assertEqual(
                discover_repository_root(bundle_root, executable=executable),
                repo.resolve(),
            )

    def test_repository_discovery_does_not_invent_remote_for_portable_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle_root = root / "pyinstaller" / "_MEI12345"
            executable = root / "portable" / "Peach.exe"

            self.assertEqual(
                discover_repository_root(bundle_root, executable=executable),
                bundle_root.resolve(),
            )

    def test_local_development_version_is_readable_without_remote(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            initialize_repo(repo)
            manager = VersionManager(repo)
            snapshot = manager.inspect()
            self.assertEqual(snapshot.branch, "master")
            self.assertNotEqual(snapshot.commit, "unknown")
            self.assertFalse(snapshot.remote_configured)
            result = manager.check()
            self.assertEqual(result.state, "unconfigured")
            self.assertIn("本地开发版", result.message)

    def test_check_fetches_and_reports_remote_commits_without_applying(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            repo = root / "repo"
            other = root / "other"
            test_config = root / "gitconfig"
            test_config.write_text(
                "[safe]\n"
                f"\tdirectory = {repo.as_posix()}\n"
                f"\tdirectory = {remote.as_posix()}\n"
                f"\tdirectory = {other.as_posix()}\n",
                encoding="utf-8",
            )
            safe_directories = {
                "GIT_CONFIG_GLOBAL": str(test_config),
                "GIT_CONFIG_NOSYSTEM": "1",
            }
            with mock.patch.dict(os.environ, safe_directories):
                subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, check=True)
                initialize_repo(repo)
                git(repo, "remote", "add", "origin", str(remote))
                git(repo, "push", "-u", "origin", "master")
                subprocess.run(["git", "clone", str(remote), str(other)], capture_output=True, check=True)
                git(other, "config", "user.name", "Peach Tests")
                git(other, "config", "user.email", "tests@peach.local")
                (other / "version.txt").write_text("two\n", encoding="utf-8")
                git(other, "add", "version.txt")
                git(other, "commit", "-m", "remote update")
                git(other, "push", "origin", "master")

                before = git(repo, "rev-parse", "HEAD").stdout.strip()
                result = VersionManager(repo).check()
                after = git(repo, "rev-parse", "HEAD").stdout.strip()
                self.assertEqual(result.state, "available")
                self.assertEqual(result.behind, 1)
                self.assertEqual(before, after)

    def test_update_fast_forwards_and_reports_what_changed(self):
        with self.tracking_clone() as (repo, other, git_env):
            with mock.patch.dict(os.environ, git_env):
                (other / "feature.txt").write_text("new\n", encoding="utf-8")
                git(other, "add", "feature.txt")
                git(other, "commit", "-m", "remote feature")
                git(other, "push", "origin", "master")

                result = VersionManager(repo).update()

                self.assertEqual(result.state, "updated")
                self.assertEqual(result.behind, 1)
                self.assertEqual(result.changed_paths, ("feature.txt",))
                self.assertTrue((repo / "feature.txt").is_file())

    def test_update_is_a_no_op_when_already_current(self):
        with self.tracking_clone() as (repo, _other, git_env):
            with mock.patch.dict(os.environ, git_env):
                before = git(repo, "rev-parse", "HEAD").stdout.strip()
                result = VersionManager(repo).update()
                self.assertEqual(result.state, "current")
                self.assertEqual(result.changed_paths, ())
                self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), before)

    def test_update_refuses_to_touch_a_dirty_checkout(self):
        """有未提交修改就停手。stash 会把别人正在改的东西卷进来，而托盘没人看着。"""
        with self.tracking_clone() as (repo, other, git_env):
            with mock.patch.dict(os.environ, git_env):
                (other / "feature.txt").write_text("new\n", encoding="utf-8")
                git(other, "add", "feature.txt")
                git(other, "commit", "-m", "remote feature")
                git(other, "push", "origin", "master")
                (repo / "version.txt").write_text("dirty\n", encoding="utf-8")

                before = git(repo, "rev-parse", "HEAD").stdout.strip()
                result = VersionManager(repo).update()

                self.assertEqual(result.state, "blocked")
                self.assertIn("未提交修改", result.message)
                self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), before)
                self.assertEqual((repo / "version.txt").read_text(encoding="utf-8"), "dirty\n")

    def test_update_never_rewrites_history_when_the_branches_diverged(self):
        """两边分叉时只报，不 rebase 也不 reset：并行工作树共用同一个对象库。"""
        with self.tracking_clone() as (repo, other, git_env):
            with mock.patch.dict(os.environ, git_env):
                (other / "feature.txt").write_text("new\n", encoding="utf-8")
                git(other, "add", "feature.txt")
                git(other, "commit", "-m", "remote feature")
                git(other, "push", "origin", "master")
                (repo / "local.txt").write_text("mine\n", encoding="utf-8")
                git(repo, "add", "local.txt")
                git(repo, "commit", "-m", "local work")

                before = git(repo, "rev-parse", "HEAD").stdout.strip()
                result = VersionManager(repo).update()

                self.assertEqual(result.state, "diverged")
                self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), before)
                self.assertFalse((repo / "feature.txt").exists())


if __name__ == "__main__":
    unittest.main()
