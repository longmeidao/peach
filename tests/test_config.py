import os
import tempfile
import unittest
from pathlib import Path

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
