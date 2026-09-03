import { vi } from 'vitest';

import type { QualityGoalsProps } from '../src/islands/quality-goals';
import { refreshQualityGoals } from '../src/state/quality-goals';
import type { QualityGoal, QualityGoalsData } from '../src/state/quality-goals';

export const goal = (overrides: Partial<QualityGoal> = {}): QualityGoal => ({
  id: 1,
  name: 'one.mp4',
  code: null,
  location: 'local',
  size: 2147483648,
  duration: 3725,
  reason: null,
  cost: 'free',
  has_thumb: true,
  has_cover: false,
  ...overrides,
});

export const payload = (items: QualityGoal[]): QualityGoalsData => ({
  total: items.length,
  items,
  offset: 0,
  has_more: false,
});

/** 遗留层传进来的那几个助手。测试里换成可辨认的最小实现，断言只看 island 是否用了它们。
 *
 * `javTitleHtml` 是 spy：它只在渲染时被调用，所以「组件有没有重画」可以直接数它的调用
 * 次数，不必从 DOM 反推。 */
export const legacyProps = () => {
  const openItem = vi.fn<(id: number) => void>();
  const javTitleHtml = vi.fn<(item: QualityGoal) => string>(
    item => `<strong class="javcode">${item.name}</strong>`,
  );
  const props: QualityGoalsProps = {
    openItem,
    javTitleHtml,
    javDisplayName: item => `名称 ${item.name}`,
    srcBadge: (location, cost) => `<span class="src ${cost}" data-location="${location}"></span>`,
  };
  return { ...props, openItem, javTitleHtml };
};

/** 一次就兑现的 fetch 替身。 */
export const okFetch = (body: unknown) => vi.fn(async (_input: string, _init?: RequestInit) => (
  { ok: true, status: 200, json: async () => body }
));

/** 服务端明确回了非 2xx；`message` 就是界面上该出现的那句话。 */
export const failFetch = (status: number, message: string) => vi.fn(
  async (_input: string, _init?: RequestInit) => (
    { ok: false, status, json: async () => ({ message }) }
  ),
);

/** 把共享 store 灌成「已经读到这些目标」。走 store 自己的写入口，不直接动 signal。 */
export async function seedGoals(items: QualityGoal[]): Promise<void> {
  vi.stubGlobal('fetch', okFetch(payload(items)));
  await refreshQualityGoals();
}

/** 把共享 store 灌成失败态。`refresh` 会重新抛出，这里咽掉：调用点要的是那个状态。 */
export async function seedGoalsError(message: string, status = 500): Promise<void> {
  vi.stubGlobal('fetch', failFetch(status, message));
  try {
    await refreshQualityGoals();
  } catch {
    // 失败已经落进 store，正是这里要的结果。
  }
}

/** 一个可手动兑现的 fetch：island 的等待窗口本身就是被测行为，不能靠 setTimeout 猜。 */
export function deferredFetch(body: unknown) {
  let settle = (): void => {};
  let signal: AbortSignal | undefined;
  const fetched = vi.fn((_input: string, init?: RequestInit) => {
    signal = init?.signal ?? undefined;
    return new Promise<{ ok: boolean; status: number; json(): Promise<unknown> }>((resolve, reject) => {
      settle = () => resolve({ ok: true, status: 200, json: async () => body });
      signal?.addEventListener('abort', () => {
        reject(new DOMException('已中止', 'AbortError'));
      });
    });
  });
  return {
    fetched,
    resolve: () => settle(),
    signal: () => signal,
    install: () => vi.stubGlobal('fetch', fetched),
  };
}
