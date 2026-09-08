import { useRef, useState } from 'preact/hooks';
import { selectOptionIconHtml, MEDIA_SOURCE_ICONS } from '@peach/legacy/ui';

/* 一行七枚、六行排完。第一枚是「不另选」：网盘库自动用网盘标识，本地路径没有可识别的
   来源，就是默认那枚磁盘。其余按题材成组：身体与情欲、身份与装扮、场景与情境、媒介与归档。 */
export const LIBRARY_ICON_CHOICES = [
  ['', '自动识别'], ['hard-drive','磁盘'], ['database','资料库'], ['heart','心动'], ['heart-hand','亲密'], ['flame','热情'], ['cherry','樱桃'],
  ['lollipop','甜心'], ['candy','糖果'], ['banana','香蕉'], ['droplets','湿润'], ['venus','女性'], ['mars','男性'], ['venus-and-mars','情侣'],
  ['gem','精选'], ['crown','女王'], ['ribbon','丝带'], ['shirt','制服'], ['graduation-cap','学生'], ['stethoscope','护士'], ['glasses','眼镜'],
  ['footprints','足迹'], ['hand','手部'], ['flower','花朵'], ['venetian-mask','角色扮演'], ['rabbit','兔女郎'], ['paw-print','兽耳'], ['dumbbell','健身'],
  ['bed-double','卧室'], ['bath','浴室'], ['key-round','私密'], ['wine','微醺'], ['cigarette','烟'], ['moon','夜色'], ['sparkles','幻想'],
  ['camera','写真'], ['video','影片'], ['film','电影'], ['image','图集'], ['gamepad-2','游戏'], ['star','收藏'], ['tags','主题'],
] as const;

/** 不另选时的字形与说法：网盘库跟着来源走（115、PikPak 的站标），本地路径没有什么可识别，就是默认磁盘。 */
export function libraryAutoChoice(kind:string):[string,string] {
  const mark=kind!=='local'?MEDIA_SOURCE_ICONS[kind]:'';
  return mark?[mark,'自动识别']:['hard-drive','默认'];
}

export function LibraryIconPicker({value,label,kind='local',onChange}:{value:string;label:string;kind?:string;onChange(value:string):void}) {
  const [draft,setDraft]=useState(value);
  const popup=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement>(null);
  const [autoMark,autoLabel]=libraryAutoChoice(kind);
  const glyph=(name:string)=><span aria-hidden="true" dangerouslySetInnerHTML={{__html:selectOptionIconHtml(name||autoMark)}}/>;
  const choiceLabel=(key:string,name:string)=>key?name:autoLabel;
  const open=()=>{setDraft(value);const dialog=popup.current!,rect=trigger.current!.getBoundingClientRect();dialog.showModal();
    const box=dialog.getBoundingClientRect();dialog.style.left=`${Math.max(8,Math.min(innerWidth-box.width-8,rect.left))}px`;
    dialog.style.top=`${rect.bottom+box.height+8<=innerHeight?rect.bottom+4:Math.max(8,rect.top-box.height-4)}px`;
  };
  return <div class="board-icon-picker">
    <button ref={trigger} type="button" class="geist-button board-icon-trigger" aria-label={label} aria-haspopup="dialog" onClick={open}>{glyph(value)}<span>{choiceLabel(value,LIBRARY_ICON_CHOICES.find(([key])=>key===value)?.[1]||autoLabel)}</span></button>
    <dialog ref={popup} class="board-icon-popover" aria-label={`${label}候选`} onCancel={()=>setDraft(value)} onClick={event=>{if(event.target===popup.current){popup.current?.close();setDraft(value)}}}>
      {/* 格子里只放图标：名字走 title 与 aria-label，带着字的话 42 个候选要排十几行。 */}
      <div class="board-icon-panel"><h3>选择媒体库图标</h3><div role="radiogroup" aria-label="候选图标" class="board-icon-grid">
        {LIBRARY_ICON_CHOICES.map(([key,name])=><label title={choiceLabel(key,name)} class={draft===key?'selected':''}><input type="radio" name={`${label}-icon`} aria-label={choiceLabel(key,name)} value={key} checked={draft===key} onChange={()=>setDraft(key)}/>{glyph(key)}</label>)}
      </div></div>
      <footer><button type="button" class="geist-button" onClick={()=>{setDraft(value);popup.current!.close()}}>取消</button><button type="button" class="geist-button primary" disabled={draft===value} onClick={()=>{onChange(draft);popup.current!.close()}}>应用</button></footer>
    </dialog>
  </div>;
}
