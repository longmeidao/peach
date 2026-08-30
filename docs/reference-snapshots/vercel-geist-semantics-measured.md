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
- 登录态 Projects 页 <https://vercel.com/sandun-bingshi>：2026-08-30 的可见 DOM
  顺序为 Search、`Filter and Sort Projects`、Add New；实测同一行 36px 高、8px gap，
  搜索占剩余宽度，筛选按钮 36×36px，Add New 115×36px。筛选菜单 250px 宽、6px
  内边距、12px 圆角，内部纵向滚动且 `overscroll-behavior:contain`；展开没有动画。
  用户截图 `codex-clipboard-b47d665c-a203-4c22-8e79-1123b896e555.png` 的 SHA-256 为
  `037CBD12E6254072817F402864A0B11C641AA920CA4BD9EDEC08D591DAF2EA1E`（1673×189）。

Peach 保留的差异：添加关注沿用现有 38px 输入基线，因此筛选钮是 38×38px；Tooltip
使用 Peach 的暗色 surface 且不复制箭头或淡入动画。复用的是可聚焦语义、严格视口夹取、
菜单无展开动画，以及 Collapse 的高度／chevron 过渡，不把三种组件的 motion 混用。

## Peach 对应

- 语义按钮：`.fbtn.danger`（清空回收站等销毁类）、`.fbtn.primary` 保持主推进、
  批量已看/忽略保持 secondary；回收站清空区用红发丝边框卡。
- 行内状态：`ok`/`error` 用低饱和 tint 徽章（`.sbadge`），不再是裸文字。
- 检查失败报告条：对齐 danger 卡语义——红发丝边 + 微红底，去掉左侧粗条。
- 低密度管理页（统计/口味/复核等）内容列限宽约 1000px 居中；浏览页（首页/
  关注）保持全宽。
- 正文字体栈补 CJK sans：`"Microsoft YaHei UI","Microsoft YaHei","PingFang SC",
  "Hiragino Sans GB","Noto Sans CJK SC"` 置于 sans-serif 前。
