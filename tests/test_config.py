import os
import unittest
from pathlib import Path

from peach import config


class DefaultPathTests(unittest.TestCase):
    def test_windows_runtime_defaults_to_the_desktop_project(self):
        project = Path.home() / "Desktop" / "peach"
        self.assertEqual(config._WINDOWS_DATA_ROOT, project / "peach-data")
        self.assertEqual(config._WINDOWS_SHARED_ROOT, project / "peach-sync")

    def test_macos_shared_copy_is_the_windows_smb_mount(self):
        self.assertEqual(config._POSIX_SHARED_ROOT, Path("/Volumes/peach-sync"))

    def test_each_platform_has_a_distinct_mdns_name(self):
        expected = "peach-win" if os.name == "nt" else "peach"
        self.assertEqual(config.MDNS_NAME, expected)
