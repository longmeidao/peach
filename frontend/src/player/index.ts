/* 播放器模块（ADR-0031 第 11a 步）：命令式 TypeScript，不进 React 渲染。
 *
 * Video.js 会把 `<video>` 包进自己的 div、在里面插控制条，DOM 归它；React 只给它一块宿主。
 * 舞台播放区在 effect 里调 `mountPlayer(video, options)`，拿回拆掉它的函数；沉浸模式只用片源、
 * 会话与上报这几样。 */
export type { PlayerHost, PlayerSettings } from './host';
export { configurePlayer } from './host';
export type { PlayerMenuHooks } from './menu';
export { closePlayerMenu, configurePlayerMenu } from './menu';
export { applyAmbientMode, applyTheaterMode, clickPlayerControl } from './controls';
export type { DetailPlayerOptions, MountPlayerOptions, PlayerMedia, PlayerResume } from './detail-player';
export { mountDetailPlayer, mountPlayer, stopPlayerPanels } from './detail-player';
export { detailPlayer, setDetailPlayer } from './registry';
export { fmtSpeed, streamSpeedBits } from './stats';
export {
  cancelDetailStream, cancelStreamSession, directStreamSource, newStreamSession, playableStreamSource,
} from './stream';
export type { TelemetryOptions } from './telemetry';
export { wireFollowTelemetry, wireTelemetry } from './telemetry';
export type { PlayerItem, VjsPlayer } from './types';
export { ensureVideojs } from './videojs';
