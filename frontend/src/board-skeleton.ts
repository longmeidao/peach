import { icon } from '@peach/legacy/core';
import { selectFieldHtml } from '@peach/legacy/ui';

/** 等待态复用页面容器，只有异步内容使用占位。 */
const line = (width = '60%') => `<span class="skeleton" style="width:${width}"></span>`;
const lines = () => `${line('80%')}${line('48%')}`;
const repeat = (html: string, count: number) => html.repeat(count);
const metrics = (labels: string[], className = 'metricstrip') => `<div class="${className}">${labels.map(label => `<div class="tastesummary"><span class="board-stat-label">${label}</span><b class="board-stat-value">${line('45%')}</b><small class="board-stat-footer">${line('60%')}</small></div>`).join('')}</div>`;
const tabs = (labels: string[], className = 'skeleton-tabs') => `<div class="${className}">${labels.map(label => `<span>${label}</span>`).join('')}</div>`;
const segments = (labels: string[], className: string) => `<div class="${className} skeleton-segments" data-board-segments="true">${labels.map((label,index) => `<span${index===0?' class="skeleton-segment-selected"':''}>${label}</span>`).join('')}</div>`;
const panel = (title: string) => `<section class="insightpanel"><header>${title}</header><div class="insightpanelbody skeleton-lines">${repeat(lines(), 3)}</div></section>`;
const followButton = (label: string, glyph: string, className = '') => `<button class="fbtn follow-skeleton-button ${className}" type="button" disabled>${icon(glyph)}${label ? `<span>${label}</span>` : ''}</button>`;
const followToolbar = (table: boolean) => `<div class="fsechead follow-skeleton-toolbar" data-collapse-toolbar><h3>关注列表</h3><span class="fmeta follow-skeleton-count">${line('132px')}</span><div class="followtoolbaractions">${followButton('检查全部','refresh-cw','primary followcheckall')}<span class="board-button-group follow-skeleton-button-group">${followButton('','layout-grid','selected')}${followButton('','table')}</span><span class="fmanagesort" data-collapse-field>${icon('sort')}${selectFieldHtml([['checked','检查时间']],'checked',{label:'关注列表排序',attr:'disabled'})}</span>${followButton('','arrow-down','square fmanagedir')}${table?'':followButton('全部收起','chevron-up')}</div></div>`;
const followCheck = () => `<span class="fchannelcheck follow-skeleton-check" aria-hidden="true"></span>`;
const followRow = () => `<div class="fsource frow follow-skeleton-source">${followCheck()}<b class="follow-skeleton-source-name">${line('72%')}</b><span class="fprovider follow-skeleton-provider skeleton"></span><span class="follow-skeleton-status skeleton"></span><span class="fmeta fchecked follow-skeleton-date">${line('100%')}</span><span class="fsourceactions follow-skeleton-row-actions"><i></i><i></i></span></div>`;
const followAuthor = (rows = 3) => `<details class="fauthor follow-skeleton-author" open><summary class="fauthorhead"><span class="favatar follow-skeleton-avatar skeleton"></span><b>${line('92px')}</b><span class="fmeta follow-skeleton-author-meta skeleton"></span><span class="board-author-actions follow-skeleton-author-actions"><i></i><button type="button" class="fbtn small" data-follow-author-select disabled>${icon('check-check')}<span data-author-select-label>全选</span></button><i></i></span></summary><div class="fauthorsources follow-skeleton-sources">${repeat(followRow(),rows)}</div></details>`;
/** 表格骨架画多少行由每页条数决定，写死一个数会在别的页大小上多留或少留一屏。
 *  偏好存在旧层那份 `peach.settings.v1` 里，直接读它：骨架跑在 island 挂载之前，
 *  这时候页面自己的状态还不存在。 */
const followPageSize = (): number => {
  try {
    return Number(JSON.parse(localStorage.getItem('peach.settings.v1')||'{}').followPageSize)||20;
  } catch { return 20 }
};
const followTable = (rows: number) => `<div class="ftableframe follow-skeleton-table"><div class="ftablewrap"><div class="ftable follow-skeleton-table-row head">${['','创作者','来源','站点','状态','上次检查',''].map(label=>`<span>${label}</span>`).join('')}</div>${repeat(`<div class="follow-skeleton-table-row">${followCheck()}${['74%','88%','62%','54%','78%'].map(width=>`<span>${line(width)}</span>`).join('')}<span class="fsourceactions follow-skeleton-row-actions"><i></i><i></i></span></div>`,rows)}</div></div>`;

export function detailSkeletonHtml(): string {
  return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${line('85%')}${line('65%')}${repeat(lines(), 4)}</div></aside></div></div>`;
}

export function boardPageSkeleton(
  path: string, options: {followLayout?: string; followPageSize?: number} = {},
): string {
  let body = '';
  if (path === '/stats') {
    body = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${line('38%')}</header>${metrics(['馆藏视频', '看过', '内容标签', '使用空间'])}${panel('馆藏视频')}${panel('内容标签')}</div>`;
  } else if (path === '/taste') {
    body = `<div class="tastepage"><header class="tastehead">${segments(['浏览器记录', 'Peach 内部'], 'insightswitch')}${line('24%')}</header><div class="tastestate"></div>${metrics(['浏览记录', '口味维度', '浏览候选', '私有导出'], 'tastesummaries')}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${repeat(lines(), 4)}</div></section>${panel('口味分析')}<div class="board-activity-charts">${panel('浏览活动')}${panel('时间分布')}</div>${panel('标签')}</div>`;
  } else if (path === '/follow-manage') {
    const table=options.followLayout==='table';
    const content=table?followTable(options.followPageSize||followPageSize()):`<div class="follow-skeleton-authors">${followAuthor(3)}${followAuthor(4)}${followAuthor(3)}</div>`;
    body = `<div class="follow followmanage follow-list-skeleton"><div class="fmanageoverview">${['关注创作者', '启用来源', '检查失败', '未看更新'].map(label => `<div><span>${label}</span><b>${line()}</b></div>`).join('')}</div>${segments(['关注列表', '添加关注', '订阅源', '来源和凭证'], 'follow-workspace-switch')}<div class="fmain"><section class="fsec follow-skeleton-surface" data-follow-workspace-panel="list">${followToolbar(table)}${table?'':`<div class="board-follow-selection follow-skeleton-select-all">${followCheck()}<span>全选本页</span></div>`}<div class="frows fsources" data-layout="${table?'table':'default'}">${content}<footer class="followpagefooter follow-skeleton-footer"><span class="followpageinfo">${line('116px')}</span><span>${line('96px')}</span><span class="follow-skeleton-pages"><i></i><i></i><i></i></span></footer></div></section></div></div>`;
  } else if (path === '/configuration') {
    body = `<div class="configpage">${tabs(['通用', '媒体', '网络与访问', '更新与维护'])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${repeat(`<div class="skeleton-setting">${line('35%')}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${line('100px')}</footer></section></div>`;
  } else if (path === '/activity') {
    body = `<div class="activitypage">${['正在进行', '被挡下的', '最近完成'].map(title => `<section class="activitysection"><h3 class="geist-fieldset-title">${title}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${line('35%')}${lines()}</div></article></div></section>`).join('')}</div>`;
  } else if (path === '/duplicates') {
    body = `<div class="review"><div class="collection-summary">${line('38%')}</div><div class="fsechead dupactions"><h3>批量保留</h3>${line('40%')}</div>${repeat(`<section class="dupgroup"><div class="duphead">${line('45%')}</div><div class="duplist">${repeat(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${line()}</span><span class="dupname">${line('90%')}</span>${line()}${line()}${line()}<span class="duppath">${line('70%')}</span></div>`, 2)}</div></section>`, 2)}</div>`;
  } else if (path === '/quality-goals') {
    body = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${line('20%')}</div><div class="qualitylist">${repeat(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${lines()}</div><footer class="qualityactions">${line('80%')}</footer></article>`, 6)}</div></div>`;
  } else if (path === '/playlists') {
    body = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${line('200px')}</div></header><div class="playlistcards">${repeat(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${lines()}</div></div></article>`, 6)}</div></section>`;
  } else return '';
  return `<div class="board-page-skeleton" data-skeleton="board${path}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${body}</div></div>`;
}
