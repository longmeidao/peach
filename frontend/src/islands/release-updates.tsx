import { useEffect, useRef, useState } from 'preact/hooks';
import { fieldsetTitle, setActionBusy, progressHtml, confirmModal } from '@peach/legacy/ui';
import { apiGet, apiSend, errorMessage } from '../api';

export interface ReleaseState {
  current_version: string;
  latest_version: string | null;
  channel: string;
  installation: string;
  state: string;
  message: string;
  release_url: string;
}

export interface UpdateJob {state: string; progress: number; message?: string; downloaded?: number; total?: number; version?: string}
const active = new Set(['downloading','verifying','extracting','preparing','restarting','installing']);

export function ReleaseUpdates({ initial, initialJob }: { initial: ReleaseState; initialJob?: UpdateJob | undefined }) {
  const [data, setData] = useState(initial);
  const [job, setJob] = useState<UpdateJob>(initialJob || {state:'idle',progress:0});
  const [error, setError] = useState('');
  const request = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  const prompted = useRef(false);
  const downloadButton = useRef<HTMLButtonElement>(null);
  useEffect(() => { setActionBusy(downloadButton.current,active.has(job.state)); }, [job.state]);
  useEffect(() => () => { mounted.current = false; request.current?.abort(); }, []);
  const restart = async () => {
    const result = await apiSend<UpdateJob>('/api/configuration/update-restart', {});
    if (mounted.current) setJob(result);
  };
  useEffect(() => {
    if (job.state !== 'ready' || prompted.current) return;
    prompted.current = true;
    void confirmModal({title:'更新已准备好',body:`Peach ${job.version || ''} 将在重启后安装。`,confirmLabel:'立即重启',cancelLabel:'稍后',onConfirm:restart});
  }, [job.state]);
  useEffect(() => {
    if (!active.has(job.state)) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let failures = 0;
    const poll = async () => {
      try {
        const result = await apiGet<UpdateJob>('/api/configuration/update-status',controller.signal);
        if (!controller.signal.aborted) {
          setJob(result); failures = 0;
          if (result.state === 'complete') setData(current => ({...current,current_version:result.version || current.current_version,state:'current',message:'已是最新测试版。'}));
        }
      } catch {
        if (++failures >= 120 && !controller.signal.aborted) setError('尚未连接到 Peach，请检查托盘后刷新页面。');
      }
      if (!controller.signal.aborted && failures < 120) timer = setTimeout(poll,1000);
    };
    timer = setTimeout(poll,1000);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [job.state]);
  const download = async (button: HTMLButtonElement) => {
    if (request.current || active.has(job.state)) return;
    const controller = new AbortController(); request.current = controller;
    prompted.current = false; setError(''); setActionBusy(button,true);
    try {
      const result = await apiSend<UpdateJob>('/api/configuration/update',{},'POST',controller.signal);
      if (!controller.signal.aborted) setJob(result);
    } catch (cause) { if (!controller.signal.aborted) setError(errorMessage(cause)); }
    finally { request.current = null; setActionBusy(button,false); }
  };
  const check = async (button: HTMLButtonElement) => {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setActionBusy(button, true); setError('');
    try {
      const result = await apiGet<ReleaseState>('/api/configuration/updates', controller.signal);
      if (!controller.signal.aborted) setData(result);
    } catch (cause) {
      if (!controller.signal.aborted) {
        setData({ ...initial, state: 'error' });
        setError(errorMessage(cause));
      }
    } finally {
      request.current = null;
      setActionBusy(button, false);
    }
  };
  return <section class="configfieldset" data-geist-fieldset aria-labelledby="configUpdatesTitle">
    <div class="geist-fieldset-content">
      <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('configUpdatesTitle', '检查更新') }} />
      <dl class="configfacts">
        <dt>当前版本</dt><dd>{data.current_version}</dd>
        <dt>安装方式</dt><dd>{data.installation}</dd>
        <dt>更新通道</dt><dd>{data.channel}</dd>
        <dt>最新版本</dt><dd>{data.latest_version || (data.state === 'unchecked' ? '尚未检查' : '未取得')}</dd>
      </dl>
      <p class={error || data.state === 'error' ? 'configbad' : 'confighelp'} role={error || data.state === 'error' ? 'alert' : 'status'}>
        {error || data.message}
      </p>
      {job.state !== 'idle' ? <div aria-live="polite">
        <p class={job.state === 'error' ? 'configbad' : 'confighelp'}>{job.message}</p>
        {job.state !== 'error' ? <>
          <div dangerouslySetInnerHTML={{__html:progressHtml(job.state === 'downloading' ? '下载进度' : '安装进度',job.state === 'downloading' ? job.downloaded || 0 : job.progress,job.state === 'downloading' ? job.total || 1 : 100)}} />
          <p class="confighelp">{job.state === 'downloading' && job.total ? `${((job.downloaded || 0)/1048576).toFixed(1)} / ${(job.total/1048576).toFixed(1)} MB` : `${job.progress}%`}</p>
        </> : null}
      </div> : null}
    </div>
    <div class="geist-fieldset-footer" data-geist-fieldset-footer>
      <a class="geist-button" href={data.release_url} target="_blank" rel="noreferrer">查看发布页<svg aria-hidden="true" viewBox="0 0 24 24"><use href="#i-external-link" /></svg></a>
      {job.state === 'ready' ? <button type="button" class="geist-button primary" onClick={() => { void confirmModal({title:'更新已准备好',body:`Peach ${job.version || ''} 将在重启后安装。`,confirmLabel:'立即重启',cancelLabel:'稍后',onConfirm:restart}); }}>重启安装</button> : null}
      {data.state === 'available' && data.installation === '独立测试包' && job.state !== 'ready' ? <button ref={downloadButton} type="button" class="geist-button primary" onClick={(event) => download(event.currentTarget)}>下载并安装</button> : null}
      <button type="button" class="geist-button" disabled={active.has(job.state)} onClick={(event) => check(event.currentTarget)}>检查更新</button>
    </div>
  </section>;
}
