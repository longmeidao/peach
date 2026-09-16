/* 口味页的数据契约、轮询节律与纯折算。
 *
 * 四个端点在 `frontend/src` 里都只在这里声明一次（`tests/test_frontend_build.py` 盯着）。
 *
 * 键带着分析范围：`['taste', window]`。同一台机器的七天和全部时间是两份真相，合成一个键
 * 的话切范围就是把上一份直接覆盖掉，切回来还得再问一遍。范围切换时用
 * `keepPreviousData` 留住上一份，不退回骨架——这一屏的结构不变，只有数在变。
 * 不给 `staleTime`：服务端已经按 `taste:{window}` 缓存过一层，前端再压一层就会出现
 * 「刚导入完，页面还是导入前那一份」。
 *
 * 刷新任务是另一份真相，节律由后台推进，所以单独一个键（`['taste','refresh']`）。 */
import { sankey, sankeyLinkHorizontal } from 'd3-sankey';

import { apiGet, apiSend, ApiError } from '../../api';
import { queryClient } from '../query';

export const TASTE_URL = '/api/taste';
export const TASTE_REFRESH_URL = '/api/taste/refresh';
export const TASTE_IMPORT_URL = '/api/taste/import';
export const TASTE_SOURCE_URL = '/api/taste/source';

/** 一份 dashboard 的键，带分析范围。 */
export const tasteKey = (window: string) => ['taste', window] as const;
/** 读取浏览记录那一趟后台任务。 */
export const TASTE_REFRESH_KEY = ['taste', 'refresh'] as const;

/** 分析范围。值就是 `/api/taste?window=` 收的那几个。 */
export const TASTE_WINDOWS = [
  ['7d', '最近 7 天'], ['30d', '最近 30 天'], ['90d', '最近 90 天'],
  ['365d', '最近一年'], ['all', '全部时间'],
] as const;

export const DEFAULT_WINDOW = 'all';

/** 排行里的一行。`entity_id` 与 `has_avatar` 决定画哪一级图，`peach_items` 决定点不点得动。 */
export interface RankRow {
  name: string;
  score?: number;
  visits?: number;
  web_visits?: number;
  peach_score?: number;
  peach_items?: number;
  entity_id?: number | null;
  has_image?: boolean;
  avatar_focus?: unknown;
  has_avatar?: boolean;
  representative_asset_id?: number | null;
  source_domain?: string | null;
}

/** 按维度聚合的名次。名字与 `taste_history.build_taste_dashboard` 对齐。 */
export interface TasteRankings {
  browser_tags?: RankRow[];
  browser_creators?: RankRow[];
  browser_categories?: RankRow[];
  domains?: RankRow[];
  peach_tags?: RankRow[];
  peach_creators?: RankRow[];
  peach_performers?: RankRow[];
}

export interface TasteSummary {
  history_visits?: number;
  history_sources?: number;
  peach_items?: number;
  peach_seconds?: number;
  liked?: number;
  disliked?: number;
  range_start?: string | null;
  range_end?: string | null;
}

export interface TasteCoverage {
  tagged?: number; identified?: number; untagged?: number; unidentified?: number;
}

/** 一台设备的一份浏览记录。`source_key` 是 64 位十六进制，移除时交回去的就是它。 */
export interface TasteSource {
  source_key: string; browser: string; profile: string; host: string; visits?: number;
}

export interface TasteAnalysis {
  headline?: string;
  confidence?: { level?: string; label?: string };
  points?: { label: string; text: string }[];
  explore?: { tag: string; title: string; detail: string }[];
  next_steps?: { route: string; title: string; detail: string }[];
}

export interface TasteActivity {
  timezone?: string;
  days?: { date: string; count: number }[];
  hours?: { weekday: number; hour: number; count: number }[];
}

export interface CreatorFlow { source: string; target: string; value: number }

/** `/api/taste` 的响应。字段与 `web_stats.q_taste` 对齐。 */
export interface TasteData {
  summary?: TasteSummary;
  coverage?: TasteCoverage;
  rankings?: TasteRankings;
  gaps?: RankRow[];
  sources?: TasteSource[];
  analysis?: TasteAnalysis;
  activity?: TasteActivity;
  creator_flows?: CreatorFlow[];
  storage?: { exports?: number; bytes?: number };
  window?: string;
  updated_at?: string | null;
}

/** 读取浏览记录那一趟的快照。`status` 一次都没跑过是 `idle`。 */
export interface TasteJob {
  status: string;
  job_id?: string;
  stage?: string;
  message?: string;
  checked?: number;
  total?: number | null;
  error?: string;
}

export const fetchTaste = (window: string, signal?: AbortSignal) =>
  apiGet<TasteData>(`${TASTE_URL}?window=${window}`, signal);

export const fetchTasteJob = (signal?: AbortSignal) =>
  apiGet<TasteJob>(TASTE_REFRESH_URL, signal);

/** 首屏：取完数才画。中止时把 `AbortError` 抛回挂载方，它据此放弃这一次。 */
export async function prefetchTaste(window: string, signal: AbortSignal): Promise<void> {
  await queryClient.fetchQuery({
    queryKey: tasteKey(window), queryFn: () => fetchTaste(window, signal),
  });
}

/** 起一趟读取浏览记录。回的是任务快照，节律仍由 `TASTE_REFRESH_KEY` 说了算。 */
export const startTasteRefresh = (window: string) =>
  apiSend<TasteJob>(TASTE_REFRESH_URL, { window, background: true });

/** 移除一台设备的浏览记录。服务端连这一范围的新 dashboard 一起回，换进缓存即可。 */
export const removeTasteSource = (sourceKey: string, window: string) =>
  apiSend<{ removed: number; dashboard: TasteData }>(
    TASTE_SOURCE_URL, { operation: 'remove', source_key: sourceKey, window });

/** 导入一份私有导出。
 *
 * 文件原样当请求体发，文件名走 `X-Peach-Filename`：走 multipart 就要在服务端多接一个
 * 解析器，而这里只有一个文件、一个名字。服务端回的是「全部时间」那一份 dashboard。 */
export async function importTasteExport(file: File): Promise<{ dashboard: TasteData }> {
  const response = await fetch(TASTE_IMPORT_URL, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/octet-stream',
      'X-Peach-Filename': encodeURIComponent(file.name),
    },
    body: file,
  });
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch { /* 失败响应不一定是 JSON，下面按状态码兜底 */ }
  if (!response.ok) {
    const reason = (payload as { error?: string } | null)?.error;
    throw new ApiError(reason || `导入失败（${response.status}）`, response.status, payload);
  }
  return payload as { dashboard: TasteData };
}

/** 任务在跑时两秒一次，闲着十秒一次——这一趟可以从别的页面或上一次会话里起来。 */
export const RUNNING_POLL_MS = 2000;
export const IDLE_POLL_MS = 10_000;
export const jobPollInterval = (job: TasteJob | undefined): number =>
  (job?.status === 'running' ? RUNNING_POLL_MS : IDLE_POLL_MS);

export const tasteDate = (value: string | null | undefined): string =>
  (value ? new Date(value).toLocaleDateString('zh-CN') : '—');

/** 累计时长：够一小时读小时，不够读分钟。与统计页同一套口径。 */
export const tasteHours = (seconds: number): string =>
  (seconds >= 3600 ? `${(seconds / 3600).toFixed(1)} 小时` : `${Math.round(seconds / 60)} 分钟`);

/** 一行在这一榜里的强度。浏览侧按访问次数，Peach 侧按分数，都退化到条目数。 */
export const rankStrength = (row: RankRow): number =>
  Number(row.web_visits ?? row.score ?? row.visits ?? row.peach_items ?? 0);

/** 一行名次底下那句补充。两侧都有证据时并排显示，只有一侧就读那一侧的数。 */
export function rankDetail(row: RankRow): string {
  if (row.web_visits == null) return Number(row.score || row.visits || 0).toLocaleString();
  const parts: string[] = [];
  if (row.web_visits) parts.push(`浏览 ${row.web_visits}`);
  if (row.peach_items) parts.push(`Peach ${row.peach_items}`);
  return parts.join(' · ');
}

/** 一段条的长度，百分比。最长的那一条占满，空榜不除零。 */
export function rankShares(rows: RankRow[]): number[] {
  const strengths = rows.map(rankStrength);
  const ceiling = Math.max(1, ...strengths);
  return strengths.map((value) => Math.max(0, Math.min(100, value / ceiling * 100)));
}

/** 雷达图的一个顶点。 */
export interface RadarPoint { name: string; x: number; y: number; labelX: number; labelY: number }

/** 雷达图几何：320×280 的画布、中心 (160,140)、值圈半径 100。 */
export const RADAR_CENTER = { x: 160, y: 140 } as const;
export const RADAR_GRID = [25, 50, 75, 100];
/** 少于三个维度画不成面，三点以下不画。最多取前六个，再多标签互相压住。 */
export const RADAR_MIN = 3;
export const RADAR_MAX = 6;

const radarAt = (index: number, count: number, radius: number): [number, number] => {
  const angle = index / count * Math.PI * 2 - Math.PI / 2;
  return [RADAR_CENTER.x + Math.cos(angle) * radius, RADAR_CENTER.y + Math.sin(angle) * radius];
};

/** 值多边形与标签位置。值为 0 或非有限的行先滤掉，按分数从高到低取前六。 */
export function radarPoints(rows: RankRow[]): RadarPoint[] {
  const values = rows
    .filter((row) => Number.isFinite(Number(row.score)) && Number(row.score) > 0)
    .slice().sort((a, b) => Number(b.score) - Number(a.score)).slice(0, RADAR_MAX);
  if (values.length < RADAR_MIN) return [];
  const max = Math.max(...values.map((row) => Number(row.score)));
  return values.map((row, index) => {
    const [x, y] = radarAt(index, values.length, Number(row.score) / max * 100);
    const [labelX, labelY] = radarAt(index, values.length, 116);
    return { name: row.name, x, y, labelX, labelY };
  });
}

/** 一圈网格的点串。 */
export const radarRing = (radius: number, count: number): string =>
  Array.from({ length: count }, (_, index) =>
    radarAt(index, count, radius).map((value) => value.toFixed(2)).join(',')).join(' ');

export const radarShape = (points: RadarPoint[]): string =>
  points.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ');

/** 热力图里的一格。`share` 是这一格相对最忙那一格的浓度，0 到 1。 */
export interface HeatCell { key: string; label: string; count: number; share: number }

export const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

/** 有访问的格子至少留一成浓度：一次访问和一次都没有必须看得出差别。 */
const shareOf = (count: number, max: number) => (count ? Math.max(0.12, count / max) : 0);

/** 星期 × 小时的 168 格。越界或负数的记录当作没有。 */
export function hourGrid(activity: TasteActivity | undefined): { cells: HeatCell[]; total: number } {
  const counts = Array.from({ length: 7 }, () => Array<number>(24).fill(0));
  for (const item of activity?.hours || []) {
    const { weekday, hour, count } = item;
    if (!Number.isInteger(weekday) || weekday < 0 || weekday > 6) continue;
    if (!Number.isInteger(hour) || hour < 0 || hour > 23) continue;
    if (!Number.isFinite(count) || count < 0) continue;
    counts[weekday]![hour] = (counts[weekday]![hour] || 0) + count;
  }
  const flat = counts.flat();
  const max = Math.max(1, ...flat);
  const cells = counts.flatMap((row, day) => row.map((count, hour) => ({
    key: `${day}-${hour}`, label: `${WEEKDAYS[day]} ${hour}:00`, count, share: shareOf(count, max),
  })));
  return { cells, total: flat.reduce((sum, count) => sum + count, 0) };
}

/** 最近 91 天的日历。末尾那天由数据说了算，往前数 90 天，中间没有记录的那些补 0。 */
export function dayCalendar(activity: TasteActivity | undefined):
{ cells: HeatCell[]; total: number; start: string; end: string } {
  const days = (activity?.days || [])
    .filter((row) => /^\d{4}-\d{2}-\d{2}$/.test(row.date)
      && Number.isFinite(row.count) && row.count >= 0)
    .slice().sort((a, b) => a.date.localeCompare(b.date));
  const empty = { cells: [], total: 0, start: '', end: '' };
  if (!days.length) return empty;
  const end = new Date(`${days.at(-1)!.date}T00:00:00Z`);
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - 90);
  const daily = new Map(days.map((row) => [row.date, row.count]));
  const max = Math.max(1, ...days.map((row) => row.count));
  const cells = Array.from({ length: 91 }, (_, index) => {
    const date = new Date(start);
    date.setUTCDate(start.getUTCDate() + index);
    const key = date.toISOString().slice(0, 10);
    const count = daily.get(key) || 0;
    return { key, label: key, count, share: shareOf(count, max) };
  });
  return {
    cells,
    total: cells.reduce((sum, cell) => sum + cell.count, 0),
    start: start.toISOString().slice(0, 10),
    end: days.at(-1)!.date,
  };
}

/** 桑基图的一个节点。`side` 决定它落在左边还是右边，也决定它的文字往哪边排。 */
export interface FlowNode {
  id: string; name: string; side: 'source' | 'target'; index: number;
  x: number; y: number; height: number; value: number; share: number; color: number;
}
/** 一条流。`d` 是 d3 算出来的贝塞尔路径。 */
export interface FlowLink {
  key: string; d: string; width: number; color: number;
  source: number; target: number; value: number; label: string;
}
export interface FlowGraph { nodes: FlowNode[]; links: FlowLink[]; total: number }

/** 节点条宽与画布：左右各留一截给文字，视口 720×435。 */
export const FLOW_NODE_WIDTH = 10;
export const FLOW_VIEWBOX = { width: 720, height: 435 } as const;
export const FLOW_LABEL_X = { source: 145, target: 545 } as const;

/** 来源网站 → 创作者的流向布局。值为 0 或缺一端的流先滤掉，全空时返回 `null`。 */
export function flowGraph(rows: CreatorFlow[] = []): FlowGraph | null {
  const flows = rows.filter((row) =>
    row.source && row.target && Number.isFinite(row.value) && row.value > 0);
  if (!flows.length) return null;
  const sources = [...new Set(flows.map((row) => row.source))];
  const targets = [...new Set(flows.map((row) => row.target))];
  const graph = sankey<{ id: string; name: string; side: 'source' | 'target' }, object>()
    .nodeId((node) => node.id).nodeWidth(FLOW_NODE_WIDTH).nodePadding(22)
    .extent([[155, 16], [535, 404]])({
      nodes: [
        ...sources.map((name) => ({ id: `source:${name}`, name, side: 'source' as const })),
        ...targets.map((name) => ({ id: `target:${name}`, name, side: 'target' as const })),
      ],
      links: flows.map((row) => (
        { source: `source:${row.source}`, target: `target:${row.target}`, value: row.value })),
    });
  const total = flows.reduce((sum, row) => sum + row.value, 0);
  const path = sankeyLinkHorizontal();
  type Node = typeof graph.nodes[number];
  const nodes: FlowNode[] = graph.nodes.map((node) => ({
    id: node.id, name: node.name, side: node.side, index: node.index ?? 0,
    x: node.x0 ?? 0, y: node.y0 ?? 0, height: Math.max(1, (node.y1 ?? 0) - (node.y0 ?? 0)),
    value: node.value ?? 0, share: (node.value ?? 0) / total * 100,
    color: sources.indexOf(node.name) % 6,
  }));
  const links: FlowLink[] = graph.links.map((link, at) => {
    const from = link.source as Node;
    const to = link.target as Node;
    return {
      key: `${from.id}->${to.id}:${at}`, d: path(link) || '',
      width: Math.max(0.5, link.width || 0), color: sources.indexOf(from.name) % 6,
      source: from.index ?? 0, target: to.index ?? 0, value: link.value,
      label: `${from.name} → ${to.name}`,
    };
  });
  return { nodes, links, total };
}

/** 节点名字太长时截断。图里一格只有这么宽，整名在 `aria-label` 和 `<title>` 里。 */
export const flowLabel = (name: string): string =>
  (name.length > 18 ? `${name.slice(0, 16)}…` : name);
