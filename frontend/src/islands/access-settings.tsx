/** 本机访问密码；表单值只留在提交期间的组件内存中。 */
import { useRef, useState } from 'preact/hooks';
import type { JSX } from 'preact';
import { noteHtml } from '@peach/legacy/ui';
import { SettingsSection, useSubmitAction } from '../settings-controls';
import { ApiError, apiSend, errorMessage } from '../api';

export interface AccessState { mode: 'open' | 'password' | 'legacy' | 'locked'; revision: string }
type FieldErrors = Partial<Record<'current_password' | 'password' | 'confirmation', string>>;

function PasswordField({ id, label, value, onInput, error, help, current = false, disabled = false }: {
  id: string; label: string; value: string; onInput(value: string): void; error?: string | undefined; help?: string; current?: boolean; disabled?: boolean;
}) {
  return <div class="configfield">
    <label for={id}>{label}</label>
    <input id={id} class="geist-input" type="password" autoComplete={current ? 'current-password' : 'new-password'}
      maxLength={256} value={value} onInput={(event) => onInput(event.currentTarget.value)} required={!disabled} disabled={disabled}
      aria-invalid={Boolean(error)} aria-describedby={error || help ? `${id}-hint` : undefined} />
    {error || help ? <p id={`${id}-hint`} class={error ? 'configbad' : 'confighelp'} role={error ? 'alert' : undefined}>{error || help}</p> : null}
  </div>;
}

export function AccessSettings({ initial, receipt }: { initial: AccessState; receipt(message: string): void }) {
  const [state, setState] = useState(initial);
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [disable, setDisable] = useState(false);
  const [fields, setFields] = useState<FieldErrors>({});
  const form = useRef<HTMLFormElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const {run, error, setError, busy} = useSubmitAction(button);
  const submit = async (event: JSX.TargetedEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busy.current) return;
    setError('');
    const issues: FieldErrors = {};
    if (state.mode === 'password' && !current) issues.current_password = '请输入当前访问密码';
    if (!disable) {
      if (password.length < 8 || password.length > 256) issues.password = '访问密码需为 8–256 个字符';
      if (password !== confirmation) issues.confirmation = '两次输入的密码不一致';
    }
    setFields(issues);
    if (Object.keys(issues).length) {
      requestAnimationFrame(() => form.current?.querySelector<HTMLInputElement>('[aria-invalid="true"]')?.focus());
      return;
    }
    await run(signal => apiSend<AccessState>('/api/configuration/access', {
        revision: state.revision, action: disable ? 'disable' : 'set', confirm_disable: disable,
        current_password: current, password: disable ? '' : password, confirmation: disable ? '' : confirmation,
      }, 'POST', signal), next => {
      setState(next); setCurrent(''); setPassword(''); setConfirmation(''); setDisable(false); setFields({});
      receipt(next.mode === 'open' ? '已关闭访问密码' : '已保存访问密码');
    }, cause => {
      const payload = cause instanceof ApiError ? cause.body as { errors?: FieldErrors; detail?: { errors?: FieldErrors } } : null;
      const errors = payload?.errors || payload?.detail?.errors;
      if (errors) setFields(errors); else setError(errorMessage(cause));
    });
  };
  return <SettingsSection titleId="accessTitle" title="访问密码" warning={disable} onSubmit={submit} noValidate formRef={form} error={error}
    help={state.mode === 'open' ? '未设置密码，能连接到 Peach 的设备可直接访问。' : state.mode === 'legacy' ? '当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。' : state.mode === 'locked' ? '访问设置无法读取，请在本机检查配置文件。' : '已设置密码。新设备需要登录，保持登录时间在登录页选择。'}
    footer={state.mode !== 'locked' && <><p>保存后立即生效。</p><button class="geist-button primary" type="submit" ref={button}>保存配置</button></>}>
      {state.mode === 'password' || state.mode === 'legacy' ? <label class="configcheck"><span class="pcheck"><input type="checkbox" checked={disable} onChange={(event) => setDisable(event.currentTarget.checked)} /><span aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-check" /></svg></span></span><span>关闭访问密码，允许能连接到 Peach 的设备直接访问</span></label> : null}
      {state.mode === 'password' ? <PasswordField id="access-current" label="当前访问密码" value={current} onInput={setCurrent} error={fields.current_password} current /> : null}
      {state.mode !== 'locked' ? <>
        <PasswordField id="access-password" label={state.mode === 'password' ? '新访问密码' : '设置访问密码'} value={password} onInput={setPassword} disabled={disable} error={disable ? undefined : fields.password} help={disable ? '关闭访问密码时无需填写。' : '至少 8 个字符。保存后其他设备需要重新登录。'} />
        <PasswordField id="access-confirm" label="确认访问密码" value={confirmation} onInput={setConfirmation} disabled={disable} error={disable ? undefined : fields.confirmation} />
      </> : null}
      {disable && <div dangerouslySetInnerHTML={{__html:noteHtml('保存后，能连接到 Peach 的设备将直接访问馆藏。',{variant:'warning',label:'访问范围'})}} />}
  </SettingsSection>;
}
