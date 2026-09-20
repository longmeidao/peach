import type { PropsWithChildren } from 'react';

export interface DataTableFrameProps extends PropsWithChildren {
  /** 关注来源表需要额外的排序图标规则；外框与行状态仍由这个共享组件负责。 */
  follow?: boolean;
}

/** BoardUI Table 的 Data Table 外框：主表面、完整边线、圆角与选中行反馈。 */
export function DataTableFrame({ children, follow = false }: DataTableFrameProps) {
  return (
    <div data-board-data-table data-follow-table={follow || undefined}>
      {children}
    </div>
  );
}
