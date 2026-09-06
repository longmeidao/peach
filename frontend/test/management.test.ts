import { describe, expect, it } from 'vitest';
import { cleanupSkeletonHtml, cloudLocations, cloudPreferenceLocations, tasteHistoryGuideHtml, wireTasteHistoryGuide, TASTE_GUIDE_KEY } from '../src/management';

describe('网盘功能范围', () => {
  it('本地与在线关注来源不显示网盘入口', () => {
    expect(cloudLocations([{ location: 'local' }, { location: 'online' }])).toEqual([]);
  });
  it('已配置但离线的网盘仍然提供状态入口', () => {
    expect(cloudLocations([{ location: '115', roots: ['B:\\'], online: false },
      { location: 'pikpak', roots: [] }])).toEqual(['115']);
  });
  it('重复文件只提供组内存在且已配置的网盘保留选项', () => {
    expect(cloudPreferenceLocations([{ location: 'local' }], ['115', 'pikpak'])).toEqual([]);
    expect(cloudPreferenceLocations([{ location: 'local' }, { location: '115' }], ['115', 'pikpak'])).toEqual(['115']);
    expect(cloudPreferenceLocations([{ location: '115' }], [])).toEqual([]);
  });
});

describe('数据管理首屏', () => {
  it('卡片复用最终正文和操作条，静态标题与按钮文本立即呈现', () => {
    const root = document.createElement('div');
    root.innerHTML = cleanupSkeletonHtml();
    const cards = root.querySelectorAll('.cleanupfieldset');
    expect(cards).toHaveLength(7);
    for (const card of cards) {
      expect(card.querySelector('.geist-fieldset-content > .geist-fieldset-title')).not.toBeNull();
      expect(card.querySelector('.geist-fieldset-footer > button')?.textContent).not.toBe('');
    }
    expect(cards[0]?.querySelector('p')?.textContent).toBe('下载高清封面，设置代理和 Cookie。');
    expect(cards[0]?.querySelector('.skeleton')).toBeNull();
    expect(root.querySelectorAll('.cleanup-count-skeleton')).toHaveLength(7);
    expect(root.querySelector('#resource-sync')).toBeNull();
  });
});

describe('浏览器历史引导', () => {
  it('首次引导可以跳过，普通访问可随时展开', () => {
    const root = document.createElement('div');
    root.innerHTML = tasteHistoryGuideHtml(true);
    expect(root.querySelector('details')?.open).toBe(true);
    expect(root.querySelector('.taste-guide-skip')?.textContent).toBe('跳过');
    root.innerHTML = tasteHistoryGuideHtml(false);
    expect(root.querySelector('details')?.open).toBe(false);
    expect(root.querySelector('.taste-guide-skip')).not.toBeNull();
  });
  it('完成导入或跳过后即使进入首次引导地址也不显示', () => {
    for (const onboarding of [true, false]) {
      expect(tasteHistoryGuideHtml(onboarding, true, false)).toBe('');
      expect(tasteHistoryGuideHtml(onboarding, false, true)).toBe('');
    }
  });
  it('折叠保留指南，跳过在刷新后仍生效且保留导入入口', () => {
    localStorage.removeItem(TASTE_GUIDE_KEY);
    const root = document.createElement('div');
    root.innerHTML = '<button data-taste-import>导入历史</button>' + tasteHistoryGuideHtml(true);
    wireTasteHistoryGuide(root, localStorage);
    root.querySelector('details')!.open = false;
    expect(localStorage.getItem(TASTE_GUIDE_KEY)).toBeNull();
    expect(root.querySelector('details')).not.toBeNull();
    root.querySelector<HTMLButtonElement>('.taste-guide-skip')!.click();
    expect(root.querySelector('details')).toBeNull();
    expect(root.querySelector('[data-taste-import]')).not.toBeNull();
    expect(tasteHistoryGuideHtml(true, false, localStorage.getItem(TASTE_GUIDE_KEY) === '1')).toBe('');
    localStorage.removeItem(TASTE_GUIDE_KEY);
  });
  it('下载入口有外链图标，指南复用现有操作且没有自动读取', () => {
    const root = document.createElement('div');
    root.innerHTML = tasteHistoryGuideHtml(true);
    const links = root.querySelectorAll('a[target="_blank"]');
    expect(links).toHaveLength(2);
    for (const link of links) {
      expect(link.getAttribute('rel')).toBe('noreferrer');
      expect(link.querySelector('use')?.getAttribute('href')).toBe('#i-external-link');
    }
    expect(root.textContent).toContain('读取 Peach 主机');
    expect(root.textContent).toContain('导入历史');
    expect(root.querySelector('script, form')).toBeNull();
  });
});
