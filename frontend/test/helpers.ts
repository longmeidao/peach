import { vi } from 'vitest';

import type { QualityGoal, QualityGoalsData, QualityGoalsProps } from '../src/islands/quality-goals';

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

/** 遗留层传进来的那几个助手。测试里换成可辨认的最小实现，断言只看 island 是否用了它们。 */
export const legacyProps = () => {
  const openItem = vi.fn<(id: number) => void>();
  const props: QualityGoalsProps = {
    openItem,
    javTitleHtml: item => `<strong class="javcode">${item.name}</strong>`,
    javDisplayName: item => `名称 ${item.name}`,
    srcBadge: (location, cost) => `<span class="src ${cost}" data-location="${location}"></span>`,
  };
  return { ...props, openItem };
};

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
