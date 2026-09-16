/* 库存的径向图：一段一圈，读数跟着指到的那一段走。
 *
 * 注册表里没有图表条目，环用 SVG 画：`pathLength={100}` 把一圈长度钉成 100，
 * `stroke-dasharray` 写的那个数就是百分比本身，几何全走属性、不用内联样式。颜色只取
 * BoardUI 的 `chart-*` 档，差异登记在 `../boardui/ORIGIN.md`。
 *
 * 高亮是 React 状态：指针进出与点选各管一件事——扫过去是看一眼，点下去是钉住。
 * 过渡用 CSS，`web/css/01-base.css` 的全局规则在 reduced motion 下把它整个关掉。 */
import { useState } from 'react';

import { cardClass } from '../components/card';
import { rings, type RadialSlice } from './stats';

/** 六档图表色循环。类名写成整串，Tailwind 扫得到。 */
const RING_STROKE = [
  'stroke-chart-1', 'stroke-chart-2', 'stroke-chart-3',
  'stroke-chart-4', 'stroke-chart-5', 'stroke-chart-6',
];
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
  const geometry = rings(slices.map((row) => row.value));
  const shown = slices[focus];
  const toggle = (index: number) => setPinned((at) => (at === index ? -1 : index));

  return (
    <section className={`${cardClass({ radius: 'chart' })} flex flex-col gap-4 max-sm:p-4`}>
      <header className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
        <span className="flex min-w-0 flex-col gap-1">
          <h3 className="text-title-2-medium text-text-primary">{shown ? shown.name : title}</h3>
          <b className="text-display-4-medium tabular-nums text-text-primary">
            {(shown ? shown.value : total).toLocaleString()}
          </b>
        </span>
        <small className="text-caption-1-regular text-text-secondary">{unit}</small>
      </header>
      <svg viewBox="0 0 320 320" fill="none" role="img" aria-label={title}
        className="block h-75 w-full max-sm:h-65" onPointerLeave={() => setHovered(-1)}>
        {slices.map((row, index) => (
          <g key={row.name} onPointerEnter={() => setHovered(index)} onClick={() => toggle(index)}>
            <title>{`${row.name}：${row.value.toLocaleString()} ${unit}`}</title>
            <circle cx="160" cy="160" r={geometry[index]!.radius} strokeWidth={geometry[index]!.width}
              strokeLinecap="round" className="stroke-chart-track" />
            <circle cx="160" cy="160" r={geometry[index]!.radius} strokeWidth={geometry[index]!.width}
              strokeLinecap="round" pathLength={100} transform="rotate(-90 160 160)"
              strokeDasharray={`${geometry[index]!.length} ${100 - geometry[index]!.length}`}
              className={focus >= 0 && focus !== index
                ? `cursor-pointer opacity-30 transition-opacity ${RING_STROKE[index % 6]}`
                : `cursor-pointer transition-opacity ${RING_STROKE[index % 6]}`} />
          </g>
        ))}
      </svg>
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
