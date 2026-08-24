from __future__ import annotations

import os
import subprocess
import threading
import time
import uuid
from pathlib import Path

from .ffmpeg import FFmpegResolver


BROWSER_NATIVE_SUFFIXES = frozenset({".mp4", ".m4v", ".webm", ".ogv", ".ogg"})


class TranscodeUnavailable(RuntimeError):
    pass


class TranscodeCancelled(TranscodeUnavailable):
    pass


class TranscodeService:
    """Create immutable browser-playable MP4 cache entries without touching sources."""

    def __init__(
        self, resolver: FFmpegResolver, cache_root: Path, *, max_concurrent: int = 2,
    ):
        self.resolver = resolver
        self.cache_root = cache_root
        self._locks: dict[int, threading.Lock] = {}
        self._locks_guard = threading.Lock()
        self._slots = threading.Semaphore(max(1, max_concurrent))

    @staticmethod
    def needs_transcode(source: Path) -> bool:
        return source.suffix.lower() not in BROWSER_NATIVE_SUFFIXES

    def browser_path(
        self, asset_id: int, source: Path, *, session: str = "", registry=None,
    ) -> tuple[Path, bool]:
        if not self.needs_transcode(source):
            return source, False

        choice = self.resolver.ffmpeg()
        if choice is None:
            raise TranscodeUnavailable("ffmpeg unavailable")

        try:
            stat = source.stat()
        except OSError as exc:
            raise TranscodeUnavailable("source unavailable") from exc

        target = self.cache_root / f"{asset_id}-{stat.st_size}-{stat.st_mtime_ns}.mp4"
        if target.is_file() and target.stat().st_size:
            return target, True

        with self._lock_for(asset_id):
            if target.is_file() and target.stat().st_size:
                return target, True
            self.cache_root.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f"{target.stem}.{uuid.uuid4().hex}.tmp.mp4")
            command = [
                str(choice.path), "-hide_banner", "-loglevel", "error", "-nostdin",
                "-y", "-i", str(source),
                "-map", "0:v:0", "-map", "0:a:0?",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart", str(temporary),
            ]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            process = None
            registered = False
            try:
                with self._slots:
                    process = subprocess.Popen(
                        command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE, creationflags=creationflags,
                    )
                    if registry is not None and session:
                        registered = registry.register_process(session, process)
                        if not registered:
                            process.kill()
                            process.communicate()
                            raise TranscodeCancelled(session)
                    deadline = time.monotonic() + 3600
                    while True:
                        try:
                            _stdout, stderr = process.communicate(timeout=0.5)
                            break
                        except subprocess.TimeoutExpired:
                            if registry is not None and session and registry.is_cancelled(session):
                                process.kill()
                                process.communicate()
                                raise TranscodeCancelled(session)
                            if time.monotonic() >= deadline:
                                process.kill()
                                process.communicate()
                                raise TranscodeUnavailable("ffmpeg timed out")
                if process.returncode or not temporary.is_file() or not temporary.stat().st_size:
                    detail = (stderr or b"").decode("utf-8", "replace")[-1000:]
                    raise TranscodeUnavailable(detail or "ffmpeg failed")
                temporary.replace(target)
            except OSError as exc:
                raise TranscodeUnavailable("ffmpeg failed") from exc
            finally:
                if registered:
                    registry.unregister_process(session, process)
                temporary.unlink(missing_ok=True)

            for stale in self.cache_root.glob(f"{asset_id}-*.mp4"):
                if stale != target:
                    stale.unlink(missing_ok=True)
            return target, True

    def _lock_for(self, asset_id: int) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(asset_id, threading.Lock())
