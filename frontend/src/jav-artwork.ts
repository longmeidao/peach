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
