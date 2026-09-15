/* 播放兼容修复：把缺时间戳表的 MP4 批量修好，修完这类片子起播就走原片。
 *
 * 一轮要跑几十分钟到几小时，所以这里只负责起停和看进度；跑到哪一步由服务自己记，
 * 页面关掉再回来照样接得上。跑动时两秒问一次，空闲时不问。 */
import { useEffect, useState } from 'react';

import { Button } from '@/components/base/buttons/button';
import { Checkbox } from '@/components/base/checkbox/checkbox';

import { apiGet, apiSend } from '../../api';
import { Note } from '../components/note';
import { Progress } from '../components/progress';
import { ErrorText, Footer, Help, Section, Stack } from './section';
import { busyProps, useAction } from './use-action';

export interface MediaRepairState {
  status: string;
  stage: string;
  checked: number;
  total: number;
  found: number;
  repaired: number;
  failed: number;
  skipped: number;
  message: string;
  error?: string;
}

const IDLE: MediaRepairState = {
  status: 'idle', stage: '', checked: 0, total: 0, found: 0,
  repaired: 0, failed: 0, skipped: 0, message: '',
};

const count = (value: number) => Number(value).toLocaleString();

/** 一句话说清此刻在干什么：扫描报进度，修复报进度加当前这部片。 */
function statusLine(state: MediaRepairState): string {
  if (state.status === 'running') {
    const where = state.total ? `${count(state.checked)} / ${count(state.total)}` : '准备中';
    return state.stage === '修复' && state.message
      ? `修复 ${where} · ${state.message}`
      : `${state.stage || '扫描'} ${where}`;
  }
  if (state.status === 'complete' && (state.repaired || state.failed)) {
    return state.failed
      ? `修好 ${count(state.repaired)} 部，${count(state.failed)} 部修不了`
      : `修好 ${count(state.repaired)} 部`;
  }
  return '';
}

export function MediaRepair({ initial }: { initial?: MediaRepairState }) {
  const [state, setState] = useState<MediaRepairState>(initial || IDLE);
  const [metered, setMetered] = useState(false);
  const action = useAction();
  const running = state.status === 'running';

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const result = await apiGet<MediaRepairState>('/api/media-repair', controller.signal);
        if (controller.signal.aborted) return;
        setState(result);
        if (result.status === 'running') timer = setTimeout(poll, 2000);
      } catch {
        // 问不到就停下：服务没起来时页面本来也做不了别的。
      }
    };
    timer = setTimeout(poll, running ? 2000 : 0);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [running]);

  const start = () => void action.run('start',
    (signal) => apiSend<MediaRepairState>('/api/media-repair',
      { allow_metered: metered, restart: true }, 'POST', signal), setState);
  const stop = () => void action.run('stop',
    (signal) => apiSend<MediaRepairState>('/api/media-repair', { stop: true }, 'POST', signal), setState);

  const progress = state.total ? Math.round((state.checked / state.total) * 100) : 0;
  return (
    <Section title="播放兼容修复">
      <Stack>
        <Help>
          有些 MP4 少了一张时间戳表，浏览器按容器给的时刻排帧，会把其中一部分丢掉，看着就是卡顿。
          修好之后这类片子起播直接用原片，不再实时转码。原始文件不改动，修好的头另存在缓存里。
        </Help>
        <Checkbox isSelected={metered} isDisabled={running} onChange={setMetered}>
          连 PikPak 上的一起修（要把片子完整拉一遍，走流量）
        </Checkbox>
        {running ? <Progress label="修复进度" value={progress} /> : null}
        {state.status === 'complete' && !state.repaired && !state.failed
          ? <Note tone="info" title="没有要修的">库里的片子都能直接播，没找到缺时间戳表的。</Note>
          : null}
        {action.error || state.error ? <ErrorText>{action.error || state.error}</ErrorText> : null}
      </Stack>
      <Footer status={statusLine(state) ? <p role="status">{statusLine(state)}</p> : null}>
        {running
          ? <Button onClick={stop} {...busyProps(action.busy === 'stop')}>停止</Button>
          : <Button onClick={start} {...busyProps(action.busy === 'start')}>开始修复</Button>}
      </Footer>
    </Section>
  );
}
