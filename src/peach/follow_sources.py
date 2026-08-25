"""站点专用追更连接器。

每个连接器只做发现：把一次显式的、有界的抓取翻译成 `FollowCandidate` 序列。
它们不写 ledger、不下载媒体、不在服务启动或普通浏览时联网，也不绕过任何机器人验证。
凭据由 `follow_secrets.CredentialStore` 提供，只进请求头或 POST 体，绝不进 URL。

站点结构证据取自 2026-08-25 的实测抓取，登记在 `docs/HANDOFF.md`。
"""
from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Mapping, Protocol

import httpx
from bs4 import BeautifulSoup

from .follow import DEFAULT_MAX_BYTES, FollowSourceError, _plain_text, _stable_id
from .follow_secrets import Credential, CredentialError
from .http import HttpRequest, HttpResponse, HttpTransport, HttpxTransport


#: 所有连接器共用的 UA。站点按它识别 Peach，不冒充浏览器。
USER_AGENT = "Peach/0.2 (+local self-hosted follow reader)"

#: 单次抓取的条目上限。追更只关心增量，不做全站归档。
DEFAULT_MAX_ITEMS = 100


@dataclass(frozen=True)
class FollowCandidate:
    """一个未经复核的追更候选。"""

    provider: str
    external_id: str
    title: str
    url: str | None = None
    media_url: str | None = None
    thumb_url: str | None = None
    published_at: str | None = None
    version: str | None = None
    duration: float | None = None
    author: str | None = None
    summary: str | None = None
    #: 来源自带的分组标识（如 booru 的 `parent_id`）。有它就不必靠标题猜同一作品的变体。
    group_hint: str | None = None
    extra: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceFetch:
    provider: str
    ref: str
    request_url: str
    semantics: str
    candidates: tuple[FollowCandidate, ...] = ()
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False
    raw_body: bytes | None = field(default=None, repr=False, compare=False)


class FollowConnector(Protocol):
    provider: str
    semantics: str

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None) -> SourceFetch: ...


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_from_epoch(value) -> str | None:
    try:
        return _iso_utc(datetime.fromtimestamp(int(value), tz=timezone.utc))
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _iso_from_text(value) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return _iso_utc(datetime.fromisoformat(text))
    except ValueError:
        return None


_RELATIVE_RE = re.compile(
    r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*(?:ago)?", re.IGNORECASE)

#: 相对时间换算成秒。月按 30 天、年按 365 天——只用来排序，不当精确发布时间用。
_RELATIVE_SECONDS = {
    "second": 1, "minute": 60, "hour": 3600, "day": 86400,
    "week": 604800, "month": 2592000, "year": 31536000,
}


def _iso_from_relative(text: str | None, *, now: datetime | None = None) -> str | None:
    """把 `1 week ago` 这类相对时间换算成近似 UTC 时间戳。

    rule34video 的列表页只给相对时间，没有绝对时间。换算结果**是近似值**，
    调用方必须在 `extra` 里标出 `published_precision='approximate'`，
    界面上也要照实显示，不能当成站点给出的精确发布时间。
    """
    if not text:
        return None
    matched = _RELATIVE_RE.search(text)
    if not matched:
        return None
    amount = int(matched.group(1))
    unit = _RELATIVE_SECONDS[matched.group(2).lower()]
    reference = now or datetime.now(timezone.utc)
    return _iso_utc(reference - timedelta(seconds=amount * unit))


_DURATION_RE = re.compile(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})\s*$")


def _duration_seconds(text: str | None) -> float | None:
    if not text:
        return None
    matched = _DURATION_RE.match(text)
    if not matched:
        return None
    hours, minutes, seconds = matched.groups()
    return float(int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds))


class _BaseConnector:
    provider = ""
    semantics = "work"
    #: 站点被机器人验证挡住时的说明；非空表示该连接器不可用。
    blocked_reason = ""

    def __init__(self, *, timeout: float = 15.0, max_bytes: int = DEFAULT_MAX_BYTES,
                 max_items: int = DEFAULT_MAX_ITEMS,
                 transport: HttpTransport | None = None,
                 credential: Credential | None = None):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.max_items = max_items
        self.transport = transport or HttpxTransport()
        self.credential = credential

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": USER_AGENT}

    def _get(self, url: str, *, headers: Mapping[str, str] | None = None,
             etag: str | None = None, last_modified: str | None = None) -> HttpResponse:
        if self.blocked_reason:
            raise FollowSourceError(self.blocked_reason)
        merged = self._headers()
        merged.update(headers or {})
        if etag:
            merged["If-None-Match"] = etag
        if last_modified:
            merged["If-Modified-Since"] = last_modified
        try:
            response = self.transport(HttpRequest("GET", url, merged),
                                      self.timeout, self.max_bytes)
        except (OSError, httpx.HTTPError) as exc:
            raise FollowSourceError(f"{self.provider} 请求失败") from exc
        if len(response.body) > self.max_bytes:
            raise FollowSourceError(f"{self.provider} 响应超出大小上限")
        return response

    @staticmethod
    def _conditional(response: HttpResponse) -> dict[str, str | None]:
        headers = {key.lower(): value for key, value in response.headers.items()}
        return {"etag": headers.get("etag"),
                "last_modified": headers.get("last-modified")}

    def _check_status(self, response: HttpResponse) -> None:
        if response.status in (401, 403):
            raise FollowSourceError(
                f"{self.provider} 拒绝访问（HTTP {response.status}）：需要有效凭据，"
                "或站点已加机器人验证")
        if response.status != 200:
            raise FollowSourceError(f"{self.provider} 返回 HTTP {response.status}")

    def _json(self, response: HttpResponse):
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FollowSourceError(f"{self.provider} 返回的不是合法 JSON") from exc


class KemonoConnector(_BaseConnector):
    """kemono.cr / coomer.st / pawchive.pw 共用同一套公开 JSON API。

    这三个站点对默认 `Accept` 头回 403，响应体里直接写着抓取应当带
    `Accept: text/css`。那是站点自己给出的抓取路径，不是绕过防护。

    `ref` 形如 `fanbox/30917150`：服务名 + 站内创作者 id。
    """

    semantics = "work"
    HOSTS = {"kemono": "kemono.cr", "coomer": "coomer.st", "pawchive": "pawchive.pw"}
    _SERVICE_RE = re.compile(r"^[a-z0-9_\-]{1,32}$")
    _USER_RE = re.compile(r"^[A-Za-z0-9_\-.]{1,64}$")

    def __init__(self, provider: str = "kemono", **kwargs):
        if provider not in self.HOSTS:
            raise FollowSourceError(f"未知的 kemono 系来源：{provider}")
        super().__init__(**kwargs)
        self.provider = provider
        self.host = self.HOSTS[provider]

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        headers["Accept"] = "text/css"
        return headers

    def _split_ref(self, ref: str) -> tuple[str, str]:
        service, _, user = (ref or "").strip().strip("/").partition("/")
        if not self._SERVICE_RE.match(service) or not self._USER_RE.match(user):
            raise FollowSourceError(
                f"{self.provider} 的 ref 必须形如 `service/user_id`，收到：{ref!r}")
        return service, user

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None) -> SourceFetch:
        service, user = self._split_ref(ref)
        url = f"https://{self.host}/api/v1/{service}/user/{user}/posts"
        response = self._get(url, etag=etag, last_modified=last_modified)
        common = {"provider": self.provider, "ref": ref, "request_url": url,
                  "semantics": self.semantics, **self._conditional(response)}
        if response.status == 304:
            return SourceFetch(not_modified=True, **common)
        self._check_status(response)
        payload = self._json(response)
        # kemono 回 {"posts": [...]}，pawchive 直接回列表；两种都要吃。
        posts = payload.get("posts", []) if isinstance(payload, dict) else payload
        if not isinstance(posts, list):
            raise FollowSourceError(f"{self.provider} 的帖子列表格式不符")
        candidates = tuple(
            self._candidate(post, service, user)
            for post in posts[: self.max_items]
            if isinstance(post, dict)
        )
        return SourceFetch(candidates=candidates, raw_body=response.body, **common)

    def _candidate(self, post: dict, service: str, user: str) -> FollowCandidate:
        post_id = str(post.get("id") or "")
        title = _plain_text(post.get("title")) or "(untitled)"
        page = f"https://{self.host}/{service}/user/{user}/post/{post_id}" if post_id else None
        primary = post.get("file") if isinstance(post.get("file"), dict) else {}
        attachments = [a for a in (post.get("attachments") or []) if isinstance(a, dict)]
        media = primary.get("path") or (attachments[0].get("path") if attachments else None)
        return FollowCandidate(
            provider=self.provider,
            external_id=post_id or _stable_id(title, str(post.get("published"))),
            title=title,
            url=page,
            media_url=f"https://{self.host}{media}" if media else None,
            published_at=_iso_from_text(post.get("published")),
            author=None,
            summary=_plain_text(post.get("substring")),
            extra={"service": service, "user": user,
                   "edited": post.get("edited"),
                   "attachment_count": len(attachments)},
        )


class Rule34VideoConnector(_BaseConnector):
    """rule34video.com 的创作者页（KVS 引擎，无公开 API，只能读 HTML）。

    `ref` 是模特/作者 slug，例如 `lazyprocrastinator`。
    """

    provider = "rule34video"
    semantics = "work"
    _SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,80}$")
    _VIDEO_RE = re.compile(r"^https://rule34video\.com/video/(\d+)/")

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None) -> SourceFetch:
        slug = (ref or "").strip().strip("/").lower()
        if not self._SLUG_RE.match(slug):
            raise FollowSourceError(f"rule34video 的 ref 必须是作者 slug，收到：{ref!r}")
        url = f"https://rule34video.com/models/{slug}/"
        response = self._get(url, headers={"Accept": "text/html"},
                             etag=etag, last_modified=last_modified)
        common = {"provider": self.provider, "ref": slug, "request_url": url,
                  "semantics": self.semantics, **self._conditional(response)}
        if response.status == 304:
            return SourceFetch(not_modified=True, **common)
        self._check_status(response)
        soup = BeautifulSoup(response.body, "html.parser")
        seen: set[str] = set()
        candidates: list[FollowCandidate] = []
        for anchor in soup.select('a[href*="/video/"]'):
            href = (anchor.get("href") or "").strip()
            matched = self._VIDEO_RE.match(href)
            if not matched or matched.group(1) in seen:
                continue
            seen.add(matched.group(1))
            candidates.append(self._candidate(anchor, href, matched.group(1)))
            if len(candidates) >= self.max_items:
                break
        if not candidates:
            raise FollowSourceError(
                "rule34video 创作者页没有解析出任何作品：页面结构可能已变，"
                "或该 slug 不存在")
        return SourceFetch(candidates=tuple(candidates), raw_body=response.body, **common)

    def _candidate(self, anchor, href: str, video_id: str) -> FollowCandidate:
        title = _plain_text(anchor.get("title"))
        if not title:
            node = anchor.select_one(".thumb_title") or anchor.select_one(".title")
            title = _plain_text(node.get_text(" ")) if node else None
        thumb = anchor.select_one("img")
        thumb_url = None
        if thumb is not None:
            thumb_url = thumb.get("data-original") or thumb.get("data-src") or thumb.get("src")
            if isinstance(thumb_url, str) and thumb_url.startswith("data:"):
                thumb_url = None
        # `.time` 是时长，`.added` 是相对提交时间——列表页没有绝对时间。
        duration_node = anchor.select_one(".time")
        added_node = anchor.select_one(".added")
        added_text = _plain_text(added_node.get_text(" ")) if added_node else None
        preview = anchor.select_one("[data-preview]")
        return FollowCandidate(
            provider=self.provider,
            external_id=video_id,
            title=title or f"video {video_id}",
            url=href,
            media_url=str(preview.get("data-preview")) if preview is not None else None,
            thumb_url=thumb_url if isinstance(thumb_url, str) else None,
            published_at=_iso_from_relative(added_text),
            duration=_duration_seconds(
                _plain_text(duration_node.get_text(" ")) if duration_node else None),
            extra={"added_text": added_text,
                   "published_precision": "approximate" if added_text else "unknown",
                   "media_kind": "preview_clip"},
        )


class Rule34XxxConnector(_BaseConnector):
    """rule34.xxx 的官方 dapi。

    网页版已挂 Cloudflare Turnstile，Peach 不绕验证码，因此这里只走官方 API，
    并且必须带账号自己的 `user_id` + `api_key`（在
    `https://rule34.xxx/index.php?page=account&s=options` 生成）。凭据只进查询参数
    以外的位置不可行——dapi 只接受查询参数——所以请求 URL 不进日志也不进 ledger，
    只有 `request_url` 的脱敏形式会被记录。

    `ref` 是标签，例如 `lazyprocrastinator`。
    """

    provider = "rule34xxx"
    semantics = "work"
    _TAG_RE = re.compile(r"^[^\s&?#]{1,100}$")

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None) -> SourceFetch:
        tag = (ref or "").strip()
        if not self._TAG_RE.match(tag):
            raise FollowSourceError(f"rule34xxx 的 ref 必须是单个标签，收到：{ref!r}")
        if self.credential is None:
            raise CredentialError(
                "rule34xxx 需要 user_id 与 api_key；请把它们写进 "
                "peach-data/secrets/follow/rule34xxx.json")
        user_id, api_key = self.credential.require("user_id", "api_key")
        query = urllib.parse.urlencode({
            "page": "dapi", "s": "post", "q": "index", "json": "1",
            "limit": str(min(self.max_items, 1000)), "tags": tag,
            "user_id": user_id, "api_key": api_key,
        })
        url = f"https://api.rule34.xxx/index.php?{query}"
        safe_url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tag}"
        response = self._get(url, headers={"Accept": "application/json"},
                             etag=etag, last_modified=last_modified)
        common = {"provider": self.provider, "ref": tag, "request_url": safe_url,
                  "semantics": self.semantics, **self._conditional(response)}
        if response.status == 304:
            return SourceFetch(not_modified=True, **common)
        self._check_status(response)
        body = response.body.decode("utf-8", errors="replace").strip()
        if body.startswith('"') and "authentication" in body.lower():
            raise CredentialError("rule34xxx 拒绝了 user_id/api_key")
        payload = self._json(response)
        posts = payload.get("post", []) if isinstance(payload, dict) else payload
        if not isinstance(posts, list):
            raise FollowSourceError("rule34xxx 的帖子列表格式不符")
        candidates = tuple(
            self._candidate(post, tag)
            for post in posts[: self.max_items]
            if isinstance(post, dict)
        )
        return SourceFetch(candidates=candidates, raw_body=response.body, **common)

    def _candidate(self, post: dict, tag: str) -> FollowCandidate:
        post_id = str(post.get("id") or "")
        # booru 帖子没有标题。用原始文件名当标题，跨站比对时它比标签串靠谱得多；
        # 没有文件名就退回标签串，并在 extra 里留下判据。
        image = str(post.get("image") or "")
        stem = re.sub(r"\.[a-z0-9]{2,5}$", "", image, flags=re.IGNORECASE)
        tags = str(post.get("tags") or "")
        title = _plain_text(stem.replace("_", " ")) or _plain_text(tags) or f"post {post_id}"
        parent = post.get("parent_id")
        return FollowCandidate(
            provider=self.provider,
            external_id=post_id or _stable_id(image, tags),
            title=title,
            url=f"https://rule34.xxx/index.php?page=post&s=view&id={post_id}"
                if post_id else None,
            media_url=str(post.get("file_url")) if post.get("file_url") else None,
            thumb_url=str(post.get("preview_url")) if post.get("preview_url") else None,
            published_at=_iso_from_epoch(post.get("change")),
            group_hint=str(parent) if parent not in (None, 0, "0", "") else None,
            extra={"tag": tag, "tags": tags, "score": post.get("score"),
                   "source": post.get("source"), "title_from": "image" if stem else "tags"},
        )


class F95ZoneConnector(_BaseConnector):
    """f95zone.to 的线程追更。

    主贴的版本号更新常常滞后于回复——真正的新链接先出现在楼下——所以这里读的是
    线程的 `/latest` 页而不是主贴；`latest_data.php` 另给线程当前的 `version` 与时间戳。

    **发现不需要登录，取媒体需要。** 2026-08-25 实测 `/latest` 页在无 cookie 下
    完整返回回复正文与外链（`/masked/...` 之类），所以追更判定本身不吃凭据；但
    `attachments.f95zone.to` 上的附件图片和 `masked` 链接的真实跳转要登录会话才拿得到。
    候选因此带 `media_needs_credential`，下载动作必须先看这个标志，不要拿 403 的
    附件冒充「已保存」。

    `ref` 是线程 id，例如 `50685`。
    """

    provider = "f95zone"
    semantics = "release"
    _THREAD_RE = re.compile(r"^\d{1,12}$")
    #: latest_data.php 按分类分库，线程不在哪个分类里事先不知道，只能逐个试。
    CATEGORIES = ("games", "animations", "comics", "assets", "mods")

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None) -> SourceFetch:
        thread = (ref or "").strip()
        if not self._THREAD_RE.match(thread):
            raise FollowSourceError(f"f95zone 的 ref 必须是线程 id，收到：{ref!r}")
        url = f"https://f95zone.to/threads/{thread}/latest"
        headers = {"Accept": "text/html"}
        if self.credential and self.credential.values.get("cookie"):
            headers["Cookie"] = self.credential.values["cookie"]
        response = self._get(url, headers=headers, etag=etag, last_modified=last_modified)
        common = {"provider": self.provider, "ref": thread, "request_url": url,
                  "semantics": self.semantics, **self._conditional(response)}
        if response.status == 304:
            return SourceFetch(not_modified=True, **common)
        self._check_status(response)
        soup = BeautifulSoup(response.body, "html.parser")
        title = self._thread_title(soup)
        candidates = tuple(self._replies(soup, thread, title or f"thread {thread}"))
        if not candidates:
            raise FollowSourceError(
                "f95zone 线程页没有解析出任何回复：可能需要登录，或页面结构已变")
        return SourceFetch(candidates=candidates, raw_body=response.body, **common)

    @staticmethod
    def _thread_title(soup) -> str | None:
        """取 `h1.p-title-value` 并去掉前缀标签。

        `<title>` 会被站点拼上栏目名和站名，og:title 同样带前缀，只有 h1 里的
        `.label` 是可以精确摘掉的结构。
        """
        heading = soup.select_one("h1.p-title-value")
        if heading is None:
            return None
        for label in heading.select(".label, .labelLink"):
            label.extract()
        return _plain_text(heading.get_text(" "))

    def _replies(self, soup, thread: str, thread_title: str):
        posts = soup.select('article[data-content^="post-"]')
        for article in posts[-self.max_items:]:
            content = str(article.get("data-content") or "")
            post_id = content.removeprefix("post-")
            if not post_id.isdigit():
                continue
            time_node = article.select_one("time")
            body = article.select_one(".bbWrapper")
            # XenForo 把被引用的楼层原样嵌在正文里。不剥掉的话，摘要会变成
            # 「某某 said: … Click to expand…」，而引用里的下载链接还会被算成这条
            # 回复自己发的——追更判断因此指向错误的楼层。
            if body is not None:
                for quote in body.select("blockquote, .bbCodeBlock, .js-expandWatch"):
                    quote.extract()
            links = [
                str(node.get("href")) for node in (body.select("a[href]") if body else [])
                if str(node.get("href", "")).startswith("http")
            ]
            yield FollowCandidate(
                provider=self.provider,
                external_id=post_id,
                title=thread_title,
                url=f"https://f95zone.to/threads/{thread}/post-{post_id}",
                media_url=links[0] if links else None,
                published_at=_iso_from_text(time_node.get("datetime"))
                if time_node is not None else None,
                author=_plain_text(str(article.get("data-author") or "")) or None,
                summary=_plain_text(body.get_text(" ")) if body else None,
                extra={"thread_id": thread, "link_count": len(links),
                       "links": links[:8],
                       # 发现是公开的，取媒体不是：附件与 masked 跳转都要登录会话。
                       "media_needs_credential": True},
            )

    def thread_index(self, category: str, query: str) -> tuple[dict, ...]:
        """在 `latest_data.php` 里按名字查线程；用于登记订阅时确认 id 与版本。"""
        if category not in self.CATEGORIES:
            raise FollowSourceError(f"未知的 f95zone 分类：{category}")
        params = urllib.parse.urlencode({
            "cmd": "list", "cat": category, "page": "1",
            "search": query, "rows": "30",
        })
        url = f"https://f95zone.to/sam/latest_alpha/latest_data.php?{params}"
        response = self._get(url, headers={"Accept": "application/json"})
        self._check_status(response)
        payload = self._json(response)
        rows = ((payload or {}).get("msg") or {}).get("data") or []
        return tuple(row for row in rows if isinstance(row, dict))


class SimpCityConnector(_BaseConnector):
    """simpcity.cr 目前挂着 DDoS-Guard 的浏览器质询。

    Peach 不绕机器人验证，所以这个连接器只登记不可用，并把原因原样报出来。
    """

    provider = "simpcity"
    semantics = "release"
    blocked_reason = (
        "simpcity.cr 由 DDoS-Guard 的浏览器质询保护；Peach 不绕机器人验证。"
        "要接入需要你在浏览器里通过质询后提供会话 cookie，或改用其他来源。")

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None) -> SourceFetch:
        raise FollowSourceError(self.blocked_reason)


CONNECTORS: dict[str, type] = {
    "kemono": KemonoConnector,
    "coomer": KemonoConnector,
    "pawchive": KemonoConnector,
    "rule34video": Rule34VideoConnector,
    "rule34xxx": Rule34XxxConnector,
    "f95zone": F95ZoneConnector,
    "simpcity": SimpCityConnector,
}


def build_connector(provider: str, **kwargs) -> FollowConnector:
    factory = CONNECTORS.get(provider)
    if factory is None:
        raise FollowSourceError(f"未知的追更来源：{provider}")
    if factory is KemonoConnector:
        return KemonoConnector(provider=provider, **kwargs)
    return factory(**kwargs)
