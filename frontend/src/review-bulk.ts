import { checkboxHtml, setActionBusy, selectFieldHtml, wireSelectField } from '@peach/legacy/ui';
import { errorMessage } from './api';

export interface ReviewRow { item_key: string; field?: string; field_label?: string; source?: string; candidates?: { candidate_key: string; source?: string }[] }
export type ReviewGrouping = 'candidates' | 'source' | 'field';
export const createReviewSelection = () => ({ busy: false, category: '', filter: '', groupBy: 'candidates' as ReviewGrouping, anchor: null as string | null, selected: new Set<string>(), choices: new Map<string, string>(), assets: new Map<string, number[]>(), errors: new Map<string, string>() });
type Selection = ReturnType<typeof createReviewSelection>;
type Payload = Record<string, unknown>;

export function updateReviewSticky(root: HTMLElement | null) {
  const controls = root?.querySelector<HTMLElement>('.reviewbulktoolbar');
  if (!root || !controls || controls.offsetParent === null) return;
  root.style.setProperty('--review-controls-height', `${controls.getBoundingClientRect().height}px`);
  const bars = [controls, ...root.querySelectorAll<HTMLElement>('.reviewgroupbar')];
  for (const bar of bars) {
    const top = parseFloat(getComputedStyle(bar).top);
    bar.classList.toggle('is-stuck', bar.offsetParent !== null && window.scrollY > 0 &&
      Number.isFinite(top) && Math.abs(bar.getBoundingClientRect().top - top) <= 1);
  }
  /* 粘住的那几行合成一块玻璃，由 `.review::before` 画。每行各挂一层 backdrop-filter 的话，
     每层只糊自己身后那一段页面，两行相接处就显出两种颜色，读起来是上下两个框。 */
  const stuck = bars.filter(bar => bar.classList.contains('is-stuck'));
  root.classList.toggle('review-is-stuck', stuck.length > 0);
  if (!stuck.length) return;
  const head = stuck[0].getBoundingClientRect(), foot = stuck[stuck.length - 1].getBoundingClientRect();
  root.style.setProperty('--review-pane-left', `${head.left}px`);
  root.style.setProperty('--review-pane-width', `${head.width}px`);
  root.style.setProperty('--review-pane-height', `${foot.bottom - head.top}px`);
}

export function reviewGroupingOptions(rows: ReviewRow[], metadata: boolean): string[][] {
  const options = [['candidates', metadata ? '按候选数量' : '全部待复核', 'list-filter']];
  if (rows.some(row => row.source || row.candidates?.some(candidate => candidate.source))) options.push(['source', '按来源', 'list-filter']);
  if (rows.some(row => row.field)) options.push(['field', '按字段', 'list-filter']);
  return options;
}

/** 按来源组合分组，每个作品字段只出现一次。 */
export function groupReviewRows(rows: ReviewRow[], by: ReviewGrouping) {
  const groups = new Map<string, { key: string; title: string; rows: ReviewRow[] }>();
  for (const row of rows) {
    let key: string, title: string;
    if (by === 'field') { key = row.field || '__unspecified_field'; title = row.field_label || row.field || '未标注字段'; }
    else if (by === 'source') {
      const sources = [...new Set((row.candidates?.map(candidate => candidate.source || '') || [row.source || '']).filter(Boolean))].sort();
      key = JSON.stringify(sources); title = sources.join(' / ') || '未标注来源';
    } else {
      key = row.candidates ? row.candidates.length === 1 ? 'single' : 'multiple' : 'pending';
      title = key === 'single' ? '单一候选' : key === 'multiple' ? '需选择来源' : '待复核';
    }
    if (!groups.has(key)) groups.set(key, { key, title, rows: [] });
    groups.get(key)!.rows.push(row);
  }
  return [...groups.values()];
}

/** Shift 使用当前显示顺序，与馆藏页相同地扩展选择范围。 */
export function selectReviewRange(state: Selection, keys: string[], key: string, range: boolean, checked: boolean) {
  const first = state.anchor === null ? -1 : keys.indexOf(state.anchor), last = keys.indexOf(key);
  if (range && first >= 0 && last >= 0) {
    keys.slice(Math.min(first, last), Math.max(first, last) + 1).forEach(value => state.selected.add(value));
  } else if (checked) state.selected.add(key); else state.selected.delete(key);
  state.anchor = key;
}

export async function applyReviewSelection(items: { key: string; payload: Payload }[], submit: (payload: Payload) => Promise<{ ok: boolean; error?: string }>, applied: (key: string) => void, active: () => boolean) {
  const failures: { key: string; message: string }[] = []; let completed = 0;
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

export function commonReviewSources(rows: ReviewRow[]): string[] {
  if (!rows.length) return [];
  return [...new Set(rows.flatMap(row => row.candidates?.map(candidate => candidate.source || '') || []))]
    .filter(source => source && rows.every(row => row.candidates?.filter(candidate => candidate.source === source).length === 1));
}

export function wireReviewSelection(root: HTMLElement, options: {
  rows: ReviewRow[]; catalog?: ReviewRow[]; metadata: boolean; category?: string; locked: boolean; state: Selection;
  payload(item: HTMLElement): Payload; submit(payload: Payload): Promise<{ ok: boolean; error?: string }>;
  applied(key: string): void; active(): boolean; refresh(): void; notify(message: string): void;
}) {
  const list = root.querySelector<HTMLElement>('.reviewlist');
  if (!list || !options.rows.length || options.locked) return;
  const state = options.state, cards = [...list.querySelectorAll<HTMLElement>('[data-review-key]')];
  if (options.category !== undefined && state.category !== options.category) {
    state.category = options.category; state.filter = ''; state.groupBy = 'candidates'; state.anchor = null;
  }
  // 分组方式和筛选项按整条队列算，卡片只画当前这一页：筛选里的计数说的是队列，不是这一屏。
  const catalog = options.catalog || options.rows;
  const groupOptions = reviewGroupingOptions(catalog, options.metadata);
  if (!groupOptions.some(option => option[0] === state.groupBy)) { state.groupBy = 'candidates'; state.filter = ''; }
  const groups = groupReviewRows(catalog, state.groupBy);
  if (!groups.some(group => group.key === state.filter)) state.filter = '';
  const visible = () => [...list.querySelectorAll<HTMLElement>('[data-review-key]')].filter(card => !card.closest('[hidden]'));
  const selected = () => visible().filter(card => state.selected.has(card.dataset.reviewKey!));
  const selectedRows = () => options.rows.filter(row => selected().some(card => card.dataset.reviewKey === row.item_key));
  const eligible = (card: HTMLElement) => !card.querySelector<HTMLButtonElement>('[data-review-status="approved"]')?.disabled;
  const button = (text: string, variant = '') => { const control = document.createElement('button'); control.type = 'button'; control.className = `geist-button ${variant}`.trim(); control.textContent = text; return control; };
  const toolbar = document.createElement('div'); toolbar.className = 'reviewbulkbar reviewbulktoolbar'; toolbar.setAttribute('role', 'group'); toolbar.setAttribute('aria-label', '复核批量操作');
  const grouping = document.createElement('div'); grouping.className = 'reviewgroupby';
  grouping.innerHTML = selectFieldHtml(groupOptions, state.groupBy, { label: '筛选分组方式' });
  const groupField = wireSelectField(grouping.firstElementChild!);
  grouping.querySelectorAll('[data-select-option] .gselectmark').forEach(mark => mark.remove());
  groupField.addEventListener('change', () => { if (state.busy || !groupOptions.some(option => option[0] === groupField.value)) return; state.groupBy = groupField.value as ReviewGrouping; state.filter = ''; state.anchor = null; const host = root.parentElement; options.refresh(); host?.querySelector<HTMLButtonElement>('.reviewgroupby button')?.focus({ preventScroll: true }); });
  const filter = document.createElement('div'); filter.className = 'reviewcategoryfilter'; filter.hidden = groups.length < 2;
  filter.innerHTML = selectFieldHtml([['', '全部分类', 'list-filter'], ...groups.map(group => [group.key, `${group.title} · ${group.rows.length}`, 'list-filter'])], state.filter, { label: state.groupBy === 'field' ? '筛选字段分类' : '筛选当前分类' });
  const filterMenu = filter.querySelector('[data-select-menu]');
  if (filterMenu) {
    const section = document.createElement('div'); section.setAttribute('role', 'group'); section.setAttribute('aria-label', state.groupBy === 'field' ? '字段分类' : '当前分类');
    const title = document.createElement('div'); title.className = 'reviewfilterheading'; title.textContent = section.getAttribute('aria-label'); title.setAttribute('aria-hidden', 'true');
    section.append(title, ...Array.from(filterMenu.children).slice(1)); filterMenu.append(section);
  }
  const filterField = wireSelectField(filter.firstElementChild!);
  filter.querySelectorAll('[data-select-option] .gselectmark').forEach(mark => mark.remove());
  filterField.addEventListener('change', () => { if (state.busy || (filterField.value && !groups.some(group => group.key === filterField.value))) return; state.filter = filterField.value; state.anchor = null; const host = root.parentElement; options.refresh(); host?.querySelector<HTMLButtonElement>('.reviewcategoryfilter button')?.focus({ preventScroll: true }); });
  const all = button('全选本页'), approve = button('通过所选', 'primary'), reject = button('拒绝所选', 'error');
  const count = document.createElement('span'); count.className = 'reviewselectedcount selectiondockcount'; count.setAttribute('role', 'status');
  const source = document.createElement('div'); source.className = 'reviewbulksource'; source.hidden = !options.metadata;
  const feedback = document.createElement('p'); feedback.className = 'reviewstate reviewbulkfeedback'; feedback.setAttribute('role', 'status');
  const decisions = document.createElement('div'); decisions.className = 'reviewbulkdecisions'; decisions.append(approve, reject);
  const dock = document.createElement('div'); dock.className = 'selectiondock reviewdock'; dock.setAttribute('role', 'group'); dock.setAttribute('aria-label', '复核所选项目');
  const cancel = button('取消选择'); dock.append(count, source, decisions, cancel, feedback);
  toolbar.append(grouping, filter, all);
  const context = root.querySelector('.reviewcontrols');
  if (context) context.after(toolbar); else list.before(toolbar);
  root.append(dock); list.classList.add('reviewgroups');
  const clear = () => { state.selected.clear(); state.anchor = null; update(); };
  cancel.onclick = () => { if (!state.busy) { clear(); all.focus({preventScroll:true}); } };
  all.onclick = () => { if (state.busy) return; const shown = visible(), checked = selected().length === shown.length; shown.forEach(card => checked ? state.selected.delete(card.dataset.reviewKey!) : state.selected.add(card.dataset.reviewKey!)); update(); };
  approve.onclick = () => run('approved', approve); reject.onclick = () => run('rejected', reject);
  const controls: (() => void)[] = [];
  for (const group of groups) {
    const groupCards = group.rows.map(row => cards.find(card => card.dataset.reviewKey === row.item_key)).filter((card): card is HTMLElement => !!card);
    // 这一页上一张都没有的组不画分组条：条子底下空着，读起来像加载坏了。
    if (!groupCards.length) continue;
    const section = document.createElement('section'); section.className = 'reviewgroup';
    section.hidden = !!state.filter && group.key !== state.filter;
    const bar = document.createElement('div'); bar.className = 'reviewbulkbar reviewgroupbar';
    const title = document.createElement('h3'); title.textContent = `${group.title} · ${groupCards.length}`;
    const select = button('全选本组'), grid = document.createElement('div'); grid.className = 'reviewlist';
    bar.append(title, select); section.append(bar, grid); list.append(section);
    select.onclick = () => { if (state.busy) return; const all = groupCards.every(card => state.selected.has(card.dataset.reviewKey!)); groupCards.forEach(card => all ? state.selected.delete(card.dataset.reviewKey!) : state.selected.add(card.dataset.reviewKey!)); update(); };
    controls.push(() => { select.textContent = groupCards.every(card => state.selected.has(card.dataset.reviewKey!)) ? '清空本组' : '全选本组'; });
    for (const card of groupCards) {
      grid.append(card); const key = card.dataset.reviewKey!;
      if (state.errors.has(key)) card.querySelector<HTMLElement>('.reviewstate')!.textContent = state.errors.get(key)!;
      const heading = card.querySelector<HTMLElement>('h4,.reviewentity b') || card;
      const label = document.createElement('label'); label.className = 'reviewpickitem'; label.innerHTML = checkboxHtml();
      const input = label.querySelector<HTMLInputElement>('input')!;
      input.setAttribute('aria-label', `选择 ${card.querySelector('legend')?.textContent || heading.textContent || key}`);
      if (heading !== card) {
        const name = document.createElement('span'); name.className = 'reviewpickname'; name.append(...heading.childNodes); heading.classList.add('reviewpickheading'); heading.append(label, name);
      } else card.prepend(label);
      const pick = (range: boolean, checked: boolean) => { selectReviewRange(state, visible().map(card => card.dataset.reviewKey!), key, range, checked); update(); };
      label.addEventListener('mousedown', event => { if (event.shiftKey) event.preventDefault(); });
      label.addEventListener('click', event => { if (event.target === input) return; event.preventDefault(); if (!state.busy) { input.focus(); pick(event.shiftKey, !input.checked); } });
      input.addEventListener('click', event => { if (state.busy) return; pick(event.shiftKey, input.checked); });
      input.addEventListener('keydown', event => {
        if (state.busy || !event.shiftKey) return;
        if (event.key === ' ') { event.preventDefault(); pick(true, true); }
        else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          event.preventDefault(); const shown = visible(), index = shown.indexOf(card) + (event.key === 'ArrowDown' ? 1 : -1), next = shown[index];
          if (next) { if (state.anchor === null) state.anchor = key; selectReviewRange(state, shown.map(card => card.dataset.reviewKey!), next.dataset.reviewKey!, true, true); update(); next.querySelector<HTMLInputElement>('.reviewpickitem input')?.focus(); }
        }
      });
      controls.push(() => { input.checked = state.selected.has(key); });
      if (state.assets.has(key)) {
        const selected = state.assets.get(key)!, cells = [...card.querySelectorAll<HTMLElement>('[data-review-asset]')];
        cells.forEach(cell => { const on = selected.includes(Number(cell.dataset.reviewAsset)); cell.setAttribute('aria-pressed', String(on)); cell.classList.toggle('picked', on); });
        const count = card.querySelector<HTMLElement>('[data-picked-count]'); if (count) count.textContent = `已选 ${selected.length} / ${cells.length}`;
      }
      card.addEventListener('click', event => { if ((event.target as Element).closest('[data-review-asset],[data-pick-all],[data-pick-none]')) state.assets.set(key, [...card.querySelectorAll<HTMLElement>('[data-review-asset][aria-pressed="true"]')].map(cell => Number(cell.dataset.reviewAsset))); });
      for (const radio of card.querySelectorAll<HTMLInputElement>('input[type="radio"]')) {
        if (state.choices.has(key)) radio.checked = state.choices.get(key) === radio.value;
        radio.addEventListener('change', () => { if (radio.checked) state.choices.set(key, radio.value); update(); });
      }
    }
  }
  root.addEventListener('keydown', event => {
    if (state.busy || !root.contains(list)) return;
    if (event.key === 'Escape' && state.selected.size) { event.preventDefault(); event.stopPropagation(); clear(); }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'a' && !(event.target as Element).matches('textarea,input:not([type="checkbox"]):not([type="radio"])')) { event.preventDefault(); event.stopPropagation(); visible().forEach(card => state.selected.add(card.dataset.reviewKey!)); update(); }
  });
  let sourceSignature = '';
  function update() {
    const chosen = selected(); all.textContent = chosen.length === visible().length ? '清空当前选择' : state.filter ? '全选当前分类' : '全选本页';
    dock.hidden = !chosen.length;
    count.textContent = `已选 ${chosen.length} 项`;
    approve.disabled = !chosen.length || chosen.some(card => !eligible(card)); reject.disabled = !chosen.length;
    const sources = commonReviewSources(selectedRows());
    source.hidden = !options.metadata || !selectedRows().some(row => (row.candidates?.length || 0) > 1);
    const label = chosen.length && !sources.length ? '所选项目无共同来源' : '统一选择来源';
    const signature = JSON.stringify([label, sources]);
    if (signature !== sourceSignature) {
      sourceSignature = signature;
      source.innerHTML = selectFieldHtml([['', label], ...sources.map(value => [value, value])], '', { label: '统一选择来源' });
      const field = wireSelectField(source.firstElementChild!); field.disabled = !sources.length;
      field.addEventListener('change', () => {
        if (state.busy || !commonReviewSources(selectedRows()).includes(field.value)) return;
        for (const card of selected()) {
          const candidate = options.rows.find(row => row.item_key === card.dataset.reviewKey)!.candidates!.find(candidate => candidate.source === field.value)!;
          card.querySelectorAll<HTMLInputElement>('input[type="radio"]').forEach(radio => { radio.checked = radio.value === candidate.candidate_key; }); state.choices.set(card.dataset.reviewKey!, candidate.candidate_key);
        }
        feedback.textContent = `已选择 ${field.value}，点击通过所选采用。`;
      });
    }
    controls.forEach(control => control());
  }
  async function run(status: 'approved' | 'rejected', trigger: HTMLButtonElement) {
    if (state.busy || !selected().length) return;
    const items: { key: string; payload: Payload }[] = selected().map(card => ({ key: card.dataset.reviewKey!, payload: { ...options.payload(card), status } }));
    if (status === 'approved' && options.metadata && items.some(item => !item.payload.candidate_key)) {
      feedback.textContent = '请先为所选的多来源候选选择来源。'; selected().find(card => !card.querySelector('input[type="radio"]:checked'))?.querySelector<HTMLInputElement>('input[type="radio"]')?.focus(); return;
    }
    state.busy = true; feedback.textContent = `正在处理 0 / ${items.length}`; setActionBusy(trigger, true);
    const inputs = [...root.querySelectorAll<HTMLElement>('button,input')], disabled = inputs.map(input => input.getAttribute('aria-disabled')); inputs.forEach(input => input.setAttribute('aria-disabled', 'true'));
    const block = (event: Event) => { if (event instanceof KeyboardEvent && event.key === 'Tab') return; event.preventDefault(); event.stopImmediatePropagation(); };
    root.addEventListener('click', block, true); root.addEventListener('keydown', block, true);
    let checked = 0;
    const result = await applyReviewSelection(items, async payload => { try { return await options.submit(payload); } finally { checked++; if (options.active()) feedback.textContent = `正在处理 ${checked} / ${items.length}`; } }, key => { state.selected.delete(key); state.errors.delete(key); options.applied(key); }, options.active);
    state.busy = false; root.removeEventListener('click', block, true); root.removeEventListener('keydown', block, true);
    inputs.forEach((input, index) => { const value = disabled[index]; if (value === null) input.removeAttribute('aria-disabled'); else input.setAttribute('aria-disabled', value!); }); setActionBusy(trigger, false);
    if (!options.active()) return;
    options.notify(`已${status === 'approved' ? '通过' : '拒绝'} ${result.completed} 项${result.failures.length ? `，${result.failures.length} 项未完成` : ''}`);
    result.failures.forEach(item => state.errors.set(item.key, item.message)); const host = root.parentElement; options.refresh(); host?.querySelector<HTMLButtonElement>('.reviewbulktoolbar button')?.focus({ preventScroll: true });
  }
  update();
  updateReviewSticky(root);
}
