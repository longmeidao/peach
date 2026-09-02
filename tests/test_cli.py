"""`peach` 顶层 CLI 的可达性与只读保证。

关注子命令另有 `test_follow_cli.py`；这里管的是 `serve`/`migrate`/`status`/`ledger-sync`
这一层，以及打包后的 EXE 到底能不能调到它们——曾经调不到，见 `build_app_entry.py`。
"""
from __future__ import annotations

import importlib.util
import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from peach import cli
from peach.migrations import upgrade

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
