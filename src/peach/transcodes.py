from __future__ import annotations

import os
import subprocess
import threading
import uuid
from pathlib import Path

from .ffmpeg import FFmpegResolver


BROWSER_NATIVE_SUFFIXES = frozenset({".mp4", ".m4v", ".webm", ".ogv", ".ogg"})


class TranscodeUnavailable(RuntimeError):
    pass


class TranscodeService:
    """Create immutable browser-playable MP4 cache entries without touching sources."""

    def __init__(self, resolver: FFmpegResolver, cache_root: Path):
        self.resolver = resolver
        self.cache_root = cache_root
        self._locks: dict[int, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    @staticmethod
    def needs_transcode(source: Path) -> bool:
        return source.suffix.lower() not in BROWSER_NATIVE_SUFFIXES

    def browser_path(self, asset_id: int, source: Path) -> tuple[Path, bool]:
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
            try:
                result = subprocess.run(
                    command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE, timeout=3600, check=False,
                    creationflags=creationflags,
                )
                if result.returncode or not temporary.is_file() or not temporary.stat().st_size:
                    detail = result.stderr.decode("utf-8", "replace")[-1000:]
                    raise TranscodeUnavailable(detail or "ffmpeg failed")
                temporary.replace(target)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise TranscodeUnavailable("ffmpeg failed") from exc
            finally:
                temporary.unlink(missing_ok=True)

            for stale in self.cache_root.glob(f"{asset_id}-*.mp4"):
                if stale != target:
                    stale.unlink(missing_ok=True)
            return target, True

    def _lock_for(self, asset_id: int) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(asset_id, threading.Lock())
