/* 作品详情岛（`item-detail`）在真浏览器里的行为：从目录卡进出、深链、Video.js 挂在岛画的 `<video>` 上、
 * 脱盘说明、共演收起、标题折叠、评分与标签的撤销、反馈键态、四种队列、播放列表排序与移出、保存 Mix、接着看、
 * 实体页入口与手机布局。
 *
 * 桩数据见 `item-fixture.ts`；读写接口全部由桩接住，演示库账本一次都不写。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { layout, launch, VIEWPORTS } from './harness.ts';
import { ITEM, NAMES, PLAYLIST, RELATED, openItemPage } from './item-fixture.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const MOBILE = VIEWPORTS.find((viewport) => viewport.mobile)!;
const DETAIL_READY = '#stage[open] [data-item-side]';
/** 桩里的片源没有正片，播放器拿到空响应会报一条 VIDEOJS 错误；量的不是它。 */
const withoutPlayer = (problems: string[]) => problems.filter((line) => !line.includes('VIDEOJS'));
const pathIs = (page: Page, path: string) => page.waitForFunction(
  (wanted) => location.pathname === wanted, path, { timeout: 10_000 });
/** 回执栈在 body 下，舞台是模态 dialog，外面整页惰性，鼠标点不到撤销键；这里量的是撤销本身。 */
const undo = (page: Page) => page.locator('#toasts').getByRole('button', { name: '撤销' }).last().dispatchEvent('click');
const current = (page: Page) => page.locator('#stage [data-queue-item][aria-current="true"]').getAttribute('data-queue-item');
const ids = (page: Page, selector: string, attribute: string) => page.locator(selector).evaluateAll(
  (nodes, name) => nodes.map((node) => Number(node.getAttribute(name))), attribute);

describe('作品详情岛', () => {
  let browser: Browser;

  before(async () => {
    browser = await launch();
  });

  after(async () => {
    await browser.close();
  });

  it('目录点卡进详情：地址换成这一条；关掉回列表不重取', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, '/', DESKTOP, { ready: `#grid [data-media-card][data-id="${ITEM.plain}"]` });
    try {
      const page = opened.page;
      const listed = opened.stub.reads.get('/api/items') || 0;
      await page.locator(`#grid [data-media-card][data-id="${ITEM.plain}"] [data-media-title]`).first().click();
      await pathIs(page, `/item/${ITEM.plain}`);
      await page.locator(DETAIL_READY).waitFor();
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'closeStage', '内容到了焦点不在关闭键上');
      await page.locator('#closeStage').click();
      await pathIs(page, '/');
      await page.locator('#stage[open]').waitFor({ state: 'detached', timeout: 10_000 }).catch(() => {});
      assert.equal(await page.locator('#stage[open]').count(), 0);
      await page.locator(`#grid [data-media-card][data-id="${ITEM.plain}"]`).first().waitFor();
      assert.equal(opened.stub.reads.get('/api/items') || 0, listed, '关掉详情回列表重取了一遍');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('深链进详情：单条取这一条；关掉之后照地址补画列表', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      assert.equal(opened.stub.reads.get('/api/item'), 1);
      await page.locator('#closeStage').click();
      await pathIs(page, '/');
      await page.locator(`#grid [data-media-card][data-id="${ITEM.plain}"]`).first().waitFor({ timeout: 15_000 });
      assert.ok((opened.stub.reads.get('/api/items') || 0) >= 1, '深链关掉之后没有补取列表');
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('岛画的 `<video>` 交给壳挂上 Video.js，氛围光画布与统计角标跟它进同一块媒体区', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      await page.locator('#stage [data-item-media="video"] > .video-js video.vjs-tech').waitFor({ state: 'attached' });
      const shape = await page.evaluate(() => {
        const media = document.querySelector('#stage [data-item-media="video"]')!;
        return { id: media.querySelector(':scope > .video-js')!.id, canvas: !!media.querySelector(':scope > .ambientcanvas'),
          stats: !!media.querySelector('#playerStatsBtn'), videos: media.querySelectorAll('video').length };
      });
      assert.deepEqual(shape, { id: 'vid', canvas: true, stats: true, videos: 1 });
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('来源没挂载：说明块代替播放器，重新检测仍未挂载就换成再试', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.offline}`, DESKTOP);
    try {
      const page = opened.page;
      const gate = page.locator('#stage [data-item-gate="offline"]');
      assert.match(await gate.innerText(), /脱盘模式/);
      assert.equal(await page.locator('#stage .vjs-tech').count(), 0, '脱盘的条目挂了播放器');
      await page.locator('#offlineRetry').click();
      await page.locator('#offlineRetry', { hasText: '仍未挂载 · 再试' }).waitFor();
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  it('出演超过 8 位先收起，点「还有 N 位」全部展开', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.cast}`, DESKTOP);
    try {
      const page = opened.page;
      const shown = () => page.locator('#stage [data-item-identity] [data-entity-kind="performer"]:visible').count();
      assert.equal(await shown(), 8);
      assert.equal((await page.locator('#castMore').innerText()).trim(), `还有 ${NAMES.length - 8} 位`);
      await page.locator('#castMore').click();
      assert.equal(await shown(), NAMES.length);
      assert.equal(await page.locator('#castMore').count(), 0);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('标题折成两行，真溢出才给展开键；展开键与标题文字都能展开，再点收回', { timeout: 60_000 }, async () => {
    const short = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      assert.equal(await short.page.locator('#stage [data-title-fold]').isHidden(), true);
    } finally {
      await short.close();
    }
    const opened = await openItemPage(browser, `/item/${ITEM.long}`, DESKTOP);
    try {
      const page = opened.page;
      const title = page.locator('#stage [data-detail-title]');
      const fold = page.locator('#stage [data-title-fold]');
      const lines = () => title.evaluate((node) => Math.round(node.clientHeight / parseFloat(getComputedStyle(node).lineHeight)));
      assert.equal(await fold.isVisible(), true);
      assert.equal(await lines(), 2);
      await fold.click();
      assert.equal(await fold.getAttribute('aria-label'), '收起标题');
      assert.ok(await lines() > 2, '展开之后整段标题都在');
      await title.click();
      assert.equal(await fold.getAttribute('aria-label'), '展开标题');
      assert.equal(await lines(), 2);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('评分：点当前那一颗是撤销评分；回执的撤销写回原分', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      const value = page.locator('#detailRating [data-rating-value]');
      assert.equal((await value.innerText()).trim(), '3 星');
      await page.locator('#detailRating [data-rate="3"]').click();
      await page.locator('#detailRating [data-rating-value]', { hasText: '未评分' }).waitFor();
      assert.equal(await page.locator('#detailRating [data-on="true"]').count(), 0);
      await undo(page);
      await page.locator('#detailRating [data-rating-value]', { hasText: '3 星' }).waitFor();
      assert.deepEqual(opened.stub.writes.filter((write) => write.url === '/api/feedback').map((write) => write.body), [
        { id: ITEM.plain, kind: 'rate', value: 0 },
        { id: ITEM.plain, kind: 'rate', value: 60 },
      ]);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('标签：删一枚再撤销回来；从选择器新建一枚', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      const tag = (name: string) => page.locator(`#detailTags [data-tag="${name}"]`);
      await page.locator('#detailTags [data-remove-tag="剧情"]').click();
      await tag('剧情').waitFor({ state: 'detached' });
      await undo(page);
      await tag('剧情').waitFor();
      await page.locator('#tagPlus').click();
      await page.locator('#tagPicker:not([hidden])').waitFor();
      await page.locator('#tagPickSearch').fill('新建的标签');
      await page.locator('#tagPicker [data-pick="新建的标签"]', { hasText: '新建“新建的标签”' }).waitFor();
      await page.locator('#tagPickSearch').press('Enter');
      await tag('新建的标签').waitFor();
      assert.equal(await page.locator('#tagPicker').isHidden(), true, '加完标签选择器没有收起');
      assert.deepEqual(opened.stub.writes.filter((write) => write.url === '/api/item-tag').map((write) => write.body), [
        { id: ITEM.plain, operation: 'remove', tag: '剧情' },
        { id: ITEM.plain, operation: 'add', tag: '剧情' },
        { id: ITEM.plain, operation: 'add', tag: '新建的标签' },
      ]);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('稍后看与反馈键：写完键态跟着服务端的回话变', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      await page.locator('#stageLater').click();
      await page.locator('#stageLater[aria-pressed="true"]').waitFor();
      await page.locator('#stage [data-kind="dislike"]').click();
      await page.locator('#stage [data-kind="dislike"][aria-pressed="true"]').waitFor();
      await page.locator('#stage [data-kind="seen"]').click();
      await page.locator('#stage [data-kind="seen"][aria-pressed="true"]').waitFor();
      assert.equal(await page.locator('#stage [data-kind="dislike"]').getAttribute('aria-pressed'), 'false', '看过与不合口味同时亮着');
      assert.deepEqual(opened.stub.writes.map((write) => [write.url, write.body.kind ?? null]), [
        ['/api/watch-later', null], ['/api/feedback', 'dislike'], ['/api/feedback', 'seen'],
      ]);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  for (const [kind, path, next, wanted] of [
    ['Mix', `/mix/${ITEM.plain}/${ITEM.plain}`, 14, `/mix/${ITEM.plain}/14`],
    ['分卷', `/parts/${ITEM.part}/22`, 23, `/parts/${ITEM.part}/23`],
    ['版本', `/editions/${ITEM.edition}/${ITEM.edition}`, 32, `/editions/${ITEM.edition}/32`],
    ['播放列表', `/playlists/${PLAYLIST.id}/11`, 15, `/playlists/${PLAYLIST.id}/15`],
  ] as const) {
    it(`${kind}队列：深链停在给的那一条，点另一条换过去且不重取队列`, { timeout: 60_000 }, async () => {
      const opened = await openItemPage(browser, path, DESKTOP);
      try {
        const page = opened.page;
        assert.equal(await current(page), path.split('/').at(-1));
        const reads = new Map(opened.stub.reads);
        await page.locator(`#stage [data-queue-item="${next}"]`).click();
        await pathIs(page, wanted);
        await page.locator(`#stage [data-queue-item="${next}"][aria-current="true"]`).waitFor();
        await page.locator(DETAIL_READY).waitFor();
        if (kind === '分卷') assert.match(await page.locator('#stage [data-detail-title]').innerText(), /第 3 卷/);
        for (const url of ['/api/parts', '/api/editions', '/api/related']) {
          assert.equal(opened.stub.reads.get(url) || 0, reads.get(url) || 0, `同一个${kind}队列里换一条又取了 ${url}`);
        }
        if (kind === '播放列表') {
          assert.deepEqual(opened.stub.writes.filter((write) => write.body.action === 'progress').map((write) => write.body.asset_id),
            [11, next], '播放列表没有记下续播位置');
        }
        assert.deepEqual(withoutPlayer(opened.problems), []);
      } finally {
        await opened.close();
      }
    });
  }

  it('播放列表：拖动换顺序、移出一条，两者都能撤销', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/playlists/${PLAYLIST.id}/11`, DESKTOP);
    try {
      const page = opened.page;
      const order = () => ids(page, '#stage [data-queue-row]', 'data-queue-row');
      const wait = (wanted: number[]) => page.waitForFunction((want) => JSON.stringify([...document
        .querySelectorAll('#stage [data-queue-row]')].map((row) => Number(row.getAttribute('data-queue-row')))) === want,
      JSON.stringify(wanted), { timeout: 10_000 });
      assert.deepEqual(await order(), PLAYLIST.items);
      await page.locator('#stage [data-queue-row="16"]').dragTo(page.locator('#stage [data-queue-row="14"]'),
        { targetPosition: { x: 4, y: 2 } });
      await wait([11, 16, 14, 15]);
      await undo(page);
      await wait(PLAYLIST.items);
      await page.locator('#stage [data-queue-remove="15"]').click();
      await page.locator('[data-modal-confirm]').click();
      await wait([11, 14, 16]);
      await undo(page);
      await wait(PLAYLIST.items);
      assert.deepEqual(opened.stub.writes.filter((write) => write.body.action !== 'progress')
        .map((write) => [write.body.action, write.body.asset_ids ?? write.body.asset_id]), [
        ['reorder', [11, 16, 14, 15]], ['reorder', PLAYLIST.items],
        ['remove', 15], ['add', [15]], ['reorder', PLAYLIST.items],
      ]);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('保存 Mix：确认之后转去新建的那份播放列表', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/mix/${ITEM.plain}/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      await page.locator('#stage [data-save-mix]').click();
      await page.locator('[name="name"]').fill('我的 Mix');
      await page.locator('[data-modal-confirm]').click();
      await page.waitForFunction(() => location.pathname.startsWith(`/playlists/${8}/`), undefined, { timeout: 10_000 });
      await page.locator('#stage [data-queue-row]').first().waitFor();
      assert.deepEqual(await ids(page, '#stage [data-queue-row]', 'data-queue-row'), [ITEM.plain, ...RELATED]);
      const created = opened.stub.writes.find((write) => write.body.action === 'create')!;
      assert.deepEqual(created.body, {
        action: 'create', name: '我的 Mix', asset_ids: [ITEM.plain, ...RELATED], source_kind: 'mix',
        source_seed_asset_id: ITEM.plain,
      });
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('接着看：一排卡按相关作品的顺序；点一张换到那一条', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      await page.locator('#nrow [data-media-card]').first().waitFor();
      assert.deepEqual(await ids(page, '#nrow [data-media-card]', 'data-id'), RELATED);
      await page.locator(`#nrow [data-media-card][data-id="${RELATED[0]}"] [data-media-title]`).click();
      await pathIs(page, `/item/${RELATED[0]}`);
      await page.locator(DETAIL_READY).waitFor();
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });

  it('点女优进她的实体页，舞台收起', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, DESKTOP);
    try {
      const page = opened.page;
      await page.locator(`#stage [data-item-identity] [data-entity-kind="performer"][data-entity-name="${NAMES[0]}"]`).click();
      await pathIs(page, `/performers/${encodeURIComponent(NAMES[0]!)}`);
      await page.waitForFunction(() => !document.querySelector('#stage[open]'), undefined, { timeout: 10_000 });
      assert.equal(await page.evaluate(() => document.body.classList.contains('entity-open')), true);
    } finally {
      await opened.close();
    }
  });

  it('手机 390：详情不横向溢出，侧栏排在播放区下面', { timeout: 60_000 }, async () => {
    const opened = await openItemPage(browser, `/item/${ITEM.plain}`, MOBILE);
    try {
      const page = opened.page;
      assert.deepEqual((await layout(page)).offenders, [], '详情里有元素越出视口右边');
      const boxes = await page.evaluate(() => ({
        media: document.querySelector('#stage [data-item-media]')!.getBoundingClientRect().bottom,
        side: document.querySelector('#stage [data-item-side]')!.getBoundingClientRect().top,
      }));
      assert.ok(boxes.side >= boxes.media - 1, `侧栏不在播放区下面：${JSON.stringify(boxes)}`);
      assert.deepEqual(withoutPlayer(opened.problems), []);
    } finally {
      await opened.close();
    }
  });
});
