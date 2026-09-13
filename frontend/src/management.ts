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

/** 首屏复用读数卡、扫描、链接管理与资源同步的内容容器。 */
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
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="board-link-button" href="/scraping"><span>来源和凭证</span><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-arrow-up"></use></svg></a><div class="splitbutton board-button-group primary"><button type="button" class="splitmain geist-button primary" disabled><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-database"></use></svg>扫描并补全资料</button><button type="button" class="splittoggle geist-button primary" disabled aria-label="更多扫描与采集方式"><svg aria-hidden="true"><use href="#i-chevron-down"></use></svg></button></div></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${bar}</strong><p class="cleanupmeta">${bar}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats">${['链接总数','官网/事务所','社交账号','作品资料站','资料出处'].map(title=>`<div><span>${title}</span><b>${bar}</b></div>`).join('')}</div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查死链</button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>${bar}</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查文件</button></div>
      </div></section></div>`;
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
