/* 「外部入口」：人物资料页上通向 みんなのAV、JavDB 与 MISSAV 的那三枚直达入口。
 *
 * 每站一个开关；JavDB 与 MISSAV 多一个镜像域名框，这两站主域名连不上时在这里换。地址
 * 由服务端拼（`peach.entry_links`），路径与占位符都在它那边——站点 id 与规范名都在账本
 * 里，前端拿不到也不该拿。`host` 是 null 的站点没有镜像可换，只画开关。
 *
 * 校验也只在服务端：哪种地址算得上一条入口是它说了算，前端复制一份判定只会漂。 */
import { useState, type FormEvent } from 'react';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Input } from '@/components/base/input/input';
import { Switch } from '@/components/base/switch/switch';

import { apiSend } from '../../api';
import type { EntryLinkSite, EntryLinksState } from '../bundle';
import { ErrorText, Footer, Help, Rows, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

export function EntryLinksForm({ initial, receipt }: {
  initial: EntryLinksState;
  receipt(message: string): void;
}) {
  const [sites, setSites] = useState<EntryLinkSite[]>(initial.sites);
  const action = useAction();

  const change = (key: string, patch: Partial<EntryLinkSite>) =>
    setSites((rows) => rows.map((row) => (row.key === key ? { ...row, ...patch } : row)));

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const body = {
      sites: Object.fromEntries(sites.map((site) =>
        [site.key, site.host === null ? { enabled: site.enabled }
          : { enabled: site.enabled, host: site.host }])),
    };
    void action.run('save', (signal) =>
      apiSend<EntryLinksState>('/api/configuration/entry-links', body, 'POST', signal),
      (next) => {
        setSites(next.sites);
        receipt('已保存配置');
      });
  };

  return (
    <Section title="外部入口" onSubmit={submit}>
      <Rows>
        {sites.map((site) => (
          <SettingsRow key={site.key} label={site.label}
            description="在女优资料页给出这个站点的直达入口。">
            <Switch aria-label={`在资料页显示 ${site.label} 入口`} isSelected={site.enabled}
              onChange={(enabled) => change(site.key, { enabled })} />
          </SettingsRow>
        ))}
      </Rows>
      <Stack divided>
        <Help>账本里没有这个站点 id 的人物不显示它那一枚入口，地址不会退回站内搜索。
          JavDB 与 MISSAV 只收 JAV 女优，这两枚还要账本里有哪个 JAV 目录站给过她 id 才出现；
          FC2 个人摄那类创作者没有这种 id，资料页上也就没有这一行。
          这两站的主域名连不上时，把能打开的那个镜像域名填在下面，后面的路径由 Peach 自己拼。</Help>
        {sites.filter((site) => site.host !== null).map((site) => (
          <Input key={site.key} id={`entry-link-${site.key}`} label={`${site.label} 镜像域名`}
            autoComplete="off" maxLength={100} value={site.host ?? ''}
            onChange={(host) => change(site.key, { host })}
            validationBehavior="aria"
            hint={`只写域名本身，默认 ${site.default_host}`} />
        ))}
        {action.error ? <ErrorText>{action.error}</ErrorText> : null}
      </Stack>
      <Footer>
        <Button type="submit" {...busyProps(action.busy === 'save')}>保存配置</Button>
      </Footer>
    </Section>
  );
}
