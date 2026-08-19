import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.media import FilesystemBackend, MediaOffline, MediaUnavailable
from peach.platform import (
    UNMAPPED_ROOT,
    is_unmapped,
    is_windows_path,
    root_online,
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


if __name__ == "__main__":
    unittest.main()
