# transitions.dev 动效配方实测记录

- 取证日期：2026-09-16
- URL：<https://transitions.dev/>，逐条配方在 `https://transitions.dev/transitions/<slug>`
- 取证方式：打开每条配方页的 CSS 标签页，读它给出的 `:root` 变量与 `@keyframes` 数值。
  页面上每条都有 CSS 与 React 两个标签页，React 那份只是把同一段 CSS 包一层组件，
  数值一致，所以只记 CSS 那份。
- **不在 `docs/reference-sources.json` 里登记**：那张表的契约是「每个来源都有可哈希的
  上游快照」。这里取的是一页上多条配方的参数，页面由站点自己的组件渲染、随时可改，
  给不出可锁定的单文件哈希。要复核就按上面的方式重开配方页读一遍 CSS 标签页。
- 许可：上游仓库没有 LICENSE 文件，页面只写「copy and paste them」，没有给出明确授权
  条款。因此 Peach 只借形态与参数，类名与变量名一律自拟：不使用它的 `t-*` 类名，
  也不使用它的 `:root` 变量名。落地代码在 `web/css/25-motion.css` 与 `web/board.css`。
- **未取得**：上游各条配方所依据的设计原始稿、参数取值理由和许可条款均未取得；
  上游没有公布 spring 参数，它的「弹」一律由带超调控制点的 `cubic-bezier` 近似。

## 逐条对照

时长与缓动一律并进 Peach 已有的动效 token：`--board-motion`（.3s cubic-bezier(.4,0,.2,1)）、
`--spring-press`（208ms 采样弹簧，峰值 1.088）、本次新增的 `--motion-swap`（.25s）、
`--motion-reveal`（.4s）、`--motion-stagger`（70ms），全部由 `board.css` 那一条
`prefers-reduced-motion` 规则统一归零。

| 配方 | slug | 上游取值 | Peach 落成值 | 落点 |
| --- | --- | --- | --- | --- |
| 字形换字形 | `icon-swap` | 250ms；`ease-in-out`；blur 2px；scale .25 | `--motion-swap`（.25s cubic-bezier(.4,0,.2,1)）；blur 2px；scale .25 | `.iconswap`；`iconSwapHtml`／`setIconSwap` |
| 一行字换一行字 | `text-states` | 150ms；`ease-in-out`；blur 2px；位移 4px | `--motion-swap`；blur 2px；位移 4px | `.textswap`；`swapText` |
| 读数按位跳出 | `number-pop-in` | 500ms；`cubic-bezier(0.34,1.45,0.64,1)`；blur 2px；位移 8px；按位延迟 70ms | `--motion-swap` + 同一条超调缓动；blur 2px；位移 8px；`--motion-stagger` 70ms | `.digits`；`popCount` |
| 占位换真内容 | `skeleton-loader` | 400ms；`ease-in-out`；blur 2px | `--motion-reveal`（.4s cubic-bezier(.4,0,.2,1)）；blur 2px | `.skelreveal`／`.skelfade`；`revealSkeleton` |
| 开关双弹 | `toggle-double-bounce` | 350ms；`cubic-bezier(0.34,1.35,0.64,1)`；行程 14.66px；超出端点 1px | `--spring-press`（208ms，峰值 1.088，行程 18px，超出约 1.6px） | `.ptoggle::after`／`::before` |
| 成功打勾 | `success-check` | 四段各 500ms；rotate 80deg；blur 10px；上荡 40px；`stroke-dasharray` 20；画笔延迟 80ms | `--board-motion` 走转正与清晰、`--spring-press` 走上荡 14px；rotate 80deg；blur 10px；`stroke-dasharray` 24；画笔延迟 `--motion-stagger` | `.checkdraw`；toast 图标 |
| 失败抖动 | `error-shake` | 280ms；`cubic-bezier(0.22,1,0.36,1)`；关键帧 0／28.57％／57.14％／78.57％／100％，位移 0／6px／-6px／4px／0 | `--board-motion`；同样的五个关键帧与位移 | `@keyframes field-shake`；`[aria-invalid="true"]` |

## 与上游取值不同的几处判断

- 开关双弹不写关键帧。上游用一条超调缓动模拟弹簧，Peach 已经有采样自真实弹簧的
  `--spring-press`，峰值 1.088 折到 18px 行程上就是约 1.6px 的超出，手感与上游那条
  1px 超出同档，所以直接让 thumb 的 `transform` 走这条弹簧。
- 成功打勾的上荡距离取 14px 而不是 40px：这枚勾长在 toast 的图标位上，只有 16px 见方，
  40px 会把它荡出 toast 的边界。`stroke-dasharray` 取 24 是 Peach 这枚 Lucide 勾的
  实际折线长度，不是上游那枚字形的 20。
- 读数与文字的换态只在值真的变了时才走，首次落笔不动。上游示例每次渲染都播一遍，
  在 Peach 这是首页每次筛选都要重画的读数，首屏会变成一片抖动。
- 骨架换内容时旧的那一层抬成绝对定位再淡出，容器高度全程由新内容决定；上游示例里
  两块内容尺寸相同，不需要处理这一步。
