/* 每条主路由在桌面与 390×844 下都要守住的不变量。
 *
 * 这些是界面验收里每一轮都要重测的几何与运行期事实：写成用例之后由测试入口执行，
 * 浏览器面板只留给新布局首次成形和观感判断。新发现的同类问题先在这里补一条再修。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser } from 'playwright-core';

import { layout, launch, requiredEnv, visit, VIEWPORTS } from './harness.ts';

const ROUTES = [
  '/',
  '/performers',
  '/studios',
  '/tags',
  '/playlists',
  '/follow',
  '/stats',
  '/review',
  '/data-cleanup',
  '/configuration',
  '/activity',
  `/item/${requiredEnv('PEACH_E2E_ITEM')}`,
];

describe('路由冒烟', () => {
  let browser: Browser;

  before(async () => {
    browser = await launch();
  });

  after(async () => {
    await browser.close();
  });

  for (const viewport of VIEWPORTS) {
    for (const route of ROUTES) {
      it(`${route} @ ${viewport.name}`, async () => {
        const opened = await visit(browser, route, viewport);
        try {
          assert.deepEqual(opened.problems, [], '页面报错或有失败请求');
          const box = await layout(opened.page);
          assert.ok(box.scrollWidth <= box.viewportWidth,
            `横向溢出：scrollWidth ${box.scrollWidth} > 视口 ${box.viewportWidth}`);
          assert.deepEqual(box.offenders, [], '有元素越出视口右边缘');
        } finally {
          await opened.close();
        }
      });
    }
  }
});
