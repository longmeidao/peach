/* 来源可达性。数据管理页要知道这次会扫哪几个来源、资源同步那一块出不出现，重复文件页要知道
 * 哪些网盘值得给一颗「优先保留」——同一份真相三个读者，所以一个 `queryKey`，端点也只在这里
 * 声明一次。
 *
 * 这一份没有节律：它是进页面那一刻的挂载情况，后台不推进它，所以不轮询。 */
import { apiGet } from '../api';
import { queryClient } from './query';

export const MEDIA_SOURCES_URL = '/api/sources';
export const MEDIA_SOURCES_KEY = ['media-sources'] as const;

/** `/api/sources` 的一行。字段与 `routes_api.source_health` 对齐。 */
export interface MediaSourceStatus {
  location: string;
  online: boolean;
  roots?: unknown[];
}

export interface MediaSourcesData {
  sources: MediaSourceStatus[];
}

export const fetchMediaSources = (signal?: AbortSignal) =>
  apiGet<MediaSourcesData>(MEDIA_SOURCES_URL, signal);

export async function prefetchMediaSources(signal: AbortSignal): Promise<void> {
  await queryClient.fetchQuery({ queryKey: MEDIA_SOURCES_KEY, queryFn: () => fetchMediaSources(signal) });
}

/** 落盘的三种存储来源。`online` 这类在线来源不落盘，不参与扫描与对账。 */
export const SCANNABLE_LOCATIONS = ['local', '115', 'pikpak'];

export const scannableSources = (data: MediaSourcesData | undefined): MediaSourceStatus[] =>
  (data?.sources ?? []).filter((source) => SCANNABLE_LOCATIONS.includes(source.location));

/** 配了根目录的网盘。离线的网盘仍然属于已配置来源：它上面的重复副本照样能挑着留。 */
export const cloudLocations = (data: MediaSourcesData | undefined): string[] =>
  (data?.sources ?? []).filter((source) => ['115', 'pikpak'].includes(source.location)
    && (source.roots === undefined || source.roots.length > 0)).map((source) => source.location);
