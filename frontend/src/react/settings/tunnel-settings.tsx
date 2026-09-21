/* Cloudflare Quick Tunnel：只显示本机托盘服务实际返回的随机入口。
 * Quick Tunnel 没有稳定域名和独立身份层，服务端会在 `open` 模式下拒绝启动；
 * 这里不保存 URL 或任何密码，刷新配置页重新读取服务状态。 */
import { useEffect, useState, type FormEvent } from 'react';

import { Button } from '@/components/base/buttons/button';

import { apiSend } from '../../api';
import type { ConfigurationData, TunnelState } from '../bundle';
import { Note } from '../components/note';
import { queryClient } from '../query';
import { CONFIGURATION_KEY, fetchConfiguration } from './configuration';
import { ExternalLink, ErrorText, Footer, Help, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

/** 连接握手在服务端进行，页面按固定间隔重问，直到拿到入口或失败原因。 */
const POLL_INTERVAL = 2000;

export function TunnelSettings({ revision: initialRevision, initial, receipt }: {
  revision: string;
  initial: TunnelState;
  receipt(message: string): void;
}) {
  const [state, setState] = useState(initial);
  const [revision, setRevision] = useState(initialRevision);
  const action = useAction();
  const active = state.state === 'starting' || state.state === 'running';

  useEffect(() => {
    if (state.state !== 'starting') return undefined;
    const controller = new AbortController();
    const timer = window.setInterval(() => {
      void fetchConfiguration(controller.signal)
        .then((next: ConfigurationData) => {
          if (controller.signal.aborted || !next.tunnel) return;
          // 取回来的是整份配置，换进整页那一个键：屏幕上只有一份真相。
          queryClient.setQueryData(CONFIGURATION_KEY, next);
          setState(next.tunnel);
          setRevision(next.revision);
        })
        .catch(() => undefined);
    }, POLL_INTERVAL);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [state.state]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void action.run('toggle', (signal) => apiSend<TunnelState & { revision: string }>(
      '/api/configuration/tunnel',
      { revision, enabled: !active }, 'POST', signal,
    ), (next) => {
      setState(next);
      setRevision(next.revision);
      receipt(next.enabled ? '临时远程链接已启动' : '临时远程链接已停止');
    });
  };

  return (
    <Section title="Cloudflare 临时链接" onSubmit={submit}>
      <Stack>
        <Help>只用于临时预览；地址随机、重启后会变化。启动前必须设置访问密码。</Help>
        {!state.available
          ? <Note tone="warning" title="找不到 cloudflared">请安装官方 cloudflared，或在设置文件的 tunnel.binary 指定路径，也可用 PEACH_CLOUDFLARED 指定。</Note>
          : null}
        {state.state === 'running' && state.url
          ? <Note tone="info" title="临时链接"><ExternalLink href={state.url}>{state.url}</ExternalLink></Note>
          : null}
        {state.state === 'starting' ? <Note tone="info" title="正在连接">正在等待 Cloudflare 返回入口地址。</Note> : null}
        {state.error ? <ErrorText>{state.error}</ErrorText> : null}
      </Stack>
      <Footer status={state.enabled ? '服务重启时会按设置尝试恢复。' : '默认关闭，不会自动暴露本机服务。'}>
        <Button type="submit" {...busyProps(action.busy === 'toggle')}>
          {active ? '停止临时链接' : '启动临时链接'}
        </Button>
      </Footer>
    </Section>
  );
}
