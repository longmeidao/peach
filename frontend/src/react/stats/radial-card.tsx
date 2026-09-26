/* 库存的径向图：一段一圈，读数跟着指到的那一段走。
 *
 * 圈由 EvilCharts 的 `EvilRadialChart` 画，颜色按 `chart-1`…`chart-6` 循环，满圈是最长那段的
 * 1.1 倍（`radialCeiling`）。高亮是 React 状态：指针进出与点选各管一件事——扫过去是看一眼，
 * 点下去是钉住。图下那排格子是同一份状态的按钮，键盘也够得着；上游的可点选图例只有一个
 * 选中态，分不出「看一眼」和「钉住」，所以圈的形状与点击走 `radialBarProps` 接到这里。
 * 差异登记在 `../evilcharts/ORIGIN.md`。 */
import { useState } from 'react';
import { Sector, type SectorProps } from 'recharts';

import { EvilRadialChart } from '@/registry/charts/recharts-radial-chart';

import { CHART_CARD, sliceConfig, sliceKey } from '../charts/chart-card';
import { ChartTip } from '../charts/chart-tip';
import { radialBarSize, radialCeiling, type RadialSlice } from './stats';

/** 六档图表色循环。类名写成整串，Tailwind 扫得到。 */
const TILE_SWATCH = [
  'bg-chart-1', 'bg-chart-2', 'bg-chart-3',
  'bg-chart-4', 'bg-chart-5', 'bg-chart-6',
];
/* 钉住某一段时那一格换成这一段自己的颜色：旧 `.board-radial-tiles>button[aria-pressed]`
 * 是同色 10% 混底加一圈 1px 同色内描边。换成中性色的话，六格里哪一格被钉住是认不出来的。 */
const TILE_PINNED = [
  'aria-pressed:bg-chart-1/10 aria-pressed:ring-chart-1',
  'aria-pressed:bg-chart-2/10 aria-pressed:ring-chart-2',
  'aria-pressed:bg-chart-3/10 aria-pressed:ring-chart-3',
  'aria-pressed:bg-chart-4/10 aria-pressed:ring-chart-4',
  'aria-pressed:bg-chart-5/10 aria-pressed:ring-chart-5',
  'aria-pressed:bg-chart-6/10 aria-pressed:ring-chart-6',
];

export function RadialCard(
  { title, rows, unit = '个视频' }: { title: string; rows: RadialSlice[]; unit?: string },
) {
  /* 钉住的那一段和指针扫过的那一段分开记：扫过去要能回到钉住的那一段，合成一个状态的话
     鼠标一离开就把用户点下的选择也擦了。 */
  const [pinned, setPinned] = useState(-1);
  const [hovered, setHovered] = useState(-1);
  const slices = rows.filter((row) => Number.isFinite(row.value) && row.value >= 0);
  if (!slices.length) return null;

  const focus = hovered >= 0 ? hovered : pinned;
  const total = slices.reduce((sum, row) => sum + row.value, 0);
  const shown = slices[focus];
  const toggle = (index: number) => setPinned((at) => (at === index ? -1 : index));
  const data = slices.map((row, index) => ({ slice: sliceKey(index), value: row.value }));

  return (
    <section className={CHART_CARD}>
      <header className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
        <span className="flex min-w-0 flex-col gap-1">
          <h3 className="text-title-2-medium text-text-primary">{shown ? shown.name : title}</h3>
          <b className="text-display-4-medium tabular-nums text-text-primary">
            {(shown ? shown.value : total).toLocaleString()}
          </b>
        </span>
        <small className="text-caption-1-regular text-text-secondary">{unit}</small>
      </header>
      <div role="img" aria-label={title} onPointerLeave={() => setHovered(-1)}>
        <EvilRadialChart data={data} nameKey="slice" config={sliceConfig(slices.map((row) => row.name))}
          max={radialCeiling(slices.map((row) => row.value))} innerRadius="22%"
          className="aspect-auto h-75 max-sm:h-65">
          <EvilRadialChart.RadialBar dataKey="value" barSize={radialBarSize(slices.length)} radialBarProps={{
            shape: (props: SectorProps & { index?: number }) => (
              <Sector {...props}
                opacity={focus >= 0 && focus !== props.index ? 0.3 : 1}
                className="cursor-pointer transition-opacity duration-200" />
            ),
            onClick: (_entry: unknown, index: number) => toggle(index),
            onMouseEnter: (_entry: unknown, index: number) => setHovered(index),
          }} />
          <ChartTip nameKey="slice" hideLabel />
        </EvilRadialChart>
      </div>
      <div className="inline-grid w-full grid-cols-3 gap-2 max-sm:grid-cols-2">
        {slices.map((row, index) => (
          <button key={row.name} type="button" aria-pressed={pinned === index}
            onClick={() => toggle(index)}
            onPointerEnter={() => setHovered(index)} onPointerLeave={() => setHovered(-1)}
            onFocus={() => setHovered(index)} onBlur={() => setHovered(-1)}
            className={`flex min-w-0 cursor-pointer flex-col items-start gap-1 rounded-xl bg-background-tertiary-default p-2.5 text-left outline-none aria-pressed:ring-1 aria-pressed:ring-inset focus-visible:ring-2 focus-visible:ring-border-focus-ring ${TILE_PINNED[index % 6]}`}>
            <span className="flex min-w-0 items-center gap-1.5 text-caption-1-regular text-text-secondary">
              <i aria-hidden className={`size-3 shrink-0 rounded-sm ${TILE_SWATCH[index % 6]}`} />
              {row.name}
            </span>
            <b className="text-title-2-medium tabular-nums text-text-primary">{row.value.toLocaleString()}</b>
            {row.detail ? <small className="text-caption-1-regular text-text-secondary">{row.detail}</small> : null}
          </button>
        ))}
      </div>
    </section>
  );
}
