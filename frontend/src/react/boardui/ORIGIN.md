# BoardUI 源码

来源是 BoardUI 的 shadcn 注册表条目 `https://www.boardui.com/r/<条目>.json`，2026-09-15 取得。
许可证为 MIT，原文见 `web/vendor/boardui-LICENSE.txt`。

本目录逐字复制条目里 `files[].content`，相对路径与上游 `path` 相同，上游源码里的
`@/utils/cx` 因此不用改写。这里的文件不做修改：Peach 需要不同的组合或外观时，
在 `../settings/` 这类 Peach 自己的目录里组合，差异写进下表。

`UPSTREAM.sha256` 记着复制时每个文件的 SHA-256，`tests/test_frontend_build.py` 逐文件比对：
改了副本、多出没登记的文件都会红。升级上游时重新复制、重算对应行，并更新下表的条目哈希。

| 条目 | 注册表 JSON 的 SHA-256 | 复制的文件 |
| --- | --- | --- |
| `theme` | `436353b1f8466dd56adf3909cb7a871288e0d6f5b067cf03a2f860375d2a013e` | `styles/theme.css` |
| `typography` | `5b7eca25350829755eb15cb474ab009fd1f8b929e62d54182f648b4f2e97bf8e` | `styles/typography.css` |
| `cx` | `d118c2ace1454a92fbfb69ad0d03b2916fece06ef5102ae26dcedaa6da2e390c` | `utils/cx.ts` |
| `button` | `89cc2c176d1d94d481bbfc6e34f233ccf109c10d319533cc7c1e98923b6e7d69` | `components/base/buttons/button.tsx` |
| `input` | `ac1e66c9ed15f9db2750dd528bc894c856ac84e79f72ff4acb96f14b1ab9c249` | `components/base/input/{input,label,hint-text}.tsx` |
| `checkbox` | `6210fdb4c54aab6dd89db3ae1bc387596a2dbacde62896aecaa2a7e15ece859c` | `components/base/checkbox/{checkbox,checkbox-glyph}.tsx` |
| `settings-modal` | `eb01742ca56daa473f042244176cd697fc20010ab18f680e3a3a8012d69f6c5b` | `components/application/settings/settings-rows.tsx` |
| `switch` | `3412c1910b2fa7f5d17404bf50bd2503e9ca097cf9d741366379cf18e09ebeb6` | `components/base/switch/switch.tsx` |
| `select` | `36a3a2b91508bdb278ecf84d24b35a7324e8be0781677e5bc12d8333eb9ff5ef` | `components/base/select/select.tsx`、`components/base/dropdown/menu-styles.ts` |
| `chevrons` | `b08900e01f7a82dcd38a66f46041a576fcefae667ed7afaba5d177c480ae85b0` | `components/foundations/icons/chevrons.tsx` |
| `use-dismiss-on-outside-press` | `854569e5d2188146c1ebb41ceccc9eaaddb3d4a31b623946e7dd72be650636b1` | `utils/use-dismiss-on-outside-press.ts` |
| `link-button` | `05eb37b3cf1334c153e0702de05fe4989e4359c9c74d5ba55cc552a58e4629bd` | `components/base/buttons/link-button.tsx` |
| `icon-button` | `1441e8301efc6e16e0693194f876ce285ca5fe8d440156a060a9266e012d2c90` | `components/base/buttons/icon-button.tsx` |

## 没有逐字复制的部分

| 上游 | 处理 | 原因 |
| --- | --- | --- |
| `globals`（`693885494e6f229637fe118852efbfb3df820dd8d174a2a7e47f65dadfcd96bf`） | 不复制整份；试点用到的 `check-draw` 动画和根元素的字体平滑搬进 `../styles.css`，作用域是 `.peach-react` | 整份 `@import "tailwindcss"` 会把 Preflight 和 `html`、`body` 的底色铺到整页，未迁移页面仍由旧样式表绘制 |
| Tailwind Preflight | `../preflight-scoped.css` 逐字包进 `@scope (.peach-react)` | 同上 |
| 深色模式 | 上游读 `<html class="dark">`；`web/app.js` 的 `applyTheme()` 与 `index.html` 首帧脚本按实际深浅加减这个类 | Peach 的主题选择写在 `data-theme`，跟随系统时不写属性 |
| 与 `web/board.css` 同名的 `--color-*` token | `:root` 上由 `board.css` 定值；`../styles.css` 在 `.peach-react` 与 `.dark .peach-react` 上按 `theme.css` 原文重新声明 | 未迁移页面的颜色保持不变，React 子树读到上游值 |
| 弹出层的挂载位置 | `../entry.tsx` 用 `react-aria` 的 `UNSAFE_PortalProvider` 把 Popover 渲染进 `body` 末尾一个同样带 `.peach-react` 的容器 | 上游 Popover 渲染到 `body`，落在 token 重声明与 Preflight 的作用域外，读到的是 `board.css` 的值 |
| 焦点环 | 输入框只画 BoardUI 外框上的 `ring`；`web/css/01-base.css` 的全局 `:focus-visible` 排除 `.peach-react` 子树 | 旧样式表排在后面，同特指度时会盖过 `outline-none`，内层输入框多出一圈 |
| 与旧样式表同名的类 | 网格容器放在 flex 父元素里写 `inline-grid`，块级化后按 `display:grid` 计算，类名不和卡片网格撞，也不触发任意值 lint；`../styles.css` 用 `@source not inline("ring")` 不生成注释里扫到的 `ring`；`frontend/test/legacy-class-names.test.ts` 核对产物与旧样式表无同名类 | 旧样式表排在后面，卡片网格那条同名规则会把 `grid-cols-*` 压成一列，生成的 `.ring` 也会落到旧页面的 `.ring` 元素上 |
| 提交键忙态 | 写 `aria-busy` 与 `aria-disabled`，不画 Spinner | `button` 条目没有加载态 |
| 行内提示 | `../settings/section.tsx` 的 `Note` 按语气取 `status-yellow`、`background-tertiary-error`、`notification-*` token 组合 | 注册表里没有行内 Note 组件；`notification` 条目是带关闭键和动效的浮动通知 |
| 进度条 | `../settings/section.tsx` 的 `Progress` 用 SVG 矩形画 | 注册表里没有进度组件 |
| 折叠 | `../settings/section.tsx` 的 `Disclosure` 用原生 `details` | 注册表里没有折叠组件 |
| 图标选择 | `../settings/library-icon-picker.tsx` 用 React Aria 的 `Popover`、`RadioGroup` 组合，面板取 `menu-styles.ts` 的外观 | 注册表里没有网格单选的弹出面板 |
