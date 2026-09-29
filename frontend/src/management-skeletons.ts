import { islandButton } from './island-skeleton';

const placeholder = 'relative overflow-hidden skeleton-sheen bg-background-tertiary-default rounded-lg';
const text = (width = '60%') => `<span class="${placeholder} inline-block max-w-full align-middle" style="width:${width};height:1em"></span>`;
const wait = 'disabled data-skeleton-action';
const chart = 'min-w-0 rounded-2-5xl bg-background-secondary-default p-5 flex flex-col gap-4 max-sm:p-4';

/** 统计首屏与 StatsPage 的读数卡、双列库存图和三列分布图共用布局。 */
export function statsSkeleton(): string {
  const metrics = ['馆藏视频', '看过', '内容标签', '使用空间'].map((label, index) => `
    <div class="min-w-0 rounded-2xl shadow-card flex flex-col overflow-hidden pt-4 text-left ${index === 0 ? 'ring-2 ring-border-focus-ring bg-background-primary-default' : 'bg-background-secondary-default'}">
      <span class="flex min-w-0 items-center gap-2 px-4 text-body-regular text-text-secondary max-sm:gap-1.5 max-sm:px-3"><i class="${placeholder} size-7 max-sm:size-6"></i>${label}</span>
      <b class="px-4 pt-3 pb-4 text-title-1-medium max-sm:px-3 max-sm:pb-3">${text('4em')}</b>
      <small class="mt-auto block min-h-9.5 bg-card-footer px-4 py-2.5 text-caption-1-regular max-sm:px-3 max-sm:py-2">${text('6em')}</small>
    </div>`).join('');
  const radial = (title: string) => `<section class="${chart}" data-stats-chart>
    <header class="flex flex-wrap items-end justify-between gap-x-4 gap-y-1"><span class="flex min-w-0 flex-col gap-1"><h3 class="text-title-2-medium text-text-primary">${title}</h3><b class="text-display-4-medium">${text('4em')}</b></span><small class="text-caption-1-regular text-text-secondary">个视频</small></header>
    <svg class="h-75 w-full max-sm:h-65 text-background-tertiary-default" viewBox="0 0 200 200" fill="none" stroke="currentColor" stroke-width="12">${[76, 54, 32].map(r => `<circle cx="100" cy="100" r="${r}"/>`).join('')}</svg>
    <div class="inline-grid w-full grid-cols-3 gap-2 max-sm:grid-cols-2">${Array.from({ length: 3 }, () => `<div class="flex min-w-0 flex-col gap-1 rounded-xl bg-background-tertiary-default p-2.5"><span class="text-caption-1-regular">${text()}</span><b class="text-title-2-medium">${text('3em')}</b><small class="text-caption-1-regular">${text()}</small></div>`).join('')}</div>
  </section>`;
  return `<div class="peach-react"><div class="mx-auto flex w-full max-w-board flex-col gap-8">
    <p class="text-caption-1-regular text-text-secondary">账本当前快照 · ${text('12em')}</p>
    <div class="flex flex-col gap-4"><div class="inline-grid w-full grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4" data-stats-metrics>${metrics}</div>
      <div class="flex flex-col gap-5"><div class="inline-grid w-full gap-5 md:grid-cols-2">${radial('网盘与本地')}${radial('媒体库')}</div>
        <div class="inline-grid w-full gap-5 md:grid-cols-2 xl:grid-cols-3">${['时长', '画质', '文件类型'].map(title => `<section class="${chart}"><h3 class="text-title-2-medium">${title}</h3><div class="${placeholder} h-64"></div></section>`).join('')}</div>
      </div>
    </div>
    <section class="rounded-surface bg-background-secondary-default dark:bg-background-primary-default">
      <div class="flex flex-wrap gap-3 px-4 pt-3 text-body-regular">${['内容标签', '最近看过', '标签来源'].map(label => `<span>${label}</span>`).join('')}</div>
      <div class="flex flex-col gap-3 px-4 pt-3.5 pb-4">${Array.from({ length: 5 }, () => `<div class="${placeholder} h-7"></div>`).join('')}</div>
    </section>
  </div></div>`;
}

/** 重复文件首屏：完整汇总、玻璃批量条、组头和两行文件，尺寸跟正文一致。 */
export function duplicatesSkeleton(): string {
  const row = `<div class="duplicate-row items-center gap-3 border-t border-separator-border px-5 py-4 max-compact:p-4">
    <span class="${placeholder} row-span-2 inline-grid aspect-16/10 w-full rounded-2lg"></span>
    <span class="text-body-regular max-duplicate-narrow:col-start-2 max-duplicate-narrow:-col-end-1">${text('70%')}</span>
    ${Array.from({ length: 3 }, () => `<span class="font-mono text-caption-1-regular leading-5">${text('3em')}</span>`).join('')}
    <span class="col-start-2 -col-end-1 min-w-0 pt-0.5 font-mono text-caption-1-regular leading-5 max-duplicate-narrow:col-span-full">${text('75%')}</span>
  </div>`;
  const group = `<section class="mb-6 overflow-hidden rounded-surface bg-background-secondary-default dark:bg-background-primary-default" data-duplicate-group>
    <div class="flex flex-wrap items-center gap-3 bg-background-tertiary-default p-5 max-compact:p-4 dark:bg-background-secondary-default">
      <b class="text-title-2-medium">${text('5em')}</b><span class="font-mono text-caption-1-regular leading-5">${text('8em')}</span>
      <span class="ml-auto flex flex-wrap gap-2 max-compact:ml-0 max-compact:w-full">${['留最大', '留最长', '整组回收'].map(label => islandButton({ variant: 'secondary', size: 'small', label, attrs: wait })).join('')}</span>
    </div>${row.repeat(2)}</section>`;
  return `<div class="peach-react"><div class="mx-auto w-full max-w-board pb-10.5">
    <div data-collection-summary class="mb-5 flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5 max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4 dark:bg-background-primary-default">
      <div class="flex min-w-0 flex-col gap-2"><span class="text-body-regular text-text-secondary">重复内容</span><strong class="text-display-4-medium">${text('4em')}</strong></div><p class="text-body-regular text-text-secondary">${text('12em')}</p>
    </div>
    <div data-filter-glass data-glass-pane class="mb-5.5 flex flex-wrap items-center gap-x-2.5 gap-y-2 px-4 py-2.5"><h3 class="mr-1 text-body-medium">批量保留</h3>${['全部保留最大', '全部保留最长'].map(label => `<button ${wait} class="h-7.5 rounded-full border border-separator-border px-3 text-body-2-medium">${label}</button>`).join('')}</div>
    ${group.repeat(2)}
  </div></div>`;
}
