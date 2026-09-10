import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { apiGet, apiSend, errorMessage } from '../api';
import { fieldsetTitle, noteHtml, projectBannerHtml, setActionBusy } from '@peach/legacy/ui';
import { jobActivityHtml, watchJob } from '../jobs';
import type { JobState } from '../jobs';
import type { IslandState } from '../islands';

export interface LibraryProcessingIssue { asset_id: number | null; message: string }
export interface LibraryProcessingData extends JobState {
  stage?: string; scanned?: number; identified?: number; candidates?: number; covers?: number;
  issue_count?: number; issue_preview?: LibraryProcessingIssue[];
  issues_truncated?: boolean; retryable_asset_ids?: number[];
  current_asset_id?: number | null; current_asset_name?: string; current_action?: string;
  current_started_at?: number; last_progress_at?: number; stalled?: boolean; waited_seconds?: number;
}
export interface LibraryProcessingProps { toast(message: string): void; onComplete?(): void; mode?: 'notice'; monitor?: boolean; preview?: boolean }
export const loadLibraryProcessing = (_props: LibraryProcessingProps, signal: AbortSignal) =>
  apiGet<LibraryProcessingData>('/api/library-processing', signal);

const ACTION_LABELS: Record<string, string> = {
  reading_local: '读取本地资料', querying_metadata: '查询外部资料',
  fetching_cover: '采集缺失封面', writing_candidates: '保存资料候选',
};

function currentLine(state: LibraryProcessingData): string {
  const action = ACTION_LABELS[state.current_action || ''] || state.stage || '正在处理';
  const waited = state.waited_seconds ? ` · 已等待 ${state.waited_seconds} 秒` : '';
  return state.current_asset_name ? `当前：${state.current_asset_name} · ${action}${waited}` : action + waited;
}

export function LibraryProcessing({ data, error, toast, onComplete, mode, monitor, preview }: LibraryProcessingProps & IslandState<LibraryProcessingData>) {
  const [state, setState] = useState<LibraryProcessingData>(data || { status: 'idle' });
  const [problem, setProblem] = useState(error);
  const [submitting, setSubmitting] = useState(false);
  const [receipt, setReceipt] = useState(false);
  const lifetime = useRef(new AbortController());
  const generation = useRef(0);
  const previousStatus = useRef(state.status);
  const button = useRef<HTMLButtonElement>(null);
  const busy = submitting || state.status === 'running';
  useLayoutEffect(() => setActionBusy(button.current, busy), [busy]);
  async function follow() {
    const epoch = ++generation.current;
    await watchJob<LibraryProcessingData>({
      read: signal => apiGet('/api/library-processing', signal),
      active: () => !lifetime.current.signal.aborted && generation.current === epoch,
      keepWatching: mode === 'notice' || !!monitor,
      render: next => {
        setState(next); setProblem('');
        if (next.status === 'complete' && previousStatus.current === 'running' && mode !== 'notice') { setReceipt(true); toast('已完成扫描与资料采集'); }
        if (previousStatus.current === 'running' && (next.status === 'complete' || next.status === 'failed')) onComplete?.();
        previousStatus.current = next.status;
      },
      disconnected: () => setProblem('连接中断，正在重新读取处理进度'),
    });
  }
  useEffect(() => {
    if (!preview && (state.status === 'running' || mode === 'notice' || monitor)) void follow();
    return () => lifetime.current.abort();
  }, []);
  async function submit(body: LibraryProcessingData | object) {
    if (busy || preview) return;
    setSubmitting(true); setProblem(''); setReceipt(false);
    try {
      const next = await apiSend<LibraryProcessingData>('/api/library-processing', body, 'POST', lifetime.current.signal);
      if (lifetime.current.signal.aborted) return;
      previousStatus.current = next.status;
      setState(next); setSubmitting(false); await follow();
    } catch (cause) {
      if (!lifetime.current.signal.aborted) { setProblem(errorMessage(cause)); setSubmitting(false); }
    }
  }
  const start = () => void submit({});
  const retry = () => {
    if (!state.job_id || !state.retryable_asset_ids?.length) return;
    void submit({ job_id: state.job_id, retry: state.retryable_asset_ids });
  };
  if (mode === 'notice') {
    if (!problem && state.status !== 'running' && state.status !== 'failed') return null;
    const message=problem || (state.status === 'failed' ? '扫描与资料采集未完成' : currentLine(state) + (state.total ? ` · ${state.checked || 0} / ${state.total}` : ''));
    return <div dangerouslySetInnerHTML={{__html:projectBannerHtml(message,{
      variant:state.status === 'failed' ? 'error' : problem ? 'warning' : state.stalled ? 'warning' : 'gray',
      href:'/data-cleanup#libraryProcessing',label:problem || state.status === 'failed' ? '查看并处理' : '查看进度',
      value:state.checked || 0,...(state.status === 'running' && state.total !== undefined ? {max:state.total} : {}),
    })}} />;
  }
  /* 进度条讲的是卡片上那个按钮此刻在做什么，留在卡片里；结果和故障讲的是这一趟任务
     的下场，挂在卡片外面，和链接管理、资源同步那两块同一个写法。 */
  const issues = state.issue_preview || [];
  const retryable = state.status === 'failed' && !!state.retryable_asset_ids?.length;
  return <>
    <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanupScrapingTitle">
      <div class="geist-fieldset-content library-processing">
        <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('cleanupScrapingTitle', '扫描与采集') }} />
        <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p>
        {state.status === 'running' && <div aria-live="polite" dangerouslySetInnerHTML={{ __html:
          jobActivityHtml(state.total ? `${currentLine(state)} · ${state.checked || 0} / ${state.total} 个视频` : currentLine(state), state.checked, state.total) }} />}
      </div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer>
        <a class="geist-button" href="/scraping">采集来源</a>
        {!!state.candidates && <a class="geist-button" href="/review">复核资料</a>}
        {(state.status !== 'failed' || !retryable) && <button ref={button} type="button" class="geist-button primary" onClick={start}>扫描并补全资料</button>}
      </footer>
    </section>
    <div class="library-processing-outcome" aria-live="polite">
      {state.status === 'running' && state.stalled && <div class="library-processing-stalled" dangerouslySetInnerHTML={{ __html: noteHtml(
        '这个项目处理时间较长，暂时没有新进展。可以继续等待，或在任务结束后重试未完成项。',
        { variant: 'warning', label: '处理较慢', filled: true }) }} />}
      {(problem || state.status === 'failed') && <div role="alert" onClick={event=>{if((event.target as HTMLElement).closest('[data-note-action]'))retry();}} dangerouslySetInnerHTML={{ __html: noteHtml(problem || state.error || '处理未完成，请重试', { variant: 'error',filled:true,actionLabel:retryable?'重试未完成项':'' }) }} />}
      {state.status === 'failed' && !!issues.length && <div class="library-processing-issues-wrap">
        <p class="library-processing-issues-summary">{state.issues_truncated
          ? `共 ${state.issue_count || 0} 项问题，以下为前 ${issues.length} 项`
          : `共 ${state.issue_count || 0} 项问题`}</p>
        <ul class="library-processing-issues">{issues.map(issue =>
          <li>{issue.asset_id ? <a href={`/item/${issue.asset_id}`}>查看视频</a> : null}{issue.asset_id ? '：' : ''}{issue.message}</li>)}</ul>
      </div>}
      {receipt && <div class="library-processing-result" dangerouslySetInnerHTML={{ __html: noteHtml(`已扫描 ${state.scanned || 0} 个文件，识别 ${state.identified || 0} 个番号，整理 ${state.candidates || 0} 组资料候选。`, { variant: 'success', label: '处理完成' }) }} />}
    </div>
  </>;
}
