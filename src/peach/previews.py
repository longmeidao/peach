from __future__ import annotations

import os
import re
import subprocess
import threading
from pathlib import Path

from PIL import Image, ImageOps

from .ffmpeg import FFmpegResolver
from .fsutil import atomic_path
from .media import remap_managed_path
from .repository import LedgerRepository


class PreviewUnavailable(RuntimeError):
    pass


#: 厂牌标识的变体后缀。取图、可用性判定、落盘三处必须认同一套后缀，否则会出现
#: 「只装了 `<key>.icon.img` 却被判成没有图」这种两边打架的结果。
LOGO_VARIANTS = ("icon", "logo")

#: 大位要的不是某个后缀，而是「这个厂牌手上最清晰的那份」，所以 `large` 是语义变体，
#: 不落盘。本库实测：`icon` 与 `logo` 只差分辨率不差形状（宽高相等，唯一的横向字标是
#: 几张 SVG），而 Prestige 的 `icon` 只有 42 px、MOODYZ 与 Wanz Factory 的只有 64 px，
#: 摆进 180 px 的索引大格就是一团糊；同时它们的裸文件分别有 632 / 403 / 238 px。
#: 按后缀选等于按名字猜清晰度，所以这里按文件本身的像素量选。
LOGO_LARGEST = "large"


def logo_key(studio: str) -> str:
    r"""厂牌标识的落盘名。

    `/logo` 取图、复核批准落地（`web_review._install_studio_logo`）和「这个厂牌有没
    有图」的可用性判定都按这个名字找文件，所以规则只能有一份。各写一遍正则的代价是
    任何一处收窄字符集或改长度上限，都会变成「装上了却取不到」或「说有图但回 404」。

    假名和汉字原样留在名字里。只留 ASCII 的话，非 ASCII 的每个字符都换成一个下划线，
    落盘名就只剩「几个字」这一个信息：129 个厂牌里 `プレステージ` 和 `ムーディーズ`
    都是 `______`，`シロウトTV` 和 `ラグジュTV` 都是 `____TV`，一共 12 组撞在一起。
    撞了不报错，后装的那张直接盖掉先装的，页面上就是 PRESTIGE 的位置挂着 MOODYZ 的牌子。
    `\w` 之外的标点仍然归一成下划线，长度上限不变。
    """
    return re.sub(r"[^\w-]", "_", studio, flags=re.UNICODE)[:60]


#: `/entity-image` 认得的实体种类。取图和可用性判定必须认同一份清单：这边多认一种，
#: 页面就会为一个必然 404 的地址出 `<img>`；少认一种，装好的图从此不显示。
ENTITY_IMAGE_KINDS = ("performer", "studio", "creator", "series", "agency")


def entity_image_key(kind: str, entity_id: int) -> str:
    """实体图的落盘名。

    和 `logo_key` 同一个道理：`/entity-image` 取图、复核批准落地
    （`web_review._install_performer_avatar`）和「这个实体有没有图」的可用性判定
    都按这个名字找文件，规则只能有一份。kind 也是名字的一部分——creator 实体写成
    `performer-<id>.img` 是永远读不到的。
    """
    return f"{kind}-{int(entity_id)}"


#: 预览生成的分片锁。一把模块级全局锁会让任何一个资产生成海报时，其他资产的
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

    同一目标同一把锁，锁内再判一次文件是否已存在：两个线程同时请求同一张图时，
    第二个直接返回第一个的结果，而不是再跑一遍 FFmpeg。落盘本身的安全由
    `fsutil.atomic_path` 负责，这把锁省的是重复的转码开销。
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
        #: 标识清晰度按 (路径, mtime, 字节数) 记住，换了文件自然算新键。大位每格一次
        #: 请求，不缓存就是一屏一百多次开图读头。
        self._logo_sharpness: dict[tuple[str, int, int], tuple[int, int]] = {}

    def poster(self, asset_id: int, cell: int = 4) -> Path:
        cell = max(0, min(8, cell))
        destination = self.poster_root / f"{asset_id}_{cell}.jpg"
        if destination.is_file():
            return destination
        source = self._snapshot(asset_id)
        ffmpeg = self._ffmpeg()
        col, row = cell % 3, cell // 3
        self.poster_root.mkdir(parents=True, exist_ok=True)
        with _generate_lock(destination):
            if destination.is_file():
                return destination
            with atomic_path(destination) as temporary:
                self._run([
                    str(ffmpeg), "-y", "-v", "error", "-i", str(source),
                    "-vf", f"crop=iw/3:ih/3:iw/3*{col}:ih/3*{row},scale='min(640,iw)':-2",
                    "-q:v", "4", str(temporary),
                ])
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

        小地方（筛选片、卡片、来源角标）要的是方形小标 `icon`。大位（索引页的厂牌大格、
        厂牌资料页那个 160px 的位置）要 `large`：按文件的像素量在这个厂牌的所有份里挑
        最清晰的一张，见 `LOGO_LARGEST`。但绝大多数厂牌只有一份图：任何变体都回落到
        `<safe>.img`，任何位置都照旧显示它。变体文件是 `<safe>.icon.img` /
        `<safe>.logo.img`，没有它们时行为和加这个参数之前一模一样。
        """
        safe = logo_key(studio)
        if not safe:
            raise PreviewUnavailable("empty studio")
        listing = list(self.logo_root.iterdir()) if self.logo_root.is_dir() else []
        if variant == LOGO_LARGEST:
            #: 顺序即同分时的偏好：字标、方标、裸文件。`max` 取第一个最大值，所以
            #: 三份一样清晰时拿到的仍是最贴合大位的那份。
            found = []
            for name in (f"{safe}.logo.img", f"{safe}.icon.img", f"{safe}.img"):
                path = self._logo_file(listing, name)
                if path is not None:
                    found.append(path)
            if not found:
                raise PreviewUnavailable("logo unavailable")
            best = max(found, key=self._logo_clarity)
            return best, self._logo_content_type(best)
        names = [f"{safe}.img"]
        if variant in LOGO_VARIANTS:
            # 认不出的 variant 不报错，按没传处理：页面可能是缓存下来的旧版本，
            # 为一个拼错的参数把图变成 404 只会让厂牌页平白缺图。
            names.insert(0, f"{safe}.{variant}.img")
        for name in names:
            path = self._logo_file(listing, name)
            if path is not None:
                return path, self._logo_content_type(path)
        raise PreviewUnavailable("logo unavailable")

    def _logo_file(self, listing: list[Path], name: str) -> Path | None:
        """标识目录里叫这个名字的文件；大小写不敏感，取不到返回 None。"""
        candidates = [self.logo_root / name]
        candidates.extend(path for path in listing if path.name.lower() == name.lower())
        for path in candidates:
            if path.is_file():
                return path
        return None

    def _logo_content_type(self, path: Path) -> str:
        """落盘时记在 `.ct` 边车里的类型；没有边车按 ico 处理，和加边车之前一致。"""
        sidecar = Path(str(path) + ".ct")
        if sidecar.is_file():
            detected = sidecar.read_text(encoding="utf-8").strip().split(";")[0]
            if detected:
                return detected
        return "image/x-icon"

    def _logo_clarity(self, path: Path) -> tuple[int, int]:
        """(是否矢量, 像素量)。矢量放多大都清晰，排在所有位图前面。

        读不出尺寸的位图记 0：那是 Pillow 不认的格式或坏文件，不能因为「面积未知」
        就把它排到真能量出 600 px 的那张前面。全都读不出时仍会出图——浏览器认得的
        格式比 Pillow 多，这一步只排序，不做可用性判定。
        """
        try:
            stat = path.stat()
        except OSError:
            return (0, 0)
        key = (str(path).casefold(), stat.st_mtime_ns, stat.st_size)
        measured = self._logo_sharpness.get(key)
        if measured is None:
            measured = self._measure_logo(path)
            self._logo_sharpness[key] = measured
        return measured

    def _measure_logo(self, path: Path) -> tuple[int, int]:
        if self._logo_content_type(path).startswith("image/svg"):
            return (1, 0)
        try:
            with Image.open(path) as image:
                width, height = image.size
        except Exception:
            return (0, 0)
        return (0, width * height)

    def entity_image(self, kind: str, entity_id: int) -> tuple[Path, str]:
        """返回已缓存的高清实体图；抓取与版权溯源由离线导入任务负责。"""
        if kind not in ENTITY_IMAGE_KINDS:
            raise PreviewUnavailable("invalid entity kind")
        path = self.avatar_root / f"{entity_image_key(kind, entity_id)}.img"
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
        # 并发请求同一张图时各写各的临时文件，最后谁替换都是同一张。
        with atomic_path(destination) as temporary:
            try:
                with Image.open(source) as opened:
                    image = ImageOps.exif_transpose(opened)
                    if image.mode not in {"RGB", "L"}:
                        image = image.convert("RGB")
                    image.thumbnail((self.width, self.width * 8), Image.LANCZOS)
                    image.save(temporary, "JPEG", quality=82, optimize=True)
            except (OSError, ValueError, Image.DecompressionBombError) as exc:
                raise PreviewUnavailable("photo thumbnail failed") from exc
        return destination
