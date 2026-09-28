/* 沉浸模式的取流与舞台形状。
 *
 * 队列固定成演示库里的一条横屏加一条竖屏：`/api/items` 的随机抽样换成这两条，谁先谁后由
 * 起播 id 定。竖屏那条的 `/stream` 故意晚回，预加载窗口拉到能采样的长度。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { launch, visit, VIEWPORTS } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const HOLD_MS = 1500;

type Item = { id: number; width: number; height: number };
type Sample = { wide: boolean; empty: boolean; framed: boolean; slides: string[] };

/** 当前的舞台：形状、轨道空不空、空着时画没画框，以及每一格的位移。 */
const sample = (page: Page) => page.evaluate((): Sample => {
  const track = document.querySelector<HTMLElement>('#tokTrack')!;
  const style = getComputedStyle(track);
  return {
    wide: document.querySelector('.tokstage')!.classList.contains('wide'),
    empty: !track.children.length,
    framed: style.backgroundColor !== 'rgba(0, 0, 0, 0)' || style.boxShadow !== 'none',
    slides: [...track.querySelectorAll<HTMLElement>('.tokslide')].map((slide) => slide.style.transform),
  };
});

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

  it('片源先问 stream-plan；新片预加载时舞台保持旧形状，出画那一刻才换', async () => {
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
      await page.route(new RegExp(`/stream\\?id=${tall.id}&`), async (route) => {
        await new Promise((resolve) => setTimeout(resolve, HOLD_MS));
        await route.continue().catch(() => {});
      });
      // 这台机器旁边有人：新插进来的每条 video 一律静音。
      await page.addInitScript(() => {
        new MutationObserver(() => document.querySelectorAll('video').forEach((video) => { video.muted = true; }))
          .observe(document, { childList: true, subtree: true });
      });
      await page.goto(new URL(`/immerse?id=${wide.id}`, page.url()).href, { waitUntil: 'load' });

      const loading = await sample(page);
      if (loading.empty) assert.equal(loading.framed, false, '第一条还没到时轨道不画框');
      await settled(page);
      assert.deepEqual(await sample(page), { wide: true, empty: false, framed: true, slides: [''] });
      assert.deepEqual(planned, [wide.id]);

      await page.dispatchEvent('#tok', 'wheel', { deltaY: 100 });
      await page.waitForFunction(() => document.querySelectorAll('#tokTrack .tokslide').length === 2);
      const preloading: Sample[] = [];
      const deadline = Date.now() + HOLD_MS - 300;
      while (Date.now() < deadline) {
        preloading.push(await sample(page));
        await new Promise((resolve) => setTimeout(resolve, 60));
      }
      assert.ok(preloading.length > 3, `预加载窗口里只采到 ${preloading.length} 次`);
      for (const moment of preloading) {
        assert.deepEqual(moment, { wide: true, empty: false, framed: true, slides: ['', 'translateY(100%)'] });
      }
      await settled(page);
      assert.deepEqual(await sample(page), { wide: false, empty: false, framed: true, slides: [''] });
      assert.deepEqual(planned, [wide.id, tall.id]);
      assert.deepEqual(opened.problems, [], JSON.stringify(opened.problems));
    } finally {
      await opened.close();
    }
  });
});
