"""独立包更新使用临时目录验证路径、进度、重启确认及回滚。"""
import json
import hashlib
from contextlib import nullcontext
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from peach import standalone_update as update


class StandaloneUpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.state = self.root / "state"
        self.state.mkdir()
        patcher = patch.object(update, "STATE_DIR", self.state)
        patcher.start(); self.addCleanup(patcher.stop)

    def archive(self, names):
        archive = self.root / "package.zip"
        with zipfile.ZipFile(archive, "w") as package:
            for name in names:
                package.writestr(name, "fixture")
        return archive

    def test_zip_requires_a_complete_standalone_layout_and_reports_progress(self):
        archive = self.archive(["Peach/Peach.exe", "Peach/_internal/standalone.txt"])
        progress = Mock()
        root = update.extract(archive, self.root / "extract", progress)
        self.assertTrue((root / "Peach.exe").is_file())
        self.assertEqual(progress.call_args.args, (2, 2))

    def test_zip_rejects_traversal_windows_streams_and_case_collisions(self):
        for name in ("../escape", "Peach/../escape", "C:/escape", "Peach/a:b", "Peach/Peach.exe"):
            with self.subTest(name=name):
                archive = self.archive(["Peach/peach.exe", name])
                with self.assertRaises(ValueError):
                    update.extract(archive, self.root / "extract", Mock())

    def test_stale_progress_is_retryable_and_public_state_hides_paths(self):
        update.write({}, state="downloading", target="private-path", progress=22)
        with patch.object(update.time, "time", return_value=10**12):
            self.assertEqual(update.public()["state"], "error")
        self.assertNotIn("target", update.public())

    def test_restart_requires_ready_and_only_records_intent(self):
        with patch.object(update.distribution, "standalone", return_value=True), patch.object(update.sys, "platform", "win32"):
            with self.assertRaises(ValueError):
                update.request_restart()
            update.write({}, state="ready", version="1.0.0")
            with patch.object(update.subprocess, "Popen") as launch:
                self.assertEqual(update.request_restart()["state"], "restarting")
                launch.assert_not_called()

    def test_source_installs_cannot_start_binary_update(self):
        with patch.object(update.distribution, "standalone", return_value=False):
            with self.assertRaises(ValueError):
                update.start()

    def test_download_prepares_verified_package_without_stopping_the_app(self):
        target = self.root / "installed"; target.mkdir()
        (target / "Peach.exe").write_text("old")
        archive = self.archive(["Peach/Peach.exe", "Peach/_internal/standalone.txt"])
        with zipfile.ZipFile(archive, "a") as package:
            package.writestr("Peach/_internal/build-info.json", json.dumps({"version":"1.0.0","commit":None,"built_at":"fixture"}))
        content = archive.read_bytes()
        response = Mock()
        response.iter_bytes.return_value = [content[:10],content[10:]]
        client = Mock()
        client.stream.return_value = nullcontext(response)
        release = dict(state="available", latest_version="1.0.0", asset_size=len(content),
                       asset_digest="sha256:" + hashlib.sha256(content).hexdigest(), asset_url="https://github.com/fixture")
        lock = Mock()
        with patch.object(update.sys,"executable",str(target/"Peach.exe")), patch.object(
                update.release_updates,"check",return_value=release), patch.object(
                update.httpx,"Client",return_value=nullcontext(client)), patch.object(update.subprocess,"Popen") as launch:
            update.prepare({"id":"download-fixture"},lock)
        state = update.read()
        self.assertEqual(state["state"],"ready",state)
        self.assertEqual(state["downloaded"],len(content))
        self.assertTrue((Path(state["helper"])/"Peach.exe").is_file())
        self.assertEqual((target/"Peach.exe").read_text(),"old")
        launch.assert_not_called()
        lock.release.assert_called_once()

    def test_install_failure_restores_program_directory_and_preserves_data(self):
        target = self.root / "app"; target.mkdir()
        (target / "Peach.exe").write_text("old")
        (target / "_internal").mkdir()
        (target / "_internal" / "standalone.txt").touch()
        transaction = self.root / ".app-update-fixture"; transaction.mkdir()
        stage = transaction / "stage" / "Peach"; stage.mkdir(parents=True)
        (stage / "Peach.exe").write_text("new")
        update.write({"id":"fixture", "target":str(target), "transaction":str(transaction), "stage":str(stage), "version":"1.0.0"}, state="restarting")
        original = update.replace_with_retry
        def replace(source, destination):
            if source == stage:
                raise OSError("occupied")
            original(source, destination)
        with patch("peach.windows_restart.process_alive", return_value=False), patch.object(
                update, "replace_with_retry", side_effect=replace), patch("peach.windows_restart.start_tray") as start:
            self.assertEqual(update.apply(update.state_path(), 999), 1)
        self.assertEqual((target / "Peach.exe").read_text(), "old")
        self.assertEqual(update.public()["state"], "error")
        start.assert_called_once_with(target / "Peach.exe")
        self.assertTrue(self.state.is_dir())
