/* island 挂载契约（ADR-0022）。
 *
 * 遗留路由（`web/app.js`）仍然拥有整个外壳和每一个页面。一个页面被重写成 Preact
 * 之后，它的入口只做两件事：铺好加载占位，然后把一个容器交给这里。
 *
 *     const ui = await import('/dist/peach-ui.js');
 *     await ui.mountIsland('configuration', $('#stats'), props);
 *
 * `mountIsland` 是 async 且**取完数才画**：遗留层已经铺了骨架，island 若先画一个空
 * 容器再自己转圈，同一次进入就会出现两段等待态（`peach-web-ui` 明确禁止）。所以这里
 * 先 await `load()`，再一次性换掉骨架。
 *
 * 容器由遗留层拥有：它会在别的页面进入时直接 `innerHTML=`。因此 `mountIsland` 每次
 * 都先自我卸载，`unmountIsland` 也不假设 DOM 还在原处。 */
import { h, render } from 'preact';
export { preferredDirection } from './sort-preferences';
export { boundedPreference, mountNumberSetting, syncNumberSetting } from './number-setting';
export { statCardBody, rankedChart, radarChart, distributionChart, jobProgressHtml } from './board-metrics';
export { initBoardControls, syncBoardRange, wireExpandableRanks, wireGrowingCharts } from './board-controls';
export { creatorSankeyHtml, wireCreatorSankey } from './board-sankey';
export { radialCardHtml, wireRadialCards, activityChartsHtml, wireActivityCharts } from './board-analytics';
export { sidebarSectionHtml, wireSidebarGroups, transitionTheme } from './sidebar-groups';
import type { Attributes, ComponentType } from 'preact';

import { errorMessage } from './api';
import { Configuration, loadConfiguration } from './islands/configuration';
import type { ConfigurationData, ConfigurationProps } from './islands/configuration';
import type * as ReactBundle from '@peach/react';

export { watchJob, followJobProgress, jobActivityHtml } from './jobs';
export { identityEvidenceHtml, reviewImageHtml, wireReviewPictures } from './review-evidence';
export { createReviewSelection, wireReviewSelection, updateReviewSticky, groupReviewRows } from './review-bulk';
export { selectRange, selectionSummary, selectGroup, syncSelectionToolbar } from './selection';
export { paginationHtml, pageCount, clampPage } from './pagination';
export { nativeImageFit, matchesFaceSource } from './native-image';
export { mountAvatarPicker, unmountAvatarPicker } from './avatar-picker';
export { entitySkeletonHtml } from './entity-skeleton';
export { boardPageSkeleton, detailSkeletonHtml } from './board-skeleton';
export { catalogSuggestions, catalogEmptyHtml, emptyCatalogLayout } from './catalog-onboarding';
export { syncSidebarSurface, sidebarTagCounts, sidebarHasCatalogContent } from './sidebar';
export { cleanupSkeletonHtml, cloudLocations, cloudPreferenceLocations, tasteHistoryGuideHtml, wireTasteHistoryGuide, TASTE_GUIDE_KEY } from './management';
export { resourceScanHtml } from './resource-sync';

/** 首屏取数的结果。`data` 与 `error` 恰有一个成立。 */
export interface IslandState<D> {
  data: D | null;
  error: string;
}

/** 每个 island 的 props 与首屏数据类型。新增 island 时在这里登记，注册表随之要求实现。
 *  React 档的页面自己管数据（首屏落在共用的 Query 缓存里），`data` 写成 `null`。 */
export interface IslandContracts {
  'library-processing': { props: ReactBundle.LibraryProcessingProps; data: null };
  'scraping': { props: ReactBundle.ScrapingProps; data: null };
  'quality-goals': { props: ReactBundle.QualityGoalsProps; data: null };
  configuration: { props: ConfigurationProps; data: ConfigurationData };
  activity: { props: ReactBundle.ActivityProps; data: null };
}

export type IslandName = keyof IslandContracts;
type PropsOf<N extends IslandName> = IslandContracts[N]['props'];
type DataOf<N extends IslandName> = IslandContracts[N]['data'];

/** Preact 档：这里取数、这里渲染。 */
interface PreactIsland<N extends IslandName> {
  /** 首屏取数。中止后抛 `AbortError`，`mountIsland` 会静默放弃。 */
  load(props: PropsOf<N>, signal: AbortSignal): Promise<DataOf<N>>;
  component: ComponentType<PropsOf<N> & IslandState<DataOf<N>>>;
}

/** React 档：整页在 `@peach/react` 的 `pages` 里，这里只记它的名字（ADR-0031）。
 *
 *  两侧的契约是同一条：先 `prefetch` 把首屏取回来，再换掉遗留骨架、创建 React 根。 */
interface ReactIsland {
  react: keyof ReactBundle.ReactPages;
}

type IslandDefinition<N extends IslandName> = PreactIsland<N> | ReactIsland;

const REGISTRY: { [N in IslandName]: IslandDefinition<N> } = {
  'library-processing': { react: 'library-processing' },
  'scraping': { react: 'scraping' },
  'quality-goals': { react: 'quality-goals' },
  configuration: { load: loadConfiguration, component: Configuration },
  activity: { react: 'activity' },
};

/** 已注册的 island 名字。遗留层与测试用它核对路由表，不必知道注册表结构。 */
export const islandNames = (): IslandName[] => Object.keys(REGISTRY) as IslandName[];

interface Mount {
  controller: AbortController;
  /** 是否已经真的画过。没画过就不许 `render(null, el)`：那会连遗留骨架一起清掉。 */
  painted: boolean;
  /** React 档画过之后，卸载那棵根并撤掉它的容器。Preact 档没有。 */
  dispose?: () => void;
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
  if ('react' in island) return mountReactPage(island, el, props, mount, options);
  let state: IslandState<DataOf<N>>;
  try {
    state = { data: await island.load(props, mount.controller.signal), error: '' };
  } catch (cause) {
    if (mount.controller.signal.aborted) return;
    state = { data: null, error: errorMessage(cause) };
  }
  if (!claimContainer(el, mount, options)) return;
  // 注册表有多个 island 之后 `PropsOf<N>` 是按名字分发的索引类型，TS 推不出它与
  // `Attributes` 相交仍是同一个对象，这里把结论写给它。
  const attrs = { ...props, ...state } as Attributes & PropsOf<N> & IslandState<DataOf<N>>;
  render(h(island.component, attrs), el);
}

/** 取数回来之后还能不能画：期间没有被重挂，遗留层也还停在这一页。能画就顺手清掉遗留骨架。 */
function claimContainer(el: Element, mount: Mount, options: MountOptions): boolean {
  // 期间被卸载或重新挂载：这一次的结果已经过期，不许往新内容上盖。
  if (mounted.get(el) !== mount) return false;
  // 遗留层已经换了页面：容器现在归别人，画上去就是把别的页面盖掉。
  if (options.isCurrent && !options.isCurrent()) {
    mounted.delete(el);
    return false;
  }
  // 遗留骨架不是 Preact 画的，交给 diff 会按标签复用节点、留下 data-skeleton 之类的
  // 旧属性。整个清掉再画，一次替换，只有一次布局变化。
  el.textContent = '';
  mount.painted = true;
  return true;
}

/** React 档：动态取回 React 产物，先把首屏落进共用的 Query 缓存，再换掉骨架、创建根。 */
async function mountReactPage<N extends IslandName>(
  island: ReactIsland, el: Element, props: PropsOf<N>, mount: Mount, options: MountOptions,
): Promise<void> {
  const bundle = await import('@peach/react');
  const page = bundle.pages[island.react] as ReactBundle.ReactPage<PropsOf<N>>;
  try {
    await page.prefetch(props, mount.controller.signal);
  } catch {
    // 中止就是用户已经走开，这一次不画。其余失败照画：原因和重试的节律都在页面自己手里，
    // 它从 Query 缓存里读到的就是这次的错误。
    if (mount.controller.signal.aborted) return;
  }
  if (!claimContainer(el, mount, options)) return;
  // token、Preflight 与焦点规则都作用在 `.peach-react` 上，React 根要挂在带这个类的容器里。
  // 容器本身归遗留层所有（它会直接 `innerHTML=`），所以另建一个，卸载时连它一起撤掉。
  const host = el.ownerDocument.createElement('div');
  host.className = 'peach-react';
  el.append(host);
  const root = page.mount(host, props);
  mount.dispose = () => { root.unmount(); host.remove() };
}

/** 这个容器上是不是已经挂着一个 island。
 *
 *  遗留层据此判断要不要重挂。`mountIsland` 开头就把容器卸干净，而卸载会把画过的
 *  内容清掉：内容根本没变时，那一下只是一次白白的布局塌陷。 */
export const islandMounted = (el: Element | null): boolean => !!el && mounted.has(el);

/** 卸载容器上的 island：中止在途取数并清空自己画过的内容。没挂过的容器是空操作。
 *
 *  连子孙容器一起卸。遗留壳在 `claimSurface` 只对管理区正文那一个容器（`#stats`）调它，
 *  而卡片挂在里面更深的一格上（`#libraryProcessing` 在 `#stats` 里）：只卸最外层的话，
 *  离开这一页之后那棵根还活着，照着原节律继续敲库。 */
export function unmountIsland(el: Element): void {
  for (const container of [...mounted.keys()]) {
    if (container === el || el.contains(container)) disposeIsland(container);
  }
}

function disposeIsland(el: Element): void {
  const mount = mounted.get(el);
  if (!mount) return;
  mount.controller.abort();
  mounted.delete(el);
  // 只清自己画过的东西。还在取数时容器里是遗留骨架，那不属于 island。
  if (mount.dispose) mount.dispose();
  else if (mount.painted) render(null, el);
}

export { javImageKind, normalizeJavImage, normalizeJavLayout, normalizeJavPreferences, panelFrame, syncJavImages } from './jav-artwork';
