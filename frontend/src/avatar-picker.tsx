/* 换头像：资料页圆框角上那个加号。
 *
 * 自动挑的那张按来源优先级来，而那个顺序回答的是「先试哪一张」，不是「哪一张适合
 * 当头像」——图库里排第一的常常是压着书名的写真封面，同一个人往下翻几张就有片商的
 * 正脸原图。所以这里不做更聪明的自动挑选，只把候选摊开让人看一眼就能换。
 *
 * 弹层照 BoardUI 的 Pro access 卡片摆（2026-09-12 实测 boardui.com/components/composer）：
 * 左边一个方图标槽、右边标题加一句说明、右上角一枚徽章。这一屏要回答的是「换成哪一
 * 张」，所以候选网格占掉中间全部高度，头部和底下那排操作固定不动，只有网格滚。
 *
 * 候选图走 `/avatar-choice?ref=`：页面只递服务端自己列出来的 ref，地址由服务端按
 * 索引拼。手填地址那一条是唯一的例外，它在服务端有自己的公网判据。 */
import { render } from 'preact';
import { useEffect, useRef, useState } from 'preact/hooks';

import { attachOverlayScrollbar } from '@peach/legacy/ui';

import { apiGet, apiSend, errorMessage } from './api';

export interface AvatarChoice {
  ref: string;
  source: 'gfriends' | 'history';
  label: string;
  width: number;
  height: number;
  detail: string;
  /** 这一格是按哪个名字从图库里找到的。只有一个名字命中时是空串。 */
  found_by: string;
  current: boolean;
}

export interface AvatarChoices {
  kind: string;
  entity_id: number;
  names: string[];
  /** 名字链里在图库中真有图的那几个，按链上的先后。 */
  matched_names: string[];
  choices: AvatarChoice[];
  index_age_hours: number | null;
  index_stale: boolean;
}

interface PickerProps {
  kind: string;
  id: number;
  name: string;
  /** 换成功后让宿主重画头像。遗留层传的是「重新进这一页」。 */
  onPicked(): void;
}

const SOURCE_LABELS: Record<string, string> = {
  gfriends: '图库',
  history: '用过的',
};

function Picker({ kind, id, name, onPicked }: PickerProps) {
  const popup = useRef<HTMLDialogElement>(null);
  const grid = useRef<HTMLDivElement>(null);
  const file = useRef<HTMLInputElement>(null);
  const [data, setData] = useState<AvatarChoices | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [url, setUrl] = useState('');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open || data) return;
    const control = new AbortController();
    apiGet<AvatarChoices>(`/api/avatar-choices?kind=${kind}&id=${id}`, control.signal)
      .then(setData).catch(cause => { if (!control.signal.aborted) setError(errorMessage(cause)) });
    return () => control.abort();
  }, [open, data, kind, id]);

  /* 网格是这一屏唯一会滚的层，滑块用全站那条覆盖式的。`attachOverlayScrollbar`
     自己认已挂过的容器，候选到齐后重画一次也只挂一遍。 */
  useEffect(() => { attachOverlayScrollbar(grid.current) }, [open, data]);

  const show = () => { setOpen(true); popup.current?.showModal() };
  const close = () => { setOpen(false); popup.current?.close() };

  /* 三种来源共用一个出口，成功后就地关掉并让宿主重画。失败留在原地并说出原因——
     这一步会改掉盘上的图，静默失败等于让人以为换好了。 */
  const commit = async (job: () => Promise<unknown>, tag: string) => {
    setBusy(tag); setError('');
    try {
      await job();
      close(); setData(null); onPicked();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy('');
    }
  };

  const pick = (choice: AvatarChoice) => commit(
    () => apiSend('/api/avatar-pick', { kind, id, ref: choice.ref }), choice.ref);

  const fromUrl = () => commit(
    () => apiSend('/api/avatar-pick', { kind, id, url: url.trim() }), 'url');

  /* 本机文件按原样发字节，不走 multipart：解析 multipart 要多一个依赖，而这里
     只有一个文件、没有别的字段。 */
  const fromFile = async (chosen: File) => commit(async () => {
    const response = await fetch(
      `/api/avatar-pick?kind=${kind}&id=${id}&name=${encodeURIComponent(chosen.name)}`,
      { method: 'POST', credentials: 'same-origin', body: chosen });
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { error?: string } | null;
      throw new Error(payload?.error || `请求失败（${response.status}）`);
    }
  }, 'file');

  const choices = data?.choices || [];
  /* 说明只留一句：这一屏已经用图说清了在选什么，多一行字就是多一行要读的东西。
     按哪个名字找到的要说——找错人是这里唯一会出的大错，而名字是唯一的线索。 */
  const elsewhere = (data?.matched_names || []).filter(one => one !== name);
  const note = !data ? '正在找可用的图…'
    : elsewhere.length
      ? `${name}：图库里按「${elsewhere.join('」「')}」找到的。`
      : choices.length ? `${name}：换上的那张留在本机，随时能换回来。`
        : `${name}：图库里没有这个名字，用下面两种方式换。`;
  const stale = !!data && data.index_stale
    && !choices.some(one => one.source === 'gfriends');

  return <div class="avatarpick">
    <button type="button" class="avatarpick-open" onClick={show}
      aria-haspopup="dialog" aria-label={`更换${name}的头像`} title="更换头像">
      <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-plus" /></svg>
    </button>
    {/* 弹层沿用全站的 `.geist-modal`：遮罩、层级和圆角都在那一份里，这里只接管
        开合动画（跟设置弹层同一套）和「头部固定、网格滚」的竖向分栏。 */}
    <dialog ref={popup} class="geist-modal avatarpick-popover" aria-label="更换头像"
      onCancel={close} onClick={event => { if (event.target === popup.current) close() }}>
      <div class="avatarpick-head">
        <span class="avatarpick-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24"><use href="#i-user-round" /></svg>
        </span>
        <div class="avatarpick-headtext">
          <div class="avatarpick-title">
            <h3>更换头像</h3>
            {!!choices.length && <span class="geist-badge">{choices.length} 张可选</span>}
          </div>
          <p>{note}</p>
          {stale && <p class="avatarpick-note">图库索引还没取过，只能从用过的图里选。</p>}
          {error && <p class="avatarpick-error" role="alert">{error}</p>}
        </div>
        {/* 关闭键跟设置弹层是同一个：样式并在那一份选择器里，不另画一遍。 */}
        <button type="button" class="avatarpick-close" onClick={close} aria-label="关闭">
          <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-x" /></svg>
        </button>
      </div>
      {/* 头部之下沉一档的那块内嵌区，网格和手填那一排都在里面——照 BoardUI 卡片：
          上面一层是卡片本身的面，中间整块沉下去，候选卡再浮回卡片的面上。 */}
      <div class="avatarpick-panel">
        <div class="avatarpick-gridwrap">
          <div class="avatarpick-grid" role="listbox" aria-label="候选头像" ref={grid}>
            {choices.map(choice => <button type="button" key={choice.ref} role="option"
              aria-selected={choice.current} disabled={!!busy}
              class={`avatarpick-cell${choice.current ? ' current' : ''}`}
              title={`${SOURCE_LABELS[choice.source] || choice.source} · ${choice.label}`
                + (choice.width ? ` · ${choice.width}×${choice.height}` : '')
                + (choice.found_by ? ` · 按「${choice.found_by}」找到` : '')}
              onClick={() => pick(choice)}>
              <img loading="lazy" alt=""
                src={`/avatar-choice?kind=${kind}&id=${id}&ref=${encodeURIComponent(choice.ref)}`} />
              <span>{choice.label}</span>
              {choice.current && <b>在用</b>}
            </button>)}
          </div>
        </div>
        {/* 手填地址和本机文件跟候选是并列的三条路，不是候选看完之后的补充，所以摆在
            固定的那一排里：网格再长也不会把它们推到看不见的地方。 */}
        <div class="avatarpick-actions">
          <button type="button" class="geist-button" disabled={!!busy}
            onClick={() => file.current?.click()}>从本机选图片</button>
          <input ref={file} type="file" accept="image/png,image/jpeg" hidden
            onChange={event => {
              const chosen = (event.currentTarget as HTMLInputElement).files?.[0];
              (event.currentTarget as HTMLInputElement).value = '';
              if (chosen) void fromFile(chosen);
            }} />
          <div class="avatarpick-url">
            <input type="url" class="geist-input" value={url} placeholder="https://…"
              aria-label="图片地址"
              onInput={event => setUrl((event.currentTarget as HTMLInputElement).value)} />
            <button type="button" class="geist-button" disabled={!url.trim() || !!busy}
              onClick={fromUrl}>用这个地址</button>
          </div>
        </div>
      </div>
    </dialog>
  </div>;
}

/** 挂在资料页圆框旁。宿主换页时自己调 `unmountAvatarPicker`。 */
export function mountAvatarPicker(host: HTMLElement, props: PickerProps): void {
  render(<Picker {...props} />, host);
}

export function unmountAvatarPicker(host: HTMLElement): void {
  render(null, host);
}
