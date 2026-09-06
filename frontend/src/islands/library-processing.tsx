import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { apiGet, apiSend, errorMessage } from '../api';
import { fieldsetTitle, loadingDotsHtml, noteHtml, progressHtml, setActionBusy } from '@peach/legacy/ui';
import { watchJob } from '../jobs';
import type { JobState } from '../jobs';
import type { IslandState } from '../islands';

export interface LibraryProcessingData extends JobState {
  stage?: string; scanned?: number; identified?: number; candidates?: number; covers?: number;
  issues?: { asset_id: number | null; message: string }[];
}
export interface LibraryProcessingProps { toast(message: string): void; onComplete?(): void }
export const loadLibraryProcessing = (_props: LibraryProcessingProps, signal: AbortSignal) =>
  apiGet<LibraryProcessingData>('/api/library-processing', signal);

export function LibraryProcessing({ data, error, toast, onComplete }: LibraryProcessingProps & IslandState<LibraryProcessingData>) {
  const [state, setState] = useState<LibraryProcessingData>(data || { status: 'idle' });
  const [problem, setProblem] = useState(error);
  const [submitting, setSubmitting] = useState(false);
  const [receipt, setReceipt] = useState(false);
  const lifetime = useRef(new AbortController());
  const generation = useRef(0);
  const button = useRef<HTMLButtonElement>(null);
  const busy = submitting || state.status === 'running';
  useLayoutEffect(() => setActionBusy(button.current, busy), [busy]);
  async function follow() {
    const epoch = ++generation.current;
    await watchJob<LibraryProcessingData>({
      read: signal => apiGet('/api/library-processing', signal),
      active: () => !lifetime.current.signal.aborted && generation.current === epoch,
      render: next => {
        setState(next); setProblem('');
        if (next.status === 'complete') { setReceipt(true); toast('已完成扫描与资料采集'); }
        if (next.status === 'complete' || next.status === 'failed') onComplete?.();
      },
      disconnected: () => setProblem('连接中断，正在重新读取处理进度'),
    });
  }
  useEffect(() => {
    if (state.status === 'running') void follow();
    return () => lifetime.current.abort();
  }, []);
  async function start() {
    if (busy) return;
    setSubmitting(true); setProblem(''); setReceipt(false);
    try {
      const next = await apiSend<LibraryProcessingData>('/api/library-processing', {}, 'POST', lifetime.current.signal);
      if (lifetime.current.signal.aborted) return;
      setState(next); setSubmitting(false); await follow();
    } catch (cause) {
      if (!lifetime.current.signal.aborted) { setProblem(errorMessage(cause)); setSubmitting(false); }
    }
  }
  return <>
    <div class="geist-fieldset-content library-processing">
      <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('cleanupScrapingTitle', '扫描与采集') }} />
      <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p>
      <div aria-live="polite">
        {state.status === 'running' && <>
          <div dangerouslySetInnerHTML={{ __html: loadingDotsHtml(state.stage || '正在处理') }} />
          {!!state.total && <div dangerouslySetInnerHTML={{ __html: progressHtml(`已处理 ${state.checked || 0} / ${state.total} 个视频`, state.checked || 0, state.total) }} />}
        </>}
        {(problem || state.status === 'failed') && <div role="alert" dangerouslySetInnerHTML={{ __html: noteHtml(problem || state.error || '处理未完成，请重试', { variant: 'error' }) }} />}
        {state.status === 'failed' && !!state.issues?.length && <ul>{state.issues.slice(0, 20).map(issue =>
          <li>{issue.asset_id ? <a href={`/item/${issue.asset_id}`}>查看视频</a> : null}{issue.asset_id ? '：' : ''}{issue.message}</li>)}</ul>}
        {receipt && <p>已扫描 {state.scanned || 0} 个文件，识别 {state.identified || 0} 个番号，整理 {state.candidates || 0} 组资料候选。</p>}
      </div>
    </div>
    <footer class="geist-fieldset-footer" data-geist-fieldset-footer>
      <a class="geist-button" href="/scraping">采集来源</a>
      {!!state.candidates && <a class="geist-button" href="/review">复核资料</a>}
      <button ref={button} type="button" class="geist-button primary" onClick={() => void start()}>{state.status === 'failed' ? '重试未完成项' : '扫描并补全资料'}</button>
    </footer>
  </>;
}
