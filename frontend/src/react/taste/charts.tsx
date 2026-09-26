/* 口味页的三张图：口味维度的雷达与排行条、创作者线索的流向图。浏览活跃的两张热力图与
 * 统计页共用 `../charts/heat-card.tsx`。
 *
 * 三张都用 SVG 画，几何全写成属性——条长是 `rect` 的宽度，流的粗细是 `stroke-width`，
 * `no-inline-styles` 因此不必开例外。颜色只取 BoardUI 的 `chart-*` 与 `border-focus-ring` 档。
 *
 * 指向流向图的一条流或一个节点时读数换成它的；换的是 React 状态，指针离开或焦点移走就回到
 * 总数。差异登记在 `../boardui/ORIGIN.md`。 */
import { useState } from 'react';

import { CHART_CARD, ChartHead } from '../charts/chart-card';
import {
  flowGraph, flowLabel, FLOW_LABEL_X, FLOW_NODE_WIDTH, FLOW_VIEWBOX,
  RADAR_GRID, radarPoints, radarRing, radarShape, rankShares,
  type CreatorFlow, type RankRow,
} from './taste';

/** 六档图表色循环。类名写成整串，Tailwind 扫得到。 */
const FLOW_STROKE = [
  'stroke-chart-1', 'stroke-chart-2', 'stroke-chart-3',
  'stroke-chart-4', 'stroke-chart-5', 'stroke-chart-6',
];
const FLOW_FILL = [
  'fill-chart-1', 'fill-chart-2', 'fill-chart-3',
  'fill-chart-4', 'fill-chart-5', 'fill-chart-6',
];

/** 主要口味维度的雷达图。三个维度以下画不成面，那时整块不出现。 */
export function TasteRadar({ rows, label }: { rows: RankRow[]; label: string }) {
  const points = radarPoints(rows);
  if (!points.length) return null;
  const count = points.length;
  return (
    <svg viewBox="0 0 320 280" role="img" aria-label={label} className="block w-full overflow-visible">
      <title>{points.map((point) => point.name).join('，')}</title>
      {RADAR_GRID.map((radius) => (
        <polygon key={radius} points={radarRing(radius, count)} fill="none"
          className="stroke-separator-border" strokeWidth={1} />
      ))}
      <polygon points={radarShape(points)} strokeWidth={2} strokeLinejoin="round" fillOpacity={0.18}
        className="fill-chart-4 stroke-chart-4" />
      {points.map((point) => (
        <text key={point.name} x={point.labelX} y={point.labelY} dominantBaseline="middle"
          textAnchor={point.labelX < 145 ? 'end' : point.labelX > 175 ? 'start' : 'middle'}
          className="fill-text-secondary text-caption-1-regular">{point.name}</text>
      ))}
    </svg>
  );
}

/** 口味维度排行。一行一条，最长那条占满。 */
export function RankedBars({ rows, label }: { rows: RankRow[]; label: string }) {
  const values = rows
    .filter((row) => Number.isFinite(Number(row.score)) && Number(row.score) > 0)
    .slice().sort((a, b) => Number(b.score) - Number(a.score)).slice(0, 8);
  if (!values.length) return null;
  const shares = rankShares(values);
  return (
    <ol aria-label={label} className="flex flex-col gap-2">
      {values.map((row, index) => (
        <li key={row.name} className="flex min-w-0 flex-col gap-1.5">
          <p className="flex items-baseline justify-between gap-3 text-body-2-regular text-text-primary">
            <span className="min-w-0 break-words">{row.name}</span>
            <b className="tabular-nums">{Number(row.score).toLocaleString()}</b>
          </p>
          <svg viewBox="0 0 100 1" preserveAspectRatio="none" aria-hidden
            className="h-1.5 w-full overflow-hidden rounded-full">
            <rect width={100} height={1} className="fill-chart-track" />
            <rect width={shares[index]} height={1} className="fill-chart-4" />
          </svg>
        </li>
      ))}
    </ol>
  );
}

/** 创作者线索的来源流向。指一条流或一个节点，读数换成它。 */
export function CreatorSankey({ flows }: { flows: CreatorFlow[] | undefined }) {
  const [shown, setShown] = useState<{ value: number; label: string; node: number | null } | null>(null);
  const graph = flowGraph(flows);
  if (!graph) return null;
  const node = shown?.node ?? null;
  /** 这条流此刻要不要淡下去。指的是节点时留下它两端的流，指的是流时只留它自己。 */
  const linkLit = (link: typeof graph.links[number], key: string) =>
    (!shown ? true
      : node !== null ? link.source === node || link.target === node
      : shown.label === key);
  return (
    <section className={CHART_CARD}>
      <ChartHead title="创作者线索来源" figure={(shown ? shown.value : graph.total).toLocaleString()}
        note={shown ? shown.label : '条线索'} />
      <div className="min-w-0 overflow-x-auto">
        <svg viewBox={`0 0 ${FLOW_VIEWBOX.width} ${FLOW_VIEWBOX.height}`} fill="none"
          role="img" aria-label="来源网站与创作者线索"
          className="block h-auto max-h-130 min-w-160 w-full" onPointerLeave={() => setShown(null)}>
          <g>
            {graph.links.map((link) => (
              <path key={link.key} d={link.d} strokeWidth={link.width} tabIndex={0} role="img"
                aria-label={`${link.label}：${link.value} 条线索`}
                fillOpacity={0} strokeOpacity={linkLit(link, link.label) ? 0.55 : 0.08}
                className={`outline-none transition-opacity ${FLOW_STROKE[link.color]}`}
                onPointerEnter={() => setShown({ value: link.value, label: link.label, node: null })}
                onFocus={() => setShown({ value: link.value, label: link.label, node: null })}
                onBlur={() => setShown(null)} />
            ))}
          </g>
          <g>
            {graph.nodes.map((item) => (
              <g key={item.id} tabIndex={0} role="img"
                aria-label={`${item.name}：${item.value} 条线索`}
                className="outline-none focus-visible:opacity-100"
                onPointerEnter={() => setShown(
                  { value: item.value, label: item.name, node: item.index })}
                onFocus={() => setShown({ value: item.value, label: item.name, node: item.index })}
                onBlur={() => setShown(null)}>
                <rect x={item.x} y={item.y} width={FLOW_NODE_WIDTH} height={item.height} rx={5}
                  className={item.side === 'source' ? FLOW_FILL[item.color] : 'fill-text-secondary'} />
                <text x={FLOW_LABEL_X[item.side]} y={item.y + item.height / 2}
                  textAnchor={item.side === 'source' ? 'end' : 'start'} dominantBaseline="middle"
                  className="fill-text-secondary text-caption-1-regular">
                  {flowLabel(item.name)}
                  <tspan x={FLOW_LABEL_X[item.side]} dy={15}>
                    {item.side === 'source'
                      ? item.value.toLocaleString()
                      : `${item.share.toFixed(1)}%`}
                  </tspan>
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>
      <footer className="flex justify-between gap-3 text-caption-1-regular text-text-secondary">
        <span>来源网站</span><span>创作者 · 线索占比</span>
      </footer>
    </section>
  );
}
