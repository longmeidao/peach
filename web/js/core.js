/* 前端最底层：DOM 取元素、请求、转义、格式化、路由常量。

   没有构建步骤——浏览器原生 ES module，只是文件多了几个。这一层不许 import 任何
   别的前端模块：它被所有域引用，一旦反向依赖就会绕成环。

   `route()` 没有放进来：它要调 syncHeaderActions/paintListTitle，那是 UI 层的事。 */
const $=s=>document.querySelector(s);
/* 方形槽位里塞不进 1.4:1 的字形：按宽度对齐它就矮一截，挨着满格的 Lucide
   图标看就是小一号。这几枚外层 viewBox 跟着 symbol 的比例走，槽位由 CSS 按高定宽。 */
const WIDE_ICONS={'text-aa':1.435,'mark-javdb':326/111};
const icon=(name,cls='')=>{
  const ratio=WIDE_ICONS[name],classes=[ratio?'iconwide':'',cls].filter(Boolean).join(' ');
  const box=ratio?`0 0 ${(24*ratio).toFixed(2)} 24`:'0 0 24 24';
  return `<svg${classes?` class="${classes}"`:''} viewBox="${box}" aria-hidden="true"><use href="#i-${name}"/></svg>`};
/* `signal` 写成显式的一项，不靠 Object.assign 顺带透传：表面切换要能作废上一屏
   还没读完的请求，「这个请求可被取消」得在签名上看得见。 */
export function requestErrorMessage(cause,status=0){
  const text=String(cause?.message??cause??'');
  const code=Number(status||cause?.status||text.match(/\b(400|401|403|404|408|409|413|429|500|502|503|504)\b/)?.[1]);
  const messages={400:'提交内容有误，请检查输入后重试。',401:'登录已失效，请刷新页面重新登录。',403:'当前设备没有执行此操作的权限，请在运行 Peach 的电脑上操作。',404:'请求的内容已不存在，请刷新列表。',408:'请求超时，请稍后重试。',409:'当前状态不允许此操作，请刷新后重试。',413:'提交内容过大，请减少数量后重试。',429:'请求过于频繁，请稍后重试。',500:'Peach 服务处理失败，请重试；持续失败时查看托盘日志。',502:'连接上游服务失败，请检查代理或来源服务。',503:'Peach 服务暂时不可用，请稍后重试。',504:'等待服务响应超时，请稍后重试。'};
  if(/Failed to fetch|fetch failed|NetworkError|Load failed|network request failed|ERR_CONNECTION/i.test(text))return '无法连接到 Peach 服务，请确认网络连接和托盘服务已启动。';
  if(cause?.name==='TimeoutError'||/timed? ?out|timeout/i.test(text))return '等待服务响应超时，请检查连接后重试。';
  if(/[\u3400-\u9fff]/.test(text)&&!/^请求失败[（(]/.test(text))return text;
  if(messages[code])return messages[code];
  return '操作未完成，请重试；持续失败时查看托盘日志。';
}
const api=async(p,o)=>{
  if(!o?.method||o.method==='GET'){
    const library=sessionStorage.getItem('peach.library');
    if(library&&/^\/api\/(items|facets)(\?|$)/.test(p))p+=(p.includes('?')?'&':'?')+'library='+encodeURIComponent(library);
  }
  const {signal=null,...rest}=o||{};
  const init={headers:{'Content-Type':'application/json'},...rest};
  if(signal)init.signal=signal;
  let response;
  try{response=await fetch(p,init)}catch(error){if(error?.name==='AbortError')throw error;throw new Error(requestErrorMessage(error),{cause:error})}
  let payload=null;
  try{payload=await response.json()}catch(_e){}
  if(!response.ok){
    const detail=payload&&(payload.message||payload.detail||payload.error);
    throw new Error(requestErrorMessage(detail,response.status));
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
/* 外链上写的是站点的短名：事务所和片商平时就被叫作 NAX、T-POWERS、DMM，而账本里的
   label 是采集时抄下来的全称（`New Actor eXperience`、`DMM 检索`），域名又要人先在
   `OFFICIAL.NAX-PRO.COM` 里认出哪一段是名字。两样都比短名难读，一排链接里尤其。

   按主机名查表，末尾后缀也算（`official.nax-pro.com` 命中 `nax-pro.com`）。表里没有的
   退回账本 label：这张表覆盖常来常往的那些站，剩下的长尾不值得逐条登记，而 label 至少
   是人写过的。账本里的 label 不动——它是采集证据，显示是另一件事。 */
const SITE_NAMES=[['nax-pro.com','NAX'],['t-powers.co.jp','T-POWERS'],['dmm.co.jp','DMM'],
  ['mgstage.com','MGStage'],['av-event.jp','AV-EVENT'],['k-mib.com','K-MIB'],
  ['minnano-av.com','みんなのAV'],
  ['km-produce.com','KMP'],['mousouzoku-av.com','妄想族'],['mines-pro.jp','マインズ'],
  ['lightpro.jp','LIGHT'],['eltra.jp','ELTRA'],['linx.live','LINX'],['bambi.ne.jp','Bambi'],
  ['prestige-av.com','Prestige'],['cmore.jp','C-more'],['so-agent.jp','SO MODEL'],
  ['attractive-llc.net','Attractive'],['krone-web.jp','KRONE'],['actentertainment.jp','ACT'],
  ['crusegroup.net','Cruse'],['prime-recruit.com','Prime'],['life-promotion.com','Life'],
  ['8man.jp','Eightman'],['senzai.tv','Five'],['maxing.jp','MAXING'],['s1s1s1.com','S1'],
  ['ideapocket.com','Idea Pocket'],['faleno.jp','FALENO'],['capsule.bz','Capsule'],
  ['sod.co.jp','SOD'],['tokyo-hot.com','Tokyo-Hot'],['heyzo.com','HEYZO'],
  ['dogma.co.jp','DOGMA'],['naturalhigh.co.jp','Natural High'],['bangbros.com','BangBros'],
  ['dorcelclub.com','Dorcel']];
const bareHost=host=>String(host).replace(/^www\./,'').toLowerCase();
const linkHost=url=>{try{return bareHost(new URL(url).hostname)}catch{return ''}};
const siteName=url=>{
  const host=linkHost(url);
  return host&&SITE_NAMES.find(([domain])=>host===domain||host.endsWith('.'+domain))?.[1]||'';
};
/* 服务端处理过的链接图标：单色字形的 favicon 会被做成「品牌色底 + 白色主体」，
   做不了就把原图按 32 px 转出来。放服务端有三个理由：它要读别人站点的图、要缓存，
   而且这样浏览器不再直接向对方站点发请求（也就不泄露正在看谁的资料页）。

   传的是链接 id 而不是地址。跟 `/follow-stream` 同一条规矩：服务端只取账本里已有的
   地址，绝不去取前端递过来的任意 URL——那等于开一个任意地址抓取的口子。 */
const linkMarkUrl=link=>`/link-mark?id=${encodeURIComponent(link.link_id ?? '')}`;
/* 采集来源和口味排行里那些站点的圆标，同一条规矩的另一个入口：递的是服务端已经
   知道的键——采集来源键，或口味域名白名单里的那条后缀——不是地址。 */
const siteMarkUrl=params=>`/site-mark?${new URLSearchParams(params)}`;
/* 图标库里有的常见社媒走内联品牌标记，连 favicon 都不取。

   favicon 是别人服务器上的一张小位图：X 和 Instagram 直接挡掉爬取，资料页上只剩一只
   地球；取得到的也多是 16×16，放进 32 px 的圆里必然糊。站点自己给的大图又是另一种坏
   法——Threads、TikTok 给的是 iOS 应用图标那种圆角方图，四边一圈高光照着方角画，裁成圆
   之后沿圆周露出一道白，而那圈高光是人家设计的一部分，`/link-mark` 抠不掉。内联 SVG
   两样都没有，还省一次跨站请求，场色是品牌自己的那块、不跟着主题走。
   名单按图标库的覆盖面定，不按链接条数：Phosphor 有这七家的字形，一家一枚配齐；库里
   没有的（livedoor、ameblo、lit.link、pub.linx.live 这类）继续走 `/link-mark`，那边按
   站点自己的图标合成品牌色圆底。 */
const BRAND_ICONS=[[['x.com','twitter.com'],'brand-x'],[['instagram.com'],'brand-instagram'],
  [['threads.com','threads.net'],'brand-threads'],[['tiktok.com'],'brand-tiktok'],
  [['youtube.com','youtu.be'],'brand-youtube'],[['facebook.com','fb.com'],'brand-facebook'],
  [['linktr.ee','linktree.com'],'brand-linktree']];
const brandIcon=url=>{
  const host=linkHost(url);
  return host&&BRAND_ICONS.find(([hosts])=>hosts.some(d=>host===d||host.endsWith('.'+d)))?.[1]||'';
};
const foldName=s=>String(s??'').normalize('NFKC').trim().toLocaleLowerCase();
/* 官网链接上那行字。写站点短名（`siteName`），表里没有就用账本 label。

   只有厂牌页上指回自家站的写「官方网站」：页头已经是厂牌名，链接再写一遍 S1、
   KMP 只是重复。事务所页和人物页照旧写名字，那里的名字就是要看的信息。名字是
   别家的（Jackson 页上链到 Prestige 的名录页）也保留，那说的是另一家。自家的判据是
   短名或 label 与规范名、别名互相包含：`C-more` 之于 `C-more Entertainment`，短名是缩写
   时看 label（`NAX` 那条的 label 是 `New Actor eXperience`）。label 只是这条链接自己的
   主机名（`www.ran-maru.com`）等于没起名，也算自家。

   存档快照（`web.archive.org`）一律照写 label：公司关门后官网只剩这一份，label 里写着
   它是哪一年的存档，改写成「官方网站」就读不出点过去看到的是旧页面。 */
const ARCHIVE_HOSTS=['web.archive.org'];
const isArchiveLink=url=>ARCHIVE_HOSTS.includes(linkHost(url));
const officialLinkText=(link,kind,names=[])=>{
  const text=siteName(link.url)||link.label||'';
  if(kind!=='studio'||isArchiveLink(link.url))return text;
  const said=[text,link.label].map(foldName).filter(Boolean);
  const own=!said.length||said.includes('官方网站')||said.some(shown=>
    bareHost(shown)===linkHost(link.url)||names.some(name=>{
      const folded=foldName(name);
      return Boolean(folded)&&(folded.includes(shown)||shown.includes(folded));
    }));
  return own?'官方网站':text;
};
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
  brandIcon,
  siteName,
  linkMarkUrl,
  siteMarkUrl,
  foldName,
  officialLinkText,
  fmtDur,
  fmtClock,
  fmtSize,
  LOC,
};
