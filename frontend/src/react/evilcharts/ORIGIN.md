# EvilCharts 源码

来源是 EvilCharts 仓库 `https://github.com/legions-developer/evilcharts` 的 Recharts 分支，
提交 `500ecd44c1fdcf319ba83ea68f3771bc76125974`（2026-08-29），2026-09-26 取得。
文档站是 `https://evilcharts.com/docs/recharts/`。许可证为 MIT，原文见 `web/vendor/evilcharts-LICENSE.txt`。
取舍见 `docs/adr/0076-evilcharts-recharts-charts.md`。

本目录逐字复制上游 `src/registry/` 下的文件，相对路径与上游相同，所以上游源码里的
`@/registry/*` 只要一条路径别名就能解析。这里的文件不做修改：Peach 需要不同的组合或外观时，
在 `../charts/`、`../stats/`、`../taste/` 里组合，差异写进下表。

`UPSTREAM.sha256` 记着复制时每个文件的 SHA-256，`tests/test_frontend_build.py` 逐文件比对：
改了副本、多出没登记的文件都会红。升级上游时重新复制、重算对应行，并更新下表。

| 注册表条目 | 复制的文件 | 上游依赖 |
| --- | --- | --- |
| `recharts-chart` | `registry/ui/recharts-chart.tsx` | `recharts` |
| `recharts-tooltip` | `registry/ui/recharts-tooltip.tsx` | `recharts` |
| `recharts-legend` | `registry/ui/recharts-legend.tsx` | `recharts` |
| `recharts-background` | `registry/ui/recharts-background.tsx` | `recharts` |
| `recharts-brush` | `registry/ui/recharts-brush.tsx` | `recharts` |
| `recharts-dot` | `registry/ui/recharts-dot.tsx` | `recharts` |
| `recharts-bar-chart` | `registry/charts/recharts-bar-chart.tsx` | `recharts`、`motion` |
| `recharts-radial-chart` | `registry/charts/recharts-radial-chart.tsx` | `recharts`、`motion` |
| `recharts-radar-chart` | `registry/charts/recharts-radar-chart.tsx` | `recharts`、`motion` |

`recharts-brush` 与 `recharts-dot` 没有页面直接用，是柱状图和雷达图 import 的部件。

## 没有逐字复制的部分

| 上游 | 处理 | 原因 |
| --- | --- | --- |
| `@/lib/utils` 的 `cn` | `../charts/cn.ts`：先经 `clsx` 摊平条件类名，再交给 BoardUI 的 `cx` | 上游的 `cn` 由 `shadcn init` 生成，Peach 不跑 init；`cx` 已是带 BoardUI 字阶的 `tailwind-merge`，但不认 `clsx` 的对象写法 |
| 路径别名 | `frontend/vite.react.config.ts`、`frontend/vitest.config.ts` 与 `../tsconfig.json` 把 `@/registry/*` 指到本目录、`@/lib/utils` 指到 `../charts/cn.ts`，排在 BoardUI 的 `@/*` 前面 | 上游按 shadcn 项目的目录写 import，改路径就要改上游文件 |
| 类型导入 | `../tsconfig.json` 关掉 `verbatimModuleSyntax` | 上游用普通 import 取 `RectRadius`、`TypedDataKey` 两个类型；`isolatedModules` 仍开着，转译时照常剥掉 |
| shadcn 语义色名 | `../styles.css` 的 `@theme inline` 把 `background`、`foreground`、`muted`、`muted-foreground`、`border` 接到 BoardUI 已有 token；`primary` 不接 | 上游浮层与轴刻度写的是 shadcn 色名，Peach 没有这一套变量；`primary` 只有加载指示用，Peach 不传 `isLoading` |
| 系列颜色 | 调用处的 `ChartConfig` 只写 `var(--color-chart-N)`，不写上游示例里的 oklch 字面值 | 颜色只取 BoardUI 的 `chart-*` 档，深浅两档跟着 token 走 |
| reduced motion | `../entry.tsx` 在每棵 React 根外包一层 `MotionConfig reducedMotion="user"` | 柱状图的生长动画由 Motion 逐帧驱动，`web/css/01-base.css` 的全局规则只关得掉 CSS 过渡；Recharts 自己的动画在 `isAnimationActive="auto"` 下已读系统设置 |
| 浮层内容 | `../charts/chart-tip.tsx` 的 `ChartTip` 照 `ChartTooltipContent` 的类名重组，容器换成 `flex flex-col`，经上游的 `ChartTooltip` 接进图里；各图的 `Tooltip` 子组件都不用 | 上游容器写 `grid` 类，与旧样式表卡片网格的 `.grid` 同名，页面上浮层会被撑成卡片宽的格子、行距变成 24px |
| lint | `frontend/.oxlintrc.json` 的 `ignorePatterns` 排除本目录，与 `boardui/` 同一个做法 | 上游源码用任意值类名、内联样式和原始颜色，逐字复制就过不了 `@shadcn/lint`；Peach 自己的组合仍全量检查。排除之后本目录里与旧样式表同名的类名不会被拦（上面那一行就是），升级上游时按 `../styles.css` 里 `@source not inline` 的几个词搜一遍 |

## Peach 的组合

| 组合 | 用到的上游 | 做法 |
| --- | --- | --- |
| `../charts/bar-card.tsx` 的 `BarCard` | `EvilBarChart` | 单系列，`ChartConfig` 只有 `value` 一个键；数值轴隐藏、留两成余量，数经 `barProps.label` 标在柱端；容器加 `flex-none`，否则在卡片的 flex 列里被压成 0 高。统计页的时长、画质、文件类型与播放次数 |
| `../stats/radial-card.tsx` 的 `RadialCard` | `EvilRadialChart` | 键写成 `s0`…`sN`，名字放进 `label`：键会进 CSS 变量名与渐变 id，来源名、库名不能直接当键。圈的形状与点击走 `radialBarProps`，按 React 状态淡化其余段、点下钉住；图例格子由 Peach 自己画 |
| `../taste/charts.tsx` 的 `TasteRadar` | `EvilRadarChart` | 取分数最高的三到六个口味维度，单系列 `value`；少于三个画不成面，整块不出现。`chartProps.outerRadius` 压到 58%，顶点外侧的维度名在窄栏里放得下 |
| `../taste/charts.tsx` 的 `RankedBars` | `EvilBarChart`（`layout="horizontal"`） | 前八个口味维度，柱端标数的写法同 `BarCard`；高度按条数取档 |
| `../charts/chart-tip.tsx` 的 `ChartTip` | `ChartTooltip`、`useChart`、`getPayloadConfigFromPayload` | 见上表「浮层内容」 |
