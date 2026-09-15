/* 已知总量的进度条。更新下载与任务活动共用这一份。
 *
 * 注册表里没有进度组件，用 SVG 矩形画：宽度按比例写进 `rect` 的属性，不用内联样式，
 * 也就不必给 `no-inline-styles` 开例外。差异登记在 `../boardui/ORIGIN.md`。 */

export function Progress({ label, value, max = 100, stops = [] }: { label: string; value: number; max?: number; stops?: number[] }) {
  const filled = Math.min(Math.max(value, 0), max);
  return (
    <svg role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={value}
      viewBox={`0 0 ${max} 1`} preserveAspectRatio="none" className="h-1.5 w-full overflow-hidden rounded-full">
      <rect width={max} height={1} className="fill-background-tertiary-default" />
      <rect width={filled} height={1} className="fill-border-focus-ring" />
      {stops.map((stop) => <rect key={stop} x={stop} width={0.4} height={1} className="fill-background-secondary-default" />)}
    </svg>
  );
}
