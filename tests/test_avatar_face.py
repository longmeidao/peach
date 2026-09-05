# -*- coding: utf-8 -*-
"""实体图人脸记录：sidecar 形状、像素换算与探针的降级行为。"""
import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from peach.avatar_face import (
    FaceProbe, drop_sidecar, face_px_width, read_sidecar, sidecar_path,
    write_sidecar,
)


def record(width=640, height=960, face_w=0.105):
    return {"ratio": round(width / height, 3), "px": [width, height],
            "face": {"cx": 0.439, "cy": 0.224, "w": face_w, "h": 0.095,
                     "score": 0.934}}


class SidecarTests(unittest.TestCase):
    def test_the_sidecar_sits_beside_the_image_under_a_swapped_suffix(self):
        self.assertEqual(sidecar_path(Path("/x/performer-8711.img")).name,
                         "performer-8711.face.json")

    def test_a_written_sidecar_reads_back_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp).resolve() / "performer-1.img"
            payload = record()
            written = write_sidecar(image, payload)
            self.assertEqual(json.loads(written.read_text(encoding="utf-8")), payload)
            self.assertEqual(read_sidecar(image), payload)

    def test_a_missing_or_broken_sidecar_reads_as_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp).resolve() / "performer-1.img"
            self.assertIsNone(read_sidecar(image))
            sidecar_path(image).write_text("{ not json", encoding="utf-8")
            self.assertIsNone(read_sidecar(image))

    def test_dropping_is_safe_to_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp).resolve() / "performer-1.img"
            write_sidecar(image, record())
            drop_sidecar(image)
            drop_sidecar(image)
            self.assertFalse(sidecar_path(image).exists())


class FacePixelWidthTests(unittest.TestCase):
    def test_the_normalized_box_becomes_pixels_against_the_source_width(self):
        """归一化值给得出比例，给不出像素——放大到几倍还清楚问的是像素。"""
        self.assertEqual(face_px_width(record(640, 960, 0.105)), 67)

    def test_everything_unmeasurable_is_zero(self):
        for payload in (None, {}, {"px": [640, 960], "face": None},
                        {"face": {"w": 0.1}}, {"px": [], "face": {"w": 0.1}},
                        {"px": [640, 960], "face": {"w": "大"}}):
            with self.subTest(payload=payload):
                self.assertEqual(face_px_width(payload), 0)


class FaceProbeTests(unittest.TestCase):
    def test_the_model_is_built_once_and_only_when_something_needs_it(self):
        """一趟里一个候选都没走到就不必去下 232 KB 的 ONNX。"""
        probe = FaceProbe()
        with unittest.mock.patch("peach.avatar_face.FaceDetector") as detector:
            self.assertEqual(detector.call_count, 0)
            with unittest.mock.patch("peach.avatar_face.face_record",
                                     return_value=record()):
                probe(Path("/tmp/a.img"))
                probe(Path("/tmp/b.img"))
            self.assertEqual(detector.call_count, 1)

    def test_an_unavailable_model_is_reported_instead_of_stopping_the_run(self):
        """取不到模型会把「今天没网」变成「所有人都没有头像」，所以只记原因。"""
        probe = FaceProbe()
        with unittest.mock.patch("peach.avatar_face.FaceDetector",
                                 side_effect=RuntimeError("模型未取得")):
            self.assertIsNone(probe(Path("/tmp/a.img")))
        self.assertEqual(probe.unavailable, "模型未取得")

    def test_one_undecodable_image_does_not_take_down_the_batch(self):
        probe = FaceProbe()
        with unittest.mock.patch("peach.avatar_face.FaceDetector"):
            with unittest.mock.patch("peach.avatar_face.face_record",
                                     side_effect=ValueError("解不开")):
                self.assertIsNone(probe(Path("/tmp/a.img")))
        self.assertEqual(probe.unavailable, "")


if __name__ == "__main__":
    unittest.main()
