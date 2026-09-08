"""作者头像与来源图标的本地缓存。

头像和站点图标是元数据：一张几 KB 到十几 KB，跟着来源走，不像视频和图片那样大到
不能存。保存在本机有三个好处：页面不再让浏览器直接向对方站点要图（不泄露正在看
谁的关注）；站点抽风、限流或改版时旧图还在，不会满屏碎图；每次开页也不必再打一遍
别人的服务器。

地址永远由服务端从固定表或固定主机拼出来，不接受前端递过来的 URL——否则这里就是
一个任意地址抓取的口子。取回的字节要先能按图片认出来才落盘：站点回的机器人质询页、
错误页和整页 HTML 都不算图。

保鲜期由设置里的「头像与站点图标刷新」决定（`web_settings.metadata_refresh_seconds`），
到期后下次显示时重取；重取失败就继续用旧的，并在 `RETRY_SECONDS` 内不再反复去试。
"""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Callable

import httpx

from .follow_sources import KemonoConnector
from .user_agent import USER_AGENT

#: 落在 `generated/` 下的目录名。头像与来源图标各占一个子目录，方便按类清理。
ROOT_NAME = "follow-assets"
#: 元数据图片的体积上限。头像 160×160 的 webp 十几 KB、favicon 几 KB；超过这个数的
#: 不是头像，多半是站点回了整页 HTML 或一张海报。
MAX_BYTES = 2 * 1024 * 1024
FETCH_TIMEOUT = 8.0
#: 一次重取失败后隔多久再试。关注页一屏几十张头像，站点挂掉时不能每次重绘都打几十枪。
RETRY_SECONDS = 3600

#: 各来源自己声明的站点图标。地址只在服务端；页面拿到的是 `/source-icon?provider=`。
#: simpcity 的 `/favicon.ico` 是 404，站点声明的图标在 `/data/assets/logo/` 下。
SOURCE_ICON_URLS: dict[str, str] = {
    "fanbox": "https://www.fanbox.cc/favicon.ico",
    "patreon": "https://www.patreon.com/favicon.ico",
    "subscribestar": "https://assets.subscribestar.com/assets/public/images/favicons/"
                     "favicon-32x32-b9aa1e7e5bab6cb1b28b5161e16f9d42.png",
    "kemono": "https://kemono.cr/assets/favicon-CPB6l7kH.ico",
    "coomer": "https://coomer.st/assets/favicon-CPB6l7kH.ico",
    "pawchive": "https://pawchive.pw/static/favicon.png",
    "rule34video": "https://rule34video.com/favicon-32x32.png",
    "rule34xxx": "https://rule34.xxx/favicon.ico",
    "rule34paheal": "https://rule34.paheal.net/favicon.ico",
    "gofile": "https://gofile.io/favicon.ico",
    "f95zone": "https://f95zone.to/assets/favicon-32x32.png",
    "simpcity": "https://simpcity.cr/data/assets/logo/favicon.png",
}

_MAGIC = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"\x00\x00\x01\x00", "image/x-icon"),
    (b"BM", "image/bmp"),
)


def sniff(data: bytes) -> str | None:
    """字节 → 图片 MIME；认不出就是 None。"""
    for magic, mime in _MAGIC:
        if data.startswith(magic):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[4:12] in (b"ftypavif", b"ftypavis"):
        return "image/avif"
    head = data[:2048].lstrip()
    if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head):
        return "image/svg+xml"
    return None


def content_type(path: Path) -> str:
    """已落盘文件的 MIME。落盘前已经 `sniff` 过，这里认不出只可能是文件被人改了。"""
    with path.open("rb") as handle:
        return sniff(handle.read(2048)) or "application/octet-stream"


def mirror_avatar_url(provider: str, ref: str) -> str | None:
    """归档站上的作者头像地址。**只有实测拿得到的来源才给，取不到就是 `None`。**

    2026-08-27 实测（`curl`，不带凭据）：
    `https://kemono.cr/icons/fanbox/30917150` → 302 → `img.kemono.cr`，
    200 `image/webp` 160×160；`pawchive.pw` 同路径 200、14,534 字节。
    coomer.st 对这个创作者回 404，但那只说明他不在 coomer 上，
    不能据此断定 coomer 没有这个端点——所以 coomer 照样按同一规则给 URL，
    取不到时页面退回作者首字母。

    rule34video / rule34.xxx **未取得**：没有可用的作者页样本可测，不猜一个路径。
    """
    if provider not in KemonoConnector.HOSTS:
        return None
    service, _, user = str(ref or "").partition("/")
    if not service or not user:
        return None
    return f"https://{KemonoConnector.HOSTS[provider]}/icons/{service}/{user}"


def cache_path(root: Path, kind: str, key: str) -> Path:
    digest = hashlib.sha256(f"{kind}:{key}".encode("utf-8")).hexdigest()[:32]
    return root / kind / f"{digest}.img"


def is_fresh(path: Path, ttl: int | None, now: float | None = None) -> bool:
    """`ttl` 为 None 表示从不重取：文件在就算新鲜。"""
    try:
        age = (now if now is not None else time.time()) - path.stat().st_mtime
    except OSError:
        return False
    return ttl is None or 0 <= age < ttl


def fetch_image(client: httpx.Client, url: str) -> bytes | None:
    """取一张图。不是 200、不是图、太大、网络出错都返回 None。不带任何凭据。"""
    try:
        response = client.get(
            url, headers={"User-Agent": USER_AGENT, "Accept": "image/*,*/*;q=0.5"},
            timeout=FETCH_TIMEOUT, follow_redirects=True)
    except (OSError, httpx.HTTPError):
        return None
    body = response.content
    if response.status_code != 200 or not body or len(body) > MAX_BYTES:
        return None
    return body if sniff(body) else None


def cached_image(root: Path, kind: str, key: str, ttl: int | None,
                 fetch: Callable[[], bytes | None], now: float | None = None) -> Path | None:
    """本地那份能用就用；到期了先重取，取不到继续用旧的；从没取到过才是 None。

    重取失败留一个 `.failed` 标记，`RETRY_SECONDS` 内不再出网——等站点恢复的这段时间里
    页面照常显示旧图，只是不再每次重绘都去碰它。
    """
    path = cache_path(root, kind, key)
    if is_fresh(path, ttl, now):
        return path
    marker = path.with_suffix(".failed")
    if is_fresh(marker, RETRY_SECONDS, now):
        return path if path.exists() else None
    body = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    if body:
        partial = path.with_suffix(".part")
        partial.write_bytes(body)
        partial.replace(path)
        _stamp(path, now)
        marker.unlink(missing_ok=True)
        return path
    marker.write_bytes(b"")
    _stamp(marker, now)
    return path if path.exists() else None


def _stamp(path: Path, now: float | None) -> None:
    """新鲜度按 mtime 算，所以调用方给了「现在」就把 mtime 也定在那一刻，两边用同一个钟。"""
    if now is not None:
        os.utime(path, (now, now))
