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
    expect([...root.querySelectorAll('.skeleton-segments > span')].map((span) => span.textContent))
      .toEqual(['关注列表', '添加关注', '订阅源', '来源和凭证']);
    expect(root.querySelectorAll('.follow-skeleton-button-group > button')).toHaveLength(2);
    expect(root.querySelector('.follow-skeleton-surface')).not.toBeNull();
    expect(root.querySelectorAll('.follow-skeleton-authors .follow-skeleton-author')).toHaveLength(3);
    expect(root.querySelectorAll('.follow-skeleton-source')).toHaveLength(10);
    expect(root.querySelectorAll('.follow-skeleton-source > *')).toHaveLength(60);
    expect(root.querySelectorAll('.follow-skeleton-select-all button')).toHaveLength(0);
    expect(root.querySelector('.followtoolbaractions')?.lastElementChild?.textContent).toBe('全部收起');
    expect(root.querySelector('.follow-skeleton-footer')).not.toBeNull();
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
    expect(root.querySelector('.follow-skeleton-table')).not.toBeNull();
    expect(root.querySelectorAll('.follow-skeleton-table-row.head > span')).toHaveLength(7);
    expect(root.querySelectorAll('.follow-skeleton-table-row:not(.head)')).toHaveLength(20);
    expect(root.querySelector('.follow-skeleton-author')).toBeNull();
  });
  it('表格骨架的行数跟着每页条数走',()=>{
    localStorage.setItem('peach.settings.v1',JSON.stringify({followPageSize:40}));
    try{
      const root=document.createElement('div');root.innerHTML=boardPageSkeleton('/follow-manage',{followLayout:'table'});
      expect(root.querySelectorAll('.follow-skeleton-table-row:not(.head)')).toHaveLength(40);
    }finally{localStorage.removeItem('peach.settings.v1')}
  });
});
