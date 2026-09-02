"""单页界面本体、它的静态资产，以及所有前端路由的落点。

这里的路由全部指向同一份 `index.html`：前端自己按 URL 渲染，服务端只负责让刷新
和直接粘地址都能进来。所以 `client_route` 的那一长串装饰器不是重复，是「前端有哪些
路由」的声明，新增页面必须在这里补一行，否则刷新就是 404。

`index` 的 401 走跳登录页，`/app.css`、`/app.js`、`/js/`、`/dist/` 走 PlainText 提示：
资产被浏览器直接请求，重定向到登录页只会让它把 HTML 当脚本解析。
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse, Response

from .config import PROJECT_ROOT
from .routes_auth import require_asset_auth, require_page_auth, set_auth_cookie
from .web_state import FAVICON

router = APIRouter()


@router.api_route("/", methods=["GET", "HEAD"])
def index(request: Request, args: dict[str, str] = Depends(require_page_auth)):
    settings = request.app.state.settings
    if settings.token and args.get("t"):
        response = RedirectResponse(request.url.path or "/", status_code=303)
        set_auth_cookie(response, request)
        return response
    if not settings.page_path.is_file():
        return PlainTextResponse("Peach page missing", status_code=500)
    response = FileResponse(settings.page_path, media_type="text/html")
    response.headers["Cache-Control"] = "no-store"
    set_auth_cookie(response, request)
    return response


@router.api_route("/app.css", methods=["GET", "HEAD"])
@router.api_route("/app.js", methods=["GET", "HEAD"])
def app_asset(request: Request, args: dict[str, str] = Depends(require_asset_auth)):
    """页面拆出来的样式与入口脚本。和 index.html 同目录，同一套口令。

    仍然没有构建步骤：`app.js` 现在是 ES module，浏览器原生解析 import，
    拆出来的模块见下面的 `/js/{name}`。页面里没有任何内联事件处理器，
    全部是 `.onclick=` 属性赋值，所以顶层声明不再是全局也不影响绑定。
    """
    name = request.url.path.lstrip("/")
    path = request.app.state.settings.page_path.parent / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    media = "text/css" if name.endswith(".css") else "text/javascript"
    response = FileResponse(path, media_type=f"{media}; charset=utf-8")
    # 页面本体是 no-store，样式与脚本跟着它一起变，不能被旧缓存钉住。
    response.headers["Cache-Control"] = "no-store"
    return response


@router.api_route("/js/{name}", methods=["GET", "HEAD"])
def app_module(request: Request, name: str,
               args: dict[str, str] = Depends(require_asset_auth)):
    """`app.js` 拆出来的 ES module。和入口脚本同一套口令与 401 形态。

    文件名严格限制为一层平铺的 `[a-z0-9_-]+.js`：静态路由拼路径是典型的目录
    穿越入口，与其在这里做 resolve 后再比较根目录，不如根本不接受分隔符。
    前端模块规模不大，平铺够用。
    """
    if not re.fullmatch(r"[a-z0-9_-]+\.js", name):
        return PlainTextResponse("bad module name", status_code=404)
    path = request.app.state.settings.page_path.parent / "js" / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    response = FileResponse(path, media_type="text/javascript; charset=utf-8")
    # 和 index.html/app.js 同一口径：页面一变模块就跟着变，不能被旧缓存钉住。
    response.headers["Cache-Control"] = "no-store"
    return response


@router.api_route("/dist/{name}", methods=["GET", "HEAD"])
def app_bundle(request: Request, name: str,
               args: dict[str, str] = Depends(require_asset_auth)):
    """`frontend/` 构建出来的 island 产物（ADR-0022）。口令与缓存口径同 `/js/`。

    产物提交进 Git 且文件名不带内容哈希，所以 `app.js` 能直接
    `await import('/dist/peach-ui.js')`；缓存仍由 no-store 兜住。
    名字判据和 `/js/` 逐字一致，只多认一个 `.css`：产物名不带内容哈希，也就不需要
    名字里再有点，`peach-ui.js.map` 这类附带文件跟着一起落在 404。
    """
    if not re.fullmatch(r"[a-z0-9_-]+\.(?:js|css)", name):
        return PlainTextResponse("bad bundle name", status_code=404)
    path = request.app.state.settings.page_path.parent / "dist" / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    media = "text/css" if name.endswith(".css") else "text/javascript"
    response = FileResponse(path, media_type=f"{media}; charset=utf-8")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.api_route("/favicon.svg", methods=["GET", "HEAD"])
def favicon():
    response = Response(FAVICON, media_type="image/svg+xml")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.api_route("/peach-logo.png", methods=["GET", "HEAD"])
def peach_logo():
    return FileResponse(PROJECT_ROOT / "resources" / "peach-logo.png", media_type="image/png")


@router.api_route("/item/{item_id}", methods=["GET", "HEAD"])
@router.api_route("/mix/{seed_id}/{mix_item_id}", methods=["GET", "HEAD"])
@router.api_route("/parts/{part_seed_id}/{part_item_id}", methods=["GET", "HEAD"])
@router.api_route("/editions/{edition_seed_id}/{edition_item_id}", methods=["GET", "HEAD"])
@router.api_route("/playlists", methods=["GET", "HEAD"])
@router.api_route("/playlists/{playlist_id}/{playlist_item_id}", methods=["GET", "HEAD"])
@router.api_route("/performers/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/studios/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/creators/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/series/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/performers", methods=["GET", "HEAD"])
@router.api_route("/creators", methods=["GET", "HEAD"])
@router.api_route("/tags", methods=["GET", "HEAD"])
@router.api_route("/unseen", methods=["GET", "HEAD"])
@router.api_route("/watch-later", methods=["GET", "HEAD"])
@router.api_route("/flagged", methods=["GET", "HEAD"])
@router.api_route("/junk-files", methods=["GET", "HEAD"])
@router.api_route("/stats", methods=["GET", "HEAD"])
@router.api_route("/immerse", methods=["GET", "HEAD"])
@router.api_route("/trash", methods=["GET", "HEAD"])
@router.api_route("/review", methods=["GET", "HEAD"])
@router.api_route("/taste", methods=["GET", "HEAD"])
@router.api_route("/data-cleanup", methods=["GET", "HEAD"])
@router.api_route("/duplicates", methods=["GET", "HEAD"])
@router.api_route("/quality-goals", methods=["GET", "HEAD"])
@router.api_route("/resource-sync", methods=["GET", "HEAD"])
@router.api_route("/follow", methods=["GET", "HEAD"])
@router.api_route("/follow-manage", methods=["GET", "HEAD"])
@router.api_route("/follow/item/{item_id}", methods=["GET", "HEAD"])
def client_route(request: Request, item_id: int | None = None,
                 seed_id: int | None = None, mix_item_id: int | None = None,
                 part_seed_id: int | None = None, part_item_id: int | None = None,
                 edition_seed_id: int | None = None, edition_item_id: int | None = None,
                 playlist_id: int | None = None, playlist_item_id: int | None = None,
                 kind: str | None = None, name: str | None = None,
                 args: dict[str, str] = Depends(require_page_auth)):
    return index(request, args)
