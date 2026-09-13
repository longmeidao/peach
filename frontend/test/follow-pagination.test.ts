import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, expect, it, vi } from 'vitest';
import { pageCount, clampPage, paginationHtml } from '../src/pagination';
import { selectionSummary, syncSelectionToolbar, selectGroup } from '../src/selection';

const source=readFileSync(resolve(process.cwd(),'../web/app.js'),'utf8');
const listing=source.slice(source.indexOf('function followSourceListHtml('),source.indexOf('function refreshFollowSourcePage('));
const sizes=source.match(/const FOLLOW_PAGE_SIZES=\[[^\]]+\];/)![0];
const groups=Array.from({length:25},(_,index)=>[{id:index*3+1},{id:index*3+2},{id:index*3+3}]);
function page(layout:string,current:number,size:number){
  const table=vi.fn(()=>'table');
  const render=new Function('followListLayout','followPageSize','pageCount','clampPage','followSourceTable','followAuthorBlock','selectFieldHtml','paginationHtml','followManagePage',`${sizes}${listing};return {html:followSourceListHtml(arguments[9]),page:followManagePage};`);
  return {table,...render(()=>layout,()=>size,pageCount,clampPage,table,(group:{id:number}[])=>`<article data-id="${group[0]!.id}"></article>`,()=>'',paginationHtml,current,groups)};
}
afterEach(()=>document.body.replaceChildren());

it('默认视图保持创作者组完整，越界页落到末页',()=>{
  const result=page('default',9,20),root=document.createElement('div');root.innerHTML=result.html;
  expect(result.page).toBe(2);
  expect(root.querySelectorAll('article')).toHaveLength(5);
  expect(root.querySelector('article')?.dataset.id).toBe('61');
  expect(root.textContent).toContain('21–25 / 25 位创作者');
});

it('表格按来源总数分页并传递范围',()=>{
  const result=page('table',8,10);
  expect(result.page).toBe(8);
  expect(result.table).toHaveBeenCalledWith(groups,true,8,10);
  expect(result.html).toContain('71–75 / 75 个来源');
});

it('表格先按来源全量排序，再截取页内行',()=>{
  const tableSource=source.slice(source.indexOf('function followSourceTable('),source.indexOf('function followAliasManager('));
  const render=new Function('FOLLOW_SOURCE_SORTS','followManageSort','followManageDir','FOLLOW_SORT_DEFAULT_DIR','followAuthorName','followSourceCells','followTableHeader','followAuthorAvatar','esc',`${tableSource};return followSourceTable;`)(
    {source:(a:{id:number},b:{id:number})=>a.id-b.id},'source','asc',{source:'asc'},()=>'',(row:{id:number})=>({className:'fsource',check:'',name:String(row.id),error:'',provider:()=>'',status:'',checked:'',actions:''}),()=>'',()=>'',String,
  );
  const root=document.createElement('div');root.innerHTML=render([[{id:4},{id:1}],[{id:3},{id:2}]],true,2,2);
  expect([...root.querySelectorAll('.ftname')].map(cell=>cell.textContent)).toEqual(['3','4']);
});

it('跨页选择用于批量动作，本页全选只作用于当前行，取消选择清空全部',()=>{
  const root=document.createElement('div');document.body.append(root);
  root.innerHTML='<label><input type="checkbox" data-follow-select-all></label><div class="fsource"><input type="checkbox" data-follow-select="2"></div><div class="followselectiondock"><span data-follow-selected-count></span><button data-follow-selection-action data-follow-check></button><button data-follow-selection-clear></button></div>';
  const selection=new Set([1]);
  const segment=source.slice(source.indexOf('  const selectable=[...root.querySelectorAll(\'[data-follow-select]\')]'),source.indexOf('  wireScrollers(root);',source.indexOf('function wireFollowManage(')));
  new Function('root','followData','followSourceSelection','followRuntime','selectionSummary','syncSelectionToolbar','selectGroup',segment)(root,{sources:[{id:1},{id:2}]},selection,{},selectionSummary,syncSelectionToolbar,selectGroup);
  const all=root.querySelector<HTMLInputElement>('[data-follow-select-all]')!;
  const action=root.querySelector<HTMLButtonElement>('[data-follow-check]')!;
  expect(all.checked).toBe(false);
  expect(action.disabled).toBe(false);
  expect(action.dataset.followSources).toBe('1');
  all.click();expect([...selection]).toEqual([1,2]);
  all.click();expect([...selection]).toEqual([1]);
  root.querySelector<HTMLButtonElement>('[data-follow-selection-clear]')!.click();
  expect(selection.size).toBe(0);
  expect(root.querySelector<HTMLElement>('.followselectiondock')!.hidden).toBe(true);
  expect(action.disabled).toBe(true);
});
