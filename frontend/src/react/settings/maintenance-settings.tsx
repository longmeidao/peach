/* 「更新与维护」分组：自动更新、检查更新、播放兼容修复、运行信息与卸载。 */
import { useState, type FormEvent } from 'react';
import { confirmModal } from '@peach/legacy/ui';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Checkbox } from '@/components/base/checkbox/checkbox';
import { Select, SelectItem } from '@/components/base/select/select';
import { Switch } from '@/components/base/switch/switch';

import { apiSend } from '../../api';
import type { AutomaticUpdateState, ConfigurationFact, ConfigurationGroupProps, UninstallState } from '../bundle';
import { PathLine } from '../components/path-line';
import { MediaRepair } from './media-repair';
import { ReleaseUpdates } from './release-updates';
import { Disclosure, ErrorText, ExternalLink, Fact, FactList, Footer, Help, Rows, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

const INTERVALS = [['6', '每 6 小时'], ['24', '每天'], ['168', '每周']] as const;

export function MaintenanceSettings({ data, receipt }: ConfigurationGroupProps) {
  return (
    <div className="flex flex-col gap-6">
      {data.automatic_updates ? <AutomaticUpdates initial={data.automatic_updates} receipt={receipt} /> : null}
      {data.updates ? <ReleaseUpdates initial={data.updates} initialJob={data.update_job} /> : null}
      <MediaRepair />
      <Facts facts={data.facts} />
      {data.uninstall ? <UninstallSettings uninstall={data.uninstall} receipt={receipt} /> : null}
    </div>
  );
}

export function AutomaticUpdates({ initial, receipt }: { initial: AutomaticUpdateState; receipt(message: string): void }) {
  const [mode, setMode] = useState(initial.mode);
  const [hours, setHours] = useState(initial.interval_hours);
  const action = useAction(initial.error);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!initial.available) return;
    void action.run('save', (signal) => apiSend<AutomaticUpdateState>('/api/configuration/automatic-updates',
      { mode, interval_hours: hours }, 'POST', signal), () => receipt('已保存配置'));
  };

  const help = !initial.available
    ? '自动更新需要由托盘管理的服务。'
    : initial.download_available
      ? '开启后一分钟内开始检查。下载完成后，在此确认重启安装。'
      : '开启后一分钟内开始检查。源码运行请前往发布页获取新版本。';
  return (
    <Section title="自动更新" onSubmit={submit}>
      <Rows>
        <SettingsRow label="自动检查新版本">
          <Switch aria-label="自动检查新版本" isSelected={mode !== 'off'} isDisabled={!initial.available}
            onChange={(on) => setMode(on ? 'check' : 'off')} />
        </SettingsRow>
        <SettingsRow label="自动下载更新">
          <Switch aria-label="自动下载更新" isSelected={mode === 'download'}
            isDisabled={!initial.available || !initial.download_available || mode === 'off'}
            onChange={(on) => setMode(on ? 'download' : 'check')} />
        </SettingsRow>
        <SettingsRow label="检查频率" description={help}>
          <Select aria-label="检查频率" selectedKey={String(hours)} isDisabled={!initial.available}
            onSelectionChange={(key) => { if (key !== null) setHours(Number(key)); }}>
            {INTERVALS.map(([key, name]) => <SelectItem key={key} id={key}>{name}</SelectItem>)}
          </Select>
        </SettingsRow>
      </Rows>
      {action.error ? <Stack divided><ErrorText>{action.error}</ErrorText></Stack> : null}
      <Footer>
        <Button type="submit" disabled={!initial.available} {...busyProps(action.busy === 'save')}>保存配置</Button>
      </Footer>
    </Section>
  );
}

function Facts({ facts }: { facts: ConfigurationFact[] }) {
  return (
    <Section title="运行信息">
      <FactList>
        {facts.map((fact) => (
          <Fact key={fact.term} term={fact.term}>
            {fact.value}
            {fact.download_url ? <ExternalLink href={fact.download_url}>{fact.download_label}</ExternalLink> : null}
          </Fact>
        ))}
      </FactList>
    </Section>
  );
}

export function UninstallSettings(
  { uninstall, receipt }: { uninstall: UninstallState; receipt(message: string): void },
) {
  const [removeData, setRemoveData] = useState(false);
  const [accepted, setAccepted] = useState('');
  const remove = () => void confirmModal({
    title: '卸载 Peach',
    danger: true,
    body: removeData
      ? '将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。'
      : '将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。',
    confirmLabel: '卸载 Peach',
    onConfirm: async () => {
      const result = await apiSend<{ message: string }>('/api/configuration/uninstall', { delete_data: removeData, confirmation: '卸载 Peach' });
      setAccepted(result.message);
    },
  });
  // 底栏左边一句说这颗按钮此刻意味着什么：拦住卸载的理由（源码安装、更新还在跑）和按下去
  // 之后的回执都在答「这颗现在能不能按」，摆在正文末尾就得先读完整段说明才找得到。
  const status = accepted || uninstall.message;
  const paths = [...new Set([uninstall.data_root, ...uninstall.directories])];
  return (
    <Section id="uninstallPeach" title="卸载 Peach">
      <Stack>
        {uninstall.available ? <Help>卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。</Help> : null}
        <Checkbox isSelected={removeData} isDisabled={!uninstall.full_available || Boolean(accepted)} onChange={setRemoveData}>
          完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存
        </Checkbox>
        <Disclosure summary="数据目录">
          {paths.map((path) => (
            <PathLine key={path} path={path} className="text-body-2-regular text-text-secondary" onRevealed={receipt} />
          ))}
        </Disclosure>
      </Stack>
      <Footer status={status ? <p role={accepted ? 'status' : undefined}>{status}</p> : null}>
        <Button variant="danger" disabled={!uninstall.available || Boolean(accepted)} onClick={remove}>卸载 Peach</Button>
      </Footer>
    </Section>
  );
}
