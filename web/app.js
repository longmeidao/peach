import {
  $,
  icon,
  api,
  pageTitle,
  STATE_ROUTES,
  ROUTE_STATES,
  STATE_LABELS,
  isCatalogPath,
  ENTITY_ROUTES,
  ROUTE_ENTITIES,
  entityPath,
  esc,
  SITE_FAVICONS,
  faviconUrl,
  faviconFallbackUrl,
  foldName,
  fmtDur,
  fmtClock,
  fmtSize,
  LOC,
} from './js/core.js';
import { initMiddleTruncate } from './js/middle-truncate.js';
import {
  emptyStateHtml, loadingDotsHtml, mediaViewButtonsHtml, noteHtml, progressHtml, scrollerHtml,
  spinnerHtml, wireScrollers,
} from './js/ui-components.js';

initMiddleTruncate(document);

function renderCatalogLoading(label='正在读取作品'){
  const count=$('#count');
  count.setAttribute('aria-busy','true');
  count.innerHTML=`${spinnerHtml(label)}<span>载入中…</span>`;
}
renderCatalogLoading();

/* 路由同时把页面表面写进 body[data-surface]：限宽等按表面生效的版式
   （管理页不全宽）靠它切换，不用每个渲染函数自己记得加类。
   调用方有传 path 也有传 href 的，这里统一归一成 pathname。 */
const syncPageTitle=path=>{
  document.title=pageTitle(path);
  document.body.dataset.surface=new URL(path,location.origin).pathname;
  paintNav();
};
/* 导航激活态必须在每次路由变化时重算：抽屉与窄栏的按钮是 buildBars 时
   一次性画出来的，管理页不跑 buildBars，切页后它们会停留在上一个页面的
   按下态（实测 /stats 下「首页」还亮着）。 */
function paintNav(){
  document.querySelectorAll('.edge button[data-nav],#drawer .dnav button[data-nav]')
    .forEach(b=>b.setAttribute('aria-pressed',String(navOn(b.dataset.nav))));
}
let surfaceEpoch=0;
const surfacePath=()=>decodeURIComponent(location.pathname);
let lastRoutePath=surfacePath();
const surfaceToken=path=>({epoch:surfaceEpoch,path});
const surfaceCurrent=token=>token.epoch===surfaceEpoch&&surfacePath()===token.path;
const claimSurface=path=>{surfaceEpoch++;return surfaceToken(path)};
const route=(path,replace=false)=>{
  surfaceEpoch++;
  history[replace?'replaceState':'pushState']({},'',path);syncPageTitle(path);
  lastRoutePath=decodeURIComponent(new URL(path,location.href).pathname);
  queueMicrotask(()=>{syncHeaderActions();paintListTitle()});
};

/* ── 脱盘模式 ─────────────────────────────────────────────────────────────────
   脱盘是来源级的：外置盘拔掉只影响 local，115/PikPak 照常可播；反过来也一样。
   服务端 /api/sources 是唯一判据，前端只负责置灰筛选和换掉播放器。 ── */
let sourceOnline={};
const sourceOffline=key=>sourceOnline[key]===false;
const OFFLINE_HINT='脱盘模式：这个来源当前没有挂载';
const OFFLINE_REASON={local:'本地硬盘没有挂载，接上后点重新检测即可播放。',
  '115':'115 网盘没有挂载，检查 CloudDrive 是否在运行。',
  pikpak:'PikPak 没有挂载，检查 CloudDrive 是否在运行。'};
const offlineReason=key=>OFFLINE_REASON[key]||'这个来源当前没有挂载。';
async function loadSourceStatus(){
  try{
    const d=await api('/api/sources');
    sourceOnline=Object.fromEntries((d.sources||[]).map(s=>[s.location,!!s.online]));
  }catch(_e){sourceOnline={}}
  document.body.classList.toggle('offline-source',Object.values(sourceOnline).includes(false));
  dropOfflineFromDefaultLoc();
  return sourceOnline;
}
/* 脱盘的来源要从默认筛选里摘掉，否则首页照样按它筛，出来一屏点开就报脱盘的卡片。
   只动默认值：地址栏里显式写了 `loc=` 就是用户自己选的，不替他改。
   全部来源都脱盘时保持原样——清空筛选会变成「什么都不筛」，那比原状更糟。 */
function dropOfflineFromDefaultLoc(){
  if(initialParams.get('loc'))return;
  const kept=state.loc.split(',').filter(Boolean).filter(k=>sourceOnline[k]!==false);
  if(kept.length&&kept.length!==state.loc.split(',').filter(Boolean).length)state.loc=kept.join(',');
}
const DURATION_TAGS=new Set(['短片-2分内','中片-10分内','长片-30分内','超长片-30分上']);
const SETTINGS_KEY='peach.settings.v1';
const DEFAULT_SIDEBAR_ORDER=['','performers','tags','jav','flagged','playlists','follow','immerse','manage'];
const OPTIONAL_SIDEBAR_KEYS=['stats','review','ads','dupes','trash','follow-manage','quality'];
const ALL_SIDEBAR_KEYS=[...DEFAULT_SIDEBAR_ORDER,...OPTIONAL_SIDEBAR_KEYS];
const SORTS=[['seed','随机'],['rating','评分'],['o','高潮计数'],['plays','观看次数'],['long','时长'],
             ['big','体积'],['new','最近入库'],['played','最近看的']];
const JAV_RELEASE_SORT=['release','发行时间'];
const SORT_KEYS=[...SORTS,JAV_RELEASE_SORT].map(([key])=>key);
const DEFAULT_SETTINGS={batchSize:60,defaultSort:'seed',sortDefaultsVersion:2,hoverDelaySeconds:5,seekSeconds:10,searchHistoryLimit:10,relatedLimit:20,javLayout:'big',ambientMode:true,theaterMode:false,sidebarOrder:DEFAULT_SIDEBAR_ORDER};
let appSettings={...DEFAULT_SETTINGS};
try{appSettings={...DEFAULT_SETTINGS,...JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}}catch(_e){}
const allowedSetting=(value,allowed,fallback)=>allowed.includes(value)?value:fallback;
delete appSettings.rotateMinutes;
/* 上一版移除了随机并把所有人的默认值强制成最近入库。只迁移这一个旧默认，
   评分、观看次数等用户主动选择继续保留。 */
let sortDefaultsMigrated=false;
if((+appSettings.sortDefaultsVersion||0)<2&&appSettings.defaultSort==='new'){
  appSettings.defaultSort='seed';sortDefaultsMigrated=true
}
appSettings.sortDefaultsVersion=2;
appSettings.batchSize=allowedSetting(+appSettings.batchSize,[30,60,90],60);
appSettings.defaultSort=allowedSetting(appSettings.defaultSort,SORT_KEYS,'seed');
appSettings.hoverDelaySeconds=allowedSetting(+appSettings.hoverDelaySeconds,[3,5,8],5);
appSettings.seekSeconds=allowedSetting(+appSettings.seekSeconds,[5,10,30],10);
appSettings.ambientMode=appSettings.ambientMode!==false;
appSettings.theaterMode=appSettings.theaterMode===true;
appSettings.searchHistoryLimit=allowedSetting(+appSettings.searchHistoryLimit,[5,10,20],10);
appSettings.relatedLimit=allowedSetting(+appSettings.relatedLimit,[12,20,30],20);
appSettings.sidebarOrder=[...new Set(Array.isArray(appSettings.sidebarOrder)?appSettings.sidebarOrder:DEFAULT_SIDEBAR_ORDER)].filter(key=>ALL_SIDEBAR_KEYS.includes(key));
if(!appSettings.sidebarOrder.length)appSettings.sidebarOrder=[...DEFAULT_SIDEBAR_ORDER];
document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);
const saveSettings=()=>localStorage.setItem(SETTINGS_KEY,JSON.stringify(appSettings));
if(sortDefaultsMigrated)saveSettings();
function syncSettingsPanel(){
  $('#batchSizeSetting').value=String(appSettings.batchSize);
  $('#defaultSortSetting').value=appSettings.defaultSort;
  $('#hoverDelaySetting').value=String(appSettings.hoverDelaySeconds);
  $('#seekSecondsSetting').value=String(appSettings.seekSeconds);
  $('#searchHistoryLimitSetting').value=String(appSettings.searchHistoryLimit);
  $('#relatedLimitSetting').value=String(appSettings.relatedLimit);
  renderSidebarOrderSetting();
  loadFollowScheduleSetting();
}
let settingsReturnFocus=null,settingsTransition=0;
function openSettings(open=true){
  const panel=$('#settingsPanel');
  if(open){
    settingsTransition++;panel.classList.remove('closing');
    settingsReturnFocus=settingsReturnFocus||document.activeElement;panel.hidden=false;document.body.classList.add('settings-open');syncSettingsPanel();
    queueMicrotask(()=>$('#settingsClose').focus());return
  }
  if(panel.hidden||panel.classList.contains('closing'))return;
  const transition=++settingsTransition;panel.classList.add('closing');
  const finish=()=>{
    if(transition!==settingsTransition||!panel.classList.contains('closing'))return;
    panel.hidden=true;panel.classList.remove('closing');document.body.classList.remove('settings-open');
    if(settingsReturnFocus&&document.contains(settingsReturnFocus))settingsReturnFocus.focus();
    settingsReturnFocus=null;
  };
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)queueMicrotask(finish);
  else{
    panel.querySelector('.settingscard')?.addEventListener('animationend',finish,{once:true});
    setTimeout(finish,380);
  }
}
$('#settingsBtn').onclick=()=>openSettings(true);$('#settingsClose').onclick=()=>openSettings(false);
$('#settingsPanel').onclick=e=>{if(e.target===$('#settingsPanel'))openSettings(false)};
$('#settingsPanel').onkeydown=e=>{
  if(e.key!=='Tab')return;
  const focusable=[...e.currentTarget.querySelectorAll('button:not([disabled]),select:not([disabled]),input:not([disabled]),textarea:not([disabled]),a[href]')];
  if(!focusable.length)return;
  const first=focusable[0],last=focusable.at(-1);
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
};
$('#batchSizeSetting').onchange=e=>{appSettings.batchSize=+e.target.value||60;saveSettings();if(location.pathname==='/')load(true)};
$('#defaultSortSetting').onchange=e=>{appSettings.defaultSort=e.target.value;saveSettings();state.sort=appSettings.defaultSort;if(location.pathname==='/')load(true)};
$('#hoverDelaySetting').onchange=e=>{appSettings.hoverDelaySeconds=+e.target.value||5;document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);saveSettings()};
$('#seekSecondsSetting').onchange=e=>{appSettings.seekSeconds=+e.target.value||10;saveSettings()};
$('#searchHistoryLimitSetting').onchange=e=>{appSettings.searchHistoryLimit=+e.target.value||10;saveSettings();writeSearchHistory(readSearchHistory())};
$('#relatedLimitSetting').onchange=e=>{appSettings.relatedLimit=+e.target.value||20;saveSettings()};
let followScheduleRequest=0;
const followScheduleCopy=status=>{
  if(!status.available)return '只在账本写入端运行';
  if(status.running)return '正在检查全部来源…';
  if(status.last_error)return `上次失败：${status.last_error}`;
  if(status.last_finished_at)return `上次完成 ${localTime(status.last_finished_at)} · 新增 ${status.last_added||0}`;
  if(status.next_run_at)return `下次 ${localTime(status.next_run_at)}`;
  return status.enabled?'等待首次运行':'已关闭';
};
async function loadFollowScheduleSetting(){
  const select=$('#followScheduleSetting'),state=$('#followScheduleState'),request=++followScheduleRequest;
  select.disabled=true;state.innerHTML=loadingDotsHtml('正在读取状态');
  try{
    const status=await api('/api/follow/schedule');if(request!==followScheduleRequest)return;
    select.value=status.enabled?String(status.interval_minutes):'0';
    select.disabled=!status.available;state.textContent=followScheduleCopy(status);
  }catch(error){if(request===followScheduleRequest)state.textContent=`状态未取得：${error.message||error}`}
}
$('#followScheduleSetting').onchange=async e=>{
  const minutes=+e.target.value,state=$('#followScheduleState');e.target.disabled=true;
  state.innerHTML=`${spinnerHtml('保存中')}<span>正在保存…</span>`;
  try{
    const status=await api('/api/follow/schedule',{method:'POST',body:JSON.stringify({enabled:minutes>0,interval_minutes:minutes||60})});
    state.textContent=followScheduleCopy(status);
  }catch(error){state.textContent=error.message||'保存失败'}
  finally{e.target.disabled=false}
};
/* 来源图标：品牌使用已缓存的官方资产；通用操作图标统一使用本地 Lucide 子集。 */
const SRCICON={
  local:icon('hard-drive'),
  '115':'<img class="source-icon" src="/logo?studio=115" alt="" onerror="this.remove()">',
  // PikPak 官方触屏图标（取证 follow-source-icons-measured.md）；/logo 的生成 logo 不对版。
  pikpak:'<img class="source-icon" src="https://mypikpak.com/apple-touch-icon.png" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">',
  online:icon('rss'),
};
const srcBadge=(loc,cost,cls)=>{const label=`${LOC[loc]||loc}${cost==='metered'?' · 计费':''}`;
  return `<span class="${cls||'src'} ${cost==='metered'?'metered':'free'}" title="${esc(label)}" aria-label="${esc(label)}">`
    +(SRCICON[loc]||'')+'</span>'};
/* 空态用 Vercel 的「icon tile + 标题 + 一句解释」结构。不放假动作按钮：
   能执行的操作仍然留在各页自己的工具栏里，空态只负责解释为什么是空的。 */
const emptyState=emptyStateHtml;

/* Toast：挂在 #toasts（body 直下）而不是 #stats 里——检查完会整页重画，
   页内浮层会被冲掉，这里不会。对齐 Geist 的处方（取证见
   docs/reference-snapshots/vercel-geist-toast.md）：只做用户主动动作的
   非阻塞回执，自动消失；hover 暂停计时，右上角关闭。回执可以带一个
   明确的后续动作（action.label + action.run）：光摆数字会让用户去找
   「哪里能点」，Geist 的做法是给一个具名的下一步。失败这类必须跟进的
   事只发一句短 toast，原因和恢复入口留在页面里的持久行上。 */
const toast=(html,{timeout=6000,warn=false,action=null}={})=>{
  const root=$('#toasts');
  const item=document.createElement('div');
  item.className='toast'+(warn?' warn':'');
  item.innerHTML=`${warn?icon('alert'):''}<p>${html}</p>${
    action?`<button class="tact">${esc(action.label)}</button>`:''
    }<button class="tclose" title="关闭" aria-label="关闭提示">${icon('x')}</button>`;
  let timer=null;
  const close=()=>{clearTimeout(timer);item.classList.add('leaving');
    setTimeout(()=>item.remove(),160)};
  item.querySelector('.tclose').onclick=close;
  if(action)item.querySelector('.tact').onclick=()=>{close();action.run()};
  const arm=()=>{if(timeout)timer=setTimeout(close,timeout)};
  item.addEventListener('mouseenter',()=>clearTimeout(timer));
  item.addEventListener('mouseleave',arm);
  root.prepend(item);arm();
  while(root.children.length>4)root.lastElementChild.remove();
  return item;
};

/* 随机排序每次进入首页都换种子；同一次访问继续复用该种子，保证筛选和分页
   不会重复或漏项。「换一批」仍可在当前访问里主动生成下一批。 */
const newSeed=()=>String((Date.now()^(Math.random()*1e9|0))%99991);
const rollSeed=()=>newSeed();
const initialParams=new URLSearchParams(location.search);
const JUNK_KIND_OPTIONS=[['','全部','layout-grid'],['video','视频','play'],['image','图片','pics'],
  ['archive','压缩包','folder-open'],['audio','音频','volume-2'],['url','网址','globe'],
  ['other','其它','hard-drive']];
const cleanJunkKind=value=>JUNK_KIND_OPTIONS.some(([key])=>key===value)?value:'';
let junkKind=cleanJunkKind(initialParams.get('type')||'');
let junkView=initialParams.get('view')==='dismissed'?'dismissed':'pending';
function junkPath(kind=junkKind,view=junkView){
  const params=new URLSearchParams();
  if(kind)params.set('type',kind);if(view==='dismissed')params.set('view','dismissed');
  return '/junk-files'+(params.size?'?'+params:'');
}
const cleanTagFilter=value=>String(value||'').split(',').filter(tag=>tag&&!DURATION_TAGS.has(tag)).join(',');
const cleanSort=(value,fallback=appSettings.defaultSort)=>SORT_KEYS.includes(value)?value:fallback;
let state={loc:initialParams.get('loc')||'local,115',creator:initialParams.get('creator')||'',studio:initialParams.get('studio')||'',
  tag:cleanTagFilter(initialParams.get('tag')),len:initialParams.get('len')||'',dur_min:initialParams.get('dur_min')||'',dur_max:initialParams.get('dur_max')||'',
  tag_match:initialParams.get('tag_match')==='any'?'any':'all',orient:initialParams.get('orient')||'',
  state:ROUTE_STATES[decodeURIComponent(location.pathname)]||initialParams.get('state')||'',sort:cleanSort(initialParams.get('sort')),
  seed:initialParams.get('seed')||rollSeed(),q:initialParams.get('q')||'',jav:initialParams.get('jav')||'',thumb:'1'};
const HOME_QUERY_KEYS=['loc','creator','studio','tag','tag_match','len','dur_min','dur_max','orient','sort','q','jav'];
function homePath(filters=state){
  const path=STATE_ROUTES[filters.state]||'/';
  const params=new URLSearchParams();
  HOME_QUERY_KEYS.forEach(key=>{const value=filters[key];if(value&&!(key==='tag_match'&&value==='all'))params.set(key,value)});
  if(!STATE_ROUTES[filters.state]&&filters.state)params.set('state',filters.state);
  return path+(params.size?'?'+params:'');
}
/* 所有明确的「回首页」动作必须得到同一个干净状态。只改地址为 `/` 不够：state.jav
   等内存筛选还会继续进入 /api/items，让页面看似首页却只剩 JAV。来源选择是用户的
   浏览范围，继续保留；其余分类、搜索和排序恢复首页默认值。 */
function resetHomeState(){
  state={loc:state.loc,creator:'',studio:'',tag:'',tag_match:'all',len:'',dur_min:'',dur_max:'',
    orient:'',state:'',sort:appSettings.defaultSort,seed:rollSeed(),q:'',jav:'',thumb:'1'};
  barsDataCache=null;barsDataPromise=null;
}
function openHome(scroll=false){
  resetHomeState();route('/');$('#q').value='';disposeStage(false);showHomeSurfaces();
  buildEdge();buildBars();load(true);
  if(scroll)window.scrollTo({top:0,behavior:'smooth'});
}
const ENTITY_FILTER_KEYS=['loc','creator','tag','dur_min','dur_max','orient','sort'];
const emptyEntityFilters=()=>Object.fromEntries(
  ENTITY_FILTER_KEYS.map(key=>[key,key==='sort'?'new':'']));
const parseEntityFilters=search=>{const params=new URLSearchParams(search),filters=emptyEntityFilters();
  ENTITY_FILTER_KEYS.forEach(key=>{filters[key]=key==='sort'?cleanSort(params.get(key),'new'):(params.get(key)||'')});return filters};
const entityFilterSearch=filters=>{const params=new URLSearchParams();
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&!(key==='sort'&&filters[key]==='new'))params.set(key,filters[key])});
  return params.toString()};
let barsContext={type:'home',filters:state},detailReturnBarsContext=null;
const cloneBarsContext=context=>context&&context.type==='entity'
  ? {...context,filters:{...context.filters}}:context;
const activeFilterState=()=>barsContext.type==='home'?state:barsContext.filters;
$('#q').value=state.q;
const REP={};   // 创作者/厂牌 → 代表作 id，用来做圆头像（裁接触印相中心格，不另造图）
let offset=0,total=0,facets=null,current=null,detailReturnPath='/',activeQueue=null;
let detailOriginAnchor=null,detailOriginAbove=false,detailReturnNeedsRestore=false;
const CACHE={};
const cache=items=>{items.forEach(x=>CACHE[x.id]=x);return items};
let detailStreamSession='',detailPlayer=null,detailStatsTimer=null,detailNetTimer=null,detailNetHideTimer=null;
function newStreamSession(){
  return globalThis.crypto?.randomUUID?.()||`${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}
function detailStreamUrl(id){
  if(!detailStreamSession)detailStreamSession=newStreamSession();
  return `/stream?id=${id}&session=${encodeURIComponent(detailStreamSession)}`;
}
function directDetailSource(it){
  return {src:detailStreamUrl(it.id),type:String(it.name||'').toLowerCase().endsWith('.webm')?'video/webm':'video/mp4'};
}
async function detailStreamSource(it){
  const direct=directDetailSource(it);
  if(!['115','pikpak'].includes(it.location))return direct;
  try{
    const plan=await api(`/api/stream-plan?id=${it.id}&session=${encodeURIComponent(detailStreamSession)}`);
    if(plan.protocol==='hls'&&plan.src)return {src:plan.src,type:plan.mime_type||'application/vnd.apple.mpegurl'};
  }catch(_e){}
  return direct;
}
function cancelDetailStream(){
  const session=detailStreamSession;if(!session)return;
  detailStreamSession='';
  cancelStreamSession(session);
}
function cancelStreamSession(session){
  if(!session)return;
  fetch(`/api/stream-cancel?session=${encodeURIComponent(session)}`,{
    method:'POST',credentials:'same-origin',keepalive:true
  }).then(r=>r.json()).then(result=>{
    document.documentElement.dataset.peachStreamCancel=JSON.stringify(result)
  }).catch(()=>{});
}
function disposeStage(push=false,preserveInlineOrigin=false){
  const stage=$('#stage');
  // 关注详情会把舞台插到头像和筛选条之后。离开详情前先放回 main 的固定槽位，
  // 否则下一次重绘 #stats 会连同 #stage 一起删掉，后续所有详情都打不开。
  const main=$('#main'),combo=$('#combo');
  if(stage.parentElement!==main)main.insertBefore(stage,combo);
  if(detailStatsTimer){clearInterval(detailStatsTimer);detailStatsTimer=null}
  if(detailNetTimer){clearInterval(detailNetTimer);detailNetTimer=null}
  if(detailNetHideTimer){clearTimeout(detailNetHideTimer);detailNetHideTimer=null}
  if(detailPlayer){try{detailPlayer.pause();detailPlayer.dispose()}catch(_e){}detailPlayer=null}
  stage.querySelectorAll('video').forEach(video=>{
    if(video._hop)clearInterval(video._hop);
    video.pause();video.removeAttribute('src');video.load();video.remove()});
  cancelDetailStream();
  stage.innerHTML='';stage.hidden=true;document.body.classList.remove('detail-open');current=null;activeQueue=null;
  if(!preserveInlineOrigin){
    detailOriginAnchor=null;detailOriginAbove=false;detailReturnNeedsRestore=false;
  }
  scheduleStickySurfaces();
  if(push)route(detailReturnPath||'/');
}

function placeItemDetail(anchor,above=false){
  const stage=$('#stage'),main=$('#main'),combo=$('#combo');
  if(!anchor?.isConnected){main.insertBefore(stage,combo);return}
  const card=anchor.closest('[data-id],[data-mix-seed]')||anchor;
  const container=card.parentElement;
  if(container&&getComputedStyle(container).display==='grid'){
    const top=card.getBoundingClientRect().top;
    const siblings=[...container.children].filter(item=>item!==stage&&!item.hidden);
    const row=siblings.filter(item=>Math.abs(item.getBoundingClientRect().top-top)<2);
    const edge=above?row[0]:row[row.length-1];
    if(edge)container.insertBefore(stage,above?edge:edge.nextSibling);
    else container.append(stage);
    return;
  }
  const block=card.closest('.shorts-inline,.srow,.nrow,section')||card;
  const parent=block.parentElement;
  if(parent)parent.insertBefore(stage,above?block:block.nextSibling);
  else main.insertBefore(stage,combo);
}

function itemDetailStickyOffset(){
  const stage=$('#stage');
  return ['.top','#tagbar','#count','.entitytagbar','.entitycollectionhead'].reduce((bottom,selector)=>{
    const el=$(selector),css=el&&getComputedStyle(el);
    const beforeStage=!!el&&(el.compareDocumentPosition(stage)&Node.DOCUMENT_POSITION_FOLLOWING);
    if(!beforeStage||el.offsetParent===null||css.position!=='sticky')return bottom;
    const top=parseFloat(css.top);
    return Number.isFinite(top)?Math.max(bottom,top+el.getBoundingClientRect().height):bottom;
  },0);
}

function scrollItemDetailIntoView(){
  const stage=$('#stage');
  stage.style.scrollMarginTop=`${itemDetailStickyOffset()+8}px`;
  stage.scrollIntoView({behavior:'auto',block:'start'});
  scheduleStickySurfaces();
}
function bufferedAhead(video){
  const at=video.currentTime||0;
  for(let i=0;i<video.buffered.length;i++)if(video.buffered.start(i)<=at&&video.buffered.end(i)>=at)
    return Math.max(0,video.buffered.end(i)-at);
  return 0;
}
function streamEntries(id,session=''){
  const encoded=session?encodeURIComponent(session):'';
  return performance.getEntriesByType('resource').filter(x=>x.name.includes('/stream')&&
    (x.name.includes('/stream?id='+id)||x.name.includes('/stream/hls/'+id+'/'))&&
    (!encoded||x.name.includes('session='+encoded)));
}
function streamSpeedBits(id,session=''){
  const entries=streamEntries(id,session);
  const bytes=entries.reduce((n,x)=>n+(x.transferSize||x.encodedBodySize||0),0);
  const seconds=entries.reduce((n,x)=>n+(x.duration||0),0)/1000;
  return bytes>0&&seconds>0?bytes*8/seconds:0;
}
function playerSpeedBits(player,id,session=''){
  let vhs=null;try{vhs=player?.tech({IWillNotUseThisInPlugins:true})?.vhs?.stats||null}catch(_e){}
  const bandwidth=Number(vhs?.bandwidth)||0;
  return bandwidth>0?bandwidth:streamSpeedBits(id,session);
}
function fmtSpeed(bits){
  if(!Number.isFinite(bits)||bits<=0)return '加载中…';
  const bytes=bits/8;
  return bytes>=1048576?`${(bytes/1048576).toFixed(1)} MB/s`:`${Math.max(1,Math.round(bytes/1024))} KB/s`;
}
function applyAmbientMode(enabled,save=true){
  appSettings.ambientMode=!!enabled;if(save)saveSettings();
  $('#stage')?.classList.toggle('ambient-on',appSettings.ambientMode);
  document.dispatchEvent(new CustomEvent('peachambientchange',{detail:{enabled:appSettings.ambientMode}}));
}
function syncPlayerTheaterButton(button){
  if(!button)return;
  const label=appSettings.theaterMode?'默认视图':'影院模式';
  button.setAttribute('aria-pressed',String(appSettings.theaterMode));button.setAttribute('aria-label',label);
  button.querySelector('use')?.setAttribute('href',appSettings.theaterMode?'#i-theater-exit':'#i-theater-enter');
  const tooltip=button.querySelector('.vjs-peach-tooltip');if(tooltip)tooltip.innerHTML=`${label} <kbd>T</kbd>`;
}
function applyTheaterMode(enabled,save=true){
  appSettings.theaterMode=!!enabled;if(save)saveSettings();
  const stage=$('#stage');stage?.classList.toggle('theater-mode',appSettings.theaterMode);
  syncPlayerTheaterButton(stage?.querySelector('[data-player-theater]'));
  if(detailPlayer&&!detailPlayer.isDisposed())requestAnimationFrame(()=>detailPlayer.trigger('resize'));
}
function mountPlayerAmbient(video){
  const stage=$('#stage'),canvas=stage?.querySelector('.ambientcanvas');if(!canvas)return()=>{};
  const ctx=canvas.getContext('2d',{alpha:false});let stopped=false,last=0,scheduled=false;
  const clear=()=>{ctx.clearRect(0,0,canvas.width,canvas.height);stage.style.removeProperty('--video-glow')};
  const schedule=()=>{if(stopped||scheduled||video.paused||!appSettings.ambientMode)return;scheduled=true;
    if(video.requestVideoFrameCallback)video.requestVideoFrameCallback(t=>paint(t));else requestAnimationFrame(paint)};
  const paint=now=>{scheduled=false;if(stopped||!appSettings.ambientMode){if(!stopped)clear();return}
    if(!document.hidden&&!video.paused&&now-last>480){last=now;
      try{ctx.drawImage(video,0,0,canvas.width,canvas.height);
        const px=ctx.getImageData(0,0,canvas.width,canvas.height).data;let r=0,g=0,b=0,n=0;
        for(let i=0;i<px.length;i+=16){r+=px[i];g+=px[i+1];b+=px[i+2];n++}
        if(n)stage.style.setProperty('--video-glow',`rgb(${Math.round(r/n)} ${Math.round(g/n)} ${Math.round(b/n)})`)
      }catch(_e){}}
    schedule()};
  const onChange=event=>{stage.classList.toggle('ambient-on',event.detail.enabled);if(event.detail.enabled)schedule();else clear()};
  document.addEventListener('peachambientchange',onChange);video.addEventListener('play',schedule);schedule();
  return()=>{stopped=true;document.removeEventListener('peachambientchange',onChange);video.removeEventListener('play',schedule);clear()};
}
function mountPlayerQualityControl(player,video,fallbackHeight=0){
  const controlBar=player.getChild('controlBar')?.el();
  if(!controlBar||controlBar.querySelector('[data-player-quality]'))return;
  const root=document.createElement('div');
  root.className='vjs-peach-settings vjs-control';root.dataset.playerQuality='';
  root.innerHTML=`<button type="button" class="vjs-peach-settings-toggle" aria-label="播放器设置" aria-expanded="false">
    ${icon('settings')}<span data-player-quality-badge hidden></span></button>
    <div class="vjs-peach-settings-menu" role="menu" aria-label="播放器设置" hidden></div>`;
  const fullscreen=controlBar.querySelector('.vjs-fullscreen-control');
  controlBar.insertBefore(root,fullscreen||null);
  const toggle=root.querySelector('button'),badge=root.querySelector('[data-player-quality-badge]');
  const menu=root.querySelector('.vjs-peach-settings-menu');
  const levels=typeof player.qualityLevels==='function'?player.qualityLevels():null;
  let selected='auto';
  const resolution=(width,height)=>{const values=[Number(width),Number(height)].filter(value=>value>0);return values.length?Math.min(...values):0};
  const rows=()=>{
    const result=[];
    if(levels?.length){
      result.push({key:'auto',label:'自动',pixels:0});
      for(let index=0;index<levels.length;index++){
        const level=levels[index],pixels=resolution(level.width,level.height);
        result.push({key:String(index),label:pixels?`${pixels}p`:(level.id||`线路 ${index+1}`),pixels});
      }
      return result;
    }
    const pixels=resolution(video.videoWidth,video.videoHeight)||Number(fallbackHeight)||0;
    return [{key:'original',label:pixels?`${pixels}p`:'原画',pixels}];
  };
  const qualityRows=()=>{
    const options=rows();
    if(!levels?.length)selected='original';
    const active=options.find(option=>option.key===selected)||options[0];
    const activePixels=active.pixels||Math.max(0,...options.map(option=>option.pixels||0));
    badge.textContent=activePixels>=2160?'4K':activePixels>=720?'HD':'';badge.hidden=!badge.textContent;
    return {options,active};
  };
  const close=()=>{menu.hidden=true;toggle.setAttribute('aria-expanded','false')};
  const showMain=()=>{
    const {active}=qualityRows(),speed=Number(player.playbackRate())||1;
    menu.innerHTML=`<div class="vjs-peach-panel-menu"><button type="button" class="vjs-peach-menu-row" role="menuitemcheckbox" data-player-ambient aria-checked="${appSettings.ambientMode}">
      ${icon('player-ambient')}<span>氛围模式</span><i class="vjs-peach-switch" aria-hidden="true"></i></button>
      <button type="button" class="vjs-peach-menu-row" role="menuitem" data-player-speed>${icon('player-speed')}<span>播放速度</span><b>${speed===1?'正常':speed+'×'}</b>${icon('player-menu-next')}</button>
      <button type="button" class="vjs-peach-menu-row" role="menuitem" data-player-quality-view>${icon('player-quality')}<span>清晰度</span><b>${esc(active.label)}</b>${icon('player-menu-next')}</button></div>`;
    menu.querySelector('[data-player-ambient]').onclick=()=>{applyAmbientMode(!appSettings.ambientMode);showMain()};
    menu.querySelector('[data-player-speed]').onclick=showSpeed;
    menu.querySelector('[data-player-quality-view]').onclick=showQuality;
  };
  const showSpeed=()=>{
    const selectedSpeed=Number(player.playbackRate())||1,speeds=[.25,.5,.75,1,1.25,1.5,1.75,2];
    menu.innerHTML=`<div class="vjs-peach-panel-header"><button type="button" class="vjs-peach-menu-back" data-player-menu-back aria-label="返回上一个菜单">${icon('player-menu-back')}</button><strong>播放速度</strong></div><div class="vjs-peach-panel-menu">${speeds.map(speed=>
      `<button type="button" class="vjs-peach-menu-option" role="menuitemradio" data-player-speed-option="${speed}" aria-checked="${speed===selectedSpeed}"><span class="vjs-peach-option-check">${speed===selectedSpeed?icon('player-option-check'):''}</span><span class="vjs-peach-option-label">${speed===1?'正常':speed+'×'}</span></button>`).join('')}</div>`;
    menu.querySelector('[data-player-menu-back]').onclick=showMain;
    menu.querySelectorAll('[data-player-speed-option]').forEach(button=>button.onclick=()=>{player.playbackRate(Number(button.dataset.playerSpeedOption));showMain()});
  };
  const showQuality=()=>{
    const {options}=qualityRows();
    menu.innerHTML=`<div class="vjs-peach-panel-header"><button type="button" class="vjs-peach-menu-back" data-player-menu-back aria-label="返回上一个菜单">${icon('player-menu-back')}</button><strong>清晰度</strong></div><div class="vjs-peach-panel-menu">${options.map(option=>
      `<button type="button" class="vjs-peach-menu-option" role="menuitemradio" data-player-quality-option="${esc(option.key)}" aria-checked="${option.key===selected}"><span class="vjs-peach-option-check">${option.key===selected?icon('player-option-check'):''}</span><span class="vjs-peach-option-label">${esc(option.label)}</span></button>`).join('')}</div>`;
    menu.querySelector('[data-player-menu-back]').onclick=showMain;
    menu.querySelectorAll('[data-player-quality-option]').forEach(button=>button.onclick=()=>{
      selected=button.dataset.playerQualityOption;
      if(levels?.length)for(let index=0;index<levels.length;index++)levels[index].enabled=selected==='auto'||selected===String(index);
      showMain();
    });
  };
  toggle.onclick=event=>{event.stopPropagation();const open=menu.hidden;if(open)showMain();menu.hidden=!open;toggle.setAttribute('aria-expanded',String(open))};
  const outside=event=>{if(!root.contains(event.target))close()};document.addEventListener('pointerdown',outside);
  root.addEventListener('keydown',event=>{if(event.key==='Escape'){close();toggle.focus()}});
  video.addEventListener('loadedmetadata',()=>{if(!menu.hidden)showMain();else qualityRows()});
  levels?.on?.(['addqualitylevel','removequalitylevel'],()=>{if(!menu.hidden)showMain();else qualityRows()});
  player.on('dispose',()=>document.removeEventListener('pointerdown',outside));qualityRows();
  mountPlayerTheaterControl(player,root);
  mountPlayerChromeLayout(player);
}
function mountPlayerTheaterControl(player,settingsRoot){
  const controlBar=player.getChild('controlBar')?.el();if(!controlBar||controlBar.querySelector('[data-player-theater]'))return;
  const root=document.createElement('div');root.className='vjs-peach-theater vjs-control';
  root.innerHTML=`<button type="button" data-player-theater aria-label="影院模式" aria-keyshortcuts="T" aria-pressed="${appSettings.theaterMode}">${icon(appSettings.theaterMode?'theater-exit':'theater-enter')}<span class="vjs-peach-tooltip" role="tooltip"></span></button>`;
  controlBar.insertBefore(root,settingsRoot.nextSibling);
  syncPlayerTheaterButton(root.querySelector('button'));
  root.querySelector('button').onclick=event=>{event.stopPropagation();applyTheaterMode(!appSettings.theaterMode)};
}
function mountPlayerChromeLayout(player){
  const controlBar=player.getChild('controlBar')?.el();if(!controlBar||controlBar.querySelector('.vjs-peach-right-controls'))return;
  const play=controlBar.querySelector(':scope>.vjs-play-control');
  if(play&&!play.querySelector(':scope>.vjs-peach-hover'))play.insertAdjacentHTML('beforeend','<span class="vjs-peach-hover" aria-hidden="true"></span>');
  const explicitIcon=(button,name)=>{
    if(!button)return null;
    button.dataset.peachExplicitIcon='';
    button.insertAdjacentHTML('beforeend',icon(name,'vjs-peach-control-icon'));
    return button.querySelector(':scope>.vjs-peach-control-icon use');
  };
  const playUse=explicitIcon(play,'player-play');
  const syncPlayIcon=()=>playUse?.setAttribute('href',player.paused()||player.ended()?'#i-player-play':'#i-player-pause');
  player.on(['play','pause','ended'],syncPlayIcon);syncPlayIcon();
  const volume=controlBar.querySelector(':scope>.vjs-volume-panel');
  const mute=volume?.querySelector(':scope>.vjs-mute-control'),muteUse=explicitIcon(mute,'player-volume');
  const syncVolumeIcon=()=>muteUse?.setAttribute('href',player.muted()||player.volume()===0?'#i-player-volume-muted':'#i-player-volume');
  player.on('volumechange',syncVolumeIcon);syncVolumeIcon();
  const time=document.createElement('button');let remaining=false;
  time.type='button';time.className='vjs-peach-time vjs-control';time.dataset.playerTime='';
  time.innerHTML='<span class="vjs-peach-time-text"></span>';
  const timeText=time.querySelector('.vjs-peach-time-text');
  const syncTime=()=>{
    const current=Math.max(0,Number(player.currentTime())||0),duration=Math.max(0,Number(player.duration())||0);
    const shown=remaining?`-${fmtClock(Math.max(0,duration-current))}`:fmtClock(current);
    timeText.textContent=`${shown} / ${fmtClock(duration)}`;
    time.dataset.remaining=String(remaining);
    time.setAttribute('aria-label',remaining?`剩余 ${fmtClock(Math.max(0,duration-current))}，总时长 ${fmtClock(duration)}；点击显示已播放时间`:`已播放 ${fmtClock(current)}，总时长 ${fmtClock(duration)}；点击显示剩余时间`);
  };
  time.onclick=event=>{event.stopPropagation();remaining=!remaining;syncTime()};
  player.on(['timeupdate','durationchange','loadedmetadata'],syncTime);syncTime();
  if(volume)volume.insertAdjacentElement('afterend',time);else controlBar.append(time);
  const pip=controlBar.querySelector(':scope>.vjs-picture-in-picture-control');
  explicitIcon(pip,'player-pip');
  const fullscreen=controlBar.querySelector(':scope>.vjs-fullscreen-control');
  const fullscreenUse=explicitIcon(fullscreen,'player-fullscreen-enter');
  const syncFullscreenIcon=()=>fullscreenUse?.setAttribute('href',player.isFullscreen()?'#i-player-fullscreen-exit':'#i-player-fullscreen-enter');
  player.on('fullscreenchange',syncFullscreenIcon);syncFullscreenIcon();
  const controls=[
    pip,
    controlBar.querySelector(':scope>.vjs-peach-settings'),
    controlBar.querySelector(':scope>.vjs-peach-theater'),
    fullscreen,
  ].filter(Boolean);
  if(!controls.length)return;
  const group=document.createElement('div');group.className='vjs-peach-right-controls';group.setAttribute('aria-label','播放器视图控制');
  controlBar.insertBefore(group,controls[0]);
  controls.forEach(control=>{
    control.insertAdjacentHTML('beforeend','<span class="vjs-peach-hover" aria-hidden="true"></span>');
    group.append(control);
  });
}
function mountPlayerSeekPreview(player,it,options={}){
  const progress=player.getChild('controlBar')?.el()?.querySelector('.vjs-progress-control');
  if(!progress||progress.querySelector('[data-player-seek-preview]'))return;
  const hasThumbnail=options.thumbnail!==false;
  const preview=document.createElement('div');
  preview.className='vjs-peach-seek-preview';preview.dataset.playerSeekPreview='';preview.hidden=true;
  preview.innerHTML=`${hasThumbnail?'<img alt="" hidden>':''}<span class="mono">0:00</span>`;
  progress.append(preview);
  const image=preview.querySelector('img'),label=preview.querySelector('span');
  let cell=-1;
  const move=event=>{
    if(event.pointerType==='touch')return;
    const duration=Number(player.duration())||Number(it.duration)||0;
    if(!duration)return;
    const rect=progress.getBoundingClientRect();
    const ratio=Math.min(1,Math.max(0,(event.clientX-rect.left)/rect.width));
    const width=image?Math.min(240,Math.max(160,rect.width*.28)):76;
    const x=Math.min(rect.width-width/2,Math.max(width/2,event.clientX-rect.left));
    preview.style.left=`${x}px`;preview.hidden=false;label.textContent=fmtClock(duration*ratio);
    if(image){
      const nextCell=Math.min(8,Math.floor(ratio*9));
      if(nextCell!==cell){cell=nextCell;image.hidden=false;image.src=`/poster?id=${encodeURIComponent(it.id)}&c=${nextCell}`}
    }
  };
  const hide=()=>{preview.hidden=true};
  if(image)image.onerror=()=>{image.hidden=true};
  progress.addEventListener('pointermove',move);progress.addEventListener('pointerleave',hide);
  player.on('dispose',()=>{progress.removeEventListener('pointermove',move);progress.removeEventListener('pointerleave',hide)});
}
function mountPlayerCenterControls(player){
  if(player.el().querySelector('[data-player-center-controls]'))return;
  const root=document.createElement('div');
  root.className='vjs-peach-center-controls';root.dataset.playerCenterControls='';
  root.setAttribute('aria-hidden','true');
  root.innerHTML=`<span class="vjs-peach-center-bezel"><svg class="vjs-peach-center-play" aria-hidden="true"><use href="#i-player-bezel-play"></use></svg><svg class="vjs-peach-center-pause" aria-hidden="true"><use href="#i-player-bezel-pause"></use></svg></span>`;
  const playerRoot=player.el();playerRoot.append(root);
  const spinner=playerRoot.querySelector('.vjs-loading-spinner');
  if(spinner)spinner.innerHTML='<span class="vjs-peach-spinner-container"><span class="vjs-peach-spinner-rotator"><span class="vjs-peach-spinner-left"><span class="vjs-peach-spinner-circle"></span></span><span class="vjs-peach-spinner-right"><span class="vjs-peach-spinner-circle"></span></span></span></span>';
  let gesture=false,gestureTimer=0;
  const sync=()=>{const playing=!player.paused()&&!player.ended();root.dataset.state=playing?'pause':'play'};
  const feedback=()=>{root.classList.remove('is-feedback');void root.offsetWidth;root.classList.add('is-feedback')};
  const arm=()=>{gesture=true;clearTimeout(gestureTimer);gestureTimer=setTimeout(()=>{gesture=false},600)};
  const onKey=event=>{if(event.key===' '||event.key.toLowerCase()==='k')arm()};
  const onState=()=>{sync();if(gesture){gesture=false;clearTimeout(gestureTimer);feedback()}};
  const hideFeedback=()=>root.classList.remove('is-feedback');
  playerRoot.addEventListener('pointerdown',arm,true);playerRoot.addEventListener('keydown',onKey,true);
  root.addEventListener('animationend',hideFeedback);
  player.on(['play','pause','ended'],onState);player.on(['waiting','seeking'],hideFeedback);player.on('dispose',()=>{clearTimeout(gestureTimer);playerRoot.removeEventListener('pointerdown',arm,true);playerRoot.removeEventListener('keydown',onKey,true)});sync();
}
function mountDetailPlayer(it,video,autoplay,options={}){
  if(detailPlayer)return detailPlayer;
  const statsButton=$('#playerStatsBtn'),statsPanel=$('#playerStats');
  const source=()=>options.source?Promise.resolve(options.source):detailStreamSource(it);
  if(!globalThis.videojs){
    video.controls=true;
    source().then(next=>{video.src=next.src;if(autoplay)video.play().catch(()=>{})}).catch(()=>{});
    return null;
  }
  detailPlayer=globalThis.videojs(video,{
    controls:true,preload:'metadata',language:'zh-CN',responsive:true,
    controlBar:{
      pictureInPictureToggle:true,currentTimeDisplay:true,timeDivider:true,
      durationDisplay:true,remainingTimeDisplay:false
    }
  });
  const expected=Number(it.duration)||0;
  let correcting=false;
  const enforceDuration=()=>{
    if(!expected||correcting||!detailPlayer||detailPlayer.isDisposed())return;
    const reported=Number(detailPlayer.duration());
    if(!Number.isFinite(reported)||Math.abs(reported-expected)>Math.max(2,expected*.001)){
      correcting=true;detailPlayer.duration(expected);queueMicrotask(()=>{correcting=false})
    }
  };
  const updateStats=()=>{
   if(!statsPanel||statsPanel.hidden||!detailPlayer||detailPlayer.isDisposed())return;
   const quality=video.getVideoPlaybackQuality?video.getVideoPlaybackQuality():null;
     const rect=video.getBoundingClientRect(),current=`${video.videoWidth||it.width||'?'}×${video.videoHeight||it.height||'?'}`;
      const resources=streamEntries(it.id,detailStreamSession);
      const bytes=resources.reduce((n,x)=>n+(x.transferSize||x.encodedBodySize||0),0);
      const seconds=resources.reduce((n,x)=>n+(x.duration||0),0)/1000;
      const speed=playerSpeedBits(detailPlayer,it.id,detailStreamSession)||(seconds>0?bytes*8/seconds:0);
     const segmented=String(detailPlayer.currentSource()?.type||'').includes('mpegurl');
     const rows=[
      ['视频 ID / 会话',`${it.id} / ${detailStreamSession.slice(0,8)}`],
      ['视口 / 帧',`${Math.round(rect.width)}×${Math.round(rect.height)} / ${quality?`${quality.totalVideoFrames-quality.droppedVideoFrames} of ${quality.totalVideoFrames}`:'—'}`],
      ['当前 / 最佳分辨率',`${current} / ${it.width||'?'}×${it.height||'?'}`],
       ['编码 / 传输',`${String(it.name||'').split('.').pop()?.toUpperCase()||'—'} / ${segmented?'HLS':'HTTP Range'}`],
      ['连接速度',speed?`${(speed/1e6).toFixed(1)} Mbps`:'—'],
      ['网络活动',`${bytes?fmtSize(bytes):'—'} · ${resources.length} 请求`],
      ['缓冲健康',`${bufferedAhead(video).toFixed(1)} 秒`],
      ['播放时间',`${fmtClock(video.currentTime)} / ${fmtClock(expected||detailPlayer.duration())}`],
      ['日期',new Date().toLocaleString()],
    ];
    statsPanel.innerHTML='<dl>'+rows.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')+'</dl>';
  };
  detailPlayer.on(['loadstart','loadedmetadata','durationchange','error'],enforceDuration);
  const player=detailPlayer;
  let segmentedSource=false,fallbackUsed=false;
  const netBadge=$('#playerNet');
  const updateNet=()=>{if(!netBadge||player.isDisposed())return;
    netBadge.textContent=`加载速度 ${fmtSpeed(playerSpeedBits(player,it.id,detailStreamSession))}`};
  const showNet=()=>{if(!netBadge)return;netBadge.hidden=false;updateNet();
    if(detailNetTimer)clearInterval(detailNetTimer);detailNetTimer=setInterval(updateNet,500)};
  const hideNet=()=>{if(!netBadge)return;if(detailNetHideTimer)clearTimeout(detailNetHideTimer);
    detailNetHideTimer=setTimeout(()=>{netBadge.hidden=true;if(detailNetTimer){clearInterval(detailNetTimer);detailNetTimer=null}},1400)};
  player.on(['loadstart','progress','waiting','stalled'],showNet);
  player.on(['canplay','playing'],()=>{updateNet();hideNet()});
  player.on('error',()=>{
    if(segmentedSource&&!fallbackUsed&&!player.isDisposed()){
      fallbackUsed=true;segmentedSource=false;
      player.src(directDetailSource(it));
      if(autoplay)player.play().catch(()=>{});
      return;
    }
    // 播到一半掉盘时 video 元素只报通用错误；来源状态才分得清脱盘和文件损坏。
    if(options.checkSourceStatus===false)return;
    loadSourceStatus().then(status=>{
      if(status[it.location]!==false||player.isDisposed())return;
      player.error({code:2,message:`脱盘模式 · ${offlineReason(it.location)}`});
    });
  });
  detailPlayer.ready(()=>{
    enforceDuration();mountPlayerQualityControl(detailPlayer,video,it.height);
    mountPlayerSeekPreview(detailPlayer,it,{thumbnail:!options.source});
    mountPlayerCenterControls(detailPlayer);
    if(statsButton)statsButton.hidden=false
  });
  if(statsButton&&statsPanel)statsButton.onclick=()=>{
    const open=statsPanel.hidden;statsPanel.hidden=!open;statsButton.setAttribute('aria-pressed',String(open));
    if(open){updateStats();if(detailStatsTimer)clearInterval(detailStatsTimer);detailStatsTimer=setInterval(updateStats,1000)}
    else if(detailStatsTimer){clearInterval(detailStatsTimer);detailStatsTimer=null}
  };
  source().then(source=>{
    if(!detailPlayer||detailPlayer!==player||player.isDisposed())return;
    segmentedSource=String(source.type||'').includes('mpegurl');
    player.src(source);
    enforceDuration();setTimeout(enforceDuration,0);setTimeout(enforceDuration,250);
    if(autoplay)player.play().catch(()=>{});
  }).catch(()=>{});
  return detailPlayer;
}
const selected=new Set(),followSelected=new Set();
let selectMode=false,lastSelectedId=null,followLastSelectedId=null,selectSurface='';
const currentSelectSurface=()=>location.pathname==='/follow'?'follow':location.pathname==='/junk-files'?'junk':'catalog';
function paintSelection(){
  document.querySelectorAll('.card[data-id]').forEach(card=>card.classList.toggle('selected',selected.has(+card.dataset.id)));
  document.querySelectorAll('.followitem[data-follow-item]').forEach(card=>
    card.classList.toggle('selected',followSelected.has(+card.dataset.followItem)));
  const followPage=location.pathname==='/follow',junkPage=location.pathname==='/junk-files';
  const picked=followPage?followSelected:selected;
  $('#batchbar').hidden=!picked.size;$('#batchCount').textContent=`已选 ${picked.size} 项`;
  $('#batchbar').querySelectorAll('[data-batch]').forEach(button=>button.hidden=followPage||junkPage);
  $('#batchbar').querySelectorAll('[data-follow-batch],[data-follow-control]').forEach(button=>button.hidden=!followPage);
  $('#batchbar').querySelectorAll('[data-trash-only]').forEach(button=>button.hidden=followPage||junkPage||state.state!=='trash');
  $('#batchbar').querySelectorAll('[data-batch="like"],[data-batch="seen"],[data-batch="later"],[data-batch="dispose"]').forEach(button=>button.hidden=followPage||junkPage||state.state==='trash');
  $('#batchbar').querySelectorAll('[data-junk-batch]').forEach(button=>{
    const operation=button.dataset.junkBatch;
    button.hidden=!junkPage||(operation==='dismiss-junk'&&junkView==='dismissed')
      ||(operation==='reconsider-junk'&&junkView!=='dismissed');
  });
  paintTagIndexSelection();
}
function setSelectMode(on,clear=false){
  if(on&&!selectMode)selectSurface=currentSelectSurface();
  selectMode=!!on;if(!selectMode)selectSurface='';document.body.classList.toggle('select-mode',selectMode);
  if(selectMode)releaseHoverPreviews();
  $('#selectMode').setAttribute('aria-pressed',selectMode);if(clear){selected.clear();followSelected.clear();selectedIndexTags.clear();lastSelectedId=null;followLastSelectedId=null}paintSelection()}
/* 只取网格直属卡片：竖屏条是嵌在网格里的横向滚动条，不该被 Shift 范围选中顺带框进来。 */
function visibleCardIds(){return [...document.querySelectorAll('#grid > .card[data-id]')].map(card=>+card.dataset.id)}
function toggleSelection(id,range=false){
  if(range&&lastSelectedId!=null){const ids=visibleCardIds(),a=ids.indexOf(lastSelectedId),b=ids.indexOf(id);
    if(a>=0&&b>=0){for(let i=Math.min(a,b);i<=Math.max(a,b);i++)selected.add(ids[i])}
    else selected.add(id);
  }else{selected.has(id)?selected.delete(id):selected.add(id)}
  lastSelectedId=id;setSelectMode(true);paintSelection();
}
function visibleFollowIds(){return [...document.querySelectorAll('.followlist > .followitem[data-follow-item]')]
  .map(card=>+card.dataset.followItem)}
function toggleFollowSelection(id,range=false){
  if(range&&followLastSelectedId!=null){const ids=visibleFollowIds(),a=ids.indexOf(followLastSelectedId),b=ids.indexOf(id);
    if(a>=0&&b>=0){for(let i=Math.min(a,b);i<=Math.max(a,b);i++)followSelected.add(ids[i])}
    else followSelected.add(id);
  }else{followSelected.has(id)?followSelected.delete(id):followSelected.add(id)}
  followLastSelectedId=id;setSelectMode(true);paintSelection();
}
$('#selectMode').onclick=()=>setSelectMode(!selectMode,!selectMode?false:true);
$('#batchClear').onclick=()=>setSelectMode(false,true);
$('#followBatchAll').onclick=()=>{visibleFollowIds().forEach(id=>followSelected.add(id));setSelectMode(true);paintSelection()};
$('#batchbar').querySelectorAll('[data-batch]').forEach(button=>button.onclick=async()=>{
  const labels={like:'喜欢',seen:'标为看过',later:'加入稍后看',dispose:'加入回收站',restore:'还原',delete:'彻底删除'};
  const operation=button.dataset.batch,ids=[...selected];if(!ids.length)return;
  if(!confirm(`确认对 ${ids.length} 个资源执行“${labels[operation]}”？\n${operation==='delete'?'此操作会永久删除文件和账本记录，不可恢复。':'回收站中的文件仍保留，可从回收站入口永久清除。'}`))return;
  button.disabled=true;
  try{const r=await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation})});
    if(r.blocked&&r.blocked.length)alert(`已永久删除 ${r.purged} 个；${r.blocked.length} 个删不掉，仍留在回收站：\n`
      +r.blocked.slice(0,5).map(x=>`${x.path}（${x.reason}）`).join('\n'));
    setSelectMode(false,true);await reloadCurrentSurface()}
  catch(error){alert(`操作失败：${error.message||'未知错误'}`)}
  finally{button.disabled=false;paintSelection()}
});
$('#batchbar').querySelectorAll('[data-follow-batch]').forEach(button=>button.onclick=async()=>{
  const action=button.dataset.followBatch,items=[...followSelected];if(!items.length)return;
  const labels={save:'保存到账本',seen:'标记已看',ignored:'忽略'};
  if(!confirm(`确认对 ${items.length} 个关注作品执行“${labels[action]}”？`))return;
  button.disabled=true;
  try{
    const path=action==='save'?'/api/follow/save':'/api/follow/status';
    const body=action==='save'?{items}:{items,to:action};
    await api(path,{method:'POST',body:JSON.stringify(body)});
    setSelectMode(false,true);await openFollow(false);
  }catch(error){alert(`操作失败：${error.message||'未知错误'}`)}
  finally{button.disabled=false;paintSelection()}
});
$('#batchbar').querySelectorAll('[data-junk-batch]').forEach(button=>button.onclick=async()=>{
  const operation=button.dataset.junkBatch,ids=[...selected];if(!ids.length)return;
  const labels={'dismiss-junk':'不是垃圾','reconsider-junk':'重新判断',dispose:'移入回收站'};
  if(!confirm(`确认把 ${ids.length} 个垃圾文件候选“${labels[operation]}”？`))return;
  button.disabled=true;
  try{
    await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation})});
    setSelectMode(false,true);adsBatch=null;await load(true);
    toast(`已批量${labels[operation]}：${ids.length} 项`);
  }catch(error){toast(`批量操作失败：${error.message||'未知错误'}`,{warn:true})}
  finally{button.disabled=false;paintSelection()}
});

/* 密度：大图为主，密集为辅 */
const TILES={big:'336px',dense:'168px'};   /* 168px 模块单位 */
let density=localStorage.getItem('density')||'big';
function applyDensity(){document.documentElement.style.setProperty('--tile',TILES[density]);
  document.body.dataset.density=density;
  $('#density').setAttribute('aria-pressed',density==='dense');
  $('#density').title='当前：'+(density==='big'?'大图':'密集')}
$('#density').onclick=()=>{density=density==='big'?'dense':'big';
  localStorage.setItem('density',density);applyDensity()};
applyDensity();

/* ── 悬停预览：只有本地文件拉真视频。
   115 / PikPak 等远端源只扫本地接触印相，避免页面移除后继续下载或填满缓存。 ── */
const POS=[[0,0],[50,0],[100,0],[0,50],[50,50],[100,50],[0,100],[50,100],[100,100]];
function releaseHoverPreviews(root=document,except=null){
  if(!root||!root.querySelectorAll)return;
  root.querySelectorAll('.card').forEach(card=>{
    if(card!==except&&card._stopHover)card._stopHover()});
  root.querySelectorAll('video.hv').forEach(v=>{
    if(v.closest('.card')===except)return;
    if(v._hop)clearInterval(v._hop);v.pause();v.removeAttribute('src');v.load();v.remove()});
}
function wireHover(el,it){
  const pic=el.querySelector('.pic'); if(!pic)return;
  el.dataset.hoverMode=it.location==='local'?'video':'frames';
  let longTimer=null;
  const armLong=()=>{clearTimeout(longTimer);el.classList.add('previewing');longTimer=setTimeout(()=>el.classList.add('longhover'),Math.max(1,appSettings.hoverDelaySeconds)*1000)};
  const clearLong=()=>{clearTimeout(longTimer);el.classList.remove('previewing','longhover')};
  if(it.location!=='local'){        // 远端源：只换预览图逐格扫视，零网络流量
    // 只扫接触印相的格子。封面图也带 .poster 类（为了共用尺寸样式），
    // 不排掉的话 hover 会把它的 src 改写成 /poster?id=，封面当场被换掉。
    const im=pic.querySelector('.poster:not(.cover)'); if(!im)return;
    let t=null,i=4;
    el.addEventListener('mouseenter',()=>{if(selectMode||censorOn())return;armLong();t=setInterval(()=>{
      i=(i+1)%9; im.src=`/poster?id=${it.id}&c=${i}`},430)});
    const stop=()=>{clearLong();clearInterval(t);t=null;im.src=`/poster?id=${it.id}&c=4`};
    el._stopHover=stop;el.addEventListener('mouseleave',stop);
    return;
  }
  let timer=null,v=null;
  el.addEventListener('mouseenter',()=>{
    if(selectMode||censorOn()||window.__scrolling)return;   // 多选、遮挡或滚动中不启动预览
    timer=setTimeout(()=>{
      if(window.__scrolling||censorOn())return;
      releaseHoverPreviews(document,el);   // 同一时间只保留一个本地视频预览
      v=document.createElement('video');
      v.className='hv'; v.muted=true; v.playsInline=true; v.loop=true; v.preload='metadata';
      v.src='/stream?id='+it.id;
      // 分段跳跃：每段放 1.4 秒就跳到下一段，扫完全片，而不是从一个点连续播
      const SEG=[0.08,0.22,0.36,0.50,0.64,0.78,0.90]; let si=0, hop=null;
      const seek=()=>{try{v.currentTime=(v.duration||0)*SEG[si]}catch(e){}};
      v.addEventListener('loadedmetadata',()=>{
        seek(); v.classList.add('on');armLong();
        hop=setInterval(()=>{si=(si+1)%SEG.length;seek()},1400);
        v._hop=hop;
      },{once:true});
      pic.appendChild(v); v.play().catch(()=>{});
    },340);                         // 340ms 防抖，鼠标划过不触发
  });
  const stop=()=>{
    clearLong();
    clearTimeout(timer);timer=null;
    if(v){if(v._hop)clearInterval(v._hop);v.pause();v.removeAttribute('src');v.load();v.remove();v=null}
  };
  el._stopHover=stop;el.addEventListener('mouseleave',stop);
}
window.addEventListener('pagehide',()=>releaseHoverPreviews());
document.addEventListener('visibilitychange',()=>{if(document.hidden)releaseHoverPreviews()});

/* 头像内层：先垫首字母，再叠真实图。规范实体图优先，取不到才回落到旧头像缓存。 */
function avatarInner(name,ref,repId,kind='performer'){
  const src=ref?`/entity-image?kind=${kind}&id=${ref.id}`:(repId?`/avatar?id=${repId}`:'');
  // 兜底链最后一环必须是 remove()：留着取不到图的 <img>，`:has(img)` 仍然匹配，
  // 首字母垫底回不来，浏览器还会把 alt 画出来。onerror=null 只是不再重试。
  const fallback=ref&&repId
    ?`if(!this.dataset.f){this.dataset.f='1';this.src='/avatar?id=${repId}'}else{this.remove()}`
    :`this.remove()`;
  return `<span class="ini">${esc((name||'?').slice(0,1))}</span>`+
    (src?`<img src="${src}" alt="" loading="lazy" onerror="${fallback}">`:'');
}
/* 人脸取景：资料页圆框按检出的人脸中心取景（/api/entity 的 avatar_focus）。
   没检出或没算过返回空串维持几何居中；换回落图时必须撤掉——那是另一张照片，
   脸不在同一位置，见 entityhero img 的 onerror。 */
function facePos(f){
  return f&&f.axis==='x'?` style="object-position:${f.pct}% 50%"`
    :f&&f.axis==='y'?` style="object-position:50% ${f.pct}%"`
    :'';
}
/* 官方封套有两种形态，实测过：整张封套约 1.48（左侧是剧照拼贴，右侧才是正封），
   竖版正封约 0.70（本身就是正封，没有左半边可裁）。所以取景不能写死「取右边」，
   得等图片加载后按它自己的宽高比分流——服务端没存这个比例，也不该为此再存一份。 */
const COVER_FRAME=`onload="const r=this.naturalWidth/this.naturalHeight;this.dataset.frame=r>1.2?'sleeve':'front'"`;
/* 整张封套里右侧正封占的宽高比。裁切靠的是容器比例而不是 CSS 裁剪：`object-fit:cover`
   只在容器比图片更「竖」时才会横向裁，容器一旦宽过 1.48 就变成纵向裁、整张封套原样
   铺满——这正是「大图」以前只是撑满画布、没取到右侧的原因。 */
const COVER_FRONT_RATIO=0.7;
/* 竖屏一律用同一个比例，不按每条视频的实际宽高。竖屏素材从 0.5 到 0.9 都有，
   按各自比例渲染会让竖屏条和竖屏网格高低不齐；比例不同的用 contain 上下留黑边
   （`.poster` 本来就是 contain + 黑底）。 */
const PORTRAIT_RATIO=9/16;
function coverImage(it,layout){
  const src=`/cover?code=${encodeURIComponent(it.code||'')}`;
  // 人脸只做纵向微调：人物在画面里的高低差别很大，写死的纵向位置会把一部分
  // 作品裁掉下巴或留出大片空白。检出率约 48%，取不到就退回固定值。
  const cy=it.cover_frame&&it.cover_frame.cy;
  const y=cy!=null?`--cover-y:${Math.round(Math.min(0.6,Math.max(0.05,cy))*100)}%`:'';
  // 小图看整张（含剧照拼贴），大图只取右侧正封。
  return `<img class="poster cover ${layout==='small'?'whole':'front'}" src="${src}"
    alt="" loading="lazy"${y?` style="${y}"`:''} ${COVER_FRAME} onerror="this.remove()">`;
}
function cardHtml(it,cls){
  /* 资料页可能同时收录番号和非番号作品；版式按钮属于页面，但封套比例只施加给
     真实 `is_jav` 卡片，不能把同页的创作者视频也拉成竖封。 */
  const jav=javActive()&&!!it.is_jav,layout=javLayout();
  const parts=it.part_group||null;
  const useCover=jav&&layout!=='preview'&&it.has_cover;
  /* 卡片比例。这个值以前算出来就没人用过——`.pic` 一直写死 16/9，于是 JAV 的两种
     版式看起来一模一样。现在写进 `--card-ratio`，由 CSS 消费。 */
  /* 一个列表里所有卡片必须同高，比例只能由**列表的语境**决定，不能由单条媒体决定。
     按 `it.ctx_orient` 逐条算的话，任何混着横屏和竖屏的网格都会高低不齐——资料页、
     相关推荐、搜索结果全中招。竖屏比例只留给两种整列都是竖屏的场合：竖屏条，
     以及用户显式筛了竖屏的时候。比例对不上的用 contain 上下留黑边。 */
  const portrait=cls==='scard'||state.orient==='竖屏';
  const ar=portrait
    ? PORTRAIT_RATIO
    /* 大图只留右侧正封，宽度不变、高度拉长；小图和预览图保持 16:9。
       没有封面的那些也跟着拉长：一行里高矮混排同样会把网格撕成锯齿状，
       缺封面的用 16:9 预览图上下留黑边即可（`.poster` 本来就是 contain + 黑底）。 */
    : (jav&&layout==='big'?COVER_FRONT_RATIO:16/9);

  const thumb=useCover
    ? coverImage(it,layout)
    : (it.has_thumb
      ? `<img class="poster" src="/poster?id=${it.id}&c=4" alt="" loading="lazy">`
      : `<span class="nopic">无预览</span>`);
  const fl=[it.feedback==='dislike'&&'dislike',it.feedback==='seen'&&'seen',
            it.disposal==='trash'&&'dispose',it.watch_later&&'later']
            .filter(Boolean).map(c=>`<i class="${c}"></i>`).join('');
  const performers=it.performers||[];
  const performerRefs=it.performer_entities||[];
  const performerTotal=it.performer_total||performers.length;
  const performer=performers[0]||'';
  const performerRef=performerRefs[0];
  // 番号旧投影常把女优罗马字同时塞进 `asset.creator`。规范 performer 实体已经
  // 本地化时，不能再让旧扁平字段抢走卡片署名和链接；非番号创作者作品仍优先 creator。
  const primaryCreator=it.is_jav&&performer?'':it.creator;
  const identity=primaryCreator?{kind:'creator',name:primaryCreator}
    :(performer?{kind:'performer',name:performer}
      :(it.code?{kind:'',name:it.code}
        :(it.studio?{kind:'studio',name:it.studio}:{kind:'',name:'未归属'})));
  const who=identity.name,whoKind=identity.kind;
  const shownName=parts?.title||it.name;
  const shownSize=parts?.total_size??it.size;
  const shownDuration=parts?.total_duration??it.duration;
  const watchedRatio=!parts&&Number(it.play_seconds)>0&&Number(it.duration)>0
    ? Math.min(Number(it.play_seconds)/Number(it.duration),1):0;
  const tr=watchedRatio>0
    ? `<div class="watchprogress" role="progressbar" aria-label="观看进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(watchedRatio*100)}"><i style="width:${(watchedRatio*100).toFixed(1)}%"></i></div>`
    : (it.leave_ratio!=null?`<div class="scrub"><i style="width:${Math.round(it.leave_ratio*100)}%"></i></div>`:'');
  const sizeText=Number(shownSize)>0?fmtSize(Number(shownSize)):'大小未知';
  const tgs=(it.tags||[]).slice(0,3).map(x=>`<span class="tg general" data-tag="${esc(x)}">${esc(tagLabel(x))}</span>`).join('');
  // 共演作品用头像提示多人，但文字只保留第一位，再给总人数。两个长名字加元数据
  // 会在普通卡片里折成三行；「第一位 + 等 N 人」仍能说明身份与规模。
  const coStarred=performers.length>1&&!primaryCreator;
  const avatar=coStarred
    ? `<div class="mavstack">${performers.slice(0,3)
        .map((nm,i)=>`<button class="mav entitylink" data-entity-kind="performer" data-entity-name="${esc(nm)}" title="打开${esc(performerLabel(it))}页：${esc(nm)}">${avatarInner(nm,performerRefs[i],REP[nm])}</button>`)
        .join('')}</div>`
    : (()=>{
        /* 头像和名字必须落到同一个身份。原来头像先看 performer、名字先看 creator，
           碰上同名的 creator/performer 重复实体（账本里有 35 组）就会一个跳
           `/performers/x`、另一个跳 `/creators/x`，同一张卡上两个入口去两个地方。 */
        const avatarKind=identity.kind||(performer?'performer':(primaryCreator?'creator':(it.studio?'studio':'')));
        const avatarName=identity.kind?identity.name:(performer||primaryCreator||it.studio||who);
        const inner=avatarInner(avatarName,performerRef,REP[avatarName]||REP[it.creator]||REP[it.studio]);
        return avatarKind
          ? `<button class="mav entitylink" data-entity-kind="${avatarKind}" data-entity-name="${esc(avatarName)}" title="打开${avatarKind==='performer'?esc(performerLabel(it)):'资料'}页">${inner}</button>`
          : `<span class="mav">${inner}</span>`;
      })();
  const whoHtml=coStarred
    ? `<button class="who entitylink" data-entity-kind="performer" data-entity-name="${esc(performer)}">${esc(performer)}</button>`
      +`<span class="whomore">等 ${performerTotal} 人</span>`
    : (whoKind?`<button class="who entitylink" data-entity-kind="${whoKind}" data-entity-name="${esc(who)}">${esc(who)}</button>`:`<span class="who">${esc(who)}</span>`);
  const tools=`<button class="previewcounter" data-open title="打开预览" aria-label="打开预览">
      <svg viewBox="-18 -18 36 36"><circle r="17"></circle><circle r="17"></circle></svg>${icon('play','ringplay')}</button>
    <div class="hovertools later-tools"><button class="laterbtn" data-later aria-pressed="${!!it.watch_later}" title="稍后看" aria-label="稍后看">
      ${it.watch_later?icon('check'):icon('bookmark-plus')}</button></div>
    <div class="hovertools seektools">
      <button data-seek="-${appSettings.seekSeconds}" title="后退 ${appSettings.seekSeconds} 秒" aria-label="后退 ${appSettings.seekSeconds} 秒">${icon('rotate-ccw')}<b>${appSettings.seekSeconds}</b></button>
      <button data-seek="${appSettings.seekSeconds}" title="前进 ${appSettings.seekSeconds} 秒" aria-label="前进 ${appSettings.seekSeconds} 秒">${icon('rotate-cw')}<b>${appSettings.seekSeconds}</b></button>
      <button data-open title="打开详情" aria-label="打开详情">${icon('maximize')}</button></div>`;
  /* 小图与预览图都是 16:9 横图，只更换图片来源；元数据 DOM 和高度必须完全相同。 */
  return `<article class="card ${parts?'partcard ':''}${cls||''} ${it.disposal==='trash'?'pending-delete':''}" data-id="${it.id}"${parts?` data-part-seed="${parts.seed_id}"`:''}>
    ${parts?'<div class="partstack">':''}<div class="pic" style="--card-ratio:${ar}">${thumb}<button class="cardopenhit" data-open aria-label="打开 ${esc(shownName)}${parts?'分卷':'详情'}"></button>
      <div class="badge mono">${srcBadge(it.location,it.cost)}</div>
      <span class="selectionMark">${icon('check')}</span><span class="deleteMark">${icon('trash')}<b>回收站</b></span>
      ${parts?`<span class="partbadge">${parts.count} 卷</span>`:''}<span class="dur mono">${fmtDur(shownDuration)}</span>${tr}${tools}</div>${parts?'</div>':''}
    <div class="meta">${avatar}<div class="mtext"><button class="t cardtitle" data-open>${esc(shownName)}</button>
      <div class="s mono">${whoHtml}
        ${it.why?`<span class="why">${esc(it.why)}</span>`:''}
        <span class="size">${sizeText}</span>
        ${it.play_count?`<span class="watchcount">看过 ${it.play_count}</span>`:''}
        <span class="flags">${fl}</span></div>
      ${tgs?`<div class="ctags">${tgs}</div>`:''}</div></div></article>`;
}
const RESOURCE_MEDIUM_LABEL={image:'图片',audio:'音频',archive:'压缩包',other:'其它文件'};
function resourceCardHtml(it){
  if(!it.medium||it.medium==='video')return cardHtml(it);
  const image=it.medium==='image'&&it.location!=='online';
  const label=(String(it.name||'').toLowerCase().endsWith('.url')?'网址快捷方式'
    :RESOURCE_MEDIUM_LABEL[it.medium]||'其它文件');
  const glyph=image?'pics':label==='网址快捷方式'?'globe':'hard-drive';
  const action=it.disposal==='trash'?'restore':'dispose';
  const actionLabel=action==='restore'?'还原':'移入回收站';
  return `<article class="card resourcecard ${it.disposal==='trash'?'pending-delete':''}" data-id="${it.id}" data-medium="${esc(it.medium||'other')}">
    <div class="pic" style="--card-ratio:16/9"><span class="resourceglyph">${icon(glyph)}<b>${esc(label)}</b></span>
      ${image?`<img class="poster" src="/photo-thumb?id=${it.id}" alt="" loading="lazy" onerror="this.remove()">`:''}
      <div class="badge mono">${srcBadge(it.location,it.cost)}</div>
      <span class="selectionMark">${icon('check')}</span><span class="deleteMark">${icon('trash')}<b>回收站</b></span>
      <button class="resourcecardaction" type="button" data-resource-operation="${action}" aria-label="${actionLabel} ${esc(it.name||'')}" title="${actionLabel}">${icon(action==='restore'?'rotate-ccw':'trash')}<span>${actionLabel}</span></button></div>
    <div class="meta"><span class="mav resourcekind" aria-hidden="true">${icon(glyph)}</span><div class="mtext">
      <span class="t resourcecardtitle" data-middle-truncate title="${esc(it.name||'')}">${esc(it.name||'未命名资源')}</span>
      <div class="s mono"><span class="who">${esc(label)}</span>${it.why?`<span class="why">${esc(it.why)}</span>`:''}<span class="size">${Number(it.size)>0?fmtSize(Number(it.size)):'大小未知'}</span></div>
    </div></div></article>`;
}
const JUNK_KIND_META={
  video:['视频','play'],image:['图片','pics'],archive:['压缩包','folder-open'],
  audio:['音频','volume-2'],url:['网址快捷方式','globe'],other:['其它文件','hard-drive'],
};
function junkCardHtml(it){
  const kind=it.junk_kind||'other',meta=JUNK_KIND_META[kind]||JUNK_KIND_META.other;
  const preview=kind==='video'
    ? `<img class="poster" src="/thumb?id=${it.id}&c=4" width="640" height="360" alt="" loading="lazy" onerror="this.remove()">`
    : kind==='image'
      ? `<img class="poster" src="/photo-thumb?id=${it.id}" width="640" height="360" alt="" loading="lazy" onerror="this.remove()">`:'';
  const decision=junkView==='dismissed'
    ? ['reconsider-junk','重新判断','rotate-ccw']
    : ['dismiss-junk','不是垃圾','check'];
  const canOpen=kind==='video'||kind==='image';
  return `<article class="card junkcard" data-id="${it.id}" data-junk-kind="${esc(kind)}">
    <div class="pic" style="--card-ratio:16/9"><span class="resourceglyph">${icon(meta[1])}<b>${esc(meta[0])}</b></span>${preview}
      <div class="badge mono">${srcBadge(it.location,it.cost)}</div><span class="selectionMark">${icon('check')}</span></div>
    <div class="junkbody"><div class="junkmeta">
      ${canOpen?`<button class="t junkcardtitle" type="button" data-junk-open data-middle-truncate title="${esc(it.name||'')}">${esc(it.name||'未命名资源')}</button>`
        :`<span class="t junkcardtitle" data-middle-truncate title="${esc(it.name||'')}">${esc(it.name||'未命名资源')}</span>`}
      <div class="s mono"><span class="who">${esc(meta[0])}</span>${it.why?`<span class="why">${esc(it.why)}</span>`:''}<span class="size">${Number(it.size)>0?fmtSize(Number(it.size)):'大小未知'}</span></div>
    </div><footer class="junkactions">
      <button type="button" data-junk-operation="${decision[0]}" title="${esc(decision[1])}" aria-label="${esc(decision[1])}">${icon(decision[2])}<span>${decision[1]}</span></button>
      <button type="button" class="junktrash" data-junk-operation="dispose" title="移入回收站" aria-label="移入回收站">${icon('trash')}<span>移入回收站</span></button>
    </footer></div></article>`;
}
async function runJunkOperation(id,operation){
  await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[id],operation})});
  adsBatch=null;await load(true);
}
function wireJunkCards(root){
  root.querySelectorAll('.junkcard').forEach(card=>{
    const id=+card.dataset.id,item=CACHE[id];
    card.onclick=event=>{
      if(event.target.closest('[data-junk-operation]'))return;
      if(selectMode||event.shiftKey||event.ctrlKey||event.metaKey){
        event.preventDefault();event.stopPropagation();toggleSelection(id,event.shiftKey);
      }
    };
    card.querySelector('[data-junk-open]')?.addEventListener('click',event=>{
      event.stopPropagation();
      if(selectMode||event.shiftKey||event.ctrlKey||event.metaKey){
        event.preventDefault();toggleSelection(id,event.shiftKey);return
      }
      if(item?.junk_kind==='image')window.open('/photo?id='+id,'_blank','noopener');
      else openItem(id,true,null,card);
    });
    card.querySelectorAll('[data-junk-operation]').forEach(button=>button.onclick=async event=>{
      event.preventDefault();event.stopPropagation();
      const operation=button.dataset.junkOperation;
      button.disabled=true;button.setAttribute('aria-busy','true');
      try{
        await runJunkOperation(id,operation);
        const disposed=operation==='dispose',reconsidered=operation==='reconsider-junk';
        toast(disposed?'已移入回收站':reconsidered?'已重新加入垃圾判断':'已标记为不是垃圾',{
          action:{label:'撤销',run:()=>runJunkOperation(id,disposed?'restore':reconsidered?'dismiss-junk':'reconsider-junk')},
        });
      }catch(error){
        toast(`操作失败：${esc(error.message||'未知错误')}`,{warn:true});
        button.disabled=false;button.removeAttribute('aria-busy');
      }
    });
  });
}
function renderJunkNavigation(data){
  const countFor=key=>key?Number(data.counts?.[key]||0):Number(data.all_total||0);
  const categoryLinks=JUNK_KIND_OPTIONS.map(([key,label,glyph])=>{
    const current=key===junkKind;
    return `<a href="${junkPath(key,junkView)}" data-junk-kind-link="${esc(key)}"${current?' aria-current="page"':''}>${icon(glyph)}${esc(label)} <span>${countFor(key).toLocaleString()}</span></a>`;
  }).join('');
  $('#count').removeAttribute('aria-busy');
  $('#count').innerHTML=`<div class="junksummary" aria-live="polite">显示 ${Number(data.total||0).toLocaleString()} 个</div>
    <nav class="junkfilters" aria-label="垃圾文件分类">${categoryLinks}<i aria-hidden="true"></i>
      <a href="${junkPath('',junkView==='dismissed'?'pending':'dismissed')}" data-junk-view-link="${junkView==='dismissed'?'pending':'dismissed'}"${junkView==='dismissed'?' aria-current="page"':''}>${icon(junkView==='dismissed'?'rotate-ccw':'eye-off')}${junkView==='dismissed'?'返回待判断':'已排除'} <span>${Number(data.dismissed_total||0).toLocaleString()}</span></a>
    </nav>`;
  $('#count').querySelectorAll('[data-junk-kind-link],[data-junk-view-link]').forEach(link=>link.onclick=event=>{
    if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    event.preventDefault();
    if(selectMode)setSelectMode(false,true);
    if(link.hasAttribute('data-junk-kind-link'))junkKind=cleanJunkKind(link.dataset.junkKindLink||'');
    if(link.dataset.junkViewLink)junkView=link.dataset.junkViewLink;
    adsBatch=null;route(junkPath());load(true);
  });
}
function openResourceCard(id,anchor=null){
  const item=CACHE[id];
  if(!item||!item.medium||item.medium==='video'){openItem(id,true,null,anchor);return}
  if(item.medium==='image'&&item.location!=='online'){
    window.open('/photo?id='+id,'_blank','noopener');return
  }
  toggleSelection(id);
}
function wireResourceCardActions(root){
  root.querySelectorAll('[data-resource-operation]').forEach(button=>{
    if(button.dataset.wired)return;button.dataset.wired='1';
    button.onclick=async event=>{
      event.preventDefault();event.stopPropagation();
      const card=button.closest('[data-id]'),operation=button.dataset.resourceOperation;
      if(!card)return;
      button.disabled=true;button.setAttribute('aria-busy','true');
      button.innerHTML=`${spinnerHtml(operation==='restore'?'正在还原':'正在移入回收站')}<span>${operation==='restore'?'正在还原':'正在处理'}</span>`;
      try{
        await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[+card.dataset.id],operation})});
        await load(true);
      }catch(error){
        alert(`操作失败：${error.message||'未知错误'}`);
        button.disabled=false;button.removeAttribute('aria-busy');
        const label=operation==='restore'?'还原':'移入回收站';
        button.innerHTML=`${icon(operation==='restore'?'rotate-ccw':'trash')}<span>${label}</span>`;
      }
    };
  });
}
function mixLabel(it){
  const performer=(it.performers||[])[0];
  return (it.is_jav&&performer?performer:it.creator)||performer||it.studio||it.code||tagLabel((it.tags||[])[0])||'为你推荐';
}
function mixCardHtml(it){
  const jav=javActive()&&!!it.is_jav,layout=javLayout();
  const useCover=jav&&layout!=='preview'&&it.has_cover;
  const ar=jav&&layout==='big'?COVER_FRONT_RATIO:16/9;
  const thumb=useCover
    ? coverImage(it,layout)
    : (it.has_thumb
      ? `<img class="poster" src="/poster?id=${it.id}&c=4" alt="" loading="lazy">`
      : `<span class="nopic">无预览</span>`);
  const label=mixLabel(it);
  return `<article class="card mixcard" data-mix-seed="${it.id}">
    <div class="mixstack"><div class="pic" style="--card-ratio:${ar}">${thumb}<button class="cardopenhit" data-open-mix aria-label="打开 Mix · ${esc(label)}"></button>
      <span class="mixbadge">${icon('play')}Mix</span></div></div>
    <div class="mixmeta"><span class="mixglyph">${icon('play')}</span><div class="mixcopy">
      <b>Mix · ${esc(label)}</b><span>${esc(it.name)}及相似作品</span></div></div></article>`;
}
let renderedPartGroups=new Set();
function collapseMultipartItems(items){
  return items.filter(it=>{
    const key=it.part_group?.key;
    if(!key)return true;
    if(renderedPartGroups.has(key))return false;
    renderedPartGroups.add(key);return true;
  });
}
function batchWithMix(items,enabled=true){
  const visible=collapseMultipartItems(items);
  const cards=visible.map(it=>cardHtml(it));
  if(!enabled)return cards.join('');
  const seed=visible.find(it=>it.creator||(it.performers||[]).length||it.studio)||visible[0];
  if(seed&&visible.length>=8)cards.splice(7,0,mixCardHtml(seed));
  return cards.join('');
}
function wireMixCards(root){
  root.querySelectorAll('[data-mix-seed]').forEach(el=>{
    if(el.dataset.wired)return;el.dataset.wired='1';
    el.onclick=()=>openMix(+el.dataset.mixSeed,+el.dataset.mixSeed,true,el);
  });
}
function wireCards(root,onClick,onTag){
  root.querySelectorAll('[data-id]').forEach(el=>{
    if(el.dataset.wired)return; el.dataset.wired='1';
    const it=CACHE[el.dataset.id];
    const openCard=(id,anchor=el)=>onClick?onClick(id,anchor):(it?.part_group
      ?openParts(it.part_group.seed_id,id,true,anchor):openItem(id,true,null,anchor));
    el.onclick=e=>{
      const seek=e.target.closest('[data-seek]');
      if(seek){e.stopPropagation();const v=el.querySelector('video.hv');
        if(v&&Number.isFinite(v.duration)){if(v._hop){clearInterval(v._hop);v._hop=null}
          v.currentTime=Math.max(0,Math.min(v.duration,v.currentTime+(+seek.dataset.seek)))}return}
      const later=e.target.closest('[data-later]');
      if(later){e.stopPropagation();api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})})
        .then(r=>{it.watch_later=r.watch_later;later.setAttribute('aria-pressed',r.watch_later);
          later.innerHTML=r.watch_later?icon('check'):icon('bookmark-plus')});return}
      if(selectMode||e.shiftKey||e.ctrlKey||e.metaKey){e.preventDefault();e.stopPropagation();toggleSelection(it.id,e.shiftKey);return}
      if(e.target.closest('[data-open]')){e.stopPropagation();openCard(+el.dataset.id,el);return}
      const ent=e.target.closest('[data-entity-kind]');
      if(ent){e.stopPropagation();openEntity(ent.dataset.entityKind,ent.dataset.entityName);return}
      const tg=e.target.closest('.tg');
      if(tg){e.stopPropagation();if(onTag){onTag(tg.dataset.tag);return}
        state.tag=tg.dataset.tag;buildBars();load(true);
        window.scrollTo({top:0,behavior:'smooth'});return}
      if(e.shiftKey||e.ctrlKey||e.metaKey||selectMode){e.preventDefault();toggleSelection(it.id,e.shiftKey);return}
      openCard(+el.dataset.id,el);
    };
    el.querySelectorAll('[data-open]').forEach(opener=>{
      opener.dataset.openWired='1';
      opener.onclick=e=>{e.stopPropagation();if(selectMode||e.shiftKey||e.ctrlKey||e.metaKey){e.preventDefault();toggleSelection(it.id,e.shiftKey);return}openCard(+el.dataset.id,el)};
    });
    if(it&&(!it.medium||it.medium==='video'))wireHover(el,it);
  });
}

/* ── 顶部标签条 + 抽屉 ── */
let barsRequestSeq=0,barsDataCache=null,barsDataAt=0,barsDataPromise=null;
let barsDataScope='';
async function getBarsData(context=barsContext){
  // JAV 模式的顶部三层与筛选面板要跟着收窄，否则会列出只出现在创作者作品里的
  // 女优和厂牌，点进去却是空的。口径变了必须丢缓存，不能沿用上一套。
  const facetParams=new URLSearchParams();
  if(javActive())facetParams.set('jav','1');
  if(context.type==='entity'){
    facetParams.set('scope_kind',context.kind);facetParams.set('scope_name',context.name)
  }else if(context.type==='item')facetParams.set('id',String(context.id));
  // 已标记/稍后看这类状态页也是一个更窄的集合。不传的话，上面那排头像和
  // 标签条走的是全库口径，列出来的人和标签在本页一个作品都没有。
  if(context.type==='home'&&state.state)facetParams.set('state',state.state);
  const scope=facetParams.toString();
  if(scope!==barsDataScope){barsDataCache=null;barsDataPromise=null;barsDataScope=scope}
  if(barsDataCache&&Date.now()-barsDataAt<30000)return barsDataCache;
  const topsParams=new URLSearchParams({n:'30',seed:state.seed||''});
  if(javActive())topsParams.set('jav','1');
  if(context.type==='home'&&state.state)topsParams.set('state',state.state);
  // 顶部三层跟着「换一批」的同一个种子走，刷新后才真的换人。
  if(!barsDataPromise)barsDataPromise=Promise.all([
      api('/api/facets'+(scope?'?'+scope:'')),
      api('/api/tops?'+topsParams)])
    .then(data=>{barsDataCache=data;barsDataAt=Date.now();return data})
    .finally(()=>{barsDataPromise=null});
  return barsDataPromise
}
function commitContextFilter(mutate){
  if(barsContext.type==='entity'){
    const filters={...barsContext.filters};mutate(filters);
    barsContext={...barsContext,filters};
    buildBars();updateEntityCollection(barsContext.kind,barsContext.name,filters,true);return
  }
  if(barsContext.type==='item'){
    const target=cloneBarsContext(detailReturnBarsContext);
    disposeStage(false);detailReturnBarsContext=null;
    if(target&&target.type==='entity'){
      mutate(target.filters);barsContext=target;
      buildBars();updateEntityCollection(target.kind,target.name,target.filters,true);return
    }
    mutate(state);barsContext={type:'home',filters:state};route(homePath());showHomeSurfaces();
    buildBars();load(true);return
  }
  mutate(state);route(homePath());buildBars();load(true)
}
async function buildBars(){
  const requestSeq=++barsRequestSeq;
  const context=barsContext,filterState=activeFilterState();
  // 两个聚合查询互不依赖。冷启动各需约 1 秒，串行会让手机首屏白等；
  // 并行取回后再一次性绘制顶部与抽屉。
  const [facetData,tops]=await getBarsData(context);
  if(requestSeq!==barsRequestSeq)return;
  if(context.type==='home')facets=facetData;
  // 详情抽屉继续只展示当前作品的真实标签；作品没有内容标签时，顶部发现栏
  // 回退到返回首页的推荐口径，避免把全库标签伪装成作品元数据。
  let topTags=facetData.tags||[];
  if(context.type==='item'&&!topTags.length){
    const recommendationParams=new URLSearchParams();
    if(javActive())recommendationParams.set('jav','1');
    if(detailReturnBarsContext?.type==='home'&&state.state)
      recommendationParams.set('state',state.state);
    const recommendationScope=recommendationParams.toString();
    const recommendationFacets=await api('/api/facets'+(recommendationScope?'?'+recommendationScope:''));
    if(requestSeq!==barsRequestSeq)return;
    topTags=recommendationFacets.tags||[]
  }

  // 顶部三层：女优圆头像 / 厂牌 / 内容标签
  tops.performers.forEach(x=>{if(x.rep)REP[x.k]=x.rep});
  tops.studios.forEach(x=>{if(x.rep)REP[x.k]=x.rep});
  const avHtml=x=>`<button class="av" data-entity-kind="performer" data-entity-name="${esc(x.k)}">
    <span class="ring"><span class="ini">${esc(x.k.slice(0,1))}</span>${x.id
      ? `<img src="/entity-image?kind=performer&id=${x.id}" alt="" loading="lazy"
           onerror="this.onerror=null;${x.rep?`this.src='/avatar?id=${x.rep}'`:`this.remove()`}">`
      : ''}</span>
    <span class="nm">${esc(x.k)}</span></button>`;
  // 正规厂牌用官网 logo；缺失时只显示首字母，绝不把作品截图冒充厂牌图标。
  const bpHtml=x=>{
    const fallback=`${esc(x.k.slice(0,2))}`;
    return `<button class="brandpill" data-entity-kind="studio" data-entity-name="${esc(x.k)}">
      <span class="mk" data-fallback="${fallback}"><img src="/logo?studio=${encodeURIComponent(x.k)}" alt=""></span>${esc(x.k)}</button>`;
  };
  // 空的一排仍占 28px，在「已标记」这种窄集合上就是两条什么都没有的空带。
  // 没人就不画那一排，两排都没人就整块收起。
  const perfRow=tops.performers.map(avHtml).join('');
  const studioRow=tops.studios.map(bpHtml).join('');
  const tier=html=>html?`<div class="tier">${html}</div>`:'';
  $('#tiers').innerHTML=tier(perfRow)+tier(studioRow);
  $('#tiers').hidden=!(perfRow||studioRow);
  $('#tiers').querySelectorAll('[data-entity-kind]').forEach(b=>b.onclick=()=>
    openEntity(b.dataset.entityKind,b.dataset.entityName));
  $('#tiers').querySelectorAll('.mk img').forEach(img=>{
    const fallback=()=>{const box=img.parentNode;if(box)box.textContent=box.dataset.fallback||''};
    img.addEventListener('error',fallback,{once:true});
    img.addEventListener('load',()=>{if(img.naturalWidth<32)fallback()},{once:true});
  });

  const views=[{k:'',label:'全部'},{k:'fresh',label:'没看过'},
               {k:'later',label:'稍后看'},{k:'flagged',label:'已标记'}];
  $('#tagbar').innerHTML=
    views.map(v=>`<a class="pill" href="${v.k?STATE_ROUTES[v.k]:'/'}" data-state="${v.k}" aria-pressed="${filterState.state===v.k}">${v.label}</a>`).join('')
    +`<span class="sep"></span>`
    +topTags.slice(0,26).map(t=>
      `<button class="pill" data-tag="${esc(t.k)}" aria-pressed="${
        String(filterState.tag||'').split(',').includes(String(t.k))}">${esc(tagLabel(t.k))}</button>`).join('');
  $('#tagbar').querySelectorAll('[data-state]').forEach(b=>b.onclick=e=>{
    e.preventDefault();state.state=b.dataset.state;route(homePath());buildBars();load(true)});
  $('#tagbar').querySelectorAll('[data-tag]').forEach(b=>b.onclick=()=>{toggleTag(b.dataset.tag)});
  renderCombo(); wireAllDrag();

  const chips=(items,key,multi,limit)=>items.length?`<div class="chips">`+items.slice(0,limit||999).map(it=>{
    const sel=(filterState[key]||'').split(',').filter(Boolean).includes(String(it.k));
    const dot=key==='loc'?(SRCICON[it.k]||`<i class="cost ${it.cost}"></i>`):'';
    // 脱盘的来源留在列表里但不可点：数量还有意义，点进去只会得到一屏放不出的卡片。
    const off=key==='loc'&&sourceOffline(it.k);
    return `<button class="chip${off?' offline':''}" aria-pressed="${sel}" data-key="${key}" data-multi="${multi?1:0}"
      ${off?`disabled title="${OFFLINE_HINT}"`:''}
      data-val="${esc(it.k)}">${dot}${esc(it.label||tagLabel(it.k))}${it.n!=null?`<span class="n">${it.n.toLocaleString()}</span>`:''}</button>`;
  }).join('')+`</div>`:'';
  // 按语义类别区分来源、创作者、内容和技术规格。
  const sec=(t,b,x,cat)=>b?`<div class="sec${cat?' cat-'+cat:''}"><h3>${t}${x||''}</h3>${b}</div>`:'';
  const scopedCreators=context.type==='entity'&&context.kind==='creator'
    ? facetData.creators.filter(item=>item.k!==context.name):facetData.creators;
  // 与窄栏共用 EDGE_ICONS —— 两边条目必须一致，原来抽屉是另一份硬编码
  const navBtn=(k,label,ic)=>`<button data-nav="${k}" draggable="true" aria-pressed="${navOn(k)}">
    ${icon(ic)}<span>${label}</span></button>`;
  $('#drawer').innerHTML=
    `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
      <b class="disp" style="font-size:15px;letter-spacing:.1em">导航与筛选</b>
      <button id="drawerClose" class="ib" title="收起">${icon('x')}</button></div>`+
    `<div class="dnav">${orderedEdgeIcons().map(([k,label,ic])=>navBtn(k,label,ic)).join('')}</div>`+
    sec('来源',chips(facetData.locations.map(l=>({k:l.k,label:LOC[l.k]||l.k,n:l.n,
        cost:(l.k==='pikpak'||l.k==='online')?'metered':'free'})),'loc',true),'','src')
    +sec('时长',facetData.stats.duration?`<div class="duration-filter"><div class="duration-readout"><span id="durMinText">不限</span><b>—</b><span id="durMaxText">不限</span></div>
      <div class="dual-range" id="durationRange"><span class="range-base"></span><span class="range-fill"></span>
        <input id="durMin" type="range" min="0" max="180" step="5" value="${filterState.dur_min?Math.min(180,+filterState.dur_min/60):0}" aria-label="最短时长（分钟）">
        <input id="durMax" type="range" min="0" max="180" step="5" value="${filterState.dur_max?Math.min(180,+filterState.dur_max/60):180}" aria-label="最长时长（分钟）"></div></div>`:'','','meta')
    +sec('画幅',chips(facetData.orientations,'orient'),'','meta')
    +sec('创作者',chips(scopedCreators,'creator',false,26),scopedCreators.length>26?'<button data-more="creator">更多</button>':'','artist')
    +sec('内容标签',chips(facetData.tags,'tag',false,30),facetData.tags.length>30?'<button data-more="tag">更多</button>':'','general')
    +sec('影片属性',chips(facetData.tech,'tag',false,16),'','meta');
  const dc=$('#drawerClose'); if(dc)dc.onclick=()=>openDrawer(false);
  $('#drawer').querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{
    openIndex(b.dataset.page); closeDrawerAfterNav()});
  $('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));
  wireNavigationDrag($('#drawer').querySelector('.dnav'));
  const bind=()=>$('#drawer').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{
    const k=b.dataset.key,v=b.dataset.val;
    commitContextFilter(filters=>{
      if(b.dataset.multi==='1'){const cur=(filters[k]||'').split(',').filter(Boolean);
        const i=cur.indexOf(v);i>=0?cur.splice(i,1):cur.push(v);filters[k]=cur.join(',')}
      else filters[k]=filters[k]===v?'':v
    })});
  bind();
  const durMin=$('#durMin'),durMax=$('#durMax'),durRange=$('#durationRange');
  if(durMin&&durMax&&durRange){
    const syncDuration=(commit=false,changed='')=>{
      let lo=+durMin.value,hi=+durMax.value;
      if(lo>hi){if(changed==='min')hi=lo;else lo=hi;durMin.value=lo;durMax.value=hi}
      durRange.style.setProperty('--lo',(lo/180*100)+'%');durRange.style.setProperty('--hi',(hi/180*100)+'%');
      $('#durMinText').textContent=lo?lo+' 分钟':'不限';$('#durMaxText').textContent=hi<180?hi+' 分钟':'不限';
      if(commit)commitContextFilter(filters=>{
        filters.len='';filters.dur_min=lo?String(lo*60):'';filters.dur_max=hi<180?String(hi*60):''})
    };
    durMin.oninput=()=>syncDuration(false,'min');durMax.oninput=()=>syncDuration(false,'max');
    durMin.onchange=()=>syncDuration(true,'min');durMax.onchange=()=>syncDuration(true,'max');syncDuration();
  }
  $('#drawer').querySelectorAll('[data-more]').forEach(b=>b.onclick=e=>{e.stopPropagation();
    const sec=b.closest('.sec'), k=b.dataset.more;
    const src=k==='tag'?facetData.tags:scopedCreators;
    const lim=k==='tag'?30:26;
    const expanded=b.dataset.on==='1';
    sec.querySelector('.chips').outerHTML=chips(src,k,false,expanded?lim:999);
    b.dataset.on=expanded?'0':'1';
    b.textContent=expanded?'更多':'收起';
    bind();});
}
/* 排序和换批都属于当前列表，放在计数行，不占用全局导航。 */
function renderCount(){
  const n=$('#grid').querySelectorAll(':scope > .card[data-id]').length;   // 竖屏条不计入「显示 N」
  const trash=state.state==='trash';
  if(trash)paintManageLede(`${total.toLocaleString()} 个符合 · 显示 ${n}`);
  $('#count').classList.toggle('count-actions-only',trash);
  $('#count').removeAttribute('aria-busy');
  $('#count').innerHTML=
    (trash?'':`<span class="mono">${total.toLocaleString()} 个符合 · 显示 ${n}</span>`)
    +(trash
      // 回收站是待清理队列，不是浏览列表：换一批和排序在这里没有意义。
      ? (total?`<span class="sorts"><button class="batchaction danger" id="emptyTrash" title="永久删除回收站内容">清空回收站</button></span>`:'')
      : `<span class="sorts"><button class="batchaction" id="batchAction" type="button"
          title="换一批" aria-label="换一批">${icon('refresh-cw')}</button>`
        // JAV 版式紧跟换批动作，和排序连成一条。
        +(javActive()?javLayoutButtons():'')
        +sortOptions().map(([k,l])=>`<button data-sort="${k}" aria-pressed="${state.sort===k}">${l}</button>`).join('')+`</span>`);
  const batch=$('#batchAction');
  if(batch)batch.onclick=async()=>{
    if(batch.getAttribute('aria-busy')==='true')return;
    const old=batch.innerHTML;batch.setAttribute('aria-busy','true');batch.innerHTML=spinnerHtml('换一批');
    try{await refreshAll()}finally{batch.removeAttribute('aria-busy');batch.innerHTML=old}
  };
  wireJavLayoutButtons($('#count'));
  const emptyTrash=$('#emptyTrash');
  if(emptyTrash)emptyTrash.onclick=async(e)=>{
    if(!confirm('永久删除回收站中的全部文件和账本记录？此操作不可恢复。'))return;
    e.currentTarget.disabled=true;
    try{
      const r=await api('/api/trash/empty',{method:'POST'});
      /* 删不掉的文件（占用中、网盘离线）会连同账本行一起留在回收站，必须说出来，
         否则用户看到条目还在会以为清空又没生效。 */
      if(r.blocked&&r.blocked.length)alert(`已永久删除 ${r.purged} 个；${r.blocked.length} 个删不掉，仍留在回收站：\n`
        +r.blocked.slice(0,5).map(x=>`${x.path}（${x.reason}）`).join('\n'));
    }finally{await load(true)}
  };
  $('#count').querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{
    // 再点当前排序就是取消它，回到稳定随机；不能让「最近入库」变成锁死的筛选。
    state.sort=state.sort===b.dataset.sort?'seed':b.dataset.sort;
    load(true)});
}

/* ── 组合筛选：多个标签同时生效 ── */
const tagList=()=>(state.tag||'').split(',').filter(Boolean);
function toggleTag(t){
  if(!t){state.tag='';}
  else{const cur=tagList();const i=cur.indexOf(t);
    i>=0?cur.splice(i,1):cur.push(t);state.tag=cur.join(',')}
  route(homePath());buildBars();load(true);
}
function renderCombo(){
  const cur=tagList(); const extra=[];
  if(state.creator)extra.push(['creator',state.creator]);
  if(state.studio)extra.push(['studio',state.studio]);
  if(!cur.length&&!extra.length){$('#combo').innerHTML='';return}
  $('#combo').innerHTML=
    extra.map(([k,v])=>`<span class="cb">${k==='creator'?'创作者':'厂牌'} ${esc(v)}
      <b data-clear="${k}">✕</b></span>`).join('')
    +cur.map(t=>`<span class="cb">${esc(tagLabel(t))} <b data-untag="${esc(t)}">✕</b></span>`).join('')
    +`<button class="clr" id="clrAll">全部清除</button>`;
  $('#combo').querySelectorAll('[data-untag]').forEach(b=>b.onclick=()=>toggleTag(b.dataset.untag));
  $('#combo').querySelectorAll('[data-clear]').forEach(b=>b.onclick=()=>{
    state[b.dataset.clear]='';buildBars();load(true)});
  $('#clrAll').onclick=()=>{state.tag='';state.creator='';state.studio='';buildBars();load(true)};
}

/* ── 统计与管理 ── */
let adsBatch=null,loadRequestSeq=0,listLoading=false;
function enterManagementSurface(){
  // A catalog request started before browser Back must not repaint filters over
  // the management page after it resolves.
  loadRequestSeq++;listLoading=false;$('#combo').innerHTML='';
  $('#tiers').style.display='none';$('#tagbar').style.display='none';
  document.body.classList.remove('entity-open','index-open');
}
async function openStats(push=true,focusResource=false){
  releaseHoverPreviews();
  if(push)route('/stats');
  const surface=claimSurface('/stats');
  enterManagementSurface();
  disposeStage(false);
  const d=await api('/api/stats');
  if(!surfaceCurrent(surface))return;
  $('#stats').hidden=false; $('#index').hidden=true; $('#grid').innerHTML='';buildManageBar();
  $('#count').textContent=''; $('#loadSentinel').hidden=true; $('#shortsSec').hidden=true;
  $('#tiers').style.display='none'; $('#tagbar').style.display='none';
  const a=d.attribution, cs=d.consumption;
  const pct=(x,y)=>y?Math.round(x/y*100):0;
  const gb=b=>b>=1099511627776?(b/1099511627776).toFixed(2)+' TB':(b/1073741824).toFixed(1)+' GB';
  const hrs=s=>s>=3600?(s/3600).toFixed(1)+' 小时':Math.round(s/60)+' 分钟';
  const totalVideos=d.by_loc.reduce((sum,row)=>sum+row.videos,0);
  const totalBytes=d.by_loc.reduce((sum,row)=>sum+row.bytes,0);
  const coverage=pct(d.tag_cov,a.videos);
  const storage=d.storage_summary||{volumes:0,online:0,measured:0,free:0,used:0,total:0};
  const kv=(k,v,u)=>`<div class="kv"><span>${k}</span><b>${v}${u?`<span class="u">${u}</span>`:''}</b></div>`;
  const metric=(k,v,max)=>`<div class="statmetric">${kv(k,v.toLocaleString(),pct(v,max)+'%')}${progressHtml(`${k}：${v.toLocaleString()} / ${max.toLocaleString()}`,v,max)}</div>`;
  const metricTab=(key,label,value,detail,selected=false)=>`<button type="button" role="tab" data-stats-metric="${key}"
    aria-selected="${selected}" aria-controls="stats-detail-${key}" tabindex="${selected?'0':'-1'}">
    <span>${label}</span><b>${value}</b><small>${detail}</small></button>`;
  const locationRows=d.by_loc.map(row=>{const label=row.k==='online'?'已保存在线':(LOC[row.k]||row.k);return `<div class="insightbarrow"><div><span>${label}</span><b>${row.videos.toLocaleString()}</b></div>
    ${progressHtml(`${label}：${row.videos.toLocaleString()} / ${totalVideos.toLocaleString()}`,row.videos,totalVideos)}
    <small>${gb(row.bytes)} · ${pct(row.videos,totalVideos)}%</small></div>`}).join('');
  const table=(head,rows)=>`<div class="insighttable"><div class="insighttablehead">${head.map(value=>`<span>${value}</span>`).join('')}</div>${rows}</div>`;
  const tagsTable=`<ol class="insightranking">${d.top_tags.map((t,index)=>`<li><button type="button" class="insightrankrow" data-k="${esc(t.k)}">
    <span class="insightrankpos">${index+1}</span><span>${esc(tagLabel(t.k))}</span><b>${t.n.toLocaleString()}</b></button></li>`).join('')}</ol>`;
  const recentTable=table(['作品','观看证据'],d.recent.length?d.recent.map(row=>{
    const real=row.duration?Math.min(row.play_seconds/row.duration,1)*100:0;
    const reached=(row.max_reached||0)*100;
    const note=row.kind==='online'?'在线直接观看':(real<reached-25?'快进扫过':(row.o_count?`高潮 ${row.o_count}`:'正常观看'));
    return `<div class="insighttablerow"><span>${esc((row.creator?row.creator+' · ':'')+row.name)}</span>
      <b>真实 ${real.toFixed(0)}% · 到达 ${reached.toFixed(0)}% · ${note}</b></div>`}).join(''):
    `<div class="insightempty">${emptyStateHtml('history','还没有观看记录','开始播放后，这里会显示最近的真实观看证据。')}</div>`);
  const sourceTable=table(['标签来源','覆盖视频'],d.tag_source.map(row=>`<div class="insighttablerow"><span>${esc(row.k)}</span>
    <b>${row.n.toLocaleString()} 条 · ${row.assets.toLocaleString()} 个视频</b></div>`).join(''));
  const storageTable=`<table class="insightdatatable"><thead><tr><th>位置</th><th>已用</th><th>可用</th><th>使用率</th></tr></thead><tbody>${(d.storage_volumes||[]).map(row=>{
    const measured=row.total!=null, usedPct=measured?pct(row.used,row.total):0;
    return `<tr><th scope="row"><span>${esc(row.label)}</span><small>${row.root?esc(row.root):'未映射'}</small></th><td>${measured?gb(row.used):'—'}</td><td>${measured?gb(row.free):'—'}</td><td>${measured?usedPct+'%':(row.online?'容量未取得':'离线')}</td></tr>`}).join('')}</tbody></table>`;
  $('#stats').innerHTML=`
    <div class="insightpage statsdashboard" data-stats-dashboard>
      <header class="insighttoolbar"><p>账本当前快照 · ${totalVideos.toLocaleString()} 个视频 · ${gb(totalBytes)}</p></header>
      <div class="metricstrip" role="tablist" aria-label="统计视图">
        ${metricTab('inventory','馆藏视频',totalVideos.toLocaleString(),gb(totalBytes),true)}
        ${metricTab('viewing','看过',cs.played.toLocaleString(),hrs(cs.play_seconds))}
        ${metricTab('coverage','内容标签',coverage+'%',`${d.tag_cov.toLocaleString()} / ${a.videos.toLocaleString()}`)}
        ${metricTab('storage','使用空间',`${storage.online} 个卷`,storage.measured?`已用 ${gb(storage.used)}`:'容量未取得')}
      </div>
      <section class="insightdetail">
        <div id="stats-detail-inventory" role="tabpanel" data-stats-detail="inventory" class="insightdetailbody">
          <div class="insightcopy"><span>库存</span><h2>${totalVideos.toLocaleString()}</h2><b>个视频</b>
            <p>按真实挂载位置汇总；体积和视频数使用同一份 ledger 快照。</p></div>
          <div class="insightvisual">${locationRows}</div></div>
        <div id="stats-detail-viewing" role="tabpanel" data-stats-detail="viewing" class="insightdetailbody" hidden>
          <div class="insightcopy"><span>观看</span><h2>${cs.played.toLocaleString()}</h2><b>个作品有播放记录</b>
            <p>累计 ${hrs(cs.play_seconds)}；馆藏播放与关注页直接在线播放都计入，不要求先保存。</p></div>
          <div class="insightfacts">${kv('馆藏观看',cs.library_played.toLocaleString())}${kv('在线直接观看',cs.online_played.toLocaleString())}
            ${kv('高潮计数',cs.o_total.toLocaleString())}${kv('快进扫过',cs.skimmed.toLocaleString())}
            ${kv('明确不喜欢',cs.dislike.toLocaleString())}${kv('看过了',cs.seen.toLocaleString())}${kv('回收站',cs.trash.toLocaleString())}</div></div>
        <div id="stats-detail-coverage" role="tabpanel" data-stats-detail="coverage" class="insightdetailbody" hidden>
          <div class="insightcopy"><span>内容标签覆盖</span><h2>${coverage}%</h2><b>${d.tag_cov.toLocaleString()} / ${a.videos.toLocaleString()}</b>
            <p>归属与加工分别保留真实分母，不用装饰性进度替代缺失数据。</p></div>
          <div class="insightvisual">${metric('有创作者',a.creator,a.videos)}${metric('有番号',a.code,a.videos)}
            ${metric('有厂牌',a.studio,a.videos)}${metric('已抽帧',a.thumb,a.videos)}${metric('已探测时长',a.duration,a.videos)}</div></div>
        <div id="stats-detail-storage" role="tabpanel" data-stats-detail="storage" class="insightdetailbody" hidden>
          <div class="insightcopy"><span>使用空间</span><h2>${storage.measured}</h2><b>个卷已取得容量</b>
            <p>同时统计系统盘、资源盘、115 与 PikPak；离线或未映射的来源明确保留，不伪造为 0。</p></div>
          <div class="insightvisual insightstorage">${storageTable}</div></div>
      </section>
      <section class="insightpanel">
        <header><div class="insighttabs" role="tablist" aria-label="统计维度">
          <button type="button" role="tab" data-stats-tab="tags" aria-selected="true" aria-controls="stats-panel-tags">内容标签</button>
          <button type="button" role="tab" data-stats-tab="recent" aria-selected="false" aria-controls="stats-panel-recent" tabindex="-1">最近看过</button>
          <button type="button" role="tab" data-stats-tab="sources" aria-selected="false" aria-controls="stats-panel-sources" tabindex="-1">标签来源</button>
        </div></header>
        <div class="insightpanelbody"><div id="stats-panel-tags" role="tabpanel" data-stats-panel="tags">${tagsTable}</div>
          <div id="stats-panel-recent" role="tabpanel" data-stats-panel="recent" hidden>${recentTable}</div>
          <div id="stats-panel-sources" role="tabpanel" data-stats-panel="sources" hidden>${sourceTable}</div></div>
      </section>
      ${resourceSyncMarkup()}
    </div>`;
  const statsRoot=$('#stats');
  statsRoot.querySelectorAll('[data-stats-metric]').forEach(button=>button.onclick=()=>{
    statsRoot.querySelectorAll('[data-stats-metric]').forEach(tab=>{
      const selected=tab===button;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1});
    statsRoot.querySelectorAll('[data-stats-detail]').forEach(panel=>panel.hidden=panel.dataset.statsDetail!==button.dataset.statsMetric)
  });
  statsRoot.querySelectorAll('[data-stats-tab]').forEach(button=>button.onclick=()=>{
    statsRoot.querySelectorAll('[data-stats-tab]').forEach(tab=>{
      const selected=tab===button;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1});
    statsRoot.querySelectorAll('[data-stats-panel]').forEach(panel=>panel.hidden=panel.dataset.statsPanel!==button.dataset.statsTab)
  });
  $('#stats').querySelectorAll('[data-k]').forEach(b=>b.onclick=()=>{
    closeStats(); toggleTag(b.dataset.k)});
  await wireResourceSync();
  if(focusResource)$('#resource-sync')?.scrollIntoView({block:'start'});
  else window.scrollTo({top:0,behavior:'smooth'});
}
function showHomeSurfaces(){
  // 两个类都要清：只清 entity-open 会让从索引页回首页时顶栏一直空着，
  // 而且下面那两行 style.display='' 恢复不了被 class 隐藏的元素。
  document.body.classList.remove('entity-open','index-open');
  $('#stats').hidden=true;$('#index').hidden=true;
  $('#tiers').style.display='';$('#tagbar').style.display='';
  buildManageBar();paintListTitle();   // 放在最后：管理区要盖掉上面刚恢复的首页横条
}
function closeStats(push=true){if(push)route('/');showHomeSurfaces();load(true)}

function resourceSyncMarkup(){
  return `<section class="resourcesync" id="resource-sync" aria-labelledby="resourceSyncTitle">
    <h2 id="resourceSyncTitle">资源同步</h2>
    <div class="resourcesyncbox"><div class="resourcesyncbody"><h3>网盘与账本</h3>
      <p>核对已挂载网盘与账本。网盘上已删除的条目先进入回收站；只清理没有在用的预览与播放缓存。</p></div>
      <div class="resourcesyncfooter"><p>离线来源会整库跳过。候选 CSV、来源证据、女优头像和厂牌 Logo 不会删除。</p>
      <button class="resourceaction" type="button" id="resourceScan" aria-busy="false">${icon('refresh-cw')}<span>扫描差异</span></button></div></div>
    <div id="resourceSyncResult" aria-live="polite"></div></section>`;
}
async function wireResourceSync(){
  const scan=$('#resourceScan'),result=$('#resourceSyncResult');
  if(!scan||!result)return;
  const active=()=>location.pathname==='/stats'&&!$('#stats').hidden&&document.body.contains(result);
  const setBusy=(busy,done=false)=>{
    scan.disabled=busy;scan.setAttribute('aria-busy',String(busy));
    scan.innerHTML=`${busy?spinnerHtml('扫描中'):icon('refresh-cw')}<span>${busy?'扫描中':done?'重新扫描':'扫描差异'}</span>`;
  };
  const render=payload=>{
    const sources=payload.sources||[];
    const cache=payload.cache||{files:0,bytes:0};
    const hasChanges=Boolean(payload.missing||cache.files);
    result.innerHTML=`<div class="resourcepanel"><div class="resourcesources">${sources.map(source=>`<article>
      <div class="resourcesourcetitle"><b>${esc(LOC[source.location]||source.location)}</b><span class="${source.online?'online':'offline'}">${source.online?'已挂载':'离线，已跳过'}</span></div>
      <strong>${source.online?source.missing.toLocaleString():'—'}</strong>
      <small>${source.online?`项已从网盘删除 · 已核对 ${source.checked.toLocaleString()} 项${source.unreadable?` · ${source.unreadable.toLocaleString()} 项暂时无法读取`:''}`:`账本有 ${source.total.toLocaleString()} 项`}</small></article>`).join('')}</div>
      <div class="resourcecache"><div><span>孤立缓存</span><b>${cache.files.toLocaleString()}</b><small>${fmtSize(cache.bytes||0)}</small></div>
      <div><span>待同步</span><b>${Number(payload.missing||0).toLocaleString()}</b><small>项；应用后进入回收站</small></div></div>
      <div class="resourceapplyrow">${hasChanges?`<p>确认后才会更改账本；操作可从回收站恢复。</p><button class="resourceaction resourcedanger" type="button" id="resourceApply">同步并清理</button>`:
        '<p class="resourcesyncok">账本与已挂载来源一致，没有孤立缓存。</p>'}</div></div>`;
    $('#resourceApply')?.addEventListener('click',async event=>{
      const button=event.currentTarget;
      if(!confirm(`把 ${payload.missing||0} 项移入回收站，并清理 ${cache.files||0} 个可重建缓存？`))return;
      button.disabled=true;button.setAttribute('aria-busy','true');
      button.innerHTML=`${spinnerHtml('正在应用')}<span>正在重新核对并应用…</span>`;
      try{
        const applied=await api('/api/resource-sync/apply',{method:'POST',body:JSON.stringify({confirm:true,clean_cache:true,scan_id:payload.scan_id||''})});
        result.innerHTML=`<p class="resourcesyncok">已把 ${applied.moved_to_trash.toLocaleString()} 项移入回收站，清理 ${applied.cache_removed.toLocaleString()} 个缓存，释放 ${fmtSize(applied.bytes_reclaimed||0)}。</p>`;
      }catch(error){
        button.disabled=false;button.removeAttribute('aria-busy');
        button.innerHTML=`${icon('refresh-cw')}<span>重试同步</span>`;
        result.insertAdjacentHTML('beforeend',noteHtml(error.message,{variant:'error',label:'同步失败'}))}
    });
  };
  const followScan=async payload=>{
    setBusy(true);result.innerHTML=`<p class="resourcescanning">${loadingDotsHtml('正在后台核对网盘元数据，不会读取视频内容。')}</p>`;
    try{
      if(!payload)payload=await api('/api/resource-sync/scan',{method:'POST',body:JSON.stringify({background:true,restart:true})});
      while(payload.status==='running'){
        const done=payload.sources||[];
        result.innerHTML=`<p class="resourcescanning">${loadingDotsHtml(`后台扫描中：已完成 ${payload.completed_sources||0} / ${payload.total_sources||3} 个来源${done.length?`（${done.map(source=>LOC[source.location]||source.location).join('、')}）`:''}。离开本页不会中断。`)}</p>`;
        await new Promise(resolve=>setTimeout(resolve,2000));
        if(!active())return;
        payload=await api('/api/resource-sync/scan',{method:'POST',body:JSON.stringify({background:true})});
      }
      if(payload.status==='failed')throw new Error(payload.error||'后台扫描失败');
      if(!active())return;
      render(payload);
    }
    catch(error){result.innerHTML=noteHtml(error.message,{variant:'error',label:'扫描失败'})}
    finally{setBusy(false,true)}
  };
  scan.onclick=()=>followScan(null);
  try{
    const existing=await api('/api/resource-sync/scan',{method:'POST',body:JSON.stringify({background:true,status_only:true})});
    if(existing.status!=='idle')void followScan(existing);
  }catch(_error){}
}
async function openResourceSync(push=true){
  if(push)route('/stats#resource-sync');
  else if(location.pathname==='/resource-sync')route('/stats#resource-sync',true);
  await openStats(false,true);
}

/* 口味仪表按窗口持久缓存：刷新页面也先显示上次结果。24 小时内不重读；
   过期后仍先显示旧结果，再在后台更新。导入、移除数据源和显式「读取」
   会立即写回缓存。缓存只含页面已经展示的聚合结果，不含原始历史。 */
const TASTE_CACHE_KEY='peach-taste-dashboard-v3',TASTE_CACHE_FRESH_MS=24*60*60*1000;
const TASTE_CACHE_WINDOWS=new Set(['all','365d','90d']);
function readTasteCache(){
  try{
    const stored=JSON.parse(localStorage.getItem(TASTE_CACHE_KEY)||'{}');
    return new Map(Object.entries(stored).filter(([window,entry])=>
      TASTE_CACHE_WINDOWS.has(window)&&entry&&Number.isFinite(Number(entry.at))&&
      entry.dashboard&&typeof entry.dashboard==='object'))
  }catch(_error){return new Map()}
}
let tasteWindow='all',tasteEvidence='browser',tasteDimension={browser:'tags',peach:'tags'};
let tasteCache=readTasteCache(),tasteRequest=0;
function tasteCacheSet(window,dashboard){
  tasteCache.set(window,{at:Date.now(),dashboard});
  try{localStorage.setItem(TASTE_CACHE_KEY,JSON.stringify(Object.fromEntries(tasteCache)))}catch(_error){}
}
const tasteDate=value=>value?new Date(value).toLocaleDateString('zh-CN'):'—';
const tasteHours=seconds=>seconds>=3600?(seconds/3600).toFixed(1)+' 小时':Math.round(seconds/60)+' 分钟';
const tasteRankRows=(rows,kind,empty='暂无足够证据',visual='')=>rows.length?rows.map((row,index)=>{
    const clickable=kind&&row.peach_items>0;
    const detail=row.web_visits!=null
      ?`${row.web_visits?`浏览 ${row.web_visits}`:''}${row.web_visits&&row.peach_items?' · ':''}${row.peach_items?`Peach ${row.peach_items}`:''}`
      :`${Number(row.score||row.visits||0).toLocaleString()}`;
    const ref=row.entity_id?{id:row.entity_id}:null,rep=row.representative_asset_id||null;
    const sourceDomain=String(row.source_domain||'');
    const media=visual==='domain'
      ?`<span class="tasteavatar tastesite"><span class="ini">${esc(row.name.slice(0,1).toUpperCase())}</span><img src="${esc(faviconUrl('https://'+row.name))}" data-fallback="${esc(faviconFallbackUrl(row.name))}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="const f=this.dataset.fallback;if(f){delete this.dataset.fallback;this.src=f}else this.remove()"></span>`
      :visual==='creator'&&!ref&&!rep&&sourceDomain
        ?`<span class="tasteavatar tastesite" title="来源：${esc(sourceDomain)}"><span class="ini">${esc(row.name.slice(0,1).toUpperCase())}</span><img src="${esc(faviconUrl('https://'+sourceDomain))}" data-fallback="${esc(faviconFallbackUrl(sourceDomain))}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="const f=this.dataset.fallback;if(f){delete this.dataset.fallback;this.src=f}else this.remove()"></span>`
      :visual?`<span class="tasteavatar">${avatarInner(row.name,ref,rep,visual)}</span>`:'';
    return `<${clickable?'button':'div'} class="tasterank${kind==='tag'?' tasterank-tag':''}${visual?' tasterank-visual':''}"${clickable?` data-taste-kind="${kind}" data-taste-name="${esc(row.name)}"`:''}>
      <span class="tastepos mono">${index+1}</span>${media}<span><b>${esc(row.name)}</b><small>${esc(detail)}</small></span>
      ${clickable?icon('chevron-right'):''}</${clickable?'button':'div'}>`}).join(''):
  emptyStateHtml('search','暂无足够证据',empty);
function openTasteSignal(kind,name){
  if(kind==='tag'){
    state={...state,tag:name,tag_match:'all',creator:'',studio:'',q:'',state:'',orient:''};
    $('#q').value='';route(homePath());showHomeSurfaces();buildBars();load(true);return
  }
  openEntity(kind,name);
}
function renderTaste(d){
  const s=d.summary||{},coverage=d.coverage||{},rank=d.rankings||{},storage=d.storage||{};
  const summary=(label,value,sub)=>`<div class="tastesummary"><span>${label}</span><b>${value}</b><small>${sub}</small></div>`;
  const coverageMetric=(label,value,sub,done,total)=>`<div class="tastecovermetric"><span>${label}</span><b>${value}</b><small>${sub}</small>${progressHtml(`${label}：${done} / ${total}`,done,total)}</div>`;
  const sourceRows=(d.sources||[]).map(source=>`<div class="tastesource">
    <span class="tastebrowser">${icon(source.browser==='browserexport'?'upload':'database')}</span>
    <span><b>${esc(source.profile)}</b><small>${esc(source.browser)} · ${esc(source.host)} · ${Number(source.visits||0).toLocaleString()} 条</small></span>
    <button data-taste-remove="${source.source_key}" title="移除分析记录" aria-label="移除 ${esc(source.profile)}">${icon('trash')}</button></div>`).join('');
  const gapRows=(d.gaps||[]).map(row=>({...row,evidence:['浏览记录']}));
  const domainRows=(rank.domains||[]).map(row=>({name:row.name,score:row.visits}));
  const categoryRows=(rank.categories||[]).map(row=>({name:row.name,score:row.score}));
  const categoryMax=Math.max(1,...categoryRows.map(row=>Number(row.score||0)));
  const categoryBars=categoryRows.length?categoryRows.map(row=>`<div class="tastebar"><div><span>${esc(row.name)}</span><b>${Number(row.score||0).toLocaleString()}</b></div>
    ${progressHtml(`${row.name}：${Number(row.score||0).toLocaleString()} / ${categoryMax.toLocaleString()}`,row.score||0,categoryMax)}</div>`).join(''):
    emptyStateHtml('search','暂无口味维度','采集浏览记录后，这里会显示聚合后的口味证据。');
  const rankPanel=(source,key,rows,kind='',empty='暂无足够证据',visual='')=>`<div id="taste-${source}-${key}" role="tabpanel"
    data-taste-dimension-panel="${source}:${key}"${tasteDimension[source]===key?'':' hidden'}>
    <div class="tasteranks${kind==='tag'?' tasteranks-tags':''}${visual?' tasteranks-visual':''}">${tasteRankRows(rows,kind,empty,visual)}</div></div>`;
  const sourceTabs=(source,tabs)=>`<div class="insighttabs" role="tablist" aria-label="${source==='browser'?'浏览器':'Peach'} 口味维度">${tabs.map(([key,label])=>
    `<button type="button" role="tab" data-taste-dimension="${source}:${key}" aria-selected="${tasteDimension[source]===key}"
      aria-controls="taste-${source}-${key}"${tasteDimension[source]===key?'':' tabindex="-1"'}>${label}</button>`).join('')}</div>`;
  $('#stats').innerHTML=`<div class="tastepage">
    <header class="tastehead"><div class="insightswitch" role="radiogroup" aria-label="口味证据来源">
        <label><input type="radio" name="taste-evidence" value="browser"${tasteEvidence==='browser'?' checked':''}><span>浏览器记录</span></label>
        <label><input type="radio" name="taste-evidence" value="peach"${tasteEvidence==='peach'?' checked':''}><span>Peach 内部</span></label></div>
      <div class="tasteactions"><select data-taste-window aria-label="分析范围">
        <option value="all">全部时间</option><option value="365d">最近一年</option><option value="90d">最近 90 天</option></select>
        <button data-taste-refresh>${icon('refresh-cw')}读取 Peach 主机</button>
        <button data-taste-import>${icon('upload')}导入历史</button><input data-taste-file type="file" hidden></div></header>
    <div class="tastestate" data-taste-state role="status" aria-live="polite"></div>
    <div class="tastesummaries" data-taste-summary="browser"${tasteEvidence==='browser'?'':' hidden'}>
      ${summary('浏览记录',Number(s.history_visits||0).toLocaleString(),`${s.history_sources||0} 个数据源 · ${tasteDate(s.range_start)}—${tasteDate(s.range_end)}`)}
      ${summary('口味维度',categoryRows.length.toLocaleString(),categoryRows[0]?.name||'尚无主维度')}
      ${summary('浏览候选',gapRows.length.toLocaleString(),'只作待复核证据')}
      ${summary('私有导出',Number(storage.exports||0).toLocaleString(),fmtSize(storage.bytes||0))}</div>
    <div class="tastesummaries" data-taste-summary="peach"${tasteEvidence==='peach'?'':' hidden'}>
      ${summary('Peach 看过',Number(s.peach_items||0).toLocaleString(),tasteHours(s.peach_seconds||0))}
      ${summary('喜欢',Number(s.liked||0).toLocaleString(),'明确正向反馈')}
      ${summary('不合口味',Number(s.disliked||0).toLocaleString(),'只归于具体项目')}
      ${summary('有标签',Number(coverage.tagged||0).toLocaleString(),`${coverage.untagged||0} 项待补`)}</div>
    <section class="tastehero" data-taste-evidence-panel="browser"${tasteEvidence==='browser'?'':' hidden'}>
      <div class="insightcopy"><span>浏览器画像</span><h2>${Number(s.history_visits||0).toLocaleString()}</h2><b>条聚合访问证据</b>
        <p>浏览器记录是当前分析主体；页面只展示聚合结果，不展示原始 URL、标题或搜索内容。</p>
        <small>${d.updated_at?`更新于 ${tasteDate(d.updated_at)}`:'尚未采集浏览记录'}</small></div>
      <div class="tastebars">${categoryBars}</div></section>
    <section class="tastehero" data-taste-evidence-panel="peach"${tasteEvidence==='peach'?'':' hidden'}>
      <div class="insightcopy"><span>Peach 观看</span><h2>${Number(s.peach_items||0).toLocaleString()}</h2><b>个作品有内部行为证据</b>
        <p>播放、评分与明确反馈保持独立，不反向代表全部浏览口味。</p></div>
      <div class="insightvisual">
        ${coverageMetric('有标签',Number(coverage.tagged||0).toLocaleString(),`${coverage.untagged||0} 项待补`,coverage.tagged||0,(coverage.tagged||0)+(coverage.untagged||0))}
        ${coverageMetric('有身份',Number(coverage.identified||0).toLocaleString(),`${coverage.unidentified||0} 项待补`,coverage.identified||0,(coverage.identified||0)+(coverage.unidentified||0))}
      </div></section>
    <section class="insightpanel tasteanalysis" data-taste-evidence-panel="browser"${tasteEvidence==='browser'?'':' hidden'}>
      <header>${sourceTabs('browser',[['tags','标签'],['creators','创作者'],['domains','常访问网站'],['gaps','浏览候选']])}</header>
      <div class="insightpanelbody">
        ${rankPanel('browser','tags',rank.browser_tags||[],'tag')}
        ${rankPanel('browser','creators',rank.browser_creators||[],'creator','暂无创作者证据','creator')}
        ${rankPanel('browser','domains',domainRows,'','暂无网站证据','domain')}
        ${rankPanel('browser','gaps',gapRows,'','这些词在浏览记录中出现，但 Peach 观看记录还没有对应证据')}
      </div></section>
    <section class="insightpanel tasteanalysis" data-taste-evidence-panel="peach"${tasteEvidence==='peach'?'':' hidden'}>
      <header>${sourceTabs('peach',[['tags','标签'],['creators','创作者'],['performers','女优']])}</header>
      <div class="insightpanelbody">
        ${rankPanel('peach','tags',rank.peach_tags||[],'tag')}
        ${rankPanel('peach','creators',rank.peach_creators||[],'creator','暂无创作者证据','creator')}
        ${rankPanel('peach','performers',rank.peach_performers||rank.performers||[],'performer','暂无女优证据','performer')}
      </div></section>
    <div data-taste-evidence-panel="peach"${tasteEvidence==='peach'?'':' hidden'}>${noteHtml('“不合口味”只记录到具体项目与理由，不自动给标签降权。',{className:'tastefootnote tastenegative'})}</div>
    <section class="insightpanel tastesources"><header><div><h3>数据源</h3><p>支持 macOS / Windows 的 Zen、Safari、Firefox、Chrome；这里列出已经采集的设备。</p></div></header>
      <div class="insightpanelbody"><div>${sourceRows||emptyStateHtml('database','还没有数据源','导入或读取浏览记录后，这里会列出已采集设备。')}</div></div></section>
    ${noteHtml('原始 URL、标题与搜索内容不会显示在页面，也不会写入 ledger；所有画像均为候选。',{className:'tastefootnote tasteprivacy'})}
  </div>`;
  const root=$('#stats'),stateEl=root.querySelector('[data-taste-state]'),file=root.querySelector('[data-taste-file]');
  root.querySelector('[data-taste-window]').value=d.window||tasteWindow;
  root.querySelectorAll('input[name="taste-evidence"]').forEach(input=>input.onchange=()=>{
    tasteEvidence=input.value;
    root.querySelectorAll('[data-taste-summary]').forEach(panel=>panel.hidden=panel.dataset.tasteSummary!==tasteEvidence);
    root.querySelectorAll('[data-taste-evidence-panel]').forEach(panel=>panel.hidden=panel.dataset.tasteEvidencePanel!==tasteEvidence)
  });
  root.querySelectorAll('[data-taste-dimension]').forEach(button=>button.onclick=()=>{
    const [source,key]=button.dataset.tasteDimension.split(':');tasteDimension[source]=key;
    root.querySelectorAll(`[data-taste-dimension^="${source}:"]`).forEach(tab=>{
      const selected=tab===button;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1});
    root.querySelectorAll(`[data-taste-dimension-panel^="${source}:"]`).forEach(panel=>panel.hidden=panel.dataset.tasteDimensionPanel!==button.dataset.tasteDimension)
  });
  root.querySelector('[data-taste-window]').onchange=e=>{tasteWindow=e.target.value;openTaste(false)};
  root.querySelector('[data-taste-refresh]').onclick=async e=>{const button=e.currentTarget;
    const oldButton=button.innerHTML;
    button.disabled=true;button.setAttribute('aria-busy','true');
    button.innerHTML=`${spinnerHtml('正在读取')}<span>读取中…</span>`;
    stateEl.innerHTML=loadingDotsHtml('正在读取 Peach 所在主机的浏览器…');
    try{const result=await api('/api/taste/refresh',{method:'POST',body:JSON.stringify({window:tasteWindow})});
      tasteCacheSet(tasteWindow,result.dashboard);renderTaste(result.dashboard)}
    catch(error){stateEl.textContent=error.message||'读取失败';button.disabled=false;
      button.removeAttribute('aria-busy');button.innerHTML=oldButton}};
  root.querySelector('[data-taste-import]').onclick=()=>file.click();
  file.onchange=async()=>{const selected=file.files[0];if(!selected)return;stateEl.textContent=`正在导入 ${selected.name}…`;
    try{const response=await fetch('/api/taste/import',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Peach-Filename':encodeURIComponent(selected.name)},body:selected});
      const payload=await response.json().catch(()=>null);if(!response.ok)throw new Error(payload?.error||`导入失败（${response.status}）`);
      tasteWindow='all';tasteCacheSet('all',payload.dashboard);renderTaste(payload.dashboard)}catch(error){stateEl.textContent=error.message||'导入失败'}};
  root.querySelectorAll('[data-taste-kind]').forEach(button=>button.onclick=()=>openTasteSignal(button.dataset.tasteKind,button.dataset.tasteName));
  root.querySelectorAll('[data-taste-remove]').forEach(button=>button.onclick=async()=>{
    if(!confirm('从口味分析中移除这个数据源？原始导出文件会保留。'))return;
    button.disabled=true;stateEl.textContent='正在移除…';
    try{const result=await api('/api/taste/source',{method:'POST',body:JSON.stringify({operation:'remove',source_key:button.dataset.tasteRemove,window:tasteWindow})});
      tasteCacheSet(tasteWindow,result.dashboard);renderTaste(result.dashboard)}
    catch(error){stateEl.textContent=error.message||'移除失败';button.disabled=false}});
}
async function openTaste(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  state={...state,creator:'',studio:'',tag:'',tag_match:'all',len:'',dur_min:'',dur_max:'',orient:'',state:'',q:'',jav:''};
  $('#q').value='';
  if(push)route('/taste');
  const surface=claimSurface('/taste');
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;buildManageBar();
  const cachedEntry=tasteCache.get(tasteWindow),cached=cachedEntry?.dashboard;
  const cacheFresh=cached&&Date.now()-cachedEntry.at<TASTE_CACHE_FRESH_MS;
  if(cached)renderTaste(cached);
  else $('#stats').innerHTML=`<div class="tastepage"><div class="skeletonpanel">
    <span class="skeleton" style="width:38%"></span>
    <span class="skeleton" style="width:100%"></span>
    <span class="skeleton" style="width:100%"></span>
    <span class="skeleton" style="width:72%"></span></div></div>`;
  if(!cacheFresh){
    const request=++tasteRequest;
    const requestedWindow=tasteWindow;
    void api('/api/taste?window='+requestedWindow).then(data=>{
      tasteCacheSet(requestedWindow,data);
      if(request===tasteRequest&&tasteWindow===requestedWindow&&surfaceCurrent(surface))renderTaste(data)
    }).catch(error=>{
      if(!cached&&request===tasteRequest&&surfaceCurrent(surface))$('#stats').innerHTML=
        `<div class="tastepage">${noteHtml(error.message||'分析未取得',{variant:'error',label:'分析未取得'})}</div>`
    })
  }
  window.scrollTo({top:0,behavior:'smooth'});
}

function playlistDialog(content){
  document.querySelector('#playlistDialog')?.remove();
  const dialog=document.createElement('dialog');dialog.id='playlistDialog';dialog.className='playlistdialog';
  dialog.innerHTML=`<div class="playlistdialoghead"><h2></h2><button type="button" data-dialog-close aria-label="关闭">${icon('x')}</button></div><div class="playlistdialogbody"></div>`;
  dialog.querySelector('h2').textContent=content.title;
  dialog.querySelector('.playlistdialogbody').innerHTML=content.body;
  dialog.querySelector('[data-dialog-close]').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>dialog.remove(),{once:true});
  document.body.append(dialog);dialog.showModal();return dialog;
}
async function saveMixAsPlaylist(mix){
  if(mix?.kind!=='mix')return;
  const dialog=playlistDialog({title:'保存 Mix',body:`<form class="playlistcreate" data-save-mix-form>
    <label>名称<input name="name" maxlength="80" value="${esc(mix.title)}" required></label>
    <button type="submit">保存 ${mix.items.length} 个视频</button><span data-playlist-state></span></form>`});
  dialog.querySelector('form').onsubmit=async event=>{event.preventDefault();
    const form=event.currentTarget,stateEl=form.querySelector('[data-playlist-state]');
    try{const result=await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'create',name:new FormData(form).get('name'),asset_ids:mix.items.map(item=>item.id),source_kind:'mix',source_seed_asset_id:mix.seedId})});
      dialog.close();await openPlaylist(result.playlist.id,result.playlist.current_asset_id,true)
    }catch(error){stateEl.textContent=error.message||'保存失败'}
  };
  dialog.querySelector('input').select();
}
async function openAddToPlaylist(item){
  const lists=(await api('/api/playlists')).items||[];
  const rows=lists.map(list=>`<button type="button" class="playlistpickrow" data-add-playlist="${list.id}"><span>${esc(list.name)}</span><small>${list.item_count} 个视频</small></button>`).join('');
  const dialog=playlistDialog({title:'加入播放列表',body:`<form class="playlistcreate" data-create-playlist>
      <label>新播放列表<input name="name" maxlength="80" placeholder="输入名称" required></label><button type="submit">新建并加入</button><span data-playlist-state></span></form>
    <div class="playlistpicklist">${rows||'<p class="empty">还没有播放列表</p>'}</div>`});
  const finish=async body=>{const stateEl=dialog.querySelector('[data-playlist-state]');
    try{await api('/api/playlist',{method:'POST',body:JSON.stringify(body)});dialog.close()}
    catch(error){stateEl.textContent=error.message||'加入失败'}};
  dialog.querySelector('form').onsubmit=event=>{event.preventDefault();finish({action:'create',name:new FormData(event.currentTarget).get('name'),asset_ids:[item.id]})};
  dialog.querySelectorAll('[data-add-playlist]').forEach(button=>button.onclick=()=>finish({action:'add',id:+button.dataset.addPlaylist,asset_ids:[item.id]}));
}
async function movePlaylistItem(queue,index,delta,currentId){
  if(queue?.kind!=='playlist')return;
  const target=index+delta;if(target<0||target>=queue.items.length)return;
  const ids=queue.items.map(item=>item.id);[ids[index],ids[target]]=[ids[target],ids[index]];
  await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'reorder',id:queue.playlistId,asset_ids:ids})});
  await openPlaylist(queue.playlistId,currentId,false);
}
async function removePlaylistItem(queue,assetId,currentId){
  if(queue?.kind!=='playlist'||!confirm('从播放列表移出这个视频？'))return;
  const result=await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'remove',id:queue.playlistId,asset_id:assetId})});
  if(!result.playlist.items.length){await openPlaylists(true);return}
  const next=result.playlist.items.some(item=>item.id===currentId)?currentId:result.playlist.current_asset_id;
  await openPlaylist(queue.playlistId,next,false);
}
async function openPlaylists(push=true){
  releaseHoverPreviews();disposeStage(false);document.body.classList.remove('entity-open','index-open');
  if(push)route('/playlists');
  const surface=claimSurface('/playlists');
  const data=await api('/api/playlists');
  if(!surfaceCurrent(surface))return;
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;$('#tiers').style.display='none';$('#tagbar').style.display='none';
  $('#managebar').hidden=true;$('#manageTitle').hidden=true;buildEdge();
  const cards=(data.items||[]).map(list=>{const resume=list.current_asset_id||list.preview_asset_id;
    const poster=list.preview_asset_id?`<img src="/poster?id=${list.preview_asset_id}&c=4" alt="" loading="lazy" onerror="this.remove()">`:'';
    return `<article class="playlistcard" data-playlist-card="${list.id}"><button class="playlistcover" data-open-playlist="${list.id}" ${resume?'':'disabled'}>${poster}<span>${list.item_count} 个视频</span></button>
      <div class="playlistmeta"><input data-playlist-name maxlength="80" value="${esc(list.name)}" aria-label="播放列表名称"><small>${list.source_kind==='mix'?'由 Mix 保存':'手动播放列表'}</small></div>
      <div class="playlistactions"><button data-rename-playlist="${list.id}">保存名称</button><button data-open-playlist="${list.id}" ${resume?'':'disabled'}>继续播放</button><button class="danger" data-delete-playlist="${list.id}">删除</button></div></article>`}).join('');
  $('#stats').innerHTML=`<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><form class="playlistcreate" id="newPlaylist"><label>新播放列表<input name="name" maxlength="80" placeholder="输入名称" required></label><button type="submit">新建</button><span data-playlist-state></span></form></header><div class="playlistcards">${cards||emptyState('list-filter','还没有播放列表','保存 Mix 或新建列表后，会在这里按自己的顺序继续播放。')}</div></section>`;
  $('#newPlaylist').onsubmit=async event=>{event.preventDefault();const form=event.currentTarget;
    try{await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'create',name:new FormData(form).get('name'),asset_ids:[]})});await openPlaylists(false)}
    catch(error){form.querySelector('[data-playlist-state]').textContent=error.message||'新建失败'}};
  $('#stats').querySelectorAll('[data-open-playlist]').forEach(button=>button.onclick=()=>{
    const list=data.items.find(item=>item.id===+button.dataset.openPlaylist),resume=list?.current_asset_id||list?.preview_asset_id;
    if(resume)openPlaylist(list.id,resume,true)});
  $('#stats').querySelectorAll('[data-rename-playlist]').forEach(button=>button.onclick=async()=>{const card=button.closest('[data-playlist-card]'),input=card.querySelector('[data-playlist-name]');
    await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'rename',id:+button.dataset.renamePlaylist,name:input.value})});await openPlaylists(false)});
  $('#stats').querySelectorAll('[data-delete-playlist]').forEach(button=>button.onclick=async()=>{if(!confirm('删除这个播放列表？视频本身不会删除。'))return;
    await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'delete',id:+button.dataset.deletePlaylist})});await openPlaylists(false)});
  window.scrollTo({top:0,behavior:'smooth'});
}

let reviewData=null,reviewRuntime=null,reviewCategory='metadata_fields';
/* 主体是实体而不是单条作品的复核分类。值就是实体 kind。 */
const ENTITY_REVIEW_CATEGORIES={creator_tags:'creator',western_identity:'creator'};
const REVIEW_LABELS={metadata_fields:'元数据字段',creator_tags:'创作者标签',studio_logos:'厂牌 Logo',performer_avatars:'女优头像',western_identity:'西方身份回配',code_creators:'番号目录存疑',fc2_markings:'FC2 评论标记',fc2_similarity:'FC2 跨号相似',video_endcards:'片尾/出处证据',media_failure:'媒体失败'};
let dupData=null;
/* 重复文件。判据是「同番号 + 时长相近 + 分卷标记一致」，不是同番号即重复——
   合集、分卷和混入的广告都会共用一个 code，只按番号做「保留最大」会删掉内容。
   批量一律走 dispose 进回收站，可逆；永久删除仍只能从回收站单独执行。 */
async function openDuplicates(push=true){
  releaseHoverPreviews();disposeStage(false);document.body.classList.remove('entity-open');
  if(push)route('/duplicates');
  const surface=claimSurface('/duplicates');
  buildManageBar();
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#stats').innerHTML=`<div class="review"><p class="empty">${loadingDotsHtml('正在比对')}</p></div>`;
  const next=await api('/api/duplicates?limit=120');
  if(!surfaceCurrent(surface))return;
  dupData=next;
  renderDuplicates();
}
function renderDuplicates(){
  const d=dupData;if(!d)return;
  const groups=d.groups||[];
  paintManageLede(`${d.total} 组 · ${d.files} 个文件 · 可回收 ${fmtSize(d.reclaimable)}`);
  $('#stats').innerHTML=`<div class="review">
    ${groups.length?`<div class="fsechead dupactions"><h3>操作</h3>
      <button data-dup-all="largest">全部保留最大</button>
      <button data-dup-all="longest">全部保留最长</button>
      <button data-dup-all="115">全部优先 115</button>
      <button data-dup-all="pikpak">全部优先 PikPak</button></div>`:''}
    ${groups.length?groups.map((g,gi)=>`<section class="dupgroup" data-dup-group="${gi}">
      <div class="duphead"><b class="mono">${esc(g.code)}</b>
        <span class="mono">${g.count} 个 · 可回收 ${fmtSize(g.reclaimable)}</span>
        ${g.identical?'<span class="dupflag ok">sha1 一致</span>':'<span class="dupflag">时长推断</span>'}
        ${g.cross_drive?`<span class="dupflag">跨盘 ${esc(g.drives.join(' '))}</span>`:''}
        <span class="dupbtns"><button data-dup-keep="largest" data-dup-i="${gi}">留最大</button>
          <button data-dup-keep="longest" data-dup-i="${gi}">留最长</button>
          <button data-dup-keep="115" data-dup-i="${gi}">留 115</button>
          <button data-dup-keep="pikpak" data-dup-i="${gi}">留 PikPak</button>
          <button class="danger" data-dup-keep="all" data-dup-i="${gi}">整组回收</button></span></div>
      <div class="duplist">${g.files.map(f=>`<div class="duprow">
        <span class="dupmarks">${f.is_largest?'<i class="big">最大</i>':''}${f.is_longest?'<i class="long">最长</i>':''}</span>
        <button class="dupname" data-middle-truncate data-open-dup="${f.id}" title="${esc(f.name)}">${esc(f.name)}</button>
        <span class="mono">${esc(LOC[f.location]||f.location||f.drive||'')}</span>
        <span class="mono">${fmtSize(f.size||0)}</span>
        <span class="mono">${fmtDur(f.duration)}</span>
        <span class="mono duppath" data-middle-truncate title="${esc(f.path||'')}">${esc(f.path||'')}</span></div>`).join('')}</div>
    </section>`).join(''):emptyState('database','没有找到重复文件','所有来源之间没有检测到内容相同的文件。扫描新来源后，这里会自动更新。')}</div>`;
  $('#stats').querySelectorAll('[data-open-dup]').forEach(b=>
    b.onclick=()=>openItem(+b.dataset.openDup));
  $('#stats').querySelectorAll('[data-dup-keep]').forEach(b=>
    b.onclick=()=>disposeDuplicates([groups[+b.dataset.dupI]],b.dataset.dupKeep,b));
  $('#stats').querySelectorAll('[data-dup-all]').forEach(b=>
    b.onclick=()=>disposeDuplicates(groups,b.dataset.dupAll,b));
}
/* 每组只留一个，其余进回收站；整组都是广告时允许一个不留。 */
function duplicateVictims(groups,keep){
  const ids=[];
  for(const g of groups){
    if(keep==='all'){for(const f of g.files)ids.push(f.id);continue}
    const flag=keep==='longest'?'is_longest':'is_largest';
    const preferred=(keep==='115'||keep==='pikpak')?g.files.filter(f=>f.location===keep):[];
    const pool=preferred.length?preferred:g.files;
    const keeper=(keep==='largest'||keep==='longest')
      ? (g.files.find(f=>f[flag])||g.files[0])
      : pool.reduce((best,file)=>(file.size||0)>(best.size||0)?file:best,pool[0]);
    for(const f of g.files)if(f.id!==keeper.id)ids.push(f.id);
  }
  return ids;
}
async function disposeDuplicates(groups,keep,button){
  const ids=duplicateVictims(groups,keep);
  if(!ids.length)return;
  const victims=new Set(ids);
  const bytes=groups.reduce((n,g)=>n+g.files.reduce((m,f)=>m+(victims.has(f.id)?f.size||0:0),0),0);
  const label={largest:'最大的一个',longest:'最长的一个','115':'115（没有则留最大）',pikpak:'PikPak（没有则留最大）',all:'零个文件'}[keep];
  if(!confirm(`把 ${ids.length} 个文件移入回收站，每组保留${label}？\n`
    +`预计回收 ${fmtSize(bytes)}。文件仍在回收站里，可以还原。`))return;
  button.disabled=true;
  try{
    // /api/batch 单次上限 200，分批发。
    for(let i=0;i<ids.length;i+=200){
      await api('/api/batch',{method:'POST',
        body:JSON.stringify({ids:ids.slice(i,i+200),operation:'dispose'})});
    }
    await openDuplicates(false);
  }finally{button.disabled=false}
}
async function openReview(push=true){
  releaseHoverPreviews();disposeStage(false);document.body.classList.remove('entity-open');
  if(push)route('/review');
  const surface=claimSurface('/review');
  buildManageBar();
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;$('#tiers').style.display='none';$('#tagbar').style.display='none';
  const runtime=await api('/healthz');
  if(!surfaceCurrent(surface))return;
  /* ADR-0018：确定的那部分先落库再取队列。reader 明知不能写就不要制造一次 409；
     它改为读取 writer 的严格 CA HTTPS 镜像，判定按钮也一起锁住。 */
  if(!runtime.ledger_read_only)try{
    const auto=await api('/api/review/auto-apply',{method:'POST',body:'{}'});
    if(!surfaceCurrent(surface))return;
    if(auto&&auto.applied)console.info(`自动落库 ${auto.applied} 条（ADR-0018）`);
  }catch(e){console.info('自动落库未执行：'+e.message)}
  const next=await api('/api/review');
  if(!surfaceCurrent(surface))return;
  reviewRuntime=runtime;reviewData=next;
  const render=()=>{
    const rows=reviewData.sections[reviewCategory]||[];
    const title=REVIEW_LABELS[reviewCategory];
    const mirror=reviewData.mirror||null,locked=!!reviewRuntime.ledger_read_only;
    const writer=reviewRuntime.ledger_writer_origin
      ?new URL('/review',reviewRuntime.ledger_writer_origin).href:'';
    const mirrorText=mirror?.state==='live'?'正在显示写入端的实时复核队列'
      :mirror?.state==='cached'?`写入端暂时不可达，显示 ${localTime(mirror.fetched_at)} 的缓存`
      :mirror?.error||reviewRuntime.ledger_read_only_message||'';
    const value=row=>row.tags||row.japanese_name||row.path||row.suggested_query||'';
     $('#stats').innerHTML=`<div class="review">
      ${locked?`<div class="runtimegate">${icon('info')}<span>${esc(mirrorText)}</span>${writer
        ?`<a href="${esc(writer)}">前往写入端复核</a>`:''}</div>`:''}
      <div class="reviewtabs">${Object.entries(REVIEW_LABELS).map(([key,label])=>`<button data-review-tab="${key}" aria-pressed="${key===reviewCategory}">${label} <span class="n mono">${reviewData.counts[key]||0}</span></button>`).join('')}</div>
      <section class="reviewsection"><div class="reviewlist">${rows.length?rows.map(row=>{
        const key=row.item_key,decision=row.decision||'pending';
        const metadata=reviewCategory==='metadata_fields',candidates=row.candidates||[];
        const tags=String(row.tags||'').split('|').filter(Boolean).map(tag=>`<span>${esc(tag)}</span>`).join('');
        const titleText=metadata?`${row.query||row.code} · ${row.field_label||row.field}`:(row.creator||row.studio||row.current_name||row.name||key);
        const evidence=row.reason||row.evidence||row.note||row.decision_note||'';
        const canApprove=metadata?candidates.length>0:(reviewCategory!=='creator_tags'||String(row.status||'').trim()==='candidate');
         const approveLabel=canApprove?'通过':'已跳过';
         const assets=row.preview_assets||[];
         /* 有些候选判的是「这位创作者」，不是某一条作品：创作者标签看的是他全部
            作品该打什么标签，西方身份回配的是这个人对不对得上。这类卡片顶上必须给
            创作者入口，而不是从样本里挑一条画成「原视频」——下面 60 个样本、上面
            1 个视频，读起来就是错的（西方身份那条更极端：772 部作品配 1 个）。 */
         const subjectKind=ENTITY_REVIEW_CATEGORIES[reviewCategory];
         const subjectName=String(row.creator||'').trim();
         const works=Number(row.video_count||row.videos||0);
         const comparison=row.comparison_assets||[];
         const comparisonOrigin=comparison.length>1?`<div class="reviewcompare">${comparison.map(asset=>`<div class="revieworigin">
             <button class="revieworigincover" data-review-open-item="${asset.id}" aria-label="打开原视频 ${esc(asset.name||'')}">
               ${asset.preview_url?`<img src="${esc(asset.preview_url)}" alt="" loading="lazy" onerror="this.remove()">`:'<span>无封面</span>'}</button>
             <div><b data-middle-truncate title="${esc(asset.name||'')}">${esc(asset.code||asset.name||'原视频')}</b>
               <button type="button" data-review-open-item="${asset.id}">${icon('play')}打开原视频</button></div></div>`).join('')}</div>`:'';
         const origin=comparisonOrigin||subjectKind&&subjectName?comparisonOrigin||`<div class="reviewentity">
             <button class="reviewentityface" data-entity-kind="${subjectKind}" data-entity-name="${esc(subjectName)}"
               aria-label="打开创作者页：${esc(subjectName)}">${avatarInner(subjectName,
                 row.entity_id?{id:row.entity_id}:null,null,subjectKind)}</button>
             <div><b><button type="button" class="reviewentityname" data-entity-kind="${subjectKind}" data-entity-name="${esc(subjectName)}">${esc(subjectName)}</button></b>
               ${works?`<small class="mono">${works.toLocaleString()} 部作品</small>`:''}</div></div>`
           :row.asset_id?`<div class="revieworigin">
             <button class="revieworigincover" data-review-open-item="${row.asset_id}" aria-label="打开原视频 ${esc(row.asset_name||'')}">
               ${row.asset_preview_url?`<img src="${esc(row.asset_preview_url)}" alt="" loading="lazy" onerror="this.remove()">`:'<span>无封面</span>'}</button>
             <div><b data-middle-truncate title="${esc(row.asset_name||'')}">${esc(row.asset_name||'原视频')}</b>
               <button type="button" data-review-open-item="${row.asset_id}">${icon('play')}打开原视频</button></div></div>`:'';
         /* 只有一个候选时没什么可选的，单选圈只是让人以为还有别的选项。
            改成纯展示，几何对齐上面的「打开原视频」块。
            radio 保留但不可见：提交路径读的就是 `[name^="metadata-"]:checked`，
            删掉它会让批准退化成「必须选择一个来源值」的报错，而不是少一个圈。 */
         const evidenceLabels={title:'标题',original_title:'原标题',runtime:'来源时长',director:'导演',label:'Label',poster_url:'海报',cover_url:'封面',screenshot_urls:'截图',trailer_url:'预告片'};
         const candidateEvidence=candidate=>{
           const rows=Object.entries(candidate.catalog_evidence||{}).filter(([,item])=>item&&item.display_value);
           return rows.length?`<dl class="metadataevidence">${rows.map(([field,item])=>`<div><dt>${esc(evidenceLabels[field]||field)}</dt><dd>${esc(item.display_value)}</dd>${(item.warnings||[]).map(warning=>`<small>${esc(warning)}</small>`).join('')}</div>`).join('')}</dl>`:''};
         const candidateBody=candidate=>`<b>${esc(candidate.source)}${candidate.official?' · 官方优先':''}${candidate.content_id||candidate.provider_id?` · ID ${esc(candidate.content_id||candidate.provider_id)}`:''}</b>`
           +`<span>${esc(candidate.display_value||'')}</span>`
           +(candidate.warnings||[]).map(warning=>`<i>${esc(warning)}</i>`).join('')
           +candidateEvidence(candidate);
         const preview=metadata
           ? (candidates.length===1
             ? `<div class="metadatasole"><input type="radio" name="metadata-${esc(key)}" value="${esc(candidates[0].candidate_key)}" checked>
                 <span>${candidateBody(candidates[0])}</span></div>`
             : `<div class="metadatacandidates">${candidates.map((candidate,index)=>`<label class="metadatacandidate"><input type="radio" name="metadata-${esc(key)}" value="${esc(candidate.candidate_key)}"${index===0?' checked':''}><span>${candidateBody(candidate)}</span></label>`).join('')}</div>`)
           : reviewCategory==='creator_tags'
           ? (assets.length?`<div class="reviewpick"><div class="reviewpickhead"><span class="mono" data-picked-count></span>
               <button type="button" data-pick-all>全选</button><button type="button" data-pick-none>清空</button></div>
               <div class="reviewasset-grid">${assets.map(asset=>`<button type="button" class="reviewasset picked" data-review-asset="${asset.id}" aria-pressed="true" title="${esc(asset.name)}"><img src="/poster?id=${asset.id}&c=4" alt="" loading="lazy"><span class="pickmark">${icon('check')}</span></button>`).join('')}</div></div>`
              // 空白一片会被当成界面坏了。真实原因是这些作品还没抽帧，说清楚比留白好。
              : `<p class="empty">这 ${esc(row.video_count||'')} 条作品尚未抽帧，暂无预览；批准后仍会按候选写入标签</p>`)
           : reviewCategory==='fc2_similarity'?''
           : (row.preview_url?`<div class="reviewimage"><img src="${esc(row.preview_url)}" alt="" loading="lazy" onerror="this.closest('.reviewimage').remove()"></div>`:'<p class="empty">未取得图片预览</p>');
         const body=`${
           // 实体类卡片的名字已经写在创作者入口里，再画一个 h4 就是同一行字上下两遍。
           subjectKind&&subjectName?'':`<h4>${esc(titleText)}</h4>`}${
           // 账本规范名当标题，抓取来源给的写法（多为罗马音）留作副标题。
           row.source_name?`<p class="reviewalias">来源写法：${esc(row.source_name)}</p>`:''}${
           // 实体类卡片的作品数已经写在创作者入口里，这里再写一遍就是同一个数字两处。
           subjectKind&&subjectName?'':`<p>${esc(row.board||row.assets?`样本/资产：${row.video_count||row.assets||''}`:'')}</p>`}${origin}${tags?`<div class="reviewtags">${tags}</div>`:''}${preview}<p>${esc(evidence)}</p>`;
         const actions=`<button class="approve" data-review-status="approved"${canApprove&&!locked?'':' disabled'}>${approveLabel}</button><button class="skip" data-review-status="skipped"${locked?' disabled':''}>跳过</button><button class="reject" data-review-status="rejected"${locked?' disabled':''}>拒绝</button><span class="reviewstate" aria-live="polite"></span>`;
         return `<fieldset class="reviewitem" data-geist-fieldset data-review-key="${esc(key)}" data-decision="${esc(decision)}"><legend class="sr-only">${esc(titleText)}</legend><div class="geist-fieldset-content">${scrollerHtml(body,{className:'reviewcontent',label:`复核：${titleText}`})}</div><footer class="reviewactions geist-fieldset-footer" data-geist-fieldset-footer>${actions}</footer></fieldset>`}).join(''):emptyState('square-check-big','暂无候选','该分类当前没有待人工复核的项目。')}</div></section></div>`;
     wireReviewAssets($('#stats'));
    wireScrollers($('#stats'));
    $('#stats').querySelectorAll('[data-review-open-item]').forEach(button=>button.onclick=()=>openItem(+button.dataset.reviewOpenItem));
    // 没有全局委托，每个界面各自接线（见 #stage 的同类处理）。
    $('#stats').querySelectorAll('[data-entity-kind]').forEach(button=>button.onclick=()=>
      openEntity(button.dataset.entityKind,button.dataset.entityName));
    $('#stats').querySelectorAll('[data-review-tab]').forEach(button=>button.onclick=()=>{reviewCategory=button.dataset.reviewTab;render()});
    $('#stats').querySelectorAll('[data-review-status]').forEach(button=>button.onclick=async()=>{
      const item=button.closest('[data-review-key]'),row=rows.find(x=>String(x.item_key)===item.dataset.reviewKey);button.disabled=true;
       const selectedIds=[...item.querySelectorAll('[data-review-asset][aria-pressed="true"]')].map(cell=>+cell.dataset.reviewAsset);
       const candidateKey=item.querySelector('[name^="metadata-"]:checked')?.value||'';
       /* api() 在任何非 2xx 都 throw。这里原来没有 catch：错误被吞成 unhandled
         rejection，下面的 button.disabled=false 永远到不了，于是按钮永久禁用、
         界面一句话都不给——用户看到的就是「点了没反应」。
         失败必须说出来，并且把按钮放开让人能重试。 */
      const state=item.querySelector('.reviewstate');
      if(state)state.textContent='';
      try{
        const result=await api('/api/review/decision',{method:'POST',body:JSON.stringify({category:reviewCategory,item_key:item.dataset.reviewKey,status:button.dataset.reviewStatus,candidate_key:candidateKey,creator:row.creator,tags:row.tags,studio:row.studio,entity_id:row.entity_id,avatar_url:row.avatar_url,selected_ids:selectedIds})});
        if(result.ok){
          // 只改 data 属性的话，条目还杵在队列里，看起来就像没生效。
          // 判过的直接移出本批并同步计数，下一条立刻顶上来。
          const index=rows.indexOf(row);
          if(index>=0)rows.splice(index,1);
          reviewData.counts[reviewCategory]=Math.max(0,(reviewData.counts[reviewCategory]||1)-1);
          render();
          return;
        }
        if(state)state.textContent=result.error||'服务端拒绝了这次判定';
      }catch(e){
        if(state)state.textContent=e.message||'判定失败，请重试';
      }
      button.disabled=false;
    });
  };
  render();window.scrollTo({top:0,behavior:'smooth'});
}

let qualityData=null;
async function openQualityGoals(push=true){
  releaseHoverPreviews();disposeStage(false);document.body.classList.remove('entity-open');
  if(push)route('/quality-goals');
  const surface=claimSurface('/quality-goals');
  buildManageBar();$('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#stats').innerHTML=`<div class="review"><p class="empty">${loadingDotsHtml('正在读取')}</p></div>`;
  const next=await api('/api/quality-goals?limit=200');
  if(!surfaceCurrent(surface))return;
  qualityData=next;
  const items=qualityData.items||[];
  $('#stats').innerHTML=`<div class="qualitylist">${items.length?items.map(item=>{
    const preview=item.has_cover?`/cover?code=${encodeURIComponent(item.code||'')}`:`/poster?id=${item.id}&c=4`;
    return `<article class="qualityitem"><button class="qualitycover" data-quality-open="${item.id}" aria-label="打开 ${esc(item.name)}">
        <img src="${preview}" alt="" loading="lazy" onerror="this.remove()"></button>
      <div><h3><button data-middle-truncate data-quality-open="${item.id}">${esc(item.name)}</button></h3>
        <p class="mono">${srcBadge(item.location,item.cost)}<span>${esc(LOC[item.location]||item.location)}</span><span>${fmtDur(item.duration)}</span><span>${fmtSize(item.size||0)}</span></p>
        ${item.reason?`<p>${esc(item.reason)}</p>`:''}</div></article>`}).join(''):emptyState('sparkles','没有标记中的高清版目标','现有版本都已满足条件，或还没有加入追踪。')}</div>`;
  $('#stats').querySelectorAll('[data-quality-open]').forEach(button=>button.onclick=()=>openItem(+button.dataset.qualityOpen));
  window.scrollTo({top:0,behavior:'smooth'});
}

/* ── 在线追更 ──
   两个页面，因为是两件事：
   - `/follow`（左侧导航）是**看**：一张卡片一个作品，点开就去看。本站的 alt 与 WIP
     折进卡片内部，跨站的同一作品折成「另见」，24 条抓取记录才读成 20 个作品。
   - `/follow-manage`（管理区）是**管**：加来源、检查更新、移除来源、看凭据状态，
     以及对内容做批量标记。
   联网只发生在管理页点「检查更新」的那一刻——看的那一页不联网。 */
let followData=null,followRuntime=null,followFilter='new',followBusy=false,followManageSort='checked';
/* 来源筛选：fsrcProviders 记录见过的全部来源（默认全选），
   fsrcUnchecked 只记被取消勾选的——新来源自动进入「全选」。 */
const fsrcProviders=new Set(),fsrcUnchecked=new Set();
let fsrcOpened=null;
if(!globalThis.__peachFsrcCloser){
  globalThis.__peachFsrcCloser=true;
  document.addEventListener('click',event=>{
    if(fsrcOpened&&!fsrcOpened.mount.contains(event.target)){
      fsrcOpened.setOpen(false);fsrcOpened=null}},true);
}
/* 关注页一次取一屏。counts 是全库口径（「未看 2292」），groups 只有这一页——
   两个数并排显示时看起来像自相矛盾，实际是两个口径，所以列表底部要能继续加载。 */
const FOLLOW_PAGE=300;
const followPageUrl=offset=>
  `/api/follow?limit=${FOLLOW_PAGE}&offset=${offset}`
  +(followFilter?`&status=${followFilter}`:'');
/* 分组在取回之后做，所以同一个作品可能被这一页的边界切开：
   前 300 条里有它的一个变体，后 300 条里有另一个。按 release_key 合并，
   不然界面上会出现两张长得几乎一样的卡。 */
function mergeFollowGroups(existing,incoming){
  const byKey=new Map(existing.map(group=>[group.release_key,group]));
  for(const group of incoming){
    const seen=byKey.get(group.release_key);
    if(!seen){byKey.set(group.release_key,group);existing.push(group);continue}
    const ids=new Set([seen.primary,...seen.variants,...seen.duplicates].map(i=>i.id));
    for(const item of [group.primary,...group.variants,...group.duplicates]){
      if(!ids.has(item.id)){seen.variants.push(item);ids.add(item.id)}
    }
  }
  return existing;
}
async function loadMoreFollow(button){
  if(!followData||followBusy)return;
  followBusy=true;
  const oldButton=button?.innerHTML;
  if(button){button.setAttribute('aria-busy','true');button.innerHTML=`${spinnerHtml('加载更多')}<span>加载中…</span>`}
  try{
    const next=await api(followPageUrl((followData.offset||0)+FOLLOW_PAGE));
    followData={...next,
      groups:mergeFollowGroups([...followData.groups],next.groups||[]),
      // counts 一直是全库口径，用新的那份即可；offset/has_more 跟着最新一页走。
      sources:next.sources||followData.sources};
    renderFollow();
  }finally{followBusy=false;if(button){button.removeAttribute('aria-busy');button.innerHTML=oldButton}}
}
let followCredentialProviders=new Set();
/* 上一次检查的结果。检查完页面会整页重画，如果不把结果留在这里，用户看到的就只是
   一次闪烁——他的原话是「完全没返回任何结果」。接口其实每条来源都回了
   added/updated/not_modified/error，是界面把它们全丢了。 */
let followCheckReport=null;
const FOLLOW_FILTERS=[['','全部'],['new','未看'],['seen','已看'],['saved','已保存'],['ignored','已忽略']];

/* 账本里一律存 UTC（ISO 带 Z），界面要按看的人所在时区显示。
   原来直接把那串字面量印出来，UTC+8 的人看到的每个时间都早 8 小时。 */
function localTime(iso){
  if(!iso)return '';
  // 没有时区标记的按 UTC 解释——存进去的时候就是 UTC。
  const text=/[Zz]|[+-]\d\d:?\d\d$/.test(iso)?iso:iso+'Z';
  const when=new Date(text);
  if(isNaN(when))return String(iso).replace('T',' ').slice(0,16);
  const pad=n=>String(n).padStart(2,'0');
  return `${when.getFullYear()}-${pad(when.getMonth()+1)}-${pad(when.getDate())} `
    +`${pad(when.getHours())}:${pad(when.getMinutes())}`;
}

function followWhen(item){
  const raw=item.published_at||'';
  if(!raw)return '时间未取得';
  const text=localTime(raw);
  // 精度仍保留在 API；列表按用户要求不再给近似时间加「约」前缀。
  return text;
}

const followTagType=(item,tag)=>item.tag_types&&item.tag_types[tag]||'general';
const followTagChip=(item,tag,kind='span')=>`<${kind} class="tg r34-${
  esc(followTagType(item,tag))}" data-follow-tag="${esc(tag)}">${esc(tagLabel(tag))}</${kind}>`;

function followBadges(group){
  const badges=[];
  if(group.has_wip)badges.push('<span class="fbadge wip">WIP</span>');
  if(group.primary.version)badges.push(`<span class="fbadge ver">${esc(group.primary.version)}</span>`);
  if(group.variants.length)badges.push(`<span class="fbadge">${
    group.is_release?`${group.variants.length+1} 条动态`:`${group.variants.length} 个版本`}</span>`);
  if(group.duplicates.length)badges.push(`<span class="fbadge dup">另见 ${
    esc([...new Set(group.duplicates.map(d=>d.provider_label))].join('、'))}</span>`);
  return badges.join('');
}

function followCollectionItems(group){
  const seen=new Set();
  return [group.primary,...group.variants,...group.duplicates].filter(item=>{
    if(!item||seen.has(item.id))return false;seen.add(item.id);return true});
}

// F95 的「8 条动态」可能只有一个网盘页，也可能一条实际视频都没有。Mix 是播放
// 语义，只能由已解析、可在 Peach 内播放的视频触发，不能拿回复数或外链数冒充。
function followVideoItems(group){
  return followCollectionItems(group).filter(item=>
    item.playable&&item.media_kind==='video');
}

/* 关注条目和资料页的作品不是同一种 DTO，但媒体切换的语义相同：一个卡片只要
   含对应媒体就进入对应视图。external 只说明有外部文件页，不能再冒充视频；
   没有可验证媒体类型的旧行不进入任一媒体视图。 */
function followItemMediaKinds(item){
  const kinds=new Set();
  const embedded=item.media_items||[];
  if(embedded.length)embedded.forEach(media=>{
    if(media.media_kind==='image'||media.media_kind==='video')kinds.add(media.media_kind)});
  else if(item.media_kind==='image'||item.media_kind==='video')kinds.add(item.media_kind);
  return kinds;
}
const followMediaKinds=group=>{
  const kinds=new Set();
  followCollectionItems(group).forEach(item=>
    followItemMediaKinds(item).forEach(kind=>kinds.add(kind)));
  return kinds;
};
const followItemForMedia=(group,view=followMediaView)=>{
  const wanted=view==='images'?'image':'video';
  return followCollectionItems(group).find(item=>followItemMediaKinds(item).has(wanted))||group.primary;
};

function followMediaNote(item){
  if(item.media_error)return `媒体未取得：${item.media_error}`;
  if(item.media_needs_credential)return followCredentialProviders.has(item.provider)
    ?'已保存 F95 登录会话，等待下次检查重新解析资源'
    :'媒体链接需要 F95 登录会话解析';
  if(item.has_media&&!item.playable&&item.media_kind==='external')return item.resource_urls?.length
    ?`已取得 ${item.resource_urls.length} 个外部文件页；视频列表未取得`
    :'外部文件页未取得；视频列表未取得';
  return '';
}

function followResourceLabel(url){
  try{
    const host=new URL(url).hostname.replace(/^www\./,'');
    return ({'gofile.io':'Gofile','pixeldrain.com':'Pixeldrain','mega.nz':'MEGA',
      'mega.io':'MEGA','mediafire.com':'MediaFire','drive.google.com':'Google Drive'})[host]||host;
  }catch{return '外部文件页'}
}

function followResourceLinks(item){
  const links=item.resource_urls||[];
  if(!links.length)return '';
  return `<div class="followresources">${links.map(url=>
    `<a href="${esc(url)}" target="_blank" rel="noreferrer noopener">${esc(followResourceLabel(url))}${icon('external-link')}</a>`
  ).join('')}</div>`;
}

/* 集合弹层沿用原来的动态语义：线程标题不能冒充每条回复的正文，
   行首则说明它与主条目的关系。 */
function followCollectionCopy(group,item,mark=''){
  let label=mark;
  if(!label&&group.is_release)label=localTime(item.published_at).slice(5,10)||'动态';
  if(!label)label=item.variant_kind==='wip'?'WIP':(item.variant_label||item.variant_kind||'视频');
  const body=group.is_release
    ?(item.summary||(item.has_media?'（仅附件）':'（无正文）')):item.title;
  return {label,title:group.is_release&&item.author?`${item.author}：${body}`:body};
}

function followQueueHtml(group,itemId){
  const items=followVideoItems(group);
  return `<aside class="mixqueue followqueue" data-queue-kind="collection"><div class="mixqueuehead"><div><h2>视频合集</h2><span>${esc(group.primary.title||'未命名合集')} · ${items.length} 个视频</span></div><div class="mixqueueactions">
    <button data-follow-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${items.map(item=>{
      const copy=followCollectionCopy(group,item,group.duplicates.includes(item)?item.provider_label:'');
      const thumb=item.thumb_url
        ?`<img src="${esc(item.thumb_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`
        :`<span class="fnothumb">${sourceIcon(item.provider)}</span>`;
      return `<div class="mixrow"><button class="mixitem ${item.id===itemId?'current':''}" data-follow-queue-item="${item.id}" aria-current="${item.id===itemId?'true':'false'}">
        <span class="mixitempic">${thumb}${item.duration?`<i class="dur mono">${fmtDur(item.duration)}</i>`:''}</span>
        <span class="mixitemtext"><b data-truncate-end>${esc(copy.title)}</b><span data-truncate-end><i class="fvkind ${esc(item.variant_kind||'')}">${esc(copy.label)}</i>${followWhen(item)}</span></span></button></div>`;
    }).join('')}</div></aside>`;
}

function followEmbeddedQueueHtml(item,mediaIndex){
  const items=item.media_items||[];
  return `<aside class="mixqueue followqueue" data-queue-kind="media"><div class="mixqueuehead"><div><h2>多媒体</h2><span>${esc(item.title||'未命名内容')} · ${items.length} 个媒体</span></div><div class="mixqueueactions">
    <button data-follow-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${items.map(media=>{
      const thumb=media.thumb_url
        ?`<img src="${esc(media.thumb_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`
        :`<span class="fnothumb">${sourceIcon(media.resource_provider||item.provider)}</span>`;
      return `<div class="mixrow"><button class="mixitem ${media.index===mediaIndex?'current':''}" data-follow-media-item="${media.index}" data-media-kind="${media.media_kind}" aria-current="${media.index===mediaIndex?'true':'false'}">
        <span class="mixitempic">${thumb}</span><span class="mixitemtext"><b data-middle-truncate>${esc(media.name)}</b><span data-truncate-end>${media.media_kind==='image'?'图片':'视频'}</span></span></button></div>`;
    }).join('')}</div></aside>`;
}

function indexFollowItems(data){
  const groups=data?.groups||[];
  followItemsById=new Map();followGroupByItemId=new Map();
  groups.forEach(group=>followCollectionItems(group).forEach(item=>{
    followItemsById.set(item.id,item);followGroupByItemId.set(item.id,group)}));
}

async function followItemById(id){
  if(followItemsById.has(id))return followItemsById.get(id);
  const data=await api(`/api/follow?item=${encodeURIComponent(id)}`);
  if(!followData)followData=data;
  indexFollowItems(data);
  return followItemsById.get(id);
}

async function openFollowDetail(id,push=true,mediaIndex=null,preserveReturn=false){
  releaseHoverPreviews();
  const entering=!location.pathname.startsWith('/follow/item/');
  if(push&&entering)followDetailReturnPath=location.pathname+location.search;
  if(!push&&!preserveReturn)followDetailReturnPath='/follow';
  const item=await followItemById(+id);if(!item)return;
  const group=followGroupByItemId.get(item.id);
  const embedded=item.media_items||[];
  const preferredKind=followMediaView==='images'?'image':'video';
  const preferredMedia=embedded.find(media=>media.media_kind===preferredKind)||embedded[0];
  const selectedMedia=embedded.length
    ?embedded.find(media=>media.index===(mediaIndex??preferredMedia.index))||preferredMedia
    :null;
  const imageMedia=embedded.filter(media=>media.media_kind==='image');
  const imagePosition=imageMedia.findIndex(media=>media.index===selectedMedia?.index);
  const imageCarousel=imageMedia.length>1&&imagePosition>=0;
  const embeddedQueue=embedded.length>1&&!imageCarousel;
  const collection=!embedded.length&&group&&followVideoItems(group).length>1?group:null;
  disposeStage(false);
  if(push)route(`/follow/item/${item.id}`);
  const source=(followData?.sources||[]).find(row=>row.id===item.source_id);
  const authorSources=(followData?.sources||[]).filter(row=>
    source?.author_key&&row.author_key===source.author_key);
  if(!authorSources.length&&source)authorSources.push(source);
  const src=item.playable?`/follow-stream?id=${item.id}${selectedMedia?`&media=${selectedMedia.index}`:''}`:'';
  const selectedKind=selectedMedia?.media_kind||item.media_kind;
  const media=item.playable&&selectedKind==='video'
    ?`<video class="video-js vjs-big-play-centered" controls playsinline preload="metadata"></video>`
    :item.playable&&selectedKind==='image'
      ?`<img class="followdetailposter" src="${src}" alt="${esc(item.title)}">`
      :item.thumb_url
        ?`<img class="followdetailposter" src="${esc(item.thumb_url)}" alt="${esc(item.title)}" referrerpolicy="no-referrer">`
        :`<div class="followdetailplaceholder">${sourceIcon(item.provider)}<span>没有可用预览</span></div>`;
  const imageControls=imageCarousel?`<button class="followimagearrow prev" data-follow-image-step="-1" aria-label="上一张图片" title="上一张">${icon('chevron-left')}</button>
    <button class="followimagearrow next" data-follow-image-step="1" aria-label="下一张图片" title="下一张">${icon('chevron-right')}</button>
    <div class="followimagedots" role="group" aria-label="${imageMedia.length} 张图片">${imageMedia.map((image,index)=>`<button data-follow-image-item="${image.index}" aria-current="${index===imagePosition}" aria-label="第 ${index+1} 张，共 ${imageMedia.length} 张" title="第 ${index+1} 张"></button>`).join('')}</div>`:'';
  const badges=followBadges({primary:item,variants:[],duplicates:[],has_wip:item.variant_kind==='wip'});
  const tags=(item.tags||[]).map(tag=>followTagChip(item,tag,'button')).join('');
  const author=followAuthorName(authorSources)||item.author||item.source_label||'作者未取得';
  const postedBy=item.author&&foldName(item.author)!==foldName(author)?item.author:'';
  // 关注列表的头像与筛选就是详情的上文；舞台放在筛选和卡片网格之间，
  // 不再占用 main 最顶部、把用户从原来的筛选上下文里切走。
  const followList=$('#stats').querySelector('.followlist');
  if(followList)followList.before($('#stage'));
  $('#stage').hidden=false;document.body.classList.add('detail-open');
  $('#stage').innerHTML=`<div class="sgrid followdetailgrid${collection||embeddedQueue?' mixgrid':''}">
    <div class="vwrap followdetailmedia${selectedKind==='image'?' image':''}">${selectedKind==='video'?'<canvas class="ambientcanvas" width="32" height="18"></canvas>':''}<button class="closestage" id="closeStage" title="关闭" aria-label="关闭">${icon('x')}</button>${media}${imageControls}</div>
    ${embeddedQueue?followEmbeddedQueueHtml(item,selectedMedia.index):(collection?followQueueHtml(collection,item.id):'')}
    <div class="side followdetailside"><div class="sidecontent">
      <div class="followdetailtitle"><div class="stitle">${esc(item.title)}</div>${item.url?`<a class="followorigin" href="${esc(item.url)}" target="_blank" rel="noreferrer noopener" title="打开来源页面" aria-label="打开来源页面">${icon('external-link')}</a>`:''}</div>
      <div class="followdetailidentity"><span class="mav fsourceavatar">${followAuthorAvatar(authorSources)}</span>
        <div><b>${esc(author)}</b>${postedBy?`<span>发布者 ${esc(postedBy)}</span>`:''}</div></div>
      <div class="smeta mono"><span>${followWhen(item)}</span>${item.duration?`<span>${fmtDur(item.duration)}</span>`:''}${badges?`<span class="fbadges">${badges}</span>`:''}</div>
      ${item.summary?`<p class="followdetailsummary">${esc(item.summary)}</p>`:''}
      ${tags?`<div class="stags followdetailtags">${tags}</div>`:''}
      ${followMediaNote(item)?`<p class="fnote followmedianote">${esc(followMediaNote(item))}</p>`:''}
      ${followResourceLinks(item)}
      <div class="fb followdetailactions">
        <button class="later" data-follow-detail-save aria-label="${item.status==='saved'?'已保存':'保存到账本'}" title="${item.status==='saved'?'已保存':'保存到账本'}"${item.status==='saved'?' disabled':''}>${item.status==='saved'?icon('check'):icon('bookmark-plus')}</button>
        <button class="seen" data-follow-detail-status="seen" aria-label="标记已看" title="标记已看" aria-pressed="${item.status==='seen'}">${icon('eye')}</button>
        <button class="dislike" data-follow-detail-status="ignored" aria-label="忽略" title="忽略" aria-pressed="${item.status==='ignored'}">${icon('eye-off')}</button>
        ${item.status==='seen'||item.status==='ignored'?`<button data-follow-detail-status="new" aria-label="恢复未看" title="恢复未看">${icon('rotate-ccw')}</button>`:''}</div>
      <span class="fstate" aria-live="polite"></span>
    </div></div></div>`;
  $('#stage').classList.toggle('ambient-on',selectedKind==='video'&&appSettings.ambientMode);
  $('#stage').classList.toggle('theater-mode',selectedKind==='video'&&appSettings.theaterMode);
  const closeDetail=async()=>{disposeStage(false);route(followDetailReturnPath||'/follow');await openFollow(false)};
  $('#closeStage').onclick=closeDetail;
  $('#stage').querySelectorAll('[data-follow-queue-close]').forEach(button=>button.onclick=closeDetail);
  $('#stage').querySelectorAll('[data-follow-queue-item]').forEach(button=>button.onclick=()=>
    openFollowDetail(+button.dataset.followQueueItem,true));
  $('#stage').querySelectorAll('[data-follow-media-item]').forEach(button=>button.onclick=()=>
    openFollowDetail(item.id,false,+button.dataset.followMediaItem,true));
  const switchImage=index=>openFollowDetail(item.id,false,+index,true);
  $('#stage').querySelectorAll('[data-follow-image-item]').forEach(button=>button.onclick=()=>
    switchImage(button.dataset.followImageItem));
  $('#stage').querySelectorAll('[data-follow-image-step]').forEach(button=>button.onclick=()=>{
    const next=(imagePosition+(+button.dataset.followImageStep)+imageMedia.length)%imageMedia.length;
    switchImage(imageMedia[next].index);
  });
  const followVideo=$('#stage').querySelector('.followdetailmedia>video');
  if(followVideo){
    const followPlayer=mountDetailPlayer(item,followVideo,false,{
      source:{src,type:selectedMedia?.media_type||item.media_type||'video/mp4'},
      checkSourceStatus:false
    });
    const stopFollowAmbient=mountPlayerAmbient(followVideo);
    followPlayer?.one?.('dispose',stopFollowAmbient);
    followVideo.addEventListener('emptied',stopFollowAmbient,{once:true});
    wireFollowTelemetry(item,followVideo);
  }
  wireDrag($('#stage').querySelector('.mixlist'));
  $('#stage').querySelectorAll('.followdetailtags [data-follow-tag]').forEach(button=>button.onclick=async()=>{
    const tag=button.dataset.followTag;
    if(followTags.has(tag))followTags.delete(tag);else followTags.add(tag);
    await closeDetail();
  });
  const write=async(button,path,body,done)=>{
    const state=$('#stage').querySelector('.fstate');button.disabled=true;
    try{await api(path,{method:'POST',body:JSON.stringify(body)});done();state.textContent='已更新'}
    catch(error){button.disabled=false;state.textContent=error.message||'操作失败'}
  };
  $('#stage').querySelector('[data-follow-detail-save]')?.addEventListener('click',event=>{
    const button=event.currentTarget;
    write(button,'/api/follow/save',{item:item.id},()=>{
      item.status='saved';button.innerHTML=icon('check');button.title='已保存';button.setAttribute('aria-label','已保存')});
  });
  $('#stage').querySelectorAll('[data-follow-detail-status]').forEach(button=>button.onclick=()=>
    write(button,'/api/follow/status',{item:item.id,to:button.dataset.followDetailStatus},()=>{
      item.status=button.dataset.followDetailStatus;
      $('#stage').querySelectorAll('[data-follow-detail-status]').forEach(control=>
        control.setAttribute('aria-pressed',String(control.dataset.followDetailStatus===item.status)))}));
  alignFollowImageControls();
  ($('#stats').querySelector('.followhead')||$('#stage')).scrollIntoView({block:'start',behavior:'smooth'});
}

/* object-fit:contain 后图片左右黑边会随图片比例和窗口改变。箭头应位于黑边的视觉中心，
   不能永远贴容器边缘；黑边太窄时才退回原来的安全内边距。 */
function alignFollowImageControls(){
  const frame=$('#stage:not([hidden]) .followdetailmedia');
  const image=frame?.querySelector('.followdetailposter');
  const arrow=frame?.querySelector('.followimagearrow');
  if(!frame||!image||!arrow)return;
  const align=()=>{
    if(!image.naturalWidth||!image.naturalHeight)return;
    const box=frame.getBoundingClientRect(),ratio=image.naturalWidth/image.naturalHeight;
    const renderedWidth=Math.min(box.width,box.height*ratio);
    const gutter=Math.max(0,(box.width-renderedWidth)/2);
    const fallback=matchMedia('(max-width:640px)').matches?10:16;
    const inset=gutter>=arrow.offsetWidth+fallback*2?(gutter-arrow.offsetWidth)/2:fallback;
    frame.style.setProperty('--follow-image-arrow-inset',`${Math.round(inset)}px`);
  };
  if(image.complete)requestAnimationFrame(align);
  else image.addEventListener('load',align,{once:true});
}

function wireFollowDetail(root){
  root.querySelectorAll('[data-follow-detail]').forEach(button=>button.onclick=event=>{
    event.preventDefault();event.stopPropagation();
    if(root.matches?.('dialog'))root.close();
    openFollowDetail(+button.dataset.followDetail)});
}

function followCard(group,authorSources=[]){
  const item=followItemForMedia(group);
  const imageView=followMediaView==='images';
  const selectedMedia=imageView?(item.media_items||[]).find(media=>media.media_kind==='image'):null;
  const thumbUrl=selectedMedia?.thumb_url||item.thumb_url;
  const thumb=thumbUrl
    ? `<img src="${esc(thumbUrl)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`
    : `<span class="fnothumb">${esc(item.provider_label)}</span>`;
  const videos=followMediaView==='videos'?followVideoItems(group):[],embedded=item.media_items||[];
  const isMix=embedded.length>1||videos.length>1;
  const mixCount=embedded.length>1?embedded.length:videos.length;
  const mixKind=embedded.length&&embedded.every(media=>media.media_kind==='image')?'图片'
    :embedded.length&&embedded.some(media=>media.media_kind==='image')?'媒体':'视频';
  const mixTarget=embedded.length>1?item.id:videos[0]?.id;
  const badges=followBadges(group);
  const tags=(item.tags||[]).slice(0,3).map(tag=>followTagChip(item,tag)).join('');
  const open=`<button class="cardopenhit" data-follow-detail="${item.id}" aria-label="打开 ${esc(item.title)} 详情"></button>`;
  return `<article class="card followitem${isMix?' collection':''}${imageView?' imagecard':''}" data-follow-item="${item.id}" data-status="${esc(item.status)}">
    <div class="${isMix?'mixstack ':''}followvisual"><div class="pic">
      ${open}${thumb}
      <span class="badge" title="${esc(item.provider_label)}" aria-label="来源：${esc(item.provider_label)}">${sourceIcon(item.provider)}</span>
      <span class="selectionMark">${icon('check')}</span>${item.duration?`<span class="dur mono">${fmtDur(item.duration)}</span>`:''}
      ${isMix?`<button class="mixbadge" data-follow-collection="${mixTarget}">${icon('play')}${mixCount} 个${mixKind}</button>`:''}
      <div class="factions">
        <button data-follow-save="${item.id}" title="${item.status==='saved'?'已保存':'保存到账本'}" aria-label="${item.status==='saved'?'已保存':'保存到账本'}"${item.status==='saved'?' disabled':''}>${item.status==='saved'?icon('check'):icon('bookmark-plus')}</button>
        <button data-follow-status="${item.id}" data-to="seen" title="标记已看" aria-label="标记已看"${item.status==='seen'?' disabled':''}>${icon('eye')}</button>
        <button data-follow-status="${item.id}" data-to="ignored" title="忽略" aria-label="忽略"${item.status==='ignored'?' disabled':''}>${icon('eye-off')}</button>
        ${item.status==='seen'||item.status==='ignored'?`<button data-follow-status="${item.id}" data-to="new" title="恢复未看" aria-label="恢复未看">${icon('rotate-ccw')}</button>`:''}
      </div></div></div>
    <div class="meta"><span class="mav fsourceavatar" title="作者头像">${followAuthorAvatar(authorSources)}</span>
      <div class="mtext"><button class="t cardtitle" data-follow-detail="${item.id}">${esc(item.title)}</button>
        <div class="s mono"><span>${followWhen(item)}</span>${badges?`<span class="fbadges">${badges}</span>`:''}</div>
        ${tags?`<div class="ctags">${tags}</div>`:''}${followMediaNote(item)?`<span class="fnote">${esc(followMediaNote(item))}</span>`:''}</div></div>
    <span class="fstate" aria-live="polite"></span></article>`;
}

/* 检查完必须说清三件事：新增了什么、哪些确实没有更新、哪些失败了以及为什么。
   反馈走两条通道（Geist toast 处方，取证见 docs/reference-snapshots/vercel-geist-toast.md）：
   「检查了 N 个来源」是用户主动动作的非阻塞回执 → toast，自动消失；
   失败是「不跟进就会一直漏更新」的事 → 摘要里只留一句短提示，原因和
   恢复入口放进页内的持久行（followCheckFailNote），关掉 toast 也还在。 */
function followCheckBits(report){
  const rows=report.results||[];
  const added=rows.reduce((n,r)=>n+(r.added||0),0);
  const updated=rows.reduce((n,r)=>n+(r.updated||0),0);
  const quiet=rows.filter(r=>r.ok&&!r.added&&!r.updated).length;
  const skipped=rows.reduce((n,r)=>n+(r.skipped||0),0);
  const compilations=rows.reduce((n,r)=>n+(r.skipped_compilations||0),0);
  const bits=[];
  if(added)bits.push(`新增 <b>${added}</b> 条`);
  if(updated)bits.push(`更新 <b>${updated}</b> 条`);
  // 过滤掉多少也要说：不然用户只看到条目变少，分不清是被过滤了还是根本没抓到。
  if(skipped-compilations)bits.push(`跳过 <b>${skipped-compilations}</b> 条无资源`);
  if(compilations)bits.push(`排除 <b>${compilations}</b> 个超大合集`);
  // 回查是唯一会放大请求数的路径，报出来才看得出某个作者是不是每帖都要多打一次站点。
  const probed=rows.reduce((n,r)=>n+(r.probed||0),0);
  if(probed)bits.push(`回查 <b>${probed}</b> 条`);
  if(quiet)bits.push(`${quiet} 个来源没有更新`);
  if(!bits.length)bits.push('没有任何更新');
  return {rows,bits};
}
function followCheckToast(report){
  const {rows,bits}=followCheckBits(report);
  const failed=rows.filter(r=>!r.ok).length;
  const exhausted=rows.filter(r=>r.exhausted).length;
  toast(`检查了 <b>${rows.length}</b> 个来源：${bits.join(' · ')}`+
    (exhausted?` · <b>${exhausted} 个没有更多内容</b>`:'')+
    (failed?` · <b>${failed} 个失败</b>`:''),
    {warn:!!failed,timeout:failed?8000:6000,
     action:{label:'去看更新',run:()=>openFollow()}});
}
/* 页内持久行：只装失败与取证缺档，渲染在管理页自己的检查区里。全部成功时
   返回空串——成功摘要整条交给 toast，页面上不再出现通栏横条。关注页不渲染
   这块：那里的持久行是 .fwarn，带「去管理关注」的恢复入口。 */
function followCheckFailNote(report){
  const rows=report.results||[];
  const failed=rows.filter(r=>!r.ok);
  const exhausted=rows.filter(r=>r.exhausted);
  const evidence=rows.filter(r=>r.evidence_error);
  if(!failed.length&&!evidence.length&&!exhausted.length)return '';
  const dismiss=`<button type="button" class="wclose" data-follow-report-dismiss
    aria-label="关闭检查结果">${icon('x')}</button>`;
  const ended=exhausted.length?`<div class="geist-note geist-note-secondary fcheckreport neutral" role="note">
    ${icon('info')}<div><p><b>${exhausted.length} 个来源没有更多内容</b></p>
    ${exhausted.map(row=>`<p class="fchecknote">${esc([row.provider_label||row.provider,row.ref]
      .filter(Boolean).join(' '))}：没有更多历史内容</p>`).join('')}</div>${dismiss}</div>`:'';
  const errors=failed.length||evidence.length?`<div class="geist-note geist-note-error fcheckreport" role="alert">${icon('alert')}<div>
    ${failed.length?`<p><b>${failed.length} 个来源检查失败</b></p>`:''}
    ${failed.map(row=>`<p class="fcheckfail">${esc([row.provider_label||row.provider,row.ref]
      .filter(Boolean).join(' '))}${row.provider?'：':''}${esc(row.error||'未说明原因')}</p>`).join('')}
    ${evidence.length?`<p class="fchecknote">候选已入库，但这一次的原始响应没有留档：${
      esc(evidence[0].evidence_error)}</p>`:''}
  </div>${dismiss}</div>`:'';
  return `<div class="fcheckreports">${ended}${errors}</div>`;
}

/* ── 看的那一页 ── */
let followAuthor='',followProvider='',followTags=new Set(),followMediaView='videos',followGroupByItemId=new Map(),followItemsById=new Map(),followDetailReturnPath='/follow';
function followViewPath(){
  const params=new URLSearchParams();
  if(followAuthor)params.set('author',followAuthor);
  if(followMediaView==='images')params.set('media','images');
  const search=params.toString();return '/follow'+(search?'?'+search:'');
}
function followMediaControl(counts){
  if(!counts.images)return '';
  return mediaViewButtonsHtml({active:followMediaView,videoCount:counts.videos,imageCount:counts.images});
}
function groupTagType(groups,tag){
  for(const group of groups){
    const type=group.primary&&group.primary.tag_types&&group.primary.tag_types[tag];
    if(type)return type;
  }
  return 'general';
}
function renderFollow(){
  const groups=followData.groups||[],counts=followData.counts||{};
  indexFollowItems(followData);
  const sources=followData.sources||[];
  const broken=sources.filter(s=>s.last_status==='error'||s.last_status==='unauthorized');
  const byId=new Map(sources.map(source=>[source.id,source]));
  const sourceOf=group=>byId.get(group.primary&&group.primary.source_id);
  const authorSources=new Map(),activeAuthors=new Set(),providers=new Map(),tagCounts=new Map();
  sources.forEach(source=>{
    if(!source.author_key)return;
    if(!authorSources.has(source.author_key))authorSources.set(source.author_key,[]);
    authorSources.get(source.author_key).push(source);
  });
  groups.forEach(group=>{
    (group.primary&&group.primary.tags||[]).forEach(tag=>
      tagCounts.set(tag,(tagCounts.get(tag)||0)+1));
    const source=sourceOf(group);if(!source)return;
    if(source.author_key)activeAuthors.add(source.author_key);
    if(!providers.has(source.provider))providers.set(source.provider,source.provider_label);
  });
  const authors=new Map([...authorSources].filter(([key])=>activeAuthors.has(key)).map(([key,list])=>[key,{
    name:followAuthorName(list),sources:list,
  }]));
  const rankedTags=[...tagCounts].sort((a,b)=>b[1]-a[1]);
  const topTagRows=rankedTags.slice(0,20);
  followTags.forEach(tag=>{
    if(tagCounts.has(tag)&&!topTagRows.some(([key])=>key===tag))
      topTagRows.push([tag,tagCounts.get(tag)]);
  });
  const topTags=topTagRows.map(([tag,n])=>[tag,tagLabel(tag),n]);
  if(followAuthor&&!authors.has(followAuthor))followAuthor='';
  if(followProvider&&!providers.has(followProvider))followProvider='';
  followTags=new Set([...followTags].filter(tag=>tagCounts.has(tag)));
  const filtered=groups.filter(group=>{
    const source=sourceOf(group);
    if(!source)return !followAuthor&&!followProvider;
    if(followAuthor&&source.author_key!==followAuthor)return false;
    if(followProvider&&source.provider!==followProvider)return false;
    if(followTags.size&&![...followTags].every(tag=>(group.primary&&group.primary.tags||[]).includes(tag)))return false;
    return true;
  });
  const mediaCounts={videos:0,images:0};
  filtered.forEach(group=>followMediaKinds(group).forEach(kind=>
    mediaCounts[kind==='image'?'images':'videos']++));
  const requestedMediaView=followMediaView;
  if(followMediaView==='images'&&!mediaCounts.images)followMediaView='videos';
  if(followMediaView==='videos'&&!mediaCounts.videos&&mediaCounts.images)followMediaView='images';
  if(requestedMediaView!==followMediaView&&location.pathname==='/follow')route(followViewPath(),true);
  const wantedKind=followMediaView==='images'?'image':'video';
  const visible=filtered.filter(group=>followMediaKinds(group).has(wantedKind));
  const providerPills=[...providers].map(([key,label])=>
    `<button class="pill sourcepill" data-follow-provider="${esc(key)}" aria-pressed="${key===followProvider}"
      title="${esc(label)}" aria-label="来源：${esc(label)}">${sourceIcon(key)}</button>`).join('');
  const allCount=Object.values(counts).reduce((total,count)=>total+(+count||0),0);
  $('#stats').innerHTML=`<div class="follow">
    <div class="followhead"><h2 class="disp pagetitle">关注</h2>
      <button class="fbtn primary fcheck" data-follow-manage>${icon('settings')}管理关注</button></div>
    ${authors.size?`<div class="tier followauthors" aria-label="按作者筛选">${[...authors].map(([key,author])=>
      `<button class="av" data-follow-author="${esc(key)}" aria-pressed="${key===followAuthor}">
        <span class="ring">${followAuthorAvatar(author.sources)}</span><span class="nm">${esc(author.name)}</span></button>`
      ).join('')}</div>`:''}
    <div class="tagbar followfilters" aria-label="关注筛选">${followMediaControl(mediaCounts)}${FOLLOW_FILTERS.map(([key,label])=>
      `<button class="pill" data-follow-filter="${key}" aria-pressed="${key===followFilter}">${label}${
        ` <span class="n mono">${key?counts[key]||0:allCount}</span>`}</button>`).join('')}
      ${providerPills?`<span class="sep" aria-hidden="true"></span>${providerPills}`:''}
      ${topTags.length?`<span class="sep" aria-hidden="true"></span>`+
        topTags.map(([key,label,n])=>
          `<button class="pill r34-${esc(groupTagType(groups,key))}" data-follow-tag="${esc(key)}" aria-pressed="${followTags.has(key)}">${
            esc(label)}${n?` <span class="n mono">${n}</span>`:''}</button>`).join(''):''}</div>
    ${broken.length&&!sessionStorage.getItem('peach-fwarn-dismissed')
      ?`<p class="geist-banner fwarn">${icon('alert')}<span>${broken.length} 个来源上次检查失败，去<button class="flink" data-follow-manage>管理关注</button>看原因。</span><button class="wclose" data-fwarn-dismiss title="本次会话不再显示" aria-label="关闭提醒">${icon('x')}</button></p>`:''}
    <div class="followlist${followMediaView==='images'?' followphotowall':''}">${visible.length?visible.map(group=>{
      const source=sourceOf(group),siblings=source&&authorSources.get(source.author_key)||[];
      return followCard(group,siblings)}).join('')
      :groups.length?emptyState('layout-grid','当前筛选下没有更新','切换媒体类型、作者、来源或标签后再试。')
      :sources.length?emptyState('rss','没有符合条件的更新','切换状态或来源筛选后再试。')
      :emptyState('rss','还没有关注任何来源','添加作者或订阅来源后，更新会集中显示在这里。',{actions:'<button class="fbtn primary" data-follow-manage>添加关注</button>'})}</div>
    ${followData.has_more||sources.some(source=>source.can_backfill)?`<div class="followpagination">
      ${followData.has_more?`<span class="followpageaction"><button class="fbtn" data-follow-more>${icon('refresh-cw')}加载更多</button>
        <span class="fmeta">已显示 ${visible.length.toLocaleString()} / ${
        (counts[followFilter]||0).toLocaleString()} 项</span></span>`:''}
      ${sources.some(source=>source.can_backfill)?`<span class="followpageaction"><button class="fbtn" data-follow-older>${icon('history')}抓更早的一页</button>
        <span class="fmeta">${esc(followBackfillState(sources))}</span></span>`:''}</div>`:''}</div>`;
  /* 滚到底自动续取，按钮只是兜底（观察器不可用、或用户用键盘跳到底部）。
     照搬实体合集那套：按钮观察自己，进视口就触发——用户不必先看懂
     「未看 3036」和「已显示 152」是两个口径，一直往下滚就是了。 */
  const more=$('#stats').querySelector('[data-follow-more]');
  if(more){
    more.onclick=()=>loadMoreFollow(more);
    more._observer?.disconnect();
    more._observer=new IntersectionObserver(
      entries=>{if(entries.some(x=>x.isIntersecting))loadMoreFollow(more)},
      {rootMargin:'320px'});
    more._observer.observe(more);
  }
  wireFollowItems();
  wireFollowOlder();
  wireDrag($('#stats').querySelector('.followauthors'));
  wireDrag($('#stats').querySelector('.followfilters'));
  paintSelection();
  $('#stats').querySelectorAll('[data-follow-filter]').forEach(button=>button.onclick=()=>{
    followFilter=button.dataset.followFilter;openFollow(false)});
  $('#stats').querySelectorAll('.followfilters [data-media-view]').forEach(button=>button.onclick=()=>{
    followMediaView=button.dataset.mediaView;
    route(followViewPath());renderFollow()});
  $('#stats').querySelectorAll('[data-follow-author]').forEach(button=>button.onclick=()=>{
    followAuthor=followAuthor===button.dataset.followAuthor?'':button.dataset.followAuthor;
    route(followViewPath());renderFollow()});
  $('#stats').querySelectorAll('[data-follow-provider]').forEach(button=>button.onclick=()=>{
    followProvider=followProvider===button.dataset.followProvider?'':button.dataset.followProvider;renderFollow()});
  $('#stats').querySelectorAll('[data-follow-tag]').forEach(button=>button.onclick=()=>{
    const tag=button.dataset.followTag;
    if(followTags.has(tag))followTags.delete(tag);else followTags.add(tag);renderFollow()});
  $('#stats').querySelectorAll('[data-follow-manage]').forEach(button=>
    button.onclick=()=>openFollowManage());
  $('#stats').querySelectorAll('[data-fwarn-dismiss]').forEach(button=>button.onclick=()=>{
    sessionStorage.setItem('peach-fwarn-dismissed','1');renderFollow()});
}

/* 往回抓到哪儿了。不说的话，用户点一次只看到列表变长一点，不知道自己走到第几页，
   也不知道还要点几次。页码是 0 起的游标（0 = 只抓过第一页），显示成人读的第几页。 */
function followBackfillState(sources){
  const pages=sources.filter(source=>source.can_backfill)
    .map(source=>(source.backfill_page||0)+1);
  if(!pages.length)return '';
  const deepest=Math.max(...pages), shallowest=Math.min(...pages);
  if(deepest<=1)return '每个来源都只抓了第 1 页';
  return shallowest===deepest
    ? `每个来源都抓到第 ${deepest} 页`
    : `已抓到第 ${shallowest}–${deepest} 页`;
}

/* 一次只往回一页。追更的常规检查永远只看第一页——每次都从头翻一遍站点既慢又没必要；
   但那也意味着每个来源只有第一页那点内容，用户问「怎么这么少」就是这个原因。
   所以往回抓是一个独立的、显式的动作，点一次走一页，不自动、不连翻。 */
function wireFollowOlder(){
  const button=$('#stats').querySelector('[data-follow-older]');
  if(!button)return;
  button.onclick=async()=>{
    if(followBusy)return;
    followBusy=true;button.setAttribute('aria-busy','true');
    button.innerHTML=loadingDotsHtml('抓取中…');
    try{
      followCheckReport=await api('/api/follow/check',
        {method:'POST',body:JSON.stringify({older:true})});
      followCheckToast(followCheckReport);
      await openFollow(false);
    }catch(error){
      followCheckReport={results:[{ok:false,error:error.message}]};
      followCheckToast(followCheckReport);
      await openFollow(false);
    }finally{followBusy=false;button.removeAttribute('aria-busy')}
  };
}

async function openFollow(push=true,renderForDetail=false){
  releaseHoverPreviews();disposeStage(false);
  document.body.classList.remove('entity-open','index-open');
  if(push){followAuthor='';followMediaView='videos';route('/follow')}
  else if(location.pathname==='/follow'){
    const params=new URLSearchParams(location.search);
    followAuthor=params.get('author')||'';
    followMediaView=params.get('media')==='images'?'images':'videos';
  }
  const surface=claimSurface(renderForDetail?surfacePath():'/follow');
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#tiers').style.display='none';$('#tagbar').style.display='none';
  $('#managebar').hidden=true;$('#manageTitle').hidden=true;buildEdge();
  $('#stats').innerHTML=`<div class="follow"><p class="empty">${loadingDotsHtml('正在读取')}</p></div>`;
  const [data,credentials]=await Promise.all([
    api(followPageUrl(0)),
    api('/api/follow/credentials').catch(()=>({providers:[]})),
  ]);
  if(!surfaceCurrent(surface))return;
  followData=data;
  followCredentialProviders=new Set((credentials.providers||[])
    .filter(provider=>provider.present).map(provider=>provider.provider));
  if(!surfaceCurrent(surface))return;
  renderFollow();
  if(!renderForDetail)window.scrollTo({top:0,behavior:'smooth'});
}

/* ── 管的那一页 ── */
/* 同一个作者在不同站点上是多条来源、一个人。用户截图里 `LazyProcrastinator · fanbox`
   出现两次（Kemono / Pawchive）、`lazyprocrastinator` 出现两次（Rule34Video /
   Rule34.xxx），四行读起来像四个人。归组用后端给的 `author_key`——那是实体 id
   或归一化后的名字，不在前端二次猜。

   注意这跟卡片里的变体折叠不是同一个轴：那个折的是同一条发布的多个版本，
   这里折的是同一个人的多个来源。 */
function followAuthorGroups(sources){
  const order=[],byKey=new Map();
  sources.forEach(source=>{
    const key=source.author_key||`source:${source.id}`;
    if(!byKey.has(key)){byKey.set(key,[]);order.push(key)}
    byKey.get(key).push(source);
  });
  const groups=order.map(key=>byKey.get(key));
  const name=group=>followAuthorName(group);
  const checked=group=>Math.max(...group.map(source=>Date.parse(source.last_checked_at||'')||0));
  return groups.sort((a,b)=>{
    if(followManageSort==='name')return name(a).localeCompare(name(b),'zh-CN',{numeric:true});
    if(followManageSort==='sources')return b.length-a.length||name(a).localeCompare(name(b),'zh-CN',{numeric:true});
    return checked(b)-checked(a)||name(a).localeCompare(name(b),'zh-CN',{numeric:true});
  });
}

/* 这些地址来自各站实际声明的图标；内容哈希变更或站点拒绝外链时退回纯文字。 */
const SOURCE_ICONS={
  fanbox:'https://www.fanbox.cc/favicon.ico',
  patreon:'https://www.patreon.com/favicon.ico',
  subscribestar:'https://assets.subscribestar.com/assets/public/images/favicons/favicon-32x32-b9aa1e7e5bab6cb1b28b5161e16f9d42.png',
  kemono:'https://kemono.cr/assets/favicon-CPB6l7kH.ico',
  coomer:'https://coomer.st/assets/favicon-CPB6l7kH.ico',
  pawchive:'https://pawchive.pw/static/favicon.png',
  rule34video:'https://rule34video.com/favicon-32x32.png',
  rule34xxx:'https://rule34.xxx/favicon.ico',
  rule34paheal:'https://rule34.paheal.net/favicon.ico',
  gofile:'https://gofile.io/favicon.ico',
  f95zone:'https://f95zone.to/assets/favicon-32x32.png',
};
const sourceIcon=provider=>SOURCE_ICONS[provider]
  ? `<img class="ficon" src="${esc(SOURCE_ICONS[provider])}" alt="" loading="lazy"
       referrerpolicy="no-referrer" onerror="this.remove()">`
  : '';

function followAvatarInitial(group){
  const name=followAuthorName(group).trim();
  const ascii=name.match(/[A-Za-z0-9]/);
  return (ascii?ascii[0]:Array.from(name)[0]||'?').toUpperCase();
}

/* 同一作者的官方来源优先提供头像，归档来源只回退。都取不到时明确用作者首字母，
   不再从某条来源的中文显示标签切出“初”“一”之类与作者无关的字。 */
function followAuthorAvatar(group){
  const official=group.find(source=>source.official_avatar_url);
  const mirror=group.find(source=>source.avatar_url);
  const src=official?.official_avatar_url||mirror?.avatar_url;
  const fallback=official&&mirror&&mirror.avatar_url!==src?mirror.avatar_url:'';
  const initial=followAvatarInitial(group);
  if(src)return `<img class="favatar" src="${esc(src)}" alt="" data-initial="${esc(initial)}"
    ${fallback?`data-fallback="${esc(fallback)}"`:''}
    loading="lazy" referrerpolicy="no-referrer" onerror="if(!this.dataset.f&&this.dataset.fallback){
      this.dataset.f='1';this.src=this.dataset.fallback}else{this.replaceWith(
      Object.assign(document.createElement('span'),{className:'favatar none',textContent:this.dataset.initial}))}">`;
  return `<span class="favatar none" title="没有可用头像">${esc(initial)}</span>`;
}

/* 分组标题要用作者本人的名字，不是某一条来源的标签。`LazyProcrastinator · fanbox`
   里「· fanbox」只说明他在哪个平台连载——四条来源合成一组之后还挂着其中一条的
   平台后缀，等于说这一组只属于 fanbox，那正是这次要消掉的误读。
   同名的几种写法里取大写最多的那个：`LazyProcrastinator` 比 `lazyprocrastinator`
   更像作者自己写的名字。 */
function followAuthorName(group){
  if(!group.length)return '';
  const entity=group.find(source=>source.entity_name);
  if(entity)return entity.entity_name;
  const aliasGroup=(followData.author_aliases||[]).find(
    item=>`name:${item.canonical_key}`===group[0]?.author_key);
  if(aliasGroup)return aliasGroup.canonical_name;
  // 官方主页来源不只优先提供头像，也优先提供作者写法；否则 F95 的线程标题
  // `Lazy Procrastinator Collection` 会因为大写字母更多而抢成分组标题。
  const official=group.find(source=>source.official_avatar_url);
  if(official){
    const officialName=String(official.label||'')
      .replace(/\s*[·|]\s*[A-Za-z0-9_-]+\s*$/,'').trim();
    if(officialName)return officialName;
  }
  const names=group.map(source=>String(source.label||'').replace(/\s*[·|]\s*[A-Za-z0-9_-]+\s*$/,''))
    .filter(Boolean);
  if(!names.length)return group[0].label||group[0].ref||'';
  const caps=text=>(text.match(/[A-Z]/g)||[]).length;
  return names.reduce((best,name)=>caps(name)>caps(best)?name:best,names[0]);
}

function followAuthorBlock(group){
  const name=followAuthorName(group);
  const bad=group.filter(s=>s.last_status==='error'||s.last_status==='unauthorized').length;
  const sources=scrollerHtml(group.map(followSourceRow).join(''),{
    className:'fauthorsources',label:`${name} 的关注来源`});
  return `<div class="fauthor${bad?' bad':''}">
    <div class="fauthorhead">${followAuthorAvatar(group)}
      <b>${esc(name)}</b>
      <span class="fmeta">${group.length>1
        ? group.map(source=>sourceIcon(source.provider)).join('')+`${group.length} 个来源`
        : sourceIcon(group[0].provider)+esc(group[0].provider_label)}</span>
      ${bad?`<span class="fmeta warn">${bad} 个失败</span>`:''}
    </div>
    ${sources}</div>`;
}

function followSourceRow(source){
  const state=source.last_status||'未检查';
  const bad=state==='error'||state==='unauthorized';
  /* 状态用 Geist 的低饱和徽章（取证 vercel-geist-semantics-measured.md）：
     行级状态不上实底彩色，ok 绿 tint、失败红 tint、未检查灰。 */
  const badge=state==='ok'?'ok':bad?'error':'none';
  const stateTitle=source.history_exhausted?'没有更多历史内容':state;
  return `<div class="frow fsource${bad?' bad':''}${source.enabled?'':' disabled'}">
    <label class="fchannelcheck" title="${source.enabled?'参与检查更新':'暂停检查更新'}">
      <input type="checkbox" data-follow-enabled="${source.id}" ${source.enabled?'checked':''}
        aria-label="${source.enabled?'暂停':'启用'} ${esc(source.label)} 的更新检查">
      <span aria-hidden="true">${icon('check')}</span>
    </label>
    <b><a class="fsourcelink" href="${esc(source.url)}" target="_blank"
      rel="noreferrer noopener" title="打开原来源">${esc(source.label)}</a></b>
    <span class="fmeta fprovider">${sourceIcon(source.provider)}${esc(source.provider_label)}</span>
    <span class="fmeta fchecked">${esc(source.last_checked_at?localTime(source.last_checked_at):'未检查')}</span>
    <span class="sbadge ${badge}" title="${esc(stateTitle)}"><i aria-hidden="true"></i>
      ${source.history_exhausted?'<span>没有更多</span>':''}</span>
    <span class="fsourceactions">
      <button class="frowicon" data-follow-check="${source.id}" title="检查更新"
        ${source.enabled?'':'disabled'}
        aria-label="检查 ${esc(source.label)} 的更新">${icon('refresh-cw')}</button>
      <button class="frowicon danger" data-follow-remove="${source.id}" title="移除来源"
        aria-label="移除 ${esc(source.label)}">${icon('trash')}</button>
    </span>
    ${source.last_error?`<p class="frowerr">${esc(source.last_error)}</p>`:''}</div>`;
}

function followAliasManager(groups,suggestions){
  groups=groups||[];suggestions=suggestions||[];
  const detected=suggestions.map(item=>`<div class="faliassuggest">
    <span><b>${esc(item.canonical)}</b><i>+</i><b>${esc(item.alias)}</b>
      <small>${esc(item.evidence)}</small></span>
    <button class="fbtn small" data-follow-alias-add
      data-canonical="${esc(item.canonical)}" data-alias="${esc(item.alias)}">合并</button>
  </div>`).join('');
  const saved=groups.map(group=>`<div class="faliasrow"><b>${esc(group.canonical_name)}</b>
    <span>${group.aliases.map(alias=>`<span class="faliaschip">${esc(alias.name)}
      <button type="button" data-follow-alias-remove="${esc(alias.name)}"
        title="移除别名" aria-label="移除别名 ${esc(alias.name)}">${icon('x')}</button></span>`).join('')}</span>
  </div>`).join('');
  return `<details class="faliasmanager"${suggestions.length?' open':''}>
    <summary>作者别名${suggestions.length?` · 检测到 ${suggestions.length} 组可能重复`:groups.length?` · ${groups.length} 组`:''}</summary>
    ${detected?`<div class="faliassuggestions">${detected}</div>`:''}
    <form class="faliasform" id="followAliasAdd">
      <input name="canonical" required placeholder="规范作者名" aria-label="规范作者名">
      <input name="alias" required placeholder="平台别名" aria-label="平台别名">
      <button class="fbtn" type="submit">保存别名</button>
    </form>
    ${saved?`<div class="faliasrows">${saved}</div>`:'<p class="fnote">还没有保存作者别名。</p>'}
  </details>`;
}

/* 四种状态四种颜色：待办（缺凭据）和完成（已配置）不能同色，那正是要一眼分开的两件事。 */
const CRED_STATE={required:['需要','req'],optional:['可选','opt'],
  none:['不需要','none'],blocked:['接不进来','blocked']};

/* placeholder 用库里真实存在的创作者，而不是编一个名字——`facets.creators`
   是首页推荐词同一条数据路径，保证是用户自己库里的人。取不到就退回链接示例。 */
/* 「猜你喜欢」由后端从**用户自己浏览过的在线创作者**里挑（`location='online'` 的
   pixiv / X 资产，项目初期从浏览记录导入的那批）。曾经用过 `facets.creators`，
   那是「他有谁的文件」而不是「他喜欢谁」——那些人在 kemono/rule34 上大多找不到，
   点了白点。判据留在 web_follow._suggestions。 */
function followSuggestionChips(list){
  return (list||[]).map(item=>
    `<button class="fchip" data-follow-guess="${esc(item.name)}"
      title="浏览历史里出现 ${item.visits} 次${item.origin?` · ${esc(item.origin)}`:''}"
      >${esc(item.name)}</button>`).join('');
}

function followCredentialRow(row){
  const [label,kind]=CRED_STATE[row.requirement]||CRED_STATE.none;
  const configured=row.present&&!row.missing.length;
  const needsAttention=row.requirement==='required'&&!configured;
  const fields=(row.needs||[]).map(name=>`<label class="fcredfield">
    <span>${esc(name)}</span>
    <input type="password" name="${esc(name)}" autocomplete="off" spellcheck="false"
      placeholder="${(row.shared_fields||[]).includes(name)?'来自共享，留空表示不改'
        :row.fields.includes(name)?'已保存，留空表示不改':'未填写'}"></label>`).join('');
  const body=row.requirement==='none'?''
    :row.requirement==='blocked'?`<p>${esc(row.why)}</p>`
    :`<p>${esc(row.why)}${row.where?` <a href="${esc(row.where)}" target="_blank" rel="noreferrer noopener">去取</a>`:''}</p>
      ${row.howto?`<p>${esc(row.howto)}</p>`:''}
      <form class="fcredform" data-cred-form="${esc(row.provider)}">${fields}
        <div class="fcredactions"><button type="submit">保存</button>
          ${configured?`<button type="button" class="fquiet" data-cred-clear="${esc(row.provider)}">清除</button>`:''}
          <span data-cred-state aria-live="polite"></span></div></form>
      ${(row.shared_fields||[]).length?`<p class="fnote">${esc(row.shared_fields.join('、'))} 是从共享副本回填的，本机没有单独存。清除会把两边一起删。</p>`:''}
      <p class="fcredpath mono">${esc(row.path)}</p>
      ${row.world_readable?'<p class="fnote warn">文件权限过宽，请在运行 Peach 的 POSIX 主机上收紧为 0600。</p>':''}`;
  // 两个分支必须用同一个状态类，否则「不需要」那几行走 .fmeta、其余走 .fstate，
  // 同一列出现两套样式和两种对齐——用户一眼就看出来了。
  if(!body)return `<div class="frow fcred none"><b>${esc(row.provider_label)}</b>
    <span class="fcstate none">${esc(label)}</span></div>`;
  return `<details class="frow fcred ${esc(kind)}${configured?' ok':''}"${needsAttention?' open':''}>
    <summary><b>${esc(row.provider_label)}</b>
      <span class="fcstate ${configured?'done':esc(kind)}">${esc(configured?'已配置':label)}</span>
      ${row.missing.length?`<span class="fcstate missing">缺 ${esc(row.missing.join('、'))}</span>`:''}
    </summary>${body}</details>`;
}

/* 版式判据来自 docs/reference-sources.json 的 vercel-report-design：
   要避开卡片套卡片、用边框补救层级、成排通栏空条、
   细小灰字加随意字号。所以这里不再用嵌套卡片盒子——分组靠标题和一条发丝分隔线，
   行与行之间也只用分隔线，不各自套框。控件尺寸按实测 Geist：32px 高、6px 圆角、14px。 */
function renderFollowManage(credentials){
  const sources=followData.sources||[],counts=followData.counts||{};
  const broken=sources.filter(s=>s.last_status==='error'||s.last_status==='unauthorized');
  const creds=(credentials.providers||[]);
  const needCred=creds.filter(c=>c.requirement==='required'&&!(c.present&&!c.missing.length));
  const locked=!!followRuntime?.ledger_read_only;
  const writer=followRuntime?.ledger_writer_origin
    ?new URL('/follow-manage',followRuntime.ledger_writer_origin).href:'';
  $('#stats').innerHTML=`<div class="follow followmanage">
    ${locked?`<div class="runtimegate">${icon('info')}<span>${esc(followRuntime.ledger_read_only_message||'本机当前只能浏览')}</span>${writer
      ?`<a href="${esc(writer)}">前往写入端管理关注</a>`:''}</div>`:''}
    <div class="fmain">
      <section class="fsec">
        <div class="fsechead"><h3>添加关注</h3></div>
        <form class="faddform" id="followAdd">
          <div class="fsearchinput" data-follow-search-input>
            <span class="fsearchprefix" data-follow-search-prefix>${icon('search')}</span>
            <textarea name="lines" rows="1" required spellcheck="false"
              aria-label="来源链接、名字或 id"></textarea></div>
          <div class="fsrcfilter" id="followSrcFilter"></div>
          <button class="fbtn primary" type="submit">查找</button>
        </form>
        <p class="fnote" data-follow-add-state aria-live="polite"></p>
        <div id="followPicks"></div>
        ${(followData.suggestions||[]).length
          ?`<div class="fguess"><span class="fmeta">猜你喜欢</span>${
              followSuggestionChips(followData.suggestions)}</div>`:''}
        ${followAliasManager(followData.author_aliases,followData.alias_suggestions)}
      </section>
      <section class="fsec">
        <div class="fsechead"><h3>关注列表</h3>
          <span class="fmeta">${sources.length} 个来源${
            counts.new?` · <b>${counts.new}</b> 条未看`:''}</span>
          <label class="fmanagesort"><span>排序</span><select data-follow-sort aria-label="关注列表排序">
            <option value="checked"${followManageSort==='checked'?' selected':''}>最近检查</option>
            <option value="name"${followManageSort==='name'?' selected':''}>作者名称</option>
            <option value="sources"${followManageSort==='sources'?' selected':''}>来源数量</option>
          </select></label>
          <button class="fbtn" data-follow-check=""${sources.length?'':' disabled'}>${
            icon('refresh-cw')}检查全部</button>
          <button class="fbtn" data-follow-view>${icon('rss')}去看更新</button></div>
        ${followCheckReport?followCheckFailNote(followCheckReport):''}
        ${broken.length?`<p class="fnote warn">${broken.length} 个来源上次检查失败，原因见对应那一行。</p>`:''}
        ${sources.length?`<div class="frows fsources">${
          followAuthorGroups(sources).map(followAuthorBlock).join('')}</div>
          ${counts.new?`<div class="fsecfoot"><p class="fnote fbulkrow"><span class="fbulkcounts">未看 ${counts.new} · 已看 ${counts.seen||0}
            · 已保存 ${counts.saved||0} · 已忽略 ${counts.ignored||0}</span>
            <span class="fbulk"><button class="fbtn" data-follow-bulk="seen">全部标记已看</button>
            <button class="fbtn" data-follow-bulk="ignored">全部忽略</button></span></p></div>`:''}`
          :emptyState('rss','还没有关注来源','关注来源及其检查状态会显示在这里。',{className:'compact'})}
      </section>
    </div>
    <aside class="faside">
      <section class="fsec">
        <div class="fsechead"><h3>凭据</h3>
          ${needCred.length?`<span class="fmeta warn">${needCred.length} 个待配置</span>`:''}</div>
        <div class="frows">${creds.map(followCredentialRow).join('')}</div>
        <p class="fdesc"><b>存放位置与权限
            <button type="button" class="fdescinfo" data-fdesc-tooltip
              aria-label="凭据存放位置说明">${icon('info')}</button></b>
          <span>Windows 上不收紧文件权限</span>
          <span class="fdescpop" id="follow-credential-tooltip" role="tooltip" hidden>存放在<b>运行 Peach 的那台机器</b>上，不是浏览器所在机器；不进 Git、URL、日志或 ledger。NTFS 的访问控制走 ACL，<code>chmod</code> 在那里没有效果；POSIX 上建成 0600。</span></p>
      </section>
    </aside></div>`;
  wireFollowManage();
  if(locked)$('#stats').querySelectorAll(
    '#followAdd textarea,#followAdd button,[data-follow-remove],[data-follow-check],'+
    '[data-follow-enabled],'+
    '[data-follow-bulk],[data-follow-guess],[data-follow-alias-add],'+
    '[data-follow-alias-remove],#followAliasAdd input,#followAliasAdd button,[data-cred-form] input,'+
    '[data-cred-form] button,[data-cred-clear]'
  ).forEach(control=>{control.disabled=true});
}


async function openFollowManage(push=true){
  releaseHoverPreviews();disposeStage(false);
  document.body.classList.remove('entity-open','index-open');
  if(push){followManageSort='checked';route('/follow-manage')}
  else if(location.pathname==='/follow-manage'){
    const requested=new URLSearchParams(location.search).get('sort');
    followManageSort=['checked','name','sources'].includes(requested)?requested:'checked';
  }
  const surface=claimSurface('/follow-manage');
  buildManageBar();
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#stats').innerHTML=`<div class="follow"><p class="empty">${loadingDotsHtml('正在读取')}</p></div>`;
  const [data,credentials,runtime]=await Promise.all([
    api('/api/follow?limit=1'),api('/api/follow/credentials'),api('/healthz')]);
  if(!surfaceCurrent(surface))return;
  followData=data;followRuntime=runtime;
  renderFollowManage(credentials);
  window.scrollTo({top:0,behavior:'smooth'});
}

/* ── 共用接线 ── */
function wireFollowItems(){
  const root=$('#stats');
  wireFollowDetail(root);
  root.querySelectorAll('[data-follow-status]').forEach(button=>button.onclick=async event=>{
    event.stopPropagation();
    await followWrite(button,'/api/follow/status',
      {item:+button.dataset.followStatus,to:button.dataset.to})});
  root.querySelectorAll('[data-follow-save]').forEach(button=>button.onclick=async event=>{
    event.stopPropagation();
    await followWrite(button,'/api/follow/save',{item:+button.dataset.followSave})});
  root.querySelectorAll('[data-follow-collection]').forEach(button=>button.onclick=event=>{
    event.stopPropagation();openFollowDetail(+button.dataset.followCollection)});
  root.querySelectorAll('.followitem[data-follow-item]').forEach(card=>{
    const id=+card.dataset.followItem;
    card.onclick=event=>{
      if(event.target.closest('[data-follow-status],[data-follow-save],[data-follow-collection],[data-follow-detail],.tg'))return;
      if(selectMode||event.shiftKey||event.ctrlKey||event.metaKey){
        event.preventDefault();event.stopPropagation();toggleFollowSelection(id,event.shiftKey);return}
      openFollowDetail(id);
    };
    card.querySelectorAll('a').forEach(link=>link.onclick=event=>{
      if(selectMode||event.shiftKey||event.ctrlKey||event.metaKey){
        event.preventDefault();event.stopPropagation();toggleFollowSelection(id,event.shiftKey)}
    });
    const mark=card.querySelector('.selectionMark');
    if(mark)mark.onclick=event=>{event.preventDefault();event.stopPropagation();toggleFollowSelection(id,event.shiftKey)};
  });
}

function wireFollowManage(){
  const root=$('#stats'),form=root.querySelector('#followAdd');
  wireScrollers(root);
  const sort=root.querySelector('[data-follow-sort]');
  if(sort)sort.onchange=()=>{
    followManageSort=sort.value;
    route('/follow-manage'+(followManageSort==='checked'?'':'?sort='+encodeURIComponent(followManageSort)));
    openFollowManage(false);
  };
  renderFollowSrcFilter(root.querySelector('#followSrcFilter'));
  const tooltipTrigger=root.querySelector('[data-fdesc-tooltip]');
  const tooltip=root.querySelector('#follow-credential-tooltip');
  if(tooltipTrigger&&tooltip){
    let tooltipHovered=false,tooltipFocused=false;
    const hideTooltip=()=>{
      tooltip.hidden=true;tooltipTrigger.removeAttribute('aria-describedby');
      window.removeEventListener('resize',hideTooltip);
      window.removeEventListener('scroll',hideTooltip,true)};
    const hideTooltipIfIdle=()=>{if(!tooltipHovered&&!tooltipFocused)hideTooltip()};
    const showTooltip=()=>{
      tooltip.hidden=false;tooltipTrigger.setAttribute('aria-describedby',tooltip.id);
      tooltip.style.left='0px';tooltip.style.top='0px';
      const anchor=tooltipTrigger.getBoundingClientRect(),box=tooltip.getBoundingClientRect();
      const left=Math.max(8,Math.min(anchor.left+(anchor.width-box.width)/2,innerWidth-box.width-8));
      let top=anchor.top-box.height-10;
      if(top<8)top=Math.min(innerHeight-box.height-8,anchor.bottom+10);
      tooltip.style.left=left+'px';tooltip.style.top=Math.max(8,top)+'px';
      window.addEventListener('resize',hideTooltip);
      window.addEventListener('scroll',hideTooltip,{capture:true,passive:true})};
    tooltipTrigger.addEventListener('pointerenter',()=>{tooltipHovered=true;showTooltip()});
    tooltipTrigger.addEventListener('pointerleave',()=>{tooltipHovered=false;hideTooltipIfIdle()});
    tooltipTrigger.addEventListener('focus',()=>{tooltipFocused=true;showTooltip()});
    tooltipTrigger.addEventListener('blur',()=>{tooltipFocused=false;hideTooltipIfIdle()});
    tooltipTrigger.addEventListener('keydown',event=>{
      if(event.key==='Escape'){tooltipHovered=false;tooltipFocused=false;hideTooltip();tooltipTrigger.blur()}});
  }
  /* 作者别名的折叠用 Geist Collapse 机制：内容包 .fcollapse，开合时 JS 量
     scrollHeight 写 inline height 过渡（原生 details 无过渡；此前试过
     ::details-content 方案会吞内容，已弃）。凭据行是 flex 行布局不接。 */
  root.querySelectorAll('details.faliasmanager').forEach((details,index)=>{
    if(details.querySelector(':scope > .fcollapse'))return;
    const body=document.createElement('div');body.className='fcollapse';
    [...details.children].forEach(child=>{
      if(child.tagName==='SUMMARY')return;
      body.appendChild(child)});
    details.appendChild(body);
    const summary=details.querySelector('summary');
    let expanded=details.open,transitionRun=0;
    body.id=`follow-alias-collapse-${index}`;
    body.inert=!expanded;
    summary.setAttribute('aria-controls',body.id);
    summary.setAttribute('aria-expanded',String(expanded));
    const settle=(run,fn)=>{
      let done=false,timer;
      const finish=e=>{
        if(e&&e.propertyName!=='height')return;
        if(done)return;done=true;
        body.removeEventListener('transitionend',finish);clearTimeout(timer);
        if(run===transitionRun)fn()};
      body.addEventListener('transitionend',finish);
      timer=setTimeout(finish,260)};
    summary.addEventListener('click',e=>{
      e.preventDefault();
      expanded=!expanded;const run=++transitionRun;
      summary.setAttribute('aria-expanded',String(expanded));
      if(expanded){
        body.inert=false;
        const start=details.open?body.getBoundingClientRect().height:0;
        details.open=true;
        body.style.height=start+'px';body.getBoundingClientRect();
        body.style.height=body.scrollHeight+'px';
        settle(run,()=>{body.style.height='auto'});
      }else{
        body.inert=true;
        body.style.height=body.getBoundingClientRect().height+'px';body.getBoundingClientRect();
        body.style.height='0px';
        settle(run,()=>{details.open=false;body.style.height=''});
      }
    });
  });
  const box=form&&form.querySelector('textarea');
  /* 常见情况是粘一条，多行是例外——所以静止时就一行高，和按钮齐平；
     真粘了多行才往下长。原来固定三行，按钮只有它 1/3 高，看着就是没对齐。 */
  if(box){
    const grow=()=>{box.style.height='auto';
      box.style.height=Math.min(box.scrollHeight,240)+'px'};
    box.addEventListener('input',grow);
    box.addEventListener('paste',()=>setTimeout(grow,0));
    grow();
  }
  if(form)form.onsubmit=async event=>{
    event.preventDefault();
    if(form.dataset.busy==='true')return;
    /* 状态提示在表单外面的说明行里，不能在 form 里找——找不到就是 null，
       第一次赋值直接抛 TypeError，整个提交静默失败。 */
    const state=root.querySelector('[data-follow-add-state]');
    const button=form.querySelector('button[type="submit"]');
    const prefix=form.querySelector('[data-follow-search-prefix]');
    const lines=String(new FormData(form).get('lines')||'').split('\n')
      .map(line=>line.trim()).filter(Boolean);
    if(!lines.length)return;
    const byName=lines.some(line=>!line.includes('/'));
    form.dataset.busy='true';button.setAttribute('aria-busy','true');
    if(prefix)prefix.innerHTML=spinnerHtml('查找中');
    // 索引下载的提醒只在真按名字查时出现；常驻成一句说明就是噪音。
    state.textContent=byName?'查找中…（首次按名字查要下载创作者索引，可能几十秒）':'识别中…';
    try{
      const result=await api('/api/follow/resolve',{method:'POST',
        body:JSON.stringify({lines})});
      state.textContent='';if(box){box.value='';box.style.height='auto'}
      renderFollowPicks(result.results||[]);
    }catch(error){state.textContent=error.message||'查找失败'}
    finally{form.dataset.busy='false';button.removeAttribute('aria-busy');
      if(prefix)prefix.innerHTML=icon('search')}
  };
  root.querySelectorAll('[data-follow-remove]').forEach(button=>button.onclick=async()=>{
    if(!confirm('不再追这个来源？已经抓到的条目会一并移除，媒体本身不受影响。'))return;
    button.disabled=true;
    try{
      await api('/api/follow/source',{method:'POST',
        body:JSON.stringify({action:'remove',id:+button.dataset.followRemove})});
      await openFollowManage(false);
    }catch(error){button.disabled=false;alert(error.message)}
  });
  root.querySelectorAll('[data-follow-enabled]').forEach(control=>control.onchange=async()=>{
    const enabled=control.checked;control.disabled=true;
    try{
      await api('/api/follow/source',{method:'POST',body:JSON.stringify(
        {action:'enabled',id:Number(control.dataset.followEnabled),enabled})});
      await openFollowManage(false);
    }catch(error){control.checked=!enabled;control.disabled=false;alert(error.message)}
  });
  root.querySelectorAll('[data-follow-check]').forEach(button=>button.onclick=async()=>{
    if(followBusy)return;
    followBusy=true;const oldTitle=button.title;
    const oldAria=button.getAttribute('aria-label');
    const oldButton=button.innerHTML;
    button.setAttribute('aria-busy','true');button.title='检查中…';
    button.setAttribute('aria-label','检查中…');
    button.innerHTML=`${spinnerHtml('检查中')}${button.matches('.frowicon')?'':'<span>检查中…</span>'}`;
    try{
      const id=button.dataset.followCheck;
      const result=await api('/api/follow/check',{method:'POST',
        body:JSON.stringify(id?{source:+id}:{})});
      // 一个来源失败不该让其余来源的更新一起消失，所以逐条报，不整体报错。
      /* 结果先留下再重画，否则整页重绘会把它冲掉，用户只看到一次闪烁。
         逐条报而不是整体报错：一个来源缺凭据，不该让其余来源的更新一起消失。 */
      followCheckReport=result;
      followCheckToast(result);
      await openFollowManage(false);
    }catch(e){
      // 整个请求就失败了（断网、写入端不可达）：同样走那块报告，不弹 alert。
      followCheckReport={results:[{ok:false,error:e.message}]};
      followCheckToast(followCheckReport);
      const note=followCheckFailNote(followCheckReport);
       const box=$('#stats').querySelector('.fcheckreports');
       if(box)box.outerHTML=note;
      else $('#stats').querySelector('.fsec')?.insertAdjacentHTML('afterbegin',note);
    }
    finally{followBusy=false;button.removeAttribute('aria-busy');button.innerHTML=oldButton;
      button.title=oldTitle;if(oldAria===null)button.removeAttribute('aria-label');
      else button.setAttribute('aria-label',oldAria)}
  });
  const saveAuthorAlias=async(canonical,alias,button)=>{
    button.disabled=true;
    try{
      await api('/api/follow/author-alias',{method:'POST',body:JSON.stringify(
        {action:'add',canonical,alias})});
      await openFollowManage(false);
    }catch(error){button.disabled=false;alert(error.message)}
  };
  root.querySelectorAll('[data-follow-alias-add]').forEach(button=>button.onclick=()=>
    saveAuthorAlias(button.dataset.canonical,button.dataset.alias,button));
  const aliasForm=root.querySelector('#followAliasAdd');
  if(aliasForm)aliasForm.onsubmit=event=>{
    event.preventDefault();const data=new FormData(aliasForm),button=aliasForm.querySelector('button');
    saveAuthorAlias(String(data.get('canonical')||'').trim(),
      String(data.get('alias')||'').trim(),button);
  };
  root.querySelectorAll('[data-follow-alias-remove]').forEach(button=>button.onclick=async()=>{
    const alias=button.dataset.followAliasRemove;
    if(!confirm(`移除作者别名「${alias}」？对应来源会恢复成独立作者组。`))return;
    button.disabled=true;
    try{
      await api('/api/follow/author-alias',{method:'POST',body:JSON.stringify(
        {action:'remove',alias})});
      await openFollowManage(false);
    }catch(error){button.disabled=false;alert(error.message)}
  });
  root.querySelectorAll('[data-follow-guess]').forEach(chip=>chip.onclick=()=>{
    if(!form)return;
    const box=form.querySelector('textarea');
    box.value=chip.dataset.followGuess;
    box.dispatchEvent(new Event('input'));
    form.requestSubmit();
  });
  root.querySelectorAll('[data-cred-form]').forEach(form=>form.onsubmit=async event=>{
    event.preventDefault();
    const state=form.querySelector('[data-cred-state]'),button=form.querySelector('button');
    const values={};
    form.querySelectorAll('input[name]').forEach(input=>{
      if(input.value.trim())values[input.name]=input.value.trim()});
    if(!Object.keys(values).length){state.textContent='没有填写内容';return}
    button.disabled=true;state.textContent='保存中…';
    try{
      await api('/api/follow/credential',{method:'POST',body:JSON.stringify(
        {provider:form.dataset.credForm,values})});
      // 值不回显：清掉输入框，重画之后只看得到字段名。
      form.reset();await openFollowManage(false);
    }catch(error){state.textContent=error.message||'保存失败';button.disabled=false}
  });
  root.querySelectorAll('[data-cred-clear]').forEach(button=>button.onclick=async()=>{
    if(!confirm('清除这个来源的凭据？本机和共享副本都会被删除。'))return;
    button.disabled=true;
    try{
      // 共享盘不在时后端只撤掉了本机那份，必须让用户看见——否则他以为撤干净了，
      // 等盘回来 key 又被同步回来。
      const done=await api('/api/follow/credential',{method:'POST',body:JSON.stringify(
        {provider:button.dataset.credClear,values:{}})});
      if(done.note)alert(done.note);
      await openFollowManage(false);
    }catch(error){button.disabled=false;alert(error.message)}
  });
  root.querySelectorAll('[data-follow-bulk]').forEach(button=>button.onclick=async()=>{
    const to=button.dataset.followBulk;
    if(!confirm(`把当前全部「未看」标记为${to==='seen'?'已看':'已忽略'}？`))return;
    button.disabled=true;
    try{
      const pending=await api('/api/follow?status=new&limit=1000');
      const ids=(pending.groups||[]).flatMap(g=>[g.primary,...g.variants,...g.duplicates])
        .filter(item=>item.status==='new').map(item=>item.id);
      for(const id of ids){
        await api('/api/follow/status',{method:'POST',body:JSON.stringify({item:id,to})});
      }
      await openFollowManage(false);
    }catch(error){button.disabled=false;alert(error.message)}
  });
  root.querySelectorAll('[data-follow-view]').forEach(button=>
    button.onclick=()=>openFollow());
  root.querySelectorAll('[data-follow-report-dismiss]').forEach(button=>button.onclick=()=>{
    followCheckReport=null;root.querySelector('.fcheckreports')?.remove()});
}

/* 查找结果先摆出来由人勾选，不自动登记：发现要联网，结果也可能不止一个，
   替用户决定「就是这个」是错的。已经关注的项灰掉但仍显示，免得人以为没查到。 */
/* 来源筛选的常驻控件：挂在「添加关注」面板里，列出全部已关注来源，
   默认全选；取消勾选的来源，其查找结果行隐藏、也不进「添加选中」。 */
function renderFollowSrcFilter(mount){
  if(!mount)return;
  if(fsrcOpened){fsrcOpened.setOpen(false);fsrcOpened=null}
  const providers=[...new Set((followData?.sources||[])
    .map(source=>source.provider_label).filter(Boolean))];
  providers.forEach(provider=>{if(!fsrcProviders.has(provider))fsrcProviders.add(provider)});
  if(!providers.length){mount.innerHTML='';return}
  const label=()=>{const n=providers.filter(p=>!fsrcUnchecked.has(p)).length;
    return n===providers.length?'全部来源':`${n}/${providers.length} 个来源`};
  mount.innerHTML=`<button type="button" class="fbtn" data-srcfilter-toggle
      aria-expanded="false" aria-haspopup="menu" aria-controls="follow-source-menu"
      aria-label="${esc(label())}" title="${esc(label())}">
      ${icon('list-filter')}<span data-srcfilter-label>${esc(label())}</span></button>
    <div class="fsrcmenu" id="follow-source-menu" role="menu" data-srcfilter-menu hidden>${providers.map(provider=>
      `<label><input type="checkbox" data-srcfilter="${esc(provider)}"${fsrcUnchecked.has(provider)?'':' checked'}>
        <span>${esc(provider)}</span></label>`).join('')}</div>`;
  const toggle=mount.querySelector('[data-srcfilter-toggle]');
  const menu=mount.querySelector('[data-srcfilter-menu]');
  /* Vercel 项目页的 Filter and Sort 菜单没有展开动画。菜单固定在视口内，
     优先从触发钮右缘向左展开；下方放不下时改到上方，内容在菜单内滚动。 */
  const positionMenu=()=>{
    const anchor=toggle.getBoundingClientRect(),width=menu.getBoundingClientRect().width;
    const height=Math.min(menu.scrollHeight,innerHeight-16);
    const left=Math.max(8,Math.min(anchor.right-width,innerWidth-width-8));
    const below=anchor.bottom+8;
    const top=below+height<=innerHeight-8?below:Math.max(8,anchor.top-height-8);
    menu.style.left=left+'px';menu.style.top=top+'px'};
  const closeFromViewport=()=>setOpenTracked(false);
  const setOpen=open=>{
    if(open){
      menu.hidden=false;
      positionMenu();
      window.addEventListener('resize',positionMenu);
      window.addEventListener('scroll',closeFromViewport,{capture:true,passive:true});
    }else{
      menu.hidden=true;menu.style.left='';menu.style.top='';
      window.removeEventListener('resize',positionMenu);
      window.removeEventListener('scroll',closeFromViewport,true);
    }
    toggle.setAttribute('aria-expanded',String(open));
  };
  const setOpenTracked=open=>{
    setOpen(open);
    fsrcOpened=open?{mount,setOpen}:null};
  toggle.onclick=e=>{e.stopPropagation();setOpenTracked(menu.hidden)};
  mount.onkeydown=event=>{
    if(event.key==='Escape'&&!menu.hidden){setOpenTracked(false);toggle.focus()}};
  menu.querySelectorAll('[data-srcfilter]').forEach(input=>input.onchange=()=>{
    input.checked?fsrcUnchecked.delete(input.dataset.srcfilter)
      :fsrcUnchecked.add(input.dataset.srcfilter);
    toggle.setAttribute('aria-label',label());toggle.title=label();
    toggle.querySelector('[data-srcfilter-label]').textContent=label();
    document.querySelectorAll('.fpickitem').forEach(item=>{
      item.hidden=fsrcUnchecked.has(item.dataset.provider||'')})});
}
function renderFollowPicks(results){
  const box=$('#followPicks');
  if(!box)return;
  if(!results.length){box.innerHTML='';return}
  /* 来源筛选：默认全选（集合为空 = 全部）；取消勾选的来源其结果行隐藏，
     隐藏行不进「添加选中」。新来源出现时默认勾上。 */
  const providers=[...new Set(results.flatMap(row=>(row.candidates||[])
    .map(c=>c.provider_label).filter(Boolean)))];
  providers.forEach(provider=>{if(!fsrcProviders.has(provider))fsrcProviders.add(provider)});
  const srcChecked=provider=>fsrcProviders.has(provider) &&
    !fsrcUnchecked.has(provider);
  const blocks=results.map((row,index)=>{
    if(row.kind==='error')
      return `<div class="fpick bad"><b>${esc(row.line)}</b><p>${esc(row.error)}</p></div>`;
    const failures=Object.entries(row.failures||{});
    const items=(row.candidates||[]).map((c,ci)=>`<label class="fpickitem${c.known?' known':''}" data-provider="${esc(c.provider_label||'')}">
      <input type="checkbox" data-pick="${index}-${ci}" value="${esc(c.url)}"
        data-author="${esc(c.author||'')}"
        data-label="${esc(c.label)}"${c.known?' disabled':' checked'}>
      <span><b>${esc(c.provider_label)}</b> ${esc(c.label)}
        <i>${esc(c.known?'已经关注':c.evidence)}</i></span></label>`).join('');
    const searches=(row.external_searches||[]).map(search=>
      `<a class="fpicksearch" href="${esc(search.url)}" target="_blank" rel="noreferrer noopener">
        <b>${esc(search.label)}</b><span>${esc(search.query)}</span>
        <i>${esc(search.evidence)}</i></a>`).join('');
    return `<div class="fpick"><b>${esc(row.line)}</b>
      ${items||'<p class="fpickempty">站内没有查到来源</p>'}
      ${searches}
      ${failures.length?`<p class="fpickfail">${failures.map(([k,v])=>
        `${esc(k)}：${esc(v)}`).join('；')}</p>`:''}</div>`;
  }).join('');
  const total=results.reduce((n,row)=>n+(row.candidates||[])
    .filter(c=>!c.known && srcChecked(c.provider_label||'')).length,0);
  box.innerHTML=`<div class="fpicks"><div class="fpickhead"><h3>查找结果</h3></div>${blocks}
    ${total?`<div class="fpickactions"><button data-pick-add>添加选中</button>
      <button data-pick-cancel>取消</button><span data-pick-state aria-live="polite"></span></div>`
      :'<div class="fpickactions"><button data-pick-cancel>关闭</button></div>'}</div>`;
  box.scrollIntoView({block:'nearest',behavior:'smooth'});
  box.querySelector('[data-pick-cancel]').onclick=()=>{box.innerHTML=''};
  const applySrcFilter=()=>document.querySelectorAll('.fpickitem').forEach(item=>{
    item.hidden=fsrcUnchecked.has(item.dataset.provider||'')});
  applySrcFilter();
  const addButton=box.querySelector('[data-pick-add]');
  if(addButton)addButton.onclick=async()=>{
    const picked=[...box.querySelectorAll('[data-pick]:checked')]
      .filter(input=>{const row=input.closest('.fpickitem');
        return !row||!row.hidden;});
    if(!picked.length)return;
    const state=box.querySelector('[data-pick-state]');
    if(addButton.getAttribute('aria-busy')==='true')return;
    addButton.setAttribute('aria-busy','true');
    let done=0;const failures=[];
    for(const input of picked){
      state.innerHTML=`${spinnerHtml('添加中')}<span>添加中… ${++done}/${picked.length}</span>`;
      try{
        await api('/api/follow/source',{method:'POST',body:JSON.stringify(
          {action:'add',url:input.value,label:input.dataset.label,
           author:input.dataset.author})});
      }catch(error){
        // 一条失败不该把其余的一起丢掉，逐条报。
        failures.push(`${input.dataset.label}：${error.message}`);
      }
    }
    if(failures.length){
      state.textContent=failures.join('；');
      addButton.removeAttribute('aria-busy');
      return;
    }
    await openFollowManage(false);
  };
}

async function followWrite(button,path,body){
  const card=button.closest('.followitem'),state=card?.querySelector('.fstate');
  button.disabled=true;
  try{
    await api(path,{method:'POST',body:JSON.stringify(body)});
    await openFollow(false);
  }catch(e){
    button.disabled=false;
    // 只读端（reader）写入必然 409，那是正常状态；照实显示比静默失败好。
    if(state)state.textContent=e.message;else alert(e.message);
  }
}
function wireReviewAssets(root){
  /* 复核页不再自造「多选模式」和框选：交互与主网格一致——点一下切换，Shift 选一段。
     多一套只在这一页生效的选择方式，用户得先发现它、再记住它。 */
  root.querySelectorAll('.reviewpick').forEach(pick=>{
    const cells=[...pick.querySelectorAll('.reviewasset')];
    const readout=pick.querySelector('[data-picked-count]');
    let anchor=null;
    const paint=()=>{
      const n=cells.filter(c=>c.getAttribute('aria-pressed')==='true').length;
      if(readout)readout.textContent=`已选 ${n} / ${cells.length}`;
    };
    const set=(cell,on)=>{cell.setAttribute('aria-pressed',on);cell.classList.toggle('picked',on)};
    cells.forEach((cell,index)=>{
      cell.onclick=e=>{
        if(e.shiftKey&&anchor!==null){
          const [a,b]=[Math.min(anchor,index),Math.max(anchor,index)];
          for(let i=a;i<=b;i++)set(cells[i],true);
        }else set(cell,cell.getAttribute('aria-pressed')!=='true');
        anchor=index;paint();
      };
    });
    pick.querySelector('[data-pick-all]').onclick=()=>{cells.forEach(c=>set(c,true));paint()};
    pick.querySelector('[data-pick-none]').onclick=()=>{cells.forEach(c=>set(c,false));paint()};
    paint();
  });
}

/* ── 全部艺人 / 创作者 / 标签索引页 ── */
let tagIndexMode='alphabet',tagIndexCategory='all',indexRequestSeq=0;
const TAG_CATEGORIES=[['all','全部'],['meta','影片属性'],['relationship','人物关系'],
  ['role','角色设定'],['appearance','外貌身材'],['scene','情境场所'],['story','故事剧情'],
  ['position','性交体位'],['general','其他内容']];
const TAG_DISPLAY_NAMES={'1080P':'1080p','60fps':'60FPS','AI去码':'AI解码',
  '淫语ASMR':'ASMR','JK制服':'JK','OL制服':'OL','眼镜':'眼镜娘','情趣内衣':'性感内衣',
  '口罩遮脸':'口罩','强制剧情':'强制','足交':'脚交','骑乘':'骑乘位',
  '后入':'背后位','3P多人':'3P','双洞齐插':'双洞齐下','毒龙':'毒龙钻'};
const tagLabel=tag=>TAG_DISPLAY_NAMES[tag]||tag;
const selectedIndexTags=new Set();
let tagIndexMatch='any';
function paintTagIndexSelection(){
  const root=$('#index');if(!root||location.pathname!=='/tags')return;
  root.querySelectorAll('[data-k]').forEach(button=>{
    const on=selectedIndexTags.has(button.dataset.k);
    button.setAttribute('aria-pressed',String(on));button.classList.toggle('selected',on)});
  const panel=root.querySelector('[data-tag-selection]');if(!panel)return;
  panel.hidden=!selectMode;
  const count=panel.querySelector('[data-tag-selected]');if(count)count.textContent=`已选 ${selectedIndexTags.size} 个标签`;
  const apply=panel.querySelector('[data-tag-apply]');if(apply)apply.disabled=!selectedIndexTags.size;
}
async function openIndex(kind,q,push=true){
  releaseHoverPreviews();
  const requestSeq=++indexRequestSeq;
  document.body.classList.remove('entity-open');
  delete $('#index').dataset.entityKind;delete $('#index').dataset.entityName;
  const people=kind==='creators'||kind==='performers';
  const entityKind=kind==='performers'?'performer':'creator';
  const indexLimit=people?120:180;
  const indexQuery=new URLSearchParams();if(q)indexQuery.set('q',q);
  if(kind==='tags'){
    indexQuery.set('view',tagIndexMode);
    if(tagIndexCategory!=='all')indexQuery.set('category',tagIndexCategory)}
  if(push)route('/'+kind+(indexQuery.size?'?'+indexQuery:''),!!q);
  showHomeSurfaces();
  // 必须在 showHomeSurfaces 之后加：它会清掉这两个类并恢复顶部横条，
  // 写在前面等于自己加完自己删。
  document.body.classList.add('index-open');
  disposeStage(false);
  const indexApi=offset=>'/api/index?kind='+kind+'&limit='+indexLimit+'&offset='+offset+
    (q?'&q='+encodeURIComponent(q):'')+
    (kind==='tags'&&tagIndexCategory!=='all'?'&category='+encodeURIComponent(tagIndexCategory):'');
  const d=await api(indexApi(0));
  if(requestSeq!==indexRequestSeq||location.pathname!=='/'+kind)return;
  $('#index').hidden=false;buildEdge(); $('#grid').innerHTML=''; $('#count').textContent='';
  $('#loadSentinel').hidden=true; $('#shortsSec').hidden=true;
  const title=kind==='performers'?'艺人':(kind==='creators'?'创作者':'标签');
  const tagItems=[...d.items];
  const tagGroups=items=>{
    const groups={};[...items].sort((a,b)=>a.k.localeCompare(b.k,'zh-CN',{numeric:true,sensitivity:'base'})).forEach(x=>{
      const ch=tagLabel(x.k).normalize('NFKC').trim().charAt(0).toUpperCase();
      const key=/[A-Z]/.test(ch)?ch:(/[0-9]/.test(ch)?'#':(/[\u3400-\u9fff]/.test(ch)?'中文':'其他'));
      (groups[key]||(groups[key]=[])).push(x)});
    return Object.entries(groups).sort(([a],[b])=>a.localeCompare(b,'zh-CN')).map(([letter,items])=>
      `<section class="alphagroup"><h3>${letter}</h3><div class="alphalist">${items.map(x=>
        `<button class="alphatag ${x.cat||'general'}" data-k="${esc(x.k)}" aria-pressed="${selectedIndexTags.has(x.k)}"><span>${esc(tagLabel(x.k))}</span><span class="n">${x.n.toLocaleString()}</span></button>`).join('')}</div></section>`).join('')};
  const peopleHtml=items=>items.map(x=>`<button class="icell" data-k="${esc(x.k)}" data-kind="${entityKind}">
        <span class="ring">${avatarInner(x.k,
          kind==='performers'&&x.entity_id?{id:x.entity_id}:null, x.rep)}</span>
        <span class="nm">${esc(x.k)}</span><span class="n">${x.n.toLocaleString()}</span></button>`).join('');
  const tagHtml=items=>tagIndexMode==='alphabet'?`<div class="alphabet">${tagGroups(items)}</div>`:`<div class="tagwall index-tags">`+items.map(x=>`<button class="tg ${x.cat||'general'}" data-k="${esc(x.k)}" aria-pressed="${selectedIndexTags.has(x.k)}"
        style="padding:5px 12px;font-size:13px">${esc(tagLabel(x.k))}
        <span style="opacity:.6;font-size:11px">${x.n.toLocaleString()}</span></button>`).join('')+`</div>`;
  const body=people?`<div class="igrid">${peopleHtml(d.items)}</div>`:tagHtml(tagItems);
  const visibleTagCategories=TAG_CATEGORIES.filter(([key])=>key==='all'||Number(d.categories?.[key]||0)>0);
  const filters=kind==='tags'?`<div class="tagfilters" aria-label="标签类型">${visibleTagCategories.map(([key,label])=>
    `<button class="${key}" data-tag-category="${key}" aria-pressed="${tagIndexCategory===key}">${label}</button>`).join('')}</div>
    <div class="tagselection" data-tag-selection hidden>
      <label><input type="checkbox" data-tag-match-any ${tagIndexMatch==='any'?'checked':''}><span><b>广泛匹配</b><small>开启后匹配任一所选标签；关闭后必须同时包含全部标签。</small></span></label>
      <span class="mono" data-tag-selected>已选 0 个标签</span>
      <button type="button" data-tag-clear>清空</button>
      <button type="button" class="primary" data-tag-apply disabled>显示结果</button>
    </div>`:'';
  $('#index').innerHTML=`<div class="ihead">
      <h2 class="disp">${title}</h2>
      <span class="mono" id="indexCount" style="color:var(--muted)">${tagItems.length}${d.has_more?'+':''} 项</span>
      ${kind==='tags'?`<div class="tagmodes"><button data-tag-view="cloud" aria-pressed="${tagIndexMode==='cloud'}">标签云</button><button data-tag-view="alphabet" aria-pressed="${tagIndexMode==='alphabet'}">字母表</button></div>`:''}
      <div class="isearch"><input id="iq" placeholder="过滤…" value="${esc(q||'')}"></div>
    </div>${filters}<div id="indexBody">${body}</div><button class="indexmore" id="indexMore" type="button" ${d.has_more?'':'hidden'}>载入更多</button>`;
  let it2; $('#iq').oninput=e=>{clearTimeout(it2);it2=setTimeout(()=>openIndex(kind,e.target.value.trim(),true),300)};
  $('#index').querySelectorAll('[data-tag-view]').forEach(b=>b.onclick=()=>{
    tagIndexMode=b.dataset.tagView;openIndex('tags',$('#iq').value.trim(),true)});
  $('#index').querySelectorAll('[data-tag-category]').forEach(b=>b.onclick=()=>{
    tagIndexCategory=b.dataset.tagCategory;openIndex('tags',$('#iq').value.trim(),true)});
  const wireIndexEntries=root=>root.querySelectorAll('[data-k]').forEach(b=>b.onclick=()=>{
    if(people){openEntity(b.dataset.kind,b.dataset.k);return}
    if(selectMode){const key=b.dataset.k;selectedIndexTags.has(key)?selectedIndexTags.delete(key):selectedIndexTags.add(key);paintTagIndexSelection();return}
    $('#index').hidden=true;state={...state,state:'',tag:b.dataset.k,tag_match:'all'};route(homePath());buildBars();load(true)});
  wireIndexEntries($('#indexBody'));
  if(kind==='tags'){
    const panel=$('#index').querySelector('[data-tag-selection]');
    panel.querySelector('[data-tag-match-any]').onchange=e=>{tagIndexMatch=e.target.checked?'any':'all'};
    panel.querySelector('[data-tag-clear]').onclick=()=>{selectedIndexTags.clear();paintTagIndexSelection()};
    panel.querySelector('[data-tag-apply]').onclick=()=>{
      if(!selectedIndexTags.size)return;
      state={...state,state:'',tag:[...selectedIndexTags].join(','),tag_match:tagIndexMatch};
      selectedIndexTags.clear();setSelectMode(false,false);route(homePath());showHomeSurfaces();buildEdge();buildBars();load(true)};
    paintTagIndexSelection();
  }
  let indexOffset=d.items.length;
  $('#indexMore').onclick=async()=>{const more=$('#indexMore');more.disabled=true;
    try{const next=await api(indexApi(indexOffset));if(requestSeq!==indexRequestSeq)return;
      indexOffset+=next.items.length;d.has_more=next.has_more;
      if(people){d.items.push(...next.items);const grid=$('#indexBody .igrid');
        grid.insertAdjacentHTML('beforeend',peopleHtml(next.items));wireIndexEntries(grid)}
      else{d.items.push(...next.items);tagItems.push(...next.items);$('#indexBody').innerHTML=tagHtml(tagItems);wireIndexEntries($('#indexBody'));paintTagIndexSelection()}
      $('#indexCount').textContent=indexOffset+(next.has_more?'+':'')+' 项';more.hidden=!next.has_more}
    finally{if(requestSeq===indexRequestSeq)more.disabled=false}};
}

const ENTITY_LABELS={performer:'艺人',studio:'厂牌',creator:'创作者',series:'系列'};
/* 「女优」只用于番号发行物。素人、创作者自制和网红内容里的出镜者是艺人，
   套上 JAV 的行业称谓既不准确也会和创作者身份混淆。判据由后端 `is_jav` 给。 */
const performerLabel=it=>it&&it.is_jav?'女优':'艺人';
let entityRequestSeq=0,entityJavLayout=false;
async function fetchEntityItems(kind,name,filters,offset=0){
  const p=new URLSearchParams();p.set(kind,name);p.set('limit','48');p.set('offset',String(offset));
  p.set('sort',filters.sort||'new');
  if(filters.sort==='seed')p.set('seed',state.seed);
  if(offset)p.set('count','0');
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&key!==kind&&key!=='sort')p.set(key,filters[key])});
  // 资料页继承 JAV 开关：女优页和厂牌页同样是按番号浏览的语境。
  if(state.jav==='1')p.set('jav','1');
  const items=await api('/api/items?'+p);cache(items.items);return items
}
let entityCollectionPage={items:[],total:0,has_more:false};
function renderEntityCollection(kind,name,items,filters,append=false){
  const entityTag=filters.tag||'';
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  if(!append){
    renderedPartGroups.clear();
    entityCollectionPage={items:[...(items.items||[])],total:items.total||0,
      has_more:items.has_more==null?(items.items||[]).length<(items.total||0):!!items.has_more};
    section.innerHTML=`<div class="entitycollectionhead"><h3></h3><span class="sorts">
      <button class="batchaction entitybatch" type="button" title="换一批" aria-label="换一批">${icon('refresh-cw')}</button>
      ${javActive()?javLayoutButtons():''}
      ${sortOptions().map(([key,label])=>`<button type="button" data-entity-sort="${key}"
        aria-pressed="${(filters.sort||'new')===key}">${label}</button>`).join('')}</span></div>
      <div class="grid"></div><button class="entitymore" type="button">载入更多</button>`;
    section.dataset.total=String(items.total||0);
    section.querySelector('h3').textContent=`视频 · ${(items.total||0).toLocaleString()}${entityTag?' · '+entityTag:''}`;
    wireJavLayoutButtons(section);
    section.querySelector('.entitybatch').onclick=()=>{
      state.seed=rollSeed();updateEntityCollection(kind,name,{...filters,sort:'seed'},true)};
    section.querySelectorAll('[data-entity-sort]').forEach(button=>button.onclick=()=>{
      const sort=button.dataset.entitySort;
      updateEntityCollection(kind,name,{...filters,sort},true)});
  }else{
    entityCollectionPage.items.push(...(items.items||[]));
    entityCollectionPage.has_more=!!items.has_more;
  }
  const grid=section.querySelector('.grid');
  grid.insertAdjacentHTML('beforeend',collapseMultipartItems(items.items).map(it=>cardHtml(it)).join(''));
  wireCards(grid,undefined,tag=>updateEntityCollection(
    kind,name,{...filters,tag:tag===entityTag?'':tag},true));
  const more=section.querySelector('.entitymore');
  more.hidden=!entityCollectionPage.has_more;
  const requestMore=async()=>{if(more.hidden||more.disabled)return;more.disabled=true;const seq=entityRequestSeq;
    try{const next=await fetchEntityItems(kind,name,filters,entityCollectionPage.items.length);
      if(seq===entityRequestSeq&&$('#index').dataset.entityKind===kind&&$('#index').dataset.entityName===name)
        renderEntityCollection(kind,name,next,filters,true)}
    finally{if(seq===entityRequestSeq)more.disabled=false}};
  more.onclick=requestMore;
  more._observer?.disconnect();
  if(!more.hidden){
    more._observer=new IntersectionObserver(entries=>{if(entries.some(x=>x.isIntersecting))requestMore()},{rootMargin:'320px'});
    more._observer.observe(more);
  }
  scheduleStickySurfaces();
}
async function updateEntityCollection(kind,name,filters,push=true){
  // 标签是作品筛选，点了就回到作品视图：留在照片里既不生效，标签条也会自相矛盾。
  entityMediaView=emptyMediaView();
  const search=entityFilterSearch(filters);
  if(push)route(entityPath(kind,name)+(search?'?'+search:''));
  barsContext={type:'entity',kind,name,filters:{...filters}};
  const seq=++entityRequestSeq;
  const items=await fetchEntityItems(kind,name,filters);
  if(seq!==entityRequestSeq)return;
  renderEntityMediaToggle(kind,name,filters);
  $('#index').querySelectorAll('[data-entity-tag]').forEach(b=>
    b.setAttribute('aria-pressed',String(b.dataset.entityTag===filters.tag)));
  renderEntityCollection(kind,name,items,filters)
}
/* ── 资料页的照片 ─────────────────────────────────────────────────────────────
   图集就是目录：账本里没有图集实体，`<作品目录>\P\001.jpg` 这种约定只保留在后端，
   页面不先造一层固定比例封面，照片标签直接进入瀑布流，再点图进入灯箱。
   瀑布流用 CSS `column-count` 而不是 JS 布局：图片行没有宽高，等宽多列流式排版正好
   不需要知道比例，也就不用等图片加载完再算位置。
   缩略图一律走 `/photo-thumb`（服务端缓存），只有灯箱里的大图读 `/photo` 原图——
   PikPak 是计费来源，瀑布流直接铺原图等于一屏付几十兆流量。 ── */
const emptyMediaView=()=>({media:'videos',set:0});
const parseMediaView=search=>{const params=new URLSearchParams(search),set=params.get('set')||'';
  return {media:params.get('media')==='photos'?'photos':'videos',set:/^\d+$/.test(set)?Number(set):0}};
const entityViewSearch=(filters,view)=>{const params=new URLSearchParams(entityFilterSearch(filters));
  if(view&&view.media==='photos'){params.set('media','photos');if(view.set)params.set('set',String(view.set))}
  return params.toString()};
let entityPhotos=null,entityMediaView=emptyMediaView(),photoWallItems=[];
const routeEntityView=(kind,name,view)=>{
  const filters=barsContext.type==='entity'?barsContext.filters:emptyEntityFilters();
  const search=entityViewSearch(filters,view);
  route(entityPath(kind,name)+(search?'?'+search:''))};
const photoTotalOf=()=>entityPhotos&&!entityPhotos.error?(entityPhotos.total||0):0;

function renderEntityMediaToggle(kind,name,filters){
  const controls=$('#index').querySelector('.entitymediaview');if(!controls)return;
  const photos=photoTotalOf();
  controls.hidden=!photos;
  if(!photos)return;
  controls.querySelectorAll('[data-media-view]').forEach(button=>{
    const media=button.dataset.mediaView;
    button.setAttribute('aria-pressed',String(entityMediaView.media===media));
    button.onclick=()=>switchEntityMedia(kind,name,filters,media);
  });
}

async function switchEntityMedia(kind,name,filters,media){
  if((entityMediaView.media==='photos')===(media==='photos')&&!entityMediaView.set)return;
  entityMediaView=media==='photos'?{media:'photos',set:0}:emptyMediaView();
  routeEntityView(kind,name,entityMediaView);
  renderEntityMediaToggle(kind,name,filters);
  if(media==='photos'){renderPhotoWall(kind,name,filters,entityPhotos);return}
  const seq=++entityRequestSeq;
  const items=await fetchEntityItems(kind,name,filters);
  if(seq!==entityRequestSeq)return;
  renderEntityCollection(kind,name,items,filters);
}

async function openPhotoSet(kind,name,filters,setId,push=true){
  const seq=++entityRequestSeq;
  const data=await api('/api/photo-set?id='+setId+'&limit=120');
  if(seq!==entityRequestSeq||data.error)return;
  entityMediaView={media:'photos',set:setId};
  if(push)routeEntityView(kind,name,entityMediaView);
  renderEntityMediaToggle(kind,name,filters);
  renderPhotoWall(kind,name,filters,data);
}

const photoCell=(item,index)=>`<button class="photocell" data-photo-index="${index}" title="${esc(item.name)}">
    <img src="/photo-thumb?id=${item.id}" alt="${esc(item.name)}" loading="lazy"
      decoding="async" fetchpriority="low"
      onerror="this.closest('.photocell').remove()"></button>`;

function renderPhotoWall(kind,name,filters,data,append=false){
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  const entityWide=!data.id;
  if(!append){
    photoWallItems=[];
    section.innerHTML=entityWide
      ? `<div class="photohead"><h3>照片 · ${(data.total||0).toLocaleString()} 张</h3></div>
        <div class="photowall"></div><button class="entitymore" type="button">载入更多</button>`
      : `<div class="photohead">
          <button class="photoback" type="button">${icon('chevron-left')}<span>全部照片</span></button>
          <h3>${esc(data.title)} · ${(data.total||0).toLocaleString()} 张</h3>
          ${sourceTools(data.id)}</div>
        <div class="photowall"></div><button class="entitymore" type="button">载入更多</button>`;
    if(!entityWide){
      section.querySelector('.photoback').onclick=()=>{
        entityMediaView={media:'photos',set:0};
        routeEntityView(kind,name,entityMediaView);
        renderPhotoWall(kind,name,filters,entityPhotos)};
      // 对账后整组数量都变了，重开这一组比逐格摘除简单也更不容易错。
      wireSourceTools(section.querySelector('.photohead'),
        ()=>openPhotoSet(kind,name,filters,data.id,false));
    }
  }
  const wall=section.querySelector('.photowall');
  const start=photoWallItems.length;
  photoWallItems.push(...data.items);
  wall.insertAdjacentHTML('beforeend',data.items.map((item,i)=>photoCell(item,start+i)).join(''));
  wall.querySelectorAll('.photocell:not([data-wired])').forEach(cell=>{
    cell.dataset.wired='1';
    cell.onclick=()=>openPhotoLightbox(Number(cell.dataset.photoIndex))});
  const more=section.querySelector('.entitymore');
  more.hidden=!data.has_more;
  const requestMore=async()=>{if(more.hidden||more.disabled)return;more.disabled=true;const seq=entityRequestSeq;
    try{const next=await api(entityWide
      ? `/api/photos?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}&limit=120&offset=${photoWallItems.length}`
      : `/api/photo-set?id=${data.id}&limit=120&offset=${photoWallItems.length}`);
      if(seq===entityRequestSeq&&!next.error&&$('#index').dataset.entityName===name)
        renderPhotoWall(kind,name,filters,next,true)}
    finally{if(seq===entityRequestSeq)more.disabled=false}};
  more.onclick=requestMore;
  more._observer?.disconnect();
  if(!more.hidden){
    more._observer=new IntersectionObserver(entries=>{if(entries.some(x=>x.isIntersecting))requestMore()},{rootMargin:'320px'});
    more._observer.observe(more);
  }
}

/* ── 源文件管理 ───────────────────────────────────────────────────────────────
   标题旁两个按钮，服务的是「跳过去自己整理网盘目录」这条来回：定位打开源文件所在
   目录（A:/B: 是 CloudDrive 挂上来的盘符，在资源管理器里和本地目录没区别），在那边
   删掉不要的，回来点一下同步，账本跟着对齐。
   删除不进复核，但账本记录先放进回收站。真正要防的是把「盘没挂上」当成
   「文件没了」，那个闸门在服务端：整条来源不在线时直接拒绝，一行都不动。
   路径始终由服务端按 asset id 查，前端拿不到也不该拿到 `path`。 ── */
const SOURCE_HINTS={
  'source offline':'来源不在线，已拒绝对账（避免把没挂上的盘当成文件被删）',
  'source not mapped':'本机没有映射这个来源的盘符',
  'file missing':'源文件已经不在了，点右边同步把账本对齐',
  'unsupported platform':'当前服务端系统不支持直接定位文件',
  'reveal failed':'打开文件管理器失败，请重试',
};
const sourceHint=message=>SOURCE_HINTS[message]||message;

async function revealSource(id,status,{toastSuccess=false,button=null}={}){
  if(button?.getAttribute('aria-busy')==='true')return;
  const buttonHtml=button?.innerHTML,label=button?.textContent.trim();
  if(button){button.disabled=true;button.setAttribute('aria-busy','true');
    button.innerHTML=`${spinnerHtml('正在定位')}<span>${esc(label)}</span>`}
  status.textContent='正在定位…';
  try{
    await api('/api/reveal',{method:'POST',body:JSON.stringify({id})});
    if(toastSuccess){status.textContent='';toast('已在资源管理器中显示')}
    else status.textContent='已在服务端弹出文件管理器';
  }catch(e){status.textContent=sourceHint(e.message)}
  finally{if(button){button.disabled=false;button.removeAttribute('aria-busy');button.innerHTML=buttonHtml}}
}

async function syncMissing(id,status,done){
  status.textContent='正在核对目录…';
  try{
    const r=await api('/api/purge-missing',{method:'POST',body:JSON.stringify({id})});
    if(r.ok===false){status.textContent=sourceHint(r.error);return}
    status.textContent=r.removed
      ? `已把 ${r.removed} 项移入回收站（核对 ${r.checked} 项）`
      : `目录内 ${r.checked} 项都还在，无需改动`;
    if(r.removed&&done)done(r);
  }catch(e){status.textContent=sourceHint(e.message)}
}

/* 两个动作在照片详情里和作品标题旁复用；状态位置由各自表面决定。 */
const sourceToolButtons=id=>`
    <button type="button" data-reveal="${id}" title="在文件管理器里打开源文件所在目录"
      aria-label="定位源文件">${icon('folder-open')}</button>
    <button type="button" data-sync="${id}" title="核对该目录：磁盘上已删除的，移入 Peach 回收站"
      aria-label="同步删除">${icon('refresh-cw')}</button>`;
const sourceTools=id=>`<div class="srctools">${sourceToolButtons(id)}
    <span class="srcstate" aria-live="polite"></span></div>`;

function wireSourceTools(root,done){
  const status=root.querySelector('.srcstate');
  if(!status)return;
  const reveal=root.querySelector('[data-reveal]');
  const sync=root.querySelector('[data-sync]');
  if(reveal)reveal.onclick=()=>revealSource(Number(reveal.dataset.reveal),status);
  if(sync)sync.onclick=()=>syncMissing(Number(sync.dataset.sync),status,done);
}

/* 灯箱按需加载 Swiper：大图轮播、底部缩略图条和键盘左右键都是它自带的模块，
   没必要自己写一遍；但它只有看照片时才用得上，不该进首屏。 */
let swiperLoader=null,activeLightbox=null;
const loadSwiper=()=>swiperLoader||(swiperLoader=new Promise((resolve,reject)=>{
  const style=document.createElement('link');
  style.rel='stylesheet';style.href='/vendor/swiper/14.2.0/swiper-bundle.min.css';
  document.head.appendChild(style);
  const script=document.createElement('script');
  script.src='/vendor/swiper/14.2.0/swiper-bundle.min.js';
  script.onload=()=>resolve(window.Swiper);
  script.onerror=()=>{swiperLoader=null;reject(new Error('swiper unavailable'))};
  document.head.appendChild(script)}));
const photoLightKeys=e=>{if(e.key!=='Escape')return;
  e.preventDefault();e.stopImmediatePropagation();
  if(activeLightbox?.detail?.isOpen()){activeLightbox.detail.dismiss(true);return}
  closePhotoLightbox()};
const ZOOM_MAX=4;

/* 缩放条。Swiper 的 zoom 模块只给 in/out/toggle，没有「缩到这个倍数」的入口，
   但 `zoom.in()` 用的就是 `params.zoom.maxRatio`——先改上限再 in，就等于设定值。
   双击和触控板捏合仍由模块自己处理，`zoomChange` 负责把滑块同步回来。 */
function wirePhotoZoom(box, main){
  const slider=box.querySelector('.photozoom input');
  const label=box.querySelector('.photozoom b');
  const show=scale=>{slider.value=scale;label.textContent=Math.round(scale*100)+'%'};
  const apply=raw=>{
    const scale=Math.min(ZOOM_MAX,Math.max(1,Math.round(raw*10)/10));
    show(scale);
    if(scale<=1){main.zoom.out();return}
    main.params.zoom.maxRatio=scale;main.zoom.in();
  };
  slider.oninput=()=>apply(Number(slider.value));
  box.querySelectorAll('[data-zoom-step]').forEach(b=>
    b.onclick=()=>apply(Number(slider.value)+Number(b.dataset.zoomStep)*0.5));
  // 翻页会把缩放清回 1，滑块得跟着回位，否则它显示 200% 而图是原始大小。
  main.on('slideChange',()=>show(1));
  // `zoomChange` 的第一个参数是 swiper 实例，倍数在第二个；接错了滑块会写进 NaN。
  main.on('zoomChange',(_swiper,scale)=>show(Math.min(ZOOM_MAX,Math.max(1,scale||1))));
  return {show};
}

/* 图片详情只展示安全元数据，定位仍只把 asset id 交给服务端。绝不能为了显示路径把
   ledger 的本机绝对路径送进浏览器。 */
const fmtPhotoSize=raw=>{const size=Number(raw)||0;if(!size)return'大小未知';
  return (size<1024*1024?`${Math.max(1,Math.round(size/1024))} KB`:fmtSize(size)).replace(' ','\u00a0')};
function wirePhotoDetail(box,items,index){
  const toggle=box.querySelector('.photodetailtoggle');
  const panel=box.querySelector('.photodetail');
  const title=panel.querySelector('h2');
  const meta=panel.querySelector('.photodetailmeta');
  const reveal=panel.querySelector('[data-photo-reveal]');
  const status=panel.querySelector('.srcstate');
  const paint=at=>{
    const item=items[at];if(!item)return;
    title.textContent=item.name||'未命名图片';
    meta.textContent=[LOC[item.location]||item.location||'来源未知',fmtPhotoSize(item.size)].join(' · ');
    reveal.dataset.photoReveal=String(item.id);status.textContent='';
  };
  const dismiss=returnFocus=>{panel.hidden=true;toggle.setAttribute('aria-expanded','false');
    if(returnFocus&&document.contains(toggle))toggle.focus()};
  const dismissOutside=target=>{if(panel.hidden||toggle.contains(target)||panel.contains(target))return false;
    dismiss();return true};
  toggle.onclick=()=>{if(panel.hidden){panel.hidden=false;toggle.setAttribute('aria-expanded','true');
      queueMicrotask(()=>reveal.focus())}
    else dismiss()};
  reveal.onclick=()=>revealSource(Number(reveal.dataset.photoReveal),status,{toastSuccess:true,button:reveal});
  paint(index);return {paint,dismiss,dismissOutside,isOpen:()=>!panel.hidden};
}

function closePhotoLightbox(){
  if(!activeLightbox)return;
  document.removeEventListener('keydown',photoLightKeys,true);
  activeLightbox.resize?.disconnect();
  activeLightbox.main.destroy(true,true);activeLightbox.strip.destroy(true,true);
  activeLightbox.box.remove();activeLightbox=null;
  document.body.classList.remove('photolight-open');
}
async function openPhotoLightbox(index){
  const items=photoWallItems;
  if(!items.length||index<0||index>=items.length)return;
  let SwiperCtor;
  try{SwiperCtor=await loadSwiper()}
  catch(_e){window.open('/photo?id='+items[index].id,'_blank','noopener');return}
  closePhotoLightbox();
  const box=document.createElement('div');
  box.className='photolight';
  box.innerHTML=`<button class="photoclose" type="button" aria-label="关闭">${icon('x')}</button>
    <div class="swiper photomain"><div class="swiper-wrapper">${items.map(item=>
      `<div class="swiper-slide"><div class="swiper-zoom-container"><img src="/photo?id=${item.id}"
        alt="${esc(item.name)}" loading="lazy"></div></div>`).join('')}</div>
      <button class="photonav back" type="button" aria-label="上一张">${icon('chevron-left')}</button>
      <button class="photonav fwd" type="button" aria-label="下一张">${icon('chevron-left')}</button></div>
    <div class="photobar">
      <button class="photodetailtoggle" type="button" aria-expanded="false" aria-controls="photoDetail"
        aria-haspopup="dialog"
        aria-label="图片详情" title="图片详情">${icon('info')}</button>
      <div class="photocount mono" aria-live="polite">${index+1} / ${items.length}</div>
      <div class="photozoom">
        <button type="button" data-zoom-step="-1" aria-label="缩小">${icon('minus')}</button>
        <input type="range" min="1" max="${ZOOM_MAX}" step="0.1" value="1" aria-label="缩放">
        <button type="button" data-zoom-step="1" aria-label="放大">${icon('plus')}</button>
        <b class="mono">100%</b></div></div>
    <section class="photodetail" id="photoDetail" role="dialog" aria-modal="false"
      aria-labelledby="photoDetailTitle" hidden>
      <div class="photodetailcopy"><h2 id="photoDetailTitle" data-middle-truncate></h2><span class="photodetailmeta"></span></div>
      <button type="button" data-photo-reveal="">${icon('folder-open')}<span>在资源管理器中显示</span></button>
      <span class="srcstate" aria-live="polite"></span>
    </section>
    <div class="swiper photostrip"><div class="swiper-wrapper">${items.map(item=>
      `<div class="swiper-slide"><img src="/photo-thumb?id=${item.id}" alt="" loading="lazy"></div>`).join('')}</div></div>`;
  document.body.appendChild(box);
  document.body.classList.add('photolight-open');
  const counter=box.querySelector('.photocount');
  const strip=new SwiperCtor(box.querySelector('.photostrip'),{
    slidesPerView:'auto',spaceBetween:8,freeMode:true,watchSlidesProgress:true,
    centeredSlides:true,centeredSlidesBounds:true,slideToClickedSlide:true});
  const main=new SwiperCtor(box.querySelector('.photomain'),{
    initialSlide:index,zoom:{maxRatio:ZOOM_MAX},keyboard:{enabled:true},lazyPreloadPrevNext:1,
    // 上下滚也翻页：看图时手在滚轮上，没人愿意为了换一张去够左右键或按钮。
    mousewheel:{enabled:true,forceToAxis:false},
    thumbs:{swiper:strip},
    navigation:{prevEl:box.querySelector('.photonav.back'),nextEl:box.querySelector('.photonav.fwd')},
    on:{slideChange(){counter.textContent=`${this.activeIndex+1} / ${items.length}`}}});
  const zoomBar=wirePhotoZoom(box,main);
  const detail=wirePhotoDetail(box,items,index);
  main.on('slideChange',()=>detail.paint(main.activeIndex));
  /* Swiper 只在自己构造的那一刻量一次容器。灯箱是插进已经布好版的页面里的，
     窗口一改大小（或首屏字体、滚动条落定得比构造晚）slide 就停在旧宽度上，
     大图按错误的框缩放，看起来就是「显示不全」。挂个 ResizeObserver 让它重量。 */
  const resize=new ResizeObserver(()=>{main.update();strip.update()});
  resize.observe(box);
  activeLightbox={box,main,strip,resize,zoomBar,detail};
  box.querySelector('.photoclose').onclick=closePhotoLightbox;
  // 只在背景本身上关闭：点图片、缩略图条和翻页按钮都不该退出。
  box.addEventListener('click',e=>{
    if(detail.dismissOutside(e.target))return;
    if(e.target===box)closePhotoLightbox()});
  document.addEventListener('keydown',photoLightKeys,true);
}

async function openEntity(kind,name,push=true,requestedTag){
  releaseHoverPreviews();
  const filters=push?emptyEntityFilters():parseEntityFilters(location.search);
  if(requestedTag!==undefined)filters.tag=requestedTag;
  if(kind==='creator')filters.creator='';
  const entityTag=filters.tag||'';
  const expectedPath=entityPath(kind,name);
  // 深链和前进后退要能直接落到照片视图；点进来的新页面一律从作品开始。
  entityMediaView=push?emptyMediaView():parseMediaView(location.search);
  const search=entityViewSearch(filters,entityMediaView);
  if(push)route(expectedPath+(search?'?'+search:''));
  barsContext={type:'entity',kind,name,filters};
  showHomeSurfaces();
  disposeStage(false);
  detailReturnBarsContext=null;
  entityJavLayout=false;
  const seq=++entityRequestSeq;
  const [d,items,photos]=await Promise.all([
    api(`/api/entity?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}`),
    fetchEntityItems(kind,name,filters),
    api(`/api/photos?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}`)]);
  if(d.error||seq!==entityRequestSeq||
     decodeURIComponent(location.pathname)!==decodeURIComponent(expectedPath))return;
  /* 直达或刷新资料页时 URL 没有 `jav=1`。以返回作品的真实 `is_jav` 恢复女优／厂牌
     语境，避免大图／小图／预览图按钮只在从 JAV 首页点进来时偶然存在。 */
  entityJavLayout=(kind==='performer'||kind==='studio')&&
    (state.jav==='1'||(items.items||[]).some(item=>item.is_jav));
  document.body.classList.add('entity-open');
  $('#index').hidden=false;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  const image=d.id?(kind==='studio'
    ? `<img src="/logo?studio=${encodeURIComponent(d.canonical_name)}" alt="${esc(d.canonical_name)}"
        onerror="if(!this.dataset.f){this.dataset.f='1';this.src='/entity-image?kind=studio&id=${d.id}'}else{this.remove()}">`
    /* 兜底链的最后一环必须是 `this.remove()`：留着取不到图的 <img> 会让浏览器
       画出 alt 文本（整个艺人名横在头像圈里），而 `:has(img)` 仍然匹配，首字母
       垫底永远回不来。`onerror=null` 只是不再重试，不等于这一环走完了。 */
    : `<img src="/entity-image?kind=${kind}&id=${d.id}" alt="${esc(d.canonical_name)}"${facePos(d.avatar_focus)}
        onerror="this.removeAttribute('style');${d.representative_asset_id?`if(!this.dataset.f){this.dataset.f='1';this.src='/avatar?id=${d.representative_asset_id}'}else{this.remove()}`:`this.remove()`}">`):'';
  const links=(d.links||[]).map(x=>x.clickable&&/^https?:\/\//i.test(x.url||'')
    ? `<a href="${esc(x.url)}" target="_blank" rel="noreferrer"><span class="entitylinkicon">${icon('globe')}<img class="entityfavicon" src="${esc(faviconUrl(x.url))}" data-studio="${kind==='studio'?esc(d.canonical_name):''}" alt=""></span><span class="entitylinklabel">${esc(x.label)}</span><span class="entitylinkarrow" aria-hidden="true">↗</span></a>`
    : `<span class="private" title="私人馆藏来源记录，不直接打开下载页"><span class="entitylinkicon">${icon('globe')}</span><span class="entitylinklabel">来源 · ${esc(x.label||x.hostname||'已记录')}</span></span>`).join('');
  const terms=(d.search_terms||[]).map(x=>`<code>${esc(x.term)}</code>`).join('');
  const tags=(d.tags||[]).map(x=>`<button class="pill" data-entity-tag="${esc(x.k)}" aria-pressed="${entityTag===x.k}">${esc(tagLabel(x.k))}<small>${x.n.toLocaleString()}</small></button>`).join('');
  const related=(d.related_performers||[]).map(x=>`<button class="relatedperson" data-related-performer="${esc(x.k)}">
      <span class="ring"><span>${esc(x.k.slice(0,1))}</span><img src="/entity-image?kind=performer&id=${x.id}" alt="" loading="lazy"
        onerror="${x.rep?`if(!this.dataset.f){this.dataset.f='1';this.src='/avatar?id=${x.rep}'}else{this.remove()}`:`this.remove()`}"></span>
      <span class="nm">${esc(x.k)}</span><small>${x.n.toLocaleString()} 部</small></button>`).join('');
  const photoCount=photos&&!photos.error?(photos.total||0):0;
  const mediaSelected=entityMediaView.media==='photos';
  const mediaToggle=photoCount?mediaViewButtonsHtml({active:mediaSelected?'photos':'videos',
    imageValue:'photos',imageLabel:'照片',videoCount:d.asset_count,imageCount:photoCount,
    className:'entitymediaview'}):'';
  $('#index').dataset.entityKind=kind;$('#index').dataset.entityName=name;
  $('#index').innerHTML=`<div class="entityhero"><div class="entityportrait ${kind==='performer'||kind==='creator'?'':'square'}">${image}<span>${esc(name.slice(0,1))}</span></div>
      <div><h2>${esc(d.canonical_name)}</h2>
        <div class="alias">${(d.display_aliases||[]).length?'别名 · '+d.display_aliases.map(esc).join(' / '):'暂无别名'} · ${d.asset_count.toLocaleString()} 个视频</div>
        ${d.summary?`<div class="entitysummary">${esc(d.summary)}</div>`:''}
        ${links?`<div class="entitylinks">${links}</div>`:''}
        ${terms?`<div class="entityterms">馆藏检索词 · ${terms}</div>`:''}</div></div>
    ${related?`<div class="entitymeta"><section aria-label="同台艺人"><div class="relatedpeople">${related}</div></section></div>`:''}
    ${(tags||mediaToggle)?`<section class="entitytagbar" aria-label="媒体与标签"><div class="entitytags">${mediaToggle}${tags}</div></section>`:''}
    <div class="entitysection"></div>`;
  $('#index').querySelectorAll('[data-entity-tag]').forEach(b=>b.onclick=()=>{
    const next=b.dataset.entityTag===entityTag?'':b.dataset.entityTag;
    const nextFilters={...filters,tag:next};barsContext={type:'entity',kind,name,filters:nextFilters};
    buildBars();updateEntityCollection(kind,name,nextFilters,true)});
  $('#index').querySelectorAll('.entityfavicon').forEach(img=>img.addEventListener('error',()=>{
    if(img.dataset.studio&&!img.dataset.fallback){img.dataset.fallback='1';img.src='/logo?studio='+encodeURIComponent(img.dataset.studio)}
    else img.remove()}));
  $('#index').querySelectorAll('[data-related-performer]').forEach(b=>b.onclick=()=>
    openEntity('performer',b.dataset.relatedPerformer));
  entityPhotos=photos&&!photos.error?photos:null;
  if(entityMediaView.media==='photos'&&!photoTotalOf())entityMediaView=emptyMediaView();
  renderEntityMediaToggle(kind,name,filters);
  if(entityMediaView.media!=='photos')renderEntityCollection(kind,name,items,filters);
  else if(entityMediaView.set)await openPhotoSet(kind,name,filters,entityMediaView.set,false);
  else renderPhotoWall(kind,name,filters,entityPhotos);
  buildBars();
  window.scrollTo({top:0,behavior:'smooth'});
}

let drawerSuppressUntil=0;
const openDrawer=v=>{$('#drawer').classList.toggle('open',v);$('#scrim').classList.toggle('on',v);
  document.body.classList.toggle('drawer-open',!!v)};
const closeDrawerAfterNav=()=>{drawerSuppressUntil=Date.now()+650;openDrawer(false)};
$('#filterBtn').onclick=()=>openDrawer(!$('#drawer').classList.contains('open'));
/* 常驻窄图标条：点即切视图，鼠标停留 180ms 展开完整抽屉 */
const EDGE_ICONS=[
  ['','首页','home'],
  ['performers','艺人','user-round'],
  ['tags','标签','tags'],
  ['jav','JAV','jav'],
  ['flagged','已标记','star'],
  ['playlists','播放列表','list-filter'],
  ['follow','关注','rss'],
  ['immerse','沉浸模式','play'],
  ['manage','管理','database'],
];
/* 统计、垃圾文件、回收站、人工复核默认都收在「管理」下，不主动占用顶层空间；
   用户仍可在设置里把某个具体页面加到顶层。每个页面都有可直接打开的 URL。
   顺序按做事顺序分成两段：先是库里已有的东西——看现状、复核新进来的候选、
   清广告与重复、落到回收站；再是要往外拿的——关注和高清版都是「还想要什么」，
   原先把它夹在高清版和回收站中间，两边都不挨着。 */
const MANAGE_SECTIONS=[
  ['stats','统计','chart'],
  ['taste','口味','heart'],
  ['review','人工复核','square-check-big'],
  ['ads','垃圾文件','alert'],
  ['dupes','重复文件','hard-drive'],
  ['trash','回收站','trash'],
  ['follow','关注','rss'],
  ['quality','高清版','sparkles'],
];
const OPTIONAL_EDGE_ICONS=MANAGE_SECTIONS.map(([key,label,ic])=>
  key==='follow'?['follow-manage','关注管理',ic]:[key,label,ic]);
const NAV_CATALOG=[...EDGE_ICONS,...OPTIONAL_EDGE_ICONS];
const DIRECT_MANAGE_NAV={stats:'stats',review:'review',ads:'ads',dupes:'dupes',trash:'trash','follow-manage':'follow',quality:'quality'};
function orderedEdgeIcons(){
  const byKey=new Map(NAV_CATALOG.map(item=>[item[0],item]));
  return appSettings.sidebarOrder.map(key=>byKey.get(key)).filter(Boolean);
}
/* 侧栏顺序跟账本走，不跟浏览器走：在 Windows 上排好，Mac 上就该是同一份。
   本地那份仍然写，但只当首屏缓存（见 loadSyncedSettings）。
   写服务端失败不回滚也不打断：reader 会返回 409，本地顺序照样已经生效，
   只是这次改动不跨机同步——那是只读端的既定约束，不是操作失败。 */
function saveSidebarSetting(){
  saveSettings();renderSidebarOrderSetting();buildEdge();buildBars();
  api('/api/settings',{method:'POST',
    body:JSON.stringify({sidebarOrder:appSettings.sidebarOrder})}).catch(()=>{});
}
/* 启动时用账本上的那份纠正本地缓存。
   不等它回来再画侧栏：侧栏在首屏就要出现，等一个网络往返会闪一下。
   所以先用本地缓存画，服务端回来后只有真的不一致才重绘。 */
async function loadSyncedSettings(){
  let remote=null;
  try{remote=await api('/api/settings')}catch(_e){return}
  const order=Array.isArray(remote&&remote.sidebarOrder)?remote.sidebarOrder:null;
  if(!order||!order.length||order.join(',')===appSettings.sidebarOrder.join(','))return;
  appSettings.sidebarOrder=order;
  saveSettings();renderSidebarOrderSetting();buildEdge();buildBars();wireAllDrag();
}
function moveSidebarItem(key,targetKey,after=false){
  if(key===targetKey)return;
  const next=[...appSettings.sidebarOrder],from=next.indexOf(key);
  if(from<0)return;
  next.splice(from,1);
  const target=next.indexOf(targetKey);
  if(target<0)return;
  next.splice(target+(after?1:0),0,key);
  appSettings.sidebarOrder=next;saveSidebarSetting();
}
function wireNavigationDrag(root){
  if(!root)return;
  const items=[...root.querySelectorAll(':scope > [data-nav]')];
  items.forEach(item=>{
    if(root.id==='edge')item.onpointerdown=()=>{
      // 按下时就决定是点击或拖动；不能让 180ms 悬停计时器在按住期间把窄栏换成抽屉。
      clearTimeout(edgeT);edgeT=null;drawerSuppressUntil=Date.now()+900;
    };
    item.ondragstart=e=>{
      sidebarDragKey=item.dataset.nav;item.classList.add('nav-dragging');
      e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',sidebarDragKey||'__home__');
    };
    item.ondragover=e=>{
      if(sidebarDragKey===null||sidebarDragKey===item.dataset.nav)return;
      e.preventDefault();e.dataTransfer.dropEffect='move';
      const after=e.clientY>item.getBoundingClientRect().top+item.offsetHeight/2;
      items.forEach(node=>node.classList.remove('nav-drop-before','nav-drop-after'));
      item.classList.add(after?'nav-drop-after':'nav-drop-before');
    };
    item.ondrop=e=>{
      e.preventDefault();
      const after=item.classList.contains('nav-drop-after'),target=item.dataset.nav,key=sidebarDragKey;
      sidebarDragKey=null;moveSidebarItem(key,target,after);
    };
    item.ondragend=()=>{
      sidebarDragKey=null;items.forEach(node=>node.classList.remove('nav-dragging','nav-drop-before','nav-drop-after'));
    };
  });
}
let sidebarDragKey=null;
function renderSidebarOrderSetting(){
  const root=$('#sidebarOrderSetting');if(!root)return;
  const byKey=new Map(NAV_CATALOG.map(item=>[item[0],item]));
  const visible=appSettings.sidebarOrder.map(key=>byKey.get(key)).filter(Boolean);
  const available=NAV_CATALOG.filter(([key])=>!appSettings.sidebarOrder.includes(key));
  const rows=visible.map(([key,label,ic],index)=>
    `<div class="sidebarorderrow" draggable="true" data-sidebar-row="${esc(key)}">
      <span class="sidebarorderlabel"><i class="sidebardrag" aria-hidden="true">${icon('grip-vertical')}</i>${icon(ic)}<b>${esc(label)}</b></span><span class="sidebarorderactions">
      <button data-sidebar-key="${esc(key)}" data-sidebar-move="-1" aria-label="上移 ${esc(label)}" title="上移"${index===0?' disabled':''}>${icon('chevron-up')}</button>
      <button data-sidebar-key="${esc(key)}" data-sidebar-move="1" aria-label="下移 ${esc(label)}" title="下移"${index===visible.length-1?' disabled':''}>${icon('chevron-down')}</button>
      <button data-sidebar-key="${esc(key)}" data-sidebar-hide aria-label="隐藏 ${esc(label)}" title="隐藏"${visible.length===1?' disabled':''}>${icon('eye-off')}</button></span></div>`).join('');
  const firstValue=available.length?(available[0][0]===''?'__home__':available[0][0]):'';
  root.innerHTML=rows+`<div class="sidebaradd"><div class="sidebaraddpicker">
      <button type="button" class="sidebaraddfield" data-sidebar-add-trigger aria-haspopup="listbox" aria-expanded="false"${available.length?'':' disabled'}>
        ${available.length?`${icon(available[0][2])}<span data-sidebar-add-label>${esc(available[0][1])}</span>${icon('chevron-down')}`:`${icon('check')}<span>全部页面都已显示</span>`}
      </button>
      ${available.length?`<div class="sidebaraddmenu" data-sidebar-add-menu role="listbox" aria-label="选择要添加的页面" hidden>${available.map(([key,label,ic],index)=>
        `<button type="button" role="option" data-sidebar-add-option="${esc(key===''?'__home__':key)}" aria-selected="${index===0}" tabindex="${index===0?'0':'-1'}">${icon(ic)}<span>${esc(label)}</span></button>`).join('')}</div>`:''}
    </div>
    <button data-sidebar-add${available.length?'':' disabled'}>${icon('plus')}<span>添加</span></button></div>`;
  let selectedAddKey=firstValue;
  const addTrigger=root.querySelector('[data-sidebar-add-trigger]'),addMenu=root.querySelector('[data-sidebar-add-menu]');
  const closeAddMenu=()=>{if(!addMenu)return;addMenu.hidden=true;addTrigger.setAttribute('aria-expanded','false')};
  addTrigger?.addEventListener('click',()=>{
    if(!addMenu)return;const opening=addMenu.hidden;addMenu.hidden=!opening;addTrigger.setAttribute('aria-expanded',String(opening));
    if(opening)addMenu.querySelector('[aria-selected="true"]')?.focus();
  });
  addMenu?.querySelectorAll('[data-sidebar-add-option]').forEach(option=>{
    option.onclick=()=>{
      selectedAddKey=option.dataset.sidebarAddOption;
      addMenu.querySelectorAll('[role="option"]').forEach(item=>{item.setAttribute('aria-selected',String(item===option));item.tabIndex=item===option?0:-1});
      const item=NAV_CATALOG.find(([key])=>(key===''?'__home__':key)===selectedAddKey);
      if(item)addTrigger.innerHTML=`${icon(item[2])}<span data-sidebar-add-label>${esc(item[1])}</span>${icon('chevron-down')}`;
      closeAddMenu();addTrigger.focus();
    };
    option.onkeydown=e=>{
      if(e.key==='Escape'){e.preventDefault();closeAddMenu();addTrigger.focus();return}
      const all=[...addMenu.querySelectorAll('[role="option"]')],at=all.indexOf(option);
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();all[(at+(e.key==='ArrowDown'?1:-1)+all.length)%all.length].focus()}
    };
  });
  root.querySelector('.sidebaraddpicker')?.addEventListener('focusout',e=>{
    if(!e.currentTarget.contains(e.relatedTarget))closeAddMenu();
  });
  root.querySelectorAll('[data-sidebar-move]').forEach(button=>button.onclick=()=>{
    const from=appSettings.sidebarOrder.indexOf(button.dataset.sidebarKey),to=from+(+button.dataset.sidebarMove);
    if(from<0||to<0||to>=appSettings.sidebarOrder.length)return;
    const next=[...appSettings.sidebarOrder];[next[from],next[to]]=[next[to],next[from]];
    appSettings.sidebarOrder=next;saveSidebarSetting();
  });
  root.querySelectorAll('[data-sidebar-hide]').forEach(button=>button.onclick=()=>{
    if(appSettings.sidebarOrder.length<=1)return;
    appSettings.sidebarOrder=appSettings.sidebarOrder.filter(key=>key!==button.dataset.sidebarKey);
    saveSidebarSetting();
  });
  root.querySelector('[data-sidebar-add]')?.addEventListener('click',()=>{
    const key=selectedAddKey==='__home__'?'':selectedAddKey;
    if(key===undefined||appSettings.sidebarOrder.includes(key)||!ALL_SIDEBAR_KEYS.includes(key))return;
    appSettings.sidebarOrder=[...appSettings.sidebarOrder,key];saveSidebarSetting();
  });
  root.querySelectorAll('[data-sidebar-row]').forEach(row=>{
    row.ondragstart=e=>{
      sidebarDragKey=row.dataset.sidebarRow;row.classList.add('dragging');
      e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',sidebarDragKey||'__home__');
    };
    row.ondragover=e=>{
      if(sidebarDragKey===null||sidebarDragKey===row.dataset.sidebarRow)return;
      e.preventDefault();e.dataTransfer.dropEffect='move';
      const after=e.clientY>row.getBoundingClientRect().top+row.offsetHeight/2;
      root.querySelectorAll('[data-sidebar-row]').forEach(item=>item.classList.remove('drop-before','drop-after'));
      row.classList.add(after?'drop-after':'drop-before');
    };
    row.ondrop=e=>{
      e.preventDefault();
      const after=row.classList.contains('drop-after'),target=row.dataset.sidebarRow,key=sidebarDragKey;
      sidebarDragKey=null;moveSidebarItem(key,target,after);
    };
    row.ondragend=()=>{
      sidebarDragKey=null;root.querySelectorAll('[data-sidebar-row]').forEach(item=>item.classList.remove('dragging','drop-before','drop-after'));
    };
  });
}
function manageSection(){
  const path=decodeURIComponent(location.pathname);
  if(path==='/stats')return 'stats';
  if(path==='/taste')return 'taste';
  if(path==='/review')return 'review';
  if(path==='/trash')return 'trash';
  if(path==='/duplicates')return 'dupes';
  if(path==='/quality-goals')return 'quality';
  if(path==='/follow-manage')return 'follow';
  return path==='/junk-files'||state.state==='ads'?'ads':'';
}
function buildManageBar(){
  const current=manageSection(),bar=$('#managebar');
  bar.hidden=!current;
  // 管理区是行政界面，不该顶着首页的人物/厂牌横条和标签筛选。
  // 隐藏 tagbar 的同时同步 count 栏的吸顶偏移：它默认按「顶栏+筛选条」留位，
  // 筛选条不在时那个偏移会留出一条 58px 的缝，滚动内容从缝里穿出来。
  if(current){$('#tiers').style.display='none';$('#tagbar').style.display='none'}
  $('#count').classList.toggle('no-tagbar',!!current);
  buildEdge();     // 顶层高亮跟随管理区；否则从首页进来时仍停在「首页」上
  paintJavBar();
  paintManageTitle();
  if(!current)return;
  const entry=MANAGE_SECTIONS.find(([k])=>k===current);
  bar.classList.remove('is-open');
  bar.innerHTML=`<button class="managebar-toggle" type="button" aria-expanded="false" aria-controls="managebar-menu">
      <span class="managebar-current">${icon(entry[2])}<span>管理 · ${entry[1]}</span></span>${icon('chevron-down')}
    </button><div class="managebar-menu" id="managebar-menu">${MANAGE_SECTIONS.map(([k,label,ic])=>
      `<button data-manage="${k}" aria-pressed="${k===current}">${icon(ic)}<span>${label}</span></button>`).join('')}</div>`;
  const toggle=bar.querySelector('.managebar-toggle');
  toggle.onclick=()=>{const open=bar.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open))};
  toggle.onkeydown=event=>{if(event.key==='Escape'){bar.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');toggle.focus()}};
  bar.querySelectorAll('[data-manage]').forEach(b=>b.onclick=()=>openManage(b.dataset.manage));
}
/* 管理区分页共用同一个标题元素。回收站和垃圾文件走首页网格路径，
   本来就没有标题层；统计/复核/重复各自内嵌 h2 又导致字号不一致。 */
function paintManageTitle(){
  const current=manageSection(),el=$('#manageTitle');
  if(!el)return;
  document.body.classList.toggle('insight-layout',current==='stats'||current==='taste');
  const entry=MANAGE_SECTIONS.find(([k])=>k===current);
  el.hidden=!entry;
  if(entry)el.textContent=entry[1];
  paintManageLede();
}
function paintManageLede(text=''){
  const el=$('#manageLede');if(!el)return;
  el.hidden=!text;el.textContent=text;
}
function paintListTitle(){
  const el=$('#listTitle');if(!el)return;
  const path=decodeURIComponent(location.pathname);
  const label=!manageSection()&&isCatalogPath(path)?STATE_LABELS[state.state]||'':'';
  el.hidden=!label;if(label)el.textContent=label;
}
function openManage(section='stats'){
  if(section==='stats'){openStats();return}
  if(section==='taste'){openTaste();return}
  if(section==='review'){openReview();return}
  if(section==='dupes'){openDuplicates();return}
  if(section==='quality'){openQualityGoals();return}
  if(section==='follow'){openFollowManage();return}
  state.orient='';state.state=section==='trash'?'trash':'ads';
  route(section==='trash'?'/trash':junkPath());
  showHomeSurfaces();buildEdge();buildBars();load(true);
}
/* JAV 模式。只有带番号的作品才有官方封套，所以版式切换只在这个语境里出现——
   首页混着创作者作品和素人流出，给它们切「封面」没有意义。
   资料页（女优/厂牌）进入时继承这个开关，因为那里同样是按番号浏览。 */
const JAV_LAYOUTS=[['big','大图 · 只看正封','maximize'],['small','小图 · 整张封套','layout-grid'],
  ['preview','预览图','eye']];
/* 旧键沿用：设置存在浏览器里，改名不能让用户的选择静默回落到默认值。 */
const JAV_LAYOUT_ALIASES={cover:'big',sleeve:'small'};
function javActive(){
  const path=decodeURIComponent(location.pathname);
  if(path==='/')return state.jav==='1';
  if(path.startsWith('/performers/')||path.startsWith('/studios/'))
    return state.jav==='1'||entityJavLayout;
  return false;
}
/* 发行时间只对有正式发行证据的番号列表有意义。普通馆藏继续使用入库时间，
   避免把大量空日期的创作者作品挂上一个看似可用、实际无值的排序。 */
const sortOptions=()=>javActive()?[JAV_RELEASE_SORT,...SORTS]:SORTS;
function javLayout(){
  const raw=JAV_LAYOUT_ALIASES[appSettings.javLayout]||appSettings.javLayout;
  return allowedSetting(raw,JAV_LAYOUTS.map(([k])=>k),'big');
}
const javLayoutButtons=()=>`<fieldset class="javlayout"><legend class="sr-only">JAV 卡片版式</legend>`+JAV_LAYOUTS.map(([k,label,ic])=>
  `<label title="${esc(label)}"><input type="radio" name="jav-layout" value="${k}" data-jav-layout
    ${k===javLayout()?'checked':''}><span aria-hidden="true">${icon(ic)}</span><span class="sr-only">${esc(label)}</span></label>`).join('')+`</fieldset>`;
const wireJavLayoutButtons=root=>root?.querySelectorAll('[data-jav-layout]').forEach(b=>
  b.onchange=()=>{if(b.checked)setJavLayout(b.value)});
function setJavLayout(value){
  appSettings.javLayout=value;
  saveSettings();
  // 只重画卡片，不重新请求：版式是纯展示层的事。资料页保留已经载入的分页。
  const index=$('#index'),kind=index?.dataset.entityKind,name=index?.dataset.entityName;
  if(kind&&name&&!index.hidden&&entityMediaView.media!=='photos'){
    renderEntityCollection(kind,name,{...entityCollectionPage,items:[...entityCollectionPage.items]},
      barsContext.type==='entity'?barsContext.filters:emptyEntityFilters());
    return;
  }
  if(!$('#grid').hidden)load(true);
}
function paintJavBar(){
  // 版式按钮现在长在排序行里（见 renderCount），这里只负责收掉旧容器。
  const bar=$('#javbar');if(bar)bar.hidden=true;
}
function toggleJavMode(){
  state.jav=state.jav==='1'?'':'1';
  if(state.jav!=='1'&&state.sort==='release')state.sort='seed';
  state.state='';state.orient='';
  route(state.jav==='1'?'/?jav=1':'/');
  showHomeSurfaces();buildEdge();buildBars();load(true);
}
/* 批量操作后回到刚才那一页，而不是首页列表。
   实体资料页、索引页和管理区各有自己的取数路径，`load(true)` 只会重建首页网格，
   于是在女优页选一批进回收站后会被莫名其妙地扔回首页。 */
async function reloadCurrentSurface(){
  const index=$('#index');
  const kind=index?.dataset.entityKind,name=index?.dataset.entityName;
  if(kind&&name&&!index.hidden){
    await updateEntityCollection(kind,name,parseEntityFilters(location.search),false);
    return;
  }
  const path=decodeURIComponent(location.pathname);
  if(path==='/performers'||path==='/creators'||path==='/tags'){
    await openIndex(path.slice(1),$('#iq')?.value.trim()||'',false);
    return;
  }
  if(path==='/follow'){await openFollow(false);return}
  await load(true);
}
function navOn(k){
  const path=decodeURIComponent(location.pathname);
  const directSection=DIRECT_MANAGE_NAV[k];
  if(directSection)return manageSection()===directSection;
  if(k==='manage'){
    const current=manageSection();
    return !!current&&!orderedEdgeIcons().some(([key])=>DIRECT_MANAGE_NAV[key]===current);
  }
  if(k==='performers'||k==='tags')return path==='/'+k;
  if(k==='immerse')return path==='/immerse';
  if(k==='playlists')return path==='/playlists'||path.startsWith('/playlists/');
  if(k==='follow')return path==='/follow';
  if(k==='jav')return javActive();
  if(k==='shorts')return state.orient==='竖屏';
  // 首页只在真的停在首页列表上时亮：管理区、索引页、实体页都不算，
  // 否则它会和当前所在的入口同时高亮。
  if(k==='')return path==='/'&&!manageSection()&&!state.state&&!javActive()&&state.orient!=='竖屏';
  if(STATE_ROUTES[k])return path===STATE_ROUTES[k]&&state.orient!=='竖屏';
  return path==='/'&&state.state===k&&state.orient!=='竖屏';
}
/* 窄栏与抽屉共用同一套跳转。两边曾各写一份分支，抽屉那份漏了追更和播放列表，
   点下去只把 state.state 设成一个后端不认识的值，看上去就是“点了没反应”。 */
function navTo(k){
  closeDrawerAfterNav();                 // 点了就收起抽屉，且短暂禁止悬停把它立刻弹回
  if(DIRECT_MANAGE_NAV[k]){openManage(DIRECT_MANAGE_NAV[k]);return}
  if(k==='immerse'){openTok();return}
  if(k==='playlists'){openPlaylists();return}
  if(k==='follow'){openFollow();return}
  if(k==='manage'){openManage();return}
  if(k==='jav'){toggleJavMode();return}
  if(k===''){openHome();return}
  if(k==='performers'||k==='tags'){setSelectMode(false,true);openIndex(k);return}
  if(k==='shorts'){state.orient='竖屏';state.state=''}else{state.orient='';state.state=k}
  route(homePath());
  showHomeSurfaces();
  buildEdge();buildBars();load(true);
}
function syncHeaderActions(){
  const path=decodeURIComponent(location.pathname),parts=path.split('/').filter(Boolean);
  if(selectMode&&selectSurface!==currentSelectSurface())
    setSelectMode(false,true);
  const entity=parts.length>1&&Object.prototype.hasOwnProperty.call(ROUTE_ENTITIES,parts[0]);
  const catalog=isCatalogPath(path)||path==='/trash';
  const canSelect=catalog||entity||path==='/tags'||path==='/follow';
  const canDensity=catalog||entity||path==='/follow';
  $('#selectMode').hidden=!canSelect;$('#density').hidden=!canDensity;
  if(!canSelect&&selectMode)setSelectMode(false,true);
}
function buildEdge(){
  $('#edge').innerHTML=orderedEdgeIcons().map(([k,t,ic])=>
    `<button data-nav="${k}" draggable="true" title="${t}" aria-pressed="${navOn(k)}">
      ${icon(ic)}</button>`).join('')
;
  $('#edge').querySelectorAll('[data-loc]').forEach(b=>b.onclick=()=>{
    const cur=(state.loc||'').split(',').filter(Boolean);
    const i=cur.indexOf(b.dataset.loc);
    i>=0?cur.splice(i,1):cur.push(b.dataset.loc);
    state.loc=cur.join(',');
    buildEdge(); buildBars(); load(true);
  });
  $('#edge').querySelectorAll('[data-nav]').forEach(b=>b.onclick=e=>{
    e.stopPropagation();navTo(b.dataset.nav)});
  wireNavigationDrag($('#edge'));
  syncHeaderActions();
}
let edgeT=null;
$('#edge').addEventListener('mouseenter',()=>{if(Date.now()<drawerSuppressUntil)return;
  edgeT=setTimeout(()=>openDrawer(true),180)});
/* 滚动期间挂起悬停预览：内容在鼠标下滑过会连续触发 mouseenter，
   每次都新建 video 并发起 /stream 请求，直接把页面拖垮。 */
window.__scrolling=false; let scrollT=null;
let stickyFrame=0;
function updateStickySurfaces(){
  ['#tagbar','#count','.entitytagbar','.entitycollectionhead'].forEach(selector=>{
    const el=$(selector),css=el&&getComputedStyle(el),top=css?parseFloat(css.top):NaN;
    const stuck=!!el&&css.position==='sticky'&&el.offsetParent!==null&&window.scrollY>0&&
      Number.isFinite(top)&&el.getBoundingClientRect().top<=top+1;
    if(el)el.classList.toggle('is-stuck',stuck);
  });
}
function scheduleStickySurfaces(){
  if(stickyFrame)return;
  stickyFrame=requestAnimationFrame(()=>{stickyFrame=0;updateStickySurfaces()});
}
window.addEventListener('scroll',()=>{
  scheduleStickySurfaces();
  window.__scrolling=true;
  // 滚动中挂起悬停预览：内容从鼠标下滑过会连续触发 mouseenter，
  // 每次新建 video 并发 /stream，几十个并发直接把页面拖垮
  releaseHoverPreviews();
  clearTimeout(scrollT); scrollT=setTimeout(()=>{window.__scrolling=false},180);
},{passive:true});
window.addEventListener('resize',()=>{scheduleStickySurfaces();alignFollowImageControls()},{passive:true});

/* 只在真正进入 72 px 图标栏时展开；内容区左缘不再设隐形热区。 */
$('#edge').addEventListener('mouseleave',()=>clearTimeout(edgeT));
$('#drawer').addEventListener('mouseleave',()=>{
  setTimeout(()=>{if(!$('#drawer').matches(':hover')&&!$('#edge').matches(':hover'))openDrawer(false)},240)});
$('#scrim').onclick=()=>openDrawer(false);

/* ── 列表 ── */
async function load(reset){
  const requestSeq=reset?++loadRequestSeq:loadRequestSeq;
  const surface=reset?claimSurface(surfacePath()):surfaceToken(surfacePath());
  if(!reset&&listLoading)return;
  if(!reset)listLoading=true;
  try{
  if(reset){barsContext={type:'home',filters:state};detailReturnBarsContext=null;disposeStage(false);
    renderCatalogLoading(state.state==='ads'?'正在读取资源':'正在读取作品')}
  showHomeSurfaces();
  if(reset){offset=0;renderedPartGroups.clear()}
  renderCombo();
  // 垃圾文件是逐项处置队列，计数只是当前队列说明，不是需要跟随浏览的排序工具。
  const countRow=$('#count'),staticManageCount=state.state==='ads';
  countRow.classList.toggle('manage-static',staticManageCount);
  countRow.classList.toggle('junkcount',staticManageCount);
  if(staticManageCount)countRow.classList.remove('is-stuck');
  if(state.state==='ads'){
    if(reset||!adsBatch){const junkQuery=new URLSearchParams({limit:'200',status:junkView});if(junkKind)junkQuery.set('kind',junkKind);
      const nextAds=await api('/api/ads?'+junkQuery);if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;
      adsBatch=nextAds;cache(adsBatch.items)}
    const batch=adsBatch.items.slice(offset,offset+appSettings.batchSize);
    const html=batch.map(junkCardHtml).join('');
    if(reset)releaseHoverPreviews($('#grid'));
    if(reset&&!batch.length)$('#grid').innerHTML=emptyState('check',junkView==='dismissed'?'没有已排除的文件':'没有待判断的垃圾文件',junkView==='dismissed'?'点“不是垃圾”的资源会保留在这里，可随时重新判断。':'当前分类没有候选文件。');
    else if(reset)$('#grid').innerHTML=html;else $('#grid').insertAdjacentHTML('beforeend',html);
    renderJunkNavigation(adsBatch);
    $('#loadSentinel').hidden=$('#grid').children.length>=adsBatch.items.length;
    $('#shortsSec').hidden=true;wireJunkCards($('#grid'));paintSelection();return;
  }
  adsBatch=null;
  const p=new URLSearchParams(Object.entries(state).filter(([,v])=>v));
  /* 只有首页默认列表排除竖屏——那里另有独立的竖屏条承接它们。
     搜索必须能搜到竖屏作品，否则按名字找一条竖屏视频会得到 0 结果。 */
  if(isCatalogPath(decodeURIComponent(location.pathname))&&!state.q&&!state.orient)p.set('exclude_vertical','1');
  // JAV 模式恒不含竖屏：番号发行物本身就是横版，竖屏是另一类内容。
  if(state.jav==='1')p.set('exclude_vertical','1');
  p.set('limit',appSettings.batchSize); p.set('offset',offset);
  if(!reset)p.set('count','0');
  const d=await api('/api/items?'+p);cache(d.items);
  if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;
  if(reset)total=d.total;
  buildManageBar();
  const html=state.state==='trash'?d.items.map(resourceCardHtml).join('')
    :batchWithMix(d.items,isCatalogPath(decodeURIComponent(location.pathname))&&state.state!=='trash');
  if(reset)releaseHoverPreviews($('#grid'));
  if(reset&&state.state==='trash'&&!d.items.length)
    $('#grid').innerHTML=emptyState('trash','回收站是空的','删掉的内容会先到这里；确认不再需要后再清空。');
  else if(reset&&!d.items.length)
    $('#grid').innerHTML=emptyState('search','没有符合条件的作品','调整筛选或搜索条件后再试。');
  else if(reset)$('#grid').innerHTML=html;
  else $('#grid').insertAdjacentHTML('beforeend',html);
  renderCount();
  $('#loadSentinel').hidden=reset?d.items.length>=total:!d.has_more;
  wireCards($('#grid'),state.state==='trash'?openResourceCard:undefined);
  if(state.state==='trash')wireResourceCardActions($('#grid'));
  wireMixCards($('#grid'));
  paintSelection();
  if(reset)loadShorts(requestSeq,surface);
  }finally{if(!reset&&requestSeq===loadRequestSeq)listLoading=false}
}
const loadObserver=new IntersectionObserver(entries=>{
  if(entries.some(x=>x.isIntersecting)&&!listLoading&&!$('#loadSentinel').hidden&&$('#stats').hidden&&$('#index').hidden){
    offset+=appSettings.batchSize;load(false)}
},{rootMargin:'320px'});
loadObserver.observe($('#loadSentinel'));
const SEARCH_HINTS=['Prestige','FC2','Sakura Misaki','丝袜','足交','ABW'];
/* 推荐词取自真实数据，所以每一条都保证能搜到东西；写死的常量池只有 6 个词，
   翻两次就重复。顶部聚合只给几十条，不够；索引接口一次能给近千条名字。 */
let searchPoolCache=null;
function searchPool(){
  if(searchPoolCache&&searchPoolCache.length)return searchPoolCache;
  const pool=[];
  const take=list=>(list||[]).forEach(x=>{const v=x&&x.k;if(v)pool.push(String(v))});
  if(typeof facets==='object'&&facets){take(facets.creators);take(facets.tagperformers);take(facets.tags)}
  const seen=new Set();
  const unique=pool.filter(v=>v.length>1&&!seen.has(v)&&seen.add(v));
  return unique.length>=8?unique:SEARCH_HINTS;
}
async function loadSearchPool(){
  if(searchPoolCache)return searchPoolCache;
  try{
    const lists=await Promise.all(['performers','creators','tags'].map(
      kind=>api(`/api/index?kind=${kind}&limit=400`)));
    const seen=new Set();
    const names=lists.flatMap(d=>(d.items||[]).map(x=>String(x.k||'')))
      .filter(v=>v.length>1&&!seen.has(v)&&seen.add(v));
    if(names.length>=50)searchPoolCache=names;
  }catch(e){/* 取不到就退回聚合结果，不影响搜索本身 */}
  return searchPool();
}
const searchSuggestion=SEARCH_HINTS[Math.floor(Math.random()*SEARCH_HINTS.length)];
$('#q').dataset.suggestion=searchSuggestion;$('#q').placeholder=searchSuggestion;
let searchHistory=[];
const readSearchHistory=()=>searchHistory.slice(0,appSettings.searchHistoryLimit);
const loadSearchHistory=()=>api('/api/search-history?limit='+appSettings.searchHistoryLimit).then(d=>{searchHistory=Array.isArray(d.items)?d.items:[];return searchHistory}).catch(()=>searchHistory);
const writeSearchHistory=list=>{searchHistory=list.slice(0,appSettings.searchHistoryLimit);return searchHistory};
// 搜索本身是只读能力；账本暂时只读时，历史记录降级为本次页面内存，不能让一个
// 非关键 POST 变成未处理异常或妨碍搜索结果。
const rememberSearch=async query=>{if(!query)return;
  writeSearchHistory([query,...readSearchHistory().filter(x=>foldName(x)!==foldName(query))]);
  await api('/api/search-history',{method:'POST',body:JSON.stringify({query})}).catch(()=>null)};
function renderSearchMenu(){const menu=$('#searchMenu'),history=readSearchHistory();
  const recommendations=[...searchPool()].sort(()=>Math.random()-.5).filter(x=>!history.some(h=>foldName(h)===foldName(x))).slice(0,5);
  const row=(value,type)=>`<div class="searchoption" data-search-value="${esc(value)}">${icon(type==='history'?'history':'sparkles')}<span>${esc(value)}</span>${type==='history'?`<button class="removehistory" data-remove-history="${esc(value)}" aria-label="删除历史 ${esc(value)}">${icon('x')}</button>`:''}</div>`;
  menu.innerHTML=(history.length?`<section class="searchgroup"><h3>搜索记录</h3>${history.map(x=>row(x,'history')).join('')}</section>`:'')+
    `<section class="searchgroup"><h3>推荐</h3>${recommendations.map(x=>row(x,'recommend')).join('')}</section>`;
  menu.hidden=false;searchActive=-1;
  menu.querySelectorAll('[data-search-value]').forEach(x=>x.onclick=e=>{if(e.target.closest('[data-remove-history]'))return;
    $('#q').value=x.dataset.searchValue;runSearch(false,true);menu.hidden=true});
  menu.querySelectorAll('[data-remove-history]').forEach(b=>{
    /* 按下就 preventDefault，不让删除按钮把焦点从输入框抢走。抢走会触发 `#q` 的
       blur，那个 handler 140ms 后无条件 `hidden=true`，于是「删一条记录」实际等于
       「关掉整个下拉栏」。 */
    b.onmousedown=e=>e.preventDefault();
    b.onclick=async e=>{
      e.stopPropagation();
      const value=b.dataset.removeHistory;
      await api('/api/search-history',{method:'POST',body:JSON.stringify({operation:'remove',query:value})}).catch(()=>null);
      writeSearchHistory(readSearchHistory().filter(x=>foldName(x)!==foldName(value)));
      /* 只摘掉这一行，不整段重建：`renderSearchMenu` 每次都会把推荐词重新洗牌，
         删一条历史却换了一批推荐，看着像列表自己跳了。 */
      const row=b.closest('[data-search-value]'),group=row&&row.closest('.searchgroup');
      if(row)row.remove();
      if(group&&!group.querySelector('[data-search-value]'))group.remove();
      // 行没了，键盘选中的下标就不再指向原来那一项，归零重来。
      searchActive=-1;
      menu.querySelectorAll('[data-search-value]').forEach(x=>x.classList.remove('active'));
    };
  })}
const runSearch=(useSuggestion=false,committed=false)=>{let query=$('#q').value.trim();
  if(useSuggestion&&!query){query=$('#q').dataset.suggestion||'';$('#q').value=query}
  if(committed)rememberSearch(query);
  disposeStage(false);
  state.q=query;route(state.q?'/?q='+encodeURIComponent(state.q):'/',true);load(true)};
/* 下拉里被键盘选中的那一项。列表每次重建都要归零，否则索引会指向已经不存在的行。 */
let searchActive=-1;
const searchOptions=()=>{const menu=$('#searchMenu');
  return menu.hidden?[]:[...menu.querySelectorAll('[data-search-value]')]};
function moveSearchActive(step){
  const options=searchOptions();if(!options.length)return false;
  searchActive=(searchActive+step+options.length)%options.length;
  options.forEach((option,index)=>option.classList.toggle('active',index===searchActive));
  options[searchActive].scrollIntoView({block:'nearest'});
  return true;
}
$('#q').oninput=()=>{searchActive=-1;if(!$('#searchMenu').hidden)renderSearchMenu()};
$('#q').onkeydown=e=>{
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){
    if(moveSearchActive(e.key==='ArrowDown'?1:-1))e.preventDefault();
    return;
  }
  if(e.key!=='Enter')return;
  e.preventDefault();
  const picked=searchOptions()[searchActive];
  if(picked)$('#q').value=picked.dataset.searchValue;
  searchActive=-1;
  // 选中某一项时用它原样搜索；没选中才回退到「空输入按 Enter 用推荐词」。
  runSearch(!picked,true);
  $('#searchMenu').hidden=true;$('#q').blur();
};
$('#q').addEventListener('focus',()=>{Promise.all([loadSearchHistory(),loadSearchPool()]).then(renderSearchMenu)});

const SHORTS_ROW_OFFSET=2;   // 竖屏条插在第几行之后，0 表示置顶
async function loadShorts(requestSeq=loadRequestSeq,surface=surfaceToken(surfacePath())){
  // JAV 模式不插竖屏条：番号发行物本身是横版，竖屏是另一类内容。
  // 主列表的 exclude_vertical 管不到这条——它是独立请求、独立插入的。
  if(!isCatalogPath(decodeURIComponent(location.pathname))||javActive()||state.orient==='竖屏'
     ||state.state==='ads'||state.state==='trash'){
    $('#shortsSec').hidden=true;$('#grid').querySelector('#shortsInline')?.remove();return}
  const p=new URLSearchParams(Object.entries(state).filter(([,v])=>v));
  /* 排序跟着主列表走，不再写死 sort=new；换一批时竖屏条也要一起换。 */
  p.set('orient','竖屏');p.set('limit',18);p.set('offset',0);
  const d=await api('/api/items?'+p);
  if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;
  if(!d.items.length){$('#shortsSec').hidden=true;return}
  cache(d.items);
  releaseHoverPreviews($('#srow'));
  const grid=$('#grid');grid.querySelector('#shortsInline')?.remove();
  /* 竖屏条整行占位（grid-column:1/-1），插在行边界上才不会把上一行截断留空。
     早先的做法是另拉一批横屏视频补满余位，但那批 id 不在分页序列里，
     翻下一页必然重复，而且被当成 scard 渲染会把横屏压成竖框。 */
  const columns=Math.max(1,getComputedStyle(grid).gridTemplateColumns.split(' ').length);
  const cards=[...grid.children].filter(x=>x.matches('.card[data-id]'));
  const anchor=cards[Math.min(cards.length,columns*SHORTS_ROW_OFFSET)]||null;
   const inline=`<section class="shorts-inline" id="shortsInline"><h2 class="disp">竖屏 <span class="mono" style="color:var(--muted);font-size:11px">${d.total.toLocaleString()} 个</span><button class="shorts-enter" type="button">${icon('play')}<span>进入沉浸模式</span></button></h2><div class="srow">${d.items.map(it=>cardHtml(it,'scard')).join('')}</div></section>`;
  if(anchor)anchor.insertAdjacentHTML('beforebegin',inline); else grid.insertAdjacentHTML('beforeend',inline);
  const section=grid.querySelector('#shortsInline');
  section.querySelector('.shorts-enter').onclick=()=>openTok();
  wireCards(section.querySelector('.srow'),openTok); wireDrag(section.querySelector('.srow'));
}

/* ── 就地展开播放 ── */
function queueHtml(queue,itemId){
  const action=queue.kind==='mix'
    ? `<button data-save-mix title="保存为播放列表" aria-label="保存为播放列表">${icon('bookmark-plus')}</button>`
    : queue.kind==='playlist'?`<button data-edit-playlist title="编辑播放列表" aria-label="编辑播放列表">${icon('list-filter')}</button>`:'';
  const countLabel=queue.kind==='parts'?`${queue.items.length} 卷`:`${queue.items.length} 个视频`;
  const kindLabel={mix:'Mix',parts:'分卷',playlist:'播放列表'}[queue.kind]||'视频合集';
  return `<aside class="mixqueue" data-queue-kind="${esc(queue.kind)}"><div class="mixqueuehead"><div><h2>${kindLabel}</h2><span>${esc(queue.title)} · ${countLabel}</span></div><div class="mixqueueactions">${action}
    <button data-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${queue.items.map((x,index)=>{
      const thumb=x.has_thumb?`<img src="/poster?id=${x.id}&c=4" alt="" loading="lazy">`:'';
      const edit=queue.kind==='playlist'?`<span class="queueedit"><button data-queue-up="${index}" aria-label="上移" ${index===0?'disabled':''}>↑</button><button data-queue-down="${index}" aria-label="下移" ${index===queue.items.length-1?'disabled':''}>↓</button><button data-queue-remove="${x.id}" aria-label="移出播放列表">${icon('x')}</button></span>`:'';
      return `<div class="mixrow"><button class="mixitem ${x.id===itemId?'current':''}" data-queue-item="${x.id}" aria-current="${x.id===itemId?'true':'false'}">
        <span class="mixitempic">${thumb}<i class="dur mono">${fmtDur(x.duration)}</i></span><span class="mixitemtext"><b data-middle-truncate>${esc(x.name)}</b><span data-truncate-end>${queue.kind==='parts'?`第 ${esc(x.part_label)} 卷`:esc(mixLabel(x))}</span></span></button>${edit}</div>`;
    }).join('')}</div></aside>`;
}
async function buildMix(seedId){
  const [seed,related]=await Promise.all([api('/api/item?id='+seedId),api('/api/related?id='+seedId+'&limit=28')]);
  const items=[seed,...(related.items||[]).filter(x=>x.id!==seed.id)];cache(items);
  return {kind:'mix',seedId,title:`Mix · ${mixLabel(seed)}`,items};
}
async function openMix(seedId,itemId=seedId,push=true,anchor=null){
  const previous=activeQueue?.kind==='mix'&&activeQueue.seedId===seedId?activeQueue:null;
  if(push&&!previous)detailReturnPath=location.pathname+location.search;
  const mix=previous||await buildMix(seedId);
  await openItem(itemId,false,mix,anchor);
  if(push)route(`/mix/${seedId}/${itemId}`);
}
async function openParts(seedId,itemId=seedId,push=true,anchor=null){
  const previous=activeQueue?.kind==='parts'&&activeQueue.seedId===seedId?activeQueue:null;
  if(push&&!previous)detailReturnPath=location.pathname+location.search;
  let queue=previous;
  if(!queue){
    const group=await api('/api/parts?id='+seedId);
    if(group.error){await openItem(itemId,true);return}
    queue={kind:'parts',seedId,title:`分卷 · ${group.title}`,items:group.items};cache(queue.items);
  }
  const chosen=queue.items.some(item=>item.id===itemId)?itemId:queue.items[0].id;
  await openItem(chosen,false,queue,anchor);
  if(push)route(`/parts/${seedId}/${chosen}`);
}
async function openPlaylist(playlistId,itemId=null,push=true){
  if(push)detailReturnPath=location.pathname+location.search;
  const playlist=await api('/api/playlist?id='+playlistId);
  if(!playlist.items.length){await openPlaylists(push);return}
  const chosen=playlist.items.some(item=>item.id===itemId)
    ? itemId:(playlist.current_asset_id||playlist.items[0].id);
  const queue={kind:'playlist',playlistId,title:playlist.name,items:playlist.items};
  cache(queue.items);await openItem(chosen,false,queue);
  if(push)route(`/playlists/${playlistId}/${chosen}`);
  api('/api/playlist',{method:'POST',body:JSON.stringify({action:'progress',id:playlistId,asset_id:chosen})}).catch(()=>{});
}
async function openItem(id,push=true,queueContext=null,anchor=null){
  releaseHoverPreviews();
  const origin=anchor?.isConnected?anchor:(detailOriginAnchor?.isConnected?detailOriginAnchor:null);
  const above=anchor?.isConnected
    ? anchor.getBoundingClientRect().top+anchor.getBoundingClientRect().height/2>window.innerHeight/2
    : detailOriginAbove;
  const returnSurfaceReady=$('#grid').children.length>0||!$('#index').hidden||!$('#stats').hidden;
  const needsReturnRestore=detailReturnNeedsRestore||(!push&&!returnSurfaceReady);
  const returnBars=barsContext.type==='item'?detailReturnBarsContext:cloneBarsContext(barsContext);
  if(push)detailReturnPath=location.pathname+location.search;
  disposeStage(false,true);
  detailOriginAnchor=origin;detailOriginAbove=above;detailReturnNeedsRestore=needsReturnRestore;
  detailReturnBarsContext=returnBars;
  activeQueue=queueContext;
  if(push&&!queueContext)route('/item/'+id);
  const detailSurface=surfaceToken(surfacePath());
  const it=await api('/api/item?id='+id); if(it.error)return;
  if(!surfaceCurrent(detailSurface))return;
  current=it; CACHE[it.id]=it;
  barsContext={type:'item',id:it.id,filters:returnBars?.type==='entity'
    ? {...returnBars.filters}:emptyEntityFilters()};
  const gated=it.cost==='metered';
  const offline=sourceOffline(it.location);
  const online=it.location==='online';
  const who=it.creator||it.code||it.studio||'未归属';
  const refs=it.entity_refs||{},studioRef=(refs.studio||[])[0];
  // 共演作品的女优逐行列出，每行带自己的头像；标签只写在第一行，其余留空保持对齐。
  const performerRefs=(refs.performer||[]).length
    ? refs.performer
    : (it.performers||[]).map(name=>({id:null,name}));
  // 身份按类别分组：标签作为组标题写在上方，同类横向排开。
  // 逐行一个名字在共演作品上会把整个侧栏撑满，标签列也重复得毫无信息量。
  const identitySeen=new Set();
  const fresh=name=>{const key=foldName(name);
    if(!name||identitySeen.has(key))return false;identitySeen.add(key);return true};
  const castList=performerRefs.filter(ref=>fresh(ref.name));
  const studioFallback=studioRef?[]:(it.studio?[{id:null,name:it.studio}]:[]);
  const studioList=[...(refs.studio||[]),...studioFallback].filter(ref=>fresh(ref.name));
  const creatorList=(refs.creator||[]).filter(ref=>fresh(ref.name));
  const seriesList=(refs.series||[]).filter(ref=>fresh(ref.name));

  // BEST 合集实测有 41 位出镜者，全铺开会把标签和反馈按钮挤出可视区。
  // 前 8 位直接展示，其余默认收起但仍在 DOM 里，一次点击即可看全。
  const CAST_SHOWN=8;
  const castOverflow=Math.max(0,castList.length-CAST_SHOWN);
  const idFace=(kind,item)=>kind==='performer'
    ? `<span>${esc(item.name.slice(0,1))}</span>${item.id?`<img src="/entity-image?kind=performer&id=${item.id}" alt="" loading="lazy" onerror="this.remove()">`:''}`
    : kind==='studio'
      ? `<span>${esc(item.name.slice(0,2))}</span><img src="/logo?studio=${encodeURIComponent(item.name)}" alt="" loading="lazy" onerror="this.remove()">`
      : `<span>${esc(item.name.slice(0,1))}</span>`;
  const idCell=(kind,item,index)=>{
    const hide=kind==='performer'&&index>=CAST_SHOWN;
    const content=`<span class="idface">${idFace(kind,item)}</span><span class="idname">${esc(item.name)}</span>`;
    if(!item.id)return `<span class="idcell${kind==='studio'?' logo':''}" title="${esc(item.name)}"${hide?' hidden data-castoverflow':''}>${content}</span>`;
    return `<button class="idcell entitylink${kind==='studio'?' logo':''}" data-entity-kind="${kind}"
      data-entity-name="${esc(item.name)}" title="${esc(item.name)}"${hide?' hidden data-castoverflow':''}>${content}</button>`;
  };
  const idGroup=(label,kind,list,extra='')=>list.length
    ? `<section class="idgroup"><h5 class="idlabel">${label}</h5>
        <div class="idrow">${list.map((item,i)=>idCell(kind,item,i)).join('')}${extra}</div></section>`
    : '';
  const seriesCell=item=>{const content=`${icon('tags')}<span>${esc(item.name)}</span>`;
    return item.id
      ? `<button class="serieslink entitylink" data-entity-kind="series" data-entity-name="${esc(item.name)}" title="${esc(item.name)}">${content}</button>`
      : `<span class="serieslink" title="${esc(item.name)}">${content}</span>`};
  const seriesGroup=list=>list.length
    ? `<section class="idgroup idseries"><h5 class="idlabel">系列</h5>
        <div class="seriesrows">${list.map(seriesCell).join('')}</div></section>`
    : '';
  const primaryIdentity=
    idGroup(performerLabel(it),'performer',castList,
      castOverflow?`<button class="castmore" id="castMore">还有 ${castOverflow} 位</button>`:'')
    +idGroup('厂牌','studio',studioList);
  const identityRows=
    (primaryIdentity?`<div class="identityprimary">${primaryIdentity}</div>`:'')
    +idGroup('创作者','creator',creatorList)
    +seriesGroup(seriesList);
  placeItemDetail(origin,above);
  $('#stage').hidden=false;document.body.classList.add('detail-open');delete $('#stage').dataset.c;
  $('#stage').innerHTML=`<div class="sgrid ${queueContext?'mixgrid':''}">
    <div class="vwrap"><canvas class="ambientcanvas" id="ambientCanvas" width="32" height="18"></canvas><button class="closestage" id="closeStage" title="关闭" aria-label="关闭">${icon('x')}</button>
       <button class="playerstatsbtn" id="playerStatsBtn" aria-label="播放统计" title="播放统计" aria-pressed="false" hidden>${icon('chart')}</button>
       <div class="playernet" id="playerNet" role="status" aria-live="polite" hidden></div>
       <div class="playerstats" id="playerStats" role="status" hidden></div>
      ${offline?`<div class="gate offline" id="offlineGate" role="status">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <b style="font-size:14px">脱盘模式</b>
          <span style="font-size:12px;color:var(--muted)">${esc(offlineReason(it.location))}</span>
          <button class="chip" id="offlineRetry" type="button">重新检测</button></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none"
          hidden style="display:none"></video>`
       :online?`<div class="gate" id="onlineGate" role="status">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <b style="font-size:14px">在线资产</b>
          <span style="font-size:12px;color:var(--muted)">这条内容从关注候选保存；媒体与原始页面在关注详情中查看。</span>
          <button class="chip" id="openSavedFollow" type="button">打开已保存关注</button></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none"
          hidden style="display:none"></video>`
       :gated?`<div class="gate" id="gate">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <span style="font-size:12px;color:var(--muted)">点此开始拉流 · ${fmtSize(it.size||0)}</span></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none" hidden></video>`
       :`<video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="metadata"></video>`}
    </div>${queueContext?queueHtml(queueContext,it.id):''}
    <div class="side"><div class="sidecontent">
      <div class="detailtitle">${srcBadge(it.location,it.cost,'srcbig')}
        <div class="stitle">${esc(it.name)}</div>
        ${it.location==='online'?'':`<div class="srctools detailtitletools">${sourceToolButtons(it.id)}</div>`}</div>
      ${it.location==='online'?'':`<span class="srcstate detailtitlestate" aria-live="polite"></span>`}
      <div class="smeta mono">
        <span class="detailmetaitem">${icon('monitor')}<span>${it.width||'?'}×${it.height||'?'}</span></span>
        <span class="detailmetaitem">${icon('hard-drive')}<span>${fmtSize(it.size||0)}</span></span>
        ${it.release_date?`<span class="detailmetaitem">${icon('calendar')}<span>${esc(it.release_date)}</span></span>`:''}</div>
      <div class="detailidentity">${identityRows||`<div class="identityrow"><span></span><span class="ilabel">归属</span><span>${esc(who)}</span></div>`}</div>
      <div class="stags" id="detailTags"></div>
      <div class="trace"><div class="lab mono"><span>离开位置</span><span id="ratioTxt">0%</span></div>
        <div class="bar"><u id="watched"></u><b id="mark" style="left:0"></b></div>
        <div class="lab mono trace-real"><span>真实观看</span><span id="realTxt">0%</span></div>
        <div class="bar"><u id="realBar" style="background:color-mix(in srgb,var(--keep) 40%,transparent)"></u></div>
      </div>
      <div class="fb">
        <button class="like" id="likeBtn" aria-label="${it.liked?'取消喜欢':'喜欢'}" title="喜欢 · 记录口味偏好" aria-pressed="${!!it.liked}">${icon('thumbs-up')}</button>
        <button class="reason" id="preferenceToggle" aria-label="喜爱理由" title="喜爱理由" aria-expanded="false" aria-controls="preferencePanel" data-has-reason="${!!it.like_reason}">${icon('heart')}</button>
        <button class="dislike" data-kind="dislike" aria-label="不合口味" title="不合口味 · 降低推荐权重" aria-pressed="${it.feedback==='dislike'}">${icon('thumbs-down')}</button>
        <button class="seen" data-kind="seen" aria-label="看过了" title="看过了 · 只降低近期推荐" aria-pressed="${it.feedback==='seen'}">${icon('eye')}</button>
        <button class="later" id="stageLater" aria-label="稍后看" title="稍后看 · 加入或移出队列" aria-pressed="${!!it.watch_later}">${it.watch_later?icon('check'):icon('bookmark-plus')}</button>
        <button class="playlistadd" id="addPlaylist" aria-label="加入播放列表" title="加入播放列表">${icon('list-filter')}</button>
        <button class="upgrade" id="betterVersion" aria-label="寻找更好版本" title="寻找高清、无水印或完整版" aria-pressed="${!!it.better_version}">${icon('sparkles')}</button>
        <button class="dispose" data-kind="dispose" aria-label="加入回收站" title="加入回收站 · 文件仍保留，可从回收站永久清除" aria-pressed="${it.disposal==='trash'}">${icon('trash')}</button></div>
      <div class="preference" id="preferencePanel" hidden>
        <textarea id="likeReason" maxlength="2000" placeholder="为什么喜欢？">${esc(it.like_reason||'')}</textarea>
        <div class="preference-foot"><span id="preferenceState" aria-live="polite"></span>
          <button type="button" class="geist-button primary savepreference" id="savePreference" title="提交喜爱理由" aria-label="提交喜爱理由"><span>提交</span></button></div>
      </div>
      <button class="obtn" data-kind="o">${icon('sperm')}<span>记一次高潮</span><b class="mono" id="oCount">${it.o_count||0}</b></button>
    </div></div></div>
    ${queueContext?'':`<div class="next"><h3>接着看</h3><div class="nrow" id="nrow">载入中…</div></div>`}`;
  $('#stage').classList.toggle('ambient-on',appSettings.ambientMode);
  $('#stage').classList.toggle('theater-mode',appSettings.theaterMode);

  const closeDetail=async()=>{const restore=cloneBarsContext(detailReturnBarsContext);
    const returnPath=detailReturnPath||'/',restoreSurface=detailReturnNeedsRestore;
    disposeStage(false);detailReturnBarsContext=null;
    barsContext=restore||{type:'home',filters:state};
    route(returnPath);
    if(restoreSurface)await restoreRoute();
    else{buildBars();if(location.pathname==='/playlists')openPlaylists(false)}};
  $('#closeStage').onclick=closeDetail;
  // 对账删掉的可能就是当前这条；删了就没什么可停留的，直接退回列表。
  wireSourceTools($('#stage'),r=>{
    if(r.items.some(x=>x.id===it.id))closeDetail();});
  if($('#castMore'))$('#castMore').onclick=e=>{
    $('#stage').querySelectorAll('[data-castoverflow]').forEach(row=>row.hidden=false);
    e.currentTarget.remove()};
  $('#stage').querySelectorAll('[data-queue-close]').forEach(b=>b.onclick=closeDetail);
  $('#stage').querySelectorAll('[data-queue-item]').forEach(b=>b.onclick=()=>queueContext.kind==='mix'
    ?openMix(queueContext.seedId,+b.dataset.queueItem,true)
    :queueContext.kind==='parts'?openParts(queueContext.seedId,+b.dataset.queueItem,true)
    :openPlaylist(queueContext.playlistId,+b.dataset.queueItem,true));
  $('#stage').querySelectorAll('[data-save-mix]').forEach(b=>b.onclick=()=>saveMixAsPlaylist(queueContext));
  $('#stage').querySelectorAll('[data-edit-playlist]').forEach(b=>b.onclick=()=>openPlaylists(true));
  $('#stage').querySelectorAll('[data-queue-up],[data-queue-down]').forEach(b=>b.onclick=()=>movePlaylistItem(queueContext,+b.dataset[b.hasAttribute('data-queue-up')?'queueUp':'queueDown'],b.hasAttribute('data-queue-up')?-1:1,it.id));
  $('#stage').querySelectorAll('[data-queue-remove]').forEach(b=>b.onclick=()=>removePlaylistItem(queueContext,+b.dataset.queueRemove,it.id));
  wireDrag($('#stage').querySelector('.mixlist'));
  const g=$('#gate');
  const onlineGate=$('#onlineGate');
  $('#addPlaylist').onclick=()=>openAddToPlaylist(it);
  $('#stage').querySelectorAll('[data-kind]').forEach(b=>b.onclick=async()=>{
    try{
      const r=await api('/api/feedback',{method:'POST',body:JSON.stringify({id:it.id,kind:b.dataset.kind})});
      Object.assign(it,{feedback:r.feedback,disposal:r.disposal,o_count:r.o_count});
      $('#stage').querySelector('.dislike').setAttribute('aria-pressed',r.feedback==='dislike');
      $('#stage').querySelector('.seen').setAttribute('aria-pressed',r.feedback==='seen');
      $('#stage').querySelector('.dispose').setAttribute('aria-pressed',r.disposal==='trash');
      $('#oCount').textContent=r.o_count||0;
      if(b.dataset.kind==='dispose'&&r.disposal==='trash'&&state.state==='ads'){
        disposeStage(true);await load(true);
      }
    }catch(error){alert(`操作失败：${error.message||'未知错误'}`)}
  });
  const renderDetailTags=()=>{
    const wrap=$('#detailTags');if(!wrap)return;
    const visible=(it.tags||[]).filter(t=>!DURATION_TAGS.has(t.k)).slice(0,40);
    wrap.innerHTML=visible.map(t=>`<span class="detailtag"><button class="tagfilter" data-tag="${esc(t.k)}">${esc(tagLabel(t.k))}</button><button class="tagremove" data-remove-tag="${esc(t.k)}" title="从此视频隐藏该标签" aria-label="删除标签 ${esc(tagLabel(t.k))}">${icon('x')}</button></span>`).join('')+
      `<button class="tagplus" id="tagPlus" title="添加标签" aria-label="添加标签" aria-expanded="false">${icon('plus')}</button>
       <div class="tagpicker" id="tagPicker" role="dialog" aria-label="添加标签" hidden>
         <label class="tagpicksearch">${icon('search')}<input id="tagPickSearch" maxlength="80" placeholder="搜索或输入新标签" autocomplete="off"></label>
         <div class="tagpickbody" id="tagPickBody"></div>
       </div>`;
    wrap.querySelectorAll('[data-tag]').forEach(s=>s.onclick=()=>{
      commitContextFilter(filters=>{filters.tag=s.dataset.tag});
      window.scrollTo({top:0,behavior:'smooth'})});
    wrap.querySelectorAll('[data-remove-tag]').forEach(b=>b.onclick=async()=>{
      b.disabled=true;const tag=b.dataset.removeTag;
      const r=await api('/api/item-tag',{method:'POST',body:JSON.stringify({id:it.id,operation:'remove',tag})});
      if(r.ok){it.tags=(it.tags||[]).filter(x=>foldName(x.k)!==foldName(tag));renderDetailTags()}else b.disabled=false});
    const addTag=async tag=>{tag=tag.trim();if(!tag)return;
      const r=await api('/api/item-tag',{method:'POST',body:JSON.stringify({id:it.id,operation:'add',tag})});
      if(r.ok){
        if(!it.tags.some(x=>foldName(x.k)===foldName(tag)))it.tags.push({k:tag,cat:'general'});
        try{const old=JSON.parse(localStorage.getItem('peach.recentTags')||'[]').filter(x=>foldName(x)!==foldName(tag));
          localStorage.setItem('peach.recentTags',JSON.stringify([tag,...old].slice(0,12)))}catch(_e){}
        renderDetailTags()
      }
    };
    const plus=$('#tagPlus'),picker=$('#tagPicker'),search=$('#tagPickSearch'),body=$('#tagPickBody');
    let outsideHandler=null,activeIndex=-1;
    const closePicker=()=>{picker.hidden=true;plus.setAttribute('aria-expanded','false');
      if(outsideHandler)document.removeEventListener('pointerdown',outsideHandler,true);outsideHandler=null};
    const candidates=()=>{const source=(facets&&facets.tags)||[],byName=new Map(source.map(x=>[foldName(x.k),x]));
      let recent=[];try{recent=JSON.parse(localStorage.getItem('peach.recentTags')||'[]')}catch(_e){}
      return {all:source,recent:recent.map(name=>byName.get(foldName(name))||{k:name,n:0})}};
    const pickButton=x=>{const selected=(it.tags||[]).some(t=>foldName(t.k)===foldName(x.k));
      return `<button class="tagpickitem${selected?' selected':''}" data-pick="${esc(x.k)}" aria-pressed="${selected}">
        ${selected?icon('check'):icon('tags')}<span class="pickname">${esc(tagLabel(x.k))}</span><span class="pickcount">${(x.n||0).toLocaleString()}</span></button>`};
    const renderPicker=()=>{const q=foldName(search.value),data=candidates();
      const filtered=data.all.filter(x=>!q||foldName(x.k).includes(q)).slice(0,120);
      const recent=q?[]:data.recent.filter((x,i,a)=>a.findIndex(y=>foldName(y.k)===foldName(x.k))===i).slice(0,12);
      const exact=filtered.some(x=>foldName(x.k)===q);
      body.innerHTML=(recent.length?`<section class="tagpicksection"><h4>最近使用</h4><div class="tagpickgrid">${recent.map(pickButton).join('')}</div></section>`:'')+
        `<section class="tagpicksection"><h4>${q?'搜索结果':'全部标签'}</h4><div class="tagpickgrid">${filtered.map(pickButton).join('')}
        ${q&&!exact?`<button class="tagpickitem" data-pick="${esc(search.value.trim())}">${icon('plus')}<span class="pickname">新建“${esc(search.value.trim())}”</span></button>`:''}</div></section>`;
      activeIndex=-1;body.querySelectorAll('[data-pick]').forEach(b=>b.onclick=()=>{
        const selected=b.getAttribute('aria-pressed')==='true',tag=b.dataset.pick;closePicker();if(!selected)addTag(tag)})};
    search.oninput=renderPicker;
    search.onkeydown=e=>{const options=[...body.querySelectorAll('[data-pick]')];
      if(e.key==='Escape'){e.preventDefault();closePicker();plus.focus();return}
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!options.length)return;
        activeIndex=(activeIndex+(e.key==='ArrowDown'?1:-1)+options.length)%options.length;
        options.forEach((b,i)=>b.classList.toggle('active',i===activeIndex));options[activeIndex].scrollIntoView({block:'nearest'});return}
      if(e.key==='Enter'){e.preventDefault();if(activeIndex>=0&&options[activeIndex])options[activeIndex].click();
        else if(search.value.trim()){closePicker();addTag(search.value.trim())}}};
    plus.onclick=()=>{picker.hidden=false;plus.setAttribute('aria-expanded','true');renderPicker();search.focus();
      outsideHandler=e=>{if(!picker.contains(e.target)&&e.target!==plus)closePicker()};
      setTimeout(()=>document.addEventListener('pointerdown',outsideHandler,true),0)};
  };
  renderDetailTags();
  $('#stage').querySelectorAll('[data-entity-kind]').forEach(b=>b.onclick=()=>
    openEntity(b.dataset.entityKind,b.dataset.entityName));
  $('#stageLater').onclick=async()=>{const r=await api('/api/watch-later',{method:'POST',
    body:JSON.stringify({id:it.id})});it.watch_later=r.watch_later;
    $('#stageLater').setAttribute('aria-pressed',r.watch_later);
    $('#stageLater').innerHTML=r.watch_later?icon('check'):icon('bookmark-plus')};
  $('#betterVersion').onclick=async()=>{const b=$('#betterVersion'),wanted=b.getAttribute('aria-pressed')!=='true';
    const r=await api('/api/quality-goal',{method:'POST',body:JSON.stringify({id:it.id,wanted})});
    it.better_version=r.better_version;it.better_version_reason=r.better_version_reason;
    b.setAttribute('aria-pressed',String(r.better_version));b.title=r.better_version?(r.better_version_reason||'已标记寻找更好版本'):'寻找高清、无水印或完整版'};
  const preferenceToggle=$('#preferenceToggle'),preferencePanel=$('#preferencePanel');
  preferenceToggle.onclick=()=>{const open=preferencePanel.hidden;preferencePanel.hidden=!open;
    preferenceToggle.setAttribute('aria-expanded',String(open));if(open)$('#likeReason').focus()};
  const savePreference=async()=>{
    const btn=$('#savePreference'),like=$('#likeBtn'),stateText=$('#preferenceState');
    btn.disabled=true;btn.setAttribute('aria-busy','true');
    btn.innerHTML=`${spinnerHtml('正在提交喜爱理由')}<span>提交中…</span>`;stateText.textContent='保存中…';
    const reason=$('#likeReason').value;
    const liked=like.getAttribute('aria-pressed')==='true'||reason.trim().length>0;
    try{const r=await api('/api/preference',{method:'POST',body:JSON.stringify({id:it.id,liked,reason})});
      it.liked=r.liked;it.like_reason=r.like_reason;
      like.setAttribute('aria-pressed',r.liked);like.setAttribute('aria-label',r.liked?'取消喜欢':'喜欢');
      preferenceToggle.dataset.hasReason=String(!!r.like_reason);
      stateText.textContent='已保存';setTimeout(()=>{if(stateText.textContent==='已保存')stateText.textContent=''},1400);
    }catch(e){stateText.textContent='保存失败 · 请重试'}finally{
      btn.disabled=false;btn.removeAttribute('aria-busy');btn.innerHTML='<span>提交</span>'}
  };
  $('#likeBtn').onclick=async()=>{const b=$('#likeBtn');
    b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')!=='true');await savePreference()};
  $('#savePreference').onclick=savePreference;
  const vv=$('#vid');
  vv.addEventListener('play',()=>{if(!$('#stage').dataset.c){$('#stage').dataset.c='1';
    api('/api/play',{method:'POST',body:JSON.stringify({id:it.id})})}});
  if(it.play_seconds&&it.duration){
    const rp=Math.min(it.play_seconds/it.duration,1)*100;
    $('#realTxt').textContent=rp.toFixed(0)+'%';
    $('#realBar').style.width=rp.toFixed(1)+'%';
  }
  wireTelemetry(it,vv,{watched:'#watched',mark:'#mark',ratio:'#ratioTxt'});
  let stopAmbient=()=>{};
  const offlineGate=$('#offlineGate');
  if(offlineGate){
    const retry=$('#offlineRetry');
    if(retry)retry.onclick=async()=>{
      retry.disabled=true;
      const status=await loadSourceStatus();
      retry.disabled=false;
      if(status[it.location]===false){retry.textContent='仍未挂载 · 再试';return}
      openItem(it.id,false);            // 盘回来了就按正常路径重开，不在这里半路挂播放器
    };
  }
  else if(onlineGate){
    $('#openSavedFollow').onclick=()=>{followFilter='saved';openFollow()};
  }
  else if(g)g.onclick=()=>{vv.hidden=false;g.remove();const mounted=mountDetailPlayer(it,vv,true);stopAmbient=mountPlayerAmbient(vv);mounted?.one?.('dispose',stopAmbient)};
  else{const mounted=mountDetailPlayer(it,vv,true);stopAmbient=mountPlayerAmbient(vv);mounted?.one?.('dispose',stopAmbient)}
  vv.addEventListener('emptied',()=>stopAmbient(),{once:true});
  buildBars();
  scrollItemDetailIntoView();

  if(!queueContext)api('/api/related?id='+it.id+'&limit='+appSettings.relatedLimit).then(d=>{
    const n=$('#nrow'); if(!n)return; cache(d.items);
    n.innerHTML=d.items.length?d.items.map(x=>cardHtml(x,'ncard')).join(''):'<span class="empty">暂无</span>';
    wireCards(n);});
}

function wireTelemetry(it,v,sel){
  if(!v)return; let last=0,acc=0,timer=null,seeks=0;
  v.addEventListener('seeking',()=>{seeks++});
  const paint=()=>{const d=it.duration||v.duration||0;if(!d)return;
    const r=Math.min(v.currentTime/d,1);
    const w=sel.watched&&$(sel.watched),m=sel.mark&&$(sel.mark),t=sel.ratio&&$(sel.ratio);
    if(w)w.style.width=(r*100).toFixed(1)+'%'; if(m)m.style.left=(r*100).toFixed(1)+'%';
    if(t)t.textContent=(r*100).toFixed(0)+'%'};
  const flush=e=>{const d=it.duration||v.duration||0;if(!acc&&!e&&!seeks)return;
    api('/api/activity',{method:'POST',body:JSON.stringify(
      {id:it.id,position:v.currentTime,duration:d,delta:acc,ended:!!e,seeks})})
      .then(r=>{ // 回填面板的真实观看率
        const rr=$('#realTxt'); if(rr&&r&&r.real_ratio!=null){
          const rp=Math.min(r.real_ratio,1)*100;
          rr.textContent=rp.toFixed(0)+'%';
          const b=$('#realBar'); if(b)b.style.width=rp.toFixed(1)+'%';
        }});
    acc=0;seeks=0};
  v.onplay=()=>{last=v.currentTime;timer=setInterval(()=>flush(false),10000)};
  v.ontimeupdate=()=>{const dt=v.currentTime-last;if(dt>0&&dt<2)acc+=dt;last=v.currentTime;paint()};
  v.onpause=()=>{clearInterval(timer);flush(false)};
  v.onended=()=>{clearInterval(timer);flush(true);if(!$('#tok').hidden)tokNext(1)};
  paint();
}

function wireFollowTelemetry(item,video){
  let last=0,acc=0,timer=null,started=false;
  const flush=ended=>{const duration=Number(item.duration)||video.duration||0;
    if(!acc&&!ended)return;
    api('/api/follow/activity',{method:'POST',body:JSON.stringify({
      item:item.id,position:video.currentTime,duration,delta:acc,ended:!!ended
    })}).catch(()=>{});
    acc=0;
  };
  video.addEventListener('play',()=>{
    if(!started){started=true;api('/api/follow/play',{method:'POST',body:JSON.stringify({item:item.id})})
      .then(result=>{item.status=result.status||item.status}).catch(()=>{})}
    last=video.currentTime;
    if(timer)clearInterval(timer);timer=setInterval(()=>flush(false),10000);
  });
  video.addEventListener('timeupdate',()=>{
    const delta=video.currentTime-last;if(delta>0&&delta<2)acc+=delta;last=video.currentTime;
  });
  video.addEventListener('pause',()=>{if(timer)clearInterval(timer);timer=null;flush(false)});
  video.addEventListener('ended',()=>{if(timer)clearInterval(timer);timer=null;flush(true)});
  video.addEventListener('emptied',()=>{if(timer)clearInterval(timer);timer=null;flush(false)},{once:true});
}

/* ── 短片全屏 ── */
let tokList=[],tokIdx=0,tokSwitching=false,tokNetTimer=null,tokLoadHideTimer=null,tokLoadingLabel='加载中…';
function tokStreamUrl(video,id){
  const session=newStreamSession();video.dataset.streamSession=session;
  return `/stream?id=${id}&session=${encodeURIComponent(session)}`;
}
function cancelTokStream(video){
  const session=video?.dataset.streamSession||'';if(!session)return;
  delete video.dataset.streamSession;cancelStreamSession(session);
}
function disposeTokVideo(video,remove=false){
  if(!video)return;
  video.pause();cancelTokStream(video);video.removeAttribute('src');video.load();
  if(remove)video.remove();
}
/* 沉浸模式 = 滚动刷新的连续流，横屏竖屏都进（不是「短片模式」）。
   队列滚到尾自动续取下一页，形成无限流。 */
let tokOffset=0, tokLoading=false;
async function fetchTok(off){
  const p=new URLSearchParams(Object.entries(state).filter(([,v])=>v));
  p.delete('orient');                        // 不限画幅
  p.set('sort','rand');                      // ⚠️ 随机，不是顺序播前 60 个
  p.set('limit',60); p.set('offset',0); p.set('thumb','');
  const d=await api('/api/items?'+p);
  const list=d.items.filter(x=>x.cost!=='metered' && x.duration);
  for(let i=list.length-1;i>0;i--){const j=Math.random()*(i+1)|0;[list[i],list[j]]=[list[j],list[i]]}
  return list;
}
function updateTokLoading(it){
  const text=$('#tokLoadingText');if(!text)return;
  const speed=it?streamSpeedBits(it.id):0;
  text.textContent=speed?`${tokLoadingLabel} · ${fmtSpeed(speed)}`:tokLoadingLabel;
}
function setTokLoading(on,label='加载中…',it=null){
  const loader=$('#tokLoader');if(!loader)return;
  if(tokLoadHideTimer){clearTimeout(tokLoadHideTimer);tokLoadHideTimer=null}
  if(!on){loader.hidden=true;if(tokNetTimer){clearInterval(tokNetTimer);tokNetTimer=null}return}
  tokLoadingLabel=label;loader.hidden=false;updateTokLoading(it);
  if(tokNetTimer)clearInterval(tokNetTimer);
  tokNetTimer=setInterval(()=>updateTokLoading(tokList[tokIdx]),500);
}
function waitTokReady(video,timeout=15000){
  if(video.readyState>=3)return Promise.resolve();
  return new Promise(resolve=>{
    let finished=false;
    const done=()=>{if(finished)return;finished=true;
      ['loadeddata','canplay','error'].forEach(event=>video.removeEventListener(event,done));resolve()};
    ['loadeddata','canplay','error'].forEach(event=>video.addEventListener(event,done,{once:true}));
    setTimeout(done,timeout);
  });
}
/* 沉浸模式默认 cover 铺满，但那只在片源和视口比例接近时才成立。
   旧判据是「片源是不是竖屏」：于是 16:9 的横屏进竖屏视口照样 cover，按高度放大到
   两边各裁掉一大半——就是「竖屏沉浸模式看横屏视频看不全」。
   判据改成两者比例差多少。容差取得很紧（1.05）是刻意的：原代码对竖屏片源用
   contain，是「不裁掉正在看的画面」的有意选择，只有横屏那一格判错了。放宽到
   1.25 会顺手把 9:16 片源在 9:19.5 手机上改成 cover、裁掉约 18% 高度——那是
   没人要求的回退。现在只有比例几乎一致时才 cover（省掉取整产生的 1px 黑边），
   其余一律完整显示。
   视口比例会随旋转和窗口尺寸改变，所以必须跟着重算，不能只在 loadedmetadata 算一次。 */
const TOK_FIT_TOLERANCE=1.05;
function tokFitOne(v){
  if(!v||!v.videoWidth||!v.videoHeight)return;
  const track=v.parentElement;
  const box=(track&&track.clientWidth&&track.clientHeight)
    ? track.clientWidth/track.clientHeight
    : window.innerWidth/window.innerHeight;
  if(!box||!isFinite(box))return;
  const source=v.videoWidth/v.videoHeight;
  const wide=source>=1;
  track.closest('.tokstage')?.classList.toggle('wide',wide);
  $('#tok').classList.toggle('tok-wide',wide);
  const mismatch=source>box?source/box:box/source;
  v.classList.toggle('contain',mismatch>TOK_FIT_TOLERANCE);
}
function applyTokFit(v){
  v.classList.remove('contain');
  const fit=()=>tokFitOne(v);
  if(v.readyState>=1)fit();
  else v.addEventListener('loadedmetadata',fit,{once:true});
}
// 旋转手机或改窗口大小后，原来该铺满的可能要改成完整显示，反之亦然。
addEventListener('resize',()=>{
  if($('#tok').hidden)return;
  $('#tokTrack').querySelectorAll('video').forEach(tokFitOne);
});
async function openTok(startId,push=true){
  if(push)route('/immerse');
  $('#tok').hidden=false;document.body.style.overflow='hidden';setTokLoading(true,'加载内容…');
  try{
    tokOffset=0;
    tokList=await fetchTok(0);
    if(startId&&!tokList.some(x=>x.id===startId)){
      const selectedItem=await api('/api/item?id='+startId);
      if(selectedItem.id)tokList=[selectedItem,...tokList.filter(x=>x.id!==startId)];
    }
    if(!tokList.length){alert('当前筛选下没有可直接播放的内容（计费源不进沉浸模式）');$('#tokClose').click();return}
    tokIdx=Math.max(0,tokList.findIndex(x=>x.id===startId));
    await tokShow();
  }catch(_e){setTokLoading(false);$('#tokClose').click()}
}
async function tokShow(dir){
  const it=tokList[tokIdx];if(!it||tokSwitching)return;
  tokSwitching=true;setTokLoading(true,dir?'切换中…':'加载中…',it);
  try{
    const full=await api('/api/item?id='+it.id);
    const track=$('#tokTrack'),old=$('#tokVid');
    let v=old;
    if(dir&&old&&old.getAttribute('src')){
      v=document.createElement('video');v.id='tokIncoming';v.playsInline=true;v.preload='auto';
      v.src=tokStreamUrl(v,it.id);applyTokFit(v);v.style.transform=`translate(-50%,${dir>0?100:-100}%)`;track.appendChild(v);
      await waitTokReady(v);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        old.style.transform=`translate(-50%,${dir>0?-100:100}%)`;v.style.transform='translate(-50%,0)'}));
      await new Promise(resolve=>setTimeout(resolve,210));
      disposeTokVideo(old,true);v.id='tokVid';v.style.transform='translateX(-50%)';
    }else{
      disposeTokVideo(v);v.preload='auto';v.src=tokStreamUrl(v,it.id);applyTokFit(v);await waitTokReady(v);
    }
    if(location.pathname==='/'){
      const url=new URL(location.href),query=new URLSearchParams();
      for(const key of ['q','loc','creator','studio','tag','len','dur_min','dur_max','orient','state','sort']){
        const value=state[key];if(value&&!(key==='loc'&&value==='local,115')&&!(key==='sort'&&value==='daily'))query.set(key,value)
      }
      url.search=query.toString();history.replaceState({},'',url.pathname+(url.search||''));
    }
    v.play().catch(()=>{});
    $('#tokTitle').textContent=it.name;
    // 标题进详情页。沉浸模式里只看得到文件名，想看标签、相关推荐或改东西
    // 都得先退出再去列表里把它找回来。路径和旁边的创作者链接一致：先关，再开。
    $('#tokTitle').onclick=()=>{const id=it.id;$('#tokClose').click();openItem(id)};
    // 共演作品在沉浸模式也要念全出镜者；点击仍进第一位的资料页。
    const cast=full.performers||[];
    const who=cast.length
      ? cast.slice(0,3).join('、')+(cast.length>3?` 等 ${cast.length} 人`:'')
      : (full.creator||it.code||'未归属');
    const ownerKind=cast.length?'performer':(full.creator?'creator':'');
    const ownerName=cast.length?cast[0]:(full.creator||it.code||'未归属');
    const ownerRef=ownerKind?(full.entity_refs?.[ownerKind]?.[0]||null):null;
    $('#tokAvatar').innerHTML=avatarInner(ownerName,ownerRef,REP[ownerName],ownerKind||'performer');
    $('#tokWho').textContent=who;
    const openTokOwner=e=>{e.preventDefault();
      $('#tokClose').click();
      if(full.performers&&full.performers[0])openEntity('performer',full.performers[0]);
      else if(full.creator)openEntity('creator',full.creator);
      else if(it.code){state.q=it.code;buildEdge();buildBars();load(true)}};
    $('#tokWho').onclick=openTokOwner;
    $('#tokAvatar').onclick=openTokOwner;
    $('#tokMeta').textContent=`· ${fmtDur(it.duration)} · ${it.ctx_orient||''} · ${tokIdx+1}/${tokList.length}`;
    // 进度条
    const bar=$('#tokBar'), prog=$('#tokProg');
    v.ontimeupdate=null;
    const upd=()=>{const d=v.duration||it.duration||0;
      if(d)prog.style.width=(v.currentTime/d*100).toFixed(2)+'%'};
    v.addEventListener('timeupdate',upd);
    // 拖动而不只是点。pointer 一套同时盖鼠标和触控，捕获指针后手滑出进度条
    // 也不会断。拖动中只画进度，松手才 seek——每帧都 seek 会让远程源一直重新缓冲。
    tokWireScrub(bar,prog,v,()=>v.duration||it.duration||0);
    $('#tokDislike').setAttribute('aria-pressed',full.feedback==='dislike');
    $('#tokSeen').setAttribute('aria-pressed',full.feedback==='seen');
    $('#tokSeenLabel').textContent=full.feedback==='seen'?'已看':'看过';
    $('#tokOn').textContent=full.o_count||0;
    api('/api/play',{method:'POST',body:JSON.stringify({id:it.id})});
    wireTelemetry(it,v,{});
    setTokLoading(false);
  }catch(_e){
    $('#tokTrack').querySelectorAll('#tokIncoming').forEach(video=>disposeTokVideo(video,true));
    setTokLoading(false)
  }finally{tokSwitching=false}
}
/* 进度条拖动。抽成函数是因为每次切片都要重新绑一次，而监听器必须能被覆盖。 */
function tokWireScrub(bar,prog,video,duration){
  const ratio=event=>{const r=bar.getBoundingClientRect();
    return Math.min(1,Math.max(0,(event.clientX-r.left)/r.width))};
  let scrubbing=false;
  bar.onpointerdown=e=>{
    const d=duration(); if(!d)return;
    scrubbing=true;bar.classList.add('scrubbing');bar.setPointerCapture(e.pointerId);
    prog.style.width=(ratio(e)*100).toFixed(2)+'%';
    e.preventDefault();
  };
  bar.onpointermove=e=>{if(scrubbing)prog.style.width=(ratio(e)*100).toFixed(2)+'%'};
  const finish=e=>{
    if(!scrubbing)return;
    scrubbing=false;bar.classList.remove('scrubbing');
    const d=duration(); if(d)video.currentTime=d*ratio(e);
  };
  bar.onpointerup=finish;
  bar.onpointercancel=e=>{scrubbing=false;bar.classList.remove('scrubbing')};
  // 没拖动的单击走同一条路：pointerdown 已经画了进度，pointerup 落地。
  bar.onclick=null;
}
async function tokNext(d){
  if(tokSwitching)return;
  tokIdx=tokIdx+d;
  setTokLoading(true,'切换中…',tokList[tokIdx]);
  // 滚到尾部就续取下一页 —— 无限流
  if(tokIdx>=tokList.length-3 && !tokLoading){
    tokLoading=true; tokOffset+=60;
    const more=await fetchTok(tokOffset);   // 每次都是新的随机抽样
    if(more.length){const seen=new Set(tokList.map(x=>x.id));
      tokList=tokList.concat(more.filter(x=>!seen.has(x.id)))}
    tokLoading=false;
  }
  if(tokIdx>=tokList.length)tokIdx=0;
  if(tokIdx<0)tokIdx=tokList.length-1;
  await tokShow(d);
}
$('#tokBtn').onclick=()=>openTok();
$('#immerseBtn').onclick=()=>openTok();

$('#searchBtn').onclick=()=>{const s=$('.search');s.classList.toggle('open');
  if(s.classList.contains('open'))$('#q').focus()};
/* 窄屏退出搜索。失焦那条 140ms 的兜底只在输入框为空时才收起搜索栏，
   输入过内容就没有出口了；返回按钮无条件收起，并清掉下拉栏。 */
$('#searchBack').onclick=()=>{
  $('.search').classList.remove('open');
  $('#searchMenu').hidden=true;
  $('#q').blur();
};
$('#q').addEventListener('blur',()=>setTimeout(()=>{if(!$('#q').value&&!$('#searchMenu').matches(':hover'))$('.search').classList.remove('open');$('#searchMenu').hidden=true},140));
$('#brandHome').onclick=e=>{e.preventDefault();openHome(true)};
$('#tokClose').onclick=()=>{setTokLoading(false);clearTokTap();$('#tok').hidden=true;$('#tokTrack').querySelectorAll('video').forEach(v=>{
  disposeTokVideo(v,v.id!=='tokVid')});
  const v=$('#tokVid');if(v){v.style.transform='translateX(-50%)'}$('#tok').classList.remove('tok-wide');
  $('#tok .tokstage').classList.remove('wide');tokSwitching=false;document.body.style.overflow='';openHome()};
addEventListener('pagehide',()=>{
  cancelDetailStream();
  $('#tokTrack').querySelectorAll('video').forEach(cancelTokStream);
});
let wl=0;
$('#tok').addEventListener('wheel',e=>{const n=Date.now();if(n-wl<260)return;wl=n;tokNext(e.deltaY>0?1:-1)},{passive:true});
/* 手机上竖划切片、横划拖进度。横划在哪儿起手都行——屏幕最下沿那条
   进度条在手机上几乎摸不到。方向一旦定下就不再改，否则斜着划会又切片又跳进度。
   位移按屏宽换算成时长的相对量，所以从任何位置起手都是「往右 = 往后」。 */
const TOK_DOUBLE_TAP_MS=280;
let tokTouch=null,tokTapTimer=null,tokLastTap=null,tokIgnoreClickUntil=0;
function clearTokTap(){
  if(tokTapTimer)clearTimeout(tokTapTimer);
  tokTapTimer=null;tokLastTap=null;
}
function toggleVideoPlayback(video){
  if(!video)return;
  if(video.paused)video.play().catch(()=>{});else video.pause();
}
function handleTokTap(clientX){
  const video=$('#tokVid');if(!video)return;
  const side=clientX<window.innerWidth/2?-1:1;
  const now=Date.now();
  if(tokLastTap&&tokLastTap.side===side&&now-tokLastTap.at<=TOK_DOUBLE_TAP_MS){
    clearTokTap();
    seekVideoBy(video,appSettings.seekSeconds*side);
    return;
  }
  // 两次点在不同半区时，第一下仍是一次完整的单击；立即兑现后再等当前点击。
  if(tokTapTimer){clearTimeout(tokTapTimer);tokTapTimer=null;toggleVideoPlayback(video)}
  tokLastTap={side,at:now};
  tokTapTimer=setTimeout(()=>{
    tokTapTimer=null;tokLastTap=null;
    if(!$('#tok').hidden)toggleVideoPlayback($('#tokVid'));
  },TOK_DOUBLE_TAP_MS);
}
$('#tokTrack').onclick=()=>{
  // 触屏的合成 click 会紧跟 touchend；那一下已经由单击/双击判定接管，不能再切一次。
  if(Date.now()<tokIgnoreClickUntil)return;
  toggleVideoPlayback($('#tokVid'));
};
$('#tok').addEventListener('touchstart',e=>{
  if(e.touches.length!==1||!e.target.closest('.toktrack')){tokTouch=null;return}
  const v=$('#tokVid');
  tokTouch={x:e.touches[0].clientX,y:e.touches[0].clientY,axis:'',
    from:v?v.currentTime||0:0};
},{passive:true});
$('#tok').addEventListener('touchmove',e=>{
  if(!tokTouch||e.touches.length!==1)return;
  const dx=e.touches[0].clientX-tokTouch.x,dy=e.touches[0].clientY-tokTouch.y;
  if(!tokTouch.axis){
    if(Math.abs(dx)<12&&Math.abs(dy)<12)return;
    tokTouch.axis=Math.abs(dx)>Math.abs(dy)?'x':'y';
    if(tokTouch.axis==='x')$('#tokBar').classList.add('scrubbing');
  }
  if(tokTouch.axis!=='x')return;
  const v=$('#tokVid'),d=v&&(v.duration||0);
  if(!d)return;
  e.preventDefault();                       // 横划归进度，不交给页面滚动
  tokTouch.to=Math.min(d,Math.max(0,tokTouch.from+dx/window.innerWidth*d));
  $('#tokProg').style.width=(tokTouch.to/d*100).toFixed(2)+'%';
},{passive:false});
$('#tok').addEventListener('touchend',e=>{
  if(!tokTouch)return;
  const touch=tokTouch;tokTouch=null;
  tokIgnoreClickUntil=Date.now()+700;
  $('#tokBar').classList.remove('scrubbing');
  if(touch.axis==='x'){
    const v=$('#tokVid');
    if(v&&touch.to!=null)v.currentTime=touch.to;
    return;
  }
  const end=e.changedTouches[0],dx=end.clientX-touch.x,dy=touch.y-end.clientY;
  if(Math.abs(dy)>60){clearTokTap();tokNext(dy>0?1:-1);return}
  if(Math.abs(dx)<=14&&Math.abs(dy)<=14){
    e.preventDefault();
    handleTokTap(end.clientX);
  }
},{passive:false});
$('#tok').addEventListener('touchcancel',()=>{
  tokTouch=null;$('#tokBar').classList.remove('scrubbing');
},{passive:true});
[['#tokDislike','dislike'],['#tokSeen','seen'],['#tokO','o']].forEach(([s,kind])=>{
  $(s).onclick=async()=>{const it=tokList[tokIdx];
    const r=await api('/api/feedback',{method:'POST',body:JSON.stringify({id:it.id,kind})});
    $('#tokDislike').setAttribute('aria-pressed',r.feedback==='dislike');
    $('#tokSeen').setAttribute('aria-pressed',r.feedback==='seen');
    $('#tokSeenLabel').textContent=r.feedback==='seen'?'已看':'看过';
    $('#tokOn').textContent=r.o_count||0;
    if(kind==='dislike'&&r.feedback==='dislike')setTimeout(()=>tokNext(1),260)}});

/* 当前该响应播放快捷键的 video：沉浸模式优先，其次详情播放器，都没开就返回 null。
   直接操作原生元素而不是 Video.js 实例——沉浸模式没有 Video.js，而详情播放器读的
   就是这个元素，两边共用一条实现。 */
function activeVideo(){
  if(!$('#tok').hidden)return $('#tokVid');
  const stage=$('#stage');
  // 不能按 #vid 取：Video.js 挂载后会把 <video id="vid"> 换成同 id 的
  // <div class="video-js">，真正的媒体元素变成 #vid_html5_api。给那个 div 写
  // currentTime 只是挂了个同名属性——读得回来、播放却毫无变化，失败得毫无声息。
  return stage&&!stage.hidden?stage.querySelector('video'):null;
}
function isTypingTarget(el){
  return !!el&&(el.tagName==='INPUT'||el.tagName==='TEXTAREA'||el.isContentEditable);
}
function seekVideoBy(video,seconds){
  const total=video.duration;
  const target=(video.currentTime||0)+seconds;
  // duration 在元数据到位前是 NaN，此时只夹下界，不要拿 NaN 去比上界。
  video.currentTime=Number.isFinite(total)?Math.max(0,Math.min(total,target)):Math.max(0,target);
}
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){
    if(!$('#settingsPanel').hidden){openSettings(false);return}
    if(!$('#searchMenu').hidden){$('#searchMenu').hidden=true;return}
    if(!$('#tok').hidden){$('#tokClose').click();return}
    if($('#drawer').classList.contains('open')){openDrawer(false);return}
    if(selectMode||selected.size||followSelected.size){setSelectMode(false,true);return}
    const st=$('#stage');if(st&&!st.hidden){const c=$('#closeStage');if(c)c.click()}
    return;
  }
  // 输入态不抢键：搜索框、标签弹窗和任何可编辑区域里的按键归它们自己处理。
  if(isTypingTarget(e.target)||e.ctrlKey||e.metaKey||e.altKey)return;
  const imageDots=[...document.querySelectorAll('#stage:not([hidden]) .followimagedots [data-follow-image-item]')];
  if(imageDots.length&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){
    e.preventDefault();
    const current=Math.max(0,imageDots.findIndex(dot=>dot.getAttribute('aria-current')==='true'));
    imageDots[(current+(e.key==='ArrowRight'?1:-1)+imageDots.length)%imageDots.length].click();
    return;
  }
  const video=activeVideo();
  if(video){
    if(e.key==='t'||e.key==='T'){
      e.preventDefault();applyTheaterMode(!appSettings.theaterMode);return;
    }
    if(e.key==='ArrowLeft'||e.key==='ArrowRight'){
      e.preventDefault();
      seekVideoBy(video,appSettings.seekSeconds*(e.key==='ArrowRight'?1:-1));
      return;
    }
    if(e.key===' '){
      e.preventDefault();          // 不加这句空格会把页面滚下去
      toggleVideoPlayback(video);
      return;
    }
  }
  // 沉浸模式：纵向切片、横向快进退，和竖屏短视频的手势方向保持一致。
  if(!$('#tok').hidden){if(e.key==='ArrowDown')tokNext(1);if(e.key==='ArrowUp')tokNext(-1)}
});

/* ── 列表栏 ⟳ = 换一批（不是重载页面）──
   每次点用一个新种子重排，所以「这一批」内部翻页稳定，批与批之间不同。
   不用 RANDOM()：那样翻页会重复和漏掉条目。
   自动刷新只在首页空闲态执行，不打断播放、搜索、选择或其他页面。 */
async function refreshAll(automatic=false){
  if(automatic&&(document.hidden||!isCatalogPath(decodeURIComponent(location.pathname))||
      !$('#stage').hidden||!$('#tok').hidden||selectMode||selected.size||document.activeElement===$('#q')))return false;
  if(!$('#stats').hidden){
    if(location.pathname==='/review'){await openReview(false);return}
    if(location.pathname==='/taste'){await openTaste(false);return}
    if(location.pathname==='/duplicates'){await openDuplicates(false);return}
    if(location.pathname==='/quality-goals'){await openQualityGoals(false);return}
    if(location.pathname==='/playlists'){await openPlaylists(false);return}
    /* 追更页不参与换批：重画要重新取数，联网检查只能由自己的明确按钮触发。 */
    if(location.pathname==='/follow'||location.pathname==='/follow-manage')return;
    await openStats(false);return
  }
  if(!$('#index').hidden){return}
  state.sort='seed';state.seed=rollSeed();
  // 顶部三层（女优头像、厂牌、标签）此前从不跟着换：它们有 30 秒会话缓存，
  // 而 refreshAll 只重载网格，于是「换一批」之后上面还是原来那批人。
  barsDataCache=null;barsDataPromise=null;
  await Promise.all([load(true),buildBars()]);
  if(!automatic)window.scrollTo({top:0,behavior:'smooth'});
  return true;
}
/* ── 审查遮挡 ──
   共享屏幕 / 录屏 / 截图时把全站内容画面盖住。开关在设置面板（安全组），
   默认关闭：日常浏览不需要遮挡；只在「用会审查内容的模型做截图或视觉
   测试」的会话里打开（项目规则见 AGENTS.md）。开启时顺手撤掉正在飞的
   悬停预览——动起来的画面比静帧更漏。悬停预览的启动路径也查这个开关，
   遮挡期间不再拉流。 */
const CENSOR_KEY='peach-censor';
const censorOn=()=>document.body.classList.contains('censor');
function applyCensor(on){
  document.body.classList.toggle('censor',on);
  const box=$('#censorSetting');
  if(box)box.checked=on;
}
applyCensor(localStorage.getItem(CENSOR_KEY)==='1');
$('#censorSetting').onchange=e=>{
  const on=e.target.checked;
  localStorage.setItem(CENSOR_KEY,on?'1':'0');
  applyCensor(on);
  if(on)releaseHoverPreviews();
};

/* 横向行支持鼠标拖动（三层顶栏、短片带、接着看都没滚动条，只能滚轮/触摸） */
function wireDrag(el){
  if(!el||el.dataset.drag)return; el.dataset.drag='1';
  let down=false,sx=0,sl=0,moved=0;
  el.addEventListener('mousedown',e=>{
    if(e.button!==0)return; down=true;moved=0;sx=e.pageX;sl=el.scrollLeft;
    el.style.cursor='grabbing'});
  window.addEventListener('mouseup',()=>{if(!down)return;down=false;el.style.cursor=''});
  el.addEventListener('mousemove',e=>{
    if(!down)return; const dx=e.pageX-sx; moved=Math.max(moved,Math.abs(dx));
    el.scrollLeft=sl-dx; e.preventDefault()});
  // 拖动过就吞掉这次点击，别误触发筛选
  el.addEventListener('click',e=>{if(moved>6){e.stopPropagation();e.preventDefault();moved=0}},true);
  // 滚轮竖向 → 横向
  el.addEventListener('wheel',e=>{
    if(Math.abs(e.deltaY)>Math.abs(e.deltaX)){el.scrollLeft+=e.deltaY;e.preventDefault()}},
    {passive:false});
}
function wireAllDrag(){['#tagbar','#srow','#nrow'].forEach(s=>wireDrag($(s)));
  document.querySelectorAll('.tier').forEach(wireDrag)}

async function restoreRoute(){
  surfaceEpoch++;
  syncPageTitle(location.href);
  const path=decodeURIComponent(location.pathname),parts=path.split('/').filter(Boolean);
  const previousPath=lastRoutePath;lastRoutePath=path;
  if(path==='/'&&new URLSearchParams(location.search).get('state')==='ads'){
    route(junkPath(),true);await restoreRoute();return;
  }
  if(isCatalogPath(path)){
    const params=new URLSearchParams(location.search);
    const enteringHome=path==='/'&&previousPath!=='/';
    if(enteringHome){barsDataCache=null;barsDataPromise=null}
    if(path==='/junk-files'){
      junkKind=cleanJunkKind(params.get('type')||'');
      junkView=params.get('view')==='dismissed'?'dismissed':'pending';
    }
    state={...state,loc:params.get('loc')||'local,115',creator:params.get('creator')||'',studio:params.get('studio')||'',
      tag:cleanTagFilter(params.get('tag')),tag_match:params.get('tag_match')==='any'?'any':'all',len:params.get('len')||'',
      dur_min:params.get('dur_min')||'',dur_max:params.get('dur_max')||'',orient:params.get('orient')||'',
      state:ROUTE_STATES[path]||params.get('state')||'',sort:cleanSort(params.get('sort')),
      seed:params.get('seed')||(enteringHome?rollSeed():state.seed||rollSeed()),q:params.get('q')||'',jav:params.get('jav')||''};
    $('#q').value=state.q;buildEdge();buildBars();load(true);return;
  }
  if(path==='/trash'){
    state={...state,creator:'',studio:'',tag:'',orient:'',state:'trash',q:''};$('#q').value='';
    buildEdge();buildBars();load(true);return;
  }
  if(path==='/playlists'){await openPlaylists(false);return}
  if(parts[0]==='playlists'&&/^\d+$/.test(parts[1]||'')&&/^\d+$/.test(parts[2]||'')){await openPlaylist(+parts[1],+parts[2],false);return}
  if(parts[0]==='mix'&&/^\d+$/.test(parts[1]||'')&&/^\d+$/.test(parts[2]||'')){await openMix(+parts[1],+parts[2],false);return}
  if(parts[0]==='parts'&&/^\d+$/.test(parts[1]||'')&&/^\d+$/.test(parts[2]||'')){await openParts(+parts[1],+parts[2],false);return}
  if(parts[0]==='item'&&/^\d+$/.test(parts[1]||'')){await openItem(+parts[1],false);return}
  if(parts[0]==='follow'&&parts[1]==='item'&&/^\d+$/.test(parts[2]||'')){
    await openFollow(false,true);await openFollowDetail(+parts[2],false);return}
  const entityKind=ROUTE_ENTITIES[parts[0]];
  if(entityKind&&parts.length>=2){await openEntity(entityKind,parts.slice(1).join('/'),false);return}
  if(path==='/performers'||path==='/creators'||path==='/tags'){
    const params=new URLSearchParams(location.search);
    if(path==='/tags'){
      tagIndexMode=params.get('view')==='cloud'?'cloud':'alphabet';
      const category=params.get('category')||'all';
      tagIndexCategory=TAG_CATEGORIES.some(([key])=>key===category)?category:'all'}
    await openIndex(path.slice(1),params.get('q')||'',false);return}
  if(path==='/stats'){await openStats(false);return}
  if(path==='/taste'){await openTaste(false);return}
  if(path==='/review'){await openReview(false);return}
  if(path==='/duplicates'){await openDuplicates(false);return}
  if(path==='/resource-sync'){await openResourceSync(false);return}
  if(path==='/quality-goals'){await openQualityGoals(false);return}
  if(path==='/follow'){await openFollow(false);return}
  if(path==='/follow-manage'){await openFollowManage(false);return}
  if(path==='/immerse'){await openTok(undefined,false);return}
  showHomeSurfaces();disposeStage(false);
}
window.addEventListener('popstate',restoreRoute);
buildEdge();
loadSourceStatus()
  .then(buildBars)
  .then(async()=>{buildEdge();wireAllDrag();await restoreRoute();scheduleStickySurfaces()})
  .then(loadSyncedSettings);
