/* 沉浸模式的取流与舞台形状。
 *
 * 队列固定成演示库里的一条横屏加一条竖屏：`/api/items` 的随机抽样换成这两条，谁先谁后由
 * 起播 id 定。两条的 `/stream` 都故意晚回，首条加载与切片预加载的窗口拉到能采样的长度。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { launch, visit, VIEWPORTS } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const HOLD_MS = 1500;

type Item = { id: number; width: number; height: number };
type Sample = { wide: boolean; shown: boolean; slides: string[] };

/** 当前的舞台：形状、框与动作列、作者标题看不看得见，以及每一格的位移。 */
const sample = (page: Page) => page.evaluate((): Sample => ({
  wide: document.querySelector('.tokstage')!.classList.contains('wide'),
  shown: ['.tokstage', '.tokbtns', '.tokui'].every((selector) =>
    getComputedStyle(document.querySelector(selector)!).visibility === 'visible'),
  slides: [...document.querySelectorAll<HTMLElement>('#tokTrack .tokslide')].map((slide) => slide.style.transform),
}));

/** 每 60ms 采一次，直到 `until` 成立或到点。 */
async function watch(page: Page, until: () => Promise<boolean>, ms: number) {
  const moments: Sample[] = [];
  const deadline = Date.now() + ms;
  while (Date.now() < deadline && !(await until())) {
    moments.push(await sample(page));
    await new Promise((resolve) => setTimeout(resolve, 60));
  }
  return moments;
}

/** 只剩一格、加载提示收起、这一格的 video 有画面可出。 */
const settled = (page: Page) => page.waitForFunction(() =>
  document.querySelectorAll('#tokTrack .tokslide').length === 1
  && Boolean(document.querySelector<HTMLElement>('#tokLoader')?.hidden)
  && (document.querySelector<HTMLVideoElement>('#tokTrack .tokslide video')?.readyState ?? 0) >= 2,
undefined, { timeout: 20_000 });

describe('沉浸模式', () => {
  let browser: Browser;
  before(async () => { browser = await launch(); });
  after(async () => { await browser?.close(); });

  it('片源先问 stream-plan；首条出画前不露舞台，切片预加载时保持旧形状，出画那一刻才换', async () => {
    const opened = await visit(browser, '/', DESKTOP);
    const { page } = opened;
    try {
      const items: Item[] = await page.evaluate(async () =>
        (await (await fetch('/api/items?limit=60&offset=0&thumb=')).json()).items);
      const wide = items.find((item) => item.width > item.height);
      const tall = items.find((item) => item.height > item.width);
      assert.ok(wide && tall, '演示库里横屏、竖屏各要有一条');
      await page.route(/\/api\/items\?.*sort=rand/, (route) => route.fulfill({ json: { items: [wide, tall]
        .map((item) => items.find((full) => full.id === item.id)) } }));
      const planned: number[] = [];
      page.on('request', (request) => {
        const url = new URL(request.url());
        if (url.pathname === '/api/stream-plan') planned.push(Number(url.searchParams.get('id')));
      });
      await page.route(new RegExp(`/stream\\?id=(${wide.id}|${tall.id})&`), async (route) => {
        await new Promise((resolve) => setTimeout(resolve, HOLD_MS));
        await route.continue().catch(() => {});
      });
      // 这台机器旁边有人：新插进来的每条 video 一律静音。
      await page.addInitScript(() => {
        new MutationObserver(() => document.querySelectorAll('video').forEach((video) => { video.muted = true; }))
          .observe(document, { childList: true, subtree: true });
      });
      await page.goto(new URL(`/immerse?id=${wide.id}`, page.url()).href, { waitUntil: 'load' });

      // 首条出画前：框、动作列、作者标题一样都不露，出画时一次摆成横屏。
      const loaderHidden = () => page.evaluate(() => document.querySelector<HTMLElement>('#tokLoader')!.hidden);
      const loading = await watch(page, loaderHidden, 20_000);
      assert.ok(loading.length > 3, `首条加载窗口里只采到 ${loading.length} 次`);
      for (const moment of loading) assert.equal(moment.shown, false, JSON.stringify(moment));
      await settled(page);
      assert.deepEqual(await sample(page), { wide: true, shown: true, slides: [''] });
      assert.deepEqual(planned, [wide.id]);

      await page.dispatchEvent('#tok', 'wheel', { deltaY: 100 });
      await page.waitForFunction(() => document.querySelectorAll('#tokTrack .tokslide').length === 2);
      const preloading = await watch(page, async () => false, HOLD_MS - 300);
      assert.ok(preloading.length > 3, `预加载窗口里只采到 ${preloading.length} 次`);
      for (const moment of preloading) {
        assert.deepEqual(moment, { wide: true, shown: true, slides: ['', 'translateY(100%)'] });
      }
      await settled(page);
      assert.deepEqual(await sample(page), { wide: false, shown: true, slides: [''] });
      assert.deepEqual(planned, [wide.id, tall.id]);
      assert.deepEqual(opened.problems, [], JSON.stringify(opened.problems));
    } finally {
      await opened.close();
    }
  });
});
