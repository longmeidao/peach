import { act } from 'react';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { islandMounted, islandNames, mountIsland, unmountIsland } from '../src/islands';
import { queryClient } from '../src/react/query';

import { deferredFetch } from './helpers';

// 挂的是一棵真的 React 根，更新要在 `act` 里落地，否则断言读到的是上一帧。
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const container = () => {
  const el = document.createElement('div');
  // 遗留层进入页面时先铺骨架，island 接手的容器里已经有东西。
  el.innerHTML = '<div class="geist-skeleton" data-skeleton="cards">正在读取处理进度</div>';
  document.body.append(el);
  return el;
};

afterEach(async () => {
  // 页面自己的轮询挂在 React 根上，只清 DOM 不卸载的话，它会一直敲到下一条用例里。
  await act(async () => {
    for (const el of [...document.body.children]) unmountIsland(el);
  });
  document.body.innerHTML = '';
  // 首屏落在共用的 Query 缓存里，它是模块级的，会活过单个用例。
  queryClient.clear();
  vi.unstubAllGlobals();
});

/** 动态取回 React 产物再取数，中间隔几步不固定；等到条件成立为止。 */
async function until(ok: () => boolean, what: string): Promise<void> {
  for (let step = 0; step < 100; step += 1) {
    if (ok()) return;
    await new Promise((resolve) => { setTimeout(resolve, 0) });
  }
  throw new Error(`一直没等到：${what}`);
}

describe('island 注册表', () => {
  it('登记的名字就是遗留路由能挂载的名字', () => {
    expect(islandNames()).toEqual([
      'avatar-picker', 'library-processing', 'scraping', 'quality-goals', 'configuration', 'activity',
      'stats', 'taste']);
  });

  it('未注册的名字立刻失败，不是静默什么都不画', async () => {
    const el = container();
    // @ts-expect-error 名字不在契约里：这条断言的目的就是运行期也要拦住。
    await expect(mountIsland('nope', el, {})).rejects.toThrow('未注册的 island：nope');
  });
});

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

describe('mountIsland', () => {
  // 第一次 `import('@peach/react')` 要现编译整棵 React 子树，比用例里的等待窗口长得多。
  beforeAll(async () => { await import('@peach/react') });

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

const configuration = {
  editable: true, notice: '', revision: 'rev-1', media_dirs: ['D:\\Media'], port: 9123, facts: [],
  startup: { available: true, enabled: false, silent: true, message: '', desktop: false, desktop_message: '' },
  peach_proxy: { mode: 'environment', proxy_saved: false, needs_selection: false },
};

describe('配置页的分区拆分', () => {
  beforeAll(async () => { await import('@peach/react') });

  /* 遗留壳按 `.configgroup` 小标题把后面的兄弟节点切进左栏那一列（`configTabItems`），
     设置弹层挂完这一页紧接着就读它。`mountIsland` 返回时结构必须已经在 DOM 上——所以
     React 根的第一帧走 `flushSync`（`react/entry.tsx` 的 `mounter`）。
     分区自己怎么排在 `test/react/configuration.test.tsx`。 */
  it('挂载返回的那一刻，小标题和它的分区已经在容器里', async () => {
    const fetch = deferredFetch(configuration);
    fetch.install();
    const el = container();
    await act(async () => {
      const mounting = mountIsland('configuration', el, { receipt: vi.fn() });
      await until(() => fetch.fetched.mock.calls.length > 0, '取数发出去');
      fetch.resolve();
      await mounting;
      const titles = [...el.querySelectorAll('.configgroup')].map((title) => title.textContent);
      expect(titles, '标题还没落到 DOM 上，壳那一刻就拆不出分区')
        .toEqual(['通用', '媒体', '网络与访问', '更新与维护']);
      expect(el.querySelector('.configpage')?.parentElement?.classList.contains('peach-react')).toBe(true);
    });
  });

});

describe('unmountIsland', () => {
  beforeAll(async () => { await import('@peach/react') });

  it('没挂载过的容器是空操作，不抛错也不动 DOM', () => {
    const el = container();
    unmountIsland(el);
    expect(el.querySelector('[data-skeleton]')).not.toBeNull();
  });

  it('容器上挂没挂着，遗留层问得出来', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => tasks })));
    const el = container();
    expect(islandMounted(el)).toBe(false);
    // 取数还没回来也算挂着：这段时间里再挂一次会把在途那次作废，白等一趟。
    const mounting = mountIsland('activity', el, {});
    expect(islandMounted(el)).toBe(true);
    await act(async () => { await mounting });
    expect(islandMounted(el)).toBe(true);
    await act(async () => { unmountIsland(el) });
    expect(islandMounted(el)).toBe(false);
    // 遗留层拿到的可能是个空引用——那时页面上根本没有这个容器。
    expect(islandMounted(null)).toBe(false);
  });

  it('连子孙容器一起卸：壳只对外层调一次，里面那格也得停', async () => {
    const surface = container();
    // `/data-cleanup` 的形状：卡片挂在管理区正文里更深的一格上。
    const card = surface.ownerDocument.createElement('div');
    card.id = 'libraryProcessing';
    surface.append(card);

    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true, status: 200, json: async () => ({ status: 'idle' }),
    })));
    await act(async () => {
      await mountIsland('library-processing', card, { toast: vi.fn(), monitor: true });
    });
    expect(islandMounted(card)).toBe(true);

    // 遗留壳换页时只认识管理区正文这一个容器（`claimSurface` 对 `#stats` 调卸载）。
    await act(async () => { unmountIsland(surface) });
    expect(islandMounted(card), '外层卸了里面那棵根还活着的话，离开这页也会照原节律继续敲库')
      .toBe(false);
    expect(card.querySelector('.peach-react')).toBeNull();
  });
});
