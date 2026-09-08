"""本机配置的 JSON 契约：读取、校验、原子保存与托盘重启请求。

页面本体是 `frontend/src/islands/configuration.tsx`，挂在主站的 `/configuration` 路由里
（ADR-0022）；这里只回数据。两道门都在服务端：只放行本机连接，只在托盘管理的服务里可写。
手机上的管理菜单不列这一页，靠的是 `/healthz` 的 `configurable`，但那只是入口的显隐，
拒绝写入的判定在这里。
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import ipaddress
import os
import shutil
import threading
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from filelock import FileLock, Timeout

from . import access, distribution, folder_picker, onboarding, settings_file, media_configuration
from .routes_auth import require_auth
from .routes_pages import runtime_fact_entries
from . import release_updates, standalone_update, peach_proxy, desktop_startup, desktop_uninstall

router = APIRouter()
_SAVE_LOCK = threading.Lock()
RELOAD_NAME = onboarding.RELOAD_NAME
#: 直接由 CLI 管理的服务使用设置文件。
FILE_MANAGED_NOTICE = "此部署通过配置文件管理服务，请在本机编辑下方的设置文件。"


def managed_configuration() -> bool:
    """托盘负责消费配置保存后的重载标记。"""
    return distribution.standalone() or os.environ.get("PEACH_TRAY_MANAGED") == "1"


def revision(config) -> str:
    return hashlib.sha256(config.path.read_bytes()).hexdigest()


def local_client(request: Request) -> bool:
    """按连接两端的 IP 识别本机；Host 只用于校验允许的入口名称。"""
    if not request.client:
        return False
    server = request.scope.get("server")
    try:
        peer = ipaddress.ip_address(request.client.host)
        bound = ipaddress.ip_address(server[0]) if server else None
    except ValueError:
        # ASGI 测试或非 IP 绑定没有可比较的服务端 IP；回环客户端仍可识别。
        bound = None
        try:
            peer = ipaddress.ip_address(request.client.host)
        except ValueError:
            return False
    if not peer.is_loopback and (peer != bound or peer.is_unspecified):
        return False
    if managed_configuration():
        name = request.app.state.settings.mdns_name.lower().removesuffix(".local")
        hosts = {"127.0.0.1", "localhost", "::1", f"{name}.local"}
        if bound and not bound.is_unspecified:
            hosts.add(str(bound))
        if (request.url.hostname or "").lower().rstrip(".") not in hosts:
            return False
    return True


def local_only(request: Request) -> None:
    if not local_client(request):
        raise HTTPException(403, "请在运行 Peach 的电脑上打开配置")


def configurable(request: Request) -> bool:
    """配置只向已配置的托盘服务的本机调用方开放。"""
    return (managed_configuration() and bool(request.app.state.settings.configured)
            and local_client(request))


def snapshot(config) -> dict[str, Any]:
    """配置页首屏要的一切：当前值、修订号、可写与否，以及这台机器的运行信息。"""
    editable = managed_configuration()
    media = config.mounts.get("local") or config.locations.get("local", ())
    return {
        "startup": desktop_startup.snapshot(config),
        "uninstall": desktop_uninstall.snapshot(config),
        "peach_proxy": peach_proxy.describe(config.directory("secrets")),
        "updates": release_updates.snapshot(),
        "update_job": standalone_update.public(),
        "access": access.public(access.load(config.directory("secrets") / "access.json")),
        "editable": editable,
        "notice": "" if editable else FILE_MANAGED_NOTICE,
        "revision": revision(config),
        "media_dirs": list(media),
        "media_sources": media_configuration.rows(config, windows=os.name == "nt", probe=True),
        "mount_dependencies": media_configuration.mount_dependencies(),
        "windows": os.name == "nt",
        "port": config.server.port,
        "port_editable": distribution.standalone(),
        "facts": runtime_fact_entries(config),
    }


@router.get("/api/configuration")
def read_configuration(request: Request, _args=Depends(require_auth)):
    local_only(request)
    config = settings_file.load_config()
    if not config.present:
        raise HTTPException(409, "请先完成首次设置")
    result = snapshot(config)
    result["automatic_updates"] = request.app.state.automatic_updates.snapshot()
    if result["automatic_updates"].get("result"):
        result["updates"] = result["automatic_updates"]["result"]
    return result


@router.get("/api/configuration/automatic-updates")
def read_automatic_updates(request: Request, _args=Depends(require_auth)):
    local_only(request)
    return request.app.state.automatic_updates.snapshot()


@router.post("/api/configuration/automatic-updates")
def save_automatic_updates(request: Request, body: dict = Body(...), _args=Depends(require_auth)):
    local_only(request)
    same_origin(request)
    try:
        return request.app.state.automatic_updates.save(body)
    except (ValueError, OSError, Timeout) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/api/configuration/peach-proxy")
def save_peach_proxy(request: Request, body: dict = Body(...), _args=Depends(require_auth)):
    local_only(request)
    same_origin(request)
    try:
        return peach_proxy.save(settings_file.load_config().directory("secrets"), body)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/api/configuration/startup")
def save_startup(request: Request, body: dict = Body(...), _args=Depends(require_auth)):
    local_only(request)
    same_origin(request)
    try:
        return desktop_startup.save(settings_file.load_config(), enabled=body.get("enabled"), silent=body.get("silent"),
                                    desktop=body.get("desktop"))
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/api/configuration/uninstall")
def uninstall(request: Request, body: dict = Body(...), _args=Depends(require_auth)):
    local_only(request)
    same_origin(request)
    if body.get("confirmation") != "卸载 Peach":
        raise HTTPException(400, "请确认卸载 Peach")
    from .jobs import BackgroundJob
    if any(isinstance(job, BackgroundJob) and (job.snapshot() or {}).get("status") == "running"
           for job in vars(request.app.state.web_contract).values()):
        raise HTTPException(409, "后台任务正在运行，请完成后卸载")
    try:
        return desktop_uninstall.request(settings_file.load_config(), body.get("delete_data"))
    except (ValueError, Timeout) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/api/configuration/updates")
def check_updates(request: Request, _args=Depends(require_auth)):
    local_only(request)
    result = release_updates.check()
    request.app.state.automatic_updates.remember(result)
    return result


@router.get("/api/configuration/update-status")
def update_status(request: Request, _args=Depends(require_auth)):
    local_only(request)
    return standalone_update.public()


@router.post("/api/configuration/update")
def download_update(request: Request, _args=Depends(require_auth)):
    local_only(request)
    try:
        return standalone_update.start()
    except (ValueError, Timeout) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/api/configuration/update-restart")
def restart_update(request: Request, _args=Depends(require_auth)):
    local_only(request)
    contract = request.app.state.web_contract
    from .jobs import BackgroundJob
    if any(isinstance(job, BackgroundJob) and (job.snapshot() or {}).get("status") == "running"
           for job in vars(contract).values()):
        raise HTTPException(409, "后台任务正在运行，请完成后重启安装。")
    try:
        return standalone_update.request_restart()
    except (ValueError, Timeout) as exc:
        raise HTTPException(409, str(exc)) from exc


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
        names, icons = {}, {}
        if not problems:
            for index, row in enumerate(body["media_sources"]):
                name = str(row.get("library", "")).strip()
                if len(name) > 80 or any(ord(char) < 32 for char in name):
                    problems = [""] * len(body["media_sources"])
                    problems[index] = "媒体库名称请使用 1 到 80 个可见字符"
                    break
                root = str(media_configuration.PureWindowsPath(row["path"] if os.name == "nt" else row["root"]))
                if name:
                    names[root] = name
                from .media_libraries import LIBRARY_ICONS
                glyph = str(row.get("library_icon", ""))
                if glyph and glyph not in LIBRARY_ICONS:
                    problems = [""] * len(body["media_sources"])
                    problems[index] = "请选择列表中的媒体库图标"
                    break
                if glyph:
                    icons[root] = glyph
            validated["library_names"] = names
            validated["library_icons"] = icons
    else:
        paths, problems = onboarding.read_media_dirs(
            rows, validate=onboarding.media_dir_validator(windows=os.name == "nt"))
    if problems:
        errors["media_dirs"] = problems
    else:
        validated["media_dirs"] = paths
    try:
        port = onboarding.validate_port(str(body.get("port", config.server.port)))
        if distribution.standalone():
            onboarding.check_available_port(port, config.server.port)
        elif port != config.server.port:
            raise ValueError("访问端口由托盘管理")
        validated["port"] = port
    except ValueError as exc:
        errors["port"] = str(exc)
    return errors, validated


def same_origin(request: Request) -> None:
    """浏览器发来的写请求必须来自 Peach 自己的页面：带了别处的 Origin 就拒。"""
    origin = request.headers.get("origin")
    if request.headers.get("sec-fetch-site") == "cross-site" or (origin and origin.rstrip("/") != str(request.base_url).rstrip("/")):
        raise HTTPException(403, "请从 Peach 配置页提交")


@router.post("/api/configuration/access")
def save_access(request: Request, body: dict[str, Any] = Body(default_factory=dict),
                _args=Depends(require_auth)):
    local_only(request)
    same_origin(request)
    path = request.app.state.settings.access_path
    if not request.app.state.settings.configured or path is None:
        raise HTTPException(409, "请先完成首次设置")
    if any(not isinstance(body.get(key, ""), str) for key in ("password", "confirmation", "current_password")):
        raise HTTPException(400, "密码需要是文字")
    password = body.get("password", "")
    if body.get("action") not in {"set", "disable"}:
        raise HTTPException(400, "请选择设置或关闭密码")
    if body["action"] == "set" and not password:
        raise HTTPException(400, {"message": "请输入访问密码", "errors": {"password": "请输入访问密码"}})
    if body["action"] == "disable" and body.get("confirm_disable") is not True:
        raise HTTPException(400, "请确认允许能连接到 Peach 的设备直接访问")
    try:
        try:
            access.validate_password(password, body.get("confirmation", ""))
        except ValueError as exc:
            field = "confirmation" if password != body.get("confirmation", "") else "password"
            raise HTTPException(400, {"message": str(exc), "errors": {field: str(exc)}}) from exc
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(path.with_suffix(".lock")), timeout=0):
            policy = access.load(path)
            if body.get("revision") != policy["revision"]:
                raise HTTPException(409, "访问设置已变更，请刷新后再保存")
            if policy["mode"] == "locked":
                raise HTTPException(409, "访问设置无法读取，请在本机检查配置文件")
            if policy["mode"] == "password" and not access.verify(policy, body.get("current_password", "")):
                raise HTTPException(400, {"message": "当前访问密码不正确", "errors": {"current_password": "当前访问密码不正确"}})
            policy = access.save(path, password if body["action"] == "set" else "")
    except Timeout:
        raise HTTPException(409, "访问设置正在保存，请稍后重试") from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    response = JSONResponse(access.public(policy), headers={"Cache-Control": "no-store"})
    response.delete_cookie("tok", path="/")
    response.delete_cookie(access.COOKIE, path="/")
    if policy["mode"] == "password":
        from .routes_auth import set_auth_cookie
        set_auth_cookie(response, request, login=True)
    return response


@router.post("/api/pick-folder")
def pick_folder(request: Request, body: dict[str, Any] = Body(default_factory=dict),
                _args=Depends(require_auth)):
    """让运行 Peach 的这台电脑弹系统文件夹对话框，选中的绝对路径交回页面。

    只对本机连接开放：系统对话框显示在运行 Peach 的电脑上。首启页和配置页共用这一条，
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
    if not managed_configuration():
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
                           library_names=validated.get("library_names", config.library_names),
                           library_icons=validated.get("library_icons", config.library_icons),
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
    url = f"http://127.0.0.1:{prepared.server.port}/" if distribution.standalone() else str(request.base_url)
    return {"saved": True, "url": url,
            "revision": revision(prepared)}
