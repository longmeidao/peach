import { noteHtml } from '@peach/legacy/ui';

export interface ResourceSource {
  location: string; online: boolean; checked: number; total: number; missing: number; unreadable?: number;
}
export interface ResourceScan {
  sources?: ResourceSource[]; missing?: number; cache?: {files: number; bytes: number}; scan_id?: string;
}
const count = (value = 0) => Number(value).toLocaleString();
const labels: Record<string, string> = {local: '本地磁盘', '115': '115', pikpak: 'PikPak'};
export function resourceScanHtml(scan: ResourceScan, formatSize: (bytes: number) => string): string {
  const cache = scan.cache || {files: 0, bytes: 0};
  const changes = Boolean(scan.missing || cache.files);
  return `<div class="resourcepanel" data-geist-fieldset><div class="resourcesources">${(scan.sources || []).map(source => `<article>
    <div class="resourcesourcetitle"><b>${labels[source.location] || '媒体来源'}</b><span class="${source.online ? 'online' : 'offline'}">${source.online ? '可访问' : '离线，已跳过'}</span></div>
    <strong>${source.online ? `${count(source.missing)} 项` : '—'}</strong>
    <small>${source.online ? `找不到文件 · 已检查 ${count(source.checked)} 项` : `馆藏中有 ${count(source.total)} 项`}</small>
    ${source.unreadable ? `<small>${count(source.unreadable)} 项读取失败，已跳过</small>` : ''}</article>`).join('')}</div>
    <div class="resourcecache"><div><span>可清理的缓存</span><b>${count(cache.files)} 个</b><small>${formatSize(cache.bytes)}</small></div>
    <div><span>待移入回收站</span><b>${count(scan.missing)} 项</b></div></div>
    ${changes ? noteHtml(`将把找不到文件的 ${count(scan.missing)} 项馆藏记录移入回收站，并清理 ${count(cache.files)} 个闲置缓存。`, {label: '清理内容'}) : ''}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${changes ? '<button class="geist-button primary" type="button" id="resourceApply">清理失效记录与缓存</button>' : '<p class="resourcesyncok">已检查可访问的来源，没有待清理的记录或缓存。</p>'}</div></div>`;
}
