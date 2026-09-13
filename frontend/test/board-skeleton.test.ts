import { describe, expect, it } from 'vitest';
import { boardPageSkeleton, detailSkeletonHtml } from '../src/board-skeleton';
import { wireBoardSegments } from '../src/board-controls';

describe('Board 页面骨架', () => {
  it.each(['/stats', '/taste', '/follow-manage', '/configuration', '/activity', '/duplicates', '/quality-goals', '/playlists'])('为 %s 提供单一等待语义', path => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton(path);
    expect(root.querySelectorAll('[role="status"]')).toHaveLength(1);
    expect(root.querySelector('[aria-hidden="true"]')).not.toBeNull();
    expect(root.querySelectorAll('button, input, a')).toHaveLength(0);
  });
  it('统计预留四张指标卡，未知页面交给自身骨架', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/stats');
    expect(root.querySelectorAll('.tastesummary')).toHaveLength(4);
    expect(boardPageSkeleton('/item/5')).toBe('');
  });
  it.each([
    ['/stats', '.board-inventory-charts > .board-radial-card', 2],
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
  it('骨架分区不接入交互滑块', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/follow-manage');
    wireBoardSegments(root);
    expect(root.querySelector('.board-segment-thumb')).toBeNull();
    expect(root.querySelector('.skeleton-segment-selected')?.textContent).toBe('关注列表');
    expect(root.querySelectorAll('.skeleton-segments > span')).toHaveLength(3);
  });
  it('口味骨架保留分段背景与状态行间距', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/taste');
    expect(root.querySelector('.insightswitch[data-board-segments]')).not.toBeNull();
    expect(root.querySelector('.skeleton-segment-selected')?.textContent).toBe('浏览器记录');
    expect(root.querySelector('.tastehead + .tastestate + .tastesummaries')).not.toBeNull();
    expect(root.querySelector('.tastehead .skeleton-tabs')).toBeNull();
  });
});
