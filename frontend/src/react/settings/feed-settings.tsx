/* 「订阅源」小节：列表、开关、移除、上次拉取时间与错误（ADR-0042）。
 *
 * 数据不在 `/api/configuration` 那份快照里：订阅源有自己的写接口，开关与移除之后要重取的
 * 只是这一节。自己收自己的状态，不进共用的 `QueryClient`——这一节是「通用」组里唯一
 * 不看配置快照的内容，而它的几个兄弟分区在用例里是脱离 Provider 单独挂的。
 *
 * 订阅只从人物页的「订阅新作」进，这里不收地址（ADR-0047）。拉回来的新作在首页与人物页的
 * 「新作 · 未入库」里，不在设置里列——设置页列一遍就成了第二个入口，两处的已读状态会各说各话。 */
import { useCallback, useEffect, useState } from 'react';
import { RiCloseLine } from '@remixicon/react';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Switch } from '@/components/base/switch/switch';

import { apiGet, apiSend, errorMessage } from '../../api';
import { Note } from '../components/note';
import { ErrorText, Footer, Help, Rows, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

interface FeedSource {
  id: number;
  kind: string;
  kind_label: string;
  name: string;
  url: string;
  entity_name: string | null;
  enabled: boolean;
  interval_minutes: number;
  last_fetched_at: string | null;
  last_error: string | null;
  last_new_count: number;
  seen: number;
}

interface FeedsData {
  sources: FeedSource[];
  unread: number;
}

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

export function FeedSettings() {
  const [data, setData] = useState<FeedsData | null>(null);
  const [failure, setFailure] = useState('');
  /* 服务端是唯一真相：开关与移除之后重取整份，不在前端按响应拼一份新的本地状态。 */
  const reload = useCallback(async (signal?: AbortSignal) => {
    try {
      const payload = await apiGet<FeedsData>('/api/feeds', signal);
      // 认不出的响应当没读到：没有 sources 的那份不是这一节的数据，画出来只会在
      // 第一次取长度时炸掉整页配置。
      if (Array.isArray(payload?.sources)) setData(payload);
    } catch (cause) {
      if (!signal?.aborted) setFailure(errorMessage(cause));
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);
  const action = useAction();

  const toggle = (source: FeedSource, enabled: boolean) => {
    void action.run(`enabled-${source.id}`, (signal) => apiSend('/api/feeds/source',
      { action: 'enabled', id: source.id, enabled }, 'POST', signal), () => void reload());
  };

  const remove = (source: FeedSource) => {
    void action.run(`remove-${source.id}`, (signal) => apiSend('/api/feeds/source',
      { action: 'remove', id: source.id }, 'POST', signal), () => void reload());
  };

  // 立即拉取走的是和定时同一条路，只是把到期判断换成「全部启用的源」。
  const check = () => {
    void action.run('check', (signal) => apiSend('/api/feeds/check', { all: true }, 'POST', signal),
      () => void reload());
  };

  if (!data) {
    return (
      <Section title="订阅源">
        <Stack>
          {failure
            ? <Note tone="error" title="打不开订阅源">{failure}</Note>
            : <Help>正在读订阅源。</Help>}
        </Stack>
      </Section>
    );
  }

  return (
    <Section title="订阅源">
      {data.sources.length ? (
        <Rows>
          {data.sources.map((source) => (
            <SettingsRow key={source.id} label={source.name || source.url} description={describe(source)}>
              {/* 移除键取 xs 那一档：和开关一样 24px 高，两样并排才读成同一行的两个控件。 */}
              <div className="flex items-center gap-2">
                <Switch aria-label={`启用 ${source.name || source.url}`} isSelected={source.enabled}
                  onChange={(enabled) => toggle(source, enabled)} />
                <Button variant="danger" size="xs" iconOnly leadingIcon={RiCloseLine}
                  aria-label={`移除 ${source.name || source.url}`}
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
        <Button onClick={check} {...busyProps(action.busy === 'check')}>立即拉取</Button>
      </Footer>
    </Section>
  );
}
