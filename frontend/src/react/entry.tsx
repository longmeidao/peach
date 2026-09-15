/* React 子树的构建入口（`web/dist/peach-react.js`），按 `bundle.d.ts` 的签名导出挂载函数。 */
import './styles.css';

import type { ComponentType } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { UNSAFE_PortalProvider } from 'react-aria';
import { createRoot } from 'react-dom/client';

import { ActivityPage } from './activity/activity-page';
import { prefetchTasks } from './activity/tasks';
import type * as Bundle from './bundle';
import { prefetchLibraryProcessing } from './library-processing/library-processing';
import { LibraryProcessingCard } from './library-processing/library-processing-card';
import { LibraryProcessingNotice } from './library-processing/library-processing-notice';
import { QualityGoalsPage } from './quality-goals/quality-goals-page';
import { prefetchQualityGoals } from './quality-goals/quality-goals';
import { queryClient } from './query';
import { ScrapingPage } from './scraping/scraping-page';
import { prefetchScraping } from './scraping/scraping';
import { GeneralSettings } from './settings/general-settings';
import { MaintenanceSettings } from './settings/maintenance-settings';
import { MediaSettings } from './settings/media-settings';
import { NetworkSettings } from './settings/network-settings';

/* Popover 这类弹出层由 React Aria 渲染到挂载容器外面。落在 `body` 上就出了 `.peach-react`
 * 的作用域：token 读到的是 `board.css` 的值，Preflight 也管不到。所有 React 根的弹出层都进
 * `body` 末尾这一个同样带 `.peach-react` 的容器。 */
let overlays: HTMLElement | null = null;
function overlayContainer(): HTMLElement {
  if (!overlays?.isConnected) {
    overlays = document.createElement('div');
    overlays.className = 'peach-react';
    overlays.dataset.reactOverlays = '';
    document.body.append(overlays);
  }
  return overlays;
}

/* 所有 React 根共用一个 QueryClient（ADR-0031）：页面级 `prefetch` 写进去的首屏，
 * 组件挂上去就直接读到，同一份数据不会因为挂在哪棵根上而各取一次。 */
function mounter<P extends object>(Component: ComponentType<P>) {
  return (el: Element, props: P): Bundle.ReactMount<P> => {
    const root = createRoot(el);
    const paint = (next: P) => root.render(
      <QueryClientProvider client={queryClient}>
        <UNSAFE_PortalProvider getContainer={overlayContainer}><Component {...next} /></UNSAFE_PortalProvider>
      </QueryClientProvider>,
    );
    paint(props);
    return { update: paint, unmount: () => root.unmount() };
  };
}

/* 扫描与采集一个名字两种形态：数据管理页那张卡片，和目录页顶上那条横幅。两边读同一个
 * `queryKey`，所以同时挂着时它们看的是同一份快照，Query 也只发一份轮询。 */
const LibraryProcessing = (props: Bundle.LibraryProcessingProps) => (
  props.mode === 'notice' ? <LibraryProcessingNotice {...props} /> : <LibraryProcessingCard {...props} />
);

/** 整页归 React 的那些页面，按名字给遗留层的 React 档用。 */
export const pages: Bundle.ReactPages = {
  activity: { prefetch: (_props, signal) => prefetchTasks(signal), mount: mounter(ActivityPage) },
  'library-processing': {
    prefetch: (_props, signal) => prefetchLibraryProcessing(signal),
    mount: mounter(LibraryProcessing),
  },
  'quality-goals': {
    prefetch: (_props, signal) => prefetchQualityGoals(signal), mount: mounter(QualityGoalsPage),
  },
  scraping: { prefetch: (_props, signal) => prefetchScraping(signal), mount: mounter(ScrapingPage) },
};

export const mountGeneralSettings: typeof Bundle.mountGeneralSettings = mounter(GeneralSettings);
export const mountMediaSettings: typeof Bundle.mountMediaSettings = mounter(MediaSettings);
export const mountNetworkSettings: typeof Bundle.mountNetworkSettings = mounter(NetworkSettings);
export const mountMaintenanceSettings: typeof Bundle.mountMaintenanceSettings = mounter(MaintenanceSettings);
