import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.ffmpeg import BinaryChoice
from peach.transcodes import TranscodeService, TranscodeUnavailable


class _Resolver:
    def __init__(self, binary: Path | None):
        self.binary = binary

    def ffmpeg(self):
        return BinaryChoice(self.binary, "test") if self.binary else None


class TranscodeServiceTests(unittest.TestCase):
    def test_native_mp4_is_returned_without_ffmpeg(self):
        source = Path("movie.mp4")
        service = TranscodeService(_Resolver(None), Path("cache"))
        self.assertEqual(service.browser_path(1, source), (source, False))

    def test_unsupported_container_requires_ffmpeg(self):
        service = TranscodeService(_Resolver(None), Path("cache"))
        with self.assertRaises(TranscodeUnavailable):
            service.browser_path(1, Path("movie.avi"))

    def test_avi_is_transcoded_once_and_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "movie.avi"
            source.write_bytes(b"avi")
            service = TranscodeService(_Resolver(root / "ffmpeg.exe"), root / "cache")

            def run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"mp4")
                return subprocess.CompletedProcess(command, 0, b"", b"")

            with patch("peach.transcodes.subprocess.run", side_effect=run) as execute:
                first, transcoded = service.browser_path(9, source)
                second, cached = service.browser_path(9, source)

            self.assertTrue(transcoded and cached)
            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), b"mp4")
            self.assertEqual(execute.call_count, 1)
            self.assertIn("libx264", execute.call_args.args[0])
