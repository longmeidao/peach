# ADR-0031：前端改用 React + Tailwind v4 + BoardUI 原版源码，继续按页面绞杀式迁移

- 状态：Accepted
- 日期：2026-09-15
- 修订：2026-09-15 补齐迁移桥接契约、弹层样式作用域、上游升级方式、lint 边界与验收定义；同日写下前端基础库的取舍与引入时机。2026-09-16 活动页迁入后 Query 的引入时机与共用方式按实际落地改写；同日配置页外壳与换头像迁入、Preact 移除后，挂载方式只剩 React 档一种，JSX 运行时不再分档；同日复核页迁入、已迁八页外观对回迁移前基线后，补页面外观以基线 CSS 为准的判据与玻璃面高对比回退的归属
- 关系：替代 ADR-0022 的框架与样式选择；沿用它的绞杀式迁移、构建产物入库、`/dist/` 路由与单一测试入口；ADR-0014 的 Video.js 保留。

## 背景

ADR-0022 选了 Preact 加手写 CSS，BoardUI 的外观靠把样式规则抄进 `web/css/` 与 `web/board.css`。抄写没有单一真相：同一个 token 在 BoardUI 与 `board.css` 各有一份定值，浅色中性灰、焦点蓝和跟随系统深色的三档文字色都对不上，界面反复「没对齐」。

BoardUI 通过 shadcn 注册表发布 React + Tailwind v4 源码，表单与弹层交互建在 React Aria 上。留在 Preact 里，要么继续抄样式，要么经 `preact/compat` 运行 React Aria 并自行验证每个组件的焦点、弹层与键盘行为。

2026-09-14 在配置页「访问密码」分区做了试点：BoardUI 源码逐字复制，React 子树由 Preact 岛经 `ReactSlot` 挂载，与旧样式表同页共存。量到的代价与约束：

- `peach-react.js` gzip 110.6 kB，只在挂 React 子树的页面动态加载；`peach-react.css` gzip 11.8 kB，每页加载；
- 旧样式表不分层，其中 `button,input{color:inherit}` 这类标签规则会压过层叠层里的工具类；
- Tailwind Preflight 铺到整页会改掉未迁移页面的标题、表单与图片基线；
- `board.css` 的同名 token 排在后面，会盖过 `theme.css` 的上游值；
- 旧的全局 `:focus-visible` 会给 React 输入框多画一圈。

测试也要换写法。`tests/test_web_ui.py` 639 个用例里有 597 个只读旧前端源码的字符串；页面迁走后，这批断言如果改绑新源码的字符串，等于把「没对齐」从 CSS 挪进测试。

曾评估但不采用的方案：

- 继续 Preact + 手写 CSS：正是反复没对齐的来源。
- Preact + `preact/compat` 跑 BoardUI：兼容层下 React Aria 的焦点管理、Portal 与键盘行为需要逐组件验证，升级时还要重验。Peach 不承担这份适配维护。
- 只引入 Tailwind、组件自己写：样式仍是抄的，只是换成类名。
- 整站 React 重写：没有可验收的中间态，违反「替代实现测试通过后才删旧代码」。
- Next.js：本次迁移用不到它的路由与服务端能力；静态导出同样不需要 Node 运行时，但既有 Vite 构建加 Python 静态服务已经满足需要，换框架只增加迁移面。
- 用 ESLint 承载 `@shadcn/lint`：`@typescript-eslint/parser` 的 peer 只到 TypeScript 6.0，项目用的是 7.0.2。

## 决策

### 技术栈与上游源码

- 新页面与迁移页面用 **React 19 + TypeScript（strict）+ Tailwind v4**，源码在 `frontend/src/react/`，单测用 vitest。
- 前端只有 React 一种渲染层，`frontend/src` 里 JSX 只出现在 `src/react/`；`frontend/src/react/tsconfig.json` 只为逐字复制的 BoardUI 源码放宽 `exactOptionalPropertyTypes` 与 `noUncheckedIndexedAccess` 两条，其余继承全局配置。Vite 与 tsc 都取离文件最近的 tsconfig。
- **BoardUI 源码日常开发只读**：从注册表逐字复制到 `frontend/src/react/boardui/`，来源与条目哈希记在 `ORIGIN.md`，逐文件 SHA-256 记在 `UPSTREAM.sha256`。Peach 需要不同组合或外观时，在 `src/react/` 下 Peach 自己的目录里组合，差异写进 `ORIGIN.md`。
- **页面外观以该页迁移前的基线 CSS 为准**，不以「BoardUI 里长什么样」为准：卡面、读数卡、分段控件、空态这类跨页共用的面收在 `src/react/components/` 各自一处（`card.tsx` 按基线选 `filled` / `outlined` / `raised`），页面不自己拼类名串。测试只钉数据流与结构，钉不住外观，验收要对照迁移前提交的样式表与骨架逐块核卡面、网格列数、控件形态。
- **上游升级走独立提交**：整文件重新复制，同一提交更新 `ORIGIN.md` 条目哈希、`UPSTREAM.sha256`、`theme.css` 与相关依赖，跑 `web` 域回归。发现上游缺陷时同样以组合件绕开或等上游修复后整文件替换，不在副本上打补丁。没有引用者的上游文件连同哈希行一起删除。哈希只证明副本没有偏离登记版本，组件行为仍由 vitest 与浏览器断言验证。

### 迁移桥接

- **迁移节奏不变**：逐页替换，每次一到两个页面、独立分支集成；旧渲染函数、旧 CSS 与旧断言随页面删除，不保留双实现。
- **迁移期只有一种 React 挂载方式**，由 `frontend/src/islands.ts` 的 `mountIsland` / `unmountIsland` 对遗留层暴露：注册表写 `{react: '<page>'}`，`@peach/react` 的 `pages.<page>` 提供 `prefetch(props, signal)` 与 `mount(el, props)`。`mountIsland` 先 `prefetch` 把首屏写进 Query 缓存（取完数才画，中止就放弃这一次；产物加载回来后先确认容器仍在、遗留层还停在这一页，再画），再在容器里建一个 `.peach-react` 宿主创建 React root，第一帧用 `flushSync` 同步落 DOM（遗留壳挂完紧接着就读页面结构，配置页按 `.configgroup` 拆左栏页签靠它）；`unmountIsland` 中止在途请求、卸根、撤宿主。遗留壳在 `claimSurface` 换页时对 `#stats` 与 `#index` 调 `unmountIsland`，它连子孙容器一起卸（`#libraryProcessing` 挂在 `#stats` 里更深的一格上，换头像挂在 `#index` 的圆框上），所以离开页面后组件不再活着，轮询随组件一起停；不在这两个容器里的（目录页横幅 `#libraryProcessingNotice`）由它自己的路由判据卸。
- **业务状态只有一份**：取数与缓存归 TanStack Query，所有 React root 共用一个 `QueryClient`，同一份真相只用一个 `queryKey`，第二个读者读同一个键；节律不同的两份真相分键（来源列表由用户改、由写操作换单条，封面任务由后台推进、按状态轮询），合成一键会让轮询重画用户正在填的表单。写操作用 `useMutation`，成功后用 `setQueryData` 换局部，不为一次写入重取整页；页面之间不另起一套订阅传数据，也不在遗留层与 React 两侧各存一份同一数据。页面经 props 拿遗留能力、经回调（如 `receipt`、`onPicked`）交回结果。需要的遗留能力（`confirmModal`、来源图标表、番号标题）只经 `@peach/legacy/*` 的声明模块或 props 传入的遗留函数调用，不抄一份。
- Peach 自己以 HTML 字符串拼出的 Board 风格组件随使用它们的页面改写成 `src/react/` 下的组合件，复用其中的数据与布局计算：`board-metrics.ts`、`board-sankey.ts`、`board-analytics.ts` 已随统计页与口味页改写并删除；`board-controls.ts` 剩下的是给遗留页共用的 DOM 行为（范围输入读数、全站 tooltip、下划线 Tabs 与分段控件的滑块），读者只剩各页骨架（复核页迁走后页面里没有遗留读者，`.follow-workspace-switch` 只剩骨架里那一份），随最后一个遗留读者一起删。
- 删除顺序：Preact 已随最后一个岛（配置页外壳与换头像）移除，`peach-ui.js` 现在是把遗留壳接到 `pages` 上的那层加上仍被 `web/app.js` 调用的非页面模块，这些模块随使用它们的页面一起迁走；壳与路由迁完，React Router 直接挂页面，删除 `web/app.js`、`mountIsland` 与 `peach-ui.js`。`board.css` 里与 BoardUI 同名的 token 按 `var()` 读者归零删除，不按自写组件删完删除：口味页迁完时这些 token 仍被 `board.css` 自身和遗留页读着，删早了遗留页就掉色。

### 新旧样式并存

以下做法只服务于新旧样式表同页的阶段，由 `tests/test_frontend_build.py` 的 `BoardTokenTests`、`ReactBundleTests` 钉住：

- 工具类不进层叠层，旧样式表的标签规则因此压不过类名；
- Preflight 逐字包进 `@scope (.peach-react)`；
- React 容器上按 `theme.css` 的 `:root` 与 `.dark` 块重新声明同名 token。这份声明不是手工副本，`BoardTokenTests` 逐条比对它与 `theme.css`，不一致即失败；
- 全局 `:focus-visible` 排除 `.peach-react` 子树；
- React 子树里复刻的旧玻璃面，其高对比回退仍写在 `web/board.css`，按 `data-*` 属性（`data-glass-pane`）认人：`frontend/test/legacy-class-names.test.ts` 禁止 React 产物与遗留样式表出现同名类。

**作用域覆盖弹层**：React Aria 的 Popover、Select 列表与 Dialog 经 Portal 渲染到容器外。`entry.tsx` 用 `UNSAFE_PortalProvider` 把它们统一挂到 `body` 末尾一个同样带 `.peach-react` 的容器，读到的 token、Preflight 与焦点规则和页面内一致。弹层不塞进可能裁切它的局部容器。

旧样式表全部退出后重新评估上述五条：仍被第三方样式（如 Video.js）需要的隔离保留并写明原因，其余删除，Tailwind 回到上游默认的层叠层写法。

### 测试与门槛

- **沿用 ADR-0022**：`npm run build` 的产物提交进 `web/dist/`，运行时不需要 Node；`/dist/{path}` 路由不变；测试入口仍是 `scripts/test.ps1` / `scripts/test.sh` 的 `web` 域；依赖精确锁定，在 `docs/FRONTEND.md` 登记用途。
- **旧断言先分类再删**。页面迁走时，它在 `tests/test_web_ui.py` 等处的源码字符串断言逐条归入三类，去向写进提交说明：
  - 设计决定（用户定过的颜色、状态色块、焦点样式）写成 `frontend/e2e/design.test.ts` 里读 `getComputedStyle` 的断言，或由 lint 规则覆盖；
  - 行为（提交什么、错误写回哪个字段、控件何时可用）写成 vitest；
  - 布局与运行期问题（溢出、等待态、控制台报错）归 `frontend/e2e/smoke.test.ts`。
  - 三类各管一件事：lint 查源码是否守约定，`getComputedStyle` 查浏览器实际应用的样式，vitest 与浏览器交互查点击和键盘行为，互不替代。
- **lint**：`npm run lint` 用 Oxlint 跑 `@shadcn/lint` 的六条规则，只查 `src/react/`、排除 `boardui/`；`web` 域与 CI 都执行。
  - `no-restyle` 按 `settings.shadcn.ui`（`@/components`）识别 BoardUI 组件，所以 Peach 代码一律经 `@/components/...` 别名引用 BoardUI，不写相对路径；
  - 规则约束的是随手改颜色、间距与组件外观。由数据决定的几何（进度、定位、媒体尺寸）走 SVG／元素属性或 React Aria 自带定位；确需内联样式时逐行禁用并在同一行写明原因，不整条关规则。
- **哈希**：`tests/test_frontend_build.py` 按 `UPSTREAM.sha256` 逐文件比对 `boardui/`。
- **页面稳定判据**：冒烟先断言目标页面主体已出现（成功内容、空态或错误态之一），再等 `aria-busy` 与 `data-skeleton` 消失。只看等待标记消失不算稳定：页面完全没渲染时也没有这两个标记。React 子树在请求期间写 `aria-busy`，首屏骨架写 `data-skeleton`；BoardUI 组件不带加载态，由 Peach 的组合件补上。

## 后果

- 迁移期同一页会有两种外观：未迁移的分区仍是旧写法。
- 每个页面多加载一份 `peach-react.css`，体积随迁移的页面增长，当前值记在 `docs/FRONTEND.md`。
- Oxlint 的 JS 插件 API 仍是 alpha，`@shadcn/lint` 只有 0.1.0：两者精确钉版本，升级前先跑 `web` 域。`eslint` 作为 `@shadcn/lint` 的 peer 会装进 `node_modules`，不调用。
- 冒烟与设计决定断言依赖 npm、ffmpeg 与 Chrome。本机缺任一项时整组显式跳过，这只适用于非验收运行。CI 的 `web-bundle` 任务跑 typecheck、lint、vitest 与 build，不跑 e2e；CI 接入带浏览器的 e2e 任务、并在 CI 里把缺依赖判为失败之前，迁移分支须在本机 `web` 域输出里确认 e2e 实际执行。
- `ReactBundleTests` 与 `BoardTokenTests` 里只在新旧并存期成立的断言，随「新旧样式并存」一节的做法一起删除。

## 验收门槛

- 每个迁移分支：
  - 目标页面在桌面与 390×844 下功能等价；
  - `web` 域与 `full` 全绿，含 tsc、vitest、lint、冒烟与设计决定断言，e2e 显示为跳过的运行不算通过；
  - 反复进入、离开、返回页面，以及请求未完成时切页，都不重复请求、不留旧数据覆盖新页面，控制台无报错；
  - 页面含弹层时，在浏览器里核对明暗主题、焦点进出与恢复、层叠顺序与滚动锁定；
  - `web/dist/` 与源码一致；旧断言的去向写进提交说明。
- 迁移完成的定义：
  - `web/app.js` 删除，`mountIsland` 与 `@peach/legacy/*` 移除；
  - 并存期断言按上一节删除；
  - `tests/test_web_ui.py` 里依赖旧实现的断言迁移或删除完毕，仍然成立的静态资源、页面服务与构建契约测试保留或迁往对应测试文件；
  - AGENTS.md 与 README 的前端章节只描述 React。

## 修订：浏览器用例在 CI 执行，冒烟逐路由写明主体（2026-09-15）

「后果」里约定：CI 接入带浏览器的 e2e 任务、并把缺依赖判为失败之前，迁移分支须在本机确认 e2e 实际执行。
当时 `python` 矩阵没有 Node、`frontend/node_modules`、ffmpeg 与 Chrome，`tests/test_web_e2e.py` 在 CI 上每次都跳过；
冒烟也只等 `aria-busy` 与 `data-skeleton` 消失，「页面稳定判据」要求的主体断言还没有落到用例里。两件事现已接入：

- 需要 Node、前端依赖、ffmpeg 或 Chrome 的用例统一经 `tests/support/conditions.py` 的
  `missing_prerequisite` 判定：本机缺失时显式跳过，`GITHUB_ACTIONS=true` 时判失败。
  `test_frontend_build.py` 的 tsc、lint、vitest 同一口径。
- CI 新增 `web-e2e` job，在 `windows-latest` 上装齐四样、经 `PEACH_E2E_CHROME` 指定 Chrome，
  执行 `web` 域并纳入 `verified` 汇总；矩阵扩成全量时 Windows 全量行已含 `web` 域，它按条件跳过，
  同一批用例不跑两遍。`python` 矩阵里 `core` 以外的行也装 Node，Windows 行
  另装 ffmpeg 与 Chrome，否则全量行上的这些用例会判失败。工作流结构由 `test_frontend_build.py` 断言。
  本机确认 e2e 实际执行那一条随之由 CI 兜住；本机跳过仍不算验收通过。
- `frontend/e2e/smoke.test.ts` 为每条路由写明主体：路由自己的标题，加上内容区、索引条目或明确的空态。
  先等主体可见，再 `settle`，再量几何。新增路由要同时写明它的主体。

## 修订：前端基础库随页面引入，不预装（2026-09-15）

外部审查按 master `a1ff3cf6` 逐项评估了迁移期常被一并推荐的基础库。判据只有一条：**页面既然要改写，比较的是改写后
的长期维护成本，不是「现在多装一个依赖」**；已有实现不是保留它的理由，但业务语义（身份、分页口径、显式触发）不随库
一起换掉。取舍如下，引入时机都绑在对应页面的迁移分支上，不单独开「装库」的提交。

| 库 | 决定 | 时机与边界 |
| --- | --- | --- |
| TanStack Query | 引入 | 随第一个整页归 React 的页面进入：活动页的三段读 `/api/tasks` 一个 `queryKey`，轮询写成 `refetchInterval`。高清版页随页面迁移接进同一个 client，前端没有 Preact signals store、`frontend/src/state/` 与 `refreshStore`，`@preact/signals` 不在依赖清单里；数据管理卡片的总数在数据管理页迁移时读高清版页同一个 `queryKey`。API 地址、响应类型、错误文案与 `useAction` 的提交互斥保留。所有 React root 共用 `frontend/src/react/query.ts` 里那一个 `QueryClient`：`retry: 0`，不因窗口聚焦或重新挂载自动重取（首屏由页面级 `prefetch` 决定，重进页面就是重取）；本机接口用 `networkMode: 'always'`；对外部来源的采集与追更仍只由用户显式触发，不进 Query 的自动重取；后台任务的**状态**是本机端点，按 `running` 开关 `refetchInterval` 跟进度，跟的是状态不是重新触发；首屏读到的旧终态不画成新结果，只有本次启动过或本次见过 `running` 的那一趟才发回执；`AbortSignal` 必须传到实际 `fetch` |
| TanStack Table | 已引入（8.21.3） | 随关注管理的表格视图进入：BoardUI 的 Data Table 本身由它驱动，Peach 逐字复制的是 `table` 条目，`data-table` 是只有示例的 block、依赖的条目 Peach 没有，只读不抄；别名表、只读信息表用 BoardUI 基础 Table。选择以来源 ID、条目 ID 为身份（`getRowId`），卡片与表格两个视图共用一份选择集合，跨页批量以 ID 集合为准；排序作用于整个结果集：数据能一次取完时由前端对全集排（`manualSorting`，`/api/follow` 一次回全部来源），取不完时由后端全量排，两种都不许把「只排当前页」表现成排了整个结果集 |
| React Router | 外壳阶段接管 | 在迁移 `web/app.js` 的壳与路由那一步用 Declarative 模式接管客户端导航，此前旧路由是唯一导航管理者，不在 React 子树里另设路由。迁移要保留 `web/js/routes.js` 的既有规则：数字 ID 校验、实体名称吃掉后续含斜杠的路径、返回列表的状态与播放期间的导航行为 |
| TanStack Virtual | 随馆藏网格迁移引入；旧壳先用 `content-visibility` 缓解 | 见下节实测：连续加载到 1500 张卡片时滚动帧间隔到 48 ms，给卡片加一条 `content-visibility: auto` 就降到 18 ms。网格是分段、竖屏带、悬停预览与就地舞台的组合，不是均匀列表，虚拟化要同时解决动态高度、滚动位置恢复与页内查找，所以在网格迁到 React 时作为该页的设计输入一起做，不在旧壳里再写一份。旧壳阶段只加那条 CSS，随 `web/css/12-cards.css` 的改动走 e2e |
| Vidstack、Uppy、Refine | 不引入 | Video.js 保留（ADR-0014），只迁播放器的 React 接入；Peach 的入口是扫描、挂载与来源采集，没有上传中心；已有自己的业务接口、复核与任务处理，不再套资源管理层 |

### 馆藏网格连续加载的实测

2026-09-15，1500 部合成库（`scripts/demo_dataset.py`，占位短片、无缩略图），回环 `peach serve --no-auth`，
无头 Chrome 1280×800，每批 60 张，沿 `#loadSentinel` 连续加载；脚本与原始结果在
`attic/evidence/20260915-grid-dom-scale/`。

| 卡片 | DOM 元素 | JS 堆 MB | 帧间隔均值 ms（原样） | 最长帧 ms（原样） | 帧间隔均值 ms（加 `content-visibility: auto`） | 最长帧 ms（同） |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 61 | 3862 | 3.2 | 6.6 | 12.5 | 6.7 | 14.9 |
| 610 | 28306 | 3.8 | 13.2 | 20.3 | 8.4 | 11.5 |
| 915 | 41886 | 4.8 | 30.3 | 42.6 | 11.0 | 13.1 |
| 1525 | 69037 | 6.6 | 47.7 | 59.7 | 18.2 | 24.6 |

帧间隔取往返滚动 30 帧的均值。每张卡片约 45 个元素；堆与强制布局的开销都小，涨的是滚动时的每帧工作量，
原样十批之后就贴近 16.7 ms 的帧预算。对照组只多一条 `#grid article.card{content-visibility:auto;contain-intrinsic-size:auto 320px}`，
DOM 数不变，浏览器跳过视口外卡片的渲染，1500 张时仍在预算附近。真实库的卡片带缩略图与悬停预览，只会更重；
无头 Chrome 没有 GPU 合成，绝对值偏高，趋势成立。
