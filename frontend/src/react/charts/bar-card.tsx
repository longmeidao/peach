/* 分布柱状图：一类一根柱子，画的是 EvilCharts 的 `EvilBarChart`。
 *
 * 页头的大数是各类合计，柱子的数在悬停浮层（`./chart-tip.tsx`）里读。柱子由 Motion 逐根长出来，
 * 系统开了减弱动态效果时直接画终态（`../entry.tsx` 的 `MotionConfig`）。 */
import { EvilBarChart } from '@/registry/charts/recharts-bar-chart';

import { CHART_CARD, ChartHead, tone } from './chart-card';
import { ChartTip } from './chart-tip';

/** 一根柱子：显示的名字和它的数。 */
export interface BarRow { name: string; value: number }

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
  return (
    <section className={CHART_CARD} aria-label={title}>
      <ChartHead title={title} figure={total.toLocaleString()} note={unit} />
      <EvilBarChart data={data} config={{ value: { label: series, colors: tone(color) } }}
        layout={layout} barRadius={4}
        className={horizontal ? 'aspect-auto h-64 text-text-secondary' : 'aspect-auto h-56 text-text-secondary'}>
        <EvilBarChart.Grid />
        {horizontal
          ? <EvilBarChart.YAxis dataKey="name" />
          : <EvilBarChart.XAxis dataKey="name" />}
        {horizontal
          ? <EvilBarChart.XAxis tickFormatter={(value: number) => value.toLocaleString()} />
          : <EvilBarChart.YAxis tickFormatter={(value: number) => value.toLocaleString()} />}
        <EvilBarChart.Bar dataKey="value" enableHoverHighlight />
        <ChartTip />
      </EvilBarChart>
    </section>
  );
}
