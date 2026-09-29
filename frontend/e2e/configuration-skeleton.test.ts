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
    it(`${viewport.name} 的分类导航适配方向并保留未保存输入`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, '/configuration', viewport);
      try {
        const { page } = opened;
        await expectBody(page, '/configuration', configurationBody(page));
        await settle(page);
        const nav = page.getByRole('tablist', { name: '配置分区' });
        assert.equal(await nav.getAttribute('aria-orientation'), 'horizontal');
        const geometry = await measure(page);
        assert.ok(geometry.nav.y + geometry.nav.height <= geometry.sections[0].label.y);
        const input = page.getByRole('textbox', { name: 'JavDB 地址', exact: true });
        await input.fill('example.invalid');
        const general = nav.getByRole('tab', { name: '通用', exact: true });
        await general.focus();
        await page.keyboard.press('ArrowRight');
        assert.equal(await nav.getByRole('tab', { name: '媒体', exact: true }).getAttribute('aria-selected'), 'true');
        await page.keyboard.press('End');
        assert.equal(await nav.getByRole('tab', { name: '更新与维护' }).getAttribute('aria-selected'), 'true');
        await page.keyboard.press('Home');
        assert.equal(await input.inputValue(), 'example.invalid');
        const bounds = await layout(page);
        assert.ok(bounds.scrollWidth <= bounds.viewportWidth);
        assert.deepEqual(bounds.offenders, []);
        await page.setViewportSize({ width: viewport.mobile ? 1280 : 390, height: 844 });
        await page.waitForFunction(expected => document.querySelector('.configpage>.board-local-nav')?.getAttribute('aria-orientation') === expected,
          'horizontal');
        assert.equal(await general.getAttribute('aria-selected'), 'true');
        assert.equal(await input.inputValue(), 'example.invalid');
        assert.deepEqual(opened.problems, []);
      } finally { await opened.close() }
    });
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
  for (const path of ['/configuration', '/review']) {
    it(`${path} 的明暗主题使用透明容器与灰色 Pills 选中底色`, { timeout: 60_000 }, async () => {
      const opened = await visit(browser, path, VIEWPORTS[0]);
      try {
        const { page } = opened;
        const nav = page.locator('#stats [data-section-nav]:not([data-skeleton] *)');
        await nav.locator('[aria-selected=true]').waitFor();
        await settle(page);
        if (path === '/review') {
          assert.equal(await nav.getByRole('heading', { name: '复核分类' }).count(), 1);
          assert.equal(await nav.getByRole('tablist').getAttribute('aria-orientation'), 'vertical');
        }
        for (const dark of [false, true]) {
          await page.evaluate(dark => {
            document.documentElement.dataset.theme = dark ? 'dark' : 'light';
            document.documentElement.classList.toggle('dark', dark);
          }, dark);
          const colors = await nav.evaluate(node => {
            const selected = getComputedStyle(node.querySelector('[aria-selected=true]')!);
            const inactive = getComputedStyle(node.querySelector('[aria-selected=false]')!);
            return {
              surface: getComputedStyle(node).backgroundColor,
              selected: selected.backgroundColor,
              border: selected.borderWidth,
              radius: selected.borderRadius,
              text: selected.color,
              inactive: inactive.color,
              inactiveBackground: inactive.backgroundColor,
            };
          });
          assert.equal(colors.surface, 'rgba(0, 0, 0, 0)');
          assert.notEqual(colors.selected, 'rgba(0, 0, 0, 0)');
          assert.equal(colors.border, '0px');
          assert.notEqual(colors.radius, '0px');
          assert.notEqual(colors.text, colors.inactive);
          assert.equal(colors.inactiveBackground, 'rgba(0, 0, 0, 0)');
        }
        assert.deepEqual(opened.problems, []);
      } finally { await opened.close() }
    });
  }
});
