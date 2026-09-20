import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from peach import access, routes_auth, routes_configuration, tunnel


class _Config:
    def __init__(self, root: Path, *, port: int = 8900, binary: str = ""):
        self.data_root = root
        self.server = SimpleNamespace(port=port, mdns_name="peach")
        self.tunnel = SimpleNamespace(binary=binary)

    def directory(self, name: str) -> Path:
        return self.data_root / name


class _Stream:
    def __init__(self, *lines: str):
        self._lines = iter(lines)
        self.closed = False

    def readline(self):
        try:
            return next(self._lines)
        except StopIteration:
            return ""

    def close(self):
        self.closed = True


class _Process:
    def __init__(self, stream, pid: int = 4123):
        self.stdout = stream
        self.pid = pid
        self._returncode = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self._returncode

    def terminate(self):
        self.terminated = True
        self._returncode = 0

    def kill(self):
        self.killed = True
        self._returncode = -9

    def wait(self, timeout=None):
        if self._returncode is None:
            self._returncode = 0
        return self._returncode


class TunnelPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.binary = self.root / "cloudflared.exe"
        self.binary.write_bytes(b"fake")
        self.config = _Config(self.root, binary=str(self.binary))
        self.access_path = self.root / "secrets" / "access.json"
        access.save(self.access_path, "a-strong-test-password")

    def tearDown(self):
        self.temp.cleanup()

    def test_quick_url_extraction_rejects_non_cloudflare_urls(self):
        self.assertEqual(
            tunnel.extract_quick_url(
                "INF | https://AbC-123.trycloudflare.com. connected"
            ),
            "https://AbC-123.trycloudflare.com",
        )
        self.assertIsNone(tunnel.extract_quick_url("https://example.com/trycloudflare.com"))

    def test_standalone_uses_loopback_http_without_tls_options(self):
        plan = tunnel.plan_for_config(
            self.config, access_path=self.access_path, token="internal-token",
            standalone_mode=True,
        )
        self.assertEqual(plan.origin.url, "http://127.0.0.1:8900")
        self.assertNotIn("--origin-server-name", plan.command)
        self.assertNotIn("--origin-ca-pool", plan.command)

    def test_standalone_uses_the_actual_runtime_port_when_supplied(self):
        plan = tunnel.plan_for_config(
            self.config, access_path=self.access_path, token="internal-token",
            standalone_mode=True, https_port=18901,
        )
        self.assertEqual(plan.origin.url, "http://127.0.0.1:18901")

    def test_source_uses_lan_https_and_project_ca(self):
        ca = self.config.directory("secrets") / "tls" / "peach-local-ca.crt"
        ca.parent.mkdir(parents=True)
        ca.write_bytes(b"ca")
        plan = tunnel.plan_for_config(
            self.config, access_path=self.access_path, token="internal-token",
            standalone_mode=False, lan_address="192.0.2.162",
        )
        self.assertEqual(plan.origin.url, "https://192.0.2.162:443")
        self.assertEqual(plan.origin.origin_server_name, "peach.local")
        self.assertIn(("--origin-ca-pool", str(ca)), tuple(zip(plan.command, plan.command[1:])))

    def test_source_can_use_a_nonstandard_https_port(self):
        ca = self.config.directory("secrets") / "tls" / "peach-local-ca.crt"
        ca.parent.mkdir(parents=True)
        ca.write_bytes(b"ca")
        origin = tunnel.origin_for_config(
            self.config, standalone_mode=False, lan_address="192.0.2.162",
            https_port=8443,
        )
        self.assertEqual(origin.url, "https://192.0.2.162:8443")

    def test_source_ipv6_origin_is_bracketed(self):
        ca = self.config.directory("secrets") / "tls" / "peach-local-ca.crt"
        ca.parent.mkdir(parents=True)
        ca.write_bytes(b"ca")
        origin = tunnel.origin_for_config(
            self.config, standalone_mode=False, lan_address="2001:db8::5",
        )
        self.assertEqual(origin.url, "https://[2001:db8::5]:443")

    def test_source_without_tls_is_rejected_before_starting_a_tunnel(self):
        with self.assertRaisesRegex(tunnel.TunnelError, "需要正在运行的 HTTPS"):
            tunnel.plan_for_config(
                self.config, access_path=self.access_path, token="internal-token",
                standalone_mode=False, lan_address="192.0.2.162",
                tls_enabled=False,
            )

    def test_open_access_and_missing_token_are_rejected_before_binary_lookup(self):
        access.save(self.access_path, "")
        with self.assertRaisesRegex(tunnel.TunnelError, "访问密码"):
            tunnel.plan_for_config(
                self.config, access_path=self.access_path, token="internal-token",
                standalone_mode=True,
            )
        access.save(self.access_path, "a-strong-test-password")
        with self.assertRaisesRegex(tunnel.TunnelError, "内部访问令牌"):
            tunnel.plan_for_config(
                self.config, access_path=self.access_path, token="",
                standalone_mode=True,
            )

    def test_missing_binary_is_rejected(self):
        self.binary.unlink()
        self.config.tunnel.binary = str(self.root / "missing.exe")
        with self.assertRaisesRegex(tunnel.TunnelError, "找不到 cloudflared"):
            tunnel.plan_for_config(
                self.config, access_path=self.access_path, token="internal-token",
                standalone_mode=True, environ={}, which=lambda _name: None,
            )


class TunnelManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.processes = []

    def tearDown(self):
        self.temp.cleanup()

    def popen(self, command, **kwargs):
        pid_index = command.index("--pidfile") + 1
        Path(command[pid_index]).write_text("4123\n", encoding="ascii")
        process = _Process(_Stream("INF | Your quick Tunnel has been created! https://unit-7.trycloudflare.com\n"))
        self.processes.append(process)
        return process

    def plan(self):
        return tunnel.TunnelPlan(
            binary=self.root / "cloudflared.exe",
            origin=tunnel.TunnelOrigin("http://127.0.0.1:8900"),
            command=("cloudflared", "tunnel", "--url", "http://127.0.0.1:8900"),
        )

    def test_start_writes_url_and_stop_removes_state(self):
        manager = tunnel.TunnelManager(
            self.root / "state", self.root / "logs", popen=self.popen, wait_timeout=2,
        )
        started = manager.start(self.plan())
        self.assertEqual(started.state, "running")
        self.assertEqual(started.url, "https://unit-7.trycloudflare.com")
        state = json.loads((self.root / "state" / tunnel.STATE_FILENAME).read_text())
        self.assertEqual(state["url"], started.url)
        self.assertIn(started.url, (self.root / "logs" / tunnel.LOG_FILENAME).read_text())
        stopped = manager.stop()
        self.assertEqual(stopped.state, "stopped")
        self.assertFalse((self.root / "state" / tunnel.STATE_FILENAME).exists())
        self.assertTrue(self.processes[0].terminated)

    def test_child_exit_after_start_is_reported_as_error(self):
        manager = tunnel.TunnelManager(
            self.root / "state", self.root / "logs", popen=self.popen, wait_timeout=2,
        )
        manager.start(self.plan())
        self.processes[0]._returncode = 1
        snapshot = manager.snapshot()
        self.assertEqual(snapshot.state, "error")
        self.assertEqual(snapshot.url, "https://unit-7.trycloudflare.com")

    def test_saved_running_state_is_not_reused_after_restart(self):
        state_dir = self.root / "state"
        state_dir.mkdir()
        (state_dir / tunnel.STATE_FILENAME).write_text(
            json.dumps({"state": "running", "url": "https://old.trycloudflare.com"}),
            encoding="utf-8",
        )
        snapshot = tunnel.saved_snapshot(state_dir)
        self.assertEqual(snapshot.state, "stopped")
        self.assertIn("上一次", snapshot.error)

    def test_missing_state_file_is_a_clean_stopped_snapshot(self):
        snapshot = tunnel.saved_snapshot(self.root / "state")
        self.assertEqual(snapshot.state, "stopped")
        self.assertEqual(snapshot.error, "")

    def test_corrupt_state_file_remains_an_error(self):
        state_dir = self.root / "state"
        state_dir.mkdir()
        (state_dir / tunnel.STATE_FILENAME).write_text("{", encoding="utf-8")
        snapshot = tunnel.saved_snapshot(state_dir)
        self.assertEqual(snapshot.state, "stopped")
        self.assertEqual(snapshot.error, "Tunnel 状态文件不可读")

    def test_pidfile_for_another_process_does_not_mark_tunnel_ready(self):
        manager = tunnel.TunnelManager(
            self.root / "state", self.root / "logs", popen=self.popen, wait_timeout=0.05,
        )
        original = self.popen

        def mismatched_popen(command, **kwargs):
            process = original(command, **kwargs)
            Path(command[command.index("--pidfile") + 1]).write_text("9999\n", encoding="ascii")
            return process

        manager._popen = mismatched_popen
        with self.assertRaisesRegex(tunnel.TunnelError, "连接到 Cloudflare"):
            manager.start(self.plan())
        self.assertTrue(self.processes[0].terminated)
        self.assertFalse((self.root / "state" / tunnel.PID_FILENAME).exists())

    def test_snapshot_accepts_a_process_without_a_pid_attribute(self):
        process = SimpleNamespace(poll=lambda: None, stdout=_Stream())
        manager = tunnel.TunnelManager(self.root / "state", self.root / "logs")
        manager._process = process
        snapshot = manager.snapshot()
        self.assertEqual(snapshot.state, "starting")
        self.assertIsNone(snapshot.pid)


class TunnelOriginGuardTests(unittest.TestCase):
    def request(self, origin: str):
        manager = SimpleNamespace(snapshot=lambda: tunnel.TunnelSnapshot(
            state="running", url="https://unit-7.trycloudflare.com",
        ))
        app = SimpleNamespace(state=SimpleNamespace(tunnel=manager))
        return SimpleNamespace(
            app=app,
            headers={"origin": origin},
            base_url="http://127.0.0.1:8900/",
        )

    def test_current_quick_tunnel_origin_is_allowed_for_write_requests(self):
        routes_auth.same_origin(self.request("https://unit-7.trycloudflare.com"))

    def test_regular_local_origin_is_still_allowed(self):
        routes_auth.same_origin(self.request("http://127.0.0.1:8900/"))

    def test_other_origin_is_rejected_even_when_it_looks_like_a_tunnel(self):
        with self.assertRaises(HTTPException) as raised:
            routes_auth.same_origin(self.request("https://other.trycloudflare.com"))
        self.assertEqual(raised.exception.status_code, 403)


class TunnelRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.config_path = self.root / "config.toml"
        self.config_path.write_text("[tunnel]\nenabled = false\n", encoding="utf-8")
        self.config = SimpleNamespace(
            present=True, path=self.config_path,
            tunnel=SimpleNamespace(enabled=False, binary=""),
            data_root=self.root,
        )
        self.settings = SimpleNamespace(
            access_path=self.root / "access.json", token="internal-token",
            tunnel_standalone=True, tunnel_lan_address=None, tunnel_origin_port=443,
        )
        self.plan = tunnel.TunnelPlan(
            binary=self.root / "cloudflared.exe",
            origin=tunnel.TunnelOrigin("http://127.0.0.1:8900"),
            command=("cloudflared", "tunnel", "--url", "http://127.0.0.1:8900"),
        )

    def tearDown(self):
        self.temp.cleanup()

    def request(self, manager):
        state = SimpleNamespace(tunnel=manager, settings=self.settings)
        return SimpleNamespace(
            app=SimpleNamespace(state=state),
            client=SimpleNamespace(host="127.0.0.1"),
            scope={"server": ("127.0.0.1", 8900)},
            url=SimpleNamespace(hostname="127.0.0.1"),
            headers={"origin": "http://127.0.0.1:8900"},
            base_url="http://127.0.0.1:8900/",
        )

    def manager(self, state="stopped"):
        manager = mock.Mock()
        manager.snapshot.return_value = tunnel.TunnelSnapshot(state=state)
        manager.start.return_value = tunnel.TunnelSnapshot(
            state="running", url="https://unit-7.trycloudflare.com", pid=4123,
        )
        manager.stop.return_value = tunnel.TunnelSnapshot(state="stopped")
        return manager

    def patches(self, current=None):
        current = current or self.config
        return mock.patch.multiple(
            routes_configuration.settings_file,
            load_config=mock.Mock(side_effect=[self.config, current]),
            write=mock.Mock(),
        )

    def test_enable_starts_and_persists_the_tunnel(self):
        manager = self.manager()
        with self.patches(), mock.patch.object(routes_configuration, "revision", return_value="rev"), \
                mock.patch.object(routes_configuration.tunnel, "plan_for_config", return_value=self.plan), \
                mock.patch.object(routes_configuration, "FileLock") as lock, \
                mock.patch.object(routes_configuration, "replace", return_value=self.config):
            lock.return_value.__enter__.return_value = lock.return_value
            result = routes_configuration.save_tunnel(
                self.request(manager), {"revision": "rev", "enabled": True}, None,
            )
        self.assertEqual(result["state"], "running")
        manager.start.assert_called_once_with(self.plan)
        manager.stop.assert_not_called()

    def test_stale_revision_rolls_back_only_a_tunnel_started_by_this_request(self):
        manager = self.manager()
        with self.patches(current=SimpleNamespace(path=self.config_path)), \
                mock.patch.object(routes_configuration, "revision", side_effect=["rev", "changed", "rev"]), \
                mock.patch.object(routes_configuration.tunnel, "plan_for_config", return_value=self.plan), \
                mock.patch.object(routes_configuration, "FileLock") as lock, \
                mock.patch.object(routes_configuration, "replace", return_value=self.config):
            lock.return_value.__enter__.return_value = lock.return_value
            with self.assertRaises(HTTPException) as raised:
                routes_configuration.save_tunnel(
                    self.request(manager), {"revision": "rev", "enabled": True}, None,
                )
        self.assertEqual(raised.exception.status_code, 409)
        manager.stop.assert_called_once_with()

    def test_stale_revision_does_not_stop_an_existing_tunnel(self):
        manager = self.manager(state="running")
        with self.patches(current=SimpleNamespace(path=self.config_path)), \
                mock.patch.object(routes_configuration, "revision", side_effect=["rev", "changed", "rev"]), \
                mock.patch.object(routes_configuration.tunnel, "plan_for_config", return_value=self.plan), \
                mock.patch.object(routes_configuration, "FileLock") as lock, \
                mock.patch.object(routes_configuration, "replace", return_value=self.config):
            lock.return_value.__enter__.return_value = lock.return_value
            with self.assertRaises(HTTPException):
                routes_configuration.save_tunnel(
                    self.request(manager), {"revision": "rev", "enabled": True}, None,
                )
        manager.stop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
