/* 每条主路由在桌面与 390×844 下都要守住的不变量。
 *
 * 这些是界面验收里每一轮都要重测的几何与运行期事实：写成用例之后由测试入口执行，
 * 浏览器面板只留给新布局首次成形和观感判断。新发现的同类问题先在这里补一条再修。
 *
 * 分区 tab（`.board-local-nav`）只显示当前那一格，其余面板不参与布局；每一格都切过去
 * 再测一遍，否则配置页「网络与访问」这类不在首屏的分区永远不会被量到。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { layout, launch, requiredEnv, settle, visit, VIEWPORTS } from './harness.ts';

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

async function assertHolds(page: Page, problems: string[], where: string): Promise<void> {
  assert.deepEqual(problems, [], `${where}：页面报错或有失败请求`);
  const box = await layout(page);
  assert.ok(box.scrollWidth <= box.viewportWidth,
    `${where}：横向溢出，scrollWidth ${box.scrollWidth} > 视口 ${box.viewportWidth}`);
  assert.deepEqual(box.offenders, [], `${where}：有元素越出视口右边缘`);
}

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
      // 单条超时远小于 Python 侧的整轮超时：卡住的那一条自己报名字，不拖垮整轮输出。
      it(`${route} @ ${viewport.name}`, { timeout: 60_000 }, async () => {
        const opened = await visit(browser, route, viewport);
        try {
          await assertHolds(opened.page, opened.problems, route);
          // 设置浮层的那一排 tab 常驻 DOM、关着时不可见；只点页面上看得见的那一排。
          const tabs = opened.page.locator('.board-local-nav [role="tab"]:visible');
          const count = await tabs.count();
          // 选择器一旦对不上，循环一格都不跑也照样绿；配置页至少有媒体、网络与访问、更新与维护三格。
          if (route === '/configuration') assert.ok(count >= 3, `配置页只看到 ${count} 个分区 tab`);
          for (let index = 0; index < count; index += 1) {
            const tab = tabs.nth(index);
            const name = (await tab.textContent())?.trim() || `第 ${index + 1} 格`;
            await tab.click({ timeout: 5_000 });
            await settle(opened.page);
            assert.equal(await tab.getAttribute('aria-selected'), 'true', `${route}「${name}」点了没有选中`);
            await assertHolds(opened.page, opened.problems, `${route}「${name}」`);
          }
        } finally {
          await opened.close();
        }
      });
    }
  }
});
