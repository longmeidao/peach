import { describe, it, expect } from 'vitest';
import { creatorSankeyHtml, wireCreatorSankey } from '../src/board-sankey';

describe('创作者线索流向',()=>{
  it('同名来源与创作者独立计量，聚焦联动并恢复总量',()=>{
    document.body.innerHTML=creatorSankeyHtml([{source:'alice',target:'alice',value:3},{source:'site',target:'alice',value:2}]);
    wireCreatorSankey(document);
    expect(document.querySelectorAll('[data-flow-node]')).toHaveLength(3);
    expect(document.querySelector('[data-sankey-number]')?.textContent).toBe('5');
    const link=document.querySelector<SVGElement>('[data-flow-source]')!;
    expect(link.getAttribute('d')).not.toMatch(/NaN|undefined/);
    link.dispatchEvent(new Event('focus'));
    expect(document.querySelector('[data-sankey-number]')?.textContent).toBe('3');
    link.dispatchEvent(new Event('blur'));
    expect(document.querySelector('[data-sankey-number]')?.textContent).toBe('5');
  });
  it('无有效计数时不绘制虚构流量',()=>{
    expect(creatorSankeyHtml([{source:'a',target:'b',value:NaN},{source:'a',target:'b',value:0}])).toBe('');
  });
});
