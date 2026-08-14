import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.ffmpeg import FFmpegResolver
from peach.media import FilesystemBackend, MediaEngine, StashAdapter, normalized_path
from peach.stash import StashClient


class MediaEngineTests(unittest.TestCase):
    def test_filesystem_backend_enforces_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inside = root / "media" / "one.mp4"
            outside = root.parent / "outside.mp4"
            backend = FilesystemBackend([root])
            result = backend.stream_candidates({"path": str(inside)})
            self.assertEqual(result[0].backend, "filesystem")
            self.assertEqual(backend.stream_candidates({"path": str(outside)}), ())

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
            result = adapter.stream_candidates({"stash_scene_id": 42})
        self.assertEqual([x.label for x in result], ["Direct", "HLS"])
        self.assertEqual(graphql.call_args.args[1], {"id": "42"})

    def test_engine_composes_backends_without_hidden_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            filesystem = FilesystemBackend([Path(tmp)])
            client = StashClient()
            stash = StashAdapter(client)
            with patch.object(client, "graphql", return_value={"sceneStreams": []}):
                engine = MediaEngine([filesystem, stash])
                result = engine.stream_candidates({"path": str(Path(tmp) / "one.mp4"),
                                                   "stash_scene_id": 42})
        self.assertEqual([x.backend for x in result], ["filesystem"])

    def test_ffmpeg_resolver_prefers_explicit_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "ffmpeg.exe"
            binary.write_bytes(b"test")
            resolver = FFmpegResolver(root, allow_legacy_stash=False)
            with patch.dict("os.environ", {"PEACH_FFMPEG": str(binary)}, clear=False):
                choice = resolver.ffmpeg()
        self.assertEqual(choice.source, "environment")

    def test_offline_windows_root_does_not_block_startup(self):
        with patch.object(Path, "resolve", side_effect=OSError("offline")):
            path = normalized_path(Path("B:/"))
        self.assertTrue(path.is_absolute())


if __name__ == "__main__":
    unittest.main()
