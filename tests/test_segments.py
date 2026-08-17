"""HLS 分片：关键帧对齐、时间戳连续、播放列表报真实时长。"""
import struct
import tempfile
import unittest
from pathlib import Path

from peach.mp4index import keyframe_seconds, segment_plan
from peach.segments import build_hls_playlist


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
