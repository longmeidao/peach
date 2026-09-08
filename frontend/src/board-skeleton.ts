/** 页面骨架复用首屏结构；装饰元素不进入辅助技术阅读序列。 */
export function boardPageSkeleton(path:string):string {
  const line=(width='60%')=>`<i class="skeleton" style="width:${width}"></i>`;
  const row=()=>`<div class="board-skeleton-row">${line('36%')}${line('24%')}</div>`;
  let body='';
  if(path==='/stats'||path==='/taste'){
    body=`${path==='/taste'?`<div class="board-skeleton-row">${line('26%')}${line('32%')}</div>`:''}<div class="metricstrip board-skeleton-metrics">${Array.from({length:4},()=>`<div class="tastesummary">${line()}<b class="skeleton"></b><small class="board-stat-footer">${line('48%')}</small></div>`).join('')}</div><div class="board-skeleton-chart"><div class="board-skeleton-ring skeleton"></div><div>${row().repeat(4)}</div></div><div class="board-skeleton-section">${line('32%')}${row().repeat(5)}</div>`;
  }else if(path==='/follow-manage'){
    body=`<div class="board-skeleton-section">${line('20%')}<div class="skeleton board-skeleton-input"></div>${line('72%')}</div><div class="board-skeleton-row">${line('24%')}${line('40%')}</div><div class="board-skeleton-section">${row().repeat(6)}</div><div class="board-skeleton-row">${line('30%')}${line('30%')}</div>`;
  }else if(path==='/configuration'){
    body=`<div class="board-skeleton-row">${line('16%').repeat(4)}</div><div class="board-skeleton-section">${line('24%')}${row().repeat(3)}<div class="skeleton board-skeleton-input"></div></div><div class="board-skeleton-section">${line('24%')}${row().repeat(2)}</div>`;
  }else return '';
  return `<div class="board-page-skeleton" data-skeleton="board${path}" role="status" aria-label="正在读取页面"><div aria-hidden="true">${body}</div></div>`;
}
