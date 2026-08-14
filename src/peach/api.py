import hmac
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response

from .config import PeachSettings
from .ffmpeg import FFmpegResolver
from .legacy_web import load_legacy
from .media import FilesystemMediaService, MediaNotFound, MediaUnavailable
from .previews import PreviewService, PreviewUnavailable
from .repository import LedgerRepository


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
    legacy = load_legacy(settings.legacy_module_path, settings.db_path, settings.token)
    repository = LedgerRepository(settings.db_path)
    resolver = FFmpegResolver(settings.ffmpeg_root)
    media_service = FilesystemMediaService(
        repository, settings.allowed_media_roots, settings.snapshot_root,
    )
    preview_service = PreviewService(
        repository, resolver, settings.snapshot_root, settings.poster_root,
        settings.avatar_root, settings.logo_root,
    )
    app = FastAPI(
        title="Peach API",
        version="0.2.0",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.legacy = legacy
    app.state.repository = repository
    app.state.media_service = media_service
    app.state.preview_service = preview_service

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
        return {"ok": True, "service": "peach-api", "mode": "fastapi",
                "db": "available" if settings.db_path.is_file() else "missing",
                "ffmpeg": ffmpeg.source if ffmpeg else "unavailable"}

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
        response = Response(legacy.FAVICON, media_type="image/svg+xml")
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.api_route("/stream", methods=["GET", "HEAD"])
    def stream(request: Request, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = media_service.file_for(id, thumbnail=False)
        except MediaNotFound:
            return JSONResponse({"error": "no such id"}, status_code=404)
        except MediaUnavailable:
            return JSONResponse({"error": "unavailable"}, status_code=404)
        response = FileResponse(path)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.api_route("/thumb", methods=["GET", "HEAD"])
    def thumbnail(request: Request, id: int):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            path = media_service.file_for(id, thumbnail=True)
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

    @app.get("/api/{route:path}")
    def api_get(route: str, request: Request):
        args = _first_query_values(request)
        if not _authorized(request, settings.token, args):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            return legacy.dispatch_api_get(f"/api/{route}", args)
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
            return legacy.dispatch_api_post(f"/api/{route}", body)
        except KeyError:
            return JSONResponse({"error": "not found"}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
        except Exception as exc:
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)

    return app
