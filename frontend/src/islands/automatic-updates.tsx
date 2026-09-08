import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import { fieldsetTitle, selectFieldHtml, wireSelectField, setActionBusy } from '@peach/legacy/ui';
import { apiSend, errorMessage } from '../api';

export interface AutomaticUpdateState { mode: string; interval_hours: number; available: boolean; download_available: boolean; error?: string }

export function AutomaticUpdateSettings({ initial, receipt }: { initial: AutomaticUpdateState; receipt(message: string): void }) {
  const [mode, setMode] = useState(initial.mode);
  const [hours, setHours] = useState(initial.interval_hours);
  const [error, setError] = useState(initial.error || '');
  const options = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const busy = useRef(false);
  const lifetime = useRef(new AbortController());
  useEffect(() => () => lifetime.current.abort(), []);
  useLayoutEffect(() => {
    const root = options.current!;
    root.innerHTML = selectFieldHtml([['6','每 6 小时'],['24','每天'],['168','每周']],String(initial.interval_hours),{label:'检查频率',className:'configselect',attr:'data-fixed-width'});
    const field = wireSelectField(root.firstElementChild!);
    const change = () => setHours(Number(field.value));
    field.addEventListener('change', change);
    return () => { field.removeEventListener('change', change); root.replaceChildren(); };
  }, []);
  async function save() {
    if (busy.current) return;
    busy.current = true; setActionBusy(button.current, true); setError('');
    try {
      await apiSend<AutomaticUpdateState>('/api/configuration/automatic-updates',{mode,interval_hours:hours},'POST',lifetime.current.signal);
      if (!lifetime.current.signal.aborted) receipt('已保存自动更新设置');
    } catch (cause) { if (!lifetime.current.signal.aborted) setError(errorMessage(cause)); }
    finally { busy.current = false; setActionBusy(button.current, false); }
  }
  return <form class="configfieldset" data-geist-fieldset onSubmit={event => { event.preventDefault(); void save(); }}>
    <div class="geist-fieldset-content">
      <div dangerouslySetInnerHTML={{__html:fieldsetTitle('automaticUpdatesTitle','自动更新')}} />
      <div class="configoptions" role="group" aria-labelledby="automaticUpdatesTitle">
        <label class="configtoggle"><span>自动检查新版本</span><input class="ptoggle" type="checkbox" role="switch" checked={mode !== 'off'} disabled={!initial.available} onChange={event => setMode(event.currentTarget.checked ? 'check' : 'off')} /></label>
        <label class="configtoggle"><span>自动下载更新</span><input class="ptoggle" type="checkbox" role="switch" checked={mode === 'download'} disabled={!initial.available || !initial.download_available || mode === 'off'} onChange={event => setMode(event.currentTarget.checked ? 'download' : 'check')} /></label>
      </div>
      <div ref={options} />
      <p class="confighelp">{!initial.available ? '自动更新需要由托盘管理的服务。' : initial.download_available ? '开启后一分钟内开始检查。下载完成后，在此确认重启安装。' : '开启后一分钟内开始检查。源码运行请前往发布页获取新版本。'}</p>
      {error && <p class="configbad" role="alert">{error}</p>}
    </div>
    <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button ref={button} type="submit" class="geist-button" disabled={!initial.available}>保存自动更新</button></footer>
  </form>;
}
