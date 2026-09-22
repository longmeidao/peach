/* `web/dist/peach-react.js` 的对外契约。
 *
 * `frontend/src/islands.ts` 按 `@peach/react` 引用这份产物，构建时改写成 `/dist/peach-react.js`；
 * `entry.tsx` 按这里的签名实现，两边的类型检查各自对照同一份声明。
 * 配置数据的形状以 `/api/configuration`（`src/peach/routes_configuration.py`）为准。 */
import type { QualityGoal } from './quality-goals/quality-goals';

export interface AccessState { mode: 'open' | 'password' | 'legacy' | 'locked'; revision: string }

export interface TunnelState {
  enabled: boolean;
  state: 'stopped' | 'starting' | 'running' | 'error';
  url: string;
  error: string;
  available: boolean;
  mode: 'quick' | 'named';
  /** 命名隧道绑定的公开主机名，临时链接模式下为空。 */
  hostname: string;
  /** 隧道令牌存没存过。令牌本身不回传，页面只据此显示已保存。 */
  token_set: boolean;
  /** 这台部署能不能用命名隧道；独立包为 false，那一块整个不渲染。 */
  named_available: boolean;
}

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

/** 人物资料页上的一枚外部入口。`placeholder` 是这一站的模板里该填的那个占位符。 */
export interface EntryLinkSite {
  key: string;
  label: string;
  placeholder: string;
  enabled: boolean;
  template: string;
  default_template: string;
}

export interface EntryLinksState { sites: EntryLinkSite[] }

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
  entry_links?: EntryLinksState;
  updates?: ReleaseState;
  update_job?: UpdateJob;
  automatic_updates?: AutomaticUpdateState;
  access?: AccessState;
  tunnel?: TunnelState;
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

/** 配置页只要遗留层的 Toast：保存是写操作，回执归全站那一份。 */
export interface ConfigurationProps {
  /** 保存成功后的过去时回执（遗留层的 Toast）。 */
  receipt(message: string): void;
  /** 让安装教程重新出现：跳过与折叠归位、撤回账本标记，再关掉设置弹层。 */
  reopenTutorial(): Promise<void>;
}

/** 配置页的一个分组（「通用」「媒体」「网络与访问」「更新与维护」）。
 *  重开教程那一半只归「更新与维护」，别的分组不必接它。 */
export interface ConfigurationGroupProps extends Pick<ConfigurationProps, 'receipt'> {
  data: ConfigurationData;
}

/** 一棵挂在遗留容器里的 React 根。`unmount` 之后容器归还给挂载方。 */
export interface ReactMount<P> {
  update(props: P): void;
  unmount(): void;
}

/** 整页归 React 的那些页面（`islands.ts` 的 React 档）。
 *
 * `prefetch` 把首屏写进共用的 Query 缓存，`mount` 创建这一页的 React 根。两件事分开是因为
 * 「取完数才画」的契约：遗留层已经铺了骨架，页面自己再转一次圈就是同一次进入里两段等待态。 */
export interface ReactPage<P> {
  /** 首屏取数。中止后抛 `AbortError`，挂载方据此放弃这一次。 */
  prefetch(props: P, signal: AbortSignal): Promise<void>;
  mount(el: Element, props: P): ReactMount<P>;
}

/** 活动页没有来自遗留层的助手：整页的数据都来自 `/api/tasks`。 */
export type ActivityProps = Record<string, never>;

/** 高清版目标页仍由遗留层提供的能力。全是纯函数或导航，页面不持有它们的状态。 */
export interface QualityGoalsProps {
  /** 打开作品详情（遗留层的整页视图，含播放器与队列）。 */
  openItem(id: number): void;
  /** 番号 + 版次徽章 + 标题的 HTML。非 JAV 条目退化成转义后的文件名。 */
  javTitleHtml(item: QualityGoal): string;
  /** 同一条目的纯文本形态，用于无障碍名称。 */
  javDisplayName(item: QualityGoal): string;
  /** 来源徽标（含计费标记）的 HTML。 */
  srcBadge(location: string, cost: string): string;
}

/** 统计页仍由遗留层提供的能力。都是纯函数或导航，页面不持有它们的状态。 */
export interface StatsProps {
  /** 标签键到界面上的名称（`web/js/tags.js` 的 `tagLabel`）。 */
  tagLabel(key: string): string;
  /** 点一个内容标签：回目录并按它筛选。整页换成目录由遗留壳做。 */
  onTag(key: string): void;
  /** 打开媒体文件夹设置。没有视频或没有存储来源时空态里的那个去处。 */
  openMediaSettings(): void;
  /** 这台机器能不能改配置。不能改时空态不给「添加媒体文件夹」。 */
  configurable: boolean;
}

/** 口味页仍由遗留层提供的能力。都是导航、查表或回执，页面不持有它们的状态。 */
export interface TasteProps {
  /** 点一条名次：回目录并按它筛选。`kind` 是 `tag`／`creator`／`performer`。 */
  onSignal(kind: string, name: string): void;
  /** 去口味总结里指的那一页（`#/manage/scraping` 这类遗留路由）。 */
  navigate(route: string): void;
  /** 写操作在服务端落地之后的过去时回执。 */
  toast(message: string): void;
  /** 实体圆标的内层 HTML：有图走图，没图退到首字母。遗留层那份唯一的回落链实现。 */
  avatarInner(
    name: string,
    entity: { id: number; has_image: boolean; avatar_focus?: unknown } | null,
    representativeAssetId: number | null,
    kind: string,
  ): string;
  /** 从引导流程进来（`?onboarding=1`）：浏览记录导入指南直接展开。 */
  onboarding: boolean;
}

/** 来源和凭证页只要遗留层的 Toast：保存与撤销是写操作，回执归全站那一份。 */
export interface ScrapingProps {
  /** 写操作在服务端落地之后的过去时回执。 */
  toast(message: string): void;
}

/** 关注管理页。
 *
 *  地址栏与个人偏好在这里分成两组：`tab`／`page`／`sort`／`dir` 外面链接得过来，跟着地址
 *  走；`pageSize`／`layout` 是这台浏览器的习惯，跟着 `appSettings` 走。两组都由壳持有存储、
 *  React 持有实时状态，各只有一份。 */
export interface FollowManageProps {
  /** 地址栏此刻带着的页签（`list`／`add`／`source`）。 */
  tab: string;
  page: number;
  sort: string;
  dir: string;
  /** 把这四项写回地址栏。空串表示这一项此刻就是默认值，壳不写进去。 */
  route(params: { tab: string; page: number; sort: string; dir: string }): void;
  /** 这台浏览器的偏好当前值。 */
  pageSize: number;
  layout: string;
  /** 偏好改了：存储归壳（`appSettings`），页面不自己写一份。 */
  savePreference(patch: { pageSize?: number; layout?: string }): void;
  /** 写操作在服务端落地之后的过去时回执。 */
  toast(message: string): void;
  /** 去「看更新」那一页（`/follow`）。整页换成哪一屏仍归遗留壳。 */
  openFollow(): void;
  /** 账本只读：这台机器只能浏览，写操作全部不给点。 */
  readOnly: boolean;
  readOnlyMessage: string;
  /** 写入端上这一页的地址。取不到时门禁里不给去处。 */
  writerUrl: string;
}

/** 人工复核页。
 *
 *  `category` 是唯一进地址栏的那一项：十个分类是固定的一组身份，「在看哪一条队列」链接
 *  得过来，刷新也要还原。分组、筛选与页码是这一刻的看法，队列又是消耗性的（判一条就少
 *  一条），写进地址栏分享出去只会指向另一批东西。 */
export interface ReviewProps {
  /** 地址栏此刻带着的分类。不认识的值退回默认那一档。 */
  category: string;
  /** 把分类写回地址栏。空串表示这一项此刻就是默认值，壳不写进去。 */
  route(params: { category: string }): void;
  /** 打开作品详情（遗留层的整页视图，含播放器与队列）。 */
  openItem(id: number): void;
  /** 打开实体资料页。`kind` 是 `creator`／`performer`。 */
  openEntity(kind: string, name: string): void;
  /** 在资源管理器里显示这个文件。成功由遗留层自己发回执，失败回一句原因。 */
  revealSource(id: number): Promise<string>;
  /** 实体圆标的内层 HTML：有图走图，没图退到首字母。遗留层那份唯一的回落链实现。 */
  avatarInner(
    name: string,
    entity: { id: number; has_image: boolean; avatar_focus?: unknown } | null,
    representativeAssetId: number | null,
    kind: string,
  ): string;
  /** 写操作在服务端落地之后的过去时回执。 */
  toast(message: string): void;
  /** 账本只读：这台机器只能浏览，判定与收录全部不给点，进页面也不发那一次自动落库。 */
  readOnly: boolean;
  readOnlyMessage: string;
  /** 写入端上这一页的地址。取不到时门禁里不给去处。 */
  writerUrl: string;
}

/** 扫描与采集。同一份数据两个读者，所以同一个名字挂两种形态：数据管理页那张卡片，
 *  和目录页顶上那条横幅（`mode: 'notice'`）。 */
export interface LibraryProcessingProps {
  /** 任务跑完时的一次通知。同一趟按 `job_id` 只报一次，谁先看到结束谁报。 */
  toast(message: string): void;
  /** 这一趟从运行走到终态：让遗留层重画数据管理页那几个计数。 */
  onComplete?(): void;
  /** 画成目录页顶上那条横幅，而不是数据管理页那张卡片。 */
  mode?: 'notice';
  /** 卡片闲着时也接着问：任务由后台自己起，页面要认出「现在跑起来了」。 */
  monitor?: boolean;
}

/** 换头像：资料页圆框角上那个加号，连同它点开的那一屏候选。 */
export interface AvatarPickerProps {
  /** 实体类型（`performer`／`creator`）。 */
  kind: string;
  entityId: number;
  /** 页面上显示的这个人的名字，用在无障碍名称和那一句说明里。 */
  name: string;
  /** 换成功后让宿主重画头像。遗留层传的是「重新进这一页」。 */
  onPicked(): void;
}

export interface ReactPages {
  activity: ReactPage<ActivityProps>;
  'avatar-picker': ReactPage<AvatarPickerProps>;
  configuration: ReactPage<ConfigurationProps>;
  'follow-manage': ReactPage<FollowManageProps>;
  'library-processing': ReactPage<LibraryProcessingProps>;
  'quality-goals': ReactPage<QualityGoalsProps>;
  review: ReactPage<ReviewProps>;
  scraping: ReactPage<ScrapingProps>;
  stats: ReactPage<StatsProps>;
  taste: ReactPage<TasteProps>;
}

export declare const pages: ReactPages;
