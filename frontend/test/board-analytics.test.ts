import { describe,it,expect } from 'vitest';
import { activityChartsHtml,wireActivityCharts } from '../src/board-analytics';

describe('口味页交互图表',()=>{
  it('热图使用真实读数，填充零值并排除非法坐标',()=>{
    document.body.innerHTML=activityChartsHtml({days:[{date:'2026-09-08',count:3}],hours:[{weekday:1,hour:12,count:3},{weekday:10,hour:99,count:200}]});
    expect(document.querySelectorAll('.board-hour-grid button')).toHaveLength(168);
    expect(document.querySelectorAll('.board-day-grid button')).toHaveLength(91);
    wireActivityCharts(document);
    const cell=document.querySelector<HTMLButtonElement>('[data-heat-label="周二 12:00"]')!;cell.focus();
    expect(document.querySelector('[data-heat-number]')?.textContent).toBe('3');
    expect(document.querySelector('[data-heat-title]')?.textContent).toBe('周二 12:00');
  });
  it('没有历史时给出空态，不生成假活动',()=>{
    expect(activityChartsHtml(undefined)).toContain('还没有');expect(activityChartsHtml(undefined)).not.toContain('data-heat-value');
  });
});
