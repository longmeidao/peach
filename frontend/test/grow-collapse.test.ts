import { afterEach, expect, it, vi } from 'vitest';
// @ts-expect-error 遗留模块由浏览器直接加载，此测试调用实际实现。
import { growCollapse } from '../../web/js/ui-components.js';

afterEach(() => { vi.useRealTimers(); document.body.replaceChildren(); });

it('从起始高度长到内容高度，跑完交回 auto 并装回展开态', () => {
  vi.useFakeTimers();
  const body = document.createElement('div'); body.className = 'fcollapse fcollapse-settled'; document.body.append(body);
  Object.defineProperty(body, 'scrollHeight', { configurable: true, value: 480 });
  growCollapse(body, 120);
  expect(body.classList.contains('fcollapse-settled')).toBe(false);
  expect(body.style.height).toBe('480px');
  body.dispatchEvent(Object.assign(new Event('transitionend'), { propertyName: 'opacity' }));
  expect(body.style.height).toBe('480px');
  vi.advanceTimersByTime(260);
  expect(body.style.height).toBe('auto');
  expect(body.classList.contains('fcollapse-settled')).toBe(true);
});

it('过渡途中又被收起时不收尾', () => {
  vi.useFakeTimers();
  const body = document.createElement('div'); body.className = 'fcollapse'; document.body.append(body);
  let open = true;
  growCollapse(body, 0, () => open);
  open = false; body.style.height = '0px';
  vi.advanceTimersByTime(260);
  expect(body.style.height).toBe('0px');
  expect(body.classList.contains('fcollapse-settled')).toBe(false);
});
