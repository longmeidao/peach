import { boundedPreference, createSettingsStore, loadSettingsPanel, settingsPanelApi, sidebarSectionHtml, wireSidebarGroups, transitionTheme } from './dist/peach-ui.js';
import {$, ENTITY_ROUTES, LOC, ROUTE_ENTITIES, ROUTE_STATES, STATE_LABELS, STATE_ROUTES, api, isAbort, mapLimit, entityPath, esc, fmtClock, fmtDur, fmtSize, foldName, icon, isCatalogPath, realDuration, seededRank} from './js/core.js';
import { faceFrame } from './js/face-frame.js';
import { searchMorphFrames } from './js/search-morph.js';
import { filterScrollState } from './js/filter-scroll.js';
import { selectRange, selectionSummary, selectGroup, syncSelectionToolbar } from './dist/peach-ui.js';
import { MEDIA_SOURCE_ICONS } from './js/media-source-icons.js';
import { boardPageSkeleton, detailSkeletonHtml, initBoardControls } from './dist/peach-ui.js';
import { imageFallbackAttrs, wireImageFallbacks } from './js/image-fallback.js';
import { javDisplayName, javTitleHtml } from './js/jav-title.js';
import { matchRoute, routeLabel } from './js/routes.js';
import { initMiddleTruncate } from './js/middle-truncate.js';
import { tagLabel } from './js/tags.js';
import { playUiSound, setUiSoundsEnabled, wireUiSounds } from './js/ui-sounds.js';
import { ACCENTS, DEFAULT_ACCENT, DEFAULT_HOME_GLOW, GLASS_NATIVE_PRESET, HOME_GLOW_CHOICES, HOME_GLOW_PRESETS, HOME_GLOW_SPOTS, glowAccent, glowChipFill, glowPalette, isNativeGlass, normalizeAccent, normalizeHomeGlow, paintGlassFaces, paintHomeGlow } from './js/home-glow.js';
import { mountIsland, unmountIsland, updateIsland, islandMounted, preloadIslands, paginationHtml, pageCount, clampPage, preferredDirection, showToast, followJobProgress } from './dist/peach-ui.js';
import { junkCountSkeletonHtml, junkPath, junkRoute } from './dist/peach-ui.js';
import { catalogSuggestions, catalogEmptyHtml, catalogFilterSkeletonHtml, syncSidebarSurface, sidebarTagCounts, sidebarHasCatalogContent, cleanupSkeletonHtml } from './dist/peach-ui.js';
import { javImageKind, normalizeJavLayout, normalizeJavPreferences, panelFrame, relayoutJavImages, syncJavImages, nativeImageFit, faceSourceScale, entitySkeletonHtml } from './dist/peach-ui.js';
import { cancelStreamSession, clickPlayerControl, directStreamSource, ensureVideojs, fmtSpeed, loadStage, newStreamSession, playableStreamSource, stageApi, streamSpeedBits, wireTelemetry as playerWireTelemetry } from './dist/peach-ui.js';
import {
  attachOverlayScrollbar, breadcrumbHtml, checkboxHtml, confirmModal, dismissMenu, emptyStateHtml,
  fitSkeleton, formModal, iconSwapHtml, iconSwitchHtml, indexSkeletonHtml, loadingDotsHtml,
  dissolveValue, popBadges, revealSkeleton, revealTexts, setIconSwap, swapText,
  boardTabsHtml, moveGlidePane, glideEase, collectionHeaderHtml, wireHorizontalScroller, noteHtml, presentMenu, gaugeHtml, scrollerHtml, searchInputHtml,
  SKELETON_REVEAL_DELAY, setActionBusy, skeletonHtml, spinnerHtml, growCollapse, wireAnchoredMenu, wireBusyActions, wireCollapse, wireDragReorder,
  wireOverlayScrollbars, wireScrollers, configurationSkeletonHtml, wireAutoScroll, stopAutoScroll, scrollMovesAnchor,
  postSetupTutorialMarker, setPostSetupTutorialMarker, postSetupTutorialCollapsed, setPostSetupTutorialCollapsed,
  postSetupTutorialSkipped, setPostSetupTutorialSkipped, postSetupTutorialSignature,
  nextPostSetupTutorialRequest, isCurrentPostSetupTutorialRequest, resetPostSetupTutorialState,
} from './js/ui-components.js';

initMiddleTruncate(document);
initBoardControls();
wireBusyActions(document);
attachOverlayScrollbar(document.documentElement,{variant:'page'});
attachOverlayScrollbar($('#drawerScroll'));
// 滚动容器是各处 innerHTML 现画出来的，没有一个统一的渲染出口可以挂。与其在几十个
// 渲染点各补一行（漏一个就是那一处又冒出系统滚动条），不如认 DOM 变动本身：一批变动
// 只扫一次，attachOverlayScrollbar() 自带幂等，已经接过的容器直接跳过。
// 合批用 setTimeout 不用 requestAnimationFrame：页面在后台标签页里时 rAF 整个停摆，
// 那期间画出来的容器会一直等到重新可见才接上滚动条。
let overlayScan=0;
new MutationObserver(()=>{
  if(overlayScan)return;
  overlayScan=setTimeout(()=>{overlayScan=0;wireOverlayScrollbars()});
}).observe(document.body,{childList:true,subtree:true});
wireOverlayScrollbars();
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
let homeHasFeed=null;
const selected=new Set(),followSelected=new Set();
let barsRequestSeq=0,barsDataCache=null,barsDataAt=0,barsDataPromise=null;
// 顶部三层与抽屉上一次画的是哪一份：口径加数据，两样都没变就不必再画一遍。
let barsRendered='';
/* 首页筛选条（`catalog-filter` 岛）的整份 props、挂载中的那一次、标签条的成员（见 `paintCatalogFilter`）。 */
let catalogFilterProps=null,catalogFilterMounting=null,catalogTagRows=[],catalogTopsPages=null;
/* 侧栏「更多」摊开时要照最新那份 facets 重画那一列。挂在 buildBars 的闭包上就只能是
   画那一遍时的那份——中途改过筛选，摊开看到的是一列旧数字。 */
let barsFacets=null,barsScopedCreators=[];
let loadRequestSeq=0;
// `#grid` 上此刻挂的是哪一个 island：目录与回收站的 `catalog-grid`，或垃圾文件的 `junk-queue`。
let gridIsland='';
/* `followRevision` 是关注页岛的刷新代次：已经挂着时要求重读（批量标记之后、前进后退），
   推一个新代次让它重取，不重挂。 */
let followFilter='',followRevision=0;
/* 值是天数，`0` 表示不限。选项文本自己说清量的是时间：这一行不挂文字标签，收起时
   框里只剩当前这一项，「全部」放在时钟图标旁边读不出是全部什么。 */
const FOLLOW_INITIAL_RANGE_OPTIONS=[['0','不限时间'],['7','最近 7 天'],['30','最近 30 天'],
  ['90','最近 90 天']];
let followAuthors=new Set(),followProviders=new Set(),followTags=new Set(),followWorks=new Set(),followMediaView='videos',followDetailReturnPath='/follow';
/* 看的那一页按什么排。只有这三档在每条更新上都成立：观看次数、体积那几列问的是本机
   文件，而这一页上的东西多数还没下载。壳只拿它核对地址栏上的 `sort`；键上的说法在岛里
   （`follow-feed.ts` 的 `FOLLOW_FEED_DIR_WORDS`）。 */
const FOLLOW_FEED_SORTS=[['new','更新时间'],['hot','热度'],['dur','时长']];
/* 「换一批」按下去就是这一档：整批更新按一粒种子打散，跟首页同一个意思。它没有自己的
   排序键——那三枚键任一按下就离开它；种子写进地址，刷新和后退回到的是同一批次序。 */
const FOLLOW_RANDOM_SORT='rand';
let followSort='new',followDir='desc',followSeed=0;
let sidebarDragKey=null;
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
  /* 索引页的状态全在地址栏上（过滤词、范围、视图、类型由页面自己写回），所以就地重取
     与刷新都是按当前地址重开一次。 */
  {match:'/performers',nav:'performers',title:'女优',
    open:(params,push)=>openIndex('performers',push),
    reload:()=>openIndex('performers',false)},
  {match:'/creators',title:'创作者',
    open:(params,push)=>openIndex('creators',push),
    reload:()=>openIndex('creators',false)},
  /* 厂牌出片、事务所出人，是两种实体，所以是两条路径；页内那个
     开关只是在两条路径之间走，不是同一份数据的两种筛选。 */
  {match:'/studios',nav:'studios',title:'厂牌',
    open:(params,push)=>openIndex('studios',push),
    reload:()=>openIndex('studios',false)},
  {match:'/agencies',title:'事务所',
    open:(params,push)=>openIndex('agencies',push),
    reload:()=>openIndex('agencies',false)},
  {match:'/tags',nav:'tags',title:'标签',
    open:(params,push)=>openIndex('tags',push),
    reload:()=>openIndex('tags',false)},
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
  {match:'/scraping',section:'cleanup',title:'来源和凭证',refresh:'reopen',
    open:(params,push)=>openScraping(push)},
  {match:'/follow',nav:'follow',title:'关注',refresh:'skip',
    open:(params,push)=>openFollow(push),reload:()=>openFollow(false)},
  {match:'/follow-manage',section:'follow',title:'关注管理',refresh:'skip',
    open:(params,push)=>openFollowManage(push)},
  // 这台电脑的媒体文件夹与端口。页面是 island，数据走 /api/configuration。
  {match:'/configuration',section:'configuration',title:'配置',refresh:'reopen',
    open:(params,push)=>openConfiguration(push)},
  // 任务中心的界面：谁在跑、谁被挡下了、刚跑完的怎么样。数据走 /api/tasks。
  {match:'/activity',section:'activity',title:'活动',refresh:'reopen',
    open:(params,push)=>openActivity(push)},
  {match:'/immerse',nav:'immerse',title:'沉浸模式',
    open:(params,push)=>openTok(immerseStartId(),push)},
];
/* 登记一条新路由。ADR-0022 的迁移是逐屏搬到 `frontend/`：搬走的那一屏在自己的
   入口里登记，不必回来改这张表。挂在 window 上是因为 app.js 是入口模块，别的
   bundle 没法 import 它。
   插在表尾，所以新路由要么是一条新路径，要么比现有条目更具体。 */
const registerRoute=spec=>{ROUTES.push(spec);return spec};
window.peachRegisterRoute=registerRoute;

const pageSkeletonHtml=(label,{cards=false,className='',variant='',count,fill,cardRatio,gridClass='',gridSize=''}={})=>
  skeletonHtml(label,{variant:variant||(cards?'cards':'panel'),className,gridClass,gridSize,
    ...(count?{count}:{}),...(fill===undefined?{}:{fill}),...(cardRatio?{cardRatio}:{})});
/* 关注页列表那一块的骨架：进页整块骨架的下半，也是岛换筛选时列表区铺的那一块。图片视图借
   照片墙的网格算式，列数跟着照片墙尺寸档走。 */
const followContentSkeletonHtml=(media=new URLSearchParams(location.search).get('media')==='images'?'images':'videos',
  label='正在读取关注内容')=>pageSkeletonHtml(label,{cards:true,className:'follow-content-skeleton postercard-skeleton',
  gridClass:media==='images'?'followlist followphotowall':'',gridSize:photoSize()});
/* 关注页的骨架跟首页共用海报卡那套几何：网格算式、卡内每一格都一样，只有归属行
   高一点（岛卡片的署名行至少 21px，见 `follow-feed.css`）。上面是它自己的创作者行、题材行和那块
   两排的玻璃浮层，形状取 `.tier`、`.tagbar`、`.count` 本身，所以和首页顶栏那两排是
   同一枚：创作者行铺 `av`、题材行铺 `brandpill`，跟内容回来之后的形状一致。外框
   要自己写全：岛挂上之前没有别处替它合并外框，少了它上下两排会被画成两块各带圆角的
   浮层，等内容回来又并成一块。 */
const followSkeletonHtml=(label='正在读取关注内容')=>`<div class="follow">
  <div class="followhead"><h2 class="pagetitle">关注</h2></div>
  <div class="tier followauthors" data-skeleton-tier="av"></div>
  <div class="tier followworks" data-skeleton-tier="brandpill"></div>
  <div class="board-filter-frame" data-filter-frame>
    <div class="tagbar followfilters" data-filter-row="top" data-skeleton-tier="pill"></div>
    <div class="count followcount" data-filter-row="bottom"><span class="mono"><span class="countskeleton"></span></span></div></div>
  ${followContentSkeletonHtml(undefined,label)}</div>`;
/* 分类名是静态文案，骨架和复核页各要一份，所以它排在骨架前面而不是跟着复核页那段代码。 */
const REVIEW_LABELS={metadata_fields:'元数据字段',creator_tags:'创作者标签',studio_logos:'厂牌 Logo',performer_avatars:'女优头像',western_identity:'西方身份回配',code_creators:'番号目录存疑',fc2_markings:'FC2 评论标记',fc2_similarity:'FC2 跨号相似',video_endcards:'片尾/出处证据'};
/* 复核页是左边一列分类、右边工具条加一格一格 Fieldset，骨架就用最终容器的那几个类名，
   分栏、列宽和卡高全由页面自己那套规则给：读完数据只是把占位换成内容，版面一格不挪。
   分类名和「复核分类」这两样与数据无关，直接写出来；等的是每类多少条，所以只有计数
   那一枚是占位。工具条上那三件——分组方式、分类筛选、全选本页——要等队列回来才知道
   选项和条数，三枚占位一件对一件。 */
const reviewSkeletonHtml=(label='正在读取复核队列')=>`<div class="review review-workspace review-skeleton" data-skeleton="review" aria-busy="true" aria-label="${esc(label)}">
  <div class="reviewcontrols" data-section-nav><h2 class="review-category-title">复核分类</h2>
    <div class="reviewtabs" data-section-items>${Object.values(REVIEW_LABELS).map((text,i)=>
      `<button type="button" disabled aria-selected="${i===0}">${esc(text)}<span class="skeleton reviewcountskeleton" aria-hidden="true"></span></button>`).join('')}</div></div>
  <div class="reviewbulkbar reviewbulktoolbar" aria-hidden="true">${'<span class="skeleton reviewtoolskeleton"></span>'.repeat(3)}</div>
  <section class="reviewsection"><div class="reviewlist">${
    '<div class="skeletoncard" aria-hidden="true"><i></i><b></b><em></em></div>'.repeat(6)}</div></section></div>`;
$('#loadSentinel').innerHTML=loadingDotsHtml('继续载入中…');
$('#tokLoader').insertAdjacentHTML('afterbegin',spinnerHtml('媒体加载中'));
/* 网格还没挂上 island 时，壳把骨架写进 `#grid > .grid`。卡片都归 island：目录与回收站是
   `catalog-grid`，垃圾文件是 `junk-queue`。同形骨架复用节点，只有骨架交给内容才淡入。 */
const setGridCards=html=>revealSkeleton($('#grid'),()=>{$('#grid').innerHTML=`<div class="grid">${html}</div>`});
/* 「本页有哪些卡」，Shift 连选按这个顺序：目录、垃圾文件与资料页网格里的卡。竖屏带
   和接着看那一排不在其中，它们不在网格的分段里。 */
const gridCards=()=>document.querySelectorAll(
  ':is(#grid,#index [data-entity-grid]) [data-media-grid] > [data-media-card][data-id]');
/* 骨架只盖这次加载真会变的东西，也就是读数那一串数字：筛选条下排那一格换成微光，排序键与
   版式照当前 state 推过去。连它们一起收掉的话，点下去的那一枚会在等数据的这段时间里失去高亮，
   看着像没点上。上方的标签条和已选条件同理不动，它们本来就不随这次请求变。 */
function renderCatalogLoading(label='正在读取作品'){
  const count=$('#count');
  /* 垃圾文件那一屏的计数行是自己的：一块摘要面加一条分类切换，没有排序也没有换批。
     这一版是 `junk-queue` island 等数据时那一版的静态副本，island 挂上就换掉它；骨架里的
     分类链接是真的 `<a href>`，React 包没到时点下去照常换页。目录与回收站的读数在筛选条里，
     这一行留空。 */
  const junk=decodeURIComponent(location.pathname)==='/junk-files';
  count.classList.toggle('manage-static',junk);
  count.classList.toggle('junkcount',junk);
  if(junk){
    count.setAttribute('aria-busy','true');count.setAttribute('aria-label',label);
    count.innerHTML=junkCountSkeletonHtml(junkRoute(location.search));
    fitSkeleton(count);
  }else{
    count.removeAttribute('aria-busy');count.removeAttribute('aria-label');count.textContent='';
    if(state)paintCatalogFilter({count:null,...catalogHeadProps()});
  }
  /* 骨架一铺上去就得把底部那颗 Loading Dots 收掉。骨架说的是「等下会出现几张什么
     形状的卡」，dots 说的是「上面已经有内容，还在往下接」；两段同时在场时一屏里
     铺着两种等待动画，而实际只有一次请求在跑。哨兵的可见性由数据落地后的
     `has_more` 重新决定，所以这里只管收，不必记住原值。 */
  $('#loadSentinel').hidden=true;
  /* 网格已经挂着时骨架归它自己铺：`#grid` 是它的容器，壳往里写会把 React 根冲掉。 */
  if(islandMounted($('#grid')))return;
  const grid=$('#grid'),placeholder=catalogSkeletonHtml(label);
  const skeleton=grid.querySelector('.catalog-skeleton');
  if(skeleton?.dataset.skeleton===skeletonKeyOf(placeholder)
    &&Number(skeleton.querySelector('[style]')?.style.getPropertyValue('--skeleton-card-ratio'))===catalogCardRatio())return;
  if(skeleton)grid.innerHTML=`<div class="grid">${placeholder}</div>`;
  else setGridCards(placeholder);
  fitSkeleton($('#grid'));
}
/* 每个管理表面的加载态只有一份定义，深链启动和路由到位后都从这里取。
   两处各写各的时，整页刷新会连播两段动画：先一张通用大布局骨架，再各页自己的
   加载态（数据管理那张还是 Loading Dots）。取同一份，键就相同，
   showManagementBody 认出是同一张后不再重画。 */
const MANAGEMENT_PLACEHOLDERS={
  '/stats':()=>`<div class="insightpage"><div class="insighttoolbar" aria-hidden="true"><span class="skeleton stats-lede-skeleton"></span></div>${pageSkeletonHtml('正在读取统计',{variant:'dashboard'})}</div>`,
  // 口味页与统计页同一套版式：指标带、一块主详情、下面同层的数据面板。
  '/taste':()=>`<div class="tastepage">${pageSkeletonHtml('正在读取口味分析',{variant:'dashboard'})}</div>`,
  '/data-cleanup':()=>cleanupSkeletonHtml(),
  // /resource-sync 只是数据管理页上的一个锚点，启动时占位也该是数据管理那张。
  '/resource-sync':()=>MANAGEMENT_PLACEHOLDERS['/data-cleanup'](),
  '/duplicates':()=>pageSkeletonHtml('正在比对重复内容',{cards:true}),
  '/review':()=>reviewSkeletonHtml(),
  '/quality-goals':()=>pageSkeletonHtml('正在读取高清版目标',{cards:true}),
  // 活动页是三段纵向排开的清单，不是同质卡片网格：骨架画三块窄条。
  '/activity':()=>pageSkeletonHtml('正在读取任务活动',
    {cards:true,count:3,fill:false,className:'activity-skeleton'}),
  '/playlists':()=>pageSkeletonHtml('正在读取播放列表',{cards:true}),
  // 关注管理是三个大区（添加关注、关注列表、凭据），不是一屏同质卡片：
  // 骨架照 .fsec 的轮廓画三块，六张 16:9 占位说的是另一个页面的结构。
  '/follow-manage':()=>`<div class="follow">${pageSkeletonHtml('正在读取关注管理',
    {cards:true,count:3,fill:false,className:'followmanage-skeleton'})}</div>`,
  '/configuration':()=>configurationSkeletonHtml(),
  /* 采集来源是 812px 窄列里一叠同宽的 Fieldset：一块高清封面加六个来源。骨架画四块，
     那是首屏装得下的张数；说明那一句是静态文案，与数据无关，立刻显示。 */
  '/scraping':()=>`<div class="scraping-page"><p>高清图片可能要经代理才能下载，先检查连接。</p>
    ${pageSkeletonHtml('正在读取采集来源',{cards:true,count:4,fill:false,className:'cleanup-skeleton'})}</div>`,
};
/* 关注管理的骨架要照用户上次选的视图画：等数据的这段时间画成卡片、数据到了换成表格
   的话，同一次进入里版式会整个翻一遍。视图是这台浏览器的偏好，取值走
   `followListLayout()`——偏好那份存储声明在本行下面，直接读它就是声明前引用，
   会提升的函数声明才能从这里回去问。页面自己的那份状态在 island 里。排序与方向在地址栏
   里，骨架上的排序框和方向键照它画，跟接管后是同一档。 */
const managementPlaceholder=path=>
  boardPageSkeleton(path,{followLayout:followListLayout(),
    ...(path==='/follow-manage'?(({sort,dir})=>({followSort:sort,followDir:dir}))(followManageParams()):{})})||
  (MANAGEMENT_PLACEHOLDERS[path]||(()=>pageSkeletonHtml('正在读取页面')))();
/* 顶部三层只属于首页。深链启动时先画一遍再由路由收起来，等于向管理页和索引页
   承诺了三条永远不会到货的横条。 */
function hideDiscoveryBars(){$('#catalogFilter').style.display='none';syncCatalogFilterScreen()}
/* 启动那一屏收没收横条，就是这一次启动要不要那两个聚合查询。问屏幕不问路径：
   判断只写在上面那个函数里一份，两边各抄一张路径表迟早会对不上。 */
const wantsDiscoveryBars=()=>$('#catalogFilter').style.display!=='none';
/* 资料页形状名单（`loadEntityShapes`）的在途请求，和画骨架前最多等它多久。 */
let entityShapesReady=null;
const ENTITY_SHAPES_WAIT=400;
/* 那 400ms 只算页面能画东西的时间。启动脚本发出名单请求后还要连续跑几百毫秒，响应这时
   已经到了、只是排在队里；按墙钟算的话计时器常常先于它被处理，骨架就画成了没有那两块的
   样子。所以每 50ms 醒一次，被长任务拖住的那一截只记 50ms。 */
function waitEntityShapes(){
  const deadline=new Promise(resolve=>{
    let left=ENTITY_SHAPES_WAIT,last=performance.now();
    const tick=()=>{
      const now=performance.now();
      left-=Math.min(now-last,50);last=now;
      if(left>0)setTimeout(tick,Math.min(left,50));else resolve();
    };
    setTimeout(tick,50);
  });
  return Promise.race([entityShapesReady||=loadEntityShapes(),deadline]);
}
/* 冷启动直接落在详情地址上：详情下面那份列表一次请求都没发过，由 `fillIdleCatalog` 补发一次。 */
let bootDetailDeepLink=false;
function renderInitialSurfaceLoading(){
  const path=decodeURIComponent(location.pathname);
  /* 骨架画的就是这个表面，所以先把 `data-surface` 写上：深链冷启动时 `restoreRoute()`
     排在这一步后面，等它写的话骨架会先按默认版式铺一遍，数据到货再跳成分栏。 */
  document.body.dataset.surface=location.pathname;
  if(/^\/(item\/\d+|(?:mix|parts|editions|playlists)\/\d+\/\d+)$/.test(path)){
    /* 详情的骨架归舞台岛：路由到位后 `openItem` 取回 React 包就画。下面那份列表照这一次补发。 */
    hideDiscoveryBars();bootDetailDeepLink=true;return;
  }
  if(path==='/junk-files'){
    /* 垃圾文件是一屏同质卡片，等的是内容结构不是后台进度：Loading Dots 说的是
       「还在跑」，这里要说的是「等下会出现几张什么形状的卡」，所以用目录骨架。 */
    renderCatalogLoading('正在读取垃圾文件');
    return;
  }
  const management=new Set(['/stats','/taste','/review','/data-cleanup','/duplicates','/quality-goals','/scraping',
    '/playlists','/resource-sync','/follow','/follow-manage','/configuration','/activity']);
  if(management.has(path)||path.startsWith('/follow/item/')){
    hideDiscoveryBars();
    const stats=$('#stats');stats.hidden=false;clearCatalogGrid();
    stats.innerHTML=path.startsWith('/follow/item/')?detailSkeletonHtml():path.startsWith('/follow')&&path!=='/follow-manage'
      ?followSkeletonHtml('正在读取关注内容')
      :managementPlaceholder(path);
    fitSkeleton(stats);
    return;
  }
  if(/^\/(performers|creators|studios|agencies|tags)$/.test(path)){
    hideDiscoveryBars();
    showIndexSkeleton(indexRoute(path.slice(1)));
    return;
  }
  if(/^\/(?:performers|creators|studios|agencies)\//.test(path)){
    hideDiscoveryBars();
    $('#index').hidden=false;clearCatalogGrid();
    // 形状名单这时刚发出去：等它一下再画，骨架第一帧就带着这一位有的那两块。
    const kind=ROUTE_ENTITIES[path.split('/')[1]],name=path.split('/').slice(2).join('/');
    void waitEntityShapes().then(()=>{
      if($('#index').firstElementChild||decodeURIComponent(location.pathname)!==path)return;
      showEntityLoading(kind,name);
      fitSkeleton($('#index'));
    });
    return;
  }
  /* 未匹配的地址没有随后的读取，不能留一张永远不会被替换的目录骨架。合法的目录、
     回收站和沉浸模式都有路由，才进入各自真实请求对应的等待态。 */
  if(!matchRoute(ROUTES,path)){
    clearCatalogGrid();$('#count').textContent='';$('#loadSentinel').hidden=true;
    return;
  }
  renderCatalogLoading();
}

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
  /* 侧栏那块玻璃的动画从这里起跑，不从点击那里：这一行是激活态唯一的权威出口，
     窄栏、抽屉、浏览器后退和键盘走的都是它。挂在点击上等于每加一个入口补一次。
     它跑在 `route()` 的同步段里，比抽屉重画早一拍，玻璃拿到的是旧位置到新位置。 */
  syncNavGlide(true);
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
  /* 那条横幅讲的是库里那趟后台任务的下场，跟当前看的是哪一份名单无关。跟着每次取数
     卸了再挂，换一条筛选就会让它塌一下再撑回来——实测那一下底下整块先往上跳 62px，
     二十来毫秒后落回原处，比它要说的那句话显眼得多。目录页之间它一直挂着，自己在轮询
     库那边的进度；离开目录页才收起，那些页面本来就不该有它。 */
  if(!isProcessingNoticePath(path))unmountIsland($('#libraryProcessingNotice'));
  /* 首页那一行新作同样只属于目录页。管理区的入口不经过 `showHomeSurfaces`，离开目录页时
     在这里收起并清空，连同它的自动滚动一起停掉。 */
  if(!isFeedNewPath(path))clearHomeFeed();
  /* 管理区正文的容器每次换页都经过这里，所以卸载也落在这里。React 档的页面是一棵自己
     管取数的根：不卸掉它，离开之后那棵根还活着，有轮询的页面照着原节律继续敲库。
     没挂过东西的容器 unmountIsland 直接返回，逐页判断反而会漏掉新迁过来的那一页。 */
  unmountIsland($('#stats'));
  /* 资料页那块（换头像挂在它的圆框上）在管理区打开时只是被藏起来，DOM 还在。 */
  unmountIsland($('#index'));
  /* 目录网格同理：目录页与回收站之间它一直挂着，换筛选只是换查询；去别的页面就卸掉，
     那些页面接着会往 `#grid` 里写自己的东西。 */
  if(!isCatalogPath(path)&&path!=='/trash')clearCatalogGrid();
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
  queueMicrotask(()=>{syncHeaderActions();paintListTitle();buildDrawerNavigation();void syncPostSetupTutorial()});
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
/* 侧栏默认给的那八个入口和它们的次序。首页之后先是关注——它是每天有新东西的那一屏；
   JAV 是主库最常用的浏览模式，排在三个索引（艺人、标签、厂牌）前面；已标记是回头找，
   管理垫底。播放列表和沉浸模式默认不在：两者都是从一条作品或一个索引里发起的动作，
   常驻一格换来的是每次都要跳过它。要它们的人在设置里加回来，键仍在 NAV_CATALOG 里。
   这份清单与 `src/peach/web_settings.py` 的同名常量逐字比对（test_web_settings.py）。 */
const DEFAULT_SIDEBAR_ORDER=['','follow','jav','performers','tags','studios','flagged','manage'];
const OPTIONAL_SIDEBAR_KEYS=['playlists','immerse','stats','review','data-cleanup','trash','follow-manage','quality'];
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
/* 词表可换：关注页排的是在线更新，列不一样（热度那一列只有它有），但「点未选中项换列、
   点选中项翻方向」和箭头怎么画两页完全相同。传表进来，那三枚函数就不必各写一份。 */
const sortDirWord=(key,dir,words=SORT_DIR_WORDS)=>(words[key]||[])[dir==='asc'?1:0]||'';
const defaultSortDir=(key,words=SORT_DIR_WORDS)=>words[key]?'desc':'';
/* 主题三档，键名与 <html> 上的 data-theme 同一套写法：web/css/01-base.css 的色板
   已经按 `prefers-color-scheme` 和 `[data-theme]` 两条路径写好，这里只负责选哪一条。
   跟随系统是默认档，选它等于不写属性。 */
const THEME_CHOICES=['system','light','dark'];
const JAV_LAYOUTS=[['big','大图','maximize'],['small','小图','layout-grid']];
/* 图片墙是等宽网格，改的是列数。默认小图——一套图几十上百张，先看得见全貌，挑中
   哪一张再点开看大的。 */
const PHOTO_SIZES=[['big','大图','maximize'],['small','小图','layout-grid']];
const PHOTO_LAYOUTS=[['fixed','固定比例','layout-grid'],['masonry','瀑布流','columns-2']];
/* 显示器用于跟随系统主题和详情页的画面分辨率。 */
const THEME_OPTIONS=[['system','跟随系统','monitor'],['light','浅色','sun'],['dark','深色','moon']];
const DEFAULT_SETTINGS={batchSize:60,defaultSort:'seed',sortDefaultsVersion:3,hoverDelaySeconds:5,seekSeconds:10,searchHistoryLimit:10,relatedLimit:20,javLayout:'big',homeLayout:'small',javImage:'cover',followLayout:'default',peopleLayout:'big',photoSize:'small',ambientMode:true,miniplayer:true,theaterMode:false,theme:'system',groupCollapse:true,sidebarOrder:DEFAULT_SIDEBAR_ORDER,homeGlow:DEFAULT_HOME_GLOW,accent:DEFAULT_ACCENT};
let appSettings={...DEFAULT_SETTINGS};
try{appSettings={...DEFAULT_SETTINGS,...JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}}catch(_e){}
appSettings.followInitialDays=[0,7,30,90].includes(+appSettings.followInitialDays)?+appSettings.followInitialDays:30;
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
appSettings.batchSize=boundedPreference(+appSettings.batchSize,1,200,60);
appSettings.defaultSort=allowedSetting(appSettings.defaultSort,SORT_KEYS,'seed');
appSettings.hoverDelaySeconds=boundedPreference(+appSettings.hoverDelaySeconds,0,60,5);
appSettings.seekSeconds=boundedPreference(+appSettings.seekSeconds,1,300,10);
delete appSettings.loginDays;
appSettings.ambientMode=appSettings.ambientMode!==false;
appSettings.theaterMode=appSettings.theaterMode===true;
appSettings.groupCollapse=appSettings.groupCollapse!==false;
appSettings.detailAutoplay=appSettings.detailAutoplay!==false;
appSettings.miniplayer=appSettings.miniplayer!==false;
appSettings.uiSounds=appSettings.uiSounds!==false;
appSettings.feedAutoScroll=appSettings.feedAutoScroll!==false;
/* 新作那一行收不收合集由服务端按账本里的设置筛（列表、未读数、补封面同一份），这里只是
   镜像：开关的真相在 `/api/settings`。默认收起大合集与切片、单人合集照列。 */
const FEED_COMPILATION_KEYS=['feedHideGroupCompilations','feedHideSoloCompilations','feedHideExcerpts'];
appSettings.feedHideGroupCompilations=appSettings.feedHideGroupCompilations!==false;
appSettings.feedHideSoloCompilations=appSettings.feedHideSoloCompilations===true;
appSettings.feedHideExcerpts=appSettings.feedHideExcerpts!==false;
appSettings.searchHistoryLimit=boundedPreference(+appSettings.searchHistoryLimit,0,50,10);
appSettings.relatedLimit=boundedPreference(+appSettings.relatedLimit,0,60,20);
const METADATA_REFRESH_DAYS=[0,7,30,90];
appSettings.metadataRefreshDays=allowedSetting(+appSettings.metadataRefreshDays,METADATA_REFRESH_DAYS,30);
Object.assign(appSettings,normalizeJavPreferences(appSettings));
appSettings.theme=allowedSetting(appSettings.theme,THEME_CHOICES,'system');
appSettings.homeGlow=normalizeHomeGlow(appSettings.homeGlow);
appSettings.accent=normalizeAccent(appSettings.accent);
const sidebarKeyAlias=key=>key==='ads'||key==='dupes'?'data-cleanup':key;
appSettings.sidebarOrder=[...new Set((Array.isArray(appSettings.sidebarOrder)?appSettings.sidebarOrder:DEFAULT_SIDEBAR_ORDER).map(sidebarKeyAlias))].filter(key=>ALL_SIDEBAR_KEYS.includes(key));
if(!appSettings.sidebarOrder.length)appSettings.sidebarOrder=[...DEFAULT_SIDEBAR_ORDER];
document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);
/* 音效跟着偏好走。点击与开关那两声由 document 上的一对监听统一发；回执、菜单和弹层
   在各自的入口自己响。 */
setUiSoundsEnabled(appSettings.uiSounds);
wireUiSounds();
/* 这份对象的读写都在壳里原地改字段；落盘走 store，同一下通知开着的设置面板跟上
   （`frontend/src/settings-store.ts`）。 */
const settingsStore=createSettingsStore(SETTINGS_KEY,appSettings);
const saveSettings=()=>settingsStore.save();
if(sortDefaultsMigrated)saveSettings();
/* 主题只写属性，不写颜色：两套色板都在 web/css/01-base.css，选跟随系统就把属性摘掉，
   交还给 `prefers-color-scheme`。React 子树里的 BoardUI 源码把深色 token 挂在 `.dark` 上，
   所以同一次调用按实际深浅给 <html> 加减 `dark` 类，跟随系统时也算上系统那一档。
   地址栏色块跟着同一次调用走——两枚 meta 各代表一档，
   选中的那枚开到 `all`、另一枚关成 `not all`，否则手机上的地址栏还留在系统那一档。
   `index.html` 的首屏内联脚本做的是同三件事，它只负责第一帧，之后都从这里出。 */
const prefersDark=matchMedia('(prefers-color-scheme: dark)');
function applyTheme(choice=appSettings.theme){
  const root=document.documentElement;
  if(choice==='system')delete root.dataset.theme;else root.dataset.theme=choice;
  const dark=choice==='dark'||(choice==='system'&&prefersDark.matches);
  root.classList.toggle('dark',dark);
  document.querySelectorAll('[data-board-theme]').forEach(button=>button.setAttribute('aria-pressed',String((button.dataset.boardTheme==='dark')===dark)));
  document.querySelector('.board-theme-toggle')?.classList.toggle('is-dark',dark);
  document.querySelectorAll('meta[data-theme-color]').forEach(meta=>{
    meta.media=(meta.dataset.themeColor==='dark')===dark?'all':'not all';
  });
}
applyTheme();
prefersDark.addEventListener('change',()=>{if(appSettings.theme==='system')applyTheme()});
/* 光晕怎么算、怎么写都在 `./js/home-glow.js`：那一份不认识 appSettings，React 壳直接
   import 同一个文件。这里只负责把当前设置和 `.glowlayer` 那枚空 div 递进去。
   写的对象是那枚 div 而不是 <html>：自定义属性是继承的，写在根上整棵树都要重算样式，
   实测每帧 15ms 上下，拖动时帧预算当场就超；量法和数字记在 web/css/01-base.css 那条规则
   上面。
   一帧只写一次。指针拖动一秒能发上百个 pointermove，每一个都同步写变量的话，写进去的
   中间那几十份没有任何一帧画得出来，代价却照付。排进 requestAnimationFrame 之后，写的
   就是这一帧真正要画的那一份。 */
const glowField=document.querySelector('.glowlayer');
let glowFrame=0;
function applyHomeGlow(){
  if(glowFrame)return;
  glowFrame=requestAnimationFrame(()=>{glowFrame=0;paintHomeGlow(glowField,appSettings.homeGlow)});
}
/* 其余玻璃面（搜索框、顶栏图标钮、筛选浮层、设置卡的分区导航、媒体库与配色弹层、窄栏、
   选择工具条）分散在整棵树上，没有共同的宿主，它们那两团反光的色相只能写在根上。
   写一次根就是整棵树重算样式，所以这一条只接换档、点颜色和开关那几下；拖强度那条拉条
   走的是上面的 applyHomeGlow()，一次都不碰根。
   强调色同理：一次点选写一个属性，换来的是整页的按钮、焦点环和链接跟着走。 */
const glowRoot=document.documentElement;
function applyGlassFaces(){paintGlassFaces(glowRoot,appSettings.homeGlow)}
function applyAccent(){glowRoot.dataset.accent=appSettings.accent}
paintHomeGlow(glowField,appSettings.homeGlow);
applyGlassFaces();applyAccent();
/* 光晕预设色块在侧栏底部那枚配色钮和设置面板（`frontend/src/react/settings-panel/`）上各有
   一份，是同一组色块、同一份写入：两处读的都是 `appSettings.homeGlow`，都由下面这两个函数
   画和接，点哪一边另一边当场对齐。 */
/* 预设色块照 feralui 的预设 chip 做：三枚光晕色等分一圈 conic-gradient，再叠 BoardUI 那
   三层白色高光。「玻璃原色」那一格的球不带颜色：它画的是当前主题下玻璃自带的那两团
   反光，两个主题各一套，值只有样式表里一份，所以这里交出一个标记、由 CSS 去取。 */
const glowSpotColors=glow=>HOME_GLOW_SPOTS.map(key=>glow[key].color);
const glowChipHtml=(key,label,colors,chosen)=>`<button type="button" class="board-glow-chip" data-glow-preset="${key}"
  aria-pressed="${key===chosen}" title="${esc(label)}" aria-label="${esc(label)}"><span class="board-glow-ball"
  aria-hidden="true" ${isNativeGlass(key)?'data-glow-native':`style="--glow-chip:${glowChipFill(colors)}"`}></span></button>`;
const glowChipsHtml=()=>{
  const glow=appSettings.homeGlow;
  const chips=HOME_GLOW_PRESETS.map(([key,label,palette])=>
    glowChipHtml(key,label,HOME_GLOW_SPOTS.map(spot=>palette[spot].color),glow.preset));
  /* 「自定义」只有在用户真手调过颜色之后才占一格：没调过时那一格里是一份和默认档
     一模一样的球，点它什么也不会变，读起来却像还有一档没试过。 */
  if(glow.preset==='custom')chips.push(glowChipHtml('custom','自定义',glowSpotColors(glow),'custom'));
  return chips.join('');
};
/* 整格重画：「自定义」那一格会出现或消失。焦点正落在某一枚上时，画完落回同一档那一枚——
   键盘选完一档，焦点不该掉回页面开头。 */
function renderGlowPresetGrid(grid){
  const focused=grid.contains(document.activeElement)?document.activeElement.dataset.glowPreset:'';
  grid.innerHTML=glowChipsHtml();
  if(focused)grid.querySelector(`[data-glow-preset="${focused}"]`)?.focus();
}
/* 换一档光晕连强调色一起换：一档配色就是一副面，光晕暖着、按钮还是蓝的，读起来是两套
   皮叠在一起。侧栏卡下面那一排强调色可以单独点，点完只改强调色、不动光晕——先给一套
   搭配好的，要拆开也拆得开。
   一个监听接整格：那一排球会因为「自定义」出现或消失而重画，逐枚绑事件的话，重画之后
   绑的是上一批已经不在文档里的按钮。 */
function wireGlowPresetGrid(grid){
  grid.addEventListener('click',event=>{
    const chip=event.target.closest?.('[data-glow-preset]');
    if(!chip)return;
    const glow=appSettings.homeGlow,key=chip.dataset.glowPreset;
    if(key==='custom')return;
    glow.preset=key;Object.assign(glow,glowPalette(key));
    appSettings.accent=glowAccent(key);
    saveSettings();applyHomeGlow();applyGlassFaces();applyAccent();syncGlowChrome();
  });
}
/* 侧栏那枚配色钮由壳尾的装配段接上；接上之前这里是个空函数，首页第一帧就改光晕也不会炸。
   设置面板读的是同一份 `appSettings.homeGlow`，经 store 通知自己跟上。 */
let syncGlowSidebar=()=>{};
function syncGlowChrome(){syncGlowSidebar()}
/* 设置面板归 React 岛（`frontend/src/react/settings-panel/`）。岛只改 `appSettings` 的字段并落盘，
   改完用效果名告诉这里跟着做什么：重画网格、重取目录、换主题、重排侧栏都还是壳的事。 */
const settingsEffects={
  theme:()=>applyTheme(),
  /* 开这一格时立刻响一声开关音，人才知道它开了。关的那一声由 document 上的 change 监听
     发出：捕获阶段排在这里前面，那时开关还没关掉，最后一声还能响出来。 */
  uiSounds:()=>{setUiSoundsEnabled(appSettings.uiSounds);if(appSettings.uiSounds)playUiSound('toggle-on')},
  glowFrame:()=>applyHomeGlow(),
  glow:()=>{applyHomeGlow();applyGlassFaces();syncGlowSidebar()},
  batchSize:()=>{if(location.pathname==='/')loadCatalog()},
  defaultSort:()=>{
    state.sort=appSettings.defaultSort;
    state.dir=preferredDirection(state.sort,appSettings.defaultSort,appSettings.defaultSortDirection);
    if(location.pathname==='/')loadCatalog();
  },
  sortDirection:()=>{
    state.dir=preferredDirection(state.sort,appSettings.defaultSort,appSettings.defaultSortDirection);
    if(location.pathname==='/')loadCatalog();
  },
  hoverDelay:()=>{
    if(!appSettings.hoverDelaySeconds)document.querySelectorAll('[data-previewing],[data-longhover]')
      .forEach(el=>{setHoverState(el,'previewing',false);setHoverState(el,'longhover',false)});
    document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);
  },
  seekSeconds:()=>repaintCatalogGrid(),
  /* 折叠是在渲染时做的，不重取的话已经被跳过的那些卡不会自己冒出来。 */
  groupCollapse:()=>reloadCurrentSurface(),
  feedAutoScroll:()=>syncFeedAutoScroll(),
  feedCompilations:()=>refreshFeedRows(),
  /* 设置说的是「离开详情不再进小窗」，已经开着的那个小窗留着反而像没生效。 */
  miniplayer:()=>{if(!appSettings.miniplayer)stageApi()?.closeMiniplayer()},
  javImage:()=>{
    syncJavImages(document,appSettings.javImage);repaintCatalogGrid();
    document.querySelectorAll('img[data-jav-image].cover').forEach(coverAnchor);
    repaintDetailPoster();
  },
  searchHistoryLimit:()=>updateIsland($('#searchMenu'),{historyLimit:appSettings.searchHistoryLimit}),
  sidebarOrder:()=>{buildEdge();buildBars()},
};
/* 折射贴图由壳尾的装配段挂；设置面板左栏那块玻璃第一次进 DOM 时要它再扫一遍。 */
let syncGlassOptics=()=>{};
/* 来源图标：品牌使用已缓存的官方资产；通用操作图标统一使用本地 Lucide 子集。
   115 与 PikPak 都取 `MEDIA_SOURCE_ICONS` 里那份官方站标（取证
   follow-source-icons-measured.md）：来源角标、媒体库切换器和配置页问的是同一件事
   「这是哪个网盘」，同一个答案不该因为取图入口不同而长成两枚不一样的图形。 */
const SRCICON={
  local:icon('hard-drive'),
  '115':`<img class="source-icon" src="${MEDIA_SOURCE_ICONS['115']}" alt="">`,
  pikpak:`<img class="source-icon" src="${MEDIA_SOURCE_ICONS.pikpak}" alt="">`,
  online:icon('rss'),
};
const srcBadge=(loc,cost,cls)=>{const label=`${LOC[loc]||loc}${cost==='metered'?' · 计费':''}`;
  return `<span class="${cls||'src'} ${cost==='metered'?'metered':'free'}" title="${esc(label)}" aria-label="${esc(label)}">`
    +(SRCICON[loc]||'')+'</span>'};
/* 空态用 Vercel 的「icon tile + 标题 + 一句解释」结构。不放假动作按钮：
   能执行的操作仍然留在各页自己的工具栏里，空态只负责解释为什么是空的。 */
const emptyState=emptyStateHtml;
let runtimeConfigurable=null;

/* Toast：Sonner 的栈（`frontend/src/react/toaster.tsx`），挂在 #toasts（body 直下）而不是
   #stats 里——检查完会整页重画，页内浮层会被冲掉，这里不会。用法照 Geist 的处方（取证见
   docs/reference-snapshots/vercel-geist-toast.md）：只做用户主动动作的非阻塞回执，自动
   消失。回执可以带一个明确的后续动作（action.label + action.run）：光摆数字会让用户去找
   「哪里能点」，Geist 的做法是给一个具名的下一步。失败这类必须跟进的事只发一句短 toast，
   原因和恢复入口留在页面里的持久行上。 */
/* Toast 的正文只接 `{text}`（转义后插入）或 `{html}`（原样插入）。

   签名不接裸字符串：那样「这是文本还是 HTML」全靠调用点自己记得 `esc()`，而
   actionReceipt 传的是已经转义过的串、followCheckToast 传的是带 `<b>` 的片段，
   两者在签名上完全一样。真出问题的是那些内容来自账本的回执——
   `已删除标签「${tagLabel(tag)}」` 里的标签名是用户或刮削器写进账本的，含 `<`
   就直接被当成标签插进 DOM。谁是 HTML 由调用点显式声明，不再靠约定。 */
const toastBody=message=>message&&typeof message==='object'&&'html' in message
  ? String(message.html)
  : esc(message&&typeof message==='object'?(message.text??''):message??'');
/* 音效按通知表达的状态分三档：成功、警告、失败。默认由 `warn` 取成功或失败；事情
   做完了但有一部分要留意（几个来源失败、筛出来没有能放的）的传 `sound:'warning'`。 */
let toastSeq=0;
const toast=(message,{timeout=6000,warn=false,action=null,sound=null}={})=>{
  const id=`toast-${++toastSeq}`;
  const show=(body,alert,duration,next)=>{
    playUiSound(sound||(alert?'error':'success'));
    showToast($('#toasts'),{success:icon('check'),error:icon('circle-alert')},id,{html:body,alert:!!alert,timeout:duration,
      action:next&&!alert?{label:next.label,run:button=>{setActionBusy(button);next.run()}}:null});
  };
  show(toastBody(message),warn,timeout,action);
  /* 结果就写在同一条 toast 上（同一个 id）。「关掉回执 + 另发一条已撤销」会让两条在同一个
     底部对齐的栈里一进一出，看上去就是整块跳了一下。 */
  return {replaceMessage:(body,{warn:alert=false,timeout:next=4000}={})=>show(toastBody(body),alert,next,null)};
};
/* 教程卡和 Toast 都停在右下角。卡在屏幕上时，把 Toast 栈的底边抬到卡的上沿之上，回执不压在
   教程上；卡几乎占满一屏时（手机上展开那一版）不抬，免得回执被顶出视口，照旧盖在卡上面。
   位置写在 #toasts 自己身上：高频改的变量挂在 html 上会让整棵树重算样式。 */
const liftToastsOverTutorial=()=>{
  const card=$('#postSetupTutorial'),host=$('#toasts');
  const top=card.hidden?innerHeight:card.getBoundingClientRect().top;
  if(card.hidden||!card.offsetHeight||top<160)host.style.removeProperty('--toast-bottom');
  else host.style.setProperty('--toast-bottom',`${Math.round(innerHeight-top+12)}px`);
};
new ResizeObserver(liftToastsOverTutorial).observe($('#postSetupTutorial'));
addEventListener('resize',liftToastsOverTutorial);

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
/* 异或结果是有符号 32 位，先转无符号再取模：种子要写进地址，后端只认非负整数。 */
const newSeed=()=>String(((Date.now()^(Math.random()*1e9|0))>>>0)%99991);
const rollSeed=()=>newSeed();
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
const cleanTagFilter=value=>String(value||'').split(',').filter(tag=>tag&&!DURATION_TAGS.has(tag)).join(',');
const cleanSort=(value,fallback=appSettings.defaultSort)=>SORT_KEYS.includes(value)?value:fallback;
/* 列和方向一次解出来：旧键自带方向，`dir` 显式写了就听它的，随机没有方向。 */
function resolveSort(rawSort,rawDir,fallback=appSettings.defaultSort){
  const alias=SORT_ALIASES[rawSort];
  const sort=cleanSort(alias?alias[0]:rawSort,fallback);
  if(!SORT_DIR_WORDS[sort])return{sort,dir:''};
  return{sort,dir:rawDir==='asc'||rawDir==='desc'?rawDir:(alias?alias[1]:rawSort?'desc':preferredDirection(sort,appSettings.defaultSort,appSettings.defaultSortDirection))};
}
/* 查询参数属于它所在的路由，所以目录的筛选只从目录 URL 里读。

   不能无条件读启动 URL：`/follow?tag=blender` 会顺手把目录也筛成 blender，
   于是顶部画出「blender ✕ 全部清除」——一条目录筛选芯片挂在关注页上，回到首页
   还发现自己被筛住了。关注页的 `tag` 和目录的 `tag` 是两套词表（一个是 booru
   英文标签，一个是本地中文标签），撞在同一个键上只能靠路由分开。 */
const initialCatalogUrl=(path=>isCatalogPath(path)||path==='/trash')(
  decodeURIComponent(location.pathname));
const initialParam=key=>initialCatalogUrl?initialParams.get(key):null;
state={loc:initialParams.get('loc')??'local,115',creator:initialParam('creator')||'',studio:initialParam('studio')||'',
  owner:initialParam('owner')==='none'?'none':'',
  tag:cleanTagFilter(initialParam('tag')),len:initialParam('len')||'',dur_min:initialParam('dur_min')||'',dur_max:initialParam('dur_max')||'',
  tag_match:initialParam('tag_match')==='any'?'any':'all',orient:initialParam('orient')||'',
  region:initialParam('region')||'',
  state:ROUTE_STATES[decodeURIComponent(location.pathname)]||initialParam('state')||'',
  ...resolveSort(initialParam('sort'),initialParam('dir')),
  seed:initialParam('seed')||rollSeed(),q:initialParam('q')||'',jav:initialParam('jav')||'',thumb:initialParam('thumb')||'0'};
/* 脱盘的来源要从默认筛选里摘掉，否则首页照样按它筛，出来一屏点开就报脱盘的卡片。
   只动默认值：地址栏里显式写了 `loc=` 就是用户自己选的，不替他改。
   全部来源都脱盘时保持原样——清空筛选会变成「什么都不筛」，那比原状更糟。
   必须写在 `state` 之后：`loadSourceStatus()` 在启动时调它，那时 `state` 已初始化。 */
function dropOfflineFromDefaultLoc(){
  if(initialParams.has('loc'))return;
  state.loc=onlineDefaultLoc(state.loc);
}
function onlineDefaultLoc(loc){
  return loc.split(',').filter(Boolean).filter(k=>sourceOnline[k]!==false).join(',')||loc;
}
const HOME_QUERY_KEYS=['loc','creator','studio','owner','tag','tag_match','len','dur_min','dur_max','orient','region','sort','dir','q','jav'];
function homePath(filters=state){
  const path=STATE_ROUTES[filters.state]||'/';
  const params=new URLSearchParams();
  HOME_QUERY_KEYS.forEach(key=>{const value=filters[key];
    if(value&&!(key==='tag_match'&&value==='all')&&!(key==='dir'&&value===defaultSortDir(filters.sort)))params.set(key,value)});
  if(!STATE_ROUTES[filters.state]&&filters.state)params.set('state',filters.state);
  return path+(params.size?'?'+params:'');
}
/* 顶部三层与筛选条画的是哪一套筛选，由它说了算。声明必须排在 resetHomeState 之前：
   那个函数会把它拨回 home，而它是 let，用在声明之前就是 TDZ。 */
let barsContext={type:'home',filters:state},detailReturnBarsContext=null;
/* 所有明确的「回首页」动作必须得到同一个干净状态。只改地址为 `/` 不够：state.jav
   等内存筛选还会继续进入 /api/items，让页面看似首页却只剩 JAV。来源选择是用户的
   浏览范围，继续保留；其余分类、搜索和排序恢复首页默认值。
   barsContext 也在这里回到 home：从资料页点侧栏或左上角标志回首页时，loadCatalog()
   确实会把它拨回来，但 openHome 是先 buildBars() 后 loadCatalog()，buildBars 开头就把
   activeFilterState() 取走了——取到的是资料页那份筛选，它没有 state 这个键，
   于是四枚视图胶囊一枚都不亮，首页看上去像谁都没选中。 */
function resetHomeState(){
  state={loc:state.loc,creator:'',studio:'',owner:'',tag:'',tag_match:'all',len:'',dur_min:'',dur_max:'',
    orient:'',region:'',state:'',sort:appSettings.defaultSort,dir:preferredDirection(appSettings.defaultSort,appSettings.defaultSort,appSettings.defaultSortDirection),
    seed:rollSeed(),q:'',jav:'',thumb:'0'};
  barsContext={type:'home',filters:state};detailReturnBarsContext=null;
  barsDataCache=null;barsDataPromise=null;
}
/* 离开搜索结果时把搜索框一起清掉。框里的字不是瞬间没的：`dissolveValue` 先照着它此刻
   的位置摆一份同样的字飘上去糊掉，输入框当场就空了，回来的人看见的是一个空框加一段
   刚散掉的残影，而不是「刚才那句话去哪了」。 */
let searchValueSnapshot={text:'',scrollLeft:0};
let cancelSearchDissolve=()=>{};
const rememberSearchValue=(input=$('#q'))=>{
  searchValueSnapshot={text:input?.value||'',scrollLeft:input?.scrollLeft||0};
};
const clearSearchField=(snapshot=null)=>{
  const input=$('#q');if(!input)return;
  const liveSnapshot={text:input.value,scrollLeft:input.scrollLeft||0};
  const previous=snapshot||(liveSnapshot.text?liveSnapshot:searchValueSnapshot);
  cancelSearchDissolve();
  cancelSearchDissolve=dissolveValue(input,input.parentElement,previous);
  searchValueSnapshot={text:'',scrollLeft:0};
};
/* 「未归属」是全库那一类，不是当前这一页里的子筛选：在某位女优的资料页上再筛「没有
   署名人」永远是空的。所以它和打开资料页一样离开当前语境，回目录只留这一条筛选，
   顶栏芯片指的就是同一份列表。 */
function openUnowned(){
  resetHomeState();state.owner='none';
  clearSearchField();disposeStage(false);showHomeSurfaces();
  route(homePath());buildEdge();buildBars();loadCatalog();
  window.scrollTo({top:0,behavior:'smooth'});
}
/* 详情页那枚产地和未归属同一种东西：它标的不是一句说明，是馆藏里一个能筛的集合。 */
function openRegion(region){
  resetHomeState();state.region=region||'none';
  clearSearchField();disposeStage(false);showHomeSurfaces();
  route(homePath());buildEdge();buildBars();loadCatalog();
  window.scrollTo({top:0,behavior:'smooth'});
}
function openHome(scroll=false){
  resetHomeState();route('/');clearSearchField();disposeStage(false);showHomeSurfaces();
  buildEdge();buildBars();loadCatalog();
  if(scroll)window.scrollTo({top:0,behavior:'smooth'});
}
/* `onboarding=1` 来自设置完成页。标记会在 Peach 的每一页保持生效；清单只读真实接口，
   不用“访问过页面”冒充完成。地址栏里那一位一进门就擦掉——它只说明「这一次是从设置
   完成页进来的」，留在地址里会被收藏、被分享、被刷新时重放。口味页要知道这件事，
   所以它落在一个内存变量上，取一次就没了。 */
let cameFromSetup=new URLSearchParams(location.search).get('onboarding')==='1';
const claimSetupEntry=()=>{const came=cameFromSetup;cameFromSetup=false;return came};
/* 清单做完这件事跟着账本走（`/api/settings` 的 `postSetupTutorialDone`），本地的
   `pending` 只是这台设备上的镜像。null 表示还没问过服务端，问一次就够——页面活着的
   这段时间里改动它的只有我们自己。 */
let postSetupTutorialDone=null,postSetupTutorialNeedsReopen=false;
if(cameFromSetup){
  setPostSetupTutorialMarker('pending');
  // 账本里那句「教程做完了」可能是上一次安装留下的，刚走完设置就得撤回。
  postSetupTutorialDone=false;postSetupTutorialNeedsReopen=true;
  const clean=new URL(location.href);clean.searchParams.delete('onboarding');
  history.replaceState(history.state,'',clean.pathname+(clean.search||'')+clean.hash);
}
/* 界面标注工具（docs/FRONTEND.md「界面标注」）：`?agentation=on|off` 写这台设备的开关并从
   地址里去掉；开关开着才请求 `/dev/agentation.js`，没在本机构建过就是 404，静默不装。 */
{
  const clean=new URL(location.href),flag=clean.searchParams.get('agentation');
  if(flag==='on')localStorage.setItem('peach.agentation','on');
  if(flag==='off')localStorage.removeItem('peach.agentation');
  if(flag!==null){
    clean.searchParams.delete('agentation');
    history.replaceState(history.state,'',clean.pathname+(clean.search||'')+clean.hash);
  }
  if(localStorage.getItem('peach.agentation')==='on')import('/dev/agentation.js').catch(()=>{});
}
const postSetupTutorialTasks=async()=>{
  const {library,scraping,taste,follow,credentials,review}=await api('/api/post-setup-tutorial');
  const scrapingCredentialSources=(scraping.sources||[]).filter(source=>source.accepts_cookie);
  const savedScrapingCredentials=scrapingCredentialSources.filter(source=>source.cookie_saved);
  const sources=(follow.sources||[]).filter(source=>source.enabled!==false);
  const providers=new Map((credentials.providers||[]).map(row=>[row.provider,row]));
  const required=[...new Set(sources.map(source=>source.provider))]
    .map(provider=>providers.get(provider)).filter(row=>row?.requirement==='required');
  const libraryReady=Number(library.total||0)>0;
  const followReady=sources.length>0;
  const credentialsReady=followReady&&required.every(row=>row.present&&!row.missing?.length);
  const pendingReview=Object.values(review.counts||{})
    .reduce((sum,value)=>sum+(Number(value)||0),0);
  return [
    {key:'library',label:'完成首次扫描',description:libraryReady
      ?`已经导入 ${Number(library.total).toLocaleString()} 项馆藏。`:'等待扫描导入第一项馆藏。',
      href:'/data-cleanup',done:libraryReady,icon:'scan-search'},
    {key:'scraping',label:'设置采集来源与凭证',description:savedScrapingCredentials.length
      ?`已为 ${savedScrapingCredentials.length.toLocaleString()} 个采集来源保存凭证。`
      :'检查来源连接方式，并为需要登录的来源保存凭证。',
      href:'/scraping',done:savedScrapingCredentials.length>0,icon:'settings'},
    {key:'history',label:'导入浏览器历史记录',description:Number(taste.history_sources||0)>0
      ?`已导入 ${Number(taste.history_sources).toLocaleString()} 份浏览器历史。`
      :'从这台电脑的浏览器导入口味分析记录。',
      href:'/taste',setupEntry:true,done:Number(taste.history_sources||0)>0,icon:'history'},
    {key:'follow',label:'添加一个关注来源',description:followReady
      ?`已启用 ${sources.length.toLocaleString()} 个来源。`:'添加想持续追踪的创作者或来源。',
      href:'/follow-manage?tab=add',done:followReady,icon:'rss'},
    {key:'credentials',label:'补齐关注来源凭证',description:!followReady
      ?'添加关注后，会按来源检查必要凭证。':required.length
        ?(credentialsReady?'已配置当前来源需要的凭证。':`${required.length.toLocaleString()} 个来源需要凭证。`)
        :'当前关注来源不需要凭证。',
      href:'/follow-manage?tab=source',done:credentialsReady,icon:'key-round'},
    {key:'review',label:'处理首次复核',description:!libraryReady
      ?'扫描完成后，这里会列出需要复核的资料。':pendingReview
        ?`还有 ${pendingReview.toLocaleString()} 条需要复核。`:'首次复核队列已清空。',
      href:'/review',done:libraryReady&&pendingReview===0,icon:'square-check-big'},
  ];
};
const postSetupTutorialHtml=(tasks,skippedCount,totalCount)=>{
  const ordered=[...tasks].sort((left,right)=>Number(left.done)-Number(right.done));
  const next=tasks.find(task=>!task.done);
  const completeCount=tasks.filter(task=>task.done).length+skippedCount;
  const collapsed=postSetupTutorialCollapsed();
  const rows=ordered.map(task=>`<li class="post-setup-task" data-state="${task.done?'checked':'unchecked'}">
    <a href="${task.href}" data-tutorial-task="${task.key}">
      <span class="post-setup-check" aria-hidden="true">${task.done?icon('check'):icon(task.icon)}</span>
      <span><b>${task.label}</b><small>${task.description}</small></span>
      ${icon('chevron-right')}</a>
    ${task.done?'':`<button class="post-setup-skip" type="button" data-tutorial-skip="${task.key}" data-tutorial-label="${task.label}">跳过</button>`}
    </li>`).join('');
  return `<article class="post-setup-notification" data-collapsed="${collapsed}">
      <header class="post-setup-notification-head">
        <span class="post-setup-notification-icon" aria-hidden="true">${icon('compass')}</span>
        <div><h2>完成 Peach 的安装教程</h2>
        <p>已处理 ${completeCount}/${totalCount} 项。</p></div>
        <button class="post-setup-collapse" type="button" data-tutorial-collapse aria-controls="postSetupTaskList" aria-expanded="${!collapsed}"
          aria-label="${collapsed?'展开安装教程':'折叠安装教程'}">${icon(collapsed?'chevron-up':'chevron-down')}</button>
      </header>
      <ol class="post-setup-task-list" id="postSetupTaskList">${rows}</ol>
      <footer><button class="geist-button" type="button" data-tutorial-action="next">继续：${next.label}</button></footer>
    </article>`;
};
const writePostSetupTutorialDone=async done=>{
  postSetupTutorialDone=done;
  await api('/api/settings',{method:'POST',body:JSON.stringify({postSetupTutorialDone:done})});
};
const readPostSetupTutorialDone=async()=>{
  if(postSetupTutorialDone===null){
    try{postSetupTutorialDone=(await api('/api/settings')).postSetupTutorialDone===true}
    catch(_error){postSetupTutorialDone=false}
  }
  return postSetupTutorialDone;
};
/* 教程自己的跳转不走整页刷新：那张卡是常驻的，刷新一次要重来一遍取数和动画，
   刚点开的折叠也没了。口味页的导入指南要知道这一步是教程带过去的。 */
const openTutorialTarget=task=>{
  if(task.setupEntry)cameFromSetup=true;
  route(task.href);void restoreRoute();
};
/** 重新打开安装教程：本地三个键归位，服务端标记同时撤回。
 *  重开键在配置页的「更新与维护」里，忙态、失败原因和回执都由那一侧给；教程卡是固定定位的，
 *  在配置页上就露出来。写入失败就把原因抛回去。 */
async function reopenPostSetupTutorial(){
  resetPostSetupTutorialState();
  await writePostSetupTutorialDone(false);
  await syncPostSetupTutorial();
}
async function syncPostSetupTutorial(){
  const root=$('#postSetupTutorial');if(!root)return;
  const hide=()=>{root.hidden=true;root.innerHTML='';delete root.dataset.tutorialSignature;
    root.removeAttribute('aria-busy')};
  if(postSetupTutorialNeedsReopen){
    postSetupTutorialNeedsReopen=false;
    await writePostSetupTutorialDone(false).catch(()=>{});
  }
  if(postSetupTutorialMarker()!=='pending'||await readPostSetupTutorialDone()){hide();return}
  const request=nextPostSetupTutorialRequest();root.hidden=false;root.setAttribute('aria-busy','true');
  if(!root.firstElementChild){
    root.innerHTML=`<article class="post-setup-notification post-setup-loading">${icon('compass')}<p>正在检查安装进度…</p></article>`;
  }
  try{
    const tasks=await postSetupTutorialTasks();
    if(!isCurrentPostSetupTutorialRequest(request))return;
    const knownKeys=new Set(tasks.map(task=>task.key));
    const skipped=new Set([...postSetupTutorialSkipped()].filter(key=>knownKeys.has(key)));
    setPostSetupTutorialSkipped(skipped);
    const visible=tasks.filter(task=>!skipped.has(task.key));
    const pending=visible.filter(task=>!task.done);
    if(!pending.length){
      setPostSetupTutorialMarker('complete');hide();
      await writePostSetupTutorialDone(true).catch(()=>{});
      return
    }
    const signature=postSetupTutorialSignature(visible);
    if(root.dataset.tutorialSignature===signature){root.removeAttribute('aria-busy');return}
    root.innerHTML=postSetupTutorialHtml(visible,skipped.size,tasks.length);
    root.dataset.tutorialSignature=signature;root.removeAttribute('aria-busy');
    const next=pending[0];
    const collapse=root.querySelector('[data-tutorial-collapse]');
    collapse.onclick=()=>{
      const card=root.querySelector('.post-setup-notification');
      const collapsed=card.dataset.collapsed!=='true';
      card.dataset.collapsed=String(collapsed);setPostSetupTutorialCollapsed(collapsed);
      collapse.setAttribute('aria-expanded',String(!collapsed));
      collapse.setAttribute('aria-label',collapsed?'展开安装教程':'折叠安装教程');
      collapse.innerHTML=icon(collapsed?'chevron-up':'chevron-down');
    };
    root.querySelectorAll('[data-tutorial-skip]').forEach(button=>button.onclick=()=>{
      const skippedNow=postSetupTutorialSkipped(),key=button.dataset.tutorialSkip;
      skippedNow.add(key);setPostSetupTutorialSkipped(skippedNow);
      actionReceipt(`已跳过「${button.dataset.tutorialLabel}」`,{undo:async()=>{
        const restored=postSetupTutorialSkipped();restored.delete(key);setPostSetupTutorialSkipped(restored);
        setPostSetupTutorialMarker('pending');await syncPostSetupTutorial();
      }});
      void syncPostSetupTutorial();
    });
    const byKey=new Map(visible.map(task=>[task.key,task]));
    root.querySelectorAll('[data-tutorial-task]').forEach(link=>link.onclick=event=>{
      const task=byKey.get(link.dataset.tutorialTask);
      if(!task||event.metaKey||event.ctrlKey||event.shiftKey||event.button)return;
      event.preventDefault();openTutorialTarget(task);
    });
    root.querySelector('[data-tutorial-action]').onclick=()=>openTutorialTarget(next);
  }catch(_error){
    if(!isCurrentPostSetupTutorialRequest(request))return;
    /* 取数失败时这张卡是死的：没有清单，也没有下一步。给一条重试和一个关闭，
       不然它只能一直杵在右下角占着地方。 */
    root.innerHTML=`<article class="post-setup-notification post-setup-error">${icon('alert')}
      <div><h2>暂时无法检查安装进度</h2><p>切换页面或重新打开后会再检查一次。</p>
      <div class="post-setup-error-actions"><button class="geist-button" type="button" data-tutorial-retry>重试</button>
      <button class="geist-button" type="button" data-tutorial-dismiss>关闭</button></div></div></article>`;
    root.removeAttribute('aria-busy');
    root.querySelector('[data-tutorial-retry]').onclick=()=>{
      delete root.dataset.tutorialSignature;root.innerHTML='';void syncPostSetupTutorial();
    };
    root.querySelector('[data-tutorial-dismiss]').onclick=hide;
  }
}
const ENTITY_FILTER_KEYS=['loc','creator','tag','state','dur_min','dur_max','orient','sort','dir'];
const emptyEntityFilters=()=>Object.fromEntries(
  ENTITY_FILTER_KEYS.map(key=>[key,key==='sort'?'new':key==='dir'?'desc':'']));
const parseEntityFilters=search=>{const params=new URLSearchParams(search),filters=emptyEntityFilters();
  ENTITY_FILTER_KEYS.forEach(key=>{if(key!=='sort'&&key!=='dir')filters[key]=params.get(key)||''});
  Object.assign(filters,resolveSort(params.get('sort'),params.get('dir'),'new'));return filters};
const entityFilterSearch=filters=>{const params=new URLSearchParams();
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&!(key==='sort'&&filters[key]==='new')
    &&!(key==='dir'&&filters[key]===defaultSortDir(filters.sort)))params.set(key,filters[key])});
  return params.toString()};
const cloneBarsContext=context=>context&&context.type==='entity'
  ? {...context,filters:{...context.filters}}:context;
const activeFilterState=()=>barsContext.type==='home'?state:barsContext.filters;
$('#q').value=state.q;rememberSearchValue();
const REP={};   // 创作者/厂牌 → 代表作 id，用来做圆头像（裁接触印相中心格，不另造图）
/* `activeQueue` 是此刻开着的队列（`{kind, seedId|playlistId}`），只用来判「是不是同一个队列里换
   一条」；队列的条目归详情岛。`pendingQueueRoute` 是队列地址的前缀：停在哪一条要等岛定下来，
   画出来那一刻（`present`）才推。 */
let total=0,facets=null,detailReturnPath='/',activeQueue=null,pendingQueueRoute=null,presentedItem=null;
let detailOriginAnchor=null,detailOriginAbove=false,detailReturnNeedsRestore=false;
const CACHE={};
const cache=items=>{items.forEach(x=>CACHE[x.id]=x);return items};
/* ── 详情舞台（`frontend/src/react/stage/`）──
   浮窗、进出场、骨架、两座详情、播放器与小窗都归舞台岛，壳只留来处（`detailReturnPath`、
   `followDetailReturnPath`、`detailOriginAnchor`）与命令式入口。舞台岛所在的 React 包在第一次
   打开详情时才装载，之前 `stageApi()` 是 null：那时舞台没开，小窗也不在。 */
const stageHost={
  player:{
    settings:()=>appSettings,saveSettings:()=>saveSettings(),
    toast:(text,options)=>toast({text},options),
    loadSourceStatus:()=>loadSourceStatus(),offlineReason:key=>offlineReason(key),
    posterUrl:it=>detailPosterUrl(it),
  },
  sourceOffline:key=>sourceOffline(key),
  /* 小窗里的「展开」：同一个播放器搬回这一条的详情，地址与来处照点卡片进来的那一条走。 */
  expand:(kind,id,mediaIndex)=>{if(kind==='follow')void openFollowDetail(id,true,mediaIndex);else void openItem(id,true)},
  openItem:id=>void openItem(id),
  cache:it=>{CACHE[it.id]=it},
  release:el=>releaseHoverPreviews(el),
};
const stageOpen=()=>!!stageApi()?.isOpen();
/* 深链带 `?t=`：第一次挂上这一条时从这一刻接着放。 */
function urlResume(){
  const seconds=Number(new URLSearchParams(location.search).get('t'));
  return Number.isFinite(seconds)&&seconds>0?{time:seconds,autoplay:false}:null;
}
function stageExit(){return stageApi()?.exit()||Promise.resolve()}
/* 离开详情。正在放的视频默认进小窗接着放；显式关闭（叉、Escape）、换成别的详情和删掉当前条目
   都传 miniplayer:false。 */
function disposeStage(push=false,preserveInlineOrigin=false,{miniplayer=true}={}){
  stageApi()?.dispose({miniplayer});
  activeQueue=null;pendingQueueRoute=null;presentedItem=null;
  if(!preserveInlineOrigin){
    detailOriginAnchor=null;detailOriginAbove=false;detailReturnNeedsRestore=false;
  }
  scheduleStickySurfaces();
  if(push)route(detailReturnPath||'/');
}
/* 换「JAV 默认封面」时，开着的作品详情把海报位跟同一张图一起换。 */
function repaintDetailPoster(){stageApi()?.repaintPoster()}
let selectMode=false,lastSelectedId=null,followLastSelectedId=null,selectSurface='';
const currentSelectSurface=()=>location.pathname==='/follow'?'follow':location.pathname==='/junk-files'?'junk':'catalog';
function paintSelection(){
  // 卡片网格、垃圾队列与关注页的选中态归 React：每次推一份新的集合，卡片按引用比较才看得出变了。
  gridIslandHosts().forEach(host=>updateIsland(host,{selected:new Set(selected),selectMode}));
  pushFollowFeed({selected:new Set(followSelected),selectMode});
  const followPage=location.pathname==='/follow',junkPage=location.pathname==='/junk-files';
  const picked=followPage?followSelected:selected;
  $('#batchbar').hidden=!picked.size;$('#batchCount').textContent=`已选 ${picked.size} 项`;
  $('#batchbar').querySelectorAll('[data-batch]').forEach(button=>button.hidden=followPage||junkPage);
  $('#batchbar').querySelectorAll('[data-follow-batch]').forEach(button=>button.hidden=!followPage);
  $('#batchbar').querySelectorAll('[data-trash-only]').forEach(button=>button.hidden=followPage||junkPage||state.state!=='trash');
  $('#batchbar').querySelectorAll('[data-batch="like"],[data-batch="seen"],[data-batch="later"],[data-batch="dispose"],[data-batch-region]').forEach(button=>button.hidden=followPage||junkPage||state.state==='trash');
  const junkView=junkRoute(location.search).view;
  $('#batchbar').querySelectorAll('[data-junk-batch]').forEach(button=>{
    const operation=button.dataset.junkBatch;
    button.hidden=!junkPage||(operation==='dismiss-junk'&&junkView==='dismissed')
      ||(operation==='reconsider-junk'&&junkView!=='dismissed');
  });
}
/* 标签页的多选归 React 页面自己记：键在壳里，所以开关一变就推给正挂着的那一页，关掉时
   页面随之清空所选。别的页面上没有挂着的索引页，`updateIsland` 是空操作。 */
function setSelectMode(on,clear=false){
  if(on&&!selectMode)selectSurface=currentSelectSurface();
  selectMode=!!on;if(!selectMode)selectSurface='';document.body.classList.toggle('select-mode',selectMode);
  if(selectMode)releaseHoverPreviews();
  $('#selectMode').setAttribute('aria-pressed',selectMode);if(clear){selected.clear();followSelected.clear();lastSelectedId=null;followLastSelectedId=null}paintSelection();
  if(location.pathname==='/tags')updateIsland($('#index'),{selectMode})}
/* 只取网格直属卡片：竖屏条是嵌在网格里的横向滚动条，不该被 Shift 范围选中顺带框进来。 */
function visibleCardIds(){return [...gridCards()].map(card=>+card.dataset.id)}
function toggleSelection(id,range=false){
  lastSelectedId=selectRange(selected,visibleCardIds(),lastSelectedId,id,range);setSelectMode(true);paintSelection();
}
function visibleFollowIds(){return [...document.querySelectorAll('[data-follow-list] > [data-follow-item]')]
  .map(card=>+card.dataset.followItem)}
function toggleFollowSelection(id,range=false){
  followLastSelectedId=selectRange(followSelected,visibleFollowIds(),followLastSelectedId,id,range);setSelectMode(true);paintSelection();
}
$('#selectMode').onclick=()=>setSelectMode(!selectMode,!selectMode?false:true);
$('#batchClear').onclick=()=>setSelectMode(false,true);
$('#batchbar').querySelectorAll('[data-batch]').forEach(button=>button.onclick=async()=>{
  const labels={like:'喜欢',seen:'标为看过',later:'加入稍后看',dispose:'移入回收站',restore:'还原',delete:'彻底删除'};
  const titles={like:'喜欢所选项目',seen:'标记为已看',later:'加入稍后看',dispose:'移入回收站',restore:'还原所选项目',delete:'永久删除所选项目'};
  const operation=button.dataset.batch,ids=[...selected];if(!ids.length)return;
  return confirmModal({title:titles[operation],body:`将处理选中的 ${ids.length} 项。${operation==='delete'?'文件和馆藏记录会永久删除，无法恢复。':operation==='dispose'?'馆藏记录可在回收站还原。':''}`,confirmLabel:titles[operation],danger:operation==='delete',onConfirm:async()=>{
  setActionBusy(button);
  try{const r=await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation})});
    if(r.blocked&&r.blocked.length)throw new Error(`已永久删除 ${r.purged} 项；${r.blocked.length} 项未能删除，仍在回收站：\n`
      +r.blocked.slice(0,5).map(x=>`${x.path}（${x.reason}）`).join('\n'));
    setSelectMode(false,true);await reloadCurrentSurface();
    const inverse=operation==='dispose'?'restore':operation==='restore'?'dispose':null;
    actionReceipt(`已${labels[operation]} ${ids.length} 项`,{undo:inverse?async()=>{
      await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation:inverse})});
      await reloadCurrentSurface();
    }:null})}
  catch(error){setActionBusy(button,false);throw error}
  finally{setActionBusy(button,false);paintSelection()}
  }});
});
/* 产地是选中这一批的共同判断，不是逐条编辑，所以入口和「喜欢」「看过」并列在选择栏。
   药丸做单选：筛选面板里的产地已经是这个样子，弹层里换一套控件只会让人重新认一遍。
   「撤回判定」和那四类并列——加了「进入某状态」就得有「退出」，否则判错的片只能改成
   另一个错的产地，回不到未判定。 */
const REGION_CHOICES=[['jp','日本'],['kr','韩国'],['cn','国产'],['west','欧美'],
  ['other','其他'],['none','撤回判定']];
$('#batchbar').querySelector('[data-batch-region]').onclick=async()=>{
  const ids=[...selected];if(!ids.length)return;
  const modal=formModal({
    title:'判定产地',
    description:`选中的 ${ids.length} 项归为同一个产地。判定之后，刮削和自动推断不再改写产地。`,
    body:`<div class="chips" role="group" aria-label="产地">`+REGION_CHOICES.map(([key,label])=>
      `<button type="button" class="chip" aria-pressed="false" data-region-pick="${key}">
        <span class="chip-label">${label}</span></button>`).join('')+`</div>`,
    confirmLabel:'判定产地',
    confirmDisabled:true,
    onConfirm:async()=>{
      const picked=modal.dialog.querySelector('[data-region-pick][aria-pressed="true"]');
      if(!picked)throw new Error('先选一个产地');
      await api('/api/batch',{method:'POST',
        body:JSON.stringify({ids,operation:'region',region:picked.dataset.regionPick})});
      return {region:picked.dataset.regionPick,label:picked.textContent.trim()};
    }});
  modal.dialog.querySelectorAll('[data-region-pick]').forEach(chip=>chip.onclick=()=>{
    modal.dialog.querySelectorAll('[data-region-pick]').forEach(other=>
      other.setAttribute('aria-pressed',String(other===chip)));
    modal.confirmButton.disabled=false;
  });
  const {confirmed,result}=await modal.done;
  if(!confirmed)return;
  setSelectMode(false,true);await reloadCurrentSurface();
  actionReceipt(result.region==='none'
    ? `已撤回 ${ids.length} 项的产地判定` : `已判为${result.label}：${ids.length} 项`);
};
$('#batchbar').querySelectorAll('[data-follow-batch]').forEach(button=>button.onclick=async()=>{
  const action=button.dataset.followBatch,items=[...followSelected];if(!items.length)return;
  const labels={save:'保存到账本',seen:'标记已看',ignored:'忽略'};
  const titles={save:'保存所选作品',seen:'标记为已看',ignored:'忽略所选作品'};
  return confirmModal({title:titles[action],body:`将处理选中的 ${items.length} 项关注作品。`,confirmLabel:titles[action],danger:false,onConfirm:async()=>{
  setActionBusy(button);
  try{
    const path=action==='save'?'/api/follow/save':'/api/follow/status';
    const body=action==='save'?{items}:{items,to:action};
    await api(path,{method:'POST',body:JSON.stringify(body)});
    setSelectMode(false,true);await openFollow(false);actionReceipt(`已${labels[action]} ${items.length} 项`);
  }catch(error){setActionBusy(button,false);throw error}
  finally{setActionBusy(button,false);paintSelection()}
  }});
});
$('#batchbar').querySelectorAll('[data-junk-batch]').forEach(button=>button.onclick=async()=>{
  const operation=button.dataset.junkBatch,ids=[...selected];if(!ids.length)return;
  const labels={'dismiss-junk':'不是垃圾','reconsider-junk':'重新判断',dispose:'移入回收站'};
  const titles={'dismiss-junk':'标记为非垃圾','reconsider-junk':'重新检查文件',dispose:'移入回收站'};
  return confirmModal({title:titles[operation],body:`将处理选中的 ${ids.length} 个文件。`,confirmLabel:titles[operation],danger:false,onConfirm:async()=>{
  setActionBusy(button);
  try{
    await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation})});
    setSelectMode(false,true);await loadCatalog();
    const inverse=operation==='dispose'?'restore':operation==='dismiss-junk'?'reconsider-junk':
      operation==='reconsider-junk'?'dismiss-junk':null;
    actionReceipt(`已批量${labels[operation]}：${ids.length} 项`,{undo:inverse?async()=>{
      await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation:inverse})});
      await loadCatalog();
    }:null});
  }catch(error){setActionBusy(button,false);throw error}
  finally{setActionBusy(button,false);paintSelection()}
  }});
});

/* 密度：大图为主，密集为辅 */
const TILES={big:'336px',dense:'168px'};   /* 168px 模块单位 */
let density=localStorage.getItem('density')||'big';
/* 顶栏这颗键和筛选框里的版式开关问同一件事「现在是哪种排法」，所以字形也取同一份
   映射（PHOTO_SIZES 的第三位），按下去跟着换成当前状态的图标。 */
function syncDensityIcon(size){
  const button=$('#density');if(!button)return;
  const [big,small]=PHOTO_SIZES;
  if(!button.querySelector('[data-icon-swap]')){
    button.innerHTML=iconSwapHtml(big[2],small[2],size===small[0]?'b':'a');
  }else setIconSwap(button,size===small[0]?'b':'a');
  button.setAttribute('aria-label',size==='big'?'切换为小图':'切换为大图')}
function applyDensity(){document.documentElement.style.setProperty('--tile',TILES[density]);
  document.body.dataset.density=density;
  $('#density').setAttribute('aria-pressed',density==='dense');
  $('#density').title='当前：'+(density==='big'?'大图':'密集');
  syncDensityIcon(density==='big'?'big':'small')}
$('#density').onclick=()=>{if(photoViewActive()){
    setPhotoSize(photoSize()==='big'?'small':'big');return}
  density=density==='big'?'dense':'big';
  localStorage.setItem('density',density);applyDensity()};
applyDensity();

/* ── 悬停预览：只有本地文件拉真视频。
   115 / PikPak 等远端源只扫本地接触印相，避免页面移除后继续下载或填满缓存。 ── */
/* 卡片有两种：壳拼的 `.card`，和 React 网格里的 `[data-media-card]`／`[data-mix-card]`。 */
const HOVER_CARDS='.card,[data-media-card],[data-mix-card]';
function releaseHoverPreviews(root=document,except=null){
  if(!root||!root.querySelectorAll)return;
  root.querySelectorAll(HOVER_CARDS).forEach(card=>{
    if(card!==except&&card._stopHover)card._stopHover()});
  root.querySelectorAll('video.hv').forEach(v=>{
    if(v.closest(HOVER_CARDS)===except)return;
    if(v._hop)clearInterval(v._hop);v.pause();v.removeAttribute('src');v.load();v.remove()});
  // 远端源那一层和视频同样要兜一遍：卡片被重画过的话，旧元素上的 `_stopHover`
  // 已经跟着旧 DOM 走了，只靠上面那轮回调收不到它留在画面上的扫视图。
  root.querySelectorAll('img.hvframes').forEach(im=>{
    if(im.closest(HOVER_CARDS)===except)return;
    im.removeAttribute('src');im.remove()});
}
/* 悬停态写在卡上的 `data-previewing`／`data-longhover`：卡的类名归 React 管，壳不往上加。 */
function setHoverState(el,name,on){if(on)el.dataset[name]='';else delete el.dataset[name]}
function wireHover(el,it){
  const pic=el.querySelector('[data-media-pic]'); if(!pic)return;
  el.dataset.hoverMode=it.location==='local'?'video':'frames';
  let longTimer=null;
  const armLong=()=>{clearTimeout(longTimer);if(!appSettings.hoverDelaySeconds)return;setHoverState(el,'previewing',true);longTimer=setTimeout(()=>{if(appSettings.hoverDelaySeconds)setHoverState(el,'longhover',true)},appSettings.hoverDelaySeconds*1000)};
  const clearLong=()=>{clearTimeout(longTimer);setHoverState(el,'previewing',false);setHoverState(el,'longhover',false)};
  if(it.location!=='local'){        // 远端源：只在接触印相的格子间扫视，零网络流量
    /* 扫视图是叠在画面之上新建的一层，不改任何已有 `<img>` 的 src。JAV 大图和小图
       版式里画面就是封面本身（`.poster.cover`），改它的 src 等于把封面当场换掉；
       按类名把封面排掉又等于这两种版式整个没有悬停预览，连 `data-longhover` 都不进，
       快退快进那三颗也跟着永远不出现。叠一层对三种版式是同一条路。
       这一层用 contain 加黑底：大图版式的容器是 0.75 的竖比例，16:9 的接触印相格子
       在里面居中、上下留黑，和本地视频的 `.hv` 同一个口径。 */
    if(!it.has_thumb)return;        // 没有接触印相就没有可扫的格子
    let t=null,i=4,layer=null,loading=false;
    el.addEventListener('mouseenter',()=>{
      if(selectMode||censorOn())return;armLong();
      if(!layer){
        layer=document.createElement('img');
        layer.className='hvframes';layer.alt='';
        layer.src=`/poster?id=${it.id}&c=${i}`;
        pic.appendChild(layer);
      }
      clearInterval(t);
      t=setInterval(()=>{
        if(!layer||loading)return;
        const next=(i+1)%9, pre=new Image(); loading=true;
        pre.onload=()=>{if(layer){layer.src=pre.src;i=next}loading=false};
        pre.onerror=()=>{loading=false};
        pre.src=`/poster?id=${it.id}&c=${next}`;
      },430);
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
        seek(); v.classList.add('on');v.dataset.playing='';armLong();
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
/* `thumb` 要的是实体图缩到长边 640 的那一份。开给一屏几十格的位置用：实体图是给
   资料页大位存的照片，本库 727 张均 221 KB，索引页一屏 120 格铺进 150 px 的格子就是
   十几 MB，而屏幕上用得着的只有其中百分之几的像素。资料页仍取原件——那里就是要看清。 */
function entityFaceImg({kind='performer',id=null,hasImage=false,rep=null,mark=null,logo='',
                        logoVariant='logo',alt='',lazy=true,style='',dropStyle=false,
                        focus=null,thumb=false}={}){
  const useEntity=!!(id&&hasImage);
  const entitySrc=useEntity?`/entity-image?kind=${kind}&id=${id}${thumb?'&thumb=1':''}`:'';
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
  const faceBox=framed?faceBoxAttrs(focus):'';
  /* 挪和放大是同一份 sidecar 的两半，这里替调用点把挪那一半补上：给了 `focus` 却
     没给 `style` 的，按同一个换算自己算。分开传时漏掉 `style` 不会报错也看不出来
     ——图照样出，只是几何居中，脸落在画面顶上的那些正好被裁掉脑袋。 */
  const framedStyle=style||facePos(focus);
  /* 贴了脸框就一定要能撤 style：放大是 avatarFrame 写进 img 内联 style 的，回落时
     不撤，那几个百分比会按上一张图的尺寸套在这一张上。调用点不必记得开这个开关——
     忘了开的代价是页面上一张明显错位的图，而它只在回落发生时才现形。 */
  /* `decoding="async"` 让解码离开主线程：一屏几十张图同时落地时，同步解码把滚动
     和点击一起压住，而这些图一张都不参与首屏的排版——框的尺寸由 CSS 定死。 */
  return `<img src="${src}" alt="${alt}"${lazy?' loading="lazy"':''} decoding="async"${framed?framedStyle:''} `+
    `${faceBox}${imageFallbackAttrs({dropStyle:(dropStyle||!!faceBox||!!framedStyle)&&framed,
                                     fallbacks})}>`;
}
/* 头像内层：先垫首字母，再叠真实图。

   `has_image` 缺席按「没图」处理，和 entityFaceImg 的默认值一致：每一个调用点的
   ref 都由服务端带着标志下发（卡片署名、索引页、口味榜、复核卡片、沉浸模式），
   宽容缺席只会让下一个忘了挂标志的端点悄悄退回「无条件出图、等 404 再摘」。

   取景反过来：不传就从 ref 上取。它和 `has_image` 出自同一份下发，分开传的代价是
   七个调用点要各记一次，而漏掉不报错也不掉图，只是几何居中——这种错只有对着页面
   一个个看才发现得了。公司那一格要的是「明确不取景」，传 `null` 覆盖掉。 */
function avatarInner(name,ref,repId,kind='performer',markId=null,logoName='',logoVariant='icon',
                     focus=undefined,thumb=false){
  // 这一层大多是小圆框和窄格子，厂牌标识在那里要方形图标而不是横着的字标；索引页的
  // 厂牌大格是同一个模板里的例外，由调用方点名要 `large`。
  const hint=focus===undefined?(ref&&ref.avatar_focus)||null:focus;
  return `<span class="ini">${esc((name||'?').slice(0,1))}</span>`+
    entityFaceImg({kind,id:ref&&ref.id,hasImage:!!(ref&&ref.has_image),rep:repId,mark:markId,
                   logo:logoName,logoVariant,focus:hint,thumb});
}
/* 人脸取景：资料页圆框按检出的人脸中心取景（/api/entity 的 avatar_focus）。
   没检出或没算过返回空串维持几何居中；换回落图时必须撤掉——那是另一张照片，
   脸不在同一位置，见资料卡大位那张图的 `data-drop-style`。 */
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
/* 人脸放大：把脸框的像素尺寸交给页面，倍数在图加载后按框的真实尺寸算。

   只挪解决不了「脸太小」——cover 的缩放由框和图的比例定死，脸在图里占多少，在框里
   就占多少。539 张里有 29 张是全身站姿照，脸落在画面上半截的一小块里，挪到正中依旧
   是一颗认不出是谁的头。放大倍数由 `web/js/face-frame.js` 夹在「够看清」「不上采样」
   「不切头」三条之间，服务端算不了：它不知道这个框有多大、这块屏幕几倍像素。

   属性而不是 style：倍数得等图和框都落地才算得出来，和封面的 `data-cx`／`coverAnchor`
   同一条路。缺 `box` 的 sidecar（补字段之前算的）不贴属性，那些图照旧只挪不放大。

   五个数挤在一个属性里，是为了让回落只需要摘一样东西：脸框只描述第一环那张实体图，
   换到 `/avatar` 那张就整个作废，见 image-fallback.js 的 advanceImageFallback。 */
function faceBoxAttrs(f){
  const b=f&&f.box;
  if(!b)return '';
  return ` data-facebox="${[b.cx,b.cy,b.faceW,b.imgW,b.imgH].map(Number).join(' ')}"`;
}
/* 圆框里那张图按人脸取景。放大靠改 img 自己的尺寸和偏移，不用 transform：
   `object-position` 只能在 cover 裁掉的那部分里挪，方图根本没得挪，而 transform
   缩放会连圆框的描边一起放大。元素撑到「图按 cover 缩放再乘倍数」那么大，再用负偏移
   把脸心拉到框心，圆框的 `overflow:hidden` 负责裁——和不放大时是同一套几何。 */
function avatarFrame(img){
  const ring=img.parentElement;
  if(!ring)return;
  ['position','right','bottom','left','top','width','height'].forEach(name=>img.style.removeProperty(name));
  if(ring.dataset.nativeSmall==='true')return;
  const rect=ring.getBoundingClientRect();
  /* 图加载完时框还没布局，是真会发生的一整类情况：面板隐藏、`display:none` 的页签、
     缓存直出。那一刻框是 0×0，算出来的倍数只能是 1，而 `load` 不会再来第二次——
     放大于是静默地永不生效，页面上看不出和「这张图不需要放大」有任何区别。
     实测在资料页复现过：框已经 160×160、图也 complete，style 里却只有平移。
     等到框拿到尺寸再算一次，等不到就维持不放大。 */
  if(!(rect.width>0&&rect.height>0)){
    if(typeof ResizeObserver!=='function')return;
    const watch=new ResizeObserver(()=>{
      const now=ring.getBoundingClientRect();
      if(!(now.width>0&&now.height>0))return;
      watch.disconnect();
      avatarFrame(img);
    });
    watch.observe(ring);
    return;
  }
  const [cx,cy,faceW,imgW,imgH]=String(img.dataset.facebox).split(' ').map(Number);
  /* 索引页取的是实体图的派生件，边车记的是原件像素：等比缩过的仍是同一张图，按比例
     换算就对得上。脸心是归一化的，不跟着缩；脸框和图的像素一起乘，`faceZoom` 里那条
     无损上限才问得到手上这张真有多少像素。比例为 0 是换成了别的图，那时退回几何居中。 */
  const scale=faceSourceScale(img.naturalWidth,img.naturalHeight,imgW,imgH);
  if(!scale){
    img.style.objectPosition='50% 50%';
    return;
  }
  const frame=faceFrame({cx,cy,faceW:faceW*scale,imgW:imgW*scale,imgH:imgH*scale},
    {w:rect.width,h:rect.height},window.devicePixelRatio||1);
  // 放不大就一个字都不写：留下的是 CSS 里那份几何，`object-position` 照旧生效。
  if(!frame)return;
  const s=img.style;
  // `inset:0` 定了 right/bottom，和这里的 left+width 过约束；显式撤掉，不靠浏览器取舍。
  s.position='absolute';s.right='auto';s.bottom='auto';
  s.left=`${frame.left}%`;s.top=`${frame.top}%`;
  s.width=`${frame.width}%`;s.height=`${frame.height}%`;
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
  const code=new URL(img.currentSrc||img.src,location.href).searchParams.get('code')||'';
  // FC2 封面是整幅画面，横向取景跟随人脸；宽高比不代表有 DVD 正封。
  img.dataset.frame=/^FC2(?:-PPV)?-/i.test(code)||r>=1.65?'still':r>1.2?'sleeve':'front';
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
  posterPanel(img,car);
  /* 小图版式整张放进卡片（`.whole`）：FC2 那种方图、竖版正封放进横卡片，两侧同样留出
     两条，垫模糊底而不是黑边。比例差不到 2% 的那一丝留白看不出来，不必多解一张图。 */
  if((img.classList.contains('whole')||img.dataset.frame==='front')&&Math.abs(r/car-1)>.02)coverBackdrop(img);
}
/* 只把折痕右边那块正封摆进卡片，封底一个像素都不露。折痕位置在 `data-posterbox` 里，
   换算要的容器比例只有页面知道，两边在这里才凑齐。整张封套和「剧照 | 正封 | 剧照」
   的 16:9 拼图才有正封可切；没有框（本机 1516 张封面里 771 张判定为不裁，永远拿不到）
   就一个字都不写，CSS 里那份贴右缘或按人脸的回退照旧生效。 */
/* 正封的宽高比先验，与 `jav_poster_crop.PANEL_ASPECT` 同一个数。没有边车的封套
   按正封宽度取景，贴右缘时 0.75 的卡片比正封宽，会带进一条书脊。 */
const PANEL_ASPECT=0.704;
function posterPanel(img,ratio){
  if(img.dataset.frame==='front')return;
  let [x0,imgW,imgH,y0,x1,y1]=String(img.dataset.posterbox||'').split(' ').map(Number);
  /* 没有框的双页封套按先验从右缘量回去，与服务端折痕找不到时的比例框一致。 */
  if(!img.dataset.posterbox&&img.dataset.frame==='sleeve'){
    imgW=img.naturalWidth;imgH=img.naturalHeight;
    x0=Math.round(imgW-PANEL_ASPECT*imgH);y0=0;x1=imgW;y1=imgH;
  }
  /* 框是按那一版源图的像素算的，而封面会被更大的那张原子替换。尺寸对不上就说明
     框描述的是另一张图，落在这张上是一块错位的区域——而错位在页面上和「本来就该
     这么取景」看不出区别，所以宁可退回回退值。 */
  // 卡片先取的是等比缩小的派生档，框的百分比在等比缩放下不变，所以认缩小，不认别的图。
  if(!faceSourceScale(img.naturalWidth,img.naturalHeight,imgW,imgH))return;
  const frame=panelFrame({x0,y0,x1,y1,px:[imgW,imgH]},ratio);
  if(!frame)return;
  img.classList.add('panel');
  img.style.setProperty('--panel-clip',
    `${frame.clip.top}% ${frame.clip.right}% ${frame.clip.bottom}% ${frame.clip.left}%`);
  img.style.setProperty('--panel-left',`${frame.left}%`);
  img.style.setProperty('--panel-top',`${frame.top}%`);
  img.style.setProperty('--panel-height',`${frame.height}%`);
  coverBackdrop(img);
}
/* 封面比卡片窄或宽时留出的那两条，垫同一张封面的模糊放大版。挂在卡片上而不是图片上：
   正封那时已经被 `clip-path` 切成一块，铺不到留白处。糊成一片的底用不着原件的像素，
   换回原件之后这一层仍取派生档。 */
function coverBackdrop(img){
  img.closest('.pic,[data-media-pic]')?.style.setProperty('--cover-blur',
    `url("${img.dataset.thumbSrc||img.currentSrc||img.src}")`);
}
/* 卡片先取封面的派生档（`/cover?thumb=1`）：高清原件一张解码 38 MB，一页几十张挤爆
   解码缓存，来回滚动时滚走的被清掉、滚回来现解，那一段是空白。取景落定之后量这张图在
   屏幕上铺开多大：一个源像素要占不止一个设备像素，就是派生档不够清楚，换回原件。
   单列、大图这些真用得上像素的地方照旧是原件，多列时屏幕本来就放不下那么多像素。 */
function upgradeCover(img){
  if(!/[?&]thumb=1(&|$)/.test(img.src)||!img.naturalWidth)return;
  const {width,height}=img.getBoundingClientRect();
  const pick=getComputedStyle(img).objectFit==='contain'?Math.min:Math.max;
  const scale=pick(width/img.naturalWidth,height/img.naturalHeight)*(window.devicePixelRatio||1);
  if(!(scale>1.01))return;
  img.dataset.thumbSrc=img.src;
  img.src=img.src.replace(/[?&]thumb=1(?=&|$)/,'');
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
  if(!(img instanceof HTMLImageElement))return;
  settleImage(img);
  fitNativeImage(img);
  if(img.classList.contains('cover')){coverAnchor(img);upgradeCover(img)}
  // 头像走同一条路，理由也同一个：倍数要等图和框都落地才算得出来。
  else if(img.dataset.facebox)avatarFrame(img);
},true);
/* 封面与头像的加载态，和换头像那一格同一形态：图还在路上时框上铺一层微光，到手后
   微光淡出并糊掉（`09-skeleton.css` 的 `.imgwait`）。图是模板字符串拼进来的，逐张挂
   监听做不到，所以在插进页面时看一眼：已经 `complete` 的（缓存里直接解码的那种）
   什么都不标，页面每次重绘都不会闪一下微光。标上之后 `load` 一定会来——图已经挂在
   文档上，捕获阶段的监听收得到；取不到图的 `error` 同样收尾，不让微光盖住首字母。
   收尾后类名一并摘掉：没到门槛就到手的直接摘，淡出过的等淡出完再摘，封面上平时不留
   那层 `::after`。React 索引页的头像框（`[data-person-ring]`）与资料卡的大位、同台艺人
   （`[data-entity-portrait]`、`[data-hero-ring]`）里那张图同样由遗留层拼，插进页面时照样
   被这里看见。 */
const PENDING_IMAGES='.pic>img.poster,[data-media-art]>img,.ring>img,[data-tier-ring]>img,[data-person-ring]>img,[data-entity-portrait]>img,[data-hero-ring]>img';
const pendingSince=new WeakMap();
function watchPendingImages(node){
  const found=node.matches(PENDING_IMAGES)?[node]:node.querySelectorAll(PENDING_IMAGES);
  for(const img of found){
    // 缓存图插入时先完成取景；load 尚未派发也不露出默认的居中封套。
    if(img.complete&&img.naturalWidth&&img.classList.contains('cover'))coverAnchor(img);
    if(!img.complete){
      img.parentElement.classList.add('imgwait');pendingSince.set(img.parentElement,performance.now());
    }
  }
}
function settleImage(img){
  const box=img.parentElement;
  if(!box?.classList.contains('imgwait'))return;
  if(performance.now()-pendingSince.get(box)<SKELETON_REVEAL_DELAY){box.classList.remove('imgwait');return}
  box.classList.replace('imgwait','imgdone');
  let timer=null;
  const drop=event=>{
    if(event&&(event.target!==box||event.pseudoElement!=='::after'))return;
    box.removeEventListener('transitionend',drop);clearTimeout(timer);box.classList.remove('imgdone');
  };
  box.addEventListener('transitionend',drop);
  // 兜底：面板藏在后台或动效归零时 `transitionend` 不会来。
  timer=setTimeout(drop,1000);
}
new MutationObserver(records=>{
  for(const record of records)for(const node of record.addedNodes)
    if(node.nodeType===Node.ELEMENT_NODE)watchPendingImages(node);
}).observe(document.body,{childList:true,subtree:true});
// 挂在 document 上，比 body 上那条兜底链先收到：图被摘掉之前框还找得到。兜底链里还有
// 下一张时微光留着，换上的那张到手才收。
document.addEventListener('error',event=>{
  const img=event.target;
  if(img instanceof HTMLImageElement&&!img.dataset.fallbacks)settleImage(img);
},true);
/* 图比框还小时不再拉伸：原尺寸居中摆，空出来的一圈拿同一张图放大模糊补底。

   厂牌标识实测从 42 px 到 1378 px 都有。`/logo?variant=large` 已经先挑过这个厂牌
   最清晰的一份，剩下的是本来就没有大图的厂牌——把 112 px 的那张拉满 180 px 的格子
   只是把糊放大给人看，而摆在原尺寸上，它至少是清楚的。

   度量只能在 `load` 之后做：图没加载完时 `naturalWidth` 读到的是 0。换过回落图后
   `load` 会再来一次，这里读的 `currentSrc` 也就跟着是当前真正显示的那张。 */
// 允许适度放大；明显过小的图片才按源尺寸补底。
function fitNativeImage(img){
  const box=img.closest('[data-fit-native]');
  if(!box||!img.naturalWidth)return;
  // 版式切换会改变框的大小，每次按屏幕像素密度重新判断。
  const {small,width,height}=nativeImageFit(img.naturalWidth,img.naturalHeight,box.clientWidth,box.clientHeight,window.devicePixelRatio||1);
  box.dataset.nativeSmall=String(small);
  box.style.setProperty('--markw',small?width+'px':'100%');
  box.style.setProperty('--markh',small?height+'px':'100%');
  const src=(img.currentSrc||img.src).replace(/"/g,'%22');
  box.style.setProperty('--markbg',small?`url("${src}")`:'none');
}
/* 已经加载完的图不会再发 `load`，容器换了尺寸就得自己重量一遍。 */
function refitNativeImages(root){
  (root||document).querySelectorAll('[data-fit-native] img').forEach(img=>{
    fitNativeImage(img);
    if(img.dataset.facebox)avatarFrame(img);
  });
}
let coverRecheck=0;
window.addEventListener('resize',()=>{
  refitNativeImages($('#index'));
  // 窗口放大后卡片跟着变大，先前够用的派生档可能就不够了；只增不减，换回来的原件留着。
  // 等拖动停下再量：逐张量尺寸要读样式和盒子，跟着每一帧 resize 跑就是一次次强制排版。
  clearTimeout(coverRecheck);
  coverRecheck=setTimeout(()=>$('#index').querySelectorAll('img.cover').forEach(img=>{
    if(img.complete)upgradeCover(img)}),200);
},{passive:true});
/* 大图卡片的容器比例。本机 1014 张封面实测，683 张判定有正封，正封自己的宽高比
   从 0.667 到 0.749 都有，中位数 0.704、99% 分位 0.725——一行卡片必须等高，容器
   只能取一个数，所以它对不上其中大多数。0.75 比最宽的那张还宽：683 张一张都不用
   从左边切，全部居中摆，两侧留白交给 `--cover-blur` 那层模糊背景，每边中位 3.1%、
   最大 5.6%。
   取 0.72 会让 10 张被切掉最多 3.8%，取 0.76 同样一张不切但留白到每边中位 3.7%。 */
const COVER_FRONT_RATIO=0.75;
function coverImage(it,layout,eager){
  const src=`/cover?code=${encodeURIComponent(it.code||'')}&thumb=1`;
  // 人脸位置原样交给页面，锚点由 `coverAnchor` 在加载后算：哪个轴被裁、要推多远，
  // 只有同时拿到图片和容器的比例才知道。人物在画面里的位置差别很大，写死的锚点会把
  // 一部分作品裁掉下巴或整个切出画外；取不到人脸就退回固定取景。
  const f=it.cover_frame||{};
  // 纵向夹在 5%–60%：脸不会长在图片下半截，落在那儿是检出跑偏而不是构图。
  const face=[f.cx!=null?` data-cx="${f.cx}"`:'',
    f.cy!=null?` data-cy="${Math.min(0.6,Math.max(0.05,f.cy))}"`:''].join('');
  /* 正封那一块的取景框，源图像素坐标加源图尺寸，由 `posterAnchor` 在加载后换算成
     百分比。`map(Number)` 既是校验也是转义：进到属性里的一定是数字。 */
  const pb=it.poster_box;
  const box=pb?` data-posterbox="${[pb.x0,(pb.px||[])[0],(pb.px||[])[1],pb.y0,pb.x1,pb.y1].map(Number).join(' ')}"`:'';
  // 小图看整张（含剧照拼贴），大图只取右侧正封。
  return `<img class="poster cover ${layout==='small'?'whole':'front'}" src="${src}"
    alt="" loading="${eager?'eager':'lazy'}"${face}${box} data-drop="self">`;
}
function javArtwork(it,layout,eager=false){
  const kind=javImageKind(it,appSettings.javImage);
  if(!kind)return '<span class="nopic">无预览</span>';
  const cover=it.has_cover&&it.code?`/cover?code=${encodeURIComponent(it.code)}&thumb=1`:'';
  const thumb=(it.has_thumb||it.has_local_poster)?`/poster?id=${it.id}&c=4`:'';
  const coverHtml=coverImage(it,layout==='big'?'big':'small',eager);
  // 取景数据要跟着元素走：换回官方封面时 `syncJavImages` 换的是同一个 <img>，
  // 只贴在封面那份 HTML 上的话，从预览图切回来就取不到框。
  const frame=(coverHtml.match(/ data-(?:c[xy]|posterbox)="[^"]*"/g)||[]).join('');
  const image=kind==='cover'?coverHtml
    :`<img class="poster" src="${thumb}" alt="" loading="${eager?'eager':'lazy'}"${frame}>`;
  return image.replace('<img ',`<img data-jav-image="${it.id}" data-jav-cover="${esc(cover)}" data-jav-thumb="${esc(thumb)}" data-jav-image-layout="${layout}" `);
}
/* 详情开场给播放器的海报位：video.js 的脚本还在下载、流源还没接上时，画面先给本地
   封面，不留一块黑。选哪张与卡片同一份判据，番号作品跟随「JAV 默认封面」设置——
   官方封套或预览图；其它媒体退到本地预览格。返回空串表示这条没有可用的本地图，
   播放器照旧从黑场开始。 */
function detailPosterUrl(it){
  const thumb=(it.has_thumb||it.has_local_poster)?`/poster?id=${it.id}&c=4`:'';
  if(!it.is_jav)return thumb;
  return javImageKind(it,appSettings.javImage)==='cover'
    ?`/cover?code=${encodeURIComponent(it.code||'')}`:thumb;
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
      :{kind:'',name:'未归属'});
  const who=identity.name,whoKind=identity.kind;
  // 共演作品用头像提示多人，但文字只保留第一位，再给总人数。两个长名字加元数据
  // 会在普通卡片里折成三行；「第一位 + 等 N 人」仍能说明身份与规模。
  const coStarred=performers.length>1&&!primaryCreator;
  const avatar=coStarred
    ? `<div class="mavstack">${performers.slice(0,5)
        .map((nm,i)=>link('mav',`data-entity-kind="performer" data-entity-name="${esc(nm)}" title="打开${esc(performerLabel(it))}页：${esc(nm)}"`,avatarInner(nm,performerRefs[i],REP[nm])))
        .join('')}</div>`
    : (()=>{
        /* 头像和名字必须落到同一个身份。各自挑 kind（头像先看 performer、名字先看
           creator）时，同名的 creator/performer 重复实体（账本里有 35 组）会一个跳
           `/performers/x`、另一个跳 `/creators/x`，同一张卡上两个入口去两个地方。 */
        const avatarKind=identity.kind;
        const avatarName=identity.name;
        const avatarRef=avatarKind==='performer'?performerRef:it.creator_entity;
        const inner=avatarInner(avatarName,avatarRef,
          avatarKind?REP[avatarName]:null,avatarKind||'performer');
        return avatarKind
          ? link('mav',`data-entity-kind="${avatarKind}" data-entity-name="${esc(avatarName)}" title="打开${avatarKind==='performer'?esc(performerLabel(it)):'资料'}页"`,inner)
          : `<span class="mav">${inner}</span>`;
      })();
  const whoHtml=coStarred
    ? link('who',`data-entity-kind="performer" data-entity-name="${esc(performer)}"`,esc(performer))
      +`<span class="whomore">等 ${performerTotal} 人</span>`
    : (whoKind?link('who',`data-entity-kind="${whoKind}" data-entity-name="${esc(who)}"`,esc(who))
      /* 没有署名人的那批是馆藏里的一类，不是一句读完就没用的说明：这里点得开，
         和女优名、厂牌名一样。队列行整行本身是 <button>，嵌不了按钮，仍出文字。 */
      :linked?`<button class="who unownedlink" type="button" data-open-unowned>${esc(who)}</button>`
        :`<span class="who">${esc(who)}</span>`);
  return {avatar,whoHtml};
}
function openResourceCard(id,anchor=null){
  const item=CACHE[id];
  if(!item||!item.medium||item.medium==='video'){openItem(id,true,null,anchor);return}
  if(item.medium==='image'&&item.location!=='online'){
    window.open('/photo?id='+id,'_blank','noopener');return
  }
  toggleSelection(id);
}
function mixLabel(it){
  const performer=(it.performers||[])[0];
  return (it.is_jav&&performer?performer:it.creator)||performer||it.studio||it.code||tagLabel((it.tags||[])[0])||'为你推荐';
}
/* 播放队列每一行的小图。取图的判据同网格里 Mix 卡的画面（`catalog-grid` 的 `mixFace`）：
   番号作品走封套链，其余取本地预览格，同一条在两处长得一样。 */
function mixFacePoster(it,layout,eager){
  const jav=cardLayoutActive()&&!!it.is_jav;
  /* 翻动的那几张必须 eager：它们是悬浮时才插进一个 hidden 容器的，
     lazy 图在没有布局盒时根本不会发请求，一翻就是黑屏。 */
  const load=eager?'eager':'lazy';
  return it.is_jav
    ? javArtwork(it,jav?layout:'small',eager)
    : (it.has_thumb||it.has_local_poster
      ? `<img class="poster" src="/poster?id=${it.id}&c=4" alt="" loading="${load}">`
      : `<span class="nopic">无预览</span>`);
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
const reduceMotion=()=>matchMedia('(prefers-reduced-motion:reduce)').matches;
/* 一个标签是否生效、按一下变成什么，全站只有这一份判据。目录、资料页和详情页各自
   存着自己的筛选，谁在那里手写一次 `split(',')` 或 `=== filters.tag`，谁就会与其余
   几处漂开：按下态按多选算、点击按单选写，同一枚标签的显示和行为对不上。 */
const tagList=(value=state.tag)=>String(value||'').split(',').filter(Boolean);
const tagPressed=(value,tag)=>tagList(value).includes(String(tag));
const withTagToggled=(value,tag)=>{const cur=tagList(value);const index=cur.indexOf(tag);
  index>=0?cur.splice(index,1):cur.push(tag);return cur.join(',')};
/* 馆藏卡片网格（`catalog-grid` island）用的助手与动作。各只有一份、身份不变：卡片按引用
   比较，每次推新对象进去就是整屏重画。 */
const gridHelpers={
  coverHtml:(it,layout,eager)=>coverImage(it,layout,eager),
  relayoutArt:(root,layout)=>relayoutJavImages(root,layout).forEach(img=>{coverAnchor(img);upgradeCover(img)}),
  badgeHtml:(location,cost)=>srcBadge(location,cost),
  titleHtml:(it,raw)=>javTitleHtml(it,raw),
  displayName:(it,raw)=>javDisplayName(it,raw),
  avatarHtml:(name,ref,kind)=>avatarInner(name,ref,kind?REP[name]:null,kind||'performer'),
  tagLabel:tag=>tagLabel(tag),
  wireHover:(el,it)=>wireHover(el,it),
  releaseHover:el=>{el._stopHover?.();releaseHoverPreviews(el)},
};
/* 打开一张作品卡：小窗开着时普通视频卡直接在小窗里换片，分卷／版次组各进自己的队列，
   其余打开详情。 */
function openGridCard(it,anchor){
  if(stageApi()?.miniplayerTakesCard(it)){stageApi().miniplayerPlay(it.id);return}
  if(it.part_group){openParts(it.part_group.seed_id,it.id,true,anchor);return}
  if(it.edition_group){openEditions(it.edition_group.seed_id,it.id,true,anchor);return}
  openItem(it.id,true,null,anchor);
}
/* 稍后看只由点击触发，写 ledger；成功与撤销都把新值回给卡片上那枚键。 */
async function toggleWatchLater(it,onChange){
  try{
    const r=await api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})});
    it.watch_later=r.watch_later;onChange(!!r.watch_later);
    actionReceipt(r.watch_later?'已加入稍后看':'已移出稍后看',{undo:async()=>{
      const restored=await api('/api/watch-later',{method:'POST',body:JSON.stringify({id:it.id})});
      it.watch_later=restored.watch_later;onChange(!!restored.watch_later);
    }});
  }catch(error){actionFailure('更新稍后看',error)}
}
/* 回收站卡上那枚键：还原或移入回收站，写 ledger，做完重读目录并给撤销。失败再抛给卡片，
   它据此把键恢复成可点。 */
async function runResourceOperation(it,operation){
  try{
    await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[it.id],operation})});
    await loadCatalog();
    const inverse=operation==='restore'?'dispose':'restore';
    actionReceipt(operation==='restore'?'已还原':'已移入回收站',{undo:async()=>{
      await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[it.id],operation:inverse})});
      await loadCatalog();
    }});
  }catch(error){actionFailure('操作',error);throw error}
}
const gridActions={
  open:(it,anchor)=>openGridCard(it,anchor),
  openResource:(it,anchor)=>stageApi()?.miniplayerTakesCard(it)?stageApi().miniplayerPlay(it.id):openResourceCard(it.id,anchor),
  openShort:it=>stageApi()?.miniplayerTakesCard(it)?stageApi().miniplayerPlay(it.id):openTok(it.id),
  openShorts:()=>openTok(),
  openMix:(seedId,anchor)=>openMix(seedId,seedId,true,anchor),
  openEntity:(kind,name)=>openEntity(kind,name),
  openUnowned:()=>openUnowned(),
  /* 卡片上的标签是「只看这个标签」，已经在筛它就取消。在哪一屏点就在哪一屏生效。 */
  toggleTag:tag=>{
    commitContextFilter(filters=>{filters.tag=tagPressed(filters.tag,tag)?'':tag});
    window.scrollTo({top:0,behavior:'smooth'});
  },
  toggleSelection:(id,range)=>toggleSelection(id,range),
  watchLater:(it,onChange)=>toggleWatchLater(it,onChange),
  resourceOperation:(it,operation)=>runResourceOperation(it,operation),
  mixRelated:seedId=>mixRelated(seedId),
  canFlip:()=>!selectMode&&!censorOn()&&!window.__scrolling&&!reduceMotion(),
};

/* ── 顶部标签条 + 抽屉 ── */
/* 状态页把顶部三层收窄到本页口径，为的是不列出「在这一页一个作品都没有」的人和厂牌。
   但集合窄到聚合结果为空时（「已标记」常年只有几条），收窄就把整排一并收走了：
   同一条筛选条上换一格，页面顶上凭空少两层，读起来是跳去了另一个页面而不是换了筛选。
   空了就退回全库口径。这一排点开的是实体页，本来就要离开当前状态，
   它回答的从来不是「这一页里有谁」，而是「接下来去看谁」。 */
async function loadTops(params){
  const scoped=await api('/api/tops?'+params);
  if(scoped.performers.length||scoped.studios.length||!params.has('state'))return scoped;
  const wide=new URLSearchParams(params);wide.delete('state');
  return api('/api/tops?'+wide)
}
/* 一排一页六十个，滚到底再要下一页。写成函数是因为续页要跟第一页同一套口径——种子、
   JAV、状态少一个，续上来的就是另一份名单里的人。 */
const topsQueryParams=(context,page=0)=>{
  const params=new URLSearchParams({n:'60',seed:state.seed||''});
  if(page)params.set('page',String(page));
  if(javActive())params.set('jav','1');
  if(context.type==='home'&&state.state)params.set('state',state.state);
  return params;
};
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
    ['loc','creator','studio','tag','tag_match','len','dur_min','dur_max','orient','region','q','thumb'].forEach(key=>{
      if(filters[key])facetParams.set(key,filters[key]);
    });
  }
  const scope=facetParams.toString();
  if(scope!==barsDataScope){barsDataCache=null;barsDataPromise=null;barsDataScope=scope}
  if(barsDataCache&&Date.now()-barsDataAt<30000)return barsDataCache;
  // 顶部三层跟着「换一批」的同一个种子走，刷新后才真的换人。
  if(!barsDataPromise)barsDataPromise=Promise.all([
      api('/api/facets'+(scope?'?'+scope:'')),
      loadTops(topsQueryParams(context))])
    .then(data=>{barsDataCache=data;barsDataAt=Date.now();return data})
    .finally(()=>{barsDataPromise=null});
  return barsDataPromise
}
/* 换一个筛选就是换一份名单，而第一屏是这份名单的开头。人停在半路时原地换掉，屏幕上那
   一段跟他刚才在读的既不连也不相干；新名单还常比旧的短，浏览器只好把他钳到别处，落点
   跟按之前不是同一个地方。滚动锚定这时也在帮倒忙：骨架换成卡片那一下它会照新内容再推
   一次，把正在走的这段滚动顶开——所以这一路上先把它关掉。 */
function scrollFilteredViewToTop(){
  if(scrollY<=0)return;
  const root=document.documentElement;
  root.classList.add('refiltering');
  const done=()=>{root.classList.remove('refiltering');removeEventListener('scrollend',done)};
  addEventListener('scrollend',done);
  setTimeout(done,1200);
  scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
}
/* 加一条筛选不重画顶部。整块重画的代价不是耗时，是把人读到一半的东西换掉：那排女优
   已经横着续到六十枚、停在第 600 像素上，重画一次退回二十四枚、滚回起点；标签条同理。
   而这一下他要看的是底下那份名单变成什么样，上面那几排跟这件事无关。
   所以按下态就地改，成员和滚动位置一概不动。选中的标签排到最前是重画时的事——刚点的
   那枚就在他眼皮底下，这一下把它抽走反倒是替他决定现在该看哪儿。 */
function applyFilterStateInPlace(filters){
  // 资料页那一条的按下态由岛按地址上的筛选算，新的筛选已经经 `routeEntityPage` 推过去了。
  if(barsContext.type!=='entity')paintCatalogFilter({tags:catalogTags(filters)});
  $('#drawer').querySelectorAll('.chip[data-key]').forEach(b=>
    b.setAttribute('aria-pressed',String(String(filters[b.dataset.key]||'')
      .split(',').filter(Boolean).includes(b.dataset.val))));
  const durMin=$('#durMin'),durMax=$('#durMax');
  if(durMin&&durMax){
    durMin.value=String(filters.dur_min?Math.min(180,+filters.dur_min/60):0);
    durMax.value=String(filters.dur_max?Math.min(180,+filters.dur_max/60):180);
    // 轨道上那截填充由 oninput 算，改 value 不会自己触发。
    durMin.dispatchEvent(new Event('input'));
  }
  renderCombo();
}
/* 侧栏那些数字是跟着当前筛选走的，不刷新就是一列对不上的数。但刷新只该改数字：整段
   重画会合上人展开的那几组、把这一列滚回顶上，而那正是「重画一遍」要避免的事。 */
let facetCountsSeq=0;
async function refreshFacetCounts(context){
  const seq=++facetCountsSeq;
  const [facetData]=await getBarsData(context);
  if(seq!==facetCountsSeq)return;
  barsFacets=facetData;
  if(context.type==='home')facets=facetData;
  const counts=new Map();
  [['loc',facetData.locations],['orient',facetData.orientations],['region',facetData.regions],
   ['creator',facetData.creators],
   ['tag',facetData.tags],['tag',facetData.tech]].forEach(([key,rows])=>
    (rows||[]).forEach(row=>counts.set(key+'\n'+row.k,row.n)));
  $('#drawer').querySelectorAll('.chip[data-key] .n').forEach(el=>{
    const chip=el.closest('.chip');
    el.textContent=(counts.get(chip.dataset.key+'\n'+chip.dataset.val)||0).toLocaleString();
  });
}
function commitContextFilter(mutate){
  scrollFilteredViewToTop();
  if(barsContext.type==='entity'){
    // 标签是作品筛选，点了就回到作品视图：留在照片或名册里既不生效，标签条也会自相矛盾。
    const filters={...barsContext.filters};mutate(filters);
    routeEntityPage(barsContext.kind,barsContext.name,filters);
    applyFilterStateInPlace(filters);refreshFacetCounts(barsContext);return
  }
  if(barsContext.type==='item'){
    // 从详情回到列表是换语境，不是换一条筛选：那几排本来就要照新语境重新画。
    const target=cloneBarsContext(detailReturnBarsContext);
    disposeStage(false);detailReturnBarsContext=null;
    if(target&&target.type==='entity'){
      mutate(target.filters);
      // 详情下面那一页通常还挂着，推新筛选就够；深链进的详情下面没有它，照新地址重开。
      if(routeEntityPage(target.kind,target.name,target.filters))buildBars();
      else void openEntity(target.kind,target.name,false);
      return
    }
    mutate(state);barsContext={type:'home',filters:state};route(homePath());showHomeSurfaces();
    buildBars();loadCatalog();return
  }
  mutate(state);route(homePath());
  applyFilterStateInPlace(state);refreshFacetCounts(barsContext);
  loadCatalog();
}
/* 左端四枚视图。资料页那一条（`entity-filter` 岛）用同一份清单画自己的观看状态。 */
const VIEW_PILLS=[{k:'',label:'全部'},{k:'fresh',label:'没看过'},
                  {k:'later',label:'稍后看'},{k:'flagged',label:'已标记'}];
const catalogViews=()=>VIEW_PILLS.map(v=>({...v,href:v.k?STATE_ROUTES[v.k]:'/'}));
/* 抽屉那一列跟筛选条那一排是同一块玻璃，只是换了根轴。它挂在 `#drawer` 上而不是那
   一列里：切页会把 `#drawerScroll` 整块重画，住在里面的话玻璃跟着一起没，动画在第
   一个微任务里就断了，看到的只是当前项换了个地方亮起来。`#drawer` 自己不重画，是这
   一侧唯一的定位宿主。代价跟筛选条那边一样——那一列自己的位置和纵滚都得补回来。 */
let navGlide=null,navGlideBox=null,navGlideTarget=null;
/* 切一次页那一列要被画两遍：先是导航自己那一遍，跟着是发现栏连侧栏一起重画的那一遍，
   两遍的标题行相差 4px。同步落在第一遍的读数上，玻璃就钉在那儿——一次切页留下 4px，
   来回切几次，它离当前那一格越来越远。所以画完下一帧再对一次，量到的一样就什么都不
   做。用当次那一格自己的引用，不重新去找按下态：指针悬在别的格上时找到的是另一格。 */
let navGlideSettle=0;
function settleNavGlide(deadline){
  if(navGlideSettle)return;
  const until=deadline||performance.now()+800;
  navGlideSettle=requestAnimationFrame(()=>{
    navGlideSettle=0;
    const scroll=$('#drawerScroll'),active=navGlideTarget;
    if(!navGlide||!navGlideBox||!scroll||!active||!active.isConnected)return;
    /* 有位移正在跑就等它跑完再对：这一下改的是终点，会把走到一半的那段掐掉。切页那次
       动画正好压在重画上，只看一帧就放弃的话，要对的正是这一次。 */
    if(navGlide.getAnimations().length){
      if(performance.now()<until)settleNavGlide(until);
      return;
    }
    const box={x:active.offsetLeft,y:active.offsetTop-scroll.scrollTop,
      w:active.offsetWidth,h:active.offsetHeight};
    if(!box.h)return;
    if(box.x===navGlideBox.x&&box.y===navGlideBox.y
      &&box.w===navGlideBox.w&&box.h===navGlideBox.h)return;
    navGlideBox=box;moveGlidePane(navGlide,null,box,'y');
  });
}
function syncNavGlide(animate,target){
  const host=$('#drawer'),scroll=$('#drawerScroll');
  const active=(target&&target.isConnected?target:null)
    ||(scroll&&scroll.querySelector('.dnav button[aria-pressed="true"]'));
  navGlideTarget=active||null;
  if(!host||!active){if(navGlide)navGlide.hidden=true;navGlideBox=null;return}
  if(!navGlide||navGlide.parentElement!==host){
    navGlide=document.createElement('span');navGlide.className='navglide';
    navGlide.setAttribute('aria-hidden','true');host.prepend(navGlide);navGlideBox=null;
  }
  /* 坐标走 `offsetTop` 不走 `getBoundingClientRect`：抽屉自己带一条收起的位移动画，
     量屏幕坐标会把宿主正在走的那一下一起吃进来，每量一次都是个新位置，玻璃于是在
     一次切页里连着起跑好几段。偏移量只认布局，抽屉滑到哪儿它都不变。 */
  const box={x:active.offsetLeft,y:active.offsetTop-scroll.scrollTop,
    w:active.offsetWidth,h:active.offsetHeight};
  if(!box.h)return;
  /* 那一列纵滚到看不见当前项时收起来：它住在滚动容器外面，不跟着一起被裁，不收的话
     会停在侧栏顶上，像块没人要的高光。 */
  navGlide.hidden=box.y+box.h<=scroll.offsetTop||box.y>=scroll.offsetTop+scroll.clientHeight;
  const from=navGlideBox;navGlideBox=box;
  moveGlidePane(navGlide,animate?from:null,box,'y');
  settleNavGlide();
}
/* 侧栏纵滚时玻璃原地跟上：容器滚走了它不动就会脱开对准的那一格。一帧只算一次——
   每次都要量位置，逐个滚动事件地量等于把滚动这件事拖回主线程排队。 */
let navGlideTick=0;
/* 开合与响应式布局都按实际尺寸同步；开合后悬停目标归回当前导航项。 */
function resizeNavGlide(){
  navGlide?.getAnimations().forEach(animation=>animation.cancel());
  syncNavGlide(false,navGlideTarget);
}
const navGlideResize=new ResizeObserver(resizeNavGlide);
navGlideResize.observe($('#drawer'));
navGlideResize.observe($('#drawerScroll'));
document.addEventListener('board:sidebar',()=>{
  navGlideTarget=null;
  if(navGlideTick)cancelAnimationFrame(navGlideTick);
  navGlideTick=requestAnimationFrame(()=>{navGlideTick=0;syncNavGlide(false)});
});
$('#drawerScroll').addEventListener('scroll',()=>{
  if(navGlideTick)return;
  navGlideTick=requestAnimationFrame(()=>{navGlideTick=0;syncNavGlide(false)});
},{passive:true});
/* 玻璃跟着指针走，不等点击：指到哪一格就滑过去，指针离开这一列再滑回真正选中的那格。
   `aria-pressed` 全程不动——移过去不是选中，读屏和键盘那边不该跟着变。
   两个监听都委托在 `#drawer` 上：那一列每次切页都整块重画，挂在按钮身上等于每次重画
   都要记得再接一遍。用 `pointerover`／`pointerout` 而不是 enter／leave，后两个不冒泡，
   委托接不到。 */
$('#drawer').addEventListener('pointerover',event=>{
  if(event.pointerType==='touch')return;
  const button=event.target.closest?.('.dnav button[data-nav]');
  if(button)syncNavGlide(true,button);
});
$('#drawer').addEventListener('pointerout',event=>{
  if(event.pointerType==='touch')return;
  const column=event.target.closest?.('.dnav');
  if(column&&!column.contains(event.relatedTarget))syncNavGlide(true);
});
/* ── 首页筛选条（`catalog-filter` 岛，ADR-0031） ──
   两排头像、浮层上排的视图与标签、下排读数与排序，外加正文里网格上面那条交集条。筛选、路由与
   取数仍归壳：成员与按下态在这里算好当 props 递进去，动作回到这里，落点照旧是
   `commitContextFilter` 与 `loadCatalog`。壳手上留一份完整的 props，每次只改其中几项：岛画好了
   就推补丁；还在挂就先记着，挂完再把整份推一次。 */
/* 顶上那几排先画一屏够用的量，横滚到右端再续下一批（岛里的 `usePaged`）。标签条先摆的是生效
   的那几枚加抽出来的这一批。 */
const TAGS_FIRST=26;
function catalogFilterBase(){
  return {tiers:null,empty:false,tags:[],tagFirst:TAGS_FIRST,views:catalogViews(),state:'',count:null,
    trash:false,sorts:[],layout:null,refreshing:false,offscreen:false,combo:[],comboHidden:true,comboHost:$('#combo'),
    actions:catalogFilterActions(),
    helpers:{wireDrag,wireScroller:row=>{if(row)wireHorizontalScroller(row)}}};
}
/* 筛选条收起或露出之后补推一次，岛才知道这一刻在不在屏幕上。还没挂过就不必：挂的那一刻自己会算。 */
function syncCatalogFilterScreen(){if(catalogFilterProps)paintCatalogFilter({})}
function paintCatalogFilter(patch){
  const host=$('#catalogFilter');
  /* 收起时岛只留两排头像：浮层那两排与资料页、索引页的是同一组控件，藏着一份就是两套同名的，
     等不来的读数微光也会一直挂在页面上。收起时同样不铺静态骨架。 */
  const offscreen=host.style.display==='none'||document.body.matches('.entity-open,.index-open');
  patch={...patch,offscreen};
  catalogFilterProps={...(catalogFilterProps||catalogFilterBase()),...patch};
  if(catalogFilterMounting)return;
  if(islandMounted(host)){updateIsland(host,patch);return}
  if(!host.firstChild&&!offscreen){host.innerHTML=catalogFilterSkeletonHtml(catalogViews(),catalogFilterProps.state);fitSkeleton(host)}
  catalogFilterMounting=mountIsland('catalog-filter',host,catalogFilterProps)
    .then(()=>updateIsland(host,catalogFilterProps))
    .finally(()=>{catalogFilterMounting=null});
}
function catalogFilterActions(){
  return {
    openEntity:(kind,name)=>openEntity(kind,name),
    /* 按下去当场就推新的按下态，滑动玻璃跟着走，不等这一趟取数。 */
    setView:view=>{
      state.state=view;paintCatalogFilter({state:view});
      route(homePath());buildBars();loadCatalog();
    },
    toggleTag:tag=>toggleTag(tag),
    clearFilter:key=>commitContextFilter(filters=>{filters[key]=''}),
    clearAll:()=>commitContextFilter(filters=>{filters.tag='';filters.creator='';filters.studio='';filters.owner=''}),
    setSort:key=>{
      const next=nextSortState(key,state.sort,state.dir);
      if(!next)return;
      state.sort=next.sort;state.dir=next.dir;loadCatalog();
    },
    reshuffle:()=>refreshAll(),
    setLayout:value=>{if(javActive())setJavLayout(value);else setHomeLayout(value)},
    /* 每排各记各的页号：两排的长度不一样，共用一个计数会让先到头的那排替另一排把页翻过去。
       页号跟着这一份名单走，`buildBars` 换名单时从头数起。 */
    moreTops:async kind=>{
      const pages=catalogTopsPages;if(!pages)return [];
      const rows=(await loadTops(topsQueryParams(pages.context,++pages[kind])))[kind]||[];
      return kind==='performers'?rows.map(tierPerformer):rows.map(tierStudio);
    },
  };
}
/* 读数右边那组分段开关：JAV 与首页各存一份卡片版式，别的目录路径上没有。 */
function catalogLayoutProp(){
  if(javActive())return {name:'jav-layout',label:'JAV 卡片版式',value:javLayout(),options:JAV_LAYOUTS};
  if(homeLayoutActive())return {name:'home-layout',label:'首页卡片版式',value:cardLayout(),options:JAV_LAYOUTS};
  return null;
}
/* 下排只由当前 state 决定，这次加载不会改变它，所以每次取数前就推成最终样子。回收站是待清理
   队列，不是浏览列表：换一批和排序在那里没有意义，读数挂在说明行上，岛不出下排。 */
function catalogHeadProps(){
  return {sorts:sortKeys(state.sort,state.dir),layout:catalogLayoutProp(),
    state:state.state||'',trash:state.state==='trash'};
}
/* 标签条的成员由 `buildBars` 定，按下态跟着筛选走：加一条筛选只改按下态，成员与滚动位置不动。 */
function catalogTags(filters){
  return catalogTagRows.map(row=>({...row,selected:tagPressed(filters.tag,row.k)}));
}
/* 这排圆框只有 48 px，脸在里面本来就小。框越小，同一张图能无损放大的余量越大：
   `performer-8711` 那种全身站姿照在资料页只放得到 2 倍，在这里放到 3 倍还没碰到
   源图 1:1。取景与索引页同一份 sidecar、同一个换算。 */
function tierPerformer(x){
  return {name:x.k,ringHtml:`<span data-tier-initial>${esc(x.k.slice(0,1))}</span>${entityFaceImg(
    {id:x.id,hasImage:x.has_image,rep:x.has_avatar?x.rep:null,style:facePos(x.avatar_focus),focus:x.avatar_focus})}`};
}
/* 正规厂牌用官网 logo；缺失时只显示首两个字，绝不把作品截图冒充厂牌图标。

   没装标识就不给地址，一个 `<img>` 都不出。无条件出图、靠 `/logo` 回 404 换成首字母的
   代价是：一排 30 个厂牌里 21 个是 404，而 404 那条响应不可缓存，每次重绘再打一整轮。
   `has_logo` 由 `/api/tops` 下发，判据和取图同一个函数。 */
function tierStudio(x){
  return {name:x.k,fallback:x.k.slice(0,2),
    logo:x.has_logo?`/logo?studio=${encodeURIComponent(x.k)}&variant=icon`:''};
}
/* 首屏时这一块要等两个聚合查询，约一秒。铺上骨架就必须有一次真的绘制来顶掉它，哪怕取回的
   数据跟上一次一模一样。只在还没画过时铺：导航到已经有内容的页面留着旧内容等新内容，那不是
   从无到有。React 包没到之前宿主里是壳铺的那份静态骨架（`paintCatalogFilter`），四枚视图已经是
   真链接，点下去由宿主上的委托接住。 */
function renderBarsLoading(filterState){
  if(catalogFilterProps?.tiers)return;
  barsRendered='';
  paintCatalogFilter({tiers:null,state:filterState.state||''});
}
$('#catalogFilter').addEventListener('click',event=>{
  const view=event.target.closest?.('[data-catalog-view]');
  if(!view||event.defaultPrevented)return;
  event.preventDefault();catalogFilterActions().setView(view.dataset.catalogView);
});
/* 展开与收起是同一枚键的两面，`aria-expanded` 说的就是这一组眼下摊开到哪一步，箭头照它
   翻。一个箭头说得完的事不再配一句字：名单末尾那个位置，字比图标更像名单的最后一项。 */
const sidebarMoreHtml=(key,group)=>`<button class="sidemore" data-more="${key}" aria-expanded="false" aria-label="展开全部${group}"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-down"/></svg></button>`;
async function buildBars(){
  const requestSeq=++barsRequestSeq;
  buildDrawerNavigation();
  if(!sidebarHasCatalogContent(location.pathname))return;
  /* 详情浮窗是盖住整页的模态：两排头像、标签条和抽屉在它开着的时候一格都看不见。
     为它们另取一趟这一部作品口径的聚合，换来的只是把列表那份缓存挤掉——关掉详情时
     整排头像连 `<img>` 一起重建，人看到的就是「点进去又退出来，页面自己刷新了一次」。
     所以详情不碰表面的条，列表的口径和那份缓存原样留着等他回来。 */
  if(barsContext.type==='item')return;
  const context=barsContext,filterState=activeFilterState();
  const signature=JSON.stringify([context,filterState,state.state||'',state.seed||'',javActive()]);
  renderBarsLoading(filterState);
  // 两个聚合查询互不依赖。冷启动各需约 1 秒，串行会让手机首屏白等；
  // 并行取回后再一次性绘制顶部与抽屉。
  const [facetData,tops]=await getBarsData(context);
  if(requestSeq!==barsRequestSeq)return;
  /* 口径和数据都和上一次一样时，画出来的是同一串 HTML。照样赋一次 innerHTML 只换来
     整排头像连 `<img>` 一起重建、重解一遍码，屏幕上就是白闪一下——这一排每一个都是
     一张图。比数据不比时间：详情看上十分钟再回来，取回的多半还是同一份。 */
  const rendered=signature+'\n'+JSON.stringify([facetData,tops]);
  if(rendered===barsRendered)return;
  barsRendered=rendered;
  const followTagRows=facetData.follow_tags||[];
  if(context.type==='home')facets=facetData;
  const topTags=facetData.tags||[];

  /* 顶部三层：女优圆头像 / 厂牌 / 内容标签。
     REP 表只收真能取到头像的代表作：卡片署名圈回落时读的就是它，取不到的进了表
     就是一个必然 404 的 `<img>`。`has_avatar` 说的是「已经裁好或印相还在」，不是
     「目录里有没有那张 jpg」——`/avatar` 按需生成，还没抓过的那条路留着。 */
  tops.performers.forEach(x=>{if(x.rep&&x.has_avatar)REP[x.k]=x.rep});
  tops.studios.forEach(x=>{if(x.rep&&x.has_avatar)REP[x.k]=x.rep});
  // 「两排都空」现在只剩全库真的一个人都没有这一种：窄集合已经由 loadTops 退回全库口径。
  const emptyHome=context.type==='home'&&!javActive()&&!state.state&&!state.q&&!facetData.locations.some(row=>row.n>0);
  catalogTopsPages={context,performers:0,studios:0};
  /* 加上去的那几枚排在最前面，按加的先后。它们不一定在抽出来的这一批里，也可能压根不
     在榜上——人是从卡片或详情页点进来的。这一排横着滚，一枚生效的标签落在第三十位跟没
     画出来是一回事：要撤掉刚加的那一条，得先把整排推过去把它找回来。
     第一屏其余的位置由那一批抽样填——「换一批」换的就是这批成员。续上去的是这一批之外
     剩下的，照数量从多到少读下来：抽样只管开头露谁，后面的顺序不归它管。
     标签后面带上这个标签下有多少，跟资料页那条筛选条同一个口径；生效的标签不在这一批里
     时不印数字（`n` 为空）。 */
  const appliedKeys=tagList(filterState.tag);
  const byTagKey=new Map(topTags.map(row=>[row.k,row]));
  const appliedTags=appliedKeys.map(k=>byTagKey.get(k)||{k});
  const tagPool=topTags.filter(row=>!appliedKeys.includes(row.k));
  const pickedTags=seededSample(tagPool,TAGS_FIRST,`tags:${state.seed||''}`);
  const pickedKeys=new Set(pickedTags.map(row=>row.k));
  catalogTagRows=appliedTags.concat(pickedTags,tagPool.filter(row=>!pickedKeys.has(row.k)))
    .map(row=>({k:row.k,label:tagLabel(row.k),n:row.n??null}));
  paintCatalogFilter({
    tiers:{key:String(barsRequestSeq),performers:tops.performers.map(tierPerformer),studios:tops.studios.map(tierStudio)},
    empty:emptyHome,tags:catalogTags(filterState),tagFirst:appliedTags.length+pickedTags.length,
    views:catalogViews(),state:filterState.state||'',
  });
  renderCombo();

  const chips=(items,key,multi,limit)=>items.length?`<div class="chips">`+items.slice(0,limit||999).map(it=>{
    const sel=(filterState[key]||'').split(',').filter(Boolean).includes(String(it.k));
    const dot=key==='loc'?(SRCICON[it.k]||`<i class="cost ${it.cost}"></i>`):'';
    // 脱盘的来源留在列表里但不可点：数量还有意义，点进去只会得到一屏放不出的卡片。
    const off=key==='loc'&&sourceOffline(it.k);
    return `<button class="chip${off?' offline':''}" aria-pressed="${sel}" data-key="${key}" data-multi="${multi?1:0}"
      ${off?`disabled title="${OFFLINE_HINT}"`:''}
      data-val="${esc(it.k)}">${dot}<span class="chip-label">${esc(it.label||tagLabel(it.k))}</span>${it.n!=null?`<span class="n" data-count-badge="${key}:${esc(it.k)}">${it.n.toLocaleString()}</span>`:''}</button>`;
  }).join('')+`</div>`:'';
  // 按语义类别区分来源、创作者、内容和技术规格。
  const sec=(t,b,x,cat)=>sidebarSectionHtml(t,b,x,cat);
  const scopedCreators=context.type==='entity'&&context.kind==='creator'
    ? facetData.creators.filter(item=>item.k!==context.name):facetData.creators;
  barsFacets=facetData;barsScopedCreators=scopedCreators;
  // 与窄栏共用 EDGE_ICONS —— 两边条目必须一致，抽屉不另写一份硬编码
  const navBtn=(k,label,ic)=>`<button data-nav="${k}" draggable="true" aria-pressed="${navOn(k)}">
    ${navigationIcon(k,ic)}<span>${label}</span></button>`;
  $('#drawerScroll').innerHTML=
    `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
      <b class="disp" style="font-size:15px;letter-spacing:.1em">导航与筛选</b>
      <button id="drawerClose" class="ib" title="收起">${icon('x')}</button></div>`+
    `<div class="dnav">${orderedEdgeIcons().map(([k,label,ic])=>navBtn(k,label,ic)).join('')}</div>`+
    sec('来源',chips(facetData.locations.map(l=>({k:l.k,label:LOC[l.k]||l.k,n:l.n,
        cost:(l.k==='pikpak'||l.k==='online')?'metered':'free'})),'loc',true),'','src')
    /* 时长只有一处读数：手柄上方那枚气泡，在拖它的时候出现。另起一行写「不限 — 不限」
       是同一件事说第二遍，而且滑块不动时它永远是那句话。 */
    +sec('时长',facetData.stats.duration?`<div class="duration-filter">
      <div class="dual-range" id="durationRange"><span class="range-base"></span><span class="range-fill"></span>
        <input id="durMin" type="range" min="0" max="180" step="5" value="${filterState.dur_min?Math.min(180,+filterState.dur_min/60):0}" aria-label="最短时长（分钟）">
        <input id="durMax" type="range" min="0" max="180" step="5" value="${filterState.dur_max?Math.min(180,+filterState.dur_max/60):180}" aria-label="最长时长（分钟）"></div></div>`:'','','meta')
    /* 产地紧挨着来源：两者回答的都是「这批片打哪来」，一个说存储，一个说发行体系。
       可多选——想一次看完日韩两边的片，不该逼人点两趟。 */
    +sec('产地',chips(facetData.regions,'region',true),'','general')
    +sec('画幅',chips(facetData.orientations,'orient'),'','meta')
    /* 展开键接在名单末尾，它说的是「这张名单还没完」——那句话要跟名单断掉的地方在
       一起。挂在组名那一行时，人得先把这一列读到底、再抬头回到标题去找它。
       身量取排名那枚展开药丸：一个箭头就说得完的事不必再配一句字。 */
    +sec('创作者',chips(scopedCreators,'creator',false,26),scopedCreators.length>26?sidebarMoreHtml('creator','创作者'):'','artist')
    +sec('内容标签',chips(facetData.tags,'tag',false,30),facetData.tags.length>30?sidebarMoreHtml('tag','内容标签'):'','general')
    +sec('影片属性',chips(facetData.tech,'tag',false,16),'','meta')
    +sec('关注标签',followTagRows.length?`<div class="chips">`+followTagRows.map(row=>
      `<button class="chip online" data-follow-drawer-tag="${esc(row.k)}"><span class="chip-label">${esc(tagLabel(row.k))}</span><span class="n" data-count-badge="follow:${esc(row.k)}">${row.n.toLocaleString()}</span></button>`
      ).join('')+`</div>`:'','','online');
  /* 抽屉每次筛选都整块重画，所以徽标弹不弹由 `popBadges` 按上一次的值判断，不由节点
     是不是新建的判断——照后者判，每换一个筛选整列计数都会一起弹。 */
  popBadges($('#drawerScroll'),'drawer');
  const dc=$('#drawerClose'); if(dc)dc.onclick=()=>openDrawer(false);
  $('#drawer').querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{
    openIndex(b.dataset.page); closeDrawerAfterNav()});
  $('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));
  $('#drawer').querySelectorAll('[data-follow-drawer-tag]').forEach(b=>b.onclick=()=>{
    followAuthors=new Set();followProviders=new Set();followMediaView='videos';followFilter='saved';
    followTags=new Set([b.dataset.followDrawerTag]);
    openDrawer(false);route(followViewPath());openFollow(false)});
  wireNavigationDrag($('#drawer').querySelector('.dnav'));
  syncNavGlide(false);
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
      if(commit)commitContextFilter(filters=>{
        filters.len='';filters.dur_min=lo?String(lo*60):'';filters.dur_max=hi<180?String(hi*60):''})
    };
    durMin.oninput=()=>syncDuration(false,'min');durMax.oninput=()=>syncDuration(false,'max');
    durMin.onchange=()=>syncDuration(true,'min');durMax.onchange=()=>syncDuration(true,'max');syncDuration();
  }
  $('#drawer').querySelectorAll('[data-more]').forEach(b=>b.onclick=()=>{
    const group=b.closest('.sec'), k=b.dataset.more;
    const src=k==='tag'?barsFacets.tags:barsScopedCreators;
    const lim=k==='tag'?30:26;
    const name=group.dataset.sidebarGroup;
    const expanded=b.getAttribute('aria-expanded')==='true';
    /* 这一列的位置归人自己管：摊开的内容全在按下的这个点以下，把他挪过去等于替他决定
       现在要看第几条。名单一变长，浏览器会顺着焦点和锚定把这一列推走，所以记下再放回。 */
    const scroller=$('#drawerScroll'),keep=scroller.scrollTop;
    const hold=()=>{scroller.scrollTop=keep};
    const body=group.querySelector(':scope > .fcollapse'),before=body?.getBoundingClientRect().height;
    group.querySelector('.chips').outerHTML=chips(src,k,false,expanded?lim:999);
    /* 摊开时名单从二十几条长到全部，和分组的 Collapse 走同一份高度过渡；中途收起整组就不收尾。 */
    const toggle=group.querySelector('.board-section-toggle');
    if(!expanded&&body)growCollapse(body,before,()=>toggle.getAttribute('aria-expanded')==='true');
    b.setAttribute('aria-expanded',String(!expanded));
    b.setAttribute('aria-label',(expanded?'展开全部':'收起')+name);
    /* 收起收的是整组。名单已经摊到最长，把它退回二十几条只是换一个断点，人还站在同一
       列读不完的东西前面；他按这一下要的是把这一组放回去。 */
    if(expanded)group.querySelector('.board-section-toggle').click();
    bind();hold();requestAnimationFrame(hold);});
}
/* 排序和换批都属于当前列表，放在筛选条下排，不占用全局导航。目录网格每接一页报一次总数与
   显示的卡数（竖屏带与 Mix 不算），读数由岛按位错峰写出来。 */
function paintCatalogCount(nextTotal,n){
  total=nextTotal;buildManageBar();
  const trash=state.state==='trash';
  /* 「清空回收站」和左边的计数说的是同一批文件，挂在说明行右端。它自己占一行时，
     标题和网格之间会空出一条只放一个按钮的带子。 */
  if(trash)paintManageLede(`${total.toLocaleString()} 个符合 · 显示 ${n}`,
    total?`<button class="batchaction danger" id="emptyTrash" type="button" title="永久删除回收站内容">清空回收站</button>`:'');
  paintCatalogFilter({count:{total,shown:n}});
  const emptyTrash=$('#emptyTrash');
  if(emptyTrash)emptyTrash.onclick=async(e)=>{
    return confirmModal({title:'清空回收站',body:'回收站中的全部文件和馆藏记录将永久删除，无法恢复。',confirmLabel:'清空回收站',danger:true,onConfirm:async()=>{

    try{
      const r=await api('/api/trash/empty',{method:'POST'});
      /* 删不掉的文件（占用中、网盘离线）会连同账本行一起留在回收站，必须说出来，
         否则用户看到条目还在会以为清空又没生效。 */
      if(r.blocked&&r.blocked.length)throw new Error(`已永久删除 ${r.purged} 项；${r.blocked.length} 项未能删除，仍在回收站：\n`
        +r.blocked.slice(0,5).map(x=>`${x.path}（${x.reason}）`).join('\n'));
      actionReceipt(`已永久删除 ${r.purged} 项`);
    }finally{await loadCatalog()}
  }});
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
const COMBO_LABELS={creator:'创作者',studio:'厂牌',owner:'归属'};
/* 生效的筛选一颗一颗列出来：先是创作者、厂牌与归属这几条整项的，再是叠加的标签。目录那条
   （`catalog-filter` 岛）与资料页那条（`entity-filter` 岛）拿同一份清单画。 */
function comboItems(filters){
  const items=[];
  if(filters.creator)items.push({kind:'clear',key:'creator',label:`${COMBO_LABELS.creator} ${filters.creator}`});
  if(filters.studio)items.push({kind:'clear',key:'studio',label:`${COMBO_LABELS.studio} ${filters.studio}`});
  if(filters.owner==='none')items.push({kind:'clear',key:'owner',label:`${COMBO_LABELS.owner} 未归属`});
  tagList(filters.tag).forEach(t=>items.push({kind:'untag',key:t,label:tagLabel(t)}));
  return items;
}
/* 资料页有自己的一条，挂在这一页的玻璃浮层正上方，所指的是这一页的筛选；目录那条这时
   跟目录一起被盖住。两条是同一样东西，清单、组件和落点都共用。 */
function renderCombo(){
  paintCatalogFilter({combo:comboItems(state),comboHidden:!catalogOnScreen()});
}
/* 盖住目录的整页入口当场收起目录那条。筛选条还没挂过时没有东西可收。 */
const hideCatalogCombo=()=>{if(catalogFilterProps)paintCatalogFilter({comboHidden:true})};

/* ── 统计与管理 ── */
/* 账本只读时铺在复核页与关注管理页顶上的那一条，用的就是 Note，不另画一只框：
   图标、文字和底色要出自同一个色调，自己描一圈暖色边再把字写成 --ink 的话，
   背景说的是「注意」、字说的是「普通说明」，两句话对不上。

   色调跟着成因走：另一台机器持有写入权是正常分工，只是说明现状，走中性档；
   冲突要人照日志处理，属于必须先被看见的故障，走 warning。恢复动作在另一台
   机器上，所以是链接不是按钮。 */
function ledgerGateNote(runtime,message,actionLabel,actionHref){
  return noteHtml(message,{variant:runtime?.ledger_sync==='conflict'?'warning':'secondary',
    className:'runtimegate',actionLabel:actionHref?actionLabel:'',actionHref});
}
/* 整页视图接管页面主体。

   这段六行的显隐此前在八个入口里各抄了一份，每份还带着随手的小差异：空格、顺序、
   是 `buildManageBar()` 还是隐藏管理条再 `buildEdge()`。抄一次就多一次漏行的机会——
   关注、播放列表、复核三个页面漏掉筛选芯片，就是从抄 `enterManagementSurface` 抄漏
   开始的，那次漏的是「离开目录」这一半，这里是「铺开新页面」的另一半。

   两个函数不合并，是因为调用时机真的不同：`enterManagementSurface` 必须在任何 await
   之前跑（`loadRequestSeq++` 要抢在在途的目录请求之前作废它），而主体有的入口在取数
   前铺（配 `placeholder` 给反馈），有的在取数后铺（数据快时不闪一下骨架）。
   两个都要调，由 `test_every_full_page_view_enters_through_the_shared_helpers` 兜住。 */
function skeletonKeyOf(html){return String(html).match(/data-skeleton="([^"]*)"/)?.[1]||''}
function showManagementBody({manage=true,placeholder=''}={}){
  $('#stats').hidden=false;$('#index').hidden=true;clearCatalogGrid();
  $('#count').textContent='';$('#loadSentinel').hidden=true;
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
function enterManagementSurface(){
  // A catalog request started before browser Back must not repaint filters over
  // the management page after it resolves.
  loadRequestSeq++;hideCatalogCombo();
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
  const ui=await import('/dist/peach-ui.js');
  /* 点一个内容标签是「回目录并按它筛选」：整页换成目录仍归遗留壳，页面只说点了哪个键。 */
  await ui.mountIsland('stats',$('#stats'),{
    tagLabel,onTag:k=>{closeStats();toggleTag(k)},
    openMediaSettings:()=>openConfigurationSection('媒体'),configurable:!!runtimeConfigurable,
  },{isCurrent:()=>surfaceCurrent(surface)});
  window.scrollTo({top:0,behavior:'smooth'});
}
function showHomeSurfaces(){
  // 两个类都要清：只清 entity-open 会让从索引页回首页时顶栏一直空着，
  // 而且下面那一行 style.display='' 恢复不了被 class 隐藏的元素。
  document.body.classList.remove('entity-open','index-open');
  /* 索引页和资料页都画进 #index，两条路都先经过这里再 `innerHTML=`：直接盖掉的话，
     上一页挂在里面的 React 根（换头像）就没人卸，留着一棵管着已经不在页面上的节点的根。 */
  unmountIsland($('#index'));
  $('#stats').hidden=true;$('#index').hidden=true;
  if(!isFeedNewPath(location.pathname))$('#feedNew').hidden=true;
  $('#catalogFilter').style.display='';syncCatalogFilterScreen();
  buildManageBar();paintListTitle();   // 放在最后：管理区要盖掉上面刚恢复的首页横条
}
function closeStats(push=true){if(push)route('/');showHomeSurfaces();loadCatalog()}

/* 未入库的新作：订阅源发现的番号，库里还没有文件（ADR-0042）。
 *
 * 这一块和网格里的卡片说的不是同一件事——那些是本机有文件的作品，这些只是「外面出了
 * 这一部」。所以它自己一行，卡片上不出时长、大小、来源徽章：那几个读数对一条还没有
 * 文件的番号全是空的，照着资产卡画会让人以为点开能看。这一行不另起标题：它就排在
 * 筛选栏下面、作品网格上面，卡片的形状和那枚外链已经说清楚它是什么。
 *
 * 落点用发现时那条地址，不另拼。JavDB 演员页那类源给的就是作品页 `/v/…`，而按番号拼
 * 搜索地址是把「这是哪一部」交给站内检索去猜——缺 id 就不给入口，全站同一条规矩。 */
/* 封面和资产卡同一套取景：取资料那一轮把封面装进本机封面目录，书脊折痕与人脸位置
   随它落在边车里，这里照 `coverImage` 读出来。还没装上的只有来源给的地址，没有边车，
   `coverAnchor` 按图片自己的宽高比认出封套，`data-panel-prior` 让它按正封先验比例切，
   不带进书脊，也不留上下黑边。 */
function feedNewCoverHtml(item){
  if(item.has_cover)return coverImage(item,'big');
  if(!item.cover_url)return '<span class="nopic">无封面</span>';
  return coverImage({code:item.code},'big').replace(/ src="[^"]*"/,
    ` src="${esc(item.cover_url)}" referrerpolicy="no-referrer" data-panel-prior="1"`);
}
function feedNewCardHtml(item){
  // 女优名与发行日各占一段：订阅按人订，底行说是谁的新片；放不下时只收女优名，日期整段留着。
  const label=[item.performers&&`<span class="feednewperformers">${esc(item.performers)}</span>`,
    item.release_date&&`<span>${esc(item.release_date)}</span>`].filter(Boolean)
    .join('<span aria-hidden="true">·</span>');
  const cover=feedNewCoverHtml(item);
  // 番号与标题排在同一个两行的标题块里，和资产卡一样：番号加粗打头，标题接在后面截断。
  const heading=javTitleHtml({is_jav:true,code:item.code,name:item.code,display_title:item.title||''});
  /* 点击区自己一个类，不共用 `.cardopenhit`：那一个是「在 Peach 里打开这条」的落点，
     全站按它认站内跳转（`test_follow_web` 盯着它不许变成外链）。这一条通向别人的站。 */
  const open=item.link
    ?`<a class="feednewopen" href="${esc(item.link)}" target="_blank" rel="noreferrer" aria-label="打开 ${esc(item.code)} 的作品页"></a>`:'';
  return `<article class="card feednewcard${item.read?' isread':''}" data-feed-id="${item.id}">
    ${open}<div class="pic" style="--card-ratio:${COVER_FRONT_RATIO}">${cover}
      <div class="hovertools feednewtools">
        <button type="button" data-feed-action="ignore" title="不想看" aria-label="不想看 ${esc(item.code)}">${icon('x')}</button>
        <button type="button" data-feed-action="read" title="标为已看过" aria-label="标为已看过 ${esc(item.code)}">${icon('check')}</button></div></div>
    <div class="meta"><div class="mtext"><span class="t">${heading}</span>
      <div class="s mono">${label||(item.title?'':'资料还没取到')}</div></div></div></article>`;
}

/* 订阅了这位时，新作那一行先按真卡的轮廓占住位置：取数回来再整行换掉，没有就收起。
   不占的话，那一行在资料卡和作品之间凭空插进来，把下面整个作品网格往下推一截。
   封面格直接挂 `imgwait`，微光与真卡等封面时是同一层。 */
const FEED_SKELETON_CARDS=8;
const feedNewSkeletonHtml=()=>`<div class="feednewrow srow" aria-hidden="true">${
  `<article class="card feednewcard feednewskeleton"><div class="pic imgwait" style="--card-ratio:${COVER_FRONT_RATIO}"></div>
    <div class="meta"><div class="mtext"><span class="t"><span class="skeleton"></span></span>
      <div class="s mono"><span class="skeleton">&#8203;</span></div></div></div></article>`
    .repeat(FEED_SKELETON_CARDS)}</div>`;
/* 资料页上可有可无的两块——新作那一行（`feed`）和卡底的同台艺人（`costars`）——哪几位
   有，名单由服务端给（`/api/entity/shapes`），几台设备看到的是同一份。页面一启动就取，
   第一次进资料页时骨架已经照它画成最终的形状，资料回来时哪一块都不从中间顶进来。 */
let entityShapes=null;
async function loadEntityShapes(){
  const data=await api('/api/entity/shapes').catch(()=>null);
  if(data&&!data.error){
    entityShapes=new Map((data.entities||[])
      .flatMap(entity=>entity.names.map(name=>[`${entity.kind}/${foldName(name)}`,entity.parts])));
    if(typeof data.home?.feed==='boolean')homeHasFeed=data.home.feed;
    if(isFeedNewPath(location.pathname))prepareHomeFeed($('#feedNew'));
  }
  return entityShapes;
}
function prepareHomeFeed(host){
  // 岛一挂上，宿主就归它：骨架只在挂载之前铺，之后由岛画的那一行或空着说话。
  if(!host||islandMounted(host)||host.querySelector('[data-feed-id]'))return;
  host.hidden=homeHasFeed!==true;
  if(homeHasFeed!==true)return;
  host.setAttribute('aria-busy','true');
  if(!host.querySelector('.feednewskeleton'))host.innerHTML=feedNewSkeletonHtml();
}
const hasEntityPart=(kind,name,part)=>!!name&&!!entityShapes?.get(`${kind}/${foldName(name)}`)?.includes(part);
const feedNewSkeletonSection=()=>`<section class="feednew">${feedNewSkeletonHtml()}</section>`;
const COSTAR_SKELETON_PEOPLE=12;
const costarSkeletonFoot=()=>`<div class="entityfoot"><div class="relatedpeople">${
  '<span class="av avskeleton"><span class="ring"></span><span class="nm">&#8203;</span></span>'
    .repeat(COSTAR_SKELETON_PEOPLE)}</div></div>`;
/* 资料表在骨架里占满五行：名单只说她有没有资料表，不说有几项，按最常见的五项都有留位。 */
const factsSkeleton=()=>`<dl class="entityfacts">${
  '<dt><span class="skeleton"></span></dt><dd><span class="skeleton"></span></dd>'.repeat(5)}</dl>`;

/* 最近一轮取封面断在连接上、这一行又还有没封面的卡时，行上方挂一条 Note 指去配连接方式。
   中国移动宽带直连 DMM 图片主机大多在握手后被断开，官方其实有图；不说清楚的话，一排
   「无封面」看起来就像官方没出。 */
function feedNetworkNote(unreachable,items){
  if(!(unreachable>0)||!items.some(item=>!item.has_cover))return '';
  return noteHtml(`${unreachable} 部新作的封面连不上 DMM 图片主机，中国移动宽带常见。把 DMM / FANZA 的连接方式设成 Peach 代理，下一轮会自动重取。`,
    {variant:'warning',className:'feednetwork',actionLabel:'配置连接方式',actionHref:'/scraping'});
}
/* 新作那一行的整段 HTML：首页那一行与资料页那一行同一份。 */
function feedRowHtml(data){
  const items=data&&!data.error?(data.items||[]):[];
  return feedNetworkNote(data?.cover_network,items)
    +`<div class="feednewrow srow">${items.map(feedNewCardHtml).join('')}</div>`;
}
/* 新作那一行：拖动、滚轮，按设置接自动滚动。首页与资料页两行同一份。 */
function wireFeedNewRow(row){
  if(!row)return;
  wireDrag(row);
  if(appSettings.feedAutoScroll)wireAutoScroll(row);
}
/* 首页那一行归 `feed-new` 岛（`frontend/src/react/feed-new/`），与资料页那一行同一个组件、同一族
   查询键：取数、换掉骨架、卡上那两颗键都在岛里。壳留骨架、宿主和它什么时候在场。
   合集开关改了、或人在目录页里换了一次筛选，都换一个代次推过去，岛见它变了就重取；资料页那
   一行收的是同一个代次。 */
function isFeedNewPath(path){return isCatalogPath(path)&&path!=='/junk-files'}
/* 处理横幅同样只挂在首页那几条名单上。垃圾文件也是目录路径，但它是数据管理底下的一页，
   顶上是管理区的 tabs，库里那趟任务的进度与下场归数据管理首页那张卡。 */
function isProcessingNoticePath(path){return isCatalogPath(path)&&path!=='/junk-files'}
let feedRevision=0;
const feedNewHelpers={feedRowHtml,wireFeedRow:row=>wireFeedNewRow(row)};
const feedNewActions={settled:hasItems=>{homeHasFeed=hasItems}};
function renderHomeFeed(){
  const host=$('#feedNew');
  if(islandMounted(host)){updateIsland(host,{revision:++feedRevision});return}
  prepareHomeFeed(host);
  /* 这一行不随筛选变，判在不在场只看路径：换筛选换掉的是目录的代次，不该把它这一趟作废。 */
  void mountIsland('feed-new',host,{host,revision:feedRevision,helpers:feedNewHelpers,actions:feedNewActions},
    {isCurrent:()=>isFeedNewPath(location.pathname)});
}
/* 离开目录页时收起并清空，连同它的自动滚动一起停掉。岛还没画出来时宿主里是骨架，一起清。 */
function clearHomeFeed(){
  const host=$('#feedNew');
  host.querySelectorAll('.feednewrow').forEach(stopAutoScroll);
  unmountIsland(host);
  host.hidden=true;host.innerHTML='';host.removeAttribute('aria-busy');
}
function refreshFeedRows(){
  feedRevision+=1;
  // 首页那一行只在目录页挂着，人不在那儿时 `updateIsland` 是空操作，不会在别的页面上冒出来。
  updateIsland($('#feedNew'),{revision:feedRevision});
  pushEntityPage({feedRevision});
}
/* 设置里开关自动滚动，页面上已经摆着的那几行当场跟着停或走，不等下一次重画。 */
function syncFeedAutoScroll(){
  document.querySelectorAll('.feednewrow').forEach(row=>
    appSettings.feedAutoScroll?wireAutoScroll(row):stopAutoScroll(row));
}

/* 资料卡排不排三栏看 `#index` 自己有多宽（判据与原因见 07-entity.css 那条规则）。
   量的是常驻的内容区，骨架和画好的页头读同一个开关，换页时不跳一次。 */
const HERO_WIDE_PX=900;
function syncHeroWide([entry]){
  $('#index').toggleAttribute('data-hero-wide',entry.contentRect.width>=HERO_WIDE_PX);
}
new ResizeObserver(syncHeroWide).observe($('#index'));

/* 旧直达 URL 仍然可用，落点跟着面板一起搬到数据管理。 */
async function openResourceSync(push=true){
  if(push||location.pathname==='/resource-sync')route('/data-cleanup#resource-sync',!push);
  await openDataCleanup(false);
  $('#resource-sync')?.scrollIntoView({block:'start'});
}

/* 点一条口味名次：标签是「回目录并按它筛选」，人名直接进资料页。整页换成哪一屏
   仍归遗留壳，React 档只说点了哪一条。 */
function openTasteSignal(kind,name){
  if(kind==='tag'){
    state={...state,tag:name,tag_match:'all',creator:'',studio:'',q:'',state:'',orient:''};
    clearSearchField();route(homePath());showHomeSurfaces();buildBars();loadCatalog();return
  }
  openEntity(kind,name);
}
async function openTaste(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  state={...state,creator:'',studio:'',tag:'',tag_match:'all',len:'',dur_min:'',dur_max:'',orient:'',region:'',state:'',q:'',jav:''};
  clearSearchField();
  if(push)route('/taste');
  const surface=claimSurface('/taste');
  showManagementBody({placeholder:managementPlaceholder('/taste')});
  const ui=await import('/dist/peach-ui.js');
  /* 总结里的下一步动作按路径走，派发仍旧交给 ROUTES：在 React 档里比对一遍路径字符串，
     就又多出一处会和那张表不一致的知识。 */
  await ui.mountIsland('taste',$('#stats'),{
    onSignal:openTasteSignal,navigate:path=>{route(path);restoreRoute()},
    toast:actionReceipt,avatarInner,
    onboarding:claimSetupEntry(),
  },{isCurrent:()=>surfaceCurrent(surface)});
  window.scrollTo({top:0,behavior:'smooth'});
}

const playlistWrite=body=>api('/api/playlist',{method:'POST',body:JSON.stringify(body)});
/* 播放列表的三个弹层都是「填一份表交上去」，所以穿的是 Geist Modal 那身：标题是
   20px/26px 的 h3，正文一律 20px 内边距，操作条粘在底、两端对齐，保存在右下角。
   壳只有 formModal 这一份，上下不会各有一套内边距。 */
function playlistNameField(value=''){
  return `<label class="modalfield"><span>名称</span><input class="geist-input" name="name"
    maxlength="80" placeholder="输入名称" value="${esc(value)}"></label>`;
}
/* 保存 Mix：详情岛递来标题、条数和写库那一下（`save`），存好了转去那份播放列表并给撤销。 */
async function saveMixAsPlaylist({title,count,save}){
  const modal=formModal({
    title:'保存为播放列表',
    description:`这个 Mix 的 ${count} 个视频会存成一份可以继续播放的列表。`,
    body:playlistNameField(title),
    confirmLabel:'保存为播放列表',
    onConfirm:()=>{
      const name=modal.dialog.querySelector('[name="name"]').value.trim();
      if(!name)throw new Error('播放列表名称不能为空');
      return save(name);
    }});
  modal.dialog.querySelector('[name="name"]').select();
  const {confirmed,result}=await modal.done;
  if(!confirmed)return;
  await openPlaylist(result.id,result.current_asset_id,true);
  actionReceipt('已保存为播放列表',{undo:async()=>{
    await playlistWrite({action:'delete',id:result.id});await openPlaylists(true);
  }});
}
/* 一次能勾好几份列表：此前一行就是一个按钮，点下去当场写库、弹层立刻关掉，
   想加进两份就得把整个流程再走一遍。行前的勾选框是选择，右下角的保存才是提交。 */
async function openAddToPlaylist(item){
  const lists=(await api('/api/playlists')).items||[];
  const rows=lists.map(list=>`<label class="pickrow">${checkboxHtml(`data-pick-playlist="${list.id}"`)}
    <span class="pickrowtext"><b>${esc(list.name)}</b><small>${list.item_count} 个视频</small></span></label>`).join('');
  const modal=formModal({
    title:'加入播放列表',
    description:'勾选要加入的列表，或者填个名称新建一份。',
    body:playlistNameField()+(rows
      ?`<div class="picklist" role="group" aria-label="已有播放列表">${rows}</div>`
      :noteHtml('还没有播放列表，填个名称就能新建一份。',{size:'small'})),
    confirmLabel:'保存',
    confirmDisabled:true,
    onConfirm:async()=>{
      const name=modal.dialog.querySelector('[name="name"]').value.trim();
      const chosen=[...modal.dialog.querySelectorAll('[data-pick-playlist]:checked')]
        .map(box=>+box.dataset.pickPlaylist);
      const created=name
        ?(await playlistWrite({action:'create',name,asset_ids:[item.id]})).playlist:null;
      for(const id of chosen)await playlistWrite({action:'add',id,asset_ids:[item.id]});
      return {created,added:chosen};
    }});
  const sync=()=>{
    const name=modal.dialog.querySelector('[name="name"]').value.trim();
    modal.confirmButton.disabled=!name&&!modal.dialog.querySelector('[data-pick-playlist]:checked');
  };
  modal.dialog.addEventListener('input',sync);
  modal.dialog.addEventListener('change',sync);
  const {confirmed,result}=await modal.done;
  if(!confirmed)return;
  const total=(result.created?1:0)+result.added.length;
  actionReceipt(`已加入 ${total} 个播放列表`,{undo:async()=>{
    for(const id of result.added)await playlistWrite({action:'remove',id,asset_id:item.id});
    if(result.created)await playlistWrite({action:'delete',id:result.created.id});
  }});
}
/* 播放列表页整个归 React 子树（ADR-0031）：取数、卡面、新建改名删除都在 /dist/peach-ui.js 里。
   壳只铺骨架，交出打开队列、资料页、头像 HTML、翻页门槛与回执。
   已经停在这一页、岛还挂着时要求重读（顶栏「换一批」、从播放队列返回、撤销后），
   推一个刷新代次让页面重取，不重挂：重挂会先铺一遍骨架，卡片与滚动位置都跟着闪。 */
let playlistsSurface=null,playlistsRevision=0;
async function openPlaylists(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/playlists');
  if(!push&&playlistsSurface&&surfaceCurrent(playlistsSurface)&&islandMounted($('#stats'))){
    showManagementBody({manage:false});
    updateIsland($('#stats'),{revision:++playlistsRevision});
    return;
  }
  const surface=claimSurface('/playlists');
  showManagementBody({manage:false,placeholder:managementPlaceholder('/playlists')});
  const ui=await import('/dist/peach-ui.js');
  if(!surfaceCurrent(surface))return;
  const props={
    openPlaylist:(id,resume)=>openPlaylist(id,resume,true),openEntity,
    faceAvatar:face=>avatarInner(face.name,face,REP[face.name],face.kind),
    canFlip:()=>!selectMode&&!censorOn()&&!window.__scrolling&&!reduceMotion(),
    toast:(message,{undo}={})=>actionReceipt(message,{undo}),revision:playlistsRevision,
  };
  playlistsSurface=surface;
  await ui.mountIsland('playlists',$('#stats'),props,{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface))window.scrollTo({top:0,behavior:'smooth'});
}

/* 数据管理是「库里已经有的东西怎么收拾」的唯一入口：广告、重复、失效条目，
   加上复核队列、回收站和高清版。整页归 React 子树（ADR-0031），遗留层只铺骨架、
   交出回执与换页；读数卡通往的那几页仍归遗留路由。 */
async function openDataCleanup(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/data-cleanup');
  const surface=claimSurface('/data-cleanup');
  showManagementBody({placeholder:managementPlaceholder('/data-cleanup')});
  paintManageLede();
  const ui=await import('/dist/peach-ui.js');
  if(!surfaceCurrent(surface))return;
  /* 重复文件报数据管理的身份，`openManage('duplicates')` 找不到它自己的 section。 */
  const props={toast:(message,{warning=false}={})=>warning?toast({text:message},{sound:'warning'}):actionReceipt(message),
    failure:actionFailure,open:section=>section==='duplicates'?openDuplicates():openManage(section)};
  await ui.mountIsland('data-cleanup',$('#stats'),props,{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface)&&location.hash==='#libraryProcessing')$('#libraryProcessing')?.scrollIntoView({block:'start'});
}

/* 重复文件。判据是「同番号 + 时长相近 + 分卷标记一致」，不是同番号即重复；整页归 React
   子树（ADR-0031），批量一律走 dispose 进回收站，永久删除仍只能从回收站单独执行。 */
async function openDuplicates(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/duplicates');
  const surface=claimSurface('/duplicates');
  showManagementBody({placeholder:managementPlaceholder('/duplicates')});
  paintManageLede();
  const ui=await import('/dist/peach-ui.js');
  if(!surfaceCurrent(surface))return;
  const props={openItem,failure:actionFailure,toast:(message,{undo}={})=>actionReceipt(message,{undo})};
  await ui.mountIsland('duplicates',$('#stats'),props,{isCurrent:()=>surfaceCurrent(surface)});
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
/* 复核页的分类进地址栏：十个分类是固定的一组身份，「在看哪一条队列」链接得过来，
   刷新也要还原。分组、筛选与页码不进——队列是消耗性的，判一条就少一条，第 3 页
   指的是哪二十行随每一次判定而变，分享出去只会指向另一批东西。 */
function reviewParams(){
  const category=new URLSearchParams(location.search).get('category')||'';
  return {category:Object.hasOwn(REVIEW_LABELS,category)?category:''};
}
function routeReview(params){
  route('/review'+(params.category?'?category='+encodeURIComponent(params.category):''));
}
async function openReview(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  const params=reviewParams();
  // 从窄栏点进来是「重新进入」：回到默认那一档分类。
  if(push){params.category='';routeReview(params)}
  const surface=claimSurface('/review');
  showManagementBody({placeholder:managementPlaceholder('/review')});
  const [ui,runtime]=await Promise.all([
    import('/dist/peach-ui.js'),surfaceApi(surface,'/healthz')]);
  if(!surfaceCurrent(surface))return;
  const writer=runtime?.ledger_writer_origin
    ?new URL('/review',runtime.ledger_writer_origin).href:'';
  await ui.mountIsland('review',$('#stats'),{...params,
    route:routeReview,
    openItem:id=>void openItem(id),
    openEntity:(kind,name)=>void openEntity(kind,name),
    revealSource:revealForIsland,
    avatarInner,toast:actionReceipt,
    readOnly:!!runtime?.ledger_read_only,
    readOnlyMessage:runtime?.ledger_read_only_message||'本机当前只能浏览',
    writerUrl:writer,
  },{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface))window.scrollTo({top:0,behavior:'smooth'});
}
/* 活动页（任务中心）也是 island。它自己按内容决定轮询快慢，遗留层不给它任何助手：
   这一屏只显示 /api/tasks 的结果，不打开条目、不发起任务。 */
async function openActivity(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/activity');
  const surface=claimSurface('/activity');
  showManagementBody({placeholder:managementPlaceholder('/activity')});
  const ui=await import('/dist/peach-ui.js');
  await ui.mountIsland('activity',$('#stats'),{},{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface))window.scrollTo({top:0,behavior:'smooth'});
}
/* 配置页（这台电脑的媒体文件夹与端口）同样是 island。它只在运行 Peach 的这台电脑上
   有意义：服务端按回环地址与独立包两道门放行，手机上的管理菜单也不列它
   （见 runtimeConfigurable）。保存成功的回执由遗留层的 Toast 发，island 只管表单。 */
/* 配置页要选中的那一组页签名。页签由 `decorate` 按 `.configgroup` 切出来，它读这个名字
   选中对应的那一格，选中之后清空。 */
let configurationRequestedSection='';
async function openConfiguration(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/configuration');
  const surface=claimSurface('/configuration');
  showManagementBody({placeholder:managementPlaceholder('/configuration')});
  if(location.hash==='#peachProxy')configurationRequestedSection='网络与访问';
  const ui=await import('/dist/peach-ui.js');
  const props={receipt:message=>actionReceipt(message),reopenTutorial:reopenPostSetupTutorial};
  await ui.mountIsland('configuration',$('#stats'),props,{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface)){
    if(location.hash==='#libraryProcessing'){history.replaceState(null,'','/data-cleanup#libraryProcessing');await openDataCleanup(false);return}
    if(location.hash==='#peachProxy')$('#peachProxy')?.scrollIntoView({block:'start'});
    else window.scrollTo({top:0,behavior:'smooth'});
  }
}
/* 从别处点「管理媒体库」「添加媒体文件夹」进来：落到配置页并直接选中那一组页签。 */
function openConfigurationSection(section){
  configurationRequestedSection=section;
  void openConfiguration(true);
}

async function openScraping(push=true){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  if(push)route('/scraping');
  const surface=claimSurface('/scraping');
  /* 占位取共用那一份：这里另写一张时，整页刷新会先画深链启动那张、再画这一张，
     同一段 shimmer 连放两遍。标题由 paintManageTitle 按 MANAGE_CRUMB_PAGES 认，
     不在这里再赋一次值。 */
  showManagementBody({placeholder:managementPlaceholder('/scraping')});
  const ui=await import('/dist/peach-ui.js');
  await ui.mountIsland('scraping',$('#stats'),{toast},{isCurrent:()=>surfaceCurrent(surface)});
}

/* ── 在线追更 ──
   两个页面，因为是两件事：
   - `/follow`（左侧导航）是**看**：一张卡片一个作品，点开就去看。本站的 alt 与 WIP
     折进卡片内部，跨站的同一作品折成「另见」，24 条抓取记录才读成 20 个作品。
   - `/follow-manage`（管理区）是**管**：加来源、检查更新、移除来源、看凭据状态，
     以及对内容做批量标记。
   联网只发生在管理页点「检查更新」的那一刻——看的那一页不联网。 */
/* 这一次进入的取样种子：创作者、题材、标签三排露出哪些由它定，岛按它取样（`randomOrder`）。 */
let followDiscoverySeed=Math.floor(Math.random()*0xffffffff);
/* 关注页一次取一屏。counts 是全库口径（「未看 2292」），groups 只有这一页——
   两个数并排显示时看起来像自相矛盾，实际是两个口径，所以列表底部要能继续加载。 */
const FOLLOW_PAGE=300;
/* 创作者、来源和标签一起交给服务端。只让状态走服务端、这三个在浏览器里筛的话，
   药丸上的数字（全库口径）和列表（筛过的这几页）就是两套口径，换个筛选条件
   数字纹丝不动；而且选个冷门创作者，一页 300 条里可能只剩两条，得反复点加载更多。 */
const followPageUrl=offset=>
  `/api/follow?limit=${FOLLOW_PAGE}&offset=${offset}`
  +(followFilter?`&status=${followFilter}`:'')
  +(followAuthors.size?`&author=${encodeURIComponent([...followAuthors].join(','))}`:'')
  +(followProviders.size?`&provider=${encodeURIComponent([...followProviders].join(','))}`:'')
  +(followTags.size?`&tag=${encodeURIComponent([...followTags].join(','))}`:'')
  +(followWorks.size?`&work=${encodeURIComponent([...followWorks].join(','))}`:'')
  /* 排序也归服务端，理由同上：分页在它那一侧。浏览器只拿到当前这几页，在这里排
     等于每加载一页就把先后顺序重算一次，越往下翻越乱。 */
  +(followSort!=='new'?`&sort=${followSort}`:'')
  +(followSort===FOLLOW_RANDOM_SORT?`&seed=${followSeed}`:'')
  +(followDir!=='desc'?`&dir=${followDir}`:'');
/* 这一排是「现在看的哪一档」。已看那一档不摆出来：看过就归档，要再翻出来是「全部」
   的事，而一枚常年指向十几条的筛选占的是这一排最值钱的横向空间。状态本身照旧记，
   卡片和详情面板上都还能把一条标成已看。 */
const FOLLOW_FILTERS=[['','全部'],['new','未看'],['saved','已保存'],['ignored','已忽略']];

/* 卡片、详情、筛选条和在线标签页都只消费服务端的内容标签投影。过滤只维护一份，
   原始来源标签仍完整留在 metadata。 */
const followCardTags=item=>item.tags||[];

/* 检查完必须说清三件事：新增了什么、哪些确实没有更新、哪些失败了以及为什么。
   反馈走两条通道（Geist toast 处方，取证见 docs/reference-snapshots/vercel-geist-toast.md）：
   「检查了 N 个来源」是用户主动动作的非阻塞回执 → toast，自动消失；
   失败是「不跟进就会一直漏更新」的事 → 摘要里只留一句短提示，原因和恢复入口放进
   页内的持久行，关掉 toast 也还在：看的那一页是 `.fwarn`，管理页那一份归 React 的
   `Note`（`follow-manage/source-list.tsx`）。 */
function followCheckBits(report){
  const rows=report.results||[];
  const added=rows.reduce((n,r)=>n+(r.added||0),0);
  const updated=rows.reduce((n,r)=>n+(r.updated||0),0);
  const quiet=rows.filter(r=>r.ok&&!r.added&&!r.updated).length;
  const skipped=rows.reduce((n,r)=>n+(r.skipped||0),0);
  const compilations=rows.reduce((n,r)=>n+(r.skipped_compilations||0),0);
  const history=rows.reduce((n,r)=>n+(r.history_skipped||0),0);
  const bits=[];
  if(added)bits.push(`新增 <b>${added}</b> 条`);
  if(updated)bits.push(`更新 <b>${updated}</b> 条`);
  // 过滤掉多少也要说：不然用户只看到条目变少，分不清是被过滤了还是根本没抓到。
  if(skipped-compilations)bits.push(`跳过 <b>${skipped-compilations}</b> 条无资源`);
  if(compilations)bits.push(`排除 <b>${compilations}</b> 个超大合集`);
  if(history)bits.push(`跳过 <b>${history}</b> 条超出首次采集范围的历史内容`);
  // 回查是唯一会放大请求数的路径，报出来才看得出某个创作者是不是每帖都要多打一次站点。
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
    {warn:!!failed,timeout:failed?8000:6000,sound:failed?'warning':'success',
     action:{label:'去看更新',run:()=>openFollow()}});
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
  if(followAuthors.size)params.set('author',[...followAuthors].join(','));
  if(followProviders.size)params.set('provider',[...followProviders].join(','));
  if(followTags.size)params.set('tag',[...followTags].join(','));
  if(followWorks.size)params.set('work',[...followWorks].join(','));
  if(followFilter)params.set('status',followFilter);
  if(followMediaView==='images')params.set('media','images');
  // 默认那一档不写进地址：`/follow` 本身就是「按更新时间从新到旧」。
  if(followSort!=='new')params.set('sort',followSort);
  if(followSort===FOLLOW_RANDOM_SORT)params.set('seed',String(followSeed));
  if(followDir!=='desc')params.set('dir',followDir);
  const search=params.toString();return '/follow'+(search?'?'+search:'');
}
function readFollowView(){
  const params=new URLSearchParams(location.search);
  const csv=key=>new Set((params.get(key)||'').split(',').filter(Boolean));
  // 作者、来源、题材一维只按着一个；旧链接里逗号连着的几个取第一个。
  const one=key=>new Set([...csv(key)].slice(0,1));
  followAuthors=one('author');
  followProviders=one('provider');
  followTags=csv('tag');
  followWorks=one('work');
  const status=params.get('status');
  // 这一排上没有的那一档按「全部」读：旧链接里的 `status=seen` 落在这一条上，
  // 否则页面停在一个没有任何药丸按下去的筛选里，看不出自己正被什么筛着。
  followFilter=FOLLOW_FILTERS.some(([key])=>key&&key===status)?status:'';
  followMediaView=params.get('media')==='images'?'images':'videos';
  // 认不出的键退回默认那一档，同上一条的道理：不能停在一个没有任何键按下去的排序上。
  const sort=params.get('sort');
  followSort=sort===FOLLOW_RANDOM_SORT||FOLLOW_FEED_SORTS.some(([key])=>key===sort)?sort:'new';
  // 地址里没带种子的随机链接照样能开，只是开出来的是哪一批不保证跟上次一样。
  followSeed=Number(params.get('seed'))>>>0||followSeed||Number(rollSeed());
  followDir=params.get('dir')==='asc'?'asc':'desc';
}
/* 看的那一页整个归 React 岛 `follow-feed`（ADR-0031）：取数、两排、玻璃、列表、写操作、检查
   更新与往回抓都在 /dist/peach-react.js 里。壳只管三样：地址栏（筛选的唯一真相源）、这一次
   进入的取样种子、选择与照片墙这几样全站偏好。侧栏标签抽屉仍在壳里，岛每取到一版列表就经
   `loaded` 交回可见条目的标签计数。

   岛改筛选只调 `route(view)`：这里写进地址栏，再经 `updateIsland` 推回新的 `view`。已经挂着时
   换一档（前进后退、侧栏标签、批量标记之后）也走推送，只有列表铺骨架；重挂会把页头、两排和
   那块玻璃一起先撤掉再画。 */
function followView(){
  return {status:followFilter,media:followMediaView,author:[...followAuthors][0]||'',
    provider:[...followProviders][0]||'',work:[...followWorks][0]||'',tags:[...followTags],
    sort:followSort,dir:followDir,seed:followSeed};
}
function adoptFollowView(view){
  followFilter=view.status;followMediaView=view.media;
  followAuthors=new Set(view.author?[view.author]:[]);
  followProviders=new Set(view.provider?[view.provider]:[]);
  followWorks=new Set(view.work?[view.work]:[]);
  followTags=new Set(view.tags);
  followSort=view.sort;followDir=view.dir;followSeed=view.seed;
}
/* `#stats` 上此刻画着的是不是关注页那座岛：别的页面也挂在这个容器上，推错了就是往播放列表
   里塞一份关注页的 props。 */
function followFeedLive(){return islandMounted($('#stats'))&&!!$('#stats').querySelector('[data-follow-feed]')}
function pushFollowFeed(patch){if(followFeedLive())updateIsland($('#stats'),patch)}
/* 媒体那一档只换分组、不换列表，不滚回顶部；其余换的是整份列表，跟进页一样回到顶上。 */
function routeFollowFeed(view,patch={}){
  const list=followPageUrl(0);
  adoptFollowView(view);route(followViewPath());
  pushFollowFeed({...patch,view:followView()});
  syncPhotoWalls();
  if(followPageUrl(0)!==list)window.scrollTo({top:0,behavior:'smooth'});
}
/* 换一批掷一粒新种子，上面三排的取样和下面列表的次序都读它；排序键上没有「随机」这一档，
   进随机就是三枚键都抬起来，按任一枚就离开。 */
function shuffleFollowFeed(){
  followSeed=Number(rollSeed());followDiscoverySeed=followSeed;
  routeFollowFeed({...followView(),sort:FOLLOW_RANDOM_SORT},{seed:followDiscoverySeed});
}
/* 岛要的助手与动作各只有一份、身份不变：卡片按引用比较，每次推新对象进去就是整屏重画。
   这里只剩要借壳里实现的几样：题材圆标借资料页的取景，标签写法、拖动与横滚、骨架和后台
   任务进度都是壳的那一份；署名、头像、来源图标与标题前后的字样在岛里（`follow-marks.ts`）。 */
const followFeedHelpers={
  workMark:row=>followWorkMark(row),
  tagLabel:tag=>tagLabel(tag),
  wireDrag:row=>{if(row)wireDrag(row)},
  wireScroller:row=>{if(row)wireHorizontalScroller(row)},
  listSkeletonHtml:media=>followContentSkeletonHtml(media),
  jobProgress:options=>followJobProgress(options),
};
const followFeedActions={
  route:view=>routeFollowFeed(view),
  shuffle:()=>shuffleFollowFeed(),
  loaded:tags=>renderFollowDrawer(tags),
  openDetail:id=>openFollowDetail(id),
  openManage:()=>openFollowManage(),
  toggleSelection:(id,range)=>toggleFollowSelection(id,range),
  setImagesOnly:on=>{appSettings.followImagesOnly=!!on;saveSettings();syncPhotoWalls()},
  setPhotoLayout:layout=>{
    appSettings.photoLayout=allowedSetting(layout,['fixed','masonry'],'masonry');saveSettings();syncPhotoWalls()},
  canFlip:()=>!selectMode&&!censorOn()&&!window.__scrolling&&!reduceMotion(),
  toast:(message,{undo}={})=>actionReceipt(message,{undo}),
  failure:(action,error)=>actionFailure(action,error),
  checkReport:report=>followCheckToast(report),
};
const followFeedProps=()=>({view:followView(),seed:followDiscoverySeed,revision:followRevision,
  selectMode,selected:new Set(followSelected),photoSize:photoSize(),photoLayout:photoLayout(),
  imagesOnly:!!appSettings.followImagesOnly,helpers:followFeedHelpers,actions:followFeedActions});

/* 关注详情整块归舞台岛（`frontend/src/react/stage/`）：条目取数、媒体区、队列、侧栏、写操作与
   播放器都在 /dist/peach-react.js 里。壳留来处与地址。换到组里另一条也走这里：舞台上的播放器
   要先拆，地址要换。 */
const followDetailActions={
  close:()=>closeFollowDetail(),
  openItem:(id,mediaIndex=null)=>openFollowDetail(id,true,mediaIndex,true),
  openTag:tag=>{
    if(followTags.has(tag))followTags.delete(tag);else followTags.add(tag);
    // 回到的是带上这枚标签的那一份列表：地址栏是筛选的唯一真相源，只改全局会被推回去。
    followDetailReturnPath=followViewPath();
    closeFollowDetail();
  },
  /* 侧栏标签抽屉跟着画出来的这一条走（这一条自己的标签）。 */
  present:item=>{renderFollowDrawer(sidebarTagCounts([{tags:followCardTags(item)}]))},
  toast:(message,{undo}={})=>actionReceipt(message,{undo}),
  failure:(action,error)=>actionFailure(action,error),
};

async function openFollowDetail(id,push=true,mediaIndex=null,preserveReturn=false){
  releaseHoverPreviews();
  id=+id;
  const entering=!location.pathname.startsWith('/follow/item/');
  if(push&&entering&&!preserveReturn)followDetailReturnPath=location.pathname+location.search;
  if(!push&&!preserveReturn)followDetailReturnPath='/follow';
  // 换详情不进小窗；小窗里放着别的条目也让位（舞台岛判），两个播放器不同时出声。
  disposeStage(false,false,{miniplayer:false});
  if(push)route(`/follow/item/${id}`);
  const stage=await loadStage(stageHost);
  await stage.open({kind:'follow',id,mediaIndex,mediaView:followMediaView,
    helpers:followFeedHelpers,actions:followDetailActions,resume:push?null:urlResume()});
  scheduleStickySurfaces();
}


/* 关掉详情只是回到列表，不该重新取一遍。重取要等一个网络往返（慢），而且只会取回第一页——
   「加载更多」出来的条目会一起消失。列表岛还挂着就只把地址栏上的那一份推回去（没变就是同一个
   键，不重取）；深链直接进的详情没挂过列表，这时才挂。 */
async function closeFollowDetail(){
  await stageExit();
  disposeStage(false,false,{miniplayer:false});
  route(followDetailReturnPath||'/follow');
  if(location.pathname!=='/follow'){await restoreRoute();return}
  if(!followFeedLive()){await openFollow(false);return}
  readFollowView();pushFollowFeed({view:followView()});
}


async function openFollow(push=true,renderForDetail=false){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  /* 从窄栏点进来（push）是「重新进入」，回到干净的 /follow、换一粒取样种子；其余情况一律照
     URL 推导。筛选状态由 URL 推导，不在这里逐个手写重置——漏一个就会让某一维一直按着，
     而它们还决定服务端取哪些条目，等于取错数据。 */
  if(push)followDiscoverySeed=Math.floor(Math.random()*0xffffffff);
  if(push)route('/follow');
  if(location.pathname==='/follow')readFollowView();
  if(followFeedLive()){
    // 详情盖在列表上面：列表原样留着，返回时接着看。
    if(renderForDetail)return;
    showManagementBody({manage:false});
    pushFollowFeed({view:followView(),seed:followDiscoverySeed,revision:++followRevision});
    syncPhotoWalls();
    window.scrollTo({top:0,behavior:'smooth'});
    return;
  }
  if(renderForDetail){
    /* 深链直接进详情：详情岛自己取这一条，列表区只让出位置，岛等回到列表时再挂。侧栏抽屉由
       详情画出来时按这一条的标签铺。 */
    claimSurface(surfacePath());
    showManagementBody({manage:false});
    $('#stats').replaceChildren();
    return;
  }
  const surface=claimSurface('/follow');
  showManagementBody({manage:false,placeholder:followSkeletonHtml('正在读取关注内容')});
  await mountIsland('follow-feed',$('#stats'),followFeedProps(),
    {isCurrent:()=>surfaceCurrent(surface),reveal:revealSkeleton});
  if(surfaceCurrent(surface))window.scrollTo({top:0,behavior:'smooth'});
}

/* 题材那一枚跟首页的厂牌药丸同形：28px 圆标识加作品名。圆里装的是这个题材下最热的
   那几条里第一张看得见脸的封面，服务端按 `work` 这个身份自己去挑再存在本机，页面
   递不进地址。挑不出图的题材（facet 那一行的第四位说了算）直接出两个字母，不出
   `<img>`：无条件出图、靠 404 换回字母的代价是每次重绘都再打一轮，而 404 那条响应
   不可缓存。
   第五位是服务端对那张图检出的取景，和实体图同一个形状，所以挪和放大都走资料页那
   两个函数。放大在这里不是锦上添花：圆标只有 28px，而这是一整张作品图不是烤好边距
   的头像，只挪不放大的话脸在图里占多少、在这枚圆里就占多少，一排看下来仍是身体。
   没检出脸就两样都不写，圆标按样式表里的默认取景摆。 */
function followWorkMark([key,label,,icon,focus]){
  const fallback=esc(String(label||'').slice(0,2));
  return icon?`<img src="/work-icon?work=${encodeURIComponent(key)}" alt="" loading="lazy"${facePos(focus)}${faceBoxAttrs(focus)}>`:fallback;
}

/* ── 管的那一页 ──
   整页归 React（ADR-0031）。遗留层只留外壳：铺骨架、把地址栏上的那几项和这台浏览器的
   偏好交出去，取数、渲染、检查更新那趟后台任务都在 /dist/peach-react.js 里。

   地址栏归这里写，偏好存在 appSettings 里，实时状态在 island 手里——三样东西各只有
   一份。哪几项该进地址栏由 island 说：它把默认值传成空串，这里就不写进去，分享出去的
   地址不会挂一串和默认完全一样的参数。 */
const FOLLOW_MANAGE_TABS=['list','add','feeds','source'];
/* 这两样偏好只有骨架和挂载这两个读者，值都在 appSettings 里。 */
function followListLayout(){return appSettings.followLayout==='table'?'table':'default'}
function followListPageSize(){return Number(appSettings.followPageSize)||20}
function followManageParams(){
  const params=new URLSearchParams(location.search),tab=params.get('tab');
  return {tab:FOLLOW_MANAGE_TABS.includes(tab)?tab:'list',
    page:Math.max(1,Math.floor(Number(params.get('page')))||1),
    sort:params.get('sort')||'',dir:params.get('dir')||''};
}
function routeFollowManage(params){
  const search=new URLSearchParams();
  if(params.tab&&params.tab!=='list')search.set('tab',params.tab);
  if(params.page>1)search.set('page',String(params.page));
  if(params.sort)search.set('sort',params.sort);
  if(params.dir)search.set('dir',params.dir);
  const query=search.toString();
  route('/follow-manage'+(query?'?'+query:''));
}
async function openFollowManage(push=true,workspace=''){
  releaseHoverPreviews();disposeStage(false);enterManagementSurface();
  const params=followManageParams();
  if(workspace)params.tab=workspace;
  // 从窄栏点进来是「重新进入」：回到第一页与默认排序，页签由调用方说。
  if(push){params.page=1;params.sort='';params.dir=''}
  if(push||workspace)routeFollowManage(params);
  const surface=claimSurface('/follow-manage');
  showManagementBody({placeholder:managementPlaceholder('/follow-manage')});
  const [ui,runtime]=await Promise.all([
    import('/dist/peach-ui.js'),surfaceApi(surface,'/healthz')]);
  if(!surfaceCurrent(surface))return;
  const writer=runtime?.ledger_writer_origin
    ?new URL('/follow-manage',runtime.ledger_writer_origin).href:'';
  await ui.mountIsland('follow-manage',$('#stats'),{...params,
    route:routeFollowManage,
    pageSize:followListPageSize(),
    layout:followListLayout(),
    savePreference:patch=>{
      if(patch.pageSize!==undefined)appSettings.followPageSize=patch.pageSize;
      if(patch.layout!==undefined)appSettings.followLayout=patch.layout;
      saveSettings();
    },
    toast:actionReceipt,openFollow:()=>void openFollow(),avatarInner,
    readOnly:!!runtime?.ledger_read_only,
    readOnlyMessage:runtime?.ledger_read_only_message||'本机当前只能浏览',
    writerUrl:writer,
  },{isCurrent:()=>surfaceCurrent(surface)});
  if(surfaceCurrent(surface))window.scrollTo({top:0,behavior:'smooth'});
}
/* 空态里那条「添加关注」：已经在这一页上时也走同一条路，页签跟着地址一起换。 */
document.addEventListener('click',event=>{
  if(event.target.closest?.('[data-empty-settings]')){openConfigurationSection('媒体');return}
  const link=event.target.closest?.('a[href="/follow-manage?tab=add"]');
  if(!link||event.defaultPrevented||event.button||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
  void openFollowManage(true,'add');
});

/* ── 全部艺人 / 创作者 / 厂牌 / 事务所 / 标签索引页 ──
   整页在 React（`frontend/src/react/index/`）。壳做三件事：从地址栏读出这一页的状态、铺骨架、
   把遗留层唯一那一份取图链与去处当 props 递进去。换档（厂牌↔事务所、本地↔在线、类型、视图、
   过滤词）由页面经 `route` 写回地址栏，不经过这里重挂。 */
const INDEX_TITLES={performers:'艺人',creators:'创作者',studios:'厂牌',
                    agencies:'事务所',tags:'标签'};
/* 艺人索引版式，思路同 JAV 大图：列宽不变、只把图从圆框拉成竖幅，一屏里的人数
   不变而每张脸更大；紧凑就是圆头像那一屏。资料页的名册读的是同一个设置值。 */
const PEOPLE_LAYOUTS=[['big','大图 · 竖幅头像','maximize'],['compact','紧凑 · 圆形头像','layout-grid']];
/* 公司那一格摆的是方形标识而不是脸，说法跟着换；档位仍是同一个设置值。 */
const COMPANY_LAYOUTS=[['big','大图 · 完整标识','maximize'],['compact','紧凑 · 圆形标识','layout-grid']];
function peopleIndexLayout(){
  return allowedSetting(appSettings.peopleLayout,PEOPLE_LAYOUTS.map(([k])=>k),'big');
}
/* 一格人的圆框里那段：有图走图、没图退首字母。索引页（React）和资料页名册摆的是同一格，
   所以取图只有这一份。

   公司这一格不退到代表作截图，和它自己的资料页保持同一条判据：那是某部片的画面，
   摆在公司名下就是替它拿别人的脸当门面，同一个厂牌两个页面还会各出各的图。
   公司摆的是标识而不是脸，而两个版式要的不是同一份：180 px 的大格要 `large`（这个厂牌
   手上最清晰的那份）并且允许小图按原尺寸摆，圆框要 `ring`：方标够填满圆框就用方标，
   只有邮票大小的才换最清晰那份，免得圆里只剩一粒糊点。判据在服务端 `_ring_variant`，
   度量在 fitNativeImage 里。

   平移挂在圆框上而不是 img 上：竖幅裁到 3:4 时几何居中会切掉脸，而 img 由八处共用的
   avatarInner 拼，两个版式都只能从容器这一侧改。放大反过来只能挂在 img 上，所以脸框
   穿过 avatarInner 贴到 img 上，两件事各走各的。 */
function personRingHtml(x,kind,big){
  const ref=x.entity_id||x.id;
  const company=kind==='studio'||kind==='agency';
  return avatarInner(x.k,ref?{id:ref,has_image:x.has_image}:null,
    x.has_avatar&&!company?x.rep:null,kind,x.mark,x.has_logo?x.k:'',
    company&&big?'large':'ring',company?null:x.avatar_focus,true);
}
/* 两座岛（索引页、资料页正文的名册）要的那一格头像：圆框里的 HTML 和人脸取景。 */
const personAvatar=(x,entityKind,big)=>({html:personRingHtml(x,entityKind,big),face:faceOrigin(x.avatar_focus)});
/* 在线创作者这一格跟本地艺人同形，差别只在圆里那张图从哪儿来：本地走 `/entity-image`
   那条自家链，在线只有来源站点给的地址，官方主页优先、归档兜底，两条都取不到就落回
   首字母——跟关注页的创作者行同一套判据。 */
function onlineAuthorRingHtml(x){
  const initial=(String(x.k||'').match(/[A-Za-z0-9]/)||[Array.from(String(x.k||''))[0]||'?'])[0].toUpperCase();
  const image=x.avatar?`<img src="${esc(x.avatar)}" alt="" loading="lazy" referrerpolicy="no-referrer" ${
    imageFallbackAttrs({fallbacks:[x.avatar_fallback||'']})}>`:'';
  return `<span class="ini">${esc(initial)}</span>${image}`;
}
/* 地址栏上的那几项。范围与视图只认两个值；类型由页面按这一套词表核对，认不出的回到全部。 */
function indexRoute(kind){
  const params=new URLSearchParams(location.search);
  return {kind,q:params.get('q')||'',scope:params.get('scope')==='online'?'online':'local',
    view:params.get('view')==='cloud'?'cloud':'alphabet',category:params.get('category')||'all'};
}
function indexPath({kind,q,scope,view,category}){
  const params=new URLSearchParams();if(q)params.set('q',q);
  if(kind==='tags'){
    params.set('view',view);
    if(scope==='online')params.set('scope','online');
    if(category!=='all')params.set('category',category)}
  if(kind==='performers'&&scope==='online')params.set('scope','online');
  return '/'+kind+(params.size?'?'+params:'');
}
/* 页头那几样此刻就能给出最终样子：标题、读数的占位、版式开关、过滤框和页面级 Tabs，
   等的只有下面那块内容。React 页取回首屏后整块换掉它，键和文字同页面那一份一致，换的
   那一下页头不跳。这里的控件不接线：骨架只在取数那一段露面。 */
const MAKER_INDEX_KINDS=[['studios','厂牌','clapperboard'],['agencies','事务所','briefcase']];
const INDEX_SCOPES=[['local','本地','hard-drive'],['online','在线','rss']];
const TAG_VIEWS=[['cloud','标签云','tags'],['alphabet','字母表','text-aa']];
/* 标签页 Tabs 下面还有一块两排的筛选玻璃（React 的 `FilterGlassRows`）：上排是类型药丸，
   下排是读数、按首字跳转和视图切换。药丸有哪几枚、读数多少、有哪些首字都要等数据，
   视图切换此刻就是最终那一档；块高与下边距同旧 `.board-filter-frame`，页面落地时它原地
   换成真的那一块，下面的内容不下跳。 */
const tagFilterSkeletonHtml=view=>`<div class="board-filter-frame" data-filter-frame>
    <div class="tagbar" data-filter-row="top" data-skeleton-tier="pill" aria-label="标签类型"></div>
    <div class="count" data-filter-row="bottom"><span class="mono"><span class="countskeleton"></span></span>
      ${iconSwitchHtml('tag-view','标签视图',TAG_VIEWS,view)}</div></div>`;
function indexPlaceholderHtml({kind,q,scope,view}){
  const title=INDEX_TITLES[kind]||'标签',people=kind!=='tags',company=kind==='studios'||kind==='agencies';
  const layout=peopleIndexLayout();
  const tabs=(items,active,label)=>boardTabsHtml(items.map(([value,text,symbol])=>({value,label:text,symbol})),
    {active,label,className:'indextabs'});
  const switcher=people?iconSwitchHtml('people-layout',title+'索引版式',company?COMPANY_LAYOUTS:PEOPLE_LAYOUTS,layout):'';
  return `<div class="ihead">
      <h2 class="disp indexheading">${title}</h2>
      ${people?'<span class="mono" id="indexCount"><span class="countskeleton"></span></span>':''}${switcher}
      ${searchInputHtml({label:'过滤'+title,value:q||''})}
    </div>
    ${kind==='tags'?tabs(INDEX_SCOPES,scope,'词表'):kind==='performers'?tabs(INDEX_SCOPES,scope,'名册')
      :company?tabs(MAKER_INDEX_KINDS,kind,'公司类型'):''}
    ${kind==='tags'?tagFilterSkeletonHtml(view):''}
    ${indexSkeletonHtml({kind,layout,mode:view})}`;
}
/* 屏幕上已经是同一张骨架就别重画：深链冷启动时首屏骨架先铺过一遍，innerHTML 换新节点会把
   shimmer 从头放一遍。 */
function showIndexSkeleton(params){
  $('#stats').hidden=true;$('#index').hidden=false;clearCatalogGrid();hideCatalogCombo();
  $('#count').textContent='';$('#loadSentinel').hidden=true;
  const placeholder=indexPlaceholderHtml(params);
  if($('#index').querySelector('[data-skeleton]')?.dataset.skeleton!==skeletonKeyOf(placeholder)){
    $('#index').innerHTML=placeholder;fitSkeleton($('#index'));
  }
}
/* 回目录按标签筛选：点一枚是「只看这一枚」，按所选显示结果是照匹配方式拼几枚。 */
function showIndexTags(tags,match){
  state={...state,state:'',tag:tags.join(','),tag_match:match};
  setSelectMode(false,false);route(homePath());showHomeSurfaces();buildEdge();buildBars();loadCatalog();
}
/* 在线那一档的人和标签还没进账本，没有资料页可去：他们名下那批东西全在关注页上，所以点开
   等于「关注 · 这一位 / 这一枚」。其余条件一并清空——从名册点进来问的是这一位的全部更新，
   不是「这一位 且 上次留在筛选条上的那几个标签」。 */
function openFollowAuthorFromIndex(key){
  followTags=new Set();followProviders=new Set();followWorks=new Set();
  followMediaView='videos';followFilter='';
  followAuthors=new Set([key]);
  $('#index').hidden=true;route(followViewPath());openFollow(false);
}
function openFollowTagFromIndex(tag){
  followAuthors=new Set();followProviders=new Set();followMediaView='videos';followFilter='';
  followTags=new Set([tag]);
  $('#index').hidden=true;route(followViewPath());openFollow(false);
}
/* `push=true` 是从导航点进来：退出选择模式、不带过滤词，回到本地与字母表。
   `push=false` 是地址栏已经在这一屏（刷新、前进后退、批量操作后的就地重取）：状态全从地址读。 */
async function openIndex(kind,push=true){
  releaseHoverPreviews();
  document.body.classList.remove('entity-open');
  delete $('#index').dataset.entityKind;delete $('#index').dataset.entityName;
  const params=push?{kind,q:'',scope:'local',view:'alphabet',category:'all'}:indexRoute(kind);
  if(push){setSelectMode(false,true);route(indexPath(params))}
  const surface=claimSurface('/'+kind);
  showHomeSurfaces();
  // 必须在 showHomeSurfaces 之后加：它会清掉这两个类并恢复顶部横条，
  // 写在前面等于自己加完自己删。
  document.body.classList.add('index-open');syncCatalogFilterScreen();
  disposeStage(false);
  showIndexSkeleton(params);
  await mountIsland('index',$('#index'),{...params,layout:peopleIndexLayout(),selectMode,
    route:(next,{replace=false}={})=>route(indexPath(next),replace),
    savePreference:({layout})=>{appSettings.peopleLayout=layout;saveSettings()},
    exitSelectMode:()=>setSelectMode(false,false),
    personAvatar,authorAvatar:onlineAuthorRingHtml,refitImages:refitNativeImages,tagLabel,
    openEntity:(entityKind,name)=>openEntity(entityKind,name),
    showTags:showIndexTags,openFollowAuthor:openFollowAuthorFromIndex,openFollowTag:openFollowTagFromIndex,
    configurable:!!runtimeConfigurable,
  },{isCurrent:()=>surfaceCurrent(surface)});
  if(!surfaceCurrent(surface))return;
  buildEdge();scheduleStickySurfaces();
}

/* 「女优」只用于番号发行物。素人、创作者自制和网红内容里的出镜者是艺人，
   套上 JAV 的行业称谓既不准确也会和创作者身份混淆。判据由后端 `is_jav` 给。 */
function performerLabel(it){return it&&it.is_jav?'女优':'艺人'}
let entityRequestSeq=0,entityJavLayout=false;
/* 资料页整页归 React（`entity-page`，ADR-0031 第 11d 步）：资料卡、筛选浮层、新作那一行与正文是
   同一座岛，`/api/entity`、作品、照片与新作都由岛按查询键取（`frontend/src/react/entity-page/`）。
   壳只写地址、挂岛、递 props：地址栏是这一页筛选与媒体视图的唯一真相源，岛改筛选调
   `actions.route`，壳写好地址再经 `routeEntityPage` 把新的 `filters`／`media` 推回去。
   挂载点是资料卡那一格（`[data-entity-hero]`）；浮层、新作与正文三块由壳在 `#index` 里排好，
   岛用 portal 画进去——浮层吸顶要它的父盒就是 `#index`，新作那一行是遗留层的卡片。 */
let entityPageHost=null,entityBodyHost=null,entityPageView='',entityPageRevision=0;
const entityPageCurrent=()=>!!entityPageHost?.isConnected&&islandMounted(entityPageHost);
const entityPageLive=(kind,name)=>entityPageCurrent()&&!$('#index').hidden
  &&$('#index').dataset.entityKind===kind&&$('#index').dataset.entityName===name;
function pushEntityPage(patch){if(entityPageCurrent())updateIsland(entityPageHost,patch)}
/* 首页与资料页的排序键：箭头只画在选中那一枚上，无障碍名称播报的是点下去会得到什么。
   资料页的 JAV 语境由岛按第一页作品推出来，随参数递进来。 */
function sortKeys(current,dir,jav=javActive()){
  return sortOptions(jav).map(([key,label])=>{
    const pressed=current===key,next=nextSortState(key,current,dir);
    return {key,label,pressed,dir:pressed&&sortDirWord(key,dir)?(dir==='asc'?'asc':'desc'):'',
      ariaLabel:next?`按${label}${next.dir?sortDirWord(next.sort,next.dir):''}排序`:''}});
}
/* 地址栏上的媒体视图：`media=photos` 与目录图集 `set=<id>`。名册不进地址栏，是事务所页与片商页
   进页时的默认视图，归岛记。 */
const EMPTY_ENTITY_MEDIA={media:'videos',set:0};
const parseMediaView=search=>{const params=new URLSearchParams(search),set=params.get('set')||'';
  return {media:params.get('media')==='photos'?'photos':'videos',set:/^\d+$/.test(set)?Number(set):0}};
const entityViewSearch=(filters,view)=>{const params=new URLSearchParams(entityFilterSearch(filters));
  if(view&&view.media==='photos'){params.set('media','photos');if(view.set)params.set('set',String(view.set))}
  return params.toString()};
/* 这一页换筛选、换视图的唯一落点：地址先写好，再把新的筛选与视图推给岛，岛按新键重取。
   这一页没挂着（从作品详情回来、深链）时返回 false，由调用方重开这一页。 */
function routeEntityPage(kind,name,filters,media=EMPTY_ENTITY_MEDIA,{push=true}={}){
  const search=entityViewSearch(filters,media);
  if(push)route(entityPath(kind,name)+(search?'?'+search:''));
  barsContext={type:'entity',kind,name,filters:{...filters}};
  if(!entityPageLive(kind,name))return false;
  releaseHoverPreviews(entityBodyHost);
  pushEntityPage({filters:{...filters},media:{...media},seed:String(state.seed||''),jav:state.jav==='1'});
  return true;
}
/* 名册一格的取图同索引页；卡片的助手与动作就是目录那一份，身份不变。照片墙多一样：灯箱里
   定位本地图片的源文件。 */
const entityCard={helpers:{...gridHelpers,personAvatar},actions:{...gridActions,revealSource:revealForIsland}};
const entityBodyCanLoadMore=()=>!$('#index').hidden&&$('#stats').hidden;
const entityBodySkeleton=()=>catalogSkeletonHtml();
/* 资料页里仍由遗留层拼的 HTML 与接线：头像的 `<img>`（兜底链、人脸放大与等待微光都直接改这个
   节点）、横滚行的拖动与滚轮、回执与弹层、图集那两枚源文件键。 */
const entityPageHelpers={
  /* 大位这条链每一环都先问过再出图：公司取自己的标识（厂牌是 `/logo`，事务所是官网圆标），人是
     实体图→代表作头像，一环都取不到就一个 `<img>` 都不出，首字母垫底直接露出来。四个标志
     （`has_logo`／`has_image`／`has_avatar`／`mark_link_id`）都由 `/api/entity` 随资料下发。

     作品截图不给公司用：厂牌那张是自家片没错，可这一页要认的是牌子；事务所名下的片更是成员
     各自拍的，拿其中一部的画面当门面，说的是别人的事。 */
  portraitImg:(kind,d)=>{
    const company=kind==='studio'||kind==='agency';
    return d.id?entityFaceImg({kind,id:d.id,hasImage:d.has_image,
      rep:company||!d.has_avatar?null:d.representative_asset_id,
      mark:kind==='agency'?d.mark_link_id:null,
      logo:company&&d.has_logo?d.canonical_name:'',logoVariant:'large',
      alt:esc(d.canonical_name),lazy:false,
      style:company?'':facePos(d.avatar_focus),focus:company?null:d.avatar_focus,
      dropStyle:true}):''},
  costarImg:x=>entityFaceImg({id:x.id,hasImage:x.has_image,rep:x.has_avatar?x.rep:null,
    style:facePos(x.avatar_focus),focus:x.avatar_focus}),
  wireDrag:row=>{if(row)wireDrag(row)},
  wireScroller:row=>{if(row)wireHorizontalScroller(row)},
  wireFeedRow:row=>wireFeedNewRow(row),
  feedRowHtml,
  receipt:(message,options)=>actionReceipt(message,options),
  failure:(label,error)=>actionFailure(label,error),
  aliasForm:(mine,write)=>entityAliasForm(mine,write),
  sourceToolsHtml:id=>sourceTools(id),
  wireSourceTools:(root,done)=>wireSourceTools(root,done),
  tagLabel:tag=>tagLabel(tag),
  comboItems:filters=>comboItems(filters),
  sortKeys:(sort,dir,jav)=>sortKeys(sort,dir,jav),
};
/* 岛递回来的写操作与跳转。筛选现读 `barsContext`，不捕获挂载那一刻的那一份。 */
function entityPageActions(kind,name){
  const live=()=>barsContext.type==='entity'&&barsContext.kind===kind&&barsContext.name===name
    ?barsContext.filters:emptyEntityFilters();
  return {
    route:(filters,media)=>void routeEntityPage(kind,name,filters,media),
    toggleTag:tag=>toggleTag(tag),
    clearFilter:key=>commitContextFilter(filters=>{filters[key]=''}),
    clearAll:()=>commitContextFilter(filters=>{
      filters.tag='';filters.creator='';filters.studio='';filters.owner=''}),
    setSort:key=>{
      const filters=live(),next=nextSortState(key,filters.sort||'new',filters.dir);
      if(next)routeEntityPage(kind,name,{...filters,...next})},
    reshuffleVideos:()=>{
      state.seed=rollSeed();routeEntityPage(kind,name,{...live(),sort:'seed'});return String(state.seed)},
    setJavLayout:value=>{setJavLayout(value);pushEntityPage({javLayout:javLayout()})},
    setPhotoLayout:value=>{
      appSettings.photoLayout=allowedSetting(value,['fixed','masonry'],'masonry');saveSettings();syncPhotoWalls()},
    openEntity:(target,to)=>void openEntity(target,to),
    javContext:on=>{entityJavLayout=!!on},
    painted:view=>{
      const wasPhotos=photoViewActive();entityPageView=view;
      if(photoViewActive()!==wasPhotos)syncDensityControl();
      scheduleStickySurfaces()},
    missing:()=>queueMicrotask(()=>{
      if(!entityPageCurrent())return;
      unmountIsland($('#index'));showEntityMissing(kind)}),
  };
}
/* 卡片网格原样要的那几样与展示设置随挂载带上现值，之后由各自的开关经 `updateIsland` 推最新值。 */
function entityPageProps(kind,name,filters,media,hosts){
  return {kind,name,filters,media,hosts,
    jav:state.jav==='1',seed:String(state.seed||''),revision:entityPageRevision,feedRevision,
    photoSize:photoSize(),photoLayout:photoLayout(),photoLayouts:PHOTO_LAYOUTS,
    javLayout:javLayout(),javLayouts:JAV_LAYOUTS,states:VIEW_PILLS,peopleLayout:peopleIndexLayout(),
    layout:catalogGridLayout(),selectMode,selected:new Set(selected),seekSeconds:appSettings.seekSeconds,
    groupCollapse:appSettings.groupCollapse,cache,wireDrag,skeletonHtml:entityBodySkeleton,
    canLoadMore:entityBodyCanLoadMore,
    card:entityCard,helpers:entityPageHelpers,actions:entityPageActions(kind,name)};
}
function photoSize(){
  return allowedSetting(appSettings.photoSize,PHOTO_SIZES.map(([key])=>key),'small');
}
function photoLayout(){return allowedSetting(appSettings.photoLayout,['fixed','masonry'],'masonry')}
/* 资料页与关注页那面墙都由岛异步画，刚推过去的这一刻 DOM 里还没有它：按视图状态判，不查墙。
   资料页的视图由岛每次画完报回来（`painted`）。剩下那一条认的是进页骨架里借照片墙网格的那一块。 */
function photoViewActive(){
  if(entityPageView==='photos'&&entityPageCurrent()&&!$('#index').hidden)return true;
  if(location.pathname==='/follow'&&followMediaView==='images'&&!$('#stats').hidden)return true;
  return [...document.querySelectorAll('.followphotowall')].some(wall=>wall.getClientRects().length>0)}
function syncPhotoWalls(){
  // 骨架里那面墙一律按固定比例铺：瀑布流的列高要等图片回来才知道。
  document.querySelectorAll('.followphotowall').forEach(wall=>{
    wall.dataset.size=photoSize();wall.dataset.layout='fixed';
    wall.dataset.imagesOnly=String(!!appSettings.followImagesOnly)});
  pushEntityPage({photoSize:photoSize(),photoLayout:photoLayout()});
  pushFollowFeed({photoSize:photoSize(),photoLayout:photoLayout(),imagesOnly:!!appSettings.followImagesOnly});
  syncDensityControl();
}
/* 顶栏那枚大小图键：停在照片墙上时管照片的大小，别处管卡片密度。 */
function syncDensityControl(){
  if(photoViewActive()){
    $('#density').setAttribute('aria-pressed',String(photoSize()==='small'));
    $('#density').title='当前：'+(photoSize()==='big'?'大图':'小图');
    syncDensityIcon(photoSize());
  }else applyDensity();
}
/* 换大小一次请求都不发，也不重拼这面墙：列数是 CSS 的事，重画只会把已经取回的缩略图
   丢掉再要一遍，还把人滚到的位置带走。 */
function setPhotoSize(value){
  appSettings.photoSize=allowedSetting(value,PHOTO_SIZES.map(([key])=>key),'small');
  saveSettings();
  syncPhotoWalls();
}

/* ── 源文件管理 ───────────────────────────────────────────────────────────────
   标题旁两个按钮，服务的是「跳过去自己整理网盘目录」这条来回：定位打开源文件所在
   目录（A:/B: 是 CloudDrive 挂上来的盘符，在资源管理器里和本地目录没区别），在那边
   删掉不要的，回来点一下同步，账本跟着对齐。
   删除不进复核，但账本记录先放进回收站。真正要防的是把「盘没挂上」当成
   「文件没了」，那个闸门在服务端：整条来源不在线时直接拒绝，一行都不动。
   路径始终由服务端按 asset id 查，前端拿不到也不该拿到 `path`。 ── */
const SOURCE_HINTS={
  'source offline':'来源不在线，这一次不对账；接上这个来源后重试',
  'source not mapped':'本机没有映射这个来源的盘符',
  'file missing':'源文件已不在盘上；点右边的同步把账本对齐',
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
/* React 那一侧（复核页、灯箱）用的形态：忙态由它自己画，定位成功的回执归全站那一份 Toast，
   失败的原因要回到出事的那一行旁边。`revealSource` 把原因写进 `status.textContent`，这里给它
   一个收字的对象读回来。 */
async function revealForIsland(id){const status={textContent:''};await revealSource(id,status);return status.textContent}
/* 同上，核对目录：状态一行读回来，外加这一趟移入回收站的那几条（作品详情据此判自己还在不在）。 */
async function syncForIsland(id){
  const status={textContent:''};let removed=[];
  await syncMissing(id,status,result=>{if(result.items)removed=result.items.map(item=>item.id)});
  return {text:status.textContent,removed};
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
      aria-label="同步删除">${icon('folder-sync')}</button>`;
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

/* 「添加别名」弹层。名字下拉本身在资料卡里（`name-picker.tsx`），换统称的确认也在岛里；这一段
   只是弹层的表单与回执，写回交给岛递进来的 `write`（`/api/entity-alias`，成功后岛重取资料与作品）。
   添别名写的是 `entity_alias`，只往这条实体上加一个写法，不改任何已有断言，所以不再问一遍；撤销
   摆在同一个弹层里，添和撤是一件事的两头。写回来的名字随后就出现在下拉里，要把它提成统称再点
   一次即可——那一步有它自己的代价，仍走确认。 */
async function entityAliasForm(mine,write){
  const form=formModal({
    title:'添加别名',
    description:'图库按名字存图，多记一个写法就多一批候选；这里添的名字也能提为统称。',
    body:`<label class="modalfield"><span>别名</span>
        <input class="geist-input" name="alias" maxlength="80" autocomplete="off"
          placeholder="另一种写法，或另一个艺名"></label>`
      +(mine.length?`<div class="modalfield"><span>自己添过的</span>
        <div class="aliaschips">${mine.map(one=>`<span class="aliaschip">${esc(one)}
          <button type="button" data-alias-drop="${esc(one)}"
            aria-label="撤销别名 ${esc(one)}">${icon('x')}</button></span>`).join('')}</div></div>`:''),
    confirmLabel:'添加别名',
    confirmDisabled:true,
    onConfirm:()=>write({alias:field.value.trim()})});
  const field=form.dialog.querySelector('[name=alias]');
  field.oninput=()=>{form.confirmButton.disabled=!field.value.trim()};
  /* 撤销只认自己添的那几个：刮削和合并留下的别名是这条实体当初被认成这个人的依据，
     一次点击删不得。服务端按来源守这条线，这里只列它报回来的那几个。 */
  form.dialog.querySelectorAll('[data-alias-drop]').forEach(chip=>chip.onclick=async()=>{
    const gone=chip.dataset.aliasDrop;
    form.close();
    try{await write({alias:gone,remove:true})}
    catch(error){actionFailure('撤销别名',error);return}
    actionReceipt(`已撤销别名 ${gone}`,{undo:async()=>{await write({alias:gone})}});
  });
  const {confirmed,result}=await form.done;
  if(!confirmed)return;
  if(result?.added)actionReceipt(`已添加别名 ${result.alias}`,{undo:async()=>{
    await write({alias:result.alias,remove:true})}});
  else actionReceipt(`${result?.alias} 已经是这条实体的名字`);
}

/* 横着滚的那一行两端要渐隐：不然浮层圆角那儿最后一个标签被直角硬切掉半个字，
   也看不出右边还有。首页筛选条本来就这么做，资料页的标签行是同一条，用同一段。 */
/* 等着的这一下浮层也得是整块的：下半要到列表回来才画的话，上半的下沿在等的那几秒里
   留着两个直角，读起来是这块浮层缺了一半。这一页的作品多时那几秒不算短。 */
function showEntityLoading(kind,name){
  const head=collectionHeaderHtml({readout:'&nbsp;',loading:true,filterRow:'bottom'});
  const body=kind==='agency'
    ?indexSkeletonHtml({kind:'performers',layout:peopleIndexLayout()})
    :catalogSkeletonHtml();
  const placeholder=entitySkeletonHtml(kind,head,body);
  if($('#index').firstElementChild?.dataset.skeleton!==`entity/${kind}`){
    $('#index').innerHTML=placeholder;
    syncEntitySkeletonParts(kind,name);
    fitSkeleton($('#index'));
  }else syncEntitySkeletonParts(kind,name);
}
/* 两块在骨架里的位置和画好的页面一样：同台艺人在资料卡底，新作那一行在筛选框之下、
   作品之上。名单晚到或换了一位时只增删这两段，骨架其余部分不重画，微光不从头再闪。 */
function syncEntitySkeletonParts(kind,name){
  const skeleton=$('#index').firstElementChild;
  if(skeleton?.dataset.skeleton!==`entity/${kind}`)return;
  const sync=(present,wanted,insert)=>{if(wanted&&!present)insert();else if(!wanted&&present)present.remove()};
  sync(skeleton.querySelector('.entityfoot'),kind!=='agency'&&hasEntityPart(kind,name,'costars'),
    ()=>skeleton.querySelector('.entityhero')?.insertAdjacentHTML('beforeend',costarSkeletonFoot()));
  sync(skeleton.querySelector('.feednew'),hasEntityPart(kind,name,'feed'),
    ()=>skeleton.querySelector('.entitysection')?.insertAdjacentHTML('beforebegin',feedNewSkeletonSection()));
  sync(skeleton.querySelector('.entityfacts'),kind==='performer'&&hasEntityPart(kind,name,'facts'),
    ()=>skeleton.querySelector('.entityprofile')?.insertAdjacentHTML('beforeend',factsSkeleton()));
}
/* 名字对不上任何一位时 `/api/entity` 回 `{error}`：骨架不换掉就一直在闪，读起来是还在取。 */
function showEntityMissing(kind){
  const index=ENTITY_ROUTES[kind]||kind,title=INDEX_TITLES[index]||'条目';
  const actions=INDEX_TITLES[index]?`<a class="geist-button primary" href="/${index}">返回${title}列表</a>`:'';
  $('#index').innerHTML=emptyState('search-x',`找不到这个${title}`,'名字可能拼错了，或者已经合并到别的名字下；回列表里重新找。',{actions});
}
/* 资料页的路由入口：写地址、铺骨架、挂岛。取数与页内状态都在岛里，挂载时 `prefetch` 把资料
   （连同新作）、作品第一页与照片取齐，骨架与整页一次换掉。前进后退落在同一位的另一份筛选上时
   这一页还挂着，只把地址上的新筛选推过去，不重挂。 */
async function openEntity(kind,name,push=true){
  const filters=push?emptyEntityFilters():parseEntityFilters(location.search);
  if(kind==='creator')filters.creator='';
  // 深链和前进后退要能直接落到照片视图；点进来的新页面一律从作品开始。
  const media=push?EMPTY_ENTITY_MEDIA:parseMediaView(location.search);
  if(!push&&barsContext.type==='entity'&&barsContext.kind===kind&&barsContext.name===name
    &&routeEntityPage(kind,name,filters,media,{push:false})){
    applyFilterStateInPlace(filters);refreshFacetCounts(barsContext);return;
  }
  releaseHoverPreviews();
  const expectedPath=entityPath(kind,name);
  const search=entityViewSearch(filters,media);
  if(push)route(expectedPath+(search?'?'+search:''));
  barsContext={type:'entity',kind,name,filters};
  showHomeSurfaces();
  disposeStage(false);
  document.body.classList.add('entity-open');syncCatalogFilterScreen();
  $('#stats').hidden=true;$('#index').hidden=false;clearCatalogGrid();hideCatalogCombo();
  $('#count').textContent='';$('#loadSentinel').hidden=true;
  const seq=++entityRequestSeq;
  // 资料页是 React 岛：包在等名单、铺骨架的这一下就开始取，挂载时取数不再排在下包后面。
  void preloadIslands();
  /* 名单启动时就在取；深链直接落在资料页时它可能还在路上，稍等一下再画骨架，画出来
     就是最终的形状。等不到就先画，名单到了再补那两块。 */
  if(!entityShapes){
    await waitEntityShapes();
    if(seq!==entityRequestSeq)return;
  }
  showEntityLoading(kind,name);
  detailReturnBarsContext=null;
  entityJavLayout=false;entityPageView='';
  // 名单每进一页重取一遍，下一页用的就是服务端的现状。
  void loadEntityShapes().then(()=>{if(seq===entityRequestSeq)syncEntitySkeletonParts(kind,name)});
  /* 卡外面依次是交集条与玻璃浮层、新作和正文，顶到底一条线。四块宿主先在文档外排好，岛取齐数据
     那一刻才换掉骨架：换掉与画出整页落在同一帧。浮层与正文各带一层 `.peach-react`（React 子树的
     样式范围）；新作那一行是遗留层的卡片，宿主不进这个范围。 */
  const frame=document.createElement('template');
  frame.innerHTML=`<div data-entity-hero></div>
    <div data-entity-filter><div class="peach-react"></div></div>
    <section class="feednew" data-feed-new aria-label="未入库的新作" hidden></section>
    <div data-entity-body><div class="peach-react"></div></div>`;
  const parts=[...frame.content.childNodes];
  const heroHost=frame.content.querySelector('[data-entity-hero]');
  const hosts={filter:frame.content.querySelector('[data-entity-filter]>.peach-react'),
    feed:frame.content.querySelector('[data-feed-new]'),
    body:frame.content.querySelector('[data-entity-body]>.peach-react')};
  entityPageHost=heroHost;entityBodyHost=hosts.body.parentElement;
  const isCurrent=()=>seq===entityRequestSeq&&
    decodeURIComponent(location.pathname)===decodeURIComponent(expectedPath);
  await mountIsland('entity-page',heroHost,entityPageProps(kind,name,filters,media,hosts),{isCurrent,
    reveal:(_el,paint)=>{$('#index').replaceChildren(...parts);paint()}});
  if(!isCurrent()||!entityPageCurrent())return;
  $('#index').dataset.entityKind=kind;$('#index').dataset.entityName=name;
  buildBars();
  window.scrollTo({top:0,behavior:'smooth'});
}

/* 抽屉里所有重画都只写 #drawerScroll：#drawer 本身是定位宿主，覆盖式滚动条的轨道和
   这层滚动容器都挂在它身上，整块 innerHTML 一换就把 buildBars() 要写的容器连轨道一起
   抹掉，首页从此停在骨架态。换页面的判据 data-surface 也记在滚动层上：
   syncSidebarSurface() 认定换了页面就 replaceChildren()，传宿主进去等于把滚动层删掉。 */
function buildDrawerNavigation(){
  const scroll=$('#drawerScroll'),key=surfacePath()+location.search;
  if(!syncSidebarSurface(scroll,key)){
    scroll.querySelectorAll('[data-nav]').forEach(button=>
      button.setAttribute('aria-pressed',String(navOn(button.dataset.nav))));
    syncNavGlide(true);
    return;
  }
  scroll.innerHTML=`<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
    <b class="disp" style="font-size:15px;letter-spacing:.1em">导航与筛选</b>
    <button id="drawerClose" class="ib" title="收起" aria-label="收起导航">${icon('x')}</button></div>
    <div class="dnav">${orderedEdgeIcons().map(([k,label,ic])=>
      `<button data-nav="${k}" draggable="true" aria-pressed="${navOn(k)}">${navigationIcon(k,ic)}<span>${label}</span></button>`).join('')}</div>`;
  $('#drawerClose').onclick=()=>openDrawer(false);
  scroll.querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));
  wireNavigationDrag(scroll.querySelector('.dnav'));
  /* 重画换掉的是那一列的按钮，玻璃在 `#drawer` 上没动。这一下只把它对回新画出来的
     那一格，不带动画：这时候动画早已经从 `paintNav` 那里起跑了。 */
  syncNavGlide(false);
}
/* 侧栏那一列标签 chip。计数由调用方给：列表是岛那一版可见条目的（`loaded`），详情是这一条自己的。 */
function renderFollowDrawer(counts){
  buildDrawerNavigation();
  const scroll=$('#drawerScroll');
  scroll.querySelectorAll('.sec').forEach(section=>section.remove());
  if(!counts.length)return;
  const tagBody=`<div class="chips">${
    counts.map(([tag,n])=>
      `<button class="chip online" data-follow-drawer-tag="${esc(tag)}" aria-pressed="${followTags.has(tag)}"><span class="chip-label">${esc(tagLabel(tag))}</span><span class="n">${n}</span></button>`).join('')}</div>`;
  scroll.insertAdjacentHTML('beforeend',sidebarSectionHtml('内容标签',tagBody,'','online'));
  $('#drawer').querySelectorAll('[data-follow-drawer-tag]').forEach(b=>b.onclick=()=>{
    followTags=new Set([b.dataset.followDrawerTag]);
    openDrawer(false);route(followViewPath());openFollow(false)});
}
function openDrawer(v){const drawer=$('#drawer'),restore=!v&&drawer.contains(document.activeElement);
  drawer.inert=!v&&innerWidth<=760;
  drawer.classList.toggle('open',v);$('#scrim').classList.toggle('on',v);
  document.body.classList.toggle('drawer-open',!!v);document.dispatchEvent(new Event('board:sidebar'));
  $('#filterBtn').setAttribute('aria-expanded',String(!!v));$('#filterBtn').setAttribute('aria-controls','drawer');$('#filterBtn').setAttribute('aria-label',v?'收起侧栏':'展开侧栏');
  if(restore)$('#filterBtn').focus();sessionStorage.setItem('board.sidebar',v?'open':'closed')}
function closeDrawerAfterNav(){if(innerWidth<=760)openDrawer(false)}
$('#filterBtn').onclick=()=>openDrawer(!$('#drawer').classList.contains('open'));
/* 常驻窄图标条：点即切视图，鼠标停留 180ms 展开完整抽屉 */
const EDGE_ICONS=[
  ['','首页','home'],
  ['performers','艺人','user-round'],
  ['studios','厂牌','clapperboard'],
  ['tags','标签','tags'],
  ['jav','JAV','jav'],
  ['flagged','已标记','bookmark'],
  ['playlists','播放列表','playlist'],
  ['follow','关注','rss'],
  ['immerse','沉浸模式','gallery-vertical-end'],
  /* 扳手＝收拾库里的东西（数据管理、回收站、人工复核、高清版都在这一层）。
     圆柱只说「数据源」那一件事，归口味页那几处；齿轮只说「我的界面偏好」，
     归右上角。三个名字都带「管」「设」的字，字形就得把它们分开。 */
  ['manage','管理','wrench'],
];
function navigationIcon(key,glyph){return key===''?'<img class="board-home-logo" src="/peach-logo.png" alt="">':icon(glyph)}
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
  // 任务中心：扫描、追更、批量和命令行批处理各跑了哪几轮。字形取「往回看的记录」
  // 那一枚，和观看记录、搜索记录同一个意思——这一页的正文就是一份按时间排的记录。
  ['activity','活动','history'],
  // 这台电脑的媒体文件夹与端口，字形是一个待配置的文件夹；`settings` 归右上角的设置弹层。
  ['configuration','配置','folder-cog'],
];
/* 管理菜单只留这几项。人工复核、回收站、高清版都是「收拾库里已有的东西」，
   和垃圾文件、重复文件、失效条目是同一件事的不同步骤，统一从数据管理进；
   统计页也因此不再挂链接管理和资源同步这两块跟统计无关的面板。
   活动页进这张菜单：它横跨所有这些页面（扫描、追更、批量都在它上面出现），
   从其中任何一页进都会像是那一页的下一步，而它不是。
   「配置」是唯一的配置编辑页（ADR-0050）：带「保存配置」的多字段表单都在它上面，
   设置弹层只留一张摘要卡指过来。 */
const MANAGE_MENU_SECTIONS=['stats','taste','cleanup','follow','activity','configuration'];
/* 「配置」只对运行 Peach 的这台电脑有意义：服务端按调用方回 `/healthz` 的 `configurable`，
   手机和另一台电脑的菜单里不列它。第一次画管理条时问一次，答复回来后重画。
   馆藏空态也按它决定是给「去配置媒体文件夹」还是给一句解释。 */
function probeConfigurable(){
  if(runtimeConfigurable!==null)return;
  runtimeConfigurable=false;
  api('/healthz').then(runtime=>{
    runtimeConfigurable=!!runtime.configurable;
    if(runtimeConfigurable&&manageSection())buildManageBar();
  }).catch(()=>{});
}
const manageMenuSections=()=>MANAGE_SECTIONS.filter(([key])=>MANAGE_MENU_SECTIONS.includes(key)
  &&(key!=='configuration'||runtimeConfigurable===true));
/* 配置页绑定这台机器，不进跨机同步的侧栏顺序：钉到手机的侧栏上只会得到一句「请在运行
   Peach 的电脑上打开」。 */
const OPTIONAL_EDGE_ICONS=MANAGE_SECTIONS.filter(([key])=>key!=='configuration').map(([key,label,ic])=>
  key==='follow'?['follow-manage',label,ic]
    :key==='cleanup'?['data-cleanup',label,ic]:[key,label,ic]);
const NAV_CATALOG=[...EDGE_ICONS,...OPTIONAL_EDGE_ICONS];
const DIRECT_MANAGE_NAV={stats:'stats',review:'review','data-cleanup':'cleanup',trash:'trash','follow-manage':'follow',quality:'quality',activity:'activity'};
/* 设置面板第一次打开时才装载 React 包；宿主只在那一下建一次，里面读到的常量那时都已就位。 */
const settingsHost=()=>({
  store:settingsStore,
  changed:effect=>settingsEffects[effect]?.(),
  sound:name=>playUiSound(name),
  navCatalog:NAV_CATALOG,themeOptions:THEME_OPTIONS,videoLayouts:JAV_LAYOUTS,
  followInitialRanges:FOLLOW_INITIAL_RANGE_OPTIONS,
  videoLayout:()=>cardLayout(),setVideoLayout,
  censored:censorOn,setCensored,
  highContrast:()=>document.documentElement.classList.contains('board-high-contrast'),setHighContrast,
  renderGlowGrid:renderGlowPresetGrid,wireGlowGrid:wireGlowPresetGrid,
  receipt:message=>actionReceipt(message),
  failure:actionFailure,
  syncRemote:remote=>applySyncedSettings(remote),
  openConfiguration:()=>void openConfiguration(true),
  attached:()=>syncGlassOptics(),
  /* 「这台电脑」那一格的判据：服务由托盘管、已完成配置、请求来自本机三条同时成立。 */
  configurable:()=>api('/healthz')
    .then(runtime=>{runtimeConfigurable=!!runtime.configurable;return runtimeConfigurable})
    .catch(()=>null),
});
/* 设置能从侧栏的设置钮、配色弹层的「详细设置」和快捷键几处进来；给了分区名就落到那一页。 */
function openSettings(section=''){
  return loadSettingsPanel(settingsHost()).then(panel=>{panel.open(section);return panel});
}
$('#settingsBtn').onclick=()=>void openSettings();
function orderedEdgeIcons(){
  const byKey=new Map(NAV_CATALOG.map(item=>[item[0],item]));
  return appSettings.sidebarOrder.map(key=>byKey.get(key)).filter(Boolean);
}
/* 侧栏顺序跟账本走，不跟浏览器走：在 Windows 上排好，Mac 上就该是同一份。
   本地那份仍然写，但只当首屏缓存（见 loadSyncedSettings）。
   写服务端失败不回滚也不打断：reader 会返回 409，本地顺序照样已经生效，
   只是这次改动不跨机同步——那是只读端的既定约束，不是操作失败。 */
function saveSidebarSetting(){
  saveSettings();buildEdge();buildBars();
  api('/api/settings',{method:'POST',
    body:JSON.stringify({sidebarOrder:appSettings.sidebarOrder})}).catch(()=>{});
}
/* 启动时用账本上的那份纠正本地缓存。侧栏立即用缓存显示；最终横条和作品在同步后绘制，
   读取期间只更新设置，保持已经显示的加载态。 */
async function loadSyncedSettings({render=true}={}){
  let remote=null;
  try{remote=await api('/api/settings')}catch(_e){return}
  applySyncedSettings(remote,{render});
}
/* 账本那一份落进本地缓存。设置面板每次打开都重取一次再交到这里，开着的面板经 store 通知跟上；
   那时侧栏已经画过，顺序变了就当场重画。 */
function applySyncedSettings(remote,{render=true}={}){
  const initial=remote&&remote.followInitialDays;
  if([0,7,30,90].includes(initial)){appSettings.followInitialDays=initial;saveSettings()}
  const days=remote&&remote.metadataRefreshDays;
  if(METADATA_REFRESH_DAYS.includes(days)&&days!==appSettings.metadataRefreshDays){
    appSettings.metadataRefreshDays=days;saveSettings();
  }
  for(const key of FEED_COMPILATION_KEYS){
    if(typeof remote?.[key]!=='boolean'||remote[key]===appSettings[key])continue;
    appSettings[key]=remote[key];saveSettings();
  }
  /* 账本里还没有条数时，这台设备本地改过的那个数替所有访问端先定下来，只送这一次。 */
  const limit=remote&&remote.searchHistoryLimit;
  if(Number.isInteger(limit)&&limit>=0&&limit<=50){
    if(limit!==appSettings.searchHistoryLimit)applySearchHistoryLimit(limit);
  }else if(remote&&remote.searchHistoryLimit===null&&appSettings.searchHistoryLimit!==DEFAULT_SETTINGS.searchHistoryLimit)postSearchHistoryLimit();
  const order=Array.isArray(remote&&remote.sidebarOrder)?remote.sidebarOrder:null;
  if(!order||!order.length||order.join(',')===appSettings.sidebarOrder.join(','))return;
  appSettings.sidebarOrder=order;
  saveSettings();
  if(render){buildEdge();buildBars();wireAllDrag()}
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
  probeConfigurable();
  // 管理区是行政界面，不该顶着首页的人物/厂牌横条和标签筛选。
  // 隐藏 tagbar 的同时同步 count 栏的吸顶偏移：它默认按「顶栏+筛选条」留位，
  // 筛选条不在时那个偏移会留出一条 58px 的缝，滚动内容从缝里穿出来。
  if(current)hideDiscoveryBars();
  $('#count').classList.toggle('no-tagbar',!!current);
  buildEdge();     // 顶层高亮跟随管理区；否则从首页进来时仍停在「首页」上
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
   层级上仍从数据管理进；资源同步是 hub 上的就地操作，没有独立页面。 */
//: 上一次页面标题说的是哪一页。空串表示此刻没有管理区标题（首页、目录这些）。
let lastManagePageLabel='';
const MANAGE_CRUMB_PAGES={
  '/junk-files':'垃圾文件',
  '/duplicates':'重复文件',
  '/review':'人工复核',
  '/trash':'回收站',
  '/quality-goals':'高清版',
  '/scraping':'来源和凭证',
};
//: 数据管理这一支里正文是 812px 窄列的页面，标题与面包屑要跟着居中。
const CENTERED_CLEANUP_PAGES=new Set(['/data-cleanup','/scraping']);
function paintManageTitle(){
  const current=manageSection(),el=$('#manageTitle');
  if(!el)return;
  document.body.classList.toggle('insight-layout',current==='stats'||current==='taste');
  /* 812px 居中跟着正文走，不跟着 section 走。数据管理 hub（.cleanuppage）和采集来源
     （.scraping-page）的正文都是这个宽度的窄列，标题不居中就比正文左出去一截；同一个
     section 下的垃圾文件、重复文件正文是全宽网格，跟着居中反而对不齐。所以判据是
     「这条路径的正文是不是窄列」，列在下面这张表里。 */
  document.body.classList.toggle('cleanup-layout',CENTERED_CLEANUP_PAGES.has(decodeURIComponent(location.pathname)));
  document.body.classList.toggle('follow-manage-layout',decodeURIComponent(location.pathname)==='/follow-manage');
  document.body.classList.toggle('configuration-layout',current==='configuration');
  const entry=MANAGE_SECTIONS.find(([k])=>k===current);
  el.hidden=!entry;
  // 数据管理之下按路径再分一层（MANAGE_CRUMB_PAGES）：垃圾文件/重复文件的
  // 标题用页面自己的名字，「数据管理」让给 breadcrumb 的上一级。
  const pageLabel=current==='cleanup'?MANAGE_CRUMB_PAGES[decodeURIComponent(location.pathname)]:null;
  if(entry)el.textContent=pageLabel||entry[1];
  paintManageCrumb();
  /* 回收站的说明行由目录计数写（paintCatalogCount）。读数到之前先铺同形占位，计数栏不在
     落地那一下才冒出来把网格往下推；已经写着读数的（同页重画）原样留着。 */
  if(current==='trash'){if(!$('#manageLede [data-lede-text]'))paintTrashLedeSkeleton()}
  else paintManageLede();
  /* 换了页才揭示一遍。同一页里的每一次重画（筛选、判完一批、翻页）走的也是这个函数，
     不比一下标题的话，页面标题会跟着每一次取数再飘一次。
     统计页正文里那几块节标题归 React 那一档（ADR-0031），这一批不动 React 子树；
     这里放的是统计、复核、数据管理共用的那一块页面标题。 */
  const label=el.hidden?'':el.textContent;
  if(label===lastManagePageLabel)return;
  lastManagePageLabel=label;
  if(label)revealTexts(document,'#manageTitle:not([hidden]),#manageLede:not([hidden])');
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
  /* 说明行的文字那一格留在原地：它每次重画说的都是同一件事的新读数，整格重建就没有
     起点可走，换态只好硬切。右端的动作仍整块重写——它换的是有没有这个按钮。 */
  const keep=el.querySelector('[data-lede-text]');
  el.querySelectorAll(':scope>:not([data-lede-text])').forEach(node=>node.remove());
  if(text){
    const slot=keep||el.appendChild(Object.assign(document.createElement('span'),{}));
    slot.setAttribute('data-lede-text','');
    swapText(slot,text);
  }else if(keep)keep.remove();
  if(actionsHtml)el.insertAdjacentHTML('beforeend',actionsHtml);
}
function paintTrashLedeSkeleton(){
  const el=$('#manageLede');if(!el)return;
  el.hidden=false;el.classList.add('pagelede-actions');
  el.innerHTML='<span class="skeleton trash-lede-skeleton" aria-hidden="true"></span><span class="skeleton trash-lede-skeleton" aria-hidden="true"></span>';
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
  showHomeSurfaces();buildEdge();buildBars();loadCatalog();
}
/* JAV 模式。只有带番号的作品才有官方封套，发行时间排序、番号筛选都挂在这个语境上；
   资料页（女优/厂牌）进入时继承这个开关，因为那里同样是按番号浏览。
   卡片版式另有首页那一份，见 `homeLayoutActive`。 */
function javActive(){
  const path=decodeURIComponent(location.pathname);
  if(path==='/')return state.jav==='1';
  if(path.startsWith('/performers/')||path.startsWith('/studios/'))
    return state.jav==='1'||entityJavLayout;
  return false;
}
/* 发行时间只对有正式发行证据的番号列表有意义。普通馆藏继续使用入库时间，
   避免把大量空日期的创作者作品挂上一个看似可用、实际无值的排序。 */
function sortOptions(jav=javActive()){
  const ordered=SORTS.filter(([key])=>key!=='seed');
  return jav?[JAV_RELEASE_SORT,...ordered]:ordered;
}
/* 点未选中项＝换列并用该列的默认方向；点选中项＝翻方向。随机没有方向，重复点它
   什么都不做——换一批是它旁边那枚按钮的事。 */
function nextSortState(key,current,dir,words=SORT_DIR_WORDS){
  if(key!==current)return{sort:key,dir:defaultSortDir(key,words)};
  if(!words[key])return null;
  return{sort:key,dir:dir==='asc'?'desc':'asc'};
}
function javLayout(){
  return normalizeJavLayout(appSettings.javLayout);
}
/* 首页与 JAV 视图分别保存版式。大图统一作品卡与 Mix 的画面框，预览图完整居中并留黑边。 */
function homeLayoutActive(){
  return decodeURIComponent(location.pathname)==='/'&&state.jav!=='1';
}
function cardLayoutActive(){return javActive()||homeLayoutActive()}
function cardLayout(){
  return homeLayoutActive()?normalizeJavLayout(appSettings.homeLayout):javLayout();
}
function setHomeLayout(value){
  appSettings.homeLayout=normalizeJavLayout(value);
  saveSettings();
  syncVideoLayoutSetting();
  if(!$('#grid').hidden)repaintCatalogGrid();
}
function setJavLayout(value){
  appSettings.javLayout=normalizeJavLayout(value);
  saveSettings();
  syncVideoLayoutSetting();
  // 只重画卡片，不重新请求：版式是纯展示层的事。资料页保留已经载入的分页。
  repaintCatalogGrid();
}
/* 版式开关在两处：设置里那一组与筛选条下排那一组，改了哪边都让另一边跟上。 */
function syncVideoLayoutSetting(){
  document.querySelectorAll('[data-video-layout]').forEach(input=>{input.checked=input.value===cardLayout()});
  if(catalogFilterProps)paintCatalogFilter({layout:catalogLayoutProp()});
}
function setVideoLayout(value){
  appSettings.homeLayout=appSettings.javLayout=normalizeJavLayout(value);
  saveSettings();
  syncVideoLayoutSetting();
  repaintCatalogGrid();
}
function toggleJavMode(){
  state.jav=state.jav==='1'?'':'1';
  if(state.jav!=='1'&&state.sort==='release'){state.sort='seed';state.dir=''}
  state.state='';state.orient='';
  route(state.jav==='1'?'/?jav=1':'/');
  showHomeSurfaces();buildEdge();buildBars();loadCatalog();
}
/* 批量操作后回到刚才那一页，而不是首页列表。
   实体资料页、索引页和管理区各有自己的取数路径，`loadCatalog()` 只会重建首页网格，
   于是在女优页选一批进回收站后会被莫名其妙地扔回首页。 */
async function reloadCurrentSurface(){
  const index=$('#index');
  const kind=index?.dataset.entityKind,name=index?.dataset.entityName;
  if(kind&&name&&!index.hidden){
    // 换一个代次，岛按地址上的筛选重取作品；照片与名册不受批量操作影响。还没挂上就照地址重开。
    if(entityPageLive(kind,name))pushEntityPage({revision:++entityPageRevision});
    else await openEntity(kind,name,false);
    return;
  }
  const hit=matchRoute(ROUTES,decodeURIComponent(location.pathname));
  if(hit?.route.reload){await hit.route.reload();return}
  await loadCatalog();
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
  buildEdge();buildBars();loadCatalog();
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
  syncPhotoWalls();
  if(!canSelect&&selectMode)setSelectMode(false,true);
}
function buildEdge(){
  buildDrawerNavigation();
  $('#edge').innerHTML=orderedEdgeIcons().map(([k,t,ic])=>
    `<button data-nav="${k}" draggable="true" title="${t}" aria-pressed="${navOn(k)}">
      ${navigationIcon(k,ic)}</button>`).join('')
;
  $('#edge').querySelectorAll('[data-loc]').forEach(b=>b.onclick=()=>{
    const cur=(state.loc||'').split(',').filter(Boolean);
    const i=cur.indexOf(b.dataset.loc);
    i>=0?cur.splice(i,1):cur.push(b.dataset.loc);
    state.loc=cur.join(',');
    buildEdge(); buildBars(); loadCatalog();
  });
  $('#edge').querySelectorAll('[data-nav]').forEach(b=>b.onclick=e=>{
    e.stopPropagation();navTo(b.dataset.nav)});
  wireNavigationDrag($('#edge'));
  syncHeaderActions();
}
/* 滚动期间挂起悬停预览：内容在鼠标下滑过会连续触发 mouseenter，
   每次都新建 video 并发起 /stream 请求，直接把页面拖垮。 */
window.__scrolling=false; let scrollT=null;
let stickyFrame=0;
let mobileFilterScroll=null,mobileFilterHost=null,mobileFilterPath='';
function updateMobileFilterScroll(){
  const frames=[...document.querySelectorAll('[data-filter-frame]')];
  const active=frames.find(frame=>frame.offsetParent!==null);
  if(active!==mobileFilterHost||location.pathname!==mobileFilterPath)mobileFilterScroll=null;
  mobileFilterHost=active;mobileFilterPath=location.pathname;
  const y=Math.max(0,Math.min(scrollY,document.documentElement.scrollHeight-innerHeight));
  const hold=!!active?.querySelector(':focus-visible,input:focus,select:focus,textarea:focus,[aria-expanded="true"]');
  mobileFilterScroll=filterScrollState(mobileFilterScroll,y,innerWidth<=760,hold);
  for(const frame of frames){
    const free=frame===active&&mobileFilterScroll.free;
    if(free)frame.style.setProperty('--filter-free-top',`${-frame.offsetHeight-12}px`);
    /* 标记写成属性不写类：资料页那块浮层是 React 画的，className 归它管。 */
    if(free===frame.hasAttribute('data-filter-free'))continue;
    /* `top` 一步到位，再用 translate 从量到的起点滑到落点：逐帧改 `top` 每一帧都要重排，滚动中主线程一忙
       就一顿一顿，translate 走合成线程。起点量的是连着上一段滑动的实际位置，半路反向也接得上。 */
    const from=frame.getBoundingClientRect().top;
    frame.getAnimations().forEach(a=>a.id==='filter-slide'&&a.cancel());
    frame.toggleAttribute('data-filter-free',free);
    const shift=from-frame.getBoundingClientRect().top;
    const [duration,easing]=getComputedStyle(document.documentElement).getPropertyValue('--board-motion').trim().split(' ');
    if(Math.abs(shift)>=1&&parseFloat(duration)>0)
      frame.animate([{translate:`0 ${shift}px`},{translate:'0 0'}],{id:'filter-slide',duration:parseFloat(duration)*1000,easing});
  }
}
function updateStickySurfaces(){
  updateMobileFilterScroll();
  ['.board-filter-frame','#count'].forEach(selector=>{
    const el=$(selector),css=el&&getComputedStyle(el),top=css?parseFloat(css.top):NaN;
    const stuck=!!el&&css.position==='sticky'&&el.offsetParent!==null&&window.scrollY>0&&
      Number.isFinite(top)&&el.getBoundingClientRect().top-(parseFloat(css.translate.split(' ')[1])||0)<=top+1;
    if(el)el.classList.toggle('is-stuck',stuck);
    if(el?.matches('.board-filter-frame'))el.classList.toggle('board-is-stuck',stuck);
  });
}
function scheduleStickySurfaces(){
  if(stickyFrame)return;
  stickyFrame=requestAnimationFrame(()=>{stickyFrame=0;updateStickySurfaces()});
}
document.addEventListener('focusin',scheduleStickySurfaces);
document.addEventListener('focusout',scheduleStickySurfaces);
window.addEventListener('scroll',()=>{
  scheduleStickySurfaces();
  window.__scrolling=true;
  // 滚动中挂起悬停预览：内容从鼠标下滑过会连续触发 mouseenter，
  // 每次新建 video 并发 /stream，几十个并发直接把页面拖垮
  releaseHoverPreviews();
  clearTimeout(scrollT); scrollT=setTimeout(()=>{window.__scrolling=false},180);
},{passive:true});
window.addEventListener('resize',scheduleStickySurfaces,{passive:true});

$('#scrim').onclick=()=>openDrawer(false);

/* ── 列表 ── */
/* 按当前筛选进入或重读目录：`/` 与四个筛选态、回收站、垃圾文件。返回的 Promise 在这次
   取数落定（成功、为空或失败）时兑现，调用方 `await` 它再做下一步（撤销回执、换一批的转圈）。
   目录与回收站的卡片网格是 `catalog-grid` island（ADR-0031）：已经挂着就把新筛选推过去，
   它按新键重取、自己铺骨架；还没挂就挂上，首屏取完才换掉壳铺的骨架。垃圾文件那一屏是
   逐项处置的队列，是另一个 island（`junk-queue`），同样挂在 `#grid` 上，两者换页时互相先卸。 */
async function loadCatalog(){
  const requestSeq=++loadRequestSeq;
  const surface=claimSurface(surfacePath());
  // 已经挂着就让它接着跑：重挂要先清空容器，而它这一刻要说的话跟上一刻是同一句。
  if(isProcessingNoticePath(location.pathname)&&!islandMounted($('#libraryProcessingNotice')))
    void mountIsland('library-processing',$('#libraryProcessingNotice'),{toast,mode:'notice'},{isCurrent:()=>surfaceCurrent(surface)});
  /* 新作那一行只在目录路径上出现：管理页、回收站这些页面回答的是别的问题，一行「外面出了
     什么」摆在那里只是噪音。离开目录时要显式收起——它是 `#main` 的固定子节点，没人收就
     一直挂在那儿。 */
  barsContext={type:'home',filters:state};detailReturnBarsContext=null;disposeStage(false);
  if(state.state==='ads')return loadJunk(surface);
  // 卸掉垃圾队列要赶在铺骨架之前：它的计数行也在 `#count` 里，先铺就把它挂着的那一格冲掉了。
  if(gridIsland==='junk-queue')clearCatalogGrid();
  renderCatalogLoading();
  showHomeSurfaces();
  if(isFeedNewPath(location.pathname)){
    await entityShapesReady;
    if(!surfaceCurrent(surface))return;
    renderHomeFeed();
  }else clearHomeFeed();
  renderCombo();
  $('#count').classList.remove('manage-static','junkcount');
  return paintCatalogGrid(surface);
}
/* 网格每次取数带一个代次：壳每要求一次重读就加一，查询随之换键重取。等着某一次重读的调用方
   挂在这里，网格报告那一代（或更新的一代）落定时一起放行；网格被卸掉时也放行，不让
   `await loadCatalog()` 永远挂着。 */
let catalogRevision=0,catalogWaiters=[],catalogPainting=null;
function settleCatalog(revision){
  catalogWaiters=catalogWaiters.filter(waiter=>{if(waiter.revision>revision)return true;waiter.resolve();return false});
}
function releaseCatalogWaiters(){const waiters=catalogWaiters;catalogWaiters=[];waiters.forEach(waiter=>waiter.resolve())}
/* 离开目录时收起网格。`#grid` 是 React 根的容器，壳往里写内容之前必须先卸掉它。 */
function clearCatalogGrid(){
  releaseHoverPreviews($('#grid'));unmountIsland($('#grid'));catalogPainting=null;gridIsland='';releaseCatalogWaiters();
  $('#grid').innerHTML='';
}
function paintCatalogGrid(surface){return paintGridIsland('catalog-grid',catalogGridProps,surface,{reveal:revealSkeleton})}
/* 垃圾队列不在挂载前取数，挂上就画它自己那份骨架，和壳铺的这份逐项相同，不必交叉淡入。 */
function paintJunkQueue(surface){return paintGridIsland('junk-queue',junkQueueProps,surface)}
/* `#grid` 上挂哪一个 island 记在 `gridIsland` 里：换成另一个之前先卸，旧的那棵不能收新的 props。 */
function paintGridIsland(name,propsFor,surface,options={}){
  const grid=$('#grid');
  if(gridIsland&&gridIsland!==name)clearCatalogGrid();
  const revision=++catalogRevision;
  const settled=new Promise(resolve=>catalogWaiters.push({revision,resolve}));
  const props=propsFor();
  /* 首屏还在取的那一次也算没挂好：`updateIsland` 对还没画出来的根是空操作，新筛选会丢。
     重挂一次，上一次的取数随之作废。 */
  if(islandMounted(grid)&&!catalogPainting){updateIsland(grid,props);return settled}
  releaseHoverPreviews(grid);
  gridIsland=name;
  const painting=catalogPainting=mountIsland(name,grid,props,
    {...options,isCurrent:()=>surfaceCurrent(surface)});
  painting.catch(error=>console.error(error)).finally(()=>{
    if(catalogPainting===painting)catalogPainting=null;
    if(!islandMounted(grid))releaseCatalogWaiters();
  });
  return settled;
}
/* 一屏卡片的版式。只在真变了的时候换新对象：卡片按引用比较，版式对象每次都新建的话，
   选一张卡也会让整屏每一张都重画一遍。 */
let catalogLayoutValue=null;
function catalogGridLayout(){
  const next={active:cardLayoutActive(),size:cardLayout(),portrait:state.orient==='竖屏',javImage:appSettings.javImage};
  if(!catalogLayoutValue||Object.keys(next).some(key=>next[key]!==catalogLayoutValue[key]))catalogLayoutValue=next;
  return catalogLayoutValue;
}
/* 作品网格的骨架与真卡共享比例：显式竖屏为 9:16，大图为 3:4，其余为 16:9。 */
function catalogSkeletonHtml(label='正在读取作品'){
  return pageSkeletonHtml(label,{cards:true,className:'catalog-skeleton postercard-skeleton',cardRatio:catalogCardRatio()});
}
function catalogCardRatio(){
  if(!state)return 16/9;
  const layout=catalogGridLayout();
  if(layout.portrait)return 9/16;
  return layout.active&&layout.size==='big'?COVER_FRONT_RATIO:16/9;
}
/* 挂着卡片网格的几处：目录 `#grid`、资料页作品区、作品详情（接着看那一排在它里面，版式、
   快进秒数与选择态同名递进去）。 */
function gridIslandHosts(){
  return [$('#grid'),entityPageCurrent()?entityPageHost:null]
    .filter(host=>host&&islandMounted(host));
}
/* 版式、「JAV 默认封面」、快进秒数这些展示层的设置变了，只推给正挂着的网格重画，不重取。 */
function repaintCatalogGrid(){
  gridIslandHosts().forEach(host=>{
    releaseHoverPreviews(host);
    updateIsland(host,{layout:catalogGridLayout(),seekSeconds:appSettings.seekSeconds});
  });
}
function catalogGridProps(){
  const path=decodeURIComponent(location.pathname),home=isCatalogPath(path),trash=state.state==='trash';
  return {
    mode:'catalog',helpers:gridHelpers,actions:gridActions,layout:catalogGridLayout(),
    selectMode,selected:new Set(selected),seekSeconds:appSettings.seekSeconds,revision:catalogRevision,
    cache,wireDrag,settled:settleCatalog,
    skeletonHtml:()=>catalogSkeletonHtml(),
    filters:{...state},batchSize:appSettings.batchSize,groupCollapse:appSettings.groupCollapse,
    /* 只有首页默认列表排除竖屏——那里另有独立的竖屏带承接它们。搜索必须能搜到竖屏作品，
       否则按名字找一条竖屏视频会得到 0 结果。JAV 模式恒不含竖屏：番号发行物本身就是横版。 */
    excludeVertical:(home&&!state.q&&!state.orient)||state.jav==='1',
    mix:home&&!trash,
    /* JAV 模式不插竖屏带：主列表的 exclude_vertical 管不到它，它是独立请求、独立插入的。 */
    shorts:home&&!javActive()&&state.orient!=='竖屏'&&!trash,
    countRow:$('#count'),onCount:paintCatalogCount,
    emptyHtml:({trash:inTrash,libraryEmpty})=>inTrash
      ?emptyState('trash','回收站是空的','删掉的内容会先到这里；确认不再需要后再清空。')
      :catalogEmptyHtml({jav:javActive()&&!libraryEmpty,configurable:runtimeConfigurable,filtered:!libraryEmpty}),
    canLoadMore:()=>$('#stats').hidden&&$('#index').hidden,
  };
}
/* 进入或重读垃圾文件队列。已经挂着且计数行那一格还在（在这一屏里换分类、换视图，处置完
   重读）就把新的地址与代次推过去；否则先卸掉 `#grid` 上的旧根，铺骨架再挂。分类与视图
   只从地址读，壳不另记一份。 */
function loadJunk(surface){
  const count=$('#count');
  const live=gridIsland==='junk-queue'&&islandMounted($('#grid'))&&!catalogPainting
    &&count.querySelector(':scope > .peach-react:not([data-junk-count-skeleton])');
  if(!live){clearCatalogGrid();renderCatalogLoading('正在读取垃圾文件')}
  showHomeSurfaces();
  renderCombo();
  // 垃圾文件是逐项处置队列，计数只是当前队列说明，不是需要跟随浏览的排序工具。
  count.classList.add('manage-static','junkcount');
  count.classList.remove('is-stuck');
  return paintJunkQueue(surface);
}
/* 垃圾卡上那三颗键与标题。写 ledger 的操作做完重读队列并给撤销（互逆操作，移入回收站
   的撤销是还原）；失败再抛给卡片，它据此把键恢复成可点。 */
async function runJunkOperation(it,operation){
  const ids=[it.id],disposed=operation==='dispose',reconsidered=operation==='reconsider-junk';
  try{
    await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation})});
    await loadCatalog();
    const inverse=disposed?'restore':reconsidered?'dismiss-junk':'reconsider-junk';
    actionReceipt(disposed?'已移入回收站':reconsidered?'已重新加入垃圾判断':'已标记为不是垃圾',{undo:async()=>{
      await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation:inverse})});
      await loadCatalog();
    }});
  }catch(error){actionFailure('操作',error);throw error}
}
const junkQueueHelpers={badgeHtml:(location,cost)=>srcBadge(location,cost)};
const junkQueueActions={
  /* 换分类、换视图：先收起多选，改地址再重读。 */
  navigate:path=>{if(selectMode)setSelectMode(false,true);route(path);loadCatalog()},
  toggleSelection:(id,range)=>toggleSelection(id,range),
  open:(it,anchor)=>it.junk_kind==='image'
    ?window.open('/photo?id='+it.id,'_blank','noopener'):openItem(it.id,true,null,anchor),
  /* 定位成功由 Toast 报，卡上状态行留空；失败把原因写回状态行。 */
  reveal:async it=>{
    try{await api('/api/reveal',{method:'POST',body:JSON.stringify({id:it.id})});toast({text:'已在资源管理器中显示'});return ''}
    catch(error){return sourceHint(error.message)}
  },
  operate:(it,operation)=>runJunkOperation(it,operation),
};
function junkQueueProps(){
  return {
    ...junkRoute(location.search),helpers:junkQueueHelpers,actions:junkQueueActions,
    batchSize:appSettings.batchSize,revision:catalogRevision,selectMode,selected:new Set(selected),
    countRow:$('#count'),cache,settled:settleCatalog,
    skeletonHtml:()=>pageSkeletonHtml('正在读取垃圾文件',{cards:true,className:'catalog-skeleton postercard-skeleton'}),
    canLoadMore:()=>$('#stats').hidden&&$('#index').hidden,
  };
}
/* ── 顶栏搜索 ──
   输入框 `#q` 是顶栏的静态节点；下拉栏里的记录、推荐、补全、键盘选中与提交归 `search` 岛，
   提交与打开都回这里走路由。残影（`clearSearchField`）、窄屏开合、失焦与外点收起也还在壳里，
   收起一律经岛交出来的 `close()`。 */
let searchControl=null;
function applySearchHistoryLimit(limit){
  appSettings.searchHistoryLimit=boundedPreference(limit,0,50,10);saveSettings();
  updateIsland($('#searchMenu'),{historyLimit:appSettings.searchHistoryLimit});
}
function postSearchHistoryLimit(){
  return api('/api/settings',{method:'POST',body:JSON.stringify({searchHistoryLimit:appSettings.searchHistoryLimit})}).catch(()=>{});
}
function hideSearchMenu(){searchControl?.close()}
/* 小图和卡片同一套取景：正封按 `--card-ratio` 从封套里切出来，番号作品跟随
   「JAV 默认封面」设置。两样都没有的画一块「无预览」，格子不塌。 */
function searchCoverImage(card){
  const kind=card?javImageKind({...card,is_jav:!!card.code},appSettings.javImage):'';
  return kind==='cover'?coverImage(card,'big')
    :kind?`<img class="poster still" src="/poster?id=${card.id}&c=4" alt="" loading="lazy" data-drop="self">`
    :'<span class="nopic">无预览</span>';
}
const searchActions={
  search:query=>{
    rememberSearchValue();disposeStage(false);
    state.q=query;route(state.q?'/?q='+encodeURIComponent(state.q):'/',true);loadCatalog();
  },
  openItem:id=>openItem(id),
  openEntity:(kind,name)=>openEntity(kind,name),
};
const searchHelpers={
  pool:()=>catalogSuggestions(state,api),
  /* `.pic` 是卡片封面那一格（比例、底色、圆角与模糊垫底都认它），和里面那张图一起由壳给。 */
  coverHtml:card=>`<span class="pic">${searchCoverImage(card)}</span>`,
  /* 人和公司的门面走索引页同一条兜底链：人是实体图 → 代表作头像，厂牌是标识，
     事务所是官网站点圆标；都取不到就是首字母。 */
  faceHtml:(item,kind)=>avatarInner(item.value,{id:item.entity_id,has_image:item.has_image,avatar_focus:item.avatar_focus},
    item.rep||null,kind,item.mark||null,item.has_logo?item.value:'','icon',undefined,true),
  present:menu=>presentMenu(menu),
  dismiss:menu=>dismissMenu(menu),
  wireScroller:row=>wireHorizontalScroller(row),
  /* 字变了：清空时照着上一刻的字留一段残影，敲进新字就收掉正在散的那段。 */
  typed:input=>{
    const next=input.value;
    if(!next&&searchValueSnapshot.text)clearSearchField(searchValueSnapshot);
    else{
      if(next){cancelSearchDissolve();cancelSearchDissolve=()=>{}}
      rememberSearchValue(input);
    }
  },
  composing:()=>{cancelSearchDissolve();cancelSearchDissolve=()=>{}},
  clearField:input=>clearSearchField({text:input.value,scrollLeft:input.scrollLeft||searchValueSnapshot.scrollLeft}),
};
mountIsland('search',$('#searchMenu'),{
  input:$('#q'),historyLimit:appSettings.searchHistoryLimit,actions:searchActions,helpers:searchHelpers,
  expose:control=>{searchControl=control},
});
$('#q').addEventListener('beforeinput',e=>{if(!e.isComposing)rememberSearchValue(e.currentTarget)});
$('#q').addEventListener('scroll',e=>{if(e.currentTarget.value)rememberSearchValue(e.currentTarget)});
$('#q').addEventListener('pointerdown',e=>{if(e.currentTarget.value)rememberSearchValue(e.currentTarget)});

/* ── 就地展开播放 ── */
/* 四种队列的入口（Mix、分卷、版本、播放列表）。队列的条目、停在哪一条、卷标都归详情岛
   （`item-detail`），岛按 `{kind, seedId|playlistId}` 自己取；壳只判「是不是同一个队列里换一条」
   （是就读岛的缓存，不重取），并记下地址的前缀，等岛定下停在哪一条之后再推。播放列表每次都
   重取：它的顺序和内容别处也在改。版次视图复用分卷的队列：两者都是「一个番号下的几个可播
   条目」，差别只在标题和每条的副标题。 */
const QUEUE_ROUTES={mix:'/mix',parts:'/parts',editions:'/editions',playlist:'/playlists'};
function openQueue(kind,key,itemId,push,anchor=null){
  key=+key;
  const same=activeQueue?.kind===kind&&(kind==='playlist'?activeQueue.playlistId:activeQueue.seedId)===key;
  if(push&&(kind==='playlist'||!same))detailReturnPath=location.pathname+location.search;
  const queue=kind==='playlist'?{kind,playlistId:key,fresh:true}:{kind,seedId:key,fresh:!same};
  return openItem(itemId==null?null:+itemId,false,queue,anchor,push);
}
function openMix(seedId,itemId=seedId,push=true,anchor=null){return openQueue('mix',seedId,itemId,push,anchor)}
function openEditions(seedId,itemId=seedId,push=true,anchor=null){return openQueue('editions',seedId,itemId,push,anchor)}
function openParts(seedId,itemId=seedId,push=true,anchor=null){return openQueue('parts',seedId,itemId,push,anchor)}
function openPlaylist(playlistId,itemId=null,push=true){return openQueue('playlist',playlistId,itemId,push)}
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
   占位的那张「正在读取作品」就停在详情下方，写着在读，其实没有任何请求在跑。这里把那
   一次请求补发出去：从列表里点进详情时下面就是那份列表，直接刷新详情页的地址也该有
   同样的东西，否则排序条底下是一整屏空白。
   走的是 `paintCatalogGrid` 直接挂网格那条路——`loadCatalog` 开头就 `disposeStage()`，
   会把刚打开的这一屏详情一起收掉。网格已经挂上（哪怕还在取第一页）就不再补发；静态骨架留在
   原位，由挂载时的 `revealSkeleton` 淡出。 */
function fillIdleCatalog(){
  const grid=$('#grid');
  if(islandMounted(grid)||catalogPainting)return;
  const deepLink=bootDetailDeepLink;bootDetailDeepLink=false;
  if(!grid.querySelector('.catalog-skeleton')&&!deepLink)return;
  const count=$('#count');count.removeAttribute('aria-busy');count.removeAttribute('aria-label');
  void paintCatalogGrid(surfaceToken(surfacePath()));
}
/* 作品详情整块归舞台岛（`frontend/src/react/stage/`）：条目与队列的取数、播放区、侧栏、接着看、
   写操作与播放器都在 /dist/peach-react.js 里。壳留来处：从哪一张卡进来、关掉回哪一份列表、顶栏
   换成哪条作品的上下文。
   队列里换一条也走 `openItem`：舞台上的播放器要先拆，地址要换。 */
const itemDetailHelpers={
  badgeHtml:(location,cost,cls)=>srcBadge(location,cost,cls),
  titleHtml:it=>javTitleHtml(it),
  displayName:it=>javDisplayName(it),
  performerLabel:it=>performerLabel(it),
  // 和顶栏圆头像同一条判据：没装实体图就不出 `<img>`，取不到就是首字母垫底。
  faceHtml:ref=>entityFaceImg({id:ref.id,hasImage:ref.has_image,focus:ref.avatar_focus}),
  queueThumbHtml:it=>mixFacePoster(it,'small'),
  queueAvatarHtml:it=>cardIdentity(it,false).avatar,
  mixLabel:it=>mixLabel(it),
  tagLabel:tag=>tagLabel(tag),
  isDurationTag:tag=>DURATION_TAGS.has(tag),
  tagCandidates:()=>(facets&&facets.tags)||[],
  sourceOffline:key=>sourceOffline(key),
  offlineReason:key=>offlineReason(key),
  relatedSkeletonHtml:()=>pageSkeletonHtml('正在读取推荐',{cards:true,className:'related-skeleton'}),
  mixRelated:seedId=>mixRelated(seedId),
  wireDrag:el=>wireDrag(el),
  wireDragReorder:(root,options)=>wireDragReorder(root,options),
};
const itemDetailActions={
  close:()=>closeItemDetail(),
  /* 顶栏的实体上下文跟着画出来的这一条走；队列的地址也在这时推，停在哪一条要等岛定下来。 */
  present:item=>{
    cache([item]);presentedItem=item;
    const returnBars=detailReturnBarsContext;
    barsContext={type:'item',id:item.id,filters:returnBars?.type==='entity'
      ? {...returnBars.filters}:emptyEntityFilters()};
    if(pendingQueueRoute){route(`${pendingQueueRoute}/${item.id}`);pendingQueueRoute=null}
    buildBars();
  },
  /* 取数时发现要换去别处：保存过的在线资产转关注详情，队列取不到退回普通详情，播放列表空了
     回列表页，条目已不在就收起舞台。壳一换舞台，岛这一次挂载就作废。 */
  redirect:to=>{
    const push=!!pendingQueueRoute;
    if(to.kind==='follow'){followDetailReturnPath=detailReturnPath||'/';void openFollowDetail(to.id,false,null,true);return}
    if(to.kind==='item'){void openItem(to.id,true);return}
    if(to.kind==='playlists'){void openPlaylists(push);return}
    disposeStage(false);
  },
  openQueueItem:(queue,id,push=true)=>void openQueue(queue.kind,queue.kind==='playlist'?queue.playlistId:queue.seedId,id,push),
  // 盘回来了就按正常路径重开，不在半路挂播放器；开着的队列跟着留下。
  reopen:()=>{
    const it=presentedItem;
    if(!it)return;
    const queue=activeQueue;
    if(queue)void openQueue(queue.kind,queue.kind==='playlist'?queue.playlistId:queue.seedId,it.id,false);
    else void openItem(it.id,false);
  },
  checkSource:async key=>(await loadSourceStatus())[key]!==false,
  /* 直接进「已保存」这一档。openFollow(true) 会 route 回干净的 /follow 再照 URL 推导，所以状态
     要先写进 URL，光设全局会被推回未看。 */
  openSavedFollow:()=>{
    followAuthors=new Set();followProviders=new Set();followTags=new Set();followWorks=new Set();followMediaView='videos';
    followFilter='saved';route(followViewPath());openFollow(false)},
  openEntity:(kind,name)=>openEntity(kind,name),
  openUnowned:()=>openUnowned(),
  openRegion:region=>openRegion(region),
  openTag:tag=>{commitContextFilter(filters=>{filters.tag=tag});window.scrollTo({top:0,behavior:'smooth'})},
  addToPlaylist:item=>openAddToPlaylist(item),
  saveMix:options=>saveMixAsPlaylist(options),
  editPlaylist:()=>openPlaylists(true),
  openPlaylists:()=>openPlaylists(true),
  reveal:id=>revealForIsland(id),
  sync:id=>syncForIsland(id),
  /* 「垃圾文件」那一档（`state=ads`）按回收站状态列：移进回收站的这一条要从列表里消失，撤销
     任何一次反馈之后列表也重读一遍。别的列表不受影响。 */
  trashChanged:async(disposal,undo)=>{
    if(state.state!=='ads')return;
    if(!undo&&disposal!=='trash')return;
    if(!undo)disposeStage(true,false,{miniplayer:false});
    await loadCatalog();
  },
  toast:(message,{undo}={})=>actionReceipt(message,{undo}),
  failure:(action,error)=>actionFailure(action,error),
};

async function openItem(id,push=true,queue=null,anchor=null,queuePush=false){
  releaseHoverPreviews();
  id=id==null?null:+id;
  const origin=anchor?.isConnected?anchor:(detailOriginAnchor?.isConnected?detailOriginAnchor:null);
  const above=anchor?.isConnected
    ? anchor.getBoundingClientRect().top+anchor.getBoundingClientRect().height/2>window.innerHeight/2
    : detailOriginAbove;
  const returnSurfaceReady=hasReturnSurface();
  const needsReturnRestore=detailReturnNeedsRestore||(!push&&!returnSurfaceReady);
  if(!returnSurfaceReady)fillIdleCatalog();
  const returnBars=barsContext.type==='item'?detailReturnBarsContext:cloneBarsContext(barsContext);
  if(push)detailReturnPath=location.pathname+location.search;
  // 换详情不进小窗；小窗里放着别的条目也让位（舞台岛判），两个播放器不同时出声。
  disposeStage(false,true,{miniplayer:false});
  detailOriginAnchor=origin;detailOriginAbove=above;detailReturnNeedsRestore=needsReturnRestore;
  detailReturnBarsContext=returnBars;
  activeQueue=queue&&{kind:queue.kind,seedId:queue.seedId,playlistId:queue.playlistId};
  pendingQueueRoute=queue&&queuePush
    ? `${QUEUE_ROUTES[queue.kind]}/${queue.kind==='playlist'?queue.playlistId:queue.seedId}`:null;
  if(push&&!queue)route('/item/'+id);
  const stage=await loadStage(stageHost);
  await stage.open({kind:'item',
    id,queue,relatedLimit:appSettings.relatedLimit>0?+appSettings.relatedLimit:0,
    helpers:itemDetailHelpers,actions:itemDetailActions,
    grid:{helpers:gridHelpers,actions:gridActions,cache},
    layout:catalogGridLayout(),selectMode,selected:new Set(selected),seekSeconds:appSettings.seekSeconds,
    resume:push||id==null?null:urlResume(),
  });
  scheduleStickySurfaces();
}
/* 关掉作品详情：退场动画、拆舞台，再把来处的地址、筛选与顶栏带回去。列表还在下面就不重画；
   深链直接进的详情下面没有东西，这时才照地址重建。 */
async function closeItemDetail(){
  const restore=cloneBarsContext(detailReturnBarsContext);
  const returnPath=detailReturnPath||'/',restoreSurface=detailReturnNeedsRestore;
  await stageExit();
  disposeStage(false,false,{miniplayer:false});detailReturnBarsContext=null;
  barsContext=restore||{type:'home',filters:state};
  route(returnPath);
  if(restoreSurface)await restoreRoute();
  else{buildBars();if(location.pathname==='/playlists')openPlaylists(false)}
}

/* 沉浸模式的观看上报（`frontend/src/player/telemetry.ts`）：放完接着放下一条。 */
function wireTelemetry(it,v,sel){
  playerWireTelemetry(it,v,{...sel,onEnded:()=>{if(!$('#tok').hidden)tokNext(1)}});
}

/* ── 短片全屏 ── */
let tokList=[],tokIdx=0,tokSwitching=false,tokNetTimer=null,tokLoadHideTimer=null,tokLoadingLabel='加载中…';
/* 沉浸模式的每一格：外层 `.tokslide` 负责上下滑动，里面的 video 交给 Video.js。
   片源和详情同一个判据（`playableStreamSource`），要转码分片的片子只有 Video.js 播得了。
   每格一个流会话，切走、关闭、离开页面时按会话取消。当前格用变量持有，不按 id 查：
   Video.js 挂载后会把 video 的 id 挪到外包的 div 上。 */
let tokCurrent=null;
const tokSlides=new Set();
const tokVideo=()=>tokCurrent?.video||null;
function createTokSlide(track,offset=0){
  const el=document.createElement('div');el.className='tokslide';
  if(offset)el.style.transform=`translateY(${offset}%)`;
  // `video-js` 类要写在挂载前的 video 上，Video.js 才会把它带到外包 div 上。
  const video=document.createElement('video');video.className='video-js';video.playsInline=true;video.preload='auto';
  el.appendChild(video);track.appendChild(el);
  const slide={el,video,player:null,session:newStreamSession(),disposed:false};
  tokSlides.add(slide);return slide;
}
async function loadTokSlide(slide,it){
  const [source,vjs]=await Promise.all([
    playableStreamSource(it,slide.session),ensureVideojs().catch(()=>null)]);
  if(slide.disposed)return;
  const direct=directStreamSource(it,slide.session);
  const segmented=String(source.type||'').includes('mpegurl');
  // 播放器脚本拉不到时退回原生 video；原生元素播不了分片，只能直读。
  if(!vjs){slide.video.src=(segmented?direct:source).src;return}
  // 只留媒体本身：进度条、加载提示和动作键都由沉浸模式自己画。
  slide.player=vjs(slide.video,{controls:false,preload:'auto',
    posterImage:false,titleBar:false,textTrackDisplay:false,loadingSpinner:false,
    bigPlayButton:false,controlBar:false,errorDisplay:false,textTrackSettings:false});
  // 分片出错退回直读，和详情播放器同一个兜底。
  if(segmented)slide.player.one('error',()=>{if(!slide.disposed)slide.player.src(direct)});
  slide.player.src(source);
}
function disposeTokSlide(slide){
  if(!slide||slide.disposed)return;
  slide.disposed=true;tokSlides.delete(slide);cancelStreamSession(slide.session);
  if(slide.player&&!slide.player.isDisposed())slide.player.dispose();
  else{slide.video.pause();slide.video.removeAttribute('src');slide.video.load()}
  slide.el.remove();
  if(tokCurrent===slide)tokCurrent=null;
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
  // 脱盘来源的片子拉不到流，进了队列就是一条黑屏加载中；详情页有门挡着，这里只能在入口筛掉。
  const list=d.items.filter(x=>x.cost!=='metered' && x.duration && !sourceOffline(x.location));
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
  const track=v.closest('.toktrack');
  const box=(track&&track.clientWidth&&track.clientHeight)
    ? track.clientWidth/track.clientHeight
    : window.innerWidth/window.innerHeight;
  if(!box||!isFinite(box))return;
  const source=v.videoWidth/v.videoHeight;
  const mismatch=source>box?source/box:box/source;
  v.classList.toggle('contain',mismatch>TOK_FIT_TOLERANCE);
}
/* 舞台形状（竖 9:16／横 16:9）只在一条片子真正出画时换。新片预加载时旧片还在屏上，
   形状提前翻过去，旧片就被塞进另一种比例的框里。换完形状，框里每条片子的铺满判定重算。 */
const tokItemWide=it=>it?.width>0&&it?.height>0?it.width>=it.height:null;
const tokVideoWide=(v,it)=>v.videoWidth&&v.videoHeight?v.videoWidth>=v.videoHeight:!!tokItemWide(it);
function setTokStage(wide){
  $('#tok .tokstage').classList.toggle('wide',wide);
  $('#tok').classList.toggle('tok-wide',wide);
  $('#tokTrack').querySelectorAll('video').forEach(tokFitOne);
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
  stageApi()?.closeMiniplayer();
  $('#tok').hidden=false;$('#tok').classList.add('tok-idle');
  document.body.style.overflow='hidden';setTokLoading(true,'加载内容…');
  try{
    tokList=await fetchTok();
    if(startId&&!tokList.some(x=>x.id===startId)){
      const selectedItem=await api('/api/item?id='+startId);
      if(selectedItem.id)tokList=[selectedItem,...tokList.filter(x=>x.id!==startId)];
    }
    if(!tokList.length){$('#tokClose').click();toast({text:'当前筛选下没有可直接播放的内容'},{sound:'warning'});return}
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
  let incoming=null;
  try{
    const full=await api('/api/item?id='+it.id);
    const track=$('#tokTrack'),old=tokCurrent,slide=!!(dir&&old);
    if(!slide)disposeTokSlide(old);
    incoming=createTokSlide(track,slide?(dir>0?100:-100):0);
    const v=incoming.video;applyTokFit(v);
    await loadTokSlide(incoming,it);
    await waitTokReady(v);
    if(incoming.disposed)return;
    setTokStage(tokVideoWide(v,it));
    if(slide){
      const next=incoming;
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        old.el.style.transform=`translateY(${dir>0?-100:100}%)`;next.el.style.transform=''}));
      await new Promise(resolve=>setTimeout(resolve,210));
      // 动画帧没跑到（页面在后台）也要落位，否则新片停在屏幕外。
      disposeTokSlide(old);next.el.style.transform='';
    }
    tokCurrent=incoming;incoming=null;
    $('#tok').classList.remove('tok-idle');
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
      : (full.creator||'未归属');
    const ownerKind=cast.length?'performer':(full.creator?'creator':'');
    const ownerName=cast.length?cast[0]:(full.creator||'未归属');
    const ownerRef=ownerKind?(full.entity_refs?.[ownerKind]?.[0]||null):null;
    $('#tokAvatar').innerHTML=avatarInner(ownerName,ownerRef,REP[ownerName],ownerKind||'performer');
    $('#tokWho').textContent=who;
    const openTokOwner=e=>{e.preventDefault();
      $('#tokClose').click();
      if(full.performers&&full.performers[0])openEntity('performer',full.performers[0]);
      else if(full.creator)openEntity('creator',full.creator);
      else openUnowned()};
    $('#tokWho').onclick=openTokOwner;
    $('#tokAvatar').onclick=openTokOwner;
    $('#tokMeta').textContent=`· ${fmtDur(it.duration)} · ${it.ctx_orient||''} · ${tokIdx+1}/${tokList.length}`;
    // 进度条
    const bar=$('#tokBar'), prog=$('#tokProg');
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
    disposeTokSlide(incoming);
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
$('#immerseBtn').onclick=()=>openTok();

let searchMorph=null;
/* 玻璃轮廓与内容使用同一时间轴，位置和宽度从当前可见矩形接续。
   绝对定位层只在自身内部排版，字形不随玻璃宽度被压扁。 */
function finishSearchMorph(){
  searchMorph?.cancel();searchMorph=null;
  $('.search').classList.remove('search-morphing');
}
function setNarrowSearchOpen(open){
  const search=$('.search'),button=$('#searchBtn');
  if(search.classList.contains('open')===open)return;
  const interrupted=!!searchMorph;
  const current=search.getBoundingClientRect();
  const currentPadding=parseFloat(getComputedStyle(search).paddingLeft);
  finishSearchMorph();
  search.classList.remove('open');
  const anchor=button.getBoundingClientRect();
  search.classList.toggle('open',open);
  $('#searchBtn').setAttribute('aria-expanded',String(open));
  if(innerWidth>760||matchMedia('(prefers-reduced-motion:reduce)').matches)return;
  const expanded=search.getBoundingClientRect(),css=getComputedStyle(search);
  const padding=parseFloat(css.paddingLeft);
  const iconWidth=search.querySelector('svg').getBoundingClientRect().width;
  const compactPadding=Math.max(0,(anchor.width-iconWidth)/2-parseFloat(css.borderLeftWidth));
  const from=interrupted?current:open?anchor:expanded,to=open?expanded:anchor;
  const ease=glideEase();
  search.classList.add('search-morphing');
  const motion=search.animate(searchMorphFrames(from,to,expanded,
    interrupted?currentPadding:open?compactPadding:padding,open?padding:compactPadding,
    ease.easing,innerWidth),{duration:ease.duration,easing:'linear',fill:'both'});
  searchMorph=motion;
  motion.onfinish=()=>{if(searchMorph===motion)finishSearchMorph()};
}
let searchMorphViewport=innerWidth;
addEventListener('resize',()=>{
  if(innerWidth===searchMorphViewport)return;
  searchMorphViewport=innerWidth;finishSearchMorph();
},{passive:true});
matchMedia('(prefers-reduced-motion:reduce)').addEventListener('change',finishSearchMorph);
$('#searchBtn').onclick=()=>{setNarrowSearchOpen(true);$('#q').focus({preventScroll:true})};
/* 窄屏退出搜索。失焦那条 140ms 的兜底只在输入框为空时才收起搜索栏，
   输入过内容就没有出口了；返回按钮无条件收起，并清掉下拉栏。 */
$('#searchBack').onclick=()=>{
  setNarrowSearchOpen(false);
  hideSearchMenu();
  $('#q').blur();
  $('#searchBtn').focus({preventScroll:true});
};
$('#q').addEventListener('blur',()=>setTimeout(()=>{
  if(document.activeElement===$('#q'))return;
  if(!$('#q').value&&!$('#searchMenu').matches(':hover'))setNarrowSearchOpen(false);
  hideSearchMenu();
},140));
/* 收起下拉栏不能只有失焦这一条路：焦点未必在输入框上，而下拉栏照样开着。
   落在 `.search` 之外的第一下按压一律收起，这条判据不问焦点在哪儿。走捕获期
   的 pointerdown，是因为被点的那个东西自己可能吃掉事件或立刻把自己从页面里
   摘掉，冒泡到 document 时已经没有可供判断的祖先了。 */
document.addEventListener('pointerdown',event=>{
  if(!event.target.closest('.search'))hideSearchMenu();
},true);
$('#brandHome').onclick=e=>{e.preventDefault();openHome(true)};
$('#tokClose').onclick=()=>{setTokLoading(false);clearTokTap();$('#tok').hidden=true;
  [...tokSlides].forEach(disposeTokSlide);setTokStage(false);
  tokSwitching=false;document.body.style.overflow='';openHome()};
addEventListener('pagehide',()=>{
  tokSlides.forEach(slide=>cancelStreamSession(slide.session));
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
  const video=tokVideo();if(!video)return;
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
    if(!$('#tok').hidden)toggleVideoPlayback(tokVideo());
  },TOK_DOUBLE_TAP_MS);
}
$('#tokTrack').onclick=()=>{
  // 触屏的合成 click 会紧跟 touchend；那一下已经由单击/双击判定接管，不能再切一次。
  if(Date.now()<tokIgnoreClickUntil)return;
  toggleVideoPlayback(tokVideo());
};
$('#tok').addEventListener('touchstart',e=>{
  if(e.touches.length!==1||!e.target.closest('.toktrack')){tokTouch=null;return}
  const v=tokVideo();
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
  const v=tokVideo(),d=v&&(v.duration||0);
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
    const v=tokVideo();
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

/* 当前该响应播放快捷键的 video：沉浸模式优先，其次舞台（详情里的，没开详情就是小窗里的），都没开
   就返回 null。直接操作原生元素而不是 Video.js 实例：两边的 Video.js 读的都是这个元素，
   沉浸模式在播放器脚本拉不到时还是裸 video，一条实现全盖住。 */
function activeVideo(){
  if(!$('#tok').hidden)return tokVideo();
  return stageApi()?.activeVideo()||null;
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
    const settings=settingsPanelApi();
    if(settings?.isOpen()){settings.close();return}
    if(!$('#searchMenu').hidden){hideSearchMenu();return}
    if(!$('#tok').hidden){$('#tokClose').click();return}
    /* 详情开着：Escape 归舞台。焦点在浮窗里时舞台自己已经收了这一下；里层弹层（标签搜索框、右键
       菜单）先收掉的会 `preventDefault`，那一下只关弹层。焦点落在浮窗外（body）时在这里转给舞台。 */
    if(stageOpen()){if(!e.defaultPrevented){e.preventDefault();stageApi().requestClose()}return}
    if($('#drawer').classList.contains('open')){openDrawer(false);return}
    if(selectMode||selected.size||followSelected.size){setSelectMode(false,true);return}
    return;
  }
  // 输入态不抢键：搜索框、标签弹窗和任何可编辑区域里的按键归它们自己处理。
  if(isTypingTarget(e.target)||e.ctrlKey||e.metaKey||e.altKey)return;
  const imageDots=[...document.querySelectorAll('#stage[open] [data-follow-image-dots] [data-follow-image-item]')];
  if(imageDots.length&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){
    e.preventDefault();
    const current=Math.max(0,imageDots.findIndex(dot=>dot.getAttribute('aria-current')==='true'));
    imageDots[(current+(e.key==='ArrowRight'?1:-1)+imageDots.length)%imageDots.length].click();
    return;
  }
  const video=activeVideo();
  if(video){
    if(e.key==='t'||e.key==='T'){
      // 影院模式是详情舞台的版式，小窗里没有这个东西可切。
      e.preventDefault();stageApi()?.toggleTheater();return;
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
    if(e.key==='i'||e.key==='I'){e.preventDefault();stageApi()?.toggleMiniplayer();return}
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
      stageOpen()||!$('#tok').hidden||selectMode||selected.size||document.activeElement===$('#q')))return false;
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
  /* 网格和顶部三层一起换，两边耗时不一样，所以转圈归这一层管：换批键转到这个 Promise
     落定，网格先到时标签条还在等的那段时间里它不停。顶部三层与标签条不铺骨架——它们此刻
     有内容在屏幕上，撕成灰条再填回去比直接换掉更晃眼；只铺一层微光，骨架留给从无到有的首屏。 */
  paintCatalogFilter({refreshing:true});
  try{await Promise.all([loadCatalog(),buildBars()])}
  finally{paintCatalogFilter({refreshing:false})}
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
  settingsStore.notify();
}
applyCensor(localStorage.getItem(CENSOR_KEY)==='1');
function setCensored(on){
  localStorage.setItem(CENSOR_KEY,on?'1':'0');
  applyCensor(on);
  if(on)releaseHoverPreviews();
}
/* 增加对比度：关掉玻璃折射与透明，换实色背景。只落这台设备，壳尾的装配段启动时读回。 */
function setHighContrast(on){
  localStorage.setItem('peach.high-contrast',String(on));
  document.documentElement.classList.toggle('board-high-contrast',on);
  settingsStore.notify();
}

function wireDrag(el){return wireHorizontalScroller(el,{drag:true})}
/* `#count` 一起登记：窄屏下垃圾文件那一行由 `.count` 自己横向滚动，而它没有滚动条，
   不接拖动和滚轮就只剩看得见够不着的半个按钮。首页筛选条那几排由岛自己登记。 */
function wireAllDrag(){['#nrow','#count'].forEach(s=>wireDrag($(s)));
  document.querySelectorAll('.tier,.srow').forEach(wireDrag)}

/* 目录页（首页 + 四个筛选态）：筛选全部从 URL 读，路径只决定初始筛选态。
   `enteringHome` 判的是「从别处回到首页」：顶部三层有 30 秒会话缓存，不作废的话
   回到首页看到的还是上一次那批人。判据是 `lastRoutePath`，所以 `restoreRoute`
   要等派发完再更新它。 */
function openCatalog(path){
  const params=new URLSearchParams(location.search);
  const enteringHome=path==='/'&&lastRoutePath!=='/';
  if(enteringHome){barsDataCache=null;barsDataPromise=null}
  state={...state,loc:params.get('loc')??onlineDefaultLoc('local,115'),creator:params.get('creator')||'',studio:params.get('studio')||'',
    tag:cleanTagFilter(params.get('tag')),tag_match:params.get('tag_match')==='any'?'any':'all',len:params.get('len')||'',
    dur_min:params.get('dur_min')||'',dur_max:params.get('dur_max')||'',orient:params.get('orient')||'',
    state:ROUTE_STATES[path]||params.get('state')||'',...resolveSort(params.get('sort'),params.get('dir')),
    seed:params.get('seed')||(enteringHome?rollSeed():state.seed||rollSeed()),q:params.get('q')||'',jav:params.get('jav')||''};
  $('#q').value=state.q;rememberSearchValue();buildEdge();buildBars();loadCatalog();
}
/* 回收站。它和目录页共用同一张网格，只是筛选被钉死成 `trash`。 */
function openTrash(push){
  if(push)route('/trash');
  state={...state,creator:'',studio:'',tag:'',orient:'',state:'trash',q:''};clearSearchField();
  showHomeSurfaces();buildEdge();buildBars();loadCatalog();
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
  void syncPostSetupTutorial();
  if(path==='/'&&new URLSearchParams(location.search).get('state')==='ads'){
    const {kind,view}=junkRoute(location.search);
    route(junkPath(kind,view),true);await restoreRoute();return;
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
entityShapesReady=loadEntityShapes();
renderInitialSurfaceLoading();
buildManageBar();
/* 那两个聚合查询喂的是首页顶部三条横条。深链进管理页或索引页时横条一开始就收着，
   结果没人看，却排在这一页自己的数据前面。 */
Promise.all([loadSourceStatus(),loadSyncedSettings({render:false}),entityShapesReady])
  .then(()=>wantsDiscoveryBars()?buildBars():null)
  .then(async()=>{buildEdge();wireAllDrag();await restoreRoute();scheduleStickySurfaces()});

;(()=>{
/* Board 外壳与配置页导航。 */
document.documentElement.classList.toggle('board-high-contrast',localStorage.getItem('peach.high-contrast')==='true');
let tabSequence=0;
/* 配置页的左栏是一排下划线式页签，一条管一段节点。整块是一个 tablist，方向键在整排里走。 */
function localTabs(root,items){
  if(!items.length||root.querySelector(':scope > .board-local-nav'))return null;
  const prefix=`board-tabs-${++tabSequence}`;
  const nav=document.createElement('div');nav.className='board-local-nav';nav.setAttribute('role','tablist');nav.setAttribute('aria-label','配置分区');
  nav.dataset.sectionNav='';nav.dataset.sectionItems='';nav.setAttribute('aria-orientation','horizontal');
  const buttons=[];
  const choose=index=>{
    /* 先全清再点亮当前这一条。一条可以带好几个节点，逐条 toggle 的话节点之间有重叠时，
       后面那条会把前面点亮的又抹掉。 */
    items.forEach(item=>item.nodes.forEach(node=>node.classList.remove('board-group-active')));
    items[index].nodes.forEach(node=>node.classList.add('board-group-active'));
    buttons.forEach((button,i)=>{button.setAttribute('aria-selected',String(i===index));button.tabIndex=i===index?0:-1});
  };
  items.forEach((item,i)=>{
    const button=document.createElement('button');button.type='button';button.role='tab';button.id=`${prefix}-tab-${i}`;button.textContent=item.title;
    item.nodes.forEach((node,j)=>{node.dataset.boardGroup=String(i);node.id||=`${prefix}-panel-${i}-${j}`;node.setAttribute('role','tabpanel');node.setAttribute('aria-labelledby',button.id)});
    button.setAttribute('aria-controls',item.nodes.map(node=>node.id).join(' '));button.onclick=()=>choose(i);
    button.onkeydown=event=>{let next=i;if(event.key==='ArrowRight'||event.key==='ArrowDown')next=(i+1)%items.length;else if(event.key==='ArrowLeft'||event.key==='ArrowUp')next=(i+items.length-1)%items.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=items.length-1;else return;event.preventDefault();choose(next);buttons[next].focus()};
    buttons.push(button);nav.append(button);
  });
  root.prepend(nav);
  choose(0);
  return {nav,select:index=>choose(Math.min(Math.max(index,0),items.length-1))};
}
/* 一张配置页按 `.configgroup` 小标题切成几段，标题本身不进面板：它的字已经由左栏那一条
   写出来了，留着就是同一句话在两处各说一遍。 */
const configTabItems=page=>{
  const items=[];
  [...page.children].forEach(node=>{if(node.matches('.configgroup'))items.push({title:node.textContent.trim(),nodes:[]});else if(items.length)items.at(-1).nodes.push(node)});
  return items.filter(item=>item.nodes.length);
};
function decorate(){
  const config=document.querySelector('#stats .configpage');
  if(config&&!config.querySelector(':scope > .board-local-nav')){
    const items=configTabItems(config);
    const tabs=localTabs(config,items);
    /* 骨架也带 `.configpage`，但切不出页签；真页签画出来之后才消费这次请求。 */
    if(tabs){
      const requested=items.findIndex(item=>item.title===configurationRequestedSection);
      if(requested>=0)tabs.select(requested);
      configurationRequestedSection='';
    }
  }
  document.querySelectorAll('#managebar [data-manage]').forEach(button=>{if(button.getAttribute('aria-pressed')==='true')button.setAttribute('aria-current','page');else button.removeAttribute('aria-current')});
}
const boardBrand=document.querySelector('#brandHome');
boardBrand.setAttribute('aria-label','Peach 首页');
const libraryPicker=document.createElement('div');libraryPicker.className='board-library-menu';libraryPicker.id='boardLibraryMenu';libraryPicker.hidden=true;libraryPicker.setAttribute('popover','manual');libraryPicker.setAttribute('role','dialog');libraryPicker.setAttribute('aria-label','媒体库');
document.body.append(libraryPicker);
boardBrand.setAttribute('aria-haspopup','dialog');boardBrand.setAttribute('aria-controls',libraryPicker.id);
boardBrand.insertAdjacentHTML('beforeend','<svg class="board-library-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m5 6 3-3 3 3M5 10l3 3 3-3"/></svg>');
boardBrand.onclick=event=>{event.preventDefault()};
const libraryFloating=wireAnchoredMenu(document.querySelector('#drawer'),boardBrand,libraryPicker,{side:true});
/* 媒体库这一列跟侧栏导航那一列、筛选条那一排是同一件事：标出「当前是哪一个」，指到
   哪儿就滑到哪儿，指针离开这一列再滑回真正选中的那一项。所以走同一块玻璃、同一段
   位移，不在这里另写一份选中底色——那样这一处的手感会自己漂移成第四种。
   `aria-pressed` 全程不动：移过去不是选中，读屏和键盘那边不该跟着变。
   菜单收起时量不到尺寸（`offsetHeight` 是 0），玻璃先收起来，开的时候再落位。 */
let libraryGlide=null,libraryGlideBox=null;
function syncLibraryGlide(animate,target){
  const rows=libraryPicker.querySelector('.board-library-rows');
  const active=(target&&target.isConnected?target:null)
    ||rows?.querySelector('button[aria-pressed="true"]');
  if(!rows||!active?.offsetHeight){if(libraryGlide)libraryGlide.hidden=true;libraryGlideBox=null;return}
  if(!libraryGlide||libraryGlide.parentElement!==rows){
    libraryGlide=document.createElement('span');libraryGlide.className='viewglide';
    libraryGlide.setAttribute('aria-hidden','true');rows.prepend(libraryGlide);libraryGlideBox=null;
  }
  libraryGlide.hidden=false;
  const box={x:active.offsetLeft,y:active.offsetTop,w:active.offsetWidth,h:active.offsetHeight};
  const from=libraryGlideBox;libraryGlideBox=box;
  moveGlidePane(libraryGlide,animate?from:null,box,'y');
}
libraryPicker.addEventListener('toggle',event=>{if(event.newState==='open'){
  libraryPicker.querySelector('button')?.focus();syncLibraryGlide(false)}});
libraryPicker.addEventListener('keydown',event=>{if(event.key==='Escape'){event.stopPropagation();libraryFloating.setOpen(false);boardBrand.focus()}});
api('/api/libraries').then(data=>{
  const choices=[['','全部媒体库','database'],...data.libraries.map(row=>[row.id,row.name,row.icon||'database'])];
  const selected=sessionStorage.getItem('peach.library')||'';
  if(!choices.some(row=>row[0]===selected)){sessionStorage.removeItem('peach.library');location.reload();return}
  const current=sessionStorage.getItem('peach.library')||'';
  boardBrand.querySelector('h1').textContent=current||'全部媒体库';
  const libraryMark=glyph=>MEDIA_SOURCE_ICONS[glyph]?.startsWith('data:')?`<img src="${MEDIA_SOURCE_ICONS[glyph]}" alt="">`:icon(glyph==='local'?'hard-drive':glyph);
  const mark=document.createElement('span');mark.className='mark';mark.setAttribute('aria-hidden','true');
  mark.innerHTML=libraryMark(choices.find(row=>row[0]===current)?.[2]||'database');boardBrand.querySelector('.mark').replaceWith(mark);
  libraryPicker.innerHTML=`<p>媒体库</p><div class="board-library-rows">${choices.map(([id,name,glyph])=>`<button type="button" data-library="${esc(id)}" aria-pressed="${id===current}"><span class="board-library-avatar">${libraryMark(glyph)}</span><span>${esc(name)}</span></button>`).join('')}</div><footer><button type="button" class="geist-button primary" data-library-manage>管理媒体库</button></footer>`;
  libraryPicker.querySelectorAll('[data-library]').forEach(button=>button.onclick=()=>{sessionStorage.setItem('peach.library',button.dataset.library);location.assign('/')});
  libraryPicker.querySelector('[data-library-manage]').onclick=()=>{libraryFloating.setOpen(false);openDrawer(false);openConfigurationSection('媒体')};
  /* 委托在这一列上，不挂在每个按钮身上：菜单每次取回媒体库都整块重画。
     `pointerover`／`pointerout` 而不是 enter／leave，后两个不冒泡，委托接不到。 */
  const libraryRows=libraryPicker.querySelector('.board-library-rows');
  libraryRows.addEventListener('pointerover',event=>{
    if(event.pointerType==='touch')return;
    const button=event.target.closest?.('button[data-library]');
    if(button)syncLibraryGlide(true,button);
  });
  libraryRows.addEventListener('pointerout',event=>{
    if(event.pointerType==='touch')return;
    if(!libraryRows.contains(event.relatedTarget))syncLibraryGlide(true);
  });
  syncLibraryGlide(false);
}).catch(()=>{libraryPicker.hidden=true});
const boardToggle=document.querySelector('#filterBtn'),toggleHome=document.createComment('sidebar toggle');boardToggle.before(toggleHome);
const boardFoot=document.createElement('div');boardFoot.className='board-sidebar-foot';
boardFoot.innerHTML=`<div class="board-theme-toggle" role="group" aria-label="明暗主题"><span class="board-theme-thumb" aria-hidden="true"></span><button type="button" data-board-theme="light" aria-label="浅色主题">${icon('sun')}</button><button type="button" data-board-theme="dark" aria-label="深色主题">${icon('moon')}</button></div>`;
/* 光晕配色钮和设置钮归一组，明暗键单独一组：侧栏收窄到 60px 时这一列竖着排，明暗键
   落在最下面（boardui.com 右下角那一对就是配色在上、明暗在下）。展开态横排：明暗在左、
   这一组在右。
   字形直接引 `#ri-palette-line`，不走 `icon()`：那一枚是 Remix 的实心路径，`icon()` 拼的是
   `#i-` 前缀的线条件。它和设置分区「界面」那一枚是同一个意思——这枚钮的弹层底部「详细
   设置」开的正是那一页，两处说的都是外观，同一个意思本来就只该有一枚字形。 */
boardFoot.insertAdjacentHTML('beforeend',`<div class="board-foot-actions"><button type="button" class="board-glow-toggle" id="boardGlowBtn" aria-label="光晕配色" aria-haspopup="dialog" aria-expanded="false" aria-controls="boardGlowMenu"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#ri-palette-line"/></svg><span class="board-glow-mark" aria-hidden="true"><span class="board-glow-mark-glow"></span><span class="board-glow-mark-accent"></span></span></button></div>`);
boardFoot.querySelector('.board-foot-actions').append(document.querySelector('#settingsBtn'));
document.querySelector('#drawer').append(boardFoot);
boardFoot.querySelectorAll('[data-board-theme]').forEach(button=>button.onclick=()=>{if(button.getAttribute('aria-pressed')==='true')return;transitionTheme(button,()=>{appSettings.theme=button.dataset.boardTheme;saveSettings();applyTheme()})});
applyTheme();
/* 侧栏的光晕配色弹层照 boardui.com 右下角那枚「Accent color」：钮上不画字形，画的就是
   它管的那两样——左上一枚光晕色的圆、右下一枚强调色的圆叠在它上面，卡里两组球各取一枚；
   点开是一张 248px 的卡，头部一行标题加「重置」文字键，主体是两组 6 列圆球——上面一组
   光晕、下面一组强调色，底部一枚全宽主按钮通到详细设置。光晕那一组球和设置里「配色」
   那一组是同一份（`glowChipsHtml`）；强调色那一组换成 BoardUI 自己那颗 radial-gradient
   的球。卡的材质与媒体库选择弹层同一条规则。
   实测见 docs/reference-snapshots/feralui-studio-boardui-accent-measured.md。 */
/* 强调色那一排同样不带颜色：球拿的就是这一档真会写上去的 400 与 600 两级。 */
const accentChipHtml=([key,label],current)=>`<button type="button" class="board-glow-chip" data-accent="${key}"
  aria-pressed="${key===current}" title="${esc(label)}" aria-label="${esc(label)}"><span class="board-glow-ball"
  aria-hidden="true" data-accent-ball="${key}"></span></button>`;
const glowPicker=document.createElement('div');
glowPicker.className='popmenu board-glow-menu';glowPicker.id='boardGlowMenu';glowPicker.hidden=true;
glowPicker.setAttribute('popover','manual');glowPicker.setAttribute('role','dialog');
glowPicker.setAttribute('aria-label','配色');
glowPicker.innerHTML=`<header class="board-glow-head" data-glow-presets><span>光晕</span><button type="button" class="board-glow-reset" data-glow-preset-reset>重置</button></header>
  <div class="board-glow-grid" data-glow-grid role="group" aria-label="光晕"></div>
  <p class="board-glow-head board-glow-sub"><span>强调色</span></p>
  <div class="board-glow-grid" data-accent-grid role="group" aria-label="强调色"></div>
  <footer><button type="button" class="geist-button primary" data-glow-detail>详细设置</button></footer>`;
document.body.append(glowPicker);
const glowButton=boardFoot.querySelector('#boardGlowBtn');
const glowFloating=wireAnchoredMenu(boardFoot,glowButton,glowPicker);
/* 光晕关掉之后这张卡上只剩强调色可挑：上面那一组球和它的「重置」换的是一层现在不画的
   东西，点下去屏幕上没有任何反应，而它们还占着卡的上半张。整组收起来，卡就只说当前还
   管用的那一件事。钮上那枚点同时改口说强调色——BoardUI 原版那颗点本来就是强调色，光晕
   开着时它说的是第一枚光晕，关着时那一枚收起、只剩强调色那一枚。 */
syncGlowSidebar=()=>{
  const glow=appSettings.homeGlow;
  glowButton.style.setProperty('--glow-swatch',glow.on?glow.spot1.color:'var(--color-accent-500)');
  glowButton.toggleAttribute('data-glow-native',glow.on&&isNativeGlass(glow.preset));
  glowButton.toggleAttribute('data-glow-off',!glow.on);
  glowPicker.querySelectorAll('[data-glow-presets],[data-glow-grid]').forEach(node=>node.hidden=!glow.on);
  renderGlowPresetGrid(glowPicker.querySelector('[data-glow-grid]'));
  glowPicker.querySelector('[data-accent-grid]').innerHTML=
    ACCENTS.map(accent=>accentChipHtml(accent,appSettings.accent)).join('');
};
wireGlowPresetGrid(glowPicker.querySelector('[data-glow-grid]'));
glowPicker.querySelector('[data-accent-grid]').addEventListener('click',event=>{
  const chip=event.target.closest?.('[data-accent]');
  if(!chip)return;
  appSettings.accent=normalizeAccent(chip.dataset.accent);
  saveSettings();applyAccent();syncGlowChrome();
});
/* 这里重置的是配色，不是整份光晕：标题就写着「光晕」和「强调色」，把强度和颗粒一起
   清掉会让人以为按错了键。整份恢复默认在详细设置那一屏。 */
glowPicker.querySelector('[data-glow-preset-reset]').onclick=()=>{
  const glow=appSettings.homeGlow;
  glow.preset=DEFAULT_HOME_GLOW.preset;Object.assign(glow,glowPalette(glow.preset));
  appSettings.accent=DEFAULT_ACCENT;
  saveSettings();applyHomeGlow();applyGlassFaces();applyAccent();syncGlowChrome();
};
glowPicker.querySelector('[data-glow-detail]').onclick=()=>{
  glowFloating.setOpen(false);openDrawer(false);
  void openSettings('界面').then(panel=>panel.reveal('#homeGlowControls'));
};
syncGlowSidebar();
function placeBrand(){
  const close=document.querySelector('#drawerClose');
  if(close){const head=close.parentElement;head.classList.add('board-sidebar-head');
    boardBrand.setAttribute('aria-label','选择媒体库');
    wireSidebarGroups(document.querySelector('#drawerScroll'));
    const expanded=document.querySelector('#drawer').classList.contains('open'),desktop=innerWidth>760;
    if(desktop||expanded){if(boardToggle.parentElement!==head)head.append(boardToggle)}else if(boardToggle.parentElement!==toggleHome.parentElement)toggleHome.after(boardToggle);
    document.querySelector('#drawer').inert=!desktop&&!expanded;
    document.querySelectorAll('#drawer .dnav button').forEach(button=>button.setAttribute('aria-label',button.textContent.trim()));
  }
  if(close&&boardBrand.parentElement!==close.parentElement){
    const heading=close.parentElement.querySelector('h2,h3,strong,b');if(heading)heading.hidden=true;
    close.before(boardBrand);
  }
}
placeBrand();
document.addEventListener('board:sidebar',placeBrand);
addEventListener('resize',placeBrand);
new MutationObserver(placeBrand).observe(document.querySelector('#drawer'),{childList:true,subtree:true});
decorate();
new MutationObserver(decorate).observe(document.querySelector('#stats'),{childList:true,subtree:true});
new MutationObserver(decorate).observe(document.querySelector('#managebar'),{childList:true});

let floatingScheduled=false;
function updateFloating(){
  floatingScheduled=false;
  document.body.classList.toggle('board-scrolled',scrollY>8);
}
addEventListener('scroll',()=>{if(!floatingScheduled){floatingScheduled=true;requestAnimationFrame(updateFloating)}},{passive:true});addEventListener('resize',updateFloating);updateFloating();

/* Generate an edge-normal displacement field; only the backdrop is refracted. */
if(/Chrome|Chromium|Edg\//.test(navigator.userAgent)){
  const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');svg.setAttribute('width','0');svg.setAttribute('height','0');svg.setAttribute('aria-hidden','true');svg.style.position='fixed';svg.style.pointerEvents='none';
  const defs=document.createElementNS(ns,'defs');svg.append(defs);document.body.append(svg);
  const attached=new Map();let sequence=0;
  /* 侧栏开合那 300ms 里（`body` 的 `padding-left` 与抽屉的 `width` 在过渡），抽屉和主区里的
     玻璃宽度逐帧在变，贴图不跟着画：一张是几毫秒 JS 加一次 PNG 编码，写回 `--glass-optic`
     又让排在后面的观察器每次读尺寸都强制重排一遍，关注页实测一次开合要画十到十六张，
     观察器回调合计 95–126ms。过渡期间尺寸变了的那几块先退成同一档的纯模糊，全部停下来
     再按终态尺寸补画一次。 */
  let sizing=0;const stale=new Set();
  const sizingEvent=event=>(event.target===document.body&&event.propertyName==='padding-left')
    ||(attached.has(event.target)&&(event.propertyName==='width'||event.propertyName==='height'));
  document.addEventListener('transitionrun',event=>{if(sizingEvent(event))sizing++},true);
  const settleSizing=event=>{
    if(!sizingEvent(event)||!sizing||--sizing)return;
    const nodes=[...stale];stale.clear();nodes.forEach(node=>attached.get(node)?.draw());
  };
  document.addEventListener('transitionend',settleSizing,true);document.addEventListener('transitioncancel',settleSizing,true);
  function attach(node){
    if(attached.has(node))return;
    const id=`peach-optic-${++sequence}`;const filter=document.createElementNS(ns,'filter');filter.id=id;filter.setAttribute('filterUnits','userSpaceOnUse');filter.setAttribute('color-interpolation-filters','sRGB');
    const map=document.createElementNS(ns,'feImage');map.setAttribute('result','edge-map');map.setAttribute('preserveAspectRatio','none');
    const displacement=document.createElementNS(ns,'feDisplacementMap');displacement.setAttribute('in','SourceGraphic');displacement.setAttribute('in2','edge-map');displacement.setAttribute('xChannelSelector','R');displacement.setAttribute('yChannelSelector','G');displacement.setAttribute('scale','24');filter.append(map,displacement);defs.append(filter);
    let previous='';
    const draw=()=>{
      const width=Math.round(node.clientWidth),height=Math.round(node.clientHeight);if(!width||!height)return;
      const radius=Math.min(parseFloat(getComputedStyle(node).borderRadius)||22,width/2,height/2);const key=`${width}:${height}:${radius}`;if(previous===key)return;
      if(sizing){
        if(node.dataset.opticGlass&&node.style.getPropertyValue('--glass-optic')!=='blur(14px)')node.style.setProperty('--glass-optic','blur(14px)');
        previous='';stale.add(node);return;
      }
      previous=key;
      const ratio=Math.min(1,600/width,600/height);const w=Math.max(2,Math.round(width*ratio)),h=Math.max(2,Math.round(height*ratio));
      /* 画布只拿来写一次像素、读一次 PNG，走 CPU 那一种：默认的 GPU 画布在 toDataURL 时要把
         像素读回来，第一次还得先建 GPU 上下文，冷启动实测单这一下就是一百毫秒上下，之后的
         重画也时不时要和合成抢 GPU 等几十毫秒。 */
      const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});const pixels=ctx.createImageData(w,h);
      const distance=(x,y)=>{const qx=Math.abs(x-width/2)-(width/2-radius),qy=Math.abs(y-height/2)-(height/2-radius);return Math.hypot(Math.max(qx,0),Math.max(qy,0))+Math.min(Math.max(qx,qy),0)-radius};
      const depth=Math.min(24,Math.min(width,height)/3);
      for(let y=0;y<h;y++)for(let x=0;x<w;x++){
        const px=(x+.5)/ratio,py=(y+.5)/ratio,inside=-distance(px,py);let dx=0,dy=0;
        if(inside>0&&inside<depth){const gx=distance(px+.5,py)-distance(px-.5,py),gy=distance(px,py+.5)-distance(px,py-.5),length=Math.hypot(gx,gy)||1;const bend=Math.sin(Math.PI*inside/depth);dx=gx/length*bend;dy=gy/length*bend}
        const i=(y*w+x)*4;pixels.data[i]=128+dx*116;pixels.data[i+1]=128+dy*116;pixels.data[i+2]=128;pixels.data[i+3]=255;
      }
      ctx.putImageData(pixels,0,0);map.setAttribute('href',canvas.toDataURL());map.setAttribute('width',width);map.setAttribute('height',height);filter.setAttribute('x','0');filter.setAttribute('y','0');filter.setAttribute('width',width);filter.setAttribute('height',height);
      /* 模糊排在位移前面：backdrop-filter 是一条流水线，先糊的是身后那片内容，
         再由边缘法线场把已经糊掉的像素往外挤，边上那圈拉伸就带着颜色一起走。
         反过来先位移再糊，折射出来的亮边会被第二步抹平，只剩一块均匀磨砂。 */
      node.style.setProperty('--glass-optic',`blur(14px) url("#${id}")`);node.dataset.opticGlass='true';
    };
    const observer=new ResizeObserver(draw);observer.observe(node);
    attached.set(node,{observer,filter,draw});draw();
  }
  const sync=()=>{
    for(const [node,{observer,filter}] of attached){
      if(!node.isConnected){observer.disconnect();filter.remove();attached.delete(node)}
    }
    /* 设置面板左栏那块 `[data-glass-pane]` 挂在 `<body>` 上、不在 `#main` 里，下面那个
       观察器看不到它；岛第一次画出面板时经 `syncGlassOptics` 叫这里再扫一遍。面板收着时
       宽高是零，`draw` 直接返回，等 `ResizeObserver` 在它露出来那一帧再画一次贴图。 */
    document.querySelectorAll('.board-filter-frame,.top>.ib,.edge,.drawer,.selectiondock,.reviewcontrols,.reviewgroupbar,[data-glass-pane]').forEach(attach);
  };
  syncGlassOptics=sync;
  new MutationObserver(sync).observe(document.querySelector('#main'),{childList:true,subtree:true});sync();
}

})();

openDrawer(innerWidth>760&&sessionStorage.getItem('board.sidebar')!=='closed');
