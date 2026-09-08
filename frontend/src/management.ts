import { wireCollapse } from '@peach/legacy/ui';

/** 管理页按已配置的来源显示能力；离线来源仍然属于已配置来源。 */
export interface MediaSource { location: string; roots?: unknown[]; online?: boolean }

export function cloudLocations(sources: readonly MediaSource[]): string[] {
  return sources.filter(source => ['115', 'pikpak'].includes(source.location)
    && (source.roots === undefined || source.roots.length > 0)).map(source => source.location);
}

export function cloudPreferenceLocations(files: readonly { location: string }[], configured: readonly string[]): string[] {
  return configured.filter(location => files.some(file => file.location === location));
}

/** 首屏复用最终排版：顶上五张读数卡的图标与标题、下面两张卡的标题、说明和按钮都不必等接口。 */
export function cleanupSkeletonHtml(): string {
  const stats = [['人工复核', 'square-check-big'], ['高清版', 'sparkles'], ['重复文件', 'file-stack'], ['垃圾文件', 'file-archive'], ['回收站', 'trash']];
  const bar = '<span class="skeleton cleanup-count-skeleton" aria-hidden="true"></span>';
  return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${stats.map(([title, glyph]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${glyph}"></use></svg></span>${title}</span>
        <strong>${bar}</strong><span class="cleanupmeta">${bar}</span></button>`).join('')}</div>
    <div class="cleanupgrid">
      <section class="cleanupfieldset board-processing-skeleton" data-geist-fieldset aria-labelledby="cleanup-loading-scan">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-scan">扫描与采集</h3>
          <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="geist-button" href="/scraping">采集来源</a><button type="button" class="geist-button primary" disabled>扫描并补全资料</button></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${bar}</strong><p class="cleanupmeta">${bar}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div></div>`;
}

/** 使用口味页现有读取／导入按钮，展开指南本身不发起读取。 */
export function tasteHistoryGuideHtml(onboarding: boolean, completed = false, skipped = false): string {
  if (completed || skipped) return '';
  const external = '<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link"></use></svg>';
  return `<details class="taste-history-guide"${onboarding ? ' open' : ''}>
    <summary><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a class="externallink" href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${external}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a class="externallink" href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${external}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      <button type="button" class="geist-button taste-guide-skip">跳过</button>
    </div></details>`;
}

/** 跳过是当前浏览器的持久偏好；折叠只改变 details 的展开状态。 */
export const TASTE_GUIDE_KEY = 'peach-taste-guide-dismissed';
export function wireTasteHistoryGuide(root: ParentNode, storage: Storage): void {
  wireCollapse(root, '.taste-history-guide', 'taste-guide-collapse');
  const guide = root.querySelector<HTMLDetailsElement>('.taste-history-guide');
  guide?.querySelector<HTMLButtonElement>('.taste-guide-skip')?.addEventListener('click', () => {
    storage.setItem(TASTE_GUIDE_KEY, '1');
    guide.remove();
  });
}
