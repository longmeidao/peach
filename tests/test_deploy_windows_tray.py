from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach import __version__


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "deploy_windows_tray.py"
SPEC = importlib.util.spec_from_file_location("deploy_windows_tray", SCRIPT)
deploy_windows_tray = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = deploy_windows_tray
SPEC.loader.exec_module(deploy_windows_tray)


def git_runner(porcelain: str = "", commit: str = "abc12345def", branch: str = "master"):
    answers = {
        "status --porcelain": porcelain,
        "rev-parse HEAD": commit,
        "rev-parse --abbrev-ref HEAD": branch,
    }

    def run(command, **_kwargs):
        return subprocess.CompletedProcess(
            command, 0, stdout=answers[" ".join(command[1:])], stderr="",
        )

    return run


class DeployWindowsTrayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        # 部署入口先 resolve 检出根和目标，断言也得拿 resolve 过的路径比。
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / "dist" / "Peach" / "Peach.exe"
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"old")
        self.staged = self.root / "staging" / "Peach.exe"
        self.staged.parent.mkdir()
        self.staged.write_bytes(b"new")
        self.installer = mock.Mock()
        self.installer.log_path = self.root / "sync.log"
        self.installer.build_staged_tray.return_value = self.staged
        self.installer.packaged_migrations_pass.return_value = True
        self.restarted = mock.Mock(return_value=mock.Mock(
            ok=True, message="托盘已正常重启并重新拥有 HTTP/HTTPS 子服务",
            old_tray_pid=10, new_tray_pid=30, service_pids=(51, 52),
            backup=str(self.target.with_name("Peach.pre-source-sync-20260906-120000.exe")),
        ))

    def tearDown(self):
        self.temp.cleanup()

    def run_deploy(self, **overrides):
        arguments = dict(
            target=self.target, installer=self.installer, restart=self.restarted,
            run=git_runner(), version=lambda **_kwargs: __version__,
        )
        arguments.update(overrides)
        return deploy_windows_tray.deploy(self.root, **arguments)

    def test_a_dirty_checkout_stops_before_anything_is_built_or_swapped(self):
        outcome = self.run_deploy(run=git_runner(porcelain=" M src/peach/tray.py\n"))
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["step"], "checkout")
        self.installer.build_staged_tray.assert_not_called()
        self.restarted.assert_not_called()

    def test_a_package_that_fails_the_migration_check_never_reaches_production(self):
        self.installer.packaged_migrations_pass.return_value = False
        outcome = self.run_deploy()
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["step"], "validate")
        self.restarted.assert_not_called()
        self.assertEqual(self.target.read_bytes(), b"old")

    def test_a_given_package_is_reused_instead_of_building_again(self):
        outcome = self.run_deploy(staged=self.staged)
        self.assertTrue(outcome["ok"], outcome["message"])
        self.installer.build_staged_tray.assert_not_called()
        self.assertEqual(self.restarted.call_args.kwargs["swap_from"], self.staged)
        self.assertEqual(outcome["commit"], "abc12345def")
        self.assertEqual(outcome["version"], __version__)

    def test_a_tray_that_serves_another_version_is_reported_as_a_failure(self):
        outcome = self.run_deploy(version=lambda **_kwargs: "0.0.1")
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["step"], "verify")
        self.assertEqual(outcome["expected_version"], __version__)
        self.assertEqual(outcome["backup"], self.restarted.return_value.backup)

    def test_a_silent_health_endpoint_is_reported_as_a_failure(self):
        outcome = self.run_deploy(version=lambda **_kwargs: None)
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["step"], "verify")
        self.assertIn("/healthz", outcome["message"])


class ServingVersionTests(unittest.TestCase):
    def test_the_verdict_comes_from_the_https_port_checked_against_the_project_ca(self):
        specs = (
            mock.Mock(name="http", health_url="http://127.0.0.1/healthz", verify=True),
            mock.Mock(health_url="https://192.0.2.10/healthz", verify="/ca/peach.crt"),
        )
        specs[0].name = "http"
        specs[1].name = "https"
        response = mock.Mock(status_code=200)
        response.json.return_value = {"ok": True, "version": "9.9.9"}
        with (
            mock.patch.object(deploy_windows_tray, "build_service_specs",
                              return_value=specs),
            mock.patch.object(deploy_windows_tray.httpx, "get",
                              return_value=response) as get,
        ):
            self.assertEqual(deploy_windows_tray.serving_version(), "9.9.9")
        self.assertEqual(get.call_args.args[0], "https://192.0.2.10/healthz")
        self.assertEqual(get.call_args.kwargs["verify"], "/ca/peach.crt")
        self.assertFalse(get.call_args.kwargs["trust_env"],
                         "系统代理会替生产口回话，探测必须直连")


if __name__ == "__main__":
    unittest.main()
