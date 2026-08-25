import hmac
import asyncio
import html
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
from typing import Any
from urllib.parse import parse_qs, quote

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response,
)
from fastapi.staticfiles import StaticFiles

from . import __version__, web_contract
from .config import LOCATION_ROOT_DECLARATIONS, PROJECT_ROOT, PeachSettings
from .ffmpeg import FFmpegResolver
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
from .platform import (
    is_unmapped,
    reveal_command,
    root_online,
    translate_ledger_path,
)
from .previews import PhotoThumbnailService, PreviewService, PreviewUnavailable
from .providers import OpenCodeGoClient, ProviderUnavailable, default_registry
from .repository import LedgerDatabase, LedgerRepository
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


def create_app(
    settings: PeachSettings | None = None,
    sync: LedgerSync | None = None,
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
        database=database,
    )
    repository = LedgerRepository(database)
    resolver = FFmpegResolver(settings.ffmpeg_root)
    http_transport = HttpxTransport()
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

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if sync is not None:
            sync.start()
        if mdns is not None:
            try:
                await asyncio.to_thread(mdns.start)
            except Exception:
                mdns.status = "unavailable"
                logging.getLogger(__name__).exception("mDNS publication failed")
        try:
            yield
        finally:
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
    app.state.http_transport = http_transport
    stream_sessions = StreamSessionRegistry()
    app.state.stream_sessions = stream_sessions
    app.state.sync = sync

    def require_auth(request: Request) -> dict[str, str]:
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            raise HTTPException(status_code=401, detail="unauthorized")
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
        return {"ok": True, "service": "peach-api", "version": __version__, "mode": "fastapi",
                "db": "available" if settings.db_path.is_file() else "missing",
                "ffmpeg": ffmpeg.source if ffmpeg else "unavailable",
                "mdns": mdns.status if mdns is not None else "disabled",
                "mdns_backend": mdns.backend if mdns is not None else None,
                "mdns_service": mdns.name if mdns is not None else None,
                "mdns_service_host": mdns.hostname if mdns is not None else None,
                "mdns_address": mdns.address if mdns is not None else None,
                "ledger_sync": sync.status if sync is not None else "disabled",
                "scheme": "https" if settings.tls_enabled else "http"}

    def login_html(next_path: str, *, invalid: bool = False) -> str:
        safe_next = html.escape(next_path, quote=True)
        error = '<p role="alert">口令不正确</p>' if invalid else ""
        return (
            '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="dark"><title>登录 Peach</title>'
            '<style>'
            '*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#020408;color:#f5f7fb}'
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
    def index(request: Request):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return RedirectResponse(
                "/login?next=" + quote(request.url.path or "/", safe="/"), status_code=303,
            )
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
    def app_asset(request: Request):
        """页面拆出来的样式与脚本。和 index.html 同目录，同一套口令。

        没有构建步骤：`app.js` 是普通脚本不是 module，顶层声明仍然是全局的，
        和内联时行为一致——内联事件处理器和跨函数调用都还指着同一批全局名字。
        """
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return PlainTextResponse("需要 ?t=口令", status_code=401)
        name = request.url.path.lstrip("/")
        path = settings.page_path.parent / name
        if not path.is_file():
            return PlainTextResponse("missing", status_code=404)
        media = "text/css" if name.endswith(".css") else "text/javascript"
        response = FileResponse(path, media_type=f"{media}; charset=utf-8")
        # 页面本体是 no-store，样式与脚本跟着它一起变，不能被旧缓存钉住。
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
    def stream(request: Request, id: int, session: str = ""):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            asset = media_engine.asset(id)
            path = media_engine.filesystem.file_for(asset, thumbnail=False)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
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
    def stream_plan(request: Request, id: int, session: str = "", mode: str = ""):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        if session and len(session) > 128:
            return JSONResponse({"error": "invalid session"}, status_code=400)
        if session and stream_sessions.is_cancelled(session):
            return JSONResponse({"error": "stream cancelled"}, status_code=410)
        try:
            asset = media_engine.asset(id)
            plan = media_engine.stream_plan(id, mode=mode or "auto")
            # 只有真的能读出关键帧才宣告 HLS，否则客户端会拿到一个必然 404 的播放列表。
            resolved = _hls_plan(id) if plan.protocol == "hls" else None
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
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
    def hls_playlist(request: Request, id: int, session: str = ""):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        # 分片必须带 session 才能被取消，播放列表这层就要求它；
        # 否则会生成一份每个分片都必然 400 的目录。
        if not session or len(session) > 128:
            return PlainTextResponse("session required", status_code=400)
        if stream_sessions.is_cancelled(session):
            return PlainTextResponse("stream cancelled", status_code=410)
        try:
            resolved = _hls_plan(id, session)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
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
    async def hls_segment(request: Request, id: int, index: int, session: str = ""):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
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
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
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
        response.headers["Cache-Control"] = "private, max-age=86400"
        response.headers["X-Peach-HLS-Segment"] = "1"
        return response

    @app.post("/api/stream-cancel")
    async def stream_cancel(request: Request, session: str):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        if not session or len(session) > 128:
            return JSONResponse({"error": "invalid session"}, status_code=400)
        cancelled = stream_sessions.cancel(session)
        return JSONResponse({"ok": True, "cancelled": cancelled})

    @app.api_route("/thumb", methods=["GET", "HEAD"])
    def thumbnail(request: Request, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = media_engine.file_for(id, thumbnail=True)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/photo", methods=["GET", "HEAD"])
    def photo(request: Request, id: int):
        """图片资产原图。灯箱看大图用这条，瀑布流一律走 `/photo-thumb`。"""
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = media_engine.file_for(id)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/photo-thumb", methods=["GET", "HEAD"])
    def photo_thumb(request: Request, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            source = media_engine.file_for(id)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaOffline as exc:
            return _offline_response(exc)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        try:
            path = photo_service.thumbnail(id, source)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/poster", methods=["GET", "HEAD"])
    def poster(request: Request, id: int, c: int = 4):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = preview_service.poster(id, c)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/cover", methods=["GET", "HEAD"])
    def cover(request: Request, code: str = ""):
        """官方封套原图。存原图不裁：4:3 与 16:9 两种版式在界面上按比例取景。"""
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        path = contract.cover_path(code)
        if path is None:
            return JSONResponse({"error": "no cover"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/endcard-frame", methods=["GET", "HEAD"])
    def endcard_frame(request: Request, id: int, name: str):
        """Serve only generated OCR evidence frames, never a client-provided path."""
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        if (id <= 0 or not name.endswith(".png") or "/" in name or "\\" in name
                or name.startswith(".")):
            return JSONResponse({"error": "invalid frame"}, status_code=400)
        root = (settings.candidate_root / "endcard-evidence" / str(id)).resolve()
        path = (root / name).resolve()
        if path.parent != root or not path.is_file():
            return JSONResponse({"error": "no frame"}, status_code=404)
        response = FileResponse(path, media_type="image/png")
        response.headers["Cache-Control"] = "private, max-age=86400"
        return response

    @app.api_route("/avatar", methods=["GET", "HEAD"])
    def avatar(request: Request, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = preview_service.avatar(id)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type="image/jpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/logo", methods=["GET", "HEAD"])
    def logo(request: Request, studio: str = ""):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path, content_type = preview_service.logo(studio)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type=content_type)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.api_route("/item/{item_id}", methods=["GET", "HEAD"])
    @app.api_route("/mix/{seed_id}/{mix_item_id}", methods=["GET", "HEAD"])
    @app.api_route("/performers/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/studios/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/creators/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/series/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/performers", methods=["GET", "HEAD"])
    @app.api_route("/creators", methods=["GET", "HEAD"])
    @app.api_route("/tags", methods=["GET", "HEAD"])
    @app.api_route("/stats", methods=["GET", "HEAD"])
    @app.api_route("/immerse", methods=["GET", "HEAD"])
    @app.api_route("/trash", methods=["GET", "HEAD"])
    @app.api_route("/review", methods=["GET", "HEAD"])
    @app.api_route("/duplicates", methods=["GET", "HEAD"])
    @app.api_route("/quality-goals", methods=["GET", "HEAD"])
    def client_route(request: Request, item_id: int | None = None,
                     seed_id: int | None = None, mix_item_id: int | None = None,
                     kind: str | None = None, name: str | None = None):
        return index(request)

    @app.api_route("/entity-image", methods=["GET", "HEAD"])
    def entity_image(request: Request, kind: str, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path, content_type = preview_service.entity_image(kind, id)
        except PreviewUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path, media_type=content_type)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.get("/api/providers")
    def provider_health(request: Request):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return providers.health()

    @app.get("/api/sources")
    def source_health(request: Request):
        """无副作用的来源可达性。前端据此把脱盘来源的筛选置灰。"""
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        rows = _source_status()
        return {
            "ok": True,
            "sources": rows,
            "offline": [row["location"] for row in rows if not row["online"]],
        }

    @app.post("/api/reveal")
    def reveal(request: Request, body: dict[str, Any] = Body(default_factory=dict)):
        """在本机文件管理器里定位某个资产的源文件。

        用于「跳过去自己整理网盘目录」：A:/B: 是 CloudDrive 挂上来的盘符，在
        资源管理器里和本地目录没有区别。路径一律由服务端按 asset id 查出来——
        `q_item` 刻意不把 `path` 发给前端，这里不能反过来让前端把路径传进来。

        写不进 ledger，所以不受 reader 的只读闸门约束；但它会在**服务端所在的
        机器**上弹窗，从 Mac 浏览时弹在 Windows 那台，也正是文件所在的机器。
        """
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
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
        command = reveal_command(target)
        if command is None:
            return JSONResponse({"error": "unsupported platform"}, status_code=501)
        try:
            # explorer 成功时也返回 1，所以不能用 check=True 判成败。
            subprocess.Popen(command, close_fds=True)
        except OSError as error:
            LOGGER.warning("reveal failed for asset %s: %s", asset_id, error)
            return JSONResponse({"error": "reveal failed"}, status_code=500)
        return {"ok": True, "id": asset_id, "location": asset.location}

    @app.get("/api/providers/opencode-go/models")
    def opencode_go_models(request: Request):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            models = opencode_go.list_models()
        except ProviderUnavailable:
            return JSONResponse({"error": "provider unavailable"}, status_code=502)
        return {"ok": True, "provider": "opencode-go", "models": models}

    @app.get("/api/{route:path}")
    def api_get(route: str, args: dict[str, str] = Depends(require_auth)):
        try:
            return web_contract.dispatch_api_get(contract, f"/api/{route}", args)
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception:
            LOGGER.exception("unhandled GET contract error for /api/%s", route)
            return JSONResponse({"error": "internal server error"}, status_code=500)

    @app.post("/api/{route:path}")
    def api_post(
        route: str,
        body: dict[str, Any] = Body(default_factory=dict),
        _args: dict[str, str] = Depends(require_auth),
    ):
        if sync is not None and sync.read_only:
            # 非写入端或冲突状态都只读；继续写只会产生无法自动合并的分叉。
            return JSONResponse(
                {"error": "ledger read-only", "detail": sync.detail}, status_code=409,
            )
        try:
            return web_contract.dispatch_api_post(contract, f"/api/{route}", body)
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception:
            LOGGER.exception("unhandled POST contract error for /api/%s", route)
            return JSONResponse({"error": "internal server error"}, status_code=500)

    return app
