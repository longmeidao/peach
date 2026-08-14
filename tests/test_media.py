import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.ffmpeg import FFmpegResolver
from peach.media import (
    FilesystemBackend, MediaEngine, StashAdapter, normalized_path, remap_managed_path,
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
            binary = root / "bin" / "ffmpeg.exe"
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
            self.assertEqual(remap_managed_path(raw, current, (legacy,)), expected)

            unrelated = root / "untrusted" / "one.jpg"
            self.assertEqual(remap_managed_path(unrelated, current, (legacy,)), unrelated.resolve())


if __name__ == "__main__":
    unittest.main()
