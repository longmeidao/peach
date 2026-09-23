/* 「通用」分组：开机自启与桌面快捷方式，人物资料页那三枚外部入口。 */
import { useState, type FormEvent } from 'react';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Switch } from '@/components/base/switch/switch';

import { apiSend } from '../../api';
import type { ConfigurationGroupProps, StartupState } from '../bundle';
import { EntryLinksForm } from './entry-links-settings';
import { ErrorText, Footer, Help, Rows, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

export function GeneralSettings({ data, receipt }: ConfigurationGroupProps) {
  return (
    <div className="flex flex-col gap-6">
      {data.startup ? <StartupSettings startup={data.startup} receipt={receipt} /> : null}
      {data.entry_links ? <EntryLinksForm initial={data.entry_links} receipt={receipt} /> : null}
    </div>
  );
}

export function StartupSettings({ startup, receipt }: { startup: StartupState; receipt(message: string): void }) {
  const [enabled, setEnabled] = useState(startup.enabled);
  const [silent, setSilent] = useState(startup.silent);
  const [desktop, setDesktop] = useState(startup.desktop);
  const action = useAction();
  // 桌面快捷方式只有 Windows 有，桌面上已经摆着另一份安装的图标时也不给动；两种情况后端
  // 都在 desktop_message 里说了原因，所以按它有没有内容判禁用，不在前端判平台。
  const desktopReady = startup.available && !startup.desktop_message;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!startup.available) return;
    void action.run('save', (signal) => apiSend('/api/configuration/startup', { enabled, silent, desktop }, 'POST', signal),
      () => receipt('已保存配置'));
  };

  return (
    <Section title="开机自启" onSubmit={submit}>
      <Rows>
        <SettingsRow label="开机后启动 Peach">
          <Switch aria-label="开机后启动 Peach" isSelected={enabled} isDisabled={!startup.available} onChange={setEnabled} />
        </SettingsRow>
        <SettingsRow label="静默启动" description="开机后只显示托盘图标，不打开网页；「开机后启动 Peach」打开时生效。">
          <Switch aria-label="静默启动" isSelected={silent} isDisabled={!startup.available || !enabled} onChange={setSilent} />
        </SettingsRow>
        <SettingsRow label="在桌面创建快捷方式" description={startup.desktop_message || '双击图标打开 Peach 网页；卸载时一并移除。'}>
          <Switch aria-label="在桌面创建快捷方式" isSelected={desktop} isDisabled={!desktopReady} onChange={setDesktop} />
        </SettingsRow>
      </Rows>
      {startup.message || action.error ? (
        <Stack divided>
          {startup.message ? <Help>{startup.message}</Help> : null}
          {action.error ? <ErrorText>{action.error}</ErrorText> : null}
        </Stack>
      ) : null}
      <Footer>
        <Button type="submit" disabled={!startup.available} {...busyProps(action.busy === 'save')}>保存配置</Button>
      </Footer>
    </Section>
  );
}
