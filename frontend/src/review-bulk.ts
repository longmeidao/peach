import { checkboxHtml, setActionBusy } from '@peach/legacy/ui';
import { errorMessage } from './api';

export interface ReviewRow { item_key: string; candidates?: { candidate_key: string }[] }
export const createReviewSelection = () => ({ active: false, busy: false, selected: new Set<string>(), choices: new Map<string, string>(), assets: new Map<string, number[]>(), errors: new Map<string, string>() });
type Selection = ReturnType<typeof createReviewSelection>;
type Payload = Record<string, unknown>;
export async function applyReviewSelection(items: { key: string; payload: Payload }[], submit: (payload: Payload) => Promise<{ ok: boolean; error?: string }>, applied: (key: string) => void, active: () => boolean) {
  const failures: { key: string; message: string }[] = [];
  let completed = 0;
  for (const item of items) {
    if (!active()) break;
    try {
      const result = await submit(item.payload);
      if (!result.ok) throw new Error(result.error || '服务端未采用该项');
      completed++; applied(item.key);
    } catch (error) { failures.push({ key: item.key, message: errorMessage(error) }); }
  }
  return { completed, failures };
}

export function wireReviewSelection(root: HTMLElement, options: {
  rows: ReviewRow[]; metadata: boolean; locked: boolean; state: Selection;
  payload(item: HTMLElement): Payload;
  submit(payload: Payload): Promise<{ ok: boolean; error?: string }>;
  applied(key: string): void; active(): boolean; refresh(): void; notify(message: string): void;
}) {
  const list = root.querySelector<HTMLElement>('.reviewlist');
  if (!list || !options.rows.length || options.locked) return;
  const state = options.state;
  const cards = [...list.querySelectorAll<HTMLElement>('[data-review-key]')];
  const toolbar = document.createElement('div'); toolbar.className = 'reviewbulkbar';
  const toggle = document.createElement('button'); toggle.className = 'geist-button'; toggle.type = 'button';
  toolbar.append(toggle); list.before(toolbar);
  const groups = options.metadata ? [
    { title: '单一候选', cards: cards.filter(card => (options.rows.find(row => row.item_key === card.dataset.reviewKey)?.candidates?.length || 0) === 1) },
    { title: '需选择来源', cards: cards.filter(card => (options.rows.find(row => row.item_key === card.dataset.reviewKey)?.candidates?.length || 0) !== 1) },
  ] : [{ title: '待复核', cards }];
  list.classList.add('reviewgroups');
  const eligible = (card: HTMLElement) => !card.querySelector<HTMLButtonElement>('[data-review-status="approved"]')?.disabled;
  const controls: (() => void)[] = [];
  for (const group of groups.filter(group => group.cards.length)) {
    const section = document.createElement('section'); section.className = 'reviewgroup';
    const bar = document.createElement('div'); bar.className = 'reviewbulkbar';
    const title = document.createElement('h3'); title.textContent = `${group.title} · ${group.cards.length}`;
    const select = document.createElement('button'); select.className = 'geist-button'; select.type = 'button';
    const apply = document.createElement('button'); apply.className = 'geist-button'; apply.type = 'button';
    const feedback = document.createElement('p'); feedback.className = 'reviewstate'; feedback.setAttribute('role', 'status');
    const grid = document.createElement('div'); grid.className = 'reviewlist';
    bar.append(title, select, apply); section.append(bar, feedback, grid); list.append(section);
    for (const card of group.cards) {
      grid.append(card);
      const key = card.dataset.reviewKey!;
      const canApprove = eligible(card);
      if (state.errors.has(key)) card.querySelector<HTMLElement>('.reviewstate')!.textContent = state.errors.get(key)!;
      const label = document.createElement('label'); label.className = 'reviewpickitem';
      label.innerHTML = checkboxHtml('aria-label="选择此复核项"') + '<span>选择此项</span>';
      const input = label.querySelector<HTMLInputElement>('input')!;
      card.prepend(label);
      if (state.assets.has(key)) {
        const selected = state.assets.get(key)!;
        const cells = [...card.querySelectorAll<HTMLElement>('[data-review-asset]')];
        cells.forEach(cell => { const on = selected.includes(Number(cell.dataset.reviewAsset)); cell.setAttribute('aria-pressed', String(on)); cell.classList.toggle('picked', on); });
        const count = card.querySelector<HTMLElement>('[data-picked-count]');
        if (count) count.textContent = `已选 ${selected.length} / ${cells.length}`;
      }
      card.addEventListener('click', event => {
        if ((event.target as Element).closest('[data-review-asset],[data-pick-all],[data-pick-none]')) state.assets.set(key,
          [...card.querySelectorAll<HTMLElement>('[data-review-asset][aria-pressed="true"]')].map(cell => Number(cell.dataset.reviewAsset)));
      });
      for (const radio of card.querySelectorAll<HTMLInputElement>('input[type="radio"]')) {
        if (state.choices.has(key)) radio.checked = state.choices.get(key) === radio.value;
        radio.addEventListener('change', () => { if (radio.checked) state.choices.set(key, radio.value); });
      }
      input.onchange = () => { if (input.checked) state.selected.add(key); else state.selected.delete(key); update(); };
      controls.push(() => { label.hidden = !state.active; input.checked = state.selected.has(key); input.disabled = !canApprove; });
    }
    const chosen = () => group.cards.filter(card => state.selected.has(card.dataset.reviewKey!) && eligible(card));
    controls.push(() => {
      select.hidden = apply.hidden = !state.active;
      select.textContent = chosen().length && chosen().length === group.cards.filter(eligible).length ? '清空本组' : '全选本组';
      apply.textContent = `采用所选${chosen().length ? `（${chosen().length}）` : ''}`;
      apply.disabled = !chosen().length; select.disabled = !group.cards.some(eligible);
    });
    select.onclick = () => { if (state.busy) return; const available = group.cards.filter(eligible); const all = chosen().length === available.length; available.forEach(card => all ? state.selected.delete(card.dataset.reviewKey!) : state.selected.add(card.dataset.reviewKey!)); update(); };
    apply.onclick = async () => {
      if (state.busy || !chosen().length) return;
      const items = chosen().map(card => ({ key: card.dataset.reviewKey!, payload: options.payload(card) }));
      if (options.metadata && items.some(item => !item.payload.candidate_key)) {
        feedback.textContent = '请先为所选的多来源候选选择来源。';
        chosen().find(card => !card.querySelector('input[type="radio"]:checked'))?.querySelector<HTMLInputElement>('input[type="radio"]')?.focus();
        return;
      }
      state.busy = true; feedback.textContent = `正在采用 0 / ${items.length}`; update(); setActionBusy(apply, true);
      const inputs = [...root.querySelectorAll<HTMLInputElement | HTMLButtonElement>('button,input')];
      const disabled = inputs.map(input => input.getAttribute('aria-disabled')); inputs.forEach(input => { input.setAttribute('aria-disabled', 'true'); });
      const block = (event: Event) => { if (event instanceof KeyboardEvent && event.key === 'Tab') return; event.preventDefault(); event.stopImmediatePropagation(); };
      root.addEventListener('click', block, true); root.addEventListener('keydown', block, true);
      let checked = 0;
      const result = await applyReviewSelection(items, async payload => {
        try { return await options.submit(payload); }
        finally { checked++; if (options.active()) feedback.textContent = `正在采用 ${checked} / ${items.length}`; }
      }, key => { state.selected.delete(key); state.errors.delete(key); options.applied(key); }, options.active);
      state.busy = false;
      root.removeEventListener('click', block, true); root.removeEventListener('keydown', block, true);
      inputs.forEach((input, index) => { const value = disabled[index]; if (value === null) input.removeAttribute('aria-disabled'); else input.setAttribute('aria-disabled', value!); });
      setActionBusy(apply, false);
      if (!options.active()) return;
      options.notify(`已采用 ${result.completed} 项${result.failures.length ? `，${result.failures.length} 项未完成` : ''}`);
      result.failures.forEach(item => state.errors.set(item.key, item.message));
      const host = root.parentElement;
      options.refresh();
      host?.querySelector<HTMLButtonElement>('.reviewbulkbar button')?.focus({ preventScroll: true });
    };
  }
  function update() { toggle.textContent = state.active ? '退出多选' : '多选'; toggle.setAttribute('aria-pressed', String(state.active)); controls.forEach(control => control()); }
  toggle.onclick = () => { if (state.busy) return; state.active = !state.active; if (!state.active) state.selected.clear(); update(); };
  update();
}
