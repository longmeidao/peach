import { vi } from 'vitest';

import type { ConfigurationData, ConfigurationProps } from '../src/islands/configuration';

/** 配置页的一份首屏。`islands.test.ts` 拿它当 Preact 档的样本——配置页是仅剩的一个。 */
export const configuration = (
  overrides: Partial<ConfigurationData> = {},
): ConfigurationData => ({
  editable: true, notice: '', revision: 'rev-1', media_dirs: ['D:\\Media'], port: 9123, facts: [],
  ...overrides,
});

/** 遗留层传给 Preact 档的助手。换成可辨认的最小实现，断言只看 island 是否用了它们。 */
export const legacyProps = (): ConfigurationProps => ({ receipt: vi.fn<(message: string) => void>() });

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
