"""Generate cached high-resolution covers for remote follow videos.

Paheal exposes the original video and a 150/250px thumbnail, but no larger still.
The card therefore extracts the first non-black decodable frame once and serves the
cached JPEG.
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


# FFmpeg's blackframe filter exports ``lavfi.blackframe.pblack`` only when the
# configured amount is reached.  Setting amount=0 makes that percentage available
# on every frame; metadata/select can then drop frames that are at least 98% black.
# Scan at most the opening 30 seconds so an all-black/broken video still reaches the
# existing low-resolution fallback promptly.
FOLLOW_COVER_SCAN_SECONDS = 30
FOLLOW_COVER_FILTER = (
    "blackframe=amount=0:threshold=32,"
    "metadata=select:key=lavfi.blackframe.pblack:value=98:function=less,"
    "scale='min(1280,iw)':-2"
)
_CACHE_VERSION = "nonblack-v1"

#: 取不到图时回的占位图。以前 `/follow-cover` 在这里 302 到上游缩略图，等于把上游
#: 主机和地址交回浏览器——而这个端点存在的全部理由就是不让它外露。占位图内联成
#: SVG：不占磁盘、不用打包资源，也不会因为文件缺失再失败一次。
#: 图里不写字：这一层不知道界面语言，画一个中性的播放三角就够。
PLACEHOLDER_CONTENT_TYPE = "image/svg+xml"
PLACEHOLDER_IMAGE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 90">'
    '<rect width="160" height="90" fill="#1f1f22"/>'
    '<path d="M68 33 100 45 68 57 Z" fill="#4c4c52"/>'
    '</svg>'
).encode("utf-8")


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

        fingerprint = hashlib.sha256(
            f"{_CACHE_VERSION}\0{target.url}".encode("utf-8")
        ).hexdigest()[:16]
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
                "-t", str(FOLLOW_COVER_SCAN_SECONDS), "-i", target.url,
                "-frames:v", "1", "-vf", FOLLOW_COVER_FILTER, "-update", "1",
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

    #: 同时追踪多少把生成锁。键是带指纹的缓存文件名，条目一多、URL 一变就再加一条，
    #: 原来只增不减：进程活多久它就长多久。超过上限就丢掉当前没人持有的键——丢锁最
    #: 坏只是让两次并发生成各跑一遍 ffmpeg，`os.replace` 仍是原子的，不会出错图。
    MAX_TRACKED_LOCKS = 256

    def _lock_for(self, key: str) -> threading.Lock:
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                if len(self._locks) >= self.MAX_TRACKED_LOCKS:
                    for name, tracked in list(self._locks.items()):
                        if not tracked.locked():
                            del self._locks[name]
                lock = self._locks[key] = threading.Lock()
            return lock
