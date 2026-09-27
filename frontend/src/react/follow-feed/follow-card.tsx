/* 关注页的一张卡：一个作品，本站的 alt 与 WIP、跨站的另见都折在里面。
 *
 * 形状同馆藏作品卡（`../components/media-card.tsx`）：封面格在上，下面一行头像、两行标题、一行署名
 * 与时间，再往下是另见徽章、标签和「媒体未取得」。封面格左上是来源角标，右下是时长，右上是合并
 * 计数；悬停时计数让位，右上角换成保存、已看、忽略几枚圆键，触屏上它们常驻。
 *
 * 结构与样式钩子沿用作品卡的 `data-media-*`（几何、悬停面、选中描边、勾选圆都在
 * `../components/media-card.css`），关注卡自己多出来的几格用 `data-follow-*`，写在
 * `./follow-feed.css`。标题前的版本字样、另见徽章、头像圆框与来源图标是遗留层拼的 HTML，详情里
 * 用的是同一份，这一格 React 不拥有里面的节点。
 *
 * 一叠（`isMix`）悬停时逐张翻过组里彼此不同的画面，时序与门槛同 Mix 卡（`../components/use-stack-flip.ts`）。
 * 翻的是卡片渲染时就在手上的缩略图，悬停不为动画再发请求；第一张是静止封面本身。 */
import { memo, useCallback, useRef, useState, type MouseEvent } from 'react';
import { esc, fmtDur, icon } from '@peach/legacy/core';

import { MIX_FLIP_FACES, useStackFlip } from '../components/use-stack-flip';
import {
  followStack, itemForMedia, videoItems, type FollowContext, type FollowFeedActions, type FollowFeedHelpers,
  type FollowGroup, type FollowMedia, type FollowSource,
} from './follow-feed';

/** 时长只在是真时长时写：来源没给、给了 0 或给了一个明显是占位的数，都不出这一格。 */
const realDuration = (value: unknown) => Number(value) > 0;

/** 列表里时间只写到日：今年的去掉年份，往年的留着。悬停读得到完整时间。 */
function compactWhen(when: string): string {
  if (!/^\d{4}-/.test(when)) return when;
  return when.startsWith(String(new Date().getFullYear())) ? when.slice(5, 10) : when.slice(0, 10);
}

export interface FollowCardProps {
  group: FollowGroup;
  /** 这张卡的创作者名下那几个来源：头像与署名读它。 */
  authorSources: readonly FollowSource[];
  media: FollowMedia;
  context: FollowContext;
  selected: boolean;
  selectMode: boolean;
  /** 这张卡正在写的那一下（状态或保存），和写失败时留在卡上的那一句。 */
  busy: string;
  failure: string;
  helpers: FollowFeedHelpers;
  actions: FollowFeedActions;
  onStatus(id: number, to: string): void;
  onSave(id: number): void;
}

/** 卡面那张图。取不到就撤掉，只剩封面格的底色，同遗留层 `data-drop="self"`。 */
function Thumb({ src, width, height, onLearn }: {
  src: string; width?: number; height?: number; onLearn?: (width: number, height: number) => void;
}) {
  const [broken, setBroken] = useState(false);
  if (broken) return null;
  return (
    <img src={src} alt="" loading="lazy" referrerPolicy="no-referrer" width={width} height={height}
      onError={() => setBroken(true)}
      onLoad={onLearn ? (event) => {
        const image = event.currentTarget;
        if (image.naturalWidth && image.naturalHeight) onLearn(image.naturalWidth, image.naturalHeight);
      } : undefined} />
  );
}

function FollowCardView(props: FollowCardProps) {
  const { group, authorSources, media, context, selected, selectMode, busy, failure, helpers, actions } = props;
  const item = itemForMedia(group, media);
  const imageView = media === 'images';
  const selectedMedia = imageView ? (item.media_items || []).find((entry) => entry.media_kind === 'image') : undefined;
  const thumbUrl = selectedMedia?.thumb_url || item.thumb_url || '';
  /* width/height 让浏览器在图片落地前就按固有比例占位：瀑布流按卡片高度分列，没有这两个属性时
     未加载的图高度是零，每一张加载完都把整墙的列重新平衡一遍，卡片就在列间跳。只有图片视图摆成
     瀑布流，视频卡片不占位也不回写。比例取卡面上这张图自己的：卡面是媒体清单里那张就落在那张上；
     卡面就是条目自己的缩略图时落在条目上。都没有就不硬猜，走无尺寸占位那套，并在这张图加载完后
     把固有尺寸回写给它的主人。 */
  const cardMedia = selectedMedia && selectedMedia.thumb_url === thumbUrl ? selectedMedia : null;
  const itemOwnsCard = !cardMedia || thumbUrl === item.thumb_url;
  const sized = imageView
    ? [cardMedia, itemOwnsCard ? item : null].find((owner) => Number(owner?.width) > 0 && Number(owner?.height) > 0)
    : null;
  const learn = imageView && !sized && thumbUrl
    ? (width: number, height: number) => helpers.learnDims(item.id, cardMedia ? cardMedia.index : null, width, height)
    : undefined;
  const videos = media === 'videos' ? videoItems(group) : [];
  const embedded = item.media_items || [];
  const mixTarget = embedded.length > 1 ? item.id : (videos[0]?.id || item.id);
  /* 角标与翻卡都取服务端对整组的判定（`group.stack`）：同一个画面只翻一次，跨站重复算来源。 */
  const stack = followStack({
    cover: thumbUrl, coverFace: (selectedMedia?.thumb_url ? selectedMedia : item).face, stack: group.stack,
    imageView, limit: MIX_FLIP_FACES,
  });
  const faces = useRef(stack.faces);
  faces.current = stack.faces;
  const flip = useStackFlip({
    load: async () => faces.current, canFlip: () => faces.current.length > 1 && actions.canFlip(),
    referrerPolicy: 'no-referrer',
  });
  /* 壳在滚动、换页和开多选时按 `_stopHover` 收掉一切悬停动效，这张卡的翻页也在其中。 */
  const stop = useRef(flip.onPointerLeave);
  stop.current = flip.onPointerLeave;
  const attach = useCallback((el: (HTMLElement & { _stopHover?: () => void }) | null) => {
    if (el) el._stopHover = () => stop.current();
  }, []);

  const identity = helpers.identity(item, authorSources, context);
  const when = helpers.when(item);
  const tags = (item.tags || []).slice(0, 3);
  const issue = helpers.mediaIssue(item, context);
  const badges = helpers.badges(group, item);
  const saved = item.status === 'saved';

  const click = (event: MouseEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    /* 标签在这张卡上只是读的，点它什么都不做，多选里也不算点了这张卡。 */
    if (target.closest('[data-media-tag]')) return;
    if (selectMode || event.shiftKey || event.ctrlKey || event.metaKey) {
      event.preventDefault();
      actions.toggleSelection(item.id, event.shiftKey);
      return;
    }
    actions.openDetail(item.id);
  };
  const act = (event: MouseEvent, run: () => void) => { event.stopPropagation(); run() };

  return (
    <article ref={attach} data-media-card="" data-follow-item={item.id} data-status={item.status}
      data-follow-image={imageView ? '' : undefined} data-collection={stack.isMix ? '' : undefined}
      data-selected={selected ? '' : undefined} onClick={click}
      onMouseEnter={flip.onPointerEnter} onMouseLeave={flip.onPointerLeave}>
      <div data-follow-visual="" data-mix-stack={stack.isMix ? '' : undefined}>
        <div data-media-pic="">
          <button type="button" data-follow-open="" aria-label={`打开 ${item.title} 详情`} />
          {thumbUrl
            ? <Thumb key={thumbUrl} src={thumbUrl} width={sized?.width} height={sized?.height} onLearn={learn} />
            : <span data-follow-nothumb="" dangerouslySetInnerHTML={{ __html: helpers.sourceIcon(item.resource_provider || item.provider) }} />}
          {stack.faces.length > 1 ? (
            <div data-mix-faces="" hidden={!flip.faces.length}>
              {flip.faces.map((src, index) => (
                <div key={src} data-mix-face={index === flip.current ? 'on' : index === flip.leaving ? 'off' : ''}>
                  <img src={src} alt="" loading="eager" referrerPolicy="no-referrer" />
                </div>
              ))}
            </div>
          ) : null}
          <span data-media-badge="" title={item.provider_label} aria-label={`来源：${item.provider_label || ''}`}
            dangerouslySetInnerHTML={{ __html: helpers.sourceIcon(item.provider) }} />
          <span data-media-check="" onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            actions.toggleSelection(item.id, event.shiftKey);
          }} dangerouslySetInnerHTML={{ __html: icon('check') }} />
          {realDuration(item.duration) ? <span data-media-duration="">{fmtDur(item.duration)}</span> : null}
          <div data-follow-corner="">
            {stack.isMix ? (
              <button type="button" data-follow-collection={mixTarget}
                onClick={(event) => act(event, () => actions.openDetail(mixTarget))}>
                <span className="contents" dangerouslySetInnerHTML={{ __html: icon(stack.glyph) }} />{stack.label}
              </button>
            ) : null}
            <div data-follow-actions="">
              <button type="button" data-follow-save={item.id} title={saved ? '已保存' : '保存到账本'}
                aria-label={saved ? '已保存' : '保存到账本'} disabled={saved}
                aria-busy={busy === 'save' || undefined} aria-disabled={busy === 'save' || undefined}
                onClick={(event) => act(event, () => props.onSave(item.id))}
                dangerouslySetInnerHTML={{ __html: icon(saved ? 'check' : 'bookmark-plus') }} />
              <button type="button" data-follow-status={item.id} data-to="seen" title="标记已看" aria-label="标记已看"
                disabled={item.status === 'seen'} aria-busy={busy === 'seen' || undefined}
                aria-disabled={busy === 'seen' || undefined}
                onClick={(event) => act(event, () => props.onStatus(item.id, 'seen'))}
                dangerouslySetInnerHTML={{ __html: icon('eye') }} />
              <button type="button" data-follow-status={item.id} data-to="ignored" title="忽略" aria-label="忽略"
                disabled={item.status === 'ignored'} aria-busy={busy === 'ignored' || undefined}
                aria-disabled={busy === 'ignored' || undefined}
                onClick={(event) => act(event, () => props.onStatus(item.id, 'ignored'))}
                dangerouslySetInnerHTML={{ __html: icon('eye-off') }} />
              {item.status === 'seen' || item.status === 'ignored' ? (
                <button type="button" data-follow-status={item.id} data-to="new" title="恢复未看" aria-label="恢复未看"
                  aria-busy={busy === 'new' || undefined} aria-disabled={busy === 'new' || undefined}
                  onClick={(event) => act(event, () => props.onStatus(item.id, 'new'))}
                  dangerouslySetInnerHTML={{ __html: icon('rotate-ccw') }} />
              ) : null}
            </div>
          </div>
        </div>
      </div>
      <div data-media-meta="">
        <span data-media-avatar="" data-follow-avatar="" title="创作者头像"
          dangerouslySetInnerHTML={{ __html: identity.avatar }} />
        <div data-media-text="">
          <button type="button" data-media-title=""
            dangerouslySetInnerHTML={{ __html: helpers.titleMarks(group, item) + esc(item.title) }} />
          <div data-follow-byline="">
            <span data-follow-author="" title={identity.author}>{identity.author}</span>
            <time dateTime={item.published_at || ''} title={when}>{compactWhen(when)}</time>
          </div>
          {identity.credited
            ? <div data-follow-credit="" title={`署名含 ${identity.credited}`}>{`署名含 ${identity.credited}`}</div>
            : null}
          {badges ? <div data-follow-badges="" dangerouslySetInnerHTML={{ __html: badges }} /> : null}
          {tags.length ? (
            <div data-media-tags="">
              {tags.map((tag) => (
                <span key={tag} data-media-tag="" data-tag-cat={`r34-${item.tag_types?.[tag] || 'unknown'}`}
                  data-follow-tag={tag}>
                  {helpers.tagLabel(tag)}
                </span>
              ))}
            </div>
          ) : null}
          {issue ? <span data-follow-issue="">{issue}</span> : null}
        </div>
      </div>
      <span data-follow-state="" aria-live="polite">{failure}</span>
    </article>
  );
}

/** 一屏几百张，选择与写操作之外的重画不该连带每一张：比较的都是引用，壳递进来的助手与动作身份不变。 */
export const FollowCard = memo(FollowCardView);
