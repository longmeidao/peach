/* 设计决定按浏览器里的计算值断言，不绑定 CSS 源码的写法。
 *
 * 页面迁到 React 时，旧的源码字符串断言按 ADR-0031 分三类：设计决定落在这里或 lint 规则，
 * 行为落在 vitest，布局与运行期问题归 `smoke.test.ts`。每条用例守一个决定，读的是
 * `getComputedStyle`，类名或样式写法换了照样成立。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Locator, Page } from 'playwright-core';

import { configurationBody, expectBody, launch, layout, settle, visit, VIEWPORTS, type Visit } from './harness.ts';

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
async function openFollowManage(browser: Browser, viewport = DESKTOP): Promise<Visit> {
  const opened = await visit(browser, '/follow-manage', viewport);
  await stubFollowManage(opened.page);
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('section[aria-label="kou 的关注来源"]').waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

async function stubFollowManage(page: Page): Promise<void> {
  const json = (body: unknown) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  await page.route('**/api/follow?limit=1', (route) => route.fulfill(json({
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
  await page.route('**/api/follow/credentials', (route) => route.fulfill(json({
    root: 'C:\\peach\\creds',
    providers: [
      followCredential('Fanbox', 'required', false, ['FANBOXSESSID']),
      followCredential('Patreon', 'optional', true, []),
      followCredential('OnlyFans', 'blocked', false, []),
      followCredential('Kemono', 'none', false, []),
    ],
  })));
  await page.route('**/source-icon**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  /* 服务端的定时检查可能正在跑，那一趟会让每颗检查键挂着 aria-busy，settle 等不到头。 */
  await page.route('**/api/follow/check', (route) => (route.request().method() === 'GET'
    ? route.fulfill(json({ status: 'idle' })) : route.fallback()));
}

/** 把 `/api/` 请求挂住，直到调用返回的 `release()`：首屏骨架停在屏幕上，量完再放行。
 *  先注册的桩照常生效：放行走 `fallback()`，交给它们或真实服务端。 */
async function holdApi(page: Page): Promise<() => void> {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  await page.route((url) => url.pathname.startsWith('/api/') && url.pathname !== '/api/settings', async (route) => {
    await gate;
    await route.fallback().catch(() => {});
  });
  return release;
}

/** 一组控件此刻的长相：面色、字色、边线、圆角与外框尺寸，以及按钮组的选中标记。 */
async function controlFaces(page: Page, selectors: Record<string, string>) {
  return page.evaluate((map) => Object.fromEntries(Object.entries(map).map(([name, selector]) => {
    const node = document.querySelector(selector);
    if (!node) return [name, null];
    const style = getComputedStyle(node);
    const box = node.getBoundingClientRect();
    return [name, {
      face: `${style.backgroundColor} ${style.backgroundImage}`, ink: style.color,
      edge: `${style.borderTopWidth} ${style.borderTopColor}`, radius: style.borderTopLeftRadius,
      size: `${Math.round(box.width)}x${Math.round(box.height)}`, pressed: node.getAttribute('aria-pressed'),
    }];
  })), selectors);
}

/** 打开一位订了新作、有一排同台艺人的人物页。演示库里没有人物实体，资料照服务端下发的形状写。 */
async function openPerformer(browser: Browser, viewport = DESKTOP): Promise<Visit> {
  const name = '七沢みあ';
  const opened = await visit(browser, '/', viewport);
  const costar = (id: number, k: string) => ({ id, k, n: 1, rep: null, has_image: false, has_avatar: false, avatar_focus: null });
  await opened.page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
    id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [],
    user_aliases: [], asset_count: 0, tags: [],
    related_performers: ['本田愛华', '枢木葵', '美谷朱音', '高杉麻里', '高桥圣子', '今井夏帆'].map((k, at) => costar(90_002 + at, k)),
    links: [], metadata: {}, has_image: false, has_avatar: false, avatar_focus: null, representative_asset_id: null,
    entry_links: [
      { site: 'javdb', label: 'JavDB', ordinal: '', slot: 'mark', mark: 'mark-javdb', url: 'https://javdb.com/actors/NPD3' },
      { site: 'missav', label: 'MISSAV', ordinal: '', slot: 'mark', mark: '', url: 'https://missav.ai/actresses/x' },
    ],
    feed: { following: true },
  } }));
  await opened.page.goto(new URL(`/performers/${encodeURIComponent(name)}`, opened.page.url()).href, { waitUntil: 'load' });
  await opened.page.locator('.entryfeed').waitFor({ timeout: 15_000 });
  await opened.page.locator('.entityfoot [data-related-performer]').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  await opened.page.evaluate(() => {
    document.documentElement.dataset.theme = 'light';
    document.documentElement.classList.remove('dark');
  });
  return opened;
}

/** 有 minnano-av 资料的女优。`profile` 与 `name_groups` 照 `peach.entity_profile.header` 的形状写，
 *  出道片名故意很长：资料表那一格要单行截断。 */
const PROFILED = {
  name: '篠田ゆう',
  profile: {
    birth_date: '1991-07-21', age: 35, height: 155, bust: 86, waist: 60, hip: 87, cup: 'F',
    debut_date: '2010-12-02', debut_title: 'セキララ 〜今どき世代のゆるい性事情〜 03 はじめての撮影でとまどう素人娘の記録',
    active: { from: '2010', to: '2023' },
    tags: ['美乳', '美臀', '百合', '肛交', '巨乳', '高颜值', '苗条', '高个', '剛毛'],
  },
  name_groups: {
    reading: 'しのだゆう', shown: ['篠崎ゆう子', '高木早希', '橋本真紀'], total: 7,
    groups: [
      { label: '旧名义', names: [{ name: '篠崎ゆう子', reading: 'しのざきゆうこ' }] },
      { label: '舞ワイフ', names: [{ name: '橋本真紀' }, { name: '桧山彩音' }, { name: '篠田杏奈' }] },
      { label: 'ラグジュTV', names: [{ name: '高木早希' }] },
      { label: '其它', names: [{ name: '城田優子' }] },
    ],
  },
};

/** 打开一位有资料的女优：资料表、名字行和外链照服务端下发的形状写，主题按参数切好。 */
async function openProfiledPerformer(browser: Browser, viewport = DESKTOP, theme: 'light' | 'dark' = 'light'): Promise<Visit> {
  const opened = await visit(browser, '/', viewport);
  await opened.page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
    id: 90_101, kind: 'performer', canonical_name: PROFILED.name, aliases: ['篠崎ゆう子'], display_aliases: ['篠崎ゆう子'],
    user_aliases: [], asset_count: 42, tags: [], related_performers: [], metadata: {},
    has_image: false, has_avatar: false, avatar_focus: null, representative_asset_id: null,
    agency: { id: 90_102, canonical_name: 'New Actor eXperience', source: 'test', checked_at: '' },
    links: [
      { link_id: 90_201, link_kind: 'official', clickable: true, label: 'New Actor eXperience',
        url: 'https://official.nax-pro.com/actress/shinoda' },
      { link_id: 90_202, link_kind: 'social', clickable: true, label: 'X @shinoda_yu', url: 'https://x.com/shinoda_yu' },
    ],
    entry_links: [{ site: 'minnano-av', label: 'みんなのAV', ordinal: '', slot: 'pill', mark: 'brand-minnano',
      url: 'https://www.minnano-av.com/actress12345.html' }],
    profile: PROFILED.profile, name_groups: PROFILED.name_groups,
  } }));
  // 这几条链接是造出来的，服务端的圆标取不到；那是另一条判据，这里给一张能加载完的图。
  await opened.page.route('**/link-mark**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.goto(new URL(`/performers/${encodeURIComponent(PROFILED.name)}`, opened.page.url()).href, { waitUntil: 'load' });
  await opened.page.locator('.entityhero .entitylinks').waitFor({ timeout: 15_000 });
  await settle(opened.page);
  await opened.page.evaluate((dark) => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.classList.toggle('dark', dark);
  }, theme === 'dark');
  return opened;
}

/** 资料卡此刻的几何：身份列、资料表与卡本身的外框，以及资料表那道分隔线落在哪一边。 */
async function heroGeometry(page: Page) {
  return page.evaluate(() => {
    const rect = (selector: string) => {
      const box = document.querySelector(selector)?.getBoundingClientRect();
      return box ? { left: box.left, right: box.right, top: box.top, bottom: box.bottom } : null;
    };
    const hero = document.querySelector('.entityhero')!;
    const facts = document.querySelector('.entityfacts');
    const style = facts ? getComputedStyle(facts) : null;
    return {
      hero: rect('.entityhero'), identity: rect('.entityidentity'), facts: rect('.entityfacts'),
      heroScrolls: hero.scrollWidth > hero.clientWidth + 1,
      rule: style ? { left: style.borderLeftWidth, top: style.borderTopWidth } : null,
      labels: [...document.querySelectorAll('.entityfacts dt')].map((dt) => dt.textContent!.trim()),
    };
  });
}

/** 禁用档的三样颜色（peach-web-ui「按钮悬停只抬填充」那条）：`--surface` 底、`--border-15` 边、`--muted` 字。 */
async function disabledTokens(page: Page) {
  return {
    face: await tokenColor(page, '#main', '--surface'),
    ink: await tokenColor(page, '#main', '--muted'),
    ring: await tokenColor(page, '#main', '--border-15'),
  };
}

/** 骨架里等数据的操作键此刻的长相与状态，按文档顺序。 */
async function waitingActionFaces(page: Page, selector: string) {
  return page.locator(selector).evaluateAll((buttons) => buttons.map((button) => {
    const style = getComputedStyle(button);
    return {
      name: (button.getAttribute('aria-label') || button.textContent || '').trim(),
      disabled: (button as HTMLButtonElement).disabled, cursor: style.cursor, opacity: style.opacity,
      face: style.backgroundColor, image: style.backgroundImage, ink: style.color, ring: style.boxShadow,
      split: !!button.closest('[data-split-button]'),
    };
  }));
}

function assertDisabledFace(face: Awaited<ReturnType<typeof waitingActionFaces>>[number],
  expected: Awaited<ReturnType<typeof disabledTokens>>): void {
  assert.equal(face.disabled, true, `${face.name} 在骨架里没有禁用`);
  assert.equal(face.cursor, 'not-allowed', `${face.name} 在骨架里的光标不是禁用那一种`);
  assert.equal(face.opacity, '1', `${face.name} 的禁用态靠透明度，而不是换颜色`);
  assert.equal(face.face, expected.face, `${face.name} 在骨架里不是禁用底色`);
  assert.equal(face.image, 'none', `${face.name} 在骨架里还铺着渐变`);
  assert.equal(face.ink, expected.ink, `${face.name} 在骨架里不是禁用字色`);
  // 分体键的外圈画在整组上，两半各画一圈的话中缝会出现两道线。
  if (!face.split) assert.ok(face.ring.includes(expected.ring), `${face.name} 在骨架里没有禁用描边：${face.ring}`);
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
    } finally {
      await opened.close();
    }
  });

  it('拆分按钮两半各自抬填充：悬停哪半只有哪半变，中缝那条线不动', { timeout: 60_000 }, async () => {
    // Geist 实测（`vercel-geist-split-button.md`「悬停」）：两半各是一颗有自己底色的按钮，
    // 悬停只抬指针下那一颗；分隔线是触发档 `::before`，`left:-1px` 盖在主动作最后一列上，
    // 高度顶满、颜色不随悬停变。
    const opened = await openProcessing(browser, '/data-cleanup', { status: 'idle' });
    try {
      // 骨架那张卡同名同结构，等到 React 接管、两半不再带骨架标记才量。
      const split = opened.page.locator('section[aria-label="扫描与采集"] [data-split-button]:not(:has(> [data-skeleton-action]))');
      await split.waitFor({ state: 'visible', timeout: 15_000 });
      await settle(opened.page);
      const parts = split.locator(':scope > button');
      const faces = () => parts.evaluateAll((buttons) => buttons.map((button) => {
        const style = getComputedStyle(button), lift = getComputedStyle(button, '::before');
        return { fill: style.backgroundImage, lift: lift.opacity, ink: style.color };
      }));
      const seam = () => parts.nth(1).evaluate((element) => {
        const line = getComputedStyle(element, '::after');
        return { color: line.backgroundColor, width: line.width, left: line.left,
          height: line.height, full: `${element.getBoundingClientRect().height}px`,
          clip: getComputedStyle(element).overflowX };
      });
      assert.equal(await split.evaluate((element) => getComputedStyle(element).backgroundImage), 'none',
        '底色画在整组上，两半就没法各自抬填充');
      await opened.page.mouse.move(0, 0);
      const rest = await faces();
      assert.match(rest[0]!.fill, /gradient/, '主动作那半没有自己的蓝色填充');
      assert.equal(rest[1]!.fill, rest[0]!.fill, '两半静止时不是同一档填充');
      assert.deepEqual(rest.map((face) => face.lift), ['0', '0'], '没悬停就抬了填充');
      const line = await seam();
      assert.equal(line.width, '1px');
      assert.equal(line.left, '-1px', '分隔线该盖在主动作最后一列上，不占触发档的宽度');
      assert.equal(line.height, line.full, '分隔线没有上下顶满');
      assert.equal(line.clip, 'visible', '触发档把伸到左邻上的分隔线裁掉了，屏幕上看不见');
      assert.notEqual(line.color, 'rgba(0, 0, 0, 0)');
      for (const [at, other] of [[0, 1], [1, 0]] as const) {
        await parts.nth(at).hover();
        // 悬停层按 150ms 淡入淡出，直接读会落在半路；走到终点再比。
        await opened.page.evaluate(() => document.getAnimations().forEach((animation) => animation.finish()));
        const hovered = await faces();
        assert.equal(hovered[at]!.lift, '1', `悬停第 ${at + 1} 半没有抬填充`);
        assert.equal(hovered[other]!.lift, '0', `悬停第 ${at + 1} 半时另一半也跟着变了`);
        assert.deepEqual(hovered.map((face) => face.ink), rest.map((face) => face.ink), '悬停改了字色');
        assert.deepEqual(await seam(), line, '悬停时分隔线变了');
      }
      assert.deepEqual(opened.problems, []);
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

  it('分卷卡不翻卡、悬停走分段预览，叠层纸边和封面同一档圆角', { timeout: 60_000 }, async () => {
    /* 各卷共用同一个番号的封套，翻过去还是那张图。演示库没有分卷，给首张卡挂一个。 */
    const opened = await openCatalogFixture(browser, (payload) => {
      const [first, second] = payload.items;
      payload.items[0] = { ...first, part_group: {
        key: 'DEMO-PART', title: 'DEMO-PART', count: 2, seed_id: first.id,
        item_ids: [first.id, second.id], total_duration: 120, total_size: 1 } };
    });
    try {
      const shapeOf = (selector: string) => opened.page.locator(selector).first().evaluate((element) => {
        const stack = element.querySelector('.partstack,.mixstack')!;
        return {
          cover: getComputedStyle(element.querySelector('.pic')!).borderTopLeftRadius,
          ground: getComputedStyle(element.querySelector('.pic')!).backgroundColor,
          layers: ['::before', '::after'].map((pseudo) => getComputedStyle(stack, pseudo).borderTopLeftRadius),
          faces: element.querySelectorAll('[data-mix-faces]').length,
          preview: Boolean(element.querySelector('.previewcounter')),
        };
      });
      await opened.page.locator('article.card.partcard').first().waitFor({ timeout: 10_000 });
      const part = await shapeOf('article.card.partcard');
      assert.notEqual(part.cover, '0px', '封面没有圆角，比对失去意义');
      assert.deepEqual(part.layers, [part.cover, part.cover], '分卷卡的叠层纸边和封面不是同一档圆角');
      // 封面格背后压着纸边：格子是空的，纸边线条就从封面没盖住的地方透出来。
      assert.notEqual(part.ground, 'rgba(0, 0, 0, 0)', '叠层卡的封面格是透明的，纸边会透进封面');
      assert.equal(part.faces, 0, '分卷卡仍挂着翻卡面板');
      assert.ok(part.preview, '分卷卡悬停没有分段预览入口');
      if (await opened.page.locator('article.mixcard').count()) {
        const mix = await shapeOf('article.mixcard');
        assert.deepEqual(mix.layers, [mix.cover, mix.cover], 'Mix 卡的叠层纸边和封面不是同一档圆角');
      }
      assert.deepEqual(opened.problems, []);
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

  it('390px 下教程浮窗贴着右下角，Toast 和批量选择条盖在它上面', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', MOBILE);
    try {
      await opened.page.evaluate(() => {
        localStorage.setItem('peach.post-setup-tutorial.v1', 'pending');
        localStorage.removeItem('peach.post-setup-tutorial-collapsed.v1');
        localStorage.removeItem('peach.post-setup-tutorial-skipped.v1');
      });
      await opened.page.reload({ waitUntil: 'load' });
      /* 目录网格画出来时 paintSelection 已经按当前页收好批量条的按钮；教程卡取数期间的
         占位带 aria-busy，settle 等到的是最终那张卡。 */
      await expectBody(opened.page, '/', [
        opened.page.locator('article.card[data-id]').first(),
        opened.page.locator('#postSetupTutorial .post-setup-notification'),
      ]);
      await settle(opened.page);
      /* 回执和批量条平时不在 DOM 里，用它们各自的正式类名放一份进去，再在各自中心点
         取最上层元素。演示库自己弹出来的回执先清掉，栈里只剩这一枚。
         清空、放入和量取必须在同一次同步执行里做完：演示库刚跑完扫描，「扫描与资料采集
         已完成」的回执随状态轮询随时会到；重画网格的 paintSelection 也能在这个空当里
         把批量条收回去。 */
      const probe = await opened.page.evaluate(() => {
        const toasts = document.getElementById('toasts')!;
        toasts.replaceChildren();
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = '<p>已保存配置</p>';
        toasts.append(toast);
        const dock = document.getElementById('batchbar')!;
        dock.hidden = false;
        const tutorial = document.querySelector('#postSetupTutorial .post-setup-notification')!;
        const card = tutorial.getBoundingClientRect();
        const hit = (node: Element) => {
          const box = node.getBoundingClientRect();
          const x = box.left + box.width / 2;
          const y = box.top + box.height / 2;
          const top = document.elementFromPoint(x, y);
          return { overlaps: x >= card.left && x <= card.right && y >= card.top && y <= card.bottom,
            tutorialOnTop: !!top && tutorial.contains(top) };
        };
        return { top: card.top, bottom: card.bottom, left: card.left, right: card.right,
          toast: hit(toast), dock: hit(dock) };
      });
      assert.ok(Math.abs(probe.bottom - (MOBILE.height - 12)) <= 1,
        `教程浮窗没有贴着右下角：下沿 ${probe.bottom}，应为 ${MOBILE.height - 12}`);
      for (const [name, spot] of [['Toast', probe.toast], ['批量选择条', probe.dock]] as const) {
        assert.ok(spot.overlaps, `${name}的中心没落在教程浮窗上，这条判据没有量到重叠`);
        assert.ok(!spot.tutorialOnTop, `教程浮窗盖住了${name}`);
      }
      assert.ok(probe.top >= 0 && probe.left >= 0 && probe.right <= MOBILE.width,
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

  for (const viewport of [DESKTOP, MOBILE]) {
    it(`关注列表骨架的偏好控件和接管后同一副长相，等数据的操作键是禁用态（${viewport.name}）`, { timeout: 60_000 }, async () => {
      /* 骨架与真页面各量一遍。版式、排序和方向是这台浏览器的偏好，骨架里就是最终那一档；
         检查全部、全部收起和行尾的移除键要等名单，骨架里是禁用态，只有尺寸与接管后一致。
         窄屏上工具行收成纯图标，两边按同一条线收，尺寸也要对得上。 */
      const opened = await visit(browser, '/follow-manage', viewport);
      try {
        const page = opened.page;
        await stubFollowManage(page);
        const release = await holdApi(page);
        await page.reload({ waitUntil: 'load' });
        await page.locator('[data-skeleton="board/follow-manage"] .follow-skeleton-toolbar').waitFor({ timeout: 15_000 });
        const toolbar = '[data-skeleton] .follow-skeleton-toolbar';
        const skeleton = await controlFaces(page, {
          检查全部: `${toolbar} > button:nth-of-type(1)`,
          默认视图: `${toolbar} > [data-button-group] > button:first-child`,
          表格视图: `${toolbar} > [data-button-group] > button:last-child`,
          排序框: `${toolbar} button[aria-haspopup="listbox"]`,
          方向键: `${toolbar} > button:nth-of-type(2)`,
          全部收起: `${toolbar} > button:nth-of-type(3)`,
          移除来源: '[data-skeleton] .follow-skeleton-source > span:last-child > button:last-child',
        });
        const expected = await disabledTokens(page);
        const waiting = await waitingActionFaces(page, '[data-skeleton] [data-skeleton-action]');
        assert.ok(waiting.length >= 3, '关注列表骨架里没有标出等数据的操作键');
        for (const face of waiting) assertDisabledFace(face, expected);
        release();
        await page.locator('section[aria-label="kou 的关注来源"]').waitFor({ timeout: 15_000 });
        await settle(page);
        const final = await controlFaces(page, {
          检查全部: 'button[aria-label="检查全部"]',
          默认视图: '[aria-label="关注列表版式"] > button:first-child',
          表格视图: '[aria-label="关注列表版式"] > button:last-child',
          排序框: 'button[aria-label="关注列表排序"]',
          方向键: 'button[aria-label^="按检查时间"]',
          全部收起: 'button[aria-label="全部收起"]',
          移除来源: '[data-source-divider] > div > span:last-child > button:last-child',
        });
        const waitsForData = new Set(['检查全部', '全部收起', '移除来源']);
        for (const name of Object.keys(final)) {
          assert.ok(final[name], `接管后找不到 ${name}`);
          if (waitsForData.has(name)) {
            assert.equal(skeleton[name]!.size, final[name]!.size, `${name} 接管时尺寸跳了`);
            continue;
          }
          assert.deepEqual(skeleton[name], final[name], `${name} 在骨架里和接管后长得不一样`);
        }
        assert.equal(final['默认视图']!.pressed, 'true', '默认版式下选中的不是网格那颗');
      } finally {
        await opened.close();
      }
    });
  }

  it('数据管理骨架里等数据的操作键是禁用态，数据到了才换回蓝色主按钮', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/data-cleanup', DESKTOP);
    try {
      const page = opened.page;
      // 没有任务在跑：跑着的那一档会把扫描键压成忙碌态，那是数据不是骨架。
      await page.route('**/api/library-processing', (route) => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'idle' }),
      }));
      const release = await holdApi(page);
      await page.reload({ waitUntil: 'load' });
      await page.locator('[data-skeleton="cleanup"] .cleanupscraping [data-split-button]').waitFor({ timeout: 15_000 });
      const expected = await disabledTokens(page);
      const waiting = await waitingActionFaces(page, '[data-skeleton="cleanup"] [data-skeleton-action]');
      assert.deepEqual(waiting.map((face) => face.name),
        ['扫描并补全资料', '更多扫描与采集方式', '开始修复', '检查来源', '预览', '检查死链', '检查文件']);
      for (const face of waiting) assertDisabledFace(face, expected);
      const ring = await page.locator('[data-skeleton="cleanup"] [data-split-button]')
        .evaluate((element) => getComputedStyle(element).boxShadow);
      assert.ok(ring.includes(expected.ring), `骨架里的分体键外圈不是禁用那一档描边：${ring}`);
      const sizes = await controlFaces(page, {
        扫描并补全资料: '.cleanupscraping [data-split-button] > button:first-child',
        更多方式: '.cleanupscraping [data-split-button] > button:last-child',
        开始修复: '.cleanupmediarepair footer > button',
      });
      release();
      await page.locator('[data-skeleton="cleanup"]').waitFor({ state: 'detached', timeout: 15_000 });
      // 正式页面先摆一份同样的骨架卡，等 React 岛接管；键上没了 `data-skeleton-action` 才算接管完。
      await page.locator('.cleanupscraping [data-split-button] > button:first-child:not([data-skeleton-action])')
        .waitFor({ timeout: 15_000 });
      await page.locator('section[aria-label="媒体修复"] footer > button:not([data-skeleton-action])')
        .waitFor({ timeout: 15_000 });
      await settle(page);
      const final = await controlFaces(page, {
        扫描并补全资料: '.cleanupscraping [data-split-button] > button:first-child',
        更多方式: '.cleanupscraping [data-split-button] > button:last-child',
        开始修复: 'section[aria-label="媒体修复"] footer > button',
      });
      for (const name of Object.keys(sizes)) {
        assert.equal(sizes[name]!.size, final[name]!.size, `${name} 接管时尺寸跳了`);
        assert.match(final[name]!.face, /gradient/, `${name} 接管后没换回蓝色主按钮`);
      }
      const enabled = await page.locator('.cleanupscraping [data-split-button] > button')
        .evaluateAll((buttons) => buttons.map((button) => (button as HTMLButtonElement).disabled));
      assert.deepEqual(enabled, [false, false], '数据到了扫描键还是禁用的');
    } finally {
      await opened.close();
    }
  });

  it('骨架里的占位和按键悬停不给任何反馈，也点不中', { timeout: 120_000 }, async () => {
    const name = '七沢みあ';
    const pages: { path: string; ready: string; targets: string[]; prepare?: (page: Page) => Promise<void> }[] = [
      { path: `/performers/${encodeURIComponent(name)}`, ready: '[data-skeleton="entity/performer"] .entityfoot .avskeleton',
        targets: ['[data-skeleton] .entityfoot .avskeleton'],
        prepare: (page) => page.route(/\/api\/entity\/shapes/, (route) => route.fulfill({ json: {
          ok: true, entities: [{ id: 90_001, kind: 'performer', names: [name], parts: ['costars'] }] } })) },
      { path: '/data-cleanup', ready: '[data-skeleton="cleanup"] [data-skeleton-action]',
        targets: ['[data-skeleton] .board-plain-stat', '[data-skeleton] a[href="/scraping"]',
          '[data-skeleton] [data-skeleton-action]', '[data-skeleton] .cleanupfieldset [data-skeleton-action]'] },
      { path: '/review', ready: '[data-skeleton="review"] .reviewtabs button',
        targets: ['[data-skeleton] .reviewtabs button', '[data-skeleton] .skeletoncard'] },
      { path: '/follow', ready: '.followauthors .avskeleton',
        targets: ['.followauthors .avskeleton', '.followworks .brandskeleton', '[data-skeleton^="cards/"] > div > *'] },
      { path: '/follow-manage', ready: '[data-skeleton="board/follow-manage"] .follow-skeleton-toolbar',
        targets: ['[data-skeleton] .follow-skeleton-toolbar > button:nth-of-type(2)',
          '[data-skeleton] .follow-skeleton-toolbar > button:nth-of-type(1)'] },
    ];
    for (const { path, ready, targets, prepare } of pages) {
      const opened = await visit(browser, '/', DESKTOP);
      try {
        const page = opened.page;
        // 后登记的路由先拿到请求：桩要排在挂住 /api/ 那条之后，不然它也被挂住。
        await holdApi(page);
        await prepare?.(page);
        await page.goto(new URL(path, page.url()).href, { waitUntil: 'load' });
        await page.locator(ready).first().waitFor({ state: 'visible', timeout: 15_000 });
        for (const target of targets) {
          const node = page.locator(target).first();
          await node.waitFor({ state: 'visible', timeout: 5_000 });
          const box = (await node.boundingBox())!;
          const look = () => node.evaluate((element) => [element, ...element.querySelectorAll('*')].slice(0, 6).map((part) => {
            const style = getComputedStyle(part);
            return [style.borderColor, style.boxShadow, style.backgroundColor, style.backgroundImage,
              style.outlineStyle, style.color, style.scale, style.transform].join(' | ');
          }));
          await page.mouse.move(0, 0);
          const rest = await look();
          const [x, y] = [box.x + box.width / 2, box.y + box.height / 2];
          await page.mouse.move(x, y);
          assert.deepEqual(await look(), rest, `${path} ${target} 悬停时变了样子`);
          // 分层骨架那一排（`data-skeleton-tier`）是最终那条轨道本身，点中它等于点在页面底上；
          // 要问的是指针有没有落在某一枚占位或整块骨架里。
          const hit = await page.evaluate(([px, py]) => {
            const at = document.elementFromPoint(px!, py!);
            return { cursor: at ? getComputedStyle(at).cursor : '',
              inside: !!at?.closest('[data-skeleton],.avskeleton,.brandskeleton,.tagskeleton,.skeletoncard'),
              disabled: !!at?.closest('button:disabled') };
          }, [x, y]);
          assert.ok(['auto', 'default', 'not-allowed'].includes(hit.cursor), `${path} ${target} 悬停换了光标：${hit.cursor}`);
          assert.ok(!hit.inside || hit.disabled, `${path} ${target} 在骨架里还能点中`);
        }
      } finally {
        await opened.close();
      }
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
      const feed = opened.page.locator('.entryfeed');
      await opened.page.emulateMedia({ reducedMotion: 'no-preference' });
      assert.equal(await feed.evaluate((element) => getComputedStyle(element).animationName),
        'entryfeed-breathe', '没订的那枚图标不呼吸，一枚墨色小图标没人注意到');
      const tip = opened.page.locator('#entityFeedTip');
      assert.equal(await tip.isVisible(), false);
      await feed.hover();
      assert.equal(await tip.isVisible(), true, '悬停没有说明这枚图标是干嘛的');
      assert.match(await tip.innerText(), /JavDB/);
      const placed = await tip.evaluate((element) => {
        const box = element.getBoundingClientRect();
        return box.left >= 0 && box.right <= innerWidth && box.bottom <= innerHeight;
      });
      assert.ok(placed, '说明浮层越出了视口');
      await toggle.focus();
      await opened.page.keyboard.press('Escape');
      assert.equal(await tip.isVisible(), false, 'Escape 收不起说明浮层');
    } finally {
      await opened.close();
    }
  });

  for (const viewport of [DESKTOP, MOBILE]) {
    it(`订阅新作的说明浮层整块露在外面：不被资料卡裁掉，也不被同台艺人那条盖住（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openPerformer(browser, viewport);
      try {
        const page = opened.page;
        const feed = page.locator('.entryfeed');
        await feed.hover();
        const tip = page.locator('#entityFeedTip');
        await tip.waitFor({ state: 'visible', timeout: 5_000 });
        const placement = await tip.evaluate((element) => {
          const box = element.getBoundingClientRect();
          const clippedBy: string[] = [];
          // 顶层里的元素不受祖先 overflow 裁切，只有写在文档流里的浮层才要逐层量。
          const topLayer = element.matches(':popover-open');
          for (let node = topLayer ? null : element.parentElement; node; node = node.parentElement) {
            const style = getComputedStyle(node);
            if (style.overflowX === 'visible' && style.overflowY === 'visible') continue;
            const clip = node.getBoundingClientRect();
            if (box.left < clip.left - 0.5 || box.right > clip.right + 0.5
              || box.top < clip.top - 0.5 || box.bottom > clip.bottom + 0.5) clippedBy.push(node.className || node.tagName);
          }
          // 浮层本身不接指针；临时放开再问四条边和正中最上面是谁，盖在它上面的东西就现形了。
          // 取样点离角 16px：圆角外那一小块本来就不属于它。
          element.style.pointerEvents = 'auto';
          const [midX, midY] = [box.left + box.width / 2, box.top + box.height / 2];
          const covered = [[box.left + 16, box.top + 2], [box.right - 16, box.top + 2], [box.left + 16, box.bottom - 2],
            [box.right - 16, box.bottom - 2], [box.left + 2, midY], [box.right - 2, midY], [midX, midY]]
            .map(([x, y]) => document.elementFromPoint(x!, y!))
            .filter((hit) => !hit || !element.contains(hit)).map((hit) => hit?.className || 'null');
          element.style.pointerEvents = '';
          return { inView: box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight,
            clippedBy, covered, below: box.top >= document.querySelector('.entryfeed')!.getBoundingClientRect().bottom };
        });
        assert.ok(placement.inView, '说明浮层越出了视口');
        assert.deepEqual(placement.clippedBy, [], '说明浮层被外层容器裁掉了一截');
        assert.deepEqual(placement.covered, [], '说明浮层被别的东西盖住了');
        assert.ok(placement.below, '视口下方放得下时说明浮层应该在图标下面');
        const page_ = await layout(page);
        assert.ok(page_.scrollWidth <= page_.viewportWidth, '说明浮层把页面撑出了横向滚动');
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  // 1000px 窗口侧栏展开时内容区只剩七百来像素：三栏的判据量的是内容区，这一档要排成两层，
  // 身份那一栏不能被资料表挤到只剩一个字宽。
  for (const [viewport, stacked] of [[DESKTOP, false], [{ name: 'wide', width: 1440, height: 900, mobile: false }, false],
    [{ name: 'mid', width: 1000, height: 900, mobile: false }, true], [MOBILE, true]] as const) {
    it(`女优页头：宽屏资料表在身份信息右侧隔一道竖线，窄屏排到下面隔一道横线，整张卡不横向溢出（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openProfiledPerformer(browser, viewport);
      try {
        const geometry = await heroGeometry(opened.page);
        assert.deepEqual(geometry.labels, ['生日', '身材', '出道', '生涯', '标签'], '资料表不是那五项');
        assert.ok(geometry.facts && geometry.identity && geometry.hero, '页头缺了资料表');
        assert.ok(geometry.identity.right - geometry.identity.left >= 240, '身份那一栏被挤窄了');
        if (stacked) {
          assert.ok(geometry.facts.top >= geometry.identity.bottom - 0.5, '窄屏下资料表没有排到身份信息下面');
          assert.deepEqual(geometry.rule, { left: '0px', top: '1px' }, '窄屏下资料表该用横线和身份信息隔开');
        } else {
          assert.ok(geometry.facts.left >= geometry.identity.right - 0.5, '宽屏下资料表没有排在身份信息右侧');
          assert.deepEqual(geometry.rule, { left: '1px', top: '0px' }, '宽屏下资料表该用竖线和身份信息隔开');
        }
        assert.ok(geometry.facts.right <= geometry.hero.right + 0.5, '资料表越出了资料卡');
        assert.equal(geometry.heroScrolls, false, '资料卡里有东西被横向裁掉');
        const debut = await opened.page.locator('.entityfacts dd[title]').evaluate((dd) => ({
          title: dd.getAttribute('title'), wrap: getComputedStyle(dd).whiteSpace,
          cut: getComputedStyle(dd).textOverflow, clipped: dd.scrollWidth > dd.clientWidth,
          lines: Math.round(dd.getBoundingClientRect().height / parseFloat(getComputedStyle(dd).lineHeight)),
        }));
        assert.equal(debut.title, PROFILED.profile.debut_title, '出道那一格的 title 没给全名');
        assert.deepEqual([debut.wrap, debut.cut, debut.lines], ['nowrap', 'ellipsis', 1], '出道片名没有单行截断');
        const page_ = await layout(opened.page);
        assert.ok(page_.scrollWidth <= page_.viewportWidth, `页头把页面撑出了横向滚动：${page_.offenders.join('，')}`);
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  it('女优页头名字下面一行：视频数、事务所与读音加前三个别名，外链一律 36px 纯图标方块', { timeout: 60_000 }, async () => {
    const opened = await openProfiledPerformer(browser, DESKTOP);
    try {
      const page = opened.page;
      const line = await page.locator('.entityhero .alias').evaluate((alias) => ({
        glyphs: [...alias.querySelectorAll(':scope > .metaitem > svg use')].map((use) => use.getAttribute('href')),
        names: [...alias.querySelectorAll('.aliasnames > span')].map((span) => span.textContent!.trim()),
        more: alias.querySelector('.aliasmore')?.textContent?.trim() ?? '',
        agency: alias.querySelector('a[data-agency]')?.textContent?.trim() ?? '',
      }));
      assert.deepEqual(line.glyphs, ['#i-film', '#i-briefcase', '#i-id-card'], '名字那一行的三项不是视频、事务所、别名');
      assert.deepEqual(line.names, ['しのだゆう', '篠崎ゆう子', '高木早希', '橋本真紀'], '读音没有排在别名最前，或别名不是前三个');
      assert.equal(line.more, '+4', '「+N」数的不是剩下那几个别名');
      assert.equal(line.agency, 'New Actor eXperience');
      const links = await page.locator('.entityhero .entitylinks a').evaluateAll((anchors) => anchors.map((a) => {
        const box = a.getBoundingClientRect();
        return { size: `${Math.round(box.width)}x${Math.round(box.height)}`, cls: a.className, title: a.getAttribute('title'),
          name: a.querySelector('.sr-only')?.textContent ?? '', visibleText: a.querySelector('.entitylinklabel') !== null };
      }));
      assert.equal(links.length, 3);
      for (const link of links) {
        assert.deepEqual([link.size, link.cls, link.visibleText], ['36x36', 'iconlink', false], `${link.title} 不是纯图标方块`);
        assert.equal(link.name, link.title, `${link.title} 给读屏的名字和悬停提示不一致`);
      }
      assert.deepEqual(links.map((link) => link.title), ['みんなのAV', 'New Actor eXperience 官方资料', 'X @shinoda_yu']);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  for (const viewport of [DESKTOP, MOBILE]) {
    it(`别名的「+N」浮层进顶层按名义分组：悬停、聚焦都出，不被资料卡裁掉，Escape 收起（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openProfiledPerformer(browser, viewport);
      try {
        const page = opened.page;
        const more = page.locator('.aliasmore');
        const pop = page.locator('#entityAliasPop');
        assert.equal(await pop.isVisible(), false);
        await more.hover();
        await pop.waitFor({ state: 'visible', timeout: 5_000 });
        assert.equal(await more.getAttribute('aria-expanded'), 'true');
        const shown = await pop.evaluate((element) => {
          const box = element.getBoundingClientRect();
          return {
            topLayer: element.matches(':popover-open'),
            inView: box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight,
            title: element.querySelector('.aliaspophead')?.textContent?.trim(),
            groups: [...element.querySelectorAll('dt')].map((dt) => dt.textContent!.trim()),
            face: getComputedStyle(element).backgroundColor,
          };
        });
        assert.equal(shown.topLayer, true, '别名浮层没进顶层，会被资料卡的 overflow:hidden 裁掉');
        assert.ok(shown.inView, '别名浮层越出了视口');
        assert.equal(shown.title, '7 个别名');
        assert.deepEqual(shown.groups, ['旧名义', '舞ワイフ', 'ラグジュTV', '其它']);
        assert.notEqual(shown.face, 'rgba(0, 0, 0, 0)', '别名浮层没有底色');
        // 指针从按钮挪到浮层上读名字，浮层不能在半路收起。
        const box = (await pop.boundingBox())!;
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 4 });
        await page.waitForTimeout(300);
        assert.equal(await pop.isVisible(), true, '指针移到浮层上它就收起了');
        await page.mouse.move(1, 1);
        await pop.waitFor({ state: 'hidden', timeout: 5_000 });
        await more.focus();
        await page.keyboard.press('Tab');
        await page.keyboard.press('Shift+Tab');
        await pop.waitFor({ state: 'visible', timeout: 5_000 });
        await page.keyboard.press('Escape');
        assert.equal(await pop.isVisible(), false, 'Escape 收不起别名浮层');
        const page_ = await layout(page);
        assert.ok(page_.scrollWidth <= page_.viewportWidth, '别名浮层把页面撑出了横向滚动');
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  it('资料表的标签只列前四个，余下的收进「+N」，浮层进顶层列全部标签', { timeout: 60_000 }, async () => {
    const opened = await openProfiledPerformer(browser, DESKTOP);
    try {
      const page = opened.page;
      const cell = await page.locator('.entityfacts dd.facttags').evaluate((dd) => ({
        shown: [...dd.querySelectorAll(':scope > .facttag')].map((tag) => tag.textContent!.trim()),
        more: dd.querySelector(':scope > .factmore')?.textContent?.trim() ?? '',
      }));
      assert.deepEqual(cell.shown, PROFILED.profile.tags.slice(0, 4), '标签那一格不是前四个');
      assert.equal(cell.more, '+5', '「+N」数的不是剩下那几个标签');
      const pop = page.locator('#entityTagPop');
      assert.equal(await pop.isVisible(), false);
      await page.locator('.factmore').hover();
      await pop.waitFor({ state: 'visible', timeout: 5_000 });
      const shown = await pop.evaluate((element) => {
        const box = element.getBoundingClientRect();
        return {
          topLayer: element.matches(':popover-open'),
          inView: box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight,
          title: element.querySelector('.aliaspophead')?.textContent?.trim(),
          tags: [...element.querySelectorAll('.facttag')].map((tag) => tag.textContent!.trim()),
        };
      });
      assert.equal(shown.topLayer, true, '标签浮层没进顶层，会被资料卡的 overflow:hidden 裁掉');
      assert.ok(shown.inView, '标签浮层越出了视口');
      assert.equal(shown.title, '9 个标签');
      assert.deepEqual(shown.tags, PROFILED.profile.tags);
      await page.mouse.move(1, 1);
      await pop.waitFor({ state: 'hidden', timeout: 5_000 });
      // 点一下钉住：指针离开也不收，Escape 才收。
      await page.locator('.factmore').click();
      await page.mouse.move(1, 1);
      await page.waitForTimeout(300);
      assert.equal(await pop.isVisible(), true, '点按钉住的标签浮层指针一走就收了');
      await page.keyboard.press('Escape');
      assert.equal(await pop.isVisible(), false, 'Escape 收不起标签浮层');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('换头像的加号量在圆框上：整行比圆框高时也贴着圆框右下角', { timeout: 60_000 }, async () => {
    const opened = await openProfiledPerformer(browser, { name: 'wide', width: 1440, height: 900, mobile: false });
    try {
      const page = opened.page;
      const button = page.locator('.entityportraitwrap [data-avatar-picker] button');
      await button.waitFor({ timeout: 15_000 });
      // 行有多高看她有多少资料、别名那一行折不折；这里直接把身份列撑高，量的是加号跟不跟圆框。
      await page.addStyleTag({ content: '.entityidentity{padding-block:40px}' });
      const box = await page.evaluate(() => {
        const rect = (element: Element) => element.getBoundingClientRect();
        const wrap = rect(document.querySelector('.entityportraitwrap')!);
        const circle = rect(document.querySelector('.entityportrait')!);
        const plus = rect(document.querySelector('.entityportraitwrap [data-avatar-picker] button')!);
        return { wrap: wrap.height, circle: { right: circle.right, bottom: circle.bottom, height: circle.height },
          plus: { right: plus.right, bottom: plus.bottom } };
      });
      assert.ok(box.wrap > box.circle.height + 8, `这一行没有比圆框高，用例量不出偏移（行 ${box.wrap}，圆框 ${box.circle.height}）`);
      // Tailwind 的 `right-1 bottom-1`：按钮离圆框外框右、下各 4px。
      assert.ok(Math.abs(box.circle.bottom - box.plus.bottom - 4) < 1, `加号没有贴着圆框底边：${JSON.stringify(box)}`);
      assert.ok(Math.abs(box.circle.right - box.plus.right - 4) < 1, `加号没有贴着圆框右边：${JSON.stringify(box)}`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('女优页头深色主题：资料表与别名浮层跟着主题取墨色和浮层底', { timeout: 60_000 }, async () => {
    const opened = await openProfiledPerformer(browser, DESKTOP, 'dark');
    try {
      const page = opened.page;
      const ink = await tokenColor(page, '#main', '--ink');
      const muted = await tokenColor(page, '#main', '--muted');
      const ground = await tokenColor(page, '#main', '--ground');
      const facts = await page.locator('.entityfacts').evaluate((dl) => ({
        dd: getComputedStyle(dl.querySelector('dd')!).color, dt: getComputedStyle(dl.querySelector('dt')!).color,
      }));
      assert.equal(facts.dd, ink, '深色下资料表的值不是墨色');
      assert.equal(facts.dt, muted, '深色下资料表的项名不是次级字色');
      await page.locator('.aliasmore').hover();
      const pop = page.locator('#entityAliasPop');
      await pop.waitFor({ state: 'visible', timeout: 5_000 });
      const face = await pop.evaluate((element) => getComputedStyle(element).backgroundColor);
      assert.notEqual(face, 'rgba(0, 0, 0, 0)');
      assert.notEqual(face, 'rgb(255, 255, 255)', '深色下别名浮层还是白底');
      assert.notEqual(ground, 'rgb(255, 255, 255)', '主题没有切到深色');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('人物页同台艺人的头像悬停和首页顶栏女优头像同一副：抬整格填充、不描圈', { timeout: 60_000 }, async () => {
    const opened = await openPerformer(browser, DESKTOP);
    try {
      const page = opened.page;
      const person = page.locator('.entityfoot [data-related-performer]').first();
      const face = () => person.evaluate((element) => {
        const style = getComputedStyle(element), ring = getComputedStyle(element.querySelector('.ring')!);
        return { fill: style.backgroundColor, ink: style.color, radius: style.borderRadius, padding: style.padding,
          width: style.width, ring: ring.boxShadow, size: ring.width };
      });
      await page.mouse.move(0, 0);
      const rest = await face();
      await person.hover();
      const hovered = await face();
      // 首页那一格（board.css「首页顶部两排」）：76px 宽、6/4px 内边距、12px 圆角，悬停铺
      // primary-hover、字换主文字色，48px 圆头像不另描圈。
      const home = {
        fill: await tokenColor(page, '#main', '--color-background-primary-hover'),
        ink: await tokenColor(page, '#main', '--color-text-primary'),
      };
      assert.equal(rest.fill, 'rgba(0, 0, 0, 0)', '没悬停就垫了底');
      assert.deepEqual({ radius: hovered.radius, padding: hovered.padding, width: hovered.width, size: hovered.size },
        { radius: '12px', padding: '6px 4px', width: '76px', size: '48px' }, '同台艺人那一格和首页头像格不是同一副几何');
      assert.equal(hovered.fill, home.fill, '悬停没有铺首页那一档填充');
      assert.equal(hovered.ink.replace(/\s/g, ''), home.ink.replace(/\s/g, ''), '悬停没有换成主文字色');
      assert.equal(hovered.ring, 'none', '悬停还在给圆头像描圈');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('人物页骨架第一帧就带着这一位有的新作行与同台艺人，数据到了一次换齐、高度不变、封面不再等第二遍', { timeout: 60_000 }, async () => {
    const name = '七沢みあ';
    const opened = await visit(browser, '/', DESKTOP);
    try {
      await opened.page.route(/\/api\/entity\/shapes/, (route) => route.fulfill({ json: {
        ok: true, entities: [{ id: 90_001, kind: 'performer', names: [name], parts: ['feed', 'costars'] }] } }));
      // 骨架插进页面的那一刻就记下它带着哪几块：之后才补进去的，就是在骨架里跳了一下。
      await opened.page.addInitScript(() => {
        const first = { feed: null as boolean | null, foot: null as boolean | null, sheen: '' };
        (window as unknown as { skeletonFirst: typeof first }).skeletonFirst = first;
        new MutationObserver(() => {
          const skeleton = document.querySelector('[data-skeleton="entity/performer"]');
          if (!skeleton || first.feed !== null) return;
          first.feed = !!skeleton.querySelector('.feednew');
          first.foot = !!skeleton.querySelector('.entityfoot');
          // 骨架卡的微光和骨架同一帧就在：晚一步的话，那一步里露出来的是封面格的黑底。
          const pic = skeleton.querySelector('.feednewskeleton .pic.imgwait');
          first.sheen = pic ? getComputedStyle(pic, '::after').opacity : '';
        }).observe(document, { childList: true, subtree: true });
        // 真实库上启动脚本发出名单请求后还要连续跑四五百毫秒，名单的响应就在这段时间里到、
        // 排在队里。这里在发请求的同一个任务末尾占住主线程 700ms，把那一段复现出来。
        const fetch = window.fetch;
        let blocked = false;
        window.fetch = (...args) => {
          if (!blocked && String(args[0]).includes('/api/entity/shapes')) {
            blocked = true;
            queueMicrotask(() => { const end = performance.now() + 700; while (performance.now() < end); });
          }
          return fetch(...args);
        };
      });
      let release = () => {};
      const held = new Promise<void>((resolve) => { release = resolve; });
      await opened.page.route(/\/api\/entity\?/, async (route) => {
        await held;
        await route.fulfill({ json: {
          id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [],
          user_aliases: [], asset_count: 0, tags: [],
          related_performers: [{ id: 90_002, k: '共演者', n: 1, rep: null, has_image: false,
            has_avatar: false, avatar_focus: null }],
          links: [], metadata: {}, has_image: false, has_avatar: false, avatar_focus: null,
          representative_asset_id: null, entry_links: [], feed: { following: true },
        } });
      });
      await opened.page.route(/\/api\/feeds\/discoveries\?/, (route) => route.fulfill({ json: {
        ok: true, more: false, items: [{
          id: 1, code: 'ABC-001', title: '标题', link: 'https://javdb.com/v/x', cover_url: null,
          has_cover: true, cover_frame: null, poster_box: null, release_date: '2026-09-01',
          studio: '厂牌', performers: name, source_name: '', read: false, ignored: false,
          scrape_error: null }] } }));
      // 封面比数据晚到一截：整页要等它，而不是先换上真卡、再在封面格里微光一遍。
      await opened.page.route(/\/cover\?code=ABC-001/, async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 400));
        await route.fulfill({ contentType: 'image/png', body: Buffer.from(PIXEL, 'base64') });
      });
      await opened.page.goto(new URL(`/performers/${encodeURIComponent(name)}`,
        opened.page.url()).href, { waitUntil: 'load' });
      const skeleton = opened.page.locator('[data-skeleton="entity/performer"]');
      await skeleton.locator('.feednew .feednewskeleton').first().waitFor({ timeout: 15_000 });
      const before = await skeleton.evaluate((element) => {
        const row = element.querySelector('.feednew')!;
        const foot = element.querySelector('.entityhero > .entityfoot');
        // 同一个 `.pic.imgwait` 放在新作那一行外面，它的微光就是全站等待态那一种。
        const probe = document.createElement('div');
        probe.className = 'pic imgwait';
        document.querySelector('#main')!.append(probe);
        const plain = getComputedStyle(probe, '::after').backgroundImage;
        probe.remove();
        return { height: row.getBoundingClientRect().height,
          footHeight: foot?.getBoundingClientRect().height ?? 0,
          between: !!row.previousElementSibling?.matches('[data-filter-frame]')
            && !!row.nextElementSibling?.matches('.entitysection'),
          sheen: getComputedStyle(row.querySelector('.pic.imgwait')!, '::after').backgroundImage, plain,
          first: (window as unknown as { skeletonFirst: { feed: boolean; foot: boolean; sheen: string } }).skeletonFirst };
      });
      assert.ok(before.between, '骨架里的新作那一行不在筛选框和作品之间');
      const { sheen, ...parts } = before.first;
      assert.deepEqual(parts, { feed: true, foot: true }, '骨架先画了一版，新作行或同台艺人是后来才补进去的');
      assert.equal(sheen, '1', '新作骨架卡的微光晚于骨架出现，中间露出封面格的黑底');
      assert.ok(before.footHeight > 0, '骨架的资料卡底没有同台艺人那一条');
      assert.equal(before.sheen, before.plain, '新作骨架的微光另起了一种颜色');
      // 画好的页面上那一行一出现就得是真卡：再露一回它自己的骨架，就是同一行等了两遍。
      await opened.page.evaluate(() => {
        const seen = { second: false };
        (window as unknown as { feedSeen: typeof seen }).feedSeen = seen;
        new MutationObserver(() => {
          if (document.querySelector('[data-feed-new] .feednewskeleton')) seen.second = true;
        }).observe(document.querySelector('#index')!, { childList: true, subtree: true });
      });
      release();
      const row = opened.page.locator('[data-feed-new]');
      await row.locator('[data-feed-id]').waitFor({ timeout: 15_000 });
      const after = await row.evaluate((element) => ({
        height: element.getBoundingClientRect().height, busy: element.getAttribute('aria-busy'),
        waiting: element.querySelectorAll('[data-feed-id] .pic.imgwait').length,
        footHeight: document.querySelector('.entityhero > .entityfoot')?.getBoundingClientRect().height ?? 0,
        second: (window as unknown as { feedSeen: { second: boolean } }).feedSeen.second }));
      assert.equal(after.height, before.height, '占位行和到货的那一行不一样高，下面的作品网格会跳');
      assert.equal(after.footHeight, before.footHeight, '同台艺人那一条占位和真的不一样高，资料卡会伸缩');
      assert.equal(after.busy, null);
      assert.equal(after.second, false, '整页画出来之后新作那一行又单独骨架了一轮');
      assert.equal(after.waiting, 0, '骨架退场后封面格里又微光了一遍');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('卡片悬停面不顶到邻卡，三处卡片网格同一副列距', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      const card = opened.page.locator('#grid .grid > article.card').first();
      await card.hover();
      const geometry = await card.evaluate((element) => {
        const box = element.getBoundingClientRect();
        const neighbor = [...element.parentElement!.children].find((other) => other !== element
          && Math.abs(other.getBoundingClientRect().top - box.top) < 1)!;
        const spread = Number(/0px 0px 0px (\d+(?:\.\d+)?)px/.exec(getComputedStyle(element).boxShadow)?.[1]);
        // 人物页的作品网格和关注页的视频列表不在首页这叠卡里：各挂一个同类名的空壳读列距。
        const columnGap = (className: string) => {
          const probe = document.createElement('div');
          probe.className = className;
          document.querySelector('#main')!.append(probe);
          const gap = parseFloat(getComputedStyle(probe).columnGap);
          probe.remove();
          return gap;
        };
        return {
          spread, clearance: neighbor.getBoundingClientRect().left - (box.right + spread),
          home: parseFloat(getComputedStyle(element.parentElement!).columnGap),
          entity: columnGap('grid'), follow: columnGap('followlist'),
        };
      });
      assert.ok(geometry.spread > 0, '卡片悬停面没有往盒外铺');
      assert.ok(geometry.clearance >= geometry.spread,
        `悬停面离邻卡只剩 ${geometry.clearance}px，比它自己往外铺的 ${geometry.spread}px 还窄`);
      assert.equal(geometry.entity, geometry.home, '人物页作品网格的列距和首页不一样');
      assert.equal(geometry.follow, geometry.home, '关注页视频列表的列距和首页不一样');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('跳过渲染的元信息区不裁掉贴着边的头像悬停描边和焦点环', { timeout: 60_000 }, async () => {
    /* 演示库的作品都未归属，头像是不可聚焦的 `<span>`；首张卡归给一位女优，头像才是按钮。 */
    const opened = await openCatalogFixture(browser, (payload) => {
      const item = payload.items[0];
      if (!item) throw new Error('演示目录没有可替换的卡片');
      item.creator = '';
      item.performers = ['演示演员'];
      item.performer_total = 1;
      item.performer_entities = [{ id: 90_000, name: '演示演员', has_image: false }];
    });
    try {
      /* 视口外跳过渲染连带 paint containment，元信息区里画出 padding box 的像素一律裁掉；
         几何照算，所以这里比的是描边外沿与 padding box，不是与内容盒。头像贴着内容盒的
         左缘和上缘。这条不读 `overflow-clip-margin`：Safari 不认它，裁切边只能靠盒子本身。 */
      const { page } = opened;
      const avatar = page.locator('#grid .grid > article.card .meta > button.mav').first();
      const edges = () => avatar.evaluate((element) => {
        const meta = element.closest('.meta')!;
        const style = getComputedStyle(element);
        const shadow = Number(/0px 0px 0px (\d+(?:\.\d+)?)px/.exec(style.boxShadow)?.[1] ?? 0);
        const outline = style.outlineStyle === 'none' ? 0
          : parseFloat(style.outlineWidth) + parseFloat(style.outlineOffset);
        const ring = Math.max(shadow, outline);
        const box = element.getBoundingClientRect();
        const clip = meta.getBoundingClientRect();
        const left = clip.left + meta.clientLeft, top = clip.top + meta.clientTop;
        return {
          contained: getComputedStyle(meta).contentVisibility === 'auto',
          focused: element.matches(':focus-visible'), ring,
          // 描边外沿到裁切边还剩多少，四边取最小的那一边。
          room: Math.min(box.left - ring - left, box.top - ring - top,
            left + meta.clientWidth - (box.right + ring), top + meta.clientHeight - (box.bottom + ring)),
        };
      });
      await avatar.hover();
      const hovered = await edges();
      assert.ok(hovered.contained, '首页卡片的元信息区不再跳过渲染：这条用例守的裁切前提变了，改用例');
      assert.ok(hovered.ring > 0, '头像悬停没有描边');
      assert.ok(hovered.room >= -.5, `头像悬停描边越过了元信息区的裁切边 ${-hovered.room}px，那一截会被裁掉`);
      await page.mouse.move(0, 0);
      await page.keyboard.press('Tab');
      await avatar.focus();
      const focused = await edges();
      assert.ok(focused.focused && focused.ring > 0, '键盘聚焦的头像没有焦点环');
      assert.ok(focused.room >= -.5, `头像焦点环越过了元信息区的裁切边 ${-focused.room}px，那一截会被裁掉`);
    } finally {
      await opened.close();
    }
  });

  it('暗色下 React 卡片和旧样式表控件的阴影都换成看得见的那一档', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/stats', DESKTOP);
    try {
      const card = opened.page.locator('#main [class~="shadow-card"]').first();
      await card.waitFor({ timeout: 15_000 });
      await settle(opened.page);
      /* Tailwind 把阴影 token 的字面值抄进工具类，`.dark` 里改 `--shadow-*` 够不着它；
         旧样式表里写死的浅色阴影同样不跟主题走。读三类来源各一处的计算值。 */
      const alphas = () => opened.page.evaluate(() => {
        const strongest = (shadow: string) => Math.max(0, ...[...shadow.matchAll(
          /rgba\(0, 0, 0, ([\d.]+)\)|rgb\(0, 0, 0\)/g)].map((match) => (match[1] ? Number(match[1]) : 1)));
        const probe = (html: string) => {
          const holder = document.createElement('div');
          holder.innerHTML = html;
          const element = holder.firstElementChild!;
          // 挂在 React 岛外面：岛里的重置会把旧样式表的按钮阴影清掉。
          document.body.append(element);
          const shadow = getComputedStyle(element).boxShadow;
          element.remove();
          return strongest(shadow);
        };
        return {
          card: strongest(getComputedStyle(document.querySelector('#main [class~="shadow-card"]')!).boxShadow),
          button: probe('<button class="geist-button" type="button">键</button>'),
          toast: probe('<div class="toast">回执</div>'),
        };
      });
      await opened.page.evaluate(() => {
        document.documentElement.dataset.theme = 'light';
        document.documentElement.classList.remove('dark');
      });
      const light = await alphas();
      // `web/app.js` 的 `applyTheme('dark')` 就是这两句；这里只借它换一次配色。
      await opened.page.evaluate(() => {
        document.documentElement.dataset.theme = 'dark';
        document.documentElement.classList.add('dark');
      });
      const dark = await alphas();
      for (const key of Object.keys(light) as Array<keyof typeof light>) {
        assert.ok(light[key] > 0 && light[key] < .2, `浅色下 ${key} 的阴影 ${light[key]} 不在浅色那一档`);
        // #111 的页面底上，黑影再淡就压不出比底更暗的一圈。
        assert.ok(dark[key] >= .4, `暗色下 ${key} 的阴影只有 ${dark[key]}，在 #111 底上看不见`);
      }
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('被打断的那一轮只有结束原因，卡片正文下面不留空行', { timeout: 60_000 }, async () => {
    const opened = await openActivity(browser, [
      { ...settledRun(1, 'interrupted', '追更检查'), error: '服务重启，这一轮没有跑完' },
    ]);
    try {
      const body = await opened.page.locator('li[data-status="interrupted"] > div').first()
        .evaluate((element) => ({
          trailing: element.getBoundingClientRect().bottom - element.lastElementChild!.getBoundingClientRect().bottom,
          padding: parseFloat(getComputedStyle(element).paddingBottom),
        }));
      assert.ok(Math.abs(body.trailing - body.padding) <= .5,
        `正文最后一行下面空出 ${body.trailing}px，底边距只有 ${body.padding}px`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  /* 首页「未入库的新作」那一排会自己横着走，每一帧都发一次 scroll。手机上侧栏是抽屉，
     两枚弹层一打开就碰上它；演示库没有订阅，这一排由拦下的 `/api/feeds/discoveries`
     画出来（字段以 `src/peach/web_feeds.py` 为准）。夹具关了动效，自动滚动不起步，
     所以这里亲手滚它，发出的是同一种 scroll。 */
  it('390px 下侧栏两枚弹层不随别处那一排横滚收起，整页滚动才收', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', MOBILE);
    try {
      const items = Array.from({ length: 12 }, (_, index) => ({
        id: index + 1, code: `DEMO-${String(index + 1).padStart(3, '0')}`, title: `演示新作 ${index + 1}`,
        studio: '演示厂牌', release_date: '2026-09-01', has_cover: false, cover_url: '', link: '', read: false,
      }));
      await opened.page.route((url) => url.pathname === '/api/feeds/discoveries', (route) => route.fulfill({
        status: 200, contentType: 'application/json', body: JSON.stringify({ items }),
      }));
      await opened.page.reload({ waitUntil: 'load' });
      const row = opened.page.locator('#feedNew .feednewrow');
      await row.waitFor({ state: 'visible', timeout: 15_000 });
      await settle(opened.page);
      assert.ok(await row.evaluate((element) => element.scrollWidth > element.clientWidth + 120),
        '新作那一排在 390px 下没有可横滚的余量，这条用例量不到东西');
      await opened.page.locator('#filterBtn').tap();
      await opened.page.waitForFunction(() => document.querySelector('#drawer')?.classList.contains('open'));
      for (const [trigger, menuId] of [['#brandHome', 'boardLibraryMenu'], ['#boardGlowBtn', 'boardGlowMenu']] as const) {
        const menu = opened.page.locator(`#${menuId}`);
        await opened.page.locator(trigger).tap();
        await menu.waitFor({ state: 'visible', timeout: 5_000 });
        for (let step = 0; step < 4; step += 1) {
          await row.evaluate((element) => { element.scrollLeft += 30; });
          await opened.page.waitForTimeout(100);
        }
        assert.ok(await menu.isVisible(), `${trigger} 打开的弹层随新作那一排横滚收起了`);
        // 菜单装不下时本来就要在内部滚；捕获阶段的 scroll 连它自己的也收得到。
        await menu.evaluate((element) => element.dispatchEvent(new Event('scroll')));
        await opened.page.waitForTimeout(100);
        assert.ok(await menu.isVisible(), `${trigger} 打开的弹层随它自己的内部滚动收起了`);
        assert.equal(await opened.page.locator(trigger).getAttribute('aria-expanded'), 'true');
        await opened.page.evaluate(() => document.dispatchEvent(new Event('scroll')));
        await menu.waitFor({ state: 'hidden', timeout: 5_000 });
      }
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('设置里的光晕配色和侧栏配色卡是同一组预设色块，键盘选一档两处一起换', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', DESKTOP);
    try {
      await settle(opened.page);
      await opened.page.locator('#settingsBtn').click();
      const grid = opened.page.locator('#homeGlowControls [data-glow-grid]');
      await grid.waitFor({ state: 'visible', timeout: 10_000 });
      const chips = (root: string) => opened.page.locator(`${root} [data-glow-preset]`).evaluateAll((nodes) =>
        nodes.map((node) => ({
          key: (node as HTMLElement).dataset.glowPreset,
          label: node.getAttribute('aria-label'),
          pressed: node.getAttribute('aria-pressed'),
          ball: getComputedStyle(node.querySelector('.board-glow-ball')!).backgroundImage,
        })));
      const inSettings = await chips('#homeGlowControls');
      assert.ok(inSettings.length >= 2, '设置里没有预设色块');
      assert.deepEqual(inSettings, await chips('#boardGlowMenu'), '设置里的预设色块和侧栏配色卡不是同一组');
      const size = await grid.locator('.board-glow-ball').first().evaluate((node) => node.getBoundingClientRect().width);
      assert.equal(size, 28, '设置里的色块和侧栏那一枚不是同一副尺寸');
      /* 设置这一行有整块设置那么宽：列数跟着可用宽度走，每格就是一枚球，挨着排满再换行，
         间距与侧栏那条 `.board-glow-grid` 同一个值；侧栏那张卡仍是六列。 */
      const gridStyle = (root: string) => opened.page.locator(`${root} [data-glow-grid]`).evaluate((node) => {
        const style = getComputedStyle(node);
        return { tracks: style.gridTemplateColumns, gap: style.columnGap, inline: style.paddingLeft };
      });
      const swatchLayout = () => grid.evaluate((node) => {
        const box = node.getBoundingClientRect();
        const chips = [...node.querySelectorAll('[data-glow-preset]')].map((chip) => chip.getBoundingClientRect());
        const firstTop = chips[0]!.top;
        return {
          count: chips.length,
          firstRow: chips.filter((chip) => chip.top === firstTop).length,
          rows: new Set(chips.map((chip) => chip.top)).size,
          steps: chips.slice(1).filter((chip) => chip.top === firstTop).map((chip, index) => chip.left - chips[index]!.left),
          startsAt: chips[0]!.left - box.left,
          overflow: node.scrollWidth > node.clientWidth || chips.some((chip) => chip.right > box.right + 0.5),
          viewportOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        };
      });
      const settingsGrid = await gridStyle('#homeGlowControls');
      const sidebarGrid = await gridStyle('#boardGlowMenu');
      assert.ok(settingsGrid.tracks.split(' ').every((track) => track === '28px'), '设置里的色块每格不是一枚球的宽度');
      assert.equal(settingsGrid.gap, sidebarGrid.gap, '设置里的色块间距和侧栏配色卡不同');
      assert.equal(settingsGrid.inline, '0px', '设置里的色块没有从这一行的内容左缘起');
      // 侧栏配色卡此刻收着，计算值停在声明式 `repeat(6, 1fr)`；展开时是六个解析后的宽度。
      assert.ok(sidebarGrid.tracks === 'repeat(6, 1fr)' || sidebarGrid.tracks.split(' ').length === 6,
        `侧栏配色卡不再是每行六枚：${sidebarGrid.tracks}`);
      const wide = await swatchLayout();
      assert.ok(wide.firstRow > 6, `桌面宽度下第一行只排了 ${wide.firstRow} 枚，右边的空间没用上`);
      assert.ok(wide.steps.every((step) => step === 34), `设置里的色块没有挨着排：步长 ${wide.steps.join('/')}`);
      assert.equal(wide.startsAt, 0, '设置里的第一枚色块没有从这一行的内容左缘起');
      assert.equal(wide.overflow, false, '桌面宽度下色块越出了这一行');
      assert.equal(await grid.getAttribute('role'), 'group');
      assert.ok(await grid.getAttribute('aria-label'), '预设色块那一组没有无障碍名称');

      const target = inSettings.find((chip) => chip.pressed === 'false')!;
      const chip = grid.locator(`[data-glow-preset="${target.key}"]`);
      await chip.focus();
      await opened.page.keyboard.press('Space');
      await opened.page.waitForFunction((key) => document.querySelector(
        `#homeGlowControls [data-glow-preset="${key}"]`)?.getAttribute('aria-pressed') === 'true', target.key);
      assert.equal(await grid.locator('[aria-pressed="true"]').count(), 1);
      assert.equal(await opened.page.evaluate(() => (document.activeElement as HTMLElement | null)?.dataset.glowPreset
        && document.activeElement!.closest('#homeGlowControls [data-glow-grid]') ? (document.activeElement as HTMLElement).dataset.glowPreset : null),
        target.key, '选完之后焦点离开了刚选的那一枚色块');
      assert.equal(await opened.page.locator(`#boardGlowMenu [data-glow-preset="${target.key}"]`)
        .getAttribute('aria-pressed'), 'true', '侧栏配色卡没有跟着换到同一档');
      assert.equal(await opened.page.locator('#homeGlowControls [data-glow-preset-name]').textContent(), target.label);
      assert.equal(await opened.page.evaluate(() => JSON.parse(localStorage.getItem('peach.settings.v1')!).homeGlow.preset),
        target.key, '选中的那一档没有写进设置');

      await opened.page.setViewportSize({ width: MOBILE.width, height: MOBILE.height });
      await grid.waitFor({ state: 'visible', timeout: 10_000 });
      const narrow = await swatchLayout();
      assert.ok(narrow.firstRow < narrow.count && narrow.rows > 1, `${MOBILE.width}px 下色块没有换行`);
      assert.ok(narrow.steps.every((step) => step === 34), `${MOBILE.width}px 下色块没有挨着排`);
      assert.equal(narrow.startsAt, 0, `${MOBILE.width}px 下第一枚色块没有从内容左缘起`);
      assert.equal(narrow.overflow, false, `${MOBILE.width}px 下色块越出了这一行`);
      assert.equal(narrow.viewportOverflow, false, `${MOBILE.width}px 下页面出现横向溢出`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  /* ADR-0050：设置弹层只放一行一个值、改完就生效的控件；带「保存配置」的表单在配置页，
     要确认、要看进度的长任务在数据管理页，订阅源在关注管理页。 */
  it('设置弹层「这台电脑」只有摘要卡，按钮直达配置页；媒体修复与订阅源都不在设置和配置页里', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', DESKTOP);
    try {
      const { page } = opened;
      await settle(page);
      await page.locator('#settingsBtn').click();
      const panel = page.locator('#settingsPanel');
      await panel.getByRole('tab', { name: '这台电脑' }).click({ timeout: 10_000 });
      const machine = panel.locator('#machineSettings');
      const go = machine.getByRole('button', { name: '打开配置页', exact: true });
      await go.waitFor({ state: 'visible', timeout: 10_000 });
      assert.deepEqual(await machine.locator('dt').allTextContents(), ['媒体库', '端口', '更新']);
      assert.equal(await machine.locator('input, textarea, select, form, [role="switch"], [aria-haspopup="listbox"]').count(), 0,
        '摘要卡里出现了可编辑的控件');
      assert.equal(await panel.locator('.configpage').count(), 0, '设置弹层里又挂了一份配置页');
      for (const text of ['媒体修复', '订阅源', '保持登录时间']) {
        assert.equal(await panel.getByText(text, { exact: true }).count(), 0, `设置弹层里还有「${text}」`);
      }

      await go.click();
      await expectBody(page, '/configuration', configurationBody(page));
      assert.equal(new URL(page.url()).pathname, '/configuration');
      assert.equal(await panel.isHidden(), true, '去配置页之后设置弹层没有关');
      await settle(page);
      for (const text of ['媒体修复', '订阅源']) {
        assert.equal(await page.locator('#stats').getByText(text, { exact: true }).count(), 0, `配置页上还有「${text}」`);
      }
      const entry = page.locator('#managebar [data-manage="configuration"]');
      await entry.waitFor({ state: 'attached', timeout: 10_000 });
      assert.equal(await entry.getAttribute('aria-pressed'), 'true', '管理菜单里的「配置」没有标成当前页');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });
});
