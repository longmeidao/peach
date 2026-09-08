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
  it('读数卡与两张任务卡复用最终排版，静态标题、图标与按钮文本立即呈现', () => {
    const root = document.createElement('div');
    root.innerHTML = cleanupSkeletonHtml();
    const stats = root.querySelectorAll('.cleanupstats > .board-plain-stat');
    expect(stats).toHaveLength(5);
    expect([...stats].map(card => card.querySelector('.board-stat-tile use')?.getAttribute('href')))
      .toEqual(['#i-square-check-big', '#i-sparkles', '#i-file-stack', '#i-file-archive', '#i-trash']);
    expect([...stats].map(card => card.querySelector('.board-plain-stat-head')?.textContent))
      .toEqual(['人工复核', '高清版', '重复文件', '垃圾文件', '回收站']);
    for (const card of stats) {
      expect(card.hasAttribute('disabled')).toBe(true);
      expect(card.querySelector('strong > .cleanup-count-skeleton')).not.toBeNull();
      expect(card.querySelector('.cleanupmeta > .cleanup-count-skeleton')).not.toBeNull();
    }
    const cards = root.querySelectorAll('.cleanupgrid > .cleanupfieldset');
    expect(cards).toHaveLength(2);
    for (const card of cards) {
      expect(card.querySelector('.geist-fieldset-content > .geist-fieldset-title')).not.toBeNull();
      expect(card.querySelector('.geist-fieldset-footer > button')?.textContent).not.toBe('');
    }
    expect(cards[0]?.querySelector('p')?.textContent).toBe('扫描媒体文件夹，导入已有资料，采集缺失信息。');
    expect(cards[0]?.querySelector('.skeleton')).toBeNull();
    // 扫描卡的两枚键从骨架起就都在位，内容换入时只是变成可点。
    expect(cards[0]?.querySelector('.geist-fieldset-footer > a.geist-button')?.getAttribute('href')).toBe('/scraping');
    expect(cards[0]?.querySelector('.geist-fieldset-footer > button.geist-button.primary')?.hasAttribute('disabled')).toBe(true);
    expect(cards[1]?.classList.contains('cleanupemptyfolders')).toBe(true);
    expect(cards[1]?.querySelector('.geist-fieldset-footer use')?.getAttribute('href')).toBe('#i-scan-search');
    expect(root.querySelectorAll('.cleanup-count-skeleton')).toHaveLength(12);
    expect(root.querySelector('#resource-sync')).toBeNull();
  });
});

describe('浏览器历史引导', () => {
  it('首次引导可以跳过，普通访问可随时展开', () => {
    const root = document.createElement('div');
    root.innerHTML = tasteHistoryGuideHtml(true);
    expect(root.querySelector('details')?.open).toBe(true);
    expect(root.querySelector('.taste-guide-skip')?.textContent).toBe('跳过');
    expect(root.querySelector('.taste-guide-skip')?.classList.contains('geist-button')).toBe(true);
    expect(root.querySelector('.taste-guide-skip')?.hasAttribute('disabled')).toBe(false);
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
