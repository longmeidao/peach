/* 圆头像的人脸取景：按源图里那张脸有多少像素，算出能放大多少倍。

   只挪不放大的时候，「脸太小」这件事是没法解决的：`object-fit:cover` 的缩放由框和
   图的比例定死，脸在图里占多少，在框里就占多少。实测 539 张实体图，脸框宽占框宽的
   中位数是 44%——四分之三的头像本来就是特写，放大只会把头顶和下巴切出去；真正偏小的
   只有 29 张，它们几乎都是全身站姿照，脸落在画面上半截的一小块里。

   所以放大倍数不能写死，也不能只由服务端算一份：约束是「源图里那张脸有多少像素」比
   「这个框要显示多少像素」，而后者取决于框的实际尺寸和设备像素比。同一张 640×960、
   脸只有 67 px 宽的图（`performer-8711`），在资料页 160 px 圆框上放大 2 倍就到了
   源图 1:1，再放大就是上采样；在顶栏 64 px 圆框上放到 3 倍仍有余量。判据一样，
   结论差一倍多，只有在页面这一侧、拿到框的真实尺寸时才算得出来。

   夹持顺序固定：先算「要多大才看得清」，再用「放到多大就开始虚」压住，最后卡构图上限。
   `zoom` 为 1 时只挪不放大，已经够大的那 395 张走的就是这条路。 */

/** 脸框宽占框短边这个比例就算看得清是谁，不再往上放。
 *
 *  检出给的框只覆盖眼鼻嘴，不含头发和下巴外沿；32% 时整颗头大约占七成，构图还松。
 *  往上调会让本来就偏紧的特写被这一档"救"进放大，那些图不需要。 */
export const FACE_TARGET = 0.32;

/** 放大上限。源图再清楚也不越过这条线：脸框之外还有头顶、下巴和肩，
 *  按脸框放到满框等于把这些全裁掉，剩下一张认不出是谁的五官特写。 */
export const MAX_ZOOM = 3;

/** 人脸数据齐不齐。缺一样就没法算，调用方只挪不放大。
 *
 *  `faceW` 是脸框宽的**源图像素**，不是归一化值：无损上限问的就是「有多少像素可用」，
 *  归一化值除得出比例却除不出像素，换算要在拿得到原图尺寸的那一侧做。 */
export function hasFaceBox(face) {
  if (!face) return false;
  // 脸心可以是 0：脸贴着左边缘或顶边的图确实存在，那不是缺数据。
  return Number.isFinite(face.cx) && Number.isFinite(face.cy)
    && face.faceW > 0 && face.imgW > 0 && face.imgH > 0;
}

/** 放大多少倍。`frame` 是框的 CSS 像素尺寸，`dpr` 是设备像素比。
 *
 *  三个上限都必须在：只有目标会把小脸图放到糊，只有无损上限会把已经够大的图
 *  也推到 3 倍，只有构图上限则对着一张 4096 px 高的图能放到二十几倍。 */
export function faceZoom(face, frame, dpr = 1,
                         target = FACE_TARGET, maxZoom = MAX_ZOOM) {
  if (!hasFaceBox(face) || !(frame && frame.w > 0 && frame.h > 0)) return 1;
  const ratio = dpr > 0 ? dpr : 1;
  // cover 的基础缩放：图缩到刚好盖住框，紧的那一边说话。
  const base = Math.max(frame.w / face.imgW, frame.h / face.imgH);
  const shown = face.faceW * base;
  if (!(shown > 0)) return 1;
  const wanted = target * Math.min(frame.w, frame.h) / shown;
  // 脸的源像素 ÷ 现在这个框要的设备像素。等于 1 就是已经 1:1，再放大就是上采样。
  const lossless = face.faceW / (shown * ratio);
  return Math.max(1, Math.min(wanted, lossless, maxZoom));
}

/** 取景结果，四个值都是相对框的百分比。
 *
 *  给百分比而不是像素：索引页大图版式的框宽跟着列宽走，视口一变就得跟着变，
 *  百分比让 CSS 自己跟随。`zoom` 按加载时的框尺寸算一次就够——框变大只会让
 *  放大倍数偏保守，不会突然越过无损上限。 */
export function faceFrame(face, frame, dpr = 1,
                          target = FACE_TARGET, maxZoom = MAX_ZOOM) {
  const zoom = faceZoom(face, frame, dpr, target, maxZoom);
  if (zoom <= 1 || !hasFaceBox(face)) return null;
  const scale = Math.max(frame.w / face.imgW, frame.h / face.imgH) * zoom;
  const width = face.imgW * scale;
  const height = face.imgH * scale;
  // 脸心对准框心，再夹回来不许露白。`zoom >= 1` 且底子是 cover，所以图一定比框大，
  // 这个区间不会是空的。
  const left = Math.min(0, Math.max(frame.w - width, frame.w / 2 - face.cx * width));
  const top = Math.min(0, Math.max(frame.h - height, frame.h / 2 - face.cy * height));
  const pct = (value, span) => Math.round(value / span * 1e4) / 100;
  return {
    zoom: Math.round(zoom * 1000) / 1000,
    width: pct(width, frame.w), height: pct(height, frame.h),
    left: pct(left, frame.w), top: pct(top, frame.h),
  };
}
