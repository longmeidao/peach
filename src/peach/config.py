import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("PEACH_DATA_ROOT", r"R:\Resources"))
INTAKE_ROOT = DATA_ROOT / "Intake"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


@dataclass(frozen=True)
class PeachSettings:
    db_path: Path = INTAKE_ROOT / "ledger.db"
    page_path: Path = PROJECT_ROOT / "web" / "index.html"
    token: str = ""
    legacy_module_path: Path = Path(__file__).with_name("compat_web.py")
    docs_enabled: bool = False
    allowed_media_roots: tuple[Path, ...] = (Path(r"R:\Media"), Path("B:/"), Path("A:/"))
    snapshot_root: Path = INTAKE_ROOT / "snapshots"
    poster_root: Path = INTAKE_ROOT / "posters"
    avatar_root: Path = INTAKE_ROOT / "avatars"
    logo_root: Path = INTAKE_ROOT / "logos"
    allow_legacy_stash_ffmpeg: bool = True
