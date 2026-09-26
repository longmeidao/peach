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
| lint | `frontend/.oxlintrc.json` 的 `ignorePatterns` 排除本目录，与 `boardui/` 同一个做法 | 上游源码用任意值类名、内联样式和原始颜色，逐字复制就过不了 `@shadcn/lint`；Peach 自己的组合仍全量检查 |
