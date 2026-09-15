/* 配置页各分区共用的组合件。
 *
 * 外框取 BoardUI 设置弹层的 `SettingsSectionLabel` + `SettingsCard`，开关行直接用 `SettingsRow`。
 * 注册表里没有折叠，它用 BoardUI token 组合，差异登记在 `boardui/ORIGIN.md`。
 * 提示与进度条另有页面共用的一份，在 `../components/`。 */
import { useId, useRef, useState } from 'react';
import type { FormEvent, MouseEvent, ReactNode } from 'react';
import { RiArrowRightSLine, RiExternalLinkLine } from '@remixicon/react';
import { setCollapseOpen } from '@peach/legacy/ui';

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

/** 展开正文。原生 `details` 给键盘与无障碍语义；开合交给共用 Collapse 的 `setCollapseOpen`，
 *  它给正文外层挂上旧样式表的 `.fcollapse` 让高度过渡。内边距放在里层，高度才能收到 0。 */
export function Disclosure({ summary, children }: { summary: string; children: ReactNode }) {
  const id = useId();
  const details = useRef<HTMLDetailsElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const toggle = (event: MouseEvent) => {
    event.preventDefault();
    if (!details.current || !body.current) return;
    setCollapseOpen(details.current, body.current, !open);
    setOpen(!open);
  };
  return (
    <details ref={details}>
      <summary aria-expanded={open} aria-controls={id} onClick={toggle}
        className="flex w-fit cursor-pointer list-none items-center gap-1 rounded-sm text-body-2-medium text-text-secondary outline-none select-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring">
        <RiArrowRightSLine aria-hidden className={open ? 'size-4 shrink-0 rotate-90 transition-transform' : 'size-4 shrink-0 transition-transform'} />
        {summary}
      </summary>
      <div ref={body} id={id} inert={!open}>
        <div className="flex flex-col gap-2 pt-3">{children}</div>
      </div>
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
