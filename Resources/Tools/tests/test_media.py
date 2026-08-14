import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peach.media import FilesystemBackend, MediaEngine, StashAdapter


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
        adapter = StashAdapter()
        payload = {"sceneStreams": [
            {"url": "http://127.0.0.1:9999/scene/42/stream", "mime_type": "video/mp4",
             "label": "Direct"},
            {"url": "http://127.0.0.1:9999/scene/42/hls", "mime_type": "application/x-mpegURL",
             "label": "HLS"},
        ]}
        with patch.object(adapter, "_graphql", return_value=payload) as graphql:
            result = adapter.stream_candidates({"stash_scene_id": 42})
        self.assertEqual([x.label for x in result], ["Direct", "HLS"])
        self.assertEqual(graphql.call_args.args[1], {"id": "42"})

    def test_engine_composes_backends_without_hidden_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            filesystem = FilesystemBackend([Path(tmp)])
            stash = StashAdapter()
            with patch.object(stash, "_graphql", return_value={"sceneStreams": []}):
                engine = MediaEngine([filesystem, stash])
                result = engine.stream_candidates({"path": str(Path(tmp) / "one.mp4"),
                                                   "stash_scene_id": 42})
        self.assertEqual([x.backend for x in result], ["filesystem"])


if __name__ == "__main__":
    unittest.main()
