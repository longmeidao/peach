"""Proxy targets for playing a follow candidate inside Peach.

The browser receives only a Peach URL. Upstream URLs stay in the ledger/source layer, and
Rule34Video's expiring signed URL is resolved only when the user explicitly presses play.
"""
from __future__ import annotations

import html
import re
import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Callable, Mapping

from . import follow_providers
from .follow_sources import USER_AGENT, f95_attachment_media_items
from .follow_secrets import Credential
from .follow_store import FollowItemRow
from .http import HttpRequest, HttpTransport


class FollowMediaUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedFollowMedia:
    url: str
    referer: str | None = None
    headers: Mapping[str, str] | None = None


#: 媒体代理允许的主机，投影自 follow_providers；不在表里的 provider 一律拒绝。
_PROVIDER_HOSTS = follow_providers.hosts()
_VIDEO_URL_RE = re.compile(r"\bvideo_url\s*:\s*'([^']+)'", re.IGNORECASE)


def _allowed(provider: str, url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").casefold()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return False
    return any(host == suffix or host.endswith("." + suffix)
               for suffix in _PROVIDER_HOSTS.get(provider, ()))


class FollowMediaResolver:
    """Resolve stable ledger candidates into short-lived upstream playback URLs."""

    def __init__(self, transport: HttpTransport, *, ttl: float = 300.0,
                 timeout: float = 20.0, max_bytes: int = 2_000_000):
        self.transport = transport
        self.ttl = ttl
        self.timeout = timeout
        self.max_bytes = max_bytes
        self._cache: dict[int, tuple[float, ResolvedFollowMedia]] = {}
        self._lock = threading.Lock()

    def with_credential_loader(
            self, loader: Callable[[str], Credential | None]) -> "FollowMediaResolver":
        self._credential_loader = loader
        return self

    def resolve(self, item: FollowItemRow, media_index: int | None = None) -> ResolvedFollowMedia:
        if item.metadata.get("media_needs_credential"):
            raise FollowMediaUnavailable("媒体需要来源登录会话")
        media_items = item.metadata.get("media_items")
        if (not isinstance(media_items, list) or not media_items) \
                and item.provider == "f95zone":
            media_items = f95_attachment_media_items(item.metadata)
        if isinstance(media_items, list) and media_items:
            index = 0 if media_index is None else media_index
            if index < 0 or index >= len(media_items):
                raise FollowMediaUnavailable("媒体序号不存在")
            media = media_items[index]
            if not isinstance(media, dict):
                raise FollowMediaUnavailable("媒体条目格式不符")
            url = str(media.get("url") or "")
            resource_provider = str(media.get("resource_provider") or "")
            if resource_provider == "gofile":
                if not _allowed_resource(url, ("gofile.io",)):
                    raise FollowMediaUnavailable("Gofile 返回了不受信任的媒体地址")
                loader = getattr(self, "_credential_loader", None)
                credential = loader("gofile") if loader else None
                token = str(credential.values.get("api_token") or "") if credential else ""
                if not token:
                    raise FollowMediaUnavailable("Gofile API token 未配置")
                return ResolvedFollowMedia(
                    url, item.url, {"Authorization": f"Bearer {token}"})
            if resource_provider == "fanbox":
                if not _allowed_resource(url, ("fanbox.cc",)):
                    raise FollowMediaUnavailable("FANBOX 返回了不受信任的图片地址")
                return ResolvedFollowMedia(url, item.url)
            if resource_provider == "f95zone":
                if not _allowed_resource(url, ("attachments.f95zone.to",)):
                    raise FollowMediaUnavailable("F95 返回了不受信任的图片地址")
                return ResolvedFollowMedia(url, item.url)
            raise FollowMediaUnavailable("媒体来源不受支持")
        if item.provider != "rule34video":
            if not item.media_url or not _allowed(item.provider, item.media_url):
                raise FollowMediaUnavailable("来源媒体地址不可用")
            return ResolvedFollowMedia(item.media_url, item.url)

        with self._lock:
            cached = self._cache.get(item.id)
            if cached and cached[0] > time.monotonic():
                return cached[1]
        if not item.url or not _allowed(item.provider, item.url):
            raise FollowMediaUnavailable("Rule34Video 详情地址不可用")
        response = self.transport(
            HttpRequest("GET", item.url, {"User-Agent": USER_AGENT,
                                           "Accept": "text/html"}),
            self.timeout, self.max_bytes,
        )
        if response.status != 200 or len(response.body) > self.max_bytes:
            raise FollowMediaUnavailable("Rule34Video 详情页未取得")
        text = response.body.decode("utf-8", errors="replace")
        matched = _VIDEO_URL_RE.search(text)
        if not matched:
            raise FollowMediaUnavailable("Rule34Video 正片地址未取得")
        target = html.unescape(matched.group(1)).replace("\\/", "/")
        if not _allowed(item.provider, target):
            raise FollowMediaUnavailable("Rule34Video 返回了不受信任的媒体地址")
        resolved = ResolvedFollowMedia(target, item.url)
        with self._lock:
            self._cache[item.id] = (time.monotonic() + self.ttl, resolved)
        return resolved


def _allowed_resource(url: str, hosts: tuple[str, ...]) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").casefold()
    return (parsed.scheme == "https" and not parsed.username and not parsed.password
            and any(host == suffix or host.endswith("." + suffix) for suffix in hosts))
