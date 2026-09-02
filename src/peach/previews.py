from __future__ import annotations

import os
import re
import subprocess
import threading
from pathlib import Path

from PIL import Image, ImageOps

from .ffmpeg import FFmpegResolver
from .media import remap_managed_path
from .repository import LedgerRepository


class PreviewUnavailable(RuntimeError):
    pass


#: 预览生成的分片锁。原来是一把模块级全局锁：任何一个资产在生成海报，其他资产的
#: 头像和海报全得排队，而 `avatar()` 持锁要连跑 6 次 ffmpeg（每次 20 秒上限），
#: 最坏能把所有预览堵上两分钟。
#:
#: 分片而不是 per-asset 字典：字典要么只增不减（8 万个资产各留一把锁，永远不回收），
#: 要么就得处理「删锁时还有人在等」的竞态。分片是固定内存、零清理，代价只是偶尔
#: 两个不相干的目标撞进同一把锁——那只是少一次并行，不影响正确性。
_LOCK_STRIPES = 16
_GENERATE_LOCKS = tuple(threading.Lock() for _ in range(_LOCK_STRIPES))


def _generate_lock(destination: Path) -> threading.Lock:
    """按目标文件取锁：同一个目标一定拿同一把，不同目标大概率并行。

    同一目标同一把锁是这里的正确性要求——两个线程同时生成同一个文件，
    `os.replace` 会互相覆盖，而其中一个的临时文件可能已经被删掉了。
    """
    return _GENERATE_LOCKS[hash(str(destination)) % _LOCK_STRIPES]


class PreviewService:
    def __init__(self, repository: LedgerRepository, resolver: FFmpegResolver,
                 snapshot_root: Path, poster_root: Path, avatar_root: Path, logo_root: Path,
                 legacy_snapshot_roots: tuple[Path, ...] = ()):
        self.repository = repository
        self.resolver = resolver
        self.snapshot_root = snapshot_root.resolve()
        self.poster_root = poster_root.resolve()
        self.avatar_root = avatar_root.resolve()
        self.logo_root = logo_root.resolve()
        self.legacy_snapshot_roots = tuple(path.resolve() for path in legacy_snapshot_roots)

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
        with _generate_lock(destination):
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
        with _generate_lock(destination):
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

    def logo(self, studio: str, variant: str = "") -> tuple[Path, str]:
        """厂牌标识；`variant` 只在这个厂牌真的存了两份时才分岔。

        小地方（筛选片、卡片、来源角标）要的是方形小标 `icon`，厂牌页那个 160px
        大位要的是完整字标 `logo`——和社媒头像同一条判断。但绝大多数厂牌只有一份图：
        两个变体都回落到 `<safe>.img`，任何位置都照旧显示它。变体文件是新增的
        `<safe>.icon.img` / `<safe>.logo.img`，没有它们时行为和加这个参数之前一模一样。
        """
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]
        if not safe:
            raise PreviewUnavailable("empty studio")
        names = [f"{safe}.img"]
        if variant in {"icon", "logo"}:
            # 认不出的 variant 不报错，按没传处理：页面可能是缓存下来的旧版本，
            # 为一个拼错的参数把图变成 404 只会让厂牌页平白缺图。
            names.insert(0, f"{safe}.{variant}.img")
        listing = list(self.logo_root.iterdir()) if self.logo_root.is_dir() else []
        for name in names:
            candidates = [self.logo_root / name]
            candidates.extend(path for path in listing if path.name.lower() == name.lower())
            for path in candidates:
                if path.is_file():
                    content_type = "image/x-icon"
                    sidecar = Path(str(path) + ".ct")
                    if sidecar.is_file():
                        detected = sidecar.read_text(encoding="utf-8").strip().split(";")[0]
                        content_type = detected or content_type
                    return path, content_type
        raise PreviewUnavailable("logo unavailable")

    def entity_image(self, kind: str, entity_id: int) -> tuple[Path, str]:
        """返回已缓存的高清实体图；抓取与版权溯源由离线导入任务负责。"""
        if kind not in {"performer", "studio", "creator", "series"}:
            raise PreviewUnavailable("invalid entity kind")
        path = self.avatar_root / f"{kind}-{int(entity_id)}.img"
        if not path.is_file():
            raise PreviewUnavailable("entity image unavailable")
        content_type = "image/jpeg"
        sidecar = Path(str(path) + ".ct")
        if sidecar.is_file():
            detected = sidecar.read_text(encoding="utf-8").strip().split(";")[0]
            content_type = detected or content_type
        return path, content_type

    def _snapshot(self, asset_id: int) -> Path:
        asset = self.repository.media_asset(asset_id)
        if asset is None or not asset.snapshot_path:
            raise PreviewUnavailable("snapshot unavailable")
        path = remap_managed_path(
            asset.snapshot_path, self.snapshot_root, self.legacy_snapshot_roots,
        )
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


#: 瀑布流一列大约 300 CSS px，二倍屏取 640 够用；再大只是白付云盘流量。
PHOTO_THUMB_WIDTH = 640


class PhotoThumbnailService:
    """图片资产的缓存缩略图。

    图片和视频不一样：视频有接触印相可裁，图片只能读原图。云盘一张原图动辄几 MB，
    瀑布流一屏就是几十张，所以每张只回源一次、缩好存下来，之后都读本地缓存。
    授权由调用方的 MediaEngine 负责，这里只认已解析好的源文件路径。
    """

    def __init__(self, root: Path, width: int = PHOTO_THUMB_WIDTH):
        self.root = root.resolve()
        self.width = width

    def thumbnail(self, asset_id: int, source: Path) -> Path:
        destination = self.root / f"{asset_id}.jpg"
        if destination.is_file():
            return destination
        self.root.mkdir(parents=True, exist_ok=True)
        # 临时文件名带线程号：并发请求同一张图时各写各的，最后谁替换都是同一张。
        temporary = destination.with_name(
            f"{destination.stem}.{os.getpid()}.{threading.get_ident()}.tmp.jpg")
        try:
            with Image.open(source) as opened:
                image = ImageOps.exif_transpose(opened)
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                image.thumbnail((self.width, self.width * 8), Image.LANCZOS)
                image.save(temporary, "JPEG", quality=82, optimize=True)
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            temporary.unlink(missing_ok=True)
            raise PreviewUnavailable("photo thumbnail failed") from exc
        os.replace(temporary, destination)
        return destination
