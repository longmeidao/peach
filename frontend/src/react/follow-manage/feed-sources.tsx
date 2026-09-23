/* 关注管理页的「订阅源」页签：列表、开关、移除、上次拉取时间与错误（ADR-0042）。
 *
 * 订阅只从人物页的「订阅新作」进，这里不收地址（ADR-0047）。拉回来的新作排在首页与人物页
 * 筛选栏下面那一行，不在这里列——这里再列一遍就成了第二个入口，两处的已读状态会各说各话。
 * 服务端是唯一真相：开关与移除之后重取这一份，不在前端按响应拼一份新的本地状态。 */
import { useQuery } from '@tanstack/react-query';
import { RiCloseLine } from '@remixicon/react';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Switch } from '@/components/base/switch/switch';

import { errorMessage } from '../../api';
import { Note } from '../components/note';
import { queryClient } from '../query';
import { ErrorText, Footer, Help, Rows, Section, Stack } from '../settings/section';
import { busyProps, useAction } from '../settings/use-action';
import {
  checkFeeds, FEEDS_KEY, fetchFeeds, removeFeed, setFeedEnabled, type FeedSource,
} from './follow-manage';

/** 一行订阅源在名称下面那句话：上次什么时候拉的、拉到几条。没拉过就直说还没拉过。 */
function describe(source: FeedSource): string {
  const when = source.last_fetched_at
    ? `上次拉取 ${new Date(source.last_fetched_at).toLocaleString()}`
    : '还没拉过';
  const interval = source.interval_minutes >= 60
    ? `每 ${Math.round(source.interval_minutes / 60)} 小时一次`
    : `每 ${source.interval_minutes} 分钟一次`;
  return `${source.kind_label} · ${interval} · ${when} · 上次新增 ${source.last_new_count} 条`;
}

const reload = () => queryClient.invalidateQueries({ queryKey: FEEDS_KEY, exact: true });

export function FeedSources({ readOnly }: { readOnly: boolean }) {
  const feeds = useQuery({ queryKey: FEEDS_KEY, queryFn: ({ signal }) => fetchFeeds(signal) });
  const action = useAction();
  const data = feeds.data;

  if (!data) {
    return (
      <Section title="订阅源">
        <Stack>
          {feeds.error
            ? <Note tone="error" title="打不开订阅源">{errorMessage(feeds.error)}</Note>
            : <Help>正在读订阅源。</Help>}
        </Stack>
      </Section>
    );
  }

  const toggle = (source: FeedSource, enabled: boolean) => void action.run(`enabled-${source.id}`,
    (signal) => setFeedEnabled(source.id, enabled, signal), () => void reload());
  const remove = (source: FeedSource) => void action.run(`remove-${source.id}`,
    (signal) => removeFeed(source.id, signal), () => void reload());
  const check = () => void action.run('check', (signal) => checkFeeds(signal), () => void reload());

  return (
    <Section title="订阅源">
      {data.sources.length ? (
        <Rows>
          {data.sources.map((source) => (
            <SettingsRow key={source.id} label={source.name || source.url} description={describe(source)}>
              {/* 移除键取 xs 那一档：和开关一样 24px 高，两样并排才读成同一行的两个控件。 */}
              <div className="flex items-center gap-2">
                <Switch aria-label={`启用 ${source.name || source.url}`} isSelected={source.enabled}
                  isDisabled={readOnly} onChange={(enabled) => toggle(source, enabled)} />
                <Button variant="danger" size="xs" iconOnly leadingIcon={RiCloseLine}
                  aria-label={`移除 ${source.name || source.url}`} disabled={readOnly}
                  onClick={() => remove(source)} {...busyProps(action.busy === `remove-${source.id}`)} />
              </div>
            </SettingsRow>
          ))}
        </Rows>
      ) : null}
      <Stack divided={data.sources.length > 0}>
        {/* 拉不动的源各自把原因摆在自己那一行下面：一条源坏掉不该让整节看起来都坏了。 */}
        {data.sources.filter((source) => source.last_error).map((source) => (
          <Note key={source.id} tone="error" title={`${source.name || source.url} 拉取失败`}>
            {source.last_error}
          </Note>
        ))}
        {action.error ? <ErrorText>{action.error}</ErrorText> : null}
        <Help>在人物页点「订阅新作」就会加到这里。订阅只发现番号、建一条「未入库」的新作，不下载任何文件；新作在首页和人物页里看。</Help>
      </Stack>
      <Footer status={data.unread ? `有 ${data.unread} 条新作还没看` : '新作都看过了'}>
        <Button onClick={check} disabled={readOnly} {...busyProps(action.busy === 'check')}>立即拉取</Button>
      </Footer>
    </Section>
  );
}
