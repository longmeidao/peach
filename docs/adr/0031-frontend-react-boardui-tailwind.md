# ADR-0031：前端改用 React + Tailwind v4 + BoardUI 原版源码，继续按页面绞杀式迁移

- 状态：Accepted
- 日期：2026-09-15
- 关系：替代 ADR-0022 的框架与样式选择；沿用它的绞杀式迁移、构建产物入库、`/dist/` 路由与单一测试入口；ADR-0014 的 Video.js 保留。

## 背景

ADR-0022 选了 Preact 加手写 CSS，BoardUI 的外观靠把样式规则抄进 `web/css/` 与 `web/board.css`。抄写没有单一真相：同一个 token 在 BoardUI 与 `board.css` 各有一份定值，浅色中性灰、焦点蓝和跟随系统深色的三档文字色都对不上，界面反复「没对齐」。

BoardUI 通过 shadcn 注册表发布 React + Tailwind v4 源码，交互建在 React Aria 上。React Aria 不在 Preact 兼容层的支持范围内，留在 Preact 里就只能继续抄样式。

2026-09-14 在配置页「访问密码」分区做了试点：BoardUI 源码逐字复制，React 子树由 Preact 岛经 `ReactSlot` 挂载，与旧样式表同页共存。量到的代价与约束：

- `peach-react.js` gzip 110.6 kB，只在挂 React 子树的页面动态加载；`peach-react.css` gzip 11.8 kB，每页加载；
- Tailwind Preflight 必须限定在 `.peach-react` 容器内，工具类不能进层叠层；
- `board.css` 的同名 token 排在后面，React 容器上要按 `theme.css` 原文重新声明；
- 旧的全局 `:focus-visible` 会给 React 输入框多画一圈，必须排除 React 子树。

测试也要换写法。`tests/test_web_ui.py` 639 个用例里有 597 个只读旧前端源码的字符串；页面迁走后，这批断言如果改绑新源码的字符串，等于把「没对齐」从 CSS 挪进测试。

曾评估但不采用的方案：

- 继续 Preact + 手写 CSS：正是反复没对齐的来源。
- Preact + `preact/compat` 跑 BoardUI：React Aria 不支持兼容层。
- 只引入 Tailwind、组件自己写：样式仍是抄的，只是换成类名。
- 整站 React 重写：没有可验收的中间态，违反「替代实现测试通过后才删旧代码」。
- Next.js 等服务端渲染框架：单人自托管没有收益，还让运行时依赖 Node。
- 用 ESLint 承载 `@shadcn/lint`：`@typescript-eslint/parser` 的 peer 只到 TypeScript 6.0，项目用的是 7.0.2。

## 决策

- 新页面与迁移页面用 **React 19 + TypeScript（strict）+ Tailwind v4**，源码在 `frontend/src/react/`，单测用 vitest。
- **BoardUI 源码只加不改**：从注册表逐字复制到 `frontend/src/react/boardui/`，来源与条目哈希记在 `ORIGIN.md`，逐文件 SHA-256 记在 `UPSTREAM.sha256`。Peach 需要不同组合或外观时，在 `src/react/` 下 Peach 自己的目录里组合，差异写进 `ORIGIN.md`。
- **迁移节奏不变**：Preact 岛通过 `ReactSlot` 挂 React 子树，逐页替换，每次一到两个页面、独立分支集成；旧渲染函数、旧 CSS 与旧断言随页面删除，不保留双实现。最后一个 Preact 岛迁完移除 Preact；壳与路由迁完删除 `web/app.js`，`board.css` 里与 BoardUI 同名的 token 一并删除。
- **沿用 ADR-0022**：`npm run build` 的产物提交进 `web/dist/`，运行时不需要 Node；`/dist/{path}` 路由不变；测试入口仍是 `scripts/test.ps1` / `scripts/test.sh` 的 `web` 域；依赖精确锁定，在 `docs/FRONTEND.md` 登记用途。
- **旧断言先分类再删**。页面迁走时，它在 `tests/test_web_ui.py` 等处的源码字符串断言逐条归入三类，去向写进提交说明：
  - 设计决定（用户定过的颜色、状态色块、焦点样式）写成 `frontend/e2e/design.test.ts` 里读 `getComputedStyle` 的断言，或由 lint 规则覆盖；
  - 行为（提交什么、错误写回哪个字段、控件何时可用）写成 vitest；
  - 布局与运行期问题（溢出、等待态、控制台报错）归 `frontend/e2e/smoke.test.ts`。
- **门槛**：
  - `npm run lint` 用 Oxlint 跑 `@shadcn/lint` 的六条规则，只查 `src/react/`、排除 `boardui/`；`web` 域与 CI 都执行。
  - `tests/test_frontend_build.py` 按 `UPSTREAM.sha256` 逐文件比对 `boardui/`。
  - React 子树在请求期间写 `aria-busy`，首屏骨架写 `data-skeleton`，冒烟靠这两个标记判断页面稳定；BoardUI 组件不带加载态，由 Peach 的组合件补上。

## 后果

- 迁移期同一页会有两种外观：未迁移的分区仍是旧写法。
- 每个页面多加载 11.8 kB gzip 的 `peach-react.css`。
- Oxlint 的 JS 插件 API 仍是 alpha，`@shadcn/lint` 只有 0.1.0：两者精确钉版本，升级前先跑 `web` 域。`eslint` 作为 `@shadcn/lint` 的 peer 会装进 `node_modules`，不调用。
- 设计决定的浏览器断言和冒烟一样依赖本机 Chrome，缺 Chrome 时整组显式跳过。
- `tests/test_frontend_build.py` 的 `ReactBundleTests`（Preflight 作用域、样式表顺序、焦点环排除）只在新旧并存期成立，最后一个旧页面迁完时删除。

## 验收门槛

- 每个迁移分支：目标页面在桌面与 390×844 下功能等价；`web` 域与 `full` 全绿（含 tsc、vitest、lint、冒烟与设计决定断言）；`web/dist/` 与源码一致；旧断言的去向写进提交说明。
- 迁移完成的定义：`web/app.js` 删除，Preact 移除，`ReactBundleTests` 删除，`tests/test_web_ui.py` 删空，AGENTS.md 与 README 的前端章节只描述 React。
