import {$, ENTITY_ROUTES, LOC, ROUTE_ENTITIES, ROUTE_STATES, SITE_FAVICONS, STATE_LABELS, STATE_ROUTES, api, isAbort, mapLimit, brandIcon, entityPath, esc, faviconFallbackUrl, faviconUrl, linkHost, linkMarkUrl, fmtClock, fmtDur, fmtSize, foldName, icon, isCatalogPath, realDuration} from './js/core.js';
import { imageFallbackAttrs, wireImageFallbacks } from './js/image-fallback.js';
import { javDisplayName, javTitleHtml } from './js/jav-title.js';
import { matchRoute, routeLabel } from './js/routes.js';
import { initMiddleTruncate } from './js/middle-truncate.js';
import { tagLabel } from './js/tags.js';
import { syncSidebarSurface, sidebarTagCounts, sidebarHasCatalogContent } from './dist/peach-ui.js';
import {
  breadcrumbHtml, checkboxHtml, closeAnchoredMenu, confirmModal, emptyStateHtml, fieldsetTitle,
  fillSkeletonTier, fitSkeleton, iconSwitchHtml, loadingDotsHtml,
  mediaViewButtonsHtml, noteHtml, progressHtml, scrollerHtml, searchInputHtml, setActionBusy,
  skeletonHtml, spinnerHtml, wireAnchoredMenu, wireBusyActions, wireCollapse, wireIconSwitch,
  wireScrollers,
} from './js/ui-components.js';

initMiddleTruncate(document);
wireBusyActions(document);
/* 图片回退链全站只有这一条监听。`error` 不冒泡，但捕获阶段照样经过祖先，所以
   挂在 body 上就能接住任何后代 <img>——模板里不再有内联 `onerror`。 */
wireImageFallbacks(document.body);

/* ── 模块级可变状态 ────────────────────────────────────────────────────────────
   下面这些绑定都被写在它们之前的函数读写，所以声明必须排在文件最前面。

   `let`/`const` 有 TDZ：声明那一行执行之前读它是 ReferenceError，不是 undefined。
   「函数在上、声明在下」只在那个函数直到启动之后才第一次被调用时才不炸；谁把它
   挪进启动路径，首屏就直接白屏。真相只留一份，一律放这里，不在用它的地方再声明。

   契约由 tests/test_web_ui.py::test_module_level_bindings_are_declared_before_they_are_used
   守住：app.js 里任何模块级 `let`/`const` 都不许在声明行之前被引用。 */
/* 目录筛选状态。初值要读启动 URL 和保存过的设置，真正的赋值排在 `initialParam()`
   之后（搜索 `state={loc:`）；这里只提前建立绑定，好让上面设置面板的 onchange
   不再落在 TDZ 里。 */
let state;
let barsRequestSeq=0,barsDataCache=null,barsDataAt=0,barsDataPromise=null;
let adsBatch=null,loadRequestSeq=0,listLoading=false;
let followData=null,followRuntime=null,followFilter='',followBusy=false,
  followManageSort='checked',followManageDir='desc';
/* 关注列表四列各自的方向词与默认方向。作者名称是文本列，「从多到少」在它身上
   不成立，只说正倒。 */
const FOLLOW_SORT_LABELS={checked:'检查时间',added:'添加时间',name:'作者名称',sources:'来源数量'};
const FOLLOW_SORT_DIR_WORDS={checked:['从近到远','从远到近'],added:['从近到远','从远到近'],
  name:['倒序','正序'],sources:['从多到少','从少到多']};
const FOLLOW_SORT_DEFAULT_DIR={checked:'desc',added:'desc',name:'asc',sources:'desc'};
/* 同 `sortButtonHtml`：这枚键的无障碍名称说的是点下去会得到什么，所以取反方向的词。 */
const followSortLabel=()=>`按${FOLLOW_SORT_LABELS[followManageSort]||'关注列表'}${
  (FOLLOW_SORT_DIR_WORDS[followManageSort]||[])[followManageDir==='asc'?0:1]||''}排序`;
let followAuthor='',followProvider='',followTags=new Set(),followMediaView='videos',followGroupByItemId=new Map(),followItemsById=new Map(),followDetailReturnPath='/follow';
const selectedIndexTags=new Set();
let entityPhotos=null,entityMediaView=emptyMediaView(),photoWallItems=[];
/* 事务所页看的是它签了谁，所以进页面先摆艺人。视频照样在，只是换一个开关的距离：
   那批片是成员各自拍的，混成一条 feed 回答不了「这家有哪些人」。每次进页面都回到
   艺人，切到视频是这一次浏览的选择，不是这类页面的常态。 */
let agencyRosterView='people',agencyRoster=[];
let sidebarDragKey=null;
let edgeT=null;
/* 搜索下拉里被键盘选中的那一项。列表每次重建都要归零，否则索引会指向已经不存在的行。 */
let searchActive=-1;
/* ────────────────────────────────────────────────────────────────────────── */

/* ── 路由表 ───────────────────────────────────────────────────────────────────
   一屏一条。`match` 的三种写法见 `web/js/routes.js`，其余字段：

   - `open(params,push)`：进入这一屏。`push=false` 表示地址栏已经是它了——首屏
     恢复、popstate、换一批都是这种，此时不再 `route()`。
   - `title`：document.title 用的标签，字符串或拿 params 算的函数；不写则用站名。
   - `nav`：侧栏／抽屉里 `data-nav` 的键，同时决定高亮（`navOn`）和跳转（`navTo`）。
   - `section`：管理区身份（`manageSection`），也是 `openManage` 的入口键。
   - `refresh`：列表栏 ⟳「换一批」在这一屏的行为。`reopen` 重开自己；`skip` 不参与
     ——追更页重画要联网，只能由它自己的按钮触发；不写则回统计页。
   - `reload`：批量操作后就地重取（`reloadCurrentSurface`）。它和 `open` 的区别是
     要保留页内已经打好的输入，所以不能拿 `open` 顶替。

   顺序即优先级：先匹配上的赢，所以精确路径写在同前缀的动态路径前面。

   这张表替掉的是同一份知识的七个副本：`restoreRoute` 的分支链，加上 `navTo`、
   `navOn`、`openManage`、`manageSection`、`reloadCurrentSurface`、`refreshAll`
   各自抄的那几条。加一屏只改这张表；同一份知识散成七处时，漏一处的症状还各不相同：URL 能进但侧栏不亮、
   点进去了但「换一批」把你扔回统计页、批量操作后回到首页而不是刚才那一屏。 */
const ROUTES=[
  /* 目录页：首页和四个筛选态是同一屏，路径只决定初始筛选，所以共用一个 open。
     四条筛选态直接由 STATE_ROUTES 生成——它同时是 `isCatalogPath` 的判据，
     两边各写一份就会有「路由认得、目录判定不认得」的半死路径。 */
  {match:'/',open:()=>openCatalog('/')},
  ...Object.entries(STATE_ROUTES).map(([key,path])=>({
    match:path,nav:key,title:STATE_LABELS[key],open:()=>openCatalog(path)})),
  {match:'/trash',section:'trash',open:(params,push)=>openTrash(push)},
  {match:'/playlists',nav:'playlists',title:'播放列表',refresh:'reopen',
    open:(params,push)=>openPlaylists(push)},
  {match:'/playlists/:playlist/:item',nav:'playlists',title:'播放列表',
    open:(params,push)=>openPlaylist(params.playlist,params.item,push)},
  {match:'/mix/:seed/:item',title:'Mix',
    open:(params,push)=>openMix(params.seed,params.item,push)},
  {match:'/parts/:seed/:item',open:(params,push)=>openParts(params.seed,params.item,push)},
  {match:'/editions/:seed/:item',open:(params,push)=>openEditions(params.seed,params.item,push)},
  {match:'/item/:id',title:'作品',open:(params,push)=>openItem(params.id,push)},
  /* 追更详情要先把列表铺好：详情页的返回、上一条／下一条都从那份列表来。 */
  {match:'/follow/item/:id',title:'关注',open:async(params,push)=>{
    await openFollow(push,true);await openFollowDetail(params.id,push)}},
  /* 实体资料页。四种实体只有 kind 不同，名字里可能带斜杠，所以吃掉剩下全部段。 */
  ...Object.entries(ROUTE_ENTITIES).map(([segment,kind])=>({
    match:`/${segment}/:name*`,title:params=>params.name,
    open:(params,push)=>openEntity(kind,params.name,push)})),
  {match:'/performers',nav:'performers',title:'女优',
    open:(params,push)=>openIndexRoute('performers',push),
    reload:()=>openIndexRoute('performers',false,indexQuery())},
  {match:'/creators',title:'创作者',
    open:(params,push)=>openIndexRoute('creators',push),
    reload:()=>openIndexRoute('creators',false,indexQuery())},
  /* 厂商索引的两半。厂牌出片、事务所出人，是两种实体，所以是两条路径；页内那个
     开关只是在两条路径之间走，不是同一份数据的两种筛选。 */
  {match:'/studios',nav:'studios',title:'厂牌',
    open:(params,push)=>openIndexRoute('studios',push),
    reload:()=>openIndexRoute('studios',false,indexQuery())},
  {match:'/agencies',title:'事务所',
    open:(params,push)=>openIndexRoute('agencies',push),
    reload:()=>openIndexRoute('agencies',false,indexQuery())},
  {match:'/tags',nav:'tags',title:'标签',
    open:(params,push)=>openIndexRoute('tags',push),
    reload:()=>openIndexRoute('tags',false,indexQuery())},
  {match:'/stats',section:'stats',title:'统计',open:(params,push)=>openStats(push)},
  {match:'/taste',section:'taste',title:'口味',refresh:'reopen',
    open:(params,push)=>openTaste(push)},
  {match:'/review',section:'review',title:'人工复核',refresh:'reopen',
    open:(params,push)=>openReview(push)},
  {match:'/data-cleanup',section:'cleanup',title:'数据管理',
    open:(params,push)=>openDataCleanup(push)},
  // 重复文件报数据管理的身份：它是那一屏的下一步，`openManage('cleanup')` 仍
  // 应该开数据管理本身，靠的是 /data-cleanup 在表里排在前面。
  {match:'/duplicates',section:'cleanup',title:'重复文件',refresh:'reopen',
    open:(params,push)=>openDuplicates(push)},
  // /resource-sync 是数据管理页上的一个锚点，没有自己的管理身份。
  {match:'/resource-sync',title:'数据管理',open:(params,push)=>openResourceSync(push)},
  {match:'/quality-goals',section:'quality',title:'高清版',refresh:'reopen',
    open:(params,push)=>openQualityGoals(push)},
  {match:'/follow',nav:'follow',title:'关注',refresh:'skip',
    open:(params,push)=>openFollow(push),reload:()=>openFollow(false)},
  {match:'/follow-manage',section:'follow',title:'关注管理',refresh:'skip',
    open:(params,push)=>openFollowManage(push)},
  {match:'/immerse',nav:'immerse',title:'沉浸模式',
    open:(params,push)=>openTok(immerseStartId(),push)},
];
/* 登记一条新路由。ADR-0022 的迁移是逐屏搬到 `frontend/`：搬走的那一屏在自己的
   入口里登记，不必回来改这张表。挂在 window 上是因为 app.js 是入口模块，别的
   bundle 没法 import 它。
   插在表尾，所以新路由要么是一条新路径，要么比现有条目更具体。 */
const registerRoute=spec=>{ROUTES.push(spec);return spec};
window.peachRegisterRoute=registerRoute;

const pageSkeletonHtml=(label,{cards=false,className='',variant='',count,fill}={})=>
  skeletonHtml(label,{variant:variant||(cards?'cards':'panel'),className,
    ...(count?{count}:{}),...(fill===undefined?{}:{fill})});
/* 关注页的骨架跟首页共用海报卡那套几何：网格算式、卡内每一格都一样，只有归属行
   高一点（`.followitem .meta .s` 有 min-height）。上面两条是它自己的作者行和筛选
   行，形状取 `.tier`/`.tagbar` 本身，所以和首页顶栏是同一枚，不必另画一套。 */
const followSkeletonHtml=(label='正在读取关注内容')=>`<div class="follow">
  <div class="followhead"><h2 class="pagetitle">关注</h2></div>
  <div class="tier followauthors" data-skeleton-tier="av"></div>
  <div class="tagbar followfilters" data-skeleton-tier="pill"></div>
  ${pageSkeletonHtml(label,{cards:true,className:'follow-content-skeleton postercard-skeleton'})}</div>`;
$('#loadSentinel').innerHTML=loadingDotsHtml('继续载入中…');
$('#tokLoader').insertAdjacentHTML('afterbegin',spinnerHtml('媒体加载中'));
/* 筛选条只由当前 state 决定，这次加载不会改变它，所以它现在就能画成最终样子。
   `state` 在启动 URL 解析之后才赋值，冷启动第一张骨架比它早，那一次只画计数骨架。 */
const countSortsHtml=()=>!state?'':`<span class="sorts"><button class="batchaction" id="batchAction" type="button"
    title="换一批" aria-label="换一批">${icon('refresh-cw')}</button>`
  // JAV 版式紧跟换批动作，和排序连成一条。
  +(javActive()?javLayoutButtons():'')
  +sortOptions().map(([k,l])=>sortButtonHtml(k,l,state.sort,state.dir,'data-sort')).join('')+`</span>`;
function wireCountRow(){
  const batch=$('#batchAction');
  if(batch)batch.onclick=async()=>{
    if(batch.getAttribute('aria-busy')==='true')return;
    const old=batch.innerHTML;setActionBusy(batch);batch.innerHTML=spinnerHtml('换一批');
    try{await refreshAll()}finally{setActionBusy(batch,false);batch.innerHTML=old}
  };
  wireJavLayoutButtons($('#count'));
  $('#count').querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{
    const next=nextSortState(b.dataset.sort,state.sort,state.dir);
    if(!next)return;
    state.sort=next.sort;state.dir=next.dir;
    load(true)});
}
/* 骨架只盖这次加载真会变的东西，也就是计数那一串数字。筛选条照常画出来并接上事件：
   连它一起清空的话，点下去的那一枚会在等数据的这段时间里失去高亮，看着像没点上；
   `.count:empty` 还会让整行折叠，网格跟着往上跳一截。计数骨架宽高固定、行本身有
   `min-height:var(--sortH)` 兜底，所以数字回来时不发生位移。上方的标签条和已选条件
   同理不动——它们本来就不随这次请求变。 */
function renderCatalogLoading(label='正在读取作品'){
  const count=$('#count');
  count.setAttribute('aria-busy','true');
  count.setAttribute('aria-label',label);
  // 回收站的计数挂在说明行上，这一行只剩「清空回收站」，没有会变的数字可占位。
  count.innerHTML=state&&state.state==='trash'?''
    :`<span class="mono"><span class="countskeleton"></span></span>`+countSortsHtml();
  wireCountRow();
  /* 骨架一铺上去就得把底部那颗 Loading Dots 收掉。骨架说的是「等下会出现几张什么
     形状的卡」，dots 说的是「上面已经有内容，还在往下接」；两段同时在场时一屏里
     铺着两种等待动画，而实际只有一次请求在跑。哨兵的可见性由数据落地后的
     `has_more` 重新决定，所以这里只管收，不必记住原值。 */
  $('#loadSentinel').hidden=true;
  $('#grid').innerHTML=pageSkeletonHtml(label,
    {cards:true,className:'catalog-skeleton postercard-skeleton'});
  fitSkeleton($('#grid'));
}
/* 每个管理表面的加载态只有一份定义，深链启动和路由到位后都从这里取。
   两处各写各的时，整页刷新会连播两段动画：先一张通用大布局骨架，再各页自己的
   加载态（数据管理那张还是 Loading Dots）。取同一份，键就相同，
   showManagementBody 认出是同一张后不再重画。 */
const MANAGEMENT_PLACEHOLDERS={
  '/stats':()=>`<div class="insightpage">${pageSkeletonHtml('正在读取统计',{variant:'dashboard'})}</div>`,
  // 口味页与统计页同一套版式：指标带、一块主详情、下面同层的数据面板。
  '/taste':()=>`<div class="tastepage">${pageSkeletonHtml('正在读取口味分析',{variant:'dashboard'})}</div>`,
  '/data-cleanup':()=>`<div class="cleanuppage">${
    pageSkeletonHtml('正在读取数据管理状态',
      {cards:true,fill:false,className:'cleanup-skeleton'})}</div>`,
  // /resource-sync 只是数据管理页上的一个锚点，启动时占位也该是数据管理那张。
  '/resource-sync':()=>MANAGEMENT_PLACEHOLDERS['/data-cleanup'](),
  '/duplicates':()=>pageSkeletonHtml('正在比对重复内容',{cards:true}),
  '/review':()=>pageSkeletonHtml('正在读取复核队列',{cards:true}),
  '/quality-goals':()=>pageSkeletonHtml('正在读取高清版目标',{cards:true}),
  '/playlists':()=>pageSkeletonHtml('正在读取播放列表',{cards:true}),
  // 关注管理是三个大区（添加关注、关注列表、凭据），不是一屏同质卡片：
  // 骨架照 .fsec 的轮廓画三块，六张 16:9 占位说的是另一个页面的结构。
  '/follow-manage':()=>`<div class="follow">${pageSkeletonHtml('正在读取关注管理',
    {cards:true,count:3,fill:false,className:'followmanage-skeleton'})}</div>`,
};
const managementPlaceholder=path=>
  (MANAGEMENT_PLACEHOLDERS[path]||(()=>pageSkeletonHtml('正在读取页面')))();
/* 顶部三层只属于首页。深链启动时先画一遍再由路由收起来，等于向管理页和索引页
   承诺了三条永远不会到货的横条。 */
const hideDiscoveryBars=()=>{$('#tiers').style.display='none';$('#tagbar').style.display='none'};
/* 启动那一屏收没收横条，就是这一次启动要不要那两个聚合查询。问屏幕不问路径：
   判断只写在上面那个函数里一份，两边各抄一张路径表迟早会对不上。 */
const wantsDiscoveryBars=()=>$('#tiers').style.display!=='none';
function renderInitialSurfaceLoading(){
  const path=decodeURIComponent(location.pathname);
  if(path==='/junk-files'){
    /* 垃圾文件是一屏同质卡片，等的是内容结构不是后台进度：Loading Dots 说的是
       「还在跑」，这里要说的是「等下会出现几张什么形状的卡」，所以用目录骨架。 */
    renderCatalogLoading('正在读取垃圾文件');
    return;
  }
  const management=new Set(['/stats','/taste','/review','/data-cleanup','/duplicates','/quality-goals',
    '/playlists','/resource-sync','/follow','/follow-manage']);
  if(management.has(path)||path.startsWith('/follow/item/')){
    hideDiscoveryBars();
    const stats=$('#stats');stats.hidden=false;$('#grid').innerHTML='';
    stats.innerHTML=path.startsWith('/follow')&&path!=='/follow-manage'
      ?followSkeletonHtml('正在读取关注内容')
      :managementPlaceholder(path);
    fitSkeleton(stats);
    return;
  }
  if(path==='/performers'||path==='/creators'||path==='/tags'||
      /^\/(?:performers|creators|studios|agencies)\//.test(path)){
    hideDiscoveryBars();
    $('#index').hidden=false;$('#grid').innerHTML='';
    $('#index').innerHTML=pageSkeletonHtml('正在读取页面',{cards:true});
    fitSkeleton($('#index'));
    return;
  }
  renderCatalogLoading();
}
renderInitialSurfaceLoading();

/* 路由同时把页面表面写进 body[data-surface]：限宽等按表面生效的版式
   （管理页不全宽）靠它切换，不用每个渲染函数自己记得加类。
   调用方有传 path 也有传 href 的，这里统一归一成 pathname。 */
const syncPageTitle=path=>{
  const url=new URL(path,location.origin);
  const label=routeLabel(ROUTES,decodeURIComponent(url.pathname));
  document.title=label?`${label} · Peach`:'Peach · 蜜桃';
  document.body.dataset.surface=url.pathname;
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
/* 每个表面自带一个 AbortController：claimSurface 先作废上一屏的读请求再推进 epoch。
   只判过期（`surfaceCurrent`）而让请求跑到底的话，切三四页就有三四份读请求同时占着
   那 6 条连接，最后停留的那一页反而排在队尾。
   只有拿到 token 的读请求会被取消；写操作不带 signal，切页不会撤掉一次真实写入。 */
let surfaceRequests=null;
const surfaceToken=path=>({epoch:surfaceEpoch,path,signal:surfaceRequests?.signal});
const surfaceCurrent=token=>token.epoch===surfaceEpoch&&surfacePath()===token.path;
const claimSurface=path=>{
  surfaceRequests?.abort();
  surfaceRequests=new AbortController();
  surfaceEpoch++;return surfaceToken(path)};
/* 表面级读请求：带上这个表面的 signal，被取消时返回 null 而不是抛错。
   取消只可能由 claimSurface 触发，而它已经推进了 epoch，所以调用点紧随其后的
   `surfaceCurrent()` 必然为假、走的是同一条过期分支——不用给每个表面套一层
   try/catch，也不会多出一条没人接的 rejection。 */
const surfaceApi=(token,path,options)=>api(path,{...options,signal:token.signal})
  .catch(error=>{if(isAbort(error))return null;throw error});
const route=(path,replace=false)=>{
  surfaceEpoch++;
  barsRequestSeq++;
  history[replace?'replaceState':'pushState']({},'',path);syncPageTitle(path);
  lastRoutePath=decodeURIComponent(new URL(path,location.href).pathname);
  queueMicrotask(()=>{syncHeaderActions();paintListTitle();buildDrawerNavigation()});
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
/* `dropOfflineFromDefaultLoc()` 的定义挪到了 `state` 声明之后。它读 `initialParams`
   和 `state`，两者都是模块级 `const`/`let`，在声明行之前处于 TDZ。函数声明会提升，
   所以上面这一行调用照样成立。 */
const DURATION_TAGS=new Set(['短片-2分内','中片-10分内','长片-30分内','超长片-30分上']);
const SETTINGS_KEY='peach.settings.v1';
const DEFAULT_SIDEBAR_ORDER=['','performers','studios','tags','jav','flagged','playlists','follow','immerse','manage'];
const OPTIONAL_SIDEBAR_KEYS=['stats','review','data-cleanup','trash','follow-manage','quality'];
const ALL_SIDEBAR_KEYS=[...DEFAULT_SIDEBAR_ORDER,...OPTIONAL_SIDEBAR_KEYS];
const SORTS=[['seed','随机'],['rating','评分'],['o','高潮计数'],['plays','观看次数'],['dur','时长'],
             ['size','体积'],['new','入库时间'],['played','观看时间']];
const JAV_RELEASE_SORT=['release','发行时间'];
const SORT_KEYS=[...SORTS,JAV_RELEASE_SORT].map(([key])=>key);
/* 方向词按列各自定义：同一个 desc 在时间列上是「从新到旧」，在时长上是「从长到短」，
   写成通用的「降序」等于让界面解释 SQL。数组是 [desc,asc]，在表里就等于这一列可翻转。 */
const SORT_DIR_WORDS={rating:['从高到低','从低到高'],o:['从多到少','从少到多'],
  plays:['从多到少','从少到多'],dur:['从长到短','从短到长'],size:['从大到小','从小到大'],
  new:['从新到旧','从旧到新'],played:['从近到远','从远到近'],release:['从新到旧','从旧到新']};
/* 旧键沿用：地址栏、书签和设置里存着把方向写进键名的值。方向现在单独由 `dir` 表达，
   两个时长键收敛成一个 dur；认不出旧键的后果不是报错，是静默换成另一种排序。 */
const SORT_ALIASES={big:['size','desc'],short:['dur','asc'],long:['dur','desc']};
const sortDirWord=(key,dir)=>(SORT_DIR_WORDS[key]||[])[dir==='asc'?1:0]||'';
const defaultSortDir=key=>SORT_DIR_WORDS[key]?'desc':'';
const DEFAULT_SETTINGS={batchSize:60,defaultSort:'seed',sortDefaultsVersion:3,hoverDelaySeconds:5,seekSeconds:10,searchHistoryLimit:10,relatedLimit:20,javLayout:'big',followLayout:'cozy',peopleLayout:'big',ambientMode:true,theaterMode:false,groupCollapse:true,sidebarOrder:DEFAULT_SIDEBAR_ORDER};
let appSettings={...DEFAULT_SETTINGS};
try{appSettings={...DEFAULT_SETTINGS,...JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}}catch(_e){}
const allowedSetting=(value,allowed,fallback)=>allowed.includes(value)?value:fallback;
delete appSettings.rotateMinutes;
/* 迁移只碰默认值本身：把界面上已经不存在的键换成当前键，用户主动选过的排序不动。
   不迁移的话 allowedSetting 会把它静默打回随机。 */
let sortDefaultsMigrated=false;
if((+appSettings.sortDefaultsVersion||0)<2&&appSettings.defaultSort==='new'){
  appSettings.defaultSort='seed';sortDefaultsMigrated=true
}
if((+appSettings.sortDefaultsVersion||0)<3&&SORT_ALIASES[appSettings.defaultSort]){
  appSettings.defaultSort=SORT_ALIASES[appSettings.defaultSort][0];sortDefaultsMigrated=true
}
appSettings.sortDefaultsVersion=3;
appSettings.batchSize=allowedSetting(+appSettings.batchSize,[30,60,90],60);
appSettings.defaultSort=allowedSetting(appSettings.defaultSort,SORT_KEYS,'seed');
appSettings.hoverDelaySeconds=allowedSetting(+appSettings.hoverDelaySeconds,[3,5,8],5);
appSettings.seekSeconds=allowedSetting(+appSettings.seekSeconds,[5,10,30],10);
appSettings.ambientMode=appSettings.ambientMode!==false;
appSettings.theaterMode=appSettings.theaterMode===true;
appSettings.groupCollapse=appSettings.groupCollapse!==false;
appSettings.searchHistoryLimit=allowedSetting(+appSettings.searchHistoryLimit,[5,10,20],10);
appSettings.relatedLimit=allowedSetting(+appSettings.relatedLimit,[12,20,30],20);
const sidebarKeyAlias=key=>key==='ads'||key==='dupes'?'data-cleanup':key;
appSettings.sidebarOrder=[...new Set((Array.isArray(appSettings.sidebarOrder)?appSettings.sidebarOrder:DEFAULT_SIDEBAR_ORDER).map(sidebarKeyAlias))].filter(key=>ALL_SIDEBAR_KEYS.includes(key));
if(!appSettings.sidebarOrder.length)appSettings.sidebarOrder=[...DEFAULT_SIDEBAR_ORDER];
document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);
const saveSettings=()=>localStorage.setItem(SETTINGS_KEY,JSON.stringify(appSettings));
if(sortDefaultsMigrated)saveSettings();
function syncSettingsPanel(){
  $('#batchSizeSetting').value=String(appSettings.batchSize);
  $('#defaultSortSetting').value=appSettings.defaultSort;
  $('#hoverDelaySetting').value=String(appSettings.hoverDelaySeconds);
  $('#groupCollapseSetting').checked=appSettings.groupCollapse;
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
$('#defaultSortSetting').onchange=e=>{appSettings.defaultSort=e.target.value;saveSettings();state.sort=appSettings.defaultSort;state.dir=defaultSortDir(state.sort);if(location.pathname==='/')load(true)};
$('#hoverDelaySetting').onchange=e=>{appSettings.hoverDelaySeconds=+e.target.value||5;document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);saveSettings()};
/* 关掉后同一番号的每个分卷／版次各占一张卡。改完要重取当前列表：折叠是在渲染
   时做的，不重画的话已经被跳过的那些卡不会自己冒出来。 */
$('#groupCollapseSetting').onchange=e=>{appSettings.groupCollapse=!!e.target.checked;saveSettings();reloadCurrentSurface()};
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
  '115':'<img class="source-icon" src="/logo?studio=115&variant=icon" alt="" data-drop="self">',
  // PikPak 官方触屏图标（取证 follow-source-icons-measured.md）；/logo 的生成 logo 不对版。
  pikpak:'<img class="source-icon" src="https://mypikpak.com/apple-touch-icon.png" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self">',
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
/* Toast 的正文只接 `{text}`（转义后插入）或 `{html}`（原样插入）。

   签名不接裸字符串：那样「这是文本还是 HTML」全靠调用点自己记得 `esc()`，而
   actionReceipt 传的是已经转义过的串、followCheckToast 传的是带 `<b>` 的片段，
   两者在签名上完全一样。真出问题的是那些内容来自账本的回执——
   `已删除标签「${tagLabel(tag)}」` 里的标签名是用户或刮削器写进账本的，含 `<`
   就直接被当成标签插进 DOM。谁是 HTML 由调用点显式声明，不再靠约定。 */
const toastBody=message=>message&&typeof message==='object'&&'html' in message
  ? String(message.html)
  : esc(message&&typeof message==='object'?(message.text??''):message??'');
const toast=(message,{timeout=6000,warn=false,action=null}={})=>{
  const root=$('#toasts');
  const item=document.createElement('div');
  item.className='toast'+(warn?' warn':'');
  const initial=toastBody(message);
  const paint=(body,alert)=>{
    item.classList.toggle('warn',!!alert);
    item.innerHTML=`${alert?icon('alert'):''}<p>${body}</p>${
      action&&!alert&&body===initial?`<button class="tact">${esc(action.label)}</button>`:''
      }<button class="tclose" title="关闭" aria-label="关闭提示">${icon('x')}</button>`;
    item.querySelector('.tclose').onclick=close;
    const act=item.querySelector('.tact');
    if(act)act.onclick=()=>{setActionBusy(act);action.run()};
  };
  let timer=null;
  /* 收起前先把当前高度写死再过渡到 0。直接 remove() 会让这一格瞬间消失，
     栈里剩下的 toast 一次跳过来，正是撤销那一下最明显的抖动。 */
  const close=()=>{clearTimeout(timer);
    item.style.height=`${item.offsetHeight}px`;item.getBoundingClientRect();
    item.classList.add('leaving');setTimeout(()=>item.remove(),200)};
  const arm=()=>{if(timeout)timer=setTimeout(close,timeout)};
  /* 结果就写在同一条 toast 上。「关掉回执 + 另发一条已撤销」会让两条在同一个
     底部对齐的栈里一进一出，看上去就是整块跳了一下。 */
  item.replaceMessage=(body,{warn:alert=false,timeout:next=4000}={})=>{
    clearTimeout(timer);paint(toastBody(body),alert);timeout=next;arm()};
  paint(initial,warn);
  item.addEventListener('mouseenter',()=>clearTimeout(timer));
  item.addEventListener('mouseleave',arm);
  root.prepend(item);arm();
  while(root.children.length>4)root.lastElementChild.remove();
  return item;
};

/* 所有可逆写操作共用同一种回执：只在请求真正完成后报过去时结果，撤销入口
   保留 8 秒。撤销本身也是一次真实写入，失败时另报一条短错误，不能把本地 UI
   偷偷改回去假装成功。不可逆或不适合撤销的操作仍用同一函数，但不传 undo。 */
const actionReceipt=(message,{undo=null,timeout=undo?8000:6000}={})=>{
  let item=null;
  item=toast({text:message},{
    timeout,
    action:undo?{label:'撤销',run:async()=>{
      try{await undo();item.replaceMessage({text:'已撤销'})}
      catch(error){item.replaceMessage({text:`撤销失败：${error.message||'请重试'}`},{warn:true})}
    }}:null,
  });
  return item;
};
const actionFailure=(message,error)=>toast(
  {text:`${message}失败：${error?.message||'请重试'}`},{warn:true});

/* 随机排序每次进入首页都换种子；同一次访问继续复用该种子，保证筛选和分页
   不会重复或漏项。「换一批」仍可在当前访问里主动生成下一批。 */
const newSeed=()=>String((Date.now()^(Math.random()*1e9|0))%99991);
const rollSeed=()=>newSeed();
/* 种子随机：FNV-1a 把「种子 + 键」压成一个 32 位数当排序键。同一个种子下顺序稳定，
   换种子就是另一套顺序，客户端不必存 PRNG 状态，也不必让后端多带一个参数。 */
const seededRank=(seed,value)=>{
  let hash=2166136261>>>0;
  for(const char of `${seed}\u0000${value}`){hash^=char.codePointAt(0);hash=Math.imul(hash,16777619)>>>0}
  return hash;
};
/* 抽样只决定「这一批露出哪些」，不动原有顺序：标签条照旧按数量从多到少读下来，
   换一批换的是成员。装不满就原样返回，详情页那种只有几个标签的集合不受影响。 */
const seededSample=(rows,count,seed,key=row=>row.k)=>{
  if(rows.length<=count)return rows;
  const picked=new Set([...rows]
    .sort((a,b)=>seededRank(seed,key(a))-seededRank(seed,key(b)))
    .slice(0,count).map(key));
  return rows.filter(row=>picked.has(key(row)));
};
const initialParams=new URLSearchParams(location.search);
const JUNK_KIND_OPTIONS=[['','全部','layout-grid'],['video','视频','play'],['image','图片','pics'],
  ['archive','压缩包','file-archive'],['audio','音频','file-audio'],['url','网址','globe'],
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
/* 列和方向一次解出来：旧键自带方向，`dir` 显式写了就听它的，随机没有方向。 */
function resolveSort(rawSort,rawDir,fallback=appSettings.defaultSort){
  const alias=SORT_ALIASES[rawSort];
  const sort=cleanSort(alias?alias[0]:rawSort,fallback);
  if(!SORT_DIR_WORDS[sort])return{sort,dir:''};
  return{sort,dir:rawDir==='asc'||rawDir==='desc'?rawDir:(alias?alias[1]:'desc')};
}
/* 查询参数属于它所在的路由，所以目录的筛选只从目录 URL 里读。

   不能无条件读启动 URL：`/follow?tag=blender` 会顺手把目录也筛成 blender，
   于是顶部画出「blender ✕ 全部清除」——一条目录筛选芯片挂在关注页上，回到首页
   还发现自己被筛住了。关注页的 `tag` 和目录的 `tag` 是两套词表（一个是 booru
   英文标签，一个是本地中文标签），撞在同一个键上只能靠路由分开。 */
const initialCatalogUrl=(path=>isCatalogPath(path)||path==='/trash')(
  decodeURIComponent(location.pathname));
const initialParam=key=>initialCatalogUrl?initialParams.get(key):null;
state={loc:initialParams.get('loc')||'local,115',creator:initialParam('creator')||'',studio:initialParam('studio')||'',
  tag:cleanTagFilter(initialParam('tag')),len:initialParam('len')||'',dur_min:initialParam('dur_min')||'',dur_max:initialParam('dur_max')||'',
  tag_match:initialParam('tag_match')==='any'?'any':'all',orient:initialParam('orient')||'',
  state:ROUTE_STATES[decodeURIComponent(location.pathname)]||initialParam('state')||'',
  ...resolveSort(initialParam('sort'),initialParam('dir')),
  seed:initialParam('seed')||rollSeed(),q:initialParam('q')||'',jav:initialParam('jav')||'',thumb:'1'};
/* 脱盘的来源要从默认筛选里摘掉，否则首页照样按它筛，出来一屏点开就报脱盘的卡片。
   只动默认值：地址栏里显式写了 `loc=` 就是用户自己选的，不替他改。
   全部来源都脱盘时保持原样——清空筛选会变成「什么都不筛」，那比原状更糟。
   必须写在 `state` 之后：`loadSourceStatus()` 在启动时调它，那时 `state` 已初始化。 */
function dropOfflineFromDefaultLoc(){
  if(initialParams.get('loc'))return;
  const kept=state.loc.split(',').filter(Boolean).filter(k=>sourceOnline[k]!==false);
  if(kept.length&&kept.length!==state.loc.split(',').filter(Boolean).length)state.loc=kept.join(',');
}
const HOME_QUERY_KEYS=['loc','creator','studio','tag','tag_match','len','dur_min','dur_max','orient','sort','dir','q','jav'];
function homePath(filters=state){
  const path=STATE_ROUTES[filters.state]||'/';
  const params=new URLSearchParams();
  HOME_QUERY_KEYS.forEach(key=>{const value=filters[key];
    if(value&&!(key==='tag_match'&&value==='all')&&!(key==='dir'&&value===defaultSortDir(filters.sort)))params.set(key,value)});
  if(!STATE_ROUTES[filters.state]&&filters.state)params.set('state',filters.state);
  return path+(params.size?'?'+params:'');
}
/* 所有明确的「回首页」动作必须得到同一个干净状态。只改地址为 `/` 不够：state.jav
   等内存筛选还会继续进入 /api/items，让页面看似首页却只剩 JAV。来源选择是用户的
   浏览范围，继续保留；其余分类、搜索和排序恢复首页默认值。 */
function resetHomeState(){
  state={loc:state.loc,creator:'',studio:'',tag:'',tag_match:'all',len:'',dur_min:'',dur_max:'',
    orient:'',state:'',sort:appSettings.defaultSort,dir:defaultSortDir(appSettings.defaultSort),
    seed:rollSeed(),q:'',jav:'',thumb:'1'};
  barsDataCache=null;barsDataPromise=null;
}
function openHome(scroll=false){
  resetHomeState();route('/');$('#q').value='';disposeStage(false);showHomeSurfaces();
  buildEdge();buildBars();load(true);
  if(scroll)window.scrollTo({top:0,behavior:'smooth'});
}
const ENTITY_FILTER_KEYS=['loc','creator','tag','dur_min','dur_max','orient','sort','dir'];
const emptyEntityFilters=()=>Object.fromEntries(
  ENTITY_FILTER_KEYS.map(key=>[key,key==='sort'?'new':key==='dir'?'desc':'']));
const parseEntityFilters=search=>{const params=new URLSearchParams(search),filters=emptyEntityFilters();
  ENTITY_FILTER_KEYS.forEach(key=>{if(key!=='sort'&&key!=='dir')filters[key]=params.get(key)||''});
  Object.assign(filters,resolveSort(params.get('sort'),params.get('dir'),'new'));return filters};
const entityFilterSearch=filters=>{const params=new URLSearchParams();
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&!(key==='sort'&&filters[key]==='new')
    &&!(key==='dir'&&filters[key]===defaultSortDir(filters.sort)))params.set(key,filters[key])});
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
/* 在线资产的 `path` 是来源作品页，不是可播地址。能播的那条代理在
   `/follow-stream?id=<follow_item>`，保存时写了 `follow_item.asset_id`，
   `/api/item` 反查后回传 `follow_item_id`。 */
function followStreamSource(it){
  return it.location==='online'&&it.follow_item_id
    ?{src:`/follow-stream?id=${it.follow_item_id}`,type:'video/mp4'}:null;
}
async function detailStreamSource(it){
  const proxied=followStreamSource(it);
  if(proxied)return proxied;
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
/* ── 详情舞台的收尾登记 ──────────────────────────────────────────────────────
   `disposeStage()` 用 `stage.innerHTML=''` 清场，那只删得掉 DOM。挂在
   document/window 上的监听和 setInterval 不在舞台里，节点没了它们照样活着，
   并且闭包还攥着已经脱离文档的元素——一次导航泄一份，翻十几个详情就是十几份。

   所以凡是在舞台上开了「舞台之外」的东西，就在这里登记一条撤销。返回值是注销
   函数：浮层自己先关掉时用它把登记摘掉，别让集合无界地长。 */
let stageDisposers=new Set();
function onStageDispose(dispose){stageDisposers.add(dispose);return ()=>stageDisposers.delete(dispose)}
function runStageDisposers(){
  const pending=[...stageDisposers];stageDisposers.clear();
  pending.forEach(dispose=>{try{dispose()}catch(_e){}});
}
/* 浮层的「点外面就关」。document 级捕获监听不随浮层 DOM 一起消失，登记与撤销
   必须成对；关不掉的那一次由舞台销毁兜底。 */
function bindOutsideClose(anchor,inside,close){
  const handler=event=>{if(!inside.contains(event.target)&&event.target!==anchor)close()};
  let unregister=null;
  const detach=()=>{
    document.removeEventListener('pointerdown',handler,true);
    if(unregister){unregister();unregister=null}
  };
  // 延一拍再挂：打开浮层的这一次 pointerdown 还在冒泡，立刻挂上会自己把自己关掉。
  setTimeout(()=>document.addEventListener('pointerdown',handler,true),0);
  unregister=onStageDispose(detach);
  return detach;
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
  runStageDisposers();
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
/* 缓冲前沿：当前播放位置所在那段缓冲的末端。看的是前沿而不是缓冲区总长——播放时浏览器
   会驱逐播过的部分，总长几乎恒定，拿它当下载量会得出「一直是 0」。 */
function bufferedFrontier(video){
  const at=video.currentTime||0;
  for(let i=0;i<video.buffered.length;i++)
    if(video.buffered.start(i)<=at+.25&&video.buffered.end(i)>=at)return video.buffered.end(i);
  return video.buffered.length?video.buffered.end(video.buffered.length-1):0;
}
/* 渐进下载（HTTP Range）量不到网络：浏览器用一条长连接边下边播，请求在播放期间不结束，
   resource timing 里就一直不出现新条目。实测本地 MP4 播到 37 秒时仍只有挂载那两条、字节数
   停在 862 KB，面板于是显示「— · 0 请求」。HLS 是另一回事，每个分片都是一次独立完成的请求，
   VHS 自己也报 bandwidth，resource timing 那套口径只对它成立。
   渐进源改看缓冲前沿的推进：每秒新推进的秒数 × 平均码率就是字节速率；码率未知（在线关注
   条目没有 size）就只报推进倍速。缓冲吃满后浏览器停拉，增量归零，此时保留上一次读数而不是
   跳回 0——那不是速度掉了，是没有在下载。 */
const BUFFER_METER_WINDOW_MS=3000;
function averageBitrate(size,duration){
  const bytes=Number(size)||0,seconds=realDuration(duration)||0;
  return bytes>0&&seconds>0?bytes*8/seconds:0;
}
function createBufferMeter(bitrate){
  const samples=[];let last=null,advanced=0,bits=0,ratio=0;
  return {
    bitrate:Number(bitrate)||0,
    get bits(){return bits},
    get ratio(){return ratio},
    get seconds(){return advanced},
    bytes(){return this.bitrate>0?advanced*this.bitrate/8:0},
    sample(video){
      if(!video)return bits;
      const at=performance.now(),frontier=bufferedFrontier(video),ct=video.currentTime||0;
      if(last){
        const gap=(at-last.at)/1000;
        /* seek 会把前沿整段挪走，那不是这一秒下载了几十分钟；判据是播放位置自己跳了。 */
        const seeked=Math.abs(ct-last.ct)>gap*4+1;
        const step=frontier-last.frontier;
        if(!seeked&&step>0)advanced+=step;
        /* 面板和角标都关着时没人采样，再打开时两点隔了几分钟，窗口要重新起算。 */
        if(gap*1000>BUFFER_METER_WINDOW_MS*2)samples.length=0;
      }
      last={at,frontier,ct};
      samples.push({at,advanced});
      while(samples.length>2&&at-samples[0].at>BUFFER_METER_WINDOW_MS)samples.shift();
      const span=(at-samples[0].at)/1000,gained=advanced-samples[0].advanced;
      if(span>=.5&&gained>0){ratio=gained/span;bits=this.bitrate>0?gained*this.bitrate/span:0}
      return bits;
    }
  };
}
const PLAYER_STATS_HISTORY=24;
function pushPlayerStat(samples,value){
  samples.push(Number.isFinite(value)&&value>0?value:0);
  if(samples.length>PLAYER_STATS_HISTORY)samples.splice(0,samples.length-PLAYER_STATS_HISTORY);
}
/* 设置面板和播放统计都盖在画面上，同时开就互相遮挡。开哪个都往 document 广播一次，
   另一个自己收起：两块面板挂在不同的作用域里，共享一个事件名比互相持有引用干净。 */
const PLAYER_PANEL_EVENT='peach-player-panel';
function playerStatsPlot(samples,kind,ceiling,label){
  const values=Array(Math.max(0,PLAYER_STATS_HISTORY-samples.length)).fill(null).concat(samples);
  const top=Math.max(1,ceiling||0);
  const bars=values.map(value=>{
    if(value===null)return '<i aria-hidden="true"></i>';
    const level=value<=0?0:Math.max(.08,Math.min(1,value/top));
    const state=kind==='buffer'?(value<5?' low':value<15?' mid':' good'):'';
    return `<i class="active${state}" style="height:${(level*100).toFixed(1)}%" aria-hidden="true"></i>`;
  }).join('');
  return `<span class="playerstatsplot ${kind}" role="img" aria-label="${esc(label)}">${bars}</span>`;
}
/* 统计角标、加载速度与面板：作品详情和关注详情共用同一组 id，mountDetailPlayer 直接按 id 取。
   关注详情缺了这三个节点，在线视频就连统计入口都没有。 */
function playerStatsOverlayHtml(){
  return `<button class="playerstatsbtn" id="playerStatsBtn" aria-label="播放统计" title="播放统计" aria-pressed="false" hidden>${icon('chart')}</button>
       <div class="playernet" id="playerNet" role="status" aria-live="polite" hidden></div>
       <div class="playerstats" id="playerStats" role="status" hidden></div>`;
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
function playerSpeedBits(player,id,session='',meter=null){
  let vhs=null;try{vhs=player?.tech({IWillNotUseThisInPlugins:true})?.vhs?.stats||null}catch(_e){}
  const bandwidth=Number(vhs?.bandwidth)||0;
  if(bandwidth>0)return bandwidth;
  /* 传了 meter 就是渐进源：它的 resource timing 本来就量不到，不能拿别的条目顶上。 */
  return meter?Number(meter.bits)||0:streamSpeedBits(id,session);
}
function fmtSpeed(bits){
  if(!Number.isFinite(bits)||bits<=0)return '加载中…';
  const bytes=bits/8;
  return bytes>=1048576?`${(bytes/1048576).toFixed(1)} MB/s`:`${Math.max(1,Math.round(bytes/1024))} KB/s`;
}
/* 码率未知时字节速率无从换算，退回缓冲推进倍速：3 秒里多缓冲了 36 秒就是 12× 实时。 */
function fmtLoadRate(bits,ratio){
  if(bits>0)return fmtSpeed(bits);
  return ratio>0?`${ratio.toFixed(1)}× 实时`:fmtSpeed(0);
}
function applyAmbientMode(enabled,save=true){
  appSettings.ambientMode=!!enabled;if(save)saveSettings();
  $('#stage')?.classList.toggle('ambient-on',appSettings.ambientMode);
  document.dispatchEvent(new CustomEvent('peachambientchange',{detail:{enabled:appSettings.ambientMode}}));
}
/* 控制条上每个按钮的悬停提示都从这里出：文案 + 快捷键徽标，样式取自 YouTube delhi-modern。
   同时抹掉浏览器原生 title——两层提示会一前一后弹出来叠在一起。Video.js 每次改 controlText
   都会把 title 写回去，所以按钮状态同步的地方必须重新调一次返回的 sync。 */
function playerControlTooltip(button,label,shortcut=''){
  if(!button)return()=>{};
  let tip=button.querySelector(':scope>.vjs-peach-tooltip');
  if(!tip){
    tip=document.createElement('span');tip.className='vjs-peach-tooltip';tip.setAttribute('role','tooltip');
    tip.innerHTML='<span class="vjs-peach-tooltip-text"></span><kbd hidden></kbd>';
    button.append(tip);
  }
  const text=tip.querySelector('.vjs-peach-tooltip-text'),key=tip.querySelector('kbd');
  if(shortcut)button.setAttribute('aria-keyshortcuts',shortcut);
  const sync=(nextLabel=label,aria='')=>{
    text.textContent=nextLabel;key.textContent=shortcut;key.hidden=!shortcut;
    button.setAttribute('aria-label',aria||nextLabel);button.removeAttribute('title');
  };
  sync();return sync;
}
/* 快捷键复用按钮自己的点击路径：全屏、画中画、静音各有兜底逻辑挂在按钮上，
   在键盘分支里再实现一遍就会和按钮走岔。 */
function clickPlayerControl(video,selector){
  video?.closest('.vwrap')?.querySelector('.vjs-control-bar '+selector)?.click();
}
function syncPlayerTheaterButton(button){
  if(!button)return;
  const label=appSettings.theaterMode?'默认视图':'影院模式';
  button.setAttribute('aria-pressed',String(appSettings.theaterMode));
  button.querySelector('use')?.setAttribute('href',appSettings.theaterMode?'#i-theater-exit':'#i-theater-enter');
  (button.peachTooltipSync||(()=>{}))(label);
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
/* `sourceQualities` 是来源自己给的清晰度表（[{height,label}]，从高到低）。
   rule34video 把每档写成独立字段，videojs 的 qualityLevels 看不到它们——那套只认
   HLS/DASH 的自适应轨道，而这里是四个各自独立的 mp4。所以由调用方查好再传进来。 */
function mountPlayerQualityControl(player,video,fallbackHeight=0,initialSourceQualities=null){
  const controlBar=player.getChild('controlBar')?.el();
  if(!controlBar||controlBar.querySelector('[data-player-quality]'))return;
  const root=document.createElement('div');
  root.className='vjs-peach-settings vjs-control';root.dataset.playerQuality='';
  root.innerHTML=`<button type="button" class="vjs-peach-settings-toggle" aria-label="播放器设置" aria-expanded="false">
    ${icon('settings')}<span data-player-quality-badge hidden></span></button>
    <div class="vjs-peach-settings-menu" role="menu" aria-label="播放器设置" aria-hidden="true"></div>`;
  const fullscreen=controlBar.querySelector('.vjs-fullscreen-control');
  controlBar.insertBefore(root,fullscreen||null);
  const toggle=root.querySelector('button'),badge=root.querySelector('[data-player-quality-badge]');
  playerControlTooltip(toggle,'设置');
  const menu=root.querySelector('.vjs-peach-settings-menu');
  const levels=typeof player.qualityLevels==='function'?player.qualityLevels():null;
  let sourceQualities=initialSourceQualities;
  let selectedQuality='auto';
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
    if(sourceQualities?.length){
      return sourceQualities.map(q=>({key:`h${q.height}`,label:q.label||`${q.height}p`,pixels:q.height}));
    }
    const pixels=resolution(video.videoWidth,video.videoHeight)||Number(fallbackHeight)||0;
    return [{key:'original',label:pixels?`${pixels}p`:'原画',pixels}];
  };
  const qualityRows=()=>{
    const options=rows();
    if(!levels?.length&&!sourceQualities?.length)selectedQuality='original';
    const active=options.find(option=>option.key===selectedQuality)||options[0];
    const activePixels=active.pixels||Math.max(0,...options.map(option=>option.pixels||0));
    badge.textContent=activePixels>=2160?'4K':activePixels>=720?'HD':'';badge.hidden=!badge.textContent;
    return {options,active};
  };
  const isOpen=()=>menu.getAttribute('aria-hidden')!=='true';
  const setOpen=open=>{menu.setAttribute('aria-hidden',String(!open));toggle.setAttribute('aria-expanded',String(open));
    if(open)document.dispatchEvent(new CustomEvent(PLAYER_PANEL_EVENT,{detail:'settings'}))};
  const close=()=>setOpen(false);
  const closeSettingsForOtherPanel=event=>{if(event.detail!=='settings')close()};
  document.addEventListener(PLAYER_PANEL_EVENT,closeSettingsForOtherPanel);
  /* 面板之间的切换照 YouTube 播放器 9470c977 的 www-player.css：popup 自己 .25s
     cubic-bezier(.4,0,.2,1) 改高度，旧面板往来的方向滑出、新面板从去的方向滑入。
     旧面板必须先脱离布局再滑，否则两块内容会在动画期间把菜单撑成两倍高；高度也得
     先钉在旧值、下一帧再写新值，同一帧写两次只会直接跳到新值，看不到过渡。 */
  const PANEL_MS=250;
  let panelTimer=null;
  const renderPanel=(html,direction)=>{
    const current=menu.querySelector('.vjs-peach-panel');
    const next=document.createElement('div');next.className='vjs-peach-panel';next.innerHTML=html;
    if(!current||!direction||!isOpen()){menu.replaceChildren(next);menu.style.height='';return next}
    if(panelTimer){clearTimeout(panelTimer);panelTimer=null}
    const from=menu.getBoundingClientRect().height;
    current.classList.add('vjs-peach-panel-leaving');
    next.classList.add(direction>0?'vjs-peach-panel-animate-forward':'vjs-peach-panel-animate-back');
    menu.append(next);menu.style.height=`${from}px`;
    const to=next.scrollHeight;
    requestAnimationFrame(()=>{
      menu.classList.add('vjs-peach-popup-animating');menu.style.height=`${to}px`;
      next.classList.remove('vjs-peach-panel-animate-forward','vjs-peach-panel-animate-back');
      current.classList.add(direction>0?'vjs-peach-panel-animate-back':'vjs-peach-panel-animate-forward');
      panelTimer=setTimeout(()=>{
        panelTimer=null;current.remove();
        menu.classList.remove('vjs-peach-popup-animating');menu.style.height='';
      },PANEL_MS);
    });
    return next;
  };
  const showMain=(direction=0)=>{
    const {active}=qualityRows(),speed=Number(player.playbackRate())||1;
    const panel=renderPanel(`<div class="vjs-peach-panel-menu"><button type="button" class="vjs-peach-menu-row" role="menuitemcheckbox" data-player-ambient aria-checked="${appSettings.ambientMode}">
      ${icon('player-ambient')}<span>氛围模式</span><i class="vjs-peach-switch" aria-hidden="true"></i></button>
      <button type="button" class="vjs-peach-menu-row" role="menuitem" data-player-speed>${icon('player-speed')}<span>播放速度</span><b>${speed===1?'正常':speed+'×'}</b>${icon('player-menu-next')}</button>
      <button type="button" class="vjs-peach-menu-row" role="menuitem" data-player-quality-view>${icon('player-quality')}<span>清晰度</span><b>${esc(active.label)}</b>${icon('player-menu-next')}</button></div>`,direction);
    panel.querySelector('[data-player-ambient]').onclick=()=>{applyAmbientMode(!appSettings.ambientMode);showMain()};
    panel.querySelector('[data-player-speed]').onclick=()=>showSpeed();
    panel.querySelector('[data-player-quality-view]').onclick=()=>showQuality();
  };
  /* 播放速度面板照 YouTube delhi-modern（player 9470c977 的 base.js）：滑条两端取播放器
     支持的最低与最高倍速，步进 0.05，加减键各动 0.05 并按两位小数收敛，读数写成 1.00x。
     预设胶囊点了就地生效，面板不退回上一级。第五格 3.0 在上游是 Premium 专属，本机装的
     Peach 没有会员分级这回事，那一格照上游留着，只是不画角标；滑条上限跟着抬到 3，
     不然点 3.0 会被收敛回 2。 */
  const SPEED_RATES=[.25,.5,.75,1,1.25,1.5,1.75,2,3],SPEED_STEP=.05,SPEED_PRESETS=[1,1.25,1.5,2,3];
  const speedLabel=speed=>Number.isInteger(speed)?speed.toFixed(1):String(speed);
  const showSpeed=(direction=1)=>{
    const min=SPEED_RATES[0],max=SPEED_RATES[SPEED_RATES.length-1];
    const clampSpeed=value=>Math.min(max,Math.max(min,Number(value.toFixed(2))));
    const panel=renderPanel(`<div class="vjs-peach-panel-header"><button type="button" class="vjs-peach-menu-back" data-player-menu-back aria-label="返回上一个菜单">${icon('player-menu-back')}</button><strong>播放速度</strong></div>
      <div class="vjs-peach-speed-panel"><div class="vjs-peach-speed-display"><output data-player-speed-display></output></div>
      <div class="vjs-peach-speed-slider"><button type="button" class="vjs-peach-speed-button" data-player-speed-step="-1" aria-label="播放速度减 0.05">−</button>
      <input type="range" class="vjs-peach-speed-range" data-player-speed-range min="${min}" max="${max}" step="${SPEED_STEP}" aria-label="播放速度">
      <button type="button" class="vjs-peach-speed-button" data-player-speed-step="1" aria-label="播放速度加 0.05">+</button></div>
      <div class="vjs-peach-speed-chips">${SPEED_PRESETS.map(speed=>
        `<span class="vjs-peach-speed-preset"><button type="button" class="vjs-peach-speed-button" data-player-speed-option="${speed}" aria-pressed="false">${speedLabel(speed)}</button>${speed===1?'<span class="vjs-peach-speed-preset-label">正常</span>':''}</span>`).join('')}</div></div>`,direction);
    const display=panel.querySelector('[data-player-speed-display]'),range=panel.querySelector('[data-player-speed-range]');
    // player.playbackRate() 读的是 ratechange 之后才写的缓存，面板自己记住这一次的倍速。
    let rate=clampSpeed(Number(player.playbackRate())||1);
    const syncSpeed=()=>{
      display.textContent=`${rate.toFixed(2)}x`;range.value=String(rate);
      range.style.setProperty('--peach-speed-percent',`${(rate-min)/(max-min)*100}%`);
      panel.querySelectorAll('[data-player-speed-option]').forEach(button=>
        button.setAttribute('aria-pressed',String(Number(button.dataset.playerSpeedOption)===rate)));
    };
    const setSpeed=value=>{rate=clampSpeed(value);player.playbackRate(rate);syncSpeed()};
    panel.querySelector('[data-player-menu-back]').onclick=()=>showMain(-1);
    range.oninput=()=>setSpeed(Number(range.value));
    panel.querySelectorAll('[data-player-speed-step]').forEach(button=>button.onclick=()=>
      setSpeed(rate+Number(button.dataset.playerSpeedStep)*SPEED_STEP));
    panel.querySelectorAll('[data-player-speed-option]').forEach(button=>button.onclick=()=>
      setSpeed(Number(button.dataset.playerSpeedOption)));
    syncSpeed();
  };
  const showQuality=(direction=1)=>{
    const {options}=qualityRows();
    const panel=renderPanel(`<div class="vjs-peach-panel-header"><button type="button" class="vjs-peach-menu-back" data-player-menu-back aria-label="返回上一个菜单">${icon('player-menu-back')}</button><strong>清晰度</strong></div><div class="vjs-peach-panel-menu">${options.map(option=>
      `<button type="button" class="vjs-peach-menu-option" role="menuitemradio" data-player-quality-option="${esc(option.key)}" aria-checked="${option.key===selectedQuality}"><span class="vjs-peach-option-check">${option.key===selectedQuality?icon('player-option-check'):''}</span><span class="vjs-peach-option-label">${esc(option.label)}</span></button>`).join('')}</div>`,direction);
    panel.querySelector('[data-player-menu-back]').onclick=()=>showMain(-1);
    panel.querySelectorAll('[data-player-quality-option]').forEach(button=>button.onclick=()=>{
      selectedQuality=button.dataset.playerQualityOption;
      if(levels?.length)for(let index=0;index<levels.length;index++)levels[index].enabled=selectedQuality==='auto'||selectedQuality===String(index);
      /* 来源档位是四个各自独立的 mp4，不是同一条流的多个轨道，所以只能换 src。
         记住当前进度和播放状态再换：换源会重新加载，不接回去就等于从头开始。 */
      if(sourceQualities?.length&&selectedQuality.startsWith('h')){
        const height=selectedQuality.slice(1);
        const at=player.currentTime()||0,wasPlaying=!player.paused();
        const next=new URL(player.currentSrc()||video.src,location.origin);
        next.searchParams.set('quality',height);
        player.src({src:next.pathname+next.search,type:'video/mp4'});
        player.one('loadedmetadata',()=>{
          if(at>0)player.currentTime(at);
          if(wasPlaying)player.play().catch(()=>{});
        });
      }
      showMain(-1);
    });
  };
  toggle.onclick=event=>{event.stopPropagation();const open=!isOpen();if(open)showMain();setOpen(open)};
  const outside=event=>{if(!root.contains(event.target))close()};document.addEventListener('pointerdown',outside);
  root.addEventListener('keydown',event=>{if(event.key==='Escape'){close();toggle.focus()}});
  video.addEventListener('loadedmetadata',()=>{if(isOpen())showMain();else qualityRows()});
  levels?.on?.(['addqualitylevel','removequalitylevel'],()=>{if(isOpen())showMain();else qualityRows()});
  player.on('dispose',()=>{document.removeEventListener('pointerdown',outside);
    document.removeEventListener(PLAYER_PANEL_EVENT,closeSettingsForOtherPanel);
    if(panelTimer)clearTimeout(panelTimer)});qualityRows();
  mountPlayerTheaterControl(player,root);
  mountPlayerChromeLayout(player);
  return next=>{sourceQualities=next?.length?next:null;if(isOpen())showMain();else qualityRows()};
}
function mountPlayerTheaterControl(player,settingsRoot){
  const controlBar=player.getChild('controlBar')?.el();if(!controlBar||controlBar.querySelector('[data-player-theater]'))return;
  const root=document.createElement('div');root.className='vjs-peach-theater vjs-control';
  root.innerHTML=`<button type="button" data-player-theater aria-pressed="${appSettings.theaterMode}">${icon(appSettings.theaterMode?'theater-exit':'theater-enter')}</button>`;
  controlBar.insertBefore(root,settingsRoot.nextSibling);
  const theaterButton=root.querySelector('button');
  theaterButton.peachTooltipSync=playerControlTooltip(theaterButton,'影院模式','T');
  syncPlayerTheaterButton(theaterButton);
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
  /* 播放键和静音键的图标要自己形变，不能整块换掉：`<use>` 克隆出来的是影子树，里面的
     `d` 改不动，也挂不上过渡。所以这两个键把 sprite 里的 <path> 搬进自己的 svg，图标怎么变
     由 CSS 说。照 YouTube delhi-modern（player 9470c977 的 base.js）：播放↔暂停是同一条
     路径逐个数字插值 200ms（上游 `eST` 把 `d` 拆成数字与分隔符再逐位插值），音量的两道弧
     各自缩放 250ms（上游 `jjc`：内弧绕 (18,12)、外弧绕 (22,12)），两处曲线都是 `qn3`
     也就是 cubic-bezier(.4,0,.2,1)。 */
  const morphIcon=(button,name)=>{
    if(!button)return null;
    const symbol=document.getElementById(`i-${name}`);if(!symbol)return null;
    button.dataset.peachExplicitIcon='';
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox',symbol.getAttribute('viewBox'));
    svg.setAttribute('aria-hidden','true');
    svg.setAttribute('class','vjs-peach-control-icon vjs-peach-morph-icon');
    svg.innerHTML=symbol.innerHTML;button.append(svg);return svg;
  };
  const spritePaths=name=>[...(document.getElementById(`i-${name}`)?.querySelectorAll('path')||[])];
  const playIcon=morphIcon(play,'player-play'),playPath=playIcon?.querySelector('path');
  const playD=spritePaths('player-play')[0]?.getAttribute('d')||'',pauseD=spritePaths('player-pause')[0]?.getAttribute('d')||'';
  const syncPlayTooltip=playerControlTooltip(play,'播放','K');
  const syncPlayIcon=()=>{const paused=player.paused()||player.ended();
    if(playPath)playPath.style.d=`path("${paused?playD:pauseD}")`;
    syncPlayTooltip(paused?'播放':'暂停')};
  player.on(['play','pause','ended'],syncPlayIcon);syncPlayIcon();
  const volume=controlBar.querySelector(':scope>.vjs-volume-panel');
  const mute=volume?.querySelector(':scope>.vjs-mute-control'),muteIcon=morphIcon(mute,'player-volume');
  /* 静音那张图标搬进同一个 svg：挖空的喇叭和叉号跟实心喇叭、两道弧共处一处，弧缩完了
     它们才一起顶上，靠 opacity 换而不是换整块 svg。 */
  if(muteIcon)spritePaths('player-volume-muted').forEach(path=>muteIcon.append(path.cloneNode(true)));
  const syncMuteTooltip=playerControlTooltip(mute,'静音','M');
  /* 外弧跟音量走：上游 `setVolume` 里超过 50 才给 1，否则 0，静音时两道弧一起收掉。 */
  const syncVolumeIcon=()=>{const silent=player.muted()||player.volume()===0;
    if(muteIcon){muteIcon.dataset.silent=String(silent);muteIcon.dataset.loud=String(!silent&&player.volume()>.5)}
    syncMuteTooltip(silent?'取消静音':'静音')};
  player.on('volumechange',syncVolumeIcon);syncVolumeIcon();
  /* 中心提示照 YouTube delhi-modern（player 9470c977 的 www-player.css 与 base.js）：一块
     78px 的毛玻璃圆闪一下当前动作的图标，1s 走完 0→1.33→1 的缩放淡出。捕获阶段读的是
     切换之前的状态，闪出来的正好是这一次做的事：暂停中点播放键闪播放。键盘快捷键走的
     也是同一个按钮的点击路径，所以只挂控制条这一处。 */
  const bezel=document.createElement('div');
  bezel.className='vjs-peach-bezel';bezel.setAttribute('role','status');bezel.hidden=true;
  bezel.innerHTML=`<span class="vjs-peach-bezel-icon">${icon('player-play')}</span>`;
  const bezelUse=bezel.querySelector('use');let bezelTimer=null;
  const flashBezel=(name,label)=>{
    bezelUse.setAttribute('href',`#i-${name}`);bezel.setAttribute('aria-label',label);
    bezel.hidden=false;bezel.classList.remove('vjs-peach-bezel-run');
    void bezel.offsetWidth;bezel.classList.add('vjs-peach-bezel-run');
    if(bezelTimer)clearTimeout(bezelTimer);
    bezelTimer=setTimeout(()=>{bezel.hidden=true;bezel.classList.remove('vjs-peach-bezel-run')},1000);
  };
  player.el().insertBefore(bezel,controlBar);
  controlBar.addEventListener('click',event=>{
    if(event.target.closest('.vjs-play-control')){
      const paused=player.paused()||player.ended();
      flashBezel(paused?'player-play':'player-pause',paused?'播放':'暂停');
    }else if(event.target.closest('.vjs-mute-control')){
      const silent=player.muted()||player.volume()===0;
      flashBezel(silent?'player-volume':'player-volume-muted',silent?'取消静音':'静音');
    }
  },true);
  player.on('dispose',()=>{if(bezelTimer)clearTimeout(bezelTimer)});
  const time=document.createElement('button');let remaining=false;
  time.type='button';time.className='vjs-peach-time vjs-control';time.dataset.playerTime='';
  time.innerHTML='<span class="vjs-peach-time-text"></span>';
  const timeText=time.querySelector('.vjs-peach-time-text');
  const syncTimeTooltip=playerControlTooltip(time,'显示剩余时间');
  const syncTime=()=>{
    const current=Math.max(0,Number(player.currentTime())||0),duration=Math.max(0,Number(player.duration())||0);
    const shown=remaining?`-${fmtClock(Math.max(0,duration-current))}`:fmtClock(current);
    timeText.textContent=`${shown} / ${fmtClock(duration)}`;
    time.dataset.remaining=String(remaining);
    syncTimeTooltip(remaining?'显示已播放时间':'显示剩余时间',remaining?`剩余 ${fmtClock(Math.max(0,duration-current))}，总时长 ${fmtClock(duration)}；点击显示已播放时间`:`已播放 ${fmtClock(current)}，总时长 ${fmtClock(duration)}；点击显示剩余时间`);
  };
  time.onclick=event=>{event.stopPropagation();remaining=!remaining;syncTime()};
  player.on(['timeupdate','durationchange','loadedmetadata'],syncTime);syncTime();
  if(volume)volume.insertAdjacentElement('afterend',time);else controlBar.append(time);
  const pip=controlBar.querySelector(':scope>.vjs-picture-in-picture-control');
  explicitIcon(pip,'player-pip');
  const syncPipTooltip=playerControlTooltip(pip,'画中画','I');
  player.on(['enterpictureinpicture','leavepictureinpicture'],()=>syncPipTooltip(document.pictureInPictureElement?'退出画中画':'画中画'));
  const fullscreen=controlBar.querySelector(':scope>.vjs-fullscreen-control');
  const fullscreenUse=explicitIcon(fullscreen,'player-fullscreen-enter');
  const syncFullscreenTooltip=playerControlTooltip(fullscreen,'全屏','F');
  /* CSS 的 `.vjs-fullscreen` 只能覆盖 Video.js 已经同步状态类的路径。实际浏览器还可能
     走 full-window 回退，或者先触发 fullscreenchange、下一帧才完成 class 更新。把播放器
     自己的 `isFullscreen()` 结果登记到 DOM，画面填充不再依赖某一个实现细节类名。 */
  const syncFullscreenState=()=>{
    const active=!!player.isFullscreen();
    player.el().toggleAttribute('data-peach-fullscreen',active);
    fullscreenUse?.setAttribute('href',active?'#i-player-fullscreen-exit':'#i-player-fullscreen-enter');
    syncFullscreenTooltip(active?'退出全屏':'全屏');
    requestAnimationFrame(()=>player.trigger('resize'));
  };
  player.on(['fullscreenchange','enterFullWindow','exitFullWindow'],syncFullscreenState);
  syncFullscreenState();
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
  /* 窄屏折叠照 YouTube 的判据来：base.js 9470c977 里播放器宽度 `v.width<528` 打开
     ytp-xsmall-width-mode，右侧收成「设置 + 展开」，点开才铺开其余按钮。判据必须是播放器
     自己的宽度，不是视口——同一个视口下影院模式和普通视图的播放器宽度差一大截。 */
  const expand=document.createElement('div');expand.className='vjs-peach-expand vjs-control';
  /* 高亮层要挂在 `.vjs-control` 这一层：亮起来的规则是 `>.vjs-peach-hover`，塞进
     button 里就差一层，展开键成了这排唯一没有 hover 的按钮。位置在这排左端——
     这排整体右对齐，展开时新按钮从它右边长出来，箭头指左才对得上要发生的事。箭头用
     `i-player-expand`：菜单行那个 `>` 是 24 视框、一个单位粗的细线，铺到 32px 只有 1.3px 粗；
     上游展开键自带一个 32 视框、两个单位粗的箭头，同样 32px 渲染就是 2px。 */
  expand.innerHTML=`<button type="button" data-player-expand aria-expanded="false">${icon('player-expand')}</button><span class="vjs-peach-hover" aria-hidden="true"></span>`;
  group.prepend(expand);
  const expandButton=expand.querySelector('button');
  const syncExpandTooltip=playerControlTooltip(expandButton,'展开控件');
  const setExpanded=open=>{
    player.el().classList.toggle('vjs-peach-right-expanded',open);
    expandButton.setAttribute('aria-expanded',String(open));syncExpandTooltip(open?'收起控件':'展开控件');
  };
  expandButton.onclick=event=>{event.stopPropagation();setExpanded(!player.el().classList.contains('vjs-peach-right-expanded'))};
  const syncWidthMode=()=>{
    const box=player.el(),narrow=box.clientWidth<528;
    /* 设置面板要按播放器高度收顶，而它的定位祖先只有 36px 高，百分比取不到播放器。 */
    box.style.setProperty('--peach-player-h',`${box.clientHeight}px`);
    box.classList.toggle('vjs-peach-xsmall',narrow);
    if(!narrow)setExpanded(false);
  };
  const widthObserver=new ResizeObserver(syncWidthMode);widthObserver.observe(player.el());
  player.on('dispose',()=>widthObserver.disconnect());
  setExpanded(false);syncWidthMode();
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
    const duration=realDuration(player.duration())||realDuration(it.duration);
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
/* 播放器按需加载，和灯箱的 Swiper 同一个理由：video.js 676KB，只有真的开始看片才
   用得上，进首屏就是每次开页都白下一遍。灯箱那边还要等一张样式表，所以它保留自己的
   Promise.all；这里只有脚本，用下面这个最小加载器。主脚本与语言包有依赖
   ——`videojs.addLanguage` 得先有 videojs——必须串行，不能 Promise.all。 */
const loadScript=src=>new Promise((resolve,reject)=>{
  const script=document.createElement('script');
  script.src=src;script.onload=resolve;
  script.onerror=()=>reject(new Error(`script unavailable: ${src}`));
  document.head.appendChild(script)});
let videojsLoader=null;
const ensureVideojs=()=>{
  if(globalThis.videojs)return Promise.resolve(globalThis.videojs);
  return videojsLoader||(videojsLoader=loadScript('/vendor/videojs/8.24.0/video.min.js')
    .then(()=>loadScript('/vendor/videojs/8.24.0/lang/zh-CN.js'))
    .then(()=>globalThis.videojs)
    /* 失败要把 loader 清空，否则一次网络抖动之后这一整页都再也挂不上播放器了。 */
    .catch(error=>{videojsLoader=null;throw error}));
};
async function mountDetailPlayer(it,video,autoplay,options={}){
  if(detailPlayer)return detailPlayer;
  const statsButton=$('#playerStatsBtn'),statsPanel=$('#playerStats');
  const source=()=>options.source?Promise.resolve(options.source):detailStreamSource(it);
  /* 拉不到就退回原生 video，和「页面里没有 videojs」是同一个兜底出口。 */
  try{await ensureVideojs()}
  catch(_e){
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
  // 非正时长一律当未知：强行 player.duration(-1) 会被 Video.js 转成 Infinity 并标成直播。
  const expected=realDuration(it.duration);
  const statsHistory={speed:[],activity:[],buffer:[]};
  const meter=createBufferMeter(averageBitrate(options.size??it.size,it.duration));
  let statsLoaded=0;
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
     const segmented=String(detailPlayer.currentSource()?.type||'').includes('mpegurl');
      const resources=segmented?streamEntries(it.id,detailStreamSession):[];
      const bytes=resources.reduce((n,x)=>n+(x.transferSize||x.encodedBodySize||0),0);
      const seconds=resources.reduce((n,x)=>n+(x.duration||0),0)/1000;
     meter.sample(video);
      const speed=playerSpeedBits(detailPlayer,it.id,detailStreamSession,segmented?null:meter)
        ||(seconds>0?bytes*8/seconds:0);
     /* 分片流按已完成请求的字节累计；渐进源没有这种请求，按前沿推进折算，码率未知时退到秒。 */
     const loaded=segmented?bytes:(meter.bitrate>0?meter.bytes():meter.seconds);
     const activity=Math.max(0,loaded-statsLoaded);statsLoaded=loaded;
     const buffer=bufferedAhead(video);
     pushPlayerStat(statsHistory.speed,speed);
     pushPlayerStat(statsHistory.activity,activity);
     pushPlayerStat(statsHistory.buffer,buffer);
     /* 关注条目没有落盘文件名，容器格式只能从片源 MIME 反推；HLS 已经写在传输一侧，不重复。 */
     const named=String(it.name||'');
     const container=(named.includes('.')?named.split('.').pop()
       :segmented?'':String(detailPlayer.currentSource()?.type||'').split('/').pop()).toUpperCase()||'—';
     const speedText=speed?`${(speed/1e6).toFixed(1)} Mbps`
       :(!segmented&&meter.ratio>0?`${meter.ratio.toFixed(1)}× 实时`:'—');
     const byteScale=segmented||meter.bitrate>0;
     const loadedRow=segmented
       ?['网络活动',`${bytes?fmtSize(bytes):'—'} · ${resources.length} 请求`,
         `最近一秒网络活动 ${activity?fmtSize(activity):'0 B'}`]
       :['已下载',byteScale?`${fmtSize(loaded)}${Number(it.size)>0?` / ${fmtSize(Number(it.size))}`:''}`
           :`${loaded.toFixed(0)} 秒`,
         byteScale?`最近一秒下载 ${activity?fmtSize(activity):'0 B'}`
           :`最近一秒下载 ${activity.toFixed(1)} 秒`];
     const rows=[
      ['视频 ID / 会话',detailStreamSession&&!options.source?`${it.id} / ${detailStreamSession.slice(0,8)}`:`${it.id}`],
      ['视口 / 帧',`${Math.round(rect.width)}×${Math.round(rect.height)} / ${quality?`${quality.totalVideoFrames-quality.droppedVideoFrames} of ${quality.totalVideoFrames}`:'—'}`],
      ['当前 / 最佳分辨率',`${current} / ${it.width||video.videoWidth||'?'}×${it.height||video.videoHeight||'?'}`],
       ['编码 / 传输',`${container} / ${segmented?'HLS':'HTTP Range'}`],
      ['连接速度',speedText,
        playerStatsPlot(statsHistory.speed,'speed',Math.max(10e6,...statsHistory.speed),`连接速度 ${speedText==='—'?'暂无数据':speedText}`)],
      [loadedRow[0],loadedRow[1],
        playerStatsPlot(statsHistory.activity,'activity',Math.max(1,...statsHistory.activity),loadedRow[2])],
      ['缓冲健康',`${buffer.toFixed(1)} 秒`,
        playerStatsPlot(statsHistory.buffer,'buffer',30,`当前可连续播放 ${buffer.toFixed(1)} 秒`)],
      ['播放时间',`${fmtClock(video.currentTime)} / ${fmtClock(expected||detailPlayer.duration())}`],
      ['日期',new Date().toLocaleString()],
    ];
    statsPanel.innerHTML='<dl>'+rows.map(([k,v,plot])=>`<dt>${esc(k)}</dt><dd${plot?' class="playerstatsmetric"':''}>${plot||''}<span>${esc(v)}</span></dd>`).join('')+'</dl>';
  };
  detailPlayer.on(['loadstart','loadedmetadata','durationchange','error'],enforceDuration);
  const player=detailPlayer;
  let segmentedSource=false,fallbackUsed=false;
  const netBadge=$('#playerNet');
  const updateNet=()=>{if(!netBadge||player.isDisposed())return;
    const segmented=String(player.currentSource()?.type||'').includes('mpegurl');
    if(!segmented)meter.sample(video);
    const bits=playerSpeedBits(player,it.id,detailStreamSession,segmented?null:meter);
    const rate=segmented?fmtSpeed(bits):fmtLoadRate(bits,meter.ratio);
    netBadge.innerHTML=`${icon('gauge')}<span class="sr-only">加载速度</span><span>${esc(rate)}</span>`};
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
    enforceDuration();
    const updateQualities=mountPlayerQualityControl(detailPlayer,video,it.height,options.qualities);
    options.qualitiesPromise?.then(next=>{
      if(detailPlayer===player&&!player.isDisposed())updateQualities?.(next)
    }).catch(()=>{});
    mountPlayerSeekPreview(detailPlayer,it,{thumbnail:!options.source});
    mountPlayerCenterControls(detailPlayer);
    if(statsButton)statsButton.hidden=false
  });
  if(statsButton&&statsPanel){
    const closeStats=()=>{
      if(statsPanel.hidden)return;
      statsPanel.hidden=true;statsButton.setAttribute('aria-pressed','false');
      if(detailStatsTimer){clearInterval(detailStatsTimer);detailStatsTimer=null}
    };
    statsButton.onclick=()=>{
      if(!statsPanel.hidden){closeStats();return}
      document.dispatchEvent(new CustomEvent(PLAYER_PANEL_EVENT,{detail:'stats'}));
      statsPanel.hidden=false;statsButton.setAttribute('aria-pressed','true');
      updateStats();if(detailStatsTimer)clearInterval(detailStatsTimer);detailStatsTimer=setInterval(updateStats,1000);
    };
    const closeStatsForOtherPanel=event=>{if(event.detail!=='stats')closeStats()};
    document.addEventListener(PLAYER_PANEL_EVENT,closeStatsForOtherPanel);
    detailPlayer.on('dispose',()=>document.removeEventListener(PLAYER_PANEL_EVENT,closeStatsForOtherPanel));
  }
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
    setSelectMode(false,true);await reloadCurrentSurface();
    const inverse=operation==='dispose'?'restore':operation==='restore'?'dispose':null;
    actionReceipt(`已${labels[operation]} ${ids.length} 项`,{undo:inverse?async()=>{
      await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation:inverse})});
      await reloadCurrentSurface();
    }:null})}
  catch(error){actionFailure('批量操作',error)}
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
    setSelectMode(false,true);await openFollow(false);actionReceipt(`已${labels[action]} ${items.length} 项`);
  }catch(error){actionFailure('批量操作',error)}
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
    const inverse=operation==='dispose'?'restore':operation==='dismiss-junk'?'reconsider-junk':
      operation==='reconsider-junk'?'dismiss-junk':null;
    actionReceipt(`已批量${labels[operation]}：${ids.length} 项`,{undo:inverse?async()=>{
      await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation:inverse})});
      await load(true);
    }:null});
  }catch(error){actionFailure('批量操作',error)}
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
  // 远端源那一层和视频同样要兜一遍：卡片被重画过的话，旧元素上的 `_stopHover`
  // 已经跟着旧 DOM 走了，只靠上面那轮回调收不到它留在画面上的扫视图。
  root.querySelectorAll('img.hvframes').forEach(im=>{
    if(im.closest('.card')===except)return;
    im.removeAttribute('src');im.remove()});
}
function wireHover(el,it){
  const pic=el.querySelector('.pic'); if(!pic)return;
  el.dataset.hoverMode=it.location==='local'?'video':'frames';
  let longTimer=null;
  const armLong=()=>{clearTimeout(longTimer);el.classList.add('previewing');longTimer=setTimeout(()=>el.classList.add('longhover'),Math.max(1,appSettings.hoverDelaySeconds)*1000)};
  const clearLong=()=>{clearTimeout(longTimer);el.classList.remove('previewing','longhover')};
  if(it.location!=='local'){        // 远端源：只在接触印相的格子间扫视，零网络流量
    /* 扫视图是叠在画面之上新建的一层，不改任何已有 `<img>` 的 src。JAV 大图和小图
       版式里画面就是封面本身（`.poster.cover`），改它的 src 等于把封面当场换掉；
       按类名把封面排掉又等于这两种版式整个没有悬停预览，连 `.longhover` 都不进，
       快退快进那三颗也跟着永远不出现。叠一层对三种版式是同一条路。
       这一层用 contain 加黑底：大图版式的容器是 0.7 的竖比例，16:9 的接触印相格子
       在里面居中、上下留黑，和本地视频的 `.hv` 同一个口径。 */
    if(!it.has_thumb)return;        // 没有接触印相就没有可扫的格子
    let t=null,i=4,layer=null;
    el.addEventListener('mouseenter',()=>{
      if(selectMode||censorOn())return;armLong();
      if(!layer){
        layer=document.createElement('img');
        layer.className='hvframes';layer.alt='';
        layer.src=`/poster?id=${it.id}&c=${i}`;
        pic.appendChild(layer);
      }
      clearInterval(t);
      t=setInterval(()=>{i=(i+1)%9;layer.src=`/poster?id=${it.id}&c=${i}`},430);
    });
    const stop=()=>{clearLong();clearInterval(t);t=null;
      if(layer){layer.remove();layer=null}i=4};
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

/* 实体那张脸：规范实体图优先，取不到退到代表作头像，两样都取不到就一个 `<img>`
   都不出。四个位置（顶栏圆头像、卡片署名、共演者、资料页大位）共用这一份。

   无条件出图、等 404 再把图摘掉的代价是：一个作品详情页 9 个这样的 404（1 个厂牌
   实体图、4 个人物实体图、4 个头像），首页手机视口 2 个；`/entity-image` 与
   `/avatar` 的 404 都不带缓存头，每次重绘再打一整轮。`hasImage` 由 `/api/tops`、
   `/api/items`、`/api/item`、`/api/entity` 随资料下发，判据和取图同一个函数。

   `rep` 这一侧不带标志：调用方传进来的就该是「取得到的代表作」（顶栏在入 REP 表时
   已经筛过）。`/avatar` 是按需生成的，还没裁过但印相还在也算取得到——那条点一下就
   有的路不能一起关掉。

   兜底链最后一环必须真的把 `<img>` 拿掉（`data-drop="self"`）：留着取不到图的
   `<img>`，`:has(img)` 仍然匹配，首字母垫底回不来，浏览器还会把 alt 画出来。 */
function entityFaceImg({kind='performer',id=null,hasImage=false,rep=null,mark=null,logo='',
                        logoVariant='logo',alt='',lazy=true,style='',dropStyle=false}={}){
  const useEntity=!!(id&&hasImage);
  const entitySrc=useEntity?`/entity-image?kind=${kind}&id=${id}`:'';
  // `rep` 由服务端的 has_avatar 决定有没有值，没有就不出这一环。
  const avatarSrc=rep?`/avatar?id=${rep}`:'';
  /* 公司的门面是它自己的标识，不是作品截图——那是某部片的画面，说的是别人的事。
     厂牌走 `/logo`：`logo` 只在调用方问过 `has_logo` 时才有值。变体跟着位置走，
     大位要字标、小位要方形图标。事务所没有标识文件，走官网那条链接的站点圆标 `mark`。 */
  const useLogo=!!logo;
  const src=useLogo?`/logo?studio=${encodeURIComponent(logo)}&variant=${logoVariant}`
    :(entitySrc||avatarSrc||(mark?`/link-mark?id=${mark}`:''));
  if(!src)return '';
  const fallbacks=useLogo?[entitySrc,avatarSrc].filter(Boolean)
    :(useEntity&&avatarSrc?[avatarSrc]:[]);
  // 人脸取景是按实体图算出来的，回落图是另一张照片，脸不在同一位置：只贴给第一环。
  const framed=useEntity&&!useLogo;
  return `<img src="${src}" alt="${alt}"${lazy?' loading="lazy"':''}${framed?style:''} `+
    `${imageFallbackAttrs({dropStyle:dropStyle&&framed,fallbacks})}>`;
}
/* 头像内层：先垫首字母，再叠真实图。

   `has_image` 缺席按「没图」处理，和 entityFaceImg 的默认值一致：每一个调用点的
   ref 都由服务端带着标志下发（卡片署名、索引页、口味榜、复核卡片、沉浸模式），
   宽容缺席只会让下一个忘了挂标志的端点悄悄退回「无条件出图、等 404 再摘」。 */
function avatarInner(name,ref,repId,kind='performer',markId=null,logoName=''){
  // 这一层全是小圆框和窄格子，厂牌标识在这里要方形图标而不是横着的字标。
  return `<span class="ini">${esc((name||'?').slice(0,1))}</span>`+
    entityFaceImg({kind,id:ref&&ref.id,hasImage:!!(ref&&ref.has_image),rep:repId,mark:markId,
                   logo:logoName,logoVariant:'icon'});
}
/* 人脸取景：资料页圆框按检出的人脸中心取景（/api/entity 的 avatar_focus）。
   没检出或没算过返回空串维持几何居中；换回落图时必须撤掉——那是另一张照片，
   脸不在同一位置，见 entityhero img 的 `data-drop-style`。 */
/* 换算只有这一份。资料页把它写进 img 的 style；索引页大图版式要把它交给圆框上的
   CSS 变量——那里的 img 由共用的 avatarInner 拼，版式能改的容器只有圆框。 */
function faceOrigin(f){
  return f&&f.axis==='x'?`${f.pct}% 50%`
    :f&&f.axis==='y'?`50% ${f.pct}%`
    :'';
}
function facePos(f){
  const origin=faceOrigin(f);
  return origin?` style="object-position:${origin}"`:'';
}
/* 官方封面有三种形态，实测过：整张封套约 1.48（左侧是剧照拼贴，右侧才是正封），
   竖版正封约 0.70（本身就是正封，没有左半边可裁），16:9 官方剧照约 1.78（整幅
   都是画面，没有「正封那一块」可推）。所以取景不能写死「取右边」，得等图片加载后
   按它自己的宽高比分流——服务端没存这个比例，也不该为此再存一份。
   剧照必须自成一档：把 1.78 归进 front 就会按写死的 50% 取横向中段，人偏在一侧
   就整个被切掉，而大图容器比所有封面都竖、纵向锚点在那里根本不生效。 */
function coverAnchor(img){
  const r=img.naturalWidth/img.naturalHeight;
  if(!r)return;
  img.dataset.frame=r>=1.65?'still':r>1.2?'sleeve':'front';
  /* `object-position` 的百分比说的是「图片上这个点对齐可见窗口的同一个百分比位置」，
     不是「这个点落到窗口正中」。所以人脸中心原样当锚点只能保证脸还在画面里：0.81
     那种偏右的脸会贴着窗口右缘，图片右边还剩一截永远露不出来。可见窗口占图片 w 时，
     让人脸落到正中的锚点是 (face - w/2) / (1 - w)。夹回 0–1 是因为脸离图片边缘不足
     半个窗口时窗口已经顶到边，再往外推只会把图片外面推进来。 */
  const car=coverRatio(img);
  const center=(name,face,visible)=>{
    // 只给被裁的那个轴算。`object-fit:cover` 一次只裁一个轴，另一个轴整幅可见
    // （visible>=1），那里的 object-position 是死值，算了也不生效。
    if(face==null||!(visible>0&&visible<1))return;
    const pct=Math.min(1,Math.max(0,(face-visible/2)/(1-visible)));
    img.style.setProperty(name,`${Math.round(pct*100)}%`);
  };
  center('--cover-x',coverFace(img,'cx'),car/r);
  center('--cover-y',coverFace(img,'cy'),r/car);
}
/* 容器比例只有 `.pic` 的 `--card-ratio` 知道：竖屏开关、JAV 大图和普通卡片各写一个
   值，在这里按 layout 重算迟早会和它分叉。自定义属性会继承，直接从图片上读；
   `aspect-ratio` 允许 `16/9` 这种写法，所以两种形式都得认。 */
function coverRatio(img){
  const parts=getComputedStyle(img).getPropertyValue('--card-ratio').trim().split('/').map(Number);
  const r=parts.length===2?parts[0]/parts[1]:parts[0];
  return Number.isFinite(r)&&r>0?r:16/9;
}
function coverFace(img,axis){
  const face=parseFloat(img.dataset[axis]);
  return Number.isFinite(face)?face:null;
}
/* 封面是模板字符串拼出来的，没法逐张挂监听；内联 `onload` 属性只能调全局函数，而
   app.js 以 `type="module"` 加载，取景函数在那里取不到——页面会每张图报一次
   ReferenceError，封面全部按回落取景。`load` 不冒泡，但捕获阶段照样收得到。 */
document.addEventListener('load',event=>{
  const img=event.target;
  if(img instanceof HTMLImageElement&&img.classList.contains('cover'))coverAnchor(img);
},true);
/* 整张封套里右侧正封占的宽高比。裁切靠的是容器比例而不是 CSS 裁剪：`object-fit:cover`
   只在容器比图片更「竖」时才会横向裁；容器一旦宽过 1.48 就变成纵向裁、整张封套原样
   铺满，「大图」于是只撑满画布而取不到右侧。 */
const COVER_FRONT_RATIO=0.7;
/* 竖屏一律用同一个比例，不按每条视频的实际宽高。竖屏素材从 0.5 到 0.9 都有，
   按各自比例渲染会让竖屏条和竖屏网格高低不齐；比例不同的用 contain 上下留黑边
   （`.poster` 本来就是 contain + 黑底）。 */
const PORTRAIT_RATIO=9/16;
function coverImage(it,layout,eager){
  const src=`/cover?code=${encodeURIComponent(it.code||'')}`;
  // 人脸位置原样交给页面，锚点由 `coverAnchor` 在加载后算：哪个轴被裁、要推多远，
  // 只有同时拿到图片和容器的比例才知道。人物在画面里的位置差别很大，写死的锚点会把
  // 一部分作品裁掉下巴或整个切出画外；取不到人脸就退回固定取景。
  const f=it.cover_frame||{};
  // 纵向夹在 5%–60%：脸不会长在图片下半截，落在那儿是检出跑偏而不是构图。
  const face=[f.cx!=null?` data-cx="${f.cx}"`:'',
    f.cy!=null?` data-cy="${Math.min(0.6,Math.max(0.05,f.cy))}"`:''].join('');
  // 小图看整张（含剧照拼贴），大图只取右侧正封。
  return `<img class="poster cover ${layout==='small'?'whole':'front'}" src="${src}"
    alt="" loading="${eager?'eager':'lazy'}"${face} data-drop="self">`;
}
/* 卡片署名。版次队列要和「接着看」长得一样，就必须用同一份身份推导——各算各的
   迟早会在同名 creator/performer 那 35 组上分叉，同一条作品在两处指向两个实体。
   `linked=false` 给队列用：整行本身就是一个 <button>，里面再嵌 <button> 会被
   浏览器就地拆散，头像和标题会被甩到行外面去。 */
function cardIdentity(it,linked=true){
  const link=(cls,attrs,inner)=>linked
    ? `<button class="${cls} entitylink" ${attrs}>${inner}</button>`
    : `<span class="${cls}">${inner}</span>`;
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
  // 共演作品用头像提示多人，但文字只保留第一位，再给总人数。两个长名字加元数据
  // 会在普通卡片里折成三行；「第一位 + 等 N 人」仍能说明身份与规模。
  const coStarred=performers.length>1&&!primaryCreator;
  const avatar=coStarred
    ? `<div class="mavstack">${performers.slice(0,3)
        .map((nm,i)=>link('mav',`data-entity-kind="performer" data-entity-name="${esc(nm)}" title="打开${esc(performerLabel(it))}页：${esc(nm)}"`,avatarInner(nm,performerRefs[i],REP[nm])))
        .join('')}</div>`
    : (()=>{
        /* 头像和名字必须落到同一个身份。各自挑 kind（头像先看 performer、名字先看
           creator）时，同名的 creator/performer 重复实体（账本里有 35 组）会一个跳
           `/performers/x`、另一个跳 `/creators/x`，同一张卡上两个入口去两个地方。 */
        const avatarKind=identity.kind||(performer?'performer':(primaryCreator?'creator':(it.studio?'studio':'')));
        const avatarName=identity.kind?identity.name:(performer||primaryCreator||it.studio||who);
        const inner=avatarInner(avatarName,performerRef,REP[avatarName]||REP[it.creator]||REP[it.studio]);
        return avatarKind
          ? link('mav',`data-entity-kind="${avatarKind}" data-entity-name="${esc(avatarName)}" title="打开${avatarKind==='performer'?esc(performerLabel(it)):'资料'}页"`,inner)
          : `<span class="mav">${inner}</span>`;
      })();
  const whoHtml=coStarred
    ? link('who',`data-entity-kind="performer" data-entity-name="${esc(performer)}"`,esc(performer))
      +`<span class="whomore">等 ${performerTotal} 人</span>`
    : (whoKind?link('who',`data-entity-kind="${whoKind}" data-entity-name="${esc(who)}"`,esc(who)):`<span class="who">${esc(who)}</span>`);
  return {avatar,whoHtml};
}
function cardHtml(it,cls){
  /* 资料页可能同时收录番号和非番号作品；版式按钮属于页面，但封套比例只施加给
     真实 `is_jav` 卡片，不能把同页的创作者视频也拉成竖封。 */
  const jav=javActive()&&!!it.is_jav,layout=javLayout();
  const parts=it.part_group||null;
  const editions=it.edition_group||null;
  const useCover=jav&&layout!=='preview'&&it.has_cover;
  /* 卡片比例，写进 `--card-ratio` 交给 CSS 消费。`.pic` 写死 16/9 的话，JAV 的两种
     版式看起来一模一样。 */
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
    : it.follow_thumb_url
      ? `<img class="poster" src="${esc(it.follow_thumb_url)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
    : (it.has_thumb
      ? `<img class="poster" src="/poster?id=${it.id}&c=4" alt="" loading="lazy">`
      : `<span class="nopic">无预览</span>`);
  const fl=[it.feedback==='dislike'&&'dislike',it.feedback==='seen'&&'seen',
            it.disposal==='trash'&&'dispose',it.watch_later&&'later']
            .filter(Boolean).map(c=>`<i class="${c}"></i>`).join('');
  const {avatar,whoHtml}=cardIdentity(it);
  const rawShownName=parts?.title||it.name;
  const shownName=javDisplayName(it,rawShownName);
  const shownTitle=javTitleHtml(it,rawShownName);
  const shownSize=parts?.total_size??it.size;
  const shownDuration=parts?.total_duration??it.duration;
  const watchedRatio=!parts&&Number(it.play_seconds)>0&&Number(it.duration)>0
    ? Math.min(Number(it.play_seconds)/Number(it.duration),1):0;
  const tr=watchedRatio>0
    ? `<div class="watchprogress" role="progressbar" aria-label="观看进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(watchedRatio*100)}"><i style="width:${(watchedRatio*100).toFixed(1)}%"></i></div>`
    : (it.leave_ratio!=null?`<div class="scrub"><i style="width:${Math.round(it.leave_ratio*100)}%"></i></div>`:'');
  const sizeText=Number(shownSize)>0?fmtSize(Number(shownSize)):'大小未知';
  const tgs=(it.follow_tags||it.tags||[]).slice(0,3).map(x=>`<span class="tg general"${it.follow_item_id?'':` data-tag="${esc(x)}"`}>${esc(tagLabel(x))}</span>`).join('');
  const laterTool=`<div class="hovertools later-tools"><button class="laterbtn" data-later aria-pressed="${!!it.watch_later}" title="稍后看" aria-label="稍后看">
      ${it.watch_later?icon('check'):icon('bookmark-plus')}</button></div>`;
  /* 分卷卡悬浮翻的是各卷首帧，没有可控的视频：倒计时环和快退／快进那三颗留着的话，
     按下去找不到 `video.hv`，等于三颗空按钮压在正在翻的画面上。 */
  const tools=parts?laterTool:`<button class="previewcounter" data-open title="打开预览" aria-label="打开预览">
      <svg viewBox="-18 -18 36 36"><circle r="17"></circle><circle r="17"></circle></svg>${icon('play','ringplay')}</button>
    ${laterTool}
    <div class="hovertools seektools">
      <button data-seek="-${appSettings.seekSeconds}" title="后退 ${appSettings.seekSeconds} 秒" aria-label="后退 ${appSettings.seekSeconds} 秒">${icon('rotate-ccw')}</button>
      <button data-seek="${appSettings.seekSeconds}" title="前进 ${appSettings.seekSeconds} 秒" aria-label="前进 ${appSettings.seekSeconds} 秒">${icon('rotate-cw')}</button>
      <button data-open title="打开详情" aria-label="打开详情">${icon('maximize')}</button></div>`;
  /* 小图与预览图都是 16:9 横图，只更换图片来源；元数据 DOM 和高度必须完全相同。 */
  /* 叠层纸边是「这张卡代表不止一条」的视觉说法，分卷和版次都成立。只给分卷的话，
     同样被折叠过的版次卡长得和普通卡一模一样，只有角标能看出来。 */
  const stacked=parts||editions;
  return `<article class="card ${stacked?'partcard ':''}${cls||''} ${it.disposal==='trash'?'pending-delete':''}" data-id="${it.id}"${parts?` data-part-seed="${parts.seed_id}"`:''}>
    ${stacked?'<div class="partstack">':''}<div class="pic" style="--card-ratio:${ar}">${thumb}${parts?'<div class="mixfaces" data-mix-faces hidden></div>':''}<button class="cardopenhit" data-open aria-label="打开 ${esc(shownName)}${parts?'分卷':editions?'版本':'详情'}"></button>
      <div class="badge mono">${srcBadge(it.location,it.cost)}</div>
      <span class="selectionMark">${icon('check')}</span><span class="deleteMark">${icon('trash')}<b>回收站</b></span>
      ${parts?`<span class="partbadge">${parts.count} 卷</span>`:''}${editions?`<span class="partbadge editionbadge" title="${esc(editions.editions.join(' · '))}">${editions.count} 个版本</span>`:''}<span class="dur mono">${fmtDur(shownDuration)}</span>${tr}${tools}</div>${stacked?'</div>':''}
    <div class="meta">${avatar}<div class="mtext"><button class="t cardtitle" data-open>${shownTitle}</button>
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
      ${image?`<img class="poster" src="/photo-thumb?id=${it.id}" alt="" loading="lazy" data-drop="self">`:''}
      <div class="badge mono">${srcBadge(it.location,it.cost)}</div>
      <span class="selectionMark">${icon('check')}</span><span class="deleteMark">${icon('trash')}<b>回收站</b></span>
      <button class="resourcecardaction" type="button" data-resource-operation="${action}" aria-label="${actionLabel} ${esc(it.name||'')}" title="${actionLabel}">${icon(action==='restore'?'rotate-ccw':'trash')}<span>${actionLabel}</span></button></div>
    <div class="meta"><span class="mav resourcekind" aria-hidden="true">${icon(glyph)}</span><div class="mtext">
      <span class="t resourcecardtitle" data-middle-truncate title="${esc(it.name||'')}">${esc(it.name||'未命名资源')}</span>
      <div class="s mono"><span class="who">${esc(label)}</span>${it.why?`<span class="why">${esc(it.why)}</span>`:''}<span class="size">${Number(it.size)>0?fmtSize(Number(it.size)):'大小未知'}</span></div>
    </div></div></article>`;
}
const JUNK_KIND_META={
  video:['视频','play'],image:['图片','pics'],archive:['压缩包','file-archive'],
  audio:['音频','file-audio'],url:['网址快捷方式','globe'],other:['其它文件','hard-drive'],
};
function junkCardHtml(it){
  const kind=it.junk_kind||'other',meta=JUNK_KIND_META[kind]||JUNK_KIND_META.other;
  const preview=kind==='video'
    ? `<img class="poster" src="/thumb?id=${it.id}&c=4" width="640" height="360" alt="" loading="lazy" data-drop="self">`
    : kind==='image'
      ? `<img class="poster" src="/photo-thumb?id=${it.id}" width="640" height="360" alt="" loading="lazy" data-drop="self">`:'';
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
      <button type="button" data-junk-reveal title="在资源管理器中显示" aria-label="在资源管理器中显示">${icon('folder-open')}<span>打开位置</span></button>
      <button type="button" data-junk-operation="${decision[0]}" title="${esc(decision[1])}" aria-label="${esc(decision[1])}">${icon(decision[2])}<span>${decision[1]}</span></button>
      <button type="button" class="junktrash" data-junk-operation="dispose" title="移入回收站" aria-label="移入回收站">${icon('trash')}<span>移入回收站</span></button>
      <span class="junkstate" aria-live="polite"></span>
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
      if(event.target.closest('[data-junk-operation],[data-junk-reveal]'))return;
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
    const reveal=card.querySelector('[data-junk-reveal]'),status=card.querySelector('.junkstate');
    if(reveal)reveal.onclick=event=>{
      event.preventDefault();event.stopPropagation();revealSource(id,status,{button:reveal});
    };
    card.querySelectorAll('[data-junk-operation]').forEach(button=>button.onclick=async event=>{
      event.preventDefault();event.stopPropagation();
      const operation=button.dataset.junkOperation;
      setActionBusy(button);
      try{
        await runJunkOperation(id,operation);
        const disposed=operation==='dispose',reconsidered=operation==='reconsider-junk';
        actionReceipt(disposed?'已移入回收站':reconsidered?'已重新加入垃圾判断':'已标记为不是垃圾',{
          undo:()=>runJunkOperation(id,disposed?'restore':reconsidered?'dismiss-junk':'reconsider-junk'),
        });
      }catch(error){
        actionFailure('操作',error);
        setActionBusy(button,false);
      }
    });
  });
}
function renderJunkNavigation(data){
  const countFor=key=>key?Number(data.counts?.[key]||0):Number(data.all_total||0);
  const dismissedTotal=Number(data.dismissed_total||0);
  const categoryLinks=JUNK_KIND_OPTIONS.map(([key,label,glyph])=>{
    const current=key===junkKind,count=countFor(key);
    /* 同一套 Geist Tabs 徽标口径：计数为 0 时整枚去掉。这一条仍用 <a>，因为分类要落到
       URL 上——规范里 Tabs 的行为条款本身就要求当前项可深链、可刷新恢复。 */
    return `<a href="${junkPath(key,junkView)}" data-junk-kind-link="${esc(key)}"${current?' aria-current="page"':''}>${icon(glyph)}${esc(label)}${count?` <span class="n mono">${count.toLocaleString()}</span>`:''}</a>`;
  }).join('');
  $('#count').removeAttribute('aria-busy');
  $('#count').innerHTML=`<div class="junksummary" aria-live="polite">显示 ${Number(data.total||0).toLocaleString()} 个</div>
    <nav class="junkfilters" aria-label="垃圾文件分类">${categoryLinks}<i aria-hidden="true"></i>
      <a href="${junkPath('',junkView==='dismissed'?'pending':'dismissed')}" data-junk-view-link="${junkView==='dismissed'?'pending':'dismissed'}"${junkView==='dismissed'?' aria-current="page"':''}>${icon(junkView==='dismissed'?'rotate-ccw':'eye-off')}${junkView==='dismissed'?'返回待判断':'已排除'}${dismissedTotal?` <span class="n mono">${dismissedTotal.toLocaleString()}</span>`:''}</a>
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
      setActionBusy(button);
      button.innerHTML=`${spinnerHtml(operation==='restore'?'正在还原':'正在移入回收站')}<span>${operation==='restore'?'正在还原':'正在处理'}</span>`;
      try{
        const id=+card.dataset.id;
        await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[id],operation})});
        await load(true);
        const inverse=operation==='restore'?'dispose':'restore';
        actionReceipt(operation==='restore'?'已还原':'已移入回收站',{undo:async()=>{
          await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[id],operation:inverse})});
          await load(true);
        }});
      }catch(error){
        actionFailure('操作',error);
        setActionBusy(button,false);
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
/* 这一条真能画出图吗。必须和下面 mixFacePoster 的分支一致：只看 has_cover 会把
   非 JAV 模式下只有官方封套的条目当成有图，选它做 seed 或翻到它都是一张「无预览」。 */
function mixHasPicture(it,layout){
  return !!it&&((javActive()&&!!it.is_jav&&layout!=='preview'&&!!it.has_cover)||!!it.has_thumb);
}
/* Mix 卡片的静止封面和悬浮翻动的每一张都走这里：翻进来的那张必须和静止的
   那张长得一样，否则一翻就露出比例和取景的差别。 */
function mixFacePoster(it,layout,eager){
  const jav=javActive()&&!!it.is_jav;
  const useCover=jav&&layout!=='preview'&&it.has_cover;
  /* 翻动的那几张必须 eager：它们是悬浮时才插进一个 hidden 容器的，
     lazy 图在没有布局盒时根本不会发请求，一翻就是黑屏。 */
  const load=eager?'eager':'lazy';
  return useCover
    ? coverImage(it,layout,eager)
    : (it.has_thumb
      ? `<img class="poster" src="/poster?id=${it.id}&c=4" alt="" loading="${load}">`
      : `<span class="nopic">无预览</span>`);
}
function mixCardHtml(it){
  const jav=javActive()&&!!it.is_jav,layout=javLayout();
  const ar=jav&&layout==='big'?COVER_FRONT_RATIO:16/9;
  const thumb=mixFacePoster(it,layout);
  const label=mixLabel(it);
  return `<article class="card mixcard" data-mix-seed="${it.id}">
    <div class="mixstack"><div class="pic" style="--card-ratio:${ar}">${thumb}<div class="mixfaces" data-mix-faces hidden></div><button class="cardopenhit" data-open-mix aria-label="打开 Mix · ${esc(label)}"></button>
      <span class="mixbadge">${icon('play')}Mix</span></div></div>
    <div class="mixmeta"><span class="mixglyph">${icon('play')}</span><div class="mixcopy">
      <b>Mix · ${esc(label)}</b><span>${esc(javDisplayName(it))}及相似作品</span></div></div></article>`;
}
let renderedPartGroups=new Set();
/* 版次组和分卷组各自折叠。分卷是「一部片被切成几段」，版次是「同一部片的几个来源」
   ——有码、中字、无码。它们能同时出现在一个番号上，所以两套 key 分开记，不共用。 */
let renderedEditionGroups=new Set();
function collapseMultipartItems(items){
  if(!appSettings.groupCollapse)return items;
  return items.filter(it=>{
    const key=it.part_group?.key;
    if(!key)return true;
    if(renderedPartGroups.has(key))return false;
    renderedPartGroups.add(key);return true;
  });
}
function collapseEditionGroups(items){
  if(!appSettings.groupCollapse)return items;
  return items.filter(it=>{
    const key=it.edition_group?.key;
    if(!key)return true;
    if(renderedEditionGroups.has(key))return false;
    renderedEditionGroups.add(key);return true;
  });
}
const MIX_SLOT=7;                 // Mix 卡片插在这一位，也就是每批的第 8 张
/* seed 决定 Mix 的封面和署名。旧写法取「本批第一个有署名的作品」，而几乎
   每条都有 creator，于是 seed 恒等于第一张卡片：Mix 卡片永远显示它上面几行那张
   同样的图，看起来像渲染错了。改成从 Mix 位再往下隔一屏开始找：仍然是本批里的
   一部作品，语义不变，但不会和同屏可见的卡片撞图。 */
function mixSeed(visible){
  const layout=javLayout();
  const named=it=>mixHasPicture(it,layout)&&(it.creator||(it.performers||[]).length||it.studio);
  return visible.slice(MIX_SLOT+8).find(named)
    ||visible.slice(MIX_SLOT+1).find(named)
    ||visible.slice(MIX_SLOT+1).find(it=>mixHasPicture(it,layout))
    ||visible[visible.length-1];
}
function batchWithMix(items,enabled=true){
  const visible=collapseEditionGroups(collapseMultipartItems(items));
  const cards=visible.map(it=>cardHtml(it));
  if(!enabled)return cards.join('');
  const seed=mixSeed(visible);
  if(seed&&visible.length>=8)cards.splice(MIX_SLOT,0,mixCardHtml(seed));
  return cards.join('');
}
/* 相关作品每个 seed 只取一次：悬浮翻动和点开后的队列用的是同一份，
   悬浮过再点开 Mix 不会再发一次请求。 */
const mixRelatedCache=new Map();
function mixRelated(seedId){
  if(!mixRelatedCache.has(seedId))
    mixRelatedCache.set(seedId,api('/api/related?id='+seedId+'&limit=28')
      .then(d=>cache((d.items||[]).filter(x=>x.id!==seedId)))
      .catch(error=>{mixRelatedCache.delete(seedId);throw error}));
  return mixRelatedCache.get(seedId);
}
const MIX_FLIP_MS=1100;      // 一张停多久再翻走
const MIX_FLIP_LEAD_MS=420;  // 面板建好到第一次翻动。直接用 1.1 秒间隔等第一张，鼠标停下到有反应要接近两秒
const MIX_FLIP_FACES=9;      // 最多预渲染几张，一次悬浮不拉一整批封面
const reduceMotion=()=>matchMedia('(prefers-reduced-motion:reduce)').matches;
/* 悬浮一叠卡片时把它里面的前几张逐张翻走，说明它是一叠而不是某一个视频。
   门槛和悬停预览一致：多选、遮挡、滞后动画偏好和滚动中都不启动，离开即停并
   还原静止封面；`_stopHover` 让 releaseHoverPreviews 能连它一起收掉。
   翻哪些由调用方给：目录页的 Mix 现拉相关作品，关注页的合集用卡片自己已有的
   缩略图，两处共用同一套时序和门槛，不各写一份动效。 */
function wireStackFlip(el,loadFaces){
  const box=el.querySelector('[data-mix-faces]');if(!box)return;
  let armed=null,lead=null,cycle=null,faces=[],index=0,live=false;
  const stop=()=>{
    live=false;clearTimeout(armed);armed=null;clearTimeout(lead);lead=null;
    clearInterval(cycle);cycle=null;
    box.hidden=true;box.innerHTML='';faces=[];index=0;
  };
  const step=()=>{
    const out=faces[index],next=faces[(index+1)%faces.length];
    out.classList.remove('on');out.classList.add('off');
    next.classList.remove('off');next.classList.add('on');
    // 翻出去的那张得先演完才能卸掉 off，否则会当场弹回原位。
    setTimeout(()=>{if(out!==next)out.classList.remove('off')},MIX_FLIP_MS-120);
    index=(index+1)%faces.length;
  };
  const start=async()=>{
    if(selectMode||censorOn()||window.__scrolling||reduceMotion())return;
    live=true;
    let pool=[];
    try{pool=await loadFaces()}catch(_e){return}
    if(!live||selectMode||censorOn())return;
    if(pool.length<2)return;
    box.innerHTML=pool.map((face,i)=>`<div class="mixface${i?'':' on'}">${face}</div>`).join('');
    faces=[...box.children];index=0;box.hidden=false;
    lead=setTimeout(()=>{step();cycle=setInterval(step,MIX_FLIP_MS)},MIX_FLIP_LEAD_MS);
  };
  el.addEventListener('mouseenter',()=>{clearTimeout(armed);armed=setTimeout(start,340)});
  el.addEventListener('mouseleave',stop);
  el._stopHover=stop;
}
function wireMixFlip(el,seedId){
  wireStackFlip(el,async()=>{
    const related=await mixRelated(seedId),layout=javLayout();
    return [CACHE[seedId],...related]
      .filter(x=>mixHasPicture(x,layout)).slice(0,MIX_FLIP_FACES)
      .map(x=>mixFacePoster(x,layout,true));
  });
}
/* 分卷组每个 seed 只取一次：悬浮翻动和点开后的分卷队列用的是同一份。 */
const partGroupCache=new Map();
function partGroup(seedId){
  if(!partGroupCache.has(seedId))
    partGroupCache.set(seedId,api('/api/parts?id='+seedId)
      .then(group=>{if(group.error)throw new Error(group.error);cache(group.items);return group})
      .catch(error=>{partGroupCache.delete(seedId);throw error}));
  return partGroupCache.get(seedId);
}
/* 分卷卡悬浮翻的是同一部片各卷的画面，和 Mix 用同一套时序与门槛。版次组不翻：
   有码、中字、无码是同一段画面的几个来源，翻过去前后两张几乎一样，看着像图卡住了，
   那种卡继续用分段视频预览。第一张是卡片自己的静止封面，翻进来的才不会跳取景。 */
function wirePartFlip(el,it){
  wireStackFlip(el,async()=>{
    const items=await partGroup(it.part_group.seed_id).then(group=>group.items),layout=javLayout();
    return [it,...items.filter(x=>x.id!==it.id)]
      .filter(x=>mixHasPicture(x,layout)).slice(0,MIX_FLIP_FACES)
      .map(x=>mixFacePoster(x,layout,true));
  });
}
/* 关注页的合集翻的是卡片渲染时就写进 DOM 的那几张缩略图：同一组媒体已经在
   手上，悬浮不该再为动画发一次请求。第一张必须是静止封面本身，否则一翻就
   露出取景差别。 */
function wireFollowStackFlip(card){
  const box=card.querySelector('[data-mix-faces]');if(!box)return;
  let urls=[];
  try{urls=JSON.parse(box.dataset.mixFaces||'[]')}catch(_e){return}
  wireStackFlip(card,async()=>urls.map(url=>
    `<img class="poster" src="${esc(url)}" alt="" loading="eager" referrerpolicy="no-referrer">`));
}
function wireMixCards(root){
  root.querySelectorAll('[data-mix-seed]').forEach(el=>{
    if(el.dataset.wired)return;el.dataset.wired='1';
    const seedId=+el.dataset.mixSeed;
    el.onclick=()=>openMix(seedId,seedId,true,el);
    wireMixFlip(el,seedId);
  });
}
/* 一个标签是否生效、按一下变成什么，全站只有这一份判据。目录、资料页和详情页各自
   存着自己的筛选，谁在那里手写一次 `split(',')` 或 `=== filters.tag`，谁就会与其余
   几处漂开：按下态按多选算、点击按单选写，同一枚标签的显示和行为对不上。 */
const tagList=(value=state.tag)=>String(value||'').split(',').filter(Boolean);
const tagPressed=(value,tag)=>tagList(value).includes(String(tag));
const withTagToggled=(value,tag)=>{const cur=tagList(value);const index=cur.indexOf(tag);
  index>=0?cur.splice(index,1):cur.push(tag);return cur.join(',')};
function wireCards(root,onClick){
  root.querySelectorAll('[data-id]').forEach(el=>{
    if(el.dataset.wired)return; el.dataset.wired='1';
    const it=CACHE[el.dataset.id];
    const openCard=(id,anchor=el)=>onClick?onClick(id,anchor):(it?.part_group
      ?openParts(it.part_group.seed_id,id,true,anchor)
      :it?.edition_group
        ?openEditions(it.edition_group.seed_id,id,true,anchor)
        :openItem(id,true,null,anchor));
    el.onclick=e=>{
      const seek=e.target.closest('[data-seek]');
      if(seek){e.stopPropagation();const v=el.querySelector('video.hv');
        if(v&&Number.isFinite(v.duration)){if(v._hop){clearInterval(v._hop);v._hop=null}
          v.currentTime=Math.max(0,Math.min(v.duration,v.currentTime+(+seek.dataset.seek)))}return}
      const later=e.target.closest('[data-later]');
      if(later){e.stopPropagation();setActionBusy(later);api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})})
        .then(r=>{it.watch_later=r.watch_later;later.setAttribute('aria-pressed',r.watch_later);
          later.innerHTML=r.watch_later?icon('check'):icon('bookmark-plus');
          actionReceipt(r.watch_later?'已加入稍后看':'已移出稍后看',{undo:async()=>{
            const restored=await api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})});
            it.watch_later=restored.watch_later;if(!later.isConnected)return;
            later.setAttribute('aria-pressed',restored.watch_later);
            later.innerHTML=restored.watch_later?icon('check'):icon('bookmark-plus');
          }})}).catch(error=>actionFailure('更新稍后看',error)).finally(()=>setActionBusy(later,false));return}
      if(selectMode||e.shiftKey||e.ctrlKey||e.metaKey){e.preventDefault();e.stopPropagation();toggleSelection(it.id,e.shiftKey);return}
      if(e.target.closest('[data-open]')){e.stopPropagation();openCard(+el.dataset.id,el);return}
      /* 只认卡片自己身上的实体链接。资料页把 `data-entity-kind` 写在 `#index` 上，
         无界的 `closest` 会一路找到它：卡片上任何一次点击都变成「再打开一次这一页」，
         底下的标签和播放分支一个都轮不到。 */
      const ent=e.target.closest('[data-entity-kind]');
      if(ent&&el.contains(ent)){e.stopPropagation();openEntity(ent.dataset.entityKind,ent.dataset.entityName);return}
      /* 卡片上的标签是「只看这个标签」，已经在筛它就取消。在哪一屏点就在哪一屏
         生效：目录上换成这个标签，资料页上是在这个人／厂牌内部换。 */
      const tg=e.target.closest('.tg');
      if(tg){e.stopPropagation();
        commitContextFilter(filters=>{
          filters.tag=tagPressed(filters.tag,tg.dataset.tag)?'':tg.dataset.tag});
        window.scrollTo({top:0,behavior:'smooth'});return}
      if(e.shiftKey||e.ctrlKey||e.metaKey||selectMode){e.preventDefault();toggleSelection(it.id,e.shiftKey);return}
      openCard(+el.dataset.id,el);
    };
    el.querySelectorAll('[data-open]').forEach(opener=>{
      opener.dataset.openWired='1';
      opener.onclick=e=>{e.stopPropagation();if(selectMode||e.shiftKey||e.ctrlKey||e.metaKey){e.preventDefault();toggleSelection(it.id,e.shiftKey);return}openCard(+el.dataset.id,el)};
    });
    if(it?.part_group)wirePartFlip(el,it);
    else if(it&&(!it.medium||it.medium==='video'))wireHover(el,it);
  });
}

/* ── 顶部标签条 + 抽屉 ── */
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
  if(context.type!=='item'){
    const filters=activeFilterState();
    ['loc','creator','studio','tag','tag_match','len','dur_min','dur_max','orient','q','thumb'].forEach(key=>{
      if(filters[key])facetParams.set(key,filters[key]);
    });
  }
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
/* 首屏时顶部三层和标签条还是两个空 div，而这一次请求要花约一秒。Geist 的判据是
   骨架宽高必须等于最终内容——「200×20 的块变成 80×16 的字读起来像故障」——所以
   这里直接套真实类名，让几何自己对上。只在还空着时画：导航到已经有内容的页面
   留着旧内容等新内容，那不是从无到有，不该铺骨架。四枚视图胶囊由 state 决定，
   这次请求不改它们，所以现在就画成最终样子并接上事件。 */
const VIEW_PILLS=[{k:'',label:'全部'},{k:'fresh',label:'没看过'},
                  {k:'later',label:'稍后看'},{k:'flagged',label:'已标记'}];
const viewPillsHtml=filterState=>VIEW_PILLS.map(v=>
    `<a class="pill" href="${v.k?STATE_ROUTES[v.k]:'/'}" data-state="${v.k}" aria-pressed="${
      filterState.state===v.k}">${v.label}</a>`).join('')+`<span class="sep"></span>`;
function wireViewPills(){
  $('#tagbar').querySelectorAll('[data-state]').forEach(b=>b.onclick=e=>{
    e.preventDefault();state.state=b.dataset.state;route(homePath());buildBars();load(true)});
}
// 宽度是一组定值而不是随机数：随机会让同一次冷启动在两台机器上长得不一样，也没法测。
function renderBarsLoading(filterState){
  const tiers=$('#tiers'),tagbar=$('#tagbar');
  if(!tiers.innerHTML){
    tiers.hidden=false;tiers.setAttribute('aria-busy','true');
    tiers.innerHTML=`<div class="tier" data-skeleton-tier="av"></div>
      <div class="tier" data-skeleton-tier="brandpill"></div>`;
    fitSkeleton(tiers);
  }
  if(!tagbar.innerHTML){
    tagbar.setAttribute('aria-busy','true');
    tagbar.innerHTML=viewPillsHtml(filterState);
    fillSkeletonTier(tagbar,'pill');
    wireViewPills();
  }
}
async function buildBars(){
  const requestSeq=++barsRequestSeq;
  buildDrawerNavigation();
  if(!sidebarHasCatalogContent(location.pathname))return;
  const context=barsContext,filterState=activeFilterState();
  renderBarsLoading(filterState);
  // 两个聚合查询互不依赖。冷启动各需约 1 秒，串行会让手机首屏白等；
  // 并行取回后再一次性绘制顶部与抽屉。
  const [facetData,tops]=await getBarsData(context);
  if(requestSeq!==barsRequestSeq)return;
  const followTagRows=facetData.follow_tags||[];
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
  /* REP 表只收真能取到头像的代表作：卡片署名圈回落时读的就是它，取不到的进了表
     就是一个必然 404 的 `<img>`。`has_avatar` 说的是「已经裁好或印相还在」，不是
     「目录里有没有那张 jpg」——`/avatar` 按需生成，还没抓过的那条路留着。 */
  tops.performers.forEach(x=>{if(x.rep&&x.has_avatar)REP[x.k]=x.rep});
  tops.studios.forEach(x=>{if(x.rep&&x.has_avatar)REP[x.k]=x.rep});
  const avHtml=x=>`<button class="av" data-entity-kind="performer" data-entity-name="${esc(x.k)}">
    <span class="ring"><span class="ini">${esc(x.k.slice(0,1))}</span>${entityFaceImg(
      {id:x.id,hasImage:x.has_image,rep:x.has_avatar?x.rep:null})}</span>
    <span class="nm">${esc(x.k)}</span></button>`;
  /* 正规厂牌用官网 logo；缺失时只显示首字母，绝不把作品截图冒充厂牌图标。

     没装标识就一个 `<img>` 都不输出。无条件出图、靠 `/logo` 回 404 换成首字母的
     代价是：顶栏一排 30 个厂牌里 21 个是 404，而 404 那条响应不可缓存，每次重绘
     再打一整轮。`has_logo` 由 `/api/tops` 下发，判据和取图同一个函数。 */
  const bpHtml=x=>{
    const fallback=`${esc(x.k.slice(0,2))}`;
    const mark=x.has_logo
      ? `<img src="/logo?studio=${encodeURIComponent(x.k)}&variant=icon" alt="">`
      : fallback;
    return `<button class="brandpill" data-entity-kind="studio" data-entity-name="${esc(x.k)}">
      <span class="mk" data-fallback="${fallback}">${mark}</span>${esc(x.k)}</button>`;
  };
  // 空的一排仍占 28px，在「已标记」这种窄集合上就是两条什么都没有的空带。
  // 没人就不画那一排，两排都没人就整块收起。
  const perfRow=tops.performers.map(avHtml).join('');
  const studioRow=tops.studios.map(bpHtml).join('');
  const tier=html=>html?`<div class="tier">${html}</div>`:'';
  $('#tiers').innerHTML=tier(perfRow)+tier(studioRow);
  $('#tiers').hidden=!(perfRow||studioRow);
  $('#tiers').removeAttribute('aria-busy');
  $('#tiers').querySelectorAll('[data-entity-kind]').forEach(b=>b.onclick=()=>
    openEntity(b.dataset.entityKind,b.dataset.entityName));
  // 兜底只剩「装了但读不出来」这一种：文件坏了，或归一漏掉、图小到看不出是什么。
  // 「没装标识」在 bpHtml 就已经不出图了，走不到这里。
  $('#tiers').querySelectorAll('.mk img').forEach(img=>{
    const fallback=()=>{const box=img.parentNode;if(box)box.textContent=box.dataset.fallback||''};
    img.addEventListener('error',fallback,{once:true});
    img.addEventListener('load',()=>{if(img.naturalWidth<32)fallback()},{once:true});
  });

  $('#tagbar').removeAttribute('aria-busy');
  $('#tagbar').innerHTML=viewPillsHtml(filterState)
    +seededSample(topTags,26,`tags:${state.seed||''}`).map(t=>
      `<button class="pill" data-tag="${esc(t.k)}" aria-pressed="${
        tagPressed(filterState.tag,t.k)}">${esc(tagLabel(t.k))}</button>`).join('');
  wireViewPills();
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
  // 与窄栏共用 EDGE_ICONS —— 两边条目必须一致，抽屉不另写一份硬编码
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
    +sec('影片属性',chips(facetData.tech,'tag',false,16),'','meta')
    +sec('关注标签',followTagRows.length?`<div class="chips">`+followTagRows.map(row=>
      `<button class="chip online" data-follow-drawer-tag="${esc(row.k)}">${esc(tagLabel(row.k))}<span class="n">${row.n.toLocaleString()}</span></button>`
      ).join('')+`</div>`:'','','online');
  const dc=$('#drawerClose'); if(dc)dc.onclick=()=>openDrawer(false);
  $('#drawer').querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{
    openIndex(b.dataset.page); closeDrawerAfterNav()});
  $('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));
  $('#drawer').querySelectorAll('[data-follow-drawer-tag]').forEach(b=>b.onclick=()=>{
    followAuthor='';followProvider='';followMediaView='videos';followFilter='saved';
    followTags=new Set([b.dataset.followDrawerTag]);
    openDrawer(false);route(followViewPath());openFollow(false)});
  wireNavigationDrag($('#drawer').querySelector('.dnav'));
  /* 只认目录筛选自己的芯片。选择器写成 `.chip` 会把关注标签也扫进来——它同样
     用 chip 的样式，但没有 data-key，被这里接管后点下去等于按 undefined 筛目录，
     表现是跳回首页。这段在下面才执行，覆盖的正是关注标签自己的处理。 */
  const bind=()=>$('#drawer').querySelectorAll('.chip[data-key]').forEach(b=>b.onclick=()=>{
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
  /* 「清空回收站」和左边的计数说的是同一批文件，挂在说明行右端。它自己占一行时，
     标题和网格之间会空出一条只放一个按钮的带子。 */
  if(trash)paintManageLede(`${total.toLocaleString()} 个符合 · 显示 ${n}`,
    total?`<button class="batchaction danger" id="emptyTrash" type="button" title="永久删除回收站内容">清空回收站</button>`:'');
  $('#count').classList.toggle('count-actions-only',trash);
  $('#count').removeAttribute('aria-busy');$('#count').removeAttribute('aria-label');
  $('#count').innerHTML=
    (trash?'':`<span class="mono">${total.toLocaleString()} 个符合 · 显示 ${n}</span>`)
    // 回收站是待清理队列，不是浏览列表：换一批和排序在这里没有意义。
    +(trash?'':countSortsHtml());
  wireCountRow();
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
      actionReceipt(`已永久删除 ${r.purged} 项`);
    }catch(error){actionFailure('清空回收站',error);
    }finally{await load(true)}
  };
}

/* ── 组合筛选：多个标签同时生效 ── */
/* 标签开关作用在当前语境上：目录上筛目录，资料页上就在这个人／厂牌内部筛。写入一律
   走 `commitContextFilter`，它是筛选的唯一落点；绕过它直接改 `state`，在资料页上点
   一个标签就会被扔回目录，而按下态读的是资料页自己的筛选，两边说的不是一回事。 */
function toggleTag(t){commitContextFilter(filters=>{filters.tag=t?withTagToggled(filters.tag,t):''})}
/* 芯片是目录列表自己的生效筛选，只在目录铺在屏幕上时才有所指。资料页、索引页和管理页
   都会铺开 `#index` 或 `#stats` 盖住目录，那时它指的那个列表不在屏幕上，画出来就是一条
   对本页无效、点下去还会把人带走的筛选条。判据取自屏幕本身，不依赖每个整页入口记得
   清一次——绘制侧无条件画，清除侧就得在每个新入口补一遍，补漏一个就复发。 */
const catalogOnScreen=()=>$('#index').hidden&&$('#stats').hidden;
function renderCombo(){
  if(!catalogOnScreen()){$('#combo').innerHTML='';return}
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
  $('#combo').querySelectorAll('[data-clear]').forEach(b=>b.onclick=()=>
    commitContextFilter(filters=>{filters[b.dataset.clear]=''}));
  $('#clrAll').onclick=()=>commitContextFilter(filters=>{
    filters.tag='';filters.creator='';filters.studio=''});
}

/* ── 统计与管理 ── */
/* 整页视图接管页面主体。

   这段六行的显隐此前在八个入口里各抄了一份，每份还带着随手的小差异：空格、顺序、
   是 `buildManageBar()` 还是隐藏管理条再 `buildEdge()`。抄一次就多一次漏行的机会——
   关注、播放列表、复核三个页面漏掉筛选芯片，就是从抄 `enterManagementSurface` 抄漏
   开始的，那次漏的是「离开目录」这一半，这里是「铺开新页面」的另一半。

   两个函数不合并，是因为调用时机真的不同：`enterManagementSurface` 必须在任何 await
   之前跑（`loadRequestSeq++` 要抢在在途的目录请求之前作废它），而主体有的入口在取数
   前铺（配 `placeholder` 给反馈），有的在取数后铺（数据快时不闪一下骨架）。
   两个都要调，由 `test_every_full_page_view_enters_through_the_shared_helpers` 兜住。 */
/* 「载入更多」按钮观察自己：滚到它进视口就自动续取，按钮只是兜底（观察器不可用、
   或用户用键盘跳到底部）。这么做是因为「未看 3036」和「已显示 152」是两个口径，
   用户不必先看懂它们，一直往下滚就是了。

   这段此前抄了三份：关注流、实体合集、照片墙。已经开始漂——后两份有 `hidden` 判断，
   关注那份没有。藏起来的按钮观察它没有意义（它永远不会进视口），漏掉只是浪费一个
   观察器，但下一次抄漏的可能就不是这一行了。

   重画会换掉按钮节点，所以每次都要先 disconnect：旧观察器还盯着已经脱离文档的节点，
   既不会触发也不会被回收。 */
function wireLoadMore(button, load){
  if(!button)return;
  button.onclick=()=>load();
  button._observer?.disconnect();
  if(button.hidden)return;
  button._observer=new IntersectionObserver(
    entries=>{if(entries.some(entry=>entry.isIntersecting))load()},
    {rootMargin:'320px'});
  button._observer.observe(button);
}
const skeletonKeyOf=html=>String(html).match(/data-skeleton="([^"]*)"/)?.[1]||'';
function showManagementBody({manage=true,placeholder=''}={}){
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  if(manage)buildManageBar();
  else{$('#managebar').hidden=true;$('#manageTitle').hidden=true;buildEdge()}
  if(!placeholder)return;
  /* 屏幕上已经是同一张骨架就别重画：innerHTML 换新节点会把 shimmer 从头放一遍，
     整页刷新看到的就是同一段动画闪两次。 */
  const painted=$('#stats').querySelector('[data-skeleton]')?.dataset.skeleton||'';
  const next=skeletonKeyOf(placeholder);
  if(!next||next!==painted){$('#stats').innerHTML=placeholder;fitSkeleton($('#stats'))}
}
/* 铺开索引页与资料页。这一屏盖住目录，所以在这里收掉目录的筛选芯片，与管理页那侧的
   `enterManagementSurface()` 对称：索引页此后不再重画芯片，画上去的那条会一直留着。
   `renderCombo()` 自己也拦得住（它先问过屏幕），两侧都要有——一个负责当场擦掉，
   一个负责之后谁都别再画上去。 */
function showIndexLoading(label){
  $('#stats').hidden=true;$('#index').hidden=false;$('#grid').innerHTML='';$('#combo').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#index').innerHTML=pageSkeletonHtml(label,{cards:true});
  fitSkeleton($('#index'));
}
function enterManagementSurface(){
  // A catalog request started before browser Back must not repaint filters over
  // the management page after it resolves.
  loadRequestSeq++;listLoading=false;$('#combo').innerHTML='';
  hideDiscoveryBars();
  document.body.classList.remove('entity-open','index-open');
}
async function openStats(push=true){
  releaseHoverPreviews();
  if(push)route('/stats');
  const surface=claimSurface('/stats');
  enterManagementSurface();
  disposeStage(false);
  showManagementBody({placeholder:managementPlaceholder('/stats')});
  const d=await surfaceApi(surface,'/api/stats');
  if(!surfaceCurrent(surface))return;
  showManagementBody();
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
  /* 一行都没有时整张表不出现，只留 Empty State：Geist Table 的判据是空态渲染在表格
     外面，留一张只有列头的空表等于让人对着两个列名找不存在的行。 */
  const table=(head,rows,empty)=>rows?`<div class="insighttable"><div class="insighttablehead">${head.map(value=>`<span>${value}</span>`).join('')}</div>${rows}</div>`:empty;
  const tagsTable=`<ol class="insightranking">${d.top_tags.map((t,index)=>`<li><button type="button" class="insightrankrow" data-k="${esc(t.k)}">
    <span class="insightrankpos">${index+1}</span><span>${esc(tagLabel(t.k))}</span><b>${t.n.toLocaleString()}</b></button></li>`).join('')}</ol>`;
  const recentTable=table(['作品','观看证据'],d.recent.map(row=>{
    const real=row.duration?Math.min(row.play_seconds/row.duration,1)*100:0;
    const reached=(row.max_reached||0)*100;
    const note=row.kind==='online'?'在线直接观看':(real<reached-25?'快进扫过':(row.o_count?`高潮 ${row.o_count}`:'正常观看'));
    return `<div class="insighttablerow"><span>${esc((row.creator?row.creator+' · ':'')+row.name)}</span>
      <b>真实 ${real.toFixed(0)}% · 到达 ${reached.toFixed(0)}% · ${note}</b></div>`}).join(''),
    `<div class="insightempty">${emptyStateHtml('history','还没有观看记录','开始播放后，这里会显示最近的真实观看证据。')}</div>`);
  const sourceTable=table(['标签来源','覆盖视频'],d.tag_source.map(row=>`<div class="insighttablerow"><span>${esc(row.k)}</span>
    <b>${row.n.toLocaleString()} 条 · ${row.assets.toLocaleString()} 个视频</b></div>`).join(''),
    `<div class="insightempty">${emptyStateHtml('tags','还没有标签来源','刮削或手动打标之后，这里会显示每个来源覆盖了多少视频。')}</div>`);
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
            </div>
          <div class="insightvisual">${locationRows}</div></div>
        <div id="stats-detail-viewing" role="tabpanel" data-stats-detail="viewing" class="insightdetailbody" hidden>
          <div class="insightcopy"><span>观看</span><h2>${cs.played.toLocaleString()}</h2><b>个作品有播放记录</b>
            <p>累计 ${hrs(cs.play_seconds)}</p></div>
          <div class="insightfacts">${kv('馆藏观看',cs.library_played.toLocaleString())}${kv('在线直接观看',cs.online_played.toLocaleString())}
            ${kv('高潮计数',cs.o_total.toLocaleString())}${kv('快进扫过',cs.skimmed.toLocaleString())}
            ${kv('明确不喜欢',cs.dislike.toLocaleString())}${kv('看过了',cs.seen.toLocaleString())}${kv('回收站',cs.trash.toLocaleString())}</div></div>
        <div id="stats-detail-coverage" role="tabpanel" data-stats-detail="coverage" class="insightdetailbody" hidden>
          <div class="insightcopy"><span>内容标签覆盖</span><h2>${coverage}%</h2><b>${d.tag_cov.toLocaleString()} / ${a.videos.toLocaleString()}</b>
            </div>
          <div class="insightvisual">${metric('有创作者',a.creator,a.videos)}${metric('有番号',a.code,a.videos)}
            ${metric('有厂牌',a.studio,a.videos)}${metric('已抽帧',a.thumb,a.videos)}${metric('已探测时长',a.duration,a.videos)}</div></div>
        <div id="stats-detail-storage" role="tabpanel" data-stats-detail="storage" class="insightdetailbody" hidden>
          <div class="insightcopy"><span>使用空间</span><h2>${storage.measured}</h2><b>个卷已取得容量</b>
            </div>
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
  window.scrollTo({top:0,behavior:'smooth'});
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

/* 外链是别人服务器上的东西，会在我们不知情的时候烂掉——实测 719 条里 152 条打不开，
   而它们在资料页上和好链接长得一模一样，只有点下去才知道。所以检查要能随时重跑，
   不是一次性脚本。放在资源同步上面：两块都是「把库里的记录和外部现实对齐」。 */
function linkManagerMarkup(){
  return `<section class="resourcesync" id="link-manager" aria-labelledby="linkManagerTitle">
    <h2 id="linkManagerTitle">链接管理</h2>
    <div class="resourcesyncbox" data-geist-fieldset>
      <div class="resourcesyncbody geist-fieldset-content">${fieldsetTitle('linkBoxTitle','外链与实体')}
      <div id="linkSummary" class="linksummary"></div></div>
      <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer>
      <button class="resourceaction" type="button" id="linkCheck">${icon('refresh-cw')}<span>检查死链</span></button></div></div>
    <div id="linkCheckResult" aria-live="polite"></div></section>`;
}
async function wireLinkManager(){
  const button=$('#linkCheck'),result=$('#linkCheckResult'),summary=$('#linkSummary');
  if(!button||!result)return;
  const active=()=>location.pathname==='/data-cleanup'&&!$('#stats').hidden&&document.body.contains(result);
  /* `官网 · 事务所` 里的间隔点会和「按类型」那行的分隔点撞在一起，读出来是
     「社媒 373 · 官网 · 事务所 224」——分不清哪个数字属于哪一类。 */
  const KINDS={official:'官网/事务所',social:'社媒',catalog:'资料库',source_reference:'来源记录'};
  try{
    const info=await api('/api/links');
    /* 每一类各占一格。挤成一行时标签和数字之间只剩间隔点，数字归谁全靠猜。 */
    const stat=(label,value,note='')=>`<div><span>${esc(label)}</span><b>${value}</b>${
      note?`<small>${note}</small>`:''}</div>`;
    const kinds=Object.entries(info.by_kind||{})
      .map(([kind,count])=>stat(KINDS[kind]||kind,Number(count).toLocaleString())).join('');
    const hosts=(info.top_hosts||[]).slice(0,3).map(([host,count])=>`${esc(host)} ${count}`).join(' · ');
    summary.innerHTML=`<div class="linkstats">
      ${stat('链接',info.total.toLocaleString(),`分布在 ${info.entities.toLocaleString()} 个实体上`)}
      ${kinds}</div>
      ${hosts?`<div class="linkhosts"><span>最多的站点</span><b>${hosts}</b></div>`:''}`;
  }catch(error){summary.innerHTML=noteHtml(error.message,{variant:'error',label:'读取失败'})}

  const row=item=>`<tr><td>${esc(item.entity)}</td><td>${esc(KINDS[item.link_kind]||item.link_kind)}</td>
    <td>${esc(item.label||'')}</td><td class="linknote">${esc(item.note)}</td>
    <td class="linkurl"><a href="${esc(item.url)}" target="_blank" rel="noreferrer" data-middle-truncate>${esc(item.url)}</a></td></tr>`;
  const table=(title,items,hint)=>items.length?`<div class="linkgroup"><h4>${esc(title)} <b>${items.length}</b></h4>
    <p>${esc(hint)}</p><div class="linktablewrap"><table class="linktable"><thead><tr><th>实体</th><th>类型</th><th>标签</th><th>结果</th><th>地址</th></tr></thead><tbody>${items.map(row).join('')}</tbody></table></div></div>`:'';

  const render=payload=>{
    const running=payload.status==='running';
    const done=payload.status==='complete';
    button.innerHTML=`${icon('refresh-cw')}<span>${running?'检查中':done?'重新检查':'检查死链'}</span>`;
    setActionBusy(button,running);
    if(payload.status==='idle'){result.innerHTML='';return}
    if(payload.status==='failed'){result.innerHTML=noteHtml(payload.error||'检查失败',{variant:'error',label:'检查失败'});return}
    const progress=running?loadingDotsHtml(`已检查 ${payload.checked.toLocaleString()} / ${(payload.total||0).toLocaleString()} 条`)
      +(payload.total?progressHtml('已检查链接',payload.checked,payload.total):''):'';
    /* gone 和 unclear 必须分开摆：`linktr.ee` 回 403 是挡爬虫、`x.com` 回 500 是临时错误，
       链接本身好好的。混成一张表会让人顺手把好链接一起删掉。 */
    const gone=table('已失效',payload.gone||[],'上游明确回 404／410，页面确实没了。');
    const unclear=table('取不到',payload.unclear||[],'一次访问没成功，但不等于没了：有的站挡爬虫，有的是临时错误。不会被删除，下次检查会重试。');
    const apply=(done&&(payload.gone||[]).length)?`<div class="resourceapplyrow"><p>删除前会逐条重验一次；此操作不可撤销。</p>
      <button class="resourceaction resourcedanger" type="button" id="linkPrune">删除 ${payload.gone.length} 条失效链接</button></div>`:'';
    const clean=(done&&!(payload.gone||[]).length&&!(payload.unclear||[]).length)?'<p class="resourcesyncok">全部链接都能打开。</p>':'';
    result.innerHTML=`<div class="resourcepanel">${progress}${gone}${unclear}${apply}${clean}</div>`;
    $('#linkPrune')?.addEventListener('click',async event=>{
      const control=event.currentTarget;
      if(!confirm(`删除 ${payload.gone.length} 条已失效链接？删除前会逐条重验，但删除本身不可撤销。`))return;
      setActionBusy(control);
      control.innerHTML=`${spinnerHtml('正在重验')}<span>正在重验并删除…</span>`;
      try{
        const out=await api('/api/links/prune',{method:'POST',body:JSON.stringify({confirm:true,check_id:payload.check_id,background:true})});
        sessionStorage.setItem('peach-link-prune-job',out.job_id);
        if(active())void wirePruneProgress();
      }catch(error){if(active()){result.insertAdjacentHTML('beforeend',noteHtml(error.message,{variant:'error',label:'删除失败'}));void wirePruneProgress()}}
    });
  };

  const ui=await import('/dist/peach-ui.js');
  let watching=0;
  const poll=()=>{const generation=++watching;return ui.watchJob({
    active:()=>active()&&watching===generation,
    read:signal=>api('/api/links/check',{signal,method:'POST',body:JSON.stringify({status_only:true})}),
    render,disconnected:()=>{result.innerHTML=noteHtml('暂时无法读取进度，正在重新连接…',{label:'任务状态'})}})};
  button.onclick=async()=>{
    if(button.getAttribute('aria-busy')==='true')return;
    setActionBusy(button);
    try{const payload=await api('/api/links/check',{method:'POST',body:JSON.stringify({restart:true})});
      if(!active())return;render(payload);void poll();
    }catch(error){if(active()){result.innerHTML=noteHtml('暂时无法确认启动结果，正在读取任务状态…',{label:'任务状态'});void poll()}}
  };
  void poll();
  void wirePruneProgress();
}
function wirePruneProgress(){
  return wireOperationProgress({host:$('#link-manager'),path:'/api/links/prune',key:'peach-link-prune-job',title:'正在重验并删除失效链接…',
    busy:running=>{const button=$('#linkPrune');if(button){setActionBusy(button,running);if(!running)button.textContent='重试删除失效链接'}},
    complete:out=>{$('#linkCheckResult').innerHTML=noteHtml(`已删除 ${out.removed} 条；保留 ${out.recovered} 条恢复的链接。`,{label:'完成'})}});
}
function resourceSyncMarkup(){
  return `<section class="resourcesync" id="resource-sync" aria-labelledby="resourceSyncTitle">
    <h2 id="resourceSyncTitle">资源同步</h2>
    <div class="resourcesyncbox" data-geist-fieldset>
      <div class="resourcesyncbody geist-fieldset-content">${fieldsetTitle('resourceBoxTitle','网盘与账本')}
      <p>网盘上已删除的条目进入回收站；只清理没有在用的预览与播放缓存。</p></div>
      <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer>
      <button class="resourceaction" type="button" id="resourceScan">${icon('refresh-cw')}<span>扫描差异</span></button></div></div>
    <div id="resourceSyncResult" aria-live="polite"></div></section>`;
}
async function wireResourceSync(){
  const scan=$('#resourceScan'),result=$('#resourceSyncResult');
  if(!scan||!result)return;
  const active=()=>location.pathname==='/data-cleanup'&&!$('#stats').hidden&&document.body.contains(result);
  const setBusy=(busy,done=false)=>{
    setActionBusy(scan,busy);
    scan.innerHTML=`${icon('refresh-cw')}<span>${busy?'扫描中':done?'重新扫描':'扫描差异'}</span>`;
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
      <div><span>待同步</span><b>${Number(payload.missing||0).toLocaleString()} 项</b></div></div>
      <div class="resourceapplyrow">${hasChanges?`<button class="resourceaction resourcedanger" type="button" id="resourceApply">同步并清理</button>`:
        '<p class="resourcesyncok">账本与已挂载来源一致，没有孤立缓存。</p>'}</div></div>`;
    $('#resourceApply')?.addEventListener('click',async event=>{
      const button=event.currentTarget;
      if(!confirm(`把 ${payload.missing||0} 项移入回收站，并清理 ${cache.files||0} 个可重建缓存？`))return;
      setActionBusy(button);
      button.innerHTML=`${spinnerHtml('正在应用')}<span>正在重新核对并应用…</span>`;
      try{
        const applied=await api('/api/resource-sync/apply',{method:'POST',body:JSON.stringify({confirm:true,clean_cache:true,scan_id:payload.scan_id||'',background:true})});
        sessionStorage.setItem('peach-resource-apply-job',applied.job_id);
        if(active())void wireResourceApplyProgress();
      }catch(error){
        setActionBusy(button,false);
        button.innerHTML=`${icon('refresh-cw')}<span>重试同步</span>`;
        result.insertAdjacentHTML('beforeend',noteHtml(error.message,{variant:'error',label:'同步失败'}));if(active())void wireResourceApplyProgress()}
    });
  };
  const followScan=async payload=>{
    setBusy(true);result.innerHTML=`<p class="resourcescanning">${loadingDotsHtml('正在后台核对网盘元数据，不会读取视频内容。')}</p>`;
    try{
      if(!payload){try{payload=await api('/api/resource-sync/scan',{method:'POST',body:JSON.stringify({background:true,restart:true})})}
        catch(error){if(active())result.innerHTML=noteHtml('暂时无法确认启动结果，正在读取任务状态…',{label:'任务状态'})}}
      const ui=await import('/dist/peach-ui.js');
      await ui.watchJob({active,
        read:signal=>api('/api/resource-sync/scan',{signal,method:'POST',body:JSON.stringify({background:true,status_only:true})}),
        render:state=>{payload=state;if(state.status==='running'){
          result.innerHTML=loadingDotsHtml(`后台扫描中：已完成 ${state.completed_sources||0}/${state.total_sources||0} 个来源`)
            +(state.total_sources?progressHtml('已扫描来源',state.completed_sources||0,state.total_sources):'')}},
        disconnected:()=>{result.innerHTML=noteHtml('暂时无法读取进度，正在重新连接…',{label:'任务状态'})}});
      if(payload.status==='failed')throw new Error(payload.error||'后台扫描失败');
      if(payload.status==='idle')throw new Error('任务尚未启动，请重试扫描');
      if(!active())return;
      render(payload);
    }
    catch(error){result.innerHTML=noteHtml(error.message,{variant:'error',label:'扫描失败'})}
    finally{setBusy(false,true)}
  };
  scan.onclick=()=>{if(scan.getAttribute('aria-busy')!=='true')void followScan(null)};
  const ui=await import('/dist/peach-ui.js');
  void ui.watchJob({active,once:true,
    read:signal=>api('/api/resource-sync/scan',{signal,method:'POST',body:JSON.stringify({background:true,status_only:true})}),
    render:existing=>{if(existing.status==='running')void followScan(existing)},
    disconnected:()=>{result.innerHTML=noteHtml('暂时无法读取进度，正在重新连接…',{label:'任务状态'})}});
  void wireResourceApplyProgress();
}
function wireResourceApplyProgress(){
  return wireOperationProgress({host:$('#resource-sync'),path:'/api/resource-sync/apply',key:'peach-resource-apply-job',title:'正在核对来源、同步并清理缓存…',
    busy:running=>{const button=$('#resourceApply');if(button){setActionBusy(button,running);if(!running)button.textContent='同步并清理'}},
    complete:out=>{$('#resourceSyncResult').innerHTML=noteHtml(`已把 ${out.moved_to_trash} 项移入回收站，清理 ${out.cache_removed} 个缓存，释放 ${fmtSize(out.bytes_reclaimed||0)}。`,{label:'完成'})}});
}
/* 旧直达 URL 仍然可用，落点跟着面板一起搬到数据管理。 */
async function openResourceSync(push=true){
  if(push||location.pathname==='/resource-sync')route('/data-cleanup#resource-sync',!push);
  await openDataCleanup(false);
  $('#resource-sync')?.scrollIntoView({block:'start'});
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
/* 站点头像：先垫首字母，再叠 favicon；站点自己的 favicon 取不到就换 Google 的
   代理图，两条都取不到才把 <img> 拿掉，露出底下的首字母。 */
function siteAvatar(name,domain,title=''){
  return `<span class="tasteavatar tastesite"${title?` title="${esc(title)}"`:''}>`+
    `<span class="ini">${esc(String(name).slice(0,1).toUpperCase())}</span>`+
    `<img src="${esc(faviconUrl('https://'+domain))}" alt="" loading="lazy" referrerpolicy="no-referrer" `+
    `${imageFallbackAttrs({fallbacks:[faviconFallbackUrl(domain)]})}></span>`;
}
const tasteRankRows=(rows,kind,empty='暂无足够证据',visual='')=>rows.length?rows.map((row,index)=>{
    const clickable=kind&&row.peach_items>0;
    const detail=row.web_visits!=null
      ?`${row.web_visits?`浏览 ${row.web_visits}`:''}${row.web_visits&&row.peach_items?' · ':''}${row.peach_items?`Peach ${row.peach_items}`:''}`
      :`${Number(row.score||row.visits||0).toLocaleString()}`;
    // 两级图都由 `/api/taste` 说了算：实体图看 `has_image`，代表作头像看 `has_avatar`。
    const ref=row.entity_id?{id:row.entity_id,has_image:row.has_image}:null,
      rep=row.has_avatar?row.representative_asset_id||null:null;
    const sourceDomain=String(row.source_domain||'');
    const media=visual==='domain'
      ?siteAvatar(row.name,row.name)
      :visual==='creator'&&!ref&&!rep&&sourceDomain
        ?siteAvatar(row.name,sourceDomain,`来源：${sourceDomain}`)
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
function tasteAnalysisSection(analysis){
  if(!analysis||!analysis.headline)return '';
  const confidence=analysis.confidence||{};
  const points=(analysis.points||[]).map(point=>`<div class="tasteinsight">
    <span>${esc(point.label)}</span><b>${esc(point.text)}</b></div>`).join('');
  //: 探索标签和下一步动作都是「点进去就能做的事」，排成同一列表；
  //: 前者带 data-taste-kind 走信号面板，后者带 data-taste-route 直接换页。
  const leads=[...(analysis.explore||[]).map(item=>
      ({attrs:`data-taste-kind="tag" data-taste-name="${esc(item.tag)}"`,title:item.title,detail:item.detail})),
    ...(analysis.next_steps||[]).map(item=>
      ({attrs:`data-taste-route="${esc(item.route)}"`,title:item.title,detail:item.detail}))]
    .map(lead=>`<button type="button" class="tastelead" ${lead.attrs}>
      <span><b>${esc(lead.title)}</b><small>${esc(lead.detail)}</small></span>${icon('chevron-right')}</button>`).join('');
  return `<section class="insightpanel tasteleads">
      <header><div><h3>口味总结</h3><p>${esc(analysis.headline)}</p></div>
        <span class="tasteconfidence ${esc(confidence.level||'early')}">${esc(confidence.label||'仍在学习')}</span></header>
      <div class="insightpanelbody">
        ${points?`<div class="tasteinsights">${points}</div>`:''}
        <div class="tasteleadlist">${leads||emptyStateHtml('search','还没有可探索的入口','馆藏里暂时没有对得上浏览信号的标签。')}</div>
      </div></section>`;
}
function renderTaste(d){
  const s=d.summary||{},coverage=d.coverage||{},rank=d.rankings||{},storage=d.storage||{};
  const summary=(label,value,sub='')=>`<div class="tastesummary"><span>${label}</span><b>${value}</b>${sub?`<small>${sub}</small>`:''}</div>`;
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
      ${summary('浏览候选',gapRows.length.toLocaleString())}
      ${summary('私有导出',Number(storage.exports||0).toLocaleString(),fmtSize(storage.bytes||0))}</div>
    <div class="tastesummaries" data-taste-summary="peach"${tasteEvidence==='peach'?'':' hidden'}>
      ${summary('Peach 看过',Number(s.peach_items||0).toLocaleString(),tasteHours(s.peach_seconds||0))}
      ${summary('喜欢',Number(s.liked||0).toLocaleString())}
      ${summary('不合口味',Number(s.disliked||0).toLocaleString())}
      ${summary('有标签',Number(coverage.tagged||0).toLocaleString())}</div>
    <section class="tastehero" data-taste-evidence-panel="browser"${tasteEvidence==='browser'?'':' hidden'}>
      <div class="insightcopy"><span>浏览器画像</span><h2>${Number(s.history_visits||0).toLocaleString()}</h2><b>条聚合访问证据</b>
        <small>${d.updated_at?`更新于 ${tasteDate(d.updated_at)}`:'尚未采集浏览记录'}</small></div>
      <div class="tastebars">${categoryBars}</div></section>
    <section class="tastehero" data-taste-evidence-panel="peach"${tasteEvidence==='peach'?'':' hidden'}>
      <div class="insightcopy"><span>Peach 观看</span><h2>${Number(s.peach_items||0).toLocaleString()}</h2><b>个作品有内部行为证据</b>
        </div>
      <div class="insightvisual">
        ${coverageMetric('有标签',Number(coverage.tagged||0).toLocaleString(),`${coverage.untagged||0} 项待补`,coverage.tagged||0,(coverage.tagged||0)+(coverage.untagged||0))}
        ${coverageMetric('有身份',Number(coverage.identified||0).toLocaleString(),`${coverage.unidentified||0} 项待补`,coverage.identified||0,(coverage.identified||0)+(coverage.unidentified||0))}
      </div></section>
    ${tasteAnalysisSection(d.analysis)}
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
    <section class="insightpanel tastesources"><header><div><h3>数据源</h3></div></header>
      <div class="insightpanelbody"><div>${sourceRows||emptyStateHtml('database','还没有数据源','导入或读取浏览记录后，这里会列出已采集设备。')}</div></div></section>
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
  /* 总结里的下一步动作按路径走，派发仍旧交给 ROUTES：在这里比对一遍路径字符串，
     就又多出一处会和那张表不一致的知识。 */
  root.querySelectorAll('[data-taste-route]').forEach(button=>button.onclick=()=>{
    route(button.dataset.tasteRoute);restoreRoute()});
  root.querySelector('[data-taste-refresh]').onclick=async e=>{const button=e.currentTarget;
    const oldButton=button.innerHTML;
    setActionBusy(button);
    button.innerHTML=`${spinnerHtml('正在读取')}<span>读取中…</span>`;
    stateEl.textContent='';
    try{const result=await api('/api/taste/refresh',{method:'POST',body:JSON.stringify({window:tasteWindow,background:true})});
      sessionStorage.setItem('peach-taste-job',result.job_id);
      if(button.isConnected)void wireTasteProgress()}
    catch(error){stateEl.textContent=error.message||'读取失败';setActionBusy(button,false);
      button.innerHTML=oldButton;if(button.isConnected)void wireTasteProgress()}};
  void wireTasteProgress();
  root.querySelector('[data-taste-import]').onclick=()=>file.click();
  file.onchange=async()=>{const selected=file.files[0];if(!selected)return;stateEl.textContent=`正在导入 ${selected.name}…`;
    try{const response=await fetch('/api/taste/import',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Peach-Filename':encodeURIComponent(selected.name)},body:selected});
      const payload=await response.json().catch(()=>null);if(!response.ok)throw new Error(payload?.error||`导入失败（${response.status}）`);
      tasteWindow='all';tasteCacheSet('all',payload.dashboard);renderTaste(payload.dashboard);actionReceipt('已导入口味数据')}
    catch(error){stateEl.textContent=error.message||'导入失败';actionFailure('导入口味数据',error)}};
  root.querySelectorAll('[data-taste-kind]').forEach(button=>button.onclick=()=>openTasteSignal(button.dataset.tasteKind,button.dataset.tasteName));
  root.querySelectorAll('[data-taste-remove]').forEach(button=>button.onclick=async()=>{
    if(!confirm('从口味分析中移除这个数据源？原始导出文件会保留。'))return;
    button.disabled=true;stateEl.textContent='正在移除…';
    try{const result=await api('/api/taste/source',{method:'POST',body:JSON.stringify({operation:'remove',source_key:button.dataset.tasteRemove,window:tasteWindow})});
      tasteCacheSet(tasteWindow,result.dashboard);renderTaste(result.dashboard);actionReceipt('已移除口味数据源')}
    catch(error){stateEl.textContent=error.message||'移除失败';button.disabled=false}});
}
async function openTaste(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  state={...state,creator:'',studio:'',tag:'',tag_match:'all',len:'',dur_min:'',dur_max:'',orient:'',state:'',q:'',jav:''};
  $('#q').value='';
  if(push)route('/taste');
  const surface=claimSurface('/taste');
  showManagementBody();
  const cachedEntry=tasteCache.get(tasteWindow),cached=cachedEntry?.dashboard;
  const cacheFresh=cached&&Date.now()-cachedEntry.at<TASTE_CACHE_FRESH_MS;
  if(cached)renderTaste(cached);
  else showManagementBody({placeholder:managementPlaceholder('/taste')});
  if(!cacheFresh){
    const request=++tasteRequest;
    const requestedWindow=tasteWindow;
    void surfaceApi(surface,'/api/taste?window='+requestedWindow).then(data=>{
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
    <label>名称<input class="geist-input" name="name" maxlength="80" value="${esc(mix.title)}" required></label>
    <button class="geist-button primary" type="submit">保存 ${mix.items.length} 个视频</button><span data-playlist-state></span></form>`});
  dialog.querySelector('form').onsubmit=async event=>{event.preventDefault();
    const form=event.currentTarget,stateEl=form.querySelector('[data-playlist-state]');
    try{const result=await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'create',name:new FormData(form).get('name'),asset_ids:mix.items.map(item=>item.id),source_kind:'mix',source_seed_asset_id:mix.seedId})});
      dialog.close();actionReceipt('已保存为播放列表');await openPlaylist(result.playlist.id,result.playlist.current_asset_id,true)
    }catch(error){stateEl.textContent=error.message||'保存失败'}
  };
  dialog.querySelector('input').select();
}
async function openAddToPlaylist(item){
  const lists=(await api('/api/playlists')).items||[];
  const rows=lists.map(list=>`<button type="button" class="playlistpickrow" data-add-playlist="${list.id}"><span>${esc(list.name)}</span><small>${list.item_count} 个视频</small></button>`).join('');
  const dialog=playlistDialog({title:'加入播放列表',body:`<form class="playlistcreate" data-create-playlist>
      <label>新播放列表<input class="geist-input" name="name" maxlength="80" placeholder="输入名称" required></label><button class="geist-button primary" type="submit">新建并加入</button><span data-playlist-state></span></form>
    <div class="playlistpicklist">${rows||'<p class="empty">还没有播放列表</p>'}</div>`});
  const finish=async body=>{const stateEl=dialog.querySelector('[data-playlist-state]');
    try{await api('/api/playlist',{method:'POST',body:JSON.stringify(body)});dialog.close();actionReceipt('已加入播放列表')}
    catch(error){stateEl.textContent=error.message||'加入失败'}};
  dialog.querySelector('form').onsubmit=event=>{event.preventDefault();finish({action:'create',name:new FormData(event.currentTarget).get('name'),asset_ids:[item.id]})};
  dialog.querySelectorAll('[data-add-playlist]').forEach(button=>button.onclick=()=>finish({action:'add',id:+button.dataset.addPlaylist,asset_ids:[item.id]}));
}
async function movePlaylistItem(queue,index,delta,currentId){
  if(queue?.kind!=='playlist')return;
  const target=index+delta;if(target<0||target>=queue.items.length)return;
  const ids=queue.items.map(item=>item.id);[ids[index],ids[target]]=[ids[target],ids[index]];
  await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'reorder',id:queue.playlistId,asset_ids:ids})});
  await openPlaylist(queue.playlistId,currentId,false);actionReceipt('已调整播放顺序');
}
async function removePlaylistItem(queue,assetId,currentId){
  if(queue?.kind!=='playlist'||!confirm('从播放列表移出这个视频？'))return;
  const result=await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'remove',id:queue.playlistId,asset_id:assetId})});
  if(!result.playlist.items.length){await openPlaylists(true);return}
  const next=result.playlist.items.some(item=>item.id===currentId)?currentId:result.playlist.current_asset_id;
  await openPlaylist(queue.playlistId,next,false);actionReceipt('已移出播放列表');
}
async function openPlaylists(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/playlists');
  const surface=claimSurface('/playlists');
  showManagementBody({manage:false,placeholder:managementPlaceholder('/playlists')});
  const data=await surfaceApi(surface,'/api/playlists');
  if(!surfaceCurrent(surface))return;
  showManagementBody({manage:false});
  const cards=(data.items||[]).map(list=>{const resume=list.current_asset_id||list.preview_asset_id;
    const poster=list.preview_asset_id?`<img src="/poster?id=${list.preview_asset_id}&c=4" alt="" loading="lazy" data-drop="self">`:'';
    return `<article class="playlistcard" data-playlist-card="${list.id}"><button class="playlistcover" data-open-playlist="${list.id}" ${resume?'':'disabled'}>${poster}<span>${list.item_count} 个视频</span></button>
      <div class="playlistmeta"><input class="geist-input" data-playlist-name maxlength="80" value="${esc(list.name)}" aria-label="播放列表名称"><small>${list.source_kind==='mix'?'由 Mix 保存':'手动播放列表'}</small></div>
      <div class="playlistactions"><button data-rename-playlist="${list.id}">保存名称</button><button data-open-playlist="${list.id}" ${resume?'':'disabled'}>继续播放</button><button class="danger" data-delete-playlist="${list.id}">删除</button></div></article>`}).join('');
  $('#stats').innerHTML=`<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><form class="playlistcreate" id="newPlaylist"><label>新播放列表<input class="geist-input" name="name" maxlength="80" placeholder="输入名称" required></label><button class="geist-button primary" type="submit">新建</button><span data-playlist-state></span></form></header><div class="playlistcards">${cards||emptyState('playlist','还没有播放列表','保存 Mix 或新建列表后，会在这里按自己的顺序继续播放。')}</div></section>`;
  $('#newPlaylist').onsubmit=async event=>{event.preventDefault();const form=event.currentTarget;
    try{await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'create',name:new FormData(form).get('name'),asset_ids:[]})});await openPlaylists(false);actionReceipt('已新建播放列表')}
    catch(error){form.querySelector('[data-playlist-state]').textContent=error.message||'新建失败'}};
  $('#stats').querySelectorAll('[data-open-playlist]').forEach(button=>button.onclick=()=>{
    const list=data.items.find(item=>item.id===+button.dataset.openPlaylist),resume=list?.current_asset_id||list?.preview_asset_id;
    if(resume)openPlaylist(list.id,resume,true)});
  $('#stats').querySelectorAll('[data-rename-playlist]').forEach(button=>button.onclick=async()=>{const card=button.closest('[data-playlist-card]'),input=card.querySelector('[data-playlist-name]');
    try{await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'rename',id:+button.dataset.renamePlaylist,name:input.value})});await openPlaylists(false);actionReceipt('已重命名播放列表')}
    catch(error){actionFailure('重命名播放列表',error)}});
  $('#stats').querySelectorAll('[data-delete-playlist]').forEach(button=>button.onclick=async()=>{if(!confirm('删除这个播放列表？视频本身不会删除。'))return;
    try{await api('/api/playlist',{method:'POST',body:JSON.stringify({action:'delete',id:+button.dataset.deletePlaylist})});await openPlaylists(false);actionReceipt('已删除播放列表')}
    catch(error){actionFailure('删除播放列表',error)}});
  window.scrollTo({top:0,behavior:'smooth'});
}

let reviewData=null,reviewRuntime=null,reviewCategory='metadata_fields';
/* 主体是实体而不是单条作品的复核分类。值就是实体 kind。 */
const ENTITY_REVIEW_CATEGORIES={creator_tags:'creator',western_identity:'creator'};
const REVIEW_LABELS={metadata_fields:'元数据字段',creator_tags:'创作者标签',studio_logos:'厂牌 Logo',performer_avatars:'女优头像',western_identity:'西方身份回配',code_creators:'番号目录存疑',fc2_markings:'FC2 评论标记',fc2_similarity:'FC2 跨号相似',video_endcards:'片尾/出处证据',media_failure:'媒体失败'};

/* 数据管理是「库里已经有的东西怎么收拾」的唯一入口：广告、重复、空目录，
   加上复核队列、回收站和高清版。它们此前散在管理菜单和统计页两处，
   统计页因此还挂着两块跟统计无关的面板。 */
const DATA_MANAGEMENT_ENTRIES=[
  ['review','人工复核','查看候选'],
  ['trash','回收站','查看回收站'],
  ['quality','高清版','查看高清版'],
];

async function openDataCleanup(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/data-cleanup');
  const surface=claimSurface('/data-cleanup');
  showManagementBody({placeholder:managementPlaceholder('/data-cleanup')});
  const [junk,duplicates,sources]=await Promise.all([
    surfaceApi(surface,'/api/ads?limit=1'),surfaceApi(surface,'/api/duplicates?limit=1'),
    surfaceApi(surface,'/api/sources'),
  ]);
  if(!surfaceCurrent(surface))return;
  paintManageLede();
  /* 三个「· 在线」徽章换成一行来源名：卡片要说的是这次会扫哪几个来源，
     来源在线与否是资源同步那一块的读数，在这里只有离线时才改变结论。 */
  const scanSources=(sources.sources||[]).filter(source=>['local','115','pikpak'].includes(source.location));
  const sourceName=source=>esc(LOC[source.location]||source.location);
  const online=scanSources.filter(source=>source.online),offline=scanSources.filter(source=>!source.online);
  const sourceLine=[online.map(sourceName).join(' · '),
    offline.length?`${offline.map(sourceName).join(' · ')} 离线`:''].filter(Boolean).join(' · ');
  const junkCounts=junk.counts||{};
  const junkBreakdown=[...JUNK_KIND_OPTIONS.filter(([key])=>key&&Number(junkCounts[key])>0)
    .map(([key,label])=>`${esc(label)} ${Number(junkCounts[key]).toLocaleString()}`),
    ...(Number(junk.dismissed_total)>0?[`已忽略 ${Number(junk.dismissed_total).toLocaleString()}`]:[])].join(' · ');
  $('#stats').innerHTML=`<div class="cleanuppage"><div class="cleanupgrid">
    <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanupJunkTitle">
      <div class="geist-fieldset-content">${fieldsetTitle('cleanupJunkTitle','垃圾文件')}
        <strong>${Number(junk.pending_total||0).toLocaleString()} 个待判断</strong>
        <p class="cleanupmeta">${junkBreakdown}</p></div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" data-cleanup-open="junk">查看垃圾文件</button></footer>
    </section>
    <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanupDupTitle">
      <div class="geist-fieldset-content">${fieldsetTitle('cleanupDupTitle','重复文件')}
        <strong>${Number(duplicates.total||0)
          ?`${Number(duplicates.total).toLocaleString()} 组 · ${Number(duplicates.files||0).toLocaleString()} 个文件`
          :'没有重复内容'}</strong>
        <p class="cleanupmeta">${Number(duplicates.total||0)?`可回收 ${fmtSize(duplicates.reclaimable||0)}`:''}</p></div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" data-cleanup-open="duplicates">查看重复文件</button></footer>
    </section>
    <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanupEmptyTitle">
      <div class="geist-fieldset-content">${fieldsetTitle('cleanupEmptyTitle','空文件夹')}
        <strong>${online.length.toLocaleString()} 个来源可扫描</strong>
        <p class="cleanupmeta">${sourceLine}</p><p class="cleanupstate" aria-live="polite"></p></div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" class="danger" data-cleanup-empty>${icon('trash')}<span>删除空文件夹</span></button></footer>
    </section>
    ${DATA_MANAGEMENT_ENTRIES.map(([section,title,label])=>`
    <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanup-${section}-title">
      <div class="geist-fieldset-content">${fieldsetTitle(`cleanup-${section}-title`,title)}
        <strong data-cleanup-count="${section}">—</strong>
        <p class="cleanupmeta" data-cleanup-meta="${section}"></p></div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" data-cleanup-go="${section}">${esc(label)}</button></footer>
    </section>`).join('')}
  </div>
  ${linkManagerMarkup()}
  ${resourceSyncMarkup()}</div>`;
  $('#stats').querySelector('[data-cleanup-open="junk"]').onclick=()=>openManage('ads');
  $('#stats').querySelector('[data-cleanup-open="duplicates"]').onclick=()=>openDuplicates();
  $('#stats').querySelectorAll('[data-cleanup-go]').forEach(button=>
    button.onclick=()=>openManage(button.dataset.cleanupGo));
  paintDataManagementCounts();
  const emptyButton=$('#stats').querySelector('[data-cleanup-empty]');
  emptyButton.onclick=async()=>{
    if(!confirm('删除所有已挂载资源来源中的空文件夹？来源根目录不会删除。'))return;
    const status=$('#stats').querySelector('.cleanupstate'),original=emptyButton.innerHTML;
    setActionBusy(emptyButton);emptyButton.innerHTML=`${spinnerHtml('正在删除空文件夹')}<span>正在清理</span>`;
    status.textContent='正在自底向上检查已挂载来源…';
    try{
      const result=await api('/api/data-cleanup/empty-folders',{method:'POST',body:'{}'});
      status.textContent=`已检查 ${Number(result.scanned||0).toLocaleString()} 个目录，删除 ${Number(result.removed||0).toLocaleString()} 个${result.errors?`，${Number(result.errors).toLocaleString()} 个读取或删除失败`:''}。`;
      if(result.errors)actionFailure('空文件夹清理',new Error(`${result.errors} 个目录处理失败`));
      else actionReceipt(`已删除 ${Number(result.removed||0).toLocaleString()} 个空文件夹`);
    }catch(error){status.textContent=error.message||'空文件夹清理失败';actionFailure('空文件夹清理',error)}
    finally{setActionBusy(emptyButton,false);emptyButton.innerHTML=original}
  };
  await wireLinkManager();
  await wireResourceSync();
}

/* 计数各自失败各自算：复核接口出错不该把回收站那张卡也变成「—」。
   第二行是同一份 payload 里已经有的分项，不额外发请求。 */
async function paintDataManagementCounts(){
  const write=(section,text,meta='')=>{
    const root=$('#stats');
    const count=root?.querySelector(`[data-cleanup-count="${section}"]`);
    if(count)count.textContent=text;
    const line=root?.querySelector(`[data-cleanup-meta="${section}"]`);
    if(line)line.textContent=meta;
  };
  const fill=async(section,load)=>{
    try{const [text,meta='']=await load();write(section,text,meta)}
    catch(_error){write(section,'读取失败')}
  };
  await Promise.all([
    fill('review',async()=>{
      const data=await api('/api/review?counts=1');
      const counts=Object.entries(data.counts||{})
        .map(([key,value])=>[REVIEW_LABELS[key]||key,Number(value)||0])
        .filter(([,value])=>value>0).sort((a,b)=>b[1]-a[1]);
      const total=counts.reduce((sum,[,value])=>sum+value,0);
      // 只列前三类，剩下的合成一项：卡片是入口，不是复核队列本身。
      const top=counts.slice(0,3).map(([label,value])=>`${label} ${value.toLocaleString()}`);
      const rest=counts.slice(3).reduce((sum,[,value])=>sum+value,0);
      if(rest)top.push(`其余 ${rest.toLocaleString()}`);
      return [`${total.toLocaleString()} 条待复核`,top.join(' · ')];
    }),
    fill('trash',async()=>{
      const data=await api('/api/items?state=trash&limit=1');
      const total=Number(data.total||0);
      return [`${total.toLocaleString()} 项在回收站`,total?`占用 ${fmtSize(data.bytes||0)}`:''];
    }),
    fill('quality',async()=>
      [`${Number((await api('/api/quality-goals?limit=1')).total||0).toLocaleString()} 个待升级`]),
  ]);
}

let dupData=null;
/* 重复文件。判据是「同番号 + 时长相近 + 分卷标记一致」，不是同番号即重复——
   合集、分卷和混入的广告都会共用一个 code，只按番号做「保留最大」会删掉内容。
   批量一律走 dispose 进回收站，可逆；永久删除仍只能从回收站单独执行。 */
async function openDuplicates(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/duplicates');
  const surface=claimSurface('/duplicates');
  showManagementBody({placeholder:managementPlaceholder('/duplicates')});
  const next=await surfaceApi(surface,'/api/duplicates?limit=120');
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
    </section>`).join(''):emptyState('file-stack','没有找到重复文件','所有来源之间没有检测到内容相同的文件。扫描新来源后，这里会自动更新。')}</div>`;
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
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/review');
  const surface=claimSurface('/review');
  showManagementBody({placeholder:managementPlaceholder('/review')});
  const runtime=await surfaceApi(surface,'/healthz');
  if(!surfaceCurrent(surface))return;
  /* ADR-0018：确定的那部分先落库再取队列。reader 明知不能写就不要制造一次 409；
     它改为读取 writer 的严格 CA HTTPS 镜像，判定按钮也一起锁住。 */
  if(!runtime.ledger_read_only)try{
    const auto=await api('/api/review/auto-apply',{method:'POST',body:'{}'});
    if(!surfaceCurrent(surface))return;
    if(auto&&auto.applied)console.info(`自动落库 ${auto.applied} 条（ADR-0018）`);
  }catch(e){console.info('自动落库未执行：'+e.message)}
  const next=await surfaceApi(surface,'/api/review');
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
      <div class="reviewtabs" role="tablist" aria-label="复核分类">${Object.entries(REVIEW_LABELS).map(([key,label])=>{
        /* Geist Tabs（vercel.com/geist/tabs）：计数走独立徽标，为 0 时整枚去掉，不留一个
           「0」占位；tabindex 只留在选中项上，方向键负责在同一条里移动焦点。 */
        const on=key===reviewCategory,count=Number(reviewData.counts[key]||0);
        return `<button role="tab" id="reviewtab-${key}" aria-controls="reviewpanel" data-review-tab="${key}"
          aria-selected="${on}" tabindex="${on?'0':'-1'}">${label}${
          count?` <span class="n mono">${count.toLocaleString()}</span>`:''}</button>`;
      }).join('')}</div>
      <section class="reviewsection" id="reviewpanel" role="tabpanel" aria-labelledby="reviewtab-${reviewCategory}"><div class="reviewlist">${rows.length?rows.map(row=>{
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
               ${asset.preview_url?`<img src="${esc(asset.preview_url)}" alt="" loading="lazy" data-drop="self">`:'<span>无封面</span>'}</button>
             <div><b data-middle-truncate title="${esc(asset.name||'')}">${esc(asset.code||asset.name||'原视频')}</b>
               <button type="button" data-review-open-item="${asset.id}">${icon('play')}打开原视频</button></div></div>`).join('')}</div>`:'';
         const origin=comparisonOrigin||subjectKind&&subjectName?comparisonOrigin||`<div class="reviewentity">
             <button class="reviewentityface" data-entity-kind="${subjectKind}" data-entity-name="${esc(subjectName)}"
               aria-label="打开创作者页：${esc(subjectName)}">${avatarInner(subjectName,
                 row.entity_id?{id:row.entity_id,has_image:row.has_image}:null,null,subjectKind)}</button>
             <div><b><button type="button" class="reviewentityname" data-entity-kind="${subjectKind}" data-entity-name="${esc(subjectName)}">${esc(subjectName)}</button></b>
               ${works?`<small class="mono">${works.toLocaleString()} 部作品</small>`:''}</div></div>`
           :row.asset_id?`<div class="revieworigin">
             <button class="revieworigincover" data-review-open-item="${row.asset_id}" aria-label="打开原视频 ${esc(row.asset_name||'')}">
               ${row.asset_preview_url?`<img src="${esc(row.asset_preview_url)}" alt="" loading="lazy" data-drop="self">`:'<span>无封面</span>'}</button>
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
           : (row.preview_url?`<div class="reviewimage"><img src="${esc(row.preview_url)}" alt="" loading="lazy" data-drop="closest:.reviewimage"></div>`:'<p class="empty">未取得图片预览</p>');
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
    /* Geist Tabs 的键盘契约：左右方向键在同一条 tab 里移动焦点，Home/End 到两端；
       激活仍交给 button 自己的 Enter/Space，不另设快捷键。 */
    const reviewTabs=[...$('#stats').querySelectorAll('[data-review-tab]')];
    reviewTabs.forEach((button,index)=>{
      button.onclick=()=>{reviewCategory=button.dataset.reviewTab;render()};
      button.onkeydown=event=>{
        const step=event.key==='ArrowRight'?1:event.key==='ArrowLeft'?-1:0;
        const target=step?reviewTabs[(index+step+reviewTabs.length)%reviewTabs.length]
          :event.key==='Home'?reviewTabs[0]:event.key==='End'?reviewTabs[reviewTabs.length-1]:null;
        if(!target)return;
        event.preventDefault();target.focus();
      };
    });
    $('#stats').querySelectorAll('[data-review-status]').forEach(button=>button.onclick=async()=>{
      const item=button.closest('[data-review-key]'),row=rows.find(x=>String(x.item_key)===item.dataset.reviewKey);button.disabled=true;
       const selectedIds=[...item.querySelectorAll('[data-review-asset][aria-pressed="true"]')].map(cell=>+cell.dataset.reviewAsset);
       const candidateKey=item.querySelector('[name^="metadata-"]:checked')?.value||'';
       /* api() 在任何非 2xx 都 throw，这个 onclick 必须自己 catch：漏掉就吞成 unhandled
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
          actionReceipt(button.dataset.reviewStatus==='approved'?'已通过候选':
            button.dataset.reviewStatus==='rejected'?'已拒绝候选':'已跳过候选');
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

/* ── island 挂载点（ADR-0022）──
   高清版目标页已经迁到 Preact。遗留层只留外壳：铺骨架、把自己独有的助手交出去，
   取数与渲染都在 /dist/peach-ui.js 里。产物不带内容哈希，所以路径可以写死。
   换页判据仍归遗留层：`isCurrent` 让 island 在用户走开后不要把数据画上来。 */
async function openQualityGoals(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/quality-goals');
  const surface=claimSurface('/quality-goals');
  showManagementBody({placeholder:managementPlaceholder('/quality-goals')});
  const ui=await import('/dist/peach-ui.js');
  const props={openItem,javTitleHtml,javDisplayName,srcBadge};
  await ui.mountIsland('quality-goals',$('#stats'),props,{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface))window.scrollTo({top:0,behavior:'smooth'});
}

/* ── 在线追更 ──
   两个页面，因为是两件事：
   - `/follow`（左侧导航）是**看**：一张卡片一个作品，点开就去看。本站的 alt 与 WIP
     折进卡片内部，跨站的同一作品折成「另见」，24 条抓取记录才读成 20 个作品。
   - `/follow-manage`（管理区）是**管**：加来源、检查更新、移除来源、看凭据状态，
     以及对内容做批量标记。
   联网只发生在管理页点「检查更新」的那一刻——看的那一页不联网。 */
let followDiscoverySeed=Math.floor(Math.random()*0xffffffff);
const followDiscoveryRank=value=>seededRank(followDiscoverySeed,value);
const followRandomOrder=(rows,key)=>[...rows].sort((a,b)=>
  followDiscoveryRank(key(a))-followDiscoveryRank(key(b))||String(key(a)).localeCompare(String(key(b))));
/* 来源筛选：fsrcProviders 记录见过的全部来源（默认全选），
   fsrcUnchecked 只记被取消勾选的——新来源自动进入「全选」。 */
const fsrcProviders=new Set(),fsrcUnchecked=new Set();
/* 关注页一次取一屏。counts 是全库口径（「未看 2292」），groups 只有这一页——
   两个数并排显示时看起来像自相矛盾，实际是两个口径，所以列表底部要能继续加载。 */
const FOLLOW_PAGE=300;
/* 作者、来源和标签一起交给服务端。只让状态走服务端、这三个在浏览器里筛的话，
   药丸上的数字（全库口径）和列表（筛过的这几页）就是两套口径，换个筛选条件
   数字纹丝不动；而且选个冷门作者，一页 300 条里可能只剩两条，得反复点加载更多。 */
const followPageUrl=offset=>
  `/api/follow?limit=${FOLLOW_PAGE}&offset=${offset}`
  +(followFilter?`&status=${followFilter}`:'')
  +(followAuthor?`&author=${encodeURIComponent(followAuthor)}`:'')
  +(followProvider?`&provider=${encodeURIComponent(followProvider)}`:'')
  +(followTags.size?`&tag=${encodeURIComponent([...followTags].join(','))}`:'');
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
  if(button){setActionBusy(button);button.innerHTML=`${spinnerHtml('加载更多')}<span>加载中…</span>`}
  try{
    const next=await api(followPageUrl((followData.offset||0)+FOLLOW_PAGE));
    followData={...next,
      groups:mergeFollowGroups([...followData.groups],next.groups||[]),
      // counts 一直是全库口径，用新的那份即可；offset/has_more 跟着最新一页走。
      sources:next.sources||followData.sources};
    renderFollow();
  }finally{followBusy=false;if(button){setActionBusy(button,false);button.innerHTML=oldButton}}
}
let followCredentialProviders=new Set();
/* 上一次检查的结果。检查完页面会整页重画，如果不把结果留在这里，用户看到的就只是
   一次闪烁——他的原话是「完全没返回任何结果」。接口其实每条来源都回了
   added/updated/not_modified/error，是界面把它们全丢了。 */
let followCheckReport=null;
const FOLLOW_FILTERS=[['','全部'],['new','未看'],['seen','已看'],['saved','已保存'],['ignored','已忽略']];

/* 账本里一律存 UTC（ISO 带 Z），界面要按看的人所在时区显示。
   直接把那串字面量印出来的话，UTC+8 的人看到的每个时间都早 8 小时。 */
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

/* 版式切换只翻容器上的一个属性、不重画列表，所以「去掉年份」不能靠换一次格式化，
   得让同一份 DOM 两种显示：年份单独包一层，由 CSS 在紧凑版式里收掉。 */
function localTimeHtml(iso){
  const text=localTime(iso);
  return /^\d{4}-/.test(text)
    ? `<i class="fyear">${esc(text.slice(0,5))}</i>${esc(text.slice(5))}`
    : esc(text);
}

function followWhen(item){
  const raw=item.published_at||'';
  if(!raw)return '时间未取得';
  const text=localTime(raw);
  // 精度仍保留在 API；列表按用户要求不再给近似时间加「约」前缀。
  return text;
}

const followTagType=(item,tag)=>item.tag_types&&item.tag_types[tag]||'unknown';
/* 卡片、详情、筛选条和在线标签页都只消费服务端的内容标签投影。过滤只维护一份，
   原始来源标签仍完整留在 metadata。 */
const followCardTags=item=>item.tags||[];
const followTagChip=(item,tag,kind='span')=>`<${kind} class="tg r34-${
  esc(followTagType(item,tag))}" data-follow-tag="${esc(tag)}">${esc(tagLabel(tag))}</${kind}>`;
/* 详情标签按 rule34.xxx 帖子页 `#tag-sidebar` 的类型顺序分组，组内按名升序——
   证据见 docs/reference-snapshots/rule34-follow-tags-and-collections.md（2026-09-01
   两个帖子页实测，顺序一致，缺的类型直接跳过不占位）。
   来源没记类型的排最后并保持中性色：不按词形猜类型是关注标签的既有门槛。 */
const FOLLOW_TAG_ORDER=['copyright','character','artist','general','metadata'];
function followDetailTags(item){
  const tags=item.detail_tags||item.tags||[];
  const rank=tag=>{const at=FOLLOW_TAG_ORDER.indexOf(followTagType(item,tag));
    return at<0?FOLLOW_TAG_ORDER.length:at};
  return [...tags].sort((a,b)=>rank(a)-rank(b)||tagLabel(a).localeCompare(tagLabel(b)));
}

/* 角标上的数和点开后真能看到的条数必须来自同一个集合。
   实测两处对不上：paheal 一组 9 条里有 1 张图，卡上写「9 个版本」、播放角标写
   「8 个视频」，点开也是 8 条；`2B Camp [4K]` 更极端——卡上写「2 个版本」，同组
   另一条不是可播视频，`collection` 因此整个为 null，点开只有 1 条。 */
function followOpenableItems(group){
  if(followMediaView==='videos')return followVideoItems(group);
  return followCollectionItems(group)
    .filter(item=>followItemMediaKinds(item).has('image'));
}
function followBadges(group,openable=null){
  const badges=[];
  const count=(openable||followOpenableItems(group)).length;
  /* WIP 说的是这一条，不是这一组。`2B Camp [4K]` 判的是 alt，只因为同组还有一条
     `[WIP]` 就在它头上挂 WIP，读起来就成了「这一条是半成品」。同组有 WIP 仍然要
     说，但要说成「含」。 */
  if(group.primary.variant_kind==='wip')badges.push('<span class="fbadge wip">WIP</span>');
  else if(group.has_wip)badges.push('<span class="fbadge wip partial">含 WIP</span>');
  if(group.primary.version)badges.push(`<span class="fbadge ver">${esc(group.primary.version)}</span>`);
  if(count>1)badges.push(`<span class="fbadge">${
    `${count} ${group.is_release?'条动态':'个版本'}`}</span>`);
  if(group.duplicates.length)badges.push(`<span class="fbadge dup">另见 ${
    esc([...new Set(group.duplicates.map(d=>d.provider_label))].join('、'))}</span>`);
  return badges.join('');
}

function followCollectionItems(group){
  const seen=new Set();
  return [group.primary,...group.variants,...group.duplicates].filter(item=>{
    if(!item||seen.has(item.id))return false;seen.add(item.id);return true});
}

function followCollectionItemsNewest(group){
  return followCollectionItems(group).sort((a,b)=>{
    const byTime=(Date.parse(b.published_at||'')||0)-(Date.parse(a.published_at||'')||0);
    return byTime||(+b.id||0)-(+a.id||0);
  });
}

const followGroupedMediaOwner=group=>followCollectionItems(group).find(item=>
  (item.media_items||[]).some(media=>media.resource_group));

// F95 的「8 条动态」可能只有一个网盘页，也可能一条实际视频都没有。Mix 是播放
// 语义，只能由已解析、可在 Peach 内播放的视频触发，不能拿回复数或外链数冒充。
function followVideoItems(group){
  return followCollectionItemsNewest(group).filter(item=>
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
  return followCollectionItemsNewest(group).find(item=>followItemMediaKinds(item).has(wanted))||group.primary;
};

function followMediaIssue(item){
  if(item.media_error)return `媒体未取得：${item.media_error}`;
  if(item.media_needs_credential&&!followCredentialProviders.has(item.provider))return item.playable
    ?'部分媒体未取得：需要 F95 登录会话解析'
    :'媒体未取得：需要 F95 登录会话解析';
  return '';
}

function followResourceLabel(url){
  try{
    const host=new URL(url).hostname.replace(/^www\./,'');
    return ({'gofile.io':'Gofile','pixeldrain.com':'Pixeldrain','mega.nz':'MEGA',
      'mega.io':'MEGA','mediafire.com':'MediaFire','drive.google.com':'Google Drive'})[host]||host;
  }catch{return '外部文件页'}
}

function followMediaSourceLabel(media,item){
  const provider=media?.resource_provider;
  return ({gofile:'Gofile',pixeldrain:'Pixeldrain',mega:'MEGA',mediafire:'MediaFire',
    google_drive:'Google Drive'})[provider]||item.provider_label||item.provider||'在线图片';
}

function followResourceLinks(item){
  const links=item.resource_urls||[];
  if(!links.length)return '';
  return `<div class="followresources">${links.map(url=>
    `<a href="${esc(url)}" target="_blank" rel="noreferrer noopener">${esc(followResourceLabel(url))}${icon('external-link')}</a>`
  ).join('')}</div>`;
}

/* 集合弹层与列表共用同一套动态语义：线程标题不能冒充每条回复的正文，
   行首则说明它与主条目的关系。 */
function followCollectionCopy(group,item,mark=''){
  let label=mark;
  // 发布时间已经由 followWhen 单独显示，不能再伪装成版本/类型标签。
  if(!label&&group.is_release)label=item.variant_label||item.variant_kind||'';
  if(!label)label=item.variant_kind==='wip'?'WIP':(item.variant_label||item.variant_kind||'视频');
  const body=group.is_release
    ?(item.summary||(item.has_media?'（仅附件）':'（无正文）')):item.title;
  return {label,title:group.is_release&&item.author?`${item.author}：${body}`:body};
}

function followQueueHtml(group,itemId){
  const groupedOwner=followGroupedMediaOwner(group);
  if(groupedOwner)return followEmbeddedQueueHtml(groupedOwner,null);
  const items=followVideoItems(group);
  return `<aside class="mixqueue followqueue" data-queue-kind="collection"><div class="mixqueuehead"><div><h2>视频合集</h2><span>${esc(group.primary.title||'未命名合集')} · ${items.length} 个视频</span></div><div class="mixqueueactions">
    <button data-follow-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${items.map(item=>{
      const copy=followCollectionCopy(group,item,group.duplicates.includes(item)?item.provider_label:'');
      const thumb=item.thumb_url
        ?`<img src="${esc(item.thumb_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self">`
        :`<span class="fnothumb">${sourceIcon(item.provider)}</span>`;
      return `<div class="mixrow"><button class="mixitem ${item.id===itemId?'current':''}" data-follow-queue-item="${item.id}" aria-current="${item.id===itemId?'true':'false'}">
        <span class="mixitempic">${thumb}${realDuration(item.duration)?`<i class="dur mono">${fmtDur(item.duration)}</i>`:''}</span>
        <span class="mixitemtext"><b data-truncate-end>${esc(copy.title)}</b><span data-truncate-end><i class="fvkind ${esc(item.variant_kind||'')}">${esc(copy.label)}</i>${followWhen(item)}</span></span></button></div>`;
    }).join('')}</div></aside>`;
}

function followEmbeddedQueueHtml(item,mediaIndex){
  const items=item.media_items||[];
  const groups=[];
  items.forEach(media=>{
    const key=media.resource_group||'ungrouped';
    let group=groups.find(row=>row.key===key);
    if(!group){group={key,label:media.resource_group_label||'',items:[]};groups.push(group)}
    group.items.push(media);
  });
  const rows=groups.map(group=>`${group.label?`<h3 class="mixgrouplabel">${esc(group.label)} <span>${group.items.length}</span></h3>`:''}${group.items.map(media=>{
      const thumb=media.thumb_url
        ?`<img src="${esc(media.thumb_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self">`
        :`<span class="fnothumb">${sourceIcon(media.resource_provider||item.provider)}</span>`;
      return `<div class="mixrow"><button class="mixitem ${media.index===mediaIndex?'current':''}" data-follow-media-owner="${item.id}" data-follow-media-item="${media.index}" data-media-kind="${media.media_kind}" aria-current="${media.index===mediaIndex?'true':'false'}">
        <span class="mixitempic">${thumb}</span><span class="mixitemtext"><b data-middle-truncate>${esc(javDisplayName(media))}</b><span data-truncate-end>${media.media_kind==='image'?'图片':'视频'}</span></span></button></div>`;
    }).join('')}`).join('');
  return `<aside class="mixqueue followqueue" data-queue-kind="media"><div class="mixqueuehead"><div><h2>多媒体</h2><span>${esc(item.title||'未命名内容')} · ${items.length} 个媒体</span></div><div class="mixqueueactions">
    <button data-follow-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${rows}</div></aside>`;
}

/* 重建条目索引。`merge` 时只往里加，不清空已有的。

   单条查询（followItemById）不能走整表重建：那会让点一个不在索引里的条目把索引
   替换成只剩那一条，再点别的又没有、又替换。列表能翻页之后这条路径被踩得很频繁，
   表现就是「多点几次详情就打不开了」。 */
function indexFollowItems(data,{merge=false}={}){
  const groups=data?.groups||[];
  if(!merge){followItemsById=new Map();followGroupByItemId=new Map()}
  groups.forEach(group=>followCollectionItems(group).forEach(item=>{
    followItemsById.set(item.id,item);followGroupByItemId.set(item.id,group)}));
}

async function followItemById(id){
  if(followItemsById.has(id))return followItemsById.get(id);
  const data=await api(`/api/follow?item=${encodeURIComponent(id)}`);
  if(!followData)followData=data;
  indexFollowItems(data,{merge:true});
  return followItemsById.get(id);
}

async function openFollowDetail(id,push=true,mediaIndex=null,preserveReturn=false){
  releaseHoverPreviews();
  const entering=!location.pathname.startsWith('/follow/item/');
  if(push&&entering&&!preserveReturn)followDetailReturnPath=location.pathname+location.search;
  if(!push&&!preserveReturn)followDetailReturnPath='/follow';
  const surface=surfaceToken(surfacePath());
  const item=await followItemById(+id);if(!item||!surfaceCurrent(surface))return;
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
  renderFollowDrawer([item]);
  const source=(followData?.sources||[]).find(row=>row.id===item.source_id);
  const authorSources=(followData?.sources||[]).filter(row=>
    source?.author_key&&row.author_key===source.author_key);
  if(!authorSources.length&&source)authorSources.push(source);
  const src=item.playable?`/follow-stream?id=${item.id}${selectedMedia?`&media=${selectedMedia.index}`:''}`:'';
  const selectedKind=selectedMedia?.media_kind||item.media_kind;
  const media=item.playable&&selectedKind==='video'
    ?`<video class="video-js vjs-big-play-centered" controls playsinline preload="metadata"${item.thumb_url?` poster="${esc(item.thumb_url)}"`:''}></video>`
    :item.playable&&selectedKind==='image'
      ?`<img class="followdetailposter" src="${src}" alt="${esc(item.title)}">`
      :item.thumb_url
        ?`<img class="followdetailposter" src="${esc(item.thumb_url)}" alt="${esc(item.title)}" referrerpolicy="no-referrer">`
        :`<div class="followdetailplaceholder">${sourceIcon(item.provider)}<span>没有可用预览</span></div>`;
  const imageControls=imageCarousel?`<button class="media-circle media-overlay followimagearrow prev" data-follow-image-step="-1" aria-label="上一张图片" title="上一张">${icon('chevron-left')}</button>
    <button class="media-circle media-overlay followimagearrow next" data-follow-image-step="1" aria-label="下一张图片" title="下一张">${icon('chevron-right')}</button>
    <div class="followimagedots" role="group" aria-label="${imageMedia.length} 张图片">${imageMedia.map((image,index)=>`<button data-follow-image-item="${image.index}" aria-current="${index===imagePosition}" aria-label="第 ${index+1} 张，共 ${imageMedia.length} 张" title="第 ${index+1} 张"></button>`).join('')}</div>`:'';
  const badges=followBadges({primary:item,variants:[],duplicates:[],has_wip:item.variant_kind==='wip'});
  // 卡片只消费 general 内容投影；详情保留来源记录的全部类型，并按类型着色。
  const tags=followDetailTags(item).map(tag=>followTagChip(item,tag,'button')).join('');
  const author=followAuthorName(authorSources)||item.author||item.source_label||'作者未取得';
  const postedBy=item.author&&foldName(item.author)!==foldName(author)?item.author:'';
  const mediaIssue=followMediaIssue(item);
  /* 舞台就近展开：插在被点击那张卡片所在的一行之后，而不是整个列表之前。
     插在列表前等于永远回到页面顶部——翻了几屏点开一条，视线要被拽回最上面，
     关掉后还得再翻回来。首页的详情早就是就近展开的，关注页一直没跟上。

     按行插入而不是紧跟卡片：列表是网格，插在某张卡片正后面会把它那一行截断。
     行的判定用 offsetTop——同一行的卡片顶边相同。 */
  const followList=$('#stats').querySelector('.followlist');
  const clicked=followList&&followList.querySelector(`[data-follow-item="${item.id}"]`);
  if(followList?.classList.contains('followphotowall')){
    /* 图片墙是稳定网格；详情独立放在墙前，避免成为网格子项并改变所有行的排列。 */
    followList.before($('#stage'));
  }else if(clicked){
    const cards=[...followList.children];
    const row=clicked.offsetTop;
    // 同一行里最后一张卡片：它之后就是插入点。
    let last=clicked;
    for(const card of cards){
      if(Math.abs(card.offsetTop-row)<2)last=card;
    }
    last.after($('#stage'));
  }else if(followList){
    followList.before($('#stage'));
  }else{
    placeItemDetail(detailOriginAnchor,detailOriginAbove);
  }
  $('#stage').hidden=false;document.body.classList.add('detail-open');
  $('#stage').innerHTML=`<div class="sgrid followdetailgrid${collection||embeddedQueue?' mixgrid':''}">
    <div class="vwrap followdetailmedia${selectedKind==='image'?' image':''}">${selectedKind==='video'?'<canvas class="ambientcanvas" width="32" height="18"></canvas>':''}<button class="closestage" id="closeStage" title="关闭" aria-label="关闭">${icon('x')}</button>${selectedKind==='video'?playerStatsOverlayHtml():''}${media}${imageControls}</div>
    ${embeddedQueue?followEmbeddedQueueHtml(item,selectedMedia.index):(collection?followQueueHtml(collection,item.id):'')}
    <div class="side followdetailside"><div class="sidecontent">
      <div class="followdetailtitle"><div class="stitle">${esc(item.title)}</div>${item.url?`<a class="followorigin" href="${esc(item.url)}" target="_blank" rel="noreferrer noopener" title="打开来源页面" aria-label="打开来源页面">${icon('external-link')}</a>`:''}</div>
      <div class="followdetailidentity"><span class="mav fsourceavatar">${followAuthorAvatar(authorSources)}</span>
        <div><b>${esc(author)}</b>${postedBy?`<span>发布者 ${esc(postedBy)}</span>`:''}</div></div>
      <div class="smeta mono"><span>${followWhen(item)}</span>${realDuration(item.duration)?`<span>${fmtDur(item.duration)}</span>`:''}${badges?`<span class="fbadges">${badges}</span>`:''}</div>
      ${item.summary?`<p class="followdetailsummary">${esc(item.summary)}</p>`:''}
      ${mediaIssue?`<p class="fnote followmediaissue">${esc(mediaIssue)}</p>`:''}
      ${followResourceLinks(item)}
      <div class="fb followdetailactions">
        <button class="later" data-follow-detail-save aria-label="${item.status==='saved'?'已保存':'保存到账本'}" title="${item.status==='saved'?'已保存':'保存到账本'}"${item.status==='saved'?' disabled':''}>${item.status==='saved'?icon('check'):icon('bookmark-plus')}</button>
        <button class="seen" data-follow-detail-status="seen" aria-label="标记已看" title="标记已看" aria-pressed="${item.status==='seen'}">${icon('eye')}</button>
        <button class="dislike" data-follow-detail-status="ignored" aria-label="忽略" title="忽略" aria-pressed="${item.status==='ignored'}">${icon('eye-off')}</button>
        ${item.status==='seen'||item.status==='ignored'?`<button data-follow-detail-status="new" aria-label="恢复未看" title="恢复未看">${icon('rotate-ccw')}</button>`:''}
        ${src?`<a class="fdownload" href="${esc(src)}${src.includes('?')?'&':'?'}download=1" download
          aria-label="下载到本地" title="下载到本地">${icon('download')}</a>`:''}</div>
      <span class="fstate" aria-live="polite"></span>
      ${tags?`<div class="stags followdetailtags">${tags}</div>`:''}
    </div></div></div>`;
  $('#stage').classList.toggle('ambient-on',selectedKind==='video'&&appSettings.ambientMode);
  $('#stage').classList.toggle('theater-mode',selectedKind==='video'&&appSettings.theaterMode);
  /* 关掉详情只是回到列表，不该重新取一遍。重取要等一个网络往返（慢），而且只会
     取回第一页——「加载更多」出来的条目会连同索引一起消失，那些卡片的详情随后
     就打不开了。列表数据还在 followData 里，直接重画。 */
  const closeDetail=async()=>{
    disposeStage(false);
    route(followDetailReturnPath||'/follow');
    if(location.pathname!=='/follow'){await restoreRoute();return}
    if(followData)renderFollow();else await openFollow(false);
  };
  $('#closeStage').onclick=closeDetail;
  $('#stage').querySelectorAll('[data-follow-queue-close]').forEach(button=>button.onclick=closeDetail);
  $('#stage').querySelectorAll('[data-follow-queue-item]').forEach(button=>button.onclick=()=>
    openFollowDetail(+button.dataset.followQueueItem,true,null,true));
  $('#stage').querySelectorAll('[data-follow-media-item]').forEach(button=>button.onclick=()=>
    openFollowDetail(+(button.dataset.followMediaOwner||item.id),false,
      +button.dataset.followMediaItem,true));
  const switchImage=index=>openFollowDetail(item.id,false,+index,true);
  $('#stage').querySelectorAll('[data-follow-image-item]').forEach(button=>button.onclick=()=>
    switchImage(button.dataset.followImageItem));
  $('#stage').querySelectorAll('[data-follow-image-step]').forEach(button=>button.onclick=()=>{
    const next=(imagePosition+(+button.dataset.followImageStep)+imageMedia.length)%imageMedia.length;
    switchImage(imageMedia[next].index);
  });
  /* 详情里点图开大图，跟女优页同一个灯箱。多图时把整组交进去，左右翻页就能看完
     一条帖子的所有图，不用退出去再点下一张。取不到正片就退而用缩略图——看小图
     总比点了没反应强。 */
  const followSlides=imageMedia.length
    ?imageMedia.map((image,index)=>({follow:true,
      src:`/follow-stream?id=${item.id}&media=${image.index}`,
      thumb:image.thumb_url||item.thumb_url||`/follow-stream?id=${item.id}&media=${image.index}`,
      name:image.name||item.title,source:followMediaSourceLabel(image,item),size:image.size,
      position:index+1,total:imageMedia.length}))
    :selectedKind==='image'&&src
      ?[{follow:true,src,thumb:item.thumb_url||src,name:item.title,
        source:followMediaSourceLabel(selectedMedia,item),size:selectedMedia?.size,position:1,total:1}]
      :item.thumb_url?[{follow:true,src:item.thumb_url,thumb:item.thumb_url,name:item.title,
        source:item.provider_label||item.provider||'在线图片',position:1,total:1}]:[];
  const poster=$('#stage').querySelector('.followdetailposter');
  if(poster&&followSlides.length){
    poster.classList.add('zoomable');
    poster.onclick=()=>openPhotoLightbox(Math.max(0,imagePosition),followSlides);
  }
  const followVideo=$('#stage').querySelector('.followdetailmedia>video');
  if(followVideo){
    /* 清晰度解析与默认片源并行。它需要回源抓详情，不能挡住播放器挂载；否则来源慢
       一点，详情里就会先留下一个没有 src 的空视频框。 */
    const qualitiesPromise=api(`/follow-qualities?id=${encodeURIComponent(item.id)}`)
      .then(answer=>answer?.qualities?.length?answer.qualities:null).catch(()=>null);
    const followPlayer=await mountDetailPlayer(item,followVideo,false,{
      source:{src,type:selectedMedia?.media_type||item.media_type||'video/mp4'},
      checkSourceStatus:false,
      size:selectedMedia?.size,
      qualitiesPromise
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
  const write=async(button,path,body,done,{message='已更新',undo=null}={})=>{
    const state=$('#stage').querySelector('.fstate');setActionBusy(button);
    try{await api(path,{method:'POST',body:JSON.stringify(body)});done();state.textContent='';
      actionReceipt(message,{undo})}
    catch(error){state.textContent=error.message||'操作失败';actionFailure('更新关注状态',error)}
    finally{setActionBusy(button,false)}
  };
  $('#stage').querySelector('[data-follow-detail-save]')?.addEventListener('click',event=>{
    const button=event.currentTarget;
    write(button,'/api/follow/save',{item:item.id},()=>{
      item.status='saved';button.innerHTML=icon('check');button.title='已保存';button.setAttribute('aria-label','已保存')},
    {message:'已保存到账本'});
  });
  $('#stage').querySelectorAll('[data-follow-detail-status]').forEach(button=>button.onclick=()=>{
    const before=item.status,to=button.dataset.followDetailStatus;
    write(button,'/api/follow/status',{item:item.id,to},()=>{
      item.status=to;
      $('#stage').querySelectorAll('[data-follow-detail-status]').forEach(control=>
        control.setAttribute('aria-pressed',String(control.dataset.followDetailStatus===item.status)))},
    {message:to==='seen'?'已标记看过':'已更新关注状态',undo:before!=='saved'?async()=>{
      await api('/api/follow/status',{method:'POST',body:JSON.stringify({item:item.id,to:before})});
      item.status=before;
      $('#stage').querySelectorAll('[data-follow-detail-status]').forEach(control=>
        control.setAttribute('aria-pressed',String(control.dataset.followDetailStatus===before)));
    }:null});
  });
  alignFollowImageControls();
  // 滚到舞台本身，不是页面头部——就近展开的意义就在于视线不被拽走。
  // 复用首页那套 sticky 偏移，标题不会被吸顶的筛选条盖住。
  scrollItemDetailIntoView();
}

/* object-fit:contain 后图片左右黑边会随图片比例和窗口改变。箭头应位于黑边的视觉中心，
   不能永远贴容器边缘；黑边太窄时才退回固定的安全内边距。 */
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
    ? `<img src="${esc(thumbUrl)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self">`
    : `<span class="fnothumb">${esc(item.provider_label)}</span>`;
  const videos=followMediaView==='videos'?followVideoItems(group):[],embedded=item.media_items||[];
  const groupedOwner=followMediaView==='videos'?followGroupedMediaOwner(group):null;
  const groupedVideos=(groupedOwner?.media_items||[]).filter(media=>media.media_kind==='video');
  const isMix=embedded.length>1||groupedVideos.length>1||videos.length>1;
  const mixCount=embedded.length>1?embedded.length:(groupedVideos.length||videos.length);
  const mixKind=embedded.length&&embedded.every(media=>media.media_kind==='image')?'图片'
    :embedded.length&&embedded.some(media=>media.media_kind==='image')?'媒体':'视频';
  const mixTarget=embedded.length>1?item.id:(videos[0]?.id||item.id);
  /* 翻动用的几张必须来自角标数的那一组，否则卡上写「9 个视频」翻的却是别处的图。
     图片视图里只翻图片：这一叠说的就是这几张图。 */
  const faceSource=embedded.length>1?embedded:(groupedVideos.length>1?groupedVideos:videos);
  const faceUrls=isMix?[...new Set([thumbUrl,...faceSource
    .filter(entry=>!imageView||entry.media_kind==='image')
    .map(entry=>entry.thumb_url)].filter(Boolean))].slice(0,MIX_FLIP_FACES):[];
  const badges=followBadges(group);
  const tags=followCardTags(item).slice(0,3).map(tag=>followTagChip(item,tag)).join('');
  const mediaIssue=followMediaIssue(item);
  const open=`<button class="cardopenhit" data-follow-detail="${item.id}" aria-label="打开 ${esc(item.title)} 详情"></button>`;
  return `<article class="card followitem${isMix?' collection':''}${imageView?' imagecard':''}" data-follow-item="${item.id}" data-status="${esc(item.status)}">
    <div class="${isMix?'mixstack ':''}followvisual"><div class="pic">
      ${open}${thumb}${faceUrls.length>1?`<div class="mixfaces" data-mix-faces="${esc(JSON.stringify(faceUrls))}" hidden></div>`:''}
      <span class="badge" title="${esc(item.provider_label)}" aria-label="来源：${esc(item.provider_label)}">${sourceIcon(item.provider)}</span>
      <span class="selectionMark">${icon('check')}</span>${realDuration(item.duration)?`<span class="dur mono">${fmtDur(item.duration)}</span>`:''}
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
        ${tags?`<div class="ctags">${tags}</div>`:''}${mediaIssue?`<span class="fnote followmediaissue">${esc(mediaIssue)}</span>`:''}</div></div>
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
  /* 这一条显式走 `html`：`bits` 由 followCheckBits 用计数拼出来、含 `<b>`，
     里面全是本地算出来的数字和固定中文，没有账本字段能流进来。 */
  toast({html:`检查了 <b>${rows.length}</b> 个来源：${bits.join(' · ')}`+
    (exhausted?` · <b>${exhausted} 个没有更多内容</b>`:'')+
    (failed?` · <b>${failed} 个失败</b>`:'')},
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
  const ended=exhausted.length?`<div class="geist-note geist-note-secondary fcheckreport" role="note">
    ${icon('info')}<div><p><b>${exhausted.length} 个来源没有更多内容</b></p>
    ${exhausted.map(row=>`<p class="fchecknote">${esc([row.provider_label||row.provider,row.ref]
      .filter(Boolean).join(' '))}：没有更多历史内容</p>`).join('')}</div>${dismiss}</div>`:'';
  const errors=failed.length||evidence.length?`<div class="geist-note geist-note-error fcheckreport" role="alert">${icon('alert')}<div>
    ${failed.length?`<p><b>${failed.length} 个来源检查失败</b></p>`:''}
    ${failed.map(row=>`<p class="fcheckfail"><strong>${esc(row.provider_label||row.provider||'')}</strong>
      <strong>${esc(row.author||row.label||row.ref||'')}</strong>${row.provider?'：':''}${esc(row.error||'未说明原因')}</p>`).join('')}
    ${evidence.length?`<p class="fchecknote">候选已入库，但这一次的原始响应没有留档：${
      esc(evidence[0].evidence_error)}</p>`:''}
  </div>${dismiss}</div>`:'';
  return `<div class="fcheckreports">${ended}${errors}</div>`;
}

/* ── 看的那一页 ── */
/* URL 是关注页筛选的唯一真相源。

   五个键都归 URL。只放 author 和 media、让 provider、tag、status 活在模块级全局里的话：
   离开再回来还按着（谁都不重置它们），刷新就丢，也没法从别处链到一个筛好的视图。
   标签页要能点一个在线标签直接进「关注 · 这个标签」，就必须走 URL。

   `status` 的默认值是「全部」，所以缺省即全部，不写这个参数。旧链接里的
   `status=all` 仍按全部读——那是「全部」还不是默认值时的写法。 */
function followViewPath(){
  const params=new URLSearchParams();
  if(followAuthor)params.set('author',followAuthor);
  if(followProvider)params.set('provider',followProvider);
  if(followTags.size)params.set('tag',[...followTags].join(','));
  if(followFilter)params.set('status',followFilter);
  if(followMediaView==='images')params.set('media','images');
  const search=params.toString();return '/follow'+(search?'?'+search:'');
}
function readFollowView(){
  const params=new URLSearchParams(location.search);
  followAuthor=params.get('author')||'';
  followProvider=params.get('provider')||'';
  followTags=new Set((params.get('tag')||'').split(',').filter(Boolean));
  const status=params.get('status');
  followFilter=(status===null||status==='all')?'':status;
  followMediaView=params.get('media')==='images'?'images':'videos';
}
function followMediaControl(counts){
  if(!counts.images&&followMediaView!=='images')return '';
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
  /* 筛选条上能选什么来自服务端的全库口径 facets，不是这一页的 groups。按 groups 算
     的话，选中一个作者之后服务端只回他的条目，作者栏就只剩他一个人，再也切不回去。 */
  const facets=followData.facets||{};
  const activeAuthors=new Set(facets.authors||[]);
  const providerLabels=new Map(sources.map(source=>[source.provider,source.provider_label]));
  const providers=new Map((facets.providers||[]).map(key=>[key,providerLabels.get(key)||key]));
  const tagCounts=new Map(facets.tags||[]);
  const authorSources=new Map();
  sources.forEach(source=>{
    if(!source.author_key)return;
    if(!authorSources.has(source.author_key))authorSources.set(source.author_key,[]);
    authorSources.get(source.author_key).push(source);
  });
  const authors=new Map([...authorSources].filter(([key])=>activeAuthors.has(key)).map(([key,list])=>[key,{
    name:followAuthorName(list),sources:list,
  }]));
  const randomizedAuthors=followRandomOrder([...authors],row=>row[0]);
  const allCount=Object.values(counts).reduce((total,count)=>total+(+count||0),0);
  const topTagRows=followRandomOrder([...tagCounts],row=>row[0]).slice(0,20);
  followTags.forEach(tag=>{
    if(!topTagRows.some(([key])=>key===tag))
      topTagRows.push([tag,tagCounts.get(tag)||allCount]);
  });
  const topTags=topTagRows.map(([tag,n])=>[tag,tagLabel(tag),n]);
  if(followAuthor&&!authors.has(followAuthor))followAuthor='';
  if(followProvider&&!providers.has(followProvider))followProvider='';
  // artist/character/copyright/metadata 不进入 general facets，但从在线标签索引点入后
  // 仍是有效筛选，不能因为顶部筛选条的口径更窄就把它从 URL 和界面删掉。
  // 作者、来源和标签都已在服务端筛过，这里不再筛第二遍——两份同义的判定必然漂移。
  const mediaCounts={videos:0,images:0};
  groups.forEach(group=>followMediaKinds(group).forEach(kind=>
    mediaCounts[kind==='image'?'images':'videos']++));
  const wantedKind=followMediaView==='images'?'image':'video';
  const visible=groups.filter(group=>followMediaKinds(group).has(wantedKind));
  renderFollowDrawer(visible.flatMap(group=>followCollectionItems(group)));
  const providerPills=[...providers].map(([key,label])=>
    `<button class="pill sourcepill" data-follow-provider="${esc(key)}" aria-pressed="${key===followProvider}"
      title="${esc(label)}" aria-label="来源：${esc(label)}">${sourceIcon(key)}</button>`).join('');
  $('#stats').innerHTML=`<div class="follow">
    <div class="followhead"><h2 class="disp pagetitle">关注</h2>
      <button class="fbtn primary fcheck" data-follow-manage>${icon('settings')}管理关注</button></div>
    ${authors.size?`<div class="tier followauthors" aria-label="按作者筛选">${randomizedAuthors.map(([key,author])=>
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
      ?`<div class="geist-note geist-note-error fwarn" role="alert">${icon('alert')}<span>${broken.length} 个来源上次检查失败，去<button class="flink" data-follow-manage>管理关注</button>看原因。</span><button class="wclose" data-fwarn-dismiss title="本次会话不再显示" aria-label="关闭提醒">${icon('x')}</button></div>`:''}
    <div class="followlist${followMediaView==='images'?' followphotowall':''}">${visible.length?visible.map(group=>{
      const source=sourceOf(group),siblings=source&&authorSources.get(source.author_key)||[];
      return followCard(group,siblings)}).join('')
      :groups.length?emptyState('search-x','当前筛选下没有更新','切换媒体类型、作者、来源或标签后再试。')
      :sources.length?emptyState('rss','没有符合条件的更新','切换状态或来源筛选后再试。')
      :emptyState('rss','还没有关注任何来源','添加作者或订阅来源后，更新会集中显示在这里。',{actions:'<button class="fbtn primary" data-follow-manage>添加关注</button>'})}</div>
    ${followData.has_more||sources.some(source=>source.can_backfill)?`<div class="followpagination">
      ${followData.has_more?`<span class="followpageaction"><button class="fbtn" data-follow-more>${icon('chevron-down')}加载更多</button>
        <span class="fmeta">已显示 ${visible.length.toLocaleString()} / ${
        (followFilter?counts[followFilter]||0:allCount).toLocaleString()} 项</span></span>`:''}
      ${sources.some(source=>source.can_backfill)?`<span class="followpageaction"><button class="fbtn" data-follow-older>${icon('history')}抓更早的一页</button>
        <span class="fmeta">${esc(followBackfillState(sources))}</span></span>`:''}</div>`:''}</div>`;
  const more=$('#stats').querySelector('[data-follow-more]');
  wireLoadMore(more,()=>loadMoreFollow(more));
  wireFollowItems();
  wireFollowOlder();
  void wireFollowProgress();
  wireDrag($('#stats').querySelector('.followauthors'));
  wireDrag($('#stats').querySelector('.followfilters'));
  paintSelection();
  /* 一律先把新状态写进 URL 再重取：openFollow 现在照 URL 推导，不先写就会被
     推回旧值。前进后退也因此天然可用。 */
  const applyFollowView=()=>{route(followViewPath());openFollow(false)};
  $('#stats').querySelectorAll('[data-follow-filter]').forEach(button=>button.onclick=()=>{
    followFilter=button.dataset.followFilter;applyFollowView()});
  $('#stats').querySelectorAll('.followfilters [data-media-view]').forEach(button=>button.onclick=()=>{
    // 媒体类型是纯前端的分组，不影响服务端取哪些条目，所以只重画不重取。
    followMediaView=button.dataset.mediaView;
    route(followViewPath());renderFollow()});
  $('#stats').querySelectorAll('[data-follow-author]').forEach(button=>button.onclick=()=>{
    followAuthor=followAuthor===button.dataset.followAuthor?'':button.dataset.followAuthor;
    applyFollowView()});
  $('#stats').querySelectorAll('[data-follow-provider]').forEach(button=>button.onclick=()=>{
    followProvider=followProvider===button.dataset.followProvider?'':button.dataset.followProvider;
    applyFollowView()});
  $('#stats').querySelectorAll('[data-follow-tag]').forEach(button=>button.onclick=()=>{
    const tag=button.dataset.followTag;
    if(followTags.has(tag))followTags.delete(tag);else followTags.add(tag);
    applyFollowView()});
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
async function wireFollowProgress(){
  const host=$('#stats').querySelector('.followmanage')||$('#stats'),surface=surfaceToken(surfacePath());
  host.querySelector('[data-follow-progress]')?.remove();
  const marker=document.createElement('div');marker.dataset.followProgress='';host.prepend(marker);
  const ui=await import('/dist/peach-ui.js');
  if(!surfaceCurrent(surface)||!marker.isConnected)return;
  ui.followJobProgress({host:marker,active:()=>surfaceCurrent(surface),
    read:signal=>api('/api/follow/check',{signal}),
    busy:running=>{followBusy=running;
      host.querySelectorAll('[data-follow-check],[data-follow-older]').forEach(button=>setActionBusy(button,running))},
    complete:report=>{followCheckReport=report.status==='failed'
      ?{results:[{ok:false,error:report.error}]}:report;
      followCheckToast(followCheckReport);
      if(surfaceCurrent(surface))void refreshFollowSurface(surface)},
    note:text=>noteHtml(text,{label:'任务状态'}),loading:text=>loadingDotsHtml(text),
    container:content=>`<section class="followtask" data-geist-fieldset aria-label="检查更新进度"><div class="geist-fieldset-content">${content}</div></section>`,
    progress:(value,max)=>progressHtml(`已完成 ${value}/${max} 个来源`,value,max)});
}
async function refreshFollowSurface(surface){
  try{
    const [data,credentials]=await Promise.all([
      surfaceApi(surface,surface.path==='/follow-manage'?'/api/follow?limit=1':followPageUrl(0)),
      surfaceApi(surface,'/api/follow/credentials')]);
    if(!surfaceCurrent(surface))return;
    followData=data;
    if(surface.path==='/follow-manage')renderFollowManage(credentials);
    else renderFollow();
  }catch(error){if(surfaceCurrent(surface))toast(error.message,{warn:true})}
}
async function wireOperationProgress({host,path,key,title,busy,complete}){
  if(!host)return;
  host.querySelector('[data-operation-progress]')?.remove();
  const marker=document.createElement('div');marker.dataset.operationProgress='';host.append(marker);
  const surface=surfaceToken(surfacePath()),ui=await import('/dist/peach-ui.js');
  if(!surfaceCurrent(surface)||!marker.isConnected)return;
  ui.followJobProgress({host:marker,active:()=>surfaceCurrent(surface),read:signal=>api(path,{signal}),
    storageKey:key,title,busy,watchIdle:false,complete:report=>{
      if(report.status==='failed'){marker.innerHTML=noteHtml(report.error||'任务失败',{variant:'error',label:'任务失败'});return}
      complete(report)},note:text=>noteHtml(text,{label:'任务状态'}),
    loading:text=>loadingDotsHtml(text),progress:()=>''});
}
function wireTasteProgress(){
  const button=$('#stats').querySelector('[data-taste-refresh]');
  if(!button)return;
  return wireOperationProgress({host:$('#stats').querySelector('[data-taste-state]'),
    path:'/api/taste/refresh',key:'peach-taste-job',title:'正在读取浏览记录并更新口味分析…',
    busy:running=>{setActionBusy(button,running);button.innerHTML=`${icon('refresh-cw')}读取 Peach 主机`},
    complete:()=>{tasteCache.clear();void openTaste(false);actionReceipt('已更新口味分析')}});
}
function wireResolveProgress(){
  return wireOperationProgress({host:$('#stats').querySelector('[data-follow-add-state]'),
    path:'/api/follow/resolve',key:'peach-resolve-job',title:'正在查找关注来源…',
    busy:running=>{const form=$('#followAdd');
      if(form){form.dataset.busy=String(running);form.setAttribute('aria-busy',String(running))}},
    complete:report=>renderFollowPicks(report.results||[])});
}
function wireFollowOlder(){
  const button=$('#stats').querySelector('[data-follow-older]');
  if(!button)return;
  button.onclick=async()=>{
    if(followBusy)return;
    followBusy=true;setActionBusy(button);
    button.innerHTML=`${spinnerHtml('抓取中')}<span>抓取中…</span>`;
    try{
      const started=await api('/api/follow/check',
        {method:'POST',body:JSON.stringify({older:true,background:true})});
      sessionStorage.setItem('peach-follow-job',started.job_id);
      if(button.isConnected)void wireFollowProgress();
    }catch(error){
      followCheckReport={results:[{ok:false,error:error.message}]};
      followCheckToast(followCheckReport);
      await openFollow(false);
    }finally{if(button.isConnected){followBusy=false;setActionBusy(button,false)}}
  };
}

async function openFollow(push=true,renderForDetail=false){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  /* 从窄栏点进来（push）是「重新进入」，回到干净的 /follow；其余情况一律照 URL
     推导。筛选状态由 URL 推导，不在这里逐个手写重置——漏一个就会让 provider、tag、
     status 一直按着，而它们还决定服务端取哪些条目，等于取错数据。 */
  if(push)followDiscoverySeed=Math.floor(Math.random()*0xffffffff);
  if(push)route('/follow');
  if(location.pathname==='/follow')readFollowView();
  const surface=claimSurface(renderForDetail?surfacePath():'/follow');
  showManagementBody({manage:false,
    placeholder:followSkeletonHtml('正在读取关注内容')});
  const [data,credentials]=await Promise.all([
    surfaceApi(surface,followPageUrl(0)),
    surfaceApi(surface,'/api/follow/credentials').catch(()=>({providers:[]})),
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
  const added=group=>Math.max(...group.map(source=>Date.parse(source.created_at||'')||0));
  /* 每条比较器写的都是该列的默认方向，`flip` 只在方向偏离默认时取反：写成
     「asc 就取反」的话，作者名称默认本来就是正序，一进页面就被翻成倒序。
     同值回退始终按名字正序，不跟着翻——否则「来源数量」里数量相同的那几个人
     每换一次方向就整段倒序一遍，看着像列表在乱跳。 */
  const flip=followManageDir===(FOLLOW_SORT_DEFAULT_DIR[followManageSort]||'desc')?1:-1;
  const byName=(a,b)=>name(a).localeCompare(name(b),'zh-CN',{numeric:true});
  return groups.sort((a,b)=>{
    if(followManageSort==='name')return flip*byName(a,b);
    if(followManageSort==='sources')return flip*(b.length-a.length)||byName(a,b);
    if(followManageSort==='added')return flip*(added(b)-added(a))||byName(a,b);
    return flip*(checked(b)-checked(a))||byName(a,b);
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
function sourceIcon(provider){return SOURCE_ICONS[provider]
  ? `<img class="ficon" src="${esc(SOURCE_ICONS[provider])}" alt="" loading="lazy"
       referrerpolicy="no-referrer" data-drop="self">`
  : ''}

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
  if(src)return `<img class="favatar" src="${esc(src)}" alt=""
    loading="lazy" referrerpolicy="no-referrer" ${imageFallbackAttrs({
      drop:'initial',dropClass:'favatar none',initial,fallbacks:[fallback]})}>`;
  return `<span class="favatar none" title="没有可用头像">${esc(initial)}</span>`;
}

/* 分组标题要用作者本人的名字，不是某一条来源的标签。`LazyProcrastinator · fanbox`
   里「· fanbox」只说明他在哪个平台连载——四条来源合成一组之后还挂着其中一条的
   平台后缀，等于说这一组只属于 fanbox，那正是这次要消掉的误读。
   同名的几种写法里取大写最多的那个：`LazyProcrastinator` 比 `lazyprocrastinator`
   更像作者自己写的名字。 */
function followAuthorName(group){
  if(!group.length)return '';
  const clean=value=>String(value||'')
    .replace(/\s*[·|]\s*[A-Za-z0-9_-]+\s*$/,'')
    .replace(/\s+collections?\s*$/i,'').trim();
  const entity=group.find(source=>source.entity_name);
  if(entity)return entity.entity_name;
  const aliasGroup=(followData.author_aliases||[]).find(
    item=>`name:${item.canonical_key}`===group[0]?.author_key);
  if(aliasGroup)return clean(aliasGroup.canonical_name);
  // 官方主页来源不只优先提供头像，也优先提供作者写法；否则 F95 的线程标题
  // `Lazy Procrastinator Collection` 会因为大写字母更多而抢成分组标题。
  const official=group.find(source=>source.official_avatar_url);
  if(official){
    const officialName=clean(official.label);
    if(officialName)return officialName;
  }
  const names=group.map(source=>clean(source.label))
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
      <button type="button" class="frowicon" data-follow-check="" data-follow-sources="${group.filter(s=>s.enabled).map(s=>s.id).join(',')}"
        ${group.some(s=>s.enabled)?'':'disabled'} title="检查此作者" aria-label="检查 ${esc(name)} 的全部来源">${icon('refresh-cw')}</button>
      <span class="fmeta"${group.length>1?` title="${group.length} 个来源"`:''}>${group.length>1
        ? group.map(source=>sourceIcon(source.provider)).join('')
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
    <label class="fchannelcheck" title="${source.enabled?'参与检查更新':'暂停检查更新'}">${checkboxHtml(
      `data-follow-enabled="${source.id}" ${source.enabled?'checked':''}`
      +` aria-label="${source.enabled?'暂停':'启用'} ${esc(source.label)} 的更新检查"`)}</label>
    <b><a class="fsourcelink" href="${esc(source.url)}" target="_blank"
      rel="noreferrer noopener" title="打开原来源">${esc(source.label)}</a></b>
    <span class="fmeta fprovider" title="${esc(source.provider_label)}">${sourceIcon(source.provider)
      }<span>${esc(source.provider_label)}</span></span>
    <span class="fmeta fchecked">${source.last_checked_at?localTimeHtml(source.last_checked_at):'未检查'}</span>
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
    <summary>${icon('chevron-right')}作者别名${suggestions.length?`<span class="faliasbadge">${suggestions.length} 组待合并</span>`
      :groups.length?`<span class="faliasbadge">${groups.length} 组</span>`:''}</summary>
    ${detected?`<div class="faliassuggestions">${detected}</div>`:''}
    <form class="faliasform" id="followAliasAdd">
      <input class="geist-input" name="canonical" required placeholder="规范作者名" aria-label="规范作者名">
      <input class="geist-input" name="alias" required placeholder="平台别名" aria-label="平台别名">
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
   pixiv / X 资产，项目初期从浏览记录导入的那批）。不取 `facets.creators`：
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
      ${row.world_readable?noteHtml('文件权限过宽，请在运行 Peach 的 POSIX 主机上收紧为 0600。',{variant:'error'}):''}`;
  // 两个分支必须用同一个状态类，否则「不需要」那几行走 .fmeta、其余走 .fstate，
  // 同一列出现两套样式和两种对齐——用户一眼就看出来了。
  /* 站点标记跟着来源走：凭据配的就是那个站，来源行已经用同一枚 favicon 指认它。
     槽位固定 14px，不看里面有没有图：没登记 favicon 的站本来就没有，取不下来的那些
     还会被 data-drop="self" 整个丢掉——两种情况都会让这一列的名字左边缘参差。 */
  const mark=`<span class="ficonslot" aria-hidden="true">${sourceIcon(row.provider)}</span>`;
  if(!body)return `<div class="frow fcred none">${mark}<b>${esc(row.provider_label)}</b>
    <span class="fcstate none">${esc(label)}</span></div>`;
  return `<details class="frow fcred ${esc(kind)}${configured?' ok':''}"${needsAttention?' open':''}>
    <summary>${mark}<b>${esc(row.provider_label)}</b>
      <span class="fcstate ${configured?'done':esc(kind)}">${esc(configured?'已配置':label)}</span>
      ${row.missing.length?`<span class="fcstate missing">缺 ${esc(row.missing.join('、'))}</span>`:''}
    </summary>${body}</details>`;
}

/* 关注列表版式。默认一行一个，来源行的六列都在；紧凑是一行两个，半幅宽度放不下
   六列，收掉「上次检查」——哪个站、成没成功、能不能点都还留着，时间是里面最不
   影响判断的一列。和 JAV 版式共用 iconSwitchHtml，只是 name 与选项不同。 */
const FOLLOW_LAYOUTS=[['cozy','舒适 · 一行一个','maximize'],['compact','紧凑 · 一行两个','layout-grid']];
function followListLayout(){
  return allowedSetting(appSettings.followLayout,FOLLOW_LAYOUTS.map(([k])=>k),'cozy');
}
function followLayoutButtons(){
  return iconSwitchHtml('follow-layout','关注列表版式',FOLLOW_LAYOUTS,followListLayout(),
    {attr:'data-follow-layout'});
}
function setFollowListLayout(value){
  appSettings.followLayout=value;
  saveSettings();
  // 版式是纯展示层的事：改容器上的一个属性就够，不重画列表，也不重新请求。
  document.querySelectorAll('.fsources').forEach(node=>{node.dataset.layout=followListLayout()});
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
          ${searchInputHtml({name:'line',label:'来源链接、名字或 id',
            placeholder:'粘贴来源链接，或输入作者名、id…',attrs:'required'})}
          <div class="fsrcfilter" id="followSrcFilter"></div>
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
          <label class="fmanagesort">${icon('sort')}<select data-follow-sort aria-label="关注列表排序">
            <option value="checked"${followManageSort==='checked'?' selected':''}>检查时间</option>
            <option value="added"${followManageSort==='added'?' selected':''}>添加时间</option>
            <option value="name"${followManageSort==='name'?' selected':''}>作者名称</option>
            <option value="sources"${followManageSort==='sources'?' selected':''}>来源数量</option>
          </select></label>
          <button class="fbtn fmanagedir" type="button" data-follow-dir aria-label="${
            followSortLabel()}">${icon(followManageDir==='asc'?'arrow-up':'arrow-down')}</button>
          ${followLayoutButtons()}
          <button class="fbtn" data-follow-check=""${sources.length?'':' disabled'}>${
            icon('refresh-cw')}检查全部</button>
          <button class="fbtn" data-follow-view>${icon('rss')}去看更新</button></div>
        ${followCheckReport?followCheckFailNote(followCheckReport):''}
        ${sources.length?`<div class="frows fsources" data-layout="${followListLayout()}">${
          followAuthorGroups(sources).map(followAuthorBlock).join('')}</div>
          ${counts.new?`<div class="fsecfoot"><p class="fnote fbulkrow"><span class="fbulkcounts">未看 ${counts.new} · 已看 ${counts.seen||0}
            · 已保存 ${counts.saved||0} · 已忽略 ${counts.ignored||0}</span>
            <span class="fbulk"><button class="fbtn" data-follow-bulk="seen">全部标记已看</button>
            <button class="fbtn" data-follow-bulk="ignored">全部忽略</button></span></p></div>`:''}`
          :emptyState('rss','还没有关注来源','关注来源及其检查状态会显示在这里。',{className:'compact'})}
      </section>
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
    </div></div>`;
  wireFollowManage();
  void wireFollowProgress();
  if(locked)$('#stats').querySelectorAll(
    '#followAdd input,#followAdd button,[data-follow-remove],[data-follow-check],'+
    '[data-follow-enabled],'+
    '[data-follow-bulk],[data-follow-guess],[data-follow-alias-add],'+
    '[data-follow-alias-remove],#followAliasAdd input,#followAliasAdd button,[data-cred-form] input,'+
    '[data-cred-form] button,[data-cred-clear]'
  ).forEach(control=>{control.disabled=true});
}


/* 排序落在地址栏上，返回同一页还是同一个顺序。方向等于该列默认值时不写进地址，
   免得地址栏挂一个和默认完全一样的参数。 */
function routeFollowManageSort(){
  const params=new URLSearchParams();
  if(followManageSort!=='checked')params.set('sort',followManageSort);
  if(followManageDir!==(FOLLOW_SORT_DEFAULT_DIR[followManageSort]||'desc'))params.set('dir',followManageDir);
  const query=params.toString();
  route('/follow-manage'+(query?'?'+query:''));
  openFollowManage(false);
}
async function openFollowManage(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push){followManageSort='checked';followManageDir='desc';route('/follow-manage')}
  else if(location.pathname==='/follow-manage'){
    const params=new URLSearchParams(location.search),requested=params.get('sort');
    followManageSort=['checked','added','name','sources'].includes(requested)?requested:'checked';
    const requestedDir=params.get('dir');
    followManageDir=requestedDir==='asc'||requestedDir==='desc'?requestedDir
      :(FOLLOW_SORT_DEFAULT_DIR[followManageSort]||'desc');
  }
  const surface=claimSurface('/follow-manage');
  showManagementBody({placeholder:managementPlaceholder('/follow-manage')});
  const [data,credentials,runtime]=await Promise.all([
    surfaceApi(surface,'/api/follow?limit=1'),surfaceApi(surface,'/api/follow/credentials'),
    surfaceApi(surface,'/healthz')]);
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
    if(!card.dataset.flipWired){card.dataset.flipWired='1';wireFollowStackFlip(card)}
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
  void wireResolveProgress();
  const root=$('#stats'),form=root.querySelector('#followAdd');
  wireScrollers(root);
  const sort=root.querySelector('[data-follow-sort]');
  if(sort)sort.onchange=()=>{
    followManageSort=sort.value;
    followManageDir=FOLLOW_SORT_DEFAULT_DIR[followManageSort]||'desc';
    routeFollowManageSort();
  };
  const dir=root.querySelector('[data-follow-dir]');
  if(dir)dir.onclick=()=>{
    followManageDir=followManageDir==='asc'?'desc':'asc';
    routeFollowManageSort();
  };
  wireIconSwitch(root,'data-follow-layout',setFollowListLayout);
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
  /* 作者别名和凭据行都走 Geist Collapse，两处同一份实现。凭据行的 `details.fcred`
     必须是 block：flex 行布局接不上 Collapse 的高度过渡。 */
  wireCollapse(root,'details.faliasmanager','follow-alias-collapse');
  wireCollapse(root,'details.fcred','follow-cred-collapse');
  const box=form&&form.querySelector('input[name="line"]');
  /* 回车自己接管，不靠隐式提交：没有提交按钮时浏览器只在「表单里仅有一个文本字段」
     才替你提交，而来源筛选的那串复选框就住在同一个 <form> 里。实测按下去什么也不发生。
     isComposing 是给中文输入法的——选字那一下的回车不是提交。 */
  if(box)box.addEventListener('keydown',event=>{
    if(event.key!=='Enter'||event.isComposing)return;
    event.preventDefault();form.requestSubmit();
  });
  if(form)form.onsubmit=async event=>{
    event.preventDefault();
    if(form.dataset.busy==='true')return;
    /* 状态提示在表单外面的说明行里，不能在 form 里找——找不到就是 null，
       第一次赋值直接抛 TypeError，整个提交静默失败。 */
    const state=root.querySelector('[data-follow-add-state]');
    const prefix=form.querySelector('[data-search-prefix]');
    const line=String(new FormData(form).get('line')||'').trim();
    if(!line)return;
    const lines=[line];
    const byName=!line.includes('/');
    /* 没有提交按钮可以变灰，忙态就落在输入框自己身上：前缀图标原位换 Spinner，
       aria-busy 播报给辅助技术，重复回车由 dataset.busy 挡住。 */
    form.dataset.busy='true';form.setAttribute('aria-busy','true');
    if(prefix)prefix.innerHTML=spinnerHtml('查找中');
    // 索引下载的提醒只在真按名字查时出现；常驻成一句说明就是噪音。
    state.textContent=byName?'查找中…（首次按名字查要下载创作者索引，可能几十秒）':'识别中…';
    try{
      const result=await api('/api/follow/resolve',{method:'POST',
        body:JSON.stringify({lines,background:true})});
      sessionStorage.setItem('peach-resolve-job',result.job_id);
      state.textContent='';if(box)box.value='';
      if(form.isConnected)void wireResolveProgress();
    }catch(error){state.textContent=error.message||'查找失败';if(form.isConnected)void wireResolveProgress()}
    finally{form.dataset.busy='false';form.removeAttribute('aria-busy');
      if(prefix)prefix.innerHTML=icon('search')}
  };
  root.querySelectorAll('[data-follow-remove]').forEach(button=>button.onclick=async()=>{
    if(!confirm('不再追这个来源？已经抓到的条目会一并移除，媒体本身不受影响。'))return;
    button.disabled=true;
    try{
      await api('/api/follow/source',{method:'POST',
        body:JSON.stringify({action:'remove',id:+button.dataset.followRemove})});
      await openFollowManage(false);actionReceipt('已取消关注来源');
    }catch(error){button.disabled=false;actionFailure('取消关注来源',error)}
  });
  root.querySelectorAll('[data-follow-enabled]').forEach(control=>control.onchange=async()=>{
    const enabled=control.checked;control.disabled=true;
    try{
      await api('/api/follow/source',{method:'POST',body:JSON.stringify(
        {action:'enabled',id:Number(control.dataset.followEnabled),enabled})});
      await openFollowManage(false);actionReceipt(enabled?'已启用关注来源':'已暂停关注来源',{undo:async()=>{
        await api('/api/follow/source',{method:'POST',body:JSON.stringify(
          {action:'enabled',id:Number(control.dataset.followEnabled),enabled:!enabled})});
        await openFollowManage(false);
      }});
    }catch(error){control.checked=!enabled;control.disabled=false;actionFailure('更新关注来源',error)}
  });
  root.querySelectorAll('[data-follow-check]').forEach(button=>button.onclick=async()=>{
    if(followBusy)return;
    followBusy=true;let startedJob=false;const oldTitle=button.title;
    const oldAria=button.getAttribute('aria-label');
    const oldButton=button.innerHTML;
    setActionBusy(button);button.title='检查中…';
    button.setAttribute('aria-label','检查中…');
    button.innerHTML=`${spinnerHtml('检查中')}${button.matches('.frowicon')?'':'<span>检查中…</span>'}`;
    try{
      const id=button.dataset.followCheck;
      const sources=button.dataset.followSources?.split(',').filter(Boolean).map(Number);
      const started=await api('/api/follow/check',{method:'POST',
        body:JSON.stringify({...(sources?{sources}:id?{source:+id}:{}),background:true})});
      sessionStorage.setItem('peach-follow-job',started.job_id);
      followCheckReport=null;root.querySelector('.fcheckreports')?.remove();
      startedJob=true;
      if(button.isConnected)void wireFollowProgress();
    }catch(e){
      // 整个请求就失败了（断网、写入端不可达）：同样走那块报告，不弹 alert。
      followCheckReport={results:[{ok:false,error:e.message}]};
      followCheckToast(followCheckReport);
      const note=followCheckFailNote(followCheckReport);
       const box=$('#stats').querySelector('.fcheckreports');
       if(box)box.outerHTML=note;
      else $('#stats').querySelector('.fsec')?.insertAdjacentHTML('afterbegin',note);
    }
    finally{if(button.isConnected)followBusy=startedJob;setActionBusy(button,startedJob);button.innerHTML=oldButton;
      button.title=oldTitle;if(oldAria===null)button.removeAttribute('aria-label');
      else button.setAttribute('aria-label',oldAria)}
  });
  const saveAuthorAlias=async(canonical,alias,button)=>{
    button.disabled=true;
    try{
      await api('/api/follow/author-alias',{method:'POST',body:JSON.stringify(
        {action:'add',canonical,alias})});
      await openFollowManage(false);actionReceipt('已合并作者别名',{undo:async()=>{
        await api('/api/follow/author-alias',{method:'POST',body:JSON.stringify({action:'remove',alias})});
        await openFollowManage(false);
      }});
    }catch(error){button.disabled=false;actionFailure('合并作者别名',error)}
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
      await openFollowManage(false);actionReceipt('已移除作者别名');
    }catch(error){button.disabled=false;actionFailure('移除作者别名',error)}
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
      form.reset();await openFollowManage(false);actionReceipt('已保存来源凭据');
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
      await openFollowManage(false);actionReceipt('已清除来源凭据');
    }catch(error){button.disabled=false;actionFailure('清除来源凭据',error)}
  });
  root.querySelectorAll('[data-follow-bulk]').forEach(button=>button.onclick=async()=>{
    const to=button.dataset.followBulk;
    if(!confirm(`把当前全部「未看」标记为${to==='seen'?'已看':'已忽略'}？`))return;
    button.disabled=true;
    try{
      const pending=await api('/api/follow?status=new&limit=1000');
      const ids=(pending.groups||[]).flatMap(g=>[g.primary,...g.variants,...g.duplicates])
        .filter(item=>item.status==='new').map(item=>item.id);
      /* 一千条串行发是实测的卡点：请求之间的往返全靠等，界面按住不放。
         这里的每一条都是独立的写入，彼此没有顺序要求，交给有界并发。 */
      const results=await mapLimit(ids,6,id=>
        api('/api/follow/status',{method:'POST',body:JSON.stringify({item:id,to})}));
      const failed=results.filter(result=>!result.ok);
      await openFollowManage(false);
      if(failed.length)actionFailure(`批量更新 ${failed.length}/${ids.length} 项`,failed[0].error);
      else actionReceipt(`已批量标记 ${ids.length} 项`);
    }catch(error){button.disabled=false;actionFailure('批量更新关注状态',error)}
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
  closeAnchoredMenu();
  const providers=[...new Set((followData?.sources||[])
    .map(source=>source.provider_label).filter(Boolean))];
  /* 下拉里的每一行带上该来源的 favicon：label 只是展示名，图标要靠 provider
     查 SOURCE_ICONS，所以另建一张 label→provider 的映射。 */
  const providerIcon=new Map((followData?.sources||[]).filter(source=>source.provider&&source.provider_label)
    .map(source=>[source.provider_label,source.provider]));
  providers.forEach(provider=>{if(!fsrcProviders.has(provider))fsrcProviders.add(provider)});
  if(!providers.length){mount.innerHTML='';return}
  const label=()=>{const n=providers.filter(p=>!fsrcUnchecked.has(p)).length;
    return n===providers.length?'全部来源':`${n}/${providers.length} 个来源`};
  mount.innerHTML=`<button type="button" class="fbtn" data-srcfilter-toggle
      aria-expanded="false" aria-haspopup="menu" aria-controls="follow-source-menu"
      aria-label="${esc(label())}" title="${esc(label())}">
      ${icon('list-filter')}<span data-srcfilter-label>${esc(label())}</span></button>
    <div class="popmenu fsrcmenu" id="follow-source-menu" role="menu" data-srcfilter-menu hidden>${providers.map(provider=>
      `<label>${checkboxHtml(`data-srcfilter="${esc(provider)}"${fsrcUnchecked.has(provider)?'':' checked'}`)}
        ${sourceIcon(providerIcon.get(provider)||'')}<span>${esc(provider)}</span></label>`).join('')}</div>`;
  const toggle=mount.querySelector('[data-srcfilter-toggle]');
  const menu=mount.querySelector('[data-srcfilter-menu]');
  wireAnchoredMenu(mount,toggle,menu);
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
      ${checkboxHtml(`data-pick="${index}-${ci}" value="${esc(c.url)}"`
        +` data-author="${esc(c.author||'')}"`
        +` data-label="${esc(c.label)}"${c.known?' disabled':' checked'}`)}
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
    setActionBusy(addButton);
    let done=0;const failures=[],sources=[];
    for(const input of picked){
      state.innerHTML=`${spinnerHtml('添加中')}<span>添加中… ${++done}/${picked.length}</span>`;
      try{
        const registered=await api('/api/follow/source',{method:'POST',body:JSON.stringify(
          {action:'add',url:input.value,label:input.dataset.label,
           author:input.dataset.author,defer_check:true})});
        sources.push(registered.source);
      }catch(error){
        // 一条失败不该把其余的一起丢掉，逐条报。
        failures.push(`${input.dataset.label}：${error.message}`);
      }
    }
    if(sources.length){try{
      const started=await api('/api/follow/check',{method:'POST',body:JSON.stringify({sources,background:true})});
      sessionStorage.setItem('peach-follow-job',started.job_id);
    }catch(error){failures.push(error.message)}}
    if(failures.length){
      state.textContent=failures.join('；');
      setActionBusy(addButton,false);
      return;
    }
    await openFollowManage(false);
    actionReceipt(`已添加 ${picked.length} 个关注来源`);
  };
}

async function followWrite(button,path,body){
  const card=button.closest('.followitem'),state=card?.querySelector('.fstate');
  const before=card?.dataset.status||'new';
  setActionBusy(button);
  try{
    await api(path,{method:'POST',body:JSON.stringify(body)});
    await openFollow(false);
    const saving=path==='/api/follow/save',to=body.to;
    const labels={new:'已恢复未看',seen:'已标记已看',ignored:'已忽略'};
    actionReceipt(saving?'已保存到账本':(labels[to]||'已更新关注状态'),{undo:!saving&&before!=='saved'?async()=>{
      await api('/api/follow/status',{method:'POST',body:JSON.stringify({item:body.item,to:before})});
      await openFollow(false);
    }:null});
  }catch(e){
    // 只读端（reader）写入必然 409，那是正常状态；照实显示比静默失败好。
    if(state)state.textContent=e.message;
    actionFailure(path==='/api/follow/save'?'保存到账本':'更新关注状态',e);
  }finally{
    setActionBusy(button,false);
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
/* 标签页有两套词表：本地是 ledger 里的中文标签，在线是关注页那套 booru 英文标签。
   计数含义（作品数 / 更新数）、类别划分和点击后去哪儿三者都不同，混在一列只会
   互相说谎，所以用范围切换分开。字母表对在线那套正合适——实测 3582 个标签全是
   ASCII；本地全是中文，做字母表只会得到一个「中文」分组。 */
let tagIndexMode='alphabet',tagIndexCategory='all',tagIndexScope='local',indexRequestSeq=0;
const TAG_CATEGORIES=[['all','全部'],['meta','影片属性'],['relationship','人物关系'],
  ['role','角色设定'],['appearance','外貌身材'],['scene','情境场所'],['story','故事剧情'],
  ['position','性交体位'],['general','其他内容']];
const ONLINE_TAG_CATEGORIES=[['all','全部'],['general','通用'],['artist','作者'],
  ['character','角色'],['copyright','作品'],['metadata','元数据']];
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
/* 艺人索引版式，思路同 JAV 大图：列宽不变、只把图从圆框拉成竖幅，一屏里的人数
   不变而每张脸更大；紧凑就是圆头像那一屏。控件与 JAV 版式、关注列表版式共用
   iconSwitchHtml，切换只改容器上的 data-layout——版式是纯展示层的事，不重画列表，
   也不重新请求。 */
const PEOPLE_LAYOUTS=[['big','大图 · 竖幅头像','maximize'],['compact','紧凑 · 圆形头像','layout-grid']];
function peopleIndexLayout(){
  return allowedSetting(appSettings.peopleLayout,PEOPLE_LAYOUTS.map(([k])=>k),'big');
}
function peopleLayoutButtons(){
  return iconSwitchHtml('people-layout','艺人索引版式',PEOPLE_LAYOUTS,peopleIndexLayout(),
    {attr:'data-people-layout'});
}
function setPeopleIndexLayout(value){
  appSettings.peopleLayout=value;
  saveSettings();
  document.querySelectorAll('.igrid').forEach(grid=>{grid.dataset.layout=peopleIndexLayout()});
}
/* 一格人：圆框或竖幅头像、名字、一个读数。索引页和事务所名册摆的是同一样东西，
   区别只在读数的口径，所以模板只有这一份，版式也由同一个 `.igrid[data-layout]` 管。

   取景挂在圆框上而不是 img 上：竖幅裁到 3:4 时几何居中会切掉脸，而 img 由八处共用的
   avatarInner 拼，两个版式都只能从容器这一侧改。 */
function personCellHtml(x,kind,countText){
  const face=faceOrigin(x.avatar_focus);
  const ref=x.entity_id||x.id;
  /* 公司这一格不退到代表作截图，和它自己的资料页保持同一条判据：那是某部片的画面，
     摆在公司名下就是替它拿别人的脸当门面，同一个厂牌两个页面还会各出各的图。 */
  const company=kind==='studio'||kind==='agency';
  return `<button class="icell" data-k="${esc(x.k)}" data-kind="${kind}">
      <span class="ring"${face?` style="--face:${face}"`:''}>${avatarInner(x.k,
        ref?{id:ref,has_image:x.has_image}:null,
        x.has_avatar&&!company?x.rep:null, kind, x.mark, x.has_logo?x.k:'')}</span>
      <span class="nm">${esc(x.k)}</span><span class="n">${countText}</span></button>`;
}
const INDEX_TITLES={performers:'艺人',creators:'创作者',studios:'厂牌',
                    agencies:'事务所',tags:'标签'};
/* 厂牌与事务所是两种实体，不是同一份数据的两种筛选：厂牌出片，事务所出人，一位女优
   可以同一年给多个厂牌拍片而只属于一家事务所。所以这个开关切的是路径，不是筛选。 */
const MAKER_INDEX_KINDS=[['studios','厂牌','building'],['agencies','事务所','briefcase']];
function makerModeHtml(kind){
  return `<div class="viewmodes">`+MAKER_INDEX_KINDS.map(([key,label,symbol])=>
    `<button data-index-kind="${key}" aria-pressed="${kind===key}">${icon(symbol)}${label}</button>`
    ).join('')+`</div>`;
}
/* refine=true 表示这一次是筛选框自己重跑，不是一次页面进入：既不铺骨架，也不重画表头。 */
async function openIndex(kind,q,push=true,refine=false){
  releaseHoverPreviews();
  const requestSeq=++indexRequestSeq;
  document.body.classList.remove('entity-open');
  delete $('#index').dataset.entityKind;delete $('#index').dataset.entityName;
  /* 圆头像那一档索引：四种实体同一套版式、同一条取图链，区别只在 kind。 */
  const people=Object.prototype.hasOwnProperty.call(ROUTE_ENTITIES,kind);
  const entityKind=ROUTE_ENTITIES[kind]||'performer';
  const indexLimit=people?120:180;
  const indexQuery=new URLSearchParams();if(q)indexQuery.set('q',q);
  const onlineTags=kind==='tags'&&tagIndexScope==='online';
  if(kind==='tags'){
    indexQuery.set('view',tagIndexMode);
    if(onlineTags)indexQuery.set('scope','online');
    if(tagIndexCategory!=='all')indexQuery.set('category',tagIndexCategory)}
  if(push)route('/'+kind+(indexQuery.size?'?'+indexQuery:''),!!q);
  showHomeSurfaces();
  // 必须在 showHomeSurfaces 之后加：它会清掉这两个类并恢复顶部横条，
  // 写在前面等于自己加完自己删。
  document.body.classList.add('index-open');
  disposeStage(false);
  /* 骨架只盖真正在等的内容区。筛选重跑时页面已经在这儿了，把骨架铺上去会连筛选框
     一起吃掉——同步就能给出的控件不进骨架，正在打字的那个更不能。 */
  if(!refine)showIndexLoading('正在读取'+(INDEX_TITLES[kind]||'标签'));
  /* 在线标签走关注页那套统计，形状与 /api/index 一致，所以分页、搜索和「载入更多」
     这三处现成的机制换个地址就能用。 */
  const indexApi=offset=>onlineTags
    ?'/api/follow/tags?types=all&limit='+indexLimit+'&offset='+offset+
      (tagIndexCategory!=='all'?'&type='+encodeURIComponent(tagIndexCategory):'')+
      (q?'&q='+encodeURIComponent(q):'')
    :'/api/index?kind='+kind+'&limit='+indexLimit+'&offset='+offset+
      (q?'&q='+encodeURIComponent(q):'')+
      (kind==='tags'&&tagIndexCategory!=='all'?'&category='+encodeURIComponent(tagIndexCategory):'');
  const d=await api(indexApi(0));
  if(requestSeq!==indexRequestSeq||location.pathname!=='/'+kind)return;
  $('#index').hidden=false;buildEdge(); $('#grid').innerHTML=''; $('#count').textContent='';
  $('#loadSentinel').hidden=true; $('#shortsSec').hidden=true;
  const title=INDEX_TITLES[kind]||'标签';
  const tagItems=[...d.items];
  const tagGroups=items=>{
    const groups={};[...items].sort((a,b)=>a.k.localeCompare(b.k,'zh-CN',{numeric:true,sensitivity:'base'})).forEach(x=>{
      const ch=tagLabel(x.k).normalize('NFKC').trim().charAt(0).toUpperCase();
      const key=/[A-Z]/.test(ch)?ch:(/[0-9]/.test(ch)?'#':(/[\u3400-\u9fff]/.test(ch)?'中文':'其他'));
      (groups[key]||(groups[key]=[])).push(x)});
    return Object.entries(groups).sort(([a],[b])=>a.localeCompare(b,'zh-CN')).map(([letter,items])=>
      `<section class="alphagroup"><h3>${letter}</h3><div class="alphalist">${items.map(x=>
        `<button class="alphatag ${onlineTags?'r34-'+(x.cat||'unknown'):(x.cat||'general')}" data-k="${esc(x.k)}" aria-pressed="${selectedIndexTags.has(x.k)}"><span>${esc(tagLabel(x.k))}</span><span class="n">${x.n.toLocaleString()}</span></button>`).join('')}</div></section>`).join('')};
  const peopleHtml=items=>items.map(x=>
    /* 事务所数的是人：它名下那 N 个视频是成员拍的，只报视频数会让「这家有几个人」
       这个它唯一独有的读数消失。数字带单位，否则 411 读不出是人还是片。 */
    personCellHtml(x,entityKind,entityKind==='agency'
      ?`${(x.members||0).toLocaleString()} 人`:x.n.toLocaleString())).join('');
  const tagHtml=items=>tagIndexMode==='alphabet'?`<div class="alphabet">${tagGroups(items)}</div>`:`<div class="tagwall index-tags">`+items.map(x=>`<button class="tg ${onlineTags?'r34-'+(x.cat||'unknown'):(x.cat||'general')}" data-k="${esc(x.k)}" aria-pressed="${selectedIndexTags.has(x.k)}"
        >${esc(tagLabel(x.k))}
        <span class="n">${x.n.toLocaleString()}</span></button>`).join('')+`</div>`;
  /* 公司格和人格在大图版式下要的形状不一样：竖幅是给脸留的，方标进去左右各被裁掉
     一截。这一格里装的是什么，只有这里知道，所以在这里写进 DOM。 */
  const cells=entityKind==='studio'||entityKind==='agency'?'company':'people';
  const body=people?`<div class="igrid" data-cells="${cells}" data-layout="${
    peopleIndexLayout()}">${peopleHtml(d.items)}</div>`:tagHtml(tagItems);
  const categoryOptions=onlineTags?ONLINE_TAG_CATEGORIES:TAG_CATEGORIES;
  const visibleTagCategories=categoryOptions.filter(([key])=>key==='all'||Number(d.categories?.[key]||0)>0);
  const categoryFilters=kind==='tags'?`<div class="tagfilters" aria-label="标签类型">${visibleTagCategories.map(([key,label])=>
    `<button class="${key}" data-tag-category="${key}" aria-pressed="${tagIndexCategory===key}">${label}</button>`).join('')}</div>
    `:'';
  /* 多选面板拼的是目录筛选，只在本地范围出现；在线分类来自上游 booru tag_type。 */
  const filters=categoryFilters+(kind==='tags'&&!onlineTags?`
    <div class="tagselection" data-tag-selection hidden>
      <label>${checkboxHtml(`data-tag-match-any ${tagIndexMatch==='any'?'checked':''}`)}<span><b>广泛匹配</b><small>开启后匹配任一所选标签；关闭后必须同时包含全部标签。</small></span></label>
      <span class="mono" data-tag-selected>已选 0 个标签</span>
      <button type="button" data-tag-clear>清空</button>
      <button type="button" class="primary" data-tag-apply disabled>显示结果</button>
    </div>`:'');
  const countText=`${tagItems.length}${d.has_more?'+':''} 项`;
  /* 筛选重跑不重画表头：输入框是同一个节点，焦点、光标位置和中文输入法正在组的字
     才不会在 300 ms 后被换掉。表头里随查询变的只有计数一处，单独改它。 */
  if(refine&&$('#iq')){
    $('#indexCount').textContent=countText;
    $('#indexFilters').innerHTML=filters;
    $('#indexBody').innerHTML=body;
    $('#indexMore').hidden=!d.has_more;
  }else $('#index').innerHTML=`<div class="ihead">
      <h2 class="disp indexheading">${kind==='tags'?icon('tags'):''}${title}</h2>
      <span class="mono" id="indexCount">${countText}</span>
      ${kind==='tags'?`<div class="viewmodes"><button data-tag-scope="local" aria-pressed="${!onlineTags}">${icon('hard-drive')}本地</button><button data-tag-scope="online" aria-pressed="${onlineTags}">${icon('rss')}在线</button></div>
      <div class="viewmodes"><button data-tag-view="cloud" aria-pressed="${tagIndexMode==='cloud'}">${icon('tags')}标签云</button><button data-tag-view="alphabet" aria-pressed="${tagIndexMode==='alphabet'}">${icon('text-aa')}字母表</button></div>`:''}
      ${MAKER_INDEX_KINDS.some(([key])=>key===kind)?makerModeHtml(kind):''}
      ${people?peopleLayoutButtons():''}
      ${searchInputHtml({id:'iq',label:'过滤'+title,value:q||''})}
    </div><div id="indexFilters">${filters}</div><div id="indexBody">${body}</div><button class="indexmore" id="indexMore" type="button" ${d.has_more?'':'hidden'}>载入更多</button>`;
  const iq=$('#iq');let it2;
  const refineIndex=()=>{clearTimeout(it2);
    it2=setTimeout(()=>openIndex(kind,iq.value.trim(),true,true),300)};
  /* 中文输入法在选字过程中一样发 input，事件上的 isComposing 是唯一可靠的判据：
     拿还没定型的拼音去筛选，筛的是「zhon」这种半截输入。组完字由 compositionend 接手。 */
  iq.oninput=e=>{if(e.isComposing)return;refineIndex()};
  iq.oncompositionend=refineIndex;
  /* 只读筛选不配提交按钮，回车就是「别等那 300 ms，现在就查」。组字过程中的回车
     是在定字，放过去会拿半截拼音发请求。 */
  iq.onkeydown=e=>{if(e.isComposing||e.key!=='Enter')return;
    e.preventDefault();clearTimeout(it2);openIndex(kind,iq.value.trim(),true,true)};
  wireIconSwitch($('#index'),'data-people-layout',setPeopleIndexLayout);
  /* 厂牌与事务所各有自己的地址，所以这个开关走的是 openIndex 的另一条 kind，
     不是在同一批数据上再筛一次。过滤词跟着走：它问的是同一个问题。 */
  $('#index').querySelectorAll('[data-index-kind]').forEach(b=>b.onclick=()=>{
    if(kind===b.dataset.indexKind)return;
    openIndex(b.dataset.indexKind,$('#iq').value.trim(),true)});
  $('#index').querySelectorAll('[data-tag-scope]').forEach(b=>b.onclick=()=>{
    if(tagIndexScope===b.dataset.tagScope)return;
    tagIndexScope=b.dataset.tagScope;
    // 在线标签全是英文，字母表才是它的形态；切过去时顺手换上，不必用户再点一次。
    if(tagIndexScope==='online')tagIndexMode='alphabet';
    tagIndexCategory='all';
    selectedIndexTags.clear();
    openIndex('tags',$('#iq').value.trim(),true)});
  $('#index').querySelectorAll('[data-tag-view]').forEach(b=>b.onclick=()=>{
    tagIndexMode=b.dataset.tagView;openIndex('tags',$('#iq').value.trim(),true)});
  $('#index').querySelectorAll('[data-tag-category]').forEach(b=>b.onclick=()=>{
    tagIndexCategory=b.dataset.tagCategory;openIndex('tags',$('#iq').value.trim(),true)});
  const wireIndexEntries=root=>root.querySelectorAll('[data-k]').forEach(b=>b.onclick=()=>{
    if(people){openEntity(b.dataset.kind,b.dataset.k);return}
    /* 在线标签只在关注页有意义——它标注的是还没入库的在线更新，拿去筛目录必然
       一条不中。所以直接进「关注 · 这个标签」，并且绕过多选：多选拼的是目录筛选。 */
    if(onlineTags){
      followAuthor='';followProvider='';followMediaView='videos';followFilter='';
      followTags=new Set([b.dataset.k]);
      $('#index').hidden=true;route(followViewPath());openFollow(false);return}
    if(selectMode){const key=b.dataset.k;selectedIndexTags.has(key)?selectedIndexTags.delete(key):selectedIndexTags.add(key);paintTagIndexSelection();return}
    $('#index').hidden=true;state={...state,state:'',tag:b.dataset.k,tag_match:'all'};route(homePath());buildBars();load(true)});
  wireIndexEntries($('#indexBody'));
  if(kind==='tags'&&!onlineTags){
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
function performerLabel(it){return it&&it.is_jav?'女优':'艺人'}
let entityRequestSeq=0,entityJavLayout=false;
async function fetchEntityItems(kind,name,filters,offset=0){
  const p=new URLSearchParams();p.set(kind,name);p.set('limit','48');p.set('offset',String(offset));
  p.set('sort',filters.sort||'new');
  if(filters.dir)p.set('dir',filters.dir);
  if(filters.sort==='seed')p.set('seed',state.seed);
  if(offset)p.set('count','0');
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&key!==kind&&key!=='sort')p.set(key,filters[key])});
  // 资料页继承 JAV 开关：女优页和厂牌页同样是按番号浏览的语境。
  if(state.jav==='1')p.set('jav','1');
  const items=await api('/api/items?'+p);cache(items.items);return items
}
let entityCollectionPage={items:[],total:0,has_more:false};
/* 资料页作品集的表头与首页计数行同源：排序条由 filters 决定，`视频 · N` 由响应决定。 */
const entityCollectionSortsHtml=filters=>`<span class="sorts">
      <button class="batchaction entitybatch" type="button" title="换一批" aria-label="换一批">${icon('refresh-cw')}</button>
      ${javActive()?javLayoutButtons():''}
      ${sortOptions().map(([key,label])=>sortButtonHtml(
        key,label,filters.sort||'new',filters.dir,'data-entity-sort')).join('')}</span>`;
function wireEntityCollectionHead(section,kind,name,filters){
  wireJavLayoutButtons(section);
  section.querySelector('.entitybatch').onclick=()=>{
    state.seed=rollSeed();updateEntityCollection(kind,name,{...filters,sort:'seed'},true)};
  section.querySelectorAll('[data-entity-sort]').forEach(button=>button.onclick=()=>{
    const next=nextSortState(button.dataset.entitySort,filters.sort||'new',filters.dir);
    if(next)updateEntityCollection(kind,name,{...filters,...next},true)});
}
/* 换列和翻方向此刻就已确定，用不着等一次请求才在界面上生效：先把排序条重画成
   最终样子，只让会变的 `视频 · N` 换成骨架。标题、标签条和已经铺好的网格不动。 */
function markEntityCollectionBusy(kind,name,filters){
  const section=$('#index').querySelector('.entitysection');
  const head=section&&section.querySelector('.entitycollectionhead');
  if(!head)return;
  head.setAttribute('aria-busy','true');
  head.querySelector('.sorts').outerHTML=entityCollectionSortsHtml(filters);
  head.querySelector('h3').innerHTML='<span class="countskeleton"></span>';
  wireEntityCollectionHead(section,kind,name,filters);
}
/* 事务所名册。和艺人索引摆的是同一格、同一套版式设置，只是这批人随资料页一起下来了，
   不再单独请求；读数写的是这个人有多少视频。 */
function renderAgencyRoster(people){
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  section.innerHTML=`<div class="entitycollectionhead"><h3>艺人 · ${
      people.length.toLocaleString()}</h3></div>
    <div class="igrid" data-layout="${peopleIndexLayout()}">${
      people.map(x=>personCellHtml(x,'performer',x.n.toLocaleString())).join('')}</div>`;
  section.querySelectorAll('[data-k]').forEach(button=>button.onclick=()=>
    openEntity('performer',button.dataset.k));
  scheduleStickySurfaces();
}
function renderEntityCollection(kind,name,items,filters,append=false){
  // 资料页的标签同样可以叠加，表头把生效的几个都写出来。
  const entityTags=tagList(filters.tag).map(tagLabel);
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  if(!append){
    renderedPartGroups.clear();renderedEditionGroups.clear();
    entityCollectionPage={items:[...(items.items||[])],total:items.total||0,
      has_more:items.has_more==null?(items.items||[]).length<(items.total||0):!!items.has_more};
    section.innerHTML=`<div class="entitycollectionhead"><h3></h3>${entityCollectionSortsHtml(filters)}</div>
      <div class="grid"></div><button class="entitymore" type="button">载入更多</button>`;
    section.dataset.total=String(items.total||0);
    section.querySelector('h3').textContent=`视频 · ${(items.total||0).toLocaleString()}${entityTags.length?' · '+entityTags.join(' · '):''}`;
    wireEntityCollectionHead(section,kind,name,filters);
  }else{
    entityCollectionPage.items.push(...(items.items||[]));
    entityCollectionPage.has_more=!!items.has_more;
  }
  const grid=section.querySelector('.grid');
  grid.insertAdjacentHTML('beforeend',
    collapseEditionGroups(collapseMultipartItems(items.items)).map(it=>cardHtml(it)).join(''));
  wireCards(grid);
  const more=section.querySelector('.entitymore');
  more.hidden=!entityCollectionPage.has_more;
  const requestMore=async()=>{if(more.hidden||more.disabled)return;more.disabled=true;const seq=entityRequestSeq;
    try{const next=await fetchEntityItems(kind,name,filters,entityCollectionPage.items.length);
      if(seq===entityRequestSeq&&$('#index').dataset.entityKind===kind&&$('#index').dataset.entityName===name)
        renderEntityCollection(kind,name,next,filters,true)}
    finally{if(seq===entityRequestSeq)more.disabled=false}};
  wireLoadMore(more,requestMore);
  scheduleStickySurfaces();
}
async function updateEntityCollection(kind,name,filters,push=true){
  // 标签是作品筛选，点了就回到作品视图：留在照片或名册里既不生效，标签条也会自相矛盾。
  entityMediaView=emptyMediaView();
  agencyRosterView='videos';
  const search=entityFilterSearch(filters);
  if(push)route(entityPath(kind,name)+(search?'?'+search:''));
  barsContext={type:'entity',kind,name,filters:{...filters}};
  const seq=++entityRequestSeq;
  markEntityCollectionBusy(kind,name,filters);
  const items=await fetchEntityItems(kind,name,filters);
  if(seq!==entityRequestSeq)return;
  renderEntityMediaToggle(kind,name,filters);
  $('#index').querySelectorAll('[data-entity-tag]').forEach(b=>
    b.setAttribute('aria-pressed',String(tagPressed(filters.tag,b.dataset.entityTag))));
  renderEntityCollection(kind,name,items,filters)
}
/* ── 资料页的照片 ─────────────────────────────────────────────────────────────
   图集就是目录：账本里没有图集实体，`<作品目录>\P\001.jpg` 这种约定只保留在后端，
   页面不先造一层固定比例封面，照片标签直接进入瀑布流，再点图进入灯箱。
   瀑布流用 CSS `column-count` 而不是 JS 布局：图片行没有宽高，等宽多列流式排版正好
   不需要知道比例，也就不用等图片加载完再算位置。
   缩略图一律走 `/photo-thumb`（服务端缓存），只有灯箱里的大图读 `/photo` 原图——
   PikPak 是计费来源，瀑布流直接铺原图等于一屏付几十兆流量。 ── */
function emptyMediaView(){return {media:'videos',set:0}}
const parseMediaView=search=>{const params=new URLSearchParams(search),set=params.get('set')||'';
  return {media:params.get('media')==='photos'?'photos':'videos',set:/^\d+$/.test(set)?Number(set):0}};
const entityViewSearch=(filters,view)=>{const params=new URLSearchParams(entityFilterSearch(filters));
  if(view&&view.media==='photos'){params.set('media','photos');if(view.set)params.set('set',String(view.set))}
  return params.toString()};
const routeEntityView=(kind,name,view)=>{
  const filters=barsContext.type==='entity'?barsContext.filters:emptyEntityFilters();
  const search=entityViewSearch(filters,view);
  route(entityPath(kind,name)+(search?'?'+search:''))};
const photoTotalOf=()=>entityPhotos&&!entityPhotos.error?(entityPhotos.total||0):0;

/* 这一页当前是哪个视图。名册和媒体不共用 `entityMediaView`：地址栏只认 `media`，
   而名册是事务所页的默认视图，进页面就该在那里，不靠一个参数撑着。 */
const entityViewNow=kind=>kind==='agency'&&agencyRosterView==='people'&&agencyRoster.length
  ?'people':(entityMediaView.media==='photos'?'photos':'videos');

function renderEntityMediaToggle(kind,name,filters){
  const controls=$('#index').querySelector('.entitymediaview');if(!controls)return;
  const now=entityViewNow(kind);
  controls.querySelectorAll('[data-media-view]').forEach(button=>{
    const media=button.dataset.mediaView;
    button.setAttribute('aria-pressed',String(now===media));
    button.onclick=()=>switchEntityMedia(kind,name,filters,media);
  });
}

async function switchEntityMedia(kind,name,filters,media){
  if(entityViewNow(kind)===media&&!entityMediaView.set)return;
  agencyRosterView=media==='people'?'people':'videos';
  if(media==='people'){
    entityMediaView=emptyMediaView();
    routeEntityView(kind,name,entityMediaView);
    renderEntityMediaToggle(kind,name,filters);
    renderAgencyRoster(agencyRoster);
    return;
  }
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
      data-drop="closest:.photocell"></button>`;

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
  wireLoadMore(more,requestMore);
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

async function revealSource(id,status,{button=null}={}){
  if(button?.getAttribute('aria-busy')==='true')return;
  const buttonHtml=button?.innerHTML,label=button?.textContent.trim();
  if(button){setActionBusy(button);
    button.innerHTML=`${spinnerHtml('正在定位')}${label?`<span>${esc(label)}</span>`:''}`}
  status.textContent='';
  try{
    await api('/api/reveal',{method:'POST',body:JSON.stringify({id})});
    status.textContent='';toast({text:'已在资源管理器中显示'});
  }catch(e){status.textContent=sourceHint(e.message)}
  finally{if(button){setActionBusy(button,false);button.innerHTML=buttonHtml}}
}

async function syncMissing(id,status,done){
  status.textContent='正在核对目录…';
  try{
    const r=await api('/api/purge-missing',{method:'POST',body:JSON.stringify({id})});
    if(r.ok===false){status.textContent=sourceHint(r.error);return}
    status.textContent=r.removed
      ? `已把 ${r.removed} 项移入回收站（核对 ${r.checked} 项${r.unreadable?`，${r.unreadable} 项未能读取`:''}）`
      : r.unreadable
        ? `目录有 ${r.unreadable} 项暂时无法读取，本次未改动`
        : `目录内 ${r.checked} 项都还在，无需改动`;
    if(r.removed){
      const ids=(r.items||[]).map(item=>item.id);
      if(done)done(r);
      actionReceipt(`已把 ${r.removed} 项移入回收站`,{undo:ids.length?async()=>{
        await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation:'restore'})});
        if(done)done({removed:0,restored:ids.length});
      }:null});
    }else actionReceipt('目录核对完成，无需改动');
  }catch(e){status.textContent=sourceHint(e.message);actionFailure('核对目录',e)}
}

/* 两个动作在照片详情里和作品标题旁复用；状态位置由各自表面决定。 */
const sourceToolButtons=id=>`
    <button type="button" data-reveal="${id}" title="在文件管理器里打开源文件所在目录"
      aria-label="定位源文件">${icon('folder-open')}</button>
    <button type="button" data-sync="${id}" title="核对该目录：磁盘上已删除的，移入 Peach 回收站"
      aria-label="同步删除">${icon('refresh-cw')}</button>`;
function sourceTools(id){return `<div class="srctools">${sourceToolButtons(id)}
    <span class="srcstate" aria-live="polite"></span></div>`}

function wireSourceTools(root,done){
  const status=root.querySelector('.srcstate');
  if(!status)return;
  const reveal=root.querySelector('[data-reveal]');
  const sync=root.querySelector('[data-sync]');
  if(reveal)reveal.onclick=()=>revealSource(Number(reveal.dataset.reveal),status,{button:reveal});
  if(sync)sync.onclick=()=>syncMissing(Number(sync.dataset.sync),status,done);
}

/* 灯箱按需加载 Swiper：大图轮播、底部缩略图条和键盘左右键都是它自带的模块，
   没必要自己写一遍；但它只有看照片时才用得上，不该进首屏。 */
let swiperLoader=null,activeLightbox=null;
/* 灯箱既服务本地照片墙，也服务关注页的在线图集。两边共用信息面板，但动作不同：
   本地图可按 asset id 定位源文件；在线图只展示来源、序号、尺寸和可取得的大小。 */
const photoSlide=item=>item.follow
  ?{src:item.src,thumb:item.thumb||item.src,name:item.name||'',asset:null,
    source:item.source||'在线图片',size:item.size,position:item.position,total:item.total}
  :{src:`/photo?id=${item.id}`,thumb:`/photo-thumb?id=${item.id}`,name:item.name||'',asset:item};
const loadSwiper=()=>swiperLoader||(swiperLoader=Promise.all([
  new Promise((resolve,reject)=>{
    const href='/vendor/swiper/14.2.0/swiper-bundle.min.css';
    const existing=document.querySelector(`link[href="${href}"]`);
    if(existing?.sheet){resolve();return}
    const style=existing||document.createElement('link');
    style.rel='stylesheet';style.href=href;
    style.addEventListener('load',resolve,{once:true});
    style.addEventListener('error',()=>reject(new Error('swiper styles unavailable')),{once:true});
    if(!existing)document.head.appendChild(style)}),
  window.Swiper?Promise.resolve(window.Swiper):new Promise((resolve,reject)=>{
    const script=document.createElement('script');
    script.src='/vendor/swiper/14.2.0/swiper-bundle.min.js';
    script.onload=()=>resolve(window.Swiper);
    script.onerror=()=>reject(new Error('swiper unavailable'));
    document.head.appendChild(script)})
]).then(([,SwiperCtor])=>SwiperCtor).catch(error=>{swiperLoader=null;throw error}));
const photoLightKeys=e=>{if(e.key!=='Escape')return;
  e.preventDefault();e.stopImmediatePropagation();
  if(activeLightbox?.detail?.isOpen()){activeLightbox.detail.dismiss(true);return}
  closePhotoLightbox()};
const PHOTO_ZOOM_MIN=10,PHOTO_ZOOM_MAX=400,PHOTO_ZOOM_STEP=10;

/* 缩放条显示相对原图像素的百分比，而不是相对「适应窗口」的变换倍数。
   因此大图初始可能是 34%，原大小才是 100%；Swiper 14 的 zoom.in(number)
   能直接接收目标倍数，既可低于 1 也可高于 1。 */
function wirePhotoZoom(box, main){
  const slider=box.querySelector('.photozoom input');
  const label=box.querySelector('.photozoom b');
  let target='fit';
  const image=()=>main.slides[main.activeIndex]?.querySelector('img');
  const fitPercent=()=>{
    const img=image();
    if(!img?.naturalWidth||!img.naturalHeight)return 100;
    return Math.min(100,img.offsetWidth/img.naturalWidth*100,img.offsetHeight/img.naturalHeight*100)
  };
  const show=percent=>{const value=Math.round(percent);slider.value=value;label.textContent=value+'%'};
  const apply=raw=>{
    const fit=fitPercent();
    const percent=raw==='fit'?fit:Math.min(PHOTO_ZOOM_MAX,Math.max(PHOTO_ZOOM_MIN,Number(raw)||fit));
    target=raw==='fit'?'fit':percent;show(percent);
    const ratio=percent/fit;
    if(Math.abs(ratio-1)<.001)main.zoom.out();
    else main.zoom.in(ratio);
  };
  const reset=()=>requestAnimationFrame(()=>apply('fit'));
  slider.oninput=()=>apply(Number(slider.value));
  box.querySelectorAll('[data-zoom-step]').forEach(b=>
    b.onclick=()=>apply(Number(slider.value)+Number(b.dataset.zoomStep)*PHOTO_ZOOM_STEP));
  box.querySelector('[data-photo-scale="fit"]').onclick=()=>apply('fit');
  box.querySelector('[data-photo-scale="original"]').onclick=()=>apply(100);
  main.on('slideChange',reset);
  main.on('zoomChange',(_swiper,scale)=>{if(scale)show(fitPercent()*scale)});
  box.querySelectorAll('.photomain img').forEach(img=>{
    if(!img.complete)img.addEventListener('load',()=>{if(img===image())apply(target)})});
  reset();
  return {resize:()=>apply(target)};
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
  const images=[...box.querySelectorAll('.photomain img')];
  let painted=index;
  const paint=at=>{
    const item=items[at];if(!item)return;
    const asset=item.asset,image=images[at];painted=at;
    toggle.hidden=false;
    title.textContent=(asset?.name||item.name)||'未命名图片';
    const resolution=image?.naturalWidth&&image?.naturalHeight
      ?`${image.naturalWidth} × ${image.naturalHeight}`:'';
    const sequence=!asset&&item.total>1?`第 ${item.position} / ${item.total} 张`:'';
    meta.textContent=asset
      ?[LOC[asset.location]||asset.location||'来源未知',fmtPhotoSize(asset.size)].join(' · ')
      :[item.source||'在线图片',sequence,resolution,item.size?fmtPhotoSize(item.size):'']
        .filter(Boolean).join(' · ');
    reveal.hidden=!asset;
    if(asset)reveal.dataset.photoReveal=String(asset.id);
    else reveal.removeAttribute('data-photo-reveal');
    status.textContent='';
    if(!asset&&image&&!image.complete)image.addEventListener('load',()=>{
      if(painted===at)paint(at)},{once:true});
  };
  const dismiss=returnFocus=>{panel.hidden=true;toggle.setAttribute('aria-expanded','false');
    if(returnFocus&&document.contains(toggle))toggle.focus()};
  const dismissOutside=target=>{if(panel.hidden||toggle.contains(target)||panel.contains(target))return false;
    dismiss();return true};
  toggle.onclick=()=>{if(panel.hidden){panel.hidden=false;toggle.setAttribute('aria-expanded','true');
      queueMicrotask(()=>{const target=reveal.hidden?title:reveal;target.focus()})}
    else dismiss()};
  reveal.onclick=()=>{if(reveal.dataset.photoReveal)
    revealSource(Number(reveal.dataset.photoReveal),status,{button:reveal})};
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
async function openPhotoLightbox(index,source=null){
  const items=(source||photoWallItems).map(photoSlide);
  if(!items.length||index<0||index>=items.length)return;
  let SwiperCtor;
  try{SwiperCtor=await loadSwiper()}
  catch(_e){window.open(items[index].src,'_blank','noopener');return}
  closePhotoLightbox();
  const box=document.createElement('div');
  box.className='photolight'+(items.length>1?' has-strip':'');
  box.innerHTML=`<button class="media-circle media-overlay photoclose" type="button" aria-label="关闭">${icon('x')}</button>
    <div class="swiper photomain"><div class="swiper-wrapper">${items.map(item=>
      `<div class="swiper-slide"><div class="swiper-zoom-container"><img src="${esc(item.src)}"
        alt="${esc(item.name)}" loading="lazy" referrerpolicy="no-referrer"></div></div>`).join('')}</div>
      <button class="media-circle media-overlay photonav back" type="button" aria-label="上一张">${icon('chevron-left')}</button>
      <button class="media-circle media-overlay photonav fwd" type="button" aria-label="下一张">${icon('chevron-left')}</button></div>
    <div class="photobar">
      <button class="photodetailtoggle" type="button" aria-expanded="false" aria-controls="photoDetail"
        aria-haspopup="dialog"
        aria-label="图片详情" title="图片详情">${icon('info')}</button>
      <div class="photocount mono" aria-live="polite">${index+1} / ${items.length}</div>
      <div class="photozoom">
        <button type="button" data-zoom-step="-1" aria-label="缩小">${icon('minus')}</button>
        <input type="range" min="${PHOTO_ZOOM_MIN}" max="${PHOTO_ZOOM_MAX}" step="1" value="100" aria-label="缩放">
        <button type="button" data-zoom-step="1" aria-label="放大">${icon('plus')}</button>
        <b class="mono">100%</b>
        <button class="photoscale" type="button" data-photo-scale="fit" aria-label="适应窗口" title="适应窗口">${icon('maximize')}</button>
        <button class="photoscale photooriginal mono" type="button" data-photo-scale="original" aria-label="原大小" title="原大小">1:1</button>
      </div></div>
    <section class="photodetail" id="photoDetail" role="dialog" aria-modal="false"
      aria-labelledby="photoDetailTitle" hidden>
      <div class="photodetailcopy"><h2 id="photoDetailTitle" data-middle-truncate tabindex="-1"></h2><span class="photodetailmeta"></span></div>
      <button type="button" data-photo-reveal="">${icon('folder-open')}<span>在资源管理器中显示</span></button>
      <span class="srcstate" aria-live="polite"></span>
    </section>
    <div class="swiper photostrip"><div class="swiper-wrapper">${items.map(item=>
      `<div class="swiper-slide"><img src="${esc(item.thumb)}" alt="" loading="lazy" referrerpolicy="no-referrer"></div>`).join('')}</div></div>`;
  document.body.appendChild(box);
  document.body.classList.add('photolight-open');
  const counter=box.querySelector('.photocount');
  const strip=new SwiperCtor(box.querySelector('.photostrip'),{
    slidesPerView:'auto',spaceBetween:8,freeMode:true,watchSlidesProgress:true,
    centeredSlides:true,slideToClickedSlide:true});
  const centerThumb=(at,speed=200)=>strip.slideTo(at,speed);
  const main=new SwiperCtor(box.querySelector('.photomain'),{
    initialSlide:index,zoom:{minRatio:.01,maxRatio:100},keyboard:{enabled:true},lazyPreloadPrevNext:1,
    // 上下滚也翻页：看图时手在滚轮上，没人愿意为了换一张去够左右键或按钮。
    mousewheel:{enabled:true,forceToAxis:false},
    thumbs:{swiper:strip},
    navigation:{prevEl:box.querySelector('.photonav.back'),nextEl:box.querySelector('.photonav.fwd')},
    on:{slideChange(){counter.textContent=`${this.activeIndex+1} / ${items.length}`;
      centerThumb(this.activeIndex)}}});
  centerThumb(index,0);
  const zoomBar=wirePhotoZoom(box,main);
  const detail=wirePhotoDetail(box,items,index);
  main.on('slideChange',()=>detail.paint(main.activeIndex));
  /* Swiper 只在自己构造的那一刻量一次容器。灯箱是插进已经布好版的页面里的，
     窗口一改大小（或首屏字体、滚动条落定得比构造晚）slide 就停在旧宽度上，
     大图按错误的框缩放，看起来就是「显示不全」。挂个 ResizeObserver 让它重量。 */
  const resize=new ResizeObserver(()=>{main.update();strip.update();zoomBar.resize()});
  resize.observe(box);
  activeLightbox={box,main,strip,resize,zoomBar,detail};
  box.querySelector('.photoclose').onclick=closePhotoLightbox;
  // 主画布铺满视口后，黑色留白属于 zoom 容器而不是最外层；两者都视为背景。
  // 点图片、缩略图条、工具栏和翻页按钮仍不退出。
  box.addEventListener('click',e=>{
    if(detail.dismissOutside(e.target))return;
    if(e.target===box||e.target.classList.contains('swiper-zoom-container'))closePhotoLightbox()});
  document.addEventListener('keydown',photoLightKeys,true);
}

/* 统称选择器的行为。换统称改的是 `entity.canonical_name` 这个真相字段，所以只在
   服务端换完之后才重画这一页；撤销同样是一次真实写回，不在本地把标题改回去当成功。
   页面重画会把菜单连同这里绑的处理器一起换掉，每次渲染重新绑一遍。 */
function wireNamePicker(kind,current){
  const mount=$('#index').querySelector('[data-namepick]');
  if(!mount)return;
  const toggle=mount.querySelector('[data-namepick-toggle]');
  const menu=mount.querySelector('[data-namepick-menu]');
  const anchored=wireAnchoredMenu(mount,toggle,menu);
  const rename=(from,to)=>api('/api/entity-name',
    {method:'POST',body:JSON.stringify({kind,name:from,canonical:to})});
  menu.querySelectorAll('[data-namepick-name]').forEach(item=>item.onclick=async()=>{
    const chosen=item.dataset.namepickName;
    anchored.setOpen(false);
    if(chosen===current)return;
    /* 换统称要重写整条实体的扁平投影，先把代价说清再问。确认键、标题和成功回执共用
       「更改统称」这一个动词；写入失败时弹层留在原地，原因写在正文下方等重试。 */
    const {confirmed,result}=await confirmModal({
      title:'更改统称',
      body:`「${chosen}」将成为这条实体的规范名，「${current}」留作别名。`
        +'作品上的署名、搜索和标签都会跟着改写。',
      confirmLabel:'更改统称',
      onConfirm:()=>rename(current,chosen)});
    if(!confirmed||!result?.changed)return;
    actionReceipt(`已把统称更改为 ${result.canonical_name}`,{undo:async()=>{
      await rename(result.canonical_name,result.previous_name);
      await openEntity(kind,result.previous_name)}});
    await openEntity(kind,result.canonical_name);
  });
}

async function openEntity(kind,name,push=true){
  releaseHoverPreviews();
  const filters=push?emptyEntityFilters():parseEntityFilters(location.search);
  if(kind==='creator')filters.creator='';
  const expectedPath=entityPath(kind,name);
  // 深链和前进后退要能直接落到照片视图；点进来的新页面一律从作品开始。
  entityMediaView=push?emptyMediaView():parseMediaView(location.search);
  const search=entityViewSearch(filters,entityMediaView);
  if(push)route(expectedPath+(search?'?'+search:''));
  barsContext={type:'entity',kind,name,filters};
  showHomeSurfaces();
  disposeStage(false);
  document.body.classList.add('entity-open');
  showIndexLoading('正在读取资料');
  detailReturnBarsContext=null;
  entityJavLayout=false;
  agencyRosterView='people';
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
  /* 大位这条链每一环都先问过再出图：公司取自己的标识（厂牌是 `/logo`，事务所是官网
     圆标），人是实体图→代表作头像，一环都取不到就一个 `<img>` 都不出，首字母垫底直接
     露出来。四个标志（`has_logo`／`has_image`／`has_avatar`／`mark_link_id`）都由
     `/api/entity` 随资料下发。

     作品截图不给公司用：厂牌那张是自家片没错，可这一页要认的是牌子；事务所名下的片
     更是成员各自拍的，拿其中一部的画面当门面，说的是别人的事。 */
  const company=kind==='studio'||kind==='agency';
  const image=d.id?entityFaceImg({kind,id:d.id,hasImage:d.has_image,
    rep:company||!d.has_avatar?null:d.representative_asset_id,
    mark:kind==='agency'?d.mark_link_id:null,
    logo:company&&d.has_logo?d.canonical_name:'',
    alt:esc(d.canonical_name),lazy:false,
    style:company?'':facePos(d.avatar_focus),dropStyle:true}):'';
  /* 链接按 beeg 的资料页形态：社媒收成纯图标，官网／事务所保留名字。

     社媒的 handle 是网址的一部分，写出来只是把 URL 抄一遍——`X @remu19971203` 里
     真正有信息量的只有那个 X。图标本身就说明了去哪，名字留给官网那种「点之前看不出
     是谁」的链接。外链箭头一并去掉：`target="_blank"` 已经是外链，箭头只是重复，
     一排链接里还会挤掉本来就不多的横向空间。 */
  const links=(d.links||[]).map(x=>{
    if(!(x.clickable&&/^https?:\/\//i.test(x.url||'')))
      return `<span class="private" title="私人馆藏来源记录，不直接打开下载页"><span class="entitylinkicon">${icon('globe')}</span><span class="entitylinklabel">来源 · ${esc(x.label||x.hostname||'已记录')}</span></span>`;
    /* 社媒的 handle 是网址的一部分，写出来只是把 URL 抄一遍——图标本身已经说明了去哪。 */
    if(x.link_kind==='social'){
      const brand=brandIcon(x.url);
      const mark=brand?`<span class="entitylinkicon brand">${icon(brand)}</span>`
        :`<span class="entitylinkicon">${icon('globe')}<img class="entityfavicon" src="${esc(linkMarkUrl(x))}" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self"></span>`;
      // 纯图标的链接自己不带可读文字，得把标签留给辅助技术。
      return `<a class="iconlink" href="${esc(x.url)}" target="_blank" rel="noreferrer" title="${esc(x.label)}">${mark}<span class="sr-only">${esc(x.label)}</span></a>`;
    }
    /* 厂牌页的官网链接不放图标，直接给网址。

       这一页的头像就是厂牌 logo，旁边再放一枚同品牌的小图标只是把同一个东西说两遍；
       而域名本身就是名字，比图标说得更清楚。女优页不一样：那里的头像是人，站点图标
       不构成重复，标签写的是这个域名归谁——图标、文字和落点因此说的是同一件事。 */
    if(kind==='studio')
      return `<a class="urllink" href="${esc(x.url)}" target="_blank" rel="noreferrer" title="${esc(x.label)}"><span class="entitylinklabel">${esc(linkHost(x.url)||x.label)}</span></a>`;
    return `<a href="${esc(x.url)}" target="_blank" rel="noreferrer" title="${esc(x.label)}"><span class="entitylinkicon">${icon('globe')}<img class="entityfavicon" src="${esc(linkMarkUrl(x))}" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self"></span><span class="entitylinklabel">${esc(x.label)}</span></a>`;
  }).join('');
  const tags=(d.tags||[]).map(x=>`<button class="pill" data-entity-tag="${esc(x.k)}" aria-pressed="${tagPressed(filters.tag,x.k)}">${esc(tagLabel(x.k))}<small>${x.n.toLocaleString()}</small></button>`).join('');
  /* 事务所名下的这批人不摆在这排小圆头像里：那是「同台艺人」，一条附注；名册是这一页
     的正文，占的是下面那整块。所以同一份 `related_performers` 在事务所页走另一条路。 */
  const roster=kind==='agency'?(d.related_performers||[]):[];
  agencyRoster=roster;
  const related=roster.length?'':(d.related_performers||[]).map(x=>`<button class="relatedperson" data-related-performer="${esc(x.k)}">
      <span class="ring"><span>${esc(x.k.slice(0,1))}</span>${entityFaceImg(
        {id:x.id,hasImage:x.has_image,rep:x.has_avatar?x.rep:null})}</span>
      <span class="nm">${esc(x.k)}</span></button>`).join('');
  const photoCount=photos&&!photos.error?(photos.total||0):0;
  /* 艺人名册和视频、照片是这一页的三个互斥视图，共用一组按钮：它们回答的是同一个
     问题，摆成两个控件只会各说各的。切换只重画下面那块，不重开这一页——名册已经随
     资料下来了，视频那一半本来也要请求。 */
  const mediaToggle=(photoCount||roster.length)?mediaViewButtonsHtml({
    active:entityViewNow(kind),
    peopleValue:roster.length?'people':'',peopleCount:roster.length,
    imageValue:photoCount?'photos':'',imageLabel:'照片',
    videoCount:d.asset_count,imageCount:photoCount,
    label:roster.length?'页面视图':'媒体类型',className:'entitymediaview'}):'';
  /* 统称由用户自己定。同一个人在库里常有中文、日文、罗马字几种写法，哪一个该顶在
     标题上是他的偏好，账本里没有能推出答案的字段。菜单只列这条实体名下已有的写法：
     换统称是换显示的那一个，不是改名——改名要有来源和证据，不该由一次点击完成。
     只有一个写法时不出这个控件，那里没有可选的东西。 */
  /* 事务所是身份信息，不是链接。它此前寄居在官方链接的标签里，于是那个控件同时替
     两家公司说话——文字是事务所名，图标和落点却是片商的站。名字归名字、链接归链接，
     它就跟着别名和作品数排在同一行。

     账本里有这家事务所的实体时给出去处：`d.agency` 是那条实体，点进去是它的资料页。
     只有 `metadata.agency` 时仍写名字但不做链接——那是采到的原文，还没有对应身份，
     做成链接会通向一个不存在的页面。

     这一行不写类别名。`T-POWERS` 这样的公司名摆在别名和作品数中间，读的人一眼就知道
     那是什么；多出来的两个字只占掉这行本来就不多的横向空间。 */
  const agencyHome=d.agency||null;
  const agencyName=agencyHome?agencyHome.canonical_name:((d.metadata||{}).agency?.name||'');
  const agencyHtml=!agencyName?''
    :agencyHome?` · <a class="entitylink" href="${esc(entityPath('agency',agencyName))}"
        data-agency="${esc(agencyName)}">${esc(agencyName)}</a>`
    :` · ${esc(agencyName)}`;
  /* 事务所页数的是人，不是片。它名下那 N 个视频是成员拍的，只报视频数会让「这家有
     几个人」这个它唯一独有的读数消失。 */
  const memberHtml=kind==='agency'
    ?` · <b>${(d.member_count||0).toLocaleString()}</b> 位艺人`:'';
  const nameChoices=[d.canonical_name,...(d.aliases||[])]
    .filter((option,index,all)=>option&&all.indexOf(option)===index);
  const namePick=nameChoices.length>1?`<div class="namepick" data-namepick>
      <button type="button" class="npbtn" data-namepick-toggle aria-haspopup="menu"
        aria-expanded="false" aria-controls="entity-name-menu"
        aria-label="选择统称" title="选择统称">${icon('chevron-down')}</button>
      <div class="popmenu npmenu" id="entity-name-menu" role="menu" data-namepick-menu hidden>${
        nameChoices.map(option=>`<button type="button" role="menuitemradio"
          data-namepick-name="${esc(option)}" aria-checked="${option===d.canonical_name}"
          >${icon('check')}<span>${esc(option)}</span></button>`).join('')}</div></div>`:'';
  $('#index').dataset.entityKind=kind;$('#index').dataset.entityName=name;
  $('#index').innerHTML=`<div class="entityhero"><div class="entityportrait ${kind==='performer'||kind==='creator'?'':'square'}">${image}<span>${esc(name.slice(0,1))}</span></div>
      <div><div class="entitytitle"><h2>${esc(d.canonical_name)}</h2>${namePick}</div>
        <div class="alias">${(d.display_aliases||[]).length?`${d.display_aliases.map(esc).join(' / ')} · `:''}<b>${d.asset_count.toLocaleString()}</b> 个视频${memberHtml}${agencyHtml}</div>
        ${links?`<div class="entitylinks">${links}</div>`:''}</div></div>
    ${related?`<div class="entitymeta"><section aria-label="同台艺人"><div class="relatedpeople">${related}</div></section></div>`:''}
    ${(tags||mediaToggle)?`<section class="entitytagbar" aria-label="媒体与标签"><div class="entitytags">${mediaToggle}${tags}</div></section>`:''}
    <div class="entitysection"></div>`;
  // 资料页的标签和顶部标签条是同一个开关，读的写的都是这一页的筛选。
  $('#index').querySelectorAll('[data-entity-tag]').forEach(b=>b.onclick=()=>
    toggleTag(b.dataset.entityTag));
  $('#index').querySelectorAll('[data-related-performer]').forEach(b=>b.onclick=()=>
    openEntity('performer',b.dataset.relatedPerformer));
  // 站内跳转走同一个 SPA 入口，不让浏览器整页重载。
  $('#index').querySelectorAll('[data-agency]').forEach(a=>a.onclick=event=>{
    event.preventDefault();openEntity('agency',a.dataset.agency)});
  /* 同台艺人和标签这两行都是 `overflow-x:auto` 加隐藏滚动条：能滚，但鼠标没有一个
     够得着的入口——滚轮是竖向的，滚动条不画出来，于是第 8 位之后的人和标签看得见
     够不着。全站横向行的那套拖动加滚轮映射就是为这个写的，登记上即可。 */
  wireDrag($('#index').querySelector('.relatedpeople'));
  wireDrag($('#index').querySelector('.entitytags'));
  if(namePick)wireNamePicker(kind,d.canonical_name);
  entityPhotos=photos&&!photos.error?photos:null;
  if(entityMediaView.media==='photos'&&!photoTotalOf())entityMediaView=emptyMediaView();
  renderEntityMediaToggle(kind,name,filters);
  if(entityViewNow(kind)==='people')renderAgencyRoster(roster);
  else if(entityMediaView.media!=='photos')renderEntityCollection(kind,name,items,filters);
  else if(entityMediaView.set)await openPhotoSet(kind,name,filters,entityMediaView.set,false);
  else renderPhotoWall(kind,name,filters,entityPhotos);
  buildBars();
  window.scrollTo({top:0,behavior:'smooth'});
}

let drawerSuppressUntil=0;
function buildDrawerNavigation(){
  const drawer=$('#drawer'),key=surfacePath()+location.search;
  if(!syncSidebarSurface(drawer,key)){
    drawer.querySelectorAll('[data-nav]').forEach(button=>
      button.setAttribute('aria-pressed',String(navOn(button.dataset.nav))));
    return;
  }
  drawer.innerHTML=`<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
    <b class="disp" style="font-size:15px;letter-spacing:.1em">导航与筛选</b>
    <button id="drawerClose" class="ib" title="收起" aria-label="收起导航">${icon('x')}</button></div>
    <div class="dnav">${orderedEdgeIcons().map(([k,label,ic])=>
      `<button data-nav="${k}" draggable="true" aria-pressed="${navOn(k)}">${icon(ic)}<span>${label}</span></button>`).join('')}</div>`;
  $('#drawerClose').onclick=()=>openDrawer(false);
  $('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));
  wireNavigationDrag(drawer.querySelector('.dnav'));
}
function renderFollowDrawer(items){
  buildDrawerNavigation();
  $('#drawer').querySelectorAll('.sec').forEach(section=>section.remove());
  const counts=sidebarTagCounts(items.map(item=>({tags:followCardTags(item)})));
  if(!counts.length)return;
  $('#drawer').insertAdjacentHTML('beforeend',`<div class="sec cat-online"><h3>内容标签</h3><div class="chips">${
    counts.map(([tag,n])=>
      `<button class="chip online" data-follow-drawer-tag="${esc(tag)}" aria-pressed="${followTags.has(tag)}">${esc(tagLabel(tag))}<span class="n">${n}</span></button>`).join('')}</div></div>`);
  $('#drawer').querySelectorAll('[data-follow-drawer-tag]').forEach(b=>b.onclick=()=>{
    followTags=new Set([b.dataset.followDrawerTag]);
    openDrawer(false);route(followViewPath());openFollow(false)});
}
function openDrawer(v){$('#drawer').classList.toggle('open',v);$('#scrim').classList.toggle('on',v);
  document.body.classList.toggle('drawer-open',!!v)}
function closeDrawerAfterNav(){drawerSuppressUntil=Date.now()+650;openDrawer(false)}
$('#filterBtn').onclick=()=>openDrawer(!$('#drawer').classList.contains('open'));
/* 常驻窄图标条：点即切视图，鼠标停留 180ms 展开完整抽屉 */
const EDGE_ICONS=[
  ['','首页','home'],
  ['performers','艺人','user-round'],
  ['studios','厂商','building'],
  ['tags','标签','tags'],
  ['jav','JAV','jav'],
  ['flagged','已标记','bookmark'],
  ['playlists','播放列表','playlist'],
  ['follow','关注','rss'],
  ['immerse','沉浸模式','gallery-vertical-end'],
  ['manage','管理','database'],
];
/* 每个管理页的身份（标题、图标、可直达的 URL）。用户仍可在设置里把其中任何
   一个加到顶层侧栏，所以这里保留全部页面，不因为它进了数据管理就删掉。 */
const MANAGE_SECTIONS=[
  ['stats','统计','chart'],
  ['taste','口味','heart'],
  ['review','人工复核','square-check-big'],
  ['cleanup','数据管理','hard-drive'],
  ['trash','回收站','trash'],
  // 这一项的页面是 /follow-manage（加来源、看凭据、移除来源），不是关注更新流
  // `/follow`。两处都叫「关注」时，管理菜单和页标题都在说一个它去不到的地方。
  ['follow','关注管理','rss'],
  ['quality','高清版','sparkles'],
];
/* 管理菜单只留四项。人工复核、回收站、高清版都是「收拾库里已有的东西」，
   和垃圾文件、重复文件、空文件夹是同一件事的不同步骤，统一从数据管理进；
   统计页也因此不再挂链接管理和资源同步这两块跟统计无关的面板。 */
const MANAGE_MENU_SECTIONS=['stats','taste','cleanup','follow'];
const manageMenuSections=()=>MANAGE_SECTIONS.filter(([key])=>MANAGE_MENU_SECTIONS.includes(key));
const OPTIONAL_EDGE_ICONS=MANAGE_SECTIONS.map(([key,label,ic])=>
  key==='follow'?['follow-manage',label,ic]
    :key==='cleanup'?['data-cleanup',label,ic]:[key,label,ic]);
const NAV_CATALOG=[...EDGE_ICONS,...OPTIONAL_EDGE_ICONS];
const DIRECT_MANAGE_NAV={stats:'stats',review:'review','data-cleanup':'cleanup',trash:'trash','follow-manage':'follow',quality:'quality'};
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
      ${available.length?`<div class="popmenu sidebaraddmenu" data-sidebar-add-menu role="listbox" aria-label="选择要添加的页面" hidden>${available.map(([key,label,ic],index)=>
        `<button type="button" role="option" data-sidebar-add-option="${esc(key===''?'__home__':key)}" aria-selected="${index===0}" tabindex="${index===0?'0':'-1'}">${icon(ic)}<span>${esc(label)}</span></button>`).join('')}</div>`:''}
    </div>
    <button type="button" class="geist-button primary" data-sidebar-add${available.length?'':' disabled'}>添加</button></div>`;
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
/* 当前在哪个管理区。路由表里的 `section` 是唯一判据；垃圾文件那一屏没有自己的
   身份，它是数据管理的一部分，`state.state` 才是判据（`/junk-files` 从启动那一刻
   起 state 就是 `ads`，首页带 `?state=ads` 也一样）。 */
function manageSection(){
  const hit=matchRoute(ROUTES,decodeURIComponent(location.pathname));
  return hit?.route.section||(state.state==='ads'?'cleanup':'');
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
    </button><div class="managebar-menu" id="managebar-menu">${manageMenuSections().map(([k,label,ic])=>
      `<button data-manage="${k}" aria-pressed="${k===current}">${icon(ic)}<span>${label}</span></button>`).join('')}</div>`;
  const toggle=bar.querySelector('.managebar-toggle');
  toggle.onclick=()=>{const open=bar.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open))};
  toggle.onkeydown=event=>{if(event.key==='Escape'){bar.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');toggle.focus()}};
  bar.querySelectorAll('[data-manage]').forEach(b=>b.onclick=()=>openManage(b.dataset.manage));
}
/* 管理区分页共用同一个标题元素。回收站和垃圾文件走首页网格路径，
   本来就没有标题层；统计/复核/重复各自内嵌 h2 又导致字号不一致。 */
/* 数据管理五张卡对应的子页（vercel.com/geist/breadcrumbs：有上一级页面的
   子页才画面包屑）。人工复核、回收站、高清版虽也保留侧栏直达入口，
   层级上仍从数据管理进；空文件夹是 hub 上的就地操作，没有独立页面。 */
const MANAGE_CRUMB_PAGES={
  '/junk-files':'垃圾文件',
  '/duplicates':'重复文件',
  '/review':'人工复核',
  '/trash':'回收站',
  '/quality-goals':'高清版',
};
function paintManageTitle(){
  const current=manageSection(),el=$('#manageTitle');
  if(!el)return;
  document.body.classList.toggle('insight-layout',current==='stats'||current==='taste');
  /* 812px 居中是数据管理 hub 自己的窄列宽度（.cleanuppage）。它下面的垃圾文件、
     重复文件正文都是全宽网格，跟着居中就是标题在宽屏上凭空左缩一截、跟内容对不齐。 */
  document.body.classList.toggle('cleanup-layout',current==='cleanup'&&decodeURIComponent(location.pathname)==='/data-cleanup');
  document.body.classList.toggle('follow-manage-layout',decodeURIComponent(location.pathname)==='/follow-manage');
  const entry=MANAGE_SECTIONS.find(([k])=>k===current);
  el.hidden=!entry;
  // 数据管理之下按路径再分一层（MANAGE_CRUMB_PAGES）：垃圾文件/重复文件的
  // 标题用页面自己的名字，「数据管理」让给 breadcrumb 的上一级。
  const pageLabel=current==='cleanup'?MANAGE_CRUMB_PAGES[decodeURIComponent(location.pathname)]:null;
  if(entry)el.textContent=pageLabel||entry[1];
  paintManageCrumb();
  paintManageLede();
}
function paintManageCrumb(){
  const el=$('#manageCrumb');if(!el)return;
  const label=MANAGE_CRUMB_PAGES[decodeURIComponent(location.pathname)];
  el.hidden=!label;
  if(!label)return;
  el.innerHTML=breadcrumbHtml([{label:'数据管理',href:'/data-cleanup'},{label,current:true}]);
  /* href 是给「新标签页打开」和右键菜单用的，普通左键必须走路由：这里没有
     全局锚点拦截，不接就是整页重载，SPA 的返回表面和已读位置全部丢掉。 */
  el.querySelectorAll('a[href]').forEach(a=>a.onclick=event=>{
    if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||event.button)return;
    event.preventDefault();openDataCleanup();
  });
}
/* 说明行可以在右端挂一个属于本页的动作（回收站的「清空回收站」）。左文右动作是
   一行，不是两行；没有动作时它仍是一段纯文本。 */
function paintManageLede(text='',actionsHtml=''){
  const el=$('#manageLede');if(!el)return;
  el.hidden=!text&&!actionsHtml;
  el.classList.toggle('pagelede-actions',!!actionsHtml);
  el.innerHTML='';
  if(text)el.appendChild(Object.assign(document.createElement('span'),{textContent:text}));
  if(actionsHtml)el.insertAdjacentHTML('beforeend',actionsHtml);
}
function paintListTitle(){
  const el=$('#listTitle');if(!el)return;
  const path=decodeURIComponent(location.pathname);
  const label=!manageSection()&&isCatalogPath(path)?STATE_LABELS[state.state]||'':'';
  el.hidden=!label;if(label)el.textContent=label;
}
/* 进某个管理区。入口就是路由表里 `section` 等于它的第一条，所以这里不再有一份
   「section → 打开哪个函数」的副本。 */
function openManage(section='stats'){
  const target=ROUTES.find(spec=>spec.section===section);
  if(target){target.open({},true);return}
  /* 认不出的 section 一律落到垃圾文件：统计页那颗「查看垃圾文件」传的就是 `ads`，
     而垃圾文件是目录页的一个筛选态，没有自己的 section。 */
  state.orient='';state.state='ads';route(junkPath());
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
function sortOptions(){return javActive()?[JAV_RELEASE_SORT,...SORTS]:SORTS}
/* 方向只画在选中的那一枚上：箭头既是当前方向，也是「再点一次能翻」的唯一提示。
   未选中项不画箭头——那会变成八个方向按钮，其中七个的方向此刻不生效。
   箭头对辅助技术隐藏（`icon()` 自带 aria-hidden），无障碍名称播报的是「点下去会得到
   什么」而不是当前状态：Geist Table 的可排序表头就是这么分工的，当前状态由
   `aria-pressed` 和这枚箭头各自表达，名称留给下一步动作。 */
function sortButtonHtml(key,label,current,dir,attr){
  const on=current===key,next=nextSortState(key,current,dir);
  const word=on?sortDirWord(key,dir):'';
  return `<button type="button" ${attr}="${key}" aria-pressed="${on}"${
    next?` aria-label="按${label}${next.dir?sortDirWord(next.sort,next.dir):''}排序"`:''}>${label}${
    word?icon(dir==='asc'?'arrow-up':'arrow-down','sortdir'):''}</button>`;
}
/* 点未选中项＝换列并用该列的默认方向；点选中项＝翻方向。随机没有方向，重复点它
   什么都不做——换一批是它旁边那枚按钮的事。 */
function nextSortState(key,current,dir){
  if(key!==current)return{sort:key,dir:defaultSortDir(key)};
  if(!SORT_DIR_WORDS[key])return null;
  return{sort:key,dir:dir==='asc'?'desc':'asc'};
}
function javLayout(){
  const raw=JAV_LAYOUT_ALIASES[appSettings.javLayout]||appSettings.javLayout;
  return allowedSetting(raw,JAV_LAYOUTS.map(([k])=>k),'big');
}
function javLayoutButtons(){
  return iconSwitchHtml('jav-layout','JAV 卡片版式',JAV_LAYOUTS,javLayout(),
    {attr:'data-jav-layout',className:'javlayout'});
}
function wireJavLayoutButtons(root){wireIconSwitch(root,'data-jav-layout',setJavLayout)}
/* 版式切换一次请求都不发。卡片 HTML 完全由 CACHE 里那条媒体决定，走 `load(true)` 的话
   会先把整屏换成骨架、再重新取一遍同样的数据，于是纯展示层的一个开关被演成了一次页面
   加载：列表整屏消失、骨架闪一下、内容再回来。
   逐张换 outerHTML，不重跑 batchWithMix：网格里的顺序、Mix 的落位和分卷／版次折叠都是
   前几批累积下来的结果，重跑一遍分组会把它们重排。 */
function repaintCatalogCards(){
  // 回收站和垃圾文件的卡片由 resourceCardHtml／junkCardHtml 画，形状和动作都不同，
  // 不能拿 cardHtml 重画；这两屏本来也没有版式开关。
  if(state.state==='trash'||state.state==='ads')return;
  const grid=$('#grid');
  releaseHoverPreviews(grid);
  grid.querySelectorAll('.card[data-id],.card[data-mix-seed]').forEach(card=>{
    const seed=card.dataset.mixSeed;
    const it=CACHE[seed||card.dataset.id];
    if(it)card.outerHTML=seed?mixCardHtml(it):cardHtml(it);
  });
  wireCards(grid);wireMixCards(grid);paintSelection();
}
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
  if(!$('#grid').hidden)repaintCatalogCards();
}
function paintJavBar(){
  // 版式按钮现在长在排序行里（见 renderCount），这里只负责收掉旧容器。
  const bar=$('#javbar');if(bar)bar.hidden=true;
}
function toggleJavMode(){
  state.jav=state.jav==='1'?'':'1';
  if(state.jav!=='1'&&state.sort==='release'){state.sort='seed';state.dir=''}
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
  const hit=matchRoute(ROUTES,decodeURIComponent(location.pathname));
  if(hit?.route.reload){await hit.route.reload();return}
  await load(true);
}
function navOn(k){
  const path=decodeURIComponent(location.pathname);
  const nav=matchRoute(ROUTES,path)?.route.nav||'';
  const directSection=DIRECT_MANAGE_NAV[k];
  if(directSection)return manageSection()===directSection;
  if(k==='manage'){
    const current=manageSection();
    return !!current&&!orderedEdgeIcons().some(([key])=>DIRECT_MANAGE_NAV[key]===current);
  }
  // JAV 和竖屏不是路径，是内存里的筛选开关，所以这两条只能问 state。
  if(k==='jav')return javActive();
  if(k==='shorts')return state.orient==='竖屏';
  // 首页只在真的停在首页列表上时亮：管理区、索引页、实体页都不算，
  // 否则它会和当前所在的入口同时高亮。
  if(k==='')return path==='/'&&!manageSection()&&!state.state&&!javActive()&&state.orient!=='竖屏';
  // 目录页的四个筛选态共用一屏，竖屏是压在它们之上的另一层筛选。
  if(STATE_ROUTES[k])return nav===k&&state.orient!=='竖屏';
  if(nav)return nav===k;
  return path==='/'&&state.state===k&&state.orient!=='竖屏';
}
/* 窄栏与抽屉共用同一套跳转。两边曾各写一份分支，抽屉那份漏了追更和播放列表，
   点下去只把 state.state 设成一个后端不认识的值，看上去就是“点了没反应”。 */
function navTo(k){
  closeDrawerAfterNav();                 // 点了就收起抽屉，且短暂禁止悬停把它立刻弹回
  if(DIRECT_MANAGE_NAV[k]){openManage(DIRECT_MANAGE_NAV[k]);return}
  if(k==='manage'){openManage();return}
  if(k==='jav'){toggleJavMode();return}
  if(k===''){openHome();return}
  // 有自己路径的入口（追更、播放列表、沉浸模式、索引页）从路由表进。
  const target=ROUTES.find(spec=>spec.nav===k&&!STATE_ROUTES[k]);
  if(target){target.open({},true);return}
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
  buildDrawerNavigation();
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
    renderCatalogLoading(state.state==='ads'?'正在读取垃圾文件':'正在读取作品')}
  showHomeSurfaces();
  if(reset){offset=0;renderedPartGroups.clear();renderedEditionGroups.clear()}
  renderCombo();
  // 垃圾文件是逐项处置队列，计数只是当前队列说明，不是需要跟随浏览的排序工具。
  const countRow=$('#count'),staticManageCount=state.state==='ads';
  countRow.classList.toggle('manage-static',staticManageCount);
  countRow.classList.toggle('junkcount',staticManageCount);
  if(staticManageCount)countRow.classList.remove('is-stuck');
  if(state.state==='ads'){
    // 哨兵由 renderCatalogLoading 统一收掉：铺骨架和收 dots 是同一件事的两半，
    // 分开写就会有分支只做了一半。
    if(reset||!adsBatch){const junkQuery=new URLSearchParams({limit:'200',status:junkView});if(junkKind)junkQuery.set('kind',junkKind);
      const nextAds=await surfaceApi(surface,'/api/ads?'+junkQuery);
      if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;
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
  const d=await surfaceApi(surface,'/api/items?'+p);
  if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;
  cache(d.items);
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
function readSearchHistory(){return searchHistory.slice(0,appSettings.searchHistoryLimit)}
const loadSearchHistory=()=>api('/api/search-history?limit='+appSettings.searchHistoryLimit).then(d=>{searchHistory=Array.isArray(d.items)?d.items:[];return searchHistory}).catch(()=>searchHistory);
function writeSearchHistory(list){searchHistory=list.slice(0,appSettings.searchHistoryLimit);return searchHistory}
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
      // 行没了，键盘选中的下标就指不回同一项，归零重来。
      searchActive=-1;
      menu.querySelectorAll('[data-search-value]').forEach(x=>x.classList.remove('active'));
    };
  })}
function runSearch(useSuggestion=false,committed=false){let query=$('#q').value.trim();
  if(useSuggestion&&!query){query=$('#q').dataset.suggestion||'';$('#q').value=query}
  if(committed)rememberSearch(query);
  disposeStage(false);
  state.q=query;route(state.q?'/?q='+encodeURIComponent(state.q):'/',true);load(true)}
const searchOptions=()=>{const menu=$('#searchMenu');
  return menu.hidden?[]:[...menu.querySelectorAll('[data-search-value]')]};
function moveSearchActive(step){
  const options=searchOptions();if(!options.length)return false;
  searchActive=(searchActive+step+options.length)%options.length;
  options.forEach((option,index)=>option.classList.toggle('active',index===searchActive));
  options[searchActive].scrollIntoView({block:'nearest'});
  return true;
}
const refreshSearchMenu=()=>{searchActive=-1;if(!$('#searchMenu').hidden)renderSearchMenu()};
$('#q').oninput=e=>{if(e.isComposing)return;refreshSearchMenu()};
$('#q').oncompositionend=refreshSearchMenu;
$('#q').onkeydown=e=>{
  /* 组字过程中的方向键在挑候选字、回车在定字，都不是给这个菜单的。 */
  if(e.isComposing)return;
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
  const d=await surfaceApi(surface,'/api/items?'+p);
  if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;
  if(!d.items.length){$('#shortsSec').hidden=true;return}
  cache(d.items);
  releaseHoverPreviews($('#srow'));
  const grid=$('#grid');grid.querySelector('#shortsInline')?.remove();
  /* 竖屏条整行占位（grid-column:1/-1），插在行边界上才不会把上一行截断留空。
     余位不另拉一批横屏视频来补：那批 id 不在分页序列里，翻下一页必然重复，
     而且被当成 scard 渲染会把横屏压成竖框。 */
  const columns=Math.max(1,getComputedStyle(grid).gridTemplateColumns.split(' ').length);
  const cards=[...grid.children].filter(x=>x.matches('.card[data-id]'));
  const anchor=cards[Math.min(cards.length,columns*SHORTS_ROW_OFFSET)]||null;
   const inline=`<section class="shorts-inline" id="shortsInline"><h2 class="disp">竖屏 <span class="mono shortscount">${d.total.toLocaleString()} 个</span><button class="shorts-enter" type="button">${icon('play')}<span>进入沉浸模式</span></button></h2><div class="srow">${d.items.map(it=>cardHtml(it,'scard')).join('')}</div></section>`;
  if(anchor)anchor.insertAdjacentHTML('beforebegin',inline); else grid.insertAdjacentHTML('beforeend',inline);
  const section=grid.querySelector('#shortsInline');
  section.querySelector('.shorts-enter').onclick=()=>openTok();
  wireCards(section.querySelector('.srow'),openTok); wireDrag(section.querySelector('.srow'));
}

/* ── 就地展开播放 ── */
/* 版次徽章的配色跟卡片标题上的那套走。多一个 `有码`：卡片上正片不加角标是对的
   （没角标就是正片），但队列里两条并排时「什么都不写」等于让人自己猜哪条是哪条。 */
const EDITION_TONE={'中字':'subtitle','无码':'uncensored','无码破解':'cracked','有码':'censored'};
/* 同一部片的几卷共用文件名，标题、女优、厂牌逐字相同：详情标题不写卷号的话，在队列里
   换一卷，右侧整栏看上去纹丝不动。卷号说的是「第几份文件」而不是版次，用中性灰。 */
const partLabelBadge=(it,queue)=>queue?.kind==='parts'&&it.part_label
  ? `<small class="javedition partlabel">第 ${esc(it.part_label)} 卷</small>`:'';
function queueHtml(queue,itemId){
  const action=queue.kind==='mix'
    ? `<button data-save-mix title="保存为播放列表" aria-label="保存为播放列表">${icon('bookmark-plus')}</button>`
    : queue.kind==='playlist'?`<button data-edit-playlist title="编辑播放列表" aria-label="编辑播放列表">${icon('playlist')}</button>`:'';
  const countLabel=queue.kind==='parts'?`${queue.items.length} 卷`
    :queue.kind==='editions'?`${queue.items.length} 个版本`:`${queue.items.length} 个视频`;
  const kindLabel={mix:'Mix',parts:'分卷',editions:'版本',playlist:'播放列表'}[queue.kind]||'视频合集';
  /* 版次队列的标题是「版本 · 番号」，而番号就印在正上方的详情标题里，标题栏又已经
     写着「版本」——三处说同一件事。这里只留数量。别的队列标题带真信息（播放列表名、
     Mix 种子），不能一起砍。 */
  const summary=queue.kind==='editions'?countLabel:`${esc(queue.title)} · ${countLabel}`;
  return `<aside class="mixqueue" data-queue-kind="${esc(queue.kind)}"><div class="mixqueuehead"><div><h2>${kindLabel}</h2><span>${summary}</span></div><div class="mixqueueactions">${action}
    <button data-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${queue.items.map((x,index)=>{
      /* 没抽过帧就退回番号封套。版次组里常有一份刚入库、还没抽帧的无码，
         只认 `has_thumb` 会让它在队列里是个纯黑块，而同一条在列表卡上是有封面的。 */
      const thumb=x.has_thumb?`<img src="/poster?id=${x.id}&c=4" alt="" loading="lazy">`
        :(x.is_jav&&x.code?`<img src="/cover?code=${encodeURIComponent(x.code)}" alt="" loading="lazy" data-drop="self">`:'');
      const edition=queue.kind==='editions'&&x.edition_label
        ?`<i class="qedition javedition ${EDITION_TONE[x.edition_label]||'censored'}">${esc(x.edition_label)}</i>`:'';
      const edit=queue.kind==='playlist'?`<span class="queueedit"><button data-queue-up="${index}" aria-label="上移" ${index===0?'disabled':''}>↑</button><button data-queue-down="${index}" aria-label="下移" ${index===queue.items.length-1?'disabled':''}>↓</button><button data-queue-remove="${x.id}" aria-label="移出播放列表">${icon('x')}</button></span>`:'';
      return `<div class="mixrow"><button class="mixitem ${x.id===itemId?'current':''}" data-queue-item="${x.id}" aria-current="${x.id===itemId?'true':'false'}">
        <span class="mixitempic">${thumb}<i class="dur mono">${fmtDur(x.duration)}</i></span><span class="mixitemmeta">${cardIdentity(x,false).avatar}<span class="mixitemtext"><span class="mixitemhead">${edition}<b data-middle-truncate>${esc(javDisplayName(x))}</b></span><span data-truncate-end>${queue.kind==='parts'?`第 ${esc(x.part_label)} 卷`:esc(mixLabel(x))}</span></span></span></button>${edit}</div>`;
    }).join('')}</div></aside>`;
}
async function buildMix(seedId){
  const [seed,related]=await Promise.all([api('/api/item?id='+seedId),mixRelated(seedId)]);
  const items=[seed,...related.filter(x=>x.id!==seed.id)];cache(items);
  return {kind:'mix',seedId,title:`Mix · ${mixLabel(seed)}`,items};
}
async function openMix(seedId,itemId=seedId,push=true,anchor=null){
  const previous=activeQueue?.kind==='mix'&&activeQueue.seedId===seedId?activeQueue:null;
  if(push&&!previous)detailReturnPath=location.pathname+location.search;
  const mix=previous||await buildMix(seedId);
  await openItem(itemId,false,mix,anchor);
  if(push)route(`/mix/${seedId}/${itemId}`);
}
/* 版次视图复用分卷的队列：两者都是「一个番号下的几个可播条目」，差别只在标题和
   每条的副标题。另写一套只会让队列的键盘、续播和返回路径各演化一份。 */
async function openEditions(seedId,itemId=seedId,push=true,anchor=null){
  const previous=activeQueue?.kind==='editions'&&activeQueue.seedId===seedId?activeQueue:null;
  if(push&&!previous)detailReturnPath=location.pathname+location.search;
  let queue=previous;
  if(!queue){
    const group=await api('/api/editions?id='+seedId);
    if(group.error){await openItem(itemId,true);return}
    queue={kind:'editions',seedId,title:`版本 · ${group.title}`,items:group.items};cache(queue.items);
  }
  const chosen=queue.items.some(item=>item.id===itemId)?itemId:queue.items[0].id;
  await openItem(chosen,false,queue,anchor);
  if(push)route(`/editions/${seedId}/${chosen}`);
}
async function openParts(seedId,itemId=seedId,push=true,anchor=null){
  const previous=activeQueue?.kind==='parts'&&activeQueue.seedId===seedId?activeQueue:null;
  if(push&&!previous)detailReturnPath=location.pathname+location.search;
  let queue=previous;
  if(!queue){
    let group;
    try{group=await partGroup(seedId)}catch(_e){await openItem(itemId,true);return}
    queue={kind:'parts',seedId,title:`分卷 · ${group.title}`,items:group.items};
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
/* 关掉详情要不要重新装一遍列表，判据是「退回去有没有东西可看」。
   按 `#grid` 有没有子节点判会误判：直接打开 `/parts/28125/28125` 这类深链时，
   网格里躺着一个还没被替换掉的加载骨架，它也是子节点。于是关掉播放器后
   `route('/')` 只改了地址，列表永远停在那张骨架上——首页看起来打不开了。
   卡片一定带 `data-id`（Mix 带 `data-mix-seed`），骨架没有。 */
function hasReturnSurface(){
  return !!$('#grid').querySelector('[data-id],[data-mix-seed]')
    ||!$('#index').hidden||!$('#stats').hidden;
}
/* 同一张骨架的另一半问题：深链冷启动时列表一次请求都没发过，`renderInitialSurfaceLoading`
   占位的那张「正在读取作品」就永远停在详情下方——写着在读，其实没有任何请求在跑。
   关掉详情时 `detailReturnNeedsRestore` 会补装列表，所以这里直接清掉即可。 */
function clearIdleCatalogLoading(){
  const grid=$('#grid');
  if(!grid.querySelector('.catalog-skeleton'))return;
  grid.innerHTML='';
  const count=$('#count');count.removeAttribute('aria-busy');count.removeAttribute('aria-label');
}
async function openItem(id,push=true,queueContext=null,anchor=null){
  releaseHoverPreviews();
  const origin=anchor?.isConnected?anchor:(detailOriginAnchor?.isConnected?detailOriginAnchor:null);
  const above=anchor?.isConnected
    ? anchor.getBoundingClientRect().top+anchor.getBoundingClientRect().height/2>window.innerHeight/2
    : detailOriginAbove;
  const returnSurfaceReady=hasReturnSurface();
  const needsReturnRestore=detailReturnNeedsRestore||(!push&&!returnSurfaceReady);
  if(!returnSurfaceReady)clearIdleCatalogLoading();
  const returnBars=barsContext.type==='item'?detailReturnBarsContext:cloneBarsContext(barsContext);
  if(push)detailReturnPath=location.pathname+location.search;
  disposeStage(false,true);
  detailOriginAnchor=origin;detailOriginAbove=above;detailReturnNeedsRestore=needsReturnRestore;
  detailReturnBarsContext=returnBars;
  activeQueue=queueContext;
  if(push&&!queueContext)route('/item/'+id);
  const detailSurface=surfaceToken(surfacePath());
  const it=await surfaceApi(detailSurface,'/api/item?id='+id);
  if(!surfaceCurrent(detailSurface))return;
  if(it.error)return;
  if(it.location==='online'&&it.follow_item_id){
    followDetailReturnPath=detailReturnPath||'/';
    await openFollowDetail(it.follow_item_id,false,null,true);
    return;
  }
  /* 卷标只有分卷队列知道：`/api/item` 是单条口径，它答不出「这是第几卷」。不补的话
     标题栏里的卷号在深链进来和点开队列另一条时都不出现。 */
  if(queueContext?.kind==='parts')
    it.part_label=queueContext.items.find(part=>part.id===it.id)?.part_label||'';
  current=it; CACHE[it.id]=it;
  barsContext={type:'item',id:it.id,filters:returnBars?.type==='entity'
    ? {...returnBars.filters}:emptyEntityFilters()};
  const gated=it.cost==='metered'&&it.location!=='online';
  const offline=sourceOffline(it.location);
  const online=it.location==='online';
  /* 保存过的在线资产照常播；只有反查不到关注条目时才拦下来说明原因。 */
  const onlineGated=online&&!it.follow_item_id;
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
  // 非规范厂牌只有扁平 `studio` 字段，它的标识可用性单独下发在 `has_studio_logo`：
  // 不接过来，这条路径会从「本来能取到图」退化成永远只显示首字母。
  const studioFallback=studioRef?[]
    :(it.studio?[{id:null,name:it.studio,has_logo:it.has_studio_logo}]:[]);
  const studioList=[...(refs.studio||[]),...studioFallback].filter(ref=>fresh(ref.name));
  const creatorList=(refs.creator||[]).filter(ref=>fresh(ref.name));
  const seriesList=(refs.series||[]).filter(ref=>fresh(ref.name));

  // BEST 合集实测有 41 位出镜者，全铺开会把标签和反馈按钮挤出可视区。
  // 前 8 位直接展示，其余默认收起但仍在 DOM 里，一次点击即可看全。
  const CAST_SHOWN=8;
  const castOverflow=Math.max(0,castList.length-CAST_SHOWN);
  const idFace=(kind,item)=>kind==='performer'
    // 和顶栏圆头像同一条判据：没装实体图就不出 `<img>`。这一格没有代表作头像可退，
    // 取不到就是首字母垫底。
    ? `<span>${esc(item.name.slice(0,1))}</span>${entityFaceImg(
        {id:item.id,hasImage:item.has_image})}`
    : kind==='studio'
      // 和顶栏小圆片同一条判据：没装标识就不出 `<img>`，不再靠 404 把图摘掉。
      ? `<span>${esc(item.name.slice(0,2))}</span>${item.has_logo?`<img src="/logo?studio=${encodeURIComponent(item.name)}&variant=icon" alt="" loading="lazy" data-drop="self">`:''}`
      : `<span>${esc(item.name.slice(0,1))}</span>`;
  const idCell=(kind,item,index)=>{
    const hide=kind==='performer'&&index>=CAST_SHOWN;
    const content=`<span class="idface">${idFace(kind,item)}</span><span class="idname">${esc(item.name)}</span>`;
    if(!item.id)return `<span class="idcell${kind==='studio'?' logo':''}" title="${esc(item.name)}"${hide?' hidden data-castoverflow':''}>${content}</span>`;
    return `<button class="idcell entitylink${kind==='studio'?' logo':''}" data-entity-kind="${kind}"
      data-entity-name="${esc(item.name)}" title="${esc(item.name)}"${hide?' hidden data-castoverflow':''}>${content}</button>`;
  };
  const idGroup=(label,kind,list,extra='')=>list.length
    ? `<section class="idgroup idgroup-${kind}"><h5 class="idlabel">${label}</h5>
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
       ${playerStatsOverlayHtml()}
      ${offline?`<div class="gate offline" id="offlineGate" role="status">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <b>脱盘模式</b>
          <span>${esc(offlineReason(it.location))}</span>
          <button class="chip" id="offlineRetry" type="button">重新检测</button></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none" hidden></video>`
       :onlineGated?`<div class="gate" id="onlineGate" role="status">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <b>在线资产</b>
          <span>这条没有对应的关注条目，媒体地址无从解析。</span>
          <button class="chip" id="openSavedFollow" type="button">打开已保存关注</button></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none" hidden></video>`
       :gated?`<div class="gate" id="gate">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <span>点此开始拉流 · ${fmtSize(it.size||0)}</span></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none" hidden></video>`
       :`<video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="metadata"></video>`}
    </div>${queueContext?queueHtml(queueContext,it.id):''}
    <div class="side"><div class="sidecontent">
      <div class="detailtitle">${srcBadge(it.location,it.cost,'srcbig')}
        <div class="stitle">${javTitleHtml(it)}${partLabelBadge(it,queueContext)}${it.location==='online'?'':`<span class="srctools detailtitletools">${sourceToolButtons(it.id)}</span>`}</div></div>
      ${it.location==='online'?'':`<span class="srcstate detailtitlestate" aria-live="polite"></span>`}
      <div class="smeta mono">
        <span class="detailmetaitem">${icon('monitor')}<span>${it.width||'?'}×${it.height||'?'}</span></span>
        <span class="detailmetaitem">${icon('hard-drive')}<span>${fmtSize(it.size||0)}</span></span>
        ${it.release_date?`<span class="detailmetaitem">${icon('calendar')}<span>${esc(it.release_date)}</span></span>`:''}</div>
      <div class="detailidentity">${identityRows||`<div class="identityrow"><span></span><span class="ilabel">归属</span><span>${esc(who)}</span></div>`}</div>
      <div class="stags" id="detailTags"></div>
      <div class="trace"><div class="lab mono"><span>离开位置</span><span id="ratioTxt">0%</span></div>
        <div class="bar"><u id="watched"></u><b id="mark"></b></div>
        <div class="lab mono trace-real"><span>真实观看</span><span id="realTxt">0%</span></div>
        <div class="bar"><u id="realBar"></u></div>
      </div>
      <div class="fb">
        <button class="like" id="likeBtn" aria-label="${it.liked?'取消喜欢':'喜欢'}" title="喜欢 · 记录口味偏好" aria-pressed="${!!it.liked}">${icon('thumbs-up')}</button>
        <button class="reason" id="preferenceToggle" aria-label="喜爱理由" title="喜爱理由" aria-expanded="false" aria-controls="preferencePanel" data-has-reason="${!!it.like_reason}">${icon('notebook-pen')}</button>
        <button class="dislike" data-kind="dislike" aria-label="不合口味" title="不合口味 · 降低推荐权重" aria-pressed="${it.feedback==='dislike'}">${icon('thumbs-down')}</button>
        <button class="seen" data-kind="seen" aria-label="看过了" title="看过了 · 只降低近期推荐" aria-pressed="${it.feedback==='seen'}">${icon('eye')}</button>
        <button class="later" id="stageLater" aria-label="稍后看" title="稍后看 · 加入或移出队列" aria-pressed="${!!it.watch_later}">${it.watch_later?icon('check'):icon('bookmark-plus')}</button>
        <button class="playlistadd" id="addPlaylist" aria-label="加入播放列表" title="加入播放列表">${icon('playlist')}</button>
        <button class="upgrade" id="betterVersion" aria-label="寻找更好版本" title="寻找高清、无水印或完整版" aria-pressed="${!!it.better_version}">${icon('sparkles')}</button>
        <button class="dispose" data-kind="dispose" aria-label="加入回收站" title="加入回收站 · 文件仍保留，可从回收站永久清除" aria-pressed="${it.disposal==='trash'}">${icon('trash')}</button></div>
      <div class="preference" id="preferencePanel" hidden>
        <textarea id="likeReason" maxlength="2000" placeholder="为什么喜欢？">${esc(it.like_reason||'')}</textarea>
        <div class="preference-foot"><span id="preferenceState" aria-live="polite"></span>
          <button type="button" class="geist-button primary savepreference" id="savePreference" title="提交喜爱理由" aria-label="提交喜爱理由"><span>提交</span></button></div>
      </div>
      <button class="obtn" data-kind="o">${icon('sperm')}<span>记一次高潮</span><b class="mono" id="oCount">${it.o_count||0}</b></button>
    </div></div></div>
    ${queueContext?'':`<div class="next"><h3>接着看</h3><div class="nrow" id="nrow">${
      pageSkeletonHtml('正在读取推荐',{cards:true,className:'related-skeleton'})}</div></div>`}`;
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
    :queueContext.kind==='editions'?openEditions(queueContext.seedId,+b.dataset.queueItem,true)
    :openPlaylist(queueContext.playlistId,+b.dataset.queueItem,true));
  $('#stage').querySelectorAll('[data-save-mix]').forEach(b=>b.onclick=()=>saveMixAsPlaylist(queueContext));
  $('#stage').querySelectorAll('[data-edit-playlist]').forEach(b=>b.onclick=()=>openPlaylists(true));
  $('#stage').querySelectorAll('[data-queue-up],[data-queue-down]').forEach(b=>b.onclick=()=>movePlaylistItem(queueContext,+b.dataset[b.hasAttribute('data-queue-up')?'queueUp':'queueDown'],b.hasAttribute('data-queue-up')?-1:1,it.id));
  $('#stage').querySelectorAll('[data-queue-remove]').forEach(b=>b.onclick=()=>removePlaylistItem(queueContext,+b.dataset.queueRemove,it.id));
  wireDrag($('#stage').querySelector('.mixlist'));
  const g=$('#gate');
  const onlineGate=$('#onlineGate');
  $('#addPlaylist').onclick=()=>openAddToPlaylist(it);
  const paintDetailFeedback=result=>{
    Object.assign(it,{feedback:result.feedback,disposal:result.disposal,o_count:result.o_count});
    const stage=$('#stage');if(!stage)return;
    stage.querySelector('.dislike')?.setAttribute('aria-pressed',result.feedback==='dislike');
    stage.querySelector('.seen')?.setAttribute('aria-pressed',result.feedback==='seen');
    stage.querySelector('.dispose')?.setAttribute('aria-pressed',result.disposal==='trash');
    if($('#oCount'))$('#oCount').textContent=result.o_count||0;
  };
  const postFeedback=async kind=>{
    const result=await api('/api/feedback',{method:'POST',body:JSON.stringify({id:it.id,kind})});
    paintDetailFeedback(result);return result;
  };
  $('#stage').querySelectorAll('[data-kind]').forEach(b=>b.onclick=async()=>{
    const kind=b.dataset.kind;
    const before={feedback:it.feedback||null,disposal:it.disposal||null,o_count:it.o_count||0};
    setActionBusy(b);
    try{
      const r=await postFeedback(kind);
      const messages={dislike:r.feedback==='dislike'?'已标记不合口味':'已取消不合口味',
        seen:r.feedback==='seen'?'已标记看过':'已取消看过',
        dispose:r.disposal==='trash'?'已移入回收站':'已移出回收站',o:'已记录一次高潮'};
      actionReceipt(messages[kind],{undo:async()=>{
        if(kind==='o')await postFeedback('o-undo');
        else if(kind==='dispose')await postFeedback('dispose');
        else{
          if(r.feedback)await postFeedback(r.feedback);
          if(before.feedback)await postFeedback(before.feedback);
        }
        if(state.state==='ads')await load(true);
      }});
      if(kind==='dispose'&&r.disposal==='trash'&&state.state==='ads'){
        disposeStage(true);await load(true);
      }
    }catch(error){actionFailure('操作',error)}finally{setActionBusy(b,false)}
  });
  const renderDetailTags=()=>{
    const wrap=$('#detailTags');if(!wrap)return;
    const byDisplay=new Map();
    (it.tags||[]).filter(t=>!DURATION_TAGS.has(t.k)).forEach(t=>{
      const key=foldName(tagLabel(t.k)),previous=byDisplay.get(key);
      // `足系` 与 `美腿` 的可见名相同；优先保留本身就是规范显示名的那条。
      if(!previous||foldName(t.k)===key&&foldName(previous.k)!==key)byDisplay.set(key,t)});
    const visible=[...byDisplay.values()].slice(0,40);
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
      const tag=b.dataset.removeTag;setActionBusy(b);
      try{const r=await api('/api/item-tag',{method:'POST',body:JSON.stringify({id:it.id,operation:'remove',tag})});
        if(!r.ok)throw new Error('标签未删除');
        const old=(it.tags||[]).find(x=>foldName(x.k)===foldName(tag))||{k:tag,cat:'general'};
        it.tags=(it.tags||[]).filter(x=>foldName(x.k)!==foldName(tag));renderDetailTags();
        actionReceipt(`已删除标签「${tagLabel(tag)}」`,{undo:async()=>{
          await api('/api/item-tag',{method:'POST',body:JSON.stringify({id:it.id,operation:'add',tag})});
          if(!(it.tags||[]).some(x=>foldName(x.k)===foldName(tag)))it.tags.push(old);
          renderDetailTags();
        }});
      }catch(error){actionFailure('删除标签',error)}finally{setActionBusy(b,false)}});
    const addTag=async tag=>{tag=tag.trim();if(!tag)return;
      try{const r=await api('/api/item-tag',{method:'POST',body:JSON.stringify({id:it.id,operation:'add',tag})});
      if(r.ok){
        if(!it.tags.some(x=>foldName(x.k)===foldName(tag)))it.tags.push({k:tag,cat:'general'});
        try{const old=JSON.parse(localStorage.getItem('peach.recentTags')||'[]').filter(x=>foldName(x)!==foldName(tag));
          localStorage.setItem('peach.recentTags',JSON.stringify([tag,...old].slice(0,12)))}catch(_e){}
        renderDetailTags();actionReceipt(`已添加标签「${tagLabel(tag)}」`,{undo:async()=>{
          await api('/api/item-tag',{method:'POST',body:JSON.stringify({id:it.id,operation:'remove',tag})});
          it.tags=(it.tags||[]).filter(x=>foldName(x.k)!==foldName(tag));renderDetailTags();
        }})
      }}catch(error){actionFailure('添加标签',error)}
    };
    const plus=$('#tagPlus'),picker=$('#tagPicker'),search=$('#tagPickSearch'),body=$('#tagPickBody');
    let detachOutside=null,activeIndex=-1;
    const closePicker=()=>{picker.hidden=true;plus.setAttribute('aria-expanded','false');
      if(detachOutside){detachOutside();detachOutside=null}};
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
    search.oninput=e=>{if(e.isComposing)return;renderPicker()};
    search.oncompositionend=renderPicker;
    search.onkeydown=e=>{const options=[...body.querySelectorAll('[data-pick]')];
      /* 选字那一下的回车是定字，不是「新建这个标签」——半截拼音会真的建成标签。 */
      if(e.isComposing)return;
      if(e.key==='Escape'){e.preventDefault();closePicker();plus.focus();return}
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!options.length)return;
        activeIndex=(activeIndex+(e.key==='ArrowDown'?1:-1)+options.length)%options.length;
        options.forEach((b,i)=>b.classList.toggle('active',i===activeIndex));options[activeIndex].scrollIntoView({block:'nearest'});return}
      if(e.key==='Enter'){e.preventDefault();if(activeIndex>=0&&options[activeIndex])options[activeIndex].click();
        else if(search.value.trim()){closePicker();addTag(search.value.trim())}}};
    plus.onclick=()=>{picker.hidden=false;plus.setAttribute('aria-expanded','true');renderPicker();search.focus();
      detachOutside=bindOutsideClose(plus,picker,closePicker)};
  };
  renderDetailTags();
  $('#stage').querySelectorAll('[data-entity-kind]').forEach(b=>b.onclick=()=>
    openEntity(b.dataset.entityKind,b.dataset.entityName));
  const paintLater=value=>{it.watch_later=value;const button=$('#stageLater');if(!button)return;
    button.setAttribute('aria-pressed',value);button.innerHTML=value?icon('check'):icon('bookmark-plus')};
  $('#stageLater').onclick=async()=>{const button=$('#stageLater');setActionBusy(button);
    try{const r=await api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})});
      paintLater(r.watch_later);actionReceipt(r.watch_later?'已加入稍后看':'已移出稍后看',{undo:async()=>{
        const restored=await api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})});
        paintLater(restored.watch_later);
      }});
    }catch(error){actionFailure('更新稍后看',error)}finally{setActionBusy(button,false)}};
  $('#betterVersion').onclick=async()=>{const b=$('#betterVersion'),wanted=b.getAttribute('aria-pressed')!=='true';
    const before={wanted:!!it.better_version,reason:it.better_version_reason||''};setActionBusy(b);
    const paintQuality=r=>{it.better_version=r.better_version;it.better_version_reason=r.better_version_reason;
      if(!$('#betterVersion'))return;$('#betterVersion').setAttribute('aria-pressed',String(r.better_version));
      $('#betterVersion').title=r.better_version?(r.better_version_reason||'已标记寻找更好版本'):'寻找高清、无水印或完整版'};
    try{const r=await api('/api/quality-goal',{method:'POST',body:JSON.stringify({id:it.id,wanted})});paintQuality(r);
      actionReceipt(r.better_version?'已标记寻找更好版本':'已取消寻找更好版本',{undo:async()=>{
        const restored=await api('/api/quality-goal',{method:'POST',body:JSON.stringify({id:it.id,wanted:before.wanted,reason:before.reason})});paintQuality(restored);
      }});
    }catch(error){actionFailure('更新版本需求',error)}finally{setActionBusy(b,false)}};
  const preferenceToggle=$('#preferenceToggle'),preferencePanel=$('#preferencePanel');
  preferenceToggle.onclick=()=>{const open=preferencePanel.hidden;preferencePanel.hidden=!open;
    preferenceToggle.setAttribute('aria-expanded',String(open));if(open)$('#likeReason').focus()};
  const savePreference=async(options={})=>{
    const btn=$('#savePreference'),like=$('#likeBtn'),stateText=$('#preferenceState');
    const before={liked:!!it.liked,reason:it.like_reason||''};
    setActionBusy(btn);
    btn.innerHTML=`${spinnerHtml('正在提交喜爱理由')}<span>提交中…</span>`;stateText.textContent='保存中…';
    const reason=$('#likeReason').value;
    const liked=options.liked??(like.getAttribute('aria-pressed')==='true'||reason.trim().length>0);
    const paintPreference=r=>{it.liked=r.liked;it.like_reason=r.like_reason;
      if(!$('#likeBtn'))return;$('#likeBtn').setAttribute('aria-pressed',r.liked);
      $('#likeBtn').setAttribute('aria-label',r.liked?'取消喜欢':'喜欢');
      $('#preferenceToggle').dataset.hasReason=String(!!r.like_reason);
      $('#likeReason').value=r.like_reason||''};
    try{const r=await api('/api/preference',{method:'POST',body:JSON.stringify({id:it.id,liked,reason})});
      paintPreference(r);
      stateText.textContent='已保存';setTimeout(()=>{if(stateText.textContent==='已保存')stateText.textContent=''},1400);
      actionReceipt(r.liked?'已保存喜欢偏好':'已取消喜欢',{undo:async()=>{
        const restored=await api('/api/preference',{method:'POST',body:JSON.stringify({id:it.id,...before})});
        paintPreference(restored);
      }});
    }catch(e){stateText.textContent='保存失败 · 请重试';actionFailure('保存喜欢偏好',e)}finally{
      setActionBusy(btn,false);btn.innerHTML='<span>提交</span>'}
  };
  $('#likeBtn').onclick=()=>savePreference({liked:$('#likeBtn').getAttribute('aria-pressed')!=='true'});
  $('#savePreference').onclick=savePreference;
  const vv=$('#vid');
  vv.addEventListener('play',()=>{if(!$('#stage').dataset.c){$('#stage').dataset.c='1';
    api('/api/play',{method:'POST',body:JSON.stringify({id:it.id})})}});
  if(it.play_seconds&&realDuration(it.duration)){
    const rp=Math.min(it.play_seconds/realDuration(it.duration),1)*100;
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
    /* 直接进「已保存」这一档。openFollow(true) 会 route 回干净的 /follow 再照 URL
       推导，所以状态要先写进 URL，光设全局会被推回未看。 */
    $('#openSavedFollow').onclick=()=>{
      followAuthor='';followProvider='';followTags=new Set();followMediaView='videos';
      followFilter='saved';route(followViewPath());openFollow(false)};
  }
  else if(g)g.onclick=async()=>{vv.hidden=false;g.remove();const mounted=await mountDetailPlayer(it,vv,true);stopAmbient=mountPlayerAmbient(vv);mounted?.one?.('dispose',stopAmbient)};
  else{const mounted=await mountDetailPlayer(it,vv,true);stopAmbient=mountPlayerAmbient(vv);mounted?.one?.('dispose',stopAmbient)}
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
  /* 同一个 -1 哨兵：`it.duration||v.duration||0` 对 -1 求值仍是 -1，通过了真值判断，
     于是 currentTime/-1 得到负比例，面板上就是「离开位置 -3320%」。后端 w_activity 有
     `dur > 0` 守卫，脏比例不会进账本；坏的只是显示。 */
  const paint=()=>{const d=realDuration(it.duration)||realDuration(v.duration);if(!d)return;
    const r=Math.min(v.currentTime/d,1);
    const w=sel.watched&&$(sel.watched),m=sel.mark&&$(sel.mark),t=sel.ratio&&$(sel.ratio);
    if(w)w.style.width=(r*100).toFixed(1)+'%'; if(m)m.style.left=(r*100).toFixed(1)+'%';
    if(t)t.textContent=(r*100).toFixed(0)+'%'};
  const flush=e=>{const d=realDuration(it.duration)||realDuration(v.duration);if(!acc&&!e&&!seeks)return;
    api('/api/activity',{method:'POST',body:JSON.stringify(
      {id:it.id,position:v.currentTime,duration:d,delta:acc,ended:!!e,seeks})})
      .then(r=>{ // 回填面板的真实观看率
        const rr=$('#realTxt'); if(rr&&r&&r.real_ratio!=null){
          const rp=Math.min(r.real_ratio,1)*100;
          rr.textContent=rp.toFixed(0)+'%';
          const b=$('#realBar'); if(b)b.style.width=rp.toFixed(1)+'%';
        }});
    acc=0;seeks=0};
  /* 十秒一次的上报只有一个定时器。onplay 每次新起一个而只有 onpause 清的话，
     「播放→拖动→播放」这类不经过 pause 的序列会把定时器叠起来；更要紧的是
     离开详情时既不 pause 也不 ended，setInterval 连着已被销毁的 video 一直跑，
     每十秒往 /api/activity 打一发。跟 wireFollowTelemetry 对齐：`emptied` 收尾，
     并向舞台登记一条撤销。 */
  const stopTelemetry=()=>{if(timer){clearInterval(timer);timer=null}};
  v.onplay=()=>{last=v.currentTime;stopTelemetry();timer=setInterval(()=>flush(false),10000)};
  v.ontimeupdate=()=>{const dt=v.currentTime-last;if(dt>0&&dt<2)acc+=dt;last=v.currentTime;paint()};
  v.onpause=()=>{stopTelemetry();flush(false)};
  v.onended=()=>{stopTelemetry();flush(true);if(!$('#tok').hidden)tokNext(1)};
  v.addEventListener('emptied',()=>{stopTelemetry();flush(false)},{once:true});
  onStageDispose(stopTelemetry);
  paint();
}

function wireFollowTelemetry(item,video){
  let last=0,acc=0,timer=null,started=false;
  const flush=ended=>{const duration=realDuration(item.duration)||realDuration(video.duration);
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
let tokLoading=false;
/* 没有 offset 参数：`sort=rand` 在服务端是未加种子的 `RANDOM()`（web_contract.py），
   每次请求都是一次全新的随机抽样，翻页偏移在它上面没有意义——带上去只会随机跳过
   若干行。续取靠的是调用点那个 `seen` 集合去重，不是偏移量。 */
async function fetchTok(){
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
// 旋转手机或改窗口大小后，同一条视频的铺满／完整显示判定可能翻转。
addEventListener('resize',()=>{
  if($('#tok').hidden)return;
  $('#tokTrack').querySelectorAll('video').forEach(tokFitOne);
});
async function openTok(startId,push=true){
  if(push)route('/immerse');
  $('#tok').hidden=false;document.body.style.overflow='hidden';setTokLoading(true,'加载内容…');
  try{
    tokList=await fetchTok();
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
  /* 当前这一条也过一遍 route()：竖划十条之后刷新页面，落回来的该是同一条片子，
     而不是重新抽一批。用 replace——每划一下都往历史里塞一条，后退键就废了。 */
  route('/immerse?id='+it.id,true);
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
      for(const key of ['q','loc','creator','studio','tag','len','dur_min','dur_max','orient','state','sort','dir']){
        const value=state[key];if(value&&!(key==='loc'&&value==='local,115')&&!(key==='sort'&&value==='daily'))query.set(key,value)
      }
      url.search=query.toString();history.replaceState({},'',url.pathname+(url.search||''));
    }
    v.play().catch(()=>{});
    $('#tokTitle').textContent=javDisplayName(it);
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
    const upd=()=>{const d=realDuration(v.duration)||realDuration(it.duration);
      if(d)prog.style.width=(v.currentTime/d*100).toFixed(2)+'%'};
    v.addEventListener('timeupdate',upd);
    // 拖动而不只是点。pointer 一套同时盖鼠标和触控，捕获指针后手滑出进度条
    // 也不会断。拖动中只画进度，松手才 seek——每帧都 seek 会让远程源一直重新缓冲。
    tokWireScrub(bar,prog,v,()=>realDuration(v.duration)||realDuration(it.duration));
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
    tokLoading=true;
    const more=await fetchTok();   // 每次都是新的随机抽样
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
  $(s).onclick=async()=>{const it=tokList[tokIdx],button=$(s),before=it.feedback||null;
    const paint=r=>{Object.assign(it,{feedback:r.feedback,o_count:r.o_count});
      if(tokList[tokIdx]?.id!==it.id)return;
      $('#tokDislike').setAttribute('aria-pressed',r.feedback==='dislike');
      $('#tokSeen').setAttribute('aria-pressed',r.feedback==='seen');
      $('#tokSeenLabel').textContent=r.feedback==='seen'?'已看':'看过';
      $('#tokOn').textContent=r.o_count||0};
    const post=async value=>{const r=await api('/api/feedback',{method:'POST',
      body:JSON.stringify({id:it.id,kind:value})});paint(r);return r};
    setActionBusy(button);
    try{const r=await post(kind);
      actionReceipt(kind==='o'?'已记录一次高潮':r.feedback===kind?
        (kind==='seen'?'已标记看过':'已标记不合口味'):
        (kind==='seen'?'已取消看过':'已取消不合口味'),{undo:async()=>{
          if(kind==='o')await post('o-undo');
          else{if(r.feedback)await post(r.feedback);if(before)await post(before)}
        }});
      if(kind==='dislike'&&r.feedback==='dislike')setTimeout(()=>tokNext(1),260)
    }catch(error){actionFailure('更新反馈',error)}finally{setActionBusy(button,false)}}});

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
    if(e.key===' '||e.key==='k'||e.key==='K'){
      e.preventDefault();          // 不加这句空格会把页面滚下去
      toggleVideoPlayback(video);
      return;
    }
    if(e.key==='m'||e.key==='M'){e.preventDefault();clickPlayerControl(video,'.vjs-mute-control');return}
    if(e.key==='f'||e.key==='F'){e.preventDefault();clickPlayerControl(video,'.vjs-fullscreen-control');return}
    if(e.key==='i'||e.key==='I'){e.preventDefault();clickPlayerControl(video,'.vjs-picture-in-picture-control');return}
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
    /* 管理区的换批行为写在路由表的 `refresh` 上：`reopen` 重开自己，
       `skip` 不参与（追更页重画要联网，只能由它自己的按钮触发），
       没写的（统计、数据管理、资源同步）落到统计页。 */
    const hit=matchRoute(ROUTES,decodeURIComponent(location.pathname));
    if(hit?.route.refresh==='skip')return;
    if(hit?.route.refresh==='reopen'){await hit.route.open(hit.params,false);return}
    await openStats(false);return
  }
  if(!$('#index').hidden){return}
  state.sort='seed';state.dir='';state.seed=rollSeed();
  // 顶部三层（女优头像、厂牌、标签）有 30 秒会话缓存，而 refreshAll 只重载网格：
  // 不清掉这两个缓存，「换一批」之后上面还是同一批人。
  barsDataCache=null;barsDataPromise=null;
  /* 网格和顶部三层一起换，两边耗时不一样，所以转圈归这一层管：挂在计数行的
     aria-busy 上时，网格先到就被 renderCount 摘掉，标签条还在等的那段时间里
     按钮已经停了。顶部三层与标签条不铺骨架——它们此刻有内容在屏幕上，撕成
     灰条再填回去比直接换掉更晃眼；骨架留给从无到有的首屏。 */
  document.body.classList.add('refreshing');
  try{await Promise.all([load(true),buildBars()])}
  finally{document.body.classList.remove('refreshing')}
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
function censorOn(){return document.body.classList.contains('censor')}
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
/* 正在被拖的那一行。松开鼠标全站只需要一个 window 监听。
   每 wireDrag 一个元素就往 window 上挂一条 mouseup 的话，麻烦在这些横向行是
   innerHTML 重绘出来的：每次重绘都换一批新节点，那些闭包连着已经脱离文档的元素
   永远不回收。一屏三层顶栏加两条横向带，翻十几页就攒下上百条死监听。 */
let dragRow=null;
window.addEventListener('mouseup',()=>{
  if(!dragRow)return;
  dragRow.style.cursor='';dragRow=null;
});
function wireDrag(el){
  if(!el||el.dataset.drag)return; el.dataset.drag='1';
  let sx=0,sl=0,moved=0;
  /* 同一个元素在宽屏不溢出、窄屏才溢出（`.count` 就是这样）。不判溢出就会在宽屏
     把滚轮和拖动从真正在滚的子元素手里抢走。 */
  const scrollable=()=>el.scrollWidth-el.clientWidth>1;
  el.addEventListener('mousedown',e=>{
    if(e.button!==0||!scrollable())return; dragRow=el;moved=0;sx=e.pageX;sl=el.scrollLeft;
    el.style.cursor='grabbing'});
  el.addEventListener('mousemove',e=>{
    if(dragRow!==el)return; const dx=e.pageX-sx; moved=Math.max(moved,Math.abs(dx));
    el.scrollLeft=sl-dx; e.preventDefault()});
  // 拖动过就吞掉这次点击，别误触发筛选
  el.addEventListener('click',e=>{if(moved>6){e.stopPropagation();e.preventDefault();moved=0}},true);
  // 滚轮竖向 → 横向
  el.addEventListener('wheel',e=>{
    if(scrollable()&&Math.abs(e.deltaY)>Math.abs(e.deltaX)){el.scrollLeft+=e.deltaY;e.preventDefault()}},
    {passive:false});
}
/* `#count` 一起登记：窄屏下排序筛选整行由 `.count` 自己横向滚动，而它没有滚动条，
   不接拖动和滚轮就只剩看得见够不着的半个按钮。 */
function wireAllDrag(){['#tagbar','#srow','#nrow','#count'].forEach(s=>wireDrag($(s)));
  document.querySelectorAll('.tier').forEach(wireDrag)}

/* 目录页（首页 + 四个筛选态）：筛选全部从 URL 读，路径只决定初始筛选态。
   `enteringHome` 判的是「从别处回到首页」：顶部三层有 30 秒会话缓存，不作废的话
   回到首页看到的还是上一次那批人。判据是 `lastRoutePath`，所以 `restoreRoute`
   要等派发完再更新它。 */
function openCatalog(path){
  const params=new URLSearchParams(location.search);
  const enteringHome=path==='/'&&lastRoutePath!=='/';
  if(enteringHome){barsDataCache=null;barsDataPromise=null}
  if(path==='/junk-files'){
    junkKind=cleanJunkKind(params.get('type')||'');
    junkView=params.get('view')==='dismissed'?'dismissed':'pending';
  }
  state={...state,loc:params.get('loc')||'local,115',creator:params.get('creator')||'',studio:params.get('studio')||'',
    tag:cleanTagFilter(params.get('tag')),tag_match:params.get('tag_match')==='any'?'any':'all',len:params.get('len')||'',
    dur_min:params.get('dur_min')||'',dur_max:params.get('dur_max')||'',orient:params.get('orient')||'',
    state:ROUTE_STATES[path]||params.get('state')||'',...resolveSort(params.get('sort'),params.get('dir')),
    seed:params.get('seed')||(enteringHome?rollSeed():state.seed||rollSeed()),q:params.get('q')||'',jav:params.get('jav')||''};
  $('#q').value=state.q;buildEdge();buildBars();load(true);
}
/* 回收站。它和目录页共用同一张网格，只是筛选被钉死成 `trash`。 */
function openTrash(push){
  if(push)route('/trash');
  state={...state,creator:'',studio:'',tag:'',orient:'',state:'trash',q:''};$('#q').value='';
  showHomeSurfaces();buildEdge();buildBars();load(true);
}
/* 索引页（女优／创作者／标签）三条路由共用。
   `push=true` 是从导航点进来：退出选择模式、不带搜索词从头开始。
   `push=false` 是地址栏已经在这一屏：视图状态从 URL 读。
   `q` 显式传入时优先——批量操作后的就地重取要保留搜索框里已经打好的词。 */
function indexQuery(){return $('#iq')?.value.trim()||''}
function openIndexRoute(kind,push,q=null){
  if(push){setSelectMode(false,true);return openIndex(kind)}
  const params=new URLSearchParams(location.search);
  if(kind==='tags'){
    tagIndexScope=params.get('scope')==='online'?'online':'local';
    tagIndexMode=params.get('view')==='cloud'?'cloud':'alphabet';
    const category=params.get('category')||'all';
    const categories=tagIndexScope==='online'?ONLINE_TAG_CATEGORIES:TAG_CATEGORIES;
    tagIndexCategory=categories.some(([key])=>key===category)?category:'all';
  }
  return openIndex(kind,q??(params.get('q')||''),false);
}
/* 沉浸模式当前这一条写在 `?id=`（见 tokShow），刷新和后退都该回到同一条片子。 */
function immerseStartId(){
  const id=new URLSearchParams(location.search).get('id');
  return /^\d+$/.test(id||'')?Number(id):undefined;
}

async function restoreRoute(){
  surfaceEpoch++;
  barsRequestSeq++;
  syncPageTitle(location.href);
  buildDrawerNavigation();
  const path=decodeURIComponent(location.pathname);
  if(path==='/'&&new URLSearchParams(location.search).get('state')==='ads'){
    route(junkPath(),true);await restoreRoute();return;
  }
  /* 唯一的派发点：路径匹配哪条路由，就把那一屏打开。`push=false`——地址栏本来
     就是它，再 `route()` 一次会往历史里塞一条重复记录。
     `lastRoutePath` 等派发完再更新：目录页要拿它判断是不是刚从别处回到首页。 */
  const hit=matchRoute(ROUTES,path);
  try{
    if(hit)await hit.route.open(hit.params,false);
    else{showHomeSurfaces();disposeStage(false)}
  }finally{lastRoutePath=path}
}
window.addEventListener('popstate',restoreRoute);
/* 左侧导航、管理条、页面标题和面包屑只认 location 和本地设置，一个请求都不等。
   挂在下面那条链上时它们排在 /api/sources 和 /api/facets 后面，实测让骨架先顶着
   一个没有标题的空壳站了约半秒。buildManageBar() 内部会一并建好左侧导航，
   所以这里不再单独调 buildEdge()。 */
buildManageBar();
/* 那两个聚合查询喂的是首页顶部三条横条。深链进管理页或索引页时横条一开始就收着，
   结果没人看，却排在这一页自己的数据前面。 */
loadSourceStatus()
  .then(()=>wantsDiscoveryBars()?buildBars():null)
  .then(async()=>{buildEdge();wireAllDrag();await restoreRoute();scheduleStickySurfaces()})
  .then(loadSyncedSettings);
