/* `/js/core.js` 在测试里的替身（vitest.config.ts 里做 alias）。
 *
 * 真实实现由 Peach 在浏览器里提供，node 里不存在。这里照抄它的**行为**而不是引用它：
 * 断言要能说明「island 用的是遗留层的格式化口径」，所以哨兵值（时长 0／负数 → `—`）
 * 必须一起复制过来，否则测试会放过一个把 `-1` 画成 `0:-1` 的回归。 */
export const LOC: Record<string, string> = {
  local: '本地',
  '115': '115',
  pikpak: 'PikPak',
  online: '在线',
};

export const fmtDur = (seconds: number | null | undefined): string => {
  const total = Number(seconds);
  if (!Number.isFinite(total) || total <= 0) return '—';
  const value = Math.round(total);
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const rest = value % 60;
  const pad = (part: number) => String(part).padStart(2, '0');
  return hours ? `${hours}:${pad(minutes)}:${pad(rest)}` : `${minutes}:${pad(rest)}`;
};

export const fmtSize = (bytes: number | null | undefined): string => {
  const value = Number(bytes) || 0;
  if (value >= 1099511627776) return `${(value / 1099511627776).toFixed(2)} TB`;
  if (value >= 1073741824) return `${(value / 1073741824).toFixed(1)} GB`;
  return `${Math.floor(value / 1048576)} MB`;
};
