"""可替换 Media Engine 契约。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from .repository import LedgerRepository
from .stash import StashClient


def normalized_path(path: Path | str) -> Path:
    """Windows 离线/云盘可能让 realpath 失败；启动时仍需保留安全的绝对路径边界。"""
    candidate = Path(path)
    try:
        return candidate.resolve()
    except OSError:
        return Path(os.path.abspath(os.fspath(candidate)))


def remap_managed_path(path: Path | str, current_root: Path,
                       legacy_roots: Sequence[Path] = ()) -> Path:
    """将数据迁移前的受控根路径映射到当前根，不接受任意 basename 搜索。"""
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


class MediaNotFound(RuntimeError):
    pass


class MediaUnavailable(RuntimeError):
    pass


class FilesystemMediaService:
    def __init__(self, repository: LedgerRepository, allowed_roots: Sequence[Path],
                 snapshot_root: Path, legacy_snapshot_roots: Sequence[Path] = ()):
        self.repository = repository
        self.allowed_roots = tuple(normalized_path(root) for root in allowed_roots)
        self.snapshot_root = normalized_path(snapshot_root)
        self.legacy_snapshot_roots = tuple(
            normalized_path(root) for root in legacy_snapshot_roots
        )

    def file_for(self, asset_id: int, thumbnail: bool = False) -> Path:
        asset = self.repository.media_asset(asset_id)
        if asset is None:
            raise MediaNotFound(asset_id)
        raw = asset.snapshot_path if thumbnail else asset.path
        if not raw:
            raise MediaUnavailable(asset_id)
        path = (remap_managed_path(raw, self.snapshot_root, self.legacy_snapshot_roots)
                if thumbnail else normalized_path(raw))
        roots = (self.snapshot_root,) if thumbnail else self.allowed_roots
        if not any(path == root or root in path.parents for root in roots):
            raise MediaUnavailable(asset_id)
        if not path.is_file():
            raise MediaUnavailable(asset_id)
        return path


class MediaBackend(Protocol):
    name: str

    def capabilities(self) -> MediaCapabilities: ...
    def stream_candidates(self, asset: Mapping[str, object]) -> Sequence[StreamCandidate]: ...


class FilesystemBackend:
    name = "filesystem"

    def __init__(self, allowed_roots: Sequence[Path]):
        self.allowed_roots = tuple(normalized_path(root) for root in allowed_roots)

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities(probe=True, preview=True, direct_stream=True)

    def stream_candidates(self, asset: Mapping[str, object]) -> Sequence[StreamCandidate]:
        raw = asset.get("path")
        if not raw:
            return ()
        path = normalized_path(str(raw))
        if not any(path == root or root in path.parents for root in self.allowed_roots):
            return ()
        return (StreamCandidate(self.name, "file", str(path)),)


class StashAdapter:
    """公开 GraphQL 协议 adapter；不复制 Stash 的 AGPL 实现。"""

    name = "stash"

    def __init__(self, client: StashClient | None = None):
        self.client = client or StashClient()

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities(probe=True, preview=True, direct_stream=True,
                                 transcode=True, search=True)

    def stream_candidates(self, asset: Mapping[str, object]) -> Sequence[StreamCandidate]:
        scene_id = asset.get("stash_scene_id")
        if not scene_id:
            return ()
        payload = self.client.graphql(
            "query($id:ID!){sceneStreams(id:$id){url mime_type label}}",
            {"id": str(scene_id)},
        )
        streams = payload.get("sceneStreams") or []
        return tuple(
            StreamCandidate(self.name, "http", str(item["url"]),
                            item.get("mime_type"), item.get("label"))
            for item in streams if item.get("url")
        )

class MediaEngine:
    def __init__(self, backends: Sequence[MediaBackend]):
        self.backends = tuple(backends)

    def stream_candidates(self, asset: Mapping[str, object]) -> tuple[StreamCandidate, ...]:
        candidates: list[StreamCandidate] = []
        for backend in self.backends:
            candidates.extend(backend.stream_candidates(asset))
        return tuple(candidates)
