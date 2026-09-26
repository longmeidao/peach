/* 全站 Toast：Sonner 的栈，挂在 `#toasts`（body 直下，遗留层整页重画冲不掉）。
 *
 * 遗留壳的 `toast()` 与各 island 拿到的 `toast` prop 最后都落到 `showToast`。堆叠、悬停展开、
 * 滑动关闭与悬停暂停计时照 Sonner；面、线、圆角、阴影取 Board 的浮层那一套，写在
 * `web/css/17-overlay.css` 的 `#toasts` 一节。宿主不带 `.peach-react`：那一层的 Preflight 会把
 * Sonner 自己的按钮样式清掉，而这里用到的 Board token 本来就挂在 `:root` 上。 */
import type { CSSProperties } from 'react';
import { createRoot } from 'react-dom/client';
import { Toaster, toast } from 'sonner';

import type * as Bundle from './bundle';

/* 成功那一枚勾自己画出来（`web/css/25-motion.css` 的 `[data-toast-glyph=draw]`），失败那一枚
   不画：错误要的是立刻看清。字形由遗留层的 `icon()` 给，和全站其余图标同一套描边件。 */
const glyph = (html: string, draw: boolean) => (
  <span data-toast-glyph={draw ? 'draw' : 'still'} aria-hidden="true" dangerouslySetInnerHTML={{ __html: html }} />
);

let mounted = false;

export const mountToaster: typeof Bundle.mountToaster = (host, icons) => {
  if (mounted) return;
  mounted = true;
  /* 底边读 `--toast-bottom`：教程卡在右下角时，遗留层把它写成卡上沿之上的位置；没写就是
     Sonner 的默认边距。宽度和教程卡同宽，两块叠在一列里左右对齐。 */
  createRoot(host).render(
    <Toaster position="bottom-right" closeButton gap={8}
      style={{ '--width': '400px' } as CSSProperties}
      offset={{ right: 24, bottom: 'var(--toast-bottom, 24px)' }}
      mobileOffset={{ right: 16, left: 16, bottom: 'var(--toast-bottom, 16px)' }}
      toastOptions={{ closeButtonAriaLabel: '关闭提示' }} containerAriaLabel="通知"
      icons={{ success: glyph(icons.success, true), error: glyph(icons.error, false) }} />,
  );
};

/* 同一个 `id` 再调一次就是改写那一条：撤销的结果写回原回执，不另起一条，底部对齐的栈里
   不会一进一出地跳一格。改写时 `action` 显式给成 `undefined`，Sonner 按 id 合并，不写这一项
   旧的「撤销」键会留在「已撤销」旁边。 */
export const showToast: typeof Bundle.showToast = (id, request) => {
  const show = request.alert ? toast.error : toast.success;
  const action = request.action;
  show(<span dangerouslySetInnerHTML={{ __html: request.html }} />, {
    id,
    duration: request.timeout || Infinity,
    action: action ? {
      label: action.label,
      // 点了不关：结果要写回这一条。关掉它的是随后那次改写的计时。
      onClick: (event) => { event.preventDefault(); action.run(event.currentTarget) },
    } : undefined,
  });
};
