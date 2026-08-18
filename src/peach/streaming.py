from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import MutableSet
from pathlib import Path
from time import monotonic
from typing import Any

from starlette.responses import FileResponse, Response
from starlette.types import Receive, Scope, Send


class StreamSessionRegistry:
    """Track addressable browser stream requests so the UI can cancel them."""

    def __init__(self, *, tombstone_seconds: float = 300.0) -> None:
        self._active: dict[str, MutableSet[asyncio.Task[object]]] = {}
        self._processes: dict[str, MutableSet[Any]] = {}
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

    def register_process(self, session: str, process: Any) -> bool:
        """把生成 HLS 片段的子进程纳入同一个可取消会话。"""
        with self._lock:
            self._prune(monotonic())
            if session in self._cancelled:
                return False
            self._processes.setdefault(session, set()).add(process)
            return True

    def unregister_process(self, session: str, process: Any) -> None:
        with self._lock:
            processes = self._processes.get(session)
            if not processes:
                return
            processes.discard(process)
            if not processes:
                self._processes.pop(session, None)

    def is_cancelled(self, session: str) -> bool:
        with self._lock:
            self._prune(monotonic())
            return session in self._cancelled

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
            processes = tuple(self._processes.pop(session, ()))
        for task in tasks:
            task.cancel()
        for process in processes:
            try:
                if process.returncode is None:
                    process.kill()
            except (OSError, ProcessLookupError):
                pass
        return len(tasks) + len(processes)

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
