import { describe, expect, it, vi } from 'vitest';
import { boardPageSkeleton, detailSkeletonHtml } from '../src/board-skeleton';
import { wireBoardSegments } from '../src/board-controls';

vi.mock('@peach/legacy/core', async importOriginal => ({
  ...await importOriginal<object>(),
  icon: (name: string) => `<svg aria-hidden="true" data-icon="${name}"></svg>`,
}));

describe('Board 页面骨架', () => {
  it.each(['/stats', '/taste', '/follow-manage', '/configuration', '/activity', '/duplicates', '/quality-goals', '/playlists'])('为 %s 提供单一等待语义', path => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton(path);
    expect(root.querySelectorAll('[role="status"]')).toHaveLength(1);
    expect(root.querySelector('[aria-hidden="true"]')).not.toBeNull();
    expect(root.querySelector('[aria-hidden="true"][inert]')).not.toBeNull();
    for (const control of root.querySelectorAll('button, input, a, summary')) {
      expect(control.closest('[inert]')).not.toBeNull();
    }
  });
  it('统计预留四张指标卡，未知页面交给自身骨架', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/stats');
    expect(root.querySelectorAll('.tastesummary')).toHaveLength(4);
    expect(boardPageSkeleton('/item/5')).toBe('');
  });
  it.each([
    ['/stats', '.insightpanel > .insightpanelbody', 2],
    ['/activity', '.activitysection', 3],
    ['/duplicates', '.dupgroup .duprow', 4],
    ['/quality-goals', '.qualityitem > .qualitycover', 6],
    ['/follow-manage', '.fmanageoverview > div', 4],
    ['/configuration', '.configfieldset', 1],
    ['/playlists', '.playlistcards > .playlistcard', 6],
  ] as const)('%s 复用最终内容容器', (path, selector, count) => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton(path);
    expect(root.querySelectorAll(selector)).toHaveLength(count);
    expect(root.querySelector('.skeleton-cards')).toBeNull();
  });
  it('详情保留媒体区和资料侧栏，不创建播放器', () => {
    const root = document.createElement('div');
    root.innerHTML = detailSkeletonHtml();
    expect(root.querySelector('.sgrid > .vwrap')).not.toBeNull();
    expect(root.querySelector('.sgrid > .side > .sidecontent')).not.toBeNull();
    expect(root.querySelectorAll('video, audio, iframe')).toHaveLength(0);
    expect(root.querySelectorAll('[role="status"]')).toHaveLength(1);
  });
  it('关注骨架的工作区切换保留原来的分段控件', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/follow-manage');
    wireBoardSegments(root);
    expect(root.querySelector('.board-segment-thumb')).toBeNull();
    expect(root.querySelector('.skeleton-segment-selected')?.textContent).toBe('关注列表');
    expect(root.querySelectorAll('.skeleton-segments > span')).toHaveLength(3);
    expect(root.querySelectorAll('.board-button-group > button')).toHaveLength(2);
    expect(root.querySelector('[data-follow-workspace-panel="list"]')).not.toBeNull();
    expect(root.querySelector('[data-follow-panel="sources"]')).toBeNull();
    expect(root.querySelectorAll('.board-follow-list .fauthor')).toHaveLength(4);
    expect(root.querySelectorAll('.fauthorsources .fsource.frow')).toHaveLength(12);
    expect(root.querySelectorAll('.fsource.frow > *')).toHaveLength(60);
    expect(root.querySelectorAll('.board-follow-selection button')).toHaveLength(0);
    expect(root.querySelector('.followtoolbaractions')?.lastElementChild?.textContent).toBe('全部收起');
    expect(root.querySelector('.followpagefooter')).not.toBeNull();
    expect(root.querySelector('.selectiondock')).toBeNull();
  });
  it('口味骨架保留分段背景与状态行间距', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/taste');
    expect(root.querySelector('.insightswitch[data-board-segments]')).not.toBeNull();
    expect(root.querySelector('.skeleton-segment-selected')?.textContent).toBe('浏览器记录');
    expect(root.querySelector('.tastehead + .tastestate + .tastesummaries')).not.toBeNull();
    expect(root.querySelector('.tastehead .skeleton-tabs')).toBeNull();
  });
  it('关注表格视图预留表头与来源行',()=>{
    const root=document.createElement('div');root.innerHTML=boardPageSkeleton('/follow-manage',{followLayout:'table'});
    expect(root.querySelector('.fsources[data-layout="table"]')).not.toBeNull();
    expect(root.querySelectorAll('thead th')).toHaveLength(7);
    expect(root.querySelectorAll('tbody tr')).toHaveLength(6);
    expect(root.querySelector('.fauthor')).toBeNull();
  });
});
