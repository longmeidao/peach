/* 前端最底层：DOM 取元素、请求、转义、格式化、路由常量。

   没有构建步骤——浏览器原生 ES module，只是文件多了几个。这一层不许 import 任何
   别的前端模块：它被所有域引用，一旦反向依赖就会绕成环。

   `route()` 没有放进来：它要调 syncHeaderActions/paintListTitle，那是 UI 层的事。 */
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
const pageTitle=path=>{
  const url=new URL(path,location.origin),parts=decodeURIComponent(url.pathname).split('/').filter(Boolean);
  const fixed={stats:'统计',taste:'口味',review:'人工复核',duplicates:'重复文件','quality-goals':'高清版',
    follow:'关注','follow-manage':'关注管理',playlists:'播放列表',performers:'女优',studios:'厂牌',
    creators:'创作者',series:'系列',tags:'标签',unseen:'没看过','watch-later':'稍后看',flagged:'已标记',
    immerse:'沉浸模式',mix:'Mix',item:'作品','resource-sync':'统计','junk-files':'垃圾文件'};
  const label=parts.length>1&&['performers','studios','creators','series'].includes(parts[0])
    ? parts.slice(1).join('/') : fixed[parts[0]];
  return label?`${label} · Peach`:'Peach · 蜜桃';
};
const STATE_ROUTES={fresh:'/unseen',later:'/watch-later',flagged:'/flagged',ads:'/junk-files'};
const ROUTE_STATES=Object.fromEntries(Object.entries(STATE_ROUTES).map(([state,path])=>[path,state]));
const STATE_LABELS={fresh:'没看过',later:'稍后看',flagged:'已标记',ads:'垃圾文件'};
const isCatalogPath=path=>path==='/'||Object.prototype.hasOwnProperty.call(ROUTE_STATES,path);
const ENTITY_ROUTES={performer:'performers',studio:'studios',creator:'creators',series:'series'};
const ROUTE_ENTITIES={performers:'performer',studios:'studio',creators:'creator',series:'series'};
const entityPath=(kind,name)=>`/${ENTITY_ROUTES[kind]||kind}/${encodeURIComponent(name)}`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const SITE_FAVICONS={
  'kemono.cr':'https://kemono.cr/assets/favicon-CPB6l7kH.ico',
  'simpcity.cr':'https://simpcity.cr/data/assets/logo/favicon.png',
  'hanime1.me':'https://vdownload.hembed.com/image/icon/tab_logo.png?secure=EJYLwnrDlidVi_wFp3DaGw==,4867726124',
};
const faviconUrl=url=>{try{const parsed=new URL(url),host=parsed.hostname.replace(/^www\./,'');
  return SITE_FAVICONS[host]||new URL('/favicon.ico',parsed).href}catch{return ''}};
const faviconFallbackUrl=domain=>`https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;
const foldName=s=>String(s??'').normalize('NFKC').trim().toLocaleLowerCase();
/* 什么才算一个真时长——只有这一处说了算。

   账本里 `-1` 是 probe 的「硬失败」哨兵（见 scripts/probe.py：抽帧的 duration>2 门槛
   会让失败条目永远卡住，所以硬失败写成 -1），它不是时长。而 `!s` 这种真值判断挡不住
   负数：`fmtDur(-1)` 会算出 `0:-1`，喂进播放器更糟——Video.js 的 duration() setter 里写着
   `parseFloat(e)<0 ? Infinity : e`，随后 `=== Infinity` 就 `addClass("vjs-live")`，
   于是一部本地影片被标成「直播」，总时长显示 NaN。

   所以判据是「有限且大于零」，不是「非空」。 */
const realDuration=value=>{const n=Number(value);return Number.isFinite(n)&&n>0?n:0};
const fmtDur=s=>{s=realDuration(s);if(!s)return'—';s=Math.round(s);const h=s/3600|0,m=(s%3600)/60|0,x=s%60;
  return h?`${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`:`${m}:${String(x).padStart(2,'0')}`};
const fmtClock=s=>{s=Math.max(0,Math.floor(Number(s)||0));const h=s/3600|0,m=(s%3600)/60|0,x=s%60;
  return h?`${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`:`${m}:${String(x).padStart(2,'0')}`};
const fmtSize=b=>b>=1099511627776?(b/1099511627776).toFixed(2)+' TB':b>=1073741824?(b/1073741824).toFixed(1)+' GB':(b/1048576|0)+' MB';
const LOC={local:'本地','115':'115',pikpak:'PikPak',online:'在线'};

export {
  $,
  realDuration,
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
};
