/* 「外部入口」：人物资料页上通向 みんなのAV、JavDB 与 MISSAV 的那几枚直达入口。
 *
 * 这里只有 JavDB 与 MISSAV 两个地址框，这两站主域名连不上时在这里换成能打开的镜像；
 * みんなのAV 只此一家，没有可换的东西，它不出现在这一页上。框默认是空的，占位符写着
 * 当前在用的那个域名——默认值不需要使用者先抄一遍，清空就回到它。
 *
 * 入口出不出现不由这里决定：地址由服务端拼（`peach.entry_links`），站点 id 缺席那一枚
 * 就不在资料页上，所以这里没有开关。校验也只在服务端，前端复制一份判定只会漂。 */
import { useState, type FormEvent } from 'react';

import { Button } from '@/components/base/buttons/button';
import { Input } from '@/components/base/input/input';

import { apiSend } from '../../api';
import type { EntryLinkSite, EntryLinksState } from '../bundle';
import { ErrorText, Footer, Help, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

export function EntryLinksForm({ initial, receipt }: {
  initial: EntryLinksState;
  receipt(message: string): void;
}) {
  const [sites, setSites] = useState<EntryLinkSite[]>(initial.sites);
  const action = useAction();

  const change = (key: string, host: string) =>
    setSites((rows) => rows.map((row) => (row.key === key ? { ...row, host } : row)));

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const body = { sites: Object.fromEntries(sites.map((site) => [site.key, { host: site.host }])) };
    void action.run('save', (signal) =>
      apiSend<EntryLinksState>('/api/configuration/entry-links', body, 'POST', signal),
      (next) => {
        setSites(next.sites);
        receipt('已保存配置');
      });
  };

  return (
    <Section title="外部入口" onSubmit={submit}>
      <Stack divided>
        <Help>账本里没有这个站点 id 的人物不显示它那一枚入口，地址不会退回站内搜索。
          JavDB 与 MISSAV 只收 JAV 女优，这两枚还要账本里有哪个 JAV 目录站给过她 id 才出现；
          FC2 个人摄那类创作者没有这种 id，资料页上也就没有这一行。
          这两站的主域名连不上时，把能打开的那个镜像域名填在下面，后面的路径由 Peach 自己拼。</Help>
        {sites.map((site) => (
          <Input key={site.key} id={`entry-link-${site.key}`} label={`${site.label} 地址`}
            autoComplete="off" maxLength={100} value={site.host}
            placeholder={site.default_host}
            onChange={(host) => change(site.key, host)}
            validationBehavior="aria" hint="只写域名本身，留空就是默认" />
        ))}
        {action.error ? <ErrorText>{action.error}</ErrorText> : null}
      </Stack>
      <Footer>
        <Button type="submit" {...busyProps(action.busy === 'save')}>保存配置</Button>
      </Footer>
    </Section>
  );
}
