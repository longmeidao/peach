/* 换头像：点开之前不取候选，点开之后三条路交什么、换不成时说什么。
 *
 * 弹层由 React Aria 渲染到挂载容器外面，所以这里的查询都从整页找。
 * 外观（遮罩、网格列数）由 `frontend/e2e/design.test.ts` 读 `getComputedStyle` 断言。 */
import { act } from 'react';
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';

import type { AvatarChoice } from '../../src/react/avatar-picker/avatar-picker';
import { AvatarPicker } from '../../src/react/avatar-picker/avatar-picker-page';
import { queryClient } from '../../src/react/query';

import { buttonNamed, click, mount, settle, type } from './render';

afterEach(() => { queryClient.clear() });

/* Query 派发更新用的是它自己抓住的那个真 `setTimeout(0)`，用例里的等待推不动它。 */
notifyManager.setScheduler((notify) => notify());

const choice = (over: Partial<AvatarChoice> = {}): AvatarChoice => ({
  ref: 'gfriends:7-S1/葵つかさ.jpg',
  source: 'gfriends',
  label: '7-S1',
  width: 0,
  height: 0,
  detail: '葵つかさ.jpg',
  found_by: '',
  current: false,
  crop: false,
  bases: [],
  focus: null,
  cast: 0,
  ...over,
});

const listing = (choices: AvatarChoice[], extra: Record<string, unknown> = {}) => ({
  kind: 'performer', entity_id: 7792, names: ['葵司', '葵つかさ'],
  matched_names: ['葵つかさ'], choices, index_age_hours: 2, index_stale: false, ...extra,
});

type Call = [string, RequestInit];

/** 第一次取候选、之后每次提交都成功。 */
function server(body: unknown) {
  const calls: Call[] = [];
  const fetched = vi.fn(async (input: string, init?: RequestInit) => {
    calls.push([input, init || {}]);
    return { ok: true, status: 200, json: async () => (init?.method === 'POST' ? { ok: true } : body) };
  });
  vi.stubGlobal('fetch', fetched);
  return calls;
}

const sent = (calls: Call[], n: number): Call => calls[n] as Call;
const body = (calls: Call[], n: number) => JSON.parse(String(sent(calls, n)[1].body));

const cells = () => [...document.querySelectorAll<HTMLElement>('[data-avatar-choice]')];
const dialog = () => document.querySelector('[role="dialog"]');

/** 挂上资料页那个加号，并点开弹层。 */
async function openPicker(props: Record<string, unknown> = {}) {
  const picked = vi.fn();
  const host = await mount(
    <QueryClientProvider client={queryClient}>
      <AvatarPicker kind="performer" entityId={7792} name="葵司" onPicked={picked} {...props} />
    </QueryClientProvider>,
  );
  await click(host.querySelector('button'));
  await settle();
  return { host, picked };
}

it('候选到点开才取，图片只带服务端列出来的 ref', async () => {
  const calls = server(listing([
    choice(), choice({ ref: 'sha256:abc', source: 'history', label: 'twitter', current: true }),
  ]));
  const picked = vi.fn();
  const host = await mount(
    <QueryClientProvider client={queryClient}>
      <AvatarPicker kind="performer" entityId={7792} name="葵司" onPicked={picked} />
    </QueryClientProvider>,
  );
  // 资料页每进一次就预取一遍的话，多数时候没人点开这一屏。
  expect(calls).toHaveLength(0);
  expect(dialog()).toBeNull();

  await click(host.querySelector('button'));
  await settle();
  expect(sent(calls, 0)[0]).toBe('/api/avatar-choices?kind=performer&id=7792');
  expect(cells()).toHaveLength(2);
  expect(cells()[0]?.querySelector('img')?.getAttribute('src'))
    .toBe('/avatar-choice?kind=performer&id=7792&ref=gfriends%3A7-S1%2F%E8%91%B5%E3%81%A4%E3%81%8B%E3%81%95.jpg');
  // 在用的那张标出来，但照样可点——换回去和换过去是同一件事。
  expect(cells()[1]?.getAttribute('aria-selected')).toBe('true');
  expect(cells()[1]?.getAttribute('aria-disabled')).toBeNull();
  expect(cells()[1]?.textContent).toContain('在用');
});

it('图库里的名字与页面上的不同名时说清按谁找到的', async () => {
  server(listing([choice()]));
  await openPicker();
  expect(dialog()?.textContent).toContain('图库里按「葵つかさ」找到的');
});

it('好几个名字各带回一批图时，每一格说清自己是按哪个名字找到的', async () => {
  // 找错人是这一屏唯一会出的大错，而名字是唯一的线索：整屏只报一句「图库里找到的」，
  // 一张同名不同人的图就没有任何能让人起疑的地方。
  server(listing(
    [choice({ found_by: '葵つかさ' }),
      choice({ ref: 'gfriends:3-Prestige/葵ツカサ.jpg', label: '3-Prestige', found_by: '葵ツカサ' })],
    { matched_names: ['葵つかさ', '葵ツカサ'] }));
  await openPicker();
  expect(dialog()?.textContent).toContain('图库里按「葵つかさ」「葵ツカサ」找到的');
  expect(cells()[0]?.getAttribute('title')).toContain('按「葵つかさ」找到');
  expect(cells()[1]?.getAttribute('title')).toContain('按「葵ツカサ」找到');
});

it('点一张就提交，换完关掉弹层并让宿主重画', async () => {
  const calls = server(listing([choice()]));
  const { picked } = await openPicker();
  await click(cells()[0]);
  await settle();
  expect(sent(calls, 1)[0]).toBe('/api/avatar-pick');
  expect(body(calls, 1)).toEqual({ kind: 'performer', id: 7792, ref: 'gfriends:7-S1/葵つかさ.jpg' });
  expect(picked).toHaveBeenCalledOnce();
  expect(dialog()).toBeNull();
});

it('换过之后再点开重新取，「在用」不停在上一次那一格', async () => {
  const calls = server(listing([choice(), choice({ ref: 'sha256:abc', source: 'history', label: 'twitter' })]));
  const { host } = await openPicker();
  await click(cells()[0]);
  await settle();
  await click(host.querySelector('button'));
  await settle();
  expect(calls.filter(([url]) => url.startsWith('/api/avatar-choices'))).toHaveLength(2);
});

it('地址栏填了才允许提交，提交的是 url 而不是 ref', async () => {
  const calls = server(listing([]));
  await openPicker();
  expect(buttonNamed('用这个地址')?.disabled).toBe(true);
  await type(document.querySelector<HTMLInputElement>('input[aria-label="图片地址"]'), '  https://example.com/a.jpg  ');
  expect(buttonNamed('用这个地址')?.disabled).toBe(false);
  await click(buttonNamed('用这个地址'));
  await settle();
  expect(body(calls, 1)).toEqual({ kind: 'performer', id: 7792, url: 'https://example.com/a.jpg' });
});

it('本机选的图按原字节发出去，名字走查询串', async () => {
  const calls = server(listing([]));
  await openPicker();
  const file = new File([new Uint8Array([1, 2, 3])], '我的图.jpg', { type: 'image/jpeg' });
  const input = document.querySelector<HTMLInputElement>('input[type=file]')!;
  Object.defineProperty(input, 'files', { value: [file], configurable: true });
  // 按钮只是把点击转给这个输入框，挑完文件由浏览器派发 change。
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })) });
  await settle();
  expect(sent(calls, 1)[0]).toBe('/api/avatar-pick?kind=performer&id=7792&name=%E6%88%91%E7%9A%84%E5%9B%BE.jpg');
  expect(sent(calls, 1)[1].body).toBe(file);
});

it('换不成时弹层留在原地，原因写在里面', async () => {
  vi.stubGlobal('fetch', vi.fn(async (_input: string, init?: RequestInit) => (
    init?.method === 'POST'
      ? { ok: false, status: 400, json: async () => ({ error: '只接受指向公网的 https 地址' }) }
      : { ok: true, status: 200, json: async () => listing([choice()]) }
  )));
  const { picked } = await openPicker();
  await click(cells()[0]);
  await settle();
  expect(dialog()?.querySelector('[role="alert"]')?.textContent).toContain('只接受指向公网的 https 地址');
  expect(picked).not.toHaveBeenCalled();
  expect(dialog()).not.toBeNull();
});

it('图库索引还没取过时只剩手填那两条路', async () => {
  server(listing([], { matched_names: [], index_age_hours: null, index_stale: true }));
  await openPicker();
  expect(cells()).toHaveLength(0);
  expect(dialog()?.textContent).toContain('图库索引还没取过');
  expect(buttonNamed('从本机选图片')).not.toBeNull();
  expect(document.querySelector('input[type=file]')).not.toBeNull();
});

it('过期的图库索引说出多久没更新，不说成还没取过', async () => {
  server(listing([], { matched_names: [], index_age_hours: 124, index_stale: true }));
  await openPicker();
  expect(dialog()?.textContent).toContain('图库索引 5 天没更新');
  expect(dialog()?.textContent).not.toContain('还没取过');
});

it('合演作品的格子标出人数，框选时提醒先找到她自己的脸', async () => {
  server(listing([choice({
    ref: 'asset:11:cover', source: 'asset', label: 'DVAJ-495', crop: true,
    width: 800, height: 540, bases: ['asset:11:cover'], cast: 15,
  })]));
  await openPicker();
  const [cell] = cells();
  expect(cell?.textContent).toContain('15 人');
  expect(cell?.getAttribute('title')).toContain('15 人合演');
  await click(cell);
  expect(dialog()?.textContent).toContain('DVAJ-495：15 人合演，先找到她自己的脸');
});

/** 作品画面那一档：点开是框一块，不是直接装上去。 */
const artwork = () => choice({
  ref: 'asset:11:cover', source: 'asset', label: 'ABW-232', detail: '',
  crop: true, bases: ['asset:11:cover', 'asset:11:cell4'],
});

it('候选回来之前网格里是同一种格子的骨架，回来之后换成真格子', async () => {
  let answer: (value: unknown) => void = () => {};
  vi.stubGlobal('fetch', vi.fn(() => new Promise((resolve) => { answer = resolve })));
  await openPicker();
  const grid = document.querySelector('[role="listbox"]');
  expect(grid?.getAttribute('aria-busy')).toBe('true');
  expect(document.querySelectorAll('[data-avatar-skeleton]').length).toBeGreaterThan(0);
  // 骨架只给辅助技术一个忙态，不再另写一句「正在读取」。
  expect(dialog()?.textContent).not.toContain('正在');
  await act(async () => answer({ ok: true, status: 200, json: async () => listing([choice()]) }));
  await settle();
  expect(grid?.getAttribute('aria-busy')).toBeNull();
  expect(document.querySelectorAll('[data-avatar-skeleton]')).toHaveLength(0);
  expect(cells()).toHaveLength(1);
});

it('一格的图到了才揭开，取不到也揭开', async () => {
  server(listing([choice(), choice({ ref: 'sha256:abc', source: 'history', label: 'twitter' })]));
  await openPicker();
  const [first, second] = cells();
  const layers = (cell: HTMLElement | undefined) =>
    [...(cell?.querySelectorAll('img, [aria-hidden]') ?? [])];
  expect(layers(first).map((one) => one.hasAttribute('data-revealed'))).toEqual([false, false]);
  await act(async () => { first?.querySelector('img')?.dispatchEvent(new Event('load')) });
  expect(layers(first).map((one) => one.hasAttribute('data-revealed'))).toEqual([true, true]);
  await act(async () => { second?.querySelector('img')?.dispatchEvent(new Event('error')) });
  expect(second?.querySelector('img')?.hasAttribute('data-revealed')).toBe(true);
});

it('封面格子在取景区里取一块 3:4，图库人像照旧铺满', async () => {
  server(listing([
    choice(),
    choice({ ref: 'asset:11:cover', source: 'asset', label: 'ABW-232', crop: true,
      width: 800, height: 540, bases: ['asset:11:cover'],
      focus: { x0: 592, y0: 114, x1: 688, y1: 210 } }),
  ]));
  await openPicker();
  const [portrait, cover] = cells().map((cell) => cell.querySelector('img'));
  expect(portrait?.style.getPropertyValue('--tile-width')).toBe('');
  // 96px 的方块里装得下的 3:4 是 72×96，居中在 (640, 162)：左上角 (604, 114)。
  expect({
    left: cover?.style.getPropertyValue('--tile-left'),
    top: cover?.style.getPropertyValue('--tile-top'),
    width: cover?.style.getPropertyValue('--tile-width'),
    height: cover?.style.getPropertyValue('--tile-height'),
  }).toEqual({
    left: `${(-604 / 72) * 100}%`, top: `${(-114 / 96) * 100}%`,
    width: `${(800 / 72) * 100}%`, height: `${(540 / 96) * 100}%`,
  });
});

it('按番号取来的封面直接进框选，默认框就是脸那一块', async () => {
  const code = choice({
    ref: 'cover:ABW-999', source: 'code', label: 'ABW-999', crop: true,
    width: 800, height: 540, bases: ['cover:ABW-999'],
    focus: { x0: 592, y0: 114, x1: 688, y1: 210 },
  });
  const calls: Call[] = [];
  vi.stubGlobal('fetch', vi.fn(async (input: string, init?: RequestInit) => {
    calls.push([input, init || {}]);
    const answer = input === '/api/avatar-code-cover' ? code
      : init?.method === 'POST' ? { ok: true } : listing([]);
    return { ok: true, status: 200, json: async () => answer };
  }));
  await openPicker();
  expect(buttonNamed('取封面来框')?.disabled).toBe(true);
  const input = document.querySelector<HTMLInputElement>('input[aria-label="番号"]');
  await type(input, ' abw-999 ');
  // 回车就能交，和按那枚键是同一件事。
  await act(async () => { input?.form?.requestSubmit() });
  await settle();
  expect(sent(calls, 1)[0]).toBe('/api/avatar-code-cover');
  expect(body(calls, 1)).toEqual({ code: 'abw-999' });
  expect(dialog()?.textContent).toContain('框出头像那一块');
  expect([...document.querySelectorAll('[data-crop-base]')]).toHaveLength(0);
  await reportSize(800, 540);
  await click(buttonNamed('用这一块'));
  await settle();
  expect(body(calls, 2)).toEqual({
    kind: 'performer', id: 7792, ref: 'cover:ABW-999',
    crop: { x0: 592, y0: 114, x1: 688, y1: 210 },
  });
});

it('番号取不到封面时原因留在弹层里', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: string) => (
    input === '/api/avatar-code-cover'
      ? { ok: false, status: 400, json: async () => ({ error: '官方渠道没有这个番号的封面' }) }
      : { ok: true, status: 200, json: async () => listing([]) }
  )));
  await openPicker();
  await type(document.querySelector<HTMLInputElement>('input[aria-label="番号"]'), 'ABW-999');
  await click(buttonNamed('取封面来框'));
  await settle();
  expect(dialog()?.querySelector('[role="alert"]')?.textContent).toContain('官方渠道没有这个番号的封面');
  expect(dialog()?.textContent).toContain('更换头像');
});

/** happy-dom 不真取图，所以自己报一次尺寸：框的一切都从这一步开始。 */
async function reportSize(width: number, height: number) {
  const image = document.querySelector('[role="dialog"] img');
  if (!image) throw new Error('取景图没有画出来');
  for (const [name, value] of [['naturalWidth', width], ['naturalHeight', height],
    ['clientWidth', width], ['clientHeight', height]] as const) {
    Object.defineProperty(image, name, { value, configurable: true });
  }
  image.dispatchEvent(new Event('load', { bubbles: false }));
  await settle();
}

it('作品画面先框一块再装，方框是正方形的', async () => {
  const calls = server(listing([artwork()]));
  const { picked } = await openPicker();
  await click(cells()[0]);
  await settle();
  // 点一下不该直接换头像：这一步只是进框选。
  expect(calls).toHaveLength(1);
  expect(dialog()?.textContent).toContain('框出头像那一块');
  await reportSize(800, 540);
  await click(buttonNamed('用这一块'));
  await settle();
  expect(sent(calls, 1)[0]).toBe('/api/avatar-pick');
  expect(body(calls, 1)).toEqual({
    kind: 'performer', id: 7792, ref: 'asset:11:cover',
    // 头像是圆的，框只能是正方形：短边 540 居中。
    crop: { x0: 130, y0: 0, x1: 670, y1: 540 },
  });
  expect(picked).toHaveBeenCalledOnce();
});

it('换底图就换一张图，上一张的框一个数都不留', async () => {
  server(listing([artwork()]));
  await openPicker();
  await click(cells()[0]);
  await settle();
  const bases = [...document.querySelectorAll<HTMLElement>('[data-crop-base]')];
  expect(bases.map((one) => one.textContent?.trim())).toEqual(['封面', '第 5 格']);
  await reportSize(800, 540);
  await click(bases[1]);
  await settle();
  // 新底图还没量出尺寸，这一刻没有框可提交。
  expect(buttonNamed('用这一块')?.getAttribute('disabled')).not.toBeNull();
});

it('框错了能回候选，回去还是那一屏', async () => {
  const calls = server(listing([artwork()]));
  await openPicker();
  await click(cells()[0]);
  await settle();
  await click(buttonNamed('回候选'));
  await settle();
  expect(cells()).toHaveLength(1);
  expect(calls).toHaveLength(1);
});
