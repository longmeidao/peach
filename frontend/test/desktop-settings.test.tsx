import { render } from 'preact';
import { act } from 'preact/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { StartupSettings, UninstallSettings } from '../src/islands/desktop-settings';
import { preferredDirection } from '../src/sort-preferences';

// 交互回归直接使用浏览器共用模块，包含 Collapse 的真实接线。
// @ts-expect-error 遗留 JS 的声明由正式 alias 提供。
vi.mock('@peach/legacy/ui',()=>import('../../web/js/ui-components.js'));
// @ts-expect-error 遗留 JS 的声明由正式 alias 提供。
vi.mock('@peach/legacy/core',()=>import('../../web/js/core.js'));

afterEach(()=>{document.body.replaceChildren();vi.unstubAllGlobals();});
it('自启保存实际选项，卸载默认保留数据',async()=>{
  const fetch = vi.fn(async(_url:string,_init:RequestInit)=>({ok:true,json:async()=>({})}));vi.stubGlobal('fetch',fetch);
  const host=document.createElement('div');document.body.append(host);
  await act(async()=>render(<><StartupSettings startup={{available:true,enabled:false,silent:true,message:''}} receipt={()=>{}} />
    <UninstallSettings uninstall={{available:true,full_available:true,message:'',data_root:'fixture',directories:[]}} /></>,host));
  const boxes=host.querySelectorAll<HTMLInputElement>('input');
  expect(host.querySelectorAll('[role="switch"]')).toHaveLength(2);
  expect(host.querySelector('form button')?.textContent).toBe('保存配置');
  expect(fetch).not.toHaveBeenCalled();
  expect(boxes[2]!.checked).toBe(false);
  expect(host.querySelector('[data-fieldset-type=error]')).not.toBeNull();
  const summary=host.querySelector('summary')!;
  expect(summary.getAttribute('aria-expanded')).toBe('false');
  expect(host.querySelector('.fcollapse')).not.toBeNull();
  await act(async()=>{summary.click();});
  expect(summary.getAttribute('aria-expanded')).toBe('true');
  await act(async()=>{boxes[0]!.checked=true;boxes[0]!.dispatchEvent(new Event('change',{bubbles:true}));});
  await act(async()=>{host.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));});
  expect(JSON.parse(String(fetch.mock.calls[0]![1].body))).toEqual({enabled:true,silent:true});
  render(null,host);
});
it('随机无方向，首页偏好与其他排序分别解析',()=>{
  expect(preferredDirection('seed','seed','asc')).toBe('');
  expect(preferredDirection('new','new','asc')).toBe('asc');
  expect(preferredDirection('rating','new','asc')).toBe('desc');
});
