import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .platform import translate_ledger_path, translate_roots


def _project_root(module_file=__file__, bundle_root=None) -> Path:
    """源码树保留 `src/` 层；PyInstaller 的资源直接落在 `_MEIPASS`。"""
    return (Path(bundle_root) if bundle_root is not None
            else Path(module_file).resolve().parents[2])


PROJECT_ROOT = _project_root(bundle_root=getattr(sys, "_MEIPASS", None))

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

# macOS 重启后不会自动挂回这个 SMB 共享，`plan()` 于是把本机的日常状态判成 offline。
# 托盘按下面的坐标补挂一次，所以主机与账号必须是配置项而不是散在代码里的字面量：
# 家里的 IP 由 DHCP 分配，钉死总有失效的一天，主机名一律走 Windows 那台的 mDNS 名。
# 账号要和钥匙串里已有的那条记录同名——服务端拒绝 guest，匿名挂载不会成功。
_WINDOWS_MDNS_NAME = "peach-win"
SHARED_SMB_HOST = os.environ.get("PEACH_SHARED_SMB_HOST") or f"{_WINDOWS_MDNS_NAME}.local"
SHARED_SMB_SHARE = os.environ.get("PEACH_SHARED_SMB_SHARE") or _POSIX_SHARED_ROOT.name
SHARED_SMB_USER = os.environ.get("PEACH_SHARED_SMB_USER") or "peachsync"
GENERATED_DIR = DATA_ROOT / "generated"
SOURCES_DIR = DATA_ROOT / "sources"
STATE_DIR = DATA_ROOT / "state"
SECRETS_DIR = DATA_ROOT / "secrets"
LOG_DIR = DATA_ROOT / "logs"
ARCHIVE_DIR = DATA_ROOT / "archive"
INBOX_DIR = DATA_ROOT / "inbox"
TOOLS_DIR = DATA_ROOT / "tools"
REVIEW_DIR = DATA_ROOT / "review"
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
MDNS_NAME = os.environ.get("PEACH_MDNS_NAME") or (
    _WINDOWS_MDNS_NAME if os.name == "nt" else "peach")
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
    # reader 只从 writer 的严格 CA HTTPS 镜像复核 JSON；不复制候选 CSV，更不放宽写入闸门。
    # Windows 日常入口固定发布 192.168.50.162；地址变化时可显式覆盖。
    review_writer_origin: str = os.environ.get(
        "PEACH_REVIEW_WRITER_ORIGIN",
        "https://192.168.50.162" if os.name != "nt" else "",
    )
    review_writer_ca: Path = SECRETS_DIR / "tls" / "peach-local-ca.crt"
    review_mirror_cache: Path = REVIEW_DIR / "writer-review.json"
    # macOS LaunchAgent 的 Python 可能没有 Local Network 权限；只经本机 Stash 代理兜底。
    review_writer_proxy: str = os.environ.get(
        "PEACH_REVIEW_WRITER_PROXY",
        "http://127.0.0.1:7890" if sys.platform == "darwin" else "",
    )
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
    taste_history_store: Path = SOURCES_DIR / "taste-history" / "history.sqlite"
    taste_history_import_root: Path = SOURCES_DIR / "taste-history" / "imports"
    taste_history_output_root: Path = DATA_ROOT / "review" / "taste-history"
    taste_history_manifest: Path = STATE_DIR / "taste-history" / "manifest.json"
    # 自动追更频率是本机运行偏好，不属于 ledger 真相。
    follow_state_root: Path = STATE_DIR
