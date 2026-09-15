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

## 没有逐字复制的部分

| 上游 | 处理 | 原因 |
| --- | --- | --- |
| `globals`（`693885494e6f229637fe118852efbfb3df820dd8d174a2a7e47f65dadfcd96bf`） | 不复制整份；试点用到的 `check-draw` 动画和根元素的字体平滑搬进 `../styles.css`，作用域是 `.peach-react` | 整份 `@import "tailwindcss"` 会把 Preflight 和 `html`、`body` 的底色铺到整页，未迁移页面仍由旧样式表绘制 |
| Tailwind Preflight | `../preflight-scoped.css` 逐字包进 `@scope (.peach-react)` | 同上 |
| 深色模式 | 上游读 `<html class="dark">`；`web/app.js` 的 `applyTheme()` 与 `index.html` 首帧脚本按实际深浅加减这个类 | Peach 的主题选择写在 `data-theme`，跟随系统时不写属性 |
| 与 `web/board.css` 同名的 `--color-*` token | `:root` 上由 `board.css` 定值；`../styles.css` 在 `.peach-react` 与 `.dark .peach-react` 上按 `theme.css` 原文重新声明 | 未迁移页面的颜色保持不变，React 子树读到上游值；渲染到容器外的浮层不在这个范围里，用到时另行处理 |
| 焦点环 | 输入框只画 BoardUI 外框上的 `ring`；`web/css/01-base.css` 的全局 `:focus-visible` 排除 `.peach-react` 子树 | 旧样式表排在后面，同特指度时会盖过 `outline-none`，内层输入框多出一圈 |
| 提交键忙态 | 写 `aria-busy` 与 `aria-disabled`，不画 Spinner | `button` 条目没有加载态 |
| 行内警示 | `../settings/access-settings.tsx` 的 `Warning` 用 `status-yellow` token 组合 | 注册表里没有行内 Note 组件 |
