/* 设计决定按浏览器里的计算值断言，不绑定 CSS 源码的写法。
 *
 * 页面迁到 React 时，旧的源码字符串断言按 ADR-0031 分三类：设计决定落在这里或 lint 规则，
 * 行为落在 vitest，布局与运行期问题归 `smoke.test.ts`。每条用例守一个决定，读的是
 * `getComputedStyle`，类名或样式写法换了照样成立。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Locator, Page } from 'playwright-core';

import { DETAIL, openFollowFeed } from './follow-fixture.ts';
import {
  configurationBody, expectBody, launch, layout, requiredEnv, settle, visit, VIEWPORTS, type Visit,
} from './harness.ts';
import { ITEM, openItemPage } from './item-fixture.ts';

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

/** 口味页浏览器画像的五个维度：头一个是其余的十倍，和真实馆藏的分布一样。 */
const TASTE_CATEGORIES = [['剧情', 657], ['写真', 68], ['素人', 56], ['偶像', 4], ['企划', 1]]
  .map(([name, score]) => ({ name, score }));

/** 一张全身站姿照的人脸框：脸落在画面上半截的一小块里，小圆框要放大好几倍才看得清。 */
const TASTE_FACE = { cx: .439, cy: .224, faceW: 67, imgW: 640, imgH: 960 };

/** 口味页按改写过的 `/api/taste` 打开：演示库没有浏览记录，也没有带人脸框的实体图。
 * 字段以 `src/peach/taste_history.py` 与 `src/peach/web_stats.py` 为准；实体图换成与人脸框同尺寸的纯色图。 */
async function openTaste(browser: Browser, viewport: typeof DESKTOP): Promise<Visit> {
  const opened = await visit(browser, '/taste', viewport);
  const face = (id: number, name: string) => ({
    name, peach_items: 3, peach_score: 5, entity_id: id, has_image: true, avatar_focus: { box: TASTE_FACE },
  });
  await opened.page.route(/\/api\/taste\?/, async (route) => {
    const json = await (await route.fetch()).json();
    await route.fulfill({ json: { ...json, rankings: { ...json.rankings,
      browser_categories: TASTE_CATEGORIES,
      peach_performers: [face(901, '演示女优')],
      peach_creators: [face(902, '演示创作者')],
    } } });
  });
  await opened.page.route(/\/entity-image\?/, (route) => route.fulfill({
    contentType: 'image/svg+xml',
    body: `<svg xmlns="http://www.w3.org/2000/svg" width="${TASTE_FACE.imgW}" height="${TASTE_FACE.imgH}">`
      + `<rect width="${TASTE_FACE.imgW}" height="${TASTE_FACE.imgH}" fill="#888"/></svg>`,
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await expectBody(opened.page, '/taste', [
    opened.page.locator('#stats').getByRole('tab', { name: '浏览器记录', exact: true }),
  ]);
  return opened;
}

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

/** 垃圾文件页。计数行由 `junk-queue` island 画，演示库里一条候选都没有时它照样在；壳铺的
 *  骨架（`[data-junk-count-skeleton]`）也有这两块，等的是 island 接管之后的那一版。 */
const JUNK_COUNT = '#count > .peach-react:not([data-junk-count-skeleton])';
async function openJunk(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/junk-files', WIDE);
  await expectBody(opened.page, '/junk-files', [
    opened.page.locator(`${JUNK_COUNT} [data-collection-summary]`),
    opened.page.locator(`${JUNK_COUNT} [data-junk-filters]`),
  ]);
  await settle(opened.page);
  return opened;
}

/** 一条垃圾候选。字段以 `/api/ads`（`src/peach/web_batch.py` 的 `q_ads`）为准；类型都挑没有预览
 *  的，造出来的 id 取不到缩略图。 */
const junkItem = (id: number, kind: string, name: string) => ({
  id, name, junk_kind: kind, why: '文件名像推广', size: 1048576 * id, location: 'local', cost: '',
});

/** 垃圾文件页按给定的候选打开：演示库里没有垃圾候选。`/api/ads` 每次都按当前名单回话，
 *  `/api/batch` 记下请求体、把处置掉的那条从名单里拿掉。 */
async function openJunkWith(browser: Browser, items: ReturnType<typeof junkItem>[], viewport = WIDE) {
  const opened = await visit(browser, '/junk-files', viewport);
  const state = { items: [...items], batches: [] as { ids: number[]; operation: string }[], reads: [] as string[] };
  await opened.page.route('**/api/ads?**', (route) => {
    const url = new URL(route.request().url());
    state.reads.push(url.search);
    const kind = url.searchParams.get('kind');
    const shown = state.items.filter((item) => !kind || item.junk_kind === kind);
    const counts: Record<string, number> = {};
    for (const item of state.items) counts[item.junk_kind] = (counts[item.junk_kind] || 0) + 1;
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      items: shown, total: shown.length, all_total: state.items.length, pending_total: state.items.length,
      dismissed_total: 0, counts,
    }) });
  });
  await opened.page.route('**/api/batch', (route) => {
    const body = JSON.parse(route.request().postData() || '{}');
    state.batches.push(body);
    state.items = state.items.filter((item) => !body.ids.includes(item.id));
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, updated: body.ids.length }) });
  });
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('#grid [data-junk-card]').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return { ...opened, state };
}

/** 一个重复文件。字段以 `/api/duplicates`（`src/peach/web_contract.py`）为准。 */
const duplicateFile = (id: number, location: string, patch: Record<string, unknown> = {}) => ({
  id, name: `DUPE-${id}.mp4`, path: `R:\\media\\DUPE-${id}.mp4`, location, drive: location === '115' ? 'B:' : 'R:',
  size: 1073741824, duration: 3600, is_largest: false, is_longest: false, ...patch,
});

/** 重复文件页按给定的两组打开：演示库里没有重复组。一组字节一致，一组本地与 115 混着。
 *  文件是造出来的，抽帧那一趟必然取不到，给它一张能加载完的图。 */
async function openDuplicates(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/duplicates', DESKTOP);
  const groups = [
    { code: 'DUPE-001', count: 2, identical: true, drives: ['R:'], cross_drive: false, reclaimable: 1073741824,
      files: [duplicateFile(9001, 'local', { is_largest: true }), duplicateFile(9002, 'local', { is_longest: true })] },
    { code: 'DUPE-002', count: 2, identical: false, drives: ['R:', 'B:'], cross_drive: true, reclaimable: 1073741824,
      files: [duplicateFile(9003, 'local', { is_largest: true, is_longest: true }), duplicateFile(9004, '115')] },
  ];
  await opened.page.route('**/api/duplicates?**', (route) => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ total: 2, files: 4, reclaimable: 2147483648, groups }),
  }));
  await opened.page.route('**/thumb?**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('#stats section[aria-label="DUPE-002"] .duplicate-row').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** 打开一张索引页，名册与词表都换成桩：演示库的索引在一轮里会从空变成有，不桩的话
 * 这一条量到的可能是空态。名册第一格带一张桩图，其余只落首字母。 */
async function openIndexPage(browser: Browser, path: string): Promise<Visit> {
  const opened = await visit(browser, path, DESKTOP);
  const json = (body: unknown) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  await opened.page.route('**/api/index?**', (route) => {
    const kind = new URL(route.request().url()).searchParams.get('kind');
    return route.fulfill(json(kind === 'tags'
      ? { items: [{ k: '痴女', n: 4, cat: 'role' }, { k: '秘书OL', n: 2, cat: 'scene' }], has_more: false,
        categories: { role: 1, scene: 1 } }
      : { items: [{ k: '甲', n: 3, members: 2, entity_id: 90_101, has_image: true }, { k: '乙', n: 1, members: 1 }],
        has_more: false }));
  });
  // 桩图要比框大：比框小的图按原尺寸摆，走的是另一条规则。
  await opened.page.route('**/entity-image?**', (route) => route.fulfill({
    status: 200, contentType: 'image/svg+xml',
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="800"><rect width="600" height="800" fill="#888"/></svg>',
  }));
  await opened.page.route('**/api/follow/tags?**', (route) => route.fulfill(json({
    items: [{ k: 'some_artist', n: 5, cat: 'artist' }, { k: 'long_hair', n: 9, cat: 'general' }], has_more: false,
    categories: { artist: 1, general: 1 } })));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('#index [data-index-cell], #index [data-alpha-tag], #index [data-tag-chip]').first()
    .waitFor({ timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** 一串 `box-shadow`（计算值或 token 原文）里最大的那个像素数：落影三层里最远那层的模糊半径。 */
const farthestShadow = (shadow: string) =>
  Math.max(0, ...[...shadow.matchAll(/(\d+(?:\.\d+)?)px/g)].map((match) => Number(match[1])));

/** 播放列表页按一份造出来的 `/api/playlists`（`src/peach/web_playlists.py`）打开：演示库里
 * 没有播放列表。第一份带三位署名，第二份没人（画标题首字），第三份是空列表（写「无预览」）。
 * 封面是造出来的编号，给一张能加载完的图。 */
async function openPlaylistsPage(browser: Browser, viewport = DESKTOP): Promise<Visit> {
  const opened = await visit(browser, '/playlists', viewport);
  const face = (id: number, name: string, kind = 'performer') => ({ kind, id, name, has_image: false });
  const row = (id: number, patch: Record<string, unknown> = {}) => ({
    id, name: `列表${id}`, source_kind: 'manual', source_seed_asset_id: null, current_asset_id: null,
    created_at: '2026-09-01 10:00:00', updated_at: '2026-09-01 10:00:00', item_count: 2,
    preview_asset_id: 11, preview_ids: [11, 12], faces: [], ...patch,
  });
  await opened.page.route((url) => url.pathname === '/api/playlists', (route) => route.fulfill({ json: { items: [
    row(1, { source_kind: 'mix', faces: [face(901, '甲'), face(902, '乙'), face(903, '丙', 'creator')] }),
    row(2),
    row(3, { item_count: 0, preview_asset_id: null, preview_ids: [] }),
  ] } }));
  await opened.page.route('**/poster**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.reload({ waitUntil: 'load' });
  await opened.page.locator('#stats [data-playlist-card]').first().waitFor({ timeout: 15_000 });
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
  await page.route('**/api/follow?summary=1', (route) => route.fulfill(json({
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
  await opened.page.locator('[data-entry-feed]').waitFor({ timeout: 15_000 });
  await opened.page.locator('[data-entity-foot] [data-related-performer]').first().waitFor({ timeout: 15_000 });
  await settle(opened.page);
  await opened.page.evaluate(() => {
    document.documentElement.dataset.theme = 'light';
    document.documentElement.classList.remove('dark');
  });
  return opened;
}

/** 照片档：一部作品的两张官方样张加六张本地图片，缩略图都是 1×1 的图，量的是墙的几何。 */
async function openPhotoWall(browser: Browser, viewport = DESKTOP): Promise<Visit> {
  const name = '七沢みあ';
  const opened = await visit(browser, '/', viewport);
  const { page } = opened;
  await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
    id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [], user_aliases: [],
    asset_count: 0, tags: [], related_performers: [], links: [], metadata: {}, has_image: false, has_avatar: false,
    avatar_focus: null, representative_asset_id: null, entry_links: [], feed: { following: false },
  } }));
  // 下一页一直不回：「载入更多」停在忙态，墙不再变，量得到那枚键的几何。
  await page.route(/\/api\/photos\?/, (route) => Number(new URL(route.request().url()).searchParams.get('offset') || 0) ? undefined : route.fulfill({ json: {
    kind: 'performer', name, entity_id: 90_001, total: 12, seed: '', has_more: true, sample_total: 2,
    items: Array.from({ length: 6 }, (_, i) => ({ id: 200 + i, name: `${200 + i}.jpg`, size: 1, location: 'media' })),
    sets: [{ id: 'code:SSIS-057', kind: 'code', code: 'SSIS-057', name: '雨の日', title: 'SSIS-057 雨の日', n: 2,
      release_date: '2021-05-18', site: 'dmm', site_label: 'DMM', has_cover: true }],
  } }));
  await page.route(/\/(?:photo-thumb|sample-thumb)\?/, (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await page.goto(new URL(`/performers/${encodeURIComponent(name)}?media=photos`, page.url()).href, { waitUntil: 'load' });
  await page.locator('[data-local-wall] [data-photo-cell] img').first().waitFor({ timeout: 15_000 });
  await settle(page);
  return opened;
}

/** 本地图片那面墙的排法：网格数列宽，瀑布流数 column-count。 */
const photoWallFaces = (page: Page) => page.evaluate(() => {
  const wall = document.querySelector<HTMLElement>('[data-local-wall]')!;
  const style = getComputedStyle(wall);
  const cell = wall.querySelector<HTMLElement>('[data-photo-cell]')!;
  const box = cell.getBoundingClientRect();
  return {
    display: style.display,
    columns: style.display === 'grid' ? style.gridTemplateColumns.split(' ').length : Number(style.columnCount),
    gap: style.columnGap,
    square: Math.abs(box.width - box.height) <= 1,
  };
});

/** 照片档里 `count` 张本地图，点开第一张的灯箱。大图是 `width`×`height` 的 SVG；取图口全部回桩图，
 *  `/photo` 原图走计费来源，设计用例也不碰真的。 */
async function openLightbox(browser: Browser, { count, width, height }: { count: number; width: number; height: number }):
  Promise<Visit & { box: Locator }> {
  const name = '七沢みあ';
  const opened = await visit(browser, '/', DESKTOP);
  const { page } = opened;
  const svg = (w: number, h: number) => ({ status: 200, contentType: 'image/svg+xml',
    body: `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="100%" height="100%" fill="#3a4a5a"/></svg>` });
  await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
    id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [], user_aliases: [],
    asset_count: 0, tags: [], related_performers: [], links: [], metadata: {}, has_image: false, has_avatar: false,
    avatar_focus: null, representative_asset_id: null, entry_links: [], feed: { following: false },
  } }));
  await page.route(/\/api\/photos\?/, (route) => route.fulfill({ json: {
    kind: 'performer', name, entity_id: 90_001, total: count, seed: '', has_more: false, sample_total: 0, sets: [],
    items: Array.from({ length: count }, (_, i) => ({ id: 300 + i, name: `${300 + i}.jpg`, size: 1, location: 'media' })),
  } }));
  await page.route(/\/photo\?/, (route) => route.fulfill(svg(width, height)));
  await page.route(/\/photo-thumb\?/, (route) => route.fulfill(svg(160, 120)));
  await page.goto(new URL(`/performers/${encodeURIComponent(name)}?media=photos`, page.url()).href, { waitUntil: 'load' });
  await page.locator('[data-photo-cell] img').first().waitFor({ timeout: 15_000 });
  await settle(page);
  await page.locator('[data-photo-cell]').first().click();
  const box = page.locator('dialog[data-photo-lightbox][open]');
  await box.waitFor();
  await page.waitForFunction(() => document.querySelector<HTMLImageElement>('[data-photo-main] .swiper-slide-active img')!
    .naturalWidth > 0, undefined, { timeout: 10_000 });
  return { ...opened, box };
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

/** 打开一位有资料的女优：资料表、名字行和外链照服务端下发的形状写，主题按参数切好。
 *  `extra` 覆盖资料里的字段：默认没有看片那一行（`entry_links` 只有 minnano-av 那枚 pill、没有 `feed`），
 *  要验两行都在的几何就从这里补。 */
async function openProfiledPerformer(browser: Browser, viewport = DESKTOP, theme: 'light' | 'dark' = 'light',
  extra: Record<string, unknown> = {}): Promise<Visit> {
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
    ...extra,
  } }));
  // 这几条链接是造出来的，服务端的圆标取不到；那是另一条判据，这里给一张能加载完的图。
  await opened.page.route('**/link-mark**', (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await opened.page.goto(new URL(`/performers/${encodeURIComponent(PROFILED.name)}`, opened.page.url()).href, { waitUntil: 'load' });
  await opened.page.locator('[data-entity-card] [data-entity-links]').waitFor({ timeout: 15_000 });
  await settle(opened.page);
  await opened.page.evaluate((dark) => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.classList.toggle('dark', dark);
  }, theme === 'dark');
  return opened;
}

/** 资料卡浮层的落影要和遗留 `.popmenu` 同一副：在同一页造一个空 `.popmenu` 取它的计算值。 */
async function popmenuShadow(page: Page): Promise<string> {
  return page.evaluate(() => {
    const menu = document.body.appendChild(Object.assign(document.createElement('div'), { className: 'popmenu' }));
    const shadow = getComputedStyle(menu).boxShadow;
    menu.remove();
    return shadow;
  });
}

/** 下拉栏里一部作品的小图。字段以 `_suggest_work_card`（`src/peach/web_entity.py`）为准。 */
const suggestCard = (id: number) => ({ id, code: `ABW-${id % 1000}`, has_cover: true, has_thumb: false, cover_frame: null, poster_box: null });

/** 一段输入命中女优、厂牌与视频三类的补全，字段以 `q_suggest` 为准。演示库里没有女优实体。 */
const SUGGEST = {
  q: '涼森',
  groups: [
    { kind: 'performer', label: '女优', total: 2, items: [
      { value: '涼森れむ', n: 128, matched: '', id: null, entity_id: 90_301, has_image: true, avatar_focus: null, rep: null,
        agency: 'Capsule Agency', works: [1, 2, 3, 4].map((at) => suggestCard(90_400 + at)) },
      { value: '涼森ひより', n: 3, matched: 'すずもりひより', id: null, entity_id: 90_302, has_image: false, rep: null,
        agency: '', works: [] },
    ] },
    { kind: 'studio', label: '厂牌', total: 1, items: [
      { value: 'Prestige', n: 900, matched: '', id: null, entity_id: 90_303, has_image: false, has_logo: true },
    ] },
    { kind: 'asset', label: '视频', total: 12, items: [1, 2, 3, 4, 5].map((at) => ({
      value: `ABW-${500 + at}`, n: 0, matched: '', id: 90_500 + at, code: `ABW-${500 + at}`,
      title: '出演作', who: '涼森れむ', card: suggestCard(90_500 + at),
    })) },
  ],
};

/** 补全、下拉里的图和点进去的资料页都按上面那份造好的数据答。返回每次补全请求问的种类。
 *  图是造出来的实体和番号，服务端取不到；那是另一条判据，这里给一张能加载完的图。 */
async function stubSuggest(page: Page): Promise<string[]> {
  const kinds: string[] = [];
  await page.route(/\/api\/suggest\?/, (route) => {
    const kind = new URL(route.request().url()).searchParams.get('kind') || '';
    kinds.push(kind);
    return route.fulfill({ json: { q: SUGGEST.q, groups: SUGGEST.groups.filter((group) => !kind || group.kind === kind) } });
  });
  await page.route(/\/(?:cover|entity-image|avatar|logo)\?/, (route) => route.fulfill({
    status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
  }));
  await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
    id: 90_301, kind: 'performer', canonical_name: '涼森れむ', aliases: [], display_aliases: [], user_aliases: [],
    asset_count: 0, tags: [], related_performers: [], links: [], metadata: {}, entry_links: [],
    has_image: false, has_avatar: false, avatar_focus: null, representative_asset_id: null,
  } }));
  return kinds;
}

/** 资料卡此刻的几何：身份列、资料表与卡本身的外框，以及资料表那道分隔线落在哪一边。 */
async function heroGeometry(page: Page) {
  return page.evaluate(() => {
    const rect = (selector: string) => {
      const box = document.querySelector(selector)?.getBoundingClientRect();
      return box ? { left: box.left, right: box.right, top: box.top, bottom: box.bottom } : null;
    };
    const hero = document.querySelector('[data-entity-card]')!;
    const facts = document.querySelector('[data-entity-facts]');
    const style = facts ? getComputedStyle(facts) : null;
    return {
      hero: rect('[data-entity-card]'), identity: rect('[data-entity-identity]'), facts: rect('[data-entity-facts]'),
      heroScrolls: hero.scrollWidth > hero.clientWidth + 1,
      rule: style ? { left: style.borderLeftWidth, top: style.borderTopWidth } : null,
      labels: [...document.querySelectorAll('[data-entity-facts] dt')].map((dt) => dt.textContent!.trim()),
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
      const stack = opened.page.locator('[data-media-card][data-id] [data-media-avatars]').first();
      await stack.waitFor({ timeout: 5_000 });
      const avatars = stack.locator('[data-media-avatar]');
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
      const card = stack.locator('xpath=ancestor::article[@data-media-card]').first();
      const bounds = await card.evaluate((cardElement) => {
        const stackRect = cardElement.querySelector('[data-media-avatars]')!.getBoundingClientRect();
        const lastRect = cardElement.querySelector('[data-media-avatar]:last-child')!.getBoundingClientRect();
        const firstRect = cardElement.querySelector('[data-media-avatar]')!.getBoundingClientRect();
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
        const firstRect = cardElement.querySelector('[data-media-avatar]')!.getBoundingClientRect();
        const lastRect = cardElement.querySelector('[data-media-avatar]:last-child')!.getBoundingClientRect();
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

  /* 搜索框住在粘性顶栏里，永远在视口上沿；可 `html` 的 `scroll-padding-top` 把那一条
     划成「被顶栏盖住」的区域，浏览器每敲一个字就把光标往下滚一次，页面一路往回退。
     点击走鼠标坐标：定位器的 click 会先替元素滚进视口，那一下不是页面自己的行为。 */
  it('往下翻过之后在搜索框里打字，页面停在原处', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      const { page } = opened;
      await page.setViewportSize({ width: DESKTOP.width, height: 480 });
      await page.mouse.move(DESKTOP.width / 2, 300);
      await page.mouse.wheel(0, 600);
      await page.waitForFunction(() => scrollY > 300, undefined, { timeout: 5_000 });
      const before = await page.evaluate(() => scrollY);
      const box = await page.locator('#q').boundingBox();
      if (!box) throw new Error('搜索框不可见');
      await page.mouse.click(box.x + 40, box.y + box.height / 2);
      await page.keyboard.type('演示abc', { delay: 60 });
      await page.waitForTimeout(300);
      assert.equal(await page.evaluate(() => scrollY), before, '打字时页面跟着滚动了');
    } finally {
      await opened.close();
    }
  });

  it('首页也有大图／小图：默认小图，大图只拉长番号卡，选择单独记住', { timeout: 60_000 }, async () => {
    /* 演示库没有番号作品，给首张卡挂一个；第二张保持普通视频，看它不跟着拉长。 */
    const opened = await openCatalogFixture(browser, (payload) => {
      Object.assign(payload.items[0], { is_jav: true, code: 'ABC-123', display_code: 'ABC-123', has_cover: true });
    });
    const { page } = opened;
    const ratio = (index: number) => page.locator('#grid [data-media-grid] > [data-media-card][data-id]').nth(index).locator('[data-media-pic]')
      .evaluate((element) => element.getBoundingClientRect().width / element.getBoundingClientRect().height);
    const choice = (value: string) => page.locator(`#count input[name="home-layout"][value="${value}"]`);
    try {
      assert.equal(await choice('small').isChecked(), true, '首页版式默认不是小图');
      assert.ok(Math.abs(await ratio(0) - 16 / 9) < 0.05, '小图下番号卡不是 16:9');
      await choice('big').check({ force: true });
      assert.ok(Math.abs(await ratio(0) - 0.75) < 0.05, '大图下番号卡没有拉成正封比例');
      assert.ok(Math.abs(await ratio(1) - 16 / 9) < 0.05, '大图把非番号卡也拉长了');
      // 两张卡同在首行：普通视频卡按自己的内容定高，悬停面不铺进番号卡撑出来的那截空白。
      const box = (index: number) => page.locator('#grid [data-media-grid] > [data-media-card][data-id]').nth(index)
        .evaluate((element) => ({ top: element.getBoundingClientRect().top, height: element.getBoundingClientRect().height }));
      const [jav, plain] = [await box(0), await box(1)];
      assert.ok(Math.abs(jav.top - plain.top) < 1, '前两张卡不在同一行，量不到撑高');
      assert.ok(plain.height < jav.height - 40, '普通视频卡被同行的番号卡撑到整行高');
      // `visit()` 的初始化脚本每次导航都重写设置，刷新验不了；直接读存下来的那份。
      const saved = await page.evaluate(() => JSON.parse(localStorage.getItem('peach.settings.v1') || '{}'));
      assert.equal(saved.homeLayout, 'big', '首页版式没有存下来');
    } finally {
      await opened.close();
    }
  });

  /* 骨架是列表回来之前那一屏的形状预告：JAV 默认大图，卡片是 3:4 的正封，骨架照 16:9
     铺的话，内容一到整屏卡片都被拉高一截。把列表请求扣住，只看骨架本身。 */
  it('作品骨架的封面比例跟当前版式走：JAV 大图 3:4，首页小图 16:9', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', DESKTOP);
    const { page } = opened;
    await page.route(/\/api\/items\?/, () => {});
    /* 骨架挂上的那一帧可能还没排版（宽高都是 0），量出来是 NaN。等它有了尺寸、且连续两帧
       比例不变再读：量的是这一屏落定后的形状，不是插进 DOM 的那一瞬。 */
    const skeletonRatio = async (path: string) => {
      await page.goto(new URL(path, page.url()).href, { waitUntil: 'load' });
      const handle = await page.waitForFunction(() => {
        const cover = document.querySelector('#grid .catalog-skeleton .skeletoncard i');
        const box = cover?.getBoundingClientRect();
        if (!box || !box.width || !box.height) return false;
        const ratio = box.width / box.height;
        const holder = window as unknown as { skeletonRatioSeen?: number };
        const settled = holder.skeletonRatioSeen === ratio;
        holder.skeletonRatioSeen = ratio;
        return settled && ratio;
      }, undefined, { polling: 'raf', timeout: 15_000 });
      return Number(await handle.jsonValue());
    };
    try {
      assert.ok(Math.abs(await skeletonRatio('/?jav=1') - 0.75) < 0.05, 'JAV 大图下骨架封面不是正封比例');
      assert.ok(Math.abs(await skeletonRatio('/') - 16 / 9) < 0.05, '首页小图下骨架封面不是 16:9');
    } finally {
      await opened.close();
    }
  });

  it('卡片悬停反馈不在封面像素上描边', { timeout: 60_000 }, async () => {
    const opened = await openCatalog(browser);
    try {
      const card = opened.page.locator('#grid [data-media-card]').first();
      const picture = card.locator('[data-media-pic]');
      await card.hover();
      const overlay = await picture.evaluate((element) => {
        const style = getComputedStyle(element, '::after');
        return { content: style.content, borderWidth: style.borderTopWidth };
      });
      assert.equal(overlay.content, 'none', '悬停伪元素仍覆盖在封面像素上');
      assert.equal(overlay.borderWidth, '0px', '悬停边线仍污染圆角边缘像素');
      assert.match(await card.evaluate((element) => getComputedStyle(element).boxShadow),
        /0px 0px 0px 8px/, '悬停底色没有在卡片四周向外多铺 8px');
      assert.equal(await card.locator('[data-media-later]').evaluate(
        (element) => getComputedStyle(element).opacity), '1', '移除描边后没有保留悬停反馈');
    } finally {
      await opened.close();
    }
  });

  it('馆藏卡片的字取页面正文那一档，角标、悬停控件、进度条、竖屏带、Mix 与回收站卡面按定下的样子画', { timeout: 90_000 }, async () => {
    /* 演示库凑不出回收站里的非视频资源：回收站那一页把第二条换成一个压缩包。
       目录那一页给前三条挂半程观看进度，量进度条的颜色。 */
    const opened = await openCatalogFixture(browser, (payload, url) => {
      if (url.searchParams.get('state') !== 'trash') {
        for (const item of payload.items.slice(0, 3)) Object.assign(item, { duration: 600, play_seconds: 300 });
        return;
      }
      const item = payload.items[1];
      if (!item) throw new Error('演示目录不够两条');
      Object.assign(item, { medium: 'archive', name: '演示资料.zip', disposal: 'trash' });
      payload.items[0].disposal = 'trash';
    });
    const { page } = opened;
    /* 岛根是 `line-height:1.5`，卡里没写行高的格子会继承它；旧卡读的是页面正文 14px/20px。
       取值用同一个岛根下的空元素量 token，不在断言里抄像素。 */
    const readStyles = (selectors: Record<string, string>) => page.evaluate((wanted) => {
      const root = document.querySelector('#grid .peach-react')!;
      const pick = (element: Element | null) => {
        if (!element) return null;
        const style = getComputedStyle(element);
        return { fontSize: style.fontSize, lineHeight: style.lineHeight, fontFamily: style.fontFamily,
          letterSpacing: style.letterSpacing, minHeight: style.minHeight, padding: style.padding,
          display: style.display, place: `${style.alignItems} ${style.justifyItems}`, color: style.color,
          background: style.backgroundColor, borderWidth: style.borderTopWidth, borderColor: style.borderTopColor,
          leftRadius: style.borderTopLeftRadius, width: style.width, opacity: style.opacity };
      };
      const probe = (css: string) => {
        const element = document.createElement('div');
        element.style.cssText = css;
        root.append(element);
        const value = pick(element)!;
        element.remove();
        return value;
      };
      return {
        body: probe('font: var(--board-body)'), caption: probe('font: var(--board-caption)'),
        md: probe('font-size: var(--fs-md)'), muted: probe('color: var(--muted)'), text: probe(''),
        ground: probe('background: var(--ground)'), tungsten: probe('background: var(--tungsten)'),
        overlay: probe('background: var(--overlay-5); border: 1px solid var(--border-10)'),
        ...Object.fromEntries(Object.entries(wanted).map(([key, selector]) => [key, pick(root.querySelector(selector))])),
      };
    }, selectors);
    try {
      await page.locator('#grid [data-shorts-strip]').first().waitFor({ timeout: 10_000 });
      await page.locator('#grid [data-media-grid] > [data-media-card] [data-media-progress]').first().waitFor({ timeout: 10_000 });
      const catalog = await readStyles({
        card: '[data-media-grid] > [data-media-card]',
        badge: '[data-media-grid] > [data-media-card] [data-media-badge]',
        shorts: '[data-shorts-strip] > h2',
        mix: '[data-media-grid] > [data-mix-card]',
        mixTitle: '[data-media-grid] > [data-mix-card] [data-mix-title]',
        mixGlyph: '[data-media-grid] > [data-mix-card] [data-mix-glyph]',
        strip: '[data-shorts-strip]',
        progress: '[data-media-grid] > [data-media-card] [data-media-progress] > i',
        seekGlyph: '[data-media-grid] > [data-media-card] [data-media-seek] svg',
        laterButton: '[data-media-grid] > [data-media-card] [data-media-later] button',
        laterGlyph: '[data-media-grid] > [data-media-card] [data-media-later] svg',
      });
      const { body, caption, md, card, badge, shorts, mix, mixTitle } = catalog;
      /* 竖屏带靠底色和网格区分，不描线；宽屏上往左铺过侧栏轨道，贴视口那一侧不留圆角。 */
      assert.deepEqual([catalog.strip?.background, catalog.strip?.borderWidth], [catalog.ground.background, '0px'],
        '竖屏带不是页面底色那一张面，或者描了一圈线');
      assert.equal(catalog.strip?.leftRadius, '0px', '宽屏上竖屏带贴视口的那一侧还留着圆角');
      const edges = await page.evaluate(() => ({
        strip: document.querySelector('#grid [data-shorts-strip]')!.getBoundingClientRect().left,
        grid: document.querySelector('#grid [data-media-grid]')!.getBoundingClientRect().left,
      }));
      assert.ok(edges.strip < edges.grid, `竖屏带左缘 ${edges.strip} 没有越过网格左缘 ${edges.grid} 铺到侧栏底下`);
      /* 沉浸模式是一叠竖着翻的卡，入口用叠卡那一枚字形，不和别的动作共用。 */
      assert.equal(await page.locator('#grid [data-shorts-enter] svg use').first().getAttribute('href'), '#i-gallery-vertical-end',
        '竖屏带的「进入沉浸模式」换了字形');
      assert.equal(catalog.progress?.background, catalog.tungsten.background, '观看进度条不是钨丝蓝');
      assert.deepEqual([catalog.mixGlyph?.background, catalog.mixGlyph?.borderWidth, catalog.mixGlyph?.borderColor],
        [catalog.overlay.background, '1px', catalog.overlay.borderColor], 'Mix 署名位那枚字形不是半透明底加细边');
      /* 居中的快退快进和右下角「稍后看」是同一种控件，只是尺寸不同：58px 配 34px 图标，36px 配 21px。 */
      assert.deepEqual([catalog.seekGlyph?.width, catalog.laterButton?.width, catalog.laterGlyph?.width], ['34px', '36px', '21px'],
        '悬停控件的尺寸和图标比例变了');
      const denseShort = await page.evaluate(() => {
        document.body.dataset.density = 'dense';
        const width = getComputedStyle(document.querySelector('#grid [data-shorts-strip] [data-media-card]')!).width;
        delete document.body.dataset.density;
        return width;
      });
      assert.equal(denseShort, '107px', '密集模式下竖屏带里的卡没有跟着缩到 214px 的一半');
      assert.deepEqual([card?.fontSize, card?.lineHeight], ['14px', '20px'], '作品卡的字不是页面正文那一档，岛根的 1.5 行高漏了进来');
      assert.deepEqual([badge?.fontSize, badge?.lineHeight], [caption.fontSize, caption.lineHeight], '来源角标的字不是 caption 那一档');
      assert.equal(badge?.minHeight, '24px', '来源角标矮于 24px');
      assert.deepEqual([shorts?.fontFamily, shorts?.lineHeight], [body.fontFamily, '20px'], '竖屏带标题的字体或行高不同页面正文');
      assert.ok(mix && mixTitle, '夹具目录里没有插进 Mix');
      assert.deepEqual([mix.fontSize, mix.lineHeight], ['14px', '20px'], '网格里的 Mix 卡没取页面正文那一档');
      assert.equal(mixTitle.letterSpacing, 'normal', '网格里的 Mix 标题带着字距');
      assert.ok(Math.abs(parseFloat(mixTitle.lineHeight) - parseFloat(md.fontSize) * 1.45) < .5,
        `网格里的 Mix 标题行高 ${mixTitle.lineHeight}，不是 --fs-md 的 1.45 倍`);

      await page.goto(new URL('/trash', page.url()).href, { waitUntil: 'load' });
      await page.locator('#grid [data-media-card][data-variant="resource"]').first().waitFor({ timeout: 15_000 });
      await settle(page);
      const trash = await readStyles({
        meta: '[data-media-grid] > [data-media-card] [data-media-meta]',
        glyph: '[data-variant="resource"] [data-media-glyph]',
        kind: '[data-variant="resource"] [data-media-kind-glyph]',
      });
      assert.equal(trash.meta?.padding, '8px', '回收站卡的元信息区不是网格卡那 8px 内边距');
      assert.deepEqual([trash.glyph?.display, trash.glyph?.place, trash.glyph?.color], ['grid', 'center center', trash.muted.color],
        '回收站资源卡封面格里的字形没有居中或不是次要文字色');
      assert.deepEqual([trash.kind?.display, trash.kind?.place, trash.kind?.color], ['grid', 'center center', trash.text.color],
        '回收站资源卡头像位的字形没有居中或不是正文色');
      /* 悬停扫视层是壳插进封面格的 `img.hvframes`：待删卡的灰化要连它一起，否则悬停时整卡「复活」成正常色。 */
      const scan = await page.locator('#grid [data-media-card][data-pending-delete]:not([data-variant="resource"]) [data-media-pic]')
        .first().evaluate((pic) => {
          const layer = document.createElement('img');
          layer.className = 'hvframes';
          pic.append(layer);
          const filter = getComputedStyle(layer).filter;
          layer.remove();
          return filter;
        });
      assert.match(scan, /grayscale\(0\.9\)/, '待删卡的悬停扫视层没有跟着灰化');
      /* 待删卡整块压暗：元信息区降透明度，封面两侧那层模糊垫底也要重写一遍 blur 再灰化，
         `filter` 不叠加，只写灰化会把模糊冲掉。 */
      const pending = await page.locator('#grid [data-media-card][data-pending-delete]:not([data-variant="resource"])')
        .first().evaluate((card) => ({
          meta: getComputedStyle(card.querySelector('[data-media-meta]')!).opacity,
          backdrop: getComputedStyle(card.querySelector('[data-media-pic]')!, '::before').filter,
        }));
      assert.equal(pending.meta, '0.58', '待删卡的元信息区没有压暗');
      assert.match(pending.backdrop, /blur\(26px\) grayscale\(0\.9\) brightness\(0\.27\)/, '待删卡封面两侧的模糊垫底没有跟着灰化');
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
        const stack = element.querySelector('[data-media-stack],[data-mix-stack]')!;
        const cover = element.querySelector('[data-media-pic],[data-mix-cover]')!;
        return {
          cover: getComputedStyle(cover).borderTopLeftRadius,
          ground: getComputedStyle(cover).backgroundColor,
          layers: ['::before', '::after'].map((pseudo) => getComputedStyle(stack, pseudo).borderTopLeftRadius),
          faces: element.querySelectorAll('[data-mix-faces]').length,
          preview: Boolean(element.querySelector('[data-media-preview]')),
        };
      });
      await opened.page.locator('[data-media-card][data-part-seed]').first().waitFor({ timeout: 10_000 });
      const part = await shapeOf('[data-media-card][data-part-seed]');
      assert.notEqual(part.cover, '0px', '封面没有圆角，比对失去意义');
      assert.deepEqual(part.layers, [part.cover, part.cover], '分卷卡的叠层纸边和封面不是同一档圆角');
      // 封面格背后压着纸边：格子是空的，纸边线条就从封面没盖住的地方透出来。
      assert.notEqual(part.ground, 'rgba(0, 0, 0, 0)', '叠层卡的封面格是透明的，纸边会透进封面');
      assert.equal(part.faces, 0, '分卷卡仍挂着翻卡面板');
      assert.ok(part.preview, '分卷卡悬停没有分段预览入口');
      if (await opened.page.locator('#grid [data-mix-card]').count()) {
        const mix = await shapeOf('#grid [data-mix-card]');
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
      const card = opened.page.locator('#grid [data-media-card][data-id]').first();
      const opener = card.locator('[data-media-open]');
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

      const nested = card.locator('[data-media-tag]:not(:disabled)').first();
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

  for (const [label, viewport, inset] of [['390px', MOBILE, 12], ['宽屏', DESKTOP, 24]] as const) {
    it(`${label} 下教程浮窗贴着右下角，Toast 让到它上方，批量选择条盖在它上面`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/', viewport);
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
          opened.page.locator('#grid [data-media-card][data-id]').first(),
          opened.page.locator('#postSetupTutorial .post-setup-notification'),
        ]);
        await settle(opened.page);
        /* 批量条平时不在 DOM 里，放出来再在它中心点取最上层元素。放出和量取在同一次同步执行
           里做完：重画网格的 paintSelection 能在空当里把它收回去。窄屏上它横跨整行，一定落在
           教程卡上；宽屏上两者不在同一处，这一条只在窄屏量。 */
        const probe = await opened.page.evaluate(() => {
          const dock = document.getElementById('batchbar')!;
          dock.hidden = false;
          const tutorial = document.querySelector('#postSetupTutorial .post-setup-notification')!;
          const card = tutorial.getBoundingClientRect();
          const box = dock.getBoundingClientRect();
          const x = box.left + box.width / 2;
          const y = box.top + box.height / 2;
          const top = document.elementFromPoint(x, y);
          return { top: card.top, bottom: card.bottom, left: card.left, right: card.right,
            dock: { overlaps: x >= card.left && x <= card.right && y >= card.top && y <= card.bottom,
              tutorialOnTop: !!top && tutorial.contains(top) } };
        });
        assert.ok(Math.abs(probe.bottom - (viewport.height - inset)) <= 1,
          `教程浮窗没有贴着右下角：下沿 ${probe.bottom}，应为 ${viewport.height - inset}`);
        if (viewport.mobile) {
          assert.ok(probe.dock.overlaps, '批量选择条的中心没落在教程浮窗上，这条判据没有量到重叠');
          assert.ok(!probe.dock.tutorialOnTop, '教程浮窗盖住了批量选择条');
        }
        assert.ok(probe.top >= 0 && probe.left >= 0 && probe.right <= viewport.width,
          `教程浮窗越出了 ${viewport.width}px 视口`);

        /* 回执走真的入口发一条不会自己消失的，等栈里每一条都进场停稳再量。演示库刚跑完扫描，
           「扫描与资料采集已完成」随时可能也进栈，所以判据是栈里每一条都在卡上沿之上。 */
        await opened.page.evaluate(async () => {
          const entry = '/dist/peach-ui.js';
          const ui = await import(entry);
          ui.showToast(document.getElementById('toasts'), { success: '', error: '' }, 'e2e-tutorial-lift',
            { html: '已保存配置', alert: false, timeout: 0, action: null });
        });
        await opened.page.locator('#toasts [data-sonner-toast]').first().waitFor();
        await opened.page.waitForFunction(() => [...document.querySelectorAll('#toasts [data-sonner-toast]')]
          .every((node) => node.getAttribute('data-mounted') === 'true' && node.getAnimations().length === 0));
        const stack = await opened.page.evaluate(() => {
          const card = document.querySelector('#postSetupTutorial .post-setup-notification')!.getBoundingClientRect();
          const boxes = [...document.querySelectorAll('#toasts [data-sonner-toast]')].map((node) => node.getBoundingClientRect());
          return { cardTop: card.top, lowest: Math.max(...boxes.map((box) => box.bottom)),
            highest: Math.min(...boxes.map((box) => box.top)) };
        });
        assert.ok(stack.lowest <= stack.cardTop,
          `Toast 压在教程浮窗上：Toast 下沿 ${stack.lowest}，教程上沿 ${stack.cardTop}`);
        assert.ok(stack.highest >= 0, `Toast 被顶出了视口：上沿 ${stack.highest}`);
      } finally {
        await opened.close();
      }
    });
  }

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
          summary: span('#count [data-collection-summary]'),
          filters: span('#count [data-junk-filters]'),
          grid: span('#grid'),
          summaryFace: face('#count [data-collection-summary]'),
          filtersFace: face('#count [data-junk-filters]'),
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
      // 等 island 接管：壳铺的骨架和它等数据时那一版相同，接管之后仍是这一版才算数。
      await opened.page.locator(`${JUNK_COUNT} [data-junk-filters]`).waitFor({ timeout: 15_000 });
      const row = await opened.page.locator('#count').evaluate((node) => ({
        busy: node.getAttribute('aria-busy'),
        filters: node.querySelectorAll('[data-junk-filters] a').length,
        placeholder: node.querySelectorAll('[data-collection-summary] [data-skeleton="count"]').length,
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

  it('垃圾卡处置发出一条批量请求、卡随之离开；换分类不整页跳转', { timeout: 90_000 }, async () => {
    const opened = await openJunkWith(browser, [
      junkItem(9101, 'archive', '推广合集.zip'), junkItem(9102, 'url', '官网.url'), junkItem(9103, 'audio', '广告.mp3'),
    ]);
    try {
      const page = opened.page;
      const cards = page.locator('#grid [data-junk-card]');
      assert.equal(await cards.count(), 3);
      await cards.first().locator('[data-junk-action="dispose"]').click();
      await page.waitForFunction(() => document.querySelectorAll('#grid [data-junk-card]').length === 2, null,
        { timeout: 10_000 });
      assert.deepEqual(opened.state.batches, [{ ids: [9101], operation: 'dispose' }]);
      await page.getByText('已移入回收站', { exact: true }).first().waitFor({ timeout: 5_000 });

      // 分类是 `<a href>`，普通左键由壳改地址重读：整页重载的话，页面上记的这个标记会丢。
      await page.evaluate(() => { (window as { junkStay?: boolean }).junkStay = true });
      await page.locator(`${JUNK_COUNT} [data-junk-kind-link="url"]`).click();
      await page.waitForFunction(() => location.search === '?type=url'
        && document.querySelectorAll('#grid [data-junk-card]').length === 1, null, { timeout: 10_000 });
      assert.equal(await page.evaluate(() => (window as { junkStay?: boolean }).junkStay), true, '换分类整页重载了');
      assert.match(opened.state.reads.at(-1)!, /kind=url/);
      assert.equal(await page.locator(`${JUNK_COUNT} [data-junk-kind-link="url"]`).getAttribute('aria-current'), 'page');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('垃圾卡是一块有边的面：三颗键等宽居中，移入回收站静止就是实底红', { timeout: 90_000 }, async () => {
    const opened = await openJunkWith(browser, [junkItem(9201, 'archive', '推广.zip'), junkItem(9202, 'url', '官网.url')]);
    try {
      const page = opened.page;
      const read = () => page.evaluate(() => {
        const card = document.querySelector('#grid [data-junk-card]')!;
        const keys = [...card.querySelectorAll('[data-junk-action]')].map((button) => {
          const style = getComputedStyle(button);
          const rect = button.getBoundingClientRect();
          return {
            action: (button as HTMLElement).dataset.junkAction, width: Math.round(rect.width), height: Math.round(rect.height),
            justify: style.justifyContent, border: style.borderTopWidth, face: style.backgroundColor, ink: style.color,
            label: getComputedStyle(button.querySelector('[data-junk-label]')!).display,
          };
        });
        const links = [...document.querySelectorAll('#count [data-junk-filters] a')].map((link) => ({
          current: link.getAttribute('aria-current') === 'page', face: getComputedStyle(link).backgroundColor,
          height: Math.round(link.getBoundingClientRect().height),
        }));
        // 卡在 island 里取 oklch，页面底是 rgb：各画一个像素再比，字面不同不等于颜色不同。
        const pixel = (color: string) => {
          const context = document.createElement('canvas').getContext('2d')!;
          context.fillStyle = color;
          context.fillRect(0, 0, 1, 1);
          return [...context.getImageData(0, 0, 1, 1).data].join(',');
        };
        const style = getComputedStyle(card);
        const ground = [document.body, document.documentElement].map((el) => pixel(getComputedStyle(el).backgroundColor))
          .find((value) => !value.endsWith(',0')) ?? '255,255,255,255';
        return { edge: style.borderTopWidth, line: pixel(style.borderTopColor), page: ground, keys, links };
      });
      const red = await tokenColor(page, 'body', '--board-red');
      const wide = await read();
      // 浅色下卡底与页面同为白，卡的轮廓全靠这圈边：边宽 1px、颜色不能跟页面底一样。
      assert.equal(wide.edge, '1px', '垃圾卡没有描边');
      assert.notEqual(wide.line, wide.page, '垃圾卡的边和页面底色同色');
      assert.equal(new Set(wide.keys.map((key) => key.width)).size, 1, `三颗键不等宽：${wide.keys.map((key) => key.width)}`);
      for (const key of wide.keys) {
        assert.equal(key.justify, 'center', `${key.action} 的图标与标签没有居中`);
        assert.equal(key.height, 36, `${key.action} 高 ${key.height}`);
      }
      const dispose = wide.keys.find((key) => key.action === 'dispose')!;
      assert.equal(dispose.face, red, '移入回收站静止态不是实底红');
      assert.equal(dispose.ink, 'rgb(255, 255, 255)');
      for (const key of wide.keys.filter((one) => one.action !== 'dispose')) assert.equal(key.border, '1px', `${key.action} 没有描边`);
      const current = wide.links.filter((link) => link.current);
      assert.equal(current.length, 1);
      assert.ok(wide.links.filter((link) => !link.current).every((link) => link.face === 'rgba(0, 0, 0, 0)'), '未选中的分类不该有底');
      assert.notEqual(current[0]!.face, 'rgba(0, 0, 0, 0)', '选中的分类没有抬底');

      // 紧凑密度下键上只剩图标。
      await page.evaluate(() => { document.body.dataset.density = 'dense' });
      assert.ok((await read()).keys.every((key) => key.label === 'none'), '紧凑密度下键上还有字');
      await page.evaluate(() => { delete document.body.dataset.density });

      // 手机上够手指点：分类与三颗键都到 44px。
      await page.setViewportSize({ width: MOBILE.width, height: MOBILE.height });
      const narrow = await read();
      assert.ok(narrow.keys.every((key) => key.height >= 44), `手机上键高 ${narrow.keys.map((key) => key.height)}`);
      assert.ok(narrow.links.every((link) => link.height >= 44), `手机上分类高 ${narrow.links.map((link) => link.height)}`);
      assert.deepEqual(opened.problems, []);
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

  /* 整行都能点选之后，指着哪一行得看得出来。卡片视图的来源行和表格行走同一条规则；选中行
     有自己的底色，指着它时不换。 */
  it('关注列表指着哪一行哪一行换底色，两种视图都是，选中行的底色不被 hover 盖掉', { timeout: 60_000 }, async () => {
    const opened = await openFollowManage(browser);
    try {
      const page = opened.page;
      const background = (locator: Locator) => locator.evaluate((element) => {
        for (const animation of element.getAnimations()) animation.finish();
        return getComputedStyle(element).backgroundColor;
      });
      /* 勾选框的 input 视觉隐藏在画出来的方框底下，点它要 force，和上面选中底色那条用例一样。 */
      const select = () => page.getByRole('checkbox', { name: '选择 kou · Kemono' })
        .check({ force: true, timeout: 5_000 });
      const card = page.locator('[data-source-divider] > div').first();
      const cardRested = await background(card);
      await card.hover();
      assert.notEqual(await background(card), cardRested, '指着卡片视图的来源行时底色没换');
      await select();
      const cardSelectedHovered = await background(card);
      await page.mouse.move(0, 0);
      const cardSelectedRested = await background(card);
      assert.equal(cardSelectedHovered, cardSelectedRested, '卡片视图选中行指着时换了底色，盖掉了选中态');
      assert.notEqual(cardSelectedRested, cardRested, '卡片视图选中行没有自己的底色');

      await page.locator('button[aria-label="表格视图"]').click({ timeout: 5_000 });
      const row = page.locator('[data-board-data-table] tbody tr').first();
      await row.waitFor({ timeout: 15_000 });
      await page.mouse.move(0, 0);
      const selectedRested = await background(row);
      await row.hover();
      assert.equal(await background(row), selectedRested, '表格视图选中行指着时换了底色，盖掉了选中态');
      await page.getByRole('checkbox', { name: '选择 kou · Kemono' }).uncheck({ force: true, timeout: 5_000 });
      await page.mouse.move(0, 0);
      const rested = await background(row);
      assert.notEqual(selectedRested, rested, '表格视图选中行没有自己的底色');
      await row.hover();
      assert.notEqual(await background(row), rested, '指着表格行时底色没换');
    } finally {
      await opened.close();
    }
  });

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
        ['扫描并补全资料', '更多扫描与采集方式', '开始修复', '预览', '检查死链', '检查文件']);
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
      await page.locator('section[aria-label="扫描与采集"] [data-split-button] > button:first-child:not([data-skeleton-action])')
        .waitFor({ timeout: 15_000 });
      await page.locator('section[aria-label="媒体修复"] footer > button:not([data-skeleton-action])')
        .waitFor({ timeout: 15_000 });
      await settle(page);
      const final = await controlFaces(page, {
        扫描并补全资料: 'section[aria-label="扫描与采集"] [data-split-button] > button:first-child',
        更多方式: 'section[aria-label="扫描与采集"] [data-split-button] > button:last-child',
        开始修复: 'section[aria-label="媒体修复"] footer > button',
      });
      for (const name of Object.keys(sizes)) {
        assert.equal(sizes[name]!.size, final[name]!.size, `${name} 接管时尺寸跳了`);
        assert.match(final[name]!.face, /gradient/, `${name} 接管后没换回蓝色主按钮`);
      }
      const enabled = await page.locator('section[aria-label="扫描与采集"] [data-split-button] > button')
        .evaluateAll((buttons) => buttons.map((button) => (button as HTMLButtonElement).disabled));
      assert.deepEqual(enabled, [false, false], '数据到了扫描键还是禁用的');
    } finally {
      await opened.close();
    }
  });

  it('数据管理卡外的分区标题是 20px 的 Title 2，链接读数照旧版字号与行高', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/data-cleanup', DESKTOP);
    try {
      const page = opened.page;
      await page.locator('#link-manager .link-stat-grid b').first().waitFor({ timeout: 15_000 });
      await page.locator('#resource-sync-title').waitFor({ timeout: 15_000 });
      await settle(page);
      const faces = await page.evaluate(() => {
        const style = (selector: string) => {
          const computed = getComputedStyle(document.querySelector(selector)!);
          return {
            size: computed.fontSize, weight: computed.fontWeight, line: computed.lineHeight,
            top: computed.marginTop, bottom: computed.marginBottom,
          };
        };
        return {
          links: style('#link-manager-title'),
          sync: style('#resource-sync-title'),
          label: style('#link-manager .link-stat-grid span'),
          figure: style('#link-manager .link-stat-grid b'),
        };
      });
      /* 这一页挂在 `#stats` 里，遗留样式表给那里的二级标题定了 24px 与 4px 底距。 */
      for (const [name, heading] of [['链接管理', faces.links], ['资源同步', faces.sync]] as const) {
        assert.equal(heading.size, '20px', `${name}标题字号不是 Title 2`);
        assert.equal(heading.bottom, '0px', `${name}标题带着遗留那 4px 底距`);
      }
      assert.deepEqual([faces.label.size, faces.label.line], ['12px', '20px'], '链接读数的标签不是 12/20');
      assert.deepEqual([faces.figure.size, faces.figure.weight, faces.figure.line], ['20px', '700', '20px'],
        '链接读数的数字不是 20px 粗体、20px 行高');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('可点的卡悬停时铺卡面掺 5% 主文字色的那一档面，不是透明', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/data-cleanup', DESKTOP);
    try {
      const page = opened.page;
      const selector = '.peach-react [data-cleanup-go]';
      const card = page.locator(selector).first();
      await card.waitFor({ timeout: 15_000 });
      await settle(page);
      const rest = await card.evaluate((element) => getComputedStyle(element).backgroundColor);
      await card.hover();
      // 过渡跑完才读：等到底色变了，或三秒后照实读出没变的那个值。
      await page.waitForFunction(([target, before]) =>
        getComputedStyle(document.querySelector(target)!).backgroundColor !== before,
      [selector, rest] as const, { timeout: 3_000 }).catch(() => undefined);
      const hovered = await card.evaluate((element) => getComputedStyle(element).backgroundColor);
      assert.notEqual(hovered, 'rgba(0, 0, 0, 0)', '悬停底色落成了透明：token 在根上就折掉了');
      assert.notEqual(hovered, rest, '悬停没有换面');
      assert.equal(hovered, await tokenColor(page, '.peach-react', '--card-hover'), '悬停底色不是卡面掺 5% 主文字色');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('索引页名册格用遗留卡面那一套：格底 --ground、头像框 --sunk、首字与读数 --muted 配 Bahnschrift，悬停掺 6% 主文字色；页头过滤框与版式切换同为 36px 高，切换两枚共 66px 宽', { timeout: 60_000 }, async () => {
    const opened = await openIndexPage(browser, '/performers');
    try {
      const page = opened.page;
      const selector = '#index [data-index-cell]';
      const cell = page.locator(selector).first();
      const rest = await cell.evaluate((element) => getComputedStyle(element).backgroundColor);
      const face = await page.evaluate(() => {
        const ring = document.querySelector('#index [data-person-ring]')!;
        const initial = document.querySelector('#index [data-person-ring] .ini')!;
        const readout = document.querySelector('#index [data-index-readout]')!;
        return { ring: getComputedStyle(ring).backgroundColor, initial: getComputedStyle(initial).color,
          font: getComputedStyle(initial).fontFamily, readout: getComputedStyle(readout).color };
      });
      assert.equal(rest, await tokenColor(page, 'html', '--ground'), '名册格底不是 --ground');
      assert.equal(face.ring, await tokenColor(page, 'html', '--sunk'), '头像框底不是 --sunk');
      const muted = await page.evaluate(() => {
        const probe = document.createElement('div');
        probe.style.color = 'var(--muted)';
        document.documentElement.append(probe);
        const value = getComputedStyle(probe).color;
        probe.remove();
        return value;
      });
      assert.deepEqual([face.initial, face.readout], [muted, muted], '首字与读数不是 --muted');
      assert.match(face.font, /^Bahnschrift/, '首字不是 Bahnschrift');
      await cell.hover();
      await page.waitForFunction(([target, before]) =>
        getComputedStyle(document.querySelector(target)!).backgroundColor !== before,
      [selector, rest] as const, { timeout: 3_000 }).catch(() => undefined);
      const hovered = await cell.evaluate((element) => getComputedStyle(element).backgroundColor);
      const lifted = await page.evaluate(() => {
        const probe = document.createElement('div');
        probe.style.backgroundColor = 'color-mix(in srgb, var(--ink) 6%, var(--ground))';
        document.documentElement.append(probe);
        const value = getComputedStyle(probe).backgroundColor;
        probe.remove();
        return value;
      });
      assert.equal(hovered, lifted, '名册格悬停不是格底掺 6% 主文字色');
      const head = await page.evaluate(() => {
        const input = document.querySelector('#index [data-index-search] input')!;
        const shell = input.closest('[role="presentation"]')!;
        const toggle = document.querySelector('#index [data-index-layout]')!;
        return { search: getComputedStyle(shell).height, toggle: getComputedStyle(toggle).height,
          width: getComputedStyle(toggle).width };
      });
      assert.deepEqual(head, { search: '36px', toggle: '36px', width: '66px' });
      // 人脸放大把 img 撑得比框还宽再负偏移；Preflight 的 `max-width:100%` 会把它压回框宽。
      const photo = page.locator('#index [data-person-ring] img').first();
      await photo.waitFor({ state: 'attached', timeout: 5_000 });
      await page.waitForFunction(() => document.querySelector('#index [data-person-ring]')?.hasAttribute('data-native-small'),
        undefined, { timeout: 5_000 });
      assert.equal(await photo.evaluate((element) => getComputedStyle(element).maxWidth), 'none');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('索引页换一档 Tabs 时那条蓝线沿弹簧滑过去，不是一跳', { timeout: 60_000 }, async () => {
    const opened = await openIndexPage(browser, '/studios');
    try {
      const page = opened.page;
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      const indicator = page.locator('#index [data-tab-indicator]');
      await page.waitForFunction(() => document.querySelector('#index [data-tab-indicator]')?.hasAttribute('data-ready'),
        undefined, { timeout: 5_000 });
      const motion = await indicator.evaluate((element) => {
        const style = getComputedStyle(element);
        return { property: style.transitionProperty, duration: style.transitionDuration, height: style.height };
      });
      assert.equal(motion.property, 'transform, width');
      assert.notEqual(motion.duration.split(',')[0]!.trim(), '0s', '蓝线没有过渡时长');
      assert.equal(motion.height, '2px');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('播放列表卡：封面后压两层纸边、黑底封面、玻璃徽标、38px 头像叠 22px；标题 32/44，菜单键静止透明', { timeout: 60_000 }, async () => {
    const opened = await openPlaylistsPage(browser);
    try {
      const page = opened.page;
      const look = await page.evaluate(() => {
        const card = document.querySelector('#stats [data-playlist-card="1"]')!;
        const css = (selector: string) => getComputedStyle(card.querySelector(selector)!);
        const stack = card.querySelector('[data-mix-stack]')!;
        const back = getComputedStyle(stack, '::before');
        const mid = getComputedStyle(stack, '::after');
        const title = getComputedStyle(document.querySelector('#stats header h2')!);
        const cover = css('[data-mix-cover]');
        const badge = css('[data-mix-badge]');
        const menu = css('[data-playlist-menu]');
        const blank = getComputedStyle(document.querySelector('#stats [data-playlist-card="3"] [data-mix-cover] > span')!);
        return {
          title: [title.fontSize, title.lineHeight, title.fontWeight],
          gap: getComputedStyle(document.querySelector('#stats [data-playlist-grid]')!).gap,
          back: [back.borderTopWidth, back.inset, back.transform, back.opacity],
          mid: [mid.borderTopWidth, mid.inset, mid.transform, mid.opacity],
          cover: [cover.backgroundColor, cover.borderRadius],
          badge: [badge.backgroundColor, badge.backdropFilter, badge.minHeight, badge.borderRadius, badge.right, badge.bottom],
          avatars: [...card.querySelectorAll('[data-mix-avatars] button')].map((button) => {
            const style = getComputedStyle(button);
            return [style.width, style.marginLeft, style.zIndex];
          }),
          menu: [menu.width, menu.height, menu.borderRadius, menu.backgroundColor],
          blank: [blank.letterSpacing, blank.textTransform],
        };
      });
      assert.deepEqual(look, {
        title: ['32px', '44px', '500'],
        gap: '18px',
        back: ['1px', '0px 12px 8px', 'matrix(1, 0, 0, 1, 0, -7)', '0.54'],
        mid: ['1px', '0px 6px 4px', 'matrix(1, 0, 0, 1, 0, -4)', '0.78'],
        cover: ['rgb(0, 0, 0)', '14px'],
        badge: ['rgba(12, 8, 8, 0.72)', 'blur(10px)', '28px', '10px', '9px', '9px'],
        avatars: [['38px', '0px', '5'], ['38px', '-22px', '4'], ['38px', '-22px', '3']],
        menu: ['30px', '30px', '10px', 'rgba(0, 0, 0, 0)'],
        blank: ['1.44px', 'uppercase'],
      });
      // 指到的头像抬起 4px、放大到 1.05，右边那位朝标题让开 10px。
      await page.locator('#stats [data-playlist-card="1"] [data-mix-avatars] button').first().hover();
      const lifted = await page.evaluate(() => {
        document.getAnimations().forEach((animation) => animation.finish());
        return [...document.querySelectorAll('#stats [data-playlist-card="1"] [data-mix-avatars] button')]
          .slice(0, 2).map((button) => getComputedStyle(button).transform);
      });
      assert.deepEqual(lifted, ['matrix(1.05, 0, 0, 1.05, 0, -4)', 'matrix(1, 0, 0, 1, 10, -1.8)']);
      // 点点点菜单外宽 172px，同旧卡片菜单。
      await page.locator('#stats [data-playlist-card="1"] [data-playlist-menu]').click();
      const panel = page.locator(':has(> [role="dialog"][aria-label="播放列表操作：列表1"])');
      await panel.waitFor({ timeout: 5_000 });
      assert.equal(await panel.evaluate((element) => getComputedStyle(element).width), '172px');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('播放列表页窄屏：页头改竖排，新建框字号 16px 免得 iOS 聚焦时放大', { timeout: 60_000 }, async () => {
    const opened = await openPlaylistsPage(browser, MOBILE);
    try {
      const narrow = await opened.page.evaluate(() => ({
        header: getComputedStyle(document.querySelector('#stats header')!).flexDirection,
        input: getComputedStyle(document.querySelector('#stats [data-playlist-create] input')!).fontSize,
        title: getComputedStyle(document.querySelector('#stats header h2')!).fontSize,
      }));
      assert.deepEqual(narrow, { header: 'column', input: '16px', title: '32px' });
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('标签多选坞出现时页底让出 96px；在线词表的类型色走上游 tag_type 那一套', { timeout: 60_000 }, async () => {
    const opened = await openIndexPage(browser, '/tags');
    try {
      const page = opened.page;
      await page.locator('#selectMode').click({ timeout: 5_000 });
      await page.locator('#index [data-alpha-tag]').nth(0).click({ timeout: 5_000 });
      await page.locator('#index [data-alpha-tag]').nth(1).click({ timeout: 5_000 });
      const dock = page.locator('[data-selection-dock]');
      await dock.waitFor({ timeout: 5_000 });
      const padding = await page.evaluate(() =>
        getComputedStyle(document.querySelector('#index .peach-react')!).paddingBottom);
      assert.equal(padding, '96px', '选择坞盖住了最后一行标签');
      await page.locator('#index [role="tab"][data-tab="online"]').click({ timeout: 5_000 });
      const dot = page.locator('#index [data-alpha-tag][data-tag-cat="r34-artist"] [data-tag-dot]');
      await dot.waitFor({ timeout: 5_000 });
      assert.equal(await dot.evaluate((element) => getComputedStyle(element).backgroundColor), 'rgb(227, 108, 108)');
      assert.equal(await dock.count(), 0, '在线词表不给多选坞');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('标签云一枚里名字与计数只隔一个空格宽；筛选浮层的 Aa 字形摆进 16×16 的框', { timeout: 60_000 }, async () => {
    const opened = await openIndexPage(browser, '/tags?view=cloud');
    try {
      const page = opened.page;
      const spacing = await page.locator('#index [data-tag-chip]').first().evaluate((chip) => {
        // 名字那段文字按字符切开量：字的右缘到计数左缘，与末尾那个空格自己画出来的宽度相比。
        const name = chip.firstChild!;
        const end = name.textContent!.trimEnd().length;
        const box = (from: number, to: number) => {
          const part = document.createRange();
          part.setStart(name, from);
          part.setEnd(name, to);
          return part.getBoundingClientRect();
        };
        const count = chip.querySelector('[data-tag-n]')!.getBoundingClientRect();
        return { gap: count.left - box(0, end).right, space: box(end, name.textContent!.length).width,
          columnGap: getComputedStyle(chip).columnGap };
      });
      assert.equal(spacing.columnGap, 'normal', '名字与计数之间不另加 flex 间距');
      assert.ok(spacing.space > 2 && Math.abs(spacing.gap - spacing.space) < 0.5,
        `名字与计数隔了 ${spacing.gap}px，一个空格是 ${spacing.space}px`);
      const glyph = page.locator('#index svg:has(use[href="#i-text-aa"])');
      assert.deepEqual(await glyph.evaluate((element) => {
        const style = getComputedStyle(element);
        return [style.width, style.height];
      }), ['16px', '16px']);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('重复文件的汇总条是玻璃面，组卡 14px 圆角、组头 20px 内边距，每行上方一条 1px 分隔线', { timeout: 60_000 }, async () => {
    const opened = await openDuplicates(browser);
    try {
      const faces = await opened.page.evaluate(() => {
        const glass = getComputedStyle(document.querySelector('[data-filter-glass]')!);
        const group = document.querySelector('#stats section[aria-label="DUPE-002"]')!;
        const head = group.firstElementChild!;
        const card = getComputedStyle(group);
        const header = getComputedStyle(head);
        const code = getComputedStyle(head.querySelector('b')!);
        return {
          glass: { filter: glass.backdropFilter, padding: glass.padding, height: glass.height },
          card: { radius: card.borderRadius, overflow: card.overflow, face: card.backgroundColor },
          head: { padding: header.padding, face: header.backgroundColor, size: code.fontSize, weight: code.fontWeight },
          rows: [...group.querySelectorAll('.duplicate-row')].map((row) => {
            const computed = getComputedStyle(row);
            return [computed.borderTopWidth, computed.padding];
          }),
        };
      });
      assert.match(faces.glass.filter, /blur\(/, '汇总条没有背景模糊，不是玻璃面');
      assert.deepEqual([faces.glass.padding, faces.glass.height], ['10px 16px', '50px']);
      assert.deepEqual([faces.card.radius, faces.card.overflow], ['14px', 'hidden'], '组卡圆角或裁切不对');
      assert.notEqual(faces.head.face, faces.card.face, '组头和组卡同色，番号那一行分不出来');
      assert.deepEqual([faces.head.padding, faces.head.size, faces.head.weight], ['20px', '20px', '500']);
      assert.deepEqual(faces.rows, [['1px', '16px 20px'], ['1px', '16px 20px']],
        '组内每一行上方不是 1px 分隔线，或内边距不是 16/20');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('整页空态沉一档底色、20px 圆角、至少 320px 高，图标装进 54px 描边方框；卡里的空态不带方框', { timeout: 60_000 }, async () => {
    // 演示库在一轮里凑得出重复组，桩成空的才一定落到整页空态上。
    const opened = await visit(browser, '/duplicates', DESKTOP);
    try {
      const page = opened.page;
      await page.route('**/api/duplicates?**', (route) => route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ total: 0, files: 0, reclaimable: 0, groups: [] }),
      }));
      await page.reload({ waitUntil: 'load' });
      await page.locator('#stats [data-empty-state]').waitFor({ timeout: 15_000 });
      await settle(page);
      const face = await page.evaluate(() => {
        const root = document.querySelector('#stats [data-empty-state]')!;
        const glyph = root.querySelector('svg')!;
        const box = glyph.parentElement!;
        const shell = getComputedStyle(root);
        const frame = getComputedStyle(box);
        const title = getComputedStyle(root.querySelector('h3')!);
        const copy = getComputedStyle(root.querySelector('p')!);
        return {
          shell: { face: shell.backgroundColor, line: shell.borderTopColor, width: shell.borderTopWidth,
            radius: shell.borderTopLeftRadius, minHeight: shell.minHeight },
          boxed: box !== root,
          frame: { width: frame.width, height: frame.height, radius: frame.borderTopLeftRadius,
            line: frame.borderTopWidth, glyph: getComputedStyle(glyph).width },
          title: [title.fontSize, title.fontWeight], copy: [copy.maxWidth, copy.lineHeight],
        };
      });
      assert.equal(face.shell.face, await tokenColor(page, '.peach-react', '--color-background-secondary-default'),
        '整页空态没有沉一档底色');
      assert.equal(face.shell.line, await tokenColor(page, '.peach-react', '--color-separator-border'), '外框不是分隔线色');
      assert.deepEqual([face.shell.width, face.shell.radius, face.shell.minHeight], ['1px', '20px', '320px']);
      assert.ok(face.boxed, '整页空态的图标没有装进方框');
      assert.deepEqual(face.frame, { width: '54px', height: '54px', radius: '20px', line: '1px', glyph: '32px' });
      assert.deepEqual(face.title, ['14px', '600']);
      assert.deepEqual(face.copy, ['340px', '20.15px']);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
    // 卡里那一档（活动页没有任务记录）图标直接挂在空态上，外面没有方框。
    const activity = await visit(browser, '/activity', DESKTOP);
    try {
      await activity.page.route('**/api/tasks', (route) => route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ available: true, running: [], skipped: [], finished: [] }),
      }));
      await activity.page.reload({ waitUntil: 'load' });
      const empty = activity.page.locator('[data-empty-state]');
      await empty.waitFor({ timeout: 15_000 });
      await settle(activity.page);
      assert.equal(await empty.evaluate((root) => root.querySelector('svg')!.parentElement === root), true,
        '卡里的空态也套了图标方框');
      assert.deepEqual(activity.problems, []);
    } finally {
      await activity.close();
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
          // 落在首屏以下的目标（数据管理的整理卡）先滚进视口：`elementFromPoint` 只认视口里的点。
          await node.scrollIntoViewIfNeeded();
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

  /* 建议由这里给，两组共 30 条，两个视口下字段下方都装不下。桌面取 1280×1000，
     字段下缘在视口中段偏下，正是只能往下开、又放不全的那种处境。 */
  for (const viewport of [{ ...DESKTOP, height: 1000 }, MOBILE]) {
    it(`添加关注的建议下拉压在字段下方剩下的空间里，装不下在菜单内滚，选中行滚进可见区（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openFollowManage(browser, viewport);
      try {
        const { page } = opened;
        await page.route(/\/api\/follow\/suggest\?/, (route) => route.fulfill({ json: {
          q: 'bulging',
          groups: [['归档站', 18], ['站方分类', 12]].map(([label, count]) => ({
            kind: String(label), label,
            items: Array.from({ length: Number(count) }, (_, at) => ({
              value: `bulging ${label} ${at + 1}`, matched: 'Kemono', n: 120 - at,
            })),
          })),
        } }));
        await followTab(opened, '添加关注');
        const before = await page.evaluate(() => document.documentElement.scrollHeight);
        const input = page.getByRole('textbox', { name: '来源链接、名字或 id' });
        await input.click({ timeout: 5_000 });
        await input.fill('bulging');
        const menu = page.locator('[aria-label="来源建议"]');
        await menu.locator('button').nth(29).waitFor({ state: 'attached', timeout: 10_000 });
        const measure = () => menu.evaluate((element) => {
          for (const animation of element.getAnimations({ subtree: true })) animation.finish();
          const box = element.getBoundingClientRect();
          const field = element.ownerDocument.querySelector('input[aria-label="来源链接、名字或 id"]')!
            .getBoundingClientRect();
          const row = element.querySelector('[aria-current="true"]')?.getBoundingClientRect();
          return {
            top: box.top, bottom: box.bottom, fieldBottom: field.bottom, viewport: innerHeight,
            overflowing: element.scrollHeight > element.clientHeight,
            overscroll: getComputedStyle(element).overscrollBehaviorY,
            page: document.documentElement.scrollHeight, pageWidth: document.documentElement.scrollWidth,
            width: innerWidth, y: scrollY,
            row: row ? { top: row.top, bottom: row.bottom } : null,
          };
        });
        const open = await measure();
        assert.ok(open.bottom <= open.viewport + .5, `下拉底边 ${open.bottom} 越出视口 ${open.viewport}`);
        assert.ok(open.top >= open.fieldBottom, `下拉上沿 ${open.top} 盖住了字段（下缘 ${open.fieldBottom}）`);
        assert.ok(open.overflowing, '30 条建议没有让下拉溢出，这条用例没练到内滚');
        assert.equal(open.overscroll, 'contain', '下拉滚到头会带着页面一起滚');
        assert.ok(open.page <= before, `下拉把页面从 ${before} 撑到 ${open.page}`);
        assert.ok(open.pageWidth <= open.width, `页面被撑出横向滚动：${open.pageWidth} > ${open.width}`);

        // 走到最后一条：它在初始可见区外面，得被滚进来，页面本身不动。
        for (let step = 0; step < 30; step++) await input.press('ArrowDown');
        const last = await measure();
        assert.ok(last.row, '上下键没有选中任何一行');
        assert.ok(last.row.top >= last.top - .5 && last.row.bottom <= last.bottom + .5,
          `选中行 ${last.row.top}–${last.row.bottom} 不在下拉可见区 ${last.top}–${last.bottom} 内`);
        assert.equal(last.y, open.y, '选中行滚进可见区时把页面也滚了');
        await input.press('ArrowDown');
        const first = await measure();
        assert.ok(first.row && first.row.top >= first.top - .5, '绕回第一条后它没有滚回可见区');
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

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
      const mark = opened.page.locator('[data-entry-marks] a[data-entry-mark]').first();
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
        card: getComputedStyle(element.closest('[data-entity-card]')!).backgroundColor,
      }));
      assert.notEqual(faces.mark, 'rgba(0, 0, 0, 0)', '悬停没有垫底');
      assert.notEqual(faces.mark, faces.card, '悬停底色和资料卡同色，看不出来');
      const toggle = opened.page.getByRole('switch', { name: '订阅新作' });
      assert.equal(await toggle.count(), 1, '资料卡上没有订阅新作开关');
      assert.equal(await toggle.isChecked(), false);
      const feed = opened.page.locator('[data-entry-feed]');
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
        const feed = page.locator('[data-entry-feed]');
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
            clippedBy, covered, below: box.top >= document.querySelector('[data-entry-feed]')!.getBoundingClientRect().bottom };
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
        const debut = await opened.page.locator('[data-entity-facts] dd[title]').evaluate((dd) => ({
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
      const line = await page.locator('[data-entity-alias]').evaluate((alias) => ({
        glyphs: [...alias.querySelectorAll(':scope > [data-meta-item] > svg use')].map((use) => use.getAttribute('href')),
        names: [...alias.querySelectorAll('[data-alias-names] > span')].map((span) => span.textContent!.trim()),
        more: alias.querySelector('[data-hero-more="alias"]')?.textContent?.trim() ?? '',
        agency: alias.querySelector('a[data-agency]')?.textContent?.trim() ?? '',
      }));
      assert.deepEqual(line.glyphs, ['#i-film', '#i-briefcase', '#i-id-card'], '名字那一行的三项不是视频、事务所、别名');
      assert.deepEqual(line.names, ['しのだゆう', '篠崎ゆう子', '高木早希', '橋本真紀'], '读音没有排在别名最前，或别名不是前三个');
      assert.equal(line.more, '+4', '「+N」数的不是剩下那几个别名');
      assert.equal(line.agency, 'New Actor eXperience');
      const links = await page.locator('[data-entity-links] a').evaluateAll((anchors) => anchors.map((a) => {
        const box = a.getBoundingClientRect();
        return { size: `${Math.round(box.width)}x${Math.round(box.height)}`, kind: a.getAttribute('data-link'), title: a.getAttribute('title'),
          name: a.getAttribute('aria-label') ?? '', visibleText: a.querySelector('[data-link-label]') !== null };
      }));
      assert.equal(links.length, 3);
      for (const link of links) {
        assert.deepEqual([link.size, link.kind, link.visibleText], ['36x36', 'icon', false], `${link.title} 不是纯图标方块`);
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
        const more = page.locator('[data-hero-more="alias"]');
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
            title: element.querySelector('[data-hero-pop-head]')?.textContent?.trim(),
            groups: [...element.querySelectorAll('dt')].map((dt) => dt.textContent!.trim()),
            face: getComputedStyle(element).backgroundColor,
            shadow: getComputedStyle(element).boxShadow,
          };
        });
        assert.equal(shown.shadow, await popmenuShadow(page), '别名浮层的落影和 .popmenu 不是同一副');
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

  // 名字右边那枚按钮往左开的话，260px 的菜单越过名字压在头像上（用户报过）。
  for (const viewport of [DESKTOP, MOBILE]) {
    it(`名字与别名菜单从按钮左缘往右开，不盖住页头头像（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openProfiledPerformer(browser, viewport);
      try {
        const page = opened.page;
        await page.locator('[data-namepick-toggle]').click();
        await page.locator('[data-namepick-menu]').waitFor({ state: 'visible', timeout: 5_000 });
        const box = await page.evaluate(() => {
          const rect = (selector: string) => {
            const b = document.querySelector(selector)!.getBoundingClientRect();
            return { left: b.left, right: b.right, top: b.top, bottom: b.bottom };
          };
          return { menu: rect('[data-namepick-menu]'), portrait: rect('[data-entity-portrait]'), toggle: rect('[data-namepick-toggle]') };
        });
        const overlaps = box.menu.left < box.portrait.right && box.menu.right > box.portrait.left
          && box.menu.top < box.portrait.bottom && box.menu.bottom > box.portrait.top;
        assert.equal(overlaps, false, `名字菜单盖住了头像：${JSON.stringify(box)}`);
        assert.ok(box.menu.left >= 0 && box.menu.right <= viewport.width, '名字菜单越出了视口');
        if (!viewport.mobile) assert.ok(Math.abs(box.menu.left - box.toggle.left) < 1, '宽屏下菜单没有对齐按钮左缘');
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  for (const [viewport, split] of [[WIDE, true], [MOBILE, false]] as const) {
    it(`搜索下拉按种类分页签；宽屏分两栏、人名带头像与近作、视频排成封面格，窄屏一栏（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/', viewport);
      try {
        const page = opened.page;
        const kinds = await stubSuggest(page);
        await expectBody(page, '/', [page.locator('#grid [data-media-card][data-id]').first()]);
        await settle(page);
        if (viewport.mobile) await page.locator('#searchBtn').click();
        await page.locator('#q').fill(SUGGEST.q);
        const menu = page.locator('#searchMenu');
        await menu.locator('.searchperson').first().waitFor({ state: 'visible', timeout: 5_000 });
        const shown = await page.evaluate(() => {
          const menuBox = document.querySelector('#searchMenu')!.getBoundingClientRect();
          const results = document.querySelector<HTMLElement>('#searchMenu .searchresults')!;
          const columns = [...results.querySelectorAll(':scope > .searchcol')];
          const person = document.querySelector('#searchMenu .searchperson')!;
          return {
            tabs: [...document.querySelectorAll('#searchMenu [role="tab"]')].map((tab) => tab.textContent!.trim()),
            tracks: getComputedStyle(results).gridTemplateColumns.split(' ').filter((track) => track !== 'none').length,
            divider: getComputedStyle(results, '::before').content,
            dividerHeight: parseFloat(getComputedStyle(results, '::before').height),
            resultsHeight: results.getBoundingClientRect().height,
            right: columns.at(-1)!.querySelector('.searchgroup')?.getAttribute('data-kind'),
            videoGrid: getComputedStyle(document.querySelector('#searchMenu [data-kind="asset"] .searchitems')!).display,
            peeks: getComputedStyle(person.querySelector('.searchpeeks')!).display,
            peekCount: person.querySelectorAll('.searchpeek').length,
            sub: person.querySelector('.searchsub')!.textContent,
            face: person.querySelector('.searchface img')?.getAttribute('src'),
            inView: menuBox.left >= 0 && menuBox.right <= innerWidth,
            edges: [Math.round(menuBox.left), Math.round(innerWidth - menuBox.right)],
          };
        });
        assert.deepEqual(shown.tabs, ['全部', '女优2', '厂牌1', '视频12'], '页签不是「全部」加各类命中数');
        assert.equal(shown.tracks, split ? 2 : 0, split ? '宽屏下拉没有分两栏' : '窄屏下拉不该分栏');
        assert.equal(shown.divider, split ? '""' : 'none', split ? '宽屏两栏之间没有分隔线' : '窄屏一栏不该有分隔线');
        if (split) {
          assert.ok(Math.abs(shown.dividerHeight - shown.resultsHeight) <= 1,
            `分隔线高 ${shown.dividerHeight}px，两栏高 ${shown.resultsHeight}px`);
        }
        assert.equal(shown.right, 'asset', '视频不在最后一栏');
        assert.equal(shown.videoGrid, split ? 'grid' : 'block', split ? '宽屏视频没排成封面格' : '窄屏视频该一行一部');
        assert.equal(shown.peeks, split ? 'flex' : 'none', split ? '宽屏人名一行没摆近作' : '窄屏人名一行不摆近作');
        assert.equal(shown.peekCount, 4);
        assert.equal(shown.sub, '128 个视频 · Capsule Agency');
        assert.equal(shown.face, '/entity-image?kind=performer&id=90301&thumb=1');
        assert.ok(shown.inView, '下拉栏越出了视口');
        // 窄屏下拉栏盖过返回键那一列，和顶栏两侧一样各留 8，不缩进到搜索框底下。
        if (viewport.mobile) assert.deepEqual(shown.edges, [8, 8], '窄屏下拉栏两侧留白不是 8');
        const page_ = await layout(page);
        assert.ok(page_.scrollWidth <= page_.viewportWidth, `下拉把页面撑出了横向滚动：${page_.offenders.join('，')}`);

        await menu.getByRole('tab', { name: /^女优/ }).click();
        await page.waitForFunction(() => document.querySelectorAll('#searchMenu .searchgroup[data-kind]').length === 1);
        assert.equal(await menu.isVisible(), true, '点页签把下拉栏收掉了');
        assert.ok(kinds.includes('performer'), '选了一类没有按这一类去拉满');
        assert.equal(await menu.getByRole('tab', { name: /^女优/ }).getAttribute('aria-selected'), 'true');

        // 人名那一行点开的是资料页，不是按名字再搜一遍。
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
        await page.waitForURL(/\/performers\//, { timeout: 5_000 });
        assert.equal(decodeURIComponent(new URL(page.url()).pathname), '/performers/涼森れむ');
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  it('只看视频时封面格按列均分铺满整栏，每格有宽度上限', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', WIDE);
    try {
      const page = opened.page;
      await stubSuggest(page);
      await expectBody(page, '/', [page.locator('article[data-media-card][data-id]').first()]);
      await settle(page);
      await page.locator('#q').fill(SUGGEST.q);
      const menu = page.locator('#searchMenu');
      await menu.locator('.searchperson').first().waitFor({ state: 'visible', timeout: 5_000 });
      await menu.getByRole('tab', { name: /^视频/ }).click();
      await page.waitForFunction(() => document.querySelectorAll('#searchMenu .searchgroup[data-kind]').length === 1);
      const grid = await page.evaluate(() => {
        const items = document.querySelector('#searchMenu [data-kind="asset"] .searchitems')!;
        const box = items.getBoundingClientRect();
        const cards = [...items.querySelectorAll('.searchwork')].map((card) => card.getBoundingClientRect());
        return {
          rows: new Set(cards.map((card) => Math.round(card.top))).size,
          widths: cards.map((card) => Math.round(card.width)),
          slack: Math.round(box.right - cards.at(-1)!.right),
        };
      });
      assert.equal(grid.rows, 1, '五部视频没排在同一行');
      assert.ok(grid.slack <= 1, `封面格右侧空出 ${grid.slack}px`);
      assert.ok(grid.widths.every((width) => width >= 96 && width <= 242), `封面宽度越出 96～242：${grid.widths.join('、')}`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('资料页照片墙：1280 宽小图 4 列、大图 2 列，手机 2 列；固定版式是方格，瀑布流按列填；格子是一块等图的空底', { timeout: 90_000 }, async () => {
    const opened = await openPhotoWall(browser);
    try {
      const { page } = opened;
      // 默认瀑布流、小图。
      assert.deepEqual(await photoWallFaces(page), { display: 'block', columns: 4, gap: '10px', square: true });
      const cell = await page.evaluate(() => {
        const node = document.querySelector<HTMLElement>('[data-local-wall] [data-photo-cell]')!;
        const style = getComputedStyle(node);
        const head = document.querySelector('[data-photo-group]')!;
        return {
          radius: style.borderRadius, cursor: style.cursor, sunk: style.backgroundColor,
          token: getComputedStyle(document.documentElement).getPropertyValue('--surface-radius').trim(),
          alt: getComputedStyle(node.querySelector('img')!).color,
          headTop: getComputedStyle(head).marginTop,
          rows: [head, head.querySelector('b')!].map((node) => getComputedStyle(node).lineHeight),
          code: getComputedStyle(head.querySelector('b')!).fontFamily,
          meta: getComputedStyle(head.querySelector('[data-photo-group-meta]')!).marginLeft !== '0px',
        };
      });
      assert.equal(cell.radius, cell.token, '照片格的圆角是 --surface-radius');
      assert.equal(cell.cursor, 'zoom-in');
      assert.equal(cell.alt, 'rgba(0, 0, 0, 0)', '等图时 alt 文件名不画出来');
      assert.notEqual(cell.sunk, 'rgba(0, 0, 0, 0)', '格子自带一块沉底色');
      assert.equal(cell.headTop, '28px', '每段上方留出段距');
      assert.deepEqual(cell.rows, ['20px', '20px'], '段头一行 20px，番号不按自己的字号撑高');
      assert.match(cell.code, /Cascadia Mono/, '段头番号是等宽字');
      assert.ok(cell.meta, '来源与张数靠右');
      assert.equal(await page.locator('#index [data-entity-more]').evaluate((node) => {
        const style = getComputedStyle(node);
        return `${style.height} ${style.borderRadius} ${style.fontSize} ${style.fontWeight}`;
      }), '36px 10px 14px 500', '载入更多是 36px 高、10px 圆角的 secondary 按钮');
      await page.locator('[data-entity-layout][aria-label="图片布局"] label:has(input[value="fixed"])').click();
      await page.waitForFunction(() => document.querySelector('[data-local-wall]')?.getAttribute('data-layout') === 'fixed');
      assert.deepEqual(await photoWallFaces(page), { display: 'grid', columns: 4, gap: '10px', square: true });
      // 顶栏那枚大小键在照片档里换的是照片的大小档，一次请求都不发。
      await page.locator('#density').click();
      await page.waitForFunction(() => document.querySelector('[data-local-wall]')?.getAttribute('data-size') === 'big');
      assert.deepEqual(await photoWallFaces(page), { display: 'grid', columns: 2, gap: '10px', square: true });
      assert.equal(await page.locator('#density').getAttribute('title'), '当前：大图');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
    const phone = await openPhotoWall(browser, MOBILE);
    try {
      const { page } = phone;
      assert.deepEqual(await photoWallFaces(page), { display: 'block', columns: 2, gap: '10px', square: true });
      await page.locator('[data-entity-layout][aria-label="图片布局"] label:has(input[value="fixed"])').click();
      await page.waitForFunction(() => document.querySelector('[data-local-wall]')?.getAttribute('data-layout') === 'fixed');
      assert.deepEqual(await photoWallFaces(page), { display: 'grid', columns: 2, gap: '8px', square: true });
      assert.deepEqual(phone.problems, []);
    } finally {
      await phone.close();
    }
  });

  it('空输入时搜索记录与推荐并排，两栏之间的分隔线从顶画到底', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', WIDE);
    try {
      const page = opened.page;
      const history = Array.from({ length: 10 }, (_, at) => `搜索记录 ${at + 1}`);
      await page.route(/\/api\/search-history\?/, (route) => route.fulfill({ json: { items: history } }));
      await page.reload({ waitUntil: 'load' });
      await expectBody(page, '/', [page.locator('article[data-media-card][data-id]').first()]);
      await settle(page);
      await page.locator('#q').click();
      await page.locator('#searchMenu .searchresults[data-split]').waitFor({ state: 'visible', timeout: 5_000 });
      const split = await page.evaluate(() => {
        const results = document.querySelector('#searchMenu .searchresults')!;
        const [left, right] = [...results.querySelectorAll(':scope > .searchcol')].map((col) => col.getBoundingClientRect());
        const box = results.getBoundingClientRect();
        const line = getComputedStyle(results, '::before');
        return {
          box: box.height, left: left.height, right: right.height, line: parseFloat(line.height),
          offset: parseFloat(line.left) + parseFloat(line.width) / 2 - ((left.right + right.left) / 2 - box.left),
        };
      });
      assert.ok(split.right < split.left, `推荐一栏（${split.right}px）应比十条搜索记录（${split.left}px）短`);
      assert.ok(Math.abs(split.line - split.box) <= 1, `分隔线高 ${split.line}px，两栏高 ${split.box}px`);
      assert.ok(Math.abs(split.offset) <= 1, `分隔线偏离两栏之间的缝 ${split.offset}px`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('资料表的标签只列前四个，余下的收进「+N」，浮层进顶层列全部标签', { timeout: 60_000 }, async () => {
    const opened = await openProfiledPerformer(browser, DESKTOP);
    try {
      const page = opened.page;
      const cell = await page.locator('[data-entity-facts] dd[data-fact="tags"]').evaluate((dd) => ({
        shown: [...dd.querySelectorAll(':scope > [data-fact-tag]')].map((tag) => tag.textContent!.trim()),
        more: dd.querySelector(':scope > [data-hero-more="fact"]')?.textContent?.trim() ?? '',
      }));
      assert.deepEqual(cell.shown, PROFILED.profile.tags.slice(0, 4), '标签那一格不是前四个');
      assert.equal(cell.more, '+5', '「+N」数的不是剩下那几个标签');
      const pop = page.locator('#entityTagPop');
      assert.equal(await pop.isVisible(), false);
      await page.locator('[data-hero-more="fact"]').hover();
      await pop.waitFor({ state: 'visible', timeout: 5_000 });
      const shown = await pop.evaluate((element) => {
        const box = element.getBoundingClientRect();
        return {
          topLayer: element.matches(':popover-open'),
          inView: box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight,
          title: element.querySelector('[data-hero-pop-head]')?.textContent?.trim(),
          tags: [...element.querySelectorAll('[data-fact-tag]')].map((tag) => tag.textContent!.trim()),
        };
      });
      assert.equal(shown.topLayer, true, '标签浮层没进顶层，会被资料卡的 overflow:hidden 裁掉');
      assert.ok(shown.inView, '标签浮层越出了视口');
      assert.equal(shown.title, '9 个标签');
      assert.deepEqual(shown.tags, PROFILED.profile.tags);
      await page.mouse.move(1, 1);
      await pop.waitFor({ state: 'hidden', timeout: 5_000 });
      // 点一下钉住：指针离开也不收，Escape 才收。
      await page.locator('[data-hero-more="fact"]').click();
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
      const button = page.locator('[data-entity-portrait-wrap] [data-avatar-picker] button');
      await button.waitFor({ timeout: 15_000 });
      // 行有多高看她有多少资料、别名那一行折不折；这里直接把身份列撑高，量的是加号跟不跟圆框。
      await page.addStyleTag({ content: '[data-entity-identity]{padding-block:40px}' });
      const box = await page.evaluate(() => {
        const rect = (element: Element) => element.getBoundingClientRect();
        const wrap = rect(document.querySelector('[data-entity-portrait-wrap]')!);
        const circle = rect(document.querySelector('[data-entity-portrait]')!);
        const plus = rect(document.querySelector('[data-entity-portrait-wrap] [data-avatar-picker] button')!);
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
      const facts = await page.locator('[data-entity-facts]').evaluate((dl) => ({
        dd: getComputedStyle(dl.querySelector('dd')!).color, dt: getComputedStyle(dl.querySelector('dt')!).color,
      }));
      assert.equal(facts.dd, ink, '深色下资料表的值不是墨色');
      assert.equal(facts.dt, muted, '深色下资料表的项名不是次级字色');
      await page.locator('[data-hero-more="alias"]').hover();
      const pop = page.locator('#entityAliasPop');
      await pop.waitFor({ state: 'visible', timeout: 5_000 });
      const { face, shadow } = await pop.evaluate((element) => {
        const style = getComputedStyle(element);
        return { face: style.backgroundColor, shadow: style.boxShadow };
      });
      assert.notEqual(face, 'rgba(0, 0, 0, 0)');
      assert.notEqual(face, 'rgb(255, 255, 255)', '深色下别名浮层还是白底');
      assert.equal(shadow, await popmenuShadow(page), '深色下别名浮层的落影和 .popmenu 不是同一副');
      assert.notEqual(ground, 'rgb(255, 255, 255)', '主题没有切到深色');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('详情出演区每一组的标题、头像和名字共用一条左边缘', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/', DESKTOP);
    try {
      const page = opened.page;
      /* 演示库的作品没有女优与厂牌，身份数据按 `/api/item` 的 `entity_refs` 形状换进去；
         名字比头像宽的那种最容易看出错位，所以女优名取四个字。 */
      await page.route(/\/api\/item\?/, async (route) => {
        const payload = await (await route.fetch()).json();
        Object.assign(payload, {
          is_jav: true, performers: ['凉森玲梦'], studio: 'Prestige', creator: '',
          entity_refs: {
            creator: [], series: [],
            performer: [{ id: 90_101, name: '凉森玲梦', has_image: true }],
            studio: [{ id: 90_102, name: 'Prestige', has_image: false, has_logo: true }],
          },
        });
        await route.fulfill({ json: payload });
      });
      const square = { contentType: 'image/svg+xml',
        body: '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#888"/></svg>' };
      await page.route(/\/entity-image\?/, (route) => route.fulfill(square));
      await page.route(/\/logo\?/, (route) => route.fulfill(square));
      await page.goto(new URL(`/item/${requiredEnv('PEACH_E2E_ITEM')}`, page.url()).href, { waitUntil: 'load' });
      await page.locator('[data-item-identity] [data-id-group="studio"] [data-id-name]').waitFor({ timeout: 15_000 });
      const edges = await page.evaluate(() => Object.fromEntries(
        ['performer', 'studio'].map((kind) => {
          const group = document.querySelector(`[data-item-identity] [data-id-group="${kind}"]`)!;
          const name = document.createRange();
          name.selectNodeContents(group.querySelector('[data-id-name]')!);
          return [kind, {
            label: group.querySelector('[data-id-label]')!.getBoundingClientRect().left,
            face: group.querySelector('[data-id-face]')!.getBoundingClientRect().left,
            name: name.getBoundingClientRect().left,
          }];
        })));
      for (const [kind, edge] of Object.entries(edges)) {
        assert.ok(Math.abs(edge.face - edge.label) < 0.5, `${kind} 组头像左缘 ${edge.face} 不在标题左缘 ${edge.label}`);
        assert.ok(Math.abs(edge.name - edge.label) < 0.5, `${kind} 组名字左缘 ${edge.name} 不在标题左缘 ${edge.label}`);
      }
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('人物页同台艺人的头像悬停和首页顶栏女优头像同一副：抬整格填充、不描圈', { timeout: 60_000 }, async () => {
    const opened = await openPerformer(browser, DESKTOP);
    try {
      const page = opened.page;
      const person = page.locator('[data-entity-foot] [data-related-performer]').first();
      const face = () => person.evaluate((element) => {
        const style = getComputedStyle(element), ring = getComputedStyle(element.querySelector('[data-hero-ring]')!);
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

  it('资料卡大位与同台艺人的头像按人脸框放大：图保持原比例、盖满圆框，不被预检的 max-width 夹住', { timeout: 60_000 }, async () => {
    const name = '七沢みあ';
    const opened = await visit(browser, '/', DESKTOP);
    try {
      const page = opened.page;
      const focus = { box: TASTE_FACE };
      await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
        id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [],
        user_aliases: [], asset_count: 0, tags: [], links: [], metadata: {}, entry_links: [],
        related_performers: [{ id: 90_002, k: '共演者', n: 1, rep: null, has_image: true, has_avatar: false,
          avatar_focus: focus }],
        has_image: true, has_avatar: false, avatar_focus: focus, representative_asset_id: null,
      } }));
      await page.route(/\/entity-image\?/, (route) => route.fulfill({
        contentType: 'image/svg+xml',
        body: `<svg xmlns="http://www.w3.org/2000/svg" width="${TASTE_FACE.imgW}" height="${TASTE_FACE.imgH}">`
          + `<rect width="${TASTE_FACE.imgW}" height="${TASTE_FACE.imgH}" fill="#888"/></svg>`,
      }));
      await page.goto(new URL(`/performers/${encodeURIComponent(name)}`, page.url()).href, { waitUntil: 'load' });
      for (const [where, selector] of [['大位', '[data-entity-portrait] > img[data-facebox]'],
        ['同台艺人', '[data-hero-ring] > img[data-facebox]']] as const) {
        const img = page.locator(selector).first();
        await img.waitFor({ state: 'attached', timeout: 15_000 });
        // 放大是图加载后 `avatarFrame` 写进内联 style 的；等到那一步落地再量。
        await page.waitForFunction((element) => element instanceof HTMLImageElement
          && element.complete && element.naturalWidth > 0 && element.style.width !== '',
        await img.elementHandle(), { timeout: 15_000 });
        const frame = await img.evaluate((element) => {
          const ring = element.parentElement!.getBoundingClientRect();
          const box = element.getBoundingClientRect();
          return {
            maxWidth: getComputedStyle(element).maxWidth, maxHeight: getComputedStyle(element).maxHeight,
            ring: ring.width, width: box.width, aspect: box.width / box.height,
            gaps: [box.left - ring.left, ring.right - box.right, box.top - ring.top, ring.bottom - box.bottom],
            initial: getComputedStyle(element.parentElement!.querySelector('span')!).display,
          };
        });
        assert.deepEqual([frame.maxWidth, frame.maxHeight], ['none', 'none'], `${where}的图被预检的 max-width 夹住`);
        assert.ok(frame.width > frame.ring, `${where}没有按人脸框放大：图宽 ${frame.width}px，圆框 ${frame.ring}px`);
        assert.ok(Math.abs(frame.aspect - TASTE_FACE.imgW / TASTE_FACE.imgH) < .02, `${where}的图宽高比 ${frame.aspect}，被压扁了`);
        assert.ok(frame.gaps.every((gap) => gap <= .5), `${where}的图没盖满圆框：${frame.gaps.join('、')}`);
        if (where === '大位') assert.equal(frame.initial, 'none', '大位有图时首字母没有让位');
      }
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  for (const viewport of [DESKTOP, MOBILE]) {
    it(`资料卡外链的圆盘不垫底、社媒字形铺满圆盘；手机上那一排不换行、横滑，滚动层顶到卡沿（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openProfiledPerformer(browser, viewport);
      try {
        const row = await opened.page.locator('[data-entity-links]').evaluate((element) => {
          const style = getComputedStyle(element);
          const card = element.closest('[data-entity-card]')!.getBoundingClientRect();
          const box = element.getBoundingClientRect();
          const brand = element.querySelector('[data-link-icon="brand"]')!;
          const glyph = brand.querySelector('svg')!.getBoundingClientRect(), plate = brand.getBoundingClientRect();
          return {
            wrap: style.flexWrap, overflowX: style.overflowX, justify: style.justifyContent,
            edges: [box.left - card.left, card.right - box.right],
            discs: [...element.querySelectorAll('[data-link-icon]')].map((disc) => getComputedStyle(disc).backgroundColor),
            glyph: [Math.round(glyph.width), Math.round(glyph.height)], plate: [Math.round(plate.width), Math.round(plate.height)],
          };
        });
        // 垫一层底会让圆盘比周围暗一档，看着像这条链接被禁用了。
        assert.ok(row.discs.every((fill) => fill === 'rgba(0, 0, 0, 0)'), `外链圆盘垫了底色：${row.discs.join('、')}`);
        assert.deepEqual(row.glyph, row.plate, '社媒字形没有铺满圆盘，场色的角露出底');
        if (viewport.mobile) {
          // 普通 `center` 在溢出时把前半排推到滚动起点之前，那几条滑不到。
          assert.deepEqual([row.wrap, row.overflowX, row.justify], ['nowrap', 'auto', 'safe center'], '窄屏外链不是一行横滑');
          assert.ok(row.edges.every((gap) => Math.abs(gap) < 0.5), `窄屏外链的滚动层没有顶到卡沿：${row.edges.join('、')}`);
        } else {
          assert.equal(row.wrap, 'wrap', '宽屏外链该换行，不横滑');
        }
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });

    it(`名字菜单：当前统称抬一档底色并打勾，其余行的勾位空着；手机上开关画 32px、命中区 44px，菜单行 44px（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openProfiledPerformer(browser, viewport);
      try {
        const page = opened.page;
        const toggle = page.locator('[data-namepick-toggle]');
        const hit = await toggle.evaluate((element) => {
          const box = element.getBoundingClientRect(), after = getComputedStyle(element, '::after');
          return { drawn: [Math.round(box.width), Math.round(box.height)], hit: [after.width, after.height] };
        });
        assert.deepEqual(hit.drawn, [32, 32], '名字旁那枚开关画出来不是 32px');
        if (viewport.mobile) assert.deepEqual(hit.hit, ['44px', '44px'], '手机上开关的命中区不到 44px');
        await toggle.click();
        await page.locator('[data-namepick-menu]').waitFor({ state: 'visible', timeout: 5_000 });
        const rows = await page.locator('[data-namepick-menu] [role="menuitemradio"]').evaluateAll((items) => items.map((item) => ({
          checked: item.getAttribute('aria-checked') === 'true', fill: getComputedStyle(item).backgroundColor,
          tick: getComputedStyle(item.querySelector('svg')!).visibility, height: item.getBoundingClientRect().height,
          menu: getComputedStyle(item.closest('[data-namepick-menu]')!).backgroundColor,
        })));
        assert.deepEqual(rows.map((row) => row.checked), [true, false], '菜单里当前统称不是第一行，或不止一行被选中');
        const [current, other] = rows;
        assert.notEqual(current!.fill, 'rgba(0, 0, 0, 0)', '当前统称那一行没有抬底');
        assert.notEqual(current!.fill, current!.menu, '当前统称那一行的底色和菜单面同色，看不出来');
        assert.deepEqual([current!.tick, other!.tick], ['visible', 'hidden'], '勾没有只给当前统称，或未选中那行不留勾位');
        assert.equal(other!.fill, 'rgba(0, 0, 0, 0)', '未选中那一行也抬了底');
        const least = viewport.mobile ? 44 : 36;
        const alias = await page.locator('[data-namepick-alias]').evaluate((item) => item.getBoundingClientRect().height);
        assert.ok([...rows.map((row) => row.height), alias].every((height) => height >= least - 0.5), `菜单行矮于 ${least}px`);
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  /* 尺寸按身份列有哪几行定：外链与看片那一行都在是 160px，缺一行是 120px。取行高百分比的话
     圆框宽、列宽、别名折行、行高绕成一个圈，折行多出的那截压进卡底内边距。
     有资料的女优默认只有外链那一行，两行都在的那位要补上看片标识与订阅开关；七沢みあ只有看片那一行。 */
  const openBothRows = (browser: Browser, viewport: typeof DESKTOP) => openProfiledPerformer(browser, viewport, 'light', {
    entry_links: [
      { site: 'minnano-av', label: 'みんなのAV', ordinal: '', slot: 'pill', mark: 'brand-minnano',
        url: 'https://www.minnano-av.com/actress12345.html' },
      { site: 'javdb', label: 'JavDB', ordinal: '', slot: 'mark', mark: 'mark-javdb', url: 'https://javdb.com/actors/NPD3' },
    ],
    feed: { following: false },
  });
  for (const [label, open, size] of [
    ['外链与看片那一行都在', openBothRows, 160],
    ['只有看片那一行', openPerformer, 120],
    ['只有外链那一行', openProfiledPerformer, 120],
  ] as const) {
    it(`资料卡大位按身份列的行数定尺寸：${label}是 ${size}px 正圆，身份列不压进卡底内边距`, { timeout: 60_000 }, async () => {
      const opened = await open(browser, DESKTOP);
      try {
        const box = await opened.page.locator('[data-entity-portrait]').evaluate((element) => {
          const portrait = element.getBoundingClientRect();
          const profile = element.closest('[data-entity-profile]')!.getBoundingClientRect();
          const identity = element.closest('[data-entity-profile]')!.querySelector('[data-entity-identity]')!.getBoundingClientRect();
          return { width: portrait.width, height: portrait.height, room: profile.bottom - identity.bottom };
        });
        assert.ok(Math.abs(box.height - size) < 1, `头像 ${box.height}px，应是 ${size}px`);
        assert.ok(Math.abs(box.width - box.height) < 1, '头像不是正圆');
        assert.ok(box.room >= 19.5, `身份列离卡底只剩 ${box.room}px，压进了 20px 的内边距`);
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  it('看片那一行：两枚标识隔 32px、按 22px 字高对齐；MISSAV 按它站上的排字，AV 用它的粉；第二枚带序号', { timeout: 60_000 }, async () => {
    const name = '七沢みあ';
    const opened = await visit(browser, '/', DESKTOP);
    try {
      const page = opened.page;
      await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
        id: 90_001, kind: 'performer', canonical_name: name, aliases: [], display_aliases: [],
        user_aliases: [], asset_count: 0, tags: [], related_performers: [], links: [], metadata: {},
        has_image: false, has_avatar: false, avatar_focus: null, representative_asset_id: null,
        entry_links: [
          { site: 'javdb', label: 'JavDB', ordinal: '', slot: 'mark', mark: 'mark-javdb', url: 'https://javdb.com/actors/NPD3' },
          { site: 'missav', label: 'MISSAV', ordinal: '2', slot: 'mark', mark: '', url: 'https://missav.ws/actresses/x' },
        ],
      } }));
      await page.goto(new URL(`/performers/${encodeURIComponent(name)}`, page.url()).href, { waitUntil: 'load' });
      await page.locator('[data-missav-mark]').waitFor({ timeout: 15_000 });
      const marks = await page.locator('[data-entry-marks]').evaluate((row) => {
        const wordmark = row.querySelector('[data-missav-mark]')!;
        const [miss, av] = [...wordmark.children].map((part) => getComputedStyle(part).color);
        return {
          gap: getComputedStyle(row).columnGap,
          javdb: row.querySelector('[data-entry-mark] svg')!.getBoundingClientRect().height,
          family: getComputedStyle(wordmark).fontFamily, weight: getComputedStyle(wordmark).fontWeight,
          miss, av, ink: getComputedStyle(wordmark.closest('a')!).color,
          ordinal: row.querySelector('[data-entry-ordinal]')?.textContent ?? '',
          hrefs: [...row.querySelectorAll('a[data-entry-mark]')].map((a) => a.getAttribute('href')),
        };
      });
      assert.equal(marks.gap, '32px', '两枚标识的间距不是 32px');
      assert.equal(Math.round(marks.javdb), 22, 'JavDB 标识的字高不是 22px');
      assert.match(marks.family, /^Halant/, 'MISSAV 没有用 Halant 排字');
      assert.equal(marks.weight, '500');
      assert.equal(marks.miss, marks.ink, 'MISS 那半没有跟页面墨色');
      assert.equal(marks.av, 'rgb(254, 98, 142)', 'AV 那半不是 MISSAV 的粉');
      assert.equal(marks.ordinal, '2', '第二枚没带服务端编好的序号');
      assert.deepEqual(marks.hrefs, ['https://javdb.com/actors/NPD3', 'https://missav.ws/actresses/x'], '入口地址不是服务端下发的那个');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('厂牌页资料卡：标识铺满方框；指回自家站的官网写「官方网站」，带站点圆标、字距 .02em', { timeout: 60_000 }, async () => {
    const name = 'S1 NO.1 STYLE';
    const opened = await visit(browser, '/', DESKTOP);
    try {
      const page = opened.page;
      await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
        id: 90_601, kind: 'studio', canonical_name: name, aliases: [], display_aliases: [], user_aliases: [],
        asset_count: 3, tags: [], related_performers: [], labels: [], metadata: {}, entry_links: [],
        has_image: false, has_avatar: false, has_logo: true, avatar_focus: null, representative_asset_id: null,
        links: [{ link_id: 90_602, link_kind: 'official', clickable: true, label: 'S1', url: 'https://www.s1s1s1.com/' }],
      } }));
      // 标识比方框大，走铺满那条；比框小的走原尺寸居中，是另一条判据。
      await page.route(/\/logo\?/, (route) => route.fulfill({
        contentType: 'image/svg+xml',
        body: '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600"><rect width="600" height="600" fill="#888"/></svg>',
      }));
      await page.route('**/link-mark**', (route) => route.fulfill({
        status: 200, contentType: 'image/png', body: Buffer.from(PIXEL, 'base64'),
      }));
      await page.goto(new URL(`/studios/${encodeURIComponent(name)}`, page.url()).href, { waitUntil: 'load' });
      const logo = page.locator('[data-entity-portrait] > img');
      await logo.waitFor({ state: 'attached', timeout: 15_000 });
      await page.waitForFunction((element) => element instanceof HTMLImageElement && element.complete && element.naturalWidth > 0,
        await logo.elementHandle(), { timeout: 15_000 });
      const face = await logo.evaluate((element) => {
        const frame = element.parentElement!, box = element.getBoundingClientRect(), outer = frame.getBoundingClientRect();
        return { shape: frame.getAttribute('data-entity-portrait'), radius: getComputedStyle(frame).borderTopLeftRadius,
          fit: getComputedStyle(element).objectFit,
          gaps: [box.left - outer.left, outer.right - box.right, box.top - outer.top, outer.bottom - box.bottom] };
      });
      assert.equal(face.shape, 'square');
      assert.notEqual(face.radius, '50%', '厂牌的标识框画成了圆');
      // 标识走「图比框小就别放大」那组：contain 不裁字标，比框大的按框收，所以照样铺满。
      assert.equal(face.fit, 'contain', '厂牌标识被裁成了铺满');
      assert.ok(face.gaps.every((gap) => Math.abs(gap) < 0.5), `标识没盖满方框：${face.gaps.join('、')}`);
      const site = await page.locator('[data-entity-links] a[data-link="url"]').evaluate((a) => ({
        text: a.querySelector('[data-link-label]')?.textContent ?? '',
        spacing: parseFloat(getComputedStyle(a).letterSpacing) / parseFloat(getComputedStyle(a).fontSize),
        mark: a.querySelector('[data-link-icon] img')?.getAttribute('src') ?? '',
        referrer: a.querySelector('[data-link-icon] img')?.getAttribute('referrerpolicy') ?? '',
      }));
      assert.equal(site.text, '官方网站');
      assert.ok(Math.abs(site.spacing - 0.02) < 0.001, `官网那一格的字距是 ${site.spacing}em`);
      assert.deepEqual([site.mark, site.referrer], ['/link-mark?id=90602', 'no-referrer'], '官网没带本机合成的站点圆标');
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
        footHeight: document.querySelector('[data-entity-card] > [data-entity-foot]')?.getBoundingClientRect().height ?? 0,
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
      const card = opened.page.locator('#grid [data-media-grid] > [data-media-card]').first();
      await card.hover();
      const geometry = await card.evaluate((element) => {
        const box = element.getBoundingClientRect();
        const neighbor = [...element.parentElement!.children].find((other) => other !== element
          && Math.abs(other.getBoundingClientRect().top - box.top) < 1)!;
        const spread = Number(/0px 0px 0px (\d+(?:\.\d+)?)px/.exec(getComputedStyle(element).boxShadow)?.[1]);
        // 壳画的骨架网格和关注页岛的视频列表不在首页这叠卡里：各挂一个同形的空壳读列距。
        const columnGap = (build: (probe: HTMLElement) => HTMLElement) => {
          const probe = document.createElement('div');
          const host = build(probe);
          document.querySelector('#main')!.append(host);
          const gap = parseFloat(getComputedStyle(probe).columnGap);
          host.remove();
          return gap;
        };
        return {
          spread, clearance: neighbor.getBoundingClientRect().left - (box.right + spread),
          home: parseFloat(getComputedStyle(element.parentElement!).columnGap),
          skeleton: columnGap((probe) => { probe.className = 'grid'; return probe }),
          follow: columnGap((probe) => {
            const island = document.createElement('div');
            island.className = 'peach-react';
            probe.setAttribute('data-follow-list', '');
            island.append(probe);
            return island;
          }),
        };
      });
      assert.ok(geometry.spread > 0, '卡片悬停面没有往盒外铺');
      assert.ok(geometry.clearance >= geometry.spread,
        `悬停面离邻卡只剩 ${geometry.clearance}px，比它自己往外铺的 ${geometry.spread}px 还窄`);
      assert.equal(geometry.skeleton, geometry.home, '壳画的骨架网格的列距和首页不一样，真卡换上来时整排挪位');
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
      const avatar = page.locator('#grid [data-media-grid] > [data-media-card] [data-media-meta] > button[data-media-avatar]').first();
      const edges = () => avatar.evaluate((element) => {
        const meta = element.closest('[data-media-meta]')!;
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

  it('头像圆框里的图按人脸框写进的内联尺寸不被岛里的预检夹回框宽', { timeout: 60_000 }, async () => {
    /* 演示库没有实体图，往首张卡的头像框里塞一张按人脸框放大的图：宽超过框宽时图就该那么宽，
       由圆框的 overflow 裁；被夹回框宽的话脸偏到左边，右侧露出底下的首字母。 */
    const opened = await openCatalogFixture(browser, (payload) => {
      const item = payload.items[0];
      if (!item) throw new Error('演示目录没有可替换的卡片');
      item.creator = '';
      item.performers = ['演示演员'];
      item.performer_total = 1;
      item.performer_entities = [{ id: 90_000, name: '演示演员', has_image: false }];
    });
    try {
      const avatar = opened.page.locator('#grid [data-media-grid] > [data-media-card] [data-media-meta] > button[data-media-avatar]').first();
      const framed = await avatar.evaluate((element) => {
        const img = document.createElement('img');
        img.setAttribute('style', 'position:absolute;inset:-25% auto auto 0;width:150%;height:195%');
        element.appendChild(img);
        const frame = element.getBoundingClientRect();
        const box = img.getBoundingClientRect();
        const style = getComputedStyle(img);
        return { maxWidth: style.maxWidth, maxHeight: style.maxHeight,
          width: box.width / frame.width, height: box.height / frame.height };
      });
      assert.equal(framed.maxWidth, 'none', '头像图还带着预检的 max-width');
      assert.equal(framed.maxHeight, 'none', '头像图还带着 max-height');
      assert.ok(Math.abs(framed.width - 1.5) <= .02, `按人脸框放大到 1.5 倍框宽的图被夹成了 ${framed.width} 倍`);
      assert.ok(Math.abs(framed.height - 1.95) <= .02, `按人脸框放大到 1.95 倍框高的图被夹成了 ${framed.height} 倍`);
    } finally {
      await opened.close();
    }
  });

  it('亮暗卡片、按钮与回执使用克制的接触阴影', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/stats', DESKTOP);
    try {
      // 选中的那张页签按基线收掉接触阴影，读旁边没选中的一张。
      const card = opened.page.locator('#main [class~="shadow-card"]:not([data-selected])').first();
      await card.waitFor({ timeout: 15_000 });
      await settle(opened.page);
      /* Tailwind 把阴影 token 的字面值抄进工具类，`.dark` 里改 `--shadow-*` 够不着它；
         旧样式表里写死的浅色阴影同样不跟主题走。读三类来源各一处的计算值。 */
      const alphas = () => opened.page.evaluate(() => {
        const strongest = (shadow: string) => Math.max(0, ...[...shadow.matchAll(
          /rgba\(0, 0, 0, ([\d.]+)\)|rgb\(0, 0, 0\)/g)].map((match) => (match[1] ? Number(match[1]) : 1)));
        const probe = (html: string, parent: Element = document.body) => {
          const holder = document.createElement('div');
          holder.innerHTML = html;
          const element = holder.firstElementChild!;
          // 挂在 React 岛外面：岛里的重置会把旧样式表的按钮阴影清掉。
          parent.append(element);
          const shadow = getComputedStyle(element).boxShadow;
          element.remove();
          return strongest(shadow);
        };
        return {
          card: strongest(getComputedStyle(document.querySelector('#main [class~="shadow-card"]:not([data-selected])')!).boxShadow),
          button: probe('<button class="geist-button" type="button">键</button>'),
          // Toast 的面只在 #toasts 里成立：阴影写在 Sonner 那一条的属性选择器上。
          toast: probe('<li data-sonner-toast data-styled="true">回执</li>', document.getElementById('toasts')!),
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
        assert.ok(dark[key] > light[key] && dark[key] <= .2,
          `暗色 ${key} 阴影应保留接触感而不形成重边：${dark[key]}`);
      }
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  for (const viewport of [DESKTOP, MOBILE]) {
    it(`关注分类使用 Pills，凭据列表与外层共用一个表面（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openFollowManage(browser, viewport);
      try {
        const page = opened.page;
        const tabs = page.getByRole('tablist', { name: '关注管理区域' });
        for (const theme of ['light', 'dark']) {
          await page.evaluate((value) => {
            document.documentElement.dataset.theme = value;
            document.documentElement.classList.toggle('dark', value === 'dark');
          }, theme);
          await tabs.getByRole('tab', { name: /来源和凭证/ }).click();
          const face = await tabs.evaluate((element) => {
            const selected = element.querySelector('[aria-selected=true]')!;
            return { track: getComputedStyle(element).backgroundColor,
              selected: getComputedStyle(selected).backgroundColor,
              shadow: getComputedStyle(selected).boxShadow };
          });
          assert.equal(face.track, 'rgba(0, 0, 0, 0)', 'Pills 容器应透明');
          assert.notEqual(face.selected, face.track, '当前分类应有独立底色');
          assert.equal(face.shadow, 'none', 'Pills 不使用浮起滑块');
          const list = page.getByRole('heading', { name: '来源和凭证', exact: true }).locator('..').locator('..');
          const rows = await list.evaluate((element) => {
            const group = element.children[1];
            const style = getComputedStyle(group);
            return { shadow: style.boxShadow, radius: style.borderRadius, background: style.backgroundColor };
          });
          assert.deepEqual(rows, { shadow: 'none', radius: '0px', background: 'rgba(0, 0, 0, 0)' });
          await tabs.getByRole('tab', { name: /来源和凭证/ }).focus();
          await page.keyboard.press('Home');
          await page.keyboard.press('Enter');
          assert.equal(await tabs.getByRole('tab', { name: '关注列表', exact: true }).getAttribute('aria-selected'), 'true');
          const dimensions = await layout(page);
          assert.ok(dimensions.scrollWidth <= dimensions.viewportWidth + 1, JSON.stringify(dimensions));
        }
        await page.route('**/api/follow/resolve', (route) => route.fulfill({
          status: 200, contentType: 'application/json', body: JSON.stringify({
            status: 'done', results: [{ line: '主题测试来源', candidates: [{
              provider: 'kemono', provider_label: 'Kemono', label: '主题测试候选', url: 'https://example.com/creator',
            }] }],
          }),
        }));
        await tabs.getByRole('tab', { name: '添加关注', exact: true }).click();
        await page.getByRole('textbox', { name: '来源链接、名字或 id' }).fill('主题测试来源');
        await page.getByRole('button', { name: '查找', exact: true }).click();
        const result = page.getByText('主题测试来源', { exact: true }).locator('..');
        await result.waitFor();
        for (const theme of ['light', 'dark']) {
          await page.evaluate((value) => {
            document.documentElement.dataset.theme = value;
            document.documentElement.classList.toggle('dark', value === 'dark');
          }, theme);
          const surface = await result.evaluate((element) => {
            const s = getComputedStyle(element);
            return { shadow: s.boxShadow, width: s.borderTopWidth, border: s.borderTopColor, bg: s.backgroundColor };
          });
          assert.equal(surface.shadow, 'none');
          assert.equal(surface.width, '1px');
          assert.notEqual(surface.border, surface.bg, '结果分组必须有可辨认边界');
        }
        assert.deepEqual(opened.problems, []);
      } finally { await opened.close(); }
    });
  }

  it('使用空间按字节量级的真实容量画出已用那一段，每个卷一行、不越出卡片', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/stats', DESKTOP);
    try {
      const page = opened.page;
      const TB = 1024 ** 4;
      const volumes = [
        { kind: 'system', label: '系统盘', root: 'C:\\', online: true, total: 2 * TB, used: 1.8 * TB, free: .2 * TB },
        { kind: 'media', label: '资源盘', root: 'R:\\media', online: false, total: null, used: null, free: null },
        { kind: 'media', label: 'PikPak 网盘', root: 'A:\\', online: true, total: 10240 * TB, used: 0, free: 10240 * TB },
      ];
      await page.route(/\/api\/stats(?:\?|$)/, async (route) => {
        const json = await (await route.fetch()).json();
        await route.fulfill({ json: { ...json, storage_volumes: volumes, storage_summary: {
          volumes: 3, online: 2, measured: 2, free: 10240.2 * TB, used: 1.8 * TB, total: 10242 * TB,
        } } });
      });
      await page.reload({ waitUntil: 'load' });
      await page.getByRole('tab', { name: /使用空间/ }).click();
      const panel = page.locator('[role="tabpanel"]').first();
      await panel.locator('[role="progressbar"]').first().waitFor({ state: 'visible', timeout: 15_000 });
      await settle(page);
      const shown = await panel.evaluate((element) => {
        const card = element.firstElementChild!;
        const cardBox = card.getBoundingClientRect();
        const detail = card.lastElementChild!.getBoundingClientRect();
        return {
          filled: [...element.querySelectorAll('[role="progressbar"]')].map((bar) =>
            Math.round(bar.querySelectorAll('rect')[1]!.getBoundingClientRect().width / bar.getBoundingClientRect().width * 100)),
          rows: [...element.querySelectorAll('article')].map((row) => getComputedStyle(row).borderBottomWidth),
          overflow: detail.right - (cardBox.right - parseFloat(getComputedStyle(card).paddingRight)),
          text: element.textContent ?? '',
        };
      });
      assert.deepEqual(shown.filled, [90, 0], '进度条画出来的已用比例不对');
      assert.deepEqual(shown.rows, ['1px', '1px', '0px'], '卷与卷之间没有覆盖率那样的分隔线');
      assert.ok(shown.overflow <= .5, `使用空间的详情越出卡片内边距 ${shown.overflow}px`);
      assert.ok(shown.text.includes('10.00 PB'), '网盘容量没按 PB 写');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  for (const viewport of VIEWPORTS) {
    it(`口味维度排名宽屏跟雷达那一栏等高、窄屏按条数给高度，图拉高时条不变粗（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await openTaste(browser, viewport);
      try {
        const page = opened.page;
        const bars = page.locator('section[aria-label="口味维度排名"]');
        await bars.locator('.recharts-bar-rectangle').first().waitFor({ state: 'visible', timeout: 15_000 });
        await settle(page);
        const shown = await page.locator('section[aria-label="浏览器画像"]').evaluate((section) => {
          const radar = section.firstElementChild!.getBoundingClientRect();
          const ranked = section.querySelector('section[aria-label="口味维度排名"]')!.getBoundingClientRect();
          return {
            radar: radar.height,
            ranked: ranked.height,
            thickness: [...section.querySelectorAll('.recharts-bar-rectangle')]
              .map((bar) => bar.getBoundingClientRect().height),
          };
        });
        assert.equal(shown.thickness.length, TASTE_CATEGORIES.length);
        if (viewport.mobile) {
          assert.ok(shown.ranked >= 32 * TASTE_CATEGORIES.length,
            `窄屏排行条只有 ${shown.ranked}px，${TASTE_CATEGORIES.length} 条挤不下`);
        } else {
          assert.ok(Math.abs(shown.ranked - shown.radar) < 2,
            `排行条 ${shown.ranked}px，雷达那一栏 ${shown.radar}px，两栏不等高`);
        }
        // 26 是一格 32 里默认留出的粗细；图被拉高时多出来的高度拉开条距，不进条本身。
        assert.ok(shown.thickness.every((height) => height <= 26.5), `条粗 ${shown.thickness.join('、')}px`);
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }

  it('口味榜的女优与创作者头像按人脸框放大：图保持原比例、盖满圆框，不露出底下的首字母', { timeout: 60_000 }, async () => {
    const opened = await openTaste(browser, DESKTOP);
    try {
      const page = opened.page;
      await page.getByRole('tablist', { name: '口味证据来源' }).getByRole('tab', { name: 'Peach 内部' }).click();
      for (const name of ['女优', '创作者']) {
        await page.getByRole('tablist', { name: 'Peach 口味维度' }).getByRole('tab', { name }).click();
        const img = page.getByRole('tabpanel', { name }).locator('img[data-facebox]').first();
        await img.scrollIntoViewIfNeeded();
        // 放大是图加载后 `avatarFrame` 写进内联 style 的；等到那一步落地再量。
        await page.waitForFunction((element) => element instanceof HTMLImageElement
          && element.complete && element.naturalWidth > 0 && element.style.width !== '',
        await img.elementHandle(), { timeout: 15_000 });
        const frame = await img.evaluate((element) => {
          const ring = element.parentElement!.getBoundingClientRect();
          const box = element.getBoundingClientRect();
          return {
            maxWidth: getComputedStyle(element).maxWidth, ring: ring.width,
            width: box.width, aspect: box.width / box.height,
            gaps: [box.left - ring.left, ring.right - box.right, box.top - ring.top, ring.bottom - box.bottom],
          };
        });
        assert.equal(frame.maxWidth, 'none', `${name}头像的图被预检的 max-width 夹住`);
        assert.ok(frame.width > frame.ring, `${name}头像没有按人脸框放大：图宽 ${frame.width}px，圆框 ${frame.ring}px`);
        assert.ok(Math.abs(frame.aspect - TASTE_FACE.imgW / TASTE_FACE.imgH) < .02,
          `${name}头像的图宽高比 ${frame.aspect}，被压扁了`);
        assert.ok(frame.gaps.every((gap) => gap <= .5), `${name}头像的图没盖满圆框：${frame.gaps.join('、')}`);
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

  it('统计页选中的读数卡：2px 描边压在脚注带上面、圆角跟卡走，接触阴影收掉', { timeout: 60_000 }, async () => {
    const opened = await visit(browser, '/stats', DESKTOP);
    try {
      const page = opened.page;
      const tab = page.locator('#stats [role="tab"][data-selected]').first();
      await tab.waitFor({ timeout: 15_000 });
      await settle(page);
      const ring = await tokenColor(page, '.peach-react', '--color-border-focus-ring');
      const shown = await tab.evaluate((element) => {
        const card = getComputedStyle(element);
        const after = getComputedStyle(element, '::after');
        const footer = element.querySelector('small')!;
        const other = document.querySelector('#stats [role="tab"]:not([data-selected])')!;
        // `shadow-none` 是五层透明的 0px，不是字面的 none：看有没有一层带颜色。
        const shadowVisible = [...card.boxShadow.matchAll(/rgba?\([^)]*\)/g)]
          .some((match) => !/, 0\)$/.test(match[0]));
        return {
          shadowVisible, position: card.position, radius: card.borderRadius,
          after: {
            content: after.content, position: after.position, width: after.borderTopWidth,
            color: after.borderTopColor, radius: after.borderRadius, z: after.zIndex,
            inset: [after.top, after.right, after.bottom, after.left],
          },
          footerFace: getComputedStyle(footer).backgroundColor,
          otherAfter: getComputedStyle(other, '::after').content,
        };
      });
      assert.equal(shown.shadowVisible, false, '选中的卡还压着接触阴影');
      assert.equal(shown.position, 'relative');
      assert.equal(shown.after.content, '""', '选中的卡没有画覆盖层');
      assert.equal(shown.after.position, 'absolute');
      assert.deepEqual(shown.after.inset, ['0px', '0px', '0px', '0px'], '覆盖层没有铺满整张卡');
      assert.deepEqual([shown.after.width, shown.after.color], ['2px', ring], '描边不是 2px 焦点环色');
      assert.equal(shown.after.radius, shown.radius, '覆盖层圆角和卡不一致');
      assert.ok(Number(shown.after.z) >= 1, `覆盖层 z-index ${shown.after.z}，会被脚注带盖住`);
      assert.notEqual(shown.footerFace, 'rgba(0, 0, 0, 0)', '脚注带没有底色，这条用例守的就是环压在它上面');
      assert.equal(shown.otherAfter, 'none', '没选中的卡也画了覆盖层');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('索引页容器不横向裁剪：筛选玻璃左右两侧的影洒得出来，页面也不横向溢出', { timeout: 60_000 }, async () => {
    const opened = await openIndexPage(browser, '/tags');
    try {
      const page = opened.page;
      const clip = await page.evaluate(() => {
        const index = document.querySelector('#index')!;
        return {
          overflow: getComputedStyle(index).overflowX,
          spill: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        };
      });
      assert.equal(clip.overflow, 'visible', '#index 横向裁剪，玻璃左右两侧的影被切成直边');
      assert.equal(clip.spill, 0, '不裁剪后页面被撑出横向滚动');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('标签页骨架里就铺着那块筛选玻璃，React 落地时玻璃与开头那组内容都留在原位', { timeout: 60_000 }, async () => {
    /* 骨架与真页面各量一遍：玻璃的位置与大小、开头那组内容的上沿。药丸、读数与首字要等数据，
       骨架里是占位；视图切换此刻就是最终那一档。 */
    const opened = await visit(browser, '/tags', DESKTOP);
    try {
      const page = opened.page;
      await page.route('**/api/index?**', (route) => route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: [{ k: '痴女', n: 4, cat: 'role' }, { k: '秘书OL', n: 2, cat: 'scene' }],
          has_more: false, categories: { role: 1, scene: 1 } }),
      }));
      const release = await holdApi(page);
      await page.reload({ waitUntil: 'load' });
      await page.locator('#index [data-skeleton^="index/tags/"]').waitFor({ timeout: 15_000 });
      const measure = (glass: string, group: string, view: string) => page.evaluate(([glassSelector, groupSelector, viewSelector]) => {
        const rect = (selector: string) => {
          const box = document.querySelector(selector)?.getBoundingClientRect();
          return box ? { top: box.top, left: box.left, width: box.width, height: box.height } : null;
        };
        return { glass: rect(glassSelector), group: rect(groupSelector),
          pills: document.querySelectorAll(`${glassSelector} [data-filter-row="top"] > *`).length,
          view: rect(`${glassSelector} [data-filter-row="bottom"] ${viewSelector}`) };
      }, [glass, group, view] as const);
      const skeleton = await measure('#index .board-filter-frame', '#index [data-skeleton] .alphagroup', '.iconswitch');
      release();
      await page.locator('#index [data-alphabet]').waitFor({ timeout: 15_000 });
      await settle(page);
      const live = await measure('#index [data-filter-glass]', '#index [data-alpha-group]', '[aria-label="标签视图"]');
      assert.ok(skeleton.glass && skeleton.group && skeleton.view, '标签页骨架里缺筛选玻璃、开头那组或视图切换');
      assert.ok(skeleton.pills > 0, '骨架玻璃的上排没有铺药丸占位');
      assert.ok(live.glass && live.group && live.view, '接管后找不到筛选玻璃、开头那组或视图切换');
      for (const key of ['top', 'left', 'width', 'height'] as const) {
        assert.ok(Math.abs(skeleton.glass![key] - live.glass![key]) <= 1,
          `筛选玻璃的 ${key} 接管时跳了：骨架 ${skeleton.glass![key]}，接管后 ${live.glass![key]}`);
      }
      assert.ok(Math.abs(skeleton.group!.top - live.group!.top) <= 1,
        `开头那组内容的上沿接管时跳了：骨架 ${skeleton.group!.top}，接管后 ${live.group!.top}`);
      assert.ok(Math.abs(skeleton.view!.top - live.view!.top) <= 1 && Math.abs(skeleton.view!.left - live.view!.left) <= 1,
        `视图切换接管时挪了位：骨架 (${skeleton.view!.left}, ${skeleton.view!.top})，接管后 (${live.view!.left}, ${live.view!.top})`);
    } finally {
      await opened.close();
    }
  });

  it('标签页的筛选玻璃吸到顶栏下沿时影换成抬起来那一档，上沿垫一条页面底色的遮带', { timeout: 60_000 }, async () => {
    const opened = await openIndexPage(browser, '/tags');
    try {
      const page = opened.page;
      const read = () => page.evaluate(() => {
        const glass = document.querySelector('[data-filter-glass]')!;
        const root = getComputedStyle(document.documentElement);
        return {
          stuck: glass.hasAttribute('data-stuck'),
          shadow: getComputedStyle(glass).boxShadow,
          strip: getComputedStyle(glass, '::before'),
          lift: root.getPropertyValue('--glass-lift'),
          rest: root.getPropertyValue('--glass-shadow'),
        };
      });
      const readStrip = () => page.evaluate(() => {
        const strip = getComputedStyle(document.querySelector('[data-filter-glass]')!, '::before');
        return { content: strip.content, top: strip.top, height: strip.height, z: strip.zIndex, mask: strip.maskImage };
      });
      const resting = await read();
      assert.equal(resting.stuck, false, '还没滚就标成吸顶');
      assert.equal(farthestShadow(resting.shadow), farthestShadow(resting.rest), '静止态的影不是 --glass-shadow');
      assert.equal((await readStrip()).content, 'none', '静止态就画了遮带');
      // 桩数据只有两枚标签，页面不够长滚不动：垫一块高度再滚。
      await page.evaluate(() => document.body.insertAdjacentHTML('beforeend', '<div style="height:200vh"></div>'));
      await page.evaluate(() => window.scrollTo(0, 600));
      await page.waitForFunction(() => document.querySelector('[data-filter-glass]')!.hasAttribute('data-stuck'),
        undefined, { timeout: 5_000 });
      const stuck = await read();
      const strip = await readStrip();
      assert.equal(farthestShadow(stuck.shadow), farthestShadow(stuck.lift), '吸顶后的影不是 --glass-lift');
      assert.ok(farthestShadow(stuck.shadow) > farthestShadow(resting.shadow), '吸顶后影没有抬起来');
      assert.match(stuck.shadow, /inset/, '吸顶后四条内嵌 rim 线丢了');
      assert.deepEqual([strip.content, strip.top, strip.height, strip.z], ['""', '-9px', '9px', '-1']);
      assert.match(strip.mask, /linear-gradient/, '遮带两端没有渐隐');
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForFunction(() => !document.querySelector('[data-filter-glass]')!.hasAttribute('data-stuck'),
        undefined, { timeout: 5_000 });
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('图片灯箱：竖图按高度整张收进视口，上下让出工具条与缩略图条，左右让出翻页键', { timeout: 60_000 }, async () => {
    const opened = await openLightbox(browser, { count: 3, width: 1200, height: 4000 });
    try {
      const read = await opened.page.evaluate(() => {
        const rect = (selector: string) => document.querySelector(selector)!.getBoundingClientRect().toJSON() as DOMRect;
        return { img: rect('[data-photo-main] .swiper-slide-active img'), bar: rect('[data-photo-bar]'),
          strip: rect('[data-photo-strip]'), back: rect('[data-photo-nav="back"]'), viewport: innerHeight };
      });
      const { img } = read;
      assert.ok(img.top >= 24 - .5 && img.bottom <= read.viewport - 148 + .5, `大图越出了上下安全区：${img.top}–${img.bottom}`);
      assert.ok(Math.abs(img.width / img.height - 1200 / 4000) < .01, `竖图被拉变形：${img.width}×${img.height}`);
      assert.ok(Math.abs(img.left + img.width / 2 - DESKTOP.width / 2) <= 1, '大图没有水平居中');
      assert.ok(read.bar.bottom <= read.strip.top, '工具条压到了缩略图条上');
      assert.equal(Math.round(read.viewport - read.strip.bottom), 14);
      assert.ok(read.back.right <= 72, '翻页键伸进了图片那一栏');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('图片灯箱只有一张时不画缩略图条、页码点和翻页键，底部空间还给图片', { timeout: 60_000 }, async () => {
    const opened = await openLightbox(browser, { count: 1, width: 4000, height: 3000 });
    try {
      const read = await opened.page.evaluate(() => {
        const style = (selector: string) => getComputedStyle(document.querySelector(selector)!);
        return {
          strip: style('[data-photo-strip]').display,
          nav: [...document.querySelectorAll('[data-photo-nav]')].map((button) => getComputedStyle(button).display),
          pagination: document.querySelectorAll('[data-photo-pagination]').length,
          padding: style('[data-photo-main] .swiper-zoom-container').paddingBottom,
          count: document.querySelector('[data-photo-count]')!.textContent,
        };
      });
      assert.deepEqual(read, { strip: 'none', nav: ['none', 'none'], pagination: 0, padding: '76px', count: '1 / 1' });
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('灯箱圆钮：图标压在圆心，线头是圆的、不填充；前进那枚是同一枚箭头转半圈，到头那枚让开', { timeout: 60_000 }, async () => {
    const opened = await openLightbox(browser, { count: 3, width: 4000, height: 3000 });
    try {
      const read = await opened.page.evaluate(() => [
        '[data-photo-close]', '[data-photo-nav="back"]', '[data-photo-nav="fwd"]', '[data-photo-detail-toggle]',
      ].map((selector) => {
        const button = document.querySelector(selector)!, svg = button.querySelector('svg')!;
        const outer = button.getBoundingClientRect(), inner = svg.getBoundingClientRect(), style = getComputedStyle(svg);
        return {
          selector, glyph: svg.querySelector('use')?.getAttribute('href'),
          off: Math.max(Math.abs(outer.left + outer.width / 2 - inner.left - inner.width / 2),
            Math.abs(outer.top + outer.height / 2 - inner.top - inner.height / 2)),
          fill: style.fill, cap: style.strokeLinecap, turn: style.transform,
          visibility: getComputedStyle(button).visibility,
        };
      }));
      for (const icon of read) {
        assert.ok(icon.off <= .5, `${icon.selector} 的图标偏离圆心 ${icon.off}px`);
        assert.equal(icon.fill, 'none', `${icon.selector} 的描边图标被填实了`);
        // Lucide 的 info 圆点是长度 .01 的短线，没有圆头就缩成看不见的一横。
        assert.equal(icon.cap, 'round', `${icon.selector} 的线头不是圆的`);
      }
      const [close, back, fwd, info] = read;
      assert.equal(close.glyph, '#i-x');
      assert.equal(info.glyph, '#i-info');
      assert.deepEqual([back.glyph, fwd.glyph], ['#i-chevron-left', '#i-chevron-left']);
      assert.equal(back.turn, 'none');
      assert.match(fwd.turn, /^matrix\(-1, /, '前进键的箭头没有转半圈');
      assert.deepEqual([back.visibility, fwd.visibility], ['hidden', 'visible'], '停在第一张时后退键该让开');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('关注页：标题 24px、窄屏 20px，药丸间距同首页 7px，读数用等宽字', { timeout: 90_000 }, async () => {
    const read = (page: Page) => page.evaluate(() => {
      const style = (selector: string) => getComputedStyle(document.querySelector(selector)!);
      return {
        title: style('[data-follow-title]').fontSize,
        gaps: ['[data-follow-filter-glass] [data-entity-states]', '[data-follow-filter-glass] [data-entity-tags]']
          .map((selector) => style(selector).columnGap),
        readout: style('[data-follow-readout]').fontFamily,
      };
    });
    const wide = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const shown = await read(wide.page);
      assert.equal(shown.title, '24px');
      assert.deepEqual(shown.gaps, ['7px', '7px'], '关注页的药丸间距和首页那条不一样');
      assert.match(shown.readout, /Cascadia Mono|Consolas|monospace/, `读数不是等宽字：${shown.readout}`);
      assert.deepEqual(wide.problems, []);
    } finally {
      await wide.close();
    }
    const narrow = await openFollowFeed(browser, '/follow', MOBILE);
    try {
      assert.equal((await read(narrow.page)).title, '20px', '窄屏的关注标题没有收到 20px');
      assert.deepEqual(narrow.problems, []);
    } finally {
      await narrow.close();
    }
  });

  it('关注详情的翻页圆钮：48px 玻璃底、窄屏 44px；落在图片黑边的视觉中心，太窄才退回 16/10 的安全内距；圆点离底 18/12', { timeout: 90_000 }, async () => {
    const read = (page: Page) => page.evaluate(() => {
      const frame = document.querySelector<HTMLElement>('#stage [data-follow-detail-media="image"]')!;
      const next = frame.querySelector('[data-follow-image-arrow="next"]')!, style = getComputedStyle(next);
      const outer = frame.getBoundingClientRect(), box = next.getBoundingClientRect();
      const dots = frame.querySelector('[data-follow-image-dots]')!.getBoundingClientRect();
      // 桩里的图都是 600×800：object-fit:contain 之后左右各留一道黑边。
      const rendered = Math.min(outer.width, outer.height * 600 / 800);
      const gutter = (outer.width - rendered) / 2;
      return {
        size: [box.width, box.height], background: style.backgroundColor, blur: style.backdropFilter,
        inset: outer.right - box.right, gutter, dotsBottom: outer.bottom - dots.bottom,
        framed: frame.hasAttribute('data-framed'),
        ratio: getComputedStyle(frame.querySelector('[data-follow-detail-poster]')!).aspectRatio,
      };
    });
    const centered = (shown: { gutter: number; size: number[] }, safe: number) =>
      shown.gutter >= shown.size[0]! + safe * 2 ? (shown.gutter - shown.size[0]!) / 2 : safe;
    const wide = await openFollowFeed(browser, `/follow/item/${DETAIL.gallery}`, DESKTOP,
      { ready: '#stage [data-follow-image-arrow="next"]' });
    try {
      await wide.page.waitForFunction(() => (document.querySelector('#stage [data-follow-detail-poster]') as HTMLImageElement)?.complete);
      const shown = await read(wide.page);
      assert.deepEqual(shown.size, [48, 48]);
      assert.equal(shown.background, 'rgba(0, 0, 0, 0.6)');
      assert.equal(shown.blur, 'blur(16px)');
      assert.ok(Math.abs(shown.inset - centered(shown, 16)) <= 1, `箭头没落在黑边中心：${JSON.stringify(shown)}`);
      assert.ok(Math.abs(shown.dotsBottom - 18) <= .5, `圆点离底 ${shown.dotsBottom}px`);
      // 画框比例跟整组图走：换图时详情不忽高忽低。
      assert.equal(shown.framed, true);
      assert.match(shown.ratio, /^0\.75\b/);
      assert.deepEqual(wide.problems, []);
    } finally {
      await wide.close();
    }
    const narrow = await openFollowFeed(browser, `/follow/item/${DETAIL.gallery}`, MOBILE,
      { ready: '#stage [data-follow-image-arrow="next"]' });
    try {
      await narrow.page.waitForFunction(() => (document.querySelector('#stage [data-follow-detail-poster]') as HTMLImageElement)?.complete);
      const shown = await read(narrow.page);
      assert.deepEqual(shown.size, [44, 44]);
      assert.ok(Math.abs(shown.inset - centered(shown, 10)) <= 1, `窄屏箭头内距不对：${JSON.stringify(shown)}`);
      assert.ok(Math.abs(shown.dotsBottom - 12) <= .5, `窄屏圆点离底 ${shown.dotsBottom}px`);
      assert.deepEqual(narrow.problems, []);
    } finally {
      await narrow.close();
    }
  });

  it('关注详情：没有预览的那一格占 16:9；标签按来源记下的类型取 r34 色板，未知类型取中性灰', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, `/follow/item/${DETAIL.bare}`, DESKTOP,
      { ready: '#stage [data-follow-detail-tags]' });
    try {
      const page = opened.page;
      const shown = await page.evaluate(() => ({
        placeholder: getComputedStyle(document.querySelector('#stage [data-follow-detail-placeholder]')!).aspectRatio,
        tags: Object.fromEntries([...document.querySelectorAll<HTMLElement>('#stage [data-follow-tag]')].map((tag) =>
          [tag.dataset.followTag, getComputedStyle(tag).getPropertyValue('--tag-color').trim()])),
      }));
      assert.equal(shown.placeholder, '16 / 9');
      const muted = await tokenColor(page, '#stage [data-follow-detail]', '--muted');
      const unknown = await page.evaluate(() => {
        const tag = document.querySelector<HTMLElement>('#stage [data-follow-tag="odd"]')!;
        const probe = document.createElement('div');
        probe.style.backgroundColor = 'var(--tag-color)';
        tag.append(probe);
        const value = getComputedStyle(probe).backgroundColor;
        probe.remove();
        return value;
      });
      assert.deepEqual({ ...shown.tags, odd: unknown }, {
        ow: '#d675d6', tracer: '#68c76f', kou: '#e36c6c', solo: '#55a7ff', animated: '#f5a24a', odd: muted,
      });
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  /* 作品详情（`item-detail` 岛）。桩数据见 `item-fixture.ts`：普通那一条评了 3 星、两位出演、
     一个厂牌一个系列，都带实体 id。桩里的片源没有正片，播放器那一条 VIDEOJS 错误不算。 */
  const withoutPlayer = (problems: string[]) => problems.filter((line) => !line.includes('VIDEOJS'));

  it('作品详情标题与评分：来源徽标站在标题第一行开头；整排星一种琥珀、评没评只看填不填，悬停预演到指针那一颗', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      const title = await page.evaluate(() => {
        const text = document.querySelector('#stage [data-detail-title]')!;
        const badge = text.querySelector('[class~="srcbig"]')!;
        const style = getComputedStyle(badge);
        return {
          clamp: getComputedStyle(text).webkitLineClamp,
          first: text.firstElementChild === badge,
          badge: { display: style.display, width: style.width, height: style.height, gap: style.marginRight },
          tools: document.querySelector('#stage [data-title-tools]')!.getBoundingClientRect().top
            >= text.getBoundingClientRect().bottom - 0.5,
        };
      });
      assert.deepEqual(title, {
        clamp: '2', first: true, badge: { display: 'inline-grid', width: '17px', height: '28px', gap: '8px' }, tools: true,
      }, '徽标是行内块、随文字一起被两行折叠裁住；那排键自成一行排在标题下面');

      const stars = page.locator('#stage [data-rate]');
      const read = () => stars.evaluateAll((nodes) => nodes.map((node) => ({
        color: getComputedStyle(node).color, filled: getComputedStyle(node.querySelector('svg')!).fill !== 'none',
      })));
      const amber = await tokenColor(page, '#stage [data-item-detail]', '--rating');
      await page.mouse.move(0, 0);
      const rest = await read();
      assert.deepEqual(rest.map((star) => star.color), Array(5).fill(amber), '换色那一档在浅色主题下凑不出两级都成立的灰');
      assert.deepEqual(rest.map((star) => star.filled), [true, true, true, false, false]);
      await stars.nth(1).hover();
      const preview = await read();
      assert.deepEqual(preview.map((star) => star.color), Array(5).fill(amber));
      assert.deepEqual(preview.map((star) => star.filled), [true, true, false, false, false]);
      const edges = await page.evaluate(() => {
        const box = (selector: string) => document.querySelector(`#stage ${selector}`)!.getBoundingClientRect();
        return { stars: box('[data-rating-stars]').left, title: box('[data-detail-title]').left };
      });
      assert.equal(edges.stars, edges.title - 4, '26px 命中区里的星形靠右约 4px 起笔，这一排往左让回来');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('作品详情身份区：各组按内容宽并排换行，名字行框容得下下伸部；系列是整行宽的图标链接，不是标签胶囊', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      const shown = await page.evaluate(() => {
        const stage = document.querySelector('#stage')!;
        const primary = stage.querySelector('[data-identity-primary]')!;
        const width = primary.getBoundingClientRect().width;
        const name = getComputedStyle(stage.querySelector('[data-id-group="performer"] [data-id-name]')!);
        const series = stage.querySelector('[data-series-link]')!;
        const link = getComputedStyle(series);
        return {
          primary: [getComputedStyle(primary).display, getComputedStyle(primary).flexWrap],
          narrower: [...primary.querySelectorAll('[data-id-group]')].every((group) => group.getBoundingClientRect().width < width),
          name: { ratio: parseFloat(name.lineHeight) / parseFloat(name.fontSize), overflow: name.textOverflow, align: name.textAlign },
          cursor: getComputedStyle(stage.querySelector('[data-id-group="performer"] [data-id-cell]')!).cursor,
          face: getComputedStyle(stage.querySelector('[data-id-group="performer"] [data-id-face]')!).backgroundColor,
          series: {
            display: link.display, wrap: link.overflowWrap, border: link.borderTopWidth,
            full: Math.abs(series.getBoundingClientRect().width - series.parentElement!.getBoundingClientRect().width) < 0.5,
          },
        };
      });
      assert.deepEqual(shown.primary, ['flex', 'wrap']);
      assert.equal(shown.narrower, true, '组按内容宽，共演作品不会一组占满一行');
      assert.ok(shown.name.ratio >= 1.5, `名字行高 ${shown.name.ratio} 倍字号，拉丁字母的下伸部会被省略号那层 overflow 裁掉`);
      assert.deepEqual([shown.name.overflow, shown.name.align], ['ellipsis', 'left']);
      assert.equal(shown.cursor, 'pointer');
      assert.notEqual(shown.face, 'rgba(0, 0, 0, 0)', '没图的头像画首字盘');
      assert.deepEqual(shown.series, { display: 'flex', wrap: 'anywhere', border: '0px', full: true });
      await page.locator('#stage [data-series-link]').hover();
      const hovered = await page.locator('#stage [data-series-link]').evaluate((node) =>
        [getComputedStyle(node).color, getComputedStyle(node).textDecorationLine]);
      assert.deepEqual(hovered, [await tokenColor(page, '#stage [data-item-detail]', '--tungsten'), 'none']);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('作品详情身份区：没实体 id 的格子不给手形，厂牌标识铺满方框', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      // 先经桩取到原样的那一条；`route.fetch()` 会绕过桩直接打到服务器。
      const base = await page.evaluate(() => fetch('/api/item?id=14').then((response) => response.json()));
      const payload = {
        ...base, performers: ['无名氏'], performer_total: 1, performer_entities: [{ id: 0, has_image: false }], has_studio_logo: true,
        entity_refs: { ...base.entity_refs,
          performer: [{ id: 0, name: '无名氏', has_image: false, avatar_focus: null }],
          studio: [{ id: 50, name: 'Peach Studio', has_image: false, has_logo: true }] },
      };
      await page.route((url) => url.pathname === '/api/item', (route) => route.fulfill({ json: payload }));
      await page.goto(new URL('/item/14', page.url()).href, { waitUntil: 'load' });
      await page.locator('#stage [data-id-cell="studio"] img').waitFor({ timeout: 15_000 });
      await settle(page);
      const shown = await page.evaluate(() => {
        const cell = (kind: string) => document.querySelector(`#stage [data-id-cell="${kind}"]`)!;
        const face = cell('studio').querySelector('[data-id-face]')!.getBoundingClientRect();
        const img = cell('studio').querySelector('img')!;
        const box = img.getBoundingClientRect();
        return {
          performer: [cell('performer').tagName, getComputedStyle(cell('performer')).cursor],
          studio: getComputedStyle(cell('studio')).cursor,
          fit: getComputedStyle(img).objectFit,
          filled: [box.left - face.left, box.top - face.top, box.width - face.width, box.height - face.height]
            .every((delta) => Math.abs(delta) < 0.5),
        };
      });
      assert.deepEqual(shown, { performer: ['SPAN', 'default'], studio: 'pointer', fit: 'cover', filled: true },
        '标识文件自带边距，页面再补 inset 或换成 contain 就多围出一圈框');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('作品详情标签与反馈键：标签和卡片同一张脸，筛选那半边悬停抬填充；反馈条每一枚悬停都换色', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      const face = await page.evaluate(() => {
        const tag = document.querySelector('#stage [data-detail-tag]')!;
        const probe = document.createElement('div');
        probe.style.cssText = 'border:1px solid var(--line);border-radius:var(--tag-radius);background:var(--tag-fill);color:var(--ink-2)';
        tag.parentElement!.append(probe);
        const want = getComputedStyle(probe);
        const expected = { radius: want.borderTopLeftRadius, line: want.borderTopColor, fill: want.backgroundColor, ink: want.color };
        probe.remove();
        const style = getComputedStyle(tag);
        return { expected, actual: { radius: style.borderTopLeftRadius, line: style.borderTopColor,
          fill: style.backgroundColor, ink: getComputedStyle(tag.querySelector('[data-tag]')!).color } };
      });
      assert.deepEqual(face.actual, face.expected, '圆角、线、填充与字色都走卡片那颗 `.tg` 的同一组 token');
      const filter = page.locator('#stage [data-detail-tag] [data-tag]').first();
      await filter.hover();
      assert.equal(await filter.evaluate((node) => getComputedStyle(node).backgroundColor),
        await tokenColor(page, '#stage [data-item-detail]', '--hover'));

      const buttons = ['[data-fb="like"]', '[data-fb="reason"]', '.dislike', '.seen', '.later', '[data-fb="playlist"]',
        '[data-fb="quality"]', '[data-fb="dispose"]'];
      const unchanged: string[] = [];
      for (const selector of buttons) {
        const button = page.locator(`#stage .fb ${selector}`);
        const color = () => button.evaluate((node) => {
          node.getAnimations({ subtree: true }).forEach((animation) => animation.finish());
          return getComputedStyle(node).color;
        });
        await page.mouse.move(0, 0);
        const rest = await color();
        await button.hover();
        if (await color() === rest) unchanged.push(selector);
      }
      assert.deepEqual(unchanged, [], '漏写配色的那一枚全程停在 --muted，看着像不能点');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('作品详情喜爱理由框与「接着看」：输入框聚焦画 BoardUI 那枚 2px 内环；接着看和侧栏同底、顶上一条细线', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      await page.locator('#stage [data-media-card]').first().waitFor({ timeout: 15_000 });
      await page.locator('#preferenceToggle').click();
      const field = page.locator('#stage [data-item-preference] textarea');
      await field.focus();
      const ring = await field.evaluate((node) => {
        node.getAnimations().forEach((animation) => animation.finish());
        return getComputedStyle(node).boxShadow;
      });
      const active = await tokenColor(page, '#stage [data-item-detail]', '--color-border-button-active');
      assert.equal(ring, `${active} 0px 0px 0px 2px inset`);

      const related = await page.evaluate(() => {
        const block = document.querySelector('#stage [data-item-related]')!;
        const style = getComputedStyle(block);
        const row = getComputedStyle(block.querySelector('[data-related-row]')!);
        return {
          fill: style.backgroundColor, side: getComputedStyle(document.querySelector('#stage [data-item-side]')!).backgroundColor,
          line: [style.borderTopWidth, style.borderTopStyle, style.borderTopColor],
          heading: getComputedStyle(block.querySelector('h3')!).fontWeight,
          row: [row.display, row.overflowX, row.scrollbarWidth],
        };
      });
      assert.equal(related.fill, related.side, '同一格详情的两块，底色同源，不然整幅宽度上留一道色差');
      assert.deepEqual(related.line, ['1px', 'solid', await tokenColor(page, '#stage', '--line-soft')]);
      assert.equal(related.heading, '600');
      assert.deepEqual(related.row, ['flex', 'auto', 'none'], '那一排横滚，不露系统滚动条');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('作品详情队列与说明块：版次徽章和标题同一行、不斜体；脱盘说明块铺满播放器格', { timeout: 60_000 }, async () => {
    const editions = await openItemPage(browser, `/editions/${ITEM.edition}/${ITEM.edition}`, DESKTOP,
      { ready: '#stage [data-queue-edition]' });
    try {
      const shown = await editions.page.evaluate(() => {
        const badge = document.querySelector('#stage [data-queue-edition]')!;
        const head = badge.parentElement!;
        const name = head.querySelector('b')!.getBoundingClientRect();
        const box = badge.getBoundingClientRect();
        return {
          head: [getComputedStyle(head).display, getComputedStyle(head).flexDirection],
          badge: [getComputedStyle(badge).fontStyle, getComputedStyle(badge).flexShrink],
          sameRow: box.top < name.bottom && box.bottom > name.top,
          heading: getComputedStyle(document.querySelector('#stage .mixqueuehead h2')!).fontWeight,
        };
      });
      assert.deepEqual(shown, { head: ['flex', 'row'], badge: ['normal', '0'], sameRow: true, heading: '600' },
        '`<i>` 默认斜体，徽章不是强调语气');
      assert.deepEqual(withoutPlayer(editions.problems), []);
    } finally {
      await editions.close();
    }
    const offline = await openItemPage(browser, `/item/${ITEM.offline}`, DESKTOP, { ready: '#stage #offlineGate' });
    try {
      const fit = await offline.page.evaluate(() => {
        const gate = document.querySelector('#stage #offlineGate')!;
        const cell = gate.parentElement!;
        const a = gate.getBoundingClientRect(), b = cell.getBoundingClientRect();
        return {
          filled: [a.left - b.left, a.top - b.top, a.width - b.width, a.height - b.height].every((delta) => Math.abs(delta) < 0.5),
          radius: [getComputedStyle(gate).borderTopLeftRadius, getComputedStyle(cell).borderTopLeftRadius],
        };
      });
      assert.equal(fit.filled, true, '说明块铺满播放器格，不上下留黑');
      assert.equal(fit.radius[0], fit.radius[1], '圆角跟着格走');
      assert.notEqual(fit.radius[0], '0px');
      assert.deepEqual(offline.problems, []);
    } finally {
      await offline.close();
    }
  });

  it('作品详情标签选择器用全站下拉面板那一对开合动效，减少动态效果时当场开合', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      const picker = page.locator('#stage [data-tag-picker]');
      const motion = () => page.evaluate(() => {
        const node = document.querySelector<HTMLElement>('#stage [data-tag-picker]');
        return node && !node.hidden ? getComputedStyle(node).animationName : 'closed';
      });
      const cycle = async () => {
        await page.locator('#tagPlus').click();
        await page.locator('#tagPickSearch').waitFor();
        const opening = await motion();
        await page.locator('#stage [data-rating-value]').click();
        const closing = await motion();
        await picker.waitFor({ state: 'hidden' });
        return [opening, closing];
      };
      assert.deepEqual(await cycle(), ['none', 'closed']);
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      assert.deepEqual(await cycle(), ['board-menu-in', 'board-menu-out']);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });
});
