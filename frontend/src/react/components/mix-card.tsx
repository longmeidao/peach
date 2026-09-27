/* 一叠视频的卡片：播放列表页的每一份列表，和首页那张 Mix 卡是同一件东西。
 *
 * 封面后面压着两层纸边，说明它是一叠；悬停时逐张翻过这一叠里的画面（`use-stack-flip.ts`）。
 * 封面右下角是条数徽标，下面一行是这一叠里出镜最多的那几位的头像，标题与一行来源，
 * 最右边留一格给次要动作（点点点菜单）。整块封面是「打开」的点击区，头像各自通往资料页。
 *
 * 卡是媒体卡，不是 Board 的填充卡：透明底、无内边距，面只在封面那一块。纸边、翻页、
 * 徽标底色与叠放头像的让位几何写在 `../styles.css` 的 `[data-mix-*]` 那一组规则里：
 * 伪元素、`color-mix` 与相邻兄弟选择器在工具类里写不出来。 */
import { useState, type ReactNode } from 'react';

import { spriteGlyph } from './sprite-glyph';
import { useStackFlip } from './use-stack-flip';

export { MIX_FLIP_FACES, MIX_FLIP_LEAD_MS, MIX_FLIP_MS } from './use-stack-flip';

const PLAY = spriteGlyph('play');

/** 署名行的一位。`kind` 是 `performer`／`creator`。 */
export interface MixCardFace {
  kind: string;
  id: number;
  name: string;
  has_image?: boolean;
  avatar_focus?: unknown;
}

export interface MixCardProps {
  /** 标题，同时是点击区与菜单的无障碍名称里那个名字。 */
  name: string;
  /** 标题下那一行：这一叠从哪儿来。 */
  caption: ReactNode;
  /** 徽标上的条数。 */
  count: number;
  /** 静止封面的地址。没有就写「无预览」。 */
  poster: string | null;
  /** 悬停时翻过的那几张图的地址，按顺序；最多取前 `MIX_FLIP_FACES` 张。 */
  flipImages(): Promise<readonly string[]>;
  /** 此刻能不能翻（壳的多选、遮挡、减少动效、滚动中）。 */
  canFlip(): boolean;
  /** 署名行的人，最多画五位；一位都没有时画标题首字。 */
  faces: readonly MixCardFace[];
  /** 圆框里那段 HTML，由遗留层 `avatarInner` 拼：有图走图，没图退首字母。 */
  faceAvatar(face: MixCardFace): string;
  /** 点头像：去这个人的资料页。 */
  onOpenEntity(kind: string, name: string): void;
  /** 点封面。不给就是这一叠没有去处（空列表），点击区不可点。 */
  onOpen?: () => void;
  /** 封面点击区的无障碍名称，例如「打开播放列表 周末慢看」。 */
  openLabel: string;
  /** 署名行最右那一格：次要动作的菜单。 */
  menu?: ReactNode;
}

/** 静止封面。取不到时把图撤掉，只剩黑底，同遗留层 `data-drop="self"`。 */
function Poster({ src }: { src: string }) {
  const [broken, setBroken] = useState(false);
  if (broken) return null;
  return (
    <img data-mix-poster="" src={src} alt="" loading="lazy" onError={() => setBroken(true)}
      className="absolute inset-0 block size-full object-contain" />
  );
}

/** 圆框共用的那一副：38px 正圆，图铺满，首字母居中。 */
const RING = 'relative inline-grid size-9.5 flex-none place-items-center overflow-hidden rounded-full'
  + ' bg-background-secondary-default text-body-2-regular text-text-secondary'
  + ' [&_img]:absolute [&_img]:inset-0 [&_img]:block [&_img]:size-full [&_img]:object-cover';

function Avatars({ faces, fallback, faceAvatar, onOpenEntity }: {
  faces: readonly MixCardFace[]; fallback: string;
  faceAvatar: MixCardProps['faceAvatar']; onOpenEntity: MixCardProps['onOpenEntity'];
}) {
  if (!faces.length) {
    return <span data-mix-initial="" aria-hidden className={`${RING} mt-0.5`}>{fallback}</span>;
  }
  return (
    <div data-mix-avatars="">
      {faces.slice(0, 5).map((face) => (
        <button key={`${face.kind}:${face.id}`} type="button" title={`打开资料页：${face.name}`}
          aria-label={`打开资料页：${face.name}`} onClick={() => onOpenEntity(face.kind, face.name)}
          className={`${RING} cursor-pointer outline-none`}
          dangerouslySetInnerHTML={{ __html: faceAvatar(face) }} />
      ))}
    </div>
  );
}

export function MixCard({
  name, caption, count, poster, flipImages, canFlip, faces, faceAvatar, onOpenEntity, onOpen, openLabel, menu,
  ...data
}: MixCardProps & Record<`data-${string}`, string>) {
  const flip = useStackFlip({ load: flipImages, canFlip });
  return (
    <article {...data} data-mix-card="" onMouseEnter={flip.onPointerEnter} onMouseLeave={flip.onPointerLeave}
      className="relative flex min-w-0 cursor-pointer flex-col gap-2">
      <div data-mix-stack="" className="relative isolate rounded-surface">
        <div data-mix-cover=""
          className="relative z-1 flex aspect-video items-center justify-center overflow-hidden rounded-surface">
          {poster
            ? <Poster key={poster} src={poster} />
            : <span className="text-caption-1-regular tracking-caps text-text-secondary uppercase">无预览</span>}
          <div data-mix-faces="" hidden={!flip.faces.length}>
            {flip.faces.map((src, index) => (
              <div key={src} data-mix-face={index === flip.current ? 'on' : index === flip.leaving ? 'off' : ''}>
                <img src={src} alt="" loading="eager" />
              </div>
            ))}
          </div>
          <button type="button" data-mix-open="" aria-label={openLabel} disabled={!onOpen} onClick={onOpen}
            className="absolute inset-0 z-1 cursor-pointer rounded-surface outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-border-focus-ring disabled:cursor-default" />
          <span data-mix-badge=""
            className="absolute right-2.25 bottom-2.25 z-6 flex min-h-7 items-center gap-1.5 rounded-2lg px-2.25 py-1 text-caption-1-semibold text-text-white">
            <PLAY aria-hidden className="size-3.75" />
            {`${count} 个视频`}
          </span>
        </div>
      </div>
      <div className="flex min-w-0 items-start gap-2.25">
        <Avatars faces={faces} fallback={name.slice(0, 1)} faceAvatar={faceAvatar} onOpenEntity={onOpenEntity} />
        <div className="flex min-w-0 flex-1 flex-col">
          <b className="truncate text-body-bold text-text-primary">{name}</b>
          <span className="mt-0.5 truncate text-caption-1-regular text-text-secondary">{caption}</span>
        </div>
        {menu}
      </div>
    </article>
  );
}
