"""账本盘符与本机挂载点之间的受控映射。

账本里的 `asset.path` 一律是 Windows 形态的绝对路径：`R:\\Media\\...`（本地硬盘）、
`A:\\...`（PikPak）、`B:\\...`（115）。2026-08 起同一份账本要在 macOS 上读，而
CloudDrive 在两个平台的挂载方式完全不同：Windows 是盘符，macOS 是 macFUSE 挂载点。

Peach 不重写账本，只在**读取时**把盘符映射到本机挂载点。写回账本的索引脚本仍然只在
Windows 上运行，账本因此保持单一路径口径。

没有对应挂载点的盘符会被映射到 `UNMAPPED_ROOT` 下，一定通不过 `allowed_media_roots`
授权，于是该来源整体按「脱盘」处理，而不是意外落到当前工作目录下的同名相对路径。
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path, PureWindowsPath
from typing import Callable
from urllib.parse import quote

LOGGER = logging.getLogger(__name__)

# 盘符 -> 本机挂载点。Windows 上恒为空：盘符本身就是挂载点，不需要任何转换。
_DEFAULT_DRIVE_MAP: dict[str, str] = (
    {}
    if os.name == "nt"
    else {
        "R": "/Volumes/RESOURCES",
        "A": str(Path.home() / "Desktop" / "IMSL" / "Pikpak"),
        "B": str(Path.home() / "Desktop" / "IMSL" / "115"),
    }
)

# 未映射盘符的落点。刻意选一个不可能存在的绝对路径，让授权和存在性检查都必然失败。
UNMAPPED_ROOT = Path("/nonexistent/peach-unmapped-drive")


@lru_cache(maxsize=8)
def _parse_override(raw: str) -> tuple[tuple[str, str], ...]:
    """`PEACH_DRIVE_MAP=R=/Volumes/RESOURCES,B=/Users/me/115` 形式的覆盖。"""
    pairs: list[tuple[str, str]] = []
    for chunk in raw.split(","):
        drive, separator, mount = chunk.partition("=")
        drive = drive.strip()
        if not separator or len(drive) != 1 or not drive.isalpha():
            continue
        pairs.append((drive.upper(), mount.strip()))
    return tuple(pairs)


def drive_map() -> dict[str, Path]:
    """当前生效的盘符映射；空值表示显式声明「本机没有这个来源」。"""
    merged = dict(_DEFAULT_DRIVE_MAP)
    merged.update(dict(_parse_override(os.environ.get("PEACH_DRIVE_MAP", ""))))
    return {drive: Path(mount) for drive, mount in merged.items() if mount}


def root_online(root: Path) -> bool:
    """挂载点在不在。

    目录存在还不够：CloudDrive 掉线后挂载点目录仍然在，但读第一个条目就报错
    `Device not configured`。判据统一成「能否列出一个条目」。
    """
    try:
        with os.scandir(root) as entries:
            next(iter(entries), None)
    except OSError:
        return False
    return True


#: 挂载超时。这是兜底，不是常规耗时——本机实测一次成功挂载 0.6 秒。
MOUNT_TIMEOUT_SECONDS = 15.0

#: 钥匙串里 SMB 记录的协议标识。四字符定长，末尾那个空格是格式的一部分。
_SMB_PROTOCOL = "smb "


def share_url(host: str, share: str, user: str = "") -> str:
    """SMB URL。每一段都做百分号编码，引号和反斜杠因此不可能落进 AppleScript 字面量。"""
    credentials = f"{quote(user, safe='')}@" if user else ""
    return f"smb://{credentials}{quote(host, safe='')}/{quote(share, safe='')}"


def mount_share_command(url: str) -> list[str] | None:
    """挂上一个 SMB 共享的 argv；本平台没有这条路径时返回 None。

    走 `osascript` 的 `mount volume` 而不是 `open smb://`：两者都经 NetFS，会自己在
    `/Volumes` 下建挂载点并取钥匙串里的凭据（`/Volumes` 归 root，脚本 mkdir 不了，
    而 `mount_smbfs` 又要求挂载点已经存在），区别是 `open` 会顺带弹一个 Finder 窗口。
    2026-08-27 本机实测：卸载后跑这条命令 0.6 秒挂回来，无窗口，返回 0。
    """
    if sys.platform != "darwin":
        return None
    return ["osascript", "-e", f'mount volume "{url}"']


def share_credentials_command(host: str, user: str) -> list[str]:
    """查钥匙串里有没有这台主机的 SMB 记录的 argv。

    刻意不带 `-w`：只判断记录在不在，密码不会被读出来，也就不会经过本进程。
    """
    return [
        "security", "find-internet-password",
        "-s", host, "-a", user, "-r", _SMB_PROTOCOL,
    ]


def share_credentials_present(
    host: str,
    user: str,
    *,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> bool:
    """钥匙串里有没有这台主机、这个账号的 SMB 记录。

    2026-08-27 实测：没有记录时 NetFS 不会失败，而是拉起 NetAuthAgent 弹一个认证框
    然后一直等——托盘那次点击既卡到超时，又在用户没要求的时候把密码框推到屏幕上。
    先查一次就把这条路径变成一次快速失败。记录按**主机名**存：同一台机器的 IP 和
    mDNS 名是两条不同的记录，换一个主机名就要重新记一次密码。
    """
    try:
        result = run(share_credentials_command(host, user),
                     capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        LOGGER.warning("查钥匙串失败：%s", exc)
        return False
    return result.returncode == 0


def mount_share(
    host: str,
    share: str,
    user: str = "",
    *,
    timeout: float = MOUNT_TIMEOUT_SECONDS,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> bool:
    """挂一次共享，成败只用返回值表示。

    任何失败都不抛：调用方是「挂不上就照旧降级」的那条路径，异常在那里只会把一条
    清楚的消息换成一次崩溃。失败原因写日志，否则事后完全无从查起。
    """
    command = mount_share_command(share_url(host, share, user))
    if command is None:
        return False
    if user and not share_credentials_present(host, user, run=run):
        LOGGER.warning("钥匙串里没有 %s@%s 的 SMB 记录，不去弹认证框", user, host)
        return False
    try:
        result = run(command, capture_output=True, text=True,
                     timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        LOGGER.warning("挂载 //%s/%s 失败：%s", host, share, exc)
        return False
    if result.returncode:
        LOGGER.warning("挂载 //%s/%s 失败：%s", host, share,
                       (result.stderr or result.stdout or "").strip())
        return False
    return True


def within_root(path: Path, root: Path) -> bool:
    """路径是否落在授权根内。

    字面比较先走一遍；不匹配时用 inode 比较兜底，因为账本里是 `R:\\Media`
    而授权根是 `/Volumes/RESOURCES/media`，exFAT/NTFS 大小写不敏感、pathlib 不是。
    """
    if path == root or root in path.parents:
        return True
    depth = len(root.parts)
    if len(path.parts) < depth:
        return False
    try:
        return Path(*path.parts[:depth]).samefile(root)
    except OSError:
        return False


def system_volume() -> Path:
    """磁盘闸门看的那块盘。

    CloudDrive 会把下载块缓存到系统盘：Windows 是 `C:`，macOS 是根卷。
    """
    return Path("C:/") if os.name == "nt" else Path("/")


def is_windows_path(raw: str | os.PathLike[str]) -> bool:
    text = os.fspath(raw)
    return len(text) >= 3 and text[0].isalpha() and text[1] == ":" and text[2] in "\\/"


def is_unmapped(path: Path) -> bool:
    return path == UNMAPPED_ROOT or UNMAPPED_ROOT in path.parents


def translate_ledger_path(raw: str | os.PathLike[str]) -> Path:
    """把账本里的 Windows 路径翻译成本机路径；非 Windows 形态原样返回。"""
    text = os.fspath(raw)
    if os.name == "nt" or not is_windows_path(text):
        return Path(text)
    parts = PureWindowsPath(text).parts
    drive = parts[0][0].upper()
    rest = parts[1:]
    root = drive_map().get(drive)
    if root is None:
        return UNMAPPED_ROOT.joinpath(drive, *rest)
    return root.joinpath(*rest)


def translate_roots(roots) -> tuple[Path, ...]:
    """翻译一组授权根，丢掉本机没有挂载的来源。"""
    translated = [translate_ledger_path(root) for root in roots]
    return tuple(path for path in translated if not is_unmapped(path))


def media_root_status(roots) -> tuple[dict[str, object], ...]:
    """每个声明来源的可达性；`/api/index` 靠它决定要不要把本地筛选置灰。"""
    status: list[dict[str, object]] = []
    for root in roots:
        raw = os.fspath(root)
        path = translate_ledger_path(raw)
        mapped = not is_unmapped(path)
        status.append(
            {
                "declared": raw,
                "resolved": str(path) if mapped else None,
                "mapped": mapped,
                "online": bool(mapped and path.is_dir()),
            }
        )
    return tuple(status)


def reveal_command(path: Path) -> list[str] | None:
    """在文件管理器里定位这个文件的 argv；本平台不支持时返回 None。

    做成纯函数是为了能在没有桌面的环境里测：真正 spawn 的那一步只有一行。
    `explorer` 要求 `/select,<路径>` 整体是**一个**参数，逗号后不能断开，所以
    必须用列表传参而不是拼字符串——顺带也就没有引号注入的余地。
    """
    target = os.fspath(path)
    if os.name == "nt":
        return ["explorer", f"/select,{target}"]
    if sys.platform == "darwin":
        return ["open", "-R", target]
    return None
