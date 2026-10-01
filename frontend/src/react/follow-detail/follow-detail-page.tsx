/* 关注详情（ADR-0031）：舞台里那一整块——媒体区、右侧队列与侧栏。
 *
 * 舞台（`<dialog id="stage">`）、它的进出场、小窗与 Video.js 都归舞台岛（`../stage/`），JAV 详情
 * 也在用；这里只画舞台里的内容，视频的媒体框画好之后经 `actions.mountPlayer` 交给舞台挂播放器。媒体区、侧栏与队列的结构照
 * JAV 详情那一套（`[data-stage-grid]` / `[data-stage-media]` / `[data-stage-side]` / `[data-mix-queue]`，两边共用，
 * 样式在 `../stage/stage.css`）；关注自己多出来的几块样式在 `follow-detail.css`。
 *
 * 换一份媒体（轮播、多媒体队列）只改岛内状态：媒体区按「条目:媒体」换一块，播放器随之拆了重挂。
 * 换到组里另一条经壳（`actions.openItem`），因为舞台上的播放器要先拆、地址也要换。 */
import { useCallback, useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { esc, fmtDur, foldName, icon, requestErrorMessage } from '@peach/legacy/core';

import { apiSend } from '../../api';
import { RetryNote } from '../components/grid-reveal';
import { MixGroupLabel, MixQueue, MixQueueRow } from '../components/mix-queue';
import {
  FOLLOW_CREDENTIALS_KEY, fetchFollowCredentials, replaceFollowItem, setFollowItemStatus, videoItems,
  type FollowContext, type FollowFeedHelpers, type FollowGroup,
} from '../follow-feed/follow-feed';
import {
  followBadges, followIdentity, followMediaIssue, followTitleMarks, followWhen, sourceIcon,
} from '../follow-feed/follow-marks';
import { FOLLOW_STATUS_URL } from '../follow-manage/follow-manage';
import { openPhotoLightbox } from '../photo-lightbox/photo-lightbox-dialog';
import { queryClient } from '../query';
import {
  FOLLOW_MEDIA_HIDE_URL, FOLLOW_SAVE_URL, authorSources, collectionCopy, detailContext, detailMedia, detailSlides,
  detailTags, fetchFollowItem, followItemKey, groupedMediaOwner, mediaName, resourceLabel, statusReceipt, tagCategory,
  type DetailMedia, type FollowDetailActions, type FollowDetailData, type FollowDetailItem, type FollowDetailMedia,
  type FollowDetailProps,
} from './follow-detail';

const realDuration = (value: unknown) => Number(value) > 0;

/** 字形原样取壳那一份 `icon()`：骨架与遗留详情画的就是它，换成别的字形接管那一拍会跳。 */
const Glyph = ({ name }: { name: string }) => (
  <span className="contents" dangerouslySetInnerHTML={{ __html: icon(name) }} />
);
/** 外链那一枚：描边由全站 `svg.externalmark` 给，这一页的 18px 尺寸在 `follow-detail.css`。 */
const EXTERNAL_MARK = icon('external-link', 'externalmark');

export function FollowDetailPage(props: FollowDetailProps) {
  const { id, actions } = props;
  const result = useQuery({ queryKey: followItemKey(id), queryFn: ({ signal }) => fetchFollowItem(id, signal) });
  const credentialsResult = useQuery({
    queryKey: FOLLOW_CREDENTIALS_KEY, queryFn: ({ signal }) => fetchFollowCredentials(signal),
  });
  const credentials = useMemo(() => new Set((credentialsResult.data?.providers || [])
    .filter((provider) => provider.present).map((provider) => provider.provider)), [credentialsResult.data]);
  const [mediaIndex, setMediaIndex] = useState(props.mediaIndex);

  if (!result.data) {
    return (
      <div data-stage-grid="" data-follow-detail="">
        <div data-stage-media="" data-follow-detail-media="none">
          <CloseStage onClose={actions.close} />
          <div data-follow-detail-placeholder="">
            {result.isError
              ? <RetryNote message={requestErrorMessage(result.error)} onRetry={() => void result.refetch()} />
              : null}
          </div>
        </div>
      </div>
    );
  }
  return (
    <Detail {...props} data={result.data} context={detailContext(result.data, credentials)}
      mediaIndex={mediaIndex} onMedia={setMediaIndex} />
  );
}

/** 关闭键。`id` 留着：Escape、点浮窗外面与壳的兜底都按 `#closeStage` 找它再点一下。 */
const CloseStage = ({ onClose }: { onClose(): void }) => (
  <button type="button" data-stage-close="" id="closeStage" title="关闭" aria-label="关闭" onClick={onClose}
    dangerouslySetInnerHTML={{ __html: icon('x') }} />
);

function Detail({ data, context, mediaIndex, onMedia, mediaView, helpers, actions }: FollowDetailProps & {
  data: FollowDetailData; context: FollowContext; onMedia(index: number | null): void;
}) {
  const { item, group } = data;
  const media = detailMedia(item, group, mediaIndex, mediaView);
  const write = useDetailWrite(item, actions, onMedia);
  /* 媒体没取回的那两句提示只说这一块媒体区：换一份媒体就从头来。 */
  const frameKey = `${item.id}:${media.selected?.index ?? ''}`;
  const [issue, setIssue] = useState<{ key: string; kind: MediaIssue }>({ key: '', kind: '' });
  const issues: MediaIssues = {
    failed: () => setIssue({ key: frameKey, kind: 'failed' }),
    thumbFallback: () => setIssue({ key: frameKey, kind: 'thumb' }),
  };

  useLayoutEffect(() => { actions.present(item, media.kind) }, [actions, item, media.kind]);

  const owner = !media.embedded.length && media.collection ? groupedMediaOwner(media.collection) : undefined;
  const queue = media.embeddedQueue
    ? <MediaQueue item={item} current={media.selected!.index} helpers={helpers} actions={actions} onMedia={onMedia} />
    : media.collection
      ? owner
        ? <MediaQueue item={owner} current={null} helpers={helpers} actions={actions} onMedia={onMedia} currentId={item.id} />
        : <CollectionQueue group={media.collection} itemId={item.id} helpers={helpers} actions={actions} />
      : null;

  return (
    <div data-stage-grid="" data-with-queue={queue ? '' : undefined} data-follow-detail="">
      <MediaFrame key={frameKey} item={item} media={media}
        helpers={helpers} actions={actions} onMedia={onMedia} issues={issues} />
      {queue}
      <Side item={item} data={data} context={context} media={media} write={write}
        issue={issue.key === frameKey ? issue.kind : ''} helpers={helpers} actions={actions} />
    </div>
  );
}

/* ── 媒体区 ── */

function MediaFrame({ item, media, helpers, actions, onMedia, issues }: {
  item: FollowDetailItem; media: DetailMedia; helpers: FollowFeedHelpers; actions: FollowDetailActions;
  onMedia(index: number | null): void; issues: MediaIssues;
}) {
  const { kind, selected, src, images, position, carousel, frameRatio } = media;
  const frame = useRef<HTMLDivElement>(null);
  const [inset, setInset] = useState<number | null>(null);
  const slides = detailSlides(item, media);
  /* 原图经代理取，缩略图由浏览器直接读公开主机：归档站的原文件主机会拦下服务端（pawchive 的
     file. 子域挂着 ddos-guard，一律 403），缩略图主机照常给。 */
  const thumb = selected?.thumb_url || item.thumb_url || '';
  const playable = item.playable && kind === 'video';
  const imageSrc = item.playable && kind === 'image' ? src : item.thumb_url || '';
  const fallback = item.playable && kind === 'image' && thumb && thumb !== src ? thumb : '';
  const [shown, setShown] = useState(imageSrc);

  /* 播放器只随这一块媒体区挂一次、卸一次：写完状态换的是同一条的新对象，不能因此拆了重挂。
     这一块本身按「条目:媒体」换，换条目或换媒体时整块重建，清理就在那一刻跑。`<video>` 由舞台
     建在这块框里（同作品详情），报错时回到这里说明。 */
  const mounting = useRef({ item, selected });
  const failed = useRef(issues.failed);
  failed.current = issues.failed;
  useLayoutEffect(() => {
    const node = frame.current;
    if (!node || !playable) return;
    return actions.mountPlayer(node, mounting.current.item, mounting.current.selected, { onError: () => failed.current() });
  }, [actions, playable]);

  /* object-fit:contain 之后图片左右的黑边随图片比例和窗口变。箭头落在黑边的视觉中心，不永远
     贴着容器边缘；黑边太窄时才退回固定的安全内边距。 */
  useLayoutEffect(() => {
    const box = frame.current;
    const image = box?.querySelector<HTMLImageElement>('[data-follow-detail-poster]');
    const arrow = box?.querySelector<HTMLElement>('[data-follow-image-step]');
    if (!box || !image || !arrow) return;
    const align = () => {
      if (!image.naturalWidth || !image.naturalHeight) return;
      const rect = box.getBoundingClientRect();
      const rendered = Math.min(rect.width, rect.height * (image.naturalWidth / image.naturalHeight));
      const gutter = Math.max(0, (rect.width - rendered) / 2);
      const safe = matchMedia('(max-width:640px)').matches ? 10 : 16;
      setInset(Math.round(gutter >= arrow.offsetWidth + safe * 2 ? (gutter - arrow.offsetWidth) / 2 : safe));
    };
    const observer = new ResizeObserver(align);
    observer.observe(box);
    image.addEventListener('load', align);
    return () => { observer.disconnect(); image.removeEventListener('load', align) };
  }, [shown]);

  const step = (delta: number) => onMedia(images[(position + delta + images.length) % images.length]!.index);
  return (
    <div ref={frame} data-stage-media="" data-follow-detail-media={kind || 'none'} data-framed={frameRatio ? '' : undefined}
      // oxlint-disable-next-line shadcn/no-inline-styles -- 画框比例与箭头内距是按这一组图的尺寸和当前视口算出来的
      style={{ '--follow-frame-ratio': frameRatio ? frameRatio.toFixed(4) : undefined, '--follow-image-arrow-inset': inset === null ? undefined : `${inset}px` } as CSSProperties}>
      <CloseStage onClose={actions.close} />
      {playable ? null : imageSrc ? (
        <img data-follow-detail-poster="" data-zoomable={slides.length ? '' : undefined} src={shown} alt={item.title}
          referrerPolicy="no-referrer"
          onClick={slides.length ? () => void openPhotoLightbox(Math.max(0, position), slides) : undefined}
          onError={() => {
            if (fallback && shown !== fallback) { setShown(fallback); issues.thumbFallback(); return }
            issues.failed();
          }} />
      ) : (
        <div data-follow-detail-placeholder="">
          <span className="contents" dangerouslySetInnerHTML={{ __html: sourceIcon(item.resource_provider || item.provider) }} />
          <span>没有可用预览</span>
        </div>
      )}
      {carousel ? (
        <>
          <button type="button" data-follow-image-step="-1" data-follow-image-arrow="prev" aria-label="上一张图片" title="上一张"
            onClick={() => step(-1)} dangerouslySetInnerHTML={{ __html: icon('chevron-left') }} />
          <button type="button" data-follow-image-step="1" data-follow-image-arrow="next" aria-label="下一张图片" title="下一张"
            onClick={() => step(1)} dangerouslySetInnerHTML={{ __html: icon('chevron-right') }} />
          <div data-follow-image-dots="" role="group" aria-label={`${images.length} 张图片`}>
            {images.map((image, index) => (
              <button type="button" key={image.index} data-follow-image-item={image.index}
                aria-current={index === position ? 'true' : 'false'}
                aria-label={`第 ${index + 1} 张，共 ${images.length} 张`} title={`第 ${index + 1} 张`}
                onClick={() => onMedia(image.index)} />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

/* ── 队列 ── */

/** 队列里没有画面的那一格放中性图形，不放站点图标：格子里的图一律按画面铺满，48px 的 favicon
 *  会被拉成整格，看上去就像这条视频的缩略图。 */
const NoThumb = ({ kind }: { kind: string }) => (
  <span data-follow-nothumb="" dangerouslySetInnerHTML={{ __html: icon(kind === 'image' ? 'image-off' : 'play') }} />
);

/** 缩略图取不到就撤掉，同遗留层 `data-drop="self"`。 */
function QueueThumb({ src }: { src: string }) {
  const [broken, setBroken] = useState(false);
  if (broken) return null;
  return <img src={src} alt="" loading="lazy" referrerPolicy="no-referrer" onError={() => setBroken(true)} />;
}

function useDragRow(helpers: FollowFeedHelpers) {
  return useCallback((node: HTMLDivElement | null) => { if (node) helpers.wireDrag(node) }, [helpers]);
}

function CollectionQueue({ group, itemId, helpers, actions }: {
  group: FollowGroup; itemId: number; helpers: FollowFeedHelpers; actions: FollowDetailActions;
}) {
  const items = videoItems(group) as FollowDetailItem[];
  const listRef = useDragRow(helpers);
  return (
    <MixQueue kind="collection" data-follow-queue="" title="视频合集" onClose={actions.close} listRef={listRef}
      summary={`${group.primary.title || '未命名合集'} · ${items.length} 个视频`}>
      {items.map((member) => {
        const duplicate = group.duplicates.includes(member);
        const copy = collectionCopy(group, member, duplicate ? member.provider_label : '');
        /* 另一站的同一条由站点图标报出处，图标的 alt 就是站名；没登记图标的站仍写站名。 */
        const siteIcon = duplicate ? sourceIcon(member.provider, member.provider_label) : '';
        return (
          <MixQueueRow key={member.id} current={member.id === itemId} data-follow-queue-item={member.id}
            onClick={() => actions.openItem(member.id)}
            pic={<>
              {member.thumb_url ? <QueueThumb src={member.thumb_url} /> : <NoThumb kind="video" />}
              {realDuration(member.duration) ? <i className="mono" data-mix-item-duration="">{fmtDur(member.duration)}</i> : null}
            </>}>
            <b data-truncate-end="">{copy.title}</b>
            <span data-follow-queue-meta="">
              {siteIcon
                ? <span data-follow-queue-source="" dangerouslySetInnerHTML={{ __html: siteIcon }} />
                : <i data-follow-variant={member.variant_kind || ''}>{copy.label}</i>}
              <time dateTime={member.published_at || ''}>{followWhen(member)}</time>
            </span>
          </MixQueueRow>
        );
      })}
    </MixQueue>
  );
}

/** 多媒体队列：一条帖子里的全部图与视频，按网盘分组。`currentId` 是舞台上正看着的那一条——
 *  合集改列组里挂着网盘分组的那一条时，它和队列的主人不是同一条。 */
function MediaQueue({ item, current, currentId = item.id, helpers, actions, onMedia }: {
  item: FollowDetailItem; current: number | null; currentId?: number; helpers: FollowFeedHelpers;
  actions: FollowDetailActions; onMedia(index: number | null): void;
}) {
  const items = item.media_items || [];
  const listRef = useDragRow(helpers);
  const groups: { key: string; label: string; items: FollowDetailMedia[] }[] = [];
  items.forEach((media) => {
    const key = media.resource_group || 'ungrouped';
    let row = groups.find((entry) => entry.key === key);
    if (!row) { row = { key, label: media.resource_group_label || '', items: [] }; groups.push(row) }
    row.items.push(media);
  });
  const pick = (media: FollowDetailMedia) => (item.id === currentId ? onMedia(media.index) : actions.openItem(item.id, media.index));
  return (
    <MixQueue kind="media" data-follow-queue="" title="多媒体" onClose={actions.close} listRef={listRef}
      summary={`${item.title || '未命名内容'} · ${items.length} 个媒体`}>
      {groups.map((row) => [
        row.label ? <MixGroupLabel key={`label:${row.key}`} label={row.label} count={row.items.length} /> : null,
        ...row.items.map((media) => (
          <MixQueueRow key={media.index} current={media.index === current} data-follow-media-owner={item.id}
            data-follow-media-item={media.index} data-media-kind={media.media_kind || ''} onClick={() => pick(media)}
            pic={media.thumb_url ? <QueueThumb src={media.thumb_url} /> : <NoThumb kind={media.media_kind || ''} />}>
            <b data-middle-truncate="">{mediaName(media)}</b>
            <span data-truncate-end="">{media.media_kind === 'image' ? '图片' : '视频'}</span>
          </MixQueueRow>
        )),
      ])}
    </MixQueue>
  );
}

/* ── 侧栏 ── */

function Side({ item, data, context, media, write, issue, helpers, actions }: {
  item: FollowDetailItem; data: FollowDetailData; context: FollowContext; media: DetailMedia;
  write: DetailWrite; issue: MediaIssue; helpers: FollowFeedHelpers; actions: FollowDetailActions;
}) {
  const { kind, selected, src } = media;
  const single: FollowGroup = { primary: item, variants: [], duplicates: [], has_wip: item.variant_kind === 'wip' };
  const badges = followBadges(single, item);
  const identity = followIdentity(item, authorSources(item, data.sources), context);
  const postedBy = identity.credited ? ''
    : item.author && foldName(item.author) !== foldName(identity.author) ? item.author : '';
  const mediaIssue = followMediaIssue(item, context);
  const tags = detailTags(item, helpers.tagLabel);
  const saved = item.status === 'saved';
  const { busy } = write;
  const busyAttrs = (key: string) => (busy.has(key) ? { 'aria-busy': true, 'aria-disabled': true } as const : {});
  return (
    <div data-stage-side="" data-follow-detail-side="">
      <div data-stage-side-content="">
        <div data-follow-detail-title="">
          <div data-stage-title="" data-follow-detail-name="" data-reveal-line=""
            dangerouslySetInnerHTML={{ __html: followTitleMarks(single, item) + esc(item.title) }} />
          {item.url ? (
            <a data-follow-origin="" href={item.url} target="_blank" rel="noreferrer noopener"
              title="打开来源页面" aria-label="打开来源页面"
              dangerouslySetInnerHTML={{ __html: EXTERNAL_MARK }} />
          ) : null}
        </div>
        <div data-follow-detail-identity="">
          <span data-follow-source-avatar="" dangerouslySetInnerHTML={{ __html: identity.avatar }} />
          <div>
            <b>{identity.author}</b>
            {postedBy ? <span>发布者 {postedBy}</span> : null}
            {identity.credited ? <span>署名含 {identity.credited}</span> : null}
          </div>
        </div>
        <div className="mono" data-stage-meta="" data-reveal-line="">
          <span>{followWhen(item)}</span>
          {realDuration(item.duration) ? <span>{fmtDur(item.duration)}</span> : null}
          {badges ? <span data-follow-badges="" dangerouslySetInnerHTML={{ __html: badges }} /> : null}
        </div>
        {item.summary ? <p data-follow-detail-summary="">{item.summary}</p> : null}
        {mediaIssue ? <p data-follow-media-issue="">{mediaIssue}</p> : null}
        {/* 上游没给出媒体时，代理只会回一个不含缘由的失败。有缩略图就换上缩略图并说明这是缩略图；
            连缩略图也取不到，才说「这次没取到、多半是限流」——别让人对着一块空画布猜。 */}
        <p data-follow-media-issue="" data-media-load-issue="" hidden={issue !== 'failed'}>
          媒体未取回：上游这一次没有返回内容，多半是站点限流，过一阵再打开。
        </p>
        <p data-follow-media-issue="" data-media-thumb-fallback="" hidden={issue !== 'thumb'}>
          原图未取回，先显示缩略图：上游拦下了这一次请求。
        </p>
        {item.resource_urls?.length ? (
          <div data-follow-resources="">
            {item.resource_urls.map((url) => (
              <a key={url} href={url} target="_blank" rel="noreferrer noopener">
                {resourceLabel(url)}<span className="contents" dangerouslySetInnerHTML={{ __html: EXTERNAL_MARK }} />
              </a>
            ))}
          </div>
        ) : null}
        <div data-stage-actions="" data-follow-detail-actions="">
          <button type="button" data-stage-action="later" data-follow-detail-save="" aria-label={saved ? '已保存' : '保存到账本'}
            title={saved ? '已保存' : '保存到账本'} disabled={saved} {...busyAttrs('save')}
            onClick={write.save} dangerouslySetInnerHTML={{ __html: icon(saved ? 'check' : 'bookmark-plus') }} />
          <button type="button" data-stage-action="seen" data-follow-detail-status="seen" aria-label="标记已看" title="标记已看"
            aria-pressed={item.status === 'seen'} {...busyAttrs('seen')} onClick={() => write.status('seen')}
            dangerouslySetInnerHTML={{ __html: icon('eye') }} />
          <button type="button" data-stage-action="dislike" data-follow-detail-status="ignored" aria-label="忽略" title="忽略"
            aria-pressed={item.status === 'ignored'} {...busyAttrs('ignored')} onClick={() => write.status('ignored')}
            dangerouslySetInnerHTML={{ __html: icon('eye-off') }} />
          {item.status === 'seen' || item.status === 'ignored' ? (
            <button type="button" data-follow-detail-status="new" aria-label="恢复未看" title="恢复未看"
              {...busyAttrs('new')} onClick={() => write.status('new')}
              dangerouslySetInnerHTML={{ __html: icon('rotate-ccw') }} />
          ) : null}
          {kind === 'image' && selected ? (
            <button type="button" data-stage-action="dislike" data-follow-media-hide={selected.index} aria-label="隐藏这张图"
              title="隐藏这张图" {...busyAttrs(`hide:${selected.index}`)} onClick={() => write.hide(selected.index)}
              dangerouslySetInnerHTML={{ __html: icon('image-off') }} />
          ) : null}
          {src ? (
            <a data-follow-download="" href={`${src}${src.includes('?') ? '&' : '?'}download=1`} download=""
              aria-label="下载到本地" title="下载到本地" dangerouslySetInnerHTML={{ __html: icon('download') }} />
          ) : null}
        </div>
        {/* 被隐藏的图退到这条恢复带上：缩略图加一枚撤销键，点了就回到轮播。不占媒体队列，也不进
            角标数——它们已经是「不在看」的那部分。 */}
        {item.hidden_media?.length ? (
          <div data-follow-hidden-media="">
            <span data-follow-hidden-label="">已隐藏 {item.hidden_media.length} 张</span>
            <div data-follow-hidden-thumbs="">
              {item.hidden_media.map((hidden) => (
                <button type="button" key={hidden.index} data-follow-media-restore={hidden.index}
                  title={`恢复显示 ${hidden.name || ''}`} aria-label={`恢复显示 ${hidden.name || ''}`}
                  {...busyAttrs(`restore:${hidden.index}`)} onClick={() => write.restore(hidden.index)}>
                  {hidden.thumb_url ? <QueueThumb src={hidden.thumb_url} /> : <Glyph name="image-off" />}
                  <i dangerouslySetInnerHTML={{ __html: icon('rotate-ccw') }} />
                </button>
              ))}
            </div>
          </div>
        ) : null}
        <span data-follow-state="" aria-live="polite">{write.failure}</span>
        {tags.length ? (
          <div data-stage-tags="" data-follow-detail-tags="">
            {tags.map((tag) => (
              <button type="button" key={tag} data-tag-cat={tagCategory(item, tag)} data-follow-tag={tag}
                onClick={() => actions.openTag(tag)}>{helpers.tagLabel(tag)}</button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

/* ── 写操作 ──
 * 保存、状态、隐藏与恢复这张图都在岛里发。状态与保存成功后在两处缓存里换同一条（详情这条与
 * 关注页列表里那一条，卡面状态一起变），不重读列表：关掉详情回列表不该再等一个网络往返。
 * 隐藏与恢复换掉的是整份媒体清单，重取一次这一条，服务端投影给出新的可见集合与缩略图。 */
type MediaIssue = '' | 'failed' | 'thumb';
type MediaIssues = { failed(): void; thumbFallback(): void };
type DetailWrite = ReturnType<typeof useDetailWrite>;

function useDetailWrite(item: FollowDetailItem, actions: FollowDetailActions, onMedia: (index: number | null) => void) {
  const id = item.id;
  const key = followItemKey(id);
  const [busy, setBusy] = useState<ReadonlySet<string>>(() => new Set());
  const [failure, setFailure] = useState('');
  const mark = (name: string, on: boolean) => setBusy((now) => {
    const next = new Set(now);
    if (on) next.add(name); else next.delete(name);
    return next;
  });
  const apply = (to: string) => {
    queryClient.setQueryData<FollowDetailData>(key, (data) => (data ? { ...data, item: { ...data.item, status: to } } : data));
    setFollowItemStatus(id, to);
  };
  const failed = (error: unknown) => {
    setFailure(requestErrorMessage(error) || '操作失败');
    actions.failure('更新关注状态', error);
  };
  const statusMutation = useMutation({
    mutationFn: ({ to }: { to: string; was: string }) => apiSend(FOLLOW_STATUS_URL, { item: id, to }),
    onSuccess: (_result, { to, was }) => {
      apply(to);
      setFailure('');
      actions.toast(statusReceipt(to), {
        undo: was !== 'saved' ? async () => { await apiSend(FOLLOW_STATUS_URL, { item: id, to: was }); apply(was) } : undefined,
      });
    },
    onError: failed,
    onSettled: (_result, _error, { to }) => mark(to, false),
  });
  const saveMutation = useMutation({
    mutationFn: () => apiSend(FOLLOW_SAVE_URL, { item: id }),
    onSuccess: () => { apply('saved'); setFailure(''); actions.toast('已保存到账本') },
    onError: failed,
    onSettled: () => mark('save', false),
  });
  const mediaMutation = useMutation({
    mutationFn: async ({ index, hidden }: { index: number; hidden: boolean; next: number | null }) => {
      await apiSend(FOLLOW_MEDIA_HIDE_URL, { item: id, media: index, hidden });
      await queryClient.invalidateQueries({ queryKey: key, exact: true });
    },
    onSuccess: (_result, { hidden, next }) => {
      const data = queryClient.getQueryData<FollowDetailData>(key);
      if (data) replaceFollowItem(data.item);
      onMedia(next);
      setFailure('');
      actions.toast(hidden ? '已隐藏这张图' : '已恢复显示');
    },
    onError: failed,
    onSettled: (_result, _error, { index, hidden }) => mark(`${hidden ? 'hide' : 'restore'}:${index}`, false),
  });
  return {
    busy, failure,
    save: () => { mark('save', true); saveMutation.mutate() },
    status: (to: string) => { mark(to, true); statusMutation.mutate({ to, was: item.status }) },
    hide: (index: number) => {
      const next = (item.media_items || []).find((media) => media.index !== index && media.media_kind === 'image');
      mark(`hide:${index}`, true);
      mediaMutation.mutate({ index, hidden: true, next: next ? next.index : null });
    },
    restore: (index: number) => { mark(`restore:${index}`, true); mediaMutation.mutate({ index, hidden: false, next: index }) },
  };
}
