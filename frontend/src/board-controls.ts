/** Board 控件的共享展示层；范围输入保留浏览器原生键盘语义。 */
export function syncBoardRange(input: HTMLInputElement) {
  const min=Number(input.min)||0,max=Number(input.max)||100,value=Number(input.value);
  const percent=max>min?Math.max(0,Math.min(100,(value-min)/(max-min)*100)):0;
  input.style.setProperty('--board-range-value',`${percent}%`);
  const group=input.closest('.dual-range');
  if(!group)return;
  const end=input.id==='durMax'?'max':'min';
  let tip=group.querySelector<HTMLElement>(`[data-range-end="${end}"]`);
  if(!tip){tip=document.createElement('output');tip.className='board-range-tip';tip.dataset.rangeEnd=end;tip.setAttribute('aria-hidden','true');group.append(tip)}
  tip.textContent=value>=max&&end==='max'?'不限':`${value} 分钟`;
  tip.style.left=`${percent}%`;
}

export function initBoardControls() {
  const scan=(root:ParentNode)=>root.querySelectorAll<HTMLInputElement>('input[type=range]').forEach(syncBoardRange);
  scan(document);
  const observer=new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)if(node instanceof Element){if(node.matches('input[type=range]'))syncBoardRange(node as HTMLInputElement);scan(node)}});
  observer.observe(document.body,{subtree:true,childList:true});
  document.addEventListener('input',event=>{if(event.target instanceof HTMLInputElement&&event.target.type==='range')syncBoardRange(event.target)});
  const tip=document.createElement('div');tip.className='board-tooltip';tip.id='board-control-tooltip';tip.role='tooltip';tip.hidden=true;document.body.append(tip);
  let target:HTMLElement|null=null,title='',described:string|null=null,timer:ReturnType<typeof setTimeout>|undefined;
  const hide=()=>{clearTimeout(timer);tip.hidden=true;if(target){if(!target.hasAttribute('title'))target.title=title;if(described===null)target.removeAttribute('aria-describedby');else target.setAttribute('aria-describedby',described)}target=null};
  const show=(node:EventTarget|null,delay:number)=>{
    const next=node instanceof Element?node.closest<HTMLElement>('[title]'):null;
    if(!next||next===target||next.closest('.vjs-control')||!next.title.trim())return;
    hide();target=next;title=next.title;described=next.getAttribute('aria-describedby');next.removeAttribute('title');
    timer=setTimeout(()=>{if(target!==next||!next.isConnected)return;tip.textContent=title;tip.hidden=false;
      const rect=next.getBoundingClientRect(),box=tip.getBoundingClientRect();
      tip.style.left=`${Math.max(8,Math.min(innerWidth-box.width-8,rect.left+(rect.width-box.width)/2))}px`;
      tip.style.top=`${rect.top>=box.height+16?rect.top-box.height-8:Math.min(innerHeight-box.height-8,rect.bottom+8)}px`;
      next.setAttribute('aria-describedby',[described,tip.id].filter(Boolean).join(' '));
    },delay);
  };
  document.addEventListener('pointerover',event=>show(event.target,400));
  document.addEventListener('pointerout',event=>{if(target&&!target.contains(event.relatedTarget as Node|null))hide()});
  document.addEventListener('focusin',event=>show(event.target,0));
  document.addEventListener('focusout',hide);
  document.addEventListener('keydown',event=>{if(event.key==='Escape')hide()});
  document.addEventListener('scroll',hide,true);window.addEventListener('resize',hide);
}

export function wireExpandableRanks(root:ParentNode) {
  root.querySelectorAll<HTMLElement>('.tasteranks,.insightranking').forEach((list,index)=>{
    if(list.children.length<=5||list.parentElement?.hasAttribute('data-expandable-ranks'))return;
    const outer=document.createElement('div');outer.className='board-expand-ranks';outer.dataset.expandableRanks='';list.before(outer);outer.append(list);
    list.id=list.id||`board-rank-list-${index}`;list.classList.add('board-rank-list');
    const button=document.createElement('button');button.type='button';button.className='board-rank-expand';button.setAttribute('aria-controls',list.id);button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','展开更多排名');button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-down"/></svg>';outer.append(button);
    const size=()=>{const row=list.children[4] as HTMLElement;if(!list.offsetWidth)return;outer.style.setProperty('--rank-collapsed-height',`${row.offsetTop-list.offsetTop+row.offsetHeight+20}px`);outer.style.setProperty('--rank-expanded-height',`${list.scrollHeight}px`)};
    const update=()=>{const expanded=button.getAttribute('aria-expanded')==='true';outer.classList.toggle('expanded',expanded);[...list.children].forEach((child,i)=>(child as HTMLElement).inert=!expanded&&i>=5);size()};
    button.onclick=()=>{const expanded=button.getAttribute('aria-expanded')!=='true';button.setAttribute('aria-expanded',String(expanded));button.setAttribute('aria-label',expanded?'收起排名':'展开更多排名');update()};
    new ResizeObserver(size).observe(list);update();
  });
}
