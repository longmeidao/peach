from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "restart_windows_tray.py"
SPEC = importlib.util.spec_from_file_location("restart_windows_tray", SCRIPT)
restart_windows_tray = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = restart_windows_tray
SPEC.loader.exec_module(restart_windows_tray)


class RestartWindowsTrayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        # restart_tray 第一件事就是 target.resolve()，并由它推出 .venv 里的服务入口。
        # CI runner 的临时目录是别名（macOS /var 软链到 /private/var，Windows 的
        # RUNNER~1 短名展开成 runneradmin），不先 resolve 推出来的服务入口就对不上
        # self.service，services() 返回空、循环空转，最后把 find_windows 的假迭代器
        # 耗尽成 StopIteration。
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / "dist" / "Peach" / "Peach.exe"
        self.service = self.root / ".venv" / "Scripts" / "peach.exe"
        self.target.parent.mkdir(parents=True)
        self.service.parent.mkdir(parents=True)
        self.target.write_bytes(b"tray")
        self.service.write_bytes(b"service")

    def tearDown(self):
        self.temp.cleanup()

    def test_refuses_when_the_exact_tray_window_is_not_unique(self):
        start = mock.Mock()
        result = restart_windows_tray.restart_tray(
            self.target, find_windows=lambda _target: (), start=start,
        )
        self.assertFalse(result.ok)
        self.assertIn("唯一", result.message)
        start.assert_not_called()

    def test_timeout_never_force_kills_or_starts_a_second_tray(self):
        start = mock.Mock()
        result = restart_windows_tray.restart_tray(
            self.target, timeout=0.001,
            find_windows=lambda _target: (restart_windows_tray.TrayWindow(10, 20),),
            stop_window=lambda _handle: True, alive=lambda _pid: True,
            start=start, sleep=lambda _seconds: None,
        )
        self.assertFalse(result.ok)
        self.assertIn("未强杀、未另启", result.message)
        start.assert_not_called()

    def test_normal_exit_restarts_and_requires_tray_owned_services(self):
        windows = iter((
            (restart_windows_tray.TrayWindow(10, 20),),
            (restart_windows_tray.TrayWindow(30, 40),),
        ))
        launched = mock.Mock()
        launched.poll.return_value = None
        result = restart_windows_tray.restart_tray(
            self.target,
            find_windows=lambda _target: next(windows),
            stop_window=lambda handle: handle == 20,
            alive=lambda _pid: False,
            start=lambda _target: launched,
            services=lambda tray_pid, executable: (51, 52)
            if tray_pid == 30 and executable == self.service else (),
            sleep=lambda _seconds: None,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.old_tray_pid, 10)
        self.assertEqual(result.new_tray_pid, 30)
        self.assertEqual(result.service_pids, (51, 52))


if __name__ == "__main__":
    unittest.main()
