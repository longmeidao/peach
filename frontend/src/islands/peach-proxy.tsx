import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { fieldsetTitle, selectFieldHtml, wireSelectField, setActionBusy } from '@peach/legacy/ui';
import { apiSend, errorMessage } from '../api';

export interface PeachProxyState { mode: string; proxy_saved: boolean; needs_selection: boolean }
export function PeachProxy({ initial, receipt }: { initial: PeachProxyState; receipt(message: string): void }) {
  const [saved, setSaved] = useState(initial);
  const [mode, setMode] = useState(initial.mode);
  const [address, setAddress] = useState('');
  const [error, setError] = useState('');
  const busy = useRef(false);
  const mount = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const lifetime = useRef(new AbortController());
  useEffect(() => () => lifetime.current.abort(), []);
  useLayoutEffect(() => {
    const root = mount.current!;
    root.innerHTML = selectFieldHtml([['environment','系统代理'],['direct','直连'],['proxy','自定义']],initial.mode,{label:'Peach 代理'});
    const field = wireSelectField(root.firstElementChild!);
    const change = () => setMode(field.value);
    field.addEventListener('change', change);
    return () => { field.removeEventListener('change',change); root.replaceChildren(); };
  }, []);
  async function save() {
    if (busy.current) return;
    busy.current = true; setActionBusy(button.current,true); setError('');
    try {
      const next = await apiSend<PeachProxyState>('/api/configuration/peach-proxy',{mode,proxy:address},'POST',lifetime.current.signal);
      if (!lifetime.current.signal.aborted) { setSaved(next); setAddress(''); receipt('已保存 Peach 代理'); }
    } catch (cause) { if (!lifetime.current.signal.aborted) setError(errorMessage(cause)); }
    finally { busy.current = false; setActionBusy(button.current,false); }
  }
  return <form id="peachProxy" class="configfieldset" data-geist-fieldset onSubmit={event => {event.preventDefault();void save();}}>
    <div class="geist-fieldset-content">
      <div dangerouslySetInnerHTML={{__html:fieldsetTitle('peachProxyTitle','Peach 代理')}} />
      <p class="confighelp">采集来源选择“Peach 代理”时共用此设置。</p>
      <div ref={mount} />
      {mode === 'proxy' && <label class="configfield">代理地址<input class="geist-input" type="password" autoComplete="off" value={address}
        placeholder={saved.proxy_saved ? '已保存，留空保留' : 'http://127.0.0.1:7890'} onInput={event => setAddress(event.currentTarget.value)} /></label>}
      {saved.needs_selection && <p class="configbad">已有来源的代理地址不同，请选择公共连接方式。</p>}
      {error && <p class="configbad" role="alert">{error}</p>}
    </div>
    <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button ref={button} class="geist-button primary" type="submit">保存代理</button></footer>
  </form>;
}
