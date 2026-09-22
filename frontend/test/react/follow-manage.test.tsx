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
  authorAvatar, authorGroups, authorInitial, authorName, checkSummary, FOLLOW_CHECK_URL,
  FOLLOW_CREDENTIAL_URL, FOLLOW_CREDENTIALS_URL, FOLLOW_RESOLVE_URL, FOLLOW_SOURCE_URL,
  FOLLOW_SUGGEST_URL, FOLLOW_URL, JOB_POLL_MS, pageWindow, prefetchFollowManage,
  sortLabel, SUGGEST_DEBOUNCE_MS, tableRows,
  type CheckJob, type CredentialData, type CredentialRow, type FollowData, type FollowSource,
  type ResolveJob, type SuggestData,
} from '../../src/react/follow-manage/follow-manage';
import { FollowManagePage } from '../../src/react/follow-manage/follow-manage-page';

import { buttonNamed, choose, click, mountRoot, pending, settle, type } from './render';

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

const refuse = (error: string) => ({ ok: false, status: 400, json: async () => ({ error }) });

interface Plan {
  data?: FollowData;
  creds?: CredentialData;
  /** 检查任务的快照：给一串就按顺序一份一份回（最后一份之后一直回它），给函数就每次现问。
   *  函数回一个还没兑现的 Promise，就是这一问还在路上。 */
  check?: CheckJob[] | (() => CheckJob | Promise<CheckJob>);
  /** 查找任务此刻的快照，每次现问：用例在点「查找」之前把它推到想要的那一步。 */
  resolve?: () => ResolveJob | Promise<ResolveJob>;
  /** 敲字建议。回一个不落地的 Promise 就能停在「正在查找建议」那一刻。 */
  suggest?: (q: string) => SuggestData | Promise<SuggestData>;
  /** 登记一条来源。回 `refuse(...)` 就是这一条被服务端挡回来。 */
  add?: (body: { url: string; label: string }) => unknown;
}

/** 按端点分流的假 fetch。写操作各回一个最小成功体。 */
function serve(plan: Plan = {}) {
  const checks = typeof plan.check === 'function' ? plan.check : [...(plan.check ?? [IDLE])];
  const fetcher = vi.fn(async (input: string, init?: RequestInit) => {
    const url = String(input);
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    if (url === FOLLOW_CREDENTIALS_URL) return ok(plan.creds ?? credentials());
    if (url === FOLLOW_CREDENTIAL_URL) return ok({});
    if (url === FOLLOW_CHECK_URL) {
      if (init?.method) return ok({ status: 'running', checked: 0, total: 1 });
      if (typeof checks === 'function') return ok(await checks());
      return ok(checks.length > 1 ? checks.shift()! : checks[0]!);
    }
    if (url === FOLLOW_SOURCE_URL) {
      if (body?.action === 'add' && plan.add) return plan.add(body);
      return ok({ ok: true, source: 9 });
    }
    if (url === FOLLOW_RESOLVE_URL) {
      if (init?.method) return ok({ status: 'running' });
      return ok(plan.resolve ? await plan.resolve() : IDLE);
    }
    if (url.startsWith(`${FOLLOW_SUGGEST_URL}?`)) {
      const q = new URL(url, 'http://peach.test').searchParams.get('q') || '';
      return ok(await (plan.suggest ? plan.suggest(q) : { q, groups: [] }));
    }
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

it('添加时间看创作者最近登记的那条，名字默认正序不被方向翻过去', () => {
  const rows = [
    source({ id: 1, author_key: 'name:b', author_name: 'b', created_at: '2026-08-01T00:00:00Z' }),
    source({ id: 2, author_key: 'name:a', author_name: 'a', created_at: '2026-08-03T00:00:00Z' }),
    source({ id: 3, author_key: 'name:b', author_name: 'b', created_at: '2026-08-05T00:00:00Z' }),
  ];
  const authors = (groups: FollowSource[][]) => groups.map((group) => group[0]!.author_name);
  expect(authors(authorGroups(rows, 'added', 'desc'))).toEqual(['b', 'a']);
  expect(authors(authorGroups(rows, 'added', 'asc'))).toEqual(['a', 'b']);
  expect(authors(authorGroups(rows, 'name', 'asc'))).toEqual(['a', 'b']);
});

it('方向键读出的是点下去会得到的那一头', () => {
  expect(sortLabel('checked', 'desc')).toBe('按检查时间从远到近排序');
  expect(sortLabel('name', 'asc')).toBe('按创作者名称倒序排序');
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

it('卡片里每条来源两枚图标键，勾中的那条自己标出来', async () => {
  const { host } = await open();
  const card = cards(host)[0]!;
  expect(buttonLabelled(card, '检查 甲 的全部来源')).not.toBeNull();
  const rows = () => [...card.querySelectorAll('[data-source-divider] > *')];
  expect(rows()).toHaveLength(2);
  for (const row of rows()) {
    const icons = [...row.querySelectorAll('button')].filter((button) => !button.textContent?.trim());
    expect(icons.map((button) => button.getAttribute('aria-label'))).toHaveLength(2);
  }

  await click(checkboxNamed(host, '选择 甲 · Kemono'));
  expect(rows().filter((row) => row.hasAttribute('data-selected'))).toHaveLength(1);
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
  expect(checkboxNamed(host, '选择 甲 · Pawchive')?.closest('[role="row"]')
    ?.hasAttribute('data-follow-selected')).toBe(true);

  await click([...host.querySelectorAll('button')].find((b) => b.textContent === '暂停'));
  await settle();
  expect(sentBody(fetcher, FOLLOW_SOURCE_URL)).toEqual([{ action: 'enabled', id: 2, enabled: false }]);
});

it('表格的可排序列显示并更新排序三角', async () => {
  const { host, props } = await open({}, { layout: 'table' });
  const author = [...host.querySelectorAll<HTMLElement>('[role="columnheader"]')]
    .find((cell) => cell.textContent?.includes('创作者'));
  expect(author?.querySelector('svg')).not.toBeNull();

  await click(author);
  expect(props.route).toHaveBeenCalledWith({ tab: 'list', page: 1, sort: 'name', dir: '' });
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

it('点下检查到重读回来之间，缓存里上一趟的终态不冒充这一趟的回执', async () => {
  const stale = { status: 'done', results: [{ ok: false, error: '上一趟的失败' }] } as CheckJob;
  let state: CheckJob | Promise<CheckJob> = stale;
  const { host, props } = await open({ check: () => state });
  const reread = pending<CheckJob>();
  state = reread.answer;
  await click(buttonLabelled(host, '检查全部'));
  await settle();
  // 重读还没回来，但这一趟已经起了：既不该报回执，也不该把上一趟的失败铺成这一趟的。
  expect(props.toast).not.toHaveBeenCalled();
  expect(host.textContent).not.toContain('上一趟的失败');
  expect(host.querySelector('[role="progressbar"]')).not.toBeNull();

  await reread.release({ status: 'done', results: [{ ok: true, added: 2 }] } as CheckJob);
  await settle();
  expect(props.toast).toHaveBeenCalledTimes(1);
  expect(props.toast).toHaveBeenCalledWith(expect.stringContaining('新增 2 条'));
});

it('检查失败逐条说出是哪个站上的谁，缺哪样就往下一样取', async () => {
  let state: CheckJob = IDLE;
  const { host, fetcher } = await open({ check: () => state });
  state = { status: 'running', checked: 0, total: 3 } as CheckJob;
  await click(buttonLabelled(host, '检查全部'));
  await settle();
  // 「检查全部」不点名来源，由服务端取全部启用的那几条。
  expect(sentBody(fetcher, FOLLOW_CHECK_URL)).toEqual([{ background: true }]);
  state = {
    status: 'done',
    results: [
      { ok: false, provider_label: 'Kemono', author: '乙', label: '乙 · Kemono', error: '连不上' },
      { ok: false, provider: 'pawchive', label: '甲 · Pawchive' },
      { ok: false, provider_label: 'F95zone', ref: 'threads/42', error: '要登录' },
      { ok: true, added: 1, evidence_error: '磁盘已满' },
    ],
  } as CheckJob;
  await act(async () => { await queryClient.refetchQueries({ queryKey: ['follow-manage', 'check'] }) });
  await settle();
  expect(host.textContent).toContain('3 个来源检查失败');
  expect([...host.querySelectorAll('[aria-live] li')].map((row) => row.textContent)).toEqual([
    'Kemono 乙：连不上', 'pawchive 甲 · Pawchive：未说明原因', 'F95zone threads/42：要登录',
  ]);
  // 成功的那条也可能没留下原始响应：候选照样入库，但这件事得说出来。
  expect(host.textContent).toContain('候选已入库，但这一次的原始响应没有留档：磁盘已满');
});

it('创作者卡上那一枚只检查这位创作者还开着的来源', async () => {
  const sources = CAST.map((row) => (row.id === 2 ? { ...row, enabled: false } : row));
  const { host, fetcher } = await open({ data: follow({ sources }) });
  await click(buttonLabelled(host, '检查 甲 的全部来源'));
  await settle();
  expect(sentBody(fetcher, FOLLOW_CHECK_URL)).toEqual([{ sources: [1], background: true }]);
});

// ── 创作者身份：名字、首字母与头像 ──────────────────────────────────────────

it('组名取官方来源上的写法，归档标题的 Collection 后缀不算名字', () => {
  const mirror = source({ id: 1, author_name: '', label: 'Lazy Procrastinator Collection' });
  const official = source({ id: 2, author_name: 'lazyprocrastinator', official_avatar_url: '/a.png' });
  expect(authorName([mirror, official])).toBe('lazyprocrastinator');
  expect(authorName([mirror])).toBe('Lazy Procrastinator');
});

it('首字母取创作者名里的第一个拉丁字母或数字，没有才取第一个字', () => {
  expect(authorInitial('lazy')).toBe('L');
  expect(authorInitial('初音 miku')).toBe('M');
  expect(authorInitial('初音')).toBe('初');
});

it('头像先用官方的，取不下来退到镜像的，再取不下来画首字母', async () => {
  const official = source({ id: 1, official_avatar_url: '/official.png' });
  const mirror = source({ id: 2, avatar_url: '/mirror.png' });
  expect(authorAvatar([mirror, official])).toEqual({ src: '/official.png', fallback: '/mirror.png' });
  expect(authorAvatar([mirror])).toEqual({ src: '/mirror.png', fallback: '' });

  const kou = { author_key: 'name:kou', author_name: 'kou' };
  const { host } = await open({ data: follow({ sources: [
    source({ ...official, ...kou }), source({ ...mirror, ...kou }),
  ] }) });
  const avatar = () => cards(host)[0]!.querySelector('[data-follow-author-header]')!.firstElementChild!;
  expect(avatar().getAttribute('src')).toBe('/official.png');
  await act(async () => { avatar().dispatchEvent(new Event('error')) });
  expect(avatar().getAttribute('src')).toBe('/mirror.png');
  await act(async () => { avatar().dispatchEvent(new Event('error')) });
  expect(avatar().tagName).toBe('SPAN');
  expect(avatar().textContent).toBe('K');
});

it('按状态正序先列要处理的：失败、暂停、未检查、正常', () => {
  const rows = [
    source({ id: 1, label: '正常', last_status: 'ok' }),
    source({ id: 2, label: '未检查', last_status: '' }),
    source({ id: 3, label: '暂停', enabled: false, last_status: 'ok' }),
    source({ id: 4, label: '失败', last_status: 'unauthorized' }),
  ];
  expect(authorGroups(rows, 'status', 'asc').map((group) => group[0]!.label))
    .toEqual(['失败', '暂停', '未检查', '正常']);
});

// ── 关注列表：写回、计数与空态 ───────────────────────────────────────────────

const listReads = (fetcher: ReturnType<typeof serve>) => fetcher.mock.calls.filter(([input, init]) =>
  String(input).startsWith(`${FOLLOW_URL}?`) && !(init as RequestInit | undefined)?.method).length;

it('暂停只改那一条的状态，不把整张清单重取一遍', async () => {
  const { host, fetcher } = await open();
  const before = listReads(fetcher);
  await click(checkboxNamed(host, '选择 甲 · Kemono'));
  await click(buttonNamed('暂停', host));
  await settle();
  expect(listReads(fetcher)).toBe(before);
  const card = cards(host)[0]!;
  expect([...card.querySelectorAll('[data-source-divider] > *')].map((row) => row.textContent))
    .toEqual([expect.stringContaining('已暂停'), expect.stringContaining('正常')]);
});

it('卡片标题行只摆站标，站名留给读屏', async () => {
  const { host } = await open();
  const head = cards(host)[0]!.querySelector('[data-follow-author-header]')!;
  expect(head.textContent).toContain('来源：Kemono、Pawchive');
  expect(head.querySelector('[title="Kemono、Pawchive"]')).not.toBeNull();
});

it('还有未看时卡底给出计数和三颗动作键，没有未看就整条不出现', async () => {
  const counts = { new: 3, seen: 1, saved: 0, ignored: 2 };
  const busy = await open({ data: follow({ counts }) });
  expect(busy.host.textContent).toContain('4 个来源 · 3 条未看');
  expect(busy.host.textContent).toContain('未看 3 · 已看 1 · 已保存 0 · 已忽略 2');
  expect(buttonNamed('全部标记已看', busy.host)).not.toBeNull();
  expect(buttonNamed('全部忽略', busy.host)).not.toBeNull();
  await click(buttonNamed('去看更新', busy.host));
  expect(busy.props.openFollow).toHaveBeenCalledTimes(1);
  await busy.unmount();
  queryClient.clear();

  const quiet = await open();
  expect(quiet.host.textContent).not.toContain('未看 0');
  expect(buttonNamed('全部忽略', quiet.host)).toBeNull();
});

it('一条来源都没有时说清这里会显示什么', async () => {
  const { host } = await open({ data: follow({ sources: [] }) });
  expect(host.textContent).toContain('还没有关注来源');
  expect(host.textContent).toContain('关注来源及其检查状态会显示在这里。');
});

// ── 页签与只读 ──────────────────────────────────────────────────────────────

it('三栏按做事的先后排，缺凭据的数挂在最后一栏上', async () => {
  const { host } = await open({ creds: { root: 'C:\\creds', providers: [credential({ provider: 'fanbox' })] } });
  expect([...host.querySelectorAll('[role="tab"]')].map((tab) => tab.textContent))
    .toEqual(['关注列表', '添加关注', '来源和凭证（1）']);
});

it('只读的这台说清楚、指向写入端，写操作一律停用', async () => {
  const writer = 'https://writer.example/follow-manage';
  const list = await open({}, { readOnly: true, readOnlyMessage: '本机是只读副本', writerUrl: writer });
  expect(list.host.textContent).toContain('本机只能浏览');
  expect(list.host.textContent).toContain('本机是只读副本');
  expect([...list.host.querySelectorAll('a')].find((a) => a.textContent?.includes('前往写入端管理关注'))
    ?.getAttribute('href')).toBe(writer);
  expect(buttonLabelled(list.host, '检查全部')?.disabled).toBe(true);
  expect(buttonLabelled(list.host, '移除 甲 · Kemono')?.disabled).toBe(true);
  await list.unmount();
  queryClient.clear();

  const add = await open({}, { tab: 'add', readOnly: true });
  expect(lookupField(add.host).disabled).toBe(true);
});

// ── 添加关注：查找、候选与登记 ───────────────────────────────────────────────

/** 查找框。BoardUI 的 `Input` 把无障碍名称落在外层字段上，输入框在它里面。 */
function lookupField(root: ParentNode): HTMLInputElement {
  const named = root.querySelector('[aria-label="来源链接、名字或 id"]');
  const field = named instanceof HTMLInputElement ? named : named?.querySelector('input');
  if (!field) throw new Error('查找框没有画出来');
  return field;
}

const press = (el: Element, key: string) => act(async () => {
  el.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
});

const focus = (el: HTMLElement) => act(async () => { el.focus() });

/** 一条候选的勾选框，按它那一行的文字找。 */
const candidateBox = (root: ParentNode, text: string) =>
  [...root.querySelectorAll('label')].find((label) => label.textContent?.includes(text))
    ?.querySelector<HTMLInputElement>('input[type="checkbox"]') ?? null;

const lookups = (fetcher: ReturnType<typeof serve>) => sentBody(fetcher, FOLLOW_RESOLVE_URL);

const CANDIDATES = {
  line: 'kou',
  candidates: [
    { provider: 'kemono', provider_label: 'Kemono', url: 'https://kemono.test/kou', label: 'kou · Kemono',
      author: 'kou', aliases: ['kou_art'], evidence: '站内同名' },
    { provider: 'pawchive', provider_label: 'Pawchive', url: 'https://pawchive.test/kou', label: 'kou · Pawchive',
      author: 'kou', evidence: '站内同名' },
    { provider: 'fanbox', provider_label: 'Fanbox', url: 'https://fanbox.test/kou', label: 'kou · Fanbox',
      author: 'kou', known: true, evidence: '站内同名' },
  ],
};

/** 服务端那一趟查找。首屏读到的是空闲，用例在点「查找」之前把它推到想要的那一步。 */
function lookupJob() {
  let state: ResolveJob | Promise<ResolveJob> = IDLE as ResolveJob;
  return {
    resolve: () => state,
    set: (next: ResolveJob | Promise<ResolveJob>) => { state = next },
    finish: (results: ResolveJob['results']) => { state = { status: 'complete', results } as ResolveJob },
  };
}

const RUNNING = { status: 'running' } as ResolveJob;

async function lookUp(host: HTMLElement, text: string) {
  await type(lookupField(host), text);
  await press(lookupField(host), 'Enter');
  await settle();
}

it('回车和「查找」键走同一趟查找，查找框是一行字不是一叠地址', async () => {
  const { host, fetcher } = await open({}, { tab: 'add' });
  expect(host.querySelector('textarea')).toBeNull();

  await lookUp(host, '  kou  ');
  await type(lookupField(host), 'https://kemono.test/kou');
  await click(buttonNamed('查找', host));
  await settle();
  expect(lookups(fetcher)).toEqual([
    { lines: ['kou'], background: true },
    { lines: ['https://kemono.test/kou'], background: true },
  ]);
});

it('一趟查找没跑完时不起第二趟，按钮进忙态', async () => {
  const job = lookupJob();
  const { host, fetcher } = await open({ resolve: job.resolve }, { tab: 'add' });
  job.set(RUNNING);
  await lookUp(host, 'kou');
  expect(buttonNamed('查找', host)?.getAttribute('aria-busy')).toBe('true');
  await lookUp(host, 'kou again');
  expect(lookups(fetcher)).toHaveLength(1);
});

it('等待时说的话跟着这一趟查的是名字还是链接走', async () => {
  const hint = async (text: string) => {
    const job = lookupJob();
    const { host, unmount } = await open({ resolve: job.resolve }, { tab: 'add' });
    job.set(RUNNING);
    await lookUp(host, text);
    const said = host.querySelector('[aria-live] [role="status"]')?.textContent;
    await unmount();
    queryClient.clear();
    return said;
  };
  // 按名字查的第一趟要下载创作者索引，几十秒没有动静得先说一声；贴链接不走索引。
  expect(await hint('kou')).toContain('首次按名字查要下载创作者索引');
  expect(await hint('https://kemono.test/kou')).toBe('识别中…');
});

it('说得出进度的查找画进度条', async () => {
  const job = lookupJob();
  const { host } = await open({ resolve: job.resolve }, { tab: 'add' });
  job.set({ status: 'running', checked: 2, total: 5 } as ResolveJob);
  await lookUp(host, 'kou');
  expect(host.querySelector('[role="progressbar"]')?.getAttribute('aria-label')).toBe('查找中：2/5');
});

it('点下查找到重读回来之间，上一次的结果不冒充这一次的', async () => {
  const job = lookupJob();
  job.finish([CANDIDATES]);
  const { host } = await open({ resolve: job.resolve }, { tab: 'add' });
  const reread = pending<ResolveJob>();
  job.set(reread.answer);
  await lookUp(host, 'someone else');
  expect(host.textContent).not.toContain('kou · Kemono');
  expect(host.querySelector('[aria-live] [role="status"]')).not.toBeNull();

  await reread.release({ status: 'complete', results: [{ line: 'someone else', candidates: [] }] } as ResolveJob);
  await settle();
  expect(host.textContent).toContain('站内没有查到来源');
  expect(host.textContent).not.toContain('kou · Kemono');
});

it('查完先列候选、默认勾上，已经关注的列出来但勾不动，点了「添加选中」才登记', async () => {
  const job = lookupJob();
  const { host, fetcher } = await open({ resolve: job.resolve }, { tab: 'add' });
  job.finish([CANDIDATES]);
  await lookUp(host, 'kou');

  // 结果留在「添加关注」这一张卡里，不另起标题。
  const panel = [...host.querySelectorAll('h3')].find((h) => h.textContent === '添加关注')!.parentElement!;
  expect(panel.textContent).toContain('查找结果');
  expect(panel.querySelectorAll('h3')).toHaveLength(1);

  expect(candidateBox(panel, 'kou · Kemono')?.checked).toBe(true);
  expect(candidateBox(panel, 'kou · Fanbox')?.disabled).toBe(true);
  expect(candidateBox(panel, 'kou · Fanbox')?.checked).toBe(false);
  expect(candidateBox(panel, 'kou · Fanbox')?.closest('label')?.textContent).toContain('已经关注');
  expect(sentBody(fetcher, FOLLOW_SOURCE_URL)).toEqual([]);

  await click(candidateBox(panel, 'kou · Pawchive'));
  await click(buttonNamed('添加选中（1）', host));
  await settle();
  // 当初是按谁查的一起写回去：同一个人在几个站上的来源靠它归成一组。
  expect(sentBody(fetcher, FOLLOW_SOURCE_URL)).toEqual([{
    action: 'add', url: 'https://kemono.test/kou', label: 'kou · Kemono',
    author: 'kou', aliases: ['kou_art'], defer_check: true,
  }]);
  // 登记时跳过了检查，登记完一次性起一趟。
  expect(sentBody(fetcher, FOLLOW_CHECK_URL)).toEqual([{ sources: [9], background: true }]);
});

it('登记失败的那几条原因留在页面上，清单重取也冲不掉', async () => {
  const job = lookupJob();
  const { host, fetcher, props } = await open({
    resolve: job.resolve,
    add: (body) => (body.label === 'kou · Pawchive' ? refuse('站点拒绝') : ok({ source: 9 })),
  }, { tab: 'add' });
  job.finish([CANDIDATES]);
  await lookUp(host, 'kou');
  const before = listReads(fetcher);

  await click(buttonNamed('添加选中（2）', host));
  await settle();
  expect(listReads(fetcher)).toBeGreaterThan(before);
  expect(host.textContent).toContain('这一次没有完成');
  expect(host.textContent).toContain('kou · Pawchive：站点拒绝');
  expect(sentBody(fetcher, FOLLOW_CHECK_URL)).toEqual([{ sources: [9], background: true }]);
  expect(props.toast).not.toHaveBeenCalled();
});

it('站内查不到时先说为什么，再给一条能点的外部搜索', async () => {
  const job = lookupJob();
  const { host } = await open({ resolve: job.resolve }, { tab: 'add' });
  job.finish([{
    line: 'kou',
    candidates: [],
    external_searches: [{
      label: 'Google', query: 'site:f95zone.to kou', url: 'https://www.google.com/search?q=kou',
      evidence: 'F95 站内搜索要登录',
    }],
  }]);
  await lookUp(host, 'kou');
  expect(host.textContent).toContain('站内没有查到来源');
  const link = [...host.querySelectorAll('a')].find((a) => a.textContent?.includes('Google：site:f95zone.to kou'))!;
  expect(link.getAttribute('href')).toBe('https://www.google.com/search?q=kou');
  const why = [...host.querySelectorAll('small')].find((node) => node.textContent === 'F95 站内搜索要登录')!;
  expect(why.compareDocumentPosition(link) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

it('来源筛选按钮写着筛到哪几个站，筛掉的站既不显示也不登记', async () => {
  const creds = {
    root: 'C:\\creds',
    providers: [
      credential({ provider: 'kemono', provider_label: 'Kemono', requirement: 'none', missing: [] }),
      credential({ provider: 'pawchive', provider_label: 'Pawchive', requirement: 'none', missing: [] }),
    ],
  };
  const job = lookupJob();
  const { host } = await open({ creds, resolve: job.resolve }, { tab: 'add' });
  job.finish([CANDIDATES]);
  await lookUp(host, 'kou');

  await click(buttonLabelled(host, '全部来源'));
  await click(buttonNamed('全不选'));
  expect(buttonLabelled(host, '0/2 个来源')).not.toBeNull();
  expect(candidateBox(host, 'kou · Kemono')).toBeNull();
  expect(buttonNamed('添加选中（0）', host)?.disabled).toBe(true);

  await click(buttonNamed('全选'));
  expect(buttonLabelled(host, '全部来源')).not.toBeNull();
  expect(buttonNamed('添加选中（2）', host)).not.toBeNull();
});

it('筛选里撞见缺凭据的站，一步跳到凭据那一栏', async () => {
  const creds = { root: 'C:\\creds', providers: [credential({ provider: 'fanbox', provider_label: 'Fanbox' })] };
  const { host, props } = await open({ creds }, { tab: 'add' });
  await click(buttonLabelled(host, '全部来源'));
  await click(buttonNamed('需要配置凭据'));
  expect(props.route).toHaveBeenLastCalledWith(expect.objectContaining({ tab: 'source' }));
  expect([...host.querySelectorAll('h3')].map((h) => h.textContent)).toContain('来源和凭证');
});

it('「猜你喜欢」点一下就拿那个名字去查', async () => {
  const data = follow({ suggestions: [{ name: 'lewdgazer', visits: 12, origin: 'Chrome' }] });
  const { host, fetcher } = await open({ data }, { tab: 'add' });
  const guess = buttonNamed('lewdgazer', host)!;
  expect(guess.getAttribute('title')).toBe('浏览历史里出现 12 次 · Chrome');
  await click(guess);
  await settle();
  expect(lookups(fetcher)).toEqual([{ lines: ['lewdgazer'], background: true }]);
});

// ── 添加关注：敲字建议 ───────────────────────────────────────────────────────

const SUGGESTED: SuggestData = {
  q: 'strau',
  groups: [
    { kind: 'library', label: '馆藏', items: [{ value: 'strauzek' }] },
    { kind: 'site', label: 'Kemono', items: [{ value: 'Mr_Strauz', matched: 'Mr_Strauz (Kemono)' }] },
  ],
};

const suggestCalls = (fetcher: ReturnType<typeof serve>) => fetcher.mock.calls
  .map(([input]) => String(input)).filter((url) => url.startsWith(`${FOLLOW_SUGGEST_URL}?`));

async function typeAndWait(host: HTMLElement, text: string) {
  await focus(lookupField(host));
  await type(lookupField(host), text);
  await tick(SUGGEST_DEBOUNCE_MS);
  await settle();
}

it('连着敲只在停手之后问一次，地址不进建议这一路', async () => {
  vi.useFakeTimers();
  const { host, fetcher } = await open({ suggest: () => SUGGESTED }, { tab: 'add' });
  await focus(lookupField(host));
  await type(lookupField(host), 'st');
  await tick(SUGGEST_DEBOUNCE_MS / 2);
  await typeAndWait(host, 'strau');
  expect(suggestCalls(fetcher)).toEqual([`${FOLLOW_SUGGEST_URL}?q=strau`]);

  await typeAndWait(host, 'https://kemono.test/strau');
  await tick(SUGGEST_DEBOUNCE_MS);
  expect(suggestCalls(fetcher)).toHaveLength(1);
});

it('建议按服务端给的分组和次序列出，上下键选中再回车就查那个名字', async () => {
  vi.useFakeTimers();
  const { host, fetcher } = await open({ suggest: () => SUGGESTED }, { tab: 'add' });
  await typeAndWait(host, 'strau');
  expect([...host.querySelectorAll('[aria-label="来源建议"] button')].map((row) => row.textContent))
    .toEqual(['strauzek馆藏', 'Mr_Strauz (Kemono)Kemono']);

  await press(lookupField(host), 'ArrowDown');
  await press(lookupField(host), 'ArrowDown');
  await press(lookupField(host), 'Enter');
  await settle();
  expect(lookups(fetcher)).toEqual([{ lines: ['Mr_Strauz'], background: true }]);
});

it('鼠标点建议时查找框不失焦，点中的那个名字直接去查', async () => {
  vi.useFakeTimers();
  const { host, fetcher } = await open({ suggest: () => SUGGESTED }, { tab: 'add' });
  await typeAndWait(host, 'strau');
  const row = host.querySelector('[aria-label="来源建议"] button')!;
  const down = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
  await act(async () => { row.dispatchEvent(down) });
  expect(down.defaultPrevented).toBe(true);
  await click(row);
  await settle();
  expect(lookups(fetcher)).toEqual([{ lines: ['strauzek'], background: true }]);
});

it('输入法选字时的回车归输入法，不拿半截拼音去查', async () => {
  const { host, fetcher } = await open({}, { tab: 'add' });
  await type(lookupField(host), 'chu');
  await act(async () => {
    lookupField(host).dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Enter', isComposing: true, bubbles: true, cancelable: true,
    }));
  });
  await settle();
  expect(lookups(fetcher)).toEqual([]);
});

it('站点还没回话时下拉里是一行等待，回车查的是框里敲的字', async () => {
  vi.useFakeTimers();
  const { host, fetcher } = await open({ suggest: () => new Promise<SuggestData>(() => {}) }, { tab: 'add' });
  await typeAndWait(host, 'strau');
  expect(host.querySelector('[aria-label="来源建议"]')?.textContent).toContain('正在查找建议');
  await press(lookupField(host), 'ArrowDown');
  await press(lookupField(host), 'Enter');
  await settle();
  expect(lookups(fetcher)).toEqual([{ lines: ['strau'], background: true }]);
});

// ── 来源和凭证 ──────────────────────────────────────────────────────────────

function credential(over: Partial<CredentialRow> & { provider: string }): CredentialRow {
  return {
    provider_label: over.provider, followable: true, requirement: 'required',
    needs: ['cookie'], fields: [], missing: ['cookie'], present: false, ...over,
  } as CredentialRow;
}

const CREDENTIAL_CAST: CredentialData = {
  root: 'C:\\peach\\creds',
  providers: [
    credential({
      provider: 'fanbox', provider_label: 'Fanbox', needs: ['FANBOXSESSID', 'cf_clearance'],
      missing: ['FANBOXSESSID', 'cf_clearance'], why: '会员内容要登录后才看得到。',
      where: 'https://www.fanbox.cc/', howto: '从浏览器开发者工具里复制。', path: 'C:\\peach\\creds\\fanbox.json',
    }),
    credential({
      provider: 'patreon', provider_label: 'Patreon', requirement: 'optional', present: true,
      fields: ['cookie'], missing: [], world_readable: true,
    }),
    credential({
      provider: 'onlyfans', provider_label: 'OnlyFans', requirement: 'blocked', needs: [], missing: [],
      why: '站点要求设备指纹，接不进来。',
    }),
    credential({ provider: 'kemono', provider_label: 'Kemono', requirement: 'none', needs: [], missing: [] }),
  ],
};

/** 一个站那一行，从站名找到它自己的外框。 */
const credentialRow = (root: ParentNode, label: string) =>
  [...root.querySelectorAll('b')].find((b) => b.textContent === label)!.closest('div')!;

const chipText = (row: Element) => [...row.querySelectorAll('span')]
  .map((span) => span.textContent).filter((text) => ['需要', '已配置', '接不进来', '不需要', '可选'].includes(text!));

it('每个站说清自己的处境：需要、已配置、接不进来、不需要', async () => {
  const { host } = await open({ creds: CREDENTIAL_CAST }, { tab: 'source' });
  expect(['Fanbox', 'Patreon', 'OnlyFans', 'Kemono'].map((label) => chipText(credentialRow(host, label))))
    .toEqual([['需要'], ['已配置'], ['接不进来'], ['不需要']]);
  expect(host.textContent).toContain('1 个待配置');
});

it('缺什么、为什么要、去哪儿取都写在那一行上，非配不可的一进来就展开', async () => {
  const { host } = await open({ creds: CREDENTIAL_CAST }, { tab: 'source' });
  const fanbox = credentialRow(host, 'Fanbox');
  expect(fanbox.textContent).toContain('缺 FANBOXSESSID、cf_clearance');
  expect(fanbox.textContent).toContain('会员内容要登录后才看得到。');
  expect(fanbox.textContent).toContain('从浏览器开发者工具里复制。');
  expect([...fanbox.querySelectorAll('a')].find((a) => a.textContent?.includes('去取'))?.getAttribute('href'))
    .toBe('https://www.fanbox.cc/');
  expect(fanbox.querySelector('details')?.open).toBe(true);
  expect(fanbox.querySelector('summary')?.textContent).toContain('填写凭据');

  const patreon = credentialRow(host, 'Patreon');
  expect(patreon.querySelector('details')?.open).toBe(false);
  expect(patreon.querySelector('summary')?.textContent).toContain('修改凭据');
  // 接不进来的站没有表单可填，只说为什么。
  const blocked = credentialRow(host, 'OnlyFans');
  expect(blocked.querySelector('details')).toBeNull();
  expect(blocked.textContent).toContain('站点要求设备指纹，接不进来。');
});

it('凭据填在页面上，保存后输入框清空，空着点保存会被拦下', async () => {
  const { host, fetcher, props } = await open({ creds: CREDENTIAL_CAST }, { tab: 'source' });
  const fanbox = credentialRow(host, 'Fanbox');
  const fields = [...fanbox.querySelectorAll<HTMLInputElement>('input[type="password"]')];
  expect(fields).toHaveLength(2);

  await click(buttonNamed('保存配置', fanbox));
  expect(fanbox.textContent).toContain('没有填写内容');
  expect(sentBody(fetcher, FOLLOW_CREDENTIAL_URL)).toEqual([]);

  await type(fields[0], '  secret  ');
  await click(buttonNamed('保存配置', fanbox));
  await settle();
  expect(sentBody(fetcher, FOLLOW_CREDENTIAL_URL))
    .toEqual([{ provider: 'fanbox', values: { FANBOXSESSID: 'secret' } }]);
  expect(fields[0]!.value).toBe('');
  expect(props.toast).toHaveBeenCalledWith('已保存来源凭据');
  // 已经配好的那一行才给「清除」。
  expect(buttonNamed('清除', fanbox)).toBeNull();
  expect(buttonNamed('清除', credentialRow(host, 'Patreon'))).not.toBeNull();
});

it('凭据存在哪、权限过宽的警告跟在列表后面常驻', async () => {
  const { host } = await open({ creds: CREDENTIAL_CAST }, { tab: 'source' });
  expect(host.textContent).toContain('能登录那台电脑的人都能打开');
  expect(credentialRow(host, 'Patreon').textContent).toContain('凭据文件权限过宽');
  const storage = [...host.querySelectorAll('b')].find((b) => b.textContent === '这些账号信息存在哪里')!;
  const lastRow = credentialRow(host, 'Kemono');
  expect(lastRow.compareDocumentPosition(storage) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});
