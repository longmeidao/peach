import { render } from 'preact';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { QualityGoals, loadQualityGoals } from '../src/islands/quality-goals';
import { QUALITY_GOALS_URL, resetQualityGoals } from '../src/state/quality-goals';
import type { QualityGoal } from '../src/state/quality-goals';

import { goal, legacyProps, payload, seedGoals, seedGoalsError } from './helpers';

/** 画一遍当前的共享状态。数据不再由 props 传进来，所以先灌 store 再画。 */
const show = () => {
  const el = document.createElement('div');
  document.body.append(el);
  const props = legacyProps();
  render(<QualityGoals {...props} />, el);
  return { el, props };
};

const mountGoals = async (items: QualityGoal[]) => {
  await seedGoals(items);
  return show();
};

afterEach(() => {
  document.body.innerHTML = '';
  resetQualityGoals();
  vi.unstubAllGlobals();
});

describe('高清版目标列表', () => {
  it('每条目标一张卡片，读数走遗留层同一套格式化口径', async () => {
    const { el } = await mountGoals([goal({
      id: 42, name: 'one.mp4', location: '115', cost: 'metered',
      duration: 3725, size: 2147483648, reason: '只有 720p',
    })]);
    const item = el.querySelector('.qualityitem');
    expect(item).not.toBeNull();
    const cells = [...item!.querySelectorAll('p.mono > span')].map(node => node.textContent);
    expect(cells).toEqual(['', '115', '1:02:05', '2.0 GB']);
    expect(item!.querySelector('.src')?.getAttribute('data-location')).toBe('115');
    expect(item!.querySelector('.src')?.classList.contains('metered')).toBe(true);
    expect(item!.querySelector('h3 .javcode')?.textContent).toBe('one.mp4');
    expect(item!.querySelector('h3 button')?.hasAttribute('data-middle-truncate')).toBe(true);
    expect([...item!.querySelectorAll('p')].at(-1)?.textContent).toBe('只有 720p');
  });

  it('探测失败的时长显示占位，不显示 0 也不显示负数', async () => {
    const { el } = await mountGoals([goal({ duration: -1, size: 0 })]);
    const cells = [...el.querySelectorAll('p.mono > span')].map(node => node.textContent);
    expect(cells).toEqual(['', '本地', '—', '0 MB']);
  });

  it('有番号封面就用番号封面，否则退回海报', async () => {
    const withCover = await mountGoals([goal({ has_cover: true, code: 'ABC-123' })]);
    expect(withCover.el.querySelector('img')?.getAttribute('src'))
      .toBe('/cover?code=ABC-123');
    const withoutCover = await mountGoals([goal({ id: 7, has_cover: false })]);
    expect(withoutCover.el.querySelectorAll('img')[0]?.getAttribute('src'))
      .toBe('/poster?id=7&c=4');
  });

  it('封面取不到就把图摘掉，卡片其余部分照常显示', async () => {
    const { el } = await mountGoals([goal()]);
    const image = el.querySelector('img')!;
    image.dispatchEvent(new Event('error'));
    expect(el.querySelector('img')).toBeNull();
    expect(el.querySelector('.qualitycover')).not.toBeNull();
  });

  it('封面和标题都能打开详情，无障碍名称用纯文本形态', async () => {
    const { el, props } = await mountGoals([goal({ id: 42 })]);
    const cover = el.querySelector<HTMLButtonElement>('.qualitycover')!;
    expect(cover.getAttribute('aria-label')).toBe('打开 名称 one.mp4');
    cover.click();
    el.querySelector<HTMLButtonElement>('h3 button')!.click();
    expect(props.openItem.mock.calls).toEqual([[42], [42]]);
  });

  it('没有目标时用共享空态，不是一行灰字', async () => {
    const { el } = await mountGoals([]);
    expect(el.querySelector('[data-geist-empty-state]')).not.toBeNull();
    expect(el.querySelector('.es-copy h3')?.textContent).toBe('没有标记中的高清版目标');
    expect(el.querySelector('.qualityitem')).toBeNull();
  });

  it('读取失败时把原因留在原位，用 error Note', async () => {
    await seedGoalsError('请求失败（500）');
    const { el } = show();
    expect(el.querySelector('.geist-note-error')?.textContent).toContain('请求失败（500）');
    expect(el.querySelector('[data-geist-empty-state]')).toBeNull();
  });

  it('共享状态变了就自己重画，不用重新挂载一遍', async () => {
    const { el } = await mountGoals([goal({ id: 1, name: 'old.mp4' })]);
    expect(el.textContent).toContain('old.mp4');
    await seedGoals([goal({ id: 2, name: 'new.mp4' }), goal({ id: 3, name: 'also.mp4' })]);
    expect(el.querySelectorAll('.qualityitem')).toHaveLength(2);
    expect(el.textContent).toContain('new.mp4');
    expect(el.textContent).not.toContain('old.mp4');
  });
});

describe('loadQualityGoals', () => {
  it('取的是遗留层同一个契约端点，并把中止信号带下去', async () => {
    const fetched = vi.fn(async (_input: string, _init?: RequestInit) => (
      { ok: true, status: 200, json: async () => payload([]) }
    ));
    vi.stubGlobal('fetch', fetched);
    const controller = new AbortController();
    await loadQualityGoals(legacyProps(), controller.signal);
    expect(QUALITY_GOALS_URL).toBe('/api/quality-goals?limit=200');
    expect(fetched.mock.calls[0]?.[0]).toBe(QUALITY_GOALS_URL);
    expect((fetched.mock.calls[0]?.[1] as RequestInit).signal).toBe(controller.signal);
    expect((fetched.mock.calls[0]?.[1] as RequestInit).credentials).toBe('same-origin');
  });

  it('首屏一律重取：这一页的刷新就是重新进来一次，不能被缓存吃掉', async () => {
    await seedGoals([goal({ id: 1, name: 'cached.mp4' })]);
    const fetched = vi.fn(async (_input: string, _init?: RequestInit) => (
      { ok: true, status: 200, json: async () => payload([goal({ id: 2, name: 'fresh.mp4' })]) }
    ));
    vi.stubGlobal('fetch', fetched);
    const data = await loadQualityGoals(legacyProps(), new AbortController().signal);
    expect(fetched).toHaveBeenCalledTimes(1);
    expect(data.items[0]?.name).toBe('fresh.mp4');
  });
});
