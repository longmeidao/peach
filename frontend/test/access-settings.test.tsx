import { render } from 'preact';
import { afterEach, expect, it, vi } from 'vitest';
import { AccessSettings } from '../src/islands/access-settings';

const settle = async () => { for (let i = 0; i < 6; i++) await Promise.resolve(); };
afterEach(() => { for (const el of [...document.body.children]) render(null, el); document.body.innerHTML = ''; vi.unstubAllGlobals(); });

it('系统口令可直接转为可选密码且关闭需要明确提交', async () => {
  const host = document.createElement('div'); document.body.append(host);
  const receipt = vi.fn();
  const fetcher = vi.fn(async () => ({ ok: true, json: async () => ({ mode: 'open', revision: 'next' }) }));
  vi.stubGlobal('fetch', fetcher);
  render(<AccessSettings initial={{ mode: 'legacy', revision: 'legacy' }} receipt={receipt} />, host);
  expect(host.querySelector('[autocomplete="current-password"]')).toBeNull();
  expect(host.querySelector('.geist-fieldset-footer .primary')?.textContent).toBe('保存配置');
  const toggle = host.querySelector<HTMLInputElement>('[type="checkbox"]')!;
  toggle.checked = true; toggle.dispatchEvent(new Event('change', { bubbles: true })); await settle();
  const passwordFields = [...host.querySelectorAll<HTMLInputElement>('[autocomplete="new-password"]')];
  expect(passwordFields).toHaveLength(2);
  expect(passwordFields.every((input) => input.disabled && !input.required)).toBe(true);
  expect(host.querySelector('form')?.getAttribute('data-fieldset-type')).toBe('warning');
  expect(host.querySelector('.geist-note-warning')?.textContent).toContain('直接访问馆藏');
  expect(fetcher).not.toHaveBeenCalled();
  host.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true })); await settle();
  expect(JSON.parse((fetcher.mock.calls[0] as unknown as [string, RequestInit])[1].body as string)).toMatchObject({ action: 'disable', confirm_disable: true });
  expect(receipt).toHaveBeenCalledWith('已关闭访问密码');
  expect(host.textContent).toContain('未设置密码');
});

it('关闭选项位于输入上方且保留草稿并要求当前密码验证', async () => {
  const host = document.createElement('div'); document.body.append(host);
  const fetcher = vi.fn(async () => ({ ok: true, json: async () => ({ mode: 'open', revision: 'next' }) }));
  vi.stubGlobal('fetch', fetcher);
  render(<AccessSettings initial={{ mode: 'password', revision: 'one' }} receipt={vi.fn()} />, host);
  const toggle = host.querySelector<HTMLInputElement>('[type="checkbox"]')!;
  const current = host.querySelector<HTMLInputElement>('#access-current')!;
  const fields = [...host.querySelectorAll<HTMLInputElement>('[autocomplete="new-password"]')];
  expect(toggle.compareDocumentPosition(current) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  for (const input of fields) {
    input.value = 'draft-password'; input.dispatchEvent(new Event('input', { bubbles: true }));
  }
  await settle();
  toggle.checked = true; toggle.dispatchEvent(new Event('change', { bubbles: true })); await settle();
  expect(fields.every((input) => input.disabled && input.value === 'draft-password')).toBe(true);
  expect(current.disabled).toBe(false);
  expect(current.required).toBe(true);
  toggle.checked = false; toggle.dispatchEvent(new Event('change', { bubbles: true })); await settle();
  expect(fields.every((input) => !input.disabled && input.required && input.value === 'draft-password')).toBe(true);
  toggle.checked = true; toggle.dispatchEvent(new Event('change', { bubbles: true })); await settle();
  expect(fetcher).not.toHaveBeenCalled();
  host.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true })); await settle();
  expect(current.getAttribute('aria-invalid')).toBe('true');
  expect(fetcher).not.toHaveBeenCalled();
  current.value = 'current-password'; current.dispatchEvent(new Event('input', { bubbles: true })); await settle();
  host.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true })); await settle();
  expect(JSON.parse((fetcher.mock.calls[0] as unknown as [string, RequestInit])[1].body as string)).toMatchObject({
    action: 'disable', confirm_disable: true, current_password: 'current-password', password: '', confirmation: '',
  });
});

it('已设置的密码需要当前密码且失败原因留在表单中', async () => {
  const host = document.createElement('div'); document.body.append(host);
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 400, json: async () => ({ message: '当前访问密码不正确', errors: { current_password: '当前访问密码不正确' } }) })));
  render(<AccessSettings initial={{ mode: 'password', revision: 'one' }} receipt={vi.fn()} />, host);
  expect(host.querySelector('[autocomplete="current-password"]')).not.toBeNull();
  for (const input of host.querySelectorAll<HTMLInputElement>('input[type="password"]')) {
    input.value = 'example-password'; input.dispatchEvent(new Event('input', { bubbles: true }));
  }
  await settle();
  host.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true })); await settle();
  expect(host.querySelector('[role="alert"]')?.textContent).toBe('当前访问密码不正确');
  expect(host.querySelector('[autocomplete="current-password"]')?.getAttribute('aria-invalid')).toBe('true');
});

it('长度提示紧贴字段且提交不合法内容时变为字段错误', async () => {
  const host = document.createElement('div'); document.body.append(host);
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
  render(<AccessSettings initial={{ mode: 'open', revision: 'one' }} receipt={vi.fn()} />, host);
  expect(host.querySelector('.configfieldset-heading #accessTitle')).not.toBeNull();
  expect(host.querySelector('.configfieldset-heading > .confighelp')?.textContent).toContain('未设置密码');
  const field = host.querySelector<HTMLInputElement>('#access-password')!;
  expect(field.nextElementSibling?.textContent).toContain('至少 8 个字符');
  host.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true })); await settle();
  expect(field.getAttribute('aria-invalid')).toBe('true');
  expect(field.nextElementSibling?.className).toBe('configbad');
  expect(field.nextElementSibling?.getAttribute('role')).toBe('alert');
  expect(fetcher).not.toHaveBeenCalled();
});
