import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';
import type { Browser, Page } from 'playwright-core';
import { configurationBody, expectBody, launch, layout, settle, visit, VIEWPORTS } from './harness.ts';

const measure = (page: Page) => page.locator('.configpage').evaluate(root => {
  const rect = (el: Element) => {
    const r = el.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  };
  const sections = ['开机自启', '外部入口'].map(name => root.querySelector(`[aria-label="${name}"]`)!);
  return {
    nav: rect(root.querySelector('.board-local-nav')!),
    selected: root.querySelector('.board-local-nav [aria-selected="true"]')?.textContent,
    sections: sections.map(section => ({
      label: rect(section.firstElementChild!),
      card: rect(section.lastElementChild!),
      save: rect(section.querySelector('button')!),
    })),
  };
});

describe('配置页等待态', () => {
  let browser: Browser;
  before(async () => { browser = await launch() });
  after(async () => { await browser?.close() });
  for (const viewport of VIEWPORTS) {
    it(`${viewport.name} 的标题、卡片、页签和保存键在接管时保持几何`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/configuration', viewport);
      let release = () => {};
      try {
        await expectBody(opened.page, '/configuration', configurationBody(opened.page));
        await settle(opened.page);
        const pending = new Promise<void>(resolve => { release = resolve });
        await opened.page.route('**/api/configuration', async route => {
          const response = await route.fetch();
          const data = await response.json();
          await pending;
          await route.fulfill({ json: { ...data, startup: {
            available: true, enabled: true, silent: true, desktop: true, desktop_message: '', message: '',
          } } });
        });
        await opened.page.reload({ waitUntil: 'load' });
        await opened.page.locator('[data-skeleton="board/configuration"]').waitFor();
        const skeleton = await measure(opened.page);
        const waitingLayout = await layout(opened.page);
        release();
        await expectBody(opened.page, '/configuration', configurationBody(opened.page));
        await settle(opened.page);
        const live = await measure(opened.page);
        assert.equal(skeleton.selected, live.selected);
        const pairs = [[skeleton.nav, live.nav], ...skeleton.sections.flatMap((section, i) =>
          (['label', 'card', 'save'] as const).map(key => [section[key], live.sections[i][key]]))];
        for (const [a, b] of pairs) for (const key of ['x', 'y', 'width', 'height'] as const) {
          assert.ok(Math.abs(a[key] - b[key]) <= 1, `${key}: skeleton=${a[key]}, content=${b[key]}`);
        }
        assert.ok(waitingLayout.scrollWidth <= waitingLayout.viewportWidth);
        assert.deepEqual(waitingLayout.offenders, []);
        assert.deepEqual(opened.problems, []);
      } finally {
        release();
        await opened.close();
      }
    });
  }
});
