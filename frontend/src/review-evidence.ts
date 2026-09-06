import { esc } from '@peach/legacy/core';

interface IdentityEvidence {
  creator?: string; babepedia_name?: string; preview_url?: string; profile_url?: string;
  videos?: string | number; video_count?: number;
  preview_assets?: { id: number; name: string; has_preview?: boolean }[];
}
const webUrl = (value = '') => /^https?:\/\//i.test(value) ? value : '';

export function reviewImageHtml(url = '') {
  const image = webUrl(url) || (url.startsWith('/') && !url.startsWith('//') ? url : '');
  return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${image ? ' hidden' : ''}>未取得来源图片</span>${image ? `<img src="${esc(image)}" alt="来源候选图片" loading="lazy">` : ''}</div>`;
}

export function identityEvidenceHtml(row: IdentityEvidence) {
  const profile = webUrl(row.profile_url), samples = (row.preview_assets || []).slice(0, 6);
  const count = Math.max(0, Number(row.video_count || row.videos || 0));
  return `<section class="reviewidentityevidence"><h5>候选身份：${esc(row.babepedia_name || '未标注')}</h5>
    <div class="reviewevidenceactions">${profile ? `<a class="geist-button externallink" href="${esc(profile)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ''}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${esc(row.creator || '')}">查看全部 ${count.toLocaleString()} 部作品</button></div>
    ${reviewImageHtml(row.preview_url)}
    <p>通过后记录身份判断。</p>
    ${samples.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${samples.map(asset => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${asset.id}"><span data-middle-truncate title="${esc(asset.name)}">${esc(asset.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${asset.id}" aria-label="打开 ${esc(asset.name)} 的文件位置">文件位置</button>
    </div>`).join('')}</div>` : '<p>暂无本地作品样本，打开全部作品核对。</p>'}</section>`;
}

export function wireReviewPictures(root: ParentNode) {
  for (const image of root.querySelectorAll<HTMLImageElement>('[data-review-picture] img')) {
    const failed = () => { image.hidden = true; const placeholder = image.parentElement?.querySelector<HTMLElement>('.reviewimageempty'); if (placeholder) placeholder.hidden = false; };
    image.addEventListener('error', failed);
    if (image.complete && !image.naturalWidth) failed();
  }
}
