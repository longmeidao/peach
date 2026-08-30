/* Geist MiddleTruncate 的 Peach 原生适配层。

   Peach 没有 React 或构建步骤，因此这里只复用已验证的行为：按容器宽度保留首尾、
   使用单个省略号、宽度变化后重算、复制与无障碍名称仍提供完整原文。调用方只需给
   文件名、路径、URL 或 ID 加 data-middle-truncate；标题和说明继续使用末尾省略。 */

const ELLIPSIS='…';
const segmenter=typeof Intl.Segmenter==='function'
  ? new Intl.Segmenter(undefined,{granularity:'grapheme'})
  : null;
const states=new WeakMap();
const observed=new WeakSet();
let resizeObserver=null;

const graphemes=value=>segmenter
  ? [...segmenter.segment(String(value??''))].map(part=>part.segment)
  : Array.from(String(value??''));

/* 纯算法边界单独导出，Node 可直接实测，不需要伪造 DOM。fits(candidate) 由浏览器
   测量层注入；二分寻找能放下的最长首尾组合，奇数位优先保留开头。 */
function middleTruncateText(value,fits){
  const parts=graphemes(value);
  if(!parts.length||fits(value))return String(value??'');
  let low=0,high=Math.max(0,parts.length-1),best=ELLIPSIS;
  while(low<=high){
    const kept=(low+high)>>1;
    const head=Math.ceil(kept/2),tail=Math.floor(kept/2);
    const candidate=parts.slice(0,head).join('')+ELLIPSIS+(tail?parts.slice(-tail).join(''):'');
    if(fits(candidate)){best=candidate;low=kept+1}else high=kept-1;
  }
  return best;
}

const measuredWidth=(element,value)=>{
  const style=getComputedStyle(element);
  const canvas=measuredWidth.canvas||(measuredWidth.canvas=document.createElement('canvas'));
  const context=canvas.getContext('2d');
  if(!context)return Number.POSITIVE_INFINITY;
  context.font=style.font;
  let width=context.measureText(value).width;
  const letterSpacing=parseFloat(style.letterSpacing);
  if(Number.isFinite(letterSpacing))width+=Math.max(0,graphemes(value).length-1)*letterSpacing;
  const wordSpacing=parseFloat(style.wordSpacing);
  if(Number.isFinite(wordSpacing))width+=(value.match(/\s/g)||[]).length*wordSpacing;
  return width;
};

const paint=element=>{
  const state=states.get(element);if(!state||!element.isConnected)return;
  const available=element.clientWidth;
  const rendered=available>0
    ? middleTruncateText(state.full,candidate=>measuredWidth(element,candidate)<=available)
    : state.full;
  state.rendered=rendered;
  if(element.textContent!==rendered)element.textContent=rendered;
  const truncated=rendered!==state.full;
  element.classList.toggle('middle-truncated',truncated);
  element.setAttribute('aria-label',state.full);
  if(!element.hasAttribute('title')||element.dataset.middleTitle==='true'){
    element.title=state.full;element.dataset.middleTitle='true';
  }
};

const schedule=element=>{
  const state=states.get(element);if(!state||state.raf)return;
  state.raf=requestAnimationFrame(()=>{state.raf=0;paint(element)});
};

const bind=element=>{
  if(!(element instanceof HTMLElement))return;
  if(!states.has(element))states.set(element,{full:element.textContent||'',rendered:element.textContent||'',raf:0});
  if(!observed.has(element)){
    observed.add(element);
    resizeObserver?.observe(element);
  }
  schedule(element);
};

const scan=node=>{
  if(node.nodeType!==Node.ELEMENT_NODE)return;
  const element=/** @type {Element} */(node);
  if(element.matches('[data-middle-truncate]'))bind(element);
  element.querySelectorAll('[data-middle-truncate]').forEach(bind);
};

function initMiddleTruncate(root=document){
  resizeObserver=new ResizeObserver(entries=>entries.forEach(entry=>schedule(entry.target)));
  scan(root.documentElement||root);
  const mutations=new MutationObserver(records=>records.forEach(record=>{
    record.addedNodes.forEach(scan);
    const element=record.target.nodeType===Node.TEXT_NODE?record.target.parentElement:record.target;
    const target=element?.closest?.('[data-middle-truncate]');
    if(!target)return;
    const state=states.get(target);
    if(state&&target.textContent!==state.rendered){
      state.full=target.textContent||'';
      if(target.dataset.middleTitle==='true')target.removeAttribute('title');
      schedule(target);
    }
  }));
  mutations.observe(root.body||root,{childList:true,characterData:true,subtree:true});
  document.fonts?.ready?.then(()=>root.querySelectorAll('[data-middle-truncate]').forEach(schedule));
  root.addEventListener('copy',event=>{
    const selection=document.getSelection();
    if(!selection||selection.isCollapsed)return;
    const anchor=selection.anchorNode?.nodeType===Node.ELEMENT_NODE?selection.anchorNode:selection.anchorNode?.parentElement;
    const target=anchor?.closest?.('[data-middle-truncate]');
    const state=target&&states.get(target);
    if(!state||!target.contains(selection.focusNode)||!event.clipboardData)return;
    event.clipboardData.setData('text/plain',state.full);event.preventDefault();
  });
}

export { initMiddleTruncate, middleTruncateText };
