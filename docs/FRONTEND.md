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
| `frontend/src/api.ts` | 带 `AbortController` 的取数封装 |
| `frontend/src/legacy/*.d.ts` | `/js/core.js`、`/js/ui-components.js` 的手写类型 |
| `frontend/test/` | vitest 用例与遗留模块的桩 |
| `web/dist/peach-ui.js` | 构建产物，**进 Git**，由 `/dist/{name}` 提供 |

产物名字不带内容哈希：引用它的 `web/app.js` 不经过构建，构建时改不了那里的路径。
缓存由服务端的 `Cache-Control: no-store` 兜住，和 `index.html`／`app.js` 同一口径。

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

## 迁移下一个页面

先挑一个**数据来自单个 `/api/...` GET、容器不与别人共用、没有写操作和轮询**的页面。

1. `frontend/src/islands/<page>.tsx`：导出数据类型、props 类型、端点常量、`load<Page>()`
   和组件。组件只接 `{...props, data, error}`，不自己取数。
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
| `vite` | 构建入口。库模式出单个 ES module，`external` + `output.paths` 把遗留模块留在外面 |
| `typescript` | 类型即契约：注册表、props 与端点响应都靠它在编译期拦住漂移 |
| `vitest` | 前端测试运行器。与 Vite 共用同一份配置解析，不必再维护第二套转译 |
| `happy-dom` | vitest 的 DOM 环境。断言的是真实 DOM 结构，比 jsdom 轻且启动快 |

**`@preact/signals` 本轮没有装。** ADR-0022 把它写进技术栈，同一份决策里也写了
「直接依赖数量要最小，每个依赖登记一句用途」。第一个迁过去的页面是只读单 GET，
组件之间没有共享状态，装进来会是一个没有使用者的依赖——它是**被认可的状态原语，
但要跟着第一个真需要它的页面进来**（追更、复核、批处理面板这类同时有写入和轮询的
页面），届时在这张表里补一行用途。同理没有引入 `@testing-library/preact`：`preact`
的 `render` 加 `querySelector` 已经够用，断言的本来就是真实 DOM。
