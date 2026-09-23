/* 设置弹层「这台电脑」那一格的摘要卡：只读三项读数，编辑都去配置页。 */
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { CONFIGURATION_URL } from '../../src/configuration-endpoints';
import type { ConfigurationData, ReleaseState } from '../../src/react/bundle';
import { queryClient } from '../../src/react/query';
import { prefetchConfiguration } from '../../src/react/settings/configuration';
import { ConfigurationSummary } from '../../src/react/settings/configuration-summary';
import { buttonNamed, click, mount } from './render';

afterEach(() => { queryClient.clear() });
notifyManager.setScheduler((notify) => notify());

const release: ReleaseState = {
  current_version: '0.9.0', latest_version: null, channel: '测试版', installation: '独立测试包',
  state: 'unchecked', message: '尚未检查', release_url: 'https://github.com/longmeidao/peach/releases',
};

const data = (over: Partial<ConfigurationData> = {}): ConfigurationData => ({
  editable: true, notice: '', revision: 'r', media_dirs: [], port: 9123, facts: [], ...over,
});

async function open(config: ConfigurationData, openConfiguration = vi.fn()) {
  const fetcher = vi.fn(async (path: string) => ({ ok: true, status: 200, json: async () => (path === CONFIGURATION_URL ? config : {}) }));
  vi.stubGlobal('fetch', fetcher);
  await prefetchConfiguration(new AbortController().signal);
  const host = await mount(
    <QueryClientProvider client={queryClient}><ConfigurationSummary openConfiguration={openConfiguration} /></QueryClientProvider>,
  );
  return { host, fetcher };
}

const facts = (host: ParentNode) =>
  [...host.querySelectorAll('dt')].map((dt) => [dt.textContent, dt.nextElementSibling?.textContent]);

it('三行读数：同名文件夹算一个媒体库，端口，当前版本连同检查结果', async () => {
  const { host } = await open(data({
    updates: release,
    media_sources: [
      { location: 'R:', root: 'R:\\Media', path: 'R:\\Media\\a', library: '网盘' },
      { location: 'R:', root: 'R:\\Media', path: 'R:\\Media\\b', library: '网盘' },
      { location: 'D:', root: 'D:\\Local', path: 'D:\\Local' },
    ],
  }));
  expect(facts(host)).toEqual([['媒体库', '2 个'], ['端口', '9123'], ['更新', '0.9.0 · 尚未检查']]);
});

it('摘要卡里没有可编辑的控件，只有一颗去配置页的按钮', async () => {
  const openConfiguration = vi.fn();
  const { host, fetcher } = await open(data(), openConfiguration);
  expect(host.querySelectorAll('input, textarea, select, [role="switch"], [aria-haspopup="listbox"]')).toHaveLength(0);
  expect([...host.querySelectorAll('button')].map((button) => button.textContent)).toEqual(['打开配置页']);
  expect(facts(host).at(-1)).toEqual(['更新', '未取得']);
  await click(buttonNamed('打开配置页', host));
  expect(openConfiguration).toHaveBeenCalledTimes(1);
  expect(fetcher).toHaveBeenCalledTimes(1);
});

it('读不到配置时说打不开，按钮照样能去配置页', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 503, json: async () => ({ message: '账本正在迁移' }) })));
  await prefetchConfiguration(new AbortController().signal).catch(() => undefined);
  const host = await mount(
    <QueryClientProvider client={queryClient}><ConfigurationSummary openConfiguration={vi.fn()} /></QueryClientProvider>,
  );
  expect(host.textContent).toContain('打不开配置');
  expect(buttonNamed('打开配置页', host)).not.toBeNull();
});
