"""本机配置表单：读取、校验、原子保存与托盘应用请求。"""
from __future__ import annotations

from dataclasses import replace
import hashlib
from html import escape
import os
import shutil
import threading
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from . import __version__, distribution, onboarding, settings_file
from .routes_auth import require_page_auth
from .routes_pages import _document, _field_html
from .ffmpeg import FFmpegResolver

router = APIRouter()
_SAVE_LOCK = threading.Lock()
RELOAD_NAME = onboarding.RELOAD_NAME


def revision(config) -> str:
    return hashlib.sha256(config.path.read_bytes()).hexdigest()


def page(config, *, values=None, errors=None, saved=False) -> str:
    values, errors = values or {}, errors or {}
    media = config.mounts.get("local") or config.locations.get("local", "")
    body = '<a href="/">返回馆藏</a><h1>配置 Peach</h1>'
    if saved:
        url = f"http://127.0.0.1:{config.server.port}/"
        body += ('<p role="status">配置已保存，正在重新启动服务。</p>'
                 f'<p><a href="{url}">进入馆藏</a></p>'
                 f'<meta http-equiv="refresh" content="8;url={url}">')
    else:
        body += '<p>管理这台电脑的媒体文件夹和访问端口。</p>'
    if distribution.standalone() and not saved:
        body += '<form method="post" action="/configuration">'
        body += f'<input type="hidden" name="revision" value="{revision(config)}">'
        for question in onboarding.questions(config, windows=os.name == "nt"):
            if question.key not in {"media_dir", "port"}:
                continue
            default = media if question.key == "media_dir" else str(config.server.port)
            body += _field_html(question, values.get(question.key, default),
                                errors.get(question.key, ""), "")
        body += ('<label class="check"><input type="checkbox" name="scan_now" value="y">'
                 '保存后扫描媒体文件夹</label><button type="submit">保存配置</button></form>')
    elif not distribution.standalone():
        body += '<p>此部署通过配置文件管理服务，请在本机编辑下方文件。</p>'
    available = FFmpegResolver(config.directory("tools") / "ffmpeg").ffmpeg() is not None
    body += ('<h2>运行信息</h2><dl>'
             f'<dt>版本</dt><dd>{escape(__version__)}</dd>'
             f'<dt>数据目录</dt><dd>{escape(str(config.data_root))}</dd>'
             f'<dt>配置文件</dt><dd>{escape(str(config.path))}</dd>'
             f'<dt>日志目录</dt><dd>{escape(str(config.directory("logs")))}</dd>'
             f'<dt>FFmpeg</dt><dd>{"可用" if available else "未安装；MP4 可直接播放，转码和缩略图需要安装 FFmpeg。"}</dd></dl>')
    return _document("Peach · 配置", body)


def local_only(request):
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(403, "请在运行 Peach 的电脑上打开配置")
    if distribution.standalone() and request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise HTTPException(403, "请使用本机地址打开配置")


@router.get("/configuration", response_class=HTMLResponse)
def configuration(request: Request, _args=Depends(require_page_auth)):
    local_only(request)
    config = settings_file.load_config()
    if not config.present:
        raise HTTPException(409, "请先完成首次设置")
    return HTMLResponse(page(config), headers={"Cache-Control": "no-store"})


@router.post("/configuration", response_class=HTMLResponse)
async def save_configuration(request: Request, _args=Depends(require_page_auth)):
    local_only(request)
    if not distribution.standalone():
        raise HTTPException(409, "此部署通过配置文件管理服务")
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "请从 Peach 配置页提交")
    form = parse_qs((await request.body()).decode("utf-8", "replace"), keep_blank_values=True)
    values = {key: value[0] for key, value in form.items()}
    with _SAVE_LOCK:
        config = settings_file.load_config()
        if values.get("revision") != revision(config):
            raise HTTPException(409, "配置已变更，请刷新后再保存")
        errors, validated = {}, {}
        validators = {"media_dir": onboarding.media_dir_validator(windows=os.name == "nt"),
                      "port": onboarding.validate_port}
        for key, validator in validators.items():
            try:
                validated[key] = validator(values.get(key, ""))
            except ValueError as exc:
                errors[key] = str(exc)
        if errors:
            return HTMLResponse(page(config, values=values, errors=errors), status_code=400)
        try:
            onboarding.check_available_port(validated["port"], config.server.port)
        except ValueError as exc:
            return HTMLResponse(page(config, values=values, errors={"port": str(exc)}), status_code=400)
        locations, mounts = dict(config.locations), dict(config.mounts)
        if os.name == "nt":
            locations["local"] = str(validated["media_dir"])
        else:
            locations["local"] = onboarding.POSIX_LOCAL_DECLARED_ROOT
            mounts["local"] = str(validated["media_dir"])
        prepared = replace(config, locations=locations, mounts=mounts,
                           server=replace(config.server, port=validated["port"]))
        temporary = config.path.with_suffix(".pending.toml")
        try:
            shutil.copy2(config.path, config.path.with_suffix(".previous.toml"))
            temporary.write_text(settings_file.render(prepared), encoding="utf-8")
            os.replace(temporary, config.path)
            if "scan_now" in form:
                onboarding.request_first_scan(prepared)
            config.directory("state").mkdir(parents=True, exist_ok=True)
            (config.directory("state") / RELOAD_NAME).write_text("reload", encoding="utf-8")
        except OSError as exc:
            raise HTTPException(500, f"配置保存失败：{exc}") from exc
    return HTMLResponse(page(prepared, saved=True), headers={"Cache-Control": "no-store"})
