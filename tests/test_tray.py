import contextlib
import importlib.util
import inspect
import io
import os
import plistlib
import re
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


from peach import appid, onboarding, settings_file
from peach import tray as tray_module
from peach.config import SECRETS_DIR
from peach.tray import (
    AlreadyRunning, PeachTray, ServiceManager, ServiceSpec, SetupGate,
    SingleInstance, apply_macos_template, build_service_specs,
    build_setup_service_specs, create_icon, enable_hidpi,
    launchd_owns_this_process, ledger_menu_items, needs_setup,
    restart_tray_process, tray_restart_required,
)
from peach.tray import main as tray_main
from peach.sync import SyncPlan
from peach.versioning import UpdateResult, VersionSnapshot
from peach.windows_update import PendingWindowsUpdate, WindowsUpdatePreparation


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
        owners = [spec for spec in specs if "--no-ledger-sync" not in spec.command
                  and "--redirect-origin" not in spec.command]
        self.assertEqual(owners, [])
        for spec in specs:
            if spec.name == "https":
                self.assertIn("--no-ledger-sync", spec.command)
                self.assertNotIn("--no-mdns", spec.command)
            else:
                self.assertIn("--redirect-origin", spec.command)

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

    本类里的账本同步用例都以「这台机器开了复制」为前提，所以显式钉住开关；
    关掉之后的行为由 `ReplicationSwitchTests` 单独验。
    """

    def setUp(self):
        patcher = patch("peach.tray.REPLICATION_ENABLED", True)
        patcher.start()
        self.addCleanup(patcher.stop)

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
        """挂不上就回到那条固定消息：菜单栏项不能卡住，服务也不该白停一次。"""
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


class ReplicationSwitchTests(unittest.TestCase):
    """ADR-0023 第 3 阶段：`replication.enabled = false` 时托盘不装配复制那一层。"""

    def items(self, enabled):
        with patch("peach.tray.REPLICATION_ENABLED", enabled):
            return ledger_menu_items(
                lambda label, action: (label, action), Mock(), Mock())

    def test_menu_items_disappear_when_replication_is_off(self):
        self.assertEqual(self.items(False), [])

    def test_menu_items_are_assembled_when_replication_is_on(self):
        labels = [label for label, _ in self.items(True)]
        self.assertEqual(labels, ["同步 Ledger", "接管 Ledger 写入"])

    def test_sync_ledger_refuses_instead_of_probing_a_share(self):
        """菜单项没了，但托盘还有别的入口；这条路径会去探一个不存在的共享。"""
        plan = Mock()
        mount = Mock()
        manager = ServiceManager(tuple(), ledger_plan=plan, mount_share=mount)
        with patch("peach.tray.REPLICATION_ENABLED", False):
            ok, message = manager.sync_ledger(Path("/venv/peach"))
        self.assertFalse(ok)
        self.assertIn("replication.enabled", message)
        plan.assert_not_called()
        mount.assert_not_called()


class SetupGateTests(unittest.TestCase):
    """首次设置期间的服务切换（ADR-0023 的 GUI 引导）。

    托盘不重启自己就要完成切换，所以这里断言的是「规格换了、日志目录和 PEACH_DATA_ROOT
    跟着换了、首扫标记只被消费一次」，而不是某个平台的菜单长什么样。
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()
        self.data_root = self.root / "peach-data"
        patcher = patch("peach.tray._peach_executable", return_value=Path("/venv/peach"))
        self.addCleanup(patcher.stop)
        patcher.start()

    def _config(self):
        return settings_file.load_config(
            project_root=self.root / "app",
            environ={"PEACH_DATA_ROOT": str(self.data_root)})

    def _tls(self, config):
        tls_dir = config.directory("secrets") / "tls"
        tls_dir.mkdir(parents=True, exist_ok=True)
        for name in ("peach-local-ca.crt", "peach.crt", "peach.key"):
            (tls_dir / name).write_text("test-only", encoding="utf-8")

    def test_a_fresh_machine_needs_setup_even_after_a_state_directory_appeared(self):
        self.assertTrue(needs_setup(self._config()))
        # 托盘的单实例锁会建出 `state/`，数据根目录于是存在、`configured` 变成 True。
        (self.data_root / "state").mkdir(parents=True)
        self.assertTrue(self._config().configured)
        self.assertTrue(needs_setup(self._config()), "空数据根不算配置过")

    def test_an_existing_deployment_without_a_settings_file_is_left_alone(self):
        (self.data_root / "database").mkdir(parents=True)
        (self.data_root / "database" / "ledger.db").write_bytes(b"")
        self.assertFalse(needs_setup(self._config()))

    def test_the_setup_service_is_loopback_only_without_tls_or_a_token(self):
        specs = build_setup_service_specs(self._config())
        self.assertEqual([spec.name for spec in specs], ["setup"])
        command = specs[0].command
        self.assertIn("--setup", command)
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "8900")
        self.assertNotIn("--ssl-certfile", command)
        self.assertNotIn("0.0.0.0", command)
        self.assertEqual(specs[0].health_url, "http://127.0.0.1:8900/healthz")

    def test_an_unconfigured_machine_starts_the_setup_service_not_the_normal_one(self):
        config = self._config()
        manager = ServiceManager(build_setup_service_specs(config),
                                 log_dir=config.directory("logs"))
        gate = SetupGate(manager, config, waiting=True, load=self._config)
        self.assertTrue(gate.waiting)
        self.assertEqual(gate.open_url(), "http://127.0.0.1:8900/")
        self.assertEqual(gate.open_label(), "重新打开设置页")
        self.assertIn("等待完成首次设置", gate.status_line())
        self.assertFalse(gate.poll(), "设置还没做完，轮询不动任何东西")
        self.assertEqual([spec.name for spec in manager.specs], ["setup"])

    def test_a_finished_setup_switches_to_the_normal_services_and_runs_the_first_scan(self):
        config = self._config()
        manager = ServiceManager(build_setup_service_specs(config),
                                 log_dir=config.directory("logs"),
                                 popen=Mock(), health_get=lambda *a, **k: Response())
        scan_popen = Mock()
        gate = SetupGate(manager, config, waiting=True, load=self._config,
                         popen=scan_popen, open_browser=Mock())
        self._tls(config)
        (self.data_root / "config.toml").write_text(
            "[server]\nport = 9100\nmdns_name = 'peach-writer'\n", encoding="utf-8")
        onboarding.request_first_scan(self._config())

        with patch("peach.tray.lan_ipv4", return_value="192.0.2.10"):
            self.assertTrue(gate.poll())
        self.assertFalse(gate.waiting)
        self.assertNotIn("setup", [spec.name for spec in manager.specs])
        self.assertTrue(manager.specs, "切换之后必须有正常服务规格")
        self.assertEqual(manager.log_dir, self.data_root / "logs")
        self.assertEqual(manager.child_environment()["PEACH_DATA_ROOT"], str(self.data_root))
        self.assertEqual(gate.open_label(), "打开 Peach")
        self.assertEqual(gate.open_url(), "https://peach-writer.local/")

        scan = scan_popen.call_args
        self.assertEqual(list(scan.args[0][1:]), ["scan", "local"])
        self.assertEqual(scan.kwargs["env"]["PEACH_DATA_ROOT"], str(self.data_root))
        # 标记只消费一次：下一轮轮询已经不在等待状态，也不会再拉起一次扫描。
        self.assertFalse(gate.poll())
        self.assertEqual(scan_popen.call_count, 1)
        self.assertIsNone(gate.start_first_scan(self._config()))

    def test_the_plain_port_redirects_to_the_name_the_setup_form_just_wrote(self):
        """明文口的跳转目标取新鲜读到的 mDNS 名，不用模块常量。

        `MDNS_HOSTNAME` 在 import 期就按当时的设置文件定型，而首次设置里那一题正是它；
        托盘不重启自己就完成切换，用常量会把人跳到一个不存在的 `.local` 名下。
        """
        config = self._config()
        manager = ServiceManager(build_setup_service_specs(config),
                                 log_dir=config.directory("logs"),
                                 popen=Mock(), health_get=lambda *a, **k: Response())
        gate = SetupGate(manager, config, waiting=True, load=self._config,
                         popen=Mock(), open_browser=Mock())
        self._tls(config)
        (self.data_root / "config.toml").write_text(
            "[server]\nport = 9100\nmdns_name = 'peach-writer'\n", encoding="utf-8")

        # 打进去的是 import 期那份旧名字；跳转目标必须是表单刚写下的那个。
        with patch("peach.tray.MDNS_HOSTNAME", "peach-reader.local"), patch(
                "peach.tray.lan_ipv4", return_value="192.0.2.10"):
            self.assertTrue(gate.poll())
        redirecting = [spec for spec in manager.specs
                       if "--redirect-origin" in spec.command]
        self.assertTrue(redirecting, "正常规格里必须有一条只做跳转的明文口")
        for spec in redirecting:
            command = spec.command
            self.assertEqual(command[command.index("--redirect-origin") + 1],
                             "https://peach-writer.local")

    def test_missing_tls_material_keeps_the_gate_waiting(self):
        """没有 openssl 的机器上 CA 生成会失败；那时不能拿一组缺文件的规格去启动。

        macOS 的规格是另一种约定：证书缺失只是不起 HTTPS，闸门照样打开，只带明文口。
        两种行为都在这里钉住，`popen` 必须是替身——闸门一开就会真的去拉起服务进程。
        """
        config = self._config()
        popen = Mock()
        manager = ServiceManager(build_setup_service_specs(config),
                                 log_dir=config.directory("logs"),
                                 popen=popen, health_get=lambda *a, **k: Response())
        gate = SetupGate(manager, config, waiting=True, load=self._config,
                         popen=Mock(), open_browser=Mock())
        self.data_root.mkdir(parents=True, exist_ok=True)
        (self.data_root / "config.toml").write_text("[server]\nport = 8900\n", encoding="utf-8")
        with patch("peach.tray.lan_ipv4", return_value="192.0.2.10"):
            opened = gate.poll()
        if sys.platform == "darwin":
            self.assertTrue(opened)
            self.assertFalse(gate.waiting)
            self.assertEqual([spec.name for spec in manager.specs], ["http"])
            return
        self.assertFalse(opened)
        self.assertTrue(gate.waiting)
        self.assertEqual([spec.name for spec in manager.specs], ["setup"])
        popen.assert_not_called()


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
        # 两个 Ledger 项由 `ledger_menu_items` 统一给出（复制关掉时为空），
        # 位置契约因此变成「同步开发进度 紧挨着那次调用之前」。
        self.assertLess(source.index("同步开发进度"), source.index("ledger_menu_items"))
        self.assertLess(source.index("ledger_menu_items"), source.index("重启服务"))
        self.assertIn("sync_source", source)

    def test_windows_tray_lists_source_sync_next_to_ledger(self):
        source = inspect.getsource(PeachTray.__init__)
        self.assertIn('MenuItem("同步开发进度", self.sync_source)', source)
        self.assertLess(source.index("同步开发进度"), source.index("ledger_menu_items"))
        self.assertLess(source.index("ledger_menu_items"), source.index("重启服务"))

    def test_windows_source_sync_tests_then_restarts_services(self):
        snapshot = VersionSnapshot("0.6.4", "master", "abc12345", False, True, "origin/master")
        completed = threading.Event()

        class Versions:
            root = ROOT

            def inspect(self):
                return snapshot

            def update(self):
                return UpdateResult(
                    "updated", "updated", snapshot, behind=1,
                    changed_paths=("docs/STATUS.md",),
                )

        class Updates:
            value = None

            def pending(self):
                return self.value

            def mark_pending(self, commit, changed_paths):
                self.value = PendingWindowsUpdate(commit, changed_paths)

            def prepare(self, _commit, _changed_paths):
                return WindowsUpdatePreparation("services", "测试通过。")

            def clear_pending(self):
                self.value = None
                completed.set()

        manager = Mock()
        manager.restart.return_value = True
        icon = Mock()
        with patch("peach.tray.pystray.Icon", return_value=Mock()):
            tray = PeachTray(manager, Versions(), Updates())
        tray.sync_source(icon)
        self.assertTrue(completed.wait(2))
        manager.restart.assert_called_once()
        manager.stop_owned.assert_not_called()

    def test_windows_source_sync_stops_services_only_after_replacer_is_ready(self):
        snapshot = VersionSnapshot("0.6.4", "master", "abc12345", False, True, "origin/master")
        stopped = threading.Event()

        class Versions:
            root = ROOT

            def inspect(self):
                return snapshot

            def update(self):
                return UpdateResult(
                    "updated", "updated", snapshot, behind=1,
                    changed_paths=("src/peach/tray.py",),
                )

        class Updates:
            value = None

            def pending(self):
                return self.value

            def mark_pending(self, commit, changed_paths):
                self.value = PendingWindowsUpdate(commit, changed_paths)

            def prepare(self, _commit, _changed_paths):
                return WindowsUpdatePreparation("replace", "替换已准备。")

        manager = Mock()
        manager.stop_owned.side_effect = lambda: stopped.set()
        icon = Mock()
        with patch("peach.tray.pystray.Icon", return_value=Mock()):
            tray = PeachTray(manager, Versions(), Updates())
        tray.sync_source(icon)
        self.assertTrue(stopped.wait(2))
        icon.stop.assert_called_once()
        manager.restart.assert_not_called()

    def test_tray_restart_asks_launchd_to_kill_and_relaunch_this_label(self):
        runner = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
        restart_tray_process(runner, uid=501)
        self.assertEqual(
            runner.call_args.args[0],
            ["launchctl", "kickstart", "-k",
             "gui/501/io.github.longmeidao.peach.tray"],
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
            self.assertNotIn("--no-mdns", command)
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


class MacIdentityTests(unittest.TestCase):
    """bundle ID、launchd 标签与 pf anchor 名只有 `peach.appid` 一个来源。

    这四处名字对不上时没有任何报错：`launchctl kickstart` 去踢一个不存在的服务、
    pf 加载一个空 anchor，表现只是菜单栏没图标、`peach.local` 不带端口打不开。
    所以每个消费者都在这里对着同一处常量核一遍。
    """

    def setUp(self):
        self.shell = (ROOT / "scripts" / "setup_macos_port80.sh").read_text(encoding="utf-8")

    def test_every_consumer_takes_the_identifier_from_peach_appid(self):
        self.assertEqual(tray_module.LAUNCH_AGENT_LABEL, appid.MACOS_LAUNCH_AGENT_LABEL)
        self.assertEqual(load_script("build_macos_app").BUNDLE_ID, appid.MACOS_BUNDLE_ID)
        self.assertEqual(load_script("build_macos_app").LABEL,
                         appid.MACOS_LAUNCH_AGENT_LABEL)
        self.assertEqual(load_script("install_macos_agent").LABEL,
                         appid.MACOS_LAUNCH_AGENT_LABEL)

    def test_the_identifier_is_the_repository_owner_not_a_private_domain(self):
        """下载者装上的东西不该带着维护者的私有域名（ADR-0023 第 4 阶段）。"""
        for value in (appid.MACOS_BUNDLE_ID, appid.MACOS_LAUNCH_AGENT_LABEL,
                      appid.MACOS_PF_ANCHOR):
            self.assertTrue(value.startswith("io.github."), value)

    def test_the_shell_script_pins_the_same_anchor_names(self):
        """POSIX shell import 不了 Python，那两行字面量只能由这条用例守住。"""
        found = dict(re.findall(r'^(ANCHOR_NAME|LEGACY_ANCHOR_NAMES)="([^"]*)"',
                                self.shell, re.MULTILINE))
        self.assertEqual(found.get("ANCHOR_NAME"), appid.MACOS_PF_ANCHOR)
        self.assertEqual(found.get("LEGACY_ANCHOR_NAMES"),
                         " ".join(appid.LEGACY_MACOS_PF_ANCHORS))

    def test_the_port_forward_script_clears_the_legacy_anchor_on_both_paths(self):
        """遗留 anchor 的那份 LaunchDaemon 每次开机都抢同一个 80/443 转发目标。"""
        self.assertIn("remove_legacy()", self.shell)
        uninstall = self.shell.split('if [ "$ACTION" = "uninstall" ]', 1)[1]
        self.assertIn("remove_legacy", uninstall)
        self.assertIn("strip_conf /etc/pf.conf", uninstall)


class MacLegacyAgentTests(unittest.TestCase):
    """装新标签之前先卸掉遗留标签的 LaunchAgent。

    `launchctl bootout` 只作用于给定的那一个 label，装新标签这一步碰不到遗留的那份：
    它会继续开机自启一个菜单栏进程，也继续占着 80/443 的转发。
    """

    def setUp(self):
        self.module = load_script("install_macos_agent")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.agents = Path(tmp.name).resolve() / "LaunchAgents"
        self.agents.mkdir()
        self.module.launch_agents_dir = lambda: self.agents
        self.calls: list[tuple[str, ...]] = []

    def _launchctl(self, *args: str, loaded: bool):
        self.calls.append(args)
        returncode = 0 if (args[0] == "print" and loaded) else 1
        return Mock(returncode=returncode, stdout="", stderr="")

    def test_installing_boots_out_the_legacy_label_and_deletes_its_plist(self):
        legacy = appid.LEGACY_MACOS_LAUNCH_AGENT_LABELS[0]
        stale = self.agents / f"{legacy}.plist"
        stale.write_bytes(b"stale")
        self.module.launchctl = lambda *args: self._launchctl(*args, loaded=True)

        self.assertEqual(self.module.remove_legacy_agents("gui/501"), [legacy])
        self.assertFalse(stale.exists())
        self.assertIn(("bootout", f"gui/501/{legacy}"), self.calls)

    def test_a_machine_without_the_legacy_label_is_left_alone(self):
        self.module.launchctl = lambda *args: self._launchctl(*args, loaded=False)
        self.assertEqual(self.module.remove_legacy_agents("gui/501"), [])
        self.assertEqual([args[0] for args in self.calls], ["print"])

    def test_install_clears_the_legacy_label_before_writing_the_new_plist(self):
        """顺序反了就会把刚装好的那份又 bootout 掉一次，白等一轮超时。"""
        source = inspect.getsource(self.module.run)
        self.assertLess(source.index("remove_legacy_agents"),
                        source.index("plistlib.dumps"))


class TrayCommandLineTests(unittest.TestCase):
    """`peach-tray` 的参数解析先于一切进程级副作用。

    新用户试探 `peach-tray --help` 时，程序不能先去拿单实例锁：那一步会在 venv 旁边
    凭空建出 `peach-data/state/`，之后的安装探测就把这台机器当成已配置。
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_dir = Path(self._tmp.name).resolve() / "state"
        for target in ("peach.tray.enable_hidpi", "peach.tray.SingleInstance",
                       "peach.tray.ServiceManager", "peach.tray.webbrowser"):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            setattr(self, target.rsplit(".", 1)[1], patcher.start())
        patcher = patch("peach.tray.STATE_DIR", self.state_dir)
        self.addCleanup(patcher.stop)
        patcher.start()

    def _run(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                tray_main(argv)
        return raised.exception.code, stdout.getvalue(), stderr.getvalue()

    def _assert_nothing_touched(self):
        self.assertFalse(self.state_dir.exists(), "帮助与参数错误不得创建状态目录")
        self.enable_hidpi.assert_not_called()
        self.SingleInstance.assert_not_called()
        self.ServiceManager.assert_not_called()
        self.webbrowser.open.assert_not_called()

    def test_help_exits_zero_and_leaves_the_state_directory_alone(self):
        code, stdout, _ = self._run(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("peach-tray", stdout)
        self.assertIn("托盘", stdout)
        self._assert_nothing_touched()

    def test_unknown_argument_exits_two_and_leaves_the_state_directory_alone(self):
        code, _, stderr = self._run(["--bogus"])
        self.assertEqual(code, 2)
        self.assertIn("--bogus", stderr)
        self._assert_nothing_touched()


if __name__ == "__main__":
    unittest.main()
