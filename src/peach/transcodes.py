from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .ffmpeg import FFmpegResolver


BROWSER_NATIVE_SUFFIXES = frozenset({".mp4", ".m4v", ".webm", ".ogv", ".ogg"})
DIRECT_MP4_PIXEL_FORMATS = frozenset({"yuv420p", "yuvj420p"})
TRANSCODE_TIMEOUT_SECONDS = 3600
PROBE_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class _MediaProfile:
    video_codec: str
    pixel_format: str
    audio_codec: str


@dataclass(frozen=True)
class _TranscodeAttempt:
    name: str
    command: tuple[str, ...]


class TranscodeUnavailable(RuntimeError):
    pass


class TranscodeCancelled(TranscodeUnavailable):
    pass


class TranscodeService:
    """Create immutable browser-playable MP4 cache entries without touching sources."""

    def __init__(
        self,
        resolver: FFmpegResolver,
        cache_root: Path,
        *,
        max_concurrent: int = 2,
        prefer_hardware: bool | None = None,
    ):
        self.resolver = resolver
        self.cache_root = cache_root
        # 当前生产机是 NVIDIA Windows。macOS 保持原来的软件路径，避免每次先跑两次
        # 必然失败的 CUDA/NVENC 命令；测试和后续平台适配可显式覆盖。
        self.prefer_hardware = os.name == "nt" if prefer_hardware is None else prefer_hardware
        self._locks: dict[int, list] = {}
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
            deadline = time.monotonic() + TRANSCODE_TIMEOUT_SECONDS
            last_detail = ""
            completed = False
            try:
                with self._slots:
                    self._raise_if_cancelled(session, registry)
                    profile = self._probe(source, session, registry, deadline)
                    for attempt in self._attempts(
                        choice.path, source, temporary, profile,
                    ):
                        temporary.unlink(missing_ok=True)
                        try:
                            returncode, _stdout, stderr = self._execute(
                                attempt.command,
                                session=session,
                                registry=registry,
                                deadline=deadline,
                                label=attempt.name,
                            )
                        except TranscodeCancelled:
                            raise
                        except (OSError, TranscodeUnavailable) as exc:
                            last_detail = f"{attempt.name}: {exc}"
                            if time.monotonic() >= deadline:
                                break
                            continue
                        if (returncode == 0 and temporary.is_file()
                                and temporary.stat().st_size):
                            temporary.replace(target)
                            completed = True
                            break
                        detail = (stderr or b"").decode("utf-8", "replace")[-1000:]
                        last_detail = f"{attempt.name}: {detail or 'ffmpeg failed'}"
                if not completed:
                    raise TranscodeUnavailable(last_detail or "ffmpeg failed")
            finally:
                temporary.unlink(missing_ok=True)

            for stale in self.cache_root.glob(f"{asset_id}-*.mp4"):
                if stale != target:
                    stale.unlink(missing_ok=True)
            return target, True

    def _probe(
        self, source: Path, session: str, registry, deadline: float,
    ) -> _MediaProfile | None:
        choice = self.resolver.ffprobe()
        if choice is None:
            return None
        command = (
            str(choice.path), "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,pix_fmt", "-of", "json", str(source),
        )
        try:
            returncode, stdout, _stderr = self._execute(
                command,
                session=session,
                registry=registry,
                deadline=min(deadline, time.monotonic() + PROBE_TIMEOUT_SECONDS),
                label="ffprobe",
                capture_stdout=True,
            )
        except TranscodeCancelled:
            raise
        except (OSError, TranscodeUnavailable):
            return None
        if returncode:
            return None
        try:
            streams = json.loads(stdout.decode("utf-8", "replace")).get("streams", ())
        except (AttributeError, json.JSONDecodeError):
            return None
        video = next((item for item in streams if item.get("codec_type") == "video"), {})
        audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
        codec = str(video.get("codec_name") or "").lower()
        if not codec:
            return None
        return _MediaProfile(
            video_codec=codec,
            pixel_format=str(video.get("pix_fmt") or "").lower(),
            audio_codec=str(audio.get("codec_name") or "").lower(),
        )

    def _attempts(
        self,
        ffmpeg: Path,
        source: Path,
        temporary: Path,
        profile: _MediaProfile | None,
    ) -> tuple[_TranscodeAttempt, ...]:
        prefix = (
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        )
        mapping = ("-map", "0:v:0", "-map", "0:a:0?", "-sn", "-dn")
        finish = ("-movflags", "+faststart", str(temporary))
        attempts: list[_TranscodeAttempt] = []

        if (profile is not None and profile.video_codec == "h264"
                and profile.pixel_format in DIRECT_MP4_PIXEL_FORMATS):
            audio = (
                ("-c:a", "copy")
                if profile.audio_codec in {"", "aac"}
                else ("-c:a", "aac", "-b:a", "160k")
            )
            attempts.append(_TranscodeAttempt(
                "video-copy",
                prefix + ("-i", str(source)) + mapping + ("-c:v", "copy") + audio + finish,
            ))

        fast_audio = (
            ("-c:a", "copy")
            if profile is not None and profile.audio_codec in {"", "aac"}
            else ("-c:a", "aac", "-b:a", "160k")
        )
        nvenc = (
            "-c:v", "h264_nvenc", "-preset", "p1", "-tune", "hq",
            "-rc", "vbr", "-cq", "21", "-b:v", "0",
        )
        if self.prefer_hardware:
            # CUDA surfaces stay on the GPU; scale_cuda also converts common 10-bit HEVC
            # inputs to NV12 so H.264 NVENC does not have to fall back to a CPU transfer.
            attempts.append(_TranscodeAttempt(
                "cuda-nvenc",
                prefix + (
                    "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
                    "-i", str(source),
                ) + mapping + ("-vf", "scale_cuda=format=nv12") + nvenc + fast_audio + finish,
            ))
            # Some codecs have no NVDEC path but can still keep the expensive encode on NVENC.
            attempts.append(_TranscodeAttempt(
                "nvenc",
                prefix + ("-i", str(source)) + mapping + nvenc + (
                    "-pix_fmt", "yuv420p",
                ) + fast_audio + finish,
            ))

        # Final compatibility path: preserve the previous encoder and always normalize audio.
        attempts.append(_TranscodeAttempt(
            "libx264",
            prefix + ("-i", str(source)) + mapping + (
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            ) + finish,
        ))
        return tuple(attempts)

    def _execute(
        self,
        command: tuple[str, ...],
        *,
        session: str,
        registry,
        deadline: float,
        label: str,
        capture_stdout: bool = False,
    ) -> tuple[int, bytes, bytes]:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        registered = False
        try:
            if registry is not None and session:
                registered = registry.register_process(session, process)
                if not registered:
                    process.kill()
                    process.communicate()
                    raise TranscodeCancelled(session)
            while True:
                try:
                    stdout, stderr = process.communicate(timeout=0.5)
                    break
                except subprocess.TimeoutExpired:
                    if registry is not None and session and registry.is_cancelled(session):
                        process.kill()
                        process.communicate()
                        raise TranscodeCancelled(session)
                    if time.monotonic() >= deadline:
                        process.kill()
                        process.communicate()
                        raise TranscodeUnavailable(f"{label} timed out")
            self._raise_if_cancelled(session, registry)
            return (
                process.returncode if process.returncode is not None else -1,
                stdout or b"",
                stderr or b"",
            )
        finally:
            if registered:
                registry.unregister_process(session, process)

    @staticmethod
    def _raise_if_cancelled(session: str, registry) -> None:
        if registry is not None and session and registry.is_cancelled(session):
            raise TranscodeCancelled(session)

    @contextmanager
    def _lock_for(self, asset_id: int):
        """同一 asset 的转码互斥；引用归零的条目随手清掉，长跑不再只增不减。

        清理之所以安全：任何等锁线程都先在 guard 里加过引用，持有者退出临界区、
        释放锁之后再减引用。减到零的那一刻不可能还有持有者或等待者，此时删除
        才不会让后来的线程拿到第二把锁绕过互斥。
        """
        with self._locks_guard:
            entry = self._locks.get(asset_id)
            if entry is None:
                entry = [threading.Lock(), 0]
                self._locks[asset_id] = entry
            entry[1] += 1
        try:
            with entry[0]:
                yield
        finally:
            with self._locks_guard:
                entry[1] -= 1
                if entry[1] <= 0:
                    self._locks.pop(asset_id, None)
