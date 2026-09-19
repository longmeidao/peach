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

/** 按给定的一份 `/api/library-processing` 打开某一页：演示库里那趟任务早就跑完了，
 *  而运行态和失败态正是这两条要看的东西。字段以 `src/peach/web_library_processing.py` 为准。 */
async function openProcessing(
  browser: Browser, path: string, job: Record<string, unknown>,
): Promise<Visit> {
  const opened = await visit(browser, path, DESKTOP);
  await opened.page.route('**/api/library-processing', (route) => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(job),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  return opened;
}

/** 打开目录并等到读数与卡片一起替下首屏骨架。 */
async function openCatalog(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/', DESKTOP);
  await opened.page.locator('#count [data-count-readout]').waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

interface CatalogFixture {
  total: number;
  items: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

/** 从演示库取一份能完整渲染的真实目录响应，只替换当前判据需要的字段。 */
async function openCatalogFixture(
  browser: Browser,
  change: (payload: CatalogFixture, url: URL) => void,
): Promise<Visit> {
  const opened = await visit(browser, '/', DESKTOP);
  let baseline: CatalogFixture | undefined;
  await opened.page.route(/\/api\/items\?/, async (route) => {
    if (!baseline) {
      const response = await route.fetch();
      baseline = await response.json() as CatalogFixture;
    }
    const payload = structuredClone(baseline);
    change(payload, new URL(route.request().url()));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    });
  });
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('#count [data-count-readout]').waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** 一趟跑到一半的扫描与采集。 */
const RUNNING_JOB = { status: 'running', stage: '采集缺失资料', checked: 38, total: 100 };

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

  it('目录页那条处理横幅在跑的时候不占语气色，失败了才换成状态红并报警', { timeout: 60_000 }, async () => {
    const running = await openProcessing(browser, '/', RUNNING_JOB);
    try {
      const banner = running.page.locator('#libraryProcessingNotice [role="status"]');
      await banner.waitFor({ state: 'visible', timeout: 15_000 });
      assert.match(await banner.innerText(), /采集缺失资料 · 38 \/ 100/);
      // 一圈长度钉成 100，画出来的那一段就是百分比本身。
      assert.equal(await banner.locator('[role="progressbar"]').getAttribute('aria-valuenow'), '38');
      // 判据是「不是语气色」，不钉某一个具体的底：在跑那条走中性底，黄与红留给出事的时候。
      const tint = await banner.evaluate((element) => getComputedStyle(element).backgroundColor);
      for (const tone of ['--color-background-tertiary-error', '--color-status-yellow-background']) {
        assert.notEqual(tint, await tokenColor(running.page, '.peach-react', tone),
          '任务在跑是正在发生的事，配上状态底色就和「出事了」一个分量');
      }
    } finally {
      await running.close();
    }

    const failed = await openProcessing(browser, '/', { status: 'failed', error: '来源离线' });
    try {
      const banner = failed.page.locator('#libraryProcessingNotice [role="alert"]');
      await banner.waitFor({ state: 'visible', timeout: 15_000 });
      assert.equal(
        await banner.evaluate((element) => getComputedStyle(element).backgroundColor),
        await tokenColor(failed.page, '.peach-react', '--color-background-tertiary-error'));
    } finally {
      await failed.close();
    }
  });

  it('扫描卡的进度条走焦点环色，底槽是三级底，按下的那颗键转成忙态', { timeout: 60_000 }, async () => {
    const opened = await openProcessing(browser, '/data-cleanup', RUNNING_JOB);
    try {
      const card = opened.page.locator('section[aria-label="扫描与采集"]');
      await card.waitFor({ state: 'visible', timeout: 15_000 });
      const bar = card.locator('[role="progressbar"]');
      assert.equal(await bar.getAttribute('aria-valuenow'), '38');
      assert.equal(await bar.getAttribute('aria-valuemax'), '100');
      const fill = (at: number) =>
        bar.locator('rect').nth(at).evaluate((element) => getComputedStyle(element).fill);
      assert.equal(await fill(0),
        await tokenColor(opened.page, '.peach-react', '--color-background-tertiary-default'));
      assert.equal(await fill(1),
        await tokenColor(opened.page, '.peach-react', '--color-border-focus-ring'));
      // 忙态不改 `disabled`：控件仍可聚焦，重复触发由页面自己挡。
      const scan = card.getByRole('button', { name: '扫描并补全资料', exact: true });
      assert.equal(await scan.getAttribute('aria-busy'), 'true');
      assert.equal(await scan.evaluate((element) => (element as HTMLButtonElement).disabled), false,
        '用原生 disabled 挡的话按钮连焦点都拿不到');
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

  it('顶栏版式键保留两枚字形并原地换态', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      await opened.page.emulateMedia({ reducedMotion: 'no-preference' });
      const button = opened.page.locator('#density');
      const swap = button.locator('[data-icon-swap]');
      await swap.waitFor({ timeout: 5_000 });
      assert.equal(await swap.locator('[data-icon]').count(), 2);
      const before = await swap.getAttribute('data-icon-state');
      await swap.evaluate((element) => { element.setAttribute('data-test-identity', 'density-swap'); });
      await button.click();
      assert.notEqual(await swap.getAttribute('data-icon-state'), before,
        '按下后仍停在同一枚字形');
      assert.equal(await swap.locator('[data-icon]').count(), 2,
        '换态不应销毁其中一枚字形');
      await button.click();
      assert.equal(await swap.getAttribute('data-icon-state'), before, '第二次按下没有回到原字形');
      assert.equal(await button.locator('[data-icon-swap][data-test-identity="density-swap"]').count(), 1,
        '两次换态之间重建了字形容器');
    } finally {
      await opened.close();
    }
  });

  it('读数首次静态落笔，变值时每一位都有有效动画', { timeout: 60_000 }, async () => {
    const opened = await openCatalogFixture(browser, (payload, url) => {
      payload.total = url.searchParams.has('q') ? 34 : 12;
    });
    try {
      await opened.page.emulateMedia({ reducedMotion: 'no-preference' });
      const result = await opened.page.evaluate(async () => {
        const { popCount } = await import('/js/ui-components.js');
        const host = document.createElement('span');
        document.body.append(host);
        popCount(host, '12');
        const firstWasStatic = !host.firstElementChild?.classList.contains('popping');
        popCount(host, '34');
        const digit = host.querySelector<HTMLElement>('.digits.popping > span');
        const style = digit && getComputedStyle(digit);
        const answer = {
          firstWasStatic,
          animationName: style?.animationName || '',
          duration: style?.animationDuration || '',
        };
        host.remove();
        return answer;
      });
      assert.equal(result.firstWasStatic, true, '首次写入不应弹动');
      assert.equal(result.animationName, 'digit-pop-in');
      assert.equal(result.duration, '0.25s');

      const input = opened.page.locator('#q');
      await opened.page.evaluate(() => {
        document.documentElement.removeAttribute('data-count-animation');
        const count = document.querySelector('#count');
        const observer = new MutationObserver(() => {
          const digit = count?.querySelector<HTMLElement>('[data-count-readout] .digits.popping > span');
          if (!digit) return;
          const style = getComputedStyle(digit);
          document.documentElement.dataset.countAnimation = JSON.stringify({
            animationName: style.animationName,
            duration: style.animationDuration,
          });
          observer.disconnect();
        });
        observer.observe(count!, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
      });
      await input.fill('读数变值');
      await input.press('Enter');
      await opened.page.waitForFunction(() =>
        document.querySelector('#count [data-count-readout]')?.textContent?.includes('34 个符合'));
      /* 读数更新后还可能因自动续页再重画。在触发前观察真实节点，既能验收
         动画的计算值，也不把断言绑在之后某一次采样恰好撞上短暂节点。 */
      await opened.page.waitForFunction(() =>
        document.documentElement.hasAttribute('data-count-animation'), undefined, { timeout: 5_000 });
      const liveAnimation = await opened.page.evaluate(() =>
        JSON.parse(document.documentElement.dataset.countAnimation || '{}') as {
          animationName?: string; duration?: string;
        });
      assert.equal(liveAnimation.animationName, 'digit-pop-in', '真实读数节点变值后没有播放动画');
      assert.equal(liveAnimation.duration, '0.25s');
    } finally {
      await opened.close();
    }
  });

  it('五枚叠放头像只朝标题方向展开，左缘和窄卡边界不动', { timeout: 60_000 }, async () => {
    const names = Array.from({ length: 7 }, (_, index) => `演示演员 ${index + 1}`);
    const opened = await openCatalogFixture(browser, (payload) => {
      const item = payload.items[0];
      if (!item) throw new Error('演示目录没有可替换的卡片');
      item.creator = '';
      item.performers = names;
      item.performer_total = names.length;
      item.performer_entities = names.map((name, index) => ({ id: 90_000 + index, name, has_image: false }));
    });
    try {
      await opened.page.emulateMedia({ reducedMotion: 'no-preference' });
      const stack = opened.page.locator('.card[data-id] .mavstack').first();
      await stack.waitFor({ timeout: 5_000 });
      const avatars = stack.locator('.mav');
      assert.equal(await avatars.count(), 5, 'API 给七位表演者时卡片没有收在五枚以内');
      const before = await avatars.evaluateAll((items) => items.map((item) => item.getBoundingClientRect().x));
      const left = (await stack.boundingBox())!.x;

      await avatars.first().hover();
      await opened.page.waitForTimeout(320);
      const firstSpread = await avatars.evaluateAll((items) => items.map((item) => item.getBoundingClientRect().x));
      for (let index = 1; index < firstSpread.length; index += 1) {
        assert.ok(firstSpread[index] > before[index], `首枚悬停时第 ${index + 1} 枚没有向标题方向展开`);
      }

      await avatars.nth(2).hover();
      await opened.page.waitForTimeout(320);
      const after = await avatars.evaluateAll((items) => items.map((item) => item.getBoundingClientRect().x));
      const card = stack.locator('xpath=ancestor::*[contains(concat(" ", normalize-space(@class), " "), " card ")]').first();
      const bounds = await card.evaluate((cardElement) => {
        const stackRect = cardElement.querySelector('.mavstack')!.getBoundingClientRect();
        const lastRect = cardElement.querySelector('.mav:last-child')!.getBoundingClientRect();
        const firstRect = cardElement.querySelector('.mav')!.getBoundingClientRect();
        const cardRect = cardElement.getBoundingClientRect();
        return {
          stackLeft: stackRect.left,
          firstRingLeft: firstRect.left - 2,
          lastRingRight: lastRect.right + 2,
          cardLeft: cardRect.left,
          cardRight: cardRect.right,
        };
      });
      assert.equal(bounds.stackLeft, left, '展开时左缘发生位移');
      // Chrome 合成层结束 transition 时会留下远小于一个物理像素的浮点残差；这里守的是
      // 头像没有发生可见位移，不把 303 与 302.9933 这种同一像素内的取整差判成布局回退。
      assert.ok(Math.abs(after[0] - before[0]) <= .5, '指向第三枚时第一枚被往左推');
      assert.ok(Math.abs(after[1] - before[1]) <= .5, '指向第三枚时第二枚被往左推');
      assert.ok(after[3] > before[3] && after[4] > before[4], '右侧邻座没有朝标题方向让开');
      assert.ok(bounds.firstRingLeft >= bounds.cardLeft - .5, '首枚放大加描边后被卡片左缘裁切');
      assert.ok(bounds.lastRingRight <= bounds.cardRight + .5, '头像展开越出卡片右缘');

      await opened.page.mouse.move(0, 0);
      await avatars.nth(2).focus();
      await opened.page.waitForTimeout(320);
      const layers = await avatars.evaluateAll((items) => items.map((item) => Number(getComputedStyle(item).zIndex)));
      assert.equal(layers[2], Math.max(...layers), '键盘焦点所在头像没有升到最高层');

      await opened.page.setViewportSize({ width: 390, height: 844 });
      const drawer = opened.page.locator('#drawer');
      if (await drawer.evaluate((element) => element.classList.contains('open'))) {
        await opened.page.locator('#scrim').evaluate((element) => (element as HTMLElement).click());
        await opened.page.waitForFunction(() => !document.querySelector('#drawer')?.classList.contains('open'));
      }
      await avatars.first().hover();
      await opened.page.waitForTimeout(320);
      const narrow = await card.evaluate((cardElement) => {
        const cardRect = cardElement.getBoundingClientRect();
        const firstRect = cardElement.querySelector('.mav')!.getBoundingClientRect();
        const lastRect = cardElement.querySelector('.mav:last-child')!.getBoundingClientRect();
        let clip: Element | null = cardElement.parentElement;
        while (clip && clip !== document.documentElement) {
          const style = getComputedStyle(clip);
          if (style.overflowX !== 'visible' || style.overflowY !== 'visible') break;
          clip = clip.parentElement;
        }
        const clipRect = (clip || document.documentElement).getBoundingClientRect();
        return {
          firstRingLeft: firstRect.left - 2,
          lastRingRight: lastRect.right + 2,
          cardLeft: cardRect.left,
          cardRight: cardRect.right,
          clipLeft: clipRect.left,
          clipRight: clipRect.right,
          viewport: document.documentElement.clientWidth,
        };
      });
      assert.ok(narrow.firstRingLeft >= Math.max(narrow.cardLeft, narrow.clipLeft) - .5,
        '390px 视口下首枚头像或描边被最近的裁切祖先截掉');
      assert.ok(narrow.lastRingRight <= Math.min(narrow.cardRight, narrow.clipRight, narrow.viewport) + .5,
        '390px 视口下展开头像越出卡片、裁切祖先或视口');
    } finally {
      await opened.close();
    }
  });

  it('搜索框从非空变空时立即清值并溶解原内容', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      await opened.page.emulateMedia({ reducedMotion: 'no-preference' });
      const input = opened.page.locator('#q');
      const text = '一段长到会在搜索框里横向滚动的内容 0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ '.repeat(4).trim();
      await input.fill(text);
      await input.evaluate((element) => {
        const field = element as HTMLInputElement;
        field.setSelectionRange(field.value.length, field.value.length);
        field.scrollLeft = field.scrollWidth;
        field.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText' }));
      });
      assert.ok(await input.evaluate((element) => (element as HTMLInputElement).scrollLeft) > 0,
        '测试内容没有真正让搜索框横向滚动');
      await input.fill('');
      const ghost = opened.page.locator('.search > .cleardissolve');
      await ghost.waitFor({ timeout: 1_000 });
      assert.equal(await input.inputValue(), '', '动画阻塞了真实输入框清空');
      assert.equal(await ghost.locator('[data-dissolve-value]').textContent(), text);
      assert.equal(await input.evaluate((element) => getComputedStyle(element, '::placeholder').opacity), '0');
      assert.match(await ghost.locator('[data-dissolve-value]').getAttribute('style') || '', /translateX\(-\d+px\)/);
      await ghost.waitFor({ state: 'detached', timeout: 2_000 });
      assert.equal(await input.evaluate((element) => element.classList.contains('dissolving')), false,
        '动画结束后仍压着输入框的溶解状态');

      await input.fill(text);
      await input.fill('');
      await opened.page.locator('.search > .cleardissolve').waitFor({ timeout: 1_000 });
      await input.type('新输入');
      assert.equal(await opened.page.locator('.search > .cleardissolve').count(), 0,
        '清空后继续输入仍被旧残影覆盖');
      assert.equal(await input.inputValue(), '新输入');

      await input.fill('输入法候选');
      await input.fill('');
      await opened.page.locator('.search > .cleardissolve').waitFor({ timeout: 1_000 });
      await input.evaluate((element) => element.dispatchEvent(new CompositionEvent('compositionstart', {
        bubbles: true,
        data: '候',
      })));
      assert.equal(await opened.page.locator('.search > .cleardissolve').count(), 0,
        '输入法开始组字后旧残影仍覆盖候选字');
    } finally {
      await opened.close();
    }
  });

  it('卡片悬停反馈不在封面像素上描边', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      const card = opened.page.locator('article.card:not(.junkcard)').first();
      const picture = card.locator('.pic');
      await card.hover();
      const overlay = await picture.evaluate((element) => {
        const style = getComputedStyle(element, '::after');
        return { content: style.content, borderWidth: style.borderTopWidth };
      });
      assert.equal(overlay.content, 'none', '悬停伪元素仍覆盖在封面像素上');
      assert.equal(overlay.borderWidth, '0px', '悬停边线仍污染圆角边缘像素');
      assert.equal(await card.locator('.later-tools').evaluate(
        (element) => getComputedStyle(element).opacity), '1', '移除描边后没有保留悬停反馈');
    } finally {
      await opened.close();
    }
  });

  it('抬起与推开只属于作品卡的共演头像', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      await opened.page.emulateMedia({ reducedMotion: 'no-preference' });
      for (const selector of ['#tiers .av', '#tiers .brandpill']) {
        const entry = opened.page.locator(selector).first();
        if (!await entry.count()) continue;
        await entry.hover();
        await opened.page.waitForTimeout(320);
        assert.equal(await entry.evaluate((element) => getComputedStyle(element).transform), 'none',
          `${selector} 仍套用了作品共演头像的抬起效果`);
      }
    } finally {
      await opened.close();
    }
  });

  it('视频卡整块是入口且内部链接保持独立', { timeout: 60_000 }, async () => {
    const opened = await openCatalogFixture(browser, (payload) => {
      payload.items[0] = { ...payload.items[0], tags: ['演示标签'] };
    });
    try {
      const card = opened.page.locator('article.card[data-id]').first();
      const opener = card.locator('.cardopenhit');
      const boxes = await Promise.all([card.boundingBox(), opener.boundingBox()]);
      assert.deepEqual(boxes[1], boxes[0], '全卡入口没有覆盖图片、文字与卡内空白');
      await card.hover();
      assert.notEqual(await card.evaluate((element) => getComputedStyle(element).backgroundColor),
        'rgba(0, 0, 0, 0)', '悬停整卡没有灰色反馈');

      await opened.page.setViewportSize({ width: 390, height: 844 });
      const narrow = await Promise.all([card.boundingBox(), opener.boundingBox()]);
      assert.deepEqual(narrow[1], narrow[0], '390px 下全卡入口没有覆盖完整卡片');
      assert.ok((narrow[0]?.x || 0) >= 0 && (narrow[0]?.x || 0) + (narrow[0]?.width || 0) <= 390,
        '390px 下视频卡越出视口');

      const nested = card.locator('.tg:not(:disabled)').first();
      const tag = await nested.getAttribute('data-tag');
      assert.ok(tag, '演示卡没有可操作的内部标签');
      await nested.focus();
      assert.equal(await nested.evaluate((element) => element.matches(':focus-visible')), true,
        '卡内链接不能用键盘聚焦');
      await nested.press('Enter');
      await opened.page.waitForURL((url) => url.searchParams.get('tag') === tag, { timeout: 10_000 });
      assert.doesNotMatch(opened.page.url(), /\/item\//, '卡内链接冒泡打开了视频');
    } finally {
      await opened.close();
    }
  });
});
