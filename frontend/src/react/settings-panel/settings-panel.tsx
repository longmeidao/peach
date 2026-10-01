/* 设置面板岛：顶栏齿轮打开的那一屏浮层，左栏分区、右边一组组设置行。
 *
 * 面板常驻：第一次打开时在 body 末尾建一枚 `[data-settings-host]` 挂上根，之后开合只换
 * `hidden`，分区、滚动位置之外的状态跨次打开保留。界面偏好读写的是壳递进来的那一份
 * `appSettings`（`host.store`），改完一项用 `host.changed(effect)` 告诉壳跟着做什么；跟账本走的
 * 那几项经 `/api/settings` 写（`settings-data.ts`）。
 *
 * 面板不在 `.peach-react` 里：行、开关、下拉、拉条与色块都是全站共用的遗留控件，外观由
 * `settings-panel.css` 与遗留样式表给。只有「这台电脑」那一格的摘要卡是 BoardUI，单独套一层。
 *
 * 每次打开都像重新进一次这一屏：共用控件重画、数值框回到当前值、两份机器状态重取。
 * 焦点先交给关闭钮，Tab 在面板里转圈，关掉后还给打开前那一枚。 */
import {
  useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore,
  type KeyboardEvent, type ReactNode,
} from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { flushSync } from 'react-dom';
import { useQuery } from '@tanstack/react-query';

import {
  attachOverlayScrollbar, closeAnchoredMenu, iconSwapHtml, loadingDotsHtml, moveGlidePane, noteHtml, revealTexts,
  setActionBusy, setIconSwap, spinnerHtml, wireHorizontalScroller,
} from '@peach/legacy/ui';

import { normalizeJavImage } from '../../jav-artwork';
import { boundedPreference } from '../../number-setting';
import { Providers } from '../providers';
import { prefetchConfiguration } from '../settings/configuration';
import { ConfigurationSummary } from '../settings/configuration-summary';
import { GlowSettings } from './glow-settings';
import { RemixIcon } from './icon';
import { IconSwitch, SelectField } from './legacy-controls';
import { NumberSetting } from './number-setting';
import type { Choice, PanelSettings, SettingsPanelApi, SettingsPanelHost } from './settings-panel-api';
import {
  FOLLOW_SCHEDULE_KEY, THUMBNAIL_JOBS_KEY, fetchFollowSchedule, fetchThumbnailJobs, followScheduleCopy,
  refreshPanelData, useSaveFollowSchedule, useSaveSettings, useSaveThumbnailMode, videoThumbnailCopy,
} from './settings-data';
import { SidebarOrder } from './sidebar-order';

/* 左栏的分区，顺序即右边各组的顺序。字形按条目自己的名字取：整列取自 Remix，一家画的笔画
   才一样粗。 */
const SECTIONS = [
  ['界面', 'ri-palette-line'], ['浏览', 'ri-layout-grid-line'], ['播放', 'ri-play-circle-line'],
  ['搜索', 'ri-search-line'], ['关注', 'ri-rss-line'], ['安全', 'ri-shield-check-line'],
  ['这台电脑', 'ri-macbook-line'],
] as const;

const SORT_OPTIONS: readonly Choice[] = [
  ['seed', '随机'], ['rating', '评分'], ['o', '高潮计数'], ['plays', '观看次数'],
  ['dur', '时长'], ['size', '体积'], ['new', '入库时间'], ['played', '观看时间'],
];
const DIRECTION_OPTIONS: readonly Choice[] = [['desc', '降序'], ['asc', '升序']];
const THUMBNAIL_OPTIONS: readonly Choice[] = [['off', '关闭'], ['precise', '精准'], ['coarse', '粗略']];
const METADATA_OPTIONS: readonly Choice[] = [['7', '每周'], ['30', '每月'], ['90', '每季'], ['0', '从不']];
const METADATA_REFRESH_DAYS = [0, 7, 30, 90];
const JAV_IMAGE_OPTIONS: readonly Choice[] = [['cover', '官方封面', ''], ['thumbnail', '预览图', '']];
/* 新作那一行收不收合集由服务端按账本里的设置筛，这里的开关只是镜像：真相在 `/api/settings`。 */
const FEED_COMPILATIONS = [
  ['feedHideGroupSetting', 'feedHideGroupCompilations', '大合集', '新作收起大合集', 'feedHideGroupDescription',
    '多人片段拼成的精选、总集和连发不进新作那一行，也不替它们补封面。'],
  ['feedHideSoloSetting', 'feedHideSoloCompilations', '单人合集', '新作收起单人合集', 'feedHideSoloDescription',
    '只有一位女优的精选与长时间合集，比如「8時間 BEST」。'],
  ['feedHideExcerptSetting', 'feedHideExcerpts', '切片', '新作收起切片', 'feedHideExcerptDescription',
    '把出过的正片剪成十几分钟单卖的，比如ハイライト厂牌。'],
] as const;
type CompilationKey = typeof FEED_COMPILATIONS[number][1];

const FOCUSABLE = 'button:not([disabled]),input:not([disabled]),textarea:not([disabled]),a[href]';

type Machine = 'none' | 'note' | 'summary';
interface View { open: boolean; closing: boolean; epoch: number; tab: number; machine: Machine }

let host: SettingsPanelHost | null = null;
let root: Root | null = null;
let container: HTMLElement | null = null;
let view: View = { open: false, closing: false, epoch: 0, tab: 0, machine: 'none' };
let transition = 0;
let returnFocus: Element | null = null;

function panelRoot(): Root {
  if (!root || !container?.isConnected) {
    root?.unmount();
    container = document.createElement('div');
    container.dataset.settingsHost = '';
    document.body.append(container);
    root = createRoot(container);
  }
  return root;
}

function paint(): void {
  const current = host;
  if (!current) return;
  flushSync(() => panelRoot().render(<Providers><SettingsPanel host={current} view={view} /></Providers>));
}

function update(patch: Partial<View>): void {
  view = { ...view, ...patch };
  paint();
}

/* 「这台电脑」：能在这台设备上改配置时放摘要卡，否则一句话说清去哪儿改。摘要卡一旦挂上就留着；
   判据取回来之前面板已经关了，就退回未挂状态，下次打开重来。 */
async function checkMachine(current: SettingsPanelHost): Promise<void> {
  if (view.machine === 'summary') return;
  const configurable = await current.configurable();
  if (!view.open) return;
  if (!configurable) { update({ machine: 'note' }); return }
  try { await prefetchConfiguration(new AbortController().signal) } catch { /* 摘要卡自己报读取失败 */ }
  if (view.open) update({ machine: 'summary' });
}

function open(section = ''): void {
  const current = host;
  if (!current) return;
  /* 设置这一屏盖住整页，任何还开着的锚定弹层都得先收掉：设置有侧栏的设置钮、配色弹层的
     「详细设置」和快捷键几处入口，收在这里就不会漏掉哪一处。 */
  closeAnchoredMenu();
  transition += 1;
  returnFocus ||= document.activeElement;
  current.sound('whoosh');
  document.documentElement.style.overflow = 'hidden';
  document.body.classList.add('settings-open');
  const requested = SECTIONS.findIndex(([title]) => title === section);
  /* 先发取数再挂根：第一次打开时查询还不存在，这一趟由 `fetchQuery` 建起来，组件挂上去读到
     的就是在途的这一份，不会再发第二趟。 */
  const remote = refreshPanelData();
  update({ open: true, closing: false, epoch: view.epoch + 1, tab: requested >= 0 ? requested : view.tab });
  void remote.then((settings) => { if (settings) current.syncRemote(settings) });
  void checkMachine(current);
  queueMicrotask(() => document.getElementById('settingsClose')?.focus());
}

function close(): void {
  if (!view.open || view.closing) return;
  const ticket = ++transition;
  update({ closing: true });
  const finish = () => {
    if (ticket !== transition || !view.closing) return;
    update({ open: false, closing: false });
    document.documentElement.style.overflow = '';
    document.body.classList.remove('settings-open');
    if (returnFocus instanceof HTMLElement && document.contains(returnFocus)) returnFocus.focus();
    returnFocus = null;
  };
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { queueMicrotask(finish); return }
  container?.querySelector('[data-settings-card]')?.addEventListener('animationend', finish, { once: true });
  setTimeout(finish, 380);
}

const api: SettingsPanelApi = {
  open,
  close,
  isOpen: () => view.open,
  reveal: (selector) => queueMicrotask(() => document.querySelector(selector)?.scrollIntoView({ block: 'nearest' })),
};

export function configureSettingsPanel(next: SettingsPanelHost): SettingsPanelApi {
  host = next;
  paint();
  return api;
}

function trapTab(event: KeyboardEvent<HTMLElement>): void {
  if (event.key !== 'Tab') return;
  /* 没选中的分区整块 hidden，里面的控件拿不到焦点；圈的两头只在看得见的控件里找。 */
  const focusable = [...event.currentTarget.querySelectorAll<HTMLElement>(FOCUSABLE)]
    .filter((node) => node.getClientRects().length > 0);
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
}

const tabId = (index: number) => `settings-tab-${index}`;
const groupId = (index: number) => index === SECTIONS.length - 1 ? 'machineGroup' : `settings-group-${index}`;

/* 左栏当前项由一块滑过去的玻璃标出来，和左侧抽屉是同一件事的两种形态。坐标取 `offsetTop`
   不取屏幕坐标：面板开合自带一段缩放动画，量屏幕坐标会把正在走的那一下吃进来。玻璃跟着指针走，
   指针离开这一列就滑回当前那格；触点没有悬停，碰一下就滑过去等于替用户点了一次，所以挡在外面。 */
function SettingsNav({ tab, epoch, onSelect }: { tab: number; epoch: number; onSelect(index: number): void }) {
  const nav = useRef<HTMLDivElement | null>(null);
  const glide = useRef<HTMLSpanElement | null>(null);
  const box = useRef<{ x: number; y: number; w: number; h: number } | null>(null);
  const shown = useRef(tab);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);

  const place = (active: HTMLElement | null | undefined, animate: boolean) => {
    const pane = glide.current;
    if (!pane) return;
    if (!active || !active.offsetHeight) { pane.hidden = true; return }
    pane.hidden = false;
    const next = { x: active.offsetLeft, y: active.offsetTop, w: active.offsetWidth, h: active.offsetHeight };
    const from = box.current;
    box.current = next;
    moveGlidePane(pane, animate ? from : null, next, 'y');
  };
  const placeRef = useRef(place);
  placeRef.current = place;

  useLayoutEffect(() => {
    const node = nav.current;
    if (!node) return undefined;
    wireHorizontalScroller(node);
    /* 面板收着时这一栏是零尺寸，量不到落点；露出来那一帧、窄屏断点换宽度时都由这一条对齐。 */
    const observer = new ResizeObserver(() => placeRef.current(buttons.current[shown.current], false));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  useLayoutEffect(() => {
    const moved = shown.current !== tab;
    shown.current = tab;
    placeRef.current(buttons.current[tab], moved);
  }, [tab, epoch]);

  const keys = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const count = SECTIONS.length;
    let next = index;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % count;
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index + count - 1) % count;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = count - 1;
    else return;
    event.preventDefault();
    onSelect(next);
    buttons.current[next]?.focus();
  };

  /* 整块是一个 tablist：小标题写成 presentation，不占 tab 的位置，方向键从头走到尾。 */
  return (
    <div data-settings-nav="" data-glass-pane="" role="tablist" aria-label="设置分区" ref={nav}
      onPointerLeave={(event) => { if (event.pointerType !== 'touch') place(buttons.current[shown.current], true) }}>
      <span data-settings-glide="" aria-hidden="true" hidden ref={glide} />
      <p data-settings-nav-caption="" role="presentation">设置</p>
      {SECTIONS.map(([title, icon], index) => (
        <button type="button" role="tab" key={title} id={tabId(index)} aria-controls={groupId(index)}
          aria-selected={index === tab} tabIndex={index === tab ? 0 : -1}
          ref={(node) => { buttons.current[index] = node }}
          onClick={() => onSelect(index)} onKeyDown={(event) => keys(event, index)}
          onPointerEnter={(event) => { if (event.pointerType !== 'touch') place(event.currentTarget, true) }}>
          <RemixIcon name={icon} />{title}
        </button>
      ))}
    </div>
  );
}

function Group({ index, tab, children }: { index: number; tab: number; children: ReactNode }) {
  return (
    <section data-setting-group="" id={groupId(index)} role="tabpanel" aria-labelledby={tabId(index)} hidden={index !== tab}>
      <h3>{SECTIONS[index][0]}</h3>
      {children}
    </section>
  );
}

/** 一行开关：整行是 label，点哪儿都切。说明那一句的 id 默认取开关 id 去掉 `Setting` 再接 `Description`。 */
function ToggleRow({ id, title, description, describedBy = `${id.replace(/Setting$/, '')}Description`, checked, onToggle }: {
  id: string; title: string; description: string; describedBy?: string; checked: boolean; onToggle(on: boolean): void;
}) {
  return (
    <label data-setting-row="">
      <span><b>{title}</b><small id={describedBy}>{description}</small></span>
      <input data-toggle="" type="checkbox" id={id} role="switch" aria-describedby={describedBy}
        checked={checked} onChange={(event) => onToggle(event.target.checked)} />
    </label>
  );
}

function Row({ title, description, kind, children }: {
  title: string; description?: ReactNode; kind?: 'sort' | 'related'; children: ReactNode;
}) {
  return (
    <div data-setting-row="" data-setting-sort={kind === 'sort' ? '' : undefined}
      data-setting-related={kind === 'related' ? '' : undefined}>
      <span><b>{title}</b>{typeof description === 'string' ? <small>{description}</small> : description}</span>
      {children}
    </div>
  );
}

const Html = ({ html, ...props }: { html: string; id?: string; 'aria-live'?: 'polite' }) =>
  <small {...props} dangerouslySetInnerHTML={{ __html: html }} />;
const savingHtml = () => `${spinnerHtml('保存中')}<span>正在保存…</span>`;
const errorText = (error: unknown, fallback: string) => (error instanceof Error && error.message) || fallback;

function SettingsPanel({ host: current, view: shown }: { host: SettingsPanelHost; view: View }) {
  const version = useSyncExternalStore(current.store.subscribe, current.store.version);
  const settings = current.store.value;
  const panel = useRef<HTMLElement | null>(null);
  const card = useRef<HTMLDivElement | null>(null);
  const head = useRef<HTMLDivElement | null>(null);
  const scroll = useRef<HTMLDivElement | null>(null);
  const resync = useRef<(() => void) | null>(null);
  const lastTab = useRef(shown.tab);

  /* 标题下那道影子的门槛是那段留白自己：它长在这一栏的上内边距上，滚掉它就等于两块重合，
     差 4px 时点亮。留白的值只写在 `--settings-gap` 一处，这里读它。 */
  const fade = () => {
    const [box, body] = [card.current, scroll.current];
    if (!box || !body) return;
    const gap = parseFloat(getComputedStyle(box).getPropertyValue('--settings-gap')) || 0;
    box.toggleAttribute('data-scrolled', body.scrollTop > Math.max(gap - 4, 0));
  };
  const fadeRef = useRef(fade);
  fadeRef.current = fade;

  useLayoutEffect(() => {
    const body = scroll.current;
    if (!body || !panel.current) return undefined;
    resync.current = attachOverlayScrollbar(body) ?? resync.current;
    current.attached(panel.current);
    const listener = () => fadeRef.current();
    body.addEventListener('scroll', listener, { passive: true });
    return () => body.removeEventListener('scroll', listener);
  }, [current]);
  /* 换分区、每次打开都回到顶上；换了分区时标题逐字揭示，只开合不放。 */
  useLayoutEffect(() => {
    const moved = lastTab.current !== shown.tab;
    lastTab.current = shown.tab;
    if (scroll.current) scroll.current.scrollTop = 0;
    if (moved && head.current) revealTexts(head.current, 'h2');
    fadeRef.current();
  }, [shown.tab, shown.epoch]);
  /* 换分区、展开收起一组都只切 `hidden`，滚动条的观察器只看子树增删，内容长短变了它不知道。
     每次画完按新的内容长度重量一遍滑块和两端渐隐。 */
  useLayoutEffect(() => { resync.current?.() });

  const epoch = shown.epoch;
  const select = (index: number) => { if (index !== view.tab) update({ tab: index }) };
  const save = () => current.store.save();

  return (
    <section data-settings-panel="" id="settingsPanel" hidden={!shown.open} aria-modal="true" role="dialog"
      aria-labelledby="settingsTitle" data-closing={shown.closing ? '' : undefined} ref={panel} onKeyDown={trapTab}
      onClick={(event) => { if (event.target === event.currentTarget) close() }}>
      <div data-settings-card="" ref={card}>
        <div data-settings-head="" ref={head}>
          <h2 id="settingsTitle">{SECTIONS[shown.tab][0]}</h2>
          <button type="button" id="settingsClose" aria-label="关闭设置" onClick={close}>
            <svg viewBox="0 0 24 24"><use href="#i-x" /></svg>
          </button>
        </div>
        <SettingsNav tab={shown.tab} epoch={epoch} onSelect={select} />
        <div data-settings-scroll="" ref={scroll}>
          <Group index={0} tab={shown.tab}>
            <Row title="主题" description="跟随系统，或固定用浅色、深色。">
              <IconSwitch id="themeSetting" name="theme" legend="主题" options={current.themeOptions} value={settings.theme}
                attr="data-theme-choice" variant="themeswitch" epoch={epoch}
                onChoose={(choice) => { settings.theme = choice; save(); current.changed('theme') }} />
            </Row>
            <div data-setting-row="">
              <label htmlFor="glassContrastSetting"><b>增加对比度</b>
                <small>关闭玻璃折射与透明效果，使用实色背景。</small></label>
              <input type="checkbox" id="glassContrastSetting" data-toggle="" role="switch" checked={current.highContrast()}
                onChange={(event) => current.setHighContrast(event.target.checked)} />
            </div>
            <ToggleRow id="uiSoundsSetting" title="界面音效" checked={settings.uiSounds}
              description="按钮、开关、菜单、弹层和操作回执各配一声轻响。"
              onToggle={(on) => { settings.uiSounds = on; save(); current.changed('uiSounds') }} />
            <ToggleRow id="homeGlowSetting" title="侧栏光晕" checked={settings.homeGlow.on}
              description="左栏玻璃面上那三枚慢慢漂动的光，其余玻璃面跟着取前两枚的颜色。配色在下面或左栏底部那枚配色钮上挑，强调色在配色钮上挑；这里还调强度、颗粒、漂移速度、柔化、大小和每一枚光晕的颜色。浅色主题按同一组颜色淡一档显示。"
              onToggle={(on) => { settings.homeGlow.on = on; save(); current.changed('glow') }} />
            <GlowSettings host={current} version={version} />
            <section data-sidebar-setting="" aria-labelledby="sidebarOrderTitle">
              <span><b id="sidebarOrderTitle">左侧导航</b>
                <small>直接拖动排序；可隐藏入口，也可从具体页面列表重新添加。窄栏和筛选抽屉会保持一致。</small></span>
              <SidebarOrder host={current} />
            </section>
          </Group>
          <BrowseGroup host={current} tab={shown.tab} epoch={epoch} />
          <PlaybackGroup host={current} tab={shown.tab} epoch={epoch} />
          <Group index={3} tab={shown.tab}>
            <SearchHistoryRow host={current} epoch={epoch} />
          </Group>
          <FollowGroup host={current} tab={shown.tab} epoch={epoch} />
          <Group index={5} tab={shown.tab}>
            <ToggleRow id="censorSetting" title="SFW 模式" describedBy="sfwDescription" checked={current.censored()}
              description="模糊、降低饱和度并压暗全站图片和视频，包括封面、头像与详情预览；停止悬停预览。文字、品牌标识和来源图标保持可见。"
              onToggle={(on) => current.setCensored(on)} />
          </Group>
          <Group index={6} tab={shown.tab}>
            <MachineSettings host={current} machine={shown.machine} />
          </Group>
        </div>
      </div>
    </section>
  );
}

interface GroupProps { host: SettingsPanelHost; tab: number; epoch: number }

/* 排序方向那一格叠着两枚箭头，换的只是方向这一件事：整格重写会把旧字形连同它的动画一起丢掉，
   读出来是一次硬切，所以只在这一格还没建起来时写一次。 */
function decorateDirection(field: HTMLElement, ascending: boolean): void {
  const mark = field.querySelector('[data-select-label]');
  if (!mark) return;
  if (!mark.querySelector('[data-icon-swap]')) {
    mark.innerHTML = iconSwapHtml('arrow-up', 'arrow-down', 'a', { className: 'gselectmark', iconClass: 'gselectmark' })
      + '<span data-sort-direction-label></span>';
  }
  setIconSwap(mark, ascending ? 'a' : 'b');
  const label = mark.querySelector('[data-sort-direction-label]');
  if (label) label.textContent = ascending ? '升序' : '降序';
}

function BrowseGroup({ host: current, tab, epoch }: GroupProps) {
  const settings = current.store.value;
  const save = () => current.store.save();
  const random = settings.defaultSort === 'seed';
  const ascending = settings.defaultSortDirection === 'asc';
  return (
    <Group index={1} tab={tab}>
      <Row title="每批作品" description="首页每次加载的作品数量。">
        <div id="batchSizeSetting">
          <NumberSetting key={epoch} id="batchSizeSetting" label="每批作品" value={settings.batchSize}
            onApply={(value) => { settings.batchSize = value || 60; save(); current.changed('batchSize') }} />
        </div>
      </Row>
      <Row title="默认排序" kind="sort"
        description={<small id="sortDirectionHelp">{random ? '随机排序不使用方向。' : '打开首页时使用的排序与方向。'}</small>}>
        <div data-setting-sort-controls="">
          <SelectField id="defaultSortSetting" label="默认排序" options={SORT_OPTIONS} value={settings.defaultSort} epoch={epoch}
            onPick={(value) => { settings.defaultSort = value; save(); current.changed('defaultSort') }} />
          <SelectField id="defaultSortDirectionSetting" label="默认排序方向" options={DIRECTION_OPTIONS}
            value={ascending ? 'asc' : 'desc'} hidden={random} disabled={random} describedBy="sortDirectionHelp" epoch={epoch}
            onPick={(value) => { settings.defaultSortDirection = value; save(); current.changed('sortDirection') }}
            decorate={(field) => decorateDirection(field, ascending)} />
        </div>
      </Row>
      <label data-setting-row=""><span><b>合并分卷与版本</b><small>同一番号的多个分卷或版次只占一张卡，展示第一个。</small></span>
        <input type="checkbox" id="groupCollapseSetting" data-toggle="" role="switch" checked={settings.groupCollapse}
          onChange={(event) => { settings.groupCollapse = event.target.checked; save(); current.changed('groupCollapse') }} />
      </label>
      <Row title="JAV 默认封面" description="首页、接着看和 Mix 等位置共用；缺图时使用另一种封面。">
        <IconSwitch id="javImageSetting" name="jav-image" legend="JAV 默认封面" options={JAV_IMAGE_OPTIONS}
          value={settings.javImage} attr="data-jav-image-choice" variant="javimageswitch" text epoch={epoch}
          onChoose={(choice) => { settings.javImage = normalizeJavImage(choice); save(); current.changed('javImage') }} />
      </Row>
      <Row title="视频封面默认大小" kind="related" description="首页和 JAV 等视频列表共用；小图展示完整封套，大图展示完整正封。">
        <IconSwitch id="javSizeSetting" name="video-size" legend="视频封面默认大小" options={current.videoLayouts}
          value={current.videoLayout()} attr="data-video-layout" variant="javimageswitch" text epoch={epoch}
          onChoose={(layout) => current.setVideoLayout(layout)} />
      </Row>
      <ToggleRow id="feedAutoScrollSetting" title="新作自动滚动" checked={settings.feedAutoScroll}
        description="首页和人物页那一行未入库的新作缓缓向前滚，到头停一下再往回；指针移上去或手动滚过时停下。"
        onToggle={(on) => { settings.feedAutoScroll = on; save(); current.changed('feedAutoScroll') }} />
      {FEED_COMPILATIONS.map(([id, key, label, title, describedBy, description]) => (
        <CompilationToggle key={id} host={current} id={id} settingKey={key} label={label} title={title}
          describedBy={describedBy} description={description} />
      ))}
    </Group>
  );
}

/* 合集开关由服务端判，列表、未读数和补封面排队都跟着它，所以先存到服务端再重画；往返期间开关
   停在新位置、挂忙态，失败退回原位。 */
function CompilationToggle({ host: current, id, settingKey, label, title, describedBy, description }: {
  host: SettingsPanelHost; id: string; settingKey: CompilationKey; label: string; title: string;
  describedBy: string; description: string;
}) {
  const save = useSaveSettings();
  const [pending, setPending] = useState<boolean | null>(null);
  const box = useRef<HTMLInputElement | null>(null);
  const settings: PanelSettings = current.store.value;
  const toggle = (on: boolean) => {
    setPending(on);
    setActionBusy(box.current);
    save.mutate({ [settingKey]: on }, {
      onSuccess: (saved) => {
        settings[settingKey] = saved[settingKey] === true;
        current.store.save();
        current.changed('feedCompilations');
        current.receipt(on ? `新作已收起${label}` : `新作已列出${label}`);
      },
      onError: (error) => current.failure(`保存${label}开关`, error),
      onSettled: () => { setPending(null); setActionBusy(box.current, false) },
    });
  };
  return (
    <label data-setting-row="">
      <span><b>{title}</b><small id={describedBy}>{description}</small></span>
      <input data-toggle="" type="checkbox" id={id} role="switch" aria-describedby={describedBy} ref={box}
        checked={pending ?? settings[settingKey]} onChange={(event) => toggle(event.target.checked)} />
    </label>
  );
}

function PlaybackGroup({ host: current, tab, epoch }: GroupProps) {
  const settings = current.store.value;
  const save = () => current.store.save();
  return (
    <Group index={2} tab={tab}>
      <Row title="悬停放大" description="转圈完成后进入放大预览。">
        <div id="hoverDelaySetting">
          <NumberSetting key={epoch} id="hoverDelaySetting" label="悬停放大" value={settings.hoverDelaySeconds}
            onApply={(value) => {
              settings.hoverDelaySeconds = boundedPreference(value, 0, 60, 5); save(); current.changed('hoverDelay');
            }} />
        </div>
      </Row>
      <ToggleRow id="detailAutoplaySetting" title="打开详情自动播放" checked={settings.detailAutoplay}
        description="打开本地作品或关注视频详情时开始播放；关闭后点击播放按钮开始。"
        onToggle={(on) => { settings.detailAutoplay = on; save() }} />
      <ToggleRow id="miniplayerSetting" title="小窗播放" checked={settings.miniplayer}
        description="离开详情时正在播放的视频缩到角落继续播放；小窗开着时点击其他视频直接在小窗里换片。"
        onToggle={(on) => { settings.miniplayer = on; save(); current.changed('miniplayer') }} />
      <Row title="快进 / 快退" description="卡片预览和详情播放器共用。">
        <div id="seekSecondsSetting">
          <NumberSetting key={epoch} id="seekSecondsSetting" label="快进 / 快退" value={settings.seekSeconds}
            onApply={(value) => { settings.seekSeconds = value || 10; save(); current.changed('seekSeconds') }} />
        </div>
      </Row>
      <VideoThumbnailRow epoch={epoch} />
      <Row title="相关推荐" description="详情下方一次显示的相似作品数量。">
        <div id="relatedLimitSetting">
          <NumberSetting key={epoch} id="relatedLimitSetting" label="相关推荐" value={settings.relatedLimit}
            onApply={(value) => { settings.relatedLimit = value; save() }} />
        </div>
      </Row>
    </Group>
  );
}

/* 视频缩略图采集的档位跟着这台机器走（`/api/thumbnail-jobs`），不存在本地：跑的是这台机器上的
   一条长任务，从另一台设备打开设置要看到的是它正在按什么密度采。采集进度在活动页，这里不轮询。 */
function VideoThumbnailRow({ epoch }: { epoch: number }) {
  const status = useQuery({ queryKey: THUMBNAIL_JOBS_KEY, queryFn: ({ signal }) => fetchThumbnailJobs(signal) });
  const save = useSaveThumbnailMode();
  const reset = save.reset;
  useEffect(() => { reset() }, [epoch, reset]);
  const mode = status.data?.mode || 'off';
  const html = save.isPending ? savingHtml()
    : status.isFetching ? loadingDotsHtml('正在读取状态')
      : save.isError ? escapeHtml(errorText(save.error, '保存失败'))
        : status.isError ? escapeHtml(`状态未取得：${errorText(status.error, String(status.error))}`)
          : status.data ? escapeHtml(videoThumbnailCopy(status.data)) : '读取运行状态…';
  return (
    <Row title="视频缩略图采集" description={<>
      <small>拖动进度条时按时间点看画面。精准每 10 秒一张，粗略每 30 秒一张；两小时的片子约 720 / 240 张，占 20–100 / 7–35 MB。只采集本机磁盘上的片子，网盘上的每张都要回源拉一次。</small>
      <Html id="videoThumbnailState" aria-live="polite" html={html} />
    </>}>
      <SelectField id="videoThumbnailSetting" label="视频缩略图采集" options={THUMBNAIL_OPTIONS}
        value={save.isPending || save.isError ? (save.variables ?? mode) : mode}
        disabled={save.isPending || status.isFetching} epoch={epoch}
        onPick={(value) => save.mutate(value)} />
    </Row>
  );
}

function SearchHistoryRow({ host: current, epoch }: { host: SettingsPanelHost; epoch: number }) {
  const settings = current.store.value;
  const save = useSaveSettings();
  /* 条数跟着账本走（`/api/settings`），所有访问端看到同一个数；本地那份只是镜像。 */
  return (
    <Row title="搜索记录" description="保存在 Peach 账本，所有访问端同步。">
      <div id="searchHistoryLimitSetting">
        <NumberSetting key={epoch} id="searchHistoryLimitSetting" label="搜索记录" value={settings.searchHistoryLimit}
          onApply={(value) => {
            settings.searchHistoryLimit = boundedPreference(value, 0, 50, 10);
            current.store.save();
            current.changed('searchHistoryLimit');
            save.mutate({ searchHistoryLimit: settings.searchHistoryLimit }, { onError: () => {} });
          }} />
      </div>
    </Row>
  );
}

function FollowGroup({ host: current, tab, epoch }: GroupProps) {
  const settings = current.store.value;
  const save = useSaveSettings();
  const initial = useSaveSettings();
  const [initialState, setInitialState] = useState('');
  useEffect(() => { setInitialState('') }, [epoch]);
  /* 服务端按这个数决定要不要重取，所以它跟着账本走；保存期间下拉挂忙态，失败退回原值。 */
  const saveInitialDays = (value: number) => {
    if (initial.isPending) return;
    setInitialState('正在保存…');
    initial.mutate({ followInitialDays: value }, {
      onSuccess: (saved) => {
        if (typeof saved.followInitialDays === 'number') settings.followInitialDays = saved.followInitialDays;
        current.store.save();
        setInitialState('已保存，适用于尚未开始采集的来源。');
        current.receipt('已保存首次采集历史范围');
      },
      onError: (error) => {
        setInitialState(errorText(error, ''));
        current.failure('保存首次采集历史范围', error);
      },
    });
  };
  return (
    <Group index={4} tab={tab}>
      <Row title="首次采集历史范围" description={<>
        <small>按发布时间限制新来源首次导入的内容；范围内不足 30 条时补到 30 条。没有日期的条目仍会导入；已有内容不受影响，支持历史分页的来源可手动加载更早。</small>
        <small id="followInitialDaysState" aria-live="polite">{initialState}</small>
      </>}>
        <SelectField id="followInitialDaysSetting" label="首次采集历史范围" options={current.followInitialRanges}
          value={initial.isPending ? String(initial.variables?.followInitialDays ?? settings.followInitialDays)
            : String(settings.followInitialDays)}
          busy={initial.isPending} epoch={epoch} onPick={(value) => saveInitialDays(Number(value))} />
      </Row>
      <FollowScheduleRow epoch={epoch} />
      <Row title="头像与站点图标刷新" description="创作者头像、来源图标和外链圆标保存在本机，到期后下次显示时重新取一次；视频与图片不保存。">
        <SelectField id="metadataRefreshSetting" label="头像与站点图标刷新" options={METADATA_OPTIONS}
          value={String(settings.metadataRefreshDays)} epoch={epoch}
          onPick={(value) => {
            const days = Number(value);
            settings.metadataRefreshDays = METADATA_REFRESH_DAYS.includes(days) ? days : 30;
            current.store.save();
            save.mutate({ metadataRefreshDays: settings.metadataRefreshDays }, { onError: () => {} });
          }} />
      </Row>
    </Group>
  );
}

/* 关注自动更新的档位与上次运行状态跟着这台机器走（`/api/follow/schedule`）；读取与保存期间整块禁用。 */
function FollowScheduleRow({ epoch }: { epoch: number }) {
  const status = useQuery({ queryKey: FOLLOW_SCHEDULE_KEY, queryFn: ({ signal }) => fetchFollowSchedule(signal) });
  const save = useSaveFollowSchedule();
  const reset = save.reset;
  useEffect(() => { reset() }, [epoch, reset]);
  const data = status.data;
  /* 读取失败时整块停在禁用；保存失败时回到上一次读到的那一档，还能再改。 */
  const busy = save.isPending || status.isFetching || (status.isError && !save.isError);
  const html = save.isPending ? savingHtml()
    : status.isFetching ? loadingDotsHtml('正在读取状态')
      : save.isError ? escapeHtml(errorText(save.error, '保存失败'))
        : status.isError ? escapeHtml(`状态未取得：${errorText(status.error, String(status.error))}`)
          : data ? escapeHtml(followScheduleCopy(data)) : '读取运行状态…';
  return (
    <Row title="关注自动更新" description={<Html id="followScheduleState" aria-live="polite" html={html} />}>
      <div id="followScheduleSetting">
        <NumberSetting key={epoch} id="followScheduleSetting" label="关注自动更新"
          value={data && !busy ? (data.enabled ? data.interval_minutes : 0) : null}
          disabled={data ? !data.available : false}
          onApply={(minutes) => save.mutate(minutes)} />
      </div>
    </Row>
  );
}

function MachineSettings({ host: current, machine }: { host: SettingsPanelHost; machine: Machine }) {
  if (machine === 'summary') {
    return (
      <div id="machineSettings" key="summary">
        <div className="peach-react">
          <ConfigurationSummary openConfiguration={() => { close(); current.openConfiguration() }} />
        </div>
      </div>
    );
  }
  if (machine === 'note') {
    return (
      <div id="machineSettings" key="note" dangerouslySetInnerHTML={{
        __html: noteHtml('媒体文件夹、端口、代理与更新只能在运行 Peach 服务的那台设备上改：在它的浏览器里打开配置页。',
          { label: '在服务端设备修改' }),
      }} />
    );
  }
  return <div id="machineSettings" key="none" />;
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}
