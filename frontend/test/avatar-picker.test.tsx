import { afterEach, expect, it, vi } from 'vitest';
import { act } from 'preact/test-utils';

import { mountAvatarPicker, unmountAvatarPicker } from '../src/avatar-picker';
import type { AvatarChoice } from '../src/avatar-picker';

let root: HTMLDivElement;
afterEach(() => { unmountAvatarPicker(root); document.body.innerHTML = ''; vi.unstubAllGlobals() });

const choice = (overrides: Partial<AvatarChoice> = {}): AvatarChoice => ({
  ref: 'gfriends:7-S1/葵つかさ.jpg',
  source: 'gfriends',
  label: '7-S1',
  width: 0,
  height: 0,
  detail: '葵つかさ.jpg',
  found_by: '',
  current: false,
  ...overrides,
});

const listing = (choices: AvatarChoice[], extra: Record<string, unknown> = {}) => ({
  kind: 'performer', entity_id: 7792, names: ['葵司', '葵つかさ'],
  matched_names: ['葵つかさ'], choices, index_age_hours: 2, index_stale: false, ...extra,
});

type Call = [string, RequestInit];

/** 按次序记下的第 n 个请求。 */
const sent = (calls: Call[], n: number): Call => calls[n] as Call;

/** 第一次取候选、之后每次提交都成功。 */
const server = (body: unknown) => {
  const calls: Call[] = [];
  const fetched = vi.fn(async (input: string, init?: RequestInit) => {
    calls.push([input, init || {}]);
    return { ok: true, status: 200, json: async () => (init?.method === 'POST' ? { ok: true } : body) };
  });
  vi.stubGlobal('fetch', fetched);
  return calls;
};

/** 取数与提交都跨若干个微任务，等它们落地再断言。 */
const settle = () => act(async () => { await new Promise(resolve => setTimeout(resolve, 0)) });

const press = async (selector: string) => {
  await act(async () => { root.querySelector<HTMLButtonElement>(selector)!.click() });
  await settle();
};

/** jsdom 没有实现 `showModal`／`close`，它们只改 open 属性。 */
async function openPicker(props: Record<string, unknown> = {}) {
  root = document.createElement('div');
  document.body.append(root);
  const picked = vi.fn();
  await act(async () => mountAvatarPicker(root, {
    kind: 'performer', id: 7792, name: '葵司', onPicked: picked, ...props,
  } as never));
  const popup = root.querySelector('dialog')!;
  popup.showModal = () => popup.setAttribute('open', '');
  popup.close = () => popup.removeAttribute('open');
  await press('.avatarpick-open');
  return { picked, popup };
}

it('候选到点开才取，图片只带服务端列出来的 ref', async () => {
  const calls = server(listing([choice(), choice({ ref: 'sha256:abc', source: 'history', label: 'twitter', current: true })]));
  await openPicker();
  expect(sent(calls, 0)[0]).toBe('/api/avatar-choices?kind=performer&id=7792');
  const cells = [...root.querySelectorAll('.avatarpick-cell')];
  expect(cells).toHaveLength(2);
  expect(cells[0]!.querySelector('img')!.getAttribute('src'))
    .toBe('/avatar-choice?kind=performer&id=7792&ref=gfriends%3A7-S1%2F%E8%91%B5%E3%81%A4%E3%81%8B%E3%81%95.jpg');
  // 在用的那张标出来，但照样可点——换回去和换过去是同一件事。
  expect(cells[1]!.classList.contains('current')).toBe(true);
  expect(cells[1]!.querySelector('b')!.textContent).toBe('在用');
});

it('图库里的名字与页面上的不同名时说清按谁找到的', async () => {
  server(listing([choice()]));
  await openPicker();
  expect(root.textContent).toContain('图库里按「葵つかさ」找到的');
});

it('好几个名字各带回一批图时，每一格说清自己是按哪个名字找到的', async () => {
  // 找错人是这一屏唯一会出的大错，而名字是唯一的线索：整屏只报一句「图库里找到的」，
  // 一张同名不同人的图就没有任何能让人起疑的地方。
  server(listing(
    [choice({ found_by: '葵つかさ' }),
     choice({ ref: 'gfriends:3-Prestige/葵ツカサ.jpg', label: '3-Prestige', found_by: '葵ツカサ' })],
    { matched_names: ['葵つかさ', '葵ツカサ'] }));
  await openPicker();
  expect(root.textContent).toContain('图库里按「葵つかさ」「葵ツカサ」找到的');
  const cells = [...root.querySelectorAll('.avatarpick-cell')];
  expect(cells[0]!.getAttribute('title')).toContain('按「葵つかさ」找到');
  expect(cells[1]!.getAttribute('title')).toContain('按「葵ツカサ」找到');
});

it('点一张就提交，换完关掉弹层并让宿主重画', async () => {
  const calls = server(listing([choice()]));
  const { picked, popup } = await openPicker();
  await press('.avatarpick-cell');
  expect(sent(calls, 1)[0]).toBe('/api/avatar-pick');
  expect(JSON.parse(String(sent(calls, 1)[1].body))).toEqual({
    kind: 'performer', id: 7792, ref: 'gfriends:7-S1/葵つかさ.jpg',
  });
  expect(picked).toHaveBeenCalledOnce();
  expect(popup.hasAttribute('open')).toBe(false);
});

it('地址栏填了才允许提交，提交的是 url 而不是 ref', async () => {
  const calls = server(listing([]));
  await openPicker();
  expect(root.querySelector<HTMLButtonElement>('.avatarpick-url button')!.disabled).toBe(true);
  const field = root.querySelector<HTMLInputElement>('.avatarpick-url input')!;
  field.value = '  https://example.com/a.jpg  ';
  await act(async () => { field.dispatchEvent(new Event('input', { bubbles: true })) });
  expect(root.querySelector<HTMLButtonElement>('.avatarpick-url button')!.disabled).toBe(false);
  await press('.avatarpick-url button');
  expect(JSON.parse(String(sent(calls, 1)[1].body))).toEqual({
    kind: 'performer', id: 7792, url: 'https://example.com/a.jpg',
  });
});

it('本机选的图按原字节发出去，名字走查询串', async () => {
  const calls = server(listing([]));
  await openPicker();
  const file = new File([new Uint8Array([1, 2, 3])], '我的图.jpg', { type: 'image/jpeg' });
  const input = root.querySelector<HTMLInputElement>('input[type=file]')!;
  Object.defineProperty(input, 'files', { value: [file], configurable: true });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })) });
  await settle();
  expect(sent(calls, 1)[0]).toBe('/api/avatar-pick?kind=performer&id=7792&name=%E6%88%91%E7%9A%84%E5%9B%BE.jpg');
  expect(sent(calls, 1)[1].body).toBe(file);
});

it('换不成时弹层留在原地，原因写在里面', async () => {
  const fetched = vi.fn(async (_input: string, init?: RequestInit) => (
    init?.method === 'POST'
      ? { ok: false, status: 400, json: async () => ({ error: '只接受指向公网的 https 地址' }) }
      : { ok: true, status: 200, json: async () => listing([choice()]) }
  ));
  vi.stubGlobal('fetch', fetched);
  const { picked, popup } = await openPicker();
  await press('.avatarpick-cell');
  expect(root.querySelector('.avatarpick-error')!.textContent).toContain('只接受指向公网的 https 地址');
  expect(picked).not.toHaveBeenCalled();
  expect(popup.hasAttribute('open')).toBe(true);
});

it('图库索引还没取过时只剩手填那两条路', async () => {
  server(listing([], { matched_names: [], index_age_hours: null, index_stale: true }));
  await openPicker();
  expect(root.querySelectorAll('.avatarpick-cell')).toHaveLength(0);
  expect(root.textContent).toContain('图库索引还没取过');
  expect(root.querySelector('input[type=file]')).not.toBeNull();
});
