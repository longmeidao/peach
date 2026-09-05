/* `web/js/ui-components.js` 的类型声明。由 Peach 以 `/js/ui-components.js` 提供，不进 bundle。
 *
 * 这一层返回 HTML 字符串，island 里用 `dangerouslySetInnerHTML` 插入。它们内部已经
 * 对文本做转义，且是 Peach 唯一那份 Geist 控件实现——在 island 里另画一遍空态或 Note
 * 就是同一语义的第二份实现，`peach-web-ui` 的门槛不允许。 */

/** Geist Empty State：图标、标题与说明同处一个组件内。 */
export declare function emptyStateHtml(
  iconName: string,
  title: string,
  description: string,
  options?: { className?: string; actions?: string },
): string;

/** Geist Fieldset 的标题：放在框体里的 h3，不用原生 legend。 */
export declare function fieldsetTitle(id: string, title: string): string;

export declare function selectFieldHtml(items: string[][], current: string,
  options?: { label?: string; attr?: string; className?: string }): string;
export declare function wireSelectField(root: Element): HTMLElement & { value: string; disabled: boolean };

/** 用户触发的动作等待结果时的忙态：`aria-busy` 与 `aria-disabled` 一起写，控件仍可聚焦，
 *  重复触发由遗留层的 `wireBusyActions` 拦住。请求等待期不许改用原生 `disabled`。 */
export declare function setActionBusy(control: Element | null, busy?: boolean): void;

/** Geist Note：字段、卡片、分区旁的持久反馈。 */
export declare function noteHtml(
  message: string,
  options?: {
    variant?: 'secondary' | 'warning' | 'error' | 'success';
    label?: string;
    className?: string;
  },
): string;
