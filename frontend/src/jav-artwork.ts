export type JavImagePreference = 'cover' | 'thumbnail';
export type JavLayout = 'big' | 'small';

export function normalizeJavLayout(value: unknown): JavLayout {
  return ['small', 'sleeve', 'preview'].includes(String(value)) ? 'small' : 'big';
}

export function normalizeJavPreferences(settings: { javLayout?: unknown; javImage?: unknown }) {
  return {
    javLayout: normalizeJavLayout(settings.javLayout),
    javImage: normalizeJavImage(settings.javLayout === 'preview' ? 'thumbnail' : settings.javImage),
  };
}

export function normalizeJavImage(value: unknown): JavImagePreference {
  return value === 'thumbnail' ? 'thumbnail' : 'cover';
}

export function javImageKind(item: { is_jav?: boolean; code?: string; has_cover?: boolean; has_thumb?: boolean }, preference: unknown): 'cover' | 'thumbnail' | '' {
  const cover = Boolean(item.is_jav && item.code && item.has_cover);
  if (cover && (normalizeJavImage(preference) === 'cover' || !item.has_thumb)) return 'cover';
  return item.has_thumb ? 'thumbnail' : '';
}

/** 接口 `poster_box` 的形状：`x0/y0/x1/y1` 是源图像素坐标，`px` 是源图尺寸，
 *  `method` 记着这个框是沿折痕（`fold`）还是按右半居中（`ratio`）定出来的。
 *  不该裁、没算过、算法版本落后的封面拿到的是 null。 */
export interface PosterBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  method?: string;
  px: number[];
}

/** 正封在卡片里的摆法：`clip` 是从图片左缘切掉的比例（折痕以左是封底），`left` 是
 *  图片左缘相对卡片宽度的偏移，两个都是百分数。没有框时返回 null，调用方原样退回
 *  CSS 里那份贴右缘的回退。
 *
 *  图片按卡片高度铺满、宽度随原始比例走，于是渲染宽度是卡片宽的
 *  `源图宽 / 源图高 / 容器比例` 倍——页面这一侧只需要知道容器的比例，不必去量它。
 *  正封占其中 `1 − 折痕比例`：装得下就居中，两侧各留一条交给模糊背景；装不下只能
 *  贴右缘从左边切，因为标题、女优名和角标都压在正封右侧。
 *
 *  纵向一个像素都不裁：图片高度正好等于卡片高度，所以这一档没有纵向锚点可写。 */
export function panelFrame(box: Partial<PosterBox> | null | undefined, ratio: number): { clip: number; left: number } | null {
  const width = Number(box?.px?.[0]);
  const height = Number(box?.px?.[1]);
  const x0 = Number(box?.x0);
  if (!(width > 0 && height > 0 && ratio > 0) || !Number.isFinite(x0)) return null;
  // 夹回 0–1：框落在图片外面是数据坏了，按整幅可见处理比按负宽度算下去安全。
  const fold = Math.min(1, Math.max(0, x0 / width));
  const wide = width / height / ratio;
  const visible = (1 - fold) * wide;
  if (!(visible > 0)) return null;
  const left = visible <= 1 ? (1 - visible) / 2 - fold * wide : 1 - wide;
  const percent = (value: number) => Math.round(value * 10000) / 100;
  return { clip: percent(fold), left: percent(left) };
}

/** 原地换图，保留列表顺序、滚动位置和正在播放的媒体。 */
export function syncJavImages(root: ParentNode, preference: unknown): void {
  root.querySelectorAll<HTMLImageElement>('img[data-jav-image]').forEach(img => {
    const cover = img.dataset.javCover || '';
    const thumb = img.dataset.javThumb || '';
    const useCover = Boolean(cover && (normalizeJavImage(preference) === 'cover' || !thumb));
    const src = useCover ? cover : thumb;
    img.classList.toggle('cover', useCover);
    img.classList.toggle('whole', useCover && img.dataset.javImageLayout !== 'big');
    img.classList.toggle('front', useCover && img.dataset.javImageLayout === 'big');
    /* 取景是按上一张图算的，换图之后一律作废，由 `coverAnchor` 在新图加载完重算。
       模糊背景挂在卡片上而不是图片上，`removeAttribute('style')` 够不着它。 */
    img.classList.remove('panel');
    img.removeAttribute('style');
    (img.closest('.pic') as HTMLElement | null)?.style.removeProperty('--cover-blur');
    if (src && img.getAttribute('src') !== src) img.src = src;
  });
}
