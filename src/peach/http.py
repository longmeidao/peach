"""共享 HTTP transport：连接池、超时、有界读取与可注入测试边界。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

import httpx


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes | None = None


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


class HttpTransport(Protocol):
    def __call__(
        self,
        request: HttpRequest,
        timeout: float,
        max_bytes: int,
    ) -> HttpResponse: ...


class HttpxTransport:
    """可跨请求复用的同步 HTTPX client；不会自动重试或持久化响应。"""

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(
            follow_redirects=True,
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
            headers={"User-Agent": "Peach/0.2"},
        )
        self._owns_client = client is None

    def __call__(
        self,
        request: HttpRequest,
        timeout: float,
        max_bytes: int,
    ) -> HttpResponse:
        chunks: list[bytes] = []
        total = 0
        with self.client.stream(
            request.method,
            request.url,
            headers=dict(request.headers),
            content=request.body,
            timeout=timeout,
        ) as response:
            for chunk in response.iter_bytes():
                remaining = max_bytes + 1 - total
                if remaining <= 0:
                    break
                chunks.append(chunk[:remaining])
                total += min(len(chunk), remaining)
                if total > max_bytes:
                    break
            return HttpResponse(
                response.status_code,
                dict(response.headers),
                b"".join(chunks),
            )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
