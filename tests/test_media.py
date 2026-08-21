import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.ffmpeg import FFmpegResolver
from peach.media import (
    FilesystemBackend, MediaEngine, StashAdapter, normalized_path, remap_managed_path,
    resolve_case_insensitive,
)
from peach.repository import MediaAsset
from peach.stash import StashClient


class MediaEngineTests(unittest.TestCase):
    def test_filesystem_backend_enforces_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inside = root / "media" / "one.mp4"
            outside = root.parent / "outside.mp4"
            inside.parent.mkdir()
            inside.write_bytes(b"test")
            backend = FilesystemBackend([root], root / "snapshots")
            result = backend.stream_candidates(MediaAsset(1, str(inside), None))
            self.assertEqual(result[0].backend, "filesystem")
            self.assertEqual(
                backend.stream_candidates(MediaAsset(2, str(outside), None)), ()
            )

    def test_stash_adapter_uses_public_stream_contract(self):
        client = StashClient()
        adapter = StashAdapter(client)
        payload = {"sceneStreams": [
            {"url": "http://127.0.0.1:9999/scene/42/stream", "mime_type": "video/mp4",
             "label": "Direct"},
            {"url": "http://127.0.0.1:9999/scene/42/hls", "mime_type": "application/x-mpegURL",
             "label": "HLS"},
        ]}
        with patch.object(client, "graphql", return_value=payload) as graphql:
            result = adapter.stream_candidates(
                MediaAsset(1, None, None, (("stash", "42"),))
            )
        self.assertEqual([x.label for x in result], ["Direct", "HLS"])
        self.assertEqual(graphql.call_args.args[1], {"id": "42"})

    def test_engine_composes_backends_without_hidden_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media = root / "one.mp4"
            media.write_bytes(b"test")
            filesystem = FilesystemBackend([root], root / "snapshots")
            client = StashClient()
            stash = StashAdapter(client)
            repository = unittest.mock.Mock()
            repository.media_asset.return_value = MediaAsset(
                1, str(media), None, (("stash", "42"),)
            )
            with patch.object(client, "graphql", return_value={"sceneStreams": []}):
                engine = MediaEngine(repository, filesystem, (stash,))
                result = engine.stream_candidates(1)
        self.assertEqual([x.backend for x in result], ["filesystem"])

    def test_engine_raises_for_unknown_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = unittest.mock.Mock()
            repository.media_asset.return_value = None
            engine = MediaEngine(
                repository,
                FilesystemBackend([root], root / "snapshots"),
            )
            with self.assertRaises(Exception) as raised:
                engine.file_for(404)
        self.assertEqual(type(raised.exception).__name__, "MediaNotFound")

    def test_ffmpeg_resolver_prefers_explicit_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "ffmpeg.exe"
            binary.write_bytes(b"test")
            resolver = FFmpegResolver(root)
            with patch.dict("os.environ", {"PEACH_FFMPEG": str(binary)}, clear=False):
                choice = resolver.ffmpeg()
        self.assertEqual(choice.source, "environment")

    def test_ffmpeg_resolver_uses_managed_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            binary.parent.mkdir()
            binary.write_bytes(b"test")
            with patch.dict("os.environ", {"PEACH_FFMPEG": ""}, clear=False), \
                    patch("peach.ffmpeg.shutil.which", return_value=None):
                choice = FFmpegResolver(root).ffmpeg()
        self.assertEqual(choice.source, "peach-managed")

    def test_offline_windows_root_does_not_block_startup(self):
        with patch.object(Path, "resolve", side_effect=OSError("offline")):
            path = normalized_path(Path("B:/"))
        self.assertTrue(path.is_absolute())

    def test_legacy_snapshot_path_is_rebased_by_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "generated" / "snapshots"
            legacy = root / "old" / "snapshots"
            raw = legacy / "cloud" / "local" / "aa" / "one.jpg"
            expected = current / "cloud" / "local" / "aa" / "one.jpg"
            self.assertEqual(
                remap_managed_path(raw, current, (legacy,)),
                normalized_path(expected),
            )

            unrelated = root / "untrusted" / "one.jpg"
            self.assertEqual(remap_managed_path(unrelated, current, (legacy,)), unrelated.resolve())

    def test_filesystem_backend_matches_case_insensitively_on_sensitive_mounts(self):
        """CloudDrive 大小写敏感：账本 `abw-118.mp4` 对磁盘 `ABW-118.mp4` 必须救回。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "ABW-118.MP4"
            real.write_bytes(b"test")
            backend = FilesystemBackend([root], root / "snapshots")
            result = backend.stream_candidates(MediaAsset(1, str(root / "abw-118.mp4"), None))
            opened = Path(result[0].uri)
            self.assertTrue(opened.is_file())
            self.assertEqual(opened.name.casefold(), "abw-118.mp4")
            # 完全缺失的名字仍应拒绝
            self.assertEqual(
                backend.stream_candidates(MediaAsset(2, str(root / "nope.mp4"), None)), ()
            )

    def test_batch_path_resolution_translates_ledger_drive_before_case_matching(self):
        """sheets/probe 不经过 FilesystemBackend，也必须先翻译账本盘符。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "ABW-118.MP4"
            real.write_bytes(b"test")
            with patch(
                "peach.media.translate_ledger_path",
                return_value=root / "abw-118.mp4",
            ):
                opened = Path(resolve_case_insensitive(r"A:\\ABW-118.mp4"))
            self.assertTrue(opened.is_file())
            self.assertTrue(opened.parent.samefile(root))

    def test_remote_mp4_defaults_to_range_and_only_segments_on_request(self):
        """默认 HLS 会让 HEVC 静默黑屏：`-c copy` 把 HEVC 装进 MPEG-TS，而 Chromium 的
        MSE 不支持 TS 里的 HEVC（实测 `video/mp2t; codecs="hvc1…"` 为 false），数据进得了
        缓冲却一帧都解不出，也没有 error 事件。同一浏览器直接 Range 播同一文件能出帧。
        见 ADR-0016。
        """
        repository = unittest.mock.Mock()
        repository.media_asset.return_value = MediaAsset(
            1, r"B:\video\one.mp4", None, (), "115", "one.mp4", 31.5, 100,
        )
        engine = MediaEngine(
            repository, FilesystemBackend([Path("B:/")], Path("snapshots")),
        )
        self.assertEqual(engine.stream_plan(1).protocol, "range")
        self.assertEqual(engine.stream_plan(1, mode="auto").protocol, "range")
        plan = engine.stream_plan(1, mode="hls")
        self.assertEqual(plan.protocol, "hls")
        self.assertEqual(plan.segment_seconds, 6)

    def test_hls_stays_unavailable_where_it_never_applied(self):
        """按需模式不是万能开关：本地来源和时长未知的片源仍然只能走 Range。"""
        repository = unittest.mock.Mock()
        repository.media_asset.return_value = MediaAsset(
            1, r"R:\video\one.mp4", None, (), "local", "one.mp4", 31.5, 100,
        )
        engine = MediaEngine(repository, FilesystemBackend([Path("R:/")], Path("snapshots")))
        self.assertEqual(engine.stream_plan(1, mode="hls").protocol, "range")

        repository.media_asset.return_value = MediaAsset(
            1, r"B:\video\one.mp4", None, (), "115", "one.mp4", None, 100,
        )
        engine = MediaEngine(repository, FilesystemBackend([Path("B:/")], Path("snapshots")))
        self.assertEqual(engine.stream_plan(1, mode="hls").protocol, "range")

    def test_local_or_unknown_duration_keeps_range_plan(self):
        repository = unittest.mock.Mock()
        repository.media_asset.return_value = MediaAsset(
            1, r"R:\video\one.mp4", None, (), "local", "one.mp4", None, 100,
        )
        engine = MediaEngine(
            repository, FilesystemBackend([Path("R:/")], Path("snapshots")),
        )
        self.assertEqual(engine.stream_plan(1).protocol, "range")


if __name__ == "__main__":
    unittest.main()
