/* 配置页各分区共用的组合件。
 *
 * 外框取 BoardUI 设置弹层的 `SettingsSectionLabel` + `SettingsCard`，开关行直接用 `SettingsRow`。
 * 注册表里没有行内提示、进度条和折叠，这三样用 BoardUI token 组合，差异登记在 `boardui/ORIGIN.md`。 */
import type { FormEvent, ReactNode } from 'react';
import { RiArrowRightSLine, RiExternalLinkLine } from '@remixicon/react';

import { SettingsCard, SettingsSectionLabel } from '@/components/application/settings/settings-rows';
import { LinkButton } from '@/components/base/buttons/link-button';

interface SectionProps {
  title: string;
  id?: string;
  /** 给了就画成表单：回车提交，提交键放在 `Footer` 里。 */
  onSubmit?: (event: FormEvent<HTMLFormElement>) => void;
  children: ReactNode;
}

export function Section({ title, id, onSubmit, children }: SectionProps) {
  const body = (
    <>
      <SettingsSectionLabel>{title}</SettingsSectionLabel>
      <SettingsCard>{children}</SettingsCard>
    </>
  );
  return onSubmit
    ? <form id={id} aria-label={title} noValidate onSubmit={onSubmit} className="flex w-full flex-col gap-2">{body}</form>
    : <section id={id} aria-label={title} className="flex w-full flex-col gap-2">{body}</section>;
}

/** 一组 `SettingsRow`。行自己画下边线、最后一行不画，所以要有一层只装行的父元素。 */
export function Rows({ children }: { children: ReactNode }) {
  return <div className="flex flex-col">{children}</div>;
}

/** 卡片只管左内边距和底色；不是 `SettingsRow` 的内容由这一层给行距和上下右内边距。
 *  排在 `Rows` 或 `FactList` 后面时 `divided`，和上面那组行之间补一道分隔线。 */
export function Stack({ divided = false, children }: { divided?: boolean; children: ReactNode }) {
  return divided
    ? <div className="flex flex-col gap-4 border-t border-separator-border py-4 pr-3">{children}</div>
    : <div className="flex flex-col gap-4 py-4 pr-3">{children}</div>;
}

/** 底栏：左边一句说这颗按钮此刻意味着什么，右边是按钮。 */
export function Footer({ status, children }: { status?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-3 border-t border-separator-border py-3 pr-3">
      {status ? <div className="mr-auto min-w-0 text-body-2-regular text-text-secondary">{status}</div> : null}
      {children}
    </div>
  );
}

export function Help({ role, children }: { role?: 'status'; children: ReactNode }) {
  return <p role={role} className="text-body-2-regular text-text-secondary">{children}</p>;
}

export function ErrorText({ children }: { children: ReactNode }) {
  return <p role="alert" className="text-body-2-regular text-text-error-primary">{children}</p>;
}

/** 字段上方的名字，外观同 BoardUI `Label`；控件自己的无障碍名称由 `aria-label` 给。 */
export function FieldLabel({ children }: { children: ReactNode }) {
  return <p className="text-body-medium text-text-primary">{children}</p>;
}

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'error';

/** 字段、分区旁的持久提示。没有密码、保存失败这类是当前状态，不和字段说明共用灰色小字。 */
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

/** 新窗口打开的外部链接，尾部带外链字形。 */
export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <LinkButton href={href} target="_blank" rel="noreferrer" size="small" trailingIcon={RiExternalLinkLine}>
      {children}
    </LinkButton>
  );
}

/** 只读的名目与读数，一行一对，行距与分隔线同 `SettingsRow`。 */
export function FactList({ children }: { children: ReactNode }) {
  return <dl className="flex flex-col">{children}</dl>;
}

export function Fact({ term, children }: { term: ReactNode; children: ReactNode }) {
  return (
    <div className="flex min-h-11 items-center justify-between gap-4 border-b border-separator-border py-2.5 pr-3 last:border-b-0">
      <dt className="flex shrink-0 items-center gap-2 text-body-regular text-text-secondary">{term}</dt>
      <dd className="flex min-w-0 flex-wrap items-center justify-end gap-2 text-right text-body-regular break-all text-text-primary">{children}</dd>
    </div>
  );
}

/** 已知总量的进度。宽度按比例画在 SVG 里：条宽写进 `rect` 的属性，不用内联样式。 */
export function Progress({ label, value, max = 100, stops = [] }: { label: string; value: number; max?: number; stops?: number[] }) {
  const filled = Math.min(Math.max(value, 0), max);
  return (
    <svg role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={value}
      viewBox={`0 0 ${max} 1`} preserveAspectRatio="none" className="h-1.5 w-full overflow-hidden rounded-full">
      <rect width={max} height={1} className="fill-background-tertiary-default" />
      <rect width={filled} height={1} className="fill-border-focus-ring" />
      {stops.map((stop) => <rect key={stop} x={stop} width={0.4} height={1} className="fill-background-secondary-default" />)}
    </svg>
  );
}

/** 展开正文。原生 `details`：键盘、状态与无障碍语义都由浏览器给。 */
export function Disclosure({ summary, children }: { summary: string; children: ReactNode }) {
  return (
    <details className="group">
      <summary className="flex w-fit cursor-pointer list-none items-center gap-1 rounded-sm text-body-2-medium text-text-secondary outline-none select-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring">
        <RiArrowRightSLine aria-hidden className="size-4 shrink-0 transition-transform group-open:rotate-90" />
        {summary}
      </summary>
      <div className="flex flex-col gap-2 pt-3">{children}</div>
    </details>
  );
}

/** 遗留雪碧图（`web/index.html` 的 `#i-*` symbol）里的字形。媒体库图标的取值就是这些名字。 */
export function SpriteIcon({ name }: { name: string }) {
  return (
    <svg aria-hidden viewBox="0 0 24 24" fill="none" className="size-4 shrink-0 stroke-current stroke-2">
      <use href={`#i-${name}`} />
    </svg>
  );
}

/** 来源标识：网盘站标是内嵌 PNG，其余是雪碧图字形（`web/js/media-source-icons.js`）。 */
export function SourceMark({ mark }: { mark: string }) {
  return mark.startsWith('data:image/png;base64,')
    ? <img src={mark} alt="" width={16} height={16} className="size-4 shrink-0" />
    : <SpriteIcon name={mark} />;
}
