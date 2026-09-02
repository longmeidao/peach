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

from peach.previews import PreviewService, PreviewUnavailable


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
            "'/logo?studio='+encodeURIComponent(img.dataset.studio)+'&variant=icon'",
        ):
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
        """补白之后每一张都是方的，从像素上再也看不出原来是条状——只能认边车。"""
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


class HarvestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.candidates = self.root / "candidates"
        self.padded = {"Fitch": {"width": 130, "height": 43}}
        self.links = {"Fitch": [{"entity_id": 5591, "studio": "Fitch",
                                 "link_kind": "official", "url": "https://fitch-av.com/"}]}

    def tearDown(self):
        self.tmp.cleanup()

    def run_harvest(self, mark, padded=None, links=None, reachable=True):
        """`fetch.fetched` 是 harvest 用来分辨「站点不可达」和「取到了但都是字标」的
        唯一依据，所以替身也得照着记数，不能只当个哑函数。"""
        class Fetch:
            fetched = 0

            def __call__(self, url):
                if reachable:
                    Fetch.fetched += 1
                    return b"payload", "image/png"
                return None

        fetch = Fetch()
        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, render, fallback=None):
            fetcher(url)
            return mark

        MODULE.site_icons.best_mark = stub
        try:
            return MODULE.harvest(self.padded if padded is None else padded,
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
        class Fetch:
            fetched = 0

            def __call__(self, url):
                Fetch.fetched += 1
                return b"payload", "image/png"

        original = MODULE.site_icons.best_mark

        def stub(url, fetcher, policy, fallback=None):
            fetcher(url)
            policy.reasons.append("只有 16x16")
            return None

        MODULE.site_icons.best_mark = stub
        try:
            rows = MODULE.harvest(self.padded, self.links, Fetch(), self.candidates)
        finally:
            MODULE.site_icons.best_mark = original
        self.assertEqual(rows[0]["verdict"], MODULE.TOOSMALL)


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
            [(1, "studio", "Fitch"), (2, "studio", "HEYZO"), (3, "studio", "kawaii")])
        connection.executemany(
            "INSERT INTO entity_link(entity_id, link_kind, label, url) VALUES(?,?,?,?)",
            [(1, "official", "官方网站", "https://fitch-av.com/"),
             (2, "official", "官方网站", "https://www.heyzo.com/")])
        connection.commit()
        connection.close()

    def tearDown(self):
        self.tmp.cleanup()

    def invoke(self, install=False, marks=None):
        """只有 Fitch 能做出方标；kawaii 根本没链接。

        替身不调 `fetcher`——真调下去就是往 fitch-av.com 发请求，测试不联网。
        """
        marks = marks if marks is not None else {"https://fitch-av.com/": png_bytes()}
        original = MODULE.site_icons.best_mark
        MODULE.site_icons.best_mark = lambda url, fetcher, render, fallback=None: marks.get(url)
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

    def test_the_csv_covers_every_padded_studio(self):
        stats = self.invoke()
        self.assertEqual(stats["复核行"], 3)
        self.assertEqual({row["safe"] for row in self.read_csv()},
                         {"Fitch", "HEYZO", "kawaii"})

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
        self.assertEqual((self.logos / "Fitch.img").read_bytes(), b"padded wordmark")

    def test_only_narrows_the_batch(self):
        original = MODULE.site_icons.best_mark
        MODULE.site_icons.best_mark = lambda url, fetcher, render, fallback=None: None
        try:
            stats = MODULE.run(SimpleNamespace(
                database=self.database, output=self.root / "studio-icons.csv",
                logo_root=self.logos, candidate_dir=self.root / "candidates",
                only=["HEYZO"], interval=0.0, timeout=1.0, install=False))
        finally:
            MODULE.site_icons.best_mark = original
        self.assertEqual(stats["复核行"], 1)
        self.assertEqual(self.read_csv()[0]["safe"], "HEYZO")


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
        MODULE.install([dict(self.row, verdict=MODULE.WORDMARK)], self.logos)
        self.assertFalse((self.logos / "Fitch.icon.img").exists())


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
            [(1, "studio", "Idea Pocket"), (2, "studio", "Fitch"), (3, "performer", "某人")])
        self.connection.executemany(
            "INSERT INTO entity_link(entity_id, link_kind, label, url) VALUES(?,?,?,?)",
            [(1, "official", "官方网站", "https://ideapocket.com/"),
             (1, "social", "X", "https://x.com/ideapocket"),
             (3, "official", "官方网站", "https://example.com/")])

    def tearDown(self):
        self.connection.close()

    def test_only_official_studio_links_come_back(self):
        """社媒头像是另一条线的产物，混进来会把厂牌小标换成运营的自拍。"""
        links = MODULE.studio_links(self.connection)
        self.assertEqual(sorted(links), ["Idea_Pocket"])
        self.assertEqual([item["url"] for item in links["Idea_Pocket"]],
                         ["https://ideapocket.com/"])

    def test_the_key_is_the_installed_file_name(self):
        """归拢键必须是文件名，否则和 `padded_studios` 对不上。"""
        self.assertIn("Idea_Pocket", MODULE.studio_links(self.connection))


if __name__ == "__main__":
    unittest.main()
