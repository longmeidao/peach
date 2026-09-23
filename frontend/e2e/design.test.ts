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
const MOBILE = VIEWPORTS.find((viewport) => viewport.mobile)!;

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

/** 一行等人判的元数据候选。字段以 `src/peach/web_review.py` 的 `_review_rows` 为准。 */
const REVIEW_ROW = {
  item_key: 'metadata_fields:ABC-123:studio',
  field: 'studio',
  field_label: '厂牌',
  code: 'ABC-123',
  query: 'ABC-123',
  candidates: [{ candidate_key: 'javdb:studio', source: 'javdb', display_value: '示例厂牌' }],
};

/** 人工复核页按一行造出来的队列打开：演示库里这一格未必正好有候选，而队列空了就没有卡。 */
async function openReview(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/review', DESKTOP);
  await opened.page.route('**/api/review', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      sections: { metadata_fields: [REVIEW_ROW] }, counts: { metadata_fields: 1 }, genre_tags: [],
    }),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('section[data-review-key]').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** CIE L*。一条 1px 的线看不看得见跟的是明度差，不是对比度比值：同样 1.48:1，浅色底上
 *  是一条灰线，深色底上两头的绝对亮度都贴着 0，什么都看不出来。 */
function lightness([red, green, blue]: number[]): number {
  const linear = (channel: number) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  };
  const y = 0.2126 * linear(red!) + 0.7152 * linear(green!) + 0.0722 * linear(blue!);
  return y > 0.008856 ? 116 * Math.cbrt(y) - 16 : 903.3 * y;
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

/** 1280 的桌面视口比 `--board-content` 还窄，量不出「网格铺满、标题居中」这类差别。 */
const WIDE = { name: 'wide', width: 1600, height: 900, mobile: false };

/** 垃圾文件页。计数行由页面自己画，演示库里一条候选都没有时它照样在。 */
async function openJunk(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/junk-files', WIDE);
  await expectBody(opened.page, '/junk-files', [
    opened.page.locator('#count .collection-summary'),
    opened.page.locator('#count .junkfilters'),
  ]);
  await settle(opened.page);
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
    const url = new URL(route.request().url());
    /* `visit()` 返回时，首屏还可能在后台续取下一页。路由接管之后若先撞上 offset>0，
       那份响应本来就可能没有卡片，不能拿它当首屏基线；让旧请求原样完成，reload 后
       再以 offset=0 的响应建立夹具。 */
    if (url.searchParams.get('offset') !== '0') {
      await route.continue();
      return;
    }
    if (!baseline) {
      const response = await route.fetch();
      baseline = await response.json() as CatalogFixture;
    }
    const payload = structuredClone(baseline);
    change(payload, url);
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

/** 一趟断在半路、攒下一份长问题清单的扫描与采集：演示库里这两样都凑不出来。 */
const FAILED_JOB = {
  status: 'failed', job_id: 'one', error: '处理被中断，请检查媒体目录后重试。',
  issue_count: 347, issues_truncated: true, retryable_asset_ids: [1, 2],
  issues_log: 'C:\\peach-data\\state\\library-processing-demo.issues.jsonl',
  issue_preview: Array.from({ length: 20 }, (_, at) => ({
    asset_id: at + 1, title: `示例-${at + 1}.mp4`, path: `B:\\番号\\示例-${at + 1}.mp4`,
    message: '封面未取得：javdb：本趟采集次数已用完，再跑一次接着采；已有图片保留',
  })),
};

/** 一条关注来源。字段以 `_source_payload`（`src/peach/web_follow.py`）为准。 */
const followSource = (id: number, author: string, provider: string, label: string, status = 'ok') => ({
  id, provider: provider.toLowerCase(), provider_label: provider, ref: `ref/${id}`, label,
  url: `https://example.com/${id}`, enabled: true, last_status: status,
  last_checked_at: '2026-09-01T00:00:00Z', created_at: '2026-08-01T00:00:00Z',
  author_key: `name:${author}`, author_name: author,
});

/** 一个站的凭据状态。字段以 `/api/follow/credentials` 为准。 */
const followCredential = (provider: string, requirement: string, present: boolean, missing: string[]) => ({
  provider: provider.toLowerCase(), provider_label: provider, followable: true, requirement,
  needs: missing, fields: present ? ['cookie'] : [], missing, present,
});

/** 关注管理页按一份造好的来源与凭据打开：演示库没有关注来源，也凑不齐四种凭据处境。
 *  站标同 `openScraping`：造出来的来源取不到图标，给一张能加载完的图。 */
async function openFollowManage(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/follow-manage', DESKTOP);
  const json = (body: unknown) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  await opened.page.route('**/api/follow?limit=1', (route) => route.fulfill(json({
    sources: [
      followSource(1, 'kou', 'Kemono', 'kou · Kemono'),
      followSource(2, 'kou', 'Pawchive', 'kou · Pawchive'),
      followSource(3, 'mira', 'Kemono', 'mira · Kemono', 'error'),
    ],
    counts: { new: 0, seen: 0, saved: 0, ignored: 0 },
    author_aliases: [{ canonical_key: 'kou', canonical_name: 'kou', aliases: [{ key: 'kou_art', name: 'kou_art' }] }],
    alias_suggestions: [],
    suggestions: [],
  })));
  await opened.page.route('**/api/follow/credentials', (route) => route.fulfill(json({
    root: 'C:\\peach\\creds',
    providers: [
      followCredential('Fanbox', 'required', false, ['FANBOXSESSID']),
      followCredential('Patreon', 'optional', true, []),
      followCredential('OnlyFans', 'blocked', false, []),
      followCredential('Kemono', 'none', false, []),
    ],
  })));
  await opened.page.route('**/source-icon**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('section[aria-label="kou 的关注来源"]').waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** 切到关注管理页的另一栏。栏名后面可能挂着待配置的数目，按开头认。 */
async function followTab(opened: Visit, name: string): Promise<void> {
  await opened.page.locator('#stats').getByRole('tab', { name: new RegExp(`^${name}`) }).click({ timeout: 5_000 });
  await settle(opened.page);
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
      await opened.form.getByText('关闭访问密码', { exact: true }).click({ timeout: 5_000 });
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
      /* 计算值现在是 `oklab()`／`oklch()`，两种记法之间没法直接比字符串，所以统一在
         canvas 上取回 RGBA 再比。 */
      const surface = await banner.evaluate((element) => {
        const style = getComputedStyle(element);
        const context = document.createElement('canvas').getContext('2d')!;
        const paint = (color: string) => {
          context.clearRect(0, 0, 1, 1);
          context.fillStyle = color;
          context.fillRect(0, 0, 1, 1);
          return [...context.getImageData(0, 0, 1, 1).data];
        };
        return { tint: style.backgroundColor, line: paint(style.borderTopColor), ink: paint(style.color) };
      });
      assert.equal(surface.tint,
        await tokenColor(failed.page, '.peach-react', '--color-background-tertiary-error'));
      // 上下两条线取自己的文字色：红底上横一条中性灰线，读起来是把这一条切成了两半。
      for (const at of [0, 1, 2]) {
        assert.ok(Math.abs(surface.line[at]! - surface.ink[at]!) <= 2,
          `横幅的线没跟着语气走：线 ${surface.line} 与字 ${surface.ink} 不是同一个色`);
      }
      assert.ok(surface.line[3]! < surface.ink[3]!,
        '线和字一样实，整条读起来像三行字');
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
      const split = card.locator('[data-split-button]');
      const parts = split.locator(':scope > button');
      assert.equal(await parts.count(), 2, '拆分按钮没有保持主操作与菜单两区');
      const boxes = await parts.evaluateAll((buttons) => buttons.map((button) => {
        const rect = button.getBoundingClientRect();
        return { left: rect.left, right: rect.right, height: rect.height };
      }));
      assert.ok(Math.abs(boxes[0]!.right - boxes[1]!.left) < 0.5,
        '拆分按钮两区之间留了空隙');
      assert.equal(boxes[0]!.height, boxes[1]!.height, '拆分按钮两区高度不一致');
      const divider = await parts.nth(1).evaluate((element) => {
        const style = getComputedStyle(element, '::after');
        return { width: style.width, color: style.backgroundColor };
      });
      assert.equal(divider.width, '1px', '拆分按钮分隔线宽度不对');
      assert.notEqual(divider.color, 'rgba(0, 0, 0, 0)', '拆分按钮分隔线没有颜色');
      const base = await split.evaluate((element) => getComputedStyle(element).backgroundImage);
      for (const part of [parts.first(), parts.last()]) {
        await part.hover();
        assert.equal(await split.evaluate(
          (element) => getComputedStyle(element).backgroundImage), base,
        '拆分按钮悬停时改变了整组底色');
        assert.deepEqual(await parts.evaluateAll((buttons) => buttons.map(
          (button) => getComputedStyle(button).backgroundColor)),
        ['rgba(0, 0, 0, 0)', 'rgba(0, 0, 0, 0)'], '按钮自己仍在切换底色');
      }
    } finally {
      await opened.close();
    }
  });

  it('失败提示里重试键靠右，问题清单铺满提示并走覆盖式滚动条', { timeout: 60_000 }, async () => {
    const opened = await openProcessing(browser, '/data-cleanup', FAILED_JOB);
    try {
      const alert = opened.page.locator('#libraryProcessing [role="alert"]');
      await alert.waitFor({ state: 'visible', timeout: 15_000 });
      await alert.locator('summary').click();
      const list = alert.locator('ul');
      await list.waitFor({ state: 'visible', timeout: 5_000 });
      const geometry = await alert.evaluate((element) => {
        const note = element.getBoundingClientRect();
        const button = element.querySelector('button')!.getBoundingClientRect();
        const items = element.querySelector('ul')!;
        return {
          padding: parseFloat(getComputedStyle(element).paddingRight),
          noteRight: note.right, buttonRight: button.right,
          listRight: items.getBoundingClientRect().right,
          client: items.clientWidth, offset: items.offsetWidth,
          track: !!element.querySelector('.ovtrack'),
        };
      });
      assert.ok(geometry.noteRight - geometry.buttonRight - geometry.padding < 1,
        '重试键没有贴着提示的右内边，读起来就不是这条提示的主动作');
      assert.ok(geometry.noteRight - geometry.listRight - geometry.padding < 1,
        '问题清单没有铺满提示的宽度');
      assert.equal(geometry.client, geometry.offset, '原生滚动条还占着清单右边一列');
      assert.ok(geometry.track, '清单没有挂上全站那条覆盖式滚动条');
      /* 同一块红底上叠着三段：结论、清单、完整记录。条与条之间要看得见界，完整记录
         要退回灰字——它不是这条提示在说的事，是出事之后自己去翻的东西。 */
      const layering = await alert.evaluate((element) => {
        const context = document.createElement('canvas').getContext('2d')!;
        const paint = (color: string) => {
          context.clearRect(0, 0, 1, 1);
          context.fillStyle = color;
          context.fillRect(0, 0, 1, 1);
          return [...context.getImageData(0, 0, 1, 1).data];
        };
        // `divide-y` 把线画在每条的下缘（末条除外），所以量的是第一条的下边。
        const first = element.querySelectorAll('li')[0]!;
        const log = element.querySelector('details p')!;
        return {
          divider: parseFloat(getComputedStyle(first).borderBottomWidth),
          dividerInk: paint(getComputedStyle(first).borderBottomColor),
          logInk: paint(getComputedStyle(log).color),
          bodyInk: paint(getComputedStyle(element).color),
        };
      });
      assert.ok(layering.divider > 0, '两条明细之间没有界，几十条连成一片');
      assert.ok(layering.dividerInk[3]! < layering.bodyInk[3]!, '条间的线和正文一样实');
      assert.ok([0, 1, 2].some((at) => Math.abs(layering.logInk[at]! - layering.bodyInk[at]!) > 8),
        '完整记录还跟着提示是红的，读起来像又出了一件事');
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
      const waitForAvatarMotion = () => stack.evaluate(async (element) => {
        const animations = element.getAnimations({ subtree: true });
        await Promise.all(animations.map((animation) => animation.finished.catch(() => undefined)));
      });

      await avatars.first().hover();
      await waitForAvatarMotion();
      const firstSpread = await avatars.evaluateAll((items) => items.map((item) => item.getBoundingClientRect().x));
      for (let index = 1; index < firstSpread.length; index += 1) {
        assert.ok(firstSpread[index] > before[index], `首枚悬停时第 ${index + 1} 枚没有向标题方向展开`);
      }

      await avatars.nth(2).hover();
      await waitForAvatarMotion();
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
      await waitForAvatarMotion();
      const layers = await avatars.evaluateAll((items) => items.map((item) => Number(getComputedStyle(item).zIndex)));
      assert.equal(layers[2], Math.max(...layers), '键盘焦点所在头像没有升到最高层');

      await opened.page.setViewportSize({ width: 390, height: 844 });
      const drawer = opened.page.locator('#drawer');
      if (await drawer.evaluate((element) => element.classList.contains('open'))) {
        await opened.page.locator('#scrim').evaluate((element) => (element as HTMLElement).click());
        await opened.page.waitForFunction(() => !document.querySelector('#drawer')?.classList.contains('open'));
      }
      await avatars.first().hover();
      await waitForAvatarMotion();
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
      // 残影节点先挂载，placeholder 再经 CSS transition 淡出；慢速 Windows runner 上
      // 两件事可能跨帧。等待过渡的最终状态，仍然守住 placeholder 必须完全不可见。
      await opened.page.waitForFunction(() => {
        const field = document.querySelector('#q');
        return field !== null && getComputedStyle(field, '::placeholder').opacity === '0';
      }, undefined, { timeout: 1_000 });
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
      assert.match(await card.evaluate((element) => getComputedStyle(element).boxShadow),
        /0px 0px 0px 8px/, '悬停底色没有在卡片四周向外多铺 8px');
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

  it('390px 下教程浮窗不压住 Toast 和批量选择条', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', MOBILE);
    try {
      await opened.page.evaluate(() => {
        localStorage.setItem('peach.post-setup-tutorial.v1', 'pending');
        localStorage.removeItem('peach.post-setup-tutorial-collapsed.v1');
        localStorage.removeItem('peach.post-setup-tutorial-skipped.v1');
      });
      await opened.page.reload({ waitUntil: 'load' });
      const card = opened.page.locator('#postSetupTutorial .post-setup-notification');
      await card.waitFor({ state: 'visible', timeout: 20_000 });
      /* 回执和批量条平时不在 DOM 里，用它们各自的正式类名放一份进去再量。留白按
         一枚回执算，所以演示库自己弹出来的那几枚先清掉，量的才是这条判据。 */
      await opened.page.evaluate(() => {
        const toasts = document.getElementById('toasts')!;
        toasts.replaceChildren();
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = '<p>已保存配置</p>';
        toasts.append(toast);
        document.getElementById('batchbar')!.hidden = false;
      });
      const tops = await opened.page.evaluate(() => {
        const top = (selector: string) => Math.min(...[...document.querySelectorAll(selector)]
          .map((node) => node.getBoundingClientRect().top));
        const card = document.querySelector('#postSetupTutorial .post-setup-notification')!
          .getBoundingClientRect();
        return { tutorial: card.top, bottom: card.bottom, left: card.left, right: card.right,
          toast: top('#toasts .toast'), dock: top('#batchbar') };
      });
      for (const [name, top] of [['Toast', tops.toast], ['批量选择条', tops.dock]] as const) {
        assert.ok(Number.isFinite(top), `${name}没有出现在页面上`);
        assert.ok(tops.bottom <= top + 1,
          `教程浮窗盖住了${name}：教程下沿 ${tops.bottom}，${name} 上沿 ${top}`);
      }
      assert.ok(tops.tutorial >= 0 && tops.left >= 0 && tops.right <= MOBILE.width,
        '教程浮窗越出了 390px 视口');
    } finally {
      await opened.close();
    }
  });

  it('复核筛选条上的下拉和按钮一样高', { timeout: 60_000 }, async () => {
    const opened = await openReview(browser);
    try {
      /* BoardUI 的 Button 和 Input 都写死 h-8／h-9，Select 的 trigger 只有内边距，
         自己撑到 28px／38px。三颗并排时那 4px 一眼就看得见。量的是整条筛选条上每一颗
         控件，而不是点名某一颗：这一排以后加什么，都得落在同一档上。 */
      const heights = await opened.page.locator('[data-review-filter]')
        .evaluate((bar) => [...bar.querySelectorAll('button')]
          .map((node) => Math.round(node.getBoundingClientRect().height)));
      assert.ok(heights.length >= 2, `筛选条上只量到 ${heights.length} 颗控件`);
      assert.deepEqual([...new Set(heights)], [heights[0]],
        `筛选条上的控件高度不齐：${heights.join(' / ')}`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('复核卡的勾选框和标题共用一条中线', { timeout: 60_000 }, async () => {
    const opened = await openReview(browser);
    try {
      /* 勾选框 16px、标题那行 24px（字段名是一枚 caption Chip）。两个高度不同的东西
         顶对顶排在一起，读的人看到的是勾选框比标题高出一截，而它们说的是同一张卡。 */
      const offset = await opened.page.locator('section[data-review-key] header').first()
        .evaluate((element) => {
          const middle = (node: Element) => {
            const box = node.getBoundingClientRect();
            return box.top + box.height / 2;
          };
          return middle(element.querySelector('label > span')!) - middle(element.querySelector('h4')!);
        });
      assert.ok(Math.abs(offset) <= 1, `勾选框比标题偏了 ${offset.toFixed(1)}px，不在同一条中线上`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('暗色下没选中的勾选框边线不比浅色下更弱', { timeout: 60_000 }, async () => {
    const opened = await openReview(browser);
    try {
      /* 这颗框的底和卡面同色，所以整个形状全靠那一圈 1px 的边说话。浅色下它是白底上的
         浅灰线，暗色下必须至少同样清楚——否则卡上看着就是「没有框」。 */
      /* 计算值是 `oklch()` 原样，解析不出通道；画进 1×1 的画布再读回来就是 RGBA。 */
      const edge = () => opened.page.locator('section[data-review-key] header label > span').first()
        .evaluate((node) => {
          const context = document.createElement('canvas').getContext('2d')!;
          const paint = (color: string) => {
            context.clearRect(0, 0, 1, 1);
            context.fillStyle = color;
            context.fillRect(0, 0, 1, 1);
            return [...context.getImageData(0, 0, 1, 1).data];
          };
          const style = getComputedStyle(node);
          return [paint(style.borderTopColor), paint(style.backgroundColor)] as const;
        });
      const [lightEdge, lightFace] = await edge();
      // `web/app.js` 的 `applyTheme('dark')` 就是这两句；这里只借它换一次配色。
      await opened.page.evaluate(() => {
        document.documentElement.dataset.theme = 'dark';
        document.documentElement.classList.add('dark');
      });
      const [darkEdge, darkFace] = await edge();
      const light = Math.abs(lightness(lightEdge) - lightness(lightFace));
      const dark = Math.abs(lightness(darkEdge) - lightness(darkFace));
      assert.ok(dark >= light,
        `暗色下边线与框内只差 ${dark.toFixed(1)} 个明度，浅色下有 ${light.toFixed(1)}`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('暗色下分隔线在两种卡面上都不比浅色更弱', { timeout: 60_000 }, async () => {
    const opened = await openReview(browser);
    try {
      /* 量的是 token 对而不是某一条线：`separator-border` 画在哪种面上由各处自己决定，
         复核卡的外框和候选块之间那条线落在 `primary`，脚注带那条落在 `secondary`。逐条去点名，
         新加一处就得记得再补一条用例，而漏补和「这处本来就没线」在屏幕上看不出区别。
         末尾再核一次复核卡自己的框线确实取的就是这个 token，免得两档都合格却根本没落到现场。 */
      const read = () => opened.page.locator('section[data-review-key]').first()
        .evaluate((node) => {
          const context = document.createElement('canvas').getContext('2d')!;
          const paint = (color: string) => {
            context.clearRect(0, 0, 1, 1);
            context.fillStyle = color;
            context.fillRect(0, 0, 1, 1);
            return [...context.getImageData(0, 0, 1, 1).data];
          };
          const style = getComputedStyle(node);
          const token = (name: string) => paint(style.getPropertyValue(name).trim());
          return {
            line: token('--color-separator-border'),
            card: token('--color-background-primary-default'),
            filled: token('--color-background-secondary-default'),
            edge: paint(style.borderTopColor),
          };
        });
      const before = await read();
      // `web/app.js` 的 `applyTheme('dark')` 就是这两句；这里只借它换一次配色。
      await opened.page.evaluate(() => {
        document.documentElement.dataset.theme = 'dark';
        document.documentElement.classList.add('dark');
      });
      const after = await read();
      for (const [face, label] of [['card', '描边卡面'], ['filled', '填充卡面']] as const) {
        const light = Math.abs(lightness(before.line) - lightness(before[face]));
        const dark = Math.abs(lightness(after.line) - lightness(after[face]));
        assert.ok(dark >= light,
          `暗色下分隔线压在${label}上只差 ${dark.toFixed(1)} 个明度，浅色下有 ${light.toFixed(1)}`);
      }
      assert.deepEqual(after.edge, after.line, '复核卡的框线没走 separator-border');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('垃圾文件的计数行是两块看得见、跟标题同宽的面', { timeout: 60_000 }, async () => {
    const opened = await openJunk(browser);
    try {
      /* 三件事一起量，它们是同一条：这一行装着摘要和分类切换两块整宽的面，横排时后者
         被挤成 0 宽；两块面和网格只要有一支不受 --board-content 约束，宽屏上标题就缩在
         中间、卡片顶着两边；浅色下 primary 就是页面底色，不换一档这两块面整个消失。 */
      const box = await opened.page.evaluate(() => {
        // 浅色是两块面最容易消失的那一档：深色下 primary 本来就比页面亮一级。
        document.documentElement.dataset.theme = 'light';
        document.documentElement.classList.remove('dark');
        const span = (selector: string) => {
          const rect = document.querySelector(selector)!.getBoundingClientRect();
          return { left: Math.round(rect.left), width: Math.round(rect.width) };
        };
        const face = (selector: string) =>
          getComputedStyle(document.querySelector(selector)!).backgroundColor;
        return {
          title: span('#manageTitle'),
          summary: span('#count .collection-summary'),
          filters: span('#count .junkfilters'),
          grid: span('#grid'),
          summaryFace: face('#count .collection-summary'),
          filtersFace: face('#count .junkfilters'),
          page: getComputedStyle(document.body).backgroundColor,
        };
      });
      assert.ok(box.filters.width > 0, '分类切换被摘要挤成 0 宽，整条在宽屏上看不见');
      for (const [label, measured] of [['摘要', box.summary], ['分类切换', box.filters],
        ['网格', box.grid]] as const) {
        assert.deepEqual(measured, box.title,
          `${label}和标题不同宽：${measured.left}+${measured.width} 对 ${box.title.left}+${box.title.width}`);
      }
      assert.notEqual(box.summaryFace, box.page, '摘要那块面和页面底色同色，整块看不见');
      assert.notEqual(box.filtersFace, box.page, '分类切换那块面和页面底色同色，整块看不见');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('垃圾文件等数据时画的仍是它自己那条计数行', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/junk-files', WIDE);
    try {
      /* 把等待态停在屏幕上：让这一页唯一那次取数挂着不回。等的只有读数，分类切换由
         URL 决定、此刻就画得出最终样子；画成目录那条的话，等待期间摆着一排这一页根本
         没有的换批与排序键，数据到货整行再换成另一种东西。 */
      await opened.page.route('**/api/ads?**', () => {});
      await opened.page.reload({ waitUntil: 'load' });
      await opened.page.locator('#count .junkfilters').waitFor({ timeout: 15_000 });
      const row = await opened.page.locator('#count').evaluate((node) => ({
        busy: node.getAttribute('aria-busy'),
        filters: node.querySelectorAll('.junkfilters a').length,
        placeholder: node.querySelectorAll('.collection-summary .countskeleton').length,
        sorts: node.querySelectorAll('.sorts').length,
      }));
      assert.equal(row.busy, 'true', '等待态没有对辅助技术公开');
      assert.ok(row.filters > 0, '等待期间这一行没有分类切换');
      assert.equal(row.placeholder, 1, '占位没有落在读数那一格');
      assert.equal(row.sorts, 0, '等待期间摆着这一页没有的排序键');
    } finally {
      await opened.close();
    }
  });

  it('关注列表工具行里的主动作、版式开关、排序框和方向键同高', { timeout: 60_000 }, async () => {
    const opened = await openFollowManage(browser);
    try {
      const page = opened.page;
      const controls = {
        检查全部: page.locator('button[aria-label="检查全部"]'),
        // 两枚图标键拼成一组，对齐的是整组的外框，不是组里单个键。
        版式开关: page.locator('[aria-label="关注列表版式"]'),
        排序框: page.locator('button[aria-label="关注列表排序"]'),
        方向键: page.locator('button[aria-label^="按检查时间"]'),
      };
      const heights: Record<string, number> = {};
      for (const [name, control] of Object.entries(controls)) {
        heights[name] = (await control.boundingBox())!.height;
      }
      assert.equal(new Set(Object.values(heights)).size, 1, `同一排控件高度不一：${JSON.stringify(heights)}`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('勾中的来源在卡片和表格里都铺 BoardUI 数据表那一档选中底色', { timeout: 60_000 }, async () => {
    const opened = await openFollowManage(browser);
    try {
      const page = opened.page;
      const selected = await tokenColor(page, '.peach-react', '--color-background-secondary-default');
      await page.getByRole('checkbox', { name: '选择 kou · Kemono' }).check({ force: true, timeout: 5_000 });
      const cardRow = page.locator('[data-source-divider] > [data-selected]');
      assert.equal(await cardRow.count(), 1);
      assert.equal(await cardRow.evaluate((row) => getComputedStyle(row).backgroundColor), selected,
        '卡片里的选中行没有铺选中底色');

      await page.locator('button[aria-label="表格视图"]').click({ timeout: 5_000 });
      const tableRow = page.locator('[data-follow-selected]');
      await tableRow.waitFor({ timeout: 5_000 });
      assert.equal(await tableRow.evaluate((row) => getComputedStyle(row).backgroundColor), selected,
        '表格里的选中行和卡片里的不是同一档');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('别名的组数是次要字色的读数，不借提醒或主按钮的颜色', { timeout: 60_000 }, async () => {
    const opened = await openFollowManage(browser);
    try {
      await followTab(opened, '添加关注');
      const count = opened.page.getByText('1 组', { exact: true });
      const look = await count.evaluate((node) => ({
        ink: getComputedStyle(node).color, face: getComputedStyle(node).backgroundColor,
      }));
      assert.equal(look.ink, await tokenColor(opened.page, '.peach-react', '--color-text-secondary'));
      assert.equal(look.face, 'rgba(0, 0, 0, 0)', '组数画成了带底色的徽章');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('凭据的四种处境四副底色：待办和完成一眼分得开', { timeout: 60_000 }, async () => {
    const opened = await openFollowManage(browser);
    try {
      await followTab(opened, '来源和凭证');
      const faces: Record<string, string> = {};
      for (const state of ['需要', '已配置', '接不进来', '不需要']) {
        faces[state] = await opened.page.getByText(state, { exact: true }).first()
          .evaluate((chip) => getComputedStyle(chip).backgroundColor);
      }
      assert.equal(new Set(Object.values(faces)).size, 4, `有两种处境同色：${JSON.stringify(faces)}`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('浅色下看片那两枚标识悬停时有底，资料卡上带订阅新作开关', { timeout: 60_000 }, async () => {
    // 演示库里没有人物实体：资料由这里给，入口与开关字段照服务端拼好下发的形状写。
    const name = '七沢みあ';
    const opened = await visit(browser, '/', DESKTOP);
    try {
      await opened.page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
        id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [],
        user_aliases: [], asset_count: 0, tags: [], related_performers: [], links: [],
        metadata: {}, has_image: false, has_avatar: false, avatar_focus: null,
        representative_asset_id: null,
        entry_links: [{ site: 'javdb', label: 'JavDB', ordinal: '', slot: 'mark',
          mark: 'mark-javdb', url: 'https://javdb.com/actors/NPD3' }],
        feed: { following: false },
      } }));
      await opened.page.goto(new URL(`/performers/${encodeURIComponent(name)}`,
        opened.page.url()).href, { waitUntil: 'load' });
      const mark = opened.page.locator('.entrymarks a.entrymark').first();
      await mark.waitFor({ timeout: 15_000 });
      await settle(opened.page);
      // 浅色下 `--hover` 与资料卡的 `--ground` 同是 #f5f5f5，垫上去等于没垫。
      await opened.page.evaluate(() => {
        document.documentElement.dataset.theme = 'light';
        document.documentElement.classList.remove('dark');
      });
      await mark.hover();
      const faces = await mark.evaluate((element) => ({
        mark: getComputedStyle(element).backgroundColor,
        card: getComputedStyle(element.closest('.entityhero')!).backgroundColor,
      }));
      assert.notEqual(faces.mark, 'rgba(0, 0, 0, 0)', '悬停没有垫底');
      assert.notEqual(faces.mark, faces.card, '悬停底色和资料卡同色，看不出来');
      const toggle = opened.page.getByRole('switch', { name: '订阅新作' });
      assert.equal(await toggle.count(), 1, '资料卡上没有订阅新作开关');
      assert.equal(await toggle.isChecked(), false);
    } finally {
      await opened.close();
    }
  });
});
