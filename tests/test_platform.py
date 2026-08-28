import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from peach.media import FilesystemBackend, MediaOffline, MediaUnavailable
from peach.platform import (
    UNMAPPED_ROOT,
    is_unmapped,
    is_windows_path,
    mount_share,
    mount_share_command,
    _windows_reveal,
    reveal_path,
    root_online,
    share_credentials_command,
    share_credentials_present,
    share_url,
    system_volume,
    translate_ledger_path,
    translate_roots,
    within_root,
)
from peach.repository import MediaAsset


POSIX_ONLY = unittest.skipIf(os.name == "nt", "盘符翻译只在非 Windows 上发生")


class DriveTranslationTests(unittest.TestCase):
    def test_windows_path_shape_is_recognised(self):
        self.assertTrue(is_windows_path(r"R:\Media\one.mp4"))
        self.assertTrue(is_windows_path("B:/one.mp4"))
        self.assertFalse(is_windows_path("/Volumes/RESOURCES/media/one.mp4"))
        self.assertFalse(is_windows_path("relative/one.mp4"))

    @POSIX_ONLY
    def test_ledger_drive_is_mapped_to_the_local_mount(self):
        with patch.dict("os.environ", {"PEACH_DRIVE_MAP": "R=/mnt/res,B=/mnt/115"}):
            self.assertEqual(
                translate_ledger_path(r"R:\Media\创作者\one.mp4"),
                Path("/mnt/res/Media/创作者/one.mp4"),
            )
            self.assertEqual(translate_ledger_path("B:/x/one.mp4"), Path("/mnt/115/x/one.mp4"))

    @POSIX_ONLY
    def test_unmapped_drive_never_becomes_a_relative_path(self):
        """没有挂载点的盘符必须落到不可达根，否则会被当成当前目录下的同名文件。"""
        with patch.dict("os.environ", {"PEACH_DRIVE_MAP": "R=/mnt/res"}):
            path = translate_ledger_path(r"Z:\secret\one.mp4")
        self.assertTrue(path.is_absolute())
        self.assertTrue(is_unmapped(path))
        self.assertTrue(str(path).startswith(str(UNMAPPED_ROOT)))

    @POSIX_ONLY
    def test_unmapped_roots_are_dropped_from_authorisation(self):
        with patch.dict("os.environ", {"PEACH_DRIVE_MAP": "R=/mnt/res,A=,B="}):
            roots = translate_roots((r"R:\media", "B:/", "A:/"))
        self.assertEqual(roots, (Path("/mnt/res/media"),))

    def test_posix_path_passes_through_untouched(self):
        self.assertEqual(translate_ledger_path("/tmp/one.mp4"), Path("/tmp/one.mp4"))

    def test_system_volume_is_the_disk_gate_target(self):
        self.assertEqual(system_volume(), Path("C:/") if os.name == "nt" else Path("/"))


class RootBoundaryTests(unittest.TestCase):
    def test_within_root_accepts_exact_and_nested(self):
        root = Path("/mnt/res/media")
        self.assertTrue(within_root(root, root))
        self.assertTrue(within_root(root / "a" / "b.mp4", root))

    def test_within_root_rejects_sibling_and_shorter_paths(self):
        root = Path("/mnt/res/media")
        self.assertFalse(within_root(Path("/mnt/res/other/b.mp4"), root))
        self.assertFalse(within_root(Path("/mnt"), root))

    def test_within_root_survives_case_only_differences_on_insensitive_mounts(self):
        """账本写 `R:\\Media`，授权根是 `.../media`；大小写不敏感的挂载必须仍然放行。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "media"
            root.mkdir()
            shouting = Path(tmp) / "MEDIA" / "one.mp4"
            insensitive = (Path(tmp) / "MEDIA").is_dir()
            self.assertEqual(within_root(shouting, root), insensitive)

    def test_root_online_needs_a_readable_mount_not_just_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(root_online(Path(tmp)))
        self.assertFalse(root_online(Path(tmp)))
        self.assertFalse(root_online(UNMAPPED_ROOT))


class OfflineModeTests(unittest.TestCase):
    """脱盘是来源级判定：一个盘不在，不影响其他盘上的资产。"""

    def _backend(self, tmp: Path) -> FilesystemBackend:
        return FilesystemBackend([tmp], tmp / "snapshots")

    @POSIX_ONLY
    def test_asset_on_an_unmapped_drive_reports_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend = self._backend(Path(tmp))
            with patch.dict("os.environ", {"PEACH_DRIVE_MAP": "R=/mnt/res"}):
                with self.assertRaises(MediaOffline) as caught:
                    backend.file_for(MediaAsset(1, r"Z:\video\one.mp4", None))
        self.assertEqual(caught.exception.source, "Z:")
        self.assertEqual(caught.exception.asset_id, 1)

    @POSIX_ONLY
    def test_asset_on_a_detached_but_mapped_drive_reports_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            detached = Path(tmp) / "gone"
            backend = FilesystemBackend([detached], Path(tmp) / "snapshots")
            with patch.dict("os.environ", {"PEACH_DRIVE_MAP": f"R={detached}"}):
                with self.assertRaises(MediaOffline):
                    backend.file_for(MediaAsset(2, r"R:\video\one.mp4", None))

    @POSIX_ONLY
    def test_missing_file_on_a_live_drive_is_not_offline(self):
        """单个文件丢失和整块盘不在必须分开报，否则前端会误显示脱盘模式。"""
        with tempfile.TemporaryDirectory() as tmp:
            live = Path(tmp)
            backend = FilesystemBackend([live], live / "snapshots")
            with patch.dict("os.environ", {"PEACH_DRIVE_MAP": f"R={live}"}):
                with self.assertRaises(MediaUnavailable) as caught:
                    backend.file_for(MediaAsset(3, r"R:\nope.mp4", None))
        self.assertNotIsInstance(caught.exception, MediaOffline)

    def test_source_status_reports_each_root_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            live = Path(tmp)
            dead = live / "gone"
            status = FilesystemBackend([live, dead], live / "snapshots").source_status()
        self.assertEqual([row["online"] for row in status], [True, False])


class RevealPathTests(unittest.TestCase):
    """在文件管理器里定位源文件。"""

    @unittest.skipUnless(os.name == "nt", "Windows Shell API only")
    def test_windows_uses_the_native_shell_selection_api(self):
        ole32, shell32 = Mock(), Mock()
        ole32.CoInitializeEx.return_value = 0

        def parse(_path, _bind, output, _attributes, _read_attributes):
            output._obj.value = 1234
            return 0

        shell32.SHParseDisplayName.side_effect = parse
        shell32.SHOpenFolderAndSelectItems.return_value = 0
        with patch("peach.platform.ctypes.WinDLL",
                   side_effect=lambda name: ole32 if name == "ole32" else shell32):
            _windows_reveal(Path(r"B:\创作者 a\c,d.mp4"))
        self.assertEqual(shell32.SHParseDisplayName.call_args.args[0],
                         r"B:\创作者 a\c,d.mp4")
        self.assertEqual(shell32.SHOpenFolderAndSelectItems.call_args.args[1:],
                         (0, None, 0))
        ole32.CoTaskMemFree.assert_called_once()
        ole32.CoUninitialize.assert_called_once_with()

    def test_windows_reveal_delegates_to_the_native_shell(self):
        source = Path(r"B:\创作者 a\c,d.mp4")
        with (patch("peach.platform.os.name", "nt"),
              patch("peach.platform._windows_reveal") as reveal):
            self.assertTrue(reveal_path(source))
        reveal.assert_called_once_with(source)

    def test_macos_reveals_in_finder(self):
        source = Path("/Volumes/RESOURCES/media/a.mp4")
        with (patch("peach.platform.os.name", "posix"),
              patch("peach.platform.sys.platform", "darwin"),
              patch("peach.platform.subprocess.Popen") as launch):
            self.assertTrue(reveal_path(source))
        launch.assert_called_once_with(["open", "-R", str(source)], close_fds=True)

    def test_unsupported_platform_returns_false_instead_of_guessing(self):
        with (patch("peach.platform.os.name", "posix"),
              patch("peach.platform.sys.platform", "linux")):
            self.assertFalse(reveal_path(Path("/srv/a.mp4")))



if __name__ == "__main__":
    unittest.main()


def _found(*_args, **_kwargs):
    """`security find-internet-password` 找到了记录。"""
    return Mock(returncode=0, stdout="", stderr="")


class ShareMountTests(unittest.TestCase):
    """把掉了的 SMB 共享挂回来。这条路径失败必须降级，不能抛、不能卡、不能弹框。"""

    def test_url_keeps_the_ordinary_case_readable(self):
        self.assertEqual(
            share_url("peach-win.local", "peach-sync", "peachsync"),
            "smb://peachsync@peach-win.local/peach-sync")

    def test_url_without_a_user_has_no_stray_at_sign(self):
        self.assertEqual(
            share_url("peach-win.local", "peach-sync"),
            "smb://peach-win.local/peach-sync")

    def test_url_percent_encodes_every_segment(self):
        # URL 在 AppleScript 里落在一对双引号中间：账号或主机带引号、反斜杠就能拼出
        # 第二条语句。编码之后这两个字符不可能出现在字面量里。
        url = share_url('pe"ach\\win', 'sh"are', 'us"er')
        self.assertNotIn('"', url)
        self.assertNotIn("\\", url)

    def test_macos_mounts_through_netfs_without_a_finder_window(self):
        with patch("peach.platform.sys.platform", "darwin"):
            command = mount_share_command("smb://peachsync@peach-win.local/peach-sync")
        # `open smb://` 也走 NetFS、也能挂上，但会顺带弹一个 Finder 窗口；
        # 菜单栏那条动作不该在用户没看着的时候把窗口翻到前面来。
        self.assertEqual(command, [
            "osascript", "-e",
            'mount volume "smb://peachsync@peach-win.local/peach-sync"'])

    def test_other_platforms_have_no_mount_path(self):
        runner = Mock()
        with patch("peach.platform.sys.platform", "linux"):
            self.assertIsNone(mount_share_command("smb://host/share"))
            self.assertFalse(mount_share("host", "share", "user", run=runner))
        runner.assert_not_called()

    def test_keychain_lookup_never_asks_for_the_password_itself(self):
        # 带 `-w` 就会把密码打到 stdout，于是密码要经过本进程。只判断记录在不在，
        # 不需要它，也不该碰它。
        command = share_credentials_command("peach-win.local", "peachsync")
        self.assertNotIn("-w", command)
        self.assertEqual(command[:2], ["security", "find-internet-password"])
        self.assertIn("peach-win.local", command)
        self.assertIn("peachsync", command)

    def test_a_missing_keychain_entry_fails_fast_instead_of_prompting(self):
        # 2026-08-27 实测：钥匙串里没有这台主机的记录时，NetFS 不报错，而是拉起
        # NetAuthAgent 弹认证框并一直等到超时——用户没点过密码框，却看见一个。
        runner = Mock(return_value=Mock(returncode=44, stdout="", stderr="not found"))
        with patch("peach.platform.sys.platform", "darwin"):
            self.assertFalse(mount_share("peach-win.local", "peach-sync", "peachsync",
                                         run=runner))
        runner.assert_called_once()
        self.assertEqual(runner.call_args.args[0][:2],
                         ["security", "find-internet-password"])

    def test_a_present_keychain_entry_goes_on_to_mount(self):
        runner = Mock(side_effect=[_found(), Mock(returncode=0, stdout="", stderr="")])
        with patch("peach.platform.sys.platform", "darwin"):
            self.assertTrue(mount_share("peach-win.local", "peach-sync", "peachsync",
                                        run=runner))
        self.assertEqual(runner.call_args.args[0][0], "osascript")

    def test_an_anonymous_mount_skips_the_keychain_check(self):
        runner = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
        with patch("peach.platform.sys.platform", "darwin"):
            self.assertTrue(mount_share("peach-win.local", "peach-sync", run=runner))
        runner.assert_called_once()
        self.assertEqual(runner.call_args.args[0][0], "osascript")

    def test_a_failed_keychain_lookup_is_false_not_an_exception(self):
        self.assertFalse(share_credentials_present(
            "peach-win.local", "peachsync", run=Mock(side_effect=OSError("没有 security"))))

    def test_mount_is_bounded_by_a_timeout(self):
        # 认证框只是最常见的一种等待；网络半通时 SMB 协商同样会挂着。没有超时，
        # 托盘那个线程就永远停在这里，「同步 Ledger」再也点不动。
        runner = Mock(side_effect=[_found(), Mock(returncode=0, stdout="", stderr="")])
        with patch("peach.platform.sys.platform", "darwin"):
            self.assertTrue(mount_share("peach-win.local", "peach-sync", "peachsync",
                                        run=runner))
        self.assertGreater(runner.call_args.kwargs["timeout"], 0)

    def test_every_mount_failure_is_false_not_an_exception(self):
        failures = (
            Mock(returncode=1, stdout="", stderr="No route to host"),
            subprocess.TimeoutExpired("osascript", 15),
            OSError("osascript 不存在"),
        )
        with patch("peach.platform.sys.platform", "darwin"):
            for failure in failures:
                with self.subTest(failure=failure):
                    self.assertFalse(mount_share(
                        "peach-win.local", "peach-sync", "peachsync",
                        run=Mock(side_effect=[_found(), failure])))
