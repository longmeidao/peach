/** 侧栏筛选分组：标题、展开状态与叶项计数各自承担一种含义。 */
import { wireCollapse } from '@peach/legacy/ui';
const escape=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!));
export function sidebarSectionHtml(title:string,body:string,extra='',kind=''):string {
  if(!body)return '';
  const id=`sidebar-group-${encodeURIComponent(title)}`;
  return `<details class="sec${kind?' cat-'+escape(kind):''}" data-sidebar-group="${escape(title)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${escape(title)}</span>${extra}</summary><div class="board-sidebar-body" id="${id}">${body}</div></details>`;
}
export function wireSidebarGroups(root:HTMLElement):void {
  root.querySelectorAll<HTMLDetailsElement>('[data-sidebar-group]').forEach(group=>{
    if(group.dataset.sidebarWired)return;group.dataset.sidebarWired='true';
    const button=group.querySelector<HTMLElement>('.board-section-toggle')!,body=group.querySelector<HTMLElement>('.board-sidebar-body')!;
    const key=`peach.sidebar.group.${group.dataset.sidebarGroup}`;
    let saved:string|null=null;try{saved=sessionStorage.getItem(key)}catch{}
    const active=!!body.querySelector('[aria-pressed=true]');
    /* 一进来只有正在生效的那几组是展开的。挑两组常驻展开等于替人决定他这次要按哪个维度
       筛，而侧栏一屏就那么长，展开的部分把别的组挤到看不见的地方去。 */
    group.open=saved!==null?saved==='open':active;
    button.querySelectorAll('button').forEach(control=>control.addEventListener('click',event=>event.stopPropagation()));
  });
  wireCollapse(root,'details[data-sidebar-group]','sidebar-collapse');
  root.querySelectorAll<HTMLElement>('.board-section-toggle').forEach(button=>{
    if(button.dataset.persistWired)return;button.dataset.persistWired='true';
    button.addEventListener('click',()=>{const key=`peach.sidebar.group.${button.closest<HTMLElement>('[data-sidebar-group]')!.dataset.sidebarGroup}`;try{sessionStorage.setItem(key,button.getAttribute('aria-expanded')==='true'?'open':'closed')}catch{}});
  });
}

let themeChanging=false;
/** Board 的主题切换从触发器中心扩散，减少动态效果时直接应用。 */
export async function transitionTheme(button:HTMLElement,apply:()=>void):Promise<void>{
  if(themeChanging)return;
  if(!document.startViewTransition||matchMedia('(prefers-reduced-motion: reduce)').matches){apply();return}
  const rect=button.getBoundingClientRect(),x=rect.left+rect.width/2,y=rect.top+rect.height/2;
  const size=Math.hypot(Math.max(x,innerWidth-x),Math.max(y,innerHeight-y))*2.5;
  const mask=`url("data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><filter id="b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2"/></filter></defs><circle cx="50" cy="50" r="42" fill="white" filter="url(#b)"/></svg>')}")`;
  const style=document.createElement('style');style.textContent=`::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:${mask};mask-repeat:no-repeat;animation:peach-theme-reveal 820ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${x}px ${y}px;mask-size:0px 0px}to{mask-position:${x-size/2}px ${y-size/2}px;mask-size:${size}px ${size}px}}`;
  themeChanging=true;document.head.append(style);
  try{await document.startViewTransition(apply).finished}catch{apply()}finally{style.remove();themeChanging=false}
}
