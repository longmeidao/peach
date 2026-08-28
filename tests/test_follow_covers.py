import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from peach.ffmpeg import BinaryChoice
from peach.follow_covers import FollowCoverService, FollowCoverUnavailable
from peach.follow_stream import ResolvedFollowMedia


class _FFmpeg:
    def ffmpeg(self):
        return BinaryChoice(Path("ffmpeg"), "test")


class _Media:
    def __init__(self):
        self.calls = 0

    def resolve(self, item):
        self.calls += 1
        return ResolvedFollowMedia(
            "https://r34i.paheal-cdn.net/ab/cd/video", item.url)


class FollowCoverServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.media = _Media()
        self.service = FollowCoverService(_FFmpeg(), self.media, self.root)

    @staticmethod
    def _item(provider="rule34paheal", kind="video"):
        return SimpleNamespace(
            id=7, provider=provider, metadata={"media_kind": kind},
            url="https://rule34.paheal.net/post/view/7")

    def test_first_frame_is_generated_once_and_cached(self):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            Path(command[-1]).write_bytes(b"jpeg")
            return subprocess.CompletedProcess(command, 0, b"", b"")

        with mock.patch("peach.follow_covers.subprocess.run", side_effect=run):
            first = self.service.cover(self._item())
            second = self.service.cover(self._item())
        self.assertEqual(first, second)
        self.assertEqual(first.read_bytes(), b"jpeg")
        self.assertEqual(len(commands), 1)
        self.assertIn("-frames:v", commands[0])
        self.assertIn("scale='min(1280,iw)':-2", commands[0])

    def test_only_paheal_videos_enter_the_generator(self):
        for provider, kind in (("rule34xxx", "video"),
                               ("rule34paheal", "image")):
            with self.subTest(provider=provider, kind=kind):
                with self.assertRaises(FollowCoverUnavailable):
                    self.service.cover(self._item(provider, kind))
