import { esc, icon } from './core.js';

const NOTE_VARIANTS=new Set(['secondary','warning','error','success']);

/** Inline, persistent context beside the field/card/section it describes. */
export function noteHtml(message,{variant='secondary',label='',className=''}={}){
  const kind=NOTE_VARIANTS.has(variant)?variant:'secondary';
  const symbol=kind==='success'?'check':'alert';
  const role=kind==='error'?' role="alert"':' role="note"';
  return `<div class="geist-note geist-note-${kind}${className?` ${esc(className)}`:''}"${role}>
    ${icon(symbol)}<p>${label?`<b>${esc(label)}</b>`:''}<span>${esc(message)}</span></p></div>`;
}

/** Determinate progress only. Callers supply real units instead of a decorative width. */
export function progressHtml(label,value,max=100){
  const ceiling=Math.max(0,Number(max)||0);
  const current=Math.max(0,Math.min(Number(value)||0,ceiling));
  const percent=ceiling?current/ceiling*100:0;
  return `<div class="geist-progress" role="progressbar" aria-label="${esc(label)}"
    aria-valuemin="0" aria-valuemax="${ceiling}" aria-valuenow="${current}"
    style="--progress-value:${percent}%"><i></i></div>`;
}
