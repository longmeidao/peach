/* 详情浮窗右侧那一列队列（Mix、分卷、版本、播放列表、关注的合集与多媒体）。
 *
 * 结构与类名照遗留层 `queueHtml`（`web/app.js`）：`.mixqueue` / `.mixrow` / `.mixitem` 的
 * 样式在 `web/css/13-stage.css`，JAV 详情同一套，迁它那一步之前两边共用，所以这里输出的是
 * 遗留类名（`.oxlintrc.json` 的放行名单，理由见 `docs/FRONTEND.md`）。一列十几条要能拖着
 * 横滚（窄屏下队列是横排），拖动借壳的 `wireDrag`，由调用方经 `listRef` 接上。 */
import type { ButtonHTMLAttributes, ReactNode, Ref } from 'react';
import { icon } from '@peach/legacy/core';

export function MixQueue({ kind, title, summary, onClose, actions, listRef, children, ...data }: {
  kind: string;
  title: string;
  summary: string;
  onClose(): void;
  /** 关闭键前面的动作键（保存为播放列表之类）。 */
  actions?: ReactNode;
  listRef?: Ref<HTMLDivElement>;
  children: ReactNode;
} & Record<`data-${string}`, string>) {
  return (
    <aside className="mixqueue" data-queue-kind={kind} {...data}>
      <div className="mixqueuehead">
        {/* 作用域 Preflight 把标题字重清成 inherit，这里按字重三档取 semibold。 */}
        <div><h2 className="font-semibold">{title}</h2><span>{summary}</span></div>
        <div className="mixqueueactions">
          {actions}
          {/* 并排布局（`.sgrid.mixgrid`）里队列头不放关闭键，关舞台用媒体框上那一枚（`13-stage.css`）。 */}
          <button type="button" data-queue-close="" title="关闭" aria-label="关闭" onClick={onClose}
            dangerouslySetInnerHTML={{ __html: icon('x') }} />
        </div>
      </div>
      <div className="mixlist" ref={listRef}>{children}</div>
    </aside>
  );
}

/** 队列里的一行：左边缩略图（时长角标由调用方放进 `pic`），右边两行字。作品队列的字前面还有
 *  一枚署名头像（`lead`，和卡片的署名层同一套）；播放列表的行尾多一组抓手与移出（`after`），
 *  拖动排序认的是行上的 `row` 属性。 */
export function MixQueueRow({ current, pic, lead, after, row, children, ...button }: {
  current: boolean;
  pic: ReactNode;
  lead?: ReactNode;
  after?: ReactNode;
  row?: Record<`data-${string}`, string | number>;
  children: ReactNode;
} & ButtonHTMLAttributes<HTMLButtonElement> & Record<`data-${string}`, string | number>) {
  const text = <span className="mixitemtext">{children}</span>;
  return (
    <div className="mixrow" {...row}>
      <button type="button" className={current ? 'mixitem current' : 'mixitem'} aria-current={current ? 'true' : 'false'} {...button}>
        <span className="mixitempic">{pic}</span>
        {lead === undefined ? text : <span className="mixitemmeta">{lead}{text}</span>}
      </button>
      {after}
    </div>
  );
}

/** 网盘分组的小标题：组名加条数。 */
export const MixGroupLabel = ({ label, count }: { label: string; count: number }) => (
  <h3 className="mixgrouplabel">{label} <span>{count}</span></h3>
);
