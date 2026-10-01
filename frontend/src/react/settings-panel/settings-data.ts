/* 设置面板的三份服务端数据，各一个 Query 键。
 *
 * - `['settings']`：跟账本走、所有访问端同一份的那几项（`/api/settings`，`src/peach/web_settings.py`）。
 *   面板每次打开都重取一次，取回来交给壳对账（`host.syncRemote`）：界面偏好的真相仍是壳里那一份
 *   `appSettings`，这个键只是账本那边的快照。写入同样走这个端点，成功后回来的整份写回这个键。
 * - `['follow-schedule']`：这台机器上关注自动更新的档位与上次运行状态。
 * - `['thumbnail-jobs']`：视频缩略图采集的档位与状态。档位跟着机器走，不存在浏览器里。
 *
 * 面板常驻不卸载，缓存默认挂载不重取（`../query.ts`），所以每次打开面板都由它自己重取一遍。 */
import { useMutation, type QueryClient } from '@tanstack/react-query';

import { apiGet, apiSend } from '../../api';
import { queryClient } from '../query';
import { localTime } from '../time';

export const SETTINGS_URL = '/api/settings';
export const FOLLOW_SCHEDULE_URL = '/api/follow/schedule';
export const THUMBNAIL_JOBS_URL = '/api/thumbnail-jobs';

export const SETTINGS_KEY = ['settings'] as const;
export const FOLLOW_SCHEDULE_KEY = ['follow-schedule'] as const;
export const THUMBNAIL_JOBS_KEY = ['thumbnail-jobs'] as const;

/** `q_settings` 返回的整份；写入时只送改了的那几个键，回来的仍是整份。 */
export interface SyncedSettings {
  sidebarOrder?: string[];
  metadataRefreshDays?: number;
  followInitialDays?: number;
  postSetupTutorialDone?: boolean;
  feedHideGroupCompilations?: boolean;
  feedHideSoloCompilations?: boolean;
  feedHideExcerpts?: boolean;
  /** 账本里还没存过时是 null：这台设备本地那个数替所有访问端先定下来。 */
  searchHistoryLimit?: number | null;
}

export interface FollowScheduleStatus {
  available: boolean;
  enabled: boolean;
  interval_minutes: number;
  running?: boolean;
  last_error?: string | null;
  last_finished_at?: string | null;
  last_added?: number | null;
  next_run_at?: string | null;
}

export interface ThumbnailJobStatus {
  mode: string;
  status: 'idle' | 'running' | 'failed' | 'complete' | string;
  stopped?: string;
}

export const fetchSettings = (signal?: AbortSignal) => apiGet<SyncedSettings>(SETTINGS_URL, signal);
export const fetchFollowSchedule = (signal?: AbortSignal) =>
  apiGet<FollowScheduleStatus>(FOLLOW_SCHEDULE_URL, signal);
export const fetchThumbnailJobs = (signal?: AbortSignal) =>
  apiGet<ThumbnailJobStatus>(THUMBNAIL_JOBS_URL, signal);

/** 打开面板那一下：三份都按服务端此刻的值重取，在途的那一趟直接复用。返回账本那一份，
 *  取不到时是 null——失败由两行机器状态各自显示，账本那份取不到就不对账。 */
export function refreshPanelData(client: QueryClient = queryClient): Promise<SyncedSettings | null> {
  void client.fetchQuery({
    queryKey: FOLLOW_SCHEDULE_KEY, queryFn: ({ signal }) => fetchFollowSchedule(signal), staleTime: 0,
  }).catch(() => null);
  void client.fetchQuery({
    queryKey: THUMBNAIL_JOBS_KEY, queryFn: ({ signal }) => fetchThumbnailJobs(signal), staleTime: 0,
  }).catch(() => null);
  return client.fetchQuery({
    queryKey: SETTINGS_KEY, queryFn: ({ signal }) => fetchSettings(signal), staleTime: 0,
  }).catch(() => null);
}

/** 写跟账本走的那几项。回来的是合并之后的整份，写回 `['settings']`。 */
export function useSaveSettings() {
  return useMutation({
    mutationFn: (patch: SyncedSettings) => apiSend<SyncedSettings>(SETTINGS_URL, patch),
    onSuccess: (saved) => queryClient.setQueryData(SETTINGS_KEY, saved),
  });
}

export function useSaveFollowSchedule() {
  return useMutation({
    mutationFn: (minutes: number) => apiSend<FollowScheduleStatus>(FOLLOW_SCHEDULE_URL,
      { enabled: minutes > 0, interval_minutes: minutes || 60 }),
    onSuccess: (status) => queryClient.setQueryData(FOLLOW_SCHEDULE_KEY, status),
  });
}

export function useSaveThumbnailMode() {
  return useMutation({
    mutationFn: (mode: string) => apiSend<ThumbnailJobStatus>(THUMBNAIL_JOBS_URL, { mode }),
    onSuccess: (status) => queryClient.setQueryData(THUMBNAIL_JOBS_KEY, status),
  });
}

export function followScheduleCopy(status: FollowScheduleStatus): string {
  if (!status.available) return '只在账本写入端运行';
  if (status.running) return '正在检查全部来源…';
  if (status.last_error) return `上次失败：${status.last_error}`;
  if (status.last_finished_at) return `上次完成 ${localTime(status.last_finished_at)} · 新增 ${status.last_added || 0}`;
  if (status.next_run_at) return `下次 ${localTime(status.next_run_at)}`;
  return status.enabled ? '等待首次运行' : '已关闭';
}

export function videoThumbnailCopy(status: ThumbnailJobStatus): string {
  if (status.status === 'running') return '正在采集，进度在活动页查看。';
  if (status.status === 'failed') return `上一轮采集停下了：${status.stopped || '原因未取得'}`;
  if (status.status === 'complete') return status.stopped ? '上一轮采集已按停。' : '上一轮采集已完成。';
  return status.mode === 'off'
    ? '关闭时不采集；已经生成的图留在盘上，清理走数据管理页。'
    : '选定档位后从最近看过的片子开始采集。';
}
