import { describe, expect, it } from 'vitest';
import { sidebarTagCounts, syncSidebarSurface, sidebarHasCatalogContent } from '../src/sidebar';

describe('侧栏内容范围', () => {
  it('视频集合提供馆藏筛选，管理与索引页只提供导航', () => {
    for (const path of ['/', '/unseen', '/trash', '/item/1', '/creators/Demo', '/parts/1/2'])
      expect(sidebarHasCatalogContent(path)).toBe(true);
    for (const path of ['/follow-manage', '/stats', '/follow', '/tags', '/data-cleanup', '/creators'])
      expect(sidebarHasCatalogContent(path)).toBe(false);
  });
  it('管理页直达即建立导航，导航切换清除上一页标签', () => {
    const drawer = document.createElement('aside');
    expect(syncSidebarSurface(drawer, '/follow-manage')).toBe(true);
    drawer.innerHTML = '<div class="dnav">导航</div>';
    expect(syncSidebarSurface(drawer, '/follow-manage')).toBe(false);
    expect(drawer.textContent).toBe('导航');
    expect(syncSidebarSurface(drawer, '/')).toBe(true);
    drawer.innerHTML = '<div class="dnav">导航</div><div class="sec">视频标签</div>';
    expect(syncSidebarSurface(drawer, '/follow-manage')).toBe(true);
    expect(drawer.querySelector('.sec')).toBeNull();
  });

  it('相同页面保留筛选，查询变化清除旧集合', () => {
    const drawer = document.createElement('aside');
    syncSidebarSurface(drawer, '/?tag=a');
    drawer.innerHTML = '<div class="dnav"></div><div class="sec">a</div>';
    expect(syncSidebarSurface(drawer, '/?tag=a')).toBe(false);
    expect(drawer.querySelector('.sec')).not.toBeNull();
    expect(syncSidebarSurface(drawer, '/?tag=b')).toBe(true);
    expect(drawer.querySelector('.sec')).toBeNull();
  });

  it('只计当前内容的标签，空内容没有标签', () => {
    expect(sidebarTagCounts([{tags: ['a', 'a', 'b']}, {tags: ['b']}, {}]))
      .toEqual([['b', 2], ['a', 1]]);
    expect(sidebarTagCounts([])).toEqual([]);
  });
});
