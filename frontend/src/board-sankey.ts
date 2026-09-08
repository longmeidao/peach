import { sankey, sankeyLinkHorizontal } from 'd3-sankey';
import { esc } from '@peach/legacy/core';
export interface CreatorFlow { source:string; target:string; value:number }

export function creatorSankeyHtml(rows:CreatorFlow[] = []) {
  const flows=rows.filter(row=>row.source&&row.target&&Number.isFinite(row.value)&&row.value>0);
  if(!flows.length)return '';
  const sources=[...new Set(flows.map(row=>row.source))],targets=[...new Set(flows.map(row=>row.target))];
  const graph=sankey<{id:string;name:string;side:string},{}>().nodeId(node=>node.id).nodeWidth(10).nodePadding(22).extent([[155,16],[535,404]])({
    nodes:[...sources.map(name=>({id:`source:${name}`,name,side:'source'})),...targets.map(name=>({id:`target:${name}`,name,side:'target'}))],
    links:flows.map(row=>({source:`source:${row.source}`,target:`target:${row.target}`,value:row.value})),
  });
  const total=flows.reduce((sum,row)=>sum+row.value,0),path=sankeyLinkHorizontal();
  const links=graph.links.map(link=>{
    const source=link.source as typeof graph.nodes[number],target=link.target as typeof graph.nodes[number];
    return `<path d="${path(link)}" stroke-width="${Math.max(.5,link.width||0)}" style="--flow-color:var(--board-chart-${sources.indexOf(source.name)%6})" data-flow-source="${source.index}" data-flow-target="${target.index}" data-flow-value="${link.value}" data-flow-label="${esc(source.name)} → ${esc(target.name)}" tabindex="0" role="img" aria-label="${esc(source.name)} → ${esc(target.name)}：${link.value} 条线索"/>`;
  }).join('');
  const nodes=graph.nodes.map(node=>`<g data-flow-node="${node.index}" data-flow-value="${node.value}" data-flow-label="${esc(node.name)}" tabindex="0" role="img" aria-label="${esc(node.name)}：${node.value} 条线索"><rect x="${node.x0}" y="${node.y0}" width="10" height="${Math.max(1,(node.y1||0)-(node.y0||0))}" rx="5" fill="${node.side==='source'?`var(--board-chart-${sources.indexOf(node.name)%6})`:'var(--color-text-secondary)'}"/><text x="${node.side==='source'?145:545}" y="${((node.y0||0)+(node.y1||0))/2}" text-anchor="${node.side==='source'?'end':'start'}" dominant-baseline="middle">${esc(node.name.length>18?node.name.slice(0,16)+'…':node.name)}<tspan x="${node.side==='source'?145:545}" dy="15">${node.side==='source'?node.value?.toLocaleString():((node.value||0)/total*100).toFixed(1)+'%'}</tspan></text></g>`).join('');
  return `<section class="board-sankey-card" data-sankey-card><header><h3>创作者线索来源</h3><b data-sankey-number>${total.toLocaleString()}</b><span data-sankey-label>条线索</span></header><div class="board-sankey-scroll"><svg viewBox="0 0 720 435" aria-label="来源网站与创作者线索"><g class="board-sankey-links">${links}</g><g class="board-sankey-nodes">${nodes}</g></svg></div><footer><span>来源网站</span><span>创作者 · 线索占比</span></footer></section>`;
}

export function wireCreatorSankey(root:ParentNode) {
  root.querySelectorAll<HTMLElement>('[data-sankey-card]').forEach(card=>{
    const links=[...card.querySelectorAll<SVGElement>('[data-flow-source]')],nodes=[...card.querySelectorAll<SVGElement>('[data-flow-node]')];
    const headline=card.querySelector('[data-sankey-number]')!,label=card.querySelector('[data-sankey-label]')!,total=headline.textContent;
    const reset=()=>{links.forEach(link=>link.style.opacity='');nodes.forEach(node=>node.style.opacity='');headline.textContent=total;label.textContent='条线索'};
    [...links,...nodes].forEach(element=>{
      const show=()=>{const node=element.dataset.flowNode;
        links.forEach(link=>link.style.opacity=String((node!==undefined?link.dataset.flowSource===node||link.dataset.flowTarget===node:link===element)? .7:.08));
        nodes.forEach(item=>item.style.opacity=String(node!==undefined?(item===element||links.some(link=>(link.dataset.flowSource===node&&link.dataset.flowTarget===item.dataset.flowNode)||(link.dataset.flowTarget===node&&link.dataset.flowSource===item.dataset.flowNode))?1:.3):(item.dataset.flowNode===element.dataset.flowSource||item.dataset.flowNode===element.dataset.flowTarget?1:.3)));
        headline.textContent=Number(element.dataset.flowValue).toLocaleString();label.textContent=element.dataset.flowLabel!;
      };
      element.addEventListener('pointerenter',show);element.addEventListener('pointerleave',reset);element.addEventListener('focus',show);element.addEventListener('blur',reset);
    });
  });
}
