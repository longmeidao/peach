"""`peach` 顶层 CLI 的可达性与只读保证。

关注子命令另有 `test_follow_cli.py`；这里管的是 `serve`/`migrate`/`status`/`ledger-sync`
这一层，以及打包后的 EXE 到底能不能调到它们——曾经调不到，见 `build_app_entry.py`。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from peach import cli, settings_file
from peach.migrations import plan, upgrade

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StatusCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.db = self.root / "ledger.db"
        self.shared = self.root / "shared" / "ledger.db"
        self.state = self.root / "state"
        upgrade(self.db, MIGRATIONS)
        connection = sqlite3.connect(self.db)
        connection.executemany(
            "INSERT INTO asset(location,path,name,medium,size,duration,snapshot_path,"
            "creator,ctx_length) VALUES(?,?,?,?,?,?,?,?,?)",
            [
                ("local", r"R:\media\a.mp4", "a.mp4", "video", 2 << 30, 1800.0,
                 r"R:\snap\a.jpg", "Someone", "中"),
                ("local", r"R:\media\b.mp4", "b.mp4", "video", 1 << 30, None, None,
                 None, None),
                ("online", "https://example.test/x", "x", "account", None, None, None,
                 "Handle", None),
            ])
        connection.commit()
        connection.close()

    def _run(self, argv):
        output = io.StringIO()
        with mock.patch.object(cli, "STATE_DIR", self.state), redirect_stdout(output):
            code = cli.main(argv)
        return code, output.getvalue()

    def test_status_reports_ledger_migration_and_sync_state(self):
        code, output = self._run(["status", "--db", str(self.db),
                                  "--shared-db", str(self.shared)])
        self.assertEqual(code, 0)
        self.assertIn("合计", output)
        self.assertIn("加工进度（本机视频 2 条）", output)
        # 在线资产不进「加工进度」的分母，否则百分比永远到不了 100。
        self.assertIn("有时长 (ffprobe)", output)
        self.assertIn("1 / 2", output)
        self.assertIn("待应用 0 个", output)
        self.assertIn("同步：", output)

    def test_status_never_writes_the_ledger_or_invents_a_device_id(self):
        before = self.db.stat().st_mtime_ns, self.db.stat().st_size
        code, _ = self._run(["status", "--db", str(self.db),
                             "--shared-db", str(self.shared)])
        self.assertEqual(code, 0)
        self.assertEqual((self.db.stat().st_mtime_ns, self.db.stat().st_size), before)
        self.assertFalse((self.state / "device-id").exists(),
                         "状态命令不该顺手生成一个从没写过库的写入端标识")

    def test_missing_ledger_is_reported_rather_than_created(self):
        missing = self.root / "nope.db"
        code, output = self._run(["status", "--db", str(missing),
                                  "--shared-db", str(self.shared)])
        self.assertEqual(code, 4)
        self.assertIn("账本不存在", output)
        self.assertFalse(missing.exists())


class InitCommandTests(unittest.TestCase):
    """`peach init`：一台全新机器从零到能跑的唯一入口。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / "peach-data"
        # 证书生成要调 openssl；那是 `test_certs.py` 的事，这里只验初始化流程。
        patcher = mock.patch.object(cli.certs, "bootstrap_certificates")
        self.certs = patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli.main(argv)
        return code, output.getvalue()

    def _init(self, *extra):
        return self._run(["init", "--data-root", str(self.root), *extra])

    def test_fresh_init_builds_a_runnable_data_root(self):
        code, output = self._init()
        self.assertEqual(code, 0)
        for key in settings_file.DIRECTORY_KEYS:
            self.assertTrue((self.root / key).is_dir(), key)
        database = self.root / "database" / "ledger.db"
        self.assertTrue(database.is_file())
        # 建完就必须是最新 schema，否则第一次 serve 就撞上待应用迁移。
        self.assertEqual(plan(database, MIGRATIONS)[1], [])
        self.assertIn("下一步", output)
        self.certs.assert_called_once()

    def test_fresh_init_output_is_readable_by_the_settings_layer(self):
        self._init("--mdns-name", "peach-two", "--port", "9443",
                   "--mount", "local=/mnt/media")
        loaded = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(self.root)})
        self.assertTrue(loaded.present)
        self.assertTrue(loaded.configured)
        self.assertEqual(loaded.server.mdns_name, "peach-two")
        self.assertEqual(loaded.server.port, 9443)
        self.assertEqual(loaded.mounts, {"local": "/mnt/media"})
        # 全新机器不开复制：单机用户不该凭空多出一条同步路径。
        self.assertFalse(loaded.replication.enabled)

    def test_mount_for_an_undeclared_location_is_refused(self):
        """打错来源 ID 静默收下，那个来源就会安静地进脱盘模式。"""
        with self.assertRaises(SystemExit) as caught:
            self._init("--mount", "locla=/mnt/media")
        self.assertIn("locla", str(caught.exception))
        self.assertIn("local", str(caught.exception))

    def test_mount_without_an_equals_sign_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self._init("--mount", "/mnt/media")
        self.assertIn("来源ID=路径", str(caught.exception))

    def test_mount_ids_keep_their_case(self):
        """来源 ID 不是盘符，`local` 不能被改写成 `LOCAL`。"""
        self.assertEqual(
            cli._parse_mounts(["local=/mnt/res"], {"local": r"R:\media"}),
            {"local": "/mnt/res"})

    def test_the_new_ledger_is_readable_by_status(self):
        self._init()
        code, output = self._run(
            ["status", "--db", str(self.root / "database" / "ledger.db"),
             "--shared-db", str(self.root / "nope.db")])
        self.assertEqual(code, 0)
        self.assertIn("待应用 0 个", output)

    def test_existing_settings_file_is_not_overwritten_without_force(self):
        self._init()
        stamp = (self.root / "config.toml").read_text(encoding="utf-8")
        code, output = self._init("--mdns-name", "changed")
        self.assertEqual(code, 3)
        self.assertIn("已存在", output)
        self.assertEqual((self.root / "config.toml").read_text(encoding="utf-8"), stamp)
        self.assertEqual(self._init("--mdns-name", "changed", "--force")[0], 0)
        self.assertNotEqual(
            (self.root / "config.toml").read_text(encoding="utf-8"), stamp)

    def test_from_existing_only_writes_the_settings_file(self):
        code, _ = self._init("--from-existing", "--smb-host", "other.local",
                             "--smb-user", "someone")
        self.assertEqual(code, 0)
        self.assertFalse((self.root / "database").exists())
        self.assertFalse((self.root / "generated").exists())
        self.certs.assert_not_called()
        loaded = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(self.root)})
        # 现有部署本来就在复制；写一份设置文件不该把它悄悄关掉。
        self.assertTrue(loaded.replication.enabled)
        self.assertEqual(loaded.replication.smb_host, "other.local")
        self.assertEqual(loaded.replication.smb_user, "someone")

    def test_from_existing_says_so_when_the_old_file_is_unreadable(self):
        """升级路径上最贵的一次静默：第一阶段的 `[media] R = ...` 现在是硬错误。

        `--from-existing` 声称落盘的是「当前生效的配置」，而旧文件读不出来时那份配置
        其实是内建默认。不说这一句，重写出来的文件会安静地丢掉 mDNS 名和 SMB 坐标。
        """
        self.root.mkdir(parents=True)
        (self.root / "config.toml").write_text(
            "[media]\nR = '/Volumes/RESOURCES'\n", encoding="utf-8")
        code, output = self._init("--from-existing", "--force")
        self.assertEqual(code, 0)
        self.assertIn("media.mounts", output)      # 原始错误里的升级提示
        self.assertIn("没有**继承", output)
        loaded = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(self.root)})
        self.assertEqual(loaded.mounts, {})

    def test_blank_coordinates_are_listed_instead_of_guessed(self):
        _, output = self._init("--from-existing")
        self.assertIn("replication.smb_host", output)
        self.assertIn("--smb-host", output)

    def test_an_existing_ledger_is_never_rebuilt_by_a_fresh_init(self):
        database = self.root / "database" / "ledger.db"
        database.parent.mkdir(parents=True)
        database.write_bytes(b"not really a database")
        code, output = self._init()
        self.assertEqual(code, 0)
        self.assertEqual(database.read_bytes(), b"not really a database")
        self.assertIn("--from-existing", output)


class ReplicationAssemblyTests(unittest.TestCase):
    """ADR-0023 第 3 阶段：整条复制链路按 `replication.enabled` 装配或完全不装配。"""

    def _build(self, enabled):
        args = argparse.Namespace(shared_db=Path("/nonexistent/shared.db"))
        settings = mock.Mock(db_path=Path("/nonexistent/local.db"))
        output = io.StringIO()
        with mock.patch.object(cli, "REPLICATION_ENABLED", enabled), \
                mock.patch.object(cli, "LedgerSync") as ledger_sync, \
                redirect_stdout(output):
            sync = cli._build_sync(args, settings)
        return sync, ledger_sync, output.getvalue()

    def test_replication_off_builds_no_observer_and_probes_nothing(self):
        """没有第二台机器就没有「读者」：服务按独立写者跑，写接口照常开。"""
        sync, ledger_sync, output = self._build(False)
        self.assertIsNone(sync)
        ledger_sync.assert_not_called()
        self.assertIn("disabled", output)

    def test_replication_on_keeps_todays_behaviour(self):
        sync, ledger_sync, _ = self._build(True)
        ledger_sync.assert_called_once()
        ledger_sync.return_value.observe.assert_called_once()
        self.assertIs(sync, ledger_sync.return_value)


class BrokenSettingsTests(unittest.TestCase):
    """设置文件读不出来时，命令必须响亮地失败，而不是拿默认值跑出个假状态。"""

    def test_commands_refuse_to_run_and_name_the_file(self):
        broken = settings_file.SettingsFileError(
            "设置文件读不出来：/tmp/peach-data/config.toml：TOML 语法错误")
        with mock.patch.object(cli, "SETTINGS_ERROR", broken):
            with self.assertRaises(SystemExit) as caught:
                cli.main(["status", "--db", "/tmp/nope.db"])
        message = str(caught.exception)
        self.assertIn("config.toml", message)
        self.assertIn("peach init --force", message)


class PackagedEntryTests(unittest.TestCase):
    """打包后的 EXE 必须能调到 `peach.cli` 的每一个子命令。

    原来的判据是硬编码的 `{"serve", "migrate"}`，于是 `follow`、`ledger-sync` 和新增的
    `status` 在 EXE 里全部不可达——参数被当成托盘参数吞掉，既不报错也不执行。
    """

    @classmethod
    def setUpClass(cls):
        cls.entry = load_script("build_app_entry")

    def test_every_cli_subcommand_is_reachable_from_the_packaged_entry(self):
        subcommands = set()
        for action in cli.build_parser()._subparsers._group_actions:
            subcommands.update(action.choices)
        self.assertIn("status", subcommands)
        self.assertIn("follow", subcommands)
        self.assertEqual(subcommands, self.entry.cli_commands())

    def test_tray_still_starts_when_the_first_argument_is_not_a_subcommand(self):
        self.assertFalse(self.entry.wants_cli(["peach.exe"]))
        self.assertFalse(self.entry.wants_cli(["peach.exe", "--tray-only"]))
        self.assertTrue(self.entry.wants_cli(["peach.exe", "status"]))
        self.assertTrue(self.entry.wants_cli(["peach.exe", "ledger-sync"]))


if __name__ == "__main__":
    unittest.main()
