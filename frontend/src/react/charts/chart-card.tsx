/* 图表卡的外壳、页头与 EvilCharts 配色，统计页与口味页共用。
 *
 * 图表卡比读数卡大一档圆角：旧 `.board-radial-card`／`.board-heat-card`／`.board-sankey-card`
 * 都是 20px。页头是两列：标题压着大数在左，那句注解贴右下角对齐大数的基线，注解长短不一
 * 也不会把标题挤走。 */
import type { ChartConfig } from '@/registry/ui/recharts-chart';

import { cardClass } from '../components/card';

export const CHART_CARD = `${cardClass({ radius: 'chart' })} flex flex-col gap-4 max-sm:p-4`;

/** 一张图的头：一个标题、一个大数、一句它此刻指的是什么。 */
export function ChartHead({ title, figure, note }: { title: string; figure: string; note: string }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
      <span className="flex min-w-0 flex-col gap-1">
        <h3 className="text-title-2-medium text-text-primary">{title}</h3>
        <b className="text-display-4-medium tabular-nums text-text-primary">{figure}</b>
      </span>
      <small className="min-w-0 text-caption-1-regular break-words text-text-secondary">{note}</small>
    </header>
  );
}

/** BoardUI 的六档图表色，`ChartConfig` 里只写这几个变量，深浅两档跟着 token 走。 */
export const CHART_COLORS = [
  'var(--color-chart-1)', 'var(--color-chart-2)', 'var(--color-chart-3)',
  'var(--color-chart-4)', 'var(--color-chart-5)', 'var(--color-chart-6)',
] as const;

/** 一种颜色的 EvilCharts 配色。 */
export const tone = (color: string): ChartConfig[string]['colors'] => ({ light: [color] });

/** 分类图（径向、每段一色）的键。
 *
 * EvilCharts 拿键拼 CSS 变量名和 SVG 渐变 id，媒体库名、来源名里的空格与中文进不了标识符，
 * 所以键一律是 `s0`、`s1`…，显示的名字放在 `label` 里。 */
export const sliceKey = (index: number) => `s${index}`;

export function sliceConfig(names: string[]): ChartConfig {
  return Object.fromEntries(names.map((label, index) => [
    sliceKey(index), { label, colors: tone(CHART_COLORS[index % CHART_COLORS.length]!) },
  ]));
}
