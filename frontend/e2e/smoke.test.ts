/* 每条主路由在桌面与 390×844 下都要守住的不变量。
 *
 * 这些是界面验收里每一轮都要重测的几何与运行期事实：写成用例之后由测试入口执行，
 * 浏览器面板只留给新布局首次成形和观感判断。新发现的同类问题先在这里补一条再修。
 *
 * 每条路由先等它自己的主体出现，再 settle、再量几何。报错、失败请求、横向溢出和等待态
 * 这几条在页面完全没渲染时全都成立，不写主体的话白屏也是绿的。主体按 `tests/test_web_e2e.py`
 * 生成的演示库写：12 条视频，没有播放列表、关注来源和任务记录，这几页等到的是各自的空态。
 * 女优、厂牌与标签的索引在一轮里会从空变成有：前面的路由打开过作品之后条目就出现了，
 * 所以索引页的主体是「条目或空态」二选一，不绑死其中一种。标题只能拿来认页面，不能单独
 * 当主体：管理页的 `#manageTitle` 由外壳先写好，内容区失败时它照样在。
 *
 * 分区 tab（`.board-local-nav`）只显示当前那一格，其余面板不参与布局；每一格都切过去
 * 再测一遍，否则配置页「网络与访问」这类不在首屏的分区永远不会被量到。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Locator, Page } from 'playwright-core';

import { layout, launch, requiredEnv, settle, visit, VIEWPORTS } from './harness.ts';

interface Route {
  path: string;
  /** 目标页面主体：每个定位器都要可见。骨架屏的占位标题带 `aria-hidden`，按角色找不到。 */
  body(page: Page): Locator[];
}

const heading = (page: Page, scope: string, name: string): Locator =>
  page.locator(scope).getByRole('heading', { name, exact: true });

/** 索引条目（`data-k`）或明确的空态，先出现哪个算哪个。 */
const indexEntries = (page: Page): Locator =>
  page.locator('#index [data-k], #index [data-geist-empty-state]').first();

const ROUTES: readonly Route[] = [
  { path: '/', body: (page) => [page.locator('#grid article.card').first()] },
  { path: '/performers', body: (page) => [heading(page, '#index', '艺人'), indexEntries(page)] },
  { path: '/studios', body: (page) => [heading(page, '#index', '厂牌'), indexEntries(page)] },
  { path: '/tags', body: (page) => [heading(page, '#index', '标签'), indexEntries(page)] },
  {
    path: '/playlists',
    body: (page) => [heading(page, '#stats', '播放列表'), heading(page, '#stats', '还没有播放列表')],
  },
  {
    path: '/follow',
    body: (page) => [heading(page, '#stats', '关注'), heading(page, '#stats', '还没有关注任何来源')],
  },
  {
    path: '/stats',
    body: (page) => [heading(page, '#main', '统计'), page.locator('#stats').getByText('馆藏视频', { exact: true })],
  },
  { path: '/review', body: (page) => [heading(page, '#main', '人工复核'), heading(page, '#stats', '复核分类')] },
  {
    path: '/data-cleanup',
    body: (page) => [heading(page, '#main', '数据管理'), heading(page, '#stats', '扫描与采集')],
  },
  {
    path: '/configuration',
    body: (page) => [heading(page, '#main', '配置'), page.locator('#stats').getByRole('tab', { name: '通用' })],
  },
  { path: '/activity', body: (page) => [heading(page, '#main', '活动'), heading(page, '#stats', '还没有任务记录')] },
  {
    path: `/item/${requiredEnv('PEACH_E2E_ITEM')}`,
    body: (page) => {
      const stage = page.getByRole('dialog', { name: '作品详情' });
      return [stage, stage.locator('video')];
    },
  },
];

async function assertBody(page: Page, route: Route): Promise<void> {
  for (const locator of route.body(page)) {
    try {
      await locator.waitFor({ state: 'visible', timeout: 15_000 });
    } catch (error) {
      // 带上此刻的无障碍树：CI 上只有这段输出，看得出停在骨架、空态换了文案还是整块没画。
      const snapshot = await page.locator('#main').ariaSnapshot({ timeout: 5_000 }).catch(() => '未取得');
      assert.fail(`${route.path}：页面主体没有出现，等不到 ${locator}\n${(error as Error).message}\n`
        + `#main 当时的无障碍树：\n${snapshot.slice(0, 3000)}`);
    }
  }
}

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
      it(`${route.path} @ ${viewport.name}`, { timeout: 60_000 }, async () => {
        const opened = await visit(browser, route.path, viewport);
        try {
          await assertBody(opened.page, route);
          await settle(opened.page);
          await assertHolds(opened.page, opened.problems, route.path);
          // 设置浮层的那一排 tab 常驻 DOM、关着时不可见；只点页面上看得见的那一排。
          const tabs = opened.page.locator('.board-local-nav [role="tab"]:visible');
          const count = await tabs.count();
          // 选择器一旦对不上，循环一格都不跑也照样绿；配置页至少有媒体、网络与访问、更新与维护三格。
          if (route.path === '/configuration') assert.ok(count >= 3, `配置页只看到 ${count} 个分区 tab`);
          for (let index = 0; index < count; index += 1) {
            const tab = tabs.nth(index);
            const name = (await tab.textContent())?.trim() || `第 ${index + 1} 格`;
            await tab.click({ timeout: 5_000 });
            await settle(opened.page);
            assert.equal(await tab.getAttribute('aria-selected'), 'true', `${route.path}「${name}」点了没有选中`);
            await assertHolds(opened.page, opened.problems, `${route.path}「${name}」`);
          }
        } finally {
          await opened.close();
        }
      });
    }
  }
});
