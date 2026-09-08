/** 侧栏筛选分组：标题、展开状态与叶项计数各自承担一种含义。 */
const escape=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!));
export function sidebarSectionHtml(title:string,body:string,extra='',kind=''):string {
  if(!body)return '';
  const id=`sidebar-group-${encodeURIComponent(title)}`;
  return `<section class="sec${kind?' cat-'+escape(kind):''}" data-sidebar-group="${escape(title)}"><h3><button type="button" class="board-section-toggle" aria-expanded="true" aria-controls="${id}"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${escape(title)}</span></button>${extra}</h3><div class="board-sidebar-body" id="${id}">${body}</div></section>`;
}
export function wireSidebarGroups(root:HTMLElement):void {
  root.querySelectorAll<HTMLElement>('[data-sidebar-group]').forEach(group=>{
    if(group.dataset.sidebarWired)return;group.dataset.sidebarWired='true';
    const button=group.querySelector<HTMLButtonElement>('.board-section-toggle')!,body=group.querySelector<HTMLElement>('.board-sidebar-body')!;
    const key=`peach.sidebar.group.${group.dataset.sidebarGroup}`;
    let saved:string|null=null;try{saved=sessionStorage.getItem(key)}catch{}
    const show=(open:boolean)=>{button.setAttribute('aria-expanded',String(open));body.hidden=!open};
    const active=!!body.querySelector('[aria-pressed=true]');
    show(saved!==null?saved==='open':active||group.classList.contains('cat-src')||group.dataset.sidebarGroup==='时长');
    button.onclick=()=>{const open=button.getAttribute('aria-expanded')!=='true';show(open);try{sessionStorage.setItem(key,open?'open':'closed')}catch{}};
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
