# Geist 语义控件实测记录（按钮/徽章/标题/布局）

- 取证日期：2026-08-29
- URL：<https://vercel.com/geist/button>、<https://vercel.com/geist/banner>、<https://vercel.com/geist/badge>
- 取证方式：浏览器加载页面后读 `getComputedStyle`（与 `vercel-geist-controls-measured.md` 同法）
- **不在 `docs/reference-sources.json` 里登记**：理由同上，渲染结果没有可哈希上游快照。

## Button（dark 主题实测）

| 变体 | 背景 | 文字 | 几何 |
| --- | --- | --- | --- |
| primary | `rgb(237,237,237)` | `rgb(10,10,10)` | 500 字重 |
| danger | `rgb(217,48,54)` | `#fff` | 同上 |
| warning | `rgb(255,153,10)` | `rgb(10,10,10)` | 同上 |
| secondary | `rgb(10,10,10)` 或透明 | `rgb(237,237,237)` | 同上 |

- 小号（default）：32 px 高、`border-radius:6px`、`padding:0 6px`、14 px 字。
- 大号（large）：40 px 高、`border-radius:8px`、`padding:0 14px`、16 px 字。

语义对应：销毁类操作用 danger 实底，暂停/降级类用 warning，主推进动作用 primary
（dark 主题下是白），其余一律 secondary。Dashboard 的危险设置卡（Delete Project）
是红发丝边框 + 底部一条红 tint 区放危险按钮。

## Badge

- 彩色变体：24 px 高、12 px 字、正圆胶囊（radius 999px）、`padding:2px 12px`、实底。
  blue `rgb(0,98,209)`、red `rgb(217,48,54)`、amber `rgb(255,178,36)`（黑字）、
  green `rgb(26,147,56)`、teal `rgb(12,151,132)`、purple `rgb(95,46,133)`、pink `rgb(179,26,87)`。
- 灰色默认（代码示例里量到的）：bg `rgb(26,26,26)`、边 `rgb(41,41,41)`、字
  `rgb(161,161,161)`、radius 6px、mono 字体。Dashboard 的状态徽章走低饱和
  tint（如 subtle 绿/红），不是每行都上实底彩色。

## 标题

- H1：40 px / 600 / `letter-spacing:-2.4px` / `line-height:48px` / `margin:0 0 12px`。
- H2：24 px / 600 / `letter-spacing:-0.96px` / `line-height:32px`。

## 布局与字体

- 文档正文列：body `max-width:1265px`，main 实测 1220px；Dashboard 的设置类
  页面内容列实测约 943px（用户提供的 Team Settings 截图）——低密度页面不全宽。
- 正文字体栈：`Geist, Inter, -apple-system, …, sans-serif`，全程无衬线；站方
  栈里没有 CJK 名字，中文站必须自行补 CJK sans，否则 Chrome 的中文默认字体
  （宋体）会接管标题。

## Dashboard 后台实测（2026-08-29，登录态）

- 设置页内容列：卡片实测 **914px**（1265px 视口），居中；低密度管理页不全宽。
- 设置卡：bg `rgb(10,10,10)`，radius **6px**，发丝边（文档示例卡为
  `1px rgba(255,255,255,0.14)`、radius 8px）；卡内标题 **20px/600/26px 行高**，
  描述为 muted 灰；卡底与主体之间发丝分隔，底部一行「左侧 helper 灰字 +
  右侧动作按钮」。
- 危险设置卡（Delete Project，用户截图）：整卡红发丝边框，底部一条红 tint
  区，右侧 danger 实底按钮；Pause Project 用 warning（amber）实底按钮。
- 文档页排版：H1 40px/48 行高/600/`-2.4px`/`mb 12px`；导语 20px/30 行高 muted；
  正文段落 16px/24 行高，`mt 16px`。


## Toggle 与卡片面（2026-08-29 补测）

- **Geist 的「Switch」是分段选择器**（radio 语义，2–3 个互斥视图切换），
  布尔开/关的正确控件叫 **Toggle**。
- Toggle 实测：小号 28×14、中号 36×20、大号 40×24，全胶囊；圆点 = 高-3 px
  （11/17/21），左右各留 2 px。关 = 轨道 `rgb(46,46,46)`、圆点
  `rgba(237,237,237,.84)` 靠左；开 = 轨道 `rgb(0,112,243)`、圆点靠右。
  禁用：轨道 `rgb(31,31,31)`、圆点 `rgb(69,69,69)`。
- **卡片面用贴背景的实底升起面**，不是白色透明叠加：Vercel 后台黑主题
  实测卡片 `rgb(10,10,10)` 置于 `#000` 上，配低透明发丝边。Peach 对应
  `--surface` 置于 `--ground` 上（统计卡即此方案），设置面板此前用的
  `--overlay-5`（白色 5% 叠加）与全站卡片色系不一致，已统一到 `--surface`。

## Tooltip、Collapse 与 Projects 工具栏（2026-08-30 补测）

- Tooltip：<https://vercel.com/geist/tooltip> 当前加载的组件 chunk 为
  `/vc-ap-b3331f/_next/static/immutable/chunks/118l4-ay8nz2o.js`，SHA-256
  `FA7C49EDEB237132B09619409AAF97B09EF265BA8FED71CEBD09D21216F7C8DE`。
  默认最大宽度 250px，8px 圆角，水平／垂直内边距 8／6px，13px 字、1.3 行高；
  内容经 Portal 渲染，打开时才给触发器 `aria-describedby`，触发器默认可聚焦，支持
  hover、focus、触摸和 Escape。上下方向的自动对齐在离左右视口不足 100px 时改为
  left／right boxAlign。
- Collapse：<https://vercel.com/geist/collapse> 当前组件位于
  `/vc-ap-b3331f/_next/static/immutable/chunks/1k513hf7se3-l.js`，SHA-256
  `0BD8AA9351E4CAA33F01CCEC48C68EDAD491BD1D25234964A4482B7E7E273982`。
  触发器使用 `aria-controls`／`aria-expanded`；内容区关闭时 `inert`，以测量高度写入
  inline `height`，`overflow-y:hidden`，高度和 chevron 都使用 200ms `ease-in-out`。
- 登录态 Projects 页 `https://vercel.com/<account>`：2026-08-30 的可见 DOM
  顺序为 Search、`Filter and Sort Projects`、Add New；实测同一行 36px 高、8px gap，
  搜索占剩余宽度，筛选按钮 36×36px，Add New 115×36px。筛选菜单 250px 宽、6px
  内边距、12px 圆角，内部纵向滚动且 `overscroll-behavior:contain`；展开没有动画。
  用户截图 `codex-clipboard-b47d665c-a203-4c22-8e79-1123b896e555.png` 的 SHA-256 为
  `037CBD12E6254072817F402864A0B11C641AA920CA4BD9EDEC08D591DAF2EA1E`（1673×189）。

Peach 保留的差异：添加关注沿用现有 38px 输入基线，因此筛选钮是 38×38px；Tooltip
使用 Peach 的暗色 surface 且不复制箭头或淡入动画。复用的是可聚焦语义、严格视口夹取、
菜单无展开动画，以及 Collapse 的高度／chevron 过渡，不把三种组件的 motion 混用。

## Context Card／Toast／Material（2026-08-30 补查）

- <https://vercel.com/geist/context-card>：短元数据卡最多保留一个主动作；键盘可进入卡片，
  Escape 关闭并把焦点交还触发器。触发器的无障碍名称独立存在，卡片只补充上下文。
- <https://vercel.com/geist/toast>：用户主动动作的非阻塞成功回执用自动消失 Toast；失败若
  需要处理，原因与恢复动作仍留在原位置。Toast 区域使用 `aria-live="polite"`。
- <https://vercel.com/geist/material>：浮层的阴影、边框只负责视觉层级，语义必须落在外层
  `role` 和标题关联上；暗色主题不能只靠阴影分层。

Peach 图片灯箱的信息卡据此保持一个“在资源管理器中显示”动作，改为具名非模态 dialog；
触发器通过 `aria-controls`／`aria-expanded` 关联，打开后把焦点移到动作，Escape 只关闭信息卡
并交还焦点。成功回执进入现有 Toast，失败原因保留在卡内。视觉上沿用 Peach 的 12px
浮层圆角、发丝边与双层阴影，不复制 Vercel 品牌样式。

## 选中态与开关色（2026-09-03 实测，深色主题）

用 Claude_Browser 打开 `vercel.com/geist/*` 的示例块，读 `getComputedStyle` 得到的值。
取证目的只有一个：Geist 的「被选中」到底用不用蓝。

| 控件 | 页面 | 选中／开态 | 未选中 |
| --- | --- | --- | --- |
| Toggle | `/geist/toggle` | 轨道 `rgb(0,112,243)`（蓝），28×14 与 36×20 两档，`background .15s cubic-bezier(0,0,.2,1)` | 轨道 `rgb(46,46,46)` |
| Tabs | `/geist/tabs` | 文字 `rgb(237,237,237)` + `border-bottom:2px solid rgb(237,237,237)`，字重 400 | 文字 `rgb(161,161,161)` |
| Checkbox | `/geist/checkbox` | 框底仍是 `rgb(10,10,10)`，勾 `rgb(237,237,237)`；16px，圆角 4px | 框底 `rgb(10,10,10)`，边 `rgb(143,143,143)`；禁用且选中时底 `rgb(135,135,135)` |
| Switch（分段） | `/geist/switch` | 选中项底 `rgb(26,26,26)`、字 `rgb(237,237,237)`，高 28px | 透明底；容器底 `rgb(10,10,10)`、圆角 6px、内边距 4px、`box-shadow:0 0 0 1px rgba(255,255,255,.14)`、高 36px |
| Button primary | `/geist/button` | 底 `rgb(237,237,237)`、字 `rgb(10,10,10)`、字重 500 | — |
| Badge gray | `/geist/badge` | 底 `rgb(26,26,26)`、边 `rgb(41,41,41)`、字 `rgb(161,161,161)`、圆角 6px | — |
| Collapse | `/geist/collapse` | 触发器是带 `aria-expanded`／`aria-controls` 的 `<button>`；内容关闭时仍在 DOM；文档明写「Animate the open/close transition; jump-cuts make the page feel like it teleported」 | — |

结论：整套 Geist 里只有 Toggle 开态用蓝，Tabs／Switch／Checkbox／主按钮的选中与强调全是墨色
反相或抬一档的灰面。蓝色的另外两个去处是焦点环与链接。

## Button 全变体与状态（2026-09-03 复测，深色主题）

- URL：<https://vercel.com/geist/button>
- 取证方式：`getComputedStyle` 遍历页面全部 `<button>` 去重；hover 与 disabled 的规则原文
  直接 `fetch` 站点样式表 `0p9r363b8n-x2.css` 后按 `}`…`}` 切片取出——手工写
  `data-hover` 属性并不触发 Geist 的悬停样式，只能读源规则。

| 尺寸 | 高 | 内边距 | 圆角 | 字号 |
| --- | --- | --- | --- | --- |
| small | 32px | `0 6px` | 6px | 14px |
| medium | 36px | `0 10px` | 6px | 14px |
| large | 40px | `0 14px` | 8px | 16px |
| rounded（胶囊） | 同上 | `0 12px` | 999px | 同上 |

变体（32px 档实测）：primary 底 `rgb(237,237,237)` 字 `rgb(10,10,10)`；secondary 底
`rgb(10,10,10)` 字 `rgb(237,237,237)`；tertiary／ghost 透明底 `rgb(237,237,237)` 字；
error 底 `rgb(217,48,54)` 字 `#fff`；warning 底 `rgb(255,153,10)` 字 `rgb(10,10,10)`。
全部 500 字重、`border-width:0`——边框是 `box-shadow:0 0 0 1px rgb(46,46,46)` 画的，
只有 secondary 有，tertiary 的 `box-shadow` 是 `none`。过渡统一
`.15s cubic-bezier(.4,0,.2,1)`。

三条关键状态规则：

- **悬停只动填充，边框不动**。源规则里没有任何按钮 hover 改 border/ring：
  primary 走 `--themed-hover-bg` 默认 `#ccc`（`hsl(0,0%,80%)`，即 #EDEDED 掉一档），
  secondary 走 `--ds-gray-200`（深色下 `#1F1F1F`，即 #0A0A0A 抬一档），
  ghost 走 `--ds-gray-alpha-200`。
- **禁用是实底灰，不是半透明**：底 `rgb(26,26,26)`、字 `rgb(143,143,143)`、
  ring `rgb(46,46,46)`、`opacity:1`、`cursor:not-allowed`。
- **按下没有缩放**：页面上全部按钮的 `transform` 都是 `none`，Geist 不做 `scale`。

### 选中态与它的悬停：源类名取证（2026-09-03）

`getComputedStyle` 读不到悬停态（要么得手工触发，要么被冻住的 transition 骗），但 Geist
是 Tailwind 写的，`class` 属性里的 `hover:`／`aria-selected:`／`peer-checked:` 前缀就是
规则原文，比计算值更硬。三个组件的类名清单一致：

| 组件 | 未选中悬停 | 选中 |
| --- | --- | --- |
| Switch 分段项 `/geist/switch` | `hover:text-[var(--ds-gray-1000)]` | `peer-checked:text-[--ds-gray-1000]` + `peer-checked:bg-[--switch-checked-color]` + `peer-checked:rounded-[4px]` |
| Tabs primary `/geist/tabs` | `not-disabled:hover:text-gray-1000` | `aria-selected:text-gray-1000` + `primary:aria-selected:border-gray-1000`（底边 2px） |
| Tabs secondary `/geist/tabs` | `not-disabled:hover:text-gray-1000` | `aria-selected:text-gray-1000` + `aria-selected:bg-gray-200`，`rounded-md`、`h-8`、`px-3` |

三条共同点，都与我们之前的写法相反：

- **悬停只改文字色，不上填充**。填充是「选中」的专属信号，所以一行选项里鼠标划过邻居时，
  哪个是当前项始终看得见。这与 Button 的「悬停只抬填充」不冲突：Button 没有选中态，
  没有需要让位的信号。
- **选中不加边、不加内嵌一圈线**。Tabs primary 的底边 2px 是这个组件自己的形状语言
  （未选中也占着 `border-b-2 border-transparent`），不是通用的选中环。
- **字重两态相同**。Switch 分段项 `font-medium` 常驻，Tabs 全程不改字重。

唯一的例外是主题选择器（system／light／dark 三个圆形按钮）：选中项是
`bg-[--ds-background-100]` + `shadow-[0_0_0_1px_var(--ds-gray-400)]`。它加环是因为选中项
的底色和容器同色，填充本身分不出来；不是通用做法。

### 主题选择器：整件几何（2026-09-04 实测，深色主题）

- URL：<https://vercel.com/geist/switch>，1440×900 视口（它挂在 `hidden xl:block` 的
  文档栏里，窄视口下三档的盒子都是 0，必须先把视口撑到 xl 再读）。
- 取证方式：按 `aria-label` 取 `system`／`light`／`dark` 三个 `type=radio`，读它们的
  `label` 与外层 `fieldset` 的 `getBoundingClientRect` 和 `getComputedStyle`；悬停与
  选中的规则原文取自 Tailwind 类名（`peer-checked:`／`hover:` 前缀就是规则本身）。

| 部位 | 值 |
| --- | --- |
| 外框 `fieldset` | 96×32，`rounded-full`，无填充，`--ds-shadow-border`（`0 0 0 1px`）一圈环，`p-0`、`border-0` |
| 每一档 `label` | 32×32 正圆（`size-8 rounded-full`），图标 16×16 |
| 未选中 | 透明底，图标 `--ds-gray-700`（`rgb(143,143,143)`）；`hover:text-[var(--ds-gray-1000)]`，不上填充 |
| 选中 | 底 `--ds-background-100`（`rgb(10,10,10)`，与页面同色），`shadow-[0_0_0_1px_var(--ds-gray-400),0_1px_2px_0_var(--ds-gray-alpha-100)]`，图标 `--ds-gray-1000` |
| 语义 | `fieldset` + `legend.sr-only`「Select a display theme:」+ 三个共享 name 的 radio，每档一个 `span.sr-only` 写档位名 |
| 焦点 | `peer-focus-visible:shadow-[var(--ds-focus-ring)]`，环由 radio 的焦点态传给同级 label |

三枚图标都是 16×16 的 Geist 私有 SVG：system 是一台显示器，light 是太阳，dark 是月亮带星。

2026-09-04 在登录态的 <https://vercel.com/sandun-bingshi> 复读同一个控件（账户菜单里的
「Theme」行），类名与上表逐条一致，只多一个把 32 收成 24 的 `data-small` 档。这套几何在
文档站与后台是同一份。

**Peach 采用与差异**：形状、尺寸、语义和「选中项加环」照抄，颜色换成本仓库 token
（外框环 `--border-15`，选中底 `--ground`、环 `--line` 加 `0 1px 2px var(--overlay-5)`，
未选中 `--muted`、悬停提到 `--ink`）。跟随系统那一档同样用显示器字形（Lucide `monitor`）：
这一档说的是「照这台设备的设定走」，讲的是设备而不是明暗。详情页的画面尺寸因此换成
`ratio`——那里量的是画幅本身，不是放画幅的机器。一处有意不同：`≤760px` 时三档各撑到
44×44，这是本仓库的手机命中区要求，Geist 没有这一档。

### 下拉：后台没有一个原生控件（2026-09-04 实测，登录态）

- URL：<https://vercel.com/sandun-bingshi>（Projects 后台首页）。
- 取证方式：先枚举页面里的 `select` 与 `[role="combobox"]`——两者都是 0 个；触发器一律是
  `button[aria-haspopup="true"]`（Filter and Sort Projects、Add New、Preview Menu…）。
  然后点开 Filter and Sort，读面板与行的 `getComputedStyle`，规则原文取自类名与 CSSOM。

| 部位 | 值 |
| --- | --- |
| 触发器 | 36×36，6px 圆角，`0 0 0 1px rgb(46,46,46)` 一圈环，无实心底 |
| 面板 | `ul[role="menu"]`，宽 250px（inline style），`--ds-background-100` 底（**浅色下是纯白**），12px 圆角，`padding:6px` |
| 面板阴影 | `--ds-shadow-menu`：`0 0 0 1px 边框色, 0 1px 1px #00000005, 0 4px 8px -4px #0000000a, 0 16px 24px -8px #0000000f` |
| 行 | `--ds-popover-row-height:36px`、`--ds-popover-row-radius:6px`、`--ds-popover-row-padding:0 8px`，14px/400 |
| 行的悬停与选中 | 同一个 token：`data-highlighted:bg-gray-alpha-100`、`data-selected:bg-gray-alpha-100`（浅色 `#0000000d`，深色 `#ffffff0f`），`transition:background .1s` |
| 行内次要文字 | `--ds-gray-900` |

### 浅色一档的中性刻度（2026-09-04 实测）

在同一页把 `<html>` 的 `dark-theme` 换成 `light-theme` 读 `:root` 的计算值（只改 DOM，不动
账号设置），拿到两档并排的刻度：

| token | 浅色 | 深色 |
| --- | --- | --- |
| `--ds-background-100` / `-200` | `#FFFFFF` / `#FAFAFA` | `hsl(0 0% 4%)` / `#000` |
| `--ds-gray-100` / `-200` / `-300` / `-400` | `#F2F2F2` / `#EBEBEB` / `#E5E5E5` / `#EBEBEB` | 10% / 12% / 16% / 18% |
| `--ds-gray-700` / `-900` / `-1000` | `#8F8F8F` / `#4D4D4D` / `#171717` | 56% / 63% / 93% |
| `--ds-gray-alpha-100` / `-200` / `-300` | `#0000000d` / `#00000014` / `#0000001a` | `#ffffff0f` / `#ffffff17` / `#ffffff21` |

要点：浅色这一档**没有色相**，从纸白到近黑全部落在 `hsl(0,0%,·)` 上；中间态（悬停、选中）
是纯黑透明度而不是调过色的实色灰，所以它永远比所在面板重一点点，不会自己变成一块底。

**Peach 采用与差异**：浅色色板照这张表改成无色相，`--hover` 从实色 `#EEF1F5` 换成
`rgba(0,0,0,.05)`；`--surface`/`--sunk`/`--line`/`--line-soft` 取 `#FAFAFA`/`#F2F2F2`/
`#E5E5E5`/`#EBEBEB`，`--ink`/`--ink-2` 取 `#171717`/`#4D4D4D`。两处不同：`--muted` 用
`#666666` 而不是 Geist 的 `#8F8F8F`（本仓库这一档要承担 12–13px 的说明文字，56% 灰在白底
上读不动），`--border-10`/`--border-15` 保留本仓库自己的 10%／15% 两档而不是收到 Geist 的
8%。下拉面板与菜单行按上表：`.popmenu` 底色改成 `--ground`、阴影换成那四层薄影，行高走
本仓库既有的 `--control-h`（38px）而不是 36px，悬停与选中共用 `--hover`。

### 侧栏导航是例外：分工反过来（2026-09-04 实测，深色主题）

上一节那张表只取了横排选项组（Switch、Tabs），当时把结论推广到了侧栏，这是错的。
2026-09-04 在 `https://vercel.com/geist/tabs` 用 1600×900 视口读左栏文档导航
（`aside` 里那 82 条链接，值取自每条链接内层的 `span`，悬停用真实鼠标移入后再读计算值）：

| 状态 | 背景 | 文字 | 类名 |
| --- | --- | --- | --- |
| 未选中 | `rgba(0,0,0,0)` | `rgb(161,161,161)` | `text-gray-900 hover:bg-gray-100` |
| 未选中 + 悬停 | `rgb(26,26,26)` | `rgb(161,161,161)`（不动） | 同上 |
| 当前项 | `rgba(255,255,255,.06)` | `rgb(237,237,237)` | `text-gray-1000 bg-gray-alpha-100`，**不带任何 hover 类** |

几何两态相同：`h-10`、`rounded-md`（6px）、`px-3 py-1.5`、`text-copy-14`，字重全程 400，无边框无环。

要点：

- **侧栏的悬停是抬填充的**，而且填充强度和当前项几乎一样：`--ds-gray-100` 是 hsl 10% 的实底，
  `--ds-gray-alpha-100`（`#ffffff0f`）压在 hsl 4% 的页底上合成约 hsl 9.4%。Geist 显然不打算
  用填充的强弱区分「鼠标在这儿」和「你在这儿」。
- **区分二者的是文字色**：63% 灰对 93% 白。悬停不碰文字色，当前项不带 hover 类。
  所以横排选项组那条「填充专属选中、悬停只提文字色」在这里是反的。
- 当前项确实不加边、不加环、不加字重——上一节这部分结论仍然成立。

Peach 的两列侧栏导航按上表对齐：`.edge button` 与 `.dnav button` 的未选中字色都是
`--muted`（63% 灰），当前项是 `--hover` 底 `--ink` 字。抽屉里的图标不再自己声明颜色，
跟着按钮的 `currentColor` 走，所以图标与标签始终同色、同时变。

### 纠正记录

`1367a9a`（2026-09-03）把 Switch／Tabs 的取证结论推广成了全站规则，顺手删掉了
`.edge button:hover` 与 `.dnav button:hover` 的填充。用户 2026-09-04 指出窄栏悬停没反馈，
并给出 Vercel 后台左栏的截图（Projects 与 Deployments 两行同时带填充）。上表是照此复测的结果：
证据只覆盖横排选项组，推广到侧栏没有依据。已按上表把两处填充改回，并加正向断言
`test_sidebar_nav_keeps_the_hover_fill_and_leaves_state_to_the_color` 锁住。

### Peach 对应（2026-09-03 收敛，2026-09-04 修正侧栏一条）

- 按下／选中（`aria-pressed="true"`、`aria-current`、`.selected`、`.current`、`.picked`、`:checked`）
  只有填充：一律 `--hover` 底 `--ink` 字，不加边、不加内嵌一圈线、不加字重。这条推翻了本文件
  此前写的两版——先是「统一 `--ink-2` 底 `--ground` 字」（Geist 的 Switch 选中项只是 `#0A0A0A`
  面上抬到 `#1A1A1A`，没有一处是反相白块），再是「无边框补内嵌一圈线、带边框提到墨色 28%、
  还要更强就加字重」（那一整套是自造的强调阶梯，上面三个组件的类名里一条都没有）。
- 因此**同一排横向互斥选项的未选中项，悬停只提文字色到 `--ink`，不上填充**。这些组的
  未选中基态一律 `--muted`（对应 Geist 横排选项实测的 `rgb(161,161,161)`）：停在 `--ink-2`
  时悬停只剩一档可提，肉眼读不出鼠标停在哪一枚。适用于 `.pill`、`.chip`、
  `.reviewtabs button`、`.sorts button`、`.junkfilters a`、`.tagmodes button`、
  `.managebar button`、`.mediaviewbutton`、`.javbar button`。没有选中态的按钮
  （`.fbtn`、`.fchip`）和没有并排邻居的孤立开关（`.ib`、`.brandpill`、`.playerstatsbtn`、
  `.fb .like`）悬停照旧抬填充。**侧栏导航 `.edge button` 与 `.dnav button` 不在这条里**，
  按上一节的实测走「悬停抬填充、当前项握着颜色」。彩色标签类控件（`.tagfilters`、`.index-tags .tg`、`.alphatag`、
  `.sec.cat-* .chip`）的悬停本来就是标签色 tint，与白色选中底不同色，不受这条影响。
- 主动作 `--ink` 底 `--ground` 字，悬停 `color-mix(in srgb,var(--ink) 88%,var(--ground))`
  （对应 Geist 的 #EDEDED→#CCC，同为掉一档而非换色）；每屏最多一个。
- 按钮（无选中态）悬停只抬填充到 `--hover`，边框与文字色不动——同样推翻此前的
  「悬停边提亮到墨色 28%」，那一档在 Peach 是全站最亮的边，实际效果比 Vercel 重得多。
  墨色 28% 的边现在只剩输入框 `.fpicksearch:hover` 一处。
- 禁用统一 `--sunk` 底、`--line-soft` 边、`--muted` 字，不用 `opacity`；
  按下不加 `scale`。Peach 保留 `cursor:default` 而不是 Geist 的 `not-allowed`，
  与本仓库其余禁用态写法一致。
- 计数徽章（如作者别名「3 组」）走 gray badge：`--overlay-5` 底、`--border-15` 细边、`--muted` 字、`--control-radius`。
- 保留蓝：`:focus*`、真正的链接（`.entitylink`／`.flink`／`.fsourcelink`／`.fcred a`／`.tokauthor>a`）、
  进度与数据（progress／watchprogress／range／slider／tokbar／trace）、`#censorSetting:checked`（Toggle）。
- `--tungsten-soft` 退役。允许清单由 `tests/test_web_ui.py` 的
  `test_tungsten_is_reserved_for_focus_links_progress_and_toggle` 强制。

## Peach 对应

- 语义按钮：`.fbtn.danger`（清空回收站等销毁类）、`.fbtn.primary` 保持主推进、
  批量已看/忽略保持 secondary；回收站清空区用红发丝边框卡。
- 行内状态：`ok`/`error` 用低饱和 tint 徽章（`.sbadge`），不再是裸文字。
- 检查失败报告条：对齐 danger 卡语义——红发丝边 + 微红底，去掉左侧粗条。
- 低密度管理页（统计/口味/复核等）内容列限宽约 1000px 居中；浏览页（首页/
  关注）保持全宽。
- 正文字体栈补 CJK sans：`"Microsoft YaHei UI","Microsoft YaHei","PingFang SC",
  "Hiragino Sans GB","Noto Sans CJK SC"` 置于 sans-serif 前。

## 2026-09-05 实测 vercel.com 后台（浅色档，另加暗色 token 对照）

- 取证方式：内置浏览器登录态下打开 `vercel.com/<team>/~/settings` 与 `vercel.com/<team>`，
  读 `getComputedStyle`；暗色一档把 `<html>` 的 `light-theme` 换成 `dark-theme` 后重读 token。
- 这一轮回答的是四个问题：输入框聚焦是什么色、fieldset 两块面各是什么色、
  按钮是不是「无脑全黑」、滚动条有没有被改写。

### 中性刻度（同一组 token 的明暗两档）

| token | 浅色 | 暗色 |
| --- | --- | --- |
| `--ds-background-100`（正文面） | `#FFFFFF` | `hsl(0,0%,4%)` |
| `--ds-background-200`（操作条） | `#FAFAFA` | `#000000` |
| `--ds-gray-200`（分隔线） | `#EBEBEB` | `hsl(0,0%,12%)` |
| `--ds-gray-alpha-400`（静止边） | `#00000014` | `#ffffff24` |
| `--ds-gray-alpha-500`（悬停边） | `#00000036` | `#ffffff3d` |
| `--ds-gray-alpha-600`（聚焦边） | `#00000057` | `#ffffff82` |
| `--geist-radius` | 6px | 6px |

两档的方向是一致的：操作条永远比正文面深一档，边永远是当前主题的中性透明色，
没有一处焦点或选中用到蓝。

### Fieldset

- 外框：`background:#FFFFFF`、`border-radius:6px`、`overflow:hidden`，边不是 border 而是
  `box-shadow:rgba(0,0,0,.08) 0 0 0 1px, #FAFAFA 0 0 0 1px`。
- 正文区：`#FFFFFF`、`padding:20px`；标题 20px/600，说明 14px、`padding:8px 0 20px`。
- 操作条：`#FAFAFA`、`border-top:1px #EBEBEB`、`min-height:56px`、
  `padding:12px 12px 12px 20px`，说明推到最左、按钮靠右。

### Button（同一屏上同时出现的两档）

| 档 | 背景 | 文字 | 边 | 几何 |
| --- | --- | --- | --- | --- |
| primary（Save／Add New／Import） | `#171717` | `#FFFFFF` | 无 | 32–36px 高、6px 圆角、14px/500 |
| secondary（Filter and Sort Projects） | `#FFFFFF` | `#171717` | `0 0 0 1px #EBEBEB` | 同上 |
| disabled（Delete Team／Add more） | `#F2F2F2` | `#8F8F8F` | `0 0 0 1px #EBEBEB` | 同上 |

次级档不是透明的：它自己是一块比所在容器亮的面，所以压在 `#FAFAFA` 的操作条上仍读得出边界。
仪表盘工具行里两档并排出现，「主动作实底、其余白面」就是这套的全部规则。

### 滚动条

整站 `scrollbar-width` 与 `scrollbar-color` 都是 `auto`，没有一条 `::-webkit-scrollbar` 规则；
只在个别内部滚动区把滚动条整个藏掉。明暗两档的滚动条外观由 `color-scheme` 交给浏览器。

## Peach 对应（2026-09-05）

- 输入框一组边与环收进 `--field-ring`／`--field-ring-hover`／`--field-ring-focus`／`--field-glow`，
  聚焦是 1px 中性边加 4px 辉光，不再是蓝。顶部搜索、`.geist-search`、`.geist-input`、
  `.gselectfield`、`.sidebaraddfield`、偏好文本域共用这一份。
- 框体两块面收进 `--fieldset-bar`：正文一律 `--ground`，操作条 `--fieldset-bar`，
  外框 1px `--field-ring`、内部分隔线 `--line-soft`。暗色一档 Peach 的底带蓝，
  所以取 `#04060A` 而不是纯黑，方向与 Vercel 一致（操作条比正文更深）。
- 按钮次级档填 `--ground` 而不是透明，悬停抬到 `--surface`；禁用落到 `--sunk`。
- 滚动条不写任何自定义样式，交给 `html` 上的 `color-scheme`。
