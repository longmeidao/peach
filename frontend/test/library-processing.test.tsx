import { afterEach, expect, it, vi } from 'vitest';
import { h, render } from 'preact';
import { act } from 'preact/test-utils';
import { LibraryProcessing } from '../src/islands/library-processing';

let host: HTMLDivElement;
it('没有来源资料显示中性记录且不提供失败重试',async()=>{
  host=document.createElement('div');document.body.append(host);
  await act(async()=>render(h(LibraryProcessing,{data:{status:'complete',error_count:0,issue_count:1,issue_preview:[{asset_id:1,title:'孤立资源',message:'来源未收录',severity:'info'}]},error:'',toast:vi.fn(),preview:true}),host));
  expect(host.textContent).toContain('1 项采集记录');
  expect(host.querySelector('.geist-note-error')).toBeNull();
  expect(host.textContent).not.toContain('重试未完成项');
  expect(host.querySelector('.geist-note-details a')?.getAttribute('href')).toBe('/item/1');
});
it('三种扫描采集方式使用分体菜单并提交对应阶段', async () => {
  const bodies: object[] = [];
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
    if (init?.method === 'POST') bodies.push(JSON.parse(String(init.body)));
    return {ok:true,json:async()=>({status:'complete'})};
  }));
  host=document.createElement('div');document.body.append(host);
  await act(async()=>render(h(LibraryProcessing,{data:{status:'idle'},error:'',toast:vi.fn()}),host));
  expect(host.querySelector('.splitmain')?.textContent).toBe(host.querySelector('[role=menuitem]')?.textContent);
  const items=host.querySelectorAll<HTMLButtonElement>('[role=menuitem]');
  for (const item of items) await act(async()=>{item.click();await new Promise(resolve=>setTimeout(resolve,0));});
  expect(bodies).toEqual([{}, {stage:'scan'}, {stage:'collect'}]);
  expect(host.querySelector('a[href="/scraping"]')?.textContent).toContain('来源和凭证');
});
it('演示运行态与失败重试都不请求真实任务', async()=>{
  const fetch=vi.fn();vi.stubGlobal('fetch',fetch);
  host=document.createElement('div');document.body.append(host);
  await act(async()=>render(h(LibraryProcessing,{data:{status:'running',checked:2,total:10},error:'',toast:vi.fn(),preview:true,monitor:true}),host));
  expect(host.querySelector('[role=progressbar]')?.getAttribute('aria-valuenow')).toBe('2');
  expect(host.querySelectorAll('[role=progressbar]')).toHaveLength(1);
  expect(host.querySelector('.geist-loading-dots')).toBeNull();
  await act(async()=>{render(h(LibraryProcessing,{key:'failed',data:{status:'failed'},error:'',toast:vi.fn(),preview:true}),host)});
  await act(async()=>{host.querySelector<HTMLButtonElement>('[data-note-action]')?.click()});
  expect(fetch).not.toHaveBeenCalled();
});
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
  expect(toast).not.toHaveBeenCalled();
});
it('运行态显示当前项目、动作与等待时长，stalled 只提示不另起任务', async () => {
  host=document.createElement('div');document.body.append(host);
  await act(async()=>render(h(LibraryProcessing,{data:{status:'running',job_id:'one',checked:2,total:10,stalled:true,current_asset_name:'ABW-001.mp4',current_action:'querying_metadata',waited_seconds:300},error:'',toast:vi.fn(),preview:true}),host));
  expect(host.textContent).toContain('当前：ABW-001.mp4 · 查询外部资料 · 已等待 300 秒');
  expect(host.textContent).toContain('处理时间较长');
  expect(host.querySelector('[data-note-action]')).toBeNull();
});
it('失败时把问题清单折叠进错误提示并只提交失败项重试', async () => {
  const calls:{url:string,init:RequestInit|undefined}[]=[];
  vi.stubGlobal('fetch',vi.fn(async (url:string, init?:RequestInit)=>{
    calls.push({url,init});
    return {ok:true,json:async()=>init?.method==='POST'?{status:'running',job_id:'two'}:{status:'running',job_id:'two'}};
  }));
  host=document.createElement('div');document.body.append(host);
  const data={status:'failed',job_id:'one',error:'2 项需要处理',issue_count:23,
    issues_log:'C:\\peach-data\\state\\library-processing-one.issues.jsonl',
    issue_preview:[{asset_id:7,title:'样品.mp4',path:'R:\\Media\\样品.mp4',message:'未识别到番号'}],
    issues_truncated:true,retryable_asset_ids:[7,8]};
  await act(async()=>{render(h(LibraryProcessing,{data,error:'',toast:vi.fn()}),host)});
  const details=host.querySelector<HTMLDetailsElement>('.geist-note .geist-note-details')!;
  expect(details.open).toBe(false);
  expect(details.querySelector('summary')?.textContent).toBe('问题清单：共 23 项，展开查看前 1 项');
  expect(details.querySelector('li a')?.getAttribute('href')).toBe('/item/7');
  expect(details.querySelector('li')?.textContent).toContain('样品.mp4');
  expect(details.querySelector('li code')?.textContent).toBe('R:\\Media\\样品.mp4');
  expect(details.querySelector('p')?.textContent).toContain('C:\\peach-data\\state\\library-processing-one.issues.jsonl');
  expect(host.textContent).toContain('重试未完成项');
  expect(host.querySelector('.geist-fieldset-footer .geist-button.primary')).toBeNull();
  await act(async()=>{host.querySelector<HTMLButtonElement>('[data-note-action]')!.click();await new Promise(resolve=>setTimeout(resolve,0));});
  const post=calls.find(call=>call.init?.method==='POST');
  expect(post).toBeTruthy();
  expect(JSON.parse(String(post!.init!.body))).toEqual({job_id:'one',retry:[7,8]});
});
it('失败项都不可重试时仍能重新发起整批任务', async () => {
  host=document.createElement('div');document.body.append(host);
  const data={status:'failed',job_id:'one',error:'1 项需要处理',issue_count:1,
    issue_preview:[{asset_id:1,message:'未识别到番号'}],retryable_asset_ids:[]};
  await act(async()=>{render(h(LibraryProcessing,{data,error:'',toast:vi.fn()}),host)});
  expect(host.querySelector('[data-note-action]')).toBeNull();
  expect(host.querySelector('.geist-fieldset-footer .splitmain')?.textContent).toBe('扫描并补全资料');
});
it('首页从空闲发现后台任务，完成后收起横幅、用通知报完成，卸载后停止查询', async () => {
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
  expect(toast).toHaveBeenCalledTimes(1);
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
it('刚结束的任务在目录页横幅第一次读到时也提示，同一任务只提示一次', async () => {
  vi.useFakeTimers();
  const job={status:'complete' as const,job_id:'job-fresh',identified:3,candidates:2,completed_at:Date.now()/1000};
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>job})));
  localStorage.removeItem('peach.library-processing.announced');
  const toast=vi.fn();
  for (let round=0; round<2; round++) {
    host=document.createElement('div');document.body.append(host);
    await act(async()=>render(h(LibraryProcessing,{data:job,error:'',toast,mode:'notice'}),host));
    await act(async()=>{await vi.advanceTimersByTimeAsync(4000);});
    render(null,host);
  }
  expect(toast).toHaveBeenCalledTimes(1);
  expect(toast.mock.calls[0][0]).toBe('扫描与资料采集已完成：识别 3 个番号，整理 2 组资料候选');
});
