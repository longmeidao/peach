import { useLayoutEffect, useRef, useState } from 'preact/hooks';
import { fieldsetTitle, setActionBusy, confirmModal, wireCollapse } from '@peach/legacy/ui';
import { icon } from '@peach/legacy/core';
import { apiSend, errorMessage } from '../api';

export interface StartupState { available: boolean; enabled: boolean; silent: boolean; message: string }
export interface UninstallState { available: boolean; full_available: boolean; message: string; data_root: string; directories: string[] }

function SettingCheck({ label, checked, disabled, change }: { label:string; checked:boolean; disabled:boolean; change(value:boolean):void }) {
  return <label class="configcheck"><span class="pcheck"><input type="checkbox" checked={checked} disabled={disabled} onChange={event=>change(event.currentTarget.checked)} />
    <span aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-check" /></svg></span></span><span>{label}</span></label>;
}

function SettingToggle({ label, checked, disabled, change }: { label:string; checked:boolean; disabled:boolean; change(value:boolean):void }) {
  return <label class="configtoggle"><span>{label}</span><input class="ptoggle" type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={event=>change(event.currentTarget.checked)} /></label>;
}

export function StartupSettings({ startup, receipt }: { startup: StartupState; receipt(message: string): void }) {
  const [enabled,setEnabled] = useState(startup.enabled);
  const [silent,setSilent] = useState(startup.silent);
  const [error,setError] = useState('');
  const busy = useRef(false);
  const button = useRef<HTMLButtonElement>(null);
  async function save() {
    if (busy.current) return;
    busy.current = true; setActionBusy(button.current,true); setError('');
    try { await apiSend('/api/configuration/startup',{enabled,silent}); receipt('已保存开机自启'); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { busy.current = false; setActionBusy(button.current,false); }
  }
  return (
    <form class="configfieldset" data-geist-fieldset onSubmit={event=>{event.preventDefault();void save();}}>
      <div class="geist-fieldset-content">
        <div dangerouslySetInnerHTML={{__html:fieldsetTitle('startupTitle','开机自启')}} />
        <div class="configoptions" role="group" aria-labelledby="startupTitle">
          <SettingToggle label="开机后启动 Peach" checked={enabled} disabled={!startup.available} change={setEnabled} />
          <div class="configoption"><SettingToggle label="静默启动" checked={silent} disabled={!startup.available} change={setSilent} />
            <p class="confighelp">静默启动仅显示托盘。</p></div>
        </div>
        {startup.message && <p class="confighelp">{startup.message}</p>}
        {error && <p class="configbad" role="alert">{error}</p>}
      </div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button ref={button} type="submit" class="geist-button primary" disabled={!startup.available}>保存配置</button></footer>
    </form>
  );
}

function DataDirectories({ data }: { data: UninstallState }) {
  const mount = useRef<HTMLDivElement>(null);
  useLayoutEffect(()=>{
    const root=mount.current!;
    const details=document.createElement('details');details.className='configdirectories';
    const summary=document.createElement('summary');summary.innerHTML=icon('chevron-right')+'<span>数据目录</span>';
    details.append(summary);
    for(const path of [...new Set([data.data_root,...data.directories])]) {
      const line=document.createElement('p');line.className='confighelp';line.textContent=path;details.append(line);
    }
    root.replaceChildren(details);wireCollapse(root,'details','uninstall-data');
    return ()=>root.replaceChildren();
  },[data]);
  return <div ref={mount} />;
}

export function UninstallSettings({ uninstall }: { uninstall: UninstallState }) {
  const [removeData,setRemoveData] = useState(false);
  const [accepted,setAccepted] = useState('');
  async function remove() {
    await confirmModal({title:'卸载 Peach',danger:true,body:removeData
      ? '将退出 Peach，移除程序、开机自启、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。'
      : '将退出 Peach 并移除程序和开机自启。设置、本地数据库、观看记录与缓存保留。',
    confirmLabel:'卸载 Peach',onConfirm:async () => {
      const result = await apiSend<{message:string}>('/api/configuration/uninstall',{delete_data:removeData,confirmation:'卸载 Peach'});
      setAccepted(result.message);
    }});
  }
  return <section id="uninstallPeach" class="configfieldset configdanger" data-geist-fieldset data-fieldset-type="error">
      <div class="geist-fieldset-content">
        <div dangerouslySetInnerHTML={{__html:fieldsetTitle('uninstallTitle','卸载 Peach')}} />
        {uninstall.available && <p class="confighelp">卸载会退出 Peach、移除程序和开机自启。原始媒体文件保留。</p>}
        <SettingCheck label="完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存" checked={removeData} disabled={!uninstall.full_available || !!accepted} change={setRemoveData} />
        <DataDirectories data={uninstall} />
        {uninstall.message && <p class="confighelp">{uninstall.message}</p>}
        {accepted && <p class="confighelp" role="status">{accepted}</p>}
      </div>
      <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" class="geist-button danger" disabled={!uninstall.available || !!accepted} onClick={()=>void remove()}>卸载 Peach</button></footer>
    </section>;
}
