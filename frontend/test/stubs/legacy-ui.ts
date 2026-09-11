/* `/js/ui-components.js` 在测试里的替身（vitest.config.ts 里做 alias）。
 *
 * 只保留断言真正依赖的结构标记（`data-geist-empty-state`、`geist-note-error`）。
 * 完整的 Geist 结构由 `tests/test_web_ui.py` 直接对 `web/js/ui-components.js` 断言，
 * 这里再抄一遍只会多一处要维护的副本。 */
export const emptyStateHtml = (
  iconName: string,
  title: string,
  description: string,
  options: { actions?: string } = {},
): string => `<div class="emptystate" data-geist-empty-state role="status">`
  + `<div class="es-icon" data-icon="${iconName}"></div>`
  + `<div class="es-copy"><h3>${title}</h3><p>${description}</p></div>${options.actions || ''}</div>`;

// @ts-expect-error 横幅复用正式模板。
export {projectBannerHtml, collectionSummaryHtml} from '../../../web/js/ui-components.js';
export const fieldsetTitle = (id: string, title: string): string =>
  `<h3 class="geist-fieldset-title" id="${id}">${title}</h3>`;
export const loadingDotsHtml = (label: string): string => `<span>${label}</span>`;
export const checkboxHtml = (attrs = ''): string => `<span class="pcheck"><input type="checkbox" ${attrs}></span>`;
export const progressHtml = (label: string, value: number, max = 100): string =>
  `<progress role="progressbar" aria-label="${label}" value="${value}" max="${max}" aria-valuenow="${value}" aria-valuemax="${max}"></progress>`;
export const confirmModal = async (_options: unknown) => ({confirmed:false});

export const MEDIA_SOURCE_ICONS: Record<string,string> = {local:'hard-drive','115':'fixture-115',pikpak:'fixture-pikpak'};
export const selectOptionIconHtml = (mark?: string): string => mark ? `<i data-source-icon="${mark}"></i>` : '';

export const selectFieldHtml = (items: string[][], value: string, options: { label?: string } = {}): string =>
  `<div class="gselect" data-value="${value}"><button type="button" aria-haspopup="listbox" aria-label="${options.label}">${items.find(item => item[0] === value)?.[1]}</button></div>`;
export const wireSelectField = (root: HTMLElement) => {
  Object.defineProperty(root, 'value', { get: () => root.dataset.value, set: (value: string) => { root.dataset.value = value; } });
  return root as HTMLElement & { value: string; disabled: boolean };
};
export const wireCollapse = (_root: ParentNode, _selector: string, _idPrefix: string): void => {};
/* 只落位，不动画：jsdom 没有布局，量出来处处是零，那段弹簧也就没有什么可跑的。
   动作本身由 `tests/test_web_ui.py` 对 `web/js/ui-components.js` 直接断言。 */
export const moveGlidePane = (
  pane: HTMLElement,
  _from: unknown,
  box: { x: number; y: number; w: number; h: number },
): void => {
  pane.style.width = `${box.w}px`;
  pane.style.height = `${box.h}px`;
  pane.style.translate = `${box.x}px ${box.y}px`;
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

// @ts-expect-error 使用正式 Note 验证内部操作。
export {noteHtml} from '../../../web/js/ui-components.js';

export const badgeHtml = (text: string): string => `<span class="geist-badge">${text}</span>`;
