"""采集来源的本机设置、域内 Cookie 和按来源连接策略。"""
from __future__ import annotations

import http.cookiejar
import hashlib
from http.cookies import SimpleCookie, CookieError
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urljoin

import httpx

from .follow_secrets import CredentialStore
from .http import HttpRequest, HttpxTransport
from .scripting import USER_AGENT, host_under, hostname_of


SOURCES = {
    "r18dev": {"label": "R18.dev", "domains": ("r18.dev",), "login": "https://r18.dev/"},
    "dmm": {"label": "DMM / FANZA", "domains": ("dmm.co.jp", "dmm.com"), "login": "https://www.dmm.co.jp/"},
    "prestige": {"label": "Prestige", "domains": ("prestige-av.com",), "login": "https://www.prestige-av.com/"},
    "mgstage": {"label": "MGStage", "domains": ("mgstage.com",), "login": "https://www.mgstage.com/"},
    "fc2cmadb": {"label": "FC2 CMADB", "domains": ("fc2cmadb.com",), "login": "https://fc2cmadb.com/", "cookie": True},
    "instagram": {"label": "Instagram", "domains": ("instagram.com", "cdninstagram.com"), "login": "https://www.instagram.com/accounts/login/", "cookie": True},
}
_LOCK = threading.RLock()


class SourcePaused(RuntimeError):
    """来源冷却期内停止请求，保留已有图像。"""


def source_for(url: str) -> str | None:
    return next((name for name, spec in SOURCES.items()
                 if host_under(hostname_of(url), spec["domains"])), None)


def _store(root: Path) -> CredentialStore:
    return CredentialStore(root)


def values_for(root: Path, source: str) -> dict[str, str]:
    if source not in SOURCES:
        raise ValueError("未知采集来源")
    credential = _store(root).load("scraping-" + source)
    return dict(credential.values) if credential else {}


def cookie_jar(values: dict[str, str], source: str) -> http.cookiejar.CookieJar:
    """文本导入复用标准库；过期项、异域项和 CDN 会话项不参与请求。"""
    domain = urlsplit(SOURCES[source]["login"]).hostname or ""
    domain = domain.removeprefix("www.")
    jar = http.cookiejar.MozillaCookieJar()
    text = values.get("cookies_text", "")
    if text:
        path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as handle:
                path = handle.name
                handle.write(text)
            jar.load(path, ignore_discard=True, ignore_expires=False)
        except (OSError, http.cookiejar.LoadError) as exc:
            raise ValueError("Cookie 文件须为 Netscape 文本格式") from exc
        finally:
            if path:
                Path(path).unlink(missing_ok=True)
        for cookie in list(jar):
            if not host_under(cookie.domain.lstrip(".").lower(), (domain,)):
                jar.clear(cookie.domain, cookie.path, cookie.name)
    elif values.get("cookie"):
        text = values["cookie"]
        if "\r" in text or "\n" in text:
            raise ValueError("请粘贴一行 Cookie 请求头")
        parsed = SimpleCookie()
        try:
            parsed.load(text)
        except CookieError as exc:
            raise ValueError("Cookie 请求头格式无效") from exc
        for name, item in parsed.items():
            jar.set_cookie(http.cookiejar.Cookie(
                0, name, item.value, None, False, domain, True, False,
                "/", True, True, None, True, None, None, {}, False))
    return jar


def save(root: Path, source: str, body: dict) -> dict:
    with _LOCK:
        values = values_for(root, source)
        mode = body.get("network", values.get("network", "environment"))
        if mode not in {"direct", "environment", "proxy"}:
            raise ValueError("请选择来源连接方式")
        proxy = body.get("proxy") or values.get("proxy", "")
        if mode == "proxy":
            parsed = urlsplit(proxy)
            if parsed.scheme not in {"http", "https", "socks5", "socks5h"} or not parsed.hostname:
                raise ValueError("请填写有效的 HTTP 或 SOCKS 代理地址")
        values["network"] = mode
        values["proxy"] = proxy if mode == "proxy" else ""
        if body.get("revoke"):
            values.pop("cookie", None)
            values.pop("cookies_text", None)
        elif body.get("cookie") or body.get("cookies_text"):
            if not SOURCES[source].get("cookie"):
                raise ValueError("此来源不接受登录 Cookie")
            if body.get("cookie") and body.get("cookies_text"):
                raise ValueError("Cookie 粘贴与文件导入只选一种")
            supplied = {name: str(body.get(name) or "") for name in ("cookie", "cookies_text")}
            if sum(map(len, supplied.values())) > 256 * 1024:
                raise ValueError("Cookie 文本超过 256 KiB")
            if not list(cookie_jar(supplied, source)):
                raise ValueError("未找到该来源尚未过期的 Cookie")
            values.update(supplied)
        path = _store(root).path_for("scraping-" + source)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(values, handle, ensure_ascii=False)
            if os.name != "nt":
                temporary.chmod(0o600)
            temporary.replace(path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
    return describe(root, source)


def describe(root: Path, source: str) -> dict:
    values = values_for(root, source)
    return {"source": source, "label": SOURCES[source]["label"],
            "login": SOURCES[source]["login"], "accepts_cookie": bool(SOURCES[source].get("cookie")),
            "network": values.get("network", "environment"),
            "proxy_saved": bool(values.get("proxy")),
            "cookie_saved": bool(values.get("cookie") or values.get("cookies_text"))}


def client_for(root: Path, source: str, *, session: bool = False, **kwargs) -> httpx.Client:
    values = values_for(root, source)
    mode = values.get("network", "environment")
    options = {"trust_env": mode == "environment", "follow_redirects": True,
               "headers": {"User-Agent": USER_AGENT}}
    if mode == "proxy":
        options["proxy"] = values["proxy"]
    if session:
        options["cookies"] = cookie_jar(values, source)
    options.update(kwargs)
    return httpx.Client(**options)


class SourceTransport:
    """公开采集按来源复用连接池；登录会话由特定来源消费者显式建立。"""

    def __init__(self, secrets_root: Path, *, max_requests: int = 0,
                 max_bytes: int = 0, max_seconds: float = 0):
        self.root = secrets_root
        self.transports: dict[str | None, HttpxTransport] = {}
        self.max_requests, self.max_bytes = max_requests, max_bytes
        self.deadline = time.monotonic() + max_seconds if max_seconds else 0
        self.requests = self.bytes = 0

    def __call__(self, request: HttpRequest, timeout: float, max_bytes: int):
        for _ in range(6):
            response = self._request(request, timeout, max_bytes)
            if response.status not in {301, 302, 303, 307, 308} or not response.headers.get("location"):
                return response
            target = urljoin(request.url, response.headers["location"])
            if urlsplit(target).scheme != "https":
                raise ValueError("采集重定向必须使用 HTTPS")
            cross_origin = urlsplit(target).netloc != urlsplit(request.url).netloc
            headers = {k: v for k, v in request.headers.items()
                       if not cross_origin or k.lower() not in {"cookie", "authorization", "host"}}
            request = HttpRequest("GET" if response.status == 303 else request.method,
                                  target, headers, None if response.status == 303 else request.body)
        raise ValueError("采集重定向次数超过上限")

    def _request(self, request: HttpRequest, timeout: float, max_bytes: int):
        source = source_for(request.url)
        if self.max_requests and self.requests >= self.max_requests:
            raise SourcePaused("请求预算已用完；已有图片保留")
        if self.deadline:
            timeout = min(timeout, self.deadline - time.monotonic())
            if timeout <= 0:
                raise SourcePaused("采集时间预算已用完；已有图片保留")
        if self.max_bytes:
            remaining = self.max_bytes - self.bytes
            if remaining <= 0:
                raise SourcePaused("下载预算已用完；已有图片保留")
            max_bytes = min(max_bytes, remaining - 1)
        key = source or hashlib.sha256(hostname_of(request.url).encode()).hexdigest()
        cooldown = self.root / ("scraping-" + key + ".cooldown.json")
        try:
            until = float(json.loads(cooldown.read_text(encoding="utf-8"))["until"])
        except (OSError, ValueError, KeyError, TypeError):
            until = 0
        if until > time.time():
            raise SourcePaused("来源正在冷却，请稍后重试；已有图片保留")
        if source not in self.transports:
            client = (client_for(self.root, source, follow_redirects=False) if source else
                      httpx.Client(follow_redirects=False, headers={"User-Agent": USER_AGENT}))
            self.transports[source] = HttpxTransport(client, owns_client=True)
        self.requests += 1
        try:
            response = self.transports[source](request, timeout, max_bytes)
        except httpx.HTTPError as exc:
            raise httpx.TransportError("来源连接未取得，请检查该来源的网络设置") from None
        self.bytes += len(response.body)
        if response.status == 429:
            retry = response.headers.get("retry-after", "")
            try:
                until = time.time() + max(0, int(retry))
            except ValueError:
                try:
                    until = parsedate_to_datetime(retry).timestamp()
                except (ValueError, TypeError, OverflowError):
                    until = time.time() + 900
            with _LOCK:
                cooldown.parent.mkdir(parents=True, exist_ok=True)
                cooldown.write_text(json.dumps({"until": max(until, time.time() + 1)}), encoding="utf-8")
            raise SourcePaused("来源限流，已记录冷却时间；已有图片保留")
        return response

    def renew(self):
        self.close()

    def close(self):
        for transport in self.transports.values():
            transport.close()
        self.transports.clear()
