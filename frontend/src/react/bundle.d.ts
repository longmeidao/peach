/* `web/dist/peach-react.js` 的对外契约。
 *
 * Preact 那一侧按 `@peach/react` 引用这份产物，构建时改写成 `/dist/peach-react.js`；
 * `entry.tsx` 按这里的签名实现，两边的类型检查各自对照同一份声明。
 * 配置数据的形状以 `/api/configuration`（`src/peach/routes_configuration.py`）为准。 */

export interface AccessState { mode: 'open' | 'password' | 'legacy' | 'locked'; revision: string }

export interface AccessSettingsProps {
  initial: AccessState;
  receipt(message: string): void;
}

export interface StartupState {
  available: boolean; enabled: boolean; silent: boolean; message: string; desktop: boolean; desktop_message: string;
}

export interface UninstallState {
  available: boolean; full_available: boolean; message: string; data_root: string; directories: string[];
}

export interface PeachProxyState { mode: string; proxy_saved: boolean; needs_selection: boolean }

export interface AutomaticUpdateState {
  mode: string; interval_hours: number; available: boolean; download_available: boolean; error?: string;
}

export interface ReleaseState {
  current_version: string;
  latest_version: string | null;
  channel: string;
  installation: string;
  state: string;
  message: string;
  release_url: string;
  checked_at?: number;
}

export interface UpdateJob {
  state: string; progress: number; message?: string; downloaded?: number; total?: number; version?: string;
}

export interface MediaSource {
  location: string; root: string; path: string; online?: boolean; library?: string; library_icon?: string;
}

export interface ConfigurationFact {
  term: string;
  value: string;
  download_url?: string;
  download_label?: string;
}

export interface ConfigurationData {
  startup?: StartupState;
  uninstall?: UninstallState;
  peach_proxy?: PeachProxyState;
  updates?: ReleaseState;
  update_job?: UpdateJob;
  automatic_updates?: AutomaticUpdateState;
  access?: AccessState;
  editable: boolean;
  /** 不能编辑时给用户看的原因，可编辑时为空。 */
  notice: string;
  /** 设置文件的指纹，保存时带回去，服务端据此拒绝盖掉别处的改动。 */
  revision: string;
  media_dirs: string[];
  media_sources?: MediaSource[];
  windows?: boolean;
  port: number;
  port_editable?: boolean;
  mount_dependencies?: { name: string; available: boolean; download_url: string }[];
  facts: ConfigurationFact[];
}

/** 配置页的一个分组（「通用」「媒体」「网络与访问」「更新与维护」）。 */
export interface ConfigurationGroupProps {
  data: ConfigurationData;
  /** 保存成功后的过去时回执（遗留层的 Toast）。 */
  receipt(message: string): void;
}

/** 一棵挂在遗留容器里的 React 根。`unmount` 之后容器归还给挂载方。 */
export interface ReactMount<P> {
  update(props: P): void;
  unmount(): void;
}

export declare function mountGeneralSettings(el: Element, props: ConfigurationGroupProps): ReactMount<ConfigurationGroupProps>;
export declare function mountMediaSettings(el: Element, props: ConfigurationGroupProps): ReactMount<ConfigurationGroupProps>;
export declare function mountNetworkSettings(el: Element, props: ConfigurationGroupProps): ReactMount<ConfigurationGroupProps>;
export declare function mountMaintenanceSettings(el: Element, props: ConfigurationGroupProps): ReactMount<ConfigurationGroupProps>;
