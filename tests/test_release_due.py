"""收尾时那句「该发版了」：什么时候该出声，什么时候一个字都不能说。

提醒最容易坏在「说得太多」上：每轮回话都触发一次的钩子，只要有一次判错就变成每分钟
一条的噪音，人会连同真正该看的那一条一起划过去。所以这里的断言大半是在证明它闭嘴。
"""
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import release_due

#: 版本号的唯一来源在测试仓库里的最小复刻。
VERSION_SEED = '"""Peach application package."""\n\n__version__ = "0.7.14"\n'


def git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", check=True)
    return done.stdout.strip()


def commit(root: Path, subject: str) -> None:
    note = root / "note.txt"
    note.write_text(subject, encoding="utf-8")
    git(root, "add", "note.txt")
    git(root, "commit", "-m", subject)


class ReleaseDueCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # 先 resolve：CI runner 的临时目录都是别名，git 报回来的是真实路径，拿未
        # resolve 的路径去比对会本机全绿、CI 全红。
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.latch = self.root / "state" / "release-due.json"
        subprocess.run(["git", "init", "-b", "master", str(self.repo)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Peach Test")
        package = self.repo / "src" / "peach"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(VERSION_SEED, encoding="utf-8")
        git(self.repo, "add", "src/peach/__init__.py")
        git(self.repo, "commit", "-m", "chore: 起底")

    def pile_up_user_facing_work(self, count: int = 10) -> None:
        """攒够「不必等满周期」那道判据要的条目数。"""
        for index in range(count):
            commit(self.repo, f"feat(review): 复核加第 {index} 项")

    def say(self) -> str:
        return release_due.verdict(self.repo, self.latch)["say"]


class SpeakingTests(ReleaseDueCase):
    def test_a_release_worth_of_user_facing_changes_gets_said(self):
        self.pile_up_user_facing_work()
        said = self.say()
        self.assertIn("该发下一版了", said)
        self.assertIn("release_tag.py", said)

    def test_the_same_master_is_only_asked_about_once(self):
        """闩住 sha，不是闩住会话。

        每轮回话结束都会触发一次，按会话闩的话，同一个 master 在下一个会话里又会被
        问一遍；按 sha 闩，master 前进了才再问，那时确实是又攒了新东西。
        """
        self.pile_up_user_facing_work()
        first = release_due.verdict(self.repo, self.latch)
        release_due.remember(self.latch, first["sha"])
        self.assertEqual(self.say(), "")
        commit(self.repo, "feat(follow): 关注页加筛选")
        self.assertIn("该发下一版了", self.say())

    def test_a_latch_that_cannot_be_read_counts_as_never_asked(self):
        """闩坏了要退回「再问一次」，不能退回「永远闭嘴」。

        反过来的话，一次写坏的文件会让这条提醒从此消失，而且没有任何迹象。
        """
        self.pile_up_user_facing_work()
        self.latch.parent.mkdir(parents=True, exist_ok=True)
        self.latch.write_text("{ 半个 json", encoding="utf-8")
        self.assertIn("该发下一版了", self.say())


class SilenceTests(ReleaseDueCase):
    def test_work_no_user_can_see_says_nothing(self):
        for subject in ("chore: 收拾脚本", "test: 补断言", "refactor(web): 收口",
                        "docs: 记一笔"):
            commit(self.repo, subject)
        self.assertEqual(self.say(), "")

    def test_a_worker_worktree_is_never_asked_to_release(self):
        """工作树里的工作者不发版，提醒他等于提醒错人。"""
        self.pile_up_user_facing_work()
        worker = self.root / "worker"
        git(self.repo, "worktree", "add", "-b", "agent/test/x", str(worker))
        self.assertEqual(release_due.verdict(worker.resolve(), self.latch)["say"], "")
        self.assertFalse(release_due.is_main_checkout(worker.resolve()))
        self.assertTrue(release_due.is_main_checkout(self.repo))

    def test_standing_on_another_branch_says_nothing(self):
        self.pile_up_user_facing_work()
        git(self.repo, "checkout", "-q", "-b", "agent/test/y")
        self.assertEqual(self.say(), "")

    def test_a_dirty_checkout_says_nothing(self):
        """此刻发不了版，问了也动不了手；等这轮落地，下一次收尾时再问。"""
        self.pile_up_user_facing_work()
        (self.repo / "note.txt").write_text("还没提交", encoding="utf-8")
        self.assertEqual(self.say(), "")

    def test_somewhere_that_is_not_a_repository_says_nothing(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.assertEqual(release_due.verdict(outside, self.latch)["say"], "")


class HookTests(ReleaseDueCase):
    def run_hook(self, cwd: Path) -> tuple[int, str]:
        received = json.dumps({"hook_event_name": "Stop", "cwd": str(cwd)})
        with mock.patch("sys.stdin", io.StringIO(received)), \
                mock.patch("sys.stdout", io.StringIO()) as out:
            code = release_due.main(["--hook-event", "--latch", str(self.latch)])
        return code, out.getvalue()

    def test_the_answer_is_the_shape_both_agents_read(self):
        """Claude 与 Codex 的 Stop 钩子读的是同一个字段，所以一个脚本供两边。"""
        self.pile_up_user_facing_work()
        code, out = self.run_hook(self.repo)
        self.assertEqual(code, 0)
        self.assertIn("该发下一版了", json.loads(out)["systemMessage"])

    def test_nothing_to_say_prints_nothing_at_all(self):
        """不该发时连「不用发」也不说：钩子每轮都跑，多一个字就是每轮多一行。"""
        commit(self.repo, "chore: 收拾脚本")
        code, out = self.run_hook(self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_the_hook_reads_the_session_directory_from_the_event(self):
        """钩子里的仓库位置只能听事件的 `cwd`。

        Claude 的 `${CLAUDE_PROJECT_DIR}` 在进入工作树后仍指着会话启动时的那个项目
        根，照它判的话，工作树里的工作者会话会被当成主检出，收到一条他动不了手的提醒。
        """
        self.pile_up_user_facing_work()
        worker = self.root / "worker"
        git(self.repo, "worktree", "add", "-b", "agent/test/z", str(worker))
        self.assertEqual(self.run_hook(worker.resolve()), (0, ""))

    def test_only_the_hook_moves_the_latch(self):
        """人手查是只读的，不该顺手把钩子的嘴堵上。"""
        self.pile_up_user_facing_work()
        with mock.patch("sys.stdout", io.StringIO()):
            release_due.main(["--repo", str(self.repo), "--latch", str(self.latch)])
        self.assertFalse(self.latch.exists())
        self.run_hook(self.repo)
        self.assertTrue(self.latch.exists())


class WiringTests(unittest.TestCase):
    """判断写好了却没人调用，等于没写。"""

    ROOT = Path(__file__).resolve().parents[1]

    def test_the_claude_stop_hook_runs_the_check(self):
        settings = json.loads((self.ROOT / ".claude" / "settings.json")
                              .read_text(encoding="utf-8"))
        commands = [" ".join([entry["command"], *entry.get("args", [])])
                    for group in settings["hooks"]["Stop"] for entry in group["hooks"]]
        self.assertTrue(any("scripts/release_due.py" in line and "--hook-event" in line
                            for line in commands), commands)

    def test_the_codex_stop_hook_runs_the_same_check(self):
        hooks = json.loads((self.ROOT / ".codex" / "hooks.json")
                           .read_text(encoding="utf-8"))
        commands = [entry["command"]
                    for group in hooks["hooks"]["Stop"] for entry in group["hooks"]]
        self.assertTrue(any("scripts/release_due.py" in line and "--hook-event" in line
                            for line in commands), commands)


if __name__ == "__main__":
    unittest.main()
