"""`scripts/demo_dataset.py`：SFW 合成演示库要能被 scan 与 process 离线消费。

README 承诺「文档中的演示素材仅限 SFW」，这里把承诺变成门槛：演示词表不得与
`catalog_rules` 的成人词表相交；生成的目录布局要和 `library_nfo` 的边车规则对得上；
`process_library` 跑完不能向任何外部来源发过请求。
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock

from peach import catalog_rules
from peach.ffmpeg import FFmpegResolver
from peach.field_owners import review_owner
from peach.library_nfo import local_art, read_nfo, sidecars
from peach.library_processing import process_library
from peach.review_csv import read_rows
from peach.settings_file import PeachConfig
from peach.web_review import _apply_metadata_candidate
from support.ledger import fresh_ledger

ROOT = Path(__file__).resolve().parents[1]


def load_script():
    path = ROOT / "scripts" / "demo_dataset.py"
    spec = importlib.util.spec_from_file_location("peach_script_demo_dataset", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DemoDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo = load_script()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def _generate(self, name: str, count: int = 9, **kwargs) -> tuple[Path, list]:
        output = self.root / name
        items = self.demo.generate(output, count=count, seed=kwargs.pop("seed", 7),
                                   video=kwargs.pop("video", "stub"),
                                   duration=kwargs.pop("duration", 8), **kwargs)
        return output, items

    def test_vocabulary_is_disjoint_from_the_adult_tag_sets(self):
        adult = set().union(
            catalog_rules.ROLE_TAGS, catalog_rules.APPEARANCE_TAGS, catalog_rules.POSITION_TAGS,
            catalog_rules.STORY_TAGS, catalog_rules.RELATIONSHIP_TAGS, catalog_rules.SCENE_TAGS,
            catalog_rules.ATTRIBUTE_TAGS)
        vocabulary = set(self.demo.CONTENT_TAGS) | set(self.demo.SERIES) | set(self.demo.PERFORMERS)
        vocabulary |= set(self.demo.CREATORS) | {name for _, name in self.demo.STUDIOS}
        vocabulary |= {title for title, _ in self.demo.TITLES} | set(self.demo.PLOTS)
        self.assertEqual(vocabulary & adult, set())
        for prefix, _ in self.demo.STUDIOS:
            self.assertNotIn(prefix, catalog_rules.KOREAN_MIB_PREFIXES)
            self.assertEqual(catalog_rules.release_code_from_filename(f"{prefix}-001.mp4"), f"{prefix}-001")

    def test_stub_generation_is_deterministic_and_lays_out_the_three_shapes(self):
        first, items = self._generate("one")
        second, _ = self._generate("two")
        manifest_one = json.loads((first / self.demo.MANIFEST_NAME).read_text(encoding="utf-8"))
        manifest_two = json.loads((second / self.demo.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest_one["items"], manifest_two["items"])
        kinds = {item.kind for item in items}
        self.assertEqual(kinds, {"coded", "creator", "bare"})
        for item in items:
            self.assertTrue((first / item.path).is_file(), item.path)
            if item.kind == "coded":
                self.assertTrue((first / item.nfo).is_file())
                self.assertTrue((first / item.poster).is_file())
                self.assertEqual(Path(item.poster).name, f"{item.code}-poster.jpg")
            elif item.kind == "creator":
                self.assertTrue((first / item.nfo).is_file())
                self.assertEqual(Path(item.poster).suffix, ".png")
                self.assertEqual(Path(item.path).parent.name, item.creator)
            else:
                self.assertEqual((item.nfo, item.poster), ("", ""))
        galleries = [item for item in items if item.gallery]
        self.assertTrue(galleries)
        for photo in galleries[0].gallery:
            self.assertTrue((first / photo).is_file(), photo)
        self.assertEqual(Path(galleries[0].gallery[0]).parent.name, "P")

    def test_nfo_and_poster_follow_the_sidecar_rules(self):
        output, items = self._generate("nfo")
        coded = next(item for item in items if item.kind == "coded")
        video = output / coded.path
        nfo, posters = sidecars(video)
        self.assertEqual(nfo, output / coded.nfo)
        self.assertEqual(posters[0], output / coded.poster)
        payload, _ = read_nfo(nfo)
        self.assertEqual(payload["id"], coded.code)
        self.assertEqual(payload["title"], coded.title)
        self.assertEqual(payload["maker"], coded.studio)
        self.assertEqual(payload["series"], coded.series)
        self.assertEqual(payload["release_date"], coded.release_date)
        self.assertEqual([actor["japanese_name"] for actor in payload["actresses"]], coded.performers)
        self.assertEqual(payload["local_tags"], coded.tags)
        self.assertEqual(local_art(video, payload), output / coded.poster)
        made = next(item for item in items if item.kind == "creator")
        payload, _ = read_nfo(output / made.nfo)
        self.assertEqual(payload["id"], "")
        self.assertEqual(payload["title"], made.title)

    def test_scan_and_process_consume_the_tree_without_any_network_call(self):
        media, items = self._generate("media")
        db = fresh_ledger(self.root)
        config = PeachConfig(self.root, self.root / "config.toml", present=True,
                             locations={"local": (str(media),)})
        factory = Mock()
        result = process_library(config, db, self.root / "generated", self.root / "covers",
                                 provider_factory=factory)
        factory.assert_not_called()
        coded = [item for item in items if item.kind == "coded"]
        bare = [item for item in items if item.kind == "bare"]
        self.assertEqual(result["identified"], len(coded))
        # 裸文件那条「未识别到番号」是演示要展示的问题项，不是失败。
        self.assertEqual(result["issue_count"], len(bare))
        for item in coded:
            self.assertTrue((self.root / "covers" / f"{item.code}.jpg").is_file(), item.code)
        with closing(sqlite3.connect(db)) as connection:
            connection.row_factory = sqlite3.Row
            videos = connection.execute("SELECT count(*) FROM asset WHERE medium='video'").fetchone()[0]
            images = connection.execute("SELECT count(*) FROM asset WHERE medium='image'").fetchone()[0]
            made_ids = [row["id"] for row in connection.execute(
                "SELECT id FROM asset WHERE medium='video' AND (code IS NULL OR code='') "
                "AND name LIKE '%.mp4' AND path NOT LIKE '%未整理%'")]
        self.assertEqual(videos, len(items))
        self.assertEqual(images, sum(len(item.gallery) for item in items) + sum(1 for item in items if item.poster))
        for asset_id in made_ids:
            self.assertTrue((self.root / "generated" / "posters" / f"{asset_id}_4.jpg").is_file())
        rows = read_rows(self.root / "generated" / "library-metadata-field-candidates.csv")
        fields = {(row["code"], row["field"]) for row in rows}
        for item in coded:
            for field in ("title", "original_title", "performers", "studio", "series", "release_date", "tags"):
                self.assertIn((item.code, field), fields, (item.code, field))
        studio_row = next(row for row in rows if row["code"] == coded[0].code and row["field"] == "studio")
        candidate = json.loads(studio_row["candidates_json"])[0]
        self.assertEqual(candidate["source"], "local_nfo")
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.row_factory = sqlite3.Row
            self.assertEqual(_apply_metadata_candidate(
                connection, studio_row, candidate, "2026-09-11", review_owner("local_nfo")), 1)
            self.assertEqual(connection.execute(
                "SELECT canonical_name FROM entity WHERE kind='studio'").fetchone()[0], coded[0].studio)

    def test_ffmpeg_mode_encodes_a_playable_clip(self):
        choice = FFmpegResolver(self.root).ffmpeg()
        probe = FFmpegResolver(self.root).ffprobe()
        if choice is None or probe is None:
            self.skipTest("ffmpeg is unavailable")
        try:
            output, items = self._generate("clip", count=1, video="ffmpeg", duration=2,
                                           ffmpeg=str(choice.path))
        except RuntimeError as error:
            self.skipTest(f"local ffmpeg cannot encode the fixture: {error}")
        result = subprocess.run(
            [str(probe.path), "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(output / items[0].path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(float(result.stdout.strip()), 2.0, delta=0.5)

    def test_generation_without_ffmpeg_is_refused_with_a_hint(self):
        with self.assertRaises(RuntimeError) as caught:
            self.demo.generate(self.root / "none", count=1, seed=1, video="ffmpeg", duration=2, ffmpeg=None)
        self.assertIn("--video stub", str(caught.exception))

    def test_next_steps_name_the_settings_lines_and_the_manifest(self):
        text = self.demo.next_steps(self.root / "demo")
        self.assertIn("[media.locations]", text)
        self.assertIn("peach init", text)
        self.assertIn("apply_metadata_tags.py", text)
        self.assertIn(self.demo.MANIFEST_NAME, text)


if __name__ == "__main__":
    unittest.main()
