import { expect, it } from 'vitest';

import { preferredDirection } from '../src/sort-preferences';

it('随机无方向，首页偏好与其他排序分别解析', () => {
  expect(preferredDirection('seed', 'seed', 'asc')).toBe('');
  expect(preferredDirection('new', 'new', 'asc')).toBe('asc');
  expect(preferredDirection('rating', 'new', 'asc')).toBe('desc');
});
