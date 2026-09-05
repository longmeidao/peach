import { render } from 'preact';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  CONFIGURATION_URL, Configuration, PICK_FOLDER_URL, loadConfiguration,
} from '../src/islands/configuration';
import type { ConfigurationData } from '../src/islands/configuration';

const data = (over: Partial<ConfigurationData> = {}): ConfigurationData => ({
  editable: true,
  notice: '',
  revision: 'rev-1',
  media_dirs: ['D:\\Media'],
  port: 9123,
  facts: [{ term: '版本', value: '0.7.25' }, { term: 'FFmpeg', value: '内置' }],
  ...over,
});

const mount = (props: Partial<ConfigurationData> = {}, receipt = vi.fn()) => {
  const el = document.createElement('div');
  document.body.append(el);
  render(<Configuration receipt={receipt} data={data(props)} error="" />, el);
  return { el, receipt };
};

const inputs = (el: Element) => [...el.querySelectorAll<HTMLInputElement>('.configdir > input')];
const submit = (el: Element) => {
  el.querySelector('form')?.dispatchEvent(new Event('submit', { cancelable: true }));
};
// Preact 把状态更新攒到微任务里再画；输入之后、提交之前都要等它落地。
const settle = async () => {
  for (let i = 0; i < 4; i += 1) await Promise.resolve();
};
type FetchCall = [string, RequestInit];
const fetchMock = (status: number, body: unknown) => vi.fn<(...call: FetchCall) => Promise<unknown>>(
  async () => ({ ok: status < 400, status, json: async () => body }),
);

afterEach(() => {
  for (const el of [...document.body.children]) render(null, el);
  document.body.innerHTML = '';
  vi.unstubAllGlobals();
});

describe('配置页取数', () => {
  it('首屏走 /api/configuration 并带上中止信号', async () => {
    const fetch = fetchMock(200, data());
    vi.stubGlobal('fetch', fetch);
    const controller = new AbortController();
    await loadConfiguration({ receipt: vi.fn() }, controller.signal);
    const [url, init] = fetch.mock.calls[0] ?? [];
    expect(url).toBe(CONFIGURATION_URL);
    expect(init?.signal).toBe(controller.signal);
  });
});

describe('媒体文件夹列表', () => {
  it('刷新挂载状态保留未保存的路径', async () => {
    const media_sources = [{ location: '115', path: 'B:/', root: 'B:/', online: false }];
    vi.stubGlobal('fetch', fetchMock(200, data({media_sources: [{ ...media_sources[0]!, online: true }]})));
    const { el } = mount({ windows: true, media_sources });
    const input = inputs(el)[0]!;
    input.value = 'B:/Movies'; input.dispatchEvent(new Event('input')); await settle();
    [...el.querySelectorAll<HTMLButtonElement>('button')].find((button) => button.textContent === '刷新挂载状态')?.click();
    await settle();
    expect(inputs(el)[0]?.value).toBe('B:/Movies');
    expect(el.textContent).toContain('在线');
  });
  it('按来源回填所有挂载点，提交时保留 macOS 盘符映射', async () => {
    const fetch = fetchMock(200, { saved: true, url: '/', revision: 'rev-2' });
    vi.stubGlobal('fetch', fetch);
    const { el } = mount({ windows: false, media_sources: [
      { location: '115', root: 'B:\\', path: '/Volumes/115', online: false },
      { location: 'pikpak', root: 'A:\\', path: '/Volumes/PikPak', online: true },
    ] });
    expect(inputs(el).map((input) => input.value)).toEqual(['/Volumes/115', '/Volumes/PikPak']);
    expect(el.textContent).toContain('离线');
    expect(el.textContent).toContain('在线');
    submit(el); await settle();
    const body = JSON.parse(String(fetch.mock.calls[0]?.[1].body));
    expect(body.media_sources).toEqual([
      { location: '115', root: 'B:\\', path: '/Volumes/115' },
      { location: 'pikpak', root: 'A:\\', path: '/Volumes/PikPak' },
    ]);
  });
  it('一行一个文件夹，只有一行时没有移除键', () => {
    const { el } = mount();
    expect(inputs(el).map((input) => input.value)).toEqual(['D:\\Media']);
    expect(el.querySelector('.configrm')).toBeNull();
  });

  it('添加文件夹是次级按钮，新行接过焦点，之后每行都能移除', async () => {
    const { el } = mount();
    const add = el.querySelector<HTMLButtonElement>('.configadd');
    expect(add?.classList.contains('primary'), '每屏只有「保存配置」一个主动作').toBe(false);
    add?.click();
    await settle();
    expect(inputs(el)).toHaveLength(2);
    expect(document.activeElement).toBe(inputs(el)[1]);
    expect(el.querySelectorAll('.configrm')).toHaveLength(2);
    el.querySelectorAll<HTMLButtonElement>('.configrm')[0]?.click();
    await settle();
    expect(inputs(el)).toHaveLength(1);
    expect(inputs(el)[0]?.value).toBe('');
  });
});

describe('选择文件夹', () => {
  it('让这台电脑弹系统对话框，选中的路径填回这一行', async () => {
    const fetch = fetchMock(200, { path: 'E:\\Movies' });
    vi.stubGlobal('fetch', fetch);
    const { el } = mount();
    const pickButtons = el.querySelectorAll('.configpick');
    expect(pickButtons).toHaveLength(1);
    expect(el.querySelector('.configdir')?.children[1]).toBe(pickButtons[0]);
    el.querySelector<HTMLButtonElement>('.configpick')?.click();
    await settle();
    const [url, init] = fetch.mock.calls[0] ?? [];
    expect(url).toBe(PICK_FOLDER_URL);
    expect(init?.method).toBe('POST');
    expect(JSON.parse(String(init?.body))).toEqual({ initial: 'D:\\Media' });
    expect(inputs(el)[0]?.value).toBe('E:\\Movies');
    expect(el.querySelector('.configpick')?.getAttribute('aria-busy'), '对话框关了忙态要撤掉').toBeNull();
  });

  it('取消什么也不改；打不开对话框时原因写在这一行下面', async () => {
    vi.stubGlobal('fetch', fetchMock(200, { path: null }));
    const { el } = mount();
    el.querySelector<HTMLButtonElement>('.configpick')?.click();
    await settle();
    expect(inputs(el)[0]?.value).toBe('D:\\Media');
    expect(el.querySelector('.configbad')).toBeNull();
    vi.stubGlobal('fetch', fetchMock(501, { error: '这个系统上没有可用的文件夹对话框' }));
    el.querySelector<HTMLButtonElement>('.configpick')?.click();
    await settle();
    expect(el.querySelector('.configdir .configbad')?.textContent).toContain('没有可用的文件夹对话框');
  });
});

describe('保存', () => {
  it('提交带上指纹、全部文件夹、端口与是否扫描，成功后发过去时回执并留下新地址', async () => {
    const fetch = fetchMock(200, { saved: true, url: 'http://127.0.0.1:9124/', revision: 'rev-2' });
    vi.stubGlobal('fetch', fetch);
    const { el, receipt } = mount();
    const port = el.querySelector<HTMLInputElement>('#configPort');
    if (!port) throw new Error('端口输入框没有画出来');
    port.value = '9124';
    port.dispatchEvent(new Event('input'));
    await settle();
    submit(el);
    await settle();
    const [url, init] = fetch.mock.calls[0] ?? [];
    expect(url).toBe(CONFIGURATION_URL);
    expect(init?.method).toBe('POST');
    expect(JSON.parse(String(init?.body))).toEqual({
      revision: 'rev-1', media_dirs: ['D:\\Media'], port: '9124', scan_now: false,
    });
    expect(receipt).toHaveBeenCalledWith('已保存配置');
    expect(el.querySelector('.geist-note-success')?.textContent).toContain('正在重新启动');
    expect(el.querySelector<HTMLAnchorElement>('.configsaved a')?.getAttribute('href'))
      .toBe('http://127.0.0.1:9124/');
    expect(el.querySelector('form'), '保存后表单不再留在页面上').toBeNull();
  });

  it('服务端按字段退回的原因写回原位，不发回执', async () => {
    vi.stubGlobal('fetch', fetchMock(400, {
      error: '有几项需要修改',
      errors: { media_dirs: ['', '和上面的文件夹重复了'], port: '端口要在 1024 到 65535 之间' },
    }));
    const { el, receipt } = mount({ media_dirs: ['D:\\Media', 'D:\\Media'] });
    submit(el);
    await settle();
    const rows = el.querySelectorAll('.configdir');
    expect(rows[0]?.querySelector('.configbad')).toBeNull();
    expect(rows[1]?.querySelector('.configbad')?.textContent).toBe('和上面的文件夹重复了');
    expect(inputs(el)[1]?.getAttribute('aria-invalid')).toBe('true');
    expect(el.querySelector('#configPort + .configbad')?.textContent).toContain('端口');
    expect(receipt).not.toHaveBeenCalled();
    expect(el.querySelector('.geist-note-error'), '字段级原因不再叠一条整体 Note').toBeNull();
  });

  it('其它失败留在表单下方等重试', async () => {
    vi.stubGlobal('fetch', fetchMock(409, { error: '配置已变更，请刷新后再保存' }));
    const { el } = mount();
    submit(el);
    await settle();
    expect(el.querySelector('.geist-note-error')?.textContent).toContain('配置已变更');
    expect(el.querySelector('form')).not.toBeNull();
    expect(el.querySelector('.geist-button.primary')?.getAttribute('aria-busy'), '失败后忙态要撤掉').toBeNull();
  });
});

describe('不能编辑时', () => {
  it('只说原因和运行信息，不画表单', () => {
    const { el } = mount({ editable: false, notice: '请在运行 Peach 的电脑上打开配置' });
    expect(el.querySelector('form')).toBeNull();
    expect(el.querySelector('.geist-note-secondary')?.textContent).toContain('请在运行 Peach 的电脑上打开配置');
    expect([...el.querySelectorAll('.configfacts dt')].map((dt) => dt.textContent)).toEqual(['版本', 'FFmpeg']);
  });

  it('首屏取数失败时画原因', () => {
    const el = document.createElement('div');
    document.body.append(el);
    render(<Configuration receipt={vi.fn()} data={null} error="请先完成首次设置" />, el);
    expect(el.querySelector('.geist-note-error')?.textContent).toContain('请先完成首次设置');
  });
});
