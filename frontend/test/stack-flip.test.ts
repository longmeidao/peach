import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// 执行生产函数，隔离整页启动与网络请求。
const app = readFileSync(resolve(process.cwd(), '../web/app.js'), 'utf8');
const source = app.slice(app.indexOf('function wireStackFlip('), app.indexOf('function wireMixFlip('));
const wire = new Function('selectMode', 'censorOn', 'reduceMotion', 'syncJavImages', 'appSettings',
  'MIX_FLIP_MS', 'MIX_FLIP_LEAD_MS', `${source};return wireStackFlip`)(
  false, () => false, () => false, () => {}, {}, 1100, 420);
const pool = ['a', 'b', 'c'].map(id => `<img src="/${id}.jpg">`);
function card(stack = true) {
  const el = document.createElement('article');
  el.innerHTML = `<img class="base" src="/base.jpg">${stack ? '<div data-mix-faces hidden></div>' : ''}`;
  document.body.append(el);
  return el;
}
function enter(el: HTMLElement) { el.dispatchEvent(new MouseEvent('mouseenter')); }
function leave(el: HTMLElement) { el.dispatchEvent(new MouseEvent('mouseleave')); }

describe('悬停合集封面', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(HTMLImageElement.prototype, 'complete', 'get').mockReturnValue(true);
    vi.spyOn(HTMLImageElement.prototype, 'naturalWidth', 'get').mockReturnValue(320);
    vi.spyOn(HTMLImageElement.prototype, 'decode').mockResolvedValue();
  });
  afterEach(() => { document.body.replaceChildren(); vi.clearAllTimers(); vi.useRealTimers(); });

  it('全部图片解码后才覆盖静止封面，退出清理计时器', async () => {
    const ready: Array<() => void> = [];
    vi.mocked(HTMLImageElement.prototype.decode).mockImplementation(() => new Promise<void>(resolve => { ready.push(resolve); }));
    const el = card(); wire(el, async () => pool.slice(0, 2)); enter(el);
    await vi.advanceTimersByTimeAsync(340);
    expect((el.querySelector('[data-mix-faces]') as HTMLElement).hidden).toBe(true);
    ready[0]!(); await vi.advanceTimersByTimeAsync(0);
    expect((el.querySelector('[data-mix-faces]') as HTMLElement).hidden).toBe(true);
    ready[1]!(); await vi.advanceTimersByTimeAsync(0);
    expect((el.querySelector('[data-mix-faces]') as HTMLElement).hidden).toBe(false);
    leave(el);
    await vi.advanceTimersByTimeAsync(6000);
    expect(el.querySelectorAll('.mixface')).toHaveLength(0);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('移出再移入时丢弃旧请求，保持一套翻动计时器', async () => {
    let stale!: (value: string[]) => void;
    const load = vi.fn().mockImplementationOnce(() => new Promise(resolve => { stale = resolve; }))
      .mockResolvedValue(pool);
    const el = card(); wire(el, load); enter(el);
    await vi.advanceTimersByTimeAsync(340); leave(el); enter(el);
    await vi.advanceTimersByTimeAsync(340);
    stale(['<img src="/stale.jpg">', '<img src="/old.jpg">']);
    await vi.advanceTimersByTimeAsync(420);
    expect(el.querySelectorAll('.mixface')).toHaveLength(3);
    expect(el.querySelector('.on img')?.getAttribute('src')).toBe('/b.jpg');
    await vi.advanceTimersByTimeAsync(1100);
    expect(el.querySelector('.on img')?.getAttribute('src')).toBe('/c.jpg');
    expect(vi.getTimerCount()).toBe(2);
    leave(el); expect(vi.getTimerCount()).toBe(0);
  });

  it('加载失败的帧不会进入翻动队列', async () => {
    vi.mocked(HTMLImageElement.prototype.decode).mockImplementation(function (this: HTMLImageElement) {
      return this.getAttribute('src') === '/b.jpg' ? Promise.reject(new Error('image')) : Promise.resolve();
    });
    const el = card(); wire(el, async () => pool); enter(el);
    await vi.advanceTimersByTimeAsync(760);
    expect(el.querySelectorAll('.mixface')).toHaveLength(2);
    expect(el.querySelector('.on img')?.getAttribute('src')).toBe('/c.jpg');
    leave(el);
  });

  it('单版本静止卡片不加载悬停封面', async () => {
    const el = card(false), load = vi.fn(); wire(el, load); enter(el);
    await vi.advanceTimersByTimeAsync(10000);
    expect(load).not.toHaveBeenCalled();
    expect(el.querySelector('.base')).not.toBeNull();
    expect(vi.getTimerCount()).toBe(0);
  });
});

it('关闭灯箱后到达的图片事件和缩放回调不访问已销毁的轮播', () => {
  const zoomSource = app.slice(app.indexOf('function wirePhotoZoom('), app.indexOf('const fmtPhotoSize='));
  const zoom = new Function('syncBoardRange', 'PHOTO_ZOOM_MIN', 'PHOTO_ZOOM_MAX', 'PHOTO_ZOOM_STEP',
    `${zoomSource};return wirePhotoZoom`)(() => {}, 10, 400, 10);
  vi.useFakeTimers();
  const box = document.createElement('div');
  box.innerHTML = '<div class="photozoom"><input><b></b></div><button data-photo-scale="fit"></button><button data-photo-scale="original"></button><div class="photomain"><div><img></div></div>';
  document.body.append(box);
  const img = box.querySelector('img')!;
  vi.spyOn(img, 'complete', 'get').mockReturnValue(false);
  const main = { slides: [img.parentElement!] as HTMLElement[] | undefined, activeIndex: 0,
    destroyed: false, on: vi.fn(), zoom: { in: vi.fn(), out: vi.fn() } };
  const controller = zoom(box, main);
  main.destroyed = true; main.slides = undefined; box.remove();
  expect(() => { img.dispatchEvent(new Event('load')); controller.resize(); vi.runAllTimers(); }).not.toThrow();
  expect(main.zoom.out).not.toHaveBeenCalled();
  vi.useRealTimers();
});
