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

## Peach 对应

- 语义按钮：`.fbtn.danger`（清空回收站等销毁类）、`.fbtn.primary` 保持主推进、
  批量已看/忽略保持 secondary；回收站清空区用红发丝边框卡。
- 行内状态：`ok`/`error` 用低饱和 tint 徽章（`.sbadge`），不再是裸文字。
- 检查失败报告条：对齐 danger 卡语义——红发丝边 + 微红底，去掉左侧粗条。
- 低密度管理页（统计/口味/复核等）内容列限宽约 1000px 居中；浏览页（首页/
  关注）保持全宽。
- 正文字体栈补 CJK sans：`"Microsoft YaHei UI","Microsoft YaHei","PingFang SC",
  "Hiragino Sans GB","Noto Sans CJK SC"` 置于 sans-serif 前。
