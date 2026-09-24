/* 关注卡叠层的两件判断：封面角标报什么、悬浮翻哪几张。

   哪几张是同一个画面由服务端判（`peach.follow_faces`，文件内容哈希，缩略图 dHash、8×8 色块加
   时长）：每个成员和媒体带 `face`，编号相同就是同一个画面；组上的 `stack` 给出去重后的媒体数
   `media`、合并了几份 `copies`、媒体类型 `kind` 和彼此不同的翻卡画面 `faces`。
   这里只决定怎么说、翻哪几张。

   角标只报一个数：这张卡合并了几个不同的媒体。同一个视频在两个站各传一份是一个媒体、
   两个来源；去重后只剩一个媒体时，报的就是来源数。量词随媒体类型走：视频论「个」，
   图片论「张」，与详情里「第 1 张，共 11 张」同一套；图和视频混在一起时说「个媒体」，
   不说「项」——「项」在关注页数的是更新条目，读起来像又在数帖子。 */

const UNITS = { video: '个视频', image: '张图片', mixed: '个媒体' };

export function followStack({ cover = '', coverFace = null, stack = null, imageView = false, limit = 9 } = {}) {
  const media = stack?.media || 0;
  const copies = stack?.copies || 0;
  const kind = stack?.kind || '';
  const label = media > 1 ? `${media} ${UNITS[kind] || UNITS.mixed}`
    : copies > 1 ? `${copies} 个来源` : '';
  /* 字形说的是点开以后看什么：视频起播是 play，图片是 pics，与全站的视频／图片同一对。
     图和视频混在一起时，点开落在哪一种由视图决定，字形跟着视图走。 */
  const glyph = kind === 'image' || (kind !== 'video' && imageView) ? 'pics' : 'play';
  /* 图片视图里只翻图片：这一叠说的就是这几张图。第一张是静止封面本身，否则一翻就露出
     取景差别；和封面同一个画面的不再翻。画面彼此相同的服务端已经并成一张。 */
  const seen = new Set([coverFace ?? cover]);
  const faces = cover ? [cover] : [];
  for (const face of stack?.faces || []) {
    if (imageView && face.media_kind !== 'image') continue;
    if (!face.thumb_url || face.thumb_url === cover || seen.has(face.face)) continue;
    seen.add(face.face);
    faces.push(face.thumb_url);
  }
  return { isMix: Boolean(label), label, glyph, faces: faces.length > 1 ? faces.slice(0, limit) : [] };
}
