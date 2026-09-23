/* 任务中心的数据契约与折算：`/api/tasks` 一次请求供整页三段使用。
 *
 * 分三次取会出现「在跑那段是新的、完成那段是旧的」这种自相矛盾的一屏，所以只有一个
 * queryKey。首屏由 `prefetchTasks` 写进 Query 缓存，组件挂上去读的就是它。 */
import { apiGet } from '../../api';
import { queryClient } from '../query';

export const TASKS_URL = '/api/tasks';
/** 整页共用这一个键：三段是同一次响应的三个字段。 */
export const TASKS_KEY = ['tasks'] as const;

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
  /** 派出这一轮的父任务；不是后继时为 null（ADR-0040）。 */
  parent_run_id: number | null;
  root_run_id: number | null;
  /** 这条后继要做的那件事的全名。不是后继时是空串，界面据此判断它挂不挂到父卡片下。 */
  followup_key: string;
  followup_depth: number;
}

export interface ActivityData {
  available: boolean;
  message?: string;
  running: TaskRunPayload[];
  skipped: TaskRunPayload[];
  finished: TaskRunPayload[];
  /** 「最近完成」这一页后面还有更早的。 */
  finished_has_more?: boolean;
}

/** 往前翻的一页：只有「最近完成」，在跑与被挡下的由轮询那一份负责。 */
export interface FinishedPage {
  finished: TaskRunPayload[];
  finished_has_more: boolean;
}

/** 以 `oldest` 为游标取它之前的一页。游标是它的结束时刻加 id，与服务端的排序键一致。 */
export const fetchEarlier = (oldest: TaskRunPayload, signal?: AbortSignal) => {
  const query = new URLSearchParams({
    before_finished_at: oldest.finished_at || '', before_id: String(oldest.id) });
  return apiGet<FinishedPage>(`${TASKS_URL}?${query}`, signal);
};

/** 几批终态行并成一列：同一轮只留一条，按结束时刻从新到旧、同一时刻按 id 从大到小，
 *  和服务端翻页的排序键同一个，拼接处才不会乱序。终态落地后不再变，重复的哪一份都一样。 */
export function mergeFinished(...batches: TaskRunPayload[][]): TaskRunPayload[] {
  const byId = new Map<number, TaskRunPayload>();
  for (const batch of batches) for (const row of batch) if (!byId.has(row.id)) byId.set(row.id, row);
  return [...byId.values()].sort((a, b) => {
    const left = a.finished_at || '', right = b.finished_at || '';
    if (left !== right) return left < right ? 1 : -1;
    return b.id - a.id;
  });
}

/** 有东西在跑就两秒一次（和进度写库的节流同一个数），全是终态时十秒一次。 */
export const RUNNING_POLL_MS = 2000;
export const SETTLED_POLL_MS = 10000;
export const pollInterval = (data: ActivityData | undefined): number =>
  data?.running.length ? RUNNING_POLL_MS : SETTLED_POLL_MS;

export const fetchTasks = (signal?: AbortSignal) => apiGet<ActivityData>(TASKS_URL, signal);

/** 首屏：取完数才画。中止时 `fetchQuery` 把 `AbortError` 抛回给挂载方，它据此放弃这一次。 */
export async function prefetchTasks(signal: AbortSignal): Promise<void> {
  await queryClient.fetchQuery({ queryKey: TASKS_KEY, queryFn: () => fetchTasks(signal) });
}

export const TRIGGER_LABELS: Record<string, string> = {
  manual: '手动', scheduled: '定时', startup: '启动', cli: '命令行',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '排队中', running: '进行中', succeeded: '已完成',
  failed: '失败', cancelled: '已取消', interrupted: '被打断',
};

/** 状态的中文名。表里的状态集是封闭的，认不出来只可能是表先改了，那就原样显示。 */
export const statusLabel = (status: string): string => STATUS_LABELS[status] || status;

/* 摘要里的键来自各域自己的状态字典，是英文标识；能认出来的翻成中文，认不出的原样
   显示——瞎猜一个中文名比留着英文键更难查。 */
const SUMMARY_LABELS: Record<string, string> = {
  checked: '已检查', total: '总数', scanned: '已扫描', identified: '已识别',
  candidates: '资料候选', covers: '封面', changed: '已改动', operation: '操作',
  ok: '取得', miss: '未取得', kept: '保留', planned: '计划', done: '已处理', added: '新增',
  written: '已写入', removed: '已移除', exit_code: '退出码', issue_count: '问题',
  followups: '派出后继', followups_duplicate: '已在排队', followups_truncated: '超上限未派',
  followups_depth_exceeded: '超深度未派', outcome: '结果', name: '实体',
  matched: '图库命中', size: '尺寸', source: '来源',
};

/** 把一批任务按 `parent_run_id` 归到各自的父任务下。没有父的那些留在外面。 */
export function groupFollowups(rows: TaskRunPayload[]): Map<number, TaskRunPayload[]> {
  const grouped = new Map<number, TaskRunPayload[]>();
  for (const row of rows) {
    if (!row.followup_key || row.parent_run_id == null) continue;
    const siblings = grouped.get(row.parent_run_id);
    if (siblings) siblings.push(row);
    else grouped.set(row.parent_run_id, [row]);
  }
  return grouped;
}

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

/* 不进摘要的键：「谁挡的」已经写在错误那一句里；其余是域状态字典里的簿记——状态、
   起止时间戳、请求号和任务号，卡片标题、徽章和时间那一行已经说过，原样摆出来只是一串
   英文键和纪元秒。 */
const SUMMARY_HIDDEN = new Set([
  'blocked_by', 'status', 'run_id', 'request_id', 'started_at', 'completed_at', 'finished_at',
]);

/** 摘要压成一行。只取标量：明细留在各域自己的页面和日志里。 */
export function summaryText(summary: Record<string, unknown>): string {
  return Object.entries(summary || {})
    .filter(([key, value]) => !SUMMARY_HIDDEN.has(key)
      && (typeof value === 'number' || typeof value === 'string')
      && String(value) !== '')
    .map(([key, value]) => `${SUMMARY_LABELS[key] || key} ${value}`)
    .join(' · ');
}
