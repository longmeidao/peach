import { afterEach, expect, it, vi } from 'vitest';
import { h, render } from 'preact';
import { act } from 'preact/test-utils';

import { Activity, elapsedText, summaryText } from '../src/islands/activity';
import type { ActivityData, TaskRunPayload } from '../src/islands/activity';

let host: HTMLDivElement;

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

const mount = async (data: ActivityData | null, error = '') => {
  host = document.createElement('div');
  document.body.append(host);
  await act(async () => render(h(Activity, { data, error, preview: true }), host));
};

afterEach(() => {
  if (host) render(null, host);
  document.body.innerHTML = '';
  vi.unstubAllGlobals();
});

it('在跑的那一轮给出真实计数的进度条与已跑时长', async () => {
  await mount(payload({ running: [run()] }));
  const bar = host.querySelector('[role=progressbar]')!;
  expect(bar.getAttribute('aria-valuenow')).toBe('3');
  expect(bar.getAttribute('aria-valuemax')).toBe('12');
  expect(host.querySelector('.activity-progress .cleanupmeta')?.textContent).toContain('3 / 12 项');
  expect(host.querySelector('.cleanupmeta')?.textContent).toContain('已跑 1 分 15 秒');
  expect(host.querySelector('.activity-run-head strong')?.textContent).toBe('追更检查');
  // 卡片是管理区那一份 Geist Fieldset，不是这一页自造的盒子。
  expect(host.querySelector('.activity-run')?.classList.contains('cleanupfieldset')).toBe(true);
});

it('总量未知时不画假进度条，只说正在做什么', async () => {
  await mount(payload({ running: [run({ progress_total: null, progress_current: null })] }));
  expect(host.querySelector('[role=progressbar]')).toBeNull();
  expect(host.textContent).toContain('正在查第三个来源');
});

it('被挡下的那一轮单独成段，说清是谁挡的', async () => {
  const blocked = run({
    id: 7, status: 'cancelled', trigger: 'scheduled', progress_total: null,
    finished_at: '2026-09-11T10:05:00Z', elapsed_seconds: null,
    result_summary: { blocked_by: 3 }, error: '与第 3 轮（手动触发）冲突，本次跳过',
  });
  await mount(payload({ skipped: [blocked], finished: [blocked] }));
  const sections = host.querySelectorAll('.activitysection');
  expect([...sections].map(section => section.querySelector('h3')?.textContent))
    .toEqual(['正在进行', '被挡下的']);
  // 原因落在 fieldset 的底部说明区，跟扫描与采集那张卡同一个位置。
  expect(host.querySelector('.geist-fieldset-footer p')?.textContent).toContain('与第 3 轮');
  expect(host.querySelector('.sbadge')?.className).toBe('sbadge paused');
  // 同一轮不在「最近完成」里再出现一次：一屏两行说的是同一件事，读起来像跑了两轮。
  expect(host.querySelectorAll('.activity-run')).toHaveLength(1);
});

it('跑完那一轮显示摘要，失败那一轮显示原因', async () => {
  await mount(payload({ finished: [
    run({ id: 2, status: 'succeeded', finished_at: '2026-09-11T10:02:00Z',
          progress_total: null, result_summary: { checked: 7, results: [1, 2] } }),
    run({ id: 3, status: 'failed', task_label: '扫描与采集', finished_at: '2026-09-11T10:03:00Z',
          progress_total: null, error: 'RuntimeError: 上游挡回来了' }),
  ] }));
  const settled = host.querySelector('[data-status=succeeded] .geist-fieldset-content')!;
  expect(settled.querySelectorAll('p')[1]?.textContent).toBe('已检查 7');
  expect(host.querySelector('[data-status=failed] .geist-fieldset-footer p')?.textContent)
    .toContain('上游挡回来了');
  expect(host.querySelector('[data-status=succeeded] .sbadge')?.textContent).toBe('已完成');
  expect(host.querySelector('[data-status=failed] .sbadge')?.className).toBe('sbadge error');
  // 跑成功那张没有说明区：没有原因可写时不留一条空条子。
  expect(host.querySelector('[data-status=succeeded] .geist-fieldset-footer')).toBeNull();
});

it('一条记录都没有时给空态，不是一片白', async () => {
  await mount(payload());
  expect(host.querySelector('[data-geist-empty-state] h3')?.textContent).toBe('还没有任务记录');
  expect(host.querySelector('.activitysection')).toBeNull();
});

it('账本上还没有这张表时说清怎么办，不当成故障', async () => {
  await mount(payload({ available: false, message: '账本还没有任务中心的表，执行一次 peach migrate --apply 就好' }));
  expect(host.querySelector('.geist-note')?.textContent).toContain('migrate --apply');
  expect(host.querySelector('.geist-note-error')).toBeNull();
});

it('首屏取数就失败时只剩一条错误，不画空的三段', async () => {
  await mount(null, '请求失败（500）');
  // 文案由遗留层的 `noteHtml` 按 500 统一成那句可操作的说明，island 不自己另说一遍。
  expect(host.querySelector('[role=alert]')?.textContent).toContain('查看托盘日志');
  expect(host.querySelector('.activitysection')).toBeNull();
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
