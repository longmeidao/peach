"""Peach 的唯一 Media Engine：按 asset id 解析本机与挂载来源的文件。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PureWindowsPath
from time import monotonic
from typing import Sequence

from .platform import (
    is_unmapped,
    is_windows_path,
    root_online,
    translate_ledger_path,
    within_root,
)
from .repository import LedgerRepository, MediaAsset
from .segments import HLS_SEGMENT_SECONDS


def normalized_path(path: Path | str) -> Path:
    """Windows 离线/云盘可能让 realpath 失败；仍保留绝对路径安全边界。

    账本里的盘符路径先按本机挂载点翻译，macOS 上才不会被当成当前目录下的相对路径。
    """
    candidate = translate_ledger_path(path)
    try:
        return candidate.resolve()
    except OSError:
        return Path(os.path.abspath(os.fspath(candidate)))


CASE_MATCH_TTL_SECONDS = 5.0


@lru_cache(maxsize=512)
def _cached_case_insensitive_match(
    parent_key: str, name_key: str, _ttl_bucket: int,
) -> str | None:
    """同目录大小写不敏感匹配；只为大小写敏感的挂载层（CloudDrive/APFS）兜底。

    NTFS 上 `Path.is_file()` 已不区分大小写，正常情况不会走到这里。
    结果按 (parent, name) 缓存，避免同一目录反复 scandir。
    """
    target = name_key.casefold()
    try:
        with os.scandir(parent_key) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.casefold() == target:
                    return entry.name
    except OSError:
        return None
    return None


def _case_insensitive_match(parent_key: str, name_key: str) -> str | None:
    """Cache scans briefly without pinning misses or stale names forever."""
    bucket = int(monotonic() // CASE_MATCH_TTL_SECONDS)
    return _cached_case_insensitive_match(parent_key, name_key, bucket)


def resolve_case_insensitive(path: Path | str) -> str:
    """返回可直接打开的实际路径：原路径不存在时按大小写不敏感匹配同目录文件。"""
    # 批处理脚本直接调用本函数，不经过 FilesystemBackend；因此这里也必须先把账本的
    # Windows 盘符翻译成本机挂载点，否则 macOS 会把 `A:\\...` 当成相对文件名。
    candidate = normalized_path(path)
    if candidate.is_file():
        return str(candidate)
    matched = _case_insensitive_match(str(candidate.parent), candidate.name)
    if matched is not None:
        return str(candidate.parent / matched)
    return str(candidate)


def remap_managed_path(
    path: Path | str,
    current_root: Path,
    legacy_roots: Sequence[Path] = (),
) -> Path:
    """将拆分前的受控根映射到当前根，不接受 basename 搜索。"""
    candidate = normalized_path(path)
    current = normalized_path(current_root)
    if candidate == current or current in candidate.parents:
        return candidate
    for legacy_root in legacy_roots:
        legacy = normalized_path(legacy_root)
        try:
            relative = candidate.relative_to(legacy)
        except ValueError:
            continue
        return current / relative
    return candidate


@dataclass(frozen=True)
class StreamPlan:
    """协议层播放计划；来源层决定是否值得切到短分片。"""

    protocol: str
    mime_type: str
    segment_seconds: int | None = None
    reason: str = ""


class MediaNotFound(RuntimeError):
    pass


class MediaUnavailable(RuntimeError):
    pass


class MediaOffline(MediaUnavailable):
    """来源盘整体不可达（脱盘），不是这一个文件缺失。

    脱盘只影响挂在该盘上的资产：本地硬盘拔掉时，115/PikPak 的云端资产照常可播。
    """

    def __init__(self, asset_id: int, source: str):
        super().__init__(asset_id)
        self.asset_id = asset_id
        self.source = source


class FilesystemBackend:
    """原生文件 backend；路径授权、旧快照映射和存在性检查集中在这里。"""

    name = "filesystem"

    def __init__(
        self,
        allowed_roots: Sequence[Path],
        snapshot_root: Path,
        legacy_snapshot_roots: Sequence[Path] = (),
    ):
        self.allowed_roots = tuple(normalized_path(root) for root in allowed_roots)
        self.snapshot_root = normalized_path(snapshot_root)
        self.legacy_snapshot_roots = tuple(
            normalized_path(root) for root in legacy_snapshot_roots
        )

    def file_for(self, asset: MediaAsset, thumbnail: bool = False) -> Path:
        raw = asset.snapshot_path if thumbnail else asset.path
        if not raw:
            raise MediaUnavailable(asset.id)
        path = (
            remap_managed_path(raw, self.snapshot_root, self.legacy_snapshot_roots)
            if thumbnail
            else normalized_path(raw)
        )
        roots = (self.snapshot_root,) if thumbnail else self.allowed_roots
        if not any(within_root(path, root) for root in roots):
            self._raise_unavailable(asset.id, raw, thumbnail)
        if path.is_file():
            return path
        matched = _case_insensitive_match(str(path.parent), path.name)
        if matched is not None:
            return path.parent / matched
        self._raise_unavailable(asset.id, raw, thumbnail)

    def _raise_unavailable(self, asset_id: int, raw: str, thumbnail: bool) -> None:
        """来源盘整体不可达时报 MediaOffline，单个文件缺失仍报 MediaUnavailable。"""
        if not thumbnail and is_windows_path(raw):
            translated = translate_ledger_path(raw)
            source = PureWindowsPath(raw).drive
            if is_unmapped(translated):
                raise MediaOffline(asset_id, source)
            candidate = normalized_path(raw)
            for root in self.allowed_roots:
                if within_root(candidate, root):
                    if not root_online(root):
                        raise MediaOffline(asset_id, source)
                    break
        raise MediaUnavailable(asset_id)

    def source_status(self) -> tuple[dict[str, object], ...]:
        """当前授权根的在线状态；脱盘模式的判据只有这一份。"""
        return tuple(
            {"root": str(root), "online": root_online(root)} for root in self.allowed_roots
        )


class MediaEngine:
    """按 asset id 解析媒体文件。

    这里曾经是一层 backend 契约，为的是让 Stash 作为可关闭的 adapter 参与解析。
    2026-09-01 关掉 adapter 时它一并删掉：本机文件是唯一来源，多留一层间接
    只会让「谁决定了这个路径」变得不好回答。见 ADR-0021。
    """

    def __init__(self, repository: LedgerRepository, filesystem: FilesystemBackend):
        self.repository = repository
        self.filesystem = filesystem

    def asset(self, asset_id: int) -> MediaAsset:
        asset = self.repository.media_asset(asset_id)
        if asset is None:
            raise MediaNotFound(asset_id)
        return asset

    def file_for(self, asset_id: int, thumbnail: bool = False) -> Path:
        return self.filesystem.file_for(self.asset(asset_id), thumbnail=thumbnail)

    def stream_plan(self, asset_id: int, *, mode: str = "auto") -> StreamPlan:
        """远端挂载的 MP4 默认走标准 Range；HLS 只在显式要求时给出。见 ADR-0016。

        默认 HLS 会把 HEVC 用 `-c copy` 原样装进 MPEG-TS，而 Chromium 的 MSE 不支持
        TS 里的 HEVC（实测 `isTypeSupported('video/mp2t; codecs="hvc1…"')` 为 false）。
        数据能进缓冲、时间轴照走，却一帧都解不出来，于是是静默黑屏而不是报错。
        同一浏览器直接 Range 播放同一个文件可正常出帧。
        """
        asset = self.asset(asset_id)
        suffix = Path(asset.path or asset.name or "").suffix.lower()
        if (
            mode == "hls"
            and asset.location in {"115", "pikpak"}
            and suffix in {".mp4", ".m4v"}
            and asset.duration is not None
            and asset.duration > 0
        ):
            return StreamPlan(
                "hls",
                "application/vnd.apple.mpegurl",
                HLS_SEGMENT_SECONDS,
                "remote-mounted-file",
            )
        return StreamPlan("range", "video/mp4", reason="standard-http-range")
