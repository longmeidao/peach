import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import type { Browser } from 'playwright-core';
import { launch, layout, settle, visit, VIEWPORTS } from './harness.ts';

describe('来源链接与凭据布局', () => {
  let browser: Browser;
  before(async () => { browser = await launch(); });
  after(async () => { await browser?.close(); });
  for (const viewport of VIEWPORTS) {
    it(`GitHub 标识、网址和外链箭头居中对齐（${viewport.name}）`, async () => {
      const opened = await visit(browser, '/scraping', viewport);
      try {
        await opened.page.route('**/api/scraping/amane-bridge', route => route.fulfill({ json: {
          installed: true, installed_version: '0.17.0', version: '0.17.0',
          repository: 'https://github.com/sgzw-x/amane', license: 'GPL-3.0', sites: [], job: { status: 'idle' },
        } }));
        await opened.page.reload();
        const link = opened.page.locator('section[aria-label="amane"] a');
        await link.waitFor(); await settle(opened.page);
        const positions = await link.evaluate(node => {
          const boxes = [node.querySelector('img')!, node.querySelector('span')!, node.querySelector('svg')!].map(el => {
            const r = el.getBoundingClientRect(); return { center: r.y + r.height / 2, width: r.width };
          });
          return boxes;
        });
        assert.equal(positions.length, 3);
        assert.ok(positions.every(p => p.width > 0));
        assert.ok(Math.max(...positions.map(p => p.center)) - Math.min(...positions.map(p => p.center)) <= 1);
        const dimensions = await layout(opened.page);
        assert.ok(dimensions.scrollWidth <= dimensions.viewportWidth);
      } finally { await opened.close(); }
    });
    it(`凭据的每个输入字段占满正文宽度（${viewport.name}）`, async () => {
      const opened = await visit(browser, '/follow-manage?tab=source', viewport);
      try {
        await opened.page.route('**/api/follow/credentials', route => route.fulfill({ json: {
          root: '', providers: [{ provider: 'simpcity', provider_label: 'SimpCity', followable: true,
            requirement: 'required', needs: ['cookie', 'user_agent'], fields: [], missing: ['cookie', 'user_agent'], why: '来源登录说明' }],
        } }));
        await opened.page.reload();
        const field = opened.page.getByLabel('cookie', { exact: true });
        await field.waitFor(); await settle(opened.page);
        for (const name of ['cookie', 'user_agent']) {
          const geometry = await opened.page.getByLabel(name, { exact: true }).evaluate(node => {
            const wrapper = node.closest('[data-input-size]')!;
            return { width: wrapper.getBoundingClientRect().width, available: wrapper.parentElement!.getBoundingClientRect().width };
          });
          assert.ok(Math.abs(geometry.width - geometry.available) <= 1, JSON.stringify(geometry));
        }
        const dimensions = await layout(opened.page);
        assert.ok(dimensions.scrollWidth <= dimensions.viewportWidth);
      } finally { await opened.close(); }
    });
  }
});
