/* 前端最底层：DOM 取元素、请求、转义、格式化、路由常量。

   没有构建步骤——浏览器原生 ES module，只是文件多了几个。这一层不许 import 任何
   别的前端模块：它被所有域引用，一旦反向依赖就会绕成环。

   `route()` 没有放进来：它要调 syncHeaderActions/paintListTitle，那是 UI 层的事。 */
const $=s=>document.querySelector(s);
/* 方形槽位里塞不进 1.4:1 的字形：按宽度对齐它就矮一截，挨着满格的 Lucide
   图标看就是小一号。这几枚外层 viewBox 跟着 symbol 的比例走，槽位由 CSS 按高定宽。 */
const WIDE_ICONS={'text-aa':1.435};
const icon=(name,cls='')=>{
  const ratio=WIDE_ICONS[name],classes=[ratio?'iconwide':'',cls].filter(Boolean).join(' ');
  const box=ratio?`0 0 ${(24*ratio).toFixed(2)} 24`:'0 0 24 24';
  return `<svg${classes?` class="${classes}"`:''} viewBox="${box}" aria-hidden="true"><use href="#i-${name}"/></svg>`};
/* `signal` 写成显式的一项，不靠 Object.assign 顺带透传：表面切换要能作废上一屏
   还没读完的请求，「这个请求可被取消」得在签名上看得见。 */
const api=async(p,o)=>{
  const {signal=null,...rest}=o||{};
  const init={headers:{'Content-Type':'application/json'},...rest};
  if(signal)init.signal=signal;
  const response=await fetch(p,init);
  let payload=null;
  try{payload=await response.json()}catch(_e){}
  if(!response.ok){
    const detail=payload&&(payload.message||payload.detail||payload.error);
    throw new Error(detail||`请求失败（${response.status}）`);
  }
  return payload;
};
/* 取消不是失败。abort 只可能来自表面切换，调用点本来就有一条「已过期」分支要走，
   不该顺手弹一个「请求失败」的错误提示。 */
const isAbort=error=>error?.name==='AbortError';
/* 有界并发的批量请求。串行发一千次 POST 是实测的卡点（批量标记「已看」要几分钟，
   界面全程按住），而一次全发出去等于自己挤自己：浏览器对同一 host 只有 6 条
   HTTP/1.1 连接，多出来的排在队里，连同一时间的正常浏览请求一起等。所以固定几个
   工人按序取任务。返回值顺序与输入一致；某一项失败只记下原因，不中断整批——
   批量操作里一条失败不该把其余几百条一起放弃。 */
const mapLimit=async(items,limit,run)=>{
  const list=[...items],results=new Array(list.length);
  let next=0;
  const worker=async()=>{
    while(next<list.length){
      const index=next++;
      try{results[index]={ok:true,value:await run(list[index],index)}}
      catch(error){results[index]={ok:false,error}}
    }
  };
  const workers=Math.min(Math.max(1,limit),list.length);
  await Promise.all(Array.from({length:workers},worker));
  return results;
};
const STATE_ROUTES={fresh:'/unseen',later:'/watch-later',flagged:'/flagged',ads:'/junk-files'};
const ROUTE_STATES=Object.fromEntries(Object.entries(STATE_ROUTES).map(([state,path])=>[path,state]));
const STATE_LABELS={fresh:'没看过',later:'稍后看',flagged:'已标记',ads:'垃圾文件'};
const isCatalogPath=path=>path==='/'||Object.prototype.hasOwnProperty.call(ROUTE_STATES,path);
const ENTITY_ROUTES={performer:'performers',studio:'studios',creator:'creators',series:'series',agency:'agencies'};
const ROUTE_ENTITIES={performers:'performer',studios:'studio',creators:'creator',series:'series',agencies:'agency'};
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
/* 域名当名字：厂牌页的官网链接直接显示它，比一枚小图标说得清楚。大写跟着 beeg 的
   资料页写法，`www.` 去掉——它不携带信息，只占宽度。 */
const linkHost=url=>{try{return new URL(url).hostname.replace(/^www\./,'').toUpperCase()}catch{return ''}};
/* 服务端处理过的链接图标：单色字形的 favicon 会被做成「品牌色底 + 白色主体」，
   做不了就把原图按 32 px 转出来。放服务端有三个理由：它要读别人站点的图、要缓存，
   而且这样浏览器不再直接向对方站点发请求（也就不泄露正在看谁的资料页）。

   传的是链接 id 而不是地址。跟 `/follow-stream` 同一条规矩：服务端只取账本里已有的
   地址，绝不去取前端递过来的任意 URL——那等于开一个任意地址抓取的口子。 */
const linkMarkUrl=link=>`/link-mark?id=${encodeURIComponent(link.link_id ?? '')}`;
/* 有品牌标记的主机连 favicon 都不取。

   favicon 是别人服务器上的一张小位图：X 直接挡掉爬取（资料页那个空白白圆就是它），
   取到的也多是 16×16，放进 32 px 的圆里必然糊。内联 SVG 没有这两个问题，还省一次
   跨站请求。只覆盖真正占量的主机——416 条社媒链接里 372 条是 x.com／twitter.com；
   其余继续走 favicon，不为个位数的链接各配一个图标。 */
const BRAND_ICONS=[[['x.com','twitter.com'],'brand-x']];
const brandIcon=url=>{try{
  const host=new URL(url).hostname.replace(/^www\./,'').toLowerCase();
  return BRAND_ICONS.find(([hosts])=>hosts.some(d=>host===d||host.endsWith('.'+d)))?.[1]||'';
}catch{return ''}};
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
  isAbort,
  mapLimit,
  STATE_ROUTES,
  ROUTE_STATES,
  STATE_LABELS,
  isCatalogPath,
  ENTITY_ROUTES,
  ROUTE_ENTITIES,
  entityPath,
  esc,
  SITE_FAVICONS,
  brandIcon,
  faviconUrl,
  linkHost,
  linkMarkUrl,
  faviconFallbackUrl,
  foldName,
  fmtDur,
  fmtClock,
  fmtSize,
  LOC,
};
