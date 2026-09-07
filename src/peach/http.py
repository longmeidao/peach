"""共享 HTTP transport：连接池、超时、有界读取与可注入测试边界。"""
from __future__ import annotations
from .user_agent import USER_AGENT

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
    #: 跟完重定向后的最终地址。两个 transport 都跟重定向，请求 URL 因此不等于实际
    #: 取到的页面；判断「这一页属于谁」必须看最终地址，而不是我们发出去的那个。
    #: 默认空字符串是为了让既有的三参数构造（多在测试里）保持可用。
    url: str = ""


class HttpTransport(Protocol):
    def __call__(
        self,
        request: HttpRequest,
        timeout: float,
        max_bytes: int,
    ) -> HttpResponse: ...


#: 跟这些状态的 Location。与 httpx 自己的判据一致。
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
#: 跨源跳转时丢掉的请求头：凭据只属于发出它的那个站。
_CREDENTIAL_HEADERS = ("cookie", "authorization")


def _same_origin(left: httpx.URL, right: httpx.URL) -> bool:
    return (left.scheme, left.host, left.port) == (right.scheme, right.host, right.port)


def _without(headers: dict[str, str], names: tuple[str, ...]) -> dict[str, str]:
    return {key: value for key, value in headers.items() if key.lower() not in names}


class HttpxTransport:
    """可跨请求复用的同步 HTTPX client；不会自动重试或持久化响应。

    重定向自己跟，不交给 httpx 的 `follow_redirects`：httpx 跟跳时会无条件丢掉显式的
    `Cookie` 头，只保留 client 自己 cookie jar 里的那些。连接器的登录会话正是作为请求头
    传进来的，于是「直接请求目标页 200、经一次同源 30x 到达就 403」（2026-09-08 实测
    simpcity.cr 的 `/latest` 与纯数字线程地址）。这里同源跳转保留全部请求头，跨源跳转
    丢掉 Cookie 与 Authorization——凭据只属于发出它的那个站。
    """

    #: 最多跟几跳。站点正常只跳一两次，再多就是环。
    MAX_REDIRECTS = 5

    def __init__(self, client: httpx.Client | None = None, *, owns_client: bool = False):
        self.client = client or httpx.Client(
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
            headers={"User-Agent": USER_AGENT},
        )
        self._owns_client = client is None or owns_client

    def __call__(
        self,
        request: HttpRequest,
        timeout: float,
        max_bytes: int,
    ) -> HttpResponse:
        method = request.method
        url = httpx.URL(request.url)
        headers = dict(request.headers)
        body = request.body
        for _ in range(self.MAX_REDIRECTS + 1):
            with self.client.stream(
                method, url, headers=headers, content=body, timeout=timeout,
                follow_redirects=False,
            ) as response:
                location = response.headers.get("location")
                if response.status_code not in _REDIRECT_STATUSES or not location:
                    return HttpResponse(
                        response.status_code,
                        dict(response.headers),
                        _bounded_body(response.iter_bytes(), max_bytes),
                        str(response.url),
                    )
                target = response.url.join(location)
            if not _same_origin(url, target):
                headers = _without(headers, _CREDENTIAL_HEADERS)
            # 303 一律改成 GET；301/302 只把非 GET 改成 GET，和浏览器与 httpx 的做法一致。
            if response.status_code == 303 or (
                    response.status_code in (301, 302) and method not in ("GET", "HEAD")):
                if method != "HEAD":
                    method = "GET"
                body = None
                headers = _without(headers, ("content-length", "content-type"))
            url = target
        raise httpx.TooManyRedirects(
            f"超过 {self.MAX_REDIRECTS} 次重定向", request=response.request)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


def _bounded_body(chunks, max_bytes: int) -> bytes:
    """最多读 `max_bytes + 1` 字节：多出的那一个字节让调用方能判「超限」而不是「刚好」。"""
    kept: list[bytes] = []
    total = 0
    for chunk in chunks:
        remaining = max_bytes + 1 - total
        if remaining <= 0:
            break
        kept.append(chunk[:remaining])
        total += min(len(chunk), remaining)
        if total > max_bytes:
            break
    return b"".join(kept)


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
