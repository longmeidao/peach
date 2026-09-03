"""单页界面本体、它的静态资产，以及所有前端路由的落点。

这里的路由全部指向同一份 `index.html`：前端自己按 URL 渲染，服务端只负责让刷新
和直接粘地址都能进来。所以 `client_route` 的那一长串装饰器不是重复，是「前端有哪些
路由」的声明，新增页面必须在这里补一行，否则刷新就是 404。

`index` 的 401 走跳登录页，`/app.css`、`/app.js`、`/js/`、`/dist/` 走 PlainText 提示：
资产被浏览器直接请求，重定向到登录页只会让它把 HTML 当脚本解析。

缓存也分两档：`index.html` 是 `no-store`，它是所有资产 URL 的来源；四类资产走
`asset_response()` 的 ETag 复验，更新语义与 `no-store` 相同但没变时零传输。
"""
from __future__ import annotations

import re

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)

from .config import DATA_ROOT, PROJECT_ROOT, SETTINGS_PATH
from .routes_auth import require_asset_auth, require_page_auth, set_auth_cookie
from .web_state import FAVICON

router = APIRouter()

#: 未配置时的首次运行页。刻意不引用 `web/` 里的任何资产：那一套一上来就会去打
#: `/api/items`，而未配置的机器还没有数据库，页面只会是一屏红色报错。
_SETUP_PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peach · 首次运行</title>
<style>body{{margin:0;padding:3rem 1.5rem;background:#141216;color:#f2eef5;
font:16px/1.7 system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
main{{max-width:36rem;margin:0 auto}}h1{{font-size:1.5rem;margin:0 0 1rem}}
code{{background:#231f27;border-radius:.3rem;padding:.15rem .4rem}}
pre{{background:#231f27;border-radius:.5rem;padding:.9rem 1rem;overflow-x:auto}}
dt{{color:#b9aec4;font-size:.9rem}}dd{{margin:0 0 .6rem;word-break:break-all}}</style>
</head><body><main>
<h1>Peach 还没初始化</h1>
<p>这台机器上还没有数据根和设置文件，所以没有账本可读。服务本身是正常的。</p>
<pre>peach init</pre>
<p>它会建好数据目录、把数据库迁到最新、生成设置文件和本机 CA，然后告诉你下一步。
已经在跑的旧部署改用 <code>peach init --from-existing</code>：只生成设置文件，不动现有数据。</p>
<dl><dt>数据根（预定落点）</dt><dd>{data_root}</dd>
<dt>设置文件</dt><dd>{settings_path}</dd></dl>
<p><code>/healthz</code> 会报 <code>configured: false</code>，初始化完刷新本页即可。</p>
</main></body></html>
"""


def setup_page() -> str:
    """未配置提示页。路径是这一页唯一的动态内容，别让人自己去猜文件在哪。"""
    return _SETUP_PAGE.format(data_root=DATA_ROOT, settings_path=SETTINGS_PATH)


def asset_response(request: Request, path: Path, media: str) -> Response:
    """页面资产用 ETag 复验代替 no-store，`/app.js`、`/app.css`、`/js/`、`/dist/` 共用。

    `no-store` 让 `app.js`（435KB）加 `app.css`（232KB）每次开页都全量重下；
    `no-cache` 的更新语义完全一样——每次都回源验证，文件一变立刻生效——但没变时
    只回一个 304，零字节传输。代价是一次条件请求的往返。

    ETag 取 mtime_ns 加字节数，不读文件内容：这几个文件都由 Git 检出或 `frontend/`
    构建产生，改一次就换一次 mtime，不需要为了强校验去算全文哈希。
    """
    stat = path.stat()
    etag = f'"peach-{stat.st_mtime_ns:x}-{stat.st_size:x}"'
    if request.headers.get("if-none-match") == etag:
        response: Response = Response(status_code=304)
    else:
        response = FileResponse(path, media_type=f"{media}; charset=utf-8")
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"
    return response


@router.api_route("/", methods=["GET", "HEAD"])
def index(request: Request, args: dict[str, str] = Depends(require_page_auth)):
    settings = request.app.state.settings
    if settings.token and args.get("t"):
        response = RedirectResponse(request.url.path or "/", status_code=303)
        set_auth_cookie(response, request)
        return response
    if not settings.configured:
        # 未配置不是错误状态：服务照常起，页面告诉人去跑 `peach init`。
        return HTMLResponse(setup_page())
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
    return asset_response(request, path, media)


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
    return asset_response(request, path, "text/javascript")


@router.api_route("/dist/{name}", methods=["GET", "HEAD"])
def app_bundle(request: Request, name: str,
               args: dict[str, str] = Depends(require_asset_auth)):
    """`frontend/` 构建出来的 island 产物（ADR-0022）。口令与缓存口径同 `/js/`。

    产物提交进 Git 且文件名不带内容哈希，所以 `app.js` 能直接
    `await import('/dist/peach-ui.js')`；也正因为名字不带哈希，缓存只能靠复验，
    和 `/js/` 共用 `asset_response` 的 ETag 口径。
    名字判据和 `/js/` 逐字一致，只多认一个 `.css`：产物名不带内容哈希，也就不需要
    名字里再有点，`peach-ui.js.map` 这类附带文件跟着一起落在 404。
    """
    if not re.fullmatch(r"[a-z0-9_-]+\.(?:js|css)", name):
        return PlainTextResponse("bad bundle name", status_code=404)
    path = request.app.state.settings.page_path.parent / "dist" / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    media = "text/css" if name.endswith(".css") else "text/javascript"
    return asset_response(request, path, media)


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
