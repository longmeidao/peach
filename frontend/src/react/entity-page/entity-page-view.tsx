/* 实体资料页（`entity-page` island）：资料卡、筛选浮层、新作那一行与正文，一棵根、四块宿主。
 *
 * 资料卡画在挂载点里（`[data-entity-hero]`），浮层、新作与正文经 portal 画进壳排好的另外三块：浮层
 * 吸顶要它的父元素就是 `#index`，新作那一行是遗留层的卡片、不进 React 子树的样式范围，所以四块各
 * 守自己的宿主。页内状态都在这里：当前视图、名册还是作品、照片墙的种子与翻页；筛选与媒体视图读
 * 地址栏（壳推进来的 `filters`／`media`），改它们只调 `actions.route`。 */
import { useInfiniteQuery, useMutation, useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { api } from '@peach/legacy/core';
import { confirmModal } from '@peach/legacy/ui';

import { errorMessage } from '../../api';
import type { MediaCardLayout } from '../catalog-grid/types';
import { RetryNote } from '../components/grid-reveal';
import type { EntityBodyActions, EntityPhotos, EntityRoster } from '../entity-body/entity-body';
import { EntityBodyPage } from '../entity-body/entity-body-page';
import type {
  EntityFilterActions, EntityFilterHelpers, EntityFilterTag, EntityPhotoHead, EntityVideoHead, EntityView, EntityViewKeys,
} from '../entity-filter/entity-filter';
import { EntityFilterPage } from '../entity-filter/entity-filter-page';
import type { EntityHeroActions, EntityHeroHelpers } from '../entity-hero/entity-hero';
import { EntityHeroPage } from '../entity-hero/entity-hero-page';
import { feedNewKey, feedNewOptions, postFeedAction } from '../feed-new/feed-new';
import { queryClient } from '../query';
import {
  EMPTY_MEDIA, codeSetsOf, entityKey, entityOptions, entityPhotosKey, fetchItems, itemsOptions,
  photosOptions, tagList, tagPressed, type EntityPageData, type EntityPageProps, type PhotoPage,
} from './entity-page';

export function EntityPage(props: EntityPageProps) {
  const { kind, name } = props;
  const entity = useQuery(entityOptions(kind, name));
  /* 名字对不上任何一位时 `/api/entity` 回 `{error}`：整块换成壳里那一屏空态，骨架不留着闪。空态是
     遗留层的标记，不放进 React 子树的样式范围。 */
  const missing = !!entity.data?.error;
  const { actions } = props;
  useLayoutEffect(() => { if (missing) actions.missing() }, [actions, missing]);
  if (entity.isError) return <RetryNote message={errorMessage(entity.error)} onRetry={() => { void entity.refetch() }} />;
  if (!entity.data || missing) return null;
  return <EntityLoaded {...props} entity={entity.data} />;
}

/** 键一变就加一的代次：作品网格与照片墙按它换键，骨架与续页都从头开始。 */
function useRevision(key: string): number {
  const [seen, setSeen] = useState({ key, n: 1 });
  if (seen.key === key) return seen.n;
  const next = { key, n: seen.n + 1 };
  setSeen(next);
  return next.n;
}

const newSeed = () => String(((Date.now() ^ (Math.random() * 1e9 | 0)) >>> 0) % 99991);

/** 照片一屏的读数：本地图片与样张各数各的；只有样张时不写「0 张」。 */
function photoReadout(page: PhotoPage, codeSets: number) {
  return `照片 · ${[
    page.total || !codeSets ? `${(page.total || 0).toLocaleString()} 张` : '',
    codeSets ? `样张 ${(page.sample_total || 0).toLocaleString()} 张 · ${codeSets} 部作品` : '',
  ].filter(Boolean).join(' · ')}`;
}

function EntityLoaded(props: EntityPageProps & { entity: EntityPageData }) {
  const { kind, name, entity, filters, media, helpers, actions, hosts } = props;
  const company = kind === 'agency' || kind === 'studio';
  /* 事务所名下的这批人不摆在资料卡底那排小圆头像里：那是「同台艺人」，一条附注；名册是这一页的
     正文。片商页的名册是旗下 label，同台艺人那排照旧留在卡底。 */
  const roster = kind === 'agency' ? (entity.related_performers || []) : kind === 'studio' ? (entity.labels || []) : [];
  const entityId = Number(entity.id) || 0;

  /* ── 照片：整组那一份数出照片档有几张、出不出；墙读的是当前这一组（整组或一个图集）。 ── */
  const base = useInfiniteQuery(photosOptions(kind, name, 0, ''));
  const basePage = base.data?.pages[0];
  const basePhotos = basePage && !basePage.error ? basePage : null;
  const photoCount = basePhotos ? (basePhotos.total || 0) + (basePhotos.sample_total || 0) : 0;
  const photosAvailable = (basePhotos?.total || 0) > 0 || codeSetsOf(basePhotos).length > 0;
  const mediaNow = media.media === 'photos' && photosAvailable ? media : EMPTY_MEDIA;

  /* 名册与媒体不共用地址栏：地址栏只认 `media`，名册是事务所页与片商页的默认视图，进页就在那里。
     换了筛选就回到作品：标签是作品筛选，留在名册里既不生效，标签条也会自相矛盾。 */
  const [rosterView, setRosterView] = useState<'people' | 'videos'>('people');
  const filterKey = new URLSearchParams(Object.entries(filters).filter(([, value]) => value)).toString();
  const [seenFilters, setSeenFilters] = useState(filterKey);
  if (seenFilters !== filterKey) {
    setSeenFilters(filterKey);
    setRosterView('videos');
  }
  const view: EntityView = company && rosterView === 'people' && roster.length ? 'people' : mediaNow.media;

  /* ── 作品 ── */
  const itemsQuery = itemsOptions(props);
  const items = useQuery(itemsQuery);
  const itemsRevision = useRevision(JSON.stringify(itemsQuery.queryKey));
  /* 直达或刷新资料页时 URL 没有 `jav=1`：以第一页作品的真实 `is_jav` 恢复女优／厂牌语境，版式开关
     不是只在从 JAV 首页点进来时才偶然存在。只看进页那一份，页内换筛选不改语境。 */
  const [javPage] = useState(() => (kind === 'performer' || kind === 'studio')
    && (props.jav || (items.data?.items || []).some((item) => item.is_jav)));
  useLayoutEffect(() => { actions.javContext(javPage) }, [actions, javPage]);
  const layout = useMemo<MediaCardLayout>(() => (props.layout.active === javPage ? props.layout
    : { ...props.layout, active: javPage }), [props.layout, javPage]);
  const opts = { jav: props.jav, seed: props.seed };
  const fetchPage = useCallback(
    (offset: number, signal: AbortSignal) => fetchItems(kind, name, filters, opts, offset, props.cache, signal),
    // 续页的口径就是第一页那一份：代次随键变，键里已经带着筛选、种子与 JAV 开关。
    [itemsRevision]);

  /* ── 照片墙 ── */
  const [seeds, setSeeds] = useState<Record<number, string>>({});
  const wallSet = mediaNow.set;
  const wallSeed = seeds[wallSet] || '';
  const wall = useInfiniteQuery({ ...photosOptions(kind, name, wallSet, wallSeed), enabled: view === 'photos' });
  const wallPage = wall.data?.pages[0];
  const wallRevision = useRevision(JSON.stringify(entityPhotosKey(kind, name, wallSet, wallSeed)));
  const photos = useMemo<EntityPhotos | null>(() => {
    const pages = wall.data?.pages;
    if (!pages?.[0] || pages[0].error) return null;
    const first = pages[0];
    return {
      revision: wallRevision,
      codeSets: first.id ? [] : codeSetsOf(first),
      items: pages.flatMap((page) => page.items || []),
      total: first.total || 0,
      hasMore: !!pages[pages.length - 1]?.has_more,
    };
  }, [wall.data, wallRevision]);
  const wallRefetch = wall.refetch;
  const fetchNextPhotos = wall.fetchNextPage;

  /* ── 新作 ── */
  const feed = useQuery({ ...feedNewOptions(entityId, helpers.feedRowHtml), enabled: !!entityId });
  const feedRevision = useRef(props.feedRevision);
  useEffect(() => {
    if (feedRevision.current === props.feedRevision) return;
    feedRevision.current = props.feedRevision;
    void queryClient.invalidateQueries({ queryKey: feedNewKey(entityId) });
  }, [entityId, props.feedRevision]);

  /* 换了视图、换了一批内容之后吸顶要重算一次。 */
  const hasItems = !!items.data;
  useEffect(() => { actions.painted(view) }, [actions, view, itemsRevision, photos?.revision, hasItems]);

  /* ── 写操作 ── */
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false }, []);
  const [portraitEpoch, setPortraitEpoch] = useState(0);
  const refreshEntity = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: entityKey(kind, name) });
    await queryClient.invalidateQueries({ queryKey: ['entity-items', kind, name] });
  }, [kind, name]);
  const alias = useMutation({
    mutationFn: (payload: { alias: string; remove?: boolean }) => api('/api/entity-alias',
      { method: 'POST', body: JSON.stringify({ kind, name: entity.canonical_name, ...payload }) }) as Promise<{ added?: boolean; alias?: string }>,
    onSuccess: () => refreshEntity(),
  });
  const rename = useMutation({
    mutationFn: ({ from, to }: { from: string; to: string }) => api('/api/entity-name',
      { method: 'POST', body: JSON.stringify({ kind, name: from, canonical: to }) }) as Promise<{
        changed?: boolean; canonical_name?: string; previous_name?: string }>,
  });
  const follow = useMutation({
    mutationFn: (on: boolean) => api('/api/feeds/source',
      { method: 'POST', body: JSON.stringify({ action: 'follow', entity_id: entityId, enabled: on }) }),
    onSuccess: (_data, on) => queryClient.setQueryData<EntityPageData>(entityKey(kind, name),
      (current) => (current ? { ...current, feed: { ...current.feed, following: on } } : current)),
  });

  const heroActions = useMemo<EntityHeroActions>(() => ({
    openEntity: actions.openEntity,
    /* 换统称要重写整条实体的扁平投影，先把代价说清再问。确认键、标题和成功回执共用「更改统称」这一个
       动词；写入失败时弹层留在原地，原因写在正文下方等重试。地址换成新名字，由壳重进这一页。 */
    chooseName: (chosen) => {
      const current = entity.canonical_name;
      if (chosen === current) return;
      void confirmModal({
        title: '更改统称',
        body: `「${chosen}」将成为这条实体的规范名，「${current}」留作别名。作品上的署名、搜索和标签都会跟着改写。`,
        confirmLabel: '更改统称',
        onConfirm: () => rename.mutateAsync({ from: current, to: chosen }),
      }).then(({ confirmed, result }) => {
        const done = result as { changed?: boolean; canonical_name?: string; previous_name?: string } | undefined;
        if (!confirmed || !done?.changed) return;
        helpers.receipt(`已把统称更改为 ${done.canonical_name}`, { undo: async () => {
          await rename.mutateAsync({ from: done.canonical_name || '', to: done.previous_name || '' });
          actions.openEntity(kind, done.previous_name || '');
        } });
        actions.openEntity(kind, done.canonical_name || '');
      });
    },
    addAlias: () => { void helpers.aliasForm(entity.user_aliases || [], (payload) => alias.mutateAsync(payload)) },
    follow: async (on) => {
      try {
        await follow.mutateAsync(on);
      } catch (error) {
        helpers.failure(on ? '订阅新作' : '取消订阅新作', error);
        throw error;
      }
    },
    /* 「订阅新作」打开时服务端当场在后台拉一轮：等那一轮跑完再把新作那一行重取一次。等的上限是
       那一轮自己的时长量级，页面换走了就不再等。 */
    refreshFeedAfterCheck: () => {
      void (async () => {
        for (let tries = 0; tries < 40 && alive.current; tries += 1) {
          await new Promise((resolve) => { setTimeout(resolve, 3000) });
          const job = await (api('/api/feeds/check') as Promise<{ status?: string }>).catch(() => null);
          if (!job || job.status !== 'running') break;
        }
        if (alive.current) await queryClient.invalidateQueries({ queryKey: feedNewKey(entityId) });
      })();
    },
    feedAction: postFeedAction,
    /* 圆框角上那个加号：头像索引在服务端已经换过，重取资料、整块资料卡重建才读得到新图。 */
    avatarPicked: () => {
      void queryClient.refetchQueries({ queryKey: entityKey(kind, name) }).then(() => {
        if (alive.current) setPortraitEpoch((epoch) => epoch + 1);
      });
    },
  }), [actions, alias, entity, entityId, follow, helpers, kind, name, rename]);
  const heroHelpers = useMemo<EntityHeroHelpers>(() => ({
    portraitImg: () => helpers.portraitImg(kind, entity),
    costarImg: helpers.costarImg,
    wireScroller: helpers.wireDrag,
    wireFeedRow: helpers.wireFeedRow,
    receipt: helpers.receipt,
  }), [entity, helpers, kind]);

  /* ── 浮层 ── */
  const filterActions = useMemo<EntityFilterActions>(() => ({
    /* 按下去那一下视图键就换过去，玻璃跟着滑，不等换视图的活干完。 */
    setView: (next) => {
      if (next === view && !mediaNow.set) return;
      setRosterView(next === 'people' ? 'people' : 'videos');
      actions.route(filters, next === 'photos' ? { media: 'photos', set: 0 } : EMPTY_MEDIA);
    },
    setState: (value) => actions.route({ ...filters, state: value }, EMPTY_MEDIA),
    toggleTag: actions.toggleTag,
    clearFilter: actions.clearFilter,
    clearAll: actions.clearAll,
    setSort: actions.setSort,
    /* 换一批：照片换一粒种子把这一屏重排一遍，整组或单个图集都是，新墙取回来再换上，等的这一下
       键上转圈；作品那一粒是全站的种子，交给壳。 */
    reshuffle: async () => {
      if (view !== 'photos') {
        const seed = actions.reshuffleVideos();
        const next = itemsOptions({ kind, name, filters: { ...filters, sort: 'seed' }, jav: props.jav, seed,
          revision: props.revision, cache: props.cache });
        await queryClient.fetchQuery(next).catch(() => null);
        return;
      }
      const seed = newSeed();
      const next = await queryClient.fetchInfiniteQuery(photosOptions(kind, name, wallSet, seed)).catch(() => null);
      if (!alive.current || !next?.pages[0] || next.pages[0].error) return;
      setSeeds((current) => ({ ...current, [wallSet]: seed }));
    },
    setJavLayout: actions.setJavLayout,
    setPhotoLayout: actions.setPhotoLayout,
    photoBack: () => actions.route(filters, { media: 'photos', set: 0 }),
  }), [actions, filters, kind, mediaNow.set, name, props.cache, props.jav, props.revision, view, wallSet]);
  const filterHelpers = useMemo<EntityFilterHelpers>(() => ({
    wireDrag: helpers.wireDrag,
    wireScroller: helpers.wireScroller,
    sourceToolsHtml: helpers.sourceToolsHtml,
    wireSourceTools: (root) => helpers.wireSourceTools(root, () => { void wallRefetch() }),
  }), [helpers, wallRefetch]);

  /* 标签按资料里的顺序摆，选中的不往前挪：刚点的那枚就在指针底下，这一下把它抽走反倒是替人决定
     现在该看哪儿。数的是这个人／厂牌名下带这个标签的视频。 */
  const tags: EntityFilterTag[] = (entity.tags || []).map((tag) => ({
    k: tag.k, label: helpers.tagLabel(tag.k), n: tag.n, selected: tagPressed(filters.tag, tag.k) }));
  /* 艺人名册、视频、照片是这一页的三个互斥视图，共用一组圆键；只有一类东西时不出这一组。 */
  const views: EntityViewKeys | null = photoCount || roster.length ? {
    label: roster.length ? '页面视图' : '媒体类型',
    people: roster.length ? { label: kind === 'studio' ? '厂牌' : '艺人', count: roster.length,
      icon: kind === 'studio' ? 'clapperboard' : 'user-round' } : null,
    videos: { count: entity.asset_count || 0 },
    photos: photoCount ? { count: photoCount } : null,
  } : null;
  const video: EntityVideoHead = {
    sorts: helpers.sortKeys(filters.sort || 'new', filters.dir || '', javPage),
    jav: javPage ? { layout: props.javLayout, options: props.javLayouts } : null,
  };
  /* 照片这一排不给排序键：账本里图片只有文件名、体积和来源三样。在一个图集里多两枚源文件键。 */
  const inSet = !!wallPage?.id && !wallPage.error;
  const photo: EntityPhotoHead | null = wallPage && !wallPage.error ? {
    back: inSet, shuffle: !!wallPage.total, layout: props.photoLayout, layouts: props.photoLayouts,
    setId: inSet ? Number(wallPage.id) : 0,
  } : null;
  let readout = '';
  let busy = false;
  if (view === 'people') readout = `${kind === 'studio' ? '厂牌' : '艺人'} · ${roster.length.toLocaleString()}`;
  else if (view === 'videos') {
    busy = !items.data;
    const labels = tagList(filters.tag).map(helpers.tagLabel);
    readout = `视频 · ${(items.data?.total || 0).toLocaleString()}${labels.length ? ` · ${labels.join(' · ')}` : ''}`;
  } else if (wallPage && !wallPage.error) {
    readout = inSet ? `${wallPage.title} · ${(wallPage.total || 0).toLocaleString()} 张`
      : photoReadout(wallPage, codeSetsOf(wallPage).length);
  } else busy = wall.isPending;

  /* ── 正文 ── */
  const bodyActions = useMemo<EntityBodyActions>(() => ({
    ...props.card.actions,
    /* 本地图片的下一页；取不到就抛错，键下出重试。 */
    loadMorePhotos: async () => {
      const result = await fetchNextPhotos();
      if (result.isError) throw result.error;
    },
  }), [fetchNextPhotos, props.card.actions]);
  const rosterProps = useMemo<EntityRoster | null>(() => (roster.length
    ? { kind: kind === 'studio' ? 'studios' : 'performers', people: roster, layout: props.peopleLayout } : null),
  [kind, props.peopleLayout, roster]);

  return (
    <>
      <EntityHeroPage key={portraitEpoch} kind={kind} name={name} entity={entity} feedNew={feed.data ?? null}
        feedHost={entityId ? hosts.feed : null} jav={javPage} actions={heroActions} helpers={heroHelpers} />
      {createPortal(
        <EntityFilterPage kind={kind} name={name} view={view} views={views} state={filters.state || ''}
          states={props.states} tags={tags} combo={helpers.comboItems(filters)} readout={readout} busy={busy}
          video={video} photo={photo} actions={filterActions} helpers={filterHelpers} />,
        hosts.filter)}
      {createPortal(
        view === 'videos' && items.isError
          ? <RetryNote message={errorMessage(items.error)} onRetry={() => { void items.refetch() }} />
          : (
            <EntityBodyPage kind={kind} name={name} view={view} roster={rosterProps} items={items.data ?? null}
              revision={itemsRevision} fetchPage={fetchPage} photos={photos} photoSize={props.photoSize}
              photoLayout={props.photoLayout} helpers={props.card.helpers} actions={bodyActions} layout={layout}
              selectMode={props.selectMode} selected={props.selected} seekSeconds={props.seekSeconds} cache={props.cache}
              wireDrag={props.wireDrag} skeletonHtml={props.skeletonHtml} groupCollapse={props.groupCollapse}
              canLoadMore={props.canLoadMore} />
          ),
        hosts.body)}
    </>
  );
}

