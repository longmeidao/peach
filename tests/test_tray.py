import importlib.util
import os
import plistlib
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    """按路径加载 `scripts/` 下的脚本；它们不是包的一部分。"""
    spec = importlib.util.spec_from_file_location(f"test_{name}", ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


from peach.tray import (
    AlreadyRunning, PeachTray, ServiceManager, ServiceSpec, SingleInstance,
    apply_macos_template, build_service_specs, create_icon, enable_hidpi,
)
from peach.versioning import UpdateResult, VersionSnapshot


class Response:
    status_code = 200

    @staticmethod
    def json():
        return {"ok": True}


class TrayTests(unittest.TestCase):
    def test_create_icon_has_expected_size_and_alpha(self):
        icon = create_icon(64)
        self.assertEqual(icon.size, (64, 64))
        self.assertEqual(icon.mode, "RGBA")

    def test_start_missing_does_not_duplicate_healthy_service(self):
        spec = ServiceSpec("http", "http://local/healthz", ("peach", "serve"), True)
        popen = Mock()
        manager = ServiceManager((spec,), popen=popen, health_get=lambda *args, **kwargs: Response())
        manager.start_missing()
        popen.assert_not_called()

    @patch("peach.tray.LOG_DIR")
    def test_start_and_stop_only_owned_service(self, log_dir):
        with tempfile.TemporaryDirectory() as directory:
            log_dir.__fspath__ = lambda: directory
            log_dir.mkdir.side_effect = lambda **_kwargs: None
            log_dir.__truediv__.side_effect = lambda name: Path(directory) / name
            spec = ServiceSpec("http", "http://local/healthz", ("peach", "serve"), True)
            process = Mock()
            process.poll.return_value = None
            popen = Mock(return_value=process)
            manager = ServiceManager(
                (spec,), popen=popen,
                health_get=Mock(side_effect=OSError("down")),
            )
            manager.start_missing()
            popen.assert_called_once()
            manager.stop_owned()
            process.terminate.assert_called_once()

    @unittest.skipUnless(
        os.name == "nt", "DPI 声明与单实例锁是 Windows 托盘专属能力"
    )
    @patch("peach.tray.ctypes.windll.user32.SetProcessDpiAwarenessContext", create=True)
    def test_hidpi_prefers_per_monitor_v2(self, set_context):
        set_context.return_value = True
        self.assertEqual(enable_hidpi(), "per-monitor-v2")

    def test_update_check_is_background_notification_not_modal_dialog(self):
        snapshot = VersionSnapshot("0.2.1", "master", "abc12345", False, False, None)
        completed = threading.Event()

        class Versions:
            def inspect(self):
                return snapshot

            def check(self):
                completed.set()
                return UpdateResult("unconfigured", "未配置更新源", snapshot)

        icon = Mock()
        tray = PeachTray(ServiceManager(tuple()), Versions())
        tray.check_updates(icon)
        self.assertTrue(completed.wait(2))
        for _ in range(20):
            if icon.notify.call_count == 2:
                break
            time.sleep(0.01)
        self.assertEqual(icon.notify.call_count, 2)
        icon.update_menu.assert_called_once()

    def test_single_instance_rejects_a_second_holder(self):
        """两个菜单栏项会各自再拉起一份服务去抢同一个端口，必须挡住。"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tray.lock"
            first = SingleInstance(path)
            second = SingleInstance(path)
            first.acquire()
            try:
                with self.assertRaises(AlreadyRunning):
                    second.acquire()
            finally:
                first.close()


@unittest.skipUnless(sys.platform == "darwin", "菜单栏图标与服务规格是 macOS 专属")
class MacMenuBarTests(unittest.TestCase):
    def test_template_icon_is_a_black_silhouette(self):
        """macOS 菜单栏图标必须是 template image：彩色图不会跟着浅色/深色反色。"""
        colored = create_icon(32)
        template = create_icon(32, template=True)
        self.assertEqual(template.size, colored.size)
        self.assertEqual(template.getchannel("A").tobytes(), colored.getchannel("A").tobytes())
        opaque = [p for p in template.convert("RGBA").getdata() if p[3] > 0]
        self.assertTrue(opaque, "模板图不该整张透明")
        self.assertTrue(all(p[:3] == (0, 0, 0) for p in opaque), "模板图的颜色必须全黑")

    def test_service_spec_avoids_privileged_ports_and_a_pinned_address(self):
        """80/443 在 macOS 上要 root；地址钉死等于换个 Wi-Fi 就打不开。"""
        specs = build_service_specs()
        self.assertEqual(len(specs), 1)
        command = specs[0].command
        self.assertIn("--port", command)
        self.assertGreater(int(command[command.index("--port") + 1]), 1024)
        self.assertNotIn("--mdns-address", command)
        self.assertNotIn("--ssl-certfile", command)


class TemplateHookTests(unittest.TestCase):
    def test_apply_template_is_a_no_op_without_a_backing_nsimage(self):
        """拿不到底层 NSImage 就安静跳过：菜单栏项本身仍然可用。"""
        self.assertFalse(apply_macos_template(Mock(spec=[])))


class MacAppBundleTests(unittest.TestCase):
    """菜单栏项必须打成 bundle 才拿得稳。

    裸控制台进程启动 `peach-tray` 时，AppKit 的运行循环没有应用上下文会立刻返回：
    服务起来了、托盘父进程却安静退出，退出码 0、零输出。实测就是这样。
    """

    def setUp(self):
        self.module = load_script("build_macos_app")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.tray = self.root / "peach-tray"
        self.tray.write_text("#!/bin/sh\n", encoding="utf-8")

    def test_bundle_declares_itself_as_a_menu_bar_agent(self):
        app = self.module.build(self.root, self.tray)
        info = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
        # LSUIElement：只在菜单栏出现，不占 Dock、不进 ⌘Tab。
        self.assertIs(info["LSUIElement"], True)
        self.assertEqual(info["CFBundleExecutable"], "Peach")
        self.assertTrue(info["CFBundleIdentifier"])

    def test_launcher_is_executable_and_keeps_a_log(self):
        """`open -a` 起的进程没有终端，不落盘就完全看不出它为什么没起来。"""
        app = self.module.build(self.root, self.tray)
        launcher = app / "Contents" / "MacOS" / "Peach"
        self.assertTrue(os.access(launcher, os.X_OK))
        body = launcher.read_text(encoding="utf-8")
        self.assertIn(str(self.tray), body)
        self.assertIn("macos-tray.log", body)

    def test_rebuild_replaces_a_stale_bundle(self):
        app = self.module.build(self.root, self.tray)
        (app / "Contents" / "MacOS" / "stale").write_text("x", encoding="utf-8")
        self.module.build(self.root, self.tray)
        self.assertFalse((app / "Contents" / "MacOS" / "stale").exists())


if __name__ == "__main__":
    unittest.main()
