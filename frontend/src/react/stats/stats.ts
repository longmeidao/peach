/* 统计页的数据契约与折算：`/api/stats` 一次请求供整页使用。
 *
 * 端点在 `frontend/src` 里只在这里声明一次（`tests/test_frontend_build.py` 盯着）。
 * 这一页是账本当前的快照，没有后台任务也不轮询：整页只有一个 `queryKey`，一屏里的四个
 * 指标、下面那三个面板读的都是同一份数，分开取就会出现这一格是新的、那一格是旧的。
 *
 * 体积走 `/js/core.js` 的 `fmtSize`，与馆藏、重复项、高清版同一套口径；播放时长、百分比
 * 与图表的分档是这一页自己的折算，写成纯函数放在这里，由 vitest 直接验。 */
import { apiGet } from '../../api';
import type { BarRow } from '../charts/bar-card';
import type { ActivityCounts } from '../charts/heat';
import { queryClient } from '../query';

export const STATS_URL = '/api/stats';
/** 整页共用这一个键。 */
export const STATS_KEY = ['stats'] as const;

/** 按来源分的库存。`k` 是 `local`／`115`／`pikpak`／`online` 这些来源代号。 */
export interface LocationCount { k: string; n: number; bytes: number; videos: number }

/** 按媒体库分的库存。`name` 是用户给这个库起的名字。 */
export interface LibraryCount { k: string; name: string; icon: string; videos: number; bytes: number }

/** 视频的资料归属：分母是 `videos`，其余几项是已经有那一项的条数。 */
export interface Attribution {
  videos: number; creator: number; code: number; studio: number; thumb: number; duration: number;
}

/** 一个标签来源覆盖了多少条标签、多少个视频。 */
export interface TagSource { k: string; n: number; assets: number }

export interface TopTag { k: string; n: number; cat: string }

export interface Consumption {
  played: number; library_played: number; online_played: number; play_seconds: number;
  o_total: number; liked: number; dislike: number; seen: number; trash: number; skimmed: number;
}

/** 按文件类型分的条目数。`k` 是 `video`／`image`／`archive` 这些媒介代号。 */
export interface MediumCount { k: string; n: number; bytes: number }

/** 视频的一个时长或画质分档。 */
export interface BandCount { k: string; n: number }

/** 播放过 `k` 次的作品有 `n` 个。 */
export interface ReplayCount { k: number; n: number }

/** 最近一条播放记录。馆藏与在线追更两条来源合并后按时间排，`kind` 决定点进去去哪。 */
export interface RecentPlay {
  id: number; name: string; creator: string | null; play_seconds: number;
  duration: number | null; max_reached: number | null; o_count: number; kind: string;
}

/** 一个存储卷。离线或取不到容量时 `total` 是 null，此时不画使用率。 */
export interface StorageVolume {
  kind: string; label: string; root: string | null; online: boolean;
  free: number | null; used: number | null; total: number | null;
}

export interface StorageSummary {
  volumes: number; online: number; measured: number; free: number; used: number; total: number;
}

/** `/api/stats` 的响应。字段与 `web_stats.q_stats` 对齐。 */
export interface StatsData {
  by_loc: LocationCount[];
  by_medium: MediumCount[];
  by_library: LibraryCount[];
  by_length: BandCount[];
  by_quality: BandCount[];
  play_activity: ActivityCounts;
  replays: ReplayCount[];
  attribution: Attribution;
  tag_source: TagSource[];
  tag_cov: number;
  top_tags: TopTag[];
  consumption: Consumption;
  recent: RecentPlay[];
  storage_volumes: StorageVolume[];
  storage_summary: StorageSummary;
}

export const fetchStats = (signal?: AbortSignal) => apiGet<StatsData>(STATS_URL, signal);

/** 首屏：取完数才画。
 *
 * 不给 `staleTime`。这一页读的是账本此刻的样子，每进一次都该重新问一遍；缓存住的话，
 * 扫完一批回来看到的还是进页面之前那个数。 */
export async function prefetchStats(signal: AbortSignal): Promise<void> {
  await queryClient.fetchQuery({ queryKey: STATS_KEY, queryFn: () => fetchStats(signal) });
}

/** 整数百分比。分母是 0 时读 0，不是 NaN。 */
export const percentOf = (value: number, total: number): number =>
  total ? Math.round(value / total * 100) : 0;

/** 累计播放时长：够一小时读小时，不够读分钟。 */
export const playedFor = (seconds: number): string =>
  seconds >= 3600 ? `${(seconds / 3600).toFixed(1)} 小时` : `${Math.round(seconds / 60)} 分钟`;

/** 真实看过的比例：播放秒数占时长，封顶 100%。时长未取得时读 0。 */
export const watchedShare = (row: RecentPlay): number =>
  row.duration ? Math.min(row.play_seconds / row.duration, 1) * 100 : 0;

/** 到达过的最远位置，百分比。 */
export const reachedShare = (row: RecentPlay): number => (row.max_reached || 0) * 100;

/** 这一条读出来是哪一种观看。
 *
 * 真实看过的比例比到达位置低一大截，说明中间大段是拖过去的——那和从头看到尾是两回事，
 * 一行里只显示一个百分比的话读者分不出来。 */
export const watchNote = (row: RecentPlay): string => {
  if (row.kind === 'online') return '在线直接观看';
  if (watchedShare(row) < reachedShare(row) - 25) return '快进扫过';
  return row.o_count ? `高潮 ${row.o_count}` : '正常观看';
};

/** 点进去的去处。在线追更的条目不在馆藏里，走它自己那条详情路由。 */
export const playedItemUrl = (row: RecentPlay): string =>
  `${row.kind === 'online' ? '/follow/item/' : '/item/'}${row.id}`;

/** 径向图里的一段。 */
export interface RadialSlice { name: string; value: number; detail: string }

/** 满圈代表的数：最长那段留一成余量，看得出是「最多」而不是「全部」。 */
export const radialCeiling = (values: number[]): number => Math.max(1, ...values) * 1.1;

/** 每圈的粗细（像素）。段数多时压细，最内圈才不会缩进圆心，也不会和相邻那圈叠在一起。 */
export const radialBarSize = (count: number): number =>
  Math.max(4, Math.min(14, Math.round(90 / Math.max(1, count))));

/** 文件类型的显示名。与馆藏里资源卡片的叫法相同。 */
const MEDIUM_LABEL: Record<string, string> = {
  video: '视频', image: '图片', illustration: '插画', archive: '压缩包',
  audio: '音频', account: '账号', other: '其它文件',
};

/** 按文件类型分的条目数，多的在前。 */
export const mediumRows = (rows: MediumCount[]): BarRow[] =>
  rows.map((row) => ({ name: MEDIUM_LABEL[row.k] ?? row.k, value: row.n }))
    .sort((a, b) => b.value - a.value);

/** 时长分档的显示名。分界同 `media_probe.context_fields`：300、900、2400 秒。 */
const LENGTH_LABEL: Record<string, string> = {
  速食: '<5 分钟', 短: '5–15 分钟', 中: '15–40 分钟', 长: '>40 分钟',
};

/** 时长与画质分档，顺序由服务端给。时长换成分钟区间，画质原样。 */
export const bandRows = (rows: BandCount[], labels: Record<string, string> = {}): BarRow[] =>
  rows.map((row) => ({ name: labels[row.k] ?? row.k, value: row.n }));

export const lengthRows = (rows: BandCount[]): BarRow[] => bandRows(rows, LENGTH_LABEL);

/** 播放次数的分档：五次以内一次一档，往后并成两档，长尾不把柱子拉成一排细线。
 * 名字写短，390 宽的手机上七根柱子的类别名不互相挤掉。 */
const REPLAY_BANDS: readonly [number, number, string][] = [
  [1, 1, '1 次'], [2, 2, '2 次'], [3, 3, '3 次'], [4, 4, '4 次'], [5, 5, '5 次'],
  [6, 9, '6–9 次'], [10, Infinity, '≥10 次'],
];

export const replayRows = (rows: ReplayCount[]): BarRow[] =>
  REPLAY_BANDS.map(([low, high, name]) => ({
    name,
    value: rows.filter((row) => row.k >= low && row.k <= high).reduce((sum, row) => sum + row.n, 0),
  }));
