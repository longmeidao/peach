import os
from dataclasses import dataclass
from pathlib import Path

from .platform import translate_ledger_path, translate_roots


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 运行数据目录按平台给默认值，两个平台各自持有一份可独立运行的 peach-data。
# `PEACH_DATA_ROOT` 覆盖默认值；worktree 也靠这个绝对路径找到同一份数据。
_WINDOWS_PROJECT_ROOT = Path.home() / "Desktop" / "peach"
_WINDOWS_DATA_ROOT = _WINDOWS_PROJECT_ROOT / "peach-data"
_POSIX_DATA_ROOT = Path.home() / "Desktop" / "lmd.gg" / "peach" / "peach-data"
DATA_ROOT = Path(
    os.environ.get("PEACH_DATA_ROOT")
    or (_WINDOWS_DATA_ROOT if os.name == "nt" else _POSIX_DATA_ROOT)
)
DATABASE_DIR = DATA_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "ledger.db"

# 共享副本只承担单写者复制传输，不是 Peach 直接运行的数据库。Windows 把它放在
# 内置盘专用目录并单独通过 SMB 暴露；macOS 按共享名挂载，不再依赖外置资源盘。
_WINDOWS_SHARED_ROOT = _WINDOWS_PROJECT_ROOT / "peach-sync"
_POSIX_SHARED_ROOT = Path("/Volumes/peach-sync")
SHARED_DATA_ROOT = Path(
    os.environ.get("PEACH_SHARED_DATA_ROOT")
    or (_WINDOWS_SHARED_ROOT if os.name == "nt" else _POSIX_SHARED_ROOT)
)
SHARED_DATABASE_PATH = SHARED_DATA_ROOT / "database" / "ledger.db"
GENERATED_DIR = DATA_ROOT / "generated"
SOURCES_DIR = DATA_ROOT / "sources"
STATE_DIR = DATA_ROOT / "state"
SECRETS_DIR = DATA_ROOT / "secrets"
LOG_DIR = DATA_ROOT / "logs"
ARCHIVE_DIR = DATA_ROOT / "archive"
INBOX_DIR = DATA_ROOT / "inbox"
TOOLS_DIR = DATA_ROOT / "tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"
TRANSCODE_DIR = GENERATED_DIR / "transcodes"
COVER_DIR = GENERATED_DIR / "covers"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"

# 媒体来源只用账本口径（Windows 盘符）声明一次，本机挂载点由 platform 层翻译：
# `R:` 本地硬盘、`B:` 115、`A:` PikPak；后两者在 macOS 上是 CloudDrive 的 macFUSE 挂载点。
# 键是 ledger 的 `asset.location`，脱盘模式按来源逐个判定，不是全局开关。
LOCATION_ROOT_DECLARATIONS: dict[str, str] = {
    "local": r"R:\media",
    "115": "B:/",
    "pikpak": "A:/",
}
MEDIA_ROOT_DECLARATIONS: tuple[str, ...] = tuple(LOCATION_ROOT_DECLARATIONS.values())

# 双机固定使用不同名字，避免同时运行时互相抢占 mDNS：macOS 是 peach.local，
# Windows 是 peach-win.local。`PEACH_MDNS_NAME` 仍可用于临时测试覆盖。
MDNS_NAME = os.environ.get("PEACH_MDNS_NAME") or ("peach-win" if os.name == "nt" else "peach")
MDNS_HOSTNAME = f"{MDNS_NAME}.local"
# 2026-08 仓库/数据拆分前写入 ledger 的旧快照根；运行时只做受控前缀重映射。
LEGACY_SNAPSHOT_DECLARATIONS: tuple[str, ...] = (r"R:\Resources\Intake\snapshots",)


@dataclass(frozen=True)
class PeachSettings:
    db_path: Path = DATABASE_PATH
    page_path: Path = PROJECT_ROOT / "web" / "index.html"
    vendor_path: Path = PROJECT_ROOT / "web" / "vendor"
    token: str = ""
    docs_enabled: bool = False
    mdns_enabled: bool = False
    mdns_name: str = "peach"
    mdns_port: int = 80
    mdns_address: str | None = None
    tls_enabled: bool = False
    # 本机挂载不到的来源不进授权列表，对应资产按「脱盘」处理而不是报错。
    allowed_media_roots: tuple[Path, ...] = translate_roots(MEDIA_ROOT_DECLARATIONS)
    snapshot_root: Path = GENERATED_DIR / "snapshots"
    legacy_snapshot_roots: tuple[Path, ...] = tuple(
        translate_ledger_path(root) for root in LEGACY_SNAPSHOT_DECLARATIONS
    )
    poster_root: Path = GENERATED_DIR / "posters"
    avatar_root: Path = GENERATED_DIR / "avatars"
    logo_root: Path = GENERATED_DIR / "logos"
    # 图片资产的缓存缩略图。云盘原图一张就有几 MB，回源一次之后瀑布流只读这里。
    photo_root: Path = GENERATED_DIR / "photo-thumbs"
    # 官方封套按番号存一份原图；4:3 与 16:9 两种版式共用同一文件，靠 CSS 取景。
    cover_root: Path = COVER_DIR
    ffmpeg_root: Path = FFMPEG_DIR
    transcode_root: Path = TRANSCODE_DIR
    stream_root: Path = GENERATED_DIR / "stream-segments"
    # 复核候选 CSV 的目录。走 settings 而不是模块常量，测试才不会读到真实的 generated 目录。
    candidate_root: Path = GENERATED_DIR
