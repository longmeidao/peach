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
    """统一二进制定位；Stash 私有目录只是显式、可关闭的迁移 fallback。"""

    def __init__(self, tools_dir: Path, allow_legacy_stash: bool = True):
        self.tools_dir = tools_dir
        self.allow_legacy_stash = allow_legacy_stash

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

        managed = self.tools_dir / "bin" / f"{executable}{suffix}"
        if managed.is_file():
            return BinaryChoice(managed.resolve(), "peach-managed")

        found = shutil.which(executable)
        if found:
            return BinaryChoice(Path(found).resolve(), "path")

        if self.allow_legacy_stash:
            local = Path(os.environ.get("LOCALAPPDATA", ""))
            root = local / "Stash" / "ffmpeg-btbn"
            matches = sorted(root.glob(f"*/bin/{executable}.exe"), reverse=True)
            if matches:
                return BinaryChoice(matches[0].resolve(), "legacy-stash")
        return None
