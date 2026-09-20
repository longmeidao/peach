/* 统计页的行为：一屏读的是不是同一份数、四张卡当页签切到哪一层、几个空态去哪、
 * 点内容标签交回给壳的是哪个键。
 *
 * 外观（环的粗细、卡片间距）是设计决定，由 `frontend/e2e/design.test.ts` 读
 * `getComputedStyle` 断言；这里只看结构、文字与请求。 */
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { queryClient } from '../../src/react/query';
import { prefetchStats, rings, STATS_URL, watchNote, type StatsData } from '../../src/react/stats/stats';
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
  by_library: [{ k: 'main', name: '主库', icon: 'film', videos: 4, bytes: 4294967296 }],
  attribution: { videos: 4, creator: 3, code: 2, studio: 1, thumb: 4, duration: 4 },
  tag_source: [{ k: 'javdb', n: 12, assets: 3 }],
  tag_cov: 2,
  top_tags: [{ k: 'tag:a', n: 9, cat: 'genre' }, { k: 'tag:b', n: 4, cat: 'genre' }],
  consumption: {
    played: 2, library_played: 1, online_played: 1, play_seconds: 7200,
    o_total: 5, dislike: 1, seen: 2, trash: 0, skimmed: 1,
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

it('库存那一层每个来源一段环，读数用来源的界面名称', async () => {
  const { host } = await open();
  const charts = host.querySelectorAll('svg[role=img]');
  expect([...charts].map((chart) => chart.getAttribute('aria-label'))).toEqual(['网盘与本地', '媒体库']);
  expect([...charts[0]!.querySelectorAll('title')].map((node) => node.textContent))
    .toEqual(['本地：3 个视频', '115：1 个视频']);
});

it('环写的是百分比本身：一圈钉成 100，最长那段留一成余量', async () => {
  const geometry = rings([10, 5]);
  expect(geometry[0]!.length).toBeCloseTo(100 / 1.1);
  expect(geometry[1]!.length).toBeCloseTo(50 / 1.1);
  const { host } = await open();
  const value = host.querySelectorAll('svg[role=img]')[0]!.querySelectorAll('circle')[1]!;
  expect(value.getAttribute('pathLength')).toBe('100');
});

it('点图例把那一段钉住，读数跟着换；再点一次放开', async () => {
  const { host } = await open();
  const tile = buttonNamed('115', host) ?? [...host.querySelectorAll('button')]
    .find((button) => button.textContent?.startsWith('115'))!;
  await click(tile);
  expect(tile.getAttribute('aria-pressed')).toBe('true');
  expect(host.querySelector('svg[role=img]')!.closest('section')!.textContent).toContain('115');
  await click(tile);
  expect(tile.getAttribute('aria-pressed')).toBe('false');
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
  expect(host.querySelector('svg[role=img]')).toBeNull();
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
