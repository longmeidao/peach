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
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

router = APIRouter()


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
    supplied = args.get("t") or request.headers.get("X-Token") or request.cookies.get("tok")
    return supplied is not None and hmac.compare_digest(str(supplied), token)


class PageLoginRequired(Exception):
    """页面路由未授权：401 形态是跳登录页，不是响应体。"""

    def __init__(self, next_path: str):
        self.next_path = next_path


class AssetLoginRequired(Exception):
    """页面资产（app.css/app.js）未授权：401 形态是 PlainText 提示。"""


def require_auth(request: Request) -> dict[str, str]:
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


def set_auth_cookie(response: Response, request: Request) -> None:
    token = request.app.state.settings.token
    if token:
        response.set_cookie(
            "tok", token, max_age=31536000, path="/", httponly=True,
            samesite="lax", secure=request.url.scheme == "https",
        )


def login_html(next_path: str, *, invalid: bool = False) -> str:
    safe_next = html.escape(next_path, quote=True)
    error = '<p role="alert">口令不正确</p>' if invalid else ""
    return (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark"><title>登录 Peach</title>'
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
        'input{width:100%;height:44px;border:1px solid var(--line);border-radius:11px;'
        'background:var(--field);color:var(--ink);padding:0 13px;font:inherit;outline:none}'
        'input:focus{border-color:#ff8b70;box-shadow:0 0 0 3px rgba(255,139,112,.16)}'
        'button{width:100%;height:44px;margin-top:16px;border:0;border-radius:11px;cursor:pointer;'
        'background:linear-gradient(135deg,#ff9a76,#f2557b);color:#130609;font:700 15px system-ui,sans-serif}'
        'button:hover{filter:brightness(1.06)}p[role=alert]{margin:0 0 14px;color:var(--alert)}'
        '</style><body><main><div class="brand"><img src="/peach-logo.png" alt=""><h1>Peach</h1></div>'
        f'{error}<form method="post" action="/login">'
        '<label>口令 <input name="token" type="password" '
        'autocomplete="current-password" required></label>'
        f'<input name="next" type="hidden" value="{safe_next}">'
        '<button type="submit">登录</button></form></main></body></html>'
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
    token = request.app.state.settings.token
    form = parse_qs(
        (await request.body()).decode("utf-8", "replace"), keep_blank_values=True,
    )
    supplied = (form.get("token") or [""])[0]
    next_path = (form.get("next") or ["/"])[0]
    if not next_path.startswith("/") or next_path.startswith("//"):
        next_path = "/"
    if token and not hmac.compare_digest(str(supplied), token):
        return HTMLResponse(login_html(next_path, invalid=True), status_code=401)
    response = RedirectResponse(next_path, status_code=303)
    set_auth_cookie(response, request)
    return response
