import { afterEach, expect, it, vi } from 'vitest';
import { h, render } from 'preact';
import { act } from 'preact/test-utils';
import { LibraryProcessing } from '../src/islands/library-processing';

let host: HTMLDivElement;
afterEach(() => { if(host)render(null, host); document.body.innerHTML=''; vi.useRealTimers(); vi.unstubAllGlobals(); });
it('启动只提交一次，进度用 GET 读取并提供复核入口', async () => {
  const requests: string[]=[];
  vi.stubGlobal('fetch',vi.fn(async (_url: string, init?: RequestInit) => {
    const method=init?.method || 'GET'; requests.push(method);
    return {ok:true,json:async()=>method==='POST'?{status:'running',job_id:'one'}:{status:'complete',job_id:'one',candidates:2}};
  }));
  host=document.createElement('div');document.body.append(host);
  const toast=vi.fn();
  await act(async()=>render(h(LibraryProcessing,{data:{status:'idle'},error:'',toast}),host));
  await act(async()=>{host.querySelector('button')!.click();await new Promise(resolve=>setTimeout(resolve,0));});
  expect(requests).toEqual(['POST','GET']);
  expect(host.querySelector('a[href="/review"]')).not.toBeNull();
  expect(toast).toHaveBeenCalledTimes(1);
  expect(host.querySelector('.library-processing-result .geist-note-success')?.textContent).toContain('处理完成');
});
it('刷新接续已有任务时只查询，旧完成结果不冒充当前回执', async () => {
  const fetch=vi.fn(async()=>({ok:true,json:async()=>({status:'failed',error:'来源离线'})}));
  vi.stubGlobal('fetch',fetch);
  host=document.createElement('div');document.body.append(host);
  const toast=vi.fn();
  await act(async()=>{render(h(LibraryProcessing,{data:{status:'running'},error:'',toast}),host);await new Promise(resolve=>setTimeout(resolve,0));});
  await act(async()=>{await new Promise(resolve=>setTimeout(resolve,0));});
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(host.textContent).toContain('来源离线');
  expect(host.textContent).toContain('重试未完成项');
  expect(toast).not.toHaveBeenCalled();
});
it('首页从空闲发现后台任务，完成后收起并在卸载后停止查询', async () => {
  vi.useFakeTimers();
  let status='running';
  const fetch=vi.fn(async (_url: string, _init?: RequestInit)=>({ok:true,json:async()=>({status,stage:'采集缺失资料',checked:2,total:5})}));
  vi.stubGlobal('fetch',fetch);
  host=document.createElement('div');document.body.append(host);
  const toast=vi.fn();
  await act(async()=>render(h(LibraryProcessing,{data:{status:'idle'},error:'',toast,mode:'notice'}),host));
  await act(async()=>{await vi.advanceTimersByTimeAsync(1);});
  expect(host.textContent).toContain('采集缺失资料');
  expect(host.querySelector('a')?.getAttribute('href')).toBe('/data-cleanup#libraryProcessing');
  status='complete';
  await act(async()=>{await vi.advanceTimersByTimeAsync(2000);});
  expect(host.textContent).toBe('');
  expect(toast).not.toHaveBeenCalled();
  render(null,host);
  const calls=fetch.mock.calls.length;
  await vi.advanceTimersByTimeAsync(4000);
  expect(fetch).toHaveBeenCalledTimes(calls);
  expect(fetch.mock.calls.every(call=>!call[1] || call[1].method!=='POST')).toBe(true);
});
it('设置持续查询已有任务，只在任务结束时提示一次', async () => {
  vi.useFakeTimers();
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({status:'complete'})})));
  host=document.createElement('div');document.body.append(host);
  const toast=vi.fn();
  await act(async()=>render(h(LibraryProcessing,{data:{status:'running'},error:'',toast,monitor:true}),host));
  await act(async()=>{await vi.advanceTimersByTimeAsync(4000);});
  expect(toast).toHaveBeenCalledTimes(1);
});
