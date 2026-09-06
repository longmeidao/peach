import { render } from 'preact';
import { act } from 'preact/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { DesktopSettings } from '../src/islands/desktop-settings';
import { preferredDirection } from '../src/sort-preferences';

afterEach(()=>{document.body.replaceChildren();vi.unstubAllGlobals();});
it('自启保存实际选项，卸载默认保留数据',async()=>{
  const fetch = vi.fn(async(_url:string,_init:RequestInit)=>({ok:true,json:async()=>({})}));vi.stubGlobal('fetch',fetch);
  const host=document.createElement('div');document.body.append(host);
  await act(async()=>render(<DesktopSettings startup={{available:true,enabled:false,silent:true,message:''}}
    uninstall={{available:true,full_available:true,message:'',data_root:'fixture',directories:[]}} receipt={()=>{}} />,host));
  const boxes=host.querySelectorAll<HTMLInputElement>('input');
  expect(boxes[2]!.checked).toBe(false);
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
