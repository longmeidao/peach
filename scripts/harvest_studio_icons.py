"""给「只有宽幅字标」和「一张图都没有」的厂牌补标识，出 `icon` 与 `logo` 两个变体。

已安装的厂牌图里有一部分源图是宽条字标，`normalize_studio_logos.py` 的边车记着它们。
补方让这些字标在 160px 的厂牌页大位上好看，但塞进筛选片那种 28px 的小圆里只剩一条糊字，
所以小位要另找一枚方标。社媒头像早就分 icon / logo 两用，厂牌按同一条判断走。另有一批
厂牌连一张图都没有（账本里现在是 Hon Naka），它们不在那份名单里，可两个位置一样空着，
所以也纳进来。

取哪一份交给 `site_icons`：官网首页声明的 apple-touch-icon / SVG / manifest 优先，
都没有才落到 `/favicon.ico`。合格与否**不能**直接用 `link_marks.render_mark`：
它是为 `/link-mark` 那种 128px 圆标写的，`MIN_DESIGNED_SIZE=96` 会把 32×32、64×64 的
favicon 一律退回。实测七个 JAV 厂牌站，六个的 favicon 内容比在 1.0～1.84 之间——
是方标，只是小。退给一个 28px 的筛选片用绰绰有余，按「不是标识」退掉是判错了。

所以这里只借 `link_marks` 里真正表达 icon / 字标之分的那一条：`content_aspect` 与
`MAX_CONTENT_ASPECT`。尺寸另设自己的下限，因为要顶的位置本来就只有 28～32px。
`MIN_DESIGNED_SIZE` 不动：那是另一个调用方的正确取值。

两条实测逼出来的规矩：

**共享主机守卫。** 链接带非根路径时（`bangbros.com/websites/BangBus`），发现流程从
`origin(url)` 出发，路径一丢，同主机的几个频道全坍缩成一枚 Aylo 站点模板 favicon。
那一枚 64×64、内容比 1.00，两道闸门都过，却和任何频道无关。所以这条路径上主机级候选
一律不算数（`site_icons.HOST_SCOPE`），判词 `平台通用图标`。`/link-mark` 那个位置本来
就是按主机的，不受这条约束。

**字标可装。** 用户 2026-09-03 定的口径：找不到方形标识时，宽扁字标烤成方图装进 `icon`
位也比露出无图强。所以方标一个都没做成、却取回过够大的字标时，用 `images.bake_square`
烤成方图装上，判词 `字标补白`，内容比照记——复核时那个数就是「这枚其实是字标」的提示。
同一份方图再出一行 `logo`：不出这行大位会回落到母品牌的 `<safe>.img`（BangBus 页顶着
BANGBROS），是错图。两位装的都是方图：页面三处取图位都是 `object-fit: cover` 的方框，
宽条装上去只剩中间两个字母。用户指定的 logo 来源做成时优先。

装盘的字节一律过 `images.bake_square`，所以 logo 目录里的文件天然是不透明方图。
入口只有这一个，`normalize_studio_logos.py` 是同一条规则对历史文件的回溯。

默认只出复核 CSV 和候选 PNG，不碰已安装的目录。`--install` 才写 `<safe>.icon.img`
与 `<safe>.logo.img`；`<safe>.img` 只在尚不存在时补写一份，已有的一个字节都不动。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import images, link_marks, site_icons  # noqa: E402
from peach.config import GENERATED_DIR, REVIEW_DIR
from peach.review_csv import write_rows


FIELDS = ("entity_id", "studio", "safe", "variant", "installed", "original_size",
          "link_kind", "url", "verdict", "mark_size", "content_aspect", "sha256",
          "candidate", "evidence")

#: 和 `/link-mark` 用同一个 UA：站点按它决定给不给图标，两处不一致会取到不同的东西。
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

OK, WORDMARK, TOOSMALL = "ok", "仍是字标", "只有小图标"
MISSING, SKIP = "未取得", "无官网链接"
#: 方标没有，装的是补白过的字标。可以装，但复核件上要能看出装的是哪一类。
PADDED = "字标补白"
#: 取到了、也够清楚，但那是整个主机共用的一枚，代表不了这个实体。
SHARED = "平台通用图标"
#: 会被 `--install` 落盘的判词。`平台通用图标` 与 `仍是字标` 不在内。
INSTALLABLE = (OK, PADDED)

ICON, LOGO = "icon", "logo"

#: 小标要顶的位置是 28px 的筛选片和 32px 的圆。短边到不了这个数，缩下去只是一团糊，
#: 还不如继续用现在那张补白字标——至少它是清晰的。
MIN_SHORT_EDGE = 32
#: `logo` 位是厂牌页那个 160 px 大位，2x 屏要 320 px；96 是「还能看」的下限，
#: 低于它说明取到的是缩略图不是标识资产。
MIN_LOGO_SHORT_EDGE = 96

#: `logo` 位的指定来源，按 canonical_name。`icon` 位的覆盖在
#: `site_icons.HOST_OVERRIDES`，两张表不能合并：那一张是「按主机发现图标」的例外，
#: 这一张是「这个厂牌的大字标在哪」，键的含义和取用位置都不同。
#:
#: FC2-PPV：用户 2026-09-03 指定 seeklogo 的 429409 这一份，600×600 P 模式、独角兽 +
#: 「FC2」文字、sha256 `6911574c…f1b7`（8916 B，2026-09-03 实测）。同站还有一份
#: 2000×662 的横向字标，那是字标不装这里。FC2 站上自己的大资产只有 189×68、690×68 两条
#: 横向字标，缩到 160 px 认不出。
#:
#: 剩下 26 条来自 jae.tokyo（Japan Adult Expo 2014／2015／2017 的参展厂牌名录），
#: 用户 2026-09-04 指定的来源。名录每届各带一套厂商 logo：2017 是 320×320，2015 是
#: 188×188，2014 是 270×180，同一家出现在多届时取像素最多的那一届。名字对不上却是
#: 同一家的按厂牌自称收在这里（`ムーディーズ` 的名录条目写作 `MOODYZ`），2016 那届
#: 只有图没有名字，认不出是谁家的，不取。
#: 这 26 家在账本里一张图都没有，且绝大多数连一条 official／catalog 链接都没有——
#: favicon 那条路走不到它们，所以小位也从这一张烤（见 `icon_from_logo`）。
LOGO_SOURCES: dict[str, str] = {
    "FC2-PPV": "https://images.seeklogo.com/logo-png/42/1/fc2-logo-png_seeklogo-429409.png",
    "ラグジュTV": "http://www.jae.tokyo/jae2017/images/maker/maker_image/036.png",
    "BAZOOKA": "http://www.jae.tokyo/jae2017/images/maker/maker_image/009.png",
    "プレステージ": "http://www.jae.tokyo/jae2017/images/maker/maker_image/023.png",
    "JET Eizo": "http://www.jae.tokyo/jae2017/images/maker/maker_image/042.png",
    "ムーディーズ": "http://www.jae.tokyo/jae2017/images/maker/maker_image/054.png",
    "MARRION": "http://www.jae.tokyo/jae2017/images/maker/maker_image/050.png",
    "V&R PRODUCE": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/vr_logo.jpg",
    "エスワン ナンバーワンスタイル": "http://www.jae.tokyo/jae2017/images/maker/maker_image/053.png",
    "センタービレッジ": "http://www.jae.tokyo/jae2015/images/maker/08_center@vllage.png",
    "DOC": "http://www.jae.tokyo/jae2017/images/maker/maker_image/025.png",
    "MAXING": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/MAXING_logo.jpg",
    "SODクリエイト": "http://www.jae.tokyo/jae2015/images/maker/11_sod.png",
    "V＆R PRODUCE": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/vr_logo.jpg",
    "million": "http://www.jae.tokyo/jae2017/images/maker/maker_image/011.png",
    "Baltan": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/baltan_logo.jpg",
    "BeFree": "http://www.jae.tokyo/jae2015/images/maker/17_befree.png",
    "Dogma": "http://www.jae.tokyo/jae2015/images/maker/34_dogma.png",
    "Momotaro Eizo": "http://www.jae.tokyo/jae2017/images/maker/maker_image/022.png",
    "Ranmaru": "http://www.jae.tokyo/jae2015/images/maker/21_ran.png",
    "TEPPAN": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/teppan_logo.jpg",
    "kira*kira": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/kirakira_logo.jpg",
    "kira☆kira": "http://www.jae.tokyo/jae2014/exhibitor/images/logo/kirakira_logo.jpg",
    "ゲッツ！！ボンボン/妄想族": "http://www.jae.tokyo/jae2017/images/maker/maker_image/029.png",
    "シロウトTV": "http://www.jae.tokyo/jae2017/images/maker/maker_image/034.png",
    "プレミアム": "http://www.jae.tokyo/jae2015/images/maker/27_premium.png",
    "俺の素人": "http://www.jae.tokyo/jae2017/images/maker/maker_image/018.png",
}


#: 指定的**字标**来源，按 canonical_name。和 `LOGO_SOURCES` 的区别是形状不是画质：
#: 这一张里的图一律宽扁，只能烤成方图再用，两个位置装的都是那张方图。
#:
#: 为什么不并进 `LOGO_SOURCES`：`logo_row` 把指定来源原样装进大位，而大位是
#: `.entityportrait` 那个 `aspect-ratio:1` + `object-fit:cover` 的 160 px 方框，
#: 宽扁图进去只剩正中间那几个字母。`MIN_LOGO_SHORT_EDGE` 拦下 406×86 拦得对——
#: 问题不在 96 这个数，在于宽扁字标根本不该走那条原样装的路。
#:
#: 来源是 MGStage 的厂牌名录 `/ppv/makers.php`（用户 2026-09-04 指定），十一页 351 家，
#: 由 `harvest_mgstage_makers.py` 对账后人工确认。站上有两种规格（2026-09-04 量过）：
#: 通用的 `pc/<slug>.gif` 是 180×54 白底纯字标，首页轮播位另有 `pc/top/<slug>.jpg`
#: 400×80／406×86，29 家对上账本的里 7 家有。取的一律是前者，理由见下面 Jackson 那条。
#:
#: 只收当前**一张图都没有**的厂牌。已装的那些多来自 jae.tokyo 名录（320×320 的真方标），
#: 拿 180×54 的字标去换是降级；而补白过的厂牌本来就在目标集里，收进来只会把它们
#: 悄悄换成另一张补白图。
#:
#: `きらきらワイフ` 与 `おっぱいちゃん` 不在表里：对账时它们只走到「前缀候选」，撞上的
#: `kira*kira` 和 `OPPAI` 是另外两家真实厂牌，而这两家都已经有图，收进来只有装错的风险。
WORDMARK_SOURCES: dict[str, str] = {
    "Flower": "https://static.mgstage.com/mgs/img/pc/flower.gif",
    "ヒビノ": "https://static.mgstage.com/mgs/img/pc/hibino.gif",
    "HMJM": "https://static.mgstage.com/mgs/img/pc/hmjm.gif",
    "Ienergy": "https://static.mgstage.com/mgs/img/pc/ienergy.gif",
    "いんすた": "https://static.mgstage.com/mgs/img/pc/insta.gif",
    # 首页轮播位那份 `top/jackson.jpg` 大一倍（400×80），但它是带洋红底的横幅：
    # 烤成方图后上下补出两大块洋红，标识本身只剩正中一条。通用位这份是白底透明的
    # 纯字标，小四倍也是对的那一张。大不等于好——2026-09-04 两份都烤出来比过。
    "Jackson": "https://static.mgstage.com/mgs/img/pc/jackson.gif",
    "まんまんランド": "https://static.mgstage.com/mgs/img/pc/manmanland.gif",
    "Planet Plus": "https://static.mgstage.com/mgs/img/pc/planetplus.gif",
    "Radix": "https://static.mgstage.com/mgs/img/pc/radix.gif",
    "S-Cute": "https://static.mgstage.com/mgs/img/pc/scute.gif",
    "VIP": "https://static.mgstage.com/mgs/img/pc/vip.gif",
    "Waap Entertainment": "https://static.mgstage.com/mgs/img/pc/waap.gif",
}


def safe_name(studio: str) -> str:
    """和 `PreviewService.logo` 同一套文件名规则，两边必须一致。"""
    return re.sub(r"[^\w-]", "_", studio, flags=re.UNICODE)[:60]


#: `LOGO_SOURCES` 按文件名归一后的同一张表：目标集是按 safe 归拢的，没有链接的厂牌
#: 拿不到 canonical_name，只能按这个键找。
LOGO_SOURCES_BY_SAFE = {safe_name(name): url for name, url in LOGO_SOURCES.items()}

WORDMARK_SOURCES_BY_SAFE = {safe_name(name): url
                            for name, url in WORDMARK_SOURCES.items()}

#: 同一张表的反向索引：安全文件名 → canonical_name。没有链接的厂牌拿不到别的名字，
#: 复核件上的 `studio` 列只能从这里取；`safe.replace("_", " ")` 对日文名会还原成一排
#: 下划线，那一列就认不出是谁了。
LOGO_SOURCE_NAMES = {safe_name(name): name
                     for name in (*LOGO_SOURCES, *WORDMARK_SOURCES)}


def padded_studios(logo_root: Path) -> dict[str, dict[str, object]]:
    """已安装图里哪些是补白过的字标。

    判据是 `normalize_studio_logos.py` 当时留下的边车，不是现在的像素比例——补白之后
    每一张都是方的，从成品上再也看不出源图是不是条状。
    """
    found: dict[str, dict[str, object]] = {}
    for sidecar in sorted(logo_root.glob("*.img.normalization.json")):
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("action") != "pad-to-square":
            continue
        safe = sidecar.name[: -len(".img.normalization.json")]
        found[safe] = {"width": data.get("original_width", ""),
                       "height": data.get("original_height", "")}
    return found


def harvest_targets(padded: dict[str, dict[str, object]],
                    links: dict[str, list[dict[str, str]]],
                    logo_root: Path) -> dict[str, dict[str, str]]:
    """要补标识的厂牌：补白过的 ∪ 一张图都没有、但有链接或有指定 logo 来源的。

    后一半不在补白名单里——`normalize_studio_logos.py` 从来没处理过它们，因为没有可处理
    的文件。可它们在页面上占的位置和别人一样，两个变体都是空的（账本里现在是 Hon Naka）。
    只看补白名单等于承认「没图的就一直没图」。

    指定 logo 来源自己就是入场理由。jae.tokyo 那 26 家在账本里没有任何链接，按「有链接」
    收目标一条都收不到，而这一位的图早就指好了在哪。`WORDMARK_SOURCES` 同理：那 12 家
    连链接带图一样都没有，图的位置也已经指好了。
    """
    targets: dict[str, dict[str, str]] = {}
    for safe, original in padded.items():
        width, height = original.get("width"), original.get("height")
        targets[safe] = {
            "original_size": f"{width}x{height}" if width and height else "",
            "installed": f"{safe}.img"}
    for safe in list(links) + list(LOGO_SOURCES_BY_SAFE) + list(WORDMARK_SOURCES_BY_SAFE):
        if safe in targets or (logo_root / f"{safe}.img").exists():
            continue
        # `original_size` 留空：没有原图，写 `x` 或 `0x0` 会被当成量到的尺寸。
        targets[safe] = {"original_size": "", "installed": ""}
    return targets


#: 能拿来找图标的链接类型。`social` 不在内：那是另一条线的头像，混进来会把厂牌小标
#: 换成运营的自拍。`catalog` 在内，因为发行平台（FC2-PPV、myfans 这类）按
#: `docs/SOURCING.md` 的判据不登记 official——它们不是厂牌，没有厂牌官网——可它们照样
#: 占着筛选片和卡片徽标那几个位置，需要一枚图标。只认 official 的话，这些实体会在复核件上
#: 记成「无官网链接」，看起来像是漏采，其实是查都没查。
ICON_LINK_KINDS = ("official", "catalog")


def studio_links(connection: sqlite3.Connection) -> dict[str, list[dict[str, str]]]:
    """按 safe 文件名归拢厂牌的站点链接；社媒不算，那是另一条线的头像。"""
    placeholders = ",".join("?" * len(ICON_LINK_KINDS))
    rows = connection.execute(
        "SELECT e.id, e.canonical_name, l.link_kind, l.url"
        " FROM entity e JOIN entity_link l ON l.entity_id = e.id"
        f" WHERE e.kind = 'studio' AND l.link_kind IN ({placeholders})"
        " ORDER BY e.canonical_name, l.id", ICON_LINK_KINDS).fetchall()
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(safe_name(row["canonical_name"]), []).append(
            {"entity_id": row["id"], "studio": row["canonical_name"],
             "link_kind": row["link_kind"], "url": row["url"]})
    return grouped


class Fetcher:
    """注入给 `site_icons.discover` 的取数闭包，顺带限流，并记下取回了几份。

    `best_mark` 返回 None 有两种完全不同的原因：一份都没取回来（站点不可达），
    和取回来了但都被闸门退掉（确实只有字标）。前者是**未取得**，下一步是换个时间
    或换条链接再试；后者是结论，下一步是人工找图。只看返回值分不出来，所以在这里数。
    """

    def __init__(self, client: httpx.Client, timeout: float, interval: float,
                 retries: int = 2, backoff: float = 2.0):
        self.client = client
        self.timeout = timeout
        self.interval = interval
        self.retries = retries
        self.backoff = backoff
        self.fetched = 0
        self.retried = 0
        self._last = 0.0

    def __call__(self, target: str):
        for attempt in range(self.retries + 1):
            wait = self.interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                response = self.client.get(target, headers={"User-Agent": USER_AGENT},
                                           timeout=self.timeout, follow_redirects=True)
            except (OSError, httpx.HTTPError):
                # 和 `page_cache.Site` 同一条规矩：这些站的 TLS 大约三次断一次，重试即成。
                # 上一轮 Fitch、Idea Pocket、Wanz Factory 都取到了，这一轮四个全断，
                # 一次失败就写「未取得」会把纯抖动记成结论。
                if attempt >= self.retries:
                    return None
                self.retried += 1
                time.sleep(self.backoff * (attempt + 1))
                continue
            # 状态码不重试：404 重试三次还是 404。
            if response.status_code != 200 or not response.content:
                return None
            self.fetched += 1
            return response.content, response.headers.get("content-type", "")
        return None


def _as_png(image) -> bytes:
    """原样保留像素，只统一成 PNG。.ico 里可能有多帧，浏览器挑哪一帧不归我们管。"""
    buffer = io.BytesIO()
    image.convert("RGBA").save(buffer, format="PNG")
    return buffer.getvalue()


class SquareMark:
    """一份图标字节 → 一枚方形小标，同时留下每次退回的理由和退回的字标本体。

    `best_mark` 只把结果传回来，退回的原因就地丢失了。可这几种退回的下一步完全不同：
    「还是条字标」现在是可装的回落，「站上只有 16×16」是去找更大的资产。所以在这里记。

    原样保留像素，不放大：存 128 会把 32×32 插值成一团，而这份图最终只显示在 28px。
    """

    def __init__(self):
        self.reasons: list[str] = []
        self.size = ""
        #: 通过的那一份的内容比。1.0 是正方的标识，越接近 2.2 越可能是一条字标
        #: 侥幸压线——复核时这个数比看文件名有用得多。
        self.aspect = ""
        #: 退回过的第一份「够大的宽扁字标」。方标一个都没做成时它就是回落，由调用方
        #: 补白成方图。留第一份而不是最大的一份：`best_mark` 的遍历顺序已经是
        #: 「覆盖表 → 声明 → 根路径猜测」，第一份就是优先级最高的那一份。
        self.wordmark: bytes | None = None
        self.wordmark_size = ""
        self.wordmark_aspect = ""

    def __call__(self, data: bytes, size: int = 0, content_type: str = "") -> bytes | None:
        image = link_marks.decode(data, content_type)
        if image is None:
            self.reasons.append("解不开")
            return None
        aspect = link_marks.content_aspect(image)
        if aspect == 0.0 or aspect > link_marks.MAX_CONTENT_ASPECT:
            self.reasons.append(f"内容比 {aspect:.2f} 是字标")
            if aspect > 0.0 and min(image.size) >= MIN_SHORT_EDGE and self.wordmark is None:
                self.wordmark = _as_png(image)
                self.wordmark_size = f"{image.size[0]}x{image.size[1]}"
                self.wordmark_aspect = f"{aspect:.2f}"
            return None
        if min(image.size) < MIN_SHORT_EDGE:
            self.reasons.append(f"只有 {image.size[0]}x{image.size[1]}")
            return None
        self.size = f"{image.size[0]}x{image.size[1]}"
        self.aspect = f"{aspect:.2f}"
        return _as_png(image)


class EntityScope:
    """否决只能代表主机的候选，并记下它是哪个主机的哪一份。

    传给 `site_icons.best_mark(accept=...)`。只在链接带非根路径时才挂上：那种链接
    说明这个实体只是主机上的一条路径，主机级图标代表的是平台不是它。
    """

    def __init__(self):
        self.rejected: list[str] = []
        self._seen: set[str] = set()

    def __call__(self, candidate, data: bytes, content_type: str = "") -> bool:
        if candidate.scope == site_icons.ENTITY_SCOPE:
            return True
        digest = hashlib.sha256(data).hexdigest()
        if digest not in self._seen:
            self._seen.add(digest)
            self.rejected.append(
                f"{candidate.url} 是 {site_icons.host_key(candidate.url)} 的主机级图标"
                f"（sha256 {digest[:8]}）")
        return False


def shares_its_host(url: str) -> bool:
    """这条链接指的是主机上的一条路径，而不是整个主机吗。

    `bangbros.com/websites/BangBus` 是，`https://honnaka.jp/` 不是。是的那些不能用
    主机级候选：同主机的三个频道会拿到同一枚 sha256 完全相同的 favicon。
    """
    return bool(urlsplit(url).path.strip("/"))


def _row(safe: str, target: dict[str, str], entry: dict[str, str] | None,
         variant: str, verdict: str, **extra) -> dict[str, object]:
    row = {"entity_id": entry["entity_id"] if entry else "",
           "studio": (entry["studio"] if entry
                      else LOGO_SOURCE_NAMES.get(safe, safe.replace("_", " "))),
           "safe": safe, "variant": variant,
           "installed": target["installed"], "original_size": target["original_size"],
           "link_kind": entry["link_kind"] if entry else "",
           "url": entry["url"] if entry else "",
           "verdict": verdict, "mark_size": "", "content_aspect": "",
           "sha256": "", "candidate": "", "evidence": ""}
    row.update(extra)
    return row


def _store(candidate_dir: Path, name: str, payload: bytes) -> Path:
    candidate_dir.mkdir(parents=True, exist_ok=True)
    path = candidate_dir / name
    path.write_bytes(payload)
    return path


def icon_row(safe: str, target: dict[str, str], entries: list[dict[str, str]],
             fetch, candidate_dir: Path
             ) -> tuple[dict[str, object], dict[str, object] | None]:
    """`icon` 位一行。一个厂牌可能挂多条链接，第一条做成就停。

    第二个返回值只在走了字标补白时才有：同一枚字标原样出的 `logo` 行。
    """
    if not entries:
        return _row(safe, target, None, ICON, SKIP,
                    evidence="账本里这个厂牌没有 official／catalog 链接"), None
    attempts: list[str] = []
    reachable = False
    policy = SquareMark()
    scope = EntityScope()
    for entry in entries:
        before = getattr(fetch, "fetched", 0)
        made = site_icons.best_mark(
            entry["url"], fetch, policy,
            accept=scope if shares_its_host(entry["url"]) else None)
        reachable = reachable or getattr(fetch, "fetched", 0) > before
        if not made:
            attempts.append(entry["url"])
            continue
        path = _store(candidate_dir, f"{safe}.png", made)
        return _row(safe, target, entry, ICON, OK, mark_size=policy.size,
                    content_aspect=policy.aspect,
                    sha256=hashlib.sha256(made).hexdigest(), candidate=str(path)), None

    entry = entries[0]
    tried = "、".join(attempts)
    plate = images.bake_square(policy.wordmark) if policy.wordmark else None
    if plate:
        # 用户 2026-09-03 的口径：不是 icon 也可以装 icon，尽量不要落入无图。
        side = link_marks.decode(plate)
        path = _store(candidate_dir, f"{safe}.png", plate)
        icon = _row(safe, target, entry, ICON, PADDED,
                    mark_size=f"{side.size[0]}x{side.size[1]}" if side else "",
                    content_aspect=policy.wordmark_aspect,
                    sha256=hashlib.sha256(plate).hexdigest(), candidate=str(path),
                    evidence=(f"方形标识未取得，装的是字标：{policy.wordmark_size}"
                              f"／内容比 {policy.wordmark_aspect}，烤成方图"))
        # 不出这一行，`logo` 位会回落到 `<safe>.img`——BangBus 的那一份是母品牌
        # BANGBROS，小位对了大位却挂着别家的牌子。
        logo_path = _store(candidate_dir, f"{safe}.logo.png", plate)
        logo = _row(safe, target, entry, LOGO, OK,
                    mark_size=icon["mark_size"], content_aspect=policy.wordmark_aspect,
                    sha256=icon["sha256"], candidate=str(logo_path),
                    evidence=(f"与 icon 位同一份方图（原字标 {policy.wordmark_size}）"))
        return icon, logo
    if not reachable:
        verdict, evidence = MISSING, f"试过 {tried}，一份字节都没取回来"
    elif scope.rejected and not policy.reasons:
        # 取到了、也够清楚，但那是平台模板的通用图标，和这个实体无关。
        verdict = SHARED
        evidence = f"试过 {tried}：" + "；".join(scope.rejected)
    elif policy.reasons and all("只有 " in reason for reason in policy.reasons):
        # 是方标，只是站上没有够大的那一份。下一步是找更大的资产，不是放弃。
        verdict, evidence = TOOSMALL, f"试过 {tried}：" + "、".join(policy.reasons)
    else:
        verdict = WORDMARK
        evidence = f"试过 {tried}：" + "、".join(
            policy.reasons + scope.rejected or ["没有候选"])
    return _row(safe, target, entry, ICON, verdict, evidence=evidence), None


def logo_row(safe: str, target: dict[str, str], entries: list[dict[str, str]],
             fetch, candidate_dir: Path) -> dict[str, object] | None:
    """`logo` 位一行；这个厂牌没有指定来源就返回 None。

    这一位不过内容比闸门——大位要的本来就是完整字标，宽扁是它应有的形状。
    只验「是图」和「够大」。
    """
    url = LOGO_SOURCES_BY_SAFE.get(safe)
    if not url:
        return None
    entry = dict(entries[0], link_kind="logo-source", url=url) if entries else None
    if entry is None:
        entry = {"entity_id": "", "studio": safe.replace("_", " "),
                 "link_kind": "logo-source", "url": url}
    got = fetch(url)
    if got is None:
        return _row(safe, target, entry, LOGO, MISSING,
                    evidence="指定的 logo 来源一份字节都没取回来")
    image = link_marks.decode(got[0], got[1])
    if image is None:
        return _row(safe, target, entry, LOGO, MISSING, evidence="指定的 logo 来源解不开")
    if min(image.size) < MIN_LOGO_SHORT_EDGE:
        return _row(safe, target, entry, LOGO, TOOSMALL,
                    mark_size=f"{image.size[0]}x{image.size[1]}",
                    evidence=f"短边 {min(image.size)} < {MIN_LOGO_SHORT_EDGE}")
    payload = _as_png(image)
    path = _store(candidate_dir, f"{safe}.logo.png", payload)
    return _row(safe, target, entry, LOGO, OK,
                mark_size=f"{image.size[0]}x{image.size[1]}",
                content_aspect=f"{link_marks.content_aspect(image):.2f}",
                sha256=hashlib.sha256(payload).hexdigest(), candidate=str(path),
                evidence="用户指定的 logo 来源")


def icon_from_logo(safe: str, target: dict[str, str], logo: dict[str, object],
                   candidate_dir: Path) -> dict[str, object]:
    """指定 logo 来源做成了、小位却还空着时，小位从同一张烤。

    jae.tokyo 那 26 家在账本里连一条链接都没有，`icon_row` 走不到发现流程，只会记一行
    「无官网链接」，然后筛选片和卡片徽标继续空着。可大位这张已经是名录里厂牌自己交的
    标识资产，比任何 favicon 都准。方的直接顶上，宽扁的补白成方图——和字标补白同一条
    口径，判词也照用 `字标补白`，区别只在源图来自指定来源而不是官网。
    """
    payload = images.bake_square(Path(str(logo["candidate"])).read_bytes())
    image = link_marks.decode(payload) if payload else None
    if payload is None or image is None:
        return _row(safe, target, None, ICON, MISSING,
                    url=str(logo["url"]), link_kind="logo-source",
                    evidence="指定的 logo 来源烤不成方图")
    # 判「补没补白」看源图自己的长宽，不看内容比：`images.MAX_ASPECT` 正是 `bake_square`
    # 「够方就原样返回」的那条线，所以 `ok` 恰好等于这一张一个像素都没动过。名录里的
    # jpg 是整幅不透明的，内容比对它一律回 0，拿那个数分不出方图和长条。
    width, height = (int(value) for value in str(logo["mark_size"]).split("x"))
    wide = max(width, height) / min(width, height) > images.MAX_ASPECT
    aspect = link_marks.content_aspect(image)
    path = _store(candidate_dir, f"{safe}.png", payload)
    return _row(safe, target, None, ICON, PADDED if wide else OK,
                url=str(logo["url"]), link_kind="logo-source",
                mark_size=f"{image.size[0]}x{image.size[1]}",
                content_aspect=f"{aspect:.2f}",
                sha256=hashlib.sha256(payload).hexdigest(), candidate=str(path),
                evidence=f'与 logo 位同一份指定来源（{logo["mark_size"]}）烤成方图')


def wordmark_source_rows(safe: str, target: dict[str, str], fetch, candidate_dir: Path
                         ) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    """指定字标来源的 `icon` + `logo` 两行；这个厂牌没有指定字标来源就返回 `(None, None)`。

    宽扁字标只有烤成方图这一条用法，两个位置装的是同一张——和官网字标补白同一条口径
    （`icon_row` 的补白分支），区别只在源图来自名录而不是站点自己的 `<img>`。
    失败也出行：复核件不丢失败记录，`--install` 只认带候选文件的行。
    """
    url = WORDMARK_SOURCES_BY_SAFE.get(safe)
    if not url:
        return None, None
    kind = "wordmark-source"
    got = fetch(url)
    if got is None:
        return _row(safe, target, None, ICON, MISSING, url=url, link_kind=kind,
                    evidence="指定的字标来源一份字节都没取回来"), None
    source = link_marks.decode(got[0], got[1])
    if source is None:
        return _row(safe, target, None, ICON, MISSING, url=url, link_kind=kind,
                    evidence="指定的字标来源解不开"), None
    if min(source.size) < MIN_SHORT_EDGE:
        return _row(safe, target, None, ICON, TOOSMALL, url=url, link_kind=kind,
                    mark_size=f"{source.size[0]}x{source.size[1]}",
                    evidence=f"短边 {min(source.size)} < {MIN_SHORT_EDGE}"), None
    plate = images.bake_square(_as_png(source))
    square = link_marks.decode(plate) if plate else None
    if square is None:
        return _row(safe, target, None, ICON, MISSING, url=url, link_kind=kind,
                    mark_size=f"{source.size[0]}x{source.size[1]}",
                    evidence="指定的字标来源烤不成方图"), None
    aspect = f"{link_marks.content_aspect(square):.2f}"
    payload = _as_png(square)
    digest = hashlib.sha256(payload).hexdigest()
    size = f"{square.size[0]}x{square.size[1]}"
    origin = f"{source.size[0]}x{source.size[1]}"
    icon = _row(safe, target, None, ICON, PADDED, url=url, link_kind=kind,
                mark_size=size, content_aspect=aspect, sha256=digest,
                candidate=str(_store(candidate_dir, f"{safe}.png", payload)),
                evidence=f"指定的字标来源（{origin}）烤成方图")
    logo = _row(safe, target, None, LOGO, OK, url=url, link_kind=kind,
                mark_size=size, content_aspect=aspect, sha256=digest,
                candidate=str(_store(candidate_dir, f"{safe}.logo.png", payload)),
                evidence=f"与 icon 位同一份方图（原字标 {origin}）")
    return icon, logo


def harvest(targets: dict[str, dict[str, str]],
            links: dict[str, list[dict[str, str]]],
            fetch, candidate_dir: Path) -> list[dict[str, object]]:
    """每个目标厂牌出一行 `icon`；有指定 logo 来源或走了字标补白的再出 `logo` 行。

    有指定字标来源的厂牌只走那一条，两行都从同一张方图出（`wordmark_source_rows`）。

    小位自己没做成、大位的指定来源做成了时，小位从大位那张烤（`icon_from_logo`）。

    指定来源做成时只有它那一行；它没做成（未取得／太小）那行照记，字标 logo 行
    跟在后面——复核表不丢失败记录，安装时只有带候选文件的行才落地。
    """
    rows: list[dict[str, object]] = []
    for safe in sorted(targets):
        target = targets[safe]
        entries = links.get(safe, [])
        marked, marked_logo = wordmark_source_rows(safe, target, fetch, candidate_dir)
        if marked is not None:
            # 指定字标来源就是这个厂牌的答案，不再去链接上碰运气：这 12 家账本里
            # 本来就一条 official／catalog 链接都没有，走发现流程只会多记一行
            # 「无官网链接」，把已经指好的那张图挤掉。
            rows.append(marked)
            if marked_logo is not None:
                rows.append(marked_logo)
            continue
        icon, wordmark_logo = icon_row(safe, target, entries, fetch, candidate_dir)
        logo = logo_row(safe, target, entries, fetch, candidate_dir)
        if (logo is not None and logo["verdict"] == OK
                and icon["verdict"] not in INSTALLABLE):
            icon = icon_from_logo(safe, target, logo, candidate_dir)
        rows.append(icon)
        if logo is not None:
            rows.append(logo)
        if wordmark_logo is not None and (logo is None or logo["verdict"] != OK):
            rows.append(wordmark_logo)
    return rows


def install(rows: list[dict[str, object]], logo_root: Path) -> list[str]:
    """把可装的候选落成 `<safe>.icon.img` / `<safe>.logo.img`。

    这两个都是新文件名，不覆盖也不删除现有的 `<safe>.img`。只有尚**没有**
    `<safe>.img` 的厂牌才补写一份：不带 `variant` 和认不出的 `variant` 都回落到它，
    缺了那些位置仍然 404。

    落盘的字节过 `images.bake_square`，装进去的一律是不透明方图。哈希核对针对
    候选文件本身，`installed_sha256` 记的才是真正写进目录的那一份。
    """
    written: list[str] = []
    logo_root.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if row["verdict"] not in INSTALLABLE or not row["candidate"]:
            continue
        candidate = Path(str(row["candidate"])).read_bytes()
        if hashlib.sha256(candidate).hexdigest() != row["sha256"]:
            raise ValueError(f'候选文件与复核记录哈希不一致，拒绝安装：{row["safe"]}')
        payload = images.bake_square(candidate)
        if payload is None:
            raise ValueError(f'候选烤不成方图，拒绝安装：{row["safe"]}')
        installed_sha256 = hashlib.sha256(payload).hexdigest()
        variant = str(row.get("variant") or ICON)
        targets = [logo_root / f'{row["safe"]}.{variant}.img']
        base = logo_root / f'{row["safe"]}.img'
        if not base.exists():
            targets.append(base)
        for destination in targets:
            staging = destination.with_name(f"{destination.name}.{uuid.uuid4().hex}.tmp")
            staging.write_bytes(payload)
            os.replace(staging, destination)
            Path(f"{destination}.ct").write_text("image/png", encoding="utf-8")
            Path(f"{destination}.provenance.json").write_text(json.dumps({
                "source": "studio icon harvest",
                "source_url": row["url"],
                "sha256": row["sha256"],
                "installed_sha256": installed_sha256,
                "variant": variant,
                "verdict": row["verdict"],
                "installed_beside": f'{row["safe"]}.img',
                "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "purpose": "small-surface studio mark" if variant == ICON
                           else "studio hero wordmark",
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            written.append(destination.name)
    return written


def run(args: argparse.Namespace) -> dict[str, object]:
    logo_root = args.logo_root.resolve()
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        links = studio_links(connection)
    finally:
        connection.close()

    targets = harvest_targets(padded_studios(logo_root), links, logo_root)
    if args.only:
        wanted = {safe_name(name) for name in args.only}
        targets = {key: value for key, value in targets.items() if key in wanted}

    client = httpx.Client(trust_env=True, follow_redirects=True)
    try:
        rows = harvest(targets, links, Fetcher(client, args.timeout, args.interval),
                       args.candidate_dir.resolve())
    finally:
        client.close()

    order = {OK: 0, PADDED: 1, TOOSMALL: 2, SHARED: 3, WORDMARK: 4, MISSING: 5, SKIP: 6}
    rows.sort(key=lambda row: (order.get(row["verdict"], 9), row["safe"], row["variant"]))
    write_rows(args.output, FIELDS, rows)
    counted = (OK, PADDED, TOOSMALL, SHARED, WORDMARK, MISSING, SKIP)
    stats: dict[str, object] = {"目标厂牌": len(targets), "复核行": len(rows)}
    stats.update({verdict: sum(1 for row in rows if row["verdict"] == verdict)
                  for verdict in counted})
    stats["logo 行"] = sum(1 for row in rows if row["variant"] == LOGO)
    stats["output"] = str(args.output)
    if args.install:
        stats["已安装"] = install(rows, logo_root)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        default=REVIEW_DIR / "studio-icons.csv")
    parser.add_argument("--logo-root", type=Path, default=GENERATED_DIR / "logos")
    parser.add_argument("--candidate-dir", type=Path,
                        default=REVIEW_DIR / "studio-icons")
    parser.add_argument("--only", nargs="*", default=[],
                        help="只处理这几个厂牌，按 canonical_name 给")
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--install", action="store_true",
                        help="把可装的候选写成 <safe>.icon.img / <safe>.logo.img")
    args = parser.parse_args(argv)
    print(run(args))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
