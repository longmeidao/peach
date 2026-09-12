/** 等待态复用页面容器，只有异步内容使用占位。 */
const line = (width = '60%') => `<span class="skeleton" style="width:${width}"></span>`;
const lines = () => `${line('80%')}${line('48%')}`;
const repeat = (html: string, count: number) => html.repeat(count);
const metrics = (labels: string[], className = 'metricstrip') => `<div class="${className}">${labels.map(label => `<div class="tastesummary"><span class="board-stat-label">${label}</span><b class="board-stat-value">${line('45%')}</b><small class="board-stat-footer">${line('60%')}</small></div>`).join('')}</div>`;
const tabs = (labels: string[], className = 'skeleton-tabs') => `<div class="${className}">${labels.map(label => `<span>${label}</span>`).join('')}</div>`;
const radial = (title: string) => `<section class="board-radial-card"><header><span>${title}</span><b>${line()}</b></header><div class="board-rings skeleton-rings"><span class="skeleton skeleton-ring"></span></div><div class="skeleton-lines">${lines()}</div></section>`;
const panel = (title: string) => `<section class="insightpanel"><header>${title}</header><div class="insightpanelbody skeleton-lines">${repeat(lines(), 3)}</div></section>`;

export function detailSkeletonHtml(): string {
  return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${line('85%')}${line('65%')}${repeat(lines(), 4)}</div></aside></div></div>`;
}

export function boardPageSkeleton(path: string): string {
  let body = '';
  if (path === '/stats') {
    body = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${line('38%')}</header>${metrics(['馆藏视频', '看过', '内容标签', '使用空间'])}<section class="insightdetail"><div class="insightdetailbody"><div class="board-inventory-charts">${radial('网盘与本地')}${radial('媒体库')}</div></div></section>${panel('内容标签')}</div>`;
  } else if (path === '/taste') {
    body = `<div class="tastepage"><header class="tastehead">${tabs(['浏览器记录', 'Peach 内部'])}${line('24%')}</header>${metrics(['浏览记录', '口味维度', '浏览候选', '私有导出'], 'tastesummaries')}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${repeat(lines(), 4)}</div></section>${panel('口味分析')}<div class="board-activity-charts">${panel('浏览活动')}${panel('时间分布')}</div>${panel('标签')}</div>`;
  } else if (path === '/follow-manage') {
    body = `<div class="follow followmanage"><div class="fmanageoverview">${['关注作者', '启用来源', '检查失败', '未看更新'].map(label => `<div><span>${label}</span><b>${line()}</b></div>`).join('')}</div>${tabs(['关注列表', '添加关注', '来源管理'], 'follow-workspace-switch')}<div class="fmain"><section class="fsec" data-follow-panel="sources"><div class="fsechead"><h3>关注列表</h3>${line('30%')}</div><div class="board-follow-selection">${line('45%')}</div><div class="frows fsources" data-layout="default"><div class="board-follow-list">${repeat(`<article class="fauthor"><div class="fauthorhead">${line('40%')}</div><div class="skeleton-lines">${repeat(lines(), 2)}</div></article>`, 4)}</div></div></section></div></div>`;
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
  return `<div class="board-page-skeleton" data-skeleton="board${path}" role="status" aria-label="正在读取页面"><div aria-hidden="true">${body}</div></div>`;
}
