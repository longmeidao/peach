/* 关注管理页的行为：按创作者归组、排序作用在全集上、翻页只切最后一步、勾选跨页也跨视图，
 * 以及「检查更新」那一趟后台任务什么时候算数。
 *
 * 外观（表格的分隔线、徽章档位）是设计决定，由 `frontend/e2e/design.test.ts` 读
 * `getComputedStyle` 断言；这里只看结构、文字与请求。 */
import { act } from 'react';
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { queryClient } from '../../src/react/query';
import {
  authorGroups, checkSummary, FOLLOW_CHECK_URL, FOLLOW_CREDENTIALS_URL, FOLLOW_SOURCE_URL,
  FOLLOW_URL, JOB_POLL_MS, pageWindow, prefetchFollowManage, tableRows,
  type CheckJob, type CredentialData, type FollowData, type FollowSource,
} from '../../src/react/follow-manage/follow-manage';
import { FollowManagePage } from '../../src/react/follow-manage/follow-manage-page';

import { choose, click, mountRoot, settle } from './render';

// 客户端是模块级的单例（所有 React 根共用一个），用例之间不清就互相喂数据。
afterEach(() => queryClient.clear());

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，假时钟推不动它：推完时钟
   断言到的还是上一帧的 DOM。用例里改成当场派发。 */
notifyManager.setScheduler((notify) => notify());

const source = (over: Partial<FollowSource> & { id: number }): FollowSource => ({
  provider: 'kemono',
  provider_label: 'Kemono',
  ref: `fanbox/${over.id}`,
  label: `来源 ${over.id}`,
  url: `https://example.com/${over.id}`,
  enabled: true,
  last_status: 'ok',
  last_checked_at: '2026-09-01T00:00:00Z',
  created_at: '2026-08-01T00:00:00Z',
  author_key: `name:作者${over.id}`,
  author_name: `作者${over.id}`,
  ...over,
} as FollowSource);

/** 三位创作者，其中一位在两个站上各有一条来源。 */
const CAST: FollowSource[] = [
  source({ id: 1, author_key: 'name:甲', author_name: '甲', label: '甲 · Kemono' }),
  source({
    id: 2, author_key: 'name:甲', author_name: '甲', label: '甲 · Pawchive',
    provider: 'pawchive', provider_label: 'Pawchive', last_checked_at: '2026-09-03T00:00:00Z',
  }),
  source({
    id: 3, author_key: 'name:乙', author_name: '乙', label: '乙 · Kemono',
    last_checked_at: '2026-09-02T00:00:00Z', last_status: 'error',
  }),
  source({ id: 4, author_key: 'name:丙', author_name: '丙', label: '丙 · Kemono' }),
];

const follow = (over: Partial<FollowData> = {}): FollowData => ({
  sources: CAST,
  counts: { new: 0, seen: 0, saved: 0, ignored: 0 },
  author_aliases: [],
  suggestions: [],
  ...over,
} as FollowData);

const credentials = (): CredentialData => ({ root: 'C:\\peach\\creds', providers: [] } as CredentialData);

const IDLE: CheckJob = { status: 'idle' } as CheckJob;

const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body });

interface Plan {
  data?: FollowData;
  /** 检查任务的快照：给一串就按顺序一份一份回（最后一份之后一直回它），给函数就每次现问。 */
  check?: CheckJob[] | (() => CheckJob);
  resolve?: unknown;
}

/** 按端点分流的假 fetch。写操作各回一个最小成功体。 */
function serve(plan: Plan = {}) {
  const checks = typeof plan.check === 'function' ? plan.check : [...(plan.check ?? [IDLE])];
  const fetcher = vi.fn(async (input: string, init?: RequestInit) => {
    const url = String(input);
    if (url === FOLLOW_CREDENTIALS_URL) return ok(credentials());
    if (url === FOLLOW_CHECK_URL) {
      if (init?.method) return ok({ status: 'running', checked: 0, total: 1 });
      if (typeof checks === 'function') return ok(checks());
      return ok(checks.length > 1 ? checks.shift()! : checks[0]!);
    }
    if (url === FOLLOW_SOURCE_URL) return ok({ ok: true, source: 9 });
    if (url.startsWith('/api/follow/resolve')) return ok(plan.resolve ?? IDLE);
    if (url.startsWith(FOLLOW_URL)) return ok(plan.data ?? follow());
    throw new Error(`没有安排这个端点：${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

type Props = Parameters<typeof FollowManagePage>[0];

const shellProps = (over: Partial<Props> = {}): Props => ({
  tab: 'list', page: 1, sort: '', dir: '',
  route: vi.fn(),
  pageSize: 20, layout: 'default',
  savePreference: vi.fn(),
  toast: vi.fn(),
  openFollow: vi.fn(),
  readOnly: false, readOnlyMessage: '', writerUrl: '',
  ...over,
});

/** 走完真实的首屏路径：先 prefetch 落进缓存，再挂载。 */
async function open(plan: Plan = {}, over: Partial<Props> = {}) {
  const fetcher = serve(plan);
  const props = shellProps(over);
  await prefetchFollowManage(new AbortController().signal).catch(() => {});
  const mounted = await mountRoot(
    <QueryClientProvider client={queryClient}><FollowManagePage {...props} /></QueryClientProvider>);
  await settle();
  return { fetcher, props, ...mounted };
}

const tick = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms) });

const cards = (root: ParentNode) => [...root.querySelectorAll('section[aria-label$="的关注来源"]')];

const checkboxNamed = (root: ParentNode, name: string) =>
  root.querySelector<HTMLInputElement>(`input[type="checkbox"][aria-label="${name}"]`);

const buttonLabelled = (root: ParentNode, name: string) =>
  root.querySelector<HTMLButtonElement>(`button[aria-label="${name}"]`);

const sentBody = (fetcher: ReturnType<typeof serve>, url: string) =>
  fetcher.mock.calls.filter(([input, init]) => String(input) === url && !!(init as RequestInit | undefined)?.method)
    .map(([, init]) => JSON.parse(String((init as RequestInit).body)));

// ── 纯函数：归组、排序与分页 ──────────────────────────────────────────────

it('同一位创作者在几个站上的来源归成一组', () => {
  const groups = authorGroups(CAST, 'checked', 'desc');
  expect(groups.map((group) => group.length)).toEqual([2, 1, 1]);
  expect(groups[0]!.map((row) => row.id).sort()).toEqual([1, 2]);
});

it('排序换的是全集的次序，不是某一页里面的', () => {
  const many = Array.from({ length: 25 }, (_, at) => source({
    id: at + 1, author_key: `name:人${at}`, author_name: `人${at}`,
    last_checked_at: `2026-09-${String(at + 1).padStart(2, '0')}T00:00:00Z`,
  }));
  const newest = authorGroups(many, 'checked', 'desc');
  const oldest = authorGroups(many, 'checked', 'asc');
  // 翻个方向之后，第一页第一条应当是原来最后一页的最后一条——只排当前页做不到这一点。
  expect(newest[0]![0]!.id).toBe(25);
  expect(oldest[0]![0]!.id).toBe(1);
  const win = pageWindow(newest.length, 10, 3);
  expect(win).toMatchObject({ page: 3, pages: 3, total: 25, start: 20, end: 25 });
});

it('越界的页码落到末页，不画一页空的', () => {
  expect(pageWindow(4, 10, 7)).toMatchObject({ page: 1, start: 0, end: 4 });
  expect(pageWindow(25, 10, 99)).toMatchObject({ page: 3, start: 20, end: 25 });
});

it('表格视图把创作者组拉平，一行一条来源', () => {
  const groups = authorGroups(CAST, 'source', 'asc');
  const rows = tableRows(groups, 'source', 'asc');
  expect(rows).toHaveLength(CAST.length);
  // 按来源名排的那几档把整张表拉平重排，这时不再按创作者聚在一起（丙 < 甲 < 乙）。
  expect(rows.map((row) => row.source.label))
    .toEqual(['丙 · Kemono', '甲 · Kemono', '甲 · Pawchive', '乙 · Kemono']);
  expect(rows[0]!.author).toBe('丙');
  // 每一行都带着自己那位创作者，表格里「创作者」这一列每行都写得出来。
  expect(rows.map((row) => row.author)).toEqual(['丙', '甲', '甲', '乙']);
});

it('检查完的那句话把数字说出来', () => {
  const job = {
    status: 'done',
    results: [
      { ok: true, added: 2 }, { ok: true, added: 0, updated: 0 },
      { ok: true, exhausted: true }, { ok: false, error: '连不上' },
    ],
  } as CheckJob;
  const said = checkSummary(job);
  expect(said).toContain('新增 2 条');
  expect(said).toContain('2 个来源没有更新');
  expect(said).toContain('1 个没有更多内容');
  expect(said).toContain('1 个失败');
});

// ── 页面：视图、勾选与地址栏 ──────────────────────────────────────────────

it('默认视图一位创作者一张卡', async () => {
  const { host } = await open();
  expect(cards(host).map((card) => card.getAttribute('aria-label')))
    .toEqual(['甲 的关注来源', '乙 的关注来源', '丙 的关注来源']);
});

it('勾选跨页也跨视图，批量发出去的是整个 ID 集合', async () => {
  const many = Array.from({ length: 12 }, (_, at) => source({
    id: at + 1, author_key: `name:人${at}`, author_name: `人${at}`,
  }));
  const { host, fetcher } = await open({ data: follow({ sources: many }) }, { pageSize: 10 });

  await click(checkboxNamed(host, '全选本页来源'));
  expect(host.textContent).toContain('已选 10 个来源');
  expect(host.querySelector('[data-selection-dock]')).not.toBeNull();

  // 翻到第二页再勾一条：上一页那十条还在选中集合里。
  await click([...host.querySelectorAll('button')].find((b) => b.textContent === '下一页'));
  expect(host.textContent).toContain('已选 10 个来源');
  await click(checkboxNamed(host, '选择 来源 11'));
  expect(host.textContent).toContain('已选 11 个来源');

  await click([...host.querySelectorAll('button')].find((b) => b.textContent === '暂停'));
  await settle();
  const writes = sentBody(fetcher, FOLLOW_SOURCE_URL);
  expect(writes).toHaveLength(11);
  expect(writes.map((body) => body.id).sort((a, b) => a - b))
    .toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);
  expect(writes.every((body) => body.action === 'enabled' && body.enabled === false)).toBe(true);
});

it('换成表格视图时勾选还是那一批', async () => {
  const { host, props } = await open();
  await click(checkboxNamed(host, '选择 甲 · Kemono'));
  expect(host.textContent).toContain('已选 1 个来源');

  await click(buttonLabelled(host, '表格视图'));
  expect(props.savePreference).toHaveBeenCalledWith({ layout: 'table' });
  // 版式是这台浏览器的偏好，不写进地址栏。
  for (const [params] of (props.route as ReturnType<typeof vi.fn>).mock.calls) {
    expect(params).not.toHaveProperty('layout');
  }
});

it('表格视图把每条来源摊成一行，勾的还是来源 ID', async () => {
  const { host, fetcher } = await open({}, { layout: 'table' });

  expect([...host.querySelectorAll('[role="columnheader"]')].map((cell) => cell.textContent?.trim()))
    .toEqual(['选择', '创作者', '来源', '站点', '状态', '上次检查', '操作']);
  // 卡片视图是三张卡（甲有两条来源），表格摊平之后是四行。
  expect(host.querySelectorAll('[role="row"][data-key]')).toHaveLength(4);

  await click(checkboxNamed(host, '选择 甲 · Pawchive'));
  expect(host.textContent).toContain('已选 1 个来源');

  await click([...host.querySelectorAll('button')].find((b) => b.textContent === '暂停'));
  await settle();
  expect(sentBody(fetcher, FOLLOW_SOURCE_URL)).toEqual([{ action: 'enabled', id: 2, enabled: false }]);
});

it('排序和页码一起写进地址栏，默认值不写', async () => {
  const { host, props } = await open();
  const route = props.route as ReturnType<typeof vi.fn>;

  await choose(host.querySelector('button[aria-label="关注列表排序"]'), '创作者名称');
  expect(route).toHaveBeenCalledWith({ tab: 'list', page: 1, sort: 'name', dir: '' });

  // 换回默认那一档时，`sort` 写成空串：哪一项算默认只有数据层知道。
  await choose(host.querySelector('button[aria-label="关注列表排序"]'), '检查时间');
  expect(route).toHaveBeenLastCalledWith({ tab: 'list', page: 1, sort: '', dir: '' });
});

// ── 检查更新：这一趟什么时候算数 ──────────────────────────────────────────

it('起了检查就两秒一问，停了就不再问', async () => {
  vi.useFakeTimers();
  const running = { status: 'running', checked: 1, total: 4 } as CheckJob;
  const done = { status: 'done', results: [{ ok: true, added: 3 }] } as CheckJob;
  // 服务端那一份状态由用例推进，不按问的次数数：问几次正是这里要测的东西。
  let state: CheckJob = IDLE;
  const { host, fetcher, props } = await open({ check: () => state });

  const polls = () => fetcher.mock.calls.filter(
    ([input, init]) => String(input) === FOLLOW_CHECK_URL && !(init as RequestInit | undefined)?.method).length;

  // happy-dom 里量不到工具行的宽度，按最窄那一档画：带字的按钮只剩图标，得按 aria-label 找。
  state = running;
  await click(buttonLabelled(host, '检查全部'));
  await settle();
  const started = polls();

  await tick(JOB_POLL_MS);
  await settle();
  expect(polls()).toBeGreaterThan(started);
  // 进度条是 SVG，进度写在 `aria-label` 上而不是文字节点里。
  expect(host.querySelector('[role="progressbar"]')?.getAttribute('aria-label'))
    .toBe('检查更新：已完成 1/4 个来源');

  state = done;
  await tick(JOB_POLL_MS);
  await settle();
  expect(props.toast).toHaveBeenCalledWith(expect.stringContaining('新增 3 条'));

  // 终态之后不再问：轮询关掉了。
  const settledAt = polls();
  await tick(JOB_POLL_MS * 3);
  expect(polls()).toBe(settledAt);
});

it('首屏读到的旧终态不冒充这一次的结果', async () => {
  const stale = {
    status: 'done', results: [{ ok: false, error: '上一趟的失败' }],
  } as CheckJob;
  const { host, props } = await open({ check: [stale] });
  await settle();
  // 没点过检查，所以这一份不算数：既不报回执，也不铺失败明细。
  expect(props.toast).not.toHaveBeenCalled();
  expect(host.textContent).not.toContain('上一趟的失败');
});
