/* 字段、分区、页面旁的持久提示。配置页与活动页共用这一份。
 *
 * 注册表里没有行内 Note：`notification` 条目是带关闭键和计时的浮动通知。这里按语气取
 * `status-*` 与 `notification-*` token 组合，差异登记在 `../boardui/ORIGIN.md`。 */
import type { ReactNode } from 'react';

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'error';

/** 没有密码、保存失败、账本缺表这类是当前状态，不和字段说明共用灰色小字。 */
export function Note({ tone, title, children }: { tone: Tone; title?: string; children: ReactNode }) {
  const content = (
    <>
      {title ? <p className="text-body-medium">{title}</p> : null}
      <p className="text-body-2-regular">{children}</p>
    </>
  );
  switch (tone) {
    case 'info':
      return <div role="status" className="flex flex-col gap-0.5 rounded-2lg bg-notification-information-background px-3 py-2 text-notification-information-foreground">{content}</div>;
    case 'success':
      return <div role="status" className="flex flex-col gap-0.5 rounded-2lg bg-notification-success-background px-3 py-2 text-notification-success-foreground">{content}</div>;
    case 'warning':
      return <div role="note" className="flex flex-col gap-0.5 rounded-2lg bg-status-yellow-background px-3 py-2 text-status-yellow-text">{content}</div>;
    case 'error':
      return <div role="alert" className="flex flex-col gap-0.5 rounded-2lg bg-background-tertiary-error px-3 py-2 text-text-error-primary">{content}</div>;
    default:
      return <div role="note" className="flex flex-col gap-0.5 rounded-2lg bg-background-tertiary-default px-3 py-2 text-text-secondary">{content}</div>;
  }
}
