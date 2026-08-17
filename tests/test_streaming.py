from __future__ import annotations

import asyncio
import unittest

from peach.streaming import CancellableFileResponse, StreamSessionRegistry
from peach.mp4index import segment_plan
from peach.segments import build_hls_playlist


class StreamSessionRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_stops_every_active_request_in_the_session(self):
        registry = StreamSessionRegistry()
        started = asyncio.Event()

        async def wait_for_cancel() -> None:
            task = asyncio.current_task()
            assert task is not None
            self.assertTrue(registry.register("detail-1", task))
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                registry.unregister("detail-1", task)

        task = asyncio.create_task(wait_for_cancel())
        await started.wait()
        self.assertEqual(registry.active_count("detail-1"), 1)
        self.assertEqual(registry.cancel("detail-1"), 1)
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(registry.active_count("detail-1"), 0)

    async def test_cancelled_session_rejects_late_range_requests(self):
        registry = StreamSessionRegistry()
        registry.cancel("detail-1")
        task = asyncio.current_task()
        assert task is not None
        self.assertFalse(registry.register("detail-1", task))

    async def test_open_ended_range_keeps_standard_http_semantics(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "remote.mp4"
            path.write_bytes(bytes(range(64)))
            registry = StreamSessionRegistry()
            response = CancellableFileResponse(
                path, session="detail-2", registry=registry,
            )
            messages: list[dict] = []

            async def receive() -> dict:
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message: dict) -> None:
                messages.append(message)

            scope = {
                "type": "http", "method": "GET", "path": "/stream",
                "headers": [(b"range", b"bytes=0-")],
            }
            await response(scope, receive, send)

        start = messages[0]
        headers = {key.decode(): value.decode() for key, value in start["headers"]}
        body = b"".join(message.get("body", b"") for message in messages[1:])
        self.assertEqual(start["status"], 206)
        self.assertEqual(headers["content-range"], "bytes 0-63/64")
        self.assertEqual(headers["content-length"], "64")
        self.assertEqual(body, bytes(range(64)))

    def test_hls_playlist_is_time_addressable_without_full_file_ranges(self):
        # 分片边界由真实关键帧决定，不再按固定秒数等分（见 tests/test_segments.py）。
        plan = segment_plan([0.0, 6.0, 12.0], 13.5, 6)
        self.assertEqual(plan, [(0.0, 6.0), (6.0, 6.0), (12.0, 1.5)])
        playlist = build_hls_playlist(plan, lambda index: f"/seg/{index}.ts")
        self.assertIn("#EXT-X-PLAYLIST-TYPE:VOD", playlist)
        self.assertIn("/seg/0.ts", playlist)
        self.assertIn("/seg/2.ts", playlist)
        self.assertEqual(playlist.count("#EXTINF:"), 3)
