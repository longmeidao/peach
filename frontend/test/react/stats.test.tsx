/* 统计页的行为：一屏读的是不是同一份数、四张卡当页签切到哪一层、几个空态去哪、
 * 点内容标签交回给壳的是哪个键、图表的分档怎么折算。
 *
 * 外观（卡片间距、阴影）是设计决定，由 `frontend/e2e/design.test.ts` 读
 * `getComputedStyle` 断言；这里只看结构、文字与请求。Recharts 在这里量不到容器尺寸，
 * 画不出图形本身，图的读数从图例、页头与纯函数上验。 */
import { act } from 'react';
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { queryClient } from '../../src/react/query';
import {
  lengthRows, mediumRows, prefetchStats, radialBarSize, radialCeiling, replayRows, STATS_URL, watchNote,
  type StatsData,
} from '../../src/react/stats/stats';
import { StatsPage } from '../../src/react/stats/stats-page';

import { buttonNamed, click, mount, mountRoot } from './render';

// 客户端是模块级的单例（所有 React 根共用一个），用例之间不清就互相喂数据。
afterEach(() => queryClient.clear());

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，假时钟推不动它：推完时钟
   断言到的还是上一帧的 DOM。用例里改成当场派发。 */
notifyManager.setScheduler((notify) => notify());

const payload = (overrides: Partial<StatsData> = {}): StatsData => ({
  by_loc: [{ k: 'local', n: 3, bytes: 3221225472, videos: 3 },
    { k: '115', n: 1, bytes: 1073741824, videos: 1 }],
  by_medium: [{ k: 'video', n: 4, bytes: 4294967296 }, { k: 'image', n: 6, bytes: 1048576 }],
  by_library: [{ k: 'main', name: '主库', icon: 'film', videos: 4, bytes: 4294967296 }],
  by_length: [{ k: '速食', n: 1 }, { k: '短', n: 3 }, { k: '中', n: 0 }, { k: '长', n: 0 }],
  by_quality: [{ k: '4K', n: 0 }, { k: '2K', n: 0 }, { k: '1080P', n: 4 }, { k: '720P', n: 0 }, { k: '低画质', n: 0 }],
  play_activity: {
    timezone: 'UTC+08:00',
    days: [{ date: '2026-09-20', count: 1 }, { date: '2026-09-22', count: 1 }],
    hours: [{ weekday: 0, hour: 23, count: 1 }, { weekday: 6, hour: 8, count: 1 }],
  },
  replays: [{ k: 1, n: 1 }, { k: 3, n: 1 }],
  attribution: { videos: 4, creator: 3, code: 2, studio: 1, thumb: 4, duration: 4 },
  tag_source: [{ k: 'javdb', n: 12, assets: 3 }],
  tag_cov: 2,
  top_tags: [{ k: 'tag:a', n: 9, cat: 'genre' }, { k: 'tag:b', n: 4, cat: 'genre' }],
  consumption: {
    played: 2, library_played: 1, online_played: 1, play_seconds: 7200,
    o_total: 5, liked: 1, dislike: 1, seen: 2, trash: 0, skimmed: 1,
  },
  recent: [{
    id: 42, name: 'one.mp4', creator: '甲', play_seconds: 600,
    duration: 1200, max_reached: 0.9, o_count: 0, kind: 'library',
  }],
  storage_volumes: [{
    kind: 'media', label: 'R:', root: 'R:\\media', online: true,
    free: 1073741824, used: 3221225472, total: 4294967296,
  }],
  storage_summary: { volumes: 1, online: 1, measured: 1, free: 1073741824, used: 3221225472, total: 4294967296 },
  ...overrides,
});

/** 遗留层交出来的那几个助手，换成可辨认的最小实现。 */
const legacyProps = () => ({
  tagLabel: (key: string) => `标签 ${key}`,
  onTag: vi.fn<(key: string) => void>(),
  openMediaSettings: vi.fn<() => void>(),
  configurable: true,
});

/** 依次回这几份数据，最后一份之后一直回它。`null` 那一份回 500。 */
function serve(...responses: (StatsData | null)[]) {
  let at = 0;
  const fetcher = vi.fn(async (_input: string, _init?: RequestInit) => {
    const body = responses[Math.min(at, responses.length - 1)] ?? null;
    at += 1;
    return body
      ? { ok: true, status: 200, json: async () => body }
      : { ok: false, status: 500, json: async () => ({ message: '账本当前只能浏览' }) };
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

/** 走完真实的首屏路径：先 prefetch 落进缓存，再挂载。 */
async function open(data: StatsData | null = payload(), props = legacyProps()) {
  const fetcher = serve(data);
  await prefetchStats(new AbortController().signal).catch(() => {});
  const mounted = await mountRoot(
    <QueryClientProvider client={queryClient}><StatsPage {...props} /></QueryClientProvider>);
  return { fetcher, props, ...mounted };
}

const tabNamed = (root: ParentNode, name: string) =>
  [...root.querySelectorAll<HTMLElement>('[role=tab]')].find((tab) => tab.textContent?.includes(name)) ?? null;

it('整页一个请求：四张卡和下面三个面板读的是同一份快照', async () => {
  const { fetcher, host } = await open();
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0]?.[0]).toBe(STATS_URL);
  expect(host.querySelectorAll('[role=tablist]')).toHaveLength(2);
  expect([...host.querySelectorAll('[role=tablist]')[0]!.querySelectorAll('[role=tab]')]
    .map((tab) => tab.querySelector('b')?.textContent))
    .toEqual(['4', '2', '50%', '1 个卷']);
});

it('抬头那一句用遗留层同一套体积口径', async () => {
  const { host } = await open();
  expect(host.querySelector('p')?.textContent).toBe('账本当前快照 · 4 个视频 · 4.0 GB');
});

it('四张卡就是页签：点「看过」换到看过那一层，其余的收起来', async () => {
  const { host } = await open();
  await click(tabNamed(host, '看过'));
  expect(tabNamed(host, '看过')?.getAttribute('aria-selected')).toBe('true');
  expect(tabNamed(host, '馆藏视频')?.getAttribute('aria-selected')).toBe('false');
  const panel = host.querySelector('[role=tabpanel]')!;
  expect(panel.textContent).toContain('个作品有播放记录');
  expect(panel.textContent).toContain('高潮计数');
  expect(panel.textContent).not.toContain('已抽帧');
});

/** 库存那一层的两张径向图：图形那一块以图的标题为名。 */
const radialCharts = (root: ParentNode) =>
  [...root.querySelectorAll<HTMLElement>('[role=tabpanel] div[role=img]')];

it('库存那一层每个来源一圈，图例用来源的界面名称', async () => {
  const { host } = await open();
  const charts = radialCharts(host);
  expect(charts.map((chart) => chart.getAttribute('aria-label'))).toEqual(['网盘与本地', '媒体库']);
  const tiles = [...charts[0]!.closest('section')!.querySelectorAll('button')];
  expect(tiles.map((tile) => tile.querySelector('span')?.textContent)).toEqual(['本地', '115']);
  expect(tiles.map((tile) => tile.querySelector('b')?.textContent)).toEqual(['3', '1']);
});

it('满圈是最长那段的 1.1 倍，圈数越多每圈越细', () => {
  expect(radialCeiling([10, 5])).toBeCloseTo(11);
  expect(radialCeiling([])).toBeCloseTo(1.1);
  expect([2, 12, 40].map(radialBarSize)).toEqual([14, 8, 4]);
});

it('点图例把那一段钉住，读数跟着换；再点一次放开', async () => {
  const { host } = await open();
  const card = radialCharts(host)[0]!.closest('section')!;
  const tile = [...card.querySelectorAll('button')].find((button) => button.textContent?.startsWith('115'))!;
  await click(tile);
  expect(tile.getAttribute('aria-pressed')).toBe('true');
  expect(card.querySelector('h3')?.textContent).toBe('115');
  expect(card.querySelector('header b')?.textContent).toBe('1');
  await click(tile);
  expect(tile.getAttribute('aria-pressed')).toBe('false');
  expect(card.querySelector('h3')?.textContent).toBe('网盘与本地');
});

it('库存那一层按时长、画质、文件类型各出一张分布图，页头读合计', async () => {
  const { host } = await open();
  const panel = host.querySelector('[role=tabpanel]')!;
  const bars = [...panel.querySelectorAll('section[aria-label]')];
  expect(bars.map((bar) => [bar.getAttribute('aria-label'), bar.querySelector('header b')?.textContent]))
    .toEqual([['时长', '4'], ['画质', '4'], ['文件类型', '10']]);
});

it('分布图的分档：时长换成分钟区间，文件类型多的在前，播放次数长尾并档', () => {
  expect(lengthRows([{ k: '速食', n: 1 }, { k: '长', n: 2 }, { k: '超长', n: 3 }]))
    .toEqual([{ name: '5 分钟内', value: 1 }, { name: '40 分钟以上', value: 2 }, { name: '超长', value: 3 }]);
  expect(mediumRows([{ k: 'video', n: 4, bytes: 0 }, { k: 'account', n: 9, bytes: 0 }, { k: 'x', n: 1, bytes: 0 }]))
    .toEqual([{ name: '账号', value: 9 }, { name: '视频', value: 4 }, { name: 'x', value: 1 }]);
  expect(replayRows([{ k: 1, n: 52 }, { k: 2, n: 13 }, { k: 4, n: 6 }, { k: 7, n: 1 }, { k: 9, n: 1 }, { k: 12, n: 2 }]))
    .toEqual([
      { name: '1 次', value: 52 }, { name: '2 次', value: 13 }, { name: '3 次', value: 0 },
      { name: '4 次', value: 6 }, { name: '5 次', value: 0 }, { name: '6–9 次', value: 2 },
      { name: '10 次以上', value: 2 },
    ]);
});

it('看过那一层有播放时间的两张热力图，指到一格读数换成那一格', async () => {
  const { host } = await open();
  await click(tabNamed(host, '看过'));
  const panel = host.querySelector('[role=tabpanel]')!;
  const heats = [...panel.querySelectorAll('svg[role=img]')];
  expect(heats.map((heat) => heat.getAttribute('aria-label'))).toEqual(['播放时间', '每日播放']);
  const card = heats[0]!.closest('section')!;
  expect(card.querySelector('header b')?.textContent).toBe('2');
  expect(card.querySelector('footer')?.textContent).toContain('UTC+08:00');
  const cell = card.querySelector<SVGRectElement>('rect[aria-label="周一 23:00，1 个作品"]')!;
  await act(async () => { cell.dispatchEvent(new FocusEvent('focusin', { bubbles: true })); });
  expect(card.querySelector('header small')?.textContent).toBe('周一 23:00');
  expect(card.querySelector('header b')?.textContent).toBe('1');
  await act(async () => { cell.dispatchEvent(new FocusEvent('focusout', { bubbles: true })); });
  expect(card.querySelector('header b')?.textContent).toBe('2');
  expect(panel.querySelector('section[aria-label="播放次数"] header b')?.textContent).toBe('2');
  const liked = [...panel.querySelectorAll('span')].find((term) => term.textContent === '喜欢');
  expect(liked?.nextElementSibling?.textContent).toBe('1');
});

it('没有播放时间记录时看过那一层不出热力图', async () => {
  const { host } = await open(payload({ play_activity: { timezone: 'UTC+08:00', days: [], hours: [] } }));
  await click(tabNamed(host, '看过'));
  expect(host.querySelector('[role=tabpanel] svg[role=img]')).toBeNull();
});

it('覆盖率那一层的每条进度用同一对分子分母，不另算一遍', async () => {
  const { host } = await open();
  await click(tabNamed(host, '内容标签'));
  const bars = [...host.querySelectorAll('[role=progressbar]')];
  expect(bars.map((bar) => bar.getAttribute('aria-label'))).toEqual([
    '有创作者：3 / 4', '有番号：2 / 4', '有厂牌：1 / 4', '已抽帧：4 / 4', '已探测时长：4 / 4',
  ]);
});

it('取不到容量的卷不画使用率，只说取不到', async () => {
  const { host } = await open(payload({
    storage_volumes: [{ kind: 'media', label: 'B:', root: null, online: true, free: null, used: null, total: null }],
    storage_summary: { volumes: 1, online: 1, measured: 0, free: 0, used: 0, total: 0 },
  }));
  await click(tabNamed(host, '使用空间'));
  const panel = host.querySelectorAll('[role=tabpanel]')[0]!;
  expect(panel.textContent).toContain('容量未取得');
  expect(panel.textContent).toContain('未映射');
  expect(panel.querySelector('[role=progressbar]')).toBeNull();
});

it('排行收起时后两项不可交互，箭头原地展开并能收回', async () => {
  const tags = Array.from({ length: 12 }, (_, index) => ({ k: `tag:${index}`, n: 12 - index, cat: 'genre' }));
  const { host } = await open(payload({ top_tags: tags }));
  const rows = host.querySelectorAll('ol li');
  const expand = host.querySelector<HTMLButtonElement>('button[aria-label="展开更多排名"]');
  expect(rows).toHaveLength(12);
  expect(rows[10]?.hasAttribute('inert')).toBe(true);
  expect(expand?.querySelector('svg')).not.toBeNull();
  expect(expand?.textContent).toBe('');
  await click(expand);
  expect(rows[10]?.hasAttribute('inert')).toBe(false);
  expect(host.querySelector('[data-expandable-ranking]')?.hasAttribute('data-animating')).toBe(true);
  await click(host.querySelector('button[aria-label="收起排名"]'));
  expect(rows[10]?.hasAttribute('inert')).toBe(true);
});

it('点一个内容标签把键交回给壳，页面自己不跳转', async () => {
  const { host, props } = await open();
  await click(host.querySelector('ol li button'));
  expect(props.onTag.mock.calls).toEqual([['tag:a']]);
});

it('快进扫过和正常看完是两回事，一行里分得出来', async () => {
  expect(watchNote({
    id: 1, name: '', creator: null, play_seconds: 100, duration: 1000, max_reached: 0.9, o_count: 0, kind: 'library',
  })).toBe('快进扫过');
  const { host } = await open();
  await click(tabNamed(host, '最近看过'));
  const entry = host.querySelector('[role=tabpanel] article')!;
  expect(entry.querySelector('a')?.getAttribute('href')).toBe('/item/42');
  expect(entry.textContent).toContain('真实 50% · 到达 90%');
});

it('一个视频都没有时给空态，能改配置就给去添加媒体文件夹', async () => {
  const { host, props } = await open(payload({ by_loc: [], by_library: [] }));
  expect(host.querySelector('h3')?.textContent).toBe('还没有视频');
  expect(radialCharts(host)).toEqual([]);
  expect(host.querySelector('[role=tabpanel] section[aria-label]')).toBeNull();
  await click(buttonNamed('添加媒体文件夹', host));
  expect(props.openMediaSettings).toHaveBeenCalledTimes(1);
});

it('这台机器不能改配置时空态不给那个按钮，只留能走的那条路', async () => {
  const props = { ...legacyProps(), configurable: false };
  const { host } = await open(payload({ by_loc: [], by_library: [] }), props);
  expect(buttonNamed('添加媒体文件夹', host)).toBeNull();
  expect(host.querySelector('a')?.textContent).toBe('添加关注');
});

it('首屏取数就失败时只剩一条错误，不画空看板', async () => {
  const { host } = await open(null);
  const alert = host.querySelector('[role=alert]');
  // 文案走遗留层的 `requestErrorMessage`：服务端给了中文原因就用它，页面不另说一遍。
  expect(alert?.textContent).toContain('读取失败');
  expect(alert?.textContent).toContain('账本当前只能浏览');
  expect(host.querySelector('[role=tablist]')).toBeNull();
});

it('重新进这一页会重取：这一页的刷新就是重新进来一次，不吃缓存', async () => {
  const first = await open();
  expect(first.fetcher).toHaveBeenCalledTimes(1);
  await first.unmount();

  // 遗留层再次进入这一页：`mountIsland` 先 prefetch 再挂载。
  await prefetchStats(new AbortController().signal);
  expect(first.fetcher).toHaveBeenCalledTimes(2);
  const host = await mount(
    <QueryClientProvider client={queryClient}><StatsPage {...legacyProps()} /></QueryClientProvider>);
  expect(first.fetcher).toHaveBeenCalledTimes(2);
  expect(host.textContent).toContain('账本当前快照');
});

it('卸载之后不再敲库：这一页没有轮询，也不该留下别的定时器', async () => {
  vi.useFakeTimers();
  const { fetcher, unmount } = await open();
  expect(fetcher).toHaveBeenCalledTimes(1);
  await unmount();
  await vi.advanceTimersByTimeAsync(60_000);
  expect(fetcher, '卸载之后还在取数').toHaveBeenCalledTimes(1);
});
