import { h, render } from 'preact';
import { useState } from 'preact/hooks';
import { LibraryProcessing } from './islands/library-processing';
import type { LibraryProcessingData } from './islands/library-processing';
import { jobProgressHtml } from './board-metrics';
import { cleanupSkeletonHtml } from './management';
import { noteHtml, loadingDotsHtml, projectBannerHtml } from '@peach/legacy/ui';

const states = [
  ['idle','待开始'],['loading','页面加载'],['preparing','准备任务'],['running','任务进行中'],
  ['retrying','等待重试'],['disconnected','失去连接'],['reconnected','恢复连接'],
  ['failed','任务失败'],['complete','任务完成'],['expired','状态已失效'],['paused','来源已暂停'],
] as const;
type State = typeof states[number][0];
const Html=({html}:{html:string})=><div dangerouslySetInnerHTML={{__html:html}}/>;

function StatePreview() {
  const [state,setState]=useState<State>('running');
  const [revision,setRevision]=useState(0);
  const [dark,setDark]=useState(document.documentElement.dataset.theme==='dark');
  const [value,setValue]=useState(38);
  const data:LibraryProcessingData={status:state==='failed'?'failed':['running','preparing','disconnected','retrying','reconnected'].includes(state)?'running':'idle',
    stage:state==='preparing'?'正在准备扫描':state==='retrying'?'等待来源响应 · 8 秒后重试':'正在整理资料',
    checked:value,...(state==='preparing'?{}:{total:100}),error:state==='failed'?'来源暂时不可用，请重试未完成项':'',
    issue_count:state==='failed'?1:0,
    issue_preview:state==='failed'?[{asset_id:null,title:'本地磁盘',path:'R:\\Media',message:'来源连接超时'}]:[],
    issues_log:state==='failed'?'peach-data\\state\\library-processing-preview.issues.jsonl':'',
    retryable_asset_ids:state==='failed'?[7]:[]};
  const problem=state==='disconnected'?'连接中断，正在重新读取处理进度':'';
  return <main class="board-state-preview">
    <header><div><h1>运行状态预览</h1><p>演示数据 · 不连接任务接口，不执行扫描或写入。</p></div>
      <button class="geist-button" onClick={()=>{document.documentElement.dataset.theme=dark?'light':'dark';setDark(!dark)}}>{dark?'浅色':'深色'}</button></header>
    <nav aria-label="演示状态">{states.map(([key,label])=><button class="geist-button" aria-pressed={state===key} onClick={()=>{setState(key);setRevision(revision+1)}}>{label}</button>)}</nav>
    <div class="board-preview-tools"><label>任务进度 <input type="range" min="0" max="100" value={value} onInput={event=>setValue(Number(event.currentTarget.value))}/><output>{value}%</output></label><button class="geist-button" onClick={()=>setRevision(revision+1)}>重播状态</button></div>
    <section aria-label="页面横幅"><h2>全局任务横幅</h2>
      <LibraryProcessing key={`banner-${state}-${revision}-${value}`} data={data} error={problem} mode="notice" preview toast={()=>{}}/>
      {!['running','preparing','disconnected','retrying','reconnected','failed'].includes(state)&&<p>此状态不常驻全局横幅。</p>}
    </section>
    <section><h2>数据管理 · 扫描与采集</h2>
      {state==='loading'?<Html html={cleanupSkeletonHtml()}/>:<div class="cleanupgrid"><div id="libraryProcessing" class="cleanupscraping"><LibraryProcessing key={`${state}-${revision}-${value}`} data={data} error={problem} preview toast={()=>{}}/></div></div>}
      {state==='complete'&&<Html html={noteHtml('已完成扫描与资料采集',{variant:'success',label:'任务完成'})}/>}
      {state==='expired'&&<Html html={noteHtml('任务状态已失效，请重新发起任务',{variant:'warning'})}/>}
      {state==='paused'&&<span class="sbadge paused">已暂停</span>}
    </section>
    <section><h2>关注检查与资源同步</h2><div class="board-preview-grid">
      <article><h3>检查更新</h3><Html html={state==='disconnected'?noteHtml('暂时无法读取进度，正在重新连接…',{label:'任务状态'}):state==='failed'?noteHtml('检查失败：来源连接超时',{variant:'error',actionLabel:'重试'}):state==='running'||state==='retrying'||state==='reconnected'?jobProgressHtml(`${state==='retrying'?'第 2/3 次尝试，8 秒后重试 · ':''}已完成 ${value}/100 个来源`,value,100):state==='preparing'?loadingDotsHtml('正在准备检查任务…'):noteHtml(state==='complete'?'已完成检查':state==='paused'?'已暂停自动检查':state==='expired'?'任务状态已失效，请重新发起任务':'等待开始',{variant:state==='complete'?'success':'secondary'})}/></article>
      <article><h3>连接与恢复</h3><Html html={projectBannerHtml(state==='disconnected'?'暂时无法连接服务器，正在重连':state==='reconnected'?'连接已恢复，继续读取任务进度':'连接正常',{variant:state==='disconnected'?'warning':'gray',href:'#',label:'查看状态'})}/><p>失去连接只影响进度读取；恢复连接后继续展示任务状态。</p></article>
    </div></section>
    <section><h2>错误与加载状态一览</h2><div class="board-preview-grid">
      <article><h3>读取失败</h3><Html html={noteHtml('无法读取状态，请重试',{variant:'error',actionLabel:'重试'})}/></article>
      <article><h3>来源离线</h3><Html html={noteHtml('媒体来源离线，请检查挂载状态',{variant:'warning'})}/></article>
      <article><h3>没有待处理内容</h3><Html html={noteHtml('没有待处理内容',{variant:'secondary'})}/></article>
      <article><h3>等待响应</h3><Html html={loadingDotsHtml('正在读取来源状态')}/></article>
    </div></section>
  </main>;
}

/** 只由开发预览入口调用；演示组件禁止发起任务请求。 */
export function mountBoardStatePreview(root:HTMLElement){render(h(StatePreview,{}),root)}
