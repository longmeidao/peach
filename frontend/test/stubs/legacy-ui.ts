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

export const noteHtml = (
  message: string,
  options: { variant?: string; label?: string } = {},
): string => `<div class="geist-note geist-note-${options.variant ?? 'secondary'}" role="note">`
  + `<b>${options.label ?? ''}</b><span>${message}</span></div>`;
