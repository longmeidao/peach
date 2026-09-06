import { afterEach, expect, it, vi } from 'vitest';
import { h, render } from 'preact';
import { act } from 'preact/test-utils';
import { LibraryProcessing } from '../src/islands/library-processing';

let host: HTMLDivElement;
afterEach(() => { if(host)render(null, host); document.body.innerHTML=''; vi.unstubAllGlobals(); });
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
