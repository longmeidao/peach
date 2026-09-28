/* 详情播放器：给两座详情画出来的 `<video>` 挂 Video.js 与全部 Peach 控件。
 *
 * - `mountDetailPlayer` 挂一个 Video.js 实例：片源解析、时长校正、统计面板与加载速度角标、出错时
 *   从分片退回直读、脱盘判定，ready 之后挂设置菜单、拖动预览、Media Session、转圈与字幕。
 * - `mountPlayer` 是舞台播放区的入口：插氛围光画布与统计角标，按作品或关注条目给片源、海报与
 *   上报，返回拆掉这一个播放器的函数。 */
import { api, esc, fmtClock, fmtSize, icon, realDuration } from '@peach/legacy/core';

import {
  mountPlayerAmbient, mountPlayerMediaSession, mountPlayerQualityControl, mountPlayerSeekPreview,
  mountPlayerSpinner, mountPlayerSubtitles,
} from './controls';
import { playerHost } from './host';
import { wirePlayerContextMenu } from './menu';
import { detailPlayer, setDetailPlayer } from './registry';
import {
  averageBitrate, bufferedAhead, createBufferMeter, fmtLoadRate, fmtSpeed, PLAYER_PANEL_EVENT,
  playerSpeedBits, playerStatsOverlayHtml, playerStatsPlot, pushPlayerStat, streamEntries,
} from './stats';
import { detailStreamSession, detailStreamSource, directDetailSource } from './stream';
import { wireFollowTelemetry, wireTelemetry } from './telemetry';
import type { MediaFacts, PlayerItem, PlayerSource, SourceQuality, VjsPlayer } from './types';
import { ensureVideojs } from './videojs';

/** 从小窗展开回来或带 `?t=` 深链进来时接着放的那一刻。 */
export interface PlayerResume { time: number; autoplay: boolean }

export interface DetailPlayerOptions {
  /** 给定片源（关注条目的 `/follow-stream`）；不给就按作品的来源解析。 */
  source?: PlayerSource;
  /** 播放出错时要不要查来源状态判脱盘。关注条目的片源不在本机来源里，不查。 */
  checkSourceStatus?: boolean;
  size?: number | null | undefined;
  poster?: string | undefined;
  qualities?: SourceQuality[] | null;
  /** 清晰度表与字节数，跟默认片源并行解析，回来得比挂载晚。 */
  mediaPromise?: Promise<MediaFacts | null>;
  resume?: PlayerResume | null;
}

/* 统计面板与加载速度角标的定时器。它们画在舞台的媒体框里，播放器进小窗时跟着舞台一起停。 */
let statsTimer: ReturnType<typeof setInterval> | null = null;
let netTimer: ReturnType<typeof setInterval> | null = null;
let netHideTimer: ReturnType<typeof setTimeout> | null = null;

/** 停掉统计面板与角标的刷新。播放器本身不动。 */
export function stopPlayerPanels(): void {
  if (statsTimer) { clearInterval(statsTimer); statsTimer = null }
  if (netTimer) { clearInterval(netTimer); netTimer = null }
  if (netHideTimer) { clearTimeout(netHideTimer); netHideTimer = null }
}

export async function mountDetailPlayer(
  item: PlayerItem, video: HTMLVideoElement, autoplay: boolean, options: DetailPlayerOptions = {},
): Promise<VjsPlayer | null> {
  const existing = detailPlayer();
  if (existing) return existing;
  const host = playerHost();
  const resume = options.resume ?? null;
  if (resume?.autoplay) autoplay = true;
  const statsButton = document.getElementById('playerStatsBtn'), statsPanel = document.getElementById('playerStats');
  const source = () => (options.source ? Promise.resolve(options.source) : detailStreamSource(item));
  /* 拉不到就退回原生 video，和「页面里没有 videojs」是同一个兜底出口。 */
  let videojs;
  try { videojs = await ensureVideojs() } catch {
    video.controls = true;
    source().then((next) => { video.src = next.src; if (autoplay) video.play().catch(() => {}) }).catch(() => {});
    return null;
  }
  const player = videojs(video, {
    controls: true, preload: 'metadata', language: 'zh-CN', responsive: true,
    /* video.js 只认 options 里的海报，不读 video 元素上的 poster 属性；不传，开播前那层本地
       封面就在挂载那一刻被丢掉。 */
    poster: options.poster || host.posterUrl(item),
    controlBar: {
      pictureInPictureToggle: true, currentTimeDisplay: true, timeDivider: true,
      durationDisplay: true, remainingTimeDisplay: false,
    },
  });
  setDetailPlayer(player);
  player.peachItem = item;
  wirePlayerContextMenu(player);
  /* 手机上的画面格按视频自己的比例排（`--peach-video-ratio`）。 */
  player.on('loadedmetadata', () => {
    const tech = player.el()?.querySelector('video');
    if (tech?.videoWidth && tech.videoHeight) player.el().style.setProperty('--peach-video-ratio', `${tech.videoWidth}/${tech.videoHeight}`);
  });
  // 非正时长一律当未知：强行 player.duration(-1) 会被 Video.js 转成 Infinity 并标成直播。
  const expected = realDuration(item.duration);
  const statsHistory = { speed: [] as number[], activity: [] as number[], buffer: [] as number[] };
  /* 关注条目的字节数要回源 HEAD 才知道，跟清晰度表同一趟回来，比挂载晚。码率是速度读数的
     换算系数，所以留一个可以后填的口子，别把它固定在挂载那一刻。 */
  let mediaSize = Number(options.size ?? item.size) || 0;
  const meter = createBufferMeter(averageBitrate(mediaSize, item.duration));
  let statsLoaded = 0;
  let correcting = false;
  const live = () => detailPlayer() === player && !player.isDisposed();
  const enforceDuration = () => {
    if (!expected || correcting || !live()) return;
    const reported = Number(player.duration());
    if (!Number.isFinite(reported) || Math.abs(reported - expected) > Math.max(2, expected * .001)) {
      correcting = true; player.duration(expected); queueMicrotask(() => { correcting = false });
    }
  };
  const segmentedNow = () => String(player.currentSource()?.type || '').includes('mpegurl');
  const updateStats = () => {
    if (!statsPanel || statsPanel.hidden || !live()) return;
    const quality = video.getVideoPlaybackQuality ? video.getVideoPlaybackQuality() : null;
    const rect = video.getBoundingClientRect(), current = `${video.videoWidth || item.width || '?'}×${video.videoHeight || item.height || '?'}`;
    const segmented = segmentedNow();
    const session = detailStreamSession();
    const resources = segmented ? streamEntries(item.id, session) : [];
    const bytes = resources.reduce((n, entry) => n + (entry.transferSize || entry.encodedBodySize || 0), 0);
    const seconds = resources.reduce((n, entry) => n + (entry.duration || 0), 0) / 1000;
    meter.sample(video);
    const speed = playerSpeedBits(player, item.id, session, segmented ? null : meter) || (seconds > 0 ? bytes * 8 / seconds : 0);
    /* 分片流按已完成请求的字节累计；渐进源没有这种请求，按前沿推进折算，码率未知时退到秒。 */
    const loaded = segmented ? bytes : (meter.bitrate > 0 ? meter.bytes() : meter.seconds);
    const activity = Math.max(0, loaded - statsLoaded); statsLoaded = loaded;
    const buffer = bufferedAhead(video);
    pushPlayerStat(statsHistory.speed, speed);
    pushPlayerStat(statsHistory.activity, activity);
    pushPlayerStat(statsHistory.buffer, buffer);
    /* 关注条目没有落盘文件名，容器格式只能从片源 MIME 反推；HLS 已经写在传输一侧，不重复。 */
    const named = String(item.name || '');
    const container = (named.includes('.') ? named.split('.').pop() || ''
      : segmented ? '' : String(player.currentSource()?.type || '').split('/').pop() || '').toUpperCase() || '—';
    const speedText = speed ? `${(speed / 1e6).toFixed(1)} Mbps` : '—';
    const byteScale = segmented || meter.bitrate > 0;
    const loadedRow: [string, string, string] = segmented
      ? ['网络活动', `${bytes ? fmtSize(bytes) : '—'} · ${resources.length} 请求`,
        `最近一秒网络活动 ${activity ? fmtSize(activity) : '0 B'}`]
      : ['已下载', byteScale ? `${fmtSize(loaded)}${mediaSize > 0 ? ` / ${fmtSize(mediaSize)}` : ''}` : `${loaded.toFixed(0)} 秒`,
        byteScale ? `最近一秒下载 ${activity ? fmtSize(activity) : '0 B'}` : `最近一秒下载 ${activity.toFixed(1)} 秒`];
    const rows: [string, string, string?][] = [
      ['视频 ID / 会话', session && !options.source ? `${item.id} / ${session.slice(0, 8)}` : `${item.id}`],
      ['视口 / 帧', `${Math.round(rect.width)}×${Math.round(rect.height)} / ${quality ? `${quality.totalVideoFrames - quality.droppedVideoFrames} of ${quality.totalVideoFrames}` : '—'}`],
      ['当前 / 最佳分辨率', `${current} / ${item.width || video.videoWidth || '?'}×${item.height || video.videoHeight || '?'}`],
      ['编码 / 传输', `${container} / ${segmented ? 'HLS' : 'HTTP Range'}`],
      ['连接速度', speedText,
        playerStatsPlot(statsHistory.speed, 'speed', Math.max(10e6, ...statsHistory.speed), `连接速度 ${speedText === '—' ? '暂无数据' : speedText}`)],
      [loadedRow[0], loadedRow[1],
        playerStatsPlot(statsHistory.activity, 'activity', Math.max(1, ...statsHistory.activity), loadedRow[2])],
      ['缓冲健康', `${buffer.toFixed(1)} 秒`,
        playerStatsPlot(statsHistory.buffer, 'buffer', 30, `当前可连续播放 ${buffer.toFixed(1)} 秒`)],
      ['播放时间', `${fmtClock(video.currentTime)} / ${fmtClock(expected || player.duration())}`],
      ['日期', new Date().toLocaleString()],
    ];
    statsPanel.innerHTML = `<dl>${rows.map(([key, value, plot]) =>
      `<dt>${esc(key)}</dt><dd${plot ? ' class="playerstatsmetric"' : ''}>${plot || ''}<span>${esc(value)}</span></dd>`).join('')}</dl>`;
  };
  player.on(['loadstart', 'loadedmetadata', 'durationchange', 'error'], enforceDuration);
  let segmentedSource = false, fallbackUsed = false;
  const netBadge = document.getElementById('playerNet');
  const updateNet = () => {
    if (!netBadge || player.isDisposed()) return;
    const segmented = segmentedNow();
    if (!segmented) meter.sample(video);
    const bits = playerSpeedBits(player, item.id, detailStreamSession(), segmented ? null : meter);
    const rate = segmented ? fmtSpeed(bits) : fmtLoadRate(bits, bufferedAhead(video));
    netBadge.innerHTML = `${icon('gauge')}<span class="sr-only">加载速度</span><span>${esc(rate)}</span>`;
  };
  const showNet = () => {
    if (!netBadge || !netBadge.isConnected) return;
    netBadge.hidden = false; updateNet();
    if (netTimer) clearInterval(netTimer);
    netTimer = setInterval(updateNet, 500);
  };
  const hideNet = () => {
    if (!netBadge) return;
    if (netHideTimer) clearTimeout(netHideTimer);
    netHideTimer = setTimeout(() => { netBadge.hidden = true; if (netTimer) { clearInterval(netTimer); netTimer = null } }, 1400);
  };
  player.on(['loadstart', 'progress', 'waiting', 'stalled'], showNet);
  player.on(['canplay', 'playing'], () => { updateNet(); hideNet() });
  player.on('error', () => {
    if (segmentedSource && !fallbackUsed && !player.isDisposed()) {
      fallbackUsed = true; segmentedSource = false;
      player.src(directDetailSource(item));
      if (autoplay) player.play()?.catch(() => {});
      return;
    }
    // 播到一半掉盘时 video 元素只报通用错误；来源状态才分得清脱盘和文件损坏。
    if (options.checkSourceStatus === false) return;
    void host.loadSourceStatus().then((status) => {
      if (status[String(item.location)] !== false || player.isDisposed()) return;
      player.error({ code: 2, message: `脱盘模式 · ${host.offlineReason(String(item.location))}` });
    });
  });
  player.ready(() => {
    enforceDuration();
    const updateQualities = mountPlayerQualityControl(player, video, item.height, options.qualities ?? null);
    options.mediaPromise?.then((next) => {
      if (!live()) return;
      updateQualities?.(next?.qualities?.length ? next.qualities : null);
      const size = Number(next?.size) || 0;
      if (size > 0 && !mediaSize) { mediaSize = size; meter.bitrate = averageBitrate(size, item.duration) }
    }).catch(() => {});
    mountPlayerSeekPreview(player, item, { thumbnail: !options.source });
    mountPlayerMediaSession(player, item);
    mountPlayerSpinner(player);
    if (!options.source) mountPlayerSubtitles(player, item.id);
    if (statsButton) statsButton.hidden = false;
  });
  if (statsButton && statsPanel) {
    const closeStats = () => {
      if (statsPanel.hidden) return;
      statsPanel.hidden = true; statsButton.setAttribute('aria-pressed', 'false');
      if (statsTimer) { clearInterval(statsTimer); statsTimer = null }
    };
    statsButton.onclick = () => {
      if (!statsPanel.hidden) { closeStats(); return }
      document.dispatchEvent(new CustomEvent(PLAYER_PANEL_EVENT, { detail: 'stats' }));
      statsPanel.hidden = false; statsButton.setAttribute('aria-pressed', 'true');
      updateStats(); if (statsTimer) clearInterval(statsTimer); statsTimer = setInterval(updateStats, 1000);
    };
    const closeStatsForOtherPanel = (event: Event) => { if ((event as CustomEvent<string>).detail !== 'stats') closeStats() };
    document.addEventListener(PLAYER_PANEL_EVENT, closeStatsForOtherPanel);
    player.on('dispose', () => document.removeEventListener(PLAYER_PANEL_EVENT, closeStatsForOtherPanel));
  }
  source().then((next) => {
    if (!live()) return;
    segmentedSource = String(next.type || '').includes('mpegurl');
    player.src(next);
    enforceDuration(); setTimeout(enforceDuration, 0); setTimeout(enforceDuration, 250);
    if (resume && resume.time > 0) player.one('loadedmetadata', () => { if (!player.isDisposed()) player.currentTime(resume.time) });
    if (autoplay) player.play()?.catch(() => {});
  }).catch(() => {});
  return player;
}

/** 关注条目里的一份媒体（组里的第几条视频）。 */
export interface PlayerMedia { index: number; media_type?: string; size?: number | null }

export interface MountPlayerOptions {
  kind: 'item' | 'follow';
  item: PlayerItem;
  media?: PlayerMedia | null;
  /** 不给就按设置（`detailAutoplay`）。 */
  autoplay?: boolean;
  resume?: PlayerResume | null;
  /** 登记一条撤销，舞台整块拆掉时调。 */
  register?: (dispose: () => void) => void;
  /** 这个播放器已经被小窗接走：拆播放区时不销毁它。 */
  handedOff?: (player: VjsPlayer) => boolean;
}

/** 舞台播放区的入口：给详情岛画好的 `<video>` 挂播放器，返回拆掉它的函数。
 *
 *  氛围光画布与统计角标在挂载之前插进媒体框：Video.js 一包，`video` 的父级就换成它自己的那层了。
 *  - 作品（`item`）：片源由 `mountDetailPlayer` 按来源解析，海报是本地图，第一次开播记一次播放，
 *    离开位置与真实观看由 `wireTelemetry` 随播放写回侧栏。
 *  - 关注（`follow`）：片源是 `/follow-stream`，清晰度与字节数（`/follow-qualities`）跟默认片源并行
 *    解析——它要回源抓详情、再 HEAD 一次正片，不能挡住播放器挂载。
 *  返回的清理在岛卸下这块媒体区时调：换一份媒体只拆这一个播放器；被小窗接走的不拆。 */
export function mountPlayer(video: HTMLVideoElement, options: MountPlayerOptions): () => void {
  const { kind, item, media = null, register, handedOff } = options;
  const host = playerHost();
  video.parentElement?.insertAdjacentHTML('afterbegin', '<canvas class="ambientcanvas" width="32" height="18"></canvas>');
  video.insertAdjacentHTML('beforebegin', playerStatsOverlayHtml());
  let detail: DetailPlayerOptions = { resume: options.resume ?? null };
  if (kind === 'follow') {
    detail = {
      ...detail,
      source: { src: `/follow-stream?id=${item.id}${media ? `&media=${media.index}` : ''}`, type: media?.media_type || item.media_type || 'video/mp4' },
      checkSourceStatus: false, size: media?.size, poster: item.thumb_url,
      mediaPromise: (api(`/follow-qualities?id=${encodeURIComponent(item.id)}`) as Promise<MediaFacts | null>).catch(() => null),
    };
  } else {
    const poster = host.posterUrl(item);
    if (poster) video.poster = poster;
    video.addEventListener('play', () => {
      const stage = host.stage();
      if (stage && !stage.dataset.c) {
        stage.dataset.c = '1';
        void (api('/api/play', { method: 'POST', body: JSON.stringify({ id: item.id }) }) as Promise<unknown>).catch(() => {});
      }
    });
    wireTelemetry(item, video, { watched: '#watched', mark: '#mark', ratio: '#ratioTxt', ...(register ? { register } : {}) });
  }
  let player: VjsPlayer | null = null, released = false, stopAmbient = () => {};
  // 进小窗时播放器不销毁，氛围采样要跟着舞台一起停，别对着已经拆掉的画布继续画。
  register?.(() => stopAmbient());
  const release = () => {
    if (!player || handedOff?.(player)) return;
    if (detailPlayer() === player) { setDetailPlayer(null); stopPlayerPanels() }
    if (!player.isDisposed()) { try { player.pause(); player.dispose() } catch { /* 已拆 */ } }
  };
  void mountDetailPlayer(item, video, options.autoplay ?? host.settings().detailAutoplay, detail).then((mounted) => {
    player = mounted;
    // 挂载还没回来岛就换了媒体：这一个一出来就拆掉。
    if (released) { release(); return }
    stopAmbient = mountPlayerAmbient(video);
    player?.one('dispose', stopAmbient);
    video.addEventListener('emptied', stopAmbient, { once: true });
    if (kind === 'follow') wireFollowTelemetry(item, video);
  });
  return () => { released = true; release() };
}
