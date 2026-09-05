"""本机配置的 JSON 契约：读取、校验、原子保存与托盘重启请求。

页面本体是 `frontend/src/islands/configuration.tsx`，挂在主站的 `/configuration` 路由里
（ADR-0022）；这里只回数据。两道门都在服务端：只放行回环地址，只在独立包里可写。
手机上的管理菜单不列这一页，靠的是 `/healthz` 的 `configurable`，但那只是入口的显隐，
拒绝写入的判定在这里。
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import os
import shutil
import threading
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from . import distribution, folder_picker, onboarding, settings_file, media_configuration
from .routes_auth import require_auth
from .routes_pages import runtime_facts

router = APIRouter()
_SAVE_LOCK = threading.Lock()
RELOAD_NAME = onboarding.RELOAD_NAME
#: 不在独立包里时页面上代替表单的那句话。
FILE_MANAGED_NOTICE = "此部署通过配置文件管理服务，请在本机编辑下方的设置文件。"


def revision(config) -> str:
    return hashlib.sha256(config.path.read_bytes()).hexdigest()


def loopback_client(request: Request) -> bool:
    """请求来自运行 Peach 的这台电脑。`/healthz` 与两个端点共用同一判据。"""
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        return False
    if distribution.standalone() and request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        return False
    return True


def local_only(request: Request) -> None:
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(403, "请在运行 Peach 的电脑上打开配置")
    if distribution.standalone() and request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise HTTPException(403, "请使用本机地址打开配置")


def configurable(request: Request) -> bool:
    """这次请求的发起方能不能改这台机器的配置：独立包、已配置、且来自回环地址。"""
    return (distribution.standalone() and bool(request.app.state.settings.configured)
            and loopback_client(request))


def snapshot(config) -> dict[str, Any]:
    """配置页首屏要的一切：当前值、修订号、可写与否，以及这台机器的运行信息。"""
    editable = distribution.standalone()
    media = config.mounts.get("local") or config.locations.get("local", ())
    return {
        "editable": editable,
        "notice": "" if editable else FILE_MANAGED_NOTICE,
        "revision": revision(config),
        "media_dirs": list(media),
        "media_sources": media_configuration.rows(config, windows=os.name == "nt", probe=True),
        "windows": os.name == "nt",
        "port": config.server.port,
        "facts": [{"term": term, "value": value} for term, value in runtime_facts(config)],
    }


@router.get("/api/configuration")
def read_configuration(request: Request, _args=Depends(require_auth)):
    local_only(request)
    config = settings_file.load_config()
    if not config.present:
        raise HTTPException(409, "请先完成首次设置")
    return snapshot(config)


def _validate(body: dict[str, Any], config) -> tuple[dict[str, Any], dict[str, Any]]:
    """逐项校验，错误按字段归位：文件夹按行、端口一句。全对时第一个返回值为空。"""
    errors: dict[str, Any] = {}
    validated: dict[str, Any] = {}
    raws = body.get("media_dirs")
    rows = [str(item) for item in raws] if isinstance(raws, list) else [str(raws or "")]
    if "media_sources" in body:
        locations, mounts, problems = media_configuration.validate(body["media_sources"], windows=os.name == "nt")
        paths = []
        validated.update(locations=locations, mounts=mounts)
    else:
        paths, problems = onboarding.read_media_dirs(
            rows, validate=onboarding.media_dir_validator(windows=os.name == "nt"))
    if problems:
        errors["media_dirs"] = problems
    else:
        validated["media_dirs"] = paths
    try:
        port = onboarding.validate_port(str(body.get("port", "")))
        onboarding.check_available_port(port, config.server.port)
        validated["port"] = port
    except ValueError as exc:
        errors["port"] = str(exc)
    return errors, validated


def same_origin(request: Request) -> None:
    """浏览器发来的写请求必须来自 Peach 自己的页面：带了别处的 Origin 就拒。"""
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "请从 Peach 配置页提交")


@router.post("/api/pick-folder")
def pick_folder(request: Request, body: dict[str, Any] = Body(default_factory=dict),
                _args=Depends(require_auth)):
    """让运行 Peach 的这台电脑弹系统文件夹对话框，选中的绝对路径交回页面。

    只对回环地址开放：否则局域网里任何人都能让这台电脑弹窗。首启页和配置页共用这一条，
    所以不要求独立包。对话框是模态的，一次只开一个；用户取消时 `path` 为 None。
    """
    local_only(request)
    same_origin(request)
    initial = body.get("initial")
    try:
        path = folder_picker.pick_folder(initial if isinstance(initial, str) and initial else None)
    except folder_picker.PickerBusy as exc:
        raise HTTPException(409, str(exc)) from exc
    except folder_picker.PickerUnavailable as exc:
        raise HTTPException(501, str(exc)) from exc
    return {"path": path}


@router.post("/api/configuration")
def save_configuration(request: Request, body: dict[str, Any] = Body(default_factory=dict),
                       _args=Depends(require_auth)):
    local_only(request)
    if not distribution.standalone():
        raise HTTPException(409, "此部署通过配置文件管理服务")
    same_origin(request)
    with _SAVE_LOCK:
        config = settings_file.load_config()
        if not config.present:
            raise HTTPException(409, "请先完成首次设置")
        if body.get("revision") != revision(config):
            raise HTTPException(409, "配置已变更，请刷新后再保存")
        errors, validated = _validate(body, config)
        if errors:
            # 400 的响应体带每个字段的原因：页面把它写回出错的那一行底下，不是弹一句总话。
            raise HTTPException(400, {"message": "有几项需要修改", "errors": errors})
        paths = validated["media_dirs"]
        locations, mounts = dict(config.locations), dict(config.mounts)
        if "locations" in validated:
            locations, mounts = validated["locations"], validated["mounts"]
            for key in set(config.locations) - dict(media_configuration.SOURCE_OPTIONS).keys():
                locations[key] = config.locations[key]
                if key in config.mounts:
                    mounts[key] = config.mounts[key]
        elif os.name == "nt":
            locations["local"] = tuple(str(path) for path in paths)
        else:
            locations["local"] = onboarding.posix_declared_roots(len(paths))
            mounts["local"] = tuple(str(path) for path in paths)
        prepared = replace(config, locations=locations, mounts=mounts,
                           server=replace(config.server, port=validated["port"]))
        temporary = config.path.with_suffix(".pending.toml")
        try:
            shutil.copy2(config.path, config.path.with_suffix(".previous.toml"))
            temporary.write_text(settings_file.render(prepared), encoding="utf-8")
            os.replace(temporary, config.path)
            if body.get("scan_now"):
                onboarding.request_first_scan(prepared, "configured")
            config.directory("state").mkdir(parents=True, exist_ok=True)
            (config.directory("state") / RELOAD_NAME).write_text("reload", encoding="utf-8")
        except OSError as exc:
            raise HTTPException(500, f"配置保存失败：{exc}") from exc
    return {"saved": True, "url": f"http://127.0.0.1:{prepared.server.port}/",
            "revision": revision(prepared)}
