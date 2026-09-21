/* 数据管理页上的「扫描与采集」卡片。
 *
 * 卡片里讲的是那颗按钮此刻在做什么（进度或等待点）；结果和故障讲的是这一趟任务的下场，
 * 挂在卡片外面，和链接管理、资源同步那两块同一个写法。
 *
 * 写操作是 `useMutation`：服务端回的就是这一趟的新快照，用 `setQueryData` 换进缓存，
 * 再让这个键立刻重读一次接上轮询的节律。首屏读到的旧终态不冒充新结果——任务关掉页面
 * 照样在跑，状态里常年躺着上一趟的回执，判据在 `use-library-processing.ts`。 */
import { useEffect, useRef, useState } from 'react';
import {
  RiArrowDownSLine, RiArrowRightLine, RiDatabase2Line, RiGlobalLine, RiHardDrive2Line,
} from '@remixicon/react';
import { useMutation } from '@tanstack/react-query';
import { Dialog, Popover } from 'react-aria-components';
import { attachOverlayScrollbar } from '@peach/legacy/ui';

import { Button } from '@/components/base/buttons/button';
import { LinkButton } from '@/components/base/buttons/link-button';
import {
  MENU_ITEM, MENU_ITEM_INTERACTIVE, MENU_POPOVER_SURFACE,
} from '@/components/base/dropdown/menu-styles';
import { cx } from '@/utils/cx';

import { apiSend, errorMessage } from '../../api';
import type { LibraryProcessingProps } from '../bundle';
import { LoadingDots } from '../components/loading-dots';
import { Note } from '../components/note';
import { PathLine } from '../components/path-line';
import { Progress } from '../components/progress';
import { Disclosure } from '../settings/section';
import { busyProps } from '../settings/use-action';
import { queryClient } from '../query';
import {
  currentLine, DISCONNECTED_TEXT, issueDetails, LIBRARY_PROCESSING_KEY, LIBRARY_PROCESSING_URL,
  notesLine, type LibraryProcessingCommand, type LibraryProcessingData,
} from './library-processing';
import { useLibraryProcessingJob } from './use-library-processing';

/** 菜单里那两种只跑一半的方式。主键「扫描并补全资料」两段都跑，交的是空请求体。 */
const PARTIAL_RUNS = [
  { label: '扫描并补全资料', icon: RiDatabase2Line, command: {} },
  { label: '只扫描', icon: RiHardDrive2Line, command: { stage: 'scan' } },
  { label: '只采集', icon: RiGlobalLine, command: { stage: 'collect' } },
] as const;

const MENU_ROW = cx(MENU_ITEM, MENU_ITEM_INTERACTIVE, 'text-body-2-medium');

/* 中文正文写成常量：JSX 里换行的文字会在接缝处多出一个空格，中文句子里看得见。 */
const CARD_TEXT = '扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，'
  + '几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。';
const STALLED_TEXT = '这个项目处理时间较长，暂时没有新进展。可以继续等待，或在任务结束后重试未完成项。';
/* 补齐女优资料是落库之后的一步，一趟里常常什么都不用补，那时这句话不出现：
   四个读数全是 0 还写一句「别名 0 个」，读的人分不清是没得补还是这一步没跑。 */
const profileText = (state: LibraryProcessingData) => {
  const aliases = state.performer_aliases || 0;
  const avatars = state.performer_avatars || 0;
  const conflicts = state.performer_profile_conflicts || 0;
  const failed = state.performer_profile_failed || 0;
  if (!aliases && !avatars && !conflicts && !failed) return '';
  const parts = [`补齐女优资料：别名 ${aliases} 个，头像 ${avatars} 张`];
  if (conflicts) parts.push(`${conflicts} 个同名冲突交回人工`);
  if (failed) parts.push(`${failed} 张头像未取得`);
  return `${parts.join('，')}。`;
};

const receiptText = (state: LibraryProcessingData) =>
  `已扫描 ${state.scanned || 0} 个文件，识别 ${state.identified || 0} 个番号，`
  + `整理 ${state.candidates || 0} 组资料候选，自动落库 ${state.auto_applied || 0} 条。`
  + profileText(state);

/** 主键加一个下拉：三种方式改的是同一件事，摊成三颗按钮读不出哪个是常用的那一个。
 *
 *  注册表 `dropdown` 条目的 `DropdownTrigger` 自己就是那颗按钮、外观全由 className 给，
 *  套不进 BoardUI `Button` 的档位，所以触发键用 `Button`、面板用 React Aria 的
 *  `Popover` + `Dialog` 组合，行的外观仍取 `menu-styles.ts`（登记在 `boardui/ORIGIN.md`）。 */
function ScanActions({ busy, onRun }: { busy: boolean; onRun(command: LibraryProcessingCommand): void }) {
  const trigger = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const run = (command: LibraryProcessingCommand) => {
    if (busy) return;
    setOpen(false);
    onRun(command);
  };
  return (
    <>
      <span data-button-group data-split-button data-variant="primary">
        <Button leadingIcon={RiDatabase2Line} onClick={() => run({})} {...busyProps(busy)}>
          扫描并补全资料
        </Button>
        <Button ref={trigger} iconOnly leadingIcon={RiArrowDownSLine}
          aria-label="更多扫描与采集方式" aria-haspopup="dialog" aria-expanded={open}
          {...busyProps(busy)} onClick={() => { if (!busy) setOpen(true) }} />
      </span>
      <Popover triggerRef={trigger} isOpen={open} onOpenChange={setOpen}
        placement="bottom end" offset={4} className={MENU_POPOVER_SURFACE}>
        <Dialog aria-label="更多扫描与采集方式" className="flex w-52 flex-col gap-1 outline-none">
          {PARTIAL_RUNS.map(({ label, icon: Glyph, command }) => (
            <button key={label} type="button" className={MENU_ROW} onClick={() => run(command)}>
              <Glyph aria-hidden className="size-4 shrink-0" />
              {label}
            </button>
          ))}
        </Dialog>
      </Popover>
    </>
  );
}

/** 卡片外面那一块：这一趟怎么了。逐条明细要展开才读，完整清单在状态给出的日志文件里。 */
function Outcome(
  { state, problem, settled, onRetry, toast }:
  {
    state: LibraryProcessingData; problem: string;
    settled: LibraryProcessingData | null; onRetry(): void; toast(message: string): void;
  },
) {
  const details = issueDetails(state);
  const retryable = state.status === 'failed' && !!state.retryable_asset_ids?.length;
  const notes = notesLine(state.notes || {});
  const list = useRef<HTMLUListElement>(null);
  /* 清单是这一页唯一自己滚的块，原生滚动条在这儿就是一条系统灰柱子。挂全站那条覆盖式
     的：它自带「已挂过」标记，所以每次渲染都试一次，清单从无到有那一次才挂得上。 */
  useEffect(() => { attachOverlayScrollbar(list.current) });
  return (
    /* 空着时整块收起：`aria-live` 的容器留着一条空轨道，卡片底下就凭空多出一个间距。 */
    <div aria-live="polite" className="flex flex-col gap-4 empty:hidden">
      {state.status === 'running' && state.stalled
        ? <Note tone="warning" title="处理较慢">{STALLED_TEXT}</Note>
        : null}
      {problem || state.status === 'failed'
        ? <Note tone="error"
            action={retryable
              ? <Button variant="primary" size="small" onClick={onRetry}>重试未完成项</Button>
              : null}
            extra={details
              /* 三层东西叠在同一块红底上：一句结论、一份清单、一条日志地址。各自之间
                 横一条自己颜色的发丝线，读的人才看得出哪一段结束了——只靠间距的话，
                 几十条同样长短的明细会连成一片。 */
              ? <div className="mt-1.5 border-t border-current/20 pt-1.5">
                  <Disclosure summary={details.label}>
                    {/* 轨道是滚动容器的兄弟，得有一层只裹着清单的定位祖先给它落脚。 */}
                    <div className="relative">
                      {/* 条间线画在每条自己身上，不用 `divide-y`：那一族的选择器裹在
                          `:where()` 里没有特异性，压不过岛内 `@scope` 末尾那条把所有元素
                          边框清零的 preflight，线会静默消失。 */}
                      <ul ref={list} className="max-h-96 overflow-y-auto pr-3">
                        {details.items.map((item) => (
                          <li key={item.key}
                            className="flex flex-col gap-0.5 border-b border-current/15 py-2 first:pt-1 last:border-b-0 last:pb-1">
                            {item.href
                              ? <a href={item.href} className="text-body-2-medium underline-offset-4 hover:underline">{item.label}</a>
                              : <span className="text-body-2-medium">{item.label}</span>}
                            <span className="text-caption-1-regular">{item.note}</span>
                            {item.hint ? <code className="text-caption-1-regular break-all">{item.hint}</code> : null}
                          </li>
                        ))}
                      </ul>
                    </div>
                    {details.log
                      /* 完整记录不是这条提示在说的事，它是出事之后自己去翻的东西：
                         留在红底上但退回灰字，分隔线跟着它一起淡下去。 */
                      ? <div className="mt-2 border-t border-separator-border pt-2 text-text-secondary">
                          <PathLine path={details.log} prefix="完整记录：" className="text-caption-1-regular"
                            onRevealed={toast} />
                        </div>
                      : null}
                  </Disclosure>
                </div>
              : null}>
            {problem || state.error || '处理未完成，请重试'}
          </Note>
        : null}
      {settled?.status === 'complete'
        ? <Note tone="success" title="处理完成">{receiptText(settled)}</Note>
        : null}
      {state.status !== 'running' && notes
        ? <Note tone="neutral"
            extra={state.issues_log
              ? <div className="mt-1.5 border-t border-separator-border pt-1.5">
                  <PathLine path={state.issues_log} prefix="完整记录：" className="text-caption-1-regular"
                    onRevealed={toast} />
                </div>
              : null}>
            {notes}
          </Note>
        : null}
    </div>
  );
}

export function LibraryProcessingCard(props: LibraryProcessingProps) {
  const { toast, onComplete } = props;
  const { job, settled, forget } = useLibraryProcessingJob(props);
  const start = useMutation({
    mutationFn: (command: LibraryProcessingCommand) =>
      apiSend<LibraryProcessingData>(LIBRARY_PROCESSING_URL, command),
    onSuccess: (next) => {
      forget();
      // 回的就是这一趟的新快照，换进缓存即可；节律由这个键说了算，让它立刻重读一次接上。
      queryClient.setQueryData(LIBRARY_PROCESSING_KEY, next);
      void queryClient.invalidateQueries({ queryKey: LIBRARY_PROCESSING_KEY });
    },
  });
  // 这一趟跑完了就让遗留层重画数据管理页那几个计数：复核与候选的读数跟着它变。
  useEffect(() => { if (settled) onComplete?.() }, [settled, onComplete]);

  const state = job.data ?? { status: 'idle' };
  const problem = start.error ? errorMessage(start.error)
    : job.isError ? (job.data ? DISCONNECTED_TEXT : errorMessage(job.error))
    : '';
  const busy = start.isPending || state.status === 'running';
  const retryable = state.status === 'failed' && !!state.retryable_asset_ids?.length;
  const line = currentLine(state);

  const run = (command: LibraryProcessingCommand) => {
    if (busy) return;
    start.reset();
    start.mutate(command);
  };
  const retry = () => {
    if (!state.job_id || !state.retryable_asset_ids?.length) return;
    run({ job_id: state.job_id, retry: state.retryable_asset_ids });
  };

  return (
    <div className="flex flex-col gap-4">
      <section aria-label="扫描与采集" data-geist-fieldset data-cleanup-task data-cleanup-processing>
        <div data-geist-fieldset-content>
          <h3 className="text-title-2-medium text-text-primary">扫描与采集</h3>
          <p className="text-body-2-regular text-text-secondary">{CARD_TEXT}</p>
          {state.status === 'running'
            ? <div className="flex flex-col gap-1.5">
                {state.total
                  ? <>
                      <Progress label={line} value={state.checked || 0} max={state.total} />
                      <p className="text-caption-1-regular text-text-secondary">
                        {line} · {state.checked || 0} / {state.total} 个视频
                      </p>
                    </>
                  : <LoadingDots label={line} />}
              </div>
            : null}
        </div>
        <footer data-geist-fieldset-footer>
          <LinkButton href="/scraping" size="small" trailingIcon={RiArrowRightLine}>来源和凭证</LinkButton>
          {state.candidates
            ? <LinkButton href="/review" size="small" trailingIcon={RiArrowRightLine}>复核资料</LinkButton>
            : null}
          {/* 失败且有可重试项时，这一趟该做的事是「重试未完成项」，它在下面那条错误提示里。 */}
          {retryable ? null : <ScanActions busy={busy} onRun={run} />}
        </footer>
      </section>
      <Outcome state={state} problem={problem} settled={settled} onRetry={retry} toast={toast} />
    </div>
  );
}
