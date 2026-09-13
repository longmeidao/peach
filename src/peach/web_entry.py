"""入口页共用件：首启、登录与配置页都要的内联样式和运行信息。

这些页面不加载 `app.js`，样式得随 HTML 一起送到；运行信息则被首启完成页、登录页
和 `/api/configuration` 共用。三个路由模块都要，就不能住在其中任何一个里：那会让
路由层互相导入成环。放在 web 层，路由模块单向依赖它，`tests/test_module_layering.py`
守着这个方向。
"""
from __future__ import annotations

from .config import PROJECT_ROOT


def board_entry_style() -> str:
    """入口页内联公共视觉层。首启和登录页不加载 app.js，样式得随 HTML 一起送到。"""
    css = (PROJECT_ROOT / "web/board-entry.css").read_text(encoding="utf-8")
    return f'<style id="boardEntryStyles">{css}</style>'


def runtime_facts(config) -> tuple[tuple[str, str], ...]:
    """这台机器上 Peach 的位置与版本：设置完成页和 `/api/configuration` 共用同一份。"""
    from . import __version__
    import platform as system_platform
    from .ffmpeg import FFmpegResolver

    available = FFmpegResolver(config.directory("tools") / "ffmpeg").ffmpeg() is not None
    ffmpeg = "可用" if available else "未安装；MP4 可直接播放，转码和缩略图需要安装 FFmpeg。"
    return (
        ("版本", __version__),
        ("操作系统", system_platform.system()),
        ("数据目录", str(config.data_root)),
        ("设置文件", str(config.path)),
        ("日志目录", str(config.directory("logs"))),
        ("FFmpeg", ffmpeg),
    )


def runtime_fact_entries(config) -> list[dict[str, str]]:
    """运行信息中的缺失依赖附带官方下载入口。"""
    from .ffmpeg import FFmpegResolver
    entries = [{"term": term, "value": value} for term, value in runtime_facts(config)]
    resolver = FFmpegResolver(config.directory("tools") / "ffmpeg")
    missing = [name for name, choice in (("FFmpeg", resolver.ffmpeg()), ("ffprobe", resolver.ffprobe()))
               if choice is None]
    if missing:
        entry = next(row for row in entries if row["term"] == "FFmpeg")
        entry.update(value="未找到 " + "、".join(missing) + "；转码、媒体信息与缩略图需要 FFmpeg 工具包。",
                     download_url="https://ffmpeg.org/download.html", download_label="下载 FFmpeg")
    return entries
