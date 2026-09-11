# -*- coding: utf-8 -*-
"""横版封套里那块 2:3 竖海报取景框的判据。

图都是 Pillow 当场合成的，不依赖真实封面：折痕是一条画上去的竖线，位置已知，
所以「找到的那一列对不对」有确定答案可比。
"""
from __future__ import annotations

import functools
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from peach import jav_poster_crop
from peach.jav_poster_crop import FOLD, NONE, RATIO


def sleeve(width: int, height: int, fold: int | None) -> Image.Image:
    """一张封套：左边是背面，右边是正面，中间可选一条书脊折痕。"""
    image = Image.new("RGB", (width, height), (200, 200, 200))
    if fold is None:
        return image
    for x in range(fold, min(fold + 3, width)):
        for y in range(height):
            image.putpixel((x, y), (0, 0, 0))
    for x in range(min(fold + 3, width), width):
        for y in range(height):
            image.putpixel((x, y), (150, 150, 150))
    return image


def edge_left(width: int, height: int) -> Image.Image:
    """折痕带之外有一条强边，带内平整：这张图没有可采信的折痕。"""
    image = Image.new("RGB", (width, height), (200, 200, 200))
    for x in range(0, int(width * 0.1)):
        for y in range(height):
            image.putpixel((x, y), (10, 10, 10))
    return image


def gradient_of(image: Image.Image):
    import cv2
    import numpy

    array = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
    return jav_poster_crop.column_gradient(array)


def opencv_available() -> bool:
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


@functools.lru_cache(maxsize=1)
def batch_script():
    """把 `scripts/poster_crop_boxes.py` 当模块载入，按文件路径而不是包名。"""
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "poster_crop_boxes", root / "scripts" / "poster_crop_boxes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CropShapeTests(unittest.TestCase):
    """框的形状：严格 2:3，落在源图里，不越出正面那一块。"""

    def assert_two_by_three(self, box: dict, width: int, height: int):
        self.assertEqual((box["x1"] - box["x0"]) * 3, (box["y1"] - box["y0"]) * 2,
                         f"框不是 2:3：{box}")
        self.assertGreaterEqual(box["x0"], 0)
        self.assertGreaterEqual(box["y0"], 0)
        self.assertLessEqual(box["x1"], width)
        self.assertLessEqual(box["y1"], height)

    def test_the_box_stays_exactly_two_by_three_at_every_sleeve_size(self):
        for width, height in ((800, 539), (2184, 1464), (1000, 674), (760, 600)):
            with self.subTest(size=(width, height)):
                box = jav_poster_crop.portrait_crop_box(width, height)
                self.assertEqual(box["method"], RATIO)
                self.assert_two_by_three(box, width, height)

    def test_the_box_shrinks_instead_of_reaching_past_the_front_panel(self):
        """正面窄到放不下满高的 2:3 时，框按正面宽度收，不往折痕左边借。"""
        box = jav_poster_crop.portrait_crop_box(1000, 700, [0.0] * 1000)
        self.assertGreaterEqual(box["x0"], 500)
        self.assert_two_by_three(box, 1000, 700)

    def test_a_degenerate_size_gives_an_empty_box_and_no_method(self):
        self.assertEqual(jav_poster_crop.portrait_crop_box(0, 0),
                         {"x0": 0, "y0": 0, "x1": 0, "y1": 0, "method": NONE})


class MethodTests(unittest.TestCase):
    """三档各自的触发条件。"""

    @unittest.skipUnless(opencv_available(), "缺 vision 依赖组")
    def test_a_visible_spine_is_found_and_the_front_starts_there(self):
        width, height, fold = 800, 540, 420
        profile = gradient_of(sleeve(width, height, fold))
        self.assertIsNotNone(profile)
        found = jav_poster_crop.fold_column(width, profile)
        self.assertIsNotNone(found, "画上去的折痕没被找到")
        self.assertLessEqual(abs(found - fold), 2, found)
        box = jav_poster_crop.portrait_crop_box(width, height, profile)
        self.assertEqual(box["method"], FOLD)
        self.assertGreaterEqual(box["x0"], fold)
        self.assertEqual((box["x1"] - box["x0"]) * 3, (box["y1"] - box["y0"]) * 2)

    @unittest.skipUnless(opencv_available(), "缺 vision 依赖组")
    def test_without_a_spine_the_front_falls_back_to_the_right_half(self):
        width, height = 800, 540
        profile = gradient_of(edge_left(width, height))
        self.assertIsNone(jav_poster_crop.fold_column(width, profile))
        box = jav_poster_crop.portrait_crop_box(width, height, profile)
        self.assertEqual(box["method"], RATIO)
        self.assertGreaterEqual(box["x0"], width // 2)

    def test_a_missing_gradient_falls_back_to_the_right_half(self):
        """OpenCV 不在时取景仍然给得出框，只是退化成先验几何。"""
        box = jav_poster_crop.portrait_crop_box(800, 540, None)
        self.assertEqual(box["method"], RATIO)

    def test_a_portrait_or_square_image_is_not_cropped(self):
        for width, height in ((600, 900), (800, 800), (900, 800)):
            with self.subTest(size=(width, height)):
                box = jav_poster_crop.portrait_crop_box(width, height)
                self.assertEqual(box, {"x0": 0, "y0": 0, "x1": width, "y1": height,
                                       "method": NONE})

    def test_a_sixteen_by_nine_still_is_not_cropped(self):
        """整幅都是画面的官方剧照没有「正面那一块」，右半居中会裁出半张背景。"""
        box = jav_poster_crop.portrait_crop_box(1920, 1080)
        self.assertEqual(box["method"], NONE)

    def test_the_band_peak_must_be_a_real_cliff(self):
        """带里总有一个最大值，它不够陡就只是噪声的最高点，按它切会切进画面。"""
        profile = [0.0] * 800
        profile[80] = 1.0
        profile[425] = 0.1
        self.assertIsNone(jav_poster_crop.fold_column(800, profile))
        profile[425] = 0.9
        self.assertEqual(jav_poster_crop.fold_column(800, profile), 425)

    def test_a_symmetric_pair_around_the_centre_is_accepted(self):
        """折痕压在中线上时两条边离中线一样远，这是另一条采信路径。"""
        profile = [0.0] * 800
        profile[396] = 1.0
        profile[404] = 1.0
        self.assertEqual(jav_poster_crop.fold_column(800, profile), 404)

    def test_a_peak_far_from_both_priors_is_rejected(self):
        profile = [0.0] * 800
        profile[330] = 1.0
        profile[510] = 1.0
        self.assertIsNone(jav_poster_crop.fold_column(800, profile))

    def test_the_spine_prior_scales_with_width(self):
        """先验偏移是全宽的 2.5%，在高清封套上是五十多像素而不是二十像素。"""
        for width in (800, 2184):
            with self.subTest(width=width):
                profile = [0.0] * width
                profile[round(width * 0.525)] = 1.0
                self.assertEqual(jav_poster_crop.fold_column(width, profile),
                                 round(width * 0.525))

    def test_a_profile_that_does_not_match_the_image_is_ignored(self):
        self.assertIsNone(jav_poster_crop.fold_column(800, [1.0] * 400))


class CodeShapeTests(unittest.TestCase):
    """哪些番号的封面是横版封套。判据全部走 `catalog_rules` 现有函数。"""

    def test_studio_and_amateur_codes_are_sleeves(self):
        for code in ("ABW-232", "abw-232", "278GYAN-017", "259LUXU-1475"):
            with self.subTest(code=code):
                self.assertTrue(jav_poster_crop.crops_to_portrait(code))

    def test_finished_landscape_artwork_is_not_cropped(self):
        for code in ("HEYZO-1380", "FC2-PPV-1812235", "FC2-1812235",
                     "040221-001", "092620-001"):
            with self.subTest(code=code):
                self.assertFalse(jav_poster_crop.crops_to_portrait(code))

    def test_non_jav_and_korean_codes_are_not_cropped(self):
        for code in ("", None, "20211103_JENNIFERMENDEZ", "HHD800",
                     "AR-101", "NOAH-101"):
            with self.subTest(code=code):
                self.assertFalse(jav_poster_crop.crops_to_portrait(code))

    def test_a_western_release_is_stopped_by_the_shape_of_its_artwork(self):
        """欧美片的编号和厂牌番号同形，番号这一关拦不住它，宽高比这一关拦得住。

        它们的封面是成品横版剧照，落在 16:9 一档，所以走的是 `none`。
        """
        self.assertTrue(jav_poster_crop.crops_to_portrait("BLACKED-2021"))
        self.assertEqual(
            jav_poster_crop.crop_record("BLACKED-2021", 1920, 1080)["box"]["method"],
            NONE)


class RecordTests(unittest.TestCase):
    """边车的内容、读写与失效判定。"""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.cover = self.root / "ABW-232.jpg"
        sleeve(800, 540, 420).save(self.cover)

    def test_a_shape_that_is_not_cropped_never_touches_the_gradient(self):
        """番号形态先判：不该裁的图连解码都不做。"""
        calls = []

        def source():
            calls.append(1)
            return [0.0] * 800

        record = jav_poster_crop.crop_record("HEYZO-1380", 800, 540, source)
        self.assertEqual(record["box"]["method"], NONE)
        self.assertEqual(calls, [])

    def test_the_record_carries_the_version_the_size_and_the_box(self):
        record = jav_poster_crop.crop_record("ABW-232", 800, 540, [0.0] * 800)
        self.assertEqual(record["version"], jav_poster_crop.ALGORITHM_VERSION)
        self.assertEqual(record["px"], [800, 540])
        self.assertEqual(record["box"]["method"], RATIO)

    def test_the_sidecar_sits_beside_the_cover_and_round_trips(self):
        record = jav_poster_crop.crop_record("ABW-232", 800, 540, [0.0] * 800)
        path = jav_poster_crop.write_sidecar(self.cover, record)
        self.assertEqual(path.name, "ABW-232.poster.json")
        self.assertEqual(jav_poster_crop.read_sidecar(self.cover), record)
        self.assertTrue(jav_poster_crop.is_current(record, 800, 540))

    def test_an_outdated_version_or_a_replaced_cover_forces_a_recount(self):
        record = jav_poster_crop.crop_record("ABW-232", 800, 540, [0.0] * 800)
        self.assertFalse(jav_poster_crop.is_current(record, 2184, 1464),
                         "封面被更大的那张换掉之后，旧框落在新图上是一块错位的区域")
        stale = dict(record, version="poster-crop-v0")
        self.assertFalse(jav_poster_crop.is_current(stale, 800, 540))
        self.assertFalse(jav_poster_crop.is_current(None, 800, 540))

    def test_a_broken_sidecar_reads_as_missing(self):
        jav_poster_crop.sidecar_path(self.cover).write_text("{not json",
                                                            encoding="utf-8")
        self.assertIsNone(jav_poster_crop.read_sidecar(self.cover))


class ProjectionTests(unittest.TestCase):
    """API 字段的投影：只有真的算出框的那一档才给值。"""

    def test_a_real_box_projects_with_the_source_size(self):
        record = jav_poster_crop.crop_record("ABW-232", 800, 540, [0.0] * 800)
        projected = jav_poster_crop.projection(record)
        self.assertEqual(projected["px"], [800, 540])
        self.assertEqual(projected["method"], RATIO)
        self.assertEqual((projected["x1"] - projected["x0"]) * 3,
                         (projected["y1"] - projected["y0"]) * 2)

    def test_everything_unusable_projects_to_none(self):
        for record in (None, {}, {"version": "poster-crop-v0"},
                       jav_poster_crop.crop_record("HEYZO-1380", 800, 540),
                       {"version": jav_poster_crop.ALGORITHM_VERSION,
                        "px": [800, 540], "box": {"x0": 0, "x1": 0, "y0": 0,
                                                  "y1": 0, "method": RATIO}},
                       {"version": jav_poster_crop.ALGORITHM_VERSION,
                        "px": [800, 540], "box": {"x0": 0, "x1": 900, "y0": 0,
                                                  "y1": 540, "method": RATIO}}):
            with self.subTest(record=record):
                self.assertIsNone(jav_poster_crop.projection(record))


class BatchScriptTests(unittest.TestCase):
    """批处理只写边车、只处理该处理的那些图。"""

    def setUp(self):
        self.script = batch_script()
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.cover = self.root / "ABW-232.jpg"
        sleeve(800, 540, 420).save(self.cover)
        self.before = self.cover.read_bytes()

    def run_script(self, *argv):
        return self.script.main([*argv, "--covers", str(self.root)])

    def test_a_dry_run_writes_nothing(self):
        self.assertEqual(self.run_script(), 0)
        self.assertFalse(jav_poster_crop.sidecar_path(self.cover).exists())

    def test_apply_writes_the_sidecar_and_leaves_the_image_untouched(self):
        self.assertEqual(self.run_script("--apply"), 0)
        record = json.loads(
            jav_poster_crop.sidecar_path(self.cover).read_text(encoding="utf-8"))
        self.assertEqual(record["px"], [800, 540])
        self.assertIn(record["box"]["method"], (FOLD, RATIO))
        self.assertEqual(self.cover.read_bytes(), self.before,
                         "取景是边车元数据，原图一个字节都不动")

    def test_a_current_sidecar_is_skipped_and_a_stale_one_is_redone(self):
        self.run_script("--apply")
        self.assertEqual(self.script.pending([self.cover], False), [])
        stale = jav_poster_crop.read_sidecar(self.cover)
        jav_poster_crop.write_sidecar(self.cover, dict(stale, version="poster-crop-v0"))
        self.assertEqual(self.script.pending([self.cover], False),
                         [(self.cover, (800, 540))])

    def test_an_unreadable_cover_is_counted_and_never_given_a_box(self):
        broken = self.root / "BAD-001.jpg"
        broken.write_bytes(b"not an image")
        self.assertEqual(self.run_script("--apply"), 0)
        self.assertFalse(jav_poster_crop.sidecar_path(broken).exists())


class ImageSizeTests(unittest.TestCase):
    def test_the_size_probe_reports_none_for_junk(self):
        root = Path(tempfile.mkdtemp()).resolve()
        broken = root / "x.jpg"
        broken.write_bytes(b"nope")
        self.assertIsNone(batch_script().image_size(broken))
        good = root / "y.jpg"
        buffer = io.BytesIO()
        Image.new("RGB", (40, 30)).save(buffer, "JPEG")
        good.write_bytes(buffer.getvalue())
        self.assertEqual(batch_script().image_size(good), (40, 30))


if __name__ == "__main__":
    unittest.main()
