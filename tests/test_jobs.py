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
        """Windows 对已消失的 PID 抛 WinError 87，不是 ProcessLookupError。

        漏掉它会让每个被强杀留下的锁把后续所有运行直接崩掉；2026-08-15 实际发生过。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.lock"
            path.write_text("39316", encoding="ascii")
            error = OSError("参数错误")
            error.winerror = 87
            with patch("peach.jobs.os.kill", side_effect=error):
                with PidFileLock(path):
                    self.assertEqual(path.read_text(encoding="ascii").strip(), str(__import__("os").getpid()))
            self.assertFalse(path.exists())

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
