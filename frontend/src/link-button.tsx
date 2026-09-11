import type { ComponentChildren } from 'preact';

/** 正文和操作区的内部导航，右箭头表示在 Peach 内继续。 */
export function LinkButton({ href, children }: { href: string; children: ComponentChildren }) {
  return <a class="board-link-button" href={href}><span>{children}</span>
    <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-arrow-up" /></svg>
  </a>;
}
