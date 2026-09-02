import { render } from 'preact';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  QUALITY_GOALS_URL, QualityGoals, loadQualityGoals,
} from '../src/islands/quality-goals';
import type { QualityGoalsData } from '../src/islands/quality-goals';

import { goal, legacyProps, payload } from './helpers';

const mount = (data: QualityGoalsData | null, error = '') => {
  const el = document.createElement('div');
  document.body.append(el);
  const props = legacyProps();
  render(<QualityGoals {...props} data={data} error={error} />, el);
  return { el, props };
};

afterEach(() => {
  document.body.innerHTML = '';
  vi.unstubAllGlobals();
});

describe('高清版目标列表', () => {
  it('每条目标一张卡片，读数走遗留层同一套格式化口径', () => {
    const { el } = mount(payload([goal({
      id: 42, name: 'one.mp4', location: '115', cost: 'metered',
      duration: 3725, size: 2147483648, reason: '只有 720p',
    })]));
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

  it('探测失败的时长显示占位，不显示 0 也不显示负数', () => {
    const { el } = mount(payload([goal({ duration: -1, size: 0 })]));
    const cells = [...el.querySelectorAll('p.mono > span')].map(node => node.textContent);
    expect(cells).toEqual(['', '本地', '—', '0 MB']);
  });

  it('有番号封面就用番号封面，否则退回海报', () => {
    const withCover = mount(payload([goal({ has_cover: true, code: 'ABC-123' })]));
    expect(withCover.el.querySelector('img')?.getAttribute('src'))
      .toBe('/cover?code=ABC-123');
    const withoutCover = mount(payload([goal({ id: 7, has_cover: false })]));
    expect(withoutCover.el.querySelectorAll('img')[0]?.getAttribute('src'))
      .toBe('/poster?id=7&c=4');
  });

  it('封面取不到就把图摘掉，卡片其余部分照常显示', () => {
    const { el } = mount(payload([goal()]));
    const image = el.querySelector('img')!;
    image.dispatchEvent(new Event('error'));
    expect(el.querySelector('img')).toBeNull();
    expect(el.querySelector('.qualitycover')).not.toBeNull();
  });

  it('封面和标题都能打开详情，无障碍名称用纯文本形态', () => {
    const { el, props } = mount(payload([goal({ id: 42 })]));
    const cover = el.querySelector<HTMLButtonElement>('.qualitycover')!;
    expect(cover.getAttribute('aria-label')).toBe('打开 名称 one.mp4');
    cover.click();
    el.querySelector<HTMLButtonElement>('h3 button')!.click();
    expect(props.openItem.mock.calls).toEqual([[42], [42]]);
  });

  it('没有目标时用共享空态，不是一行灰字', () => {
    const { el } = mount(payload([]));
    expect(el.querySelector('[data-geist-empty-state]')).not.toBeNull();
    expect(el.querySelector('.es-copy h3')?.textContent).toBe('没有标记中的高清版目标');
    expect(el.querySelector('.qualityitem')).toBeNull();
  });

  it('读取失败时把原因留在原位，用 error Note', () => {
    const { el } = mount(null, '请求失败（500）');
    const note = el.querySelector('.geist-note-error');
    expect(note?.textContent).toContain('请求失败（500）');
    expect(el.querySelector('[data-geist-empty-state]')).toBeNull();
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
});
