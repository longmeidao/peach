/** 带单位、可选开关及字段错误反馈的数值设置。 */
export interface NumberSettingSpec { min: number; max: number; unit: string; optional?: boolean; fallback: number }
const specs: Record<string, NumberSettingSpec> = {
  loginDaysSetting: { min: 1, max: 365, unit: '天', fallback: 30 },
  batchSizeSetting: { min: 1, max: 200, unit: '个', fallback: 60 },
  hoverDelaySetting: { min: 1, max: 60, unit: '秒', optional: true, fallback: 5 },
  seekSecondsSetting: { min: 1, max: 300, unit: '秒', fallback: 10 },
  relatedLimitSetting: { min: 1, max: 60, unit: '个', optional: true, fallback: 20 },
  searchHistoryLimitSetting: { min: 1, max: 50, unit: '条', optional: true, fallback: 10 },
  followScheduleSetting: { min: 15, max: 10080, unit: '分钟', optional: true, fallback: 60 },
};
export function boundedPreference(value: number, min: number, max: number, fallback: number): number {
  return Number.isInteger(value) && value >= min && value <= max ? value : fallback;
}
export function syncNumberSetting(mount: HTMLElement, value: number | null, disabled: boolean): void {
  const input=mount.querySelector<HTMLInputElement>('input[type=number]');
  const toggle=mount.querySelector<HTMLInputElement>('[role=switch]');
  const fields=mount.querySelector<HTMLElement>('.board-number-fields');
  if(input){input.disabled=disabled;if(value!==null&&value>0)input.value=String(value)}
  if(toggle){toggle.disabled=disabled;if(value!==null)toggle.checked=value>0}
  if(fields&&value!==null)fields.hidden=value===0;
}
export function mountNumberSetting(mount: HTMLElement, id: string, label: string, value: number, apply: (value: string) => void): boolean {
  const spec=specs[id]; if(!spec) return false;
  const {min,max,unit,optional,fallback}=spec;
  const storageKey=`peach.number.${id}`;
  let remembered=boundedPreference(Number(localStorage.getItem(storageKey)),min,max,value>0?value:fallback);
  const control=document.createElement('div'); control.className='board-optional-number';
  const fields=document.createElement('div'); fields.className='board-number-fields'; fields.hidden=!!optional&&value===0;
  const frame=document.createElement('div'); frame.className='board-number-control';
  const input=document.createElement('input'); input.type='number'; input.className='geist-input'; input.min=String(min); input.max=String(max); input.step='1'; input.value=String(value>0?value:remembered); input.setAttribute('aria-label',label);
  const suffix=document.createElement('span'); suffix.textContent=unit; suffix.setAttribute('aria-hidden','true');
  const error=document.createElement('small'); error.id=`${id}-error`; error.className='board-number-error'; error.setAttribute('role','status'); error.hidden=true;
  input.setAttribute('aria-describedby',error.id);
  frame.append(input,suffix); fields.append(frame,error); control.append(fields); mount.replaceChildren(control);
  const clear=()=>{input.removeAttribute('aria-invalid');error.hidden=true;error.textContent=''};
  const commit=()=>{
    if(!input.value||!input.checkValidity()) { input.setAttribute('aria-invalid','true');error.textContent=`请输入 ${min}–${max} 的整数（${unit}）`;error.hidden=false;return; }
    clear(); remembered=Number(input.value);localStorage.setItem(storageKey,String(remembered));apply(input.value);
  };
  input.addEventListener('change',commit);
  input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();commit()}});
  input.addEventListener('input',()=>{if(input.value&&input.checkValidity())clear()});
  if(optional){
    const toggle=document.createElement('input');toggle.type='checkbox';toggle.className='ptoggle';toggle.setAttribute('role','switch');toggle.setAttribute('aria-label',`启用${label}`);toggle.checked=value>0;
    toggle.onchange=()=>{
      clear();fields.hidden=!toggle.checked;
      if(toggle.checked){input.value=String(remembered);commit()}
      else{
        if(input.value&&input.checkValidity())remembered=Number(input.value);
        localStorage.setItem(storageKey,String(remembered));apply('0');
      }
    };
    control.prepend(toggle);
  }
  return true;
}
