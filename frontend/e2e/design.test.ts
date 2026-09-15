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

/** 一条待升级的目标。字段以 `/api/quality-goals`（`src/peach/web_contract.py`）为准。 */
const qualityGoal = (id: number, name: string) => ({
  id, name, code: null, location: 'local', size: 2147483648, duration: 3725,
  reason: '只有 720p', cost: 'free', has_thumb: true, has_cover: false,
});

/** 1×1 的透明 PNG，够让 `<img>` 走完一次加载。 */
const PIXEL = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';

/** 高清版目标页按给定的一份 `/api/quality-goals` 打开：演示库里凑不齐很长的标题。 */
async function openQualityGoals(browser: Browser, items: unknown[]): Promise<Visit> {
  const opened = await visit(browser, '/quality-goals', DESKTOP);
  await opened.page.route('**/api/quality-goals?limit=200', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ total: items.length, items, offset: 0, has_more: false }),
  }));
  /* 这几条目标是造出来的，演示库里没有对应的抽帧，预览图会 404——而失败请求本身是另一
     条判据。这一条量的是封面那块的几何，给它一张能加载完的图就够。 */
  await opened.page.route('**/poster**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('li[data-goal-id]').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** 一个采集来源。字段以 `/api/scraping`（`src/peach/web_scraping.py`）为准。 */
const scrapingSource = (source: string, label: string, cookie: boolean) => ({
  source, label, login: `https://${source}.example/login`,
  accepts_cookie: cookie, network: 'peach', cookie_saved: cookie,
});

/** 来源和凭证页按给定的一份 `/api/scraping` 打开：演示库里未必同时有收 Cookie 和不收的来源。
 *
 * 站标走服务端的 `/site-mark`，而这几个来源是造出来的，那一趟必然取不到；那是另一条判据，
 * 这里给它一张能加载完的图，免得运行期问题名单里混进与本条无关的失败。 */
async function openScraping(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/scraping', DESKTOP);
  await opened.page.route('**/api/scraping', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      sources: [scrapingSource('demoa', '演示来源甲', true), scrapingSource('demob', '演示来源乙', false)],
    }),
  }));
  await opened.page.route('**/site-mark**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('form[aria-label="演示来源甲"]').waitFor({ timeout: 15_000 });
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

  it('高清版卡片的封面是 150px 宽的 16/10 方块，长标题从中间省略', { timeout: 60_000 }, async () => {
    const long = '这是一个长到必须省略才放得下的文件名，用来盯住中间截断在 React 插进来的节点上也生效.mp4';
    const opened = await openQualityGoals(browser, [
      qualityGoal(1, long), qualityGoal(2, 'short.mp4'),
    ]);
    try {
      const cover = opened.page.locator('li[data-goal-id="1"] button').first();
      const box = await cover.evaluate((element) => ({
        width: getComputedStyle(element).width,
        ratio: getComputedStyle(element).aspectRatio,
      }));
      assert.equal(box.width, '150px');
      assert.equal(box.ratio.replaceAll(' ', ''), '16/10');
      // 中间截断由 `web/js/middle-truncate.js` 的 MutationObserver 接手：React 插进来的
      // 节点不经过遗留层的渲染函数，观察器认不出它就只剩尾部省略。
      const title = opened.page.locator('li[data-goal-id="1"] h3 button');
      await title.waitFor({ timeout: 5_000 });
      await opened.page.locator('li[data-goal-id="1"] h3 button.middle-truncated')
        .waitFor({ timeout: 10_000 });
      assert.ok((await title.textContent())!.includes('…'), '长标题没有被省略');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('一张来源卡底下只有写入那一颗是主按钮，其余次级', { timeout: 60_000 }, async () => {
    const opened = await openScraping(browser);
    try {
      const card = opened.page.locator('form[aria-label="演示来源甲"]');
      const fill = (name: string) => card.getByRole('button', { name, exact: true })
        .evaluate((element) => getComputedStyle(element).backgroundColor);
      // 收 Cookie 且已存了一份的来源，底下三颗：撤销、检查、保存；只有保存是写入。
      assert.equal(await fill('保存'), await tokenColor(opened.page, '.peach-react', '--color-button-primary'));
      const secondary = await tokenColor(opened.page, '.peach-react', '--color-background-primary-default');
      assert.equal(await fill('检查连接'), secondary, '检查连接被画成了主按钮');
      assert.equal(await fill('撤销 Cookie'), secondary, '撤销 Cookie 被画成了主按钮');
      // 没存过 Cookie 的来源没有可撤的对象，那一颗不画。
      const plain = opened.page.locator('form[aria-label="演示来源乙"]');
      assert.equal(await plain.getByRole('button', { name: '撤销 Cookie', exact: true }).count(), 0);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('新窗口打开的来源地址两项 rel 都写：不带走会话，也不带走来处', { timeout: 60_000 }, async () => {
    const opened = await openScraping(browser);
    try {
      const link = opened.page.locator('form[aria-label="演示来源甲"] a[target="_blank"]');
      assert.equal(await link.getAttribute('href'), 'https://demoa.example/login');
      assert.equal((await link.getAttribute('rel'))!.split(/\s+/).sort().join(' '), 'noopener noreferrer');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });
});
