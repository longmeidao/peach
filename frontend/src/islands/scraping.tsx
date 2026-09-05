import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { apiGet, apiSend, errorMessage } from '../api';
import { noteHtml, fieldsetTitle, setActionBusy } from '@peach/legacy/ui';
import type { IslandState } from '../islands';
import { watchJob } from '../jobs';
import type { JobState } from '../jobs';

interface Source {
  source: string; label: string; login: string; accepts_cookie: boolean;
  network: string; proxy_saved: boolean; cookie_saved: boolean;
}
export interface ScrapingData { sources: Source[] }
export interface ScrapingProps { toast(message: string): void }
interface Check { label: string; ok: boolean; status?: number; message?: string; width?: number; height?: number }
export const loadScraping = (_props: ScrapingProps, signal: AbortSignal) => apiGet<ScrapingData>('/api/scraping', signal);

function SourceForm({ source, toast }: { source: Source } & ScrapingProps) {
  const [saved, setSaved] = useState(source);
  const [network, setNetwork] = useState(source.network);
  const [proxy, setProxy] = useState('');
  const [cookie, setCookie] = useState('');
  const [cookieText, setCookieText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [checks, setChecks] = useState<Check[]>([]);
  const file = useRef<HTMLInputElement>(null);
  const form = useRef<HTMLFormElement>(null);
  useLayoutEffect(() => {
    form.current?.querySelectorAll('button').forEach(button => setActionBusy(button, busy));
  }, [busy]);
  const lifetime = useRef(new AbortController());
  useEffect(() => () => lifetime.current.abort(), []);
  async function action(kind: 'save' | 'revoke' | 'check') {
    if (busy) return;
    setBusy(true); setError(''); setChecks([]);
    try {
      if (kind === 'check') {
        const result = await apiSend<{ results: Check[] }>('/api/scraping/check', { source: source.source }, 'POST', lifetime.current.signal);
        if (!lifetime.current.signal.aborted) setChecks(result.results);
      } else {
        const result = await apiSend<{ saved: Source }>('/api/scraping/settings', {
          source: source.source, network, proxy, cookie, cookies_text: cookieText, revoke: kind === 'revoke',
        }, 'POST', lifetime.current.signal);
        if (!lifetime.current.signal.aborted) {
          setSaved(result.saved); setProxy(''); setCookie(''); setCookieText('');
          if (file.current) file.current.value = '';
          toast(kind === 'revoke' ? 'Cookie 已撤销' : '来源设置已保存');
        }
      }
    } catch (cause) {
      if (!lifetime.current.signal.aborted) setError(errorMessage(cause));
    } finally {
      if (!lifetime.current.signal.aborted) setBusy(false);
    }
  }
  return <section class="scraping-source">
    <form ref={form} class="cleanupfieldset" data-geist-fieldset onSubmit={event => { event.preventDefault(); void action('save'); }}>
      <div class="geist-fieldset-content scraping-fields">
        <div dangerouslySetInnerHTML={{ __html: fieldsetTitle(`scraping-${source.source}`, source.label) }} />
        <label>连接方式<select class="geist-input" value={network} disabled={busy} onChange={event => setNetwork(event.currentTarget.value)}>
          <option value="environment">环境代理</option><option value="direct">应用直连</option><option value="proxy">指定代理</option>
        </select></label>
        {network === 'proxy' && <label>代理地址<input class="geist-input" type="password" autoComplete="off" value={proxy}
          placeholder={saved.proxy_saved ? '已保存，留空保留' : 'http://127.0.0.1:7890'} disabled={busy}
          onInput={event => setProxy(event.currentTarget.value)} /></label>}
        {source.accepts_cookie && <>
          <p><a href={source.login} target="_blank" rel="noopener noreferrer">打开官网登录</a> · {saved.cookie_saved ? 'Cookie 已保存，尚未验证会话' : '尚未提供 Cookie'}</p>
          <label>Cookie 请求头<input class="geist-input" type="password" autoComplete="off" value={cookie} disabled={busy || !!cookieText}
            onInput={event => setCookie(event.currentTarget.value)} /></label>
          <label>Netscape Cookie 文件<input class="geist-input" ref={file} type="file" accept=".txt" disabled={busy || !!cookie}
            onChange={async event => {
              const selected = event.currentTarget.files?.[0];
              if (!selected) { setCookieText(''); return; }
              setCookieText('');
              if (selected.size > 256 * 1024) { setError('Cookie 文本超过 256 KiB'); event.currentTarget.value = ''; return; }
              setBusy(true);
              try { const text = await selected.text(); if (!lifetime.current.signal.aborted) setCookieText(text); }
              catch { if (!lifetime.current.signal.aborted) setError('Cookie 文件未读取，请重新选择'); }
              finally { if (!lifetime.current.signal.aborted) setBusy(false); }
            }} /></label>
        </>}
        {error && <div role="alert" dangerouslySetInnerHTML={{ __html: noteHtml(error, { variant: 'error' }) }} />}
        {checks.map(check => <p role="status" key={check.label}>{check.label}：{check.ok ? '可连接' : '未取得'}
          {check.width ? ` · ${check.width} × ${check.height}` : ''}{check.message ? ` · ${check.message}` : ''}</p>)}
      </div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer>
        <button class="geist-button primary" type="submit">保存</button>
        <button class="geist-button" type="button" onClick={() => void action('check')}>检查已保存的连接</button>
        {source.accepts_cookie && saved.cookie_saved && <button class="geist-button" type="button" onClick={() => void action('revoke')}>撤销 Cookie</button>}
      </footer>
    </form>
  </section>;
}

export function Scraping({ data, error, toast }: ScrapingProps & IslandState<ScrapingData>) {
  const [code, setCode] = useState('');
  const [running, setRunning] = useState(false);
  const [problem, setProblem] = useState('');
  const submit = useRef<HTMLButtonElement>(null);
  useLayoutEffect(() => setActionBusy(submit.current, running), [running]);
  const lifetime = useRef(new AbortController());
  const generation = useRef(0);
  async function followJob(resume = false) {
    const epoch = ++generation.current;
    await watchJob<JobState & { result?: string; width?: number; height?: number }>({
      read: signal => apiGet('/api/scraping/cover', signal),
      active: () => !lifetime.current.signal.aborted && epoch === generation.current,
      render: state => {
        setRunning(state.status === 'running');
        if (state.status === 'running') resume = false;
        if (state.status === 'failed' && !resume) setProblem(state.error || '采集未取得');
        if (state.status === 'complete' && !resume) toast(state.result || '封面采集完成');
      },
      disconnected: () => setProblem('连接中断，正在重新读取后台进度'),
    });
  }
  useEffect(() => { void followJob(true); return () => lifetime.current.abort(); }, []);
  async function fetchCover() {
    if (running) return;
    generation.current++;
    setRunning(true); setProblem('');
    try {
      await apiSend('/api/scraping/cover', { code }, 'POST', lifetime.current.signal);
      await followJob();
    } catch (cause) {
      if (!lifetime.current.signal.aborted) { setRunning(false); setProblem(errorMessage(cause)); }
    }
  }
  if (error) return <div role="alert" dangerouslySetInnerHTML={{ __html: noteHtml(error, { variant: 'error' }) }} />;
  return <div class="scraping-page">
    <p>高清来源可能需要代理。环境代理读取服务进程的代理环境变量；应用直连仍可能经过系统隧道。</p>
    <p>封面采集保留最高可得画质，失败保留已有图片。连接检查不验证登录会话。</p>
    <section class="cleanupfieldset scraping-source" data-geist-fieldset>
      <div class="geist-fieldset-content scraping-fields">
        <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('scraping-cover', '高清封面') }} />
        <form onSubmit={event => { event.preventDefault(); void fetchCover(); }}>
          <label>馆藏番号<input class="geist-input" required value={code} disabled={running} placeholder="ABW-232"
            onInput={event => setCode(event.currentTarget.value)} /></label>
          <button ref={submit} class="geist-button primary" type="submit">抓取或升级封面</button>
        </form>
        {problem && <div role="alert" dangerouslySetInnerHTML={{ __html: noteHtml(problem, { variant: 'error' }) }} />}
      </div>
    </section>
    {data?.sources.map(source => <SourceForm key={source.source} source={source} toast={toast} />)}
  </div>;
}
