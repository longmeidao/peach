/* 分段控件：一排互斥选项挤在一条药丸轨道里。
 *
 * 迁移前统计页的面板页签 `.insighttabs`、口味页的 `.insightswitch` 与关注管理页的
 * `.follow-workspace-switch` 是同一个形状：
 * 轨道 `background-tertiary-default` 打底、4px 内边距、
 * 10px 圆角，选中那一格是一块浮起来的面（6px 圆角、1px 接触阴影）。迁到 React 时这几处都掉成了
 * 裸文字加一条下划线，一排选项看不出是一个控件。
 *
 * 旧实现的滑块是一个单独的 `.board-segment-thumb` 元素，靠 `board-controls.ts` 量位置再平移。
 * 这里不搬那套：选中面直接画在被选中的那一格上。形态、尺寸与配色照旧，少的只有滑动动画。
 * 字重不随选中变（`peach-web-ui`：选中态不加字重），整排都是 `body-medium`。 */

/** 轨道。宽度按内容收，窄屏装不下时自己横向滚，不把页面撑出滚动条。 */
export const SEGMENTED_TRACK = 'inline-flex w-max max-w-full items-center gap-0.5 overflow-x-auto'
  + ' overscroll-x-contain rounded-2lg bg-background-tertiary-default p-1';

/* 深色下选中面用 `background-primary-hover`：深色的 `background-primary-default` 与轨道
 * （`background-tertiary-default`）是同一档 neutral-800，画上去看不见。 */
export const SEGMENT = 'flex min-h-7 flex-none cursor-pointer items-center gap-1.5 rounded-md px-2.5 py-1'
  + ' text-body-medium whitespace-nowrap text-text-secondary outline-none transition-colors'
  + ' hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring'
  + ' data-selected:bg-background-primary-default data-selected:text-text-primary data-selected:shadow-card'
  + ' dark:data-selected:bg-background-primary-hover';

/** `aria-selected` 而不是 `data-selected` 的宿主（自己写的 `<button role="tab">`）用这一串。 */
export const SEGMENT_ARIA = 'flex min-h-7 flex-none cursor-pointer items-center gap-1.5 rounded-md px-2.5 py-1'
  + ' text-body-medium whitespace-nowrap text-text-secondary outline-none transition-colors'
  + ' hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring'
  + ' aria-selected:bg-background-primary-default aria-selected:text-text-primary aria-selected:shadow-card'
  + ' dark:aria-selected:bg-background-primary-hover';

/** 只摆字形的那一档（版式、大图／紧凑）：每格正方，字形 16px，配上面的 `SEGMENTED_TRACK`。 */
export const SEGMENT_ICON = 'flex size-7 flex-none cursor-pointer items-center justify-center rounded-md'
  + ' text-text-secondary outline-none transition-colors'
  + ' hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring'
  + ' data-selected:bg-background-primary-default data-selected:text-text-primary data-selected:shadow-card'
  + ' dark:data-selected:bg-background-primary-hover';

/* 玻璃浮层上的那一档。flat 面那一副（灰轨道衬一枚不透明的白滑块）摆到浮层上就是整条里
 * 唯一一块实心的面，读起来像贴上去的另一个控件：轨道撤掉，字色按这块玻璃自己的文字色降到
 * 六成，选中那一格换成浮层选中态那块玻璃（`../styles.css` 的 `[data-glass-segment]`）。 */
export const SEGMENTED_GLASS_TRACK = 'inline-flex w-max max-w-full flex-none items-center gap-0.5 rounded-lg';

export const SEGMENT_GLASS = 'flex size-7.5 flex-none cursor-pointer items-center justify-center rounded-lg'
  + ' text-(--glass-text)/62 outline-none transition-colors hover:text-(--glass-text)'
  + ' focus-visible:ring-2 focus-visible:ring-border-focus-ring data-selected:text-(--glass-text)';
