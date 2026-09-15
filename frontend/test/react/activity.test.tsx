/* 活动页的行为：三段怎么分、轮询多久一次、失败时留下什么。
 *
 * 外观（状态徽章的三档颜色、失败卡的框线）是设计决定，由 `frontend/e2e/design.test.ts`
 * 读 `getComputedStyle` 断言；这里只看结构、文字与请求。 */
import { act } from 'react';
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { ActivityPage } from '../../src/react/activity/activity-page';
import { elapsedText, prefetchTasks, summaryText, TASKS_URL } from '../../src/react/activity/tasks';
import type { ActivityData, TaskRunPayload } from '../../src/react/activity/tasks';
import { queryClient } from '../../src/react/query';

import { mount, mountRoot } from './render';

// 客户端是模块级的单例（所有 React 根共用一个），用例之间不清就互相喂数据。
afterEach(() => queryClient.clear());

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，假时钟推不动它：推完时钟
   断言到的还是上一帧的 DOM。用例里改成当场派发。 */
notifyManager.setScheduler((notify) => notify());

const run = (overrides: Partial<TaskRunPayload> = {}): TaskRunPayload => ({
  id: 1,
  task_key: 'follow-check',
  task_label: '追更检查',
  trigger: 'manual',
  status: 'running',
  host: 'desk',
  started_at: '2026-09-11T10:00:00Z',
  finished_at: null,
  elapsed_seconds: 75,
  progress_current: 3,
  progress_total: 12,
  progress_label: '正在查第三个来源',
  result_summary: {},
  error: '',
  ...overrides,
});

const payload = (overrides: Partial<ActivityData> = {}): ActivityData => ({
  available: true, running: [], skipped: [], finished: [], ...overrides,
});

/** 依次回这几份数据，最后一份之后一直回它。`null` 那一份回 500。 */
function serve(...responses: (ActivityData | null)[]) {
  let at = 0;
  const fetcher = vi.fn(async (_input: string, _init?: RequestInit) => {
    const body = responses[Math.min(at, responses.length - 1)] ?? null;
    at += 1;
    return body
      ? { ok: true, status: 200, json: async () => body }
      : { ok: false, status: 500, json: async () => ({ message: '账本当前只能浏览' }) };
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

const page = () => <QueryClientProvider client={queryClient}><ActivityPage /></QueryClientProvider>;

/** 走完真实的首屏路径：先 prefetch 落进缓存，再挂载。 */
async function open(...responses: (ActivityData | null)[]) {
  const fetcher = serve(...responses);
  await prefetchTasks(new AbortController().signal).catch(() => {});
  return { fetcher, host: await mount(page()) };
}

const sections = (host: HTMLElement) => [...host.querySelectorAll('section')]
  .map((section) => section.querySelector('h3')?.textContent);

/** 轮询是组件里的定时器，推进时钟会引起重画，得在 act 里推。 */
const tick = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms) });

it('首屏用 prefetch 落进缓存的那一份画出来，挂载时不再请求一次', async () => {
  const { fetcher, host } = await open(payload({ running: [run()] }));
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0]?.[0]).toBe(TASKS_URL);
  expect(host.querySelector('[data-task-key=follow-check]')).not.toBeNull();
});

it('在跑的那一轮给出真实计数的进度条与已跑时长', async () => {
  const { host } = await open(payload({ running: [run()] }));
  const bar = host.querySelector('[role=progressbar]')!;
  expect(bar.getAttribute('aria-valuenow')).toBe('3');
  expect(bar.getAttribute('aria-valuemax')).toBe('12');
  expect(host.textContent).toContain('3 / 12 项');
  expect(host.textContent).toContain('已跑 1 分 15 秒');
  expect(host.querySelector('strong')?.textContent).toBe('追更检查');
});

it('总量未知时不画假进度条，只说正在做什么', async () => {
  const { host } = await open(payload({ running: [run({ progress_total: null, progress_current: null })] }));
  expect(host.querySelector('[role=progressbar]')).toBeNull();
  expect(host.querySelector('[role=status]')?.textContent).toContain('正在查第三个来源');
});

it('被挡下的那一轮单独成段，不在最近完成里再出现一次', async () => {
  const blocked = run({
    id: 7, status: 'cancelled', trigger: 'scheduled', progress_total: null,
    finished_at: '2026-09-11T10:05:00Z', elapsed_seconds: null,
    result_summary: { blocked_by: 3 }, error: '与第 3 轮（手动触发）冲突，本次跳过',
  });
  const { host } = await open(payload({ skipped: [blocked], finished: [blocked] }));
  expect(sections(host)).toEqual(['正在进行', '被挡下的']);
  expect(host.querySelectorAll('li')).toHaveLength(1);
  // 原因落在卡片底部的说明区，状态由徽章说。
  expect(host.querySelector('[data-status=cancelled]')?.textContent).toContain('与第 3 轮');
  expect(host.querySelector('[data-status=cancelled] span')?.textContent).toBe('已取消');
});

it('跑完那一轮显示摘要，失败那一轮显示原因', async () => {
  const { host } = await open(payload({ finished: [
    run({ id: 2, status: 'succeeded', finished_at: '2026-09-11T10:02:00Z',
          progress_total: null, result_summary: { checked: 7, results: [1, 2] } }),
    run({ id: 3, status: 'failed', task_label: '扫描与采集', finished_at: '2026-09-11T10:03:00Z',
          progress_total: null, error: 'RuntimeError: 上游挡回来了' }),
  ] }));
  expect(host.querySelector('[data-status=succeeded]')?.textContent).toContain('已检查 7');
  expect(host.querySelector('[data-status=failed]')?.textContent).toContain('上游挡回来了');
  expect(host.querySelector('[data-status=succeeded] span')?.textContent).toBe('已完成');
  // 跑成功那张没有说明区：没有原因可写时不留一条空条子。
  expect(host.querySelectorAll('[data-status=succeeded] p')).toHaveLength(2);
});

it('一条记录都没有时给空态，不是一片白', async () => {
  const { host } = await open(payload());
  expect(host.querySelector('h3')?.textContent).toBe('还没有任务记录');
  expect(host.querySelector('section')).toBeNull();
});

it('账本上还没有这张表时说清怎么办，不当成故障', async () => {
  const { host } = await open(payload({
    available: false, message: '账本还没有任务中心的表，执行一次 peach migrate --apply 就好' }));
  expect(host.querySelector('[role=note]')?.textContent).toContain('migrate --apply');
  expect(host.querySelector('[role=alert]')).toBeNull();
});

it('首屏取数就失败时只剩一条错误，不画空的三段', async () => {
  const { host } = await open(null);
  // 文案走遗留层的 `requestErrorMessage`：服务端给了中文原因就用它，页面不另说一遍。
  expect(host.querySelector('[role=alert]')?.textContent).toContain('账本当前只能浏览');
  expect(host.querySelector('section')).toBeNull();
});

it('轮询间隔跟着内容走：有东西在跑两秒一次，全是终态十秒一次', async () => {
  vi.useFakeTimers();
  const fetcher = serve(payload({ running: [run()] }), payload({ finished: [run({ status: 'succeeded' })] }));
  await prefetchTasks(new AbortController().signal);
  await mount(page());
  expect(fetcher).toHaveBeenCalledTimes(1);

  await tick(2000);
  expect(fetcher, '有任务在跑时两秒一次').toHaveBeenCalledTimes(2);

  // 这一份全是终态，下一轮要等十秒。
  await tick(2000);
  expect(fetcher, '没东西在跑还两秒敲一次库').toHaveBeenCalledTimes(2);
  await tick(8000);
  expect(fetcher).toHaveBeenCalledTimes(3);
});

it('一轮请求失败不擦掉上一份数据，只在页内多一条原因', async () => {
  vi.useFakeTimers();
  const fetcher = serve(payload({ finished: [run({ id: 5, status: 'succeeded', task_label: '扫描与采集' })] }), null);
  await prefetchTasks(new AbortController().signal);
  const host = await mount(page());

  await tick(10_000);
  expect(fetcher).toHaveBeenCalledTimes(2);
  expect(host.querySelector('[role=alert]')?.textContent).toContain('账本当前只能浏览');
  expect(host.textContent, '失败一次就把上一份结果擦掉，页面比原来知道得更少').toContain('扫描与采集');
});

it('卸载之后不再敲库：轮询跟着这棵根一起走', async () => {
  vi.useFakeTimers();
  const fetcher = serve(payload({ running: [run()] }));
  await prefetchTasks(new AbortController().signal);
  const mounted = await mountRoot(page());

  await tick(2000);
  expect(fetcher).toHaveBeenCalledTimes(2);
  await mounted.unmount();
  await tick(60_000);
  expect(fetcher, '卸载之后还在轮询').toHaveBeenCalledTimes(2);
});

it('时长与摘要的折算各自成立', () => {
  expect(elapsedText(0)).toBe('0 秒');
  expect(elapsedText(59)).toBe('59 秒');
  expect(elapsedText(75)).toBe('1 分 15 秒');
  expect(elapsedText(3725)).toBe('1 小时 2 分');
  expect(elapsedText(null)).toBe('');
  // 明细与「谁挡的」不进这一行：前者太长，后者已经写在错误那一句里了。
  expect(summaryText({ checked: 7, operation: 'like', rows: [1], blocked_by: 3 }))
    .toBe('已检查 7 · 操作 like');
});
