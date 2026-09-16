import { esc } from '@peach/legacy/core';

const valid=(value:number)=>Number.isFinite(value)&&value>=0;

export interface HistoryActivity { timezone?:string; days:{date:string;count:number}[]; hours:{weekday:number;hour:number;count:number}[] }
const weekdays=['周一','周二','周三','周四','周五','周六','周日'];
export function activityChartsHtml(activity:HistoryActivity|undefined) {
  if(!activity?.days?.length)return '<section class="board-activity-empty"><h3>浏览活跃时间</h3><p>还没有可用于分析的口味网站访问记录。</p></section>';
  const hours=Array.from({length:7},()=>Array<number>(24).fill(0));
  for(const item of activity.hours||[])if(Number.isInteger(item.weekday)&&item.weekday>=0&&item.weekday<7&&Number.isInteger(item.hour)&&item.hour>=0&&item.hour<24&&valid(item.count))hours[item.weekday]![item.hour]=(hours[item.weekday]![item.hour]||0)+item.count;
  const max=Math.max(1,...hours.flat()),total=hours.flat().reduce((a,b)=>a+b,0);
  const cells=hours.map((row,day)=>`<span class="board-heat-axis">${weekdays[day]}</span>${row.map((count,hour)=>`<button type="button" data-heat-value="${count}" data-heat-label="${weekdays[day]} ${hour}:00" aria-label="${weekdays[day]} ${hour}:00，${count} 次访问" style="--heat:${count?Math.max(12,count/max*100):0}%"></button>`).join('')}`).join('');
  const days=activity.days.filter(row=>/^\d{4}-\d{2}-\d{2}$/.test(row.date)&&valid(row.count)).sort((a,b)=>a.date.localeCompare(b.date));
  if(!days.length)return '';
  const end=new Date(`${days.at(-1)!.date}T00:00:00Z`),start=new Date(end);start.setUTCDate(start.getUTCDate()-90);
  const daily=new Map(days.map(row=>[row.date,row.count])),dayMax=Math.max(1,...days.map(row=>row.count));
  const calendar=Array.from({length:91},(_,index)=>{const date=new Date(start);date.setUTCDate(start.getUTCDate()+index);const key=date.toISOString().slice(0,10),count=daily.get(key)||0;return `<button type="button" data-heat-value="${count}" data-heat-label="${key}" aria-label="${key}，${count} 次访问" style="--heat:${count?Math.max(12,count/dayMax*100):0}%"></button>`}).join('');
  return `<div class="board-activity-charts"><section class="board-heat-card" data-heat-card><header><h3>浏览活跃时间</h3><b data-heat-number>${total.toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-heat-scroll"><div class="board-hour-grid"><span></span>${Array.from({length:24},(_,hour)=>`<span class="board-heat-axis">${hour%2?'':hour}</span>`).join('')}${cells}</div></div><footer>星期 × 小时<span>${esc(activity.timezone||'UTC+08:00')}</span></footer></section><section class="board-heat-card" data-heat-card><header><h3>每日活跃</h3><b data-heat-number>${days.filter(row=>row.date>=start.toISOString().slice(0,10)).reduce((sum,row)=>sum+row.count,0).toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-day-grid">${calendar}</div><footer>${start.toISOString().slice(0,10)}<span>${days.at(-1)!.date}</span></footer></section></div>`;
}

export function wireActivityCharts(root:ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-heat-card]').forEach(card=>{
    const number=card.querySelector<HTMLElement>('[data-heat-number]')!,title=card.querySelector<HTMLElement>('[data-heat-title]')!,total=number.textContent;
    card.querySelectorAll<HTMLElement>('[data-heat-value]').forEach(cell=>{
      const show=()=>{number.textContent=Number(cell.dataset.heatValue).toLocaleString();title.textContent=cell.dataset.heatLabel!};
      const reset=()=>{number.textContent=total;title.textContent=title.dataset.heatDefault!};
      cell.addEventListener('pointerenter',show);cell.addEventListener('pointerleave',reset);cell.addEventListener('focus',show);cell.addEventListener('blur',reset);
    });
  });
}
