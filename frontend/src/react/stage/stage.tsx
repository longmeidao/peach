/* 舞台岛（ADR-0031 第 11a 步）：详情浮窗 `<dialog id="stage">`、它的进出场、骨架与揭示、两座详情、
 * 播放器与小窗都在这一棵根里。
 *
 * 宿主是 body 末尾一个常驻容器，一棵根常驻；壳只拿 `configureStage` 给的命令式入口（形同图片灯箱
 * 与 Toast），不走 `mountIsland`：那一套是给壳的页面容器用的，容器归壳、换页就被整块重写，而舞台
 * 盖在所有页面之上，小窗还要在换页之后接着放。
 *
 * 每次 `open` 换一枚 `generation`：dialog 按它重建，取数回来时代次不对就作废。两座详情是舞台树里的
 * 子组件，和页面岛共用同一个 QueryClient（`providers.tsx`）。 */
import { useLayoutEffect, useRef, type MouseEvent, type PointerEvent } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { flushSync } from 'react-dom';

import { fitSkeleton, revealTexts } from '@peach/legacy/ui';

import { detailSkeletonBody } from '../../board-skeleton';
import { applyTheaterMode, closePlayerMenu, type PlayerResume } from '../../player';
import { prefetchFollowDetail, type FollowDetailActions, type FollowDetailProps } from '../follow-detail/follow-detail';
import { FollowDetailPage } from '../follow-detail/follow-detail-page';
import { prefetchItemDetail, type ItemDetailActions, type ItemDetailProps } from '../item-detail/item-detail';
import { ItemDetailPage } from '../item-detail/item-detail-page';
import { Providers } from '../providers';
import { Miniplayer } from './miniplayer';
import * as player from './stage-player';
import type { StageApi, StageHost, StagePatch, StageRequest } from './stage-api';

type Phase = 'skeleton' | 'reveal' | 'content';

type Content =
  | { kind: 'item'; props: ItemDetailProps }
  | { kind: 'follow'; props: FollowDetailProps };

interface View {
  generation: number;
  request: StageRequest;
  content: Content;
  /* 骨架 → 淡出（骨架抬成 `[data-stage-fade]` 一层，内容同时清晰起来）→ 内容。取得比显示门槛快时跳过
     中间那一段：从未露面的骨架不该再演一次退场。 */
  phase: Phase;
}

let host: StageHost | null = null;
let root: Root | null = null;
let container: HTMLElement | null = null;
let view: View | null = null;
let generation = 0;
let controller: AbortController | null = null;
/* 关闭键、Escape、点浮窗外面与原生 `cancel` 可能在同一下里各来一次：退场动画期间再要一次，
   会让第二次关闭跳过动画直接拆。 */
let closeRequested = false;
/* 按下那一刻在不在浮窗外面。详情里进度条、音量条和队列都能拖，从控件上拖出边界再松手同样会在
   dialog 上收到一次 click——那是一次拖动的收尾，不是要关窗。 */
let dismissArmed = false;

const stageDialog = (): HTMLDialogElement | null => {
  const el = document.getElementById('stage');
  return el instanceof HTMLDialogElement ? el : null;
};

function stageHost(): StageHost {
  if (!host) throw new Error('舞台还没有接上宿主（configureStage）');
  return host;
}

function stageRoot(): Root {
  if (!root || !container?.isConnected) {
    root?.unmount();
    container = document.createElement('div');
    container.dataset.stageHost = '';
    document.body.append(container);
    root = createRoot(container);
  }
  return root;
}

function paint(): void {
  const at = stageRoot();
  flushSync(() => at.render(<Providers><StageTree view={view} /></Providers>));
}

function StageTree({ view: current }: { view: View | null }) {
  return (
    <>
      {current ? <StageDialog key={current.generation} view={current} /> : null}
      <Miniplayer />
    </>
  );
}

const DetailSkeleton = () => (
  <div data-skeleton="detail" role="status" aria-label="正在读取作品详情" dangerouslySetInnerHTML={{ __html: detailSkeletonBody() }} />
);

/* 点浮窗外面就退出。原生模态里「外面」还是这个 dialog 自己——遮罩归它，落在遮罩上的事件 target
   就是它本人，所以判据取坐标不取 target：按 target 判，浮窗身上任何一块不属于内容的地方都会被算成
   点了外面。只看坐标也不够：播放器全屏后铺满整个视口，浮窗的矩形仍是详情排版里那块，点进度条右段
   或底部控制栏会落在矩形外。所以两条都要成立：target 是 dialog 本身，坐标在浮窗外。 */
function outside(event: MouseEvent | PointerEvent): boolean {
  const dialog = event.currentTarget as HTMLElement;
  if (event.target !== dialog) return false;
  const box = dialog.getBoundingClientRect();
  return event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom;
}

function StageDialog({ view: current }: { view: View }) {
  const ref = useRef<HTMLDialogElement>(null);
  /* 原生 `cancel`（Escape 之外的关闭请求，例如安卓返回手势）与关闭键走同一条路。Escape 本身在
     keydown 上就处理掉了：那里 `preventDefault` 之后浏览器不再派 `cancel`。 */
  useLayoutEffect(() => {
    const dialog = ref.current!;
    const cancel = (event: Event) => { event.preventDefault(); requestClose() };
    dialog.addEventListener('cancel', cancel);
    return () => dialog.removeEventListener('cancel', cancel);
  }, []);
  const { phase, content } = current;
  const body = content.kind === 'item'
    ? <ItemDetailPage {...content.props} />
    : <FollowDetailPage {...content.props} />;
  return (
    <dialog ref={ref} id="stage" data-stage="" aria-label="作品详情"
      onKeyDown={(event) => {
        /* 里层弹层（标签搜索框、右键菜单）先处理 Escape 并 `preventDefault`，这一下就不再关浮窗。 */
        if (event.key !== 'Escape' || event.defaultPrevented) return;
        event.preventDefault();
        requestClose();
      }}
      onPointerDown={(event) => { dismissArmed = outside(event) }}
      onClick={(event) => { if (dismissArmed && outside(event)) requestClose() }}>
      {phase === 'skeleton' ? <DetailSkeleton key="skeleton" /> : null}
      {phase === 'reveal' ? <div key="fade" data-stage-fade="" aria-hidden="true"><DetailSkeleton /></div> : null}
      {phase === 'skeleton' ? null : (
        /* 窄屏下滚的是 `[data-stage-scroll]`，全站那条覆盖式滚动条挂在它的兄弟位置（`<dialog>` 在顶层，
           轨道挂到它外面会落进遮罩底下）；「接着看」是 `[data-stage-grid]` 的兄弟，也得一起装进来。里面那层
           `.peach-react` 不占盒子，token 与 Preflight 从它开始作用。 */
        <div key="content" data-stage-scroll=""><div className="peach-react">{body}</div></div>
      )}
    </dialog>
  );
}

function requestClose(): void {
  if (!view || closeRequested) return;
  closeRequested = true;
  view.request.actions.close();
}

function toggleStageModes(ambient: boolean, theater: boolean): void {
  const dialog = stageDialog();
  dialog?.toggleAttribute('data-ambient', ambient);
  dialog?.toggleAttribute('data-theater', theater);
}

/* 两座详情的动作经舞台包一层：关闭走 `requestClose`；画出来那一刻登记小窗元数据、切氛围光与剧场
   模式；媒体框交给舞台的播放器。续播时刻只给第一次挂上的那一条。 */
function contentFor(request: StageRequest): Content {
  let resume: PlayerResume | null = request.resume ?? null;
  const takeResume = (id: number) => {
    const hit = resume && (request.id == null || request.id === id) ? resume : null;
    resume = null;
    return hit;
  };
  const settings = () => stageHost().player.settings();
  if (request.kind === 'item') {
    const { kind: _kind, resume: _resume, actions: base, ...props } = request;
    const actions: ItemDetailActions = {
      ...base,
      close: requestClose,
      present: (item, queue) => {
        const performers = item.performers as string[] | undefined;
        player.setStageMeta({ kind: 'item', item, title: String(item.title || item.name || ''),
          sub: String(performers?.[0] || item.creator || '未归属') });
        toggleStageModes(settings().ambientMode, settings().theaterMode);
        base.present(item, queue);
      },
      mountPlayer: (frame, item, _media, options) => player.attachStagePlayer(frame, {
        kind: 'item', item, autoplay: options?.autoplay, resume: takeResume(item.id), id: 'vid',
      }),
    };
    return { kind: 'item', props: { ...props, actions } };
  }
  const { kind: _kind, resume: _resume, actions: base, ...props } = request;
  const actions: FollowDetailActions = {
    ...base,
    close: requestClose,
    present: (item, kind) => {
      player.setStageMeta({ kind: 'follow', item, title: item.title || '', sub: item.author || item.source_label || '' });
      toggleStageModes(kind === 'video' && settings().ambientMode, kind === 'video' && settings().theaterMode);
      base.present(item, kind);
    },
    mountPlayer: (frame, item, media, options) => player.attachStagePlayer(frame, {
      kind: 'follow', item, media, poster: item.thumb_url || undefined, onError: options.onError, resume: takeResume(item.id),
    }),
  };
  return { kind: 'follow', props: { ...props, actions } };
}

/* 骨架抬成一层淡出，内容同时从模糊里清晰起来；走完（或 1s 兜底）摘掉那一层。 */
function startReveal(dialog: HTMLDialogElement, mine: number): void {
  const fade = dialog.querySelector<HTMLElement>(':scope > [data-stage-fade]');
  dialog.setAttribute('data-stage-reveal', '');
  dialog.getBoundingClientRect();
  dialog.setAttribute('data-stage-revealing', '');
  let timer = 0;
  const drop = () => {
    clearTimeout(timer);
    fade?.removeEventListener('transitionend', done);
    dialog.removeAttribute('data-stage-reveal');
    dialog.removeAttribute('data-stage-revealing');
    if (view?.generation === mine && view.phase === 'reveal') { view = { ...view, phase: 'content' }; paint() }
  };
  const done = (event: Event) => { if (event.target === fade) drop() };
  fade?.addEventListener('transitionend', done);
  timer = window.setTimeout(drop, 1000);
}

async function open(request: StageRequest): Promise<void> {
  if (view) dispose({ miniplayer: false });
  const mine = ++generation;
  const abort = new AbortController();
  controller = abort;
  closeRequested = false;
  dismissArmed = false;
  player.prepareStageFor(request.kind, request.id ?? Number.NaN);
  view = { generation: mine, request, content: contentFor(request), phase: 'skeleton' };
  paint();
  const dialog = stageDialog();
  if (!dialog) return;
  fitSkeleton(dialog);
  document.body.setAttribute('data-detail-open', '');
  if (!dialog.open) dialog.showModal();
  const content = view.content;
  try {
    if (content.kind === 'item') await prefetchItemDetail(content.props, abort.signal);
    else await prefetchFollowDetail(content.props, abort.signal);
  } catch {
    // 中止就是用户已经走开。其余失败照画：原因和重试的节律都在详情自己手里。
    if (abort.signal.aborted) return;
  }
  if (mine !== generation || !view) return;
  /* 还没到显示门槛就已经取完：直接落内容，隐藏中的占位从未被人看见。 */
  const direct = !!dialog.querySelector('.skeleton-awaiting');
  view = { ...view, phase: direct ? 'content' : 'reveal' };
  paint();
  if (!direct) startReveal(dialog, mine);
  /* 浮窗里那两行标题跟着这一次重画揭示一遍。绕开正在淡出的那一层：骨架照着最终结构画，里面也有
     一个 `[data-stage-side-content]`，按文档顺序找的话拿到的是它。 */
  revealTexts(dialog, ':scope>:not([data-stage-fade]) [data-reveal-line]');
  /* 骨架里没有可聚焦的元素，`showModal()` 只能把焦点给 dialog 本身；内容到了交给关闭键。 */
  const active = document.activeElement;
  if (active === dialog || !dialog.contains(active)) dialog.querySelector<HTMLElement>('#closeStage')?.focus();
}

/* 详情浮窗的退场跟设置弹层同一条：`data-closing` 让 `board-dialog-out` 和遮罩淡出演完，再拆。等待有
   上限：`animation` 被别的规则关掉时 animationend 不会来。 */
function exit(): Promise<void> {
  const dialog = stageDialog();
  if (!dialog?.open || dialog.hasAttribute('data-closing') || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return Promise.resolve();
  }
  dialog.setAttribute('data-closing', '');
  return new Promise((resolve) => {
    let timer = 0;
    const done = () => { clearTimeout(timer); dialog.removeEventListener('animationend', onEnd); resolve() };
    // 浮窗里的控件也会冒泡出 animationend，只认目标就是舞台本身的那一条。
    const onEnd = (event: Event) => { if (event.target === dialog) done() };
    dialog.addEventListener('animationend', onEnd);
    timer = window.setTimeout(done, 380);
  });
}

function dispose({ miniplayer = true }: { miniplayer?: boolean } = {}): void {
  generation++;
  controller?.abort();
  controller = null;
  /* 离开详情时正在放的视频不销毁：整个播放器搬进小窗接着放。要在卸掉媒体框之前搬。 */
  player.handOffStage(miniplayer);
  if (!view) return;
  const dialog = stageDialog();
  if (dialog) stageHost().release(dialog);
  // 右键菜单开着时挪进了舞台：先放回 body，别跟着浮窗一起被卸掉。
  closePlayerMenu();
  if (dialog?.open) dialog.close();
  view = null;
  closeRequested = false;
  dismissArmed = false;
  paint();
  player.setStageMeta(null);
  document.body.removeAttribute('data-detail-open');
}

function update(patch: StagePatch): void {
  if (!view || view.content.kind !== 'item') return;
  view = { ...view, content: { kind: 'item', props: { ...view.content.props, ...patch } } };
  paint();
}

function repaintPoster(): void {
  const meta = player.stageMeta();
  const item = meta?.kind === 'item' ? meta.item : null;
  const poster = item ? stageHost().player.posterUrl(item) : '';
  if (!poster) return;
  const current = player.stagePlayer();
  if (current) current.poster(poster);
  else document.getElementById('vid')?.setAttribute('poster', poster);
}

const api: StageApi = {
  open, update, exit, dispose, requestClose, repaintPoster,
  isOpen: () => !!view,
  activeVideo: () => player.activeStageVideo(),
  toggleTheater: () => { if (view) applyTheaterMode(!stageHost().player.settings().theaterMode) },
  toggleMiniplayer: () => player.toggleMiniplayer(),
  closeMiniplayer: () => player.closeMiniplayer(),
  miniplayerActive: () => player.miniplayerActive(),
  miniplayerTakesCard: (item) => player.miniplayerTakesCard(item),
  miniplayerPlay: (id) => { void player.miniplayerPlay(id) },
};

/** 接上壳给的宿主，拿回舞台的命令式入口。小窗的节点随根一起画出来，第一次进小窗之前就在。 */
export function configureStage(next: StageHost): StageApi {
  host = next;
  player.configureStagePlayer(next, { isOpen: () => !!view, requestClose });
  paint();
  return api;
}
