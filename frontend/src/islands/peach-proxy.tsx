import { useRef, useState } from 'preact/hooks';
import { apiSend } from '../api';
import { SelectField, SettingsSection, useSubmitAction } from '../settings-controls';

export interface PeachProxyState { mode: string; proxy_saved: boolean; needs_selection: boolean }
export function PeachProxy({ initial, receipt }: { initial: PeachProxyState; receipt(message: string): void }) {
  const [saved, setSaved] = useState(initial);
  const [mode, setMode] = useState(initial.mode);
  const [address, setAddress] = useState('');
  const button = useRef<HTMLButtonElement>(null);
  const action = useSubmitAction(button);
  const save = () => action.run(signal => apiSend<PeachProxyState>('/api/configuration/peach-proxy',{mode,proxy:address},'POST',signal),
    next => { setSaved(next); setAddress(''); receipt('已保存 Peach 代理'); });
  return <SettingsSection id="peachProxy" titleId="peachProxyTitle" title="Peach 代理"
    help="采集来源选择“Peach 代理”时共用此设置。" error={action.error}
    onSubmit={event => { event.preventDefault(); void save(); }}
    footer={<button ref={button} class="geist-button primary" type="submit">保存代理</button>}>
      <SelectField value={mode} onChange={setMode} label="Peach 代理" fixed
        options={ [['environment','系统代理'],['direct','直连'],['proxy','自定义']] } />
      {mode === 'proxy' && <div class="configfield"><label htmlFor="peachProxyAddress">代理地址</label><input id="peachProxyAddress" class="geist-input" type="password" autoComplete="off" value={address}
        placeholder={saved.proxy_saved ? '已保存，留空保留' : 'http://127.0.0.1:7890'} onInput={event => setAddress(event.currentTarget.value)} /></div>}
      {saved.needs_selection && <p class="configbad">已有来源的代理地址不同，请选择公共连接方式。</p>}
  </SettingsSection>;
}
