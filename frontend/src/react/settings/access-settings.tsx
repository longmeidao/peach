/* 本机访问密码，由 BoardUI 原版组件组合；表单值只留在提交期间的组件内存中。
 *
 * 分区外观取 BoardUI 设置弹层的 `SettingsSectionLabel` + `SettingsCard`，字段是 BoardUI
 * `Input`（React Aria TextField），开关是 BoardUI `Checkbox`，提交键是 BoardUI `Button`。
 * BoardUI 没有行内持久提示组件，`Warning` 用它的黄色状态 token 组合。 */
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';

import { SettingsCard, SettingsSectionLabel } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { Checkbox } from '@/components/base/checkbox/checkbox';
import { Input } from '@/components/base/input/input';

import { ApiError, apiSend, errorMessage } from '../../api';
import type { AccessSettingsProps, AccessState } from '../bundle';

type FieldErrors = Partial<Record<'current_password' | 'password' | 'confirmation', string>>;

const HELP: Partial<Record<AccessState['mode'], string>> = {
  legacy: '当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。',
  locked: '访问设置无法读取，请在本机检查配置文件。',
  password: '已设置密码。新设备需要登录，保持登录时间在登录页选择。',
};

/** 持久警示。没有密码是这台机器当前的状态，不是填表提示，所以不和字段说明共用灰色小字。 */
function Warning({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div role="note" className="flex flex-col gap-0.5 rounded-2lg bg-status-yellow-background px-3 py-2 text-status-yellow-text">
      <p className="text-body-medium">{label}</p>
      <p className="text-body-2-regular">{children}</p>
    </div>
  );
}

export function AccessSettings({ initial, receipt }: AccessSettingsProps) {
  const [state, setState] = useState(initial);
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [disable, setDisable] = useState(false);
  const [fields, setFields] = useState<FieldErrors>({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const form = useRef<HTMLFormElement>(null);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (pending.current) return;
    setError('');
    const issues: FieldErrors = {};
    if (state.mode === 'password' && !current) issues.current_password = '请输入当前访问密码';
    if (!disable) {
      if (password.length < 8 || password.length > 256) issues.password = '访问密码需为 8–256 个字符';
      if (password !== confirmation) issues.confirmation = '两次输入的密码不一致';
    }
    setFields(issues);
    if (Object.keys(issues).length) {
      requestAnimationFrame(() => form.current?.querySelector<HTMLInputElement>('input[aria-invalid="true"]')?.focus());
      return;
    }
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true);
    try {
      const next = await apiSend<AccessState>('/api/configuration/access', {
        revision: state.revision, action: disable ? 'disable' : 'set', confirm_disable: disable,
        current_password: current, password: disable ? '' : password, confirmation: disable ? '' : confirmation,
      }, 'POST', controller.signal);
      if (controller.signal.aborted) return;
      setState(next); setCurrent(''); setPassword(''); setConfirmation(''); setDisable(false); setFields({});
      receipt(next.mode === 'open' ? '已关闭访问密码' : '已保存访问密码');
    } catch (cause) {
      if (controller.signal.aborted) return;
      const payload = cause instanceof ApiError ? cause.body as { errors?: FieldErrors; detail?: { errors?: FieldErrors } } : null;
      const errors = payload?.errors || payload?.detail?.errors;
      if (errors) setFields(errors); else setError(errorMessage(cause));
    } finally {
      if (pending.current === controller) pending.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  };

  const help = HELP[state.mode];
  const editable = state.mode !== 'locked';
  return (
    <form ref={form} aria-label="访问密码" noValidate onSubmit={submit} className="flex w-full flex-col gap-2">
      <SettingsSectionLabel>访问密码</SettingsSectionLabel>
      <SettingsCard>
        {/* 卡片只管左内边距和底色；这里放的不是 SettingsRow，行距和上下内边距由这一层给。 */}
        <div className="flex flex-col gap-4 py-4 pr-3">
          {help ? <p className="text-body-2-regular text-text-secondary">{help}</p> : null}
          {state.mode === 'open'
            ? <Warning label="未设置访问密码">能连接到 Peach 的设备打开地址就能看馆藏，不需要登录。</Warning>
            : null}
          {state.mode === 'password' || state.mode === 'legacy'
            ? <Checkbox isSelected={disable} onChange={setDisable}>关闭访问密码，允许能连接到 Peach 的设备直接访问</Checkbox>
            : null}
          {state.mode === 'password'
            ? <Input id="access-current" type="password" label="当前访问密码" autoComplete="current-password" maxLength={256}
                value={current} onChange={setCurrent} isRequired validationBehavior="aria"
                isInvalid={Boolean(fields.current_password)} hint={fields.current_password} />
            : null}
          {editable ? <>
            <Input id="access-password" type="password" label={state.mode === 'password' ? '新访问密码' : '设置访问密码'}
              autoComplete="new-password" maxLength={256} value={password} onChange={setPassword}
              isDisabled={disable} isRequired={!disable} validationBehavior="aria"
              isInvalid={!disable && Boolean(fields.password)}
              hint={disable ? '关闭访问密码时无需填写。' : fields.password || '至少 8 个字符。保存后其他设备需要重新登录。'} />
            <Input id="access-confirm" type="password" label="确认访问密码" autoComplete="new-password" maxLength={256}
              value={confirmation} onChange={setConfirmation} isDisabled={disable} isRequired={!disable} validationBehavior="aria"
              isInvalid={!disable && Boolean(fields.confirmation)} hint={disable ? undefined : fields.confirmation} />
          </> : null}
          {disable ? <Warning label="访问范围">保存后，能连接到 Peach 的设备将直接访问馆藏。</Warning> : null}
          {error ? <p role="alert" className="text-body-2-regular text-text-error-primary">{error}</p> : null}
          {editable
            ? <div className="flex items-center justify-between gap-4 border-t border-separator-border pt-3">
                <p className="text-body-2-regular text-text-secondary">保存后立即生效。</p>
                <Button type="submit" aria-busy={busy || undefined} aria-disabled={busy || undefined}>保存配置</Button>
              </div>
            : null}
        </div>
      </SettingsCard>
    </form>
  );
}
