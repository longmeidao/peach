/* 关注页岛（`follow-feed`）在真浏览器里的行为：取样、筛选进地址栏、只有列表铺骨架、照片墙、
 * 续页、写操作、检查与往回抓的忙态、Shift 连选，以及进详情再回来。
 *
 * 桩数据与定种子见 `follow-fixture.ts`；关注来源的真实抓取一次都不发。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { FIRST, MORE, openFollowFeed } from './follow-fixture.ts';
import { launch, layout, VIEWPORTS } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const MOBILE = VIEWPORTS.find((viewport) => viewport.mobile)!;
const CARDS = '[data-follow-list] > [data-follow-item]';

const authorOrder = (page: Page) => page.locator('button[data-follow-author]').evaluateAll((buttons) =>
  buttons.map((button) => (button as HTMLElement).dataset.followAuthor));
const cardIds = (page: Page) => page.locator(CARDS).evaluateAll((cards) =>
  cards.map((card) => Number((card as HTMLElement).dataset.followItem)));
/** 桩里的条目没有正片，详情的播放器拿到空响应会报一条 VIDEOJS 错误；这一条量的是列表，不算它。 */
const withoutPlayer = (problems: string[]) => problems.filter((line) => !line.includes('VIDEOJS'));
/** 等地址栏换到给定的查询串；岛只交 view，地址由壳写。 */
const searchIs = (page: Page, search: string) => page.waitForFunction(
  (wanted) => location.pathname === '/follow' && location.search === wanted, search, { timeout: 10_000 });

describe('关注页岛', () => {
  let browser: Browser;

  before(async () => {
    browser = await launch();
  });

  after(async () => {
    await browser.close();
  });

  for (const viewport of [DESKTOP, MOBILE]) {
    it(`${viewport.name} 多图数量按钮可以打开详情`, { timeout: 60_000 }, async () => {
      const opened = await openFollowFeed(browser, '/follow?media=images', viewport, { settings: { followImagesOnly: false } });
      try {
        const page = opened.page;
        const payload = await page.evaluate(async () => {
          const list = await (await fetch('/api/follow?media=images')).json();
          const detail = await (await fetch('/api/follow?item=5001')).json();
          list.groups = detail.groups.map((group: Record<string, unknown>) => ({
            ...group, stack: { media: 3, kind: 'image', faces: [] },
          }));
          list.has_more = false;
          return list;
        });
        await page.route((url) => url.pathname === '/api/follow' && !url.searchParams.has('item'),
          (route) => route.fulfill({ json: payload }));
        await page.reload({ waitUntil: 'networkidle' });
        await page.locator('[data-follow-list] [data-follow-collection="5001"]').click();
        await page.waitForURL('**/follow/item/5001');
        await page.locator('#stage[open]').waitFor();
        assert.deepEqual(withoutPlayer(opened.problems), []);
      } finally {
        await opened.close();
      }
    });
  }

  it('首屏：「全部」按下，页头、两排、筛选浮层、列表自上而下', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      assert.equal(await page.locator('[data-follow-filter=""]').getAttribute('aria-pressed'), 'true');
      assert.equal(await page.locator('[data-follow-filter="new"]').getAttribute('aria-pressed'), 'false');
      const tops = await page.evaluate(() => ['[data-follow-head]', '[data-follow-authors]', '[data-follow-works]',
        '[data-follow-filter-glass]', '[data-follow-list]']
        .map((selector) => document.querySelector(selector)?.getBoundingClientRect().top ?? null));
      assert.ok(tops.every((top) => top !== null), `有一块没画出来：${JSON.stringify(tops)}`);
      assert.deepEqual([...tops].sort((a, b) => a! - b!), tops, `上下次序不对：${JSON.stringify(tops)}`);
      assert.deepEqual(await cardIds(page), FIRST.filter((row) => row.primary.media_kind === 'video')
        .map((row) => row.primary.id));
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('两排按种子取样：换状态推回新 view 不洗牌，换一批才换', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      const first = await authorOrder(page);
      assert.equal(first.length, 6);
      await page.locator('[data-follow-filter="new"]').click();
      await searchIs(page, '?status=new');
      await page.locator('[data-follow-filter="new"][aria-pressed="true"]').waitFor();
      assert.deepEqual(await authorOrder(page), first, '换状态之后创作者那一排重新洗了');
      await page.getByRole('button', { name: '换一批', exact: true }).click();
      await page.waitForFunction(() => new URLSearchParams(location.search).get('sort') === 'rand');
      await page.waitForFunction((before) => JSON.stringify([...document.querySelectorAll<HTMLElement>(
        'button[data-follow-author]')].map((button) => button.dataset.followAuthor)) !== before, JSON.stringify(first));
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('点创作者、题材、标签进组合条并写进地址栏；组合条在读数之后、列表之前', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      await page.locator('button[data-follow-author="name:mira"]').click();
      await searchIs(page, '?author=name%3Amira');
      await page.locator('button[data-follow-work="zelda"]').click();
      await searchIs(page, '?author=name%3Amira&work=zelda');
      await page.locator('button[data-follow-tag="loop"]').click();
      await searchIs(page, '?author=name%3Amira&tag=loop&work=zelda');
      const drops = await page.locator('[data-follow-drop]').evaluateAll((buttons) =>
        buttons.map((button) => (button as HTMLElement).dataset.followDropKind));
      assert.deepEqual(drops, ['创作者', '题材', '标签'], `组合条的条件不对：${JSON.stringify(drops)}`);
      const [readout, combo, list] = await page.evaluate(() => ['[data-follow-readout]', '[data-follow-combo]',
        '[data-follow-list-body]'].map((selector) => document.querySelector(selector)!.getBoundingClientRect()));
      assert.ok(readout!.bottom <= combo!.top + 1 && combo!.bottom <= list!.top + 1,
        `组合条不在读数与列表之间：${JSON.stringify([readout, combo, list])}`);
      // 撤掉一条，交回去的是撤掉之后的地址。
      await page.locator('[data-follow-drop="loop"]').click();
      await searchIs(page, '?author=name%3Amira&work=zelda');
      // 再点按下的那位创作者就撤掉它。
      await page.locator('button[data-follow-author="name:mira"]').click();
      await searchIs(page, '?work=zelda');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('换状态药丸时只有列表铺骨架，页头与两排原样留着', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      opened.stub.hold = (url) => url.searchParams.get('status') === 'saved';
      await page.locator('[data-follow-filter="saved"]').click();
      await page.locator('[data-follow-list-body] [data-skeleton]').waitFor({ timeout: 10_000 });
      const during = await page.evaluate(() => ({
        head: !!document.querySelector('[data-follow-feed] [data-follow-head]'),
        authors: document.querySelectorAll('button[data-follow-author]').length,
        glass: !!document.querySelector('[data-follow-filter-glass]'),
        wholePage: !!document.querySelector('#stats .followauthors'),
        skeletons: document.querySelectorAll('[data-skeleton]').length,
      }));
      assert.deepEqual(during, { head: true, authors: 6, glass: true, wholePage: false, skeletons: 1 });
      await opened.stub.release();
      await page.locator('[data-follow-list-body] [data-skeleton]').waitFor({ state: 'detached', timeout: 10_000 });
      await page.locator(CARDS).first().waitFor();
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('视频卡与照片墙互换；照片墙的尺寸档换列数，手机上不横向溢出', { timeout: 90_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      await page.locator('[data-media-view="images"]').click();
      await searchIs(page, '?media=images');
      await page.locator('[data-follow-list][data-follow-wall] > [data-follow-item]').first().waitFor();
      assert.deepEqual(await cardIds(page), FIRST.filter((row) => row.primary.media_kind === 'image')
        .map((row) => row.primary.id));
      const columns = () => page.locator('[data-follow-wall]').evaluate((wall) => ({
        size: (wall as HTMLElement).dataset.size, count: getComputedStyle(wall).columnCount,
      }));
      const small = await columns();
      await page.locator('#density').click();
      await page.locator('[data-follow-wall][data-size="big"]').waitFor();
      const big = await columns();
      assert.equal(small.size, 'small');
      assert.ok(Number(big.count) < Number(small.count), `大图档没有少几列：${JSON.stringify([small, big])}`);
      await page.locator('[data-media-view="videos"]').click();
      await searchIs(page, '');
      await page.locator('[data-follow-list]:not([data-follow-wall]) > [data-follow-item]').first().waitFor();
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
    const mobile = await openFollowFeed(browser, '/follow?media=images', MOBILE);
    try {
      const geometry = await layout(mobile.page);
      assert.ok(geometry.scrollWidth <= geometry.viewportWidth,
        `手机照片墙横向溢出 ${geometry.scrollWidth}>${geometry.viewportWidth}：${geometry.offenders.join('、')}`);
      assert.deepEqual(mobile.problems, []);
    } finally {
      await mobile.close();
    }
  });

  it('加载更多接在原来那些卡后面', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      const before = await cardIds(page);
      const more = page.getByRole('button', { name: '加载更多' });
      await more.scrollIntoViewIfNeeded();
      // 滚到底续页会自己接上；没接上再按一下。
      await page.waitForTimeout(800);
      if (!(await page.locator(`[data-follow-item="${MORE[0]!.primary.id}"]`).count())) await more.click().catch(() => {});
      await page.locator(`[data-follow-item="${MORE.at(-1)!.primary.id}"]`).waitFor({ timeout: 10_000 });
      assert.deepEqual(await cardIds(page), [...before, ...MORE.map((row) => row.primary.id)]);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('标记已看与稍后看：请求体只带条目与目标，卡上立刻换状态', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      const card = page.locator('[data-follow-item="1001"]');
      await card.hover();
      await card.locator('[data-follow-status="1001"][data-to="seen"]').click();
      await page.locator('[data-follow-item="1001"][data-status="seen"]').waitFor();
      // 已看的那张多出「恢复未看」。
      assert.equal(await card.locator('[data-to="new"]').count(), 1);
      await card.hover();
      await card.locator('[data-follow-save="1001"]').click();
      await card.locator('[data-follow-save="1001"][aria-label="已保存"]').waitFor();
      assert.deepEqual(opened.stub.writes, [
        { url: '/api/follow/status', body: { item: 1001, to: 'seen' } },
        { url: '/api/follow/save', body: { item: 1001 } },
      ]);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('检查更新与往回抓起同一趟任务，任务在跑时两枚键一起忙', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      await page.locator('[data-follow-older]').click();
      await page.locator('[data-follow-older][aria-busy="true"]').waitFor();
      await page.locator('[data-follow-older]').filter({ hasText: '抓取中' }).waitFor();
      assert.match(await page.locator('[data-follow-older]').innerText(), /抓取中/);
      await page.locator('[data-follow-recheck][aria-busy="true"]').waitFor();
      assert.deepEqual(opened.stub.writes, [{ url: '/api/follow/check', body: { older: true, background: true } }]);
      assert.equal(await page.evaluate(() => sessionStorage.getItem('peach-follow-job')), 'job-1');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
    const again = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = again.page;
      await page.locator('[data-follow-recheck]').click();
      await page.locator('[data-follow-recheck][aria-busy="true"]').waitFor();
      await page.locator('[data-follow-older][aria-busy="true"]').waitFor();
      // 检查那一趟只让往回抓那枚忙、不换字。
      assert.equal(await page.locator('[data-follow-older]').innerText(), '抓更早的一页');
      assert.deepEqual(again.stub.writes, [{ url: '/api/follow/check', body: { background: true } }]);
      assert.deepEqual(again.problems, []);
    } finally {
      await again.close();
    }
  });

  it('多选里 Shift 连选按屏幕上的次序框进一段', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      const ids = await cardIds(page);
      await page.locator('#selectMode').click();
      await page.locator('[data-follow-feed][data-select-mode]').waitFor();
      await page.locator(`[data-follow-item="${ids[1]}"]`).click();
      await page.locator(`[data-follow-item="${ids[4]}"]`).click({ modifiers: ['Shift'] });
      await page.locator(`[data-follow-item="${ids[4]}"][data-selected]`).waitFor();
      const picked = await page.locator(`${CARDS}[data-selected]`).evaluateAll((cards) =>
        cards.map((card) => Number((card as HTMLElement).dataset.followItem)));
      assert.deepEqual(picked, ids.slice(1, 5));
      assert.equal(new URL(page.url()).pathname, '/follow', '多选里点卡不该进详情');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('点卡进详情，关掉回到同一个岛、同一批卡；深链进详情关掉时才挂岛', { timeout: 90_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow?status=new', DESKTOP);
    try {
      const page = opened.page;
      const before = await cardIds(page);
      await page.evaluate(() => { (document.querySelector('[data-follow-feed]') as HTMLElement & { mark?: number }).mark = 7 });
      await page.locator('[data-follow-item="1002"] [data-follow-open]').click();
      await page.waitForFunction(() => location.pathname === '/follow/item/1002');
      await page.locator('#stage[open]').waitFor();
      await page.locator('#closeStage').click();
      await searchIs(page, '?status=new');
      await page.locator(CARDS).first().waitFor();
      assert.equal(await page.evaluate(() => (document.querySelector('[data-follow-feed]') as HTMLElement & { mark?: number }).mark),
        7, '回到列表时岛重挂了');
      assert.deepEqual(await cardIds(page), before);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
    const deep = await openFollowFeed(browser, '/follow/item/1003', DESKTOP, { ready: '#stage[open]' });
    try {
      const page = deep.page;
      assert.equal(await page.locator('[data-follow-feed]').count(), 0, '深链进详情时不该挂岛');
      await page.locator('#closeStage').click();
      await page.locator(CARDS).first().waitFor({ timeout: 15_000 });
      assert.equal(new URL(page.url()).pathname, '/follow');
      assert.deepEqual(withoutPlayer(deep.problems), []);
    } finally {
      await deep.close();
    }
  });
});
