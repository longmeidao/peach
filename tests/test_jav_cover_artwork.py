import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from peach import cover_artwork, jav_poster_crop
from peach.face_detect import Face, FaceModelUnavailable


def jpeg(colour, size=(840, 472)):
    output = io.BytesIO()
    Image.new("RGB", size, colour).save(output, "JPEG")
    return output.getvalue()


class Detector:
    def detect(self, image):
        return [Face(.72, .22, .1, .1, .9)]


class CoverArtworkTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.target = self.root / "259LUXU-1537.jpg"

    def test_install_replaces_image_and_both_focus_sidecars(self):
        data = jpeg((190, 120, 80))
        cover_artwork.install_cover(
            self.target, "259LUXU-1537", data, (840, 472), detector=Detector())
        self.assertEqual(self.target.read_bytes(), data)
        face = json.loads(self.target.with_suffix(".face.json").read_text(encoding="utf-8"))
        poster = jav_poster_crop.read_sidecar(self.target)
        self.assertEqual(face["face"]["cx"], .72)
        self.assertTrue(jav_poster_crop.is_current(poster, 840, 472))

    def test_missing_face_model_removes_stale_focus_but_keeps_new_cover(self):
        self.target.write_bytes(jpeg((10, 10, 10), (800, 539)))
        self.target.with_suffix(".face.json").write_text('{"ratio":1,"face":{}}')
        self.target.with_suffix(".poster.json").write_text('{"version":"old"}')
        data = jpeg((240, 240, 240))
        with patch.object(cover_artwork, "_default_detector",
                          side_effect=FaceModelUnavailable("missing")):
            cover_artwork.install_cover(self.target, "259LUXU-1537", data, (840, 472))
        self.assertEqual(self.target.read_bytes(), data)
        self.assertFalse(self.target.with_suffix(".face.json").exists())
        self.assertTrue(jav_poster_crop.is_current(
            jav_poster_crop.read_sidecar(self.target), 840, 472))

    def test_preparation_failure_leaves_the_installed_set_untouched(self):
        old = jpeg((10, 10, 10), (800, 539))
        self.target.write_bytes(old)
        face = self.target.with_suffix(".face.json")
        face.write_text('{"old":true}', encoding="utf-8")
        with patch.object(cover_artwork, "_sidecars", side_effect=RuntimeError("failed")), \
                self.assertRaisesRegex(RuntimeError, "failed"):
            cover_artwork.install_cover(
                self.target, "259LUXU-1537", jpeg((20, 20, 20)), (840, 472))
        self.assertEqual(self.target.read_bytes(), old)
        self.assertEqual(face.read_text(encoding="utf-8"), '{"old":true}')

    def test_commit_failure_restores_the_installed_set(self):
        old = jpeg((10, 10, 10), (800, 539))
        self.target.write_bytes(old)
        face = self.target.with_suffix(".face.json")
        poster = self.target.with_suffix(".poster.json")
        face.write_text('{"old":"face"}', encoding="utf-8")
        poster.write_text('{"old":"poster"}', encoding="utf-8")
        replace = os.replace

        def fail_new_face(source, destination):
            source, destination = Path(source), Path(destination)
            if destination == face and source.suffix == ".tmp":
                raise OSError("commit failed")
            replace(source, destination)

        with patch.object(cover_artwork.os, "replace", side_effect=fail_new_face), \
                self.assertRaisesRegex(OSError, "commit failed"):
            cover_artwork.install_cover(
                self.target, "259LUXU-1537", jpeg((20, 20, 20)), (840, 472),
                detector=Detector())
        self.assertEqual(self.target.read_bytes(), old)
        self.assertEqual(face.read_text(encoding="utf-8"), '{"old":"face"}')
        self.assertEqual(poster.read_text(encoding="utf-8"), '{"old":"poster"}')

    def test_concurrent_installs_never_mix_image_and_sidecars(self):
        payloads = [jpeg((220, 20, 20)), jpeg((20, 20, 220))]
        errors = []
        def install(index):
            try:
                evidence = {"raw_sha256": str(index)}
                cover_artwork.install_cover(
                    self.target, "259LUXU-1537", payloads[index], (840, 472),
                    evidence=evidence, detector=Detector())
            except Exception as error:  # pragma: no cover - 失败时由主线程报告
                errors.append(error)
        workers = [threading.Thread(target=install, args=(index,)) for index in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        self.assertEqual(errors, [])
        winner = payloads.index(self.target.read_bytes())
        evidence = json.loads(self.target.with_suffix(".scraping.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["raw_sha256"], str(winner))


if __name__ == "__main__":
    unittest.main()
