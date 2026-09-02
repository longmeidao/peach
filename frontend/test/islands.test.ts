import { afterEach, describe, expect, it, vi } from 'vitest';

import { islandNames, mountIsland, unmountIsland } from '../src/islands';

import { deferredFetch, goal, legacyProps, payload } from './helpers';

const container = () => {
  const el = document.createElement('div');
  // 遗留层进入页面时先铺骨架，island 接手的容器里已经有东西。
  el.innerHTML = '<div class="geist-skeleton" data-skeleton="cards">正在读取高清版目标</div>';
  document.body.append(el);
  return el;
};

afterEach(() => {
  document.body.innerHTML = '';
  vi.unstubAllGlobals();
});

describe('island 注册表', () => {
  it('登记的名字就是遗留路由能挂载的名字', () => {
    expect(islandNames()).toEqual(['quality-goals']);
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
});
