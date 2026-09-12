import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, expect, it, vi } from 'vitest';

const source=readFileSync(resolve(process.cwd(),'../web/app.js'),'utf8');
const manager=source.slice(source.indexOf('function followAliasManager('),source.indexOf('const CRED_STATE='));
const handlers=source.slice(source.indexOf('  const saveAuthorAlias='),source.indexOf("  root.querySelectorAll('[data-follow-guess]')"));
const esc=(value:unknown)=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
function fixture(api:ReturnType<typeof vi.fn>) {
  const root=document.createElement('div');document.body.append(root);
  const html=new Function('esc','icon','followAliasAvatar','emptyState',`${manager};return followAliasManager;`)(esc,()=>'',()=>'',()=>'');
  root.innerHTML=html([{canonical_name:'作者 A',aliases:[{name:'已存别名'}]}],[
    {canonical:'作者 A',alias:'别名 A',evidence:'来源 A'},
    {canonical:'作者 B',alias:'别名 B',evidence:'来源 B'},
  ]);
  const confirmModal=vi.fn(),refresh=vi.fn(),receipt=vi.fn();
  new Function('root','api','confirmModal','setActionBusy','openFollowManage','actionReceipt','actionFailure',handlers)(
    root,api,confirmModal,(button:HTMLElement,busy=true)=>button.setAttribute('aria-busy',String(busy)),refresh,receipt,vi.fn());
  return {root,confirmModal,refresh,receipt};
}
afterEach(()=>document.body.replaceChildren());

it('别名表格保留依据、添加和移除，全部合并等待确认',async()=>{
  const api=vi.fn().mockResolvedValue({ok:true});
  const {root,confirmModal,refresh,receipt}=fixture(api);
  expect(root.querySelectorAll('table')).toHaveLength(2);
  expect(root.querySelector('[data-follow-alias-remove]')).not.toBeNull();
  expect(root.querySelector('#followAliasAdd')).not.toBeNull();
  root.querySelector<HTMLButtonElement>('[data-follow-alias-all]')!.click();
  expect(api).not.toHaveBeenCalled();
  expect(confirmModal.mock.calls[0]![0].body).toContain('「别名 A」归入「作者 A」');
  await confirmModal.mock.calls[0]![0].onConfirm();
  expect(api.mock.calls.map(call=>JSON.parse(call[1].body))).toEqual([
    {action:'add',canonical:'作者 A',alias:'别名 A'},
    {action:'add',canonical:'作者 B',alias:'别名 B'},
  ]);
  expect(refresh).toHaveBeenCalledOnce();expect(receipt).toHaveBeenCalledOnce();
});

it('批量合并失败后重试只提交未完成别名',async()=>{
  const api=vi.fn().mockResolvedValueOnce({ok:true}).mockRejectedValueOnce(new Error('连接中断')).mockResolvedValue({ok:true});
  const {root,confirmModal,refresh}=fixture(api);
  root.querySelector<HTMLButtonElement>('[data-follow-alias-all]')!.click();
  const confirm=confirmModal.mock.calls[0]![0].onConfirm;
  await expect(confirm()).rejects.toThrow('还有 1 组未合并');
  expect(refresh).not.toHaveBeenCalled();
  expect(root.querySelectorAll('[data-follow-alias-add]')).toHaveLength(1);
  await confirm();
  expect(api.mock.calls.map(call=>JSON.parse(call[1].body).alias)).toEqual(['别名 A','别名 B','别名 B']);
  expect(refresh).toHaveBeenCalledOnce();
});
