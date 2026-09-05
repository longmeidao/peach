/** 侧栏筛选属于当前地址对应的内容集合。导航由遗留外壳同步绘制。 */
export function sidebarHasCatalogContent(path: string): boolean {
  return ['/', '/unseen', '/watch-later', '/flagged', '/trash', '/junk-files'].includes(path)
    || /^\/(item|mix|parts|editions)\//.test(path)
    || /^\/playlists\/\d+\/\d+$/.test(path)
    || /^\/(performers|studios|creators|series|agencies)\/.+/.test(path);
}

export function syncSidebarSurface(drawer: HTMLElement, key: string): boolean {
  if (drawer.dataset.surface === key && drawer.querySelector('.dnav')) return false;
  drawer.dataset.surface = key;
  drawer.replaceChildren();
  return true;
}

/** 一条内容的同名标签只计一次。调用者传入当前实际展示的媒体。 */
export function sidebarTagCounts(items: { tags?: string[] }[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const item of items) {
    for (const tag of new Set(item.tags || [])) counts.set(tag, (counts.get(tag) || 0) + 1);
  }
  return [...counts].sort((a, b) => b[1] - a[1]).slice(0, 30);
}
