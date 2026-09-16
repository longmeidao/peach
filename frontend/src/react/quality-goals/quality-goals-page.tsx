/* 高清版目标页：账本里标记为「还该有更好一版」的那些作品。
 *
 * 一屏回答两件事：还欠多少部、每一部欠在哪里。所以卡片上除了标题就只有来源、时长、
 * 体积和判定原因——决定要不要去找更好一版，看的就是这几项。
 *
 * 番号标题与来源徽标由遗留层以 HTML 字符串传进来：它们是全站语义契约的唯一实现，
 * 在这里重写一份就会漂。时长、体积、来源名走 `/js/core.js` 同一套格式化口径，同理。 */
import { RiSparklingLine } from '@remixicon/react';
import { useQuery } from '@tanstack/react-query';

import { LOC, fmtDur, fmtSize } from '@peach/legacy/core';

import { Button } from '@/components/base/buttons/button';

import { errorMessage } from '../../api';
import type { QualityGoalsProps } from '../bundle';
import { cardClass } from '../components/card';
import { EmptyState } from '../components/empty-state';
import { Note } from '../components/note';
import { Page } from '../components/page';
import {
  fetchQualityGoals, previewUrl, QUALITY_GOALS_KEY, type QualityGoal,
} from './quality-goals';

/** 一部待升级的作品一张卡。 */
function GoalCard(
  { item, openItem, javTitleHtml, javDisplayName, srcBadge }: { item: QualityGoal } & QualityGoalsProps,
) {
  const open = () => openItem(item.id);
  return (
    <li data-goal-id={item.id}
      className={cardClass({ padding: 'none', bordered: 'soft', className: 'flex flex-col gap-3 p-3' })}>
      <div className="flex min-w-0 gap-4">
        {/* 居中那句占位文字用 `inline-grid`：旧样式表里 `.grid` 是海报墙那条带列宽和
            间距的规则，排在 `peach-react.css` 后面会赢。这颗按钮是 flex 子项，行内格
            会被块级化，算出来仍是 `display:grid`。 */}
        <button type="button" onClick={open} aria-label={`打开 ${javDisplayName(item)}`}
          className="relative inline-grid w-card-cover shrink-0 aspect-card-cover cursor-pointer place-items-center overflow-hidden rounded-2lg bg-background-tertiary-default">
          {/* 图片取不到时（onError 把 img 摘掉）露出来的就是这句。 */}
          <span className="text-caption-1-regular text-text-secondary">暂无预览</span>
          <img src={previewUrl(item)} alt="" loading="lazy"
            onError={(event) => event.currentTarget.remove()}
            className="absolute inset-0 size-full object-contain" />
        </button>
        <div className="flex min-w-0 flex-col gap-1.5">
          <h3 className="text-headline-medium text-text-primary">
            <button type="button" data-middle-truncate onClick={open}
              className="block w-full cursor-pointer text-left"
              dangerouslySetInnerHTML={{ __html: javTitleHtml(item) }} />
          </h3>
          <p className="flex flex-wrap items-center gap-2 text-body-2-regular text-text-secondary">
            {/* 插原始 HTML 要有个宿主元素，而来源徽标在遗留版本里是这个 flex 容器的直接
                子项。`contents` 让宿主从布局里消失，徽标的对齐与间距保持不变。 */}
            <span className="contents" dangerouslySetInnerHTML={{ __html: srcBadge(item.location, item.cost) }} />
            <span>{LOC[item.location] ?? item.location}</span>
            <span>{fmtDur(item.duration)}</span>
            <span>{fmtSize(item.size ?? 0)}</span>
          </p>
          {item.reason
            ? <p className="border-t border-separator-border pt-3 text-body-2-regular text-text-secondary">
                {item.reason}
              </p>
            : null}
        </div>
      </div>
      <footer className="flex justify-end">
        <Button variant="secondary" size="small" onClick={open}>查看版本</Button>
      </footer>
    </li>
  );
}

export function QualityGoalsPage(props: QualityGoalsProps) {
  const goals = useQuery({ queryKey: QUALITY_GOALS_KEY, queryFn: ({ signal }) => fetchQualityGoals(signal) });
  const data = goals.data;
  if (!data) {
    return (
      <Page>
        <Note tone="error" title="读取失败">{goals.error ? errorMessage(goals.error) : '读取高清版目标失败'}</Note>
      </Page>
    );
  }
  const items = data.items || [];
  if (!items.length) {
    return (
      <Page>
        <EmptyState shell="plain" icon={RiSparklingLine} title="没有标记中的高清版目标">
          现有版本都已满足条件，或还没有加入追踪。
        </EmptyState>
      </Page>
    );
  }
  return (
    <Page>
      {/* 总数取服务端的 `total` 而不是这一页的条数：`limit` 截断时两者不是一个数，
          而这一行要回答的是「一共还欠多少部」。 */}
      <div className={cardClass({
        variant: 'raised', className: 'flex flex-col gap-1 px-6 py-5 max-sm:px-4',
      })}>
        <span className="text-body-2-regular text-text-secondary">待升级</span>
        <b className="text-display-4-medium tabular-nums text-text-primary">{`${data.total} 部作品`}</b>
      </div>
      <ul className="card-grid-cover gap-5">
        {items.map((item) => <GoalCard key={item.id} item={item} {...props} />)}
      </ul>
    </Page>
  );
}
