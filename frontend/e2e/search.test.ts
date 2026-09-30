/* 顶栏搜索（`search` 岛，ADR-0031）：下拉栏里有什么、键盘怎么走、提交之后去哪儿。
 *
 * 补全（`/api/suggest`）与搜索记录（`/api/search-history`）在这里各给一份桩，好数请求、好看写进去的
 * 是什么；作品与详情沿用 `item-fixture.ts`。下拉栏的排版（两栏、页签、封面格）由 `design.test.ts` 量。 */
import assert from 'node:assert/strict';
import { after, before, describe, it } from 'node:test';

import type { Browser, Page } from 'playwright-core';

import { launch, VIEWPORTS } from './harness.ts';
import { openItemPage, type ItemVisit } from './item-fixture.ts';

const DESKTOP = VIEWPORTS.find((viewport) => !viewport.mobile)!;
const MENU = '#searchMenu';
const OPTION = `${MENU} [data-search-option]`;

/** 「七海」命中一位女优和一枚标签；别的词一条都没有。 */
const SUGGEST = {
  q: '七海',
  groups: [
    { kind: 'performer', label: '女优', total: 1, items: [
      { value: '七海ひな', n: 12, matched: '', entity_id: 90_001, has_image: false, rep: null, agency: '', works: [] },
    ] },
    { kind: 'tag', label: '标签', total: 1, items: [{ value: '七海の夏', n: 3, matched: '' }] },
  ],
};

interface Search extends ItemVisit {
  suggest: URL[];
  /** 桩里存着的搜索记录，最近的在前。 */
  history: string[];
  posts: { query?: string; operation?: string }[];
}

const fold = (value: string) => value.normalize('NFKC').trim().toLocaleLowerCase();

async function openSearch(browser: Browser, { limit = 10, history = [] as string[] } = {}): Promise<Search> {
  const opened = await openItemPage(browser, '/', DESKTOP, {
    settings: { searchHistoryLimit: limit }, ready: '#grid [data-media-card]',
  });
  const { page } = opened;
  const suggest: URL[] = [];
  const stored = [...history];
  const posts: Search['posts'] = [];
  await page.route(/\/api\/suggest\?/, (route) => {
    const url = new URL(route.request().url());
    suggest.push(url);
    const q = url.searchParams.get('q') || '';
    return route.fulfill({ json: q === SUGGEST.q ? SUGGEST : { q, groups: [] } });
  });
  await page.route(/\/api\/search-history/, (route) => {
    const request = route.request();
    if (request.method() === 'POST') {
      const body = request.postDataJSON() as Search['posts'][number];
      posts.push(body);
      const query = body.query || '';
      const kept = stored.filter((value) => fold(value) !== fold(query));
      stored.splice(0, stored.length, ...(body.operation === 'remove' ? kept : [query, ...kept]));
      return route.fulfill({ json: { ok: true } });
    }
    const want = Number(new URL(request.url()).searchParams.get('limit')) || 10;
    return route.fulfill({ json: { items: stored.slice(0, want) } });
  });
  await page.locator(`${MENU} > .peach-react`).waitFor({ state: 'attached', timeout: 15_000 });
  return { ...opened, suggest, history: stored, posts };
}

const values = (page: Page) => page.locator(OPTION).evaluateAll((rows) =>
  rows.map((row) => row.getAttribute('data-search-value')));
const active = (page: Page) => page.locator(OPTION).evaluateAll((rows) =>
  rows.flatMap((row) => (row.hasAttribute('data-active') ? [row.getAttribute('data-search-value')] : [])));
const query = (page: Page) => new URL(page.url()).searchParams.get('q');

async function typeQuery(opened: Search, text = SUGGEST.q) {
  const { page } = opened;
  await page.locator('#q').click();
  await page.keyboard.type(text);
  await page.locator(`${OPTION}[data-search-value="七海の夏"]`).waitFor({ timeout: 5_000 });
}

describe('顶栏搜索', () => {
  let browser: Browser;
  before(async () => { browser = await launch(); });
  after(async () => { await browser?.close(); });

  it('连敲几个字只问一次补全；下拉栏照后端给的组次序摆', { timeout: 60_000 }, async () => {
    const opened = await openSearch(browser);
    try {
      const { page, suggest } = opened;
      await typeQuery(opened);
      assert.deepEqual(suggest.map((url) => url.searchParams.get('q')), [SUGGEST.q], '连敲两个字发了不止一次补全');
      assert.deepEqual(await page.locator(`${MENU} [data-search-group] > h3`).allTextContents(), ['女优', '标签']);
      assert.deepEqual(await values(page), ['七海ひな', '七海の夏']);
      assert.equal(query(opened.page), null, '只是敲字，不该提交');
    } finally {
      await opened.close();
    }
  });

  it('上下键环绕着选；回车按选中的那一项搜，记进搜索记录，下拉栏收起', { timeout: 60_000 }, async () => {
    const opened = await openSearch(browser);
    try {
      const { page, posts } = opened;
      await typeQuery(opened);
      assert.deepEqual(await active(page), [], '刚画出来就有选中');
      for (const [key, want] of [['ArrowDown', '七海ひな'], ['ArrowDown', '七海の夏'], ['ArrowDown', '七海ひな'],
        ['ArrowUp', '七海の夏']] as const) {
        await page.keyboard.press(key);
        assert.deepEqual(await active(page), [want], `${key} 之后选中的不对`);
      }
      assert.equal(await page.locator('#q').inputValue(), SUGGEST.q, '上下键不该改输入框里的字');
      await page.keyboard.press('Enter');
      await page.waitForFunction(() => new URLSearchParams(location.search).get('q') === '七海の夏');
      await page.locator(MENU).waitFor({ state: 'hidden', timeout: 5_000 });
      assert.equal(await page.locator('#q').inputValue(), '七海の夏');
      assert.deepEqual(posts, [{ query: '七海の夏' }]);
      assert.notEqual(await page.evaluate(() => document.activeElement?.id), 'q', '提交之后焦点还留在输入框里');
    } finally {
      await opened.close();
    }
  });

  it('回车选中一位女优：打开她的资料页，不绕一趟搜索', { timeout: 60_000 }, async () => {
    const opened = await openSearch(browser);
    try {
      const { page, posts } = opened;
      await typeQuery(opened);
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      await page.waitForFunction(() => decodeURIComponent(location.pathname) === '/performers/七海ひな');
      assert.equal(query(page), null);
      assert.deepEqual(posts, [{ query: '七海ひな' }], '记进搜索记录的应当是这个名字');
    } finally {
      await opened.close();
    }
  });

  it('Escape 先只关下拉栏、字留着；再按一次才清空输入框', { timeout: 60_000 }, async () => {
    const opened = await openSearch(browser);
    try {
      const { page } = opened;
      await typeQuery(opened);
      await page.keyboard.press('Escape');
      await page.locator(MENU).waitFor({ state: 'hidden', timeout: 5_000 });
      assert.equal(await page.locator('#q').inputValue(), SUGGEST.q, '第一下 Escape 把字也清了');
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'q', '第一下 Escape 把焦点带走了');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#q').inputValue(), '', '第二下 Escape 没有清空');
      assert.equal(query(page), null, 'Escape 不该提交');
    } finally {
      await opened.close();
    }
  });

  it('组字期间的回车与方向键是给输入法的：不提交、不挪选中、不关下拉栏', { timeout: 60_000 }, async () => {
    const opened = await openSearch(browser);
    try {
      const { page, posts } = opened;
      await typeQuery(opened);
      await page.locator('#q').evaluate((input) => {
        input.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true, data: '' }));
        for (const key of ['ArrowDown', 'Enter']) {
          input.dispatchEvent(new KeyboardEvent('keydown', { key, isComposing: true, bubbles: true, cancelable: true }));
        }
      });
      await page.waitForTimeout(300);
      assert.equal(query(page), null, '组字期间的回车提交了搜索');
      assert.deepEqual(posts, []);
      assert.deepEqual(await active(page), [], '组字期间的方向键挪了选中');
      assert.equal(await page.locator(MENU).isVisible(), true, '组字期间的回车把下拉栏收了');
      await page.locator('#q').evaluate((input) => {
        input.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: '' }));
      });
      await page.keyboard.press('Enter');
      await page.waitForFunction(() => new URLSearchParams(location.search).get('q') === '七海');
      assert.deepEqual(posts, [{ query: '七海' }]);
    } finally {
      await opened.close();
    }
  });

  it('搜索记录照设置的条数摆；删一条只摘掉这一条，下拉栏和焦点都不走；新搜的词排到最前', { timeout: 60_000 }, async () => {
    const opened = await openSearch(browser, { limit: 3, history: ['甲片', '乙片', '丙片', '丁片'] });
    try {
      const { page, posts, history } = opened;
      const recent = () => page.locator(`${MENU} [data-search-group]`, { hasText: '搜索记录' })
        .locator('[data-search-option]').evaluateAll((rows) => rows.map((row) => row.getAttribute('data-search-value')));
      await page.locator('#q').click();
      await page.locator(`${OPTION}[data-search-value="丙片"]`).waitFor({ timeout: 5_000 });
      assert.deepEqual(await recent(), ['甲片', '乙片', '丙片'], '搜索记录没有照设置只摆三条');
      await page.locator(`${MENU} [data-remove-history="乙片"]`).click();
      await page.waitForFunction(() => !document.querySelector('#searchMenu [data-search-value="乙片"]'));
      assert.deepEqual(await recent(), ['甲片', '丙片']);
      assert.deepEqual(posts, [{ operation: 'remove', query: '乙片' }]);
      await page.waitForTimeout(300);
      assert.equal(await page.locator(MENU).isVisible(), true, '删一条记录把下拉栏收了');
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'q', '删一条记录把焦点抢走了');
      await page.keyboard.type('戊片');
      await page.keyboard.press('Enter');
      await page.waitForFunction(() => new URLSearchParams(location.search).get('q') === '戊片');
      assert.deepEqual(posts.at(-1), { query: '戊片' });
      assert.deepEqual(history.slice(0, 3), ['戊片', '甲片', '丙片']);
      await page.locator('#q').evaluate((input: HTMLInputElement) => { input.value = ''; });
      await page.locator('#q').click();
      await page.locator(`${OPTION}[data-search-value="戊片"]`).waitFor({ timeout: 5_000 });
      assert.deepEqual(await recent(), ['戊片', '甲片', '丙片']);
    } finally {
      await opened.close();
    }
  });
});
