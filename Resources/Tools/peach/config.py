from dataclasses import dataclass
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PeachSettings:
    db_path: Path = Path(r"R:\Resources\Intake\ledger.db")
    page_path: Path = TOOLS_DIR / "rm-web.html"
    token: str = ""
    legacy_module_path: Path = TOOLS_DIR / "rm-web.py"
    docs_enabled: bool = False
    allowed_media_roots: tuple[Path, ...] = (Path("R:/"), Path("B:/"), Path("A:/"))
    snapshot_root: Path = Path(r"R:\Resources\Intake\snapshots")
    poster_root: Path = Path(r"R:\Resources\Intake\posters")
    avatar_root: Path = Path(r"R:\Resources\Intake\avatars")
    logo_root: Path = Path(r"R:\Resources\Intake\logos")
    allow_legacy_stash_ffmpeg: bool = True
