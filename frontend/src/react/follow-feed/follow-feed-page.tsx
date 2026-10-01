/* 关注页 `/follow`：页头、创作者与题材两排、两排的筛选玻璃、交集条、卡片列表与底栏（ADR-0031 第 10g 步）。
 *
 * 数据形状、取数键与这一页的判定在 `./follow-feed.ts`，卡片在 `./follow-card.tsx`。换筛选或排序时
 * 查询换键：列表区按新键重挂、铺一块列表骨架，页头、两排与玻璃照原样不动——它们此刻
 * 就能给出最终样子，整块铺骨架的代价是浮层连同上面两排一起先消失再出现，而真正在等的只有列表里
 * 摆哪些东西。
 *
 * 地址栏归壳：点筛选、排序、换媒体都只调 `actions.route`，壳写好地址再把新的 `view` 推回来。
 * 这一页唯一联网的动作是「检查更新」与「抓更早的一页」，两者起的是同一趟后台任务，进度由
 * `helpers.jobProgress` 盯着，跑完失效这一页的查询重取。 */
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from 'react';
import { useInfiniteQuery, useMutation, useQuery, type InfiniteData } from '@tanstack/react-query';
import { icon, requestErrorMessage } from '@peach/legacy/core';
import { emptyStateHtml, spinnerHtml } from '@peach/legacy/ui';

import { Button } from '@/components/base/buttons/button';

import { apiGet, apiSend } from '../../api';
import { LoadMore } from '../catalog-grid/catalog-grid-page';
import { FilterGlassRows, FilterPill } from '../components/filter-glass';
import { RetryNote, useSkeletonReveal } from '../components/grid-reveal';
import { spriteGlyph } from '../components/sprite-glyph';
import { useViewGlide } from '../components/use-view-glide';
import { Segments, Shuffle } from '../entity-filter/entity-filter-page';
import type { SegmentOption } from '../entity-filter/entity-filter';
import { FOLLOW_CHECK_URL, FOLLOW_STATUS_URL } from '../follow-manage/follow-manage';
import { sidebarTagCounts } from '../../sidebar';
import { queryClient } from '../query';
import { FollowCard } from './follow-card';
import { authorAvatarHtml, followAuthorName, sourceIcon } from './follow-marks';
import {
  FOLLOW_CREDENTIALS_KEY, FOLLOW_FEED_SORTS, FOLLOW_FILTERS, FOLLOW_TAGS_FIRST, FOLLOW_WORKS_FIRST,
  collectionItems, dropCondition, fetchFollowCredentials, followConditions, followFeedQuery, groupMediaKinds, groupTagType, itemForMedia,
  mergedPage, nextSort, randomOrder, sortAriaLabel, backfillState, withStatus,
  type FollowCondition, type FollowContext, type FollowFeedProps, type FollowGroup, type FollowPage, type FollowSource,
  type FollowJobState, type FollowView, type FollowWorkRow,
} from './follow-feed';

const Sep = () => <span data-entity-sep="" aria-hidden="true" />;
const SETTINGS = spriteGlyph('settings');
const CHEVRON_DOWN = spriteGlyph('chevron-down');
const HISTORY = spriteGlyph('history');

/** 照片墙那一排的图片布局两档，同壳里 `PHOTO_LAYOUTS`。 */
export const FOLLOW_PHOTO_LAYOUTS: readonly SegmentOption[] = [
  ['fixed', '固定比例', 'layout-grid'], ['masonry', '瀑布流', 'columns-2'],
];

/** 这一页从数据里推出来的那几样：两排的取样、筛选条的选项、可见的组。只随数据、视图与种子变。 */
function useFacets(data: FollowPage | null, view: FollowView, seed: number) {
  return useMemo(() => {
    const groups = data?.groups || [];
    const counts = data?.counts || {};
    const sources = data?.sources || [];
    /* 筛选条上能选什么来自服务端的全库口径 facets，不是这一页的 groups。按 groups 算的话，选中
       一个创作者之后服务端只回他的条目，创作者栏就只剩他一个人，再也切不回去。 */
    const facets = data?.facets || {};
    const activeAuthors = new Set(facets.authors || []);
    const providerLabels = new Map(sources.map((source) => [source.provider, source.provider_label || source.provider]));
    const providers = new Map((facets.providers || []).map((key) => [key, providerLabels.get(key) || key]));
    const tagCounts = new Map(facets.tags || []);
    const authorSources = new Map<string, FollowSource[]>();
    sources.forEach((source) => {
      if (!source.author_key) return;
      if (!authorSources.has(source.author_key)) authorSources.set(source.author_key, []);
      authorSources.get(source.author_key)!.push(source);
    });
    const authorKeys = [...authorSources.keys()].filter((key) => activeAuthors.has(key));
    /* 创作者行与题材行按本次进入的种子随机取样，进一次换一批：按条数取前几个的话，八十来个题材里
       永远只露出同样那二十几个，这两排回答的是「接下来看什么」，不是「哪个最多」。 */
    const authorOrder = randomOrder(authorKeys, (key) => key, seed);
    const workRows: FollowWorkRow[] = randomOrder(facets.works || [], (row) => row[0], seed).slice(0, FOLLOW_WORKS_FIRST);
    if (view.work && !workRows.some((row) => row[0] === view.work)) workRows.push([view.work, view.work, 0]);
    const allCount = Object.values(counts).reduce((total, count) => total + (Number(count) || 0), 0);
    const tagRows = randomOrder([...tagCounts], (row) => row[0], seed).slice(0, FOLLOW_TAGS_FIRST);
    view.tags.forEach((tag) => {
      if (!tagRows.some(([key]) => key === tag)) tagRows.push([tag, tagCounts.get(tag) || allCount]);
    });
    const mediaCounts = { videos: 0, images: 0 };
    groups.forEach((group) => groupMediaKinds(group).forEach((kind) => { mediaCounts[kind === 'image' ? 'images' : 'videos'] += 1 }));
    const wanted = view.media === 'images' ? 'image' : 'video';
    const visible = groups.filter((group) => groupMediaKinds(group).has(wanted));
    return {
      groups, counts, sources, providers, tagRows, authorSources, authorOrder, workRows, allCount, mediaCounts, visible,
      /* 按下的创作者、来源不在这一版的选项里时（改了别名、来源撤了）当作没按：页面不能停在一个
         看不见按下项的筛选里。标签与题材从别处点进来时可能不在 general facets 里，照样生效。 */
      author: authorSources.has(view.author) && activeAuthors.has(view.author) ? view.author : '',
      provider: providers.has(view.provider) ? view.provider : '',
      workNames: new Map((facets.works || []).map((row) => [row[0], row[1]])),
      broken: sources.filter((source) => source.last_status === 'error' || source.last_status === 'unauthorized'),
      byId: new Map(sources.map((source) => [source.id, source])),
    };
  }, [data, view, seed]);
}

type Facets = ReturnType<typeof useFacets>;

export function FollowFeedPage(props: FollowFeedProps) {
  const { view, seed, revision, helpers, actions } = props;
  const query = followFeedQuery(view, revision);
  const result = useInfiniteQuery(query);
  const credentialsResult = useQuery({
    queryKey: FOLLOW_CREDENTIALS_KEY, queryFn: ({ signal }) => fetchFollowCredentials(signal),
  });
  const data = useMemo(() => mergedPage(result.data), [result.data]);
  const credentials = useMemo(() => new Set((credentialsResult.data?.providers || [])
    .filter((provider) => provider.present).map((provider) => provider.provider)), [credentialsResult.data]);
  const context = useMemo<FollowContext>(() => ({
    sources: data?.sources || [], aliases: data?.author_aliases || [], credentials,
  }), [data, credentials]);
  const facets = useFacets(data, view, seed);
  const listPending = result.isPending || result.isPlaceholderData;

  /* 侧栏标签抽屉仍在壳里：每取到本键自己的数据就把可见条目的标签计数交回去，换键时暂借的
     占位数据不交。 */
  const settled = !listPending && !!data;
  const drawerTags = useMemo(
    () => sidebarTagCounts(facets.visible.flatMap(collectionItems).map((item) => ({ tags: item.tags || [] }))),
    [facets.visible],
  );
  useEffect(() => {
    if (settled) actions.loaded(drawerTags);
  }, [settled, drawerTags, actions]);

  const job = useFollowJob(props, !!data);

  if (!data) {
    if (result.isError) {
      return <RetryNote message={requestErrorMessage(result.error)} onRetry={() => void result.refetch()} />;
    }
    return null;
  }
  const route = (patch: Partial<FollowView>) => actions.route({ ...view, ...patch });
  const conditions = followConditions({ ...view, author: facets.author, provider: facets.provider }, {
    authors: new Map([...facets.authorSources].map(([key, list]) => [key, followAuthorName(list, context)])),
    providers: facets.providers,
    works: facets.workNames,
  });
  const total = view.status ? facets.counts[view.status] || 0 : facets.allCount;
  const canBackfill = facets.sources.some((source) => source.can_backfill);

  return (
    <>
      {/* 进度那一格归 `followJobProgress`：它自己往里插面板、自己开合，React 只给一个空节点。 */}
      <div key={job.generation} ref={job.host} data-follow-progress="" />
      <div data-follow-feed="" data-select-mode={props.selectMode ? '' : undefined}>
        <div data-follow-head="">
          <h2 data-follow-title="">关注</h2>
          <span data-follow-head-actions="">
            <Button variant="secondary" leadingIcon={SETTINGS} data-follow-manage="" onClick={actions.openManage}>
              管理关注
            </Button>
            {facets.sources.length ? (
              <Button variant="primary" data-follow-recheck="" aria-label="检查每个来源的更新"
                aria-busy={job.busy || undefined}
                onClick={() => void job.start(false)}>
                {job.starting === 'check'
                  ? <span className="contents" dangerouslySetInnerHTML={{ __html: spinnerHtml('检查中') }} />
                  : '检查更新'}
              </Button>
            ) : null}
          </span>
        </div>
        <Authors facets={facets} pressed={facets.author} context={context} props={props}
          onPick={(key) => route({ author: facets.author === key ? '' : key })} />
        <Works rows={facets.workRows} pressed={view.work} props={props}
          onPick={(key) => route({ work: view.work === key ? '' : key })} />
        <Glass facets={facets} view={view} total={total} busy={listPending} props={props} route={route} />
        <Combo conditions={conditions} onDrop={(row) => actions.route(dropCondition(view, row))}
          onClear={() => route({ author: '', provider: '', work: '', tags: [] })} />
        {facets.broken.length ? <BrokenNote count={facets.broken.length} onManage={actions.openManage} /> : null}
        <List key={query.queryKey.join('\u0000')} pending={listPending} facets={facets} data={data} context={context}
          props={props} />
        {data.has_more || canBackfill ? (
          <div data-follow-pagination="">
            {data.has_more ? (
              <span data-follow-page-action="">
                <LoadMore key={result.data?.pages.length} entity enabled={() => !job.busyRef.current}
                  load={async () => { await result.fetchNextPage({ throwOnError: true }) }}>
                  <CHEVRON_DOWN className="size-3.5" />加载更多
                </LoadMore>
              </span>
            ) : null}
            {canBackfill ? (
              <span data-follow-page-action="">
                <Button variant="secondary" leadingIcon={job.olderBusy ? undefined : HISTORY} data-follow-older=""
                  aria-busy={job.busy || undefined}
                  onClick={() => void job.start(true)}>
                  {job.olderBusy
                    ? <><span className="contents" dangerouslySetInnerHTML={{ __html: spinnerHtml('抓取中') }} /><span>抓取中…</span></>
                    : '抓更早的一页'}
                </Button>
                <span data-follow-backfill="">{backfillState(facets.sources)}</span>
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    </>
  );
}

/* ── 检查更新与往回抓 ──
 * 一次只往回一页：追更的常规检查永远只看第一页，往回抓是一个独立的、显式的动作，点一次走一页，
 * 不自动、不连翻。两枚键起的是同一趟任务，任务在跑时两枚一起忙，续页也停下。 */
function useFollowJob(props: FollowFeedProps, ready: boolean) {
  const { helpers, actions } = props;
  const [generation, setGeneration] = useState(0);
  const [running, setRunning] = useState(false);
  const [starting, setStarting] = useState<'' | 'check' | 'older'>('');
  /* 往回抓那枚键在它起的那一趟跑完之前一直写「抓取中」，同遗留层：检查更新那一趟只让它忙、不换字。 */
  const [olderRun, setOlderRun] = useState(false);
  const busyRef = useRef(false);
  const node = useRef<HTMLDivElement | null>(null);
  const latest = useRef({ helpers, actions });
  latest.current = { helpers, actions };

  useEffect(() => {
    const host = node.current;
    if (!host) return undefined;
    let alive = true;
    latest.current.helpers.jobProgress({
      host,
      active: () => alive,
      read: (signal) => apiGet<FollowJobState>(FOLLOW_CHECK_URL, signal),
      busy: (on) => {
        if (!alive) return;
        busyRef.current = on;
        setRunning(on);
      },
      complete: (state) => {
        if (!alive) return;
        const report = state.status === 'failed' ? { results: [{ ok: false, error: state.error }] } : state;
        latest.current.actions.checkReport(report);
        busyRef.current = false;
        setRunning(false);
        setOlderRun(false);
        void queryClient.invalidateQueries({ queryKey: ['follow-feed'] });
        /* 跟完的那一路不再盯：重新挂一路，别处再起的下一趟也接得上。 */
        setGeneration((value) => value + 1);
      },
    });
    return () => { alive = false };
    /* 首屏取数失败时进度那一格还没画出来，重试成功后 `ready` 翻过来再接上。 */
  }, [generation, ready]);

  const start = useCallback(async (older: boolean) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setStarting(older ? 'older' : 'check');
    let started = false;
    try {
      const job = await apiSend<{ job_id: string }>(FOLLOW_CHECK_URL, older ? { older: true, background: true } : { background: true });
      sessionStorage.setItem('peach-follow-job', job.job_id);
      started = true;
      if (older) setOlderRun(true);
      setGeneration((value) => value + 1);
    } catch (error) {
      latest.current.actions.checkReport({ results: [{ ok: false, error: requestErrorMessage(error) }] });
      if (older) void queryClient.invalidateQueries({ queryKey: ['follow-feed'] });
    } finally {
      busyRef.current = started;
      setStarting('');
    }
  }, []);

  return {
    generation, host: node as RefObject<HTMLDivElement | null>, busyRef, starting, start,
    busy: running || starting !== '',
    olderBusy: starting === 'older' || (olderRun && running),
  };
}

/* ── 两排 ── */

function Authors({ facets, pressed, context, props, onPick }: {
  facets: Facets; pressed: string; context: FollowContext; props: FollowFeedProps; onPick(key: string): void;
}) {
  const row = useRef<HTMLDivElement>(null);
  useEffect(() => { props.helpers.wireDrag(row.current) }, [props.helpers]);
  if (!facets.authorOrder.length) return null;
  return (
    <div ref={row} data-follow-authors="" aria-label="按创作者筛选">
      {facets.authorOrder.map((key) => {
        const list = facets.authorSources.get(key) || [];
        return (
          <button key={key} type="button" data-follow-author={key} aria-pressed={pressed === key} onClick={() => onPick(key)}>
            <span data-follow-ring="" dangerouslySetInnerHTML={{ __html: authorAvatarHtml(list, followAuthorName(list, context)) }} />
            <span data-follow-name="">{followAuthorName(list, context)}</span>
          </button>
        );
      })}
    </div>
  );
}

/* 创作者行下面这一排是题材，位置和形状对着首页那排厂牌：只收来源自己记成 copyright 与 character 的
   标签，词形猜不得。圆标里是服务端按这个题材挑好的代表图，挑不出就写两个字母。 */
function Works({ rows, pressed, props, onPick }: {
  rows: readonly FollowWorkRow[]; pressed: string; props: FollowFeedProps; onPick(key: string): void;
}) {
  const row = useRef<HTMLDivElement>(null);
  useEffect(() => { props.helpers.wireDrag(row.current) }, [props.helpers]);
  if (!rows.length) return null;
  return (
    <div ref={row} data-follow-works="" aria-label="按题材筛选">
      {rows.map((work) => (
        <button key={work[0]} type="button" data-follow-work={work[0]} aria-pressed={pressed === work[0]}
          onClick={() => onPick(work[0])}>
          <span data-follow-mark="" data-fallback={String(work[1] || '').slice(0, 2)}
            dangerouslySetInnerHTML={{ __html: props.helpers.workMark(work) }} />
          {work[1]}
        </button>
      ))}
    </div>
  );
}

/* ── 筛选玻璃 ──
 * 上排由粗到细，和资料页那条同一个次序：最左端是视频／图片——这一页现在摆的是哪一类东西；隔一道
 * 竖线是四枚状态，恒有一枚生效，滑动的那块玻璃跟着它走；再隔一道才是来源和标签这些可加可不加的
 * 筛选。媒体那一档另有一块圆玻璃：它和状态问的不是同一件事，共用一块的话，点一下图片，玻璃会从
 * 「未看」那儿飞过来。下排左端读数，右端换一批、图片墙上的布局与「仅显示图片」，然后是排序键。 */
function Glass({ facets, view, total, busy, props, route }: {
  facets: Facets; view: FollowView; total: number; busy: boolean; props: FollowFeedProps;
  route(patch: Partial<FollowView>): void;
}) {
  const { helpers, actions } = props;
  const statePane = useRef<HTMLSpanElement>(null);
  const mediaPane = useRef<HTMLSpanElement>(null);
  const stateRow = useRef<HTMLDivElement>(null);
  const mediaRow = useRef<HTMLDivElement>(null);
  const scroll = useRef<HTMLDivElement>(null);
  const tagRow = useRef<HTMLDivElement>(null);
  const showMedia = !!facets.mediaCounts.images || view.media === 'images';
  const stateGlide = useViewGlide(statePane, stateRow, '[data-follow-filter][aria-pressed="true"]', view.status);
  const mediaGlide = useViewGlide(mediaPane, mediaRow, '[data-media-view][aria-pressed="true"]', `${view.media}:${showMedia}`);
  useEffect(() => {
    helpers.wireDrag(scroll.current);
    helpers.wireDrag(tagRow.current);
    helpers.wireScroller(tagRow.current);
  }, [helpers]);
  const providers = [...facets.providers];
  const extras = providers.length + facets.tagRows.length > 0;
  const images = view.media === 'images';
  return (
    <FilterGlassRows label="筛选与排序" topLabel={showMedia ? '媒体与关注筛选' : '关注筛选'}
      attrs={{ 'data-filter-frame': '', 'data-follow-filter-glass': '' }}
      topClassName="gap-1.5 overflow-visible" busy={busy}
      panes={<>
        <span ref={statePane} data-view-glide="" aria-hidden="true" />
        <span ref={mediaPane} data-view-glide="round" aria-hidden="true" />
      </>}
      top={<>
        {showMedia ? (
          <>
            <div ref={mediaRow} role="group" aria-label="媒体类型" data-entity-media="" onPointerLeave={mediaGlide.leave}>
              {([['videos', '视频', facets.mediaCounts.videos, 'play', 'video'],
                ['images', '图片', facets.mediaCounts.images, 'pics', 'image']] as const).map(([value, text, count, symbol, kind]) => {
                const title = `${text} ${Math.max(0, count || 0).toLocaleString()}`;
                return (
                  <button key={value} type="button" data-media-view={value} data-media-icon={kind}
                    aria-pressed={view.media === value} aria-label={title} title={title}
                    onPointerEnter={mediaGlide.hover} onClick={() => { if (view.media !== value) route({ media: value }) }}
                    dangerouslySetInnerHTML={{ __html: icon(symbol) }} />
                );
              })}
            </div>
            <Sep />
          </>
        ) : null}
        <div ref={scroll} data-entity-scroll="">
          <div ref={stateRow} role="group" aria-label="状态" data-entity-states="" onPointerLeave={stateGlide.leave}>
            {FOLLOW_FILTERS.map(([key, label]) => (
              <button key={key} type="button" data-entity-state={key} data-follow-filter={key} data-entity-press=""
                aria-pressed={view.status === key} onPointerEnter={stateGlide.hover}
                onClick={() => { if (view.status !== key) route({ status: key }) }}>
                {label}
              </button>
            ))}
            {extras ? <Sep /> : null}
          </div>
          <div ref={tagRow} data-entity-tags="">
            {providers.map(([key, label]) => (
              <button key={key} type="button" data-follow-provider={key} data-entity-press=""
                aria-pressed={facets.provider === key} title={label} aria-label={`来源：${label}`}
                onClick={() => route({ provider: facets.provider === key ? '' : key })}
                dangerouslySetInnerHTML={{ __html: sourceIcon(key) }} />
            ))}
            {providers.length && facets.tagRows.length ? <Sep /> : null}
            {facets.tagRows.map(([tag, n]) => (
              <FilterPill key={tag} data-follow-tag={tag} data-entity-press=""
                data-tag-cat={`r34-${groupTagType(facets.groups, tag)}`} pressed={view.tags.includes(tag)}
                onPress={() => route({ tags: view.tags.includes(tag) ? view.tags.filter((key) => key !== tag) : [...view.tags, tag] })}>
                {helpers.tagLabel(tag)}
                {n ? <span data-count-badge={tag}>{String(n)}</span> : null}
              </FilterPill>
            ))}
          </div>
        </div>
      </>}
      bottom={<>
        <h3 data-entity-readout="" data-follow-readout="">
          {`${total.toLocaleString()} 项更新 · 显示 ${facets.visible.length.toLocaleString()}`}
        </h3>
        <span data-entity-sorts="">
          <Shuffle onPress={actions.shuffle} />
          {images ? (
            <>
              <Segments label="图片布局" value={props.photoLayout} options={FOLLOW_PHOTO_LAYOUTS}
                onChange={(value) => actions.setPhotoLayout(value === 'fixed' ? 'fixed' : 'masonry')} />
              <button type="button" data-follow-images-only="" aria-pressed={props.imagesOnly} title="仅显示图片"
                aria-label="仅显示图片" onClick={() => actions.setImagesOnly(!props.imagesOnly)}>
                {props.imagesOnly ? <span data-view-glide="" aria-hidden="true" /> : null}
                <span className="contents" dangerouslySetInnerHTML={{ __html: icon('captions-off') }} />
              </button>
            </>
          ) : null}
          {FOLLOW_FEED_SORTS.map(([key, label]) => {
            const pressed = view.sort === key;
            const Arrow = spriteGlyph(view.dir === 'asc' ? 'arrow-up' : 'arrow-down');
            return (
              <button key={key} type="button" data-entity-sort={key} data-follow-sort={key} data-entity-press=""
                aria-pressed={pressed} aria-label={sortAriaLabel(key, label, view.sort, view.dir) || undefined}
                onClick={() => {
                  const next = nextSort(key, view.sort, view.dir);
                  if (next) route(next);
                }}>
                {label}{pressed ? <Arrow className="size-3.5" /> : null}
              </button>
            );
          })}
        </span>
      </>}
    />
  );
}

/* 生效的筛选摊在浮层正下方，跟首页和资料页同一条交集筛选条。放在浮层下面：这一条从无到有会把它
   下面的东西整块推下四十像素，放在上面的话被推的是那块吸顶的玻璃和它上面的两排头像。标签那一档
   不写前缀，标签名自己就说明了它是什么。 */
function Combo({ conditions, onDrop, onClear }: {
  conditions: FollowCondition[]; onDrop(row: FollowCondition): void; onClear(): void;
}) {
  return (
    <div data-entity-combo="" data-follow-combo="">
      {conditions.length ? (
        <>
          {conditions.map((row) => {
            const text = `${row.kind === '标签' ? '' : `${row.kind} `}${row.label}`;
            return (
              <span key={`${row.kind}:${row.key}`} data-combo-chip="">
                {text}
                <button type="button" aria-label={`撤掉 ${text}`} data-follow-drop={row.key} data-follow-drop-kind={row.kind}
                  onClick={() => onDrop(row)}>✕</button>
              </span>
            );
          })}
          <button type="button" data-combo-clear="" onClick={onClear}>全部清除</button>
        </>
      ) : null}
    </div>
  );
}

/** 有来源上次检查失败：这一页不摊原因，指到管理页去看。Note 的边界与图标取全站那一份。 */
function BrokenNote({ count, onManage }: { count: number; onManage(): void }) {
  return (
    <div data-follow-broken="" onClick={(event) => {
      if ((event.target as HTMLElement).closest('[data-follow-manage]')) onManage();
    }} dangerouslySetInnerHTML={{
      __html: `<div class="geist-note geist-note-error fwarn" role="alert">${icon('alert')}<span>${count} 个来源上次检查失败，去<button type="button" class="flink" data-follow-manage>管理关注</button>看原因。</span></div>`,
    }} />
  );
}

/* ── 列表 ── */

function List({ pending, facets, data, context, props }: {
  pending: boolean; facets: Facets; data: FollowPage; context: FollowContext; props: FollowFeedProps;
}) {
  const { view, helpers } = props;
  const images = view.media === 'images';
  const reveal = useSkeletonReveal(pending, () => helpers.listSkeletonHtml(view.media));
  return (
    <div data-follow-list-body="" data-grid-reveal={reveal.fading ? '' : undefined}>
      {reveal.layer}
      {pending ? null : (
        <Cards facets={facets} data={data} context={context} props={props} images={images} />
      )}
    </div>
  );
}

function Cards({ facets, data, context, props, images }: {
  facets: Facets; data: FollowPage; context: FollowContext; props: FollowFeedProps; images: boolean;
}) {
  const { view, helpers, actions } = props;
  const write = useFollowWrite(props);
  const wall = images ? { 'data-size': props.photoSize, 'data-layout': props.photoLayout, 'data-images-only': String(props.imagesOnly) } : {};
  let body: ReactNode;
  if (facets.visible.length) {
    body = facets.visible.map((group) => {
      const source = facets.byId.get(group.primary?.source_id as number);
      const siblings = (source?.author_key && facets.authorSources.get(source.author_key)) || [];
      const id = group.primary.id;
      return (
        <FollowCard key={`${id}:${view.media}`} group={group} authorSources={siblings} media={view.media}
          context={context} selected={props.selected.has(cardId(group, view))} selectMode={props.selectMode}
          busy={write.busy.get(cardId(group, view)) || ''} failure={write.failures.get(cardId(group, view)) || ''}
          helpers={helpers} actions={actions} onStatus={write.status} onSave={write.save} />
      );
    });
  } else {
    body = <Empty data={data} />;
  }
  return (
    <div data-follow-list="" data-follow-wall={images ? '' : undefined} {...wall}>
      {body}
    </div>
  );
}

/** 卡上那一条的 id：卡面换成了组里含当前媒体的那条时，选择与写操作认的是它。 */
function cardId(group: FollowGroup, view: FollowView): number {
  return itemForMedia(group, view.media).id;
}

function Empty({ data }: { data: FollowPage }) {
  const html = (data.groups || []).length
    ? emptyStateHtml('search-x', '当前筛选下没有更新', '切换媒体类型、创作者、来源或标签后再试。')
    : (data.sources || []).length
      ? emptyStateHtml('rss', '没有符合条件的更新', '切换状态或来源筛选后再试。')
      : emptyStateHtml('rss', '还没有关注任何来源', '添加创作者或订阅来源后，更新会集中显示在这里。',
        { actions: '<a class="geist-button primary" href="/follow-manage?tab=add">添加关注</a>' });
  return <div data-follow-empty="" className="contents" dangerouslySetInnerHTML={{ __html: html }} />;
}

/* ── 写操作 ──
 * 状态与稍后看（保存到账本）都在岛里发。成功后在缓存里换局部：条目状态、状态计数，筛着某一档
 * 而新状态不在这一档时整组移出；再在后台重读一遍，拿服务端的口径校正。回执带一颗撤销键，保存
 * 进账本的不给撤销——那是另一件事。只读端写入必然 409，那是正常状态，照实写在卡上。 */
const STATUS_RECEIPTS: Record<string, string> = { new: '已恢复未看', seen: '已标记已看', ignored: '已忽略' };

function useFollowWrite(props: FollowFeedProps) {
  const { view, revision, actions } = props;
  const [busy, setBusy] = useState<Map<number, string>>(() => new Map());
  const [failures, setFailures] = useState<Map<number, string>>(() => new Map());
  const key = followFeedQuery(view, revision).queryKey;
  const mark = (id: number, value: string, into: typeof setBusy) => into((now) => {
    const next = new Map(now);
    if (value) next.set(id, value); else next.delete(id);
    return next;
  });
  const apply = (id: number, to: string) => {
    queryClient.setQueryData<InfiniteData<FollowPage>>(key, (current) => (current ? withStatus(current, view, id, to) : current));
  };
  /* 只重读这一版列表：凭据那一份和别的筛选下缓存的列表都不因为一次标记而变。 */
  const refresh = () => void queryClient.invalidateQueries({ queryKey: key, exact: true });
  const before = (id: number) => {
    const page = mergedPage(queryClient.getQueryData<InfiniteData<FollowPage>>(key));
    for (const group of page?.groups || []) {
      for (const item of [group.primary, ...group.variants, ...group.duplicates]) if (item.id === id) return item.status;
    }
    return 'new';
  };
  /* 回调写在钩子上而不是每次 `mutate` 上：连点两张卡时，`mutate` 上的回调只有最后那一次会跑。 */
  const statusMutation = useMutation({
    mutationFn: ({ id, to }: { id: number; to: string; was: string }) => apiSend(FOLLOW_STATUS_URL, { item: id, to }),
    onSuccess: (_result, { id, to, was }) => {
      apply(id, to);
      refresh();
      actions.toast(STATUS_RECEIPTS[to] || '已更新关注状态', {
        undo: was !== 'saved' ? async () => {
          await apiSend(FOLLOW_STATUS_URL, { item: id, to: was });
          apply(id, was);
          refresh();
        } : undefined,
      });
    },
    onError: (error, { id }) => {
      mark(id, requestErrorMessage(error), setFailures);
      actions.failure('更新关注状态', error);
    },
    onSettled: (_result, _error, { id }) => mark(id, '', setBusy),
  });
  const saveMutation = useMutation({
    mutationFn: (id: number) => apiSend('/api/follow/save', { item: id }),
    onSuccess: (_result, id) => {
      apply(id, 'saved');
      refresh();
      actions.toast('已保存到账本');
    },
    onError: (error, id) => {
      mark(id, requestErrorMessage(error), setFailures);
      actions.failure('保存到账本', error);
    },
    onSettled: (_result, _error, id) => mark(id, '', setBusy),
  });
  const latest = useRef({ statusMutation, saveMutation, before });
  latest.current = { statusMutation, saveMutation, before };
  /* 两个处理器身份不变：卡片按引用比较，每次重画都换新函数的话一屏几百张卡跟着重画。 */
  const status = useCallback((id: number, to: string) => {
    mark(id, to, setBusy);
    mark(id, '', setFailures);
    latest.current.statusMutation.mutate({ id, to, was: latest.current.before(id) });
  }, []);
  const save = useCallback((id: number) => {
    mark(id, 'save', setBusy);
    mark(id, '', setFailures);
    latest.current.saveMutation.mutate(id);
  }, []);
  return { busy, failures, status, save };
}
