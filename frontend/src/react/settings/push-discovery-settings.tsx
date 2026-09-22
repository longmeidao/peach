/* 「推送发现」：新文件落地就进账本，不必等下一轮全量扫描。
 *
 * 两条通道各一个开关。本地那条订阅本机文件夹的文件系统事件；网盘那条等 CloudDrive2 往
 * Peach 推一条通知，所以要给出地址、共享密钥和一张「云端路径前缀 → 媒体根」的对应表。
 * 定期全量扫描不受这一页影响，它仍是漏发时的兜底。
 *
 * 前缀怎么算合法、根是不是已声明过，都由服务端判（`peach.push_discovery`）；这一页只把
 * 那句原因显示出来，不在前端复制一份判定。 */
import { useState, type FormEvent } from 'react';
import { RiCloseLine } from '@remixicon/react';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { IconButton } from '@/components/base/buttons/icon-button';
import { Input } from '@/components/base/input/input';
import { Select, SelectItem } from '@/components/base/select/select';
import { Switch } from '@/components/base/switch/switch';

import { apiSend, errorMessage } from '../../api';
import type { PushDiscoveryPrefix, PushDiscoveryState } from '../bundle';
import { ErrorText, Fact, FactList, FieldLabel, Footer, Help, Rows, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

const SAVE_URL = '/api/configuration/push-discovery';
const SECRET_URL = '/api/configuration/push-discovery/secret';

export function PushDiscoveryForm({ initial, receipt }: {
  initial: PushDiscoveryState;
  receipt(message: string): void;
}) {
  const [state, setState] = useState(initial);
  const [rows, setRows] = useState<PushDiscoveryPrefix[]>(initial.prefixes);
  const [failure, setFailure] = useState('');
  const action = useAction();
  const roots = state.media_roots;

  const settle = (next: PushDiscoveryState, message: string) => {
    setState(next);
    setRows(next.prefixes);
    setFailure('');
    receipt(message);
  };

  const edit = (index: number, patch: Partial<PushDiscoveryPrefix>) =>
    setRows((list) => list.map((row, i) => (i === index ? { ...row, ...patch } : row)));

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const body = {
      enabled: state.enabled, watch_local: state.watch_local, cloud: state.cloud, prefixes: rows,
    };
    void action.run('save', (signal) => apiSend<PushDiscoveryState>(SAVE_URL, body, 'POST', signal),
      (next) => settle(next, '已保存配置'), (cause) => setFailure(errorMessage(cause)));
  };

  const rotate = () => {
    void action.run('secret', (signal) => apiSend<PushDiscoveryState>(SECRET_URL, {}, 'POST', signal),
      (next) => settle(next, '已更换共享密钥'), (cause) => setFailure(errorMessage(cause)));
  };

  return (
    <Section title="推送发现" onSubmit={submit}>
      <Rows>
        <SettingsRow label="新文件落地就入库"
          description="打开之后不必等下一轮扫描。定期全量扫描照常进行，漏掉的由它补上。">
          <Switch aria-label="新文件落地就入库" isSelected={state.enabled} isDisabled={!state.available}
            onChange={(enabled) => setState({ ...state, enabled })} />
        </SettingsRow>
        <SettingsRow label="监视本机文件夹"
          description="订阅本地来源的文件系统事件。网盘挂载不监视——遍历它就是走网络。">
          <Switch aria-label="监视本机文件夹" isSelected={state.watch_local}
            isDisabled={!state.available || !state.enabled}
            onChange={(watchLocal) => setState({ ...state, watch_local: watchLocal })} />
        </SettingsRow>
        <SettingsRow label="接收 CloudDrive2 通知"
          description="由 CloudDrive2 把网盘里的新文件推给 Peach。只接受本机与局域网发来的请求。">
          <Switch aria-label="接收 CloudDrive2 通知" isSelected={state.cloud}
            isDisabled={!state.available || !state.enabled}
            onChange={(cloud) => setState({ ...state, cloud })} />
        </SettingsRow>
      </Rows>
      <Stack divided>
        <FactList>
          <Fact term="通知地址">{state.endpoint}</Fact>
          <Fact term="共享密钥">{state.secret || '还没有生成'}</Fact>
          <Fact term="本机文件夹监视">
            {state.local_running ? state.local_roots.join('、') : state.local_message || '没有运行'}
          </Fact>
          <Fact term="已入库">{`${state.queue.ingested} 个文件，队列里还有 ${state.queue.pending} 条`}</Fact>
        </FactList>
      </Stack>
      <Stack divided>
        <div className="flex flex-col gap-3">
          <FieldLabel>云端路径前缀</FieldLabel>
          <Help>左边填 CloudDrive2 里看到的那一层目录，右边选它对应哪个媒体根。
            CloudDrive2 给的是它自己的路径，Peach 按这张表换算成账本里的盘符路径。</Help>
          <div role="group" aria-label="云端路径前缀" className="flex flex-col gap-3">
            {rows.map((row, index) => (
              <div key={index} className="flex items-start gap-2">
                <Input className="min-w-0 flex-1" aria-label={`云端路径前缀 ${index + 1}`}
                  placeholder="/115" autoComplete="off" maxLength={200} value={row.prefix}
                  onChange={(prefix) => edit(index, { prefix })} />
                <Select aria-label={`前缀 ${index + 1} 对应的媒体根`} selectedKey={row.root}
                  onSelectionChange={(key) => { if (key !== null) edit(index, { root: String(key) }); }}>
                  {roots.map((root) => <SelectItem key={root} id={root}>{root}</SelectItem>)}
                </Select>
                <IconButton icon={RiCloseLine} aria-label="移除这一条"
                  onClick={() => setRows((list) => list.filter((_row, i) => i !== index))} />
              </div>
            ))}
          </div>
          <div>
            <Button size="small"
              onClick={() => setRows((list) => [...list, { prefix: '', root: roots[0] ?? '' }])}>
              添加前缀
            </Button>
          </div>
        </div>
        {failure || action.error ? <ErrorText>{failure || action.error}</ErrorText> : null}
      </Stack>
      <Footer status="CloudDrive2 那一侧要填的地址、密钥与设置步骤见帮助文档。">
        <Button onClick={rotate} disabled={!state.available}
          {...busyProps(action.busy === 'secret')}>更换密钥</Button>
        <Button type="submit" disabled={!state.available} {...busyProps(action.busy === 'save')}>
          保存配置
        </Button>
      </Footer>
    </Section>
  );
}
