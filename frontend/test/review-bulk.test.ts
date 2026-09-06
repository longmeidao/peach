import { afterEach, expect, it, vi } from 'vitest';
import { applyReviewSelection, commonReviewSources, createReviewSelection, wireReviewSelection } from '../src/review-bulk';

afterEach(() => { document.body.innerHTML = ''; });
it('逐项采用保留失败项，重试仅提交失败项', async () => {
  const items = ['one', 'two', 'three'].map(key => ({ key, payload: { item_key: key, candidate_key: `${key}-nfo`, selected_ids: [2] } }));
  const submit = vi.fn(async payload => { if (payload.item_key === 'two') throw new Error('来源不可达'); return { ok: true }; });
  const applied = vi.fn();
  const result = await applyReviewSelection(items, submit, applied, () => true);
  expect(result).toEqual({ completed: 2, failures: [{ key: 'two', message: '来源不可达' }] });
  expect(applied.mock.calls.flat()).toEqual(['one', 'three']);
  const retry = vi.fn(async () => ({ ok: true }));
  await applyReviewSelection(items.filter(item => result.failures.some(failure => failure.key === item.key)), retry, applied, () => true);
  expect(retry).toHaveBeenCalledExactlyOnceWith(items[1]!.payload);
});

it('离开页面后停止提交后续项', async () => {
  let active = true;
  const submit = vi.fn(async () => { active = false; return { ok: true }; });
  const applied = vi.fn();
  await applyReviewSelection([{ key: 'a', payload: {} }, { key: 'b', payload: {} }], submit, applied, () => active);
  expect(submit).toHaveBeenCalledTimes(1);
  expect(applied).toHaveBeenCalledExactlyOnceWith('a');
});

function fixture(locked = false) {
  const state = createReviewSelection();
  const root = document.createElement('div'); document.body.append(root);
  const rows = [{ item_key: 'one', candidates: [{ candidate_key: 'one-nfo', source: 'local_nfo' }] }, { item_key: 'two', candidates: [{ candidate_key: 'two-nfo', source: 'local_nfo' }, { candidate_key: 'two-api', source: 'api' }] }];
  const submit = vi.fn(async (_payload: Record<string, unknown>) => ({ ok: true }));
  const notify = vi.fn();
  const render = () => {
    root.innerHTML = `<div class="reviewlist">${rows.map(row => `<fieldset data-review-key="${row.item_key}">${row.candidates.map(candidate => `<input type="radio" name="metadata-${row.item_key}" value="${candidate.candidate_key}" ${row.candidates.length === 1 ? 'checked' : ''}>`).join('')}<button data-review-status="approved">通过</button><span class="reviewstate"></span></fieldset>`).join('')}</div>`;
    wireReviewSelection(root, { rows, metadata: true, locked, state, payload: card => ({ item_key: card.dataset.reviewKey, candidate_key: card.querySelector<HTMLInputElement>('input[type="radio"]:checked')?.value || '' }), submit, applied: key => { rows.splice(rows.findIndex(row => row.item_key === key), 1); }, active: () => root.isConnected, refresh: render, notify });
  };
  render();
  const button = (text: string, scope: ParentNode = root) => [...scope.querySelectorAll<HTMLButtonElement>('button')].find(item => item.textContent?.startsWith(text))!;
  return { root, state, rows, submit, notify, render, button };
}

it('多来源先明确选择，失败后保持选择与错误，再次采用成功后移出队列', async () => {
  const f = fixture();
  f.button('多选').click();
  const group = [...f.root.querySelectorAll('.reviewgroup')].find(item => item.textContent?.includes('需选择来源'))!;
  f.button('全选本组', group).click();
  f.button('采用所选', group).click();
  expect(f.submit).not.toHaveBeenCalled();
  expect(group.textContent).toContain('请先为所选的多来源候选选择来源');
  const radio = group.querySelector<HTMLInputElement>('input[value="two-api"]')!;
  radio.click();
  f.submit.mockResolvedValueOnce({ ok: false });
  f.button('采用所选', group).click();
  await vi.waitFor(() => expect(f.notify).toHaveBeenCalledTimes(1));
  expect(f.state.selected.has('two')).toBe(true);
  expect(f.root.querySelector<HTMLInputElement>('input[value="two-api"]')?.checked).toBe(true);
  expect(f.root.textContent).toContain('服务端未采用该项');
  f.button('采用所选（1）').click();
  await vi.waitFor(() => expect(f.rows.map(row => row.item_key)).toEqual(['one']));
  expect(f.submit.mock.calls.map(call => call[0])).toEqual(Array(2).fill({ item_key: 'two', candidate_key: 'two-api', status: 'approved' }));
  f.button('退出多选').click();
  expect(f.state.active).toBe(false);
  expect(f.state.selected.size).toBe(0);
});

it('单一候选可整组采用，只读端不提供批量操作', async () => {
  const f = fixture();
  f.button('多选').click();
  const group = f.root.querySelector('.reviewgroup')!;
  f.button('全选本组', group).click(); f.button('采用所选', group).click();
  await vi.waitFor(() => expect(f.rows).toHaveLength(1));
  expect(f.submit).toHaveBeenCalledExactlyOnceWith({ item_key: 'one', candidate_key: 'one-nfo', status: 'approved' });
  const reader = fixture(true);
  expect(reader.root.querySelector('.reviewbulkbar')).toBeNull();
});

it('跨组统一来源只选择对应候选，统一通过才提交', async () => {
  const f = fixture(); f.button('多选').click(); f.button('全选本页').click();
  const source = f.root.querySelector('.reviewbulksource .gselect') as HTMLElement & {value: string};
  source.value = 'local_nfo'; source.dispatchEvent(new Event('change'));
  expect(f.submit).not.toHaveBeenCalled();
  expect([...f.state.choices.values()]).toEqual(['one-nfo', 'two-nfo']);
  f.button('通过所选').click();
  await vi.waitFor(() => expect(f.rows).toHaveLength(0));
  expect(f.submit.mock.calls.map(call => call[0].candidate_key)).toEqual(['one-nfo', 'two-nfo']);
});

it('统一拒绝不需要选择来源', async () => {
  const f = fixture(); f.button('多选').click(); f.button('全选本页').click(); f.button('拒绝所选').click();
  await vi.waitFor(() => expect(f.rows).toHaveLength(0));
  expect(f.submit.mock.calls.map(call => call[0].status)).toEqual(['rejected', 'rejected']);
});

it('共同来源排除缺失与同来源多候选的歧义', () => {
  expect(commonReviewSources([])).toEqual([]);
  expect(commonReviewSources([{item_key:'a', candidates:[{candidate_key:'1',source:'nfo'}, {candidate_key:'2',source:'nfo'}]}])).toEqual([]);
  expect(commonReviewSources([{item_key:'a', candidates:[{candidate_key:'1',source:'nfo'}]}, {item_key:'b',candidates:[]}])).toEqual([]);
});
