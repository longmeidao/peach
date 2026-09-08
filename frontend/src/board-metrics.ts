/** 指标卡与排名图：使用服务端读数，不推导不存在的环比。 */
const escape=(value:unknown)=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!));
export function statCardBody(label:string,value:string,detail:string,icon='chart-no-axes-combined'):string {
  const glyph=/^[a-z0-9-]+$/.test(icon)?icon:'database';
  return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${glyph}"/></svg></span>${escape(label)}</span><b class="board-stat-value">${escape(value)}</b><small class="board-stat-footer">${escape(detail||'当前记录')}</small>`;
}
export interface RankedMetric { name:string; score:number }
export function jobProgressHtml(label:string,value:number,max:number):string {
  if(!Number.isFinite(max)||max<=0)return '';
  const done=Math.max(0,Math.min(max,Number.isFinite(value)?value:0)),percent=done/max*100;
  return `<div class="board-job-progress" role="progressbar" aria-label="${escape(label)}" aria-valuemin="0" aria-valuemax="${max}" aria-valuenow="${done}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${percent} ${100-percent}" transform="rotate(-90 18 18)"/></svg><span>${escape(label)}<small>${Math.round(percent)}%</small></span></div>`;
}
export function distributionChart(rows:RankedMetric[],label:string):string {
  const values=rows.filter(row=>Number.isFinite(row.score)&&row.score>0),total=values.reduce((sum,row)=>sum+row.score,0);
  if(!total)return '';
  let offset=0;
  const sectors=values.map((row,i)=>{const length=row.score/total*100;const circle=`<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${i%4})" stroke-width="22" stroke-dasharray="${length} ${100-length}" stroke-dashoffset="${-offset}"><title>${escape(row.name)}：${row.score.toLocaleString()}</title></circle>`;offset+=length;return circle}).join('');
  return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${escape(label)}"><g transform="rotate(-90 100 100)">${sectors}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${escape(label)}</text></svg>`;
}
export function rankedChart(rows:RankedMetric[],label:string):string {
  const values=rows.filter(row=>Number.isFinite(row.score)&&row.score>0).slice().sort((a,b)=>b.score-a.score).slice(0,8);
  if(!values.length)return '';
  const max=values[0]!.score;
  const bars=values.map(row=>`<li><span class="board-rank-fill" style="width:${(row.score/max*100).toFixed(2)}%"></span><span>${escape(row.name)}</span><b>${row.score.toLocaleString()}</b></li>`).join('');
  return `<ol class="board-ranked-chart" aria-label="${escape(label)}">${bars}</ol>`;
}
export function radarChart(rows:RankedMetric[],label:string):string {
  const values=rows.filter(row=>Number.isFinite(row.score)&&row.score>0).slice().sort((a,b)=>b.score-a.score).slice(0,6);
  if(values.length<3)return '';
  const max=Math.max(...values.map(row=>row.score)),n=values.length;
  const point=(i:number,r:number):[number,number]=>{const a=i/n*Math.PI*2-Math.PI/2;return [160+Math.cos(a)*r,140+Math.sin(a)*r]};
  const polygon=(radius:(i:number)=>number)=>values.map((_,i)=>point(i,radius(i)).map(v=>v.toFixed(2)).join(',')).join(' ');
  const grid=[25,50,75,100].map(r=>`<polygon points="${polygon(()=>r)}" class="board-radar-grid"/>`).join('');
  const axes=values.map((row,i)=>{const [x,y]=point(i,116);return `<text x="${x}" y="${y}" text-anchor="${x<145?'end':x>175?'start':'middle'}">${escape(row.name)}</text>`}).join('');
  return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${escape(label)}"><title>${escape(values.map(row=>`${row.name} ${row.score}`).join('，'))}</title>${grid}<polygon points="${polygon(i=>values[i]!.score/max*100)}" class="board-radar-value"/>${axes}</svg>`;
}
