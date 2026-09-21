/* 来源和凭证页的行为：交什么、清什么、结果怎么说、后台那一趟跟到什么时候。
 *
 * 外观（页脚三键的主次、来源外链的 `rel`）是设计决定，由 `frontend/e2e/design.test.ts`
 * 读 `getComputedStyle` 断言；这里只看结构、文字与请求。 */
import { act } from 'react';
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import { queryClient } from '../../src/react/query';
import { ScrapingPage } from '../../src/react/scraping/scraping-page';
import { prefetchScraping } from '../../src/react/scraping/scraping';
import type { Check, CoverJob, Source } from '../../src/react/scraping/scraping';

import { buttonNamed, click, mount, mountRoot, section, settle, submit, type } from './render';

// 客户端是模块级的单例（所有 React 根共用一个），用例之间不清就互相喂数据。
afterEach(() => queryClient.clear());

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，假时钟推不动它：推完时钟
   断言到的还是上一帧的 DOM。用例里改成当场派发。 */
notifyManager.setScheduler((notify) => notify());

const source = (overrides: Partial<Source> = {}): Source => ({
  source: 'fc2cmadb',
  label: 'FC2CMADB',
  login: 'https://fc2cmadb.com/',
  accepts_cookie: true,
  network: 'peach',
  cookie_saved: false,
  ...overrides,
});

interface Reply {
  ok?: boolean;
  status?: number;
  body: unknown;
}

/** 按「方法 + 路径」应答。用例没造的请求当场失败，而不是静悄悄回一个空对象。 */
function serve(handlers: Record<string, (body: never) => Reply>) {
  const calls: { path: string; method: string; body: unknown }[] = [];
  const fetcher = vi.fn(async (path: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ path, method, body });
    const handler = handlers[`${method} ${path}`];
    if (!handler) throw new Error(`用例没有给 ${method} ${path} 造数据`);
    const reply = handler(body as never);
    return { ok: reply.ok !== false, status: reply.status ?? 200, json: async () => reply.body };
  });
  vi.stubGlobal('fetch', fetcher);
  return { calls, fetcher };
}

/** 依次回这几份任务快照，最后一份之后一直回它。 */
function coverStates(...states: CoverJob[]) {
  let at = 0;
  return () => {
    const state = states[Math.min(at, states.length - 1)]!;
    at += 1;
    return { body: state };
  };
}

const page = (toast: (message: string) => void) => (
  <QueryClientProvider client={queryClient}><ScrapingPage toast={toast} /></QueryClientProvider>
);

/** 走完真实的首屏路径：先 prefetch 落进缓存，再挂载。 */
async function open(handlers: Record<string, (body: never) => Reply>) {
  const toast = vi.fn();
  const served = serve(handlers);
  await prefetchScraping(new AbortController().signal).catch(() => {});
  return { ...served, toast, host: await mount(page(toast)) };
}

/** 一份只有一个来源、后台没有任务的首屏。 */
const quiet = (overrides: Partial<Source> = {}) => ({
  'GET /api/scraping': () => ({ body: { sources: [source(overrides)] } }),
  'GET /api/scraping/cover': () => ({ body: { status: 'idle' } }),
});

const password = (root: ParentNode) => root.querySelector<HTMLInputElement>('input[type=password]');
const radio = (value: string) => document.querySelector<HTMLInputElement>(`input[type=radio][value="${value}"]`);
/** 轮询是组件里的定时器，推进时钟会引起重画，得在 act 里推。 */
const tick = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms) });

it('首屏用 prefetch 落进缓存的两份画出来，挂载时不再请求一次', async () => {
  const { calls, host } = await open(quiet());
  expect(calls.map((call) => call.path))
    .toEqual(['/api/scraping', '/api/scraping/cover']);
  expect(section(host, 'FC2CMADB')).not.toBeNull();
  expect(section(host, '高清封面')).not.toBeNull();
  // 连接方式是 BoardUI 的 Select，画出来的是按钮；原生 select 是 React Aria 藏在后面
  // 供表单取值的那一个，不是这一行的长相。
  expect(host.querySelector('[aria-haspopup=listbox]')?.textContent?.trim()).toBe('Peach 代理');
  expect(host.querySelector<HTMLAnchorElement>('a[href="/configuration#peachProxy"]')?.textContent)
    .toContain('配置 Peach 代理');
  expect(host.querySelector<HTMLAnchorElement>('a[href="https://fc2cmadb.com/"]')?.target).toBe('_blank');
});

it('保存后清空秘密输入，列表就地换成服务端回的那一条，撤销随之可操作', async () => {
  const { calls, host, toast } = await open({
    ...quiet(),
    'POST /api/scraping/settings': () => ({ body: { saved: source({ cookie_saved: true }) } }),
  });
  await type(password(host), 'session=fixture');
  await submit(section(host, 'FC2CMADB'));
  await settle();

  expect(calls[2]).toEqual({
    path: '/api/scraping/settings',
    method: 'POST',
    body: {
      source: 'fc2cmadb', network: 'peach', cookie: 'session=fixture', cookies_text: '', revoke: false,
    },
  });
  expect(password(host)?.value, '保存回来之后页面上不再留着刚交上去的那一份').toBe('');
  expect(host.textContent).toContain('登录是否有效要到抓取时才知道');
  expect(buttonNamed('撤销 Cookie', host)).not.toBeNull();
  expect(toast).toHaveBeenCalledWith('来源设置已保存');
  expect(calls.filter((call) => call.path === '/api/scraping' && call.method === 'GET'),
    '保存换的是列表里的一条，不为它把整页重取一遍').toHaveLength(1);
});

it('撤销走同一条写入，回执说的是撤销', async () => {
  const { calls, host, toast } = await open({
    ...quiet({ cookie_saved: true }),
    'POST /api/scraping/settings': () => ({ body: { saved: source({ cookie_saved: false }) } }),
  });
  await click(buttonNamed('撤销 Cookie', host));
  await settle();
  expect(calls[2]?.body).toMatchObject({ source: 'fc2cmadb', revoke: true });
  expect(toast).toHaveBeenCalledWith('Cookie 已撤销');
  expect(buttonNamed('撤销 Cookie', host), '撤销之后这颗键没有对象可撤了').toBeNull();
});

it('保存失败时原因留在卡内，列表和刚填的内容都不动', async () => {
  const { host, toast } = await open({
    ...quiet(),
    'POST /api/scraping/settings': () => ({ ok: false, status: 400, body: { message: 'Cookie 不是 Netscape 格式' } }),
  });
  await type(password(host), 'session=fixture');
  await submit(section(host, 'FC2CMADB'));
  await settle();

  expect(host.querySelector('[role=alert]')?.textContent).toContain('Cookie 不是 Netscape 格式');
  expect(password(host)?.value, '失败了还清空输入，等于让人重打一遍').toBe('session=fixture');
  expect(buttonNamed('撤销 Cookie', host)).toBeNull();
  expect(toast).not.toHaveBeenCalled();
});

it('连接结果按来源名称与这一跳查的是什么说成一句话', async () => {
  const results: Check[] = [
    { label: '来源页面', ok: true, width: 800, height: 538 },
    { label: '高清图片 CDN', ok: false, status: 403, message: '需要登录' },
  ];
  const { host } = await open({
    ...quiet(),
    'POST /api/scraping/check': () => ({ body: { results } }),
  });
  await click(buttonNamed('检查连接', host));
  await settle();

  expect(host.querySelector('[role=status]')?.textContent).toBe('FC2CMADB：可连接 · 800 × 538');
  expect(host.querySelector('[role=alert]')?.textContent).toBe('FC2CMADB 高清图片：不能连接。需要登录');
});

it('Cookie 二选一：切过去的那一种才交，另一种连输入都不留', async () => {
  const { calls, host } = await open({
    ...quiet(),
    'POST /api/scraping/settings': () => ({ body: { saved: source() } }),
  });
  expect(host.querySelector('input[type=file]')).toBeNull();
  await type(password(host), 'private');
  await click(radio('file'));
  expect(password(host), '粘贴框还在页面上就会跟着提交').toBeNull();
  expect(host.querySelector('input[type=file]')).not.toBeNull();
  expect(host.textContent).toContain('未选择文件');

  await submit(section(host, 'FC2CMADB'));
  await settle();
  expect(calls[2]?.body).toMatchObject({ cookie: '', cookies_text: '' });

  await click(radio('paste'));
  expect(password(host)?.value).toBe('');
});

it('Cookie 文件超过上限时当场拦住，不拿它去占一次请求', async () => {
  const { calls, host } = await open(quiet());
  await click(radio('file'));
  const input = host.querySelector<HTMLInputElement>('input[type=file]')!;
  const oversized = new File(['x'.repeat(256 * 1024 + 1)], 'cookies.txt', { type: 'text/plain' });
  Object.defineProperty(input, 'files', { configurable: true, value: [oversized] });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })) });
  await settle();

  expect(host.querySelector('[role=alert]')?.textContent).toBe('Cookie 文本超过 256 KiB');
  expect(host.textContent).toContain('未选择文件');
  expect(calls).toHaveLength(2);
});

it('首屏读到的旧结果不冒充新结果：不画、也不发回执', async () => {
  const { host, toast } = await open({
    ...quiet(),
    'GET /api/scraping/cover': () => ({ body: { status: 'complete', result: '上一趟的封面' } }),
  });
  expect(toast).not.toHaveBeenCalled();
  expect(host.textContent).not.toContain('上一趟的封面');
  expect(host.textContent).not.toContain('正在抓取封面');
});

it('抓封面跟到终态：跑的时候两秒一次，跑完发一次回执就不再问', async () => {
  vi.useFakeTimers();
  const toast = vi.fn();
  const { calls } = serve({
    ...quiet(),
    'GET /api/scraping/cover': coverStates(
      { status: 'idle' }, { status: 'running' }, { status: 'complete', result: '已取得 1600 × 1077 封面' }),
    'POST /api/scraping/cover': () => ({ body: { status: 'running' } }),
  });
  await prefetchScraping(new AbortController().signal);
  const host = await mount(page(toast));

  await type(host.querySelector<HTMLInputElement>('input[aria-label=馆藏番号]'), 'ABW-232');
  await click(buttonNamed('抓取封面', host));
  await settle();
  expect(calls[2]).toMatchObject({ path: '/api/scraping/cover', method: 'POST', body: { code: 'ABW-232' } });
  expect(host.textContent).toContain('正在抓取封面');

  await tick(2000);
  expect(host.textContent).toContain('已取得 1600 × 1077 封面');
  expect(host.textContent).not.toContain('正在抓取封面');
  expect(toast).toHaveBeenCalledTimes(1);
  expect(toast).toHaveBeenCalledWith('已取得 1600 × 1077 封面');

  const asked = calls.length;
  await tick(60_000);
  expect(calls.length, '任务已经结束，不必接着敲后台').toBe(asked);
  expect(toast).toHaveBeenCalledTimes(1);
});

it('卸载之后不再敲后台：轮询跟着这棵根一起走', async () => {
  vi.useFakeTimers();
  const { calls } = serve({
    ...quiet(),
    'GET /api/scraping/cover': () => ({ body: { status: 'running' } }),
  });
  await prefetchScraping(new AbortController().signal);
  const mounted = await mountRoot(page(vi.fn()));

  await tick(2000);
  const asked = calls.length;
  expect(asked).toBeGreaterThan(2);
  await mounted.unmount();
  await tick(60_000);
  expect(calls.length, '卸载之后还在轮询').toBe(asked);
});
