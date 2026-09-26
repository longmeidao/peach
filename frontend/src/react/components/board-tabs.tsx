/* Board 的下划线 Tabs：一排页面级的去处（厂牌／事务所、本地／在线），答的是「现在摆的是
 * 哪一页」，不是给当前这批加一条筛选——筛选归玻璃浮层上的药丸。
 *
 * 形态照遗留 `boardTabsHtml` 那一副：底下一条 1px `border-button-default` 基线，每一枚
 * 10px／12px 内边距、14/20 正文，选中那一枚换 `border-focus-ring` 蓝色并加半档字重；760px
 * 以下间隔收到 0、内边距 10px／9px、字号降到 13px。
 *
 * 选中的 2px 蓝线是一条自己的元素，不画在按钮上：换一枚时它从旧位置滑过去，时长与缓动取
 * 全站同一条弹簧（`--spring-pane-ms`／`--spring-pane`，规则在 `../styles.css` 的
 * `[data-tab-indicator]`）。头一次画出来时直接落位，第一帧之后才打开过渡，免得它从左端飞进来。
 *
 * 不挂 `data-board-tabs`、也不用 `board-local-nav`：遗留层 `wireBoardTabs` 在 `body` 上观察
 * 新插入的节点，认的就是那两样，挂上了就是两套接线同时量同一条线。 */
import { useLayoutEffect, useRef, type KeyboardEvent } from 'react';

import { spriteGlyph } from './sprite-glyph';

export interface BoardTab<V extends string> {
  value: V;
  label: string;
  /** 遗留雪碧图里的字形名，只在它指向对象（厂牌、事务所、本地、订阅源）时给。 */
  symbol?: string;
}

/** 页签与分组标题后面挂的那个计数徽标（旧 `.board-tab-count`）：12/16 半档字重、主文字色
 *  10% 的底，整块降到五成，是附注不是读数。口径由调用方给，徽标自己不算数。 */
export function TabCount({ value }: { value: number }) {
  return (
    <span data-tab-count=""
      className="ml-1.5 inline-block rounded-sm bg-text-primary/10 px-1 py-px text-caption-1-medium text-text-primary opacity-50">
      {value.toLocaleString()}
    </span>
  );
}

const TAB = 'relative z-1 flex flex-none cursor-pointer items-center whitespace-nowrap'
  + ' border-b-2 border-transparent px-3 py-2.5 text-body-regular text-text-secondary outline-none'
  + ' focus-visible:outline-2 focus-visible:-outline-offset-3 focus-visible:outline-border-focus-ring'
  + ' aria-selected:font-medium aria-selected:text-border-focus-ring'
  + ' max-board-narrow:px-2.25 max-board-narrow:text-body-2-regular';

export function BoardTabs<V extends string>(
  { tabs, value, label, onChange }:
  { tabs: readonly BoardTab<V>[]; value: V; label: string; onChange(value: V): void },
) {
  const list = useRef<HTMLDivElement>(null);
  const indicator = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    const host = list.current;
    if (!host) return;
    const measure = () => {
      const selected = host.querySelector<HTMLElement>('[role="tab"][aria-selected="true"]');
      if (!selected || !selected.offsetWidth) return;
      host.style.setProperty('--tab-x', `${selected.offsetLeft}px`);
      host.style.setProperty('--tab-width', `${selected.offsetWidth}px`);
    };
    measure();
    const frame = requestAnimationFrame(() => indicator.current?.setAttribute('data-ready', ''));
    const resize = new ResizeObserver(measure);
    resize.observe(host);
    return () => { cancelAnimationFrame(frame); resize.disconnect() };
  }, [value]);

  /* 左右键在同一排里挪，Home／End 到两头，挪到哪一枚就是选了哪一枚：这一排每一枚都是一个
     地址，焦点停在哪儿、页面就摆哪儿，和侧栏导航同一个说法。 */
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const at = tabs.findIndex((tab) => tab.value === value);
    const next = event.key === 'ArrowRight' ? at + 1 : event.key === 'ArrowLeft' ? at - 1
      : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -2;
    if (next === -2) return;
    event.preventDefault();
    const target = tabs[(next + tabs.length) % tabs.length];
    list.current?.querySelector<HTMLElement>(`[data-tab="${target.value}"]`)?.focus();
    if (target.value !== value) onChange(target.value);
  };

  return (
    <div ref={list} role="tablist" aria-label={label} data-board-tab-list="" onKeyDown={onKeyDown}
      className="relative mb-5.5 flex flex-none gap-1 overflow-x-auto border-b border-border-button-default max-board-narrow:gap-0">
      {tabs.map((tab) => {
        const Glyph = tab.symbol ? spriteGlyph(tab.symbol) : null;
        const selected = tab.value === value;
        return (
          <button key={tab.value} type="button" role="tab" data-tab={tab.value} aria-selected={selected}
            tabIndex={selected ? 0 : -1} className={TAB}
            onClick={() => { if (!selected) onChange(tab.value) }}>
            {Glyph ? <Glyph className="mr-1.5 size-4" /> : null}
            {tab.label}
          </button>
        );
      })}
      <span ref={indicator} aria-hidden data-tab-indicator=""
        className="pointer-events-none absolute bottom-0 left-0 z-1 h-0.5 bg-border-focus-ring" />
    </div>
  );
}
