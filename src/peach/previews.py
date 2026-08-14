from __future__ import annotations

import os
import re
import subprocess
import threading
from pathlib import Path

from .ffmpeg import FFmpegResolver
from .repository import LedgerRepository


class PreviewUnavailable(RuntimeError):
    pass


_GENERATE_LOCK = threading.Lock()


class PreviewService:
    def __init__(self, repository: LedgerRepository, resolver: FFmpegResolver,
                 snapshot_root: Path, poster_root: Path, avatar_root: Path, logo_root: Path):
        self.repository = repository
        self.resolver = resolver
        self.snapshot_root = snapshot_root.resolve()
        self.poster_root = poster_root.resolve()
        self.avatar_root = avatar_root.resolve()
        self.logo_root = logo_root.resolve()

    def poster(self, asset_id: int, cell: int = 4) -> Path:
        cell = max(0, min(8, cell))
        destination = self.poster_root / f"{asset_id}_{cell}.jpg"
        if destination.is_file():
            return destination
        source = self._snapshot(asset_id)
        ffmpeg = self._ffmpeg()
        col, row = cell % 3, cell // 3
        self.poster_root.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.stem + ".tmp.jpg")
        with _GENERATE_LOCK:
            if destination.is_file():
                return destination
            self._run([
                str(ffmpeg), "-y", "-v", "error", "-i", str(source),
                "-vf", f"crop=iw/3:ih/3:iw/3*{col}:ih/3*{row},scale='min(640,iw)':-2",
                "-q:v", "4", str(temporary),
            ])
            os.replace(temporary, destination)
        return destination

    def avatar(self, asset_id: int) -> Path:
        destination = self.avatar_root / f"{asset_id}.jpg"
        if destination.is_file():
            return destination
        source = self._snapshot(asset_id)
        ffmpeg = self._ffmpeg()
        self.avatar_root.mkdir(parents=True, exist_ok=True)
        candidates: list[tuple[Path, float]] = []
        with _GENERATE_LOCK:
            if destination.is_file():
                return destination
            try:
                for col, row in ((1, 1), (0, 0), (1, 2), (2, 0), (0, 2), (2, 2)):
                    temporary = destination.with_name(f"{destination.stem}.{col}{row}.tmp.jpg")
                    self._run([
                        str(ffmpeg), "-y", "-v", "error", "-i", str(source),
                        "-vf", f"crop=iw/3:ih/3:iw/3*{col}:ih/3*{row},"
                               "scale=160:160:force_original_aspect_ratio=increase,crop=160:160",
                        "-q:v", "4", str(temporary),
                    ])
                    try:
                        raw = subprocess.run(
                            [str(ffmpeg), "-v", "error", "-i", str(temporary), "-vf", "scale=1:1",
                             "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                            capture_output=True, timeout=20, check=False,
                        ).stdout
                    except (OSError, subprocess.TimeoutExpired):
                        raw = b""
                    brightness = float(raw[0]) if raw else 0.0
                    candidates.append((temporary, brightness))
                    if brightness >= 60:
                        break
                if not candidates:
                    raise PreviewUnavailable("avatar generation failed")
                best, brightness = max(candidates, key=lambda item: item[1])
                if brightness < 12:
                    raise PreviewUnavailable("snapshot is too dark")
                os.replace(best, destination)
            finally:
                for path, _ in candidates:
                    if path.exists() and path != destination:
                        path.unlink(missing_ok=True)
        return destination

    def logo(self, studio: str) -> tuple[Path, str]:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]
        if not safe:
            raise PreviewUnavailable("empty studio")
        candidates = [self.logo_root / f"{safe}.img"]
        if self.logo_root.is_dir():
            target = f"{safe}.img".lower()
            candidates.extend(path for path in self.logo_root.iterdir() if path.name.lower() == target)
        for path in candidates:
            if path.is_file():
                content_type = "image/x-icon"
                sidecar = Path(str(path) + ".ct")
                if sidecar.is_file():
                    detected = sidecar.read_text(encoding="utf-8").strip().split(";")[0]
                    content_type = detected or content_type
                return path, content_type
        raise PreviewUnavailable("logo unavailable")

    def _snapshot(self, asset_id: int) -> Path:
        asset = self.repository.media_asset(asset_id)
        if asset is None or not asset.snapshot_path:
            raise PreviewUnavailable("snapshot unavailable")
        path = Path(asset.snapshot_path).resolve()
        if not (path == self.snapshot_root or self.snapshot_root in path.parents) or not path.is_file():
            raise PreviewUnavailable("snapshot unavailable")
        return path

    def _ffmpeg(self) -> Path:
        choice = self.resolver.ffmpeg()
        if choice is None:
            raise PreviewUnavailable("ffmpeg unavailable")
        return choice.path

    @staticmethod
    def _run(command: list[str]) -> None:
        try:
            result = subprocess.run(command, capture_output=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            Path(command[-1]).unlink(missing_ok=True)
            raise PreviewUnavailable("ffmpeg generation failed") from exc
        if result.returncode != 0 or not Path(command[-1]).is_file():
            Path(command[-1]).unlink(missing_ok=True)
            raise PreviewUnavailable("ffmpeg generation failed")
