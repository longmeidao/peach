import { MEDIA_SOURCE_ICONS, noteHtml, selectOptionIconHtml } from '@peach/legacy/ui';

export interface ResourceSource {
  location: string; online: boolean; checked: number; total: number; missing: number; unreadable?: number;
}
export interface ResourceScan {
  sources?: ResourceSource[]; missing?: number; cache?: {files: number; bytes: number}; scan_id?: string;
}
const count = (value = 0) => Number(value).toLocaleString();
const labels: Record<string, string> = {local: '本地磁盘', '115': '115', pikpak: 'PikPak'};
/* 来源角标问的是「这是哪个网盘」，答案只有一份：品牌取 MEDIA_SOURCE_ICONS 的官方站标，
   与配置页、媒体库切换器同一取图入口；认不出的来源退回 database 字形。 */
const sourceMark = (location: string) => selectOptionIconHtml(MEDIA_SOURCE_ICONS[location] ?? 'database');
/* 结果照 Board 的 stat cards 排：和数据管理顶上一排读数同一副卡片，五个读数一行。 */
const statCard = (head: string, value: string, detail: string) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${head}</span>
    <strong>${value}</strong>
    <span class="cleanupmeta">${detail}</span></article>`;
export function resourceScanHtml(scan: ResourceScan, formatSize: (bytes: number) => string): string {
  const cache = scan.cache || {files: 0, bytes: 0};
  const changes = Boolean(scan.missing || cache.files);
  const sources = (scan.sources || []).map(source => statCard(
    `<span class="board-stat-tile resourcestat-tile">${sourceMark(source.location)}</span>${labels[source.location] || '媒体来源'}`
      + `<span class="resourcestat-state ${source.online ? 'online' : 'offline'}">${source.online ? '可访问' : '离线，已跳过'}</span>`,
    source.online ? `${count(source.missing)} 项` : '—',
    [source.online ? `找不到文件 · 已检查 ${count(source.checked)} 项` : `馆藏中有 ${count(source.total)} 项`,
      source.unreadable ? `${count(source.unreadable)} 项读取失败，已跳过` : ''].filter(Boolean).join(' · ')));
  return `<div class="cleanupstats resourcestats">${sources.join('')}
    ${statCard('待移入回收站', `${count(scan.missing)} 项`, '')}
    ${statCard('可清理的缓存', `${count(cache.files)} 个`, cache.files ? formatSize(cache.bytes) : '')}</div>
    ${changes ? noteHtml(`将把找不到文件的 ${count(scan.missing)} 项馆藏记录移入回收站，并清理 ${count(cache.files)} 个闲置缓存。`, {label: '清理内容'}) : ''}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${changes ? '<button class="geist-button primary" type="button" id="resourceApply">清理失效记录与缓存</button>' : '<p class="resourcesyncok">已检查可访问的来源，没有待清理的记录或缓存。</p>'}</div>`;
}
