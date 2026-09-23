"""入口页共用件：首启、登录与配置页都要的内联样式和运行信息。

这些页面不加载 `app.js`，样式得随 HTML 一起送到；运行信息则被首启完成页、登录页
和 `/api/configuration` 共用。三个路由模块都要，就不能住在其中任何一个里：那会让
路由层互相导入成环。放在 web 层，路由模块单向依赖它，`tests/test_module_layering.py`
守着这个方向。
"""
from __future__ import annotations

import re

from .config import PROJECT_ROOT


def board_entry_style() -> str:
    """入口页内联公共视觉层。首启和登录页不加载 app.js，样式得随 HTML 一起送到。"""
    css = (PROJECT_ROOT / "web/board-entry.css").read_text(encoding="utf-8")
    return f'<style id="boardEntryStyles">{css}</style>'


#: 入口页表单的样式，首启、登录与错误页共用这一份。刻意不引用 `web/` 里的任何资产：
#: 那一套一上来就会去打 `/api/items`，而未配置的机器还没有数据库，页面只会是一屏红色
#: 报错。这几页因此落在 SPA 外壳之外，不是 `frontend/` island（ADR-0022、docs/FRONTEND.md）。
_ENTRY_FORM_STYLE = """<style>
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
.req{color:var(--drop);margin-left:4px}
input[type=text],input[type=number],input[type=password]{width:100%;height:var(--control-h);padding:0 12px;
border:1px solid var(--line);border-radius:var(--control-radius);background:var(--ground);
color:var(--ink);font:inherit}
.affix{display:flex;align-items:center;height:var(--control-h);border:1px solid var(--line);
border-radius:var(--control-radius);background:var(--ground)}
.affix input:is([type=text],[type=number]){flex:1 1 auto;min-width:0;height:100%;border:0;border-radius:0;background:transparent}
.affix input:is([type=text],[type=number]):focus-visible{outline:0}
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
.optional{margin-inline-start:8px;color:var(--muted);font-size:var(--fs-sm);font-weight:400}
.field>label:not(:first-child){margin-top:24px}
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
.dir{display:flex;flex-wrap:wrap;gap:10px;padding:16px;border:1px solid var(--line-soft);border-radius:var(--control-radius);margin-top:16px}
.dir:first-child{margin-top:0}.dir .bad{flex-basis:100%;margin:0}
.entry-input{display:contents}
.dir input[type=text]{flex:1 1 auto;width:auto;min-width:0}
.dir > input[type=text]{flex:1 1 0;width:0}
.sourcefields{flex-basis:100%;display:grid;gap:8px;min-width:0}
.sourcefields select{width:100%;height:var(--control-h);border:1px solid var(--line-soft);border-radius:var(--control-radius);background:var(--surface);color:var(--ink);padding:0 12px;font:inherit}
.sourcefields select:focus-visible{outline:2px solid var(--tungsten);outline-offset:2px}
.sourcefields select{appearance:none;padding-right:42px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='m4 6 4 4 4-4' fill='none' stroke='%23888' stroke-width='1.5'/%3E%3C/svg%3E");background-repeat:no-repeat;background-size:16px;background-position:right 14px center}
.sourcefields label{display:grid;gap:6px;color:var(--muted);font-size:var(--fs-sm)}
.sourcefields input[type=text]{width:100%;box-sizing:border-box}
.help a{text-decoration:none}.help a:hover{text-decoration:underline;text-underline-offset:3px}
.help a svg{width:14px;height:14px;margin-inline-start:4px;vertical-align:-2px;stroke:currentColor;fill:none;stroke-width:2}
.sourcefields .gselect{display:flex;width:100%}.sourcefields .gselectfield{padding-inline:14px}
.sourcefields select[hidden]{display:none}
.rm,.pick,.add{height:var(--control-h);border:1px solid var(--line);border-radius:var(--control-radius);
background:var(--ground);color:var(--ink);cursor:pointer;font:500 var(--fs-sm) system-ui,sans-serif}
.rm,.pick{width:var(--control-h);flex:none;display:grid;place-items:center;color:var(--muted)}
.rm svg,.pick svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;
stroke-linejoin:round}
.pick[aria-busy=true]{color:var(--muted);cursor:progress}
.add{margin-top:8px;padding:0 14px}
.rm:hover,.pick:hover,.add:hover{background:var(--hover);color:var(--ink)}
.rm{color:var(--drop)}.rm:hover{background:var(--drop);border-color:var(--drop);color:white}
.rm[hidden],.pick[hidden],.add[hidden]{display:none}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media(max-width:760px){input[type=text],input[type=number]{font-size:16px}}
@media(max-width:560px){body{--control-h:44px}.sourcefields select{font-size:var(--fs-lg)}}
@media(max-width:440px){body{padding:24px 20px}h1{font-size:var(--fs-2xl)}}
</style>"""

#: Board CheckboxGlyph 的归一化勾线；来源见 docs/BOARD_UI.md。
CHECK_SVG = ('<svg viewBox="0 0 16 16" fill="none">'
             '<path d="M4 7.7002L6.64645 10.3466C6.84171 10.5419 7.15829 10.5419 7.35355 10.3466L12 5.7002" '
             'stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg>')


def check_html(name: str, text_html: str, *, checked: bool, value: str = "y") -> str:
    """入口页共用的自绘勾选框：文字与框同属一个 label，没有点不到的缝。"""
    return (f'<label class="check"><span class="pcheck"><input type="checkbox" name="{name}" value="{value}"'
            + (" checked" if checked else "")
            + f'><span aria-hidden="true">{CHECK_SVG}</span></span><span>{text_html}</span></label>')


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


def _button_rules() -> str:
    """独立页面直接使用主站的 Geist Button 规则。"""
    base = (PROJECT_ROOT / "web/css/01-base.css").read_text(encoding="utf-8")
    return '\n'.join(re.findall(r'^\.(?:geist-button|gselect|popmenu)[^{}]*\{[^}]*\}', base, re.M))


def _board_button_rules() -> str:
    """入口页的主按钮就是站内那一颗：规则和 token 都从 `board.css` 原样取。

    错误页、登录页和首启页都是没登录时看到的 Peach，按钮换一种颜色就等于说这是另一个
    产品。表单提交键由 `board-entry.css` 接同一组 token，渐变色值仍只在 `board.css` 一处。

    只取主按钮那几条（静止、悬停铺的那层底、按下、尺寸）和它们用到的 token：`board.css`
    的 `:root` 里还有一份把 `--page` `--ground` 按 Board 的角色重排的映射，整块搬过来
    会把入口页自己的面色对调。
    """
    board = (PROJECT_ROOT / "web/board.css").read_text(encoding="utf-8")
    accent = re.search(
        r'^:root,:root\[data-accent=blue\],\[data-accent-ball=blue\]'
        r'\{--color-accent-50:[^}]*\}', board, re.M).group(0)
    palettes = re.findall(
        r'^(?:@media\(prefers-color-scheme:dark\)\{)?:root[^{]*\{--color-text-primary:[^}]*\}\}?',
        board, re.M)
    switches = re.findall(r'^:root[^{]*\{--control-hover:[^}]*\}', board, re.M)
    fonts = [f'{name}:{value}' for name in ("--board-font", "--board-body-medium")
             for value in re.findall(rf'{name}:([^;]+);', board)[:1]]
    rules = re.findall(
        r'^body :is\([^)]*\)\.primary(?::not\(:disabled\))?'
        r'(?::hover|:active)?(?:::before)?\{[^}]*\}', board, re.M)
    return accent + ''.join(palettes) + ''.join(switches) + ':root{' + ';'.join(fonts) + '}' + ''.join(rules)


def entry_page_style() -> str:
    """入口页的整层视觉：色板、滚动条、表单控件、Geist 按钮与 Board 表面。

    首启、设置完成、错误页和登录页是同一副面孔的四个状态。谁少接一段，那一页就换了
    产品：登录页曾只接 `board_entry_style()`，`--board-blue` 无处声明，主按钮的底色
    解析不出来，屏幕上只剩一行蓝字。顺序有意义——后面几段按同一套 token 覆盖前面的
    默认值，`board-entry.css` 必须排在表单样式之后。
    """
    return (f"<style>{_theme_tokens()}{_scrollbar_rules()}</style>{_ENTRY_FORM_STYLE}"
            f"<style>{_button_rules()}</style>{board_entry_style()}"
            f"<style>{_board_button_rules()}</style>")


def runtime_facts(config) -> tuple[tuple[str, str], ...]:
    """这台机器上 Peach 的位置与版本：设置完成页和 `/api/configuration` 共用同一份。"""
    from . import __version__
    import platform as system_platform
    from .ffmpeg import FFmpegResolver
    from .mp4recover import untrunc_path

    available = FFmpegResolver(config.directory("tools") / "ffmpeg").ffmpeg() is not None
    ffmpeg = "可用" if available else "未安装；MP4 可直接播放，转码和缩略图需要安装 FFmpeg。"
    untrunc = "可用" if untrunc_path(config.directory("tools")) else "未安装；缺索引的 MP4 需要它才修得了。"
    return (
        ("版本", __version__),
        ("操作系统", system_platform.system()),
        ("数据目录", str(config.data_root)),
        ("设置文件", str(config.path)),
        ("日志目录", str(config.directory("logs"))),
        ("FFmpeg", ffmpeg),
        ("untrunc", untrunc),
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
    untrunc = next(row for row in entries if row["term"] == "untrunc")
    if untrunc["value"] != "可用":
        untrunc.update(value=untrunc["value"] + f"解压到 {config.directory('tools') / 'untrunc'}。",
                       download_url="https://github.com/anthwlock/untrunc/releases",
                       download_label="下载 untrunc")
    return entries
