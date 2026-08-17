"""Peach 的唯一 Media Engine 与可替换 backend 契约。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol, Sequence

from .repository import LedgerRepository, MediaAsset
from .segments import HLS_SEGMENT_SECONDS
from .stash import StashClient


def normalized_path(path: Path | str) -> Path:
    """Windows 离线/云盘可能让 realpath 失败；仍保留绝对路径安全边界。"""
    candidate = Path(path)
    try:
        return candidate.resolve()
    except OSError:
        return Path(os.path.abspath(os.fspath(candidate)))


@lru_cache(maxsize=512)
def _case_insensitive_match(parent_key: str, name_key: str) -> str | None:
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


def resolve_case_insensitive(path: Path | str) -> str:
    """返回可直接打开的实际路径：原路径不存在时按大小写不敏感匹配同目录文件。"""
    candidate = Path(path)
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
class MediaCapabilities:
    probe: bool = False
    preview: bool = False
    direct_stream: bool = False
    transcode: bool = False
    search: bool = False


@dataclass(frozen=True)
class StreamCandidate:
    backend: str
    mode: str
    uri: str
    mime_type: str | None = None
    label: str | None = None


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


class MediaBackend(Protocol):
    name: str

    def capabilities(self) -> MediaCapabilities: ...

    def stream_candidates(self, asset: MediaAsset) -> Sequence[StreamCandidate]: ...


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

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities(probe=True, preview=True, direct_stream=True)

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
        if not any(path == root or root in path.parents for root in roots):
            raise MediaUnavailable(asset.id)
        if path.is_file():
            return path
        matched = _case_insensitive_match(str(path.parent), path.name)
        if matched is not None:
            return path.parent / matched
        raise MediaUnavailable(asset.id)

    def stream_candidates(self, asset: MediaAsset) -> Sequence[StreamCandidate]:
        try:
            path = self.file_for(asset)
        except MediaUnavailable:
            return ()
        return (StreamCandidate(self.name, "file", str(path)),)


class StashAdapter:
    """公开 GraphQL 协议 adapter；不复制 Stash 的 AGPL 实现。"""

    name = "stash"

    def __init__(self, client: StashClient | None = None):
        self.client = client or StashClient()

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities(
            probe=True,
            preview=True,
            direct_stream=True,
            transcode=True,
            search=True,
        )

    def stream_candidates(self, asset: MediaAsset) -> Sequence[StreamCandidate]:
        scene_id = asset.external_id("stash")
        if not scene_id:
            return ()
        payload = self.client.graphql(
            "query($id:ID!){sceneStreams(id:$id){url mime_type label}}",
            {"id": scene_id},
        )
        streams = payload.get("sceneStreams") or []
        return tuple(
            StreamCandidate(
                self.name,
                "http",
                str(item["url"]),
                item.get("mime_type"),
                item.get("label"),
            )
            for item in streams
            if item.get("url")
        )


class MediaEngine:
    """按 asset id 统一解析原生文件与外部媒体 backend。"""

    def __init__(
        self,
        repository: LedgerRepository,
        filesystem: FilesystemBackend,
        adapters: Sequence[MediaBackend] = (),
    ):
        self.repository = repository
        self.filesystem = filesystem
        self.backends: tuple[MediaBackend, ...] = (filesystem, *adapters)

    def capabilities(self) -> dict[str, MediaCapabilities]:
        return {backend.name: backend.capabilities() for backend in self.backends}

    def asset(self, asset_id: int) -> MediaAsset:
        asset = self.repository.media_asset(asset_id)
        if asset is None:
            raise MediaNotFound(asset_id)
        return asset

    def file_for(self, asset_id: int, thumbnail: bool = False) -> Path:
        return self.filesystem.file_for(self.asset(asset_id), thumbnail=thumbnail)

    def stream_candidates(self, asset_id: int) -> tuple[StreamCandidate, ...]:
        asset = self.asset(asset_id)
        candidates: list[StreamCandidate] = []
        for backend in self.backends:
            candidates.extend(backend.stream_candidates(asset))
        return tuple(candidates)

    def stream_plan(self, asset_id: int) -> StreamPlan:
        """为挂载网盘选择可按时间定位的协议，其他来源保留标准 Range。"""
        asset = self.asset(asset_id)
        suffix = Path(asset.path or asset.name or "").suffix.lower()
        if (
            asset.location in {"115", "pikpak"}
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
