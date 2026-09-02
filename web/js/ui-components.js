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
export function skeletonHtml(label='正在读取内容',{className='',variant='panel'}={}){
  const kind=new Set(['panel','cards','dashboard']).has(variant)?variant:'panel';
  const body=kind==='cards'
    ?Array.from({length:6},()=>`<span class="skeletoncard"><i></i><b></b><em></em></span>`).join('')
    :kind==='dashboard'
      ?`<span class="skeletondashhero"><i></i><b></b></span>
        <span class="skeletondashpanel"><i></i><b></b><em></em></span>
        <span class="skeletondashpanel"><i></i><b></b><em></em></span>`
    :`<span class="skeleton" style="width:38%"></span>
      <span class="skeleton" style="width:100%"></span>
      <span class="skeleton" style="width:100%"></span>
      <span class="skeleton" style="width:72%"></span>`;
  /* data-skeleton 是这张骨架的身份。深链启动先画一张、路由到位后各页再画一张，
     整页刷新就会连闪两段动画；调用方拿这个键判断「已经是同一张了」，跳过重画。 */
  return `<div class="skeletonpanel skeleton-${kind}${className?` ${esc(className)}`:''}"
    data-skeleton="${esc(kind)}${className?`/${esc(className)}`:''}"
    role="status" aria-label="${esc(label)}"><span class="sr-only">${esc(label)}</span>
    <div aria-hidden="true">${body}</div></div>`;
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
