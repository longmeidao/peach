/* 关注列表：同一份来源集合的两种视图，外加检查更新那一趟后台任务。
 *
 * 两种视图共用一个勾选集合（身份是来源 ID）和一份排序状态。表格视图由
 * `@tanstack/react-table` 驱动：列定义、排序状态、行选择与分页都在它手里，行数据是
 * 已经按共用比较器排好的**全集**——排序作用在全部结果上，分页只切最后一步，所以
 * 「下一页」看到的是真的下一批，而不是本页内部重排。
 *
 * 选择跨页也跨视图：换页、换排序、从卡片切到表格，选中的仍是同一批来源，底部那条批量
 * 操作发出去的也是整个 ID 集合，而不是屏幕上这一页。 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  RiArrowDownLine, RiArrowDownSLine, RiArrowUpLine, RiArrowUpSLine, RiCheckDoubleLine,
  RiDeleteBinLine, RiLayoutGridLine, RiRefreshLine, RiRssLine, RiTableLine,
} from '@remixicon/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  createColumnHelper, flexRender, getCoreRowModel, getPaginationRowModel, useReactTable,
  type RowSelectionState, type SortingState,
} from '@tanstack/react-table';
import { VisuallyHidden } from 'react-aria-components';
import { mapLimit } from '@peach/legacy/core';
import { confirmModal } from '@peach/legacy/ui';

import { Button } from '@/components/base/buttons/button';
import { Checkbox } from '@/components/base/checkbox/checkbox';
import { Select, SelectItem } from '@/components/base/select/select';
import {
  Table, TableBody, TableCell, TableColumn, TableHeader, TableRow,
} from '@/components/base/table/table';

import { errorMessage } from '../../api';
import { DOTS, paginationRange } from '../../pagination';
import { EmptyState } from '../components/empty-state';
import { LoadingDots } from '../components/loading-dots';
import { Note } from '../components/note';
import { Progress } from '../components/progress';
import { queryClient } from '../query';
import { busyProps } from '../settings/use-action';
import {
  authorGroups, authorName, checkedText, checkEvidenceGap, checkFailures, checkSummary,
  COLUMN_SORT, dropSources, fetchCheckJob, fetchPending, FOLLOW_CHECK_KEY, isBroken,
  jobPollInterval, LAYOUTS, markItem, PAGE_SIZES, pageWindow, patchSource, removeSource,
  reloadFollowManage, selectionState, setSourceEnabled, SORT_DEFAULT_DIR, SORT_OPTIONS,
  sortLabel, startCheck, tableRows, toggleGroup,
  type CheckJob, type FollowData, type FollowSource, type Layout, type SortDir, type SortKey,
  type TableRow as SourceTableRow,
} from './follow-manage';
import { AuthorAvatar, SourceIcon, SourceLink, StatusBadge } from './source-view';

/** 列头点的就是工具栏里的那一档排序，所以两边共用同一张对照表，方向也共用一个值。 */
const SORT_COLUMN = Object.fromEntries(
  Object.entries(COLUMN_SORT).map(([column, sort]) => [sort, column]),
) as Partial<Record<SortKey, string>>;

/** 工具行窄到这个宽度以下，带字的按钮就只留字形。取自旧版实测的那条断点。 */
const TOOLBAR_COMPACT_PX = 740;

/** 这一行自己有多宽。
 *
 * 判据只能是这一行自己的宽度，不是视口的：同一个视口下侧栏收起与展开留给它的宽度差两百
 * 像素，按视口断点会在一边早折、在另一边照样超框。塌下去用的是 `Button` 自己的 `iconOnly`
 * ——外面改它的内外边距会被 `no-restyle` 挡下，那条规则说的就是间距归控件自己。 */
function useCompactToolbar(): [(node: HTMLDivElement | null) => void, boolean] {
  const [compact, setCompact] = useState(false);
  const observer = useRef<ResizeObserver | null>(null);
  const attach = useCallback((node: HTMLDivElement | null) => {
    observer.current?.disconnect();
    if (!node) { observer.current = null; return }
    const watch = new ResizeObserver(() => setCompact(node.clientWidth < TOOLBAR_COMPACT_PX));
    watch.observe(node);
    observer.current = watch;
    setCompact(node.clientWidth < TOOLBAR_COMPACT_PX);
  }, []);
  useEffect(() => () => observer.current?.disconnect(), []);
  return [attach, compact];
}

const COLUMN_LABELS: Record<string, string> = {
  select: '选择', author: '创作者', source: '来源', provider: '站点',
  status: '状态', checked: '上次检查', actions: '操作',
};

/** 行上那两个动作由调用方给，但列定义不该跟着每一次渲染重建；两者之间放一个当前值的盒子。 */
interface RowHandlers {
  check(ids: number[]): void;
  remove(source: FollowSource): void;
  busy: boolean;
  readOnly: boolean;
}

export interface SourceListProps {
  data: FollowData;
  sort: SortKey;
  dir: SortDir;
  page: number;
  layout: Layout;
  pageSize: number;
  selected: ReadonlySet<number>;
  readOnly: boolean;
  onSort(sort: SortKey, dir: SortDir): void;
  onPage(page: number): void;
  onLayout(layout: Layout): void;
  onPageSize(size: number): void;
  onSelected(next: Set<number>): void;
  toast(message: string): void;
  openFollow(): void;
}

/** 页码。上一页／下一页在两端，页码居中，页数多时两侧折成「…」。 */
function Pagination(
  { page, pages, onPage }: { page: number; pages: number; onPage(page: number): void },
) {
  if (pages <= 1) return null;
  return (
    <nav aria-label="关注列表分页" className="flex flex-wrap items-center justify-center gap-2">
      <Button variant="secondary" size="small" disabled={page <= 1}
        onClick={() => onPage(page - 1)}>上一页</Button>
      <ul className="flex flex-wrap items-center gap-1">
        {paginationRange(page, pages).map((item, at) => (
          <li key={item === DOTS ? `dots-${at}` : item}>
            {item === DOTS
              ? <span aria-hidden className="px-1 text-body-2-regular text-text-tertiary">{DOTS}</span>
              : <Button variant={item === page ? 'secondary' : 'ghost'} size="small"
                  aria-label={`第 ${item} 页`} aria-current={item === page ? 'page' : undefined}
                  onClick={() => onPage(Number(item))}>{item}</Button>}
          </li>
        ))}
      </ul>
      <Button variant="secondary" size="small" disabled={page >= pages}
        onClick={() => onPage(page + 1)}>下一页</Button>
    </nav>
  );
}

/** 一条来源在创作者卡里的那一行：勾选、名字、站点、状态、上次检查、动作。 */
function SourceRow(
  { source, selected, onToggle, handlers }:
  { source: FollowSource; selected: boolean; onToggle(on: boolean): void; handlers: RowHandlers },
) {
  return (
    <div data-selected={selected || undefined}
      className="flex flex-wrap items-center gap-3 border-t border-separator-border py-2.5 pr-3 pl-4 data-selected:bg-background-secondary-default">
      <Checkbox isSelected={selected} onChange={onToggle} aria-label={`选择 ${source.label}`} />
      <span className="flex min-w-0 grow flex-col gap-0.5">
        <SourceLink source={source} />
        {source.last_error
          ? <small className="text-caption-1-regular text-text-error-primary">{source.last_error}</small>
          : null}
      </span>
      {/* 卡片里站名只出一枚图标：这一行紧挨着的就是作者名和状态徽章，站名写出来是同一个词
          并排两次。名字仍在 DOM 里，读屏和取不到图标时都还读得到；表格那边「站点」是独立
          一列，列头就叫这个名字，那里才出文字。 */}
      <span className="flex shrink-0 items-center gap-1.5 text-body-2-regular text-text-secondary"
        title={source.provider_label}>
        <SourceIcon provider={source.provider} label={source.provider_label} />
      </span>
      <StatusBadge source={source} />
      <span className="shrink-0 text-body-2-regular whitespace-nowrap text-text-secondary">
        {checkedText(source)}
      </span>
      <span className="flex shrink-0 items-center gap-1">
        <Button variant="ghost" size="small" iconOnly leadingIcon={RiRefreshLine}
          aria-label={`检查 ${source.label} 的更新`}
          disabled={!source.enabled || handlers.readOnly} {...busyProps(handlers.busy)}
          onClick={() => handlers.check([source.id])} />
        <Button variant="ghost" size="small" iconOnly leadingIcon={RiDeleteBinLine}
          aria-label={`移除 ${source.label}`} disabled={handlers.readOnly}
          onClick={() => handlers.remove(source)} />
      </span>
    </div>
  );
}

/** 一位创作者一张卡。同一个人在几个站上的来源收在一处，标题行给出这个人的整体状态。 */
function AuthorCard(
  { group, name, open, selected, handlers, onOpen, onToggleGroup, onToggle }:
  {
    group: FollowSource[]; name: string; open: boolean; selected: ReadonlySet<number>;
    handlers: RowHandlers;
    onOpen(open: boolean): void;
    onToggleGroup(on: boolean): void;
    onToggle(id: number, on: boolean): void;
  },
) {
  const ids = group.map((source) => source.id);
  const enabled = group.filter((source) => source.enabled).map((source) => source.id);
  const bad = group.filter(isBroken).length;
  const providers = [...new Set(group.map((source) => source.provider_label || source.provider))].join('、');
  const panel = `follow-author-${group[0]!.id}`;
  const state = selectionState(selected, ids);
  return (
    <section aria-label={`${name} 的关注来源`}
      className="flex flex-col rounded-2xl border border-separator-border">
      <div className="flex flex-wrap items-center gap-3 py-2.5 pr-3 pl-4">
        <AuthorAvatar group={group} name={name} />
        <b className="min-w-0 grow text-body-medium break-words text-text-primary">{name}</b>
        <Button variant="ghost" size="small" iconOnly leadingIcon={RiRefreshLine}
          aria-label={`检查 ${name} 的全部来源`} disabled={!enabled.length || handlers.readOnly}
          {...busyProps(handlers.busy)} onClick={() => handlers.check(enabled)} />
        <span className="flex shrink-0 items-center gap-1" title={providers}>
          {group.map((source) => <SourceIcon key={source.id} provider={source.provider} />)}
          {/* 只读屏用的文字走 `VisuallyHidden`：它把样式写在元素上，不会生成一个和旧
              样式表同名的工具类（`web/css/01-base.css` 里那条 `.sr-only` 带 !important）。 */}
          <VisuallyHidden>{`来源：${providers}`}</VisuallyHidden>
        </span>
        {bad
          ? <span className="shrink-0 text-body-2-regular text-text-error-primary">{`${bad} 个失败`}</span>
          : null}
        <Button variant="secondary" size="small" leadingIcon={RiCheckDoubleLine}
          aria-pressed={state.all ? 'true' : state.some ? 'mixed' : 'false'}
          aria-label={`${state.all ? '取消全选' : '全选'} ${name} 的来源`}
          onClick={() => onToggleGroup(!state.all)}>{state.all ? '取消全选' : '全选'}</Button>
        <Button variant="ghost" size="small" aria-expanded={open} aria-controls={panel}
          aria-label={`${open ? '收起' : '展开'} ${name} 的来源`}
          onClick={() => onOpen(!open)}>{open ? '收起' : '展开'}</Button>
      </div>
      <div id={panel} hidden={!open}>
        {group.map((source) => (
          <SourceRow key={source.id} source={source} handlers={handlers}
            selected={selected.has(source.id)} onToggle={(on) => onToggle(source.id, on)} />
        ))}
      </div>
    </section>
  );
}

export function SourceList(props: SourceListProps) {
  const {
    data, sort, dir, page, layout, pageSize, selected, readOnly,
    onSort, onPage, onLayout, onPageSize, onSelected, toast, openFollow,
  } = props;
  const sources = data.sources;
  const aliases = useMemo(() => data.author_aliases || [], [data.author_aliases]);
  const counts = data.counts || {};
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(new Set<string>());
  const [toolbar, compact] = useCompactToolbar();
  /** 本次是不是在跟一趟检查：点过检查，或者本次见过它在跑。 */
  const [tracking, setTracking] = useState(false);
  /** 本次跟完的那一趟。首屏读到的旧终态不算，它不会走到这里。 */
  const [outcome, setOutcome] = useState<CheckJob | null>(null);
  const [problem, setProblem] = useState('');

  const groups = useMemo(() => authorGroups(sources, sort, dir, aliases), [sources, sort, dir, aliases]);
  const rows = useMemo(() => tableRows(groups, sort, dir, aliases), [groups, sort, dir, aliases]);

  const job = useQuery({
    queryKey: FOLLOW_CHECK_KEY,
    queryFn: ({ signal }) => fetchCheckJob(signal),
    refetchInterval: (query) => jobPollInterval(query.state.data),
  });
  const running = job.data?.status === 'running';

  const check = useMutation({
    mutationFn: (ids: number[]) => startCheck(ids),
    onSuccess: () => {
      setTracking(true);
      setOutcome(null);
      // 起的那一次回的就是任务快照，但节律由这个键说了算：让它立刻重读一次接上。
      void queryClient.invalidateQueries({ queryKey: FOLLOW_CHECK_KEY, exact: true });
    },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  useEffect(() => {
    const state = job.data;
    if (!state) return;
    if (state.status === 'running') {
      if (!tracking) setTracking(true);
      return;
    }
    if (!tracking) return;
    setTracking(false);
    setOutcome(state);
    void reloadFollowManage();
    toast(state.status === 'failed' ? (state.error || '检查失败') : checkSummary(state));
  }, [job.data, tracking, toast]);

  const startChecking = (ids: number[]) => {
    if (running || check.isPending) return;
    setProblem('');
    check.mutate(ids);
  };

  const toggleOne = (id: number, on: boolean) => onSelected(toggleGroup(selected, [id], on));
  const toggleMany = (ids: number[], on: boolean) => onSelected(toggleGroup(selected, ids, on));

  /* 单条移除只把那一条从缓存里去掉，顺手把它从勾选里也去掉：否则底部那条会一直算着
     一个已经不存在的来源。 */
  const remove = useMutation({
    mutationFn: (id: number) => removeSource(id),
    onSuccess: (_result, id) => {
      dropSources([id]);
      onSelected(toggleGroup(selected, [id], false));
      toast('已取消关注来源');
    },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  const removeSourceRow = (source: FollowSource) => void confirmModal({
    title: '取消关注来源', body: '将移除这个来源及已抓取的条目，媒体文件保留。',
    confirmLabel: '取消关注来源', danger: true,
    onConfirm: () => remove.mutateAsync(source.id),
  });

  /** 批量：一次请求一条，有界并发。串行发几百条是实测的卡点，一次全发出去又会自己挤自己。 */
  const bulk = useMutation({
    mutationFn: async (work: { ids: number[]; action: 'enabled' | 'paused' | 'remove' }) => {
      const results = await mapLimit(work.ids, 4, async (id: number) => {
        if (work.action === 'remove') await removeSource(id);
        else await setSourceEnabled(id, work.action === 'enabled');
      });
      return { ...work, done: work.ids.filter((_id, at) => results[at]?.ok), results };
    },
    onSuccess: (result) => {
      if (result.action === 'remove') dropSources(result.done);
      else for (const id of result.done) patchSource(id, { enabled: result.action === 'enabled' });
      onSelected(toggleGroup(selected, result.done, false));
      const failed = result.results.filter((row) => !row.ok);
      if (failed.length) {
        setProblem(`${failed.length}/${result.ids.length} 个来源未更新：${errorMessage(failed[0]?.error)}`);
        return;
      }
      setProblem('');
      const word = result.action === 'remove' ? '删除' : result.action === 'enabled' ? '启用' : '暂停';
      toast(`已${word} ${result.done.length} 个关注来源`);
    },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  /** 未看条目的批量标记。先取一趟待处理清单，再逐条写。 */
  const markAll = useMutation({
    mutationFn: async (to: string) => {
      const pending = await fetchPending();
      const ids = (pending.groups || [])
        .flatMap((group) => [group.primary, ...group.variants, ...group.duplicates])
        .filter((item) => item.status === 'new').map((item) => item.id);
      const results = await mapLimit(ids, 6, (id: number) => markItem(id, to));
      return { ids, failed: results.filter((row) => !row.ok) };
    },
    onSuccess: (result) => {
      void reloadFollowManage();
      if (result.failed.length) {
        setProblem(`批量更新 ${result.failed.length}/${result.ids.length} 项未完成`);
        return;
      }
      setProblem('');
      toast(`已批量标记 ${result.ids.length} 项`);
    },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  const handlers = useRef<RowHandlers>({
    check: startChecking, remove: removeSourceRow, busy: false, readOnly,
  });
  handlers.current = {
    check: startChecking,
    remove: removeSourceRow,
    busy: running || check.isPending,
    readOnly,
  };
  const rowHandlers = handlers.current;

  /* ── 表格视图：列定义、排序、行选择与分页都交给 TanStack Table ── */
  const columns = useMemo(() => {
    const column = createColumnHelper<SourceTableRow>();
    const label = (id: string) => () => COLUMN_LABELS[id] || id;
    return [
      column.display({
        id: 'select',
        header: label('select'),
        /* `slot={null}`：表格自带一个叫 selection 的插槽，摆进去的勾不声明归属就会被它
           拦下报错。这一列的勾归 TanStack Table 那份行选择管，不走 Table 自己的选择。 */
        cell: (context) => (
          <Checkbox slot={null} isSelected={context.row.getIsSelected()}
            onChange={(on) => context.row.toggleSelected(on)}
            aria-label={`选择 ${context.row.original.source.label}`} />
        ),
      }),
      column.accessor((row) => row.author, {
        id: 'author',
        header: label('author'),
        cell: (context) => (
          <span className="flex min-w-0 items-center gap-2">
            <AuthorAvatar group={context.row.original.group} name={context.row.original.author} />
            <span className="min-w-0 break-words">{context.row.original.author}</span>
          </span>
        ),
      }),
      column.accessor((row) => row.source.label, {
        id: 'source',
        header: label('source'),
        cell: (context) => (
          <span className="flex min-w-0 flex-col gap-0.5">
            <SourceLink source={context.row.original.source} />
            {context.row.original.source.last_error
              ? <small className="text-caption-1-regular text-text-error-primary">
                  {context.row.original.source.last_error}
                </small>
              : null}
          </span>
        ),
      }),
      column.accessor((row) => row.source.provider_label, {
        id: 'provider',
        header: label('provider'),
        cell: (context) => (
          <span className="flex items-center gap-1.5">
            <SourceIcon provider={context.row.original.source.provider} />
            {context.row.original.source.provider_label}
          </span>
        ),
      }),
      column.display({
        id: 'status',
        header: label('status'),
        cell: (context) => <StatusBadge source={context.row.original.source} />,
      }),
      column.accessor((row) => row.source.last_checked_at || '', {
        id: 'checked',
        header: label('checked'),
        cell: (context) => checkedText(context.row.original.source),
      }),
      column.display({
        id: 'actions',
        header: label('actions'),
        cell: (context) => (
          <span className="flex items-center gap-1">
            <Button variant="ghost" size="small" iconOnly leadingIcon={RiRefreshLine}
              aria-label={`检查 ${context.row.original.source.label} 的更新`}
              disabled={!context.row.original.source.enabled || rowHandlers.readOnly}
              {...busyProps(rowHandlers.busy)}
              onClick={() => handlers.current.check([context.row.original.source.id])} />
            <Button variant="ghost" size="small" iconOnly leadingIcon={RiDeleteBinLine}
              aria-label={`移除 ${context.row.original.source.label}`} disabled={rowHandlers.readOnly}
              onClick={() => handlers.current.remove(context.row.original.source)} />
          </span>
        ),
      }),
    ];
  }, [rowHandlers]);

  const sorting: SortingState = useMemo(() => {
    const id = SORT_COLUMN[sort];
    return id ? [{ id, desc: dir === 'desc' }] : [];
  }, [sort, dir]);
  const rowSelection: RowSelectionState = useMemo(
    () => Object.fromEntries([...selected].map((id) => [String(id), true])), [selected]);

  const asTable = layout === 'table';
  // 越界的页码落到末页：地址栏里挂着的可能是上一次、来源更多时的页码。
  const win = pageWindow(asTable ? rows.length : groups.length, pageSize, page);

  const table = useReactTable({
    data: rows,
    columns,
    /* 行的身份是来源 ID，不是它在这一页里的下标：换页、换排序之后 `rowSelection` 里记着的
       仍是同一批来源，卡片视图读的也是同一组数。 */
    getRowId: (row) => String(row.source.id),
    state: { sorting, rowSelection, pagination: { pageIndex: win.page - 1, pageSize } },
    /* 排序由共用的比较器算好再交进来：表格自己再排一遍的话，卡片视图与表格视图会各有一套
       顺序，同一份数据在两个视图里的先后就不一样了。 */
    manualSorting: true,
    enableRowSelection: true,
    onSortingChange: (updater) => {
      const next = typeof updater === 'function' ? updater(sorting) : updater;
      const first = next[0];
      if (!first) return;
      const key = COLUMN_SORT[first.id as keyof typeof COLUMN_SORT];
      if (key) onSort(key, first.desc ? 'desc' : 'asc');
    },
    onRowSelectionChange: (updater) => {
      const next = typeof updater === 'function' ? updater(rowSelection) : updater;
      onSelected(new Set(Object.entries(next).filter(([, on]) => on).map(([id]) => Number(id))));
    },
    onPaginationChange: (updater) => {
      const now = { pageIndex: win.page - 1, pageSize };
      const next = typeof updater === 'function' ? updater(now) : updater;
      if (next.pageSize !== pageSize) onPageSize(next.pageSize);
      else if (next.pageIndex !== now.pageIndex) onPage(next.pageIndex + 1);
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const pageRows = table.getRowModel().rows;
  const pageIds = asTable
    ? pageRows.map((row) => row.original.source.id)
    : groups.slice(win.start, win.end).flatMap((group) => group.map((source) => source.id));
  const pageState = selectionState(selected, pageIds);
  const chosen = [...selected];
  const failures = checkFailures(outcome);
  const evidence = checkEvidenceGap(outcome);
  const allCollapsed = groups.length > 0 && collapsed.size >= groups.length;

  if (!sources.length) {
    return (
      <EmptyState icon={RiRssLine} title="还没有关注来源">关注来源及其检查状态会显示在这里。</EmptyState>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 放不下时带字的按钮先收成图标，再让整行换行。收起后名字由 `aria-label` 接着说。 */}
      <div ref={toolbar} className="flex flex-wrap items-center gap-2">
        <h3 className="mr-auto text-headline-medium text-text-primary">关注列表</h3>
        <span className="text-body-2-regular text-text-secondary">
          {`${sources.length} 个来源${counts.new ? ` · ${counts.new} 条未看` : ''}`}
        </span>
        <Button variant="primary" size="small" leadingIcon={RiRefreshLine} disabled={readOnly}
          aria-label="检查全部" iconOnly={compact}
          {...busyProps(rowHandlers.busy)} onClick={() => startChecking([])}>检查全部</Button>
        <Button variant={asTable ? 'ghost' : 'secondary'} size="small" iconOnly
          leadingIcon={RiLayoutGridLine} aria-label={LAYOUTS[0][1]} aria-pressed={!asTable}
          onClick={() => onLayout('default')} />
        <Button variant={asTable ? 'secondary' : 'ghost'} size="small" iconOnly
          leadingIcon={RiTableLine} aria-label={LAYOUTS[1][1]} aria-pressed={asTable}
          onClick={() => onLayout('table')} />
        <Select aria-label="关注列表排序" size="sm" selectedKey={sort}
          onSelectionChange={(key) => {
            if (key === null) return;
            const next = String(key) as SortKey;
            onSort(next, SORT_DEFAULT_DIR[next]);
          }}>
          {SORT_OPTIONS.map(([key, name]) => <SelectItem key={key} id={key}>{name}</SelectItem>)}
        </Select>
        {/* 箭头是装饰，方向由无障碍名称说，而且说的是点下去会得到的那一头。 */}
        <Button variant="secondary" size="small" iconOnly
          leadingIcon={dir === 'asc' ? RiArrowUpLine : RiArrowDownLine}
          aria-label={sortLabel(sort, dir)}
          onClick={() => onSort(sort, dir === 'asc' ? 'desc' : 'asc')} />
        {asTable ? null : (
          <Button variant="secondary" size="small" iconOnly={compact}
            leadingIcon={allCollapsed ? RiArrowDownSLine : RiArrowUpSLine}
            aria-label={allCollapsed ? '全部展开' : '全部收起'}
            onClick={() => setCollapsed(allCollapsed
              ? new Set<string>()
              : new Set(groups.map((group) => String(group[0]!.author_key || group[0]!.id))))}>
            {allCollapsed ? '全部展开' : '全部收起'}
          </Button>
        )}
      </div>

      {/* 这一趟在后台跑，关掉页面还在继续，所以状态留在页面上而不是只让按钮转一下。 */}
      <div aria-live="polite" className="flex flex-col gap-3 empty:hidden">
        {running ? (job.data?.total
          ? <Progress label={job.data.message
              || `${job.data.older ? '抓取历史' : '检查更新'}：已完成 ${job.data.checked || 0}/${job.data.total} 个来源`}
              value={job.data.checked || 0} max={job.data.total} />
          : <LoadingDots label={job.data?.message || '正在准备检查任务'} />) : null}
        {problem ? <Note tone="error" title="操作未完成">{problem}</Note> : null}
        {failures.length ? (
          <Note tone="error" title={`${failures.length} 个来源检查失败`}
            extra={<ul className="flex flex-col gap-0.5 text-body-2-regular">
              {failures.map((row, at) => (
                <li key={`${row.provider || ''}-${row.ref || at}`}>
                  {`${row.provider_label || row.provider || ''} ${row.author || row.label || row.ref || ''}：${row.error || '未说明原因'}`}
                </li>
              ))}
            </ul>}>
            这些来源这一轮没有取到更新。
          </Note>
        ) : null}
        {evidence ? <Note tone="warning">{`候选已入库，但这一次的原始响应没有留档：${evidence}`}</Note> : null}
      </div>

      {chosen.length ? (
        <div role="group" aria-label="关注来源批量操作"
          className="flex flex-wrap items-center gap-2 rounded-2lg bg-background-secondary-default px-3 py-2">
          <span role="status" className="mr-auto text-body-2-regular text-text-primary">
            {`已选 ${chosen.length} 个来源`}
          </span>
          <Button variant="secondary" size="small" disabled={readOnly}
            {...busyProps(rowHandlers.busy)} onClick={() => startChecking(chosen)}>检查所选</Button>
          <Button variant="secondary" size="small" disabled={readOnly} {...busyProps(bulk.isPending)}
            onClick={() => bulk.mutate({ ids: chosen, action: 'enabled' })}>启用</Button>
          <Button variant="secondary" size="small" disabled={readOnly} {...busyProps(bulk.isPending)}
            onClick={() => bulk.mutate({ ids: chosen, action: 'paused' })}>暂停</Button>
          <Button variant="danger" size="small" disabled={readOnly} {...busyProps(bulk.isPending)}
            onClick={() => void confirmModal({
              title: `删除 ${chosen.length} 个关注来源`,
              body: '将移除所选关注来源及其已抓取条目，媒体文件保留。',
              confirmLabel: '删除所选来源', danger: true,
              onConfirm: () => bulk.mutateAsync({ ids: chosen, action: 'remove' }),
            })}>删除</Button>
          <Button variant="ghost" size="small" onClick={() => onSelected(new Set())}>取消选择</Button>
        </div>
      ) : null}

      {asTable ? (
        <Table aria-label="关注来源"
          sortDescriptor={sorting[0]
            ? { column: sorting[0].id, direction: sorting[0].desc ? 'descending' : 'ascending' }
            : undefined}
          onSortChange={(descriptor) => table.setSorting([
            { id: String(descriptor.column), desc: descriptor.direction === 'descending' },
          ])}>
          <TableHeader>
            {table.getHeaderGroups()[0]!.headers.map((header) => {
              const sortable = header.column.id in COLUMN_SORT;
              const text = flexRender(header.column.columnDef.header, header.getContext());
              return (
                <TableColumn key={header.id} id={header.id} allowsSorting={sortable}
                  isRowHeader={header.column.id === 'source'}>
                  {sortable ? text : <VisuallyHidden>{text}</VisuallyHidden>}
                </TableColumn>
              );
            })}
          </TableHeader>
          {/* 选中与否由每行第一格那个勾表示：行底色归 Table 自己，另铺一层就是在它的
              hover 与焦点态上面再画一遍。 */}
          <TableBody renderEmptyState={() => '这一页没有来源'}>
            {pageRows.map((row) => (
              <TableRow key={row.id} id={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <>
          <Checkbox isSelected={pageState.all} isIndeterminate={pageState.some}
            onChange={(on) => toggleMany(pageIds, on)} aria-label="全选本页来源">全选本页</Checkbox>
          <div className="flex flex-col gap-3">
            {groups.slice(win.start, win.end).map((group) => {
              const key = String(group[0]!.author_key || group[0]!.id);
              return (
                <AuthorCard key={key} group={group} name={authorName(group, aliases)}
                  handlers={rowHandlers} selected={selected} open={!collapsed.has(key)}
                  onOpen={(open) => {
                    const next = new Set(collapsed);
                    if (open) next.delete(key); else next.add(key);
                    setCollapsed(next);
                  }}
                  onToggleGroup={(on) => toggleMany(group.map((source) => source.id), on)}
                  onToggle={toggleOne} />
              );
            })}
          </div>
        </>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-body-2-regular text-text-secondary">
          {`${win.start + 1}–${win.end} / ${win.total} ${asTable ? '个来源' : '位创作者'}`}
        </span>
        <Select aria-label="每页显示数量" size="sm" selectedKey={String(pageSize)}
          onSelectionChange={(key) => { if (key !== null) table.setPageSize(Number(key)) }}>
          {PAGE_SIZES.map((size) => (
            <SelectItem key={size} id={String(size)}>
              {`每页 ${size} ${asTable ? '条' : '位'}`}
            </SelectItem>
          ))}
        </Select>
        <Pagination page={win.page} pages={win.pages}
          onPage={(next) => table.setPageIndex(next - 1)} />
      </div>

      {counts.new ? (
        <div className="flex flex-wrap items-center gap-2 border-t border-separator-border pt-3">
          <span className="mr-auto text-body-2-regular text-text-secondary">
            {`未看 ${counts.new} · 已看 ${counts.seen || 0} · 已保存 ${counts.saved || 0} · 已忽略 ${counts.ignored || 0}`}
          </span>
          <Button variant="secondary" size="small" onClick={openFollow}>去看更新</Button>
          <Button variant="secondary" size="small" disabled={readOnly} {...busyProps(markAll.isPending)}
            onClick={() => void confirmModal({
              title: '标记已看', body: '将把当前未看作品标记为已看。', confirmLabel: '标记已看',
              onConfirm: () => markAll.mutateAsync('seen'),
            })}>全部标记已看</Button>
          <Button variant="secondary" size="small" disabled={readOnly} {...busyProps(markAll.isPending)}
            onClick={() => void confirmModal({
              title: '标记已忽略', body: '将把当前未看作品标记为已忽略。', confirmLabel: '标记已忽略',
              onConfirm: () => markAll.mutateAsync('ignored'),
            })}>全部忽略</Button>
        </div>
      ) : null}
    </div>
  );
}
