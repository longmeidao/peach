# Geist Tabs 的两个变体与分段器的分界（实测）

不登记进 `docs/reference-sources.json`：这里是浏览器实测的 DOM 计算值，给不出可重抓的上游字节。
对应的上游正文已登记，见 `docs/reference-snapshots/upstream/vercel-geist-tabs.md`
（来源 id `vercel-geist-tabs-secondary`）与 `docs/reference-snapshots/upstream/vercel-geist-switch.md`
（来源 id `vercel-geist-switch-segmented`）。

取证方式：2026-09-03 在浏览器打开 `https://vercel.com/geist/tabs` 与 `https://vercel.com/geist/switch`，
对 `[role="tablist"]` 及其 `[role="tab"]` 逐个读 `getComputedStyle` 与 `getBoundingClientRect`。
页面是深色主题，下面的 RGB 都是深色下的实测值。

## Tabs：primary（默认）

| 部位 | 实测 |
| --- | --- |
| tablist | `display:flex`、`gap:24px`、高 50px、`box-shadow:0 -1px 0 rgb(51,51,51) inset`（整条底线） |
| tab | `padding:14px 2px`、`font-size:14px`、`font-weight:400`、无圆角、无底色 |
| 选中 | 文字 `rgb(237,237,237)`，`border-bottom:2px solid rgb(237,237,237)` |
| 未选中 | 文字 `rgb(161,161,161)`，`border-bottom:2px solid transparent` |

## Tabs：secondary（`variant="secondary"`）

| 部位 | 实测 |
| --- | --- |
| tablist | `display:flex`、`gap:normal`（即 0）、高 32px、`!shadow-none`（不画底线） |
| tab | 高 32px、`padding:0 12px`、`border-radius:6px`、`font-size:13px`、`font-weight:400`、无边框 |
| 选中 | 底 `rgb(31,31,31)`（`--accents-2` 那一级），文字 `rgb(237,237,237)` |
| 未选中 | 底透明，文字 `rgb(161,161,161)` |

## Switch（分段器）

上游 Best Practices 原文见已登记的 upstream 文件。判据只有三条：分段器用于 2–3 个互斥选项、
两三个字的短标签、同一表面的不同视图；超过 3 项或标签变长就改用 Tabs 或 Select；布尔开关用 Toggle。
容器与选中块的实测数值早前已记在 `docs/reference-snapshots/vercel-geist-note-progress-switch-analytics.md`。

## Peach 的落点与保留的差异

- 人工复核分类 10 项、垃圾文件分类 7 项，都越过分段器的 2–3 项上限，所以这两条是 Tabs 不是 Switch。
  两条现有的 pill 外观本来就对应 secondary 变体，不改成下划线式，只把数值对齐 secondary。
- 浅色主题里选中底色取 `--hover`：深色实测的 `rgb(31,31,31)` 是「比页面底色高一级的中性面」，
  Peach 浅色下同一语义的变量是 `--hover`，不是墨色反相。原先两条都用 `--ink-2` 反相 + 600 字重，
  比规范重了一整级。
- 计数按规范当徽标处理，为 0 时整枚去掉，不留 `0` 占位。
- 垃圾文件那条仍是 `<a href>` 导航而不是 `role="tab"`：规范要求当前项反映在 URL 上可深链，
  Peach 这里就是靠 `?type=` 做的；同一条里的「已排除」是另一根轴（视图切换），
  用分隔符隔开，也不进 tablist。复核分类没有独立 URL，升级成了真正的 `role="tablist"`
  加左右方向键漫游焦点。
- Peach 保留每项前的图标（上游 `With icons` 示例支持 icon slot）与 40em 以下 44px 触摸高度。
