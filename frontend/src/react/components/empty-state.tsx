/* 没有数据或结果时的空态：图标、标题、说明同处一个组件里（`peach-web-ui`）。
 *
 * 注册表里没有空态条目。标题是真的标题元素，冒烟用例按它认页面主体：一片白和「画出来了、
 * 只是没有内容」在别的断言下长得一模一样。 */
import type { ComponentType, ReactNode } from 'react';

type Glyph = ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;

export function EmptyState(
  { icon: Icon, title, actions, children }:
  { icon: Glyph; title: string; actions?: ReactNode; children: ReactNode },
) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-separator-border px-6 py-12 text-center">
      <Icon aria-hidden className="size-6 text-text-tertiary" />
      <h3 className="text-headline-medium text-text-primary">{title}</h3>
      <p className="max-w-prose text-body-2-regular text-text-secondary">{children}</p>
      {/* 去处属于这一块，不摆到框外面：「还没有内容」和一个不知道属于谁的按钮分开放时，
          读者要先把两样东西连起来才知道按下去做什么。 */}
      {actions ? <div className="mt-2 flex flex-wrap justify-center gap-2">{actions}</div> : null}
    </div>
  );
}
