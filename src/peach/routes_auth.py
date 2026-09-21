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
from .web_entry import board_entry_style
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
    safe_next = html.escape(next_path, quote=True)
    error = '<p role="alert">访问密码不正确</p>' if invalid else ""
    return (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark"><title>登录 Peach</title>'
        # 图标声明和主站同一份。书签地址是 `/`，没有会话时这一页就是它实际停在的地方：
        # 这里不声明，浏览器只会去要 `/favicon.ico`，把「这个站没有图标」记进书签。
        '<link rel="icon" href="/favicon.ico" type="image/x-icon">'
        # 这一页在拿到 cookie 之前就要出图，取不到 /app.css，所以色板在这儿留一份最小副本。
        # 三条分支和 web/css/01-base.css 同构：默认浅色、系统深色、手动选的那一档压过系统。
        # 选择由下面这段脚本在第一次绘制前读出来——固定浅色的人不该在登录页先看一眼深色。
        '<script>(()=>{try{'
        'const c=JSON.parse(localStorage.getItem("peach.settings.v1")||"{}").theme;'
        'if(c==="light"||c==="dark")document.documentElement.dataset.theme=c;'
        '}catch(e){}})();</script>'
        '<style>'
        '*{box-sizing:border-box}'
        ':root{color-scheme:light;--bg:#FFFFFF;--card:#FAFAFA;--line:rgba(0,0,0,.10);'
        '--ink:#171717;--ink-2:#4D4D4D;--field:#FFFFFF;--alert:#C0392B;'
        '--shadow:0 1px 1px rgba(0,0,0,.02),0 4px 8px -4px rgba(0,0,0,.04),0 16px 24px -8px rgba(0,0,0,.06)}'
        '@media (prefers-color-scheme:dark){html:not([data-theme="light"]){color-scheme:dark;'
        '--bg:#080A0D;--card:#0C0F14;--line:rgba(255,255,255,.12);--ink:#FFFFFF;--ink-2:#C9CDD4;'
        '--field:#0B0D11;--alert:#FF5252;--shadow:0 24px 80px rgba(0,0,0,.48)}}'
        'html[data-theme="dark"]{color-scheme:dark;'
        '--bg:#080A0D;--card:#0C0F14;--line:rgba(255,255,255,.12);--ink:#FFFFFF;--ink-2:#C9CDD4;'
        '--field:#0B0D11;--alert:#FF5252;--shadow:0 24px 80px rgba(0,0,0,.48)}'
        'html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink)}'
        'body{min-height:100dvh;display:grid;place-items:center;padding:24px;font:15px/1.45 system-ui,sans-serif}'
        'main{width:min(360px,100%);padding:30px;border:1px solid var(--line);border-radius:20px;'
        'background:var(--card);box-shadow:var(--shadow)}'
        '.brand{display:flex;align-items:center;gap:12px;margin-bottom:24px}.brand img{width:48px;height:48px}'
        'h1{margin:0;font-size:24px;letter-spacing:.02em}label{display:grid;gap:8px;color:var(--ink-2)}'
        'input,select{width:100%;height:44px;border:1px solid var(--line);border-radius:11px;'
        'background:var(--field);color:var(--ink);padding:0 13px;font:inherit;outline:none}'
        'input:focus,select:focus{outline:2px solid var(--ink);outline-offset:2px}'
        'form{display:grid;gap:16px}form p{font-size:13px;color:var(--ink-2);margin:0}'
        '.remember{display:flex;align-items:center;gap:8px;font-size:14px;line-height:20px}'
        '.remember input{width:16px;height:16px;margin:0;accent-color:var(--ink);flex:none}'
        'button{width:100%;height:44px;margin-top:16px;border:0;border-radius:11px;cursor:pointer;'
        'background:var(--ink);color:var(--bg);font:500 15px system-ui,sans-serif}'
        'button:hover{background:color-mix(in srgb,var(--ink) 88%,var(--bg));color:var(--bg)}p[role=alert]{margin:0 0 14px;color:var(--alert)}'
        f'</style>{board_entry_style()}<body><main><div class="brand"><img src="/peach-logo.png" alt=""><h1>Peach</h1></div>'
        f'{error}<form method="post" action="/login">'
        '<label>访问密码 <input name="token" type="password" maxlength="256" '
        'autocomplete="current-password" required></label>'
        f'<input name="next" type="hidden" value="{safe_next}">'
        '<label class="remember"><input type="checkbox" name="days" value="30" checked>保持登录</label>'
        '<button type="submit">登录</button></form></main><script>'
        'try{const d=JSON.parse(localStorage.getItem("peach.settings.v1")||"{}").loginDays;'
        'if(Number.isInteger(d)&&d>=1&&d<=365)document.querySelector("[name=days]").value=String(d)}catch{}'
        '</script></body></html>'
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
