import { describe, expect, it } from 'vitest';
import { cleanupSkeletonHtml, cloudLocations, cloudPreferenceLocations } from '../src/management';

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
    // 扫描卡包含来源入口和禁用的分体操作。
    expect(cards[0]?.querySelector('.geist-fieldset-footer > a.board-link-button')?.getAttribute('href')).toBe('/scraping');
    expect(cards[0]?.querySelector('.board-link-button use')?.getAttribute('href')).toBe('#i-arrow-up');
    expect(cards[0]?.querySelector('.splitmain use')?.getAttribute('href')).toBe('#i-database');
    expect(cards[0]?.querySelector('.geist-fieldset-footer .splitbutton button.splitmain')?.hasAttribute('disabled')).toBe(true);
    expect(cards[1]?.classList.contains('cleanupemptyfolders')).toBe(true);
    expect(cards[1]?.querySelector('.geist-fieldset-footer use')?.getAttribute('href')).toBe('#i-scan-search');
    expect(root.querySelectorAll('.cleanup-count-skeleton')).toHaveLength(18);
    expect(Array.from(root.querySelectorAll('.resourcesync > h2'), title => title.textContent)).toEqual(['链接管理', '资源同步']);
    expect(root.querySelectorAll('.linkstats > div')).toHaveLength(5);
    expect(root.querySelectorAll('.resourcesyncfooter button:disabled')).toHaveLength(2);
    expect(root.querySelector('#resource-sync')).toBeNull();
  });
});
