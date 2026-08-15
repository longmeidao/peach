from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import MutableSet
from pathlib import Path
from time import monotonic

from starlette.responses import FileResponse, Response
from starlette.types import Receive, Scope, Send


class StreamSessionRegistry:
    """Track addressable browser stream requests so the UI can cancel them."""

    def __init__(self, *, tombstone_seconds: float = 300.0) -> None:
        self._active: dict[str, MutableSet[asyncio.Task[object]]] = {}
        self._cancelled: dict[str, float] = {}
        self._tombstone_seconds = tombstone_seconds
        self._lock = threading.RLock()

    def _prune(self, now: float) -> None:
        expired = [
            session for session, cancelled_at in self._cancelled.items()
            if now - cancelled_at >= self._tombstone_seconds
        ]
        for session in expired:
            self._cancelled.pop(session, None)

    def register(self, session: str, task: asyncio.Task[object]) -> bool:
        with self._lock:
            self._prune(monotonic())
            if session in self._cancelled:
                return False
            self._active.setdefault(session, set()).add(task)
            return True

    def unregister(self, session: str, task: asyncio.Task[object]) -> None:
        with self._lock:
            tasks = self._active.get(session)
            if not tasks:
                return
            tasks.discard(task)
            if not tasks:
                self._active.pop(session, None)

    def cancel(self, session: str) -> int:
        with self._lock:
            self._prune(monotonic())
            self._cancelled[session] = monotonic()
            tasks = tuple(self._active.pop(session, ()))
        for task in tasks:
            task.cancel()
        return len(tasks)

    def active_count(self, session: str) -> int:
        with self._lock:
            return len(self._active.get(session, ()))


class CancellableFileResponse(FileResponse):
    """FileResponse whose active ASGI task can be cancelled by a session id."""

    def __init__(
        self,
        path: str | Path,
        *,
        session: str,
        registry: StreamSessionRegistry,
        media_type: str | None = None,
    ) -> None:
        super().__init__(path, media_type=media_type)
        self.session = session
        self.registry = registry

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        task = asyncio.current_task()
        if task is None or not self.registry.register(self.session, task):
            await Response(status_code=410, headers={"Cache-Control": "no-store"})(scope, receive, send)
            return
        try:
            await super().__call__(scope, receive, send)
        except asyncio.CancelledError:
            logging.getLogger(__name__).info("stream session cancelled: %s", self.session)
            raise
        finally:
            self.registry.unregister(self.session, task)


class CappedRangeFileResponse(CancellableFileResponse):
    """Bound each remote Range response so CloudDrive does not read to EOF."""

    def __init__(self, *args, max_range_bytes: int = 32 * 1024 * 1024, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if max_range_bytes <= 0:
            raise ValueError("max_range_bytes must be positive")
        self.max_range_bytes = max_range_bytes

    async def _handle_single_range(
        self,
        send: Send,
        start: int,
        end: int,
        file_size: int,
        send_header_only: bool,
    ) -> None:
        capped_end = min(end, start + self.max_range_bytes)
        await super()._handle_single_range(
            send, start, capped_end, file_size, send_header_only,
        )

    async def _handle_multiple_ranges(
        self,
        send: Send,
        ranges: list[tuple[int, int]],
        file_size: int,
        send_header_only: bool,
    ) -> None:
        capped = [
            (start, min(end, start + self.max_range_bytes))
            for start, end in ranges
        ]
        await super()._handle_multiple_ranges(
            send, capped, file_size, send_header_only,
        )
