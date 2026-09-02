"""媒体字节的出口：播放、分片、缩图、封面、头像与外链圆标。

这一层只做取路径与拼响应头，不做媒体判断——能不能播、走 Range 还是 HLS、要不要
转码，全在 `media`／`transcodes`／`segments` 里。三个媒体异常（`MediaNotFound`、
`MediaOffline`、`MediaUnavailable`）由 `api.py` 的异常处理器统一收口，路由里不要
再手抄同一组 try/except。

有一条贯穿整层的规矩：**上游地址一律不外露**。`/follow-stream`、`/follow-cover`、
`/link-mark` 都只接受账本里的 id，自己去查地址；接受前端递过来的 URL 就等于开了一个
任意地址抓取的口子。
"""
from __future__ import annotations

import asyncio
import logging
import re
from functools import partial
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import (
    FileResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response,
    StreamingResponse,
)

from . import link_marks, site_icons
from .config import GENERATED_DIR
from .follow import FollowSourceError
from .follow_avatar import resolve_official_avatar
from .follow_covers import FollowCoverUnavailable
from .follow_store import FollowStore
from .follow_stream import FollowMediaUnavailable
from .media import MediaUnavailable
from .previews import PreviewUnavailable
from .routes_auth import require_auth
from .segments import SegmentCancelled, SegmentUnavailable, build_hls_playlist
from .streaming import CancellableFileResponse
from .transcodes import TranscodeCancelled, TranscodeUnavailable

router = APIRouter()

#: 生成物的缓存时长。这些端点按 asset / follow_item id 取图：内容换了 id 也就换了
#: （封面重生成写的是新文件），所以一年也不嫌长。
#: 不加 immutable——那会让浏览器连刷新都不再回源，真要换图就只能干等过期。
MEDIA_CACHE_SECONDS = 365 * 24 * 3600

#: 头像单独短一档：id 不变但人会换头像，作者换得还挺勤。
AVATAR_CACHE_SECONDS = 30 * 24 * 3600

#: 取图标时报浏览器 UA。CDN 上的图标资产（p-smith、static.cdninstagram）对
#: 机器人 UA 会直接 403，而这只是一次公开静态文件请求，没有伪装成用户的意思。
ICON_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

#: 文件名里不能出现的字符，按 Windows 的最严口径取——落盘的那台多半是它。
_UNSAFE_FILENAME = re.compile('[\\/:*?"<>|]+|[\x00-\x1f]+')

LOGGER = logging.getLogger(__name__)


def _attachment_disposition(title: str, url: str) -> str:
    """按条目标题构造下载文件名，扩展名沿用上游地址的后缀。

    不回传上游地址：主机名和签名同样是不该外露的东西，和 `/follow-stream`
    整体的边界一致。`filename*` 用 RFC 5987 编码，标题里的中文和日文才落得下来。
    """
    stem = _UNSAFE_FILENAME.sub(" ", str(title or "")).strip() or "peach-media"
    stem = " ".join(stem.split())[:120]
    suffix = Path(urlsplit(str(url or "")).path).suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{2,5}", suffix):
        suffix = ".mp4"
    name = f"{stem}{suffix}"
    # 标题整条都是中日文时，ascii 回退会只剩空格和标点，浏览器落下来是个没名字的
    # 文件。回退名必须自己站得住，不能是「把非 ASCII 删掉之后剩下的」。
    ascii_stem = "".join(ch for ch in stem if ch.isascii() and (ch.isalnum() or ch in " -_[]().")).strip()
    ascii_name = f"{ascii_stem}{suffix}" if ascii_stem else f"peach-media{suffix}"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"


def _hls_plan(state, asset_id: int, session: str = ""):
    """解析 HLS 的片源路径与关键帧分片计划；任何一步不成立就返回 None 走 Range。"""
    asset = state.media_engine.asset(asset_id)
    # 播放列表和分片端点本身就是 HLS 路径，按 ADR-0016 显式要计划，不受默认值影响。
    choice = state.media_engine.stream_plan(asset_id, mode="hls")
    if choice.protocol != "hls" or not asset.duration:
        return None
    source = state.media_engine.filesystem.file_for(asset, thumbnail=False)
    source, _ = state.transcode_service.browser_path(
        asset_id, source, session=session, registry=state.stream_sessions,
    )
    plan = state.hls_service.plan(source, asset.duration)
    return None if not plan else (asset, source, plan)


@router.api_route("/stream", methods=["GET", "HEAD"])
def stream(request: Request, id: int, session: str = "", args: dict[str, str] = Depends(require_auth)):
    state = request.app.state
    asset = state.media_engine.asset(id)
    path = state.media_engine.filesystem.file_for(asset, thumbnail=False)
    try:
        path, transcoded = state.transcode_service.browser_path(
            id, path, session=session, registry=state.stream_sessions,
        )
    except TranscodeCancelled:
        return Response(status_code=410, headers={"Cache-Control": "no-store"})
    except TranscodeUnavailable:
        LOGGER.exception("browser transcode failed for asset %s", id)
        return JSONResponse({"error": "transcode unavailable"}, status_code=503)
    media_type = "video/mp4" if transcoded else None
    response = (
        CancellableFileResponse(
            path, session=session, registry=state.stream_sessions, media_type=media_type,
        )
        if session else FileResponse(path, media_type=media_type)
    )
    if transcoded:
        response.headers["X-Peach-Transcoded"] = "1"
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/api/stream-plan")
def stream_plan(request: Request, id: int, session: str = "", mode: str = "", args: dict[str, str] = Depends(require_auth)):
    state = request.app.state
    if session and len(session) > 128:
        return JSONResponse({"error": "invalid session"}, status_code=400)
    if session and state.stream_sessions.is_cancelled(session):
        return JSONResponse({"error": "stream cancelled"}, status_code=410)
    asset = state.media_engine.asset(id)
    plan = state.media_engine.stream_plan(id, mode=mode or "auto")
    # 只有真的能读出关键帧才宣告 HLS，否则客户端会拿到一个必然 404 的播放列表。
    resolved = _hls_plan(state, id) if plan.protocol == "hls" else None
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


@router.get("/stream/hls/{id}/index.m3u8")
def hls_playlist(request: Request, id: int, session: str = "", args: dict[str, str] = Depends(require_auth)):
    state = request.app.state
    # 分片必须带 session 才能被取消，播放列表这层就要求它；
    # 否则会生成一份每个分片都必然 400 的目录。
    if not session or len(session) > 128:
        return PlainTextResponse("session required", status_code=400)
    if state.stream_sessions.is_cancelled(session):
        return PlainTextResponse("stream cancelled", status_code=410)
    try:
        resolved = _hls_plan(state, id, session)
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


@router.get("/stream/hls/{id}/{index}.ts")
async def hls_segment(request: Request, id: int, index: int, session: str = "", args: dict[str, str] = Depends(require_auth)):
    state = request.app.state
    if not session or len(session) > 128:
        return JSONResponse({"error": "invalid session"}, status_code=400)
    if state.stream_sessions.is_cancelled(session):
        return Response(status_code=410, headers={"Cache-Control": "no-store"})
    try:
        loop = asyncio.get_running_loop()
        resolved = await loop.run_in_executor(
            state.hls_plan_executor, partial(_hls_plan, state, id, session),
        )
        if resolved is None:
            return JSONResponse({"error": "hls unavailable"}, status_code=404)
        _, source, plan = resolved
        if index < 0 or index >= len(plan):
            return JSONResponse({"error": "invalid segment"}, status_code=416)
        start, duration = plan[index]
        path = await state.hls_service.generate(
            source, start, duration, asset_id=id, index=index,
            session=session, registry=state.stream_sessions,
        )
    except SegmentCancelled:
        return Response(status_code=410, headers={"Cache-Control": "no-store"})
    except TranscodeCancelled:
        return Response(status_code=410, headers={"Cache-Control": "no-store"})
    except TranscodeUnavailable:
        LOGGER.exception("browser transcode failed for asset %s", id)
        return JSONResponse({"error": "transcode unavailable"}, status_code=503)
    except SegmentUnavailable:
        LOGGER.exception("HLS segment failed for asset %s", id)
        return JSONResponse({"error": "segment unavailable"}, status_code=503)
    # 片段现在留在缓存里而不是随响应删除：回放、重连和多设备都会重复请求同一段，
    # 每次重跑 FFmpeg 等于让 CloudDrive 再预取一次块。
    response = FileResponse(path, media_type="video/mp2t")
    response.headers["Cache-Control"] = f"private, max-age={MEDIA_CACHE_SECONDS}"
    response.headers["X-Peach-HLS-Segment"] = "1"
    return response


@router.post("/api/stream-cancel")
async def stream_cancel(request: Request, session: str, args: dict[str, str] = Depends(require_auth)):
    if not session or len(session) > 128:
        return JSONResponse({"error": "invalid session"}, status_code=400)
    cancelled = request.app.state.stream_sessions.cancel(session)
    return JSONResponse({"ok": True, "cancelled": cancelled})


@router.api_route("/thumb", methods=["GET", "HEAD"])
def thumbnail(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
    path = request.app.state.media_engine.file_for(id, thumbnail=True)
    response = FileResponse(path)
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/photo", methods=["GET", "HEAD"])
def photo(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
    """图片资产原图。灯箱看大图用这条，瀑布流一律走 `/photo-thumb`。"""
    path = request.app.state.media_engine.file_for(id)
    response = FileResponse(path)
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/photo-thumb", methods=["GET", "HEAD"])
def photo_thumb(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
    state = request.app.state
    source = state.media_engine.file_for(id)
    try:
        path = state.photo_service.thumbnail(id, source)
    except PreviewUnavailable:
        return JSONResponse({"error": "unavailable"}, status_code=404)
    response = FileResponse(path, media_type="image/jpeg")
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/poster", methods=["GET", "HEAD"])
def poster(request: Request, id: int, c: int = 4, args: dict[str, str] = Depends(require_auth)):
    try:
        path = request.app.state.preview_service.poster(id, c)
    except PreviewUnavailable:
        return JSONResponse({"error": "unavailable"}, status_code=404)
    response = FileResponse(path, media_type="image/jpeg")
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/cover", methods=["GET", "HEAD"])
def cover(request: Request, code: str = "", args: dict[str, str] = Depends(require_auth)):
    """官方封套原图。存原图不裁：4:3 与 16:9 两种版式在界面上按比例取景。"""
    path = request.app.state.web_contract.cover_path(code)
    if path is None:
        return JSONResponse({"error": "no cover"}, status_code=404)
    response = FileResponse(path, media_type="image/jpeg")
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/endcard-frame", methods=["GET", "HEAD"])
def endcard_frame(request: Request, id: int, name: str, args: dict[str, str] = Depends(require_auth)):
    """Serve only generated OCR evidence frames, never a client-provided path."""
    if (id <= 0 or not name.endswith(".png") or "/" in name or "\\" in name
            or name.startswith(".")):
        return JSONResponse({"error": "invalid frame"}, status_code=400)
    root = (request.app.state.settings.candidate_root
            / "endcard-evidence" / str(id)).resolve()
    path = (root / name).resolve()
    if path.parent != root or not path.is_file():
        return JSONResponse({"error": "no frame"}, status_code=404)
    response = FileResponse(path, media_type="image/png")
    response.headers["Cache-Control"] = f"private, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/avatar", methods=["GET", "HEAD"])
def avatar(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
    try:
        path = request.app.state.preview_service.avatar(id)
    except PreviewUnavailable:
        return JSONResponse({"error": "unavailable"}, status_code=404)
    response = FileResponse(path, media_type="image/jpeg")
    response.headers["Cache-Control"] = f"public, max-age={AVATAR_CACHE_SECONDS}"
    return response


@router.api_route("/follow-avatar", methods=["GET", "HEAD"])
def follow_avatar(request: Request, service: str, id: str, args: dict[str, str] = Depends(require_auth)):
    """Resolve an official creator avatar, then let the image CDN serve it."""
    try:
        target = resolve_official_avatar(service, id)
    except (OSError, FollowSourceError):
        return JSONResponse({"error": "unavailable"}, status_code=404)
    response = RedirectResponse(target, status_code=307)
    response.headers["Cache-Control"] = f"private, max-age={AVATAR_CACHE_SECONDS}"
    return response


@router.api_route("/follow-qualities", methods=["GET"])
def follow_qualities(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
    """这条关注视频有哪些清晰度可选。

    单独一个端点而不是塞进 /api/follow：解析要抓一次来源详情页，列表一次几百条，
    逐条解析等于几百个外部请求。这里只在用户展开某个条目、播放器要画菜单时问一次，
    解析结果本身在 resolver 里有缓存。

    只有 rule34video 给多档（video_url 加 video_alt_url{,2,3}）；其余来源返回空表，
    播放器据此只显示「原画」。取不到不是错误——签名 URL 会过期、来源也可能改版，
    那时照常播默认档就行。
    """
    state = request.app.state
    with state.database.read_connection() as connection:
        item = FollowStore(lambda: connection).item(id)
    if item is None:
        return JSONResponse({"error": "no such follow item"}, status_code=404)
    try:
        resolved = state.follow_media_resolver.resolve(item)
    except FollowMediaUnavailable:
        return {"qualities": []}
    # 档位数量不写死：正则匹配 video_url 与任意编号的 video_alt_urlN，
    # 站点给几档就是几档（实测同一作者下有 4 档也有 5 档的条目）。
    # 2160 按站点自己的写法叫 4K，不叫 2160p。
    return {"qualities": [
        {"height": height, "label": "4K" if height >= 2160 else f"{height}p"}
        for height, _ in resolved.qualities if height
    ]}


@router.api_route("/follow-stream", methods=["GET", "HEAD"])
def follow_stream(request: Request, id: int, media: int | None = None,
                  quality: int | None = None, download: int = 0,
                  args: dict[str, str] = Depends(require_auth)):
    """Play a remote follow candidate through Peach without exposing its upstream URL."""
    state = request.app.state
    with state.database.read_connection() as connection:
        item = FollowStore(lambda: connection).item(id)
    if item is None:
        return JSONResponse({"error": "no such follow item"}, status_code=404)
    try:
        target = state.follow_media_resolver.resolve(item, media, quality)
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
        upstream_request = state.http_transport.client.build_request(
            request.method, target.url, headers=headers,
        )
        upstream = state.http_transport.client.send(upstream_request, stream=True)
    except FollowMediaUnavailable as error:
        return JSONResponse({"error": str(error)}, status_code=404)
    except (OSError, httpx.HTTPError):
        LOGGER.exception("follow media proxy failed for item %s", id)
        return JSONResponse({"error": "follow media unavailable"}, status_code=502)

    forwarded = {}
    for name in ("accept-ranges", "content-length", "content-range", "content-type",
                 "etag", "last-modified"):
        value = upstream.headers.get(name)
        if value:
            forwarded[name] = value
    forwarded["cache-control"] = "no-store"
    # 下载是显式动作，不是播放的副作用：只有带 `download=1` 才让浏览器落盘。
    # 文件名从条目标题来，不回传上游地址——上游主机名同样是不该外露的东西。
    if download:
        forwarded["content-disposition"] = _attachment_disposition(
            item.title, target.url)
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


@router.api_route("/follow-cover", methods=["GET", "HEAD"])
def follow_cover(request: Request, id: int, args: dict[str, str] = Depends(require_auth)):
    """Return a cached clear still for a follow video; keep its URL server-side."""
    state = request.app.state
    with state.database.read_connection() as connection:
        item = FollowStore(lambda: connection).item(id)
    if item is None:
        return JSONResponse({"error": "no such follow item"}, status_code=404)
    try:
        path = state.follow_cover_service.cover(item)
    except FollowCoverUnavailable:
        # Paheal itself only has this low-resolution fallback. A temporary FFmpeg or
        # network failure should degrade to the old cover instead of leaving a hole.
        if str(item.thumb_url or "").startswith("https://"):
            return RedirectResponse(str(item.thumb_url), status_code=307)
        return JSONResponse({"error": "follow cover unavailable"}, status_code=404)
    response = FileResponse(path, media_type="image/jpeg")
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response


@router.api_route("/logo", methods=["GET", "HEAD"])
def logo(request: Request, studio: str = "", variant: str = "",
         args: dict[str, str] = Depends(require_auth)):
    try:
        path, content_type = request.app.state.preview_service.logo(studio, variant)
    except PreviewUnavailable:
        return JSONResponse({"error": "unavailable"}, status_code=404)
    response = FileResponse(path, media_type=content_type)
    # Logo 可以缓存，但文件会在人工批准或重新归一后原地替换。固定 URL 若缓存
    # 一整天，浏览器会继续显示旧图；no-cache 会复用本地副本并用 ETag 重验。
    response.headers["Cache-Control"] = "public, no-cache"
    return response


@router.api_route("/link-mark", methods=["GET", "HEAD"])
def link_mark(request: Request, id: int = 0, args: dict[str, str] = Depends(require_auth)):
    """资料页外链的圆标：站点自己最好的那份图标资产，能上色就上色。

    地址只从账本按链接 id 解析，绝不接受前端递过来的 URL——和 `/follow-stream`
    同一条规矩，否则这就是一个任意地址抓取的口子。取哪一份交给 `site_icons`：
    先读首页声明的 apple-touch-icon / SVG / manifest，都没有才落到 favicon.ico。
    """
    state = request.app.state
    with state.database.read_connection() as connection:
        row = connection.execute(
            "SELECT url FROM entity_link WHERE id=?", (id,)).fetchone()
    if row is None:
        return JSONResponse({"error": "no such link"}, status_code=404)

    root = GENERATED_DIR / "link-marks"
    cached = link_marks.cached_path(root, row["url"])
    if cached is None:
        return JSONResponse({"error": "unavailable"}, status_code=404)
    if not link_marks.is_fresh(cached):
        def fetch(target: str):
            try:
                upstream = state.http_transport.client.get(
                    target, headers={"User-Agent": ICON_USER_AGENT},
                    timeout=8, follow_redirects=True)
            except (OSError, httpx.HTTPError):
                return None
            if upstream.status_code != 200 or not upstream.content:
                return None
            return upstream.content, upstream.headers.get("content-type", "")

        # 两条通道都不适用时退回原样缩图：糊一点也好过露出地球图标。
        made = site_icons.best_mark(row["url"], fetch, link_marks.render_mark,
                                    fallback=link_marks.plain_mark)
        if made:
            root.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(made)
        elif not cached.exists():
            # 取不到就让前端露出下面的地球图标，不要留一个空白圆。
            return JSONResponse({"error": "unavailable"}, status_code=404)
    result = FileResponse(cached, media_type="image/png")
    result.headers["Cache-Control"] = "public, no-cache"
    return result


@router.api_route("/entity-image", methods=["GET", "HEAD"])
def entity_image(request: Request, kind: str, id: int, args: dict[str, str] = Depends(require_auth)):
    try:
        path, content_type = request.app.state.preview_service.entity_image(kind, id)
    except PreviewUnavailable:
        return JSONResponse({"error": "unavailable"}, status_code=404)
    response = FileResponse(path, media_type=content_type)
    response.headers["Cache-Control"] = f"public, max-age={MEDIA_CACHE_SECONDS}"
    return response
