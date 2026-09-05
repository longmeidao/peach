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
 * 覆盖式滚动条：滑块浮在内容上，一列宽度都不占。
 *
 * 已有的 `.geist-scroller` 解决的是另一半问题——它用两端渐隐说明「还能往下」，
 * 但没有滑块，读不出这一列有多长、自己停在哪儿，而且要求内容套进它自己的包装层。
 * 这里只往既有滚动容器的父元素上挂一条轨道，不动内容结构，两者可以叠加使用。
 *
 * 容器负责关掉原生滚动条并保证父元素是定位祖先；轨道必须是容器的兄弟，
 * 跟着内容一起滚的轨道等于没有轨道。整页那一条是唯一的例外：`html` 没有元素父级，
 * 轨道挂进 body 并由 `.page` 改成 fixed，位置照样只认视口右边。
 * 几何按 2026-09-05 实测 vercel.com 侧栏：
 * 滑块高 = 可视高 / 内容高 × 轨道高，位移 = 滚动进度 × (轨道高 − 滑块高)。
 * 返回一个手动重算函数，给那些既不改容器尺寸也不改子树的情形（例如换字体后重排）。
 */
export function attachOverlayScrollbar(container,{variant=''}={}){
  if(!container||container.dataset.overlayScrollbar)return null;
  const root=container===document.documentElement;
  const host=root?document.body:container.parentElement;
  if(!host)return null;
  container.dataset.overlayScrollbar='true';
  const track=document.createElement('div');
  track.className=`ovtrack${variant?` ${variant}`:''}`;
  const thumb=document.createElement('div');
  thumb.className='ovthumb';
  track.append(thumb);
  host.append(track);
  const sync=()=>{
    const range=container.scrollHeight-container.clientHeight;
    if(range<=1){track.hidden=true;return}
    // 先显再量：藏起来的轨道高度是 0，拿它当「量不到」会把自己永久锁在隐藏态。
    track.hidden=false;
    const trackH=track.clientHeight;
    if(!trackH)return;
    // 短到抓不住的滑块等于没有滑块：内容特别长时给它一个下限，代价是滑块位置与
    // 滚动进度不再严格线性，但可拖动比可换算重要。
    const thumbH=Math.max(24,Math.min(trackH,container.clientHeight/container.scrollHeight*trackH));
    const travel=trackH-thumbH;
    thumb.style.height=`${thumbH}px`;
    thumb.style.transform=`translateY(${travel>0?container.scrollTop/range*travel:0}px)`;
  };
  (root?document:container).addEventListener('scroll',sync,{passive:true});
  new ResizeObserver(sync).observe(container);
  // 内容长短变了但容器盒子没变（抽屉重建、分区展开），容器自己的 ResizeObserver 一声不响。
  // 整页那一条改看 body：它的高度就是内容高度，而在 documentElement 上挂 subtree 的
  // MutationObserver 等于每渲染一张卡都强制一次重排。
  if(root)new ResizeObserver(sync).observe(document.body);
  else new MutationObserver(sync).observe(container,{childList:true,subtree:true});
  track.addEventListener('pointerdown',event=>{
    const trackRect=track.getBoundingClientRect(),thumbRect=thumb.getBoundingClientRect();
    const travel=trackRect.height-thumbRect.height,range=container.scrollHeight-container.clientHeight;
    if(travel<=0||range<=0)return;
    // 按在滑块上就保持按住的那一点，按在轨道空白处则把滑块中心挪过来。
    const grab=event.clientY>=thumbRect.top&&event.clientY<=thumbRect.bottom
      ?event.clientY-thumbRect.top:thumbRect.height/2;
    const to=clientY=>{container.scrollTop=Math.max(0,Math.min(range,
      (clientY-trackRect.top-grab)/travel*range))};
    const stop=()=>{track.classList.remove('dragging');
      track.removeEventListener('pointermove',move);track.removeEventListener('pointerup',stop);
      track.removeEventListener('pointercancel',stop)};
    const move=moved=>to(moved.clientY);
    track.classList.add('dragging');
    track.setPointerCapture(event.pointerId);
    track.addEventListener('pointermove',move);
    track.addEventListener('pointerup',stop);
    track.addEventListener('pointercancel',stop);
    to(event.clientY);
    event.preventDefault();
  });
  sync();
  return sync;
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
  const setOpen=open=>{
    if(open){
      menu.hidden=false;if(inTopLayer)menu.showPopover();position();
      window.addEventListener('resize',position);
      window.addEventListener('scroll',closeFromViewport,{capture:true,passive:true});
    }else{
      menu.hidden=true;menu.style.left='';menu.style.top='';menu.style.maxHeight='';
      if(inTopLayer&&menu.matches(':popover-open'))menu.hidePopover();
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

/* Geist Select：站内每一个下拉都是它，没有一个走浏览器自带的 select 控件。

   原生下拉的弹出层由操作系统画，不认站内色板：浅色主题下它要么跟着系统换成另一套灰白，
   要么只能用 `color-scheme` 整个按回深色——设置面板里那七个此前就是被按成深色的，
   白底页面上七块黑。2026-09-04 实测 vercel.com 后台：整站没有一个原生下拉，触发器是
   button，面板是自绘 listbox，面板底色就是页面底色（浅色下纯白 --ds-background-100），
   行高 36px、圆角 6px、行内边距 0 8px，悬停与选中都是 5% 中性填充。Peach 的行高走站内
   已有的 --control-h（38px），面板与定位复用 .popmenu 和 wireAnchoredMenu。

   `value`、`disabled` 和 `change` 三样按原生 select 的写法留在根元素上：调用方读写它跟
   读写原生下拉一样，换掉的只是画法。 */
export function selectFieldHtml(options,current,{label='',attr='',className=''}={}){
  const chosen=options.find(([value])=>String(value)===String(current))||options[0]||['',''];
  const rows=options.map(([value,text])=>
    `<button type="button" role="option" data-select-option="${esc(value)}"
      aria-selected="${String(value)===String(chosen[0])}" tabindex="-1">${icon('check')}<span>${esc(text)}</span></button>`).join('');
  return `<div class="gselect${className?` ${esc(className)}`:''}" ${attr}>
    <button type="button" class="gselectfield" data-select-trigger aria-haspopup="listbox"
      aria-expanded="false" aria-label="${esc(label)}"><span data-select-label>${esc(chosen[1])}</span>${icon('chevron-down')}</button>
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
  trigger.addEventListener('click',()=>{menu.style.minWidth=`${trigger.getBoundingClientRect().width}px`});
  const anchored=wireAnchoredMenu(root,trigger,menu);
  trigger.addEventListener('click',()=>{if(!menu.hidden)current()?.focus()});
  const choose=value=>{
    const picked=options().find(option=>option.dataset.selectOption===String(value));
    if(!picked)return;
    options().forEach(option=>{
      option.setAttribute('aria-selected',String(option===picked));option.tabIndex=option===picked?0:-1});
    label.textContent=picked.querySelector('span').textContent;
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

/* Geist Modal：一次写操作落库前的确认。

   实测 https://vercel.com/geist/modal（2026-09-04）：卡片 540px 宽、12px 圆角、窄屏两侧
   各留 10px，正文 20px 内边距、14px/20px，标题是 20px/26px 的 600 字重 h3，底部操作条
   12px 内边距、粘在底、两端对齐，按钮 32px 高、6px 圆角、14px/500，遮罩纯黑不带模糊。
   标题写成陈述句而不是问句；主按钮是与标题同一个动词的「动词+名词」，取消键就写「取消」；
   成功后的 Toast 与主按钮共用那个动词。

   用原生 <dialog> 承载：焦点陷阱、Escape、背景 inert 和关掉后把焦点还给触发钮都由它给，
   自己搭一遍只会少掉其中一两样。onConfirm 失败时弹层不关，原因留在原位等重试。 */
let modalSeq=0;
export function confirmModal({title,body,confirmLabel,cancelLabel='取消',onConfirm=null}={}){
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
  const failure=dialog.querySelector('[data-modal-error]');
  cancel.textContent=cancelLabel;
  accept.textContent=confirmLabel;
  document.body.append(dialog);
  return new Promise(resolve=>{
    let settled=null;
    dialog.addEventListener('close',()=>{
      dialog.remove();
      if(trigger instanceof HTMLElement&&trigger.isConnected)trigger.focus();
      resolve(settled||{confirmed:false});
    },{once:true});
    cancel.onclick=()=>dialog.close();
    /* 遮罩上的点击落在 <dialog> 自己身上，卡片里的落在子元素上。这个动作可撤销，
       按 Geist 的判据允许点外面关掉。 */
    dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});
    accept.onclick=async()=>{
      if(!onConfirm){settled={confirmed:true};dialog.close();return}
      failure.innerHTML='';
      setActionBusy(accept);
      try{
        settled={confirmed:true,result:await onConfirm()};
        dialog.close();
      }catch(error){
        failure.innerHTML=noteHtml(error.message||'操作未完成',{variant:'error'});
        setActionBusy(accept,false);
      }
    };
    dialog.showModal();
    accept.focus();
  });
}
