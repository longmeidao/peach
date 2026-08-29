"""HLS 分片：关键帧对齐、时间戳连续、播放列表报真实时长。"""
import asyncio
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from peach.mp4index import keyframe_seconds, segment_plan
from peach.segments import HlsSegmentService, StreamSessionRegistry, build_hls_playlist


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + kind + payload


def synthetic_mp4(timescale: int, sample_delta: int, samples: int, keyframe_every: int) -> bytes:
    """构造一个只含时间表的最小 MP4：足够 stss/stts 解析，不含真实媒体数据。"""
    mdhd = box(b"mdhd", struct.pack(">4sIIII HH", b"\0\0\0\0", 0, 0, timescale, samples * sample_delta, 0, 0))
    hdlr = box(b"hdlr", struct.pack(">4sI4s", b"\0\0\0\0", 0, b"vide") + b"\0" * 12)
    stts = box(b"stts", struct.pack(">IIII", 0, 1, samples, sample_delta))
    sync = [n for n in range(1, samples + 1) if (n - 1) % keyframe_every == 0]
    stss = box(b"stss", struct.pack(">II", 0, len(sync)) + b"".join(struct.pack(">I", n) for n in sync))
    stbl = box(b"stbl", stts + stss)
    minf = box(b"minf", stbl)
    mdia = box(b"mdia", mdhd + hdlr + minf)
    trak = box(b"trak", mdia)
    return box(b"ftyp", b"isom" + b"\0" * 8) + box(b"moov", trak) + box(b"mdat", b"\0" * 64)


class Mp4IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, payload: bytes, name="clip.mp4") -> Path:
        path = self.root / name
        path.write_bytes(payload)
        return path

    def test_keyframe_times_come_from_the_sync_sample_table(self):
        # 1000 刻度、每样本 40 刻度（25fps），每 25 个样本一个关键帧 = 每秒一个。
        path = self.write(synthetic_mp4(1000, 40, 250, 25))
        self.assertEqual(keyframe_seconds(path)[:5], [0.0, 1.0, 2.0, 3.0, 4.0])

    def test_moov_at_the_end_is_still_found(self):
        """非 faststart 的文件把 moov 放在结尾；顺序读到它可能要拉几个 GB。"""
        full = synthetic_mp4(1000, 40, 100, 25)
        moov_start = full.index(b"moov") - 4
        moov_size = int.from_bytes(full[moov_start:moov_start + 4], "big")
        moov = full[moov_start:moov_start + moov_size]
        rest = full[:moov_start] + full[moov_start + moov_size:]
        self.assertEqual(keyframe_seconds(self.write(rest + moov))[:3], [0.0, 1.0, 2.0])

    def test_unparsable_input_returns_none_so_callers_fall_back_to_range(self):
        self.assertIsNone(keyframe_seconds(self.write(b"not an mp4 at all")))
        self.assertIsNone(keyframe_seconds(self.root / "missing.mp4"))

    def test_plan_snaps_to_keyframes_and_covers_the_whole_duration(self):
        keyframes = [round(value * 8.33, 2) for value in range(12)]
        plan = segment_plan(keyframes, 100.0, 6)
        self.assertTrue(all(start in keyframes for start, _ in plan),
                        "每段起点都必须落在真实关键帧上，否则 -c copy 切不准")
        self.assertTrue(all(length >= 6 for _, length in plan[:-1]))
        self.assertAlmostEqual(plan[0][0], 0.0)
        self.assertAlmostEqual(plan[-1][0] + plan[-1][1], 100.0, places=6)

    def test_plan_starts_at_zero_even_when_the_first_keyframe_is_late(self):
        plan = segment_plan([3.0, 9.0, 15.0], 20.0, 6)
        self.assertAlmostEqual(plan[0][0], 0.0)
        self.assertAlmostEqual(plan[-1][0] + plan[-1][1], 20.0, places=6)

    def test_playlist_reports_real_segment_durations(self):
        """按 6 秒等分声明会和关键帧实际切点对不上，播放器进度条就错位。"""
        plan = [(0.0, 8.33), (8.33, 8.33), (16.66, 3.34)]
        playlist = build_hls_playlist(plan, lambda index: f"/s/{index}.ts")
        self.assertIn("#EXTINF:8.330,", playlist)
        self.assertIn("#EXTINF:3.340,", playlist)
        self.assertIn("#EXT-X-TARGETDURATION:8", playlist)
        self.assertNotIn("#EXTINF:6.000,", playlist)
        self.assertEqual(playlist.count("/s/"), 3)
        self.assertIn("#EXT-X-ENDLIST", playlist)


if __name__ == "__main__":
    unittest.main()


class SegmentCommandTests(unittest.TestCase):
    """片段的时间窗必须写成绝对终点，否则只有开头两段能产出。

    真实故障：`-copyts` 保留原始时间轴后，`-t` 被 FFmpeg 当成绝对结束时刻而非片段时长。
    每段的 `-t` 都约等于一个片段长，于是起点超过它的片段一律「已经过期」，FFmpeg 以
    退出码 0、空 stderr 写出 0 字节，服务端只报一句没有内容的 ffmpeg failed。
    实测 asset 6562：片段 0 与 1 返回 200，片段 2 和 300 全是 503，播到约 20 秒就断，
    也拖不动。缓存目录里三个资产都只留下 0.ts 和 1.ts，没有更靠后的片段。
    """

    def _command_for(self, index: int) -> list[str]:
        captured: list[list[str]] = []

        class _Process:
            returncode = 0

            async def communicate(self):
                return b"", b""

        async def fake_exec(*command, **_kwargs):
            captured.append(list(command))
            return _Process()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "clip.mp4"
            source.write_bytes(bytes(1024))
            service = HlsSegmentService(
                resolver=mock.Mock(ffmpeg=lambda: type("C", (), {"path": "ffmpeg"})),
                work_root=root / "cache",
            )
            # 计划固定为等长片段，免得测试依赖真实关键帧表。
            service._plans[service.fingerprint(source)] = [
                (round(n * 9.993, 3), 9.993) for n in range(400)
            ]

            async def drive():
                with mock.patch("asyncio.create_subprocess_exec", fake_exec):
                    # 产物由假进程负责写，否则会走到「0 字节」的失败分支。
                    original = service.cached_path

                    def cached_path(*args, **kwargs):
                        target = original(*args, **kwargs)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        return target

                    with mock.patch.object(service, "cached_path", cached_path):
                        try:
                            await service.generate(
                                source, round(index * 9.993, 3), 9.993,
                                asset_id=6562, index=index, session="s",
                                registry=StreamSessionRegistry(),
                            )
                        except Exception:
                            pass

            asyncio.run(drive())
        self.assertTrue(captured, "没有真的调用 FFmpeg")
        return captured[0]

    def test_silent_ffmpeg_failure_still_says_what_was_observed(self):
        """FFmpeg 可以退出码 0、stderr 全空却写出 0 字节，只报 ffmpeg failed 等于没报。"""
        from peach.segments import SegmentUnavailable

        class _Process:
            returncode = 0

            async def communicate(self):
                return b"", b""

        async def fake_exec(*_command, **_kwargs):
            return _Process()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "clip.mp4"
            source.write_bytes(bytes(1024))
            service = HlsSegmentService(
                resolver=mock.Mock(ffmpeg=lambda: type("C", (), {"path": "ffmpeg"})),
                work_root=root / "cache",
            )

            async def drive():
                with mock.patch("asyncio.create_subprocess_exec", fake_exec):
                    await service.generate(
                        source, 2997.995, 9.993, asset_id=6562, index=300,
                        session="s", registry=StreamSessionRegistry(),
                    )

            with self.assertRaises(SegmentUnavailable) as caught:
                asyncio.run(drive())

        message = str(caught.exception)
        self.assertIn("returncode=0", message)
        self.assertIn("2997.995", message)
        self.assertIn("3007.988", message)

    def test_every_segment_asks_for_an_absolute_end_not_a_length(self):
        for index in (0, 1, 2, 300):
            command = self._command_for(index)
            self.assertIn("-copyts", command)
            self.assertNotIn("-t", command, f"片段 {index} 仍在用相对时长")
            start = float(command[command.index("-ss") + 1])
            end = float(command[command.index("-to") + 1])
            self.assertAlmostEqual(end - start, 9.993, places=2)
            # 决定性判据：终点随片段前移，而不是所有片段都停在第一段的末尾。
            self.assertGreater(end, start)
            self.assertAlmostEqual(end, round(index * 9.993, 3) + 9.993, places=2)


class PlanCacheTests(unittest.TestCase):
    """计划缓存一满就 clear() 等于没有缓存；改成 LRU 后热条目要能活下来。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = HlsSegmentService(
            resolver=mock.Mock(ffmpeg=lambda: None), work_root=self.root / "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def _source(self, number: int) -> Path:
        path = self.root / f"clip{number}.mp4"
        path.write_bytes(b"x")
        return path

    def _plan(self, number: int) -> None:
        with mock.patch("peach.segments.keyframe_seconds", return_value=[0.0]):
            self.service.plan(self._source(number), 60.0)

    def _held_sources(self) -> set[str]:
        return {key[0] for key in self.service._plans}

    def test_cache_keeps_at_most_the_limit_and_evicts_the_oldest_access(self):
        from peach.segments import PLAN_CACHE_LIMIT

        for number in range(PLAN_CACHE_LIMIT):
            self._plan(number)
        self.assertEqual(len(self.service._plans), PLAN_CACHE_LIMIT)

        # 命中一次让 0 号变成最近访问，再插入新条目：被逐出的必须是 1 号。
        self._plan(0)
        self._plan(PLAN_CACHE_LIMIT)
        self.assertEqual(len(self.service._plans), PLAN_CACHE_LIMIT)
        self.assertIn(str(self._source(0)), self._held_sources())
        self.assertNotIn(str(self._source(1)), self._held_sources())
