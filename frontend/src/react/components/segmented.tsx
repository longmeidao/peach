/* 分段控件：一排互斥选项挤在一条药丸轨道里。
 *
 * 迁移前统计页的面板页签 `.insighttabs`、口味页的 `.insightswitch`、关注管理的
 * `.follow-workspace-switch` 是同一个形状：轨道 `background-tertiary-default` 打底、4px 内边距、
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
