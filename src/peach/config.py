import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("PEACH_DATA_ROOT", r"R:\peach-data"))
DATABASE_DIR = DATA_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "ledger.db"
GENERATED_DIR = DATA_ROOT / "generated"
SOURCES_DIR = DATA_ROOT / "sources"
STATE_DIR = DATA_ROOT / "state"
SECRETS_DIR = DATA_ROOT / "secrets"
LOG_DIR = DATA_ROOT / "logs"
ARCHIVE_DIR = DATA_ROOT / "archive"
INBOX_DIR = DATA_ROOT / "inbox"
TOOLS_DIR = DATA_ROOT / "tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


@dataclass(frozen=True)
class PeachSettings:
    db_path: Path = DATABASE_PATH
    page_path: Path = PROJECT_ROOT / "web" / "index.html"
    token: str = ""
    legacy_module_path: Path = Path(__file__).with_name("compat_web.py")
    docs_enabled: bool = False
    allowed_media_roots: tuple[Path, ...] = (Path(r"R:\media"), Path("B:/"), Path("A:/"))
    snapshot_root: Path = GENERATED_DIR / "snapshots"
    poster_root: Path = GENERATED_DIR / "posters"
    avatar_root: Path = GENERATED_DIR / "avatars"
    logo_root: Path = GENERATED_DIR / "logos"
    ffmpeg_root: Path = FFMPEG_DIR
