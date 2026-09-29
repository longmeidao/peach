import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import type { Browser } from 'playwright-core';

import { launch, layout, settle, VIEWPORTS } from './harness.ts';
import { ITEM, openItemPage } from './item-fixture.ts';

describe('FC2 合集与封面取景', () => {
  let browser: Browser;
  before(async () => { browser = await launch(); });
  after(async () => { await browser?.close(); });

  for (const viewport of VIEWPORTS) {
    it(`${viewport.name}: 本篇与特典的标题和队列标签一致`, async () => {
      const opened = await openItemPage(browser, `/parts/${ITEM.part}/22`, viewport);
      try {
        const parts = await opened.page.evaluate(async (id) =>
          (await fetch(`/api/parts?id=${id}`)).json(), ITEM.part);
        const labels = ['本篇', '特典 1', '特典 3'];
        parts.items = parts.items.map((item, index) => ({ ...item, part_label: labels[index] }));
        await opened.page.route('**/api/parts?*', (route) => route.fulfill({ json: parts }));
        await opened.page.reload({ waitUntil: 'load' });
        await opened.page.locator('#stage .partlabel').waitFor();
        assert.equal(await opened.page.locator('#stage .partlabel').innerText(), '特典 1');
        for (const [index, id] of [21, 22, 23].entries()) {
          assert.ok((await opened.page.locator(`#stage [data-queue-item="${id}"]`).innerText()).includes(labels[index]));
        }
        const bounds = await layout(opened.page);
        assert.ok(bounds.scrollWidth <= bounds.viewportWidth + 1, JSON.stringify(bounds));
      } finally { await opened.close(); }
    });

    for (const cx of [.519, .22]) {
    it(`${viewport.name}: 缺集归为一张卡，横图人脸 ${cx} 尽量居中`, async () => {
      const opened = await openItemPage(browser, '/', viewport, {
        ready: '[data-media-card]', settings: { javLayout: 'big', homeLayout: 'big', javImage: 'cover' },
      });
      try {
        const code = 'FC2-PPV-3312576';
        const ids = [8001, 8008, 8010, 8021];
        const base = await opened.page.evaluate(async (id) =>
          (await fetch(`/api/item?id=${id}`)).json(), ITEM.plain);
        const items = ids.map((id) => ({ ...base, id, code, is_jav: true, tags: [],
          name: `${code}-${id - 8000}.mp4`, has_cover: true,
          cover_frame: { cx, cy: .294 }, poster_box: null,
          part_group: { key: code, title: code, count: ids.length, seed_id: ids[0],
            item_ids: ids, total_duration: 9000, total_size: 9000000000 },
        }));
        await opened.page.route('**/api/items?*', (route) => route.fulfill({ json: {
          items, total: items.length, has_more: false,
        } }));
        await opened.page.route('**/cover?*', (route) => route.fulfill({
          contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="1548" height="948"><rect width="1548" height="948" fill="#ddd"/></svg>',
        }));
        await opened.page.reload({ waitUntil: 'load' });
        const covers = opened.page.locator('[data-media-card] img.cover');
        await covers.first().waitFor();
        await opened.page.waitForFunction(() =>
          document.querySelector<HTMLImageElement>('[data-media-card] img.cover')?.naturalWidth === 1548);
        await settle(opened.page);
        assert.equal(await covers.count(), 1);
        const frame = await covers.first().evaluate((img: HTMLImageElement, faceCenter: number) => {
          const style = getComputedStyle(img);
          const rect = img.getBoundingClientRect();
          const scale = Math.max(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
          const x = parseFloat(style.objectPosition) / 100;
          const sourceFaceX = faceCenter * img.naturalWidth * scale;
          const croppedWidth = img.naturalWidth * scale - rect.width;
          const faceX = sourceFaceX - croppedWidth * x;
          // 无空白的可达范围为 [sourceFaceX - croppedWidth, sourceFaceX]。
          const closestCenter = Math.min(sourceFaceX, Math.max(sourceFaceX - croppedWidth, rect.width / 2));
          return { kind: img.dataset.frame, faceX, closestCenter, croppedWidth, x };
        }, cx);
        assert.equal(frame.kind, 'still');
        assert.ok(frame.croppedWidth > 0, JSON.stringify(frame));
        assert.ok(frame.x >= 0 && frame.x <= 1, JSON.stringify(frame));
        assert.ok(Math.abs(frame.faceX - frame.closestCenter) < 5, JSON.stringify(frame));
        const bounds = await layout(opened.page);
        assert.ok(bounds.scrollWidth <= bounds.viewportWidth + 1, JSON.stringify(bounds));
        assert.deepEqual(opened.problems, []);
      } finally { await opened.close(); }
    });
    }
  }
});
