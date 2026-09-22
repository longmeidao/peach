/* 换头像：资料页圆框角上那个加号。
 *
 * 自动挑的那张按来源优先级来，而那个顺序回答的是「先试哪一张」，不是「哪一张适合当
 * 头像」——图库里排第一的常常是压着书名的写真封面，同一个人往下翻几张就有片商的正脸
 * 原图。所以这里不做更聪明的自动挑选，只把候选摊开让人看一眼就能换。
 *
 * 这一屏要回答的是「换成哪一张」，所以候选网格占掉中间全部高度，头部和底下那排操作
 * 固定不动，只有网格滚。候选到点开弹层才取：资料页每进一次就预取一遍，多数时候没人点。
 * 注册表里没有模态弹层，用 React Aria 的 `Modal` 组合，差异登记在 `../boardui/ORIGIN.md`。 */
import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent, CSSProperties } from 'react';
import { RiAddLine, RiCloseLine, RiUserLine } from '@remixicon/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Dialog, Heading, Modal, ModalOverlay } from 'react-aria-components';

import { Chip } from '@/components/base/badges/chip';
import { Button } from '@/components/base/buttons/button';
import { IconButton } from '@/components/base/buttons/icon-button';
import { Input } from '@/components/base/input/input';

import { errorMessage } from '../../api';
import { centeredBox, isUsableSize, previewStyle, type CropBox, type CropSize } from '../../crop-geometry';
import type { AvatarPickerProps } from '../bundle';
import { Note } from '../components/note';
import { useOverlayScrollbar } from '../components/overlay-scrollbar';
import { CropFrame } from '../crop/crop-frame';
import { queryClient } from '../query';
import { busyProps } from '../settings/use-action';
import {
  avatarChoicesKey, baseLabel, choiceDetail, choiceImageUrl, fetchAvatarChoices, indexNotReady,
  pickerNote, sendAvatarPick, type AvatarChoice, type AvatarSubmission,
} from './avatar-picker';

export function AvatarPicker({ kind, entityId, name, onPicked }: AvatarPickerProps) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {/* 加号压在圆框右下角那一圈上——它属于这张头像，离得远了就成了页面上一个不知道
          管什么的按钮。定位归外面这一层；头像那张图自己带 `z-index:1`，这一层要抬到它上面，
          不然按钮有一半藏在图底下。按钮收成 28px 的圆——它坐在一个圆的边上，方钮压在弧线
          上会遮掉一大块脸；一圈页面底色的描边把它和图分开。BoardUI 的 IconButton 只有方形，
          形状归组件自己管，所以这里是一枚原生按钮，底色、描边、悬停与焦点环取它同一套 token。
          悬停时底色透出身后的脸：暗色那档的悬停色本来就带 60% 透明，浅色那档是实色，
          这里给它补同样的 60%，两档读起来是同一个动作。 */}
      <span className="absolute right-1 bottom-1 z-10">
        <button type="button" aria-haspopup="dialog" aria-label={`更换${name}的头像`}
          onClick={() => setOpen(true)}
          className="flex size-7 cursor-pointer items-center justify-center rounded-full border border-border-button-default bg-background-primary-default text-foreground-icon-primary shadow-xs outline-none ring-2 ring-background-full transition-colors hover:border-border-button-hover hover:bg-background-primary-hover/60 dark:hover:bg-background-primary-hover focus-visible:ring-border-focus-ring active:bg-background-primary-active">
          <RiAddLine aria-hidden className="size-4" />
        </button>
      </span>
      {/* 层级取遗留壳的 `--layer-dialog`：顶栏和侧栏各有自己的 z-index，比 Tailwind 那档
          `z-50` 都高，遮罩压不住它们，弹层开着时那两块还亮着。 */}
      <ModalOverlay isOpen={open} onOpenChange={setOpen} isDismissable
        className="fixed inset-0 z-dialog flex items-center justify-center bg-scrim p-4">
        <Modal className="flex max-h-full w-full max-w-avatar-picker flex-col overflow-hidden rounded-2-5xl border border-separator-border bg-background-full shadow-dropdown">
          <Dialog aria-label="更换头像" className="flex min-h-0 flex-col outline-none">
            <PickerBody kind={kind} entityId={entityId} name={name} onPicked={onPicked}
              close={() => setOpen(false)} />
          </Dialog>
        </Modal>
      </ModalOverlay>
    </>
  );
}

/** 弹层内容。只在弹层开着时挂载，候选也就只在这时候取。 */
function PickerBody({ kind, entityId, name, onPicked, close }: AvatarPickerProps & { close(): void }) {
  const file = useRef<HTMLInputElement>(null);
  const grid = useOverlayScrollbar<HTMLDivElement>();
  const [url, setUrl] = useState('');
  const [fileProblem, setFileProblem] = useState('');
  /* 作品画面那一组点开的是框选，不是当场换图。整屏换掉而不是再叠一层弹层：这一步
     要的是尽可能大的底图，而弹层套弹层只会让底图更小。 */
  const [cropping, setCropping] = useState<AvatarChoice | null>(null);
  const key = avatarChoicesKey(kind, entityId);
  const picked = useRef(false);

  const listing = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => fetchAvatarChoices(kind, entityId, signal),
    // 上一次点开没取到就重来。取到过的那一份留着，反复开合不必每次再问一遍。
    retryOnMount: true,
  });
  /* 换成功之后这一份候选里「在用」是哪一格已经过期，扔掉它，下次点开重新取。要等到弹层
     真的收起来再扔：这时候还有人在读这个键，当场清掉它会立刻再取一遍，白问一趟。 */
  useEffect(() => () => {
    if (picked.current) queryClient.removeQueries({ queryKey: avatarChoicesKey(kind, entityId) });
  }, [kind, entityId]);
  /* 三种来源共用一个出口，成功后就地关掉并让宿主重画。失败留在原地并说出原因——
     这一步会改掉盘上的图，静默失败等于让人以为换好了。 */
  const submit = useMutation({
    mutationFn: (submission: AvatarSubmission) => sendAvatarPick(kind, entityId, submission),
    onSuccess: () => {
      picked.current = true;
      close();
      onPicked();
    },
  });

  function pickFile(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const chosen = input.files?.[0];
    input.value = '';
    setFileProblem('');
    if (chosen) submit.mutate({ file: chosen });
  }

  const data = listing.data;
  const choices = data?.choices ?? [];
  const problem = fileProblem
    || (submit.error ? errorMessage(submit.error) : '')
    || (listing.error ? errorMessage(listing.error) : '');
  return (
    <>
      {/* 头部：左边一个方图标槽，右边标题加一句说明，右上角是关闭键。 */}
      <div className="flex shrink-0 items-start gap-4 p-5">
        <span aria-hidden className="flex size-14 shrink-0 items-center justify-center rounded-2xl border border-separator-border bg-background-secondary-default text-foreground-icon-secondary">
          <RiUserLine className="size-6" />
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Heading slot="title" className="text-title-3-semibold text-text-primary">
              {cropping ? '框出头像那一块' : '更换头像'}
            </Heading>
            {!cropping && choices.length ? <Chip color="soft">{choices.length} 张可选</Chip> : null}
          </div>
          <p className="text-body-2-regular text-text-secondary">
            {cropping
              ? `${cropping.label}：拖动方框选一块，滚轮或角上那枚方块改大小。`
              : pickerNote(name, data)}
          </p>
          {!cropping && indexNotReady(data)
            ? <Note tone="neutral">图库索引还没取过，只能从用过的图里选。</Note>
            : null}
          {problem ? <Note tone="error">{problem}</Note> : null}
        </div>
        <IconButton icon={RiCloseLine} size="small" aria-label="关闭" onClick={close} />
      </div>
      {cropping ? (
        <CropStep kind={kind} entityId={entityId} choice={cropping} busy={submit.isPending}
          back={() => setCropping(null)}
          confirm={(ref, crop) => { if (!submit.isPending) submit.mutate({ ref, crop }) }} />
      ) : (
      <>
      {/* 候选网格是这一屏唯一会滚的层：头部和底下那排操作再长也不动。上下各留 16px：
          只留上边的话，最后一排图贴着底下那条线。外面这一层只为放那条覆盖式滚动条的
          轨道，它按 `absolute` 铺，得有一个只裹着滚动块本身的定位祖先。 */}
      <div className="relative flex min-h-0 flex-1 flex-col">
        <div ref={grid} className="flex min-h-0 flex-1 flex-col overflow-y-auto border-t border-separator-border px-5 py-4">
          <div role="listbox" aria-label="候选头像"
            className="inline-grid grid-cols-3 content-start gap-2 sm:grid-cols-4">
            {choices.map((choice) => (
              <button type="button" key={choice.ref} role="option" data-avatar-choice
                aria-selected={choice.current} title={choiceDetail(choice)} {...busyProps(submit.isPending)}
                onClick={() => {
                  if (submit.isPending) return;
                  if (choice.crop) setCropping(choice);
                  else submit.mutate({ ref: choice.ref });
                }}
                className="relative flex cursor-pointer flex-col gap-1 overflow-hidden rounded-2lg border border-separator-border bg-background-secondary-default pb-1 text-center text-caption-1-regular text-text-secondary outline-none hover:border-border-button-hover hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring aria-selected:border-border-focus-ring aria-selected:bg-background-tertiary-default aria-selected:text-text-primary aria-disabled:cursor-progress aria-disabled:opacity-60">
                <img loading="lazy" alt="" src={choiceImageUrl(kind, entityId, choice.ref)}
                  className="block w-full aspect-avatar-choice object-cover" />
                <span className="truncate px-1">{choice.label}</span>
                {choice.current
                  ? <span className="absolute top-1 left-1"><Chip variant="caption" color="gray">在用</Chip></span>
                  : null}
              </button>
            ))}
          </div>
        </div>
      </div>
      {/* 手填地址和本机文件跟候选是并列的三条路，不是候选看完之后的补充，所以摆在固定
          的那一排里：网格再长也不会把它们推到看不见的地方。 */}
      <div className="flex shrink-0 flex-wrap items-center gap-3 border-t border-separator-border p-5">
        <Button variant="secondary" onClick={() => file.current?.click()}
          {...busyProps(submit.isPending)}>从本机选图片</Button>
        {/* 原生文件选择器长相不可控，按钮归 BoardUI，输入框只留着接文件。 */}
        <input ref={file} type="file" accept="image/png,image/jpeg" tabIndex={-1} aria-hidden
          className="hidden" onChange={pickFile} />
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <div className="min-w-0 flex-1">
            <Input type="url" aria-label="图片地址" placeholder="https://…" value={url} onChange={setUrl} />
          </div>
          <Button disabled={!url.trim()} {...busyProps(submit.isPending)}
            onClick={() => { if (!submit.isPending) submit.mutate({ url: url.trim() }) }}>用这个地址</Button>
        </div>
      </div>
      </>
      )}
    </>
  );
}

/** 框选那一步：一张底图、一个方框、一个圆预览。
 *
 *  比例锁死 1:1 且不给解锁：头像框是圆的，非方图装进去只会被再裁一次，而第二次
 *  裁在哪由 CSS 说了算，人在这里框的那一块就不作数了。 */
function CropStep({ kind, entityId, choice, busy, back, confirm }: {
  kind: string; entityId: number; choice: AvatarChoice; busy: boolean;
  back(): void; confirm(ref: string, crop: CropBox): void;
}) {
  const bases = choice.bases.length ? choice.bases : [choice.ref];
  const [base, setBase] = useState(bases[0]);
  const [size, setSize] = useState<CropSize | null>(null);
  const [box, setBox] = useState<CropBox | null>(null);
  const src = choiceImageUrl(kind, entityId, base);
  const frame = useOverlayScrollbar<HTMLDivElement>();
  /* 换底图就是换一张图，上一张的框一个数都不留：同一组坐标落在另一张图上是一块
     错位的区域，而错位在屏幕上和「本来就框在这儿」看不出区别。 */
  function pickBase(next: string) {
    setBase(next);
    setSize(null);
    setBox(null);
  }
  const preview = box && size ? previewStyle(box, size) : null;
  return (
    <>
      <div ref={frame} className="flex min-h-0 flex-1 flex-col items-center gap-4 overflow-y-auto border-t border-separator-border px-5 py-4">
        <CropFrame src={src} aspect={1} box={box} size={size}
          label={`${choice.label} 的头像取景框`}
          onSize={(next) => {
            setSize(next);
            if (isUsableSize(next)) setBox(centeredBox(next, 1));
          }}
          onBox={setBox} />
        {/* 底图那一排：封面加九宫格九格。一部作品里哪一格有正脸，只能看着换。 */}
        {bases.length > 1 ? (
          <div role="radiogroup" aria-label="底图" className="flex flex-wrap justify-center gap-2">
            {bases.map((ref) => (
              <button type="button" key={ref} role="radio" aria-checked={ref === base}
                data-crop-base onClick={() => pickBase(ref)}
                className="cursor-pointer rounded-lg px-2 py-1 text-caption-1-regular text-text-secondary outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring aria-checked:bg-background-tertiary-default aria-checked:text-text-primary">
                {baseLabel(ref)}
              </button>
            ))}
          </div>
        ) : null}
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-3 border-t border-separator-border p-5">
        {/* 圆预览就是它上线之后的样子。背景图和上面那张是同一个地址，不多取一次。 */}
        <span aria-hidden data-crop-preview
          className="size-crop-preview shrink-0 rounded-full border border-separator-border bg-background-secondary-default bg-(image:--crop-preview) bg-(position:--crop-preview-at) bg-(length:--crop-preview-size) bg-no-repeat"
          style={preview ? {
            '--crop-preview': `url("${src}")`,
            '--crop-preview-size': preview.size,
            '--crop-preview-at': preview.position,
          } as CSSProperties : undefined} />
        <div className="flex flex-1 flex-wrap items-center justify-end gap-3">
          <Button variant="secondary" onClick={back} {...busyProps(busy)}>回候选</Button>
          <Button disabled={!box || !size} {...busyProps(busy)}
            onClick={() => { if (box && !busy) confirm(base, box) }}>用这一块</Button>
        </div>
      </div>
    </>
  );
}
