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
export declare function collectionSummaryHtml(label: string, value: string, detail?: string): string;
export declare function badgeHtml(text: string): string;
export declare function checkboxHtml(inputAttrs?: string): string;
export declare function loadingDotsHtml(label?: string, options?: { className?: string }): string;
export declare function progressHtml(label: string, value: number, max?: number, options?:{variant?:'active'|'warning'|'error';stops?:{value:number;label:string}[]}): string;
export declare function confirmModal(options: {title: string; body: string; confirmLabel: string; cancelLabel?: string; danger?: boolean; onConfirm?: () => Promise<unknown>}): Promise<{confirmed: boolean; result?: unknown}>;

export declare function selectFieldHtml(items: string[][], current: string,
  options?: { label?: string; attr?: string; className?: string }): string;
export declare function wireSelectField(root: Element): HTMLElement & { value: string; disabled: boolean };
export declare function wireCollapse(root: ParentNode, selector: string, idPrefix: string, triggerSelector?: string): void;
/** 共用 Collapse 的开合：`body` 是带 `.fcollapse` 的那层，高度按它的过渡长到或收到位。 */
export declare function setCollapseOpen(details: HTMLDetailsElement, body: HTMLElement, expanded: boolean): void;
/** 一排里标出「当前是哪一个」的那块底板换位；`from` 给 null 只落位不动画。 */
export declare function moveGlidePane(
  pane: HTMLElement,
  from: { x: number; y: number; w: number; h: number } | null,
  box: { x: number; y: number; w: number; h: number },
  axis?: 'x' | 'y',
): void;
export declare const MEDIA_SOURCE_ICONS: Record<string, string>;
export declare function selectOptionIconHtml(mark?: string): string;

/** 全站那条覆盖式滚动条：滑块浮在内容上，一列宽度都不占。
 *
 * 轨道是滚动容器的兄弟，挂在它父元素上，所以那个父元素得只裹着这一个滚动容器。
 * 容器自己的尺寸与子树变化它盯着，返回的函数留给「两者都没变但要重算」的情形。
 * 遗留层那份按名单批量挂的是 `wireOverlayScrollbars`；island 自己画的 DOM 不在
 * 那份名单的扫描范围里，挂到哪一层由 island 自己说。 */
export declare function attachOverlayScrollbar(
  container: Element | null,
  options?: { variant?: string },
): (() => void) | null;

/** 用户触发的动作等待结果时的忙态：`aria-busy` 与 `aria-disabled` 一起写，控件仍可聚焦，
 *  重复触发由遗留层的 `wireBusyActions` 拦住。请求等待期不许改用原生 `disabled`。 */
export declare function setActionBusy(control: Element | null, busy?: boolean): void;
export declare function wireAnchoredMenu(mount: Element, toggle: Element, menu: Element): {setOpen(open: boolean): void; isOpen(): boolean};

/** Geist Note：字段、卡片、分区旁的持久反馈。 */
export declare function noteHtml(
  message: string,
  options?: {
    variant?: 'secondary' | 'warning' | 'error' | 'success';
    label?: string;
    className?: string;
    size?: 'small' | 'medium';
    actionLabel?:string; filled?: boolean;
    /** 恢复动作要离开本页才做得成时给出目标地址，动作由按钮换成同格子的链接。 */
    actionHref?: string;
    /** 逐条明细，收在 Note 里默认折叠的 details；`hint` 放路径这类次要标注。 */
    details?: {
      label: string;
      items: { label: string; href?: string; note?: string; hint?: string }[];
      footnote?: string;
    } | null;
  },
): string;
export declare function projectBannerHtml(message:string,options:{variant?:'gray'|'success'|'warning'|'error';href:string;label:string;value?:number;max?:number}):string;
