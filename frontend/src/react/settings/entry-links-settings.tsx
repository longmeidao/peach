/* 「外部入口」：人物资料页上通向 JavDB、minnano-av 与 MISSAV 的那三枚直达入口。
 *
 * 每站一个开关加一条地址模板。地址由服务端拼（`peach.entry_links`），这一页交的只是
 * 模板本身——站点 id 与规范名都在账本里，前端拿不到也不该拿。模板里的占位符由服务端
 * 按站点给（`{javdb_id}`、`{minnano_id}`、`{name}`），所以提示里直接写它那一个。
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
        [site.key, { enabled: site.enabled, template: site.template }])),
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
        <Help>账本里没有这个站点 id 的人物不显示它那一枚入口，地址不会退回站内搜索。</Help>
        {sites.map((site) => (
          <Input key={site.key} id={`entry-link-${site.key}`} label={`${site.label} 地址模板`}
            autoComplete="off" maxLength={300} value={site.template}
            onChange={(template) => change(site.key, { template })}
            validationBehavior="aria"
            hint={`用 {${site.placeholder}} 占位，默认 ${site.default_template}`} />
        ))}
        {action.error ? <ErrorText>{action.error}</ErrorText> : null}
      </Stack>
      <Footer>
        <Button type="submit" {...busyProps(action.busy === 'save')}>保存配置</Button>
      </Footer>
    </Section>
  );
}
