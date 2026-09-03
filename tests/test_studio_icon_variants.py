"""厂牌标识的 icon / logo 两变体：文件解析、页面取用位置、补图脚本。

分岔的前提是这个厂牌真的存了两份。只有一份时两个变体都必须回落到那一份，
否则 129 个厂牌里绝大多数会在小地方变成 404。
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from peach import web_review
from peach.previews import LOGO_VARIANTS, PreviewService, PreviewUnavailable, logo_key
from peach.web_state import WebContract


ROOT = Path(__file__).resolve().parents[1]


def load_script():
    path = ROOT / "scripts" / "harvest_studio_icons.py"
    spec = importlib.util.spec_from_file_location("harvest_studio_icons_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_script()


def png_bytes(size=(256, 256), color=(30, 90, 160)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def block_png(size, inset=4, color=(210, 30, 30)):
    """透明底 + 一块不透明色块。

    内容比看的是不透明像素的外接框，所以底必须真透明：整幅纯色的图 `content_aspect`
    会回 0（四角当背景，主体成了空集），那样测不到任何闸门。
    """
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    for x in range(inset, size[0] - inset):
        for y in range(inset, size[1] - inset):
            image.putpixel((x, y), color + (255,))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


# 烤成方图后的边长。`block_png` 的不透明外接框每边比给的尺寸少一个 inset，
# 烤底再让内容占边长 `PLATE_CONTENT_RATIO`，所以两个数都由常量算出来。
PLATE_CONTENT_EDGE = 298 - 4 * 2
PLATE_SIDE = round(PLATE_CONTENT_EDGE / MODULE.images.PLATE_CONTENT_RATIO)
PLATE_SIZE = f"{PLATE_SIDE}x{PLATE_SIDE}"


class VariantResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.logos = root / "logos"
        self.logos.mkdir(parents=True)
        self.service = PreviewService(
            SimpleNamespace(), SimpleNamespace(), root / "snapshots", root / "posters",
            root / "avatars", self.logos)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str, body: bytes = b"x", content_type: str = "") -> Path:
        path = self.logos / name
        path.write_bytes(body)
        if content_type:
            Path(f"{path}.ct").write_text(content_type, encoding="utf-8")
        return path

    def test_no_variant_keeps_the_old_file(self):
        """不带 variant 的请求必须和加这个参数之前一模一样。"""
        base = self.write("Fitch.img", content_type="image/png")
        self.assertEqual(self.service.logo("Fitch"), (base, "image/png"))

    def test_the_only_installed_file_serves_both_variants(self):
        """只有一份图的厂牌占绝大多数，两个位置都得照常拿到它。"""
        base = self.write("Fitch.img")
        for variant in ("icon", "logo"):
            with self.subTest(variant=variant):
                self.assertEqual(self.service.logo("Fitch", variant)[0], base)

    def test_icon_prefers_the_icon_file(self):
        self.write("Fitch.img")
        icon = self.write("Fitch.icon.img", content_type="image/png")
        self.assertEqual(self.service.logo("Fitch", "icon"), (icon, "image/png"))

    def test_logo_ignores_the_icon_file(self):
        """大位要的是完整字标。存了小标不代表大位就该改用小标。"""
        base = self.write("Fitch.img")
        self.write("Fitch.icon.img")
        self.assertEqual(self.service.logo("Fitch", "logo")[0], base)

    def test_logo_prefers_the_logo_file(self):
        self.write("Fitch.img")
        wordmark = self.write("Fitch.logo.img")
        self.assertEqual(self.service.logo("Fitch", "logo")[0], wordmark)

    def test_an_unknown_variant_falls_back_instead_of_404(self):
        """缓存下来的旧页面可能带着别的参数；那也该出图，不该把厂牌页开出个空位。"""
        base = self.write("Fitch.img")
        self.assertEqual(self.service.logo("Fitch", "banner")[0], base)

    def test_a_studio_with_no_file_at_all_still_raises(self):
        for variant in ("", "icon", "logo"):
            with self.subTest(variant=variant):
                with self.assertRaises(PreviewUnavailable):
                    self.service.logo("Nobody", variant)

    def test_the_variant_file_name_matches_the_scripts_rule(self):
        """脚本安装的文件名和这里解析的必须是同一套，否则装了也读不到。"""
        self.assertEqual(MODULE.safe_name("Idea Pocket"), "Idea_Pocket")
        self.write("Idea_Pocket.img")
        icon = self.write(f'{MODULE.safe_name("Idea Pocket")}.icon.img')
        self.assertEqual(self.service.logo("Idea Pocket", "icon")[0], icon)


class LogoAvailabilityTests(unittest.TestCase):
    """「这个厂牌有没有标识」必须和 `/logo` 真正的取图判据逐字一致。

    页面据此决定输出 `<img>` 还是直接首字母垫底。判得松一格就是「说有图但取回
    404」——那个位置画出一张碎图；紧一格就是「明明装了却永远只显示首字母」。所以
    两边在同一个目录上对照着测，不各测一半。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.logos = root / "logos"
        self.logos.mkdir(parents=True)
        self.service = PreviewService(
            SimpleNamespace(), SimpleNamespace(), root / "snapshots", root / "posters",
            root / "avatars", self.logos)
        # 库文件不必存在：可用性判定只扫目录，一个字节都不查库。但 `logo_root` 必须
        # 显式给临时目录，默认值是本机真实的 generated 树。
        self.contract = WebContract(root / "ledger.db", logo_root=self.logos)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str) -> Path:
        path = self.logos / name
        path.write_bytes(b"x")
        return path

    def resolves(self, studio: str, variant: str = "icon") -> bool:
        try:
            self.service.logo(studio, variant)
        except PreviewUnavailable:
            return False
        return True

    def assertAgrees(self, studio: str):
        """可用性判定和取图在同一个目录上给出同一个答案。

        只对页面真会发的两个 variant 成立：三处取图位都带 `variant=`，裸 `/logo`
        由 `test_web_ui` 那条页面源测试拦住。
        """
        available = self.contract.has_logo(studio)
        for variant in LOGO_VARIANTS:
            with self.subTest(studio=studio, variant=variant):
                self.assertEqual(
                    available, self.resolves(studio, variant),
                    f"{studio!r}：可用性说 {available}，取图不同意")

    def test_a_studio_with_a_file_is_available_and_one_without_is_not(self):
        self.write("Fitch.img")
        self.assertAgrees("Fitch")
        self.assertAgrees("Nobody")

    def test_the_installed_shape_agrees_on_both_variants(self):
        """`--install` 落的就是这个形状：底图一份加两个变体，两边都得说有图。"""
        for name in ("Fitch.img", "Fitch.icon.img", "Fitch.logo.img"):
            self.write(name)
        self.assertAgrees("Fitch")

    def test_a_variant_only_studio_still_counts_as_available(self):
        """只有变体文件、没有底图时仍算有图：那个变体确实取得到。

        另一个变体会落空，但那条路径本来就有兜底（厂牌大位退到实体图，小圆片退到
        首字母），而 `--install` 总会补上底图，这个形状只可能是手工摆出来的。判成
        「没有图」反而更糟：装上的那张图从此永远不显示。
        """
        self.write("Fitch.icon.img")
        self.assertTrue(self.contract.has_logo("Fitch"))
        self.assertTrue(self.resolves("Fitch", "icon"))

    def test_the_key_rule_survives_spaces_and_punctuation(self):
        """页面上的厂牌名带空格、`&`、`/` 的比不带的多，落盘名全归一成下划线。"""
        studios = ("V&R PRODUCE", "Kahanshin Tigers /Fetika", "M Girls' Lab")
        for studio in studios:
            self.write(f"{logo_key(studio)}.img")
        for studio in studios:
            self.assertAgrees(studio)

    def test_two_japanese_studios_do_not_share_one_file(self):
        """只留 ASCII 时非 ASCII 的每个字都换成一个下划线，落盘名只剩「几个字」。

        账本里 129 个厂牌有 12 组这样撞在一起，`プレステージ` 和 `ムーディーズ` 同为
        `______`。撞了不报错，后装的盖掉先装的，PRESTIGE 的位置就挂上 MOODYZ 的牌子。
        """
        self.write(f"{logo_key('プレステージ')}.img")
        self.assertTrue(self.contract.has_logo("プレステージ"))
        self.assertFalse(self.contract.has_logo("ムーディーズ"))
        self.assertAgrees("ムーディーズ")
        self.assertNotEqual(logo_key("シロウトTV"), logo_key("ラグジュTV"))

    def test_the_ascii_file_names_already_on_disk_keep_their_key(self):
        """已经装好的 60 张都是 ASCII 名，改名规则不能让它们从此取不到。"""
        expected = {"Fitch": "Fitch", "FC2-PPV": "FC2-PPV", "Idea Pocket": "Idea_Pocket",
                    "S1 NO.1 STYLE": "S1_NO_1_STYLE", "kira*kira": "kira_kira"}
        for studio, key in expected.items():
            with self.subTest(studio=studio):
                self.assertEqual(logo_key(studio), key)

    def test_availability_is_case_insensitive_like_the_resolver(self):
        """`logo()` 对大小写不敏感（Windows 与 macOS 的默认文件系统就是这样），
        索引不能顺手把这层容错丢了。"""
        self.write("fitch.img")
        self.assertTrue(self.contract.has_logo("FITCH"))
        self.assertAgrees("FITCH")

    def test_a_sidecar_or_a_vector_original_is_not_a_logo(self):
        """`.ct` 边车和留档的 SVG 都不是 `/logo` 会取的文件，不算这个厂牌有图。"""
        self.write("Fitch.img.ct")
        self.write("Fitch.svg")
        self.assertFalse(self.contract.has_logo("Fitch"))
        self.assertAgrees("Fitch")

    def test_an_empty_studio_name_is_never_available(self):
        """裸 `/logo`（没有 studio）在服务端也是 404，页面不该发得出来。"""
        for studio in (None, "", "   "):
            with self.subTest(studio=studio):
                self.assertFalse(self.contract.has_logo(studio))

    def test_a_missing_logo_directory_is_an_empty_index(self):
        """目录还没建（新机器、干净数据目录）时全部退回首字母，不是报错。"""
        root = Path(self.tmp.name).resolve()
        contract = WebContract(root / "ledger.db", logo_root=root / "nowhere")
        self.assertEqual(contract.logo_index(), frozenset())
        self.assertFalse(contract.has_logo("Fitch"))

    def test_a_newly_installed_logo_shows_up_after_the_review_cache_bust(self):
        """索引带 TTL，但复核批准会 `cache_bust()`：用户自己装上的图立刻可见。"""
        self.assertFalse(self.contract.has_logo("Fitch"))
        self.write("Fitch.img")
        self.contract.cache_bust()
        self.assertTrue(self.contract.has_logo("Fitch"))

    def test_the_install_path_and_the_resolver_share_one_key_rule(self):
        """批准落地写的文件名和取图找的文件名只能有一个实现。"""
        self.assertIs(web_review.studio_logo_key, logo_key)


class PageSourceTests(unittest.TestCase):
    """页面按位置取变体：小地方 icon，厂牌页那个 160px 大位 logo。"""

    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

    def test_the_studio_hero_asks_for_the_wordmark(self):
        self.assertIn("/logo?studio=${encodeURIComponent(d.canonical_name)}&variant=logo",
                      self.source)

    def test_every_small_surface_asks_for_the_icon(self):
        for snippet in (
            '/logo?studio=115&variant=icon',
            '/logo?studio=${encodeURIComponent(x.k)}&variant=icon',
            '/logo?studio=${encodeURIComponent(item.name)}&variant=icon',
        ):
            # 小位只有这三处；`.entityfavicon` 的模板不写 `data-studio`，图片回退是
            # 声明式的，不存在按 `img.dataset.studio` 换图的第四处。「不许漏 variant」
            # 由下面那条按行扫描的断言守。
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, self.source)

    def test_no_logo_request_is_left_without_a_variant(self):
        """漏掉一处就会在那个位置继续显示补白字标，而且没人会注意到。"""
        bare = [line.strip() for line in self.source.splitlines()
                if "/logo?studio=" in line and "variant=" not in line]
        self.assertEqual(bare, [])


class PaddedStudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logos = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def sidecar(self, safe: str, action: str = "pad-to-square", **extra):
        payload = {"action": action, "original_width": 130, "original_height": 43}
        payload.update(extra)
        (self.logos / f"{safe}.img").write_bytes(b"x")
        (self.logos / f"{safe}.img.normalization.json").write_text(
            json.dumps(payload), encoding="utf-8")

    def test_only_padded_files_are_candidates(self):
        """补白之后每一张都是方的，从像素上再也看不出源图是条状——只能认边车。"""
        self.sidecar("FC2-PPV")
        self.sidecar("Alice_JAPAN", action="keep")
        (self.logos / "S1.img").write_bytes(b"x")
        self.assertEqual(sorted(MODULE.padded_studios(self.logos)), ["FC2-PPV"])

    def test_the_original_size_is_carried_through(self):
        self.sidecar("FC2-PPV")
        self.assertEqual(MODULE.padded_studios(self.logos)["FC2-PPV"],
                         {"width": 130, "height": 43})

    def test_a_corrupt_sidecar_is_skipped_not_fatal(self):
        (self.logos / "Broken.img.normalization.json").write_text("{", encoding="utf-8")
        self.assertEqual(MODULE.padded_studios(self.logos), {})


class HarvestTargetTests(unittest.TestCase):
    """目标集 = 补白过的 ∪ 有链接但一张图都没有的。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logos = Path(self.tmp.name).resolve()
        (self.logos / "Fitch.img").write_bytes(b"x")
        self.padded = {"Fitch": {"width": 130, "height": 43}}
        self.links = {"Fitch": [{"url": "https://fitch-av.com/"}],
                      "Hon_Naka": [{"url": "https://honnaka.jp/"}],
                      "S1": [{"url": "https://s1s1s1.com/"}]}
        # 指定来源那张真表有二十多条，留着会盖住这里每一条判据。要用的测试自己往里放。
        self.sources = dict(MODULE.LOGO_SOURCES_BY_SAFE)
        MODULE.LOGO_SOURCES_BY_SAFE.clear()

    def tearDown(self):
        MODULE.LOGO_SOURCES_BY_SAFE.clear()
        MODULE.LOGO_SOURCES_BY_SAFE.update(self.sources)
        self.tmp.cleanup()

    def test_a_studio_with_no_image_at_all_is_included(self):
        """Hon Naka 不在补白名单里——它没有可补白的文件。可它两个位置一样是空的。"""
        (self.logos / "S1.img").write_bytes(b"x")
        targets = MODULE.harvest_targets(self.padded, self.links, self.logos)
        self.assertEqual(sorted(targets), ["Fitch", "Hon_Naka"])

    def test_the_padded_studio_keeps_its_original_size(self):
        targets = MODULE.harvest_targets(self.padded, self.links, self.logos)
        self.assertEqual(targets["Fitch"],
                         {"original_size": "130x43", "installed": "Fitch.img"})

    def test_a_studio_with_no_image_leaves_the_size_columns_empty(self):
        """没有原图就没有量到的尺寸。写 `x` 或 `0x0` 会被当成量出来的结果。"""
        targets = MODULE.harvest_targets(self.padded, self.links, self.logos)
        self.assertEqual(targets["Hon_Naka"],
                         {"original_size": "", "installed": ""})

    def test_a_studio_with_neither_image_nor_link_is_not_a_target(self):
        """没链接、没图、也没指定来源的厂牌进来只会在复核件上多一行「无官网链接」。"""
        targets = MODULE.harvest_targets({}, {}, self.logos)
        self.assertEqual(targets, {})

    def test_a_designated_logo_source_is_reason_enough(self):
        """jae.tokyo 那批在账本里连一条链接都没有，按「有链接」收目标一条都收不到。"""
        MODULE.LOGO_SOURCES_BY_SAFE["Dogma"] = "http://logos.example/dogma.png"
        self.assertEqual(MODULE.harvest_targets({}, {}, self.logos),
                         {"Dogma": {"original_size": "", "installed": ""}})

    def test_a_designated_source_does_not_reopen_a_studio_that_has_its_image(self):
        """已经装好的一张都不动：这个脚本的入口只补空位。"""
        MODULE.LOGO_SOURCES_BY_SAFE["Fitch"] = "http://logos.example/fitch.png"
        self.assertNotIn("Fitch", MODULE.harvest_targets({}, {}, self.logos))


class LogoSourceTests(unittest.TestCase):
    """`logo` 位的指定来源。这一位不过内容比闸门——大位要的本来就是完整字标。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.candidates = self.root / "candidates"
        self.target = {"original_size": "130x43", "installed": "Fitch.img"}
        self.entries = [{"entity_id": 5591, "studio": "Fitch",
                         "link_kind": "official", "url": "https://fitch-av.com/"}]
        self.url = "https://logos.example/fitch.png"
        self.original = dict(MODULE.LOGO_SOURCES_BY_SAFE)
        MODULE.LOGO_SOURCES_BY_SAFE["Fitch"] = self.url

    def tearDown(self):
        MODULE.LOGO_SOURCES_BY_SAFE.clear()
        MODULE.LOGO_SOURCES_BY_SAFE.update(self.original)
        self.tmp.cleanup()

    def row(self, payload=None, reachable=True):
        pages = {self.url: payload} if payload is not None else {}
        return MODULE.logo_row("Fitch", self.target, self.entries,
                               Fetch(pages, reachable=reachable), self.candidates)

    def test_every_registered_source_is_reachable_by_its_file_name(self):
        """两张表按同一条命名规则建，键对不上时复核件上的名字会退成一排下划线。"""
        self.assertEqual(sorted(self.original), sorted(MODULE.LOGO_SOURCE_NAMES))
        for safe, studio in MODULE.LOGO_SOURCE_NAMES.items():
            with self.subTest(studio=studio):
                self.assertEqual(MODULE.safe_name(studio), safe)
                self.assertIn(studio, MODULE.LOGO_SOURCES)

    def test_the_expo_directory_is_the_source_for_the_studios_with_no_image(self):
        """用户 2026-09-04 指定 jae.tokyo：名录每届各带一套厂商自己交的 logo。

        2016 那届只有图没有名字，认不出是谁家的，所以表里没有 jae2016。
        """
        expo = [url for url in MODULE.LOGO_SOURCES.values() if "jae.tokyo" in url]
        self.assertEqual(len(expo), 26)
        self.assertEqual([url for url in expo if "jae2016" in url], [])
        for url in expo:
            with self.subTest(url=url):
                self.assertRegex(url, r"^http://www\.jae\.tokyo/jae201[457]/")

    def test_fc2_is_the_registered_logo_source(self):
        """用户 2026-09-03 指定的是 seeklogo 的 429409（600×600 方形锁定图）。

        同站那份 2000×662 是横向字标，不是这一位要的东西。
        """
        self.assertIn("fc2-logo-png_seeklogo-429409",
                      self.original[MODULE.safe_name("FC2-PPV")])

    def test_a_studio_without_a_registered_source_gets_no_logo_row(self):
        self.assertIsNone(MODULE.logo_row("HEYZO", self.target, self.entries,
                                          Fetch(), self.candidates))

    def test_a_wide_wordmark_is_accepted_here(self):
        """`icon` 位退回的形状正是这一位要的。两个位置本来就要两种东西。"""
        row = self.row(block_png((600, 200)))
        self.assertEqual((row["verdict"], row["variant"]), (MODULE.OK, MODULE.LOGO))
        self.assertEqual(row["mark_size"], "600x200")
        self.assertTrue(str(row["candidate"]).endswith("Fitch.logo.png"))
        self.assertEqual(row["url"], self.url, "记的是取图那一份的地址，不是官网")

    def test_the_recorded_sha256_matches_the_stored_file(self):
        row = self.row(block_png((600, 200)))
        stored = Path(str(row["candidate"])).read_bytes()
        self.assertEqual(hashlib.sha256(stored).hexdigest(), row["sha256"])

    def test_a_thumbnail_sized_logo_is_refused(self):
        """大位是 160 px、2x 屏 320 px。短边 64 说明取到的是缩略图不是标识资产。"""
        row = self.row(block_png((64, 64)))
        self.assertEqual(row["verdict"], MODULE.TOOSMALL)
        self.assertEqual(row["candidate"], "")

    def test_a_source_that_cannot_be_fetched_is_未取得(self):
        row = self.row(reachable=False)
        self.assertEqual(row["verdict"], MODULE.MISSING)

    def test_a_source_that_is_not_an_image_is_未取得(self):
        row = self.row(b"<html>404</html>")
        self.assertEqual(row["verdict"], MODULE.MISSING)
        self.assertIn("解不开", row["evidence"])


class Fetch:
    """`fetch.fetched` 是 harvest 用来分辨「站点不可达」和「取到了但都是字标」的
    唯一依据，所以替身也得照着记数，不能只当个哑函数。"""

    def __init__(self, pages=None, reachable=True):
        self.pages = pages or {}
        self.reachable = reachable
        self.fetched = 0
        self.asked: list[str] = []

    def __call__(self, url):
        self.asked.append(url)
        if not self.reachable:
            return None
        if self.pages:
            got = self.pages.get(url)
            if got is None:
                return None
            self.fetched += 1
            return got, "image/png"
        self.fetched += 1
        return b"payload", "image/png"


class HarvestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.candidates = self.root / "candidates"
        self.targets = {"Fitch": {"original_size": "130x43", "installed": "Fitch.img"}}
        self.links = {"Fitch": [{"entity_id": 5591, "studio": "Fitch",
                                 "link_kind": "official", "url": "https://fitch-av.com/"}]}

    def tearDown(self):
        self.tmp.cleanup()

    def run_harvest(self, mark, targets=None, links=None, reachable=True, fetch=None):
        fetch = fetch if fetch is not None else Fetch(reachable=reachable)
        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, render, fallback=None, accept=None):
            fetcher(url)
            return mark

        MODULE.site_icons.best_mark = stub
        try:
            return MODULE.harvest(self.targets if targets is None else targets,
                                  self.links if links is None else links,
                                  fetch, self.candidates)
        finally:
            MODULE.site_icons.best_mark = original

    def test_a_square_mark_becomes_an_ok_row_with_a_file(self):
        rows = self.run_harvest(png_bytes())
        self.assertEqual(rows[0]["verdict"], MODULE.OK)
        self.assertTrue(Path(str(rows[0]["candidate"])).is_file())
        self.assertEqual(rows[0]["safe"], "Fitch")

    def test_a_studio_with_no_official_link_is_skipped_not_failed(self):
        """没链接是「这条路走不通」，不是取证失败，两者的下一步动作不同。"""
        rows = self.run_harvest(png_bytes(), links={})
        self.assertEqual(rows[0]["verdict"], MODULE.SKIP)
        self.assertEqual(rows[0]["url"], "")

    def test_another_wordmark_is_rejected_not_stored(self):
        """闸门退回来就该空手而归：把同一条字标缩小再存一遍等于什么都没做。"""
        rows = self.run_harvest(None)
        self.assertEqual(rows[0]["verdict"], MODULE.WORDMARK)
        self.assertEqual(rows[0]["candidate"], "")
        self.assertFalse(self.candidates.exists())

    def test_an_unreachable_site_is_未取得_not_a_conclusion(self):
        """Idea Pocket 和 MOODYZ 的首页实测握手就断。那是「还没查到」，
        不是「这个厂牌只有字标」——写成后者会让人再也不去重试。"""
        rows = self.run_harvest(None, reachable=False)
        self.assertEqual(rows[0]["verdict"], MODULE.MISSING)
        self.assertIn("一份字节都没取回来", rows[0]["evidence"])

    def test_the_evidence_names_the_url_that_was_tried(self):
        rows = self.run_harvest(None)
        self.assertIn("https://fitch-av.com/", rows[0]["evidence"])

    def test_only_small_icons_is_its_own_verdict(self):
        """FC2 全站只有 16×16。那不是「只有字标」，下一步是找更大的资产。
        两者混成一个结论，就再没人会去找了。"""
        rows = self.harvest_with_reasons(["只有 16x16"])
        self.assertEqual(rows[0]["verdict"], MODULE.TOOSMALL)

    def harvest_with_reasons(self, reasons):
        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, policy, fallback=None, accept=None):
            fetcher(url)
            policy.reasons.extend(reasons)
            return None

        MODULE.site_icons.best_mark = stub
        try:
            return MODULE.harvest(self.targets, self.links, Fetch(), self.candidates)
        finally:
            MODULE.site_icons.best_mark = original

    def test_every_row_declares_which_variant_it_is(self):
        """CSV 里 icon 行和 logo 行长得一样，不写 variant 就分不出装到哪个位置。"""
        rows = self.run_harvest(png_bytes())
        self.assertEqual([row["variant"] for row in rows], [MODULE.ICON])

    def test_a_rejected_wordmark_is_baked_into_a_plate_and_installed_anyway(self):
        """用户 2026-09-03 的口径：不是 icon 也可以装 icon，尽量不要落入无图。"""
        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, policy, fallback=None, accept=None):
            fetcher(url)
            policy(block_png((298, 50)))
            return None

        MODULE.site_icons.best_mark = stub
        try:
            rows = MODULE.harvest(self.targets, self.links, Fetch(), self.candidates)
        finally:
            MODULE.site_icons.best_mark = original
        row = rows[0]
        self.assertEqual(row["verdict"], MODULE.PADDED)
        self.assertIn(MODULE.PADDED, MODULE.INSTALLABLE)
        with Image.open(io.BytesIO(Path(str(row["candidate"])).read_bytes())) as image:
            self.assertEqual(image.size, (PLATE_SIDE, PLATE_SIDE), "烤出来必须是方的")
            self.assertNotIn("A", image.getbands(), "装进去的文件必须不透明")
        self.assertEqual(row["mark_size"], PLATE_SIZE)
        self.assertGreater(float(row["content_aspect"]),
                           MODULE.link_marks.MAX_CONTENT_ASPECT,
                           "内容比照记：那个数就是「这枚其实是字标」的提示")
        self.assertIn("方形标识未取得，装的是字标", row["evidence"])

    def run_wordmark_harvest(self, targets=None, links=None, fetch=None):
        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, policy, fallback=None, accept=None):
            fetcher(url)
            policy(block_png((298, 50)))
            return None

        MODULE.site_icons.best_mark = stub
        try:
            return MODULE.harvest(self.targets if targets is None else targets,
                                  self.links if links is None else links,
                                  fetch or Fetch(), self.candidates)
        finally:
            MODULE.site_icons.best_mark = original

    def test_the_wordmark_plate_also_fills_the_logo_slot(self):
        """只装 icon 位，BangBus 页顶上会回落到母品牌的 `BangBus.img`（BANGBROS 字标）：
        小位对了，大位挂着别家的牌子。"""
        rows = self.run_wordmark_harvest()
        self.assertEqual([row["variant"] for row in rows], [MODULE.ICON, MODULE.LOGO])
        logo = rows[1]
        self.assertEqual(logo["verdict"], MODULE.OK)
        self.assertEqual(logo["safe"], rows[0]["safe"])
        payload = Path(str(logo["candidate"])).read_bytes()
        self.assertEqual(logo["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(logo["content_aspect"], rows[0]["content_aspect"])
        self.assertIn("298x50", logo["evidence"], "原字标尺寸留在证据里供复核")
        self.assertNotEqual(logo["candidate"], rows[0]["candidate"],
                            "两份候选文件不能互相覆盖")

    def test_the_logo_slot_gets_an_opaque_square(self):
        """厂牌页大位是 160px 的 `object-fit: cover` 方框，宽条装上去只剩中间两个字母。

        两位共用同一份烤好的方图，字节一致才能保证两个位置显示同一枚标识。
        """
        rows = self.run_wordmark_harvest()
        logo = rows[1]
        with Image.open(io.BytesIO(Path(str(logo["candidate"])).read_bytes())) as image:
            self.assertEqual(image.size, (PLATE_SIDE, PLATE_SIDE))
            self.assertNotIn("A", image.getbands())
        self.assertEqual(logo["mark_size"], PLATE_SIZE)
        self.assertEqual(logo["sha256"], rows[0]["sha256"], "与 icon 位同一份字节")

    def test_a_wordmark_logo_installs_into_the_logo_file(self):
        rows = self.run_wordmark_harvest()
        logos = self.root / "logos"
        written = MODULE.install(rows, logos)
        self.assertEqual(written, ["Fitch.icon.img", "Fitch.img", "Fitch.logo.img"])
        for name in ("Fitch.logo.img", "Fitch.icon.img", "Fitch.img"):
            with self.subTest(name=name), Image.open(logos / name) as image:
                self.assertEqual(image.size, (PLATE_SIDE, PLATE_SIDE))
                self.assertNotIn("A", image.getbands())

    def test_install_bakes_every_candidate_into_an_opaque_square(self):
        """装盘的字节过同一个烤底入口，所以 logo 目录里天然没有透明底和长条。

        入口只有这一个，`normalize_studio_logos.py` 是同一条规则对历史文件的回溯。
        """
        rows = self.run_wordmark_harvest()
        logos = self.root / "logos"
        # 候选换成一枚透明底的方标：过得了内容比闸门，可它还是透明的。
        transparent = block_png((256, 256), inset=32)
        candidate = self.candidates / "transparent.png"
        candidate.write_bytes(transparent)
        rows[0]["candidate"] = str(candidate)
        rows[0]["sha256"] = hashlib.sha256(transparent).hexdigest()
        MODULE.install([rows[0]], logos)
        with Image.open(logos / "Fitch.icon.img") as image:
            self.assertNotIn("A", image.getbands(), "透明底的方标也要烤上白底")
            self.assertEqual(image.size[0], image.size[1])
        provenance = json.loads(
            (logos / "Fitch.icon.img.provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["sha256"], rows[0]["sha256"], "候选自己的哈希")
        self.assertEqual(
            provenance["installed_sha256"],
            hashlib.sha256((logos / "Fitch.icon.img").read_bytes()).hexdigest(),
            "真正写进目录的那一份另记一列，否则复核时对不上文件")

    def test_a_working_designated_logo_source_wins_over_the_wordmark(self):
        targets = {"FC2-PPV": {"original_size": "", "installed": ""}}
        links = {"FC2-PPV": [{"entity_id": 1, "studio": "FC2-PPV",
                              "link_kind": "official", "url": "https://fc2.com/"}]}
        source = MODULE.LOGO_SOURCES_BY_SAFE["FC2-PPV"]
        rows = self.run_wordmark_harvest(targets, links, Fetch(pages={source: png_bytes()}))
        logos = [row for row in rows if row["variant"] == MODULE.LOGO]
        self.assertEqual(len(logos), 1, "两行 logo 装进同一个文件，后写的会盖掉先写的")
        self.assertEqual(logos[0]["link_kind"], "logo-source")

    def test_a_failed_designated_source_keeps_its_row_and_the_wordmark_logo_follows(self):
        targets = {"FC2-PPV": {"original_size": "", "installed": ""}}
        links = {"FC2-PPV": [{"entity_id": 1, "studio": "FC2-PPV",
                              "link_kind": "official", "url": "https://fc2.com/"}]}
        rows = self.run_wordmark_harvest(targets, links, Fetch(reachable=False))
        logos = [row for row in rows if row["variant"] == MODULE.LOGO]
        self.assertEqual([row["verdict"] for row in logos], [MODULE.MISSING, MODULE.OK])
        self.assertEqual(logos[0]["candidate"], "", "失败行没有候选，安装时不会落地")
        self.assertTrue(logos[1]["candidate"])

    def designated_source_harvest(self, studio, payload):
        """账本里一条链接都没有的厂牌：`best_mark` 根本不会被调，不用替身。"""
        safe = MODULE.safe_name(studio)
        url = f"http://logos.example/{safe}.png"
        original = dict(MODULE.LOGO_SOURCES_BY_SAFE)
        names = dict(MODULE.LOGO_SOURCE_NAMES)
        MODULE.LOGO_SOURCES_BY_SAFE[safe] = url
        MODULE.LOGO_SOURCE_NAMES[safe] = studio
        try:
            return MODULE.harvest({safe: {"original_size": "", "installed": ""}}, {},
                                  Fetch(pages={url: payload}), self.candidates)
        finally:
            MODULE.LOGO_SOURCES_BY_SAFE.clear()
            MODULE.LOGO_SOURCES_BY_SAFE.update(original)
            MODULE.LOGO_SOURCE_NAMES.clear()
            MODULE.LOGO_SOURCE_NAMES.update(names)

    def test_a_link_less_studio_takes_its_icon_from_the_designated_logo(self):
        """小位空着不是因为找不到图，是因为发现流程从官网出发，而它没有官网。

        大位这张是厂牌自己在名录里交的标识资产，比任何 favicon 都准，两位共用它。
        """
        rows = self.designated_source_harvest("俺の素人", png_bytes((320, 320)))
        icon, logo = rows[0], rows[1]
        self.assertEqual([row["variant"] for row in rows], [MODULE.ICON, MODULE.LOGO])
        self.assertEqual(icon["verdict"], MODULE.OK, "本来就是方图，一个像素都没动")
        self.assertEqual(icon["link_kind"], "logo-source")
        self.assertEqual(icon["url"], logo["url"], "小位记的是取图那一份的地址")
        self.assertEqual(icon["mark_size"], "320x320")
        self.assertIn("与 logo 位同一份指定来源", icon["evidence"])
        stored = Path(str(icon["candidate"])).read_bytes()
        self.assertEqual(hashlib.sha256(stored).hexdigest(), icon["sha256"])
        self.assertNotEqual(icon["candidate"], logo["candidate"],
                            "两份候选文件不能互相覆盖")

    def test_the_review_row_names_the_studio_a_japanese_name_cannot_survive(self):
        """`俺の素人` 的安全文件名是一排下划线，复核件上照那个反推认不出是谁家的。"""
        rows = self.designated_source_harvest("俺の素人", png_bytes((320, 320)))
        self.assertEqual(rows[0]["studio"], "俺の素人")
        self.assertEqual(rows[0]["safe"], MODULE.safe_name("俺の素人"))

    def test_a_wide_designated_logo_is_padded_for_the_small_slot(self):
        """名录里 2014 那届是 270×180 的横向字标。补白装上去也比露出无图强。"""
        rows = self.designated_source_harvest("TEPPAN", png_bytes((270, 180)))
        icon = rows[0]
        self.assertEqual(icon["verdict"], MODULE.PADDED)
        self.assertIn(MODULE.PADDED, MODULE.INSTALLABLE)
        with Image.open(io.BytesIO(Path(str(icon["candidate"])).read_bytes())) as image:
            self.assertEqual(image.size[0], image.size[1], "小位装的必须是方图")
            if "A" in image.getbands():
                # 名录 2014 那届是整幅不透明的 jpg，补白按边缘主色填，不该留出透明边。
                self.assertEqual(image.getchannel("A").getextrema(), (255, 255))

    def test_a_designated_source_fills_both_files_for_a_link_less_studio(self):
        rows = self.designated_source_harvest("Dogma", png_bytes((320, 320)))
        logos = self.root / "logos"
        self.assertEqual(MODULE.install(rows, logos),
                         ["Dogma.icon.img", "Dogma.img", "Dogma.logo.img"])

    def test_a_studio_with_a_working_icon_keeps_it_over_the_designated_logo(self):
        """官网做出方标时不动小位：那一枚才是这个站自己声明的图标。"""
        url = "http://logos.example/Fitch.png"
        original = dict(MODULE.LOGO_SOURCES_BY_SAFE)
        MODULE.LOGO_SOURCES_BY_SAFE["Fitch"] = url
        try:
            rows = self.run_harvest(png_bytes(), fetch=Fetch(pages={url: png_bytes()}))
        finally:
            MODULE.LOGO_SOURCES_BY_SAFE.clear()
            MODULE.LOGO_SOURCES_BY_SAFE.update(original)
        self.assertEqual(rows[0]["link_kind"], "official")
        self.assertEqual(rows[0]["verdict"], MODULE.OK)

    def test_a_wordmark_too_small_to_pad_is_still_a_wordmark_verdict(self):
        """16 px 高的条状 favicon 补白也救不回来，装上去只是一条糊线。"""
        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, policy, fallback=None, accept=None):
            fetcher(url)
            policy(block_png((64, 16), inset=2))
            return None

        MODULE.site_icons.best_mark = stub
        try:
            rows = MODULE.harvest(self.targets, self.links, Fetch(), self.candidates)
        finally:
            MODULE.site_icons.best_mark = original
        self.assertEqual(rows[0]["verdict"], MODULE.WORDMARK)
        self.assertEqual(rows[0]["candidate"], "")

    def test_a_platform_wide_favicon_gets_its_own_verdict(self):
        """MonstersOfCock 的实测形态：主机级 favicon 过了所有闸门，仍然不是它的标识。

        判成「仍是字标」会让人以为查过了这个频道，其实查的是整个 bangbros.com。
        """
        links = {"MonstersOfCock": [{
            "entity_id": 5622, "studio": "MonstersOfCock", "link_kind": "official",
            "url": "https://network.example/websites/MonstersOfCock"}]}
        targets = {"MonstersOfCock": {"original_size": "296x82",
                                      "installed": "MonstersOfCock.img"}}
        template = block_png((64, 64), inset=6)
        fetch = Fetch({
            "https://network.example": b'<link rel="icon" sizes="64x64" href="/f.png">',
            "https://network.example/f.png": template,
            "https://network.example/favicon.ico": template,
            "https://network.example/apple-touch-icon.png": template})
        rows = MODULE.harvest(targets, links, fetch, self.candidates)
        self.assertEqual(rows[0]["verdict"], MODULE.SHARED)
        self.assertEqual(rows[0]["candidate"], "")
        self.assertIn("network.example", rows[0]["evidence"])
        self.assertIn(hashlib.sha256(template).hexdigest()[:8], rows[0]["evidence"],
                      "证据要指名取到的是哪一份，不然没法复查")

    def test_a_root_link_is_not_subject_to_the_shared_host_guard(self):
        """`https://honnaka.jp/` 指的就是整个主机，它的 favicon 就是它的标识。"""
        icon = block_png((128, 128), inset=10)
        fetch = Fetch({
            "https://honnaka.jp": b'<link rel="icon" sizes="128x128" href="/f.png">',
            "https://honnaka.jp/f.png": icon})
        rows = MODULE.harvest(
            {"Hon_Naka": {"original_size": "", "installed": ""}},
            {"Hon_Naka": [{"entity_id": 5599, "studio": "Hon Naka",
                           "link_kind": "official", "url": "https://honnaka.jp/"}]},
            fetch, self.candidates)
        self.assertEqual(rows[0]["verdict"], MODULE.OK)
        self.assertEqual(rows[0]["mark_size"], "128x128")


class SquareMarkTests(unittest.TestCase):
    """判「是不是方标」的那一层。这里判错过一次，代价是六个厂牌被误记成只有字标。"""

    def png(self, size, box=None, color=(220, 30, 90)):
        image = Image.new("RGB", size, "white")
        left, top, right, bottom = box or (0, 0, size[0], size[1])
        for x in range(left, right):
            for y in range(top, bottom):
                image.putpixel((x, y), color)
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        return buffer.getvalue()

    def test_a_square_favicon_passes_at_its_native_size(self):
        """32×32 的 favicon 顶 28px 的筛选片绰绰有余。`link_marks.render_mark`
        的 MIN_DESIGNED_SIZE=96 是给 128px 圆标定的，套到这里会把它们全退掉。"""
        policy = MODULE.SquareMark()
        made = policy(self.png((32, 32), (4, 4, 28, 28)))
        self.assertIsNotNone(made)
        self.assertEqual(policy.size, "32x32")
        with Image.open(io.BytesIO(made)) as image:
            self.assertEqual(image.size, (32, 32), "不放大：插值只会更糊")

    def test_a_wide_wordmark_is_refused(self):
        policy = MODULE.SquareMark()
        self.assertIsNone(policy(self.png((256, 64), (4, 24, 252, 40))))
        self.assertTrue(any("字标" in reason for reason in policy.reasons))

    def test_a_tiny_icon_is_refused_with_its_size(self):
        policy = MODULE.SquareMark()
        self.assertIsNone(policy(self.png((16, 16), (2, 2, 14, 14))))
        self.assertEqual(policy.reasons, ["只有 16x16"])

    def test_the_passing_aspect_is_recorded_for_review(self):
        """Fitch 以 1.84 压线过闸，其余六个都在 1.15 以下。复核要看得见这个数。"""
        policy = MODULE.SquareMark()
        policy(self.png((64, 64), (2, 18, 62, 46)))
        self.assertTrue(policy.aspect)
        self.assertGreater(float(policy.aspect), 1.0)

    def test_an_octet_stream_png_is_still_a_png(self):
        """用户指定的 FC2 图标那台服务器回 `application/octet-stream`。

        按 content-type 决定能不能解会把它整枚丢掉；`link_marks.decode` 靠 PIL 嗅探。
        """
        policy = MODULE.SquareMark()
        made = policy(block_png((400, 400), inset=20),
                      content_type="application/octet-stream")
        self.assertIsNotNone(made)
        self.assertEqual(policy.size, "400x400")

    def test_a_refused_wordmark_is_kept_for_the_padding_fallback(self):
        """退回的理由要留，退回的**字节**也要留：字标现在是可装的回落。"""
        policy = MODULE.SquareMark()
        self.assertIsNone(policy(block_png((298, 50))))
        self.assertIsNotNone(policy.wordmark)
        self.assertEqual(policy.wordmark_size, "298x50")
        self.assertGreater(float(policy.wordmark_aspect),
                           MODULE.link_marks.MAX_CONTENT_ASPECT)

    def test_the_first_refused_wordmark_wins_not_the_last(self):
        """`best_mark` 的遍历顺序已经是「覆盖表 → 声明 → 根路径猜测」。

        留最后一份等于让根路径的猜测盖掉覆盖表里指定的那一份。
        """
        policy = MODULE.SquareMark()
        policy(block_png((298, 50)))
        policy(block_png((512, 64)))
        self.assertEqual(policy.wordmark_size, "298x50")

    def test_a_wordmark_below_the_short_edge_is_not_kept(self):
        policy = MODULE.SquareMark()
        self.assertIsNone(policy(block_png((64, 16), inset=2)))
        self.assertIsNone(policy.wordmark)


class RunTests(unittest.TestCase):
    """整条链路：账本 + 已安装目录 → 复核 CSV，`--install` 才落盘。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.logos = self.root / "logos"
        self.logos.mkdir()
        for safe in ("Fitch", "HEYZO", "kawaii"):
            (self.logos / f"{safe}.img").write_bytes(b"padded wordmark")
            (self.logos / f"{safe}.img.normalization.json").write_text(
                json.dumps({"action": "pad-to-square",
                            "original_width": 130, "original_height": 43}),
                encoding="utf-8")
        self.database = self.root / "ledger.db"
        connection = sqlite3.connect(self.database)
        connection.executescript(
            "CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT);"
            "CREATE TABLE entity_link(id INTEGER PRIMARY KEY, entity_id INTEGER,"
            " link_kind TEXT, label TEXT, url TEXT);")
        connection.executemany(
            "INSERT INTO entity(id, kind, canonical_name) VALUES(?,?,?)",
            [(1, "studio", "Fitch"), (2, "studio", "HEYZO"), (3, "studio", "kawaii"),
             (4, "studio", "Hon Naka")])
        connection.executemany(
            "INSERT INTO entity_link(entity_id, link_kind, label, url) VALUES(?,?,?,?)",
            [(1, "official", "官方网站", "https://fitch-av.com/"),
             (2, "official", "官方网站", "https://www.heyzo.com/"),
             # 有链接、一张图都没有：账本里 Hon Naka 就是这一例。
             (4, "official", "官方网站", "https://honnaka.jp/")])
        connection.commit()
        connection.close()
        # 指定来源那张真表指向站外地址，留着这一整套测试就会去联网取图。
        self.sources = dict(MODULE.LOGO_SOURCES_BY_SAFE)
        MODULE.LOGO_SOURCES_BY_SAFE.clear()

    def tearDown(self):
        MODULE.LOGO_SOURCES_BY_SAFE.clear()
        MODULE.LOGO_SOURCES_BY_SAFE.update(self.sources)
        self.tmp.cleanup()

    def invoke(self, install=False, marks=None):
        """只有 Fitch 能做出方标；kawaii 根本没链接。

        替身不调 `fetcher`——真调下去就是往 fitch-av.com 发请求，测试不联网。
        """
        marks = marks if marks is not None else {"https://fitch-av.com/": png_bytes()}
        original = MODULE.site_icons.best_mark
        MODULE.site_icons.best_mark = (
            lambda url, fetcher, render, fallback=None, accept=None: marks.get(url))
        try:
            return MODULE.run(SimpleNamespace(
                database=self.database, output=self.root / "studio-icons.csv",
                logo_root=self.logos, candidate_dir=self.root / "candidates",
                only=[], interval=0.0, timeout=1.0, install=install))
        finally:
            MODULE.site_icons.best_mark = original

    def read_csv(self):
        from peach.review_csv import read_rows
        return list(read_rows(self.root / "studio-icons.csv"))

    def test_the_csv_covers_every_target_studio(self):
        stats = self.invoke()
        self.assertEqual(stats["复核行"], 4)
        self.assertEqual({row["safe"] for row in self.read_csv()},
                         {"Fitch", "HEYZO", "kawaii", "Hon_Naka"})

    def test_ok_rows_come_first(self):
        """人工复核从上往下看，能用的那几行不该埋在一堆「无官网链接」下面。"""
        self.invoke()
        self.assertEqual(self.read_csv()[0]["safe"], "Fitch")
        self.assertEqual(self.read_csv()[0]["verdict"], MODULE.OK)

    def test_a_studio_with_no_link_is_counted_separately(self):
        stats = self.invoke()
        self.assertEqual((stats["ok"], stats["无官网链接"]), (1, 1))

    def test_reporting_never_touches_the_installed_directory(self):
        """默认只出复核件。装图必须是显式的第二步。"""
        self.invoke()
        self.assertEqual(sorted(path.name for path in self.logos.glob("*.icon.img")), [])

    def test_install_writes_only_the_new_variant_files(self):
        stats = self.invoke(install=True)
        self.assertEqual(stats["已安装"], ["Fitch.icon.img"])
        self.assertEqual(sorted(path.name for path in self.logos.glob("*.logo.img")), [])

    def test_only_narrows_the_batch(self):
        original = MODULE.site_icons.best_mark
        MODULE.site_icons.best_mark = (
            lambda url, fetcher, render, fallback=None, accept=None: None)
        try:
            stats = MODULE.run(SimpleNamespace(
                database=self.database, output=self.root / "studio-icons.csv",
                logo_root=self.logos, candidate_dir=self.root / "candidates",
                only=["HEYZO"], interval=0.0, timeout=1.0, install=False))
        finally:
            MODULE.site_icons.best_mark = original
        self.assertEqual(stats["复核行"], 1)
        self.assertEqual(self.read_csv()[0]["safe"], "HEYZO")

    def test_a_studio_with_a_link_but_no_image_joins_the_batch(self):
        """账本里 Hon Naka 就是这一例：不在补白名单里，两个位置照样是空的。"""
        stats = self.invoke()
        self.assertIn("Hon_Naka", {row["safe"] for row in self.read_csv()})
        self.assertEqual(stats["目标厂牌"], 4)
        empty = [row for row in self.read_csv() if row["safe"] == "Hon_Naka"][0]
        self.assertEqual((empty["installed"], empty["original_size"]), ("", ""))

    def test_install_also_writes_the_plain_file_for_a_studio_with_no_image(self):
        """`<safe>.img` 是不带 variant 和认不出的 variant 的回落。

        只写 `<safe>.icon.img` 的话，厂牌页那个 160 px 大位仍然 404。
        """
        stats = self.invoke(install=True,
                            marks={"https://honnaka.jp/": png_bytes()})
        self.assertEqual(sorted(stats["已安装"]),
                         ["Hon_Naka.icon.img", "Hon_Naka.img"])
        self.assertTrue((self.logos / "Hon_Naka.img.ct").is_file())

    def test_install_never_overwrites_an_existing_plain_file(self):
        stats = self.invoke(install=True)
        self.assertEqual(stats["已安装"], ["Fitch.icon.img"])
        self.assertEqual((self.logos / "Fitch.img").read_bytes(), b"padded wordmark")


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.logos = self.root / "logos"
        self.logos.mkdir()
        (self.logos / "Fitch.img").write_bytes(b"the padded wordmark")
        self.payload = png_bytes()
        candidate = self.root / "Fitch.png"
        candidate.write_bytes(self.payload)
        self.row = {"verdict": MODULE.OK, "safe": "Fitch", "candidate": str(candidate),
                    "sha256": hashlib.sha256(self.payload).hexdigest(),
                    "url": "https://fitch-av.com/"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_icon_lands_beside_the_existing_file(self):
        """加的是新文件名。已安装的 `<safe>.img` 一个字节都不能动。"""
        written = MODULE.install([self.row], self.logos)
        self.assertEqual(written, ["Fitch.icon.img"])
        self.assertEqual((self.logos / "Fitch.icon.img").read_bytes(), self.payload)
        self.assertEqual((self.logos / "Fitch.img").read_bytes(), b"the padded wordmark")

    def test_the_content_type_sidecar_is_written(self):
        MODULE.install([self.row], self.logos)
        self.assertEqual((self.logos / "Fitch.icon.img.ct").read_text(encoding="utf-8"),
                         "image/png")

    def test_provenance_records_the_source_url(self):
        MODULE.install([self.row], self.logos)
        data = json.loads((self.logos / "Fitch.icon.img.provenance.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(data["source_url"], "https://fitch-av.com/")
        self.assertEqual(data["variant"], "icon")

    def test_a_tampered_candidate_is_refused(self):
        Path(str(self.row["candidate"])).write_bytes(b"something else")
        with self.assertRaises(ValueError):
            MODULE.install([self.row], self.logos)
        self.assertFalse((self.logos / "Fitch.icon.img").exists())

    def test_rows_that_did_not_pass_install_nothing(self):
        for verdict in (MODULE.WORDMARK, MODULE.SHARED, MODULE.TOOSMALL, MODULE.MISSING):
            with self.subTest(verdict=verdict):
                MODULE.install([dict(self.row, verdict=verdict)], self.logos)
                self.assertFalse((self.logos / "Fitch.icon.img").exists())

    def test_a_padded_wordmark_installs_too(self):
        """用户的口径是「不是 icon 也可以装 icon」，所以这个判词必须真的会落盘。"""
        written = MODULE.install([dict(self.row, verdict=MODULE.PADDED)], self.logos)
        self.assertEqual(written, ["Fitch.icon.img"])

    def test_the_logo_variant_lands_in_its_own_file(self):
        row = dict(self.row, variant=MODULE.LOGO)
        self.assertEqual(MODULE.install([row], self.logos), ["Fitch.logo.img"])
        self.assertEqual((self.logos / "Fitch.logo.img").read_bytes(), self.payload)
        self.assertEqual((self.logos / "Fitch.logo.img.ct").read_text(encoding="utf-8"),
                         "image/png")
        data = json.loads((self.logos / "Fitch.logo.img.provenance.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(data["variant"], MODULE.LOGO)

    def test_a_row_without_a_variant_still_installs_as_the_icon(self):
        """老复核件没有这一列。读到 `None` 就不装等于把上一批全废掉。"""
        self.row.pop("variant", None)
        self.assertEqual(MODULE.install([self.row], self.logos), ["Fitch.icon.img"])

    def test_the_provenance_records_the_verdict(self):
        """装上去的那一枚是方标还是补白字标，事后只能从这里看出来。"""
        MODULE.install([dict(self.row, verdict=MODULE.PADDED)], self.logos)
        data = json.loads((self.logos / "Fitch.icon.img.provenance.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(data["verdict"], MODULE.PADDED)


class StudioLinkTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            "CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT);"
            "CREATE TABLE entity_link(id INTEGER PRIMARY KEY, entity_id INTEGER,"
            " link_kind TEXT, label TEXT, url TEXT);")
        self.connection.executemany(
            "INSERT INTO entity(id, kind, canonical_name) VALUES(?,?,?)",
            [(1, "studio", "Idea Pocket"), (2, "studio", "Fitch"), (3, "performer", "某人"),
             (4, "studio", "FC2-PPV")])
        self.connection.executemany(
            "INSERT INTO entity_link(entity_id, link_kind, label, url) VALUES(?,?,?,?)",
            [(1, "official", "官方网站", "https://ideapocket.com/"),
             (1, "social", "X", "https://x.com/ideapocket"),
             (3, "official", "官方网站", "https://example.com/"),
             (4, "catalog", "FC2-PPV", "https://adult.contents.fc2.com/")])

    def tearDown(self):
        self.connection.close()

    def test_social_links_are_left_out(self):
        """社媒头像是另一条线的产物，混进来会把厂牌小标换成运营的自拍。"""
        links = MODULE.studio_links(self.connection)
        self.assertEqual([item["url"] for item in links["Idea_Pocket"]],
                         ["https://ideapocket.com/"])
        self.assertNotIn("某人", links, "performer 的链接不该进厂牌图标线")

    def test_a_platform_keeps_its_catalog_link_as_an_icon_source(self):
        """发行平台按 `docs/SOURCING.md` 不登记 official——它不是厂牌，没有厂牌官网。

        可它照样占着筛选片和卡片徽标那几个位置。只认 official 的话，FC2-PPV 会在复核件上
        记成「无官网链接」，看起来像漏采，其实是查都没查。
        """
        links = MODULE.studio_links(self.connection)
        self.assertEqual(sorted(links), ["FC2-PPV", "Idea_Pocket"])
        self.assertEqual([item["url"] for item in links["FC2-PPV"]],
                         ["https://adult.contents.fc2.com/"])

    def test_the_key_is_the_installed_file_name(self):
        """归拢键必须是文件名，否则和 `padded_studios` 对不上。"""
        self.assertIn("Idea_Pocket", MODULE.studio_links(self.connection))


if __name__ == "__main__":
    unittest.main()
