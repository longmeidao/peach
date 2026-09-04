import { esc, icon } from './core.js';

const NOTE_VARIANTS=new Set(['secondary','warning','error','success']);

/** Inline, persistent context beside the field/card/section it describes. */
export function noteHtml(message,{variant='secondary',label='',className=''}={}){
  const kind=NOTE_VARIANTS.has(variant)?variant:'secondary';
  const symbol=kind==='secondary'?'info':kind==='success'?'check':'alert';
  const role=kind==='error'?' role="alert"':' role="note"';
  return `<div class="geist-note geist-note-${kind}${className?` ${esc(className)}`:''}"${role}>
    ${icon(symbol)}<p>${label?`<b>${esc(label)}</b>`:''}<span>${esc(message)}</span></p></div>`;
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
export function progressHtml(label,value,max=100){
  const ceiling=Math.max(0,Number(max)||0);
  const current=Math.max(0,Math.min(Number(value)||0,ceiling));
  const percent=ceiling?current/ceiling*100:0;
  return `<div class="geist-progress" role="progressbar" aria-label="${esc(label)}"
    aria-valuemin="0" aria-valuemax="${ceiling}" aria-valuenow="${current}"
    style="--progress-value:${percent}%"><i></i></div>`;
}

/** Geist Spinner: immediate feedback for a user-triggered action. */
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
export function skeletonHtml(label='正在读取内容',{className='',variant='panel',count=6,fill=true}={}){
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
    <div aria-hidden="true">${body}</div></div>`;
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

/** 一行横向骨架：逐枚追加到溢出容器右缘为止。上限只是死循环的护栏。 */
export function fillSkeletonTier(row,kind){
  const slot=SKELETON_SLOT[kind],widths=SKELETON_SLOT_WIDTHS[kind];
  if(!slot||!row)return;
  for(let i=0;i<64;i++){
    row.insertAdjacentHTML('beforeend',slot(widths[i%widths.length]));
    if(row.scrollWidth>row.clientWidth)break;
  }
}

/** 骨架落进 DOM 之后按实际尺寸补齐：横向一行铺满，卡片网格补到整行且盖住视口余量。 */
export function fitSkeleton(root){
  if(!root)return;
  const scoped=selector=>[...(root.matches?.(selector)?[root]:[]),...root.querySelectorAll(selector)];
  for(const row of scoped('[data-skeleton-tier]'))fillSkeletonTier(row,row.dataset.skeletonTier);
  for(const grid of scoped('.skeletonpanel[data-fill]>div')){
    const first=grid.firstElementChild,style=getComputedStyle(grid);
    /* 横排的推荐行不是网格，列数无从谈起，按整行补会把它裁成一张。 */
    if(!first||style.display!=='grid')continue;
    const columns=style.gridTemplateColumns.split(' ').filter(Boolean).length;
    const rowGap=parseFloat(style.rowGap)||0,cardHeight=first.getBoundingClientRect().height;
    if(!columns||!cardHeight)continue;
    /* 骨架说的是「这块地方等下会被填满」，所以铺到视口下沿；四行是护栏，
       再多也是一屏之外看不见的占位，白占动画。 */
    const room=window.innerHeight-grid.getBoundingClientRect().top;
    const rows=Math.max(1,Math.min(4,Math.ceil((room+rowGap)/(cardHeight+rowGap))));
    const want=columns*rows;
    while(grid.children.length>want)grid.lastElementChild.remove();
    while(grid.children.length<want)grid.appendChild(first.cloneNode(true));
  }
}

/** Shared video/image view buttons for entity profiles and the follow feed. */
export function mediaViewButtonsHtml({
  active='videos',videoValue='videos',imageValue='images',videoLabel='视频',imageLabel='图片',
  videoCount=null,imageCount=null,className='',
}={}){
  const control=(value,label,count,symbol,kind)=>{
    const text=count===null||count===undefined
      ?label:`${label} ${Math.max(0,Number(count)||0).toLocaleString()}`;
    return `<button class="mediaviewbutton" type="button" data-media-view="${esc(value)}"
      data-media-icon="${kind}" aria-pressed="${active===value}" aria-label="${esc(text)}"
      title="${esc(text)}">${icon(symbol)}</button>`;
  };
  return `<div class="mediaviewbuttons${className?` ${esc(className)}`:''}" role="group" aria-label="媒体类型">
    ${control(videoValue,videoLabel,videoCount,'play','video')}
    ${control(imageValue,imageLabel,imageCount,'pics','image')}</div>`;
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

/**
 * Geist Switch：2–3 个互斥视图用共享 name 的一组 radio，不用 Toggle。
 *
 * JAV 卡片版式和关注列表版式是同一个控件——只有 name、选项和当前值不同，所以模板
 * 与 `.iconswitch` 样式共用一份；调用方各自的摆放位置仍由自己的类负责。
 */
export function iconSwitchHtml(name,legend,options,current,{attr='',className=''}={}){
  const items=options.map(([value,label,symbol])=>
    `<label title="${esc(label)}"><input type="radio" name="${esc(name)}" value="${esc(value)}" ${attr}
      ${value===current?'checked':''}><span aria-hidden="true">${icon(symbol)}</span><span class="sr-only">${esc(label)}</span></label>`).join('');
  return `<fieldset class="iconswitch${className?` ${esc(className)}`:''}"><legend class="sr-only">${esc(legend)}</legend>${items}</fieldset>`;
}

/** 把一组 iconSwitchHtml 画出来的 radio 接到 apply(value) 上。 */
export function wireIconSwitch(root,attr,apply){
  root?.querySelectorAll(`[${attr}]`).forEach(input=>{
    input.onchange=()=>{if(input.checked)apply(input.value)};
  });
}

/**
 * 共用勾选框。原生 checkbox 在暗色下由浏览器自绘，跟站内别的控件不是同一套语言；
 * `accent-color` 也只能改选中色，未选中态连悬停反馈都给不了。所以自绘一份，关注
 * 列表、来源筛选、候选清单、标签匹配和设置项共用它。
 */
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
export function wireCollapse(root,selector,idPrefix){
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
    const summary=details.querySelector('summary');
    let expanded=details.open,transitionRun=0;
    body.id=`${idPrefix}-${index}`;
    body.inert=!expanded;
    summary.setAttribute('aria-controls',body.id);
    summary.setAttribute('aria-expanded',String(expanded));
    const settle=(run,fn)=>{
      let done=false,timer;
      const finish=e=>{
        if(e&&e.propertyName!=='height')return;
        if(done)return;done=true;
        body.removeEventListener('transitionend',finish);clearTimeout(timer);
        if(run===transitionRun)fn();
      };
      body.addEventListener('transitionend',finish);
      timer=setTimeout(finish,260);
    };
    summary.addEventListener('click',event=>{
      event.preventDefault();
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
}

/* 锚定在触发钮上的菜单：无展开动画，固定在视口内，内容在菜单内滚动。

   Vercel 项目页的 Filter and Sort 菜单没有展开动画。优先从触发钮右缘向左展开，
   下方放不下时改到上方。全站的锚定菜单共用这一份定位与开关：菜单在视口边缘的表现
   最容易各写各的，同一语义留两份实现就只会有一份被修。 */
let openedMenu=null;
if(!globalThis.__peachMenuCloser){
  globalThis.__peachMenuCloser=true;
  document.addEventListener('click',event=>{
    if(openedMenu&&!openedMenu.mount.contains(event.target))openedMenu.setOpen(false)},true);
}
export function closeAnchoredMenu(){if(openedMenu)openedMenu.setOpen(false)}
/* 可用的视口上沿是固定顶栏的下缘。顶栏在每一页都盖着最上面那一条，菜单顶到 8px
   会被它压掉半截，而且看不出是被压住的——只是第一项凭空不见了。 */
const viewportTop=()=>8+(parseFloat(getComputedStyle(document.documentElement)
  .getPropertyValue('--topH'))||0);
export function wireAnchoredMenu(mount,toggle,menu){
  const position=()=>{
    const anchor=toggle.getBoundingClientRect(),width=menu.getBoundingClientRect().width;
    const top=viewportTop(),under=innerHeight-8-anchor.bottom-8,over=anchor.top-8-top;
    /* 下方放不下就改到上方；两侧都放不下时取宽的那一侧，并把菜单压到那一侧的高度，
       内容在菜单内滚。不压高度的话它会横跨触发钮盖住自己，点开之后连改的是哪一个
       名字都看不见。 */
    const downward=under>=menu.scrollHeight||under>=over;
    const height=Math.min(menu.scrollHeight,Math.max(downward?under:over,0));
    menu.style.maxHeight=height+'px';
    menu.style.left=Math.max(8,Math.min(anchor.right-width,innerWidth-width-8))+'px';
    menu.style.top=(downward?anchor.bottom+8:anchor.top-8-height)+'px'};
  const closeFromViewport=()=>setOpen(false);
  const setOpen=open=>{
    if(open){
      menu.hidden=false;position();
      window.addEventListener('resize',position);
      window.addEventListener('scroll',closeFromViewport,{capture:true,passive:true});
    }else{
      menu.hidden=true;menu.style.left='';menu.style.top='';menu.style.maxHeight='';
      window.removeEventListener('resize',position);
      window.removeEventListener('scroll',closeFromViewport,true);
    }
    toggle.setAttribute('aria-expanded',String(open));
    openedMenu=open?{mount,setOpen}:(openedMenu&&openedMenu.mount===mount?null:openedMenu)};
  toggle.addEventListener('click',event=>{event.stopPropagation();setOpen(menu.hidden)});
  mount.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&!menu.hidden){setOpen(false);toggle.focus()}});
  return {setOpen,isOpen:()=>!menu.hidden};
}
