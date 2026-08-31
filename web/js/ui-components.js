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

/** Geist Loading Dots: indeterminate work continuing in the background. */
export function loadingDotsHtml(label='正在处理', {className=''}={}){
  return `<span class="geist-loading${className?` ${esc(className)}`:''}" role="status">
    <span class="geist-loading-dots" aria-hidden="true"><i></i><i></i><i></i></span>
    <span>${esc(label)}</span></span>`;
}

/** Geist Skeleton: reserve a large content region while its structure is loading. */
export function skeletonHtml(label='正在读取内容',{className='',variant='panel'}={}){
  const kind=new Set(['panel','cards']).has(variant)?variant:'panel';
  const body=kind==='cards'
    ?Array.from({length:6},()=>`<span class="skeletoncard"><i></i><b></b><em></em></span>`).join('')
    :`<span class="skeleton" style="width:38%"></span>
      <span class="skeleton" style="width:100%"></span>
      <span class="skeleton" style="width:100%"></span>
      <span class="skeleton" style="width:72%"></span>`;
  return `<div class="skeletonpanel skeleton-${kind}${className?` ${esc(className)}`:''}"
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
