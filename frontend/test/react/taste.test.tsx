/* 口味页的行为：两套证据怎么切、换范围时那一屏还在不在、后台那一趟什么时候算数、
 * 导入与移除各自走哪条路、点名次交回去的是什么。
 *
 * 外观（雷达图的网格、热力格的浓度档）是设计决定，由 `frontend/e2e/design.test.ts` 读
 * `getComputedStyle` 断言；这里只看结构、文字与请求。 */
import { act } from 'react';
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import * as legacyUi from '@peach/legacy/ui';

import { queryClient } from '../../src/react/query';
import {
  DEFAULT_WINDOW, prefetchTaste, RUNNING_POLL_MS, TASTE_IMPORT_URL, TASTE_REFRESH_URL,
  TASTE_SOURCE_URL, TASTE_URL, type TasteData, type TasteJob,
} from '../../src/react/taste/taste';
import { TastePage } from '../../src/react/taste/taste-page';

import { choose, click, mountRoot, settle } from './render';

// 客户端是模块级的单例（所有 React 根共用一个），用例之间不清就互相喂数据。
afterEach(() => queryClient.clear());

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，假时钟推不动它：推完时钟
   断言到的还是上一帧的 DOM。用例里改成当场派发。 */
notifyManager.setScheduler((notify) => notify());

const payload = (overrides: Partial<TasteData> = {}): TasteData => ({
  summary: {
    history_visits: 900, history_sources: 2, peach_items: 24, peach_seconds: 7200,
    liked: 6, disliked: 1, range_start: '2026-01-01', range_end: '2026-09-01',
  },
  coverage: { tagged: 18, identified: 12, untagged: 6, unidentified: 12 },
  rankings: {
    browser_categories: [
      { name: '维度甲', score: 40 }, { name: '维度乙', score: 25 }, { name: '维度丙', score: 10 },
    ],
    browser_tags: [
      { name: '标签甲', web_visits: 12, peach_items: 3 },
      { name: '标签乙', web_visits: 5, peach_items: 0 },
    ],
    browser_creators: [{ name: '创作者甲', web_visits: 8, peach_items: 2, source_domain: 'example.com' }],
    domains: [{ name: 'example.com', visits: 30 }],
    peach_tags: [{ name: '标签丁', score: 9, peach_items: 4 }],
    peach_creators: [],
    peach_performers: [],
  },
  gaps: [{ name: '候选甲', web_visits: 4 }],
  sources: [
    { source_key: 'a1', browser: 'chrome', profile: '桌面 Chrome', host: 'desk', visits: 120 },
    { source_key: 'b2', browser: 'browserexport', profile: '手机 Firefox', host: 'phone', visits: 30 },
  ],
  analysis: {
    headline: '口味集中在两个维度上',
    confidence: { level: 'medium', label: '中等把握' },
    points: [{ label: '主维度', text: '维度甲' }],
    explore: [{ tag: '标签丙', title: '探索标签丙', detail: '浏览里出现过' }],
    next_steps: [{ route: '/review', title: '去复核', detail: '补齐身份' }],
  },
  activity: { timezone: 'Asia/Shanghai', days: [{ date: '2026-09-01', count: 3 }], hours: [{ weekday: 0, hour: 21, count: 5 }] },
  creator_flows: [{ source: 'example.com', target: '创作者甲', value: 6 }],
  storage: { exports: 2, bytes: 1048576 },
  window: 'all',
  updated_at: '2026-09-10T00:00:00Z',
  ...overrides,
});

/** 遗留层交出来的那几个能力，换成可辨认的最小实现。 */
const legacyProps = () => ({
  onSignal: vi.fn<(kind: string, name: string) => void>(),
  navigate: vi.fn<(route: string) => void>(),
  toast: vi.fn<(message: string) => void>(),
  avatarInner: (name: string) => `<b>${name.slice(0, 1)}</b>`,
  onboarding: false,
});

/** 这一份永不回来：换范围时用它把「上一份还在不在」问清楚。 */
const HOLD = 'hold' as const;
type TasteReply = TasteData | null | typeof HOLD;

interface Plan {
  taste?: TasteReply[];
  job?: TasteJob[];
  imported?: { dashboard: TasteData };
  removed?: { removed: number; dashboard: TasteData };
}

const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body });

/** 按端点分流的假 fetch：每个端点各有自己的队列，最后一份之后一直回它。 */
function serve(plan: Plan) {
  const tastes = [...(plan.taste ?? [payload()])];
  const jobs = [...(plan.job ?? [{ status: 'idle' } as TasteJob])];
  const next = <T,>(queue: T[]): T => (queue.length > 1 ? queue.shift()! : queue[0]!);
  const fetcher = vi.fn(async (input: string, init?: RequestInit) => {
    if (input === TASTE_IMPORT_URL) return ok(plan.imported ?? { dashboard: payload() });
    if (input === TASTE_SOURCE_URL) return ok(plan.removed ?? { removed: 1, dashboard: payload() });
    if (input === TASTE_REFRESH_URL) return ok(next(jobs));
    if (input.startsWith(TASTE_URL)) {
      const reply = next(tastes);
      if (reply === HOLD) return new Promise<never>(() => {});
      return reply
        ? ok(reply)
        : { ok: false, status: 500, json: async () => ({ message: '账本当前只能浏览' }) };
    }
    throw new Error(`没有安排这个端点：${input}${init?.method ? ` ${init.method}` : ''}`);
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

type Fetcher = ReturnType<typeof serve>;

const tasteGets = (fetcher: Fetcher) =>
  fetcher.mock.calls.filter(([input]) => String(input).startsWith(`${TASTE_URL}?`));

const callTo = (fetcher: Fetcher, url: string) =>
  fetcher.mock.calls.filter(([input]) => String(input) === url);

/** 走完真实的首屏路径：先 prefetch 落进缓存，再挂载。 */
async function open(plan: Plan = {}, props = legacyProps()) {
  const fetcher = serve(plan);
  await prefetchTaste(DEFAULT_WINDOW, new AbortController().signal).catch(() => {});
  const mounted = await mountRoot(
    <QueryClientProvider client={queryClient}><TastePage {...props} /></QueryClientProvider>);
  await settle();
  return { fetcher, props, ...mounted };
}

/** 轮询是组件里的定时器，推进时钟会引起重画，得在 act 里推。 */
const tick = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms) });

/** 按可见文字找那一枚控件。名次行与线索行都是整行一个按钮。 */
const rowNamed = (root: ParentNode, text: string) =>
  [...root.querySelectorAll('button')].find((button) => button.textContent?.includes(text)) ?? null;

/** 原生文件框在 happy-dom 里点不出 change：直接把选中的文件放上去再派发。 */
const choosePeachFile = (input: HTMLInputElement, chosen: File) => act(async () => {
  Object.defineProperty(input, 'files', { configurable: true, value: [chosen] });
  input.dispatchEvent(new Event('change', { bubbles: true }));
});

it('首屏读 prefetch 落进缓存的那一份，两套证据是页签不是并排', async () => {
  const { fetcher, host } = await open();
  expect(tasteGets(fetcher)).toHaveLength(1);
  expect(tasteGets(fetcher)[0]?.[0]).toBe(`${TASTE_URL}?window=all`);
  expect([...host.querySelectorAll('[role=tab]')].map((tab) => tab.textContent).slice(0, 2))
    .toEqual(['浏览器记录', 'Peach 内部']);
  expect(host.textContent).toContain('900');
  expect(host.textContent).not.toContain('个作品有内部行为证据');
});

it('换分析范围时留住上一份：这一屏不退回等待态，只等新的数回来', async () => {
  const { fetcher, host } = await open({ taste: [payload(), HOLD] });
  await choose(host.querySelector('[aria-haspopup="listbox"]'), '最近 7 天');
  await settle();
  expect(tasteGets(fetcher).map(([input]) => String(input)))
    .toEqual([`${TASTE_URL}?window=all`, `${TASTE_URL}?window=7d`]);
  // 上一份仍在屏幕上：读数、页签和名次都还读得到，没有退回「读取失败」。
  expect(host.textContent).toContain('900');
  expect(rowNamed(host, '标签甲')).not.toBeNull();
  expect(host.querySelector('[role=alert]')).toBeNull();
});

it('首屏读到的旧终态不冒充新结果：不发回执，也不重取 dashboard', async () => {
  const { fetcher, props, host } = await open({ job: [{ status: 'complete' }] });
  expect(props.toast).not.toHaveBeenCalled();
  expect(tasteGets(fetcher)).toHaveLength(1);
  expect(host.querySelector('[role=alert]')).toBeNull();
});

it('本次亲眼见过它在跑，跑完才发回执并重取 dashboard', async () => {
  vi.useFakeTimers();
  const { fetcher, props, host } = await open({
    job: [{ status: 'running', message: '正在读取浏览记录' }, { status: 'complete' }],
  });
  expect(host.textContent).toContain('正在读取浏览记录');
  await tick(RUNNING_POLL_MS);
  await settle();
  expect(props.toast.mock.calls).toEqual([['已更新口味分析']]);
  expect(tasteGets(fetcher).length).toBeGreaterThan(1);
});

it('导入按 octet-stream 发原文件，文件名走请求头，回来的那一份直接换进「全部时间」', async () => {
  const { fetcher, props, host } = await open({
    imported: { dashboard: payload({ summary: { history_visits: 4321, history_sources: 3 } }) },
  });
  const input = host.querySelector<HTMLInputElement>('input[type=file]')!;
  await choosePeachFile(input, new File(['x'], '历史.zip'));
  await settle();
  const sent = callTo(fetcher, TASTE_IMPORT_URL);
  expect(sent).toHaveLength(1);
  const init = sent[0]?.[1];
  const headers = init?.headers as Record<string, string>;
  expect(init?.method).toBe('POST');
  expect(headers['Content-Type']).toBe('application/octet-stream');
  expect(headers['X-Peach-Filename']).toBe(encodeURIComponent('历史.zip'));
  expect(props.toast.mock.calls).toEqual([['已导入口味数据']]);
  // 换进缓存就够了，不为一次导入再问一遍 `/api/taste`。
  expect(host.textContent).toContain('4,321');
  expect(tasteGets(fetcher)).toHaveLength(1);
});

it('移除数据源用回来的那一份就地换掉，不为一次移除重取整页', async () => {
  const modal = vi.spyOn(legacyUi, 'confirmModal').mockImplementation(async (options) => {
    await options.onConfirm?.();
    return { confirmed: true };
  });
  const rest = payload({
    sources: [{ source_key: 'b2', browser: 'browserexport', profile: '手机 Firefox', host: 'phone', visits: 30 }],
  });
  const { fetcher, props, host } = await open({ removed: { removed: 1, dashboard: rest } });
  expect(host.textContent).toContain('桌面 Chrome');
  await click(host.querySelector('[aria-label="移除 桌面 Chrome"]'));
  await settle();
  expect(modal).toHaveBeenCalledTimes(1);
  const sent = callTo(fetcher, TASTE_SOURCE_URL);
  expect(sent).toHaveLength(1);
  expect(JSON.parse(String(sent[0]?.[1]?.body)))
    .toEqual({ operation: 'remove', source_key: 'a1', window: 'all' });
  expect(props.toast.mock.calls).toEqual([['已移除口味数据源']]);
  expect(host.textContent).not.toContain('桌面 Chrome');
  expect(tasteGets(fetcher)).toHaveLength(1);
});

it('馆藏里有对应条目的名次才点得动，点了把信号交回给壳，页面自己不跳转', async () => {
  const { props, host } = await open();
  expect(rowNamed(host, '标签乙')).toBeNull();
  await click(rowNamed(host, '标签甲'));
  expect(props.onSignal.mock.calls).toEqual([['tag', '标签甲']]);
  expect(props.navigate).not.toHaveBeenCalled();
});

it('口味总结那几条各走各的出口：探索交信号，下一步交路由', async () => {
  const { props, host } = await open();
  await click(rowNamed(host, '探索标签丙'));
  expect(props.onSignal.mock.calls).toEqual([['tag', '标签丙']]);
  await click(rowNamed(host, '去复核'));
  expect(props.navigate.mock.calls).toEqual([['/review']]);
});

it('卸载之后不再敲库：后台那一趟的轮询跟着这棵根走', async () => {
  vi.useFakeTimers();
  const { fetcher, unmount } = await open();
  const before = fetcher.mock.calls.length;
  await unmount();
  await vi.advanceTimersByTimeAsync(60_000);
  expect(fetcher.mock.calls.length, '卸载之后还在取数').toBe(before);
});
