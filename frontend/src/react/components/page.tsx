/* 管理区整页正文的那一条窄列。
 *
 * 宽度取 `max-w-board`（`../styles.css` 把它接到 `web/board.css` 的 `--board-content`），
 * 页面标题 `#manageTitle` 钉的是同一个数：正文自己写一个像素值，标题与正文就会各走一条中线。 */
import type { ReactNode } from 'react';

export function Page({ children }: { children: ReactNode }) {
  return <div className="mx-auto flex w-full max-w-board flex-col gap-8">{children}</div>;
}
