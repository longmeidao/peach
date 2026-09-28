/* 关注详情岛（`follow-detail`）在真浏览器里的行为：从列表进出、深链、舞台在媒体框里挂
 * Video.js、多图轮播、合集与多媒体两种队列、写操作与撤销、隐藏与恢复、标签回列表、手机。
 * 灯箱收到整组图那一条在 `photo-lightbox.test.ts`。
 *
 * 桩数据见 `follow-fixture.ts`（`DETAIL` 那几种形态只经单条取数交回）；关注来源的真实抓取一次都不发。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { DETAIL, openFollowFeed } from './follow-fixture.ts';
import { layout, launch, VIEWPORTS } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const MOBILE = VIEWPORTS.find((viewport) => viewport.mobile)!;
const DETAIL_READY = '#stage[open] [data-follow-detail-side]';
/** 桩里的视频没有正片，播放器拿到空响应会报一条 VIDEOJS 错误；量的不是它。 */
const withoutPlayer = (problems: string[]) => problems.filter((line) => !line.includes('VIDEOJS'));
const pathIs = (page: Page, path: string) => page.waitForFunction(
  (wanted) => location.pathname === wanted, path, { timeout: 10_000 });

/** 记下这一页之后发出的关注列表请求与单条取数，分开数。 */
function watchFollowRequests(page: Page) {
  const seen = { list: 0, item: [] as string[] };
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.pathname !== '/api/follow') return;
    if (url.searchParams.has('item')) seen.item.push(url.searchParams.get('item')!);
    else seen.list += 1;
  });
  return seen;
}

const openDetail = (browser: Browser, id: number, viewport = DESKTOP) =>
  openFollowFeed(browser, `/follow/item/${id}`, viewport, { ready: DETAIL_READY });

describe('关注详情岛', () => {
  let browser: Browser;

  before(async () => {
    browser = await launch();
  });

  after(async () => {
    await browser.close();
  });

  it('列表点卡进详情：地址换成这一条，不再单条取数；关掉回列表不重取', { timeout: 60_000 }, async () => {
    const opened = await openFollowFeed(browser, '/follow', DESKTOP);
    try {
      const page = opened.page;
      const seen = watchFollowRequests(page);
      await page.locator('[data-follow-item="1002"] [data-follow-open]').click();
      await pathIs(page, '/follow/item/1002');
      await page.locator(DETAIL_READY).waitFor();
      assert.equal((await page.locator('#stage [data-follow-detail-name]').innerText()).trim(), '演示更新 1002');
      assert.deepEqual(seen.item, [], '列表缓存里有的这一条又单条取了一次');
      await page.locator('#closeStage').click();
      await pathIs(page, '/follow');
      await page.locator('[data-follow-list] > [data-follow-item]').first().waitFor();
      assert.equal(seen.list, 0, '关掉详情回列表重取了一遍');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('深链进详情只单条取这一条，不挂列表岛；内容到了焦点在关闭键上', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.collection);
    try {
      const page = opened.page;
      assert.equal(await page.locator('[data-follow-feed]').count(), 0, '深链进详情时挂了列表岛');
      assert.equal((await page.locator('#stage [data-follow-detail-name]').innerText()).trim(), '合集主条目 5101');
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'closeStage');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('视频：舞台在媒体框里挂上 Video.js，氛围光画布与统计角标插进同一个媒体框；换一条只剩一个播放器', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.collection);
    try {
      const page = opened.page;
      const frame = page.locator('#stage [data-follow-detail-media="video"]');
      // 控制条在用户一段时间不动后会隐去（Video.js 的 userActive），只等它挂上，不等可见。
      await frame.locator('.video-js .vjs-control-bar').waitFor({ state: 'attached' });
      assert.equal(await frame.locator('[data-ambient-canvas]').count(), 1);
      assert.equal(await frame.locator('.video-js video').count(), 1, '媒体框里的 video 不止一个');
      await page.locator('[data-follow-queue-item="5102"]').click();
      await pathIs(page, '/follow/item/5102');
      await page.locator('#stage [data-follow-queue-item="5102"][aria-current="true"]').waitFor();
      await page.locator('#stage .video-js .vjs-control-bar').waitFor({ state: 'attached' });
      assert.equal(await page.locator('#stage .video-js').count(), 1, '换一条之后旧播放器没拆');
      assert.equal(await page.locator('#stage [data-ambient-canvas]').count(), 1);
      await page.locator('#closeStage').click();
      await pathIs(page, '/follow');
      await page.locator('[data-follow-list] > [data-follow-item]').first().waitFor({ timeout: 15_000 });
      assert.equal(await page.locator('.video-js').count(), 0, '关掉详情后播放器还挂着');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('多图轮播：圆点报当前那张，箭头与圆点换图不换地址', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.gallery);
    try {
      const page = opened.page;
      const current = () => page.locator('#stage [data-follow-image-dots] button').evaluateAll((dots) =>
        dots.map((dot) => dot.getAttribute('aria-current')));
      const poster = page.locator('#stage [data-follow-detail-poster]');
      assert.deepEqual(await current(), ['true', 'false', 'false']);
      assert.equal(await poster.getAttribute('src'), '/follow-stream?id=5001&media=0');
      await page.locator('#stage [data-follow-image-arrow="next"]').click();
      await page.waitForFunction(() => document.querySelector('#stage [data-follow-detail-poster]')
        ?.getAttribute('src') === '/follow-stream?id=5001&media=1');
      assert.deepEqual(await current(), ['false', 'true', 'false']);
      await page.locator('#stage [data-follow-image-arrow="prev"]').click();
      await page.locator('#stage [data-follow-image-dots] button').nth(2).click();
      await page.waitForFunction(() => document.querySelector('#stage [data-follow-detail-poster]')
        ?.getAttribute('src') === '/follow-stream?id=5001&media=2');
      assert.deepEqual(await current(), ['false', 'false', 'true']);
      assert.equal(new URL(page.url()).pathname, '/follow/item/5001');
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('合集队列：只列可播视频、新到旧，当前那条按下；另一站那条的出处是站点图标', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.collection);
    try {
      const page = opened.page;
      const queue = page.locator('#stage [data-follow-queue][data-queue-kind="collection"]');
      const rows = await queue.locator('[data-follow-queue-item]').evaluateAll((buttons) => buttons.map((button) => ({
        id: Number((button as HTMLElement).dataset.followQueueItem), current: button.getAttribute('aria-current'),
        icon: button.querySelector('[data-follow-queue-meta] img')?.getAttribute('alt') ?? null,
      })));
      assert.deepEqual(rows, [
        { id: 5101, current: 'true', icon: null },
        { id: 5102, current: 'false', icon: null },
        { id: 5103, current: 'false', icon: 'Rule34.xxx' },
      ]);
      assert.match(await queue.locator('[data-mix-queue-head]').innerText(), /视频合集[\s\S]*3 个视频/);
      assert.equal(await queue.locator('[data-queue-close]').isVisible(), false, '并排布局的队列头不该有关闭键');
      /* 桌面上媒体在左、详情在右，队列是完整的第二行、横向排开。 */
      const grid = await page.evaluate(() => {
        const box = (selector: string) => document.querySelector(selector)!.getBoundingClientRect();
        const media = box('#stage [data-stage-media]'), side = box('#stage [data-follow-detail-side]');
        const queue = box('#stage [data-follow-queue]'), whole = box('#stage [data-stage-grid]');
        return { sideRight: side.left >= media.right - 1, queueBelow: queue.top >= Math.max(media.bottom, side.bottom) - 1,
          queueFull: Math.abs(queue.width - whole.width) <= 1,
          flow: getComputedStyle(document.querySelector('#stage [data-follow-queue] [data-mix-list]')!).gridAutoFlow };
      });
      assert.deepEqual(grid, { sideRight: true, queueBelow: true, queueFull: true, flow: 'column' });
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('多媒体队列：一帖里的图与视频各占一行，点图换成图片不换地址', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.media);
    try {
      const page = opened.page;
      const queue = page.locator('#stage [data-follow-queue][data-queue-kind="media"]');
      const kinds = await queue.locator('[data-follow-media-item]').evaluateAll((buttons) =>
        buttons.map((button) => [(button as HTMLElement).dataset.mediaKind, button.getAttribute('aria-current')]));
      assert.deepEqual(kinds, [['video', 'true'], ['image', 'false'], ['video', 'false']]);
      await queue.locator('[data-follow-media-item="1"]').click();
      await page.locator('#stage [data-follow-detail-media="image"] [data-follow-detail-poster]').waitFor();
      assert.equal(await queue.locator('[data-follow-media-item="1"]').getAttribute('aria-current'), 'true');
      assert.equal(await page.locator('#stage .video-js').count(), 0, '换成图片后播放器没拆');
      assert.equal(new URL(page.url()).pathname, '/follow/item/5201');
      // 当前是图，操作条里多一枚「隐藏这张图」。
      assert.equal(await page.locator('#stage [data-follow-media-hide="1"]').count(), 1);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('保存与状态：写进桩、键态跟着变；标记已看的回执能撤销，撤销后键态回原样', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.gallery);
    try {
      const page = opened.page;
      const seen = page.locator('#stage [data-follow-detail-status="seen"]');
      assert.equal(await seen.getAttribute('aria-pressed'), 'false');
      await seen.click();
      await page.locator('#stage [data-follow-detail-status="seen"][aria-pressed="true"]').waitFor();
      assert.equal(await page.locator('#stage [data-follow-detail-status="new"]').count(), 1, '已看之后没有「恢复未看」');
      // 回执栈在 body 下，舞台是模态 dialog，外面整页惰性，鼠标点不到撤销键；这里量的是撤销本身。
      await page.locator('#toasts').getByRole('button', { name: '撤销' }).dispatchEvent('click');
      await page.locator('#stage [data-follow-detail-status="seen"][aria-pressed="false"]').waitFor();
      await page.locator('#stage [data-follow-detail-save]').click();
      await page.locator('#stage [data-follow-detail-save][aria-label="已保存"]').waitFor();
      assert.deepEqual(opened.stub.writes, [
        { url: '/api/follow/status', body: { item: 5001, to: 'seen' } },
        { url: '/api/follow/status', body: { item: 5001, to: 'new' } },
        { url: '/api/follow/save', body: { item: 5001 } },
      ]);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('隐藏这张图退到恢复带，从恢复带点回来又回到轮播', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.hidden);
    try {
      const page = opened.page;
      const restores = () => page.locator('#stage [data-follow-media-restore]').evaluateAll((buttons) =>
        buttons.map((button) => Number((button as HTMLElement).dataset.followMediaRestore)));
      const dots = () => page.locator('#stage [data-follow-image-dots] button').count();
      assert.deepEqual(await restores(), [3, 4]);
      assert.equal(await dots(), 3);
      await page.locator('#stage [data-follow-media-hide="0"]').click();
      await page.waitForFunction(() => document.querySelectorAll('#stage [data-follow-media-restore]').length === 3);
      assert.deepEqual(await restores(), [0, 3, 4]);
      assert.equal(await dots(), 2);
      assert.match(await page.locator('#stage [data-follow-hidden-label]').innerText(), /已隐藏 3 张/);
      await page.locator('#stage [data-follow-media-restore="0"]').click();
      await page.waitForFunction(() => document.querySelectorAll('#stage [data-follow-media-restore]').length === 2);
      assert.equal(await page.locator('#stage [data-follow-detail-poster]').getAttribute('src'),
        '/follow-stream?id=5301&media=0', '恢复的那张没有回到舞台上');
      assert.deepEqual(opened.stub.writes, [
        { url: '/api/follow/media/hide', body: { item: 5301, media: 0, hidden: true } },
        { url: '/api/follow/media/hide', body: { item: 5301, media: 0, hidden: false } },
      ]);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('点详情里的标签回到带上这枚标签的列表', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.gallery);
    try {
      const page = opened.page;
      const tag = page.locator('#stage [data-follow-tag]').first();
      const name = (await tag.getAttribute('data-follow-tag'))!;
      await tag.click();
      await page.waitForFunction((wanted) => location.pathname === '/follow'
        && new URLSearchParams(location.search).get('tag') === wanted, name, { timeout: 10_000 });
      await page.locator('[data-follow-list] > [data-follow-item]').first().waitFor({ timeout: 15_000 });
      assert.equal(await page.locator('#stage[open]').count(), 0);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('手机 390：详情不横向溢出，操作条按内容定宽，合集队列排在侧栏下面', { timeout: 60_000 }, async () => {
    const opened = await openDetail(browser, DETAIL.collection, MOBILE);
    try {
      const page = opened.page;
      assert.deepEqual((await layout(page)).offenders, [], '详情里有元素越出视口右边');
      const boxes = await page.evaluate(() => {
        const box = (selector: string) => document.querySelector(selector)!.getBoundingClientRect();
        const actions = box('#stage [data-follow-detail-actions]');
        const buttons = [...document.querySelectorAll('#stage [data-follow-detail-actions] > *')]
          .map((node) => node.getBoundingClientRect());
        return { actions: actions.width, used: buttons.at(-1)!.right - buttons[0]!.left,
          side: box('#stage [data-follow-detail-side]').bottom, queue: box('#stage [data-follow-queue]').top };
      });
      assert.ok(Math.abs(boxes.actions - boxes.used) <= 1, `操作条被撑宽了：${JSON.stringify(boxes)}`);
      assert.ok(boxes.queue >= boxes.side - 1, `合集队列不在侧栏下面：${JSON.stringify(boxes)}`);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });
});
