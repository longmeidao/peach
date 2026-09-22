/* 「订阅源」小节：增删、开关、上次拉取时间与错误（ADR-0042）。
 *
 * 数据不在 `/api/configuration` 那份快照里：订阅源有自己的写接口，增删开关之后要重取的
 * 只是这一节。自己收自己的状态，不进共用的 `QueryClient`——这一节是「通用」组里唯一
 * 不看配置快照的内容，而它的几个兄弟分区在用例里是脱离 Provider 单独挂的。
 *
 * 这一节只管「订阅什么、多久拉一次」。拉回来的新作在首页与人物页的「新作 · 未入库」里，
 * 不在设置里列——设置页列一遍就成了第二个入口，两处的已读状态会各说各话。 */
import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { RiCloseLine } from '@remixicon/react';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { IconButton } from '@/components/base/buttons/icon-button';
import { Input } from '@/components/base/input/input';
import { Select, SelectItem } from '@/components/base/select/select';
import { Switch } from '@/components/base/switch/switch';

import { apiGet, apiSend, errorMessage } from '../../api';
import { Note } from '../components/note';
import { ErrorText, FieldLabel, Footer, Help, Rows, Section, Stack } from './section';
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
  kinds: { value: string; label: string }[];
  min_interval_minutes: number;
  max_interval_minutes: number;
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
  /* 服务端是唯一真相：增删开关之后重取整份，不在前端按响应拼一份新的本地状态。
     拉取间隔会被后端按上下限收窄，拼出来的那份和库里的从第一次保存起就不一样。 */
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
  const kinds = data?.kinds ?? [];
  const [kind, setKind] = useState('');
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [hours, setHours] = useState('6');
  const action = useAction();

  const add = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const minutes = Math.round(Number(hours) * 60);
    void action.run('add', (signal) => apiSend('/api/feeds/source', {
      action: 'add', kind: kind || kinds[0]?.value, url: url.trim(), name: name.trim(),
      interval_minutes: Number.isFinite(minutes) ? minutes : undefined,
    }, 'POST', signal), () => {
      setUrl('');
      setName('');
      void reload();
    });
  };

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
    <Section title="订阅源" onSubmit={add}>
      {data.sources.length ? (
        <Rows>
          {data.sources.map((source) => (
            <SettingsRow key={source.id} label={source.name || source.url} description={describe(source)}>
              <div className="flex items-center gap-1">
                <Switch aria-label={`启用 ${source.name || source.url}`} isSelected={source.enabled}
                  onChange={(enabled) => toggle(source, enabled)} />
                <IconButton icon={RiCloseLine} aria-label={`移除 ${source.name || source.url}`}
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
        <div className="inline-grid grid-cols-1 gap-3 @lg:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <FieldLabel>来源类型</FieldLabel>
            <Select aria-label="来源类型" selectedKey={kind || kinds[0]?.value}
              onSelectionChange={(key) => { if (key !== null) setKind(String(key)); }}>
              {kinds.map((item) => (
                <SelectItem key={item.value} id={item.value} textValue={item.label}>{item.label}</SelectItem>
              ))}
            </Select>
          </div>
          <Input label="拉取间隔（小时）" inputMode="decimal" value={hours} onChange={setHours}
            hint={`最短 ${data.min_interval_minutes} 分钟。`} />
        </div>
        <Input label="订阅地址" placeholder="https://" value={url} onChange={setUrl}
          hint="RSS/Atom 的地址，或 JavDB 的演员页地址。只收 HTTPS。" />
        <Input label="名称" maxLength={80} placeholder="不填就用地址" value={name} onChange={setName} />
        {action.error ? <ErrorText>{action.error}</ErrorText> : null}
        <Help>订阅只发现番号、建一条「未入库」的新作，不下载任何文件。新作在首页和人物页里看。</Help>
      </Stack>
      <Footer status={data.unread ? `有 ${data.unread} 条新作还没看` : '新作都看过了'}>
        <Button onClick={check} {...busyProps(action.busy === 'check')}>立即拉取</Button>
        <Button type="submit" {...busyProps(action.busy === 'add')}>添加订阅</Button>
      </Footer>
    </Section>
  );
}
