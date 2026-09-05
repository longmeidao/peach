"""扫描一个来源的目录，把文件元数据写进账本。

这是摄取入口，不是复核写入：它新增行、刷新 `size`／`mtime`／`last_seen`，不改任何
真相字段，也不删行——本次没扫到的文件只会在 `last_seen` 上落后，由资源同步对账决定去留。

两条不变量都在这里守：

- `asset.location` 是来源 ID，`asset.path` 一律是 Windows 形态的账本路径。扫描根必须
  落在该来源 `[media.locations]` 声明根之内（`check_scan_target`），否则写进去的行既
  翻译不出本机路径、也通不过授权根，而且要等到有人点开那个资产才会发现。
- 目录在本机哪里，由 `[media.mounts]` 决定。Windows 上盘符本身就是挂载点，声明根原样
  就是要遍历的目录；macOS 上遍历的是挂载点，写进账本的仍是 `声明根\\相对路径`，这样
  读取侧的 `platform.translate_ledger_path` 才翻得回同一个文件。

`peach init` 的首次扫描、`peach scan` 与 `scripts/ledger.py scan` 都调这里，
声明根和挂载表由调用方传入而不是读进程缓存：`init` 刚写完设置文件时缓存还是旧的。
"""
from __future__ import annotations

import os
import sqlite3
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from .platform import is_windows_path, resolve_location, resolve_root

VIDEO = {".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".mov", ".ts", ".flv", ".rmvb", ".mpg",
         ".m2ts"}
IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
AUDIO = {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".opus"}
ARCHIVE = {".zip", ".rar", ".7z", ".tar", ".gz"}

#: 每攒够这么多行落一次盘，并报一行进度。
BATCH_SIZE = 2000

_UPSERT = """INSERT INTO asset(location,path,name,medium,size,mtime,first_seen,last_seen)
             VALUES(?,?,?,?,?,?,?,?)
             ON CONFLICT(location,path) DO UPDATE SET
               size=excluded.size, mtime=excluded.mtime, last_seen=excluded.last_seen"""


class ScanTargetError(ValueError):
    """来源与扫描根对不上，或者来源在本机没有落点。消息可以直接给人看。"""


def medium_of(name: str) -> str:
    suffix = os.path.splitext(name)[1].lower()
    if suffix in VIDEO:
        return "video"
    if suffix in IMAGE:
        return "image"
    if suffix in AUDIO:
        return "audio"
    if suffix in ARCHIVE:
        return "archive"
    return "other"


def check_scan_target(
    location: str, root: str, *, declared_roots: Mapping[str, Sequence[str]],
) -> None:
    """扫描根必须落在这个来源的某个声明根内，否则拒绝（ADR-0023 第 2 阶段的写入侧门槛）。"""
    declared = declared_roots.get(location)
    if declared is None:
        known = "、".join(sorted(declared_roots)) or "（设置文件里一个都没有）"
        raise ScanTargetError(f"✗ 未声明的来源 {location!r}；[media.locations] 里已知：{known}")
    actual = resolve_location(root, declared_roots)[0]
    if actual != location:
        raise ScanTargetError(
            f"✗ 扫描根与来源对不上：{location} 的声明根是 {'、'.join(declared)}，"
            f"但要扫的是 {root}"
            + (f"（那是 {actual} 的地盘）" if actual else "（不在任何声明根下）")
        )


def ledger_root_for(
    location: str, root: str | os.PathLike[str], *,
    declared_roots: Mapping[str, Sequence[str]],
    mounts: Mapping[str, Sequence[str | Path]], windows: bool | None = None,
) -> str:
    """把用户给的目录换成账本口径的扫描根。

    Windows 上任何绝对路径本来就是账本形态，相对路径先按当前目录补全。其他平台上
    给的是本机目录（某个挂载点下的某一层），换成对应那个 `声明根\\相对路径`；没有
    挂载点或不在任何挂载点下都拒绝——那种目录扫出来的行谁也翻译不回去。
    """
    windows = os.name == "nt" if windows is None else windows
    text = os.fspath(root)
    if windows:
        return text if is_windows_path(text) else str(Path(text).resolve())
    declared = declared_roots.get(location, ())
    location_mounts = tuple(mounts.get(location, ()))
    for declared_root, mount in zip(declared, location_mounts):
        try:
            tail = Path(text).resolve().relative_to(Path(mount).resolve()).parts
        except ValueError:
            continue
        return str(PureWindowsPath(declared_root, *tail))
    if is_windows_path(text):
        return text
    if not location_mounts:
        raise ScanTargetError(
            f"✗ 来源 {location!r} 在本机没有挂载点，无法把 {text} 换成账本路径；"
            f"先在 [media.mounts] 里声明它的落点")
    shown = "、".join(os.fspath(mount) for mount in location_mounts)
    raise ScanTargetError(f"✗ {text} 不在来源 {location!r} 的挂载点 {shown} 之下")


def walk_root_for(
    location: str, root: str, *, declared_roots: Mapping[str, Sequence[str]],
    mounts: Mapping[str, Sequence[str | Path]], windows: bool | None = None,
) -> Path:
    """账本口径的扫描根在本机要遍历哪个目录。调用前先过 `check_scan_target`。"""
    windows = os.name == "nt" if windows is None else windows
    if windows:
        return Path(root)
    _location, index, tail = resolve_root(root, declared_roots)
    location_mounts = tuple(mounts.get(location, ()))
    if index >= len(location_mounts):
        raise ScanTargetError(
            f"✗ 来源 {location!r} 的第 {index + 1} 个声明根在本机没有挂载点；"
            f"先在 [media.mounts] 里按顺序声明它的落点")
    return Path(location_mounts[index]).joinpath(*tail)


@dataclass(frozen=True)
class ScanResult:
    location: str
    root: str
    files: int
    total_bytes: int
    seconds: float
    #: 该来源里本次没扫到的行数（`last_seen` 落后于本次）。
    gone: int

    def summary(self) -> str:
        return (f"✓ {self.location}: {self.files:,} 文件 / "
                f"{self.total_bytes / 1024 ** 4:.2f} TB / 耗时 {self.seconds:.0f}s；"
                f"清单中已消失 {self.gone:,} 个")


def scan_location(
    db_path: str | os.PathLike[str], location: str, root: str, *,
    declared_roots: Mapping[str, str], mounts: Mapping[str, str | Path] | None = None,
    report: Callable[[str], None] = print, windows: bool | None = None,
) -> ScanResult:
    """遍历 `root`（账本口径）对应的本机目录，把文件元数据 upsert 进 `asset`。

    读不了的目录和文件直接跳过，不中断整轮：网盘挂载里零星几个条目读失败很常见，
    一个坏条目不该让几万个好条目白扫。
    """
    check_scan_target(location, root, declared_roots=declared_roots)
    walk_root = walk_root_for(
        location, root, declared_roots=declared_roots, mounts=mounts or {}, windows=windows)
    ledger_root = PureWindowsPath(root)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    started = time.time()
    files = 0
    total = 0
    batch: list[tuple] = []
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        for directory, _subdirs, names in os.walk(walk_root, onerror=lambda _error: None):
            relative = Path(directory).relative_to(walk_root).parts
            for name in names:
                try:
                    stat = os.stat(os.path.join(directory, name))
                except OSError:
                    continue
                ledger_path = str(ledger_root.joinpath(*relative, name))
                mtime = time.strftime("%Y-%m-%d", time.localtime(stat.st_mtime))
                batch.append((location, ledger_path, name, medium_of(name),
                              stat.st_size, mtime, now, now))
                files += 1
                total += stat.st_size
                if len(batch) >= BATCH_SIZE:
                    connection.executemany(_UPSERT, batch)
                    connection.commit()
                    batch.clear()
                    report(f"  {time.time() - started:5.0f}s  {files:,} 文件  "
                           f"{total / 1024 ** 4:.2f} TB")
        if batch:
            connection.executemany(_UPSERT, batch)
        connection.commit()
        gone = connection.execute(
            "SELECT COUNT(*) FROM asset WHERE location=? AND last_seen<?",
            (location, now)).fetchone()[0]
    finally:
        connection.close()
    result = ScanResult(location, root, files, total, time.time() - started, gone)
    report(result.summary())
    return result
