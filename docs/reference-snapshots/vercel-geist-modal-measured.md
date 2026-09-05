# Geist Modal 实测记录

- 取证日期：2026-09-04
- URL：<https://vercel.com/geist/modal>
- 取证方式：在浏览器里打开 Default 示例的 Modal，对 `[data-geist-modal]` 及其子节点读
  `getComputedStyle`，不是读源码或截图量取
- **不在 `docs/reference-sources.json` 里登记**：那张表的契约是「每个来源都有可哈希的
  上游快照」，这里记的是渲染结果，随上游发布变化且没有可锁定的文件哈希。要复核就按上面
  的方式重测一次。

## 实测值

| 项 | 值 |
| --- | --- |
| 容器角色 | `role="dialog"`、`aria-modal="true"`、`aria-labelledby` 指向标题 |
| 容器宽 | 540 px，`max-[540px]:max-w-[calc(100vw-20px)]` |
| 容器圆角 | 12 px |
| 容器最大高 | `min(800px, 80vh)` |
| 容器阴影 | `0 0 0 1px rgba(255,255,255,.14)` 加三层 `rgba(0,0,0,.06/.08/.12)` 的下投影 |
| 正文内边距 | 20 px |
| 正文字号／行高 | 14 px／20 px，色 `--ds-gray-900` |
| 标题元素 | `h3`，20 px／26 px，字重 600，左对齐 |
| 副标题 | 14 px／20 px，外边距 `8px 0 4px` |
| 操作条 | `sticky bottom-0`、内边距 12 px、`display:flex`、`justify-content:space-between`，两侧各是一个 `display:flex;gap:16px` 的分组 |
| 操作条高 | 约 54 px |
| 按钮高／圆角／字 | 30.7 px（Geist small 档 32 px）／6 px／14 px 500 字重 |
| 取消键 | 透明底加 `0 0 0 1px rgb(46,46,46)` 一圈线 |
| 主按钮 | `rgb(237,237,237)` 实底、`rgb(10,10,10)` 字 |
| 遮罩 | `.geist-overlay-backdrop`，纯黑 `rgb(0,0,0)`，**没有** blur |
| 出入场 | 透明度与 transform 都过渡 `.3s cubic-bezier(.175,.885,.32,1.1)`；transform 的起始值**未取得** |

## 文案判据（页面 Best Practices 一节）

- 标题是 Title Case 的**陈述句**，绝不写成问句。
- 正文 1～3 句，先说后果。
- 主按钮是「动词 + 名词」，动词与标题里那个一致；不写 Confirm、OK 或光秃秃一个动词。
- 取消键的字面就是 Cancel，不换花样。
- 销毁类弹层默认焦点落在取消键上，回车不得触发销毁动作；可撤销的弹层允许 Escape 和点
  遮罩关掉。
- 打开时锁焦点在弹层内，关掉后把焦点还给触发钮。
- 成功后的 Toast 与主按钮的动词一一对应（`Delete Project` → `Project deleted`）。

## Peach 复用了什么

`web/js/ui-components.js` 的 `confirmModal()` 与 `web/css/01-base.css` 的 `.geist-modal`
据此实现：540 px 宽、窄屏两侧各留 10 px、12 px 圆角、正文 20 px 内边距、标题 20 px／26 px
的 600 字重 `h3`、操作条粘底两端对齐、遮罩纯黑不带模糊、淡入用实测的时长与缓动。文案按上面
那一节写：资料页换统称的弹层标题是「更改统称」，主按钮同为「更改统称」，成功 Toast 是
「已把统称更改为 X」，取消键就写「取消」。

## Peach 有意不同的地方

| 项 | Peach | 原因 |
| --- | --- | --- |
| 承载元素 | 原生 `<dialog>` + `showModal()` | 焦点陷阱、Escape、背景 inert 和归还焦点都由浏览器给；Geist 那套 div 覆盖层要自己补齐这四样 |
| 按钮高 | 32 px（`--control-h` 档） | 全站控件已统一在这一档，见 `vercel-geist-controls-measured.md` |
| 手机上的按钮 | `min-height:44px` | 本项目的触控命中区门槛，Geist 未区分 |
| 出入场的 transform | 只做透明度 | 起始值未取得，不拿猜的值当复刻 |
| 阴影颜色 | `--border-15` 一圈线加 `#0009` 投影 | 暗色底下 Geist 的 `rgba(0,0,0,.06)` 几乎看不见，改用本项目已有的浮层阴影配方 |
