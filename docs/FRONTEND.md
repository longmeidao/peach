# 前端 island 层

Peach 的界面正在从 `web/app.js`（无构建、一万一千余行的原生 ES module）逐页迁到
React + Tailwind v4 + BoardUI 源码。迁移方式是 strangler：
**遗留路由继续拥有外壳和每一个页面**，一页被重写之后，遗留入口只负责铺骨架、把容器和自己独有的助手交出去。
为什么这么做、以及不做整体重写的理由见 `docs/adr/0031-frontend-react-boardui-tailwind.md`。

只有一条不可变的约束：**运行时没有 Node**。Python 服务、PyInstaller 包和 macOS 上的
检出都直接读 `web/`，所以构建产物提交进 Git，不用任何 CDN。

## 目录与产物

| 路径 | 是什么 |
| --- | --- |
| `frontend/src/islands.ts` | 挂载契约与注册表，构建入口；其余导出是遗留层仍在用的助手 |
| `frontend/src/api.ts` | 带 `AbortController` 的取数封装 |
| `frontend/src/management.ts` | 数据管理首屏 Fieldset、网盘能力显隐与浏览历史导入指南 |
| `frontend/src/legacy/*.d.ts` | `/js/core.js`、`/js/ui-components.js` 的手写类型 |
| `frontend/src/react/` | React 子树：`entry.tsx` 是构建入口，`bundle.d.ts` 是对外契约，`boardui/` 逐字复制 BoardUI 源码 |
| `frontend/src/react/query.ts` | React 子树唯一的 TanStack Query 客户端，页面级 `prefetch` 与组件读的是同一份缓存 |
| `frontend/src/react/components/` | Peach 自己的组合件（说明条、进度、空态、等待点），BoardUI 注册表里没有对应条目的那些 |
| `frontend/test/` | vitest 用例与遗留模块的桩；`test/react/` 直接挂组件，`islands.test.ts` 走挂载契约 |
| `web/dist/peach-ui.js` | 构建产物，**进 Git**，由 `/dist/{name}` 提供 |
| `web/dist/peach-react.js`、`peach-react.css` | React 子树的构建产物，**进 Git** |

首次运行页（未配置时的 `GET /` 与 `POST /setup`）不在这张表里：它是 SPA 外壳之外的一张
独立页面，HTML 与样式都自包含在 `src/peach/routes_pages.py`，只借 `/js/ui-components.js` 的 `attachOverlayScrollbar` 与 `wireCollapse` 画整页滚动条和「高级设置」的折叠，此外不引 `web/` 的资产，也不是
island。原因是那一套一上来就打 `/api/items`，而未配置的机器还没有数据库；它也没有客户端
状态，原生 `<form method="post">` 不写一行 JS 就能工作。设置成功以浏览器 cookie 登录并跳入馆藏。
它的配色 token 从 `web/css/01-base.css` 的 `:root` 两段抽出来，跟随系统深浅色。

配置好之后改文件夹与端口的那张页整个是 React（`frontend/src/react/settings/`，入口
`configuration-page.tsx`）：一条窄列里排「通用 / 媒体 / 网络与访问 / 更新与维护」四组，每组一个
`h2.configgroup` 小标题，没有内容的组连标题一起省略。数据契约是 `/api/configuration`
（`src/peach/routes_configuration.py`），端点字符串只在 `frontend/src/configuration-endpoints.ts`
声明一次，整页和挂载状态那一块读同一个 `queryKey`。
日常入口是右上角的设置弹层：同一个 island 挂进 `#machineSettings`，左栏「这台电脑」
那一块按 `.configgroup` 标题拆成四条（`web/app.js` 的 `configTabItems`）。壳挂完这一页紧接着
就读它画出来的结构，所以第一帧要同步落到 DOM 上：`react/entry.tsx` 的 `mounter` 用 `flushSync`
画第一帧，往后的更新照常异步。小标题和分区因此必须是 `.configpage` 的直接子节点、交替排列。
`/configuration` 这条路由保留，媒体库选单和首次配置引导都指向它。
服务端按两道门放行：托盘管理的服务、发起连接的是本机；并在 `/healthz` 里按调用方回
`configurable`，遗留层据此决定这一块是挂 island 还是换成一句「该配置需在服务端设备修改」。
表单校验的原因由服务端按字段给（400 的 `errors`），页面写回原位，不在前端复制判定。
浏览器直接导航撞上 `HTTPException` 时，`api.py` 的处理器按 `Accept` 回一张 HTML 错误页
（`routes_pages.error_page`），`/api/` 下和非导航请求仍回 JSON。

产物名字不带内容哈希：引用它的 `web/app.js` 不经过构建，构建时改不了那里的路径。
缓存由服务端兜住：`/dist/` 与 `/app.js`、`/app.css`、`/js/` 同一档，回
`Cache-Control: no-cache` 加一个 mtime＋字节数的 ETag——每次都回源问，没变时回 304
零传输，更新语义与 `no-store` 等价。只有 `index.html` 用 `no-store`：所有资产
URL 都从它来，它被缓存住就没人看得到新产物。

## 样式表分区

样式表按界面分区拆在 `web/css/` 下，`/app.css` 把它们按文件名顺序拼成一份交付
（`src/peach/routes_pages.py` 的 `stylesheet_response()`）。拆分只为让两处改动落在不同
文件上——一整份两千七百行的样式表，两个分支各改一处几乎必然撞在一起。页面仍然只取
一份 `/app.css`：不给首屏加二十来个阻塞请求，层叠顺序也不必写进 `index.html`。

两条规则：

- **两位数前缀就是层叠顺序**，`sorted()` 出来的顺序即生效顺序。新增分区要同时改
  `tests/test_web_ui.py` 里 `StylesheetPartitionTests.PARTITIONS`：插在哪一档决定谁覆盖
  谁，那是判断，不该由 glob 顺手发现。
- **切口只许落在花括号深度 0、注释之外**。规则或 `@media` 被切成两半时拼起来仍然完全
  正确，只有单独看每一份才会发现，所以每份分区自己的花括号和注释必须闭合。

| 分区 | 覆盖 |
| --- | --- |
| `01-base.css` | 主题变量、色板、字号、Geist 基元、滚动条 |
| `02-topbar.css` | 顶栏与顶部三层 |
| `03-filterbar.css` | 常驻筛选层、combo、页面提要 |
| `04-manage.css` | 统计页、播单、复核、元数据、数据管理 fieldset |
| `05-insights.css` | Analytics／Speed Insights 与口味页 |
| `06-index.css` | 索引页、标签词表、字母表 |
| `07-entity.css` | 实体资料页头、外链、相关人物 |
| `08-photos.css` | 照片墙与灯箱主体 |
| `09-skeleton.css` | Geist Skeleton 与各页骨架变体 |
| `10-photolight.css` | 灯箱的缩放条、详情、缩略带与窄屏 |
| `11-identity.css` | 身份组、演员与系列链接、重复项、质量清单、复核对照 |
| `12-cards.css` | 主区网格与卡片，含悬停预览、密度、短片带 |
| `13-stage.css` | 就地展开的舞台与 Mix 队列 |
| `14-player.css` | video.js 定制、播放统计、播放器的脱盘占位 |
| `15-detail.css` | 详情侧栏、标签选择器、反馈条、相关推荐 |
| `16-settings.css` | 设置面板 |
| `17-overlay.css` | Toast 与审查遮挡 |
| `18-drawer.css` | 筛选抽屉 |
| `19-immersive.css` | 沉浸模式 |
| `20-offdisk.css` | 脱盘模式 |
| `21-online.css` | 在线追更 |
| `22-followmanage.css` | 关注管理页 |

## 开发循环

```bash
npm --prefix frontend ci        # 首次或改了依赖之后
npm --prefix frontend run dev   # vite build --watch，改完存盘就重建 web/dist
npm --prefix frontend run build # 出一次正式产物，提交前必须跑
```

没有 dev server：`index.html` 归 Python 服务，页面照常从 Peach 自己的端口打开，
watch 模式只负责把产物写回 `web/dist/`。刷新页面就能看到改动。

测试与类型仍然只有一个入口：

```bash
& .\scripts\test.ps1 -Scope web   # Windows；含 tsc、vitest、产物与契约断言
./scripts/test.sh web             # macOS
```

vitest 转译时只剥掉类型、不做检查，所以 `web` 域另跑一遍 `npm --prefix frontend run typecheck`。
两者在本机没有 npm 或没装 `frontend/node_modules` 时**显式跳过**，不会让测试域变红；
CI（`GITHUB_ACTIONS=true`）里缺这些就判失败，由工作流负责装齐。「产物是否由当前源码构建出来」这一条本机验不了（不装 Node 就无法重建），
它的门槛在 CI 的 `web-bundle` job：`npm run build` 之后 `git diff --exit-code -- web/dist`。
**改了 `frontend/src` 就必须重新构建并把 `web/dist/` 一起提交**，否则 CI 会红。

同一个域里还有真浏览器冒烟 `tests/test_web_e2e.py`：它在临时数据根上生成 12 条合成演示库、
起回环 `peach serve --no-auth`，再跑 `npm --prefix frontend run e2e`。用例在
`frontend/e2e/smoke.test.ts`，每条主路由在桌面与 390×844 下先等到目标页面主体出现（路由自己的标题，
加上内容区、索引条目或明确的空态），再断言：无页面异常与 `console.error`、无同源 4xx/5xx 与失败请求、
`aria-busy` 与 `data-skeleton` 会消失、无横向溢出、无越出视口的元素。主体一项不能省：页面完全没渲染时，
其余几条照样全部成立。新增路由要在 `ROUTES` 里写明它的主体。
浏览器取本机 Google Chrome（`PEACH_E2E_CHROME` 可指定），短片由 ffmpeg 编码；缺 npm、
`playwright-core`、ffmpeg 或 Chrome 时本机显式跳过，CI 里判失败。声明根是 Windows 形态，目前只在 Windows 上执行，
CI 由 `web-e2e` job 在 `windows-latest` 上执行 `web` 域，矩阵扩成全量时改由 Windows 全量行覆盖（`docs/TESTING.md`）。界面验收里发现的同类问题，
先在这里补一条用例再修。

设计决定另有 `frontend/e2e/design.test.ts`，读 `getComputedStyle` 断言用户定过的外观：React 输入框不带旧焦点环、
React 子树读到 BoardUI 的 token 原值、持久警示是状态色块、一张卡底下只有写入那一颗是主按钮。页面迁到 React 时，旧的源码字符串断言按 ADR-0031
分三类再删：设计决定进这里或 lint，行为进 vitest，布局与运行期进冒烟。

`npm --prefix frontend run lint` 检查 `src/react/` 的设计系统规则，`web` 域与 CI 都跑。`no-restyle` 报在
BoardUI 组件上的间距或外观，处理办法是在组件外面套一层普通元素，不给规则加例外。
`src/react/boardui/` 只加不改，`UPSTREAM.sha256` 记着复制时每个文件的哈希，由 `tests/test_frontend_build.py` 比对。

## 挂载契约

```js
// web/app.js 里的遗留入口
const ui = await import('/dist/peach-ui.js');
const props = {openItem, javTitleHtml, javDisplayName, srcBadge};
await ui.mountIsland('quality-goals', $('#stats'), props, {isCurrent: () => surfaceCurrent(surface)});
```

- `mountIsland(name, el, props, options?)` 是 async 且**取完数才画**。遗留层已经铺了
  骨架，island 若先画一个空容器再自己转圈，同一次进入就会出现两段等待态。
- `options.isCurrent` 是换页判据。遗留路由用「代」而不是 `AbortSignal` 判当前页
  （`claimSurface`／`surfaceCurrent`），取数期间用户走开时，island 靠这个谓词决定不画。
- `unmountIsland(el)` 中止在途取数，并且只清自己画过的东西：还没画就卸载时容器里
  是遗留骨架，那不属于 island。它连子孙容器一起卸（`el` 自己，加上所有 `el.contains`
  得到的已挂载容器）：壳只对管理区正文那一个容器调它，而「扫描与采集」卡片挂在里面
  更深的一格上（`#libraryProcessing` 在 `#stats` 里），只卸最外层的话，离开这一页之后
  那棵根还活着，照着原节律继续敲库。
- 容器归遗留层所有，它会在别的页面进入时直接 `innerHTML=`，所以 `mountIsland` 每次
  都先自我卸载。
- 注册表里每个名字只记它在 `@peach/react` 的 `pages` 里叫什么。`mountIsland` 动态取回
  `@peach/react`，先 `pages.<page>.prefetch(props, signal)` 把首屏写进共用的 Query 缓存，
  再换掉骨架、在一个 `.peach-react` 容器里创建 React 根；`unmountIsland` 卸根、撤容器。
- 离场有两道闸。第一道是壳：`claimSurface` 是所有页面共同经过的换页点，它在那里对管理区
  正文（`#stats`）和资料页那块（`#index`）调 `unmountIsland`，根连同它的轮询一起停；
  `showHomeSurfaces` 是索引页与资料页重画前的公共点，也卸一次 `#index`。
  多数页面的离场路径是直接 `innerHTML=`，根被挤出文档却照样活着，所以卸载必须由这
  几个公共点负责，而不是逐页判断。第二道是 `isCurrent`：取数落地时用户可能已经走开，
  这时不画。再进这一页时 `mountIsland` 先自我卸载，同时只有一份。

遗留助手不打进产物：`LOC`、`fmtDur`、`fmtSize`、`emptyStateHtml`、`noteHtml` 在浏览器里
仍是 `/js/*.js`，源码用 `@peach/legacy/*` 引用，`output.paths` 在产物里改写回真实路径。
打进去就会有两份实现，语义契约各走一份。只存在于 `app.js` 里的助手
（`javTitleHtml`、`srcBadge`、`openItem` 这类）作为 props 传进来，类型写在 island 自己的文件里。

## 共享状态怎么写

判据只有一条：**这份数据有没有第二个读者**。

没有就用 hooks。展开、悬停、翻到第几页这些东西只属于一页，提上去只是把本来局部的
东西变成全局的。

有第二个读者就让两个读者读**同一个 `queryKey`**，不另建一份状态。整个 React 子树只有
`src/react/query.ts` 那一个 `QueryClient`（`tests/test_frontend_build.py` 盯着），页面级
`prefetch` 写进去的那一份，任何组件的 `useQuery` 都直接读得到，谁先谁后都是同一个数。
现成的例子是扫描与采集那趟后台任务：`/data-cleanup` 上的卡片（容器 `#libraryProcessing`）
要进度、结果和重试，目录页顶上那条横幅（容器 `#libraryProcessingNotice`）只要一句话和一个
去处。两个容器不相邻，各由遗留层自己的时机挂载，读的却是同一个 `LIBRARY_PROCESSING_KEY`：

```tsx
// src/react/library-processing/use-library-processing.ts —— 卡片与横幅都调它
const job = useQuery({
  queryKey: LIBRARY_PROCESSING_KEY,
  queryFn: ({ signal }) => fetchLibraryProcessing(signal),
  refetchInterval: (query) => pollInterval(query.state.data, watching),
});
```

两处同时在场时一个周期只发一趟请求：两个 observer 的定时器在每次查询更新后一起重排，
并发的 `fetch` 由 Query 自己合并。反过来各存一份状态的话，两边的轮询各走各的节律，卡片
说「已完成」、横幅还挂着进度。

高清版目标是同一条判据下还没接上的一处：`/quality-goals` 整页列表要 `items`，
`/data-cleanup` 上的「高清版」卡片只要一个 `total`，而卡片还在 `web/app.js` 里自己发一次
`/api/quality-goals?limit=1`。它随数据管理页迁移时改读 `QUALITY_GOALS_KEY`。
**遗留层里的读者等它所在的页面迁过来再接**，不为它在产物上另开一个通知入口。

端点字符串在 `frontend/src` 里只许出现一次，就在这一页的数据模块里
（`src/react/quality-goals/quality-goals.ts`）——要拦的是「两个地方各写一遍这条 URL」。

首屏要不要吃缓存看路由表：`/quality-goals` 是 `refresh:'reopen'`，刷新就是重新进这一页，
所以它的 `prefetch` 不给 `staleTime`，每次进来都重取。要按节律更新的页面写
`refetchInterval`（活动页 2 秒／10 秒），不另起 `setInterval`：轮询跟着组件走，
换页时壳在 `claimSurface` 卸根，它自己就停了。

## 迁移下一个页面

整页归 React（ADR-0031）。先挑一个**容器不与别人共用**的页面；写操作和后台任务的
写法已经定型，见下面第 2 条。

1. `frontend/src/react/<page>/<page>.ts`：端点常量、`queryKey`、数据类型和纯折算函数，
   外加一个 `prefetch<Page>(signal)`——`queryClient.fetchQuery` 包住 `src/api.ts` 的
   `apiGet`，信号透到真正的 `fetch` 上。同一份真相只用一个 `queryKey`：一屏里的几段要是
   分开取，就会出现这一段是新的、那一段是旧的。节律不同的两份才分键——来源和凭证页的
   来源列表由用户改，抓封面的任务状态由后台推进，合成一个键的话每两秒的一轮轮询都会把
   用户正在填的那张卡重画一遍。
2. `frontend/src/react/<page>/<page>-page.tsx`：组件用 `useQuery` 读同一个 `queryKey`，
   要轮询就写 `refetchInterval`，间隔按上一次拿到的内容算，不另起 `setInterval`。
   写操作是 `useMutation`，不进 Query 的缓存节律：成功后用 `setQueryData` 把服务端回的
   那一条换进列表，而不是把整页重取一遍——用户可能正在填同一屏的另一张卡；失败只在卡内
   留一句原因，缓存里的上一份不动，刚填的内容也不清。同一张卡上互斥的动作共用一个
   `isPending`，进另一个动作前 `reset()` 掉上一个的结果，屏幕上不会同时挂着两次的结论。
   跟后台任务时 `refetchInterval` 按状态开关（`running` 才问），并且**首屏读到的旧结果
   不冒充新结果**：任务关掉页面照样在跑，状态里常年躺着上一趟的回执，只有本次启动过、
   或者本次亲眼见过它在跑，终态才画成结果、发一次 toast。
3. `frontend/src/react/entry.tsx`：在 `pages` 里登记 `{prefetch, mount: mounter(Page)}`，
   签名写进 `bundle.d.ts` 的 `ReactPages`；`frontend/src/islands.ts` 里 `IslandContracts`
   取 bundle 的 props 类型，`REGISTRY` 登记 `{react: '<page>'}`。
4. 外观按 BoardUI：注册表里有的条目逐字复制进 `src/react/boardui/`，哈希记进
   `ORIGIN.md` 与 `UPSTREAM.sha256`；注册表里没有的（分区标题、空态、进度、说明条）
   用 `src/react/components/` 下 Peach 自己的组合件，第二个页面要用就搬进那里，不复制一份。
   `auto-fill` 网格、固定像素的封面这类工具类里没有的档位，在 `styles.css` 里加
   `@theme` 或 `@utility`，类名照常由 Tailwind 生成；lint 不收任意值。
5. `frontend/test/react/<page>.test.tsx`：假 fetch 加 `test/react/render.tsx` 的挂载助手，
   断言结构、请求次数、轮询节律和失败时留下什么，用例之间 `queryClient.clear()`。
   有写操作就再断言交上去的请求体、成功后页面上不再留着秘密输入、失败后输入原样还在；
   有后台任务就用假时钟推到终态，看回执只发一次、卸载之后不再问。
   外观决定进 `frontend/e2e/design.test.ts`：`page.route` 造出真实数据里凑不齐的状态，
   断言读 `getComputedStyle`。
6. `web/app.js` 的挂载块不变；`web/css/` 与 `web/board.css` 里只服务这一页正文的规则删掉，
   遗留骨架还要用的留着——骨架仍然用旧类名（`boardPageSkeleton`），它要的那几条不能一起删。
   遗留层只在 `app.js` 里有的助手（`javTitleHtml`、`srcBadge` 这类返回 HTML 的）继续由
   props 递进来，用 `dangerouslySetInnerHTML` 插；它们是全站语义契约的唯一实现，在页面里
   重写一份就会漂。而 `emptyStateHtml`、`noteHtml`、`collectionSummaryHtml` 这类只是
   「画个通用块」的助手不跟过来：React 页用 `components/` 下的组合件。
7. `tests/test_web_ui.py` 里这一页的断言分三处：路由、菜单入口与骨架留在原地，CSS
   字符串删掉（设计决定改由 `design.test.ts` 读计算值），行为搬进 vitest；搬到哪里写进
   提交说明。
8. 跑 `& .\scripts\test.ps1 -Scope web`（含 tsc、lint、vitest 与真浏览器冒烟），
   再 `npm --prefix frontend run build` 并把 `web/dist/` 一起提交。

遗留骨架与 `web/app.js` 画的那些页继续用 `web/css/` 下的分区，`peach-ui.js` 不出样式表。
React 子树的样式是 Tailwind v4 加 BoardUI 主题，产物 `peach-react.css`；它与旧样式表同处一页的
三条约束（工具类不分层、只扫描 `src/react/`、Preflight 限定在 `.peach-react` 里）写在
`frontend/src/react/styles.css` 开头，逐字复制与没有复制的上游文件见 `frontend/src/react/boardui/ORIGIN.md`。
`.oxlintrc.json` 里两条例外也在那儿定：`configpage`、`configgroup` 是旧样式表的类名，
React 页要按原名输出壳才拆得出分区；`shadow-dropdown` 是 BoardUI 主题里的 `--shadow-*`，
`no-raw-colors` 只认 `--color-*`，把它当成了未声明的颜色。

## 依赖清单

`frontend/package.json` 和根 `package.json` 是两份，各管一件事：根清单只登记手工
vendor 到 `web/vendor/` 的四个包（video.js、swiper、lucide-static、healthicons），
构建依赖不许混进去（`tests/test_dependency_policy.py` 卡着那份清单）。
两份都精确钉版本，lockfile 进 Git。

| 依赖 | 为什么需要它 |
| --- | --- |
| `vite` | 构建入口。库模式出单个 ES module，`external` + `output.paths` 把遗留模块留在外面 |
| `typescript` | 类型即契约：注册表、props 与端点响应都靠它在编译期拦住漂移 |
| `vitest` | 前端测试运行器。与 Vite 共用同一份配置解析，不必再维护第二套转译 |
| `happy-dom` | vitest 的 DOM 环境。断言的是真实 DOM 结构，比 jsdom 轻且启动快 |
| `playwright-core` | `frontend/e2e/` 的浏览器驱动，只驱动本机 Chrome、不下载浏览器。happy-dom 没有布局，横向溢出、等待态卡住这类事实只有真浏览器测得出；不用 `@playwright/test`，用例跑在 `node:test` 上，与 docu.md（`markdown-viewer/markdown-viewer-extension` 的 `test/helpers/browser-render-harness.ts`）同一做法 |
| `oxlint`、`@shadcn/lint` | `npm run lint`：Oxlint 加载 `@shadcn/lint` 的六条规则，只查 `src/react/`、排除 `boardui/`。不用 ESLint，因为 `@typescript-eslint/parser` 的 peer 只到 TypeScript 6.0；`eslint` 作为 `@shadcn/lint` 的 peer 会装进来，不调用 |
| `react`、`react-dom` | 前端唯一的渲染层。BoardUI 源码是 React 组件，交互建在 React Aria 上；不经兼容层运行它（ADR-0031）。`react-dom` 的 `flushSync` 还负责配置页那一帧：壳挂完紧接着就读 DOM |
| `react-aria-components` | BoardUI 输入框、勾选框、开关、下拉与弹出面板的交互和无障碍语义：标签关联、键盘操作、焦点进出、`aria-invalid` |
| `react-aria` | 只用 `UNSAFE_PortalProvider`：把 Popover 与下拉列表挂进 `body` 末尾同样带 `.peach-react` 的容器，弹层读到与页面内一致的 token 与 Preflight |
| `@tanstack/react-query` | React 页面的取数与缓存：页面级 `prefetch` 与组件里的 `useQuery` 共用一份缓存，「取完数才画」不必把首屏数据当 props 串一路；轮询写成 `refetchInterval`，卸载时跟着组件一起停 |
| `tailwind-merge` | BoardUI 的 `cx()` 合并类名时去掉互相冲突的工具类 |
| `@remixicon/react` | BoardUI 组件内置的图标 |
| `tailwindcss`、`@tailwindcss/vite` | 按 `src/react/` 里实际用到的类名生成 `peach-react.css` |
| `@types/react`、`@types/react-dom` | React 子树的类型检查 |

React 子树单独构建（`vite.react.config.ts`）。`peach-react.js` 774.5 kB（gzip 200.7 kB），
只在页面挂 React 子树时由 island 动态加载；`peach-react.css` 87.5 kB（gzip 13.7 kB），
由 `index.html` 在旧样式表之前引入。`peach-ui.js` 85.6 kB（gzip 26.6 kB），只剩挂载契约与
遗留层的助手。`build.cssTarget` 对齐 Tailwind v4 的浏览器基线
（Chrome 111、Firefox 128、Safari 16.4），oklch 颜色原样输出：目标再旧，lightningcss 会补
`lab()` 回退，末位小数随平台浮点不同，CI 在 Linux 上重建的产物就与提交的对不上。

没有引入 `@testing-library/react`：`createRoot` 加 `querySelector` 已经够用
（挂载与输入的助手在 `frontend/test/react/render.tsx`），断言的本来就是真实 DOM。
