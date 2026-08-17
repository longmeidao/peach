#!/usr/bin/env python3
"""全库关键帧接触表：可续跑、显式计费授权、产物落地后登记。"""
from __future__ import annotations

import argparse
import hashlib
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from peach.config import DATABASE_PATH, FFMPEG_DIR, GENERATED_DIR, LOG_DIR, STATE_DIR
from peach.ffmpeg import FFmpegResolver
from peach.jobs import (
    DiskGuard,
    DiskSpaceDenied,
    JobPolicyError,
    PidFileLock,
    SourceAccessPolicy,
    require_free_space,
)
from peach.media import resolve_case_insensitive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成视频关键帧接触表")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--location")
    parser.add_argument("--frames", type=int, default=9)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--min-free", type=float, default=40.0)
    parser.add_argument(
        "--disk-check-secs",
        type=float,
        default=20.0,
        help="运行期复查磁盘余量的间隔；0 表示每条都查",
    )
    parser.add_argument("--allow-metered", action="store_true")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--output-root", type=Path, default=GENERATED_DIR / "snapshots" / "cloud")
    parser.add_argument("--log-dir", type=Path, default=LOG_DIR)
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".sheets.lock")
    return parser


def output_path(output_root: Path, location: str, path: str) -> Path:
    digest = hashlib.sha1(path.encode("utf-8", "ignore")).hexdigest()[:16]
    directory = output_root / location / digest[:2]
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{digest}.jpg"


COLOR_OVERRIDE = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]

# 只有坏色彩元数据才值得用 bt709 覆盖重试。无条件重试会让网盘超时这类必然失败的文件
# 每帧都白跑第二次：单帧最坏耗时从 45 秒翻到 90 秒，9 帧就是 13.5 分钟。
COLOR_METADATA_ERROR = re.compile(
    r"(reserved|unsupported|invalid)[^\n]{0,60}(color|primaries|trc|space)"
    r"|(color|primaries|trc|space)[^\n]{0,60}(reserved|unsupported|invalid)",
    re.IGNORECASE,
)


def _capture_frame(ffmpeg: str, path: str, timestamp: float, destination: Path,
                   color_override: bool) -> tuple[bool, str]:
    """抽一帧，返回（是否成功, stderr）。stderr 用于判断值不值得重试。"""
    command = [ffmpeg, "-y", "-v", "error", "-rw_timeout", "8000000"]
    if color_override:
        # 部分网盘视频把色彩原色写成 reserved（非法值），swscale 会拒绝缩放；
        # 声明为 bt709 只是覆盖坏的元数据，不改动像素。
        command += COLOR_OVERRIDE
    command += [
        "-ss", f"{timestamp:.2f}", "-i", path, "-frames:v", "1",
        "-vf", "scale=480:-1", "-q:v", "4", str(destination),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, timeout=45)
    except subprocess.TimeoutExpired:
        return False, "ffmpeg timeout"
    ok = destination.is_file() and destination.stat().st_size > 1024
    return ok, (completed.stderr or b"").decode("utf-8", "replace")


def make_sheet(ffmpeg: str, path: str, duration: float, destination: Path, frames: int) -> bool:
    """输入端 seek 抽帧后调用 FFmpeg tile；不线性解码整片。"""
    if not duration or duration < 2:
        return False
    temporary = Path(tempfile.mkdtemp(prefix="sheet_"))
    try:
        captured: list[Path] = []
        for index in range(frames):
            timestamp = duration * (0.03 + 0.94 * (index + 0.5) / frames)
            frame = temporary / f"{index:02d}.jpg"
            ok, stderr = _capture_frame(ffmpeg, path, timestamp, frame, color_override=False)
            if not ok and COLOR_METADATA_ERROR.search(stderr):
                ok, _ = _capture_frame(ffmpeg, path, timestamp, frame, color_override=True)
            if ok:
                captured.append(frame)
        if len(captured) < 2:
            return False
        for index, frame in enumerate(captured):
            target = temporary / f"s{index:02d}.jpg"
            if frame != target:
                frame.replace(target)
        rows = (len(captured) + 2) // 3
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                ffmpeg, "-y", "-v", "error", "-i", str(temporary / "s%02d.jpg"),
                "-filter_complex", f"tile=3x{rows}", "-q:v", "4", str(destination),
            ],
            capture_output=True,
            timeout=60,
        )
        return destination.is_file() and destination.stat().st_size > 4096
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def run(args: argparse.Namespace) -> int:
    if args.workers < 1 or args.frames < 2 or args.limit < 0:
        raise SystemExit("workers 必须大于 0，frames 至少为 2，limit 不能为负数")
    resolver = FFmpegResolver(FFMPEG_DIR)
    ffmpeg = resolver.ffmpeg()
    if ffmpeg is None:
        raise RuntimeError("ffmpeg unavailable")
    require_free_space(Path("C:/"), args.min_free)
    source_sql, source_parameters = SourceAccessPolicy().sql_filter(
        args.location, args.allow_metered
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.log_dir / f"sheets-{time.strftime('%Y%m%d-%H%M%S')}.log"
    lock = threading.RLock()

    with log_path.open("w", encoding="utf-8", buffering=1) as log_file:
        def log(message: str) -> None:
            with lock:
                line = f"[{time.strftime('%H:%M:%S')}] {message}"
                print(line, flush=True)
                log_file.write(line + "\n")

        if args.allow_metered:
            log("已显式允许计费来源")
        connection = sqlite3.connect(args.db)
        sql = (
            "SELECT id,location,path,duration FROM asset WHERE medium='video' "
            "AND snapshot_path IS NULL AND location != 'online' AND duration > 2"
            + source_sql + " ORDER BY size DESC"
        )
        parameters: tuple[object, ...] = source_parameters
        if args.limit:
            sql += " LIMIT ?"
            parameters += (args.limit,)
        tasks = connection.execute(sql, parameters).fetchall()
        connection.close()
        total = len(tasks)
        log(f"待处理 {total:,} 个视频 workers={args.workers} frames={args.frames} 日志={log_path}")
        if not total:
            log("没有待处理项；可能需要先运行 probe")
            return 0

        pending: queue.Queue = queue.Queue()
        results: queue.Queue = queue.Queue()
        for task in tasks:
            pending.put(task)
        counters = {"done": 0, "failed": 0, "existing": 0}
        started = time.time()
        # 起跑线检查拦不住运行期把盘吃光的第三方缓存；这里边跑边看。
        guard = DiskGuard(Path("C:/"), args.min_free, args.disk_check_secs)
        stop = threading.Event()
        stop_reason: list[str] = []

        def worker() -> None:
            while not stop.is_set():
                try:
                    asset_id, location, path, duration = pending.get_nowait()
                except queue.Empty:
                    return
                destination = output_path(args.output_root, location, path)
                try:
                    if destination.is_file() and destination.stat().st_size > 4096:
                        results.put((str(destination), asset_id))
                        with lock:
                            counters["existing"] += 1
                    elif make_sheet(
                        str(ffmpeg.path), resolve_case_insensitive(path), duration,
                        destination, args.frames,
                    ):
                        results.put((str(destination), asset_id))
                    else:
                        with lock:
                            counters["failed"] += 1
                except Exception:
                    with lock:
                        counters["failed"] += 1
                finally:
                    with lock:
                        counters["done"] += 1
                        if counters["done"] % 100 == 0:
                            elapsed = time.time() - started
                            rate = counters["done"] / elapsed if elapsed else 0
                            eta = (total - counters["done"]) / rate / 3600 if rate else 0
                            log(f"{counters['done']:,}/{total:,} 失败 {counters['failed']} 已存在 {counters['existing']} 剩余 {eta:.1f} 小时")
                        try:
                            guard.check()
                        except JobPolicyError as exc:
                            if not stop.is_set():
                                stop_reason.append(str(exc))
                                log(f"[stop] {exc}")
                            stop.set()

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(args.workers)]
        for thread in threads:
            thread.start()

        connection = sqlite3.connect(args.db, timeout=60)
        buffer = []
        while any(thread.is_alive() for thread in threads) or not results.empty():
            try:
                buffer.append(results.get(timeout=2))
            except queue.Empty:
                pass
            if len(buffer) >= 50:
                connection.executemany("UPDATE asset SET snapshot_path=? WHERE id=?", buffer)
                connection.commit()
                buffer.clear()
        if buffer:
            connection.executemany("UPDATE asset SET snapshot_path=? WHERE id=?", buffer)
            connection.commit()
        elapsed = time.time() - started
        log(f"完成 {counters['done']:,}，失败 {counters['failed']}，已存在 {counters['existing']}，耗时 {elapsed/3600:.2f} 小时")
        connection.close()
        if stop_reason:
            # 已完成的部分都已入库；磁盘闸门中止不能报成正常完成，否则续跑决策会被误导。
            log(f"磁盘闸门中止：{stop_reason[0]}")
            return DiskSpaceDenied.exit_code
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with PidFileLock(args.lock):
            return run(args)
    except JobPolicyError as exc:
        print(f"[stop] {exc}")
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
