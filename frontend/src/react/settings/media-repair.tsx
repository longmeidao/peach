/* 媒体修复：选一个媒体库，把里面播不了或播不顺的 MP4 批量修好。
 *
 * 一轮要跑几十分钟到几小时，所以这里只负责起停和看进度；跑到哪一步由服务自己记，
 * 页面关掉再回来照样接得上。跑动时两秒问一次，空闲时不问。 */
import { useEffect, useState } from 'react';
import { confirmModal, MEDIA_SOURCE_ICONS } from '@peach/legacy/ui';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Select, SelectItem } from '@/components/base/select/select';

import { apiGet, apiSend } from '../../api';
import { Note } from '../components/note';
import { Progress } from '../components/progress';
import { ErrorText, Footer, Rows, Section, SourceMark, Stack } from './section';
import { busyProps, useAction } from './use-action';

export interface MediaRepairState {
  status: string;
  library: string;
  stage: string;
  checked: number;
  total: number;
  found: number;
  repaired: number;
  failed: number;
  missing_tool: number;
  skipped: number;
  message: string;
  error?: string;
}

export interface RepairLibrary {
  id: string;
  name: string;
  /** 媒体库图标：来源名（`115`、`pikpak`、`local`）或雪碧图字形名，与侧栏媒体库切换器同一份。 */
  icon: string;
  metered: boolean;
}

const libraryMark = (icon: string) => MEDIA_SOURCE_ICONS[icon] || icon;

const IDLE: MediaRepairState = {
  status: 'idle', library: '', stage: '', checked: 0, total: 0, found: 0,
  repaired: 0, failed: 0, missing_tool: 0, skipped: 0, message: '',
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

export function MediaRepair({ initial, initialLibraries }: {
  initial?: MediaRepairState; initialLibraries?: RepairLibrary[];
}) {
  const [state, setState] = useState<MediaRepairState>(initial || IDLE);
  const [libraries, setLibraries] = useState<RepairLibrary[]>(initialLibraries || []);
  const [chosen, setChosen] = useState('');
  const action = useAction();
  const running = state.status === 'running';

  useEffect(() => {
    if (initialLibraries) return undefined;
    const controller = new AbortController();
    apiGet<{ libraries: RepairLibrary[] }>('/api/libraries', controller.signal)
      .then((result) => { if (!controller.signal.aborted) setLibraries(result.libraries || []); })
      .catch(() => undefined);
    return () => controller.abort();
  }, [initialLibraries]);

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

  // 跑着的那一轮握着下拉框；空闲时是人选的那个，没选过就是上一轮修的库，再没有就是第一个。
  const selected = libraries.find((row) => row.id === (running ? state.library : chosen))
    ?? libraries.find((row) => row.id === state.library) ?? libraries[0];

  const start = () => {
    if (!selected) return;
    void confirmModal({
      title: `修复媒体库「${selected.name}」`,
      body: '缺时间戳表的片子另存一份修好的头，原文件不动；缺索引的片子重建后替换原文件，'
        + '坏原件改名成同目录的隐藏文件（.文件名.peach-original）留着。'
        + (selected.metered ? '这个库在计费来源上，每修一部都要把片子完整拉一遍。' : ''),
      confirmLabel: '修复媒体库',
      onConfirm: async () => setState(await apiSend<MediaRepairState>('/api/media-repair',
        { library: selected.id, restart: true })),
    });
  };
  const stop = () => void action.run('stop',
    (signal) => apiSend<MediaRepairState>('/api/media-repair', { stop: true }, 'POST', signal), setState);

  const progress = state.total ? Math.round((state.checked / state.total) * 100) : 0;
  const complete = state.status === 'complete';
  const notes = [
    running ? <Progress key="progress" label="修复进度" value={progress} /> : null,
    complete && !state.repaired && !state.failed
      ? <Note key="clean" tone="info" title="没有要修的">这个库里的片子都能直接播。</Note>
      : null,
    complete && state.missing_tool
      ? <Note key="tool" tone="warning" title="缺少 untrunc">
          {`${count(state.missing_tool)} 部缺索引的片子要装上 untrunc 才修得了，下载入口在「运行信息」里。`}
        </Note>
      : null,
    action.error || state.error ? <ErrorText key="error">{action.error || state.error}</ErrorText> : null,
  ].filter(Boolean);
  return (
    <Section title="媒体修复">
      <Rows>
        <SettingsRow label="媒体库"
          description="修缺时间戳表（播放卡顿）和缺索引（打不开）的 MP4。常看的片子先修。">
          <Select aria-label="媒体库" selectedKey={selected?.id ?? null} isDisabled={running || !libraries.length}
            onSelectionChange={(key) => { if (key !== null) setChosen(String(key)); }}>
            {libraries.map((row) => (
              <SelectItem key={row.id} id={row.id} textValue={row.name}>
                <SourceMark mark={libraryMark(row.icon)} />{row.name}
              </SelectItem>
            ))}
          </Select>
        </SettingsRow>
      </Rows>
      {notes.length ? <Stack divided>{notes}</Stack> : null}
      <Footer status={statusLine(state) ? <p role="status">{statusLine(state)}</p> : null}>
        {running
          ? <Button onClick={stop} {...busyProps(action.busy === 'stop')}>停止</Button>
          : <Button onClick={start} disabled={!selected}>开始修复</Button>}
      </Footer>
    </Section>
  );
}
