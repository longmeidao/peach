/** 管理页按已配置的来源显示能力；离线来源仍然属于已配置来源。 */
export interface MediaSource { location: string; roots?: unknown[]; online?: boolean }

export function cloudLocations(sources: readonly MediaSource[]): string[] {
  return sources.filter(source => ['115', 'pikpak'].includes(source.location)
    && (source.roots === undefined || source.roots.length > 0)).map(source => source.location);
}

export function cloudPreferenceLocations(files: readonly { location: string }[], configured: readonly string[]): string[] {
  return configured.filter(location => files.some(file => file.location === location));
}

/** 首屏复用最终 Fieldset 的排版，静态标题、说明和按钮无需等待接口。 */
export function cleanupSkeletonHtml(): string {
  const cards = [
    ['采集来源', '设置采集来源', '下载高清封面，设置代理和 Cookie。'],
    ['垃圾文件', '查看垃圾文件', ''], ['重复文件', '查看重复文件', ''],
    ['空文件夹', '删除空文件夹', ''], ['人工复核', '查看候选', ''],
    ['回收站', '查看回收站', ''], ['高清版', '查看高清版', ''],
  ];
  return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupgrid">${cards.map(([title, action, description], index) => `
      <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanup-loading-${index}">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-${index}">${title}</h3>
          ${description ? `<p>${description}</p>` : '<strong><span class="skeleton cleanup-count-skeleton" aria-hidden="true"></span></strong>'}
          ${index === 3 ? '<p class="cleanupmeta"><span class="skeleton cleanup-count-skeleton" aria-hidden="true"></span></p>' : ''}</div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button"${index === 3 ? ' class="danger"' : ''} disabled>${index === 3 ? '<svg aria-hidden="true"><use href="#i-trash"></use></svg><span>' + action + '</span>' : action}</button></footer>
      </section>`).join('')}</div></div>`;
}

/** 使用口味页现有读取／导入按钮，展开指南本身不发起读取。 */
export function tasteHistoryGuideHtml(onboarding: boolean): string {
  const external = '<svg aria-hidden="true"><use href="#i-external-link"></use></svg>';
  return `<details class="taste-history-guide"${onboarding ? ' open' : ''}>
    <summary>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${external}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${external}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      ${onboarding ? '<a class="taste-guide-skip" href="/">跳过，浏览馆藏</a>' : ''}
    </div></details>`;
}
