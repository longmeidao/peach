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
    ['/follow-manage', '.peach-react .follow-skeleton-surface .follow-skeleton-author', 3],
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
  const follow = (options: Parameters<typeof boardPageSkeleton>[1] = {}) => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/follow-manage', options);
    return root;
  };
  it('关注骨架的工作区切换是 React 那条分段轨道，选中关注列表', () => {
    const root = follow();
    wireBoardSegments(root);
    expect(root.querySelector('.board-segment-thumb')).toBeNull();
    expect(root.querySelector('.peach-react [data-selected]')?.textContent).toBe('关注列表');
    const track = root.querySelector('.peach-react [data-selected]')!.parentElement!;
    expect([...track.children].map((span) => span.textContent)).toEqual(['关注列表', '添加关注', '订阅源', '来源和凭证']);
  });
  it('关注骨架的工具行按 Board UI 最终变体画：检查全部是主按钮，视图切换是按版式选中的按钮组', () => {
    const toolbar = follow().querySelector('.follow-skeleton-toolbar')!;
    const check = toolbar.querySelector(':scope > button')!;
    expect(check.textContent).toBe('检查全部');
    expect(check.classList.contains('bg-button-primary')).toBe(true);
    const group = [...toolbar.querySelectorAll('[data-button-group][role="group"] > button')];
    expect(group.map((button) => button.querySelector('use')?.getAttribute('href'))).toEqual(['#i-layout-grid', '#i-table']);
    expect(group.map((button) => button.getAttribute('aria-pressed'))).toEqual(['true', 'false']);
    expect(group.every((button) => button.classList.contains('bg-button-ghost-background'))).toBe(true);
    expect(toolbar.querySelector('button[aria-haspopup="listbox"]')?.textContent).toBe('检查时间');
    expect(toolbar.lastElementChild?.textContent).toBe('全部收起');
    const tableGroup = follow({ followLayout: 'table' }).querySelectorAll('[data-button-group] > button');
    expect([...tableGroup].map((button) => button.getAttribute('aria-pressed'))).toEqual(['false', 'true']);
  });
  it('排序框与方向键跟着地址栏上的排序', () => {
    const toolbar = (options: Parameters<typeof boardPageSkeleton>[1]) =>
      follow(options).querySelector('.follow-skeleton-toolbar')!;
    const arrow = (root: Element) => root.querySelector('button[aria-haspopup]')!.parentElement!
      .nextElementSibling!.querySelector('use')?.getAttribute('href');
    expect(arrow(toolbar({}))).toBe('#i-arrow-down');
    const byName = toolbar({ followSort: 'name' });
    expect(byName.querySelector('button[aria-haspopup]')?.textContent).toBe('创作者名称');
    expect(arrow(byName)).toBe('#i-arrow-up');
    expect(arrow(toolbar({ followSort: 'name', followDir: 'desc' }))).toBe('#i-arrow-down');
  });
  it('创作者卡与来源行的动作键是小号次级键，和最终行内操作同一形态', () => {
    const root = follow();
    expect(root.querySelectorAll('.follow-skeleton-source')).toHaveLength(10);
    for (const row of root.querySelectorAll('.follow-skeleton-source')) {
      const actions = [...row.lastElementChild!.children];
      expect(actions.map((button) => button.querySelector('use')?.getAttribute('href'))).toEqual(['#i-refresh-cw', '#i-trash']);
      for (const button of actions) expect(button.className).toContain('size-8 rounded-lg p-0');
    }
    const head = root.querySelector('.follow-skeleton-author [data-follow-author-header]')!;
    expect([...head.querySelectorAll(':scope > button')].map((button) => button.textContent)).toEqual(['', '全选', '收起']);
    expect(root.querySelector('.follow-skeleton-surface > .group')?.textContent).toBe('全选本页');
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
  it('关注表格视图是 Board UI 表格外框，当前排序那一列带方向', () => {
    const root = follow({ followLayout: 'table' });
    const table = root.querySelector('.follow-skeleton-table[data-board-data-table] table.bui-table')!;
    expect([...table.querySelectorAll('thead th')].map((th) => th.textContent)).toEqual(['', '创作者', '来源', '站点', '状态', '上次检查', '']);
    expect(table.querySelectorAll('tbody tr')).toHaveLength(20);
    expect([...table.querySelectorAll('[data-sort-indicator][data-direction]')].map((mark) => [mark.parentElement!.textContent, mark.getAttribute('data-direction')]))
      .toEqual([['上次检查', 'descending']]);
    expect(root.querySelector('.follow-skeleton-author')).toBeNull();
    expect(root.querySelector('.follow-skeleton-toolbar')?.textContent).not.toContain('全部收起');
  });
  it('表格骨架的行数跟着每页条数走', () => {
    localStorage.setItem('peach.settings.v1', JSON.stringify({ followPageSize: 40 }));
    try {
      const root = follow({ followLayout: 'table' });
      expect(root.querySelectorAll('.follow-skeleton-table tbody tr')).toHaveLength(40);
      expect(root.querySelector('.follow-skeleton-surface > :last-child button[aria-haspopup]')?.textContent).toBe('每页 40 条');
    } finally { localStorage.removeItem('peach.settings.v1') }
  });
});
