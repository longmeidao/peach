import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.ffmpeg import BinaryChoice
from peach.transcodes import TranscodeCancelled, TranscodeService, TranscodeUnavailable


class _Resolver:
    def __init__(self, binary: Path | None):
        self.binary = binary

    def ffmpeg(self):
        return BinaryChoice(self.binary, "test") if self.binary else None


class _FakeTranscode:
    """让 Popen 立即产出缓存文件的最小替身。"""

    returncode = 0

    def __init__(self, command, **_kwargs):
        self.command = command

    def communicate(self, timeout=None):
        Path(self.command[-1]).write_bytes(b"mp4")
        return b"", b""


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

            class Process:
                returncode = 0

                def __init__(self, command, **_kwargs):
                    self.command = command

                def communicate(self, timeout=None):
                    Path(self.command[-1]).write_bytes(b"mp4")
                    return b"", b""

            with patch("peach.transcodes.subprocess.Popen", side_effect=Process) as execute:
                first, transcoded = service.browser_path(9, source)
                second, cached = service.browser_path(9, source)

            self.assertTrue(transcoded and cached)
            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), b"mp4")
            self.assertEqual(execute.call_count, 1)
            self.assertIn("libx264", execute.call_args.args[0])

    def test_lock_entries_do_not_accumulate_after_transcodes(self):
        """每把 per-asset 锁在没人持有、没人等待时必须从字典里消失。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "movie.avi"
            source.write_bytes(b"avi")
            service = TranscodeService(_Resolver(root / "ffmpeg.exe"), root / "cache")

            with patch("peach.transcodes.subprocess.Popen", side_effect=_FakeTranscode):
                service.browser_path(9, source)
            self.assertEqual(service._locks, {})

    def test_concurrent_transcodes_of_one_asset_stay_serialised(self):
        """清理之后同 asset 并发仍互斥：两个线程同时转码，FFmpeg 只真跑一次。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "movie.avi"
            source.write_bytes(b"avi")
            service = TranscodeService(_Resolver(root / "ffmpeg.exe"), root / "cache")
            start = threading.Barrier(2)
            outcomes: list[bool] = []

            def worker():
                start.wait()
                _, transcoded = service.browser_path(9, source)
                outcomes.append(transcoded)

            with patch("peach.transcodes.subprocess.Popen",
                       side_effect=_FakeTranscode) as execute:
                threads = [threading.Thread(target=worker) for _ in range(2)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
            self.assertEqual(sorted(outcomes), [True, True])
            self.assertEqual(execute.call_count, 1,
                             "第二个线程应命中缓存或等锁，不得重复转码")
            self.assertEqual(service._locks, {})

    def test_session_cancellation_kills_an_active_transcode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "movie.avi"
            source.write_bytes(b"avi")
            service = TranscodeService(_Resolver(root / "ffmpeg.exe"), root / "cache")

            class Process:
                returncode = None
                killed = False
                calls = 0

                def __init__(self, _command, **_kwargs):
                    pass

                def communicate(self, timeout=None):
                    self.calls += 1
                    if self.calls == 1:
                        raise subprocess.TimeoutExpired("ffmpeg", timeout)
                    return b"", b""

                def kill(self):
                    self.killed = True
                    self.returncode = -9

            process = Process([])

            class Registry:
                def register_process(self, session, registered):
                    self.registered = (session, registered)
                    return True

                def is_cancelled(self, _session):
                    return True

                def unregister_process(self, session, registered):
                    self.unregistered = (session, registered)

            registry = Registry()
            with patch("peach.transcodes.subprocess.Popen", return_value=process):
                with self.assertRaises(TranscodeCancelled):
                    service.browser_path(9, source, session="s1", registry=registry)
            self.assertTrue(process.killed)
            self.assertEqual(registry.registered, ("s1", process))
            self.assertEqual(registry.unregistered, ("s1", process))
