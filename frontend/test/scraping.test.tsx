import { h, render } from 'preact';
import { act } from 'preact/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { Scraping } from '../src/islands/scraping';

const source = { source: 'fc2cmadb', label: 'FC2CMADB', login: 'https://fc2cmadb.com/',
  accepts_cookie: true, network: 'environment', cookie_saved: false, proxy_saved: false };
let host: HTMLDivElement;
afterEach(() => { if (host) render(null, host); document.body.innerHTML = ''; vi.unstubAllGlobals(); });

it('保存后清空秘密输入，状态只表示保存且撤销可操作', async () => {
  const requests: { path: string; body: unknown }[] = [];
  vi.stubGlobal('fetch', vi.fn(async (path: string, init?: RequestInit) => {
    if (init?.method === 'POST') {
      requests.push({ path, body: JSON.parse(String(init.body)) });
      return { ok: true, json: async () => ({ saved: { ...source, cookie_saved: true } }) };
    }
    return { ok: true, json: async () => ({ status: 'idle' }) };
  }));
  host = document.createElement('div'); document.body.append(host);
  const toast = vi.fn();
  await act(async () => render(h(Scraping, { data: { sources: [source] }, error: '', toast }), host));
  const input = host.querySelector<HTMLInputElement>('input[type=password]')!;
  await act(async () => { input.value = 'session=fixture'; input.dispatchEvent(new Event('input', { bubbles: true })); });
  await act(async () => {
    input.closest('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    await new Promise(resolve => setTimeout(resolve, 0));
  });
  expect(requests[0]).toEqual({ path: '/api/scraping/settings', body: {
    source: 'fc2cmadb', network: 'environment', proxy: '', cookie: 'session=fixture', cookies_text: '', revoke: false,
  } });
  expect(host.querySelector<HTMLInputElement>('input[type=password]')!.value).toBe('');
  expect(host.textContent).toContain('登录是否有效请在抓取时确认');
  expect(host.textContent).toContain('撤销 Cookie');
  expect(toast).toHaveBeenCalledWith('来源设置已保存');
});

it('已有后台结果不在首屏冒充新结果', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ status: 'complete', result: 'old result' }) })));
  host = document.createElement('div'); document.body.append(host);
  const toast = vi.fn();
  await act(async () => render(h(Scraping, { data: { sources: [] }, error: '', toast }), host));
  expect(toast).not.toHaveBeenCalled();
  expect(host.textContent).not.toContain('old result');
  expect(host.querySelector('input[required]')).not.toBeNull();
});

it('连接结果用站点名称与共享状态组件呈现', async () => {
  let connected = true;
  vi.stubGlobal('fetch', vi.fn(async (path: string) => ({ ok: true, json: async () =>
    path.endsWith('/check') ? { results: [{ label: '来源页面', ok: connected }] } : { status: 'idle' },
  })));
  host = document.createElement('div'); document.body.append(host);
  await act(async () => render(h(Scraping, { data: { sources: [source] }, error: '', toast: vi.fn() }), host));
  const check = [...host.querySelectorAll('button')].find(button => button.textContent === '检查连接')!;
  await act(async () => { check.click(); await new Promise(resolve => setTimeout(resolve, 0)); });
  expect(host.querySelector('.geist-note-success')?.textContent).toBe('FC2CMADB：可连接');
  connected = false;
  await act(async () => { check.click(); await new Promise(resolve => setTimeout(resolve, 0)); });
  expect(host.querySelector('.geist-note-error')?.textContent).toBe('FC2CMADB：不能连接');
});

it('代理复用重绘下拉，Cookie 二选一且切换后不携带隐藏输入', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ status: 'idle' }) })));
  host = document.createElement('div'); document.body.append(host);
  await act(async () => render(h(Scraping, { data: { sources: [source] }, error: '', toast: vi.fn() }), host));
  expect(host.querySelector('select')).toBeNull();
  expect(host.querySelector('.gselect [aria-haspopup=listbox]')?.textContent).toBe('系统代理');
  expect(host.querySelector('.scraping-url')?.textContent).toBe(source.login);
  expect(host.querySelector('input[type=file]')).toBeNull();
  const input = host.querySelector<HTMLInputElement>('input[type=password]')!;
  await act(async () => { input.value = 'private'; input.dispatchEvent(new Event('input', { bubbles: true })); });
  const choose = (value: string) => host.querySelector<HTMLInputElement>(`input[type=radio][value=${value}]`)!.dispatchEvent(new Event('change', { bubbles: true }));
  await act(async () => { choose('file'); });
  expect(host.querySelector('input[type=password]')).toBeNull();
  expect(host.querySelector('input[type=file]')).not.toBeNull();
  await act(async () => { choose('paste'); });
  expect(host.querySelector<HTMLInputElement>('input[type=password]')!.value).toBe('');
  expect(host.querySelector('.scraping-cover-form')?.children).toHaveLength(2);
});
