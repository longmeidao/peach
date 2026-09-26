/* 粘在顶栏下沿的那条玻璃操作条：一个小标题后面一排胶囊键，或者上下两排的筛选浮层。
 *
 * 料（漂移的两团、斜光、内嵌边与落影）由 `web/board.css` 的 `[data-glass-pane]` 一处给，
 * 几何、饱和度与文字色在 `../styles.css` 的 `[data-filter-glass]`，高对比与减少透明度的回退
 * 也在那一条上。胶囊键 30px 高、透明底、一圈 `--glass-low`，
 * 悬停换成 `--glass-rim` 边加 `--glass-pick-fill` 底——玻璃上的键不是 BoardUI 那种实心按钮。 */
import type { ReactNode } from 'react';

export function FilterGlass({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div role="group" aria-label={title} data-filter-glass data-glass-pane=""
      className="sticky top-topbar z-10 mb-5.5 flex flex-wrap items-center gap-x-2.5 gap-y-2 px-4 py-2.5">
      <h3 className="mr-1 text-body-medium">{title}</h3>
      {children}
    </div>
  );
}

/** 两排的那一副：首页与标签页的筛选浮层。上排是一行横滚的筛选药丸，下排是读数和这一屏的
 *  视图控件。几何同旧 `.board-filter-frame`：上排 48px 高、8px／12px 内边距，下排最矮 46px、
 *  格间 12px。整块吸在顶栏下沿，粘住时仍是同一块玻璃。 */
export function FilterGlassRows(
  { label, topLabel, top, bottom }: { label: string; topLabel: string; top: ReactNode; bottom: ReactNode },
) {
  return (
    <div role="group" aria-label={label} data-filter-glass data-glass-pane=""
      className="sticky top-topbar z-10 mb-5.5 flex flex-col">
      <div role="group" aria-label={topLabel} data-filter-row="top"
        className="flex h-12 min-w-0 items-center gap-1.75 overflow-x-auto overscroll-x-contain px-3 py-2">
        {top}
      </div>
      <div data-filter-row="bottom" className="flex min-h-11.5 min-w-0 items-center gap-3 px-3 py-2">
        {bottom}
      </div>
    </div>
  );
}

/* 浮层上的筛选药丸：8px 圆角、13px 字，未选中是一圈虚线 `--glass-low`，悬停转实线；选中的
 * 线与填充归调用方（标签类型药丸取自己的类型色，见 `../styles.css` 的 `[data-tag-pill]`）。 */
const FILTER_PILL = 'flex h-7.5 flex-none cursor-pointer items-center gap-1.75 rounded-lg border border-dashed'
  + ' border-(--glass-low) bg-transparent px-2.5 text-body-2-regular leading-5 whitespace-nowrap text-inherit'
  + ' outline-none hover:border-solid focus-visible:ring-2 focus-visible:ring-border-focus-ring';

export function FilterPill(
  { children, pressed, onPress, ...data }:
  { children: ReactNode; pressed: boolean; onPress(): void } & Record<`data-${string}`, string>,
) {
  return (
    <button type="button" {...data} aria-pressed={pressed} className={FILTER_PILL}
      onClick={onPress}>
      {children}
    </button>
  );
}

const PILL = 'h-7.5 cursor-pointer rounded-full border border-(--glass-low) bg-transparent px-3'
  + ' text-body-2-regular leading-none whitespace-nowrap text-inherit outline-none'
  + ' hover:border-(--glass-rim) hover:bg-(--glass-pick-fill)'
  + ' focus-visible:ring-2 focus-visible:ring-border-focus-ring'
  + ' aria-busy:cursor-wait aria-busy:opacity-55';

export function GlassPill(
  { children, onPress, busy = false }: { children: ReactNode; onPress(): void; busy?: boolean },
) {
  return (
    <button type="button" className={PILL} aria-busy={busy || undefined} aria-disabled={busy || undefined}
      onClick={() => { if (!busy) onPress() }}>
      {children}
    </button>
  );
}
