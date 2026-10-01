/* 关注页卡片、两排与详情共用的署名、头像、来源图标和标题前后那几处字样。
 *
 * 都是拼好的 HTML 串，卡片与详情用 `dangerouslySetInnerHTML` 摆进去。图取不到时的回落由壳的
 * `wireImageFallbacks()` 委托监听按 `data-drop` 系列属性接手（`web/js/image-fallback.js`），
 * 这里只写属性。创作者名、首字母与头像的取舍和关注管理页是同一份（`follow-manage.ts`）。 */
import { api, esc } from '@peach/legacy/core';

import {
  authorAvatar, authorInitial, authorName, sourceIconUrl, type AliasGroup,
} from '../follow-manage/follow-manage';
import { localTime } from '../time';
import type { FollowContext, FollowGroup, FollowIdentity, FollowItem, FollowSource } from './follow-feed';

const text = (value: unknown): string => (typeof value === 'string' ? value : '');
const aliasesOf = (context: FollowContext) => context.aliases as readonly AliasGroup[];

/** 有站点图标的来源出一枚 `<img>`，没登记的站是空串。图标独自代表站名时传 `label`，alt 与
 *  title 写站名；外层已经带名字的传空，图只作装饰。取不到时撤掉，退回外层的文字。 */
export function sourceIcon(provider: string, label = ''): string {
  const url = sourceIconUrl(provider);
  return url
    ? `<img class="ficon" src="${url}" alt="${esc(label)}"${label ? ` title="${esc(label)}"` : ''} loading="lazy" data-drop="self">`
    : '';
}

/** 这一版列表里一位创作者的名字（别名合并后的统称优先）。 */
export const followAuthorName = (sources: readonly FollowSource[], context: FollowContext): string =>
  authorName(sources, aliasesOf(context));

/** 创作者圆框里那段：官方头像优先，归档站回退，都取不到时换成首字母。 */
export function authorAvatarHtml(sources: readonly FollowSource[], name: string): string {
  const { src, fallback } = authorAvatar(sources);
  const initial = authorInitial(name);
  if (!src) return `<span class="favatar none" title="没有可用头像">${esc(initial)}</span>`;
  const fallbacks = fallback ? ` data-fallbacks="${esc(fallback)}"` : '';
  return `<img class="favatar" src="${esc(src)}" alt="" loading="lazy" referrerpolicy="no-referrer" `
    + `data-drop="initial"${fallbacks} data-initial="${esc(initial)}" data-drop-class="favatar none">`;
}

/** 卡片与详情的署名。booru 帖子由服务端认出真正的发布者时（`item.credit`），名字和头像都换成
 *  发布者：也关注了这位就用那位的来源，否则只出首字母，不借被关注者的头像；被关注者退成一行
 *  「署名含」，说明这条为什么出现在这里。认不出的照常署被关注者。 */
export function followIdentity(item: FollowItem, authorSources: readonly FollowSource[],
  context: FollowContext): FollowIdentity {
  const aliases = aliasesOf(context);
  const credit = item.credit as { poster?: string; credited?: string } | undefined;
  const poster = credit?.poster;
  if (!poster) {
    const name = authorName(authorSources, aliases);
    return { author: name || text(item.author) || text(item.source_label) || '创作者未取得',
      avatar: authorAvatarHtml(authorSources, name), credited: '' };
  }
  const key = (value: unknown) => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const own = context.sources.find((row) => key(row.ref) === key(poster));
  const group = own?.author_key ? context.sources.filter((row) => row.author_key === own.author_key) : own ? [own] : [];
  const author = (group.length && authorName(group, aliases)) || poster;
  return { author, avatar: authorAvatarHtml(group, author), credited: credit.credited || '' };
}

/** 说「这一条是哪个版本」的字样，排在标题前面，与主页标题里的版次字样同一个控件。WIP 说的是
 *  这一条，不是这一组：同组还有一条 `[WIP]` 时说成「含 WIP」。声音版本说的是卡面这一条：
 *  配音版着色、无声版弱化加虚线框。 */
export function followTitleMarks(group: FollowGroup, shown: FollowItem = group.primary): string {
  const marks: string[] = [];
  if (group.primary.variant_kind === 'wip') marks.push('<small class="javedition followmark wip">WIP</small>');
  else if (group.has_wip) marks.push('<small class="javedition followmark wip partial">含 WIP</small>');
  const version = text(group.primary.version);
  if (version) marks.push(`<small class="javedition followmark ver">${esc(version)}</small>`);
  const audio = text(shown.audio);
  const label = audio === 'voiced' ? '配音版' : audio === 'silent' ? '无声版' : '';
  if (label) marks.push(`<small class="javedition followmark ${audio}">${label}</small>`);
  return marks.join('');
}

/** 另见的站用站点图标列出，站名落在图标的 alt 与徽章的 title 上；没登记图标的站写站名。
 *  「另见」相对卡面这一条（`shown`）说：卡面换成组里别的站那条时，主条目的站才是另见。 */
export function followBadges(group: FollowGroup, shown: FollowItem = group.primary): string {
  const sites = new Map([group.primary, ...group.variants, ...group.duplicates]
    .filter((member) => member.provider !== shown.provider)
    .map((member) => [member.provider, member.provider_label || member.provider] as const));
  if (!sites.size) return '';
  const marks = [...sites].map(([provider, label]) => sourceIcon(provider, label) || `<span>${esc(label)}</span>`).join('');
  return `<span class="fbadge dup" title="另见 ${esc([...sites.values()].join('、'))}">另见 ${marks}</span>`;
}

/** 「媒体未取得」那一句，没有就是空串。 */
export function followMediaIssue(item: FollowItem, context: FollowContext): string {
  const error = text(item.media_error);
  if (error) return `媒体未取得：${error}`;
  if (item.media_needs_credential && !context.credentials.has(item.provider)) {
    return item.playable ? '部分媒体未取得：需要 F95 登录会话解析' : '媒体未取得：需要 F95 登录会话解析';
  }
  return '';
}

/** 发布时间，按看的人所在时区显示；来源没给就明说。 */
export const followWhen = (item: FollowItem): string =>
  (item.published_at ? localTime(item.published_at) : '时间未取得');

/* 这次会话里已经回写过的图，`条目:媒体序号`。回写只补空缺，服务端本来就会忽略已有尺寸的
   条目，但每次重渲染都把同一批再发一遍是白跑。攒 800ms 一批、一批至多 200 条。 */
interface DimsEntry { item: number; width: number; height: number; media?: number }
const reported = new Set<string>();
let queue: DimsEntry[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;

function flushDims() {
  timer = null;
  if (!queue.length) return;
  const entries = queue.splice(0, 200);
  /* 静默：这是顺手学习，不是用户的动作；只读端 409 和网络抖动都不该弹提示。 */
  (api('/api/follow/image-dims', { method: 'POST', body: JSON.stringify({ entries }) }) as Promise<unknown>)
    .catch(() => {});
  if (queue.length) timer = setTimeout(flushDims, 800);
}

/** 图片视图里没有尺寸的卡面图加载完，把固有尺寸回写给它的主人（`/api/follow/image-dims`）。 */
export function learnFollowDims(item: number, media: number | null, width: number, height: number): void {
  const key = `${item}:${media ?? ''}`;
  if (reported.has(key)) return;
  reported.add(key);
  queue.push(media === null ? { item, width, height } : { item, width, height, media });
  if (!timer) timer = setTimeout(flushDims, 800);
}
