/* 活动页：任务中心那张表的唯一界面。
 *
 * 这一屏要回答三个问题，顺序就是它们的紧迫程度：现在有什么在跑、有哪一轮被挡下了、
 * 刚跑完的那些怎么样。三段共用 `/api/tasks` 一次请求的结果。
 *
 * 轮询交给 Query 的 `refetchInterval`：间隔按上一次拿到的内容算，有东西在跑两秒一次，
 * 全是终态十秒一次。它是后台刷新，不写 `aria-busy`——页面上的内容一直是完整的，写了
 * 等于告诉辅助技术和冒烟用例「这一屏还没好」。取数失败只在页内报一条，上一份数据留着：
 * 服务重启的那几秒里，把整页换成一句错误比留着十秒前的进度更难用。 */
import { useId } from 'react';
import type { ReactNode } from 'react';
import { RiHistoryLine } from '@remixicon/react';
import { useQuery } from '@tanstack/react-query';

import { Chip } from '@/components/base/badges/chip';

import { errorMessage } from '../../api';
import type { ActivityProps } from '../bundle';
import { EmptyState } from '../components/empty-state';
import { LoadingDots } from '../components/loading-dots';
import { Note } from '../components/note';
import { Progress } from '../components/progress';
import {
  elapsedText, fetchTasks, momentText, pollInterval, statusLabel, summaryText,
  TASKS_KEY, TRIGGER_LABELS, type TaskRunPayload,
} from './tasks';

/* 状态徽章只有三档颜色：成功是绿、失败是红、被叫停与被打断是黄，其余留中性底。
   BoardUI 的 Chip 把这三档写成 lime／rose／yellow，第四种颜色不存在。 */
const BADGE_COLORS: Record<string, 'lime' | 'rose' | 'yellow'> = {
  succeeded: 'lime', failed: 'rose', cancelled: 'yellow', interrupted: 'yellow',
};

function StatusBadge({ status }: { status: string }) {
  return <Chip color={BADGE_COLORS[status] ?? 'neutral'}>{statusLabel(status)}</Chip>;
}

/** 一轮任务一张卡。失败时整张卡的框线换成 danger 色，不给结束原因那行字上色——
 *  一屏十几行里逐行读红字，比看一眼哪张卡的框是红的慢得多。 */
function RunCard(
  { run, meta, children, footer }:
  { run: TaskRunPayload; meta: string; children?: ReactNode; footer?: string },
) {
  return (
    <li data-status={run.status} data-task-key={run.task_key}
      className={run.status === 'failed'
        ? 'flex flex-col rounded-2xl border border-border-error-default'
        : 'flex flex-col rounded-2xl border border-separator-border'}>
      <div className="flex flex-col gap-1.5 px-5 pt-5 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <strong className="min-w-0 break-words text-title-1-medium text-text-primary">{run.task_label}</strong>
          <StatusBadge status={run.status} />
        </div>
        <p className="text-caption-1-regular text-text-secondary">{meta}</p>
        {children}
      </div>
      {footer
        ? <div className="border-t border-separator-border px-5 py-3">
            <p className="text-caption-1-regular text-text-secondary">{footer}</p>
          </div>
        : null}
    </li>
  );
}

function RunningRun({ run }: { run: TaskRunPayload }) {
  const total = run.progress_total || 0;
  const current = run.progress_current || 0;
  const label = run.progress_label || '正在进行';
  const elapsed = elapsedText(run.elapsed_seconds);
  const meta = [TRIGGER_LABELS[run.trigger] || run.trigger, elapsed && `已跑 ${elapsed}`]
    .filter(Boolean).join(' · ');
  return (
    <RunCard run={run} meta={meta}>
      {total > 0
        ? <div className="flex flex-col gap-1.5">
            <Progress label={label} value={current} max={total} />
            <p className="text-caption-1-regular text-text-secondary">{label} · {current} / {total} 项</p>
          </div>
        : <LoadingDots label={label} />}
    </RunCard>
  );
}

function SettledRun({ run }: { run: TaskRunPayload }) {
  const summary = summaryText(run.result_summary);
  const elapsed = elapsedText(run.elapsed_seconds);
  const meta = [TRIGGER_LABELS[run.trigger] || run.trigger, momentText(run.finished_at),
                elapsed && `用时 ${elapsed}`].filter(Boolean).join(' · ');
  return (
    <RunCard run={run} meta={meta} footer={run.error}>
      {summary ? <p className="text-caption-1-regular text-text-secondary">{summary}</p> : null}
    </RunCard>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  const id = useId();
  return (
    <section aria-labelledby={id} className="flex min-w-0 flex-col gap-3">
      <h3 id={id} className="text-title-2-semibold text-text-primary">{title}</h3>
      {children}
    </section>
  );
}

function RunList({ live = false, children }: { live?: boolean; children: ReactNode }) {
  return (
    <ul aria-live={live ? 'polite' : undefined} className="flex min-w-0 flex-col gap-3">{children}</ul>
  );
}

/** 页面正文的一条窄列，与管理区标题同一条中线（`--board-content`）。 */
function Page({ children }: { children: ReactNode }) {
  return <div className="mx-auto flex w-full max-w-board flex-col gap-8">{children}</div>;
}

export function ActivityPage(_props: ActivityProps) {
  const tasks = useQuery({
    queryKey: TASKS_KEY,
    queryFn: ({ signal }) => fetchTasks(signal),
    refetchInterval: (query) => pollInterval(query.state.data),
  });
  const data = tasks.data;
  const problem = tasks.error ? errorMessage(tasks.error) : '';
  // 首屏就没拿到数据：只剩这一条，不画空的三段。
  if (!data) return <Page><Note tone="error">{problem || '读取任务中心失败'}</Note></Page>;

  const running = data.running || [];
  const skipped = data.skipped || [];
  // 同一轮不在「最近完成」里再出现一次：一屏两行说的是同一件事，读起来像跑了两轮。
  const finished = (data.finished || []).filter((run) => !skipped.some((row) => row.id === run.id));
  const quiet = !running.length && !skipped.length && !finished.length;
  return (
    <Page>
      {problem ? <Note tone="error">{problem}</Note> : null}
      {data.available === false
        ? <Note tone="warning">{data.message || '账本上还没有任务中心的表'}</Note>
        : null}
      {quiet
        ? <EmptyState icon={RiHistoryLine} title="还没有任务记录">
            扫描、追更检查、批量操作和命令行批处理跑起来之后，这里会显示它们的进度与结果。
          </EmptyState>
        : <>
            <Section title="正在进行">
              {running.length
                ? <RunList live>{running.map((run) => <RunningRun key={run.id} run={run} />)}</RunList>
                : <p className="text-body-2-regular text-text-secondary">没有任务在跑。</p>}
            </Section>
            {/* 「刚才那一轮为什么没跑」只有这一段答得出：定时触发撞上在跑的那一轮会
                安静跳过，不留记录的话它在界面上和从没触发过一模一样。 */}
            {skipped.length
              ? <Section title="被挡下的">
                  <RunList>{skipped.map((run) => <SettledRun key={run.id} run={run} />)}</RunList>
                </Section>
              : null}
            {finished.length
              ? <Section title="最近完成">
                  <RunList>{finished.map((run) => <SettledRun key={run.id} run={run} />)}</RunList>
                </Section>
              : null}
          </>}
    </Page>
  );
}
