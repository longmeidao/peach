import { describe, expect, it } from 'vitest';
import { entitySkeletonHtml } from '../src/entity-skeleton';

describe('实体资料骨架', () => {
  it('事务所使用方形标识、资料头、标签和成员正文', () => {
    const html = entitySkeletonHtml('agency', '<div class="igrid">成员</div>');
    expect(html).toContain('data-skeleton="entity/agency"');
    expect(html).toContain('entityportrait square skeleton');
    expect(html).toContain('entityhero');
    expect(html).toContain('entitytagbar');
    expect(html).toContain('<div class="entitysection"><div class="igrid">');
  });
  it('人物资料使用圆形头像', () => {
    expect(entitySkeletonHtml('performer', '')).toContain('entityportrait skeleton');
  });
});
