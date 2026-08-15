import hmac
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response

from . import __version__, web_contract
from .config import PeachSettings
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
from .stash import StashClient
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
    app.state.mdns = mdns
    app.state.providers = providers
    app.state.opencode_go = opencode_go
    app.state.http_transport = http_transport

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        response = await call_next(request)
        if "cache-control" not in response.headers:
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

    @app.api_route("/stream", methods=["GET", "HEAD"])
    def stream(request: Request, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = media_engine.file_for(id, thumbnail=False)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        try:
            path, transcoded = transcode_service.browser_path(id, path)
        except TranscodeUnavailable:
            logging.getLogger(__name__).exception("browser transcode failed for asset %s", id)
            return JSONResponse({"error": "transcode unavailable"}, status_code=503)
        response = FileResponse(path, media_type="video/mp4" if transcoded else None)
        if transcoded:
            response.headers["X-Peach-Transcoded"] = "1"
        response.headers["Cache-Control"] = "no-store"
        return response

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
    @app.api_route("/performers/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/studios/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/creators/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/series/{name:path}", methods=["GET", "HEAD"])
    @app.api_route("/performers", methods=["GET", "HEAD"])
    @app.api_route("/creators", methods=["GET", "HEAD"])
    @app.api_route("/tags", methods=["GET", "HEAD"])
    @app.api_route("/stats", methods=["GET", "HEAD"])
    @app.api_route("/immerse", methods=["GET", "HEAD"])
    def client_route(request: Request, item_id: int | None = None,
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
