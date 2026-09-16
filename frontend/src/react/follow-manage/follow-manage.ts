/* 关注管理页的数据契约、轮询节律与纯折算。九条端点在 `frontend/src` 里都只在这里声明
 * 一次（`tests/test_frontend_build.py` 盯着）。
 *
 * 这一页有三份各自节律的真相，所以有三个键：
 * - `['follow-manage']` 是来源清单、创作者别名与「猜你喜欢」，由用户的写操作推进。写完
 *   只把改动的那一条换进缓存（`setQueryData`），不为一次开关把整页重取一遍。
 * - `['follow-manage','credentials']` 是凭据状态。它按站点报「填没填」，和来源清单的改动
 *   互不影响，合成一个键就会让每次开关来源都顺带重问一遍每个站的凭据文件。
 * - `['follow-manage','check']` 与 `['follow-manage','resolve']` 是两趟后台任务的快照，
 *   节律由后台推进：跑起来两秒一次，停了就不问。
 *
 * 分组、排序、分页都是纯函数：两种视图（创作者卡片与表格）必须给出同一套顺序，比较器
 * 写在两处的话，同一份数据在两种视图里的先后就会不一样。 */
import { apiGet, apiSend } from '../../api';
import { clampPage, pageCount } from '../../pagination';
import { queryClient } from '../query';
import { localTime } from '../time';

export const FOLLOW_URL = '/api/follow';
export const FOLLOW_CREDENTIALS_URL = '/api/follow/credentials';
export const FOLLOW_CHECK_URL = '/api/follow/check';
export const FOLLOW_SOURCE_URL = '/api/follow/source';
export const FOLLOW_RESOLVE_URL = '/api/follow/resolve';
export const FOLLOW_SUGGEST_URL = '/api/follow/suggest';
export const FOLLOW_ALIAS_URL = '/api/follow/author-alias';
export const FOLLOW_CREDENTIAL_URL = '/api/follow/credential';
export const FOLLOW_STATUS_URL = '/api/follow/status';

/** 来源清单、创作者别名与推荐共用这一个键。 */
export const FOLLOW_MANAGE_KEY = ['follow-manage'] as const;
/** 各站凭据的状态。 */
export const FOLLOW_CREDENTIALS_KEY = ['follow-manage', 'credentials'] as const;
/** 检查更新那一趟后台任务。 */
export const FOLLOW_CHECK_KEY = ['follow-manage', 'check'] as const;
/** 查找关注来源那一趟后台任务。 */
export const FOLLOW_RESOLVE_KEY = ['follow-manage', 'resolve'] as const;
/** 敲字建议按词各存一份：同一个词回头再敲不必再打一趟站点的公开补全。 */
export const followSuggestKey = (term: string) => ['follow-manage', 'suggest', term] as const;

/** 一条关注来源。字段以 `_source_payload`（`src/peach/web_follow.py`）为准。 */
export interface FollowSource {
  id: number;
  provider: string;
  provider_label: string;
  ref: string;
  label: string;
  url: string;
  enabled: boolean;
  author_name?: string;
  author_key?: string;
  official_avatar_url?: string;
  avatar_url?: string;
  entity_id?: number | null;
  entity_name?: string;
  created_at?: string;
  last_checked_at?: string | null;
  last_status?: string;
  last_error?: string;
  history_exhausted?: boolean;
}

/** 一组已保存的创作者别名。 */
export interface AliasGroup {
  canonical_key: string;
  canonical_name: string;
  aliases: { key: string; name: string; source?: string }[];
}

/** 一条待合并的别名，带判定依据。合并永远由人点，服务端不自动升级。 */
export interface AliasSuggestion { canonical: string; alias: string; evidence: string }

/** 「猜你喜欢」的一位创作者，来自用户自己浏览过的在线记录。 */
export interface FollowGuess { name: string; visits: number; origin?: string }

export interface FollowCounts { new?: number; seen?: number; saved?: number; ignored?: number }

/** `/api/follow` 的响应里这一页要的那几项。 */
export interface FollowData {
  sources: FollowSource[];
  author_aliases?: AliasGroup[];
  alias_suggestions?: AliasSuggestion[];
  suggestions?: FollowGuess[];
  counts?: FollowCounts;
}

/** 一个站点的凭据状态。只报存在性与去哪儿配，不回凭据值。 */
export interface CredentialRow {
  provider: string;
  provider_label: string;
  followable: boolean;
  requirement: 'required' | 'optional' | 'none' | 'blocked';
  needs: string[];
  fields: string[];
  missing: string[];
  shared_fields?: string[];
  present?: boolean;
  world_readable?: boolean | null;
  why?: string;
  where?: string;
  howto?: string;
  path?: string;
}

export interface CredentialData { root: string; providers: CredentialRow[] }

/** 检查更新那一趟的一条结果。全部成功时页内不留持久行，摘要走 Toast。 */
export interface CheckResult {
  ok?: boolean;
  provider?: string;
  provider_label?: string;
  author?: string;
  label?: string;
  ref?: string;
  error?: string;
  evidence_error?: string;
  added?: number;
  updated?: number;
  skipped?: number;
  skipped_compilations?: number;
  history_skipped?: number;
  probed?: number;
  exhausted?: boolean;
}

/** 检查更新的任务快照。一次都没跑过是 `idle`。 */
export interface CheckJob {
  status: string;
  job_id?: string;
  checked?: number;
  total?: number;
  older?: boolean;
  message?: string;
  error?: string;
  results?: CheckResult[];
  current?: { label?: string; provider?: string; attempt?: number; max_attempts?: number; retry_in?: number };
}

/** 一条查找结果里的一个候选。`known` 是已经关注过的，列出来但不许再勾。 */
export interface ResolveCandidate {
  provider: string;
  provider_label: string;
  url: string;
  label: string;
  author?: string;
  aliases?: string[];
  evidence?: string;
  known?: boolean;
}

export interface ResolveRow {
  kind?: string;
  line: string;
  error?: string;
  candidates?: ResolveCandidate[];
  external_searches?: { label: string; query: string; url: string; evidence: string }[];
  failures?: Record<string, string>;
}

export interface ResolveJob {
  status: string;
  job_id?: string;
  checked?: number;
  total?: number;
  message?: string;
  error?: string;
  results?: ResolveRow[];
}

/** 添加框的建议。分组、顺序与组名都由服务端给，页面照抄。 */
export interface SuggestGroup {
  kind: string;
  label: string;
  items: { value: string; matched?: string; n?: number }[];
}
export interface SuggestData { q: string; groups: SuggestGroup[] }

/* ── 视图与排序的取值 ── */

/** 两种视图共用同一份来源集合、创作者顺序与勾选；表格视图一行一条来源。 */
export const LAYOUTS = [['default', '默认视图'], ['table', '表格视图']] as const;
export type Layout = (typeof LAYOUTS)[number][0];

export const PAGE_SIZES = [10, 20, 50, 100] as const;
export const DEFAULT_PAGE_SIZE = 20;

/** 工具栏那个下拉里的排序维度。前四个按创作者比，后三个按单条来源比。 */
export const SORT_OPTIONS = [
  ['checked', '检查时间'], ['added', '添加时间'], ['name', '创作者名称'], ['sources', '来源数量'],
  ['source', '来源名称'], ['provider', '站点'], ['status', '状态'],
] as const;
export type SortKey = (typeof SORT_OPTIONS)[number][0];
export const DEFAULT_SORT: SortKey = 'checked';

export type SortDir = 'asc' | 'desc';

/** 每一列问的那句话的常态：时间问「最近的先看」，名字问「从头排」。 */
export const SORT_DEFAULT_DIR: Record<SortKey, SortDir> = {
  checked: 'desc', added: 'desc', name: 'asc', sources: 'desc',
  source: 'asc', provider: 'asc', status: 'asc',
};

const SORT_LABELS: Record<SortKey, string> = Object.fromEntries(SORT_OPTIONS) as Record<SortKey, string>;

/** 表格五列各自对应工具栏里的哪一档排序。列头点的就是同一个状态。 */
export const COLUMN_SORT = {
  author: 'name', source: 'source', provider: 'provider', status: 'status', checked: 'checked',
} as const satisfies Record<string, SortKey>;

export const isSortKey = (value: unknown): value is SortKey =>
  SORT_OPTIONS.some(([key]) => key === value);

export const isLayout = (value: unknown): value is Layout =>
  LAYOUTS.some(([key]) => key === value);

export const pageSizeOf = (value: unknown): number =>
  (PAGE_SIZES as readonly number[]).includes(Number(value)) ? Number(value) : DEFAULT_PAGE_SIZE;

/** 方向词按维度各说各的：时间说远近、数量说多少，「正序」对一个时间戳不成立。
 *  第一项是从升序点下去会得到的那一头，第二项是它的反面。 */
const SORT_DIR_WORDS: Record<SortKey, readonly [string, string]> = {
  checked: ['从近到远', '从远到近'], added: ['从近到远', '从远到近'],
  name: ['倒序', '正序'], sources: ['从多到少', '从少到多'],
  source: ['倒序', '正序'], provider: ['倒序', '正序'], status: ['倒序', '正序'],
};

/** 方向按钮的无障碍名称：说的是点下去会得到什么，所以取反方向的词。照抄当前方向，
 *  读屏那边会以为点下去还是这个顺序。 */
export const sortLabel = (sort: SortKey, dir: SortDir): string =>
  `按${SORT_LABELS[sort]}${SORT_DIR_WORDS[sort][dir === 'asc' ? 0 : 1]}排序`;

/* ── 分组、排序、分页 ── */

/** 状态的排序位：失败最前，其次暂停、未检查，正常最后——正序就是「先看要处理的」。 */
export function statusRank(source: FollowSource): number {
  const state = source.last_status;
  if (state === 'error' || state === 'unauthorized') return 0;
  if (!source.enabled) return 1;
  return state === 'ok' ? 3 : 2;
}

/** 这一条此刻是什么状态。四种写法对应四种徽章。 */
export function statusText(source: FollowSource): string {
  if (source.history_exhausted) return '没有更多';
  if (!source.enabled) return '已暂停';
  if (source.last_status === 'ok') return '正常';
  return source.last_status === 'error' || source.last_status === 'unauthorized' ? '检查失败' : '未检查';
}

export const isBroken = (source: FollowSource): boolean =>
  source.last_status === 'error' || source.last_status === 'unauthorized';

const byLabel = (a: FollowSource, b: FollowSource) =>
  String(a.label || '').localeCompare(String(b.label || ''), 'zh-CN', { numeric: true });

/** 按单条来源比的三个维度。 */
const SOURCE_SORTS: Partial<Record<SortKey, (a: FollowSource, b: FollowSource) => number>> = {
  source: byLabel,
  provider: (a, b) => String(a.provider_label || '').localeCompare(
    String(b.provider_label || ''), 'zh-CN') || byLabel(a, b),
  status: (a, b) => statusRank(a) - statusRank(b) || byLabel(a, b),
};

const timeOf = (value: string | null | undefined): number => Date.parse(value || '') || 0;

/** 同名的几种写法里取大写最多的那个：`LazyProcrastinator` 比 `lazyprocrastinator`
 *  更像创作者自己写的名字。 */
const clean = (value: string | undefined): string => String(value || '')
  .replace(/\s*[·|]\s*[A-Za-z0-9_-]+\s*$/, '')
  .replace(/\s+collections?\s*$/i, '').trim();

/** 分组标题用创作者本人的名字，不是某一条来源的标签。哪一段是人名由服务端一处判定
 *  （`author_name`），这里只在同一个人的几种写法之间挑一个。 */
export function authorName(group: FollowSource[], aliases: AliasGroup[] = []): string {
  if (!group.length) return '';
  const authored = (source: FollowSource) => String(source.author_name || '').trim() || clean(source.label);
  const entity = group.find((source) => source.entity_name);
  if (entity) return entity.entity_name!;
  const aliasGroup = aliases.find((item) => `name:${item.canonical_key}` === group[0]?.author_key);
  if (aliasGroup) return clean(aliasGroup.canonical_name);
  /* 官方主页来源不只优先提供头像，也优先提供创作者写法；否则 F95 的线程标题
     `Lazy Procrastinator Collection` 会因为大写字母更多而抢成分组标题。 */
  const official = group.find((source) => source.official_avatar_url);
  if (official && authored(official)) return authored(official);
  const names = group.map(authored).filter(Boolean);
  if (!names.length) return group[0]!.label || group[0]!.ref || '';
  const caps = (text: string) => (text.match(/[A-Z]/g) || []).length;
  return names.reduce((best, name) => (caps(name) > caps(best) ? name : best), names[0]!);
}

/** 圆标里的字：先找拉丁字母或数字，没有就取第一个字。 */
export function authorInitial(name: string): string {
  const ascii = name.trim().match(/[A-Za-z0-9]/);
  return (ascii ? ascii[0] : Array.from(name.trim())[0] || '?').toUpperCase();
}

/** 同一位创作者的官方来源优先提供头像，归档来源只回退。都取不到时用首字母。 */
export function authorAvatar(group: FollowSource[]): { src: string; fallback: string } {
  const official = group.find((source) => source.official_avatar_url);
  const mirror = group.find((source) => source.avatar_url);
  const src = official?.official_avatar_url || mirror?.avatar_url || '';
  const fallback = official && mirror && mirror.avatar_url !== src ? mirror.avatar_url || '' : '';
  return { src, fallback };
}

/** 这位创作者的身份。同一个人在不同站点上是多条来源、一个人，归组用后端给的
 *  `author_key`——那是实体 id 或归一化后的名字，不在前端二次猜。 */
export const groupKey = (group: FollowSource[]): string =>
  String(group[0]?.author_key || group[0]?.id || '');

/** 按创作者归组，组内顺序是原始顺序。排序另算，归组本身不看排序。 */
export function groupByAuthor(sources: FollowSource[]): FollowSource[][] {
  const order: string[] = [];
  const byKey = new Map<string, FollowSource[]>();
  for (const source of sources) {
    const key = source.author_key || `source:${source.id}`;
    if (!byKey.has(key)) { byKey.set(key, []); order.push(key) }
    byKey.get(key)!.push(source);
  }
  return order.map((key) => byKey.get(key)!);
}

/** 排好序的创作者组。
 *
 * `flip` 只在方向偏离这一列的默认值时取反：写成「asc 就取反」的话，创作者名称默认本来
 * 就是正序，一进页面就被翻成倒序。同值回退始终按名字正序，不跟着翻——否则「来源数量」
 * 里数量相同的那几个人每换一次方向就整段倒序一遍，看着像列表在乱跳。 */
export function authorGroups(
  sources: FollowSource[], sort: SortKey, dir: SortDir, aliases: AliasGroup[] = [],
): FollowSource[][] {
  const groups = groupByAuthor(sources);
  const flip = dir === SORT_DEFAULT_DIR[sort] ? 1 : -1;
  const name = (group: FollowSource[]) => authorName(group, aliases);
  const byName = (a: FollowSource[], b: FollowSource[]) =>
    name(a).localeCompare(name(b), 'zh-CN', { numeric: true });
  const bySource = SOURCE_SORTS[sort];
  if (bySource) {
    // 先排每位创作者名下的来源，创作者之间再按各自排在最前的那条比。
    for (const group of groups) group.sort((a, b) => flip * bySource(a, b));
    return groups.sort((a, b) => flip * bySource(a[0]!, b[0]!) || byName(a, b));
  }
  const checked = (group: FollowSource[]) => Math.max(...group.map((s) => timeOf(s.last_checked_at)));
  const added = (group: FollowSource[]) => Math.max(...group.map((s) => timeOf(s.created_at)));
  return groups.sort((a, b) => {
    if (sort === 'name') return flip * byName(a, b);
    if (sort === 'sources') return flip * (b.length - a.length) || byName(a, b);
    if (sort === 'added') return flip * (added(b) - added(a)) || byName(a, b);
    return flip * (checked(b) - checked(a)) || byName(a, b);
  });
}

/** 表格视图的行：一行一条来源，创作者列每行都写。
 *
 * 行的顺序来自同一组创作者组，按来源比的那三档再把整张表拉平重排——那时表格不再按
 * 创作者聚在一起，而这正是点那三列列头要的效果。排序作用在全部结果上，分页只切最后一步。 */
export interface TableRow { source: FollowSource; group: FollowSource[]; author: string }

export function tableRows(
  groups: FollowSource[][], sort: SortKey, dir: SortDir, aliases: AliasGroup[] = [],
): TableRow[] {
  const rows = groups.flatMap((group) => {
    const author = authorName(group, aliases);
    return group.map((source) => ({ source, group, author }));
  });
  const bySource = SOURCE_SORTS[sort];
  if (bySource) {
    const flip = dir === SORT_DEFAULT_DIR[sort] ? 1 : -1;
    rows.sort((a, b) => flip * bySource(a.source, b.source));
  }
  return rows;
}

/** 一页的边界。总量、页数与当前页都按同一份计算，页脚那句读数和切片不会各说各的。 */
export interface PageWindow { page: number; pages: number; total: number; start: number; end: number }

export function pageWindow(total: number, size: number, page: number): PageWindow {
  const pages = pageCount(total, size);
  const current = clampPage(page, pages);
  const start = (current - 1) * size;
  return { page: current, pages, total, start, end: Math.min(start + size, total) };
}

/* ── 跨页与跨视图的选择 ── */

/** 勾选的身份是来源 ID，不是行号：换页、换视图、换排序之后选中的仍是同一批来源。
 *  已经不在清单里的 ID 顺手丢掉——删掉的来源不该还占着计数。 */
export function keepSelected(selected: ReadonlySet<number>, sources: FollowSource[]): Set<number> {
  const available = new Set(sources.map((source) => source.id));
  return new Set([...selected].filter((id) => available.has(id)));
}

/** 一组来源在当前选择里的样子：全选、半选还是都没选。表头与创作者行的全选键读它。 */
export function selectionState(selected: ReadonlySet<number>, ids: number[]):
{ all: boolean; some: boolean } {
  const count = ids.filter((id) => selected.has(id)).length;
  return { all: ids.length > 0 && count === ids.length, some: count > 0 && count < ids.length };
}

export function toggleGroup(selected: ReadonlySet<number>, ids: number[], on: boolean): Set<number> {
  const next = new Set(selected);
  for (const id of ids) { if (on) next.add(id); else next.delete(id) }
  return next;
}

/* ── 取数与写操作 ── */

/** 管理页只要来源清单与别名，条目本身一条就够：那一页读的是 `/follow`。 */
export const fetchFollow = (signal?: AbortSignal) =>
  apiGet<FollowData>(`${FOLLOW_URL}?limit=1`, signal);

export const fetchCredentials = (signal?: AbortSignal) =>
  apiGet<CredentialData>(FOLLOW_CREDENTIALS_URL, signal);

export const fetchCheckJob = (signal?: AbortSignal) =>
  apiGet<CheckJob>(FOLLOW_CHECK_URL, signal);

export const fetchResolveJob = (signal?: AbortSignal) =>
  apiGet<ResolveJob>(FOLLOW_RESOLVE_URL, signal);

export const fetchSuggestions = (query: string, signal?: AbortSignal) =>
  apiGet<SuggestData>(`${FOLLOW_SUGGEST_URL}?q=${encodeURIComponent(query)}`, signal);

/** 起一趟检查。`sources` 给了就只查这几条，都不给就是全部。 */
export const startCheck = (sources?: number[]) =>
  apiSend<CheckJob>(FOLLOW_CHECK_URL, { ...(sources?.length ? { sources } : {}), background: true });

/** 起一趟查找。结果先摆出来由人勾选，这一步不写任何东西。 */
export const startResolve = (lines: string[]) =>
  apiSend<ResolveJob>(FOLLOW_RESOLVE_URL, { lines, background: true });

export const setSourceEnabled = (id: number, enabled: boolean) =>
  apiSend<{ source: number; enabled: boolean }>(FOLLOW_SOURCE_URL, { action: 'enabled', id, enabled });

export const removeSource = (id: number) =>
  apiSend<{ ok: boolean }>(FOLLOW_SOURCE_URL, { action: 'remove', id });

export const addSource = (candidate: ResolveCandidate) =>
  apiSend<{ source: number }>(FOLLOW_SOURCE_URL, {
    action: 'add', url: candidate.url, label: candidate.label,
    author: candidate.author || '', aliases: candidate.aliases || [], defer_check: true,
  });

export const addAlias = (canonical: string, alias: string) =>
  apiSend<{ ok: boolean }>(FOLLOW_ALIAS_URL, { action: 'add', canonical, alias });

export const removeAlias = (alias: string) =>
  apiSend<{ ok: boolean }>(FOLLOW_ALIAS_URL, { action: 'remove', alias });

/** 保存或清除一个站点的凭据。`values` 为空就是清除。 */
export const saveCredential = (provider: string, values: Record<string, string>) =>
  apiSend<{ note?: string }>(FOLLOW_CREDENTIAL_URL, { provider, values });

export const markItem = (item: number, to: string) =>
  apiSend<{ ok: boolean }>(FOLLOW_STATUS_URL, { item, to });

/** 待处理的未看条目。批量标记要先知道有哪些，取一趟再逐条写。 */
export const fetchPending = () =>
  apiGet<{ groups?: { primary: { id: number; status: string }; variants: { id: number; status: string }[];
    duplicates: { id: number; status: string }[] }[] }>(`${FOLLOW_URL}?status=new&limit=1000`);

/** 首屏：来源清单与凭据状态取回来才画。
 *
 * 两趟后台任务不在首屏里：它们的快照常年躺着上一趟的回执，等它们只会让首屏多等一个
 * 往返，而它们自己的键挂上去就会读。中止时 `fetchQuery` 把 `AbortError` 抛回挂载方。 */
export async function prefetchFollowManage(signal: AbortSignal): Promise<void> {
  await Promise.all([
    queryClient.fetchQuery({ queryKey: FOLLOW_MANAGE_KEY, queryFn: () => fetchFollow(signal) }),
    queryClient.fetchQuery({ queryKey: FOLLOW_CREDENTIALS_KEY, queryFn: () => fetchCredentials(signal) }),
  ]);
}

/** 把改动的那一条换进缓存。整页重取会把用户正在填的表单一起重画，也会让正在读这一屏的
 *  人看见列表整个跳一下；服务端回的就是这一条的新样子，换进去即可。 */
export function patchSource(id: number, patch: Partial<FollowSource>): void {
  queryClient.setQueryData<FollowData>(FOLLOW_MANAGE_KEY, (data) => (data ? {
    ...data,
    sources: data.sources.map((row) => (row.id === id ? { ...row, ...patch } : row)),
  } : data));
}

/** 删掉的那几条直接从缓存里去掉。 */
export function dropSources(ids: number[]): void {
  const gone = new Set(ids);
  queryClient.setQueryData<FollowData>(FOLLOW_MANAGE_KEY, (data) => (data ? {
    ...data, sources: data.sources.filter((row) => !gone.has(row.id)),
  } : data));
}

/** 添加来源、合并别名这类会改变整份清单结构的写操作：换一条进去算不出新的分组与别名，
 *  只能让这一个键重取。
 *
 * `exact` 不能省：另外三个键都以 `follow-manage` 开头，按前缀失效会把凭据和两趟任务的
 * 快照一起推倒重来——正在跑的那一趟会在页面上闪回「没有任务」再跳回进度。 */
export const reloadFollowManage = (): Promise<void> =>
  queryClient.invalidateQueries({ queryKey: FOLLOW_MANAGE_KEY, exact: true });

/** 后台任务在跑的时候两秒一次，和别的后台任务同一个节律；停了就不再问。 */
export const JOB_POLL_MS = 2000;
export const jobPollInterval = (job: { status?: string } | undefined): number | false =>
  (job?.status === 'running' ? JOB_POLL_MS : false);

/** 敲字建议的防抖。这一路要打一次站点的公开补全，250ms 让连着敲的人停手之后才打一枪。 */
export const SUGGEST_DEBOUNCE_MS = 250;

/** 一次检查的结果说成一句话：新增了什么、哪些没有更新、哪些失败了。 */
export function checkSummary(job: CheckJob): string {
  const rows = job.results || [];
  const sum = (pick: (row: CheckResult) => number | undefined) =>
    rows.reduce((total, row) => total + (pick(row) || 0), 0);
  const added = sum((row) => row.added);
  const updated = sum((row) => row.updated);
  const compilations = sum((row) => row.skipped_compilations);
  const skipped = sum((row) => row.skipped) - compilations;
  const history = sum((row) => row.history_skipped);
  const probed = sum((row) => row.probed);
  const quiet = rows.filter((row) => row.ok && !row.added && !row.updated).length;
  const failed = rows.filter((row) => !row.ok).length;
  const bits: string[] = [];
  if (added) bits.push(`新增 ${added} 条`);
  if (updated) bits.push(`更新 ${updated} 条`);
  if (skipped) bits.push(`跳过 ${skipped} 条无资源`);
  if (compilations) bits.push(`排除 ${compilations} 个超大合集`);
  if (history) bits.push(`跳过 ${history} 条超出首次采集范围的历史内容`);
  if (probed) bits.push(`回查 ${probed} 条`);
  if (quiet) bits.push(`${quiet} 个来源没有更新`);
  if (!bits.length) bits.push('没有任何更新');
  /* 「抓到头了」和「这次没有更新」是两件事：前者以后也不会再有，后者下次还得再问一遍。
     这句只跟着回执走，页内那条持久行只装要处理的东西。 */
  const exhausted = rows.filter((row) => row.exhausted).length;
  if (exhausted) bits.push(`${exhausted} 个没有更多内容`);
  if (failed) bits.push(`${failed} 个失败`);
  return `检查了 ${rows.length} 个来源：${bits.join(' · ')}`;
}

/** 页内持久行只装要处理的东西：失败与取证缺档。全部成功时没有这一行。 */
export const checkFailures = (job: CheckJob | null): CheckResult[] =>
  (job?.results || []).filter((row) => !row.ok);

export const checkEvidenceGap = (job: CheckJob | null): string =>
  (job?.results || []).find((row) => row.evidence_error)?.evidence_error || '';

export { localTime };

export const checkedText = (source: FollowSource): string =>
  (source.last_checked_at ? localTime(source.last_checked_at) : '未检查');

/** 有站点图标的来源。图标由服务端按 `follow_assets.SOURCE_ICON_URLS` 取回并存在本机，
 *  页面只认这份名单：没登记的来源直接不出 `<img>`。 */
export const SOURCE_ICON_PROVIDERS = new Set([
  'fanbox', 'patreon', 'subscribestar', 'kemono', 'coomer', 'pawchive',
  'rule34video', 'rule34xxx', 'rule34paheal', 'gofile', 'f95zone', 'simpcity',
]);

export const sourceIconUrl = (provider: string): string =>
  (SOURCE_ICON_PROVIDERS.has(provider) ? `/source-icon?provider=${encodeURIComponent(provider)}` : '');

/** 四种凭据状态四种说法：待办（缺凭据）和完成（已配置）不能同色，那正是要一眼分开的两件事。 */
export const CREDENTIAL_STATE: Record<string, string> = {
  required: '需要', optional: '可选', none: '不需要', blocked: '接不进来',
};

export const credentialDone = (row: CredentialRow): boolean =>
  !!row.present && !row.missing.length;
