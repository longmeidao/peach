/** 实体资料的等待态使用资料头、标签条和对应正文布局。 */
export function entitySkeletonHtml(kind: string, body: string) {
  const square = kind === 'studio' || kind === 'agency';
  return `<section data-skeleton="entity/${kind}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <div class="entityhero"><div class="entityportrait ${square ? 'square ' : ''}skeleton"></div>
      <div class="entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div>
    <section class="entitytagbar"><div class="entitytags"><span class="skeleton entitymediaskeleton"></span><span class="skeleton entitymediaskeleton"></span></div></section>
    <div class="entitysection">${body}</div></div></section>`;
}
