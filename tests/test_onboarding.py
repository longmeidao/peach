"""`peach.onboarding`：首次运行问答的题目、校验与落盘，纯逻辑、可注入。

CLI 与将来的托盘设置页共用这一层，所以这里只用脚本化答案驱动，不碰 stdin；平台由
`windows=` 注入。只有一处例外：媒体目录题要收一个真实存在的目录，而那个目录是不是盘符
路径由测试机决定，所以走到这道题的用例按 `NATIVE_WINDOWS` 用本机形态。
"""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach import onboarding, settings_file

NATIVE_WINDOWS = os.name == "nt"


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
        self.assertEqual(by_key["host"].default, "1")
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
            "数据根（账本、缓存与设置文件都放这里）",
            "本地媒体目录（来源 local，必须已存在）",
            "监听范围：1 = 仅本机（127.0.0.1），2 = 局域网（0.0.0.0）",
            "服务端口",
            "局域网名字（<名字>.local，只在监听局域网时发布）",
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


if __name__ == "__main__":
    unittest.main()
