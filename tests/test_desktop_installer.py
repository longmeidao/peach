"""安装包与 Peach 自身更新、卸载机制之间的约定。"""
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from peach import desktop_installer
from peach.windows_restart import TrayWindow

ISS = Path(__file__).resolve().parents[1] / "scripts" / "installer" / "peach.iss"


def iss_value(pattern: str) -> str:
    match = re.search(pattern, ISS.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise AssertionError(f"peach.iss 里没有 {pattern}")
    return match.group(1)


class InstallerContractTests(unittest.TestCase):
    def test_installer_registers_under_the_key_peach_cleans_up(self):
        self.assertEqual(iss_value(r"^AppId=\{\{([0-9A-F-]+)\}$"), desktop_installer.APP_ID)

    def test_start_menu_entry_is_the_shortcut_peach_removes(self):
        name = iss_value(r'^Name: "\{userprograms\}\\([^"]+)"; Filename: "\{app\}\\Peach\.exe"')
        self.assertEqual(name + ".lnk", desktop_installer.MENU_SHORTCUT)


class InstallerHandoffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_update_carries_only_the_uninstaller_into_the_new_directory(self):
        old, new = self.root / "old", self.root / "new"
        old.mkdir(); new.mkdir()
        for name in ("unins000.exe", "unins000.dat", "unins000.msg", "Peach.exe", "unins.txt"):
            (old / name).write_text(name)
        desktop_installer.carry_uninstaller(old, new)
        self.assertEqual(sorted(path.name for path in new.iterdir()),
                         ["unins000.dat", "unins000.exe", "unins000.msg"])
        self.assertTrue(desktop_installer.installed(new))
        self.assertFalse(desktop_installer.installed(self.root))

    def test_entry_refuses_outside_a_standalone_windows_package(self):
        with patch.object(desktop_installer.distribution, "standalone", return_value=False):
            self.assertEqual(desktop_installer.main("--installer-stop"), 2)

    def test_stop_waits_for_the_tray_to_exit(self):
        windows = [(TrayWindow(10, 20),), (TrayWindow(10, 20),), ()]
        with patch("peach.windows_restart.find_tray_windows", side_effect=lambda _: windows.pop(0)), \
                patch("peach.windows_restart.post_stop") as post, \
                patch.object(desktop_installer, "_running_from", return_value=[]), \
                patch.object(desktop_installer.time, "sleep"):
            self.assertTrue(desktop_installer.stop(self.root))
        post.assert_called_once_with(20)

    def test_the_uninstaller_that_called_us_is_not_a_stray(self):
        program = self.root / "Peach"
        paths = {1: str(program / "unins000.exe"), 2: str(self.root / "temp" / "_unins.tmp"),
                 3: str(program / "Peach.exe"), 4: str(program / "_internal" / "ffmpeg.exe")}
        parents = {2: 1, 3: 2, 4: 99}
        with patch("peach.windows_restart._process_paths_and_parents", return_value=(paths, parents)), \
                patch.object(desktop_installer.os, "getpid", return_value=3):
            self.assertEqual(desktop_installer._running_from(program), [4])

    def test_stop_reports_a_tray_that_never_exits(self):
        with patch("peach.windows_restart.find_tray_windows", return_value=(TrayWindow(10, 20),)), \
                patch("peach.windows_restart.post_stop"), \
                patch.object(desktop_installer.time, "sleep"), \
                patch.object(desktop_installer.time, "monotonic", side_effect=[0, 0, 100]):
            self.assertFalse(desktop_installer.stop(self.root, timeout=1))

    def test_uninstall_also_withdraws_startup_and_desktop_shortcuts(self):
        with patch.object(desktop_installer.distribution, "standalone", return_value=True), \
                patch.object(desktop_installer.sys, "platform", "win32"), \
                patch.object(desktop_installer, "stop", return_value=True), \
                patch.object(desktop_installer, "remove_shortcuts") as remove:
            self.assertEqual(desktop_installer.main("--installer-stop"), 0)
            remove.assert_not_called()
            self.assertEqual(desktop_installer.main("--installer-uninstall"), 0)
            remove.assert_called_once()


if __name__ == "__main__":
    unittest.main()
