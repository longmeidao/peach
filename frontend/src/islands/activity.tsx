/* 活动页：任务中心那张表的唯一界面。
 *
 * 这一屏要回答三个问题，顺序就是它们的紧迫程度：现在有什么在跑、有哪一轮被挡下了、
 * 刚跑完的那些怎么样。三段共用 `/api/tasks` 一次请求的结果——分三次取会出现
 * 「在跑那段是新的、完成那段是旧的」这种自相矛盾的一屏。
 *
 * 轮询间隔跟着内容走：有东西在跑就两秒一次（和进度写库的节流同一个数），
 * 全是终态时十秒一次。页面停在后台时不该每两秒敲一次库。 */
import { useEffect, useRef, useState } from 'preact/hooks';
import { apiGet, errorMessage } from '../api';
import { badgeHtml, emptyStateHtml, fieldsetTitle, loadingDotsHtml, noteHtml, progressHtml }
  from '@peach/legacy/ui';
import type { IslandState } from '../islands';

export interface TaskRunPayload {
  id: number;
  task_key: string;
  task_label: string;
  trigger: string;
  status: string;
  host: string;
  started_at: string | null;
  finished_at: string | null;
  elapsed_seconds: number | null;
  progress_current: number | null;
  progress_total: number | null;
  progress_label: string;
  result_summary: Record<string, unknown>;
  error: string;
}

export interface ActivityData {
  available: boolean;
  message?: string;
  running: TaskRunPayload[];
  skipped: TaskRunPayload[];
  finished: TaskRunPayload[];
}

export interface ActivityProps {
  /** 测试与骨架预览用：不轮询，只画给到的这一份。 */
  preview?: boolean;
}

export const loadActivity = (_props: ActivityProps, signal: AbortSignal) =>
  apiGet<ActivityData>('/api/tasks', signal);

const TRIGGER_LABELS: Record<string, string> = {
  manual: '手动', scheduled: '定时', startup: '启动', cli: '命令行',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '排队中', running: '进行中', succeeded: '已完成',
  failed: '失败', cancelled: '已取消', interrupted: '被打断',
};

/** 状态的中文名。表里的状态集是封闭的，认不出来只可能是表先改了，那就原样显示。 */
const statusLabel = (status: string): string => STATUS_LABELS[status] || status;

/* 摘要里的键来自各域自己的状态字典，是英文标识；能认出来的翻成中文，认不出的原样
   显示——瞎猜一个中文名比留着英文键更难查。 */
const SUMMARY_LABELS: Record<string, string> = {
  checked: '已检查', total: '总数', scanned: '已扫描', identified: '已识别',
  candidates: '资料候选', covers: '封面', changed: '已改动', operation: '操作',
  ok: '取得', miss: '未取得', kept: '保留', planned: '计划', done: '已处理', added: '新增',
  written: '已写入', removed: '已移除', exit_code: '退出码', issue_count: '问题',
};

/** 秒数说成「几分几秒」。跑了几小时的批处理也要一眼读得出量级。 */
export function elapsedText(seconds: number | null | undefined): string {
  if (typeof seconds !== 'number' || !Number.isFinite(seconds) || seconds < 0) return '';
  const whole = Math.floor(seconds);
  if (whole < 60) return `${whole} 秒`;
  const minutes = Math.floor(whole / 60);
  if (minutes < 60) return `${minutes} 分 ${whole % 60} 秒`;
  return `${Math.floor(minutes / 60)} 小时 ${minutes % 60} 分`;
}

/** 时间戳说成本地的「月-日 时:分」。账本里存的是 UTC，界面上一律按本机时区读。 */
export function momentText(stamp: string | null | undefined): string {
  if (!stamp) return '';
  const moment = new Date(stamp);
  if (Number.isNaN(moment.getTime())) return '';
  return moment.toLocaleString(undefined,
    { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

/** 摘要压成一行。只取标量：明细留在各域自己的页面和日志里。 */
export function summaryText(summary: Record<string, unknown>): string {
  return Object.entries(summary || {})
    .filter(([key, value]) => key !== 'blocked_by'
      && (typeof value === 'number' || typeof value === 'string')
      && String(value) !== '')
    .map(([key, value]) => `${SUMMARY_LABELS[key] || key} ${value}`)
    .join(' · ');
}

function RunMeta({ run, when }: { run: TaskRunPayload; when: string }) {
  const parts = [TRIGGER_LABELS[run.trigger] || run.trigger, when].filter(Boolean);
  return <p class="activity-meta">{parts.join(' · ')}</p>;
}

function RunningRun({ run }: { run: TaskRunPayload }) {
  const total = run.progress_total || 0;
  const current = run.progress_current || 0;
  const label = run.progress_label || '正在进行';
  const elapsed = elapsedText(run.elapsed_seconds);
  return <li class="activity-run" data-task-key={run.task_key}>
    <div class="activity-run-head">
      <h3>{run.task_label}</h3>
      <span dangerouslySetInnerHTML={{ __html: badgeHtml(statusLabel(run.status)) }} />
    </div>
    <RunMeta run={run} when={elapsed ? `已跑 ${elapsed}` : ''} />
    {total > 0
      ? <div class="activity-progress">
          <div dangerouslySetInnerHTML={{ __html: progressHtml(label, current, total) }} />
          <p class="activity-progress-readout">{label} · {current} / {total} 项</p>
        </div>
      : <div dangerouslySetInnerHTML={{ __html: loadingDotsHtml(label) }} />}
  </li>;
}

function SettledRun({ run }: { run: TaskRunPayload }) {
  const summary = summaryText(run.result_summary);
  const elapsed = elapsedText(run.elapsed_seconds);
  const when = [momentText(run.finished_at), elapsed && `用时 ${elapsed}`]
    .filter(Boolean).join(' · ');
  return <li class="activity-run" data-status={run.status} data-task-key={run.task_key}>
    <div class="activity-run-head">
      <h3>{run.task_label}</h3>
      <span dangerouslySetInnerHTML={{ __html: badgeHtml(statusLabel(run.status)) }} />
    </div>
    <RunMeta run={run} when={when} />
    {summary && <p class="activity-summary">{summary}</p>}
    {run.error && <p class="activity-error">{run.error}</p>}
  </li>;
}

export function Activity({ data, error, preview }: ActivityProps & IslandState<ActivityData>) {
  const [state, setState] = useState<ActivityData | null>(data);
  const [problem, setProblem] = useState(error);
  const lifetime = useRef(new AbortController());
  const running = state?.running || [];
  useEffect(() => {
    if (preview) return;
    const signal = lifetime.current.signal;
    let timer = 0;
    const poll = async () => {
      try {
        const next = await apiGet<ActivityData>('/api/tasks', signal);
        if (signal.aborted) return;
        setState(next);
        setProblem('');
        timer = setTimeout(poll, next.running.length ? 2000 : 10000) as unknown as number;
      } catch (cause) {
        if (signal.aborted) return;
        setProblem(errorMessage(cause));
        timer = setTimeout(poll, 10000) as unknown as number;
      }
    };
    timer = setTimeout(poll, running.length ? 2000 : 10000) as unknown as number;
    return () => { lifetime.current.abort(); clearTimeout(timer) };
  }, []);
  if (!state) {
    return <div class="activitypage" role="alert" dangerouslySetInnerHTML={{ __html:
      noteHtml(problem || '读取任务中心失败', { variant: 'error', filled: true }) }} />;
  }
  const skipped = state.skipped || [];
  const finished = (state.finished || []).filter(run => !skipped.some(row => row.id === run.id));
  const quiet = !running.length && !skipped.length && !finished.length;
  return <div class="activitypage">
    {problem && <div role="alert" dangerouslySetInnerHTML={{ __html:
      noteHtml(problem, { variant: 'error', filled: true }) }} />}
    {state.available === false && <div dangerouslySetInnerHTML={{ __html:
      noteHtml(state.message || '账本上还没有任务中心的表', { variant: 'warning' }) }} />}
    {quiet
      ? <div dangerouslySetInnerHTML={{ __html: emptyStateHtml('history', '还没有任务记录',
          '扫描、追更检查、批量操作和命令行批处理跑起来之后，这里会显示它们的进度与结果。') }} />
      : <>
        <section class="activitysection" aria-labelledby="activityRunning">
          <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('activityRunning', '正在进行') }} />
          {running.length
            ? <ul class="activity-runs" aria-live="polite">
                {running.map(run => <RunningRun key={run.id} run={run} />)}
              </ul>
            : <p class="activity-quiet">没有任务在跑。</p>}
        </section>
        {!!skipped.length && <section class="activitysection" aria-labelledby="activitySkipped">
          <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('activitySkipped', '被挡下的') }} />
          {/* 「刚才那一轮为什么没跑」只有这一段答得出：定时触发撞上在跑的那一轮会
              安静跳过，不留记录的话它在界面上和从没触发过一模一样。 */}
          <ul class="activity-runs">
            {skipped.map(run => <SettledRun key={run.id} run={run} />)}
          </ul>
        </section>}
        {!!finished.length && <section class="activitysection" aria-labelledby="activityFinished">
          <div dangerouslySetInnerHTML={{ __html: fieldsetTitle('activityFinished', '最近完成') }} />
          <ul class="activity-runs">
            {finished.map(run => <SettledRun key={run.id} run={run} />)}
          </ul>
        </section>}
      </>}
  </div>;
}
