/* 换头像的数据契约。
 *
 * 候选图走 `/avatar-choice?ref=`：页面只递服务端自己列出来的 ref，地址由服务端按索引拼。
 * 手填地址那一条是唯一的例外，它在服务端有自己的公网判据。 */
import { ApiError, apiGet, apiSend } from '../../api';

export const AVATAR_CHOICES_URL = '/api/avatar-choices';
export const AVATAR_PICK_URL = '/api/avatar-pick';
const AVATAR_CHOICE_IMAGE_URL = '/avatar-choice';

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

/** 一个人一个键：换个人就是另一份候选，不该读到上一个人的。 */
export const avatarChoicesKey = (kind: string, id: number) => ['avatar-choices', kind, id] as const;

const query = (kind: string, id: number) => `?kind=${encodeURIComponent(kind)}&id=${id}`;

export const choiceImageUrl = (kind: string, id: number, ref: string) =>
  `${AVATAR_CHOICE_IMAGE_URL}${query(kind, id)}&ref=${encodeURIComponent(ref)}`;

export const fetchAvatarChoices = (kind: string, id: number, signal?: AbortSignal) =>
  apiGet<AvatarChoices>(AVATAR_CHOICES_URL + query(kind, id), signal);

/** 三条路交上去的东西不同，落点是同一个端点。 */
export type AvatarSubmission = { ref: string } | { url: string } | { file: File };

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
  if (!data) return '正在找可用的图…';
  const elsewhere = data.matched_names.filter((one) => one !== name);
  if (elsewhere.length) return `${name}：图库里按「${elsewhere.join('」「')}」找到的。`;
  return data.choices.length
    ? `${name}：换上的那张留在本机，随时能换回来。`
    : `${name}：图库里没有这个名字，用下面两种方式换。`;
}

/** 图库索引还没取过、这一次也一张图库图都没拿到：能走的只剩手填那两条路。 */
export const indexNotReady = (data: AvatarChoices | undefined): boolean =>
  !!data && data.index_stale && !data.choices.some((one) => one.source === 'gfriends');

const SOURCE_LABELS: Record<string, string> = { gfriends: '图库', history: '用过的' };

/** 一格的完整说明，进 `title`：哪儿来的、多大、按谁找到的。 */
export const choiceDetail = (choice: AvatarChoice): string =>
  `${SOURCE_LABELS[choice.source] || choice.source} · ${choice.label}`
  + (choice.width ? ` · ${choice.width}×${choice.height}` : '')
  + (choice.found_by ? ` · 按「${choice.found_by}」找到` : '');
