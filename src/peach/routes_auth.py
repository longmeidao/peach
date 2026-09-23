"""口令闸门与登录页。

401 有三种形态，按路由类分组保留（不许统一成一种）：页面路由跳登录页，页面资产
返回 PlainText 提示，API 与媒体路由返回 JSON。三个 `require_*` 是唯一的判定入口，
路由里不要自己比对口令；对应的响应形态由 `api.py` 的异常处理器给出。

口令从 `request.app.state.settings` 取，不是闭包捕获：路由挂在模块级的 `APIRouter`
上，import 期就定型了，那时还没有 settings。
"""
from __future__ import annotations

import hmac
import html
from collections import OrderedDict
import threading
import time
from urllib.parse import urlsplit
from . import access, tunnel
from .web_entry import check_html, entry_page_style
from starlette.concurrency import run_in_threadpool
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

router = APIRouter()
_ATTEMPTS: OrderedDict[str, list[float]] = OrderedDict()
_ATTEMPTS_LOCK = threading.Lock()


def _attempt_key(request: Request) -> str:
    """限速按真实来源分桶。

    隧道在跑时所有请求的连接源都是 cloudflared 的回环地址，按它计数等于把整个公网
    合成一个桶：外面一台机器试满十次，本机浏览器也跟着被锁一分钟。这时改用边缘给出
    的客户端地址，隧道没在跑就仍按连接源，避免任何人自带一个头就换一个桶。
    """
    if tunnel.running(getattr(request.app.state, "tunnel", None)):
        forwarded = (request.headers.get("cf-connecting-ip") or "").strip()
        if forwarded:
            return f"cf:{forwarded}"
    return request.client.host if request.client else "unknown"


def _login_attempt(request: Request) -> None:
    """按连接来源限制密码尝试，保留有界的短期计数。"""
    peer = _attempt_key(request)
    now = time.monotonic()
    with _ATTEMPTS_LOCK:
        attempts = [stamp for stamp in _ATTEMPTS.pop(peer, []) if now - stamp < 60]
        _ATTEMPTS[peer] = attempts
        if len(attempts) >= 10:
            raise HTTPException(429, "尝试次数较多，请一分钟后重试", headers={"Retry-After": "60"})
        attempts.append(now)
        while len(_ATTEMPTS) > 1024:
            _ATTEMPTS.popitem(last=False)


def _policy(request: Request) -> dict:
    policy = access.load(request.app.state.settings.access_path)
    if policy["mode"] == "legacy":
        policy["key"] = request.app.state.settings.token
    return policy


def _first_query_values(request: Request) -> dict[str, str]:
    """兼容 urllib.parse.parse_qs：取首值并忽略空值。"""
    result: dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        if key not in result and value != "":
            result[key] = value
    return result


def _authorized(request: Request, token: str, args: dict[str, str]) -> bool:
    if not token:
        return True
    supplied = args.get("t") or request.headers.get("X-Token")
    if supplied is not None and hmac.compare_digest(str(supplied).encode(), token.encode()):
        return True
    policy = _policy(request)
    if policy["mode"] == "open":
        return True
    if policy["mode"] == "legacy":
        if hmac.compare_digest(request.cookies.get("tok", "").encode(), token.encode()):
            return True
    return access.valid_session(policy, request.cookies.get(access.COOKIE, ""))


class PageLoginRequired(Exception):
    """页面路由未授权：401 形态是跳登录页，不是响应体。"""

    def __init__(self, next_path: str):
        self.next_path = next_path


class AssetLoginRequired(Exception):
    """页面资产（app.css/app.js）未授权：401 形态是 PlainText 提示。"""


def _origin_key(value: str) -> tuple[str, str, int | None] | None:
    """把 Origin 头和隧道 URL 归一到可比较的三元组。"""
    try:
        parsed = urlsplit(value.strip().rstrip("/"))
    except ValueError:
        return None
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    return parsed.scheme.lower(), parsed.hostname.rstrip(".").lower(), port


def _tunnel_origin(request: Request) -> tuple[str, str, int | None] | None:
    """返回当前进程实际拿到的隧道 origin，而不是信任请求头。"""
    manager = getattr(request.app.state, "tunnel", None)
    if manager is None:
        return None
    try:
        url = manager.snapshot().url
    except (AttributeError, OSError, ValueError):
        return None
    return _origin_key(url) if url else None


def _named_origin(request: Request) -> tuple[str, str, int | None] | None:
    """命名隧道的公开主机名。

    它来自本次启动注入的运行设置，不是请求头，也不随隧道握手完成才出现：连接刚建立
    那几秒页面就已经能提交，这时 manager 的快照还没进入 running。
    """
    settings = getattr(request.app.state, "settings", None)
    if getattr(settings, "tunnel_mode", "") != tunnel.NAMED_MODE:
        return None
    hostname = (getattr(settings, "tunnel_hostname", "") or "").strip()
    return _origin_key(tunnel.public_url(hostname)) if hostname else None


def same_origin(request: Request) -> None:
    """浏览器写请求只接受 Peach 页面或当前隧道页面发来的 Origin。

    独立包的 origin 是回环 HTTP，cloudflared 转发时 Host 仍可能是本机地址，
    所以不能单纯把 ``Origin`` 和 ASGI 的 ``base_url`` 比较。临时链接的随机入口由当前
    TunnelManager 产生并保存在进程内，命名隧道的公开主机名来自本次启动的运行设置；
    外部 Origin 必须精确匹配这两者之一，不能由调用方通过 ``X-Forwarded-*`` 自己
    声明一个可信地址。
    """
    origin = request.headers.get("origin")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "请从 Peach 配置页提交")
    if origin:
        supplied = _origin_key(origin)
        local = _origin_key(str(request.base_url))
        allowed = {local, _tunnel_origin(request), _named_origin(request)}
        if supplied is None or supplied not in allowed:
            raise HTTPException(403, "请从 Peach 配置页提交")


def require_auth(request: Request) -> dict[str, str]:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        same_origin(request)
    args = _first_query_values(request)
    if not _authorized(request, request.app.state.settings.token, args):
        raise HTTPException(status_code=401, detail="unauthorized")
    return args


def require_page_auth(request: Request) -> dict[str, str]:
    args = _first_query_values(request)
    if not _authorized(request, request.app.state.settings.token, args):
        raise PageLoginRequired(request.url.path or "/")
    return args


def require_asset_auth(request: Request) -> dict[str, str]:
    args = _first_query_values(request)
    if not _authorized(request, request.app.state.settings.token, args):
        raise AssetLoginRequired()
    return args


def set_auth_cookie(response: Response, request: Request, *, days: int = 30, login: bool = False) -> None:
    token = request.app.state.settings.token
    policy = _policy(request)
    response.headers["Cache-Control"] = "no-store"
    if token and policy["mode"] in {"password", "legacy"} and (login or request.query_params.get("t") == token):
        value, max_age = access.issue(policy, days)
        response.set_cookie(access.COOKIE, value, max_age=max_age, path="/", httponly=True,
                            samesite="lax", secure=request.url.scheme == "https")
        response.delete_cookie("tok", path="/")


def login_html(next_path: str, *, invalid: bool = False) -> str:
    """登录页：首启页那张 Auth Card 的单字段形态，控件全部来自 `web_entry`。

    这一页和首启页是同一副面孔的两个状态，所以样式层整份取 `entry_page_style()`，
    不在这里另留一套色板和控件——那一套自成一格，登录完跳进馆藏就像换了个产品。
    """
    safe_next = html.escape(next_path, quote=True)
    # 密码错了是这个字段的事，不是整页的事：框体线条转 danger 色，原因紧跟在下面。
    field_state = "true" if invalid else "false"
    described = ' aria-describedby="login-error"' if invalid else ""
    error = '<p class="bad" id="login-error" role="alert">访问密码不正确</p>' if invalid else ""
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark">'
        # 公网入口在跑的时候这一页就在互联网上，不希望它进任何搜索结果。
        # 响应头那一份（`X-Robots-Tag`）管所有响应，这一行管只读 HTML 的爬虫。
        '<meta name="robots" content="noindex, nofollow">'
        '<title>登录 Peach</title>'
        # 图标声明和主站同一份。书签地址是 `/`，没有会话时这一页就是它实际停在的地方：
        # 这里不声明，浏览器只会去要 `/favicon.ico`，把「这个站没有图标」记进书签。
        '<link rel="icon" href="/favicon.ico" type="image/x-icon">'
        # 手动选的那一档压过系统偏好，必须在第一次绘制前定下来——固定浅色的人不该在
        # 登录页先看一眼深色。深浅两套色板由 `entry_page_style()` 随后给出。
        '<script>(()=>{try{'
        'const c=JSON.parse(localStorage.getItem("peach.settings.v1")||"{}").theme;'
        'if(c==="light"||c==="dark")document.documentElement.dataset.theme=c;'
        '}catch(e){}})();</script>'
        f'{entry_page_style()}</head><body><main>'
        '<section class="setup-auth-card login-card">'
        '<header><img class="mark" src="/peach-logo.png" alt="" width="40" height="40"><h1>Peach</h1></header>'
        '<form method="post" action="/login">'
        '<div class="field"><label class="field-label" for="login-token">访问密码</label>'
        '<span class="entry-input"><input id="login-token" name="token" type="password" maxlength="256" '
        f'autocomplete="current-password" aria-invalid="{field_state}"{described} required autofocus></span>'
        f'{error}</div>'
        f'<input name="next" type="hidden" value="{safe_next}">'
        + check_html("days", "保持登录", checked=True, value="30")
        + '<button type="submit">登录</button></form></section></main></body></html>'
    )


@router.get("/login", response_class=HTMLResponse)
def login(request: Request, next: str = "/"):
    next_path = next if next.startswith("/") and not next.startswith("//") else "/"
    if _authorized(request, request.app.state.settings.token,
                   _first_query_values(request)):
        return RedirectResponse(next_path, status_code=303)
    return HTMLResponse(login_html(next_path))


@router.post("/login")
async def login_submit(request: Request):
    same_origin(request)
    _login_attempt(request)
    token = request.app.state.settings.token
    form = parse_qs(
        (await request.body()).decode("utf-8", "replace"), keep_blank_values=True,
    )
    supplied = (form.get("token") or [""])[0]
    next_path = (form.get("next") or ["/"])[0]
    if not next_path.startswith("/") or next_path.startswith("//"):
        next_path = "/"
    policy = access.load(request.app.state.settings.access_path)
    if token and policy["mode"] != "open" and not await run_in_threadpool(access.verify, policy, supplied, token):
        return HTMLResponse(login_html(next_path, invalid=True), status_code=401)
    try:
        days = int((form.get("days") or ["0"])[0])
        if not 0 <= days <= 365:
            raise ValueError
    except ValueError:
        raise HTTPException(400, "请选择有效的保持登录时间") from None
    response = RedirectResponse(next_path, status_code=303)
    set_auth_cookie(response, request, days=days, login=True)
    return response
