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

/** 正封那一块的横向 `object-position` 百分比；没有框或横向本来就不裁时返回 null，
 *  调用方原样退回 CSS 里那份回退值。
 *
 *  框是源图像素，`object-position` 要的是「图片上这个点对齐可见窗口的同一个百分比
 *  位置」，两者之间隔着一次 `object-fit:cover` 的缩放，所以不能拿容器宽直接当分母。
 *  cover 先把图缩到盖住容器，缩放由紧的那一边决定；可见窗口换算回源图像素是
 *  `容器宽 / max(容器宽/源图宽, 容器高/源图高)`，化简掉容器的绝对尺寸之后只剩
 *  `min(源图宽, 源图高 × 容器宽高比)`——页面这一侧只需要知道容器的比例，不必去量它。
 *
 *  源图比容器更竖时缩放改由宽度决定，整幅宽度都可见：那一轴没有余量可推，
 *  百分比在那里是死值，分母也正好是 0，两件事是同一件事。 */
export function posterBoxAnchor(box: Partial<PosterBox> | null | undefined, ratio: number): number | null {
  const width = Number(box?.px?.[0]);
  const height = Number(box?.px?.[1]);
  const x0 = Number(box?.x0);
  if (!(width > 0 && height > 0 && ratio > 0) || !Number.isFinite(x0)) return null;
  const visible = Math.min(width, height * ratio);
  const room = width - visible;
  if (!(room > 0)) return null;
  // 夹回 0–100：框贴着源图右缘时窗口已经顶到边，再往外推只会把图片外面推进来。
  return Math.round(Math.min(100, Math.max(0, x0 / room * 100)) * 100) / 100;
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
    img.removeAttribute('style');
    if (src && img.getAttribute('src') !== src) img.src = src;
  });
}
