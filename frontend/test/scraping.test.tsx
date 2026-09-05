import { h, render } from 'preact';
import { act } from 'preact/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { Scraping } from '../src/islands/scraping';

const source = { source: 'fc2cmadb', label: 'FC2 CMADB', login: 'https://fc2cmadb.com/',
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
  expect(host.textContent).toContain('尚未验证会话');
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
