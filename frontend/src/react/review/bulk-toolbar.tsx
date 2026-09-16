/* 批量工具条：分组方式、分类筛选、全选本页，以及选中之后那一条判定栏。
 *
 * 分组方式和筛选项按**整条队列**算，卡片只画当前这一页：筛选里的计数说的是队列，不是
 * 这一屏。工具条吸在顶栏下沿，所以选中之后的判定栏接在它下面，而不是另开一个浮窗——
 * 两块各自定位的话，滚动时它们会互相盖住。 */
import { RiCheckDoubleLine } from '@remixicon/react';

import { Button } from '@/components/base/buttons/button';
import { Select, SelectItem } from '@/components/base/select/select';
import type { DecisionStatus, ReviewGroup, ReviewGrouping, ReviewRow } from './review';
import { commonReviewSources } from './review';

export interface BulkToolbarProps {
  groupOptions: [ReviewGrouping, string][];
  groupBy: ReviewGrouping;
  onGroupBy(next: ReviewGrouping): void;
  groups: ReviewGroup[];
  filter: string;
  onFilter(next: string): void;
  /** 当前这一页上的行，全选就是全选它们。 */
  pageKeys: string[];
  selected: ReadonlySet<string>;
  onSelected(next: Set<string>): void;
  /** 选中的那些行，用来算共同来源。 */
  selectedRows: ReviewRow[];
  metadata: boolean;
  /** 所选项目里还能不能按下「通过所选」。 */
  approvable: boolean;
  busy: boolean;
  feedback: string;
  onUnifySource(source: string): void;
  onRun(status: Extract<DecisionStatus, 'approved' | 'rejected'>): void;
}

export function BulkToolbar(props: BulkToolbarProps) {
  const {
    groupOptions, groupBy, onGroupBy, groups, filter, onFilter, pageKeys, selected, onSelected,
    selectedRows, metadata, approvable, busy, feedback, onUnifySource, onRun,
  } = props;
  const shown = pageKeys.filter((key) => selected.has(key));
  const allShown = shown.length > 0 && shown.length === pageKeys.length;
  const sources = commonReviewSources(selectedRows);
  const needsSource = metadata && selectedRows.some((row) => (row.candidates?.length || 0) > 1);
  const sourceLabel = sources.length ? '统一选择来源' : '所选项目无共同来源';

  const toggleAll = () => {
    const next = new Set(selected);
    for (const key of pageKeys) { if (allShown) next.delete(key); else next.add(key) }
    onSelected(next);
  };

  return (
    <div role="group" aria-label="复核批量操作"
      data-glass-pane=""
      className="glass-pane sticky top-topbar z-10 flex flex-col gap-3 rounded-floating p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Select aria-label="筛选分组方式" size="sm" selectedKey={groupBy}
          onSelectionChange={(key) => { if (key !== null) onGroupBy(String(key) as ReviewGrouping) }}>
          {groupOptions.map(([key, name]) => <SelectItem key={key} id={key}>{name}</SelectItem>)}
        </Select>
        {/* 只有一组时没什么可筛的：一个「全部分类」的下拉读起来像坏了。 */}
        {groups.length > 1 ? (
          <Select aria-label={groupBy === 'field' ? '筛选字段分类' : '筛选当前分类'} size="sm"
            selectedKey={filter || '*'}
            onSelectionChange={(key) => { if (key !== null) onFilter(String(key) === '*' ? '' : String(key)) }}>
            <SelectItem id="*">全部分类</SelectItem>
            {groups.map((group) => (
              <SelectItem key={group.key} id={group.key}>
                {`${group.title} · ${group.rows.length}`}
              </SelectItem>
            ))}
          </Select>
        ) : null}
        <Button variant="secondary" size="small" leadingIcon={RiCheckDoubleLine}
          aria-pressed={allShown} disabled={busy || !pageKeys.length} onClick={toggleAll}>
          {allShown ? '清空当前选择' : filter ? '全选当前分类' : '全选本页'}
        </Button>
      </div>

      {shown.length || selected.size ? (
        <div role="group" aria-label="复核所选项目"
          className="flex flex-wrap items-center gap-2 rounded-2lg bg-background-secondary-default px-3 py-2">
          <span role="status" className="tabular-nums text-body-2-medium text-text-primary">
            {`已选 ${selected.size} 项`}
          </span>
          {needsSource ? (
            <Select aria-label="统一选择来源" size="sm" selectedKey=""
              isDisabled={busy || !sources.length}
              onSelectionChange={(key) => { if (key !== null && key !== '') onUnifySource(String(key)) }}>
              <SelectItem id="">{sourceLabel}</SelectItem>
              {sources.map((source) => <SelectItem key={source} id={source}>{source}</SelectItem>)}
            </Select>
          ) : null}
          <Button variant="primary" size="small" disabled={busy || !selected.size || !approvable}
            onClick={() => onRun('approved')}>通过所选</Button>
          <Button variant="danger" size="small" disabled={busy || !selected.size}
            onClick={() => onRun('rejected')}>拒绝所选</Button>
          <Button variant="ghost" size="small" disabled={busy}
            onClick={() => onSelected(new Set())}>取消选择</Button>
          {feedback
            ? <p role="status" className="w-full text-body-2-regular text-text-secondary">{feedback}</p>
            : null}
        </div>
      ) : null}
    </div>
  );
}
