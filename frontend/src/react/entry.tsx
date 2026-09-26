/* React 子树的构建入口（`web/dist/peach-react.js`），按 `bundle.d.ts` 的签名导出挂载函数。 */
import './styles.css';

import type { ComponentType } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { MotionConfig } from 'motion/react';
import { UNSAFE_PortalProvider } from 'react-aria';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';

import { ActivityPage } from './activity/activity-page';
import { prefetchTasks } from './activity/tasks';
import { AvatarPicker } from './avatar-picker/avatar-picker-page';
import type * as Bundle from './bundle';
import { CoverCrop } from './cover-crop/cover-crop-page';
import { prefetchFollowManage } from './follow-manage/follow-manage';
import { FollowManagePage } from './follow-manage/follow-manage-page';
import { prefetchLibraryProcessing } from './library-processing/library-processing';
import { prefetchMediaRepair } from './media-repair/media-repair';
import { MediaRepairCard } from './media-repair/media-repair-card';
import { LibraryProcessingCard } from './library-processing/library-processing-card';
import { LibraryProcessingNotice } from './library-processing/library-processing-notice';
import { QualityGoalsPage } from './quality-goals/quality-goals-page';
import { prefetchQualityGoals } from './quality-goals/quality-goals';
import { queryClient } from './query';
import { prefetchReview } from './review/review';
import { ReviewPage } from './review/review-page';
import { ScrapingPage } from './scraping/scraping-page';
import { prefetchScraping } from './scraping/scraping';
import { prefetchConfiguration } from './settings/configuration';
import { ConfigurationPage } from './settings/configuration-page';
import { ConfigurationSummary } from './settings/configuration-summary';
import { prefetchStats } from './stats/stats';
import { StatsPage } from './stats/stats-page';
import { DEFAULT_WINDOW, prefetchTaste } from './taste/taste';
import { TastePage } from './taste/taste-page';

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
 * 组件挂上去就直接读到，同一份数据不会因为挂在哪棵根上而各取一次。
 *
 * 第一帧用 `flushSync` 同步落到 DOM 上：遗留壳挂完这一页紧接着就读它画出来的结构
 * （配置页按 `.configgroup` 小标题切页签，再按地址里的 `#peachProxy` 滚过去），而
 * `root.render` 自己是排进下一次渲染的；骨架已经清掉，晚一帧画就是一帧空白。往后的
 * `update` 照常异步。
 *
 * EvilCharts 的生长动画由 Motion 逐帧驱动，`web/css/01-base.css` 那条全局 reduced motion
 * 规则只关得掉 CSS 过渡，够不着它。`MotionConfig reducedMotion="user"` 在根上一处接住：
 * 系统设了减弱动态效果，每棵 React 根里的 Motion 动画都按终态直接画。 */
function mounter<P extends object>(Component: ComponentType<P>) {
  return (el: Element, props: P): Bundle.ReactMount<P> => {
    const root = createRoot(el);
    const paint = (next: P) => root.render(
      <QueryClientProvider client={queryClient}>
        <MotionConfig reducedMotion="user">
          <UNSAFE_PortalProvider getContainer={overlayContainer}><Component {...next} /></UNSAFE_PortalProvider>
        </MotionConfig>
      </QueryClientProvider>,
    );
    flushSync(() => paint(props));
    return { update: paint, unmount: () => root.unmount() };
  };
}

/* 扫描与采集一个名字两种形态：数据管理页那张卡片，和目录页顶上那条横幅。两边读同一个
 * `queryKey`，所以同时挂着时它们看的是同一份快照，Query 也只发一份轮询。 */
const LibraryProcessing = (props: Bundle.LibraryProcessingProps) => (
  props.mode === 'notice' ? <LibraryProcessingNotice {...props} /> : <LibraryProcessingCard {...props} />
);

/** 整页归 React 的那些页面，按名字给遗留层用。 */
export const pages: Bundle.ReactPages = {
  activity: { prefetch: (_props, signal) => prefetchTasks(signal), mount: mounter(ActivityPage) },
  /* 换头像的候选要打到图库上，而资料页每进一次就预取一遍的话，多数时候没人点开它。
     首屏没有要取的东西，`prefetch` 是空操作，候选由弹层自己在打开时取。 */
  'avatar-picker': { prefetch: async () => {}, mount: mounter(AvatarPicker) },
  /* 裁剪封面同理：详情页每进一次都挂这枚键，首屏没有要取的东西，图到点开才量。 */
  'cover-crop': { prefetch: async () => {}, mount: mounter(CoverCrop) },
  configuration: {
    prefetch: (_props, signal) => prefetchConfiguration(signal), mount: mounter(ConfigurationPage),
  },
  /* 摘要卡读配置页同一份快照：从这里点进配置页时，首屏已经在缓存里。 */
  'configuration-summary': {
    prefetch: (_props, signal) => prefetchConfiguration(signal), mount: mounter(ConfigurationSummary),
  },
  /* 首屏只取来源清单与凭据状态，地址栏指着「订阅源」时连它一起取。检查更新与查找那两趟
     后台任务的快照不在首屏里：它们常年躺着上一趟的回执，等它们只会让首屏多一个往返。 */
  'follow-manage': {
    prefetch: (props, signal) => prefetchFollowManage(signal, props.tab), mount: mounter(FollowManagePage),
  },
  'library-processing': {
    prefetch: (_props, signal) => prefetchLibraryProcessing(signal),
    mount: mounter(LibraryProcessing),
  },
  'media-repair': { prefetch: (_props, signal) => prefetchMediaRepair(signal), mount: mounter(MediaRepairCard) },
  'quality-goals': {
    prefetch: (_props, signal) => prefetchQualityGoals(signal), mount: mounter(QualityGoalsPage),
  },
  /* ADR-0018 的确定项已由扫描与资料处理任务落库；复核页只读取剩下的判断题。 */
  review: {
    prefetch: (_props, signal) => prefetchReview(signal), mount: mounter(ReviewPage),
  },
  scraping: { prefetch: (_props, signal) => prefetchScraping(signal), mount: mounter(ScrapingPage) },
  stats: { prefetch: (_props, signal) => prefetchStats(signal), mount: mounter(StatsPage) },
  /* 首屏取的是「全部时间」那一份：分析范围是组件状态，每次进这一页都从它开始。 */
  taste: {
    prefetch: (_props, signal) => prefetchTaste(DEFAULT_WINDOW, signal), mount: mounter(TastePage),
  },
};
