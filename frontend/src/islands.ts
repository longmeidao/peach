/* island 挂载契约（ADR-0022）。
 *
 * 遗留路由（`web/app.js`）仍然拥有整个外壳和每一个页面。一个页面被重写成 Preact
 * 之后，它的入口只做两件事：铺好加载占位，然后把一个容器交给这里。
 *
 *     const ui = await import('/dist/peach-ui.js');
 *     await ui.mountIsland('quality-goals', $('#stats'), props);
 *
 * `mountIsland` 是 async 且**取完数才画**：遗留层已经铺了骨架，island 若先画一个空
 * 容器再自己转圈，同一次进入就会出现两段等待态（`peach-web-ui` 明确禁止）。所以这里
 * 先 await `load()`，再一次性换掉骨架。
 *
 * 容器由遗留层拥有：它会在别的页面进入时直接 `innerHTML=`。因此 `mountIsland` 每次
 * 都先自我卸载，`unmountIsland` 也不假设 DOM 还在原处。 */
import { h, render } from 'preact';
import type { ComponentType } from 'preact';

import { errorMessage } from './api';
import { QualityGoals, loadQualityGoals } from './islands/quality-goals';
import type { QualityGoalsProps } from './islands/quality-goals';
import type { QualityGoalsData } from './state/quality-goals';

/* 跨岛共享状态的入口一起从这里出去。遗留层拿到的是一个 bundle，它有两种用法：
 * `mountIsland` 挂一屏，`refreshStore` 告诉已经挂着的那屏「数据变了」。
 * 怎么写一个 store 见 `./state/index.ts` 和 `docs/FRONTEND.md`。 */
export { refreshStore, storeNames } from './state';
export { watchJob, followJobProgress } from './jobs';
export { syncSidebarSurface, sidebarTagCounts, sidebarHasCatalogContent } from './sidebar';
export type { StoreName } from './state';

/** 首屏取数的结果。`data` 与 `error` 恰有一个成立。 */
export interface IslandState<D> {
  data: D | null;
  error: string;
}

/** 每个 island 的 props 与首屏数据类型。新增 island 时在这里登记，注册表随之要求实现。 */
export interface IslandContracts {
  'quality-goals': { props: QualityGoalsProps; data: QualityGoalsData };
}

export type IslandName = keyof IslandContracts;
type PropsOf<N extends IslandName> = IslandContracts[N]['props'];
type DataOf<N extends IslandName> = IslandContracts[N]['data'];

interface IslandDefinition<N extends IslandName> {
  /** 首屏取数。中止后抛 `AbortError`，`mountIsland` 会静默放弃。 */
  load(props: PropsOf<N>, signal: AbortSignal): Promise<DataOf<N>>;
  component: ComponentType<PropsOf<N> & IslandState<DataOf<N>>>;
}

const REGISTRY: { [N in IslandName]: IslandDefinition<N> } = {
  'quality-goals': { load: loadQualityGoals, component: QualityGoals },
};

/** 已注册的 island 名字。遗留层与测试用它核对路由表，不必知道注册表结构。 */
export const islandNames = (): IslandName[] => Object.keys(REGISTRY) as IslandName[];

interface Mount {
  controller: AbortController;
  /** 是否已经真的画过。没画过就不许 `render(null, el)`：那会连遗留骨架一起清掉。 */
  painted: boolean;
}

const mounted = new Map<Element, Mount>();

/** 遗留层的换页判据。它的路由是「代」而不是 AbortSignal，所以这里收一个谓词：
 *  取数期间用户走开了，island 不能把数据画到别的页面上。 */
export interface MountOptions {
  isCurrent?: () => boolean;
}

/** 挂载一个 island 并等首屏数据落地。容器里原有的内容（遗留骨架）在这一刻被换掉。 */
export async function mountIsland<N extends IslandName>(
  name: N,
  el: Element,
  props: PropsOf<N>,
  options: MountOptions = {},
): Promise<void> {
  const island = REGISTRY[name] as IslandDefinition<N> | undefined;
  if (!island) throw new Error(`未注册的 island：${String(name)}`);
  unmountIsland(el);
  const mount: Mount = { controller: new AbortController(), painted: false };
  mounted.set(el, mount);
  let state: IslandState<DataOf<N>>;
  try {
    state = { data: await island.load(props, mount.controller.signal), error: '' };
  } catch (cause) {
    if (mount.controller.signal.aborted) return;
    state = { data: null, error: errorMessage(cause) };
  }
  // 期间被卸载或重新挂载：这一次的结果已经过期，不许往新内容上盖。
  if (mounted.get(el) !== mount) return;
  // 遗留层已经换了页面：容器现在归别人，画上去就是把别的页面盖掉。
  if (options.isCurrent && !options.isCurrent()) {
    mounted.delete(el);
    return;
  }
  // 遗留骨架不是 Preact 画的，交给 diff 会按标签复用节点、留下 data-skeleton 之类的
  // 旧属性。整个清掉再画，一次替换，只有一次布局变化。
  el.textContent = '';
  mount.painted = true;
  render(h(island.component, { ...props, ...state }), el);
}

/** 卸载容器上的 island：中止在途取数并清空自己画过的内容。没挂过的容器是空操作。 */
export function unmountIsland(el: Element): void {
  const mount = mounted.get(el);
  if (!mount) return;
  mount.controller.abort();
  mounted.delete(el);
  // 只清自己画过的东西。还在取数时容器里是遗留骨架，那不属于 island。
  if (mount.painted) render(null, el);
}
