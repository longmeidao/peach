/** 实体资料的等待态使用资料头、标签条和对应正文布局。
 *
 * 筛选条和作品抬头在这一页是同一块浮层的上下两格，等待态也得是一块：这两条各自都
 * 带着玻璃材质和 22px 圆角，不套进外框就被当成两块独立浮层画出来，中间一道缝、四个
 * 角各一道弧，等内容回来又并成一块。`mountFilterFrame` 是运行时才建外框的，骨架进不了
 * 那条路径，所以自己把外框和两个槽位的标记写全。
 */
export function entitySkeletonHtml(kind: string, head: string, body: string) {
  const square = kind === 'studio' || kind === 'agency';
  return `<section data-skeleton="entity/${kind}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <section class="entityhero"><div class="entityprofile"><div class="entityportrait ${square ? 'square ' : ''}skeleton"></div>
      <div class="entityidentity entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div></section>
    <div class="board-filter-frame" data-filter-frame>
      <section class="entitytagbar" data-filter-row="top"><div class="filterscroll" data-skeleton-tier="pill"></div></section>
      ${head}</div>
    <div class="entitysection">${body}</div></div></section>`;
}
