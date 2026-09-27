/* 实体资料页资料卡下面那一整块：交集条，加一块两排的玻璃浮层（上排视图键、观看状态与标签，
 * 下排读数与这一屏的排序、版式和换一批）。三种视图（名册、作品、照片）共用这一块，下排按视图换内容。
 *
 * 状态全在壳里：这一页的筛选、当前视图、排序与读数都当 props 递进来，点下去的动作回壳，壳在发
 * 请求之前先推一份新的按下态，所以 `aria-pressed` 与滑动玻璃当场就到位，不等这一趟取数。
 *
 * 两排「你在哪儿」各有一块滑动玻璃（视图键那块是圆的），由 `use-view-glide.ts` 挪；它们是浮层根上
 * 的常驻节点，换筛选、换视图都只挪不重建。源文件那两枚键仍由遗留层拼（照片详情里复用的是同一对），
 * 那一格用 `dangerouslySetInnerHTML`，React 不拥有里面的节点。 */
import { useEffect, useRef, useState, type RefObject } from 'react';
import { Radio, RadioGroup } from 'react-aria-components';
import { icon } from '@peach/legacy/core';
import { spinnerHtml } from '@peach/legacy/ui';

import { FilterGlassRows, FilterPill } from '../components/filter-glass';
import { SEGMENTED_GLASS_TRACK, SEGMENT_GLASS } from '../components/segmented';
import { spriteGlyph } from '../components/sprite-glyph';
import { useViewGlide } from '../components/use-view-glide';
import {
  videoOnly, type EntityComboItem, type EntityFilterActions, type EntityFilterHelpers, type EntityFilterProps,
  type EntityPhotoHead, type EntityVideoHead, type EntityView, type EntityViewKeys, type SegmentOption,
} from './entity-filter';

const Sep = () => <span data-entity-sep="" aria-hidden="true" />;

export function EntityFilterPage(props: EntityFilterProps) {
  const { view, views, state, states, tags, combo, actions, helpers } = props;
  const onVideos = videoOnly(view);
  const statePane = useRef<HTMLSpanElement>(null);
  const mediaPane = useRef<HTMLSpanElement>(null);
  const stateRow = useRef<HTMLDivElement>(null);
  const mediaRow = useRef<HTMLDivElement>(null);
  const scroll = useRef<HTMLDivElement>(null);
  const tagRow = useRef<HTMLDivElement>(null);
  const bottomRow = useRef<HTMLDivElement>(null);
  const stateGlide = useViewGlide(statePane, stateRow, '[data-entity-state][aria-pressed="true"]', `${view}:${state}`);
  const mediaGlide = useViewGlide(mediaPane, mediaRow, '[data-media-view][aria-pressed="true"]', `${view}:${!!views}`);

  /* 标签那一格是 `overflow-x:auto` 加隐藏滚动条：能滚，但鼠标没有一个够得着的入口，所以登记全站
     横向行那套拖动加滚轮映射。窄屏下滚的是外面那层（观看状态跟着一起走），两层都登记：登记在
     不滚的那一层上是空转，少登记一层就会在某一个宽度上滚不动。下排窄屏下整条横滚，同一套。 */
  useEffect(() => {
    helpers.wireDrag(tagRow.current);
    helpers.wireScroller(scroll.current);
    helpers.wireDrag(bottomRow.current);
  }, [helpers]);

  return (
    <>
      <Combo items={combo} hidden={!onVideos} actions={actions} />
      <FilterGlassRows label="筛选与排序" topLabel="媒体与标签"
        attrs={{ 'data-filter-frame': '', 'data-entity-filter-glass': '' }}
        topClassName="gap-1.5 overflow-visible"
        bottomClassName="min-h-12" bottomRef={bottomRow} busy={props.busy}
        panes={<>
          <span ref={statePane} data-view-glide="" aria-hidden="true" />
          <span ref={mediaPane} data-view-glide="round" aria-hidden="true" />
        </>}
        top={<>
          {views ? (
            <>
              <ViewKeys keys={views} view={view} row={mediaRow} glide={mediaGlide} onView={actions.setView} />
              {onVideos ? <Sep /> : null}
            </>
          ) : null}
          <div ref={scroll} data-entity-scroll="">
            <div ref={stateRow} role="group" aria-label="观看状态" data-entity-states="" hidden={!onVideos}
              onPointerLeave={stateGlide.leave}>
              {states.map((option) => (
                <button key={option.k} type="button" data-entity-state={option.k} data-entity-press=""
                  aria-pressed={state === option.k} onPointerEnter={stateGlide.hover}
                  onClick={() => { if (state !== option.k) actions.setState(option.k) }}>
                  {option.label}
                </button>
              ))}
              <Sep />
            </div>
            {/* 标签只在作品视图出：计数数的是作品，摆到名册或照片上对不上号，点一下还会把视图拨回作品。 */}
            <div ref={tagRow} data-entity-tags="">
              {onVideos ? tags.map((tag) => (
                <FilterPill key={tag.k} data-entity-tag={tag.k} data-entity-press="" pressed={tag.selected}
                  onPress={() => actions.toggleTag(tag.k)}>
                  {tag.label}<span data-count-badge={tag.k}>{tag.n.toLocaleString()}</span>
                </FilterPill>
              )) : null}
            </div>
          </div>
        </>}
        bottom={<Head {...props} />}
      />
    </>
  );
}

/** 名册、视频、照片三个互斥视图共用一组圆键：它们回答的是同一个问题。键名带上数目，悬停读得到。 */
function ViewKeys({ keys, view, row, glide, onView }: {
  keys: EntityViewKeys;
  view: EntityView;
  row: RefObject<HTMLDivElement | null>;
  glide: ReturnType<typeof useViewGlide>;
  onView(view: EntityView): void;
}) {
  const buttons: { value: EntityView; text: string; count: number; symbol: string; kind: string }[] = [];
  if (keys.people) buttons.push({ value: 'people', text: keys.people.label, count: keys.people.count, symbol: keys.people.icon, kind: 'people' });
  buttons.push({ value: 'videos', text: '视频', count: keys.videos.count, symbol: 'play', kind: 'video' });
  if (keys.photos) buttons.push({ value: 'photos', text: '照片', count: keys.photos.count, symbol: 'pics', kind: 'image' });
  return (
    <div ref={row} role="group" aria-label={keys.label} data-entity-media="" onPointerLeave={glide.leave}>
      {buttons.map(({ value, text, count, symbol, kind }) => {
        const title = `${text} ${Math.max(0, count || 0).toLocaleString()}`;
        return (
          <button key={value} type="button" data-media-view={value} data-media-icon={kind}
            aria-pressed={view === value} aria-label={title} title={title} onPointerEnter={glide.hover}
            onClick={() => onView(value)} dangerouslySetInnerHTML={{ __html: icon(symbol) }} />
        );
      })}
    </div>
  );
}

/** 生效的作品筛选。跟浮层分开摆在它上面：它说的是「现在加了哪些」，一颗一颗撤得掉。 */
function Combo({ items, hidden, actions }: { items: EntityComboItem[]; hidden: boolean; actions: EntityFilterActions }) {
  return (
    <div data-entity-combo="" hidden={hidden}>
      {items.length ? (
        <>
          {items.map((item) => (
            <span key={`${item.kind}:${item.key}`} data-combo-chip="">
              {item.label}
              <button type="button" aria-label={`撤掉 ${item.label}`}
                onClick={() => (item.kind === 'untag' ? actions.toggleTag(item.key) : actions.clearFilter(item.key))}>
                ✕
              </button>
            </span>
          ))}
          <button type="button" data-combo-clear="" onClick={actions.clearAll}>全部清除</button>
        </>
      ) : null}
    </div>
  );
}

/** 下排：读数，加这一种视图自己的那几枚控件。名册只有读数。 */
function Head(props: EntityFilterProps) {
  const { view, readout, busy, video, photo, actions, helpers } = props;
  return (
    <>
      {view === 'photos' && photo?.back ? (
        <button type="button" data-photo-back="" onClick={actions.photoBack}>
          <span className="contents" dangerouslySetInnerHTML={{ __html: icon('chevron-left') }} /><span>全部照片</span>
        </button>
      ) : null}
      <Readout text={readout} busy={busy} />
      {view === 'videos' && video ? <VideoControls head={video} actions={actions} /> : null}
      {view === 'photos' && photo ? <PhotoControls head={photo} actions={actions} helpers={helpers} /> : null}
    </>
  );
}

/** 读数：`视频 · N`、`艺人 · N`、`照片 · N 张`。等这一趟取数时换成一条微光，宽度同骨架那一条。 */
function Readout({ text, busy }: { text: string; busy: boolean }) {
  return (
    <h3 data-entity-readout="">
      {busy
        ? <span data-skeleton="count" aria-hidden className="relative inline-block h-3.5 w-24 rounded-md align-middle skeleton-sheen" />
        : text}
    </h3>
  );
}

/** 玻璃上的分段开关：卡片版式、图片布局。选中那一格是浮层选中态那块料。 */
function Segments({ label, value, options, onChange }: {
  label: string; value: string; options: readonly SegmentOption[]; onChange(value: string): void;
}) {
  return (
    <RadioGroup aria-label={label} orientation="horizontal" value={value} onChange={onChange}
      data-entity-layout="" className={SEGMENTED_GLASS_TRACK}>
      {options.map(([option, text, symbol]) => {
        const Glyph = spriteGlyph(symbol);
        return (
          <Radio key={option} value={option} aria-label={text} data-glass-segment="" className={SEGMENT_GLASS}>
            <span title={text} className="contents"><Glyph className="size-4" /></span>
          </Radio>
        );
      })}
    </RadioGroup>
  );
}

function Shuffle({ onPress, busy = false }: { onPress(): void; busy?: boolean }) {
  return (
    <button type="button" data-entity-batch="" title="换一批" aria-label="换一批" aria-busy={busy || undefined}
      aria-disabled={busy || undefined} onClick={() => { if (!busy) onPress() }}
      dangerouslySetInnerHTML={{ __html: busy ? spinnerHtml('正在换一批') : icon('shuffle') }} />
  );
}

/** 作品视图：换一批、JAV 语境下的卡片版式，排序键一律排在最末，挨着它说明的那批内容。 */
function VideoControls({ head, actions }: { head: EntityVideoHead; actions: EntityFilterActions }) {
  return (
    <span data-entity-sorts="">
      <Shuffle onPress={() => void actions.reshuffle()} />
      {head.jav ? (
        <Segments label="JAV 卡片版式" value={head.jav.layout} options={head.jav.options} onChange={actions.setJavLayout} />
      ) : null}
      {head.sorts.map((sort) => {
        const Arrow = spriteGlyph(sort.dir === 'asc' ? 'arrow-up' : 'arrow-down');
        return (
          <button key={sort.key} type="button" data-entity-sort={sort.key} data-entity-press=""
            aria-pressed={sort.pressed} aria-label={sort.ariaLabel || undefined} onClick={() => actions.setSort(sort.key)}>
            {sort.label}{sort.pressed && sort.dir ? <Arrow className="size-3.5" /> : null}
          </button>
        );
      })}
    </span>
  );
}

/** 照片视图：这一排不给排序键（账本里图片只有文件名、体积和来源），只放换一批、图片布局，
 *  在一个图集里再加那两枚源文件键。换一批的键自己转圈，等到新的一面墙回来。 */
function PhotoControls({ head, actions, helpers }: {
  head: EntityPhotoHead; actions: EntityFilterActions; helpers: EntityFilterHelpers;
}) {
  const [shuffling, setShuffling] = useState(false);
  const tools = useRef<HTMLSpanElement>(null);
  const toolsHtml = head.back ? helpers.sourceToolsHtml(head.setId) : '';
  useEffect(() => { if (tools.current && toolsHtml) helpers.wireSourceTools(tools.current) }, [helpers, toolsHtml]);
  const shuffle = () => {
    setShuffling(true);
    actions.reshuffle().finally(() => setShuffling(false));
  };
  return (
    <span data-entity-sorts="">
      {head.shuffle ? <Shuffle onPress={shuffle} busy={shuffling} /> : null}
      <Segments label="图片布局" value={head.layout} options={head.layouts} onChange={actions.setPhotoLayout} />
      {toolsHtml ? <span ref={tools} data-entity-srctools="" dangerouslySetInnerHTML={{ __html: toolsHtml }} /> : null}
    </span>
  );
}
