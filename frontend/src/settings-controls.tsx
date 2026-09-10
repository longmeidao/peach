import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import type { ComponentChildren, JSX, RefObject } from 'preact';
import { fieldsetTitle, selectFieldHtml, wireSelectField, setActionBusy } from '@peach/legacy/ui';
import { errorMessage } from './api';

/** 遗留 Select 的受控适配，挂载和事件各归一个生命周期。 */
export function SelectField({ value, options, label, onChange, disabled = false, className = '', fixed = false }: {
  value: string; options: string[][]; label: string; onChange(value: string): void;
  disabled?: boolean; className?: string; fixed?: boolean;
}) {
  const mount = useRef<HTMLDivElement>(null);
  const control = useRef<ReturnType<typeof wireSelectField> | null>(null);
  const callback = useRef(onChange); callback.current = onChange;
  const signature = JSON.stringify(options);
  useLayoutEffect(() => {
    const root = mount.current!;
    root.innerHTML = selectFieldHtml(options, value, { label, className: 'configselect', attr: fixed ? 'data-fixed-width' : '' });
    const field = wireSelectField(root.firstElementChild!); control.current = field;
    const change = () => callback.current(field.value);
    field.addEventListener('change', change);
    return () => { field.disabled = true; field.removeEventListener('change', change); control.current = null; root.replaceChildren(); };
  }, [signature, label, fixed]);
  useLayoutEffect(() => { if (control.current) { control.current.value = value; control.current.disabled = disabled; } }, [value, disabled, signature, label, fixed]);
  return <div ref={mount} class={className} />;
}

/** 写入只执行一次，离页取消等待，结果只交给仍挂载的表单。 */
export function useSubmitAction(button: RefObject<HTMLButtonElement>, initialError = '') {
  const busy = useRef(false);
  const lifetime = useRef(new AbortController());
  const [error, setError] = useState(initialError);
  useEffect(() => () => lifetime.current.abort(), []);
  async function run<T>(write: (signal: AbortSignal) => Promise<T>, success: (result: T) => void,
    failure?: (cause: unknown) => void) {
    if (busy.current || lifetime.current.signal.aborted) return;
    busy.current = true; setError(''); setActionBusy(button.current, true);
    try {
      const result = await write(lifetime.current.signal);
      if (!lifetime.current.signal.aborted) success(result);
    } catch (cause) {
      if (!lifetime.current.signal.aborted) { if (failure) failure(cause); else setError(errorMessage(cause)); }
    } finally { busy.current = false; if (!lifetime.current.signal.aborted) setActionBusy(button.current, false); }
  }
  return { run, error, setError, busy };
}

export function SettingsSection({ id, titleId, title, help, error, children, footer, onSubmit, formRef, noValidate, warning }: {
  id?: string; titleId: string; title: string; help?: ComponentChildren; error?: string;
  children: ComponentChildren; footer: ComponentChildren; onSubmit: JSX.GenericEventHandler<HTMLFormElement>;
  formRef?: RefObject<HTMLFormElement>; noValidate?: boolean; warning?: boolean;
}) {
  return <form id={id} class="configfieldset" data-geist-fieldset data-fieldset-type={warning ? 'warning' : undefined}
    aria-labelledby={titleId} onSubmit={onSubmit} ref={formRef ?? null} noValidate={noValidate}>
    <div class="geist-fieldset-content">
      <div class="configfieldset-heading"><div dangerouslySetInnerHTML={{ __html: fieldsetTitle(titleId, title) }} />
        {help && <p class="confighelp">{help}</p>}</div>
      {children}{error && <p class="configbad" role="alert">{error}</p>}
    </div>
    {footer && <footer class="geist-fieldset-footer" data-geist-fieldset-footer>{footer}</footer>}
  </form>;
}
