import hmac
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse

from .config import PeachSettings
from .legacy_web import load_legacy


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
    app = FastAPI(
        title="Peach API",
        version="0.1.0",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.legacy = legacy

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        # 不探测/迁移数据库；健康检查必须无副作用。
        return {"ok": True, "service": "peach-api", "mode": "compat"}

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
