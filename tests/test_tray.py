import importlib.util
import inspect
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
    launchd_owns_this_process, restart_tray_process, tray_restart_required,
)
from peach.sync import SyncPlan
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
            specs = build_service_specs(lan_address="192.0.2.10", tls_dir=tls_dir)
        owners = [spec for spec in specs if "--no-ledger-sync" not in spec.command]
        self.assertEqual(owners, [])
        for spec in specs:
            self.assertIn("--no-ledger-sync", spec.command)

    @unittest.skipUnless(
        os.name == "nt", "macOS 走 build_macos_service_specs，不发布 LAN 地址"
    )
    def test_windows_service_address_uses_the_current_route_when_not_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            tls_dir = Path(directory)
            for name in ("peach-local-ca.crt", "peach.crt", "peach.key"):
                (tls_dir / name).write_text("test-only", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False), patch(
                "peach.tray.lan_ipv4", return_value="192.0.2.55",
            ):
                os.environ.pop("PEACH_LAN_ADDRESS", None)
                specs = build_service_specs(tls_dir=tls_dir)
        commands = [item for spec in specs for item in spec.command]
        self.assertIn("192.0.2.55", commands)

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
        manager = ServiceManager(
            (spec,), popen=Mock(return_value=process), run=Mock(return_value=completed),
            ledger_plan=lambda: SyncPlan("pull", "共享副本更新"),
        )
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
        manager = ServiceManager(
            tuple(),
            run=Mock(return_value=Mock(
                returncode=0, stdout="账本同步：take-ownership\n", stderr="")),
            ledger_plan=lambda: SyncPlan("in-sync", "两侧一致"),
        )
        with patch.object(manager, "start_missing"), patch.object(
            manager, "wait_until_ready", return_value=True,
        ):
            ok, _message = manager.sync_ledger(Path("/venv/peach"), take_ownership=True)
        self.assertTrue(ok)
        self.assertIn("--take-ownership", manager._run.call_args.args[0])

    def test_manual_sync_refuses_a_healthy_unowned_service(self):
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        runner = Mock()
        manager = ServiceManager(
            (spec,), health_get=lambda *args, **kwargs: Response(), run=runner,
            ledger_plan=lambda: SyncPlan("pull", "共享副本更新"),
        )
        ok, message = manager.sync_ledger(Path("/venv/peach"))
        self.assertFalse(ok)
        self.assertIn("不归本托盘管理", message)
        runner.assert_not_called()

    def test_an_unreachable_share_never_stops_the_services(self):
        """共享盘没挂时，停一遍服务再启回来换不到任何东西，只换来一次断网页。"""
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        process = Mock()
        process.poll.return_value = None
        runner = Mock()
        manager = ServiceManager(
            (spec,), run=runner,
            ledger_plan=lambda: SyncPlan("offline", "共享副本所在的盘不可达，本地照常读写"),
            mount_share=Mock(return_value=False),
        )
        manager._owned["http"] = process

        ok, message = manager.sync_ledger(Path("/venv/peach"))

        self.assertFalse(ok)
        self.assertIn("盘不可达", message)
        runner.assert_not_called()
        process.terminate.assert_not_called()

    def test_a_reader_that_cannot_push_is_reported_without_an_outage(self):
        """本机不是写入端时结论已经定了，跑一遍 CLI 也只会得到同一个 conflict。"""
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        process = Mock()
        process.poll.return_value = None
        runner = Mock()
        manager = ServiceManager(
            (spec,), run=runner,
            ledger_plan=lambda: SyncPlan("conflict", "当前写入端是 host-88053062，本机不能推送"),
        )
        manager._owned["http"] = process

        ok, message = manager.sync_ledger(Path("/venv/peach"))

        self.assertFalse(ok)
        self.assertIn("不能推送", message)
        runner.assert_not_called()
        process.terminate.assert_not_called()

    def test_take_ownership_still_runs_when_the_two_sides_are_in_sync(self):
        """`in-sync` 对同步是无事可做，对接管却正是要做的那一次；短路不能一视同仁。"""
        manager = ServiceManager(
            tuple(),
            run=Mock(return_value=Mock(
                returncode=0, stdout="账本同步：take-ownership\n", stderr="")),
            ledger_plan=lambda: SyncPlan("in-sync", "两侧一致"),
        )
        with patch.object(manager, "start_missing"), patch.object(
            manager, "wait_until_ready", return_value=True,
        ):
            ok, _message = manager.sync_ledger(Path("/venv/peach"), take_ownership=True)
        self.assertTrue(ok)
        manager._run.assert_called_once()

    def test_take_ownership_refuses_early_when_the_share_is_unreachable(self):
        runner = Mock()
        manager = ServiceManager(
            tuple(), run=runner,
            ledger_plan=lambda: SyncPlan("offline", "共享副本所在的盘不可达，本地照常读写"),
            mount_share=Mock(return_value=False),
        )
        ok, message = manager.sync_ledger(Path("/venv/peach"), take_ownership=True)
        self.assertFalse(ok)
        self.assertIn("先挂上共享副本所在的盘", message)
        runner.assert_not_called()

    def test_an_unmounted_share_is_mounted_once_and_then_synced(self):
        """macOS 重启后 SMB 共享不会自己回来。`offline` 是本机的日常状态，不是结论。"""
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        process = Mock()
        process.poll.return_value = None
        plans = iter([
            SyncPlan("offline", "共享副本所在的盘不可达，本地照常读写"),
            SyncPlan("pull", "共享副本更新"),
        ])
        mount = Mock(return_value=True)
        completed = Mock(returncode=0, stdout="账本同步：pull · 共享副本更新\n", stderr="")
        manager = ServiceManager(
            (spec,), popen=Mock(return_value=process), run=Mock(return_value=completed),
            ledger_plan=lambda: next(plans), mount_share=mount,
        )
        manager._owned["http"] = process
        with patch.object(manager, "healthy", return_value=True), patch.object(
            manager, "start_missing"
        ), patch.object(manager, "wait_until_ready", return_value=True):
            ok, message = manager.sync_ledger(Path("/venv/peach"))

        self.assertTrue(ok)
        self.assertIn("共享副本更新", message)
        mount.assert_called_once_with()
        manager._run.assert_called_once()

    def test_a_share_that_will_not_mount_falls_back_to_the_clear_message(self):
        """挂不上就回到原来那条消息：菜单栏项不能卡住，服务也不该白停一次。"""
        spec = ServiceSpec("http", "http://127.0.0.1/healthz", ("peach", "serve"), True)
        process = Mock()
        process.poll.return_value = None
        runner = Mock()
        mount = Mock(return_value=False)
        manager = ServiceManager(
            (spec,), run=runner,
            ledger_plan=lambda: SyncPlan("offline", "共享副本所在的盘不可达，本地照常读写"),
            mount_share=mount,
        )
        manager._owned["http"] = process

        ok, message = manager.sync_ledger(Path("/venv/peach"))

        self.assertFalse(ok)
        self.assertIn("盘不可达", message)
        mount.assert_called_once_with()
        runner.assert_not_called()
        process.terminate.assert_not_called()

    def test_take_ownership_mounts_the_share_before_refusing(self):
        """接管同样先补挂：盘只是没挂时，`offline` 之后往往正好是可以接管的 `in-sync`。"""
        plans = iter([
            SyncPlan("offline", "共享副本所在的盘不可达，本地照常读写"),
            SyncPlan("in-sync", "两侧一致"),
        ])
        manager = ServiceManager(
            tuple(),
            run=Mock(return_value=Mock(
                returncode=0, stdout="账本同步：take-ownership\n", stderr="")),
            ledger_plan=lambda: next(plans), mount_share=Mock(return_value=True),
        )
        with patch.object(manager, "start_missing"), patch.object(
            manager, "wait_until_ready", return_value=True,
        ):
            ok, _message = manager.sync_ledger(Path("/venv/peach"), take_ownership=True)
        self.assertTrue(ok)
        self.assertIn("--take-ownership", manager._run.call_args.args[0])

    def test_a_reachable_share_is_never_remounted(self):
        """判定已经通了还去碰挂载，只是一次白跑的网络往返。"""
        mount = Mock()
        manager = ServiceManager(
            tuple(),
            run=Mock(return_value=Mock(returncode=0, stdout="ok", stderr="")),
            ledger_plan=lambda: SyncPlan("pull", "共享副本更新"), mount_share=mount,
        )
        with patch.object(manager, "start_missing"), patch.object(
            manager, "wait_until_ready", return_value=True,
        ):
            manager.sync_ledger(Path("/venv/peach"))
        mount.assert_not_called()


class SourceSyncTests(unittest.TestCase):
    """「同步开发进度」这条路径：拉到的代码要真的跑起来，托盘不能自己骗自己。"""

    def test_only_tray_owned_modules_demand_a_tray_restart(self):
        self.assertFalse(tray_restart_required(("src/peach/web.py", "docs/STATUS.md")))
        self.assertTrue(tray_restart_required(("src/peach/web.py", "src/peach/menubar.py")))
        self.assertTrue(tray_restart_required(("pyproject.toml",)))
        self.assertFalse(tray_restart_required(()))

    def test_launchd_ownership_requires_a_matching_pid_not_just_a_loaded_job(self):
        """只看「作业已加载」会在终端启动的托盘上 kickstart 出第二个菜单栏图标。"""
        loaded_elsewhere = Mock(returncode=0, stdout="\tpid = 1\n\tstate = running\n")
        self.assertFalse(launchd_owns_this_process(
            Mock(return_value=loaded_elsewhere), uid=501))

        mine = Mock(returncode=0, stdout=f"\tpid = {os.getpid()}\n\tstate = running\n")
        self.assertTrue(launchd_owns_this_process(Mock(return_value=mine), uid=501))

        self.assertFalse(launchd_owns_this_process(
            Mock(return_value=Mock(returncode=113, stdout="")), uid=501))

    def test_the_menu_lists_source_sync_next_to_the_ledger_actions(self):
        """标签和位置是语义契约：菜单只有一条，写错了没有第二处会报错。"""
        from peach import tray as tray_module

        source = inspect.getsource(tray_module.run_macos_menu_bar)
        labels = [
            line.split('"')[1]
            for line in source.splitlines()
            if line.strip().startswith('("') and '",' in line
        ]
        self.assertIn("同步开发进度", labels)
        self.assertLess(labels.index("同步开发进度"), labels.index("同步 Ledger"))
        self.assertIn("sync_source", source)

    def test_tray_restart_asks_launchd_to_kill_and_relaunch_this_label(self):
        runner = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
        restart_tray_process(runner, uid=501)
        self.assertEqual(
            runner.call_args.args[0],
            ["launchctl", "kickstart", "-k", "gui/501/gg.lmd.peach.tray"],
        )

    def test_sync_changes_restart_the_tray_and_failed_kickstart_restores_services(self):
        self.assertTrue(tray_restart_required(("src/peach/sync.py",)))
        from peach import tray as tray_module
        source = inspect.getsource(tray_module.run_macos_menu_bar)
        self.assertIn("if restarted.returncode != 0:", source)
        self.assertIn("manager.start_missing()", source)


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
