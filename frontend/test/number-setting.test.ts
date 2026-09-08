import { beforeEach, expect, it, vi } from 'vitest';
import { boundedPreference, mountNumberSetting, syncNumberSetting } from '../src/number-setting';

beforeEach(()=>{document.body.replaceChildren();localStorage.clear()});
function setup(value=10){const node=document.createElement('div');document.body.append(node);const apply=vi.fn();mountNumberSetting(node,'searchHistoryLimitSetting','搜索记录',value,apply);return {node,apply,input:node.querySelector<HTMLInputElement>('input[type=number]')!,toggle:node.querySelector<HTMLInputElement>('[role=switch]')!}}
it('rejects invalid numbers without saving and clears feedback after correction',()=>{
  const {node,input,apply}=setup();input.value='51';input.dispatchEvent(new Event('change'));
  expect(apply).not.toHaveBeenCalled();expect(input.getAttribute('aria-invalid')).toBe('true');
  expect(node.querySelector<HTMLElement>('[role=status]')!.hidden).toBe(false);
  input.value='17';input.dispatchEvent(new Event('change'));expect(apply).toHaveBeenLastCalledWith('17');expect(input.hasAttribute('aria-invalid')).toBe(false);
});
it('disabling hides the field and enabling restores its last valid number',()=>{
  const {node,input,toggle,apply}=setup();input.value='23';input.dispatchEvent(new Event('change'));
  toggle.checked=false;toggle.dispatchEvent(new Event('change'));expect(apply).toHaveBeenLastCalledWith('0');expect(node.querySelector<HTMLElement>('.board-number-fields')!.hidden).toBe(true);
  toggle.checked=true;toggle.dispatchEvent(new Event('change'));expect(input.value).toBe('23');expect(apply).toHaveBeenLastCalledWith('23');
});
it('bounds stored values and rejects fractional preferences',()=>{expect(boundedPreference(0,0,50,10)).toBe(0);expect(boundedPreference(2.5,1,50,10)).toBe(10);expect(boundedPreference(99,1,50,10)).toBe(10)});
it('restores a value received asynchronously after toggling off and on',()=>{
  const {node,input,toggle,apply}=setup();syncNumberSetting(node,37,false);
  toggle.checked=false;toggle.dispatchEvent(new Event('change'));
  toggle.checked=true;toggle.dispatchEvent(new Event('change'));
  expect(input.value).toBe('37');expect(apply).toHaveBeenLastCalledWith('37');
});
