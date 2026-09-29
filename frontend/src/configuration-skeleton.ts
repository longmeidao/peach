import { islandButton } from './island-skeleton';
import { ENTRY_LINKS_HELP, ENTRY_LINKS_HINT } from './configuration-copy';

// 首屏在 React 包到达前绘制，几何与 settings/section.tsx、BoardUI SettingsRow 共用类名。
const section = (title: string, content: string) => `<section aria-label="${title}" class="flex w-full flex-col gap-2"><p class="w-full px-3 text-body-2-medium text-text-secondary">${title}</p><div class="flex w-full flex-col rounded-2xl bg-background-secondary-default pl-3">${content}<div class="-ml-3 flex flex-wrap items-center justify-end gap-3 rounded-b-2xl border-t border-separator-border bg-card-footer px-3 py-3">${islandButton({ label: '保存配置', attrs: 'disabled data-skeleton-action' })}</div></div></section>`;
const row = (label: string, description = '') => `<div class="flex min-h-[52px] w-full items-center justify-between gap-4 py-2.5 pr-2.5 border-b border-separator-border last:border-b-0"><div class="flex min-w-0 flex-col"><p class="text-body-regular text-text-primary">${label}</p>${description ? `<p class="text-body-2-regular text-text-secondary">${description}</p>` : ''}</div><span class="skeleton configuration-skeleton-toggle"></span></div>`;
const field = (label: string) => `<div class="flex w-full flex-col gap-1"><p class="text-body-medium text-text-primary">${label} 地址</p><span class="skeleton configuration-skeleton-input"></span><p class="pt-px text-caption-1-medium text-text-secondary">${ENTRY_LINKS_HINT}</p></div>`;

export function configurationSkeleton(): string {
  const nav = `<div class="board-local-nav" data-section-nav data-section-items>${['通用', '媒体', '网络与访问', '更新与维护'].map((title, i) => `<button type="button" tabindex="-1" aria-selected="${i === 0}">${title}</button>`).join('')}</div>`;
  const startup = section('开机自启', `<div class="flex flex-col">${row('开机后启动 Peach')}${row('静默启动', '开机后只显示托盘图标，不打开网页；「开机后启动 Peach」打开时生效。')}${row('在桌面创建快捷方式', '双击图标打开 Peach 网页；卸载时一并移除。')}</div>`);
  const links = section('外部入口', `<div class="flex flex-col gap-4 py-4 pr-3"><p class="text-body-2-regular text-text-secondary">${ENTRY_LINKS_HELP}</p>${field('JavDB')}${field('MISSAV')}</div>`);
  return `<div class="peach-react"><div class="configpage">${nav}<div class="flex flex-col gap-6">${startup}${links}</div></div></div>`;
}
