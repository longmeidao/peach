"""共享 HTTP transport：连接池、超时、有界读取与可注入测试边界。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

import httpx
from curl_cffi import requests as curl_requests
from curl_cffi.requests.exceptions import CurlError


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
    #: 跟完重定向后的最终地址。两个 transport 都开着 follow_redirects，请求 URL
    #: 因此不等于实际取到的页面；判断「这一页属于谁」必须看最终地址，而不是我们
    #: 发出去的那个。默认空字符串是为了让既有的三参数构造（多在测试里）保持可用。
    url: str = ""


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
                str(response.url),
            )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


class CurlCffiTransport:
    """保持浏览器 TLS/HTTP2 指纹的有界同步 transport。

    只给明确需要浏览器传输特征的公开接口使用；它不求解验证码，也不重试。
    """

    def __init__(self, *, impersonate: str,
                 session: curl_requests.Session | None = None):
        self.session = session or curl_requests.Session(impersonate=impersonate)
        self._owns_session = session is None

    def __call__(
        self,
        request: HttpRequest,
        timeout: float,
        max_bytes: int,
    ) -> HttpResponse:
        chunks: list[bytes] = []
        total = 0
        try:
            with self.session.stream(
                request.method,
                request.url,
                headers=dict(request.headers),
                content=request.body,
                timeout=timeout,
                allow_redirects=True,
            ) as response:
                for chunk in response.iter_content():
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
                    # curl_cffi 的响应带 url，但注入的测试替身不一定；取不到就退回请求
                    # 地址，语义仍然成立（没跟到重定向即最终地址就是请求地址），
                    # 也不必逼每个替身为一个它不关心的字段长出属性。
                    str(getattr(response, "url", "") or request.url),
                )
        except CurlError as exc:
            raise OSError("browser transport request failed") from exc

    def close(self) -> None:
        if self._owns_session:
            self.session.close()
