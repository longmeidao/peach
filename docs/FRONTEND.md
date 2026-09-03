# 前端 island 层

Peach 的界面正在从 `web/app.js`（无构建、6.7k 行的原生 ES module）逐页迁到
Vite + TypeScript + Preact。迁移方式是 strangler：**遗留路由继续拥有外壳和每一个页面**，
一页被重写成 island 之后，遗留入口只负责铺骨架、把容器和自己独有的助手交出去。
为什么这么做、以及不做整体重写的理由见 `docs/adr/0022-frontend-vite-preact-strangler.md`。

只有一条不可变的约束：**运行时没有 Node**。Python 服务、PyInstaller 包和 macOS 上的
检出都直接读 `web/`，所以构建产物提交进 Git，不用任何 CDN。

## 目录与产物

| 路径 | 是什么 |
| --- | --- |
| `frontend/src/islands.ts` | 挂载契约与注册表，构建入口 |
| `frontend/src/islands/*.tsx` | 每个 island 一个文件 |
| `frontend/src/state/*.ts` | 跨岛共享状态，一份数据一个文件；`index.ts` 是登记处 |
| `frontend/src/api.ts` | 带 `AbortController` 的取数封装 |
| `frontend/src/legacy/*.d.ts` | `/js/core.js`、`/js/ui-components.js` 的手写类型 |
| `frontend/test/` | vitest 用例与遗留模块的桩 |
| `web/dist/peach-ui.js` | 构建产物，**进 Git**，由 `/dist/{name}` 提供 |

产物名字不带内容哈希：引用它的 `web/app.js` 不经过构建，构建时改不了那里的路径。
缓存由服务端兜住：`/dist/` 与 `/app.js`、`/app.css`、`/js/` 同一档，回
`Cache-Control: no-cache` 加一个 mtime＋字节数的 ETag——每次都回源问，没变时回 304
零传输，更新语义和以前的 `no-store` 相同。只有 `index.html` 仍是 `no-store`：所有资产
URL 都从它来，它被缓存住就没人看得到新产物。

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
& .\scripts\test.ps1 -Scope web   # Windows；含 vitest、产物与契约断言
./scripts/test.sh web             # macOS
npm --prefix frontend run typecheck
```

`web` 域里的 vitest 在没有 npm 或没装 `frontend/node_modules` 时**显式跳过**，不会让
测试域变红。「产物是否由当前源码构建出来」这一条本机验不了（不装 Node 就无法重建），
它的门槛在 CI 的 `web-bundle` job：`npm run build` 之后 `git diff --exit-code -- web/dist`。
**改了 `frontend/src` 就必须重新构建并把 `web/dist/` 一起提交**，否则 CI 会红。

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
  是遗留骨架，那不属于 island。
- 容器归遗留层所有，它会在别的页面进入时直接 `innerHTML=`，所以 `mountIsland` 每次
  都先自我卸载。
- 现状：遗留外壳**还没有**在换页时调 `unmountIsland`——它的离场路径是直接
  `innerHTML=`，没有统一的钩子。所以离场靠 `isCurrent` 保证不误画，在途请求要等自然
  结束。把 `unmountIsland` 接进壳的换页路径属于路由本体迁移那一步，不在单页迁移里做。

遗留助手不打进产物：`LOC`、`fmtDur`、`fmtSize`、`emptyStateHtml`、`noteHtml` 在浏览器里
仍是 `/js/*.js`，源码用 `@peach/legacy/*` 引用，`output.paths` 在产物里改写回真实路径。
打进去就会有两份实现，语义契约各走一份。只存在于 `app.js` 里的助手
（`javTitleHtml`、`srcBadge`、`openItem` 这类）作为 props 传进来，类型写在 island 自己的文件里。

## 共享状态怎么写

判据只有一条：**这份数据有没有第二个读者**。

没有就用 hooks。展开、悬停、翻到第几页这些东西只属于一个岛，搬进 store 只是把本来
局部的东西变成全局的。第一份 store 之所以存在，是因为高清版目标确实有两个读者：
`/quality-goals` 整页列表要 `items`，`/data-cleanup` 上的「高清版」卡片只要一个
`total`，为此另发了一次 `/api/quality-goals?limit=1`——同一个真相取两次，显示的数
就可能对不上。

有第二个读者就在 `frontend/src/state/` 建一个文件，规矩三条：

1. **一份数据一个文件**，文件名就是它的名字，再在 `state/index.ts` 里登记。
2. **只导出 `computed` 视图，不导出可写的 signal。** 写入只能通过该文件导出的函数，
   所以「谁改了它」在源码里数得出来；组件里直接赋值会抛 TypeError，不是靠约定。
3. **取数归 store。** `ensureX()` 是「读一次就够」，已有数据直接给、并发调用合流成
   一个请求；`refreshX(signal?)` 是「重新取」，页面刷新和写完数据之后走它。

```ts
// frontend/src/state/quality-goals.ts
const state = signal<QualityGoalsState>(BLANK);        // 不导出
export const qualityGoals = computed(() => state.value);
export const qualityGoalsTotal = computed(() => state.value.data?.total ?? null);
export async function refreshQualityGoals(abort?: AbortSignal) { /* 写 state.value */ }
export async function ensureQualityGoals() { /* 有就给，没有才 refresh */ }
```

岛这边只是读：组件里读 `qualityGoals.value` 就自动订阅，数据之后再变这一屏自己重画，
不需要重新 `mountIsland`。卸载时订阅跟着组件一起走（`test/islands.test.ts` 里有一条
mount → unmount → 改 signal 的用例盯着这件事）。`mountIsland` 仍然会把 `{data, error}`
作为 props 传进来——那是所有 island 共用的首屏契约——由 store 支撑的岛不看它们：
同一份数据两个来源，刷新之后就会各说一套。

首屏该用哪个函数看路由表：`/quality-goals` 是 `refresh:'reopen'`，刷新就是重新进这一页，
所以它的 `load` 走 `refreshQualityGoals`，不吃缓存。

**遗留层改完数据怎么通知岛**：产物上多导出一个 `refreshStore(name)`，用法和
`mountIsland(name, ...)` 一样按名字来。

```js
const ui = await import('/dist/peach-ui.js');
await ui.refreshStore('quality-goals');   // 挂着的那屏自己重画，不必重新挂载
```

它取数失败时不抛，只返回 `false`：失败已经落进 store 的错误态、显示在屏幕上了，而
调用点在 `app.js` 里是 fire-and-forget，再抛一次只会变成没人接的 rejection。名字不在
注册表里则立刻抛错——那是写错了，不是运行时状况。目前 `web/app.js` 还没有调用
它——`/data-cleanup` 那张卡片接进来属于下一批迁移，本轮只把入口备好。

## 迁移下一个页面

先挑一个**数据来自单个 `/api/...` GET、容器不与别人共用、没有写操作和轮询**的页面。

1. `frontend/src/islands/<page>.tsx`：导出数据类型、props 类型、端点常量、`load<Page>()`
   和组件。组件只接 `{...props, data, error}`，不自己取数。这份数据要是还有第二个
   读者，就按上一节把数据类型、端点和取数一起搬进 `frontend/src/state/<page>.ts`，
   island 这边只剩 props、`load` 和组件。
2. `frontend/src/islands.ts`：在 `IslandContracts` 里登记类型，在 `REGISTRY` 里登记
   `{load, component}`。类型不登记会直接编译不过。
3. `frontend/test/<page>.test.tsx`：用假 fetch 断言读数口径、空态、失败态与交互。
   遗留模块在测试里走 `frontend/test/stubs/`（只在 `vitest.config.ts` 里 alias，
   不影响构建）。
4. `web/app.js`：把原来的渲染函数体换成上面那段挂载块，保留 `enterManagementSurface()`
   与 `showManagementBody({placeholder:...})`，删掉只服务它的模块级状态。
5. `tests/test_web_ui.py`：原来对那段渲染源的断言改成断言挂载契约；搬走的语义契约
   （中间省略、空态、标签文案）在 `tests/test_frontend_build.py` 的
   `IslandSourceContractTests` 里补回来，不能让它无声消失。
6. 按顺序跑 `npm --prefix frontend run typecheck`、`& .\scripts\test.ps1 -Scope web`，
   再 `npm --prefix frontend run build` 并把 `web/dist/` 一起提交。

样式暂时继续用 `web/app.css`：已迁的页面复用原有的类名，产物这一轮不出 `peach-ui.css`。
`/dist/{name}` 已经允许 `.css`，等某个 island 真的需要自己的样式时再开。

## 依赖清单

`frontend/package.json` 和根 `package.json` 是两份，各管一件事：根清单只登记手工
vendor 到 `web/vendor/` 的四个包（video.js、swiper、lucide-static、healthicons），
构建依赖不许混进去（`tests/test_dependency_policy.py` 卡着那份清单）。
两份都精确钉版本，lockfile 进 Git。

| 依赖 | 为什么需要它 |
| --- | --- |
| `preact` | island 的渲染层。10 kB gzip 的运行时，配 `dangerouslySetInnerHTML` 能直接复用遗留层返回 HTML 的助手 |
| `@preact/signals` | 跨岛共享状态的载体。组件读 `.value` 就订阅，数据变了只重画读它的那一屏，不用把状态提到某个共同祖先——岛之间没有共同祖先 |
| `vite` | 构建入口。库模式出单个 ES module，`external` + `output.paths` 把遗留模块留在外面 |
| `typescript` | 类型即契约：注册表、props 与端点响应都靠它在编译期拦住漂移 |
| `vitest` | 前端测试运行器。与 Vite 共用同一份配置解析，不必再维护第二套转译 |
| `happy-dom` | vitest 的 DOM 环境。断言的是真实 DOM 结构，比 jsdom 轻且启动快 |

`@preact/signals` 钉在 2.11.1：它对 `preact` 的 peer 要求是 `>= 10.25.0`，和这里的
10.29.8 对得上；运行时另外带一个 `@preact/signals-core`，是它自己的依赖，由 lockfile
钉住，不进清单。产物因此从 17.7 kB 涨到 31.5 kB（gzip 6.6 → 10.6 kB）：多出来的是
`signals` + `signals-core` + `preact/hooks` 三份，最后一份以前不在包里——在这之前
没有任何一个岛用过 hooks。

没有引入 `@testing-library/preact`：`preact` 的 `render` 加 `querySelector` 已经够用，
断言的本来就是真实 DOM。
