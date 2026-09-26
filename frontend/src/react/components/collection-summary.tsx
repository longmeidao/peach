/* 列表页顶上那块汇总（旧 `.collection-summary`）：左边一个名目配一个大数，右边一句分项。
 *
 * 浅色是页面底上的一块填充面，深色反过来比页面亮一档（旧 `html:not(.dark)` 那条），14px 圆角、
 * 不压阴影。600px 以下改成上下两行。 */
export function CollectionSummary({ label, figure, detail }: { label: string; figure: string; detail: string }) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4 rounded-surface bg-background-secondary-default px-6 py-5
      max-compact:flex-col max-compact:items-start max-compact:gap-3 max-compact:p-4
      dark:bg-background-primary-default">
      <div className="flex min-w-0 flex-col gap-2">
        <span className="text-body-regular text-text-secondary">{label}</span>
        <strong className="text-display-4-medium tabular-nums text-text-primary">{figure}</strong>
      </div>
      <p className="text-body-regular text-text-secondary">{detail}</p>
    </div>
  );
}
