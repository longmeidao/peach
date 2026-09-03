/* 「高清版」管理页（`/quality-goals`）。第一个从 `web/app.js` 迁出来的页面。
 *
 * 选它是因为它的边界最干净：一个 GET（`/api/quality-goals`）、一个自己的容器、
 * 没有写入端点、没有轮询，样式在 `web/css/11-identity.css` 里已经是独立的 `.qualitylist`／
 * `.qualityitem`。迁移它不需要动别的页面，也不需要动样式。
 *
 * 列表数据不在这个文件里：它是共享状态，住在 `../state/quality-goals`，因为数据管理页
 * 的「高清版」卡片读的是同一个真相（原因见那个文件的开头）。这里只做两件
 * 事——首屏取数由 `loadQualityGoals` 发起（`mountIsland` 等它落地才画），画的时候读
 * `qualityGoals` 这个 signal，所以数据之后再变（遗留层写完通知、别处触发刷新）这一屏
 * 自己就更新了，不用重新挂载。
 *
 * 遗留层那几个返回 HTML 的助手（番号标题、来源徽标）由 props 传进来，不在这里重写：
 * 它们是全站语义契约的唯一实现，抄一份就会漂。等下一批页面迁移时再把它们提升成
 * TS 组件，那时 props 一起收窄。 */
import { LOC, fmtDur, fmtSize } from '@peach/legacy/core';
import { emptyStateHtml, noteHtml } from '@peach/legacy/ui';

import { qualityGoals, refreshQualityGoals } from '../state/quality-goals';
import type { QualityGoal, QualityGoalsData } from '../state/quality-goals';

/** 仍由遗留层提供的能力。全是纯函数或导航，island 不持有它们的状态。 */
export interface QualityGoalsProps {
  /** 打开作品详情（遗留层的整页视图，含播放器与队列）。 */
  openItem(id: number): void;
  /** 番号 + 版次徽章 + 标题的 HTML。非 JAV 条目退化成转义后的文件名。 */
  javTitleHtml(item: QualityGoal): string;
  /** 同一条目的纯文本形态，用于无障碍名称。 */
  javDisplayName(item: QualityGoal): string;
  /** 来源徽标（含计费标记）的 HTML。 */
  srcBadge(location: string, cost: string): string;
}

/** 首屏取数。强制重取而不是吃缓存：`/quality-goals` 在路由表里是 `refresh:'reopen'`，
 *  刷新这一页要的就是新数据。结果写进共享 store，返回值只是给 `mountIsland` 的落地信号。 */
export const loadQualityGoals = (
  _props: QualityGoalsProps,
  signal: AbortSignal,
): Promise<QualityGoalsData> => refreshQualityGoals(signal);

/** 封面优先用番号封面，没有就退回第 4 张海报，两者都取不到时把 img 摘掉。 */
const previewUrl = (item: QualityGoal): string => item.has_cover
  ? `/cover?code=${encodeURIComponent(item.code ?? '')}`
  : `/poster?id=${item.id}&c=4`;

/** 只接遗留助手，数据从 store 读。`mountIsland` 仍会把 `{data, error}` 传进来——那是所有
 *  island 共用的首屏契约——由 store 支撑的这一个不看它们：同一份数据两个来源，刷新之后
 *  就会各说一套。 */
export function QualityGoals(
  { openItem, javTitleHtml, javDisplayName, srcBadge }: QualityGoalsProps,
) {
  const { data, error } = qualityGoals.value;
  if (error) {
    return (
      <div
        class="qualitylist"
        dangerouslySetInnerHTML={{ __html: noteHtml(error, { variant: 'error', label: '读取失败' }) }}
      />
    );
  }
  const items = data?.items ?? [];
  if (!items.length) {
    return (
      <div
        class="qualitylist"
        dangerouslySetInnerHTML={{
          __html: emptyStateHtml('sparkles', '没有标记中的高清版目标',
            '现有版本都已满足条件，或还没有加入追踪。'),
        }}
      />
    );
  }
  return (
    <div class="qualitylist">
      {items.map(item => (
        <article class="qualityitem" key={item.id}>
          <button
            class="qualitycover"
            type="button"
            aria-label={`打开 ${javDisplayName(item)}`}
            onClick={() => openItem(item.id)}
          >
            <img
              src={previewUrl(item)}
              alt=""
              loading="lazy"
              onError={event => event.currentTarget.remove()}
            />
          </button>
          <div>
            <h3>
              <button
                type="button"
                data-middle-truncate
                onClick={() => openItem(item.id)}
                dangerouslySetInnerHTML={{ __html: javTitleHtml(item) }}
              />
            </h3>
            <p class="mono">
              {/* Preact 插原始 HTML 必须有个宿主元素，而 `.src` 在遗留版本里是这个
                  flex 容器的直接子项（20×20 的 grid 盒）。`display:contents` 让宿主
                  从布局里消失，徽标的对齐与间距保持不变。 */}
              <span style="display:contents" dangerouslySetInnerHTML={{ __html: srcBadge(item.location, item.cost) }} />
              <span>{LOC[item.location] ?? item.location}</span>
              <span>{fmtDur(item.duration)}</span>
              <span>{fmtSize(item.size ?? 0)}</span>
            </p>
            {item.reason ? <p>{item.reason}</p> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
