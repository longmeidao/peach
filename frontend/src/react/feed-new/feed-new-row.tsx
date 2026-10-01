/* 新作那一行的卡片区，首页与资料页共用：画进壳留好的 `section.feednew` 宿主里，卡片是壳拼的
 * 那一份模板（`feedNewCardHtml`）。忽略的那条当场消失，已看过的留在原位只是变淡；两样都直接改
 * 这一行的节点，不重画整行——重画会把横滚的位置和自动滚动一起打回起点。一条都没有就整块不出。 */
import { useEffect, useLayoutEffect, useRef, type MouseEvent } from 'react';

import type { FeedNew } from './feed-new';

export function FeedNewRow({ feedNew, host, wire, act, settled }: {
  feedNew: FeedNew | null;
  host: HTMLElement;
  /** 拖动、滚轮，按设置接自动滚动。 */
  wire(row: Element | null): void;
  /** 卡上那两颗键的写操作。 */
  act(feedId: number, action: string): Promise<void>;
  /** 有没有卡：画出来、或最后一张被收起时报一次。 */
  settled?(hasItems: boolean): void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const html = feedNew?.items.length ? feedNew.html : '';
  useLayoutEffect(() => {
    host.removeAttribute('aria-busy');
    host.hidden = !html;
    if (feedNew) settled?.(!!html);
  }, [host, html, feedNew, settled]);
  useEffect(() => {
    if (html) wire(box.current?.querySelector('.feednewrow') ?? null);
  }, [wire, html]);
  const click = async (event: MouseEvent<HTMLDivElement>) => {
    const button = (event.target as Element).closest<HTMLElement>('[data-feed-action]');
    const card = button?.closest<HTMLElement>('[data-feed-id]');
    if (!button || !card) return;
    const action = button.dataset.feedAction || '';
    await act(Number(card.dataset.feedId), action);
    if (action === 'ignore') card.remove();
    else card.classList.add('isread');
    if (!box.current?.querySelector('[data-feed-id]')) {
      host.hidden = true;
      settled?.(false);
    }
  };
  return html ? <div ref={box} className="contents" onClick={(event) => { void click(event) }}
    dangerouslySetInnerHTML={{ __html: html }} /> : null;
}
