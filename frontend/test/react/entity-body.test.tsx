/* 实体页正文岛：三个视图里各画什么、点下去交给壳的是什么，以及换筛选时骨架与卡片的交接。
 *
 * 名册与卡片本身各有自己的用例（`index-page.test.tsx`、`catalog-grid.test.tsx`），这里只看正文
 * 这一层把谁接到了哪儿。骨架淡出的几何、续页与 Shift 连选由 e2e 在真浏览器里量。 */
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { act, useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { EntityBodyActions, EntityBodyHelpers, EntityBodyProps } from '../../src/react/entity-body/entity-body';
import { EntityBodyPage } from '../../src/react/entity-body/entity-body-page';
import type { MediaItem, MediaPage } from '../../src/react/catalog-grid/types';
import { queryClient } from '../../src/react/query';
import { click, mount } from './render';

afterEach(() => { queryClient.clear() });
notifyManager.setScheduler((notify) => notify());

const item = (id: number): MediaItem => ({ id, name: `作品 ${id}`, has_thumb: true });
const page = (ids: number[], total = ids.length): MediaPage => ({ items: ids.map(item), total });

function helpers(): EntityBodyHelpers {
  return {
    coverHtml: () => '', relayoutArt: vi.fn(), badgeHtml: () => '', titleHtml: (_it, raw) => raw, displayName: (_it, raw) => raw,
    avatarHtml: (name) => name.slice(0, 1), tagLabel: (tag) => tag, wireHover: vi.fn(), releaseHover: vi.fn(),
    personAvatar: vi.fn(() => ({ html: '<span class="ini">A</span>', face: '' })),
  };
}

function actions(): EntityBodyActions {
  return {
    open: vi.fn(), openResource: vi.fn(), openShort: vi.fn(), openShorts: vi.fn(), openMix: vi.fn(),
    openEntity: vi.fn(), openUnowned: vi.fn(), toggleTag: vi.fn(), toggleSelection: vi.fn(),
    watchLater: vi.fn(async () => {}), resourceOperation: vi.fn(async () => {}), mixRelated: vi.fn(async () => []),
    canFlip: () => true,
  };
}

function props(patch: Partial<EntityBodyProps> = {}): EntityBodyProps {
  return {
    kind: 'performer', name: '篠田ゆう', view: 'videos', roster: null, items: page([1, 2, 3]), revision: 1,
    fetchPage: vi.fn(async () => page([])), helpers: helpers(), actions: actions(),
    layout: { active: false, size: 'small', portrait: false, javImage: 'cover' },
    selectMode: false, selected: new Set(), seekSeconds: 10, cache: vi.fn(), wireDrag: vi.fn(),
    skeletonHtml: () => '<div data-test-skeleton>骨架</div>', groupCollapse: true, canLoadMore: () => false,
    ...patch,
  };
}

let push: (patch: Partial<EntityBodyProps>) => void = () => {};
/** 壳经 `updateIsland` 推进来的补丁，这里用一层状态代替。 */
function Shell(given: EntityBodyProps) {
  const [current, set] = useState(given);
  push = (patch) => set((value) => ({ ...value, ...patch }));
  return <EntityBodyPage {...current} />;
}
const open = (given: EntityBodyProps) =>
  mount(<QueryClientProvider client={queryClient}><Shell {...given} /></QueryClientProvider>);

const cards = (host: HTMLElement) =>
  [...host.querySelectorAll<HTMLElement>('[data-entity-grid] [data-media-grid] > [data-media-card]')]
    .map((card) => card.dataset.id);

describe('名册', () => {
  it('事务所页摆索引页那一格艺人，竖幅按检出的脸取景，点一格回壳打开这个人', async () => {
    const given = props({
      kind: 'agency', view: 'people',
      roster: { kind: 'performers', people: [{ k: '河北彩花', n: 12 }, { k: '小湊よつ葉', n: 3 }], layout: 'big' },
      helpers: { ...helpers(), personAvatar: vi.fn(() => ({ html: '<img src="/entity-image?id=1" alt="">', face: '40% 20%' })) },
    });
    const host = await open(given);
    const grid = host.querySelector<HTMLElement>('[data-index-grid]');
    expect(grid?.dataset.cells).toBe('people');
    expect(grid?.dataset.layout).toBe('big');
    const ring = host.querySelector<HTMLElement>('[data-person-ring]');
    expect(ring?.dataset.fitNative).toBe('portrait');
    expect(ring?.style.getPropertyValue('--face')).toBe('40% 20%');
    expect([...host.querySelectorAll('[data-index-cell]')].map((cell) => cell.querySelector('[data-index-readout]')?.textContent))
      .toEqual(['12', '3']);
    await click(host.querySelector('[data-index-cell][data-k="小湊よつ葉"]'));
    expect(given.actions.openEntity).toHaveBeenCalledWith('performer', '小湊よつ葉');
    expect(host.querySelector('[data-entity-grid]')).toBeNull();
  });

  it('片商页的名册是旗下厂牌，一格是公司的方标', async () => {
    const given = props({
      kind: 'studio', view: 'people', roster: { kind: 'studios', people: [{ k: 'S1 NO.1 STYLE', n: 40 }], layout: 'compact' },
    });
    const host = await open(given);
    expect(host.querySelector<HTMLElement>('[data-index-grid]')?.dataset.cells).toBe('company');
    expect(host.querySelector<HTMLElement>('[data-person-ring]')?.dataset.fitNative).toBe('mark');
    expect(given.helpers.personAvatar).toHaveBeenCalledWith(expect.objectContaining({ k: 'S1 NO.1 STYLE' }), 'studio', false);
    await click(host.querySelector('[data-index-cell]'));
    expect(given.actions.openEntity).toHaveBeenCalledWith('studio', 'S1 NO.1 STYLE');
  });
});

describe('作品网格', () => {
  it('第一页由壳给，挂上就是卡片，不再取一遍', async () => {
    const given = props();
    const host = await open(given);
    expect(cards(host)).toEqual(['1', '2', '3']);
    expect(host.querySelector('[data-test-skeleton]')).toBeNull();
    expect(given.fetchPage).not.toHaveBeenCalled();
  });

  it('壳说正在取（items 为 null）就换成骨架，新列表推进来后换成新卡片', async () => {
    const host = await open(props());
    await act(async () => push({ items: null, revision: 2 }));
    expect(cards(host)).toEqual([]);
    expect(host.querySelector('[data-entity-grid] [data-test-skeleton]')).not.toBeNull();
    await act(async () => push({ items: page([7, 8]), revision: 2 }));
    expect(cards(host)).toEqual(['7', '8']);
  });

  it('选择状态与版式原样转给卡片', async () => {
    const host = await open(props());
    await act(async () => push({ selectMode: true, selected: new Set([2]) }));
    expect(host.querySelector('[data-media-sections]')?.hasAttribute('data-select-mode')).toBe(true);
    expect([...host.querySelectorAll<HTMLElement>('[data-media-card][data-selected]')].map((card) => card.dataset.id))
      .toEqual(['2']);
  });
});
