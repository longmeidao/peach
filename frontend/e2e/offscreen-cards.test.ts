/* 视口外的卡片跳过渲染：封面和元信息区交给浏览器按视口取舍，卡片盒照常排版。
 *
 * 这几条守的是跳过渲染的副作用：屏外卡确实被跳过、没渲染过的卡按估计高度排进来之后
 * 整页高度和卡片位置不跳、Ctrl+F 仍找得到屏外卡里的字。演示库只有十来条，一屏就放完，
 * 这里把目录响应放大成一长列，编号改成互不相同，封面请求再改写回原来那条。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { launch, settle, visit, VIEWPORTS, type Visit } from './harness.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const CLONES = 150;
const CLONE_BASE = 900_000;
const PROBE_TAG = '屏外探针';

interface CatalogPayload {
  total: number;
  items: Array<Record<string, unknown>>;
}

/** 目录首屏换成 `CLONES` 张卡：每三张有一张带标签，最后一张带一枚独有的标签给查找用。 */
async function openLongCatalog(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/', DESKTOP);
  const { page } = opened;
  const original = new Map<number, number>();
  let baseline: CatalogPayload | undefined;
  await page.route(/\/api\/items\?/, async (route) => {
    const url = new URL(route.request().url());
    if (url.searchParams.get('offset') !== '0') {
      await route.continue();
      return;
    }
    baseline ??= await (await route.fetch()).json() as CatalogPayload;
    const source = baseline.items.filter((item) => !item.part_group && !item.edition_group);
    const items = Array.from({ length: CLONES }, (_, index) => {
      const item = structuredClone(source[index % source.length]);
      original.set(CLONE_BASE + index, Number(item.id));
      item.id = CLONE_BASE + index;
      item.tags = index === CLONES - 1 ? [PROBE_TAG] : index % 3 === 0 ? ['演示'] : [];
      return item;
    });
    await route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ ...baseline, total: CLONES, items }) });
  });
  await page.route((url) => original.has(Number(url.searchParams.get('id'))), async (route) => {
    const url = new URL(route.request().url());
    url.searchParams.set('id', String(original.get(Number(url.searchParams.get('id')))));
    await route.continue({ url: url.toString() });
  });
  await page.reload({ waitUntil: 'load' });
  await page.waitForFunction((count) => document.querySelectorAll('#grid .card').length >= count, CLONES,
    { timeout: 15_000 });
  await settle(page);
  return opened;
}

/** 关注页换成 `CLONES` 条合成的更新：演示库没有关注来源。字段照 `/api/follow` 的形状，
 * 不带缩略图，不发外站请求；每三条有一条带标签，屏外卡因此有高矮两种元信息区。 */
async function openLongFollow(browser: Browser): Promise<Visit> {
  const opened = await visit(browser, '/', DESKTOP);
  const { page } = opened;
  const source = { id: 1, provider: 'rule34xxx', provider_label: 'Rule34.xxx', ref: 'demo', label: '演示来源',
    author_name: '演示作者', author_key: 'name:演示作者', official_avatar_url: null, avatar_url: null,
    url: 'https://example.invalid/', semantics: 'work', enabled: true, entity_id: null, entity_name: null,
    can_backfill: false, backfill_page: 0, created_at: '2026-09-01T00:00:00Z', last_checked_at: null,
    last_status: 'ok', last_error: null, history_exhausted: true };
  const groups = Array.from({ length: CLONES }, (_, index) => ({
    release_key: `demo-${index}`, variants: [], duplicates: [], providers: ['rule34xxx'], has_wip: false,
    is_release: false, newest_at: '2026-09-01T00:00:00Z',
    primary: {
      id: CLONE_BASE + index, provider: 'rule34xxx', provider_label: 'Rule34.xxx', resource_provider: 'rule34xxx',
      source_id: 1, source_label: '演示来源', external_id: String(index), title: `演示更新 ${index}`,
      author: '演示作者', summary: null, url: `https://example.invalid/${index}`, thumb_url: null,
      published_at: '2026-09-01T00:00:00Z', published_precision: 'exact', version: null, duration: 60,
      variant_kind: 'main', variant_label: null, status: 'new', asset_id: null, media_needs_credential: false,
      media_error: null, has_media: false, media_kind: 'video', width: 1280, height: 720, media_type: null,
      playable: false, media_items: [], hidden_media: [], resource_urls: [],
      tags: index % 3 === 0 ? ['演示'] : [], detail_tags: [], tag_types: {},
    },
  }));
  const body = { ok: true, sources: [source], author_aliases: [], alias_suggestions: [], suggestions: [], groups,
    counts: { new: CLONES, seen: 0, saved: 0, ignored: 0 }, sort: 'new', dir: 'desc', seed: 1,
    facets: { authors: [], providers: [], tags: [], works: [] }, offset: 0, limit: CLONES, has_more: false,
    providers: ['rule34xxx'] };
  await page.route(/\/api\/follow(\?|$)/, (route) => route.fulfill({ status: 200, contentType: 'application/json',
    body: JSON.stringify(body) }));
  await page.goto(new URL('/follow', page.url()).toString(), { waitUntil: 'load' });
  await page.waitForFunction((count) => document.querySelectorAll('.followlist>.card').length >= count, CLONES,
    { timeout: 15_000 });
  await settle(page);
  return opened;
}

/** 一屏一屏滚到底再滚回顶，每步等两帧，让每张卡都至少渲染过一次。 */
function roundTrip(page: Page): Promise<void> {
  return page.evaluate(async () => {
    const frame = () => new Promise(requestAnimationFrame);
    for (const direction of [1, -1]) {
      for (let step = 0; step < 500; step++) {
        const y = scrollY;
        scrollBy(0, direction * innerHeight * .9);
        await frame();
        await frame();
        if (scrollY === y) break;
      }
    }
  });
}

describe('视口外的卡片', () => {
  let browser: Browser;

  before(async () => {
    browser = await launch();
  });

  after(async () => {
    await browser.close();
  });

  it('跳过封面与元信息区的渲染，Ctrl+F 仍找得到屏外卡里的字', { timeout: 60_000 }, async () => {
    const opened = await openLongCatalog(browser);
    try {
      const state = await opened.page.evaluate((tag) => {
        const last = [...document.querySelectorAll<HTMLElement>('#grid .card')].at(-1)!;
        const parts = [last.querySelector('.pic')!, last.querySelector('.meta')!];
        // 跳过的是元素的内容，元素自己仍在排版里：查它的第一个子元素。
        const skipped = parts.map((part) => !part.firstElementChild!.checkVisibility({ contentVisibilityAuto: true }));
        const box = last.getBoundingClientRect();
        /* 侧栏的标签列表里也有这枚标签，排在文档前面；往下接着找，直到落进那张卡。 */
        const find = (window as unknown as { find(text: string): boolean }).find.bind(window);
        let hits = 0;
        while (hits < 5 && find(tag)) {
          hits++;
          const node = getSelection()?.anchorNode;
          if (node && last.contains(node)) break;
        }
        const hit = getSelection()?.anchorNode;
        return {
          values: parts.map((part) => getComputedStyle(part).contentVisibility),
          skipped, below: box.top - innerHeight, height: box.height,
          hits, inLast: !!hit && last.contains(hit),
        };
      }, PROBE_TAG);
      assert.deepEqual(state.values, ['auto', 'auto'], '屏外卡的封面和元信息区没有交给浏览器按视口取舍');
      assert.ok(state.below > 1000, `最后一张卡离视口只有 ${state.below}px，放大的列表不够长`);
      assert.deepEqual(state.skipped, [true, true], '屏外卡的封面或元信息区仍在渲染');
      assert.ok(state.height > 0, '屏外卡的 getBoundingClientRect 量出了零高');
      assert.ok(state.inLast, `页内查找没有落到屏外那张卡的标签上（命中 ${state.hits} 次）`);
      assert.deepEqual(opened.problems, []);
    } finally {
      await opened.close();
    }
  });

  for (const [where, open, selector] of [
    ['馆藏', openLongCatalog, '#grid .card'],
    ['关注', openLongFollow, '.followlist>.card'],
  ] as const) {
    it(`${where}：长距离往返之后整页高度和深处那张卡的位置不跳，屏外量到的几何与渲染后一致`, { timeout: 90_000 }, async () => {
      const opened = await open(browser);
      try {
        const { page } = opened;
        const measure = () => page.evaluate((cardSelector) => {
          const cards = [...document.querySelectorAll(cardSelector)];
          const deep = cards[Math.floor(cards.length * .8)];
          return { height: document.documentElement.scrollHeight,
            deep: deep.getBoundingClientRect().top + scrollY, y: scrollY,
            view: deep.getBoundingClientRect().top,
            skipping: getComputedStyle(deep.querySelector('.meta')!).contentVisibility,
            meta: deep.querySelector('.meta')!.getBoundingClientRect().height };
        }, selector);
        /* 首屏之外的卡此刻都没渲染过，高度全按估计值；往返一趟之后每张都记住了自己的实际
           尺寸。两次量到的差就是估计值的误差，一行差一点，累积到深处就是滚动条在跳。 */
        const fresh = await measure();
        assert.equal(fresh.skipping, 'auto', `${where}的屏外卡不跳过渲染，量不到估计值的误差`);
        await roundTrip(page);
        const rendered = await measure();
        assert.ok(Math.abs(rendered.height - fresh.height) <= 1,
          `整页高度从 ${fresh.height} 变成 ${rendered.height}：元信息区的估计高度与实际不符`);
        assert.ok(Math.abs(rendered.deep - fresh.deep) <= 1,
          `深处那张卡从 ${fresh.deep} 挪到 ${rendered.deep}`);

        /* 停在深处，滚到底再回来：同一个 scrollY 下那张卡应该还在原处。 */
        await page.evaluate((y) => scrollTo(0, y), rendered.deep - 300);
        await page.waitForTimeout(300);
        const parked = await measure();
        /* 跳过渲染时量到的几何要和渲染后一致：卡里有别的子元素抢空间时，内容不参与最小尺寸的
           元信息区会被压扁，整张卡的高度不变，从外面看不出来，只有量它自己才露馅。 */
        assert.ok(Math.abs(fresh.meta - parked.meta) <= 1,
          `屏外卡的元信息区量出 ${fresh.meta}px，渲染后是 ${parked.meta}px`);
        await roundTrip(page);
        await page.evaluate((y) => scrollTo(0, y), parked.y);
        await page.waitForTimeout(300);
        const back = await measure();
        assert.equal(back.y, parked.y, '回不到原来的滚动位置');
        assert.ok(Math.abs(back.view - parked.view) <= 1,
          `回到同一滚动位置后那张卡在视口里从 ${parked.view} 挪到 ${back.view}`);
        assert.deepEqual(opened.problems, []);
      } finally {
        await opened.close();
      }
    });
  }
});
