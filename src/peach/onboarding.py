"""首次运行问答：问什么、怎么校验、写出什么样的设置文件。

这里只有纯逻辑，不碰终端：`peach init` 的命令行问答是它的第一个前端，托盘首启打开的
设置页是第二个，两边都调同一组函数——`questions()` 给出题目、默认值和校验器，
`interview()` 用注入的 `ask` 把题目走一遍，`configure()` 把答案落成 `PeachConfig`。
前端只负责把字串送进来、把错误显示出去。

问答刻意只收最小集合：数据根、一个本地媒体目录、监听范围、端口、局域网名字。复制、
115、PikPak、writer 镜像与 SMB 一律保持默认关闭或留空——陌生人第一次跑不该被这些问题
拦住，设置文件里也只写用户声明过的来源，不把维护者的示例盘符写进别人的文件。

媒体目录在两个平台上落成不同的写法，因为账本路径的形状是不变量（AGENTS.md）：

- Windows：盘符本身就是挂载点，`[media.locations] local = <该目录>`，`[media.mounts]` 留空。
- macOS：声明根仍写账本口径的 `R:\\media`，`[media.mounts] local = <该目录>`，读取侧
  按「声明根前缀 → 本机挂载点」翻译（`peach.platform`），扫描侧按同一规则反着写（`peach.scan`）。
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from . import settings_file
from .platform import is_windows_path
from .settings_file import PeachConfig

#: 提问函数：(题目, 默认值) -> 用户输入的原文。空串表示接受默认值。
Ask = Callable[[str, str], str]

LOOPBACK_HOST = "127.0.0.1"
LAN_HOST = "0.0.0.0"
#: 每题最多问几次。三次都不是有效值就放弃，不能让人困在一个死循环里。
MAX_ATTEMPTS = 3
#: 非 Windows 平台上本地来源的账本口径声明根。账本一律 Windows 形态，这个值只是个前缀，
#: 真正的目录由 `[media.mounts] local` 给出。
POSIX_LOCAL_DECLARED_ROOT = r"R:\media"
#: 本地来源的 ID。v1 只收一个目录，它就是 `asset.location = 'local'`。
LOCAL_LOCATION = "local"

_DNS_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_HOST_CHOICES = {
    "1": LOOPBACK_HOST, "本机": LOOPBACK_HOST, LOOPBACK_HOST: LOOPBACK_HOST,
    "2": LAN_HOST, "局域网": LAN_HOST, LAN_HOST: LAN_HOST,
}
_YES = {"", "y", "yes", "是"}
_NO = {"n", "no", "否"}


class OnboardingAborted(RuntimeError):
    """一题没有问出有效答案：连续给错、或者输入结束。消息以句号结尾，前端接着说后果。"""


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    default: str
    #: 原文 -> 规范值；不合格就抛 `ValueError`，消息直接给人看。
    validate: Callable[[str], object]


@dataclass(frozen=True)
class Answers:
    data_root: Path
    media_dir: Path
    host: str
    port: int
    mdns_name: str


# --------------------------------------------------------------------------- 校验

def validate_data_root(raw: str) -> Path:
    text = raw.strip()
    if not text:
        raise ValueError("数据根不能为空")
    path = Path(text).expanduser()
    if path.is_file():
        raise ValueError(f"{path} 是一个文件，数据根要是目录")
    return path


def media_dir_validator(*, windows: bool) -> Callable[[str], Path]:
    def validate(raw: str) -> Path:
        text = raw.strip()
        if not text:
            raise ValueError("媒体目录不能为空")
        path = Path(text).expanduser()
        if not path.is_dir():
            raise ValueError(f"目录不存在或不是目录：{path}（这里不会替你创建）")
        resolved = path.resolve()
        if windows and not is_windows_path(str(resolved)):
            raise ValueError(f"{resolved} 不是盘符路径；网络位置先映射成盘符再来")
        return resolved
    return validate


def validate_host(raw: str) -> str:
    key = raw.strip().lower()
    try:
        return _HOST_CHOICES[key]
    except KeyError:
        raise ValueError("填 1（仅本机）或 2（局域网）") from None


def validate_port(raw: str) -> int:
    text = raw.strip()
    if not text.isdigit() or not 1 <= int(text) <= 65535:
        raise ValueError("端口要是 1 到 65535 之间的整数")
    return int(text)


def validate_mdns_name(raw: str) -> str:
    text = raw.strip()
    if not _DNS_LABEL.match(text):
        raise ValueError("名字只能用字母、数字和连字符，不能以连字符开头或结尾")
    return text


def validate_yes_no(raw: str) -> bool:
    key = raw.strip().lower()
    if key in _YES:
        return True
    if key in _NO:
        return False
    raise ValueError("填 y 或 n")


# --------------------------------------------------------------------------- 题目

def default_media_dir(home: Path, *, windows: bool) -> Path | None:
    """系统自带的视频目录存在就拿来当默认值；不存在就没有默认，必须手填。"""
    candidate = home / ("Videos" if windows else "Movies")
    return candidate if candidate.is_dir() else None


def questions(
    config: PeachConfig, *, windows: bool, home: Path | None = None,
) -> tuple[Question, ...]:
    """按顺序给出全部题目。默认值来自当前解析到的配置，和非交互 `peach init` 同一口径。"""
    home = Path.home() if home is None else home
    media_default = default_media_dir(home, windows=windows)
    return (
        Question("data_root", "数据根（账本、缓存与设置文件都放这里）",
                 str(config.data_root), validate_data_root),
        Question("media_dir", "本地媒体目录（来源 local，必须已存在）",
                 str(media_default) if media_default else "",
                 media_dir_validator(windows=windows)),
        Question("host", "监听范围：1 = 仅本机（127.0.0.1），2 = 局域网（0.0.0.0）",
                 "1", validate_host),
        Question("port", "服务端口", str(config.server.port), validate_port),
        Question("mdns_name", "局域网名字（<名字>.local，只在监听局域网时发布）",
                 config.server.mdns_name, validate_mdns_name),
    )


def scan_question(media_dir: Path) -> Question:
    return Question("scan_now", f"现在扫描 {media_dir}？(Y/n)", "Y", validate_yes_no)


def ask_until_valid(
    question: Question, ask: Ask, *, report: Callable[[str], None] = print,
    max_attempts: int = MAX_ATTEMPTS,
) -> object:
    """问到拿到合格答案为止，最多 `max_attempts` 次；空输入取默认值。"""
    for attempt in range(1, max_attempts + 1):
        raw = ask(question.prompt, question.default)
        candidate = raw if raw.strip() else question.default
        try:
            return question.validate(candidate)
        except ValueError as exc:
            remaining = max_attempts - attempt
            report(f"  {exc}" + (f"（还可以再试 {remaining} 次）" if remaining else ""))
    raise OnboardingAborted(f"「{question.prompt}」连续 {max_attempts} 次没有拿到有效值。")


def interview(
    config: PeachConfig, ask: Ask, *, windows: bool, home: Path | None = None,
    report: Callable[[str], None] = print, max_attempts: int = MAX_ATTEMPTS,
) -> Answers:
    """把全部题目走一遍。`ask` 由前端注入，测试用脚本化答案驱动。"""
    answers: dict[str, object] = {}
    for question in questions(config, windows=windows, home=home):
        answers[question.key] = ask_until_valid(
            question, ask, report=report, max_attempts=max_attempts)
    return Answers(**answers)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- 落盘

def configure(config: PeachConfig, answers: Answers, *, windows: bool) -> PeachConfig:
    """把答案落成一份可写回的设置。`config` 要按 `answers.data_root` 重新解析过。

    只写用户声明过的来源：`[media.locations]` 里只有 `local`。复制保持关闭，writer 镜像
    与 SMB 坐标留空，目录键全部落成显式值——和非交互 `peach init` 同一形状。
    """
    if windows:
        locations = {LOCAL_LOCATION: str(answers.media_dir)}
        mounts: dict[str, str] = {}
    else:
        locations = {LOCAL_LOCATION: POSIX_LOCAL_DECLARED_ROOT}
        mounts = {LOCAL_LOCATION: str(answers.media_dir)}
    prepared = settings_file.capture_existing(
        config, replication_enabled=False,
        overrides={"host": answers.host, "port": answers.port,
                   "mdns_name": answers.mdns_name},
        mounts=mounts,
    )
    return replace(prepared, locations=locations)


def scan_root(config: PeachConfig) -> str:
    """首次扫描的账本口径根：就是 `local` 的声明根。本机目录由 `peach.scan` 按挂载表取。"""
    return config.locations[LOCAL_LOCATION]


def mounts_explanation(media_dir: Path) -> str:
    """非 Windows 平台写出的两行为什么长那样，一句话说清。"""
    return (f"账本用统一的 Windows 形态记路径（{POSIX_LOCAL_DECLARED_ROOT}\\...），"
            f"本机挂载点 [media.mounts] local = {media_dir} 负责翻译成真实文件。")


def console_ask(prompt: str, default: str) -> str:
    """终端前端：把默认值放在方括号里，回车即接受；输入结束视为放弃。"""
    suffix = f" [{default}]" if default else "（必填）"
    try:
        return input(f"{prompt}{suffix}: ")
    except EOFError:
        raise OnboardingAborted("输入已结束。") from None


def is_interactive(stdin) -> bool:
    """stdin 是不是一个真的终端。管道、重定向和没有 stdin 的打包进程都不是。"""
    try:
        return bool(stdin is not None and stdin.isatty())
    except (AttributeError, ValueError, OSError):
        return False


__all__ = [
    "Answers", "Ask", "LOCAL_LOCATION", "MAX_ATTEMPTS", "OnboardingAborted",
    "POSIX_LOCAL_DECLARED_ROOT", "Question", "ask_until_valid", "configure",
    "console_ask", "default_media_dir", "interview", "is_interactive",
    "mounts_explanation", "questions", "scan_question", "scan_root",
]
