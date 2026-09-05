"""单页界面本体、它的静态资产，以及所有前端路由的落点。

这里的路由全部指向同一份 `index.html`：前端自己按 URL 渲染，服务端只负责让刷新
和直接粘地址都能进来。所以 `client_route` 的那一长串装饰器不是重复，是「前端有哪些
路由」的声明，新增页面必须在这里补一行，否则刷新就是 404。

`index` 的 401 走跳登录页，`/app.css`、`/app.js`、`/js/`、`/dist/` 走 PlainText 提示：
资产被浏览器直接请求，重定向到登录页只会让它把 HTML 当脚本解析。

缓存也分两档：`index.html` 是 `no-store`，它是所有资产 URL 的来源；四类资产走
`asset_response()` 的 ETag 复验，更新语义与 `no-store` 相同但没变时零传输。

`/app.css` 是唯一一个不对应单个文件的资产：样式表按分区拆在 `web/css/` 下，这里
按文件名顺序拼起来交付，见 `stylesheet_response()`。
"""
from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping, Sequence
import re

from html import escape
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)

from . import auth, distribution, onboarding, settings_file
from .config import PROJECT_ROOT
from .routes_auth import require_asset_auth, require_page_auth, set_auth_cookie
from .web_state import FAVICON

router = APIRouter()

#: 回环地址的三种写法。既用来判提交端点的调用方，也用来判「只有这台电脑」那个监听选择。
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost"})

#: 首次运行页的样式。刻意不引用 `web/` 里的任何资产：那一套一上来就会去打
#: `/api/items`，而未配置的机器还没有数据库，页面只会是一屏红色报错。这一页因此
#: 落在 SPA 外壳之外，不是一个 `frontend/` island（ADR-0022、docs/FRONTEND.md）。
_SETUP_STYLE = """<style>
*{box-sizing:border-box}
body{margin:0;padding:48px 24px;background:var(--ground);color:var(--ink);
font:var(--fs-md)/1.6 system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:560px;margin:0 auto}
body:has(.error-page){min-height:100svh;display:grid;align-items:center}
body:has(.error-page)>main{width:min(560px,100%)}
.error-page{display:grid;justify-items:start;gap:32px}
.error-page>h1,.error-page>p{margin:0}
.mark{display:block;width:40px;height:40px;border-radius:50%}
h1{font-size:var(--fs-3xl);font-weight:600;line-height:1.25;margin:16px 0 0}
.lede{margin:6px 0 0;color:var(--muted)}
h2{font-size:var(--fs-lg);font-weight:600;margin-top:32px;padding-top:24px;border-top:1px solid var(--line)}
p{color:var(--ink-2)}a{color:var(--tungsten);text-decoration:none}
a:hover{text-decoration:none}
code{font:var(--fs-xs)/1.5 ui-monospace,Consolas,"Cascadia Mono",monospace;
background:var(--surface);border:1px solid var(--line-soft);border-radius:var(--badge-radius);
padding:2px 6px;overflow-wrap:anywhere}
dt{color:var(--muted);font-size:var(--fs-sm)}dd{margin:0 0 12px;overflow-wrap:anywhere}
form{margin-top:32px}
.field{margin-top:24px}
.field>label,.field>.legend{display:block;margin:0 0 8px;font-weight:500;color:var(--ink)}
.req{color:var(--drop);margin-right:4px}
input[type=text],input[type=number]{width:100%;height:var(--control-h);padding:0 12px;
border:1px solid var(--line);border-radius:var(--control-radius);background:var(--ground);
color:var(--ink);font:inherit}
.affix{display:flex;align-items:center;height:var(--control-h);border:1px solid var(--line);
border-radius:var(--control-radius);background:var(--ground)}
.affix input[type=text]{flex:1 1 auto;min-width:0;height:100%;border:0;border-radius:0;background:transparent}
.affix input[type=text]:focus-visible{outline:0}
.affix:focus-within{outline:2px solid var(--tungsten);outline-offset:3px}
.affix>span{flex:none;padding:0 12px;height:100%;display:grid;place-items:center;
color:var(--muted);border-left:1px solid var(--line-soft)}
.affix>span:first-child{border-left:0;border-right:1px solid var(--line-soft)}
.affix:has(input:disabled){background:var(--surface);border-color:var(--border-15)}
.affix input:disabled{color:var(--muted);cursor:not-allowed}
.field:has(input:disabled) .req{visibility:hidden}
.switch{display:grid;grid-template-columns:1fr 1fr;padding:3px;border:1px solid var(--line-soft);
border-radius:var(--surface-radius);background:var(--surface)}
.switch label{position:relative;display:grid;place-items:center;height:calc(var(--control-h) - 8px);padding:0 14px;
border-radius:var(--control-radius);color:var(--ink-2);cursor:pointer}
.switch input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.switch label:hover{color:var(--ink)}
.switch label:has(input:checked){background:var(--hover);color:var(--ink)}
.switch label:has(input:focus-visible){outline:2px solid var(--tungsten);outline-offset:2px}
:focus-visible{outline:2px solid var(--tungsten);outline-offset:3px}
.help{margin:6px 0 0;color:var(--muted);font-size:var(--fs-sm)}
/* 高级设置是 Geist Collapse：summary 是触发器，chevron 紧跟标题，与高度一样 200ms ease-in-out；
   折叠体由 /js/ui-components.js 的 wireCollapse 接管。 */
details{margin-top:24px}
summary{display:flex;align-items:center;gap:8px;min-height:44px;
cursor:pointer;list-style:none;font-weight:500;color:var(--ink)}
summary::-webkit-details-marker{display:none}
summary svg{width:16px;height:16px;flex:none;stroke:currentColor;fill:none;stroke-width:2;
stroke-linecap:round;stroke-linejoin:round;color:var(--muted);transition:transform .2s ease-in-out}
details[open] summary svg{transform:rotate(180deg)}
/* 折叠体裁切溢出，输入框的焦点环（2px 环加 3px 间距）会被切掉：把裁切框往外放 6px，
   横向靠 .fcollapse 的负外边距，纵向靠 .fcollapsebody 的内边距——内边距不能落在
   .fcollapse 自己身上，否则高度收不到 0。 */
.fcollapse{overflow:hidden;transition:height .2s ease-in-out;margin:0 -6px;padding:0 6px}
.fcollapsebody{padding:6px 0}
details .field{margin-top:0}
details .field+.field{margin-top:24px}
.bad{margin:6px 0 0;color:var(--drop);font-size:var(--fs-sm)}
.check{display:flex;align-items:center;gap:12px;min-height:44px;margin:24px 0 0;cursor:pointer}
.pcheck{position:relative;display:grid;place-items:center;width:20px;height:20px;flex:none}
.pcheck input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.pcheck>span{width:18px;height:18px;border:1px solid var(--border-15);border-radius:var(--badge-radius);
display:grid;place-items:center;background:var(--ground);color:transparent}
.pcheck>span svg{display:block;width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2.5}
.check:hover .pcheck>span{background:var(--hover)}
.pcheck input:checked+span{border-color:var(--ink-2);color:var(--ink)}
.pcheck input:focus-visible+span{outline:2px solid var(--tungsten);outline-offset:2px}
button[type=submit]{margin-top:32px;width:100%;height:var(--control-h);border:1px solid var(--ink);
border-radius:var(--control-radius);cursor:pointer;background:var(--ink);color:var(--ground);
font:500 var(--fs-md) system-ui,sans-serif}
button[type=submit]:hover{background:color-mix(in srgb,var(--ink) 88%,var(--ground));color:var(--ground)}
/* 一行：输入框、选择文件夹、移除。flex 而不是 grid：只剩一行时移除键隐藏，
   grid 的空轨道会留下一段 gap。 */
.dir{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.dir:first-child{margin-top:0}.dir .bad{flex-basis:100%;margin:0}
.dir input[type=text]{flex:1 1 auto;width:auto;min-width:0}
.dir > input[type=text]{flex:1 1 0;width:0}
.sourcefields{flex-basis:100%;display:grid;gap:8px;min-width:0}
.sourcefields select{width:100%;height:var(--control-h);border:1px solid var(--line-soft);border-radius:var(--control-radius);background:var(--surface);color:var(--ink);padding:0 12px;font:inherit}
.sourcefields select:focus-visible{outline:2px solid var(--tungsten);outline-offset:2px}
.rm,.pick,.add{height:var(--control-h);border:1px solid var(--line);border-radius:var(--control-radius);
background:var(--ground);color:var(--ink);cursor:pointer;font:500 var(--fs-sm) system-ui,sans-serif}
.rm,.pick{width:var(--control-h);flex:none;display:grid;place-items:center;color:var(--muted)}
.rm svg,.pick svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;
stroke-linejoin:round}
.pick[aria-busy=true]{color:var(--muted);cursor:progress}
.add{margin-top:8px;padding:0 12px}
.rm:hover,.pick:hover,.add:hover{background:var(--hover);color:var(--ink)}
.rm[hidden],.pick[hidden],.add[hidden]{display:none}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media(max-width:760px){input[type=text],input[type=number]{font-size:16px}}
@media(max-width:560px){body{--control-h:44px}.sourcefields select{font-size:var(--fs-lg)}}
@media(max-width:440px){body{padding:24px 20px}h1{font-size:var(--fs-2xl)}}
</style>"""

_SETUP_HEAD = ('<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width,initial-scale=1">'
               '<meta name="color-scheme" content="light dark">'
               '<link rel="icon" href="/peach-logo.png" type="image/png">')

#: 键 -> 页面上的题目与一句说明。顺序、默认值与校验仍然来自 `onboarding.questions()`，
#: 这里只决定同一道题在浏览器里怎么称呼：命令行那份题面要把可选值写进去，页面用控件表达。
_SETUP_COPY = {
    "data_root": ("数据目录", "Peach 数据库、缓存和设置文件都放在这里。"),
    "media_dir": ("媒体文件夹", "Peach 从这些文件夹读取视频和图片。可以是外置硬盘上的文件夹，但必须已经存在。"),
    "host": ("谁可以访问", ""),
    "port": ("端口", "浏览器地址里冒号后面的数字，一般不用改。"),
    "mdns_name": ("局域网访问地址", "选了「同一局域网的设备」之后，其他设备在浏览器里输入这个地址就能打开 Peach。"),
}
#: 「谁可以访问」在页面上的顺序：局域网在左边，也是默认选项——Peach 的本意就是给
#: 同一局域网里的设备看。命令行问答按 `HOST_OPTIONS` 的编号顺序念，两边取值一致。
_HOST_ORDER = ("2", "1")

#: 选「只有这台电脑」时局域网地址没有意义，输入框跟着禁用；禁用的字段不随表单提交，
#: 服务端按题目默认值补上。没有脚本时两个字段都可编辑，提交照样成立。
#: 媒体文件夹列表的「添加文件夹」与每行的移除键也在这里亮出来：只剩一行时移除键隐藏。
_SETUP_SCRIPT = """<script>
(function(){
  var radios=document.querySelectorAll('input[name="host"]');
  var field=document.getElementById('f-mdns_name');
  if(radios.length&&field){
    var sync=function(){
      var lan=false;
      radios.forEach(function(radio){if(radio.checked&&radio.value==="2"){lan=true;}});
      field.disabled=!lan;
    };
    radios.forEach(function(radio){radio.addEventListener('change',sync);});
    sync();
  }
  var list=document.getElementById('dirs');
  var add=document.getElementById('add-dir');
  var template=document.getElementById('dir-row');
  if(!list||!add||!template){return;}
  var rows=function(){return list.querySelectorAll('.dir');};
  var refresh=function(){
    var all=rows();
    all.forEach(function(row){
      row.querySelector('.rm').hidden=all.length<2;
      row.querySelector('.pick').hidden=false;
    });
  };
  /* 「选择文件夹」让运行 Peach 的这台电脑弹系统对话框，把选中的绝对路径填回这一行：
     浏览器自己拿不到本机绝对路径。等待期间按钮置忙，再点不发第二个请求。 */
  var pickFolder=function(row,button){
    if(button.getAttribute('aria-busy')==='true'){return;}
    var input=row.querySelector('input');
    var bad=row.querySelector('.bad');
    button.setAttribute('aria-busy','true');button.setAttribute('aria-disabled','true');
    fetch('/api/pick-folder',{method:'POST',credentials:'same-origin',
      headers:{'Accept':'application/json','Content-Type':'application/json'},
      body:JSON.stringify({initial:input.value})})
      .then(function(response){return response.json().then(function(data){return {ok:response.ok,data:data};});})
      .then(function(result){
        if(!result.ok){throw new Error((result.data&&result.data.error)||'没能打开文件夹对话框');}
        if(result.data.path){
          input.value=result.data.path;input.setAttribute('aria-invalid','false');
          if(bad){bad.remove();}
        }
        input.focus();
      })
      .catch(function(error){
        var note=bad||document.createElement('p');
        note.className='bad';note.setAttribute('role','alert');note.textContent=error.message;
        row.appendChild(note);
      })
      .then(function(){button.removeAttribute('aria-busy');button.removeAttribute('aria-disabled');});
  };
  list.addEventListener('click',function(event){
    var pick=event.target.closest('.pick');
    if(pick){pickFolder(pick.closest('.dir'),pick);return;}
    var remove=event.target.closest('.rm');
    if(!remove||rows().length<2){return;}
    remove.closest('.dir').remove();
    refresh();
    add.focus();
  });
  add.addEventListener('click',function(){
    var row=template.content.firstElementChild.cloneNode(true);
    list.appendChild(row);
    refresh();
    row.querySelector('input').focus();
  });
  add.hidden=false;
  refresh();
})();
</script>"""

#: 与站内共用勾选框相同的字形（lucide `check`）。这一页不加载站内脚本，所以内联一份。
_CHECK_SVG = ('<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M20 6 9 17l-5-5"/></svg>')
#: 移除一行媒体文件夹的字形（lucide `x`）。
_X_SVG = '<svg viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>'
#: 「选择文件夹」（lucide `folder-search`）：弹系统对话框去挑一个文件夹。`folder-open` 归
#: 站内的「打开位置」，不兼任。
_FOLDER_SVG = ('<svg viewBox="0 0 24 24"><path d="M10.7 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 '
               '1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v4.1"/><path d="m21 21-1.9-1.9"/>'
               '<circle cx="17" cy="17" r="3"/></svg>')
#: 折叠触发器右侧的 chevron（lucide `chevron-down`），展开时转 180 度。
_CHEVRON_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
#: 两样东西借自站内共用控件：整页的覆盖式滚动条（原生那条藏掉，滑块浮在内容上），
#: 以及高级设置的折叠（原生 <details> 不过渡高度）。页面里没有 <details> 时 wireCollapse
#: 什么也不做，所以每张页面都挂同一段脚本。
_SHARED_SCRIPT = ('<script type="module">import{attachOverlayScrollbar,wireCollapse}from"/js/ui-components.js";'
                  'attachOverlayScrollbar(document.documentElement,{variant:"page"});'
                  'wireCollapse(document,"details","setup-collapse");</script>')


def _theme_tokens() -> str:
    """主站 `01-base.css` 里的两套色板：浅色的 `:root` 和跟随系统的深色覆盖。

    首启页在 SPA 外壳之外，但它必须和主站同一副面孔：系统是深色时主站是深色，这一页
    也得是，否则设置完一跳进馆藏就像换了个产品。
    """
    base = (PROJECT_ROOT / "web" / "css" / "01-base.css").read_text(encoding="utf-8")
    light = re.search(r":root\s*\{[^}]+\}", base).group(0)
    dark = re.search(r"@media \(prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{[^}]+\}\}",
                     base).group(0)
    return light + dark


def _scrollbar_rules() -> str:
    """主站的覆盖式滚动条：轨道、滑块与「挂上之后才藏原生那条」三组规则，原样借用。

    首启页装不下时滚起来也得是同一条；只取 .ovtrack 到 [data-overlay-scrollbar] 那一段，
    不带 html 上无条件藏滚动条的那句——脚本没跑到时首启页要还有系统滚动条可用。
    """
    base = (PROJECT_ROOT / "web" / "css" / "01-base.css").read_text(encoding="utf-8")
    rules = re.search(r"\.ovtrack\{.*?\[data-overlay-scrollbar\]::-webkit-scrollbar\{[^}]*\}", base, re.S).group(0)
    return re.sub(r"/\*.*?\*/\n?", "", rules, flags=re.S)


def error_page(status: int, message: str) -> str:
    """浏览器导航撞上 403／404／409 时给人看的那一页，不是一行 JSON。"""
    title = {403: "这里不能打开", 404: "四〇四", 409: "现在不能这样做"}.get(status, "出了点问题")
    description = '' if status == 404 else f'<p class="lede">{escape(message)}</p>'
    body = (f'<section class="error-page"><img class="mark" src="/peach-logo.png" alt=""><h1>{title}</h1>'
            f'{description}<p><a class="geist-button primary" href="/">返回首页</a></p></section>')
    return _document(f"Peach · {title}", body)


def _button_rules() -> str:
    """独立页面直接使用主站的 Geist Button 规则。"""
    base = (PROJECT_ROOT / "web/css/01-base.css").read_text(encoding="utf-8")
    return '\n'.join(re.findall(r'^\.geist-button[^{}]*\{[^}]*\}', base, re.M))


def _document(title: str, body: str) -> str:
    # 页内脚本对两张页面都生效：找不到对应控件时它什么也不做。
    return (f"{_SETUP_HEAD}<title>{title}</title><style>{_theme_tokens()}{_scrollbar_rules()}</style>"
            f"{_SETUP_STYLE}<style>{_button_rules()}</style></head><body><main>{body}</main>{_SETUP_SCRIPT}{_SHARED_SCRIPT}</body></html>\n")


def _check_html(name: str, text_html: str, *, checked: bool) -> str:
    """站内共用的自绘勾选框：文字与框同属一个 label，没有点不到的缝。"""
    return (f'<label class="check"><span class="pcheck"><input type="checkbox" name="{name}" value="y"'
            + (" checked" if checked else "")
            + f'><span aria-hidden="true">{_CHECK_SVG}</span></span><span>{text_html}</span></label>')


def runtime_facts(config) -> tuple[tuple[str, str], ...]:
    """这台机器上 Peach 的位置与版本：设置完成页和 `/api/configuration` 共用同一份。"""
    from . import __version__
    from .ffmpeg import FFmpegResolver

    available = FFmpegResolver(config.directory("tools") / "ffmpeg").ffmpeg() is not None
    ffmpeg = "可用" if available else "未安装；MP4 可直接播放，转码和缩略图需要安装 FFmpeg。"
    return (
        ("版本", __version__),
        ("数据目录", str(config.data_root)),
        ("设置文件", str(config.path)),
        ("日志目录", str(config.directory("logs"))),
        ("FFmpeg", ffmpeg),
    )


def runtime_facts_html(config) -> str:
    return ("<h2>运行信息</h2><dl>"
            + "".join(f"<dt>{escape(term)}</dt><dd>{escape(value)}</dd>"
                      for term, value in runtime_facts(config))
            + "</dl>")


def _copy_for(key: str, fallback: str) -> tuple[str, str]:
    return _SETUP_COPY.get(key, (fallback, ""))


def _media_dir_row(value: str, error: str, *, first: bool, location: str = "local", root: str = "", windows: bool = True) -> str:
    from .media_configuration import SOURCE_OPTIONS
    source = '<select name="media_location" aria-label="媒体来源">' + ''.join(
        f'<option value="{key}"{" selected" if key == location else ""}>{label}</option>'
        for key, label in SOURCE_OPTIONS) + '</select>'
    mapping = (f'<input name="media_root" type="text" aria-label="账本根目录" '
               f'placeholder="账本根目录，例如 B:\\" value="{escape(root, quote=True)}">') if not windows else ''
    attrs = ' id="f-media_dir" required' if first else ' aria-label="媒体文件夹"'
    return (f'<div class="dir"><input name="media_dir" type="text"{attrs} autocomplete="off" '
            f'spellcheck="false" aria-invalid="{"true" if error else "false"}" '
            f'value="{escape(value, quote=True)}">'
            f'<button type="button" class="pick" aria-label="选择文件夹" hidden>{_FOLDER_SVG}</button>'
            f'<button type="button" class="rm" aria-label="移除这个文件夹" hidden>{_X_SVG}</button>'
            + (f'<p class="bad" role="alert">{escape(error)}</p>' if error else "")
            + f'<div class="sourcefields">{source}{mapping}</div></div>')


def _media_dirs_html(values: Sequence[str], errors: Sequence[str], note: str, *, locations=(), roots=(), windows=True) -> str:
    """媒体文件夹列表：每行一个输入框，行尾是移除键，列表下是「添加文件夹」。

    移除键和添加键都带 `hidden`，由页面脚本亮出来：没有脚本时它们什么都做不了，与其留
    两个按不动的键，不如只给一个输入框。第一行必填，后面的行留空就当没填；错误写在
    出错的那一行底下。首次运行页与配置页共用这一段。
    """
    title, help_text = _copy_for("media_dir", "媒体文件夹")
    rows = list(values) or [""]
    body = "".join(
        _media_dir_row(value, errors[index] if index < len(errors) else "", first=index == 0,
                       location=locations[index] if index < len(locations) else "local",
                       root=roots[index] if index < len(roots) else "", windows=windows)
        for index, value in enumerate(rows))
    return (
        '<div class="field">'
        f'<label for="f-media_dir"><span class="req" aria-hidden="true">*</span>{escape(title)}</label>'
        f'<div class="dirs" id="dirs">{body}</div>'
        '<button type="button" class="add" id="add-dir" hidden>添加文件夹</button>'
        f'<template id="dir-row">{_media_dir_row("", "", first=False, windows=windows)}</template>'
        '<p class="help">CloudDrive：先在 CloudDrive 登录网盘并挂载，再选择对应的 115 或 PikPak 来源。'
        '<a href="https://www.clouddrive2.com/help.html" target="_blank" rel="noreferrer">挂载帮助</a></p>'
        + "".join(f'<p class="help">{escape(line)}</p>' for line in (help_text, note) if line)
        + "</div>"
    )


def _media_dir_values(values: Mapping[str, object], default: str) -> list[str]:
    """表单回显里的媒体文件夹：提交的是几行就几行，没提交过就一行默认值。"""
    raw = values.get("media_dir")
    if isinstance(raw, (list, tuple)):
        return [str(item) for item in raw] or [default]
    return [str(raw) if raw else default]


def _field_html(question, value: str, error: str, note: str) -> str:
    key = escape(question.key, quote=True)
    title, help_text = _copy_for(question.key, question.prompt)
    star = '<span class="req" aria-hidden="true">*</span>'
    if question.key == "host":
        labels = dict(onboarding.HOST_OPTIONS)
        options = "".join(
            f'<label><input type="radio" name="{key}" value="{escape(choice, quote=True)}"'
            f'{" checked" if choice == value else ""}><span>{escape(labels[choice])}</span></label>'
            for choice in _HOST_ORDER
        )
        control = (f'<div class="switch" role="radiogroup" aria-labelledby="l-{key}">'
                   f'{options}</div>')
        label = f'<span class="legend" id="l-{key}">{escape(title)}</span>'
    else:
        kind = "number" if question.key == "port" else "text"
        control = (f'<input id="f-{key}" name="{key}" type="{kind}" required autocomplete="off" '
                   f'spellcheck="false" aria-invalid="{"true" if error else "false"}" '
                   f'value="{escape(value, quote=True)}">')
        if question.key == "mdns_name":
            control = f'<div class="affix"><span>https://</span>{control}<span>.local</span></div>'
        label = f'<label for="f-{key}">{star}{escape(title)}</label>'
    tail = "".join(
        f'<p class="help">{escape(line)}</p>' for line in (help_text, note) if line)
    tail += f'<p class="bad" role="alert">{escape(error)}</p>' if error else ""
    return f'<div class="field">{label}{control}{tail}</div>'


def setup_page(
    config, *, windows: bool, values: Mapping[str, object] | None = None,
    errors: Mapping[str, object] | None = None, scan_now: bool = True,
) -> str:
    """首次运行表单。题目顺序、默认值与校验全部来自 `onboarding.questions()`。

    校验失败时带着 `values` 和 `errors` 重新渲染：已经填对的几项不能让人再填一遍，
    错在哪一项也要写在那一项底下，而不是页首一句「有字段不合法」。
    """
    values = values or {}
    errors = errors or {}
    asked = onboarding.questions(config, windows=windows)
    fields = []
    if errors.get("data_root"):
        fields.append(f'<p class="bad" role="alert">{escape(errors["data_root"])}</p>')
    media_dirs: list[str] = []
    # 只有媒体文件夹是非填不可的。数据目录、谁可以访问、端口、局域网地址都有能直接用的
    # 默认值，一律折进「高级设置」：不分独立包还是源码部署，同一张表单。
    advanced: list[str] = []
    for question in asked:
        if question.key == "media_dir":
            media_dirs = _media_dir_values(values, question.default)
            row_errors = errors.get("media_dir", [])
            note = "" if windows else onboarding.mounts_explanation(
                [path for path in media_dirs if path] or ["你在上面填的目录"])
            fields.append(_media_dirs_html(media_dirs, list(row_errors), "" if windows else
                "本机文件夹填写 macOS 挂载点；账本根目录填写对应的 Windows 盘符路径。",
                locations=values.get("media_location", ()), roots=values.get("media_root", ()), windows=windows))
            continue
        value = str(values.get(question.key, question.default))
        advanced.append(_field_html(question, value, str(errors.get(question.key, "")), ""))
    opened = " open" if any(errors.get(key) for key in ("data_root", "host", "port", "mdns_name")) else ""
    fields.append(f'<details{opened}><summary><span>高级设置</span>{_CHEVRON_SVG}</summary>'
                  + "".join(advanced) + "</details>")
    filled = [path for path in media_dirs if path]
    if not filled:
        scan_text = "完成设置后扫描媒体文件夹"
    elif len(filled) == 1:
        scan_text = f"完成设置后扫描 <code>{escape(filled[0])}</code>"
    else:
        scan_text = f"完成设置后扫描这 {len(filled)} 个文件夹"
    body = (
        '<header><img class="mark" src="/peach-logo.png" alt="" width="40" height="40">'
        "<h1>欢迎使用 Peach</h1>"
        '<p class="lede">选一个媒体文件夹，开始整理你的馆藏。</p></header>'
        '<form method="post" action="/setup">'
        + "".join(fields)
        + _check_html("scan_now", scan_text, checked=scan_now)
        + '<p class="help">扫描只读取文件名、大小和修改时间，不改动任何媒体文件。</p>'
        '<button type="submit">完成设置</button></form>'
    )
    return _document("Peach · 首次运行", body)


def setup_done_page(applied, *, windows: bool, scan_requested: bool) -> str:
    """成功页：接下来会自动发生什么，以及口令在哪。口令本身不显示在页面上。"""
    tree = applied.tree
    config = applied.config
    if distribution.standalone():
        destination = escape(_normal_url(config), quote=True)
        scan = "首次扫描已排队。" if scan_requested else "你可以稍后在配置界面开始扫描。"
        return _document("Peach · 设置完成",
                         '<h1>设置完成</h1><p class="lede">正在启动你的馆藏。' + scan + '</p>'
                         f'<p><a href="{destination}">进入 Peach</a></p>'
                         f'<meta http-equiv="refresh" content="8;url={destination}">'
                         + runtime_facts_html(config))
    ledger = (f"Peach 数据库已存在，没有动它：{tree.database}" if tree.ledger_existed
              else f"Peach 数据库：{tree.database}（已应用 {tree.migrations} 个迁移）")
    ca = (f"本机 CA：{tree.ca_cert}" if tree.ca_cert is not None
          else f"未生成本机 CA（{tree.ca_error}）；装好 openssl 后跑 "
               "<code>peach init --force</code> 补上。局域网设备要装这份 CA 才不报证书错。")
    scan = ("<li>首次扫描已排队，托盘会在服务起来之后在后台跑，期间页面照常能用。</li>"
            if scan_requested else
            "<li>没有请求首次扫描；要扫就跑 <code>peach scan configured</code>。</li>")
    from .media_configuration import rows
    mounts = ("" if windows else '<dl class="facts">' + ''.join(
        f'<dt>{escape(row["location"])} · {escape(row["root"])}</dt><dd>{escape(row["path"])}</dd>'
        for row in rows(config, windows=False)) + '</dl>')
    body = (
        "<h1>设置完成</h1>"
        "<p>托盘正在停掉这条引导服务，改用正常的 Peach 服务；这个页面几秒后就会连不上，"
        f"届时打开 <code>{escape(_normal_url(config))}</code> 即可。</p>"
        "<ul>"
        f"<li>{escape(ledger)}</li>"
        f"<li>{ca}</li>"
        f"<li>访问口令文件：<code>{escape(str(tree.token_path))}</code>；"
        "口令内容用 <code>peach token</code> 看，别的设备第一次访问时贴进登录页。</li>"
        f"{scan}"
        "</ul>"
        f"{mounts}"
        + runtime_facts_html(config)
    )
    return _document("Peach · 设置完成", body)


def _normal_url(config) -> str:
    """设置完成之后正常服务的地址。只有这台电脑就给回环，局域网给 `<名字>.local`。"""
    if config.server.host in _LOOPBACK:
        return f"http://127.0.0.1:{config.server.port}/"
    return f"https://{config.server.mdns_name}.local/"


def asset_response(request: Request, path: Path, media: str) -> Response:
    """页面资产用 ETag 复验代替 no-store，`/app.js`、`/js/`、`/dist/` 共用。

    `/app.css` 拼多份分区，ETag 口径见 `stylesheet_response()`，其余照这里。

    `no-store` 让 `app.js`（435KB）加 `app.css`（232KB）每次开页都全量重下；
    `no-cache` 的更新语义完全一样——每次都回源验证，文件一变立刻生效——但没变时
    只回一个 304，零字节传输。代价是一次条件请求的往返。

    ETag 取 mtime_ns 加字节数，不读文件内容：这几个文件都由 Git 检出或 `frontend/`
    构建产生，改一次就换一次 mtime，不需要为了强校验去算全文哈希。
    """
    stat = path.stat()
    etag = f'"peach-{stat.st_mtime_ns:x}-{stat.st_size:x}"'
    if request.headers.get("if-none-match") == etag:
        response: Response = Response(status_code=304)
    else:
        response = FileResponse(path, media_type=f"{media}; charset=utf-8")
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"
    return response


#: 拆分后的样式表分区。层叠顺序就是文件名顺序，所以每份都带两位数前缀；
#: 名字判据和 `/js/`、`/dist/` 同口径，不接受分隔符。清单由 `tests/test_web_ui.py` 钉住。
CSS_PART_NAME = re.compile(r"\d{2}-[a-z0-9-]+\.css")


def css_parts(web: Path) -> list[Path]:
    """`web/css/` 下的样式分区，已按层叠顺序排好。"""
    return sorted(path for path in (web / "css").glob("*.css")
                  if CSS_PART_NAME.fullmatch(path.name))


def stylesheet_response(request: Request, web: Path) -> Response:
    """`/app.css`：把 `web/css/` 的分区按顺序拼成一份交付。

    样式表拆成分区是为了让改动落在互不重叠的文件上——一整份两千多行的样式表，
    两个分支各改一处也几乎必然撞在一起。但拆开只是仓库里的事：页面仍然只取一份
    `/app.css`，不给首屏加二十来个阻塞请求，层叠顺序也不必写进 `index.html`。

    ETag 不能照 `asset_response()` 只看单个文件的 mtime 和字节数，改任何一份分区
    都要让它失效，所以取全部分区的 (mtime_ns, 字节数) 摘要。仍然不读文件内容。
    """
    parts = css_parts(web)
    if not parts:
        return PlainTextResponse("missing", status_code=404)
    stamp = "|".join(
        f"{path.name}:{stat.st_mtime_ns:x}:{stat.st_size:x}"
        for path, stat in ((path, path.stat()) for path in parts)
    )
    etag = f'"peach-css-{hashlib.sha256(stamp.encode()).hexdigest()[:16]}"'
    if request.headers.get("if-none-match") == etag:
        response: Response = Response(status_code=304)
    else:
        response = Response(b"".join(path.read_bytes() for path in parts),
                            media_type="text/css; charset=utf-8")
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"
    return response


@router.api_route("/", methods=["GET", "HEAD"])
def index(request: Request, args: dict[str, str] = Depends(require_page_auth)):
    settings = request.app.state.settings
    if settings.token and args.get("t"):
        response = RedirectResponse(request.url.path or "/", status_code=303)
        set_auth_cookie(response, request)
        return response
    if not settings.configured:
        # 未配置不是错误状态：服务照常起，首页变成首次运行表单。
        return HTMLResponse(setup_page(settings_file.active(), windows=os.name == "nt"))
    if not settings.page_path.is_file():
        return PlainTextResponse("Peach page missing", status_code=500)
    response = FileResponse(settings.page_path, media_type="text/html")
    response.headers["Cache-Control"] = "no-store"
    set_auth_cookie(response, request)
    return response


@router.post("/setup")
async def setup_submit(request: Request):
    """首次运行表单的提交端点。落盘逻辑全在 `peach.onboarding`，这里只做守卫和渲染。

    三道守卫，形态各不相同因为原因各不相同：已经配置过的机器上这个端点根本不存在
    （404，不是「禁止」——把它做成一条可探测的 403 等于对外宣告这里有个初始化入口）；
    非回环调用方是 403（引导服务只绑 127.0.0.1，能走到这里说明有人转发了它）；
    设置文件已经在了是 409（并发提交或刷新重发，不能覆盖别人刚写好的那份）。

    扫描不在这里跑：这条引导服务在设置完成的那一刻就会被托盘停掉，跑在它进程里的
    扫描会跟着一起死。这里只写一个标记，由托盘切到正常服务之后消费。
    """
    settings = request.app.state.settings
    if settings.configured:
        raise HTTPException(status_code=404, detail="not found")
    host = request.client.host if request.client else ""
    if host not in _LOOPBACK:
        raise HTTPException(status_code=403, detail="setup is loopback-only")
    if distribution.standalone() and request.url.hostname not in _LOOPBACK:
        raise HTTPException(status_code=403, detail="请使用本机地址打开设置")
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(status_code=403, detail="请从 Peach 设置页提交")

    windows = os.name == "nt"
    form = parse_qs((await request.body()).decode("utf-8", "replace"), keep_blank_values=True)
    submitted: dict[str, object] = {key: (value or [""])[0] for key, value in form.items()}
    # 媒体文件夹是一个列表：几行输入框同名提交，回显时也要原样给回几行。
    submitted["media_dir"] = list(form.get("media_dir", []))
    for key in ("media_location", "media_root"):
        if key in form:
            submitted[key] = list(form[key])
    scan_now = "scan_now" in form

    config = settings_file.active()
    answers, errors = _read_answers(config, submitted, windows=windows)
    if distribution.standalone() and answers is not None:
        try:
            onboarding.check_available_port(answers.port, request.url.port or 80)
        except ValueError as exc:
            errors["port"] = str(exc)
    if errors:
        return HTMLResponse(
            setup_page(config, windows=windows, values=submitted, errors=errors,
                       scan_now=scan_now),
            status_code=400,
        )
    # 数据根决定设置文件在哪，所以拿到它之后要按它重新解析一次，不能沿用进程启动
    # 那一刻按发现顺序算出来的这份。
    resolved, _broken = onboarding.resolve_config(answers.data_root)
    if resolved.path.exists():
        raise HTTPException(status_code=409, detail="settings file already exists")
    try:
        applied = onboarding.apply(resolved, answers, windows=windows)
    except (OSError, RuntimeError) as exc:
        return HTMLResponse(setup_page(config, windows=windows, values=submitted,
                                      errors={"data_root": str(exc)}, scan_now=scan_now), status_code=400)
    if scan_now:
        onboarding.request_first_scan(applied.config, "configured" if answers.media_sources is not None else "local")
    response = HTMLResponse(setup_done_page(applied, windows=windows, scan_requested=scan_now))
    if distribution.standalone():
        response.set_cookie("tok", auth.read_token(applied.config.directory("secrets")),
                            httponly=True, samesite="strict", max_age=31536000)
        response.headers["Cache-Control"] = "no-store"
    return response


def _read_answers(
    config, submitted: Mapping[str, object], *, windows: bool,
) -> tuple[object, dict[str, object]]:
    """逐字段校验，错误按字段收集。校验器和 CLI 问答用的是同一批。

    媒体文件夹那一项是多行：错误是与行对应的列表，其余字段的错误是一句话。
    """
    values: dict[str, object] = {}
    errors: dict[str, object] = {}
    for question in onboarding.questions(config, windows=windows):
        if question.key == "media_dir":
            if "media_location" in submitted:
                from . import media_configuration
                dirs = _media_dir_values(submitted, question.default)
                kinds = submitted["media_location"]
                roots = submitted.get("media_root", [])
                sources = [{"location": kinds[i] if i < len(kinds) else "local", "path": path,
                            "root": roots[i] if i < len(roots) else ""} for i, path in enumerate(dirs)]
                _, _, problems = media_configuration.validate(sources, windows=windows)
                if problems:
                    errors["media_dir"] = problems
                values.update(media_dirs=tuple(Path(path) for path in dirs), media_sources=sources)
                continue
            paths, problems = onboarding.read_media_dirs(
                _media_dir_values(submitted, ""), validate=question.validate,
                default=question.default)
            if problems:
                errors["media_dir"] = problems
            else:
                values["media_dirs"] = tuple(paths)
            continue
        raw = str(submitted.get(question.key, "") or "")
        try:
            values[question.key] = question.validate(raw if raw.strip() else question.default)
        except ValueError as exc:
            errors[question.key] = str(exc)
    if errors:
        return None, errors
    return onboarding.Answers(**values), {}  # type: ignore[arg-type]


@router.api_route("/app.css", methods=["GET", "HEAD"])
@router.api_route("/app.js", methods=["GET", "HEAD"])
def app_asset(request: Request, args: dict[str, str] = Depends(require_asset_auth)):
    """页面拆出来的样式与入口脚本。样式在 `web/css/`，脚本和 index.html 同目录，同一套口令。

    仍然没有构建步骤：`app.js` 现在是 ES module，浏览器原生解析 import，
    拆出来的模块见下面的 `/js/{name}`。页面里没有任何内联事件处理器，
    全部是 `.onclick=` 属性赋值，所以顶层声明不再是全局也不影响绑定。
    """
    name = request.url.path.lstrip("/")
    web = request.app.state.settings.page_path.parent
    if name == "app.css":
        return stylesheet_response(request, web)
    path = web / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    return asset_response(request, path, "text/javascript")


@router.api_route("/js/{name}", methods=["GET", "HEAD"])
def app_module(request: Request, name: str,
               args: dict[str, str] = Depends(require_asset_auth)):
    """`app.js` 拆出来的 ES module。和入口脚本同一套口令与 401 形态。

    文件名严格限制为一层平铺的 `[a-z0-9_-]+.js`：静态路由拼路径是典型的目录
    穿越入口，与其在这里做 resolve 后再比较根目录，不如根本不接受分隔符。
    前端模块规模不大，平铺够用。
    """
    if not re.fullmatch(r"[a-z0-9_-]+\.js", name):
        return PlainTextResponse("bad module name", status_code=404)
    path = request.app.state.settings.page_path.parent / "js" / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    return asset_response(request, path, "text/javascript")


@router.api_route("/dist/{name}", methods=["GET", "HEAD"])
def app_bundle(request: Request, name: str,
               args: dict[str, str] = Depends(require_asset_auth)):
    """`frontend/` 构建出来的 island 产物（ADR-0022）。口令与缓存口径同 `/js/`。

    产物提交进 Git 且文件名不带内容哈希，所以 `app.js` 能直接
    `await import('/dist/peach-ui.js')`；也正因为名字不带哈希，缓存只能靠复验，
    和 `/js/` 共用 `asset_response` 的 ETag 口径。
    名字判据和 `/js/` 逐字一致，只多认一个 `.css`：产物名不带内容哈希，也就不需要
    名字里再有点，`peach-ui.js.map` 这类附带文件跟着一起落在 404。
    """
    if not re.fullmatch(r"[a-z0-9_-]+\.(?:js|css)", name):
        return PlainTextResponse("bad bundle name", status_code=404)
    path = request.app.state.settings.page_path.parent / "dist" / name
    if not path.is_file():
        return PlainTextResponse("missing", status_code=404)
    media = "text/css" if name.endswith(".css") else "text/javascript"
    return asset_response(request, path, media)


@router.api_route("/favicon.svg", methods=["GET", "HEAD"])
def favicon():
    response = Response(FAVICON, media_type="image/svg+xml")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.api_route("/peach-logo.png", methods=["GET", "HEAD"])
def peach_logo():
    return FileResponse(PROJECT_ROOT / "resources" / "peach-logo.png", media_type="image/png")


@router.api_route("/item/{item_id}", methods=["GET", "HEAD"])
@router.api_route("/mix/{seed_id}/{mix_item_id}", methods=["GET", "HEAD"])
@router.api_route("/parts/{part_seed_id}/{part_item_id}", methods=["GET", "HEAD"])
@router.api_route("/editions/{edition_seed_id}/{edition_item_id}", methods=["GET", "HEAD"])
@router.api_route("/playlists", methods=["GET", "HEAD"])
@router.api_route("/playlists/{playlist_id}/{playlist_item_id}", methods=["GET", "HEAD"])
@router.api_route("/performers/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/studios/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/creators/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/series/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/agencies/{name:path}", methods=["GET", "HEAD"])
@router.api_route("/performers", methods=["GET", "HEAD"])
@router.api_route("/creators", methods=["GET", "HEAD"])
@router.api_route("/studios", methods=["GET", "HEAD"])
@router.api_route("/agencies", methods=["GET", "HEAD"])
@router.api_route("/tags", methods=["GET", "HEAD"])
@router.api_route("/unseen", methods=["GET", "HEAD"])
@router.api_route("/watch-later", methods=["GET", "HEAD"])
@router.api_route("/flagged", methods=["GET", "HEAD"])
@router.api_route("/junk-files", methods=["GET", "HEAD"])
@router.api_route("/stats", methods=["GET", "HEAD"])
@router.api_route("/immerse", methods=["GET", "HEAD"])
@router.api_route("/trash", methods=["GET", "HEAD"])
@router.api_route("/review", methods=["GET", "HEAD"])
@router.api_route("/taste", methods=["GET", "HEAD"])
@router.api_route("/data-cleanup", methods=["GET", "HEAD"])
@router.api_route("/duplicates", methods=["GET", "HEAD"])
@router.api_route("/quality-goals", methods=["GET", "HEAD"])
@router.api_route("/scraping", methods=["GET", "HEAD"])
@router.api_route("/resource-sync", methods=["GET", "HEAD"])
@router.api_route("/follow", methods=["GET", "HEAD"])
@router.api_route("/follow-manage", methods=["GET", "HEAD"])
@router.api_route("/follow/item/{item_id}", methods=["GET", "HEAD"])
# 配置页是主站里的一屏（island），数据走 `/api/configuration`。未配置时 `index()` 给的是
# 首次运行表单，正好就是「请先完成首次设置」该长的样子。
@router.api_route("/configuration", methods=["GET", "HEAD"])
def client_route(request: Request, item_id: int | None = None,
                 seed_id: int | None = None, mix_item_id: int | None = None,
                 part_seed_id: int | None = None, part_item_id: int | None = None,
                 edition_seed_id: int | None = None, edition_item_id: int | None = None,
                 playlist_id: int | None = None, playlist_item_id: int | None = None,
                 kind: str | None = None, name: str | None = None,
                 args: dict[str, str] = Depends(require_page_auth)):
    return index(request, args)
