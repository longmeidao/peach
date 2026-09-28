/* 舞台与小窗共用的那一个播放器（`src/react/stage/stage-player.ts`）：同一条认领回来不重建、换一条
 * 先拆旧的再挂新的、离开详情时哪些情形交给小窗。Video.js 本身换成假的：这里量的是实例在两个位置
 * 之间怎么交接，挂载与拆除各发生了几次。真 Video.js 的挂载在 `e2e/stage.test.ts` 里量。 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { PlayerItem } from '../src/player';

interface FakePlayer {
  el(): HTMLElement;
  isDisposed(): boolean;
  paused(): boolean;
  ended(): boolean;
  error(): null;
  on(): void;
  off(): void;
  duration(): number;
  currentTime(to?: number): number;
  play(): Promise<void>;
  pause(): void;
  dispose(): void;
  playing: boolean;
  time: number;
  total: number;
}

const fake = vi.hoisted(() => ({
  mounts: [] as { player: FakePlayer; previousDisposed: boolean[] }[],
  current: null as unknown,
}));

function fakePlayer(): FakePlayer {
  const el = document.createElement('div');
  el.className = 'video-js';
  el.append(document.createElement('video'));
  let disposed = false;
  const player: FakePlayer = {
    playing: true,
    time: 0,
    total: 100,
    el: () => el,
    isDisposed: () => disposed,
    paused: () => !player.playing,
    ended: () => false,
    error: () => null,
    on: () => {},
    off: () => {},
    duration: () => player.total,
    currentTime: (to?: number) => { if (to !== undefined) player.time = to; return player.time },
    play: () => Promise.resolve(),
    pause: () => { player.playing = false },
    dispose: () => { disposed = true; el.remove() },
  };
  return player;
}

vi.mock('../src/player', () => ({
  attachPlayerChrome: vi.fn(() => () => {}),
  cancelDetailStream: vi.fn(),
  closePlayerMenu: vi.fn(),
  configurePlayer: vi.fn(),
  configurePlayerMenu: vi.fn(),
  detailPlayer: () => fake.current,
  setDetailPlayer: (player: unknown) => { fake.current = player },
  disposePlayer: vi.fn((player: FakePlayer | null) => player?.dispose()),
  preparePlayerFrame: vi.fn(),
  resizeSoon: vi.fn(),
  mountPlayer: vi.fn((video: HTMLVideoElement, options: {
    onPlayer?: (player: FakePlayer) => void; handedOff?: (player: FakePlayer) => boolean;
  }) => {
    const player = fakePlayer();
    fake.mounts.push({ player, previousDisposed: fake.mounts.map(({ player: before }) => before.isDisposed()) });
    video.replaceWith(player.el());
    fake.current = player;
    options.onPlayer?.(player);
    return () => { if (!options.handedOff?.(player)) player.dispose() };
  }),
}));

type StagePlayer = typeof import('../src/react/stage/stage-player');
let stage: StagePlayer;
let open = true;
const settings = { miniplayer: true, seekSeconds: 10 };
let offline = false;
let dom: ReturnType<typeof miniplayerDom>;
const requestClose = vi.fn();
const expand = vi.fn();

function miniplayerDom() {
  const node = (tag = 'div') => document.body.appendChild(document.createElement(tag));
  const root = node('aside');
  root.hidden = true;
  return {
    root, frame: node(), play: node('button'), time: node('span'), back: node('button'), ahead: node('button'),
    title: node('span'), sub: node('span'), info: node('button'),
  };
}

const item = (id: number) => ({ id, title: `作品 ${id}` }) as PlayerItem;

/* 舞台打开一条再离开：舞台岛拆的顺序是先问要不要进小窗，再卸 React 树（媒体框的清理跟着跑）。 */
function show(id: number, frame = document.body.appendChild(document.createElement('div'))) {
  stage.setStageMeta({ kind: 'item', item: item(id), title: `作品 ${id}`, sub: '' });
  const detach = stage.attachStagePlayer(frame, { kind: 'item', item: item(id) });
  return {
    frame,
    leave(allow: boolean) { stage.handOffStage(allow); detach(); stage.setStageMeta(null) },
  };
}

beforeEach(async () => {
  vi.resetModules();
  fake.mounts.length = 0;
  fake.current = null;
  open = true;
  offline = false;
  settings.miniplayer = true;
  settings.seekSeconds = 10;
  stage = await import('../src/react/stage/stage-player');
  stage.configureStagePlayer({
    player: { settings: () => settings } as never,
    sourceOffline: () => offline, expand, openItem: vi.fn(), cache: vi.fn(),
  }, { isOpen: () => open, requestClose });
  dom = miniplayerDom();
  stage.registerMiniplayer(dom);
});

afterEach(() => { document.body.replaceChildren() });

describe('舞台与小窗之间交接播放器', () => {
  it('离开详情时正在放的那一个搬进小窗；展开回同一条认领回来，不重建', () => {
    show(1).leave(true);
    const { player } = fake.mounts[0]!;
    expect(player.isDisposed()).toBe(false);
    expect(stage.miniplayerActive()).toBe(true);
    expect(player.el().classList.contains('vjs-peach-mini')).toBe(true);

    stage.prepareStageFor('item', 1);
    const back = show(1);
    expect(fake.mounts).toHaveLength(1);
    expect(back.frame.contains(player.el())).toBe(true);
    expect(player.el().classList.contains('vjs-peach-mini')).toBe(false);
    expect(stage.stagePlayer()).toBe(player);
    expect(stage.miniplayerActive()).toBe(false);
  });

  it('小窗放着别的条目时打开另一条：先拆小窗里那一个，再挂新的', () => {
    show(1).leave(true);
    stage.prepareStageFor('item', 2);
    expect(fake.mounts[0]!.player.isDisposed()).toBe(true);
    show(2);
    expect(fake.mounts).toHaveLength(2);
    expect(fake.mounts[1]!.previousDisposed).toEqual([true]);
  });

  it('队列换条：上一条的媒体框先卸，下一条才挂', () => {
    show(1).leave(false);
    show(2);
    expect(fake.mounts[1]!.previousDisposed).toEqual([true]);
    expect(stage.miniplayerActive()).toBe(false);
  });

  it.each([
    ['显式关闭', false, true, true],
    ['暂停着', true, false, true],
    ['设置里关了小窗', true, true, false],
  ])('%s就不进小窗，播放器随舞台拆掉', (_name, allow, playing, enabled) => {
    settings.miniplayer = enabled;
    const shown = show(1);
    fake.mounts[0]!.player.playing = playing;
    shown.leave(allow);
    expect(fake.mounts[0]!.player.isDisposed()).toBe(true);
    expect(stage.miniplayerActive()).toBe(false);
  });

  it('i 键在详情里请求进小窗：越过播放态判定，关闭请求照常走舞台', () => {
    const shown = show(1);
    fake.mounts[0]!.player.playing = false;
    stage.toggleMiniplayer();
    expect(requestClose).toHaveBeenCalledOnce();
    shown.leave(false);
    expect(fake.mounts[0]!.player.isDisposed()).toBe(false);
    expect(stage.miniplayerActive()).toBe(true);

    open = false;
    stage.toggleMiniplayer();
    expect(expand).toHaveBeenCalledWith('item', 1, null);
  });
});

describe('小窗自己的键', () => {
  it('快退快进按设置里的秒数跳，标签里带着这个数；时长取不到时不封顶', () => {
    settings.seekSeconds = 15;
    show(1).leave(true);
    const { player } = fake.mounts[0]!;
    expect(dom.back.getAttribute('aria-label')).toBe('后退 15 秒');
    expect(dom.ahead.title).toBe('前进 15 秒');
    player.time = 90;
    stage.seekMiniplayer(1);
    expect(player.time).toBe(100);
    stage.seekMiniplayer(-1);
    expect(player.time).toBe(85);
    player.total = Number.NaN;
    player.time = 100;
    stage.seekMiniplayer(1);
    expect(player.time).toBe(115);
  });

  it.each([
    ['分卷组', { part_group: { key: 'p' } }],
    ['版次组', { edition_group: { key: 'e' } }],
    ['图片', { medium: 'image' }],
    ['计费来源', { cost: 'metered', location: '115' }],
    ['反查不到关注条目的在线资产', { location: 'online' }],
  ])('小窗开着时%s的卡片照常进详情，不在小窗里换片', (_name, extra) => {
    show(1).leave(true);
    expect(stage.miniplayerTakesCard({ id: 2, location: 'local' } as PlayerItem)).toBe(true);
    expect(stage.miniplayerTakesCard({ id: 2, location: 'local', ...extra } as PlayerItem)).toBe(false);
  });

  it('来源脱盘或小窗没开时也不接', () => {
    expect(stage.miniplayerTakesCard({ id: 2, location: 'local' } as PlayerItem)).toBe(false);
    show(1).leave(true);
    offline = true;
    expect(stage.miniplayerTakesCard({ id: 2, location: 'local' } as PlayerItem)).toBe(false);
  });
});
