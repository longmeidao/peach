import csv
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from peach.logo_provider import LogoCandidateCache, inspect_logo


ROOT = Path(__file__).resolve().parents[1]


def load_script():
    path = ROOT / "scripts" / "fetch_studio_avatar_candidates.py"
    spec = importlib.util.spec_from_file_location("fetch_studio_avatar_candidates_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def png_bytes(color=(20, 40, 60), size=(400, 400)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def pattern_png(kind="vertical", size=(400, 400)):
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    if kind == "vertical":
        draw.rectangle((0, 0, size[0] // 2, size[1]), fill="black")
    else:
        draw.rectangle((0, 0, size[0], size[1] // 2), fill="black")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


class Response:
    def __init__(self, body):
        self.body = body
        self.status = 200
        self.headers = {}


class FakeTransport:
    def __init__(self, images):
        self.images = list(images)
        self.calls = []

    def __call__(self, request, _timeout, _max_bytes):
        self.calls.append(request.url)
        if "unavatar.io" in request.url:
            return Response(json.dumps({"url": "https://pbs.example/logo.png"}).encode())
        return Response(self.images.pop(0))


class LogoProviderTests(unittest.TestCase):
    def test_content_cache_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = LogoCandidateCache(Path(tmp))
            body = png_bytes()
            raster = inspect_logo(body)
            path = cache.store("https://x/logo.png", body, raster)
            self.assertEqual(cache.lookup("https://x/logo.png"), body)
            path.write_bytes(b"tampered")
            self.assertIsNone(cache.lookup("https://x/logo.png"))


class StudioLogoScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.module = load_script()
        self.source = self.root / "missing.csv"
        self.handles = self.root / "handles.csv"
        self.out = self.root / "studio-logo-candidate-test.csv"
        self.health = self.root / "studio-logo-health-test.csv"
        self.images = self.root / "studio-logos"
        self.cache = self.root / "cache"
        self.installed = self.root / "installed"
        self.installed.mkdir()
        self.source.write_text("studio\nStudio A\n", encoding="utf-8-sig")
        self.handles.write_text("studio,handle\nStudio A,studio_a\n", encoding="utf-8-sig")

    def args(self, *extra):
        return [
            "--input", str(self.source), "--output", str(self.out),
            "--handles", str(self.handles), "--image-dir", str(self.images),
            "--cache-dir", str(self.cache), "--installed-dir", str(self.installed),
            "--health", str(self.health), "--interval", "0", *extra,
        ]

    def rows(self):
        with self.out.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_new_candidate_has_cache_provenance_hash_and_health(self):
        transport = FakeTransport([png_bytes()])
        self.assertEqual(self.module.main(self.args(), transport=transport), 0)
        row = self.rows()[0]
        self.assertEqual(row["content_state"], "new")
        self.assertEqual(row["accepted"], "True")
        self.assertEqual(len(row["sha256"]), 64)
        self.assertTrue((self.images / row["saved"]).is_file())
        self.assertTrue((self.cache / "evidence" / row["provenance_key"]).is_file())
        self.assertNotIn(str(self.root), row["saved"])
        with self.health.open(encoding="utf-8-sig", newline="") as handle:
            health = next(csv.DictReader(handle))
        self.assertEqual(health["new"], "1")
        self.assertEqual(health["errors"], "0")

    def test_same_installed_content_is_mechanical_unchanged(self):
        (self.installed / "Studio_A.img").write_bytes(pattern_png(size=(400, 400)))
        refreshed = pattern_png(size=(200, 200))
        self.assertEqual(self.module.main(self.args(), transport=FakeTransport([refreshed])), 0)
        row = self.rows()[0]
        self.assertEqual(row["content_state"], "unchanged")
        self.assertEqual(row["accepted"], "False")
        self.assertNotEqual(row["sha256"], "")
        self.assertLessEqual(int(row["visual_distance"]), 4)

    def test_refresh_surfaces_changed_upstream_content(self):
        (self.installed / "Studio_A.img").write_bytes(pattern_png("vertical"))
        fresh = pattern_png("horizontal")
        self.assertEqual(
            self.module.main(self.args("--refresh"), transport=FakeTransport([fresh])), 0,
        )
        row = self.rows()[0]
        self.assertEqual(row["content_state"], "changed")
        self.assertEqual(row["accepted"], "True")


if __name__ == "__main__":
    unittest.main()
