import { describe,it,expect,vi } from 'vitest';
import { syncBoardRange, wireExpandableRanks, wireBoardSegments, wireBoardTabs, wireGrowingCharts } from '../src/board-controls';

describe('范围控件',()=>{
  it('视图切换保留原生 radio 且重复接线只创建一个滑块',()=>{
    document.body.innerHTML='<div class="iconswitch"><label><input type="radio" name="view" value="large" checked>大图</label><label><input type="radio" name="view" value="small">小图</label></div>';
    wireBoardSegments(document);wireBoardSegments(document);
    expect(document.querySelectorAll('.board-segment-thumb')).toHaveLength(1);
    const inputs=[...document.querySelectorAll<HTMLInputElement>('input')];
    inputs[1]!.click();
    expect(inputs[0]!.checked).toBe(false);expect(inputs[1]!.checked).toBe(true);
    expect(document.querySelector('.board-segment-thumb')?.getAttribute('aria-hidden')).toBe('true');
  });
  it('口味页的证据切换也是分段控件，拿到同一枚滑块',()=>{
    document.body.innerHTML='<div class="insightswitch" role="radiogroup"><label><input type="radio" name="e" value="browser" checked><span>浏览器记录</span></label><label><input type="radio" name="e" value="peach"><span>Peach 内部</span></label></div>';
    wireBoardSegments(document);wireBoardSegments(document);
    expect(document.querySelectorAll('.insightswitch .board-segment-thumb')).toHaveLength(1);
    expect(document.querySelector('.insightswitch')?.getAttribute('data-board-segments')).toBe('true');
  });
  it('复核页与口味页的标签条都接上会滑的下划线',()=>{
    document.body.innerHTML='<div class="reviewtabs" role="tablist"><button role="tab" aria-selected="true">元数据字段</button><button role="tab" aria-selected="false">厂牌 Logo</button></div><div class="insighttabs" role="tablist"><button role="tab" aria-selected="true">标签</button></div>';
    wireBoardTabs(document);wireBoardTabs(document);
    expect([...document.querySelectorAll('[data-board-tabs]')].map(group=>group.className)).toEqual(['reviewtabs','insighttabs']);
  });
  it('排名条与雷达图没有 IntersectionObserver 时立刻可见，重复接线不重复标记',()=>{
    document.body.innerHTML='<ol class="board-ranked-chart"><li></li></ol><svg class="board-radar"></svg><div class="tasteranks"></div>';
    vi.stubGlobal('IntersectionObserver',undefined);
    try{wireGrowingCharts(document);wireGrowingCharts(document)}finally{vi.unstubAllGlobals()}
    expect(document.querySelectorAll('.board-chart-visible')).toHaveLength(3);
    expect(document.querySelectorAll('[data-board-chart]')).toHaveLength(3);
  });
  it('折叠排名退出键盘导航，展开后恢复，重复接线不重复按钮',()=>{
    document.body.innerHTML='<div class="tasteranks">'+Array.from({length:7},()=>'<button>排名</button>').join('')+'</div>';
    wireExpandableRanks(document);wireExpandableRanks(document);
    const toggle=document.querySelector<HTMLButtonElement>('.board-rank-expand')!;
    const sixth=document.querySelector('.board-rank-list')!.children[5] as HTMLElement;
    expect(document.querySelectorAll('.board-rank-expand')).toHaveLength(1);
    expect(sixth.inert).toBe(true);toggle.click();expect(sixth.inert).toBe(false);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');toggle.click();expect(sixth.inert).toBe(true);
  });
  it('两个端点分别保留数值与不限状态，重复接线不增加气泡',()=>{
    document.body.innerHTML='<div class="dual-range"><input id="durMin" type="range" min="0" max="180" value="20"><input id="durMax" type="range" min="0" max="180" value="180"></div>';
    const inputs=[...document.querySelectorAll('input')];inputs.forEach(syncBoardRange);inputs.forEach(syncBoardRange);
    expect(document.querySelectorAll('output')).toHaveLength(2);expect(document.querySelector('[data-range-end="min"]')?.textContent).toBe('20 分钟');
    expect(document.querySelector('[data-range-end="max"]')?.textContent).toBe('不限');
    inputs[1]!.value='60';syncBoardRange(inputs[1]!);expect(document.querySelector('[data-range-end="max"]')?.textContent).toBe('60 分钟');
  });
});
