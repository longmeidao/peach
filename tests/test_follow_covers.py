import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image

from peach.ffmpeg import BinaryChoice, FFmpegResolver
from peach.follow_covers import (
    FOLLOW_COVER_FILTER,
    FOLLOW_COVER_SCAN_SECONDS,
    FollowCoverService,
    FollowCoverUnavailable,
)
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

    def test_first_non_black_frame_is_generated_once_and_cached(self):
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
        filter_value = commands[0][commands[0].index("-vf") + 1]
        self.assertIn("blackframe=amount=0:threshold=32", filter_value)
        self.assertIn(
            "metadata=select:key=lavfi.blackframe.pblack:value=98:function=less",
            filter_value,
        )
        self.assertIn("scale='min(1280,iw)':-2", filter_value)
        self.assertEqual(
            commands[0][commands[0].index("-t") + 1],
            str(FOLLOW_COVER_SCAN_SECONDS),
        )

    def test_ffmpeg_filter_skips_a_black_intro(self):
        choice = FFmpegResolver(self.root).ffmpeg()
        if choice is None:
            self.skipTest("ffmpeg is unavailable")
        source = self.root / "black-intro.mp4"
        still = self.root / "selected.jpg"
        generated = subprocess.run(
            [
                str(choice.path), "-y", "-v", "error",
                "-f", "lavfi", "-i", "color=c=black:s=320x180:d=1:r=5",
                "-f", "lavfi", "-i", "color=c=red:s=320x180:d=1:r=5",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
                "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(source),
            ],
            capture_output=True,
            check=False,
            timeout=20,
        )
        if generated.returncode != 0:
            self.skipTest("test ffmpeg cannot create an H.264 fixture")
        selected = subprocess.run(
            [
                str(choice.path), "-y", "-v", "error", "-i", str(source),
                "-frames:v", "1", "-vf", FOLLOW_COVER_FILTER,
                "-q:v", "4", str(still),
            ],
            capture_output=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(selected.returncode, 0, selected.stderr.decode(errors="replace"))
        with Image.open(still).convert("RGB") as image:
            red, green, blue = image.resize((1, 1)).getpixel((0, 0))
        self.assertGreater(red, 150)
        self.assertLess(green, 80)
        self.assertLess(blue, 80)

    def test_only_paheal_videos_enter_the_generator(self):
        for provider, kind in (("rule34xxx", "video"),
                               ("rule34paheal", "image")):
            with self.subTest(provider=provider, kind=kind):
                with self.assertRaises(FollowCoverUnavailable):
                    self.service.cover(self._item(provider, kind))

    def test_the_lock_table_stays_bounded_and_keeps_the_locks_in_use(self):
        """一条一把锁、URL 一变再加一条：只增不减的话，进程活多久它就长多久。"""
        self.service.MAX_TRACKED_LOCKS = 3
        held = self.service._lock_for("held")
        held.acquire()
        self.addCleanup(held.release)
        for index in range(20):
            self.service._lock_for(f"item-{index}")
        self.assertLessEqual(len(self.service._locks),
                             self.service.MAX_TRACKED_LOCKS)
        self.assertIs(self.service._locks.get("held"), held,
                      "还被持有的锁不能被清掉，否则两个线程会各拿一把锁写同一个文件")
