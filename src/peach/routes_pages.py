"""单页界面本体、它的静态资产，以及所有前端路由的落点。

这里的路由全部指向同一份 `index.html`：前端自己按 URL 渲染，服务端只负责让刷新
和直接粘地址都能进来。所以 `client_route` 的那一长串装饰器不是重复，是「前端有哪些
路由」的声明，新增页面必须在这里补一行，否则刷新就是 404。

`index` 的 401 走跳登录页，`/app.css`、`/app.js`、`/js/`、`/dist/` 走 PlainText 提示：
资产被浏览器直接请求，重定向到登录页只会让它把 HTML 当脚本解析。

缓存也分两档：`index.html` 是 `no-store`，它是所有资产 URL 的来源；四类资产走
`asset_response()` 的 ETag 复验，更新语义与 `no-store` 相同但没变时零传输。

`/app.css` 是唯一一个不对应单个文件的资产：样式表按分区拆在 `web/css/` 下，这里
按文件名顺序拼起来交付，见 `stylesheet_response()`。
"""
from __future__ import annotations

import hashlib
import os
import re

from html import escape
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)

from . import auth, distribution, onboarding, settings_file
from .config import PROJECT_ROOT
from .routes_auth import require_asset_auth, require_page_auth, set_auth_cookie
from .web_state import FAVICON

router = APIRouter()

#: 回环地址的三种写法。既用来判提交端点的调用方，也用来判「仅本机」那个监听选择。
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost"})

#: 首次运行页的样式。刻意不引用 `web/` 里的任何资产：那一套一上来就会去打
#: `/api/items`，而未配置的机器还没有数据库，页面只会是一屏红色报错。这一页因此
#: 落在 SPA 外壳之外，不是一个 `frontend/` island（ADR-0022、docs/FRONTEND.md）。
_SETUP_STYLE = """<style>
*{box-sizing:border-box}
body{margin:0;padding:48px 24px;background:var(--ground);color:var(--ink);
font:16px/1.6 system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:560px;margin:0 auto}h1{font-size:28px;font-weight:600;margin:24px 0 8px}
h2{font-size:18px;font-weight:600;margin-top:32px;padding-top:24px;border-top:1px solid var(--line)}
p{color:var(--ink-2)}a{color:var(--tungsten);text-underline-offset:3px}
code{background:var(--surface);border-radius:var(--badge-radius);padding:2px 6px}
dt{color:var(--muted);font-size:14px}dd{margin:0 0 12px;overflow-wrap:anywhere}
label{display:block;margin:24px 0 8px;color:var(--ink)}
input[type=text],input[type=number],select{width:100%;height:44px;
padding:0 12px;border:1px solid var(--line);border-radius:var(--control-radius);
background:var(--ground);color:var(--ink);font:inherit}
:focus-visible{outline:2px solid var(--tungsten);outline-offset:3px}
.note{margin:8px 0 0;color:var(--ink-2);font-size:14px}
details{margin-top:24px}summary{cursor:pointer;min-height:44px;display:list-item}
.bad{margin:8px 0 0;color:var(--drop);font-size:14px}
.check{display:flex;align-items:center;gap:12px;min-height:44px;margin:24px 0 0}
.check input{width:18px;height:18px;margin:0}
button{margin-top:24px;width:100%;min-height:44px;border:1px solid var(--ink);
border-radius:var(--control-radius);cursor:pointer;background:var(--ink);color:var(--ground);
font:500 16px system-ui,sans-serif}
button:hover{background:color-mix(in srgb,var(--ink) 88%,var(--ground));color:var(--ground)}
@media(max-width:440px){body{padding:24px 20px}h1{font-size:24px}}
</style>"""

_SETUP_HEAD = ('<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width,initial-scale=1">'
               '<meta name="color-scheme" content="light">')

#: 键 -> 输入控件类型。题目、默认值与顺序全部来自 `onboarding.questions()`，
#: 这里只决定同一道题在浏览器里长什么样，不另抄一份字段清单。
_SETUP_WIDGETS = {"host": "select", "port": "number"}


def _document(title: str, body: str) -> str:
    base = (PROJECT_ROOT / "web" / "css" / "01-base.css").read_text(encoding="utf-8")
    tokens = re.search(r":root\s*\{[^}]+\}", base).group(0)
    return (f"{_SETUP_HEAD}<title>{title}</title><style>{tokens}</style>{_SETUP_STYLE}"
            f"</head><body><main>{body}</main></body></html>\n")


def _field_html(
    question, value: str, error: str, note: str,
) -> str:
    key = escape(question.key, quote=True)
    prompt = question.prompt
    if distribution.standalone():
        prompt = {"media_dir": "媒体文件夹", "port": "本机访问端口"}.get(question.key, prompt)
    label = f'<label for="f-{key}">{escape(prompt)}</label>'
    if _SETUP_WIDGETS.get(question.key) == "select":
        options = "".join(
            f'<option value="{escape(choice, quote=True)}"'
            f'{" selected" if choice == value else ""}>{escape(text)}</option>'
            for choice, text in onboarding.HOST_OPTIONS
        )
        control = f'<select id="f-{key}" name="{key}">{options}</select>'
    else:
        kind = _SETUP_WIDGETS.get(question.key, "text")
        control = (f'<input id="f-{key}" name="{key}" type="{kind}" required autocomplete="off" '
                   f'aria-invalid="{"true" if error else "false"}" '
                   f'value="{escape(value, quote=True)}">')
    tail = f'<p class="note">{escape(note)}</p>' if note else ""
    tail += f'<p class="bad" role="alert">{escape(error)}</p>' if error else ""
    return label + control + tail


def setup_page(
    config, *, windows: bool, values: dict[str, str] | None = None,
    errors: dict[str, str] | None = None, scan_now: bool = True,
) -> str:
    """首次运行表单。题目、默认值与顺序全部来自 `onboarding.questions()`。

    校验失败时带着 `values` 和 `errors` 重新渲染：已经填对的几项不能让人再填一遍，
    错在哪一项也要写在那一项底下，而不是页首一句「有字段不合法」。
    """
    values = values or {}
    errors = errors or {}
    asked = onboarding.questions(config, windows=windows)
    fields = []
    if errors.get("data_root"):
        fields.append(f'<p class="bad" role="alert">{escape(errors["data_root"])}</p>')
    for question in asked:
        value = values.get(question.key, question.default)
        if distribution.standalone() and question.key in {"data_root", "host", "mdns_name"}:
            value = {"data_root": str(config.data_root), "host": "1",
                     "mdns_name": config.server.mdns_name}[question.key]
            fields.append(f'<input type="hidden" name="{question.key}" value="{escape(value, quote=True)}">')
            continue
        note = ""
        if question.key == "media_dir" and not windows:
            note = onboarding.mounts_explanation(value or "你在上面填的目录")
        field = _field_html(question, value, errors.get(question.key, ""), note)
        if distribution.standalone() and question.key == "port":
            opened = " open" if errors.get("port") else ""
            field = f'<details{opened}><summary>高级设置</summary>{field}</details>'
        fields.append(field)
    media_value = values.get("media_dir") or next(
        (q.default for q in asked if q.key == "media_dir"), "") or "这个目录"
    scan_label = onboarding.SCAN_PROMPT.format(target=media_value)
    if distribution.standalone():
        scan_label = "完成设置后扫描媒体文件夹"
    body = (
        "<h1>欢迎使用 Peach</h1>"
        "<p>选择一个媒体文件夹，开始整理你的馆藏。</p>"
        '<form method="post" action="/setup">'
        + "".join(fields)
        + f'<label class="check"><input type="checkbox" name="scan_now" value="y"'
        + (" checked" if scan_now else "")
        + f'>{escape(scan_label)}</label>'
        '<p class="note">扫描只读取文件名、大小和修改时间，不改动任何媒体文件。</p>'
        '<button type="submit">完成设置</button></form>'
    )
    return _document("Peach · 首次运行", body)


def setup_done_page(applied, *, windows: bool, scan_requested: bool) -> str:
    """成功页：接下来会自动发生什么，以及口令在哪。口令本身不显示在页面上。"""
    tree = applied.tree
    config = applied.config
    if distribution.standalone():
        destination = escape(_normal_url(config), quote=True)
        scan = "首次扫描已排队。" if scan_requested else "你可以稍后在配置界面开始扫描。"
        return _document("Peach · 设置完成",
                         '<h1>设置完成</h1><p>正在启动你的馆藏。' + scan + '</p>'
                         f'<p><a href="{destination}">进入 Peach</a></p>'
                         f'<meta http-equiv="refresh" content="8;url={destination}">')
    ledger = (f"账本已存在，没有动它：{tree.database}" if tree.ledger_existed
              else f"账本：{tree.database}（已应用 {tree.migrations} 个迁移）")
    ca = (f"本机 CA：{tree.ca_cert}" if tree.ca_cert is not None
          else f"未生成本机 CA（{tree.ca_error}）；装好 openssl 后跑 "
               "<code>peach init --force</code> 补上。局域网设备要装这份 CA 才不报证书错。")
    scan = ("<li>首次扫描已排队，托盘会在服务起来之后在后台跑，期间页面照常能用。</li>"
            if scan_requested else
            "<li>没有请求首次扫描；要扫就跑 <code>peach scan local</code>。</li>")
    mounts = ("" if windows else
              f"<p>{escape(onboarding.mounts_explanation(config.mounts.get('local', '')))}</p>")
    body = (
        "<h1>设置完成</h1>"
        "<p>托盘正在停掉这条引导服务，改用正常的 Peach 服务；这个页面几秒后就会连不上，"
        f"届时打开 <code>{escape(_normal_url(config))}</code> 即可。</p>"
        "<ul>"
        f"<li>{escape(ledger)}</li>"
        f"<li>{ca}</li>"
        f"<li>访问口令文件：<code>{escape(str(tree.token_path))}</code>；"
        "口令内容用 <code>peach token</code> 看，别的设备第一次访问时贴进登录页。</li>"
        f"{scan}"
        "</ul>"
        f"{mounts}"
        "<dl>"
        f"<dt>数据根</dt><dd>{escape(str(config.data_root))}</dd>"
        f"<dt>设置文件</dt><dd>{escape(str(applied.settings_path))}</dd>"
        "</dl>"
    )
    return _document("Peach · 设置完成", body)


def _normal_url(config) -> str:
    """设置完成之后正常服务的地址。仅本机就给回环，局域网给 `<名字>.local`。"""
    if config.server.host in _LOOPBACK:
        return f"http://127.0.0.1:{config.server.port}/"
    return f"https://{config.server.mdns_name}.local/"


def asset_response(request: Request, path: Path, media: str) -> Response:
    """页面资产用 ETag 复验代替 no-store，`/app.js`、`/js/`、`/dist/` 共用。

    `/app.css` 拼多份分区，ETag 口径见 `stylesheet_response()`，其余照这里。

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


#: 拆分后的样式表分区。层叠顺序就是文件名顺序，所以每份都带两位数前缀；
#: 名字判据和 `/js/`、`/dist/` 同口径，不接受分隔符。清单由 `tests/test_web_ui.py` 钉住。
CSS_PART_NAME = re.compile(r"\d{2}-[a-z0-9-]+\.css")


def css_parts(web: Path) -> list[Path]:
    """`web/css/` 下的样式分区，已按层叠顺序排好。"""
    return sorted(path for path in (web / "css").glob("*.css")
                  if CSS_PART_NAME.fullmatch(path.name))


def stylesheet_response(request: Request, web: Path) -> Response:
    """`/app.css`：把 `web/css/` 的分区按顺序拼成一份交付。

    样式表拆成分区是为了让改动落在互不重叠的文件上——一整份两千多行的样式表，
    两个分支各改一处也几乎必然撞在一起。但拆开只是仓库里的事：页面仍然只取一份
    `/app.css`，不给首屏加二十来个阻塞请求，层叠顺序也不必写进 `index.html`。

    ETag 不能照 `asset_response()` 只看单个文件的 mtime 和字节数，改任何一份分区
    都要让它失效，所以取全部分区的 (mtime_ns, 字节数) 摘要。仍然不读文件内容。
    """
    parts = css_parts(web)
    if not parts:
        return PlainTextResponse("missing", status_code=404)
    stamp = "|".join(
        f"{path.name}:{stat.st_mtime_ns:x}:{stat.st_size:x}"
        for path, stat in ((path, path.stat()) for path in parts)
    )
    etag = f'"peach-css-{hashlib.sha256(stamp.encode()).hexdigest()[:16]}"'
    if request.headers.get("if-none-match") == etag:
        response: Response = Response(status_code=304)
    else:
        response = Response(b"".join(path.read_bytes() for path in parts),
                            media_type="text/css; charset=utf-8")
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
        # 未配置不是错误状态：服务照常起，首页变成首次运行表单。
        return HTMLResponse(setup_page(settings_file.active(), windows=os.name == "nt"))
    if not settings.page_path.is_file():
        return PlainTextResponse("Peach page missing", status_code=500)
    response = FileResponse(settings.page_path, media_type="text/html")
    response.headers["Cache-Control"] = "no-store"
    set_auth_cookie(response, request)
    return response


@router.post("/setup")
async def setup_submit(request: Request):
    """首次运行表单的提交端点。落盘逻辑全在 `peach.onboarding`，这里只做守卫和渲染。

    三道守卫，形态各不相同因为原因各不相同：已经配置过的机器上这个端点根本不存在
    （404，不是「禁止」——把它做成一条可探测的 403 等于对外宣告这里有个初始化入口）；
    非回环调用方是 403（引导服务只绑 127.0.0.1，能走到这里说明有人转发了它）；
    设置文件已经在了是 409（并发提交或刷新重发，不能覆盖别人刚写好的那份）。

    扫描不在这里跑：这条引导服务在设置完成的那一刻就会被托盘停掉，跑在它进程里的
    扫描会跟着一起死。这里只写一个标记，由托盘切到正常服务之后消费。
    """
    settings = request.app.state.settings
    if settings.configured:
        raise HTTPException(status_code=404, detail="not found")
    host = request.client.host if request.client else ""
    if host not in _LOOPBACK:
        raise HTTPException(status_code=403, detail="setup is loopback-only")
    if distribution.standalone() and request.url.hostname not in _LOOPBACK:
        raise HTTPException(status_code=403, detail="请使用本机地址打开设置")
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(status_code=403, detail="请从 Peach 设置页提交")

    windows = os.name == "nt"
    form = parse_qs((await request.body()).decode("utf-8", "replace"), keep_blank_values=True)
    submitted = {key: (value or [""])[0] for key, value in form.items()}
    scan_now = "scan_now" in form

    config = settings_file.active()
    if distribution.standalone():
        submitted.update(data_root=str(config.data_root), host="1",
                         mdns_name=config.server.mdns_name)
    answers, errors = _read_answers(config, submitted, windows=windows)
    if distribution.standalone() and answers is not None:
        try:
            onboarding.check_available_port(answers.port, request.url.port or 80)
        except ValueError as exc:
            errors["port"] = str(exc)
    if errors:
        return HTMLResponse(
            setup_page(config, windows=windows, values=submitted, errors=errors,
                       scan_now=scan_now),
            status_code=400,
        )
    # 数据根决定设置文件在哪，所以拿到它之后要按它重新解析一次，不能沿用进程启动
    # 那一刻按发现顺序算出来的这份。
    resolved, _broken = onboarding.resolve_config(answers.data_root)
    if resolved.path.exists():
        raise HTTPException(status_code=409, detail="settings file already exists")
    try:
        applied = onboarding.apply(resolved, answers, windows=windows)
    except (OSError, RuntimeError) as exc:
        return HTMLResponse(setup_page(config, windows=windows, values=submitted,
                                      errors={"data_root": str(exc)}, scan_now=scan_now), status_code=400)
    if scan_now:
        onboarding.request_first_scan(applied.config)
    response = HTMLResponse(setup_done_page(applied, windows=windows, scan_requested=scan_now))
    if distribution.standalone():
        response.set_cookie("tok", auth.read_token(applied.config.directory("secrets")),
                            httponly=True, samesite="strict", max_age=31536000)
        response.headers["Cache-Control"] = "no-store"
    return response


def _read_answers(
    config, submitted: dict[str, str], *, windows: bool,
) -> tuple[object, dict[str, str]]:
    """逐字段校验，错误按字段收集。校验器和 CLI 问答用的是同一批。"""
    values: dict[str, object] = {}
    errors: dict[str, str] = {}
    for question in onboarding.questions(config, windows=windows):
        raw = submitted.get(question.key, "")
        try:
            values[question.key] = question.validate(raw if raw.strip() else question.default)
        except ValueError as exc:
            errors[question.key] = str(exc)
    if errors:
        return None, errors
    return onboarding.Answers(**values), {}  # type: ignore[arg-type]


@router.api_route("/app.css", methods=["GET", "HEAD"])
@router.api_route("/app.js", methods=["GET", "HEAD"])
def app_asset(request: Request, args: dict[str, str] = Depends(require_asset_auth)):
    """页面拆出来的样式与入口脚本。样式在 `web/css/`，脚本和 index.html 同目录，同一套口令。

    仍然没有构建步骤：`app.js` 现在是 ES module，浏览器原生解析 import，
    拆出来的模块见下面的 `/js/{name}`。页面里没有任何内联事件处理器，
    全部是 `.onclick=` 属性赋值，所以顶层声明不再是全局也不影响绑定。
    """
    name = request.url.path.lstrip("/")
    web = request.app.state.settings.page_path.parent
    if name == "app.css":
        return stylesheet_response(request, web)
    path = web / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    return asset_response(request, path, "text/javascript")


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
@router.api_route("/agencies/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/performers", methods=["GET", "HEAD"])
@router.api_route("/creators", methods=["GET", "HEAD"])
@router.api_route("/studios", methods=["GET", "HEAD"])
@router.api_route("/agencies", methods=["GET", "HEAD"])
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
