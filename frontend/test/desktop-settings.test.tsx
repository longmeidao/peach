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
  await act(async()=>render(<><StartupSettings startup={{available:true,enabled:false,silent:true,message:'',desktop:false,desktop_message:''}} receipt={()=>{}} />
    <UninstallSettings uninstall={{available:true,full_available:true,message:'',data_root:'fixture',directories:[]}} /></>,host));
  expect(host.querySelector('#uninstallPeach .configfieldset-heading #uninstallTitle')).not.toBeNull();
  expect(host.querySelector('#uninstallPeach .configfieldset-heading > .confighelp')?.textContent).toContain('原始媒体文件保留');
  const boxes=host.querySelectorAll<HTMLInputElement>('input');
  expect(host.querySelectorAll('[role="switch"]')).toHaveLength(3);
  expect(host.querySelector('form button')?.textContent).toBe('保存配置');
  expect(fetch).not.toHaveBeenCalled();
  // 桌面快捷方式那颗开关排在静默启动之后，卸载的复选框因此退到第 4 个。
  expect(boxes[3]!.checked).toBe(false);
  expect(boxes[2]!.disabled).toBe(false);
  expect(boxes[1]!.disabled).toBe(true);
  expect(host.querySelector('[data-fieldset-type=error]')).not.toBeNull();
  const summary=host.querySelector('summary')!;
  expect(summary.getAttribute('aria-expanded')).toBe('false');
  expect(host.querySelector('.fcollapse')).not.toBeNull();
  await act(async()=>{summary.click();});
  expect(summary.getAttribute('aria-expanded')).toBe('true');
  await act(async()=>{boxes[0]!.checked=true;boxes[0]!.dispatchEvent(new Event('change',{bubbles:true}));});
  expect(boxes[1]!.disabled).toBe(false);
  await act(async()=>{host.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));});
  expect(JSON.parse(String(fetch.mock.calls[0]![1].body))).toEqual({enabled:true,silent:true,desktop:false});
  render(null,host);
});
it('桌面快捷方式被别的安装占着时，那颗开关锁住并说出原因',async()=>{
  // 只锁住这一颗。桌面上摆着另一份 Peach 的图标不该连开机自启都不让改，那一格自己还是好的。
  const host=document.createElement('div');document.body.append(host);
  const startup={available:true,enabled:true,silent:true,message:'',desktop:false,desktop_message:'桌面快捷方式属于另一份 Peach 安装'};
  await act(async()=>render(<StartupSettings startup={startup} receipt={()=>{}} />,host));
  const switches=host.querySelectorAll<HTMLInputElement>('[role="switch"]');
  expect(switches[2]!.disabled).toBe(true);
  expect(switches[0]!.disabled).toBe(false);
  expect(host.querySelector('form button')?.hasAttribute('disabled')).toBe(false);
  expect([...host.querySelectorAll('.confighelp')].map(node=>node.textContent))
    .toContain('桌面快捷方式属于另一份 Peach 安装');
  render(null,host);
});
it('随机无方向，首页偏好与其他排序分别解析',()=>{
  expect(preferredDirection('seed','seed','asc')).toBe('');
  expect(preferredDirection('new','new','asc')).toBe('asc');
  expect(preferredDirection('rating','new','asc')).toBe('desc');
});
