import { useLayoutEffect, useRef } from 'preact/hooks';
import { setActionBusy, wireAnchoredMenu } from '@peach/legacy/ui';

interface Action { label: string; icon: string; run(): void }
export function SplitAction({ id, label, actions, busy }: { id: string; label: string; actions: [Action, ...Action[]]; busy: boolean }) {
  const root = useRef<HTMLDivElement>(null);
  const floating = useRef<ReturnType<typeof wireAnchoredMenu>>();
  useLayoutEffect(() => {
    const mount = root.current!;
    floating.current = wireAnchoredMenu(mount, mount.querySelector('.splittoggle')!, mount.querySelector('[role=menu]')!);
    return () => floating.current?.setOpen(false);
  }, []);
  useLayoutEffect(() => {
    root.current?.querySelectorAll('button').forEach(button => setActionBusy(button, busy));
    if (busy) floating.current?.setOpen(false);
  }, [busy]);
  const glyph = (name: string) => <svg viewBox="0 0 24 24" aria-hidden="true"><use href={`#i-${name}`} /></svg>;
  const run = (action: Action) => { if (busy) return; floating.current?.setOpen(false); action.run(); };
  return <div ref={root} class="splitbutton board-button-group" onClickCapture={event => {if(busy){event.preventDefault();event.stopPropagation();}}} onKeyDown={event => {
    const items = Array.from(root.current!.querySelectorAll<HTMLButtonElement>('[role=menuitem]'));
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault(); if (busy) return;
      floating.current?.setOpen(true);
      const index = items.indexOf(document.activeElement as HTMLButtonElement);
      const next = index < 0 ? (event.key === 'ArrowDown' ? 0 : items.length - 1)
        : (index + (event.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
      items[next]?.focus();
    }
    if (event.key === 'Tab') floating.current?.setOpen(false);
  }}>
    <button type="button" class="splitmain geist-button" onClick={() => run(actions[0])}>{glyph(actions[0].icon)}{actions[0].label}</button>
    <button type="button" class="splittoggle" aria-label={label} aria-haspopup="menu" aria-expanded="false" aria-controls={id}>{glyph('chevron-down')}</button>
    <div class="popmenu cardmenupanel" id={id} role="menu" hidden>
      {actions.map(action => <button key={action.label} type="button" role="menuitem" onClick={() => run(action)}>{glyph(action.icon)}<span>{action.label}</span></button>)}
    </div>
  </div>;
}
