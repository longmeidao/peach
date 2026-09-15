/* 目录页顶上那条处理横幅。
 *
 * 它和数据管理页那张卡片读同一个 `queryKey`（同一趟任务、同一份快照），只是说得更短：
 * 一圈进度或一枚图标、一句话、一个去处。任务不在跑也没出事时整条不画——容器靠
 * `web/board.css` 的 `:has(>.peach-react:empty)` 把高度收回 0，出现与消失都是走的。
 *
 * 注册表里没有行内横幅（`notification` 条目是带关闭键和计时的浮动通知），按语气取
 * `status-*` 与 `separator-border` 组合，登记在 `../boardui/ORIGIN.md`。 */
import { RiArrowRightLine, RiErrorWarningLine, RiInformationLine } from '@remixicon/react';

import { LinkButton } from '@/components/base/buttons/link-button';

import { errorMessage } from '../../api';
import type { LibraryProcessingProps } from '../bundle';
import { currentLine, DISCONNECTED_TEXT } from './library-processing';
import { useLibraryProcessingJob } from './use-library-processing';

type Tone = 'gray' | 'warning' | 'error';

const SURFACE: Record<Tone, string> = {
  gray: 'flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-separator-border px-4 py-3 text-text-secondary',
  warning: 'flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-separator-border bg-status-yellow-background px-4 py-3 text-status-yellow-text',
  error: 'flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-separator-border bg-background-tertiary-error px-4 py-3 text-text-error-primary',
};

/** 进度环。几何走 SVG 属性：一圈长度钉成 100，画出来的那一段就是百分比本身。 */
function Gauge({ value, max }: { value: number; max: number }) {
  const percent = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <svg role="progressbar" aria-label="任务完成率" aria-valuemin={0} aria-valuemax={100}
      aria-valuenow={percent} viewBox="0 0 32 32" fill="none"
      className="size-6 shrink-0 -rotate-90 stroke-current">
      <circle cx="16" cy="16" r="13" strokeWidth="4" className="opacity-25" />
      <circle cx="16" cy="16" r="13" strokeWidth="4" pathLength={100}
        strokeDasharray={`${percent} 100`} strokeLinecap="round" />
    </svg>
  );
}

export function LibraryProcessingNotice(props: LibraryProcessingProps) {
  const { job } = useLibraryProcessingJob(props);
  const state = job.data;
  const problem = job.isError ? (state ? DISCONNECTED_TEXT : errorMessage(job.error)) : '';
  const status = state?.status ?? 'idle';
  const failed = status === 'failed';
  const running = status === 'running';
  /* 任务不在跑、也没出事时这条不该占地方：目录页顶上常年挂一句「没有任务」比没有还吵。 */
  if (!problem && !running && !failed) return null;

  const tone: Tone = failed ? 'error' : problem || state?.stalled ? 'warning' : 'gray';
  const checked = state?.checked || 0;
  const total = state?.total || 0;
  const message = problem
    || (failed ? '扫描与资料采集未完成'
      : currentLine(state!) + (total ? ` · ${checked} / ${total}` : ''));
  const Glyph = tone === 'gray' ? RiInformationLine : RiErrorWarningLine;
  return (
    <aside role={failed ? 'alert' : 'status'} className={SURFACE[tone]}>
      <div className="flex min-w-0 items-center gap-3">
        {running && total
          ? <Gauge value={checked} max={total} />
          : <Glyph aria-hidden className="size-5 shrink-0" />}
        <p className="min-w-0 text-body-2-regular">{message}</p>
      </div>
      <LinkButton href="/data-cleanup#libraryProcessing" size="small" trailingIcon={RiArrowRightLine}>
        {problem || failed ? '查看并处理' : '查看进度'}
      </LinkButton>
    </aside>
  );
}
