/* 卡片封面格里那张图。
 *
 * 图以 HTML 片段交给封面格（`[data-media-art]`），不做成 React 元素：取景整条链都在遗留壳
 * 里，并且原地改这张图。加载完成时 `coverAnchor` 按人脸与正封框给它加 `panel` 类和四个
 * 取景变量，`upgradeCover` 把派生档换成原件，换「JAV 默认封面」设置时 `syncJavImages` 在
 * 同一个 `<img>` 上换来源和类名。这些改动 React 看不见，片段不变它就不碰这张图。
 *
 * 类名 `poster cover whole|front` 是取景链的钩子，和详情页、样张集、新作卡用的是同一份
 * （`web/css/19-immersive.css`），封面那一段由壳的 `coverImage` 拼，这里只包一层 JAV 的换图
 * 属性。 */
import { esc } from '@peach/legacy/core';

import { javImageKind } from '../../jav-artwork';
import type { MediaCardHelpers, MediaItem } from './types';

/** 封面格的两种图：官方封套（取景链接管）或预览图。空串是这一条没有可用的图。 */
export type ArtworkKind = 'cover' | 'thumb' | '';

export interface Artwork {
  kind: ArtworkKind;
  html: string;
}

const NONE: Artwork = { kind: '', html: '' };

/** 番号作品的封面：按「JAV 默认封面」取官方封套或预览图，两种来源都挂在元素上，
 *  设置一换 `syncJavImages` 原地换图。取景数据跟着元素走，从预览图切回封面时还找得到框。 */
export function javArtwork(
  item: MediaItem, layout: 'big' | 'small', eager: boolean, javImage: string,
  coverHtml: MediaCardHelpers['coverHtml'],
): Artwork {
  const kind = javImageKind(item, javImage);
  if (!kind) return NONE;
  const cover = item.has_cover && item.code ? `/cover?code=${encodeURIComponent(item.code)}&thumb=1` : '';
  const thumb = item.has_thumb || item.has_local_poster ? `/poster?id=${item.id}&c=4` : '';
  const coverMarkup = coverHtml(item, layout, eager);
  const frame = (coverMarkup.match(/ data-(?:c[xy]|posterbox)="[^"]*"/g) || []).join('');
  const image = kind === 'cover'
    ? coverMarkup
    : `<img class="poster" src="${thumb}" alt="" loading="${eager ? 'eager' : 'lazy'}"${frame}>`;
  return {
    kind: kind === 'cover' ? 'cover' : 'thumb',
    html: image.replace('<img ', `<img data-jav-image="${item.id}" data-jav-cover="${esc(cover)}" data-jav-thumb="${esc(thumb)}" data-jav-image-layout="${layout}" `),
  };
}

/** 一张作品卡的封面。番号作品走上面那条；关注来源的条目用来源自己的缩略图；其余取本地
 *  预览格。`layout` 是这一屏的大图／小图，只施加给番号作品。 */
export function cardArtwork(
  item: MediaItem, layout: 'big' | 'small', eager: boolean, javImage: string,
  coverHtml: MediaCardHelpers['coverHtml'],
): Artwork {
  if (item.is_jav) return javArtwork(item, layout, eager, javImage, coverHtml);
  const loading = eager ? 'eager' : 'lazy';
  if (item.follow_thumb_url) {
    return {
      kind: 'thumb',
      html: `<img class="poster" src="${esc(item.follow_thumb_url)}" alt="" loading="${loading}" referrerpolicy="no-referrer">`,
    };
  }
  if (item.has_thumb || item.has_local_poster) {
    return { kind: 'thumb', html: `<img class="poster" src="/poster?id=${item.id}&c=4" alt="" loading="${loading}">` };
  }
  return NONE;
}
