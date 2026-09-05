/* `/js/ui-components.js` 在测试里的替身（vitest.config.ts 里做 alias）。
 *
 * 只保留断言真正依赖的结构标记（`data-geist-empty-state`、`geist-note-error`）。
 * 完整的 Geist 结构由 `tests/test_web_ui.py` 直接对 `web/js/ui-components.js` 断言，
 * 这里再抄一遍只会多一处要维护的副本。 */
export const emptyStateHtml = (
  iconName: string,
  title: string,
  description: string,
): string => `<div class="emptystate" data-geist-empty-state role="status">`
  + `<div class="es-icon" data-icon="${iconName}"></div>`
  + `<div class="es-copy"><h3>${title}</h3><p>${description}</p></div></div>`;

export const fieldsetTitle = (id: string, title: string): string =>
  `<h3 class="geist-fieldset-title" id="${id}">${title}</h3>`;

export const MEDIA_SOURCE_ICONS: Record<string,string> = {local:'hard-drive','115':'fixture-115',pikpak:'fixture-pikpak'};
export const selectOptionIconHtml = (mark?: string): string => mark ? `<i data-source-icon="${mark}"></i>` : '';

export const selectFieldHtml = (items: string[][], value: string, options: { label?: string } = {}): string =>
  `<div class="gselect" data-value="${value}"><button type="button" aria-haspopup="listbox" aria-label="${options.label}">${items.find(item => item[0] === value)?.[1]}</button></div>`;
export const wireSelectField = (root: HTMLElement) => {
  Object.defineProperty(root, 'value', { get: () => root.dataset.value, set: (value: string) => { root.dataset.value = value; } });
  return root as HTMLElement & { value: string; disabled: boolean };
};

export const setActionBusy = (control: Element | null, busy = true): void => {
  if (!control) return;
  if (busy) {
    control.setAttribute('aria-busy', 'true');
    control.setAttribute('aria-disabled', 'true');
  } else {
    control.removeAttribute('aria-busy');
    control.removeAttribute('aria-disabled');
  }
};

export const noteHtml = (
  message: string,
  options: { variant?: string; label?: string } = {},
): string => `<div class="geist-note geist-note-${options.variant ?? 'secondary'}" role="note">`
  + `<b>${options.label ?? ''}</b><span>${message}</span></div>`;
