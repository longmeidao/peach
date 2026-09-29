import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import type { Browser, Locator } from 'playwright-core';
import { launch, layout, settle, visit, VIEWPORTS } from './harness.ts';

const box = (target: Locator) => target.evaluate(node => {
  const { x, y, width, height } = node.getBoundingClientRect();
  return { x, y, width, height };
});
type Box = Awaited<ReturnType<typeof box>>;
const aligned = (waiting: Box, ready: Box, keys: readonly (keyof Box)[] = ['x', 'y', 'width', 'height']) => {
  for (const key of keys) assert.ok(Math.abs(waiting[key] - ready[key]) <= 1, `${key}: ${waiting[key]} / ${ready[key]}`);
};

describe('管理页面容器与骨架', () => {
  let browser: Browser;
  before(async () => { browser = await launch(); });
  after(async () => { await browser?.close(); });
  for (const viewport of VIEWPORTS) {
    it(`扫描和链接操作位于分隔底栏（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/data-cleanup', viewport);
      try {
        await settle(opened.page);
        for (const name of ['扫描与采集', '站外链接']) {
          const card = opened.page.locator('section').filter({ has: opened.page.getByRole('heading', { name, exact: true }) }).last();
          const geometry = await card.evaluate(node => {
            const children = Array.from(node.children);
            const body = children[0]!.getBoundingClientRect();
            const footer = children.at(-1)!;
            const rect = footer.getBoundingClientRect();
            return { bodyBottom: body.bottom, footerTop: rect.top, width: rect.width,
              bodyWidth: body.width, border: getComputedStyle(footer).borderTopWidth };
          });
          assert.ok(Math.abs(geometry.bodyBottom - geometry.footerTop) <= 1);
          assert.equal(geometry.width, geometry.bodyWidth);
          assert.equal(geometry.border, '1px');
        }
      } finally { await opened.close(); }
    });
    it(`统计读数和库存图在接管时对齐（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/stats', viewport);
      let release = () => {};
      try {
        const page = opened.page;
        await page.getByRole('tablist', { name: '统计视图' }).waitFor();
        const pending = new Promise<void>(resolve => { release = resolve; });
        await page.route('**/api/stats*', async route => {
          const response = await route.fetch();
          await pending;
          await route.fulfill({ response });
        });
        await page.reload({ waitUntil: 'load' });
        const skeleton = page.locator('[data-skeleton="board/stats"]');
        await skeleton.waitFor();
        const metrics = await box(skeleton.locator('[data-stats-metrics]'));
        const chart = await box(skeleton.locator('[data-stats-chart]').first());
        const waitingLayout = await layout(page);
        release();
        await page.getByRole('tablist', { name: '统计视图' }).waitFor();
        await settle(page);
        aligned(metrics, await box(page.getByRole('tablist', { name: '统计视图' })));
        aligned(chart, await box(page.getByRole('img', { name: '网盘与本地', exact: true }).locator('..')), ['x', 'y', 'width']);
        assert.ok(waitingLayout.scrollWidth <= waitingLayout.viewportWidth);
        assert.deepEqual(opened.problems, []);
      } finally { release(); await opened.close(); }
    });
    it(`重复文件汇总与文件行使用正文尺寸（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/duplicates', viewport);
      let release = () => {};
      try {
        const page = opened.page;
        const pending = new Promise<void>(resolve => { release = resolve; });
        await page.route('**/api/duplicates?**', async route => {
          await pending;
          await route.fulfill({ json: { total: 1, files: 2, reclaimable: 1000, groups: [{
            code: 'DEMO-001', count: 2, identical: true, drives: ['R:'], cross_drive: false, reclaimable: 1000,
            files: [1, 2].map(id => ({ id, name: `DEMO-${id}.mp4`, path: `R:\\Media\\DEMO-${id}.mp4`,
              location: 'local', drive: 'R:', size: 1000, duration: 3600, is_largest: id === 1, is_longest: id === 2 })),
          }] } });
        });
        await page.reload({ waitUntil: 'load' });
        const skeleton = page.locator('[data-skeleton="board/duplicates"]');
        await skeleton.waitFor();
        const summary = await box(skeleton.locator('[data-collection-summary]'));
        const row = await box(skeleton.locator('.duplicate-row').first());
        release();
        const body = page.locator('#stats section[aria-label="DEMO-001"]');
        await body.waitFor();
        await settle(page);
        aligned(summary, await box(page.locator('#stats [data-collection-summary]')));
        aligned(row, await box(body.locator('.duplicate-row').first()));
        const dimensions = await layout(page);
        assert.ok(dimensions.scrollWidth <= dimensions.viewportWidth);
      } finally { release(); await opened.close(); }
    });
    it(`回收站网格与标题、汇总栏同宽（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/trash', viewport);
      try {
        await opened.page.locator('#manageLede').waitFor();
        await settle(opened.page);
        const title = await box(opened.page.locator('#manageTitle'));
        const grid = await box(opened.page.locator('#grid'));
        const lede = await box(opened.page.locator('#manageLede'));
        aligned(title, grid, ['x', 'width']);
        aligned(title, lede, ['x', 'width']);
        assert.deepEqual(opened.problems, []);
      } finally { await opened.close(); }
    });
  }
});
