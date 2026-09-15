import { render } from 'preact';
import { afterEach, expect, it, vi } from 'vitest';

import { CONFIGURATION_URL } from '../src/configuration-endpoints';
import { Configuration, loadConfiguration } from '../src/islands/configuration';
import type { ConfigurationData } from '../src/islands/configuration';

// 分区本身由 `test/react/` 的用例覆盖；这里只看外壳把哪一组交给哪个挂载点。
vi.mock('../src/react-slot', () => ({
  ReactSlot: ({ mount }: { mount: string }) => <div data-slot={mount} />,
}));

const data = (over: Partial<ConfigurationData> = {}): ConfigurationData => ({
  editable: true, notice: '', revision: 'rev-1', media_dirs: ['D:\\Media'], port: 9123, facts: [], ...over,
});

afterEach(() => {
  for (const el of [...document.body.children]) render(null, el);
  document.body.innerHTML = '';
  vi.unstubAllGlobals();
});

const draw = (state: { data: ConfigurationData | null; error?: string }) => {
  const el = document.createElement('div');
  document.body.append(el);
  render(<Configuration receipt={vi.fn()} data={state.data} error={state.error ?? ''} />, el);
  return el;
};
const groups = (el: Element) => [...el.querySelectorAll('.configgroup')]
  .map((title) => [title.textContent, title.nextElementSibling?.getAttribute('data-slot')]);

it('每组小标题后面紧跟它的分区，没有内容的组连标题一起省略', () => {
  const startup = { available: true, enabled: false, silent: true, message: '', desktop: false, desktop_message: '' };
  const full = draw({ data: data({ startup, peach_proxy: { mode: 'direct', proxy_saved: false, needs_selection: false } }) });
  expect(groups(full)).toEqual([
    ['通用', 'mountGeneralSettings'],
    ['媒体', 'mountMediaSettings'],
    ['网络与访问', 'mountNetworkSettings'],
    ['更新与维护', 'mountMaintenanceSettings'],
  ]);
  const access = draw({ data: data({ access: { mode: 'open', revision: 'r' } }) });
  expect(groups(access).map(([title]) => title)).toEqual(['媒体', '网络与访问', '更新与维护']);
  const readonly = draw({ data: data({ editable: false }) });
  expect(groups(readonly).map(([title]) => title)).toEqual(['媒体', '更新与维护']);
});

it('首屏走 /api/configuration 并带上中止信号', async () => {
  const fetch = vi.fn(async (_url: string, _init: RequestInit) => ({ ok: true, status: 200, json: async () => data() }));
  vi.stubGlobal('fetch', fetch);
  const controller = new AbortController();
  await loadConfiguration({ receipt: vi.fn() }, controller.signal);
  const [url, init] = fetch.mock.calls[0] ?? [];
  expect(url).toBe(CONFIGURATION_URL);
  expect(init?.signal).toBe(controller.signal);
});

it('首屏取数失败时画原因', () => {
  const el = draw({ data: null, error: '请先完成首次设置' });
  expect(el.querySelector('.geist-note-error')?.textContent).toContain('请先完成首次设置');
  expect(el.querySelector('.configgroup')).toBeNull();
});
