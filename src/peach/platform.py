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
from functools import lru_cache
from pathlib import Path, PureWindowsPath

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


