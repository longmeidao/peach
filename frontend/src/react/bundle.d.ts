/* `web/dist/peach-react.js` 的对外契约。
 *
 * Preact 那一侧按 `@peach/react` 引用这份产物，构建时改写成 `/dist/peach-react.js`；
 * `entry.tsx` 按这里的签名实现，两边的类型检查各自对照同一份声明。 */

export interface AccessState { mode: 'open' | 'password' | 'legacy' | 'locked'; revision: string }

export interface AccessSettingsProps {
  initial: AccessState;
  receipt(message: string): void;
}

/** 一棵挂在遗留容器里的 React 根。`unmount` 之后容器归还给挂载方。 */
export interface ReactMount<P> {
  update(props: P): void;
  unmount(): void;
}

export declare function mountAccessSettings(el: Element, props: AccessSettingsProps): ReactMount<AccessSettingsProps>;
