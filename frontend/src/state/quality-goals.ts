/* 共享状态：高清版目标（`/api/quality-goals`）。
 *
 * 这份数据在界面上有两个读者，而且是两个不同的表面：
 *
 * - `/quality-goals` 整页列表（已迁成 island），要 `items`；
 * - `/data-cleanup` 数据管理页上的「高清版」卡片（`N 个待升级`），只要一个 `total`，
 *   为此单独发了 `/api/quality-goals?limit=1`。
 *
 * 同一个真相取两次，谁先谁后不定，两处显示的数就可能不一致。所以它归这里：一份
 * 数据只有一个家，读者订阅同一个 signal，取数由下面这几个函数发起。数据管理页还在
 * `web/app.js` 里，它接进来的方式是 `refreshStore()`（见 `./index.ts`），本轮不动它。
 *
 * 写入口只有 `refresh` / `ensure` / `reset` 三个。可写的 signal 不导出：组件拿到的是
 * `computed` 视图，直接赋值在运行期就抛 TypeError，不是靠约定。 */
import { computed, signal } from '@preact/signals';
import type { ReadonlySignal } from '@preact/signals';

import { apiGet, errorMessage } from '../api';

/** `/api/quality-goals` 的单条目。字段与 `web_contract.q_quality_goals` 对齐。 */
export interface QualityGoal {
  id: number;
  name: string;
  code: string | null;
  location: string;
  size: number | null;
  duration: number | null;
  reason: string | null;
  cost: string;
  has_thumb: boolean;
  has_cover: boolean;
}

export interface QualityGoalsData {
  total: number;
  items: QualityGoal[];
  offset: number;
  has_more: boolean;
}

/** `data` 与 `error` 恰有一个成立，和 island 首屏状态同一口径。 */
export interface QualityGoalsState {
  data: QualityGoalsData | null;
  error: string;
}

/** 上限沿用遗留层的 200：服务端 `limit` 也钉在 200，再大只会被截。 */
export const QUALITY_GOALS_URL = '/api/quality-goals?limit=200';

const BLANK: QualityGoalsState = { data: null, error: '' };

const state = signal<QualityGoalsState>(BLANK);

/** 每次写入带一个序号：迟到的响应不许盖住比它更新的那一次。 */
let issued = 0;
/** `ensure` 的合流点。多个岛同时挂载时只发一个请求，而不是各发一个。 */
let shared: Promise<QualityGoalsData> | null = null;

/** 当前的读取结果。组件读它就自动订阅，数据变了自己重画，不必重新挂载。 */
export const qualityGoals: ReadonlySignal<QualityGoalsState> = computed(() => state.value);

/** 待升级总数；还没读到过是 `null`——那和「读到 0 个」是两件事，不能都显示成 0。 */
export const qualityGoalsTotal: ReadonlySignal<number | null> = computed(
  () => state.value.data?.total ?? null,
);

/** 丢掉已读到的一切，下一次 `ensure` 会重新取。测试之间用它隔离，遗留层不用。 */
export function resetQualityGoals(): void {
  issued += 1;
  shared = null;
  state.value = BLANK;
}

/** 强制重取一次。
 *
 * island 的首屏走这里而不是 `ensure`：`/quality-goals` 在路由表里是 `refresh:'reopen'`，
 * 刷新就是重新进这一页，那时候要的是新数据，不是缓存。
 *
 * `abort` 归调用方所有（`mountIsland` 在卸载时中止它）。中止不写错误态：页面是被用户
 * 换掉的，屏幕上那份数据仍然有效，标成失败反而是谎报。 */
export async function refreshQualityGoals(abort?: AbortSignal): Promise<QualityGoalsData> {
  const token = (issued += 1);
  try {
    const data = await apiGet<QualityGoalsData>(QUALITY_GOALS_URL, abort);
    if (token === issued) state.value = { data, error: '' };
    return data;
  } catch (cause) {
    if (!abort?.aborted && token === issued) {
      state.value = { data: null, error: errorMessage(cause) };
    }
    throw cause;
  }
}

/** 读一次就够的读者走这里：已经有数据就直接给，没有才取。
 *
 * 不收 `AbortSignal`：这个请求归 store，不归第一个碰上它的调用方。让 A 的离场中止掉
 * B 也在等的那个请求，是把「共用」变成「谁先来谁负责」。 */
export async function ensureQualityGoals(): Promise<QualityGoalsData> {
  const cached = state.value.data;
  if (cached) return cached;
  if (!shared) {
    shared = refreshQualityGoals().finally(() => { shared = null; });
  }
  return shared;
}
