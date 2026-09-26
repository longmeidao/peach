/* 遗留雪碧图（`web/index.html` 的 `#i-*` symbol）里的字形，做成和 Remix 图标同形的组件。
 *
 * 首屏骨架由遗留层画，字形取的就是雪碧图：页面接管时换成 Remix 里形状最近的那几枚，
 * 这一排会在骨架换成正文的那一拍跳一下（方勾变圆勾、一叠文件变两页纸）。所以骨架里
 * 出现过的字形，接管后仍取同一枚。尺寸由宿主给（BoardUI `Button` 按档位传 `size-*`）。 */
import type { ComponentType } from 'react';

export type Glyph = ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;

const cache = new Map<string, Glyph>();

export function spriteGlyph(name: string): Glyph {
  const known = cache.get(name);
  if (known) return known;
  const Sprite: Glyph = ({ className }) => (
    <svg aria-hidden viewBox="0 0 24 24" fill="none" strokeLinecap="round" strokeLinejoin="round"
      className={`shrink-0 stroke-current stroke-2 ${className ?? 'size-4'}`}>
      <use href={`#i-${name}`} />
    </svg>
  );
  Sprite.displayName = `SpriteGlyph(${name})`;
  cache.set(name, Sprite);
  return Sprite;
}
