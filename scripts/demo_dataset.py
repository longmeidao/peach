#!/usr/bin/env python3
"""生成一套 SFW 合成演示媒体库，供截图、教程与性能基准使用。

演示素材不取自真实馆藏：画面是 FFmpeg lavfi 的渐变、测试图与分形，海报是 Pillow 画的
几何图，作品、厂牌、系列、出演者和标签全部虚构。词表不与 `catalog_rules` 里的成人
词表相交，由 `tests/test_demo_dataset.py` 把守。

生成的目录能直接被 `peach scan` 与 `peach process` 消费：

- 番号型作品：`<番号>/<番号>.mp4` 配同名 `.nfo` 与 `-poster.jpg`。NFO 给全标题、出演者、
  厂牌、系列、发行日期与标签，`process` 因此不会向任何外部来源发请求，封面取本地海报。
- 创作者型作品：`<创作者>/<标题>.mp4` 配同名 `.png` 与 `.nfo`，没有番号，海报落到
  `posters/<id>_4.jpg`。
- 裸文件：只有视频，没有 NFO 与海报，用来演示「未识别到番号」与九宫格回退。
- 部分番号型作品带 `P/` 子目录的几张图片，成为实体页上的图集。

资料进账本要经复核：本地 NFO 候选一律人工判，复核页全选通过，或用
`scripts/apply_metadata_tags.py --source local_nfo` 按字段落地。

本脚本只写目标目录，不碰任何账本；`--video stub` 用占位字节代替真实编码，
给几十万条的规模测试用。
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import FFMPEG_DIR  # noqa: E402
from peach.ffmpeg import FFmpegResolver  # noqa: E402

MANIFEST_NAME = "demo-manifest.json"

#: 厂牌：番号前缀与显示名。前缀满足 `catalog_rules` 的厂牌番号形状（2 到 8 个字母加连字符）。
STUDIOS: tuple[tuple[str, str], ...] = (
    ("MIST", "晨雾映画"),
    ("COAST", "海岸线工作室"),
    ("VALE", "山谷工房"),
    ("AURA", "极光影像"),
    ("SEAS", "四季纪录"),
)
SERIES: tuple[str, ...] = ("城市漫步", "慢生活厨房", "山野四季", "手作日常", "夜景延时")
PERFORMERS: tuple[str, ...] = (
    "林晚晴", "顾清和", "苏念安", "陈知夏", "周见山", "何以宁", "白露", "江小满",
)
CREATORS: tuple[str, ...] = ("山间小屋", "城市步行者", "厨房观察员")
#: 内容标签。`横屏`、`竖屏`、`4K`、`1080P`、`60fps` 是 `catalog_rules` 的技术标签，
#: 其余是演示专用的自然与生活词。
CONTENT_TAGS: tuple[str, ...] = (
    "延时摄影", "自然风景", "城市夜景", "航拍", "料理", "手工", "旅行日记", "音乐现场",
)
TITLES: tuple[tuple[str, str], ...] = (
    ("山间晨雾", "Morning Mist in the Valley"),
    ("雨后街道", "Streets After Rain"),
    ("海岸线日落", "Sunset on the Coastline"),
    ("厨房里的周末", "A Weekend in the Kitchen"),
    ("木工台前", "At the Workbench"),
    ("城市夜景延时", "City Night Timelapse"),
    ("湖面航拍", "Lake From Above"),
    ("老街早市", "Morning Market on the Old Street"),
    ("雪后山径", "Mountain Trail After Snow"),
    ("阳台花园", "Balcony Garden"),
    ("车站的傍晚", "Evening at the Station"),
    ("河畔慢跑", "Jogging by the River"),
    ("露营的一夜", "One Night Camping"),
    ("面包出炉", "Bread Out of the Oven"),
    ("陶艺初学", "First Lesson in Pottery"),
    ("春日骑行", "Spring Ride"),
    ("图书馆的下午", "An Afternoon in the Library"),
    ("港口清晨", "Harbour at Dawn"),
    ("茶园采摘", "Picking in the Tea Garden"),
    ("屋顶星空", "Stars From the Rooftop"),
    ("旧货市场", "The Flea Market"),
    ("电车沿线", "Along the Tram Line"),
    ("木屋修缮", "Repairing the Cabin"),
    ("秋日落叶", "Autumn Leaves"),
)
PLOTS: tuple[str, ...] = (
    "一段安静的记录，镜头跟着光线从清晨走到傍晚。",
    "没有旁白，只有环境声与画面本身的节奏。",
    "固定机位与手持交替，记录一处地方一天的变化。",
    "以延时与慢镜头拼接的短片，适合当背景播放。",
)

#: lavfi 画面源。每一项是 (名字, 生成参数函数)，参数里 `{w}`、`{h}`、`{seed}` 由调用方填。
VISUAL_SOURCES: tuple[tuple[str, str], ...] = (
    ("gradients", "gradients=s={w}x{h}:r=24:speed=0.03:nb_colors=3:seed={seed}"),
    ("testsrc2", "testsrc2=s={w}x{h}:r=24"),
    ("mandelbrot", "mandelbrot=s={w}x{h}:r=24:maxiter=64"),
    ("life", "life=s={w}x{h}:r=24:mold=10:ratio=0.12:death_color=#2B3A67:life_color=#F2A65A:seed={seed}"),
)

LANDSCAPE = (1280, 720)
PORTRAIT = (720, 1280)
STUB_VIDEO_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1016


@dataclass
class DemoItem:
    kind: str
    path: str
    title: str
    original_title: str
    orientation: str
    duration: int
    visual_source: str
    code: str = ""
    studio: str = ""
    series: str = ""
    release_date: str = ""
    performers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    creator: str = ""
    nfo: str = ""
    poster: str = ""
    gallery: list[str] = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 SFW 合成演示媒体库")
    parser.add_argument("--output", type=Path, required=True, help="生成到这个目录（不存在则创建）")
    parser.add_argument("--count", type=int, default=24, help="作品数量")
    parser.add_argument("--seed", type=int, default=7, help="随机种子；同一种子生成同一套内容")
    parser.add_argument("--video", choices=("ffmpeg", "stub"), default="ffmpeg",
                        help="ffmpeg 真实编码短片；stub 只写占位字节，给规模测试用")
    parser.add_argument("--duration", type=int, default=8, help="每条短片的秒数（ffmpeg 模式）")
    parser.add_argument("--ffmpeg", type=Path, help="显式指定 ffmpeg 可执行文件")
    return parser


def plan_items(count: int, seed: int, duration: int) -> list[DemoItem]:
    """按种子排出全部作品的资料，不碰文件系统。"""
    if count < 1:
        raise ValueError("--count 至少为 1")
    rng = random.Random(seed)
    coded = max(1, round(count * 0.7))
    bare = 1 if count >= 6 else 0
    creator_made = max(0, count - coded - bare)
    if creator_made == 0 and count >= 3:
        coded -= 1
        creator_made = 1
    items: list[DemoItem] = []
    for index in range(count):
        title, original = TITLES[index % len(TITLES)]
        if index // len(TITLES):
            title = f"{title}（{index // len(TITLES) + 1}）"
            original = f"{original} {index // len(TITLES) + 1}"
        orientation = "竖屏" if rng.random() < 0.3 else "横屏"
        source_name, _ = VISUAL_SOURCES[rng.randrange(len(VISUAL_SOURCES))]
        tags = [orientation, rng.choice(("1080P", "4K", "60fps"))]
        tags += rng.sample(CONTENT_TAGS, k=2)
        base = dict(title=title, original_title=original, orientation=orientation,
                    duration=max(2, duration), visual_source=source_name, tags=tags)
        if index < coded:
            prefix, studio = STUDIOS[index % len(STUDIOS)]
            code = f"{prefix}-{index + 1:03d}"
            # 每三条番号型作品带一份四张图的图集，落在作品目录的 `P/` 子目录。
            gallery = [f"{code}/P/{number:03d}.jpg" for number in range(1, 5)] if index % 3 == 0 else []
            items.append(DemoItem(
                kind="coded", path=f"{code}/{code}.mp4", code=code, studio=studio,
                series=rng.choice(SERIES),
                release_date=f"{rng.choice((2025, 2026))}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
                performers=rng.sample(PERFORMERS, k=rng.choice((1, 1, 2))),
                nfo=f"{code}/{code}.nfo", poster=f"{code}/{code}-poster.jpg", gallery=gallery, **base))
        elif index < coded + creator_made:
            creator = CREATORS[index % len(CREATORS)]
            items.append(DemoItem(
                kind="creator", path=f"{creator}/{title}.mp4", creator=creator,
                nfo=f"{creator}/{title}.nfo", poster=f"{creator}/{title}.png", **base))
        else:
            items.append(DemoItem(kind="bare", path=f"未整理/{title}.mp4", **base))
    return items


def render_nfo(item: DemoItem) -> str:
    lines = ["<?xml version='1.0' encoding='utf-8'?>", "<movie>",
             f"  <title>{escape(item.title)}</title>",
             f"  <originaltitle>{escape(item.original_title)}</originaltitle>",
             f"  <plot>{escape(PLOTS[len(item.title) % len(PLOTS)])}</plot>",
             f"  <runtime>{max(1, item.duration // 60)}</runtime>",
             "  <generator>peach demo_dataset</generator>"]
    if item.code:
        lines += [f"  <num>{item.code}</num>",
                  f"  <uniqueid type=\"num\" default=\"true\">{item.code}</uniqueid>",
                  f"  <studio>{escape(item.studio)}</studio>",
                  f"  <set><name>{escape(item.series)}</name></set>",
                  f"  <premiered>{item.release_date}</premiered>"]
    for performer in item.performers:
        lines += ["  <actor>", f"    <name>{escape(performer)}</name>", "  </actor>"]
    lines += [f"  <tag>{escape(tag)}</tag>" for tag in item.tags]
    if item.poster:
        lines += ["  <art>", f"    <poster>{escape(Path(item.poster).name)}</poster>", "  </art>"]
    lines.append("</movie>")
    return "\n".join(lines) + "\n"


def draw_poster(destination: Path, item: DemoItem, rng: random.Random) -> None:
    """几何海报：渐变底、几个圆和条，角上印番号或英文标题。全程 ASCII 文字，不依赖 CJK 字体。"""
    from PIL import Image, ImageDraw, ImageFont

    width, height = (600, 900) if item.orientation == "竖屏" else (900, 600)
    top = tuple(rng.randint(40, 200) for _ in range(3))
    bottom = tuple(rng.randint(40, 200) for _ in range(3))
    mask = Image.linear_gradient("L").resize((width, height))
    image = Image.composite(Image.new("RGB", (width, height), bottom),
                            Image.new("RGB", (width, height), top), mask)
    draw = ImageDraw.Draw(image, "RGBA")
    for _ in range(rng.randint(3, 6)):
        radius = rng.randint(width // 8, width // 3)
        cx, cy = rng.randint(0, width), rng.randint(0, height)
        colour = tuple(rng.randint(120, 255) for _ in range(3)) + (rng.randint(70, 140),)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=colour)
    bar = rng.randint(height // 12, height // 6)
    draw.rectangle((0, height - bar, width, height), fill=(20, 20, 28, 200))
    label = item.code or item.original_title
    try:
        font = ImageFont.load_default(size=max(28, width // 14))
    except TypeError:  # 旧 Pillow 的默认字体不接受尺寸
        font = ImageFont.load_default()
    draw.text((width // 20, height - bar + bar // 5), label, fill=(240, 240, 240), font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG" if destination.suffix.lower() == ".png" else "JPEG", quality=90)


def ffmpeg_command(ffmpeg: str, item: DemoItem, destination: Path, seed: int) -> list[str]:
    width, height = PORTRAIT if item.orientation == "竖屏" else LANDSCAPE
    template = dict(VISUAL_SOURCES)[item.visual_source]
    source = template.format(w=width, h=height, seed=seed)
    return [ffmpeg, "-y", "-v", "error", "-f", "lavfi", "-i", source,
            "-t", str(item.duration), "-an", "-c:v", "libx264", "-preset", "ultrafast",
            "-crf", "34", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination)]


def write_video(ffmpeg: str | None, item: DemoItem, destination: Path, seed: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if ffmpeg is None:
        destination.write_bytes(STUB_VIDEO_BYTES)
        return
    result = subprocess.run(ffmpeg_command(ffmpeg, item, destination, seed),
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=300)
    if result.returncode != 0 or not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg 生成 {destination.name} 失败：{result.stderr.strip()[:300]}")


def generate(output: Path, *, count: int, seed: int, video: str, duration: int,
             ffmpeg: str | None = None, report=lambda line: None) -> list[DemoItem]:
    """把整套演示库写进 `output`，返回作品清单（同时落成 `demo-manifest.json`）。"""
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if video == "ffmpeg" and ffmpeg is None:
        raise RuntimeError("需要 ffmpeg 才能编码短片；装好 ffmpeg，或改用 --video stub")
    items = plan_items(count, seed, duration)
    rng = random.Random(seed ^ 0x5EED)
    # 规模测试里几十万张图逐张画太慢：占位模式下每种扩展名只画第一张，其余复制。
    templates: dict[str, Path] = {}

    def picture(destination: Path) -> None:
        template = templates.get(destination.suffix.lower())
        if video == "stub" and template is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(template, destination)
            return
        draw_poster(destination, item, rng)
        templates.setdefault(destination.suffix.lower(), destination)

    started = time.time()
    for index, item in enumerate(items, 1):
        target = output / item.path
        write_video(ffmpeg if video == "ffmpeg" else None, item, target, seed + index)
        if item.nfo:
            (output / item.nfo).write_text(render_nfo(item), encoding="utf-8")
        if item.poster:
            picture(output / item.poster)
        for photo in item.gallery:
            picture(output / photo)
        if index % 10 == 0 or index == len(items):
            report(f"  {time.time() - started:5.0f}s  {index}/{len(items)}")
    manifest = dict(seed=seed, count=count, video=video, generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                    items=[asdict(item) for item in items])
    (output / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def next_steps(output: Path) -> str:
    """接下来怎么让 Peach 看见这套库。按当前平台给出设置文件里要写的行。"""
    resolved = output.resolve()
    # TOML 单引号字面串不转义，Windows 路径里的反斜杠照原样写一个。
    if sys.platform == "win32":
        settings = ["[media.locations]", f"local = '{resolved}'"]
    else:
        settings = ["[media.locations]", "local = 'R:\\peach-demo'", "", "[media.mounts]",
                    f"local = '{resolved.as_posix()}'"]
    return "\n".join([
        "下一步：",
        "1. 建一个演示数据根：peach init --data-root <目录> --no-input",
        "2. 在该数据根的设置文件里声明来源根：",
        *(f"     {line}" for line in settings),
        "3. peach scan local，再 peach process；候选在复核页全选通过，或按字段跑",
        "     scripts/apply_metadata_tags.py <候选 CSV> --db <账本> --source local_nfo --field <字段> --apply --backup <备份>",
        "4. 要卡片有九宫格就再跑 scripts/probe.py 与 scripts/sheets.py；然后 peach serve 截图。",
        f"清单：{resolved / MANIFEST_NAME}",
    ])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ffmpeg: str | None = None
    if args.video == "ffmpeg":
        if args.ffmpeg is not None:
            ffmpeg = str(args.ffmpeg)
        else:
            choice = FFmpegResolver(FFMPEG_DIR).ffmpeg()
            ffmpeg = str(choice.path) if choice else None
    try:
        items = generate(args.output, count=args.count, seed=args.seed, video=args.video,
                         duration=args.duration, ffmpeg=ffmpeg, report=lambda line: print(line, flush=True))
    except (RuntimeError, ValueError) as error:
        print(f"✗ {error}")
        return 2
    kinds = {kind: sum(1 for item in items if item.kind == kind) for kind in ("coded", "creator", "bare")}
    print(f"✓ 生成 {len(items)} 条：番号型 {kinds['coded']}、创作者型 {kinds['creator']}、裸文件 {kinds['bare']}")
    print(next_steps(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
