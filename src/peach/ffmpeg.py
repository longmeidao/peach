from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BinaryChoice:
    path: Path
    source: str


class FFmpegResolver:
    """Resolve explicit, Peach-managed, or PATH binaries without backend coupling."""

    def __init__(self, managed_root: Path):
        self.managed_root = managed_root

    def ffmpeg(self) -> BinaryChoice | None:
        return self._resolve("ffmpeg", "PEACH_FFMPEG")

    def ffprobe(self) -> BinaryChoice | None:
        return self._resolve("ffprobe", "PEACH_FFPROBE")

    def _resolve(self, executable: str, env_name: str) -> BinaryChoice | None:
        suffix = ".exe" if os.name == "nt" else ""
        configured = os.environ.get(env_name)
        if configured:
            path = Path(configured).expanduser()
            if path.is_file():
                return BinaryChoice(path.resolve(), "environment")

        managed = self.managed_root / "bin" / f"{executable}{suffix}"
        if managed.is_file():
            return BinaryChoice(managed.resolve(), "peach-managed")

        found = shutil.which(executable)
        if found:
            return BinaryChoice(Path(found).resolve(), "path")

        return None
