import { useRef, useState } from 'preact/hooks';
import { apiSend } from '../api';
import { SelectField, SettingsSection, useSubmitAction } from '../settings-controls';

export interface AutomaticUpdateState { mode: string; interval_hours: number; available: boolean; download_available: boolean; error?: string }

export function AutomaticUpdateSettings({ initial, receipt }: { initial: AutomaticUpdateState; receipt(message: string): void }) {
  const [mode, setMode] = useState(initial.mode);
  const [hours, setHours] = useState(initial.interval_hours);
  const button = useRef<HTMLButtonElement>(null);
  const action = useSubmitAction(button, initial.error);
  const save = () => action.run(signal => apiSend<AutomaticUpdateState>('/api/configuration/automatic-updates',{mode,interval_hours:hours},'POST',signal),
    () => receipt('已保存自动更新设置'));
  return <SettingsSection titleId="automaticUpdatesTitle" title="自动更新" error={action.error}
    onSubmit={event => { event.preventDefault(); if(initial.available) void save(); }}
    footer={<button ref={button} type="submit" class="geist-button" disabled={!initial.available}>保存自动更新</button>}>
      <div class="configoptions" role="group" aria-labelledby="automaticUpdatesTitle">
        <label class="configtoggle"><span>自动检查新版本</span><input class="ptoggle" type="checkbox" role="switch" checked={mode !== 'off'} disabled={!initial.available} onChange={event => setMode(event.currentTarget.checked ? 'check' : 'off')} /></label>
        <label class="configtoggle"><span>自动下载更新</span><input class="ptoggle" type="checkbox" role="switch" checked={mode === 'download'} disabled={!initial.available || !initial.download_available || mode === 'off'} onChange={event => setMode(event.currentTarget.checked ? 'download' : 'check')} /></label>
      </div>
      <SelectField value={String(hours)} onChange={value => setHours(Number(value))} label="检查频率" fixed
        options={ [['6','每 6 小时'],['24','每天'],['168','每周']] } />
      <p class="confighelp">{!initial.available ? '自动更新需要由托盘管理的服务。' : initial.download_available ? '开启后一分钟内开始检查。下载完成后，在此确认重启安装。' : '开启后一分钟内开始检查。源码运行请前往发布页获取新版本。'}</p>
  </SettingsSection>;
}
