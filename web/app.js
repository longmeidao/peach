const $=s=>document.querySelector(s);
const icon=(name,cls='')=>`<svg${cls?` class="${cls}"`:''} viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${name}"/></svg>`;
const api=async(p,o)=>{
  const response=await fetch(p,Object.assign({headers:{'Content-Type':'application/json'}},o||{}));
  let payload=null;
  try{payload=await response.json()}catch(_e){}
  if(!response.ok){
    const detail=payload&&(payload.message||payload.detail||payload.error);
    throw new Error(detail||`请求失败（${response.status}）`);
  }
  return payload;
};
const route=(path,replace=false)=>history[replace?'replaceState':'pushState']({},'',path);
const ENTITY_ROUTES={performer:'performers',studio:'studios',creator:'creators',series:'series'};
const ROUTE_ENTITIES={performers:'performer',studios:'studio',creators:'creator',series:'series'};
const entityPath=(kind,name)=>`/${ENTITY_ROUTES[kind]||kind}/${encodeURIComponent(name)}`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const faviconUrl=url=>{try{return new URL('/favicon.ico',url).href}catch{return ''}};
const foldName=s=>String(s??'').normalize('NFKC').trim().toLocaleLowerCase();
const fmtDur=s=>{if(!s)return'—';s=Math.round(s);const h=s/3600|0,m=(s%3600)/60|0,x=s%60;
  return h?`${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`:`${m}:${String(x).padStart(2,'0')}`};
const fmtClock=s=>{s=Math.max(0,Math.floor(Number(s)||0));const h=s/3600|0,m=(s%3600)/60|0,x=s%60;
  return h?`${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`:`${m}:${String(x).padStart(2,'0')}`};
const fmtSize=b=>b>=1099511627776?(b/1099511627776).toFixed(2)+' TB':b>=1073741824?(b/1073741824).toFixed(1)+' GB':(b/1048576|0)+' MB';
const LOC={local:'本地','115':'115',pikpak:'PikPak',online:'在线'};

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
const DEFAULT_SETTINGS={rotateMinutes:0,batchSize:60,defaultSort:'seed',hoverDelaySeconds:5,seekSeconds:10,searchHistoryLimit:10,relatedLimit:20,javLayout:'big'};
let appSettings={...DEFAULT_SETTINGS};
try{appSettings={...DEFAULT_SETTINGS,...JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}}catch(_e){}
const allowedSetting=(value,allowed,fallback)=>allowed.includes(value)?value:fallback;
appSettings.rotateMinutes=allowedSetting(+appSettings.rotateMinutes,[-1,0,5,10,30,1440],0);
appSettings.batchSize=allowedSetting(+appSettings.batchSize,[30,60,90],60);
appSettings.defaultSort=allowedSetting(appSettings.defaultSort,['seed','daily','rand','rating','o','plays','long','big','new','played'],'seed');
appSettings.hoverDelaySeconds=allowedSetting(+appSettings.hoverDelaySeconds,[3,5,8],5);
appSettings.seekSeconds=allowedSetting(+appSettings.seekSeconds,[5,10,30],10);
appSettings.searchHistoryLimit=allowedSetting(+appSettings.searchHistoryLimit,[5,10,20],10);
appSettings.relatedLimit=allowedSetting(+appSettings.relatedLimit,[12,20,30],20);
document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);
const saveSettings=()=>localStorage.setItem(SETTINGS_KEY,JSON.stringify(appSettings));
function syncSettingsPanel(){
  $('#rotateSetting').value=String(appSettings.rotateMinutes);
  $('#batchSizeSetting').value=String(appSettings.batchSize);
  $('#defaultSortSetting').value=appSettings.defaultSort;
  $('#hoverDelaySetting').value=String(appSettings.hoverDelaySeconds);
  $('#seekSecondsSetting').value=String(appSettings.seekSeconds);
  $('#searchHistoryLimitSetting').value=String(appSettings.searchHistoryLimit);
  $('#relatedLimitSetting').value=String(appSettings.relatedLimit);
}
function openSettings(open=true){$('#settingsPanel').hidden=!open;if(open)syncSettingsPanel()}
$('#settingsBtn').onclick=()=>openSettings(true);$('#settingsClose').onclick=()=>openSettings(false);
$('#settingsPanel').onclick=e=>{if(e.target===$('#settingsPanel'))openSettings(false)};
$('#rotateSetting').onchange=e=>{appSettings.rotateMinutes=+e.target.value;saveSettings()};
$('#batchSizeSetting').onchange=e=>{appSettings.batchSize=+e.target.value||60;saveSettings();if(location.pathname==='/')load(true)};
$('#defaultSortSetting').onchange=e=>{appSettings.defaultSort=e.target.value;saveSettings();state.sort=appSettings.defaultSort;if(location.pathname==='/')load(true)};
$('#hoverDelaySetting').onchange=e=>{appSettings.hoverDelaySeconds=+e.target.value||5;document.documentElement.style.setProperty('--hover-delay',`${appSettings.hoverDelaySeconds}s`);saveSettings()};
$('#seekSecondsSetting').onchange=e=>{appSettings.seekSeconds=+e.target.value||10;saveSettings()};
$('#searchHistoryLimitSetting').onchange=e=>{appSettings.searchHistoryLimit=+e.target.value||10;saveSettings();writeSearchHistory(readSearchHistory())};
$('#relatedLimitSetting').onchange=e=>{appSettings.relatedLimit=+e.target.value||20;saveSettings()};
/* 来源图标：品牌使用已缓存的官方资产；通用操作图标统一使用本地 Lucide 子集。 */
const SRCICON={
  local:icon('hard-drive'),
  '115':'<img class="source-icon" src="/logo?studio=115" alt="" onerror="this.remove()">',
  pikpak:'<img class="source-icon" src="/logo?studio=pikpak" alt="" onerror="this.remove()">',
  online:icon('globe'),
};
const srcBadge=(loc,cost,cls)=>{const label=`${LOC[loc]||loc}${cost==='metered'?' · 计费':''}`;
  return `<span class="${cls||'src'} ${cost==='metered'?'metered':'free'}" title="${esc(label)}" aria-label="${esc(label)}">`
    +(SRCICON[loc]||'')+'</span>'};

// sort 默认 daily：同一天进来顺序固定，隔天自动换一批（不是每次刷新都变）
/* 排序种子。顶部三层（艺人头像 / 厂牌 / 标签）和首页网格共用它，所以它一变，整屏就是
   新的一批。

   换的频率由设置里的「换一批」决定，默认每次刷新：种子只在页面加载时结算一次，页面不会
   在你看着的时候自己重排。选了分钟数就是「后台每 N 分钟换一次排序，下次刷新才体现」——
   同一批在窗口内反复刷新都是同一屏；选「从不」则只有手动点换一批才变。

   种子连同结算时间一起存，否则刷新就退回上一批。 */
const SEED_KEY='peach.seed.v2';
const newSeed=()=>String((Date.now()^(Math.random()*1e9|0))%99991);
function readSeedRecord(){
  try{
    const raw=JSON.parse(localStorage.getItem(SEED_KEY)||'null');
    return raw&&raw.value?{value:String(raw.value),at:+raw.at||0}:null;
  }catch(_e){return null}
}
function writeSeedRecord(value){
  try{localStorage.setItem(SEED_KEY,JSON.stringify({value,at:Date.now()}))}catch(_e){}
  return value;
}
function persistedSeed(){
  const minutes=appSettings.rotateMinutes;
  const saved=readSeedRecord();
  if(!saved)return writeSeedRecord(newSeed());
  if(minutes<0)return saved.value;                       // 从不：只认手动换一批
  if(minutes===0)return writeSeedRecord(newSeed());      // 每次刷新
  return Date.now()-saved.at>=minutes*60000 ? writeSeedRecord(newSeed()) : saved.value;
}
// 手动「换一批」：立刻换，并重置计时窗口。
const rollSeed=()=>writeSeedRecord(newSeed());
const initialParams=new URLSearchParams(location.search);
let state={loc:initialParams.get('loc')||'local,115',creator:initialParams.get('creator')||'',studio:initialParams.get('studio')||'',
  tag:initialParams.get('tag')||'',len:initialParams.get('len')||'',dur_min:initialParams.get('dur_min')||'',dur_max:initialParams.get('dur_max')||'',
  orient:initialParams.get('orient')||'',state:initialParams.get('state')||'',sort:initialParams.get('sort')||appSettings.defaultSort,
  seed:initialParams.get('seed')||persistedSeed(),q:initialParams.get('q')||'',jav:initialParams.get('jav')||'',thumb:'1'};
const ENTITY_FILTER_KEYS=['loc','creator','tag','dur_min','dur_max','orient'];
const emptyEntityFilters=()=>Object.fromEntries(ENTITY_FILTER_KEYS.map(key=>[key,'']));
const parseEntityFilters=search=>{const params=new URLSearchParams(search),filters=emptyEntityFilters();
  ENTITY_FILTER_KEYS.forEach(key=>{filters[key]=params.get(key)||''});return filters};
const entityFilterSearch=filters=>{const params=new URLSearchParams();
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key])params.set(key,filters[key])});
  return params.toString()};
let barsContext={type:'home',filters:state},detailReturnBarsContext=null;
const cloneBarsContext=context=>context&&context.type==='entity'
  ? {...context,filters:{...context.filters}}:context;
const activeFilterState=()=>barsContext.type==='home'?state:barsContext.filters;
$('#q').value=state.q;
const REP={};   // 创作者/厂牌 → 代表作 id，用来做圆头像（裁接触印相中心格，不另造图）
let offset=0,total=0,facets=null,current=null,detailReturnPath='/',activeQueue=null;
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
  fetch(`/api/stream-cancel?session=${encodeURIComponent(session)}`,{
    method:'POST',credentials:'same-origin',keepalive:true
  }).then(r=>r.json()).then(result=>{
    document.documentElement.dataset.peachStreamCancel=JSON.stringify(result)
  }).catch(()=>{});
}
function disposeStage(push=false){
  const stage=$('#stage');
  if(detailStatsTimer){clearInterval(detailStatsTimer);detailStatsTimer=null}
  if(detailNetTimer){clearInterval(detailNetTimer);detailNetTimer=null}
  if(detailNetHideTimer){clearTimeout(detailNetHideTimer);detailNetHideTimer=null}
  if(detailPlayer){try{detailPlayer.pause();detailPlayer.dispose()}catch(_e){}detailPlayer=null}
  stage.querySelectorAll('video').forEach(video=>{
    if(video._hop)clearInterval(video._hop);
    video.pause();video.removeAttribute('src');video.load();video.remove()});
  cancelDetailStream();
  stage.innerHTML='';stage.hidden=true;document.body.classList.remove('detail-open');current=null;activeQueue=null;
  scheduleStickySurfaces();
  if(push)route(detailReturnPath||'/');
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
function mountDetailPlayer(it,video,autoplay){
  if(detailPlayer)return detailPlayer;
  const statsButton=$('#playerStatsBtn'),statsPanel=$('#playerStats');
  if(!globalThis.videojs){
    video.controls=true;
    detailStreamSource(it).then(source=>{video.src=source.src;if(autoplay)video.play().catch(()=>{})}).catch(()=>{});
    return null;
  }
  detailPlayer=globalThis.videojs(video,{
    controls:true,preload:'metadata',language:'zh-CN',responsive:true,
    controlBar:{skipButtons:{backward:appSettings.seekSeconds,forward:appSettings.seekSeconds},pictureInPictureToggle:true}
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
    loadSourceStatus().then(status=>{
      if(status[it.location]!==false||player.isDisposed())return;
      player.error({code:2,message:`脱盘模式 · ${offlineReason(it.location)}`});
    });
  });
  detailPlayer.ready(()=>{enforceDuration();if(statsButton)statsButton.hidden=false});
  if(statsButton&&statsPanel)statsButton.onclick=()=>{
    const open=statsPanel.hidden;statsPanel.hidden=!open;statsButton.setAttribute('aria-pressed',String(open));
    if(open){updateStats();if(detailStatsTimer)clearInterval(detailStatsTimer);detailStatsTimer=setInterval(updateStats,1000)}
    else if(detailStatsTimer){clearInterval(detailStatsTimer);detailStatsTimer=null}
  };
  detailStreamSource(it).then(source=>{
    if(!detailPlayer||detailPlayer!==player||player.isDisposed())return;
    segmentedSource=String(source.type||'').includes('mpegurl');
    player.src(source);
    enforceDuration();setTimeout(enforceDuration,0);setTimeout(enforceDuration,250);
    if(autoplay)player.play().catch(()=>{});
  }).catch(()=>{});
  return detailPlayer;
}
const selected=new Set();
let selectMode=false,lastSelectedId=null;
function paintSelection(){
  document.querySelectorAll('.card[data-id]').forEach(card=>card.classList.toggle('selected',selected.has(+card.dataset.id)));
  $('#batchbar').hidden=!selected.size;$('#batchCount').textContent=`已选 ${selected.size} 项`;
  $('#batchbar').querySelectorAll('[data-trash-only]').forEach(button=>button.hidden=state.state!=='trash');
  $('#batchbar').querySelectorAll('[data-batch="like"],[data-batch="seen"],[data-batch="later"],[data-batch="dispose"]').forEach(button=>button.hidden=state.state==='trash');
}
function setSelectMode(on,clear=false){selectMode=!!on;document.body.classList.toggle('select-mode',selectMode);
  if(selectMode)releaseHoverPreviews();
  $('#selectMode').setAttribute('aria-pressed',selectMode);if(clear){selected.clear();lastSelectedId=null}paintSelection()}
/* 只取网格直属卡片：竖屏条是嵌在网格里的横向滚动条，不该被 Shift 范围选中顺带框进来。 */
function visibleCardIds(){return [...document.querySelectorAll('#grid > .card[data-id]')].map(card=>+card.dataset.id)}
function toggleSelection(id,range=false){
  if(range&&lastSelectedId!=null){const ids=visibleCardIds(),a=ids.indexOf(lastSelectedId),b=ids.indexOf(id);
    if(a>=0&&b>=0){for(let i=Math.min(a,b);i<=Math.max(a,b);i++)selected.add(ids[i])}
    else selected.add(id);
  }else{selected.has(id)?selected.delete(id):selected.add(id)}
  lastSelectedId=id;setSelectMode(true);paintSelection();
}
$('#selectMode').onclick=()=>setSelectMode(!selectMode,!selectMode?false:true);
$('#batchClear').onclick=()=>setSelectMode(false,true);
$('#batchbar').querySelectorAll('[data-batch]').forEach(button=>button.onclick=async()=>{
  const labels={like:'喜欢',seen:'标为看过',later:'加入稍后看',dispose:'加入回收站',restore:'还原',delete:'彻底删除'};
  const operation=button.dataset.batch,ids=[...selected];if(!ids.length)return;
  if(!confirm(`确认对 ${ids.length} 个作品执行“${labels[operation]}”？\n${operation==='delete'?'此操作会永久删除文件和账本记录，不可恢复。':'回收站中的文件仍保留，可从回收站入口永久清除。'}`))return;
  button.disabled=true;
  try{const r=await api('/api/batch',{method:'POST',body:JSON.stringify({ids,operation})});
    if(r.blocked&&r.blocked.length)alert(`已永久删除 ${r.purged} 个；${r.blocked.length} 个删不掉，仍留在回收站：\n`
      +r.blocked.slice(0,5).map(x=>`${x.path}（${x.reason}）`).join('\n'));
    setSelectMode(false,true);await reloadCurrentSurface()}
  catch(error){alert(`操作失败：${error.message||'未知错误'}`)}
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
    el.addEventListener('mouseenter',()=>{if(selectMode)return;armLong();t=setInterval(()=>{
      i=(i+1)%9; im.src=`/poster?id=${it.id}&c=${i}`},430)});
    const stop=()=>{clearLong();clearInterval(t);t=null;im.src=`/poster?id=${it.id}&c=4`};
    el._stopHover=stop;el.addEventListener('mouseleave',stop);
    return;
  }
  let timer=null,v=null;
  el.addEventListener('mouseenter',()=>{
    if(selectMode||window.__scrolling)return;          // 多选或滚动中不启动预览
    timer=setTimeout(()=>{
      if(window.__scrolling)return;
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
  const jav=javActive(),layout=javLayout();
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
  const tr=it.leave_ratio!=null?`<div class="scrub"><i style="width:${Math.round(it.leave_ratio*100)}%"></i></div>`:'';
  const fl=[it.feedback==='dislike'&&'dislike',it.feedback==='seen'&&'seen',
            it.disposal==='trash'&&'dispose',it.watch_later&&'later']
            .filter(Boolean).map(c=>`<i class="${c}"></i>`).join('');
  const performers=it.performers||[];
  const performerRefs=it.performer_entities||[];
  const performerTotal=it.performer_total||performers.length;
  const performer=performers[0]||'';
  const performerRef=performerRefs[0];
  const identity=it.creator?{kind:'creator',name:it.creator}
    :(performer?{kind:'performer',name:performer}
      :(it.code?{kind:'',name:it.code}
        :(it.studio?{kind:'studio',name:it.studio}:{kind:'',name:'未归属'})));
  const who=identity.name,whoKind=identity.kind;
  const sizeText=Number(it.size)>0?fmtSize(Number(it.size)):'大小未知';
  const tgs=(it.tags||[]).slice(0,3).map(x=>`<span class="tg general" data-tag="${esc(x)}">${esc(x)}</span>`).join('');
  // 共演作品的每一位出镜者都要露出，而不是只留第一位。头像叠放最多 3 个，
  // 名字最多 2 个，剩下的记为「等 N 人」，避免 BEST 合集把整行撑开。
  const coStarred=performers.length>1&&!it.creator;
  const avatar=coStarred
    ? `<div class="mavstack">${performers.slice(0,3)
        .map((nm,i)=>`<button class="mav entitylink" data-entity-kind="performer" data-entity-name="${esc(nm)}" title="打开${esc(performerLabel(it))}页：${esc(nm)}">${avatarInner(nm,performerRefs[i],REP[nm])}</button>`)
        .join('')}</div>`
    : (()=>{
        /* 头像和名字必须落到同一个身份。原来头像先看 performer、名字先看 creator，
           碰上同名的 creator/performer 重复实体（账本里有 35 组）就会一个跳
           `/performers/x`、另一个跳 `/creators/x`，同一张卡上两个入口去两个地方。 */
        const avatarKind=identity.kind||(performer?'performer':(it.creator?'creator':(it.studio?'studio':'')));
        const avatarName=identity.kind?identity.name:(performer||it.creator||it.studio||who);
        const inner=avatarInner(avatarName,performerRef,REP[avatarName]||REP[it.creator]||REP[it.studio]);
        return avatarKind
          ? `<button class="mav entitylink" data-entity-kind="${avatarKind}" data-entity-name="${esc(avatarName)}" title="打开${avatarKind==='performer'?esc(performerLabel(it)):'资料'}页">${inner}</button>`
          : `<span class="mav">${inner}</span>`;
      })();
  const whoHtml=coStarred
    ? performers.slice(0,2).map(nm=>`<button class="who entitylink" data-entity-kind="performer" data-entity-name="${esc(nm)}">${esc(nm)}</button>`).join('<span class="whosep">、</span>')
      +(performerTotal>2?`<span class="whomore">等 ${performerTotal} 人</span>`:'')
    : (whoKind?`<button class="who entitylink" data-entity-kind="${whoKind}" data-entity-name="${esc(who)}">${esc(who)}</button>`:`<span class="who">${esc(who)}</span>`);
  const tools=`<button class="previewcounter" data-open title="打开预览" aria-label="打开预览">
      <svg viewBox="-18 -18 36 36"><circle r="17"></circle><circle r="17"></circle></svg>${icon('play','ringplay')}</button>
    <div class="hovertools later-tools"><button class="laterbtn" data-later aria-pressed="${!!it.watch_later}" title="稍后看" aria-label="稍后看">
      ${it.watch_later?icon('check'):icon('bookmark-plus')}</button></div>
    <div class="hovertools seektools">
      <button data-seek="-${appSettings.seekSeconds}" title="后退 ${appSettings.seekSeconds} 秒" aria-label="后退 ${appSettings.seekSeconds} 秒">${icon('rotate-ccw')}<b>${appSettings.seekSeconds}</b></button>
      <button data-seek="${appSettings.seekSeconds}" title="前进 ${appSettings.seekSeconds} 秒" aria-label="前进 ${appSettings.seekSeconds} 秒">${icon('rotate-cw')}<b>${appSettings.seekSeconds}</b></button>
      <button data-open title="打开详情" aria-label="打开详情">${icon('maximize')}</button></div>`;
  return `<article class="card ${cls||''} ${it.disposal==='trash'?'pending-delete':''}" data-id="${it.id}">
    <div class="pic" style="--card-ratio:${ar}">${thumb}<button class="cardopenhit" data-open aria-label="打开 ${esc(it.name)} 详情"></button>
      <div class="badge mono">${srcBadge(it.location,it.cost)}</div>
      <span class="selectionMark">${icon('check')}</span><span class="deleteMark">${icon('trash')}<b>回收站</b></span>
      <span class="dur mono">${fmtDur(it.duration)}</span>${tr}${tools}</div>
    <div class="meta">${avatar}<div class="mtext"><button class="t cardtitle" data-open>${esc(it.name)}</button>
      <div class="s mono">${whoHtml}
        ${it.why?`<span class="why">${esc(it.why)}</span>`:''}
        <span class="size">${sizeText}</span>
        ${it.play_count?`<span>看过 ${it.play_count}</span>`:''}
        <span class="flags">${fl}</span></div>
      ${tgs?`<div class="ctags">${tgs}</div>`:''}</div></div></article>`;
}
function mixLabel(it){
  return it.creator||(it.performers||[])[0]||it.studio||it.code||(it.tags||[])[0]||'为你推荐';
}
function mixCardHtml(it){
  const thumb=it.has_thumb
    ? `<img class="poster" src="/poster?id=${it.id}&c=4" alt="" loading="lazy">`
    : `<span class="nopic">无预览</span>`;
  const label=mixLabel(it);
  return `<article class="card mixcard" data-mix-seed="${it.id}">
    <div class="mixstack"><div class="pic">${thumb}<button class="cardopenhit" data-open-mix aria-label="打开 Mix · ${esc(label)}"></button>
      <span class="mixbadge">${icon('play')}Mix</span></div></div>
    <div class="mixmeta"><span class="mixglyph">${icon('play')}</span><div class="mixcopy">
      <b>Mix · ${esc(label)}</b><span>${esc(it.name)}及相似作品</span></div></div></article>`;
}
function batchWithMix(items,enabled=true){
  const cards=items.map(it=>cardHtml(it));
  if(!enabled)return cards.join('');
  const seed=items.find(it=>it.creator||(it.performers||[]).length||it.studio)||items[0];
  if(seed&&items.length>=8)cards.splice(7,0,mixCardHtml(seed));
  return cards.join('');
}
function wireMixCards(root){
  root.querySelectorAll('[data-mix-seed]').forEach(el=>{
    if(el.dataset.wired)return;el.dataset.wired='1';
    el.onclick=()=>openMix(+el.dataset.mixSeed);
  });
}
function wireCards(root,onClick,onTag){
  root.querySelectorAll('[data-id]').forEach(el=>{
    if(el.dataset.wired)return; el.dataset.wired='1';
    const it=CACHE[el.dataset.id];
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
      if(e.target.closest('[data-open]')){e.stopPropagation();(onClick||openItem)(+el.dataset.id);return}
      const ent=e.target.closest('[data-entity-kind]');
      if(ent){e.stopPropagation();openEntity(ent.dataset.entityKind,ent.dataset.entityName);return}
      const tg=e.target.closest('.tg');
      if(tg){e.stopPropagation();if(onTag){onTag(tg.dataset.tag);return}
        state.tag=tg.dataset.tag;buildBars();load(true);
        window.scrollTo({top:0,behavior:'smooth'});return}
      if(e.shiftKey||e.ctrlKey||e.metaKey||selectMode){e.preventDefault();toggleSelection(it.id,e.shiftKey);return}
      (onClick||openItem)(+el.dataset.id);
    };
    el.querySelectorAll('[data-open]').forEach(opener=>{
      opener.dataset.openWired='1';
      opener.onclick=e=>{e.stopPropagation();if(selectMode||e.shiftKey||e.ctrlKey||e.metaKey){e.preventDefault();toggleSelection(it.id,e.shiftKey);return}(onClick||openItem)(+el.dataset.id)};
    });
    if(it)wireHover(el,it);
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
  const scope=facetParams.toString();
  if(scope!==barsDataScope){barsDataCache=null;barsDataPromise=null;barsDataScope=scope}
  if(barsDataCache&&Date.now()-barsDataAt<30000)return barsDataCache;
  const topsParams=new URLSearchParams({n:'30',seed:state.seed||''});
  if(javActive())topsParams.set('jav','1');
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
    mutate(state);barsContext={type:'home',filters:state};route('/');showHomeSurfaces();
    buildBars();load(true);return
  }
  mutate(state);buildBars();load(true)
}
async function buildBars(){
  const requestSeq=++barsRequestSeq;
  const context=barsContext,filterState=activeFilterState();
  // 两个聚合查询互不依赖。冷启动各需约 1 秒，串行会让手机首屏白等；
  // 并行取回后再一次性绘制顶部与抽屉。
  const [facetData,tops]=await getBarsData(context);
  if(requestSeq!==barsRequestSeq)return;
  if(context.type==='home')facets=facetData;

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
      <span class="mk" data-fallback="${fallback}"><img src="/logo?studio=${encodeURIComponent(x.k)}" alt=""
        style="width:100%;height:100%;object-fit:contain"></span>${esc(x.k)}</button>`;
  };
  $('#tiers').innerHTML=
    `<div class="tier">${tops.performers.map(avHtml).join('')}</div>`+
    `<div class="tier">${tops.studios.map(bpHtml).join('')}</div>`;
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
    views.map(v=>`<button class="pill" data-state="${v.k}" aria-pressed="${filterState.state===v.k}">${v.label}</button>`).join('')
    +`<span class="sep"></span>`
    +facetData.tags.slice(0,26).map(t=>
      `<button class="pill" data-tag="${esc(t.k)}" aria-pressed="${filterState.tag===t.k}">${esc(t.k)}</button>`).join('');
  $('#tagbar').querySelectorAll('[data-state]').forEach(b=>b.onclick=()=>{
    state.state=b.dataset.state;buildBars();load(true)});
  $('#tagbar').querySelectorAll('[data-tag]').forEach(b=>b.onclick=()=>{toggleTag(b.dataset.tag)});
  renderCombo(); wireAllDrag();

  const chips=(items,key,multi,limit)=>items.length?`<div class="chips">`+items.slice(0,limit||999).map(it=>{
    const sel=(filterState[key]||'').split(',').filter(Boolean).includes(String(it.k));
    const dot=key==='loc'?(SRCICON[it.k]||`<i class="cost ${it.cost}"></i>`):'';
    // 脱盘的来源留在列表里但不可点：数量还有意义，点进去只会得到一屏放不出的卡片。
    const off=key==='loc'&&sourceOffline(it.k);
    return `<button class="chip${off?' offline':''}" aria-pressed="${sel}" data-key="${key}" data-multi="${multi?1:0}"
      ${off?`disabled title="${OFFLINE_HINT}"`:''}
      data-val="${esc(it.k)}">${dot}${esc(it.label||it.k)}${it.n!=null?`<span class="n">${it.n.toLocaleString()}</span>`:''}</button>`;
  }).join('')+`</div>`:'';
  // 按语义类别区分来源、创作者、内容和技术规格。
  const sec=(t,b,x,cat)=>b?`<div class="sec${cat?' cat-'+cat:''}"><h3>${t}${x||''}</h3>${b}</div>`:'';
  const scopedCreators=context.type==='entity'&&context.kind==='creator'
    ? facetData.creators.filter(item=>item.k!==context.name):facetData.creators;
  // 与窄栏共用 EDGE_ICONS —— 两边条目必须一致，原来抽屉是另一份硬编码
  const navBtn=(k,label,ic)=>`<button data-nav="${k}" aria-pressed="${navOn(k)}">
    ${icon(ic)}<span>${label}</span></button>`;
  $('#drawer').innerHTML=
    `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
      <b class="disp" style="font-size:15px;letter-spacing:.1em">导航与筛选</b>
      <button id="drawerClose" class="ib" title="收起">${icon('x')}</button></div>`+
    `<div class="dnav">${EDGE_ICONS.map(([k,label,ic])=>navBtn(k,label,ic)).join('')}</div>`+
    sec('来源',chips(facetData.locations.map(l=>({k:l.k,label:LOC[l.k]||l.k,n:l.n,
        cost:(l.k==='pikpak'||l.k==='online')?'metered':'free'})),'loc',true),'','src')
    +sec('时长',facetData.stats.duration?`<div class="duration-filter"><div class="duration-readout"><span id="durMinText">不限</span><b>—</b><span id="durMaxText">不限</span></div>
      <div class="dual-range" id="durationRange"><span class="range-base"></span><span class="range-fill"></span>
        <input id="durMin" type="range" min="0" max="180" step="5" value="${filterState.dur_min?Math.min(180,+filterState.dur_min/60):0}" aria-label="最短时长（分钟）">
        <input id="durMax" type="range" min="0" max="180" step="5" value="${filterState.dur_max?Math.min(180,+filterState.dur_max/60):180}" aria-label="最长时长（分钟）"></div></div>`:'','','meta')
    +sec('画幅',chips(facetData.orientations,'orient'),'','meta')
    +sec('创作者',chips(scopedCreators,'creator',false,26),scopedCreators.length>26?'<button data-more="creator">更多</button>':'','artist')
    +sec('内容标签',chips(facetData.tags,'tag',false,30),facetData.tags.length>30?'<button data-more="tag">更多</button>':'','general')
    +sec('规格',chips(facetData.tech,'tag',false,12),'','meta');
  const dc=$('#drawerClose'); if(dc)dc.onclick=()=>openDrawer(false);
  $('#drawer').querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{
    openIndex(b.dataset.page); closeDrawerAfterNav()});
  $('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));
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
/* 排序放在计数行 —— 顶栏放不下也不该放，这是列表的属性 */
const SORTS=[['seed','推荐顺序'],['daily','每日轮换'],['rand','随机'],['rating','评分'],
             ['o','高潮计数'],['plays','观看次数'],['long','时长'],['big','体积'],
             ['new','最近入库'],['played','最近看的']];
function renderCount(){
  const n=$('#grid').querySelectorAll(':scope > .card[data-id]').length;   // 竖屏条不计入「显示 N」
  $('#count').innerHTML=
    `<span class="mono">${total.toLocaleString()} 个符合 · 显示 ${n}</span>`
    +(state.state==='trash'
      // 回收站是待清理队列，不是浏览列表：换一批和九种排序在这里没有意义。
      ? `<span class="sorts"><button class="batchaction" id="emptyTrash" title="永久删除回收站内容">清空回收站</button></span>`
      : `<span class="sorts"><button class="batchaction" id="batchAction" title="换一批" aria-label="换一批">${icon('refresh-cw')}</button>`
        // 版式紧跟在「换一批」之后：它同属这一组操作，靠右和排序连成一条。
        +(javActive()?`<span class="javlayout">`+JAV_LAYOUTS.map(([k,label,ic])=>
          `<button data-jav-layout="${k}" aria-pressed="${k===javLayout()}" title="${esc(label)}"
            aria-label="${esc(label)}">${icon(ic)}</button>`).join('')+`</span>`:'')
        +SORTS.map(([k,l])=>`<button data-sort="${k}" aria-pressed="${state.sort===k}">${l}</button>`).join('')+`</span>`);
  if($('#batchAction'))$('#batchAction').onclick=()=>{state.sort='seed';state.seed=rollSeed();load(true)};
  $('#count').querySelectorAll('[data-jav-layout]').forEach(b=>
    b.onclick=()=>setJavLayout(b.dataset.javLayout));
  if(state.state==='trash')$('#emptyTrash').onclick=async(e)=>{
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
    state.sort=b.dataset.sort;
    if(state.sort==='seed')state.seed=rollSeed();
    load(true)});
}

/* ── 组合筛选：多个标签同时生效 ── */
const tagList=()=>(state.tag||'').split(',').filter(Boolean);
function toggleTag(t){
  if(!t){state.tag='';}
  else{const cur=tagList();const i=cur.indexOf(t);
    i>=0?cur.splice(i,1):cur.push(t);state.tag=cur.join(',')}
  buildBars();load(true);
}
function renderCombo(){
  const cur=tagList(); const extra=[];
  if(state.creator)extra.push(['creator',state.creator]);
  if(state.studio)extra.push(['studio',state.studio]);
  if(!cur.length&&!extra.length){$('#combo').innerHTML='';return}
  $('#combo').innerHTML=
    extra.map(([k,v])=>`<span class="cb">${k==='creator'?'创作者':'厂牌'} ${esc(v)}
      <b data-clear="${k}">✕</b></span>`).join('')
    +cur.map(t=>`<span class="cb">${esc(t)} <b data-untag="${esc(t)}">✕</b></span>`).join('')
    +`<button class="clr" id="clrAll">全部清除</button>`;
  $('#combo').querySelectorAll('[data-untag]').forEach(b=>b.onclick=()=>toggleTag(b.dataset.untag));
  $('#combo').querySelectorAll('[data-clear]').forEach(b=>b.onclick=()=>{
    state[b.dataset.clear]='';buildBars();load(true)});
  $('#clrAll').onclick=()=>{state.tag='';state.creator='';state.studio='';buildBars();load(true)};
}

/* ── 统计与管理 ── */
async function openStats(push=true){
  releaseHoverPreviews();
  if(push)route('/stats');
  document.body.classList.remove('entity-open');
  disposeStage(false);
  const d=await api('/api/stats');
  $('#stats').hidden=false; $('#index').hidden=true; $('#grid').innerHTML='';buildManageBar();
  $('#count').textContent=''; $('#loadSentinel').hidden=true; $('#shortsSec').hidden=true;
  $('#tiers').style.display='none'; $('#tagbar').style.display='none';
  const a=d.attribution, cs=d.consumption;
  const pct=(x,y)=>y?Math.round(x/y*100):0;
  const gb=b=>b>=1099511627776?(b/1099511627776).toFixed(2)+' TB':(b/1073741824).toFixed(1)+' GB';
  const hrs=s=>s>=3600?(s/3600).toFixed(1)+' 小时':Math.round(s/60)+' 分钟';
  const bar=(x,y)=>`<div class="prog"><i style="width:${pct(x,y)}%"></i></div>`;
  const card=(t,body)=>`<div class="scard2"><h3>${t}</h3>${body}</div>`;
  const kv=(k,v,u)=>`<div class="kv"><span>${k}</span><b>${v}${u?`<span class="u">${u}</span>`:''}</b></div>`;
  $('#stats').innerHTML=`
    <div class="statshead"></div>
    <div class="scards">
      ${card('库存', d.by_loc.map(l=>kv(LOC[l.k]||l.k, l.videos.toLocaleString(), gb(l.bytes))).join('')
        + kv('合计', d.by_loc.reduce((s,l)=>s+l.videos,0).toLocaleString(),
             gb(d.by_loc.reduce((s,l)=>s+l.bytes,0))))}
      ${card('归属进度',
         kv('有创作者', a.creator.toLocaleString(), pct(a.creator,a.videos)+'%')+bar(a.creator,a.videos)
        +kv('有番号', a.code.toLocaleString(), pct(a.code,a.videos)+'%')+bar(a.code,a.videos)
        +kv('有厂牌', a.studio.toLocaleString(), pct(a.studio,a.videos)+'%')+bar(a.studio,a.videos))}
      ${card('加工进度',
         kv('已抽帧', a.thumb.toLocaleString(), pct(a.thumb,a.videos)+'%')+bar(a.thumb,a.videos)
        +kv('已探测时长', a.duration.toLocaleString(), pct(a.duration,a.videos)+'%')+bar(a.duration,a.videos)
        +kv('有内容标签', d.tag_cov.toLocaleString(), pct(d.tag_cov,a.videos)+'%')+bar(d.tag_cov,a.videos))}
      ${card('观看',
         `<div class="big">${cs.played.toLocaleString()}</div><div class="bigsub">看过的片子</div>`
        +kv('累计观看', hrs(cs.play_seconds))
        +kv('高潮计数', cs.o_total.toLocaleString())
        +kv('快进扫过', cs.skimmed.toLocaleString(), '真实观看远低于到达位置')
        +kv('不合口味', cs.dislike.toLocaleString())
        +kv('看过了', cs.seen.toLocaleString())
        +kv('回收站', cs.trash.toLocaleString()))}
      ${card('标签来源', d.tag_source.map(t=>
          kv(t.k, t.n.toLocaleString(), t.assets.toLocaleString()+' 个视频')).join(''))}
      ${card('系统盘', d.system_disk
        ? kv('可用', gb(d.system_disk.free), pct(d.system_disk.free,d.system_disk.total)+'%')
          +bar(d.system_disk.free,d.system_disk.total)
          +`<div class="bigsub">CloudDrive 的块缓存会长在这里，低于 40 GB 抽帧任务会拒绝启动</div>`
        : '—')}
    </div>
    <div class="scard2" style="margin-bottom:18px"><h3>内容标签 Top 30</h3>
      <div class="tagwall">${d.top_tags.map(t=>
        `<button class="tg ${t.cat}" data-k="${esc(t.k)}" style="padding:5px 12px;font-size:13px">
          ${esc(t.k)} <span style="opacity:.6;font-size:11px">${t.n.toLocaleString()}</span></button>`).join('')}</div></div>
    ${d.recent.length?`<div class="scard2"><h3>最近看过</h3>${d.recent.map(r=>{
      const real=r.duration?Math.min(r.play_seconds/r.duration,1)*100:0;
      const mx=(r.max_reached||0)*100;
      return kv(esc((r.creator?r.creator+' · ':'')+r.name).slice(0,90),
        `真实看 ${real.toFixed(0)}% / 到达 ${mx.toFixed(0)}%`,
        real<mx-25?'快进扫过':(r.o_count?`⌀ ${r.o_count}`:''));}).join('')}</div>`:''}`;
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
  buildManageBar();   // 放在最后：管理区要盖掉上面刚恢复的首页横条
}
function closeStats(push=true){if(push)route('/');showHomeSurfaces();load(true)}

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
  const data=await api('/api/playlists');
  if(location.pathname!=='/playlists')return;
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;$('#tiers').style.display='none';$('#tagbar').style.display='none';
  $('#managebar').hidden=true;$('#manageTitle').hidden=true;buildEdge();
  const cards=(data.items||[]).map(list=>{const resume=list.current_asset_id||list.preview_asset_id;
    const poster=list.preview_asset_id?`<img src="/poster?id=${list.preview_asset_id}&c=4" alt="" loading="lazy" onerror="this.remove()">`:'';
    return `<article class="playlistcard" data-playlist-card="${list.id}"><button class="playlistcover" data-open-playlist="${list.id}" ${resume?'':'disabled'}>${poster}<span>${list.item_count} 个视频</span></button>
      <div class="playlistmeta"><input data-playlist-name maxlength="80" value="${esc(list.name)}" aria-label="播放列表名称"><small>${list.source_kind==='mix'?'由 Mix 保存':'手动播放列表'}</small></div>
      <div class="playlistactions"><button data-rename-playlist="${list.id}">保存名称</button><button data-open-playlist="${list.id}" ${resume?'':'disabled'}>继续播放</button><button class="danger" data-delete-playlist="${list.id}">删除</button></div></article>`}).join('');
  $('#stats').innerHTML=`<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><form class="playlistcreate" id="newPlaylist"><label>新播放列表<input name="name" maxlength="80" placeholder="输入名称" required></label><button type="submit">新建</button><span data-playlist-state></span></form></header><div class="playlistcards">${cards||'<p class="empty">还没有播放列表</p>'}</div></section>`;
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

let reviewData=null,reviewCategory='metadata_fields';
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
  buildManageBar();
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#stats').innerHTML='<div class="review"><p class="empty">正在比对…</p></div>';
  dupData=await api('/api/duplicates?limit=120');
  if(location.pathname!=='/duplicates')return;
  renderDuplicates();
}
function renderDuplicates(){
  const d=dupData;if(!d)return;
  const groups=d.groups||[];
  $('#stats').innerHTML=`<div class="review">
    <p class="dupsum mono">${d.total} 组 · ${d.files} 个文件 · 可回收 ${fmtSize(d.reclaimable)}</p>
    <div class="dupactions">
      <button data-dup-all="largest">全部保留最大</button>
      <button data-dup-all="longest">全部保留最长</button>
      <button data-dup-all="115">全部优先 115</button>
      <button data-dup-all="pikpak">全部优先 PikPak</button></div>
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
        <button class="dupname" data-open-dup="${f.id}" title="${esc(f.name)}">${esc(f.name)}</button>
        <span class="mono">${esc(LOC[f.location]||f.location||f.drive||'')}</span>
        <span class="mono">${fmtSize(f.size||0)}</span>
        <span class="mono">${fmtDur(f.duration)}</span></div>`).join('')}</div>
    </section>`).join(''):'<p class="empty">没有找到重复文件</p>'}</div>`;
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
  buildManageBar();
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';$('#count').textContent='';
  $('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;$('#tiers').style.display='none';$('#tagbar').style.display='none';
  /* ADR-0018：确定的那部分先落库再取队列，否则它们会在队列里白占一轮。
     失败不拦页面——只读端（reader）本来就会 409，那是正常状态不是错误；
     但也不静默吞掉，留一行 console 便于排查。 */
  try{
    const auto=await api('/api/review/auto-apply',{method:'POST',body:'{}'});
    if(auto&&auto.applied)console.info(`自动落库 ${auto.applied} 条（ADR-0018）`);
  }catch(e){console.info('自动落库未执行：'+e.message)}
  reviewData=await api('/api/review');
  if(location.pathname!=='/review')return;
  const render=()=>{
    const rows=reviewData.sections[reviewCategory]||[];
    const title=REVIEW_LABELS[reviewCategory];
    const value=row=>row.tags||row.japanese_name||row.path||row.suggested_query||'';
     $('#stats').innerHTML=`<div class="review">
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
             <div><b title="${esc(asset.name||'')}">${esc(asset.code||asset.name||'原视频')}</b>
               <button type="button" data-review-open-item="${asset.id}">${icon('play')}打开原视频</button></div></div>`).join('')}</div>`:'';
         const origin=comparisonOrigin||subjectKind&&subjectName?comparisonOrigin||`<div class="reviewentity">
             <button class="reviewentityface" data-entity-kind="${subjectKind}" data-entity-name="${esc(subjectName)}"
               aria-label="打开创作者页：${esc(subjectName)}">${avatarInner(subjectName,
                 row.entity_id?{id:row.entity_id}:null,null,subjectKind)}</button>
             <div><b title="${esc(subjectName)}">${esc(subjectName)}</b>
               <button type="button" data-entity-kind="${subjectKind}" data-entity-name="${esc(subjectName)}">${icon('user-round')}打开创作者</button>
               ${works?`<small class="mono">${works.toLocaleString()} 部作品</small>`:''}</div></div>`
           :row.asset_id?`<div class="revieworigin">
             <button class="revieworigincover" data-review-open-item="${row.asset_id}" aria-label="打开原视频 ${esc(row.asset_name||'')}">
               ${row.asset_preview_url?`<img src="${esc(row.asset_preview_url)}" alt="" loading="lazy" onerror="this.remove()">`:'<span>无封面</span>'}</button>
             <div><b title="${esc(row.asset_name||'')}">${esc(row.asset_name||'原视频')}</b>
               <button type="button" data-review-open-item="${row.asset_id}">${icon('play')}打开原视频</button></div></div>`:'';
         /* 只有一个候选时没什么可选的，单选圈只是让人以为还有别的选项。
            改成纯展示，几何对齐上面的「打开原视频」块。
            radio 保留但不可见：提交路径读的就是 `[name^="metadata-"]:checked`，
            删掉它会让批准退化成「必须选择一个来源值」的报错，而不是少一个圈。 */
         const candidateBody=candidate=>`<b>${esc(candidate.source)}${candidate.official?' · 官方优先':''}</b>`
           +`<span>${esc(candidate.display_value||'')}</span>`
           +(candidate.warnings||[]).map(warning=>`<i>${esc(warning)}</i>`).join('');
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
         return `<article class="reviewitem" data-review-key="${esc(key)}" data-decision="${esc(decision)}">${
           // 实体类卡片的名字已经写在创作者入口里，再画一个 h4 就是同一行字上下两遍。
           subjectKind&&subjectName?'':`<h4>${esc(titleText)}</h4>`}${
           // 账本规范名当标题，抓取来源给的写法（多为罗马音）留作副标题。
           row.source_name?`<p class="reviewalias">来源写法：${esc(row.source_name)}</p>`:''}${
           // 实体类卡片的作品数已经写在创作者入口里，这里再写一遍就是同一个数字两处。
           subjectKind&&subjectName?'':`<p>${esc(row.board||row.assets?`样本/资产：${row.video_count||row.assets||''}`:'')}</p>`}${origin}${tags?`<div class="reviewtags">${tags}</div>`:''}${preview}<p>${esc(evidence)}</p><div class="reviewactions"><button class="approve" data-review-status="approved"${canApprove?'':' disabled'}>${approveLabel}</button><button class="skip" data-review-status="skipped">跳过</button><button class="reject" data-review-status="rejected">拒绝</button><span class="reviewstate" aria-live="polite"></span></div></article>`}).join(''):'<p class="empty">暂无候选</p>'}</div></section></div>`;
     wireReviewAssets($('#stats'));
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
  buildManageBar();$('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#stats').innerHTML='<div class="review"><p class="empty">正在读取…</p></div>';
  qualityData=await api('/api/quality-goals?limit=200');
  if(location.pathname!=='/quality-goals')return;
  const items=qualityData.items||[];
  $('#stats').innerHTML=`<div class="qualitylist">${items.length?items.map(item=>{
    const preview=item.has_cover?`/cover?code=${encodeURIComponent(item.code||'')}`:`/poster?id=${item.id}&c=4`;
    return `<article class="qualityitem"><button class="qualitycover" data-quality-open="${item.id}" aria-label="打开 ${esc(item.name)}">
        <img src="${preview}" alt="" loading="lazy" onerror="this.remove()"></button>
      <div><h3><button data-quality-open="${item.id}">${esc(item.name)}</button></h3>
        <p class="mono">${srcBadge(item.location,item.cost)}<span>${esc(LOC[item.location]||item.location)}</span><span>${fmtDur(item.duration)}</span><span>${fmtSize(item.size||0)}</span></p>
        ${item.reason?`<p>${esc(item.reason)}</p>`:''}</div></article>`}).join(''):'<p class="empty">没有标记中的高清版目标</p>'}</div>`;
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
let followData=null,followFilter='new',followBusy=false;
const FOLLOW_FILTERS=[['new','未看'],['seen','已看'],['saved','已保存'],['ignored','已忽略'],['','全部']];

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
  // 站点只给「1 周前」时换算出来的是近似值，界面必须照实说，不能冒充发布时间。
  return item.published_precision==='approximate'?`约 ${text}`:text;
}

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

/* 行首那一格说明「这条和主条目的关系」。三种语境的答案不一样：
   跨站重复项要说是哪个站，线程动态要说是什么时候的哪条回复，本站变体才说变体名。
   把线程回复标成「main」是没有信息量的——一个线程里九条回复全是 main。 */
function followVariantRow(group,item,mark){
  let label=mark;
  if(!label&&group.is_release)label=localTime(item.published_at).slice(5,10)||'动态';
  if(!label)label=item.variant_kind==='wip'?'WIP':(item.variant_label||item.variant_kind);
  /* 线程里九条回复的标题全是线程名，摘要才是那条动态的内容。
     只发了附件的回复没有正文，这时说清楚是没正文，比把线程名再印一遍强。 */
  const body=group.is_release
    ?(item.summary||(item.has_media?'（仅附件）':'（无正文）')):item.title;
  const title=group.is_release&&item.author?`${item.author}：${body}`:body;
  return `<li><span class="fvkind ${esc(item.variant_kind)}">${esc(label)}</span>
    <a href="${esc(item.url||'#')}" target="_blank" rel="noreferrer noopener">${esc(title)}</a>
    <button data-follow-save="${item.id}"${item.status==='saved'?' disabled':''}>${
      item.status==='saved'?'已保存':'保存'}</button></li>`;
}

function followCard(group){
  const item=group.primary;
  const thumb=item.thumb_url
    ? `<img src="${esc(item.thumb_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">`
    : `<span class="fnothumb">${esc(item.provider_label)}</span>`;
  const rows=[...group.variants.map(v=>followVariantRow(group,v)),
              ...group.duplicates.map(d=>followVariantRow(group,d,d.provider_label))].join('');
  return `<article class="followitem" data-follow-item="${item.id}" data-status="${esc(item.status)}">
    <a class="fthumb" href="${esc(item.url||'#')}" target="_blank" rel="noreferrer noopener">${thumb}</a>
    <div class="fbody">
      <h4><a href="${esc(item.url||'#')}" target="_blank" rel="noreferrer noopener">${esc(item.title)}</a></h4>
      <p class="mono"><span>${esc(item.provider_label)}</span><span>${followWhen(item)}</span>${
        item.duration?`<span>${fmtDur(item.duration)}</span>`:''}</p>
      <div class="fbadges">${followBadges(group)}</div>
      ${rows?`<ul class="fvariants">${rows}</ul>`:''}
      ${item.media_needs_credential?'<p class="fnote">媒体需要登录会话才能取，发现本身不需要</p>':''}
      <div class="factions">
        <button data-follow-save="${item.id}"${item.status==='saved'?' disabled':''}>${
          item.status==='saved'?`已保存 · asset #${item.asset_id}`:'保存到账本'}</button>
        <button data-follow-status="${item.id}" data-to="seen"${item.status==='seen'?' disabled':''}>标记已看</button>
        <button data-follow-status="${item.id}" data-to="ignored"${item.status==='ignored'?' disabled':''}>忽略</button>
        ${/* 进得去就要出得来：已看和已忽略都能退回未看。已保存不给退——那一步写了
             ledger，撤销要删 asset，不是一个按钮该做的事。 */
          item.status==='seen'||item.status==='ignored'
            ?`<button data-follow-status="${item.id}" data-to="new">恢复未看</button>`:''}
        <span class="fstate" aria-live="polite"></span>
      </div>
    </div></article>`;
}

/* ── 看的那一页 ── */
function renderFollow(){
  const groups=followData.groups||[],counts=followData.counts||{};
  const sources=followData.sources||[];
  const broken=sources.filter(s=>s.last_status==='error'||s.last_status==='unauthorized');
  $('#stats').innerHTML=`<div class="follow">
    <div class="reviewtabs">${FOLLOW_FILTERS.map(([key,label])=>
      `<button data-follow-filter="${key}" aria-pressed="${key===followFilter}">${label}${
        key?` <span class="n mono">${counts[key]||0}</span>`:''}</button>`).join('')}
      <button class="fcheck" data-follow-manage>${icon('settings')}管理关注</button></div>
    ${broken.length?`<p class="fwarn">${broken.length} 个来源上次检查失败，去
      <button class="flink" data-follow-manage>管理关注</button>看原因。</p>`:''}
    <div class="followlist">${groups.length?groups.map(followCard).join('')
      :sources.length?'<p class="empty">没有符合条件的更新</p>'
      :`<p class="empty">还没有关注任何来源。<button class="flink" data-follow-manage>去添加</button></p>`}</div></div>`;
  wireFollowItems();
  $('#stats').querySelectorAll('[data-follow-filter]').forEach(button=>button.onclick=()=>{
    followFilter=button.dataset.followFilter;openFollow(false)});
  $('#stats').querySelectorAll('[data-follow-manage]').forEach(button=>
    button.onclick=()=>openFollowManage());
}

async function openFollow(push=true){
  releaseHoverPreviews();disposeStage(false);
  document.body.classList.remove('entity-open','index-open');
  if(push)route('/follow');
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#tiers').style.display='none';$('#tagbar').style.display='none';
  $('#managebar').hidden=true;$('#manageTitle').hidden=true;buildEdge();
  $('#stats').innerHTML='<div class="follow"><p class="empty">正在读取…</p></div>';
  followData=await api(`/api/follow?limit=300${followFilter?`&status=${followFilter}`:''}`);
  if(location.pathname!=='/follow')return;
  renderFollow();
  window.scrollTo({top:0,behavior:'smooth'});
}

/* ── 管的那一页 ── */
function followSourceRow(source){
  const state=source.last_status||'未检查';
  const bad=state==='error'||state==='unauthorized';
  const idle=!source.last_checked_at;
  return `<li class="fsource${bad?' bad':idle?' idle':''}">
    <b>${esc(source.label)}</b><span class="mono">${esc(source.provider_label)}</span>
    <span class="mono">${esc(source.last_checked_at?localTime(source.last_checked_at):'未检查')}</span>
    <span class="fstatus">${esc(state)}</span>
    <button data-follow-check="${source.id}">检查</button>
    <button class="fremove" data-follow-remove="${source.id}" title="不再追这个来源">移除</button>
    ${source.last_error?`<i>${esc(source.last_error)}</i>`:''}</li>`;
}

const CRED_STATE={required:['必须配置','req'],optional:['可选','opt'],
  none:['不需要','none'],blocked:['接不进来','blocked']};

function followCredentialRow(row){
  const [label,kind]=CRED_STATE[row.requirement]||CRED_STATE.none;
  const configured=row.present&&!row.missing.length;
  /* 只有「必须配置而且没配」才自动展开——那是唯一需要你现在动手的情况。 */
  const needsAttention=row.requirement==='required'&&!configured;
  const fields=(row.needs||[]).map(name=>`<label class="fcredfield">
    <span>${esc(name)}</span>
    <input type="password" name="${esc(name)}" autocomplete="off" spellcheck="false"
      placeholder="${row.fields.includes(name)?'已保存，留空表示不改':'未填写'}"></label>`).join('');
  /* 值只往磁盘走，不回显：已保存的字段这里也是空的，占位文字说明留空等于不改。 */
  const body=row.requirement==='none'?'<p>这个来源不需要凭据。</p>'
    :row.requirement==='blocked'?`<p>${esc(row.why)}</p>`
    :`<p>${esc(row.why)}</p><p>${esc(row.howto)}</p>
      ${row.where?`<p><a href="${esc(row.where)}" target="_blank" rel="noreferrer noopener">${esc(row.where)}</a></p>`:''}
      <form class="fcredform" data-cred-form="${esc(row.provider)}">
        ${fields}
        <div class="fcredactions"><button type="submit">保存</button>
          ${configured?`<button type="button" data-cred-clear="${esc(row.provider)}">清除</button>`:''}
          <span data-cred-state aria-live="polite"></span></div>
      </form>
      <p class="mono fcredpath">${esc(row.path)}</p>
      ${row.world_readable?'<p class="fcredwarn">文件权限过宽，建议 chmod 600</p>':''}`;
  return `<details class="fcred ${esc(kind)}${configured?' ok':''}"${needsAttention?' open':''}>
    <summary><b>${esc(row.provider_label)}</b>
      <span class="fcredstate">${esc(configured&&row.requirement!=='none'?'已配置':label)}</span>
      ${row.missing.length?`<span class="fcredmissing">缺 ${esc(row.missing.join('、'))}</span>`:''}
    </summary>${body}</details>`;
}

function renderFollowManage(credentials){
  const sources=followData.sources||[],counts=followData.counts||{};
  const broken=sources.filter(s=>s.last_status==='error'||s.last_status==='unauthorized');
  /* 两栏：左边是干活的地方（加来源、看来源），右边是配置。
     原来四张通栏卡片各自只装几行内容，在宽屏上就是几条空长条加一大片右留白。
     计数不再单独占一张卡——它是来源列表的注脚，不是一个功能。 */
  $('#stats').innerHTML=`<div class="follow followmanage">
    <div class="fmain">
      <section class="fcard">
        <div class="fcardhead"><h3>添加关注</h3>
          <button class="fghost" data-follow-view>${icon('globe')}去看更新</button></div>
        <form class="faddform" id="followAdd">
          <textarea name="lines" rows="1" required spellcheck="false"
            aria-label="来源链接、名字或 id"
            placeholder="粘链接、名字或 id"></textarea>
          <button type="submit">查找</button>
        </form>
        <p class="fhint"><span data-follow-add-state aria-live="polite"></span>
          链接直接认得，名字会去六个来源各查一遍。要一次加多个就每行一条。
          首次按名字查要下载创作者索引，可能几十秒。</p>
      </section>
      <div id="followPicks"></div>
      <section class="fcard">
        <div class="fcardhead"><h3>关注列表 <span class="n mono">${sources.length}</span></h3>
          <button class="fprimary" data-follow-check=""${sources.length?'':' disabled'}>${
            icon('refresh-cw')}检查全部更新</button></div>
        ${broken.length?`<p class="fwarn">${broken.length} 个来源上次检查失败，原因见下方那一行。</p>`:''}
        ${sources.length?`<ul class="fsources">${sources.map(followSourceRow).join('')}</ul>
          <p class="fcounts">未看 <b>${counts.new||0}</b> · 已看 <b>${counts.seen||0}</b>
            · 已保存 <b>${counts.saved||0}</b> · 已忽略 <b>${counts.ignored||0}</b>
            ${counts.new?`<button class="flink" data-follow-bulk="seen">全部标记已看</button>
              <button class="flink" data-follow-bulk="ignored">全部忽略</button>`:''}</p>`
          :'<p class="empty fempty">还没有关注任何来源。把链接或名字粘进上面的输入框。</p>'}
      </section>
    </div>
    <aside class="faside">
      <section class="fcard">
        <div class="fcardhead"><h3>凭据</h3></div>
        <div class="fcreds">${(credentials.providers||[]).map(followCredentialRow).join('')}</div>
        <p class="fhint">凭据写在<b>运行 Peach 的那台机器</b>上（不是你现在这台浏览器所在的机器），
          不进 Git、URL、日志或 ledger。保存后页面上不会再显示出来。
          Windows 上不收紧文件权限——NTFS 走 ACL，<code>chmod</code> 在那里没有效果。</p>
      </section>
    </aside></div>`;
  wireFollowManage();
}


async function openFollowManage(push=true){
  releaseHoverPreviews();disposeStage(false);
  document.body.classList.remove('entity-open','index-open');
  if(push)route('/follow-manage');
  buildManageBar();
  $('#stats').hidden=false;$('#index').hidden=true;$('#grid').innerHTML='';
  $('#count').textContent='';$('#loadSentinel').hidden=true;$('#shortsSec').hidden=true;
  $('#stats').innerHTML='<div class="follow"><p class="empty">正在读取…</p></div>';
  const [data,credentials]=await Promise.all([
    api('/api/follow?limit=1'),api('/api/follow/credentials')]);
  if(location.pathname!=='/follow-manage')return;
  followData=data;
  renderFollowManage(credentials);
  window.scrollTo({top:0,behavior:'smooth'});
}

/* ── 共用接线 ── */
function wireFollowItems(){
  const root=$('#stats');
  root.querySelectorAll('[data-follow-status]').forEach(button=>button.onclick=async()=>{
    await followWrite(button,'/api/follow/status',
      {item:+button.dataset.followStatus,to:button.dataset.to})});
  root.querySelectorAll('[data-follow-save]').forEach(button=>button.onclick=async()=>{
    await followWrite(button,'/api/follow/save',{item:+button.dataset.followSave})});
}

function wireFollowManage(){
  const root=$('#stats'),form=root.querySelector('#followAdd');
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
    const state=form.querySelector('[data-follow-add-state]'),button=form.querySelector('button');
    const lines=String(new FormData(form).get('lines')||'').split('\n')
      .map(line=>line.trim()).filter(Boolean);
    if(!lines.length)return;
    const byName=lines.some(line=>!line.includes('/'));
    button.disabled=true;
    state.textContent=byName?'查找中…（首次按名字查要下载创作者索引，可能几十秒）':'识别中…';
    try{
      const result=await api('/api/follow/resolve',{method:'POST',
        body:JSON.stringify({lines})});
      state.textContent='';if(box){box.value='';box.style.height='auto'}
      renderFollowPicks(result.results||[]);
    }catch(error){state.textContent=error.message||'查找失败'}
    finally{button.disabled=false}
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
  root.querySelectorAll('[data-follow-check]').forEach(button=>button.onclick=async()=>{
    if(followBusy)return;
    followBusy=true;const label=button.innerHTML;button.disabled=true;
    button.textContent='检查中…';
    try{
      const id=button.dataset.followCheck;
      const result=await api('/api/follow/check',{method:'POST',
        body:JSON.stringify(id?{source:+id}:{})});
      // 一个来源失败不该让其余来源的更新一起消失，所以逐条报，不整体报错。
      const failed=(result.results||[]).filter(r=>!r.ok);
      if(failed.length)console.warn('追更检查失败：',failed);
      /* 证据没存下来不算检查失败，但也不能悄悄少一份原始响应——
         外置盘没插的时候就是这种情况。 */
      const noEvidence=(result.results||[]).filter(r=>r.evidence_error);
      await openFollowManage(false);
      if(noEvidence.length){
        const box=$('#followPicks');
        if(box)box.innerHTML=`<section class="fpicks"><h3>检查完成，但证据未存档</h3>
          <div class="fpick"><p class="fpickfail">${esc(noEvidence[0].evidence_error)}</p>
          <p>候选已经入库，只是这一次的原始响应没有留档。</p></div>
          <div class="fpickactions"><button data-pick-cancel>知道了</button></div></section>`;
        if(box)box.querySelector('[data-pick-cancel]').onclick=()=>{box.innerHTML=''};
      }
    }catch(e){button.innerHTML=label;alert('检查更新失败：'+e.message)}
    finally{followBusy=false;button.disabled=false}
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
    if(!confirm('清除这个来源的凭据？文件会被删除。'))return;
    button.disabled=true;
    try{
      await api('/api/follow/credential',{method:'POST',body:JSON.stringify(
        {provider:button.dataset.credClear,values:{}})});
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
}

/* 查找结果先摆出来由人勾选，不自动登记：发现要联网，结果也可能不止一个，
   替用户决定「就是这个」是错的。已经在追的项灰掉但仍显示，免得人以为没查到。 */
function renderFollowPicks(results){
  const box=$('#followPicks');
  if(!box)return;
  if(!results.length){box.innerHTML='';return}
  const blocks=results.map((row,index)=>{
    if(row.kind==='error')
      return `<div class="fpick bad"><b>${esc(row.line)}</b><p>${esc(row.error)}</p></div>`;
    const failures=Object.entries(row.failures||{});
    const items=(row.candidates||[]).map((c,ci)=>`<label class="fpickitem${c.known?' known':''}">
      <input type="checkbox" data-pick="${index}-${ci}" value="${esc(c.url)}"
        data-label="${esc(c.label)}"${c.known?' disabled':' checked'}>
      <span><b>${esc(c.provider_label)}</b> ${esc(c.label)}
        <i>${esc(c.known?'已经在追':c.evidence)}</i></span></label>`).join('');
    return `<div class="fpick"><b>${esc(row.line)}</b>
      ${items||'<p class="empty">这一条没有查到任何来源</p>'}
      ${failures.length?`<p class="fpickfail">${failures.map(([k,v])=>
        `${esc(k)}：${esc(v)}`).join('；')}</p>`:''}</div>`;
  }).join('');
  const total=results.reduce((n,row)=>n+(row.candidates||[])
    .filter(c=>!c.known).length,0);
  box.innerHTML=`<section class="fpicks"><h3>查找结果</h3>${blocks}
    ${total?`<div class="fpickactions"><button data-pick-add>添加选中</button>
      <button data-pick-cancel>取消</button><span data-pick-state aria-live="polite"></span></div>`
      :'<div class="fpickactions"><button data-pick-cancel>关闭</button></div>'}</section>`;
  box.querySelector('[data-pick-cancel]').onclick=()=>{box.innerHTML=''};
  const addButton=box.querySelector('[data-pick-add]');
  if(addButton)addButton.onclick=async()=>{
    const picked=[...box.querySelectorAll('[data-pick]:checked')];
    if(!picked.length)return;
    const state=box.querySelector('[data-pick-state]');
    addButton.disabled=true;
    let done=0;
    for(const input of picked){
      state.textContent=`添加中… ${++done}/${picked.length}`;
      try{
        await api('/api/follow/source',{method:'POST',body:JSON.stringify(
          {action:'add',url:input.value,label:input.dataset.label})});
      }catch(error){
        // 一条失败不该把其余的一起丢掉，逐条报。
        state.textContent=`${input.dataset.label}：${error.message}`;
      }
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
const TAG_CATEGORIES=[['all','全部'],['general','内容'],['artist','人物'],['character','角色'],['copyright','作品'],['meta','规格']];
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
      const ch=x.k.normalize('NFKC').trim().charAt(0).toUpperCase();
      const key=/[A-Z]/.test(ch)?ch:(/[0-9]/.test(ch)?'#':(/[\u3400-\u9fff]/.test(ch)?'中文':'其他'));
      (groups[key]||(groups[key]=[])).push(x)});
    return Object.entries(groups).sort(([a],[b])=>a.localeCompare(b,'zh-CN')).map(([letter,items])=>
      `<section class="alphagroup"><h3>${letter}</h3><div class="alphalist">${items.map(x=>
        `<button class="alphatag ${x.cat||'general'}" data-k="${esc(x.k)}"><span>${esc(x.k)}</span><span class="n">${x.n.toLocaleString()}</span></button>`).join('')}</div></section>`).join('')};
  const peopleHtml=items=>items.map(x=>`<button class="icell" data-k="${esc(x.k)}" data-kind="${entityKind}">
        <span class="ring">${avatarInner(x.k,
          kind==='performers'&&x.entity_id?{id:x.entity_id}:null, x.rep)}</span>
        <span class="nm">${esc(x.k)}</span><span class="n">${x.n.toLocaleString()}</span></button>`).join('');
  const tagHtml=items=>tagIndexMode==='alphabet'?`<div class="alphabet">${tagGroups(items)}</div>`:`<div class="tagwall index-tags">`+items.map(x=>`<button class="tg ${x.cat||'general'}" data-k="${esc(x.k)}"
        style="padding:5px 12px;font-size:13px">${esc(x.k)}
        <span style="opacity:.6;font-size:11px">${x.n.toLocaleString()}</span></button>`).join('')+`</div>`;
  const body=people?`<div class="igrid">${peopleHtml(d.items)}</div>`:tagHtml(tagItems);
  const filters=kind==='tags'?`<div class="tagfilters" aria-label="标签类型">${TAG_CATEGORIES.map(([key,label])=>
    `<button class="${key}" data-tag-category="${key}" aria-pressed="${tagIndexCategory===key}">${label}</button>`).join('')}</div>`:'';
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
    $('#index').hidden=true;state.tag=b.dataset.k;route('/?tag='+encodeURIComponent(state.tag));buildBars();load(true)});
  wireIndexEntries($('#indexBody'));
  let indexOffset=d.items.length;
  $('#indexMore').onclick=async()=>{const more=$('#indexMore');more.disabled=true;
    try{const next=await api(indexApi(indexOffset));if(requestSeq!==indexRequestSeq)return;
      indexOffset+=next.items.length;d.has_more=next.has_more;
      if(people){d.items.push(...next.items);const grid=$('#indexBody .igrid');
        grid.insertAdjacentHTML('beforeend',peopleHtml(next.items));wireIndexEntries(grid)}
      else{d.items.push(...next.items);tagItems.push(...next.items);$('#indexBody').innerHTML=tagHtml(tagItems);wireIndexEntries($('#indexBody'))}
      $('#indexCount').textContent=indexOffset+(next.has_more?'+':'')+' 项';more.hidden=!next.has_more}
    finally{if(requestSeq===indexRequestSeq)more.disabled=false}};
}

const ENTITY_LABELS={performer:'艺人',studio:'厂牌',creator:'创作者',series:'系列'};
/* 「女优」只用于番号发行物。素人、创作者自制和网红内容里的出镜者是艺人，
   套上 JAV 的行业称谓既不准确也会和创作者身份混淆。判据由后端 `is_jav` 给。 */
const performerLabel=it=>it&&it.is_jav?'女优':'艺人';
let entityRequestSeq=0;
async function fetchEntityItems(kind,name,filters,offset=0){
  const p=new URLSearchParams();p.set(kind,name);p.set('limit','48');p.set('offset',String(offset));p.set('sort','new');
  if(offset)p.set('count','0');
  ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&key!==kind)p.set(key,filters[key])});
  // 资料页继承 JAV 开关：女优页和厂牌页同样是按番号浏览的语境。
  if(state.jav==='1')p.set('jav','1');
  const items=await api('/api/items?'+p);cache(items.items);return items
}
function renderEntityCollection(kind,name,items,filters,append=false){
  const entityTag=filters.tag||'';
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  if(!append){section.innerHTML=`<h3></h3><div class="grid"></div><button class="entitymore" type="button">载入更多</button>`;
    section.dataset.total=String(items.total||0);
    section.querySelector('h3').textContent=`${ENTITY_LABELS[kind]||kind}的馆藏作品 · ${(items.total||0).toLocaleString()}${entityTag?' · '+entityTag:''}`}
  const grid=section.querySelector('.grid');
  grid.insertAdjacentHTML('beforeend',items.items.map(it=>cardHtml(it)).join(''));
  wireCards(grid,undefined,tag=>updateEntityCollection(
    kind,name,{...filters,tag:tag===entityTag?'':tag},true));
  const more=section.querySelector('.entitymore');
  more.hidden=append?!items.has_more:grid.children.length>=Number(section.dataset.total||0);
  const requestMore=async()=>{if(more.hidden||more.disabled)return;more.disabled=true;const seq=entityRequestSeq;
    try{const next=await fetchEntityItems(kind,name,filters,grid.children.length);
      if(seq===entityRequestSeq&&$('#index').dataset.entityKind===kind&&$('#index').dataset.entityName===name)
        renderEntityCollection(kind,name,next,filters,true)}
    finally{if(seq===entityRequestSeq)more.disabled=false}};
  more.onclick=requestMore;
  more._observer?.disconnect();
  if(!more.hidden){
    more._observer=new IntersectionObserver(entries=>{if(entries.some(x=>x.isIntersecting))requestMore()},{rootMargin:'320px'});
    more._observer.observe(more);
  }
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
  entityVideoCount=items.total||0;
  renderMediaTabs(kind,name,filters);
  $('#index').querySelectorAll('[data-entity-tag]').forEach(b=>
    b.setAttribute('aria-pressed',String(b.dataset.entityTag===filters.tag)));
  renderEntityCollection(kind,name,items,filters)
}
/* ── 资料页的照片 ─────────────────────────────────────────────────────────────
   图集就是目录：账本里没有图集实体，`<作品目录>\P\001.jpg` 这种约定本身就是分组依据，
   后端按目录聚合，用目录里最小的资产 id 当图集 id。三层：图集列表 → 瀑布流 → 灯箱。
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
let entityPhotos=null,entityMediaView=emptyMediaView(),entityVideoCount=0,photoWallItems=[];
const routeEntityView=(kind,name,view)=>{
  const filters=barsContext.type==='entity'?barsContext.filters:emptyEntityFilters();
  const search=entityViewSearch(filters,view);
  route(entityPath(kind,name)+(search?'?'+search:''))};
const photoTotalOf=()=>entityPhotos&&!entityPhotos.error?(entityPhotos.total||0):0;

function renderMediaTabs(kind,name,filters){
  const tabs=$('#index').querySelector('.mediatabs');if(!tabs)return;
  const photos=photoTotalOf();
  tabs.hidden=!photos;
  if(!photos){tabs.innerHTML='';return}
  const tab=(media,label,glyph,count)=>`<button data-media="${media}"
      aria-pressed="${(entityMediaView.media==='photos')===(media==='photos')}">${icon(glyph)}<span>${label}</span>
      <b class="mono">${count.toLocaleString()}</b></button>`;
  tabs.innerHTML=tab('videos','作品','play',entityVideoCount)+tab('photos','照片','layout-grid',photos);
  tabs.querySelectorAll('[data-media]').forEach(b=>
    b.onclick=()=>switchEntityMedia(kind,name,filters,b.dataset.media));
}

async function switchEntityMedia(kind,name,filters,media){
  if((entityMediaView.media==='photos')===(media==='photos')&&!entityMediaView.set)return;
  entityMediaView=media==='photos'?{media:'photos',set:0}:emptyMediaView();
  routeEntityView(kind,name,entityMediaView);
  renderMediaTabs(kind,name,filters);
  if(media==='photos'){renderPhotoSets(kind,name,filters);return}
  const seq=++entityRequestSeq;
  const items=await fetchEntityItems(kind,name,filters);
  if(seq!==entityRequestSeq)return;
  renderEntityCollection(kind,name,items,filters);
}

const photoSetCard=item=>`<button class="photoset" data-photo-set="${item.id}">
    <span class="photosetcover"><img src="/photo-thumb?id=${item.id}" alt="" loading="lazy"
      decoding="async" fetchpriority="low" onerror="this.remove()"></span>
    <span class="photosetname" title="${esc(item.title)}">${esc(item.title)}</span>
    <small class="mono">${item.n.toLocaleString()} 张 · ${fmtSize(item.bytes||0)}</small></button>`;

function renderPhotoSets(kind,name,filters){
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  const sets=(entityPhotos&&entityPhotos.sets)||[];
  section.innerHTML=`<h3>图集 · ${sets.length} 组 · ${photoTotalOf().toLocaleString()} 张</h3>
    <div class="photosets">${sets.map(photoSetCard).join('')}</div>`;
  section.querySelectorAll('[data-photo-set]').forEach(b=>
    b.onclick=()=>openPhotoSet(kind,name,filters,Number(b.dataset.photoSet)));
}

async function openPhotoSet(kind,name,filters,setId,push=true){
  const seq=++entityRequestSeq;
  const data=await api('/api/photo-set?id='+setId+'&limit=120');
  if(seq!==entityRequestSeq||data.error)return;
  entityMediaView={media:'photos',set:setId};
  if(push)routeEntityView(kind,name,entityMediaView);
  renderMediaTabs(kind,name,filters);
  renderPhotoWall(kind,name,filters,data);
}

const photoCell=(item,index)=>`<button class="photocell" data-photo-index="${index}" title="${esc(item.name)}">
    <img src="/photo-thumb?id=${item.id}" alt="${esc(item.name)}" loading="lazy"
      decoding="async" fetchpriority="low"
      onerror="this.closest('.photocell').remove()"></button>`;

function renderPhotoWall(kind,name,filters,data,append=false){
  const section=$('#index').querySelector('.entitysection');if(!section)return;
  if(!append){
    photoWallItems=[];
    section.innerHTML=`<div class="photohead">
        <button class="photoback" type="button">${icon('chevron-left')}<span>全部图集</span></button>
        <h3>${esc(data.title)} · ${(data.total||0).toLocaleString()} 张</h3>
        ${sourceTools(data.id)}</div>
      <div class="photowall"></div><button class="entitymore" type="button">载入更多</button>`;
    section.querySelector('.photoback').onclick=()=>{
      entityMediaView={media:'photos',set:0};
      routeEntityView(kind,name,entityMediaView);
      renderPhotoSets(kind,name,filters)};
    // 对账后整组数量都变了，重开这一组比逐格摘除简单也更不容易错。
    wireSourceTools(section.querySelector('.photohead'),
      ()=>openPhotoSet(kind,name,filters,data.id,false));
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
    try{const next=await api(`/api/photo-set?id=${data.id}&limit=120&offset=${photoWallItems.length}`);
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
   删除不进复核也不可恢复——手动删掉的就是不要的。真正要防的是把「盘没挂上」当成
   「文件没了」，那个闸门在服务端：整条来源不在线时直接拒绝，一行都不动。
   路径始终由服务端按 asset id 查，前端拿不到也不该拿到 `path`。 ── */
const SOURCE_HINTS={
  'source offline':'来源不在线，已拒绝对账（避免把没挂上的盘当成文件被删）',
  'source not mapped':'本机没有映射这个来源的盘符',
  'file missing':'源文件已经不在了，点右边同步把账本对齐',
  'unsupported platform':'当前服务端系统不支持直接定位文件',
  'reveal failed':'打开文件管理器失败',
};
const sourceHint=message=>SOURCE_HINTS[message]||message;

async function revealSource(id,status){
  status.textContent='正在定位…';
  try{
    await api('/api/reveal',{method:'POST',body:JSON.stringify({id})});
    status.textContent='已在服务端弹出文件管理器';
  }catch(e){status.textContent=sourceHint(e.message)}
}

async function syncMissing(id,status,done){
  status.textContent='正在核对目录…';
  try{
    const r=await api('/api/purge-missing',{method:'POST',body:JSON.stringify({id})});
    if(r.ok===false){status.textContent=sourceHint(r.error);return}
    status.textContent=r.removed
      ? `已从账本移除 ${r.removed} 项（核对 ${r.checked} 项）`
      : `目录内 ${r.checked} 项都还在，无需改动`;
    if(r.removed&&done)done(r);
  }catch(e){status.textContent=sourceHint(e.message)}
}

/* 两个按钮 + 一行状态。状态用 aria-live，屏幕阅读器和肉眼看到的是同一句。 */
const sourceTools=id=>`<div class="srctools">
    <button type="button" data-reveal="${id}" title="在文件管理器里打开源文件所在目录"
      aria-label="定位源文件">${icon('folder-open')}</button>
    <button type="button" data-sync="${id}" title="核对该目录：磁盘上已删除的，从账本一并移除"
      aria-label="同步删除">${icon('refresh-cw')}</button>
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
  style.rel='stylesheet';style.href='/vendor/swiper/14.1.0/swiper-bundle.min.css';
  document.head.appendChild(style);
  const script=document.createElement('script');
  script.src='/vendor/swiper/14.1.0/swiper-bundle.min.js';
  script.onload=()=>resolve(window.Swiper);
  script.onerror=()=>{swiperLoader=null;reject(new Error('swiper unavailable'))};
  document.head.appendChild(script)}));
const photoLightKeys=e=>{if(e.key==='Escape')closePhotoLightbox()};
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

function closePhotoLightbox(){
  if(!activeLightbox)return;
  document.removeEventListener('keydown',photoLightKeys);
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
      <div class="photocount mono" aria-live="polite">${index+1} / ${items.length}</div>
      <div class="photozoom">
        <button type="button" data-zoom-step="-1" aria-label="缩小">−</button>
        <input type="range" min="1" max="${ZOOM_MAX}" step="0.1" value="1" aria-label="缩放">
        <button type="button" data-zoom-step="1" aria-label="放大">+</button>
        <b class="mono">100%</b></div></div>
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
  /* Swiper 只在自己构造的那一刻量一次容器。灯箱是插进已经布好版的页面里的，
     窗口一改大小（或首屏字体、滚动条落定得比构造晚）slide 就停在旧宽度上，
     大图按错误的框缩放，看起来就是「显示不全」。挂个 ResizeObserver 让它重量。 */
  const resize=new ResizeObserver(()=>{main.update();strip.update()});
  resize.observe(box);
  activeLightbox={box,main,strip,resize,zoomBar};
  box.querySelector('.photoclose').onclick=closePhotoLightbox;
  // 只在背景本身上关闭：点图片、缩略图条和翻页按钮都不该退出。
  box.addEventListener('click',e=>{if(e.target===box)closePhotoLightbox()});
  document.addEventListener('keydown',photoLightKeys);
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
  const seq=++entityRequestSeq;
  const [d,items,photos]=await Promise.all([
    api(`/api/entity?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}`),
    fetchEntityItems(kind,name,filters),
    api(`/api/photos?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}`)]);
  if(d.error||seq!==entityRequestSeq||
     decodeURIComponent(location.pathname)!==decodeURIComponent(expectedPath))return;
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
  const tags=(d.tags||[]).map(x=>`<button data-entity-tag="${esc(x.k)}" aria-pressed="${entityTag===x.k}">${esc(x.k)}<small>${x.n.toLocaleString()}</small></button>`).join('');
  const related=(d.related_performers||[]).map(x=>`<button class="relatedperson" data-related-performer="${esc(x.k)}">
      <span class="ring"><span>${esc(x.k.slice(0,1))}</span><img src="/entity-image?kind=performer&id=${x.id}" alt="" loading="lazy"
        onerror="${x.rep?`if(!this.dataset.f){this.dataset.f='1';this.src='/avatar?id=${x.rep}'}else{this.remove()}`:`this.remove()`}"></span>
      <span class="nm">${esc(x.k)}</span><small>${x.n.toLocaleString()} 部</small></button>`).join('');
  $('#index').dataset.entityKind=kind;$('#index').dataset.entityName=name;
  $('#index').innerHTML=`<div class="entityhero"><div class="entityportrait ${kind==='performer'||kind==='creator'?'':'square'}">${image}<span>${esc(name.slice(0,1))}</span></div>
      <div><h2>${esc(d.canonical_name)}</h2>
        <div class="alias">${(d.aliases||[]).length?'别名 · '+d.aliases.map(esc).join(' / '):'暂无别名'} · ${d.asset_count.toLocaleString()} 个视频</div>
        ${d.summary?`<div class="entitysummary">${esc(d.summary)}</div>`:''}
        ${links?`<div class="entitylinks">${links}</div>`:''}
        ${terms?`<div class="entityterms">馆藏检索词 · ${terms}</div>`:''}</div></div>
    ${(tags||related)?`<div class="entitymeta">
      ${tags?`<section><h3>相关标签</h3><div class="entitytags">${tags}</div></section>`:''}
      ${related?`<section><h3>关联艺人</h3><div class="relatedpeople">${related}</div></section>`:''}
    </div>`:''}
    <div class="mediatabs" hidden></div>
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
  entityVideoCount=items.total||0;
  if(entityMediaView.media==='photos'&&!photoTotalOf())entityMediaView=emptyMediaView();
  renderMediaTabs(kind,name,filters);
  if(entityMediaView.media!=='photos')renderEntityCollection(kind,name,items,filters);
  else if(entityMediaView.set)await openPhotoSet(kind,name,filters,entityMediaView.set,false);
  else renderPhotoSets(kind,name,filters);
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
  ['follow','关注','globe'],
  ['immerse','沉浸模式','play'],
  ['manage','管理','settings'],
];
/* 统计、疑似广告、回收站、人工复核都是「管理」下的二级入口，不再各占一个顶层图标。
   URL 保持原样（/stats、/trash、/review、?state=ads），只是多了一层共同的导航条。
   顺序按做事顺序分成两段：先是库里已有的东西——看现状、复核新进来的候选、
   清广告与重复、落到回收站；再是要往外拿的——追更来源和高清版都是「还想要什么」，
   原先把追更来源夹在高清版和回收站中间，两边都不挨着。 */
const MANAGE_SECTIONS=[
  ['stats','统计','chart'],
  ['review','人工复核','square-check-big'],
  ['ads','疑似广告','alert'],
  ['dupes','重复文件','hard-drive'],
  ['trash','回收站','trash'],
  ['follow','追更来源','globe'],
  ['quality','高清版','sparkles'],
];
function manageSection(){
  const path=decodeURIComponent(location.pathname);
  if(path==='/stats')return 'stats';
  if(path==='/review')return 'review';
  if(path==='/trash')return 'trash';
  if(path==='/duplicates')return 'dupes';
  if(path==='/quality-goals')return 'quality';
  if(path==='/follow-manage')return 'follow';
  return state.state==='ads'?'ads':'';
}
function buildManageBar(){
  const current=manageSection(),bar=$('#managebar');
  bar.hidden=!current;
  // 管理区是行政界面，不该顶着首页的人物/厂牌横条和标签筛选。
  if(current){$('#tiers').style.display='none';$('#tagbar').style.display='none'}
  buildEdge();     // 顶层高亮跟随管理区；否则从首页进来时仍停在「首页」上
  paintJavBar();
  paintManageTitle();
  if(!current)return;
  bar.innerHTML=MANAGE_SECTIONS.map(([k,label,ic])=>
    `<button data-manage="${k}" aria-pressed="${k===current}">${icon(ic)}<span>${label}</span></button>`).join('');
  bar.querySelectorAll('[data-manage]').forEach(b=>b.onclick=()=>openManage(b.dataset.manage));
}
/* 管理区四个分页共用同一个标题元素。回收站和疑似广告走首页网格路径，
   本来就没有标题层；统计/复核/重复各自内嵌 h2 又导致字号不一致。 */
function paintManageTitle(){
  const current=manageSection(),el=$('#manageTitle');
  if(!el)return;
  const entry=MANAGE_SECTIONS.find(([k])=>k===current);
  el.hidden=!entry;
  if(entry)el.textContent=entry[1];
}
function openManage(section='stats'){
  if(section==='stats'){openStats();return}
  if(section==='review'){openReview();return}
  if(section==='dupes'){openDuplicates();return}
  if(section==='quality'){openQualityGoals();return}
  if(section==='follow'){openFollowManage();return}
  state.orient='';state.state=section==='trash'?'trash':'ads';
  route(section==='trash'?'/trash':'/');
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
  if(state.jav!=='1')return false;
  const path=decodeURIComponent(location.pathname);
  return path==='/'||path.startsWith('/performers/')||path.startsWith('/studios/');
}
function javLayout(){
  const raw=JAV_LAYOUT_ALIASES[appSettings.javLayout]||appSettings.javLayout;
  return allowedSetting(raw,JAV_LAYOUTS.map(([k])=>k),'big');
}
function setJavLayout(value){
  appSettings.javLayout=value;
  saveSettings();
  // 只重画卡片，不重新请求：版式是纯展示层的事。排序行会跟着一起重建。
  if(!$('#grid').hidden)load(true);
}
function paintJavBar(){
  // 版式按钮现在长在排序行里（见 renderCount），这里只负责收掉旧容器。
  const bar=$('#javbar');if(bar)bar.hidden=true;
}
function toggleJavMode(){
  state.jav=state.jav==='1'?'':'1';
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
  await load(true);
}
function navOn(k){
  const path=decodeURIComponent(location.pathname);
  if(k==='manage')return !!manageSection();
  if(k==='performers'||k==='tags')return path==='/'+k;
  if(k==='immerse')return path==='/immerse';
  if(k==='playlists')return path==='/playlists'||path.startsWith('/playlists/');
  if(k==='follow')return path==='/follow';
  if(k==='jav')return javActive();
  if(k==='shorts')return state.orient==='竖屏';
  // 首页只在真的停在首页列表上时亮：管理区、索引页、实体页都不算，
  // 否则它会和当前所在的入口同时高亮。
  if(k==='')return path==='/'&&!manageSection()&&!state.state&&!javActive()&&state.orient!=='竖屏';
  return path==='/'&&state.state===k&&state.orient!=='竖屏';
}
/* 窄栏与抽屉共用同一套跳转。两边曾各写一份分支，抽屉那份漏了追更和播放列表，
   点下去只把 state.state 设成一个后端不认识的值，看上去就是“点了没反应”。 */
function navTo(k){
  closeDrawerAfterNav();                 // 点了就收起抽屉，且短暂禁止悬停把它立刻弹回
  if(k==='immerse'){openTok();return}
  if(k==='playlists'){openPlaylists();return}
  if(k==='follow'){openFollow();return}
  if(k==='manage'){openManage();return}
  if(k==='jav'){toggleJavMode();return}
  if(k==='performers'||k==='tags'){openIndex(k);return}
  if(k==='shorts'){state.orient='竖屏';state.state=''}else{state.orient='';state.state=k}
  // 从管理区/索引页点回列表类入口时，路径还停在原处，高亮不会切换。
  if(location.pathname!=='/')route('/');
  showHomeSurfaces();
  buildEdge();buildBars();load(true);
}
function buildEdge(){
  $('#edge').innerHTML=EDGE_ICONS.map(([k,t,ic])=>
    `<button data-nav="${k}" title="${t}" aria-pressed="${navOn(k)}">
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
}
let edgeT=null;
$('#edge').addEventListener('mouseenter',()=>{if(Date.now()<drawerSuppressUntil)return;
  edgeT=setTimeout(()=>openDrawer(true),180)});
/* 滚动期间挂起悬停预览：内容在鼠标下滑过会连续触发 mouseenter，
   每次都新建 video 并发起 /stream 请求，直接把页面拖垮。 */
window.__scrolling=false; let scrollT=null;
let stickyFrame=0;
function updateStickySurfaces(){
  ['#tagbar','#count'].forEach(selector=>{
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
window.addEventListener('resize',scheduleStickySurfaces,{passive:true});

/* 只在真正进入 72 px 图标栏时展开；内容区左缘不再设隐形热区。 */
$('#edge').addEventListener('mouseleave',()=>clearTimeout(edgeT));
$('#drawer').addEventListener('mouseleave',()=>{
  setTimeout(()=>{if(!$('#drawer').matches(':hover')&&!$('#edge').matches(':hover'))openDrawer(false)},240)});
$('#scrim').onclick=()=>openDrawer(false);

/* ── 列表 ── */
let adsBatch=null,loadRequestSeq=0,listLoading=false;
async function load(reset){
  const requestSeq=reset?++loadRequestSeq:loadRequestSeq;
  if(!reset&&listLoading)return;
  if(!reset)listLoading=true;
  try{
  if(reset){barsContext={type:'home',filters:state};detailReturnBarsContext=null;disposeStage(false)}
  showHomeSurfaces();
  if(reset)offset=0;
  renderCombo();
  // 疑似广告是逐项处置队列，计数只是当前队列说明，不是需要跟随浏览的排序工具。
  const countRow=$('#count'),staticManageCount=state.state==='ads';
  countRow.classList.toggle('manage-static',staticManageCount);
  if(staticManageCount)countRow.classList.remove('is-stuck');
  if(state.state==='ads'){
    if(reset||!adsBatch){const nextAds=await api('/api/ads?limit=200');if(requestSeq!==loadRequestSeq)return;
      adsBatch=nextAds;cache(adsBatch.items)}
    const batch=adsBatch.items.slice(offset,offset+appSettings.batchSize);
    const html=batch.map(it=>cardHtml(it)).join('');
    if(reset)releaseHoverPreviews($('#grid'));
    if(reset)$('#grid').innerHTML=html;else $('#grid').insertAdjacentHTML('beforeend',html);
    $('#count').innerHTML=`疑似广告 ${adsBatch.total} 个 · 当前载入 ${$('#grid').children.length} 个 · 标记后统一复核，不会直接删除`;
    $('#loadSentinel').hidden=$('#grid').children.length>=adsBatch.items.length;
    $('#shortsSec').hidden=true;wireCards($('#grid'));paintSelection();return;
  }
  adsBatch=null;
  const p=new URLSearchParams(Object.entries(state).filter(([,v])=>v));
  /* 只有首页默认列表排除竖屏——那里另有独立的竖屏条承接它们。
     搜索必须能搜到竖屏作品，否则按名字找一条竖屏视频会得到 0 结果。 */
  if(location.pathname==='/'&&!state.q&&!state.orient)p.set('exclude_vertical','1');
  // JAV 模式恒不含竖屏：番号发行物本身就是横版，竖屏是另一类内容。
  if(state.jav==='1')p.set('exclude_vertical','1');
  p.set('limit',appSettings.batchSize); p.set('offset',offset);
  if(!reset)p.set('count','0');
  const d=await api('/api/items?'+p);cache(d.items);
  if(requestSeq!==loadRequestSeq)return;
  if(reset)total=d.total;
  buildManageBar();
  const html=batchWithMix(d.items,location.pathname==='/'&&state.state!=='trash');
  if(reset)releaseHoverPreviews($('#grid'));
  if(reset)$('#grid').innerHTML=html; else $('#grid').insertAdjacentHTML('beforeend',html);
  renderCount();
  $('#loadSentinel').hidden=$('#grid').querySelectorAll('[data-id]').length>=total;
  wireCards($('#grid'));
  wireMixCards($('#grid'));
  paintSelection();
  if(reset)loadShorts(requestSeq);
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
const rememberSearch=async query=>{if(!query)return;await api('/api/search-history',{method:'POST',body:JSON.stringify({query})});writeSearchHistory([query,...readSearchHistory().filter(x=>foldName(x)!==foldName(query))])};
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
      await api('/api/search-history',{method:'POST',body:JSON.stringify({operation:'remove',query:value})});
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
async function loadShorts(requestSeq=loadRequestSeq){
  // JAV 模式不插竖屏条：番号发行物本身是横版，竖屏是另一类内容。
  // 主列表的 exclude_vertical 管不到这条——它是独立请求、独立插入的。
  if(location.pathname!=='/'||javActive()||state.orient==='竖屏'
     ||state.state==='ads'||state.state==='trash'){
    $('#shortsSec').hidden=true;$('#grid').querySelector('#shortsInline')?.remove();return}
  const p=new URLSearchParams(Object.entries(state).filter(([,v])=>v));
  /* 排序跟着主列表走，不再写死 sort=new。写死等价于 `id DESC`：换一批换掉了整页网格，
     竖屏条却永远是同样那 18 条最新的，连每日轮换都不生效。 */
  p.set('orient','竖屏');p.set('limit',18);p.set('offset',0);
  const d=await api('/api/items?'+p);
  if(requestSeq!==loadRequestSeq)return;
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
    : `<button data-edit-playlist title="编辑播放列表" aria-label="编辑播放列表">${icon('list-filter')}</button>`;
  return `<aside class="mixqueue"><div class="mixqueuehead"><div><h2>${esc(queue.title)}</h2><span>${queue.items.length} 个视频</span></div><div class="mixqueueactions">${action}
    <button data-queue-close title="关闭" aria-label="关闭">${icon('x')}</button></div></div><div class="mixlist">${queue.items.map((x,index)=>{
      const thumb=x.has_thumb?`<img src="/poster?id=${x.id}&c=4" alt="" loading="lazy">`:'';
      const edit=queue.kind==='playlist'?`<span class="queueedit"><button data-queue-up="${index}" aria-label="上移" ${index===0?'disabled':''}>↑</button><button data-queue-down="${index}" aria-label="下移" ${index===queue.items.length-1?'disabled':''}>↓</button><button data-queue-remove="${x.id}" aria-label="移出播放列表">${icon('x')}</button></span>`:'';
      return `<div class="mixrow"><button class="mixitem ${x.id===itemId?'current':''}" data-queue-item="${x.id}" aria-current="${x.id===itemId?'true':'false'}">
        <span class="mixitempic">${thumb}<i class="dur mono">${fmtDur(x.duration)}</i></span><span class="mixitemtext"><b>${esc(x.name)}</b><span>${esc(mixLabel(x))}</span></span></button>${edit}</div>`;
    }).join('')}</div></aside>`;
}
async function buildMix(seedId){
  const [seed,related]=await Promise.all([api('/api/item?id='+seedId),api('/api/related?id='+seedId+'&limit=28')]);
  const items=[seed,...(related.items||[]).filter(x=>x.id!==seed.id)];cache(items);
  return {kind:'mix',seedId,title:`Mix · ${mixLabel(seed)}`,items};
}
async function openMix(seedId,itemId=seedId,push=true){
  const previous=activeQueue?.kind==='mix'&&activeQueue.seedId===seedId?activeQueue:null;
  if(push&&!previous)detailReturnPath=location.pathname+location.search;
  const mix=previous||await buildMix(seedId);
  await openItem(itemId,false,mix);
  if(push)route(`/mix/${seedId}/${itemId}`);
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
async function openItem(id,push=true,queueContext=null){
  releaseHoverPreviews();
  const returnBars=barsContext.type==='item'?detailReturnBarsContext:cloneBarsContext(barsContext);
  if(push)detailReturnPath=location.pathname+location.search;
  disposeStage(false);
  detailReturnBarsContext=returnBars;
  activeQueue=queueContext;
  if(push&&!queueContext)route('/item/'+id);
  const it=await api('/api/item?id='+id); if(it.error)return;
  current=it; CACHE[it.id]=it;
  barsContext={type:'item',id:it.id,filters:returnBars?.type==='entity'
    ? {...returnBars.filters}:emptyEntityFilters()};
  const gated=it.cost==='metered';
  const offline=sourceOffline(it.location);
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
       :gated?`<div class="gate" id="gate">
          ${srcBadge(it.location,it.cost,'srcbig')}
          <span style="font-size:12px;color:var(--muted)">点此开始拉流 · ${fmtSize(it.size||0)}</span></div>
        <video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="none" hidden></video>`
       :`<video id="vid" class="video-js vjs-big-play-centered" controls playsinline preload="metadata"></video>`}
    </div>${queueContext?queueHtml(queueContext,it.id):''}
    <div class="side">
      <div class="stitle">${esc(it.name)}</div>
      ${it.location==='online'?'':sourceTools(it.id)}
      <div class="smeta mono">${srcBadge(it.location,it.cost,'srcbig')}
        <span style="align-self:center">${it.width||'?'}×${it.height||'?'}</span>
        <span style="align-self:center">${fmtSize(it.size||0)}</span>
        ${it.release_date?`<span style="align-self:center">发行 ${esc(it.release_date)}</span>`:''}</div>
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
          <button class="savepreference" id="savePreference" title="保存喜爱理由" aria-label="保存喜爱理由">${icon('check')}</button></div>
      </div>
      <button class="obtn" data-kind="o">${icon('sperm')}<span>记一次高潮</span><b class="mono" id="oCount">${it.o_count||0}</b></button>
    </div></div>
    ${queueContext?'':`<div class="next"><h3>接着看</h3><div class="nrow" id="nrow">载入中…</div></div>`}`;

  const closeDetail=()=>{const restore=cloneBarsContext(detailReturnBarsContext);
    disposeStage(true);detailReturnBarsContext=null;
    barsContext=restore||{type:'home',filters:state};buildBars();
    if(location.pathname==='/playlists')openPlaylists(false)};
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
    :openPlaylist(queueContext.playlistId,+b.dataset.queueItem,true));
  $('#stage').querySelectorAll('[data-save-mix]').forEach(b=>b.onclick=()=>saveMixAsPlaylist(queueContext));
  $('#stage').querySelectorAll('[data-edit-playlist]').forEach(b=>b.onclick=()=>openPlaylists(true));
  $('#stage').querySelectorAll('[data-queue-up],[data-queue-down]').forEach(b=>b.onclick=()=>movePlaylistItem(queueContext,+b.dataset[b.hasAttribute('data-queue-up')?'queueUp':'queueDown'],b.hasAttribute('data-queue-up')?-1:1,it.id));
  $('#stage').querySelectorAll('[data-queue-remove]').forEach(b=>b.onclick=()=>removePlaylistItem(queueContext,+b.dataset.queueRemove,it.id));
  const g=$('#gate');
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
    wrap.innerHTML=visible.map(t=>`<span class="detailtag"><button class="tagfilter" data-tag="${esc(t.k)}">${esc(t.k)}</button><button class="tagremove" data-remove-tag="${esc(t.k)}" title="从此视频隐藏该标签" aria-label="删除标签 ${esc(t.k)}">${icon('x')}</button></span>`).join('')+
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
        ${selected?icon('check'):icon('tags')}<span class="pickname">${esc(x.k)}</span><span class="pickcount">${(x.n||0).toLocaleString()}</span></button>`};
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
    btn.disabled=true;stateText.textContent='保存中…';
    const reason=$('#likeReason').value;
    const liked=like.getAttribute('aria-pressed')==='true'||reason.trim().length>0;
    try{const r=await api('/api/preference',{method:'POST',body:JSON.stringify({id:it.id,liked,reason})});
      it.liked=r.liked;it.like_reason=r.like_reason;
      like.setAttribute('aria-pressed',r.liked);like.setAttribute('aria-label',r.liked?'取消喜欢':'喜欢');
      preferenceToggle.dataset.hasReason=String(!!r.like_reason);
      stateText.textContent='已保存';setTimeout(()=>{if(stateText.textContent==='已保存')stateText.textContent=''},1400);
    }catch(e){stateText.textContent='保存失败 · 请重试'}finally{btn.disabled=false}
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
  const startAmbient=()=>{const canvas=$('#ambientCanvas');if(!canvas)return()=>{};
    const ctx=canvas.getContext('2d',{alpha:false});let stopped=false,last=0;
    const paint=now=>{if(stopped)return;if(!document.hidden&&!vv.paused&&now-last>480){last=now;
      try{ctx.drawImage(vv,0,0,canvas.width,canvas.height);
        const px=ctx.getImageData(0,0,canvas.width,canvas.height).data;let r=0,g=0,b=0,n=0;
        for(let i=0;i<px.length;i+=16){r+=px[i];g+=px[i+1];b+=px[i+2];n++}
        if(n)$('#stage').style.setProperty('--video-glow',`rgb(${Math.round(r/n)} ${Math.round(g/n)} ${Math.round(b/n)})`)
      }catch(_e){}}
      if(vv.requestVideoFrameCallback)vv.requestVideoFrameCallback((t)=>paint(t));else requestAnimationFrame(paint)};
    vv.addEventListener('play',()=>paint(performance.now()),{once:true});return()=>{stopped=true}};
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
  else if(g)g.onclick=()=>{vv.hidden=false;g.remove();mountDetailPlayer(it,vv,true);stopAmbient=startAmbient()};
  else{mountDetailPlayer(it,vv,true);stopAmbient=startAmbient()}
  vv.addEventListener('emptied',()=>stopAmbient(),{once:true});
  $('#stage').scrollIntoView({behavior:'auto',block:'start'});
  buildBars();

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

/* ── 短片全屏 ── */
let tokList=[],tokIdx=0,tokSwitching=false,tokNetTimer=null,tokLoadHideTimer=null,tokLoadingLabel='加载中…';
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
      v.src='/stream?id='+it.id;applyTokFit(v);v.style.transform=`translate(-50%,${dir>0?100:-100}%)`;track.appendChild(v);
      await waitTokReady(v);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        old.style.transform=`translate(-50%,${dir>0?-100:100}%)`;v.style.transform='translate(-50%,0)'}));
      await new Promise(resolve=>setTimeout(resolve,210));
      old.pause();old.remove();v.id='tokVid';v.style.transform='translateX(-50%)';
    }else{
      v.preload='auto';v.src='/stream?id='+it.id;applyTokFit(v);await waitTokReady(v);
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
    // 共演作品在沉浸模式也要念全出镜者；点击仍进第一位的资料页。
    const cast=full.performers||[];
    const who=cast.length
      ? cast.slice(0,3).join('、')+(cast.length>3?` 等 ${cast.length} 人`:'')
      : (full.creator||it.code||'未归属');
    $('#tokWho').textContent=who;
    $('#tokWho').onclick=e=>{e.preventDefault();
      $('#tokClose').click();
      if(full.performers&&full.performers[0])openEntity('performer',full.performers[0]);
      else if(full.creator)openEntity('creator',full.creator);
      else if(it.code){state.q=it.code;buildEdge();buildBars();load(true)}};
    $('#tokMeta').textContent=`· ${fmtDur(it.duration)} · ${it.ctx_orient||''} · ${tokIdx+1}/${tokList.length}`;
    // 进度条
    const bar=$('#tokBar'), prog=$('#tokProg');
    v.ontimeupdate=null;
    const upd=()=>{const d=v.duration||it.duration||0;
      if(d)prog.style.width=(v.currentTime/d*100).toFixed(2)+'%'};
    v.addEventListener('timeupdate',upd);
    bar.onclick=e=>{const r=bar.getBoundingClientRect();
      const d=v.duration||0; if(d)v.currentTime=d*((e.clientX-r.left)/r.width)};
    $('#tokDislike').setAttribute('aria-pressed',full.feedback==='dislike');
    $('#tokSeen').setAttribute('aria-pressed',full.feedback==='seen');
    $('#tokSeen .toklabel').textContent=full.feedback==='seen'?'已看':'看过';
    $('#tokOn').textContent=full.o_count||0;
    api('/api/play',{method:'POST',body:JSON.stringify({id:it.id})});
    wireTelemetry(it,v,{});
    setTokLoading(false);
  }catch(_e){setTokLoading(false)}finally{tokSwitching=false}
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
$('#brandHome').onclick=e=>{e.preventDefault();
  state={loc:state.loc,creator:'',studio:'',tag:'',len:'',dur_min:'',dur_max:'',orient:'',state:'',sort:appSettings.defaultSort,seed:persistedSeed(),q:'',thumb:'1'};
  route('/');$('#q').value='';disposeStage(false);buildBars();load(true);window.scrollTo({top:0,behavior:'smooth'})};
$('#tokClose').onclick=()=>{setTokLoading(false);route('/');$('#tok').hidden=true;$('#tokTrack').querySelectorAll('video').forEach(v=>{
  v.pause();v.removeAttribute('src');v.load();if(v.id!=='tokVid')v.remove()});
  const v=$('#tokVid');if(v){v.style.transform='translateX(-50%)'}tokSwitching=false;document.body.style.overflow='';showHomeSurfaces();load(true)};
let wl=0;
$('#tok').addEventListener('wheel',e=>{const n=Date.now();if(n-wl<260)return;wl=n;tokNext(e.deltaY>0?1:-1)},{passive:true});
let ty=0;
$('#tok').addEventListener('touchstart',e=>ty=e.touches[0].clientY,{passive:true});
$('#tok').addEventListener('touchend',e=>{const dy=ty-e.changedTouches[0].clientY;
  if(Math.abs(dy)>60)tokNext(dy>0?1:-1)},{passive:true});
[['#tokDislike','dislike'],['#tokSeen','seen'],['#tokO','o']].forEach(([s,kind])=>{
  $(s).onclick=async()=>{const it=tokList[tokIdx];
    const r=await api('/api/feedback',{method:'POST',body:JSON.stringify({id:it.id,kind})});
    $('#tokDislike').setAttribute('aria-pressed',r.feedback==='dislike');
    $('#tokSeen').setAttribute('aria-pressed',r.feedback==='seen');
    $('#tokSeen .toklabel').textContent=r.feedback==='seen'?'已看':'看过';
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
    if(selectMode||selected.size){setSelectMode(false,true);return}
    const st=$('#stage');if(st&&!st.hidden){const c=$('#closeStage');if(c)c.click()}
    return;
  }
  // 输入态不抢键：搜索框、标签弹窗和任何可编辑区域里的按键归它们自己处理。
  if(isTypingTarget(e.target)||e.ctrlKey||e.metaKey||e.altKey)return;
  const video=activeVideo();
  if(video){
    if(e.key==='ArrowLeft'||e.key==='ArrowRight'){
      e.preventDefault();
      seekVideoBy(video,appSettings.seekSeconds*(e.key==='ArrowRight'?1:-1));
      return;
    }
    if(e.key===' '){
      e.preventDefault();          // 不加这句空格会把页面滚下去
      if(video.paused)video.play().catch(()=>{});else video.pause();
      return;
    }
  }
  // 沉浸模式：纵向切片、横向快进退，和竖屏短视频的手势方向保持一致。
  if(!$('#tok').hidden){if(e.key==='ArrowDown')tokNext(1);if(e.key==='ArrowUp')tokNext(-1)}
});

/* ── ⟳ = 换一批推荐（不是重载页面）──
   每次点用一个新种子重排，所以「这一批」内部翻页稳定，批与批之间不同。
   不用 RANDOM()：那样翻页会重复和漏掉条目。
   自动刷新只在首页空闲态执行，不打断播放、搜索、选择或其他页面。 */
async function refreshAll(automatic=false){
  if(automatic&&(document.hidden||location.pathname!=='/'||
      !$('#stage').hidden||!$('#tok').hidden||selectMode||selected.size||document.activeElement===$('#q')))return false;
  if(!$('#stats').hidden){
    if(location.pathname==='/review'){await openReview(false);return}
    if(location.pathname==='/duplicates'){await openDuplicates(false);return}
    if(location.pathname==='/quality-goals'){await openQualityGoals(false);return}
    if(location.pathname==='/playlists'){await openPlaylists(false);return}
    /* 两个追更页都刻意不参与「换一批」自动刷新：重画要重新取数，而管理页上紧接着的
       动作是联网检查，自动触发等于替用户决定什么时候去打站点。 */
    if(location.pathname==='/follow'||location.pathname==='/follow-manage')return;
    await openStats(false);return
  }      // 统计/复核页只刷新当前表面
  if(!$('#index').hidden){return}
  state.sort='seed'; state.seed=rollSeed();
  // 顶部三层（女优头像、厂牌、标签）此前从不跟着换：它们有 30 秒会话缓存，
  // 而 refreshAll 只重载网格，于是「换一批」之后上面还是原来那批人。
  barsDataCache=null;barsDataPromise=null;
  await Promise.all([load(true),buildBars()]);
  if(!automatic)window.scrollTo({top:0,behavior:'smooth'});
  return true;
}
/* 没有前台定时器：页面不会在你看着的时候自己重排。换排序是加载时结算的，
   「后台每 N 分钟换一次」的效果由种子的时间窗实现（见 persistedSeed）。 */
$('#refresh').onclick=()=>{const b=$('#refresh');
  b.style.transition='transform .55s cubic-bezier(.3,.9,.3,1)';b.style.transform='rotate(360deg)';
  setTimeout(()=>{b.style.transition='';b.style.transform=''},580);
  refreshAll()};

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
  const path=decodeURIComponent(location.pathname),parts=path.split('/').filter(Boolean);
  if(path==='/trash'){
    state={...state,creator:'',studio:'',tag:'',orient:'',state:'trash',q:''};$('#q').value='';
    buildEdge();buildBars();load(true);return;
  }
  if(path==='/playlists'){await openPlaylists(false);return}
  if(parts[0]==='playlists'&&/^\d+$/.test(parts[1]||'')&&/^\d+$/.test(parts[2]||'')){await openPlaylist(+parts[1],+parts[2],false);return}
  if(parts[0]==='mix'&&/^\d+$/.test(parts[1]||'')&&/^\d+$/.test(parts[2]||'')){await openMix(+parts[1],+parts[2],false);return}
  if(parts[0]==='item'&&/^\d+$/.test(parts[1]||'')){await openItem(+parts[1],false);return}
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
  if(path==='/review'){await openReview(false);return}
  if(path==='/duplicates'){await openDuplicates(false);return}
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
  .then(async()=>{buildEdge();wireAllDrag();await load(true);await restoreRoute();scheduleStickySurfaces()});
