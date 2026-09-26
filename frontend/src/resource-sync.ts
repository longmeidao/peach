import { MEDIA_SOURCE_ICONS, noteHtml, selectOptionIconHtml } from '@peach/legacy/ui';

export interface ResourceSource {
  location: string; online: boolean; total: number; missing: number; empty: number; unreadable: number;
}
export interface ResourceScan {
  sources?: ResourceSource[]; missing?: number; empty?: number; unreadable?: number;
  cache?: {files: number; bytes: number}; scan_id?: string;
}
const count = (value = 0) => Number(value).toLocaleString();
const labels: Record<string, string> = {local: '本地磁盘', '115': '115', pikpak: 'PikPak'};
/* 来源角标问的是「这是哪个网盘」，答案只有一份：品牌取 MEDIA_SOURCE_ICONS 的官方站标，
   与配置页、媒体库切换器同一取图入口；认不出的来源退回 database 字形。 */
const sourceMark = (location: string) => selectOptionIconHtml(MEDIA_SOURCE_ICONS[location] ?? 'database');
/* 结果照 Board 的 stat cards 排：和数据管理顶上一排读数同一副卡片。来源一行、要清的三样
   一行，两行各自等分，来源几个都不折出半行。 */
const statCard = (head: string, value: string, detail: string) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${head}</span>
    <strong>${value}</strong>
    <span class="cleanupmeta">${detail}</span></article>`;
const sourceDetail = (source: ResourceSource) => source.online
  ? [`找不到文件 · 共 ${count(source.total)} 项`, source.empty ? `空文件夹 ${count(source.empty)} 个` : '',
    source.unreadable ? `${count(source.unreadable)} 个目录读取失败，已跳过` : ''].filter(Boolean).join(' · ')
  : `馆藏中有 ${count(source.total)} 项`;
export function resourceScanHtml(scan: ResourceScan, formatSize: (bytes: number) => string): string {
  const cache = scan.cache || {files: 0, bytes: 0};
  const changes = Boolean(scan.missing || scan.empty || cache.files);
  const sources = (scan.sources || []).map(source => statCard(
    `<span class="board-stat-tile resourcestat-tile">${sourceMark(source.location)}</span>${labels[source.location] || '媒体来源'}`
      + `<span class="resourcestat-state ${source.online ? 'online' : 'offline'}">${source.online ? '可访问' : '离线，已跳过'}</span>`,
    source.online ? `${count(source.missing)} 项` : '—', sourceDetail(source)));
  return `<div class="cleanupstats resourcestats">${sources.join('')}</div>
    <div class="cleanupstats resourcestats">${statCard('待永久删除', `${count(scan.missing)} 项`, '文件已不在盘上，含回收站')}
    ${statCard('空文件夹', `${count(scan.empty)} 个`, '保留来源根目录')}
    ${statCard('可清理的缓存', `${count(cache.files)} 个`, cache.files ? formatSize(cache.bytes) : '')}</div>
    ${changes ? noteHtml(`将永久删除文件已不在盘上的 ${count(scan.missing)} 条记录和 ${count(scan.empty)} 个空文件夹，并清理 ${count(cache.files)} 个闲置缓存。这一步不可撤销。`, {label: '清理内容'}) : ''}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${changes ? '<button class="danger" type="button" id="resourceApply">清理失效条目</button>' : '<p class="resourcesyncok">已检查可访问的来源，没有待清理的记录、空文件夹或缓存。</p>'}</div>`;
}
