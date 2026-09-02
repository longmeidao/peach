"""`peach follow` 子命令的隔离测试：只有 check 会联网，而这里的 check 用注入的连接器。"""
import io
import sqlite3
import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach import follow_cli
from peach.cli import build_parser
from peach.follow import FollowSourceError
from peach.follow_secrets import CredentialError
from peach.follow_sources import FollowCandidate, SourceFetch
from peach.migrations import discover


ROOT = Path(__file__).resolve().parents[1]


def _fetch(**kwargs):
    base = dict(provider="rule34video", ref="lazyprocrastinator",
                request_url="https://rule34video.com/models/lazyprocrastinator/",
                semantics="work", raw_body=b"<html/>")
    base.update(kwargs)
    return SourceFetch(**base)


class FollowCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.db = self.root / "ledger.db"
        connection = sqlite3.connect(self.db)
        for migration in discover(ROOT / "migrations"):
            connection.executescript(migration.sql)
        connection.commit()
        connection.close()
        self.parser = build_parser()

    def _run(self, *argv):
        args = self.parser.parse_args([
            "follow", "--db", str(self.db),
            "--sources-root", str(self.root / "sources"),
            "--secrets-root", str(self.root / "secrets"),
            "--shared-root", str(self.root / "shared"), *argv])
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = args.handler(args)
        return code, buffer.getvalue()

    def test_creds_sees_the_shared_copy_like_the_web_surface_does(self):
        """另一台机器上配好的可同步字段，命令行这边也必须算「已配置」。

        以前只有 Web 那份仓库带上了共享根和可同步字段声明，CLI 直接
        `CredentialStore(secrets_root)`——同一份 rule34.xxx key 网页里能用、
        `peach follow check` 却报缺凭据，而错误里根本看不出是这个原因。
        """
        shared = self.root / "shared" / "secrets" / "follow"
        shared.mkdir(parents=True)
        (shared / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "sekret"}', encoding="utf-8")
        code, output = self._run("creds")
        self.assertEqual(code, 0)
        line = next(row for row in output.splitlines()
                    if row.startswith("rule34xxx"))
        self.assertIn("已配置", line)
        self.assertIn("api_key", line)
        self.assertNotIn("sekret", output, "凭据值不进任何输出")

    def test_creds_does_not_take_a_non_syncable_field_from_the_shared_copy(self):
        """f95zone 的 cookie 绑会话与客户端 IP，声明为不可同步；共享副本里有也不算。"""
        shared = self.root / "shared" / "secrets" / "follow"
        shared.mkdir(parents=True)
        (shared / "f95zone.json").write_text('{"cookie": "xf=1"}', encoding="utf-8")
        _, output = self._run("creds")
        line = next(row for row in output.splitlines() if row.startswith("f95zone"))
        self.assertIn("未配置", line)

    def test_add_derives_the_url_and_semantics_per_provider(self):
        code, output = self._run("add", "--provider", "f95zone", "--ref", "50685")
        self.assertEqual(code, 0)
        self.assertIn("release", output)
        self.assertIn("https://f95zone.to/threads/50685/", output)
        _, listing = self._run("list")
        self.assertIn("f95zone", listing)

    def test_add_defaults_work_semantics_for_per_work_sources(self):
        _, output = self._run("add", "--provider", "kemono", "--ref", "fanbox/30917150")
        self.assertIn("· work ·", output)

    def test_add_derives_official_creator_page_urls(self):
        cases = (
            ("fanbox", "ffxivinitiala", "https://ffxivinitiala.fanbox.cc/"),
            ("patreon", "sample", "https://www.patreon.com/cw/sample"),
            ("subscribestar", "subscribestar.adult/initiala",
             "https://subscribestar.adult/initiala"),
        )
        for provider, ref, expected in cases:
            _, output = self._run("add", "--provider", provider, "--ref", ref)
            self.assertIn(expected, output)

    def test_list_says_so_when_nothing_is_registered(self):
        _, output = self._run("list")
        self.assertIn("还没有登记", output)

    def test_check_records_candidates_and_classifies_them(self):
        self._run("add", "--provider", "rule34video", "--ref", "lazyprocrastinator")
        fetch = _fetch(candidates=(
            FollowCandidate(provider="rule34video", external_id="1",
                            title="Fiona - Paizuri",
                            url="https://rule34video.com/video/1/x/"),
            FollowCandidate(provider="rule34video", external_id="2",
                            title="Fiona - Paizuri (Nude)"),
        ))
        with mock.patch.object(follow_cli, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch
            code, output = self._run("check")
        self.assertEqual(code, 0)
        self.assertIn("新增 2", output)
        _, feed = self._run("feed", "--verbose")
        self.assertIn("alt/nude", feed)

    def test_check_reports_a_credential_error_without_failing_other_sources(self):
        self._run("add", "--provider", "rule34xxx", "--ref", "lazyprocrastinator")
        self._run("add", "--provider", "rule34video", "--ref", "lazyprocrastinator")

        def factory(provider, **kwargs):
            connector = mock.Mock()
            if provider == "rule34xxx":
                connector.fetch.side_effect = CredentialError("需要 user_id 与 api_key")
            else:
                connector.fetch.return_value = _fetch(candidates=(
                    FollowCandidate(provider="rule34video", external_id="1", title="A"),))
            return connector

        with mock.patch.object(follow_cli, "build_connector", factory):
            code, output = self._run("check")
        self.assertEqual(code, 1)
        self.assertIn("需要 user_id 与 api_key", output)
        self.assertIn("新增 1", output)
        _, listing = self._run("list")
        self.assertIn("unauthorized", listing)

    def test_check_records_a_source_error_and_keeps_going(self):
        self._run("add", "--provider", "rule34video", "--ref", "lazyprocrastinator")
        with mock.patch.object(follow_cli, "build_connector") as factory:
            factory.return_value.fetch.side_effect = FollowSourceError("HTTP 503")
            code, output = self._run("check")
        self.assertEqual(code, 1)
        self.assertIn("HTTP 503", output)

    def test_check_skips_disabled_sources(self):
        self._run("add", "--provider", "rule34video", "--ref", "lazyprocrastinator")
        connection = sqlite3.connect(self.db)
        connection.execute("UPDATE follow_source SET enabled=0")
        connection.commit()
        connection.close()
        with mock.patch.object(follow_cli, "build_connector") as factory:
            code, output = self._run("check")
        self.assertEqual(code, 0)
        self.assertIn("没有需要检查", output)
        factory.assert_not_called()

    def test_status_marks_items_seen(self):
        self._add_one()
        _, output = self._run("status", "1", "--to", "seen")
        self.assertIn("标记为 seen", output)
        _, feed = self._run("feed", "--status", "new")
        self.assertIn("没有符合条件", feed)

    def test_save_refuses_without_confirm(self):
        self._add_one()
        with self.assertRaises(SystemExit):
            self._run("save", "1")
        connection = sqlite3.connect(self.db)
        self.assertEqual(connection.execute("SELECT count(*) FROM asset").fetchone()[0], 0)
        connection.close()

    def test_save_with_confirm_writes_one_online_asset(self):
        self._add_one()
        code, output = self._run("save", "1", "--confirm")
        self.assertEqual(code, 0)
        self.assertIn("→ asset #1", output)
        connection = sqlite3.connect(self.db)
        row = connection.execute("SELECT location,path FROM asset").fetchone()
        connection.close()
        self.assertEqual(row, ("online", "https://rule34video.com/video/1/x/"))

    def test_creds_reports_presence_without_values(self):
        secrets = self.root / "secrets" / "follow"
        secrets.mkdir(parents=True)
        (secrets / "rule34xxx.json").write_text(
            '{"user_id": "42", "api_key": "sekret"}', encoding="utf-8")
        _, output = self._run("creds")
        self.assertIn("rule34xxx    已配置", output)
        self.assertIn("api_key", output)
        self.assertNotIn("sekret", output)

    def test_unknown_provider_is_rejected_by_the_parser(self):
        with self.assertRaises(SystemExit):
            self._run("add", "--provider", "nyaa", "--ref", "x")

    def _add_one(self):
        self._run("add", "--provider", "rule34video", "--ref", "lazyprocrastinator")
        fetch = _fetch(candidates=(
            FollowCandidate(provider="rule34video", external_id="1",
                            title="Fiona - Paizuri", duration=20.0,
                            url="https://rule34video.com/video/1/x/"),))
        with mock.patch.object(follow_cli, "build_connector") as factory:
            factory.return_value.fetch.return_value = fetch
            self._run("check")


if __name__ == "__main__":
    unittest.main()
