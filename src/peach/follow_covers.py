"""Generate cached high-resolution covers for remote follow videos.

Paheal exposes the original video and a 150/250px thumbnail, but no larger still.
The card therefore extracts the first decodable frame once and serves the cached JPEG.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import threading
from pathlib import Path

from .ffmpeg import FFmpegResolver
from .follow_store import FollowItemRow
from .follow_stream import FollowMediaResolver, FollowMediaUnavailable


class FollowCoverUnavailable(RuntimeError):
    pass


class FollowCoverService:
    """Create a bounded, cached still without exposing the upstream media URL."""

    def __init__(self, resolver: FFmpegResolver, media_resolver: FollowMediaResolver,
                 root: Path, *, timeout: float = 30.0):
        self.resolver = resolver
        self.media_resolver = media_resolver
        self.root = Path(root).resolve()
        self.timeout = timeout
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}
        # A visible grid can ask for several lazy images together. Two workers keep the
        # first screen responsive without turning the source CDN into a batch job.
        self._slots = threading.BoundedSemaphore(2)

    def cover(self, item: FollowItemRow) -> Path:
        if (item.provider != "rule34paheal"
                or str(item.metadata.get("media_kind") or "") != "video"):
            raise FollowCoverUnavailable("该条目不需要生成视频封面")
        try:
            target = self.media_resolver.resolve(item)
        except FollowMediaUnavailable as exc:
            raise FollowCoverUnavailable(str(exc)) from exc
        choice = self.resolver.ffmpeg()
        if choice is None:
            raise FollowCoverUnavailable("ffmpeg 不可用")

        fingerprint = hashlib.sha256(target.url.encode("utf-8")).hexdigest()[:16]
        destination = self.root / f"{item.id}-{fingerprint}.jpg"
        if destination.is_file():
            return destination
        lock = self._lock_for(destination.name)
        with lock:
            if destination.is_file():
                return destination
            self.root.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(
                f"{destination.stem}.{os.getpid()}.{threading.get_ident()}.tmp.jpg")
            command = [
                str(choice.path), "-y", "-v", "error",
                "-rw_timeout", "15000000", "-user_agent", "Peach follow cover",
            ]
            if target.referer:
                command.extend(("-referer", target.referer))
            command.extend((
                "-i", target.url, "-frames:v", "1",
                "-vf", "scale='min(1280,iw)':-2", "-update", "1",
                "-q:v", "4", str(temporary),
            ))
            try:
                with self._slots:
                    result = subprocess.run(
                        command, capture_output=True, timeout=self.timeout, check=False)
                if (result.returncode != 0 or not temporary.is_file()
                        or temporary.stat().st_size == 0):
                    raise FollowCoverUnavailable("视频封面生成失败")
                os.replace(temporary, destination)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise FollowCoverUnavailable("视频封面生成失败") from exc
            finally:
                temporary.unlink(missing_ok=True)
            # URL 变化时留下旧帧没有价值；只清理同一条目的旧缓存。
            for stale in self.root.glob(f"{item.id}-*.jpg"):
                if stale != destination:
                    stale.unlink(missing_ok=True)
            return destination

    def _lock_for(self, key: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(key, threading.Lock())
