"""CloudDrive 表单、来源映射与离线状态的隔离回归。"""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from peach import media_configuration as media_config, onboarding, settings_file


class MediaConfigurationTests(unittest.TestCase):
    def test_windows_cloud_sources_keep_policy_ids_and_offline_roots(self):
        roots, mounts, errors = media_config.validate([
            {"location": "115", "path": "B:/"}, {"location": "pikpak", "path": "A:/"},
        ], windows=True)
        self.assertFalse(errors)
        self.assertEqual(roots, {"115": ("B:\\",), "pikpak": ("A:\\",)})
        self.assertEqual(mounts, {})

    def test_macos_multiple_mounts_preserve_declared_root_order(self):
        roots, mounts, errors = media_config.validate([
            {"location": "115", "root": "B:/Movies", "path": "/Volumes/115/Movies"},
            {"location": "115", "root": "B:/Photos", "path": "/Volumes/115/Photos"},
        ], windows=False)
        self.assertFalse(errors)
        self.assertEqual(roots["115"], ("B:\\Movies", "B:\\Photos"))
        self.assertEqual(mounts["115"], ("/Volumes/115/Movies", "/Volumes/115/Photos"))

    def test_invalid_and_overlapping_roots_return_row_errors(self):
        for rows in ([{"location": "bad", "path": "B:/"}],
                     [{"location": "115", "path": "../115"}],
                     [{"location": "115", "path": "B:/"}, {"location": "local", "path": "b:/Movies"}]):
            self.assertTrue(media_config.validate(rows, windows=True)[2])

    def test_cloud_only_setup_roundtrips_config_without_local_source(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            config = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(base)})
            answers = onboarding.Answers(base, (), "127.0.0.1", 8900, "peach", [
                {"location": "115", "path": "/Volumes/115", "root": "B:/"}])
            prepared = onboarding.configure(config, answers, windows=False)
            settings_file.write(prepared)
            loaded = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(base)})
            self.assertEqual(loaded.locations, {"115": ("B:\\",)})
            self.assertEqual(loaded.mounts, {"115": ("/Volumes/115",)})
            self.assertFalse((base / "database" / "ledger.db").exists())

    def test_unreadable_existing_mount_is_offline(self):
        config = replace(settings_file.PeachConfig(Path('/unused'), Path('/unused/config.toml')), locations={"115": ("B:/",)}, mounts={"115": ("/Volumes/115",)})
        with patch("peach.platform.os.scandir", side_effect=OSError("Device not configured")):
            self.assertFalse(media_config.rows(config, windows=False, probe=True)[0]["online"])

    def test_setup_post_reader_keeps_cloud_source_and_inline_error(self):
        from peach.routes_pages import _read_answers, setup_page
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            config = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(base)})
            submitted = {"data_root": str(base), "media_dir": ["/Volumes/115"],
                         "media_location": ["115"], "media_root": ["B:/"], "host": "1"}
            answers, errors = _read_answers(config, submitted, windows=False)
            self.assertFalse(errors)
            self.assertEqual(answers.media_sources[0]["location"], "115")
            html = setup_page(config, windows=False, values=submitted)
            self.assertIn('value="115" selected', html)
            self.assertIn('name="media_root"', html)
            self.assertIn('value="B:/"', html)
