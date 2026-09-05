from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach import windows_restart


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "restart_windows_tray.py"


def load_entry():
    """命令行入口只做参数解析和打印，实现在 `peach.windows_restart`。"""
    spec = importlib.util.spec_from_file_location("restart_windows_tray_entry", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        result = windows_restart.restart_tray(
            self.target, find_windows=lambda _target: (), start=start,
        )
        self.assertFalse(result.ok)
        self.assertIn("唯一", result.message)
        start.assert_not_called()

    def test_timeout_never_force_kills_or_starts_a_second_tray(self):
        start = mock.Mock()
        result = windows_restart.restart_tray(
            self.target, timeout=0.001,
            find_windows=lambda _target: (windows_restart.TrayWindow(10, 20),),
            stop_window=lambda _handle: True, alive=lambda _pid: True,
            start=start, sleep=lambda _seconds: None,
        )
        self.assertFalse(result.ok)
        self.assertIn("未强杀、未另启", result.message)
        start.assert_not_called()

    def test_normal_exit_restarts_and_requires_tray_owned_services(self):
        windows = iter((
            (windows_restart.TrayWindow(10, 20),),
            (windows_restart.TrayWindow(30, 40),),
        ))
        launched = mock.Mock()
        launched.poll.return_value = None
        result = windows_restart.restart_tray(
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

    def stage(self) -> Path:
        staged = self.root / "staging" / "Peach.exe"
        staged.parent.mkdir()
        staged.write_bytes(b"new")
        return staged

    def test_the_binary_is_swapped_after_the_old_tray_exits_and_before_the_new_starts(self):
        staged = self.stage()
        launched = mock.Mock()
        launched.poll.return_value = None
        bytes_at_start = []
        windows = iter((
            (windows_restart.TrayWindow(10, 20),),
            (windows_restart.TrayWindow(30, 40),),
        ))
        result = windows_restart.restart_tray(
            self.target, swap_from=staged,
            find_windows=lambda _target: next(windows),
            stop_window=lambda _handle: True,
            alive=lambda _pid: False,
            start=lambda target: bytes_at_start.append(target.read_bytes()) or launched,
            services=lambda _pid, _executable: (51, 52),
            sleep=lambda _seconds: None,
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(bytes_at_start, [b"new"], "新托盘启动时读到的已经是新二进制")
        self.assertEqual(self.target.read_bytes(), b"new")
        self.assertEqual(Path(result.backup).read_bytes(), b"tray")
        self.assertEqual(result.swapped_from, str(staged))

    def test_a_new_tray_that_never_owns_its_services_is_rolled_back(self):
        staged = self.stage()
        launched = mock.Mock()
        launched.poll.return_value = None
        start = mock.Mock(return_value=launched)
        result = windows_restart.restart_tray(
            self.target, timeout=0.001, swap_from=staged,
            find_windows=lambda _target: (windows_restart.TrayWindow(10, 20),),
            stop_window=lambda _handle: True,
            alive=lambda _pid: False,
            start=start,
            services=lambda _pid, _executable: (),
            sleep=lambda _seconds: None,
        )
        self.assertFalse(result.ok)
        self.assertIn("已回滚到备份并重开旧托盘", result.message)
        self.assertEqual(self.target.read_bytes(), b"tray")
        self.assertEqual(Path(result.backup).read_bytes(), b"tray",
                         "备份留在原地，下一次失败还有得退")
        self.assertEqual(start.call_count, 2)


class RestartEntryTests(unittest.TestCase):
    def test_the_entry_hands_the_package_to_swap_and_prints_the_outcome(self):
        entry = load_entry()
        finished = windows_restart.RestartResult(True, "重启完成", backup="C:/dist/backup.exe")
        with (
            mock.patch.object(entry, "restart_tray", return_value=finished) as restart,
            contextlib.redirect_stdout(io.StringIO()) as printed,
        ):
            self.assertEqual(entry.main(["--swap-from", "staged.exe"]), 0)
        self.assertEqual(restart.call_args.kwargs["swap_from"], Path("staged.exe"))
        self.assertEqual(json.loads(printed.getvalue())["backup"], "C:/dist/backup.exe")


if __name__ == "__main__":
    unittest.main()
