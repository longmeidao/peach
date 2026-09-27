/* 馆藏卡片网格（`catalog-grid` island）：目录与回收站、资料页作品区、详情页的接着看。
 *
 * 取数、排法与续页都在这里；打开、选择、稍后看与回收站操作是壳递进来的动作。换筛选或壳要求
 * 重读时查询换键，整个网格按新键重挂：先铺壳那份骨架，数据回来后骨架淡出、内容从模糊里清晰
 * 起来（同遗留层 `revealSkeleton`），骨架还没到显示门槛就取完的直接落内容。
 *
 * 读数行（`#count`）的结构归壳，网格每接一页经 `onCount` 报一次，再把读数按位错峰写进
 * 那一格（遗留层 `popCount`）。无限滚动的判据照抄遗留层 `wireLoadMore`：哨兵进入视口 320px
 * 内自动取下一页，点它等于手动取；失败在哨兵后面留一条可重试的 Note，之后只有手动才重试。 */
import {
  Fragment, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState,
  type AnimationEvent, type MouseEvent, type RefObject,
} from 'react';
import { useInfiniteQuery, type InfiniteData, type QueryKey } from '@tanstack/react-query';
import { requestErrorMessage } from '@peach/legacy/core';
import { fitSkeleton, loadingDotsHtml, noteHtml, popCount } from '@peach/legacy/ui';

import { apiGet } from '../../api';
import { COVER_FRONT_RATIO, MediaCard, type MediaCardVariant } from '../components/media-card';
import { MIX_FLIP_FACES, MixCard } from '../components/mix-card';
import { javArtwork, type Artwork } from './artwork';
import {
  SHORTS_BATCH, arrangeTiles, catalogParams, catalogQuery, entityQuery, mixHasPicture, mixLabel,
  shortsBoundaries, shortsParams, splitSections, type GridPage, type ShortsCut, type Tile,
} from './catalog-grid';
import type { CatalogGridProps, MediaCardLayout, MediaCardHelpers, MediaItem, MediaPage } from './types';

/* 上一次写出去的读数。读数那一格每次随读数行整块重建，靠它分清「换了个数」和「刚出现」：
   只有前者按位错峰长出来。跨查询、跨重挂都要记得，所以放在模块里，同遗留层 `lastCountReadout`。 */
let lastReadout = '';

export function CatalogGridPage(props: CatalogGridProps) {
  if (props.mode === 'items') return <ItemsGrid {...props} />;
  const key = props.mode === 'entity'
    ? `entity:${props.entityKey || ''}:${props.revision}`
    : `catalog:${catalogParams(props.filters || {}, !!props.excludeVertical)}:${props.batchSize || 60}:${props.revision}`;
  return <GridBody key={key} {...props} />;
}

function Icon({ name }: { name: string }) {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><use href={`#i-${name}`} /></svg>;
}

/** 壳手上已有的一批（详情页的接着看）：不取数，只画卡。`next` 那一排的卡直接排进壳的横排。 */
function ItemsGrid(props: CatalogGridProps) {
  const { actions } = props;
  const onOpen = useCallback((item: MediaItem, anchor: HTMLElement) => actions.open(item, anchor), [actions]);
  const variant: MediaCardVariant = props.variant === 'next' ? 'next' : 'grid';
  const cards = (props.items || []).map((item) => (
    <MediaCard key={item.id} item={item} variant={variant} layout={props.layout}
      selected={props.selected.has(item.id)} selectMode={props.selectMode} seekSeconds={props.seekSeconds}
      helpers={props.helpers} actions={actions} onOpen={onOpen} />
  ));
  if (variant === 'next') return <div data-media-next-row="">{cards}</div>;
  return <div data-media-grid="" data-select-mode={props.selectMode ? '' : undefined}>{cards}</div>;
}

/** 一次查询的整个生命周期：骨架、首屏、续页、竖屏带与读数。 */
function GridBody(props: CatalogGridProps) {
  const { helpers, actions, layout } = props;
  const entity = props.mode === 'entity';
  const trash = !entity && props.filters?.state === 'trash';
  const query = entity ? entityQuery(props) : catalogQuery(props);
  const result = useInfiniteQuery<GridPage, Error, InfiniteData<GridPage, number>, QueryKey, number>({
    queryKey: query.queryKey,
    queryFn: ({ pageParam, signal }) => query.queryFn({ pageParam, signal }),
    initialPageParam: 0,
    getNextPageParam: query.getNextPageParam,
  });

  /* 一次取数落定就告诉壳一次，成功、为空、失败都算：壳里 `await` 这次重读的调用方据此放行。 */
  const settledOnce = useRef(false);
  useEffect(() => {
    if (result.isPending || settledOnce.current) return;
    settledOnce.current = true;
    props.settled?.(props.revision);
  }, [result.isPending]);

  const { tiles, pageStarts } = useMemo(() => arrangeTiles(result.data?.pages || [], {
    collapse: props.groupCollapse !== false, mix: !!props.mix && !trash, javImage: layout.javImage,
  }), [result.data, props.groupCollapse, props.mix, trash, layout.javImage]);
  const shown = tiles.reduce((count, tile) => count + (tile.kind === 'card' ? 1 : 0), 0);
  const total = Number(result.data?.pages[0]?.total || 0);

  const reveal = useSkeletonReveal(result.isPending, props.skeletonHtml);
  const body = useRef<HTMLDivElement | null>(null);
  const cuts = useShortsStrips(props, result.data, tiles, pageStarts, body);

  /* 读数：先让壳重画读数行，再把数写进它新建的那一格。 */
  useLayoutEffect(() => {
    if (!result.data) return;
    props.onCount?.(total, shown);
    const readout = trash ? null : props.countRow?.querySelector<HTMLElement>('[data-count-readout]');
    if (!readout) return;
    const text = `${total.toLocaleString()} 个符合 · 显示 ${shown}`;
    if (lastReadout) readout.dataset.popCount = lastReadout;
    lastReadout = text;
    popCount(readout, text);
  }, [result.data, total, shown]);

  const open = useCallback((item: MediaItem, anchor: HTMLElement) => actions.open(item, anchor), [actions]);
  const openResource = useCallback(
    (item: MediaItem, anchor: HTMLElement) => actions.openResource(item, anchor), [actions]);
  const openShort = useCallback((item: MediaItem) => actions.openShort(item), [actions]);

  const loadNext = useCallback(async () => {
    const next = await result.fetchNextPage({ cancelRefetch: false });
    if (next.isFetchNextPageError) throw next.error;
  }, [result.fetchNextPage]);

  const card = (tile: Tile) => tile.kind === 'mix'
    ? <HomeMix key={`mix:${tile.seed.id}`} seed={tile.seed} layout={layout} helpers={helpers} actions={actions} />
    : (
      <MediaCard key={tile.item.id} item={tile.item}
        variant={trash && tile.item.medium && tile.item.medium !== 'video' ? 'resource' : 'grid'} layout={layout}
        selected={props.selected.has(tile.item.id)} selectMode={props.selectMode} seekSeconds={props.seekSeconds}
        helpers={helpers} actions={actions} onOpen={trash ? openResource : open} />
    );

  const content = () => {
    if (result.isPending) return null;
    if (!result.data) {
      return <RetryNote message={requestErrorMessage(result.error)} onRetry={() => void result.refetch()} />;
    }
    if (!tiles.length) {
      const html = props.emptyHtml?.({ trash, libraryEmpty: !!result.data.pages[0]?.libraryEmpty }) || '';
      return <div data-media-empty="" dangerouslySetInnerHTML={{ __html: html }} />;
    }
    return (
      <>
        <div data-media-sections="" data-select-mode={props.selectMode ? '' : undefined}>
          {splitSections(tiles, cuts).map((section) => (
            <Fragment key={section.start}>
              <div data-media-grid="">{section.tiles.map(card)}</div>
              {section.strip ? <ShortsStrip cut={section.strip} props={props} onOpen={openShort} /> : null}
            </Fragment>
          ))}
        </div>
        {result.hasNextPage
          ? <LoadMore key={result.data.pages.length} entity={entity} load={loadNext}
            enabled={() => props.canLoadMore?.() !== false} />
          : null}
      </>
    );
  };

  return (
    <div ref={body} data-media-body="" data-grid-reveal={reveal.fading ? '' : undefined}>
      {reveal.layer}
      {content()}
    </div>
  );
}

/** 骨架与它的退场。骨架那一层在数据到了之后原地变成淡出层：同一个元素、同一段 HTML，
 *  React 不重写它，`fitSkeleton` 补齐的那几张卡也还在。骨架还没到显示门槛（`fitSkeleton`
 *  给它挂着 `.skeleton-awaiting`）就已取完，就直接撤掉，不为从未被看见的占位播退场。 */
function useSkeletonReveal(pending: boolean, skeletonHtml: () => string) {
  const [phase, setPhase] = useState<'skeleton' | 'fade' | 'none'>(pending ? 'skeleton' : 'none');
  const [markup] = useState(() => (pending ? skeletonHtml() : ''));
  const node = useRef<HTMLDivElement | null>(null);
  useLayoutEffect(() => { if (node.current) fitSkeleton(node.current) }, []);
  useLayoutEffect(() => {
    if (pending || phase !== 'skeleton') return;
    const seen = !!node.current && !node.current.querySelector('.skeleton-awaiting');
    setPhase(seen ? 'fade' : 'none');
  }, [pending]);
  /* 动画结束事件丢了（标签页在后台、元素被别的动效接管）也要收掉，同遗留层的 1 秒兜底。 */
  useEffect(() => {
    if (phase !== 'fade') return undefined;
    const timer = setTimeout(() => setPhase('none'), 1000);
    return () => clearTimeout(timer);
  }, [phase]);
  const done = (event: AnimationEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) setPhase('none');
  };
  const layer = phase === 'none' ? null : (
    <div ref={node} data-grid-fade={phase === 'fade' ? '' : undefined} aria-hidden={pending ? undefined : true}
      hidden={!pending && phase === 'skeleton'} onAnimationEnd={done}
      dangerouslySetInnerHTML={{ __html: markup }} />
  );
  return { layer, fading: phase === 'fade' };
}

/** 失败留在原位，给一颗重试。Note 由遗留层 `noteHtml` 拼，和壳里别处的失败提示是同一份。 */
function RetryNote({ message, onRetry }: { message: string; onRetry: () => void }) {
  const click = (event: MouseEvent<HTMLDivElement>) => {
    if ((event.target as HTMLElement).closest('[data-note-action]')) onRetry();
  };
  return (
    <div data-media-error="" onClick={click}
      dangerouslySetInnerHTML={{ __html: noteHtml(message, { variant: 'error', actionLabel: '重试' }) }} />
  );
}

/** 续页。目录是一颗滚到附近就自己取的哨兵，资料页是一枚「载入更多」键，两者判据相同。
 *  每接上一页就按新键重挂一次，失败状态不跨页。 */
function LoadMore({ entity, load, enabled }: { entity: boolean; load: () => Promise<void>; enabled: () => boolean }) {
  const node = useRef<HTMLElement | null>(null);
  const busy = useRef(false);
  const failed = useRef(false);
  const [state, setState] = useState<{ busy: boolean; error: string }>({ busy: false, error: '' });
  const latest = useRef({ load, enabled });
  latest.current = { load, enabled };
  const run = useCallback(async (manual: boolean) => {
    const el = node.current;
    if (busy.current || !el?.isConnected || (!manual && failed.current) || !latest.current.enabled()) return;
    busy.current = true;
    failed.current = false;
    setState({ busy: true, error: '' });
    try {
      await latest.current.load();
      if (node.current) setState({ busy: false, error: '' });
    } catch (error) {
      failed.current = true;
      if (node.current) setState({ busy: false, error: requestErrorMessage(error) });
    } finally {
      busy.current = false;
    }
  }, []);
  const attach = useCallback((el: HTMLElement | null) => { node.current = el }, []);
  useEffect(() => {
    const el = node.current;
    if (!el) return undefined;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) void run(false);
    }, { rootMargin: '320px' });
    observer.observe(el);
    return () => observer.disconnect();
  }, [run]);
  const aria = state.busy ? { 'aria-busy': true, 'aria-disabled': true } as const : {};
  return (
    <>
      {entity
        ? <button ref={attach} type="button" data-entity-more="" {...aria} onClick={() => void run(true)}>载入更多</button>
        : <div ref={attach} data-load-more="" {...aria} onClick={() => void run(true)}
          dangerouslySetInnerHTML={{ __html: loadingDotsHtml('继续载入中…') }} />}
      {state.error ? <RetryNote message={state.error} onRetry={() => void run(true)} /> : null}
    </>
  );
}

/** 竖屏带：每接一页请求一条，落点在这一页新增的那几行之间的行边界上随机取一个。
 *  请求跟着主列表的筛选与排序走；一条都没有、或这一页剪不出行边界，偏移量按遗留层归零或不动。 */
function useShortsStrips(
  props: CatalogGridProps, data: InfiniteData<GridPage, number> | undefined,
  tiles: readonly Tile[], pageStarts: readonly number[], body: RefObject<HTMLElement | null>,
): ShortsCut[] {
  const [cuts, setCuts] = useState<ShortsCut[]>([]);
  const [arrived, setArrived] = useState<{ page: number; total: number; items: MediaItem[]; more: boolean } | null>(null);
  const offset = useRef(0);
  const handled = useRef(0);
  const controllers = useRef<AbortController[]>([]);
  useEffect(() => () => controllers.current.forEach((controller) => controller.abort()), []);
  useEffect(() => {
    const pages = data?.pages.length || 0;
    if (!props.shorts || handled.current >= pages) return;
    handled.current = pages;
    const controller = new AbortController();
    controllers.current.push(controller);
    const page = pages - 1;
    apiGet<MediaPage>(`/api/items?${shortsParams(props.filters || {}, offset.current)}`, controller.signal)
      .then((strip) => {
        const items = strip.items || [];
        if (!items.length) { offset.current = 0; return }
        props.cache(items);
        setArrived({ page, total: Number(strip.total || 0), items, more: strip.has_more !== false });
      })
      /* 竖屏带是穿插进来的附加内容，取不到就不插，主列表照常。 */
      .catch(() => {});
  }, [data]);
  useLayoutEffect(() => {
    if (!arrived) return;
    setArrived(null);
    const start = cuts.reduce((at, cut) => Math.max(at, cut.at), 0);
    const sections = body.current?.querySelectorAll<HTMLElement>('[data-media-sections] > [data-media-grid]');
    const last = sections?.[sections.length - 1];
    const columns = last ? Math.max(1, getComputedStyle(last).gridTemplateColumns.split(' ').length) : 1;
    const addedFrom = Math.max(0, (pageStarts[arrived.page] ?? 0) - start);
    const boundaries = shortsBoundaries(tiles.length - start, addedFrom, columns);
    if (!boundaries.length) return;
    const at = start + (boundaries[Math.floor(Math.random() * boundaries.length)] ?? 0);
    offset.current = arrived.more ? offset.current + SHORTS_BATCH : 0;
    setCuts((current) => [...current, { at, total: arrived.total, items: arrived.items }]);
  }, [arrived]);
  return cuts;
}

function ShortsStrip({ cut, props, onOpen }: {
  cut: ShortsCut; props: CatalogGridProps; onOpen: (item: MediaItem) => void;
}) {
  const row = useRef<HTMLDivElement | null>(null);
  const { wireDrag } = props;
  useEffect(() => { if (row.current) wireDrag(row.current) }, [wireDrag]);
  return (
    <section data-shorts-strip="">
      <h2>
        竖屏 <span data-shorts-count="">{`${cut.total.toLocaleString()} 个`}</span>
        <button type="button" data-shorts-enter="" onClick={() => props.actions.openShorts()}>
          <Icon name="gallery-vertical-end" /><span>进入沉浸模式</span>
        </button>
      </h2>
      <div ref={row} data-shorts-row="">
        {cut.items.map((item) => (
          <MediaCard key={item.id} item={item} variant="short" layout={props.layout}
            selected={props.selected.has(item.id)} selectMode={props.selectMode} seekSeconds={props.seekSeconds}
            helpers={props.helpers} actions={props.actions} onOpen={onOpen} />
        ))}
      </div>
    </section>
  );
}

/** Mix 的一张画面，同遗留层 `mixFacePoster`：番号作品走封套链，其余取本地预览格。 */
function mixFace(item: MediaItem, layout: MediaCardLayout, eager: boolean, helpers: MediaCardHelpers): Artwork {
  const jav = layout.active && !!item.is_jav;
  if (item.is_jav) return javArtwork(item, jav ? layout.size : 'small', eager, layout.javImage, helpers.coverHtml);
  if (!item.has_thumb && !item.has_local_poster) return { kind: '', html: '' };
  return { kind: 'thumb', html: `<img class="poster" src="/poster?id=${item.id}&c=4" alt="" loading="${eager ? 'eager' : 'lazy'}">` };
}

/** 目录每一页第 8 位的那张 Mix：以种子为首的相似作品。整张卡是点击区，悬停逐张翻过那一叠。 */
function HomeMix({ seed, layout, helpers, actions }: {
  seed: MediaItem; layout: MediaCardLayout; helpers: MediaCardHelpers; actions: CatalogGridProps['actions'];
}) {
  const faces = useRef(new Map<string, string>());
  const latest = useRef(layout);
  latest.current = layout;
  const label = mixLabel(seed, helpers.tagLabel);
  const flipImages = useCallback(async () => {
    const current = latest.current;
    const related = await actions.mixRelated(seed.id);
    const list = [seed, ...related].filter((item) => mixHasPicture(item, current.javImage)).slice(0, MIX_FLIP_FACES);
    faces.current = new Map(list.map((item) => [String(item.id), mixFace(item, current, true, helpers).html]));
    return list.map((item) => String(item.id));
  }, [seed, actions, helpers]);
  const jav = layout.active && !!seed.is_jav;
  return (
    <MixCard data-mix-seed={String(seed.id)} name={`Mix · ${label}`}
      caption={`${helpers.displayName(seed, seed.name || '')}及相似作品`} count={0} badge="Mix" glyph wholeCard
      poster={null} artwork={mixFace(seed, layout, false, helpers)}
      ratio={jav && layout.size === 'big' ? COVER_FRONT_RATIO : 16 / 9}
      flipImages={flipImages} faceHtml={(id) => faces.current.get(id) || ''} canFlip={actions.canFlip}
      faces={[]} faceAvatar={() => ''} onOpenEntity={actions.openEntity}
      onOpen={(anchor) => actions.openMix(seed.id, anchor)} openLabel={`打开 Mix · ${label}`} />
  );
}
