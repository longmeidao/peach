import hmac
import asyncio
import html
import hashlib
import logging
import os
import re
import uuid
import httpx
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from browserexport.common import BrowserexportError

from . import __version__, web_contract, web_follow
from .config import LOCATION_ROOT_DECLARATIONS, PROJECT_ROOT, PeachSettings
from .ffmpeg import FFmpegResolver
from .follow import FollowSourceError
from .follow_scheduler import FollowUpdateScheduler
from .follow_avatar import resolve_official_avatar
from .follow_covers import FollowCoverService, FollowCoverUnavailable
from .follow_store import FollowStore
from .follow_stream import FollowMediaResolver, FollowMediaUnavailable
from .http import HttpxTransport
from .media import (
    FilesystemBackend,
    MediaEngine,
    MediaNotFound,
    MediaOffline,
    MediaUnavailable,
    StashAdapter,
)
from .mdns import create_mdns_publisher
from .interaction import reveal_path
from .platform import (
    is_unmapped,
    root_online,
    translate_ledger_path,
)
from .previews import PhotoThumbnailService, PreviewService, PreviewUnavailable
from .providers import OpenCodeGoClient, ProviderUnavailable, default_registry
from .repository import LedgerDatabase, LedgerRepository
from .review_mirror import ReviewMirror
from .segments import (
    HlsSegmentService,
    SegmentCancelled,
    SegmentUnavailable,
    build_hls_playlist,
)
from .stash import StashClient
from .streaming import CancellableFileResponse, StreamSessionRegistry
from .sync import LedgerSync
from .transcodes import TranscodeCancelled, TranscodeService, TranscodeUnavailable
from .taste_history import analyze_history, import_history_exports, write_manifest


LOGGER = logging.getLogger(__name__)


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


def _source_status() -> list[dict[str, Any]]:
    """按 ledger 的 `asset.location` 逐个报告来源可达性。

    脱盘是来源级的：本地硬盘拔掉时 115/PikPak 照常可播，反过来也一样。
    """
    rows: list[dict[str, Any]] = []
    for location, declared in LOCATION_ROOT_DECLARATIONS.items():
        resolved = translate_ledger_path(declared)
        mapped = not is_unmapped(resolved)
        rows.append({
            "location": location,
            "declared": declared,
            "resolved": str(resolved) if mapped else None,
            "mapped": mapped,
            "online": bool(mapped and root_online(resolved)),
        })
    # 在线资源是 URL，不依赖任何挂载点。
    rows.append({
        "location": "online", "declared": None, "resolved": None,
        "mapped": True, "online": True,
    })
    return rows


def _offline_response(exc: MediaOffline) -> JSONResponse:
    """脱盘：来源盘整体不在，客户端据此显示「脱盘模式」而不是当成文件丢失。"""
    response = JSONResponse(
        {"error": "offline", "source": exc.source, "id": exc.asset_id},
        status_code=503,
    )
    response.headers["X-Peach-Offline"] = "1"
    return response


#: 生成物与外部头像的缓存时长。这些端点按 asset / follow_item id 取图，内容换了
#: id 也就换了（封面重生成会写新文件、头像换了会解析到新 URL），所以一天太短——
#: 用户实测「基本不可能变动」。不加 immutable：那会让浏览器连刷新都不再回源，
#: 万一真要换图就只能等过期。
MEDIA_CACHE_SECONDS = 30 * 24 * 3600


def create_app(
    settings: PeachSettings | None = None,
    sync: LedgerSync | None = None,
    review_mirror: ReviewMirror | None = None,
) -> FastAPI:
    """`sync` 由 CLI 注入。测试直接建 app 时不传，复制与只读闸门整体不参与。"""
    settings = settings or PeachSettings()
    database = LedgerDatabase(settings.db_path)
    contract = web_contract.WebContract(
        settings.db_path, settings.snapshot_root, settings.legacy_snapshot_roots,
        candidate_root=settings.candidate_root,
        cover_root=settings.cover_root,
        avatar_root=settings.avatar_root,
        logo_root=settings.logo_root,
        poster_root=settings.poster_root,
        photo_root=settings.photo_root,
        transcode_root=settings.transcode_root,
        stream_root=settings.stream_root,
        follow_state_root=settings.follow_state_root,
        taste_history_root=settings.taste_history_output_root,
        taste_history_store=settings.taste_history_store,
        taste_history_import_root=settings.taste_history_import_root,
        taste_history_manifest=settings.taste_history_manifest,
        database=database,
    )
    repository = LedgerRepository(database)
    resolver = FFmpegResolver(settings.ffmpeg_root)
    http_transport = HttpxTransport()
    follow_media_resolver = FollowMediaResolver(http_transport).with_credential_loader(
        lambda provider: web_follow._credential_store(contract).load(provider))
    follow_cover_service = FollowCoverService(
        resolver, follow_media_resolver, settings.poster_root / "follow")
    filesystem = FilesystemBackend(
        settings.allowed_media_roots,
        settings.snapshot_root,
        settings.legacy_snapshot_roots,
    )
    media_engine = MediaEngine(
        repository,
        filesystem,
        (StashAdapter(StashClient(transport=http_transport)),),
    )
    preview_service = PreviewService(
        repository, resolver, settings.snapshot_root, settings.poster_root,
        settings.avatar_root, settings.logo_root, settings.legacy_snapshot_roots,
    )
    photo_service = PhotoThumbnailService(settings.photo_root)
    transcode_service = TranscodeService(resolver, settings.transcode_root)
    hls_plan_executor = ThreadPoolExecutor(
        max_workers=2, thread_name_prefix="PeachHlsPlan",
    )
    hls_service = HlsSegmentService(resolver, settings.stream_root)
    mdns = create_mdns_publisher(
        settings.mdns_name, settings.mdns_port, secure=settings.tls_enabled,
        address=settings.mdns_address,
    ) if settings.mdns_enabled else None
    providers = default_registry()
    opencode_go = OpenCodeGoClient(transport=http_transport)
    review_mirror = review_mirror or ReviewMirror(
        settings.review_writer_origin,
        settings.review_writer_ca,
        settings.review_mirror_cache,
        token=settings.token,
        proxy=settings.review_writer_proxy,
    )
    follow_scheduler = FollowUpdateScheduler(
        settings.follow_state_root,
        lambda: web_follow.w_follow_check(contract, {"automatic": True}),
        available=sync is None or not sync.read_only,
    )
    contract.follow_scheduler = follow_scheduler

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if sync is not None:
            sync.start()
        follow_scheduler.start()
        if mdns is not None:
            try:
                await asyncio.to_thread(mdns.start)
            except Exception:
                mdns.status = "unavailable"
                logging.getLogger(__name__).exception("mDNS publication failed")
        try:
            yield
        finally:
            follow_scheduler.stop()
            if mdns is not None:
                await asyncio.to_thread(mdns.stop)
            if sync is not None:
                await asyncio.to_thread(sync.stop)
            http_transport.close()
            hls_plan_executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(
        title="Peach API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.database = database
    app.state.web_contract = contract
    app.state.repository = repository
    app.state.media_engine = media_engine
    app.state.preview_service = preview_service
    app.state.photo_service = photo_service
    app.state.transcode_service = transcode_service
    app.state.hls_plan_executor = hls_plan_executor
    app.state.hls_service = hls_service
    app.state.mdns = mdns
    app.state.providers = providers
    app.state.opencode_go = opencode_go
    app.state.review_mirror = review_mirror
    app.state.http_transport = http_transport
    app.state.follow_media_resolver = follow_media_resolver
    app.state.follow_cover_service = follow_cover_service
    app.state.follow_scheduler = follow_scheduler
    stream_sessions = StreamSessionRegistry()
    app.state.stream_sessions = stream_sessions
    app.state.sync = sync

    # 媒体三异常的统一出口，路由里不再手抄同一组 try/except。
    # 404/503/404 是逐个异常的状态码契约，不许并成一种。
    @app.exception_handler(MediaNotFound)
    def _media_not_found_handler(request: Request, exc: MediaNotFound):
        return JSONResponse({"error": "no such id"}, status_code=404)

    @app.exception_handler(MediaOffline)
    def _media_offline_handler(request: Request, exc: MediaOffline):
        return _offline_response(exc)

    @app.exception_handler(MediaUnavailable)
    def _media_unavailable_handler(request: Request, exc: MediaUnavailable):
        return JSONResponse({"error": "unavailable"}, status_code=404)

    # 401 有三种形态，按路由类分组保留（不许统一成一种）：页面路由跳登录页，
    # 页面资产返回 PlainText 提示，API 与媒体路由返回 JSON。
    @app.exception_handler(PageLoginRequired)
    def _page_login_required_handler(request: Request, exc: PageLoginRequired):
        return RedirectResponse(
            "/login?next=" + quote(exc.next_path or "/", safe="/"), status_code=303,
        )

    @app.exception_handler(AssetLoginRequired)
    def _asset_login_required_handler(request: Request, exc: AssetLoginRequired):
        return PlainTextResponse("需要 ?t=口令", status_code=401)

    @app.exception_handler(HTTPException)
    def _http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)

    def require_auth(request: Request) -> dict[str, str]:
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            raise HTTPException(status_code=401, detail="unauthorized")
        return args

    def require_page_auth(request: Request) -> dict[str, str]:
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            raise PageLoginRequired(request.url.path or "/")
        return args

    def require_asset_auth(request: Request) -> dict[str, str]:
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            raise AssetLoginRequired()
        return args

    def set_auth_cookie(response: Response, request: Request) -> None:
        if settings.token:
            response.set_cookie(
                "tok", settings.token, max_age=31536000, path="/", httponly=True,
                samesite="lax", secure=request.url.scheme == "https",
            )

    # 第三方前端依赖固定版本并随 Peach 自托管；局域网断网时仍可播放。
    app.mount(
        "/vendor",
        StaticFiles(directory=settings.vendor_path, check_dir=False),
        name="vendor",
    )

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/vendor/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    # 健康检查常被 HEAD 探测（`curl -I`、各种 uptime 工具）。本仓库其他公开端点
    # 都显式声明了 GET+HEAD，只有这个漏了，HEAD 会拿到 405。
    @app.api_route("/healthz", methods=["GET", "HEAD"])
    def healthz() -> dict[str, Any]:
        # 不探测共享目录或迁移数据库；健康检查必须无副作用。
        ffmpeg = resolver.ffmpeg()
        read_only = bool(sync is not None and sync.read_only)
        return {"ok": True, "service": "peach-api", "version": __version__, "mode": "fastapi",
                "db": "available" if settings.db_path.is_file() else "missing",
                "ffmpeg": ffmpeg.source if ffmpeg else "unavailable",
                "mdns": mdns.status if mdns is not None else "disabled",
                "mdns_backend": mdns.backend if mdns is not None else None,
                "mdns_service": mdns.name if mdns is not None else None,
                "mdns_service_host": mdns.hostname if mdns is not None else None,
                "mdns_address": mdns.address if mdns is not None else None,
                "ledger_sync": sync.status if sync is not None else "disabled",
                "ledger_read_only": read_only,
                "ledger_read_only_message": sync.read_only_message if read_only else None,
                "ledger_writer_origin": settings.review_writer_origin if read_only else None,
                "scheme": "https" if settings.tls_enabled else "http"}

    def login_html(next_path: str, *, invalid: bool = False) -> str:
        safe_next = html.escape(next_path, quote=True)
        error = '<p role="alert">口令不正确</p>' if invalid else ""
        return (
            '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="dark"><title>登录 Peach</title>'
            '<style>'
            '*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#080A0D;color:#f5f7fb}'
            'body{min-height:100dvh;display:grid;place-items:center;padding:24px;font:15px/1.45 system-ui,sans-serif}'
            'main{width:min(360px,100%);padding:30px;border:1px solid rgba(255,255,255,.12);border-radius:20px;'
            'background:rgba(30,32,37,.9);box-shadow:0 24px 80px rgba(0,0,0,.48)}'
            '.brand{display:flex;align-items:center;gap:12px;margin-bottom:24px}.brand img{width:48px;height:48px}'
            'h1{margin:0;font-size:24px;letter-spacing:.02em}label{display:grid;gap:8px;color:#b8bec9}'
            'input{width:100%;height:44px;border:1px solid rgba(255,255,255,.16);border-radius:11px;'
            'background:#0b0d12;color:#fff;padding:0 13px;font:inherit;outline:none}'
            'input:focus{border-color:#ff8b70;box-shadow:0 0 0 3px rgba(255,139,112,.16)}'
            'button{width:100%;height:44px;margin-top:16px;border:0;border-radius:11px;cursor:pointer;'
            'background:linear-gradient(135deg,#ff9a76,#f2557b);color:#130609;font:700 15px system-ui,sans-serif}'
            'button:hover{filter:brightness(1.06)}p[role=alert]{margin:0 0 14px;color:#ff9a9a}'
            '</style><body><main><div class="brand"><img src="/peach-logo.png" alt=""><h1>Peach</h1></div>'
            f'{error}<form method="post" action="/login">'
            '<label>口令 <input name="token" type="password" '
            'autocomplete="current-password" required></label>'
            f'<input name="next" type="hidden" value="{safe_next}">'
            '<button type="submit">登录</button></form></main></body></html>'
        )

    @app.get("/login", response_class=HTMLResponse)
    def login(request: Request, next: str = "/"):
        next_path = next if next.startswith("/") and not next.startswith("//") else "/"
        if _authorized(request, settings.token, _first_query_values(request)):
            return RedirectResponse(next_path, status_code=303)
        return HTMLResponse(login_html(next_path))

    @app.post("/login")
    async def login_submit(request: Request):
        form = parse_qs(
            (await request.body()).decode("utf-8", "replace"), keep_blank_values=True,
        )
        supplied = (form.get("token") or [""])[0]
        next_path = (form.get("next") or ["/"])[0]
        if not next_path.startswith("/") or next_path.startswith("//"):
            next_path = "/"
        if settings.token and not hmac.compare_digest(str(supplied), settings.token):
            return HTMLResponse(login_html(next_path, invalid=True), status_code=401)
        response = RedirectResponse(next_path, status_code=303)
        set_auth_cookie(response, request)
        return response

    @app.api_route("/", methods=["GET", "HEAD"])
    def index(request: Request, args: dict[str, str] = Depends(require_page_auth)):
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

    @app.api_route("/app.css", methods=["GET", "HEAD"])
    @app.api_route("/app.js", methods=["GET", "HEAD"])
    def app_asset(request: Request, args: dict[str, str] = Depends(require_asset_auth)):
        """页面拆出来的样式与入口脚本。和 index.html 同目录，同一套口令。

        仍然没有构建步骤：`app.js` 现在是 ES module，浏览器原生解析 import，
        拆出来的模块见下面的 `/js/{name}`。页面里没有任何内联事件处理器，
        全部是 `.onclick=` 属性赋值，所以顶层声明不再是全局也不影响绑定。
        """
        name = request.url.path.lstrip("/")
        path = settings.page_path.parent / name
        if not path.is_file():
            return PlainTextResponse("missing", status_code=404)
        media = "text/css" if name.endswith(".css") else "text/javascript"
        response = FileResponse(path, media_type=f"{media}; charset=utf-8")
        # 页面本体是 no-store，样式与脚本跟着它一起变，不能被旧缓存钉住。
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.api_route("/js/{name}", methods=["GET", "HEAD"])
    def app_module(name: str, args: dict[str, str] = Depends(require_asset_auth)):
        """`app.js` 拆出来的 ES module。和入口脚本同一套口令与 401 形态。

        文件名严格限制为一层平铺的 `[a-z0-9_-]+.js`：静态路由拼路径是典型的目录
        穿越入口，与其在这里做 resolve 后再比较根目录，不如根本不接受分隔符。
        前端模块规模不大，平铺够用。
        """
        if not re.fullmatch(r"[a-z0-9_-]+\.js", name):
            return PlainTextResponse("bad module name", status_code=404)
        path = settings.page_path.parent / "js" / name
        if not path.is_file():
            return PlainTextResponse("missing", status_code=404)
        response = FileResponse(path, media_type="text/javascript; charset=utf-8")
        # 和 index.html/app.js 同一口径：页面一变模块就跟着变，不能被旧缓存钉住。
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.api_route("/favicon.svg", methods=["GET", "HEAD"])
    def favicon():
        response = Response(web_contract.FAVICON, media_type="image/svg+xml")
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.api_route("/peach-logo.png", methods=["GET", "HEAD"])
    def peach_logo():
        return FileResponse(PROJECT_ROOT / "resources" / "peach-logo.png", media_type="image/png")

    @app.api_route("/stream", methods=["GET", "HEAD"])
    def stream(request: Request, id: int, session: str = "", args: dict[str, str] = Depends(require_auth)):
        asset = media_engine.asset(id)
        path = media_engine.filesystem.file_for(asset, thumbnail=False)
        try:
            path, transcoded = transcode_service.browser_path(
                id, path, session=session, registry=stream_sessions,
            )
        except TranscodeCancelled:
            return Response(status_code=410, headers={"Cache-Control": "no-store"})
        except TranscodeUnavailable:
            logging.getLogger(__name__).exception("browser transcode failed for asset %s", id)
            return JSONResponse({"error": "transcode unavailable"}, status_code=503)
        media_type = "video/mp4" if transcoded else None
        response = (
            CancellableFileResponse(
                path, session=session, registry=stream_sessions, media_type=media_type,
            )
            if session else FileResponse(path, media_type=media_type)
        )
        if transcoded:
            response.headers["X-Peach-Transcoded"] = "1"
        response.headers["Cache-Control"] = "no-store"
        return response

    def _hls_plan(asset_id: int, session: str = ""):
        """解析 HLS 的片源路径与关键帧分片计划；任何一步不成立就返回 None 走 Range。"""
        asset = media_engine.asset(asset_id)
        # 播放列表和分片端点本身就是 HLS 路径，按 ADR-0016 显式要计划，不受默认值影响。
        choice = media_engine.stream_plan(asset_id, mode="hls")
        if choice.protocol != "hls" or not asset.duration:
            return None
        source = media_engine.filesystem.file_for(asset, thumbnail=False)
        source, _ = transcode_service.browser_path(
            asset_id, source, session=session, registry=stream_sessions,
        )
        plan = hls_service.plan(source, asset.duration)
        return None if not plan else (asset, source, plan)

    @app.get("/api/stream-plan")
    def stream_plan(request: Request, id: int, session: str = "", mode: str = "", args: dict[str, str] = Depends(require_auth)):
        if session and len(session) > 128:
            return JSONResponse({"error": "invalid session"}, status_code=400)
        if session and stream_sessions.is_cancelled(session):
            return JSONResponse({"error": "stream cancelled"}, status_code=410)
        asset = media_engine.asset(id)
        plan = media_engine.stream_plan(id, mode=mode or "auto")
        # 只有真的能读出关键帧才宣告 HLS，否则客户端会拿到一个必然 404 的播放列表。
        resolved = _hls_plan(id) if plan.protocol == "hls" else None
        if resolved and session:
            return {
                "id": id,
                "protocol": "hls",
                "mime_type": plan.mime_type,
                "duration": asset.duration,
                "segment_seconds": plan.segment_seconds,
                "segments": len(resolved[2]),
                "src": f"/stream/hls/{id}/index.m3u8?session={quote(session, safe='')}",
                "reason": plan.reason,
            }
        source = f"/stream?id={id}"
        if session:
            source += f"&session={quote(session, safe='')}"
        return {
            "id": id,
            "protocol": "range",
            "mime_type": plan.mime_type,
            "duration": asset.duration,
            "src": source,
            "reason": plan.reason,
        }

    @app.get("/stream/hls/{id}/index.m3u8")
    def hls_playlist(request: Request, id: int, session: str = "", args: dict[str, str] = Depends(require_auth)):
        # 分片必须带 session 才能被取消，播放列表这层就要求它；
        # 否则会生成一份每个分片都必然 400 的目录。
        if not session or len(session) > 128:
            return PlainTextResponse("session required", status_code=400)
        if stream_sessions.is_cancelled(session):
            return PlainTextResponse("stream cancelled", status_code=410)
        try:
            resolved = _hls_plan(id, session)
        except (MediaUnavailable, TranscodeUnavailable):
            return PlainTextResponse("hls unavailable", status_code=404)
        if resolved is None:
            return PlainTextResponse("hls unavailable", status_code=404)
        query = f"?session={quote(session, safe='')}"
        playlist = build_hls_playlist(
            resolved[2], lambda index: f"/stream/hls/{id}/{index}.ts{query}",
        )
        response = PlainTextResponse(playlist, media_type="application/vnd.apple.mpegurl")
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/stream/hls/{id}/{index}.ts")
    async def hls_segment(request: Request, id: int, index: int, session: str = "", args: dict[str, str] = Depends(require_auth)):
        if not session or len(session) > 128:
            return JSONResponse({"error": "invalid session"}, status_code=400)
        if stream_sessions.is_cancelled(session):
            return Response(status_code=410, headers={"Cache-Control": "no-store"})
        try:
            loop = asyncio.get_running_loop()
            resolved = await loop.run_in_executor(
                hls_plan_executor, partial(_hls_plan, id, session),
            )
            if resolved is None:
                return JSONResponse({"error": "hls unavailable"}, status_code=404)
            _, source, plan = resolved
            if index < 0 or index >= len(plan):
                return JSONResponse({"error": "invalid segment"}, status_code=416)
            start, duration = plan[index]
            path = await hls_service.generate(
                source, start, duration, asset_id=id, index=index,
                session=session, registry=stream_sessions,
            )
        except SegmentCancelled:
            return Response(status_code=410, headers={"Cache-Control": "no-store"})
        except TranscodeCancelled:
            return Response(status_code=410, headers={"Cache-Control": "no-store"})
        except TranscodeUnavailable:
            logging.getLogger(__name__).exception("browser transcode failed for asset %s", id)
            return JSONResponse({"error": "transcode unavailable"}, status_code=503)
        except SegmentUnavailable:
            logging.getLogger(__name__).exception("HLS segment failed for asset %s", id)
            return JSONResponse({"error": "segment unavailable"}, status_code=503)
        # 片段现在留在缓存里而不是随响应删除：回放、重连和多设备都会重复请求同一段，
        # 每次重跑 FFmpeg 等于让 CloudDrive 再预取一次块。
        response = FileResponse(path, media_type="video/mp2t")
        response.headers["Cache-Control"] = f"private, max-age={MEDIA_CACHE_SECONDS}"
        response.headers["X-Peach-HLS-Segment"] = "1"
        return response

    @app.post("/api/stream-cancel")
    async def stream_cancel(request: Request, session: str, args: dict[str, str] = Depends(require_auth)):
        if not session or len(session) > 128:
            return JSONResponse({"error": "invalid session"}, status_code=400)
        cancelled = stream_sessions.cancel(session)
        return JSONResponse({"ok": True, "cancelled": cancelled})

    @app.api_route("/thumb", methods=["GET", "HEAD"])
    def thumbnail(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
        path = media_engine.file_for(id, thumbnail=True)
        response = FileResponse(path)
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/photo", methods=["GET", "HEAD"])
    def photo(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
        """图片资产原图。灯箱看大图用这条，瀑布流一律走 `/photo-thumb`。"""
        path = media_engine.file_for(id)
        response = FileResponse(path)
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/photo-thumb", methods=["GET", "HEAD"])
    def photo_thumb(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
        source = media_engine.file_for(id)
        try:
            path = photo_service.thumbnail(id, source)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/poster", methods=["GET", "HEAD"])
    def poster(request: Request, id: int, c: int = 4, args: dict[str, str] = Depends(require_auth)):
        try:
            path = preview_service.poster(id, c)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/cover", methods=["GET", "HEAD"])
    def cover(request: Request, code: str = "", args: dict[str, str] = Depends(require_auth)):
        """官方封套原图。存原图不裁：4:3 与 16:9 两种版式在界面上按比例取景。"""
        path = contract.cover_path(code)
        if path is None:
            return JSONResponse({"error": "no cover"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/endcard-frame", methods=["GET", "HEAD"])
    def endcard_frame(request: Request, id: int, name: str, args: dict[str, str] = Depends(require_auth)):
        """Serve only generated OCR evidence frames, never a client-provided path."""
        if (id <= 0 or not name.endswith(".png") or "/" in name or "\\" in name
                or name.startswith(".")):
            return JSONResponse({"error": "invalid frame"}, status_code=400)
        root = (settings.candidate_root / "endcard-evidence" / str(id)).resolve()
        path = (root / name).resolve()
        if path.parent != root or not path.is_file():
            return JSONResponse({"error": "no frame"}, status_code=404)
        response = FileResponse(path, media_type="image/png")
        response.headers["Cache-Control"] = f"private, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/avatar", methods=["GET", "HEAD"])
    def avatar(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
        try:
            path = preview_service.avatar(id)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/follow-avatar", methods=["GET", "HEAD"])
    def follow_avatar(request: Request, service: str, id: str, args: dict[str, str] = Depends(require_auth)):
        """Resolve an official creator avatar, then let the image CDN serve it."""
        try:
            target = resolve_official_avatar(service, id)
        except (OSError, FollowSourceError):
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = RedirectResponse(target, status_code=307)
        response.headers["Cache-Control"] = f"private, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/follow-stream", methods=["GET", "HEAD"])
    def follow_stream(request: Request, id: int, media: int | None = None, args: dict[str, str] = Depends(require_auth)):
        """Play a remote follow candidate through Peach without exposing its upstream URL."""
        with database.read_connection() as connection:
            item = FollowStore(lambda: connection).item(id)
        if item is None:
            return JSONResponse({"error": "no such follow item"}, status_code=404)
        try:
            target = follow_media_resolver.resolve(item, media)
            headers = {
                "User-Agent": "Peach/0.2",
                "Accept": request.headers.get("accept", "*/*"),
                "Accept-Encoding": "identity",
            }
            if target.referer:
                headers["Referer"] = target.referer
            headers.update(target.headers or {})
            for name in ("range", "if-range"):
                if request.headers.get(name):
                    headers[name.title()] = request.headers[name]
            upstream_request = http_transport.client.build_request(
                request.method, target.url, headers=headers,
            )
            upstream = http_transport.client.send(upstream_request, stream=True)
        except FollowMediaUnavailable as error:
            return JSONResponse({"error": str(error)}, status_code=404)
        except (OSError, httpx.HTTPError):
            logging.getLogger(__name__).exception("follow media proxy failed for item %s", id)
            return JSONResponse({"error": "follow media unavailable"}, status_code=502)

        forwarded = {}
        for name in ("accept-ranges", "content-length", "content-range", "content-type",
                     "etag", "last-modified"):
            value = upstream.headers.get(name)
            if value:
                forwarded[name] = value
        forwarded["cache-control"] = "no-store"
        if request.method == "HEAD":
            status = upstream.status_code
            upstream.close()
            return Response(status_code=status, headers=forwarded)

        def body():
            try:
                yield from upstream.iter_raw()
            finally:
                upstream.close()

        return StreamingResponse(
            body(), status_code=upstream.status_code, headers=forwarded,
        )

    @app.api_route("/follow-cover", methods=["GET", "HEAD"])
    def follow_cover(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
        """Return a cached clear still for a follow video; keep its URL server-side."""
        with database.read_connection() as connection:
            item = FollowStore(lambda: connection).item(id)
        if item is None:
            return JSONResponse({"error": "no such follow item"}, status_code=404)
        try:
            path = request.app.state.follow_cover_service.cover(item)
        except FollowCoverUnavailable:
            # Paheal itself only has this low-resolution fallback. A temporary FFmpeg or
            # network failure should degrade to the old cover instead of leaving a hole.
            if str(item.thumb_url or "").startswith("https://"):
                return RedirectResponse(str(item.thumb_url), status_code=307)
            return JSONResponse({"error": "follow cover unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.api_route("/logo", methods=["GET", "HEAD"])
    def logo(request: Request, studio: str = "", args: dict[str, str] = Depends(require_auth)):
        try:
            path, content_type = preview_service.logo(studio)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type=content_type)
        # Logo 可以缓存，但文件会在人工批准或重新归一后原地替换。固定 URL 若缓存
        # 一整天，浏览器会继续显示旧图；no-cache 会复用本地副本并用 ETag 重验。
        response.headers["Cache-Control"] = "public, no-cache"
        return response

    @app.api_route("/item/{item_id}", methods=["GET", "HEAD"])
    @app.api_route("/mix/{seed_id}/{mix_item_id}", methods=["GET", "HEAD"])
    @app.api_route("/parts/{part_seed_id}/{part_item_id}", methods=["GET", "HEAD"])
    @app.api_route("/playlists", methods=["GET", "HEAD"])
    @app.api_route("/playlists/{playlist_id}/{playlist_item_id}", methods=["GET", "HEAD"])
    @app.api_route("/performers/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/studios/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/creators/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/series/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/performers", methods=["GET", "HEAD"])
    @app.api_route("/creators", methods=["GET", "HEAD"])
    @app.api_route("/tags", methods=["GET", "HEAD"])
    @app.api_route("/unseen", methods=["GET", "HEAD"])
    @app.api_route("/watch-later", methods=["GET", "HEAD"])
    @app.api_route("/flagged", methods=["GET", "HEAD"])
    @app.api_route("/junk-files", methods=["GET", "HEAD"])
    @app.api_route("/stats", methods=["GET", "HEAD"])
    @app.api_route("/immerse", methods=["GET", "HEAD"])
    @app.api_route("/trash", methods=["GET", "HEAD"])
    @app.api_route("/review", methods=["GET", "HEAD"])
    @app.api_route("/taste", methods=["GET", "HEAD"])
    @app.api_route("/duplicates", methods=["GET", "HEAD"])
    @app.api_route("/quality-goals", methods=["GET", "HEAD"])
    @app.api_route("/resource-sync", methods=["GET", "HEAD"])
    @app.api_route("/follow", methods=["GET", "HEAD"])
    @app.api_route("/follow-manage", methods=["GET", "HEAD"])
    @app.api_route("/follow/item/{item_id}", methods=["GET", "HEAD"])
    def client_route(request: Request, item_id: int | None = None,
                     seed_id: int | None = None, mix_item_id: int | None = None,
                     part_seed_id: int | None = None, part_item_id: int | None = None,
                     playlist_id: int | None = None, playlist_item_id: int | None = None,
                     kind: str | None = None, name: str | None = None,
                     args: dict[str, str] = Depends(require_page_auth)):
        return index(request, args)

    @app.api_route("/entity-image", methods=["GET", "HEAD"])
    def entity_image(request: Request, kind: str, id: int, args: dict[str, str] = Depends(require_auth)):
        try:
            path, content_type = preview_service.entity_image(kind, id)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type=content_type)
        response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
        return response

    @app.get("/api/providers")
    def provider_health(request: Request, args: dict[str, str] = Depends(require_auth)):
        return providers.health()

    @app.get("/api/sources")
    def source_health(request: Request, args: dict[str, str] = Depends(require_auth)):
        """无副作用的来源可达性。前端据此把脱盘来源的筛选置灰。"""
        rows = _source_status()
        return {
            "ok": True,
            "sources": rows,
            "offline": [row["location"] for row in rows if not row["online"]],
        }

    @app.post("/api/reveal")
    def reveal(request: Request, body: dict[str, Any] = Body(default_factory=dict), args: dict[str, str] = Depends(require_auth)):
        """在本机文件管理器里定位某个资产的源文件。

        用于「跳过去自己整理网盘目录」：A:/B: 是 CloudDrive 挂上来的盘符，在
        资源管理器里和本地目录没有区别。路径一律由服务端按 asset id 查出来——
        `q_item` 刻意不把 `path` 发给前端，这里不能反过来让前端把路径传进来。

        写不进 ledger，所以不受 reader 的只读闸门约束；但它会在**服务端所在的
        机器**上弹窗，从 Mac 浏览时弹在 Windows 那台，也正是文件所在的机器。
        """
        try:
            asset_id = int(body.get("id"))
        except (TypeError, ValueError):
            return JSONResponse({"error": "id must be an integer"}, status_code=400)
        asset = repository.media_asset(asset_id)
        if asset is None or not asset.path:
            return JSONResponse({"error": "not found"}, status_code=404)
        target = translate_ledger_path(asset.path)
        if is_unmapped(target):
            return JSONResponse(
                {"error": "source not mapped", "location": asset.location},
                status_code=409)
        if not target.exists():
            # 文件已经不在了——正是「删完回来同步」的入口，前端据此提示对账。
            return JSONResponse(
                {"error": "file missing", "location": asset.location},
                status_code=410)
        try:
            if not reveal_path(target):
                return JSONResponse({"error": "unsupported platform"}, status_code=501)
        except OSError as error:
            LOGGER.warning("reveal failed for asset %s: %s", asset_id, error)
            return JSONResponse({"error": "reveal failed"}, status_code=500)
        return {"ok": True, "id": asset_id, "location": asset.location}

    @app.get("/api/providers/opencode-go/models")
    def opencode_go_models(request: Request, args: dict[str, str] = Depends(require_auth)):
        try:
            models = opencode_go.list_models()
        except ProviderUnavailable:
            return JSONResponse({"error": "provider unavailable"}, status_code=502)
        return {"ok": True, "provider": "opencode-go", "models": models}

    @app.get("/api/{route:path}")
    def api_get(route: str, args: dict[str, str] = Depends(require_auth)):
        try:
            payload = web_contract.dispatch_api_get(contract, f"/api/{route}", args)
            if route == "review" and sync is not None and sync.read_only:
                payload = review_mirror.resolve(payload)
            return payload
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception:
            LOGGER.exception("unhandled GET contract error for /api/%s", route)
            return JSONResponse({"error": "internal server error"}, status_code=500)

    @app.post("/api/taste/import")
    async def taste_import(
        request: Request,
        _args: dict[str, str] = Depends(require_auth),
    ):
        """Stream one private history export to local storage, then import it.

        This deliberately avoids multipart/form-data and its extra parser dependency.  The
        browser sends the file bytes as-is and provides only a display filename header.
        """
        maximum = 1024 * 1024 * 1024
        try:
            declared = int(request.headers.get("content-length") or 0)
        except ValueError:
            declared = 0
        if declared > maximum:
            return JSONResponse({"error": "导出文件超过 1 GB"}, status_code=413)
        filename = unquote(request.headers.get("x-peach-filename") or "history-export")
        filename = re.sub(r"[^\w.()\-\u3400-\u9fff]+", "-", os.path.basename(filename)).strip(".-")
        filename = filename[-160:] or "history-export"
        root = contract.taste_history_import_root
        root.mkdir(parents=True, exist_ok=True)
        temporary = root / f".{uuid.uuid4().hex}.part"
        imported_target: Path | None = None
        digest = hashlib.sha256()
        size = 0
        try:
            with temporary.open("xb") as handle:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > maximum:
                        raise OverflowError
                    digest.update(chunk)
                    await asyncio.to_thread(handle.write, chunk)
            if not size:
                raise ValueError("导出文件为空")
            target = root / f"{digest.hexdigest()[:12]}-{filename}"
            if target.exists():
                temporary.unlink()
            else:
                os.replace(temporary, target)
                imported_target = target
            results = await asyncio.to_thread(
                import_history_exports, [target], contract.taste_history_store,
            )
            analysis = await asyncio.to_thread(
                analyze_history, contract.taste_history_store, contract.taste_history_root,
            )
            write_manifest(contract.taste_history_manifest, results, analysis)
            contract.cache_bust()
            return {
                "refresh": results,
                "dashboard": web_contract.q_taste(contract, {"window": "all"}),
            }
        except OverflowError:
            temporary.unlink(missing_ok=True)
            return JSONResponse({"error": "导出文件超过 1 GB"}, status_code=413)
        except (BrowserexportError, OSError, ValueError, TypeError) as exc:
            temporary.unlink(missing_ok=True)
            if imported_target is not None:
                imported_target.unlink(missing_ok=True)
            LOGGER.warning("taste history import rejected: %s", exc)
            return JSONResponse({"error": str(exc)}, status_code=400)

    @app.post("/api/{route:path}")
    def api_post(
        route: str,
        body: dict[str, Any] = Body(default_factory=dict),
        _args: dict[str, str] = Depends(require_auth),
    ):
        route_path = f"/api/{route}"
        if (sync is not None and sync.read_only
                and route_path not in web_contract.READ_ONLY_POST_ROUTES):
            # 非写入端或冲突状态都只读；继续写只会产生无法自动合并的分叉。
            # 但只读的 POST 要放行：它们用 POST 只是因为要带请求体，并不碰账本。
            # `detail` 是诊断信息，`message` 是给用户的可读解释与恢复方式。
            return JSONResponse(
                {
                    "error": "ledger read-only",
                    "detail": sync.detail,
                    "message": sync.read_only_message,
                },
                status_code=409,
            )
        try:
            return web_contract.dispatch_api_post(contract, route_path, body)
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception:
            LOGGER.exception("unhandled POST contract error for /api/%s", route)
            return JSONResponse({"error": "internal server error"}, status_code=500)

    return app
