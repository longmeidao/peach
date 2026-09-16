/* 读数卡：一枚图标配一个名字、一个大数、一条脚注。
 *
 * 旧 `.metricstrip>button` 与 `.tastesummary` 是同一张卡，统计页让它兼做页签、口味页只读。
 * 三段各有各的内边距，脚注贴着卡底、比卡面暗一点点，所以卡片自己不留内边距，
 * 由三段分别排（`padding:16px 0 0`、`0 16px`、`12px 16px 16px`、`10px 16px`）。
 *
 * 图标底色按卡片在一排里的位次换，四张卡四个颜色；旧值是四个字面色，这里取图表色 token
 * 里最接近的四档（蓝、紫、绿、黄），差异登记在 `../boardui/ORIGIN.md`。 */
import type { ComponentType, ReactNode } from 'react';

import { cardClass, type CardOptions } from './card';

type Glyph = ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;

/* 图标那个小方块居中用 flex 不用 grid：`grid` 与旧样式表同名，按 `../styles.css` 顶上的
 * `@source not inline(...)` 不生成这个工具类。 */

/** 一排四张卡的图标色。第五张起循环，旧样式表也只定到第四张。 */
const ACCENT = ['text-chart-6', 'text-chart-5', 'text-chart-7', 'text-chart-8'];
const ACCENT_TINT = ['bg-chart-6/10', 'bg-chart-5/10', 'bg-chart-7/10', 'bg-chart-8/10'];

/** 读数卡的卡面。宿主可能是 `<div>` 也可能是 React Aria 的 `Tab`，所以只给类名。 */
export function statCardClass(options: CardOptions = {}) {
  return `${cardClass({ ...options, padding: 'none' })} flex flex-col overflow-hidden pt-4 text-left`;
}

/** 一排读数卡：四张一排，窄屏折成两张一排。宿主可能是 `TabList`，所以类名也单独给一份。 */
export const STAT_STRIP = 'inline-grid w-full grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4';

export function StatCard(
  { label, icon: Icon, accent = 0, figure, footer }:
  { label: string; icon?: Glyph; accent?: number; figure: string; footer?: ReactNode },
) {
  return (
    <>
      <span className="flex min-w-0 items-center gap-2 px-4 text-body-regular text-text-secondary max-sm:gap-1.5 max-sm:px-3">
        {Icon ? (
          <i aria-hidden className={`flex size-7 shrink-0 items-center justify-center rounded-lg max-sm:size-6 ${ACCENT[accent % 4]} ${ACCENT_TINT[accent % 4]}`}>
            <Icon aria-hidden className="size-4" />
          </i>
        ) : null}
        <span className="min-w-0 truncate">{label}</span>
      </span>
      <b className="px-4 pt-3 pb-4 text-title-1-medium tabular-nums text-text-primary max-sm:px-3 max-sm:pb-3">
        {figure}
      </b>
      {/* 脚注压在卡底：卡片被邻居撑高时空出来的那块留给读数上方，脚注不跟着飘。 */}
      <small className="mt-auto block min-h-9.5 bg-card-footer px-4 py-2.5 text-caption-1-regular text-text-secondary max-sm:px-3 max-sm:py-2">
        {footer}
      </small>
    </>
  );
}
