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


from peach.config import SECRETS_DIR
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

    def test_services_never_own_ledger_sync(self):
        """浏览服务只观察写入角色；跨机复制只能由托盘显式执行。"""
        with tempfile.TemporaryDirectory() as directory:
            tls_dir = Path(directory)
            for name in ("peach-local-ca.crt", "peach.crt", "peach.key"):
                (tls_dir / name).write_text("test-only", encoding="utf-8")
            specs = build_service_specs(tls_dir=tls_dir)
        owners = [spec for spec in specs if "--no-ledger-sync" not in spec.command]
        self.assertEqual(owners, [])
        for spec in specs:
            self.assertIn("--no-ledger-sync", spec.command)

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
        # 这里只验证后台更新行为，不创建真实系统托盘。macOS 的 pystray Icon 构造会向
        # WindowServer 注册应用；在 Codex seatbelt 沙箱内系统会直接 SIGABRT，连测试
        # 报告都来不及生成，并弹出「Python 意外退出」。
        with patch("peach.tray.pystray.Icon", return_value=Mock()):
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


class ServiceStatusTests(unittest.TestCase):
    """状态文案逐个点名：正常的和异常的都写明白，异常的带上失败原因。

    只说「未运行」没法行动：HTTP 和 HTTPS 会因为端口占用、证书过期、pf 转发写错
    等完全不同的原因挂掉，而且服务活着时探测本身也可能被骗（见代理劫持的回归测试）。
    """

    def manager(self, health: dict) -> ServiceManager:
        specs = tuple(
            ServiceSpec(name, f"http://127.0.0.1/{name}", ("noop",), True)
            for name in health
        )
        manager = ServiceManager(specs)
        manager._last_health.update(health)
        return manager

    def test_all_healthy(self):
        self.assertEqual(
            self.manager({"http": (True, ""), "https": (True, "")}).status(),
            "HTTP 正常 · HTTPS 正常",
        )

    def test_none_healthy(self):
        self.assertEqual(
            self.manager({"http": (False, "无响应"), "https": (False, "无响应")}).status(),
            "HTTP 异常（无响应） · HTTPS 异常（无响应）",
        )

    def test_partial_names_the_broken_one_with_reason(self):
        self.assertEqual(
            self.manager({"http": (True, ""), "https": (False, "状态码 503")}).status(),
            "HTTP 正常 · HTTPS 异常（状态码 503）",
        )
        self.assertEqual(
            self.manager({"http": (False, "状态码 503"), "https": (True, "")}).status(),
            "HTTP 异常（状态码 503） · HTTPS 正常",
        )

    def test_health_check_never_goes_through_a_proxy(self):
        """健康检查必须绕过代理：Stash 等客户端设置系统级 HTTP 代理后，httpx 默认
        把 127.0.0.1 的探测送进代理、由代理回 503，服务活着却被判成「未运行」。"""
        seen: dict = {}

        def probe(url, **kwargs):
            seen.update(kwargs)
            return Response()

        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("noop",), True)
        manager = ServiceManager((spec,), popen=Mock(), health_get=probe)
        self.assertTrue(manager.healthy(spec))
        self.assertIs(seen.get("trust_env"), False)

    @patch("peach.tray.DATABASE_PATH", Path("/local/ledger.db"))
    @patch("peach.tray.SHARED_DATABASE_PATH", Path("/shared/ledger.db"))
    def test_manual_sync_stops_owned_service_and_restarts_it(self):
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        process = Mock()
        process.poll.return_value = None
        completed = Mock(returncode=0, stdout="账本同步：in-sync · 两侧已经一致\n", stderr="")
        manager = ServiceManager((spec,), popen=Mock(return_value=process), run=Mock(return_value=completed))
        manager._owned["http"] = process
        with patch.object(manager, "healthy", return_value=True), patch.object(
            manager, "start_missing"
        ) as start, patch.object(manager, "wait_until_ready", return_value=True):
            ok, message = manager.sync_ledger(Path("/venv/peach"))
        self.assertTrue(ok)
        self.assertIn("两侧已经一致", message)
        process.terminate.assert_called_once()
        start.assert_called_once()
        self.assertEqual(
            manager._run.call_args.args[0][:2],
            [str(Path("/venv/peach")), "ledger-sync"],
        )
        self.assertEqual(manager._run.call_args.kwargs["encoding"], "utf-8")
        self.assertEqual(
            manager._run.call_args.kwargs["env"]["PYTHONIOENCODING"], "utf-8",
        )

    def test_take_ownership_is_an_explicit_ledger_command(self):
        manager = ServiceManager(tuple(), run=Mock(return_value=Mock(
            returncode=0, stdout="账本同步：take-ownership\n", stderr="",
        )))
        with patch.object(manager, "start_missing"), patch.object(
            manager, "wait_until_ready", return_value=True,
        ):
            ok, _message = manager.sync_ledger(Path("/venv/peach"), take_ownership=True)
        self.assertTrue(ok)
        self.assertIn("--take-ownership", manager._run.call_args.args[0])

    def test_manual_sync_refuses_a_healthy_unowned_service(self):
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        runner = Mock()
        manager = ServiceManager((spec,), health_get=lambda *args, **kwargs: Response(), run=runner)
        ok, message = manager.sync_ledger(Path("/venv/peach"))
        self.assertFalse(ok)
        self.assertIn("不归本托盘管理", message)
        runner.assert_not_called()


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

    def test_service_specs_avoid_privileged_ports_and_a_pinned_address(self):
        """80/443 在 macOS 上要 root，所以服务跑在高位端口、由 pf 转发过去；
        地址钉死等于换个 Wi-Fi 就打不开。"""
        specs = build_service_specs()
        self.assertIn(len(specs), (1, 2))          # 没有 TLS 材料时只有 http
        self.assertEqual(specs[0].name, "http")
        for spec in specs:
            command = spec.command
            self.assertIn("--port", command)
            self.assertGreater(int(command[command.index("--port") + 1]), 1024)
            self.assertNotIn("--mdns-address", command)

    def test_https_spec_only_appears_with_real_tls_material(self):
        """macOS 这份是开发环境：没有本机 CA 也应该能用，不像 Windows 那样直接报错。"""
        specs = {spec.name: spec for spec in build_service_specs()}
        material = (SECRETS_DIR / "tls" / "peach.crt").is_file()
        self.assertEqual("https" in specs, material)
        if material:
            command = specs["https"].command
            self.assertIn("--ssl-certfile", command)
            # 两份服务只能有一份发布 mDNS，否则同名记录互相打架。
            self.assertIn("--no-mdns", command)
            self.assertTrue(str(specs["https"].verify).endswith("peach-local-ca.crt"))


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

    def test_launcher_never_execs_the_interpreter_itself(self):
        """外壳不能自己 exec 到解释器。

        macOS 26 上主可执行文件是 exec 跳板时状态项注册不上：进程活着、NSStatusItem
        也建出来了，但按钮窗口永远是 (0,0,34,0)，菜单栏上什么都不出现（FB21015611）。
        双击只负责踢 LaunchAgent，真正的菜单栏进程是 launchd 的直接子进程。
        """
        app = self.module.build(self.root, self.tray)
        launcher = app / "Contents" / "MacOS" / "Peach"
        self.assertTrue(os.access(launcher, os.X_OK))
        body = launcher.read_text(encoding="utf-8")
        self.assertIn("launchctl kickstart", body)
        self.assertNotIn(str(self.tray), body)

    def test_bundle_carries_a_rounded_icon(self):
        """方形原图直接当图标会比周围大一圈、四角还是直的。"""
        app = self.module.build(self.root, self.tray)
        import plistlib as _plistlib
        info = _plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
        icon = ROOT / "resources" / "peach.icns"
        if icon.is_file():
            self.assertEqual(info.get("CFBundleIconFile"), "peach")
            self.assertTrue((app / "Contents" / "Resources" / "peach.icns").is_file())

    def test_rebuild_replaces_a_stale_bundle(self):
        app = self.module.build(self.root, self.tray)
        (app / "Contents" / "MacOS" / "stale").write_text("x", encoding="utf-8")
        self.module.build(self.root, self.tray)
        self.assertFalse((app / "Contents" / "MacOS" / "stale").exists())


if __name__ == "__main__":
    unittest.main()
