import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, expect, it, vi } from 'vitest';
import { checkboxHtml } from '@peach/legacy/ui';

const source=readFileSync(resolve(process.cwd(),'../web/app.js'),'utf8');
const manager=source.slice(source.indexOf('function followAliasManager('),source.indexOf('const CRED_STATE='));
const handlers=source.slice(source.indexOf('  const saveAuthorAlias='),source.indexOf("  root.querySelectorAll('[data-follow-guess]')"));
const esc=(value:unknown)=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
function fixture(api:ReturnType<typeof vi.fn>) {
  const root=document.createElement('div');document.body.append(root);
  const html=new Function('esc','icon','followAliasAvatar','emptyState','checkboxHtml',`${manager};return followAliasManager;`)(esc,()=>'',()=>'',()=>'',checkboxHtml);
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

it('勾选决定合并范围，表头全选支持取消与半选',async()=>{
  const api=vi.fn().mockResolvedValue({ok:true});
  const {root,confirmModal}=fixture(api);
  const fields=[...root.querySelectorAll<HTMLInputElement>('[data-follow-alias-select]')];
  const all=root.querySelector<HTMLInputElement>('[data-follow-alias-select-all]')!;
  const merge=root.querySelector<HTMLButtonElement>('[data-follow-alias-selected]')!;
  expect(merge.disabled).toBe(true);
  fields[0]!.click();
  expect(all.indeterminate).toBe(true);
  expect(merge.textContent).toBe('合并所选（1）');
  all.click();
  expect(fields.every(field=>field.checked)).toBe(true);
  all.click();
  expect(fields.every(field=>!field.checked)).toBe(true);
  expect(merge.disabled).toBe(true);
  fields[1]!.click();merge.click();
  expect(api).not.toHaveBeenCalled();
  const confirmation=confirmModal.mock.calls[0]![0];
  expect(confirmation.body).toContain('「别名 B」归入「作者 B」');
  expect(confirmation.body).not.toContain('别名 A');
  await confirmation.onConfirm();
  expect(api.mock.calls.map(call=>JSON.parse(call[1].body).alias)).toEqual(['别名 B']);
  expect(root.querySelector('[data-follow-alias-add]')?.getAttribute('data-alias')).toBe('别名 A');
});

it('别名表格保留依据、添加和移除，全部合并等待确认',async()=>{
  const api=vi.fn().mockResolvedValue({ok:true});
  const {root,confirmModal,refresh,receipt}=fixture(api);
  expect(root.querySelectorAll('table')).toHaveLength(2);
  expect(root.querySelector('[data-follow-alias-remove]')).not.toBeNull();
  expect(root.querySelector('#followAliasAdd')).not.toBeNull();
  expect(root.querySelector('.faliasheading h4')?.textContent).toBe('手动添加别名');
  expect(root.querySelector('summary')?.textContent).toContain('创作者别名');
  expect(root.querySelector('#followAliasAdd')!.compareDocumentPosition(root.querySelector('table')!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
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
