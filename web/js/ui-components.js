import { esc, icon, requestErrorMessage } from './core.js';
import { playUiSound } from './ui-sounds.js';
export { MEDIA_SOURCE_ICONS } from './media-source-icons.js';

const NOTE_VARIANTS=new Set(['secondary','warning','error','success']);

/** 标签含义、计数口径和查询由页面提供。 */
export function filterChipHtml(label,{attr,value,selected=false,count,className='',countClass='n mono'}={}){
  /* 计数前不写空格。`.pill` 是 flex 容器，纯空白的文本节点不参与布局，写了也量不出
     一个像素——间隔归 `.pill .n` 的 margin，写在两处就是两份真相，而其中一份从来
     没生效过。 */
  return `<button type="button" class="pill${className?' '+esc(className):''}" ${attr}="${esc(value)}" aria-pressed="${selected}">${esc(label)}${count==null?'':`<span class="${esc(countClass)}" data-count-badge="${esc(value)}">${esc(count)}</span>`}</button>`;
}
/* `extra` 排在换一批与排序键之间。那个位置放的是版式、大小这类「这批东西怎么摆」的
   开关，以及跟换一批同类的动作键；排序键一律排在最末，挨着它说明的那批内容。 */
export function sortControlsHtml({items=[],renderItem=String,extra='',shuffleId='',shuffleClass='entitybatch'}={}){
  return `<span class="sorts"><button class="batchaction ${esc(shuffleClass)}"${shuffleId?` id="${esc(shuffleId)}"`:''} type="button" title="换一批" aria-label="换一批">${icon('shuffle')}</button>${extra}${items.map(renderItem).join('')}</span>`;
}
/* `filterRow` 只给等待态用：那时浮层还是一段字符串，`mountFilterFrame` 没得跑，
   槽位标记得跟着 HTML 一起生成，否则这一条会自己画成第二块浮层。 */
export function collectionHeaderHtml({readout='',controls='',before='',className='',loading=false,filterRow=''}={}){
  return `<div class="entitycollectionhead${className?' '+esc(className):''}"${filterRow?` data-filter-row="${esc(filterRow)}"`:''}>${before}<h3${loading?' class="skeleton"':''}>${readout}</h3>${controls}</div>`;
}

/* ── 原地换态的一组辅助 ──
   形状和 CSS 在 `web/css/25-motion.css`，那里也写着每一条的来源与取值。这一层只负责
   「什么时候换」：动画本身一律交给 CSS，JS 不读也不写具体的毫秒数。 */

/**
 * 两枚字形叠在一格里，换态只改容器上的 `data-icon-state`。
 *
 * 直接 `innerHTML=icon(...)` 的地方都可以换成它：重写 innerHTML 会把旧字形连同它正在
 * 走的动画一起丢掉，新字形也没有起点可走，读出来是一次硬切。
 */
export function iconSwapHtml(a,b,state='a',{className='',iconClass='',label=''}={}){
  return `<span class="iconswap${className?' '+esc(className):''}" data-icon-swap data-icon-state="${state==='b'?'b':'a'}"${
    label?` aria-label="${esc(label)}"`:''}><span data-icon="a">${icon(a,iconClass)}</span><span data-icon="b">${icon(b,iconClass)}</span></span>`;
}
/** 把 `iconSwapHtml` 画出来的那一枚切到 a 或 b；`root` 可以是它本身或它的祖先。 */
export function setIconSwap(root,state){
  const el=root&&(root.matches?.('[data-icon-swap]')?root:root.querySelector?.('[data-icon-swap]'));
  if(el)el.dataset.iconState=state==='b'||state===true?'b':'a';
  return el;
}

/**
 * 一行字换成另一行字：旧字往上糊掉，新字从下方回到原位。
 *
 * 值没变就什么也不做——同一次重绘里把同样的字再写一遍是常态，跟着抖一下会让页面看起来
 * 一直在变。首次写入（这一格还空着）也不放动画：那是内容第一次出现，归骨架那一段。
 */
export function swapText(el,text,{html=false}={}){
  if(!el)return;
  const next=String(text??''),write=()=>{if(html)el.innerHTML=next;else el.textContent=next};
  const previous=el.dataset.swapText;
  if(previous===next&&(el.textContent||'').length)return;
  el.dataset.swapText=next;
  el.classList.add('textswap');
  if(previous===undefined||previous===next){write();return}
  el.classList.remove('entering');
  el.classList.add('leaving');
  const enter=()=>{
    el.classList.remove('leaving');
    write();
    el.classList.add('entering');
    el.getBoundingClientRect();
    el.classList.remove('entering');
  };
  const done=event=>{if(event.target!==el)return;el.removeEventListener('transitionend',done);enter()};
  el.addEventListener('transitionend',done);
  /* 兜底：`--motion-swap` 归零或元素此刻不可见时 `transitionend` 不会来，
     不兜的话这一行就永远停在透明。 */
  setTimeout(()=>{if(el.classList.contains('leaving')){el.removeEventListener('transitionend',done);enter()}},400);
}

/**
 * 读数按位错峰长出来。把 `text` 拆成一个个字符，数字各占一档延迟，分隔符跟着前一档。
 *
 * 和 `swapText` 一样只在值真变时触发，首次写入不放动画。
 */
export function popCount(el,text){
  if(!el)return;
  const next=String(text??''),previous=el.dataset.popCount;
  if(previous===next&&el.firstElementChild)return;
  el.dataset.popCount=next;
  let at=-1;
  el.innerHTML=`<span class="digits">${[...next].map(ch=>{
    if(/\d/.test(ch))at+=1;
    return `<span style="--digit-at:${Math.max(at,0)}">${esc(ch)}</span>`;
  }).join('')}</span>`;
  /* 上一个值没登记过（这一格第一次出现）或压根没变，就只把字写上去。调用点整块重绘时
     把上一次的读数写回 `dataset.popCount` 再调，这一格才知道自己是换了值还是刚建出来。 */
  if(previous===undefined||previous===next)return;
  const group=el.firstElementChild;
  group.getBoundingClientRect();
  group.classList.add('popping');
}

/**
 * 占位换成真内容：旧的那一屏抬成盖在容器上的一层淡出，新内容同时从模糊里清晰起来。
 *
 * `write()` 负责把新内容写进 `container`。容器里没有骨架时直接写，不套这一层——
 * 翻页、筛选这类「内容换内容」不属于这条动效，套上去每换一次筛选整页都糊一下。
 */
export function revealSkeleton(container,write){
  if(!container)return;
  /* 还没到显示门槛就已经取完：直接落内容。隐藏中的占位从未被人看见，不该为了它再
     播一段「骨架退场」；这也让很快的本地请求完全没有骨架闪烁。 */
  if(container.querySelector('.skeleton-awaiting')){write();return}
  const hasSkeleton=container.querySelector('.skeleton,[data-skeleton],.skeletoncard,.countskeleton');
  if(!hasSkeleton||!container.firstChild){write();return}
  const fade=document.createElement('div');
  fade.className='skelfade';
  fade.setAttribute('aria-hidden','true');
  while(container.firstChild)fade.append(container.firstChild);
  write();
  container.classList.add('skelreveal');
  container.prepend(fade);
  container.getBoundingClientRect();
  container.classList.add('revealing');
  const drop=()=>{fade.remove();container.classList.remove('skelreveal','revealing')};
  const done=event=>{if(event.target!==fade)return;fade.removeEventListener('transitionend',done);drop()};
  fade.addEventListener('transitionend',done);
  setTimeout(()=>{if(fade.isConnected){fade.removeEventListener('transitionend',done);drop()}},1000);
}

/**
 * 清空输入框，框里那段字往上飘着糊掉。
 *
 * 输入框的 value 是一瞬间没的，动画只能挂在别处：这里照着它此刻的位置和字体摆一份同样
 * 的字，让那一份去飘，真正的输入框当场就空了，光标和输入法一刻也不等。`host` 缺省取
 * 输入框的父元素，它必须是定位祖先，否则这一层会飘到页面左上角去。
 */
export function dissolveValue(input,host=input&&input.parentElement,
  {text=input&&input.value,scrollLeft=input&&input.scrollLeft||0}={}){
  if(!input||!host)return ()=>{};
  host.querySelectorAll(':scope > .cleardissolve').forEach(node=>node.remove());
  input.classList.remove('dissolving');
  input.value='';
  if(!text||!input.isConnected)return ()=>{};
  const box=input.getBoundingClientRect(),frame=host.getBoundingClientRect();
  if(!box.width)return ()=>{};
  const ghost=document.createElement('span');
  ghost.className='cleardissolve';
  ghost.setAttribute('aria-hidden','true');
  const value=document.createElement('span');
  value.dataset.dissolveValue='';
  value.textContent=text;
  value.style.transform=`translateX(-${Math.max(0,scrollLeft)}px)`;
  ghost.append(value);
  const style=getComputedStyle(input);
  Object.assign(ghost.style,{left:`${box.left-frame.left-host.clientLeft}px`,
    top:`${box.top-frame.top-host.clientTop}px`,width:`${box.width}px`,height:`${box.height}px`,
    boxSizing:'border-box',padding:style.padding,font:style.font,lineHeight:style.lineHeight,
    letterSpacing:style.letterSpacing,textAlign:style.textAlign,direction:style.direction});
  input.classList.add('dissolving');
  host.append(ghost);
  let active=true,timer=null;
  const drop=()=>{
    if(!active)return;
    active=false;
    if(timer!==null)clearTimeout(timer);
    ghost.removeEventListener('animationend',drop);
    ghost.remove();
    if(!host.querySelector(':scope > .cleardissolve'))input.classList.remove('dissolving');
  };
  ghost.addEventListener('animationend',drop);
  /* 兜底：`--motion-reveal` 归零或这一刻元素不可见时 `animationend` 不会来，
     不兜的话这份复制品就永远盖在输入框上。 */
  timer=setTimeout(drop,1000);
  return drop;
}

/* 计数徽标上一次是多少。徽标所在的那一排每次筛选都整块重画，节点本身留不住上一个值，
   所以记在这里，键由调用方给的范围加徽标自己的键拼成。 */
const badgeCounts=new Map();
/**
 * 一排计数徽标里值真变了的那几枚弹一下，其余的不动。
 *
 * 首次见到某一枚不弹：那是它第一次出现在这个范围里，整排一起弹是一屏烟花，而它要说的
 * 是「这一枚刚变了」。`scope` 区分同一个键在不同排里的计数（顶部筛选条和抽屉各有一份）。
 */
export function popBadges(root,scope=''){
  if(!root)return;
  root.querySelectorAll('[data-count-badge]').forEach(el=>{
    const key=`${scope} ${el.dataset.countBadge}`,next=el.textContent||'';
    const previous=badgeCounts.get(key);
    badgeCounts.set(key,next);
    el.classList.add('countbadge');
    if(previous===undefined||previous===next)return;
    el.classList.add('popped');
    el.getBoundingClientRect();
    el.classList.remove('popped');
  });
}

/**
 * 一段标题从模糊里逐行揭示出来。
 *
 * 按行不按词：逐词要把整句拆成一串 `<span>`，复制出来的文字会跟着散架，而这几处标题
 * 正是最常被复制走的那几段字。走完把类名和行序一起摘掉，终点帧不留下 `filter`。
 */
export function revealTexts(root,selector='[data-reveal-line]'){
  if(!root)return;
  const lines=[...root.querySelectorAll(selector)];
  if(!lines.length)return;
  /* 起止两个状态都挂在行自己身上，不挂在外面那一层：这几处标题里有一对是 `<body>` 的
     直接子元素（页面标题和它的说明行），要共同的祖先就只剩 body 本身。 */
  lines.forEach((el,i)=>{el.classList.remove('revealing');el.classList.add('revealline');
    el.style.setProperty('--reveal-at',String(i))});
  lines[0].getBoundingClientRect();
  lines.forEach(el=>el.classList.add('revealing'));
  const drop=()=>lines.forEach(el=>{el.classList.remove('revealline','revealing');
    el.style.removeProperty('--reveal-at')});
  const last=lines[lines.length-1];
  const done=event=>{if(event.target!==last)return;last.removeEventListener('transitionend',done);drop()};
  last.addEventListener('transitionend',done);
  setTimeout(()=>{if(last.classList.contains('revealline')){last.removeEventListener('transitionend',done);drop()}},1200);
}

const horizontalControls=new Map();
let horizontalCleanup;
/* 两次滚轮事件隔多久算下一次手势。触控板的惯性尾巴一格一格地来，间隔在几十毫秒；
   人停下来再滚一次，中间隔的比这长得多。 */
const WHEEL_GESTURE_GAP=240;
/** 同一容器只绑定一次，滚到边缘后将下一次滚轮手势交还页面。 */
export function wireHorizontalScroller(el,{drag=false,fade=true}={}){
  if(!el)return;
  const existing=horizontalControls.get(el);
  if(existing){existing.options.drag ||= drag;existing.options.fade ||= fade;existing.update();return existing}
  const options={drag,fade},abort=new AbortController();
  let start=null,moved=0,heldUntil=0;
  const update=()=>{if(options.fade){el.dataset.overflowLeft=String(el.scrollLeft>1);el.dataset.overflowRight=String(el.scrollLeft+el.clientWidth<el.scrollWidth-1)}};
  const listen=(target,event,handler,extra={})=>target.addEventListener(event,handler,{...extra,signal:abort.signal});
  listen(el,'scroll',update,{passive:true});
  /* 滚轮按手势归属，一次手势只动一处。Chrome 把一串滚轮事件认作同一次手势，第一下
     没被拦下，后面那些就再也拦不住：页面滚着滚着让这一排经过指针底下，这时候再改
     `scrollLeft`，结果是一排和整页一起走。所以拦不住的那些原样留给页面。反过来，一次
     手势在这一排上开了头，滚到头时剩下那截（多半是惯性）也吃掉，不甩给页面——否则还没
     看清最后一张，整页已经往下走了。 */
  listen(el,'wheel',event=>{
    if(event.defaultPrevented||!event.cancelable||Math.abs(event.deltaY)<=Math.abs(event.deltaX)||el.scrollWidth<=el.clientWidth)return;
    const now=performance.now(),before=el.scrollLeft;el.scrollLeft+=event.deltaY;
    if(before===el.scrollLeft&&now>heldUntil)return;
    heldUntil=now+WHEEL_GESTURE_GAP;event.preventDefault();
  },{passive:false});
  listen(el,'mousedown',event=>{if(!options.drag||event.button!==0||el.scrollWidth-el.clientWidth<=1)return;event.stopPropagation();start={x:event.pageX,left:el.scrollLeft};moved=0;el.style.cursor='grabbing'});
  listen(window,'mousemove',event=>{if(!start)return;const dx=event.pageX-start.x;moved=Math.max(moved,Math.abs(dx));el.scrollLeft=start.left-dx;event.preventDefault()});
  listen(window,'mouseup',()=>{start=null;el.style.cursor=''});
  listen(el,'click',event=>{if(moved>6){event.stopPropagation();event.preventDefault();moved=0}},{capture:true});
  const resize=new ResizeObserver(update);resize.observe(el);
  const control={options,update,destroy(){abort.abort();resize.disconnect();horizontalControls.delete(el);el.style.cursor='';if(!horizontalControls.size){horizontalCleanup?.disconnect();horizontalCleanup=null}}};
  horizontalControls.set(el,control);
  if(!horizontalCleanup){horizontalCleanup=new MutationObserver(()=>{for(const [node,item] of horizontalControls)if(!node.isConnected)item.destroy()});horizontalCleanup.observe(document.body,{childList:true,subtree:true})}
  update();return control;
}

/* 一排里标出「当前是哪一个」的那块底板，全站只有这一种动法：滑过去、冲过落点、荡回来。
   筛选条上那块玻璃、抽屉那一列、分段控件里那块白底，在人眼里是同一件事，各写一段就会
   各自漂移成三种手感。
   弹簧曲线和它的时长都写在 `board.css` 的 `--spring-pane` 上，这里只读一次：那串数是一次
   弹簧模拟的采样结果，抄第二份就没人再改得动它。 */
let paneSpring=null;
export function glideEase(){
  if(!paneSpring){
    const css=getComputedStyle(document.documentElement);
    paneSpring={easing:css.getPropertyValue('--spring-pane').trim()||'ease',
      duration:parseFloat(css.getPropertyValue('--spring-pane-ms'))||300};
  }
  return paneSpring;
}
/* 位移走 `translate`、形变走 `scale`，两个独立属性各挂一段动画，不挤进同一条
   `transform`：一条属性上只放得下一段，而这两下的时间形状不是同一条曲线——位移冲过
   落点再荡回来，抻开是中途最大、两头归一。分开写，两段仍然都在合成线程上。
   都不碰 `width`：宽度是布局属性，逐帧改它等于让整份文档重新排版一遍，合成线程碰不
   到它，主线程一忙这块底板就跟着卡住。
   `from` 给 null 就只落位不动画：第一次出现的那块不该从别处飞进来。 */
export function moveGlidePane(pane,from,box,axis='x'){
  pane.style.width=`${box.w}px`;pane.style.height=`${box.h}px`;
  const span=axis==='y'?'h':'w',head=axis==='y'?'y':'x';
  const settled=`${box.x}px ${box.y}px`;
  if(from&&from[head]!==box[head]&&!matchMedia('(prefers-reduced-motion:reduce)').matches){
    const ease=glideEase();
    /* 先撤掉还在跑的那两段：一块上叠着两段位移，晚建的那段从头起跑，先建的还在往它
       自己的终点走，合出来的位置两边都不是。 */
    pane.getAnimations().forEach(a=>a.cancel());
    pane.animate([{translate:axis==='y'?`${box.x}px ${from.y}px`:`${from.x}px ${box.y}px`},
      {translate:settled}],{duration:ease.duration,easing:ease.easing,fill:'none'});
    /* 一块被拽着走的软东西，跑起来在跑的方向上抻开，停下来收回去。抻多少按这一跳跨了
       自己几个身位算，封在一个半身位：再远也不该更长，那时候读起来不是被拉长的同一
       块，是换上来的另一块。峰值压在前三成——加速那一段才拉得动它。
       形变只在这一排排布的方向上：另一根轴的尺寸是这一排给定的，在那儿拉扯会让它看
       起来不是这一排里的东西。 */
    const reach=Math.min(Math.abs(box[head]-from[head])/box[span],1.5),grow=1+reach*.12;
    pane.animate([{scale:'1 1',offset:0},
      {scale:axis==='y'?`1 ${grow}`:`${grow} 1`,offset:.3},{scale:'1 1',offset:1}],
      {duration:ease.duration,easing:'ease-in-out',fill:'none'});
  }
  pane.style.translate=settled;
}

const incrementalControls=new Map();
let incrementalCleanup;
/** 分页请求互斥，失败留在原位手动重试，卸载后丢弃结果。 */
export function wireLoadMore(button,options){
  if(!button)return;
  const existing=incrementalControls.get(button);
  if(existing){existing.options=options;return existing}
  let busy=false,failed=false,errorNode=null,request=null,disposed=false;
  const clearError=()=>{errorNode?.remove();errorNode=null;failed=false};
  const control={options,async run(manual=false){
    const current=control.options;
    if(disposed||busy||button.hidden||!button.isConnected||(!manual&&failed)||current.enabled?.()===false)return;
    clearError();busy=true;request=new AbortController();
    const alive=()=>!disposed&&!request.signal.aborted&&button.isConnected&&current.isCurrent?.()!==false;
    setActionBusy(button,true);
    try{
      const result=await current.read(request.signal);
      if(alive())await current.apply?.(result);
    }catch(error){
      if(alive()&&error?.name!=='AbortError'){
        failed=true;errorNode=document.createElement('div');
        errorNode.innerHTML=noteHtml(error?.message||String(error),{variant:'error',actionLabel:'重试'});
        errorNode.querySelector('[data-note-action]').onclick=()=>control.run(true);
        button.after(errorNode);
      }
    }finally{busy=false;setActionBusy(button,false)}
  },destroy(){disposed=true;request?.abort();observer.disconnect();button.removeEventListener('click',click);clearError();incrementalControls.delete(button);if(!incrementalControls.size){incrementalCleanup?.disconnect();incrementalCleanup=null}}};
  const click=()=>control.run(true);
  button.addEventListener('click',click);
  const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting))void control.run()},{rootMargin:'320px'});
  observer.observe(button);incrementalControls.set(button,control);
  if(!incrementalCleanup){incrementalCleanup=new MutationObserver(()=>{for(const [node,item] of incrementalControls)if(!node.isConnected)item.destroy()});incrementalCleanup.observe(document.body,{childList:true,subtree:true})}
  return control;
}

/** 两行筛选浮层；页面拥有槽位里的控件与查询状态。 */
export function mountFilterFrame(top,bottom,{views,tags,readout,controls}){
  let frame=top.closest('[data-filter-frame]');
  if(!frame){
    frame=document.createElement('div');
    frame.className='board-filter-frame';
    frame.dataset.filterFrame='';
    top.before(frame);
    frame.append(top);
    top.dataset.filterRow='top';
  }
  const previous=frame.querySelector('[data-filter-row="bottom"]');
  if(previous!==bottom){
    const active=document.activeElement;
    const key=previous?.contains(active)?['id','data-sort','data-entity-sort','aria-label'].map(attr=>[attr,active.getAttribute(attr)]).find(([,value])=>value):null;
    previous?.remove();frame.append(bottom);
    if(key)[...bottom.querySelectorAll('button,input,[tabindex]')].find(node=>node.getAttribute(key[0])===key[1])?.focus({preventScroll:true});
  }
  bottom.dataset.filterRow='bottom';
  for(const [slot,node] of Object.entries({views,tags,readout,controls})){
    if(node)node.dataset.filterSlot=slot;
  }
  return frame;
}

/* 逐条明细收在 Note 自己的 <details> 里，默认折叠：一句话的结论后面跟着上千行清单时，
   下面的内容全被推走，而那句结论本身才是要先读到的东西。每条给标题、说明和路径三段：
   只给一个「查看视频」链接的话，是哪个文件得逐个点开才知道。 */
function noteDetailsHtml({label='',items=[],footnote=''}={}){
  const line=item=>`<li>${item.href?`<a href="${esc(item.href)}">${esc(item.label||'')}</a>`
    :`<b>${esc(item.label||'')}</b>`}<span>${esc(item.note||'')}</span>${
    item.hint?`<code>${esc(item.hint)}</code>`:''}</li>`;
  return `<details class="geist-note-details"><summary>${esc(label)}</summary>
    <ul>${items.map(line).join('')}</ul>${footnote?`<p>${esc(footnote)}</p>`:''}</details>`;
}

/** 数据管理子页的结果标题，只接收当前查询得到的读数。
    `pending` 是这次请求还没回来：标题那一句同步就有，等的只有读数，占位也就只盖读数
    那一格，宽高定死，数字回来时这块面不改高度。 */
export function collectionSummaryHtml(label,value,detail='',{pending=false}={}){
  const figure=pending?'<span class="countskeleton"></span>':esc(value);
  return `<header class="collection-summary"><div><span>${esc(label)}</span><strong>${figure}</strong></div>${detail?`<p>${esc(detail)}</p>`:''}</header>`;
}

/* Inline, persistent context beside the field/card/section it describes.
   恢复动作有两种形态：留在本页执行的走按钮，要离开本页才做得成的走链接。
   两者占同一个格子、同一枚 `data-note-action`，Note 的版式不因为它是 <a> 改变。 */
export function noteHtml(message,{variant='secondary',label='',className='',size='medium',filled=false,actionLabel='',actionHref='',details=null}={}){
  const kind=NOTE_VARIANTS.has(variant)?variant:'secondary';
  const symbol=kind==='secondary'?'info':kind==='success'?'check':'alert';
  const role=kind==='error'?' role="alert"':' role="note"';
  const action=!actionLabel?''
    :actionHref?`<a class="geist-button" href="${esc(actionHref)}" data-note-action>${esc(actionLabel)}</a>`
    :`<button type="button" class="geist-button primary" data-note-action>${esc(actionLabel)}</button>`;
  return `<div class="geist-note geist-note-${kind}${className?` ${esc(className)}`:''}${size==='small'?' geist-note-small':''}${filled?' geist-note-filled':''}"${role}>
    ${icon(symbol)}<p>${label?`<b>${esc(label)}</b>`:''}<span>${esc(kind==='error'?requestErrorMessage(message):message)}</span></p>${action}${details?noteDetailsHtml(details):''}</div>`;
}

const PROJECT_BANNER_CLASSES={gray:'project-banner-gray',success:'project-banner-success',warning:'project-banner-warning',error:'project-banner-error'};
export function projectBannerHtml(message,{variant='gray',href,label,value,max}={}){
  const kind=['gray','success','warning','error'].includes(variant)?variant:'gray';
  return `<aside class="project-banner ${PROJECT_BANNER_CLASSES[kind]}" role="${kind==='error'?'alert':'status'}"><div>${Number(max)>0?gaugeHtml('任务完成率',value,max):icon(kind==='error'||kind==='warning'?'alert':'info')}<p>${esc(message)}</p></div><a href="${esc(href)}">${esc(label)}</a></aside>`;
}

export function gaugeHtml(label,value,max=100,{usage=false,compact=false}={}){
  const ceiling=Number(max), current=Number(value);
  if(!Number.isFinite(ceiling)||ceiling<=0||!Number.isFinite(current))return `<span>${esc(label)}：未取得</span>`;
  const percent=Math.max(0,Math.min(100,current/ceiling*100));
  const level=usage?(percent>=95?'error':percent>=80?'warning':'normal'):'normal';
  const status=usage?(level==='error'?'空间即将用满':level==='warning'?'空间使用偏高':'空间充足'):'';
  return `<span class="geist-gauge" data-level="${level}" role="progressbar" aria-label="${esc(label+(status?'：'+status:''))}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}"><svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="13"/><circle cx="16" cy="16" r="13" pathLength="100" stroke-dasharray="${percent} 100"/></svg></span>${status&&!compact?`<span class="gauge-status">${status}</span>`:''}`;
}

export function configurationSkeletonHtml(){
  const groups=[['通用',1],['媒体',2],['网络与访问',2],['更新与维护',3]];
  return `<div class="configpage" data-skeleton="configuration" role="status" aria-label="正在读取配置">${groups.map(([label,count])=>`<h2 class="configgroup" aria-hidden="true">${label}</h2>${Array.from({length:count},()=>`<div class="configfieldset config-skeleton-card" aria-hidden="true"><div class="geist-fieldset-content"><span class="skeleton"></span><span class="skeleton"></span><span class="skeleton"></span></div><footer class="geist-fieldset-footer"><span class="skeleton"></span></footer></div>`).join('')}`).join('')}</div>`;
}

/**
 * Geist Fieldset 的标题。标题是正文区的第一行，不是独立横条。
 *
 * 不用原生 `<legend>`：它会在上边框上开一个缺口，标题看起来骑在线上而不是在
 * 框里。也不给标题加下边框——Geist 的 Fieldset 全框只有一条线，在底部操作条
 * 上方（证据：https://vercel.com/geist/fieldset 的 Multiple Fieldsets 示例）。
 */
export function fieldsetTitle(id,title){
  return `<h3 class="geist-fieldset-title" id="${esc(id)}">${esc(title)}</h3>`;
}

/**
 * Geist Breadcrumbs（https://vercel.com/geist/breadcrumbs 实测）的列表本体。
 * 容器 nav[aria-label="Breadcrumb"] 归页面骨架所有，这里只画 `ol > li`。
 *
 * 每项自带一个尾部分隔符，最后一项的由 CSS 隐藏；当前项用
 * `aria-current="true"`（Geist 语义是 true，不是 "page"）渲染成纯文本，
 * 其余项必须有 href，渲染成继承颜色的链接。
 */
export function breadcrumbHtml(items){
  const trail=items.map(item=>{
    const inner=item.href?`<a href="${esc(item.href)}">${esc(item.label)}</a>`
      :`<span>${esc(item.label)}</span>`;
    return `<li${item.current?' aria-current="true"':''}>${inner}${icon('chevron-right')}</li>`;
  }).join('');
  return `<ol>${trail}</ol>`;
}

/** Determinate progress only. Callers supply real units instead of a decorative width. */
export function progressHtml(label,value,max=100,{variant='active',stops=[]}={}){
  const ceiling=Math.max(0,Number(max)||0);
  const current=Math.max(0,Math.min(Number(value)||0,ceiling));
  const percent=ceiling?current/ceiling*100:0;
  return `<div class="geist-progress" role="progressbar" aria-label="${esc(label)}"
    aria-valuemin="0" aria-valuemax="${ceiling}" aria-valuenow="${current}"
    style="--progress-value:${percent}%;--progress-color:var(${variant==='error'?'--drop':variant==='warning'?'--meter':'--feedback-success'})"><i></i>${stops.filter(stop=>Number(stop.value)>0&&Number(stop.value)<ceiling&&stop.label).map(stop=>`<span class="geist-progress-stop" style="left:${Number(stop.value)/ceiling*100}%" role="img" aria-label="${esc(stop.label)}"></span>`).join('')}</div>`;
}

/**
 * Geist Spinner: immediate feedback for a user-triggered action. Geist names
 * "inline icon refresh" as one of its three cases, so an icon-only key that
 * swaps its glyph for these ten bars is the prescribed shape, not a fallback.
 *
 * `label` names the work in flight (`正在换一批`), never the action the button
 * already carries. This span is a `role=status` region sitting inside a button
 * that has its own accessible name: repeating that name announces the same
 * words twice and tells the reader nothing changed.
 */
export function spinnerHtml(label='加载中'){
  const bars=Array.from({length:10},(_,index)=>
    `<i aria-hidden="true" style="--spinner-angle:${index*36}deg;--spinner-delay:${index*100-900}ms"></i>`).join('');
  return `<span class="geist-spinner" role="status" aria-label="${esc(label)}">${bars}</span>`;
}

/**
 * Geist Search Input: search icon as a prefix, swapped in place for a Spinner
 * while the query runs, and the input geometry never changes. Read-only queries
 * carry no submit button, so the accessible name lives in `aria-label` — a
 * placeholder is not a label, it disappears the moment there is text to read.
 */
export function searchInputHtml({label,id='',name='',value='',placeholder='',attrs=''}={}){
  const parts=[
    'type="search"',
    id?`id="${esc(id)}"`:'',
    name?`name="${esc(name)}"`:'',
    placeholder?`placeholder="${esc(placeholder)}"`:'',
    `value="${esc(value)}"`,
    `aria-label="${esc(label)}"`,
    'spellcheck="false" autocomplete="off"',
    attrs,
  ].filter(Boolean).join(' ');
  return `<div class="geist-search" data-search-input>
    <span class="geist-search-prefix" data-search-prefix>${icon('search')}</span>
    <input ${parts}></div>`;
}

/**
 * Geist loading action: visually unavailable and inert without using native
 * `disabled`, so the trigger keeps keyboard focus while its request is running.
 */
export function setActionBusy(control,busy=true){
  if(!control)return;
  if(busy){
    control.setAttribute('aria-busy','true');
    control.setAttribute('aria-disabled','true');
  }else{
    control.removeAttribute('aria-busy');
    control.removeAttribute('aria-disabled');
  }
}

const busyActionRoots=new WeakSet();

/** Block repeat pointer and keyboard activation for every shared busy action. */
export function wireBusyActions(root=document){
  if(busyActionRoots.has(root))return;
  busyActionRoots.add(root);
  root.addEventListener('click',event=>{
    const control=event.target.closest?.('button[aria-busy="true"],[role="button"][aria-busy="true"]');
    if(!control||!root.contains(control))return;
    event.preventDefault();
    event.stopImmediatePropagation();
  },true);
}

/** Geist Loading Dots: indeterminate work continuing in the background. */
export function loadingDotsHtml(label='正在处理', {className=''}={}){
  return `<span class="geist-loading${className?` ${esc(className)}`:''}" role="status">
    <span class="geist-loading-dots" aria-hidden="true"><i></i><i></i><i></i></span>
    <span>${esc(label)}</span></span>`;
}

/** Geist Skeleton: reserve a large content region while its structure is loading. */
/* `count` 只对 cards 生效：块数是骨架说出口的结构预告，六块对上的是海报网格，
   而行政界面往往只有两三个大区。多画的块加载完就消失，那不是占位是误报。 */
export function skeletonHtml(label='正在读取内容',{className='',variant='panel',count=6,fill=true,gridClass='',gridSize=''}={}){
  const kind=new Set(['panel','cards','dashboard']).has(variant)?variant:'panel';
  const body=kind==='cards'
    ?Array.from({length:Math.max(1,count)},
      ()=>`<span class="skeletoncard"><i></i><s></s><b></b><em></em><u></u></span>`).join('')
    :kind==='dashboard'
      /* 指标带是统计与口味两页真正的第一屏内容，四格的位置和高度都是定死的。
         骨架从大区开始画，等数据到货再从上面挤进一条 96px 的带子，整页往下跳一次。 */
      ?`<span class="skeletondashstrip">${Array.from({length:4},
          ()=>`<span><i></i><b></b><em></em></span>`).join('')}</span>
        <span class="skeletondashhero"><i></i><b></b></span>
        <span class="skeletondashpanel"><i></i><b></b><em></em></span>
        <span class="skeletondashpanel"><i></i><b></b><em></em></span>`
    :`<span class="skeleton" style="width:38%"></span>
      <span class="skeleton" style="width:100%"></span>
      <span class="skeleton" style="width:100%"></span>
      <span class="skeleton" style="width:72%"></span>`;
  /* data-skeleton 是这张骨架的身份。深链启动先画一张、路由到位后各页再画一张，
     整页刷新就会连闪两段动画；调用方拿这个键判断「已经是同一张了」，跳过重画。 */
  return `<div class="skeletonpanel skeleton-${kind}${className?` ${esc(className)}`:''}"
    data-skeleton="${esc(kind)}${className?`/${esc(className)}`:''}"${kind==='cards'&&fill?' data-fill=""':''}
    role="status" aria-label="${esc(label)}"><span class="sr-only">${esc(label)}</span>
    <div${gridClass?` class="${esc(gridClass)}"`:''}${gridSize?` data-size="${esc(gridSize)}"`:''} aria-hidden="true">${body}</div></div>`;
}

/** 索引占位复用最终网格、头像和词表的尺寸。 */
export function indexSkeletonHtml({kind,layout='big',mode='alphabet'}={}){
  const people=kind!=='tags',company=kind==='studios'||kind==='agencies';
  const cell=people
    ?'<span class="icell"><span class="ring skeleton"></span><span class="nm skeleton">&nbsp;</span><span class="n skeleton">&nbsp;</span></span>'
    :'<span class="alphatag"><span class="skeleton"></span><span class="n skeleton"></span></span>';
  const grid=people?`igrid" data-cells="${company?'company':'people'}" data-layout="${esc(layout)}`:'alphalist';
  const body=!people&&mode==='cloud'
    ?`<div class="tagwall index-tags">${Array.from({length:60},(_,i)=>
      `<span class="tg skeleton" style="width:${[92,128,76,108,144][i%5]}px">&nbsp;</span>`).join('')}</div>`
    :people?`<div class="${grid}">${cell.repeat(12)}</div>`
    :`<section class="alphagroup"><span class="indexletterskeleton skeleton"></span><div class="${grid}">${cell.repeat(12)}</div></section>`;
  const label='正在读取索引';
  return `<div class="skeletonpanel index-skeleton" data-skeleton="index/${esc(kind)}/${esc(layout)}/${esc(mode)}"${people||mode!=='cloud'?' data-fill=""':''}
    role="status" aria-label="${label}"><span class="sr-only">${label}</span><section aria-hidden="true">${body}</section></div>`;
}

/* 骨架的枚数由容器当下的宽度决定，不写死一个数：横向一行铺到右缘为止，网格补满
   整行。写死的话宽屏最后一行留一截豁口，窄屏和手机端又多出一堆要横滑才看得见的
   占位；算出来就不必再为断点各写一套。宽度序列只是让胶囊长短不一，像真词。 */
const SKELETON_SLOT={
  av:()=>`<span class="av avskeleton"><span class="ring"></span><span class="nm">&nbsp;</span></span>`,
  brandpill:width=>`<span class="brandpill brandskeleton" style="width:${width}px"><span class="mk"></span></span>`,
  pill:width=>`<span class="pill tagskeleton" style="width:${width}px"></span>`,
};
const SKELETON_SLOT_WIDTHS={
  av:[0],
  brandpill:[132,158,118,146,124,164,138],
  pill:[92,68,104,76,88,64,96,72,100,80,68,92,76,84],
};

/* 低于这一段的请求直接显示内容。Peach 的数据多在本机，立即把占位画出来会让几十毫秒的
   正常读取看成一次闪烁；超过门槛才说明页面确实需要等待。只藏最外层占位，内部结构仍先
   参与布局和 fit 计算，因此真正出现时不会再重排。 */
const SKELETON_REVEAL_DELAY=180;
const SKELETON_REVEAL_SELECTOR='[data-skeleton],[data-skeleton-tier],.countskeleton';
function armSkeletonReveal(root){
  if(!root)return;
  const all=[...(root.matches?.(SKELETON_REVEAL_SELECTOR)?[root]:[]),
    ...root.querySelectorAll(SKELETON_REVEAL_SELECTOR)];
  const targets=all.filter(node=>!all.some(parent=>parent!==node&&parent.contains(node)));
  for(const target of targets){
    /* 已经武装过的跳过这一枚就好。写 `return` 会让同一批里排在它后面的占位
       一个都拿不到延迟标记，补进来的那半屏骨架直接闪出来。 */
    if(target.dataset.skeletonReveal)continue;
    target.dataset.skeletonReveal='pending';
    target.classList.add('skeleton-awaiting');
    setTimeout(()=>{
      if(!target.isConnected||target.dataset.skeletonReveal!=='pending')return;
      target.dataset.skeletonReveal='shown';
      target.classList.remove('skeleton-awaiting');
    },SKELETON_REVEAL_DELAY);
  }
}

/** 一行横向骨架：逐枚追加到溢出容器右缘为止。上限只是死循环的护栏。 */
export function fillSkeletonTier(row,kind){
  const slot=SKELETON_SLOT[kind],widths=SKELETON_SLOT_WIDTHS[kind];
  if(!slot||!row)return;
  for(let i=0;i<64;i++){
    row.insertAdjacentHTML('beforeend',slot(widths[i%widths.length]));
    if(row.scrollWidth>row.clientWidth)break;
  }
  armSkeletonReveal(row);
}

/** 骨架落进 DOM 之后按实际尺寸补齐：横向一行铺满，卡片网格补到整行且盖住视口余量。 */
export function fitSkeleton(root){
  if(!root)return;
  const scoped=selector=>[...(root.matches?.(selector)?[root]:[]),...root.querySelectorAll(selector)];
  for(const row of scoped('[data-skeleton-tier]'))fillSkeletonTier(row,row.dataset.skeletonTier);
  for(const grid of scoped('.skeletonpanel[data-fill]>div,.index-skeleton[data-fill]>section>div')){
    const first=grid.firstElementChild,style=getComputedStyle(grid);
    /* 横排的推荐行不是网格，列数无从谈起，按整行补会把它裁成一张。 */
    if(!first||style.display!=='grid')continue;
    const columns=style.gridTemplateColumns.split(' ').filter(Boolean).length;
    const rowGap=parseFloat(style.rowGap)||0,cardHeight=first.getBoundingClientRect().height;
    if(!columns||!cardHeight)continue;
    /* 骨架说的是「这块地方等下会被填满」，所以铺到视口下沿；四行是护栏，
       再多也是一屏之外看不见的占位，白占动画。 */
    const room=window.innerHeight-grid.getBoundingClientRect().top;
    const maxRows=grid.classList.contains('alphalist')?24:4;
    const rows=Math.max(1,Math.min(maxRows,Math.ceil((room+rowGap)/(cardHeight+rowGap))));
    const want=columns*rows;
    while(grid.children.length>want)grid.lastElementChild.remove();
    while(grid.children.length<want)grid.appendChild(first.cloneNode(true));
  }
  armSkeletonReveal(root);
}

/**
 * 资料页与关注列表共用的视图按钮：一排、一个尺寸。
 *
 * 这几个键问的是同一件事——这一页现在显示什么，所以都是这一组里的按钮，不另起控件。
 * 给空值的那一位不出按钮：没有照片的人不该看见照片键，不是事务所的实体没有名册。
 */
export function mediaViewButtonsHtml({
  active='videos',peopleValue='',videoValue='videos',imageValue='images',
  peopleLabel='艺人',videoLabel='视频',imageLabel='图片',
  peopleCount=null,videoCount=null,imageCount=null,label='媒体类型',className='',
}={}){
  const control=(value,text,count,symbol,kind)=>{
    const title=count===null||count===undefined
      ?text:`${text} ${Math.max(0,Number(count)||0).toLocaleString()}`;
    return `<button class="mediaviewbutton" type="button" data-media-view="${esc(value)}"
      data-media-icon="${kind}" aria-pressed="${active===value}" aria-label="${esc(title)}"
      title="${esc(title)}">${icon(symbol)}</button>`;
  };
  return `<div class="mediaviewbuttons${className?` ${esc(className)}`:''}" role="group" aria-label="${esc(label)}">
    ${peopleValue?control(peopleValue,peopleLabel,peopleCount,'user-round','people'):''}
    ${videoValue?control(videoValue,videoLabel,videoCount,'play','video'):''}
    ${imageValue?control(imageValue,imageLabel,imageCount,'pics','image'):''}</div>`;
}

/**
 * Board 下划线 Tabs（boardui tabs.tsx）：一排互斥的「这一页现在摆的是哪一组东西」。
 *
 * 索引页用它切厂牌／事务所与本地／在线两套词表：两档各是一条地址。它回答的是页面层级的
 * 「在哪一页」，不是给当前这批加一条筛选——筛选归玻璃条上的药丸。
 * 每一枚都是 `role=tab`，当前项写 `aria-selected`；滑动的 2px 蓝线由 `board-local-nav`
 * 那条共用规则和 `wireBoardTabs` 提供，这里只出 DOM。计数是可选的尾随徽标，口径由调用方
 * 给：Tabs 自己不算数。前置字形也是可选的，只在它指向对象（厂牌、事务所、本地、订阅源）
 * 时出现。
 */
export function boardTabsHtml(items,{active='',attr='data-tab',label='页面视图',className='',panel=''}={}){
  const tabs=items.map(({value,label:text,count,symbol})=>{
    const selected=String(value)===String(active);
    const badge=count==null?'':`<span class="board-tab-count">${esc(Number(count).toLocaleString())}</span>`;
    return `<button type="button" role="tab" ${attr}="${esc(value)}" aria-selected="${selected}"${
      panel?` aria-controls="${esc(panel)}"`:''}>${symbol?icon(symbol):''}${esc(text)}${badge}</button>`;
  }).join('');
  return `<div class="board-local-nav board-tabs${className?` ${esc(className)}`:''}" role="tablist" aria-label="${esc(label)}">${tabs}</div>`;
}

/** Geist Empty State: icon tile, title and explanatory copy stay one semantic unit. */
export function emptyStateHtml(iconName,title,description,{className='',actions=''}={}){
  return `<div class="emptystate${className?` ${esc(className)}`:''}" data-geist-empty-state role="status">
    <div class="es-icon" aria-hidden="true">${icon(iconName)}</div>
    <div class="es-copy"><h3>${esc(title)}</h3><p>${esc(description)}</p></div>
    ${actions?`<div class="es-actions">${actions}</div>`:''}
  </div>`;
}

/** Geist Scroller: one-axis overflow with edge fades as the scroll affordance. */
export function scrollerHtml(content,{className='',label='可滚动内容',overflow='y'}={}){
  const axis=new Set(['x','y','both']).has(overflow)?overflow:'y';
  return `<div class="geist-scroller${className?` ${esc(className)}`:''}" data-geist-scroller>
    <div class="geist-scroller-overlay" aria-hidden="true"></div>
    <div class="geist-scroller-container" data-overflow="${axis}" tabindex="0" aria-label="${esc(label)}">${content}</div>
  </div>`;
}

function updateScroller(wrapper){
  const container=wrapper.querySelector(':scope > .geist-scroller-container');
  const overlay=wrapper.querySelector(':scope > .geist-scroller-overlay');
  if(!container||!overlay)return;
  overlay.classList.toggle('can-scroll-top',container.scrollTop>1);
  overlay.classList.toggle('can-scroll-bottom',container.scrollTop+container.clientHeight<container.scrollHeight-1);
  overlay.classList.toggle('can-scroll-left',container.scrollLeft>1);
  overlay.classList.toggle('can-scroll-right',container.scrollLeft+container.clientWidth<container.scrollWidth-1);
}

/** Wire newly rendered scrollers without duplicating listeners after a rerender. */
export function wireScrollers(root=document){
  root.querySelectorAll('[data-geist-scroller]').forEach(wrapper=>{
    const container=wrapper.querySelector(':scope > .geist-scroller-container');
    if(!container)return;
    if(!container.dataset.scrollerWired){
      container.dataset.scrollerWired='true';
      container.addEventListener('scroll',()=>updateScroller(wrapper),{passive:true});
      container.addEventListener('load',()=>updateScroller(wrapper),true);
    }
    requestAnimationFrame(()=>updateScroller(wrapper));
  });
}

/** 挂覆盖式滚动条的滚动容器。列表只写在这一处，样式那边认的是挂上之后的属性。
 *
 * `.stagescroll` 是详情浮窗里所有内容的外层。窄屏下整块内容自己纵向滚，滚的得是它而不是
 * `<dialog class="stage">` 本身：轨道必须是滚动容器的兄弟，而 dialog 在顶层，挂在它
 * 父级上的轨道会落到遮罩底下。宽屏下它不溢出，组件自己量得出来，轨道不显示。 */
const OVERLAY_SCROLLERS=[
  '.settingsscroll','.sidecontent','.stagescroll','.tagpickbody','.mixlist','.playlistpicklist','.playerstats',
  '.vjs-peach-settings-menu','.geist-scroller-container','.metricstrip','.tastesummaries',
  '.skeletondashstrip','.followpagination','.linktablewrap',
  '.reviewtabs','.junkfilters','.ftablewrap','.board-local-nav','.managebar-menu',
  '.follow-workspace-switch','.fmanagenav','[role="listbox"]',
].join(',');
/* Board 层里会超宽的横向滚动层：两端按滚动位置渐隐说明「那边还有」，鼠标停在上面时竖向
   滚轮转成横向。边线留给外层框，渐隐只落在这一层。
   这里登记的都是 `frontend/` 或 board.css 画出来的层，它们不经过 `wireAllDrag` 那份按 id
   点名的清单，漏登记就是「看得见、够不着」：设置弹层那排分区在 390px 下溢出 244px，
   实测既没有渐隐也不接滚轮。组件自己量溢出，不溢出的宽度上登记等于空转，所以按可能
   溢出的层登记，不按某一个断点登记。React 档的页面自己用 `overflow-x-auto`，不进这份清单。 */
const BOARD_EDGE_SCROLLERS='.reviewtabs,.ftablewrap,.board-local-nav,.managebar-menu,'
  +'.follow-workspace-switch,.fmanagenav';

/**
 * 覆盖式滚动条：滑块浮在内容上，一列宽度都不占。
 *
 * 已有的 `.geist-scroller` 解决的是另一半问题——它用两端渐隐说明「还能往下」，
 * 但没有滑块，读不出这一列有多长、自己停在哪儿，而且要求内容套进它自己的包装层。
 * 这里只往既有滚动容器的父元素上挂轨道，不动内容结构，两者可以叠加使用。
 *
 * 轨道必须是容器的兄弟：跟着内容一起滚的轨道等于没有轨道。宿主因此得是定位祖先，
 * 而且不一定和容器一样大（`.settingscard` 还含着标题栏），所以轨道的位置每次都按
 * 两个 rect 量出来，不假设它们同框。两条轴各一条轨道，谁溢出谁显示——同一个容器
 * 可能在不同版式下换轴（`.mixlist` 在 mixgrid 里就是横滚）。
 * 整页那一条是唯一的例外：`html` 没有元素父级，轨道挂进 body 并由 `.page` 改成
 * fixed，位置只认视口，不用量。
 * 几何按 2026-09-05 实测 vercel.com 侧栏：
 * 滑块长 = 可视长 / 内容长 × 轨道长，位移 = 滚动进度 × (轨道长 − 滑块长)。
 * 返回一个手动重算函数，给那些既不改容器尺寸也不改子树的情形（例如换字体后重排）。
 */
export function attachOverlayScrollbar(container,{variant=''}={}){
  if(!container||container.dataset.overlayScrollbar)return null;
  const root=container===document.documentElement;
  const host=root?document.body:container.parentElement;
  if(!host)return null;
  container.dataset.overlayScrollbar='true';
  // 轨道按宿主的内边距框定位，static 的宿主会把它甩到更外层某个祖先上去。
  if(!root&&getComputedStyle(host).position==='static')host.style.position='relative';
  const lanes=(root?['y']:['y','x']).map(axis=>{
    const track=document.createElement('div');
    // 两个类名写全，别拼 `ov-${axis}`：样式表的选择器要能在源码里查到消费者。
    track.className=`ovtrack ${axis==='y'?'ov-y':'ov-x'}${variant?` ${variant}`:''}`;
    const thumb=document.createElement('div');
    thumb.className='ovthumb';
    track.append(thumb);
    host.append(track);
    return {axis,track,thumb};
  });
  /* 容器在宿主里的偏移，只能按布局盒子量。`getBoundingClientRect()` 给的是变换后的
     几何，而下面要拿它跟 `clientWidth` 这类布局值相减——弹层开合动画正把卡片按
     `scale(.85)` 缩着的那 300ms 里，两者不在同一个坐标系，算出来的轨道位置会落进
     容器内部。实测设置弹层首帧右边距 41px（应为 0），直到滚一下触发重算才跳回右
     边缘，看着像「滚动条从左边跑到右边」。`offsetLeft`/`offsetTop` 不受变换影响，
     沿 offsetParent 链累加到宿主为止；走不到宿主（宿主不是定位祖先）才退回量 rect。 */
  const offsetWithin=()=>{
    let left=0,top=0,node=container;
    while(node&&node!==host){left+=node.offsetLeft;top+=node.offsetTop;node=node.offsetParent}
    if(node===host)return {left,top};
    const hostRect=host.getBoundingClientRect(),rect=container.getBoundingClientRect();
    return {left:rect.left-hostRect.left-host.clientLeft,
      top:rect.top-hostRect.top-host.clientTop};
  };
  const place=({axis,track})=>{
    if(root)return;
    const {left,top}=offsetWithin();
    if(axis==='y'){
      track.style.top=`${top+8}px`;
      track.style.height=`${Math.max(0,container.clientHeight-16)}px`;
      track.style.right=`${host.clientWidth-left-container.clientWidth}px`;
    }else{
      track.style.left=`${left+8}px`;
      track.style.width=`${Math.max(0,container.clientWidth-16)}px`;
      track.style.bottom=`${host.clientHeight-top-container.clientHeight}px`;
    }
  };
  const sync=()=>{
    lanes.forEach(lane=>{
      const {axis,track,thumb}=lane,vertical=axis==='y';
      const size=vertical?container.clientHeight:container.clientWidth;
      const content=vertical?container.scrollHeight:container.scrollWidth;
      const range=content-size;
      if(range<=1){track.hidden=true;return}
      // 先显再量：藏起来的轨道长度是 0，拿它当「量不到」会把自己永久锁在隐藏态。
      track.hidden=false;
      place(lane);
      const trackSize=vertical?track.clientHeight:track.clientWidth;
      if(!trackSize)return;
      // 短到抓不住的滑块等于没有滑块：内容特别长时给它一个下限，代价是滑块位置与
      // 滚动进度不再严格线性，但可拖动比可换算重要。
      const thumbSize=Math.max(24,Math.min(trackSize,size/content*trackSize));
      const travel=trackSize-thumbSize;
      const at=vertical?container.scrollTop:container.scrollLeft;
      const offset=travel>0?at/range*travel:0;
      thumb.style[vertical?'height':'width']=`${thumbSize}px`;
      thumb.style.transform=`translate${vertical?'Y':'X'}(${offset}px)`;
    });
  };
  (root?document:container).addEventListener('scroll',sync,{passive:true});
  new ResizeObserver(sync).observe(container);
  // 内容长短变了但容器盒子没变（抽屉重建、分区展开），容器自己的 ResizeObserver 一声不响。
  // 整页那一条改看 body：它的高度就是内容高度，而在 documentElement 上挂 subtree 的
  // MutationObserver 等于每渲染一张卡都强制一次重排。
  if(root)new ResizeObserver(sync).observe(document.body);
  else new MutationObserver(sync).observe(container,{childList:true,subtree:true});
  lanes.forEach(({axis,track,thumb})=>track.addEventListener('pointerdown',event=>{
    const vertical=axis==='y';
    const trackRect=track.getBoundingClientRect(),thumbRect=thumb.getBoundingClientRect();
    const travel=(vertical?trackRect.height-thumbRect.height:trackRect.width-thumbRect.width);
    const range=vertical?container.scrollHeight-container.clientHeight
      :container.scrollWidth-container.clientWidth;
    if(travel<=0||range<=0)return;
    const point=moved=>vertical?moved.clientY:moved.clientX;
    const head=vertical?thumbRect.top:thumbRect.left,tail=vertical?thumbRect.bottom:thumbRect.right;
    // 按在滑块上就保持按住的那一点，按在轨道空白处则把滑块中心挪过来。
    const grab=point(event)>=head&&point(event)<=tail?point(event)-head
      :(vertical?thumbRect.height:thumbRect.width)/2;
    const origin=vertical?trackRect.top:trackRect.left;
    const to=moved=>{const at=Math.max(0,Math.min(range,(point(moved)-origin-grab)/travel*range));
      if(vertical)container.scrollTop=at;else container.scrollLeft=at};
    const stop=()=>{track.classList.remove('dragging');
      track.removeEventListener('pointermove',to);track.removeEventListener('pointerup',stop);
      track.removeEventListener('pointercancel',stop)};
    track.classList.add('dragging');
    track.setPointerCapture(event.pointerId);
    track.addEventListener('pointermove',to);
    track.addEventListener('pointerup',stop);
    track.addEventListener('pointercancel',stop);
    to(event);
    event.preventDefault();
  }));
  sync();
  return sync;
}

/** 把这一批 DOM 里所有该有覆盖式滚动条的容器接上；重复调用只接新出现的那些。 */
export function wireOverlayScrollbars(root=document){
  root.querySelectorAll(OVERLAY_SCROLLERS).forEach(el=>{
    if(el.matches(BOARD_EDGE_SCROLLERS)){
      wireHorizontalScroller(el);return;
    }
    attachOverlayScrollbar(el);
  });
}

/**
 * Geist Switch：2–3 个互斥视图用共享 name 的一组 radio，不用 Toggle。
 *
 * JAV 卡片版式和关注列表版式是同一个控件——只有 name、选项和当前值不同，所以模板
 * 与 `.iconswitch` 样式共用一份；调用方各自的摆放位置仍由自己的类负责。
 */
export function iconSwitchHtml(name,legend,options,current,{attr='',className='',text=false}={}){
  const items=options.map(([value,label,symbol])=>
    `<label title="${esc(label)}"><input type="radio" name="${esc(name)}" value="${esc(value)}" ${attr}
      ${value===current?'checked':''}><span aria-hidden="true">${text?(symbol?icon(symbol):'')+esc(label):icon(symbol)}</span><span class="sr-only">${esc(label)}</span></label>`).join('');
  return `<fieldset class="iconswitch${className?` ${esc(className)}`:''}"><legend class="sr-only">${esc(legend)}</legend>${items}</fieldset>`;
}

/** 把一组 iconSwitchHtml 画出来的 radio 接到 apply(value) 上。 */
export function wireIconSwitch(root,attr,apply){
  root?.querySelectorAll(`[${attr}]`).forEach(input=>{
    input.onchange=()=>{if(input.checked)apply(input.value)};
  });
}

/* 自绘单值拉条。原生 `input[type=range]` 的轨道、抓手和刻度分散在三套带厂商前缀的伪
   元素里，拿不到当前值也接不上悬停才显形的刻度；换成一个 `role="slider"` 的容器之后，
   几何、状态和键盘全在一处。形状取自 feralui.dev/gradients 的 `.dial-slider`，实测记在
   `docs/reference-snapshots/feralui-studio-boardui-accent-measured.md`：30px 高、20px 轨道、
   每 10% 一根刻度、3×20px 的圆头抓手，刻度与抓手默认透明，悬停或拖动时才出现。
   颜色一律由 `--ink` 经 color-mix 得到，焦点环仍走站内的 `--tungsten`。
   当前位置写成 `--dial-at` 交给 CSS：填充宽度和抓手位置是同一个数，分两处写就会错开。 */
const DIAL_TICKS=9;
export function dialSliderHtml({value=0,min=0,max=100,step=1,label='',suffix='%',attr='',className=''}={}){
  const at=max>min?(value-min)/(max-min)*100:0;
  const text=`${value}${suffix}`;
  return `<div class="dial${className?` ${esc(className)}`:''}" ${attr}>
    <div class="dial-slider" data-dial-slider role="slider" tabindex="0" aria-label="${esc(label)}"
      aria-valuemin="${min}" aria-valuemax="${max}" aria-valuenow="${value}" aria-valuetext="${esc(text)}"
      data-dial-step="${step}" style="--dial-at:${at}%">
      <span class="dial-track" aria-hidden="true"><span class="dial-fill"></span></span>
      <span class="dial-ticks" aria-hidden="true">${'<span></span>'.repeat(DIAL_TICKS)}</span>
      <span class="dial-handle" aria-hidden="true"></span>
    </div><b class="dial-value mono" data-dial-value>${esc(text)}</b></div>`;
}

/**
 * 接上 dialSliderHtml 画出来的一条拉条。
 *
 * `onInput` 在拖动和键盘的每一步都发，调用方自己合并到一帧里；`onChange` 只在松手、
 * 键盘落键和触摸取消时发一次，落盘归它。两者分开是这条拉条唯一的性能约定：拖动中
 * 每一步都写 localStorage 的话，一次 60 步的拖动就是 60 次同步序列化。
 */
export function wireDialSlider(root,{onInput=()=>{},onChange=()=>{},suffix='%'}={}){
  const slider=root.querySelector('[data-dial-slider]'),readout=root.querySelector('[data-dial-value]');
  const track=root.querySelector('.dial-track');
  const min=+slider.getAttribute('aria-valuemin'),max=+slider.getAttribute('aria-valuemax');
  const step=+slider.dataset.dialStep||1;
  let value=+slider.getAttribute('aria-valuenow');
  const clamp=raw=>Math.min(max,Math.max(min,Math.round(raw/step)*step));
  const paint=()=>{
    const text=`${value}${suffix}`;
    slider.style.setProperty('--dial-at',`${max>min?(value-min)/(max-min)*100:0}%`);
    slider.setAttribute('aria-valuenow',String(value));
    slider.setAttribute('aria-valuetext',text);
    if(readout)readout.textContent=text;
  };
  const set=(raw,notify)=>{
    const next=clamp(raw);
    if(next===value)return false;
    value=next;paint();if(notify)onInput(value);return true;
  };
  /* 轨道几何在按下那一刻量一次就够，之后每次 pointermove 都读缓存。指针捕获期间这条
     轨道不会跑，而 `getBoundingClientRect()` 会强制同步一次样式与布局——放在每一个
     pointermove 里，一次拖动就是上百次强制布局，实测占掉这条链路一大半时间。 */
  let trackBox=null;
  const fromPointer=event=>{
    const rect=trackBox||track.getBoundingClientRect();
    const ratio=rect.width?(event.clientX-rect.left)/rect.width:0;
    set(min+(max-min)*Math.min(1,Math.max(0,ratio)),true);
  };
  slider.addEventListener('pointerdown',event=>{
    if(event.pointerType==='mouse'&&event.button!==0)return;
    event.preventDefault();slider.focus();
    trackBox=track.getBoundingClientRect();
    slider.dataset.dragging='true';
    /* 指针捕获拿不到就算了：一次合成出来的 pointerdown（自动化、辅助技术）带的 id
       不对应任何活动指针，`setPointerCapture` 会抛，抛出去整条拖动就断在第一步。 */
    try{slider.setPointerCapture(event.pointerId)}catch(_e){}
    fromPointer(event);
  });
  slider.addEventListener('pointermove',event=>{if(slider.dataset.dragging==='true')fromPointer(event)});
  const release=event=>{
    if(slider.dataset.dragging!=='true')return;
    delete slider.dataset.dragging;trackBox=null;
    try{if(slider.hasPointerCapture(event.pointerId))slider.releasePointerCapture(event.pointerId)}catch(_e){}
    onChange(value);
  };
  slider.addEventListener('pointerup',release);
  slider.addEventListener('pointercancel',release);
  /* 键盘一档就是一个 step，按住 Shift 走 10。Home／End 直接到两端：一条 0–100 的拉条
     用方向键从一头走到另一头要按一百下，那不叫可用。 */
  slider.addEventListener('keydown',event=>{
    const span=event.shiftKey?10:step;
    const moves={ArrowLeft:-span,ArrowDown:-span,ArrowRight:span,ArrowUp:span};
    let next=null;
    if(event.key in moves)next=value+moves[event.key];
    else if(event.key==='Home')next=min;
    else if(event.key==='End')next=max;
    if(next===null)return;
    event.preventDefault();
    if(set(next,true))onChange(value);
  });
  return {get value(){return value},set(next){set(next,false)}};
}

/**
 * 共用勾选框。原生 checkbox 在暗色下由浏览器自绘，跟站内别的控件不是同一套语言；
 * `accent-color` 也只能改选中色，未选中态连悬停反馈都给不了。所以自绘一份，关注
 * 列表、来源筛选、候选清单、标签匹配和设置项共用它。
 */
export function badgeHtml(text){return `<span class="geist-badge">${esc(text)}</span>`}

export function checkboxHtml(inputAttrs=''){
  return `<span class="pcheck"><input type="checkbox" ${inputAttrs}><span aria-hidden="true">${icon('check')}</span></span>`;
}

/**
 * Geist Collapse：原生 `<details>` 不过渡高度，所以把 summary 以外的内容包进
 * `.fcollapse`，开合时量 `scrollHeight` 写 inline `height` 让它过渡。
 * （试过 `::details-content`，那条路会吞掉内容，已弃。）
 *
 * 同一个 `details` 只接一次，重绘后原样再调用是安全的。
 */
export function wireCollapse(root,selector,idPrefix,triggerSelector='summary'){
  root?.querySelectorAll(selector).forEach((details,index)=>{
    if(details.querySelector(':scope > .fcollapse'))return;
    const body=document.createElement('div');body.className='fcollapse';
    /* 内边距放在内层 .fcollapsebody：.fcollapse 自身不带 padding，height 才能真正
       过渡到 0，否则 border-box 会卡在内边距上、收起末尾跳一下。 */
    const inner=document.createElement('div');inner.className='fcollapsebody';
    [...details.children].forEach(child=>{
      if(child.tagName==='SUMMARY')return;
      inner.appendChild(child);
    });
    body.appendChild(inner);details.appendChild(body);
    const summary=details.querySelector(triggerSelector);
    if(triggerSelector!=='summary')details.querySelector('summary').addEventListener('click',event=>event.preventDefault());
    let expanded=details.open;
    body.id=`${idPrefix}-${index}`;
    body.inert=!expanded;
    /* 高度过渡要 `overflow:hidden`，可展开着不动时它还在裁——里面最后那一行卡片的落影
       正好落在下沿外，被切掉半条，读出来是这一列没排完。过渡跑完（或一开始就是展开的）
       就摘掉那道裁边；收起那一下先装回去，否则内容会在高度收到 0 的过程中一直露在外面。 */
    if(expanded)body.classList.add('fcollapse-settled');
    summary.setAttribute('aria-controls',body.id);
    summary.setAttribute('aria-expanded',String(expanded));
    summary.addEventListener('click',event=>{
      event.preventDefault();
      expanded=!expanded;
      summary.setAttribute('aria-expanded',String(expanded));
      setCollapseOpen(details,body,expanded);
    });
  });
}

/**
 * 把一个 Collapse 开到或收到 `expanded`，`body` 是 summary 后面那层容器，`.fcollapse` 由这里挂上。
 * `wireCollapse` 与 React 设置页的 `Disclosure` 共用这一份；过渡途中又被反向点按时，前一次的收尾不再做。
 */
const collapseRuns=new WeakMap();
export function setCollapseOpen(details,body,expanded){
  body.classList.add('fcollapse');
  const run=(collapseRuns.get(body)||0)+1;collapseRuns.set(body,run);
  const isCurrent=()=>collapseRuns.get(body)===run;
  if(expanded){
    body.inert=false;
    const start=details.open?body.getBoundingClientRect().height:0;
    details.open=true;
    growCollapse(body,start,isCurrent);
  }else{
    body.inert=true;body.classList.remove('fcollapse-settled');
    body.style.height=body.getBoundingClientRect().height+'px';body.getBoundingClientRect();
    body.style.height='0px';
    settleHeight(body,()=>{if(isCurrent()){details.open=false;body.style.height=''}});
  }
}

/* 高度过渡跑完再收尾；减少动效时没有 transitionend，260ms 兜底。 */
function settleHeight(body,fn){
  let done=false,timer;
  const finish=e=>{
    if(e&&e.propertyName!=='height')return;
    if(done)return;done=true;
    body.removeEventListener('transitionend',finish);clearTimeout(timer);
    fn();
  };
  body.addEventListener('transitionend',finish);
  timer=setTimeout(finish,260);
}

/**
 * `.fcollapse` 从 `start` 长到内容此刻的高度，跑完交回 `auto` 并摘掉裁边。Collapse 展开与
 * 侧栏名单摊开共用这一份。`isCurrent` 返回 false 说明中途又被收起，收尾就不做。
 */
export function growCollapse(body,start,isCurrent=()=>true){
  body.classList.remove('fcollapse-settled');
  body.style.height=start+'px';body.getBoundingClientRect();
  body.style.height=body.scrollHeight+'px';
  settleHeight(body,()=>{if(isCurrent()){body.style.height='auto';body.classList.add('fcollapse-settled')}});
}

/* 锚定在触发钮上的菜单：无展开动画，固定在视口内，内容在菜单内滚动。

   优先从触发钮右缘向左展开，下方放不下时改到上方。全站的锚定菜单共用这一份定位与
   开关：菜单在视口边缘的表现最容易各写各的，同一语义留两份实现就只会有一份被修。 */
let openedMenu=null;
if(!globalThis.__peachMenuCloser){
  globalThis.__peachMenuCloser=true;
  /* 「点到别处就关」里的「别处」不能只按 mount 之外算。mount 是定位用的那一片祖先——
     侧栏配色弹层给的是 `.board-sidebar-foot`，媒体库弹层给的是整个 `#drawer`——设置钮
     和侧栏里其余每一枚控件都在里面，按 mount 算的话点它们全是「内点」，弹层就一直挂着。
     mount 缩到触发钮本身也不行：定位要按它算，菜单开在左边还是右边看的就是这一片。
     所以判据改成「点的是不是这枚菜单自己的东西」：菜单内部与触发钮上算内点，mount 里
     别的可点控件算外点，mount 里的空白仍算内点（点空白本来就什么也不该发生）。 */
  const clickable='a[href],button,input,select,textarea,summary,[role=button],[role=menuitem],[tabindex]';
  document.addEventListener('click',event=>{
    if(!openedMenu)return;
    const target=event.target;
    if(openedMenu.menu.contains(target)||openedMenu.toggle.contains(target))return;
    if(openedMenu.mount.contains(target)&&!(target instanceof Element&&target.closest(clickable)))return;
    openedMenu.setOpen(false)},true);
}
export function closeAnchoredMenu(){if(openedMenu)openedMenu.setOpen(false)}
/* 菜单面板的开合动效来自 boardui 的 menu-styles.ts（登记在 docs/BOARD_UI.md）：150ms
   ease-out，透明度、scale .95 和 2px 模糊一起进出。进场由 Board 层的 CSS 按 `:not([hidden])`
   起；退场要等动画放完再 hidden，display:none 一落下去动画就被掐掉。哪些面板算菜单由
   CSS 决定：读到的 animation-name 是 none（旧界面、prefers-reduced-motion）就当场藏起来。
   全站的菜单都从这两个口进出，`hidden` 才始终是「看不见了」，不会有一份自己写的 150ms。 */
const leavingMenus=new WeakMap();
export function presentMenu(menu){
  leavingMenus.delete(menu);menu.classList.remove('leaving');
  if(menu.hidden)playUiSound('whoosh');
  menu.hidden=false;
}
export function dismissMenu(menu,finish){
  if(menu.hidden||leavingMenus.has(menu))return;
  const done=()=>{if(leavingMenus.get(menu)!==done)return;
    leavingMenus.delete(menu);menu.classList.remove('leaving');menu.hidden=true;if(finish)finish()};
  leavingMenus.set(menu,done);
  menu.classList.add('leaving');
  if(getComputedStyle(menu).animationName==='none'){done();return}
  menu.addEventListener('animationend',event=>{if(event.target===menu)done()},{once:true});
  // 面板在动画结束前被别的规则藏掉（比如切了页）就收不到 animationend，兜一拍。
  setTimeout(done,240);
}
/* 可用的视口上沿是固定顶栏的下缘。顶栏在每一页都盖着最上面那一条，菜单顶到 8px
   会被它压掉半截，而且看不出是被压住的——只是第一项凭空不见了。 */
const viewportTop=()=>8+(parseFloat(getComputedStyle(document.documentElement)
  .getPropertyValue('--topH'))||0);
export function wireAnchoredMenu(mount,toggle,menu,{side=false}={}){
  const position=()=>{
    // 宽度读 offsetWidth：进场动画起手是 scale(.95)，getBoundingClientRect 量到的是缩过的框。
    const anchor=toggle.getBoundingClientRect(),width=menu.offsetWidth;
    if(side&&innerWidth>=640){
      menu.dataset.placement='right';
      menu.style.maxHeight=Math.max(0,innerHeight-32)+'px';
      /* 贴着触发钮的右缘开，允许压住侧栏剩下的那一段。按侧栏右缘起算的话，展开态下
         触发钮到侧栏边还有两百来像素，菜单和它点开的那个控件之间隔着一片空白，读不出
         是谁弹出来的。 */
      menu.style.left=Math.max(16,Math.min(anchor.right+8,innerWidth-width-16))+'px';
      menu.style.top=Math.max(16,Math.min(anchor.top,innerHeight-menu.offsetHeight-16))+'px';return;
    }
    const top=viewportTop(),under=innerHeight-8-anchor.bottom-8,over=anchor.top-8-top;
    /* 下方放不下就改到上方；两侧都放不下时取宽的那一侧，并把菜单压到那一侧的高度，
       内容在菜单内滚。不压高度的话它会横跨触发钮盖住自己，点开之后连改的是哪一个
       名字都看不见。 */
    const naturalHeight=menu.scrollHeight+menu.offsetHeight-menu.clientHeight;
    const downward=under>=naturalHeight||under>=over;
    const height=Math.min(naturalHeight,Math.max(downward?under:over,0));
    menu.dataset.placement=downward?'bottom':'top';
    menu.style.maxHeight=height+'px';
    const preferredLeft=menu.classList.contains('context-card')?anchor.left:anchor.right-width;
    menu.style.left=Math.max(8,Math.min(preferredLeft,innerWidth-width-8))+'px';
    menu.style.top=(downward?anchor.bottom+8:anchor.top-8-height)+'px'};
  /* 页面滚走了就关掉：菜单固定在视口里，锚点跟着内容跑，留着就悬在半空。
     菜单自己的滚动不算——它装不下时本来就要在内部滚，滚一下就关等于底下那几项
     根本够不着。捕获阶段连菜单内部的滚动一并收得到，所以这里必须自己分开。 */
  const closeFromViewport=event=>{
    if(!(event.target instanceof Node&&menu.contains(event.target)))setOpen(false)};
  /* 带 popover 的菜单进顶层。`position:fixed` 只在没有被祖先接管时才相对视口：祖先上
     一个 transform、filter 或 backdrop-filter 就会成为它的包含块，算好的视口坐标于是
     整体偏移，还要被那个祖先的 overflow 裁掉。设置面板的卡片正是这种祖先——入场动画的
     fill-mode 让 transform 一直挂在上面——菜单于是开在看不见的地方，读起来就是「点不开」。 */
  const inTopLayer=menu.hasAttribute('popover');
  /* 开着没开着记在这里，不看 `hidden`：退场那 150ms 里面板还在、hidden 还是 false，
     按 hidden 判会把「正在收」当成「开着」，再点一下触发钮就关了个已经在关的。 */
  let open=false;
  const setOpen=next=>{
    if(next){
      if(openedMenu&&openedMenu.mount!==mount)openedMenu.setOpen(false);
      open=true;presentMenu(menu);if(inTopLayer&&!menu.matches(':popover-open'))menu.showPopover();position();
      window.addEventListener('resize',position);
      window.addEventListener('scroll',closeFromViewport,{capture:true,passive:true});
    }else{
      open=false;
      window.removeEventListener('resize',position);
      window.removeEventListener('scroll',closeFromViewport,true);
      dismissMenu(menu,()=>{menu.style.left='';menu.style.top='';menu.style.maxHeight='';
        if(inTopLayer&&menu.matches(':popover-open'))menu.hidePopover()});
    }
    toggle.setAttribute('aria-expanded',String(next));
    openedMenu=next?{mount,menu,toggle,setOpen}:(openedMenu&&openedMenu.mount===mount?null:openedMenu)};
  toggle.addEventListener('click',event=>{event.stopPropagation();setOpen(!open)});
  mount.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&open){event.stopPropagation();setOpen(false);toggle.focus()}});
  return {setOpen,isOpen:()=>open};
}

/** 复杂补充信息复用顶层浮层和视口避让，正文可聚焦并独立滚动。 */
export function wireContextCard(mount,trigger,panel){
  panel.classList.add('context-card');panel.setAttribute('popover','manual');
  panel.setAttribute('role','dialog');panel.tabIndex=-1;
  trigger.setAttribute('aria-haspopup','dialog');trigger.setAttribute('aria-controls',panel.id);
  const floating=wireAnchoredMenu(mount,trigger,panel);
  let timer;
  const hide=()=>{clearTimeout(timer);floating.setOpen(false)};
  const enter=()=>{clearTimeout(timer);timer=setTimeout(()=>{if(trigger.isConnected)floating.setOpen(true)},150)};
  const leave=()=>{clearTimeout(timer);timer=setTimeout(()=>{if(!panel.matches(':hover')&&!trigger.matches(':hover')&&!panel.contains(document.activeElement)&&document.activeElement!==trigger)hide()},150)};
  trigger.addEventListener('pointerenter',enter);trigger.addEventListener('pointerleave',leave);
  panel.addEventListener('pointerenter',()=>clearTimeout(timer));panel.addEventListener('pointerleave',leave);
  trigger.addEventListener('focus',enter);trigger.addEventListener('blur',leave);
  trigger.addEventListener('click',()=>clearTimeout(timer));
  mount.addEventListener('keydown',event=>{if(event.key==='Escape')hide()});
  panel.addEventListener('focusout',leave);
  trigger.addEventListener('keydown',event=>{if(event.key==='ArrowDown'&&floating.isOpen()){event.preventDefault();(panel.querySelector('a,button,[tabindex="0"]')||panel).focus()}});
  return {...floating,hide};
}

/* Geist Select：站内每一个下拉都是它，没有一个走浏览器自带的 select 控件。

   原生下拉的弹出层由操作系统画，不认站内色板：浅色主题下它要么跟着系统换成另一套灰白，
   要么只能用 `color-scheme` 整个按回深色——设置面板里那七个此前就是被按成深色的，
   白底页面上七块黑。2026-09-04 实测 vercel.com 后台：整站没有一个原生下拉，触发器是
   button，面板是自绘 listbox，面板底色就是页面底色（浅色下纯白 --ds-background-100），
   行高 36px、圆角 6px、行内边距 0 8px，悬停与选中都是 5% 中性填充，选中项没有勾。Peach
   的行高走站内已有的 --control-h（38px），面板与定位复用 .popmenu 和 wireAnchoredMenu。

   选中态只有填充，行内也就没有一枚勾要占位：行首腾出来的那一格正好让每一项的站标和
   触发器里那一枚落在同一列上。面板的左内边距（.popmenu 的 6px 加行的 6px）按触发器的
   12px 凑，两处图标于是对齐到一像素。

   `value`、`disabled` 和 `change` 三样按原生 select 的写法留在根元素上：调用方读写它跟
   读写原生下拉一样，换掉的只是画法。 */
export function selectOptionIconHtml(mark){
  return !mark?'':mark.startsWith('data:image/png;base64,')
    ?`<img class="gselectmark" src="${esc(mark)}" alt="" width="16" height="16">`:icon(mark,'gselectmark');
}
export function selectFieldHtml(options,current,{label='',attr='',className=''}={}){
  const chosen=options.find(([value])=>String(value)===String(current))||options[0]||['',''];
  const content=([,text,mark])=>`${selectOptionIconHtml(mark)}${esc(text)}`;
  const rows=options.map(([value,text,mark])=>
    `<button type="button" role="option" data-select-option="${esc(value)}"
      aria-selected="${String(value)===String(chosen[0])}" tabindex="-1"><span data-select-content>${content([value,text,mark])}</span></button>`).join('');
  return `<div class="gselect${className?` ${esc(className)}`:''}" ${attr}>
    <button type="button" class="gselectfield" data-select-trigger aria-haspopup="listbox"
      aria-expanded="false" aria-label="${esc(label)}"><span data-select-label>${content(chosen)}</span>${icon('chevron-down')}</button>
    <div class="popmenu gselectmenu" role="listbox" aria-label="${esc(label)}" popover="manual" data-select-menu hidden>${rows}</div></div>`;
}

/** 接上 selectFieldHtml 画出来的一个下拉；返回的就是根元素，带 value / disabled。 */
export function wireSelectField(root){
  const trigger=root.querySelector('[data-select-trigger]');
  const menu=root.querySelector('[data-select-menu]'),label=root.querySelector('[data-select-label]');
  const options=()=>[...menu.querySelectorAll('[data-select-option]')];
  const current=()=>menu.querySelector('[aria-selected="true"]');
  /* 面板至少和触发器一样宽。菜单是 fixed 的，宽度不会自己跟着触发器走，而一个比触发器
     还窄的面板看着不像同一个控件。这条要接在 wireAnchoredMenu 之前：它按当前宽度定位。 */
  trigger.addEventListener('click',()=>{
    const width=`${trigger.getBoundingClientRect().width}px`;
    menu.style.minWidth=width;
    if(root.hasAttribute('data-fixed-width'))menu.style.width=width;
  });
  const anchored=wireAnchoredMenu(root,trigger,menu);
  trigger.addEventListener('click',()=>{if(anchored.isOpen())current()?.focus()});
  const choose=value=>{
    const picked=options().find(option=>option.dataset.selectOption===String(value));
    if(!picked)return;
    options().forEach(option=>{
      option.setAttribute('aria-selected',String(option===picked));option.tabIndex=option===picked?0:-1});
    label.innerHTML=picked.querySelector('[data-select-content]').innerHTML;
  };
  options().forEach(option=>{
    option.onclick=()=>{
      const changed=option.getAttribute('aria-selected')!=='true';
      choose(option.dataset.selectOption);anchored.setOpen(false);trigger.focus();
      if(changed)root.dispatchEvent(new Event('change',{bubbles:true}));
    };
    option.onkeydown=event=>{
      if(event.key!=='ArrowDown'&&event.key!=='ArrowUp')return;
      event.preventDefault();
      const all=options(),at=all.indexOf(option);
      all[(at+(event.key==='ArrowDown'?1:-1)+all.length)%all.length].focus();
    };
  });
  if(current())current().tabIndex=0;
  Object.defineProperty(root,'value',{configurable:true,
    get:()=>current()?.dataset.selectOption??'',set:value=>choose(value)});
  Object.defineProperty(root,'disabled',{configurable:true,
    get:()=>trigger.disabled,set:value=>{trigger.disabled=!!value;if(value)anchored.setOpen(false)}});
  return root;
}

/* 拖动排序：一列带 key 的行，拖到哪一行的上半截或下半截就插到那里。

   站内此前有两份几乎一样的实现（侧栏顺序、导航按钮），第三处再抄一遍，落点判据、
   拖动中的减淡和那条插入线就会各演化一份。这里只收「一列行」这一种：拖动中的行加
   `dragging`，落点行加 `drop-before` / `drop-after`，样式由调用方那一侧的类名给。

   `onMove(key,target,after)` 拿到的是两个 key 和一个方位，重排由调用方自己做——
   顺序存在哪、存完刷什么，各处本来就不一样。 */
export function wireDragReorder(root,{selector,attribute,onMove}={}){
  const rows=()=>[...root.querySelectorAll(selector)];
  const clear=()=>rows().forEach(row=>row.classList.remove('dragging','drop-before','drop-after'));
  let dragging=null;
  rows().forEach(row=>{
    const key=row.getAttribute(attribute);
    row.draggable=true;
    row.addEventListener('dragstart',event=>{
      dragging=key;row.classList.add('dragging');
      event.dataTransfer.effectAllowed='move';
      // 不写 dataTransfer 的话 Firefox 根本不认这是一次拖动；首页那一项的 key 是空串，
      // 空串等于没写，所以给它一个占位。落点判据只看 key 本身，不看这里写的字。
      event.dataTransfer.setData('text/plain',key||'peach-row');
    });
    row.addEventListener('dragover',event=>{
      if(dragging===null||dragging===key)return;
      event.preventDefault();event.dataTransfer.dropEffect='move';
      const after=event.clientY>row.getBoundingClientRect().top+row.offsetHeight/2;
      rows().forEach(item=>item.classList.remove('drop-before','drop-after'));
      row.classList.add(after?'drop-after':'drop-before');
    });
    row.addEventListener('drop',event=>{
      event.preventDefault();
      const after=row.classList.contains('drop-after'),from=dragging;
      dragging=null;clear();
      if(from!==null&&from!==key)onMove(from,key,after);
    });
    row.addEventListener('dragend',()=>{dragging=null;clear()});
  });
}

/* Geist Modal 的另一种正文：要填的一份表单，而不是一句待确认的话。

   壳、遮罩、焦点陷阱、Escape 和关掉后把焦点还给触发钮全部来自 confirmModal 用的那身
   `.geist-modal`，两者的差别只有正文和主按钮做什么。所以弹层的几何只有一处：标题
   20px/26px 的 h3、正文 20px 内边距、操作条粘在底两端对齐、主按钮在右下角。

   返回值里的 `dialog` 交给调用方接自己的行事件，`done` 在弹层关掉时兑现。 */
let formModalSeq=0;
export function formModal({title,description='',body='',confirmLabel,cancelLabel='取消',
                           onConfirm=null,confirmDisabled=false}={}){
  const trigger=document.activeElement;
  const dialog=document.createElement('dialog');
  dialog.className='geist-modal';
  const titleId=`geist-form-title-${++formModalSeq}`;
  dialog.setAttribute('aria-labelledby',titleId);
  dialog.innerHTML=`<form class="geist-modal-form" novalidate>
      <div class="geist-modal-body"><h3 id="${titleId}"></h3>${description?'<p></p>':''}
        <div class="geist-modal-fields">${body}</div><div data-modal-error></div></div>
      <footer class="geist-modal-footer">
        <div><button type="button" class="geist-button" data-modal-cancel></button></div>
        <div><button type="submit" class="geist-button primary" data-modal-confirm></button></div>
      </footer></form>`;
  dialog.querySelector('h3').textContent=title;
  if(description)dialog.querySelector('.geist-modal-body p').textContent=description;
  const cancel=dialog.querySelector('[data-modal-cancel]');
  const accept=dialog.querySelector('[data-modal-confirm]');
  const failure=dialog.querySelector('[data-modal-error]');
  cancel.textContent=cancelLabel;
  accept.textContent=confirmLabel;
  accept.disabled=!!confirmDisabled;
  document.body.append(dialog);
  let settled=null,busy=false;
  const done=new Promise(resolve=>dialog.addEventListener('close',()=>{
    dialog.remove();
    if(trigger instanceof HTMLElement&&trigger.isConnected)trigger.focus();
    resolve(settled||{confirmed:false});
  },{once:true}));
  cancel.onclick=()=>{if(!busy)dialog.close()};
  dialog.addEventListener('cancel',event=>{if(busy)event.preventDefault()});
  // 遮罩上的点击落在 <dialog> 自己身上；这里没有不可逆的动作，允许点外面关掉。
  dialog.addEventListener('click',event=>{if(event.target===dialog&&!busy)dialog.close()});
  dialog.querySelector('form').onsubmit=async event=>{
    event.preventDefault();
    if(busy||accept.disabled)return;
    if(!onConfirm){settled={confirmed:true};dialog.close();return}
    failure.innerHTML='';busy=true;setActionBusy(accept);
    try{
      settled={confirmed:true,result:await onConfirm()};
      dialog.close();
    }catch(error){
      failure.innerHTML=noteHtml(error.message||'操作未完成',{variant:'error'});
      setActionBusy(accept,false);
    }finally{busy=false}
  };
  dialog.showModal();
  playUiSound('pop');
  (dialog.querySelector('.geist-modal-fields input:not([type="checkbox"])')||accept).focus();
  return {dialog,confirmButton:accept,done,close:()=>dialog.close()};
}

/* Geist Modal：一次写操作落库前的确认。

   实测 https://vercel.com/geist/modal（2026-09-04）：卡片 540px 宽、12px 圆角、窄屏两侧
   各留 10px，正文 20px 内边距、14px/20px，标题是 20px/26px 的 600 字重 h3，底部操作条
   12px 内边距、粘在底、两端对齐，按钮 32px 高、6px 圆角、14px/500，遮罩纯黑不带模糊。
   标题写成陈述句而不是问句；主按钮是与标题同一个动词的「动词+名词」，取消键就写「取消」；
   成功后的 Toast 与主按钮共用那个动词。

   用原生 <dialog> 承载：焦点陷阱、Escape、背景 inert 和关掉后把焦点还给触发钮都由它给，
   自己搭一遍只会少掉其中一两样。onConfirm 失败时弹层不关，原因留在原位等重试。 */
let modalSeq=0;
export function confirmModal({title,body,confirmLabel,cancelLabel='取消',onConfirm=null,danger=false}={}){
  const trigger=document.activeElement;
  const dialog=document.createElement('dialog');
  dialog.className='geist-modal';
  const titleId=`geist-modal-title-${++modalSeq}`;
  dialog.setAttribute('aria-labelledby',titleId);
  dialog.innerHTML=`<div class="geist-modal-body">
      <h3 id="${titleId}"></h3><p></p><div data-modal-error></div></div>
    <footer class="geist-modal-footer">
      <div><button type="button" class="geist-button" data-modal-cancel></button></div>
      <div><button type="button" class="geist-button primary" data-modal-confirm></button></div>
    </footer>`;
  dialog.querySelector('h3').textContent=title;
  dialog.querySelector('.geist-modal-body p').textContent=body;
  const cancel=dialog.querySelector('[data-modal-cancel]');
  const accept=dialog.querySelector('[data-modal-confirm]');
  if(danger){accept.classList.remove('primary');accept.classList.add('danger')}
  const failure=dialog.querySelector('[data-modal-error]');
  cancel.textContent=cancelLabel;
  accept.textContent=confirmLabel;
  document.body.append(dialog);
  return new Promise(resolve=>{
    let settled=null;
    let busy=false;
    dialog.addEventListener('close',()=>{
      dialog.remove();
      if(trigger instanceof HTMLElement&&trigger.isConnected)trigger.focus();
      resolve(settled||{confirmed:false});
    },{once:true});
    cancel.onclick=()=>{if(!busy)dialog.close()};
    dialog.addEventListener('cancel',event=>{if(busy)event.preventDefault()});
    /* 遮罩上的点击落在 <dialog> 自己身上，卡片里的落在子元素上。这个动作可撤销，
       按 Geist 的判据允许点外面关掉。 */
    dialog.addEventListener('click',event=>{if(event.target===dialog&&!busy&&!danger)dialog.close()});
    accept.onclick=async()=>{
      if(busy)return;
      if(!onConfirm){settled={confirmed:true};dialog.close();return}
      failure.innerHTML='';
      busy=true;
      setActionBusy(accept);
      try{
        settled={confirmed:true,result:await onConfirm()};
        dialog.close();
      }catch(error){
        failure.innerHTML=noteHtml(error.message||'操作未完成',{variant:'error'});
        setActionBusy(accept,false);
      }finally{busy=false}
    };
    dialog.showModal();
    playUiSound('pop');
    (danger?cancel:accept).focus();
  });
}

/* ── 安装后教程的状态 ──
   教程本身还画在遗留层（迁往 React 的待办在 `docs/PRODUCT_BACKLOG.md`），但「做到哪了」
   不属于渲染：清单做完这件事跟着账本走（`/api/settings` 的 `postSetupTutorialDone`），
   换台设备打开不会又被教一遍；折叠和逐项跳过是当下这块屏幕的摆法，留在本地。
   三个键、签名和请求代际都收在这里，装配那一侧只管把它们接到 DOM 上。 */
export const POST_SETUP_TUTORIAL_KEY='peach.post-setup-tutorial.v1';
export const POST_SETUP_TUTORIAL_COLLAPSED_KEY='peach.post-setup-tutorial-collapsed.v1';
export const POST_SETUP_TUTORIAL_SKIPPED_KEY='peach.post-setup-tutorial-skipped.v1';

const readStored=key=>{try{return localStorage.getItem(key)}catch(_error){return null}};
const writeStored=(key,value)=>{try{localStorage.setItem(key,value)}catch(_error){}};

export const postSetupTutorialMarker=()=>readStored(POST_SETUP_TUTORIAL_KEY)||'';
export const setPostSetupTutorialMarker=value=>writeStored(POST_SETUP_TUTORIAL_KEY,value);
export const postSetupTutorialCollapsed=()=>readStored(POST_SETUP_TUTORIAL_COLLAPSED_KEY)==='1';
export const setPostSetupTutorialCollapsed=value=>
  writeStored(POST_SETUP_TUTORIAL_COLLAPSED_KEY,value?'1':'0');
export const postSetupTutorialSkipped=()=>{
  try{
    const parsed=JSON.parse(readStored(POST_SETUP_TUTORIAL_SKIPPED_KEY)||'[]');
    return new Set(Array.isArray(parsed)?parsed.filter(key=>typeof key==='string'):[]);
  }catch(_error){return new Set()}
};
export const setPostSetupTutorialSkipped=values=>
  writeStored(POST_SETUP_TUTORIAL_SKIPPED_KEY,JSON.stringify([...values]));

/* 重绘的判据：清单里每一项的文字、目标和完成与否。只要这一串没变，页面上那张卡就
   还是对的，重画一次只会打断正在读它的人和刚点开的折叠。 */
export const postSetupTutorialSignature=tasks=>JSON.stringify(
  tasks.map(task=>[task.key,task.done,task.label,task.description,task.href]));

/* 请求代际：教程跟着每次路由切换重新取数，慢的那一发回来时页面可能已经换了。 */
let postSetupTutorialRequest=0;
export const nextPostSetupTutorialRequest=()=>++postSetupTutorialRequest;
export const isCurrentPostSetupTutorialRequest=request=>request===postSetupTutorialRequest;

/** 重新打开教程：清掉跳过与折叠，本地标记回到未完成，由调用方负责服务端那一半。 */
export function resetPostSetupTutorialState(){
  setPostSetupTutorialSkipped(new Set());
  setPostSetupTutorialCollapsed(false);
  setPostSetupTutorialMarker('pending');
}
