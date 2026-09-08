import { describe,it,expect,vi } from 'vitest';
import { radialCardHtml,wireRadialCards,activityChartsHtml,wireActivityCharts } from '../src/board-analytics';

describe('统计与口味交互图表',()=>{
  it('环形图保留零读数、排除无效值并转义库名',()=>{
    document.body.innerHTML=radialCardHtml([{name:'<库>',value:4},{name:'空库',value:0},{name:'错误',value:NaN}],'媒体库');
    expect(document.querySelectorAll('[data-radial-tile]')).toHaveLength(2);
    expect(document.querySelector('[data-radial-tile]')?.textContent).toContain('<库>');
    expect(document.querySelector('[data-radial-total]')?.getAttribute('data-radial-total')).toBe('4');
  });
  it('底部读数与对应圆环双向选择，重复点击可取消',()=>{
    vi.stubGlobal('matchMedia',()=>({matches:true}));
    document.body.innerHTML=radialCardHtml([{name:'本地',value:4},{name:'网盘',value:8}],'来源');
    wireRadialCards(document);
    const tile=document.querySelector<HTMLButtonElement>('[data-radial-tile="1"]')!,ring=document.querySelector('[data-radial-ring="1"]')!;
    tile.click();expect(tile.getAttribute('aria-pressed')).toBe('true');expect(ring.getAttribute('aria-pressed')).toBe('true');
    ring.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter'}));expect(tile.getAttribute('aria-pressed')).toBe('false');
    vi.unstubAllGlobals();
  });
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
