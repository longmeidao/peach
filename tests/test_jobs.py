import os
import signal
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.jobs import (
    DiskGuard,
    DiskSpaceDenied,
    JobAlreadyRunning,
    MeteredSourceDenied,
    PidFileLock,
    SourceAccessPolicy,
    job_main,
    require_free_space,
)


class JobPolicyTests(unittest.TestCase):
    def test_metered_source_requires_explicit_authorization(self):
        policy = SourceAccessPolicy()
        with self.assertRaises(MeteredSourceDenied):
            policy.sql_filter("pikpak", allow_metered=False)

    def test_unmetered_query_uses_parameters_and_excludes_metered_sources(self):
        sql, parameters = SourceAccessPolicy().sql_filter("115", allow_metered=False)
        self.assertEqual(sql, " AND location=? AND location NOT IN (?,?)")
        self.assertEqual(parameters, ("115", "online", "pikpak"))

    def test_authorized_metered_query_is_scoped_to_requested_source(self):
        sql, parameters = SourceAccessPolicy().sql_filter("pikpak", allow_metered=True)
        self.assertEqual(sql, " AND location=?")
        self.assertEqual(parameters, ("pikpak",))

    def test_disk_guard_fails_closed_when_usage_is_unavailable(self):
        with patch("peach.jobs.shutil.disk_usage", side_effect=OSError("offline")):
            with self.assertRaises(DiskSpaceDenied):
                require_free_space(Path("C:/"), 40)

    def test_disk_guard_accepts_real_temporary_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertGreaterEqual(require_free_space(tmp, 0), 0)

    def test_runtime_guard_stops_a_job_that_started_with_room(self):
        """2026-08-15 事故：起跑时 C: 有几百 GB，跑到 0 字节也没人再看一眼。"""
        guard = DiskGuard(Path("C:/"), minimum_gb=40, interval_secs=0)
        free = 500 * 1024**3
        with patch("peach.jobs.shutil.disk_usage", return_value=type("U", (), {"free": free})):
            self.assertAlmostEqual(guard.check(force=True), 500, places=3)
        # 同一次运行中盘被第三方缓存吃光，闸门必须在运行期触发，而不是等下次启动。
        with patch("peach.jobs.shutil.disk_usage", return_value=type("U", (), {"free": 1024**3})):
            with self.assertRaises(DiskSpaceDenied):
                guard.check(force=True)

    def test_runtime_guard_throttles_and_fails_closed(self):
        guard = DiskGuard(Path("C:/"), minimum_gb=40, interval_secs=3600)
        with patch("peach.jobs.shutil.disk_usage", return_value=type("U", (), {"free": 1024**3})):
            with self.assertRaises(DiskSpaceDenied):
                guard.check(force=True)
            # 节流窗口内不重复读盘，返回 None 表示本轮未检查——不能被误当成"通过"。
            self.assertIsNone(guard.check())
        with patch("peach.jobs.shutil.disk_usage", side_effect=OSError("offline")):
            with self.assertRaises(DiskSpaceDenied):
                guard.check(force=True)

    def test_stale_lock_from_a_killed_job_does_not_crash_the_next_run(self):
        """被强杀留下的锁必须被清理后继续，而不是把后续所有运行直接崩掉。

        2026-08-15 实际发生过。取一个几乎不可能存在的 PID 走真实的存活探测。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.lock"
            path.write_text("4294967294", encoding="ascii")
            with PidFileLock(path):
                self.assertEqual(path.read_text(encoding="ascii").strip(), str(os.getpid()))
            self.assertFalse(path.exists())

    @unittest.skipUnless(os.name == "nt", "只在 Windows 上成立")
    def test_liveness_probe_never_signals_its_own_console(self):
        """Windows 上 `signal.CTRL_C_EVENT == 0`。

        于是 Unix 探测存活的经典写法 `os.kill(pid, 0)` 实际会调用
        `GenerateConsoleCtrlEvent(CTRL_C_EVENT, ...)`，把 Ctrl+C 发给整个控制台进程组。
        锁里写的又是自己的 PID，「检查锁是否还活着」就会当场把自己打断——在真实控制台里
        跑批处理或测试时表现为毫无征兆的 KeyboardInterrupt，而重定向/无控制台的环境
        不复现，因为控制台事件无处投递。这条守住「探测存活不得发信号」。
        """
        self.assertEqual(int(signal.CTRL_C_EVENT), 0, "前提：CTRL_C_EVENT 就是 0")
        with patch("peach.jobs.os.kill", side_effect=AssertionError("存活探测不得调用 os.kill")):
            self.assertTrue(PidFileLock._running(os.getpid()))
            self.assertFalse(PidFileLock._running(4294967294))

    def test_pid_lock_rejects_live_owner_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.lock"
            with PidFileLock(path):
                self.assertTrue(path.is_file())
                with self.assertRaises(JobAlreadyRunning):
                    PidFileLock(path).acquire()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()


class JobMainTests(unittest.TestCase):
    """长跑批处理的统一入口收尾。

    这段此前在四个脚本里各写了一份。前三份逐字相同；第四份只把异常变量从 `exc`
    改名成 `error`——一个标识符的差别就能让逐字扫描漏掉它，所以指望「看一眼就发现
    重复」是不成立的。
    """

    def _parser(self, lock: Path):
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--lock", type=Path, default=lock)
        return parser

    def test_returns_the_policy_exit_code_instead_of_raising(self):
        """批处理是无人值守跑的，被读的是退出码，不是栈。"""
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "job.lock"

            def run(_args):
                raise DiskSpaceDenied("盘满了")

            with patch("builtins.print") as printed:
                code = job_main(lambda: self._parser(lock), run, [])
            self.assertEqual(code, DiskSpaceDenied.exit_code)
            self.assertIn("[stop]", " ".join(str(c) for c in printed.call_args_list))

    def test_already_running_is_not_a_failure(self):
        """`JobAlreadyRunning.exit_code` 是 0：另一份还在跑不算这次失败。

        散成四份手抄时，谁把它当异常向上抛或改成非零，都不会有测试拦住。
        """
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "job.lock"
            with PidFileLock(lock):
                with patch("builtins.print"):
                    code = job_main(lambda: self._parser(lock),
                                    lambda _args: self.fail("锁没拿住就不该跑 run"), [])
            self.assertEqual(code, 0)

    def test_the_lock_wraps_the_whole_run(self):
        """pid 锁必须包住整个 run，而不是只包住入口。"""
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "job.lock"
            seen = []

            def run(_args):
                seen.append(lock.exists())
                return 7

            self.assertEqual(job_main(lambda: self._parser(lock), run, []), 7)
            self.assertEqual(seen, [True], "run 执行期间锁文件必须还在")
            self.assertFalse(lock.exists(), "退出后锁要释放")
