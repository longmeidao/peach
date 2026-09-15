/* 设计决定按浏览器里的计算值断言，不绑定 CSS 源码的写法。
 *
 * 页面迁到 React 时，旧的源码字符串断言按 ADR-0031 分三类：设计决定落在这里或 lint 规则，
 * 行为落在 vitest，布局与运行期问题归 `smoke.test.ts`。每条用例守一个决定，读的是
 * `getComputedStyle`，类名或样式写法换了照样成立。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Locator, Page } from 'playwright-core';

import { configurationBody, expectBody, launch, settle, visit, VIEWPORTS, type Visit } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;

/** 在 `scope` 里解析一个颜色 token：临时挂一个元素读背景色，读完就移除。 */
async function tokenColor(page: Page, scope: string, token: string): Promise<string> {
  return page.evaluate(([selector, name]) => {
    const probe = document.createElement('div');
    probe.style.backgroundColor = `var(${name})`;
    document.querySelector(selector)!.append(probe);
    const value = getComputedStyle(probe).backgroundColor;
    probe.remove();
    return value;
  }, [scope, token] as const);
}

/** 配置页「网络与访问」下的访问密码分区。演示库没有 access.json，分区处于系统口令状态。
 * 与冒烟同一口径：先等配置页主体，再 settle、再切分区。 */
async function openAccess(browser: Browser): Promise<Visit & { form: Locator }> {
  const opened = await visit(browser, '/configuration', DESKTOP);
  await expectBody(opened.page, '/configuration', configurationBody(opened.page));
  await settle(opened.page);
  await opened.page.getByRole('tab', { name: '网络与访问' }).click({ timeout: 5_000 });
  await settle(opened.page);
  const form = opened.page.locator('form[aria-label="访问密码"]');
  await form.waitFor({ timeout: 10_000 });
  return { ...opened, form };
}

/** 一轮跑完的任务。字段以 `/api/tasks`（`src/peach/routes_tasks.py`）为准。 */
const settledRun = (id: number, status: string, label: string) => ({
  id, task_key: `task-${id}`, task_label: label, trigger: 'manual', status, host: 'desk',
  started_at: '2026-09-11T10:00:00Z', finished_at: '2026-09-11T10:01:00Z', elapsed_seconds: 60,
  progress_current: null, progress_total: null, progress_label: '',
  result_summary: {}, error: status === 'failed' ? 'RuntimeError: 上游挡回来了' : '',
});

/** 活动页按给定的一份 `/api/tasks` 打开：演示库里凑不齐失败、被挡下和成功三种状态。 */
async function openActivity(browser: Browser, runs: unknown[]): Promise<Visit> {
  const opened = await visit(browser, '/activity', DESKTOP);
  await opened.page.route('**/api/tasks', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ available: true, running: [], skipped: [], finished: runs }),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('li[data-status]').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

describe('设计决定', () => {
  let browser: Browser;

  before(async () => {
    browser = await launch();
  });

  after(async () => {
    await browser.close();
  });

  it('聚焦 React 输入框只画 BoardUI 外框，旧样式表的焦点环不进来', { timeout: 60_000 }, async () => {
    const opened = await openAccess(browser);
    try {
      const input = opened.form.locator('#access-password');
      await input.focus();
      const style = await input.evaluate((element) => ({
        outline: getComputedStyle(element).outlineStyle,
        // TextField 经 GroupContext 把外框的 role 设成 presentation。
        ring: getComputedStyle(element.closest('[role="presentation"]')!).boxShadow,
      }));
      assert.equal(style.outline, 'none', '输入框自己画了 outline：旧的全局 :focus-visible 进了 React 子树');
      assert.notEqual(style.ring, 'none', '外框没有聚焦描边');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('React 子树读 BoardUI 的 token 原值，不被 board.css 的同名定值盖掉', { timeout: 60_000 }, async () => {
    const opened = await openAccess(browser);
    try {
      const shell = await opened.form.locator('#access-password').evaluate(
        (element) => getComputedStyle(element.closest('[role="presentation"]')!).backgroundColor);
      // BoardUI theme.css 浅色 neutral-200 是 #ebebeb；board.css 在 :root 上给的是 #e5e5e5。
      assert.equal(shell, 'rgb(235, 235, 235)');
      assert.equal(await tokenColor(opened.page, ':root', '--color-background-tertiary-default'), 'rgb(229, 229, 229)');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('持久警示是状态色块，不和字段说明共用灰色小字', { timeout: 60_000 }, async () => {
    const opened = await openAccess(browser);
    try {
      await opened.form.getByText('关闭访问密码，允许能连接到 Peach 的设备直接访问').click({ timeout: 5_000 });
      const note = opened.form.locator('[role="note"]');
      await note.waitFor({ timeout: 5_000 });
      const surface = await note.evaluate((element) => getComputedStyle(element).backgroundColor);
      assert.notEqual(surface, 'rgba(0, 0, 0, 0)', '警示没有底色');
      assert.equal(surface, await tokenColor(opened.page, '.peach-react', '--color-status-yellow-background'));
      const ink = await note.evaluate((element) => getComputedStyle(element).color);
      const hint = await opened.form.getByText('保存后立即生效。').evaluate((element) => getComputedStyle(element).color);
      assert.notEqual(ink, hint, '警示文字和字段说明同色');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('跑失败的那一轮整张卡框线换成 danger 色，结束原因还是正文色', { timeout: 60_000 }, async () => {
    const opened = await openActivity(browser, [
      settledRun(1, 'failed', '扫描与采集'), settledRun(2, 'succeeded', '追更检查'),
    ]);
    try {
      const danger = await tokenColor(opened.page, '.peach-react', '--color-border-error-default');
      const border = (status: string) => opened.page.locator(`li[data-status="${status}"]`)
        .evaluate((element) => getComputedStyle(element).borderTopColor);
      assert.equal(await border('failed'), danger, '失败卡的框线不是 danger 色');
      assert.notEqual(await border('succeeded'), danger, '没失败的卡也用了 danger 框线');
      // 一屏十几行里逐行读红字比看一眼哪张卡的框是红的慢：原因那行留正文色。
      const reason = await opened.page.locator('li[data-status="failed"] p').last()
        .evaluate((element) => getComputedStyle(element).color);
      assert.notEqual(reason, danger, '结束原因那行字被涂成了 danger 色');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('状态徽章只有三档颜色：成功绿、失败红、被叫停黄，其余中性', { timeout: 60_000 }, async () => {
    const opened = await openActivity(browser, [
      settledRun(1, 'succeeded', '追更检查'), settledRun(2, 'failed', '扫描与采集'),
      settledRun(3, 'cancelled', '批量操作'), settledRun(4, 'pending', '命令行批处理'),
    ]);
    try {
      const badge = (status: string) => opened.page.locator(`li[data-status="${status}"] span`).first()
        .evaluate((element) => getComputedStyle(element).backgroundColor);
      const token = (name: string) => tokenColor(opened.page, '.peach-react', name);
      assert.equal(await badge('succeeded'), await token('--color-status-lime-background'));
      assert.equal(await badge('failed'), await token('--color-status-rose-background'));
      assert.equal(await badge('cancelled'), await token('--color-status-yellow-background'));
      // 第四种状态不另给颜色：三档之外都读同一个中性底，颜色才还说得出「成功／失败／被叫停」。
      assert.equal(await badge('pending'), await token('--color-background-tertiary-default'));
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });
});
