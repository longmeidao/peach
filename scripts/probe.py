#!/usr/bin/env python3
"""全库 ffprobe：可续跑、单写者、显式计费授权。"""
from __future__ import annotations

import argparse
import json
import queue
import sqlite3
import subprocess
import threading
import time
from pathlib import Path

from peach.config import DATABASE_PATH, FFMPEG_DIR, LOG_DIR, STATE_DIR
from peach.ffmpeg import FFmpegResolver
from peach.jobs import JobPolicyError, PidFileLock, SourceAccessPolicy, require_free_space


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补全视频事实层和情境层")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--location")
    parser.add_argument("--interval", type=float, default=0.15)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--min-free", type=float, default=40.0)
    parser.add_argument("--allow-metered", action="store_true")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--log-dir", type=Path, default=LOG_DIR)
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".probe.lock")
    return parser


def context_fields(width: int, height: int, duration: float) -> tuple[str | None, str | None, str | None]:
    orientation = quality = length = None
    if width and height:
        orientation = "竖屏" if height > width else "横屏"
        longest = max(width, height)
        quality = (
            "4K" if longest >= 3000 else "2K" if longest >= 1900
            else "1080P" if longest >= 1300 else "720P" if longest >= 900
            else "低画质"
        )
    if duration:
        length = "速食" if duration < 300 else "短" if duration < 900 else "中" if duration < 2400 else "长"
    return length, orientation, quality


def probe_file(ffprobe: str, path: str) -> tuple:
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-rw_timeout", "8000000",
            "-select_streams", "v:0", "-show_entries",
            "format=duration:stream=width,height,codec_name,avg_frame_rate",
            "-of", "json", path,
        ],
        capture_output=True,
        timeout=20,
    )
    payload = json.loads(result.stdout or b"{}")
    duration = float((payload.get("format") or {}).get("duration") or 0)
    stream = (payload.get("streams") or [{}])[0]
    fps = 0.0
    try:
        numerator, denominator = (stream.get("avg_frame_rate") or "0/1").split("/")
        fps = float(numerator) / float(denominator) if float(denominator) else 0.0
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return (
        duration,
        int(stream.get("width") or 0),
        int(stream.get("height") or 0),
        stream.get("codec_name"),
        fps,
        None,
    )


def run(args: argparse.Namespace) -> int:
    if args.workers < 1 or args.interval < 0 or args.limit < 0:
        raise SystemExit("workers 必须大于 0；interval/limit 不能为负数")
    choice = FFmpegResolver(FFMPEG_DIR).ffprobe()
    if choice is None:
        raise RuntimeError("ffprobe unavailable")
    require_free_space(Path("C:/"), args.min_free)
    source_sql, source_parameters = SourceAccessPolicy().sql_filter(
        args.location, args.allow_metered
    )

    args.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.log_dir / f"probe-{time.strftime('%Y%m%d-%H%M%S')}.log"
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
            "SELECT id,path FROM asset WHERE medium='video' AND duration IS NULL "
            "AND location != 'online'" + source_sql + " ORDER BY size ASC"
        )
        parameters: tuple[object, ...] = source_parameters
        if args.limit:
            sql += " LIMIT ?"
            parameters += (args.limit,)
        tasks = connection.execute(sql, parameters).fetchall()
        connection.close()
        total = len(tasks)
        log(f"待处理 {total:,} 个视频 workers={args.workers} interval={args.interval}s 日志={log_path}")
        if not total:
            return 0

        pending: queue.Queue = queue.Queue()
        results: queue.Queue = queue.Queue()
        for task in tasks:
            pending.put(task)
        counters = {"done": 0, "failed": 0}
        started = time.time()

        def worker() -> None:
            while True:
                try:
                    asset_id, path = pending.get_nowait()
                except queue.Empty:
                    return
                try:
                    duration, width, height, codec, fps, audio = probe_file(str(choice.path), path)
                    length, orientation, quality = context_fields(width, height, duration)
                    results.put((duration, width, height, codec, fps, audio, length, orientation, quality, asset_id))
                except Exception:
                    results.put((-1, 0, 0, None, 0, 0, None, None, None, asset_id))
                    with lock:
                        counters["failed"] += 1
                finally:
                    with lock:
                        counters["done"] += 1
                        if counters["done"] % 50 == 0:
                            elapsed = time.time() - started
                            rate = counters["done"] / elapsed if elapsed else 0
                            eta = (total - counters["done"]) / rate / 60 if rate else 0
                            log(f"{counters['done']:,}/{total:,} 失败 {counters['failed']} {rate:.1f} 个/秒 剩余 {eta:.0f} 分钟")
                    time.sleep(args.interval)

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(args.workers)]
        for thread in threads:
            thread.start()

        connection = sqlite3.connect(args.db, timeout=120)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=120000")
        update = (
            "UPDATE asset SET duration=?,width=?,height=?,vcodec=?,fps=?,has_audio=?,"
            "ctx_length=?,ctx_orient=?,ctx_quality=? WHERE id=?"
        )
        buffer = []
        while any(thread.is_alive() for thread in threads) or not results.empty():
            try:
                buffer.append(results.get(timeout=2))
            except queue.Empty:
                pass
            if len(buffer) >= 25:
                connection.executemany(update, buffer)
                connection.commit()
                buffer.clear()
        if buffer:
            connection.executemany(update, buffer)
            connection.commit()
        elapsed = time.time() - started
        log(f"完成 {counters['done']:,} 个，失败 {counters['failed']}，耗时 {elapsed/60:.1f} 分钟")
        connection.close()
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
