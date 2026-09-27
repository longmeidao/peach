/* 实体资料页的正文（ADR-0031 第 10e 步）：筛选浮层下面那一整块的数据形状。
 *
 * 这一块在三个视图之间切换：名册（事务所旗下艺人、片商旗下厂牌）、作品网格和照片墙。
 * 壳（`web/app.js` 的 `openEntity` 一族）拥有取数、路由和视图状态，岛只画：换视图、换筛选、
 * 换排序都由壳取好再用 `updateIsland` 推一份新的，不重挂。点下去的动作全部回壳。
 *
 * 作品网格就是馆藏卡片网格（`catalog-grid`）的 entity 模式，岛里直接渲染那个组件，卡片的
 * 助手、动作、版式与选择状态原样递进去；名册摆的是索引页那一格（`PeopleGrid`）。 */
import type { CatalogGridProps, MediaCardActions, MediaCardHelpers, MediaPage } from '../catalog-grid/types';
import type { IndexPerson, PeopleLayout, PersonAvatar } from '../index/index-data';

/** 这一页此刻摆的是哪一类东西，与筛选浮层那一组视图键同一套词。 */
export type EntityBodyView = 'people' | 'videos' | 'photos';

/** 名册：随资料一起下来的那一批。`kind` 按索引页的词表给：事务所页是 `performers`，
 *  片商页是 `studios`；版式读的是索引页同一个设置值。 */
export interface EntityRoster {
  kind: 'performers' | 'studios';
  people: IndexPerson[];
  layout: PeopleLayout;
}

/** 卡片那几段遗留层 HTML，外加名册一格的取图（遗留层 `personRingHtml` 那条回落链）。 */
export interface EntityBodyHelpers extends MediaCardHelpers {
  personAvatar(item: IndexPerson, entityKind: string, big: boolean): PersonAvatar;
}

/** 卡片上的动作。名册一格点开走的是其中的 `openEntity`。 */
export type EntityBodyActions = MediaCardActions;

/** 从卡片网格原样递进去的那几样：版式、选择状态、缓存与骨架都是壳里同一份。 */
type SharedGridProps = Pick<CatalogGridProps,
  'layout' | 'selectMode' | 'selected' | 'seekSeconds' | 'cache' | 'wireDrag' | 'skeletonHtml'
  | 'groupCollapse' | 'canLoadMore'>;

export interface EntityBodyProps extends SharedGridProps {
  kind: string;
  name: string;
  view: EntityBodyView;
  /** 只有事务所与片商页有；别的页面、或这一批是空的时候是 `null`。 */
  roster: EntityRoster | null;
  /** 作品视图的第一页。`null` 是壳正在取（换了筛选、排序或观看状态）：这一格铺骨架等它，
   *  不把跟头上筛选对不上的旧卡片留在屏幕上。 */
  items: MediaPage | null;
  /** 作品列表的代次。壳每发起一次新的作品请求就加一，网格按它换键，骨架与续页都从头开始。 */
  revision: number;
  /** 续页。筛选与排序由壳在闭包里带着，和第一页同一套口径。 */
  fetchPage(offset: number, signal: AbortSignal): Promise<MediaPage>;
  helpers: EntityBodyHelpers;
  actions: EntityBodyActions;
}
