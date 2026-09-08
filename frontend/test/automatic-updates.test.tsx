import { render } from 'preact';
import { act } from 'preact/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import { AutomaticUpdateSettings } from '../src/islands/automatic-updates';

// @ts-expect-error 遗留组件使用正式实现验证控件。
vi.mock('@peach/legacy/ui', () => import('../../web/js/ui-components.js'));
const host = document.createElement('div');
afterEach(() => { render(null, host); host.remove(); vi.unstubAllGlobals(); });
const initial = {mode:'off',interval_hours:24,available:true,download_available:true};

it('开关互相约束，保存服务端成功后才回执，关闭可持久保存', async () => {
  const receipt = vi.fn();
  const fetch = vi.fn(async (_url: string, _init: RequestInit) => ({ok:true,status:200,json:async () => initial}));
  vi.stubGlobal('fetch', fetch); document.body.append(host);
  await act(() => render(<AutomaticUpdateSettings initial={initial} receipt={receipt} />,host));
  const controls = host.querySelectorAll<HTMLInputElement>('[role="switch"]');
  expect(controls[1]!.disabled).toBe(true);
  await act(() => controls[0]!.click());
  expect(controls[1]!.disabled).toBe(false);
  await act(() => controls[1]!.click());
  await act(() => host.querySelector('form')!.requestSubmit());
  expect(JSON.parse(fetch.mock.calls[0]![1].body as string)).toEqual({mode:'download',interval_hours:24});
  await vi.waitFor(() => expect(receipt).toHaveBeenCalledWith('已保存自动更新设置'));
  await act(() => controls[0]!.click());
  await act(() => host.querySelector('form')!.requestSubmit());
  expect(JSON.parse(fetch.mock.calls[1]![1].body as string).mode).toBe('off');
  await vi.waitFor(() => expect(receipt).toHaveBeenCalledTimes(2));
});

it('源码运行禁用自动下载，失败原因留在表单且不报成功', async () => {
  const receipt = vi.fn();
  vi.stubGlobal('fetch', vi.fn(async () => ({ok:false,status:400,json:async () => ({detail:'设置正在保存'})})));
  await act(() => render(<AutomaticUpdateSettings initial={{...initial,mode:'check',download_available:false}} receipt={receipt} />,host));
  expect(host.querySelectorAll<HTMLInputElement>('[role="switch"]')[1]!.disabled).toBe(true);
  await act(() => host.querySelector('form')!.requestSubmit());
  await vi.waitFor(() => expect(host.querySelector('[role="alert"]')?.textContent).toContain('设置正在保存'));
  expect(receipt).not.toHaveBeenCalled();
});
