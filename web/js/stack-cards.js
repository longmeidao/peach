/* 关注卡叠层的三件判断：封面角标数的是哪一组、悬浮翻哪几张、正文还要不要再报一次条数。

   叠层纸边说的是「这张卡不止一条」，翻动说的是「这几条长得不一样」，两件事分开判。
   同一段画面的几份翻过去还是那张图，看着像卡住了：alt 与 WIP 是某一段的另一版
   （`follow_variants` 按标题标记判定，服务端随每个成员下发 `variant_kind`），只留纸边、
   不进翻动。组里独立的几段（booru 连发、同一包短片、跨站的同作品帖）是 `main`，照翻。
   一条帖子自带的多张媒体没有这个字段，每一张本来就是不同的。 */

const isImage = (entry) => entry?.media_kind === 'image';
const isPiece = (entry) => !entry?.variant_kind || entry.variant_kind === 'main';

export function followStack({
  cover = '', embedded = [], groupedVideos = [], videos = [],
  imageView = false, openable = 0, limit = 9,
} = {}) {
  /* 帖子自带的媒体优先：角标数的就是点开后那一串。没有才数组里的视频成员。 */
  const own = embedded.length > 1 ? embedded : groupedVideos.length > 1 ? groupedVideos : null;
  const source = own || videos;
  const isMix = source.length > 1;
  const mixKind = source.length && source.every(isImage) ? '图片'
    : source.some(isImage) ? '媒体' : '视频';
  /* 图片视图里只翻图片：这一叠说的就是这几张图。第一张是静止封面本身，
     否则一翻就露出取景差别。 */
  const pieces = source.filter((entry) => (!imageView || isImage(entry)) && isPiece(entry));
  const faces = pieces.length > 1
    ? [...new Set([cover, ...pieces.map((entry) => entry.thumb_url)].filter(Boolean))].slice(0, limit)
    : [];
  /* 封面角标数的是组里的视频成员时，它和「N 个版本」数的是同一组，正文不再说第二遍。
     角标数的是一条帖子里的媒体时，组里有几条帖子是另一件事，仍然要说。 */
  const showCount = openable > 1 && !(isMix && !own);
  return { isMix, mixCount: isMix ? source.length : 0, mixKind, faces, showCount };
}
