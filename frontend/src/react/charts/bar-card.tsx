/* 分布柱状图：一类一根柱子，画的是 EvilCharts 的 `EvilBarChart`。
 *
 * 页头的大数是各类合计。每根柱子的数标在柱端，数值轴不画：几类之间差一两个数量级时，
 * 短柱子从刻度上读不出数。柱子由 Motion 逐根长出来，系统开了减弱动态效果时直接画终态
 * （`../entry.tsx` 的 `MotionConfig`）；悬停浮层是 `./chart-tip.tsx`。 */
import { EvilBarChart } from '@/registry/charts/recharts-bar-chart';

import { CHART_CARD, ChartHead, tone } from './chart-card';
import { ChartTip } from './chart-tip';

/** 一根柱子：显示的名字和它的数。写成类型别名，EvilCharts 的 `data` 要能当 `Record` 收。 */
export type BarRow = { name: string; value: number };

/** 数值轴留两成余量，最长那根柱子端上的数不被图框切掉。 */
export const BAR_DOMAIN: [number, (max: number) => number] = [0, (max) => max * 1.2];

/** 柱端的数。`position` 跟着柱子的走向：竖柱标在顶上，横条标在右端。 */
export const barLabel = (position: 'top' | 'right') => ({
  position,
  className: 'fill-text-secondary',
  formatter: (value: unknown) => Number(value).toLocaleString(),
});

/** 浮层那一行的名字：`series` 是这一组数的叫法（「视频」「作品」），不是单位。 */
export function BarCard(
  { title, unit, series, rows, color, layout = 'vertical' }:
  {
    title: string; unit: string; series: string; rows: BarRow[]; color: string;
    layout?: 'vertical' | 'horizontal';
  },
) {
  const data = rows
    .filter((row) => Number.isFinite(row.value) && row.value >= 0)
    .map((row) => ({ name: row.name, value: row.value }));
  const total = data.reduce((sum, row) => sum + row.value, 0);
  if (!total) return null;
  const horizontal = layout === 'horizontal';
  /* 图的容器自带 `flex-1`，放进卡片这一列 flex 里会按 0 起算、把 `h-*` 压成 0 高，换成 `flex-none`。
     类别轴 `interval={0}`：每根柱子都要有名字，Recharts 默认会把挤在一起的名字隔一个藏掉。 */
  return (
    <section className={CHART_CARD} aria-label={title}>
      <ChartHead title={title} figure={total.toLocaleString()} note={unit} />
      <EvilBarChart data={data} config={{ value: { label: series, colors: tone(color) } }}
        layout={layout} barRadius={4}
        className={horizontal
          ? 'aspect-auto h-64 flex-none text-text-secondary'
          : 'aspect-auto h-56 flex-none text-text-secondary'}>
        <EvilBarChart.Grid />
        {horizontal
          ? <EvilBarChart.YAxis dataKey="name" interval={0} />
          : <EvilBarChart.XAxis dataKey="name" interval={0} />}
        {horizontal
          ? <EvilBarChart.XAxis hide domain={BAR_DOMAIN} />
          : <EvilBarChart.YAxis hide domain={BAR_DOMAIN} />}
        <EvilBarChart.Bar dataKey="value" enableHoverHighlight
          barProps={{ dataKey: 'value', label: barLabel(horizontal ? 'right' : 'top') }} />
        <ChartTip />
      </EvilBarChart>
    </section>
  );
}
