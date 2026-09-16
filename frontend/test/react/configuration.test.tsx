/* 配置页整页：四个分区怎么排，取不到配置时说什么，以及「一份数据一个读者」。
 *
 * 分区的小标题是遗留壳拆左栏页签的依据（`web/app.js` 的 `configTabItems` 按 `.configgroup`
 * 切后面的兄弟节点），所以这里量的是结构，不是外观。各分区内部的行为在
 * `general-network-settings`、`media-settings`、`maintenance-settings` 几份用例里。 */
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { CONFIGURATION_URL } from '../../src/configuration-endpoints';
import type { ConfigurationData } from '../../src/react/bundle';
import { queryClient } from '../../src/react/query';
import { CONFIGURATION_KEY, prefetchConfiguration } from '../../src/react/settings/configuration';
import { ConfigurationPage } from '../../src/react/settings/configuration-page';

import { buttonNamed, click, mount, section, settle, type } from './render';

// 客户端是模块级的单例（所有 React 根共用一个），用例之间不清就互相喂数据。
afterEach(() => { queryClient.clear() });

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，用例里的等待推不动它：
   断言到的还是上一帧的 DOM。改成当场派发。 */
notifyManager.setScheduler((notify) => notify());

const data = (over: Partial<ConfigurationData> = {}): ConfigurationData => ({
  editable: true, notice: '', revision: 'rev-1', media_dirs: ['D:\\Media'], port: 9123, facts: [], ...over,
});

const startup = {
  available: true, enabled: false, silent: true, message: '', desktop: false, desktop_message: '',
};

/** 除了配置本身，页面上还有按自己节律问的块（播放兼容修复）。按路径应答，别的路径直接空转。 */
function serve(config: ConfigurationData) {
  const calls: string[] = [];
  const fetcher = vi.fn(async (path: string) => {
    calls.push(path);
    if (path === CONFIGURATION_URL) return { ok: true, status: 200, json: async () => config };
    return { ok: true, status: 200, json: async () => ({ status: 'idle' }) };
  });
  vi.stubGlobal('fetch', fetcher);
  return calls;
}

/** 走完真实的首屏路径：先 `prefetch` 把配置落进缓存，再挂页面。 */
async function open(config: ConfigurationData, receipt = vi.fn()) {
  serve(config);
  await prefetchConfiguration(new AbortController().signal);
  const host = await mount(
    <QueryClientProvider client={queryClient}><ConfigurationPage receipt={receipt} /></QueryClientProvider>,
  );
  return host;
}

const groups = (host: ParentNode) => [...host.querySelectorAll('.configgroup')].map((title) => title.textContent);

it('四个分区各有小标题，标题和分区交替排在 `.configpage` 的第一层', async () => {
  const host = await open(data({
    startup, peach_proxy: { mode: 'environment', proxy_saved: false, needs_selection: false },
  }));
  expect(groups(host)).toEqual(['通用', '媒体', '网络与访问', '更新与维护']);
  const page = host.querySelector('.configpage')!;
  expect([...page.children].map((node) => node.classList.contains('configgroup')))
    .toEqual([true, false, true, false, true, false, true, false]);
});

it('没有内容的组连标题一起省略', async () => {
  const host = await open(data());
  expect(groups(host)).toEqual(['媒体', '更新与维护']);
  expect(host.textContent).not.toContain('开机自启');
  expect(host.textContent).not.toContain('Peach 代理');
});

it('取不到配置就说打不开，连同服务端给的那句原因', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: false, status: 503, json: async () => ({ message: '账本正在迁移' }),
  })));
  const host = await mount(
    <QueryClientProvider client={queryClient}><ConfigurationPage receipt={vi.fn()} /></QueryClientProvider>,
  );
  await settle();
  const note = host.querySelector('[role="alert"]');
  expect(note?.textContent).toContain('打不开配置');
  expect(note?.textContent).toContain('账本正在迁移');
  expect(host.querySelector('.configgroup')).toBeNull();
});

/* 刷新挂载状态重取的是整份配置。它换进整页那一个 `queryKey`：屏幕上只有一份真相，
   另存一份的话，挂载点在那一块是新的、在上面那张表单里还是旧的。 */
it('刷新挂载状态换掉整页那一份配置，不动没保存的路径', async () => {
  const offline = { location: '115', path: 'B:/', root: 'B:/', online: false };
  const host = await open(data({ windows: true, media_sources: [offline] }));
  serve(data({ windows: true, media_sources: [{ ...offline, online: true }], revision: 'rev-2' }));

  await type(host.querySelector<HTMLInputElement>('input[aria-label^="媒体文件夹 "]'), 'B:/Movies');
  await click(buttonNamed('刷新挂载状态', host));
  await settle();

  expect(section(host, '挂载状态')?.textContent).toContain('在线');
  expect(host.querySelector<HTMLInputElement>('input[aria-label^="媒体文件夹 "]')?.value).toBe('B:/Movies');
  expect(queryClient.getQueryData<ConfigurationData>(CONFIGURATION_KEY)?.revision).toBe('rev-2');
});
