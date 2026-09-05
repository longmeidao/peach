"""首次运行问答：问什么、怎么校验、写出什么样的设置文件。

这里只有纯逻辑，不碰终端：`peach init` 的命令行问答是它的第一个前端，托盘首启打开的
设置页（`routes_pages`）是第二个，两边都调同一组函数——`questions()` 给出题目、默认值
和校验器，`interview()` 用注入的 `ask` 把题目走一遍，`configure()` 把答案落成
`PeachConfig`，`apply()` 把它变成一台能直接起服务的机器（目录、账本、CA、口令、设置
文件）。前端只负责把字串送进来、把结果和错误显示出去。

问答刻意只收最小集合：数据根、一个本地媒体目录、监听范围、端口、局域网名字。复制、
115、PikPak、writer 镜像与 SMB 一律保持默认关闭或留空——陌生人第一次跑不该被这些问题
拦住，设置文件里也只写用户声明过的来源，不把维护者的示例盘符写进别人的文件。

媒体目录在两个平台上落成不同的写法，因为账本路径的形状是不变量（AGENTS.md）：

- Windows：盘符本身就是挂载点，`[media.locations] local = <该目录>`，`[media.mounts]` 留空。
- macOS：声明根仍写账本口径的 `R:\\media`，`[media.mounts] local = <该目录>`，读取侧
  按「声明根前缀 → 本机挂载点」翻译（`peach.platform`），扫描侧按同一规则反着写（`peach.scan`）。
"""
from __future__ import annotations

import os
import re
import socket
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from . import auth, certs, settings_file
from .migrations import upgrade
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
#: 迁移随代码走，不随数据走。这里不 import `peach.config`：那个模块的常量在进程启动
#: 那一刻就定型了，而首次设置正是要改变它们指向的数据根。
MIGRATIONS_DIR = settings_file.PROJECT_ROOT / "migrations"
#: 「现在扫描」的一次性标记，落在 `<数据根>/state/`。设置页写它、托盘消费它：
#: 设置页所在的引导服务在设置完成的那一刻就会被托盘停掉，扫描不能跑在它的进程里。
SCAN_REQUEST_NAME = "first-scan.request"
RELOAD_NAME = "configuration-reload.request"

#: 监听范围的两个选项：(提交值, 说明)。题目文本和设置页的下拉都由它生成，
#: 所以两处永远是同一批选项，改一个不会漏掉另一个。
HOST_OPTIONS = (("1", "只有这台电脑"), ("2", "同一局域网的设备"))
#: 首扫题的题面。CLI 在后面接 `(Y/n)`，设置页把它当勾选框的标签。
SCAN_PROMPT = "现在扫描 {target}？"

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
        raise ValueError("填 1（只有这台电脑）或 2（同一局域网的设备）") from None


def validate_port(raw: str) -> int:
    text = raw.strip()
    if not text.isdigit() or not 1 <= int(text) <= 65535:
        raise ValueError("端口要是 1 到 65535 之间的整数")
    return int(text)


def check_available_port(port: int, current: int) -> None:
    if port == current:
        return
    try:
        with socket.socket() as candidate:
            candidate.bind(("127.0.0.1", port))
    except OSError as exc:
        raise ValueError("这个端口已被占用，请换一个端口") from exc


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
        Question("data_root", "数据目录（Peach 数据库、缓存和设置文件都放在这里）",
                 str(config.data_root), validate_data_root),
        Question("media_dir", "媒体文件夹（必须已经存在，可以在外置硬盘上）",
                 str(media_default) if media_default else "",
                 media_dir_validator(windows=windows)),
        Question("host",
                 "谁可以访问：" + "，".join(f"{value} = {label}" for value, label in HOST_OPTIONS),
                 "2", validate_host),
        Question("port", "端口", str(config.server.port), validate_port),
        Question("mdns_name", "局域网访问地址（<名字>.local，只在允许局域网访问时发布）",
                 config.server.mdns_name, validate_mdns_name),
    )


def scan_question(media_dir: Path | str) -> Question:
    return Question("scan_now", SCAN_PROMPT.format(target=media_dir) + "(Y/n)",
                    "Y", validate_yes_no)


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


@dataclass(frozen=True)
class DataTree:
    """`create_data_tree()` 做了什么。前端自己决定这些事实怎么说出来。"""

    data_root: Path
    database: Path
    #: 这次应用了几个迁移。账本本来就在时是 0。
    migrations: int
    ledger_existed: bool
    token_path: Path
    token_created: bool
    #: 没有 openssl 时 CA 生成失败，`ca_cert` 为 None、`ca_error` 是原因。
    ca_cert: Path | None
    ca_error: str | None


@dataclass(frozen=True)
class Applied:
    """一次完整的首次设置：目录、账本、CA、口令、设置文件都已落盘。"""

    config: PeachConfig
    settings_path: Path
    tree: DataTree


def resolve_config(
    data_root: Path | None = None, environ: dict[str, str] | None = None,
) -> tuple[PeachConfig, settings_file.SettingsFileError | None]:
    """按给定数据根重新解析设置；文件坏了就退回内建默认并把错误一并交出。

    `peach init` 与设置页都要在拿到数据根之后重新解析一次：数据根决定设置文件在哪，
    而进程启动时那一份是按发现顺序算的，用户完全可以填一个别的目录。
    """
    environ = dict(os.environ if environ is None else environ)
    if data_root is not None:
        environ["PEACH_DATA_ROOT"] = str(data_root)
    try:
        return settings_file.load_config(environ=environ), None
    except settings_file.SettingsFileError as exc:
        return settings_file.load_config(environ=environ, strict=False), exc


def create_data_tree(config: PeachConfig) -> DataTree:
    """建目录、把库迁到最新、生成本机 CA、确保口令存在。已经有账本就不碰它。

    只做事、不打印：`peach init` 把结果写到终端，设置页把同一批结果写进成功页。
    """
    for key in settings_file.DIRECTORY_KEYS:
        config.directory(key).mkdir(parents=True, exist_ok=True)
    tls_dir = config.directory("secrets") / "tls"
    tls_dir.mkdir(parents=True, exist_ok=True)

    database = config.directory("database") / "ledger.db"
    existed = database.is_file()
    # 已有账本却在跑全新 init：不迁移、不备份、不覆盖，让人自己决定。
    applied = 0 if existed else len(upgrade(database, MIGRATIONS_DIR))

    ca_cert: Path | None = None
    ca_error: str | None = None
    try:
        ca_cert = certs.bootstrap_certificates(
            tls_dir, config.server.mdns_name + ".local").ca_cert
    except (RuntimeError, OSError) as exc:
        # 没有 openssl 不该挡住初始化：HTTP 本地访问照样能用，装 openssl 后重跑即可。
        ca_error = str(exc)

    secrets_dir = config.directory("secrets")
    _token, created = auth.ensure_token(secrets_dir)
    return DataTree(
        data_root=config.data_root, database=database, migrations=applied,
        ledger_existed=existed, token_path=auth.token_path(secrets_dir),
        token_created=created, ca_cert=ca_cert, ca_error=ca_error,
    )


def apply(
    config: PeachConfig, answers: Answers, *, windows: bool, force: bool = False,
) -> Applied:
    """把答案变成一台可以直接起服务的机器：目录、账本、CA、口令、设置文件。

    `config` 要按 `answers.data_root` 重新解析过（`resolve_config`）。CLI 问答和托盘的
    设置页都只调这一个函数，两条前端因此不可能在「首次运行到底做了什么」上分叉。
    """
    prepared = configure(config, answers, windows=windows)
    tree = create_data_tree(prepared)
    path = settings_file.write(prepared, force=force)
    return Applied(config=prepared, settings_path=path, tree=tree)


def scan_request_path(config: PeachConfig) -> Path:
    return config.directory("state") / SCAN_REQUEST_NAME


def request_first_scan(config: PeachConfig, location: str = LOCAL_LOCATION) -> Path:
    """记下「用户要求首扫」。内容是来源 ID，托盘据此拉起 `peach scan <来源>`。"""
    path = scan_request_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(location, encoding="utf-8")
    return path


def take_first_scan_request(config: PeachConfig) -> str | None:
    """读走首扫标记并删掉它，没有就返回 None。只消费一次：删除在读取之后立刻发生，
    托盘的健康轮询每几秒跑一轮，留着它等于每一轮都再扫一遍整个媒体目录。
    """
    path = scan_request_path(config)
    try:
        location = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    try:
        path.unlink()
    except OSError:
        return None
    return location or None


def scan_root(config: PeachConfig) -> str:
    """首次扫描的账本口径根：就是 `local` 的声明根。本机目录由 `peach.scan` 按挂载表取。"""
    return config.locations[LOCAL_LOCATION]


def mounts_explanation(media_dir: Path | str) -> str:
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
    "HOST_OPTIONS", "SCAN_PROMPT",
    "Answers", "Applied", "Ask", "DataTree", "LOCAL_LOCATION", "MAX_ATTEMPTS",
    "OnboardingAborted", "POSIX_LOCAL_DECLARED_ROOT", "Question", "apply",
    "ask_until_valid", "configure", "console_ask", "create_data_tree",
    "default_media_dir", "interview", "is_interactive", "mounts_explanation",
    "questions", "request_first_scan", "resolve_config", "scan_question",
    "scan_request_path", "scan_root", "take_first_scan_request",
]
