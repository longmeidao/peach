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
  const scan=(root:ParentNode)=>{root.querySelectorAll<HTMLInputElement>('input[type=range]').forEach(syncBoardRange);wireBoardSegments(root);wireBoardTabs(root);wireGrowingCharts(root)};
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

const tabPositions=new Map<string,{left:number;width:number}>();
/** 全站的下划线 Tabs 共用一条会滑的 2px 蓝色指示条（boardui tabs.tsx：transform 与 width
    各 200ms ease）。复核分类是药丸、统计与口味的维度是分段控件，选中都靠填充，不进这条。 */
export function wireBoardTabs(root:ParentNode){
  const selector='.managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav)';
  const groups=[...root.querySelectorAll<HTMLElement>(selector)];
  if(root instanceof HTMLElement&&root.matches(selector))groups.push(root);
  groups.forEach(group=>{
    if(group.hasAttribute('data-board-tabs'))return;group.dataset.boardTabs='true';
    const key=group.className+group.getAttribute('aria-label');
    const paint=(position:{left:number;width:number})=>{group.style.setProperty('--tab-x',`${position.left}px`);group.style.setProperty('--tab-width',`${position.width}px`)};
    const measure=()=>{const selected=group.querySelector<HTMLElement>('button[aria-selected=true],button[aria-pressed=true]');if(!selected||!selected.offsetWidth)return;const position={left:selected.offsetLeft,width:selected.offsetWidth};paint(position);tabPositions.set(key,position)};
    const previous=tabPositions.get(key);if(previous)paint(previous);else measure();
    requestAnimationFrame(()=>{group.classList.add('board-tabs-ready');requestAnimationFrame(measure)});
    const mutation=new MutationObserver(measure);mutation.observe(group,{subtree:true,attributes:true,attributeFilter:['aria-selected','aria-pressed']});
    const resize=new ResizeObserver(()=>{if(!group.isConnected){resize.disconnect();mutation.disconnect();return}measure()});resize.observe(group);
  });
}

/** 原生 radio 保留方向键语义，选中底板按实际尺寸滑动。
    面板切换那几组是 `role=tablist`：滑块换成按 `aria-selected` 找当前项，ARIA 仍然是 Tabs
    控制 tabpanel，不为了长得像分段控件就把它写成 radiogroup。 */
export function wireBoardSegments(root:ParentNode) {
  const selector='.iconswitch,.insightswitch,.insighttabs,.follow-workspace-switch';
  const groups=[...root.querySelectorAll<HTMLElement>(selector)];
  if(root instanceof HTMLElement&&root.matches(selector))groups.push(root);
  groups.forEach(group=>{
    if(group.hasAttribute('data-board-segments'))return;
    group.dataset.boardSegments='true';
    const thumb=document.createElement('span');thumb.className='board-segment-thumb';thumb.setAttribute('aria-hidden','true');group.prepend(thumb);
    const measure=()=>{
      const selected=group.querySelector<HTMLElement>('label:has(input:checked),button[aria-selected=true]');if(!selected||!selected.offsetWidth)return;
      thumb.style.transform=`translate(${selected.offsetLeft}px,${selected.offsetTop}px)`;
      thumb.style.width=`${selected.offsetWidth}px`;thumb.style.height=`${selected.offsetHeight}px`;
    };
    group.addEventListener('change',measure);
    const mutation=new MutationObserver(measure);mutation.observe(group,{subtree:true,attributes:true,attributeFilter:['aria-selected']});
    const resize=new ResizeObserver(()=>{if(!group.isConnected){resize.disconnect();mutation.disconnect();return}measure()});resize.observe(group);
    measure();requestAnimationFrame(()=>group.classList.add('board-segments-ready'));
  });
}

/** 排名条与雷达图进入可见区域后才从零长出（1.2 秒，与统计圆环同一条曲线）；减少动态效果时直接显示。 */
export function wireGrowingCharts(root:ParentNode) {
  const selector='.board-ranked-chart,.board-radar,.tasteranks,.board-heat-card,.board-sankey-card';
  const charts=[...root.querySelectorAll<HTMLElement>(selector)];
  if(root instanceof HTMLElement&&root.matches(selector))charts.push(root);
  charts.forEach(chart=>{
    if(chart.hasAttribute('data-board-chart'))return;chart.dataset.boardChart='true';
    /* 长完就钉住终态：这些图表大多住在 tab 面板里，面板一藏一显 display 就换过一轮，
       动画会跟着重头再放。等同一棵子树里没有还在跑的动画再钉，避免掐掉后半段。 */
    chart.addEventListener('animationend',()=>{
      if(chart.getAnimations?.({subtree:true}).some(animation=>animation.playState==='running'))return;
      chart.classList.add('board-chart-settled');
    });
    const reveal=()=>chart.classList.add('board-chart-visible');
    if(typeof IntersectionObserver==='undefined'||matchMedia('(prefers-reduced-motion: reduce)').matches){reveal();return}
    const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)){observer.disconnect();reveal()}},{threshold:.15});
    observer.observe(chart);
  });
}

export function wireExpandableRanks(root:ParentNode) {
  root.querySelectorAll<HTMLElement>('.tasteranks,.insightranking').forEach((list,index)=>{
    if(list.children.length<=5||list.parentElement?.hasAttribute('data-expandable-ranks'))return;
    const outer=document.createElement('div');outer.className='board-expand-ranks';outer.dataset.expandableRanks='';list.before(outer);outer.append(list);
    list.id=list.id||`board-rank-list-${index}`;list.classList.add('board-rank-list');
    const button=document.createElement('button');button.type='button';button.className='board-rank-expand';button.setAttribute('aria-controls',list.id);button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','展开更多排名');button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-down"/></svg>';outer.append(button);
    /* 收起时正好露五行，第五行落在渐隐里当那个「还有」的提示（boardui 实测：五行 196px、
       淡掉最后 44px）。多留一截空白的话渐隐盖的是空处，看不出下面还有内容。 */
    const size=()=>{const row=list.children[4] as HTMLElement;if(!list.offsetWidth)return;outer.style.setProperty('--rank-collapsed-height',`${row.offsetTop-list.offsetTop+row.offsetHeight}px`);outer.style.setProperty('--rank-expanded-height',`${list.scrollHeight}px`)};
    const update=()=>{const expanded=button.getAttribute('aria-expanded')==='true';outer.classList.toggle('expanded',expanded);[...list.children].forEach((child,i)=>(child as HTMLElement).inert=!expanded&&i>=5);size()};
    button.onclick=()=>{const expanded=button.getAttribute('aria-expanded')!=='true';button.setAttribute('aria-expanded',String(expanded));button.setAttribute('aria-label',expanded?'收起排名':'展开更多排名');update()};
    new ResizeObserver(size).observe(list);update();
  });
}
