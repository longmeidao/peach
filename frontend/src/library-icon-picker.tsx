import { useRef, useState } from 'preact/hooks';
import { selectOptionIconHtml } from '@peach/legacy/ui';

export const LIBRARY_ICON_CHOICES = [
  ['', '自动识别'], ['hard-drive','磁盘'], ['database','资料库'], ['heart','心动'], ['heart-hand','亲密'],
  ['flame','热情'], ['cherry','樱桃'], ['gem','精选'], ['crown','女王'], ['shirt','制服'],
  ['footprints','足迹'], ['flower','花朵'], ['venetian-mask','角色扮演'], ['hand','手部'], ['bed-double','卧室'],
  ['moon','夜色'], ['sparkles','幻想'], ['camera','写真'], ['video','影片'], ['star','收藏'], ['tags','主题'],
] as const;

export function LibraryIconPicker({value,label,onChange}:{value:string;label:string;onChange(value:string):void}) {
  const [draft,setDraft]=useState(value);
  const popup=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement>(null);
  const glyph=(name:string)=><span aria-hidden="true" dangerouslySetInnerHTML={{__html:selectOptionIconHtml(name||'database')}}/>;
  const open=()=>{setDraft(value);const dialog=popup.current!,rect=trigger.current!.getBoundingClientRect();dialog.showModal();
    const box=dialog.getBoundingClientRect();dialog.style.left=`${Math.max(8,Math.min(innerWidth-box.width-8,rect.left))}px`;
    dialog.style.top=`${rect.bottom+box.height+8<=innerHeight?rect.bottom+4:Math.max(8,rect.top-box.height-4)}px`;
  };
  return <div class="board-icon-picker">
    <button ref={trigger} type="button" class="geist-button board-icon-trigger" aria-label={label} aria-haspopup="dialog" onClick={open}>{glyph(value)}<span>{LIBRARY_ICON_CHOICES.find(([key])=>key===value)?.[1]||'自动识别'}</span></button>
    <dialog ref={popup} class="board-icon-popover" aria-label={`${label}候选`} onCancel={()=>setDraft(value)} onClick={event=>{if(event.target===popup.current){popup.current?.close();setDraft(value)}}}>
      {/* 格子里只放图标：名字走 title 与 aria-label。21 个候选带着字要排六行，面板比触发它的设置卡还高。 */}
      <div class="board-icon-panel"><h3>选择媒体库图标</h3><div role="radiogroup" aria-label="候选图标" class="board-icon-grid">
        {LIBRARY_ICON_CHOICES.map(([key,name])=><label title={name} class={draft===key?'selected':''}><input type="radio" name={`${label}-icon`} aria-label={name} value={key} checked={draft===key} onChange={()=>setDraft(key)}/>{glyph(key)}</label>)}
      </div></div>
      <footer><button type="button" class="geist-button" onClick={()=>{setDraft(value);popup.current!.close()}}>取消</button><button type="button" class="geist-button primary" disabled={draft===value} onClick={()=>{onChange(draft);popup.current!.close()}}>应用</button></footer>
    </dialog>
  </div>;
}
