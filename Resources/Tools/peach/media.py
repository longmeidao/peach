"""渐进式 Media Engine 契约。

阶段一只建立独立边界；现有生产串流仍由 rm-web.py 提供，避免半迁移。
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence


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


class MediaBackend(Protocol):
    name: str

    def capabilities(self) -> MediaCapabilities: ...
    def stream_candidates(self, asset: Mapping[str, object]) -> Sequence[StreamCandidate]: ...


class FilesystemBackend:
    name = "filesystem"

    def __init__(self, allowed_roots: Sequence[Path]):
        self.allowed_roots = tuple(root.resolve() for root in allowed_roots)

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities(probe=True, preview=True, direct_stream=True)

    def stream_candidates(self, asset: Mapping[str, object]) -> Sequence[StreamCandidate]:
        raw = asset.get("path")
        if not raw:
            return ()
        path = Path(str(raw)).resolve()
        if not any(path == root or root in path.parents for root in self.allowed_roots):
            return ()
        return (StreamCandidate(self.name, "file", str(path)),)


class StashAdapter:
    """公开 GraphQL 协议 adapter；不复制 Stash 的 AGPL 实现。"""

    name = "stash"

    def __init__(self, graphql_url: str = "http://127.0.0.1:9999/graphql", timeout: float = 10.0):
        self.graphql_url = graphql_url
        self.timeout = timeout

    def capabilities(self) -> MediaCapabilities:
        return MediaCapabilities(probe=True, preview=True, direct_stream=True,
                                 transcode=True, search=True)

    def stream_candidates(self, asset: Mapping[str, object]) -> Sequence[StreamCandidate]:
        scene_id = asset.get("stash_scene_id")
        if not scene_id:
            return ()
        payload = self._graphql(
            "query($id:ID!){sceneStreams(id:$id){url mime_type label}}",
            {"id": str(scene_id)},
        )
        streams = payload.get("sceneStreams") or []
        return tuple(
            StreamCandidate(self.name, "http", str(item["url"]),
                            item.get("mime_type"), item.get("label"))
            for item in streams if item.get("url")
        )

    def _graphql(self, query: str, variables: Mapping[str, object]) -> dict:
        body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = urllib.request.Request(
            self.graphql_url, data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.load(response)
        if result.get("errors"):
            raise RuntimeError(result["errors"])
        return result.get("data") or {}


class MediaEngine:
    def __init__(self, backends: Sequence[MediaBackend]):
        self.backends = tuple(backends)

    def stream_candidates(self, asset: Mapping[str, object]) -> tuple[StreamCandidate, ...]:
        candidates: list[StreamCandidate] = []
        for backend in self.backends:
            candidates.extend(backend.stream_candidates(asset))
        return tuple(candidates)
