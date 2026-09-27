/* 垃圾文件队列（`/junk-files`）的路由与计数行骨架。
 *
 * 看哪一类、看待判断还是已排除，全由地址决定：分类链接是可深链的 `<a href>`，刷新后原样恢复。
 * 壳（`web/app.js`）与 `junk-queue` island 读的是同一组函数，所以放在 island 层这边，不依赖 React。
 *
 * 计数行骨架是壳在 React 包加载之前铺的那一版，画在 `.peach-react` 里，结构、`data-*` 钩子与
 * 类名和 island 等数据时画出来的那一版逐项相同（`junk-queue/junk-count.tsx`，用例对照两者），
 * 所以接管那一拍这一行不跳。分类与视图此刻就有答案，只有读数和各类的计数徽标要等数据。 */
import { esc } from '@peach/legacy/core';

export type JunkView = 'pending' | 'dismissed';
export type JunkKind = '' | 'video' | 'image' | 'archive' | 'audio' | 'url' | 'other';

export interface JunkRoute { kind: JunkKind; view: JunkView }

/** 分类条上的几项：键、标签、雪碧图字形。键与 `/api/ads?kind=` 的取值一一对应。 */
export const JUNK_KIND_OPTIONS: readonly (readonly [JunkKind, string, string])[] = [
  ['', '全部', 'layout-grid'], ['video', '视频', 'play'], ['image', '图片', 'pics'],
  ['archive', '压缩包', 'file-archive'], ['audio', '音频', 'file-audio'], ['url', '网址', 'globe'],
  ['other', '其它', 'hard-drive'],
];

/** 认不出的分类一律落回「全部」。 */
export const cleanJunkKind = (value: string | null | undefined): JunkKind =>
  JUNK_KIND_OPTIONS.find(([key]) => key === value)?.[0] ?? '';

/** 地址查询串里的分类与视图。 */
export function junkRoute(search: string): JunkRoute {
  const params = new URLSearchParams(search);
  return { kind: cleanJunkKind(params.get('type')), view: params.get('view') === 'dismissed' ? 'dismissed' : 'pending' };
}

/** 某一类、某一视图的地址。默认那一档（全部、待判断）不写进查询串。 */
export function junkPath(kind: JunkKind = '', view: JunkView = 'pending'): string {
  const params = new URLSearchParams();
  if (kind) params.set('type', kind);
  if (view === 'dismissed') params.set('view', 'dismissed');
  const query = params.toString();
  return `/junk-files${query ? `?${query}` : ''}`;
}

/** 分类条末尾那一项：待判断时去「已排除」，已排除时回「待判断」。 */
export function junkViewLink(view: JunkView): { view: JunkView; label: string; glyph: string; href: string } {
  return view === 'dismissed'
    ? { view: 'pending', label: '返回待判断', glyph: 'rotate-ccw', href: junkPath('', 'pending') }
    : { view: 'dismissed', label: '已排除', glyph: 'eye-off', href: junkPath('', 'dismissed') };
}

export const junkSummaryLabel = (view: JunkView) => (view === 'dismissed' ? '已排除' : '待判断');

/* 以下类名抄自 `react/components/collection-summary.tsx` 的等待态，由用例逐字对照。 */
const SUMMARY_CLASS = 'flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5 '
  + 'max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4 dark:bg-background-primary-default';
const SUMMARY_TERMS = 'flex min-w-0 flex-col gap-2';
const SUMMARY_LABEL = 'text-body-regular text-text-secondary';
const SUMMARY_FIGURE = 'text-display-4-medium tabular-nums text-text-primary';
const SUMMARY_PENDING = 'relative inline-block h-8 w-24 rounded-2lg align-middle skeleton-sheen';

const glyph = (name: string) => `<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${name}"></use></svg>`;

/** 壳在 React 包加载之前铺的计数行：摘要面与分类条，读数与计数徽标留空。 */
export function junkCountSkeletonHtml({ kind, view }: JunkRoute): string {
  const links = JUNK_KIND_OPTIONS.map(([key, label, icon]) =>
    `<a href="${junkPath(key, view)}" data-junk-kind-link="${key}"${key === kind ? ' aria-current="page"' : ''}>${glyph(icon)}${esc(label)}</a>`).join('');
  const other = junkViewLink(view);
  return `<div class="peach-react" data-junk-count-skeleton=""><div data-junk-count="">`
    + `<div data-junk-summary="" aria-live="polite"><div data-collection-summary="" class="${SUMMARY_CLASS}"><div class="${SUMMARY_TERMS}">`
    + `<span class="${SUMMARY_LABEL}">${junkSummaryLabel(view)}</span>`
    + `<strong class="${SUMMARY_FIGURE}"><span data-skeleton="count" aria-hidden="true" class="${SUMMARY_PENDING}"></span></strong>`
    + `</div></div></div>`
    + `<div data-junk-filters-frame=""><nav data-junk-filters="" aria-label="垃圾文件分类">${links}<i data-junk-divider="" aria-hidden="true"></i>`
    + `<a href="${other.href}" data-junk-view-link="${other.view}"${view === 'dismissed' ? ' aria-current="page"' : ''}>${glyph(other.glyph)}${other.label}</a>`
    + `</nav></div></div></div>`;
}
