/* 实体资料页的正文（`entity-body` island）：名册、作品网格与照片墙三个视图里的一个。
 *
 * 数据全由壳取好推进来，这里只挑出当前视图画。作品网格按 `revision` 换键：壳每发起一次新的
 * 作品请求，这一格先铺骨架（`items` 为 `null`），列表回来后骨架淡出、卡片从模糊里清晰起来，
 * 同目录那一格。骨架还没到显示门槛就回来的，直接落内容。 */
import { useMemo } from 'react';

import { CatalogGridPage } from '../catalog-grid/catalog-grid-page';
import { useSkeletonReveal } from '../components/grid-reveal';
import { PeopleGrid } from '../index/index-people';
import type { EntityBodyProps, EntityRoster } from './entity-body';

export function EntityBodyPage(props: EntityBodyProps) {
  if (props.view === 'people' && props.roster) return <Roster roster={props.roster} props={props} />;
  if (props.view === 'videos') return <VideoSection key={props.revision} {...props} />;
  return null;
}

/** 名册一格点开进这个人（或这个厂牌）的资料页，取图同索引页那条回落链。 */
function Roster({ roster, props }: { roster: EntityRoster; props: EntityBodyProps }) {
  const { helpers, actions } = props;
  const cell = useMemo(() => ({ personAvatar: helpers.personAvatar, openEntity: actions.openEntity }),
    [helpers, actions]);
  return <PeopleGrid kind={roster.kind} items={roster.people} layout={roster.layout} props={cell} />;
}

/** 作品区：外面这一层只管「壳还在取」时的骨架，列表到了就是卡片网格的 entity 模式，
 *  第一页由壳给、续页经 `fetchPage` 取。`[data-entity-grid]` 是壳按 Shift 连选排卡片时认的那一格。 */
function VideoSection(props: EntityBodyProps) {
  const reveal = useSkeletonReveal(!props.items, props.skeletonHtml);
  return (
    <div data-entity-grid="" data-grid-reveal={reveal.fading ? '' : undefined}>
      {reveal.layer}
      {props.items ? (
        <CatalogGridPage mode="entity" entityKey={`${props.kind}:${props.name}`} revision={props.revision}
          initial={props.items} fetchPage={props.fetchPage} helpers={props.helpers} actions={props.actions}
          layout={props.layout} selectMode={props.selectMode} selected={props.selected}
          seekSeconds={props.seekSeconds} cache={props.cache} wireDrag={props.wireDrag}
          skeletonHtml={props.skeletonHtml} groupCollapse={props.groupCollapse} canLoadMore={props.canLoadMore} />
      ) : null}
    </div>
  );
}
