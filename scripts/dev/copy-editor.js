/* 源码与演示预览的改字工具，仅由 ?edit 页面加载。 */
(()=>{
 const source=document.body.dataset.peachCopyMode==='source',key='peach.copy-edits.v1';
 let edits={},active=true,editing=false;
 try{edits=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
 const bar=document.createElement('div');bar.dataset.copyEditor='';
 Object.assign(bar.style,{position:'fixed',bottom:'calc(16px + var(--demo-notice-height,0px))',left:'50%',transform:'translateX(-50%)',zIndex:'2147483647',padding:'10px 14px',borderRadius:'12px',display:'flex',gap:'10px',alignItems:'center',background:'var(--ground,#fff)',color:'var(--ink,#111)',boxShadow:'0 2px 18px #0003',font:'13px system-ui',maxWidth:'calc(100vw - 32px)'});
 const label=document.createElement('b');label.textContent='改字模式';bar.append(label);
 const status=document.createElement('span');status.textContent=source?'点文字修改并保存到源码':'点文字修改，保存到本浏览器';bar.append(status);
 const button=(text,fn)=>{const b=document.createElement('button');b.textContent=text;b.type='button';b.onclick=fn;bar.append(b);return b};
 const toggle=button('暂停编辑',()=>{active=!active;toggle.textContent=active?'暂停编辑':'继续编辑'});
 button('导出修改',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(edits,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='peach-copy-edits.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
 button('退出',()=>{const url=new URL(location.href);url.searchParams.delete('edit');location.href=url});
 document.body.append(bar);
 const apply=()=>{
  if(editing)return;
  const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;
  while((node=walk.nextNode())){
   if(node.parentElement.closest('[data-copy-editor],script,style,textarea,input'))continue;
   const original=node.textContent.trim();if(original&&edits[original])node.textContent=node.textContent.replace(original,edits[original]);
  }
 };
 new MutationObserver(apply).observe(document.body,{childList:true,subtree:true});apply();
 if(source)fetch('/dev/copy-edits').then(r=>r.ok?r.json():{}).then(saved=>{edits={...edits,...saved};apply()});
 const textAt=(x,y)=>{if(document.caretPositionFromPoint){const p=document.caretPositionFromPoint(x,y);return p?.offsetNode?.nodeType===3?p.offsetNode:null}const r=document.caretRangeFromPoint?.(x,y);return r?.startContainer?.nodeType===3?r.startContainer:null};
 document.addEventListener('click',async event=>{
  if(!active||editing||event.target.closest('[data-copy-editor]'))return;
  const node=textAt(event.clientX,event.clientY);if(!node||!node.textContent.trim())return;
  event.preventDefault();event.stopImmediatePropagation();editing=true;
  const original=node.textContent.trim(),input=document.createElement('input');input.value=original;
  input.dataset.copyEditor='';input.style.cssText='position:fixed;z-index:2147483647;left:16px;right:16px;top:16px;padding:12px;font:16px system-ui;background:var(--ground,#fff);color:var(--ink,#111);border:2px solid var(--tungsten,#007aff);border-radius:10px';
  document.body.append(input);input.focus();input.select();status.textContent='回车保存，Esc 取消';
  const cancel=()=>{input.remove();editing=false};
  input.addEventListener('keydown',async event=>{
   if(event.key==='Escape'){cancel();status.textContent='已取消';return}
   if(event.key!=='Enter')return;
   event.preventDefault();const replacement=input.value.trim();if(!replacement)return;
   input.disabled=true;
   try{
    if(source){
     // 刷新后显示的是本地修改，源文件查找仍按当前可见文案。
     const response=await fetch('/dev/copy-candidates?text='+encodeURIComponent(original));
     const candidates=await response.json();if(!response.ok||!candidates.length)throw Error('未找到静态源文案；可先导出修改');
     let candidate=candidates[0];
     if(candidates.length>1){
      const select=document.createElement('select');select.dataset.copyEditor='';
      select.style.cssText=input.style.cssText+';top:70px';
      select.add(new Option('请选择文案来源',''));
      candidates.forEach((x,i)=>select.add(new Option(`${x.file}:${x.line}`,String(i))));
      document.body.append(select);status.textContent='这段文案有多个位置，请选择来源';
      candidate=await new Promise(resolve=>{select.onchange=()=>{select.remove();resolve(candidates[Number(select.value)])};input.addEventListener('keydown',event=>{if(event.key==='Escape'){select.remove();resolve(null)}},{once:true})});
      if(!candidate)throw Error('未选择源位置');
     }
     const saved=await fetch('/dev/copy-save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({original,replacement,candidate})});
     const result=await saved.json();if(!saved.ok)throw Error(result.error||'保存失败');
     status.textContent=result.needs_build?'已保存源码；前端重建后在普通模式生效':'已保存源码';
    }else status.textContent='已保存到本浏览器，可导出修改';
    edits[original]=replacement;localStorage.setItem(key,JSON.stringify(edits));node.textContent=node.textContent.replace(original,replacement);cancel();apply();
   }catch(error){input.disabled=false;status.textContent=error.message}
  });
 },true);
})();
