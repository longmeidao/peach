import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach import config


class DefaultPathTests(unittest.TestCase):
    def test_project_root_uses_pyinstaller_resource_directory_without_a_src_layer(self):
        # 锚点必须在当前平台上真的是绝对路径。`C:/repo` 在 POSIX 上是**相对**路径，
        # `_project_root` 里的 `.resolve()` 会给它前置 cwd，断言于是只在 Windows 成立。
        root = Path(tempfile.gettempdir()).resolve() / "repo"
        source = root / "src" / "peach" / "config.py"
        self.assertEqual(config._project_root(source), root)
        # bundle_root 不经过 resolve，原样构造，两个平台比较结果一致。
        self.assertEqual(
            config._project_root(source, "C:/bundle/_MEI123"),
            Path("C:/bundle/_MEI123"),
        )

    def test_windows_runtime_defaults_to_the_desktop_project(self):
        project = Path.home() / "Desktop" / "peach"
        self.assertEqual(config._WINDOWS_DATA_ROOT, project / "peach-data")
        self.assertEqual(config._WINDOWS_SHARED_ROOT, project / "peach-sync")

    def test_macos_shared_copy_is_the_windows_smb_mount(self):
        self.assertEqual(config._POSIX_SHARED_ROOT, Path("/Volumes/peach-sync"))

    def test_each_platform_has_a_distinct_mdns_name(self):
        expected = "peach-win" if os.name == "nt" else "peach"
        self.assertEqual(config.MDNS_NAME, expected)


class SharedShareTests(unittest.TestCase):
    """托盘补挂共享副本要用的坐标。"""

    def test_share_host_is_an_mdns_name_not_a_dhcp_address(self):
        # 家里的 IP 由路由器 DHCP 分配，钉进源码总有失效的一天；主机名走 mDNS
        # 才能跟着换。Windows 那台的 mDNS 名和 `MDNS_NAME` 用的是同一个常量。
        self.assertEqual(config.SHARED_SMB_HOST, "peach-win.local")
        self.assertNotRegex(config.SHARED_SMB_HOST, r"^\d+\.\d+\.\d+\.\d+$")
        self.assertEqual(config._WINDOWS_MDNS_NAME, "peach-win")

    def test_share_name_matches_the_macos_mount_point(self):
        # 挂载点是 `/Volumes/<共享名>`：两者分开写就会挂上一个没人去读的路径。
        self.assertEqual(config.SHARED_SMB_SHARE, config._POSIX_SHARED_ROOT.name)

    def test_share_user_is_named_because_the_server_refuses_guest(self):
        self.assertEqual(config.SHARED_SMB_USER, "peachsync")

    def test_every_share_coordinate_can_be_overridden(self):
        # 主机名换了、共享改名、账号换一个，都不该要求改源码再发一次版。
        overrides = {
            "PEACH_SHARED_SMB_HOST": "192.168.1.9",
            "PEACH_SHARED_SMB_SHARE": "ledger-drop",
            "PEACH_SHARED_SMB_USER": "someone",
        }
        try:
            with patch.dict(os.environ, overrides):
                reloaded = importlib.reload(config)
                self.assertEqual(reloaded.SHARED_SMB_HOST, "192.168.1.9")
                self.assertEqual(reloaded.SHARED_SMB_SHARE, "ledger-drop")
                self.assertEqual(reloaded.SHARED_SMB_USER, "someone")
        finally:
            importlib.reload(config)
        self.assertEqual(config.SHARED_SMB_HOST, "peach-win.local")
