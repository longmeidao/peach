/* island 挂载契约（ADR-0031）。
 *
 * 遗留路由（`web/app.js`）仍然拥有整个外壳和每一个页面。一个页面被重写成 React
 * 之后，它的入口只做两件事：铺好加载占位，然后把一个容器交给这里。
 *
 *     const ui = await import('/dist/peach-ui.js');
 *     await ui.mountIsland('configuration', $('#stats'), props);
 *
 * `mountIsland` 是 async 且**取完数才画**：遗留层已经铺了骨架，island 若先画一个空
 * 容器再自己转圈，同一次进入就会出现两段等待态（`peach-web-ui` 明确禁止）。所以这里
 * 先 await 页面自己的 `prefetch`，再一次性换掉骨架。
 *
 * 容器由遗留层拥有：它会在别的页面进入时直接 `innerHTML=`。因此 `mountIsland` 每次
 * 都先自我卸载，`unmountIsland` 也不假设 DOM 还在原处。 */
export { preferredDirection } from './sort-preferences';
export { boundedPreference, mountNumberSetting, syncNumberSetting } from './number-setting';
export { initBoardControls, syncBoardRange } from './board-controls';
export { sidebarSectionHtml, wireSidebarGroups, transitionTheme } from './sidebar-groups';

import type * as ReactBundle from '@peach/react';

export { watchJob, followJobProgress, jobActivityHtml } from './jobs';
export { selectRange, selectionSummary, selectGroup, syncSelectionToolbar } from './selection';
export { paginationHtml, pageCount, clampPage } from './pagination';
export { nativeImageFit, matchesFaceSource, faceSourceScale } from './native-image';
export { entitySkeletonHtml } from './entity-skeleton';
export { boardPageSkeleton, detailSkeletonHtml } from './board-skeleton';
export { catalogSuggestions, catalogEmptyHtml, emptyCatalogLayout } from './catalog-onboarding';
export { syncSidebarSurface, sidebarTagCounts, sidebarHasCatalogContent } from './sidebar';
export { cleanupSkeletonHtml, cloudLocations, cloudPreferenceLocations } from './management';
export { resourceScanHtml } from './resource-sync';

/** 每个 island 的 props。新增 island 时在这里登记，注册表随之要求实现；
 *  页面自己管数据，首屏落在共用的 Query 缓存里。 */
export interface IslandContracts {
  'avatar-picker': ReactBundle.AvatarPickerProps;
  'cover-crop': ReactBundle.CoverCropProps;
  'follow-manage': ReactBundle.FollowManageProps;
  'library-processing': ReactBundle.LibraryProcessingProps;
  'scraping': ReactBundle.ScrapingProps;
  'quality-goals': ReactBundle.QualityGoalsProps;
  review: ReactBundle.ReviewProps;
  configuration: ReactBundle.ConfigurationProps;
  activity: ReactBundle.ActivityProps;
  stats: ReactBundle.StatsProps;
  taste: ReactBundle.TasteProps;
}

export type IslandName = keyof IslandContracts;
type PropsOf<N extends IslandName> = IslandContracts[N];

/** 整页在 `@peach/react` 的 `pages` 里，这里只记它的名字（ADR-0031）：先 `prefetch`
 *  把首屏取回来，再换掉遗留骨架、创建 React 根。 */
interface Island {
  react: keyof ReactBundle.ReactPages;
}

const REGISTRY: { [N in IslandName]: Island } = {
  'avatar-picker': { react: 'avatar-picker' },
  'cover-crop': { react: 'cover-crop' },
  'follow-manage': { react: 'follow-manage' },
  'library-processing': { react: 'library-processing' },
  'scraping': { react: 'scraping' },
  'quality-goals': { react: 'quality-goals' },
  review: { react: 'review' },
  configuration: { react: 'configuration' },
  activity: { react: 'activity' },
  stats: { react: 'stats' },
  taste: { react: 'taste' },
};

/** 已注册的 island 名字。遗留层与测试用它核对路由表，不必知道注册表结构。 */
export const islandNames = (): IslandName[] => Object.keys(REGISTRY) as IslandName[];

interface Mount {
  controller: AbortController;
  /** 画过之后，卸载那棵根并撤掉它的容器。还没画过的容器里是遗留骨架，不归 island 清。 */
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
  const island = REGISTRY[name] as Island | undefined;
  if (!island) throw new Error(`未注册的 island：${String(name)}`);
  unmountIsland(el);
  const mount: Mount = { controller: new AbortController() };
  mounted.set(el, mount);
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

/** 取数回来之后还能不能画：期间没有被重挂，遗留层也还停在这一页。能画就顺手清掉遗留骨架。 */
function claimContainer(el: Element, mount: Mount, options: MountOptions): boolean {
  // 期间被卸载或重新挂载：这一次的结果已经过期，不许往新内容上盖。
  if (mounted.get(el) !== mount) return false;
  // 遗留层已经换了页面：容器现在归别人，画上去就是把别的页面盖掉。
  if (options.isCurrent && !options.isCurrent()) {
    mounted.delete(el);
    return false;
  }
  // 遗留骨架整个清掉再画，一次替换，只有一次布局变化。
  el.textContent = '';
  return true;
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
  mount.dispose?.();
}

export { javImageKind, normalizeJavImage, normalizeJavLayout, normalizeJavPreferences, panelFrame, syncJavImages } from './jav-artwork';
