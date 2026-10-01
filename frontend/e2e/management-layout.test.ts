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
        await page.emulateMedia({ reducedMotion: 'no-preference' });
        const cpu = await page.context().newCDPSession(page);
        await cpu.send('Emulation.setCPUThrottlingRate', { rate: 4 });
        const pending = new Promise<void>(resolve => { release = resolve; });
        await page.route('**/api/stats*', async route => {
          const response = await route.fetch();
          await pending;
          await route.fulfill({ response });
        });
        await page.addInitScript(() => {
          const frames: { inventory: boolean; ranking: boolean; metricsY: number; dimensionsY: number }[] = [];
          (window as unknown as { statsPaintFrames: typeof frames }).statsPaintFrames = frames;
          const sample = () => {
            const metrics = document.querySelector('[role="tablist"][aria-label="统计视图"]');
            const dimensions = document.querySelector('[role="tablist"][aria-label="统计维度"]');
            if (metrics && dimensions) frames.push({
              inventory: !!document.querySelector('[role="img"][aria-label="网盘与本地"]'),
              ranking: !!document.querySelector('[role="tabpanel"][id$="tags"]'),
              metricsY: metrics.getBoundingClientRect().y,
              dimensionsY: dimensions.getBoundingClientRect().y,
            });
            if (frames.length < 12) requestAnimationFrame(sample);
          };
          requestAnimationFrame(sample);
        });
        await page.reload({ waitUntil: 'load' });
        const skeleton = page.locator('[data-skeleton="board/stats"]');
        await skeleton.waitFor();
        /* 冷启动时侧栏展开那段过渡（`body` 的 padding-left 与侧栏宽度）还在走，整页正文跟着它横移。
           先等它落定再量：这里比的是骨架与接管后的落位，不是量的那一刻侧栏走到了哪儿。 */
        await page.evaluate(() => Promise.all(document.getAnimations()
          .filter((motion) => motion instanceof CSSTransition && ['padding-left', 'width'].includes(motion.transitionProperty)
            && (motion.effect as KeyframeEffect | null)?.target?.matches('body, #drawer'))
          .map((motion) => motion.finished.catch(() => undefined))));
        const metrics = await box(skeleton.locator('[data-stats-metrics]'));
        const chart = await box(skeleton.locator('[data-stats-chart]').first());
        const waitingLayout = await layout(page);
        release();
        await page.getByRole('tablist', { name: '统计视图' }).waitFor();
        await settle(page);
        aligned(metrics, await box(page.getByRole('tablist', { name: '统计视图' })));
        aligned(chart, await box(page.getByRole('img', { name: '网盘与本地', exact: true }).locator('..')), ['x', 'y', 'width']);
        await page.waitForFunction(() => (window as unknown as { statsPaintFrames: unknown[] }).statsPaintFrames.length >= 12);
        const frames = await page.evaluate(() => (window as unknown as {
          statsPaintFrames: { inventory: boolean; ranking: boolean; metricsY: number; dimensionsY: number }[];
        }).statsPaintFrames);
        assert.ok(frames.every(frame => frame.inventory && frame.ranking), '统计首个可见帧缺少选中页签内容');
        for (const frame of frames) {
          assert.ok(Math.abs(frame.metricsY - frames[0]!.metricsY) <= 1, '读数卡加载完成后发生位移');
          assert.ok(Math.abs(frame.dimensionsY - frames[0]!.dimensionsY) <= 1, '统计维度加载完成后发生位移');
        }
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
    it(`高清版骨架与落地同一副几何，摘要在两种主题下都和页面底色分得开（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/quality-goals', viewport);
      let release = () => {};
      try {
        const page = opened.page;
        const pending = new Promise<void>(resolve => { release = resolve; });
        await page.route('**/api/quality-goals**', async route => {
          await pending;
          await route.fulfill({ json: { total: 3, offset: 0, has_more: false, items: [1, 2, 3].map(id => ({
            id, name: `DEMO-${id}.mp4`, code: `DEMO-${id}`, location: 'local', size: 1e9, duration: 3600,
            reason: '', cost: '', has_thumb: false, has_cover: false })) } });
        });
        await page.reload({ waitUntil: 'load' });
        const skeleton = page.locator('[data-skeleton="board/quality-goals"]');
        await skeleton.waitFor();
        const summary = await box(skeleton.locator('[data-collection-summary]'));
        const card = await box(skeleton.locator('.card-grid-cover > li').first());
        release();
        const first = page.locator('#stats li[data-goal-id]').first();
        await first.waitFor();
        await settle(page);
        aligned(summary, await box(page.locator('#stats [data-collection-summary]')));
        aligned(card, await box(first));
        // 浅色下 primary 就是页面底色：摘要取 primary 的话整块化进页面，看不出那是一块面。
        const faces = await page.evaluate(() => {
          const root = document.documentElement;
          const before = { theme: root.dataset.theme, dark: root.classList.contains('dark') };
          const read = (theme: string) => {
            root.dataset.theme = theme;
            root.classList.toggle('dark', theme === 'dark');
            return [getComputedStyle(document.querySelector('#stats [data-collection-summary]')!).backgroundColor,
              getComputedStyle(document.body).backgroundColor];
          };
          const result = { light: read('light'), dark: read('dark') };
          if (before.theme === undefined) delete root.dataset.theme;
          else root.dataset.theme = before.theme;
          root.classList.toggle('dark', before.dark);
          return result;
        });
        for (const [theme, [face, ground]] of Object.entries(faces)) {
          assert.notEqual(face, ground, `${theme} 主题下高清版摘要和页面同一个底色：${face}`);
        }
      } finally { release(); await opened.close(); }
    });
    it(`垃圾卡骨架与落地同一副几何（${viewport.name}）`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/junk-files', viewport);
      let release = () => {};
      try {
        const page = opened.page;
        const pending = new Promise<void>(resolve => { release = resolve; });
        await page.route('**/api/ads?**', async route => {
          await pending;
          await route.fulfill({ json: { total: 2, all_total: 2, dismissed_total: 0, counts: { video: 2 },
            items: [1, 2].map(id => ({ id, name: `推广-${id}.mp4`, junk_kind: 'video', why: '文件名像推广',
              size: 1048576, location: 'local', cost: '' })) } });
        });
        await page.reload({ waitUntil: 'load' });
        const skeleton = page.locator('#grid .catalog-skeleton .skeletoncard').first();
        await skeleton.waitFor();
        const card = await box(skeleton);
        release();
        const first = page.locator('#grid [data-junk-card]').first();
        await first.waitFor();
        await settle(page);
        aligned(card, await box(first));
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
