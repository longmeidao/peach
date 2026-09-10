import { render } from 'preact';
import { useRef } from 'preact/hooks';
import { act } from 'preact/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { SelectField, SettingsSection, useSubmitAction } from '../src/settings-controls';
// @ts-expect-error 适配层验证正式 Select 的事件与禁用生命周期。
vi.mock('@peach/legacy/ui',()=>import('../../web/js/ui-components.js'));
const host=document.createElement('div');
afterEach(()=>{render(null,host);host.remove()});

it('受控值与选项更新同步，重复渲染只调用最新回调，卸载关闭菜单', async () => {
  document.body.append(host);const first=vi.fn(),next=vi.fn(),options=[['a','甲'],['b','乙']];
  await act(()=>render(<SelectField value="a" options={options} label="测试选择" onChange={first}/>,host));
  const field=host.querySelector('.gselect');
  await act(()=>render(<SelectField value="b" options={options} label="测试选择" onChange={next}/>,host));
  expect(host.querySelector('.gselect')).toBe(field);
  expect(host.querySelector('[aria-selected="true"]')?.getAttribute('data-select-option')).toBe('b');
  await act(()=>host.querySelector<HTMLButtonElement>('[data-select-option="a"]')!.click());
  expect(first).not.toHaveBeenCalled();expect(next).toHaveBeenCalledExactlyOnceWith('a');
  await act(()=>render(<SelectField value="c" options={[['c','丙']]} label="测试选择" disabled onChange={next}/>,host));
  expect(host.querySelector<HTMLButtonElement>('[data-select-trigger]')!.disabled).toBe(true);
  expect(host.querySelector('[data-select-label]')?.textContent).toBe('丙');
  const trigger=host.querySelector<HTMLButtonElement>('[data-select-trigger]')!;
  await act(()=>render(null,host));expect(trigger.disabled).toBe(true);
});

it('提交防重入，卸载取消等待并丢弃成功回执', async () => {
  document.body.append(host);let resolve!:(value:string)=>void,signal!:AbortSignal;
  const success=vi.fn(),write=vi.fn((next:AbortSignal)=>{signal=next;return new Promise<string>(done=>{resolve=done})});
  function Form(){const button=useRef<HTMLButtonElement>(null),action=useSubmitAction(button);
    return <SettingsSection titleId="test-title" title="设置" error={action.error}
      onSubmit={event=>{event.preventDefault();void action.run(write,success)}} footer={<button ref={button}>保存</button>}><input/></SettingsSection>}
  await act(()=>render(<Form/>,host));
  const form=host.querySelector('form')!;
  await act(()=>{form.requestSubmit();form.requestSubmit()});
  expect(write).toHaveBeenCalledOnce();expect(host.querySelector('button')?.getAttribute('aria-busy')).toBe('true');
  await act(()=>render(null,host));expect(signal.aborted).toBe(true);
  await act(()=>resolve('完成'));expect(success).not.toHaveBeenCalled();
});
