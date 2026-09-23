import { moveGlidePane, scrollMovesAnchor } from '@peach/legacy/ui';

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
  /* 气泡对着手柄居中，伸出轨道的那一截按实测溢出量收回来：这一排住在侧栏里，侧栏只
     比轨道宽出一点点，越界的半截被侧栏裁掉，读数就只剩一半。量之前先把上一次的位移
     清掉，否则量到的是已经收过一次的位置，越拖越偏。 */
  tip.style.setProperty('--range-tip-shift','0px');
  const bounds=group.getBoundingClientRect(),box=tip.getBoundingClientRect();
  const shift=box.right>bounds.right?bounds.right-box.right
    :box.left<bounds.left?bounds.left-box.left:0;
  if(shift)tip.style.setProperty('--range-tip-shift',`${Math.round(shift)}px`);
  /* 两端拖到一起时，刚动过的那枚压在上面：另一枚报的是它自己停下的位置，盖住这一枚
     等于把唯一正在变的读数藏起来——手上还在拖，屏幕上却没有数在动。 */
  group.querySelectorAll('.board-range-tip').forEach(node=>
    node.toggleAttribute('data-range-active',node===tip));
}

export function initBoardControls() {
  const scan=(root:ParentNode)=>{root.querySelectorAll<HTMLInputElement>('input[type=range]').forEach(syncBoardRange);wireBoardSegments(root);wireBoardTabs(root)};
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
  // 只在提示所指的那一枚被滚走时收：首页新作那一排每一帧都在横滚，任何 scroll 都收的话提示一出来就没了。
  document.addEventListener('scroll',event=>{if(target&&scrollMovesAnchor(event,target))hide()},true);window.addEventListener('resize',hide);
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

const segmentPositions=new Map<string,{x:number;y:number;w:number;h:number}>();
/** 原生 radio 保留方向键语义，选中底板按实际尺寸滑动。
    面板切换那几组是 `role=tablist`：滑块换成按 `aria-selected` 找当前项，ARIA 仍然是 Tabs
    控制 tabpanel，不为了长得像分段控件就把它写成 radiogroup。 */
export function wireBoardSegments(root:ParentNode) {
  const selector='.iconswitch,.insightswitch,.follow-workspace-switch';
  const groups=[...root.querySelectorAll<HTMLElement>(selector)];
  if(root instanceof HTMLElement&&root.matches(selector))groups.push(root);
  groups.forEach(group=>{
    if(group.hasAttribute('data-board-segments')||group.closest('[data-skeleton]'))return;
    group.dataset.boardSegments='true';
    const thumb=document.createElement('span');thumb.className='board-segment-thumb';thumb.setAttribute('aria-hidden','true');group.prepend(thumb);
    /* 底板换位跟筛选条上那块玻璃是同一件事——「当前是这一个」从一处挪到另一处——所以
       走同一段动作：滑过去、冲过落点、荡回来。
       上一次停在哪儿按这一组的身份记，不按节点记：点一下往往把整块重画一遍，拿节点
       记等于每次都是一块新出现的底板，只落位不动画，一路点下来它一次都没动过。
       真正头一次出现时没有上一次，那一下不动画——新出现的底板不该从别处飞进来。 */
    const key=group.className+(group.getAttribute('aria-label')??'');
    let from=segmentPositions.get(key)??null;
    const measure=()=>{
      const selected=group.querySelector<HTMLElement>('label:has(input:checked),button[aria-selected=true]');if(!selected||!selected.offsetWidth)return;
      const box={x:selected.offsetLeft,y:selected.offsetTop,w:selected.offsetWidth,h:selected.offsetHeight};
      moveGlidePane(thumb,from,box,'x');
      from=box;segmentPositions.set(key,box);
    };
    group.addEventListener('change',measure);
    const mutation=new MutationObserver(measure);mutation.observe(group,{subtree:true,attributes:true,attributeFilter:['aria-selected']});
    const resize=new ResizeObserver(()=>{if(!group.isConnected){resize.disconnect();mutation.disconnect();return}measure()});resize.observe(group);
    measure();requestAnimationFrame(()=>group.classList.add('board-segments-ready'));
  });
}
