"""按关键帧切 HLS 片段，避免挂载网盘承担整段 MP4 Range。"""
from __future__ import annotations

import asyncio
import os
import subprocess
import uuid
from pathlib import Path

from .ffmpeg import FFmpegResolver
from .mp4index import keyframe_seconds, segment_plan
from .streaming import StreamSessionRegistry

HLS_SEGMENT_SECONDS = 6
# 片段缓存上限。超了按最后访问时间淘汰；片段可再生，丢了只是重跑一次 FFmpeg。
DEFAULT_CACHE_BYTES = 2 << 30


class SegmentUnavailable(RuntimeError):
    pass


class SegmentCancelled(RuntimeError):
    pass


def build_hls_playlist(plan: list[tuple[float, float]], segment_url) -> str:
    """按真实分片计划生成 VOD 播放列表。

    时长必须写实际值。早先版本按 6 秒等分声明，而 `-c copy` 只能切在关键帧上，
    遇到关键帧间隔 8.33 秒的片源，目录说的和实际内容就完全对不上。
    """
    target = max(1, round(max(length for _, length in plan)))
    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        f"#EXT-X-TARGETDURATION:{target}",
        "#EXT-X-PLAYLIST-TYPE:VOD",
        "#EXT-X-MEDIA-SEQUENCE:0",
    ]
    for index, (_, length) in enumerate(plan):
        lines.extend((f"#EXTINF:{length:.3f},", str(segment_url(index))))
    lines.extend(("#EXT-X-ENDLIST", ""))
    return "\n".join(lines)


class HlsSegmentService:
    """按关键帧边界 remux 单个时间段，输出可缓存的 MPEG-TS。"""

    def __init__(
        self,
        resolver: FFmpegResolver,
        work_root: Path,
        segment_seconds: int = HLS_SEGMENT_SECONDS,
        max_concurrent: int | None = None,
        cache_bytes: int = DEFAULT_CACHE_BYTES,
    ):
        self.resolver = resolver
        self.work_root = work_root
        self.segment_seconds = segment_seconds
        self.cache_bytes = cache_bytes
        # 每个分片请求都会起一个 FFmpeg；播放器本身就并发预取，多设备同看能把机器打满。
        self._limit = max_concurrent or max(1, (os.cpu_count() or 4) // 2)
        self._semaphore: asyncio.Semaphore | None = None
        self._plans: dict[tuple, list[tuple[float, float]]] = {}

    def _gate(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._limit)
        return self._semaphore

    def fingerprint(self, source: Path) -> tuple:
        try:
            stat = source.stat()
        except OSError:
            return (str(source), 0, 0)
        return (str(source), stat.st_size, int(stat.st_mtime))

    def plan(self, source: Path, duration: float) -> list[tuple[float, float]] | None:
        """返回分片计划；读不到关键帧就返回 None，由调用方回退标准 Range。"""
        key = (*self.fingerprint(source), self.segment_seconds, round(duration, 3))
        cached = self._plans.get(key)
        if cached is not None:
            return cached or None
        keyframes = keyframe_seconds(source)
        result = segment_plan(keyframes, duration, self.segment_seconds) if keyframes else []
        if len(self._plans) > 256:
            self._plans.clear()
        self._plans[key] = result
        return result or None

    def cached_path(self, source: Path, asset_id: int, index: int) -> Path:
        _, size, mtime = self.fingerprint(source)
        return self.work_root / str(asset_id) / f"{size}-{mtime}-{self.segment_seconds}" / f"{index}.ts"

    def _evict(self) -> None:
        files = [item for item in self.work_root.rglob("*.ts") if item.is_file()]
        total = 0
        stats = []
        for item in files:
            try:
                stat = item.stat()
            except OSError:
                continue
            total += stat.st_size
            stats.append((stat.st_mtime, stat.st_size, item))
        if total <= self.cache_bytes:
            return
        for _, size, item in sorted(stats):
            try:
                item.unlink()
            except OSError:
                continue
            total -= size
            if total <= self.cache_bytes:
                return

    async def generate(
        self,
        source: Path,
        start: float,
        duration: float,
        *,
        asset_id: int,
        index: int,
        session: str,
        registry: StreamSessionRegistry,
    ) -> Path:
        target = self.cached_path(source, asset_id, index)
        if target.is_file() and target.stat().st_size:
            os.utime(target, None)      # 命中即续期，淘汰按最后访问时间
            return target
        choice = self.resolver.ffmpeg()
        if choice is None:
            raise SegmentUnavailable("ffmpeg unavailable")
        if registry.is_cancelled(session):
            raise SegmentCancelled(session)

        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f"{uuid.uuid4().hex}.tmp.ts")
        command = [
            str(choice.path), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            # 终点必须写成绝对时间戳。-copyts 保留原始时间轴后，-t 会被当成绝对结束时刻
            # 而不是片段时长，于是除了开头那一两段，每段的 -t 都早已过期，ffmpeg 以
            # 退出码 0、空 stderr 写出 0 字节，服务端只能报一句没有内容的 ffmpeg failed。
            "-ss", f"{start:.3f}", "-i", str(source), "-to", f"{start + duration:.3f}",
            "-map", "0:v:0", "-map", "0:a:0?", "-sn", "-dn", "-c", "copy",
            # 保留原始时间戳，让每段接着上一段走。早先用 -avoid_negative_ts make_zero
            # 把每段都归零，于是每段都自称从 0 秒开始，拖动进度条时容易跳错位置。
            "-copyts", "-muxdelay", "0", "-muxpreload", "0",
            "-f", "mpegts", str(temporary),
        ]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = None
        successful = False
        async with self._gate():
            try:
                try:
                    process = await asyncio.create_subprocess_exec(
                        *command,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=asyncio.subprocess.PIPE,
                        creationflags=creationflags,
                    )
                except OSError as exc:
                    raise SegmentUnavailable("ffmpeg failed to start") from exc

                if not registry.register_process(session, process):
                    _kill_process(process)
                    await process.communicate()
                    raise SegmentCancelled(session)

                try:
                    _, stderr = await process.communicate()
                finally:
                    registry.unregister_process(session, process)
                if (process.returncode != 0 or not temporary.is_file()
                        or not temporary.stat().st_size):
                    detail = (stderr or b"").decode("utf-8", "replace")[-1000:]
                    if registry.is_cancelled(session):
                        raise SegmentCancelled(session)
                    if not detail:
                        # FFmpeg 可以退出码 0、stderr 全空却写出 0 字节（时间窗取错就是
                        # 这样）。此时光报 "ffmpeg failed" 等于没报，把能观测到的都说出来。
                        size = temporary.stat().st_size if temporary.is_file() else None
                        detail = (
                            f"ffmpeg wrote no data: returncode={process.returncode} "
                            f"bytes={'缺文件' if size is None else size} "
                            f"ss={start:.3f} to={start + duration:.3f}"
                        )
                    raise SegmentUnavailable(detail)
                # 同一片段可能被并发请求各生成一次；原子改名让后到的覆盖同样内容即可。
                temporary.replace(target)
                successful = True
                self._evict()
                return target
            except asyncio.CancelledError:
                if process is not None:
                    _kill_process(process)
                    await process.communicate()
                    registry.unregister_process(session, process)
                raise
            finally:
                if not successful:
                    temporary.unlink(missing_ok=True)


def _kill_process(process) -> None:
    try:
        if process.returncode is None:
            process.kill()
    except (OSError, ProcessLookupError):
        pass
