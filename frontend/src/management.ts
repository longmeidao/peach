/** 管理页按已配置的来源显示能力；离线来源仍然属于已配置来源。 */
export interface MediaSource { location: string; roots?: unknown[]; online?: boolean }

export function cloudLocations(sources: readonly MediaSource[]): string[] {
  return sources.filter(source => ['115', 'pikpak'].includes(source.location)
    && (source.roots === undefined || source.roots.length > 0)).map(source => source.location);
}

export function cloudPreferenceLocations(files: readonly { location: string }[], configured: readonly string[]): string[] {
  return configured.filter(location => files.some(file => file.location === location));
}

/** 首屏复用读数卡、扫描、媒体修复、链接管理与资源同步的内容容器。 */
export function cleanupSkeletonHtml(): string {
  const stats = [['人工复核', 'square-check-big'], ['高清版', 'sparkles'], ['重复文件', 'file-stack'], ['垃圾文件', 'file-archive'], ['回收站', 'trash']];
  const bar = '<span class="skeleton cleanup-count-skeleton" aria-hidden="true"></span>';
  return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${stats.map(([title, glyph]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${glyph}"></use></svg></span>${title}</span>
        <strong>${bar}</strong><span class="cleanupmeta">${bar}</span></button>`).join('')}</div>
    <div class="cleanupgrid">
      <section class="cleanupfieldset cleanupprocessing board-processing-skeleton" data-geist-fieldset data-cleanup-task aria-labelledby="cleanup-loading-scan">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-scan">扫描与采集</h3>
          <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="board-link-button" href="/scraping"><span>来源和凭证</span><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-arrow-up"></use></svg></a><div class="splitbutton board-button-group primary"><button type="button" class="splitmain geist-button primary" disabled><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-database"></use></svg>扫描并补全资料</button><button type="button" class="splittoggle geist-button primary" disabled aria-label="更多扫描与采集方式"><svg aria-hidden="true"><use href="#i-chevron-down"></use></svg></button></div></footer>
      </section>
      <section class="cleanupfieldset cleanupprocessing board-processing-skeleton" data-geist-fieldset data-cleanup-task aria-labelledby="cleanup-loading-repair">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-repair">媒体修复</h3>
          <p>修缺时间戳表（播放卡顿）和缺索引（打不开）的 MP4。常看的片子先修。</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled>开始修复</button></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset data-cleanup-task aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${bar}</strong><p class="cleanupmeta">${bar}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats">${['链接总数','官网/事务所','社交账号','作品资料站','资料出处'].map(title=>`<div><span>${title}</span><b>${bar}</b></div>`).join('')}</div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查死链</button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset data-cleanup-task>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>${bar}</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查文件</button></div>
      </div></section></div>`;
}
