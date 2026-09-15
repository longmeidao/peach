/* React 子树的构建入口（`web/dist/peach-react.js`），按 `bundle.d.ts` 的签名导出挂载函数。 */
import './styles.css';

import type { ComponentType } from 'react';
import { createRoot } from 'react-dom/client';

import type * as Bundle from './bundle';
import { AccessSettings } from './settings/access-settings';

function mounter<P extends object>(Component: ComponentType<P>) {
  return (el: Element, props: P): Bundle.ReactMount<P> => {
    const root = createRoot(el);
    const paint = (next: P) => root.render(<Component {...next} />);
    paint(props);
    return { update: paint, unmount: () => root.unmount() };
  };
}

export const mountAccessSettings: typeof Bundle.mountAccessSettings = mounter(AccessSettings);
