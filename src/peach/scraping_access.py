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
from . import peach_proxy
from .http import HttpRequest, HttpxTransport
from .scripting import USER_AGENT, host_under, hostname_of


SOURCES = {
    "r18dev": {"label": "R18.dev", "domains": ("r18.dev",), "login": "https://r18.dev/"},
    "dmm": {"label": "DMM / FANZA", "domains": ("dmm.co.jp", "dmm.com"), "login": "https://www.dmm.co.jp/"},
    "prestige": {"label": "Prestige", "domains": ("prestige-av.com",), "login": "https://www.prestige-av.com/"},
    "mgstage": {"label": "MGStage", "domains": ("mgstage.com",), "login": "https://www.mgstage.com/"},
    # FC2 的商品页、卖家页和图片存储（`storage*`、`contents-thumbnail*`）都在 fc2.com
    # 底下，一条域名就够。免登录可读，不收 Cookie。
    "fc2": {"label": "FC2", "domains": ("fc2.com",), "login": "https://adult.contents.fc2.com/"},
    # 女優那一栏在浏览器里只对登录用户显示，公开采集也带上用户贴的 Cookie（`session`），
    # 按登录用户看到的那一页取；游客补问这一栏眼下也回，见 `sources/fc2cmadb.py`。
    "fc2cmadb": {"label": "FC2CMADB", "domains": ("fc2cmadb.com",), "login": "https://fc2cmadb.com/",
                 "cookie": True, "session": True},
    # FC2 商品的两个存档站都在 Cloudflare 的 JS 验证后面：httpx 与模拟 Chrome 指纹的直连都回 403，
    # 只有浏览器过完验证发下的 `cf_clearance` 能进，而它绑着解题那台浏览器的 User-Agent 与出口。
    # 整站 UA（`peach.user_agent`）与用户的 Chrome 保持一致就够了，Cookie 由用户贴；连接方式由用户
    # 选成与浏览器同一个出口。Cookie 过期后回 403，按 `blocked_pause` 停下等用户换新的，不反复撞。
    "fc2ppvdb": {"label": "FC2PPV-DB", "domains": ("fc2ppv-db.com",), "login": "https://fc2ppv-db.com/",
                 "cookie": True, "session": True, "blocked_pause": 6 * 3600},
    "javten": {"label": "JAVten", "domains": ("javten.com",), "login": "https://javten.com/",
               "cookie": True, "session": True, "blocked_pause": 6 * 3600},
    # 下架 FC2 的最后一档。作品页在 javarchive.com、封面转存在 javstore.net 上，两边算同一个
    # 来源。免登录可读，不收 Cookie，`robots.txt` 是全站放行。
    "javarchive": {"label": "JavArchive", "domains": ("javarchive.com", "javstore.net"),
                   "login": "https://javarchive.com/"},
    # 作品 JSON、剧照和样片都在 1pondo.tv 底下（含 `smovie.`）。免登录可读，不收 Cookie。
    "1pondo": {"label": "一本道", "domains": ("1pondo.tv",), "login": "https://www.1pondo.tv/"},
    "instagram": {"label": "Instagram", "domains": ("instagram.com", "cdninstagram.com"), "login": "https://www.instagram.com/accounts/login/", "cookie": True},
    # 两家社区来源拒绝访问时回 403，不发 Retry-After：javdb 是出口 IP 超了配额（一封 3～7 日，
    # docs/SOURCING.md），AVBase 是 Cloudflare 验证。封期里接着问只会每条都再撞一次，
    # 所以整个来源停下——停多久按 `FIRST_BLOCKED_PAUSE` 翻倍，`blocked_pause` 是这个来源的上限。
    # `session`：公开采集也带上用户在采集设置里贴的 Cookie。javdb 有登录墙，JavBus 有年龄门，
    # 不带只回确认页；Cookie 由用户在浏览器里过门或登录后贴进来，Peach 不读浏览器的 Cookie 库。
    "javdb": {"label": "JavDB", "domains": ("javdb.com", "jdbstatic.com", "jdbimgs.com"), "login": "https://javdb.com/",
              "cookie": True, "session": True, "blocked_pause": 24 * 3600},
    "javbus": {"label": "JavBus", "domains": ("javbus.com",), "login": "https://www.javbus.com/", "cookie": True, "session": True},
    "avbase": {"label": "AVBase", "domains": ("avbase.net",), "login": "https://www.avbase.net/", "blocked_pause": 6 * 3600},
}
_LOCK = threading.RLock()

#: 撞上拒绝访问后第一次停多久。`blocked_pause` 是**上限**，不是首停时长：那几家按出口
#: IP 计的封，实际封期常常远短于上限。2026-09-22 实测——javdb 记下的 24 小时只走了
#: 6.6 小时，用同一套 client 问首页和两条搜索全回 200，剩下的时间整个来源在盲等，那一轮
#: 778 部片的 1432 条失败全部写着「来源正在冷却」。所以先停这一档，连着再撞才翻倍到上限；
#: 通了一次就把记录清掉，下次从最短的一档重新起算。
FIRST_BLOCKED_PAUSE = 900


class SourcePaused(RuntimeError):
    """来源冷却期内停止请求，保留已有图像。"""


def cooldown_path(root: Path, source: str) -> Path:
    """这个来源的冷却记录。键是来源名；没有来源名的请求按主机名散列，见 `SourceTransport`。"""
    return Path(root) / ("scraping-" + source + ".cooldown.json")


def cooldown_state(root: Path, source: str) -> tuple[float, int]:
    """`(冷却到几点, 连着撞了几次)`；没有记录或记录坏了都按 `(0, 0)`。"""
    try:
        record = json.loads(cooldown_path(root, source).read_text(encoding="utf-8"))
        return float(record["until"]), int(record.get("blocks") or 0)
    except (OSError, ValueError, KeyError, TypeError):
        return 0.0, 0


def paused_until(root: Path, source: str) -> float:
    """来源还在冷却就返回到几点，否则 0。amane 桥那几站在起子进程前按它筛。"""
    until, _ = cooldown_state(root, source)
    return until if until > time.time() else 0.0


def pause_source(root: Path, source: str, *, refused: bool = False,
                 retry_after: float | None = None) -> float:
    """按现成的两档把来源停下，返回冷却到几点。

    `refused` 走 403 那一档：先停 `FIRST_BLOCKED_PAUSE`，连着再撞才翻倍，上限是
    `SOURCES[source]['blocked_pause']`，没登记上限的来源按 24 小时。否则走 429 那一档：
    停站方说的 `retry_after` 秒，没说就 15 分钟。不是 httpx 那条路（amane 桥）发现的
    限流与封禁也从这里进，两条路读写的是同一份记录。
    """
    until, blocks = cooldown_state(root, source)
    if refused:
        blocks += 1
        limit = SOURCES.get(source, {}).get("blocked_pause") or 24 * 3600
        until = time.time() + min(FIRST_BLOCKED_PAUSE * 2 ** (blocks - 1), limit)
    else:
        until = time.time() + max(0.0, float(retry_after if retry_after is not None else 900))
    _pause(cooldown_path(root, source), until, blocks)
    return until


def _pause(cooldown: Path, until: float, blocks: int = 0) -> None:
    with _LOCK:
        cooldown.parent.mkdir(parents=True, exist_ok=True)
        cooldown.write_text(json.dumps({"until": max(until, time.time() + 1), "blocks": blocks}),
                            encoding="utf-8")


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
        mode = body.get("network", "direct" if values.get("network") == "direct" else "peach")
        if mode not in {"direct", "peach"}:
            raise ValueError("请选择来源连接方式")
        if values.get("network") == "proxy" and mode == "peach":
            inherited = peach_proxy.values(root)
            peach_proxy.client_options(root)
            peach_proxy.save(root, inherited)
        values["network"] = mode
        values.pop("proxy", None)
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
            # 新 Cookie 多半是为了解开 403 才换的；冷却记的是旧 Cookie 撞出来的账，别让它压着新的等到期。
            cooldown_path(root, source).unlink(missing_ok=True)
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
            "network": "direct" if values.get("network") == "direct" else "peach",
            "cookie_saved": bool(values.get("cookie") or values.get("cookies_text"))}


def client_for(root: Path, source: str, *, session: bool = False, **kwargs) -> httpx.Client:
    values = values_for(root, source)
    network = {"trust_env": False} if values.get("network") == "direct" else peach_proxy.client_options(root)
    options = {**network, "follow_redirects": True,
               "headers": {"User-Agent": USER_AGENT}}
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
        """闸门到顶的三句话都写「本趟」和「再跑一次接着采」：这三条按任务重新计数，
        读的人要据以决定的是「现在重跑一遍」，不是去查哪里还有配额。"""
        source = source_for(request.url)
        if self.max_requests and self.requests >= self.max_requests:
            raise SourcePaused("本趟采集次数已用完，再跑一次接着采；已有图片保留")
        if self.deadline:
            timeout = min(timeout, self.deadline - time.monotonic())
            if timeout <= 0:
                raise SourcePaused("本趟采集时间已用完，再跑一次接着采；已有图片保留")
        if self.max_bytes:
            remaining = self.max_bytes - self.bytes
            if remaining <= 0:
                raise SourcePaused("本趟下载量已用完，再跑一次接着采；已有图片保留")
            max_bytes = min(max_bytes, remaining - 1)
        key = source or hashlib.sha256(hostname_of(request.url).encode()).hexdigest()
        cooldown = cooldown_path(self.root, key)
        until, blocks = cooldown_state(self.root, key)
        if until > time.time():
            raise SourcePaused("来源正在冷却，请稍后重试；已有图片保留")
        if source not in self.transports:
            client = (client_for(self.root, source, session=bool(SOURCES[source].get("session")),
                                 follow_redirects=False) if source else
                      httpx.Client(**peach_proxy.client_options(self.root), follow_redirects=False, headers={"User-Agent": USER_AGENT}))
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
            _pause(cooldown, until, blocks)
            raise SourcePaused("来源限流，已记录冷却时间；已有图片保留")
        blocked_pause = SOURCES.get(source or "", {}).get("blocked_pause")
        if response.status == 403 and blocked_pause:
            blocks += 1
            _pause(cooldown, time.time()
                   + min(FIRST_BLOCKED_PAUSE * 2 ** (blocks - 1), blocked_pause), blocks)
            if SOURCES[source].get("cookie"):
                raise SourcePaused("来源拒绝访问，暂停向它请求一段时间；"
                                   "请在采集设置里更新它的 Cookie；已有图片保留")
            raise SourcePaused("来源拒绝访问，暂停向它请求一段时间；已有图片保留")
        if blocks and response.status < 400:
            # 这一趟通了，封已经解除：清掉记录，下次撞上从最短的一档重新起算。
            cooldown.unlink(missing_ok=True)
        return response

    def renew(self):
        self.close()

    def close(self):
        for transport in self.transports.values():
            transport.close()
        self.transports.clear()
