import { afterEach, expect, it, vi } from 'vitest';
import { applyReviewSelection, groupReviewRows, selectReviewRange, commonReviewSources, createReviewSelection, wireReviewSelection, reviewGroupingOptions } from '../src/review-bulk';

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
    root.innerHTML = `<div class="reviewcontrols"></div><div class="reviewlist">${rows.map(row => `<fieldset data-review-key="${row.item_key}"><h4>${row.item_key}</h4>${row.candidates.map(candidate => `<input type="radio" name="metadata-${row.item_key}" value="${candidate.candidate_key}" ${row.candidates.length === 1 ? 'checked' : ''}>`).join('')}<button data-review-status="approved">通过</button><span class="reviewstate"></span></fieldset>`).join('')}</div>`;
    wireReviewSelection(root, { rows, metadata: true, locked, state, payload: card => ({ item_key: card.dataset.reviewKey, candidate_key: card.querySelector<HTMLInputElement>('input[type="radio"]:checked')?.value || '' }), submit, applied: key => { rows.splice(rows.findIndex(row => row.item_key === key), 1); }, active: () => root.isConnected, refresh: render, notify });
  };
  render();
  const button = (text: string, scope: ParentNode = root) => [...scope.querySelectorAll<HTMLButtonElement>('button')].find(item => item.textContent?.startsWith(text))!;
  return { root, state, rows, submit, notify, render, button };
}

it('多来源先明确选择，失败后保持选择与错误，再次采用成功后移出队列', async () => {
  const f = fixture();
  const group = [...f.root.querySelectorAll('.reviewgroup')].find(item => item.textContent?.includes('需选择来源'))!;
  f.button('全选本组', group).click();
  f.button('通过所选').click();
  expect(f.submit).not.toHaveBeenCalled();
  expect(f.root.textContent).toContain('请先为所选的多来源候选选择来源');
  const radio = group.querySelector<HTMLInputElement>('input[value="two-api"]')!;
  radio.click();
  f.submit.mockResolvedValueOnce({ ok: false });
  f.button('通过所选').click();
  await vi.waitFor(() => expect(f.notify).toHaveBeenCalledTimes(1));
  expect(f.state.selected.has('two')).toBe(true);
  expect(f.root.querySelector<HTMLInputElement>('input[value="two-api"]')?.checked).toBe(true);
  expect(f.root.textContent).toContain('服务端未采用该项');
  f.button('通过所选').click();
  await vi.waitFor(() => expect(f.rows.map(row => row.item_key)).toEqual(['one']));
  expect(f.submit.mock.calls.map(call => call[0])).toEqual(Array(2).fill({ item_key: 'two', candidate_key: 'two-api', status: 'approved' }));
  f.root.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape',bubbles:true}));
  expect(f.state.selected.size).toBe(0);
});

it('单一候选可整组采用，只读端不提供批量操作', async () => {
  const f = fixture();
  const group = f.root.querySelector('.reviewgroup')!;
  f.button('全选本组', group).click(); f.button('通过所选').click();
  await vi.waitFor(() => expect(f.rows).toHaveLength(1));
  expect(f.submit).toHaveBeenCalledExactlyOnceWith({ item_key: 'one', candidate_key: 'one-nfo', status: 'approved' });
  const reader = fixture(true);
  expect(reader.root.querySelector('.reviewbulkbar')).toBeNull();
});

it('跨组统一来源只选择对应候选，统一通过才提交', async () => {
  const f = fixture(); f.button('全选本页').click();
  const source = f.root.querySelector('.reviewbulksource .gselect') as HTMLElement & {value: string};
  source.value = 'local_nfo'; source.dispatchEvent(new Event('change'));
  expect(f.submit).not.toHaveBeenCalled();
  expect([...f.state.choices.values()]).toEqual(['one-nfo', 'two-nfo']);
  f.button('通过所选').click();
  await vi.waitFor(() => expect(f.rows).toHaveLength(0));
  expect(f.submit.mock.calls.map(call => call[0].candidate_key)).toEqual(['one-nfo', 'two-nfo']);
});

it('统一拒绝不需要选择来源', async () => {
  const f = fixture(); f.button('全选本页').click(); f.button('拒绝所选').click();
  await vi.waitFor(() => expect(f.rows).toHaveLength(0));
  expect(f.submit.mock.calls.map(call => call[0].status)).toEqual(['rejected', 'rejected']);
});

it('共同来源排除缺失与同来源多候选的歧义', () => {
  expect(commonReviewSources([])).toEqual([]);
  expect(commonReviewSources([{item_key:'a', candidates:[{candidate_key:'1',source:'nfo'}, {candidate_key:'2',source:'nfo'}]}])).toEqual([]);
  expect(commonReviewSources([{item_key:'a', candidates:[{candidate_key:'1',source:'nfo'}]}, {item_key:'b',candidates:[]}])).toEqual([]);
});

it('默认勾选框位于名称前，数量使用共用文字样式，Shift 按显示顺序连选', () => {
  const f = fixture();
  expect(f.root.textContent).not.toContain('选择此项');
  expect(f.button('多选')).toBeUndefined();
  const inputs = [...f.root.querySelectorAll<HTMLInputElement>('.reviewpickitem input')];
  expect(inputs[0]!.closest('h4')?.firstElementChild?.className).toBe('reviewpickitem');
  inputs[0]!.click();
  inputs[1]!.closest('label')!.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, shiftKey:true}));
  expect([...f.state.selected]).toEqual(['one','two']);
  expect(f.root.querySelector('.selectiondockcount')?.textContent).toBe('已选 2 项');
  expect(f.root.querySelector('.selectiondockcount .geist-badge')).toBeNull();
  expect(f.root.querySelector('.reviewcontrols + .reviewbulktoolbar')).not.toBeNull();
  expect(f.button('通过所选').textContent).toBe('通过所选');
  f.root.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
  inputs[0]!.dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowDown', shiftKey:true, bubbles:true}));
  expect([...f.state.selected]).toEqual(['one','two']);
  expect(document.activeElement).toBe(inputs[1]);
});

it('来源和字段分组保留每一项且没有重复，切换分组保持勾选与候选', () => {
  const rows = [
    {item_key:'a',field:'title',field_label:'标题',candidates:[{candidate_key:'a',source:'nfo'}]},
    {item_key:'b',field:'performers',field_label:'演员',candidates:[{candidate_key:'b',source:'nfo'},{candidate_key:'b2',source:'api'}]},
    {item_key:'c',field:'title',field_label:'标题',candidates:[{candidate_key:'c',source:'api'},{candidate_key:'c2',source:'nfo'}]},
  ];
  expect(groupReviewRows(rows,'source').map(group=>[group.title,group.rows.map(row=>row.item_key)])).toEqual([['nfo',['a']],['api / nfo',['b','c']]]);
  expect(groupReviewRows(rows,'field').map(group=>[group.title,group.rows.map(row=>row.item_key)])).toEqual([['标题',['a','c']],['演员',['b']]]);
  const f = fixture(); f.button('全选本页').click();
  f.root.querySelector<HTMLInputElement>('input[value="two-api"]')!.click();
  const field = f.root.querySelector('.reviewgroupby .gselect') as HTMLElement & {value:string};
  field.value='source';field.dispatchEvent(new Event('change'));
  expect(f.state.groupBy).toBe('source');
  expect(f.root.querySelectorAll('.reviewpickitem input:checked')).toHaveLength(2);
  expect(f.root.querySelector<HTMLInputElement>('input[value="two-api"]')!.checked).toBe(true);
  expect(f.submit).not.toHaveBeenCalled();
});

it('Shift 范围使用分组后的显示顺序，普通取消只影响单项', () => {
  const state=createReviewSelection(),keys=['a','c','b','d'];
  selectReviewRange(state,keys,'c',false,true);
  selectReviewRange(state,keys,'d',true,true);
  expect([...state.selected]).toEqual(['c','b','d']);
  selectReviewRange(state,keys,'b',false,false);
  expect([...state.selected]).toEqual(['c','d']);
});

it('Shift 鼠标按下阻止文字选择且普通点击不受影响', () => {
  const f = fixture(), label = f.root.querySelector('.reviewpickitem')!;
  expect(label.dispatchEvent(new MouseEvent('mousedown', {bubbles:true,cancelable:true,shiftKey:true}))).toBe(false);
  expect(label.dispatchEvent(new MouseEvent('mousedown', {bubbles:true,cancelable:true}))).toBe(true);
});

it('选中项目时显示共用底部浮窗，取消后关闭且保留分类入口', () => {
  const f = fixture(), dock = f.root.querySelector<HTMLElement>('.selectiondock')!;
  expect(dock.hidden).toBe(true);
  f.button('全选本页').click();
  expect(dock.hidden).toBe(false);
  expect(dock.contains(f.button('通过所选'))).toBe(true);
  expect(dock.contains(f.button('拒绝所选'))).toBe(true);
  expect(dock.querySelector('.reviewbulksource')).not.toBeNull();
  expect(f.root.querySelector('.reviewbulktoolbar .reviewbulkdecisions')).toBeNull();
  f.button('取消选择').click();
  expect(f.state.selected.size).toBe(0); expect(dock.hidden).toBe(true);
  expect(document.activeElement).toBe(f.button('全选本页'));
  expect(f.root.querySelector('.reviewgroupby')).not.toBeNull();
});

it('分类筛选后全选和快捷键仅操作当前分类，清除筛选可恢复全部', () => {
  const f = fixture();
  const filter = f.root.querySelector('.reviewcategoryfilter .gselect') as HTMLElement & {value:string};
  filter.value = 'multiple'; filter.dispatchEvent(new Event('change'));
  f.button('全选当前分类').click();
  expect([...f.state.selected]).toEqual(['two']);
  f.button('清空当前选择').click();
  f.root.dispatchEvent(new KeyboardEvent('keydown', {key:'a',ctrlKey:true,bubbles:true}));
  expect([...f.state.selected]).toEqual(['two']);
  expect(f.root.querySelectorAll('.reviewgroup:not([hidden])')).toHaveLength(1);
  f.state.filter = ''; f.render();
  expect(f.root.querySelectorAll('.reviewgroup:not([hidden])')).toHaveLength(2);
});

it('分组菜单只提供当前类别的数据维度，失效字段筛选自动重置', () => {
  expect(reviewGroupingOptions([{item_key:'identity'}],false)).toEqual([['candidates','全部待复核','list-filter']]);
  expect(reviewGroupingOptions([{item_key:'field',field:'performers',source:'nfo'}],true).map(item=>item[0])).toEqual(['candidates','source','field']);
  const f = fixture(); f.state.groupBy = 'field'; f.state.filter = 'performers'; f.render();
  expect(f.state.groupBy).toBe('candidates'); expect(f.state.filter).toBe('');
  expect((f.root.querySelector('.reviewbulksource') as HTMLElement).hidden).toBe(true);
  f.button('全选本页').click();
  expect((f.root.querySelector('.reviewbulksource') as HTMLElement).hidden).toBe(false);
});
