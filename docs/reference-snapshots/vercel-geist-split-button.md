# Geist Split Button 实测记录

- 取证日期：2026-09-07
- URL：<https://vercel.com/geist/split-button>
- 取证方式：在浏览器里打开 Default 示例，对包裹层与两颗按钮读 `getComputedStyle` 和
  `getBoundingClientRect`，再点开触发档读菜单项文字；规范正文取页面 Best Practices 一节
- **不在 `docs/reference-sources.json` 里登记**：那张表的契约是「每个来源都有可哈希的上游
  快照」，这一页由 React 渲染，记下的是渲染结果，随上游发布变化且没有可锁定的文件哈希。
  要复核就按上面的方式重测一次。

## 实测几何

包裹层是一个 `div`，里面两颗 `button` 紧挨着，中间没有间隙：

| 位置 | 宽 × 高 | 圆角 | 说明 |
| --- | --- | --- | --- |
| 包裹层 | 95.4 × 40 | 0 | 只负责并排，没有自己的边框和底色 |
| 主动作（左） | 54.4 × 32 | `6px 0 0 6px` | 文字标签，`padding:0 6px`，14px/500 |
| 触发档（右） | 41 × 32 | `0 6px 6px 0` | 只有一枚箭头，`aria-label="Select save method"` |

两颗共用同一个底色（`rgb(23,23,23)`），交界处的竖线由触发档的 `::before` 画出来：
`left:-1px`、`width:1px`、`height:100%`，浅色主题 `#404040`、深色主题 `#cdcdcd`。
主动作 `border-r-0`、触发档 `border-l-0`，所以整体看着是一个盒子而不是两颗按钮。

## 菜单

默认 `menuAlignment="bottom-start"`，菜单贴主动作左边缘往下开。Default 示例的菜单项：

1. `Save` —— 和左半那颗的可见标签一字不差
2. `Save + Redeploy`

每项可以带一行说明（示例里是 `Save changes` 与 `Save changes and create a new production
deployment`），说明不参与和主动作的比对，第一行标签才是。

## 规范正文要点

- 一个动作是明确的默认值、旁边还有 1–4 个近亲变体时才用 Split Button；不相干的动作用普通
  Menu。
- 主动作必须原样作为菜单第一项，可见标签和菜单项标签必须完全一致——键盘和读屏用户只走
  菜单这一条路。
- 主动作只能是 default 或 secondary。API 明确挡掉破坏性变体：把删除藏进下拉是个尖角。
- 菜单项用 Title Case 的「动词 + 名词」；破坏性项排在最下面，上面加分隔线。
- `menuButtonLabel` 是触发档的 `aria-label`，写成描述这组动作的句子（如 `More deploy
  options`），它是读屏用户听到的唯一名称。
- 默认 `bottom-start`；只有按钮贴着容器右边缘时才换 `bottom-end`。

## Peach 的落点

口味页顶栏原本并排摆着「读取浏览器历史」和「导入历史文件」——同一件事（把浏览记录喂给口味
分析）的两种取得方式，权重却看着一样。现在合成一个 Split Button：左半是读取本机浏览记录，
右半的箭头开出菜单，第一项与左半同名同事，第二项是导入历史文件。

几何按 Peach 的动作条走：高度 36px 与同一行的下拉框齐平，圆角取 `--control-radius`，底色取
`--ground`，交界竖线上下各收 6px 用 `--border-15`。判据由 `tests/test_web_ui.py` 的
`test_history_actions_are_one_split_button_with_the_primary_mirrored` 守住。
