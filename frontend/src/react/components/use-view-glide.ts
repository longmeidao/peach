/* 一排「你在哪儿」的键下面那块滑动玻璃（React 这一侧；首页与关注页那几排归壳的 `GLIDE_ROWS`）。
 *
 * 玻璃是一个常驻节点：由组件画在浮层根上、只建一次，换筛选、换视图都只挪它，不重建——换了
 * 元素，动画就从头起跑，看到的只是瞬移。位移与抻长交给遗留层的 `moveGlidePane`，全站只有这一种
 * 动法；这里只管「此刻落在哪一枚上」：
 *
 * - 按下去立刻滑到那一枚（壳当场推新的按下态，这里跟着 `pressed` 变）；
 * - 悬停时滑到指针下那一枚，离开这一排回到按下的那一枚（触摸不跟）；
 * - 这一排横滚或窗口改尺寸时只重量、不动画；
 * - 这一排量不出宽度（被 `hidden` 收起、祖先 `display:none`）或目标滚出了可视区，玻璃收起。
 *
 * 坐标以浮层根（玻璃的父元素）为原点，扣掉中间每一层的滚动量，同壳的 `viewGlideGeometry`：
 * 玻璃住在滚动层外面，纵向回弹不会被横滚容器切平。 */
import { useCallback, useEffect, useLayoutEffect, useRef, type PointerEvent, type RefObject } from 'react';
import { moveGlidePane } from '@peach/legacy/ui';

interface Box { x: number; y: number; w: number; h: number }

function geometry(pill: HTMLElement, host: HTMLElement): Box | null {
  if (!host.contains(pill)) return null;
  let x = 0;
  let y = 0;
  for (let node: HTMLElement | null = pill; node && node !== host; node = node.offsetParent as HTMLElement | null) {
    x += node.offsetLeft;
    y += node.offsetTop;
  }
  const rect = pill.getBoundingClientRect();
  for (let node = pill.parentElement; node && node !== host; node = node.parentElement) {
    x -= node.scrollLeft;
    y -= node.scrollTop;
    if (node.scrollWidth > node.clientWidth && getComputedStyle(node).overflowX !== 'visible') {
      const viewport = node.getBoundingClientRect();
      if (rect.right <= viewport.left || rect.left >= viewport.right) return null;
    }
  }
  return { x, y, w: pill.offsetWidth, h: pill.offsetHeight };
}

/** `pane` 是玻璃节点，`row` 是这一排；`pressed` 是这一排里按下那一枚的选择器。`key` 变了
 *  （按下态换了、这一排出现或收起）就带动画落到新的按下项上。返回的两个处理器接在键与排上。 */
export function useViewGlide(
  pane: RefObject<HTMLElement | null>, row: RefObject<HTMLElement | null>, pressed: string, key: unknown,
) {
  const last = useRef<Box | null>(null);
  const place = useCallback((target: HTMLElement | null, animate: boolean) => {
    const glass = pane.current;
    const line = row.current;
    /* 玻璃是浮层根的直接子元素，根是吸顶定位的，所以根就是它的定位基准。不读 `offsetParent`：
       收起着的玻璃那一项是 null。 */
    const host = glass?.parentElement;
    if (!glass) return;
    const active = line && line.offsetWidth ? target ?? line.querySelector<HTMLElement>(pressed) : null;
    const box = active && host ? geometry(active, host) : null;
    if (!box || !box.w) {
      glass.hidden = true;
      return;
    }
    /* 从收起到出现是第一次落位，不从上一次的旧坐标飞进来。 */
    const from = glass.hidden ? null : last.current;
    glass.hidden = false;
    last.current = box;
    moveGlidePane(glass, animate ? from : null, box, 'x');
  }, [pane, row, pressed]);

  /* 首次落位不动画；往后按下态一变就滑过去。放在布局阶段：画出来的第一帧玻璃就在位上。 */
  const placed = useRef(false);
  useLayoutEffect(() => {
    const glass = pane.current;
    if (glass && !placed.current) glass.hidden = true;
    place(null, placed.current);
    placed.current = true;
  }, [place, key]);

  /* 横滚、改尺寸只重量。滚动事件不冒泡，所以在浮层根上按捕获阶段接住这一排里任何一层的滚动。 */
  useEffect(() => {
    const host = pane.current?.parentElement;
    let frame = 0;
    const remeasure = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => { frame = 0; place(null, false) });
    };
    host?.addEventListener('scroll', remeasure, { capture: true, passive: true });
    addEventListener('resize', remeasure, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      host?.removeEventListener('scroll', remeasure, { capture: true });
      removeEventListener('resize', remeasure);
    };
  }, [pane, place]);

  const hover = useCallback((event: PointerEvent<HTMLElement>) => {
    if (event.pointerType !== 'touch') place(event.currentTarget, true);
  }, [place]);
  const leave = useCallback((event: PointerEvent<HTMLElement>) => {
    if (event.pointerType !== 'touch') place(null, true);
  }, [place]);
  return { hover, leave };
}
