import { act } from 'react';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { islandMounted, islandNames, mountIsland, unmountIsland } from '../src/islands';
import { queryClient } from '../src/react/query';
import { resetStores } from '../src/state';

import { deferredFetch, goal, legacyProps, payload, seedGoals } from './helpers';

// React 档挂的是一棵真的 React 根，更新要在 `act` 里落地，否则断言读到的是上一帧。
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const container = () => {
  const el = document.createElement('div');
  // 遗留层进入页面时先铺骨架，island 接手的容器里已经有东西。
  el.innerHTML = '<div class="geist-skeleton" data-skeleton="cards">正在读取高清版目标</div>';
  document.body.append(el);
  return el;
};

afterEach(() => {
  document.body.innerHTML = '';
  // 共享 store 是模块级的，会活过单个用例；不清就变成用例之间的隐藏耦合。
  resetStores();
  // React 档的首屏落在共用的 Query 缓存里，同样活过单个用例。
  queryClient.clear();
  vi.unstubAllGlobals();
});

/** React 档要先动态取回 React 产物再取数，中间隔几步不固定；等到条件成立为止。 */
async function until(ok: () => boolean, what: string): Promise<void> {
  for (let step = 0; step < 100; step += 1) {
    if (ok()) return;
    await new Promise((resolve) => { setTimeout(resolve, 0) });
  }
  throw new Error(`一直没等到：${what}`);
}

describe('island 注册表', () => {
  it('登记的名字就是遗留路由能挂载的名字', () => {
    expect(islandNames()).toEqual(
      ['library-processing', 'scraping', 'quality-goals', 'configuration', 'activity']);
  });

  it('未注册的名字立刻失败，不是静默什么都不画', async () => {
    const el = container();
    // @ts-expect-error 名字不在契约里：这条断言的目的就是运行期也要拦住。
    await expect(mountIsland('nope', el, {})).rejects.toThrow('未注册的 island：nope');
  });
});

describe('mountIsland', () => {
  it('取数期间保留遗留骨架，数据到位才一次性换掉', async () => {
    const fetch = deferredFetch(payload([goal()]));
    fetch.install();
    const el = container();
    const mounting = mountIsland('quality-goals', el, legacyProps());
    await Promise.resolve();
    expect(el.querySelector('[data-skeleton]'), '骨架被提前撤掉会出现第二段等待态').not.toBeNull();
    fetch.resolve();
    await mounting;
    expect(el.querySelector('[data-skeleton]')).toBeNull();
    expect(el.querySelectorAll('.qualityitem')).toHaveLength(1);
  });

  it('首屏取数失败时画出原因，不留在骨架上', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: false,
      status: 500,
      json: async () => ({ message: '账本当前只能浏览' }),
    })));
    const el = container();
    await mountIsland('quality-goals', el, legacyProps());
    expect(el.querySelector('.geist-note-error')?.textContent).toContain('账本当前只能浏览');
  });

  it('取数期间用户走开就不画：遗留层换页的判据是代，不是信号', async () => {
    const fetch = deferredFetch(payload([goal()]));
    fetch.install();
    const el = container();
    let current = true;
    const mounting = mountIsland('quality-goals', el, legacyProps(), {
      isCurrent: () => current,
    });
    await Promise.resolve();
    current = false;
    fetch.resolve();
    await mounting;
    expect(el.querySelector('.qualityitem'), '页面已经换掉，数据不能盖上去').toBeNull();
    expect(el.querySelector('[data-skeleton]')).not.toBeNull();
  });

  it('重新挂载时上一次的迟到响应不再写进容器', async () => {
    const stale = deferredFetch(payload([goal({ id: 7, name: 'stale.mp4' })]));
    stale.install();
    const el = container();
    const first = mountIsland('quality-goals', el, legacyProps());
    await Promise.resolve();

    const fresh = deferredFetch(payload([goal({ id: 9, name: 'fresh.mp4' })]));
    fresh.install();
    const second = mountIsland('quality-goals', el, legacyProps());
    fresh.resolve();
    await second;
    stale.resolve();
    await first;

    expect(el.querySelectorAll('.qualityitem')).toHaveLength(1);
    expect(el.textContent).toContain('fresh.mp4');
    expect(el.textContent).not.toContain('stale.mp4');
  });
});

describe('mountIsland 的 React 档', () => {
  // 第一次 `import('@peach/react')` 要现编译整棵 React 子树，比用例里的等待窗口长得多。
  beforeAll(async () => { await import('@peach/react') });

  const tasks = {
    available: true,
    running: [{
      id: 1, task_key: 'follow-check', task_label: '追更检查', trigger: 'manual', status: 'running',
      host: 'desk', started_at: '2026-09-11T10:00:00Z', finished_at: null, elapsed_seconds: 5,
      progress_current: null, progress_total: null, progress_label: '正在查第三个来源',
      result_summary: {}, error: '',
    }],
    skipped: [],
    finished: [],
  };

  it('先把首屏取回来再画，React 根挂在自己的 `.peach-react` 容器里', async () => {
    const fetch = deferredFetch(tasks);
    fetch.install();
    const el = container();
    const mounting = mountIsland('activity', el, {});
    await until(() => fetch.fetched.mock.calls.length > 0, '取数发出去');
    expect(el.querySelector('[data-skeleton]'), '数据还没回来就撤骨架会出现第二段等待态').not.toBeNull();
    fetch.resolve();
    await act(async () => { await mounting });
    expect(el.querySelector('[data-skeleton]')).toBeNull();
    // token、Preflight 与焦点规则都作用在 `.peach-react` 上，根不挂在它里面就没有样式。
    expect(el.querySelector('.peach-react')?.textContent).toContain('追更检查');
  });

  it('取数期间用户走开就不画，骨架留给下一页', async () => {
    const fetch = deferredFetch(tasks);
    fetch.install();
    const el = container();
    let current = true;
    const mounting = mountIsland('activity', el, {}, { isCurrent: () => current });
    await until(() => fetch.fetched.mock.calls.length > 0, '取数发出去');
    current = false;
    fetch.resolve();
    await act(async () => { await mounting });
    expect(el.querySelector('.peach-react'), '页面已经换掉，React 根不能挂上去').toBeNull();
    expect(el.querySelector('[data-skeleton]')).not.toBeNull();
  });

  it('卸载时中止在途取数，画过的话连 React 根一起撤掉', async () => {
    const fetch = deferredFetch(tasks);
    fetch.install();
    const el = container();
    const mounting = mountIsland('activity', el, {});
    await until(() => fetch.fetched.mock.calls.length > 0, '取数发出去');
    unmountIsland(el);
    await mounting;
    expect(fetch.signal()?.aborted, '离开页面必须真的中止请求').toBe(true);
    expect(el.querySelector('[data-skeleton]'), '还没画过就卸载，容器里是遗留骨架').not.toBeNull();

    const again = deferredFetch(tasks);
    again.install();
    const painting = mountIsland('activity', el, {});
    await until(() => again.fetched.mock.calls.length > 0, '第二次取数发出去');
    again.resolve();
    await act(async () => { await painting });
    expect(islandMounted(el)).toBe(true);
    await act(async () => { unmountIsland(el) });
    expect(el.querySelector('.peach-react'), 'React 根和它的容器要跟着卸载一起走').toBeNull();
    expect(islandMounted(el)).toBe(false);
  });
});

describe('unmountIsland', () => {
  it('中止在途取数并清空容器', async () => {
    const fetch = deferredFetch(payload([goal()]));
    fetch.install();
    const el = container();
    const mounting = mountIsland('quality-goals', el, legacyProps());
    await Promise.resolve();
    unmountIsland(el);
    await mounting;
    expect(fetch.signal()?.aborted, '离开页面必须真的中止请求').toBe(true);
    expect(el.querySelector('.qualityitem')).toBeNull();
    expect(el.querySelector('[data-skeleton]'),
      '还没画过就卸载时容器里是遗留骨架，island 不该清掉不属于它的东西').not.toBeNull();
  });

  it('没挂载过的容器是空操作，不抛错也不动 DOM', () => {
    const el = container();
    unmountIsland(el);
    expect(el.querySelector('[data-skeleton]')).not.toBeNull();
  });

  it('容器上挂没挂着，遗留层问得出来', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => payload([goal()]),
    })));
    const el = container();
    expect(islandMounted(el)).toBe(false);
    // 取数还没回来也算挂着：这段时间里再挂一次会把在途那次作废，白等一趟。
    const mounting = mountIsland('quality-goals', el, legacyProps());
    expect(islandMounted(el)).toBe(true);
    await mounting;
    expect(islandMounted(el)).toBe(true);
    unmountIsland(el);
    expect(islandMounted(el)).toBe(false);
    // 遗留层拿到的可能是个空引用——那时页面上根本没有这个容器。
    expect(islandMounted(null)).toBe(false);
  });

  it('卸载之后共享状态再变也不重画：订阅要跟着组件一起走', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => payload([goal({ id: 1, name: 'one.mp4' })]),
    })));
    const el = container();
    const props = legacyProps();
    await mountIsland('quality-goals', el, props);
    expect(el.querySelectorAll('.qualityitem')).toHaveLength(1);
    const painted = props.javTitleHtml.mock.calls.length;
    expect(painted).toBeGreaterThan(0);

    unmountIsland(el);
    // 换一份完全不同的数据。还留着订阅的话，组件会为一个已经卸载的容器再画一次。
    await seedGoals([goal({ id: 2, name: 'after.mp4' }), goal({ id: 3, name: 'more.mp4' })]);
    expect(props.javTitleHtml.mock.calls.length, '卸载后组件仍在响应 signal，订阅泄漏了')
      .toBe(painted);
    expect(el.querySelector('.qualityitem')).toBeNull();
    expect(el.textContent).not.toContain('after.mp4');
  });
});
