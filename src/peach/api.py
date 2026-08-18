import hmac
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

from fastapi import Body, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__, web_contract
from .config import PROJECT_ROOT, PeachSettings
from .ffmpeg import FFmpegResolver
from .http import HttpxTransport
from .media import (
    FilesystemBackend,
    MediaEngine,
    MediaNotFound,
    MediaUnavailable,
    StashAdapter,
)
from .mdns import create_mdns_publisher
from .previews import PreviewService, PreviewUnavailable
from .providers import OpenCodeGoClient, ProviderUnavailable, default_registry
from .repository import LedgerRepository
from .segments import (
    HlsSegmentService,
    SegmentCancelled,
    SegmentUnavailable,
    build_hls_playlist,
)
from .stash import StashClient
from .streaming import CancellableFileResponse, StreamSessionRegistry
from .transcodes import TranscodeService, TranscodeUnavailable


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


def create_app(settings: PeachSettings | None = None) -> FastAPI:
    settings = settings or PeachSettings()
    contract = web_contract.WebContract(
        settings.db_path, settings.snapshot_root, settings.legacy_snapshot_roots,
        candidate_root=settings.candidate_root,
    )
    repository = LedgerRepository(settings.db_path)
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
    transcode_service = TranscodeService(resolver, settings.transcode_root)
    hls_service = HlsSegmentService(resolver, settings.stream_root)
    mdns = create_mdns_publisher(
        settings.mdns_name, settings.mdns_port, secure=settings.tls_enabled,
        address=settings.mdns_address,
    ) if settings.mdns_enabled else None
    providers = default_registry()
    opencode_go = OpenCodeGoClient(transport=http_transport)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
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
            http_transport.close()

    app = FastAPI(
        title="Peach API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.web_contract = contract
    app.state.repository = repository
    app.state.media_engine = media_engine
    app.state.preview_service = preview_service
    app.state.transcode_service = transcode_service
    app.state.hls_service = hls_service
    app.state.mdns = mdns
    app.state.providers = providers
    app.state.opencode_go = opencode_go
    app.state.http_transport = http_transport
    stream_sessions = StreamSessionRegistry()
    app.state.stream_sessions = stream_sessions

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

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        # 不探测/迁移数据库；健康检查必须无副作用。
        ffmpeg = resolver.ffmpeg()
        return {"ok": True, "service": "peach-api", "version": __version__, "mode": "fastapi",
                "db": "available" if settings.db_path.is_file() else "missing",
                "ffmpeg": ffmpeg.source if ffmpeg else "unavailable",
                "mdns": mdns.status if mdns is not None else "disabled",
                "mdns_backend": mdns.backend if mdns is not None else None,
                "mdns_service": mdns.name if mdns is not None else None,
                "mdns_service_host": mdns.hostname if mdns is not None else None,
                "mdns_address": mdns.address if mdns is not None else None,
                "scheme": "https" if settings.tls_enabled else "http"}

    @app.api_route("/", methods=["GET", "HEAD"])
    def index(request: Request):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return PlainTextResponse("需要 ?t=口令", status_code=401)
        if not settings.page_path.is_file():
            return PlainTextResponse("Peach page missing", status_code=500)
        response = FileResponse(settings.page_path, media_type="text/html")
        response.headers["Cache-Control"] = "no-store"
        if settings.token:
            response.set_cookie(
                "tok", settings.token, max_age=31536000, path="/", httponly=True,
                samesite="lax", secure=request.url.scheme == "https",
            )
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
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        try:
            path, transcoded = transcode_service.browser_path(id, path)
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

    def _hls_plan(asset_id: int):
        """解析 HLS 的片源路径与关键帧分片计划；任何一步不成立就返回 None 走 Range。"""
        asset = media_engine.asset(asset_id)
        # 播放列表和分片端点本身就是 HLS 路径，按 ADR-0016 显式要计划，不受默认值影响。
        choice = media_engine.stream_plan(asset_id, mode="hls")
        if choice.protocol != "hls" or not asset.duration:
            return None
        source = media_engine.filesystem.file_for(asset, thumbnail=False)
        source, _ = transcode_service.browser_path(asset_id, source)
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
            resolved = _hls_plan(id)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
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
            resolved = _hls_plan(id)
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
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        except SegmentCancelled:
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
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path)
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
    def api_get(route: str, request: Request):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            return web_contract.dispatch_api_get(contract, f"/api/{route}", args)
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)

    @app.post("/api/{route:path}")
    def api_post(route: str, request: Request, body: dict[str, Any] = Body(default_factory=dict)):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            return web_contract.dispatch_api_post(contract, f"/api/{route}", body)
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)

    return app
