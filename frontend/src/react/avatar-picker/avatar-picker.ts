/* 换头像的数据契约。
 *
 * 候选图走 `/avatar-choice?ref=`：页面只递服务端自己列出来的 ref，地址由服务端按索引拼。
 * 手填地址那一条是唯一的例外，它在服务端有自己的公网判据。 */
import { ApiError, apiGet, apiSend } from '../../api';
import {
  centeredBox, frameWithin, isUsableSize, type CropBox, type CropSize,
} from '../../crop-geometry';

export const AVATAR_CHOICES_URL = '/api/avatar-choices';
export const AVATAR_PICK_URL = '/api/avatar-pick';
export const AVATAR_CODE_COVER_URL = '/api/avatar-code-cover';
const AVATAR_CHOICE_IMAGE_URL = '/avatar-choice';

export interface AvatarChoice {
  ref: string;
  source: 'gfriends' | 'history' | 'asset' | 'code';
  label: string;
  width: number;
  height: number;
  detail: string;
  /** 这一格是按哪个名字从图库里找到的。只有一个名字命中时是空串。 */
  found_by: string;
  current: boolean;
  /** 这一格必须先框一块再装。作品画面是横图，整张装进圆框只剩一块背景。 */
  crop: boolean;
  /** 框选时可以换的底图，按 ref 给：封面加九宫格那九格。 */
  bases: string[];
  /** 封面上该取景的那一块（脸周围的方图，没检出脸的封套是正封），源图像素。
   *  只对 `ref` 那一张、`width`×`height` 那个尺寸作数。 */
  focus: CropBox | null;
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

/** 一个人一个键：换个人就是另一份候选，不该读到上一个人的。 */
export const avatarChoicesKey = (kind: string, id: number) => ['avatar-choices', kind, id] as const;

const query = (kind: string, id: number) => `?kind=${encodeURIComponent(kind)}&id=${id}`;

export const choiceImageUrl = (kind: string, id: number, ref: string) =>
  `${AVATAR_CHOICE_IMAGE_URL}${query(kind, id)}&ref=${encodeURIComponent(ref)}`;

export const fetchAvatarChoices = (kind: string, id: number, signal?: AbortSignal) =>
  apiGet<AvatarChoices>(AVATAR_CHOICES_URL + query(kind, id), signal);

/** 按番号取一张封面来框。番号不必在馆藏里：本机没有时服务端去官方渠道取。 */
export const fetchCodeCover = (code: string) =>
  apiSend<AvatarChoice>(AVATAR_CODE_COVER_URL, { code });

/** 一张候选按 `aspect` 取景的那一块：有取景区就在它里面取，没有就整张图居中。
 *  `size` 不是这一格自己那张图时（换了底图）一律居中：取景区只对它自己的像素作数。 */
export function choiceFrame(choice: AvatarChoice, size: CropSize, aspect: number): CropBox {
  const own = size.width === choice.width && size.height === choice.height;
  return choice.focus && own ? frameWithin(choice.focus, size, aspect) : centeredBox(size, aspect);
}

/** 格子要不要自己取景：只有要框的那几路（作品画面、番号封面）是横图。竖的图库
 *  人像照旧 `object-cover`，尺寸不知道的也是。 */
export const framesItself = (choice: AvatarChoice): boolean =>
  choice.crop && isUsableSize({ width: choice.width, height: choice.height });

/** 框选出来的那一块，源图像素、右下开区间。后端按同一组整数裁。 */
export interface AvatarCrop { x0: number; y0: number; x1: number; y1: number }

/** 四条路交上去的东西不同，落点是同一个端点。`crop` 是其中三条共用的可选工序。 */
export type AvatarSubmission =
  | { ref: string; crop?: AvatarCrop }
  | { url: string; crop?: AvatarCrop }
  | { file: File };

export async function sendAvatarPick(
  kind: string, id: number, submission: AvatarSubmission,
): Promise<void> {
  if (!('file' in submission)) {
    await apiSend(AVATAR_PICK_URL, { kind, id, ...submission });
    return;
  }
  /* 本机文件按原样发字节，不走 multipart：解析 multipart 要多一个依赖，而这里只有
     一个文件、没有别的字段，文件名走查询串。请求体不是 JSON，所以不经 `apiSend`。 */
  const file = submission.file;
  const response = await fetch(
    `${AVATAR_PICK_URL}${query(kind, id)}&name=${encodeURIComponent(file.name)}`,
    { method: 'POST', credentials: 'same-origin', body: file });
  if (response.ok) return;
  const payload = await response.json().catch(() => null) as { error?: string } | null;
  throw new ApiError(payload?.error || `请求失败（${response.status}）`, response.status, payload);
}

/** 说明只留一句：这一屏已经用图说清了在选什么，多一行字就是多一行要读的东西。
 *  按哪个名字找到的要说——找错人是这里唯一会出的大错，而名字是唯一的线索。 */
export function pickerNote(name: string, data: AvatarChoices | undefined): string {
  // 候选在路上时网格里是 Skeleton，这里不再另写一句「正在读取」。
  if (!data) return name;
  const elsewhere = data.matched_names.filter((one) => one !== name);
  if (elsewhere.length) return `${name}：图库里按「${elsewhere.join('」「')}」找到的。`;
  return data.choices.length
    ? `${name}：换上的那张留在本机，随时能换回来。`
    : `${name}：图库里没有这个名字，用下面两种方式换。`;
}

/** 图库索引还没取过、这一次也一张图库图都没拿到：能走的只剩手填那两条路。 */
export const indexNotReady = (data: AvatarChoices | undefined): boolean =>
  !!data && data.index_stale && !data.choices.some((one) => one.source === 'gfriends');

const SOURCE_LABELS: Record<string, string> = {
  gfriends: '图库', history: '用过的', asset: '作品画面', code: '番号封面',
};

/** 底图那一排每一格的名字：封面一格，九宫格九格按位置数。 */
export function baseLabel(ref: string): string {
  if (ref.startsWith('cover:')) return '封面';
  const what = ref.split(':')[2] || '';
  if (what === 'cover') return '封面';
  const cell = Number(what.replace('cell', ''));
  return Number.isFinite(cell) ? `第 ${cell + 1} 格` : what;
}

/** 一格的完整说明，进 `title`：哪儿来的、多大、按谁找到的。 */
export const choiceDetail = (choice: AvatarChoice): string =>
  `${SOURCE_LABELS[choice.source] || choice.source} · ${choice.label}`
  + (choice.width ? ` · ${choice.width}×${choice.height}` : '')
  + (choice.found_by ? ` · 按「${choice.found_by}」找到` : '');
