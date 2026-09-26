/* 粘在顶栏下沿的那条玻璃操作条：一个小标题，后面一排胶囊键。
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
