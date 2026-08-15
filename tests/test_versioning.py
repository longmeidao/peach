import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach.versioning import VersionManager


def git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={path.as_posix()}", "-C", str(path), *args],
        capture_output=True, text=True, check=True,
    )


def initialize_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "master", str(path)], capture_output=True, check=True)
    git(path, "config", "user.name", "Peach Tests")
    git(path, "config", "user.email", "tests@peach.local")
    (path / "version.txt").write_text("one\n", encoding="utf-8")
    git(path, "add", "version.txt")
    git(path, "commit", "-m", "initial")


class VersionManagerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
