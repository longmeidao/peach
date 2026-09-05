"""JSON 契约的 HTTP 出口。

绝大多数端点不在这里逐个声明：`/api/{route:path}` 把路径交给 `web_router` 的两张
处理器表，加一个 API 只需要在那里注册。这里只留三类必须自己写的：
探测类（providers、sources）、本机副作用（reveal）和流式上传（taste/import）。

注册顺序有意义。`/api/{route:path}` 是 catch-all，`api.py` 必须最后 include 这个
router；同理本模块内部两条 catch-all 写在文件末尾，具名端点写在前面。
`/api/stream-plan` 与 `/api/stream-cancel` 在 `routes_media` 里，那个 router 也要
先 include。
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from browserexport.common import BrowserexportError
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse

from . import web_contract
from .config import LOCATION_ROOT_DECLARATIONS
from .interaction import reveal_path
from .platform import is_unmapped, root_online, translate_ledger_path
from .providers import ProviderUnavailable
from .routes_auth import require_auth
from .taste_history import analyze_history, import_history_exports, write_manifest

router = APIRouter()

LOGGER = logging.getLogger(__name__)


def _source_status() -> list[dict[str, Any]]:
    """按 ledger 的 `asset.location` 逐个报告来源可达性。

    脱盘是来源级的：本地硬盘拔掉时 115/PikPak 照常可播，反过来也一样。
    """
    rows: list[dict[str, Any]] = []
    for location, declared_roots in LOCATION_ROOT_DECLARATIONS.items():
        roots: list[dict[str, Any]] = []
        for declared in declared_roots:
            resolved = translate_ledger_path(declared)
            mapped = not is_unmapped(resolved)
            roots.append({
                "declared": declared,
                "resolved": str(resolved) if mapped else None,
                "mapped": mapped,
                "online": bool(mapped and root_online(resolved)),
            })
        # 一个来源可以有几个根；只要有一个不在，整个来源就按脱盘处理，宁可少播不可误判。
        rows.append({
            "location": location,
            "roots": roots,
            "mapped": all(root["mapped"] for root in roots),
            "online": all(root["online"] for root in roots),
        })
    # 在线资源是 URL，不依赖任何挂载点。
    rows.append({
        "location": "online", "declared": None, "resolved": None,
        "mapped": True, "online": True,
    })
    return rows


@router.get("/api/providers")
def provider_health(request: Request, args: dict[str, str] = Depends(require_auth)):
    return request.app.state.providers.health()


@router.get("/api/sources")
def source_health(request: Request, args: dict[str, str] = Depends(require_auth)):
    """无副作用的来源可达性。前端据此把脱盘来源的筛选置灰。"""
    rows = _source_status()
    return {
        "ok": True,
        "sources": rows,
        "offline": [row["location"] for row in rows if not row["online"]],
    }


@router.post("/api/reveal")
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
    asset = request.app.state.repository.media_asset(asset_id)
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


@router.get("/api/providers/opencode-go/models")
def opencode_go_models(request: Request, args: dict[str, str] = Depends(require_auth)):
    try:
        models = request.app.state.opencode_go.list_models()
    except ProviderUnavailable:
        return JSONResponse({"error": "provider unavailable"}, status_code=502)
    return {"ok": True, "provider": "opencode-go", "models": models}


@router.post("/api/taste/import")
async def taste_import(
    request: Request,
    _args: dict[str, str] = Depends(require_auth),
):
    """Stream one private history export to local storage, then import it.

    This deliberately avoids multipart/form-data and its extra parser dependency.  The
    browser sends the file bytes as-is and provides only a display filename header.
    """
    contract = request.app.state.web_contract
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


@router.get("/api/{route:path}")
def api_get(request: Request, route: str, args: dict[str, str] = Depends(require_auth)):
    state = request.app.state
    sync = state.sync
    try:
        payload = web_contract.dispatch_api_get(
            state.web_contract, f"/api/{route}", args)
        if route == "review" and sync is not None and sync.read_only:
            payload = state.review_mirror.resolve(payload)
        return payload
    except KeyError:
        return JSONResponse({"error": "not found"}, status_code=404)
    except (TypeError, ValueError) as exc:
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
    except Exception:
        LOGGER.exception("unhandled GET contract error for /api/%s", route)
        return JSONResponse({"error": "internal server error"}, status_code=500)


@router.post("/api/{route:path}")
def api_post(
    request: Request,
    route: str,
    body: dict[str, Any] = Body(default_factory=dict),
    _args: dict[str, str] = Depends(require_auth),
):
    sync = request.app.state.sync
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
        return web_contract.dispatch_api_post(
            request.app.state.web_contract, route_path, body)
    except KeyError:
        return JSONResponse({"error": "not found"}, status_code=404)
    except (TypeError, ValueError) as exc:
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=400)
    except Exception:
        LOGGER.exception("unhandled POST contract error for /api/%s", route)
        return JSONResponse({"error": "internal server error"}, status_code=500)
