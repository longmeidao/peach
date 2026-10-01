/* 设置面板岛（`settings-panel.tsx`）与壳之间的接缝。
 *
 * 界面偏好只有一份：壳在启动时归一化好的 `appSettings`，经 `createSettingsStore` 递进来
 * （`frontend/src/settings-store.ts`）。面板读 `store.value`、原地改字段、`store.save()` 落盘，
 * 再用 `changed(effect)` 告诉壳这一下要跟着做什么——重画网格、重取目录、换主题、重排侧栏，
 * 这些都还是壳的事。跟账本走的那几项（侧栏顺序、合集开关、首次采集范围、头像刷新、搜索记录
 * 条数）由面板经 `/api/settings` 写，成功后同样落进这一份对象。 */
import type { SettingsStore } from '../../settings-store';
import type { SyncedSettings } from './settings-data';

export interface GlowSpot { color: string; alpha: number }

export interface HomeGlow {
  on: boolean;
  preset: string;
  strength: number;
  noise: number;
  speed: number;
  soften: number;
  size: number;
  spot1: GlowSpot;
  spot2: GlowSpot;
  spot3: GlowSpot;
}

/** 面板读写的那几项；对象本身还有别的字段，面板不碰。 */
export interface PanelSettings {
  theme: string;
  uiSounds: boolean;
  homeGlow: HomeGlow;
  sidebarOrder: string[];
  batchSize: number;
  defaultSort: string;
  defaultSortDirection: string;
  groupCollapse: boolean;
  javImage: string;
  feedAutoScroll: boolean;
  feedHideGroupCompilations: boolean;
  feedHideSoloCompilations: boolean;
  feedHideExcerpts: boolean;
  hoverDelaySeconds: number;
  detailAutoplay: boolean;
  miniplayer: boolean;
  seekSeconds: number;
  relatedLimit: number;
  searchHistoryLimit: number;
  followInitialDays: number;
  metadataRefreshDays: number;
}

/** 改完一项之后壳要跟着做的事，一项一个名字；落盘已经由面板做过。 */
export type SettingsEffect =
  | 'theme' | 'uiSounds'
  /** 拖光晕拉条的每一步：只排一帧重画侧栏那一层，不碰根。 */
  | 'glowFrame'
  /** 光晕的开关、颜色、恢复默认与松手：侧栏那一层、其余玻璃面和侧栏配色钮一起对齐。 */
  | 'glow'
  | 'batchSize' | 'defaultSort' | 'sortDirection' | 'hoverDelay' | 'seekSeconds'
  | 'groupCollapse' | 'feedAutoScroll' | 'feedCompilations' | 'miniplayer' | 'javImage'
  | 'searchHistoryLimit' | 'sidebarOrder';

/** `[值, 显示名, 字形]`，与壳里各张选项表同形。 */
export type Choice = readonly [value: string, label: string, icon?: string];

export interface SettingsPanelHost {
  store: SettingsStore<PanelSettings>;
  changed(effect: SettingsEffect): void;
  sound(name: 'whoosh' | 'toggle-on'): void;
  /** 侧栏能放的全部入口，`[键, 名称, 字形]`；首页那一项的键是空串。 */
  navCatalog: readonly Choice[];
  themeOptions: readonly Choice[];
  videoLayouts: readonly Choice[];
  followInitialRanges: readonly Choice[];
  /** 视频封面默认大小跟着当前页走（首页与 JAV 各存一份），读写都归壳。 */
  videoLayout(): string;
  setVideoLayout(layout: string): void;
  /** SFW 与增加对比度各有自己的键，不在 `appSettings` 里；改完壳调 `store.notify()`。 */
  censored(): boolean;
  setCensored(on: boolean): void;
  highContrast(): boolean;
  setHighContrast(on: boolean): void;
  /** 光晕预设那一格和侧栏配色卡是同一组色块、同一份写入，由壳画、由壳接。 */
  renderGlowGrid(grid: HTMLElement): void;
  wireGlowGrid(grid: HTMLElement): void;
  receipt(message: string): void;
  failure(message: string, error: unknown): void;
  /** 账本上的那份与本地缓存对账（壳里的 `applySyncedSettings`），启动时壳自己也走这一条。 */
  syncRemote(remote: SyncedSettings): void;
  openConfiguration(): void;
  /** 面板第一次进 DOM：左栏那块玻璃要挂上折射贴图。 */
  attached(panel: HTMLElement): void;
  /** 这台设备能不能改配置（`/healthz` 的 `configurable`）；取不到时是 null。 */
  configurable(): Promise<boolean | null>;
}

export interface SettingsPanelApi {
  /** 打开面板；`section` 给分区名（「界面」「浏览」…）时直接落到那一页。 */
  open(section?: string): void;
  close(): void;
  isOpen(): boolean;
  /** 已经打开时把某一块滚进视野（配色弹层的「详细设置」落到光晕参数）。 */
  reveal(selector: string): void;
}
