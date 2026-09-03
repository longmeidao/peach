import { afterEach, describe, expect, it, vi } from 'vitest';

import { refreshStore, resetStores, storeNames } from '../src/state';
import {
  QUALITY_GOALS_URL, ensureQualityGoals, qualityGoals, qualityGoalsTotal,
  refreshQualityGoals, resetQualityGoals,
} from '../src/state/quality-goals';

import { deferredFetch, failFetch, goal, okFetch, payload } from './helpers';

afterEach(() => {
  resetStores();
  vi.unstubAllGlobals();
});

describe('共享 store 的写入口', () => {
  it('导出的是只读视图：直接赋值在运行期就失败，不是靠约定', () => {
    // @ts-expect-error 这条断言的目的就是「组件里写不了」既是类型错误也是运行期错误。
    expect(() => { qualityGoals.value = { data: null, error: '改我' }; }).toThrow(TypeError);
    expect(qualityGoals.value.error).toBe('');
  });

  it('登记的名字就是遗留层能刷新的名字', () => {
    expect(storeNames()).toEqual(['quality-goals']);
  });

  it('未登记的名字立刻失败，不是静默什么都不做', async () => {
    // @ts-expect-error 名字不在注册表里：运行期也要拦住。
    await expect(refreshStore('nope')).rejects.toThrow('未登记的共享 store：nope');
  });

  it('遗留层按名字刷新，拿到的是「成功了没有」而不是异常', async () => {
    vi.stubGlobal('fetch', okFetch(payload([goal({ id: 5 })])));
    expect(await refreshStore('quality-goals')).toBe(true);
    expect(qualityGoalsTotal.value).toBe(1);

    vi.stubGlobal('fetch', failFetch(503, '账本正在维护'));
    expect(await refreshStore('quality-goals'), '失败不抛：调用点在遗留层是 fire-and-forget')
      .toBe(false);
    expect(qualityGoals.value.error).toBe('账本正在维护');
  });
});

describe('高清版目标 store', () => {
  it('读到之前 total 是 null，不是 0：那和「一个都没有」是两件事', () => {
    expect(qualityGoalsTotal.value).toBeNull();
    expect(qualityGoals.value).toEqual({ data: null, error: '' });
  });

  it('取的是那个契约端点，结果落进 signal', async () => {
    const fetched = okFetch(payload([goal({ id: 1 }), goal({ id: 2 })]));
    vi.stubGlobal('fetch', fetched);
    const data = await refreshQualityGoals();
    expect(fetched.mock.calls[0]?.[0]).toBe(QUALITY_GOALS_URL);
    expect(data.items).toHaveLength(2);
    expect(qualityGoals.value.data?.items).toHaveLength(2);
    expect(qualityGoalsTotal.value).toBe(2);
  });

  it('ensure 只取一次：第二个读者读到的是同一份，不再发请求', async () => {
    const fetched = okFetch(payload([goal({ id: 3 })]));
    vi.stubGlobal('fetch', fetched);
    const first = await ensureQualityGoals();
    const second = await ensureQualityGoals();
    expect(fetched).toHaveBeenCalledTimes(1);
    expect(second).toBe(first);
  });

  it('两个读者同时开口也只发一个请求', async () => {
    const fetch = deferredFetch(payload([goal({ id: 4 })]));
    fetch.install();
    const both = Promise.all([ensureQualityGoals(), ensureQualityGoals()]);
    fetch.resolve();
    const [left, right] = await both;
    expect(fetch.fetched).toHaveBeenCalledTimes(1);
    expect(left).toBe(right);
  });

  it('refresh 无视缓存，ensure 之后仍然重取', async () => {
    vi.stubGlobal('fetch', okFetch(payload([goal({ id: 1, name: 'old.mp4' })])));
    await ensureQualityGoals();
    const fetched = okFetch(payload([goal({ id: 2, name: 'new.mp4' })]));
    vi.stubGlobal('fetch', fetched);
    await refreshQualityGoals();
    expect(fetched).toHaveBeenCalledTimes(1);
    expect(qualityGoals.value.data?.items[0]?.name).toBe('new.mp4');
  });

  it('失败态换掉旧数据：屏幕上不能既说读取失败又列着上一次的结果', async () => {
    vi.stubGlobal('fetch', okFetch(payload([goal({ id: 1 })])));
    await refreshQualityGoals();
    vi.stubGlobal('fetch', failFetch(409, '账本当前只能浏览'));
    await expect(refreshQualityGoals()).rejects.toThrow('账本当前只能浏览');
    expect(qualityGoals.value).toEqual({ data: null, error: '账本当前只能浏览' });
    expect(qualityGoalsTotal.value).toBeNull();
  });

  it('失败之后 ensure 会再试一次，不把错误态当成缓存', async () => {
    vi.stubGlobal('fetch', failFetch(500, '读取失败'));
    await expect(ensureQualityGoals()).rejects.toThrow('读取失败');
    const fetched = okFetch(payload([goal({ id: 9 })]));
    vi.stubGlobal('fetch', fetched);
    await ensureQualityGoals();
    expect(fetched).toHaveBeenCalledTimes(1);
    expect(qualityGoals.value.error).toBe('');
  });

  it('中止不写错误态：页面是被用户换掉的，不是读取失败', async () => {
    vi.stubGlobal('fetch', okFetch(payload([goal({ id: 1 })])));
    await refreshQualityGoals();
    const pending = deferredFetch(payload([goal({ id: 2 })]));
    pending.install();
    const controller = new AbortController();
    const refreshing = refreshQualityGoals(controller.signal);
    controller.abort();
    await expect(refreshing).rejects.toThrow();
    expect(qualityGoals.value.error, '中止被记成失败就是谎报').toBe('');
    expect(qualityGoals.value.data?.items[0]?.id).toBe(1);
  });

  it('迟到的响应盖不住比它更新的那一次', async () => {
    const slow = deferredFetch(payload([goal({ id: 1, name: 'slow.mp4' })]));
    slow.install();
    const first = refreshQualityGoals();
    const quick = deferredFetch(payload([goal({ id: 2, name: 'quick.mp4' })]));
    quick.install();
    const second = refreshQualityGoals();
    quick.resolve();
    await second;
    slow.resolve();
    await first;
    expect(qualityGoals.value.data?.items[0]?.name).toBe('quick.mp4');
  });

  it('reset 把状态清回未读，下一次 ensure 重新取', async () => {
    const fetched = okFetch(payload([goal({ id: 1 })]));
    vi.stubGlobal('fetch', fetched);
    await ensureQualityGoals();
    resetQualityGoals();
    expect(qualityGoals.value).toEqual({ data: null, error: '' });
    await ensureQualityGoals();
    expect(fetched).toHaveBeenCalledTimes(2);
  });
});
