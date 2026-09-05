"""应用组装点：把依赖建好挂到 `app.state`，再按顺序把各 router include 进来。

路由不在这里。它们按类分到四个模块，各自 import 需要的东西，运行期依赖一律从
`request.app.state` 取：

| 模块 | 管什么 |
| --- | --- |
| `routes_auth` | 口令闸门与登录页，三个 `require_*` 依赖 |
| `routes_pages` | 单页界面、静态资产与全部前端路由落点 |
| `routes_media` | 播放、分片、缩图、封面、头像、外链圆标 |
| `routes_api` | JSON 契约出口，含两条 `/api/{route:path}` catch-all |

`include_router` 的顺序是契约的一部分，不是排版：FastAPI 按注册顺序匹配，
`routes_api` 的两条 catch-all 会吃掉一切 `/api/...`，所以它必须最后。
`/api/stream-plan` 和 `/api/stream-cancel` 住在 `routes_media`，那个 router 也因此
要排在 `routes_api` 前面。

留在本文件里的只有全应用一份的东西：依赖装配、`lifespan`、异常处理器、`/vendor`
挂载、响应头与压缩中间件和 `/healthz`。
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import DEFAULT_EXCLUDED_CONTENT_TYPES, GZipMiddleware

from . import __version__, web_contract, web_follow
from . import routes_api, routes_auth, routes_configuration, routes_media, routes_pages
from .config import PeachSettings
from .ffmpeg import FFmpegResolver
from .follow_scheduler import FollowUpdateScheduler
from .follow_covers import FollowCoverService
from .follow_stream import FollowMediaResolver
from .http import HttpxTransport
from .media import (
    FilesystemBackend,
    MediaEngine,
    MediaNotFound,
    MediaOffline,
    MediaUnavailable,
)
from .mdns import create_mdns_publisher
from .previews import PhotoThumbnailService, PreviewService
from .providers import OpenCodeGoClient, default_registry
from .repository import LedgerDatabase, LedgerRepository
from .review_mirror import ReviewMirror
from .routes_auth import AssetLoginRequired, PageLoginRequired
# 两档缓存时长的实现在 `routes_media`，这里再导出：它们是对外的缓存契约，
# tests/test_follow_web.py 按 `api.MEDIA_CACHE_SECONDS` 断言两者的关系。
from .routes_media import AVATAR_CACHE_SECONDS, MEDIA_CACHE_SECONDS  # noqa: F401
from .segments import HlsSegmentService
from .streaming import StreamSessionRegistry
from .sync import LedgerSync
from .transcodes import TranscodeService


LOGGER = logging.getLogger(__name__)

#: gzip 不碰的内容类型。Starlette 的默认名单已经排掉 `video/*`、`audio/*` 和各种
#: 已压缩的图片，这里再补两个它没排、而 Peach 会真的撞上的：
#: `application/octet-stream` 是通用字节流；`text/plain` 是 `FileResponse` 猜不出
#: 扩展名时的兜底值，`/stream` 与 `/photo` 都不传 media_type，一个没登记过扩展名的
#: 媒体文件会以 `text/plain` 出去——压它纯属烧 CPU。Peach 自己有意发的
#: `text/plain` 只有 "missing" 这类错误提示，本来就在 `minimum_size` 之下。
COMPRESSION_EXCLUDED_TYPES = (
    *DEFAULT_EXCLUDED_CONTENT_TYPES, "application/octet-stream", "text/plain",
)


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
    media_engine = MediaEngine(repository, filesystem)
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
            # 死链检查和资源对账的后台线程是 daemon，本来挡不住进程退出；这里显式收
            # 一下，免得在途的那一轮在解释器拆卸期间还继续查库、往没人读的状态里写。
            contract.stop_background_jobs()
            if mdns is not None:
                await asyncio.to_thread(mdns.stop)
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
    app.state.stream_sessions = StreamSessionRegistry()
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

    # JSON 契约、页面脚本与样式是仅有的几类大文本响应，压下去省的字节最多：
    # `/api/items` 一页几十 KB，`app.js` 435KB、`app.css` 232KB。
    # `add_middleware` 是 `insert(0)`，最后加的在最外层，所以压缩看到的是上面
    # `no_store` 补完 Cache-Control 之后的最终响应头。
    # 自己写内容类型闸门的 ASGI 中间件是重复劳动：Starlette 这个已经按 Content-Type
    # 排除、跳过 206 与已编码响应、逐块流式压缩，还会把大块丢到工作线程去压，
    # 不占事件循环。只需要把它的排除名单补齐（见 COMPRESSION_EXCLUDED_TYPES）。
    app.add_middleware(
        GZipMiddleware, exclude_content_types=COMPRESSION_EXCLUDED_TYPES,
    )

    # 健康检查常被 HEAD 探测（`curl -I`、各种 uptime 工具）。本仓库其他公开端点
    # 都显式声明了 GET+HEAD，只有这个漏了，HEAD 会拿到 405。
    @app.api_route("/healthz", methods=["GET", "HEAD"])
    def healthz(ready: bool = False):
        from .health import database_status, readiness
        if ready:
            result = readiness(settings)
            return JSONResponse(result, status_code=200 if result["ready"] else 503,
                                headers={"Cache-Control": "no-store"})
        # 不探测共享目录或迁移数据库；健康检查必须无副作用。
        ffmpeg = resolver.ffmpeg()
        read_only = bool(sync is not None and sync.read_only)
        return {"ok": True, "service": "peach-api", "version": __version__, "mode": "fastapi",
                # 这台机器跑过 `peach init` 没有。未配置时服务照常起，只是没有数据。
                "configured": settings.configured,
                "db": database_status(settings.db_path),
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

    # 顺序即契约：catch-all 最后。`routes_media` 里有 `/api/stream-plan` 与
    # `/api/stream-cancel` 两条具名 API，所以它也要排在 `routes_api` 之前。
    app.include_router(routes_auth.router)
    app.include_router(routes_pages.router)
    app.include_router(routes_configuration.router)
    app.include_router(routes_media.router)
    app.include_router(routes_api.router)
    return app
