/** 侧栏筛选分组：标题、展开状态与叶项计数各自承担一种含义。 */
import { wireCollapse } from '@peach/legacy/ui';
const escape=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!));
/** `footer` 接在条目之后，属于这一组的内容；标题那一行只留组名和展开箭头。 */
export function sidebarSectionHtml(title:string,body:string,footer='',kind=''):string {
  if(!body)return '';
  const id=`sidebar-group-${encodeURIComponent(title)}`;
  return `<details class="sec${kind?' cat-'+escape(kind):''}" data-sidebar-group="${escape(title)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${escape(title)}</span></summary><div class="board-sidebar-body" id="${id}">${body}${footer}</div></details>`;
}
export function wireSidebarGroups(root:HTMLElement):void {
  root.querySelectorAll<HTMLDetailsElement>('[data-sidebar-group]').forEach(group=>{
    if(group.dataset.sidebarWired)return;group.dataset.sidebarWired='true';
    const body=group.querySelector<HTMLElement>('.board-sidebar-body')!;
    const key=`peach.sidebar.group.${group.dataset.sidebarGroup}`;
    let saved:string|null=null;try{saved=sessionStorage.getItem(key)}catch{}
    const active=!!body.querySelector('[aria-pressed=true]');
    /* 一进来只有正在生效的那几组是展开的。挑两组常驻展开等于替人决定他这次要按哪个维度
       筛，而侧栏一屏就那么长，展开的部分把别的组挤到看不见的地方去。 */
    group.open=saved!==null?saved==='open':active;
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
  /* 柔边那一圈由一段 CSS 渐变画，不套 SVG：遮罩的尺寸每一帧都在变，每一帧就要照新
     尺寸把它重新光栅化一遍，而一张带高斯模糊滤镜的 SVG 每次都要连滤镜一起重跑。
     渐变没有这一层，边缘的过渡带靠色标位置给。 */
  const mask='radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent)';
  const style=document.createElement('style');style.textContent=`::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:${mask};mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${x}px ${y}px;mask-size:0px 0px}to{mask-position:${x-size/2}px ${y-size/2}px;mask-size:${size}px ${size}px}}`;
  themeChanging=true;document.head.append(style);
  try{await document.startViewTransition(apply).finished}catch{apply()}finally{style.remove();themeChanging=false}
}
