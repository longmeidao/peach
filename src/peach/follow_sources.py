"""站点专用追更连接器。

每个连接器只做发现：把一次显式的、有界的抓取翻译成 `FollowCandidate` 序列。
它们不写 ledger、不下载媒体、不在服务启动或普通浏览时联网，也不绕过任何机器人验证。
凭据由 `follow_secrets.CredentialStore` 提供，只进请求头或 POST 体，绝不进 URL。

站点结构证据取自 2026-08-25 的实测抓取，登记在 `docs/HANDOFF.md`。
"""
from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Mapping, Protocol

import httpx
from bs4 import BeautifulSoup

from .fanbox import FanboxContentError, normalize_fanbox_post
from . import follow_providers
from .follow import (
    DEFAULT_MAX_BYTES, FollowHistoryEnd, FollowSourceError, plain_text, stable_id,
)
from .follow_secrets import Credential, CredentialError
from .follow_gofile import GofileExpander, folder_labels
from .http import CurlCffiTransport, HttpRequest, HttpResponse, HttpTransport, HttpxTransport


#: 默认连接器共用的 UA。只有 ADR-0019 明确登记的 FANBOX 详情传输例外。
USER_AGENT = "Peach/0.2 (+local self-hosted follow reader)"

#: 单次抓取的条目上限。追更只关心增量，不做全站归档。
DEFAULT_MAX_ITEMS = 100

#: 网盘与文件分发站。**判「这一帖有没有交付资源」只认这张表，不认「有外链」**——
#: 投票链接（`forms.gle`）、社交主页、打赏页都是外链，把它们算成资源会让每一帖都算
#: release，过滤就等于没做。
#:
#: 这张表注定不全，作者换网盘就得往里加。加的时候只加**分发文件**的域名：
#: 判据是点进去拿到的是文件，不是一个页面。
_FILE_HOST_DOMAINS = frozenset({
    "downloads.fanbox.cc",
    "gofile.io", "mega.nz", "mega.io", "mediafire.com", "pixeldrain.com",
    "workupload.com", "catbox.moe", "1fichier.com", "dropbox.com",
    "drive.google.com", "docs.google.com", "1drv.ms", "onedrive.live.com",
    "sendspace.com", "bunkr.site", "bunkrr.su", "cyberdrop.me",
    "krakenfiles.com", "buzzheavier.com", "saint2.su", "swisstransfer.com",
    "wetransfer.com", "we.tl", "ufile.io", "zippyshare.com", "anonfiles.com",
    "qiwi.gg", "mixdrop.co", "gigafile.nu", "xgf.nu", "firestorage.jp",
    "terabox.com", "1024terabox.com", "pan.baidu.com", "123pan.com",
    "aliyundrive.com", "alipan.com", "pan.quark.cn", "lanzou.com",
    "lanzoui.com", "lanzoux.com", "yadi.sk", "disk.yandex.ru",
    "disk.yandex.com", "fileditch.com",
})

_LINK_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.IGNORECASE)
#: URL 看起来指向一张图片。不只 f95 在用：归档站推导旧行缩略图时也要这个判据。
_IMAGE_URL_RE = re.compile(
    r"\.(?:avif|bmp|gif|jpe?g|png|webp)(?:$|[?#])", re.IGNORECASE)


def resource_links(text: str | None) -> list[str]:
    """文本里指向网盘 / 文件站的链接。

    只按域名判，不按「看起来像下载」判。匹配到注册域边界：`gofile.io` 命中
    `https://gofile.io/d/x` 和 `https://www.gofile.io/d/x`，但**不**命中
    `https://gofile.io.evil.example/`——那个的注册域根本不是 gofile。
    """
    found = []
    for link in _LINK_RE.findall(text or ""):
        if _is_resource_url(link) and link not in found:
            found.append(link)
    return found


def f95_attachment_media_items(metadata: Mapping[str, object]) -> list[dict[str, object]]:
    """Project F95 image attachments, including rows saved before galleries existed."""
    attachments = metadata.get("attachments")
    if not isinstance(attachments, list):
        return []
    result: list[dict[str, object]] = []
    for index, value in enumerate(attachments):
        url = str(value or "")
        try:
            parsed = urllib.parse.urlsplit(url)
        except ValueError:
            continue
        if (parsed.scheme != "https" or parsed.hostname != "attachments.f95zone.to"
                or not _IMAGE_URL_RE.search(url)):
            continue
        name = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1]) or f"image-{index + 1}"
        result.append({
            "id": f"f95-attachment-{index + 1}",
            "name": name,
            "media_kind": "image",
            "url": url,
            "thumb_url": url,
            "resource_provider": "f95zone",
        })
    return result


def _is_resource_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    return parsed.scheme == "https" and any(
        host == domain or host.endswith("." + domain)
        for domain in _FILE_HOST_DOMAINS
    )


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
    #: 来源自带的分组标识。可能是站内的父帖，也可能是归一化后的跨站出处键
    #: （`fanbox:12304831` 这种）。有它就不必靠标题猜同一作品的变体。
    group_hint: str | None = None
    #: 标题是不是一个真正的名字。booru 没有标题，只能拿标签凑一个可读标签——
    #: 那种「标题」不能参与按标题分组，否则同一作者的两个作品会因标签相似被并掉。
    title_is_name: bool = True
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
    #: 这次抓取里被判为「不是 release」而丢掉的条数。必须报出来：用户看到的条目数
    #: 比站点上少的时候，他得能分清少的是被过滤掉的，还是根本没抓到。
    skipped: int = 0
    #: `skipped` 里有多少条是来源详情确认的超大跨作者合集。单列出来让界面能说清
    #: 「主动不收」而不是把它误报成「没有资源」。
    skipped_compilations: int = 0
    #: 列表判不出来、额外抓了详情页的条数。这是唯一会放大请求数的路径，
    #: 报出来才能看出某个作者是不是每一帖都要多打一次站点。
    probed: int = 0
    raw_body: bytes | None = field(default=None, repr=False, compare=False)


class FollowConnector(Protocol):
    provider: str
    semantics: str

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None,
              page: int = 0) -> SourceFetch: ...


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
_ISO_DURATION_RE = re.compile(
    r"^PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?$",
    re.IGNORECASE,
)


def _duration_seconds(text: str | None) -> float | None:
    if not text:
        return None
    matched = _DURATION_RE.match(text)
    if not matched:
        return None
    hours, minutes, seconds = matched.groups()
    return float(int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds))


def _iso_duration_seconds(text) -> float | None:
    """Schema.org `PT0H27M45S` 时长转秒。"""
    if not isinstance(text, str):
        return None
    matched = _ISO_DURATION_RE.match(text.strip())
    if not matched or not any(matched.groups()):
        return None
    hours, minutes, seconds = (float(value or 0) for value in matched.groups())
    return hours * 3600 + minutes * 60 + seconds


#: 站点自报出处时能认出来的原始平台。键是主机名后缀，值是分组键的前缀。
#: 这些前缀是**跨站**的：rule34.xxx 的 `source` 指向某个 fanbox 帖时，产生的键和
#: kemono 上同一个帖子的键完全相同，跨站重复因此不必靠标题去猜。
_ORIGIN_HOSTS: tuple[tuple[str, str], ...] = (
    ("fanbox.cc", "fanbox"),
    ("patreon.com", "patreon"),
    ("pixiv.net", "pixiv"),
    ("x.com", "x"),
    ("twitter.com", "x"),
    ("subscribestar.adult", "subscribestar"),
    ("gumroad.com", "gumroad"),
)

_ORIGIN_ID_RE = re.compile(r"/(?:posts?|status(?:es)?|artworks)/(\d{4,})")


def origin_group_key(source_url: str | None) -> str | None:
    """把站点自报的出处 URL 归一成跨站可比的分组键。

    实测（2026-08-25）同一个 fanbox 帖在 rule34.xxx 上有两种写法——
    `lazyprocrast.fanbox.cc/posts/12304831` 和
    `www.fanbox.cc/@lazyprocrast/posts/12304831`——必须归一到同一个键，
    而那串数字正是 kemono 上同一帖子的 post id。
    """
    if not source_url or not isinstance(source_url, str):
        return None
    try:
        parsed = urllib.parse.urlsplit(source_url.strip())
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if not host:
        return None
    platform = next(
        (name for suffix, name in _ORIGIN_HOSTS
         if host == suffix or host.endswith("." + suffix)),
        None,
    )
    if platform is None:
        return None
    matched = _ORIGIN_ID_RE.search(parsed.path)
    return f"{platform}:{matched.group(1)}" if matched else None


def _is_opaque_filename(stem: str) -> bool:
    """文件名是不是哈希。

    rule34.xxx 实测 15/15 的 `image` 都是 32 位十六进制哈希——拿它当标题既不可读，
    又会让每条帖子各自成组，跨站去重永远不可能命中。
    """
    return bool(re.fullmatch(r"[0-9a-f]{16,}", stem.strip().lower()))


def _exc_summary(exc: Exception, limit: int = 140) -> str:
    """把底层网络异常压成一行能看懂的原因，跟着「请求失败」一起报给用户。"""
    text = f"{type(exc).__name__}: {exc}".strip()
    return re.sub(r"\s+", " ", text)[:limit]


class _BaseConnector:
    provider = ""
    semantics = "work"
    #: 站点被机器人验证挡住时的说明；非空表示该连接器不可用。
    blocked_reason = ""
    #: 往回翻页时代表「没有更早的了」的上游状态码。声明在类上而不是每次调用
    #: `_request` 时传参，因为 `is_history_end_error` 要用同一份声明去认旧行。
    HISTORY_END_STATUSES: tuple[int, ...] = ()

    def __init__(self, *, timeout: float = 15.0, max_bytes: int = DEFAULT_MAX_BYTES,
                 max_items: int = DEFAULT_MAX_ITEMS,
                 transport: HttpTransport | None = None,
                 credential: Credential | None = None,
                 gofile_credential: Credential | None = None):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.max_items = max_items
        self.transport = transport or HttpxTransport()
        self.credential = credential
        self.gofile_credential = gofile_credential

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": USER_AGENT}

    def _send(self, method: str, url: str, body: bytes | None, *,
              headers: Mapping[str, str], base: Mapping[str, str]) -> HttpResponse:
        """发一次请求。`_get`/`_post` 的共同那半都在这里。

        拦下被拦的站、合并头、把网络异常压成一句话、卡住响应大小——这四件事
        与方法无关，以前两边各写一份。两份已经开始分岁：`connector_headers=False`
        只在 GET 那一份里有，而“跳站不带来源站 Cookie”是安全语义，不应该
        取决于用的是哪个动词。
        """
        if self.blocked_reason:
            raise FollowSourceError(self.blocked_reason)
        merged = dict(base)
        merged.update(headers)
        try:
            response = self.transport(HttpRequest(method, url, merged, body),
                                      self.timeout, self.max_bytes)
        except (OSError, httpx.HTTPError) as exc:
            raise FollowSourceError(
                f"{self.provider} 请求失败：{_exc_summary(exc)}") from exc
        if len(response.body) > self.max_bytes:
            raise FollowSourceError(f"{self.provider} 响应超出大小上限")
        return response

    def _get(self, url: str, *, headers: Mapping[str, str] | None = None,
             etag: str | None = None, last_modified: str | None = None,
             connector_headers: bool = True) -> HttpResponse:
        conditional = dict(headers or {})
        if etag:
            conditional["If-None-Match"] = etag
        if last_modified:
            conditional["If-Modified-Since"] = last_modified
        # 跨站资源 API 不能继承来源站的 Cookie。Gofile 只拿自己的 Bearer token；
        # FANBOX/F95 的会话不得跟着资源链接发到第三方主机。
        base = self._headers() if connector_headers else {"User-Agent": USER_AGENT}
        return self._send("GET", url, None, headers=conditional, base=base)

    def _post(self, url: str, body: bytes, *,
              headers: Mapping[str, str] | None = None,
              connector_headers: bool = True) -> HttpResponse:
        base = self._headers() if connector_headers else {"User-Agent": USER_AGENT}
        return self._send("POST", url, body, headers=headers or {}, base=base)

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
        if response.status == 429:
            raise FollowSourceError(
                f"{self.provider} 返回 HTTP 429：请求过于频繁，稍后再试")
        if response.status != 200:
            raise FollowSourceError(f"{self.provider} 返回 HTTP {response.status}")

    #: 上游限流页的固定句式（2026-08-29 实测 rule34.xxx）：HTTP 200 + 文本正文
    #: "You currently have a limit of 60 requests every 60 second(s)"。不识别的话
    #  会被报成「请求失败/不是合法 JSON」，用户看不出是被限流了。
    _RATE_LIMIT_RE = re.compile(
        r"limit of (\d+) requests? every (\d+) seconds?", re.IGNORECASE)

    def _upstream_reason(self, response: HttpResponse) -> str | None:
        """能从响应正文里读出的明确失败原因；读不出就返回 None。"""
        text = response.body.decode("utf-8", errors="replace")
        matched = self._RATE_LIMIT_RE.search(text)
        if matched:
            count, seconds = matched.group(1), matched.group(2)
            return (f"{self.provider} 触发频率限制：每 {seconds} 秒最多 "
                    f"{count} 次请求，请稍后再试")
        return None

    @staticmethod
    def _body_snippet(response: HttpResponse, limit: int = 120) -> str:
        text = re.sub(r"<[^>]+>", " ", response.body.decode("utf-8", errors="replace"))
        return re.sub(r"\s+", " ", text).strip()[:limit]

    def parse_json(self, response: HttpResponse):
        """解析一份已经取回的响应；不是合法 JSON 就抛错。"""
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            reason = self._upstream_reason(response)
            if reason:
                raise FollowSourceError(reason) from exc
            snippet = self._body_snippet(response)
            detail = f"：{snippet}" if snippet else ""
            raise FollowSourceError(
                f"{self.provider} 返回的不是合法 JSON{detail}") from exc

    def _request(self, url: str, *, ref: str, etag: str | None = None,
                 last_modified: str | None = None, page: int = 0,
                 headers: Mapping[str, str] | None = None,
                 request_url: str | None = None,
                 ) -> tuple[dict[str, object], HttpResponse | None]:
        """每个连接器 fetch 开头都一样的那段：条件请求 → 304 短路 → 状态检查。

        返回 `(common, response)`。`response` 为 None 表示站点回了 304，调用方直接
        `return SourceFetch(not_modified=True, **common)`，不用再自己拼 common。

        往回翻页时不带条件请求头：`If-None-Match` 存的是第一页的 etag，拿它去问第二页
        很可能换回 304，表现就是「点了没反应」。这条规则过去在每个连接器里各写一遍，
        现在只有这里一处。

        `request_url` 是落进证据的那个 URL。带凭据的真实请求 URL 绝不能落盘——
        rule34xxx 的 `api_key` 在查询串里，必须传一个脱敏版本进来。
        """
        response = (self._get(url, headers=headers) if page
                    else self._get(url, headers=headers,
                                   etag=etag, last_modified=last_modified))
        common: dict[str, object] = {
            "provider": self.provider, "ref": ref,
            "request_url": request_url or url,
            "semantics": self.semantics, **self._conditional(response),
        }
        if response.status == 304:
            return common, None
        if page and response.status in self.HISTORY_END_STATUSES:
            raise FollowHistoryEnd("没有更多历史内容")
        self._check_status(response)
        return common, response

    @classmethod
    def display_thumb_url(cls, item) -> str | None:
        """一条已入库的条目现在该用哪个缩略图 URL。

        站点的 CDN 规则会变，而错的 URL 已经写进上千行。所以改写发生在读取时而不是
        改 ledger：这是可推导的投影，不是真相字段。默认照原样用，只有实测证明当前
        规则取不到的站点才在子类里覆盖——那份实测属于连接器，不属于 Web 层。
        """
        return str(item.thumb_url or "") or None

    @classmethod
    def profile_handle(cls, ref: str) -> str:
        """这条 ref 里可以当作者别名用的平台手柄，没有就返回空串。

        只有官方渠道才有这种手柄：`fanbox/ffxivinitiala` 里的 `ffxivinitiala`
        就是作者本人在那个平台的名字。归档站与标签站的 ref 是数字 id 或标签，
        它们不是名字，学成别名只会造出一个假作者。
        """
        return ""

    @classmethod
    def is_history_end_error(cls, message: str) -> bool:
        """一句已经落盘的错误文本，其实是「历史到底」吗？

        `record_history_end` 之前的版本把往回翻到尽头记成了 `error`，正文就是
        `_check_status` 那句 `<provider> 返回 HTTP <status>`。判据只能是本连接器
        声明的 `HISTORY_END_STATUSES`——原来是在 Web 层照站点名硬编码中文串比较，
        新增来源时没人会想到还要改那一处。
        """
        matched = re.fullmatch(r".+ 返回 HTTP (\d{3})",
                               str(message or "").strip(), re.IGNORECASE)
        return bool(matched) and int(matched.group(1)) in cls.HISTORY_END_STATUSES

    def probe(self, url: str, *, headers: Mapping[str, str] | None = None) -> HttpResponse:
        """探测一个 URL 是否存在，不检查状态码。

        发现流程按状态码判断「这个作者页在不在」，404 是有意义的答案而不是故障，
        所以这里刻意不做 `_check_status`。有了它，`follow_discovery` 不必再去摸
        连接器的私有方法。
        """
        return self._get(url, headers=headers)

    def fetch_json(self, url: str, *, headers: Mapping[str, str] | None = None):
        """取回并解析一份 JSON；状态码不是 200 就抛错。"""
        response = self._get(url, headers=headers)
        self._check_status(response)
        return self.parse_json(response)

    def _gofile_media(self, links: list[str], *, labels=None) -> tuple[dict[str, object], ...]:
        """把帖子里的 Gofile 链接展开成媒体条目；实现见 `follow_gofile`。

        留一个薄委托而不是让连接器直接构造展开器：调用点（f95zone / fanbox）不必知道
        展开器怎么造，而 Gofile 的 HTTP 细节也不再摊在站点基类里。
        """
        return GofileExpander(
            self.transport, credential=self.gofile_credential,
            timeout=self.timeout, max_bytes=self.max_bytes, max_items=self.max_items,
        ).expand(links, labels=labels)


class KemonoConnector(_BaseConnector):
    """kemono.cr / coomer.st / pawchive.pw 共用同一套公开 JSON API。

    这三个站点对默认 `Accept` 头回 403，响应体里直接写着抓取应当带
    `Accept: text/css`。那是站点自己给出的抓取路径，不是绕过防护。

    `ref` 形如 `fanbox/30917150`：服务名 + 站内创作者 id。
    """

    semantics = "work"
    HOSTS = {"kemono": "kemono.cr", "coomer": "coomer.st", "pawchive": "pawchive.pw"}
    #: 往回翻页翻到尽头时，kemono 系回 400（越界偏移）或 404（创作者没有更多帖子）。
    HISTORY_END_STATUSES = (400, 404)
    #: 原始文件的主机。2026-08-30 实测（取证见
    #: `docs/reference-snapshots/kemono-archive-media-host.md`）三站行为并不一致：
    #: kemono/coomer 的主域对 `/data/<path>` 回 302，分别指向 `n1.` 和 `n4.` 节点——
    #: 编号会变，所以走主域让站点自己路由，不写死；pawchive 主域对 `/data` 直接 404，
    #: 必须点名 `file.` 子域。
    #: 路径也要带 `/data` 前缀：以前拼的是 `https://<host><path>`，少了这一段，
    #: 三站都取不到原始文件。
    FILE_HOSTS = {"pawchive": "file.pawchive.pw"}
    _SERVICE_RE = re.compile(r"^[a-z0-9_\-]{1,32}$")
    _USER_RE = re.compile(r"^[A-Za-z0-9_\-.]{1,64}$")

    #: 一次抓取最多为「判不出来」的帖子额外打几次详情页。这是唯一会让请求数随条目数
    #: 增长的路径：一个从不贴附件、只发网盘链接的作者会让每一帖都触发一次。上限用完
    #: 之后剩下的判不出来的帖子一律保留——宁可多留卡片，不能因为额度用完就删更新。
    DEFAULT_MAX_PROBES = 12

    #: 列表接口一页的条数，2026-08-27 实测为 50（`?o=50` 拿到的是第 51 条起）。
    PAGE_SIZE = 50

    def __init__(self, provider: str = "kemono", *,
                 max_probes: int = DEFAULT_MAX_PROBES, **kwargs):
        if provider not in self.HOSTS:
            raise FollowSourceError(f"未知的 kemono 系来源：{provider}")
        super().__init__(**kwargs)
        self.provider = provider
        self.host = self.HOSTS[provider]
        self.max_probes = max_probes

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
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        service, user = self._split_ref(ref)
        url = f"https://{self.host}/api/v1/{service}/user/{user}/posts"
        if page:
            # 实测这个接口一页固定 50 条，往回翻用 `?o=` 偏移。
            url = f"{url}?o={page * self.PAGE_SIZE}"
        common, response = self._request(url, ref=ref, etag=etag,
                                         last_modified=last_modified, page=page)
        if response is None:
            return SourceFetch(not_modified=True, **common)
        payload = self.parse_json(response)
        # kemono 回 {"posts": [...]}，pawchive 直接回列表；两种都要吃。
        posts = payload.get("posts", []) if isinstance(payload, dict) else payload
        if not isinstance(posts, list):
            raise FollowSourceError(f"{self.provider} 的帖子列表格式不符")
        if page and not posts:
            raise FollowHistoryEnd("没有更多历史内容")
        kept, skipped, probed = [], 0, 0
        for post in posts[: self.max_items]:
            if not isinstance(post, dict):
                continue
            verdict = self._delivers_resource(post)
            if verdict is None and probed < self.max_probes:
                # 列表接口判不出来才去抓详情。这是唯一一处「一帖一请求」，
                # 所以只在拿不准时用，并且有上限。
                probed += 1
                verdict = self._probe_post(post, service, user)
            # 只有**明确判定不是** release 才丢。额度用完后仍然「不知道」的一律保留：
            # 因为探测预算耗尽就删掉用户的更新，是拿一个内部限额换一次不可见的数据丢失。
            if verdict is False:
                skipped += 1
                continue
            kept.append(self._candidate(post, service, user))
        return SourceFetch(candidates=tuple(kept), skipped=skipped, probed=probed,
                           raw_body=response.body, **common)

    @staticmethod
    def _delivers_resource(post: dict) -> bool | None:
        """这一帖交付了资源没有。`None` 表示**列表接口判不出来**，要去抓详情。

        用户定的判据是「真正的资源贴要么贴附件，要么附上网盘链接」，而且
        **有些作者只做图**——所以一张图片附件就足够算数，不要求是压缩包或视频。

        三态而不是布尔，是因为列表接口只给 `substring`（正文摘要），网盘链接常常在
        摘要之外。判不出来时直接当成「不是 release」会删掉真东西，当成「是」又等于
        没过滤；只有第三种答案「不知道」才允许下一步去抓详情。

        **按标题关键词判投票贴是错的，不要再加回来。** 2026-08-27 拿
        LazyProcrastinator 的真实 50 条跑过一版 `poll|vote|survey|…` 正则，丢掉 18 条，
        其中有 `Public Poll Release + Littlest Ramble`、`October Poll Animations
        Released`——这位作者的正片就是按投票结果命名的。同一份数据里，
        那条「February Poll + Animations」的详情页 `poll` 字段是 `null`、正文里挂着
        gofile 链接，按资源判就是 release，按标题判就被删了。
        """
        has_file = bool((post.get("file") or {}).get("path")
                        if isinstance(post.get("file"), dict) else None)
        has_attachment = any(
            isinstance(item, dict) and item.get("path")
            for item in (post.get("attachments") or []))
        if has_file or has_attachment:
            return True
        if resource_links(post.get("substring")):
            return True
        return None

    def _probe_post(self, post: dict, service: str, user: str) -> bool:
        """抓详情页再判一次。**抓不到就当它是 release。**

        这一步是兜底，不是判据来源：网络抖一下就删掉用户的一份更新，是拿一次失败的
        请求换一次不可见的数据丢失。宁可多留一张卡片。
        """
        post_id = str(post.get("id") or "")
        if not post_id:
            return True
        url = f"https://{self.host}/api/v1/{service}/user/{user}/post/{post_id}"
        try:
            response = self._get(url)
            if response.status >= 400:
                return True
            payload = self.parse_json(response)
        except (FollowSourceError, OSError, httpx.HTTPError):
            return True
        if not isinstance(payload, dict):
            return True
        detail = payload.get("post") if isinstance(payload.get("post"), dict) else payload
        for key in ("attachments", "videos", "previews"):
            if any(isinstance(item, dict) and item.get("path")
                   for item in (payload.get(key) or [])):
                return True
        return bool(resource_links(str(detail.get("content") or "")))

    #: 缩略图能直接当封面用的扩展名。视频和压缩包没有缩略图，给了也是 404，
    #: 那会让卡片显示一个碎图而不是干净的占位。
    _THUMBABLE = (".jpg", ".jpeg", ".png", ".webp", ".gif")

    def _thumb_url(self, media: str | None) -> str | None:
        """归档站的封面。

        `thumbnail/` 前缀是必需的，不是可选的美化：换成 `/data<path>` 是 404。

        **主机用 `img.` 子域。**2026-08-30 实测（取证见
        `docs/reference-snapshots/kemono-archive-media-host.md`）：主域
        `kemono.cr` 只回 302，`pawchive.pw` 直接 404，两者的 `img.` 子域都回 200。
        2026-08-27 那次记的是主域回 200——站点行为后来变了，pawchive 的卡片因此
        一直是空的。

        以前这里根本没设 `thumb_url`，归档站的卡片因此一律没有封面——
        不是取不到，是压根没去取。
        """
        if not media or not str(media).lower().endswith(self._THUMBABLE):
            return None
        return f"https://img.{self.host}/thumbnail/data{media}"

    @classmethod
    def archive_media_host(cls, provider: str, url: str) -> str:
        """把归档站的静态资源指到 `img.` 子域。

        2026-08-30 实测（取证见 `docs/reference-snapshots/kemono-archive-media-host.md`）：

            kemono.cr/thumbnail/data/<path>        302
            img.kemono.cr/thumbnail/data/<path>    200 image/jpeg 24,050 B
            pawchive.pw/thumbnail/data/<path>      404
            img.pawchive.pw/thumbnail/data/<path>  200 image/gif   12,796 B

        kemono 主域只是重定向、浏览器跟随后仍能显示，所以一直没人发现；pawchive
        主域直接 404，卡片因此永远是空的（`onerror` 把 img 摘掉，看起来像「没有
        预览图」）。2026-08-27 那次记的是主域回 200——站点行为后来变了。
        """
        host = cls.HOSTS.get(provider)
        if not host or not url.startswith(f"https://{host}/"):
            return url
        return url.replace(f"https://{host}/", f"https://img.{host}/", 1)

    @classmethod
    def display_thumb_url(cls, item) -> str | None:
        if item.thumb_url:
            return cls.archive_media_host(item.provider, str(item.thumb_url))
        # 封面修复前入库的旧行：`media_url` 是图片，但 `thumb_url` 是空的。按
        # `_thumb_url` 同一条已验证规则即时推导，不改 ledger 就能补齐旧卡片。
        media = str(item.media_url or "")
        host = cls.HOSTS.get(str(item.provider or ""))
        if not host or not _IMAGE_URL_RE.search(media):
            return None
        # `/data` 前缀是 `archive_file_url` 加的，而 `/thumbnail/data` 里已经有一个。
        # 库里两种形状都有（那次修复之前拼的没有前缀），拼之前先剥掉，否则新形状的
        # 行会得到 `/thumbnail/data/data/...` 这种必然 404 的地址。
        path = urllib.parse.urlsplit(media).path
        path = path[len("/data"):] if path.startswith("/data/") else path
        return cls.archive_media_host(
            item.provider, f"https://{host}/thumbnail/data{path}")

    def _candidate(self, post: dict, service: str, user: str) -> FollowCandidate:
        post_id = str(post.get("id") or "")
        title = plain_text(post.get("title")) or "(untitled)"
        page = f"https://{self.host}/{service}/user/{user}/post/{post_id}" if post_id else None
        primary = post.get("file") if isinstance(post.get("file"), dict) else {}
        attachments = [a for a in (post.get("attachments") or []) if isinstance(a, dict)]
        paths = [primary.get("path"), *(item.get("path") for item in attachments)]
        # 交付文件优先取**非图片**的那个。作者常把 gif 预览放在 `file` 位、真正的
        # mp4 放进附件——2026-08-30 实测 pawchive `patreon/user/80149692/post/166107691`：
        # file 是 TFCLASSIC01.gif，附件里才是两个 1080p mp4。按 `file.path` 优先会把
        # 整条判成图片，两个正片直接不见，卡片也进不了「视频」那个页签。
        media = next((path for path in paths
                      if path and not str(path).lower().endswith(self._THUMBABLE)), None)
        if media is None:
            media = primary.get("path") or (attachments[0].get("path") if attachments else None)
        # 正片/压缩包仍是主要资源；封面则要从所有附件里另找第一张图片。
        # 过去把两件事绑在同一个 `media` 上，主文件只要是 mp4/zip，后面明明附了
        # jpg 也会显示「没有预览图」。
        # 封面仍从所有路径里找第一张图片：正片是 mp4 时，那张 gif/jpg 预览就是封面。
        preview = next((path for path in paths
                        if path and str(path).lower().endswith(self._THUMBABLE)), None)
        return FollowCandidate(
            provider=self.provider,
            external_id=post_id or stable_id(title, str(post.get("published"))),
            title=title,
            url=page,
            media_url=(f"https://{self.FILE_HOSTS.get(self.provider, self.host)}"
                       f"/data{media}") if media else None,
            thumb_url=self._thumb_url(preview),
            published_at=_iso_from_text(post.get("published")),
            author=None,
            summary=plain_text(post.get("substring")),
            # kemono 系的 post id 就是原平台的 post id，所以这个键和别的站点从
            # `source` 归一出来的键是同一个命名空间——跨站重复因此能精确命中。
            group_hint=f"{service}:{post_id}" if post_id else None,
            extra={"service": service, "user": user,
                   "edited": post.get("edited"),
                   "attachment_count": len(attachments)},
        )



def archive_file_url(provider: str, url: str) -> str:
    """把归档站的**原始文件** URL 修成能取到的形式。

    存量行是按旧规则拼的 `https://<主域><path>`——既少了 `/data` 前缀，主机也不对，
    所以详情里的视频一直取不到。2026-08-30 实测：

        pawchive.pw/<path>              404
        pawchive.pw/data/<path>         404   ← 主域对 /data 也不重定向
        file.pawchive.pw/data/<path>    206 video/mp4，支持 Range
        kemono.cr/data/<path>           302 → n1.kemono.cr
        coomer.st/data/<path>           302 → n4.coomer.st

    kemono/coomer 走主域让站点自己路由（nX 的编号会变，写死会过期）；
    pawchive 必须点名 `file.` 子域。缩略图仍走 `img.`，见 `archive_media_host`。
    """
    host = KemonoConnector.HOSTS.get(provider)
    if not host or not url.startswith(f"https://{host}/"):
        return url
    path = url[len(f"https://{host}") :]
    if not path.startswith("/data/"):
        path = "/data" + path
    return f"https://{KemonoConnector.FILE_HOSTS.get(provider, host)}{path}"


class Rule34VideoConnector(_BaseConnector):
    """rule34video.com 的创作者页（KVS 引擎，无公开 API，只能读 HTML）。

    `ref` 是模特/作者 slug，例如 `lazyprocrastinator`。
    """

    provider = "rule34video"
    semantics = "work"
    #: 往回翻到尽头时作者页回 404。
    HISTORY_END_STATUSES = (404,)
    _SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,80}$")
    _VIDEO_RE = re.compile(r"^https://rule34video\.com/video/(\d+)/")
    #: 详情页的署名作者通常只有 1 位；用户给出的超大合集实测有 54 位。20 以上只会
    #: 排除这种跨作者打包，不影响普通合作作品。
    MAX_COLLECTION_MODELS = 20
    DEFAULT_MAX_PROBES = 24

    def __init__(self, *, max_probes: int = DEFAULT_MAX_PROBES,
                 max_collection_models: int = MAX_COLLECTION_MODELS, **kwargs):
        super().__init__(**kwargs)
        self.max_probes = max(0, int(max_probes))
        self.max_collection_models = max(1, int(max_collection_models))

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        slug = (ref or "").strip().strip("/").lower()
        if not self._SLUG_RE.match(slug):
            raise FollowSourceError(f"rule34video 的 ref 必须是作者 slug，收到：{ref!r}")
        url = f"https://rule34video.com/models/{slug}/"
        if page:
            # KVS 的分页是异步块请求，`from` 是 1 起的两位页码（`from:02`）。
            # 2026-08-27 实测这个端点回的是同样结构的 24 条卡片。
            url = (f"{url}?mode=async&function=get_block"
                   f"&block_id=custom_list_videos_common_videos"
                   f"&sort_by=post_date&from={page + 1:02d}")
        common, response = self._request(url, ref=slug, etag=etag,
                                         last_modified=last_modified, page=page,
                                         headers={"Accept": "text/html"})
        if response is None:
            return SourceFetch(not_modified=True, **common)
        soup = BeautifulSoup(response.body, "html.parser")
        seen: set[str] = set()
        listed: list[FollowCandidate] = []
        for anchor in soup.select('a[href*="/video/"]'):
            href = (anchor.get("href") or "").strip()
            matched = self._VIDEO_RE.match(href)
            if not matched or matched.group(1) in seen:
                continue
            seen.add(matched.group(1))
            listed.append(self._candidate(anchor, href, matched.group(1)))
            if len(listed) >= self.max_items:
                break
        if not listed:
            if page:
                raise FollowHistoryEnd("没有更多历史内容")
            raise FollowSourceError(
                "rule34video 创作者页没有解析出任何作品：页面结构可能已变，"
                "或该 slug 不存在")
        candidates: list[FollowCandidate] = []
        skipped_compilations = probed = 0
        for candidate in listed:
            enriched = candidate
            if probed < self.max_probes and candidate.url:
                probed += 1
                enriched = self._probe_detail(candidate)
            model_count = int(enriched.extra.get("model_count") or 0)
            if model_count > self.max_collection_models:
                skipped_compilations += 1
                continue
            candidates.append(enriched)
        return SourceFetch(
            candidates=tuple(candidates), skipped=skipped_compilations,
            skipped_compilations=skipped_compilations, probed=probed,
            raw_body=response.body, **common,
        )

    def _candidate(self, anchor, href: str, video_id: str) -> FollowCandidate:
        title = plain_text(anchor.get("title"))
        if not title:
            node = anchor.select_one(".thumb_title") or anchor.select_one(".title")
            title = plain_text(node.get_text(" ")) if node else None
        thumb = anchor.select_one("img")
        thumb_url = None
        if thumb is not None:
            thumb_url = thumb.get("data-original") or thumb.get("data-src") or thumb.get("src")
            if isinstance(thumb_url, str) and thumb_url.startswith("data:"):
                thumb_url = None
        # `.time` 是时长，`.added` 是相对提交时间——列表页没有绝对时间。
        duration_node = anchor.select_one(".time")
        added_node = anchor.select_one(".added")
        added_text = plain_text(added_node.get_text(" ")) if added_node else None
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
                plain_text(duration_node.get_text(" ")) if duration_node else None),
            extra={"added_text": added_text,
                   "published_precision": "approximate" if added_text else "unknown",
                   "media_kind": "preview_clip"},
        )

    def _probe_detail(self, candidate: FollowCandidate) -> FollowCandidate:
        """详情页补全封面、正片、绝对日期和标签；失败时保留列表候选。

        Rule34Video 的列表页只有预览片和相对时间，详情页才同时给 JSON-LD 正片、
        内容标签、分类与署名作者。探测有每页 24 条上限，不会无界放大请求。
        """
        try:
            response = self._get(candidate.url or "", headers={"Accept": "text/html"})
            if response.status != 200:
                return candidate
            detail = self._detail(response.body)
        except (FollowSourceError, OSError, httpx.HTTPError, ValueError):
            return candidate
        if not detail:
            return candidate
        extra = {**dict(candidate.extra), **detail["extra"]}
        return replace(
            candidate,
            title=detail.get("title") or candidate.title,
            media_url=detail.get("media_url") or candidate.media_url,
            thumb_url=detail.get("thumb_url") or candidate.thumb_url,
            published_at=detail.get("published_at") or candidate.published_at,
            duration=detail.get("duration") or candidate.duration,
            extra=extra,
        )

    @staticmethod
    def _detail(body: bytes) -> dict[str, object]:
        soup = BeautifulSoup(body, "html.parser")
        video = {}
        for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                payload = json.loads(node.get_text() or "{}")
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and payload.get("@type") == "VideoObject":
                video = payload
                break
        tags = [plain_text(node.get_text(" ")) for node in soup.select(
            'a.tag_item[href*="/tags/"]')]
        categories = [plain_text(node.get_text(" ")) for node in soup.select(
            'a.video_meta_pill[href*="/categories/"]')]
        models = [plain_text(node.get_text(" ")) for node in soup.select(
            'a.video_meta_pill[href*="/models/"]')]
        tags = list(dict.fromkeys(value for value in tags if value))
        categories = list(dict.fromkeys(value for value in categories if value))
        models = list(dict.fromkeys(value for value in models if value))
        if not video and not tags and not categories and not models:
            return {}
        tag_types = {tag: "general" for tag in tags}
        for category in categories:
            tag_types[category] = (
                "metadata" if category.casefold() in {"2d", "3d"} else "copyright")
        for model in models:
            tag_types[model] = "artist"
        published = _iso_from_text(video.get("uploadDate"))
        return {
            "title": plain_text(video.get("name")),
            "media_url": (str(video.get("contentUrl"))
                          if video.get("contentUrl") else None),
            "thumb_url": (str(video.get("thumbnailUrl"))
                          if video.get("thumbnailUrl") else None),
            "published_at": published,
            "duration": _iso_duration_seconds(video.get("duration")),
            "extra": {
                **({"published_precision": "exact"} if published else {}),
                **({"media_kind": "video"} if video.get("contentUrl") else {}),
                "tags": tags,
                "categories": categories,
                "models": models,
                "model_count": len(models),
                "tag_types": tag_types,
            },
        }


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
    #: 历史行存的是 250px 的 preview。官方 dapi 的 `sample_url` 与它用同一
    #: bucket/hash；2026-08-28 对生产历史行实测推导，结果是 1920x1080。
    _PREVIEW_RE = re.compile(
        r"^https://api-cdn\.rule34\.xxx/thumbnails/(\d+)/thumbnail_"
        r"([0-9a-f]{32})\.jpg(?:[?#].*)?$", re.IGNORECASE)

    @classmethod
    def display_thumb_url(cls, item) -> str | None:
        matched = cls._PREVIEW_RE.match(str(item.thumb_url or ""))
        if matched:
            return ("https://api-cdn.rule34.xxx/images/"
                    f"{matched.group(1)}/{matched.group(2)}.jpg")
        return str(item.thumb_url or "") or None

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        tag = (ref or "").strip()
        if not self._TAG_RE.match(tag):
            raise FollowSourceError(f"rule34xxx 的 ref 必须是单个标签，收到：{ref!r}")
        if self.credential is None:
            raise CredentialError(
                "rule34xxx 需要 user_id 与 api_key；请把它们写进 "
                "peach-data/secrets/follow/rule34xxx.json")
        user_id, api_key = self.credential.require("user_id", "api_key")
        # `pid` 是 0 起的页号，页大小就是 `limit`。
        parameters = {
            "page": "dapi", "s": "post", "q": "index", "json": "1",
            "limit": str(min(self.max_items, 1000)), "tags": tag,
            "user_id": user_id, "api_key": api_key,
        }
        if page:
            parameters["pid"] = str(page)
        query = urllib.parse.urlencode(parameters)
        url = f"https://api.rule34.xxx/index.php?{query}"
        safe_url = (f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"
                    f"&tags={tag}" + (f"&pid={page}" if page else ""))
        # request_url 传脱敏版：真实 url 的查询串里带 api_key，绝不能落进证据。
        common, response = self._request(url, ref=tag, etag=etag,
                                         last_modified=last_modified, page=page,
                                         headers={"Accept": "application/json"},
                                         request_url=safe_url)
        if response is None:
            return SourceFetch(not_modified=True, **common)
        body = response.body.decode("utf-8", errors="replace").strip()
        if body.startswith('"') and "authentication" in body.lower():
            raise CredentialError("rule34xxx 拒绝了 user_id/api_key")
        # rule34.xxx 在标签没有任何帖子时返回 HTTP 200 + 空正文，不是 JSON `[]`。
        # 这只代表零命中；非空但无法解析的响应仍按结构异常报告，避免吞掉站点改版。
        payload = [] if not body else self.parse_json(response)
        posts = payload.get("post", []) if isinstance(payload, dict) else payload
        if not isinstance(posts, list):
            raise FollowSourceError("rule34xxx 的帖子列表格式不符")
        candidates = []
        for post in posts[: self.max_items]:
            if not isinstance(post, dict):
                continue
            post_id = str(post.get("id") or "")
            tag_types = self._detail_tag_types(post_id) if post_id else {}
            candidates.append(self._candidate(post, tag, tag_types=tag_types))
        candidates = tuple(candidates)
        if page and not candidates:
            raise FollowHistoryEnd("没有更多历史内容")
        return SourceFetch(candidates=candidates, raw_body=response.body, **common)

    #: 自动补全项的形状：`ria-neearts (248)`，括号里是该标签下的帖子数。
    _AUTOCOMPLETE_COUNT_RE = re.compile(r"\((\d[\d,]*)\)\s*$")

    def autocomplete(self, prefix: str) -> tuple[tuple[str, int], ...]:
        """按前缀问站方真实存在的标签，返回 `(标签, 帖子数)`。

        标签的写法是站里的既成事实，和手边的手柄常常差一个分隔符：手柄写作
        `Ria_neearts`，站上是 `ria-neearts`（2026-09-01 实测 248 帖）。逐字拿手柄
        当标签查，结果永远是零命中。

        这个接口是官方 tag 补全，公开、不需要凭据，返回值自带帖子数，正好当
        「标签下有作品」的证据。实测匹配的是**字面前缀**且大小写不敏感：`ria`
        命中 `ria-neearts`，`neea` 和 `rianeearts` 都是空——所以要试的是分隔符的
        几种写法，不是子串。
        """
        term = (prefix or "").strip()
        if not term:
            return ()
        url = ("https://api.rule34.xxx/autocomplete.php?"
               + urllib.parse.urlencode({"q": term}))
        response = self._get(url, headers={"Accept": "application/json"})
        self._check_status(response)
        payload = self.parse_json(response)
        if not isinstance(payload, list):
            raise FollowSourceError("rule34xxx 的标签补全格式不符")
        rows = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            tag = str(row.get("value") or "").strip()
            if not tag:
                continue
            matched = self._AUTOCOMPLETE_COUNT_RE.search(str(row.get("label") or ""))
            rows.append((tag, int(matched.group(1).replace(",", "")) if matched else 0))
        return tuple(rows)

    #: 拼可读标签时跳过的词：作者手柄、媒体类型和评级，留下的才是内容。
    _TITLE_TAG_STOPWORDS = frozenset({
        "video", "sound", "animated", "mp4", "webm", "3d", "hd", "60fps",
        "tagme", "highres", "absurdres",
    })
    #: 详情页取不到时的退避节奏，与外网退避规则同一套。
    _DETAIL_RETRY_DELAYS = (1.5, 4.0, 9.0)

    def _detail_tag_types(self, post_id: str) -> dict[str, str]:
        """Read rule34.xxx's own tag taxonomy from the public post page.

        The posts DAPI only returns one flat tag string.  The post page is the
        authoritative surface that marks each tag as general, artist,
        copyright, character or metadata.  If that optional enrichment is
        unavailable we keep the post, but we do not guess types from words.
        """
        url = ("https://rule34.xxx/index.php?page=post&s=view&id="
               f"{urllib.parse.quote(post_id)}")
        # 站方公布的口径是每 60 秒 60 次，而列表页一页 24 条、每条都要单独打一次
        # 详情页，被挡回来是常态。一次挡回来就返回 {}，得到的是「这条没有类型」——
        # 和「这条确实没有类型」在日志里长得一模一样。实测：回填首轮 400 条里
        # 372 条判成「没有类型」，事后逐条直取，全部 200 且 `#tag-sidebar` 正常。
        response = None
        for delay in (0.0, *self._DETAIL_RETRY_DELAYS):
            if delay:
                time.sleep(delay)
            try:
                response = self._get(url, headers={"Accept": "text/html"})
            except FollowSourceError:
                response = None
                continue
            if response.status == 200:
                break
        if response is None or response.status != 200:
            return {}
        soup = BeautifulSoup(response.body, "html.parser")
        allowed = {"general", "artist", "copyright", "character", "metadata"}
        result: dict[str, str] = {}
        for row in soup.select("#tag-sidebar li[class*='tag-type-']"):
            tag_type = next((
                value.removeprefix("tag-type-") for value in row.get("class", [])
                if value.startswith("tag-type-")
            ), "")
            if tag_type not in allowed:
                continue
            link = row.select_one("a[href*='page=post'][href*='tags=']")
            if link is None:
                continue
            query = urllib.parse.parse_qs(
                urllib.parse.urlsplit(str(link.get("href") or "")).query)
            name = html.unescape(str((query.get("tags") or [""])[0])).strip()
            if name:
                result[name] = tag_type
        return result

    def _candidate(self, post: dict, tag: str, *,
                   tag_types: Mapping[str, str] | None = None) -> FollowCandidate:
        post_id = str(post.get("id") or "")
        # dapi 返回的标签是 HTML 转义形态（实测 `miqo&#039;te`）。实体不反转义
        # 就进 metadata，读取层再转一次就成了双重转义，用户看到的就是 `&#039;`
        # 字面量，同一个标签还会和反转义后的写法分裂成两个身份。
        tags = html.unescape(str(post.get("tags") or ""))
        image = str(post.get("image") or "")
        stem = re.sub(r"\.[a-z0-9]{2,5}$", "", image, flags=re.IGNORECASE)
        # booru 帖子没有标题。实测 rule34.xxx 的 `image` 全是 32 位十六进制哈希，
        # 拿它当标题既不可读，又会让每条帖子各自成组。哈希就退回标签拼一个可读标签，
        # 并声明这不是名字——标签相似的两个作品不能因此被并成一个。
        opaque = _is_opaque_filename(stem)
        if stem and not opaque:
            title, title_from, title_is_name = (
                plain_text(stem.replace("_", " ")) or f"post {post_id}", "image", True)
        else:
            title = self._tag_label(tags, tag) or f"post {post_id}"
            title_from, title_is_name = "tags", False
        # 出处比站内父帖强得多：实测 15 条 parent_id 全是 0，而 13 条有 source，
        # 其中 4 条指向同一个 fanbox 帖——那才是真正的同组信号，而且跨站可比。
        # source 是站点转义过的 URL（`&amp;` 代替 `&`），反转义后才是真实地址；
        # 归组键只取 path，query 里的实体不影响既有分组的稳定性。
        source = post.get("source")
        source = html.unescape(str(source)) if source else None
        parent = post.get("parent_id")
        hint = origin_group_key(str(source) if source else None)
        if hint is None:
            anchor = parent if parent not in (None, 0, "0", "") else post_id
            hint = f"{self.provider}:post:{anchor}" if anchor else None
        return FollowCandidate(
            provider=self.provider,
            external_id=post_id or stable_id(image, tags),
            title=title,
            url=f"https://rule34.xxx/index.php?page=post&s=view&id={post_id}"
                if post_id else None,
            media_url=str(post.get("file_url")) if post.get("file_url") else None,
            # dapi 的 preview_url 只有约 250px；sample_url 对视频是同帧 JPEG，
            # 对图片则是站点选定的样图。gallery-dl 的 booru 抽取器也把这三层
            # 作为可配置回退链，不能把最小 preview 固定成 Peach 封面。
            thumb_url=str(post.get("sample_url") or post.get("preview_url") or "") or None,
            published_at=_iso_from_epoch(post.get("change")),
            group_hint=hint,
            title_is_name=title_is_name,
            extra={"tag": tag, "tags": tags, "score": post.get("score"),
                   "source": source, "title_from": title_from,
                   "preview_url": post.get("preview_url"),
                   **({"tag_types": dict(tag_types)} if tag_types else {})},
        )

    @classmethod
    def _tag_label(cls, tags: str, subject: str) -> str:
        """用标签拼一个可读标签。只作展示，不参与按标题分组。"""
        skip = cls._TITLE_TAG_STOPWORDS | {subject.strip().lower()}
        words = [word.replace("_", " ") for word in tags.split()
                 if word.lower() not in skip and not word.startswith("rating:")]
        return " · ".join(words[:5])


class Rule34PahealConnector(_BaseConnector):
    """rule34.paheal.net 标签页；详情页补齐原始出处用于精确跨站去重。"""

    provider = "rule34paheal"
    semantics = "work"
    #: 往回翻到尽头时标签页回 404。
    HISTORY_END_STATUSES = (404,)
    _TAG_RE = re.compile(r"^[^/?#]{1,100}$")
    _DURATION_RE = re.compile(r"\b(\d+(?:\.\d+)?)s\b", re.IGNORECASE)
    _TITLE_STOPWORDS = frozenset({"animated", "blender", "video", "sound", "mp4", "webm"})

    def __init__(self, *, max_items: int = 24, **kwargs):
        super().__init__(max_items=max_items, **kwargs)

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        tag = str(ref or "").strip()
        if not self._TAG_RE.fullmatch(tag):
            raise FollowSourceError(f"rule34.paheal 的 ref 必须是单个标签，收到：{ref!r}")
        page_number = page + 1
        encoded = urllib.parse.quote(tag, safe="()_")
        url = f"https://rule34.paheal.net/post/list/{encoded}/{page_number}"
        common, response = self._request(url, ref=tag, etag=etag,
                                         last_modified=last_modified, page=page,
                                         headers={"Accept": "text/html"})
        if response is None:
            return SourceFetch(not_modified=True, **common)
        soup = BeautifulSoup(response.body, "html.parser")
        candidates = []
        for thumb in soup.select(".shm-image-list .shm-thumb[data-post-id]")[:self.max_items]:
            post_id = str(thumb.get("data-post-id") or "")
            if not post_id.isdigit():
                continue
            tags = str(thumb.get("data-tags") or "")
            extension = str(thumb.get("data-ext") or "").casefold()
            link = thumb.select_one("a.shm-thumb-link[href]")
            file_link = thumb.select_one("a[href*='paheal-cdn.net'], a[href*='r34i.paheal']")
            image = thumb.select_one("img[src]")
            detail = self._detail(post_id)
            tag_values = detail.get("tags") or tags.split()
            title = self._tag_label(tag_values, tag) or f"Paheal 帖子 {post_id}"
            media_url = str(detail.get("media_url") or
                            (file_link.get("href") if file_link else "")) or None
            candidates.append(FollowCandidate(
                provider=self.provider,
                external_id=post_id,
                title=title,
                url=urllib.parse.urljoin("https://rule34.paheal.net",
                                         str(link.get("href") if link else f"/post/view/{post_id}")),
                media_url=media_url,
                thumb_url=str(detail.get("thumb_url") or
                              (image.get("src") if image else "")) or None,
                published_at=detail.get("published_at"),
                duration=detail.get("duration"),
                author=detail.get("author"),
                group_hint=origin_group_key(detail.get("source")) or
                           f"{self.provider}:post:{post_id}",
                title_is_name=False,
                extra={"tag": tag, "tags": " ".join(tag_values),
                       "source": detail.get("source"), "title_from": "tags",
                       "media_kind": "video" if extension in {"mp4", "webm", "mov"}
                                     else "image",
                       "tag_types": {value: "general" for value in tag_values}},
            ))
        if not candidates:
            if page:
                raise FollowHistoryEnd("没有更多历史内容")
            raise FollowSourceError("rule34.paheal 标签页没有解析出任何作品")
        return SourceFetch(candidates=tuple(candidates), probed=len(candidates),
                           raw_body=response.body, **common)

    #: 详情页取不到就重试的状态码。列表页一页 24 条，每条都要单独打一次详情页，
    #: 上游按频率挡回来是常态；一次挡回来就当「这条没有上传时间」，得到的是一条
    #: 看似完整、时间却是抓取时刻的记录——比报错更难发现。
    _DETAIL_RETRY_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
    #: 与外网退避规则同一套节奏。
    _DETAIL_RETRY_DELAYS = (1.0, 2.0, 4.0)

    def _detail(self, post_id: str) -> dict[str, object]:
        url = f"https://rule34.paheal.net/post/view/{post_id}"
        response = self._get(url, headers={"Accept": "text/html"})
        for delay in self._DETAIL_RETRY_DELAYS:
            if response.status not in self._DETAIL_RETRY_STATUSES:
                break
            time.sleep(delay)
            response = self._get(url, headers={"Accept": "text/html"})
        if response.status != 200:
            return {}
        soup = BeautifulSoup(response.body, "html.parser")
        video = soup.select_one("video#main_image")
        source_node = soup.select_one("tr[data-row='Source Link'] td a[href]")
        time_node = soup.select_one("tr[data-row='Uploader'] time[datetime]")
        author_node = soup.select_one("tr[data-row='Uploader'] a.username")
        info_node = soup.select_one("tr[data-row='Info'] td")
        tags = [plain_text(node.get_text(" ")) for node in
                soup.select("tr[data-row='Tags'] a.tag")]
        media = (video.select_one("source[src]") if video is not None else
                 soup.select_one("img#main_image[src]"))
        duration_match = self._DURATION_RE.search(info_node.get_text(" ") if info_node else "")
        return {
            "media_url": str(media.get("src")) if media is not None and media.get("src") else None,
            "thumb_url": (str(video.get("poster")) if video is not None and video.get("poster")
                          else None),
            "published_at": _iso_from_text(time_node.get("datetime") if time_node else None),
            "duration": float(duration_match.group(1)) if duration_match else None,
            "author": plain_text(author_node.get_text(" ") if author_node else ""),
            "source": str(source_node.get("href")) if source_node is not None else None,
            "tags": [tag for tag in tags if tag],
        }

    @classmethod
    def _tag_label(cls, tags: list[str], subject: str) -> str:
        skip = cls._TITLE_STOPWORDS | {subject.casefold()}
        values = [tag.replace("_", " ") for tag in tags if tag.casefold() not in skip]
        return " · ".join(values[:5])


class F95ZoneConnector(_BaseConnector):
    """f95zone.to 的线程追更。

    主贴的版本号更新常常滞后于回复——真正的新链接先出现在楼下——所以这里读的是
    线程的 `/latest` 页而不是主贴；`latest_data.php` 另给线程当前的 `version` 与时间戳。

    **发现不需要登录，解析 masked 链接需要。** 2026-08-28 实测 `/latest` 页在无
    cookie 下完整返回回复正文与 `/masked/...`；配置 cookie 后向同一路径 POST
    `xhr=1&download=1` 才返回真实网盘 URL。cookie 只发回 f95zone.to，绝不跟着
    真实链接送到 Gofile / Pixeldrain。

    `ref` 是线程 id，例如 `50685`。
    """

    provider = "f95zone"
    semantics = "release"
    _THREAD_RE = re.compile(r"^\d{1,12}$")
    #: latest_data.php 按分类分库，线程不在哪个分类里事先不知道，只能逐个试。
    CATEGORIES = ("games", "animations", "comics", "assets", "mods")
    _MASKED_PATH_RE = re.compile(r"^/masked/", re.IGNORECASE)
    _ATTACHMENT_PATH_RE = re.compile(r"^/attachments/\d+/?$", re.IGNORECASE)
    _INLINE_IMAGE_RE = re.compile(
        r"\.(?:avif|bmp|gif|jpe?g|png|webp)(?:$|[?#])", re.IGNORECASE)

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        thread = (ref or "").strip()
        if not self._THREAD_RE.match(thread):
            raise FollowSourceError(f"f95zone 的 ref 必须是线程 id，收到：{ref!r}")
        if page:
            # `/latest` 是站点自己渲染的「最近回复」聚合视图，没有 page-N 变体，
            # 这个连接器因此只有一页可读。以前这里把 `page` 静默丢掉，往回翻页会
            # 重新抓同一页、报成一次成功的检查，表现就是「点了没反应」。报到底
            # 比假装成功好：调用方据此显示历史已尽。
            raise FollowHistoryEnd("没有更多历史内容")
        url = f"https://f95zone.to/threads/{thread}/latest"
        headers = {"Accept": "text/html"}
        if self.credential and self.credential.values.get("cookie"):
            headers["Cookie"] = self.credential.values["cookie"]
        common, response = self._request(url, ref=thread, etag=etag,
                                         last_modified=last_modified, headers=headers)
        if response is None:
            return SourceFetch(not_modified=True, **common)
        soup = BeautifulSoup(response.body, "html.parser")
        title = self._thread_title(soup)
        candidates, parsed, skipped = self._replies(
            soup, thread, title or f"thread {thread}")
        if not parsed:
            raise FollowSourceError(
                "f95zone 线程页没有解析出任何回复：可能需要登录，或页面结构已变")
        enriched = []
        for candidate in candidates:
            links = [str(value) for value in candidate.extra.get("links", [])]
            image_items = f95_attachment_media_items(candidate.extra)
            media_items = tuple(image_items) + self._gofile_media(links)
            enriched.append(replace(
                candidate,
                extra={**dict(candidate.extra), "media_items": media_items,
                       "gofile_video_count": sum(
                           item.get("media_kind") == "video" for item in media_items)},
            ))
        return SourceFetch(candidates=tuple(enriched), skipped=skipped,
                           raw_body=response.body, **common)

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
        return plain_text(heading.get_text(" "))

    def _replies(self, soup, thread: str, thread_title: str):
        posts = soup.select('article[data-content^="post-"]')
        candidates: list[FollowCandidate] = []
        parsed = 0
        skipped = 0
        for article in posts[-self.max_items:]:
            content = str(article.get("data-content") or "")
            post_id = content.removeprefix("post-")
            if not post_id.isdigit():
                continue
            parsed += 1
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
            media_links, needs_credential = self._media_links(links)
            attachment_urls = self._attachment_urls(body)
            # F95 会把正文里粘贴的 GIF / meme 也存到 attachments.f95zone.to。
            # 它们只是讨论插图，不是作者交付的资源；单凭一张内嵌图片不能让楼层
            # 进入追更。非图片附件仍保留，带文件站链接的楼层也保留全部预览图。
            downloadable_attachments = [
                url for url in attachment_urls if not self._INLINE_IMAGE_RE.search(url)
            ]
            if not media_links and not downloadable_attachments:
                skipped += 1
                continue
            direct_attachment = next((url for url in attachment_urls
                                      if urllib.parse.urlsplit(url).hostname
                                      == "attachments.f95zone.to"), None)
            candidates.append(FollowCandidate(
                provider=self.provider,
                external_id=post_id,
                title=thread_title,
                url=f"https://f95zone.to/threads/{thread}/post-{post_id}",
                media_url=media_links[0] if media_links else None,
                thumb_url=direct_attachment,
                published_at=_iso_from_text(time_node.get("datetime"))
                if time_node is not None else None,
                author=plain_text(str(article.get("data-author") or "")) or None,
                summary=plain_text(body.get_text(" ")) if body else None,
                extra={"thread_id": thread, "link_count": len(media_links),
                       "links": media_links[:8],
                       "attachment_count": len(attachment_urls),
                       "attachments": attachment_urls[:8],
                       "media_needs_credential": needs_credential},
            ))
        return tuple(candidates), parsed, skipped

    @classmethod
    def _attachment_urls(cls, body) -> list[str]:
        """只认回复正文内的 F95 附件，避免把头像或签名图算成发布内容。"""
        if body is None:
            return []
        direct: list[str] = []
        pages: list[str] = []
        for node in body.select("[data-src], a[href]"):
            for attribute in ("data-src", "href"):
                value = str(node.get(attribute) or "").strip()
                if not value.startswith("https://"):
                    continue
                try:
                    parsed = urllib.parse.urlsplit(value)
                except ValueError:
                    continue
                host = (parsed.hostname or "").casefold()
                if host == "attachments.f95zone.to":
                    if value not in direct:
                        direct.append(value)
                elif (host == "f95zone.to" or host.endswith(".f95zone.to")) \
                        and cls._ATTACHMENT_PATH_RE.match(parsed.path):
                    if value not in pages:
                        pages.append(value)
        # 同一附件通常同时有直链和详情页；优先保留可直接预览的直链，避免重复计数。
        return direct or pages

    def _media_links(self, links: list[str]) -> tuple[list[str], bool]:
        """只保留文件分发链接，并用本机 F95 会话解开 masked URL。"""
        cookie = str(self.credential.values.get("cookie") or "") \
            if self.credential else ""
        media: list[str] = []
        needs_credential = False
        for link in links:
            if self._is_masked(link):
                target = self._resolve_masked(link, cookie) if cookie else None
                if target is None:
                    needs_credential = True
                    media.append(link)
                elif target not in media:
                    media.append(target)
                continue
            if _is_resource_url(link) and link not in media:
                media.append(link)
        return media, needs_credential

    @classmethod
    def _is_masked(cls, url: str) -> bool:
        try:
            parsed = urllib.parse.urlsplit(url)
        except ValueError:
            return False
        host = (parsed.hostname or "").casefold()
        return (parsed.scheme == "https"
                and (host == "f95zone.to" or host.endswith(".f95zone.to"))
                and bool(cls._MASKED_PATH_RE.match(parsed.path)))

    def _resolve_masked(self, url: str, cookie: str) -> str | None:
        # masked.js 使用同路径 XHR POST。失败只让这一条维持「需会话」，不能让整个
        # 线程的公开发现一起失败。
        try:
            response = self._post(
                url,
                b"xhr=1&download=1",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Cookie": cookie,
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            if response.status != 200:
                return None
            payload = self.parse_json(response)
        except FollowSourceError:
            return None
        if not isinstance(payload, dict):
            return None
        target = str(payload.get("msg") or "")
        return target if payload.get("status") == "ok" and _is_resource_url(target) else None

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
        payload = self.parse_json(response)
        rows = ((payload or {}).get("msg") or {}).get("data") or []
        return tuple(row for row in rows if isinstance(row, dict))

    #: 搜索结果里线程链接的形状：`/threads/<slug>.<id>/`，后面可能还跟着帖子锚点。
    _SEARCH_THREAD_RE = re.compile(r"^/threads/(?:[^/]*\.)?(\d+)/")
    _XF_TOKEN_RE = re.compile(rb'name="_xfToken" value="([^"]+)"')

    def search_threads(self, query: str, *, title_only: bool = True) -> tuple[dict, ...]:
        """用站内搜索按标题找线程。

        `latest_data.php` 只索引 Latest Updates（游戏、动画、漫画、资产、mod）。
        艺术家的 Collection 帖发在普通版块，那份索引里根本没有：2026-09-01 实测
        `Ria_neearts` 在五个分类全为空，站内搜索一次就命中
        `/threads/ria-collection-2026-08-03-ria_neearts.146348/`。

        **站内搜索必须登录**，无 cookie 时 `/search/` 直接回 403。搜索表单里的
        `_xfToken` 和会话绑定，所以每次都要先取一遍，不能缓存成常量。
        """
        cookie = self.credential.values.get("cookie") if self.credential else None
        if not cookie:
            raise CredentialError(
                "f95zone 站内搜索需要登录 cookie；请把它写进 "
                "peach-data/secrets/follow/f95zone.json")
        headers = {"Accept": "text/html", "Cookie": cookie}
        form = self._get("https://f95zone.to/search/", headers=headers)
        self._check_status(form)
        matched = self._XF_TOKEN_RE.search(form.body)
        if matched is None:
            raise FollowSourceError("f95zone 搜索表单里没有 _xfToken：cookie 可能已失效")
        body = urllib.parse.urlencode({
            "keywords": query, "c[title_only]": "1" if title_only else "0",
            "order": "relevance", "search_type": "post",
            "_xfToken": matched.group(1).decode("utf-8", errors="replace"),
        }).encode()
        response = self._post(
            "https://f95zone.to/search/search", body,
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded",
                     "Referer": "https://f95zone.to/search/"})
        self._check_status(response)
        soup = BeautifulSoup(response.body, "html.parser")
        rows, seen = [], set()
        for link in soup.select("h3.contentRow-title a[href]"):
            found = self._SEARCH_THREAD_RE.match(link.get("href") or "")
            if found is None or found.group(1) in seen:
                continue
            seen.add(found.group(1))
            # 标题前挂着 `Collection`、`Pinup` 这类前缀标签，和 `_thread_title` 一样摘掉。
            for label in link.select(".label, .labelLink, .label-append"):
                label.extract()
            # 命中的词被 `<em class="textHighlight">` 包着，按分隔符取文本会把
            # `[Ria_neearts]` 拆成 `[ Ria_neearts ]`——标题要的是原样。
            rows.append({"thread_id": found.group(1),
                         "title": plain_text(link.get_text(""))})
        return tuple(rows)


class FanboxConnector(_BaseConnector):
    """pixivFANBOX 官方公开帖子列表。

    只保留 `feeRequired=0` 且没有受限的帖子；付费标题可以被公开接口看见，
    但这条来源的用途是跟踪作者直接公开分发的内容，不能把付费预告混进来。
    """

    provider = "fanbox"
    semantics = "work"
    _CREATOR_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

    @classmethod
    def profile_handle(cls, ref: str) -> str:
        return str(ref or "").strip()

    _IMPERSONATION = "firefox147"

    def __init__(self, *, detail_transport: HttpTransport | None = None, **kwargs):
        injected_transport = kwargs.get("transport")
        super().__init__(**kwargs)
        # 测试或调用方显式注入 transport 时保持单一边界；正式运行只把容易被
        # TLS/HTTP2 指纹拦截的 post.info 切到浏览器传输，公开列表仍复用 HTTPX。
        self.detail_transport = (
            detail_transport or injected_transport
            or CurlCffiTransport(impersonate=self._IMPERSONATION)
        )

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        headers.update({
            "Accept": "application/json",
            "Origin": "https://www.fanbox.cc",
            "Referer": "https://www.fanbox.cc/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) "
                "Gecko/20100101 Firefox/147.0"
            ),
        })
        if self.credential and self.credential.values.get("cookie"):
            headers["Cookie"] = self.credential.values["cookie"]
        return headers

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        creator = str(ref or "").strip()
        if not self._CREATOR_RE.fullmatch(creator):
            raise FollowSourceError(f"fanbox 的 ref 必须是创作者 id，收到：{ref!r}")
        if page:
            raise FollowSourceError("fanbox 官方来源暂不支持向前翻页")
        # 2026-08-27 实测公开接口单页为 10 条；不要把本地通用上限 100 原样塞给站点。
        query = urllib.parse.urlencode({"creatorId": creator,
                                        "limit": min(self.max_items, 10)})
        url = f"https://api.fanbox.cc/post.listCreator?{query}"
        common, response = self._request(url, ref=creator, etag=etag,
                                         last_modified=last_modified)
        if response is None:
            return SourceFetch(not_modified=True, **common)
        payload = self.parse_json(response)
        posts = ((payload or {}).get("body") or {}).get("posts")
        if not isinstance(posts, list):
            raise FollowSourceError("fanbox 返回的帖子列表格式不符")
        candidates, skipped, probed = [], 0, 0
        for post in posts[:self.max_items]:
            if not isinstance(post, dict) or not str(post.get("id") or "").isdigit():
                continue
            if post.get("isRestricted") or int(post.get("feeRequired") or 0) > 0:
                skipped += 1
                continue
            post_id = str(post["id"])
            cover = post.get("cover") if isinstance(post.get("cover"), dict) else {}
            user = post.get("user") if isinstance(post.get("user"), dict) else {}
            try:
                detail = self._post_detail(post_id, creator)
            except FollowSourceError as error:
                # FANBOX 会把单篇 post.info 临时换成 Cloudflare 验证页。
                # 列表本身仍是可信的公开更新；保留卡片并明确标记媒体未取得，
                # 不能让一篇详情失败拖垮整个作者来源。
                detail = {"summary": "", "links": [], "media_items": (),
                          "post_type": None, "image_count": 0,
                          "video_count": 0, "file_count": 0,
                          "error": str(error)}
            probed += 1
            links = detail["links"]
            direct_media = detail["media_items"]
            gofile_media = self._gofile_media(
                links, labels=folder_labels(str(detail.get("summary") or "")))
            media_items = tuple(direct_media) + gofile_media
            candidates.append(FollowCandidate(
                provider=self.provider,
                external_id=post_id,
                title=plain_text(str(post.get("title") or "")) or f"FANBOX 帖子 {post_id}",
                url=f"https://{creator}.fanbox.cc/posts/{post_id}",
                thumb_url=(str(direct_media[0].get("thumb_url")
                               or direct_media[0].get("url"))
                           if direct_media else
                           str(cover.get("url")) if cover.get("url") else None),
                published_at=_iso_from_text(post.get("publishedDatetime")),
                author=plain_text(str(user.get("name") or "")),
                summary=detail["summary"] or plain_text(str(post.get("excerpt") or "")),
                group_hint=f"fanbox:{post_id}",
                extra={"fee_required": 0, "official": True, "links": links,
                       "media_items": media_items,
                       "media_error": detail.get("error"),
                       "post_type": detail.get("post_type"),
                       "image_count": detail.get("image_count", 0),
                       "video_count": detail.get("video_count", 0),
                       "file_count": detail.get("file_count", 0),
                       "gofile_video_count": sum(
                           item.get("media_kind") == "video" for item in gofile_media)},
            ))
        return SourceFetch(candidates=tuple(candidates), skipped=skipped,
                           probed=probed, raw_body=response.body, **common)

    def _post_detail(self, post_id: str, creator: str) -> dict[str, object]:
        """公开详情补全正文外链和按正文顺序排列的多图。"""
        url = "https://api.fanbox.cc/post.info?" + urllib.parse.urlencode({"postId": post_id})
        headers = self._headers()
        headers["Referer"] = f"https://www.fanbox.cc/@{creator}/posts/{post_id}"
        try:
            response = self.detail_transport(
                HttpRequest("GET", url, headers), self.timeout, self.max_bytes)
        except (OSError, httpx.HTTPError) as exc:
            raise FollowSourceError("fanbox 请求失败") from exc
        if len(response.body) > self.max_bytes:
            raise FollowSourceError("fanbox 响应超出大小上限")
        self._check_status(response)
        payload = self.parse_json(response)
        if isinstance(payload, dict) and payload.get("error"):
            raise FollowSourceError(f"fanbox 帖子详情返回错误：{payload['error']}")
        body = (payload or {}).get("body") if isinstance(payload, dict) else None
        post = body.get("post") if isinstance(body, dict) else None
        if not isinstance(post, dict):
            raise FollowSourceError("fanbox 帖子详情格式不符")
        if post.get("isRestricted") or int(post.get("feeRequired") or 0) > 0:
            raise FollowSourceError("fanbox 帖子详情不是公开免费正文")
        try:
            content = normalize_fanbox_post(post)
        except FanboxContentError as exc:
            raise FollowSourceError(str(exc)) from exc
        links = resource_links("\n".join((content.summary, *content.links)))
        return {
            "summary": plain_text(content.summary),
            "links": links,
            "media_items": content.media_items,
            "post_type": content.post_type,
            "image_count": content.image_count,
            "video_count": content.video_count,
            "file_count": content.file_count,
        }


def _visible_post_image(node) -> str | None:
    image = node.select_one("img[src]") if node is not None else None
    return str(image.get("src")) if image is not None and image.get("src") else None


class SubscribeStarConnector(_BaseConnector):
    """SubscribeStar 的公开创作者页；不登录，也不穿过付费墙。"""

    provider = "subscribestar"
    semantics = "work"
    HOSTS = frozenset({"subscribestar.adult", "subscribestar.com"})
    _SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

    @classmethod
    def profile_handle(cls, ref: str) -> str:
        # ref 带着站点主机名（`subscribestar.adult/initiala`），手柄只是最后那截。
        return str(ref or "").strip().rsplit("/", 1)[-1]

    @classmethod
    def _split_ref(cls, ref: str) -> tuple[str, str]:
        host, _, slug = str(ref or "").strip().partition("/")
        if host not in cls.HOSTS or not cls._SLUG_RE.fullmatch(slug):
            raise FollowSourceError(
                "subscribestar 的 ref 必须形如 subscribestar.adult/creator")
        return host, slug

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        host, slug = self._split_ref(ref)
        if page:
            raise FollowSourceError("SubscribeStar 官方来源暂不支持向前翻页")
        url = f"https://{host}/{slug}"
        common, response = self._request(url, ref=ref, etag=etag,
                                         last_modified=last_modified,
                                         headers={"Accept": "text/html"})
        if response is None:
            return SourceFetch(not_modified=True, **common)
        try:
            soup = BeautifulSoup(response.body.decode("utf-8"), "html.parser")
        except UnicodeDecodeError as exc:
            raise FollowSourceError("subscribestar 返回的页面不是 UTF-8") from exc
        candidates = []
        for post in soup.select("div.post[data-id]")[:self.max_items]:
            post_id = str(post.get("data-id") or "")
            if not post_id.isdigit():
                continue
            title_node = post.select_one(".post-title h2")
            date_node = post.select_one(".post-date a[href]")
            author_node = post.select_one(".post-user")
            title = plain_text(title_node.get_text(" ") if title_node else "")
            published = _iso_from_text(date_node.get_text(" ") if date_node else "")
            if published is None and date_node is not None:
                try:
                    parsed = datetime.strptime(
                        date_node.get_text(" ").strip(), "%b %d, %Y %I:%M %p")
                    published = _iso_utc(parsed)
                except ValueError:
                    pass
            candidates.append(FollowCandidate(
                provider=self.provider,
                external_id=post_id,
                title=title or f"SubscribeStar 帖子 {post_id}",
                url=f"https://{host}/posts/{post_id}",
                thumb_url=_visible_post_image(post.select_one(".post-uploads")),
                published_at=published,
                author=plain_text(author_node.get_text(" ") if author_node else ""),
                summary=plain_text(
                    post.select_one(".post-content").get_text(" ")
                    if post.select_one(".post-content") else ""),
                group_hint=f"subscribestar:{post_id}",
                extra={"official": True, "published_precision": "approximate"},
            ))
        return SourceFetch(candidates=tuple(candidates), raw_body=response.body, **common)


class PatreonConnector(_BaseConnector):
    """Patreon 公开创作者页。

    Patreon 的正式 posts API 要创作者 OAuth scope，不能用于任意作者；这里仅读取官网
    已经服务端渲染给公开访客的帖子卡片，不碰登录态或私有 API。
    """

    provider = "patreon"
    semantics = "work"
    _VANITY_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
    _POST_RE = re.compile(r"/posts/(?:[^/?#]*-)?(\d{4,})(?:[/?#]|$)")

    @classmethod
    def profile_handle(cls, ref: str) -> str:
        value = str(ref or "").strip().strip("/")
        if value.startswith("user/") or value.isdigit():
            # 数字用户 id 页没有短名，`user/12345` 不是作者的名字。
            return ""
        return value.rsplit("/", 1)[-1]

    def _url(self, ref: str) -> str:
        value = str(ref or "").strip()
        if value.startswith("user/") and value[5:].isdigit():
            return f"https://www.patreon.com/user?u={value[5:]}"
        if not self._VANITY_RE.fullmatch(value):
            raise FollowSourceError(f"patreon 的 ref 必须是创作者短名，收到：{ref!r}")
        return f"https://www.patreon.com/cw/{value}"

    def fetch(self, ref: str, *, etag: str | None = None,
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        if page:
            raise FollowSourceError("Patreon 官方来源暂不支持向前翻页")
        url = self._url(ref)
        common, response = self._request(url, ref=ref, etag=etag,
                                         last_modified=last_modified,
                                         headers={"Accept": "text/html"})
        if response is None:
            return SourceFetch(not_modified=True, **common)
        try:
            soup = BeautifulSoup(response.body.decode("utf-8"), "html.parser")
        except UnicodeDecodeError as exc:
            raise FollowSourceError("patreon 返回的页面不是 UTF-8") from exc
        candidates, seen = [], set()
        for anchor in soup.select("a[href*='/posts/']"):
            href = str(anchor.get("href") or "")
            matched = self._POST_RE.search(urllib.parse.urlsplit(href).path)
            if not matched or matched.group(1) in seen:
                continue
            post_id = matched.group(1)
            seen.add(post_id)
            node = anchor
            for _ in range(8):
                if node is None or node.select_one("h3") is not None:
                    break
                node = node.parent
            title_node = node.select_one("h3") if node is not None else None
            title = plain_text(title_node.get_text(" ") if title_node else "")
            if not title:
                slug = urllib.parse.urlsplit(href).path.rsplit("/", 1)[-1]
                title = _slug_label(re.sub(rf"-{post_id}$", "", slug))
            text = plain_text(node.get_text(" ") if node is not None else "") or ""
            relative = _RELATIVE_RE.search(text)
            candidates.append(FollowCandidate(
                provider=self.provider,
                external_id=post_id,
                title=title or f"Patreon 帖子 {post_id}",
                url=urllib.parse.urljoin("https://www.patreon.com", href),
                thumb_url=_visible_post_image(node),
                published_at=_iso_from_relative(relative.group(0)) if relative else None,
                group_hint=f"patreon:{post_id}",
                extra={"official": True, "public_page": True,
                       "published_precision": "approximate"},
            ))
            if len(candidates) >= self.max_items:
                break
        return SourceFetch(candidates=tuple(candidates), raw_body=response.body, **common)


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
              last_modified: str | None = None, page: int = 0) -> SourceFetch:
        raise FollowSourceError(self.blocked_reason)


@dataclass(frozen=True)
class ParsedSource:
    """从一条粘进来的链接认出来的订阅。"""

    provider: str
    ref: str
    url: str
    label: str
    semantics: str

    @property
    def evidence(self) -> str:
        return "链接直接指明"


#: 每个来源的条目语义：`work` 是每条一个独立作品，`release` 是同一作品的历次发布。
_SEMANTICS = follow_providers.semantics()

_KEMONO_HOSTS = {"kemono.cr": "kemono", "coomer.st": "coomer", "pawchive.pw": "pawchive"}
_KEMONO_PATH_RE = re.compile(r"^/([a-z0-9_\-]{1,32})/user/([A-Za-z0-9_\-.]{1,64})")
_R34V_PATH_RE = re.compile(r"^/models/([a-z0-9][a-z0-9_\-]{0,80})")
_THREAD_PATH_RE = re.compile(r"^/threads/(?:[^/]*?\.)?(\d{1,12})")
_DIRECT_CREATOR_RE = re.compile(r"^/([A-Za-z0-9_-]{1,80})(?:/|$)")


def canonical_source_ref(provider: str, ref: str) -> str:
    """Return the provider's stable source identity.

    Most provider ids are case-sensitive opaque values.  rule34.xxx tags are not:
    the API returns the same feed for ``LazyProcrastinator`` and
    ``lazyprocrastinator``.  Keeping the pasted spelling in the unique key therefore
    creates duplicate subscriptions when the same author is added in two batches.
    """
    value = str(ref or "").strip()
    return value.casefold() if provider in {"rule34xxx", "rule34paheal"} else value


#: 线程 slug 里从这个 token 起就不是作品名了：f95 的惯例是
#: `<作品名>-<发布日期>-<作者手柄>`，日期之后全是元数据。
_SLUG_TAIL_RE = re.compile(r"^(?:19|20)\d{2}$|^v?\d+(?:\.\d+)+[a-z]?$")


def _slug_label(slug: str) -> str:
    words = [word for word in re.split(r"[-_]+", slug) if word]
    kept: list[str] = []
    for word in words:
        if kept and _SLUG_TAIL_RE.match(word):
            break
        kept.append(word)
    return " ".join(kept).strip() or re.sub(r"[-_]+", " ", slug).strip() or slug


def parse_source_url(raw_url: str) -> ParsedSource:
    """把一条来源链接认成可登记的订阅。

    只做纯解析，不联网。认不出来就抛 `FollowSourceError` 并说清楚支持哪些形状——
    与其静默登记一个永远抓不到东西的来源，不如当场说不认识。
    """
    text = (raw_url or "").strip()
    if not text:
        raise FollowSourceError("请先粘贴一条来源链接")
    if "://" not in text:
        text = "https://" + text
    try:
        parsed = urllib.parse.urlsplit(text)
    except ValueError as exc:
        raise FollowSourceError("这不是一条合法链接") from exc
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FollowSourceError("只接受 http(s) 链接")
    if parsed.username is not None or parsed.password is not None:
        raise FollowSourceError("链接里不能带账号密码")
    host = parsed.hostname.lower()
    bare = host[4:] if host.startswith("www.") else host
    path = parsed.path or "/"

    provider = _KEMONO_HOSTS.get(bare)
    if provider:
        matched = _KEMONO_PATH_RE.match(path)
        if not matched:
            raise FollowSourceError(
                f"{bare} 的链接要指向某个创作者，形如 "
                f"https://{bare}/fanbox/user/30917150")
        service, user = matched.group(1), matched.group(2)
        return ParsedSource(provider, f"{service}/{user}",
                            f"https://{bare}/{service}/user/{user}",
                            f"{user} · {service}", "work")

    if bare == "fanbox.cc" or bare.endswith(".fanbox.cc"):
        if bare.endswith(".fanbox.cc") and bare != "www.fanbox.cc":
            creator = bare.removesuffix(".fanbox.cc")
        else:
            matched = re.match(r"^/@([A-Za-z0-9_-]{1,64})(?:/|$)", path)
            creator = matched.group(1) if matched else ""
        if not creator:
            raise FollowSourceError(
                "FANBOX 的链接要指向创作者主页，形如 https://creator.fanbox.cc/")
        return ParsedSource("fanbox", creator, f"https://{creator}.fanbox.cc/",
                            creator, "work")

    if bare in SubscribeStarConnector.HOSTS:
        matched = _DIRECT_CREATOR_RE.match(path)
        if not matched or matched.group(1) in {"posts", "search", "login", "signup"}:
            raise FollowSourceError(
                "SubscribeStar 的链接要指向创作者主页，形如 "
                "https://subscribestar.adult/creator")
        slug = matched.group(1)
        return ParsedSource("subscribestar", f"{bare}/{slug}",
                            f"https://{bare}/{slug}", slug, "work")

    if bare == "patreon.com":
        user_id = urllib.parse.parse_qs(parsed.query).get("u", [""])[0]
        if path.rstrip("/") == "/user" and user_id.isdigit():
            return ParsedSource("patreon", f"user/{user_id}",
                                f"https://www.patreon.com/user?u={user_id}",
                                f"Patreon {user_id}", "work")
        parts = [part for part in path.split("/") if part]
        if parts and parts[0] == "cw":
            parts = parts[1:]
        reserved = {"posts", "join", "login", "signup", "home", "explore"}
        if not parts or parts[0].lower() in reserved:
            raise FollowSourceError(
                "Patreon 的链接要指向创作者主页，形如 https://patreon.com/cw/creator")
        vanity = parts[0]
        return ParsedSource("patreon", vanity,
                            f"https://www.patreon.com/cw/{vanity}", vanity, "work")

    if bare == "rule34video.com":
        matched = _R34V_PATH_RE.match(path)
        if not matched:
            raise FollowSourceError(
                "rule34video 的链接要指向作者页，形如 "
                "https://rule34video.com/models/lazyprocrastinator/")
        slug = matched.group(1)
        return ParsedSource("rule34video", slug,
                            f"https://rule34video.com/models/{slug}/",
                            _slug_label(slug), "work")

    if bare in ("rule34.xxx", "api.rule34.xxx"):
        tags = canonical_source_ref(
            "rule34xxx",
            urllib.parse.parse_qs(parsed.query).get("tags", [""])[0],
        )
        if not tags:
            raise FollowSourceError(
                "rule34.xxx 的链接要带标签，形如 "
                "https://rule34.xxx/index.php?page=post&s=list&tags=lazyprocrastinator")
        return ParsedSource("rule34xxx", tags,
                            "https://rule34.xxx/index.php?page=post&s=list"
                            f"&tags={urllib.parse.quote(tags)}",
                            _slug_label(tags), "work")

    if bare == "rule34.paheal.net":
        tag = urllib.parse.parse_qs(parsed.fragment).get("search", [""])[0]
        if not tag:
            matched = re.match(r"^/post/list/([^/]+)/\d+$", path)
            tag = urllib.parse.unquote(matched.group(1)) if matched else ""
        tag = canonical_source_ref("rule34paheal", tag)
        if not tag:
            raise FollowSourceError(
                "rule34.paheal 的链接要带搜索标签，形如 "
                "https://rule34.paheal.net/post/view/7428820#search=InitialA")
        encoded = urllib.parse.quote(tag, safe="()_")
        return ParsedSource("rule34paheal", tag,
                            f"https://rule34.paheal.net/post/list/{encoded}/1",
                            _slug_label(tag), "work")

    if bare == "f95zone.to":
        matched = _THREAD_PATH_RE.match(path)
        if not matched:
            raise FollowSourceError(
                "f95zone 的链接要指向一个线程，形如 "
                "https://f95zone.to/threads/xxx.50685/")
        thread = matched.group(1)
        slug = path.split("/threads/", 1)[1].rsplit(".", 1)[0] if "." in path else ""
        return ParsedSource("f95zone", thread,
                            f"https://f95zone.to/threads/{thread}/",
                            _slug_label(slug) or f"线程 {thread}", "release")

    if bare == "simpcity.cr":
        raise FollowSourceError(SimpCityConnector.blocked_reason)

    raise FollowSourceError(
        f"不认识 {bare}。当前支持 FANBOX、Patreon、SubscribeStar，"
        "kemono.cr、coomer.st、pawchive.pw 的创作者页，rule34video.com 的作者页，"
        "rule34.xxx 与 rule34.paheal.net 的标签页，以及 f95zone.to 的线程。")


CONNECTORS: dict[str, type] = {
    "fanbox": FanboxConnector,
    "patreon": PatreonConnector,
    "subscribestar": SubscribeStarConnector,
    "kemono": KemonoConnector,
    "coomer": KemonoConnector,
    "pawchive": KemonoConnector,
    "rule34video": Rule34VideoConnector,
    "rule34xxx": Rule34XxxConnector,
    "rule34paheal": Rule34PahealConnector,
    "f95zone": F95ZoneConnector,
    "simpcity": SimpCityConnector,
}


def display_thumb_url(item) -> str | None:
    """一条已入库的追更条目现在该用哪个缩略图 URL。

    分派到该站自己的连接器：「这个站的缩略图 URL 长什么样」是站点知识，属于连接器，
    不属于 Web 层。没登记的 provider 照原样用。
    """
    factory = CONNECTORS.get(str(item.provider or ""))
    if factory is None:
        return str(item.thumb_url or "") or None
    return factory.display_thumb_url(item)


def is_history_end_error(provider: str, message: str) -> bool:
    """一句已落盘的错误文本其实是「往回翻到尽头」吗？

    判据是各连接器声明的 `HISTORY_END_STATUSES`，和翻页时现场判定的用同一份声明。
    """
    factory = CONNECTORS.get(str(provider or ""))
    return factory is not None and factory.is_history_end_error(message)


def official_profile_handle(provider: str, ref: str) -> str:
    """这条来源的 ref 里那个可信的作者手柄，没有就返回空串。

    分派到该站自己的连接器：ref 的形状是站点知识。
    """
    factory = CONNECTORS.get(str(provider or ""))
    return factory.profile_handle(ref) if factory is not None else ""


def build_connector(provider: str, **kwargs) -> FollowConnector:
    factory = CONNECTORS.get(provider)
    if factory is None:
        raise FollowSourceError(f"未知的追更来源：{provider}")
    if factory is KemonoConnector:
        return KemonoConnector(provider=provider, **kwargs)
    return factory(**kwargs)
