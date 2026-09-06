/** 首页未指定方向时使用浏览偏好；显式 URL 始终优先。 */
export function preferredDirection(sort: string, preferredSort: string, direction: unknown): string {
  return sort === 'seed' ? '' : sort === preferredSort && direction === 'asc' ? 'asc' : 'desc';
}
