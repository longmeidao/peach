/* 女优资料页照片档的番号样张集（ADR-0068）。
 *
 * 演示库没有人物实体，也没有样张：资料、照片清单、封面和样张图都由这里按接口的形状给，
 * 页面自己的路由、渲染、深链与灯箱照常跑。第 2 张样张故意回 404，验「取不到的那格留着占位、
 * 灯箱照样翻得到」。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { launch, settle, visit, VIEWPORTS, type Visit } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const NAME = '七沢みあ';
const SET_ID = 'code:SSIS-057';
// 1×1 的 PNG，封面与样张都用它：这里验的是结构与交互，不是图。
const PIXEL = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  'base64');
const MISSING = /\/sample-(?:thumb|image)\?code=SSIS-057&n=2$/;

async function serveProfile(page: Page): Promise<void> {
  await page.route(/\/api\/entity\?/, (route) => route.fulfill({ json: {
    id: 90_001, kind: 'performer', canonical_name: NAME, aliases: [], display_aliases: [],
    user_aliases: [], asset_count: 0, tags: [], related_performers: [], links: [],
    metadata: {}, has_image: false, has_avatar: false, avatar_focus: null,
    representative_asset_id: null, entry_links: [], feed: { following: false },
  } }));
  await page.route(/\/api\/photos\?/, (route) => route.fulfill({ json: {
    kind: 'performer', name: NAME, entity_id: 90_001, total: 0, items: [], seed: '', has_more: false,
    sample_total: 3,
    sets: [{ id: SET_ID, kind: 'code', code: 'SSIS-057', name: '雨の日', title: 'SSIS-057 雨の日', n: 3,
      release_date: '2021-05-18', site: 'dmm', site_label: 'DMM', has_cover: true }],
  } }));
  await page.route(/\/cover\?code=SSIS-057/, (route) =>
    route.fulfill({ status: 200, contentType: 'image/png', body: PIXEL }));
  await page.route(/\/sample-(?:thumb|image)\?/, (route) => MISSING.test(route.request().url())
    ? route.fulfill({ status: 404, json: { error: 'unavailable' } })
    : route.fulfill({ status: 200, contentType: 'image/png', body: PIXEL }));
}

async function openPhotos(browser: Browser, search: string): Promise<Visit> {
  const opened = await visit(browser, '/', DESKTOP);
  await serveProfile(opened.page);
  await opened.page.goto(new URL(`/performers/${encodeURIComponent(NAME)}?${search}`, opened.page.url()).href,
    { waitUntil: 'load' });
  await opened.page.locator('#index .photohead').waitFor({ state: 'visible', timeout: 15_000 });
  await settle(opened.page);
  return opened;
}

/** 故意回 404 的那一张不算运行期问题，浏览器为它各记一条的控制台 404 也按条数扣掉；
 * 其余照 harness 的口径一条都不许有。 */
function unexpected(problems: string[]): string[] {
  const planted = /^404 \/sample-/;
  let mirrors = problems.filter((problem) => planted.test(problem)).length;
  return problems.filter((problem) => {
    if (planted.test(problem)) return false;
    if (mirrors > 0 && /^console Failed to load resource: .*404/.test(problem)) { mirrors -= 1; return false; }
    return true;
  });
}

describe('番号样张集', () => {
  let browser: Browser;
  before(async () => { browser = await launch(); });
  after(async () => { await browser?.close(); });

  it('只有样张时照片档照样出现，墙上是一排番号集卡', async () => {
    const opened = await openPhotos(browser, 'media=photos');
    const { page } = opened;
    try {
      assert.equal(await page.locator('.entitymediaview [data-media-view="photos"]').getAttribute('aria-pressed'),
        'true');
      const card = page.locator('.photosets .codeset');
      assert.equal(await card.count(), 1);
      assert.match(await card.innerText(), /SSIS-057 雨の日/);
      assert.match(await card.innerText(), /3 张/);
      assert.match(await page.locator('.photohead h3').innerText(), /1 部作品样张/);
      assert.equal(await page.locator('.photohead .entitybatch').count(), 0, '没有本地图可换一批');
      assert.deepEqual(unexpected(opened.problems), [], JSON.stringify(opened.problems));
    } finally {
      await opened.close();
    }
  });

  it('点开一组进样张墙，地址带番号集 id，取不到的那格留着占位', async () => {
    const opened = await openPhotos(browser, 'media=photos');
    const { page } = opened;
    try {
      await page.locator('[data-code-set]').click();
      await page.waitForFunction(() => document.querySelectorAll('.photowall .photocell').length === 3);
      assert.equal(new URL(page.url()).searchParams.get('set'), SET_ID);
      assert.match(await page.locator('.photohead h3').innerText(), /SSIS-057 雨の日 · 3 张/);
      await page.waitForFunction(() => !document.querySelector('.photowall .photocell:nth-child(2) img'));
      const hole = await page.locator('.photowall .photocell').nth(1).boundingBox();
      assert.ok(hole && hole.height > 0, '占位格不塌');
      await page.locator('.photowall .photocell').first().click();
      const count = page.locator('dialog.photolight .photocount');
      await count.waitFor({ state: 'visible' });
      assert.equal((await count.innerText()).trim(), '1 / 3');
      await page.locator('dialog.photolight .photoclose').click();
      await page.locator('.photoback').click();
      await page.locator('.photosets .codeset').waitFor({ state: 'visible' });
      assert.equal(new URL(page.url()).searchParams.get('set'), null);
      assert.deepEqual(unexpected(opened.problems), [], JSON.stringify(opened.problems));
    } finally {
      await opened.close();
    }
  });

  it('深链直接进样张墙', async () => {
    const opened = await openPhotos(browser, `media=photos&set=${encodeURIComponent(SET_ID)}`);
    const { page } = opened;
    try {
      assert.equal(await page.locator('.photowall .photocell').count(), 3);
      assert.equal(await page.locator('.photoback').count(), 1);
      assert.deepEqual(unexpected(opened.problems), [], JSON.stringify(opened.problems));
    } finally {
      await opened.close();
    }
  });
});
