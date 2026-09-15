/* React 子树的构建入口（`web/dist/peach-react.js`），按 `bundle.d.ts` 的签名导出挂载函数。 */
import './styles.css';

import type { ComponentType } from 'react';
import { UNSAFE_PortalProvider } from 'react-aria';
import { createRoot } from 'react-dom/client';

import type * as Bundle from './bundle';
import { GeneralSettings } from './settings/general-settings';
import { MaintenanceSettings } from './settings/maintenance-settings';
import { MediaSettings } from './settings/media-settings';
import { NetworkSettings } from './settings/network-settings';

/* Popover 这类弹出层由 React Aria 渲染到挂载容器外面。落在 `body` 上就出了 `.peach-react`
 * 的作用域：token 读到的是 `board.css` 的值，Preflight 也管不到。所有 React 根的弹出层都进
 * `body` 末尾这一个同样带 `.peach-react` 的容器。 */
let overlays: HTMLElement | null = null;
function overlayContainer(): HTMLElement {
  if (!overlays?.isConnected) {
    overlays = document.createElement('div');
    overlays.className = 'peach-react';
    overlays.dataset.reactOverlays = '';
    document.body.append(overlays);
  }
  return overlays;
}

function mounter<P extends object>(Component: ComponentType<P>) {
  return (el: Element, props: P): Bundle.ReactMount<P> => {
    const root = createRoot(el);
    const paint = (next: P) => root.render(
      <UNSAFE_PortalProvider getContainer={overlayContainer}><Component {...next} /></UNSAFE_PortalProvider>,
    );
    paint(props);
    return { update: paint, unmount: () => root.unmount() };
  };
}

export const mountGeneralSettings: typeof Bundle.mountGeneralSettings = mounter(GeneralSettings);
export const mountMediaSettings: typeof Bundle.mountMediaSettings = mounter(MediaSettings);
export const mountNetworkSettings: typeof Bundle.mountNetworkSettings = mounter(NetworkSettings);
export const mountMaintenanceSettings: typeof Bundle.mountMaintenanceSettings = mounter(MaintenanceSettings);
