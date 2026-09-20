import type { ReactNode } from 'react';

interface SelectionDockProps {
  children: ReactNode;
  count: string;
  label: string;
}

/** 与首页多选共用的底部悬浮操作框。只在确实有选择时由调用方挂载。 */
export function SelectionDock({ children, count, label }: SelectionDockProps) {
  return (
    <div role="group" aria-label={label} data-selection-dock data-glass-pane="">
      <span role="status" className="px-2 text-body-2-regular whitespace-nowrap text-text-primary">
        {count}
      </span>
      {children}
    </div>
  );
}
