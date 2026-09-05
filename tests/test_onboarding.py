"""`peach.onboarding`：首次运行问答的题目、校验与落盘，纯逻辑、可注入。

CLI 与将来的托盘设置页共用这一层，所以这里只用脚本化答案驱动，不碰 stdin；平台由
`windows=` 注入。只有一处例外：媒体目录题要收一个真实存在的目录，而那个目录是不是盘符
路径由测试机决定，所以走到这道题的用例按 `NATIVE_WINDOWS` 用本机形态。
"""
from __future__ import annotations

import importlib.util
import io
import os
import sqlite3
import tempfile
import unittest
from html import escape
from pathlib import Path
from unittest import mock

from peach import onboarding, settings_file

NATIVE_WINDOWS = os.name == "nt"
HAS_HTTP_DEPS = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))


def scripted(*answers: str):
    """按顺序吐答案，并把每一题的题目与默认值记下来。"""
    queue = list(answers)
    seen: list[tuple[str, str]] = []

    def ask(prompt: str, default: str) -> str:
        seen.append((prompt, default))
        return queue.pop(0)

    ask.seen = seen  # type: ignore[attr-defined]
    return ask


class _Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.media = self.root / "media"
        self.media.mkdir()
        self.config = settings_file.load_config(
            project_root=self.root / "app", environ={"PEACH_DATA_ROOT": str(self.root / "peach-data")})


class QuestionTests(_Case):
    def test_questions_come_in_a_fixed_order_with_defaults_from_the_config(self):
        asked = onboarding.questions(self.config, windows=True, home=self.home)
        self.assertEqual([q.key for q in asked],
                         ["data_root", "media_dir", "host", "port", "mdns_name"])
        by_key = {q.key: q for q in asked}
        self.assertEqual(by_key["data_root"].default, str(self.root / "peach-data"))
        self.assertEqual(by_key["host"].default, "2")
        self.assertEqual(by_key["port"].default, "8900")
        self.assertEqual(by_key["mdns_name"].default, "peach")

    def test_media_default_is_the_system_video_folder_only_when_it_exists(self):
        self.assertIsNone(onboarding.default_media_dir(self.home, windows=True))
        (self.home / "Videos").mkdir()
        self.assertEqual(onboarding.default_media_dir(self.home, windows=True),
                         self.home / "Videos")
        self.assertIsNone(onboarding.default_media_dir(self.home, windows=False))
        (self.home / "Movies").mkdir()
        self.assertEqual(onboarding.default_media_dir(self.home, windows=False),
                         self.home / "Movies")
        asked = {q.key: q for q in onboarding.questions(self.config, windows=False, home=self.home)}
        self.assertEqual(asked["media_dir"].default, str(self.home / "Movies"))


class ValidatorTests(_Case):
    def test_media_dir_must_already_exist_and_is_never_created(self):
        validate = onboarding.media_dir_validator(windows=False)
        missing = self.root / "nope"
        with self.assertRaises(ValueError) as caught:
            validate(str(missing))
        self.assertIn("不存在", str(caught.exception))
        self.assertFalse(missing.exists())
        with self.assertRaises(ValueError):
            validate("")
        self.assertEqual(validate(str(self.media)), self.media)

    def test_host_accepts_the_two_choices_in_several_spellings(self):
        for raw in ("1", "本机", "127.0.0.1"):
            self.assertEqual(onboarding.validate_host(raw), "127.0.0.1")
        for raw in ("2", "局域网", "0.0.0.0"):
            self.assertEqual(onboarding.validate_host(raw), "0.0.0.0")
        with self.assertRaises(ValueError):
            onboarding.validate_host("3")

    def test_port_is_an_integer_in_range(self):
        self.assertEqual(onboarding.validate_port(" 8900 "), 8900)
        for raw in ("0", "65536", "abc", ""):
            with self.assertRaises(ValueError):
                onboarding.validate_port(raw)

    def test_mdns_name_is_a_dns_label(self):
        self.assertEqual(onboarding.validate_mdns_name("peach-two"), "peach-two")
        for raw in ("", "-peach", "peach.local", "pea ch"):
            with self.assertRaises(ValueError):
                onboarding.validate_mdns_name(raw)

    def test_yes_no_defaults_to_yes(self):
        for raw in ("", "y", "Yes", "是"):
            self.assertTrue(onboarding.validate_yes_no(raw))
        for raw in ("n", "NO", "否"):
            self.assertFalse(onboarding.validate_yes_no(raw))
        with self.assertRaises(ValueError):
            onboarding.validate_yes_no("maybe")

    def test_data_root_may_not_exist_yet_but_may_not_be_a_file(self):
        self.assertEqual(onboarding.validate_data_root(str(self.root / "new")), self.root / "new")
        (self.root / "file").write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError):
            onboarding.validate_data_root(str(self.root / "file"))


class AskUntilValidTests(_Case):
    def test_empty_input_takes_the_default(self):
        question = onboarding.Question("port", "服务端口", "8900", onboarding.validate_port)
        self.assertEqual(onboarding.ask_until_valid(question, scripted(""), report=lambda _: None), 8900)

    def test_invalid_answers_are_reported_and_reasked_up_to_the_limit(self):
        question = onboarding.Question("port", "服务端口", "8900", onboarding.validate_port)
        reported: list[str] = []
        value = onboarding.ask_until_valid(question, scripted("x", "y", "9000"), report=reported.append)
        self.assertEqual(value, 9000)
        self.assertEqual(len(reported), 2)
        self.assertIn("还可以再试 2 次", reported[0])
        with self.assertRaises(onboarding.OnboardingAborted) as caught:
            onboarding.ask_until_valid(question, scripted("x", "y", "z"), report=lambda _: None)
        self.assertIn("服务端口", str(caught.exception))
        self.assertIn("3 次", str(caught.exception))


class ConfigureTests(_Case):
    def _answers(self, **overrides):
        base = dict(data_root=self.root / "peach-data", media_dir=self.media,
                    host="127.0.0.1", port=8900, mdns_name="peach")
        base.update(overrides)
        return onboarding.Answers(**base)

    def test_windows_declares_the_directory_itself_and_leaves_mounts_empty(self):
        prepared = onboarding.configure(self.config, self._answers(), windows=True)
        self.assertEqual(prepared.locations, {"local": str(self.media)})
        self.assertEqual(prepared.mounts, {})
        self.assertEqual(onboarding.scan_root(prepared), str(self.media))

    def test_posix_keeps_the_ledger_shape_and_mounts_the_directory(self):
        prepared = onboarding.configure(self.config, self._answers(), windows=False)
        self.assertEqual(prepared.locations, {"local": r"R:\media"})
        self.assertEqual(prepared.mounts, {"local": str(self.media)})
        self.assertEqual(onboarding.scan_root(prepared), r"R:\media")
        self.assertIn(str(self.media), onboarding.mounts_explanation(self.media))

    def test_only_the_asked_settings_change_and_replication_stays_off(self):
        prepared = onboarding.configure(
            self.config, self._answers(host="0.0.0.0", port=9443, mdns_name="peach-two"), windows=True)
        self.assertEqual((prepared.server.host, prepared.server.port, prepared.server.mdns_name),
                         ("0.0.0.0", 9443, "peach-two"))
        self.assertFalse(prepared.replication.enabled)
        self.assertEqual(prepared.server.review_writer_origin, "")
        self.assertEqual(prepared.replication.smb_host, "")
        self.assertEqual(set(prepared.directories), set(settings_file.DIRECTORY_KEYS))

    def test_the_written_file_reads_back_with_only_the_declared_source(self):
        """`[media.locations]` 里只有 local：内建默认的示例盘符不得从旁边混进来。"""
        prepared = onboarding.configure(self.config, self._answers(), windows=True)
        settings_file.write(prepared)
        loaded = settings_file.load_config(
            project_root=self.root / "app", environ={"PEACH_DATA_ROOT": str(self.root / "peach-data")})
        self.assertTrue(loaded.present)
        self.assertEqual(loaded.locations, {"local": str(self.media)})
        self.assertEqual(loaded.mounts, {})
        self.assertFalse(loaded.replication.enabled)


class InterviewTests(_Case):
    def test_scripted_answers_drive_the_whole_interview(self):
        ask = scripted("", str(self.media), "2", "", "peach-two")
        answers = onboarding.interview(self.config, ask, windows=NATIVE_WINDOWS, home=self.home,
                                       report=lambda _: None)
        self.assertEqual(answers, onboarding.Answers(
            data_root=self.root / "peach-data", media_dir=self.media, host="0.0.0.0",
            port=8900, mdns_name="peach-two"))
        self.assertEqual([prompt for prompt, _ in ask.seen], [
            "数据目录（Peach 数据库、缓存和设置文件都放在这里）",
            "媒体文件夹（必须已经存在，可以在外置硬盘上）",
            "谁可以访问：1 = 只有这台电脑，2 = 同一局域网的设备",
            "端口",
            "局域网访问地址（<名字>.local，只在允许局域网访问时发布）",
        ])

    def test_console_ask_shows_the_default_and_treats_eof_as_abort(self):
        with mock.patch("builtins.input", return_value="x") as prompt:
            self.assertEqual(onboarding.console_ask("服务端口", "8900"), "x")
        prompt.assert_called_once_with("服务端口 [8900]: ")
        with mock.patch("builtins.input", return_value="") as prompt:
            onboarding.console_ask("本地媒体目录", "")
        prompt.assert_called_once_with("本地媒体目录（必填）: ")
        with mock.patch("builtins.input", side_effect=EOFError):
            with self.assertRaises(onboarding.OnboardingAborted):
                onboarding.console_ask("服务端口", "8900")

    def test_only_a_real_terminal_counts_as_interactive(self):
        self.assertFalse(onboarding.is_interactive(io.StringIO()))
        self.assertFalse(onboarding.is_interactive(None))
        self.assertTrue(onboarding.is_interactive(mock.Mock(isatty=lambda: True)))


class ApplyTests(_Case):
    """`apply()` 是 CLI 问答与设置页共用的落盘入口。"""

    def setUp(self):
        super().setUp()
        (self.media / "sub").mkdir()
        (self.media / "sub" / "a.mp4").write_bytes(b"0" * 10)
        patcher = mock.patch.object(onboarding.certs, "bootstrap_certificates")
        self.certs = patcher.start()
        self.certs.return_value.ca_cert = self.root / "peach-data" / "secrets" / "tls" / "ca.crt"
        self.addCleanup(patcher.stop)

    def _answers(self, **overrides):
        base = dict(data_root=self.root / "peach-data", media_dir=self.media,
                    host="127.0.0.1", port=8900, mdns_name="peach")
        base.update(overrides)
        return onboarding.Answers(**base)

    def test_apply_builds_the_whole_tree_and_writes_the_settings_file(self):
        applied = onboarding.apply(self.config, self._answers(), windows=NATIVE_WINDOWS)
        data_root = self.root / "peach-data"
        for key in settings_file.DIRECTORY_KEYS:
            self.assertTrue((data_root / key).is_dir(), key)
        self.assertTrue((data_root / "secrets" / "tls").is_dir())
        self.assertEqual(applied.settings_path, data_root / "config.toml")
        self.assertTrue(applied.settings_path.is_file())
        self.assertFalse(applied.tree.ledger_existed)
        self.assertGreater(applied.tree.migrations, 0)
        self.assertTrue(applied.tree.database.is_file())
        self.assertTrue(applied.tree.token_path.is_file())
        self.assertTrue(applied.tree.token_created)
        self.certs.assert_called_once()
        # 账本真的被迁到最新：`asset` 表在，且是空的（apply 不扫描）。
        connection = sqlite3.connect(applied.tree.database)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM asset").fetchone()[0], 0)
        finally:
            connection.close()

    def test_an_existing_ledger_is_never_migrated_or_overwritten(self):
        first = onboarding.apply(self.config, self._answers(), windows=NATIVE_WINDOWS)
        again = onboarding.create_data_tree(first.config)
        self.assertTrue(again.ledger_existed)
        self.assertEqual(again.migrations, 0)
        self.assertFalse(again.token_created, "口令沿用已有的那份，不重新生成")

    def test_a_missing_openssl_is_reported_instead_of_aborting_the_setup(self):
        self.certs.side_effect = RuntimeError("openssl 不在 PATH 上")
        applied = onboarding.apply(self.config, self._answers(), windows=NATIVE_WINDOWS)
        self.assertIsNone(applied.tree.ca_cert)
        self.assertIn("openssl", applied.tree.ca_error)
        self.assertTrue(applied.settings_path.is_file(), "没有 CA 也要把设置文件写出来")

    def test_writing_over_an_existing_settings_file_needs_force(self):
        onboarding.apply(self.config, self._answers(), windows=NATIVE_WINDOWS)
        with self.assertRaises(settings_file.SettingsFileError):
            onboarding.apply(self.config, self._answers(), windows=NATIVE_WINDOWS)
        onboarding.apply(self.config, self._answers(port=9100),
                         windows=NATIVE_WINDOWS, force=True)
        loaded, _ = onboarding.resolve_config(self.root / "peach-data", environ={})
        self.assertEqual(loaded.server.port, 9100)

    def test_the_first_scan_marker_is_consumed_exactly_once(self):
        applied = onboarding.apply(self.config, self._answers(), windows=NATIVE_WINDOWS)
        config = applied.config
        self.assertIsNone(onboarding.take_first_scan_request(config))
        path = onboarding.request_first_scan(config)
        self.assertEqual(path, config.directory("state") / onboarding.SCAN_REQUEST_NAME)
        self.assertEqual(onboarding.take_first_scan_request(config), "local")
        self.assertFalse(path.exists())
        self.assertIsNone(onboarding.take_first_scan_request(config))

    def test_resolve_config_follows_the_given_data_root(self):
        elsewhere = self.root / "somewhere-else"
        config, broken = onboarding.resolve_config(elsewhere, environ={})
        self.assertIsNone(broken)
        self.assertEqual(config.data_root, elsewhere)
        self.assertEqual(config.path, elsewhere / "config.toml")

    def test_a_broken_settings_file_falls_back_and_hands_over_the_error(self):
        data_root = self.root / "peach-data"
        data_root.mkdir()
        (data_root / "config.toml").write_text("[server\nport = ", encoding="utf-8")
        config, broken = onboarding.resolve_config(data_root, environ={})
        self.assertIsNotNone(broken)
        self.assertEqual(config.server.port, 8900, "坏文件退回内建默认")


@unittest.skipUnless(HAS_HTTP_DEPS, "需要 fastapi 与 httpx")
class SetupPageTests(_Case):
    """首次运行表单的 HTTP 契约：页面字段、逐字段校验、守卫与落盘。

    这一层和 `peach init` 的问答共用 `peach.onboarding`，所以这里断言的是「页面渲染
    出来的字段和 `questions()` 同名同序」，而不是另抄一份字段清单去比对。
    """

    def setUp(self):
        super().setUp()
        (self.media / "a.mp4").write_bytes(b"0" * 10)
        patcher = mock.patch.object(onboarding.certs, "bootstrap_certificates")
        self.certs = patcher.start()
        self.addCleanup(patcher.stop)
        active = mock.patch.object(settings_file, "active", lambda: self.config)
        active.start()
        self.addCleanup(active.stop)
        self.data_root = self.root / "peach-data"

    def _client(self, *, configured: bool = False, client=("127.0.0.1", 12345)):
        import httpx

        from peach.api import create_app
        from peach.config import PeachSettings

        app = create_app(PeachSettings(
            db_path=self.data_root / "database" / "ledger.db",
            configured=configured, token="",
        ))
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, client=client),
            base_url="http://test")

    def _get(self, path, **kwargs):
        import asyncio

        async def run():
            async with self._client(**kwargs) as client:
                return await client.get(path)

        return asyncio.run(run())

    def _post(self, path, data, **kwargs):
        import asyncio

        async def run():
            async with self._client(**kwargs) as client:
                return await client.post(path, data=data)

        return asyncio.run(run())

    def _form(self, **overrides):
        base = {"data_root": str(self.data_root), "media_dir": str(self.media),
                "host": "1", "port": "8900", "mdns_name": "peach", "scan_now": "y"}
        base.update(overrides)
        return {key: value for key, value in base.items() if value is not None}

    def _loaded(self):
        return settings_file.load_config(environ={"PEACH_DATA_ROOT": str(self.data_root)})

    def test_the_first_run_page_renders_every_question_plus_the_scan_checkbox(self):
        response = self._get("/")
        self.assertEqual(response.status_code, 200)
        body = response.text
        self.assertIn('<form method="post" action="/setup">', body)
        for question in onboarding.questions(self.config, windows=NATIVE_WINDOWS):
            self.assertIn(f'name="{question.key}"', body)
        # 页面用自己的题面：短名词加一句说明，不把命令行那份带可选值的题面搬上来。
        for title in ("数据目录", "媒体文件夹", "谁可以访问", "端口", "局域网访问地址"):
            self.assertIn(f">{title}</", body)
        self.assertIn("Peach 数据库、缓存和设置文件都放在这里。", body)
        self.assertIn("可以是外置硬盘上的文件夹", body)
        # 品牌标记在标题上方，说明文字在标题下方。
        self.assertIn('<img class="mark" src="/peach-logo.png"', body)
        self.assertLess(body.index("<h1>"), body.index('class="lede"'))
        # 四个要手填的字段前面标红星；「谁可以访问」总有一个选中项，不标。
        self.assertEqual(body.count('<span class="req"'), 4)
        # 「谁可以访问」是两段式单选，不用原生下拉；两个选项由 `HOST_OPTIONS` 给出，
        # 局域网在左边并且默认选中。
        self.assertNotIn("<select", body)
        self.assertIn('class="switch" role="radiogroup"', body)
        for value, label in onboarding.HOST_OPTIONS:
            self.assertIn(f'<input type="radio" name="host" value="{value}"', body)
            self.assertIn(f"<span>{label}</span>", body)
        self.assertIn('<input type="radio" name="host" value="2" checked>', body)
        self.assertLess(body.index('value="2" checked'), body.index('name="host" value="1"'))
        # 选「只有这台电脑」时局域网地址输入框由页内脚本禁用。
        self.assertIn("field.disabled=!lan", body)
        # 局域网访问地址只填名字，框内前缀 `https://`、后缀 `.local` 拼成完整网址。
        self.assertIn('<div class="affix"><span>https://</span><input', body)
        self.assertIn("<span>.local</span>", body)
        # 勾选框用站内共用的自绘结构，路径在等宽框里。
        self.assertIn('<span class="pcheck"><input type="checkbox" name="scan_now" value="y" checked>', body)
        self.assertIn("完成设置后扫描 <code>", body)

    @unittest.skipIf(NATIVE_WINDOWS, "盘符本身就是挂载点，Windows 上没有这句话")
    def test_the_mounts_explanation_sits_under_the_media_field_on_posix(self):
        self.assertIn("本机挂载点", self._get("/").text)

    def test_invalid_values_come_back_as_a_form_with_per_field_messages(self):
        missing = self.root / "nope"
        response = self._post("/setup", self._form(media_dir=str(missing), port="0"))
        self.assertEqual(response.status_code, 400)
        body = response.text
        self.assertIn("目录不存在", body)
        self.assertIn("端口要是 1 到 65535 之间的整数", body)
        self.assertIn(f'value="{missing}"', body, "填错的值要留在表单里")
        self.assertFalse(missing.exists(), "校验不替人建目录")
        self.assertFalse(self.data_root.exists(), "校验失败不落任何文件")

    def test_a_disabled_lan_address_falls_back_to_the_default_name(self):
        """选「只有这台电脑」后地址框是禁用的，不随表单提交；服务端按默认值补上。"""
        response = self._post("/setup", self._form(host="1", mdns_name=None))
        self.assertEqual(response.status_code, 200)
        loaded = self._loaded()
        self.assertEqual((loaded.server.host, loaded.server.mdns_name), ("127.0.0.1", "peach"))

    def test_a_valid_submission_builds_the_tree_and_shows_what_happens_next(self):
        response = self._post("/setup", self._form())
        self.assertEqual(response.status_code, 200)
        for key in settings_file.DIRECTORY_KEYS:
            self.assertTrue((self.data_root / key).is_dir(), key)
        self.assertTrue((self.data_root / "database" / "ledger.db").is_file())
        self.assertTrue((self.data_root / "secrets" / "tls").is_dir())
        self.assertTrue((self.data_root / "config.toml").is_file())
        self.certs.assert_called_once()
        loaded = self._loaded()
        self.assertTrue(loaded.present)
        self.assertEqual((loaded.server.host, loaded.server.port), ("127.0.0.1", 8900))
        self.assertFalse(loaded.replication.enabled)
        # 勾了「现在扫描」就留下标记，扫描本身不在这条请求里跑。
        self.assertTrue((self.data_root / "state" / onboarding.SCAN_REQUEST_NAME).is_file())
        body = response.text
        self.assertIn("设置完成", body)
        self.assertIn("peach token", body)
        self.assertIn("Peach 数据库：", body)
        self.assertNotIn("账本", body)
        # 完成页尾部是与配置页共用的运行信息：版本、位置和 FFmpeg 一眼可查。
        self.assertIn("<h2>运行信息</h2>", body)
        for term in ("版本", "数据目录", "设置文件", "日志目录", "FFmpeg"):
            self.assertIn(f"<dt>{term}</dt>", body)
        self.assertIn(str(self.data_root), body)

    def test_declining_the_scan_leaves_no_marker(self):
        self._post("/setup", self._form(scan_now=None))
        self.assertFalse((self.data_root / "state" / onboarding.SCAN_REQUEST_NAME).exists())

    def test_a_configured_machine_does_not_have_this_endpoint(self):
        response = self._post("/setup", self._form(), configured=True)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.data_root.exists())

    def test_a_non_loopback_client_is_refused(self):
        response = self._post("/setup", self._form(), client=("198.51.100.7", 51000))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.data_root.exists())

    def test_a_second_submission_refuses_to_overwrite_the_settings_file(self):
        self.assertEqual(self._post("/setup", self._form()).status_code, 200)
        again = self._post("/setup", self._form(port="9100"))
        self.assertEqual(again.status_code, 409)
        self.assertEqual(self._loaded().server.port, 8900, "第二次提交不得改掉已写好的设置")


class StandaloneConfigurationTests(_Case):
    def setUp(self):
        super().setUp()
        from dataclasses import replace
        self.config = replace(self.config, locations={"local": str(self.media)},
                              mounts={}, server=settings_file.ServerSettings(port=9123))
        settings_file.write(self.config)
        self.config = settings_file.load_config(environ={"PEACH_DATA_ROOT": str(self.config.data_root)})
        self.addCleanup(mock.patch.stopall)
        mock.patch("peach.distribution.standalone", return_value=True).start()
        mock.patch("peach.settings_file.load_config", side_effect=lambda: settings_file._merge(
            self.config.data_root, self.config.path, True, True,
            settings_file._read_document(self.config.path), {})).start()

    def client(self, *, token="test-token", address="127.0.0.1"):
        from fastapi.testclient import TestClient
        from peach.api import create_app
        from peach.config import PeachSettings
        return TestClient(create_app(PeachSettings(configured=True, token=token,
                          db_path=self.config.data_root / "database" / "ledger.db")),
                          client=(address, 12345), base_url="http://localhost")

    def test_authenticated_configuration_preserves_values_and_requests_reload(self):
        from peach.routes_configuration import RELOAD_NAME, revision
        with self.client() as client:
            headers = {"X-Token": "test-token"}
            page = client.get("/configuration", headers=headers)
            self.assertEqual(page.status_code, 200)
            self.assertIn("媒体", page.text)
            # 勾选框与运行信息都复用首启页的实现，不再各写一份。
            self.assertIn('<span class="pcheck"><input type="checkbox" name="scan_now" value="y">', page.text)
            self.assertIn("<h2>运行信息</h2>", page.text)
            self.assertIn("<dt>FFmpeg</dt>", page.text)
            self.config.directory("state").mkdir(parents=True, exist_ok=True)
            response = client.post("/configuration", headers=headers, data={
                "revision": revision(self.config), "media_dir": str(self.media), "port": "9124"})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(settings_file.load_config().server.port, 9124)
            self.assertTrue(self.config.path.with_suffix(".previous.toml").is_file())
            self.assertTrue((self.config.directory("state") / RELOAD_NAME).is_file())
            self.assertFalse((self.config.directory("database") / "ledger.db").exists())

    def test_settings_reject_unauthenticated_remote_cross_origin_and_stale_forms(self):
        from peach.routes_configuration import revision
        data = {"revision": revision(self.config), "media_dir": str(self.media), "port": "9124"}
        before = self.config.path.read_bytes()
        with self.client() as client:
            self.assertEqual(client.get("/configuration", follow_redirects=False).status_code, 303)
            response = client.post("/configuration", headers={"X-Token": "test-token", "Origin": "https://example.org"}, data=data)
            self.assertEqual(response.status_code, 403)
            response = client.post("/configuration", headers={"X-Token": "test-token"}, data={**data, "revision": "stale"})
            self.assertEqual(response.status_code, 409)
        with self.client(address="192.0.2.1") as client:
            self.assertEqual(client.get("/configuration", headers={"X-Token": "test-token"}).status_code, 403)
        self.assertEqual(before, self.config.path.read_bytes())

    def test_standalone_tray_uses_its_own_binary_and_configured_loopback_port(self):
        import sys
        from peach.tray import _peach_executable, configured_service_specs, normal_url
        self.assertEqual(_peach_executable(), Path(sys.executable).resolve())
        spec, = configured_service_specs(self.config)
        self.assertEqual(spec.health_url, "http://127.0.0.1:9123/healthz")
        self.assertIn("9123", spec.command)
        self.assertEqual(normal_url(self.config), "http://127.0.0.1:9123/")

    def test_standalone_version_inspection_does_not_execute_git(self):
        from peach.versioning import VersionManager
        execute = mock.Mock(side_effect=AssertionError("Git must not run"))
        manager = VersionManager(execute=execute)
        self.assertEqual(manager.inspect().branch, "测试包")
        self.assertEqual(manager.check().state, "manual")
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
