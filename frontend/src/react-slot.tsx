/* Preact island 与 React 子树的交接点。
 *
 * Preact 只画一个空的 `.peach-react` 容器，React 根挂在它里面：Preact 的 diff 只处理自己
 * 画过的子节点，React 画进去的 DOM 它不碰。React 产物在第一次用到时才加载，
 * 没有 React 子树的页面不取 `peach-react.js`。 */
import { useEffect, useRef, useState } from 'preact/hooks';
import type * as ReactBundle from '@peach/react';

type MountName = 'mountAccessSettings';
type PropsOf<N extends MountName> = Parameters<(typeof ReactBundle)[N]>[1];

export function ReactSlot<N extends MountName>({ mount, props }: { mount: N; props: PropsOf<N> }) {
  const host = useRef<HTMLDivElement>(null);
  const root = useRef<ReactBundle.ReactMount<PropsOf<N>> | null>(null);
  const latest = useRef(props);
  latest.current = props;
  const [failure, setFailure] = useState('');

  useEffect(() => {
    let cancelled = false;
    import('@peach/react').then((bundle) => {
      if (cancelled || !host.current) return;
      const create = bundle[mount] as (el: Element, next: PropsOf<N>) => ReactBundle.ReactMount<PropsOf<N>>;
      root.current = create(host.current, latest.current);
    }, (cause: unknown) => {
      if (!cancelled) setFailure(cause instanceof Error ? cause.message : String(cause));
    });
    return () => {
      cancelled = true;
      root.current?.unmount();
      root.current = null;
    };
  }, [mount]);

  useEffect(() => { root.current?.update(props); });

  return failure
    ? <p class="configbad" role="alert">界面组件没有加载：{failure}</p>
    : <div ref={host} class="peach-react" />;
}
