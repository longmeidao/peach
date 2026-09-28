/* 播放器模块（`src/player/`）里不依赖 Video.js 的几块：片源判据、流会话取消、观看上报、
 * 加载读数、画中画的 Media Session 与外挂字幕。挂上真 Video.js 的那一面在 `e2e/stage.test.ts`。 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { mountPlayerMediaSession, mountPlayerSubtitles } from '../src/player/controls';
import { configurePlayer, type PlayerHost } from '../src/player/host';
import { averageBitrate, bufferedAhead, fmtLoadRate, pushPlayerStat } from '../src/player/stats';
import {
  cancelDetailStream, detailStreamSource, detailStreamSession, directStreamSource, playableStreamSource,
} from '../src/player/stream';
import { wireTelemetry } from '../src/player/telemetry';
import type { VjsPlayer } from '../src/player/types';

type FetchCall = { url: string; init: RequestInit | undefined };

function stubFetch(reply: (url: string) => unknown): FetchCall[] {
  const calls: FetchCall[] = [];
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    calls.push({ url, init });
    return new Response(JSON.stringify(reply(url) ?? null), { status: 200, headers: { 'Content-Type': 'application/json' } });
  }));
  return calls;
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

const host = (seekSeconds = 10): PlayerHost => ({
  settings: () => ({ ambientMode: false, theaterMode: false, seekSeconds, miniplayer: true, detailAutoplay: false }),
  saveSettings: () => {},
  toast: () => {},
  loadSourceStatus: async () => ({}),
  offlineReason: () => '',
  posterUrl: () => '',
  stage: () => null,
});

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('片源判据', () => {
  it('保存过的在线资产走关注条目的代理，不问 stream-plan', async () => {
    const calls = stubFetch(() => null);
    const source = await playableStreamSource({ id: 7, location: 'online', follow_item_id: 42 }, 's1');
    expect(source).toEqual({ src: '/follow-stream?id=42', type: 'video/mp4' });
    expect(calls).toEqual([]);
  });

  it('服务端要转码分片就给分片；计划取不到就带会话直读，webm 按扩展名给类型', async () => {
    stubFetch(() => ({ protocol: 'hls', src: '/stream/hls/3/index.m3u8' }));
    expect(await playableStreamSource({ id: 3 }, 's2'))
      .toEqual({ src: '/stream/hls/3/index.m3u8', type: 'application/vnd.apple.mpegurl' });
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch') }));
    expect(await playableStreamSource({ id: 3, name: 'a.WEBM' }, 's 2'))
      .toEqual({ src: '/stream?id=3&session=s%202', type: 'video/webm' });
    expect(directStreamSource({ id: 4 }, 'x').type).toBe('video/mp4');
  });

  it('详情这一路共用一个会话，取消时按会话通知服务端并清空', async () => {
    const calls = stubFetch(() => ({ cancelled: 1 }));
    await detailStreamSource({ id: 5 });
    const session = detailStreamSession();
    expect(session).not.toBe('');
    expect(calls[0]!.url).toBe(`/api/stream-plan?id=5&session=${encodeURIComponent(session)}`);
    cancelDetailStream();
    expect(detailStreamSession()).toBe('');
    const cancel = calls.at(-1)!;
    expect(cancel.url).toBe(`/api/stream-cancel?session=${encodeURIComponent(session)}`);
    expect(cancel.init).toMatchObject({ method: 'POST', keepalive: true });
    await flush(); await flush();
    expect(JSON.parse(document.documentElement.dataset.peachStreamCancel || 'null')).toEqual({ cancelled: 1 });
  });
});

describe('观看上报', () => {
  beforeEach(() => { vi.useFakeTimers(); });

  it('离开详情时既不 pause 也不 ended：emptied 收尾停表，撤销登记给了舞台', async () => {
    const calls = stubFetch(() => ({ real_ratio: .5 }));
    const video = document.createElement('video');
    const disposers: (() => void)[] = [];
    wireTelemetry({ id: 9, duration: -1 }, video, { register: (stop) => disposers.push(stop) });
    expect(disposers).toHaveLength(1);
    video.onplay?.(new Event('play'));
    video.dispatchEvent(new Event('seeking'));
    vi.advanceTimersByTime(10_000);
    expect(calls.filter((call) => call.url === '/api/activity')).toHaveLength(1);
    video.dispatchEvent(new Event('emptied'));
    const settled = calls.length;
    vi.advanceTimersByTime(60_000);
    expect(calls).toHaveLength(settled);
  });

  it('放完冲一次 ended，再交给调用方接着放下一条；-1 时长不画负比例', () => {
    const calls = stubFetch(() => null);
    const video = document.createElement('video');
    const ratio = document.createElement('span');
    ratio.id = 'ratioProbe';
    document.body.append(ratio);
    const onEnded = vi.fn();
    wireTelemetry({ id: 11, duration: -1 }, video, { ratio: '#ratioProbe', onEnded });
    expect(ratio.textContent).toBe('');
    video.onended?.(new Event('ended'));
    const body = JSON.parse(String(calls[0]!.init?.body));
    expect(body).toMatchObject({ id: 11, ended: true, duration: 0 });
    expect(onEnded).toHaveBeenCalledOnce();
    ratio.remove();
  });
});

describe('加载读数', () => {
  const buffered = (ranges: [number, number][]) => ({
    length: ranges.length, start: (i: number) => ranges[i]![0], end: (i: number) => ranges[i]![1],
  });

  it('缓冲健康只数播放位置所在那一段；码率要有大小和真时长才算得出', () => {
    const video = { currentTime: 12, buffered: buffered([[0, 5], [10, 30]]) } as unknown as HTMLVideoElement;
    expect(bufferedAhead(video)).toBe(18);
    expect(averageBitrate(1_000_000, 8)).toBe(1_000_000);
    expect(averageBitrate(1_000_000, -1)).toBe(0);
  });

  it('码率未知时报还能往前放多久，不报「× 实时」这类要换算的口径', () => {
    expect(fmtLoadRate(0, 12.4)).toBe('已缓冲 12 秒');
    expect(fmtLoadRate(8 * 2048, 0)).toBe('2 KB/s');
    expect(fmtLoadRate(0, 0)).toBe('加载中…');
  });

  it('三条指标各留 24 个采样，坏值记成 0', () => {
    const samples: number[] = [];
    for (let i = 1; i <= 30; i++) pushPlayerStat(samples, i);
    pushPlayerStat(samples, Number.NaN);
    expect(samples).toHaveLength(24);
    expect(samples[0]).toBe(8);
    expect(samples.at(-1)).toBe(0);
  });
});

function fakePlayer(state: { time: number; duration: number }) {
  const handlers = new Map<string, (() => void)[]>();
  const player = {
    on(events: string | string[], fn: () => void) {
      for (const event of [events].flat()) handlers.set(event, [...handlers.get(event) || [], fn]);
    },
    currentTime(value?: number) { if (value !== undefined) state.time = value; return state.time },
    duration: () => state.duration,
    playbackRate: () => 1,
    play: () => Promise.resolve(),
    pause: () => {},
    isDisposed: () => false,
    addRemoteTextTrack: vi.fn(),
  };
  const fire = (event: string) => handlers.get(event)?.forEach((fn) => fn());
  return { player: player as unknown as VjsPlayer, raw: player, fire };
}

describe('画中画的快进快退', () => {
  it('逐个登记动作，一个不认不带走其余；步长取设置；换片时整组摘掉', () => {
    configurePlayer(host(15));
    const handlers = new Map<string, MediaSessionActionHandler | null>();
    const positions: unknown[] = [];
    vi.stubGlobal('navigator', { mediaSession: {
      setActionHandler(action: string, handler: MediaSessionActionHandler | null) {
        if (action === 'seekto' && handler) throw new TypeError('unsupported');
        handlers.set(action, handler);
      },
      setPositionState(state?: unknown) { positions.push(state) },
    } });
    const state = { time: 100, duration: 600 };
    const { player, fire } = fakePlayer(state);
    mountPlayerMediaSession(player, { id: 1, duration: 600 });
    expect([...handlers.keys()]).toEqual(['play', 'pause', 'seekbackward', 'seekforward']);
    handlers.get('seekforward')!({ action: 'seekforward' });
    expect(state.time).toBe(115);
    handlers.get('seekbackward')!({ action: 'seekbackward', seekOffset: 200 });
    expect(state.time).toBe(0);
    expect(positions[0]).toEqual({ duration: 600, position: 100, playbackRate: 1 });
    state.time = 700; fire('timeupdate');
    expect(positions).toHaveLength(1);
    fire('dispose');
    expect([...handlers.values()].every((handler) => handler === null)).toBe(true);
  });
});

describe('外挂字幕', () => {
  it('能播的轨全挂上，一条都不预先打开', async () => {
    stubFetch(() => ({ subtitles: [
      { playable: true, src: '/sub/1.vtt', language: 'zh', label: '简体' },
      { playable: false, src: '/sub/2.ass', language: 'ja', label: '日语' },
      { playable: true, src: '/sub/3.vtt', label: '繁体' },
    ] }));
    const { player, raw } = fakePlayer({ time: 0, duration: 0 });
    mountPlayerSubtitles(player, 21);
    await flush(); await flush();
    expect(raw.addRemoteTextTrack.mock.calls).toEqual([
      [{ kind: 'subtitles', src: '/sub/1.vtt', srclang: 'zh', label: '简体', default: false }, true],
      [{ kind: 'subtitles', src: '/sub/3.vtt', srclang: '', label: '繁体', default: false }, true],
    ]);
  });
});
