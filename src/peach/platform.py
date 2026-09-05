"""账本来源与本机挂载点之间的受控映射。

账本里的 `asset.path` 一律是 Windows 形态的绝对路径：`R:\\media\\...`（本地硬盘）、
`A:\\...`（PikPak）、`B:\\...`（115）。这是不变量，不随平台改写。

真正会变的是「同一个来源在这台机器上落在哪」。`asset.location` 本来就是挂载点 ID
（`local` / `115` / `pikpak`），设置文件用 `[media.locations]` 声明每个 ID 的账本口径根，
用 `[media.mounts]` 声明它在本机的落点，翻译按「声明根前缀 → 本机挂载点」进行
（ADR-0023 第 2 阶段勘误）。Windows 上盘符本身就是挂载点，路径原样返回。

没有挂载点的来源会被映射到 `UNMAPPED_ROOT` 下，一定通不过 `allowed_media_roots`
授权，于是该来源整体按「脱盘」处理，而不是意外落到当前工作目录下的同名相对路径。
"""
from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path, PureWindowsPath

from . import settings_file

LOGGER = logging.getLogger(__name__)

# 未映射来源的落点。刻意选一个不可能存在的绝对路径，让授权和存在性检查都必然失败。
UNMAPPED_ROOT = Path("/nonexistent/peach-unmapped-drive")

#: 运行期覆盖挂载表的环境变量。键是 location ID，不是盘符。
MOUNTS_ENV = "PEACH_MEDIA_MOUNTS"


@lru_cache(maxsize=8)
def _parse_override(raw: str) -> tuple[tuple[str, str], ...]:
    """`PEACH_MEDIA_MOUNTS=local=/Volumes/RESOURCES/media,115=/Volumes/CloudDrive/115` 形式的覆盖。"""
    pairs: list[tuple[str, str]] = []
    for chunk in raw.split(","):
        location, separator, mount = chunk.partition("=")
        location = location.strip()
        if not separator or not location:
            continue
        pairs.append((location, mount.strip()))
    return tuple(pairs)


def location_mounts() -> dict[str, Path]:
    """当前生效的「来源 ID → 本机挂载点」；空值表示显式声明「本机没有这个来源」。

    基础映射来自设置文件的 `[media.mounts]`（内建默认为空：一台新机器什么都没挂，
    对应资产按脱盘处理）。`MOUNTS_ENV` 每次现读而不是缓存进设置层——测试和临时诊断
    会在运行期改它，缓存住就看不到变化。
    """
    merged = dict(settings_file.active().mounts)
    merged.update(dict(_parse_override(os.environ.get(MOUNTS_ENV, ""))))
    return {location: Path(mount) for location, mount in merged.items() if mount}


def location_roots() -> dict[str, str]:
    """来源 ID → 账本口径的声明根，来自 `[media.locations]`。"""
    return dict(settings_file.active().locations)


def declared_root(location: str) -> str | None:
    """某个来源在账本里的声明根；未声明的来源返回 None。"""
    return location_roots().get(location)


def resolve_location(
    raw: str | os.PathLike[str], roots: Mapping[str, str] | None = None,
) -> tuple[str | None, tuple[str, ...]]:
    """账本路径属于哪个来源，以及它在声明根之后的层级。

    翻译和写入侧门槛共用这一段判定，所以它只碰 `PureWindowsPath` 和字符串，
    在两个平台上行为一致、也都能测。声明根重叠时取最长的那个（`R:\\` 与
    `R:\\media` 同时声明时，`R:\\media\\x` 归后者）。大小写不敏感由
    `PureWindowsPath` 负责：账本里写 `R:\\Media`、声明根写 `R:\\media` 是同一处。

    `roots` 缺省取当前生效的 `[media.locations]`。`peach init` 刚写完设置文件时进程里
    那份缓存还是旧的，这种调用方把要用的声明根显式传进来。
    """
    text = os.fspath(raw)
    if not is_windows_path(text):
        return None, ()
    candidate = PureWindowsPath(text)
    best: tuple[int, str] | None = None
    declared_roots = location_roots() if roots is None else roots
    for location, root in declared_roots.items():
        declared = PureWindowsPath(root)
        if candidate == declared or candidate.is_relative_to(declared):
            depth = len(declared.parts)
            if best is None or depth > best[0]:
                best = (depth, location)
    if best is None:
        return None, ()
    return best[1], candidate.parts[best[0]:]


def location_of(
    raw: str | os.PathLike[str], roots: Mapping[str, str] | None = None,
) -> str | None:
    """账本路径属于哪个来源；不在任何声明根下则返回 None。

    写入侧用它拦截「location 和 root 对不上」的导入（`peach.scan.check_scan_target`）。
    """
    return resolve_location(raw, roots)[0]


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
    location, tail = resolve_location(text)
    if location is not None:
        mount = location_mounts().get(location)
        if mount is not None:
            return mount.joinpath(*tail)
    # 没声明过的前缀（例如遗留的 `R:\\Resources\\...`）或没挂载的来源：落到不可达根，
    # 保留盘符和其余层级，方便日志里认出是哪条路径。
    parts = PureWindowsPath(text).parts
    return UNMAPPED_ROOT.joinpath(parts[0][0].upper(), *parts[1:])


def translate_roots(roots) -> tuple[Path, ...]:
    """翻译一组授权根，丢掉本机没有挂载的来源。"""
    translated = [translate_ledger_path(root) for root in roots]
    return tuple(path for path in translated if not is_unmapped(path))
